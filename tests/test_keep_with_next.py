"""Headings stay with what follows them, without pushing long prose to the next page (PG-ORPHAN-HEADING, PG-NEAR-EMPTY).

Chromium honours break-after:avoid after one unbreakable group of headings, but not through stacked headings or in
front of an unbreakable box. So: before splittable prose the headings form their own keep group; before anything
else heading and block are kept together; a task head is kept with its prompt."""
import json
from pathlib import Path
import re
import unittest

from exam_mastery import typeset
from exam_mastery.learning import experience_books as books

META = {'title': 'T', 'subtitle': '', 'course': 'K', 'chapter_no': 1, 'lang': 'de', 'date': '', 'engine': 'x',
        'status_line': 'Entwurf'}


def _book(first_block):
    return {'meta': META, 'figures': {}, 'sections': [
        {'title': 'Abschnitt', 'subsections': [{'title': 'Unterabschnitt', 'blocks': [first_block,
                                                                                       {'type': 'text', 'md': 'Weiter.'}]}]}]}


class TextbookHeadings(unittest.TestCase):
    def test_prose_is_not_kept_whole_with_its_headings(self):
        long = '\n\n'.join('Absatz %d mit Text.' % k for k in range(40))
        body, _ = typeset.textbook(_book({'type': 'text', 'md': long}))
        group = re.search(r'<div class="keephead heads">(.*?)</div>(.*?)$', body, re.S)
        self.assertIsNotNone(group)
        self.assertEqual(re.findall(r'<h(\d)', group.group(1)), ['2', '3'])     # both headings in one keep group
        self.assertTrue(group.group(2).startswith('<div class="blk">'))          # the prose follows outside it
        self.assertNotIn('Absatz 0', group.group(1))

    def test_lead_counts_as_prose(self):
        body, _ = typeset.textbook(_book({'type': 'lead', 'md': 'Einstieg.'}))
        self.assertIn('<div class="keephead heads">', body)

    def test_unbreakable_first_block_is_kept_with_its_headings(self):
        body, _ = typeset.textbook(_book({'type': 'definition', 'term': 'Begriff', 'md': 'Inhalt.'}))
        self.assertNotIn('keephead heads', body)
        self.assertRegex(body, r'<div class="keephead"><h2 [^>]*>.*?</h2><h3 [^>]*>.*?</h3><div class="blk">.*?'
                               r'<div class="def">.*?</div></div></div>')


    def test_css_keeps_the_heading_group_with_the_next_lines(self):
        self.assertIn('.keephead.heads{break-after:avoid}', typeset.CSS)
        self.assertRegex(typeset.CSS, r'\.keephead,[^{]*\{break-inside:avoid-page\}')
        self.assertRegex(typeset.CSS, r'p\{[^}]*orphans:3')


class TaskHeads(unittest.TestCase):
    def test_task_head_is_kept_with_its_prompt(self):
        item = {'id': 'a1', 'no': '1', 'title': 'Titel', 'prompt': 'Zeigen Sie X.', 'solution': {'answer': 'X.'}}
        h = typeset._item_html(typeset.Doc({'meta': META, 'figures': {}}, 'workbook'), item)
        self.assertRegex(h, r'^<div class="item" id="a1"><div class="keephead"><div class="head">.*?</div><p>Zeigen Sie X\.</p></div>')

    def test_stage_heading_joins_the_head_of_a_worked_example_only(self):
        unit = json.loads((Path(__file__).resolve().parents[1] / 'fixtures' / 'experience_reference.json')
                          .read_text(encoding='utf-8'))
        book = books.book_model(unit)
        stage = book['stages'][0]
        stage['items'][0]['worked'] = True
        body, _ = books._combined_workbook(book)
        heading = re.search(r'<h2 id="aufgaben-1">.*?</h2>', body).group(0)
        # the stage heading sits inside the worked item's own keep group (head + prompt), not around the whole item
        self.assertIn('<div class="item worked" style="break-inside:auto" id="%s"><div class="keephead">%s<div class="head">'
                      % (stage['items'][0]['id'], heading), body)


try:
    import pymupdf
    HAVE_PDF = True
except ImportError:      # pragma: no cover
    HAVE_PDF = False


@unittest.skipUnless(HAVE_PDF, 'pymupdf not installed')
class GateHeadingHeuristic(unittest.TestCase):
    def _check(self, draw):
        import tempfile
        from exam_mastery.mastery import quality as Q
        doc = pymupdf.open()
        for fn in (self._body, draw, self._body):
            fn(doc.new_page(width=595, height=842))
        with tempfile.TemporaryDirectory() as tmp:
            doc.save(Path(tmp) / 'x.pdf')
            return [g for g, *_ in Q.check_pdf(Path(tmp) / 'x.pdf', 'Lehrbuch')]

    @staticmethod
    def _body(page, n=40, y0=80):
        for k in range(n):
            page.insert_text((70, y0 + 16 * k), 'Fließtext einer Zeile mit ausreichend vielen Wörtern.', fontsize=10.5)

    def test_bold_end_of_a_paragraph_is_not_a_heading(self):
        def page(p):
            self._body(p, 42)
            p.insert_text((70, 80 + 16 * 42), 'mit möglichst wenig Varianz?', fontsize=10.5, fontname='hebo')
        self.assertEqual(self._check(page), [])

    def test_bold_heading_with_space_above_is_still_found(self):
        def page(p):
            self._body(p, 40)
            p.insert_text((70, 80 + 16 * 40 + 14), 'Abschnitt über Spalten', fontsize=10.5, fontname='hebo')
        self.assertEqual(self._check(page), ['PG-ORPHAN-HEADING'])


if __name__ == '__main__':
    unittest.main()
