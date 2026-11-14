"""Parser adapter boundary for optional external parsers (Docling first, MinerU later).

Decision (P1): Docling is NOT installed in the engine runtime. Installing it pulls PyTorch and
layout/table model weights from the network, which the P1 execution limits forbid. Therefore:
- ``DoclingAdapter.status()`` reports availability without importing heavy modules or downloading.
- ``compare_on(paths)`` runs builtin vs. Docling only when Docling is present AND
  offline model artifacts are configured; otherwise it returns NOT_TESTED with the reason.
- The builtin extractor (fidelity.py) stays the production path until a recorded comparison
  on a gold corpus justifies switching (see P1_P2_ABNAHME.md).
"""
from __future__ import annotations
import importlib.util, os
from pathlib import Path


class DoclingAdapter:
    name = 'docling'

    @staticmethod
    def status():
        spec = importlib.util.find_spec('docling')
        if spec is None:
            return {'adapter': 'docling', 'available': False, 'state': 'NOT_INSTALLED',
                    'reason': 'not installed; install would download torch + model weights (outside P1 limits)'}
        artifacts = os.environ.get('DOCLING_ARTIFACTS_PATH')
        if not artifacts or not Path(artifacts).is_dir():
            return {'adapter': 'docling', 'available': False, 'state': 'NO_OFFLINE_MODELS',
                    'reason': 'DOCLING_ARTIFACTS_PATH not set to a local model directory; refusing implicit download'}
        return {'adapter': 'docling', 'available': True, 'state': 'READY_OFFLINE', 'artifacts_path': artifacts}

    @classmethod
    def convert(cls, path):  # pragma: no cover - requires an offline Docling installation
        st = cls.status()
        if not st['available']:
            raise RuntimeError(st['reason'])
        os.environ.setdefault('HF_HUB_OFFLINE', '1')
        from docling.document_converter import DocumentConverter
        doc = DocumentConverter().convert(str(path)).document.export_to_dict()
        out = []
        for group in ('texts', 'tables', 'pictures'):
            for item in doc.get(group, []):
                prov = (item.get('prov') or [{}])[0]
                out.append({'kind': group[:-1], 'page': prov.get('page_no'), 'bbox': prov.get('bbox'),
                            'text': item.get('text', ''), 'label': item.get('label')})
        return out


def compare_on(paths):
    """Builtin-vs-Docling element counts per file; NOT_TESTED when Docling cannot run offline."""
    st = DoclingAdapter.status()
    if not st['available']:
        return {'state': 'NOT_TESTED', 'docling': st, 'files': [str(p) for p in paths]}
    from .fidelity import _Collector, _parse_pdf, _parse_pptx, _parse_docx  # pragma: no cover
    rows = []
    for p in map(Path, paths):  # pragma: no cover
        import tempfile
        c = _Collector('cmp', Path(tempfile.mkdtemp(prefix='em-cmp-')) / 'assets')
        {'.pdf': _parse_pdf, '.docx': _parse_docx}.get(p.suffix.lower(), lambda x, y: _parse_pptx(x, y, []))(p, c)
        d = DoclingAdapter.convert(p)
        rows.append({'file': str(p), 'builtin': {k: sum(e['kind'] == k for e in c.elements) for k in ('paragraph', 'table', 'image', 'formula')},
                     'docling': {k: sum(e['kind'] == k for e in d) for k in ('text', 'table', 'picture')}})
    return {'state': 'COMPARED', 'docling': st, 'rows': rows}
