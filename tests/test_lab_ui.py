"""Gerenderte Interaktionen des Labors (labor.html) – echte Klicks, Tastatur und Zeiger im Chromium.

Prüft, dass die Darstellung exakt das zeigt, was ein unabhängiges Python-Orakel berechnet,
und dass Entdeckungspfad, Challenges, Hypothesenprüfung, Zustandslinks und Mobilansicht funktionieren.
"""
import base64
import json
import math
import tempfile
import unittest
from pathlib import Path

from exam_mastery import reference_unit as RU

UNIT = Path(__file__).resolve().parents[1] / 'units/nlp_sequence_labeling'
try:
    from playwright.sync_api import sync_playwright
    HAVE = (RU.NODE / 'mathjax-full/es5/tex-svg-full.js').exists()
except ImportError:
    HAVE = False


def softmax(s, T=1.0):
    m = max(s)
    e = [math.exp((x - m) / T) for x in s]
    return [x / sum(e) for x in e]


def de(x, d=3):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


@unittest.skipUnless(HAVE, 'playwright and MathJax runtime required')
class Lab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name)
        RU.build(UNIT, cls.out, pdf=False, anki=False)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, lab='attention', state=None, vw=1300, vh=950):
        ctx = self.browser.new_context(viewport={'width': vw, 'height': vh})
        self.addCleanup(ctx.close)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        h = f'#lab={lab}'
        if state is not None:
            h += '&s=' + base64.b64encode(json.dumps(state).encode()).decode()
        pg.goto((self.out / 'labor.html').as_uri() + h)
        pg.wait_for_function('document.body.dataset.ready === "1"', timeout=30000)
        self.addCleanup(lambda: self.assertEqual(errs, []))
        return pg

    def state(self, pg):
        m = pg.evaluate('location.hash').split('s=')[1]
        return json.loads(base64.b64decode(m + '=' * (-len(m) % 4)).decode())

    def weights_shown(self, pg):
        return pg.eval_on_selector_all('table.calc tr[data-j] td:nth-child(5)', 'ns => ns.map(n => n.textContent.trim())')

    def expected_weights(self, st):
        K = [[k[0] + st['shift'][0], k[1] + st['shift'][1]] for k in st['K']]
        c = math.sqrt(2) if st['scaled'] else 1
        return softmax([(st['q'][0] * k[0] + st['q'][1] * k[1]) / c for k in K], st['T'])

    # ---------------- Self-Attention ----------------
    def test_keyboard_and_pointer_manipulation_recompute_exactly(self):
        pg = self.open()
        st0 = self.state(pg)
        self.assertEqual(self.weights_shown(pg), [de(w) for w in self.expected_weights(st0)])
        h = pg.locator('.plane >> nth=0').locator('g.handle[data-id=q]')
        h.focus()
        for _ in range(5):
            pg.keyboard.press('ArrowUp')
        pg.keyboard.press('Shift+ArrowLeft')
        st = self.state(pg)
        self.assertAlmostEqual(st['q'][0], st0['q'][0] - .5, 9)
        self.assertAlmostEqual(st['q'][1], st0['q'][1] + .5, 9)
        self.assertEqual(self.weights_shown(pg), [de(w) for w in self.expected_weights(st)])
        # Zeiger: q zum Key von "Geld" ziehen
        box = pg.locator('.plane >> nth=0').locator('svg').bounding_box()
        hb = h.locator('circle.dot').bounding_box()
        pg.mouse.move(hb['x'] + hb['width'] / 2, hb['y'] + hb['height'] / 2)
        pg.mouse.down()
        # Koordinate (-0,4; 1,5) in Pixel: Bereich x∈[-2,5;2,5], y∈[-2;2]
        pg.mouse.move(box['x'] + (2.1 / 5) * box['width'], box['y'] + (0.5 / 4) * box['height'], steps=8)
        pg.mouse.up()
        st = self.state(pg)
        self.assertLess(abs(st['q'][0] + .4), .06)
        self.assertLess(abs(st['q'][1] - 1.5), .06)
        w = self.expected_weights(st)
        self.assertEqual(w.index(max(w)), 1)
        self.assertEqual(self.weights_shown(pg), [de(x) for x in w])
        pg.screenshot(path=str(self.out / 'att_after_drag.png'))

    def test_temperature_and_scale_limits(self):
        st = self.open()
        st0 = self.state(st)
        for T, scaled in [(0.05, True), (9.97, False)]:
            s = dict(st0, T=T, scaled=scaled)
            pg = self.open(state=s)
            w = self.expected_weights(s)
            self.assertEqual(self.weights_shown(pg), [de(x) for x in w])
        self.assertGreater(max(self.expected_weights(dict(st0, T=0.05))), .99)

    def test_shift_all_keys_keeps_weights(self):
        pg = self.open()
        before = self.weights_shown(pg)
        g = pg.locator('g.handle[data-id=shift]'); g.focus()
        for _ in range(6):
            pg.keyboard.press('Shift+ArrowRight')
        st = self.state(pg)
        self.assertAlmostEqual(st['shift'][0], 3.0, 6)
        self.assertEqual(self.weights_shown(pg), before)
        raw = pg.eval_on_selector_all('table.calc tr[data-j] td.expand b', 'ns => ns.map(n => n.textContent)')
        self.assertNotEqual(raw[0], '1,20')

    def test_guided_step_requires_prediction_then_reveals(self):
        pg = self.open()
        step = pg.locator('.step').first
        g = pg.locator('g.handle[data-id=q]'); g.focus()
        for _ in range(12):
            pg.keyboard.press('ArrowUp')
        for _ in range(3):
            pg.keyboard.press('Shift+ArrowLeft')
        self.assertIn('Vorhersage', step.locator('.goal-state').inner_text())
        self.assertEqual(step.locator('.reveal').count(), 0)
        step.locator('.pred-opts button').first.click()
        g.focus(); pg.keyboard.press('ArrowUp')
        step.locator('.reveal').wait_for()
        self.assertIn('längsten Projektion', step.locator('.reveal').inner_text())

    def test_challenge_uniform_via_numeric_inputs_and_impossible_reasoning(self):
        pg = self.open()
        pg.get_by_role('tab', name='Challenges').click()
        c = pg.locator('.chal', has_text='Gleichgültig')
        c.get_by_role('button', name='Starten').click()
        pg.wait_for_timeout(800)
        pg.locator('details.numbers summary').click()
        inputs = pg.locator('.numgrid input.num')
        vals = ['2', '0', '1', '1', '1', '-1', '1', '0,5']   # q, k1, k2, k3
        for i, v in enumerate(vals):
            inputs.nth(i).fill(v); inputs.nth(i).dispatch_event('change')
            inputs = pg.locator('.numgrid input.num')
        c.locator('.badge.ok').wait_for()
        self.assertIn('Gleichverteilt bei langer Query', c.inner_text())
        imp = pg.locator('.chal', has_text='Unerreichbar')
        imp.get_by_role('button', name='Starten').click(); pg.wait_for_timeout(800)
        imp.get_by_role('button', name='Ich halte das für unmöglich').click()
        imp.locator('.pred-opts button').nth(1).click()
        self.assertIn('gleichauf', imp.locator('.verdict.bad').inner_text())
        imp.locator('.pred-opts button').nth(0).click()
        imp.locator('.reveal').wait_for()
        self.assertIn('Konvexkombination', imp.inner_text())

    def test_hypothesis_check_reports_cause(self):
        pg = self.open()
        pg.get_by_role('tab', name='Hypothese').click()
        pg.select_option('.hyp select >> nth=0', 'H')
        pg.select_option('.hyp select >> nth=1', 'down')
        pg.fill('.hyp textarea', 'Kleinere Temperatur macht die Verteilung spitzer.')
        pg.get_by_role('button', name='Hypothese festhalten').click()
        pg.locator('input[type=range]').first.fill('-1')
        pg.get_by_role('button', name='Prüfen').click()
        v = pg.locator('.verdict').inner_text()
        self.assertIn('Bestätigt', v)
        self.assertIn('Kleinere Temperatur', pg.locator('.hyp .reveal').inner_text())

    def test_sentence_permutation_equivariance_and_pe_counterexample(self):
        pg = self.open()
        pg.get_by_role('button', name='Ganzer Satz').click()
        pg.get_by_role('button', name='Mia nach rechts').click()
        self.assertIn('Reihenfolge unsichtbar', pg.locator('p.verdict').inner_text())
        dists = pg.eval_on_selector_all('table.diff tr td:nth-child(3)', 'ns => ns.map(n => n.textContent)')
        self.assertTrue(all(d == '0,0000' for d in dists), dists)
        pg.get_by_role('checkbox', name='Positionsvektoren', exact=False).check()
        self.assertIn('andere Ausgabe', pg.locator('p.verdict').inner_text())
        pg.screenshot(path=str(self.out / 'att_sentence_pe.png'), full_page=True)

    def test_state_link_reproduces_exact_view(self):
        pg = self.open()
        g = pg.locator('g.handle[data-id=k2]'); g.focus(); pg.keyboard.press('Shift+ArrowDown')
        url = pg.url
        w1 = self.weights_shown(pg)
        pg2 = self.open(state=self.state(pg))
        self.assertEqual(self.weights_shown(pg2), w1)
        self.assertIn('lab=attention', url)

    def test_reduced_motion_toggle_persists(self):
        pg = self.open()
        pg.get_by_role('button', name='Bewegung reduzieren').click()
        self.assertTrue(pg.evaluate("document.body.classList.contains('reduced')"))
        pg.reload(); pg.wait_for_function('document.body.dataset.ready === "1"')
        self.assertTrue(pg.evaluate("document.body.classList.contains('reduced')"))

    # ---------------- weitere Labore ----------------
    def test_crf_forbidding_transitions_repairs_and_logz_matches_bruteforce(self):
        pg = self.open('crf')
        rows = pg.locator('.badge', has_text='BIO')
        self.assertIn('ungültiges', rows.nth(1).inner_text())
        pg.locator('table.matrix tr', has_text='Start').locator('input[type=checkbox]').nth(1).check()
        pg.locator('table.matrix tr').filter(has=pg.locator('th', has_text='O')).last.locator('input[type=checkbox]').nth(1).check()
        self.assertIn('gültiges', pg.locator('.badge', has_text='BIO').nth(1).inner_text())
        self.assertNotIn('ungültiges', pg.locator('.badge', has_text='BIO').nth(1).inner_text())
        m = pg.eval_on_selector_all('.meters .m b', 'ns => ns.map(n => n.textContent)')
        self.assertEqual(m[1], m[2])   # log Z vorwärts == alle Pfade
        pg.get_by_role('tab', name='Entdecken').click()
        self.assertGreaterEqual(pg.locator('.step.done').count(), 1)

    def test_birnn_forward_only_cannot_see_future(self):
        pg = self.open('birnn')
        pg.get_by_label('Rückwärts-RNN aktiv').uncheck()
        before = pg.locator('.formula-live b').inner_text()
        pg.select_option('select[aria-label="Wort 2"]', 'state')
        self.assertEqual(pg.locator('.formula-live b').inner_text(), before)
        pg.get_by_label('Rückwärts-RNN aktiv').check()
        self.assertIn('Ort', pg.locator('.plane svg').first.inner_html())

    def test_spans_boundary_error_costs_fp_and_fn(self):
        pg = self.open('spans')
        pg.get_by_role('button', name='Vorhersage = Gold').click()
        self.assertIn('= 1,000', pg.locator('.formula-live').inner_text())
        pg.get_by_role('button', name='Merkel: Vorhersage I-PER').click()   # → B-LOC
        pg.get_by_role('button', name='Merkel: Vorhersage B-LOC').click()   # → I-LOC
        txt = pg.locator('.formula-live').inner_text()
        self.assertIn('P = 2/(2+2)', txt)   # [Angela]PER und [Merkel]LOC sind FP
        self.assertIn('R = 2/(2+1)', txt)   # [Angela Merkel]PER ist FN

    def test_all_labs_mobile_no_horizontal_scroll(self):
        for lab in ('attention', 'crf', 'birnn', 'spans'):
            pg = self.open(lab, vw=390, vh=844)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            self.assertLessEqual(sw, 392, lab)
            pg.screenshot(path=str(self.out / f'{lab}_mobile.png'))


