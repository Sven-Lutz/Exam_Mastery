from __future__ import annotations
import argparse,hashlib,json,sys,shutil,importlib.util
from pathlib import Path
from .common import ContractError,sha_file,read_json,write_json
from .providers import Provider
from .ingest import ingest
from .workflow import run
ROOT=Path(__file__).resolve().parent.parent
LOCK=ROOT/'ENGINE_FREEZE.json'

def freeze_map():
    excluded={'__pycache__','build','dist','.git'}
    included=[p for p in ROOT.rglob('*') if p.is_file() and not any(part in excluded or part.endswith('.egg-info') for part in p.relative_to(ROOT).parts) and p.name!='ENGINE_FREEZE.json' and p.suffix!='.pyc']
    return {str(p.relative_to(ROOT)):sha_file(p) for p in sorted(included)}

def check_lock():
    if not LOCK.exists(): raise ContractError('Engine not frozen; run `python -m exam_mastery.cli freeze` BEFORE revealing holdout')
    snap=read_json(LOCK); now=freeze_map()
    if snap['files']!=now: raise ContractError('Engine has changed since freeze. Holdout run denied; explicitly re-freeze on development data only.')
    return snap

def offline_plan(action, rest):
    """P1/P2 offline commands: no provider, no network. `inventory|plan <root> --out <dir> [--decisions f]`."""
    import argparse
    ap = argparse.ArgumentParser(prog='exam-mastery ' + action)
    ap.add_argument('root'); ap.add_argument('--out', required=True); ap.add_argument('--decisions')
    a = ap.parse_args(rest)
    from .fidelity import inventory
    m = inventory(Path(a.root), Path(a.out))
    result = {'sources': m['source_count'], 'elements': m['element_count'], 'status_counts': m['status_counts'],
              'gaps': len(m['gaps']), 'coverage_complete': m['coverage_complete']}
    if action == 'plan':
        from .curriculum import compile_curriculum, SemanticDecisions
        d = SemanticDecisions.from_file(a.decisions) if a.decisions else None
        p = compile_curriculum(m, Path(a.out), decisions=d)
        result['curriculum'] = p['summary']; result['provider_calls'] = p['provider_calls']
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0


def kb_command(a):
    """exam-mastery kb validate | summary | context <artifact> [--subject <s>] | spec <id>"""
    from . import knowledge as kb
    sub=a[0] if a else 'summary'
    if sub=='validate':
        errs=kb.validate();print('\n'.join(errs) if errs else 'KB VALID '+kb.fingerprint());return 1 if errs else 0
    if sub=='summary':print(json.dumps(kb.evidence_summary(),indent=1,ensure_ascii=False));return 0
    if sub=='context' and len(a)>1:
        subj=a[a.index('--subject')+1] if '--subject' in a else None;print(kb.context_for(a[1],subj));return 0
    if sub=='spec' and len(a)>1:print(json.dumps(kb.spec(a[1]),indent=1,ensure_ascii=False));return 0
    print('Usage: exam-mastery kb validate | summary | context <artifact> [--subject <s>] | spec <id>');return 2


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if not args:print('Usage: exam-mastery start <root> [--dry-run --out <dir>] [--legacy-packages] | inventory <root> --out <dir> | plan <root> --out <dir> | experience validate|plan|obsidian <unit.json> [--out <note.md>] | freeze | verify-freeze | preflight');return 2
    action=args[0]
    if action in ('--version','-V','version'):
        from .common import version_info
        print(json.dumps(version_info(),ensure_ascii=False));return 0
    try:
        if action=='freeze':
            m=freeze_map();write_json(LOCK,{'schema':'exam-mastery-freeze-v4','version':'0.4.0','files':m,'sha256':hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()});print(read_json(LOCK)['sha256']);return 0
        if action=='verify-freeze':print('LOCK VERIFIED '+check_lock()['sha256']);return 0
        if action=='preflight':
            print(json.dumps({'version':'0.4.0','codex_available':bool(shutil.which('codex')),'default_backend':'codex','claude_required':False,'gemini_required':False,'python':sys.version.split()[0]},indent=2));return 0
        if action=='experience':
            from .learning.experience import command
            return command(args[1:])
        if action=='kb':
            return kb_command(args[1:])
        if action in ('inventory', 'plan'):
            return offline_plan(action, args[1:])
        from .runtime import main as start
        return start(args[1:] if action in ('run','start') else args)
    except Exception as e:print(f'ERROR: {e}');return 2
if __name__=='__main__':raise SystemExit(main())
