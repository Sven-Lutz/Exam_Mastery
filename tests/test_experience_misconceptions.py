"""Misconception hypotheses are authored, referenced and fail closed.

No diagnosis here can establish a learner's psychological cause. Numeric
wrong-value matches are hypotheses; feedback must reflect this limitation.
"""
import copy
import json
from pathlib import Path

import pytest

from exam_mastery.learning.experience import validate
from exam_mastery.learning.experience_books import book_model
from exam_mastery.learning.experience_adaptation import recommend
from exam_mastery.learning.experience_evidence import (
    SCHEMA, EvidenceError, assessment_revision,
)
from exam_mastery.learning.experience_misconceptions import to_policy_categories


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "experience_misconception_reference.json"


def unit():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def event(kind, **extra):
    return {"type": kind, "task_id": "task/prove",
            "at": "2026-11-20T19:00:00.000Z", **extra}


def log(u, *events):
    return {"schema": SCHEMA, "unit_id": u["unit_id"],
            "assessment_revision": assessment_revision(u), "events": list(events)}


def test_cross_product_reference_fixture_passes():
    u = unit()
    report = validate(u)
    assert report["valid"], report["errors"]
    categories = to_policy_categories(u)
    category = categories["binary/duplicate-boundary"]
    assert category["kind"] == "misconception"
    assert category["contrast_task_id"] == "task/contrast-unique"
    assert category["support"]["ref"] == "teach/proof"
    assert category["visual"]["ref"] == "interaction/binary-search"
    book = book_model(u)
    boxes = [block for section in book["sections"] for block in section["blocks"]
             if block["type"] == "misconception"]
    assert len(boxes) == 1
    assert "lower_bound" in boxes[0]["wrong"]
    assert "Index 1" in boxes[0]["right"]
    assert "Invariante" not in boxes[0]["why"] or len(boxes[0]["why"]) > 50


def test_first_wrong_prediction_is_hypothesis_not_certainty():
    u = unit()
    out = recommend(u, log(u, event("attempt", response_chars=1)),
                    answers={0: "2"})
    assert out["policy"]["rule"] == "RC1"
    assert out["policy"]["next_task"] == "task/prove"
    assert out["policy"]["focus"]["ref"] == "interaction/binary-search"
    assert out["mastery"] == "NOT_EVALUATED"
    assert "könnte" in u["misconceptions"][0]["feedback"]


def test_repeated_pattern_routes_to_specific_contrast_not_any_contrast():
    u = unit()
    u["assessments"].insert(1, {
        **copy.deepcopy(u["assessments"][1]),
        "id": "task/earlier-contrast",
    })
    assert validate(u)["valid"]
    l = log(u, event("attempt", response_chars=1),
            event("attempt", response_chars=1))
    out = recommend(u, l, answers={0: "2", 1: "2"})
    assert out["policy"]["rule"] == "RC2"
    assert out["policy"]["next_task"] == "task/contrast-unique"
    assert out["policy"]["support"]["ref"] == "task/contrast-unique"
    assert out["recommended_task"] == "task/contrast-unique"
    assert out["mastery"] == "NOT_EVALUATED"


