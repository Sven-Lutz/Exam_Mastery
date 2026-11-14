"""B13: interactive labs. Reference models (numerics), spec validation, and the real browser runtime:
JS models == Python models, prediction -> simulation -> feedback -> transfer, hints, solution gating, invalid input,
reset, keyboard, mobile width, dark mode, offline (zero network requests) and CSP."""
import itertools
import json
import math
import random
import tempfile
import unittest
from pathlib import Path

from exam_mastery.labs import build as B, models as M

ORD = [0, 100, 180, 190, 210, 230, 250, 270]
COST = [50 + g + x + 2 for g, x in zip([10, 30, 50, 40, 140, 60, 70, 80], [40, 40, 70, 60, 50, 40, 40, 40])]
INV = [200, 500, 300, 140]


def flat(d):
    return [*itertools.chain(*d['W1']), *d['b1'], *d['W2'], d['b2']]


class CashflowModel(unittest.TestCase):
    def test_lecture_example_regression(self):
        r = M.cashflow(ORD, 5, COST, INV)
        self.assertEqual(r['cf'], [-302, -622, -472, -292, -242, -152, -62, 8])
        self.assertEqual((r['min_balance'], r['min_period'], r['final_balance'], r['financing_need']), (-2144, 7, -2136, 2144))

    def test_independent_recomputation_random(self):
        rnd = random.Random(3)
        for _ in range(200):
            T = rnd.randint(1, 12); o = [rnd.randint(0, 300) for _ in range(T)]; c = [rnd.randint(0, 200) for _ in range(T)]
            inv = [rnd.randint(0, 400) for _ in range(rnd.randint(0, T))]; d = rnd.randint(0, 6); s0 = rnd.randint(0, 500)
            r = M.cashflow(o, d, c, inv, s0)
            bal, s = [], s0
            for t in range(T):
                s += (o[t - d] if t - d >= 0 else 0) - c[t] - (inv[t] if t < len(inv) else 0); bal.append(s)
            self.assertEqual(r['balance'], bal)
            self.assertEqual(r['financing_need'], max(0, -min(bal)))

    def test_edge_cases(self):
        self.assertEqual(M.cashflow([0], 0, [0], [])['financing_need'], 0)
        self.assertIsNone(M.cashflow([10, 10], 0, [5, 5], [])['first_shortfall'])
        r = M.cashflow([100, 100], 3, [10, 10], [], horizon=2)
        self.assertEqual(r['unpaid_orders'], 200)                  # payments after the horizon are not counted
        self.assertEqual(M.cashflow(ORD, 5, COST, INV, start_cash=3000)['financing_need'], 0)
        for bad in (-1, 1.5):
            with self.assertRaises(ValueError):
                M.cashflow(ORD, bad, COST, INV)

    def test_later_payment_never_lowers_need(self):
        rnd = random.Random(5)
        for _ in range(100):
            T = 8; o = [rnd.randint(0, 300) for _ in range(T)]; c = [rnd.randint(0, 200) for _ in range(T)]
            needs = [M.cashflow(o, d, c, [100])['financing_need'] for d in range(6)]
            self.assertEqual(needs, sorted(needs))                # monotone in the payment delay (non-negative orders)


class MlpModel(unittest.TestCase):
    def test_backprop_equals_finite_differences(self):
        for seed, ha, oa in itertools.product(range(5), ('sigmoid', 'tanh', 'linear'), ('sigmoid', 'linear')):
            p = M.mlp_init(seed=seed); x = [0.3 * seed - 0.5, 0.7]; t = 0.25
            g = flat(M.mlp_backward(p, x, t, ha, oa)['grad']); n = flat(M.mlp_numeric_grad(p, x, t, hidden_act=ha, out_act=oa))
            self.assertLess(max(abs(a - b) for a, b in zip(g, n)), 1e-7, (seed, ha, oa))

    def test_independent_numpy_reference(self):
        import numpy as np
        p = M.mlp_init(seed=7); x = np.array([0.5, -1.0]); t = 0.8
        W1, b1, W2, b2 = np.array(p['W1']), np.array(p['b1']), np.array(p['W2']), p['b2']
        sig = lambda z: 1 / (1 + np.exp(-z))
        a1 = sig(W1 @ x + b1); y = sig(W2 @ a1 + b2); do = (y - t) * y * (1 - y); dh = do * W2 * a1 * (1 - a1)
        ref = [*np.outer(dh, x).ravel(), *dh, *(do * a1), do]
        self.assertLess(max(abs(a - b) for a, b in zip(flat(M.mlp_backward(p, list(x), t)['grad']), ref)), 1e-12)

    def test_training_with_small_rate_reduces_loss(self):
        p = M.mlp_init(seed=7); _, L = M.mlp_train(p, [0.5, -1.0], 0.8, 0.5, 30)
        self.assertTrue(all(b < a for a, b in zip(L, L[1:])))

    def test_saturation_shrinks_gradient(self):
        p = {'W1': [[8.0, 0.0], [0.1, 0.1]], 'b1': [0.0, 0.0], 'W2': [1.0, 1.0], 'b2': 0.0}
        g = M.mlp_backward(p, [1.0, 1.0], 0.0)['grad']
        self.assertLess(abs(g['W1'][0][0]), abs(g['W1'][1][0]) / 50)   # saturated unit 1 vs unsaturated unit 2


