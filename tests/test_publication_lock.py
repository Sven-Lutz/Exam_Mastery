import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest
from exam_mastery.learning.publication_lock import publication_lock
from exam_mastery.learning import experience_pipeline as pipeline


def holder(root):
    code = '''
import sys, time
from exam_mastery.learning.publication_lock import publication_lock
with publication_lock(sys.argv[1]):
 print("LOCKED", flush=True)
 time.sleep(30)
'''
    p = subprocess.Popen([sys.executable, '-c', code, str(root)], stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == 'LOCKED'
    return p


def test_directory_lock_times_out_and_kernel_releases_after_kill(tmp_path):
    keep = tmp_path / 'Lehrbuch.pdf'
    keep.write_bytes(b'unchanged learning product')
    p = holder(tmp_path)
    try:
        with pytest.raises(TimeoutError):
            with publication_lock(tmp_path, timeout=0.05):
                pytest.fail('Concurrent writer entered')
        for operation in (lambda: pipeline.build({}, tmp_path, lock_timeout=0.05),
                          lambda: pipeline.recover(tmp_path, lock_timeout=0.05)):
            with pytest.raises(TimeoutError): operation()
        assert keep.read_bytes() == b'unchanged learning product'
        assert sorted(x.name for x in tmp_path.iterdir()) == ['Lehrbuch.pdf']
    finally:
        p.kill(); p.wait(); p.stdout.close()
    with publication_lock(tmp_path, timeout=0): pass
    assert keep.read_bytes() == b'unchanged learning product'


def test_direct_publishers_share_the_lock(tmp_path):
    from exam_mastery.learning import experience_books, experience_anki, interactive_reference
    p = holder(tmp_path)
    try:
        for module in (experience_books, experience_anki, interactive_reference):
            with pytest.raises(TimeoutError): module.publish({}, tmp_path, lock_timeout=0)
    finally:
        p.terminate(); p.wait(); p.stdout.close()


def test_waiter_enters_only_after_release(tmp_path):
    p = holder(tmp_path)
    code = '''
import sys
from pathlib import Path
from exam_mastery.learning.publication_lock import publication_lock
with publication_lock(sys.argv[1], timeout=5):
 Path(sys.argv[1], "entered").write_text("yes")
'''
    waiter = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)])
    try:
        time.sleep(0.1)
        assert not (tmp_path / 'entered').exists()
        p.terminate(); p.wait()
        assert waiter.wait(timeout=5) == 0
        assert (tmp_path / 'entered').read_text() == 'yes'
    finally:
        if p.poll() is None: p.kill(); p.wait()
        if waiter.poll() is None: waiter.kill(); waiter.wait()
        p.stdout.close()


def test_lock_released_on_exception_and_symlink_refused(tmp_path):
    with pytest.raises(RuntimeError):
        with publication_lock(tmp_path): raise RuntimeError('failure')
    with publication_lock(tmp_path, timeout=0): pass
    link = tmp_path / 'link'; link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        with publication_lock(link): pass


@pytest.mark.parametrize('timeout', [-1, float('nan'), float('inf'), True])
def test_invalid_timeout(timeout, tmp_path):
    with pytest.raises(ValueError):
        with publication_lock(tmp_path, timeout=timeout): pass
