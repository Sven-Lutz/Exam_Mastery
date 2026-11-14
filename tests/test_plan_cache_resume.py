"""Performance hotfix: a resumed chapter run reuses its plan when nothing planning depends on changed
(source snapshot, engine code, run arguments, course-level files such as visual_evidence.json)."""
import json, os, tempfile, unittest
from pathlib import Path
from unittest import mock
from exam_mastery import runtime as R


class PlanCache(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); t = Path(self.td.name)
        self.root = t / 'lecture'; self.root.mkdir(); (self.root / 'a.txt').write_text('x')
        self.course = t / 'course'; self.course.mkdir()
        self.out = t / 'course_out' / 'run'; (self.out / 'plan').mkdir(parents=True); (self.out / 'plan' / 'x.json').write_text('{}')
        self.calls = 0
        p = mock.patch('exam_mastery.incremental.course_dir', return_value=self.course); p.start(); self.addCleanup(p.stop)

    def tearDown(self):
        self.td.cleanup()

    def plan(self, root, out, decisions, **kw):
        self.calls += 1
        return ({'readiness': 'R', 'n': self.calls}, {'chapters': []}, {'elements': []}, {}, [])

    def run_once(self, before='S1', engine='E1', only='ch-1'):
        return R._cached_plan(self.plan, self.root, self.out, before, engine, None, only, None, None)

    def test_unchanged_resume_hits(self):
        first = self.run_once(); second = self.run_once()
        self.assertEqual((first[-1]['result'], second[-1]['result']), ('MISS', 'HIT'))
        self.assertEqual(self.calls, 1)
        self.assertEqual(first[:5], second[:5])

    def test_any_relevant_change_replans(self):
        self.run_once()
        for kw in ({'before': 'S2'}, {'engine': 'E2'}, {'only': 'ch-2'}):
            n = self.calls
            self.assertEqual(self.run_once(**kw)[-1]['result'], 'MISS', kw)
            self.assertEqual(self.calls, n + 1)
        n = self.calls
        self.run_once(only='ch-2')                       # back to an unchanged state: hit again
        self.assertEqual(self.calls, n)
        (self.course / 'visual_evidence.json').write_text(json.dumps({'pages': []}))   # new figure reading
        self.assertEqual(self.run_once(only='ch-2')[-1]['result'], 'MISS')

    def test_resume_pointer_is_not_a_planning_input(self):
        self.run_once()
        (self.course / 'active_chapters-abc.json').write_text('{"run_dir": "x"}')
        self.assertEqual(self.run_once()[-1]['result'], 'HIT')

    def test_corrupt_cache_replans(self):
        self.run_once()
        for f in (self.out.parent / '.plan_cache').glob('*.pkl'):
            f.write_bytes(b'garbage')
        self.assertEqual(self.run_once()[-1]['result'], 'MISS')


    def test_new_run_same_course_reuses_and_copies_plan_files(self):
        self.run_once()
        other = self.out.parent / 'run2'
        r = R._cached_plan(self.plan, self.root, other, 'S1', 'E1', None, 'ch-1', None, None)
        self.assertEqual(r[-1]['result'], 'HIT'); self.assertEqual(self.calls, 1)
        self.assertTrue((other / 'plan' / 'x.json').exists())

    def test_deleted_source_run_replans(self):
        self.run_once()
        import shutil; shutil.rmtree(self.out / 'plan')
        other = self.out.parent / 'run2'
        self.assertEqual(R._cached_plan(self.plan, self.root, other, 'S1', 'E1', None, 'ch-1', None, None)[-1]['result'], 'MISS')


if __name__ == '__main__':
    unittest.main()
