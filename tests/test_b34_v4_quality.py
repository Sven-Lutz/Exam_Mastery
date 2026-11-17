"""B34 (RL V4 rebuild): regression tests for the generic engine changes. Synthetic data only."""
import re
import tempfile
import unittest
from pathlib import Path

from exam_mastery import typeset, slide_numbers as SN, edition, figure_kit
from exam_mastery.chapter_publish import RAW_MATH


class SlideNumbers(unittest.TestCase):
    def test_hidden_slide_shifts_numbers_and_unnumbered_pages_are_inferred_only_between_equal_offsets(self):
        pages = [(1, []), (2, [2]), (3, [3]), (4, [5]), (5, []), (6, [7]), (7, []), (8, [10])]
        m = SN.build_map(pages)
        self.assertEqual(m[4]['slide'], 5)
        self.assertEqual((m[5]['slide'], m[5]['basis']), (6, 'inferred'))          # neighbours 4->5 and 6->7: same offset +1
        self.assertEqual((m[7]['slide'], m[7]['basis']), (None, 'none'))           # 6->7 (+1) and 8->10 (+2): no guess
        self.assertEqual(m[1]['basis'], 'none')
        self.assertEqual(SN.summary(m)[0], (2, 3, 0))

    def test_footer_numbers_far_from_the_page_are_not_slide_numbers(self):
        m = SN.build_map([(1, [2026]), (2, [2]), (3, [0, 3])])
        self.assertIsNone(m[1]['slide'])
        self.assertEqual(m[3]['slide'], 3)

    def test_label_uses_printed_numbers_and_keeps_unknown_pages_as_pdf_pages(self):
        maps = {'deck.pdf': {10: {'slide': 11, 'basis': 'printed'}, 13: {'slide': None, 'basis': 'none'}}}
        self.assertEqual(SN.label('deck.pdf S. 10', maps), 'Folie 11')
        self.assertEqual(SN.label('deck.pdf S. 10; deck.pdf S. 13', maps), 'Folie 11 · PDF-S. 13')

    def test_ambiguous_deck_names_get_no_map(self):
        maps, rep = SN.course_maps({'root': '/nonexistent', 'sources': [{'source_id': 'a', 'relative_path': 'x/02.pdf'},
                                                                         {'source_id': 'b', 'relative_path': 'y/02.pdf'}]})
        self.assertEqual(maps, {})
        self.assertEqual({r['error'] for r in rep}, {'AMBIGUOUS_FILE_NAME'})


class MathText(unittest.TestCase):
    def test_numeric_powers_become_superscripts(self):
        self.assertIn('100<sup>14</sup>', typeset.inline('etwa 100^14 Zustände'))
        self.assertIn('0.9<sup>10</sup>', typeset.inline('Gewicht 0.9^10'))
        self.assertIn('\\(0.9^{10}\\)', typeset.inline('\\(0.9^{10}\\)'))           # real math untouched

    def test_raw_math_gate_pattern(self):
        for bad in ('100^14', 'V_{k+1}', '\\frac{1}{2}', '\\(x'):
            self.assertTrue(RAW_MATH.search(bad), bad)
        for good in ('snake_case', 'e-mail_x', 'Zeit 10:30', 'V k+1'):
            self.assertFalse(RAW_MATH.search(good), good)

    def test_table_cells_do_not_split_at_bars_inside_math(self):
        html = typeset.md('| a | b |\n|---|---|\n| \\(|r| \\le R\\) | 2 |')
        self.assertEqual(html.count('<td>'), 2)
        self.assertIn('\\(|r| \\le R\\)', html)


def _book(**kw):
    item = lambda i, p: {'id': i, 'no': i, 'prompt': 'Rechnen Sie.', 'operation': 'CALCULATE', 'points': p, 'minutes': 5,
                         'solution': {'answer': '1', 'steps': [['a', 'b']], 'rubric': [['x', p]]}}
    b = {'meta': {'chapter_no': 1, 'title': 'T', 'course': 'K', 'date': 'd', 'engine': 'x', 'status_line': 's'},
         'sections': [{'title': 'S', 'blocks': [
             {'type': 'derivation', 'title': 'Kette', 'goal': 'Ziel', 'rows': [['\\[ a = b \\]', 'weil'], ['b = c', 'auch']], 'conclusion': 'fertig', 'prov': 'interpretation',
              'src': 'deck.pdf S. 10'},
             {'type': 'research_note', 'title': 'Notiz', 'md': 'Text', 'refs': ['Ref 2020'], 'tags': ['Vertiefung'], 'prov': 'interpretation'},
             {'type': 'history', 'title': 'Früher', 'md': 'Text', 'refs': ['Alt 1952'], 'prov': 'interpretation'},
             {'type': 'box', 'kind': 'exam', 'title': 'Prüfung', 'md': 'x', 'prov': 'course', 'src': 'deck.pdf S. 10'}]}],
         'figures': {}, 'slide_maps': {'deck.pdf': {'10': {'slide': 11, 'basis': 'printed'}}},
         'stages': [{'title': 'Grundlagen', 'items': [item('s1', 2)]}],
         'exams': [], 'workbook_letters': True}
    for lab in ('A', 'B'):
        it = [dict(item(f'{lab.lower()}{k}', 5), no=f'{lab}{k}') for k in (1, 2)]
        b['exams'].append({'label': lab, 'title': f'Probeklausur {lab}', 'items': it, 'total_points': 10, 'minutes': 10, 'header': [['Punkte', '10']],
                           'self_designed_notice': 'selbst entworfen', 'subtitle': 'x'})
    b['exam'] = b['exams'][0]
    b.update(kw)
    return b


