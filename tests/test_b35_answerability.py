"""B35 answerability gate: negative fixtures for every defect class named in the V4 review, plus positives that must
not be flagged (false-positive guard), plus the real V4 deck where the old format rules found nothing."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import answerability as A
from exam_mastery.anki_v2 import card_lint

V4 = Path.home() / 'Exam_Mastery_Output/rl_releases/RL_Kap03_OptimalDecisionMaking_v4_2026-11-17/produkte/Anki_Karten.apkg'


def card(front, answer='Eine Antwort mit Inhalt.', **kw):
    return dict({'key': 'x/y', 'kind': 'concept', 'front': front, 'answer': answer, 'source': 'Folie 3'}, **kw)


def status(c, dim, notation=()):
    return A.audit_card(A.card_view(c), frozenset(notation))[dim]['status']


class Negative(unittest.TestCase):
    def test_missing_image(self):
        c = card('Welche Zustände sind in der Abbildung absorbierend?')
        self.assertEqual(card_lint(c), [], 'old rules pass this card')
        self.assertEqual(status(c, 'VISUAL_DEPENDENCY'), 'FAIL')

    def test_image_on_back_only(self):
        c = card('Was zeigt die dargestellte Kurve?', figure='f1', figure_side='back')
        self.assertEqual(status(c, 'VISUAL_DEPENDENCY'), 'FAIL')

    def test_wrong_image_reference(self):
        v = A.card_view(card('Welche Zustände zeigt die Abbildung?', figure='f1', figure_side='front'), image_ok=False)
        self.assertEqual(A.audit_card(v)['VISUAL_DEPENDENCY']['status'], 'FAIL')

    def test_ambiguous_convention_dependent_count(self):
        self.assertEqual(status(card('Aus welchen sechs Bestandteilen besteht ein MDP?'), 'ANSWERABILITY'), 'WARN')
        self.assertEqual(status(card('Aus welchen sechs Bestandteilen besteht ein MDP laut Vorlesung?'), 'ANSWERABILITY'), 'PASS')

    def test_undefined_variables(self):
        c = card(r'Was gilt für \(\|T V - T U\|_\infty\)?')
        self.assertEqual(status(c, 'ANSWERABILITY'), 'WARN')
        self.assertEqual(status(c, 'ANSWERABILITY', notation={'T', 'V', 'U'}), 'PASS')

    def test_missing_model_assumptions_hidden_context(self):
        self.assertEqual(status(card('Was ergibt der Backup East in Zelle (3,3) mit V(3,2) = 0.57?'), 'ANSWERABILITY'), 'FAIL')
        self.assertEqual(status(card('Warum ist die gierige Policy im Gitter ab Sweep 10 optimal?'), 'ANSWERABILITY'), 'FAIL')

    def test_unsolvable_computation(self):
        self.assertEqual(status(card('Berechnen Sie den Wert des Startzustands?'), 'ANSWERABILITY'), 'FAIL')

    def test_wrong_back_side(self):
        c = card('Wie groß ist die geometrische Reihe 1 + 0.9 + 0.81 + ... ?', answer='10', check={'expr': '1/(1-0.9)', 'value': '9'})
        self.assertEqual(status(c, 'ANSWER_CORRECTNESS'), 'FAIL')

    def test_answer_on_front(self):
        c = card('Ist die Bellman-Gleichung linear in V für feste Policy, also linear?', answer='linear')
        self.assertEqual(status(c, 'QUESTION_VALIDITY'), 'FAIL')

    def test_gate_never_claims_correctness_without_check(self):
        self.assertEqual(status(card('Was besagt die Markov-Eigenschaft?'), 'ANSWER_CORRECTNESS'), 'NOT_VERIFIED')
        self.assertEqual(status(card('Was besagt die Markov-Eigenschaft?'), 'SOURCE_FIDELITY'), 'NOT_VERIFIED')


class Positive(unittest.TestCase):
    def test_self_contained_cards_pass(self):
        ok = [card('Welches Routing-Verfahren ist Wertiteration auf einem Graphen?'),
              card('Wie viele Schritte blickt ein Agent mit Diskont γ grob voraus?', answer='Etwa \\(1/(1-\\gamma)\\).'),
              card(r'Wie hängt \(r(s,a)\) mit \(r(s,a,s^{\prime})\) zusammen?', answer=r'\(r(s,a)=\sum_{s^{\prime}} p(s^{\prime}\mid s,a) r(s,a,s^{\prime})\)'),
              card('Was bestimmen Diskont und Rauschen jeweils?'),
              card('Wie groß ist 1/(1-0.9)?', answer='10', check={'expr': '1/(1-0.9)', 'value': '10'}),
              card('Was zeigt die Abbildung?', figure='f1', figure_side='front')]
        for c in ok:
            r = A.audit_card(A.card_view(c), frozenset('rsap'))
            for d in ('VISUAL_DEPENDENCY', 'QUESTION_VALIDITY', 'ANSWER_CORRECTNESS'):
                self.assertNotEqual(r[d]['status'], 'FAIL', (c['front'], d, r[d]))
            self.assertNotEqual(r['ANSWERABILITY']['status'], 'FAIL', (c['front'], r['ANSWERABILITY']))

    def test_duplicates_flagged(self):
        r = A.audit_deck([A.card_view(card('Was besagt die Markov-Eigenschaft eines Prozesses?', key='a/b')),
                          A.card_view(card('Was besagt die Markov-Eigenschaft eines Prozesses?', key='a/c'))])
        self.assertEqual(r['cards']['a/b']['REDUNDANCY']['status'], 'WARN')


@unittest.skipUnless(V4.exists(), 'V4 release package not present')
class RealV4Deck(unittest.TestCase):
    def test_gate_finds_defects_old_rules_missed(self):
        r = A.audit_deck(A.views_from_apkg(V4))
        self.assertEqual(r['status'], 'FAIL')
        for k in ('vi/gitter-backup', 'vi/gitter-vstar', 'pi/warten-start', 'vgl/roboter'):
            self.assertIn(k, r['blocking'])
        self.assertNotIn('anwendung/bellman-ford', r['blocking'])


if __name__ == '__main__':
    unittest.main()


class NotationPrinted(unittest.TestCase):
    def test_notation_line_makes_symbols_answerable(self):
        c = card(r'Was gilt für \(V^\pi\) bei \(\gamma < 1\)?')
        self.assertEqual(status(c, 'ANSWERABILITY'), 'WARN')
        c['context'] = A.notation_line(c, {'V': 'Wertfunktion', 'pi': 'Policy', 'gamma': 'Diskont'})
        self.assertIn('Wertfunktion', c['context'])
        self.assertEqual(status(c, 'ANSWERABILITY'), 'PASS')

    def test_no_line_when_nothing_missing(self):
        self.assertEqual(A.notation_line(card('Was ist ein MDP?'), {'V': 'x'}), '')

    def test_convention_anchor_variants(self):
        for f in ('Welche zwei Gründe nennt die Vorlesung?', 'Welche drei Merkmale hat ein Vertrag laut Skript?'):
            self.assertEqual(status(card(f), 'ANSWERABILITY'), 'PASS', f)
