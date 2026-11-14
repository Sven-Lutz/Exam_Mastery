"""B16: mathematical scenes. Reference models, scene validation and real-browser checks that formula, figure and number
show the same model state (offline, no network, no console errors)."""
import copy
import json
import math
import random
import tempfile
import unittest
from pathlib import Path

from exam_mastery.labs import build as B, models as M, scenes as SC

ORD = [0, 100, 180, 190, 210, 230, 250, 270]; COST = [102, 122, 172, 152, 242, 152, 162, 172]; INV = [200, 500, 300, 140]


def leaves(x, path=''):
    """All numeric leaves of a nested dict/list as {path: value} (same path syntax as the scenes)."""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            out.update(leaves(v, f'{path}.{k}' if path else str(k)))
        return out
    if isinstance(x, (list, tuple)):
        out = {}
        for i, v in enumerate(x):
            out.update(leaves(v, f'{path}.{i}' if path else str(i)))
        return out
    return {path: x} if isinstance(x, (int, float)) and not isinstance(x, bool) else {}


class Models(unittest.TestCase):
    def test_mlp_trace_agrees_with_backprop_and_finite_differences(self):
        for seed, ha, oa in ((7, 'sigmoid', 'sigmoid'), (3, 'tanh', 'linear'), (11, 'relu', 'sigmoid')):
            p = M.mlp_init(seed=seed); x = [0.4, -0.9]; t = 0.3
            tr = M.mlp_trace(p, x, t, 0.5, ha, oa); n = M.mlp_numeric_grad(p, x, t, hidden_act=ha, out_act=oa)
            for j in (0, 1):
                self.assertAlmostEqual(tr['part'][j][1] + p['b1'][j], tr['z1'][j], places=14)
                for i in (0, 1):   # the chain shown in the scene equals the gradient and the finite difference
                    chain = tr['delta_o'] * p['W2'][j] * tr['fprime'][j] * x[i]
                    self.assertAlmostEqual(chain, tr['grad']['W1'][j][i], places=14)
                    self.assertAlmostEqual(chain, n['W1'][j][i], places=7)
            self.assertAlmostEqual(tr['after']['loss'] - tr['loss'], tr['dloss'], places=15)
            self.assertAlmostEqual(tr['new']['W1'][0][0], p['W1'][0][0] - 0.5 * tr['grad']['W1'][0][0], places=15)

    def test_relu_dead_unit_has_zero_gradient(self):
        p = {'W1': [[-1.0, -1.0], [0.5, 0.5]], 'b1': [-0.5, 0.0], 'W2': [0.7, 0.3], 'b2': 0.1}
        tr = M.mlp_trace(p, [1.0, 1.0], 0.9, 0.5, 'relu', 'sigmoid')
        self.assertEqual(tr['fprime'][0], 0.0); self.assertEqual(tr['grad']['W1'][0], [0.0, 0.0])

    def test_chord_lift_properties(self):
        for s, t in ((0.0, 0.42), (0.13, 0.77), (0.5, 0.5)):
            a, b = M.chord_lift(s, t), M.chord_lift(t, s)
            self.assertEqual(a['lift'], b['lift'])                       # unordered pair
            self.assertGreaterEqual(a['d'], 0)
        self.assertEqual(M.chord_lift(0.3, 0.3)['d'], 0.0)              # P = Q lands on the curve
        L = M.chord_lift(0.3, 0.3); self.assertEqual(L['lift'][:2], tuple(M.curve_point(0.3)))
        u = 0.37; h = 1e-6
        num = [(a - b) / (2 * h) for a, b in zip(M.curve_point(u + h), M.curve_point(u - h))]
        self.assertLess(max(abs(a - b) for a, b in zip(num, M.curve_deriv(u))), 1e-6)   # analytic derivative

    def test_rectangle_search_finds_verified_rectangles(self):
        found = 0
        for k in range(12):
            s = k / 12
            for r in M.rect_search(s):
                found += 1
                self.assertLess(r['residual'], 1e-11)
                self.assertLess(M.rect_check(r['corners']), 1e-9)          # independent: four right angles
                for c in r['corners']:                                     # corners lie on the curve
                    u = [r['s'], r['u'], r['t'], r['v']][r['corners'].index(c)]
                    self.assertLess(math.dist(c, M.curve_point(u)), 1e-12)
                self.assertAlmostEqual(M.chord_lift(r['s'], r['t'])['d'], M.chord_lift(r['u'], r['v'])['d'], places=9)
        self.assertGreaterEqual(found, 10)

    def test_circle_diameters_share_one_lift_point(self):
        circle = {'r0': 1.0, 'terms': []}
        for s in (0.0, 0.1, 0.33):
            L = M.chord_lift(s, s + 0.5, circle)
            self.assertAlmostEqual(L['d'], 2.0, places=12); self.assertLess(abs(L['M'][0]) + abs(L['M'][1]), 1e-12)

    def test_cashflow_ledger_matches_cashflow(self):
        for d in (0, 2, 5, 9):
            led = M.cashflow_ledger(ORD, d, COST, INV); r = M.cashflow(ORD, d, COST, INV)
            self.assertEqual([x['balance'] for x in led['rows']], r['balance'])
            self.assertEqual(sum(s['amount'] for s in led['sales'] if s['within']), sum(r['inflow']))
            for row in led['rows']:
                self.assertAlmostEqual(row['prev'] + row['inflow'] - row['cost'] - row['invest'], row['balance'], places=9)


