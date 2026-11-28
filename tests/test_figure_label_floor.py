"""Figure labels stay legible in print: the body measure scales a wide SVG down, and its labels with it."""
import re
import unittest

from exam_mastery import typeset
from exam_mastery.typeset import fit_figure_labels, MEASURE_PX, WIDE_PX, FIGURE_LABEL_FLOOR_PT


def _svg(width, *sizes, css=False):
    texts = "".join((f'<text style="font-size:{s}px">t</text>' if css else f'<text font-size="{s}">t</text>') for s in sizes)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 300" width="{width}">{texts}</svg>'


def _printed_min(svg, wide):
    width = float(re.search(r'viewBox="0 0 ([\d.]+)', svg).group(1))
    sizes = [float(x) for x in re.findall(r'font-size(?:="|:)([\d.]+)', svg)]
    return min(sizes) * min(1.0, (WIDE_PX if wide else MEASURE_PX) / width) * 0.75


class FigureLabelFloor(unittest.TestCase):
    def test_small_enough_figure_unchanged(self):
        svg = _svg(400, 12, 14)
        self.assertEqual(fit_figure_labels(svg), (svg, False))

    def test_wide_figure_uses_full_text_block_without_touching_fonts(self):
        svg = _svg(680, 10, 11.5, 15)       # 10 px at the body measure would print at about 5.2 pt
        out, wide = fit_figure_labels(svg)
        self.assertTrue(wide)
        self.assertEqual(out, svg)
        self.assertGreaterEqual(_printed_min(out, wide), FIGURE_LABEL_FLOOR_PT)

    def test_too_small_even_when_wide_raises_only_small_sizes(self):
        svg = _svg(900, 7, 20, css=True)
        out, wide = fit_figure_labels(svg)
        self.assertTrue(wide)
        self.assertIn("font-size:20px", out)            # large labels untouched
        self.assertGreaterEqual(_printed_min(out, wide) + 1e-6, FIGURE_LABEL_FLOOR_PT)

    def test_narrow_figure_with_tiny_labels_is_lifted_not_widened(self):
        svg = _svg(300, 6)                                # not scaled; 6 px = 4.5 pt
        out, wide = fit_figure_labels(svg)
        self.assertFalse(wide)
        self.assertGreaterEqual(_printed_min(out, wide) + 1e-6, FIGURE_LABEL_FLOOR_PT)

    def test_svg_without_text_or_viewbox_passes_through(self):
        for svg in ('<svg viewBox="0 0 800 100"><rect/></svg>', '<svg><text font-size="5">x</text></svg>'):
            self.assertEqual(fit_figure_labels(svg), (svg, False))

    def test_wide_class_is_print_only_and_reaches_into_side_column(self):
        self.assertRegex(typeset.CSS, r"@media print\{figure\.wide\{margin-right:calc\(-1 \* \(var\(--side\) \+ var\(--gap\)\)\)\}\}")


if __name__ == "__main__":
    unittest.main()
