"""Synthetic learner stores and a catalog for the Mastery evidence ledger tests (no private data, no real Anki)."""
import copy
import json
from pathlib import Path

from exam_mastery.learning import diagnose as D, tracks as TR
from exam_mastery.learning.experience_adaptation import track_for_unit
from exam_mastery.learning.experience_evidence import assessment_revision

REPO = Path(__file__).resolve().parents[1]
UNIT = json.loads((REPO / "fixtures" / "experience_attention_reference.json").read_text(encoding="utf-8"))
ML = next(t for t in TR.all_tracks() if t["id"] == "ml/backprop-track")
NOW = "2026-11-28T12:00:00.000Z"
KEY = "mastery|ml/backprop-track"


def _unit_entry(unit, slug, course=None, chapter=None):
    entry = {"slug": slug, "title": unit["title"], "unit_id": unit["unit_id"],
             "practice_store": {"key": "em-practice-v1", "unit_id": unit["unit_id"],
                                "assessment_revision": assessment_revision(unit)},
             "competencies": [{"id": c["id"], "label": c.get("description", c["id"])} for c in unit["competencies"]],
             "assessments": [{"id": a["id"], "role": a.get("role", "core"), "competency_ids": a["competency_ids"],
                              "anchor": "exercise-x", "title": a["id"]} for a in unit["assessments"]],
             "adaptive_track": track_for_unit(unit), "tracks": []}
    if course:
        entry["course"], entry["chapter"] = course, chapter
    return entry


def catalog():
    attention = _unit_entry(UNIT, "attention")
    attention["tracks"] = [{"id": ML["id"], "title": ML["title"], "label": "Backpropagation", "relation": "prerequisite",
                            "href": "units/attention/tracks/x.html", "json": "units/attention/tracks/x.json",
                            "store_key": KEY, "data": ML}]
    chapter_unit = copy.deepcopy(UNIT)
    chapter_unit["unit_id"] = "course/la/ch1"
    chapter = _unit_entry(chapter_unit, "la-ch1", course={"slug": "la", "title": "Lineare Algebra"},
                          chapter={"id": "ch1", "order": 1, "title": "Lineare Abbildungen"})
    return {"schema": "mastery-library-v1", "units": [attention, chapter],
            "motion_demos": [{"id": "plane-map", "title": "Ebene", "claim": "x", "href": "motion/plane-map.html"}]}


def _task(tid):
    return next(t for t in ML["tasks"] if t["id"] == tid)


def _att(tid, answer, t):
    return {"type": "attempt", "task": tid, "diagnosis": D.diagnose(_task(tid), answer), "t": t}


def backprop_history():
    """Day 1: prerequisite wrong then right, core with a hint (assisted), similar right; day 2 (> 20 h): transfer-like
    retest right without help. Engine decisions and an unknown event type are interleaved."""
    pre, core = _task("ml-pre"), _task("ml-core")
    ev = [
        _att("ml-pre", "0,5", "2026-11-26T09:00:00.000Z"),
        {"type": "decision", "task": "ml-pre", "decision": {"rule": "RB"}, "t": "2026-11-26T09:00:01.000Z"},
        _att("ml-pre", str(TR._answer_for(pre)).replace(".", ","), "2026-11-26T09:02:00.000Z"),
        {"type": "hint", "task": "ml-core", "level": 1, "assist_level": "hint_1", "source": "deterministic", "t": "2026-11-26T09:05:00.000Z"},
        _att("ml-core", TR._answer_for(core), "2026-11-26T09:06:00.000Z"),
        {"type": "tutor", "task": "ml-core", "assist_level": "tutor", "source": "agent_judgement", "channel": "copy", "t": "2026-11-26T09:07:00.000Z"},
        {"type": "legacy_note", "t": "2026-11-26T09:08:00.000Z"},
        _att("ml-core", TR._answer_for(core), "2026-11-26T09:09:00.000Z"),
    ]
    for task in ML["tasks"]:
        if task["role"] in ("similar", "retest") and task["kc_id"] == pre["kc_id"]:
            ev.append(_att(task["id"], TR._answer_for(task), "2026-11-27T10:00:00.000Z"))
    pre2 = next((t for t in ML["tasks"] if t["kc_id"] == pre["kc_id"] and t["id"] != "ml-pre"), None)
    if pre2:
        ev.append(_att(pre2["id"], TR._answer_for(pre2), "2026-11-27T10:30:00.000Z"))
    ev.append(_att("ml-pre", "1", "2099-01-01T00:00:00.000Z"))               # future clock: never evidence
    ev.append({"type": "hint", "task": "ml-core", "t": "gestern"})            # unreadable time: timeline only
    return ev


