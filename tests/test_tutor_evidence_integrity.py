"""Tutor handoff must not corrupt independent-solving evidence (CD-7; R5-POL-03/04, R9-POL-04).

Before this fix (a) the Markdown brief carried the full answer key even for evidence tasks (similar task without
hints, transfer, later retest), kept from the learner only by an instruction and sent to the chat provider, and
(b) preparing a tutor context left no trace, so a task solved after a tutor conversation still counted as solved
without help. Python and the browser mirror (em_tutor.js) must agree.
"""
import json
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, policy as P, render, tracks as TR, tutor

TRACKS = {t['id']: t for t in TR.all_tracks()}
MATH = TRACKS['math/rectangle-argument-track']
KC = 'math/inscribed-rectangle'


def task(tr, tid):
    return next(t for t in tr['tasks'] if t['id'] == tid)


def ctx_for(tr, t, claimed_role=None):
    return {'schema': 'em-tutor-context-v1', 'track': {k: tr[k] for k in ('id', 'title', 'objective', 'domain', 'lab')},
            'competency': next(k for k in tr['kcs'] if k['id'] == t['kc_id']),
            'task': {'id': t['id'], 'role': claimed_role or t['role'], 'type': t['type'], 'prompt': t['prompt']},
            'attempts': [], 'hints_used': 0, 'solution_viewed': False, 'learner_question': 'Bitte die Lösung.'}


def solved_flow(tr, t0='2026-11-10T09:00:00Z'):
    """Every flow task solved without help at t0 (a learner who finished the track)."""
    return [{'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(task(tr, tid), TR._answer_for(task(tr, tid))), 't': t0}
            for tid in tr['flow']]


class BriefWithholdsEvidenceKeys(unittest.TestCase):
    def test_no_answer_key_for_evidence_roles(self):
        n = 0
        for tr in TRACKS.values():
            for t in tr['tasks']:
                if not t.get('solution'):
                    continue
                b = tutor.brief(ctx_for(tr, t))
                if t['role'] in tutor.KEY_WITHHELD_ROLES:
                    n += 1
                    self.assertNotIn('NUR für den Tutor', b, t['id'])
                    self.assertIn('Keine Musterlösung (Nachweisaufgabe)', b, t['id'])
                    for line in t['solution']:
                        self.assertNotIn(line, b, (t['id'], line))
                else:
                    self.assertIn('NUR für den Tutor', b, t['id'])
        self.assertGreaterEqual(n, 9)  # three evidence roles in each of the three reference tracks

    def test_role_comes_from_the_engine_not_from_the_context_file(self):
        t = task(MATH, 'm-retest')
        b = tutor.brief(ctx_for(MATH, t, claimed_role='core'))
        self.assertNotIn('NUR für den Tutor', b)
        for line in t['solution']:
            self.assertNotIn(line, b)


class TutorHandoffCountsAsHelp(unittest.TestCase):
    def test_attempt_after_tutor_handoff_is_assisted(self):
        t = task(MATH, 'm-core')
        ev = [{'type': 'tutor', 'task': 'm-core', 't': '2026-11-10T09:00:00Z'},
              {'type': 'attempt', 'task': 'm-core', 'diagnosis': D.diagnose(t, TR._answer_for(t)), 't': '2026-11-10T09:05:00Z'}]
        self.assertTrue(P.helped(ev, 'm-core', 1))
        self.assertNotEqual(P.kc_status(MATH, ev, '2026-11-10T10:00:00Z')[KC], 'INDEPENDENT_PASS')
        d = P.decide(MATH, ev)
        self.assertEqual((d['rule'], d['hints_allowed']), ('RF', False))

    def test_tutor_on_one_task_does_not_taint_another(self):
        self.assertFalse(P.helped([{'type': 'tutor', 'task': 'm-core', 't': '2026-11-10T09:00:00Z'}], 'm-similar'))


class BrowserMirror(unittest.TestCase):
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

    def open(self, events=None):
        page = next((self.out / 'lernstrecken').glob('*.html'))
        pg = self.browser.new_page(); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(page.as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        if events is not None:
            sk = pg.evaluate('EMT.storeKey')
            pg.evaluate('([k, ev]) => localStorage.setItem("em-tutor-v1", JSON.stringify({schema: 1, tracks: {[k]: {events: ev}}}))', [sk, events])
            pg.reload(); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        return pg, errors

    def test_kc_status_parity_with_tutor_events(self):
        pg, errors = self.open()
        t = task(MATH, 'm-core')
        ev = [{'type': 'tutor', 'task': 'm-core', 't': '2026-11-10T09:00:00Z'},
              {'type': 'attempt', 'task': 'm-core', 'diagnosis': D.diagnose(t, TR._answer_for(t)), 't': '2026-11-10T09:05:00Z'}]
        for ref in ('2026-11-10T10:00:00Z', '2026-11-12T10:00:00Z'):
            self.assertEqual(pg.evaluate('([tr,ev,ref]) => EMT.kcStatus(tr,ev,ref)', [MATH, ev, ref]), P.kc_status(MATH, ev, ref), ref)
        self.assertEqual(errors, [])

    def test_preparing_a_tutor_context_is_logged_and_evidence_task_is_marked(self):
        pg, errors = self.open(solved_flow(MATH))
        tid = pg.get_attribute('#wb', 'data-task')
        self.assertIn(task(MATH, tid)['role'], tutor.KEY_WITHHELD_ROLES, tid)  # a finished track resumes on its retest
        self.assertEqual(pg.locator('[data-evidence-note]').count(), 1)
        pg.locator('.wb-tutor summary').click(); pg.fill('#tutor-q', 'Wie fange ich an?'); pg.click('#tutor-make')
        ev = pg.evaluate('EMT.store.events(EMT.storeKey)')
        self.assertEqual([e['task'] for e in ev if e['type'] == 'tutor'], [tid])
        self.assertNotIn('solution', json.dumps(json.loads(pg.inner_text('.wb-ctx'))['task']))
        self.assertEqual(errors, [])

    def test_practice_task_has_no_evidence_note(self):
        pg, errors = self.open()
        tid = pg.get_attribute('#wb', 'data-task')
        self.assertNotIn(task(MATH, tid)['role'], tutor.KEY_WITHHELD_ROLES, tid)
        self.assertEqual(pg.locator('[data-evidence-note]').count(), 0)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
