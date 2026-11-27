"""Mastery V1 local app, end to end: build into a temporary MASTERY_HOME, serve in-process on a free port, drive it
with a real browser. Covers the daily flow (home, products, practice diagnosis, hints = assisted, tutor brief without
evidence keys, persistence across reloads, progress vocabulary), the server's guards, the repository refusal and the
Anki round trip (throwaway collection; unchanged rebuild restamps nothing)."""
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UNIT = REPO / "fixtures" / "experience_attention_reference.json"

try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:  # pragma: no cover
    HAVE_BROWSER = False
try:
    import anki  # noqa: F401
    HAVE_ANKI = True
except ImportError:  # pragma: no cover
    HAVE_ANKI = False


def _get(base, path, headers=None, method="GET", body=None):
    host, port = base.split("//")[1].rstrip("/").split(":")
    conn = http.client.HTTPConnection(host, int(port), timeout=10)
    conn.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
    hdrs = {"Host": f"{host}:{port}", **(headers or {})}
    if body is not None:
        hdrs.setdefault("Content-Type", "application/json")
        hdrs.setdefault("Content-Length", str(len(body)))
    for k, v in hdrs.items():
        conn.putheader(k, v)
    conn.endheaders(body)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, response.getheader("Content-Type"), data


class StaticContract(unittest.TestCase):
    def test_r9_protocol_header_is_the_contract_copy_template(self):
        doc = (REPO / "docs/research/workstreams/TUTOR_BEHAVIORAL_CONTRACT.md").read_text(encoding="utf-8")
        block = doc.split("## 9. Kopiervorlage", 1)[1].split("```text\n", 1)[1].split("\n```", 1)[0]
        js = (REPO / "exam_mastery/templates/em_tutor.js").read_text(encoding="utf-8")
        self.assertIn("const R9_PROTOCOL = `" + block + "`;", js)

    def test_refuses_library_inside_the_repository(self):
        from exam_mastery.mastery import MasteryError, resolve_home
        for inside in (REPO, REPO / "lib", REPO / "exam_mastery" / "x"):
            with self.assertRaises(MasteryError):
                resolve_home(inside)
        target = REPO / "mastery-lib-must-not-exist"
        run = subprocess.run([sys.executable, "-m", "exam_mastery.mastery", "--home", str(target), "build"],
                             cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn("Refusing", run.stderr)
        self.assertFalse(target.exists())

    def test_state_schema_is_checked(self):
        from exam_mastery.mastery import MasteryError, validate_state
        ok = {"schema": "mastery-state-v1", "saved_at": "2026-11-27T10:00:00Z", "origin": "http://127.0.0.1:8765",
              "storage": {"em-tutor-v1": {"schema": 1, "tracks": {"mastery|x": {"events": [{"type": "hint"}]}}},
                          "em-practice-v1": None}}
        validate_state(ok)
        for bad in ({**ok, "schema": "x"}, {**ok, "extra": 1}, {**ok, "storage": {"other-key": {}}},
                    {**ok, "storage": {"em-tutor-v1": {"schema": 1, "tracks": {"k": {"events": "no"}}}}}):
            with self.assertRaises(MasteryError):
                validate_state(bad)


@unittest.skipUnless(HAVE_BROWSER, "playwright not installed")
class MasteryV1EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import build
        from exam_mastery.mastery.server import start_in_thread
        cls.tmp = tempfile.TemporaryDirectory(prefix="mastery-home-")
        cls.home = Path(cls.tmp.name) / "Mastery"
        cls.result = build(cls.home, log=lambda *_: None)
        cls.server, cls.base = start_in_thread(cls.home)
        cls.unit = json.loads(UNIT.read_text(encoding="utf-8"))
        cls.lib = json.loads((cls.home / "library.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    # -------------------------------------------------------------- server guards
    def test_server_serves_only_the_allow_list_and_checks_host_origin_schema(self):
        from exam_mastery.mastery.server import ALLOWED
        (self.home / "library-spec.local.json").write_text("{}", encoding="utf-8")
        for path in ("/library-spec.local.json", "/state/latest.json", "/units/attention/.em-state/x.json",
                     "/units/attention/../library.json", "/assets/", "/units/"):
            self.assertEqual(_get(self.base, path)[0], 404, path)
        self.assertIsNone(ALLOWED.match("/library-spec.local.json"))
        self.assertEqual(_get(self.base, "/", headers={"Host": "evil.example:80"})[0], 403)
        snap = json.dumps({"schema": "mastery-state-v1", "saved_at": "2026-11-27T10:00:00Z", "storage": {}}).encode()
        self.assertEqual(_get(self.base, "/api/state", method="POST", body=snap, headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(_get(self.base, "/api/state", method="POST", body=b'{"schema":"nope"}')[0], 400)
        self.assertEqual(_get(self.base, "/api/state", method="POST", body=snap, headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(_get(self.base, "/api/state", method="POST", body=b"x" * 10, headers={"Content-Length": "99999999"})[0], 413)
        (self.home / "library-spec.local.json").unlink()

    # -------------------------------------------------------------- the daily flow in a real browser
    def test_daily_flow_end_to_end(self):
        base, errors, external = self.base, [], []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                ctx = browser.new_context(accept_downloads=True)
                ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=base.rstrip("/"))
                pg = ctx.new_page()
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                pg.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)

                # Home: start / continue / study, every product link resolves.
                pg.goto(base)
                pg.wait_for_selector('#app[data-ready="1"]')
                self.assertIn("Noch nichts bearbeitet", pg.inner_text("#continue"))
                self.assertEqual(pg.get_attribute("#next", "data-rule"), "M1")
                self.assertEqual(pg.get_attribute("#next", "data-engine-rule"), "R0")
                links = {a.get_attribute("data-product"): a.get_attribute("href") for a in pg.locator("#start a[data-product]").all()}
                self.assertEqual(set(links), {"interactive", "textbook", "workbook", "anki", "workbench"})
                magic = {"textbook": b"%PDF", "workbook": b"%PDF", "anki": b"PK", "interactive": b"<!doctype html", "workbench": b"<!doctype html"}
                for kind, href in links.items():
                    status, ctype, data = _get(base, "/" + href)
                    self.assertEqual(status, 200, href)
                    self.assertTrue(data.startswith(magic[kind]), href)
                self.assertIn("falls neuer", pg.inner_text("#anki"))
                self.assertIn("NOT_RUN", pg.inner_text("#limits"))

                # Workbench: wrong and correct attempt are diagnosed; hint makes the next solution assisted.
                pg.click("#next-link")
                pg.wait_for_selector('html[data-em-ready="1"]')
                self.assertEqual(pg.get_attribute("#wb", "data-task"), "ml-pre")
                pg.fill("#ans", "0,5"); pg.click("#check")
                self.assertIn(pg.get_attribute("#wb", "data-result"), {"incorrect", "partial"})
                pg.fill("#ans", "0,24"); pg.click("#check")
                self.assertEqual(pg.get_attribute("#wb", "data-result"), "correct")
                pg.click("#next")
                self.assertEqual(pg.get_attribute("#wb", "data-task"), "ml-core")
                pg.click("#hint")
                pg.fill("#ans", "delta_o*v1*fp1*x1"); pg.click("#check")
                self.assertEqual(pg.get_attribute("#wb", "data-result"), "correct")
                self.assertEqual(pg.get_attribute("#wb", "data-rule"), "RF")  # solved with help -> similar task without hints
                pg.click("#next")
                self.assertEqual(pg.get_attribute("#wb", "data-task"), "ml-similar")

                # Tutor brief on an evidence item: task + attempts, R9 header, no answer key; logged as a tutor event.
                pg.locator(".wb-tutor summary").click()
                pg.fill("#tutor-q", "Wie gehe ich den zweiten Pfad?")
                pg.click("#tutor-brief")
                brief = pg.inner_text("#tutor-brief-out")
                self.assertIn("Du bist mein Tutor", brief)
                self.assertIn("ml-similar", brief)
                self.assertIn("delta_o*v1*fp1*x1", brief)                   # own attempt (same competency)
                self.assertIn("Wie gehe ich den zweiten Pfad?", brief)
                self.assertIn("Keine Musterlösung im Paket", brief)
                self.assertNotIn("delta_o*v2*fp2*x2", brief)                # ml-similar key
                self.assertNotIn("∂L/∂w₂₂ = δ_o · v₂ · f′(z₂) · x₂", brief)   # ml-similar model solution
                store = json.loads(pg.evaluate("localStorage.getItem('em-tutor-v1')"))
                events = store["tracks"]["mastery|ml/backprop-track"]["events"]
                self.assertTrue(any(e["type"] == "tutor" and e["task"] == "ml-similar" for e in events))
                n_events = len(events)
                pg.reload(); pg.wait_for_selector('html[data-em-ready="1"]')
                store = json.loads(pg.evaluate("localStorage.getItem('em-tutor-v1')"))
                self.assertGreaterEqual(len(store["tracks"]["mastery|ml/backprop-track"]["events"]), n_events)
                self.assertTrue(pg.locator(".wb-step.done").count() >= 2)

                # Explorable: attempt, hint, solution view; transfer task tutor brief without its solution.
                pg.goto(base + self.lib["units"][0]["products"]["interactive"])
                dims = pg.locator('.assessment[data-task-id="task/dimensions"]')
                dims.locator("#attempt-task-dimensions").fill("Q K^T hat n mal m Einträge")
                dims.locator(".submit-attempt").click()
                self.assertIn("Freitext", dims.locator(".attempt-status").inner_text())
                dims.locator(".hint-button").click()
                dims.locator(".answer-button").click()
                transfer = pg.locator('.assessment[data-task-id="task/correlated-transfer"]')
                self.assertTrue(transfer.locator(".tutor-button").is_disabled())   # only after an own attempt
                transfer.locator("#attempt-task-correlated-transfer").fill("Die Varianz wächst mit der Korrelation")
                transfer.locator(".submit-attempt").click()
                transfer.locator(".tutor-panel summary").click()
                transfer.locator(".tutor-button").click()
                tbrief = transfer.locator(".tutor-brief").inner_text()
                task = next(a for a in self.unit["assessments"] if a["id"] == "task/correlated-transfer")
                self.assertIn("Du bist mein Tutor", tbrief)
                self.assertIn(task["prompt"][:40], tbrief)
                self.assertIn("Die Varianz wächst mit der Korrelation", tbrief)
                self.assertIn("Keine Musterlösung im Paket", tbrief)
                self.assertNotIn(task["solution"][:60], tbrief)
                model = json.loads(pg.evaluate("document.getElementById('em-interactive-data').textContent"))
                self.assertNotIn("solution", next(a for a in model["assessments"] if a["id"] == task["id"]))

                # Reload keeps explorable state (attempt text, hint, solution seen, tutor) and the evidence log stays valid.
                pg.reload()
                dims = pg.locator('.assessment[data-task-id="task/dimensions"]')
                self.assertEqual(dims.get_attribute("data-restored"), "1")
                self.assertEqual(dims.locator("#attempt-task-dimensions").input_value(), "Q K^T hat n mal m Einträge")
                self.assertIn("Musterlösung eingesehen", dims.locator(".attempt-status").inner_text())
                self.assertTrue(dims.locator(".hint-text").is_visible())
                transfer = pg.locator('.assessment[data-task-id="task/correlated-transfer"]')
                self.assertIn("Tutor-Brief", transfer.locator(".attempt-status").inner_text())
                with pg.expect_download() as dl:
                    pg.click("#evidence-export")
                log = json.loads(Path(dl.value.path()).read_text(encoding="utf-8"))
                self.assertEqual([e["type"] for e in log["events"]], ["attempt", "hint", "solution_reveal", "attempt", "tutor_brief"])
                self.assertNotIn("Varianz wächst", json.dumps(log))
                from exam_mastery.learning.experience_evidence import summarize
                summary = summarize(log, self.unit)
                self.assertEqual(summary["assessments"]["task/correlated-transfer"]["tutor_briefs"], 1)
                self.assertTrue(summary["assessments"]["task/correlated-transfer"]["ever_helped"])

                # Home again: continue points to the last activity; progress shows assisted vs unassisted and basis.
                pg.goto(base + "#lernstand")
                pg.wait_for_selector('#app[data-ready="1"]')
                self.assertTrue(pg.locator("#lernstand").is_visible())
                self.assertIn("keine Messung von Lernen", pg.inner_text("#proximal"))
                row = lambda src, kc: pg.locator(f'tr[data-source="{src}"][data-kc="{kc}"]')
                pre = row("workbench", "prereq/sigmoid-derivative")
                self.assertEqual(pre.get_attribute("data-status"), "INDEPENDENT_PASS")
                self.assertEqual(pre.get_attribute("data-basis"), "production")
                self.assertEqual(pre.get_attribute("data-unassisted"), "2")
                self.assertEqual(pre.get_attribute("data-assisted"), "0")
                bp = row("workbench", "ml/backpropagation")
                self.assertEqual(bp.get_attribute("data-status"), "ASSISTED")
                self.assertEqual(bp.get_attribute("data-assisted"), "1")
                self.assertEqual(bp.get_attribute("data-basis"), "none")
                shapes = row("explorable", "attention/shapes")
                self.assertEqual(shapes.get_attribute("data-status"), "NOT_ASSESSED")   # free text never changes a state
                self.assertEqual(shapes.get_attribute("data-unverified"), "1")
                self.assertEqual(shapes.get_attribute("data-unassisted"), "1")
                self.assertNotIn("%", pg.inner_text("#lernstand table"))
                pg.goto(base + "#start"); pg.wait_for_selector('#app[data-ready="1"]')
                self.assertIn("Interaktiv", pg.inner_text("#continue"))
                self.assertEqual(pg.get_attribute("#next", "data-rule"), "M1")
                pg.wait_for_selector("#backup-status[data-saved]", state="attached")
            finally:
                browser.close()
        self.assertEqual(errors, [])
        self.assertEqual(external, [])

        # The server received a validated copy; `export` writes it as a backup.
        from exam_mastery.mastery import export
        latest = json.loads((self.home / "state" / "latest.json").read_text(encoding="utf-8"))
        self.assertIn("mastery|ml/backprop-track", latest["storage"]["em-tutor-v1"]["tracks"])
        target = export(self.home)
        backup = json.loads(Path(target).read_text(encoding="utf-8"))
        self.assertEqual(backup["schema"], "mastery-backup-v1")
        self.assertEqual(backup["library"][0]["slug"], "attention")

    # -------------------------------------------------------------- Anki round trip and idempotent rebuild
    @unittest.skipUnless(HAVE_ANKI, "anki not installed")
    def test_zz_anki_imports_into_throwaway_collection_and_unchanged_rebuild_restamps_nothing(self):
        from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
        from exam_mastery.mastery import build, is_outdated
        package = self.home / "units" / "attention" / "Anki.apkg"
        with tempfile.TemporaryDirectory(prefix="throwaway-anki-") as tmp:
            col = Collection(str(Path(tmp) / "throwaway.anki2"))
            try:
                col.import_anki_package(ImportAnkiPackageRequest(package_path=str(package), options=ImportAnkiPackageOptions()))
                self.assertEqual(len(col.find_notes("")), self.lib["units"][0]["anki"]["notes"])
            finally:
                col.close()
        self.assertFalse(is_outdated(self.home))
        before = hashlib.sha256(package.read_bytes()).hexdigest()
        result = build(self.home, force=True, log=lambda *_: None)
        self.assertEqual(result["built"], ["attention"])
        report = json.loads((self.home / "units" / "attention" / "anki_report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["restamped"], [])
        self.assertEqual(report["package_status"], "UNCHANGED")
        self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(), before)


class PrivateUnitIsDataNotCode(unittest.TestCase):
    def test_private_unit_from_outside_the_repo_is_added_without_code_changes(self):
        from exam_mastery.mastery import add_private_unit, build
        with tempfile.TemporaryDirectory(prefix="mastery-private-") as tmp:
            home, private = Path(tmp) / "Mastery", Path(tmp) / "private" / "unit.json"
            private.parent.mkdir()
            unit = json.loads(UNIT.read_text(encoding="utf-8"))
            unit["unit_id"] = "private/attention-copy"
            private.write_text(json.dumps(unit, ensure_ascii=False), encoding="utf-8")
            slug = add_private_unit(private, slug="privat", tracks=["ml/backprop-track"], home=home)
            build(home, log=lambda *_: None)
            lib = json.loads((home / "library.json").read_text(encoding="utf-8"))
            self.assertEqual([u["slug"] for u in lib["units"]], ["attention", slug])
            self.assertTrue(lib["units"][1]["private"])
            self.assertNotIn(str(private), json.dumps(lib))           # served manifest carries no private path
            self.assertTrue((home / "units" / "privat" / "Interaktiv" / "index.html").is_file())
            self.assertTrue((home / "library-spec.local.json").is_file())
            spec = json.loads((REPO / "exam_mastery" / "mastery" / "library.json").read_text(encoding="utf-8"))
            self.assertEqual([u["slug"] for u in spec["units"]], ["attention"])  # the repository spec is untouched


if __name__ == "__main__":
    unittest.main()
