"""B35 argument graph / proof audit: the Bellman reference argument passes, and each defect class from the
proof-audit list is caught by a mutation of it (negative fixtures)."""
import copy, json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import argument_graph as G

REF = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/arguments/bellman_expectation.json').read_text())


def fails(g):
    return {(f['code'], f['step']) for f in G.audit(g)['findings'] if f['severity'] == 'FAIL'}


class Reference(unittest.TestCase):
    def test_reference_passes_and_reports_real_reach(self):
        r = G.audit(REF)
        self.assertEqual(r['status'], 'PASS', r['findings'])
        self.assertEqual(r['verification']['s1'], ['SYMBOLIC_PARTIAL', 'ANALYTIC_ARGUMENT'])
        s10 = r['verification']['s10']
        self.assertTrue(any(t.startswith('NUMERIC_TESTED') and 'not a proof' in t for t in s10))
        self.assertTrue(any(t.startswith('ANALYTIC_ARGUMENT (sub-proof') for t in s10))
        self.assertFalse(any(t.startswith('FORMAL_VERIFIED') for v in r['verification'].values() for t in v))
        self.assertIn('NOT machine-verified', r['scope'])
        self.assertEqual(len(G.matrix(REF)), len(REF['steps']))


class Mutations(unittest.TestCase):
    def mut(self, f):
        g = copy.deepcopy(REF); f(g); return g

    def test_hidden_premise(self):
        self.assertIn(('A3', 's5'), fails(self.mut(lambda g: g['claim']['assumptions'].remove('A_markov'))))

    def test_unjustified_step(self):
        self.assertIn(('A1', 's6'), fails(self.mut(lambda g: g['steps'][5].update(justification=''))))

    def test_forward_dependency(self):
        self.assertIn(('A2', 's3'), fails(self.mut(lambda g: g['steps'][2]['depends_on'].append('s9'))))

    def test_approximation_inside_theorem(self):
        self.assertIn(('A5', 's8'), fails(self.mut(lambda g: g['steps'][7].update(relation='APPROXIMATION'))))

    def test_wrong_algebra_detected(self):
        self.assertIn(('A6', 's2'), fails(self.mut(lambda g: g['steps'][1]['check'].update(rhs='1-g**n'))))

    def test_conclusion_not_reached(self):
        self.assertIn(('A7', 's11'), fails(self.mut(lambda g: g['steps'][-1].update(to='V = 0'))))

    def test_numeric_test_is_not_a_proof(self):
        self.assertIn(('A6', 's10'), fails(self.mut(lambda g: g['steps'][9].pop('proof'))))

    def test_undeclared_symbol_warns(self):
        r = G.audit(self.mut(lambda g: g['notation'].remove('S')))
        self.assertIn('A9', {f['code'] for f in r['findings']})

    def test_unrecorded_review_is_not_counted(self):
        g = self.mut(lambda g: g['steps'][4].update(reviews=[{'by': 'model', 'verdict': 'ok'}, {'by': 'human', 'verdict': 'pending'}]))
        t = G.audit(g)['verification']['s5']
        self.assertIn('MODEL_REVIEWED', t); self.assertNotIn('HUMAN_REVIEWED', t)

    def test_missing_counterexample_warns(self):
        r = G.audit(self.mut(lambda g: g['counterexamples'].pop('A_gamma')))
        self.assertIn('A8', {f['code'] for f in r['findings']})


if __name__ == '__main__':
    unittest.main()
