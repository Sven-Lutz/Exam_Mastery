"""Practice track ai/attention-track: every expected answer and bug value is recomputed here on an independent route
(numpy matrices, sympy derivatives, finite differences), every bug yields its own category, Python and browser agree.

These checks certify arithmetic and diagnosis wiring, not didactic quality or learning outcomes.
"""
import math
import random
import tempfile
import unittest
from pathlib import Path

import numpy as np

from exam_mastery.learning import diagnose as D, expr as X, policy as P, render, tracks as TR

TRACK = next(t for t in TR.all_tracks() if t['id'] == 'ai/attention-track')
T = {t['id']: t for t in TRACK['tasks']}
NOW = '2026-11-27T10:00:00+00:00'


def np_attention(S, scale, axis=1, mask=None):
    """Independent route: numpy, no max-shift, mask as -inf on the whole matrix."""
    Z = np.asarray(S, dtype=float) / scale
    if mask is not None:
        Z = np.where(np.asarray(mask), Z, -np.inf)
    E = np.exp(Z)
    return E / E.sum(axis=axis, keepdims=True)


def _bug_groups(task):
    """(expected, tolerance, [(wrong value, category)]) per numeric answer field."""
    if task['type'] == 'numeric':
        return [(task['expected'], task['tolerance'], [(e['value'], e['category']) for e in task.get('errors', [])])]
    if task['type'] == 'steps':
        return [(s['expected'], s['tolerance'], [(e['value'], e['category']) for e in s.get('errors', [])]) for s in task['steps']]
    return []


