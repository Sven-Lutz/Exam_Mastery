"""Mastery evidence ledger (mastery-ledger-v1) and progress summary (mastery-progress-v1). Pure, offline, no scores.

One derived read model over every learner store of a Mastery origin: workbench tracks (em-tutor-v1), explorable
practice (em-practice-v1: decision log `policy` plus its privacy-reduced mirror `events`), Mastery Motion
(em-motion-v1) and the chapter app (em-learn-v2). The stores are never migrated or changed; the ledger is rebuilt from
them on every call and is reproducible from a backup. Every ledger event points back to its origin
(`store#record#list#index`). Unknown event types are kept and labelled; engine decisions and mirror duplicates are
excluded and counted, so `read == included + excluded` per store.

The progress summary derives per competency the observed state and evidence basis with the tested policy
(learning/policy.py, mirrored by em_tutor.js) plus plain counts. Never a percentage, never a mastery score.
`templates/mastery_ledger.js` is the browser mirror; tests require equal output for equal input.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..learning import policy as P

LEDGER_SCHEMA = "mastery-ledger-v1"
PROGRESS_SCHEMA = "mastery-progress-v1"
RULES = "mastery-ledger-rules-v1"
STORES = ("em-tutor-v1", "em-practice-v1", "em-motion-v1", "em-learn-v2")
HELP = tuple(P.ASSIST_EVENTS)                       # hint, solution, tutor, guided, support
MIRROR = {"attempt": "attempt", "hint": "hint", "solution_reveal": "solution", "tutor_brief": "tutor",
          "guided_help": "guided"}
MIRROR_WINDOW_MS = 2000
FUTURE_SKEW_MS = P.FUTURE_SKEW_MINUTES * 60_000
GAP_MS = P.RETENTION_MIN_GAP_HOURS * 3_600_000
HELP_WINDOW_MS = P.KC_HELP_WINDOW_HOURS * 3_600_000
RECOGNITION = tuple(P.RECOGNITION_TYPES)
SOURCES = ("deterministic", "agent_judgement", "self_report")
LEARN_KIND = {"attempt": "attempt", "hint": "help", "solution": "help", "tutor": "help", "section_open": "view",
              "card": "self_rating", "exam_start": "exam", "exam_submit": "exam", "exam_self_score": "exam"}
MOTION_KIND = {"predict": "prediction", "reveal": "reveal", "task_attempt": "mission"}
FIELDS = ("id", "store", "record", "list", "i", "t", "at", "t_quality", "archived", "product", "course", "chapter",
          "unit", "task", "task_type", "competency", "help_kc", "type", "kind", "help", "result", "assist", "source",
          "role", "state_input", "note")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
TS = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,9}))?)?(Z|[+-]\d{2}:\d{2})?)?$")


# ------------------------------------------------------------------ time (same rules as mastery_ledger.js)

def stamp(t, now_ms):
    """(milliseconds since epoch or None, quality). Quality: exact, date_only, missing, invalid, future."""
    if not isinstance(t, str):
        return None, "missing"
    m = TS.match(t)
    if not m:
        return None, "invalid"
    y, mo, d, hh, mi, ss, frac, tz = m.groups()
    try:
        if int(y) < 1:
            raise ValueError
        base = datetime(int(y), int(mo), int(d), int(hh or 0), int(mi or 0), int(ss or 0),
                        int((frac or "0")[:3].ljust(3, "0")) * 1000, tzinfo=timezone.utc)
    except ValueError:
        return None, "invalid"
    if tz and tz != "Z":
        offset = timedelta(hours=int(tz[1:3]), minutes=int(tz[4:6]))
        base = base - offset if tz[0] == "+" else base + offset
    ms = (base - EPOCH) // timedelta(milliseconds=1)
    if ms > now_ms + FUTURE_SKEW_MS:
        return ms, "future"
    return ms, ("exact" if hh is not None else "date_only")


def iso(ms):
    return (EPOCH + timedelta(milliseconds=ms)).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _now_ms(now):
    if now is None:
        return (datetime.now(timezone.utc) - EPOCH) // timedelta(milliseconds=1)
    ms, quality = stamp(now, float("inf"))
    if ms is None:
        raise ValueError("now must be an ISO timestamp")
    return ms


def _role(r):
    if r is None:
        return None
    return "retest" if r == "retest" else "evidence" if r in ("similar", "transfer") else "practice"


def _str(v):
    return v if isinstance(v, str) else None


def _dict(v):
    return v if isinstance(v, dict) else {}


def _list(v):
    return v if isinstance(v, list) else []


# ------------------------------------------------------------------ catalog (library.json with track data)

def load_catalog(root):
    """library.json of a built MASTERY_HOME with every track's JSON attached as `data` (as the home page does)."""
    root = Path(root)
    lib = json.loads((root / "library.json").read_text(encoding="utf-8"))
    for u in lib.get("units", []):
        for tr in u.get("tracks", []):
            tr["data"] = json.loads((root / tr["json"]).read_text(encoding="utf-8"))
    return lib


