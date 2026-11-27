import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from exam_mastery.mastery import MasteryError, validate_state
from exam_mastery.mastery.server import Handler, _open_product


class HttpIntegrity(unittest.TestCase):
    def test_head_uses_file_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_bytes(b"page")
            handler = Mock(spec=Handler)
            handler.server = Mock(root=root)
            handler.wfile = Mock()
            handler._headers.side_effect = lambda *args: Handler._headers(handler, *args)
            handler.command = "HEAD"
            handler.path = "/"
            handler._host_ok.return_value = True
            with patch.object(Path, "read_bytes", side_effect=AssertionError("HEAD read file body")):
                Handler.do_GET(handler)
            handler.send_header.assert_any_call("Content-Length", "4")
            handler.wfile.write.assert_not_called()

    def test_malformed_archived_state_has_validation_error(self):
        practice = {"schema": 1, "units": {}, "archived": [1]}
        with self.assertRaises(MasteryError):
            validate_state({"schema": "mastery-state-v1", "saved_at": "now", "storage": {"em-practice-v1": practice}})

    def test_product_directories_must_be_real_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "products").mkdir()
            (root / "products" / "demo.css").touch()
            (root / "assets").symlink_to(root / "products", target_is_directory=True)
            with self.assertRaises(OSError), _open_product(root, Path("assets/demo.css")):
                self.fail("Linked directory accepted")