class RiskModel(unittest.TestCase):
    def test_lecture_example_and_ordinal_limit(self):
        self.assertEqual(M.risk_matrix(3, 4)['score'], 12)
        self.assertEqual(M.risk_matrix(2, 5)['score'], M.risk_matrix(5, 2)['score'])
        self.assertEqual((M.risk_matrix(2, 5)['class'], M.risk_matrix(5, 2)['class']), ('High', 'Moderate'))   # lecture matrix: class by cell
        self.assertEqual(M.risk_matrix(3, 4)['class'], 'High')                                                 # lecture example: 12 = high
        a, b = M.expected_loss_range(2, 400000), M.expected_loss_range(5, 10000)
        self.assertGreater(a[0], b[1])                            # same score, clearly different expected loss
        with self.assertRaises(ValueError):
            M.risk_matrix(0, 3)


class VanWestendorpModel(unittest.TestCase):
    def test_matches_delivered_standalone_lab(self):
        # regression values reported by the independently written stand-alone Lab 04 (JavaScript) for its synthetic set
        d = M.psm_synthetic()
        self.assertEqual(len(d), 240)
        st, al = M.van_westendorp(d, 'standard')['points'], M.van_westendorp(d, 'alternative')['points']
        for got, exp in ((st, {'pmc': 36.98, 'opp': 49.885, 'ipp': 52.17, 'pme': 68.43}), (al, {'pmc': 43.785, 'opp': 49.885, 'ipp': 52.17, 'pme': 57.50})):
            for k, v in exp.items():
                self.assertAlmostEqual(got[k], v, places=6, msg=k)

    def test_hand_example(self):
        rows = [{'tc': 10, 'cheap': 20, 'exp': 30, 'te': 40}, {'tc': 20, 'cheap': 30, 'exp': 40, 'te': 50}]
        sh = M.psm_shares(rows, 30)
        self.assertEqual((sh['tc'], sh['cheap'], sh['exp'], sh['te']), (0.0, 0.5, 0.5, 0.0))   # answers equal to p count
        self.assertEqual(M.psm_crossing([40, 50], [0.30, 0.10], [0.15, 0.35]), 43.75)
        self.assertEqual(M.psm_crossing([0, 1, 2, 3], [1, 0.5, 0.5, 0], [0, 0.5, 0.5, 1]), 1.5)    # coinciding stretch: midpoint
        self.assertIsNone(M.psm_crossing([0, 1], [1, 1], [0, 0]))

    def test_points_agree_with_independent_numpy_crossings(self):
        # The reference joins ECDF values at observed knots. A raw step-function root is
        # NOT a valid oracle for that interpolation, especially for equality plateaus.
        import numpy as np
        rnd = random.Random(5)
        for _ in range(25):
            prices = np.array([sorted(round(rnd.uniform(10,90)*rnd.uniform(.4,1.8),2) for _ in range(4)) for _ in range(rnd.randint(8,60))])
            rows = [dict(zip(M.PSM_KEYS,r)) for r in prices]
            xs = np.unique(np.r_[0, prices.flatten(), math.ceil(max(1,prices.max())*1.1/10)*10])
            cur = {k: (prices[:,j,None] >= xs[None,:]-1e-9).mean(axis=0) if j<2 else (prices[:,j,None] <= xs[None,:]+1e-9).mean(axis=0) for j,k in enumerate(M.PSM_KEYS)}
            cur.update(not_cheap=1-cur['cheap'],not_exp=1-cur['exp'])
            for method in ('standard','alternative'):
                r = M.van_westendorp(rows,method)
                for key,(a,b) in M.PSM_CROSSINGS[method].items():
                    # definition: the first event in price order - a tie (midpoint of that contiguous equal run)
                    # or a strict sign change (linear root between the two knots)
                    diff = cur[a]-cur[b]; zero = np.abs(diff) < 1e-10; expected = None
                    for j in range(len(xs)):
                        if zero[j]:
                            e = j
                            while e + 1 < len(xs) and zero[e + 1]:
                                e += 1
                            expected = (xs[j] + xs[e]) / 2; break
                        if j + 1 < len(xs) and not zero[j + 1] and diff[j] * diff[j + 1] < 0:
                            expected = float(np.interp(0.0, [diff[j + 1], diff[j]], [xs[j + 1], xs[j]]) if diff[j] > 0 else np.interp(0.0, [diff[j], diff[j + 1]], [xs[j], xs[j + 1]])); break
                    if expected is None:
                        self.assertIsNone(r['points'][key])
                    else:
                        self.assertAlmostEqual(r['points'][key], expected, places=8)

    def test_invalid_rows_counted_and_excluded(self):
        rows = M.psm_synthetic()[:10] + [{'tc': 30, 'cheap': 20, 'exp': 40, 'te': 50}, {'tc': 0, 'cheap': 1, 'exp': 2, 'te': 3}, {'tc': 'x', 'cheap': 1, 'exp': 2, 'te': 3}]
        r = M.van_westendorp(rows)
        self.assertEqual((r['n_valid'], r['n_invalid'], r['invalid_rows']), (10, 3, [11, 12, 13]))
        with self.assertRaises(ValueError):
            M.van_westendorp([{'tc': 3, 'cheap': 2, 'exp': 1, 'te': 0.5}])

    def test_mechanism_only_curves_that_change_move_their_points(self):
        d = M.psm_synthetic()
        for seg in ('all', 'A', 'B'):
            a = M.van_westendorp(d, segment=seg); b = M.van_westendorp(d, segment=seg, te_shift=7)
            self.assertAlmostEqual(a['points']['ipp'], b['points']['ipp']); self.assertAlmostEqual(a['points']['pmc'], b['points']['pmc'])
            self.assertGreater(b['points']['opp'], a['points']['opp']); self.assertGreater(b['points']['pme'], a['points']['pme'])
            self.assertLess(a['points']['pmc'], a['points']['pme'])
        # scaling every answer scales every price point (unit invariance of the method)
        s = [{k: (r[k] * 2 if k in M.PSM_KEYS else r[k]) for k in r} for r in d]
        for k, v in M.van_westendorp(d)['points'].items():
            self.assertAlmostEqual(M.van_westendorp(s)['points'][k], 2 * v, places=6)


