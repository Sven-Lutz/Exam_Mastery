"""The per-chapter decimal separator of labs must not leak into later labs in the same process."""
import tempfile, unittest
from exam_mastery.labs import build as B, integrate as I


class DecimalScope(unittest.TestCase):
    def test_separator_restored_after_chapter(self):
        before = B.DECIMAL['sep']
        I.build_chapter_labs([], tempfile.mkdtemp(), 'Kurs', lambda refs: '', [], decimal='.')
        self.assertEqual(B.DECIMAL['sep'], before)

    def test_restored_even_on_error(self):
        before = B.DECIMAL['sep']
        with self.assertRaises(Exception):
            I.build_chapter_labs(None and [] or [{'lab_id': 'x'}], None, 'Kurs', None, [], decimal='.')
        self.assertEqual(B.DECIMAL['sep'], before)


if __name__ == '__main__':
    unittest.main()
