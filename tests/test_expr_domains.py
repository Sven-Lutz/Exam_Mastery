"""Expression equivalence must not accept answers that are only right on a narrow sample domain (CD-10).

R6 red team RT-11: every variable was sampled in (0.15, 0.95) with a fixed public seed, so (x^2)^(1/2) was judged
identical to x. Variables without a declared domain are now drawn with both signs; tasks declare narrower domains
only where the mathematics fixes them. abs()/|x| and sqrt() exist so that the correct |x| can be entered.
Python and the browser mirror (em_tutor.js) must agree point by point.
"""
import math
import tempfile
import unittest
from pathlib import Path

from exam_mastery.learning import diagnose as D, expr as X, render, tracks as TR

PAIRS = [  # (answer, reference, domains, expected verdict)
    ('(x^2)^(1/2)', 'x', None, False),
    ('sqrt(x^2)', 'x', None, False),
    ('sqrt(x^2)', 'abs(x)', None, True),
    ('(x^2)^(1/2)', '|x|', None, True),
    ('√(x^2)', '|x|', None, True),
    ('(x^2)^(1/2)', 'x', {'x': [0.05, 0.95]}, True),        # domain-sensitive: right when x is known to be positive
    ('x^2/x', 'x', None, True),
    ('abs(x*y)', 'abs(x)*abs(y)', None, True),
    ('abs(x+y)', 'abs(x)+abs(y)', None, False),              # triangle inequality is not an identity
    ('x^3', 'abs(x)^3', None, False),                       # odd power loses the sign
]


def ast(s, vs=('x', 'y')):
    return X.parse(s, set(vs))


class ExprDomains(unittest.TestCase):
    def test_adversarial_pairs(self):
        for a, b, dom, want in PAIRS:
            pts = X.sample_points(['x', 'y'], domains=dom)
            self.assertEqual(X.same(ast(a), ast(b), pts), want, (a, b, dom))

    def test_undeclared_variables_take_both_signs(self):
        pts = X.sample_points(['x', 'y'])
        for v in ('x', 'y'):
            self.assertTrue(any(p[v] < 0 for p in pts) and any(p[v] > 0 for p in pts), v)

    def test_negative_base_with_fractional_exponent_is_nan_not_complex(self):
        r = X.evaluate(ast('x^(1/2)'), {'x': -2.0, 'y': 1.0})
        self.assertIsInstance(r, float); self.assertTrue(math.isnan(r))

    def test_reference_tracks_still_validate(self):
        for tr in TR.all_tracks():
            self.assertTrue(TR.validate(tr), tr['id'])        # raises on any problem

    def test_sigmoid_track_wrong_sign_is_not_accepted(self):
        ml = next(t for t in TR.all_tracks() if t['id'] == 'ml/backprop-track')
        core = next(t for t in ml['tasks'] if t['id'] == 'ml-core')
        self.assertEqual(D.diagnose(core, core['expected_expr'])['result'], 'correct')
        self.assertNotEqual(D.diagnose(core, 'abs(delta_o)*v1*fp1*x1')['result'], 'correct')


class BrowserParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.td = tempfile.TemporaryDirectory(); out = Path(cls.td.name)
        cls.ml = next(t for t in TR.all_tracks() if t['id'] == 'ml/backprop-track')
        render.write(cls.ml, out / 'lernstrecken', lab_href='../labs/x.html')
        cls.page_path = next((out / 'lernstrecken').glob('*.html'))
        cls.pw = sync_playwright().start(); cls.browser = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop(); cls.td.cleanup()

    def test_sample_points_and_verdicts_agree(self):
        pg = self.browser.new_page(); errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.goto(self.page_path.as_uri()); pg.wait_for_selector('html[data-em-ready="1"]', state='attached')
        for dom in (None, {'x': [0.05, 0.95]}):
            js = pg.evaluate('([d]) => EMT.expr.samplePoints(["x", "y"], null, 12, 20261110, d)', [dom])
            py = X.sample_points(['x', 'y'], domains=dom)
            for a, b in zip(js, py):
                for v in ('x', 'y'):
                    self.assertAlmostEqual(a[v], b[v], places=12)
        for a, b, dom, want in PAIRS:
            js = pg.evaluate('([a, b, d]) => { const E = EMT.expr; const p = E.samplePoints(["x", "y"], null, 12, 20261110, d);'
                             ' return E.same(E.parse(a, ["x", "y"]), E.parse(b, ["x", "y"]), p); }', [a, b, dom])
            self.assertEqual(js, want, (a, b, dom))
        core = next(t for t in self.ml['tasks'] if t['id'] == 'ml-core')
        for ans in (core['expected_expr'], 'abs(delta_o)*v1*fp1*x1', 'delta_o*v1*fp1'):
            self.assertEqual(pg.evaluate('([t, a]) => EMT.diagnose(t, a).result', [core, ans]), D.diagnose(core, ans)['result'], ans)
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
