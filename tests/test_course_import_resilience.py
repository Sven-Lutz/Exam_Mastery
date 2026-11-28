"""Course import resilience (Codex review on PR #52, open P1 findings 4 and 5).

4. reimport publishes the new inventory before it saves the STALE marks. A run that stops in between must not make
   the next run compare new with new: the affected chapter has to be marked STALE on the retry.
5. Rendering PDF pages for authoring packets needs a pixel budget; DPI alone does not bound memory for oversized
   page boxes.
Synthetic sources only (tests/course_fixture.py); no real course material.
"""
import tempfile
import unittest
from pathlib import Path

from tests.course_fixture import _pdf, make_course


class InterruptedReimport(unittest.TestCase):
    def setUp(self):
        from exam_mastery.mastery import courses as C
        self.C = C
        self.tmp = tempfile.TemporaryDirectory(prefix="mastery-resilience-")
        self.src = make_course(Path(self.tmp.name) / "Kurs")
        self.home = Path(self.tmp.name) / "Mastery"
        quiet = lambda *_: None
        s = C.import_course(self.src, title="Entscheidungsprobleme", home=self.home, log=quiet)
        rel = "Vorlesung/00 - Einführung.pdf"
        fid = {f["rel_path"]: f["file_id"] for f in s["files"]}[rel]
        self.cid = next(c["id"] for c in s["chapters"] if fid in c.get("sources", []))
        C.make_packet(s["slug"], self.cid, self.home, log=quiet)
        self.slug = s["slug"]
        self.rel = rel

    def tearDown(self):
        self.tmp.cleanup()

    def test_stale_mark_survives_a_crash_between_inventory_and_save(self):
        quiet = lambda *_: None
        _pdf(self.src / self.rel, [("Einführung", ["Neue Fassung der Folien."], False)])
        original = self.C._save
        calls = []

        def crash(*a, **k):
            calls.append(1)
            raise RuntimeError("simulated stop after the new inventory was published")
        self.C._save = crash
        try:
            with self.assertRaises(RuntimeError):
                self.C.reimport(self.slug, self.home, log=quiet)
        finally:
            self.C._save = original
        self.assertEqual(calls, [1])
        baseline = self.home / "courses" / self.slug / "inventory" / "reimport-baseline.json"
        self.assertTrue(baseline.is_file())                     # the last completed baseline is kept
        r = self.C.reimport(self.slug, self.home, log=quiet)    # retry: must still see the change
        self.assertIn(self.rel, r["impact"]["changed_files"])
        self.assertIn(self.cid, r["impact"]["stale_chapters"])
        self.assertFalse(baseline.exists())                     # journal removed after the marks are saved
        again = self.C.reimport(self.slug, self.home, log=quiet)
        self.assertEqual(again["impact"]["changed_files"], [])  # a completed run leaves no phantom changes


class PagePixelBudget(unittest.TestCase):
    def test_oversized_page_is_rendered_within_budget(self):
        import pymupdf
        from exam_mastery.mastery import courses as C
        with tempfile.TemporaryDirectory() as td:
            doc = pymupdf.open()
            page = doc.new_page(width=14400, height=14400)       # largest page box the PDF format allows
            page.draw_rect(pymupdf.Rect(100, 100, 14000, 14000), color=(0, 0, 1))
            target = Path(td) / "p.png"
            self.assertTrue(C._render_page(page, target))
            pix = pymupdf.Pixmap(str(target))
            self.assertLessEqual(pix.width * pix.height, C.MAX_PAGE_PIXELS * 1.01)
            normal = doc.new_page(width=842, height=595)
            self.assertTrue(C._render_page(normal, Path(td) / "n.png"))
            pix = pymupdf.Pixmap(str(Path(td) / "n.png"))
            self.assertAlmostEqual(pix.width, 842 * C.PAGE_DPI / 72, delta=1)   # ordinary slides keep their resolution
            doc.close()


if __name__ == "__main__":
    unittest.main()