class AttentionTrackValues(unittest.TestCase):
    def test_validates_and_flow(self):
        self.assertTrue(TR.validate(TRACK))
        self.assertEqual(TRACK['flow'], ['att-pre', 'att-core', 'att-similar', 'att-transfer', 'att-harder'])
        roles = {t['role'] for t in TRACK['tasks']}
        self.assertTrue({'diagnostic', 'prereq_retry', 'core', 'similar', 'contrast', 'transfer', 'harder', 'retest', 'open'} <= roles)
        gradient_kc = next(k for k in TRACK['kcs'] if k['id'] == 'attention/softmax-gradient')
        self.assertEqual(gradient_kc['requires'][0]['track'], 'ml/backprop-track')
        self.assertIn('ml/backpropagation', {k['id'] for k in next(t for t in TR.all_tracks() if t['id'] == 'ml/backprop-track')['kcs']})

    def test_score_matrix_tasks_against_numpy(self):
        cases = {'att-core': ([[6, 2, 0], [0, 2, 6]], 4, 0, 0), 'att-similar': ([[8, 4, 0, -4], [0, 8, 4, 0]], 16, 0, 1),
                 'att-retest': ([[3, -3, 0], [0, 3, 3]], 9, 0, 0)}
        for tid, (S, dk, i, j) in cases.items():
            t = T[tid]
            self.assertAlmostEqual(t['expected'], np_attention(S, math.sqrt(dk))[i, j], places=6, msg=tid)
            bug = {e['category']: e['value'] for e in t['errors']}
            self.assertAlmostEqual(bug['missing_scaling'], np_attention(S, 1.0)[i, j], places=6)
            self.assertAlmostEqual(bug['scaled_by_dk'], np_attention(S, dk)[i, j], places=6)
            self.assertAlmostEqual(bug['wrong_axis'], np_attention(S, math.sqrt(dk), axis=0)[i, j], places=6)
            self.assertIn(str(S[0][0]), t['prompt'])

    def test_prerequisite_contrast_and_mask_against_numpy(self):
        self.assertAlmostEqual(T['att-pre']['expected'], np_attention([[1, 0, 0]], 1)[0, 0], places=6)
        self.assertAlmostEqual(T['att-pre2']['expected'], np_attention([[0, 2, 0]], 1)[0, 1], places=6)
        steps = {s['id']: s for s in T['att-contrast']['steps']}
        z = np.array([[0.5, 0, -1]])
        self.assertAlmostEqual(steps['shift']['expected'], np_attention(z + 3, 1)[0, 0], places=6)
        self.assertAlmostEqual(steps['shift']['expected'], np_attention(z, 1)[0, 0], places=6)   # shift invariance
        self.assertAlmostEqual(steps['scale']['expected'], np_attention(2 * z, 1)[0, 0], places=6)
        z, m, v = [[1.0, 0.5, -0.5, 2.0]], [[True, True, True, False]], np.array([2, -1, 4, 10])
        A = np_attention(z, 1, mask=m)
        self.assertEqual(A[0, 3], 0.0); self.assertAlmostEqual(A.sum(), 1.0)
        t = T['att-transfer']; bug = {e['category']: e['value'] for e in t['errors']}
        self.assertAlmostEqual(t['expected'], float(A[0] @ v), places=6)
        full = np_attention(z, 1)[0]
        self.assertAlmostEqual(bug['mask_ignored'], float(full @ v), places=6)
        self.assertAlmostEqual(bug['mask_after_softmax'], float(full[:3] @ v[:3]), places=6)
        # a large finite negative instead of -inf gives the same row here (one allowed key dominates the max) ...
        self.assertAlmostEqual(float(np_attention([[1.0, 0.5, -0.5, -1e9]], 1)[0] @ v), float(A[0] @ v), places=12)
        # ... but on an all-masked row it silently returns the uniform row, while TR.softmax refuses
        self.assertTrue(np.allclose(TR.softmax([-1e9, -1e9]), [0.5, 0.5]))
        with self.assertRaises(ValueError):
            TR.softmax([1.0, 2.0], [False, False])

    def test_wrong_values_are_separated(self):
        for t in TRACK['tasks']:
            for exp, tol, vals in _bug_groups(t):
                for k, (v, cat) in enumerate(vals):
                    self.assertGreater(abs(v - exp), 2 * tol, (t['id'], cat))
                    for w, c2 in vals[k + 1:]:
                        self.assertGreater(abs(v - w), 2 * tol, (t['id'], cat, c2))

    def test_every_bug_yields_its_category_including_steps(self):
        for t in TRACK['tasks']:
            if t['type'] == 'steps':
                for s in t['steps']:
                    for e in s.get('errors', []):
                        ans = {x['id']: repr(x['expected']) for x in t['steps']}; ans[s['id']] = repr(e['value'])
                        self.assertEqual(D.diagnose(t, ans)['error_category'], e['category'], (t['id'], s['id']))
            elif t['type'] == 'numeric':
                for e in t['errors']:
                    self.assertEqual(D.diagnose(t, repr(e['value']))['error_category'], e['category'])
                    self.assertEqual(D.diagnose(t, f(e['value']))['error_category'], e['category'])   # German comma input
            elif t['type'] == 'expression':
                for b in t['bugs']:
                    self.assertEqual(D.diagnose(t, b['expr'])['error_category'], b['category'])
        self.assertEqual(D.diagnose(T['att-core'], '0,8438')['result'], 'correct')

    def test_gradient_through_softmax_sympy_and_finite_differences(self):
        import sympy as sp
        z = sp.symbols('z1:4', real=True); g = sp.symbols('g1:4', real=True)
        den = sum(sp.exp(x) for x in z); a = [sp.exp(x) / den for x in z]
        L = sum(gi * ai for gi, ai in zip(g, a))           # L linear in alpha: dL/dalpha_j = g_j exactly
        env = {'a1': a[0], 'a2': a[1], 'a3': a[2], 'g1': g[0], 'g2': g[1], 'g3': g[2]}
        to = lambda e: X.to_sympy(X.parse(e, set(TR.ATT_VARS))).subs({sp.Symbol(k): v for k, v in env.items()}, simultaneous=True)
        self.assertEqual(sp.simplify(sp.diff(L, z[0]) - to(T['att-harder']['expected_expr'])), 0)
        self.assertEqual(sp.simplify(sp.diff(a[1], z[2]) - to(T['att-jac']['expected_expr'])), 0)
        for b in T['att-harder']['bugs']:
            self.assertNotEqual(sp.simplify(sp.diff(L, z[0]) - to(b['expr'])), 0, b)
        rng = np.random.default_rng(7)
        for _ in range(5):
            zz, gg = rng.normal(size=4), rng.normal(size=4)
            f_ = lambda v: float(np.asarray(TR.softmax(list(v))) @ gg)
            fd = [(f_(zz + h) - f_(zz - h)) / 2e-6 for h in np.eye(4) * 1e-6]
            self.assertTrue(np.allclose(fd, TR.softmax_grad(TR.softmax(list(zz)), list(gg)), atol=1e-7))
            self.assertAlmostEqual(sum(TR.softmax_grad(TR.softmax(list(zz)), list(gg))), 0.0, places=12)

    def test_expression_domains_declared(self):
        for tid in ('att-harder', 'att-jac'):
            t = T[tid]
            self.assertEqual(t['defs'], {'a3': '1-a1-a2'})
            pts = X.sample_points(set(t['variables']), t['defs'], domains=t['domains'])
            self.assertTrue(all(0 < p['a1'] < 1 and 0 < p['a2'] < 1 and 0 < p['a3'] < 1 for p in pts))
            self.assertTrue(any(p['g1'] < 0 for p in pts) and any(p['g1'] > 0 for p in pts))
        # an equivalent form that uses a1 + a2 + a3 = 1 is accepted
        self.assertEqual(D.diagnose(T['att-harder'], 'a1*g1*(a2+a3) - a1*(a2*g2+a3*g3)')['result'], 'correct')
        self.assertEqual(D.diagnose(T['att-jac'], '-a2*(1-a1-a2)')['result'], 'correct')

    def test_policy_routes(self):
        ev = [{'type': 'attempt', 'task': 'att-pre', 'diagnosis': D.diagnose(T['att-pre'], '1'), 't': NOW}]
        d = P.decide(TRACK, ev); self.assertEqual((d['rule'], d['next_task']), ('RA', 'att-pre2'))
        ev = [{'type': 'attempt', 'task': 'att-core', 'diagnosis': D.diagnose(T['att-core'], f(T['att-core']['errors'][0]['value'])), 't': NOW}] * 2
        d = P.decide(TRACK, ev); self.assertEqual((d['rule'], d['next_task']), ('RC2', 'att-contrast'))
        self.assertEqual(d['support']['ref'], 'shift_vs_scale')

    def test_anki_tags_cover_misconceptions(self):
        for cid in ('missing_scaling', 'scaled_by_dk', 'wrong_axis', 'mask_after_softmax', 'normaliser_ignored'):
            self.assertIn(cid, TRACK['review_tags'])


