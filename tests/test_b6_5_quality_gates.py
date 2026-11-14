"""B6.5 independent machine checks: a solution must state the value it recomputes, and a block claimed as course
content may not introduce numbers its anchors do not contain. Offline, on the P3.1 reference chapters."""
import copy, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import test_p3_1_quality as T
from exam_mastery.quality_gates import quality_report, validate_gate_report, _states


def findings(q, gate):
    return [f for f in q['findings'] if f['gate_id'] == gate]


class IndependentChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t = T.Positive(); t.d = Path(tempfile.mkdtemp(prefix='b65q-'))
        cls.ref = {k: t.ref(k) for k in ('math', 'law', 'ml')}

    def test_reference_chapters_pass_both_gates(self):
        for kind, (a, c, plan, m) in self.ref.items():
            q = quality_report(a, c, plan, m)
            self.assertEqual(validate_gate_report(q), [])
            self.assertNotIn(q['gates']['G4.ANSWER_CONSISTENCY']['status'], ('FAIL', 'BLOCKED'), kind)
            self.assertNotIn(q['gates']['G5.SOURCE_NUMBERS']['status'], ('FAIL', 'BLOCKED'), kind)

    def test_answer_that_states_another_number_fails(self):
        a, c, plan, m = copy.deepcopy(self.ref['math'])
        s = next(s for s in a['solutions'] if s.get('numeric_checks'))
        s['answer'] = 'b = 2,5; a = 0,75'; s['steps'] = [{'statement': 'siehe oben', 'justification': '-'}]
        q = quality_report(a, c, plan, m)
        self.assertEqual(q['gates']['G4.ANSWER_CONSISTENCY']['status'], 'FAIL')
        self.assertEqual(q['machine_quality_status'], 'MACHINE_CHECKS_FAILED')
        self.assertEqual(validate_gate_report(q), [])

    def test_invented_number_in_course_definition_fails_but_instance_data_is_only_flagged(self):
        a, c, plan, m = copy.deepcopy(self.ref['math'])
        d = next(b for b in a['blocks'] if b.get('provenance') == 'COURSE_SOURCE' and b.get('kind') not in ('WORKED_EXAMPLE', 'SUBSUMPTION', 'CASE', 'COUNTEREXAMPLE'))
        d['body'] = str(d.get('body', '')) + ' Laut Vorlesung gilt dies in 87 % der Fälle.'
        q = quality_report(a, c, plan, m)
        f = [x for x in findings(q, 'G5.SOURCE_NUMBERS') if x['object_id'] == d['block_id']]
        self.assertEqual(f[0]['status'], 'FAIL'); self.assertIn('87', f[0]['reason'])
        self.assertEqual(q['machine_quality_status'], 'MACHINE_CHECKS_FAILED')
        a, c, plan, m = copy.deepcopy(self.ref['math'])
        ex = next((b for b in a['blocks'] if b.get('kind') == 'WORKED_EXAMPLE' and b.get('provenance') == 'COURSE_SOURCE'), None)
        if ex is not None:
            q = quality_report(a, c, plan, m)
            f = [x for x in findings(q, 'G5.SOURCE_NUMBERS') if x['object_id'] == ex['block_id']]
            self.assertIn(f[0]['status'], ('PASS', 'NOT_TESTED'))
            if f[0]['status'] == 'NOT_TESTED':
                self.assertIn('instance numbers', f[0]['reason'])

    def test_rounding_and_notation(self):
        self.assertTrue(_states('NNC = 44,467 €', 44466.6667))
        self.assertTrue(_states('Anteil 56,22 %', 56.221))
        self.assertFalse(_states('9.500 €', 9449.17))
        self.assertFalse(_states('keine Zahl', 3.0))


if __name__ == '__main__':
    unittest.main()
