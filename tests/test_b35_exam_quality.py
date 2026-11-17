"""B35 exam timing audit: calibration status always printed, distributed minutes and overload detected."""
import json, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery import exam_quality as X

V4 = Path.home() / 'Exam_Mastery_Output/course-a8fba2d65467/ch-20261117T120000Z-v4/chapters/ch-271642018f0467/publish/book.json'


def item(no, minutes, points, words=20, formulas=2):
    return {'no': no, 'minutes': minutes, 'points': points, 'prompt': 'Berechnen Sie den Wert.',
            'solution': {'steps': [['\\(x=1\\)', ' '.join(['Wort'] * words)]] + [['\\(y=2\\)', '']] * formulas, 'answer': 'x', 'rubric': [['a', points]]}}


class Timing(unittest.TestCase):
    def test_header_states_calibration(self):
        self.assertIn('nicht kalibriert', X.header_time({'minutes': 60}))
        self.assertIn('nicht gemessen', X.header_time({'minutes': 60, 'calibration': {'status': 'MODEL_ESTIMATE'}}))
        self.assertEqual(X.header_time({}), 'keine Vorgabe')

    def test_empirical_needs_sample(self):
        r = X.audit_exam({'minutes': 30, 'calibration': {'status': 'EMPIRICAL'}, 'items': [item('1', 30, 10)]})
        self.assertIn('X1', {f['code'] for f in r['findings']})

    def test_outlier_and_distribution(self):
        ex = {'minutes': 30, 'items': [item('1', 10, 10), item('2', 10, 10), item('3', 10, 10, words=400, formulas=30)]}
        codes = {(f['code'], f.get('item')) for f in X.audit_exam(ex)['findings']}
        self.assertIn(('X2', None), codes); self.assertIn(('X3', '3'), codes)

    def test_missing_rubric_fails(self):
        it = item('1', 10, 5); it['solution']['rubric'] = []
        self.assertIn('X5', {f['code'] for f in X.audit_exam({'items': [it]})['findings']})

    @unittest.skipUnless(V4.exists(), 'V4 build not present')
    def test_v4_exams_flagged(self):
        for e in json.loads(V4.read_text())['exams']:
            codes = {f['code'] for f in X.audit_exam(e)['findings']}
            self.assertTrue({'X2', 'X6'} <= codes, (e['label'], codes))


if __name__ == '__main__':
    unittest.main()
