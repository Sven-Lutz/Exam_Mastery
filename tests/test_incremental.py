"""Incremental update (A-G): offline change detection, chapter isolation, Anki identity, safe stop."""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from exam_mastery import incremental as inc

A = """# Break-even Analysis

Learning objectives:
- Define the break-even point as the output where total revenue equals total cost.
- Calculate the break-even quantity as fixed cost divided by the contribution margin per unit.
- Explain why a higher contribution margin lowers the break-even quantity.

Model: fixed cost F, price p, variable cost v per unit, contribution margin p - v. Break-even quantity Q = F/(p - v).

Example: F = 12000 EUR, p = 50 EUR, v = 30 EUR. Then Q = 12000/20 = 600 units.
"""
B = """# Net Present Value

Learning objectives:
- Define the net present value as the sum of discounted cash flows minus the initial investment.
- Calculate the net present value of a project with constant yearly cash flows.
- Explain why a higher discount rate lowers the net present value.

Model: initial investment I, yearly cash flow C for n years, discount rate r. NPV = -I + sum of C/(1+r)^t for t = 1..n.

Example: I = 1000 EUR, C = 600 EUR, n = 2, r = 10 %. NPV = -1000 + 545.45 + 495.87 = 41.32 EUR.
"""
C = """# Payback Period

Learning objectives:
- Define the payback period as the time until cumulative cash flows recover the investment.
- Calculate the payback period for constant yearly cash flows.
- Explain why the payback period ignores cash flows after the recovery date.

Example: investment 900 EUR, yearly cash flow 300 EUR, payback period 3 years.
"""


def fake_production(course_out, plan_dir, chapter_ids):
    """A finished product run as the engine leaves it: plan + published chapters + LERNMATERIAL folders."""
    run = Path(course_out) / ('ch-20260101T000000Z-' + str(len(list(Path(course_out).glob('ch-*')))).zfill(8))
    (run / 'plan').mkdir(parents=True)
    for f in ('curriculum.json', 'source_inventory.json'):
        shutil.copy2(Path(plan_dir) / f, run / 'plan' / f)
    plan = json.loads((run / 'plan' / 'curriculum.json').read_text())
    for c in plan['chapters']:
        if c['chapter_id'] in chapter_ids:
            art = run / 'chapters' / c['chapter_id'] / 'publish' / 'artifacts'; art.mkdir(parents=True)
            (art / 'kapitel.pdf').write_bytes(b'%PDF-1.4 fixture ' + c['chapter_id'].encode())
    (run / 'status.json').write_text(json.dumps({'run_state': 'COMPLETED', 'status': 'GO'}))
    return run