class SceneValidation(unittest.TestCase):
    def specs(self):
        return [B.mlp_spec(), B.chord_spec(), B.cashflow_spec('ent/cashflow', 'Liquidität', ['kc'], ['Folie 21'], ORD, 5, COST, INV)]

    def test_reference_scenes_are_valid_and_complete(self):
        for s in self.specs():
            self.assertTrue(B.validate(s)); sc = s['scene']
            self.assertTrue(all(sc['didactics'][k] for k in SC.DIDACTICS))
            self.assertTrue(sc['expect']['values'])

    def test_validator_rejects_broken_scenes(self):
        base = B.mlp_spec()
        bad = []
        s = copy.deepcopy(base); s['scene']['expect']['values']['loss'] += 1e-6; bad.append(('value', s))
        s = copy.deepcopy(base); s['scene']['steps'][0]['targets'] = ['nope']; bad.append(('ref', s))
        s = copy.deepcopy(base); s['scene']['steps'][0]['formula'].append({'v': 'not.a.path', 'd': 2}); bad.append(('path', s))
        s = copy.deepcopy(base); s['scene']['steps'][2]['anim'] = {'kind': 'sparkle'}; bad.append(('anim', s))
        s = copy.deepcopy(base); s['scene']['didactics']['misconception'] = ''; bad.append(('didactics', s))
        s = copy.deepcopy(base); s['scene']['objects'][0]['role'] = 'decor'; bad.append(('role', s))
        s = copy.deepcopy(base); s['scene']['steps'][9]['formula'][0]['ref'] = 'w{J}9'; bad.append(('var ref', s))
        for name, sp in bad:
            with self.assertRaises(B.LabError, msg=name):
                B.validate(sp)

    def test_every_selection_resolves(self):
        s = B.mlp_spec(); tr = SC.trace(s)
        for v in SC._var_space(s['scene']):
            vals = SC.values(s['scene'], tr, v)
            self.assertTrue(all(isinstance(x, float) for x in vals.values()))


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest('playwright not installed')
        cls.tmp = tempfile.TemporaryDirectory(); d = Path(cls.tmp.name)
        cls.nn = B.mlp_spec(); cls.ch = B.chord_spec()
        cls.cf = B.cashflow_spec('ent/cashflow', 'Liquidität', ['kc-cf'], ['Folie 21'], ORD, 5, COST, INV, course='Test')
        cls.paths = {k: B.render(s, d / 'labs') for k, s in (('nn', cls.nn), ('ch', cls.ch), ('cf', cls.cf))}
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, key, **ctx):
        ctx.setdefault('offline', True); ctx.setdefault('reduced_motion', 'reduce')
        c = self.browser.new_context(**ctx); pg = c.new_page()
        errors, requests = [], []
        pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('request', lambda r: requests.append(r.url) if not r.url.startswith(('file:', 'data:')) else None)
        pg.goto(self.paths[key].as_uri())
        pg.locator('html[data-em-ready="1"]').wait_for()
        pg.click('text=Ohne Vorhersage erkunden')
        self.addCleanup(c.close)
        return pg, errors, requests

    def wait_until(self, fn, seconds):
        import time
        end = time.time() + seconds
        while time.time() < end:
            if fn():
                return
            time.sleep(0.05)
        self.fail('condition not reached')

    def step(self, pg, n):
        pg.locator('.em-steps-dots li button').nth(n).click(); pg.locator(f'.em-scene[data-step="{n}"]').wait_for()

    def shown(self, pg):
        return pg.evaluate("[...document.querySelectorAll('.em-fbox .em-num')].map(e => [e.dataset.path, Number(e.dataset.val), e.textContent])")

    def assert_synced(self, pg, tr, label):
        """every number in the formula equals the Python trace at that path; every linked term has a figure object"""
        for path, val, text in self.shown(pg):
            want = SC.get(tr, path)
            self.assertIsNotNone(want, f'{label}: {path}')
            self.assertLess(abs(val - want), 1e-12 * max(1, abs(want)), f'{label}: {path} browser {val} python {want}')
            self.assertTrue(text.strip(), path)
        refs = pg.evaluate("[...new Set([...document.querySelectorAll('.em-fbox .em-tok[data-ref]')].map(e => e.dataset.ref))]")
        for r in refs:
            self.assertGreater(pg.locator(f'.em-graphic [data-ref="{r}"]').count(), 0, f'{label}: term {r} has no object in the figure')

    def test_js_traces_equal_python(self):
        pg, errors, _ = self.open('nn')
        rnd = random.Random(16)
        for ha, oa in (('sigmoid', 'sigmoid'), ('tanh', 'linear'), ('relu', 'sigmoid'), ('linear', 'linear')):
            p = M.mlp_init(seed=rnd.randint(1, 99)); x = [rnd.uniform(-2, 2), rnd.uniform(-2, 2)]; t = rnd.random()
            js = leaves(pg.evaluate('a => EM.models.mlpTrace(a[0], a[1], a[2], 0.7, a[3], a[4])', [p, x, t, ha, oa]))
            py = leaves(M.mlp_trace(p, x, t, 0.7, ha, oa))
            self.assertEqual(set(js), set(py))
            self.assertLess(max(abs(js[k] - py[k]) for k in py), 1e-12)
        for s, t in ((0.0, 0.42), (0.21, 0.9), (0.66, 0.1)):
            js = leaves(pg.evaluate('a => EM.models.chordTrace(a[0], a[1])', [s, t])); py = leaves(M.chord_trace(s, t))
            self.assertEqual(set(js), set(py)); self.assertLess(max(abs(js[k] - py[k]) for k in py), 1e-9)
        for d in (0, 3, 5, 8):
            js = leaves(pg.evaluate('a => EM.models.cashTrace({orders: a[0], cost: a[1], invest: a[2], delay: a[3], delayB: a[3] + 1, start_cash: 0, horizon: 8})', [ORD, COST, INV, d]))
            py = leaves(M.cash_trace(ORD, d, COST, INV, 0, 8, d + 1))
            self.assertEqual(set(js), set(py), d); self.assertLess(max(abs(js[k] - py[k]) for k in py), 1e-9)
        self.assertEqual(errors, [])

    def test_network_formula_figure_and_numbers_stay_in_sync(self):
        pg, errors, requests = self.open('nn')
        n = pg.locator('.em-steps-dots li').count(); self.assertEqual(n, len(self.nn['scene']['steps']))
        tr = SC.trace(self.nn)
        for k in range(n):
            self.step(pg, k); self.assert_synced(pg, tr, f'step {k}')
        # default values of the scene equal the stored expectation (Python)
        self.step(pg, 9)
        self.assertIn('w11', pg.inner_text('.em-step-title'))
        # select neuron h2 and input x2 by clicking the edge w22 in the figure: the chain now runs through w22
        pg.locator('.em-graphic polyline.em-hit[data-ref="w22"]').click(force=True)
        self.assertIn('w22', pg.inner_text('.em-step-title')); self.assert_synced(pg, tr, 'w22')
        self.assertEqual(pg.get_attribute('.em-graphic [data-ref="h2"]', 'class').count('em-picked'), 1)
        # click a term: the corresponding edge is highlighted
        pg.locator('.em-fbox .em-tok[data-ref="v2"]').first.click()
        self.assertIn('em-hot', pg.get_attribute('.em-graphic line[data-ref="v2"]', 'class'))
        self.assertEqual(errors, []); self.assertEqual(requests, [])

    def test_network_direct_manipulation_changes_the_computation(self):
        pg, errors, _ = self.open('nn')
        self.step(pg, 2)
        lab = pg.locator('.em-graphic text[data-ref="w11"]'); lab.focus()
        for _ in range(4):
            pg.keyboard.press('ArrowUp')
        w = float(pg.input_value('#p-w11'))
        self.assertAlmostEqual(w, round(self.nn['model']['init']['W1'][0][0] + 0.2, 3), places=9)
        tr = SC.trace(self.nn, {'w11': w}); self.assert_synced(pg, tr, 'after keyboard')
        e = pg.locator('.em-graphic line[data-ref="w11"]').bounding_box(); y = e['y'] + e['height'] / 2   # grab the edge itself
        pg.mouse.move(e['x'] + e['width'] * .6, y); pg.mouse.down(); pg.mouse.move(e['x'] + e['width'] * .6 + 60, y, steps=4); pg.mouse.up()
        w2 = float(pg.input_value('#p-w11')); self.assertGreater(w2, w)
        self.assert_synced(pg, SC.trace(self.nn, {'w11': w2}), 'after drag')
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-loss')), SC.trace(self.nn, {'w11': w2})['loss'], places=12)
        self.assertEqual(errors, [])

    def test_player_controls_and_keyboard(self):
        pg, errors, _ = self.open('nn')
        sc = pg.locator('.em-scene'); cur = lambda: int(sc.get_attribute('data-step'))
        pg.click('.em-player >> text=Weiter'); self.assertEqual(cur(), 1)
        pg.click('.em-player >> text=Zurück'); self.assertEqual(cur(), 0)
        self.assertTrue(pg.locator('.em-player >> text=Zurück').is_disabled())
        pg.select_option('.em-speed select', '2')
        pg.click('.em-player >> text=Abspielen'); self.wait_until(lambda: cur() >= 2, 15)
        pg.click('.em-player >> text=Pause'); s = cur(); pg.wait_for_timeout(2500); self.assertEqual(cur(), s)
        self.assertEqual(sc.get_attribute('data-playing'), '')
        pg.click('.em-player >> text=Neustart'); self.assertEqual(cur(), 0)
        sc.focus(); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight'); self.assertEqual(cur(), 2)
        pg.keyboard.press('ArrowLeft'); self.assertEqual(cur(), 1)
        tok = pg.locator('.em-fbox .em-tok[data-ref]').first; tok.focus(); pg.keyboard.press('Enter')
        self.assertIn('em-hot', tok.get_attribute('class'))
        self.assertTrue(pg.is_checked('.em-rm input'))                      # follows prefers-reduced-motion
        self.assertEqual(errors, [])

    def test_animation_runs_without_reduced_motion(self):
        pg, errors, _ = self.open('nn', reduced_motion='no-preference')
        self.assertFalse(pg.is_checked('.em-rm input'))
        self.step(pg, 2)
        self.wait_until(lambda: pg.locator('.em-pulse').count() > 0, 3)     # the signal travels along the edge
        self.wait_until(lambda: pg.locator('.em-pulse').count() == 0, 5)
        self.step(pg, 10)
        pg.wait_for_timeout(1600)
        tr = SC.trace(self.nn)
        self.assertEqual(pg.text_content('.em-graphic text[data-ref="w11"]'), 'w11 = ' + f'{tr["new"]["W1"][0][0]:.3f}'.replace('.', ',').replace('-', '−'))
        self.assertEqual(errors, [])

    def test_chord_scene_drag_lift_and_rectangle(self):
        pg, errors, requests = self.open('ch')
        n = len(self.ch['scene']['steps']); tr = SC.trace(self.ch)
        for k in range(n):
            self.step(pg, k); self.assert_synced(pg, tr, f'chord {k}')
            self.assertEqual(pg.get_attribute('.em-graphic svg', 'data-cam'), self.ch['scene']['steps'][k]['camera'])
        self.step(pg, 3)
        q = pg.locator('.em-graphic [data-drag="Q"]'); q.focus()
        for _ in range(6):
            pg.keyboard.press('ArrowRight')
        t = float(pg.input_value('#p-t')); self.assertAlmostEqual(t, 0.45, places=9)
        self.assert_synced(pg, SC.trace(self.ch, {'t': t}), 'moved Q')
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-d')), M.chord_lift(0.0, t)['d'], places=12)
        # drag P with the mouse to another place on the curve
        p = pg.locator('.em-graphic [data-drag="P"]').bounding_box()
        pg.mouse.move(p['x'] + p['width'] / 2, p['y'] + p['height'] / 2); pg.mouse.down(); pg.mouse.move(p['x'] - 90, p['y'] - 160, steps=6); pg.mouse.up()
        s = float(pg.input_value('#p-s')); self.assertNotEqual(s, 0.0)
        tr2 = SC.trace(self.ch, {'s': s, 't': t}); self.step(pg, 7); self.assert_synced(pg, tr2, 'rectangle after drag')
        if tr2['rect']:
            self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-rect-area')), tr2['rect']['area'], places=9)
        self.assertIn('kein Beweis', pg.inner_text('.em-scene-host'))
        self.assertEqual(errors, []); self.assertEqual(requests, [])

    def test_chord_edge_case_equal_points(self):
        pg, errors, _ = self.open('ch')
        pg.fill('#p-t', '0'); pg.dispatch_event('#p-t', 'input')
        self.step(pg, 3)
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-d')), 0.0)
        self.assertEqual(pg.text_content('.em-fbox .em-num[data-path="d"]'), '0')
        self.assertEqual(errors, [])

    def test_cashflow_process_shifts_payments_and_rebuilds_liquidity(self):
        pg, errors, requests = self.open('cf')
        n = pg.locator('.em-steps-dots li').count(); self.assertEqual(n, 5 + len(ORD))
        tr = SC.trace(self.cf)
        for k in range(n):
            self.step(pg, k); self.assert_synced(pg, tr, f'cash {k}')
        # period steps build the balance curve one point at a time
        self.step(pg, 3); self.assertEqual(pg.get_attribute('.em-graphic svg', 'data-progress'), '1')
        self.step(pg, 6); self.assertEqual(pg.locator('.em-bal-dot').count(), 4)
        # payment term 5 -> 2: the first payment (sale in P2, 100) now arrives in P4 instead of P7
        self.step(pg, 1)
        x_before = pg.evaluate("[...document.querySelectorAll('.em-tok-pay:not(.em-empty)')].map(e => +e.getAttribute('x'))")
        pg.fill('#p-delay', '2'); pg.dispatch_event('#p-delay', 'input')
        self.assertEqual(pg.locator('.em-graphic .em-tok-pay:not(.em-empty)[data-ref="in4"]').count(), 1)
        x_after = pg.evaluate("[...document.querySelectorAll('.em-tok-pay:not(.em-empty)')].map(e => +e.getAttribute('x'))")
        self.assertLess(min(x_after), min(x_before))
        self.assertGreater(len(x_after), len(x_before))                  # more payments arrive within the horizon
        tr2 = SC.trace(self.cf, {'delay': 2}); self.step(pg, n - 2); self.assert_synced(pg, tr2, 'delay 2')
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-need')), tr2['financing_need'])
        # edge: horizon change changes the number of period steps
        pg.fill('#p-horizon', '12'); pg.dispatch_event('#p-horizon', 'input')
        self.assertEqual(pg.locator('.em-steps-dots li').count(), 5 + 12)
        self.assert_synced(pg, SC.trace(self.cf, {'delay': 2, 'horizon': 12}), 'horizon 12')
        self.assertEqual(errors, []); self.assertEqual(requests, [])

    def test_mobile_dark_no_overflow_and_readable(self):
        for key in ('nn', 'ch', 'cf'):
            pg, errors, _ = self.open(key, viewport={'width': 390, 'height': 844}, color_scheme='dark')
            self.assertTrue(pg.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), key)
            box = pg.locator('.em-graphic svg').bounding_box(); self.assertGreater(box['width'], 300, key)
            fg = pg.evaluate("getComputedStyle(document.querySelector('.em-step-title')).color")
            self.assertNotEqual(fg, 'rgb(0, 0, 0)', key)                  # dark tokens applied
            self.assertEqual(errors, [], key)

    def test_existing_labs_still_render_without_scene(self):
        rk = B.risk_spec('ent/risk', 'Risiko', ['kc-r'], ['Folie 29']); self.assertNotIn('scene', rk)
        p = B.render(rk, Path(self.tmp.name) / 'labs')
        c = self.browser.new_context(offline=True); pg = c.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.goto(p.as_uri())
        pg.locator('html[data-em-ready="1"]').wait_for()
        self.assertEqual(pg.locator('.em-scene').count(), 0); self.assertEqual(errs, []); c.close()


if __name__ == '__main__':
    unittest.main()
