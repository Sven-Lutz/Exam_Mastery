"""Competency evidence: help on a sibling task and future-dated events must not create retention evidence (CD-9).

R6 red team RT-26 showed that after the CD-2 fix kc_status still reported RETAINED_ON_LATER_DAY (a) when the
learner had opened the solution of another task of the same competency a minute before the later success, because
help was only counted for the same task, and (b) when an attempt carried a future timestamp (client clock or an
imported history). Python and the browser mirror (em_tutor.js) must agree.
"""
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, policy as P, render, tracks as TR

TRACKS = {t['id']: t for t in TR.all_tracks()}
MATH = TRACKS['math/rectangle-argument-track']
KC = 'math/inscribed-rectangle'
T = lambda tid: next(t for t in MATH['tasks'] if t['id'] == tid)


def ok(tid, t):
    return {'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(T(tid), TR._answer_for(T(tid))), 't': t}


BASE = [ok('m-pre', '2026-11-10T08:00:00Z'), ok('m-core', '2026-11-10T09:00:00Z')]
CASES = {  # name: (events, reference instant, expected state of KC)
    'sibling_solution_just_before': (BASE + [{'type': 'solution', 'task': 'm-similar', 't': '2026-11-12T08:59:00Z'},
                                             ok('m-retest', '2026-11-12T09:00:00Z')], '2026-11-12T10:00:00Z', 'RETEST_DUE'),
    'sibling_tutor_just_before': (BASE + [{'type': 'tutor', 'task': 'm-transfer', 't': '2026-11-12T08:30:00Z'},
                                          ok('m-retest', '2026-11-12T09:00:00Z')], '2026-11-12T10:00:00Z', 'RETEST_DUE'),
    'sibling_help_long_before': (BASE + [{'type': 'hint', 'task': 'm-similar', 't': '2026-11-10T09:30:00Z'},
                                         ok('m-retest', '2026-11-12T09:00:00Z')], '2026-11-12T10:00:00Z', 'RETAINED_ON_LATER_DAY'),
    'future_attempt_ignored': (BASE + [ok('m-retest', '2999-01-01T00:00:00Z')], '2026-11-10T10:00:00Z', 'INDEPENDENT_PASS'),
    'clean_retention_still_counts': (BASE + [ok('m-retest', '2026-11-12T09:00:00Z')], '2026-11-12T10:00:00Z', 'RETAINED_ON_LATER_DAY'),
    'only_future_attempts': ([ok('m-core', '2999-01-01T00:00:00Z')], '2026-11-10T10:00:00Z', 'NOT_ASSESSED'),
}


class KcEvidenceScope(unittest.TestCase):
    def test_cases(self):
        for name, (ev, ref, want) in CASES.items():
            self.assertEqual(P.kc_status(MATH, ev, ref)[KC], want, name)

    def test_window_and_skew_are_named_provisional_parameters(self):
        self.assertEqual(P.KC_HELP_WINDOW_HOURS, P.RETENTION_MIN_GAP_HOURS)
        self.assertEqual(P.FUTURE_SKEW_MINUTES, 5)


class BrowserMirror(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); cls.out = Path(cls.td.name)
        render.write(MATH, cls.out / 'lernstrecken', lab_href='../labs/x.html')
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def open(self):
        pg = self.browser.new_page(); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(next((self.out / 'lernstrecken').glob('*.html')).as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        return pg, errors

    def test_js_mirror_agrees(self):
        pg, errors = self.open()
        for name, (ev, ref, want) in CASES.items():
            js = pg.evaluate('([tr,ev,ref]) => EMT.kcStatus(tr,ev,ref)', [MATH, ev, ref])
            self.assertEqual(js, P.kc_status(MATH, ev, ref), name)
            self.assertEqual(js[KC], want, name)
        self.assertEqual(errors, [])

    def test_import_refuses_future_events(self):
        pg, errors = self.open()
        n = pg.evaluate('''() => EMT.store.importObj({schema: 'em-tutor-export-v1', track: EMT.storeKey, events: [
            {t: '2026-11-10T09:00:00Z', type: 'hint', task: 'm-core'},
            {t: '2999-01-01T00:00:00Z', type: 'attempt', task: 'm-retest', diagnosis: {result: 'correct'}}]}, EMT.storeKey)''')
        self.assertEqual(n, 1)
        self.assertEqual([e['t'][:4] for e in pg.evaluate('EMT.store.events(EMT.storeKey)')], ['2026'])
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
