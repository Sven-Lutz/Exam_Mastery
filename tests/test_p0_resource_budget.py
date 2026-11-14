"""P0 resource-control regressions. Offline only: providers are mocks or fake shell
binaries in a private PATH. No real model CLI can be reached (asserted per test)."""
import json,os,signal,tempfile,threading,time,unittest,multiprocessing
from pathlib import Path
from unittest.mock import patch
from exam_mastery.budget import ResourceBudget,BudgetBlocked,normalize_usage,BUDGET_BLOCKED,QUOTA_BLOCKED
from exam_mastery.providers import Provider,ProviderError,ACTIVE_GROUPS,group_alive
from exam_mastery.checkpoints import Checkpoints
from exam_mastery.common import ContractError

def cfg(**kw):
    base={'approval_id':'a1','max_requests':10,'max_input_tokens':10**6,'max_output_tokens':10**6,'max_wall_seconds':600,
          'max_retries':5,'max_input_tokens_per_call':10**5,'max_output_tokens_per_call':1000,'input_overhead_tokens_per_call':0,'image_input_tokens':0}
    base.update(kw);return base

def codex_ok(usage=None,answer='{"ok":true}'):
    """Fake execute() for Provider('codex'): writes answer file, returns JSONL events."""
    def fake(cmd,prompt,cwd,timeout):
        Path(cmd[cmd.index('-o')+1]).write_text(answer)
        events=[{'type':'turn.completed','usage':usage}] if usage is not None else [{'type':'thread.started'}]
        return 0,'\n'.join(json.dumps(e) for e in events),'',False
    return fake

USAGE={'input_tokens':100,'cached_input_tokens':40,'output_tokens':10}

class Offline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
        self.which=patch('exam_mastery.providers.shutil.which',return_value='/offline/fake-codex');self.which.start()
    def tearDown(self):self.which.stop();self.tmp.cleanup()
    def provider(self,budget,name='codex',**kw):return Provider(name,budget=budget,**kw)
    def budget(self,**kw):return ResourceBudget(cfg(**kw),self.d/'budget')

class BudgetLimits(Offline):
    def test_unbudgeted_external_provider_never_executes(self):
        with patch('exam_mastery.providers.execute') as ex:
            with self.assertRaises(BudgetBlocked):Provider('codex').ask('r','x',self.d)
            ex.assert_not_called()
    def test_exact_limit_1_10_1000_calls(self):
        for n in (1,10,1000):
            with self.subTest(n=n),tempfile.TemporaryDirectory() as d:
                b=ResourceBudget(cfg(max_requests=n,max_retries=0),Path(d)/'b');p=self.provider(b)
                with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE)) as ex:
                    for i in range(n):p.ask(f'r{i}','x',d)
                    with self.assertRaises(BudgetBlocked) as e:p.ask('extra','x',d)
                    self.assertEqual(ex.call_count,n)   # exactly at the limit: 0 further calls
                self.assertEqual(e.exception.state,BUDGET_BLOCKED)
                s=b.summary();self.assertEqual(s['requests'],n);self.assertEqual(s['state'],BUDGET_BLOCKED)
                self.assertEqual(s['input_tokens'],100*n);self.assertEqual(s['cached_input_tokens'],40*n)
    def test_worst_case_input_and_output_reserved_before_call(self):
        b=self.budget(max_input_tokens_per_call=50)
        with patch('exam_mastery.providers.execute') as ex:
            with self.assertRaises(BudgetBlocked):self.provider(b).ask('r','x'*51,self.d)
            ex.assert_not_called()
        b2=ResourceBudget(cfg(approval_id='a2',max_output_tokens=1005,max_output_tokens_per_call=1000),self.d/'budget')
        with patch('exam_mastery.providers.execute',side_effect=codex_ok({'input_tokens':1,'output_tokens':10})) as ex:
            self.provider(b2).ask('r1','x',self.d)
            with self.assertRaises(BudgetBlocked):self.provider(b2).ask('r2','x',self.d)  # 10+1000>1005
            self.assertEqual(ex.call_count,1)
    def test_overhead_and_images_count_in_worst_case(self):
        b=self.budget(input_overhead_tokens_per_call=30,image_input_tokens=1000)
        self.assertEqual(b.worst_case('abc',images=2)['input'],3+30+2000)
        self.assertEqual(b.worst_case('ä')['input'],2+30)  # UTF-8 bytes, not characters
    def test_invalid_or_missing_limits_fail_closed(self):
        for bad in ({},cfg(max_requests=0),cfg(max_input_tokens=None),cfg(max_retries=-1),cfg(approval_id=''),cfg(max_wall_seconds=float('inf')),cfg(max_requests=True),cfg(max_input_tokens_per_call=10**7)):
            with self.subTest(bad=bad),self.assertRaises(ContractError):ResourceBudget(bad,self.d/'x')
    def test_same_approval_with_changed_limits_refused(self):
        self.budget()
        with self.assertRaises(ContractError):self.budget(max_requests=11)
    def test_block_is_sticky_and_needs_new_approval(self):
        b=self.budget(max_requests=1);p=self.provider(b)
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE)) as ex:
            p.ask('r','x',self.d)
            with self.assertRaises(BudgetBlocked):p.ask('r2','x',self.d)
            with self.assertRaises(BudgetBlocked):self.provider(self.budget(max_requests=1)).ask('r3','x',self.d)  # reload same approval
            self.provider(ResourceBudget(cfg(approval_id='a2',max_requests=1),self.d/'budget')).ask('r3','x',self.d)
            self.assertEqual(ex.call_count,2)
    def test_wall_clock_limit(self):
        now=[1000.0];b=ResourceBudget(cfg(max_wall_seconds=10),self.d/'budget',clock=lambda:now[0])
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE)) as ex:
            self.provider(b).ask('r','x',self.d)
            self.assertLessEqual(ex.call_args[0][3],10)   # per-call timeout capped by remaining wall time
            now[0]+=10
            with self.assertRaises(BudgetBlocked):self.provider(b).ask('r2','x',self.d)
            self.assertEqual(ex.call_count,1)