class SpecValidation(unittest.TestCase):
    def spec(self):
        return B.cashflow_spec('t/cf', 'T', ['k'], ['s'], ORD, 5, COST, INV)

    def test_valid_specs(self):
        for s in (self.spec(), B.mlp_spec(), B.risk_spec('t/r', 'R', ['k'], ['s'])):
            self.assertTrue(B.validate(s))

    def test_rejects_wrong_test_case_and_bad_prediction(self):
        s = self.spec(); s['tests'][0]['financing_need'] = 2136
        with self.assertRaises(B.LabError):
            B.validate(s)
        s = self.spec(); s['sequence']['predict']['correct'] = 'vielleicht'
        with self.assertRaises(B.LabError):
            B.validate(s)
        s = self.spec(); s['sequence']['tasks'][0]['errors'].append({'value': s['sequence']['tasks'][0]['expected'], 'message': 'x'})
        with self.assertRaises(B.LabError):
            B.validate(s)

    def test_html_is_self_contained_with_csp(self):
        with tempfile.TemporaryDirectory() as td:
            h = B.render(self.spec(), td).read_text()
            self.assertIn("default-src 'none'", h)
            self.assertNotIn('http://', h.replace('http://www.w3.org/2000/svg', ''))
            self.assertNotIn('https://', h)
            self.assertNotIn('eval(', h)


class VanWestendorpSpec(unittest.TestCase):
    def test_spec_numbers_and_synthetic_label(self):
        s = B.vw_spec('pricing/van-westendorp', 'VW', ['kc-x'], ['Folie 24'])
        B.validate(s)
        self.assertEqual(s['sequence']['predict']['correct'], 'opp_pme')
        t = {x['id']: x for x in s['sequence']['tasks']}
        self.assertEqual(t['share']['expected'], 60.0); self.assertEqual(t['cross']['expected'], 43.75)
        self.assertAlmostEqual(t['range']['expected'], M.van_westendorp(M.psm_synthetic(), segment='B')['range_width'])
        self.assertTrue(s['model']['synthetic']); self.assertIn('SYNTHETISCH', ' '.join(s['assumptions']))
        self.assertEqual(s['model']['data_origin'], 'SYNTHETIC_DEMO_NOT_LECTURE_RESULTS')
        bad = json.loads(json.dumps(s)); bad['assumptions'] = bad['assumptions'][1:]
        with self.assertRaises(B.LabError):
            B.validate(bad)
        bad = json.loads(json.dumps(s)); bad['tests'][0]['points']['opp'] = 50.0
        with self.assertRaises(B.LabError):
            B.validate(bad)
        svg = B.static_svg(s)
        self.assertIn('OPP 49,89', svg); self.assertIn('SYNTHETISCH', svg)

    def test_catalogue_uses_only_matching_competencies_and_their_anchors(self):
        from exam_mastery.labs.integrate import catalog_requests
        kcs = [{'kc_id': 'kc-a', 'statement': 'Erkläre/explain: Survey: Van Westendorp-Method', 'source_anchor_ids': ['el-1', 'el-2']},
               {'kc_id': 'kc-b', 'statement': 'Erkläre/explain: PRICING', 'source_anchor_ids': ['el-3']}]
        r = catalog_requests(kcs)
        self.assertEqual(len(r), 1); self.assertEqual(r[0]['kc_ids'], ['kc-a']); self.assertEqual(r[0]['source_refs'], ['el-1', 'el-2'])
        self.assertEqual(catalog_requests(kcs[1:]), [])
        self.assertEqual(catalog_requests(kcs, {'van_westendorp'}), [])            # an author request wins, no duplicate


