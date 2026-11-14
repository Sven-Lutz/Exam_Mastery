"""Offline workspace integrity check (read-only). Reports, never fixes.

Checks: engine root and default run base resolve outside sync-marked folders (macOS file-provider xattr on the path
or any parent), no sync-conflict copies ('name 2.ext') in repo/.git/run base, single git index, git fsck clean,
no symlink inside the repo pointing elsewhere.
Exit code 0 = all checks passed, 1 = at least one finding (printed as JSON).
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]  # optional: check another repo read-only
RUN_BASE = ROOT.parent.parent / 'runs_v0_5_1_p0_dev'          # same rule as runtime._base()
CONFLICT = re.compile(r' [2-9](\.[^/]*)?$')


def provider_marked(p):
    for x in [p, *p.parents]:
        if not x.exists():
            continue
        out = subprocess.run(['xattr', str(x)], capture_output=True, text=True).stdout
        if 'file-provider-domain-id' in out or 'fileprovider' in out.lower():
            return str(x)
    return None


def main():
    f = {}
    f['engine_root'] = str(ROOT); f['default_run_base'] = str(RUN_BASE)
    f['engine_root_sync_marked_by'] = provider_marked(ROOT)
    f['run_base_sync_marked_by'] = provider_marked(RUN_BASE if RUN_BASE.exists() else RUN_BASE.parent)
    f['under_cloudstorage_or_mobile_documents'] = any(s in str(ROOT) for s in ('/Library/CloudStorage/', '/Library/Mobile Documents/'))
    scan = [ROOT] + ([RUN_BASE] if RUN_BASE.exists() else [])
    f['conflict_copies'] = [str(p) for d in scan for p in d.rglob('*') if CONFLICT.search(p.name)][:50]
    f['git_index_files'] = sorted(p.name for p in (ROOT / '.git').glob('index*'))
    f['repo_symlinks'] = [str(p) for p in ROOT.rglob('*') if p.is_symlink()]
    fsck = subprocess.run(['git', '-C', str(ROOT), 'fsck', '--full'], capture_output=True, text=True)
    f['git_fsck_rc'] = fsck.returncode
    f['git_remotes'] = subprocess.run(['git', '-C', str(ROOT), 'remote'], capture_output=True, text=True).stdout.split()
    ok = (not f['engine_root_sync_marked_by'] and not f['run_base_sync_marked_by'] and not f['under_cloudstorage_or_mobile_documents']
          and not f['conflict_copies'] and f['git_index_files'] == ['index'] and not f['repo_symlinks'] and f['git_fsck_rc'] == 0)
    f['result'] = 'PASS' if ok else 'FINDINGS'
    print(json.dumps(f, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
