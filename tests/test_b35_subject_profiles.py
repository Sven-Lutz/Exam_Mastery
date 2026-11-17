"""B35 subject profiles: activation by competency text across disciplines, combinability, no cross-discipline leaks,
and the V4 finding (flattened operations) reproduced."""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import subject_profiles as SP

V4 = Path.home() / 'Exam_Mastery_Output/course-a8fba2d65467/ch-20261117T120000Z-v4/chapters/ch-271642018f0467/publish/book.json'


class Activation(unittest.TestCase):
    def packs(self, text, declared=()):
        return set(SP.resolve(text, declared)['packs'])

    def test_math_proof(self):
        r = SP.resolve('Den Konvergenzsatz der Wertiteration formulieren und beweisen.')
        self.assertIn('formal-mathematics', r['packs'])
        self.assertTrue({'theorem_statement', 'proof', 'counterexample'} <= set(r['requires']))
        self.assertIn('argument_graph', r['validators'])

    def test_legal_subsumption(self):
        r = SP.resolve('Prüfen, ob die Kündigung nach § 626 BGB wirksam ist: Tatbestand subsumieren.')
        self.assertIn('legal-reasoning', r['packs'])
        self.assertTrue({'case_solution', 'norm_text'} <= set(r['requires']))

    def test_ml_combines_packs(self):
        p = self.packs('Den Gradienten der Verlustfunktion herleiten, den Algorithmus implementieren und seine Laufzeit analysieren; '
                       'Messdaten aus dem Experiment auswerten.')
        self.assertTrue({'formal-mathematics', 'computational-reasoning', 'empirical-research'} <= p)

    def test_finance_valuation(self):
        r = SP.resolve('Den Kapitalwert eines Projekts aus den Cashflows berechnen.')
        self.assertIn('economic-modeling', r['packs']); self.assertIn('sensitivity', r['requires'])

    def test_clinical(self):
        self.assertIn('clinical-reasoning', self.packs('Eine Differentialdiagnose bei Brustschmerz aufstellen.'))

    def test_no_cross_discipline_leaks(self):
        for t in ('Policy-Bewertung und Wertiteration einordnen.', 'Die Supremumsnorm einer Differenz abschätzen.',
                  'Policy Iteration als Verfahren einordnen.'):
            self.assertFalse(self.packs(t) & {'legal-reasoning', 'economic-modeling', 'clinical-reasoning'}, t)

    def test_declared_operation_is_kept(self):
        self.assertIn('prove', SP.resolve('Satz 3 behandeln.', ['PROVE'])['operations'])


@unittest.skipUnless(V4.exists(), 'V4 build not present')
class V4Finding(unittest.TestCase):
    def test_flattened_operations_and_missing_links_reported(self):
        r = SP.coverage(json.loads(V4.read_text()))
        self.assertGreaterEqual(r['operation_flattened'], 20)
        self.assertLess(r['linked_share'], 0.5)
        self.assertTrue(any('practice_task' in o['missing'] for o in r['objectives']))


if __name__ == '__main__':
    unittest.main()


class CrossDomainCorpus(unittest.TestCase):
    """Regression on the (consumed) cross-domain corpus; the numbers are a floor, not a quality claim."""
    def test_corpus_floor_and_no_leaks(self):
        H = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/cross_domain/objectives_holdout.json').read_text())['items']
        hit = sum(1 for t, exp in H if set(SP.resolve(t)['packs']) & set(exp))
        self.assertGreaterEqual(hit, 22)
        self.assertNotIn('clinical-reasoning', SP.resolve('Compute the net present value and run a sensitivity analysis')['packs'])
        for t in ('Differentiate acute coronary syndrome from pulmonary embolism', 'Advise the claimant on negligence liability',
                  'Critically assess the source reliability of a medieval chronicle', 'Balance redox equations in acidic solution'):
            self.assertNotEqual(SP.resolve(t)['packs'], ['instructional-design'], t)