class Usage(Offline):
    def test_cached_input_is_part_of_input_and_separate(self):
        self.assertEqual(normalize_usage('codex',[USAGE]),{'input':100,'cached_input':40,'cache_creation_input':0,'output':10})
        self.assertEqual(normalize_usage('claude',{'input_tokens':10,'cache_read_input_tokens':90,'cache_creation_input_tokens':5,'output_tokens':3}),
                         {'input':105,'cached_input':90,'cache_creation_input':5,'output':3})
    def test_unknown_usage_is_never_zero(self):
        for raw,prov in (([],'codex'),(None,'codex'),([{'input_tokens':5}],'codex'),({'foo':1},'claude'),({'input_tokens':1,'output_tokens':1},'gemini'),([{'input_tokens':1,'cached_input_tokens':9,'output_tokens':1}],'codex')):
            with self.subTest(raw=raw,prov=prov):self.assertIsNone(normalize_usage(prov,raw))
        b=self.budget(max_output_tokens_per_call=700)
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(None)):self.provider(b).ask('r','abcd',self.d)
        s=b.summary();self.assertEqual(s['input_tokens'],4);self.assertEqual(s['output_tokens'],700);self.assertEqual(s['usage_unknown_calls'],1)
    def test_claude_envelope_without_usage_charged_worst_case(self):
        b=self.budget(max_output_tokens_per_call=300)
        with patch('exam_mastery.providers.execute',return_value=(0,json.dumps({'result':'{"a":1}'}),'',False)):
            self.provider(b,'claude').ask('r','xy',self.d)
        self.assertEqual(b.summary()['output_tokens'],300)
    def test_actual_usage_above_reservation_blocks_further_calls(self):
        b=self.budget(max_output_tokens=2000,max_output_tokens_per_call=1000)
        with patch('exam_mastery.providers.execute',side_effect=codex_ok({'input_tokens':1,'output_tokens':2500})) as ex:
            self.provider(b).ask('r','x',self.d)
            with self.assertRaises(BudgetBlocked):self.provider(b).ask('r2','x',self.d)
            self.assertEqual(ex.call_count,1)
        s=b.summary();self.assertEqual(s['overrun_calls'],1);self.assertEqual(s['output_tokens'],2500)
    def test_quota_message_sets_quota_blocked(self):
        b=self.budget()
        with patch('exam_mastery.providers.execute',return_value=(1,"You've hit your usage limit",'',False)) as ex:
            with self.assertRaises(ProviderError) as e:self.provider(b).ask('r','x',self.d)
            self.assertEqual(e.exception.record['classification'],'USAGE_LIMIT')
            with self.assertRaises(BudgetBlocked) as e2:self.provider(b).ask('r2','x',self.d)
            self.assertEqual(ex.call_count,1)
        self.assertEqual(e2.exception.state,QUOTA_BLOCKED);self.assertEqual(b.summary()['usage_uncertain_calls'],1)
    def test_missing_binary_releases_reservation(self):
        b=self.budget()
        with patch('exam_mastery.providers.shutil.which',return_value=None):
            with self.assertRaises(ProviderError):self.provider(b).ask('r','x',self.d)
        s=b.summary();self.assertEqual(s['requests'],0);self.assertEqual(s['open_reservations'],0)
    def test_stale_reservation_of_crashed_process_is_charged(self):
        b=self.budget(max_output_tokens_per_call=50)
        rid=b.reserve('r','abc')
        state=json.loads(b.path.read_text());state['open_reservations'][rid]['pid']=2**22+7;b.path.write_text(json.dumps(state))
        b.recover_stale();s=b.summary()
        self.assertEqual((s['open_reservations'],s['input_tokens'],s['output_tokens'],s['usage_uncertain_calls']),(0,3,50,1))

