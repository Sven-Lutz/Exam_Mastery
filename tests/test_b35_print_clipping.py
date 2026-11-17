"""B35 regression: V4 P1 defect (textbook PDF p. 49, proof of Satz 3.6, step 3) - a display formula wider than the
text block was clipped by its overflow-x:auto wrapper. Negative fixture = the real V4 formula; the old lint passed it."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import typeset
from exam_mastery.chapter_publish import _layout_lint

V4_STEP3 = (r'\|T^\pi V-T^\pi V^\pi\|_\infty\le\gamma\|V-V^\pi\|_\infty\le\gamma\big(\|V-V^*\|_\infty+\|V^*-V^\pi\|_\infty\big)'
            r'\le\gamma\varepsilon+\gamma\|V^*-V^\pi\|_\infty')
ABSURD = r'\frac{' + '+'.join(f'a_{{{i}}}x^{{{i}}}' for i in range(60)) + '}{b}'   # one fraction: no legal break point
LONG_SUM = 'S=' + '+'.join(f'a_{{{i}}}x^{{{i}}}' for i in range(40))           # breakable only at top-level +


def _render(tex):
    import pymupdf
    from playwright.sync_api import sync_playwright
    d = Path(tempfile.mkdtemp()); typeset._assets(d)
    body = f'<div class="drv"><ol class="chain"><li><div class="eq">\\[{tex}\\]</div><div class="why">x</div></li></ol></div>'
    (d / 'x.html').write_text(typeset._page('t', body), encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        typeset._pdf(pg, d / 'x.html', d / '.x.main.pdf', None); b.close()
    lint = json.loads((d / '..x.main.layout_lint.json').read_text())
    doc = pymupdf.open(d / '.x.main.pdf'); pw = doc[0].rect.width
    right = max(r['rect'].x1 for r in doc[0].get_drawings())
    return lint, right, pw, d


class PrintClipping(unittest.TestCase):
    def test_v4_p49_formula_fits_text_block(self):
        lint, right, pw, d = _render(V4_STEP3)
        self.assertTrue(lint['display_math_broken'], 'the over-wide V4 formula must be detected and broken')
        self.assertTrue(lint['display_math_broken'][0]['fits'])
        self.assertEqual(lint['display_math_scaled'], [], 'line breaking first; scaling is only the fallback')
        self.assertEqual(lint['clipped'], [])
        self.assertLessEqual(right, pw - 16 / 25.4 * 72 + 1, 'formula ink must stay inside the right margin')
        self.assertEqual(_layout_lint(d, 'x')['status'] in ('PASS', 'WARN'), True)

    def test_long_sum_breaks_at_plus(self):
        lint, right, pw, d = _render(LONG_SUM)
        self.assertTrue(lint['display_math_broken'] and lint['display_math_broken'][0]['lines'] >= 2)
        self.assertEqual([o for o in lint['overflow'] if o.get('cls') == 'display-math-too-wide'], [])

    def test_unreadably_wide_formula_fails_gate(self):
        lint, _, _, d = _render(ABSURD)
        self.assertTrue(any(o.get('cls') == 'display-math-too-wide' for o in lint['overflow']))
        self.assertEqual(_layout_lint(d, 'x')['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
