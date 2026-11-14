"""P1: source fidelity and provenance on three contrasting synthetic courses at random roots."""
import json, os, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
from exam_mastery.fidelity import inventory, impact
from exam_mastery.source_schema import validate_source_manifest, BLOCKING_GAPS
from exam_mastery.common import ContractError, sha_file
from exam_mastery.parser_adapters import DoclingAdapter, compare_on


def run(kind, fetcher=None):
    base = tempfile.mkdtemp(prefix='p1-'); root = F.make(kind, base)
    out = Path(tempfile.mkdtemp(prefix='p1out-')) / 'inv'
    return root, out, inventory(root, out, fetcher=fetcher)


def els(m, rel, kind=None):
    sid = next(s['source_id'] for s in m['sources'] if s['relative_path'] == rel)
    return [e for e in m['elements'] if e['source_id'] == sid and (kind is None or e['kind'] == kind)]


def src(m, rel):
    return next(s for s in m['sources'] if s['relative_path'] == rel)


class P1Fidelity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.math = run('math'); cls.law = run('law'); cls.ml = run('ml')

    def test_every_file_inventoried_no_silent_drop(self):
        for root, out, m in (self.math, self.law, self.ml):
            files = sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())
            self.assertEqual(files, sorted(s['relative_path'] for s in m['sources']))
            validate_source_manifest(m)
            for s in m['sources']:
                if s['status'] != 'extracted':  # every non-clean source names why
                    self.assertTrue(s['uncertainties'] or s['error'], s)
            self.assertTrue((out / 'source_inventory.json').is_file())

    def test_pptx_text_and_visuals_without_pdf_substitute(self):
        root, out, m = self.math
        rel = 'folien_projektion.pptx'
        pics = els(m, rel, 'image')
        self.assertEqual(len(pics), 1)
        a = pics[0]['asset']
        self.assertEqual(a['origin'], 'pptx_picture_blob')
        self.assertEqual(sha_file(out / a['path']), a['sha256'])
        self.assertEqual(pics[0]['locator']['slide'], 1); self.assertIsNotNone(pics[0]['locator']['bbox'])
        chart = els(m, rel, 'chart')[0]
        self.assertEqual(chart['structure']['categories'], ['x1', 'x2', 'x3'])
        self.assertEqual(chart['structure']['series'][0]['values'], [0.5, -0.2, 0.1])
        self.assertEqual(els(m, rel, 'table')[0]['structure']['rows'], [['x', 'y'], ['1', '2']])
        f = els(m, rel, 'formula')[0]
        self.assertIn('oMath', f['structure']['omml']); self.assertEqual(f['text'], 'Ax2=b')
        self.assertTrue(f['fidelity']['structure_preserved'])
        self.assertEqual(els(m, rel, 'diagram')[0]['status'], 'uncertain')
        self.assertEqual(els(m, rel, 'rendered_page'), [], 'no PDF raster may stand in for a slide render')
        s = src(m, rel)
        self.assertIn('SLIDE_RENDER_UNAVAILABLE', s['uncertainties']); self.assertEqual(s['visual_status'], 'RENDER_UNAVAILABLE')
        self.assertFalse(m['coverage_complete'])

    def test_pdf_page_anchors_images_diagrams_and_empty_page(self):
        root, out, m = self.math
        rel = 'Altklausur_2025.pdf'
        texts = els(m, rel, 'paragraph') + els(m, rel, 'heading')
        self.assertTrue(all(e['locator']['page'] == 1 and len(e['locator']['bbox']) == 4 for e in texts))
        self.assertTrue(any('Normalengleichung' in e['text'] for e in texts))
        img = els(m, rel, 'image')[0]
        self.assertEqual(img['asset']['origin'], 'pdf_embedded_image'); self.assertIsNotNone(img['locator']['bbox'])
        self.assertEqual(els(m, rel, 'diagram')[0]['status'], 'uncertain')
        render = els(m, rel, 'rendered_page')[0]
        self.assertFalse(render['fidelity']['structure_preserved']); self.assertEqual(render['status'], 'uncertain')
        formulas = els(m, rel, 'formula')
        self.assertTrue(formulas and all(not f['fidelity']['structure_preserved'] for f in formulas))
        gaps = [g for g in m['gaps'] if g['source_id'] == src(m, rel)['source_id']]
        self.assertTrue(any(g['code'] == 'EMPTY_PAGE' and 'Page 2' in g['detail'] for g in gaps))

    def test_markdown_latex_and_figure_anchors(self):
        root, out, m = self.math
        rel = 'skript/kapitel1_ausgleich.md'
        f = [e for e in els(m, rel, 'formula') if e['locator'].get('display')]
        self.assertTrue(any('nabla' in e['structure']['latex'] for e in f))
        self.assertTrue(all(e['fidelity']['representation'] == 'LaTeX source' for e in f))
        figs = els(m, rel, 'figure')
        ok = next(e for e in figs if e['status'] == 'ok'); missing = next(e for e in figs if e['status'] == 'unavailable')
        self.assertEqual(ok['structure']['linked_source_id'], src(m, 'skript/fig_projection.png')['source_id'])
        self.assertTrue(any(g['code'] == 'MISSING_LINKED_ASSET' and g['locator_str'] == missing['locator_str'] for g in m['gaps']))
        self.assertTrue(all(e['locator']['lines'] for e in els(m, rel)))
        objectives = els(m, rel, 'list_item')
        self.assertEqual(len(objectives), 3, 'heading glued to a list must not swallow the list')

    def test_unsupported_empty_corrupt_explicit(self):
        root, out, m = self.law
        self.assertEqual(src(m, 'material/altes_format.xyz')['status'], 'unsupported')
        self.assertEqual(src(m, 'material/leer.txt')['status'], 'empty')
        bad = src(m, 'material/scan_kaputt.pdf')
        self.assertEqual(bad['status'], 'failed'); self.assertIn('PARSE_FAILED', bad['uncertainties']); self.assertTrue(bad['error'])
        self.assertFalse(m['coverage_complete'])
        self.assertEqual(m['status_counts']['unsupported'], 1)

    def test_docx_structure(self):
        root, out, m = self.law
        rel = 'Vorlesung_Kaufrecht.docx'
        self.assertEqual(els(m, rel, 'heading')[0]['structure']['level'], 1)
        self.assertEqual(els(m, rel, 'table')[0]['structure']['rows'][0], ['Tatbestand', 'Rechtsfolge'])
        self.assertEqual(els(m, rel, 'image')[0]['asset']['origin'], 'docx_inline_image')
        self.assertIn('PAGE_UNKNOWN', src(m, rel)['uncertainties'])
        self.assertEqual(src(m, rel)['authority'], 'OFFICIAL_LECTURE')
        self.assertEqual(src(m, 'material/klausur_ws24.md')['authority'], 'OFFICIAL_EXAM')
        self.assertEqual(src(m, 'material/Musterlösung_ws24.md')['authority'], 'OFFICIAL_SOLUTION')

    def test_online_sources_offline_default_never_fake_success(self):
        root, out, m = self.law
        refs = {r['url']: r for r in m['online_references']}
        self.assertEqual({r['status'] for r in refs.values()}, {'NOT_FETCHED_OFFLINE_POLICY'})
        r = refs['https://www.gesetze-im-internet.de/bgb/__433.html']
        self.assertEqual(r['labels'], ['Gesetzestext BGB'])
        link = next(e for e in m['elements'] if e['element_id'] in r['referenced_by_elements'])
        self.assertEqual(link['locator'], {'row': 2, 'column': 2})

    def test_online_fetch_success_and_missing_with_injected_fake(self):
        calls = []

        def fake(url):
            calls.append(url)
            if 'unreachable' in url:
                raise ConnectionError('DNS failure (simulated)')
            return b'<html>BGB 433</html>', 'text/html', url
        with patch('socket.socket', side_effect=AssertionError('no real network')):
            root, out, m = run('law', fetcher=fake)
        refs = {r['url']: r for r in m['online_references']}
        self.assertEqual(refs['https://www.gesetze-im-internet.de/bgb/__433.html']['status'], 'FETCHED')
        self.assertEqual(len(refs['https://www.gesetze-im-internet.de/bgb/__433.html']['sha256']), 64)
        miss = refs['https://unreachable.invalid/kommentar']
        self.assertEqual(miss['status'], 'SOURCE_UNAVAILABLE'); self.assertIn('DNS failure', miss['error'])
        self.assertTrue(any(g['code'] == 'SOURCE_UNAVAILABLE' for g in m['gaps']))
        self.assertEqual(len(calls), 2)

    def test_stable_ids_on_repeat_and_other_random_root(self):
        root, out, m = self.ml
        again = inventory(root, Path(tempfile.mkdtemp()) / 'inv')
        other = F.random_root(tempfile.mkdtemp()); shutil.rmtree(other); shutil.copytree(root, other)
        third = inventory(other, Path(tempfile.mkdtemp()) / 'inv')
        key = lambda x: [(e['element_id'], e['raw_span_hash'], e['extraction_hash']) for e in x['elements']]
        self.assertEqual(key(m), key(again)); self.assertEqual(key(m), key(third))
        strip = lambda x: json.dumps({k: v for k, v in x.items() if k != 'root_name'}, sort_keys=True)
        self.assertEqual(strip(m), strip(third))

    def test_selective_change_only_touches_changed_source(self):
        base = tempfile.mkdtemp(); root = F.make('math', base)
        m1 = inventory(root, Path(tempfile.mkdtemp()) / 'a')
        target = root / 'skript' / 'kapitel2_qr.md'
        target.write_text(target.read_text().replace('numerisch stabiler', 'numerisch deutlich stabiler'))
        m2 = inventory(root, Path(tempfile.mkdtemp()) / 'b')
        d = impact(m1, m2)
        qr = src(m1, 'skript/kapitel2_qr.md')['source_id']
        self.assertEqual(d['changed_sources'], [qr])
        changed_sources = {e['source_id'] for e in m2['elements'] if e['element_id'] in d['changed_elements']}
        self.assertEqual(changed_sources, {qr}); self.assertEqual(len(d['changed_elements']), 1)
        self.assertFalse(d['added_sources'] or d['removed_sources'])

    def test_untrusted_content_never_executed(self):
        root, out, m = self.ml
        self.assertFalse(list(root.rglob('SENTINEL*'))); self.assertFalse(list(Path.cwd().glob('SENTINEL*')))
        self.assertFalse(list(out.parent.rglob('SENTINEL*')))
        nb = els(m, 'lab.ipynb')
        flagged = [e for e in nb if 'instruction_like_untrusted_text' in e['flags']]
        self.assertTrue(flagged); self.assertIn('Ignore all previous instructions', flagged[0]['text'])
        self.assertTrue(all('code_not_executed' in e['flags'] for e in nb if e['kind'] == 'code'))
        self.assertEqual(els(m, 'lab.ipynb', 'image')[0]['locator'], {'cell': 2, 'output': 2})
        self.assertIn('saved_output_not_reproduced', els(m, 'lab.ipynb', 'code_output')[0]['flags'])
        svg = src(m, 'diagram.svg'); self.assertIn('ACTIVE_CONTENT_NOT_RENDERED', svg['uncertainties'])
        py = [e for e in els(m, 'code/gd.py', 'code') if e['structure'].get('symbol')]
        self.assertEqual({e['structure']['symbol'] for e in py}, {'gradient', 'Trainer'})

    def test_originals_read_only_and_raw_text_kept(self):
        base = tempfile.mkdtemp(); root = F.make('law', base)
        before = {str(p): sha_file(p) for p in root.rglob('*') if p.is_file()}
        m = inventory(root, Path(tempfile.mkdtemp()) / 'x')
        self.assertEqual(before, {str(p): sha_file(p) for p in root.rglob('*') if p.is_file()})
        with self.assertRaises(ContractError):
            inventory(root, root / 'out')
        para = next(e for e in m['elements'] if '\n' in e['text'])
        self.assertNotEqual(para['text'], para['normalized_text'])
        self.assertNotIn('\n', para['normalized_text'])

    def test_blocking_gaps_make_coverage_incomplete(self):
        base = tempfile.mkdtemp(); root = F.random_root(base); (root / 'a.md').write_text('# Titel\n\nText ohne Lücken.\n')
        m = inventory(root, Path(tempfile.mkdtemp()) / 'x')
        self.assertTrue(m['coverage_complete'])
        (root / 'b.unknownext').write_text('x')
        m = inventory(root, Path(tempfile.mkdtemp()) / 'y')
        self.assertFalse(m['coverage_complete']); self.assertTrue(any(g['code'] in BLOCKING_GAPS for g in m['gaps']))

    def test_docling_adapter_reports_state_without_download(self):
        st = DoclingAdapter.status()
        self.assertIn(st['state'], ('NOT_INSTALLED', 'NO_OFFLINE_MODELS', 'READY_OFFLINE'))
        if st['state'] != 'READY_OFFLINE':
            self.assertEqual(compare_on(['x.pdf'])['state'], 'NOT_TESTED')


if __name__ == '__main__':
    unittest.main()