def _index(catalog):
    tracks, units = {}, {}
    for u in (catalog or {}).get("units", []):
        units.setdefault(u["practice_store"]["unit_id"], u)
        for tr in u.get("tracks", []):
            if tr.get("data"):
                tracks.setdefault(tr["store_key"], (u, tr))
    return tracks, units


def _where(u):
    if not u:
        return {"unit": None, "course": None, "chapter": None}
    return {"unit": u["slug"], "course": (u.get("course") or {}).get("slug"), "chapter": (u.get("chapter") or {}).get("id")}


# ------------------------------------------------------------------ ledger

class _Acc:
    def __init__(self, now_ms):
        self.now_ms, self.events, self.stores = now_ms, [], {}

    def store(self, name, present):
        self.stores[name] = {"store": name, "present": present, "records": 0, "read": 0, "included": 0, "excluded": {}}
        return self.stores[name]

    def exclude(self, name, reason):
        s = self.stores[name]
        s["read"] += 1
        s["excluded"][reason] = s["excluded"].get(reason, 0) + 1

    def add(self, **kw):
        ms, quality = stamp(kw.get("t"), self.now_ms)
        ev = {k: kw.get(k) for k in FIELDS}
        ev["t"] = _str(kw.get("t"))
        ev["at"] = iso(ms) if ms is not None else None
        ev["t_quality"] = quality
        ev["archived"] = bool(kw.get("archived"))
        ev["state_input"] = False
        ev["_ms"] = ms
        ev["id"] = f'{kw["store"]}#{kw["record"]}#{kw["list"]}#{kw["i"]}'
        s = self.stores[kw["store"]]
        s["read"] += 1
        s["included"] += 1
        self.events.append(ev)
        return ev


def _policy_event(acc, store, record, lst, i, e, T, where, product, archived, scope_ok):
    """One workbench/explorable decision-log event."""
    typ = e["type"]
    task = _str(e.get("task"))
    td = T.get(task) if task else None
    kind = "attempt" if typ == "attempt" else "help" if typ in HELP else "unknown"
    diag = e.get("diagnosis") if isinstance(e.get("diagnosis"), dict) else None
    result = _str(diag.get("result")) if diag else _str(e.get("result")) if typ == "guided" else None
    help_kc = _str(e.get("kc")) if kind == "help" else None
    if kind == "attempt":
        source = "unjudged" if result == "unverified" else "deterministic" if result else None
        task_type = (td or {}).get("type") or (_str(diag.get("method")) if diag else None)
    elif kind == "help":
        source = e["source"] if e.get("source") in SOURCES else "agent_judgement" if typ == "tutor" else "deterministic"
        task_type = (td or {}).get("type")
    else:
        source, task_type = None, (td or {}).get("type")
    note = None
    if kind == "unknown":
        note = "unbekannter Ereignistyp – unverändert übernommen, zählt nirgends"
    elif not scope_ok:
        note = ("frühere Aufgabenfassung – nur in der Zeitleiste" if archived else
                "Übungsstrecke nicht in der Bibliothek – nur in der Zeitleiste")
    ev = acc.add(store=store, record=record, list=lst, i=i, t=e.get("t"), archived=archived, product=product, **where,
                 task=task, task_type=task_type, competency=help_kc or (td or {}).get("kc_id"), help_kc=help_kc,
                 type=typ, kind=kind, help=typ if kind == "help" else None, result=result, source=source,
                 role=_role((td or {}).get("role")), note=note)
    ev["_task_kc"] = (td or {}).get("kc_id")
    ev["_valid_attempt"] = kind == "attempt" and result is not None
    return ev


