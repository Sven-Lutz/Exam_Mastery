"""Local, evidence-honest learning-event audit for the four-product experience.

Events are generated in the existing offline interactive product, never
uploaded. They record actions, not the learner's response text. Free-text
work is always UNVERIFIED: no status here claims correctness, mastery or a
spaced-repetition schedule. Reuses semantic assessment IDs.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json

SCHEMA = "em-practice-evidence-v1"
MAX_EVENTS = 10000
MAX_RESPONSE_CHARS = 20000
TYPES = {"attempt", "hint", "solution_reveal"}


class EvidenceError(ValueError):
    """An invalid or ambiguous learner log must not produce a competence claim."""


def assessment_revision(unit):
    """Bind a local evidence log to the assessment wording and rubric version."""
    items = [{
        "id": t["id"], "prompt": t["prompt"], "solution": t["solution"],
        "rubric": t["rubric"], "hints": t.get("hints", []),
        "competency_ids": t["competency_ids"],
    } for t in unit["assessments"]]
    payload = {"unit_id": unit["unit_id"],
               "assessments": sorted(items, key=lambda t: t["id"])}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise EvidenceError("event.at must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError("event.at must be valid ISO-8601 UTC") from exc
    if parsed.utcoffset().total_seconds() != 0:
        raise EvidenceError("event.at must be UTC")
    return parsed


def summarize(log, unit):
    """Strict audit and conservative per-assessment evidence summary.

    Only the *order* of events is used for assistance attribution. Timestamps
    are recorded for later analysis, but elapsed time or a delayed retest is
    not inferred from a browser clock. Real correctness needs independent
    grading and a distinct assessment protocol.
    """
    if not isinstance(log, dict) or set(log) != {"schema", "unit_id", "assessment_revision", "events"}:
        raise EvidenceError("expected exact schema, unit_id, assessment_revision, events keys")
    if log["schema"] != SCHEMA or log["unit_id"] != unit.get("unit_id"):
        raise EvidenceError("wrong event schema or learning unit")
    if log["assessment_revision"] != assessment_revision(unit):
        raise EvidenceError("assessment revision differs: never reuse progress on changed tasks")
    events = log["events"]
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise EvidenceError("events must be a bounded list")

    tasks = {t["id"]: t for t in unit.get("assessments", [])}
    if not tasks:
        raise EvidenceError("learning unit has no assessments")
    evidence = {
        key: {
            "status": "NOT_ATTEMPTED", "attempts": 0, "hints": 0,
            "solutions_viewed": 0, "independent_attempts_before_help": 0,
            "assisted_attempts": 0, "ever_helped": False,
        }
        for key in tasks
    }
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise EvidenceError(f"events[{index}]: expected object")
        kind = event.get("type")
        if kind not in TYPES:
            raise EvidenceError(f"events[{index}]: unknown event type")
        permitted = {"type", "task_id", "at"}
        if kind == "attempt":
            permitted.add("response_chars")
        if kind == "hint":
            permitted.add("hint_index")
        if set(event) != permitted:
            raise EvidenceError(f"events[{index}]: unknown or missing fields")
        task_id = event["task_id"]
        if not isinstance(task_id, str) or task_id not in tasks:
            raise EvidenceError(f"events[{index}]: unknown assessment ID")
        _timestamp(event["at"])
        state = evidence[task_id]
        if kind == "attempt":
            length = event["response_chars"]
            if type(length) is not int or not 1 <= length <= MAX_RESPONSE_CHARS:
                raise EvidenceError(f"events[{index}]: invalid response length")
            state["attempts"] += 1
            if state["ever_helped"]:
                state["assisted_attempts"] += 1
                state["status"] = "ASSISTED_ATTEMPT_UNVERIFIED"
            else:
                state["independent_attempts_before_help"] += 1
                state["status"] = "ATTEMPTED_UNVERIFIED"
            continue
        if state["attempts"] == 0:
            raise EvidenceError(f"events[{index}]: help or solution before an attempt")
        if kind == "hint":
            hints = tasks[task_id].get("hints") or []
            hint_index = event["hint_index"]
            if (
                type(hint_index) is not int
                or hint_index != state["hints"]
                or hint_index >= len(hints)
            ):
                raise EvidenceError(f"events[{index}]: hint index out of order")
            state["hints"] += 1
        else:
            if state["solutions_viewed"]:
                raise EvidenceError(f"events[{index}]: solution already revealed")
            state["solutions_viewed"] += 1
        state["ever_helped"] = True
        state["status"] = (
            "SOLUTION_VIEWED" if kind == "solution_reveal"
            else "HINT_USED_UNVERIFIED"
        )

    return {
        "schema": "em-practice-summary-v1",
        "unit_id": unit["unit_id"],
        "events_checked": len(events),
        "assessments": evidence,
        "correctness": "NOT_EVALUATED",
        "mastery": "NOT_EVALUATED",
        "interpretation": (
            "Attempts and assistance are observations, not proof of "
            "correctness, transfer, retention or mastery."
        ),
        "review_scheduler": "ANKI_ONLY",
    }
