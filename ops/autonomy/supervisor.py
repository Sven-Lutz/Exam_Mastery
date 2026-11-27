#!/usr/bin/env python3
"""Exam Mastery programme supervisor.

Continues the autonomous programme after usage limits, crashes and reboots by
starting a bounded headless Claude Code run from the versioned programme state.
It never works around a limit: it reads the limit status that Claude Code
itself reports (``rate_limit_event`` / refused result) and waits for the
reported reset.

Stdlib only, Python >= 3.9 (the macOS system interpreter that launchd uses).

Commands
  tick        one supervisor decision (launchd calls this periodically)
  status      print runtime state, heartbeat and the next candidate work package
  heartbeat   record that an interactive lead session is working (--session, --wp)
  enable / disable   kill switch
  reset       clear BLOCKED / FAILED state after a human looked at it
  install / uninstall   load or remove the launchd agent
  smoke       real headless call with a harmless prompt plus a resume check
  launchd-smoke   the same smoke, started by launchd, to prove the agent context works

Local, uncommitted locations (override with environment variables):
  config  ~/.config/exam-mastery-autonomy/config.json   (EM_AUTONOMY_CONFIG)
  state   ~/.local/state/exam-mastery-autonomy/          (EM_AUTONOMY_STATE)
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LABEL = "dev.exam-mastery.programme-supervisor"
STATE_FILE = "docs/programme/PROGRAMME_STATE.json"
PROMPT_FILE = "docs/programme/RESUME_PROMPT.md"

# Work-package states a headless run may pick up. RUNNING counts only when no
# lead session is alive (checked before selection): the run that owned it died.
PICKABLE = ("RESUMABLE", "CHECKPOINTED", "PAUSED_LIMIT", "FAILED_RECOVERABLE", "RUNNING")
TERMINAL_OUTCOMES = ("success",)

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULTS: Dict[str, Any] = {
    "enabled": True,
    # The worktree this script lives in holds the programme state.
    "control_worktree": str(REPO_ROOT),
    "claude_bin": "claude",
    "path": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:~/.npm-global/bin:~/.local/bin",
    # Interactive sessions busy below these path prefixes count as an active lead.
    "watch_paths": [str(REPO_ROOT.parent / REPO_ROOT.name.split("-")[0])],
    "permission_mode": "auto",
    "model": None,
    "effort": None,
    "interval_s": 1800,
    "run_timeout_min": 150,
    "lead_stale_after_min": 60,
    "max_runs_per_24h": 4,
    "max_consecutive_failures": 3,
    "failure_backoff_min": 30,
    "limit_probe_min": 60,
    "reset_grace_s": 120,
    # Headless runs stop at these utilisations of the reported windows and wait
    # for the reported reset, leaving headroom for the owner's interactive work.
    "window_ceilings": {"five_hour": 0.9, "seven_day": 0.85},
}

LIMIT_TEXT = re.compile(
    r"usage limit|hit your limit|limit reached|rate_limit_error|weekly usage limit|out of extra usage",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- io

def now_ts() -> float:
    return time.time()


def iso(ts: Optional[float]) -> Optional[str]:
    if ts is None:
        return None
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def state_dir() -> Path:
    p = Path(os.environ.get("EM_AUTONOMY_STATE", "~/.local/state/exam-mastery-autonomy")).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    (p / "runs").mkdir(exist_ok=True)
    return p


def config_path() -> Path:
    return Path(os.environ.get("EM_AUTONOMY_CONFIG", "~/.config/exam-mastery-autonomy/config.json")).expanduser()


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def load_config() -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    cfg.update(read_json(config_path(), {}))
    return cfg


def xp(p: str) -> Path:
    return Path(os.path.expanduser(p))


def claude_bin(cfg: Dict[str, Any]) -> str:
    """Resolve the CLI on the supervisor's own PATH (launchd has a minimal PATH)."""
    import shutil
    b = os.path.expanduser(cfg["claude_bin"])
    if os.sep in b:
        return b
    return shutil.which(b, path=child_env(cfg)["PATH"]) or b