if __name__ == '__main__':
    unittest.main()


SOLVE = {  # Challenge-ID -> (Lab, Zustandsänderung) – belegt, dass jedes erreichbare Ziel wirklich erreichbar ist
    'c-spot': ('attention', lambda s: s.update(q=[-1.4, -2])),
    'c-uniform': ('attention', lambda s: s.update(q=[2, 0], K=[[1, 1], [1, -1], [1, .5]])),
    'c-target': ('attention', lambda s: s.update(q=[.85, 1.5], T=.3, target=[1, 1])),
    'c-order': ('attention', lambda s: (s.update(view='sent'), s['sent'].update(causal=True, order=[2, 1, 0, 3]))),
    'k-soft': ('crf', lambda s: s.update(s=[0, -.3, 0])),
    'k-sure': ('crf', lambda s: s.update(A=[[0, 3, 0], [0, 3, 0], [0, 0, 0]], Fs=[False, True, False], FA=[[False] * 3, [False] * 3, [False, True, False]])),
    'k-mm': ('crf', lambda s: s.update(E=[[.2, -.7, 2.4], [-2, 2.1, 3], [-.5, 2.8, 0], [1.8, 1, .5]], Fs=[False, True, False], FA=[[False] * 3, [False] * 3, [False, True, False]])),
    'n-far': ('birnn', lambda s: (s.update(words=['Washington', 'state', 'the', 'a'], ub=2), s['bw'].update(wh=1.4))),
    'n-sat': ('birnn', lambda s: (s.update(words=['Washington', 'state', 'the', 'bill']), s['bw'].update(b=2))),
    'f-half': ('spans', lambda s: s.update(pred=['B-PER', 'B-PER', 'O', 'O', 'O', 'O', 'O', 'O', 'B-ORG', 'B-ORG'])),
    'f-prec': ('spans', lambda s: s.update(pred=['B-PER', 'I-PER'] + ['O'] * 8)),
    'f-macro': ('spans', lambda s: s.update(gold=['B-PER', 'I-PER', 'O', 'B-PER', 'O', 'B-PER', 'O', 'O', 'B-ORG', 'I-ORG'], pred=['B-PER', 'I-PER', 'O', 'B-PER', 'O', 'B-PER', 'O', 'O', 'O', 'O'])),
}


