"""Atomic, hash-bound stage checkpoints; crashed/failed nodes can resume safely."""
from pathlib import Path
import hashlib,json,time,os
from .common import sha_file,ContractError

def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

class Checkpoints:
    def __init__(self,out):self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
    def engine_identity(self):
        if not hasattr(self,"_engine_identity"):
            from .runtime import engine_snapshot
            self._engine_identity=digest(engine_snapshot())
        return self._engine_identity
    def invoke(self,role,prompt,provider,validate,images=None):
        key=digest({'role':role,'prompt':prompt,'provider':provider.fingerprint(),'engine':self.engine_identity(),'images':[{k:v for k,v in i.items() if k!='path'} for i in images or []]})
        checkpoint=self.out/(role+'.checkpoint.json');answer=self.out/'stage_outputs'/(role+'.json')
        if checkpoint.exists():
            old=json.loads(checkpoint.read_text())
            if old.get('status')=='SUCCEEDED' and old.get('input_sha256')==key and answer.exists() and sha_file(answer)==old.get('output_sha256'):
                obj=json.loads(answer.read_text())
                try:validate(obj)
                except (ContractError,ValueError,TypeError,KeyError):self.event(role,'CACHE_REJECTED_BY_CURRENT_CONTRACT',key)
                else:self.event(role,'CACHE_HIT',key);return obj
        # Budget gate BEFORE any checkpoint mutation: a blocked call leaves state untouched.
        budget=getattr(provider,'budget',None)
        if budget is not None:budget.preflight()
        elif getattr(provider,'external',False) is True:
            from .budget import BudgetBlocked,BUDGET_BLOCKED
            raise BudgetBlocked(BUDGET_BLOCKED,'no ResourceBudget attached to external provider',{'role':role})
        previous=json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
        if checkpoint.exists():
            history=self.out/'checkpoint_history';history.mkdir(exist_ok=True);(history/(role+'-'+str(time.time_ns())+'.json')).write_bytes(checkpoint.read_bytes())
        if answer.exists():
            archive=self.out/'superseded';archive.mkdir(exist_ok=True)
            os.replace(answer,archive/(role+'-'+str(time.time_ns())+'.json'))
        record={'schema':'em-stage-checkpoint-v4','role':role,'input_sha256':key,'status':'RUNNING','started':time.time(),'generation':previous.get('generation',0)+1}
        atomic(checkpoint,record);self.event(role,'STARTED',key)
        try:
            request=prompt
            for attempt in range(2):
                obj=provider.ask(role,request,self.out,images=[i['path'] for i in images or []])
                try:validate(obj);break
                except (ContractError,ValueError,TypeError,KeyError,ZeroDivisionError) as e:
                    atomic(self.out/f'{role}.invalid-{record["generation"]}-{attempt}.json',obj)
                    if attempt:raise
                    request=prompt+'\nCONTRACT REPAIR (one attempt): '+str(e)+'\nReturn complete corrected JSON. Invalid answer:\n'+json.dumps(obj,ensure_ascii=False)
            atomic(answer,obj);record.update(status='SUCCEEDED',output_sha256=sha_file(answer),finished=time.time());atomic(checkpoint,record);self.event(role,'SUCCEEDED',key);return obj
        except BaseException as e:
            from .budget import BudgetBlocked
            state=e.state if isinstance(e,BudgetBlocked) else 'QUOTA_BLOCKED' if getattr(e,'record',{}).get('classification')=='USAGE_LIMIT' else 'FAILED' if isinstance(e,Exception) else 'INTERRUPTED'
            record.update(status=state,error_type=type(e).__name__,error=str(e),finished=time.time(),resumable=True)
            atomic(checkpoint,record);self.event(role,state,key);raise
    def reject(self,role,provider,reason):
        """A deterministic stage gate failed on this role's SUCCEEDED answer. The cached answer must not be served again:
        mark the checkpoint, archive the stage output and let the provider discard a stored answer (agent provider)."""
        checkpoint=self.out/(role+'.checkpoint.json');answer=self.out/'stage_outputs'/(role+'.json')
        if checkpoint.exists():
            rec=json.loads(checkpoint.read_text());rec.update(status='REJECTED_BY_STAGE_GATE',rejected_reason=reason,rejected_at=time.time(),resumable=True)
            atomic(checkpoint,rec)
        if answer.exists():
            archive=self.out/'superseded';archive.mkdir(exist_ok=True);os.replace(answer,archive/(role+'-rejected-'+str(time.time_ns())+'.json'))
        moved=provider.discard(role,self.out,reason) if hasattr(provider,'discard') else []
        self.event(role,'REJECTED_BY_STAGE_GATE',None);return moved
    def event(self,role,status,key):
        with (self.out/'events.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'role':role,'status':status,'input_sha256':key})+'\n')
