"""Layout-Regression der v7-Referenzsequenz (Self-Attention) – ersetzt KEINE menschliche Gestaltungsprüfung.

Prüft am gerenderten HTML: keine horizontalen Überläufe, keine Mini-Schrift, keine überlappenden Beschriftungen in den
Originalgrafiken, Formeln in vernünftiger Höhe, Grafikzahlen = Rechenorakel, Lab-Simplex synchron zum Lehrbuch.
"""
import math
import re
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


class Figures(unittest.TestCase):
    def test_figure_numbers_come_from_oracle(self):
        from exam_mastery import figures7 as F
        import sys
        sys.path.insert(0, str(UNIT / 'src'))
        import v5_attention as V5
        R = RU.attn_full(V5.BANK)
        figs = F.render_all(V5.BANK)
        for x in R['w']:
            self.assertIn(F.de(x, 4), figs['pipeline'])
        self.assertIn(F.de(R['o'][0], 3), figs['hull'])
        self.assertEqual(len(figs), 6)
        data = F.variance_experiment(dims=(1, 16, 64), m=2000)
        for d, v in data:
            self.assertLess(abs(v / d - 1), 0.15, (d, v))                # Satz 3 empirisch

    def test_card_figures_drop_titles_and_enlarge(self):
        from exam_mastery import figures7 as F
        import sys
        sys.path.insert(0, str(UNIT / 'src'))
        import v5_attention as V5
        s = F.static_svg(F.render_all(V5.BANK)['simplex'], crop='20 60 670 360', fonts=('22px', '22px'))
        self.assertNotIn('Der Simplex: alle', s)
        self.assertIn('font-size:22px', s)
        self.assertNotIn('var(--', s)