class Incremental(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); t = Path(self.td.name)
        self.src = t / 'course'; self.src.mkdir(); self.out = t / 'out'
        (self.src / '01 Break-even Analysis.md').write_text(A)
        (self.src / '02 Net Present Value.md').write_text(B)
        self.env = mock.patch.dict(os.environ, {'EXAM_MASTERY_OUTPUT': str(self.out), 'EXAM_MASTERY_CONFIG': str(t / 'none.json')})
        self.env.start()
        first = inc.update(self.src)
        self.assertEqual(sorted(first['summary']['NEW']), sorted(first['chapters']))
        self.ids = {v['sources'][0]: c for c, v in first['chapters'].items()}
        self.course = inc.course_dir(self.src)
        self.run = fake_production(self.course, first['plan_dir'], set(first['chapters']))
        self.snap = {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}

    def tearDown(self):
        self.env.stop(); self.td.cleanup()

    def assertRunUntouched(self):
        self.assertEqual({p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}, self.snap)

    def test_a_no_change_means_no_calls_and_no_regeneration(self):
        with mock.patch('exam_mastery.providers.execute', side_effect=AssertionError('provider called')):
            r = inc.update(self.src, produce=True)
        self.assertEqual(r['summary']['CURRENT'], sorted(self.ids.values()))
        self.assertEqual(r['to_produce'], []); self.assertEqual(r['produced'], []); self.assertEqual(r['provider_calls_made'], 0)
        self.assertEqual(r['sources'], {'new': [], 'removed': [], 'changed': []})
        self.assertTrue(r['originals_unchanged']); self.assertRunUntouched()

    def test_b_new_lecture_is_inventoried_as_new_chapter(self):
        (self.src / '03 Payback Period.md').write_text(C)
        r = inc.update(self.src)
        self.assertEqual(r['sources']['new'], ['03 Payback Period.md'])
        new = r['summary']['NEW']; self.assertEqual(len(new), 1)
        self.assertEqual(r['chapters'][new[0]]['sources'], ['03 Payback Period.md'])
        inv = json.loads((Path(r['plan_dir']) / 'source_inventory.json').read_text())
        self.assertIn('03 Payback Period.md', inc.source_hashes(inv))
        self.assertEqual(sorted(r['summary']['CURRENT']), sorted(self.ids.values()))

    def test_c_and_e_changed_slide_marks_only_its_chapter(self):
        (self.src / '02 Net Present Value.md').write_text(B.replace('r = 10 %', 'r = 8 %').replace('41.32', '69.96'))
        st = inc.status(self.src)
        self.assertEqual(st['source_changes_since_last_plan']['changed'], ['02 Net Present Value.md'])
        r = inc.update(self.src)
        npv, be = self.ids['02 Net Present Value.md'], self.ids['01 Break-even Analysis.md']
        self.assertEqual(r['chapters'][npv]['state'], 'STALE')
        self.assertEqual(r['chapters'][npv]['changed_sources'], ['02 Net Present Value.md'])
        self.assertEqual(r['chapters'][be]['state'], 'CURRENT')
        self.assertEqual(r['to_produce'], [npv]); self.assertRunUntouched()

    def test_d_removed_source_marks_dependent_materials_outdated(self):
        (self.src / '02 Net Present Value.md').unlink()
        r = inc.update(self.src)
        npv = self.ids['02 Net Present Value.md']
        self.assertEqual(r['sources']['removed'], ['02 Net Present Value.md'])
        self.assertEqual(r['chapters'][npv]['state'], 'SOURCE_REMOVED')
        self.assertIsNotNone(r['chapters'][npv]['materials'])           # kept, not deleted
        self.assertEqual(r['chapters'][self.ids['01 Break-even Analysis.md']]['state'], 'CURRENT')
        self.assertRunUntouched()

    def test_d_replaced_source_with_new_content(self):
        (self.src / '02 Net Present Value.md').unlink(); (self.src / '02 Payback Period.md').write_text(C)
        r = inc.update(self.src)
        self.assertEqual(r['chapters'][self.ids['02 Net Present Value.md']]['state'], 'SOURCE_REMOVED')
        self.assertEqual(len(r['summary']['NEW']), 1)

    def test_g_quota_stop_keeps_products_and_update_resumes(self):
        from exam_mastery.budget import BudgetBlocked, QUOTA_BLOCKED
        (self.src / '02 Net Present Value.md').write_text(B.replace('r = 10 %', 'r = 8 %'))
        cfg = {'provider': 'codex', 'model': 'm'}
        with mock.patch('exam_mastery.product.run_product', side_effect=BudgetBlocked(QUOTA_BLOCKED, 'usage limit')):
            r = inc.update(self.src, produce=True, cfg=cfg)
        self.assertEqual(r['produce'], QUOTA_BLOCKED); self.assertRunUntouched()
        again = inc.update(self.src)
        self.assertEqual(again['to_produce'], [self.ids['02 Net Present Value.md']])   # still pending, safely resumable
        with mock.patch('exam_mastery.product.run_product', side_effect=RuntimeError('render crash')):
            r = inc.update(self.src, produce=True, cfg=cfg)
        self.assertEqual(r['produce'], 'FAILED'); self.assertRunUntouched()

    def test_produce_runs_only_the_changed_chapter(self):
        (self.src / '01 Break-even Analysis.md').write_text(A.replace('12000', '15000').replace('600 units', '750 units'))
        calls = []
        def fake(root, cfg, output_base=None, provider=None, only_chapter=None):
            calls.append(only_chapter); return Path('/x'), {'run_state': 'COMPLETED'}, {'release': {'technical': 'X'}}
        with mock.patch('exam_mastery.product.run_product', side_effect=fake):
            r = inc.update(self.src, produce=True, cfg={'provider': 'codex', 'model': 'm'})
        self.assertEqual(calls, [self.ids['01 Break-even Analysis.md']]); self.assertEqual(r['produce'], 'DONE')

    def test_cli_status_update_and_cwd_default(self):
        from exam_mastery.runtime import main
        cwd = os.getcwd()
        try:
            os.chdir(self.src)
            self.assertEqual(main(['status']), 0)
            self.assertEqual(main(['update']), 0)
            self.assertEqual(main([]), 3)            # no setup: fail-closed, no call
            os.chdir(Path.home())
            self.assertEqual(main(['status']), 2)    # home is never a course folder
        finally:
            os.chdir(cwd)


