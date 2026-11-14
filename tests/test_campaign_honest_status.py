"""Dashboard must never show a full pass while a gate is partial, a dimension untested, or findings are open."""
import json, tempfile, unittest
from pathlib import Path
from unittest import mock
from exam_mastery import campaign as C


class HonestStatus(unittest.TestCase):
    def card(self, dims, gate, findings):
        td = Path(tempfile.mkdtemp()); rv = td / 'r.json'
        rv.write_text(json.dumps({'verified': [1], 'findings': findings}))
        run = td / 'run'; run.mkdir()
        (run / 'quality_dossier.json').write_text(json.dumps({'chapters': {'c': {'dimensions': {k: {'status': v} for k, v in dims.items()}}}}))
        with mock.patch.object(C, 'latest_publication', return_value=(run, {}, {'gate': gate}, None)), \
             mock.patch.object(C, '_course_out', return_value=td):
            return C.course_card({'tag': 'T', 'name': 'n', 'folder': '/x', 'chapter_id': 'c', 'review': str(rv)}, str(td), {})

    def test_partial_gate_or_untested_is_not_full_pass(self):
        c = self.card({'rendering': 'PASS', 'math_numeric': 'NOT_TESTED'}, 'PARTIAL', [])
        self.assertTrue(c['status'].startswith('TEILWEISE'))
        self.assertEqual(c['dims_not_tested'], ['math_numeric'])

    def test_open_p2_counted(self):
        c = self.card({'rendering': 'PASS'}, 'READY', [{'id': 'a', 'severity': 'P2'}, {'id': 'b', 'severity': 'P1', 'resolved': 'E1'}])
        self.assertEqual((len(c['review']['open']), len(c['review']['open_all']), len(c['review']['resolved'])), (0, 1, 1))

    def test_open_p1_and_fail(self):
        self.assertEqual(self.card({'rendering': 'PASS'}, 'READY', [{'id': 'a', 'severity': 'P1'}])['status'], 'OFFENE P0/P1-FACHBEFUNDE')
        self.assertEqual(self.card({'rendering': 'FAIL'}, 'READY', [])['status'], 'FEHLER')
        self.assertTrue(self.card({'rendering': 'PASS'}, 'READY', [])['status'].startswith('TECHNISCH GEPRÜFT'))


if __name__ == '__main__':
    unittest.main()
