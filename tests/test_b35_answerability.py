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

    def test_compound_deictic_reference(self):
        self.assertEqual(status(card('Wie stark werden die Gründer im HTGF-Beispiel verwässert?'), 'ANSWERABILITY'), 'FAIL')

    def test_source_and_statute_anchors(self):
        for f in ('Welche fünf Exit-Ereignisse nennen Cumming und MacIntosh (2003)?', 'Welche drei Insolvenzgründe nennt die InsO in §§ 17–19?',
                  'In welche vier Kategorien ordnen Brandenburger et al. (2012) die Kriterien?'):
            self.assertEqual(status(card(f), 'ANSWERABILITY'), 'PASS', f)

    def test_recall_quantity_is_warn_not_fail(self):
        self.assertEqual(status(card('Wie viel investiert der Fonds üblicherweise in der Seed-Phase?'), 'ANSWERABILITY'), 'WARN')

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
        for k in ('vi/gitter-backup', 'vi/gitter-vstar', 'grid/klippe'):
            self.assertIn(k, r['blocking'])
        for k in ('pi/warten-start', 'vgl/roboter'):        # quantity questions without data: flagged, not blocking (trade-off)
            self.assertNotEqual(r['cards'][k]['ANSWERABILITY']['status'], 'PASS')
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


class ReviewFindings(unittest.TestCase):
    """Cases from the adversarial answerability and cross-domain reviews."""
    def test_cross_domain_false_positives_gone(self):
        for f in ('Evaluate the significance of the Magna Carta?', 'What is the plot of Hamlet about?',
                  'Which chart type best shows a distribution?'):
            r = A.audit_card(A.card_view(card(f)))
            self.assertNotEqual(r['ANSWERABILITY']['status'], 'FAIL', f); self.assertNotEqual(r['VISUAL_DEPENDENCY']['status'], 'FAIL', f)

    def test_cross_domain_false_negatives_caught(self):
        self.assertEqual(status(card('What does the image of this ECG show?'), 'VISUAL_DEPENDENCY'), 'FAIL')
        self.assertEqual(status(card('Name the two types of cell division?'), 'ANSWERABILITY'), 'WARN')
        self.assertEqual(status(card('What is the dose for this patient?'), 'ANSWERABILITY'), 'WARN')
        self.assertEqual(status(card('Lesen Sie den Kipppunkt ab: Wo wechselt die Policy?'), 'VISUAL_DEPENDENCY'), 'FAIL')

    def test_two_targets(self):
        self.assertEqual(status(card('Welche Operation ersetzt das Mittel? Schreiben Sie die Gleichung auf.'), 'QUESTION_VALIDITY'), 'FAIL')
        self.assertEqual(status(card('Welche Richtung ist optimal – und warum nicht Ost?'), 'QUESTION_VALIDITY'), 'FAIL')

    def test_named_example_needs_definition(self):
        ex = {'Roboter': 'Roboter: High/Low, search/wait/recharge (Modell).'}
        c = card('Welche zwei Gleichungen gelten für den Roboter unter search/recharge?')
        self.assertEqual(A.audit_card(A.card_view(c), examples=ex)['ANSWERABILITY']['status'], 'FAIL')
        c['context'] = A.example_line(c, ex)
        self.assertNotEqual(A.audit_card(A.card_view(c), examples=ex)['ANSWERABILITY']['status'], 'FAIL')


NLP = Path.home() / 'Exam_Mastery_Output/reference_units/nlp_sequence_labeling/nlp-sequence-labeling.apkg'


@unittest.skipUnless(NLP.exists(), 'NLP deck not present')
class ForeignDeckFormat(unittest.TestCase):
    """Consumed holdout: current Anki package format (zstd, schema 18) with a foreign note type must be readable."""
    def test_reads_and_audits(self):
        v = A.views_from_apkg(NLP)
        self.assertEqual(len(v), 50); self.assertEqual(len({x['key'] for x in v}), 50)
        self.assertTrue(all(A._text(x['front']) for x in v))
        r = A.audit_deck(v)
        self.assertLessEqual(len(r['blocking']), 2)

    def test_imperative_and_formula_answers_not_blocked(self):
        self.assertEqual(status(card('Fehler finden: „Die Ausgabeschicht hat 5 Parameter.“'), 'QUESTION_VALIDITY'), 'PASS')
        self.assertNotIn('mapsto', A._symbols(r'k_j \mapsto k_j + u'))
