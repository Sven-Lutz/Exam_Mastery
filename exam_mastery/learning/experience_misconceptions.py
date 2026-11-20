"""Grounded, domain-neutral hypotheses about *observable* answer patterns.

A numeric mismatch can match a deliberately authored wrong-value pattern, but
it cannot establish the learner's cognitive cause. A misconception entry thus
points to an explanatory hypothesis and a verified *authoring reference*,
not a clinical, probabilistic or pedagogically proven diagnosis.

No extra tutor engine: policy.py and its browser mirror still decide next steps.
"""
from __future__ import annotations

import math

KINDS = frozenset(("misconception", "prerequisite", "slip"))
MAX_PATTERNS = 64
MAX_FEEDBACK_CHARS = 900


def _nonempty(text):
    return isinstance(text, str) and bool(text.strip())


def validate_patterns(
    unit, *,
    skill_ids, claim_ids, teaching_ids, task_ids, interaction_ids,
):
    """Return structural errors for optional misconception/remediation specs.

    This validator is intentionally independent of textbook or law curricula.
    IDs and target references must resolve inside the canonical learning unit.
    """
    from .experience import SEMANTIC_ID
    from .policy import GENERIC

    errors = []
    specs = unit.get("misconceptions", [])
    if not isinstance(specs, list) or len(specs) > MAX_PATTERNS:
        return ["misconceptions: expected list of at most 64 hypotheses"]
    source_mode = unit.get("source_mode")
    by_id = {}
    for index, spec in enumerate(specs):
        location = f"misconceptions[{index}]"
        if not isinstance(spec, dict):
            errors.append(f"{location}: expected object")
            continue
        key = spec.get("id")
        if not isinstance(key, str) or not SEMANTIC_ID.fullmatch(key):
            errors.append(f"{location}: invalid semantic ID")
            continue
        if key in by_id or key in GENERIC:
            errors.append(f"{location}: duplicate or reserved category {key!r}")
            continue
        by_id[key] = spec
        if spec.get("kind") not in KINDS:
            errors.append(f"misconceptions.{key}: invalid hypothesis kind")
        for field in ("label", "feedback"):
            text = spec.get(field)
            if not _nonempty(text) or len(text) > MAX_FEEDBACK_CHARS:
                errors.append(f"misconceptions.{key}: bounded {field} required")
        # An explicit counterexample/explanation is essential. Otherwise an
        # identified error would only produce a generic hint, not instruction.
        for field in ("wrong_example", "corrected_example", "explanation"):
            text = spec.get(field)
            if not _nonempty(text) or len(text) > 4000:
                errors.append(f"misconceptions.{key}: bounded {field} required")
        refs = spec.get("competency_ids")
        if not isinstance(refs, list) or not refs or any(
            not isinstance(x, str) or x not in skill_ids for x in refs
        ):
            errors.append(f"misconceptions.{key}: known competency_ids required")
        crefs = spec.get("claim_ids", [])
        if not isinstance(crefs, list) or any(
            not isinstance(x, str) or x not in claim_ids for x in crefs
        ):
            errors.append(f"misconceptions.{key}: unknown claim reference")
        if source_mode == "grounded" and not crefs:
            errors.append(f"misconceptions.{key}: grounded hypothesis requires claim refs")
        for field, known in (
            ("worked_example_id", teaching_ids),
            ("contrast_task_id", task_ids),
            ("retry_task_id", task_ids),
            ("visual_interaction_id", interaction_ids),
        ):
            target = spec.get(field)
            if target is not None and (not isinstance(target, str) or target not in known):
                errors.append(f"misconceptions.{key}: unresolved {field}")
        if not any(spec.get(f) for f in (
            "worked_example_id", "contrast_task_id", "retry_task_id",
            "visual_interaction_id",
        )):
            errors.append(f"misconceptions.{key}: no remedial learning component")
        if spec.get("kind") == "misconception" and not spec.get("contrast_task_id"):
            errors.append(f"misconceptions.{key}: contrasting case required")
        if spec.get("kind") == "prerequisite" and not spec.get("retry_task_id"):
            errors.append(f"misconceptions.{key}: prerequisite retry required")

    tasks = {x.get("id"): x for x in unit.get("assessments", []) if isinstance(x, dict)}
    lessons = {x.get("id"): x for x in unit.get("teaching", []) if isinstance(x, dict)}
    interactions = {x.get("id"): x for x in unit.get("interactions", []) if isinstance(x, dict)}
    used = set()
    for task in tasks.values():
        key = task.get("id")
        checker = task.get("machine_check")
        if not isinstance(checker, dict) or checker.get("type") != "numeric":
            continue
        values = checker.get("errors", [])
        if not isinstance(values, list):
            continue
        expected = checker.get("expected")
        tolerance = checker.get("tolerance", 1e-6)
        if not (
            type(expected) in (int, float)
            and math.isfinite(expected)
            and type(tolerance) in (int, float)
            and math.isfinite(tolerance)
            and tolerance >= 0
        ):
            continue  # base numeric checker reports this instead
        prior_values = []
        for i, err in enumerate(values):
            if not isinstance(err, dict) or type(err.get("value")) not in (int, float):
                continue
            value = err["value"]
            if not math.isfinite(value):
                continue
            if abs(value - expected) <= tolerance:
                errors.append(f"assessments.{key}: wrong-value oracle equals correct value")
            if any(abs(value - earlier) <= 2 * tolerance for earlier in prior_values):
                errors.append(f"assessments.{key}: overlapping wrong-value oracles")
            prior_values.append(value)
            cid = err.get("category")
            if cid in GENERIC:
                continue
            if not isinstance(cid, str) or cid not in by_id:
                errors.append(f"assessments.{key}: unknown hypothesis category {cid!r}")
                continue
            used.add(cid)
            spec = by_id[cid]
            task_skills = task.get("competency_ids", [])
            if (not isinstance(task_skills, list)
                or any(skill not in spec.get("competency_ids", [])
                       for skill in task_skills)):
                errors.append(f"assessments.{key}: category {cid!r} competency mismatch")

    for cid, spec in by_id.items():
        refs = spec.get("competency_ids")
        if not isinstance(refs, list):
            continue
        for field, collection in (
            ("worked_example_id", lessons), ("contrast_task_id", tasks),
            ("retry_task_id", tasks), ("visual_interaction_id", interactions),
        ):
            target_id = spec.get(field)
            target = collection.get(target_id) if isinstance(target_id, str) else None
            if not isinstance(target, dict):
                continue  # already reported unresolved reference
            target_skills = target.get("competency_ids", [])
            if not isinstance(target_skills, list) or not set(refs).intersection(target_skills):
                errors.append(f"misconceptions.{cid}: {field} competency mismatch")
            if field == "contrast_task_id" and target.get("role") != "contrast":
                errors.append(f"misconceptions.{cid}: contrast_task_id must have role contrast")
        if cid not in used:
            errors.append(f"misconceptions.{cid}: no deterministic wrong-value evidence target")
    return errors


def to_policy_categories(unit):
    """Translate the same authored concepts for existing Python/JS policies."""
    result = {}
    for spec in unit.get("misconceptions", []):
        data = {
            "kind": spec["kind"],
            "label": spec["label"],
            "feedback": spec["feedback"],
            "wrong_example": spec["wrong_example"],
            "corrected_example": spec["corrected_example"],
            "explanation": spec["explanation"],
        }
        if spec.get("worked_example_id"):
            data["support"] = {
                "type": "worked_example",
                "ref": spec["worked_example_id"],
            }
        if spec.get("contrast_task_id"):
            data["contrast"] = {
                "type": "contrast_task",
                "ref": spec["contrast_task_id"],
            }
            data["contrast_task_id"] = spec["contrast_task_id"]
        if spec.get("retry_task_id"):
            data["retry_task_id"] = spec["retry_task_id"]
        if spec.get("visual_interaction_id"):
            data["visual"] = {
                "type": "interactive_reference",
                "ref": spec["visual_interaction_id"],
            }
        result[spec["id"]] = data
    return result
