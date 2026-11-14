"""Fail-closed ResourceBudget: every external model call needs an atomic worst-case
reservation before it starts and a usage commit after it ends.

Rules
- Limits come from an explicit, owner-approved budget file. Missing or invalid
  fields refuse the run (no defaults that could allow spending).
- Requests are counted at reservation time; a started request is never refunded.
- Cached input is part of total input and is also recorded separately.
- Unknown usage is never zero: the worst-case reservation is charged and the
  entry is marked USAGE_UNKNOWN / USAGE_UNCERTAIN.
- BUDGET_BLOCKED and QUOTA_BLOCKED are sticky for the approval. Continuing needs
  a new approval_id (new explicit owner consent).
- The ledger lives on disk and is guarded by a thread lock plus an fcntl file lock,
  so parallel threads and processes share one consistent count.
"""
from __future__ import annotations
import fcntl,json,math,os,threading,time,uuid
from pathlib import Path
from .common import ContractError

BUDGET_BLOCKED='BUDGET_BLOCKED'
QUOTA_BLOCKED='QUOTA_BLOCKED'
LIMIT_FIELDS=('max_requests','max_input_tokens','max_output_tokens','max_wall_seconds','max_retries',
              'max_input_tokens_per_call','max_output_tokens_per_call','input_overhead_tokens_per_call','image_input_tokens')

class BudgetBlocked(ContractError):
    """Raised instead of making a call. Carries a record like ProviderError."""
    def __init__(self,state,reason,record=None):
        super().__init__(f'{state}: {reason}')
        self.state=state;self.reason=reason
        self.record={'classification':state,'reason':reason,**(record or {})}

def load_budget_config(path):
    path=Path(path)
    try:cfg=json.loads(path.read_text())
    except (OSError,ValueError) as e:raise ContractError(f'Budget file unreadable: {e}')
    return validate_config(cfg)

def validate_config(cfg):
    if not isinstance(cfg,dict):raise ContractError('Budget config must be an object')
    approval=cfg.get('approval_id')
    if not isinstance(approval,str) or not approval.strip() or '/' in approval or approval.startswith('.'):
        raise ContractError('Budget config needs a plain approval_id (explicit owner approval)')
    out={'approval_id':approval.strip()}
    for field in LIMIT_FIELDS:
        value=cfg.get(field)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ContractError(f'Budget field {field} missing or invalid; refusing (fail-closed)')
        if field!='max_retries' and field not in ('input_overhead_tokens_per_call','image_input_tokens') and value<=0:
            raise ContractError(f'Budget field {field} must be positive')
        out[field]=value
    if out['max_input_tokens_per_call']>out['max_input_tokens'] or out['max_output_tokens_per_call']>out['max_output_tokens']:
        raise ContractError('Per-call ceiling exceeds total budget')
    # B6.8: optional cost cap. Needs list prices (USD per 1M tokens); the worst case is reserved before each call.
    if cfg.get('max_cost_usd') is not None:
        mc=cfg['max_cost_usd'];pr=cfg.get('pricing')
        if isinstance(mc,bool) or not isinstance(mc,(int,float)) or not math.isfinite(mc) or mc<=0:raise ContractError('max_cost_usd must be a positive number')
        if not isinstance(pr,dict) or any(isinstance(pr.get(k),bool) or not isinstance(pr.get(k),(int,float)) or pr.get(k)<0 for k in ('input','output')):
            raise ContractError('max_cost_usd needs pricing {input, output} in USD per 1M tokens')
        out['max_cost_usd']=float(mc);out['pricing']={'input':float(pr['input']),'output':float(pr['output'])}
    resume=cfg.get('authorize_resume_of')
    if resume is not None and (not isinstance(resume,str) or not resume):raise ContractError('authorize_resume_of must be a run directory name')
    out['authorize_resume_of']=resume
    return out