@pytest.mark.parametrize("change,needle", [
    ("unknown_category", "unknown hypothesis category"),
    ("bad_kind", "invalid hypothesis kind"),
    ("bad_target", "unresolved contrast_task_id"),
    ("wrong_target_role", "must have role contrast"),
    ("bad_reference", "unknown claim reference"),
    ("skill_mismatch", "competency mismatch"),
    ("no_remediation", "no remedial learning component"),
    ("missing_explanation", "bounded explanation required"),
    ("collision_expected", "wrong-value oracle equals correct value"),
    ("colliding_wrongs", "overlapping wrong-value oracles"),
    ("unused_category", "no deterministic wrong-value evidence target"),
])
def test_invalid_authoring_is_rejected(change, needle):
    u = unit()
    spec = u["misconceptions"][0]
    main = u["assessments"][0]
    if change == "unknown_category":
        main["machine_check"]["errors"][0]["category"] = "unknown/category"
    elif change == "bad_kind":
        spec["kind"] = "supernatural_mastery"
    elif change == "bad_target":
        spec["contrast_task_id"] = "task/missing"
    elif change == "wrong_target_role":
        u["assessments"][1]["role"] = "core"
    elif change == "bad_reference":
        spec["claim_ids"] = ["claim/never-seen"]
    elif change == "skill_mismatch":
        u["competencies"].append({
            "id": "skill/other", "operation": "explain", "prerequisites": [],
        })
        spec["competency_ids"] = ["skill/other"]
    elif change == "no_remediation":
        spec.pop("worked_example_id")
        spec.pop("contrast_task_id")
        spec.pop("visual_interaction_id")
    elif change == "missing_explanation":
        spec["explanation"] = ""
    elif change == "collision_expected":
        main["machine_check"]["errors"][0]["value"] = 1
    elif change == "colliding_wrongs":
        main["machine_check"]["errors"].append(
            {"value": 2, "category": spec["id"]}
        )
    elif change == "unused_category":
        main["machine_check"]["errors"].clear()
    report = validate(u)
    assert not report["valid"]
    assert any(needle in error for error in report["errors"]), report["errors"]


def test_grounded_hypothesis_needs_claim_reference():
    u = unit()
    u["source_mode"] = "grounded"
    u["sources"][0]["kind"] = "research"
    u["claims"][0]["evidence_status"] = "verified"
    for section in ("teaching", "assessments", "cards", "interactions"):
        for entry in u[section]:
            entry.setdefault("claim_ids", [u["claims"][0]["id"]])
    assert validate(u)["valid"]
    u["misconceptions"][0]["claim_ids"] = []
    assert any("grounded hypothesis requires claim refs" in x
               for x in validate(u)["errors"])


def test_changing_remediation_invalidates_old_learning_evidence():
    u = unit()
    record = log(u, event("attempt", response_chars=1))
    assert recommend(u, record)["mastery"] == "NOT_EVALUATED"
    modified = copy.deepcopy(u)
    modified["misconceptions"][0]["feedback"] += " Revised guidance."
    with pytest.raises(EvidenceError, match="assessment revision differs"):
        recommend(modified, record)


def test_generic_finance_numbers_do_not_require_binary_search_domain():
    u = unit()
    u["unit_id"] = "finance/liquidity-reference"
    u["title"] = "Liquidity: period vs cumulative cash"
    u["knowledge_modes"] = ["economic", "conceptual"]
    # Test generic contract machinery with different semantics, not reusing
    # the binary-search numeric answer or error content as finance evidence.
    u["misconceptions"][0].update({
        "id": "finance/period-vs-cumulative",
        "label": "Period value versus cumulative balance",
        "feedback": "The selected period value could have been mistaken for the running total.",
        "wrong_example": "Example: the last period cash flow is 4, reported as the total.",
        "corrected_example": "With an initial cash reserve of 2 and flows -3,+4, the final balance is 3.",
        "explanation": "The balance adds each period's net flow to the prior balance; a single period is not the cumulative result.",
    })
    main = u["assessments"][0]
    main["prompt"] = "Opening cash 2, flows -3,+4. What is the final cash balance?"
    main["solution"] = "2 - 3 + 4 = 3."
    main["machine_check"] = {
        "type": "numeric", "expected": 3, "tolerance": 0,
        "errors": [{"value": 4, "category": "finance/period-vs-cumulative"}],
    }
    assert validate(u)["valid"]
    outcome = recommend(u, log(u, event("attempt", response_chars=1)),
                        answers={0: "4"})
    assert outcome["policy"]["rule"] == "RC1"
    assert outcome["mastery"] == "NOT_EVALUATED"
