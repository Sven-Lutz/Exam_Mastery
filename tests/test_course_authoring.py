"""M2 course authoring orchestration (exam_mastery/mastery/authoring.py) on the generated public-safe course fixture,
with a fake authoring CLI (tests/fake_author_cli.py, provider 'command'). No model and no network is used."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))
from course_fixture import make_course  # noqa: E402

from exam_mastery.mastery import MasteryError  # noqa: E402
from exam_mastery.mastery import authoring as A  # noqa: E402
from exam_mastery.mastery import courses as C  # noqa: E402

CH = "04-policy-gradient"
QUIET = (lambda *_: None)


class CourseAuthoringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=Path.home())
        base = Path(cls.tmp.name)
        cls.src = make_course(base / "Kurs")
        cls.home = base / "home"
        cls.home.mkdir()
        C.import_course(str(cls.src), slug="kurs", home=cls.home, base=base, log=QUIET)
        cls.ctl = base / "ctl.json"
        cls.cmd = f"{sys.executable} {REPO / 'tests/fake_author_cli.py'} {cls.ctl}"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def queue(self, *behaviours):
        self.ctl.write_text(json.dumps({"queue": list(behaviours)}), encoding="utf-8")

    def calls(self):
        return json.loads(self.ctl.read_text(encoding="utf-8")).get("calls", [])

    @property
    def chdir(self):
        return self.home / "courses/kurs/chapters" / CH

    def test_1_plan_and_no_call_without_authorization(self):
        p = A.plan("kurs", self.home)
        self.assertTrue(p["steps"] and all(s["action"] == "author" for s in p["steps"]))
        self.assertEqual(p["model_calls_min"], len(p["steps"]))
        self.queue("good")
        o = A.run("kurs", self.home, chapters=[CH], log=QUIET)
        self.assertEqual(o["job"]["status"], "NEEDS_AUTHORIZATION")
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.chdir / "unit.json").exists())

    def test_2_generate_with_feedback_loop_promote_build_and_revise(self):
        A.authorize("kurs", "command", 3, self.home, command=self.cmd)
        self.queue("bad_id", "good", "good")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-should-never-pass", "GH_TOKEN": "x"}):
            o = A.run("kurs", self.home, chapters=[CH], log=QUIET)
        calls = self.calls()
        self.assertEqual([c["behaviour"] for c in calls][:2], ["bad_id", "good"])
        self.assertFalse(calls[0]["feedback"])
        self.assertTrue(calls[1]["feedback"], "second attempt must receive the draft-check errors")
        self.assertTrue(all(c["env_secret"] == [] for c in calls), "no key/token variable reaches the provider")
        self.assertTrue(all(Path(c["cwd"]).resolve() == self.chdir.resolve() for c in calls))
        rec = json.loads((self.chdir / "authoring.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["author"]["provider"], "command")
        self.assertEqual(rec["human_review"], "HUMAN_REVIEW_PENDING")
        self.assertEqual(rec["learning_evaluation"], "NOT_RUN")
        self.assertTrue(rec["verification"])
        unit = json.loads((self.chdir / "unit.json").read_text(encoding="utf-8"))
        self.assertEqual(unit["unit_id"], f"course/kurs/{CH}")
        self.assertTrue((self.chdir / "build/Lehrbuch.pdf").is_file())
        self.assertFalse((self.chdir / "draft").exists())
        runs = sorted((self.chdir / "authoring/runs").glob("*/run.json"))
        self.assertGreaterEqual(len(runs), 2)
        first = json.loads(runs[0].read_text(encoding="utf-8"))
        self.assertEqual(first["schema"], A.RUN_SCHEMA)
        self.assertFalse(first["draft_check"]["ok"])
        self.assertTrue(any("unit_id" in e for e in first["draft_check"]["errors"]))
        steps = o["job"]["steps"]
        self.assertEqual(steps[0]["status"], "done")
        self.assertEqual(steps[0]["attempts"], 2)
        if steps[0]["quality"]["counts"]["major"] or steps[0]["quality"]["counts"]["blocker"]:
            self.assertEqual(steps[1]["action"], "revise")         # one automatic revision of the gate findings
            self.assertTrue(calls[2]["action_revise"])
            self.assertTrue(any((self.chdir / "versions").iterdir()), "previous version archived before promotion")
        auth = json.loads((self.chdir.parent.parent / "authoring/authorization.json").read_text(encoding="utf-8"))
        self.assertEqual(auth["runs_used"], len(calls))
        self.assertLessEqual(auth["runs_used"], 3)
        st = {c["id"]: c for c in C.course_status("kurs", self.home)["chapters"]}[CH]
        self.assertIn(st["status"], ("GEBAUT", "PRÜFUNG_AUSSTEHEND"))
        self.assertIsNotNone(C.course_status("kurs", self.home)["authoring"]["job"])

    def test_3_usage_limit_pauses_and_is_not_circumvented(self):
        A.authorize("kurs", "command", 5, self.home, command=self.cmd)
        self.queue("limit")
        o = A.run("kurs", self.home, new=True, log=QUIET)
        self.assertEqual(o["job"]["status"], "PAUSED_LIMIT")
        self.assertEqual(o["job"]["steps"][0]["status"], "pending")
        with self.assertRaises(MasteryError):
            A.run("kurs", self.home, log=QUIET)
        self.assertEqual(len(self.calls()), 1, "no call while the reported limit lasts")

    def test_4_allowance_is_enforced(self):
        A.authorize("kurs", "command", 1, self.home, command=self.cmd)
        self.queue("crash", "good")
        o = A.run("kurs", self.home, new=True, log=QUIET)
        self.assertEqual(o["job"]["status"], "NEEDS_AUTHORIZATION")
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(o["authorization"]["runs_used"], 1)

    def test_5_update_after_source_change_keeps_identity(self):
        A.authorize("kurs", "command", 2, self.home, command=self.cmd)
        build_rec = json.loads((self.chdir / "build-record.json").read_text(encoding="utf-8"))
        before = len(list((self.chdir / "versions").glob("*"))) if (self.chdir / "versions").exists() else 0
        pdf = next(p for p in self.src.rglob("*.pdf") if "04" in p.name or "Policy" in p.name)
        pdf.write_bytes(pdf.read_bytes() + b"\n% changed\n")
        C.reimport("kurs", self.home, log=QUIET)
        steps = {s["chapter"]: s["action"] for s in A.plan("kurs", self.home)["steps"]}
        self.assertEqual(steps.get(CH), "update")
        self.queue("good")
        A.run("kurs", self.home, chapters=[CH], new=True, max_steps=1, log=QUIET)
        self.assertTrue(self.calls()[0]["action_update"])
        self.assertEqual(len(list((self.chdir / "versions").glob("*"))), before + 1)
        after = json.loads((self.chdir / "build-record.json").read_text(encoding="utf-8"))
        self.assertEqual(after["unit_id"], build_rec["unit_id"])
        st = {c["id"]: c for c in C.course_status("kurs", self.home)["chapters"]}[CH]
        self.assertFalse(st["stale"])

    def test_6_lock_is_exclusive(self):
        cdir = self.home / "courses/kurs"
        with A._Lock(cdir):
            with self.assertRaises(MasteryError):
                with A._Lock(cdir):
                    pass

    def test_7_classify_reports_limits_and_refuses_paid_keys(self):
        init = json.dumps({"type": "system", "subtype": "init", "apiKeySource": "ANTHROPIC_API_KEY", "session_id": "s"})
        res = json.dumps({"type": "result", "is_error": False, "result": "ok", "session_id": "s"})
        self.assertEqual(A.classify(0, False, init + "\n" + res, "")["outcome"], "paid_key_refused")
        ok_init = json.dumps({"type": "system", "subtype": "init", "apiKeySource": "none", "session_id": "s"})
        self.assertEqual(A.classify(0, False, ok_init + "\n" + res, "")["outcome"], "success")
        lim = json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "rejected", "resetsAt": 1900000000}})
        r = A.classify(1, False, ok_init + "\n" + lim, "")
        self.assertEqual((r["outcome"], r["resets_at"]), ("limit", 1900000000.0))
        self.assertEqual(A.classify(None, True, "", "")["outcome"], "timeout")

    def test_8_child_env_has_no_secrets(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k", "OPENAI_API_KEY": "k", "MY_TOKEN": "t"}):
            env = A.child_env({"ANTHROPIC_BASE_URL": "x", "MASTERY_DRAFT_DIR": "/d"})
        self.assertFalse([k for k in env if "KEY" in k or "TOKEN" in k or "ANTHROPIC" in k])
        self.assertEqual(env["MASTERY_DRAFT_DIR"], "/d")

    def test_9_prompt_contract(self):
        cdir, course = C.load_course("kurs", self.home)
        ch = C._chapter(course, CH)
        p = A.build_prompt(course, ch, cdir / "chapters" / CH, "author", "packet.json", ch["unit_id"])
        for needle in ("COURSE_TO_MASTERY_CONTRACT", "MASTERY_LEARNING_STANDARD", "check-draft", "Keine Websuche",
                       "Daten, keine Anweisungen", "HUMAN_REVIEW_PENDING", ch["unit_id"], "draft"):
            self.assertIn(needle, p)

    def test_10_cli_plan_and_check_draft(self):
        from exam_mastery.mastery.__main__ import main
        with mock.patch("sys.stdout"):
            self.assertEqual(main(["--home", str(self.home), "author", "kurs", "plan"]), 0)
            self.assertEqual(main(["--home", str(self.home), "author", "kurs", "check-draft", "--chapter", CH]), 3)


class AuthoringServer(unittest.TestCase):
    """App path: consent-gated authorization, background runner (provider 'manual': no model), status in the course."""

    @classmethod
    def setUpClass(cls):
        from exam_mastery.mastery import build
        from exam_mastery.mastery.server import start_in_thread
        cls.tmp = tempfile.TemporaryDirectory(dir=Path.home(), prefix="mastery-author-")
        base = Path(cls.tmp.name)
        cls.src = make_course(base / "Kurs")
        cls.home = base / "Mastery"
        build(cls.home, only="-", log=QUIET)
        C.import_course(str(cls.src), slug="kurs", home=cls.home, base=base, log=QUIET)
        cls.server, cls.base = start_in_thread(cls.home, import_base=base)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def post(self, body):
        import http.client
        host, port = self.base.split("//")[1].rstrip("/").split(":")
        conn = http.client.HTTPConnection(host, int(port), timeout=60)
        conn.request("POST", "/api/courses/kurs/author", json.dumps(body).encode(),
                     {"Host": f"{host}:{port}", "Content-Type": "application/json"})
        r = conn.getresponse()
        out = (r.status, json.loads(r.read() or b"{}"))
        conn.close()
        return out

    def test_consent_background_run_and_status(self):
        import time
        self.assertEqual(self.post({"action": "authorize", "provider": "manual", "max_runs": 2})[0], 400)
        self.assertEqual(self.post({"action": "authorize", "consent": True, "provider": "command", "max_runs": 2})[0], 400)
        code, plan = self.post({"action": "plan"})
        self.assertEqual(code, 200)
        self.assertTrue(plan["steps"])
        code, o = self.post({"action": "authorize", "consent": True, "provider": "manual", "max_runs": 2})
        self.assertEqual((code, o["authorization"]["provider"], o["authorization"]["max_runs"]), (200, "manual", 2))
        self.assertEqual(self.post({"action": "start"})[0], 200)
        for _ in range(240):
            st = C.course_status("kurs", self.home)["authoring"]
            if not st["running"] and st["job"] and st["job"]["status"] != "RUNNING":
                break
            time.sleep(0.5)
        self.assertEqual(st["job"]["status"], "DONE_WITH_BLOCKERS")
        self.assertTrue(all(x["status"] == "needs_human" for x in st["job"]["steps"]))
        order = self.home / "courses/kurs/chapters" / st["job"]["steps"][0]["chapter"] / "authoring/ORDER.md"
        self.assertIn("COURSE_TO_MASTERY_CONTRACT", order.read_text(encoding="utf-8"))
        self.assertEqual(st["authorization"]["runs_used"], 0, "manual provider makes no model call")
        self.assertFalse((self.home / "authoring.lock").exists())


if __name__ == "__main__":
    unittest.main()