@unittest.skipUnless(HAVE, 'playwright and MathJax runtime required')
class Rendered(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.out = Path(cls.tmp.name)
        RU.build(UNIT, cls.out, pdf=False, anki=False)
        cls.pw = sync_playwright().start(); cls.b = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.b.close(); cls.pw.stop(); cls.tmp.cleanup()

    def open(self, w, h=900, scheme='light'):
        ctx = self.b.new_context(viewport={'width': w, 'height': h}, color_scheme=scheme); self.addCleanup(ctx.close)
        pg = ctx.new_page(); pg.goto((self.out / 'index.html').as_uri() + '#learn/att-problem')
        pg.wait_for_function('document.body.dataset.ready === "1"', timeout=60000); pg.wait_for_timeout(1500)
        return pg

    def test_no_overflow_no_tiny_text_on_phone_and_desktop(self):
        for w in (320, 360, 390, 1280, 1440):      # 320/360: Puffer gegen breitere Linux-Schriften in CI
            pg = self.open(w)
            sec = pg.locator('section, main').first
            res = pg.evaluate("""() => {
              const root = document.querySelector('.book7');
              const over = [...root.querySelectorAll('p, li, .box, figure, table')].filter(e => e.getBoundingClientRect().right > document.documentElement.clientWidth + 1).length;
              const tiny = [...root.querySelectorAll('p, li, td, th, figcaption, span.why, .lbl')].filter(e => parseFloat(getComputedStyle(e).fontSize) < 12).length;
              const hscroll = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
              const tallMath = [...root.querySelectorAll('mjx-container[display=true]')].filter(e => e.getBoundingClientRect().height > 170).length;
              return {over, tiny, hscroll, tallMath};
            }""")
            self.assertEqual(res, {'over': 0, 'tiny': 0, 'hscroll': False, 'tallMath': 0}, w)

    def test_no_page_wider_than_viewport_on_small_phones(self):
        for w in (320, 360):
            ctx = self.b.new_context(viewport={'width': w, 'height': 800}); self.addCleanup(ctx.close); pg = ctx.new_page()
            for h in ('', '#learn/orientierung', '#learn/rnn', '#learn/att-problem', '#learn/prf', '#exam', '#review', '#tutor'):
                pg.goto((self.out / 'index.html').as_uri() + h); pg.wait_for_function('document.body.dataset.ready === "1"', timeout=60000); pg.wait_for_timeout(300)
                self.assertLessEqual(pg.evaluate('document.documentElement.scrollWidth'), w, (w, h))

    def test_figure_labels_do_not_collide(self):
        pg = self.open(1280)
        coll = pg.evaluate("""() => {
          const out = [];
          document.querySelectorAll('figure.fig7 svg').forEach((svg, fi) => {
            const boxes = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim()).map(t => ({t: t.textContent.trim(), r: t.getBoundingClientRect()}));
            for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
              const a = boxes[i].r, b = boxes[j].r;
              const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
              if (ox > 2 && oy > 2) out.push([fi + 1, boxes[i].t, boxes[j].t]);
            }
          });
          return out;
        }""")
        self.assertEqual(coll, [], coll)

    def test_semantic_colours_resolve_in_light_and_dark(self):
        for scheme in ('light', 'dark'):
            pg = self.open(1280, scheme=scheme)
            col = pg.evaluate("getComputedStyle(document.querySelector('.mw')).color")
            self.assertNotIn(col, ('rgb(0, 0, 0)', ''), scheme)

    def test_lab_simplex_point_matches_softmax(self):
        ctx = self.b.new_context(viewport={'width': 1300, 'height': 900}); self.addCleanup(ctx.close)
        pg = ctx.new_page(); pg.goto((self.out / 'labor.html').as_uri() + '#lab=attention'); pg.wait_for_function('document.body.dataset.ready === "1"')
        label = pg.locator('svg[aria-label^="Gewichte als Punkt im Simplex"]').get_attribute('aria-label')
        nums = [float(x.replace(',', '.')) for x in re.findall(r'\d+,\d+', label)]
        self.assertEqual(len(nums), 3)
        self.assertAlmostEqual(sum(nums), 1, places=2)
        s = [x / math.sqrt(2) for x in (1.2, -1.26, 0.27)]
        e = [math.exp(x) for x in s]
        self.assertEqual([round(x, 3) for x in nums], [round(x / sum(e), 3) for x in e])


if __name__ == '__main__':
    unittest.main()


class V71Mathematics(unittest.TestCase):
    """Unabhängige Prüfung der v7.1-Aussagen (Python, nicht der Lehrtext)."""

    def test_w1_w4_do_not_characterise_softmax(self):
        def g_weights(s):
            m = sum(s) / len(s); z = [1 + math.tanh(x - m) for x in s]; return [x / sum(z) for x in z]
        s = [1.0, 0.0, -1.0]
        g = g_weights(s); sm = [math.exp(x) / sum(math.exp(y) for y in s) for x in s]
        self.assertAlmostEqual(g[1], 1 / 3, places=12)
        self.assertNotAlmostEqual(sm[1], 1 / 3, places=3)
        self.assertTrue(all(x > 0 for x in g) and abs(sum(g) - 1) < 1e-12 and g[0] > g[1] > g[2])
        self.assertEqual([round(x, 12) for x in g_weights([x + 7 for x in s])], [round(x, 12) for x in g])

    def test_variational_principle(self):
        import random
        rng = random.Random(3)
        for _ in range(50):
            n = rng.choice([2, 3, 5]); s = [rng.uniform(-3, 3) for _ in range(n)]; T = rng.choice([0.3, 1, 2.5])
            Z = sum(math.exp(x / T) for x in s); ws = [math.exp(x / T) / Z for x in s]
            F = lambda w: sum(a * b for a, b in zip(w, s)) - T * sum(x * math.log(x) for x in w if x > 0)
            self.assertAlmostEqual(F(ws), T * math.log(Z), places=10)            # Optimalwert = weiches Maximum
            for _ in range(200):
                r = [rng.random() ** 3 for _ in range(n)]; r = [x / sum(r) for x in r]
                self.assertLessEqual(F(r), F(ws) + 1e-12)
            m = max(s); self.assertTrue(m - 1e-12 <= T * math.log(Z) <= m + T * math.log(n) + 1e-12)

    def test_exam_a19_tied_keys_reachable_set_is_diagonal(self):
        V = [(2, 0), (0, 2), (0, 0)]
        for q1, q2 in ((0.3, -1.2), (2.0, 0.5), (-1.0, -1.0)):
            s = [q1 / math.sqrt(2), q1 / math.sqrt(2), q2 / math.sqrt(2)]
            e = [math.exp(x) for x in s]; w = [x / sum(e) for x in e]
            o = [sum(wj * v[i] for wj, v in zip(w, V)) for i in range(2)]
            self.assertAlmostEqual(o[0], o[1], places=12)
        d = -math.sqrt(2) * math.log(2)                       # Teil (c)
        s = [d / math.sqrt(2), d / math.sqrt(2), 0.0]; e = [math.exp(x) for x in s]; w = [x / sum(e) for x in e]
        self.assertAlmostEqual(2 * w[0], 0.5, places=12)

    def test_exam_b19_causal_mask_breaks_permutation_equivariance(self):
        sA, sB = 1 / math.sqrt(2), 0.0
        wA = math.exp(sA) / (math.exp(sA) + math.exp(sB))
        oB = (2 * wA, 2 * (1 - wA))
        self.assertEqual(round(wA, 4), 0.6698)
        self.assertEqual((round(oB[0], 4), round(oB[1], 4)), (1.3395, 0.6605))
        self.assertNotEqual(oB, (0, 2))                       # vertauscht: B sieht nur sich -> (0, 2)

    def test_noninjectivity_example(self):
        V = [(2, 0), (0, 2), (0, 0), (1, 1)]
        mix = lambda w: tuple(round(sum(a * v[i] for a, v in zip(w, V)), 12) for i in range(2))
        self.assertEqual(mix([0.5, 0.5, 0, 0]), mix([0, 0, 0, 1]))
        self.assertEqual(mix([0.25] * 4), mix([0.025, 0.025, 0.25, 0.7]))
        self.assertEqual(mix([0.25] * 4), (0.75, 0.75))
