import unittest
from fractions import Fraction as F
from exam_mastery import mdp_oracle as O
from exam_mastery.labs import models as M

ROBOT = {'states': ['high', 'low', 'dead'], 'gamma': '9/10', 'transitions': [
    {'s': 'high', 'a': 'search', 'r': 2, 'next': {'high': '3/4', 'low': '1/4'}}, {'s': 'high', 'a': 'wait', 'r': 1, 'next': {'high': 1}},
    {'s': 'low', 'a': 'search', 'r': 2, 'next': {'low': '1/2', 'dead': '1/2'}}, {'s': 'low', 'a': 'wait', 'r': 1, 'next': {'low': 1}},
    {'s': 'low', 'a': 'recharge', 'r': 0, 'next': {'high': 1}}]}


class OracleTest(unittest.TestCase):
    def test_exact_optimum_and_lab_agreement(self):
        m = O.normalise(ROBOT); V, pols = O.optimal(m)
        self.assertEqual(V['high'], F(800, 49))
        self.assertEqual(pols, [{'high': 'search', 'low': 'recharge'}])
        lab = M.mdp_optimal(M.mdp_check({**ROBOT, 'gamma': 0.9, 'transitions': [{**t, 'next': {k: float(F(v)) for k, v in t['next'].items()}} for t in ROBOT['transitions']]}))
        for s in V: self.assertAlmostEqual(float(V[s]), lab[s], places=8)

    def test_bellman_expectation_identity(self):
        m = O.normalise(ROBOT); pi = {'high': 'wait', 'low': 'wait'}; V = O.evaluate(m, pi)
        self.assertEqual(V['high'], 10)
        for s in ('high', 'low'): self.assertEqual(V[s], O.q_value(m, V, s, pi[s]))

    def test_claims_and_wrong_claim(self):
        rep = O.audit({'r': ROBOT}, [{'claim_id': 'ok', 'model_id': 'r', 'quantity': 'VI_k', 'state': 'high', 'k': 1, 'value': 2},
                                     {'claim_id': 'bad', 'model_id': 'r', 'quantity': 'V_star', 'state': 'low', 'value': 14}])
        st = {c['claim_id']: c['status'] for c in rep['claims']}
        self.assertEqual(st, {'ok': 'PASS', 'bad': 'FAIL'}); self.assertEqual(rep['status'], 'FAIL')

    def test_boundaries_contraction_pi(self):
        rep = O.audit({'r': ROBOT}, [])
        r = rep['models']['r']
        self.assertEqual(rep['status'], 'PASS'); self.assertTrue(r['policy_iteration_reaches_optimum'])
        self.assertTrue(all(b['status'] == 'PASS' for b in r['boundary']))

    def test_rejects_bad_model(self):
        bad = {**ROBOT, 'transitions': ROBOT['transitions'][:1] + [{'s': 'high', 'a': 'wait', 'r': 1, 'next': {'high': '1/2'}}]}
        with self.assertRaises(O.OracleError): O.normalise(bad)
        with self.assertRaises(O.OracleError): O.normalise({**ROBOT, 'gamma': 1})

    def test_stage_checks_silent_without_models(self):
        self.assertEqual(O.stage_checks({'blocks': []}), ([], None))


if __name__ == '__main__':
    unittest.main()
