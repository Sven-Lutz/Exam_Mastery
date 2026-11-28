import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from course_fixture import _pdf
from exam_mastery.mastery import courses as C


class PacketBudget(unittest.TestCase):
    def test_shared_budget_and_rebuild(self):
        with tempfile.TemporaryDirectory() as td, patch.multiple(C, MAX_COURSE_IMAGES=2, MAX_PACKET_IMAGES=1,
                                                                    MAX_PAGE_PIXELS=20000):
            root = Path(td)
            for i in [1, 2, 3]:
                _pdf(root / "Kurs" / "Vorlesung" / f"0{i} - Thema{i}.pdf",
                     [(f"Thema{i}", ["x_1 = y + z", "s_1 = t + u", "a = b + c"], True)] * 5)
            home = root / "Home"
            status = C.import_course(root / "Kurs", home=home, log=lambda *_: None)
            chapters = [ch["id"] for ch in status["chapters"]]
            def packet(cid):
                return C.make_packet("kurs", cid, home, log=lambda *_: None)
            self.assertEqual([packet(cid)["page_images"] for cid in chapters], [1, 1, 0])
            self.assertEqual(packet(chapters[0])["page_images"], 1)
            with patch.object(C, "MAX_PACKET_PIXELS", 1):
                self.assertEqual(packet(chapters[0])["page_images"], 0)
            with patch.object(C, "MAX_COURSE_PIXELS", 1):
                result = packet(chapters[0])
                self.assertEqual(result["page_images"], 0)
                self.assertEqual(result["pages_text"], 5)
                self.assertTrue(any("Budget" in w or "budget" in w for w in result["warnings"]))
            self.assertIn("RENDER_BUDGET", {w["code"] for w in C.course_status("kurs", home)["warnings"]})
