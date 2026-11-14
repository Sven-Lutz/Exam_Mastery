"""Exactly one user argument; immutable inputs and unique external run directory."""
from __future__ import annotations
import hashlib,json,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
from .common import write_json,sha_file,is_transient_file
from .providers import Provider
from .workflow import run

def snapshot(root,hasher=sha_file):
    result={}
    for p in root.rglob('*'):
        if p.is_file() and not p.is_symlink() and not is_transient_file(p.name):
            try:result[str(p.relative_to(root))]=hasher(p)
            except OSError as e:result[str(p.relative_to(root))]={'integrity_error':f'{type(e).__name__}: {e}'}
    return result

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=1:
        print('Verwendung: exam-mastery-start /pfad/zur/vorlesung');return 2
    source=Path(args[0]).expanduser().resolve()
    if not source.is_dir():print('Quellordner nicht zugänglich');return 2
    from .cli import check_lock
    freeze=check_lock()
    base=Path(__file__).resolve().parents[3]/'runs'
    # Never allow output inside supplied sources (including project root).
    if base==source or source in base.parents:
        base=Path.home()/'Exam_Mastery_Output'
    if base==source or source in base.parents:
        print('Kein sicherer Ausgabeort außerhalb der Quellen verfügbar');return 2
    key=hashlib.sha256(str(source).encode()).hexdigest()[:12]
    out=base/key/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    print(f'Ausgabe: {out}',flush=True)
    before=snapshot(source);write_json(out/'originals_before.json',before)
    try:
        status=run(source,out,Provider('claude'),Provider('claude'))
        if (out/'learning_model.json').exists():
            from .quality import quality
            qa=quality(out)
            status['technical_qa']=qa['technical_status']
            if qa['technical_status']=='FAIL':status['status']='NO_GO'
        else:
            status['technical_qa']='NOT_RUN'
            write_json(out/'quality_report.json',{'technical_status':'NOT_RUN','release_approved':False,'blocker':status.get('error','No learning model produced')})
    except Exception as e:status={'status':'NO_GO','error':f'{type(e).__name__}: {e}'}
    after=snapshot(source)
    readable=all(isinstance(v,str) and len(v)==64 for v in before.values())
    status['originals_unchanged']=before==after and readable
    if not readable:status['status']='NO_GO';status['source_integrity_unverifiable']=True
    if before!=after:status['status']='NO_GO';status['source_mutation_detected']=True
    status['engine_freeze_sha256']=freeze['sha256']
    try:check_lock()
    except Exception as e:status['status']='NO_GO';status['engine_changed_during_run']=str(e)
    status['release_approved']=False
    write_json(out/'status.json',status)
    write_json(out/'run_manifest.json',{'engine':'0.3.0','source_root':str(source),'source_snapshot':before,'files':{str(p.relative_to(out)):sha_file(p) for p in out.rglob('*') if p.is_file() and p.name!='run_manifest.json'}})
    print(json.dumps(status,ensure_ascii=False,indent=2))
    return 2 if status['status']=='NO_GO' else 0
if __name__=='__main__':raise SystemExit(main())
