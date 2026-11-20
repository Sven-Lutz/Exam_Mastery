"""Conservative local practice evidence: actions are not correctness or mastery."""
import copy
import json
from pathlib import Path

import pytest

from exam_mastery.learning.experience_evidence import (EvidenceError, SCHEMA, summarize, assessment_revision)


def sample_unit():
    p = Path(__file__).resolve().parents[1] / "fixtures" / "experience_reference.json"
    result = json.loads(p.read_text(encoding="utf-8"))
    result["assessments"][0]["hints"] = ["First hint", "Second hint"]
    return result


@pytest.fixture
def unit():
    return sample_unit()


def event(kind, **extra):
    return {"type": kind, "task_id": "task/prove",
            "at": "2026-11-20T17:55:00.000Z", **extra}


def log(*events, lesson=None):
    source = lesson if lesson is not None else sample_unit()
    return {"schema": SCHEMA, "unit_id": source["unit_id"],
            "assessment_revision": assessment_revision(source),
            "events": list(events)}


def test_no_attempt_means_no_evidence_of_mastery(unit):
    report = summarize(log(), unit)
    state = report["assessments"]["task/prove"]
    assert state["status"] == "NOT_ATTEMPTED"
    assert state["attempts"] == 0
    assert report["correctness"] == report["mastery"] == "NOT_EVALUATED"
    assert report["review_scheduler"] == "ANKI_ONLY"


def test_unassisted_attempt_is_observed_but_not_graded(unit):
    report = summarize(log(event("attempt", response_chars=20)), unit)
    state = report["assessments"]["task/prove"]
    assert state["status"] == "ATTEMPTED_UNVERIFIED"
    assert state["independent_attempts_before_help"] == 1
    assert state["assisted_attempts"] == 0
    assert report["mastery"] == "NOT_EVALUATED"


def test_hint_and_solution_make_later_attempts_assisted(unit):
    report = summarize(log(
        event("attempt", response_chars=3),
        event("hint", hint_index=0),
        event("attempt", response_chars=5),
        event("hint", hint_index=1),
        event("solution_reveal"),
        event("attempt", response_chars=12),
    ), unit)
    state = report["assessments"]["task/prove"]
    assert state["attempts"] == 3
    assert state["independent_attempts_before_help"] == 1
    assert state["assisted_attempts"] == 2
    assert state["hints"] == 2
    assert state["solutions_viewed"] == 1
    assert state["status"] == "ASSISTED_ATTEMPT_UNVERIFIED"
    assert report["correctness"] == report["mastery"] == "NOT_EVALUATED"


@pytest.mark.parametrize("bad", [
    {"type": "hint", "hint_index": 0},
    {"type": "solution_reveal"},
    {"type": "attempt", "response_chars": 0},
    {"type": "attempt", "response_chars": True},
    {"type": "attempt", "response_chars": 20001},
    {"type": "attempt", "response_chars": 4, "correct": True},
    {"type": "mastered"},
    {"type": "attempt", "response_chars": 2, "at": "2026-11-20"},
    {"type": "attempt", "response_chars": 2, "task_id": "wrong/item"},
])
def test_invalid_events_rejected(unit, bad):
    data = event(bad.pop("type"), **{k:v for k,v in bad.items() if k not in ("at", "task_id")})
    for field in ("at", "task_id"):
        if field in bad:
            data[field] = bad[field]
    with pytest.raises(EvidenceError):
        summarize(log(data), unit)


def test_duplicate_solution_and_out_of_order_hint_rejected(unit):
    cases = [
        log(event("attempt", response_chars=5), event("hint", hint_index=1)),
        log(event("attempt", response_chars=5),
            event("solution_reveal"), event("solution_reveal")),
    ]
    for data in cases:
        with pytest.raises(EvidenceError):
            summarize(data, unit)


def test_rejects_other_unit_and_untrusted_fabricated_status(unit):
    data = log(event("attempt", response_chars=7))
    data["unit_id"] = "some-other-unit"
    with pytest.raises(EvidenceError):
        summarize(data, unit)
    data["unit_id"] = unit["unit_id"]
    data["mastery"] = "MASTERED"
    with pytest.raises(EvidenceError):
        summarize(data, unit)


def test_assistance_stays_scoped_to_its_assessment(unit):
    another = copy.deepcopy(unit["assessments"][0])
    another["id"] = "task/other"
    another["hints"] = []
    unit["assessments"].append(another)
    report = summarize(log(
        event("attempt", response_chars=8),
        event("hint", hint_index=0),
        event("attempt", task_id="task/other", response_chars=4),
        lesson=unit,
    ), unit)
    other = report["assessments"]["task/other"]
    assert other["status"] == "ATTEMPTED_UNVERIFIED"
    assert other["ever_helped"] is False


def test_edited_assessment_invalidates_prior_learning_evidence(unit):
    record = log(event("attempt", response_chars=4), lesson=unit)
    assert summarize(record, unit)["events_checked"] == 1
    updated = copy.deepcopy(unit)
    updated["assessments"][0]["prompt"] += " Revised wording."
    with pytest.raises(EvidenceError, match="assessment revision differs"):
        summarize(record, updated)
