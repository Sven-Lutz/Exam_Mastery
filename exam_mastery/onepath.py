from .runtime import main
from .common import sha_file
from .onepath_legacy import snapshot as _snapshot
def snapshot(root):return _snapshot(root,hasher=sha_file)
if __name__=="__main__":raise SystemExit(main())