def _assist(evs):
    """Assisted/unassisted per attempt of one record (same rule as policy.helped and policy._kc_helped)."""
    seq = [e for e in evs if e["kind"] in ("attempt", "help") and e["t_quality"] in ("exact", "date_only")]
    for j, e in enumerate(seq):
        if e["kind"] != "attempt":
            continue
        prev = seq[:j]
        task_help = any(p["kind"] == "help" and p["task"] == e["task"] for p in prev)
        kc = e["_task_kc"]
        kc_help = kc is not None and any(p["kind"] == "help" and (p["_task_kc"] == kc or p["help_kc"] == kc)
                                         and e["_ms"] - p["_ms"] <= HELP_WINDOW_MS for p in prev)
        e["assist"] = "assisted" if task_help or kc_help else "unassisted"


def _mirror_matches(policy_evs, mirror):
    """Indices of mirror events that duplicate a decision-log event (same task, type, within 2 s)."""
    used, dup = set(), set()
    for i, m in mirror:
        typ = MIRROR.get(m["type"])
        ms, _ = stamp(m.get("at"), float("inf"))
        if not typ or ms is None:
            continue
        for k, p in enumerate(policy_evs):
            if k in used or p["type"] != typ or p["task"] != _str(m.get("task_id")) or p["_ms"] is None:
                continue
            if abs(p["_ms"] - ms) <= MIRROR_WINDOW_MS:
                used.add(k)
                dup.add(i)
                break
    return dup