def f(v):
    return repr(v).replace('.', ',')


class AttentionTrackBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); render.write(TRACK, Path(cls.td.name))
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def test_js_python_parity_and_figure(self):
        pg = self.browser.new_page(viewport={'width': 390, 'height': 900}); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto((Path(self.td.name) / 'ai__attention-track.html').as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        r = random.Random(11)
        for t in TRACK['tasks']:
            answers = [TR._answer_for(t)]
            if t['type'] == 'numeric':
                answers += [repr(e['value']) for e in t['errors']] + [f(e['value']) for e in t['errors']] + [str(r.uniform(-3, 3)), '-' + repr(t['expected']), 'abc']
            elif t['type'] == 'expression':
                answers += [b['expr'] for b in t['bugs']] + ['-' + t['expected_expr'], '2*(' + t['expected_expr'] + ')', 'a1*a2*g3', 'x1', 'a1 +']
            elif t['type'] == 'steps':
                answers += [{s['id']: repr(e['value']) for s in t['steps'] for e in s.get('errors', [])}, {t['steps'][0]['id']: '0,1'}]
            for a in answers:
                js = pg.evaluate('([t,a]) => EMT.diagnose(t,a)', [t, a]); py = D.diagnose(t, a)
                self.assertEqual((js['result'], js['error_category'], js['evidence']), (py['result'], py['error_category'], py['evidence']), (t['id'], a))
        ev = []
        for tid, a in [('att-pre', '1'), ('att-pre2', '0,787'), ('att-core', '0,9796'), ('att-core', '0,9796'), ('att-contrast', {'shift': '0,5465', 'scale': '0,7054'})]:
            ev.append({'type': 'attempt', 'task': tid, 'diagnosis': D.diagnose(T[tid], a), 't': NOW})
            js = pg.evaluate('([tr,ev]) => EMT.decide(tr,ev)', [TRACK, ev]); py = P.decide(TRACK, ev)
            self.assertEqual((js['rule'], js['action'], js['next_task']), (py['rule'], py['action'], py['next_task']), (tid, a))
        svg = pg.locator('svg.wb-att')
        self.assertGreaterEqual(svg.count(), 1)
        self.assertNotIn('0,5761', pg.locator('main').inner_text())        # the figure never shows the answer
        self.assertFalse(pg.evaluate('document.documentElement.scrollWidth > innerWidth'))
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
