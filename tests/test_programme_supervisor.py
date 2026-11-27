"""Programme supervisor: decisions, limit pauses, crash recovery and env hygiene.

Uses a fake `claude` executable; no model call and no launchd change happens here.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("em_supervisor", ROOT / "ops" / "autonomy" / "supervisor.py")
sup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sup)

FAKE = textwrap.dedent(r'''
    #!PYTHON
    import json, os, sys, time
    argv = sys.argv[1:]
    if os.environ.get("FAKE_ARGV_OUT") and argv[:1] == ["-p"]:
        with open(os.environ["FAKE_ARGV_OUT"], "a") as fh:
            fh.write(json.dumps(argv) + "\n")
    if argv[:2] == ["agents", "--json"]:
        print(os.environ.get("FAKE_AGENTS", "[]")); sys.exit(0)
    mode = os.environ.get("FAKE_MODE", "success")
    sid = None
    for flag in ("--session-id", "--resume"):
        if flag in argv:
            sid = argv[argv.index(flag) + 1]
    if os.environ.get("FAKE_ENV_OUT"):
        with open(os.environ["FAKE_ENV_OUT"], "w") as fh:
            json.dump(sorted(os.environ), fh)
    now = time.time()
    if mode == "success":
        print(json.dumps({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "resetsAt": now + 3600,
                                                                          "rateLimitType": "five_hour"}}))
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "done",
                          "session_id": sid, "num_turns": 3, "duration_ms": 10}))
    elif mode == "limit":
        print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                          "result": "Claude usage limit reached", "session_id": sid,
                          "rate_limit_info": {"status": "rejected", "resetsAt": now + 7200,
                                              "rateLimitType": "five_hour"}}))
        sys.exit(1)
    elif mode == "success_mentions_limit":
        print(json.dumps({"type": "result", "subtype": "success", "is_error": False,
                          "result": "Researched how a usage limit reached state is handled.", "session_id": sid}))
    elif mode == "error":
        sys.stderr.write("boom\n"); sys.exit(2)
    elif mode == "hang":
        time.sleep(60)
''').replace("#!PYTHON", "#!" + sys.executable).lstrip()


class SupervisorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.state = base / "state"
        self.control = base / "control"
        (self.control / "docs" / "programme").mkdir(parents=True)
        (self.control / "docs" / "programme" / "RESUME_PROMPT.md").write_text("resume protocol text\n")
        self.fake = base / "claude"
        self.fake.write_text(FAKE)
        self.fake.chmod(0o755)
        self.argv_out = base / "argv.jsonl"
        self.cfg_path = base / "config.json"
        self.cfg_path.write_text(json.dumps({
            "control_worktree": str(self.control), "claude_bin": str(self.fake),
            "watch_paths": [str(self.control)], "run_timeout_min": 0.05, "lead_stale_after_min": 60,
            "max_runs_per_24h": 4, "max_consecutive_failures": 3, "failure_backoff_min": 30,
            "limit_probe_min": 60, "reset_grace_s": 120,
        }))
        self.saved_env = dict(os.environ)
        os.environ.update(EM_AUTONOMY_STATE=str(self.state), EM_AUTONOMY_CONFIG=str(self.cfg_path),
                          FAKE_MODE="success", FAKE_ARGV_OUT=str(self.argv_out))
        os.environ.pop("FAKE_AGENTS", None)
        self.write_programme([{"id": "WP-R1", "title": "R1", "status": "RESUMABLE", "priority": 1}])

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved_env)
        self.tmp.cleanup()

    # helpers
    def write_programme(self, wps, headless=True):
        (self.control / sup.STATE_FILE).write_text(json.dumps(
            {"autonomy": {"headless_enabled": headless}, "work_packages": wps}))

    def tick(self):
        # The supervisor passes a whitelisted environment only; fake controls go via extra_env.
        cfg = json.loads(self.cfg_path.read_text())
        cfg.setdefault("extra_env", {}).update({k: v for k, v in os.environ.items() if k.startswith("FAKE_")})
        for k in [k for k in cfg["extra_env"] if k.startswith("FAKE_") and k not in os.environ]:
            del cfg["extra_env"][k]
        self.cfg_path.write_text(json.dumps(cfg))
        return sup.tick(sup.load_config())

    def runtime(self):
        return json.loads((self.state / "runtime.json").read_text())

    def argv_calls(self):
        if not self.argv_out.exists():
            return []
        return [json.loads(l) for l in self.argv_out.read_text().splitlines()]

    # tests
    def test_success_runs_bounded_headless_session_in_auto_mode(self):
        r = self.tick()
        self.assertIn("outcome=success", r)
        rt = self.runtime()
        self.assertEqual(rt["status"], "IDLE")
        self.assertEqual(rt["last_run"]["wp"], "WP-R1")
        argv = self.argv_calls()[0]
        self.assertIn("--session-id", argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "auto")
        self.assertEqual(argv[argv.index("--permission-prompts") + 1], "none")
        self.assertIn("resume protocol text", argv[1])
        self.assertIn("WP-R1", argv[1])

    def test_kill_switch(self):
        sup.state_dir().joinpath("DISABLED").write_text("x")
        self.assertIn("disabled", self.tick())
        self.assertEqual(self.argv_calls(), [])

    def test_lock_held_by_other_tick(self):
        import fcntl
        fh = sup.state_dir().joinpath("supervisor.lock").open("a+")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            self.assertIn("lock", self.tick())
        finally:
            fh.close()
        self.assertEqual(self.argv_calls(), [])

    def test_fresh_lead_heartbeat_prevents_parallel_run(self):
        sup.write_json(sup.state_dir() / "heartbeat.json", {"ts": time.time(), "wp": "WP-R1", "session_id": "s"})
        self.assertIn("heartbeat fresh", self.tick())
        self.assertEqual(self.argv_calls(), [])

    def test_lead_hold_blocks_until_expiry_and_is_capped(self):
        sup.write_json(sup.state_dir() / "heartbeat.json", {"ts": time.time() - 7200, "wp": "WP-R1",
                                                            "hold_until": time.time() + 600})
        self.assertIn("lead hold until", self.tick())
        sup.write_json(sup.state_dir() / "heartbeat.json", {"ts": time.time() - 7200, "hold_until": time.time() - 1})
        self.assertIn("outcome=success", self.tick())
        sup.main(["heartbeat", "--wp", "X", "--hold-min", "10000"])
        hb = json.loads((sup.state_dir() / "heartbeat.json").read_text())
        self.assertLessEqual(hb["hold_until"] - hb["ts"], 360 * 60 + 1)

    def test_busy_interactive_session_in_project_prevents_run(self):
        os.environ["FAKE_AGENTS"] = json.dumps([{"pid": os.getpid(), "cwd": str(self.control / "sub"),
                                                 "status": "busy", "sessionId": "x", "name": "lead"}])
        self.assertIn("interactive session busy", self.tick())

    def test_lead_waiting_on_limit_is_left_to_builtin_resume(self):
        sup.write_json(sup.state_dir() / "heartbeat.json", {"ts": time.time() - 7200, "session_id": "lead-1"})
        os.environ["FAKE_AGENTS"] = json.dumps([{"pid": os.getpid(), "cwd": "/elsewhere", "status": "busy",
                                                 "sessionId": "lead-1", "name": "x"}])
        self.assertIn("lead session lead-1 busy", self.tick())

    def test_unrelated_busy_session_does_not_block(self):
        os.environ["FAKE_AGENTS"] = json.dumps([{"pid": os.getpid(), "cwd": "/other/project", "status": "busy",
                                                 "sessionId": "y", "name": "int-db"}])
        self.assertIn("outcome=success", self.tick())

    def test_limit_pauses_until_reported_reset_then_resumes_same_session(self):
        os.environ["FAKE_MODE"] = "limit"
        self.assertIn("outcome=limit", self.tick())
        rt = self.runtime()
        self.assertEqual(rt["status"], "PAUSED_LIMIT")
        self.assertGreater(rt["paused_until"], time.time() + 7000)
        self.assertEqual(rt["consecutive_failures"], 0)
        self.assertIn("PAUSED_LIMIT until", self.tick())
        self.assertEqual(len(self.argv_calls()), 1)
        self.assertEqual(rt["windows"]["five_hour"]["status"], "rejected")
        # Reset time reached: the same session is resumed, not restarted.
        rt["paused_until"] = time.time() - 1
        rt["windows"]["five_hour"]["resetsAt"] = time.time() - 1
        sup.save_runtime(rt)
        os.environ["FAKE_MODE"] = "success"
        self.assertIn("outcome=success", self.tick())
        second = self.argv_calls()[1]
        first = self.argv_calls()[0]
        self.assertEqual(second[second.index("--resume") + 1], first[first.index("--session-id") + 1])

    def test_limit_text_in_successful_result_is_not_a_limit(self):
        os.environ["FAKE_MODE"] = "success_mentions_limit"
        self.assertIn("outcome=success", self.tick())

    def test_failures_back_off_then_block(self):
        os.environ["FAKE_MODE"] = "error"
        for n in (1, 2, 3):
            self.assertIn("outcome=error", self.tick())
            rt = self.runtime()
            if n < 3:
                self.assertEqual(rt["status"], "FAILED_RECOVERABLE")
                self.assertGreater(rt["paused_until"], time.time() + 30 * 60 * 2 ** (n - 1) - 5)
                rt["paused_until"] = time.time() - 1
                sup.save_runtime(rt)
        self.assertEqual(self.runtime()["status"], "BLOCKED")
        self.assertIn("BLOCKED", self.tick())
        sup.main(["reset"])
        os.environ["FAKE_MODE"] = "success"
        self.assertIn("outcome=success", self.tick())

    def test_timeout_kills_run_and_next_tick_resumes(self):
        os.environ["FAKE_MODE"] = "hang"
        t0 = time.time()
        self.assertIn("outcome=timeout", self.tick())
        self.assertLess(time.time() - t0, 40)
        rt = self.runtime()
        rt["paused_until"] = time.time() - 1
        sup.save_runtime(rt)
        os.environ["FAKE_MODE"] = "success"
        self.tick()
        self.assertIn("--resume", self.argv_calls()[1])

    def test_crashed_supervisor_run_is_recovered_without_backoff(self):
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        sup.save_runtime({"status": "RUNNING", "runs": [], "consecutive_failures": 0,
                          "current": {"wp": "WP-R1", "pid": dead.pid, "session_id": "sess-old", "started": time.time()}})
        self.assertIn("outcome=success", self.tick())
        argv = self.argv_calls()[0]
        self.assertEqual(argv[argv.index("--resume") + 1], "sess-old")
        self.assertEqual(self.runtime()["consecutive_failures"], 0)

    def test_running_child_still_alive_is_not_duplicated(self):
        sup.save_runtime({"status": "RUNNING", "runs": [], "current": {"wp": "WP-R1", "pid": os.getpid()}})
        self.assertIn("still alive", self.tick())
        self.assertEqual(self.argv_calls(), [])

    def test_nothing_resumable_or_headless_disabled(self):
        self.write_programme([{"id": "A", "status": "COMPLETED"}, {"id": "B", "status": "HUMAN_DECISION_REQUIRED"},
                              {"id": "C", "status": "PLANNED"}])
        self.assertIn("no resumable", self.tick())
        self.write_programme([{"id": "A", "status": "RESUMABLE"}], headless=False)
        self.assertIn("no resumable", self.tick())

    def test_priority_and_autostart_selection(self):
        wp = sup.select_work_package({"autonomy": {"headless_enabled": True}, "work_packages": [
            {"id": "late", "status": "RESUMABLE", "priority": 5},
            {"id": "planned", "status": "PLANNED", "priority": 1, "autostart": True},
            {"id": "noheadless", "status": "RESUMABLE", "priority": 0, "headless_ok": False}]})
        self.assertEqual(wp["id"], "planned")

    def test_dependencies_must_be_completed(self):
        prog = {"autonomy": {"headless_enabled": True}, "work_packages": [
            {"id": "R1", "status": "CHECKPOINTED", "priority": 5},
            {"id": "R6", "status": "PLANNED", "autostart": True, "priority": 1, "depends_on": ["R1"]}]}
        self.assertEqual(sup.select_work_package(prog)["id"], "R1")
        prog["work_packages"][0]["status"] = "COMPLETED"
        self.assertEqual(sup.select_work_package(prog)["id"], "R6")

    def test_daily_cap(self):
        now = time.time()
        sup.save_runtime({"status": "IDLE", "consecutive_failures": 0,
                          "runs": [{"started": now - 60 * i, "outcome": "success"} for i in range(4)]})
        self.assertIn("daily cap", self.tick())

    def test_child_env_carries_no_api_keys(self):
        os.environ.update(ANTHROPIC_API_KEY="sk-test", GITHUB_TOKEN="ghp-test", OPENAI_API_KEY="x")
        env_out = Path(self.tmp.name) / "env.json"
        os.environ["FAKE_ENV_OUT"] = str(env_out)
        cfg = json.loads(self.cfg_path.read_text())
        cfg["extra_env"] = {"ANTHROPIC_BASE_URL": "x", "MY_API_KEY": "y", "EM_FLAG": "1"}
        self.cfg_path.write_text(json.dumps(cfg))
        self.tick()
        keys = set(json.loads(env_out.read_text()))
        self.assertFalse({"ANTHROPIC_API_KEY", "GITHUB_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_BASE_URL",
                          "MY_API_KEY"} & keys)
        self.assertIn("EM_FLAG", keys)

    def test_window_at_ceiling_pauses_until_its_reset(self):
        now = time.time()
        sup.save_runtime({"status": "IDLE", "runs": [], "consecutive_failures": 0, "windows": {
            "five_hour": {"utilization": 0.2, "resetsAt": now + 600},
            "seven_day": {"utilization": 0.86, "resetsAt": now + 86400}}})
        self.assertIn("seven_day window at ceiling", self.tick())
        self.assertEqual(self.argv_calls(), [])
        self.assertGreater(self.runtime()["paused_until"], now + 86400)

    def test_rolled_over_window_does_not_block_and_run_records_windows(self):
        now = time.time()
        sup.save_runtime({"status": "IDLE", "runs": [], "consecutive_failures": 0, "windows": {
            "seven_day": {"utilization": 0.99, "resetsAt": now - 5}}})
        self.assertIn("outcome=success", self.tick())
        self.assertEqual(self.runtime()["windows"]["five_hour"]["status"], "allowed")

    def test_plist_runs_tick_periodically(self):
        xml = sup.render_plist(sup.load_config(), interval=1800)
        self.assertIn("<string>tick</string>", xml)
        self.assertIn("<key>StartInterval</key><integer>1800</integer>", xml)
        self.assertIn("<key>RunAtLoad</key><false/>", xml)


if __name__ == "__main__":
    unittest.main()
