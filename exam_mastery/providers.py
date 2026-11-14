"""Provider-neutral JSON boundary with persisted, redacted process evidence."""
from __future__ import annotations
import json,os,re,shutil,subprocess,time,hashlib,signal,threading,atexit
from pathlib import Path
from .common import ContractError,extract_json,write_json
from .budget import BudgetBlocked,normalize_usage,BUDGET_BLOCKED,QUOTA_BLOCKED

def redact(text):
    text=str(text)
    for key,value in os.environ.items():
        if any(k in key.upper() for k in ('TOKEN','SECRET','API_KEY','PASSWORD')) and len(value)>12:text=text.replace(value,'<REDACTED>')
    return re.sub(r'(?i)(bearer\s+)[A-Za-z0-9._-]+',r'\1<REDACTED>',re.sub(r'\bsk-(?:ant-)?[A-Za-z0-9_-]{12,}','<REDACTED>',text))

class ProviderError(ContractError):
    def __init__(self,message,record):super().__init__(message);self.record=record

MODEL_UNAVAILABLE='MODEL_UNAVAILABLE'
# A plain model slug; never something codex could read as another option.
_MODEL_RE=re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}')
_MODEL_NOT_FOUND=re.compile(r'model_not_found|model[^\n]{0,80}(does not exist|not found|not supported|unsupported|unknown)',re.I)

class ModelUnavailable(ContractError):
    """Raised before any reservation or process when the requested model cannot be used."""
    def __init__(self,model,reason):
        super().__init__(f'{MODEL_UNAVAILABLE}: {model!r}: {reason}');self.state=MODEL_UNAVAILABLE;self.model=model;self.reason=reason

def codex_model_catalog():
    """Model slugs from codex's local cache ($CODEX_HOME/models_cache.json). Metadata only:
    listing does not prove the server will accept the model, so model_not_found at run time is handled too."""
    path=Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex')/'models_cache.json'
    try:data=json.loads(path.read_text())
    except (OSError,ValueError) as e:raise ModelUnavailable(None,f'local codex model catalog unreadable ({path.name}): {type(e).__name__}')
    models=data.get('models') if isinstance(data,dict) else None
    slugs={m.get('slug') for m in models or [] if isinstance(m,dict) and isinstance(m.get('slug'),str)}
    if not slugs:raise ModelUnavailable(None,'local codex model catalog lists no models')
    return slugs

def check_model(name,model):
    """Fail-closed model gate for external providers. Returns the model; never starts a process."""
    if model is None:raise ModelUnavailable(None,'no explicit model; pass --model <slug>')
    if not isinstance(model,str) or not _MODEL_RE.fullmatch(model):raise ModelUnavailable(model,'invalid model name')
    if name=='codex' and model not in codex_model_catalog():raise ModelUnavailable(model,'not in the local codex model catalog')
    return model

# Every live provider process group is registered so no child can outlive a stop.
ACTIVE_GROUPS=set()
_GROUP_LOCK=threading.Lock()

def _kill_group(pgid,sig=signal.SIGKILL):
    try:os.killpg(pgid,sig)
    except (ProcessLookupError,PermissionError):pass

def group_alive(pgid):
    try:os.killpg(pgid,0);return True
    except (ProcessLookupError,PermissionError):return False

def terminate_all_children(grace=2.0):
    """Stop every registered provider process group (TERM, then KILL). Returns pgids handled."""
    with _GROUP_LOCK:groups=list(ACTIVE_GROUPS)
    for g in groups:_kill_group(g,signal.SIGTERM)
    deadline=time.time()+grace
    while time.time()<deadline and any(group_alive(g) for g in groups):time.sleep(0.05)
    for g in groups:_kill_group(g,signal.SIGKILL)
    with _GROUP_LOCK:ACTIVE_GROUPS.difference_update(groups)
    return groups
atexit.register(terminate_all_children)