def build_ledger(storage, catalog, now=None):
    """Merge every learner store into one ordered, provenance-labelled event list (mastery-ledger-v1)."""
    storage = storage or {}
    now_ms = _now_ms(now)
    acc = _Acc(now_ms)
    tracks, units = _index(catalog)

    # workbench tracks
    tutor = storage.get("em-tutor-v1")
    s = acc.store("em-tutor-v1", isinstance(tutor, dict))
    for key, rec in sorted(_dict(_dict(tutor).get("tracks")).items()):
        s["records"] += 1
        u, tref = tracks.get(key, (None, None))
        T = {t["id"]: t for t in tref["data"]["tasks"]} if tref else {}
        evs = []
        for i, e in enumerate(_list(_dict(rec).get("events"))):
            if not isinstance(e, dict) or not isinstance(e.get("type"), str):
                acc.exclude("em-tutor-v1", "malformed"); continue
            if e["type"] == "decision":
                acc.exclude("em-tutor-v1", "engine_decision"); continue
            evs.append(_policy_event(acc, "em-tutor-v1", key, "events", i, e, T, _where(u), "workbench", False, bool(tref)))
        _assist(evs)
        _mark_state(evs, bool(tref), T)

    # explorable practice
    practice = storage.get("em-practice-v1")
    s = acc.store("em-practice-v1", isinstance(practice, dict))
    if isinstance(practice, dict):
        recs = [(k, r, False) for k, r in sorted(_dict(practice.get("units")).items())]
        recs += [(k, r, True) for k, r in sorted(_dict(practice.get("archived")).items())]
        for key, rec, archived in recs:
            s["records"] += 1
            if not isinstance(rec, dict):
                continue
            uid = key.rsplit("@", 1)[0] if archived else key
            u = units.get(uid)
            stale = bool(u) and not archived and rec.get("assessment_revision") != u["practice_store"]["assessment_revision"]
            arch = archived or stale
            T = {t["id"]: t for t in u["adaptive_track"]["tasks"]} if u else {}
            scope_ok = bool(u) and not arch
            evs = []
            for i, e in enumerate(_list(rec.get("policy"))):
                if not isinstance(e, dict) or not isinstance(e.get("type"), str):
                    acc.exclude("em-practice-v1", "malformed"); continue
                evs.append(_policy_event(acc, "em-practice-v1", key, "policy", i, e, T, _where(u), "explorable", arch, scope_ok))
            _assist(evs)
            _mark_state(evs, scope_ok, T)
            mirror = []
            for i, m in enumerate(_list(rec.get("events"))):
                if not isinstance(m, dict) or not isinstance(m.get("type"), str):
                    acc.exclude("em-practice-v1", "malformed"); continue
                mirror.append((i, m))
            dup = _mirror_matches(evs, mirror)
            for i, m in mirror:
                if i in dup:
                    acc.exclude("em-practice-v1", "mirror_duplicate"); continue
                typ = MIRROR.get(m["type"])
                task = _str(m.get("task_id"))
                td = T.get(task) if task else None
                kind = "attempt" if typ == "attempt" else "help" if typ in HELP else "unknown"
                acc.add(store="em-practice-v1", record=key, list="events", i=i, t=m.get("at"), archived=arch,
                        product="explorable", **_where(u), task=task, task_type=None,
                        competency=(td or {}).get("kc_id"), type=m["type"], kind=kind,
                        help=typ if kind == "help" else None,
                        source="unjudged" if kind == "attempt" else None if kind == "unknown" else
                        "agent_judgement" if typ == "tutor" else "deterministic",
                        role=_role((td or {}).get("role")),
                        note="nur im Aktionsprotokoll (em-practice-evidence-v1), ohne Gegenstück im Entscheidungsprotokoll"
                        " – nur in der Zeitleiste")

    # Mastery Motion
    motion = storage.get("em-motion-v1")
    s = acc.store("em-motion-v1", isinstance(motion, dict))
    if isinstance(motion, dict):
        recs = [(k, r, False) for k, r in sorted(_dict(motion.get("scenes")).items())]
        recs += [(k, r, True) for k, r in sorted(_dict(motion.get("archived")).items())]
        for key, rec, archived in recs:
            s["records"] += 1
            for i, e in enumerate(_list(_dict(rec).get("events"))):
                if not isinstance(e, dict) or not isinstance(e.get("type"), str):
                    acc.exclude("em-motion-v1", "malformed"); continue
                kind = MOTION_KIND.get(e["type"], "unknown")
                if kind == "prediction":
                    result = "correct" if e.get("correct") is True else "incorrect" if e.get("correct") is False else None
                elif kind == "mission":
                    result = "met" if e.get("met") is True else "not_met" if e.get("met") is False else None
                elif kind == "reveal":
                    result = "skipped_prediction" if e.get("skipped") is True else None
                else:
                    result = None
                acc.add(store="em-motion-v1", record=key, list="events", i=i, t=e.get("t"), archived=archived,
                        product="motion", unit=None, course=None, chapter=None,
                        task=_str(e.get("question")) or _str(e.get("mission")) or _str(e.get("step")),
                        type=e["type"], kind=kind, result=result,
                        source="deterministic" if result in ("correct", "incorrect", "met", "not_met") else None,
                        role="practice" if kind != "unknown" else None,
                        note="Lernhandlung, kein Kompetenznachweis" if kind != "unknown"
                        else "unbekannter Ereignistyp – unverändert übernommen, zählt nirgends")

    # chapter app (learn app)
    learn = storage.get("em-learn-v2")
    s = acc.store("em-learn-v2", isinstance(learn, dict))
    if isinstance(learn, dict):
        helped = {}
        records = set()
        for i, e in enumerate(_list(learn.get("events"))):
            if not isinstance(e, dict) or not isinstance(e.get("type"), str):
                acc.exclude("em-learn-v2", "malformed"); continue
            record = "chapter:" + (_str(e.get("chapter")) or "?")
            records.add(record)
            kind = LEARN_KIND.get(e["type"], "unknown")
            item = _str(e.get("item"))
            mode = e.get("mode")
            source = ("deterministic" if mode == "number" else "self_report" if mode == "self" else None) if kind == "attempt" \
                else "self_report" if kind == "self_rating" or e["type"] == "exam_self_score" \
                else "deterministic" if kind == "help" else None
            ev = acc.add(store="em-learn-v2", record=record, list="events", i=i, t=e.get("t"), product="chapter_app",
                         unit=None, course=None, chapter=None, task=item or _str(e.get("card")) or _str(e.get("section")),
                         type=e["type"], kind=kind, help=e["type"] if kind == "help" else None,
                         result=_str(e.get("result")), source=source,
                         note="Kapitel-App: ohne Kompetenzzuordnung in Mastery – nur in der Zeitleiste" if kind != "unknown"
                         else "unbekannter Ereignistyp – unverändert übernommen, zählt nirgends")
            if kind == "help" and item:
                helped[(record, item)] = True
            if kind == "attempt":
                ev["assist"] = "assisted" if helped.get((record, item)) else "unassisted"
        s["records"] = len(records)

    order = {name: k for k, name in enumerate(STORES)}
    acc.events.sort(key=lambda e: (e["_ms"] is None, e["_ms"] if e["_ms"] is not None else 0, order[e["store"]],
                                   e["record"], e["list"], e["i"]))
    events = []
    for e in acc.events:
        events.append({k: e[k] for k in FIELDS})
    return {"schema": LEDGER_SCHEMA, "rules": RULES, "now": iso(now_ms),
            "stores": [acc.stores[name] for name in STORES], "events": events}


