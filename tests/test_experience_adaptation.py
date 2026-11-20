"""End-to-end adapter: real legacy diagnosis/policy, no invented mastery."""
import copy
import json
from pathlib import Path

import pytest

from exam_mastery.learning.experience import validate
from exam_mastery.learning.experience_adaptation import recommend
from exam_mastery.learning.experience_evidence import (
    EvidenceError, SCHEMA, assessment_revision,
)


def lesson():
    source = Path(__file__).resolve().parents[1] / "fixtures" / "experience_reference.json"
    unit = json.loads(source.read_text(encoding="utf-8"))
    main = unit["assessments"][0]
    main["prompt"] = "Calculate the lower-bound index of 7 in [2,5,8,12]."
    main["solution"] = "The first value >= 7 is 8 at zero-based index 2."
    main["machine_check"] = {"type": "numeric", "expected": 2, "tolerance": 0}
    main["hints"] = ["Find the first element >= target."]
    main["role"] = "core"
    transfer = copy.deepcopy(main)
    transfer["id"] = "task/new-transfer"
    transfer["role"] = "transfer"
    transfer["prompt"] = "What is lower_bound(5) in [1,3,5,5,7]?"
    transfer["solution"] = "Index 2; duplicates do not change the first qualifying position."
    transfer["machine_check"] = {"type": "numeric", "expected": 2, "tolerance": 0}
    unit["assessments"].append(transfer)
    assert validate(unit)["valid"]
    return unit


def open_lesson():
    unit = lesson()
    for task in unit["assessments"]:
        task.pop("machine_check")
    assert validate(unit)["valid"]
    return unit


def log(unit, *events):
    return {
        "schema": SCHEMA, "unit_id": unit["unit_id"],
        "assessment_revision": assessment_revision(unit),
        "events": list(events),
    }


def event(kind, task="task/prove", **kwargs):
    return {"type": kind, "task_id": task,
            "at": "2026-11-20T18:56:00.000Z", **kwargs}


def test_empty_session_delegates_to_existing_R0():
    unit = lesson()
    result = recommend(unit, log(unit))
    assert result["policy"]["schema"] == "em-decision-v1"
    assert result["policy"]["rule"] == "R0"
    assert result["recommended_task"] == "task/prove"
    assert result["mastery"] == "NOT_EVALUATED"


def test_browser_only_attempt_never_becomes_correct_or_mastered():
    unit = lesson()
    report = recommend(unit, log(unit, event("attempt", response_chars=1)))
    assert report["policy"]["rule"] == "RL5"
    assert report["recommended_task"] == "task/prove"
    assert report["requires_human_or_tutor_review"]
    assert report["locally_checked_attempts"] == 0
    assert report["unverified_attempts"] == 1
    assert report["mastery"] == report["evidence"]["mastery"] == "NOT_EVALUATED"


def test_ordinary_proof_cannot_receive_numeric_grade_even_if_answer_is_supplied():
    unit = open_lesson()
    report = recommend(unit,
                       log(unit, event("attempt", response_chars=1)),
                       answers={"0": "2"})
    assert report["policy"]["rule"] == "RL5"
    assert report["locally_checked_attempts"] == 0
    assert report["requires_human_or_tutor_review"]


def test_existing_policy_moves_to_transfer_after_local_numeric_success():
    unit = lesson()
    report = recommend(unit,
                       log(unit, event("attempt", response_chars=1)),
                       answers={0: "2"})
    assert report["policy"]["rule"] == "RD"
    assert report["policy"]["action"] == "transfer"
    assert report["recommended_task"] == "task/new-transfer"
    assert report["locally_checked_attempts"] == 1
    assert not report["requires_human_or_tutor_review"]
    assert report["mastery"] == "NOT_EVALUATED"
    assert report["evidence"]["correctness"] == "NOT_EVALUATED"


def test_existing_policy_diagnoses_sign_error_without_answer_leak():
    unit = lesson()
    report = recommend(unit,
                       log(unit, event("attempt", response_chars=2)),
                       answers={"0": "-2"})
    assert report["policy"]["rule"] == "RB"
    assert report["policy"]["action"] == "focus_step"
    assert report["recommended_task"] == "task/prove"
    assert "-2" not in json.dumps(report, ensure_ascii=False)


def test_correct_after_hint_is_assisted_and_requires_fading():
    unit = lesson()
    events = [
        event("attempt", response_chars=2),
        event("hint", hint_index=0),
        event("attempt", response_chars=1),
    ]
    report = recommend(unit, log(unit, *events), answers={0: "-2", 2: "2"})
    assert report["policy"]["rule"] == "RF"
    assert report["policy"]["action"] == "similar_without_hints"
    assert report["policy"]["hints_allowed"] is False
    assert report["evidence"]["assessments"]["task/prove"]["assisted_attempts"] == 1
    assert report["mastery"] == "NOT_EVALUATED"


@pytest.mark.parametrize("bad", [
    {0: "23"},  # content length mismatches exported attempt
    {3: "2"},   # no corresponding attempt event
    {"x": "2"},
    {False: "2"},
    {0: 2},
])
def test_untrusted_response_map_is_rejected(bad):
    unit = lesson()
    with pytest.raises(EvidenceError):
        recommend(unit, log(unit, event("attempt", response_chars=1)), answers=bad)


def test_changed_numeric_oracle_invalidates_original_log():
    unit = lesson()
    record = log(unit, event("attempt", response_chars=1))
    other = copy.deepcopy(unit)
    other["assessments"][0]["machine_check"]["expected"] = 99
    with pytest.raises(EvidenceError, match="assessment revision differs"):
        recommend(other, record, answers={0: "2"})


@pytest.mark.parametrize("bad", [
    {"type": "expression", "expected": "x"},
    {"type": "numeric", "expected": float("nan")},
    {"type": "numeric", "expected": True},
    {"type": "numeric", "expected": 1, "tolerance": -1},
    {"type": "numeric", "expected": 1, "errors": [{"value": 2, "category": "invented"}]},
])
def test_unsafe_or_unimplemented_machine_checkers_fail_schema(bad):
    unit = lesson()
    unit["assessments"][0]["machine_check"] = bad
    assert not validate(unit)["valid"]


def test_multi_competency_machine_grading_forbidden():
    unit = lesson()
    unit["competencies"].append({
        "id": "skill/other", "operation": "explain", "prerequisites": [],
    })
    for area in ("teaching", "assessments"):
        unit[area][0]["competency_ids"].append("skill/other")
    unit["assessments"][1]["competency_ids"].append("skill/other")
    assert not validate(unit)["valid"]


def test_correctness_never_inferred_from_two_calendar_days():
    unit = lesson()
    first = event("attempt", response_chars=1)
    second = {**event("attempt", response_chars=1),
              "at": "2026-11-22T18:56:00.000Z"}
    report = recommend(unit, log(unit, first, second), answers={0: "2", 1: "2"})
    assert report["mastery"] == "NOT_EVALUATED"
    assert report["evidence"]["mastery"] == "NOT_EVALUATED"
