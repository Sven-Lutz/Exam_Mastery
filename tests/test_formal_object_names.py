"""Numbered formal objects get distinct competency names (ANA1: 'Lemma: 2' buckets)."""
import unittest
from exam_mastery.curriculum import _formal_name, FORMAL_HEAD


def name(t):
    fm = FORMAL_HEAD.match(t); return f"{fm.group(1)}: {_formal_name(fm.group(3).strip(), fm.group(2))}"


class FormalNames(unittest.TestCase):
    def test_numbered(self):
        self.assertEqual(name('Lemma 2.29. Seien (an)n eine beschränkte reelle Folge und ε > 0. Dann existiert'),
                         'Lemma: 2.29 Seien (an)n eine beschränkte reelle Folge und ε > 0')
        self.assertNotEqual(name('Satz 2.4. Die Folge strebe gegen a.'), name('Satz 2.10. Es seien reelle Folgen.'))
        self.assertEqual(name('Definition 2.1. Eine Folge ist eine Abbildung'), 'Definition: 2.1 Eine Folge ist eine Abbildung')

    def test_unnumbered_unchanged(self):
        self.assertEqual(name('Satz (Bolzano-Weierstraß). Jede beschränkte Folge'), 'Satz: Bolzano-Weierstraß')
        self.assertEqual(name('Definition: Markov-Entscheidungsprozess'), 'Definition: Markov-Entscheidungsprozess')


if __name__ == '__main__':
    unittest.main()