class Solvable(Lab):
    test_keyboard_and_pointer_manipulation_recompute_exactly = None
    test_temperature_and_scale_limits = None
    test_shift_all_keys_keeps_weights = None
    test_guided_step_requires_prediction_then_reveals = None
    test_challenge_uniform_via_numeric_inputs_and_impossible_reasoning = None
    test_hypothesis_check_reports_cause = None
    test_sentence_permutation_equivariance_and_pe_counterexample = None
    test_state_link_reproduces_exact_view = None
    test_reduced_motion_toggle_persists = None
    test_crf_forbidding_transitions_repairs_and_logz_matches_bruteforce = None
    test_birnn_forward_only_cannot_see_future = None
    test_spans_boundary_error_costs_fp_and_fn = None
    test_all_labs_mobile_no_horizontal_scroll = None

    def test_every_reachable_challenge_has_a_verified_solution(self):
        init = {}
        for cid, (lab, patch) in SOLVE.items():
            if lab not in init:
                init[lab] = self.state(self.open(lab))
            st = json.loads(json.dumps(init[lab]))
            patch(st)
            pg = self.open(lab, state=st)
            pg.get_by_role('tab', name='Challenges').click()
            self.assertEqual(pg.locator(f'.chal.solved[data-id="{cid}"]').count(), 1, cid)
            self.assertEqual(pg.locator('.chal.solved').count(), 1, cid)

    def test_saturation_challenge_has_exactly_one_answer(self):
        st = self.state(self.open())
        solved = []
        for d in (1, 2, 4, 8, 16, 32, 64, 128, 256, 512):
            s = json.loads(json.dumps(st)); s['view'] = 'dim'; s['dim']['d'] = d
            pg = self.open(state=s)
            pg.get_by_role('tab', name='Challenges').click()
            if pg.locator('.chal.solved', has_text='Sättigung').count():
                solved.append(d)
        self.assertEqual(len(solved), 1, solved)
