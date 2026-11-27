"""A proof (argument) competency must not look mastered on recognition-only evidence (CD-11).

R6 red team RT-10, reproduced by the lead: in the reference math track every deterministic evidence item of the
argument competency math/inscribed-rectangle is premise selection or multiple choice; the only construction task
(m-why) is unverified free text. kc_status therefore reported 'retained' for an argument nobody had formulated.
kc_status keeps its time semantics; kc_evidence_basis states what the evidence consists of and the learner view
says so. Python and the browser mirror must agree.
"""
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, policy as P, render, tracks as TR

TRACKS = {t['id']: t for t in TR.all_tracks()}
MATH, ML = TRACKS['math/rectangle-argument-track'], TRACKS['ml/backprop-track']
KC = 'math/inscribed-rectangle'


def ok(tr, tid, t):
    task = next(x for x in tr['tasks'] if x['id'] == tid)
    return {'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(task, TR._answer_for(task)), 't': t}


RECOG = [ok(MATH, 'm-pre', '2026-11-10T08:00:00Z'), ok(MATH, 'm-core', '2026-11-10T09:00:00Z'), ok(MATH, 'm-retest', '2026-11-12T09:00:00Z')]


class ProofEvidenceBasis(unittest.TestCase):
    def test_reproduction_recognition_only_reaches_retained(self):
        self.assertEqual(next(k for k in MATH['kcs'] if k['id'] == KC)['type'], 'argument')
        types = {t['type'] for t in MATH['tasks'] if t['kc_id'] == KC and t['type'] != 'open'}
        self.assertLessEqual(types - {'steps'}, set(P.RECOGNITION_TYPES))
        self.assertEqual(P.kc_status(MATH, RECOG, '2026-11-12T10:00:00Z')[KC], 'RETAINED_ON_LATER_DAY')
        self.assertEqual(P.kc_evidence_basis(MATH, RECOG)[KC], 'recognition_only')

    def test_production_evidence_is_named_as_such(self):
        ev = [ok(MATH, 'm-similar', '2026-11-10T09:00:00Z')]                      # 'steps': the learner computes
        self.assertEqual(P.kc_evidence_basis(MATH, ev)[KC], 'production')
        ev = [ok(ML, 'ml-core', '2026-11-10T09:00:00Z')]
        self.assertEqual(P.kc_evidence_basis(ML, ev)['ml/backpropagation'], 'production')

    def test_helped_attempts_are_no_basis(self):
        ev = [{'type': 'solution', 'task': 'm-core', 't': '2026-11-10T08:59:00Z'}, ok(MATH, 'm-core', '2026-11-10T09:00:00Z')]
        self.assertEqual(P.kc_evidence_basis(MATH, ev)[KC], 'none')


class BrowserMirror(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); out = Path(cls.td.name)
        render.write(MATH, out / 'lernstrecken', lab_href='../labs/x.html')
        cls.page_path = next((out / 'lernstrecken').glob('*.html'))
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def test_parity_and_learner_view(self):
        pg = self.browser.new_page(); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(self.page_path.as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        for ev in (RECOG, [ok(MATH, 'm-similar', '2026-11-10T09:00:00Z')], []):
            self.assertEqual(pg.evaluate('([tr, ev]) => EMT.kcEvidenceBasis(tr, ev)', [MATH, ev]), P.kc_evidence_basis(MATH, ev))
        sk = pg.evaluate('EMT.storeKey')
        pg.evaluate('([k, ev]) => localStorage.setItem("em-tutor-v1", JSON.stringify({schema: 1, tracks: {[k]: {events: ev}}}))', [sk, RECOG])
        pg.reload(); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        li = pg.locator('[data-kc="%s"]' % KC)
        self.assertEqual(li.get_attribute('data-basis'), 'recognition_only')
        self.assertIn('nur Wiedererkennen geprüft', li.inner_text())
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
