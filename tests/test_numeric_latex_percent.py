"""LaTeX percent (\\%) must be read as a percent sign: '= 20\\,\\%' after 10500/52500 is correct, not 0.2 vs 20."""
import unittest
from exam_mastery.numeric_checks import equations


class LatexPercent(unittest.TestCase):
    def test_escaped_percent(self):
        for t in (r'\(\frac{10,500}{52,500} = 20\,\%\)', r'\(\frac{10,500}{52,500} = 20 \%\)', '10500/52500 = 20 %'):
            (_, _, val, ok), = equations(t)
            self.assertTrue(ok, t)

    def test_wrong_percent_still_fails(self):
        (_, _, _, ok), = equations(r'\(\frac{10,500}{52,500} = 25\,\%\)')
        self.assertFalse(ok)

    def test_plain_number_still_compared(self):
        (_, _, _, ok), = equations(r'\(\frac{10,500}{52,500} = 20\)')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()


class NoPartialNumbers(unittest.TestCase):
    """A stated value is never cut to a prefix by backtracking ('5.4+…' read as 5, '0.9999 (…)' as 0)."""
    def test_chain_checks_only_whole_numbers(self):
        r = equations(r'\(0.6 \cdot 9 + 0.1 \cdot 7 + 0.3 \cdot 11 = 5.4+0.7+3.3 = 9.4\)')
        self.assertTrue(r and all(ok for *_x, ok in r), r)
        self.assertNotIn('5', [st for _e, st, *_y in r])

    def test_parenthetical_after_value(self):
        r = equations(r'Summe \(0.8268+0.1731 = 0.9999\) (Rundungsrest).')
        self.assertTrue(all(ok for *_x, ok in r), r)
        self.assertNotIn('0', [st for _e, st, *_y in r])

    def test_real_error_still_found(self):
        r = equations(r'\(0.6 \cdot 9 + 0.1 \cdot 7 + 0.3 \cdot 11 = 9.9\)')
        self.assertEqual([ok for *_x, ok in r], [False])