def execute(cmd,prompt,cwd,timeout):
    p=subprocess.Popen(cmd,cwd=cwd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    with _GROUP_LOCK:ACTIVE_GROUPS.add(p.pid)
    timed_out=False
    try:
        try:stdout,stderr=p.communicate(prompt,timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            _kill_group(p.pid,signal.SIGTERM)
            try:stdout,stderr=p.communicate(timeout=2)
            except subprocess.TimeoutExpired:_kill_group(p.pid);stdout,stderr=p.communicate()
        except BaseException:
            # Interrupt (Ctrl-C, SIGTERM->exception): never leave the provider running.
            _kill_group(p.pid,signal.SIGTERM);time.sleep(0.2);_kill_group(p.pid)
            try:p.communicate(timeout=2)
            except Exception:pass
            raise
    finally:
        # The leader may exit while grandchildren keep the group alive; reap the group.
        _kill_group(p.pid)
        with _GROUP_LOCK:ACTIVE_GROUPS.discard(p.pid)
    return p.returncode,stdout,stderr,timed_out

class Provider:
    """ask() is the only runtime dependency. Models never approve their own output."""
    def __init__(self,name='codex',model=None,timeout=600,budget=None):
        if name not in ('codex','claude','gemini','fixture'):raise ContractError('Unknown provider')
        self.name,self.model,self.timeout,self.budget=name,model,timeout,budget
    @property
    def external(self):return self.name!='fixture'

    def fingerprint(self):return {'name':self.name,'model':self.model or 'installed-default','protocol':4}
    def ask(self,role,prompt,run_dir,fixture_dir=None,images=None):
        run_dir=Path(run_dir);base=run_dir/'provider_evidence'/role;base.mkdir(parents=True,exist_ok=True)
        index=len(list(base.glob('attempt-*')))+1;attempt=base/f'attempt-{index:03d}';attempt.mkdir()
        (attempt/'request.txt').write_text(redact(prompt))
        record={'provider':self.name,'model':self.model or 'installed-default','role':role,'request_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'started':time.time(),'returncode':None,'timed_out':False,'status':'STARTED'}
        write_json(attempt/'process.json',record)
        stdout=stderr='';cmd=[];reservation=None;started_process=False;quota=False
        try:
            if images and self.name not in ('codex','fixture'):raise ContractError('This optional adapter has no validated image transport; refusing to discard images')
            if self.name=='fixture':
                if fixture_dir is None:raise ContractError('Fixture directory missing')
                stdout=(Path(fixture_dir)/(role+'.json')).read_text();code=0;timed=False;result=stdout
            else:
                # Fail-closed: no external model process without an approved budget reservation.
                if self.budget is None:raise BudgetBlocked(BUDGET_BLOCKED,'no ResourceBudget attached to external provider')
                binary=shutil.which(self.name)
                if not binary:raise ContractError(f'Executable unavailable: {self.name}')
                # An explicitly chosen model is checked before any reservation or process (controlled abort).
                if self.model is not None:check_model(self.name,self.model)
                reservation=self.budget.reserve(role,prompt,len(images or []),self.name);record['budget_reservation']=reservation
                timeout=min(self.timeout,self.budget.remaining_seconds())
                if timeout<=0:raise BudgetBlocked(BUDGET_BLOCKED,'max_wall_seconds reached')
                if self.name=='codex':
                    cmd=[binary,'exec','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral','--sandbox','read-only','--json','-c','features.shell_tool=false','-c','features.apps=false','-c','features.skills=false','-c','features.plugins=false','-c','web_search="disabled"','-o',str((attempt/'answer.txt').resolve())]
                    for img in images or []:cmd+=['--image',str(Path(img).resolve())]
                    if self.model:cmd+=['--model',self.model]
                    cmd+=['-']
                elif self.name=='claude':
                    cmd=[binary,'--safe-mode','-p','--output-format','json','--tools','','--max-turns','1','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--disable-slash-commands','--setting-sources','','--no-session-persistence']
                    if self.model:cmd+=['--model',self.model]
                else:
                    cmd=[binary,'--output-format','json']
                    if self.model:cmd+=['--model',self.model]
                started_process=True
                code,stdout,stderr,timed=execute(cmd,redact(prompt),str(attempt),timeout)
                record.update(returncode=code,timed_out=timed)
                # Persist ALL streams before parsing or checking process success.
                (attempt/'stdout.txt').write_text(redact(stdout));(attempt/'stderr.txt').write_text(redact(stderr))
                if timed:raise ContractError('Process timeout')
                if code:raise ContractError(f'Process exited {code}; stdout/stderr retained')
                if self.name=='codex':
                    events=[]
                    for line in stdout.splitlines():
                        try:events.append(json.loads(line))
                        except ValueError:continue
                    record['usage']=[e.get('usage') for e in events if e.get('type')=='turn.completed']
                    forbidden=[e for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search')]
                    if forbidden:raise ContractError('Unexpected tool use in content-only model call')
                    if any(e.get('type') in ('error','turn.failed') for e in events):raise ContractError('Codex error event; see retained stdout')
                    result=(attempt/'answer.txt').read_text() if (attempt/'answer.txt').exists() else ''
                else:
                    envelope=json.loads(stdout)
                    if envelope.get('is_error'):raise ContractError('Provider error envelope')
                    result=envelope.get('result' if self.name=='claude' else 'response','')
                    record['usage']=envelope.get('usage',envelope.get('stats'))
            obj=extract_json(result)
            record.update(status='SUCCEEDED',returncode=0)
            (attempt/'response.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2))
            return obj
        except BudgetBlocked as e:
            record.update(status=e.state,error_type='BudgetBlocked',error=redact(e),classification=e.state)
            e.record.update(record);raise
        except ModelUnavailable as e:
            record.update(status=MODEL_UNAVAILABLE,error_type='ModelUnavailable',error=redact(e),classification=MODEL_UNAVAILABLE);raise
        except Exception as e:
            model_gone=started_process and bool(_MODEL_NOT_FOUND.search(stdout+'\n'+stderr))
            if model_gone:record['model_unavailable']=True
            quota=bool(re.search(r"you.ve hit your usage limit|insufficient_quota|usage limit reached|quota exceeded|rate.?limit",stdout+'\n'+stderr,re.I))
            record.update(status='FAILED',error_type=type(e).__name__,error=redact(e),classification=MODEL_UNAVAILABLE if model_gone else 'USAGE_LIMIT' if quota else 'TIMEOUT' if record['timed_out'] else 'PROCESS_OR_PROTOCOL_ERROR')
            raise ProviderError(f'{self.name}/{role}: {redact(e)}; evidence: {attempt}',record) from e
        except BaseException as e:
            record.update(status='INTERRUPTED',error_type=type(e).__name__,classification='INTERRUPTED');raise
        finally:
            if reservation is not None:
                if not started_process:self.budget.release(reservation,'process not started')
                else:
                    usage=normalize_usage(self.name,record.get('usage')) if 'usage' in record else None
                    record['usage_status']=self.budget.commit(reservation,usage,'SUCCEEDED' if record['status']=='SUCCEEDED' else record['status'],quota=quota,
                                                              block_reason='provider reported the requested model as unavailable' if record.get('model_unavailable') else None)
                    record['usage_normalized']=usage
            if not (attempt/'stdout.txt').exists():(attempt/'stdout.txt').write_text(redact(stdout))
            if not (attempt/'stderr.txt').exists():(attempt/'stderr.txt').write_text(redact(stderr))
            record.update(finished=time.time(),duration_seconds=time.time()-record['started'],argv=cmd)
            write_json(attempt/'process.json',record)


AGENT_TURN_REQUIRED='AGENT_TURN_REQUIRED'


class CallLedger:
    """Fixed, auditable budget of NEW agent answers for a campaign (EXAM_MASTERY_CALL_LEDGER=<json path>).
    An answer is counted once, by its sha256: replaying a byte-identical answer in a later run costs nothing.
    At the limit the engine neither consumes a new answer nor asks for one (BUDGET_BLOCKED); raising the limit is
    an owner decision written into the ledger file, never done by the engine."""
    def __init__(self,path):
        self.path=Path(path)
        self.d=json.loads(self.path.read_text()) if self.path.exists() else {'schema':'em-call-ledger-v1','limit':0,'calls':[]}
    @classmethod
    def from_env(cls):
        p=os.environ.get('EXAM_MASTERY_CALL_LEDGER')
        return cls(p) if p else None
    def _save(self):
        tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.d,indent=1,ensure_ascii=False));tmp.replace(self.path)
    def used(self):return len(self.d['calls'])
    def check_open(self,role):
        if self.used()>=int(self.d.get('limit',0)):
            raise BudgetBlocked(BUDGET_BLOCKED,f'campaign call budget exhausted ({self.used()}/{self.d.get("limit")}); {role} not requested',{'role':role})
    def consume(self,role,run_dir,answer_sha,prompt_sha):
        if answer_sha in set(self.d.get('pre_campaign_answers') or []) or any(c['answer_sha256']==answer_sha for c in self.d['calls']):
            self.d.setdefault('replays',[]).append({'role':role,'run':str(run_dir),'answer_sha256':answer_sha,'at':time.strftime('%Y-%m-%dT%H:%M:%S')})
            self.d['replays']=self.d['replays'][-500:];self._save();return False
        self.check_open(role)
        self.d['calls'].append({'n':self.used()+1,'role':role,'run':str(run_dir),'course':os.environ.get('EXAM_MASTERY_CAMPAIGN_COURSE',''),
                                'prompt_sha256':prompt_sha,'answer_sha256':answer_sha,'at':time.strftime('%Y-%m-%dT%H:%M:%S')})
        self._save();return True

class AgentProvider:
    """B8: the calling agent (e.g. Claude Code running the skill) answers the model roles itself; no second model
    process. ask() returns the agent's answer if it exists for exactly this prompt; otherwise it writes the prompt and
    stops the run cleanly (resumable, like a quota stop). Running the same command again continues from there."""
    name='agent';model='calling-agent';external=False;budget=None
    def fingerprint(self):return {'name':'agent','model':'calling-agent','protocol':4}
    def ask(self,role,prompt,run_dir,fixture_dir=None,images=None):
        io=Path(run_dir)/'agent_io';io.mkdir(parents=True,exist_ok=True)
        key=hashlib.sha256(prompt.encode()).hexdigest()[:16]
        ans,req=io/f'{role}-{key}.answer.json',io/f'{role}-{key}.prompt.txt'
        led=CallLedger.from_env()
        if ans.exists():
            obj=extract_json(ans.read_text())
            if led:led.consume(role,run_dir,hashlib.sha256(ans.read_bytes()).hexdigest(),hashlib.sha256(prompt.encode()).hexdigest())
            ev=Path(run_dir)/'provider_evidence'/role;ev.mkdir(parents=True,exist_ok=True)
            write_json(ev/f'agent-{key}.json',{'provider':'agent','role':role,'request_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                                                'answer_sha256':hashlib.sha256(ans.read_bytes()).hexdigest(),'answer_file':str(ans)})
            return obj
        if led:led.check_open(role)
        req.write_text(prompt)
        write_json(io/'NEXT.json',{'role':role,'prompt_file':str(req),'answer_file':str(ans),'images':[str(i) for i in images or []],
                                   'instructions':'Answer the prompt exactly as the role demands: one JSON object, written to answer_file. '
                                                  'Then run the same exam-mastery command again.'})
        raise BudgetBlocked(AGENT_TURN_REQUIRED,f'{role} needs the calling agent: read {req}, write the JSON answer to {ans}, run the same command again')
    def discard(self,role,run_dir,reason):
        """A stage gate rejected this role's answer: move it aside so the next run asks again instead of replaying it."""
        io=Path(run_dir)/'agent_io';rej=io/'rejected';moved=[]
        for f in sorted(io.glob(f'{role}-*.answer.json')):
            rej.mkdir(exist_ok=True);dst=rej/f'{f.stem}-{time.time_ns()}.json';os.replace(f,dst);moved.append(dst.name)
        if moved:write_json(rej/f'{role}-{time.time_ns()}.reason.json',{'role':role,'reason':reason,'moved':moved})
        return moved