class Pedagogy(unittest.TestCase):
    def specs(self):
        return [B.cashflow_spec('e/cf', 'CF', ['k'], ['s'], ORD, 5, COST, INV), B.risk_spec('e/r', 'R', ['k'], ['s']),
                B.vw_spec('p/vw', 'VW', ['k'], ['s']), B.mlp_spec()]

    def test_every_lab_has_the_full_sequence_and_solvable_missions(self):
        from exam_mastery.labs import pedagogy as P
        for s in self.specs():
            q = s['sequence']
            self.assertTrue(q['predict']['explain_prompt'] and q['predict']['explain_keys'] and q['takeaways'] and q['summary_prompt'])
            self.assertTrue({'predict', 'observe', 'practice'} <= set(q['phases']))
            if 'explore' in q['phases']:
                self.assertGreaterEqual(len(q['explore']), 2, s['model']['kind'])
            else:
                self.assertEqual(q['explore'], [])                     # B15: no exploration block where the goal does not need it
            self.assertEqual([t['id'] for t in q['tasks'] if t.get('transfer')], [q['tasks'][-1]['id']])   # transfer comes last
            for m in q['explore']:
                d0 = P.defaults(s); w = {**d0, **m['witness']}
                self.assertFalse(P.holds(m['cond'], P.metrics(s, d0), d0))
                self.assertTrue(P.holds(m['cond'], P.metrics(s, w), w))

    def test_validator_rejects_weak_sequences(self):
        s = self.specs()[0]
        bad = json.loads(json.dumps(s)); bad['sequence']['explore'][0]['witness'] = {'start_cash': 10}
        with self.assertRaisesRegex(B.LabError, 'not solvable'):
            B.validate(bad)
        bad = json.loads(json.dumps(s)); bad['sequence']['explore'][0]['cond'] = [{'m': 'need', 'op': '>', 'v': 0}]
        with self.assertRaisesRegex(B.LabError, 'already holds'):
            B.validate(bad)
        bad = json.loads(json.dumps(s)); [o.update(feedback='') for t in bad['sequence']['tasks'] if t.get('type') == 'choice' for o in t['options']]
        with self.assertRaisesRegex(B.LabError, 'diagnostic feedback'):
            B.validate(bad)
        bad = json.loads(json.dumps(s)); del bad['sequence']['predict']['explain_prompt']
        with self.assertRaises(B.LabError):
            B.validate(bad)


class Integration(unittest.TestCase):
    def test_only_known_models_and_chapter_competencies_are_built(self):
        from exam_mastery.labs.integrate import build_chapter_labs
        reqs = [{'model': 'cashflow', 'lab_id': 'c/cf', 'title': 'CF', 'kc_ids': ['k1'], 'source_refs': ['e1'],
                 'data': {'orders': ORD, 'delay': 5, 'cost': COST, 'invest': INV}},
                {'model': 'fourier', 'lab_id': 'c/ft', 'title': 'FT', 'kc_ids': ['k1'], 'data': {}},
                {'model': 'risk', 'lab_id': 'c/r', 'title': 'R', 'kc_ids': ['fremd'], 'data': {}},
                {'model': 'cashflow', 'lab_id': 'c/bad', 'title': 'B', 'kc_ids': ['k1'], 'data': {'orders': ORD}}]
        with tempfile.TemporaryDirectory() as td:
            rep, blocks = build_chapter_labs(reqs, td, 'Kurs', lambda r: 'Folie 21', ['k1'])
            self.assertEqual([r['status'] for r in rep], ['BUILT', 'NOT_AVAILABLE', 'NOT_AVAILABLE', 'NOT_AVAILABLE'])
            self.assertEqual(len(blocks), 1); self.assertIn('<svg', blocks[0]['svg'])
            self.assertTrue((Path(td) / 'labs' / 'c__cf.html').exists()); self.assertFalse((Path(td) / 'labs' / 'c__ft.html').exists())