def _mark_state(evs, scope_ok, T):
    """Events that enter the state computation of their scope (policy.kc_status / kc_evidence_basis)."""
    for e in evs:
        e["state_input"] = bool(
            scope_ok and not e["archived"] and e["t_quality"] in ("exact", "date_only")
            and ((e["kind"] == "attempt" and e["_valid_attempt"] and e["task"] in T and e["result"] != "unverified")
                 or (e["kind"] == "help" and (e["task"] in T or e["help_kc"]))))


# ------------------------------------------------------------------ progress summary

def _scopes(catalog):
    out = []
    for u in (catalog or {}).get("units", []):
        for tr in u.get("tracks", []):
            if tr.get("data"):
                out.append({"scope": "workbench:" + tr["store_key"], "product": "workbench", "store": "em-tutor-v1",
                            "record": tr["store_key"], "unit": u, "track": tr["data"], "labels": {},
                            "title": tr.get("label") or tr["data"].get("title")})
        out.append({"scope": "explorable:" + u["practice_store"]["unit_id"], "product": "explorable",
                    "store": "em-practice-v1", "record": u["practice_store"]["unit_id"], "unit": u,
                    "track": u["adaptive_track"], "labels": {c["id"]: c["label"] for c in u.get("competencies", [])},
                    "title": u["title"]})
    seen, uniq = set(), []
    for sc in out:                      # a track listed under two units is one record: count it once (first unit)
        if sc["scope"] not in seen:
            seen.add(sc["scope"])
            uniq.append(sc)
    return uniq


def _raw(e):
    if e["kind"] == "attempt":
        return {"type": "attempt", "task": e["task"], "t": e["at"], "diagnosis": {"result": e["result"]}}
    raw = {"type": e["type"], "task": e["task"], "t": e["at"]}
    if e["help_kc"]:
        raw["kc"] = e["help_kc"]
    return raw


