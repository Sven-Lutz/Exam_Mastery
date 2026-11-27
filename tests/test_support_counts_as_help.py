"""A worked example, contrast or step focus shown automatically after a wrong answer is help (integrity gap reported
by the tutor work, 2026-11-28): before this, a success right after such a block counted as independent evidence.
Python and the browser mirror must agree; the workbench must log the block.
"""
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, policy as P, render, tracks as TR

TRACKS = {t['id']: t for t in TR.all_tracks()}
ML = TRACKS['ml/backprop-track']
NOW = '2026-11-10T10:00:00Z'


def attempt(tid, ans, t=NOW):
    task = next(x for x in ML['tasks'] if x['id'] == tid)
    return {'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(task, ans), 't': t}


class SupportIsHelp(unittest.TestCase):
    def test_success_after_worked_example_is_not_independent(self):
        ok = next(x for x in ML['tasks'] if x['id'] == 'ml-pre2')
        ev = [{'type': 'support', 'task': 'ml-core', 'kind': 'worked_example', 'kc': ok['kc_id'], 't': NOW},
              {'type': 'attempt', 'task': 'ml-pre2', 'diagnosis': D.diagnose(ok, TR._answer_for(ok)), 't': '2026-11-10T10:05:00Z'}]
        self.assertIn('support', P.ASSIST_EVENTS)
        self.assertNotEqual(P.kc_status(ML, ev, '2026-11-10T11:00:00Z')[ok['kc_id']], 'INDEPENDENT_PASS')
        self.assertEqual(P.kc_evidence_basis(ML, ev)[ok['kc_id']], 'none')


class BrowserLogsSupport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); out = Path(cls.td.name)
        render.write(ML, out / 'l', lab_href='../labs/x.html')
        cls.page = next((out / 'l').glob('*.html'))
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def test_shown_support_block_is_logged_and_parity_holds(self):
        pg = self.browser.new_page(); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(self.page.as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        pre = next(x for x in ML['tasks'] if x['id'] == 'ml-pre')
        pg.fill('#ans', str(TR._answer_for(pre)).replace('.', ',')); pg.click('#check'); pg.click('#next')
        for _ in range(3):                                                    # unrecognised errors -> RU worked example
            if pg.locator('[data-support]').count():
                break
            pg.fill('#ans', 'x1*x2*v2'); pg.click('#check')
        self.assertGreaterEqual(pg.locator('[data-support]').count(), 1)
        ev = pg.evaluate('EMT.store.events(EMT.storeKey)')
        sup = [e for e in ev if e['type'] == 'support']
        self.assertTrue(sup and sup[-1]['kc'])
        ml = ML
        ref = pg.evaluate('([tr, ev]) => EMT.kcStatus(tr, ev)', [ml, ev])
        self.assertEqual(ref, P.kc_status(ml, ev))
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
