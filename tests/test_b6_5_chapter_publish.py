"""B6.5: the standard chapter path publishes textbook, workbook, solutions, competency matrix and Anki.
Offline with the SYNTHETIC fixture model: this proves mechanics, consistency and rendering, not content quality."""
import contextlib, csv, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from exam_mastery.runtime import run_chapters


def synthetic_run(kind, d):
    root = F.make(kind, str(d / kind))
    with contextlib.redirect_stdout(io.StringIO()):
        out, st = run_chapters(root, provider=P.SyntheticChapterModel(), output_base=d / ('runs_' + kind))
    return out, st


class ChapterPublishing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); d = Path(cls.tmp.name)
        cls.runs = {k: synthetic_run(k, d) for k in ('math', 'law', 'ml')}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def chapters(self):
        for kind, (out, st) in self.runs.items():
            for ch in sorted((out / 'chapters').iterdir()):
                if (ch / 'content_ast.json').exists():
                    yield kind, st, ch, json.loads((ch / 'content_ast.json').read_text())

    def test_every_technically_passed_chapter_is_published(self):
        n = 0
        for kind, st, ch, ast in self.chapters():
            with self.subTest(kind=kind, chapter=ch.name):
                self.assertEqual(st['technical_status'], 'PASS')
                rec = st['chapters'][ch.name]
                self.assertEqual(rec['publish']['status'], 'PUBLISHED_DRAFT')
                art = ch / 'publish' / 'artifacts'
                for f in ('kapitel.html', 'kompetenzmatrix.csv', '1_Lehrbuch.pdf', '2_Arbeitsbuch.pdf', '3_Musterloesungen.pdf'):
                    self.assertTrue((art / f).is_file(), f)
                n += 1
        self.assertGreaterEqual(n, 3)

    def test_products_are_consistent_with_the_content_ast(self):
        # B9: separate typeset documents; every item once in the workbook and once with its solution
        import pymupdf
        for kind, st, ch, ast in self.chapters():
            with self.subTest(kind=kind, chapter=ch.name):
                art = ch / 'publish' / 'artifacts'
                html = (art / 'kapitel.html').read_text()
                self.assertIn('SYNTHETISCHES TESTMATERIAL', html)
                if any(b.get('provenance') == 'AUTHOR_INFERENCE' for b in ast['blocks']):
                    self.assertIn('Einordnung (nicht aus der Vorlesung)', html)
                wb = ''.join(p.get_text() for p in pymupdf.open(art / '2_Arbeitsbuch.pdf'))
                sol = ''.join(p.get_text() for p in pymupdf.open(art / '3_Musterloesungen.pdf'))
                for a in ast['assessments']:
                    self.assertEqual(wb.count('Aufgabe ' + a['item_id']), 1, a['item_id'])
                    self.assertEqual(sol.count('Aufgabe ' + a['item_id']), 1, a['item_id'])
                self.assertNotIn('Ergebnis', wb)                                   # no solutions leak into the workbook
                rows = list(csv.DictReader((art / 'kompetenzmatrix.csv').open()))
                self.assertEqual({r['kc_id'] for r in rows}, {r['kc_id'] for r in ast['kc_coverage']} | {o['kc_id'] for o in ast['learning_objectives']})
                rep = json.loads((ch / 'publish' / 'publish_report.json').read_text())
                self.assertEqual(rep['source_verification'], 'NONE_HUMAN'); self.assertNotIn('RELEASED', json.dumps(rep))
                self.assertIn('NOT_GENERATED', rep['labs'])
                self.assertIn('didactic_rules', rep); self.assertIn('numeric_checks', rep)
                self.assertEqual(rep['numeric_checks']['counts'].get('FAIL', 0), 0)

    def test_anki_package_was_imported_and_updated_in_isolation(self):
        for kind, st, ch, ast in self.chapters():
            anki = st['chapters'][ch.name]['publish']['products']['anki']
            if anki['cards']:
                self.assertTrue(anki['reimport'])
                self.assertEqual(anki['media_missing'], [])
                self.assertTrue(all(k.startswith(('def/', 'mis/')) for k in anki['update_delta']['new'] + anki['update_delta']['unchanged']))

    def test_republish_keeps_card_ids_stable(self):
        from exam_mastery.chapter_publish import publish_chapter
        for kind, st, ch, ast in self.chapters():
            if st['chapters'][ch.name]['publish']['products']['anki']['cards']:
                break
        else:
            self.skipTest('no chapter with cards')
        out = self.runs[kind][0]
        man = json.loads((out / 'plan' / 'source_inventory.json').read_text()); plan = json.loads((out / 'plan' / 'curriculum.json').read_text())
        rep = publish_chapter(ch, man, plan, verify_anki=False)['products']['anki']
        self.assertEqual(rep['update_delta']['new'], []); self.assertEqual(rep['update_delta']['changed'], [])
        self.assertFalse(rep['update_delta']['automatic_deletion'])

    def test_course_title_does_not_change_card_identity(self):
        # B13 regression: a display title set with `exam-mastery course-title` must not re-key the deck (lost learning state)
        from exam_mastery.chapter_publish import publish_chapter
        for kind, st, ch, ast in self.chapters():
            if st['chapters'][ch.name]['publish']['products']['anki']['cards']:
                break
        else:
            self.skipTest('no chapter with cards')
        out = self.runs[kind][0]
        man = json.loads((out / 'plan' / 'source_inventory.json').read_text()); plan = json.loads((out / 'plan' / 'curriculum.json').read_text())
        before = publish_chapter(ch, man, plan, verify_anki=False)['products']['anki']
        prof = ch.resolve().parents[2] / 'course_profile.json'
        prof.write_text(json.dumps({'course_title': 'Ein ganz anderer Anzeigetitel'}))
        try:
            after = publish_chapter(ch, man, plan, verify_anki=False)['products']['anki']
            self.assertEqual(after['update_delta']['new'], [])
            self.assertEqual(after['update_delta']['retirement_candidates'], [])
            self.assertEqual(before.get('identities'), after.get('identities'))
        finally:
            prof.unlink()

    def test_publish_failure_fails_the_run(self):
        d = Path(tempfile.mkdtemp(prefix='b65f-'))
        with patch('exam_mastery.chapter_publish.publish_chapter', side_effect=RuntimeError('render broke')):
            out, st = synthetic_run('math', d)
        self.assertEqual(st['technical_status'], 'FAIL')
        self.assertTrue(any('render broke' in f['error'] for f in st['chapter_failures']))
        self.assertTrue(all(v['status'] == 'PUBLISH_FAILED' for v in st['chapters'].values() if 'publish' in v))


if __name__ == '__main__':
    unittest.main()