def _proc_worker(ledger,results):
    b=ResourceBudget(cfg(max_requests=7,max_retries=1000),ledger);ok=0
    for i in range(10):
        try:b.reserve(f'p{os.getpid()}-{i}','x');ok+=1
        except BudgetBlocked:pass
    results.put(ok)

class Parallel(Offline):
    def test_parallel_thread_reservations_never_exceed_limit(self):
        b=self.budget(max_requests=10);ok=[];lock=threading.Lock()
        def worker(i):
            try:b.reserve(f'r{i}','x')
            except BudgetBlocked:return
            with lock:ok.append(i)
        ts=[threading.Thread(target=worker,args=(i,)) for i in range(60)];[t.start() for t in ts];[t.join() for t in ts]
        self.assertEqual(len(ok),10);self.assertEqual(b.summary()['requests'],10)
    def test_parallel_process_reservations_share_one_ledger(self):
        ctx=multiprocessing.get_context('spawn');q=ctx.Queue()
        ps=[ctx.Process(target=_proc_worker,args=(str(self.d/'budget'),q)) for _ in range(4)];[p.start() for p in ps];[p.join(60) for p in ps]
        self.assertEqual(sum(q.get(timeout=5) for _ in ps),7)

class Processes(unittest.TestCase):
    """Real subprocesses, but only fake shell scripts on an isolated PATH."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.bin=self.d/'bin';self.bin.mkdir()
        self.env=patch.dict(os.environ,{'PATH':f'{self.bin}:/bin:/usr/bin'});self.env.start()
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def fake(self,body):
        s=self.bin/'codex';s.write_text('#!/bin/sh\n'+body+'\n');s.chmod(0o700)
        import shutil;self.assertEqual(shutil.which('codex'),str(s))   # never a real model CLI
    def wait_dead(self,pid,secs=3):
        end=time.time()+secs
        while time.time()<end:
            try:os.kill(pid,0)
            except ProcessLookupError:return True
            time.sleep(0.05)
        return False
    def test_timeout_kills_child_and_grandchild(self):
        pidfile=self.d/'grandchild.pid'
        self.fake(f'cat >/dev/null; sleep 60 & echo $! > {pidfile}; sleep 60')
        b=ResourceBudget(cfg(max_output_tokens_per_call=77),self.d/'budget')
        with self.assertRaises(ProviderError) as e:Provider('codex',timeout=1,budget=b).ask('r','x',self.d)
        self.assertEqual(e.exception.record['classification'],'TIMEOUT')
        self.assertTrue(self.wait_dead(int(pidfile.read_text())));self.assertFalse(ACTIVE_GROUPS)
        s=b.summary();self.assertEqual(s['usage_uncertain_calls'],1);self.assertEqual(s['output_tokens'],77)
    def test_interrupt_kills_children_and_records_uncertain_usage(self):
        pidfile=self.d/'grandchild.pid'
        self.fake(f'cat >/dev/null; sleep 60 & echo $! > {pidfile}; sleep 60')
        b=ResourceBudget(cfg(),self.d/'budget')
        def interrupt():
            while not pidfile.exists():time.sleep(0.05)
            os.kill(os.getpid(),signal.SIGINT)
        threading.Thread(target=interrupt,daemon=True).start()
        with self.assertRaises(KeyboardInterrupt):Provider('codex',timeout=30,budget=b).ask('r','x',self.d)
        self.assertTrue(self.wait_dead(int(pidfile.read_text())));self.assertFalse(ACTIVE_GROUPS)
        s=b.summary();self.assertEqual(s['open_reservations'],0);self.assertEqual(s['usage_uncertain_calls'],1)
        rec=json.loads(next(self.d.rglob('process.json')).read_text());self.assertEqual(rec['status'],'INTERRUPTED')
    def test_terminate_all_children_stops_running_group(self):
        from exam_mastery.providers import execute,terminate_all_children
        pidfile=self.d/'gc.pid';self.fake(f'sleep 60 & echo $! > {pidfile}; sleep 60')
        result={}
        t=threading.Thread(target=lambda:result.update(r=execute([str(self.bin/'codex')],'',str(self.d),30)));t.start()
        while not pidfile.exists():time.sleep(0.05)
        groups=terminate_all_children(grace=1);t.join(10)
        self.assertEqual(len(groups),1);self.assertFalse(group_alive(groups[0]));self.assertTrue(self.wait_dead(int(pidfile.read_text())))
        self.assertFalse(t.is_alive())

class CheckpointResume(Offline):
    def validate(self,obj):
        if obj.get('ok') is not True:raise ContractError('bad')
    def test_resume_after_error_without_double_processing(self):
        b=self.budget();cp=Checkpoints(self.d/'unit')
        with patch('exam_mastery.providers.execute',return_value=(2,'','boom',False)):
            with self.assertRaises(ProviderError):cp.invoke('role','prompt',self.provider(b),self.validate)
        self.assertEqual(json.loads((self.d/'unit/role.checkpoint.json').read_text())['status'],'FAILED')
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE)) as ex:
            self.assertEqual(cp.invoke('role','prompt',self.provider(b),self.validate),{'ok':True})
            self.assertEqual(cp.invoke('role','prompt',self.provider(b),self.validate),{'ok':True})  # cache hit
            self.assertEqual(ex.call_count,1)
        s=b.summary();self.assertEqual(s['requests'],2);self.assertEqual(s['retries'],1)
        self.assertEqual(json.loads((self.d/'unit/role.checkpoint.json').read_text())['status'],'SUCCEEDED')
    def test_max_retry_blocks_contract_repair_call(self):
        b=self.budget(max_retries=0);cp=Checkpoints(self.d/'unit')
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE,'{"ok":false}')) as ex:
            with self.assertRaises(BudgetBlocked):cp.invoke('role','prompt',self.provider(b),self.validate)
            self.assertEqual(ex.call_count,1)
        rec=json.loads((self.d/'unit/role.checkpoint.json').read_text())
        self.assertEqual(rec['status'],BUDGET_BLOCKED);self.assertTrue(rec['resumable'])
    def test_blocked_preflight_leaves_existing_checkpoint_untouched(self):
        b=self.budget(max_requests=1);cp=Checkpoints(self.d/'unit')
        with patch('exam_mastery.providers.execute',side_effect=codex_ok(USAGE)):cp.invoke('a','p',self.provider(b),self.validate)
        before={p.name:p.read_bytes() for p in (self.d/'unit').rglob('*') if p.is_file() and p.name!='events.jsonl'}
        with patch('exam_mastery.providers.execute') as ex:
            with self.assertRaises(BudgetBlocked):cp.invoke('a','changed prompt',self.provider(b),self.validate)
            ex.assert_not_called()
        after={p.name:p.read_bytes() for p in (self.d/'unit').rglob('*') if p.is_file() and p.name!='events.jsonl'}
        self.assertEqual(before,after)
    def test_unbudgeted_external_provider_refused_by_checkpoints(self):
        with patch('exam_mastery.providers.execute') as ex:
            with self.assertRaises(BudgetBlocked):Checkpoints(self.d/'u').invoke('a','p',Provider('codex'),self.validate)
            ex.assert_not_called()
        self.assertFalse((self.d/'u/a.checkpoint.json').exists())

class RuntimeStops(Offline):
    def fixtures(self):
        root=self.d/'source';root.mkdir(exist_ok=True);(root/'lecture.md').write_text('Synthetic, subject-neutral fixture')
        def build(root,out,cache):
            manifest={'sources':[],'online_sources':[]};units=[{'id':'u1','segments':[{'id':'s1'}]},{'id':'u2','segments':[{'id':'s2'}]}]
            (out/'source_manifest.json').write_text(json.dumps(manifest));(out/'work_units.json').write_text(json.dumps(units));(out/'corpus.sqlite3').write_bytes(b'x')
            return manifest,units
        return root,build
    def go(self,root,build,produce,budget_config,provider=None):
        from exam_mastery.runtime import run
        with patch('exam_mastery.runtime.build',side_effect=build),patch('exam_mastery.runtime.produce_unit',side_effect=produce),patch('exam_mastery.runtime.engine_snapshot',return_value={'t':'stable'}):
            return run(root,provider or Provider('codex'),self.d/'output',budget_config)
    def test_external_run_without_budget_refused_before_any_output(self):
        from exam_mastery.runtime import run
        root,_=self.fixtures()
        with self.assertRaises(BudgetBlocked):run(root,Provider('codex'),self.d/'output')
        self.assertFalse((self.d/'output').exists())
    def test_budget_block_status_resume_marker_and_authorized_resume(self):
        root,build=self.fixtures();calls=[]
        def produce(root,manifest,unit,out,provider,course,plan_only=False):
            out.mkdir(parents=True,exist_ok=True)
            self.assertIsNotNone(provider.budget)
            raise BudgetBlocked(BUDGET_BLOCKED,'test limit')
        out,status=self.go(root,build,produce,cfg())
        self.assertEqual((status['status'],status['run_state']),('NO_GO',BUDGET_BLOCKED));self.assertTrue(status['resumable'])
        self.assertEqual(status['resume_marker']['run_dir'],out.name);self.assertFalse(status['resume_marker']['auto_restart'])
        self.assertEqual(status['child_processes']['alive_after_stop'],[]);self.assertIn('budget',status)
        self.assertEqual(json.loads((out/'status.json').read_text())['run_state'],BUDGET_BLOCKED)
        # Plain restart: refused, no new run directory, no work.
        dirs=set((self.d/'output').glob('course-*/*T*'))
        with self.assertRaises(BudgetBlocked) as e:self.go(root,build,produce,cfg(approval_id='a2'))
        self.assertEqual(e.exception.state,'RESUME_NOT_AUTHORIZED');self.assertEqual(set((self.d/'output').glob('course-*/*T*')),dirs)
        # Explicit consent + new approval: resumes the SAME run directory.
        def ok(root,manifest,unit,out,provider,course,plan_only=False):
            calls.append((unit['id'],plan_only));out.mkdir(parents=True,exist_ok=True)
            if plan_only:bp={'competencies':[],'units':[]};(out/'blueprint_namespaced.json').write_text(json.dumps(bp));return bp,None
            raise BudgetBlocked(BUDGET_BLOCKED,'stop again after planning')
        out2,s2=self.go(root,build,ok,cfg(approval_id='a2',authorize_resume_of=out.name))
        self.assertEqual(out2,out);self.assertTrue(s2['resumed']);self.assertEqual(calls,[('u1',True),('u2',True),('u1',False)])
        self.assertEqual(s2['run_state'],BUDGET_BLOCKED)
        approvals=[json.loads(l)['approval_id'] for l in (out/'budget/approvals.jsonl').read_text().splitlines()]
        self.assertEqual(approvals,['a1','a2'])
    def test_quota_stop_sets_quota_blocked(self):
        root,build=self.fixtures()
        def produce(root,manifest,unit,out,provider,course,plan_only=False):
            out.mkdir(parents=True,exist_ok=True)
            if plan_only:bp={'competencies':[],'units':[]};(out/'blueprint_namespaced.json').write_text(json.dumps(bp));return bp,None
            raise ProviderError('quota',{'classification':'USAGE_LIMIT'})
        _,status=self.go(root,build,produce,cfg())
        self.assertEqual(status['run_state'],QUOTA_BLOCKED);self.assertEqual(status['status'],'NO_GO')
    def test_sigterm_interrupt_is_clean_and_resumable(self):
        root,build=self.fixtures()
        def produce(root,manifest,unit,out,provider,course,plan_only=False):
            os.kill(os.getpid(),signal.SIGTERM);time.sleep(1);self.fail('signal not delivered')
        before=signal.getsignal(signal.SIGTERM)
        _,status=self.go(root,build,produce,cfg())
        self.assertEqual(status['run_state'],'INTERRUPTED');self.assertTrue(status['resumable']);self.assertEqual(signal.getsignal(signal.SIGTERM),before)
    def test_cli_requires_budget_and_rejects_bad_file(self):
        from exam_mastery.runtime import main
        root,_=self.fixtures()
        with patch('exam_mastery.runtime.build') as build:
            self.assertEqual(main([str(root)]),3)
            bad=self.d/'b.json';bad.write_text('{"approval_id":"x"}')
            self.assertEqual(main([str(root),'--budget',str(bad)]),2)
            build.assert_not_called()

if __name__=='__main__':unittest.main()
