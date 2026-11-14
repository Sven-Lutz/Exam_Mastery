"""One-path orchestration, safe automatic resume, complete coverage accounting."""
from pathlib import Path
import json,sys,os,fcntl,uuid,time,hashlib,shutil,traceback,copy,signal
from datetime import datetime,timezone
from .common import sha_file,write_json,ContractError
from .checkpoints import atomic,digest,Checkpoints
from .onepath_legacy import snapshot
from .providers import Provider,terminate_all_children,group_alive
from .budget import ResourceBudget,BudgetBlocked,load_budget_config,validate_config,BUDGET_BLOCKED,QUOTA_BLOCKED
from .corpus import build
from .production import produce_unit,required
from .publish import publish_all,publish_pdf
from .validate import check_blueprint,check_author,check_assess,check_cards,check_interaction,check_design,check_audit
ROOT=Path(__file__).resolve().parents[1]

def default_output_base():
    """B7: $EXAM_MASTERY_OUTPUT, else the dev checkout's historical run folder, else ~/Exam_Mastery_Output (installed)."""
    if os.environ.get('EXAM_MASTERY_OUTPUT'):return Path(os.environ['EXAM_MASTERY_OUTPUT']).expanduser()
    dev=ROOT.parent.parent/'runs_v0_5_1_p0_dev'
    return dev if (ROOT/'pyproject.toml').exists() and dev.is_dir() else Path.home()/'Exam_Mastery_Output'

def engine_snapshot():
    """Run identity = the code that runs: the exam_mastery package and pyproject.toml. Tests, caches (.pytest_cache),
    docs and notes are not part of it, so running the test suite never forces a new production run."""
    pkg=ROOT/'exam_mastery'
    files=[ROOT/'pyproject.toml'] if (ROOT/'pyproject.toml').exists() else []
    files+=[p for p in pkg.rglob('*') if p.is_file() and not any(x in ('__pycache__','.pytest_cache') for x in p.relative_to(ROOT).parts)
            and p.suffix!='.pyc' and p.name!='ENGINE_FREEZE.json' and not p.name.startswith('.')]
    return {str(p.relative_to(ROOT)):sha_file(p) for p in files}

def merged(models,course_id):
    bp={'title':models[0]['title'] if 'title' in models[0] else 'Exam Mastery — source-grounded course','domain_summary':'Integrated source-grounded units; review source and academic limitations.','knowledge_operations':[],'skills':[],'risk':'medium','competencies':[],'units':[],'interaction_choice':{'kind':'none','reason':'Individual interactive labs are included in unit products'},'course_id':course_id,'source_dispositions':[]}
    author={'claims':[],'sections':[],'limitations':[],'prerequisite_checks':[],'mathematics':[]};assess={'items':[]};cards={'cards':[],'not_needed_reason':'Retrieval suitability decided per competency'}
    for model in models:
        uid=model['unit_id'];bp['source_dispositions']+=model.get('source_dispositions',[]);bp['competencies']+=model['competencies'];bp['units']+=model['learning_units'];bp['knowledge_operations']+=list({c['operation'] for c in model['competencies']})
        for claim in model['claims']:
            c=copy.deepcopy(claim);c['local_id']=c['id'];c['id']=uid+':'+c['id'];author['claims'].append(c)
        author['sections']+=model['sections']
        author['mathematics']+=model.get('mathematics',[])
        author['prerequisite_checks']+=model['learning_plan'].get('prerequisite_checks',[])
        for item in model['assessments']:
            a=copy.deepcopy(item);a['id']=uid+':'+a['id'];assess['items'].append(a)
        for card in model['flashcards']:
            c=copy.deepcopy(card);c['id']=uid+':'+c['id'];cards['cards'].append(c)
        author['limitations']+=model.get('limitations',[])
    unique={};merged_cards=[]
    for card in cards['cards']:
        key=card['question'].strip().casefold()
        if key not in unique:unique[key]=card;merged_cards.append(card);continue
        existing=unique[key]
        if existing['answer'].strip().casefold()==card['answer'].strip().casefold():
            existing['source_refs']=sorted(set(existing['source_refs']+card['source_refs']))
            existing['competency_ids']=sorted(set(existing['competency_ids']+card['competency_ids']))
            existing.setdefault('merged_alias_ids',[]).append(card['id'])
            if card['explanation']!=existing['explanation']:existing['explanation']+='\n'+card['explanation']
        else:
            raise ContractError('Conflicting answers to an identical card prompt across units; global review required')
    cards['cards']=merged_cards
    return bp,author,assess,cards

class Interrupted(BaseException):
    """SIGTERM/SIGINT: stop cleanly, no further model calls, children terminated."""

def _external(provider):return getattr(provider,'external',False) is True

def _semantic_digest(decisions):
    """B6.2: semantic (link/order) decisions change the plan, so they belong to the run/resume identity."""
    if isinstance(decisions,(str,Path)):return sha_file(Path(decisions))
    return digest(getattr(decisions,'decisions',decisions))