class AnkiIdentity(unittest.TestCase):
    """F: a content update of an exported deck keeps note identity and the learner's scheduling; no duplicates."""

    def build(self, run, cards):
        from exam_mastery.publish import publish_cards
        from exam_mastery.anki_qa import verify
        (run / 'architect.json').write_text(json.dumps({'course_id': 'course-x:ch-1', 'title': 'Kapitel'}))
        publish_cards({'course_id': 'course-x', 'title': 'Kapitel'}, {'cards': cards},
                      {'theme': {'ink': '#000', 'accent': '#111', 'paper': '#fff', 'surface': '#eee'}}, run / 'artifacts' / 'anki')
        verify(run)
        return run / 'artifacts' / 'anki' / 'Anki_Karten.apkg'

    def test_f_reexport_updates_without_duplicates_and_keeps_scheduling(self):
        try:
            from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
        except ImportError:
            self.skipTest('anki not installed')
        cards = [{'id': f'ch-1:a-0{i}', 'question': f'Frage {i}?', 'answer': f'Antwort {i}', 'explanation': 'x', 'source_refs': ['s']} for i in range(1, 4)]
        with tempfile.TemporaryDirectory() as td:
            t = Path(td); (t / 'v1').mkdir()
            p1 = self.build(t / 'v1', cards)
            user = Collection(str(t / 'user.anki2'))
            try:
                opts = ImportAnkiPackageOptions(merge_notetypes=False, with_scheduling=False, with_deck_configs=False)
                user.import_anki_package(ImportAnkiPackageRequest(package_path=str(p1), options=opts))
                self.assertEqual(user.note_count(), 3)
                cid = user.db.scalar('select id from cards order by id limit 1')
                card = user.get_card(cid); card.reps, card.ivl, card.due, card.type, card.queue = 4, 12, 300, 2, 2; user.update_card(card)
                sched = user.db.all('select id,nid,reps,ivl,due,type,queue from cards order by id')
                # second export: one answer corrected, one card unchanged, same ids; then exported again unchanged
                cards2 = [dict(c) for c in cards]; cards2[0]['answer'] = 'Antwort 1 (korrigiert)'
                (t / 'v1' / 'artifacts').rename(t / 'v1' / 'artifacts-old')
                p2 = self.build(t / 'v1', cards2)
                for _ in range(2):
                    user.import_anki_package(ImportAnkiPackageRequest(package_path=str(p2), options=opts))
                self.assertEqual(user.note_count(), 3)
                self.assertEqual(user.db.all('select id,nid,reps,ivl,due,type,queue from cards order by id'), sched)
                answers = sorted(user.get_note(n)['Answer'] for n in user.db.list('select id from notes'))
                self.assertIn('Antwort 1 (korrigiert)', answers)
            finally:
                user.close()


if __name__ == '__main__':
    unittest.main()