def log(msg: str) -> None:
    path = state_dir() / "supervisor.log"
    if path.exists() and path.stat().st_size > 1_000_000:
        os.replace(path, path.with_suffix(".log.1"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write("%s %s\n" % (iso(now_ts()), msg))


def load_runtime() -> Dict[str, Any]:
    return read_json(state_dir() / "runtime.json", {"status": "IDLE", "runs": [], "consecutive_failures": 0})


def save_runtime(rt: Dict[str, Any]) -> None:
    rt["runs"] = rt.get("runs", [])[-50:]
    write_json(state_dir() / "runtime.json", rt)


def pid_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# ----------------------------------------------------------------- decisions

def active_sessions(cfg: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """Live Claude Code sessions, or None when that cannot be determined."""
    try:
        out = subprocess.run([claude_bin(cfg), "agents", "--json"], capture_output=True,
                             text=True, timeout=30, env=child_env(cfg))
        data = json.loads(out.stdout or "null")
        return data if isinstance(data, list) else None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def lead_activity(cfg: Dict[str, Any], now: float) -> Optional[str]:
    """Reason why an interactive lead counts as active, or None."""
    hb = read_json(state_dir() / "heartbeat.json", {})
    if hb.get("ts") and now - float(hb["ts"]) < cfg["lead_stale_after_min"] * 60:
        return "lead heartbeat fresh (%s, wp=%s)" % (iso(hb["ts"]), hb.get("wp"))
    if hb.get("hold_until") and now < float(hb["hold_until"]):
        # The lead declared it is waiting (e.g. on its background agents) until then.
        return "lead hold until %s (wp=%s)" % (iso(hb["hold_until"]), hb.get("wp"))
    sessions = active_sessions(cfg)
    if sessions is None:
        return None
    watch = [str(xp(p)) for p in cfg["watch_paths"]]
    for s in sessions:
        if not pid_alive(s.get("pid")):
            continue
        if str(s.get("name", "")).startswith("em-autonomy"):
            return "headless programme session %s still alive" % s.get("sessionId")
        if hb.get("session_id") and s.get("sessionId") == hb["session_id"] and s.get("status") == "busy":
            return "lead session %s busy (possibly waiting for a limit reset)" % s["sessionId"]
        if s.get("status") == "busy" and any(str(s.get("cwd", "")).startswith(w) for w in watch):
            return "interactive session busy in %s" % s.get("cwd")
    return None


def load_programme(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return read_json(xp(cfg["control_worktree"]) / STATE_FILE, {})


def select_work_package(prog: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not prog.get("autonomy", {}).get("headless_enabled", False):
        return None
    cands = []
    done = {w.get("id") for w in prog.get("work_packages", []) if w.get("status") == "COMPLETED"}
    for wp in prog.get("work_packages", []):
        st = wp.get("status")
        if wp.get("headless_ok") is False:
            continue
        if any(dep not in done for dep in wp.get("depends_on", [])):
            continue
        if st in PICKABLE or (st == "PLANNED" and wp.get("autostart")):
            cands.append(wp)
    cands.sort(key=lambda w: (w.get("priority", 99), w.get("id", "")))
    return cands[0] if cands else None


def record_windows(rt: Dict[str, Any], limit_info: Optional[Dict[str, Any]]) -> None:
    """Keep the latest reported utilisation per window (from rate_limit_event)."""
    if not limit_info:
        return
    wins = dict(rt.get("windows") or {})
    for name, w in (limit_info.get("unifiedWindows") or {}).items():
        if isinstance(w, dict):
            wins[name] = {"utilization": w.get("utilization"), "resetsAt": w.get("resetsAt"),
                          "status": w.get("status"), "seen": now_ts()}
    if limit_info.get("rateLimitType") and limit_info.get("rateLimitType") not in (limit_info.get("unifiedWindows") or {}):
        wins[limit_info["rateLimitType"]] = {"utilization": limit_info.get("utilization"),
                                             "resetsAt": limit_info.get("resetsAt"),
                                             "status": limit_info.get("status"), "seen": now_ts()}
    rt["windows"] = wins


def window_block(cfg: Dict[str, Any], rt: Dict[str, Any], now: float) -> Optional[Tuple[str, float]]:
    """(window, reset time) if a still-open window is at or above its ceiling or rejected."""
    for name, w in (rt.get("windows") or {}).items():
        reset = w.get("resetsAt")
        if not reset or float(reset) <= now:
            continue  # window has rolled over since it was seen; usage only drops at reset
        util = w.get("utilization")
        ceiling = (cfg.get("window_ceilings") or {}).get(name)
        if w.get("status") == "rejected" or (util is not None and ceiling is not None and float(util) >= ceiling):
            return name, float(reset)
    return None


def runs_last_24h(rt: Dict[str, Any], now: float) -> int:
    return sum(1 for r in rt.get("runs", []) if now - float(r.get("started", 0)) < 86400)


def child_env(cfg: Dict[str, Any]) -> Dict[str, str]:
    """Whitelisted environment: no API keys or tokens are passed on, so a
    headless run can only use the logged-in subscription, never a paid key."""
    env = {k: os.environ[k] for k in ("HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG", "LC_ALL",
                                      "SSH_AUTH_SOCK", "__CF_USER_TEXT_ENCODING") if k in os.environ}
    env.setdefault("HOME", str(Path.home()))
    env["PATH"] = ":".join(os.path.expanduser(p) for p in cfg["path"].split(":"))
    for k, v in cfg.get("extra_env", {}).items():
        if not re.search(r"KEY|TOKEN|SECRET|PASSWORD|ANTHROPIC", k, re.IGNORECASE):
            env[k] = str(v)
    return env


def build_prompt(cfg: Dict[str, Any], wp: Dict[str, Any], resume: bool) -> str:
    base = (xp(cfg["control_worktree"]) / PROMPT_FILE)
    text = base.read_text(encoding="utf-8") if base.exists() else "Read docs/programme/RESUME_PROTOCOL.md and follow it."
    head = "Work package: %s (%s). State file: %s.\n" % (wp.get("id"), wp.get("title", ""), STATE_FILE)
    if resume:
        head += ("This continues your interrupted previous run of the same work package. Re-read the "
                 "checkpoint before acting; do not redo steps it records as done.\n")
    return head + "\n" + text


def parse_stream(text: str) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Final result message and all rate-limit infos from stream-json output."""
    result = None
    limits: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("type") == "rate_limit_event" and isinstance(msg.get("rate_limit_info"), dict):
            limits.append(msg["rate_limit_info"])
        elif msg.get("type") == "result":
            result = msg
            if isinstance(msg.get("rate_limit_info"), dict):
                limits.append(msg["rate_limit_info"])
    return result, limits


def classify(rc: Optional[int], timed_out: bool, out: str, err: str) -> Dict[str, Any]:
    result, limits = parse_stream(out)
    rejected = [l for l in limits if l.get("status") == "rejected"]
    resets = [float(l["resetsAt"]) for l in limits if l.get("resetsAt")]
    info: Dict[str, Any] = {
        "rc": rc,
        "session_id": (result or {}).get("session_id"),
        "num_turns": (result or {}).get("num_turns"),
        "duration_ms": (result or {}).get("duration_ms"),
        "subtype": (result or {}).get("subtype"),
        "last_limit": limits[-1] if limits else None,
    }
    is_error = bool((result or {}).get("is_error")) or rc not in (0, None)
    if timed_out:
        info["outcome"] = "timeout"
    elif rejected or (is_error and LIMIT_TEXT.search(((result or {}).get("result") or "") + "\n" + err[-4000:])):
        info["outcome"] = "limit"
        rej_resets = [float(l["resetsAt"]) for l in rejected if l.get("resetsAt")]
        info["resets_at"] = max(rej_resets) if rej_resets else (max(resets) if resets else None)
    elif result is not None and not is_error:
        info["outcome"] = "success"
    elif result is None and rc is None:
        info["outcome"] = "interrupted"
    else:
        info["outcome"] = "error"
        info["error_tail"] = ((result or {}).get("result") or err or out)[-600:]
    return info


# ---------------------------------------------------------------------- run

def run_headless(cfg: Dict[str, Any], rt: Dict[str, Any], wp: Dict[str, Any], now: float) -> Dict[str, Any]:
    last = rt.get("last_run") or {}
    resume = (last.get("wp") == wp.get("id") and last.get("outcome") in ("limit", "timeout", "interrupted")
              and bool(last.get("session_id")))
    sid = last["session_id"] if resume else str(uuid.uuid4())
    cmd = [claude_bin(cfg), "-p", build_prompt(cfg, wp, resume),
           "--output-format", "stream-json", "--verbose",
           "--permission-mode", cfg["permission_mode"], "--permission-prompts", "none",
           "--name", "em-autonomy-%s" % wp.get("id")]
    cmd += ["--resume", sid] if resume else ["--session-id", sid]
    if cfg.get("model"):
        cmd += ["--model", cfg["model"]]
    if cfg.get("effort"):
        cmd += ["--effort", cfg["effort"]]
    stamp = dt.datetime.fromtimestamp(now).strftime("%Y%m%dT%H%M%S")
    out_path = state_dir() / "runs" / ("%s-%s.jsonl" % (stamp, wp.get("id")))
    err_path = out_path.with_suffix(".stderr.txt")
    with out_path.open("w") as fo, err_path.open("w") as fe:
        proc = subprocess.Popen(cmd, cwd=str(xp(cfg["control_worktree"])), env=child_env(cfg), stdout=fo,
                                stderr=fe, stdin=subprocess.DEVNULL, start_new_session=True)
        rt.update(status="RUNNING", current={"wp": wp.get("id"), "pid": proc.pid, "session_id": sid,
                                             "started": now, "resume": resume, "log": out_path.name})
        save_runtime(rt)
        log("start wp=%s pid=%s session=%s resume=%s" % (wp.get("id"), proc.pid, sid, resume))
        timed_out = False
        try:
            rc: Optional[int] = proc.wait(timeout=cfg["run_timeout_min"] * 60)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate(proc)
            rc = proc.returncode
    info = classify(rc, timed_out, out_path.read_text(errors="replace"), err_path.read_text(errors="replace"))
    info.update(wp=wp.get("id"), started=now, ended=now_ts(), resume=resume, log=out_path.name)
    info["session_id"] = info.get("session_id") or sid
    return info


def _terminate(proc: "subprocess.Popen[Any]") -> None:
    for sig, wait in ((signal.SIGTERM, 30), (signal.SIGKILL, 10)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def apply_outcome(cfg: Dict[str, Any], rt: Dict[str, Any], info: Dict[str, Any], penalty: bool = True) -> None:
    rt.pop("current", None)
    record_windows(rt, info.get("last_limit"))
    rt["last_run"] = info
    rt.setdefault("runs", []).append({k: info.get(k) for k in ("wp", "started", "ended", "outcome", "session_id",
                                                              "num_turns", "log")})
    t = now_ts()
    oc = info["outcome"]
    if oc == "success":
        rt.update(status="IDLE", consecutive_failures=0, paused_until=None)
    elif oc == "limit":
        until = info.get("resets_at")
        until = (float(until) + cfg["reset_grace_s"]) if until and float(until) > t else t + cfg["limit_probe_min"] * 60
        rt.update(status="PAUSED_LIMIT", paused_until=until, consecutive_failures=0)
    elif not penalty:
        rt.update(status="IDLE", paused_until=None)
    else:
        n = int(rt.get("consecutive_failures", 0)) + 1
        rt["consecutive_failures"] = n
        if n >= cfg["max_consecutive_failures"]:
            rt.update(status="BLOCKED", paused_until=None)
        else:
            rt.update(status="FAILED_RECOVERABLE", paused_until=t + cfg["failure_backoff_min"] * 60 * 2 ** (n - 1))
    log("end wp=%s outcome=%s status=%s paused_until=%s" % (info.get("wp"), oc, rt["status"],
                                                            iso(rt.get("paused_until"))))


def tick(cfg: Dict[str, Any]) -> str:
    """One decision. Returns a short reason (also logged)."""
    sd = state_dir()
    if not cfg.get("enabled", True) or (sd / "DISABLED").exists():
        return _skip("disabled (kill switch)")
    lock_fh = (sd / "supervisor.lock").open("a+")
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fh.close()
        return _skip("another supervisor tick holds the lock")
    try:
        rt = load_runtime()
        t = now_ts()
        cur = rt.get("current")
        if rt.get("status") == "RUNNING" and cur:
            if pid_alive(cur.get("pid")):
                return _skip("run pid %s still alive" % cur.get("pid"))
            # Supervisor died while its run was going on (crash, reboot, kill). That is not
            # the run's fault: record it and resume the same session now, without backoff.
            apply_outcome(cfg, rt, {"outcome": "interrupted", "wp": cur.get("wp"), "session_id": cur.get("session_id"),
                                    "started": cur.get("started"), "ended": t, "log": cur.get("log")}, penalty=False)
            save_runtime(rt)
        if rt.get("status") == "BLOCKED":
            return _skip("BLOCKED after %s consecutive failures: run `supervisor.py reset` after review"
                         % rt.get("consecutive_failures"))
        if rt.get("paused_until") and t < float(rt["paused_until"]):
            return _skip("%s until %s" % (rt.get("status"), iso(rt["paused_until"])))
        blocked = window_block(cfg, rt, t)
        if blocked:
            rt.update(status="PAUSED_LIMIT", paused_until=blocked[1] + cfg["reset_grace_s"])
            save_runtime(rt)
            return _skip("%s window at ceiling; waiting for reset %s" % (blocked[0], iso(blocked[1])))
        reason = lead_activity(cfg, t)
        if reason:
            return _skip(reason)
        wp = select_work_package(load_programme(cfg))
        if wp is None:
            return _skip("no resumable work package (or headless disabled in programme state)")
        if runs_last_24h(rt, t) >= cfg["max_runs_per_24h"]:
            return _skip("daily cap of %s runs reached" % cfg["max_runs_per_24h"])
        info = run_headless(cfg, rt, wp, t)
        apply_outcome(cfg, rt, info)
        save_runtime(rt)
        return "ran wp=%s outcome=%s" % (wp.get("id"), info["outcome"])
    finally:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
        lock_fh.close()


def _skip(reason: str) -> str:
    log("skip: " + reason)
    return "skip: " + reason


# ------------------------------------------------------------------ commands

def cmd_status(cfg: Dict[str, Any]) -> None:
    rt = load_runtime()
    prog = load_programme(cfg)
    wp = select_work_package(prog)
    hb = read_json(state_dir() / "heartbeat.json", {})
    print(json.dumps({
        "enabled": cfg.get("enabled", True) and not (state_dir() / "DISABLED").exists(),
        "status": rt.get("status"),
        "paused_until": iso(rt.get("paused_until")),
        "consecutive_failures": rt.get("consecutive_failures"),
        "current": rt.get("current"),
        "last_run": {k: (rt.get("last_run") or {}).get(k) for k in ("wp", "outcome", "session_id", "resets_at")},
        "runs_last_24h": runs_last_24h(rt, now_ts()),
        "windows": {k: {"utilization": v.get("utilization"), "resets": iso(v.get("resetsAt")),
                        "seen": iso(v.get("seen"))} for k, v in (rt.get("windows") or {}).items()},
        "heartbeat": {"wp": hb.get("wp"), "at": iso(hb.get("ts")), "session_id": hb.get("session_id")},
        "next_candidate": wp and {"id": wp.get("id"), "status": wp.get("status"), "next_step": wp.get("next_step")},
        "launchd_loaded": launchd_loaded(),
    }, indent=1, ensure_ascii=False))


def launchd_loaded() -> Optional[bool]:
    try:
        r = subprocess.run(["launchctl", "print", "gui/%d/%s" % (os.getuid(), LABEL)], capture_output=True, timeout=10)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return None


def plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / ("%s.plist" % LABEL)


def render_plist(cfg: Dict[str, Any], label: str = LABEL, args: Optional[List[str]] = None,
                 run_at_load: bool = False, interval: Optional[int] = None) -> str:
    script = Path(__file__).resolve()
    argv = ["/usr/bin/python3", str(script)] + (args or ["tick"])
    sd = state_dir()
    items = "".join("<string>%s</string>" % a for a in argv)
    interval_xml = "<key>StartInterval</key><integer>%d</integer>" % interval if interval else ""
    return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
            "<plist version=\"1.0\"><dict>"
            "<key>Label</key><string>%s</string>"
            "<key>ProgramArguments</key><array>%s</array>"
            "%s<key>RunAtLoad</key><%s/>"
            "<key>ProcessType</key><string>Background</string>"
            "<key>LowPriorityIO</key><true/>"
            "<key>StandardOutPath</key><string>%s</string>"
            "<key>StandardErrorPath</key><string>%s</string>"
            "</dict></plist>\n") % (label, items, interval_xml, "true" if run_at_load else "false",
                                     sd / ("%s.out.log" % label), sd / ("%s.err.log" % label))


def cmd_install(cfg: Dict[str, Any]) -> None:
    p = plist_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_plist(cfg, interval=int(cfg["interval_s"])))
    domain = "gui/%d" % os.getuid()
    subprocess.run(["launchctl", "bootout", "%s/%s" % (domain, LABEL)], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", domain, str(p)], capture_output=True, text=True)
    print("installed %s (rc=%s %s)" % (p, r.returncode, r.stderr.strip()))


def cmd_uninstall() -> None:
    subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), LABEL)], capture_output=True)
    if plist_path().exists():
        plist_path().unlink()
    print("uninstalled %s" % LABEL)


def cmd_smoke(cfg: Dict[str, Any]) -> int:
    """Harmless real call + resume of the same session. Writes smoke.json."""
    sid = str(uuid.uuid4())
    token = "AUTONOMY_SMOKE_%s" % sid[:8].upper()
    base = [claude_bin(cfg), "-p", "--output-format", "stream-json", "--verbose",
            "--permission-mode", "manual", "--permission-prompts", "none", "--tools", "",
            "--no-chrome", "--name", "em-autonomy-smoke"]
    first = subprocess.run(base[:2] + ["Reply with exactly this token and nothing else: %s" % token] + base[2:] +
                           ["--session-id", sid], capture_output=True, text=True, timeout=300,
                           cwd=str(state_dir()), env=child_env(cfg))
    r1 = classify(first.returncode, False, first.stdout, first.stderr)
    second = subprocess.run(base[:2] + ["Which exact token did you reply with in your previous answer? Reply with "
                                        "the token only."] + base[2:] + ["--resume", sid],
                            capture_output=True, text=True, timeout=300, cwd=str(state_dir()), env=child_env(cfg))
    r2 = classify(second.returncode, False, second.stdout, second.stderr)
    res1, _ = parse_stream(first.stdout)
    res2, _ = parse_stream(second.stdout)
    ok = (r1["outcome"] == "success" and r2["outcome"] == "success" and token in ((res1 or {}).get("result") or "")
          and token in ((res2 or {}).get("result") or ""))
    def _rc(cmd: List[str]) -> Optional[int]:
        try:
            return subprocess.run(cmd, capture_output=True, timeout=60, env=child_env(cfg),
                                  cwd=str(xp(cfg["control_worktree"]))).returncode
        except (OSError, subprocess.SubprocessError):
            return None
    git_rc = _rc(["git", "ls-remote", "--heads", "origin", "main"])
    gh_rc = _rc(["gh", "auth", "status"])
    ok = ok and git_rc == 0 and gh_rc == 0
    report = {"at": iso(now_ts()), "ok": ok, "token": token, "session_id": sid,
              "git_remote_rc": git_rc, "gh_auth_rc": gh_rc,
              "launched_by_launchd": bool(os.environ.get("XPC_SERVICE_NAME", "").startswith(LABEL)),
              "first": {k: r1.get(k) for k in ("outcome", "rc", "num_turns", "last_limit")},
              "resume": {k: r2.get(k) for k in ("outcome", "rc", "num_turns")},
              "first_result": (res1 or {}).get("result"), "resume_result": (res2 or {}).get("result"),
              "stderr_tail": (first.stderr + second.stderr)[-400:]}
    write_json(state_dir() / "smoke.json", report)
    rt = load_runtime()
    record_windows(rt, r1.get("last_limit"))
    save_runtime(rt)
    log("smoke ok=%s" % ok)
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 0 if ok else 1


def cmd_launchd_smoke(cfg: Dict[str, Any]) -> int:
    """Run `smoke` once through launchd (RunAtLoad) to prove auth, PATH and
    keychain access work in the agent context; then remove the test job."""
    label = LABEL + ".smoketest"
    plist = state_dir() / ("%s.plist" % label)
    plist.write_text(render_plist(cfg, label=label, args=["smoke"], run_at_load=True))
    smoke = state_dir() / "smoke.json"
    before = smoke.stat().st_mtime if smoke.exists() else 0.0
    domain = "gui/%d" % os.getuid()
    subprocess.run(["launchctl", "bootout", "%s/%s" % (domain, label)], capture_output=True)
    r = subprocess.run(["launchctl", "bootstrap", domain, str(plist)], capture_output=True, text=True)
    if r.returncode != 0:
        print("bootstrap failed: %s" % r.stderr.strip())
        return 1
    deadline = now_ts() + 300
    while now_ts() < deadline and not (smoke.exists() and smoke.stat().st_mtime > before):
        time.sleep(3)
    time.sleep(1)
    subprocess.run(["launchctl", "bootout", "%s/%s" % (domain, label)], capture_output=True)
    plist.unlink()
    rep = read_json(smoke, {})
    ok = bool(rep.get("ok")) and bool(rep.get("launched_by_launchd")) and smoke.stat().st_mtime > before
    log("launchd smoke ok=%s" % ok)
    print(json.dumps({"ok": ok, "launched_by_launchd": rep.get("launched_by_launchd"), "token": rep.get("token"),
                      "resume_result": rep.get("resume_result"), "git_remote_rc": rep.get("git_remote_rc"),
                      "gh_auth_rc": rep.get("gh_auth_rc")}, indent=1))
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("tick", "status", "enable", "disable", "reset", "install", "uninstall", "smoke", "launchd-smoke"):
        sub.add_parser(name)
    hb = sub.add_parser("heartbeat")
    hb.add_argument("--session", default=None)
    hb.add_argument("--wp", default=None)
    hb.add_argument("--hold-min", type=float, default=0.0,
                    help="lead stays authoritative this long even without new heartbeats (max 360)")
    a = ap.parse_args(argv)
    cfg = load_config()
    sd = state_dir()
    if a.cmd == "tick":
        print(tick(cfg))
    elif a.cmd == "status":
        cmd_status(cfg)
    elif a.cmd == "heartbeat":
        hold = min(max(a.hold_min, 0.0), 360.0)
        write_json(sd / "heartbeat.json", {"ts": now_ts(), "session_id": a.session, "wp": a.wp,
                                           "hold_until": now_ts() + hold * 60 if hold else None})
        print("heartbeat %s wp=%s hold_until=%s" % (iso(now_ts()), a.wp, iso(now_ts() + hold * 60) if hold else None))
    elif a.cmd == "disable":
        (sd / "DISABLED").write_text(iso(now_ts()) + "\n")
        print("disabled")
    elif a.cmd == "enable":
        if (sd / "DISABLED").exists():
            (sd / "DISABLED").unlink()
        print("enabled")
    elif a.cmd == "reset":
        rt = load_runtime()
        rt.update(status="IDLE", consecutive_failures=0, paused_until=None)
        rt.pop("current", None)
        save_runtime(rt)
        log("reset by operator")
        print("reset")
    elif a.cmd == "install":
        cmd_install(cfg)
    elif a.cmd == "uninstall":
        cmd_uninstall()
    elif a.cmd == "smoke":
        return cmd_smoke(cfg)
    elif a.cmd == "launchd-smoke":
        return cmd_launchd_smoke(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