def run(root,provider=None,output_base=None,budget_config=None):
    root=Path(root).expanduser().resolve()
    if not root.is_dir():raise ContractError('Source root is not accessible')
    provider=provider or Provider('codex')
    # Fail-closed: an external model provider never starts without explicit, valid limits.
    if _external(provider):
        if budget_config is None:raise BudgetBlocked(BUDGET_BLOCKED,'external provider requires an approved budget file (--budget)')
        budget_config=validate_config(budget_config)
    # Dev build writes to its own run base; never into earlier engines' run artifacts.
    base=Path(output_base) if output_base else default_output_base()
    if base==root or root in base.parents:base=Path.home()/'Exam_Mastery_v04_Output'
    if base==root or root in base.parents:raise ContractError('No output location outside source root')
    course_id='course-'+digest(str(root))[:12];course=base/course_id;course.mkdir(parents=True,exist_ok=True)
    with (course/'.run.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ContractError('Course already running; no concurrent writers allowed')
        before=snapshot(root);engine_before=engine_snapshot()
        if (ROOT/'ENGINE_FREEZE.json').exists() and json.loads((ROOT/'ENGINE_FREEZE.json').read_text())['files']!=engine_before:raise ContractError('Frozen engine integrity mismatch; start denied')
        identity=digest({'source':before,'engine':engine_before,'provider':provider.fingerprint()})
        pointer=course/'active.json';old=json.loads(pointer.read_text()) if pointer.exists() else {}
        if old.get('run_dir') and not Path(old['run_dir']).resolve().is_relative_to(course.resolve()):raise ContractError('Resume pointer escapes its course output directory')
        if old.get('identity')==identity and Path(old['run_dir']).exists() and json.loads((Path(old['run_dir'])/'status.json').read_text()).get('resumable'):
            out=Path(old['run_dir']);resumed=True
            # No silent auto-resume of model work: the owner must name this exact run.
            if _external(provider) and budget_config.get('authorize_resume_of')!=out.name:
                raise BudgetBlocked('RESUME_NOT_AUTHORIZED',f'resumable run {out.name} exists; set authorize_resume_of to resume it with a new approval_id')
        else:
            out=course/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir();resumed=False
        atomic(pointer,{'identity':identity,'run_dir':str(out)})
        status={'schema':'em-run-status-v4','version':'0.5.0','mode':'LEGACY_TRANSPORT_PACKAGES','status':'IN_PROGRESS','technical_status':'NOT_TESTED','academic_release':False,'resumable':True,'resumed':resumed,'source_root':str(root),'provider':provider.fingerprint(),'engine_sha256':digest(engine_before),'unit_failures':[],'limitations':[],'started':time.time(),'run_state':'RUNNING'}
        if (out/'status.json').exists():
            history=out/'status_history';history.mkdir(exist_ok=True);(history/(str(time.time_ns())+'.json')).write_bytes((out/'status.json').read_bytes())
        atomic(out/'status.json',status);atomic(out/'originals_before.json',before);atomic(out/'engine_snapshot.json',engine_before)
        budget=None
        if _external(provider):
            budget=ResourceBudget(budget_config,out/'budget');budget.recover_stale();provider.budget=budget
            approvals=out/'budget'/'approvals.jsonl'
            with approvals.open('a') as f:f.write(json.dumps({'time':time.time(),'approval_id':budget_config['approval_id'],'resumed':resumed})+'\n')
            status['budget']=budget.summary();atomic(out/'status.json',status)
        print(json.dumps({'run_dir':str(out),'resumed':resumed},ensure_ascii=False,sort_keys=True),flush=True)
        def _on_signal(signum,frame):raise Interrupted(f'signal {signum}')
        previous_handlers={}
        try:
            import threading
            if threading.current_thread() is threading.main_thread():
                for sig in (signal.SIGTERM,signal.SIGINT):previous_handlers[sig]=signal.signal(sig,_on_signal)
        except ValueError:pass
        try:
            if (out/'index.ready.json').exists():
                ready=json.loads((out/'index.ready.json').read_text())
                if all(sha_file(out/p)==h for p,h in ready['files'].items()):
                    manifest=json.loads((out/'source_manifest.json').read_text());units=json.loads((out/'work_units.json').read_text())
                else:raise ContractError('Corpus checkpoint integrity mismatch; evidence retained')
            else:
                manifest,units=build(root,out,course/'extraction_cache')
                atomic(out/'index.ready.json',{'files':{p:sha_file(out/p) for p in ('source_manifest.json','work_units.json','corpus.sqlite3')}})
            status['transport_units']=len(units);models=[];technical=[]
            status['final_audit_reached']=False
            def prepare_unit_checkpoint(unit):
                uout=out/'units'/unit['id']
                # Content-addressed completed units can migrate to a new corpus run.
                cache=course/'unit_cache'/digest(engine_before)/unit['id']
                if not uout.exists() and cache.exists():shutil.copytree(cache,uout)
                if not uout.exists():
                    previous=sorted((p for p in course.glob('*/units/'+unit['id']) if p!=uout and p.is_dir()),key=lambda p:p.stat().st_mtime,reverse=True)
                    if previous:
                        # Reuse only candidate per-role checkpoints. invoke() rechecks canonical
                        # source/prompt/provider/image hashes, output bytes and CURRENT validators.
                        origin=previous[0];uout.mkdir(parents=True)
                        for folder in ('stage_outputs','provider_evidence','checkpoint_history'):
                            if (origin/folder).exists():shutil.copytree(origin/folder,uout/folder)
                        for checkpoint in origin.glob('*.checkpoint.json'):shutil.copy2(checkpoint,uout/checkpoint.name)
                        atomic(uout/'inherited_checkpoints.json',{'origin':str(origin),'policy':'No trusted completed state: every role must pass current input/output hashes and current contract; exports, QA and rendered audits are rerun'})
                return uout,cache
            # The existing visual/architect roles first index the entire available course.
            # No author, assessment, card or publication stage precedes this barrier.
            index_report={'schema':'em-course-competency-index-v05','course_id':course_id,'source_manifest_sha256':sha_file(out/'source_manifest.json'),'total_transport_units':len(units),'planned_transport_units':[],'all_indexed_transport_units_planned':False,'source_scope_complete':bool(manifest.get('coverage_complete',False)),'complete':False,'competencies':[],'learning_units':[],'limitations':['A complete index of available material is not independent scientific clearance. Missing online/unreadable/visual material remains an explicit gap.']}
            initial_coverage={'indexed_segment_ids':[seg['id'] for unit in units for seg in unit['segments']],'processed_segment_ids':[],'failed_units':status['unit_failures'],'unavailable_sources':[src for src in manifest['sources'] if src['status'] not in ('extracted','ignored_metadata')],'unavailable_online':[src for src in manifest['online_sources'] if src['status']!='fetched'],'all_segments_processed':False}
            atomic(out/'production_coverage.json',initial_coverage)
            atomic(out/'course_competency_index.json',index_report)
            blueprints=[];status['planned_units']=0;status['completed_units']=0
            for position,unit in enumerate(units,1):
                uout,cache=prepare_unit_checkpoint(unit)
                print(f'PLAN {position}/{len(units)} {unit["id"]}',flush=True)
                try:blueprint,_=produce_unit(root,manifest,unit,uout,provider,course_id,plan_only=True)
                except Exception as error:
                    failure={'unit_id':unit['id'],'phase':'planning','error':str(error),'error_type':type(error).__name__,'source_segment_ids':[seg['id'] for seg in unit['segments']]}
                    status['unit_failures'].append(failure);uout.mkdir(parents=True,exist_ok=True)
                    atomic(uout/'unit.status.json',{'status':'FAILED','resumable':True,**failure});(uout/'error_trace.txt').write_text(traceback.format_exc())
                    if getattr(error,'record',{}).get('classification')=='USAGE_LIMIT':status['provider_blocked']='USAGE_LIMIT'
                    atomic(out/'production_coverage.json',initial_coverage)
                    raise
                blueprints.append(blueprint)
                index_report['planned_transport_units'].append({'id':unit['id'],'blueprint':'units/'+unit['id']+'/blueprint_namespaced.json','sha256':sha_file(uout/'blueprint_namespaced.json'),'competency_count':len(blueprint.get('competencies',[]))})
                status['planned_units']=position;atomic(out/'status.json',status)
                atomic(out/'course_competency_index.json',index_report)
            index_report['all_indexed_transport_units_planned']=True
            index_report['complete']=index_report['source_scope_complete']
            index_report['competencies']=[competency for blueprint in blueprints for competency in blueprint.get('competencies',[])]
            index_report['learning_units']=[unit for blueprint in blueprints for unit in blueprint.get('units',[])]
            index_report['source_dispositions']=[item for blueprint in blueprints for item in blueprint.get('source_dispositions',[])]
            atomic(out/'course_competency_index.json',index_report)
            for index,unit in enumerate(units):
                uout=out/'units'/unit['id'];print(f'UNIT {index+1}/{len(units)} {unit["id"]}',flush=True)
                uout,cache=prepare_unit_checkpoint(unit)
                try:
                    model,qa=produce_unit(root,manifest,unit,uout,provider,course_id)
                    model['title']=json.loads((uout/'architect.json').read_text())['title'];models.append(model);technical.append(qa['technical_status'])
                    atomic(uout/'unit.status.json',{'status':'COMPLETED','technical_status':qa['technical_status']})
                    if qa['technical_status']=='PASS' and not cache.exists():cache.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(uout,cache)
                except Exception as e:
                    failure={'unit_id':unit['id'],'error':str(e),'error_type':type(e).__name__,'source_segment_ids':[s['id'] for s in unit['segments']]};status['unit_failures'].append(failure)
                    atomic(uout/'unit.status.json',{'status':'FAILED','resumable':True,**failure});(uout/'error_trace.txt').write_text(traceback.format_exc())
                    if isinstance(e,BudgetBlocked) or getattr(e,'record',{}).get('classification') in ('USAGE_LIMIT',QUOTA_BLOCKED):
                        status['provider_blocked']=e.state if isinstance(e,BudgetBlocked) else 'USAGE_LIMIT'
                        status['limitations'].append('Resource budget or provider quota stop: remaining units not attempted; resume needs a new approval_id and authorize_resume_of.')
                        status['completed_units']=len(models);atomic(out/'status.json',status)
                        break
                status['completed_units']=len(models);atomic(out/'status.json',status)
            coverage={'indexed_segment_ids':[s['id'] for u in units for s in u['segments']],'processed_segment_ids':[sid for m in models for sid in m['source_segment_ids']],'failed_units':status['unit_failures'],'unavailable_sources':[s for s in manifest['sources'] if s['status'] not in ('extracted','ignored_metadata')],'unavailable_online':[u for u in manifest['online_sources'] if u['status']!='fetched']}
            coverage['all_segments_processed']=set(coverage['indexed_segment_ids'])==set(coverage['processed_segment_ids'])
            atomic(out/'production_coverage.json',coverage)
            if status.get('provider_blocked') in ('USAGE_LIMIT',BUDGET_BLOCKED,QUOTA_BLOCKED):raise ContractError('Global provider usage limit: no further model calls, including aggregate audits; same-path resume retained')
            if models:
                bp,author,assess,cards=merged(models,course_id)
                inter={'kind':'none','reason':'All justified labs live in unit web products','competency_ids':[]}
                design=models[0]['design']
                check_blueprint(bp,manifest);check_author(author,manifest);check_assess(assess,bp,manifest);check_cards(cards,bp,manifest);check_design(design)
                from .didactics import coverage_matrix,publish_support
                plan={'competency_methods':[r for m in models for r in m['learning_plan']['competency_methods']]}
                matrix=coverage_matrix(bp,assess,cards,plan)
                atomic(out/'competency_coverage.json',matrix)
                publish_all(bp,author,assess,cards,inter,design,out)
                publish_support(out,matrix)
                from .editorial import figures,split_products
                records=figures(out,{'visuals':[v for m in models for v in m['learning_plan'].get('visuals',[])],'mathematics':author.get('mathematics',[])})
                from .publish import publish_cards
                publish_cards(bp,cards,design,out/'artifacts/anki',author.get('mathematics',[]),records)
                publish_pdf(bp,author,assess,inter,design,out/'artifacts/learning_package.pdf',records);split_products(out)
                for name,obj in [('architect',bp),('author',author),('assessment',assess),('cards',cards),('interaction',inter),('design',design)]:atomic(out/(name+'.json'),obj)
                # Course audit uses hierarchical summaries, never truncates the corpus.
                summaries=[{**{k:v for k,v in m.items() if k!='audits'},'source_evidence':next(u['segments'] for u in units if u['id']==m['unit_id'])} for m in models]
                cp=Checkpoints(out);reviews=[]
                for offset in range(0,len(summaries),4):
                    batch=summaries[offset:offset+4]
                    prompt='ROLE: course coverage auditor. Check supplied unit claims, prerequisites, source conflicts and coverage honestly. Flag contradictory claims across units; do not silently choose a source as authoritative. Do not use tools or infer unseen material. Return JSON {"verdict":"PASS|FAIL|NEEDS_REVIEW","findings":[{"severity":"blocker|major|minor|info","description":"...","object_id":"...","source_refs":[]}],"reviewed_unit_ids":["exact unit ID"],"limitations":["..."]}. PASS requires no major/blocker findings and all supplied units reviewed.\n'+json.dumps({'units':batch,'coverage_summary':{'all_segments_processed':coverage['all_segments_processed'],'failed_units':coverage['failed_units'],'unavailable_source_count':len(coverage['unavailable_sources']),'unavailable_online_count':len(coverage['unavailable_online'])}},ensure_ascii=False,sort_keys=True)
                    def validate_audit(x,batch=batch):
                        required(x,['verdict','findings','reviewed_unit_ids','limitations'])
                        if set(x['reviewed_unit_ids'])!={m['unit_id'] for m in batch}:raise ContractError('Course audit must review every supplied unit')
                        if x['verdict'] not in ('PASS','FAIL','NEEDS_REVIEW'):raise ContractError('Invalid audit verdict')
                        if x['verdict']=='PASS' and any(f['severity'] in ('major','blocker') for f in x['findings']):raise ContractError('Audit PASS contradicts severe findings')
                    reviews.append(cp.invoke('course_audit_'+str(offset//4),prompt,provider,validate_audit))
                all_audits=[a for m in models for a in m['audits']]
                combined={'verdict':'FAIL' if any(a['verdict']=='FAIL' for a in all_audits) else 'NEEDS_REVIEW','findings':[f for a in all_audits for f in a['findings']],'reviewed_competencies':[c['id'] for c in bp['competencies']],'unverified_claims':[c for a in all_audits for c in a['unverified_claims']]}
                atomic(out/'audit.json',combined);atomic(out/'course_audit.json',reviews)
                atomic(out/'learning_model.json',{'schema':'em-learning-model-v4','engine_version':'0.5.0','course_id':course_id,'source_manifest_sha256':sha_file(out/'source_manifest.json'),'units':models,'competencies':bp['competencies'],'coverage':coverage,'course_audit':reviews,'interactions':[inter]})
                from .quality import quality
                qa=quality(out);technical.append(qa['technical_status'])
                from .layout_review import inspect_layout
                layout_reviews=inspect_layout(out,cp,provider)
                if any(a['verdict']=='FAIL' or any(f['severity'] in ('major','blocker') for f in a['findings']) for a in layout_reviews):technical.append('FAIL')
                qa['rendered_page_audits']=layout_reviews;atomic(out/'quality_report.json',qa)
                severe=any(f['severity'] in ('major','blocker') for a in all_audits+reviews+layout_reviews for f in a['findings'])
                incomplete=not coverage['all_segments_processed'] or bool(coverage['unavailable_sources'] or coverage['unavailable_online'])
                status.update(technical_status='PASS' if all(x=='PASS' for x in technical) and not status['unit_failures'] else 'FAIL',academic_status='NO_GO' if severe or incomplete else 'REVIEW_REQUIRED',status='NO_GO' if severe or incomplete or status['unit_failures'] or 'FAIL' in technical else 'REVIEW_REQUIRED',completed_units=len(models),final_audit_reached=True)
                create_portal(out,models)
            else:status.update(status='NO_GO',technical_status='FAIL',academic_status='NOT_TESTED',final_audit_reached=False)
            status['resumable']=bool(status['unit_failures']);status['run_state']='COMPLETE' if not status['unit_failures'] else 'FAILED'
        except BaseException as e:
            terminate_all_children()
            blocked=e.state if isinstance(e,BudgetBlocked) else QUOTA_BLOCKED if getattr(e,'record',{}).get('classification')=='USAGE_LIMIT' or status.get('provider_blocked')=='USAGE_LIMIT' else status.get('provider_blocked') if status.get('provider_blocked') in (BUDGET_BLOCKED,QUOTA_BLOCKED) else None
            interrupted=isinstance(e,(Interrupted,KeyboardInterrupt))
            state=blocked or ('INTERRUPTED' if interrupted else 'FAILED')
            status.update(status='NO_GO',run_state=state,technical_status='FAIL',error=str(e),error_type=type(e).__name__,resumable=True);(out/'error_trace.txt').write_text(traceback.format_exc())
            if state!='FAILED':status['resume_marker']={'run_dir':out.name,'reason':state,'requires':['new approval_id','authorize_resume_of='+out.name],'auto_restart':False}
            if not isinstance(e,Exception) and not interrupted:raise
        finally:
            for sig,handler in previous_handlers.items():signal.signal(sig,handler)
            groups=terminate_all_children();status['child_processes']={'terminated_at_stop':groups,'alive_after_stop':[g for g in groups if group_alive(g)]}
            if budget is not None:status['budget']=budget.summary()
            status['originals_unchanged']=snapshot(root)==before;status['engine_unchanged']=engine_snapshot()==engine_before
            if not status['originals_unchanged'] or not status['engine_unchanged']:status.update(status='NO_GO',technical_status='FAIL')
            status['finished']=time.time();atomic(out/'status.json',status)
            if not (out/'quality_report.json').exists():atomic(out/'quality_report.json',{'technical_status':'NOT_TESTED','academic_release':False,'blocker':status.get('error',status['unit_failures'])})
            qa=json.loads((out/'quality_report.json').read_text())
            qa.setdefault('technical_checks_status',qa.get('technical_status','NOT_TESTED'))
            qa.update(technical_status=status['technical_status'],pipeline_status=status['status'],academic_release=False,originals_unchanged=status['originals_unchanged'],engine_unchanged=status['engine_unchanged'])
            atomic(out/'quality_report.json',qa)
            atomic(out/'run_manifest.json',{'version':'0.5.0','identity':identity,'files':{str(p.relative_to(out)):sha_file(p) for p in out.rglob('*') if p.is_file() and p.name!='run_manifest.json'}})
        print(json.dumps(status,ensure_ascii=False,indent=2),flush=True);return out,status

def create_portal(out,models):
    import html
    links=''.join('<li><a href="units/'+m['unit_id']+'/artifacts/web/index.html">'+html.escape(m['title'])+'</a></li>' for m in models)
    (out/'START.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Exam Mastery</title><style>body{font:18px/1.6 system-ui;max-width:70ch;margin:auto;padding:24px;overflow-wrap:anywhere}a{color:#154b73}</style><h1>Exam Mastery — Lernprodukte</h1><p>Fachliche Freigabe und Quellenlücken stehen im Qualitätsbericht. Technischer Export ist keine fachliche Freigabe.</p><p><a href="artifacts/learning_package.pdf">Lehrbuch, Aufgaben und Lösungen (PDF)</a> · <a href="artifacts/anki/Anki_Karten.apkg">Anki</a></p><h2>Einheiten mit Labs und Feedback</h2><ul>'+links+'</ul></html>')

def _base(root,output_base):
    base=Path(output_base) if output_base else default_output_base()
    if base==root or root in base.parents:base=Path.home()/'Exam_Mastery_v04_Output'
    if base==root or root in base.parents:raise ContractError('No output location outside source root')
    return base

def _plan_cache_key(root,before,engine_before,decisions,only_chapter,overlay,rdecs):
    """Everything plan_dry_run reads: the source snapshot, the engine code, the run arguments and the course-level
    files outside the source root (visual evidence, course profile, ...). Any change -> a different key -> re-plan."""
    from .incremental import course_dir
    cdir=course_dir(root)
    # resume pointers (active_chapters*.json) are rewritten by every run and are not planning inputs
    side={p.name:sha_file(p) for p in sorted(cdir.glob('*.json')) if not p.name.startswith('active_chapters')} if cdir.is_dir() else {}
    return digest({'schema':'em-plan-cache-v1','source':before,'engine':engine_before,'only_chapter':only_chapter,
                   'decisions':_semantic_digest(decisions) if decisions is not None else None,
                   'overlay':overlay[1] if overlay is not None else None,'review_decisions':rdecs[1] if rdecs is not None else None,
                   'course_files':side})

def _cached_plan(plan_dry_run,root,out,before,engine_before,decisions,only_chapter,overlay,rdecs):
    """Resume without re-extracting and re-planning the whole course when nothing it depends on changed.
    The cache lives in the run's own plan folder; the gates are recomputed identically, never relaxed."""
    import pickle
    key=_plan_cache_key(root,before,engine_before,decisions,only_chapter,overlay,rdecs)
    # course-level: a new run of the same course and scope reuses the plan of an earlier run with identical inputs
    cdir=out.parent/'.plan_cache';cache=cdir/(key[:32]+'.pkl');t=time.time()
    if cache.exists():
        try:
            stored=pickle.loads(cache.read_bytes())
            src=Path(stored.get('plan_dir',''))
            if stored.get('key')==key and src.is_dir():
                dst=out/'plan'
                if src.resolve()!=dst.resolve():
                    dst.mkdir(parents=True,exist_ok=True)
                    for f in src.iterdir():
                        if f.is_file() and not (dst/f.name).exists():shutil.copy2(f,dst/f.name)
                return (*stored['value'],{'result':'HIT','key':key[:16],'seconds':round(time.time()-t,2),'from':src.parent.name})
        except Exception:pass
    value=plan_dry_run(root,out/'plan',decisions,only_chapter=only_chapter,review_overlay=overlay,review_decisions=rdecs)
    try:
        cdir.mkdir(exist_ok=True)
        tmp=cache.with_suffix('.tmp');tmp.write_bytes(pickle.dumps({'key':key,'value':value,'plan_dir':str(out/'plan')}));os.replace(tmp,cache)
    except Exception:pass
    return (*value,{'result':'MISS','key':key[:16],'seconds':round(time.time()-t,2)})

def run_chapters(root,provider=None,output_base=None,budget_config=None,decisions=None,dry_run=False,out_dir=None,only_chapter=None,review_overlay=None,review_decisions=None,mode='pilot'):
    """P3 standard path: inventory -> curriculum -> chapter plan -> fidelity gate -> per-chapter editorial production.
    Same P0 guarantees as run(): fail-closed budget before anything, single writer lock, authorized resume only,
    originals/engine snapshots, signal handling and child cleanup. No transport-unit role chain."""
    from .chapters import dry_run as plan_dry_run, select_chapter, ChapterSelectionError, production_preflight, production_preflight_auto, PilotReviewOpen
    if mode not in ('pilot','production'):raise ContractError(f'unknown run mode {mode!r}')
    if only_chapter is not None and (not isinstance(only_chapter,str) or not only_chapter.strip()):
        raise ChapterSelectionError('CHAPTER_ID_EMPTY','an exact chapter_id from the current plan is required')
    from .production import produce_chapter
    root=Path(root).expanduser().resolve()
    if not root.is_dir():raise ContractError('Source root is not accessible')
    from .review_overlay import load as review_load,evaluate as review_evaluate
    overlay=review_load(review_overlay,root) if review_overlay is not None else None  # refuses an overlay inside the source root
    from .review_decisions import load as rdec_load
    rdecs=rdec_load(review_decisions,root) if review_decisions is not None else None  # refuses decisions inside the source root
    base=_base(root,output_base);course_id='course-'+digest(str(root))[:12];course=base/course_id
    if dry_run:
        if provider is not None:raise ContractError('dry run never uses a provider')
        out=Path(out_dir) if out_dir else course/('dryrun-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6])
        before=snapshot(root);report,dplan,dmanifest,dgates,_=plan_dry_run(root,out,decisions,only_chapter=only_chapter,review_overlay=overlay,review_decisions=rdecs)
        # B7: what `start <folder>` (product mode) would produce, next to the pilot preflight
        from .auto_scope import apply as auto_scope_apply,coverage_report
        ag=auto_scope_apply(dplan,dmanifest,dgates)
        ppf=production_preflight_auto(dplan,ag,[c['chapter_id'] for c in dplan['chapters'] if ag[c['chapter_id']]['status'] not in ('BLOCKED','REVIEW_REQUIRED')])
        rows=coverage_report(dplan,dmanifest,dgates,ag);atomic(Path(out)/'competency_scope.json',rows)
        from collections import Counter as _C
        report['product_preflight']={'result':ppf['result'],'producible_chapters':len(ppf['producible_chapters']),
            'escalated':{k:[o['code'] for o in v['escalations']] for k,v in ppf['chapters'].items() if v['escalations']},
            'competencies':dict(_C(r['category'] for r in rows)),'competencies_produced':sum(r['produced_after'] for r in rows)}
        report['originals_unchanged']=snapshot(root)==before;atomic(Path(out)/'dry_run_report.json',report)
        return Path(out),report
    provider=provider or Provider('codex')
    if _external(provider):
        if budget_config is None:raise BudgetBlocked(BUDGET_BLOCKED,'external provider requires an approved budget file (--budget)')
        budget_config=validate_config(budget_config)
        # B6.4: the chapter path never runs on an implicit provider default; checked before preflight, lock or run dir.
        from .providers import check_model
        check_model(getattr(provider,'name',None),getattr(provider,'model',None))
        # B6.1: fail-closed pilot preflight BEFORE any checkpoint, lock, resume pointer or run directory exists.
        # Plans into a throw-away directory outside the source root; a budget never clears an open review reason.
        import tempfile
        with tempfile.TemporaryDirectory(prefix='em-preflight-') as td:
            _,pplan,pmanifest,pgates,_=plan_dry_run(root,Path(td)/'plan',decisions,only_chapter=only_chapter,review_overlay=overlay,review_decisions=rdecs)
            if mode=='production':
                from .auto_scope import apply as auto_scope_apply
                pgates=auto_scope_apply(pplan,pmanifest,pgates)
            if only_chapter is not None:
                psel=select_chapter(pplan,pgates,only_chapter)
                if psel['gate'] in ('BLOCKED','REVIEW_REQUIRED'):raise ChapterSelectionError('SELECTED_CHAPTER_BLOCKED',f"{only_chapter} is {psel['gate']} by the fidelity gate: {psel['blocked_kcs']}; no generation")
                if psel['academic_pilot_eligibility']=='INELIGIBLE':raise ChapterSelectionError('SELECTED_CHAPTER_INELIGIBLE',f"{only_chapter} is INELIGIBLE: {psel['eligibility_reasons']}; no generation")
                targets=[only_chapter]
            else:targets=[c['chapter_id'] for c in pplan['chapters'] if pgates[c['chapter_id']]['status'] not in ('BLOCKED','REVIEW_REQUIRED')]
            if mode=='production':
                pf=production_preflight_auto(pplan,pgates,targets)
                if not pf['producible_chapters']:raise PilotReviewOpen({**pf,'result':'ESCALATION_REQUIRED'})
            else:
                pf=production_preflight(pplan,pgates,targets)
                if pf['result']!='CLEARED_EXPERIMENTAL_SCOPE':raise PilotReviewOpen(pf)
    course.mkdir(parents=True,exist_ok=True)
    with (course/'.run.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ContractError('Course already running; no concurrent writers allowed')
        before=snapshot(root);engine_before=engine_snapshot()
        if (ROOT/'ENGINE_FREEZE.json').exists() and json.loads((ROOT/'ENGINE_FREEZE.json').read_text())['files']!=engine_before:raise ContractError('Frozen engine integrity mismatch; start denied')
        scope={'mode':'ALL_CHAPTERS'} if only_chapter is None else {'mode':'ONLY_CHAPTER','chapter_id':only_chapter}
        identity=digest({'source':before,'engine':engine_before,'provider':provider.fingerprint(),'mode':'chapters',**({'scope':scope} if only_chapter is not None else {}),**({'review_overlay_sha256':overlay[1]} if overlay is not None else {}),**({'review_decisions_sha256':rdecs[1]} if rdecs is not None else {}),**({'semantic_decisions_sha256':_semantic_digest(decisions)} if decisions is not None else {})})
        # One resume pointer per scope: selecting another chapter never continues (or hides) a different scope's run.
        pointer=course/('active_chapters.json' if only_chapter is None else 'active_chapters-'+digest(scope)[:12]+'.json')
        old=json.loads(pointer.read_text()) if pointer.exists() else {}
        named=budget_config.get('authorize_resume_of') if budget_config else None
        if named and (course/named/'status.json').exists():
            prior=json.loads((course/named/'status.json').read_text()).get('scope',{'mode':'ALL_CHAPTERS'})
            if prior.get('mode')!=scope['mode'] or prior.get('chapter_id')!=scope.get('chapter_id'):
                raise BudgetBlocked('RESUME_SCOPE_MISMATCH',f'run {named} has scope {prior}; requested {scope}; refusing to continue it')
        if old.get('run_dir') and not Path(old['run_dir']).resolve().is_relative_to(course.resolve()):raise ContractError('Resume pointer escapes its course output directory')
        if old.get('identity')==identity and Path(old['run_dir']).exists() and json.loads((Path(old['run_dir'])/'status.json').read_text()).get('resumable'):
            out=Path(old['run_dir']);resumed=True
            if _external(provider) and named and named!=out.name:
                raise BudgetBlocked('RESUME_NOT_AUTHORIZED',f'authorize_resume_of={named} does not name the resumable run {out.name} of this scope')
            if _external(provider) and budget_config.get('authorize_resume_of')!=out.name:
                raise BudgetBlocked('RESUME_NOT_AUTHORIZED',f'resumable run {out.name} exists; set authorize_resume_of to resume it with a new approval_id')
        else:
            out=course/('ch-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir();resumed=False
        atomic(pointer,{'identity':identity,'run_dir':str(out)})
        status_prior_fp=json.loads((out/'status.json').read_text()).get('scope',{}).get('plan_fingerprint') if resumed and (out/'status.json').exists() else None
        status={'schema':'em-run-status-v5','version':'0.5.1-p3','mode':'CHAPTERS','status':'IN_PROGRESS','technical_status':'NOT_TESTED','academic_release':'NOT_TESTED','resumable':True,'resumed':resumed,'source_root':str(root),'provider':provider.fingerprint(),'engine_sha256':digest(engine_before),'chapters':{},'chapter_failures':[],'started':time.time(),'run_state':'RUNNING','scope':scope,'chapters_analyzed':[],'selected_chapter_ids':[],'excluded_chapter_ids':[]}
        atomic(out/'status.json',status);atomic(out/'originals_before.json',before)
        budget=None
        if _external(provider):
            budget=ResourceBudget(budget_config,out/'budget');budget.recover_stale();provider.budget=budget
            with (out/'budget'/'approvals.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'approval_id':budget_config['approval_id'],'resumed':resumed})+'\n')
        def _on_signal(signum,frame):raise Interrupted(f'signal {signum}')
        previous_handlers={}
        try:
            import threading
            if threading.current_thread() is threading.main_thread():
                for sig in (signal.SIGTERM,signal.SIGINT):previous_handlers[sig]=signal.signal(sig,_on_signal)
        except ValueError:pass
        try:
            report,plan,manifest,gates,actions,plan_cache=_cached_plan(plan_dry_run,root,out,before,engine_before,decisions,only_chapter,overlay,rdecs)
            status['plan_cache']=plan_cache
            if mode=='production':
                # B7: text-only scope for competencies that only await a visual/neighbour-page review
                from .auto_scope import apply as auto_scope_apply,coverage_report
                gates_before_auto=gates;gates=auto_scope_apply(plan,manifest,gates)
                atomic(out/'plan'/'chapter_gates_product_mode.json',gates)
                atomic(out/'plan'/'competency_scope.json',coverage_report(plan,manifest,gates_before_auto,gates))
            review=review_evaluate(overlay,manifest,plan) if overlay is not None else None
            if overlay is not None:status['review_overlay']={'sha256':overlay[1],'counts':review['counts']}
            if rdecs is not None:status['review_decisions']={'sha256':rdecs[1],'counts':report['review_decisions']['counts'],'unlocked_kcs':report['review_decisions']['unlocked_kcs']}
            status['plan']={'readiness':report['readiness'],'planned_actions':report['planned_actions']}
            status['chapters_analyzed']=[c['chapter_id'] for c in plan['chapters']]
            selected=list(plan['chapters'])
            if only_chapter is not None:
                sel=select_chapter(plan,gates,only_chapter)  # raises ChapterSelectionError before any provider call
                fp=sel['plan_fingerprint']
                if resumed and status_prior_fp and status_prior_fp!=fp:
                    raise BudgetBlocked('RESUME_SCOPE_MISMATCH','selected chapter plan/sources changed since the interrupted run; start a new run')
                scope['plan_fingerprint']=fp;status['scope']=scope
                selected=[c for c in plan['chapters'] if c['chapter_id']==only_chapter]
                status['selected_chapter_ids']=[only_chapter];status['excluded_chapter_ids']=sel['excluded_chapter_ids']
                if sel['gate'] in ('BLOCKED','REVIEW_REQUIRED'):
                    raise ChapterSelectionError('SELECTED_CHAPTER_BLOCKED',f"{only_chapter} is {sel['gate']} by the fidelity gate: {sel['blocked_kcs']}; no generation")
                if sel['academic_pilot_eligibility']=='INELIGIBLE':
                    raise ChapterSelectionError('SELECTED_CHAPTER_INELIGIBLE',f"{only_chapter} is INELIGIBLE: {sel['eligibility_reasons']}; no generation")
            status['selected_chapter_ids']=[c['chapter_id'] for c in selected]
            status['excluded_chapter_ids']=[c['chapter_id'] for c in plan['chapters'] if c not in selected]
            cands=[c['chapter_id'] for c in selected if gates[c['chapter_id']]['status'] not in ('BLOCKED','REVIEW_REQUIRED')]
            pf=production_preflight_auto(plan,gates,cands) if mode=='production' else production_preflight(plan,gates,cands)
            status['mode_policy']=mode
            status['production_preflight']={'result':pf['result'],'chapters':{k:{'status':v['status'],'open':[o['code'] for o in v['open']],'cleared':[x['code'] for x in v['cleared']],
                                            **({'auto_resolved':[{'code':o['code'],'resolution':o['resolution'],**({'kc_id':o['kc_id']} if 'kc_id' in o else {}),**({'key':o['key']} if 'key' in o else {})} for o in v['auto_resolved']]} if 'auto_resolved' in v else {})} for k,v in pf['chapters'].items()},'enforced':_external(provider)}
            atomic(out/'status.json',status)
            if _external(provider):  # second line: sources changed since the pre-lock check
                if mode=='production' and not pf['producible_chapters']:raise PilotReviewOpen({**pf,'result':'ESCALATION_REQUIRED'})
                if mode=='pilot' and pf['result']!='CLEARED_EXPERIMENTAL_SCOPE':raise PilotReviewOpen(pf)
            escalated={k for k,v in pf['chapters'].items() if v['status']=='ESCALATED_HUMAN_DECISION_REQUIRED'} if mode=='production' else set()
            for c in selected:
                g=gates[c['chapter_id']]
                if c['chapter_id'] in escalated:
                    status['chapters'][c['chapter_id']]={'status':'ESCALATED_HUMAN_DECISION_REQUIRED','escalations':pf['chapters'][c['chapter_id']]['escalations']};continue
                if g['status'] in ('BLOCKED','REVIEW_REQUIRED'):
                    status['chapters'][c['chapter_id']]={'status':g['status'],'blocked_kcs':g['blocked_kcs'],'review_required_kcs':g.get('review_required_kcs',{})};continue
                try:
                    ast_,rep=produce_chapter(plan,manifest,c['chapter_id'],g,out/'chapters'/c['chapter_id'],provider,review)
                    status['chapters'][c['chapter_id']]={'status':ast_['status'],'gate':g['status'],'technical':rep['technical_status']}
                    if ast_['status']=='DRAFT_TECHNICAL_PASS_PENDING_REVIEW':
                        # B6.5: the standard chapter path publishes its learning products (deterministic, no model call).
                        from .chapter_publish import publish_chapter
                        try:
                            pr=publish_chapter(out/'chapters'/c['chapter_id'],manifest,plan)
                            status['chapters'][c['chapter_id']]['publish']={'status':'PUBLISHED_DRAFT','products':pr['products']}
                        except Exception as pe:
                            status['chapters'][c['chapter_id']].update(status='PUBLISH_FAILED',publish={'status':'FAILED','error':f'{type(pe).__name__}: {pe}'})
                            status['chapter_failures'].append({'chapter_id':c['chapter_id'],'error':'publish: '+str(pe),'error_type':type(pe).__name__})
                except Exception as e:
                    status['chapter_failures'].append({'chapter_id':c['chapter_id'],'error':str(e),'error_type':type(e).__name__})
                    # a planned budget stop (e.g. Stage 1 after chapter_author) is not a content failure
                    status['chapters'][c['chapter_id']]={'status':'BUDGET_STOPPED' if isinstance(e,BudgetBlocked) else 'FAILED'}
                    cdir=out/'chapters'/c['chapter_id']
                    if (cdir/'chapter_author.json').exists() and not (cdir/'content_ast.json').exists():
                        # B6.5 Stage 1: a stop after the author call still yields an inspectable, clearly labelled preview.
                        from .chapter_publish import publish_author_preview
                        try:status['chapters'][c['chapter_id']]['author_preview']=publish_author_preview(cdir,manifest,plan)['status']
                        except Exception as pe:status['chapters'][c['chapter_id']]['author_preview']=f'FAILED: {type(pe).__name__}: {pe}'
                    if isinstance(e,BudgetBlocked) or getattr(e,'record',{}).get('classification') in ('USAGE_LIMIT',QUOTA_BLOCKED):raise
                atomic(out/'status.json',status)
            states=[v['status'] for v in status['chapters'].values()]
            passed=all(x in ('DRAFT_TECHNICAL_PASS_PENDING_REVIEW','BLOCKED','REVIEW_REQUIRED') for x in states) and not status['chapter_failures']
            status.update(technical_status='PASS' if passed and any(x not in ('BLOCKED','REVIEW_REQUIRED') for x in states) else 'FAIL',
                          status='REVIEW_REQUIRED' if passed and report['readiness']=='READY_FOR_APPROVAL' else 'PARTIAL' if passed else 'NO_GO',
                          run_state='COMPLETE',resumable=bool(status['chapter_failures']))
        except BaseException as e:
            terminate_all_children()
            blocked=e.state if isinstance(e,BudgetBlocked) else QUOTA_BLOCKED if getattr(e,'record',{}).get('classification')=='USAGE_LIMIT' else None
            interrupted=isinstance(e,(Interrupted,KeyboardInterrupt))
            state=blocked or (e.state if isinstance(e,(ChapterSelectionError,PilotReviewOpen)) else 'INTERRUPTED' if interrupted else 'FAILED')
            status.update(status='NO_GO',run_state=state,technical_status='FAIL',error=str(e),error_type=type(e).__name__,resumable=True);(out/'error_trace.txt').write_text(traceback.format_exc())
            if isinstance(e,(ChapterSelectionError,PilotReviewOpen)):status['resumable']=False
            elif state!='FAILED':status['resume_marker']={'run_dir':out.name,'reason':state,'requires':['new approval_id','authorize_resume_of='+out.name],'auto_restart':False}
            if not isinstance(e,Exception) and not interrupted:raise
        finally:
            for sig,handler in previous_handlers.items():signal.signal(sig,handler)
            groups=terminate_all_children();status['child_processes']={'terminated_at_stop':groups,'alive_after_stop':[g for g in groups if group_alive(g)]}
            if budget is not None:status['budget']=budget.summary()
            status['originals_unchanged']=snapshot(root)==before;status['engine_unchanged']=engine_snapshot()==engine_before
            if not status['originals_unchanged'] or not status['engine_unchanged']:status.update(status='NO_GO',technical_status='FAIL')
            status['academic_release']='NOT_TESTED';status['finished']=time.time();atomic(out/'status.json',status)
        print(json.dumps(status,ensure_ascii=False,indent=2),flush=True);return out,status

USAGE=('Usage:\n'
       '  exam-mastery [/lecture/folder]            produce learning materials (default folder: the current directory)\n'
       '  exam-mastery status [/lecture/folder]     what is produced, whether sources changed (read-only)\n'
       '  exam-mastery course-title "Titel" [/lecture/folder]   title shown on covers (stored outside the lecture folder)\n'
       '  exam-mastery kb validate|summary|context <produkt>|spec <id>   Wissensbasis (Lernwissenschaft, offline)\n'
       '  exam-mastery tutor-brief <kontext.json>                     Tutor-Brief aus einer Lernstrecken-Kontextdatei (no model call)\n'
       '  exam-mastery lernstrecken <out_dir>                         build the three adaptive learning tracks (no model call)\n'
       '  exam-mastery recover-chapter <chapter-id> [/lecture/folder]   republish after a plan fix that only removed items (no model call)\n'
       '  exam-mastery update [/lecture/folder] [--produce]   offline change check; --produce regenerates only changed chapters (paid)\n'
       '  exam-mastery visuals [/lecture/folder] [--import evidence.json]   figure pages for the calling agent to read / import its reading\n'
       '  start --setup --provider gemini|codex --model <id> --accept-data-transfer [--max-cost-usd 5] [--key-file path] [--thinking-level low|medium|high]\n'
       '  start /lecture/folder                      product mode (uses the one-time setup)\n'
       '  start /lecture/root --dry-run [--out dir]  plan only, no provider call\n'
       '  start /lecture/root --budget budget.json [--provider gemini|codex] [--model <id>] [--only-chapter <id>] '
       '[--decisions d.json] [--review-overlay a.json] [--review-decisions d.json]   experimental audit pilot (human-signed scope)')

def main(argv=None):
    from .providers import ModelUnavailable as ModelUnavailableError
    args=list(sys.argv[1:] if argv is None else argv);opts={}
    if args and args[0] in ('-h','--help','help'):print(USAGE);return 0
    if args and args[0] in ('--version','-V','version'):
        from .common import version_info
        print(json.dumps(version_info(),ensure_ascii=False));return 0
    if args and args[0]=='kb':
        from .cli import kb_command
        return kb_command(args[1:])
    if args and args[0] in ('tutor-brief','lernstrecken'):
        # v0.18: learning engine (no model call): tutor brief from a context file, or the three adaptive tracks
        from .learning.__main__ import main as learning_main
        return learning_main(['build' if args[0]=='lernstrecken' else 'tutor-brief']+args[1:])
    if args and args[0]=='course-title':
        # B13: display title for covers, stored in the course output folder (never in the lecture folder)
        from . import incremental as inc
        if len(args)<2:print('Usage: exam-mastery course-title "Titel" [/lecture/folder]');return 2
        folder=args[2] if len(args)>2 else os.getcwd()
        if not inc.looks_like_course(folder):print(json.dumps({'status':'NOT_A_COURSE_FOLDER','folder':folder}));return 2
        d=inc.course_dir(folder);d.mkdir(parents=True,exist_ok=True);p=d/'course_profile.json'
        prof=json.loads(p.read_text()) if p.exists() else {};prof['course_title']=args[1];p.write_text(json.dumps(prof,ensure_ascii=False,indent=1))
        print(json.dumps({'status':'OK','course_title':args[1],'profile':str(p)},ensure_ascii=False));return 0
    if args.count('--only-chapter')>1:print(json.dumps({'status':'CHAPTER_ID_AMBIGUOUS','error':'--only-chapter given more than once'}));return 2
    for flag in ('--budget','--out','--decisions','--only-chapter','--review-overlay','--review-decisions','--model','--provider','--max-cost-usd','--key-file','--thinking-level'):
        if flag in args:
            i=args.index(flag)
            if i+1>=len(args):print(USAGE);return 2
            opts[flag]=args[i+1];del args[i:i+2]
    dry='--dry-run' in args;legacy='--legacy-packages' in args;setup_mode='--setup' in args;consent='--accept-data-transfer' in args
    args=[a for a in args if a not in ('--dry-run','--legacy-packages','--setup','--accept-data-transfer')]
    if setup_mode:
        from .product import setup
        try:
            pol={'max_cost_usd_per_run':float(opts['--max-cost-usd'])} if '--max-cost-usd' in opts else None
            p,cfg=setup(opts.get('--provider'),opts.get('--model'),consent,policy=pol,key_file=opts.get('--key-file'),thinking_level=opts.get('--thinking-level'))
            print(json.dumps({'status':'CONFIGURED','config':str(p),'provider':cfg['provider'],'model':cfg['model'],'usage_policy':cfg['usage_policy'],'notes':cfg['notes']},ensure_ascii=False,indent=2));return 0
        except Exception as e:print(json.dumps({'status':'SETUP_REFUSED','error':str(e)}));return 2
    if args and args[0]=='visuals' and '--import' not in opts:
        # B8: figure reading by the calling agent; offline
        from . import visual_evidence as vev, incremental as inc
        args.pop(0);imp=None
        if '--import' in args:i=args.index('--import');imp=args[i+1];del args[i:i+2]
        allp='--all' in args;args=[a for a in args if a!='--all']
        folder=args[0] if args else os.getcwd()
        if not inc.looks_like_course(folder):print(json.dumps({'status':'NOT_A_COURSE_FOLDER','folder':folder}));return 2
        try:
            if imp:print(json.dumps(vev.cmd_import(folder,imp),ensure_ascii=False,indent=2));return 0
            p,doc=vev.cmd_worklist(folder,include_all=allp)
            print(json.dumps({'worklist':str(p),'pages_to_read':len(doc['pages']),'provider_calls_made':0,'next':'read every image, fill evidence_template, then: exam-mastery visuals --import <file>'},ensure_ascii=False,indent=2));return 0
        except Exception as e:print(json.dumps({'status':'NO_GO','error':f'{type(e).__name__}: {e}'}));return 2
    if args and args[0]=='recover-chapter':
        # B14: deterministic scope-reduction recovery (no model call); refuses unless the plan change only removed ids
        from . import incremental as inc, scope_recovery as sr
        from .product import load_config,run_product
        args.pop(0)
        if not args or len(args)>2:print(USAGE);return 2
        cid=args[0];folder=args[1] if len(args)>1 else os.getcwd()
        try:
            r=inc.update(folder)
            if any((r.get('sources') or {}).get(k) for k in ('new','changed','removed')) or r.get('visual_evidence_stale'):
                print(json.dumps({'status':'NOT_RECOVERABLE','reason':'sources or figure readings changed; a production run is required','provider_calls_made':0},ensure_ascii=False));return 2
            src=sr.find_source_chapter(inc.course_dir(folder),cid)
            if src is None:
                print(json.dumps({'status':'NOT_RECOVERABLE','reason':'no earlier published run of this chapter with stored answers for all roles','provider_calls_made':0}));return 2
            pcfg=load_config()
            if pcfg is None:print(json.dumps({'status':BUDGET_BLOCKED,'reason':'NOT_CONFIGURED','provider_calls_made':0}));return 3
            prov=sr.ScopeRecoveryProvider(src)
            out,status,dossier=run_product(folder,pcfg,only_chapter=cid,provider=prov)
        except Exception as e:print(json.dumps({'status':'NO_GO','error':f'{type(e).__name__}: {e}','provider_calls_made':0}));return 2
        rec=Path(out)/'chapters'/cid/'scope_recovery.json'
        print(json.dumps({'status':status.get('status'),'run_state':status.get('run_state'),'release':dossier['release'],'dimensions':dossier['dimensions'],
                          'source_run':str(src),'scope_recovery':str(rec) if rec.exists() else None,'provider_calls_made':0},ensure_ascii=False,indent=2))
        if status.get('run_state')=='AGENT_TURN_REQUIRED' or not rec.exists():return 2
        return 0 if dossier['release']['technical']=='TECHNICAL_RELEASE_CANDIDATE' else 2
    if args and args[0] in ('status','update') and not os.sep in args[0]:
        # v0.11: incremental workflow; offline unless `update --produce`
        from . import incremental as inc
        sub=args.pop(0);produce='--produce' in args;args=[a for a in args if a!='--produce']
        if len(args)>1:print(USAGE);return 2
        folder=args[0] if args else os.getcwd()
        if not inc.looks_like_course(folder):
            print(json.dumps({'status':'NOT_A_COURSE_FOLDER','folder':str(Path(folder).expanduser().resolve()),'provider_calls_made':0,'next':f'exam-mastery {sub} "/path/to/lecture folder"'},ensure_ascii=False));return 2
        try:
            if sub=='status':print(json.dumps(inc.status(folder),ensure_ascii=False,indent=2,default=str));return 0
            r=inc.update(folder,produce=produce)
        except BudgetBlocked as e:print(json.dumps({'status':e.state,'error':str(e)}));return 3
        except Exception as e:print(json.dumps({'status':'NO_GO','error':f'{type(e).__name__}: {e}'}));return 2
        print(json.dumps({k:r.get(k) for k in ('sources','summary','to_produce','produce','produced','visual_evidence_stale','provider_calls_made','plan_dir')}|{'report':str(inc.course_dir(folder)/'update_check.json'),
                          'next':(None if not r['to_produce'] or produce else 'exam-mastery update --produce  (regenerates only these chapters; uses provider calls)')},ensure_ascii=False,indent=2,default=str))
        return 3 if r.get('produce') in (BUDGET_BLOCKED,QUOTA_BLOCKED,'NOT_CONFIGURED') else 2 if r.get('produce')=='FAILED' else 0
    if not args and not dry and not legacy:
        from .incremental import looks_like_course
        if not looks_like_course(os.getcwd()):
            print(json.dumps({'status':'NOT_A_COURSE_FOLDER','folder':os.getcwd(),'provider_calls_made':0,'next':'cd into the lecture folder or pass it: exam-mastery "/path/to/lecture folder"'},ensure_ascii=False));return 2
        args=[os.getcwd()]
    only=opts.get('--only-chapter')
    if legacy and '--review-decisions' in opts:
        print(json.dumps({'status':'INCOMPATIBLE_OPTIONS','error':'--legacy-packages does not support --review-decisions; refusing instead of ignoring it'}));return 2
    if legacy and '--review-overlay' in opts:
        print(json.dumps({'status':'INCOMPATIBLE_OPTIONS','error':'--legacy-packages does not support --review-overlay; refusing instead of ignoring it'}));return 2
    if legacy and '--only-chapter' in opts:
        print(json.dumps({'status':'INCOMPATIBLE_OPTIONS','error':'--legacy-packages does not support --only-chapter; refusing instead of ignoring the selection'}));return 2
    if len(args)!=1 or (dry and legacy):print(USAGE);return 2
    if legacy:
        # B6.2: the legacy transport-package chain has no chapter gate and no pilot preflight; a budget alone must never
        # reach a provider past an open review. Refused on the CLI (fail-closed); the programmatic run() is unchanged.
        print(json.dumps({'status':'LEGACY_PATH_HAS_NO_PILOT_PREFLIGHT','provider_calls_made':0,'error':'--legacy-packages is refused: it bypasses the chapter gate and the production pilot preflight; use the standard chapter path'}));return 2
    try:
        if dry:
            out,report=run_chapters(args[0],dry_run=True,out_dir=opts.get('--out'),decisions=opts.get('--decisions'),output_base=None,only_chapter=only,review_overlay=opts.get('--review-overlay'),review_decisions=opts.get('--review-decisions'))
            model_check=None
            if '--model' in opts:
                from .providers import check_model,ModelUnavailable
                try:check_model('codex',opts['--model']);model_check={'model':opts['--model'],'status':'LISTED_IN_LOCAL_CATALOG','note':'catalog is metadata; server acceptance is only known at run time'}
                except ModelUnavailable as e:model_check={'model':opts['--model'],'status':e.state,'reason':e.reason}
            print(json.dumps({'mode':'DRY_RUN','out':str(out),'model_check':model_check,'readiness':report['readiness'],'chapters':len(report['chapters']),'blockers':len(report['blockers']),'planned_actions':report['planned_actions'],'selection':report['selection'],'review_overlay':{k:v for k,v in (report.get('review_overlay') or {}).items() if k!='rejected'} or None,'review_decisions':{k:v for k,v in (report.get('review_decisions') or {}).items() if k not in ('rejected','page_reviews')} or None,'product_preflight':report.get('product_preflight'),'production_preflight':{'result':report['production_preflight']['result'],'chapters':{k:{'status':v['status'],'open':[o['code'] for o in v['open']]} for k,v in report['production_preflight']['chapters'].items()}},'provider_calls_made':0},ensure_ascii=False,indent=2))
            return 2 if report['readiness']=='SELECTION_ERROR' or report['selection'].get('status') in ('SELECTED_BLOCKED','SELECTED_INELIGIBLE') else 0
        experimental=any(k in opts for k in ('--budget','--review-decisions','--review-overlay','--decisions'))
        if not experimental and not legacy:
            # B6.8 product mode: one-time setup instead of per-run signatures; fail-closed budget from the stored policy.
            from .product import load_config,run_product
            pcfg=load_config()
            if pcfg is None:
                # fail-closed exactly like a missing budget (exit 3): no setup, no consent, no provider call
                print(json.dumps({'status':BUDGET_BLOCKED,'reason':'NOT_CONFIGURED','provider_calls_made':0,'next':'one-time setup. In Claude Code or Codex (no extra model process): exam-mastery --setup --provider agent --accept-data-transfer . Alternatives: --provider codex|gemini --model <id> --accept-data-transfer [--max-cost-usd 5] (see SKILL.md step 2)'},indent=2));return 3
            # B7: --only-chapter limits a product run to one chapter (bounded acceptance runs); normal use omits it
            _,status,dossier=run_product(args[0],pcfg,only_chapter=only)
            print(json.dumps({'status':status.get('status'),'run_state':status.get('run_state'),'release':dossier['release'],'dimensions':dossier['dimensions'],
                              'chapters_not_produced':dossier['chapters_not_produced'],'budget':status.get('budget')},ensure_ascii=False,indent=2))
            if status.get('run_state')=='AGENT_TURN_REQUIRED':
                print(json.dumps({'status':'AGENT_TURN_REQUIRED','next':str(Path(status.get('agent_next') or ''))},ensure_ascii=False));return 4
            if status.get('run_state') in (BUDGET_BLOCKED,QUOTA_BLOCKED):return 3
            return 0 if dossier['release']['technical']=='TECHNICAL_RELEASE_CANDIDATE' else 2
        cfg=load_budget_config(opts['--budget']) if '--budget' in opts else None
        if legacy:
            print(json.dumps({'mode':'LEGACY_TRANSPORT_PACKAGES','warning':'isolated legacy mode: per-package role chain; not the standard path'}),file=sys.stderr)
            _,status=run(args[0],budget_config=cfg)
        else:
            from .curriculum import SemanticDecisions
            d=SemanticDecisions.from_file(opts['--decisions']) if '--decisions' in opts else None
            # Budget gate first (unchanged order), then the explicit-model gate inside run_chapters.
            if opts.get('--provider','codex')=='gemini':
                from .gemini_provider import GeminiProvider
                prov=GeminiProvider(opts.get('--model'),key_file=opts.get('--key-file'),thinking_level=opts.get('--thinking-level'))
            elif opts.get('--provider','codex')=='codex':prov=Provider('codex',model=opts.get('--model'))
            else:raise ContractError('--provider must be codex or gemini')
            _,status=run_chapters(args[0],provider=prov,budget_config=cfg,decisions=d,only_chapter=only,review_overlay=opts.get('--review-overlay'),review_decisions=opts.get('--review-decisions'))
        if status.get('run_state') in (BUDGET_BLOCKED,QUOTA_BLOCKED):return 3
        if status.get('run_state')=='INTERRUPTED':return 130
        return 2 if status['technical_status']=='FAIL' or status['status']=='NO_GO' else 0
    except BudgetBlocked as e:print(json.dumps({'status':e.state,'error':str(e)}));return 3
    except ModelUnavailableError as e:print(json.dumps({'status':e.state,'provider_calls_made':0,'model':e.model,'error':e.reason}));return 2
    except Exception as e:
        if getattr(e,'state',None)=='PILOT_REVIEW_OPEN':
            print(json.dumps({'status':'PILOT_REVIEW_OPEN','provider_calls_made':0,'error':str(e),'preflight':e.preflight},ensure_ascii=False,indent=2));return 2
        print(json.dumps({'status':'NO_GO','error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