class Blocks(unittest.TestCase):
    def test_derivation_and_levels_render(self):
        h, _ = typeset.textbook(_book())
        self.assertIn('class="drv"', h)
        self.assertEqual(h.count('<li><div class="eq">'), 2)
        self.assertIn('zu Folie 11', h)                     # level C names the slide it works out
        self.assertIn('lv A', h)
        self.assertIn('Forschungsnotiz', h)
        self.assertIn('Historische Einordnung', h)
        self.assertIn('box exam', h)
        self.assertIn('Wie Sie die Quellenmarken lesen', typeset.LEVELS_HTML)

    def test_two_exams_are_separate_parts_with_distinct_item_numbers(self):
        b = _book()
        self.assertEqual(typeset.exam_check(b), [])
        body, toc = typeset.workbook_integrated(b)
        titles = [t for _, _, t in toc]
        self.assertTrue(any('Probeklausur A' in t for t in titles) and any('Probeklausur B' in t for t in titles))
        self.assertTrue(any(t.startswith('Teil B') and 'Lösungen' in t for t in titles))     # solutions follow part A directly
        self.assertIn('Aufgabe B2', body)

    def test_exam_check_reports_each_exam(self):
        b = _book()
        b['exams'][1]['total_points'] = 11
        self.assertTrue(any(p.startswith('B: ') for p in typeset.exam_check(b)))


class EditionExams(unittest.TestCase):
    def test_labelled_exam_ops_accumulate(self):
        base = {'meta': {'chapter_no': 1}, 'sections': [], 'figures': {}, 'cards': [],
                'stages': [{'title': 's', 'items': []}]}
        it = lambda i: {'id': i, 'prompt': 'p', 'operation': 'CALCULATE', 'points': 1, 'solution': {'answer': 'a', 'rubric': [['x', 1]]}}
        ed = {'schema': 'em-edition-v1', 'ops': [{'op': 'exam', 'label': 'A', 'items': [it('x1')], 'self_designed_notice': 'n'},
                                                  {'op': 'exam', 'label': 'B', 'items': [it('y1')], 'self_designed_notice': 'n'}]}
        b, _ = edition.apply(base, ed)
        self.assertEqual([e['items'][0]['no'] for e in b['exams']], ['A1', 'B1'])
        self.assertEqual(b['exam']['items'][0]['id'], 'x1')


class Figures(unittest.TestCase):
    def test_decision_text_fits_inside_the_diamond(self):
        svg = figure_kit.flow({'steps': [{'label': 'Start', 'kind': 'start'},
                                         {'label': 'Ändert sich die gierige Policy noch in irgendeinem Zustand des Modells?', 'kind': 'decision'},
                                         {'label': 'Ende', 'kind': 'end'}]})
        pts = re.search(r'<polygon points="([^"]+)"', svg).group(1).split()
        (cx, top), (right, mid), (_, bot), (left, _) = [tuple(map(float, p.split(','))) for p in pts]
        hh, half_w = mid - top, right - cx
        texts = re.findall(r'<text x="[\d.]+" y="([\d.]+)"[^>]*>([^<]*)</text>', svg)
        inside = [(float(y), t) for y, t in texts if top < float(y) < bot]
        self.assertTrue(inside)
        for y, t in inside:
            w_allowed = half_w * (1 - abs((y - 4) - mid) / hh) * 2
            self.assertLessEqual(len(t) * 7.3, w_allowed + 1, t)


class Anki(unittest.TestCase):
    def test_every_kind_has_a_cognitive_chip_and_dark_mode(self):
        from exam_mastery import anki_v2 as A
        for k in A.KIND_LABEL:
            self.assertIn(A.COGNITIVE[k], A.COG_LABEL, k)
            self.assertIn('class="k k-', A.kind_html(k))
        self.assertIn('.nightMode.card', A.CSS)
        for lab in ('Antwort', 'Warum', 'Typischer Denkfehler'):
            self.assertIn(lab, A.BASIC_A)


class Studio(unittest.TestCase):
    def test_compare_mode_asks_for_a_prediction_and_measures_work(self):
        from exam_mastery.labs import mdp_studio
        src = Path(mdp_studio.__file__).read_text()
        self.assertIn('Erst vorhersagen', src)
        self.assertIn('cmp-work-vi', src)
        self.assertIn('Multiplikationen', src)  # B35: counted under a declared cost model (was: estimated 'Rechenoperationen')


if __name__ == '__main__':
    unittest.main()


class Contrast(unittest.TestCase):
    """B34 accessibility: every role colour used as TEXT reaches 4.5:1 on white and on its own tint (WCAG AA)."""
    @staticmethod
    def ratio(a, b):
        def lum(h):
            c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
            return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
        la, lb = sorted((lum(a), lum(b)), reverse=True)
        return (la + 0.05) / (lb + 0.05)

    def test_role_colours(self):
        css = typeset.CSS
        var = dict(re.findall(r'--([a-z-]+):(#[0-9A-Fa-f]{6})', css))
        for role in ('teal', 'blue', 'indigo', 'amber', 'plum', 'coral', 'crimson', 'green', 'slate', 'navy', 'muted'):
            self.assertGreaterEqual(self.ratio(var[role], '#FFFFFF'), 4.5, role)
            if role + '-l' in var:
                self.assertGreaterEqual(self.ratio(var[role], var[role + '-l']), 4.5, role + ' on tint')