def summarize(ledger, catalog, now=None):
    """Per competency: state, evidence basis, counts, first/latest independent success, delayed success; per chapter:
    which competencies have independent production evidence. Derived only from the ledger and the catalog."""
    now_iso = ledger["now"] if now is None else iso(_now_ms(now))
    by_record = {}
    for e in ledger["events"]:
        by_record.setdefault((e["store"], e["record"]), []).append(e)
    comps = []
    for sc in _scopes(catalog):
        evs = [e for e in by_record.get((sc["store"], sc["record"]), []) if e["list"] != "events" or sc["store"] == "em-tutor-v1"]
        evs = [e for e in evs if not e["archived"]]
        evs.sort(key=lambda e: e["i"])
        state = [e for e in evs if e["state_input"]]
        raw = [_raw(e) for e in state]
        track = sc["track"]
        types = {}
        for e in state:
            if e["kind"] == "attempt" and e["task_type"] and e["task"] not in types:
                types[e["task"]] = e["task_type"]
        aug = dict(track, tasks=[dict(t, type=t.get("type") or types.get(t["id"]) or "open") for t in track["tasks"]])
        status = P.kc_status(aug, raw, today=now_iso)
        basis = P.kc_evidence_basis(aug, raw)
        u = sc["unit"]
        for kc in track["kcs"]:
            kid = kc["id"]
            att = [e for e in evs if e["kind"] == "attempt" and e["competency"] == kid and e["result"] not in (None, "invalid")
                   and e["assist"] is not None]
            refs = {"unassisted": [e["id"] for e in att if e["assist"] == "unassisted"],
                    "assisted": [e["id"] for e in att if e["assist"] == "assisted"],
                    "unverified": [e["id"] for e in att if e["result"] == "unverified"]}
            seen, retries = set(), []
            for e in att:
                if e["task"] in seen:
                    retries.append(e["id"])
                seen.add(e["task"])
            refs["retries"] = retries
            for h in HELP:
                refs[h] = [e["id"] for e in evs if e["kind"] == "help" and e["help"] == h and e["competency"] == kid]
            ind = [e for e in state if e["kind"] == "attempt" and e["competency"] == kid and e["result"] == "correct"
                   and e["assist"] == "unassisted"]
            refs["independent"] = [e["id"] for e in ind]
            ind_t = sorted((stamp(e["at"], float("inf"))[0], e["task"], e["id"]) for e in ind)
            delayed = None
            for t2, k2, id2 in ind_t:
                earlier = [t1 for t1, k1, _ in ind_t if k1 != k2 and t2 - t1 >= GAP_MS]
                if earlier:
                    delayed = {"at": iso(t2), "after_hours": (t2 - min(earlier)) // 3_600_000, "ref": id2}
                    break
            comps.append({
                "scope": sc["scope"], "product": sc["product"], "scope_title": sc["title"], **_where(u),
                "competency": kid, "label": sc["labels"].get(kid) or kc.get("label") or kid,
                "status": status[kid], "basis": basis[kid],
                "counts": {k: len(v) for k, v in refs.items()},
                "first_independent": iso(ind_t[0][0]) if ind_t else None,
                "latest_independent": iso(ind_t[-1][0]) if ind_t else None,
                "delayed": delayed, "refs": refs})
    chapters = []
    rank = {"production": 2, "recognition_only": 1, "none": 0}
    for u in (catalog or {}).get("units", []):
        items = {}
        for c in comps:
            if c["unit"] != u["slug"]:
                continue
            it = items.setdefault(c["competency"], {"competency": c["competency"], "label": c["label"], "basis": "none",
                                                     "attempted": False, "scopes": []})
            it["scopes"].append(c["scope"])
            if rank[c["basis"]] > rank[it["basis"]]:
                it["basis"] = c["basis"]
            it["attempted"] = it["attempted"] or (c["counts"]["unassisted"] + c["counts"]["assisted"]) > 0
        rows = list(items.values())
        chapters.append({**_where(u), "title": u["title"], "items": rows,
                         "with_production": [r["competency"] for r in rows if r["basis"] == "production"],
                         "without_production": [r["competency"] for r in rows if r["basis"] != "production"]})
    motion = {}
    for e in ledger["events"]:
        if e["store"] != "em-motion-v1" or e["archived"]:
            continue
        m = motion.setdefault(e["record"], {"scene": e["record"], "predictions": [], "predictions_correct": [],
                                            "reveals": [], "missions": [], "missions_met": []})
        if e["kind"] == "prediction":
            m["predictions"].append(e["id"])
            if e["result"] == "correct":
                m["predictions_correct"].append(e["id"])
        elif e["kind"] == "reveal":
            m["reveals"].append(e["id"])
        elif e["kind"] == "mission":
            m["missions"].append(e["id"])
            if e["result"] == "met":
                m["missions_met"].append(e["id"])
    return {"schema": PROGRESS_SCHEMA, "rules": RULES, "now": now_iso, "competencies": comps, "chapters": chapters,
            "motion": [motion[k] for k in sorted(motion)]}
