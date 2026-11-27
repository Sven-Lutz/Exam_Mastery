"""Course-to-Mastery import end to end on a generated, public-safe lecture folder (tests/course_fixture.py):
import -> inventory -> completeness warnings (numbering gap, missing solution, unsupported, duplicate, iCloud placeholder
simulated through the flag check) -> chapter plan and user edits -> authoring packet -> build-chapter (registered in the
library, stable Anki identity) -> reimport with a changed source marks the chapter stale without touching learner state
or builds. Server guards for the import API and the wizard in a real browser (no external requests, no page errors)."""
import hashlib
import http.client
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from course_fixture import _pdf, make_course  # noqa: E402

CLOUD = "05 - Actor Critic.pdf"
try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:  # pragma: no cover
    HAVE_BROWSER = False


def _snapshot(root):
    out = {}
    for p in sorted(Path(root).rglob("*")):
        if p.is_file():
            st = p.stat()
            out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())
    return out


class _Cloud:
    """Simulates one iCloud placeholder: the flag check says 'dataless' until brctl (patched) downloads it."""

    def __init__(self, C):
        self.C, self.local, self.calls = C, False, []
        self.orig = (C.is_dataless, C._brctl_download)
        C.is_dataless = lambda p: Path(p).name == CLOUD and not self.local
        C._brctl_download = self.download

    def download(self, path):
        self.calls.append(Path(path).name)
        self.local = True

        class R:
            returncode = 0
            stderr = ""
        return R()

    def restore(self):
        self.C.is_dataless, self.C._brctl_download = self.orig


def _post(base, path, body, headers=None):
    host, port = base.split("//")[1].rstrip("/").split(":")
    conn = http.client.HTTPConnection(host, int(port), timeout=60)
    data = json.dumps(body).encode()
    conn.request("POST", path, data, {"Host": f"{host}:{port}", "Content-Type": "application/json", **(headers or {})})
    r = conn.getresponse()
    out = (r.status, json.loads(r.read() or b"{}"))
    conn.close()
    return out


class CourseImportPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import courses as C
        cls.C = C
        cls.tmp = tempfile.TemporaryDirectory(prefix="mastery-course-")
        cls.src = make_course(Path(cls.tmp.name) / "Kurs")
        cls.home = Path(cls.tmp.name) / "Mastery"
        cls.cloud = _Cloud(C)
        cls.before = _snapshot(cls.src)
        cls.summary = C.import_course(cls.src, title="Entscheidungsprobleme", home=cls.home, log=lambda *_: None)

    @classmethod
    def tearDownClass(cls):
        cls.cloud.restore()
        cls.tmp.cleanup()

    def files(self):
        return {f["rel_path"]: f for f in self.C.course_status("kurs", self.home)["files"]}

    def test_1_inventory_kinds_and_placeholder_not_opened(self):
        s, f = self.summary, self.files()
        self.assertEqual(s["slug"], "kurs")
        self.assertEqual(f["Vorlesung/00 - Einführung.pdf"]["kind"], "lecture_slides")
        self.assertEqual(f["Übungen/Blatt 01 - Markov Entscheidungsprozesse.pdf"]["kind"], "exercise")
        self.assertEqual(f["Lösungen/Lösung Blatt 01.pdf"]["kind"], "solution")
        self.assertEqual(f["Klausur/Klausur 2024.pdf"]["kind"], "exam")
        self.assertEqual(f["daten.xyz"]["status"], "unsupported")
        self.assertEqual(f[".DS_Store"]["status"], "ignored")
        self.assertEqual(f["Vorlesung/00 - Einführung.pdf"]["pages"], 3)
        self.assertGreaterEqual(f["Vorlesung/00 - Einführung.pdf"]["vision_pages"], 1)   # the bar-chart page
        cloud = f["Vorlesung/" + CLOUD]
        self.assertEqual((cloud["status"], cloud["local"], cloud["pages"]), ("not_local", False, None))
        self.assertIsNone(self.C.load_course("kurs", self.home)[1]["files"][[x["rel_path"] for x in self.C.load_course(
            "kurs", self.home)[1]["files"]].index("Vorlesung/" + CLOUD)]["sha256"])   # never read
        dup = [x for x in f.values() if x["duplicate_of"]]
        self.assertEqual([x["rel_path"] for x in dup], ["04 - Policy Gradient.pdf"])     # the loose copy, not Vorlesung/
        self.assertEqual(_snapshot(self.src), self.before)                               # source folder untouched

    def test_2_completeness_warnings_with_provenance(self):
        warns = self.C.course_status("kurs", self.home)["warnings"]
        codes = [w["code"] for w in warns]
        gap = [w for w in warns if w["code"] == "LECTURE_GAP"]
        self.assertEqual(len(gap), 1)
        self.assertIn("Vorlesung 03 fehlt", gap[0]["message"])
        missing = [w for w in warns if w["code"] == "EXERCISE_WITHOUT_SOLUTION"]
        self.assertEqual([w["provenance"][0]["rel_path"] for w in missing], ["Übungen/Blatt 02 - Dynamische Programmierung.pdf"])
        for code in ("UNSUPPORTED", "DUPLICATE", "NOT_LOCAL", "CHAPTER_WITHOUT_EXERCISE"):
            self.assertIn(code, codes)

    def test_3_chapter_and_competency_proposal_and_edits(self):
        s = self.C.course_status("kurs", self.home)
        ids = [c["id"] for c in s["chapters"]]
        self.assertEqual(ids, ["00-einfuehrung", "01-markov-entscheidungsprozesse", "02-dynamische-programmierung",
                               "04-policy-gradient", "05-actor-critic"])
        ch = {c["id"]: c for c in s["chapters"]}
        self.assertEqual(len(ch["01-markov-entscheidungsprozesse"]["exercises"]), 1)
        self.assertEqual(len(ch["01-markov-entscheidungsprozesse"]["solutions"]), 1)
        self.assertEqual(len(ch["04-policy-gradient"]["exams"]), 1)
        goals = ch["00-einfuehrung"]["competencies_proposed"]
        self.assertEqual([g["basis"] for g in goals], ["Lernziel-Folie"] * 3)
        self.assertEqual({g["label"] for g in goals}, {"Vorschlag"})
        self.assertEqual(goals[0]["provenance"][0]["page"], 2)
        self.assertTrue(all(c["status"] == "NICHT_ERARBEITET" for c in s["chapters"]))
        s = self.C.set_overrides("kurs", {"chapters": {"02-dynamische-programmierung": {"title": "Dynamische Programmierung (DP)"},
                                                       "05-actor-critic": {"skip": True}}}, self.home)
        s = self.C.plan("kurs", self.home)                                   # re-plan keeps the user's edits
        ch = {c["id"]: c for c in s["chapters"]}
        self.assertEqual(ch["02-dynamische-programmierung"]["title"], "Dynamische Programmierung (DP)")
        self.assertTrue(ch["05-actor-critic"]["skip"])
        with self.assertRaises(self.C.MasteryError):
            self.C.set_overrides("kurs", {"chapters": {"nope": {"skip": True}}}, self.home)

    def test_4_packet_contract(self):
        r = self.C.make_packet("kurs", "04-policy-gradient", self.home, log=lambda *_: None)
        chdir = self.home / "courses/kurs/chapters/04-policy-gradient"
        p = json.loads((chdir / "packet.json").read_text(encoding="utf-8"))
        self.assertEqual(p["schema"], "mastery-authoring-packet-v1")
        self.assertEqual(p["chapter"]["unit_id"], "course/kurs/04-policy-gradient")
        self.assertEqual(p["target_schema"], "em-experience-v1")
        lecture = p["sources"][0]
        self.assertEqual((lecture["rel_path"], lecture["kind"]), ("Vorlesung/04 - Policy Gradient.pdf", "lecture_slides"))
        self.assertTrue(all(pg["text"] for pg in lecture["pages"]))
        imgs = [pg["image"] for pg in lecture["pages"] if pg.get("image")]
        self.assertEqual(len(imgs), 1)
        self.assertTrue((chdir / imgs[0]).is_file())
        self.assertEqual(len(p["related"]["exams"]), 1)
        self.assertEqual(p["related"]["prerequisite_chapters"], ["02-dynamische-programmierung"])
        self.assertTrue(any("Keine Übung" in w for w in p["coverage_warnings"]))
        self.assertFalse(p["authoring"]["offline"])
        self.assertEqual(r["page_images"], 1)
        st = {c["id"]: c for c in self.C.course_status("kurs", self.home)["chapters"]}["04-policy-gradient"]
        self.assertEqual(st["status"], "PAKET_BEREIT")
        self.assertIn("Claude-Code-Sitzung", st["instruction"]["statement"])
        # a packet written by someone else is never overwritten
        other = self.home / "courses/kurs/chapters/01-markov-entscheidungsprozesse"
        other.mkdir(parents=True)
        (other / "packet.json").write_text('{"schema": "mastery-authoring-packet-v1", "by": "hand"}', encoding="utf-8")
        self.C.make_packet("kurs", "01-markov-entscheidungsprozesse", self.home, log=lambda *_: None)
        self.assertEqual(json.loads((other / "packet.json").read_text())["by"], "hand")
        self.assertTrue((other / "packet.import.json").is_file())
        self.assertEqual(_snapshot(self.src), self.before)

    def test_5_build_chapter_registers_and_keeps_identity_then_reimport_marks_stale(self):
        from exam_mastery.mastery.server import ALLOWED
        chdir = self.home / "courses/kurs/chapters/04-policy-gradient"
        unit = json.loads((REPO / "fixtures/experience_reference.json").read_text(encoding="utf-8"))
        unit["unit_id"] = "course/kurs/04-policy-gradient"
        (chdir / "unit.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
        (chdir / "authoring.json").write_text(json.dumps({"schema": "mastery-authoring-record-v1",
                                                          "author": {"kind": "human"}}), encoding="utf-8")
        st = {c["id"]: c for c in self.C.course_status("kurs", self.home)["chapters"]}["04-policy-gradient"]
        self.assertEqual((st["status"], st["author_label"]), ("ERARBEITET", "Mensch"))
        r = self.C.build_chapter("kurs", "04-policy-gradient", self.home, log=lambda *_: None)
        self.assertEqual(r["built"], ["kurs-04-policy-gradient"])
        lib = json.loads((self.home / "library.json").read_text(encoding="utf-8"))
        u = next(x for x in lib["units"] if x["slug"] == "kurs-04-policy-gradient")
        self.assertEqual(u["course"]["slug"], "kurs")
        self.assertEqual(u["products"]["textbook"], "courses/kurs/chapters/04-policy-gradient/build/Lehrbuch.pdf")
        self.assertNotIn(str(self.src), json.dumps(lib))
        for rel in u["products"].values():
            self.assertTrue((self.home / rel).is_file())
            self.assertIsNotNone(ALLOWED.match("/" + rel))
        spec = json.loads((self.home / "library-spec.local.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["units"][0]["out"], "courses/kurs/chapters/04-policy-gradient/build")
        st = {c["id"]: c for c in self.C.course_status("kurs", self.home)["chapters"]}["04-policy-gradient"]
        self.assertEqual(st["status"], "PRÜFUNG_AUSSTEHEND")
        build = chdir / "build"
        products = {p: hashlib.sha256((build / p).read_bytes()).hexdigest() for p in ("Lehrbuch.pdf", "Anki.apkg")}
        anki_state = sorted(x.name for x in (build / ".em-state").iterdir())
        again = self.C.build_chapter("kurs", "04-policy-gradient", self.home, log=lambda *_: None)
        self.assertEqual(again["built"], [])                                  # unchanged: nothing rebuilt
        changed_id = dict(unit, unit_id="course/kurs/other")
        (chdir / "unit.json").write_text(json.dumps(changed_id, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(self.C.MasteryError):                          # Anki identity must stay stable
            self.C.build_chapter("kurs", "04-policy-gradient", self.home, log=lambda *_: None)
        (chdir / "unit.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
        # learner state and builds must survive a source change
        state = self.home / "state" / "latest.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text('{"schema": "mastery-state-v1", "storage": {}}', encoding="utf-8")
        state_before = state.read_bytes()
        unit_before = (chdir / "unit.json").read_bytes()
        _pdf(self.src / "Vorlesung/04 - Policy Gradient.pdf", [("Policy Gradient", ["Neue Fassung."], False),
                                                              ("Natürlicher Gradient", ["Fisher-Information."], False)])
        r = self.C.reimport("kurs", self.home, log=lambda *_: None)
        self.assertIn("Vorlesung/04 - Policy Gradient.pdf", r["impact"]["changed_files"])
        self.assertIn("04-policy-gradient", r["impact"]["stale_chapters"])
        st = {c["id"]: c for c in r["chapters"]}["04-policy-gradient"]
        self.assertTrue(st["stale"])
        self.assertEqual(state.read_bytes(), state_before)
        self.assertEqual((chdir / "unit.json").read_bytes(), unit_before)
        self.assertEqual({p: hashlib.sha256((build / p).read_bytes()).hexdigest() for p in products}, products)
        self.assertEqual(sorted(x.name for x in (build / ".em-state").iterdir()), anki_state)
        self.assertTrue((self.home / "courses/kurs/inventory/impact.json").is_file())
        self.before = _snapshot(self.src)

    def test_6_icloud_placeholder_only_with_consent(self):
        self.assertEqual(self.cloud.calls, [])                                 # nothing downloaded so far
        s = self.C.reimport("kurs", self.home, materialize_files=True, log=lambda *_: None)
        self.assertEqual(self.cloud.calls, [CLOUD])
        f = {x["rel_path"]: x for x in s["files"]}["Vorlesung/" + CLOUD]
        self.assertEqual((f["status"], f["pages"]), ("ok", 1))
        self.assertEqual(s["counts"]["not_local"], 0)

    def test_7_cli(self):
        import subprocess
        run = subprocess.run([sys.executable, "-m", "exam_mastery.mastery", "--home", str(self.home), "course", "kurs"],
                             cwd=REPO, capture_output=True, text=True, timeout=120, env={**os.environ, "PYTHONPATH": str(REPO)})
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Vorlesung 03 fehlt", run.stdout)
        self.assertIn("04-policy-gradient", run.stdout)


class SourceRootGuards(unittest.TestCase):
    def test_refuses_repository_library_home_and_relative_paths(self):
        from exam_mastery.mastery import MasteryError
        from exam_mastery.mastery.courses import check_source_root
        with tempfile.TemporaryDirectory(prefix="mastery-guard-") as tmp:
            home = Path(tmp) / "Mastery"
            (home / "x").mkdir(parents=True)
            ok = Path(tmp) / "Kurs"
            ok.mkdir()
            self.assertEqual(check_source_root(ok, home), ok.resolve())
            for bad in (REPO, REPO / "fixtures", home, home / "x", Path(tmp)):
                with self.assertRaises(MasteryError, msg=str(bad)):
                    check_source_root(bad, home)
            with self.assertRaises(MasteryError):
                check_source_root("Kurs", home, base=tmp)                    # relative path from the server
            with self.assertRaises(MasteryError):
                check_source_root(ok, home, base=Path(tmp) / "elsewhere")    # outside the allowed base


class ImportServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import build
        from exam_mastery.mastery import courses as C
        from exam_mastery.mastery.server import start_in_thread
        cls.C = C
        cls.tmp = tempfile.TemporaryDirectory(prefix="mastery-wizard-")
        cls.base_dir = Path(cls.tmp.name)
        cls.src = make_course(cls.base_dir / "Kurs")
        cls.home = cls.base_dir / "Mastery"
        build(cls.home, only="-", log=lambda *_: None)                          # shell + empty library, fast
        cls.cloud = _Cloud(C)
        cls.server, cls.base = start_in_thread(cls.home, import_base=cls.base_dir)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.cloud.restore()
        cls.tmp.cleanup()

    def test_import_api_guards(self):
        before = _snapshot(self.src)
        self.assertEqual(_post(self.base, "/api/import", {"path": "/etc"})[0], 400)              # outside home/base
        self.assertEqual(_post(self.base, "/api/import", {"path": "Kurs"})[0], 400)              # relative
        self.assertEqual(_post(self.base, "/api/import", {"path": str(self.src), "x": 1})[0], 400)
        self.assertEqual(_post(self.base, "/api/import", {"path": str(self.src)}, {"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(_post(self.base, "/api/courses/kurs/materialize", {})[0], 400)          # no consent, no course
        self.server.import_base = REPO.parent
        try:
            code, body = _post(self.base, "/api/import", {"path": str(REPO / "fixtures")})
            self.assertEqual(code, 400)
            self.assertIn("Repository", body["error"])
        finally:
            self.server.import_base = self.base_dir
        self.assertFalse((self.home / "courses" / "fixtures").exists())
        self.assertEqual(_snapshot(self.src), before)

    @unittest.skipUnless(HAVE_BROWSER, "playwright not installed")
    def test_wizard_end_to_end(self):
        base, errors, external = self.base, [], []
        before = _snapshot(self.src)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                pg = browser.new_page()
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "400" not in m.text else None)
                pg.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)
                pg.goto(base + "#kurse")
                pg.wait_for_selector('#app[data-ready="1"]')
                self.assertTrue(pg.is_visible("#no-courses"))
                pg.fill("#import-path", "relativ/pfad")
                pg.click("#import-run")
                pg.wait_for_selector('#import-status[data-state="error"]')
                pg.fill("#import-path", str(self.src))
                pg.fill("#import-title", "Entscheidungsprobleme")
                pg.click("#import-run")
                card = '[data-course="kurs"].m-course'
                pg.wait_for_selector(card, timeout=60000)
                self.assertIn("Vorlesung 03 fehlt", pg.inner_text(card))
                self.assertTrue(pg.is_visible('[data-not-local="1"]'))           # iCloud placeholder shown, not read
                self.assertEqual(pg.get_attribute('tr[data-file="Vorlesung/%s"]' % CLOUD, "data-status"), "not_local")
                self.assertEqual(self.cloud.calls, [])
                pg.click("#materialize-kurs")                                       # explicit consent
                pg.wait_for_selector('[data-not-local]', state="detached", timeout=60000)
                self.assertEqual(self.cloud.calls, [CLOUD])
                row = 'tr[data-chapter="04-policy-gradient"]'
                self.assertEqual(pg.get_attribute(row, "data-status"), "NICHT_ERARBEITET")
                pg.click(row + ' [data-action="packet"]')
                pg.wait_for_selector(row + '[data-status="PAKET_BEREIT"]', timeout=60000)
                instr = pg.inner_text(row + " [data-instruction]")
                self.assertIn("Claude-Code-Sitzung", instr)
                self.assertIn("nicht offline", instr)
                self.assertIn("build-chapter kurs 04-policy-gradient", instr)
                # plan edit through the safe POST
                pg.fill('tr[data-chapter="02-dynamische-programmierung"] [data-field="title"]', "DP und Bellman")
                pg.click("#plan-save-kurs")
                pg.wait_for_function("document.querySelector('tr[data-chapter=\"02-dynamische-programmierung\"] [data-field=\"title\"]').value === 'DP und Bellman'")
                # authoring happens outside Mastery (here: a human writes the unit), then build in the wizard
                chdir = self.home / "courses/kurs/chapters/04-policy-gradient"
                unit = json.loads((REPO / "fixtures/experience_reference.json").read_text(encoding="utf-8"))
                unit["unit_id"] = "course/kurs/04-policy-gradient"
                (chdir / "unit.json").write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
                (chdir / "authoring.json").write_text(json.dumps({"schema": "mastery-authoring-record-v1",
                                                                  "author": {"kind": "human"}}), encoding="utf-8")
                pg.reload()
                pg.wait_for_selector(row + '[data-status="ERARBEITET"]')
                pg.click(row + ' [data-action="build"]')
                pg.wait_for_selector(row + '[data-status="PRÜFUNG_AUSSTEHEND"]', timeout=120000)
                href = pg.get_attribute(row + ' a[data-product="textbook"]', "href")
                self.assertEqual(href, "courses/kurs/chapters/04-policy-gradient/build/Lehrbuch.pdf")
                pg.goto(base + "#start")
                pg.wait_for_selector('#app[data-ready="1"]')
                self.assertIn("Kurs: Entscheidungsprobleme", pg.inner_text("#start"))
                unit_card = '[data-unit="kurs-04-policy-gradient"]'
                for k in ("textbook", "workbook", "anki", "interactive"):
                    link = pg.get_attribute(f'{unit_card} a[data-product="{k}"]', "href")
                    self.assertEqual(pg.request.get(base + link).status, 200, link)
            finally:
                browser.close()
        self.assertEqual(errors, [])
        self.assertEqual(external, [])
        self.assertEqual(_snapshot(self.src), before)


if __name__ == "__main__":
    unittest.main()
