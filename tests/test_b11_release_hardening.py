"""B11: one figure-status source for PDF, dossier and matrix; CLI help; no stale status."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from exam_mastery import figure_status as FS


def triage(**over):
    t = {'source': 'x.pdf', 'as_of': 'test', 'slides': [
        {'slide': 1, 'status': 'DECORATIVE', 'reason': 'Titelfoto', 'kc': []},
        {'slide': 2, 'status': 'CONTENT_INTEGRATED', 'reason': 'Diagramm – in Abb. 1', 'kc': ['a']},
        {'slide': 3, 'status': 'NOT_RELIABLY_EVALUATED', 'reason': 'Schrift zu klein', 'kc': ['a']}]}
    t.update(over)
    return t


class FigureStatus(unittest.TestCase):
    def test_validate_catches_unknown_status_missing_reason_and_gaps(self):
        self.assertEqual(FS.validate(triage(), figure_pages=[1, 2, 3]), [])
        bad = triage(slides=[{'slide': 1, 'status': 'SEEN', 'reason': ''}, {'slide': 1, 'status': 'DECORATIVE', 'reason': 'x'}])
        p = FS.validate(bad, figure_pages=[1, 2])
        self.assertTrue(any('unknown status' in x for x in p) and any('no reason' in x for x in p)
                        and any('listed twice' in x for x in p) and any('slide 2: figure without status' in x for x in p), p)

    def test_counts_cover_all_four_states(self):
        self.assertEqual(FS.counts(triage()), {'CONTENT_INTEGRATED': 1, 'TEXT_EQUIVALENT': 0, 'DECORATIVE': 1, 'NOT_RELIABLY_EVALUATED': 1})

    def test_pdf_and_matrix_use_the_same_state(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'x.pdf'; d = pymupdf.open()
            for i in range(3):
                d.new_page().insert_text((50, 50), f'Folie {i + 1}')
            d.save(src)
            out = Path(td) / 'f.pdf'
            self.assertEqual(FS.render_pdf(triage(), src, out), 4)
            text = ''.join(p.get_text() for p in pymupdf.open(out))
            self.assertNotIn('?', text)                                  # typographic dashes mapped, not dropped
            for k, v in FS.counts(triage()).items():
                self.assertIn(f'{v:>2} Folien: {FS.LABEL[k]}', text)
            rows = FS.matrix(triage(), [{'key': 'a', 'label': 'A', 'operation': 'EXPLAIN'}])
            self.assertEqual(rows[0]['abbildungen'], 'F2:CONTENT_INTEGRATED F3:NOT_RELIABLY_EVALUATED')
            self.assertEqual(rows[0]['offene_abbildungen'], 'F3')


class Cli(unittest.TestCase):
    def test_help_is_not_a_production_call(self):
        from exam_mastery.runtime import main
        for flag in ('--help', '-h', 'help'):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main([flag]), 0)
            self.assertIn('exam-mastery status', buf.getvalue())



class VisualNumbers(unittest.TestCase):
    def test_numbers_may_be_json_numbers_or_strings(self):
        from exam_mastery.visual_evidence import _norm_num
        self.assertEqual(_norm_num(2009), '2009')
        self.assertEqual(_norm_num('2009'), '2009')
        self.assertEqual(_norm_num(1.5), '1.5')
        self.assertEqual(_norm_num('1,027'), '1027')



class E2EFindings(unittest.TestCase):
    """B12: defects found by the first agent-provider end-to-end run (chapter 07 of a real course copy)."""

    def test_negative_results_are_found_in_solutions(self):
        from exam_mastery.quality_gates import _states
        self.assertTrue(_states('Periode 1: \\(0 - 30 - 100 = -130\\).', -130.0))
        self.assertTrue(_states('Cashflows -130, -30, 20 k€', -30.0))
        self.assertTrue(_states('Wert −5', -5.0))
        self.assertFalse(_states('\\(50 - 30 = 20\\)', -30.0))     # an operator is not a sign
        self.assertFalse(_states('50-30=20', -30.0))

    def test_derived_card_keys_are_ascii(self):
        from exam_mastery.book_model import derived_cards
        from exam_mastery.anki_v2 import card_lint
        cards = derived_cards([{'type': 'definition', 'term': 'Prinzip 4: Lemonade (Zufälle nutzen)', 'md': 'Überraschungen nutzen. Mehr.'},
                               {'type': 'misconception', 'wrong': 'Effectuation heißt, auf jeden Plan zu verzichten.', 'right': 'Nein.', 'why': ''}], 'k')
        self.assertEqual([c['key'] for c in cards], ['def/prinzip-4-lemonade-zufaelle-nutzen', 'mis/effectuation-heisst-auf-jeden-plan-zu-verzichten'])
        self.assertTrue(all('C5' not in ' '.join(card_lint(c)) for c in cards))

    def test_calculation_item_that_asks_to_explain_practises_explain(self):
        from exam_mastery import didactic_rules as D
        book = {'meta': {'lang': 'de'}, 'sections': [{'title': 'A', 'blocks': [{'type': 'lead', 'md': 'x'}, {'type': 'summary', 'md': 'y'}]}],
                'competencies': [{'key': 'cf', 'operation': 'EXPLAIN'}],
                'stages': [{'title': 'S', 'level': 1, 'items': [{'id': 'i', 'prompt': 'Berechnen Sie den Finanzbedarf bei 3 Perioden und erklären Sie das Ergebnis.',
                                                             'operation': 'CALCULATE', 'kc_keys': ['cf'], 'solution': {'answer': 'a', 'steps': [['s', '']], 'errors': ['e']}}]}]}
        self.assertEqual([r['status'] for r in D.check_book(book) if r['rule'] == 'A1'], ['PASS'])

    def test_scale_label_significant_is_not_a_statistical_claim(self):
        from exam_mastery import semantic_checks as S
        b = {'meta': {}, 'sections': [{'title': 'R', 'blocks': [{'type': 'text', 'md': '5. **Erheblich (significant):** Das Risiko kann existenzbedrohend sein.'}]}], 'stages': [], 'cards': []}
        self.assertEqual([r['status'] for r in S.check_book(b) if r['rule'] == 'S2'], [])
        b['sections'][0]['blocks'][0]['md'] = 'Modell B ist significantly better als A.'
        self.assertEqual([r['status'] for r in S.check_book(b) if r['rule'] == 'S2'], ['FAIL'])


    def test_exam_topic_is_cut_at_a_word(self):
        from exam_mastery.book_model import _topic
        self.assertEqual(_topic('Erklären Sie die drei Gründe, die die Vorlesung für einen Businessplan nennt.'),
                         'Erklären Sie die drei Gründe, die die Vorlesung für einen …')
        self.assertEqual(_topic('Nennen Sie X. Danach Y.'), 'Nennen Sie X.')


if __name__ == '__main__':
    unittest.main()
