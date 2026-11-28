"""POSIX process-exclusive publication, locking the output directory inode.

No removable lockfile (and therefore no stale-lock or unlink/recreate race).
The kernel releases flock on close or process exit, including SIGKILL. macOS
and Linux are supported; unsupported platforms fail closed before publishing.
This coordinates cooperating publishers, not hostile filesystem writers.
"""
from contextlib import contextmanager
from functools import wraps
import inspect
import math
import os
from pathlib import Path
import stat
import time


@contextmanager
def publication_lock(output_dir, timeout=30.0):
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
        raise ValueError("Publication lock timeout must be finite and nonnegative")
    import fcntl
    root = Path(output_dir)
    if root.is_symlink():
        raise ValueError("Refusing symlinked publication root")
    root.mkdir(parents=True, exist_ok=True)
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        expected = os.fstat(fd)
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Publication lock timeout: another publisher/recovery owns this output")
                time.sleep(min(0.025, remaining))
        current = root.lstat()
        if (not stat.S_ISDIR(current.st_mode) or
                (current.st_dev, current.st_ino) != (expected.st_dev, expected.st_ino)):
            raise ValueError("Publication directory changed while acquiring lock")
        yield
    finally:
        os.close(fd)


def locked_publisher(function):
    """Keep existing public signatures/keyword aliases; add lock_timeout control."""
    signature = inspect.signature(function)
    @wraps(function)
    def locked(*args, **kwargs):
        timeout = kwargs.pop("lock_timeout", 30.0)
        bound = signature.bind(*args, **kwargs)
        root = bound.arguments.get("output_dir", bound.arguments.get("out_dir"))
        with publication_lock(root, timeout=timeout):
            return function(*args, **kwargs)
    return locked
