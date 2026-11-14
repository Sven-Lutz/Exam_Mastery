"""A PDF on which PyMuPDF's layout model is stable keeps the layout path; the probe result is cached by hash."""
import pymupdf
from exam_mastery import fidelity


def test_probe_safe_and_cached(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    d = pymupdf.open(); d.new_page().insert_text((72, 72), 'Hallo'); d.save(tmp_path / 'a.pdf')
    assert fidelity.layout_tables_safe(tmp_path / 'a.pdf') is True
    assert list((tmp_path / 'cache' / 'exam-mastery-layout-probe').glob('*.json'))


def test_crash_means_unsafe(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    monkeypatch.setattr(fidelity, '_PROBE', 'import os,signal; os.kill(os.getpid(), signal.SIGSEGV)')
    d = pymupdf.open(); d.new_page(); d.save(tmp_path / 'b.pdf')
    assert fidelity.layout_tables_safe(tmp_path / 'b.pdf') is False