def normalize_usage(provider,raw):
    """Return {'input','cached_input','cache_creation_input','output'} or None if unknown."""
    def num(d,k):
        v=d.get(k) if isinstance(d,dict) else None
        return v if isinstance(v,int) and not isinstance(v,bool) and v>=0 else None
    if provider=='codex':
        turns=[u for u in (raw or []) if isinstance(u,dict)] if isinstance(raw,list) else []
        if not turns or len(turns)!=len(raw):return None
        total={'input':0,'cached_input':0,'cache_creation_input':0,'output':0}
        for u in turns:
            i,o=num(u,'input_tokens'),num(u,'output_tokens')
            if i is None or o is None:return None
            c=num(u,'cached_input_tokens') or 0
            if c>i:return None   # cached is a subset of input in this protocol
            total['input']+=i;total['cached_input']+=c;total['output']+=o+(num(u,'reasoning_output_tokens') or 0)
        return total
    if provider=='claude':
        i,o=num(raw,'input_tokens'),num(raw,'output_tokens')
        if i is None or o is None:return None
        read=num(raw,'cache_read_input_tokens') or 0;create=num(raw,'cache_creation_input_tokens') or 0
        # Claude reports cache reads/creations outside input_tokens; total input includes them.
        return {'input':i+read+create,'cached_input':read,'cache_creation_input':create,'output':o}
    if provider=='fixture' and isinstance(raw,dict):
        i,o=num(raw,'input_tokens'),num(raw,'output_tokens')
        if i is None or o is None:return None
        c=num(raw,'cached_input_tokens') or 0
        return None if c>i else {'input':i,'cached_input':c,'cache_creation_input':0,'output':o}
    if provider=='gemini' and isinstance(raw,dict):
        # Gemini UsageMetadata: prompt_token_count includes cached_content_token_count; thoughts are billed as output
        # in addition to candidates; tool-use prompt tokens are extra input.
        g=lambda *ks:next((raw[k] for k in ks if isinstance(raw.get(k),int) and not isinstance(raw.get(k),bool) and raw[k]>=0),None)
        i=g('prompt_token_count','promptTokenCount');o=g('candidates_token_count','candidatesTokenCount')
        if i is None:return None
        o=(o or 0)+(g('thoughts_token_count','thoughtsTokenCount') or 0)
        c=g('cached_content_token_count','cachedContentTokenCount') or 0
        if c>i:return None
        return {'input':i+(g('tool_use_prompt_token_count','toolUsePromptTokenCount') or 0),'cached_input':c,'cache_creation_input':0,'output':o}
    return None   # anything unrecognised: unknown, never zero