class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise unittest.SkipTest('playwright not installed')
        cls.tmp = tempfile.TemporaryDirectory(); d = Path(cls.tmp.name)
        cls.cf = B.cashflow_spec('ent/cashflow', 'Liquidität', ['kc-cf'], ['Folie 21'], ORD, 5, COST, INV, course='Test')
        cls.nn = B.mlp_spec(); cls.rk = B.risk_spec('ent/risk', 'Risiko', ['kc-r'], ['Folie 29'])
        cls.vw = B.vw_spec('pricing/van-westendorp', 'Van Westendorp', ['kc-vw'], ['Folie 24'], 'Test')
        cls.paths = {k: B.render(s, d / 'labs') for k, s in (('cf', cls.cf), ('nn', cls.nn), ('rk', cls.rk), ('vw', cls.vw))}
        cls.env = B.environment(d, 'Test', 'Kurs', [], [])
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, key, **ctx):
        c = self.browser.new_context(**ctx); pg = c.new_page()
        errors, requests = [], []
        pg.on('console', lambda m: errors.append(m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('request', lambda r: requests.append(r.url) if not r.url.startswith(('file:', 'data:')) else None)
        # v0.18: these checks drive the full parameter panel, which is the Explore view of the network lab (Guided: test_b18)
        pg.goto((self.paths[key].as_uri() + ('?mode=explore' if key == 'nn' else '')) if key in self.paths else self.env.as_uri())
        pg.wait_for_function('document.documentElement.dataset.emReady === "1"', timeout=10000)
        return c, pg, errors, requests

    def predict(self, pg, value):
        pg.check(f'input[name=pred][value="{value}"]')
        pg.check('input[name=conf][value="sure"]')
        pg.fill('#phase-predict textarea', 'weil die Zahlungen später kommen')
        pg.click('text=Vorhersage festlegen und Simulation öffnen')

    def test_js_models_match_python(self):
        c, pg, errors, _ = self.open('cf')
        rnd = random.Random(11)
        for _ in range(60):
            T = rnd.randint(1, 12); o = [rnd.randint(0, 300) for _ in range(T)]; cs = [rnd.randint(0, 200) for _ in range(T)]
            inv = [rnd.randint(0, 400) for _ in range(rnd.randint(0, T))]; dl = rnd.randint(0, 6); s0 = rnd.randint(0, 300)
            js = pg.evaluate('a => EM.models.cashflow({orders:a[0],delay:a[1],cost:a[2],invest:a[3],start_cash:a[4]})', [o, dl, cs, inv, s0])
            py = M.cashflow(o, dl, cs, inv, s0)
            for k in ('balance', 'financing_need', 'min_period', 'first_shortfall', 'final_balance'):
                self.assertEqual(js[k], py[k], k)
        for seed, ha, oa in itertools.product(range(6), ('sigmoid', 'tanh', 'relu', 'linear'), ('sigmoid', 'linear')):
            p = M.mlp_init(seed=seed); x = [rnd.uniform(-2, 2), rnd.uniform(-2, 2)]; t = rnd.random()
            js = pg.evaluate('a => EM.models.mlpBackward(a[0], a[1], a[2], a[3], a[4])', [p, x, t, ha, oa])
            py = M.mlp_backward(p, x, t, ha, oa)
            self.assertLess(max(abs(a - b) for a, b in zip(flat(js['grad']), flat(py['grad']))), 1e-12)
            self.assertLess(abs(js['loss'] - py['loss']), 1e-15)
            q_js, _ = pg.evaluate('a => EM.models.mlpStep(a[0], a[1], a[2], 0.3, a[3], a[4])', [p, x, t, ha, oa])
            self.assertLess(max(abs(a - b) for a, b in zip(flat(q_js), flat(M.mlp_step(p, x, t, 0.3, ha, oa)[0]))), 1e-12)
        for l, i in itertools.product(range(1, 6), repeat=2):
            self.assertEqual(pg.evaluate('a => EM.models.riskMatrix(a[0], a[1], a[2])', [l, i, M.LECTURE_CLASSES]), M.risk_matrix(l, i))
        self.assertEqual(errors, []); c.close()

    def test_cashflow_full_learning_sequence(self):
        c, pg, errors, requests = self.open('cf')
        self.assertTrue(pg.is_hidden('.em-lab'))                     # result hidden before the prediction
        go = 'text=Vorhersage festlegen und Simulation öffnen'
        pg.click(go)
        self.assertIn('zuerst eine Vorhersage', pg.inner_text('.em-pre .em-feedback'))
        pg.check('input[name=pred][value="sinkt"]'); pg.click(go)
        self.assertIn('wie sicher', pg.inner_text('.em-pre .em-feedback'))          # confidence required (calibration)
        pg.check('input[name=conf][value="sure"]'); pg.click(go)
        self.assertIn('begründen', pg.inner_text('.em-pre .em-feedback'))           # reasoning required before the result
        self.assertIn('Öffnet sich nach', pg.inner_text('#phase-explain'))           # explanation locked before the prediction
        self.predict(pg, 'sinkt')
        fb = pg.inner_text('.em-pre .em-feedback')
        self.assertIn('trifft nicht zu', fb); self.assertIn('2.316', fb); self.assertIn('sicher und lagen falsch', fb)
        self.assertNotIn('Mechanismus', pg.inner_text('body'))                      # expert explanation only after own explanation
        self.assertTrue(pg.is_visible('.em-lab'))
        ex = pg.locator('#phase-explain')
        ex.locator('textarea').fill('kurz'); ex.locator('text=Mit der Erklärung vergleichen').click()
        self.assertIn('mindestens 15', ex.inner_text())
        ex.locator('textarea').fill('Die Zahlungen kommen später an, die Kosten fallen weiter sofort an.')
        ex.locator('text=Mit der Erklärung vergleichen').click()
        txt = ex.inner_text()
        self.assertIn('Mechanismus', txt); self.assertIn('✓ Einzahlungen kommen später', txt); self.assertIn('○ der tiefste kumulierte Stand', txt)
        mis = pg.locator('[data-mission=nocredit]')
        self.assertNotIn('done', mis.get_attribute('class'))
        pg.fill('#p-start_cash', '2144'); pg.dispatch_event('#p-start_cash', 'input')
        pg.wait_for_timeout(50)
        self.assertIn('done', mis.get_attribute('class'))                            # mission checked live against the model state
        pg.fill('#p-start_cash', '0'); pg.dispatch_event('#p-start_cash', 'input')
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-need-b')), 2316)   # scenario B shows the changed delay 6
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-need')), 2144)
        self.assertEqual(pg.get_attribute('.em-lab', 'data-min-period'), '7')
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-final')), -2136)
        t1 = pg.locator('[data-task=need]')
        self.assertTrue(t1.locator('text=Lösung zeigen').is_disabled())           # no solution before an attempt
        t1.locator('input').fill('abc'); t1.locator('text=Prüfen').click()
        self.assertIn('Bitte eine Zahl', t1.locator('.em-feedback').inner_text())
        t1.locator('input').fill('2136'); t1.locator('text=Prüfen').click()
        self.assertIn('Endsaldos', t1.locator('.em-feedback').inner_text())       # diagnosed typical error
        for _ in range(3):
            t1.locator('text=Hinweis').click()
        self.assertEqual(t1.locator('.em-hints li').count(), 3)
        t1.locator('input').fill('2.144'); t1.locator('input').press('Enter')    # keyboard, German thousands point
        self.assertIn('Richtig', t1.locator('.em-feedback').inner_text())
        cq = pg.locator('[data-task=concept]')
        cq.locator('input[value=none]').check(); cq.locator('text=Prüfen').click()
        self.assertIn('Zwischenstände', cq.inner_text())                              # misconception-specific feedback
        cq.locator('input[value=min]').check(); cq.locator('text=Prüfen').click()
        self.assertIn('Richtig', cq.inner_text())
        t2 = pg.locator('[data-task=transfer]'); t2.locator('input').fill('1830'); t2.locator('text=Prüfen').click()
        self.assertIn('Richtig', t2.locator('.em-feedback').inner_text())
        self.assertIn('Übertragen', pg.inner_text('#phase-transfer h2'))
        sm = pg.locator('#phase-summary'); sm.locator('textarea').fill('Der tiefste kumulierte Stand bestimmt den Bedarf.')
        sm.locator('text=Mit den Kernaussagen vergleichen').click()
        self.assertIn('nicht der Endsaldo', sm.inner_text()); self.assertIn('Anki', sm.inner_text())
        done = pg.locator('.em-phases a.done').count()
        self.assertGreaterEqual(done, 6)                                              # predict, observe, explain, practice, transfer, summary
        self.assertNotIn('%', pg.inner_text('.em-phases'))                           # progress in steps, never a mastery percentage
        pg.fill('#p-horizon', '12'); pg.dispatch_event('#p-horizon', 'input')
        self.assertEqual(pg.locator('.em-scroll table').first.locator('thead th').count(), 13)
        pg.fill('#p-start_cash', '-5'); pg.dispatch_event('#p-start_cash', 'input')
        self.assertIn('ungültig', pg.inner_text('.em-param.em-invalid'))           # out-of-range input rejected
        pg.click('text=Zurücksetzen')
        self.assertEqual(float(pg.get_attribute('.em-lab', 'data-need')), 2144)
        prog = pg.evaluate('EM.store.read()')
        self.assertTrue(any(k.endswith('::need') and v['hints'] == 3 and v['correct'] for k, v in prog.items()))
        self.assertEqual(pg.evaluate('EM.store.status(EM.store.read()["ent/cashflow::need"])'), 'ASSISTED')
        self.assertEqual(pg.evaluate('EM.store.status(EM.store.read()["ent/cashflow::transfer"])'), 'INDEPENDENT_PASS')
        self.assertEqual(errors, []); self.assertEqual(requests, []); c.close()

    def test_neural_network_step_matches_python(self):
        c, pg, errors, _ = self.open('nn')
        self.predict(pg, 'sinkt')
        self.assertIn('trifft zu', pg.inner_text('.em-pre .em-feedback'))
        self.assertEqual(float(pg.input_value('#p-v1')), self.nn['sequence']['predict']['change']['to'])   # the change really applied
        q0 = json.loads(json.dumps(self.nn['model']['init'])); q0['W2'][0] = self.nn['sequence']['predict']['change']['to']
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-loss')), M.mlp_loss(M.mlp_forward(q0, [0.5, -1.0])['y'], 0.8), places=12)
        pg.click('text=Zurücksetzen')
        p = self.nn['model']['init']; bw = M.mlp_backward(p, [0.5, -1.0], 0.8)
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-loss')), bw['loss'], places=12)
        pg.click('text=Einen Lernschritt ausführen')
        q, _ = M.mlp_step(p, [0.5, -1.0], 0.8, 0.5)
        q = json.loads(json.dumps(q, default=float))
        rounded = {'W1': [[round(w, 3) for w in r] for r in q['W1']], 'b1': [round(b, 3) for b in q['b1']], 'W2': [round(v, 3) for v in q['W2']], 'b2': round(q['b2'], 3)}
        # the parameter inputs show 3 decimals; the model keeps full precision
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-loss')), M.mlp_loss(M.mlp_forward(q, [0.5, -1.0])['y'], 0.8), places=9)
        self.assertEqual(float(pg.input_value('#p-c')), rounded['b2'])
        t = pg.locator('[data-task=delta]')
        t.locator('input').fill(str(round(bw['forward']['y'] - 0.8, 4))); t.locator('text=Prüfen').click()
        self.assertIn('Kettenregel', t.locator('.em-feedback').inner_text())       # diagnosed: forgot sigma'
        t.locator('input').fill(str(round(bw['delta_o'], 4))); t.locator('text=Prüfen').click()
        self.assertIn('Richtig', t.locator('.em-feedback').inner_text())
        pg.fill('#p-w11', '4.9'); pg.dispatch_event('#p-w11', 'input'); pg.fill('#p-x1', '1'); pg.dispatch_event('#p-x1', 'input')
        self.assertIn('Sättigung', pg.inner_text('.em-warn'))
        pg.click('text=Automatisch (20 Schritte)')
        import time
        for _ in range(100):                                     # polled from Python: the lab's CSP forbids string eval
            if pg.evaluate('() => document.querySelector(".em-lab").dataset.steps') == '21' and pg.is_enabled('text=Automatisch (20 Schritte)'):
                break
            time.sleep(0.1)
        self.assertEqual(pg.evaluate('() => document.querySelector(".em-lab").dataset.steps'), '21')   # 1 manual + 20 automatic steps
        self.assertEqual(errors, []); c.close()

    def test_risk_matrix_and_mobile_dark_offline(self):
        c, pg, errors, requests = self.open('rk', viewport={'width': 390, 'height': 844}, color_scheme='dark')
        self.predict(pg, 'gleich')
        fb = pg.inner_text('.em-pre .em-feedback')
        self.assertIn('trifft nicht zu', fb); self.assertIn('High', fb); self.assertIn('Moderate', fb)
        self.assertEqual(pg.get_attribute('.em-lab', 'data-score'), '10')
        pg.fill('#p-l', '3'); pg.dispatch_event('#p-l', 'input'); pg.fill('#p-i', '4'); pg.dispatch_event('#p-i', 'input')
        self.assertEqual(pg.get_attribute('.em-lab', 'data-score'), '12')
        self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 390)   # no horizontal page scroll
        bg = pg.evaluate('getComputedStyle(document.body).backgroundColor')
        self.assertNotEqual(bg, 'rgb(251, 250, 247)')                                    # dark theme applied
        pg.keyboard.press('Tab'); pg.keyboard.press('Tab')
        self.assertTrue(pg.evaluate('document.activeElement && document.activeElement.tagName !== "BODY"'))
        self.assertEqual(errors, []); self.assertEqual(requests, []); c.close()

    def test_van_westendorp_js_equals_python(self):
        c, pg, errors, _ = self.open('vw')
        d = M.psm_synthetic(); rnd = random.Random(9)
        cases = [(d, m, seg, sh) for m in ('standard', 'alternative') for seg in ('all', 'A', 'B') for sh in (0, 10, 23)]
        for _ in range(30):
            rows = [dict(zip(M.PSM_KEYS, sorted(round(rnd.uniform(1, 120), 2) for _ in range(4)))) for _ in range(rnd.randint(3, 50))]
            rows += [{'tc': 50, 'cheap': 40, 'exp': 60, 'te': 70}]                    # one invalid row each time
            cases.append((rows, rnd.choice(['standard', 'alternative']), 'all', rnd.choice([0, 5])))
        for rows, m, seg, sh in cases:
            js = pg.evaluate('a => EM.models.vanWestendorp(a[0], a[1], a[2], a[3])', [rows, m, seg, sh])
            py = M.van_westendorp(rows, m, seg, sh)
            self.assertEqual((js['n_valid'], js['n_invalid']), (py['n_valid'], py['n_invalid']))
            self.assertEqual(js['knots'], py['knots'])
            for k in ('pmc', 'opp', 'ipp', 'pme'):
                if py['points'][k] is None:
                    self.assertIsNone(js['points'][k])
                else:
                    self.assertAlmostEqual(js['points'][k], py['points'][k], places=9, msg=k)
        malformed = [None, {}, {'tc': True,'cheap':2,'exp':3,'te':4}, {'tc':1,'cheap':2,'exp':3,'te':None}]
        for shift in (0,5):
            rows = d[:5]+malformed
            py = M.van_westendorp(rows,te_shift=shift)
            js = pg.evaluate('a=>EM.models.vanWestendorp(a[0],"standard",null,a[1])',[rows,shift])
            self.assertEqual(js['n_invalid'],py['n_invalid'])
        for key, values in py['curves'].items():
            for a,b in zip(values,js['curves'][key]): self.assertAlmostEqual(a,b,places=12)
        self.assertEqual(errors, []); c.close()

    def test_van_westendorp_no_javascript_fallback(self):
        c=self.browser.new_context(java_script_enabled=False,offline=True);pg=c.new_page();errors=[];requests=[];pg.on('pageerror',lambda e:errors.append(str(e)));pg.on('request',lambda r:requests.append(r.url) if not r.url.startswith(('file:','data:')) else None);pg.goto(self.paths['vw'].as_uri())
        self.assertTrue(pg.locator('.em-static svg').is_visible())
        self.assertIn('SYNTHETISCHE',pg.locator('.em-static').inner_text())
        self.assertEqual(requests,[]);self.assertEqual(errors,[]);c.close()

    def test_van_westendorp_learning_sequence(self):
        c, pg, errors, requests = self.open('vw')
        self.assertTrue(pg.is_hidden('.em-lab'))                                          # no peeking before the prediction
        self.assertIn('SYNTHETISCH', pg.inner_text('body'))
        self.predict(pg, 'opp_pme')
        self.assertIn('trifft zu', pg.inner_text('.em-pre .em-feedback'))
        py = M.van_westendorp(M.psm_synthetic(), te_shift=10)['points']
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-opp')), py['opp'], places=9)
        pg.select_option('#p-segment', 'B'); pg.fill('#p-te_shift', '0'); pg.dispatch_event('#p-te_shift', 'input')
        wb = M.van_westendorp(M.psm_synthetic(), segment='B')['range_width']
        self.assertAlmostEqual(float(pg.get_attribute('.em-lab', 'data-width')), wb, places=9)
        box = pg.locator('[data-task=range]')
        box.locator('input').fill(str(round(M.van_westendorp(M.psm_synthetic(), 'alternative', segment='B')['range_width'], 2)).replace('.', ','))
        box.locator('text=Prüfen').click()
        self.assertIn('Praxisvariante', box.inner_text())                                 # diagnosed typical error
        box.locator('input').fill(str(round(wb, 2)).replace('.', ',')); box.locator('text=Prüfen').click()
        self.assertIn('Richtig', box.inner_text())
        first = pg.locator('[data-task=share]')
        self.assertTrue(first.locator('text=Lösung zeigen').is_disabled())
        first.locator('input').fill('20'); first.locator('text=Prüfen').click()
        self.assertIn('≤', first.inner_text())                                            # boundary error diagnosed
        pg.click('text=Eigene Antworten einfügen')
        pg.fill('.em-edit textarea', 'zu_billig;guenstig;teuer;zu_teuer\n10;20;30;40\n20;30;40;50\n30;20;40;50')
        pg.click('text=Übernehmen')
        self.assertEqual(pg.get_attribute('.em-lab', 'data-n-valid'), '2')
        self.assertIn('ausgeschlossen 1', pg.inner_text('.em-lab'))
        self.assertIn('EIGENE Daten', pg.inner_text('.em-lab'))
        pg.click('text=Zurücksetzen')
        self.assertEqual(pg.get_attribute('.em-lab', 'data-n-valid'), '240')
        self.assertEqual(errors, []); self.assertEqual(requests, []); c.close()

    def test_van_westendorp_mobile_dark(self):
        c, pg, errors, requests = self.open('vw', viewport={'width': 390, 'height': 844}, color_scheme='dark')
        pg.click('text=Ohne Vorhersage erkunden')
        self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), 390)
        self.assertEqual(pg.locator('.em-lab svg polyline').count(), 6)
        self.assertEqual(errors, []); self.assertEqual(requests, []); c.close()

    def test_every_mission_triggers_in_the_browser_at_its_python_witness(self):
        from exam_mastery.labs import pedagogy as P
        for key, spec in (('cf', self.cf), ('rk', self.rk), ('vw', self.vw), ('nn', self.nn)):
            for m in spec['sequence']['explore']:
                c, pg, errors, _ = self.open(key)
                pg.click('text=Ohne Vorhersage erkunden')
                w = dict(m['witness']); steps = w.pop('steps', 0)
                for pid, v in w.items():
                    sel = '#p-' + pid
                    if pg.evaluate('s => document.querySelector(s).tagName', sel) == 'SELECT':
                        pg.select_option(sel, str(v))
                    else:
                        pg.fill(sel, str(v)); pg.dispatch_event(sel, 'input')
                for _ in range(steps):
                    pg.click('text=Einen Lernschritt ausführen')
                pg.wait_for_timeout(30)
                cls = pg.get_attribute(f'[data-mission="{m["id"]}"]', 'class')
                self.assertIn('done', cls, (key, m['id']))
                self.assertEqual(errors, []); c.close()

    def test_environment_shows_observed_status_only(self):
        c, pg, errors, _ = self.open('env')
        self.assertIn('Noch keine Versuche', pg.inner_text('#em-progress'))
        pg.evaluate('EM.store.record("lab", "t", ["kc"], "correct")'); pg.reload(); pg.wait_for_function('document.documentElement.dataset.emReady === "1"')
        txt = pg.inner_text('#em-progress')
        self.assertIn('ohne Hilfe gelöst', txt); self.assertNotIn('INDEPENDENT_PASS', txt); self.assertNotIn('%', txt)   # plain language, never a raw status code
        self.assertEqual(errors, []); c.close()


if __name__ == '__main__':
    unittest.main()