def storage():
    rev = assessment_revision(UNIT)
    rev_ch1 = catalog()["units"][1]["practice_store"]["assessment_revision"]
    return {
        "em-tutor-v1": {"schema": 1, "tracks": {KEY: {"events": backprop_history()},
                                                "standalone|other-track": {"events": [{"type": "hint", "task": "x", "t": "2026-11-20T08:00:00Z"}]}}},
        "em-practice-v1": {"schema": 1, "units": {
            UNIT["unit_id"]: {"assessment_revision": rev, "events": [], "policy": []},   # owner case: explorable empty
            "course/la/ch1": {"assessment_revision": rev_ch1, "events": [
                {"type": "attempt", "task_id": "task/dimensions", "response_chars": 20, "at": "2026-11-27T11:00:00.100Z"},
                {"type": "hint", "task_id": "task/dimensions", "hint_index": 0, "at": "2026-11-27T11:01:00.000Z"},
                {"type": "solution_reveal", "task_id": "task/dimensions", "at": "2026-11-20T11:01:00.000Z"}],
                "policy": [
                {"type": "attempt", "task": "task/dimensions", "t": "2026-11-27T11:00:00.300Z",
                 "diagnosis": {"task_id": "task/dimensions", "result": "unverified", "error_category": None, "method": "open", "evidence": "UNVERIFIED"},
                 "observed": "private text"},
                {"type": "hint", "task": "task/dimensions", "t": "2026-11-27T11:01:00.200Z"}]}},
            "archived": {UNIT["unit_id"] + "@old-revision": {"assessment_revision": "old-revision", "events": [],
                                                              "policy": [{"type": "hint", "task": "task/dimensions", "t": "2026-11-01T10:00:00Z"}]}}},
        "em-motion-v1": {"schema": 1, "scenes": {"plane-map": {"revision": "r1", "events": [
            {"type": "predict", "step": "s1", "question": "q1", "answer": "a", "correct": True, "t": "2026-11-27T12:00:00.000Z"},
            {"type": "predict", "step": "s2", "question": "q2", "answer": "b", "correct": False, "t": "2026-11-27T12:01:00.000Z"},
            {"type": "reveal", "step": "s2", "t": "2026-11-27T12:01:05.000Z"},
            {"type": "task_attempt", "mission": "m1", "met": True, "t": "2026-11-27T12:05:00.000Z"}]}}},
        "em-learn-v2": {"schema": 2, "created": "2026-11-01T00:00:00Z", "prefs": {}, "events": [
            {"t": "2026-11-25T08:00:00.000Z", "chapter": "c1", "type": "section_open", "section": "s1", "kc_ids": ["k"]},
            {"t": "2026-11-25T08:01:00.000Z", "chapter": "c1", "type": "hint", "item": "i1", "n": 1},
            {"t": "2026-11-25T08:02:00.000Z", "chapter": "c1", "type": "attempt", "item": "i1", "result": "correct", "mode": "number"},
            {"t": "2026-11-25T08:03:00.000Z", "chapter": "c1", "type": "attempt", "item": "i2", "result": "partial", "mode": "self"},
            {"t": "2026-11-25T08:04:00.000Z", "chapter": "c1", "type": "card", "card": "k1", "rating": "ja"},
            {"t": "2026-11-25T08:05:00.000Z", "chapter": "c1", "type": "mystery"}]},
    }
