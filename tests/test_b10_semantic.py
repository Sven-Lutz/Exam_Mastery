"""B10: semantic consistency rules DR-1.1. Each test pairs a defective case with its corrected counterpart and uses
contrasting subjects (economics, law, mathematics, machine learning), so the rules check error classes, not one course."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'fixtures'))
from exam_mastery import semantic_checks as S  # noqa: E402


def book(blocks, items=(), cards=()):
    return {'meta': {'lang': 'de'}, 'sections': [{'title': 'A', 'blocks': list(blocks)}],
            'stages': [{'title': 'S', 'level': 1, 'items': list(items)}], 'cards': list(cards)}


def table(rows, cols=('Name', 'Ort'), **kw):
    return dict({'type': 'table', 'columns': list(cols), 'rows': [list(r) for r in rows]}, **kw)


def text(md, **kw):
    return dict({'type': 'text', 'md': md}, **kw)


def st(results, rule):
    return [r['status'] for r in results if r['rule'] == rule]


class CountClaims(unittest.TestCase):
    T = table([['A', 'München'], ['B', 'Berlin'], ['C', 'München / Gilching'], ['D', 'Köln']])

    def test_wrong_count_fails(self):
        self.assertEqual(st(S.check_book(book([self.T, text('Drei der vier Firmen sitzen in München.')])), 'S1'), ['FAIL'])

    def test_right_count_passes(self):
        self.assertEqual(st(S.check_book(book([self.T, text('Zwei der vier Firmen sitzen in München.')])), 'S1'), ['PASS'])

    def test_ml_benchmark_table(self):
        t = table([['ResNet', 'CNN'], ['ViT', 'Transformer'], ['BERT', 'Transformer']], cols=('Modell', 'Architektur'))
        self.assertEqual(st(S.check_book(book([t, text('Zwei der drei Modelle nutzen einen Transformer.')])), 'S1'), ['PASS'])
        self.assertEqual(st(S.check_book(book([t, text('Drei der drei Modelle nutzen einen Transformer.')])), 'S1'), ['FAIL'])

    def test_unverifiable_count_is_review_not_pass(self):
        self.assertEqual(st(S.check_book(book([text('Sieben der zehn Gründer scheitern.')])), 'S1'), ['REVIEW'])


class StatisticalInference(unittest.TestCase):
    def test_sd_based_inference_fails(self):
        r = S.check_book(book([text('Die Mittelwerte 2.31 und 2.32 liegen so dicht, dass die Reihenfolge bei SD 0.8 kaum belastbar ist.')]))
        self.assertEqual(st(r, 'S2'), ['FAIL'])

    def test_hedged_statement_passes(self):
        r = S.check_book(book([text('Ob der Unterschied signifikant ist, lässt sich ohne Stichprobenumfang nicht beurteilen.')]))
        self.assertEqual(st(r, 'S2'), ['PASS'])

    def test_supported_inference_passes(self):
        r = S.check_book(book([text('Modell B ist signifikant besser (n = 1200, t-Test, p < 0.01).')]))
        self.assertEqual(st(r, 'S2'), ['PASS'])


class CauseClaims(unittest.TestCase):
    def test_cause_for_source_inconsistency_fails(self):
        r = S.check_book(book([table([['a', '1'], ['Summe', '3']], known_inconsistency='x'),
                               text('Die Ursache ist eine Rundung der Beträge.')]))
        self.assertEqual(st(r, 'S3'), ['FAIL'])

    def test_hedged_cause_passes(self):
        r = S.check_book(book([table([['a', '1']], known_inconsistency='x'),
                               text('Die Ursache ist nicht belegt; plausibel ist eine Rundung.')]))
        self.assertEqual(st(r, 'S3'), [])

    def test_unsourced_consequence_claim_needs_review(self):
        r = S.check_book(book([text('Kapitalmangel ist meist die Folge schlechter Unit Economics.', prov='interpretation')]))
        self.assertEqual(st(r, 'S3'), ['REVIEW'])


class TermConflicts(unittest.TestCase):
    def test_column_used_for_other_concept_fails(self):
        t = table([['HTGF', '595', '„Agio“ ist hier ein Darlehen']], cols=('Partner', 'Agio', 'Anmerkung'))
        self.assertIn('FAIL', st(S.check_book(book([t])), 'S4'))

    def test_aggregation_contradicting_denial_fails(self):
        r = S.check_book(book([text('Insgesamt stehen 900 zur Verfügung (Eigenkapital plus Agio).'),
                               text('Der Agio-Betrag des Investors ist **kein** Aufgeld, sondern ein Darlehen.')]))
        self.assertIn('FAIL', st(r, 'S4'))

    def test_clean_distinction_passes(self):
        t = table([['HTGF', '595', 'kein Agio: Darlehen']], cols=('Partner', 'Spalte „Agio“ der Folie', 'Anmerkung'))
        self.assertEqual(st(S.check_book(book([t])), 'S4'), ['PASS'])


def item(prompt, steps, answer):
    return {'id': 'x', 'prompt': prompt, 'solution': {'steps': [[s] for s in steps], 'answer': answer}}


class LegalSubsumption(unittest.TestCase):
    def test_conclusion_without_facts_fails(self):
        it = item('A kann Rechnungen nicht bezahlen. Was gilt?', ['§ 17 InsO → Zahlungsunfähigkeit liegt vor.'], 'Antrag stellen.')
        self.assertIn('FAIL', st(S.check_book(book([], [it])), 'S5'))

    def test_conclusion_with_stated_assumptions_passes(self):
        it = item('A hat 180 fällig, 40 liquide; keine Zuflüsse (Annahmen des Falls).', ['§ 17 InsO: Zahlungsunfähigkeit liegt vor.'], 'Antrag.')
        self.assertEqual(st(S.check_book(book([], [it])), 'S5'), ['PASS'])

    def test_civil_law_case(self):
        bad = item('K will Eigentum.', ['§ 929 BGB: Einigung und Übergabe sind erfüllt.'], 'K ist Eigentümer.')
        good = item('Laut Sachverhalt einigen sich V und K und V übergibt die Sache.', ['§ 929 BGB: Einigung und Übergabe sind erfüllt.'], 'K ist Eigentümer.')
        self.assertIn('FAIL', st(S.check_book(book([], [bad])), 'S5'))
        self.assertEqual(st(S.check_book(book([], [good])), 'S5'), ['PASS'])

    def test_absolute_prohibition_flagged_for_review(self):
        it = item('Laut Sachverhalt ist die GmbH zahlungsunfähig.', ['§ 15b InsO: Die Geschäftsführer dürfen keine Zahlungen leisten.'], 'Keine Zahlungen.')
        self.assertIn('REVIEW', st(S.check_book(book([], [it])), 'S5'))


class BookCardConsistency(unittest.TestCase):
    def test_card_number_missing_in_book_needs_review(self):
        b = book([text('Der Höchststand lag bei 14.6 Mrd. €.')], cards=[{'key': 'a/b', 'kind': 'fact', 'front': 'Wie hoch?', 'answer': '15.2 Mrd. €'}])
        self.assertEqual(st(S.check_book(b), 'S6'), ['REVIEW'])

    def test_consistent_card_passes(self):
        b = book([text('Der Höchststand lag bei 14.6 Mrd. €.')], cards=[{'key': 'a/b', 'kind': 'fact', 'front': 'Wie hoch?', 'answer': '14.6 Mrd. €'}])
        self.assertEqual(st(S.check_book(b), 'S6'), ['PASS'])


class CardQuality(unittest.TestCase):
    def rules(self, c):
        return [r for r, _s, _d in S.card_quality(c)]

    def test_long_list_without_reason(self):
        c = {'key': 'k/a', 'kind': 'concept', 'front': 'Welche fünf Exit-Wege gibt es?', 'answer': 'A, B, C, D, E.'}
        self.assertIn('C6', self.rules(c))
        self.assertNotIn('C6', self.rules(dict(c, list_reason='Prüfungsfrage verlangt die Liste')))

    def test_mechanism_needs_explanation(self):
        c = {'key': 'k/b', 'kind': 'mechanism', 'front': 'Warum konvergiert Gradientenabstieg bei zu großer Lernrate nicht?', 'answer': 'Er springt über das Minimum.'}
        self.assertIn('C7', self.rules(c))
        self.assertNotIn('C7', self.rules(dict(c, explanation='Der Schritt überschreitet die Krümmungsskala 2/L.')))

    def test_visual_label_requires_front_figure(self):
        c = {'key': 'k/c', 'kind': 'visual', 'front': 'Was zeigt die Abbildung?', 'answer': 'Eine Rangfolge.', 'figure': 'f'}
        self.assertIn('C8', self.rules(c))
        self.assertNotIn('C8', self.rules(dict(c, figure_side='front')))

    def test_answer_cue(self):
        c = {'key': 'k/d', 'kind': 'concept', 'front': 'Was ist die Ableitung der Exponentialfunktion exp?', 'answer': 'Exponentialfunktion.'}
        self.assertIn('C9', self.rules(c))
        self.assertNotIn('C9', self.rules({'key': 'k/e', 'kind': 'concept', 'front': 'Innen- oder Außenfinanzierung?', 'answer': 'Außenfinanzierung.'}))


class DomainDemonstrations(unittest.TestCase):
    def test_demo_books_pass_semantic_rules(self):
        from b9_domain_books import BOOKS
        for name, b in BOOKS.items():
            bad = [r for r in S.check_book(b) if r['status'] == 'FAIL']
            self.assertEqual(bad, [], name)


if __name__ == '__main__':
    unittest.main()
