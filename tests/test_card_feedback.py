import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from anki.collection import Collection, ImportAnkiPackageRequest
from playwright.sync_api import sync_playwright
from course_fixture import _pdf
from test_course_import import _post
from exam_mastery.mastery import MasteryError, courses, export
from exam_mastery.mastery.card_feedback import record
from exam_mastery.mastery.server import start_in_thread

REPO = Path(__file__).resolve().parents[1]


class CardFeedback(unittest.TestCase):
    def test_invalid_feedback_rejected_before_storage(self):
        valid = {"key": "a/b", "package": "0" * 64, "ordinal": 0, "kind": "unklar", "text": ""}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for bad in ({"text": "x" * 2001}, {"kind": "unknown"}, {"ordinal": True}, {"extra": 1}):
                with self.subTest(fields=list(bad)), self.assertRaises(MasteryError):
                    record(root, "kurs", "kapitel", {**valid, **bad})
            self.assertEqual(list(root.iterdir()), [])

    def test_review_feedback_revise_reimport(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            home = root / "Mastery"
            _pdf(root / "Kurs/Vorlesung/01 - Suche.pdf", [("Suche", ["Suchverfahren"], False)])
            course = courses.import_course(root / "Kurs", home=home)
            cid = course["chapters"][0]["id"]
            chapter = home / "courses/kurs/chapters" / cid
            courses.make_packet("kurs", cid, home)
            unit = json.loads((REPO / "fixtures/experience_binomial_reference.json").read_text())
            unit["unit_id"] = "course/kurs/" + cid
            first = unit["cards"][0]
            first["context"] = r"Sortiertes Feld mit \(n\) Einträgen."
            graphic = unit["graphics"][0]
            first["figure"] = graphic["id"] + "-state-" + str(graphic["keyframes"][0])
            unit_path = chapter / "unit.json"
            unit_path.write_text(json.dumps(unit))
            courses.build_chapter("kurs", cid, home)
            package = chapter / "build/Anki.apkg"
            learner = Collection(str(root / "test.anki2"))
            self.addCleanup(learner.close)
            def reimport():
                learner.import_anki_package(ImportAnkiPackageRequest(package_path=str(package)))
            reimport()
            note = next(learner.get_note(n) for n in learner.find_notes("") if learner.get_note(n)["Key"] == first["key"])
            card = note.cards()[0]
            learner.db.execute("update cards set ivl=14 where id=?", card.id)
            learner.db.execute("insert into revlog values (?, ?, -1, 3, 14, 4, 2500, 6000, 1)", 1000000, card.id)
            server, base = start_in_thread(home)
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch()
                    page = browser.new_page()
                    errors, external = [], []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:")) else None)
                    page.goto(base + "#kurse")
                    page.get_by_text("Anki-Karten und Feedback", exact=True).first.click()
                    page.locator("#card").select_option(label=first["key"] + " · Karte 1")
                    frame = page.frame_locator("iframe")
                    frame.locator(".em-ctx mjx-container").first.wait_for(timeout=15000)
                    page.select_option("#side", "a")
                    frame.locator(".em-a").wait_for()
                    figure = frame.locator("img").first
                    figure.wait_for()
                    self.assertTrue(figure.evaluate("(img) => img.decode().then(() => img.naturalWidth > 0)"))
                    page.select_option("#kind", "Kontext fehlt")
                    page.fill("#text", "Bitte die Randbedingung ergänzen.")
                    page.get_by_role("button", name="Feedback speichern").click()
                    page.get_by_text("Feedback lokal gespeichert.").wait_for()
                    page.reload()
                    page.locator("#affected li").first.wait_for()
                    self.assertIn(first["key"], page.locator("#affected").inner_text())
                    self.assertEqual((errors, external), ([], []))
                    browser.close()
                endpoint = f"/api/courses/kurs/chapters/{cid}/feedback"
                self.assertEqual(_post(base, endpoint, {}, {"Origin": "https://example.invalid"})[0], 403)
                self.assertEqual(_post(base, endpoint, {"text": "x"*65000})[0], 413)
                self.assertEqual(_post(base, endpoint, {})[0], 400)
            finally:
                server.shutdown()
                server.server_close()
            subprocess.run([sys.executable, "-m", "exam_mastery.mastery", "--home", str(home), "card-feedback",
                            "kurs", cid], check=True)
            report = json.loads((chapter / "feedback.json").read_text())
            self.assertEqual(report["counts"]["Kontext fehlt"], 1)
            self.assertEqual(json.loads(export(home).read_text())["card_feedback"][0]["events"], report["events"])
            first["context"] += " Voraussetzung: aufsteigende Sortierung."
            unit_path.write_text(json.dumps(unit))
            changed = courses.build_chapter("kurs", cid, home)
            self.assertEqual(changed["anki"]["restamped_keys"], [first["key"]])
            reimport()
            self.assertEqual(learner.get_note(note.id).guid, note.guid)
            self.assertIn("Voraussetzung", learner.get_note(note.id)["Context"])
            self.assertEqual(learner.get_note(note.id).cards()[0].id, card.id)
            self.assertEqual(learner.get_card(card.id).ivl, 14)
            self.assertEqual(learner.db.scalar("select count(*) from revlog where cid=?", card.id), 1)