class ResourceBudget:
    def __init__(self,config,ledger_dir,clock=time.time):
        self.config=validate_config(config)
        self.dir=Path(ledger_dir);self.dir.mkdir(parents=True,exist_ok=True)
        self.path=self.dir/(self.config['approval_id']+'.ledger.json')
        self.lockfile=self.dir/(self.config['approval_id']+'.lock')
        self.clock=clock;self._lock=threading.Lock()
        with self._locked() as state:
            if state.get('limits') and state['limits']!={k:self.config[k] for k in LIMIT_FIELDS}:
                raise ContractError('approval_id already used with different limits; use a new approval_id')

    # --- persistence -------------------------------------------------------
    def _fresh(self):
        return {'schema':'em-resource-budget-v1','approval_id':self.config['approval_id'],
                'limits':{k:self.config[k] for k in LIMIT_FIELDS},'state':'ACTIVE','blocked_reason':None,
                'started':self.clock(),'requests':0,'retries':0,'input_tokens':0,'cached_input_tokens':0,
                'cache_creation_input_tokens':0,'output_tokens':0,'reserved_input':0,'reserved_output':0,
                'usage_unknown_calls':0,'usage_uncertain_calls':0,'overrun_calls':0,'roles_attempted':{},'cost_usd':0.0,'reserved_cost_usd':0.0,
                'open_reservations':{},'entries':[]}
    class _Ctx:
        def __init__(self,b):self.b=b
        def __enter__(self):
            self.b._lock.acquire()
            try:
                self.fh=open(self.b.lockfile,'a');fcntl.flock(self.fh,fcntl.LOCK_EX)
                self.state=json.loads(self.b.path.read_text()) if self.b.path.exists() else self.b._fresh()
            except BaseException:
                self.b._lock.release();raise
            return self.state
        def __exit__(self,et,ev,tb):
            try:
                tmp=self.b.path.with_name(self.b.path.name+f'.{os.getpid()}.tmp')
                with tmp.open('w') as f:json.dump(self.state,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
                os.replace(tmp,self.b.path)
            finally:
                fcntl.flock(self.fh,fcntl.LOCK_UN);self.fh.close();self.b._lock.release()
            return False
    def _locked(self):return self._Ctx(self)
    def snapshot(self):
        with self._locked() as s:return json.loads(json.dumps(s))

    # --- checks ------------------------------------------------------------
    def _block(self,s,state,reason):
        s['state']=state;s['blocked_reason']=reason
        s['entries'].append({'event':state,'reason':reason,'time':self.clock()})
    def _remaining_seconds(self,s):return self.config['max_wall_seconds']-(self.clock()-s['started'])
    def _check_open(self,s):
        if s['state']!='ACTIVE':raise BudgetBlocked(s['state'],s['blocked_reason'] or 'blocked for this approval; new approval_id required')
    def preflight(self):
        """Raise BudgetBlocked if no further request could be reserved now."""
        with self._locked() as s:
            self._check_open(s)
            if s['requests']>=self.config['max_requests']:self._block(s,BUDGET_BLOCKED,'max_requests reached')
            elif self._remaining_seconds(s)<=0:self._block(s,BUDGET_BLOCKED,'max_wall_seconds reached')
            self._check_open(s)
    def remaining_seconds(self):
        with self._locked() as s:return self._remaining_seconds(s)
    def worst_case(self,prompt,images=0):
        # One token never spans less than one byte, so UTF-8 bytes bound prompt tokens.
        return {'input':len(str(prompt).encode())+self.config['input_overhead_tokens_per_call']+images*self.config['image_input_tokens'],
                'output':self.config['max_output_tokens_per_call']}

    # --- reserve / commit ----------------------------------------------------
    def reserve(self,role,prompt,images=0,provider='unknown'):
        wc=self.worst_case(prompt,images)
        with self._locked() as s:
            self._check_open(s)
            cfg=self.config;reason=None
            retry=role in s['roles_attempted']
            if s['requests']+1>cfg['max_requests']:reason='max_requests reached'
            elif self._remaining_seconds(s)<=0:reason='max_wall_seconds reached'
            elif retry and s['retries']+1>cfg['max_retries']:reason='max_retries reached'
            elif wc['input']>cfg['max_input_tokens_per_call']:reason=f'worst-case input {wc["input"]} exceeds per-call ceiling'
            elif s['input_tokens']+s['reserved_input']+wc['input']>cfg['max_input_tokens']:reason='worst-case input would exceed max_input_tokens'
            elif s['output_tokens']+s['reserved_output']+wc['output']>cfg['max_output_tokens']:reason='worst-case output would exceed max_output_tokens'
            elif cfg.get('max_cost_usd') and s.get('cost_usd',0)+s.get('reserved_cost_usd',0)+self.worst_cost(wc)>cfg['max_cost_usd']:
                reason=f"worst-case cost {self.worst_cost(wc):.4f} USD would exceed max_cost_usd {cfg['max_cost_usd']}"
            if reason:
                self._block(s,BUDGET_BLOCKED,reason)
                raise BudgetBlocked(BUDGET_BLOCKED,reason,{'role':role})
            rid=uuid.uuid4().hex
            s['requests']+=1;s['retries']+=int(retry);s['roles_attempted'][role]=s['roles_attempted'].get(role,0)+1
            s['reserved_input']+=wc['input'];s['reserved_output']+=wc['output'];s['reserved_cost_usd']=s.get('reserved_cost_usd',0)+self.worst_cost(wc)
            s['open_reservations'][rid]={'role':role,'provider':provider,'input':wc['input'],'output':wc['output'],'cost':self.worst_cost(wc),'time':self.clock(),'pid':os.getpid()}
            s['entries'].append({'event':'RESERVED','id':rid,'role':role,'retry':retry,'worst_case':wc,'time':self.clock()})
            return rid
    def release(self,rid,reason):
        """Undo a reservation ONLY when no external process was started."""
        with self._locked() as s:
            r=s['open_reservations'].pop(rid,None)
            if r is None:return
            s['reserved_input']-=r['input'];s['reserved_output']-=r['output'];s['requests']-=1;s['reserved_cost_usd']=s.get('reserved_cost_usd',0)-r.get('cost',0)
            s['roles_attempted'][r['role']]-=1
            if not s['roles_attempted'][r['role']]:
                del s['roles_attempted'][r['role']]
            elif s['retries']:s['retries']-=1
            s['entries'].append({'event':'RELEASED_NOT_STARTED','id':rid,'reason':reason,'time':self.clock()})
    def worst_cost(self,wc):
        """Upper bound of one call's cost (no cache discount assumed); 0 when no cost cap is configured."""
        pr=self.config.get('pricing')
        return (wc['input']*pr['input']+wc['output']*pr['output'])/1e6 if pr else 0.0
    def commit(self,rid,usage,outcome='SUCCEEDED',quota=False,block_reason=None,cost_usd=None):
        """usage: normalized dict or None. None charges the worst case. block_reason makes the approval sticky-blocked.
        cost_usd: provider estimate for this call; unknown cost is charged at the reserved worst case."""
        with self._locked() as s:
            r=s['open_reservations'].pop(rid,None)
            if r is None:raise ContractError('Unknown or already committed reservation')
            s['reserved_input']-=r['input'];s['reserved_output']-=r['output'];s['reserved_cost_usd']=s.get('reserved_cost_usd',0)-r.get('cost',0)
            charged_cost=cost_usd if (cost_usd is not None and usage is not None) else r.get('cost',0)
            s['cost_usd']=s.get('cost_usd',0)+charged_cost
            if usage is None:
                charged={'input':r['input'],'cached_input':0,'cache_creation_input':0,'output':r['output']}
                status='USAGE_UNKNOWN' if outcome=='SUCCEEDED' else 'USAGE_UNCERTAIN'
                s['usage_unknown_calls' if status=='USAGE_UNKNOWN' else 'usage_uncertain_calls']+=1
            else:
                charged=dict(usage);status='MEASURED' if outcome=='SUCCEEDED' else 'MEASURED_PARTIAL'
            overrun=charged['input']>r['input'] or charged['output']>r['output']
            s['overrun_calls']+=int(overrun)
            s['input_tokens']+=charged['input'];s['cached_input_tokens']+=charged['cached_input']
            s['cache_creation_input_tokens']+=charged.get('cache_creation_input',0);s['output_tokens']+=charged['output']
            s['entries'].append({'event':'COMMITTED','id':rid,'role':r['role'],'outcome':outcome,'usage_status':status,'charged':charged,'cost_usd':charged_cost,'overrun':overrun,'time':self.clock()})
            if quota:self._block(s,QUOTA_BLOCKED,'provider reported usage/quota limit')
            elif block_reason:self._block(s,BUDGET_BLOCKED,block_reason)
            elif self.config.get('max_cost_usd') and s['cost_usd']>=self.config['max_cost_usd']:
                self._block(s,BUDGET_BLOCKED,'cost budget exhausted')
            elif s['input_tokens']>=self.config['max_input_tokens'] or s['output_tokens']>=self.config['max_output_tokens']:
                self._block(s,BUDGET_BLOCKED,'token budget exhausted'+(' (actual usage exceeded reservation)' if overrun else ''))
            return status
    def recover_stale(self):
        """Reservations left open by a crashed process are charged at worst case."""
        with self._locked() as s:
            for rid,r in list(s['open_reservations'].items()):
                try:os.kill(r['pid'],0);alive=r['pid']!=os.getpid()
                except (ProcessLookupError,PermissionError):alive=False
                if alive:continue
                s['open_reservations'].pop(rid)
                s['reserved_input']-=r['input'];s['reserved_output']-=r['output']
                s['input_tokens']+=r['input'];s['output_tokens']+=r['output'];s['usage_uncertain_calls']+=1;s['cost_usd']=s.get('cost_usd',0)+r.get('cost',0);s['reserved_cost_usd']=s.get('reserved_cost_usd',0)-r.get('cost',0)
                s['entries'].append({'event':'STALE_RESERVATION_CHARGED','id':rid,'role':r['role'],'usage_status':'USAGE_UNCERTAIN','time':self.clock()})
    def summary(self):
        s=self.snapshot()
        keys=('approval_id','state','blocked_reason','requests','retries','input_tokens','cached_input_tokens','cache_creation_input_tokens','output_tokens','usage_unknown_calls','usage_uncertain_calls','overrun_calls','limits')
        out={k:s[k] for k in keys};out['cost_usd_estimate']=round(s.get('cost_usd',0),6);out['max_cost_usd']=self.config.get('max_cost_usd');out['open_reservations']=len(s['open_reservations']);out['elapsed_seconds']=self.clock()-s['started']
        return out
