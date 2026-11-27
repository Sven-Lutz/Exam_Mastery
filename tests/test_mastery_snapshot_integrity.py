import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from exam_mastery import mastery


class SnapshotIntegrity(unittest.TestCase):
    def test_same_second_rotation_and_export(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mastery, "now", return_value="2026-11-27T12:00:00Z"):
            root = Path(tmp)
            exports = []
            for i in range(3):
                snapshot = {"schema": mastery.STATE_SCHEMA, "saved_at": str(i), "storage": {}}
                mastery.store_state(root, snapshot, keep=2)
                exports.append(mastery.export(root))
            history = sorted((root / "state/history").glob("state-*.json"))
            self.assertEqual([json.loads(p.read_text())["saved_at"] for p in history], ["1", "2"])
            self.assertEqual([json.loads(p.read_text())["state"]["saved_at"] for p in exports], ["0", "1", "2"])

    def test_private_destinations_outside_engine_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for marker in ("directory", "file"):
                repo = root / marker
                repo.mkdir()
                git = repo / ".git"
                git.mkdir() if marker == "directory" else git.touch()
                with self.assertRaises(mastery.MasteryError):
                    mastery.resolve_home(repo / "data")
                with self.assertRaises(mastery.MasteryError):
                    mastery._guard_output(repo / "backup.json")

    def test_archive_failure_preserves_previous_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = {"schema": mastery.STATE_SCHEMA, "saved_at": "first", "storage": {}}
            mastery.store_state(root, snapshot)
            latest = root / "state/latest.json"
            prior = latest.read_bytes()
            write = mastery._write_json

            def fail_history(path, record):
                if path.parent.name == "history":
                    raise OSError("simulated storage failure")
                write(path, record)

            with patch.object(mastery, "_write_json", side_effect=fail_history), self.assertRaises(OSError):
                mastery.store_state(root, dict(snapshot, saved_at="second"))
            self.assertEqual(prior, latest.read_bytes())
