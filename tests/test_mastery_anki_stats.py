"""Optional Anki statistics (standard §5.6, R8-POL-12): only from an export the learner makes, only after consent,
parsed in a temporary directory, only Mastery decks, labelled as scheduling data. Every collection here is a throwaway
collection created with the anki library in a temporary directory; no real Anki collection is touched."""
import base64
import json
import os
import tempfile
import unittest
from pathlib import Path

try:
    from anki.collection import Collection, DeckIdLimit, ExportAnkiPackageOptions
    HAVE_ANKI = True
except ImportError:  # pragma: no cover
    HAVE_ANKI = False

from exam_mastery.mastery import anki_stats as A


def _throwaway_exports(tmp):
    """Two Mastery cards (one reviewed twice, one lapse) and one card of another deck; exported three ways."""
    col = Collection(str(Path(tmp) / "throwaway.anki2"))
    try:
        mastery = col.decks.id("Exam Mastery::Attention")
        other = col.decks.id("Privat")
        basic = col.models.by_name("Basic")
        for i, did in enumerate((mastery, mastery, other)):
            note = col.new_note(basic)
            note["Front"], note["Back"] = f"<b>Frage {i}</b> zur&nbsp;Attention", "Antwort"
            col.add_note(note, did)
        col.decks.select(mastery)
        for ease in (3, 1):
            card = col.sched.getCard()
            col.sched.answerCard(card, ease)
        out = {}
        for legacy in (True, False):
            path = Path(tmp) / f"mastery-{'legacy' if legacy else 'modern'}.apkg"
            col.export_anki_package(out_path=str(path), options=ExportAnkiPackageOptions(
                with_scheduling=True, with_media=False, legacy=legacy), limit=DeckIdLimit(mastery))
            out["apkg_legacy" if legacy else "apkg_modern"] = path
        reviews = col.db.scalar("select count() from revlog")
        path = Path(tmp) / "all.colpkg"
        col.export_collection_package(out_path=str(path), include_media=False, legacy=True)   # closes the collection
        out["colpkg_legacy"] = path
    finally:
        if col.db:
            col.close()
    return out, reviews


@unittest.skipUnless(HAVE_ANKI, "anki not installed")
class ParseExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="throwaway-anki-")
        cls.files, cls.reviews = _throwaway_exports(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def check(self, stats, other_ignored):
        self.assertEqual(stats["schema"], A.SCHEMA)
        self.assertEqual(stats["label"], "Anki-Planungsdaten, kein Kompetenznachweis")
        self.assertEqual([d["name"] for d in stats["decks"]], ["Exam Mastery::Attention"])
        self.assertEqual(len(stats["cards"]), 2)
        self.assertEqual(stats["other_cards_ignored"], other_ignored)
        self.assertEqual(sum(c["reviews"] for c in stats["cards"]), self.reviews)
        self.assertEqual(stats["decks"][0]["reviews"], self.reviews)
        self.assertTrue(all(c["front"].startswith("Frage") and "<b>" not in c["front"] for c in stats["cards"]))
        self.assertNotIn("Privat", json.dumps(stats))
        self.assertIn("kein Kompetenznachweis", stats["label"])
        self.assertNotIn("%", json.dumps(stats, ensure_ascii=False))

    def test_legacy_deck_package(self):
        self.check(A.parse_export(self.files["apkg_legacy"].read_bytes(), "Mastery.apkg"), 0)

    def test_current_deck_package_via_throwaway_collection(self):
        stats = A.parse_export(self.files["apkg_modern"].read_bytes(), "Mastery.apkg")
        self.assertEqual(stats["file"]["collection"], "anki21b")
        self.check(stats, 0)

    def test_legacy_collection_package_reports_only_mastery_decks(self):
        self.check(A.parse_export(self.files["colpkg_legacy"].read_bytes(), "all.colpkg"), 1)

    def test_temporary_copy_is_removed(self):
        before = set(Path(tempfile.gettempdir()).glob("mastery-anki-stats-*"))
        A.parse_export(self.files["apkg_legacy"].read_bytes(), "Mastery.apkg")
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("mastery-anki-stats-*")), before)

    def test_rejects_other_files(self):
        for data, name in ((b"not a zip", "x.apkg"), (b"PK\x05\x06" + b"\0" * 18, "x.apkg"), (b"x", "notes.csv")):
            with self.assertRaises(A.AnkiStatsError):
                A.parse_export(data, name)


@unittest.skipUnless(HAVE_ANKI, "anki not installed")
class ServerPermission(unittest.TestCase):
    def test_endpoint_requires_consent_and_can_forget(self):
        from exam_mastery.mastery.server import start_in_thread
        from test_mastery_v1_app import _get
        with tempfile.TemporaryDirectory(prefix="mastery-home-") as tmp:
            files, _ = _throwaway_exports(tmp)
            home = Path(tmp) / "Mastery"
            home.mkdir()
            server, base = start_in_thread(home)
            try:
                payload = {"filename": "Mastery.apkg", "data_base64": base64.b64encode(files["apkg_legacy"].read_bytes()).decode()}
                status, _, body = _get(base, "/api/anki-stats", method="POST", body=json.dumps(payload).encode())
                self.assertEqual(status, 400)
                self.assertIn("Zustimmung", json.loads(body)["error"])
                self.assertFalse((home / "anki-stats").exists())
                status, _, body = _get(base, "/api/anki-stats", method="POST", body=json.dumps({**payload, "consent": True}).encode())
                self.assertEqual(status, 200, body)
                self.assertEqual(len(json.loads(body)["stats"]["cards"]), 2)
                self.assertEqual(_get(base, "/anki-stats/latest.json")[0], 404)              # never served as a file
                self.assertEqual(json.loads(_get(base, "/api/anki-stats")[2])["stats"]["schema"], A.SCHEMA)
                status, _, _ = _get(base, "/api/anki-stats", method="POST", body=json.dumps({**payload, "consent": True}).encode(),
                                    headers={"Origin": "http://evil.example"})
                self.assertEqual(status, 403)
                self.assertEqual(_get(base, "/api/anki-stats/forget", method="POST", body=b"{}")[0], 200)
                self.assertIsNone(json.loads(_get(base, "/api/anki-stats")[2])["stats"])
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
