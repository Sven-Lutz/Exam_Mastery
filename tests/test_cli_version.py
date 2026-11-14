"""`exam-mastery --version` prints the version instead of treating the flag as a lecture folder."""
import contextlib, io, json, unittest
from exam_mastery import runtime, cli


class Version(unittest.TestCase):
    def run_main(self, main, arg):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main([arg])
        return rc, json.loads(buf.getvalue())

    def test_both_entry_points(self):
        for main in (runtime.main, cli.main):
            for arg in ('--version', '-V', 'version'):
                rc, d = self.run_main(main, arg)
                self.assertEqual(rc, 0); self.assertIn('engine', d); self.assertNotIn('error', d)


if __name__ == '__main__':
    unittest.main()
