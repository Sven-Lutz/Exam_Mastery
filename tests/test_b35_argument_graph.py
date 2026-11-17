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
        self.assertEqual(r['verification']['s1'], 'SYMBOLIC_IDENTITY')
        self.assertTrue(r['verification']['s10'].startswith('NUMERIC_EVIDENCE'))
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

    def test_missing_counterexample_warns(self):
        r = G.audit(self.mut(lambda g: g['counterexamples'].pop('A_gamma')))
        self.assertIn('A8', {f['code'] for f in r['findings']})


if __name__ == '__main__':
    unittest.main()
