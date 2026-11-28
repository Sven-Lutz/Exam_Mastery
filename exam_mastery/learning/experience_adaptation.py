"""Reuse the existing adaptive policy with conservative four-product evidence.

The new offline experience records *actions*, not answers. Without a response
and an explicit deterministic authoring oracle, every attempt remains
UNVERIFIED. This module bridges assessment IDs into learning.policy, not a
second spaced-repetition engine, grader or mastery estimator.

Optional responses are supplied transiently by a trusted local caller. They
are never written into browser evidence and are never returned. Grading against
an author-specified numeric oracle is formative, not independent scientific
verification. No scenario here can certify long-term retention or MASTERED.
"""
from __future__ import annotations

from . import diagnose, policy
from .experience import validate
from .experience_evidence import EvidenceError, summarize
from .experience_misconceptions import to_policy_categories


SCHEMA = "em-experience-adaptive-recommendation-v1"


def _as_answer_indices(answers, events):
    if answers is None:
        return {}
    if not isinstance(answers, dict):
        raise EvidenceError("answers must map event indexes to ephemeral strings")
    result = {}
    for raw_index, answer in answers.items():
        if type(raw_index) is int:
            idx = raw_index
        elif isinstance(raw_index, str) and raw_index.isascii() and raw_index.isdecimal():
            idx = int(raw_index)
        else:
            raise EvidenceError("answers: invalid event index")
        if idx < 0 or idx >= len(events) or events[idx]["type"] != "attempt":
            raise EvidenceError("answers: index is not an attempt event")
        if idx in result:
            raise EvidenceError("answers: duplicate event index")
        if not isinstance(answer, str) or not answer.strip() or len(answer.strip()) > 20000:
            raise EvidenceError("answers: nonempty bounded response required")
        if len(answer.strip()) != events[idx]["response_chars"]:
            raise EvidenceError("answers: response length and exported event differ")
        result[idx] = answer.strip()
    return result


def track_for_unit(unit):
    """Minimum legacy-policy contract; no fabricated diagnoses or knowledge."""
    tasks = []
    for task in unit["assessments"]:
        refs = task["competency_ids"]
        # Multi-competency free-text submissions are never locally graded.
        # Policy uses the primary KC only for navigation, not competence credit.
        tasks.append({
            "id": task["id"], "kc_id": refs[0], "title": task["prompt"],
            "role": task.get("role", "core"),
        })
    return {
        "flow": [t["id"] for t in tasks],
        "tasks": tasks, "kcs": [{"id": k["id"]} for k in unit["competencies"]],
        "categories": to_policy_categories(unit), "worked_examples": {}, "anki_tags": [],
    }


def _diagnosis(task, answer):
    """Evaluate only a declared numeric checker using legacy diagnose.py."""
    checker = task.get("machine_check")
    if checker is None or answer is None:
        return {
            "task_id": task["id"], "result": "unverified",
            "error_category": None, "method": "open",
            "evidence": "UNVERIFIED",
        }
    if checker["type"] != "numeric" or len(task["competency_ids"]) != 1:
        raise EvidenceError("unsupported formative grader")
    item = {
        **checker, "id": task["id"],
        "kc_id": task["competency_ids"][0],
    }
    computed = diagnose.diagnose(item, answer)
    # Only machine-check decision fields reach the policy; no answer text.
    return {
        "task_id": task["id"], "result": computed["result"],
        "error_category": computed["error_category"],
        "method": computed["method"], "evidence": computed["evidence"],
    }


def recommend(unit, log, answers=None):
    """Return next-step advice, never an independently validated mastery score.

    `answers` optionally maps attempt event indexes to transient responses,
    e.g. {0: "5"}. The function checks event alignment and discards responses
    after computation. A browser-only log never earns correctness credit.
    """
    checked = validate(unit)
    if not checked["valid"]:
        raise EvidenceError("invalid learning unit: " + "; ".join(checked["errors"]))
    audit = summarize(log, unit)
    events = log["events"]
    provided = _as_answer_indices(answers, events)
    tasks = {task["id"]: task for task in unit["assessments"]}
    policy_events = []
    locally_checked = 0
    unverifiable = 0
    recent_grade = None
    for index, event in enumerate(events):
        task_id = event["task_id"]
        if event["type"] == "attempt":
            diagnosis = _diagnosis(tasks[task_id], provided.get(index))
            if diagnosis["evidence"] == "UNVERIFIED":
                unverifiable += 1
            else:
                locally_checked += 1
            recent_grade = diagnosis
            policy_events.append({
                "type": "attempt", "task": task_id, "t": event["at"],
                "diagnosis": diagnosis,
            })
        else:
            policy_events.append({
                "type": "hint" if event["type"] == "hint" else "solution",
                "task": task_id, "t": event["at"],
            })

    # Same policy as the existing learning engine, not a replacement.
    decision = policy.decide(track_for_unit(unit), policy_events)
    review_required = bool(
        recent_grade is not None and recent_grade["result"] == "unverified"
    )
    # An open written proof must not silently graduate to the next task. The
    # legacy policy RL5 says 'continue' but cannot judge that proof; we expose
    # its reasoning and withhold competence-based advancement.
    suggested = (
        recent_grade["task_id"] if review_required
        else decision["next_task"]
    )
    return {
        "schema": SCHEMA,
        "unit_id": unit["unit_id"],
        "policy": decision,
        "recommended_task": suggested,
        "requires_human_or_tutor_review": review_required,
        "locally_checked_attempts": locally_checked,
        "unverified_attempts": unverifiable,
        "evidence": audit,
        "mastery": "NOT_EVALUATED",
        "correctness_scope": (
            "LOCAL_FORMATIVE_ONLY: numeric checks use author-specified "
            "expected values; written answers remain UNVERIFIED. "
            "No independent subject or retention assessment."
        ),
    }
