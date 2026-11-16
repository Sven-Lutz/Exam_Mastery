"""B33: nested Bellman backups are checked as whole computations, not as extracted sub-expressions."""
import unittest

from exam_mastery.numeric_checks import equations


class BellmanParser(unittest.TestCase):
    def test_nested_backup_whole_expression(self):
        r = equations('\\(2 + 0.9\\,(0.7 \\cdot 0 + 0.3 \\cdot 0) = 2\\)')
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][0], '2 + 0.9*(0.7 * 0 + 0.3 * 0)')
        self.assertTrue(r[0][3])

    def test_negative_reward_backup(self):
        self.assertTrue(equations('-2 + 0.9 (0.4 * 2 + 0.6 * 0.5) = -1.01')[0][3])

    def test_wrong_backup_still_fails(self):
        r = equations('2 + 0.9 (0.7 * 3.26 + 0.3 * 1.8) = 4.62')
        self.assertFalse(r[0][3])

    def test_real_error_after_word_not_hidden(self):
        r = equations('Summe 3 + 4 = 8')
        self.assertEqual(len(r), 1)
        self.assertFalse(r[0][3])

    def test_symbolic_fragment_skipped(self):
        self.assertEqual(equations('V(H)(0.7*2) = 1.4'), [])


if __name__ == '__main__':
    unittest.main()
