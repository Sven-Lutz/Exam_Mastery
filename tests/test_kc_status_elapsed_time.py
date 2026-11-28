"""kc_status: retention evidence needs elapsed time and a different task (CD-2, R0 §2, R1 A01/A05).

Before this fix two independent successes on different calendar dates counted as 'retained on a later day',
even at 23:59 and 00:01 or on the very same task. Python and the browser mirror (em_tutor.js) must agree.
"""
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, policy as P, render, tracks as TR

TRACKS = {t['id']: t for t in TR.all_tracks()}
MATH = TRACKS['math/rectangle-argument-track']
KC = 'math/inscribed-rectangle'
T = lambda tid: next(t for t in MATH['tasks'] if t['id'] == tid)


def attempt(ev, tid, ans, t):
    ev.append({'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(T(tid), ans), 't': t})


def history(case):
    ev = []
    attempt(ev, 'm-pre', 'parallelogram', '2026-11-10T23:50:00Z')
    if case == 'midnight':        # two tasks, 2 minutes apart across midnight
        attempt(ev, 'm-core', ['mid', 'len', 'distinct'], '2026-11-10T23:59:00Z')
        attempt(ev, 'm-transfer', 'square', '2026-11-11T00:01:00Z')
    elif case == 'same_task':     # the same task solved again a day later: not a new item
        attempt(ev, 'm-core', ['mid', 'len', 'distinct'], '2026-11-10T23:59:00Z')
        attempt(ev, 'm-core', ['mid', 'len', 'distinct'], '2026-11-12T09:00:00Z')
    elif case == 'later_new_task':  # new task after a night
        attempt(ev, 'm-core', ['mid', 'len', 'distinct'], '2026-11-10T23:59:00Z')
        attempt(ev, 'm-retest', 'rect', '2026-11-12T09:00:00Z')
    elif case == 'later_but_helped':
        attempt(ev, 'm-core', ['mid', 'len', 'distinct'], '2026-11-10T23:59:00Z')
        ev.append({'type': 'hint', 'task': 'm-retest', 't': '2026-11-12T08:59:00Z'})
        attempt(ev, 'm-retest', 'rect', '2026-11-12T09:00:00Z')
    return ev


EXPECTED = {  # (reference instant, expected status)
    'midnight': [('2026-11-11T00:05:00Z', 'INDEPENDENT_PASS'), ('2026-11-12T00:00:00Z', 'RETEST_DUE')],
    'same_task': [('2026-11-12T10:00:00Z', 'RETEST_DUE')],
    'later_new_task': [('2026-11-12T10:00:00Z', 'RETAINED_ON_LATER_DAY')],
    'later_but_helped': [('2026-11-12T10:00:00Z', 'RETEST_DUE')],
}


class KcStatusElapsedTime(unittest.TestCase):
    def test_cases(self):
        for case, checks in EXPECTED.items():
            for ref, want in checks:
                self.assertEqual(P.kc_status(MATH, history(case), ref)[KC], want, (case, ref))

    def test_bare_date_reference_is_start_of_day_utc(self):
        ev = history('midnight')
        self.assertEqual(P.kc_status(MATH, ev, '2026-11-11')[KC], 'INDEPENDENT_PASS')
        self.assertEqual(P.kc_status(MATH, ev, '2026-11-12')[KC], 'RETEST_DUE')

    def test_gap_is_a_named_provisional_parameter(self):
        self.assertEqual(P.RETENTION_MIN_GAP_HOURS, 20)


class KcStatusBrowserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory()
        cls.out = Path(cls.td.name)
        render.write(MATH, cls.out / 'lernstrecken', lab_href='../labs/x.html')
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def test_js_mirror_agrees(self):
        page = next((self.out / 'lernstrecken').glob('*.html'))
        pg = self.browser.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(page.as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        for case, checks in EXPECTED.items():
            ev = history(case)
            for ref, want in checks + [('2026-11-11', None)]:
                js = pg.evaluate('([tr,ev,ref]) => EMT.kcStatus(tr,ev,ref)', [MATH, ev, ref])
                self.assertEqual(js, P.kc_status(MATH, ev, ref), (case, ref))
                if want:
                    self.assertEqual(js[KC], want, (case, ref))
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
