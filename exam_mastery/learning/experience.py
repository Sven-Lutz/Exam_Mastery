"""Offline, subject-adaptive learning-experience contract.

This is a canonical *linking and validation* layer, not a fifth learning
product or an alternative Anki scheduler. Its plan does not build files.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "em-experience-v1"
PRODUCTS = {
    "textbook": "Lehrbuch.pdf",
    "workbook": "Arbeitsbuch.pdf",
    "anki": "Anki.apkg",
    "interactive": "Interaktiv/index.html",
}
MODES = {
    "formal_reasoning", "computational", "legal_reasoning",
    "clinical_reasoning", "experimental", "procedural", "spatial",
    "economic", "conceptual", "interpretative", "practical",
}
OPERATIONS = {
    "recall", "explain", "prove", "derive", "calculate", "implement",
    "debug", "trace", "design", "diagnose", "subsume", "argue",
    "compare", "evaluate", "experiment", "interpret", "transfer", "classify",
}
INTERACTIONS = {
    "explorable_model", "visual_derivation", "code_trace", "coding_workbench",
    "scenario_decision", "case_reasoning", "spatial_exploration",
    "simulation", "interactive_explanation",
}
SEMANTIC_ID = re.compile(r"^[a-z0-9][a-z0-9/_-]{2,100}$")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _objects(unit, section, errors):
    items = unit.get(section, [])
    if not isinstance(items, list):
        errors.append(f"{section}: expected list")
        return [], set()
    unique = set()
    output = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"{section}[{index}]: expected object")
            continue
        key = item.get("key") if section == "cards" else item.get("id")
        if not isinstance(key, str) or not SEMANTIC_ID.fullmatch(key):
            errors.append(f"{section}[{index}]: invalid semantic ID")
        elif key in unique:
            errors.append(f"{section}[{index}]: duplicate semantic ID {key}")
        else:
            unique.add(key)
        output.append(item)
    return output, unique


def _references(value, known, where, errors):
    if not isinstance(value, list):
        errors.append(f"{where}: expected list of IDs")
        return
    for ref in value:
        if not isinstance(ref, str) or ref not in known:
            errors.append(f"{where}: unknown reference {ref!r}")


def _check_prerequisites(competencies, known, errors):
    graph = {}
    for item in competencies:
        key = item.get("id")
        if item.get("operation") not in OPERATIONS:
            errors.append(f"competencies.{key}: unsupported learning operation")
        values = item.get("prerequisites", [])
        _references(values, known, f"competencies.{key}.prerequisites", errors)
        if isinstance(values, list) and key in values:
            errors.append(f"competencies.{key}: cannot depend on itself")
        if isinstance(values, list) and isinstance(key, str):
            graph[key] = [v for v in values if isinstance(v, str)]
    active, done = set(), set()

    def visit(key):
        if key in active:
            errors.append(f"competencies: cycle involving {key}")
            return
        if key in done or key not in graph:
            return
        active.add(key)
        for child in graph[key]:
            visit(child)
        active.remove(key)
        done.add(key)

    for key in graph:
        visit(key)


def validate(unit):
    """Structural QA only; not a scientific or learning-effectiveness certificate."""
    if not isinstance(unit, dict):
        return {"valid": False, "errors": ["root: expected object"], "warnings": []}
    errors, warnings = [], []
    if unit.get("schema") != SCHEMA:
        errors.append(f"schema: expected {SCHEMA}")
    uid = unit.get("unit_id")
    if not isinstance(uid, str) or not SEMANTIC_ID.fullmatch(uid):
        errors.append("unit_id: invalid semantic ID")
    if not _text(unit.get("title")):
        errors.append("title: required")
    modes = unit.get("knowledge_modes")
    if not isinstance(modes, list) or not modes:
        errors.append("knowledge_modes: nonempty list required")
    else:
        for mode in modes:
            if mode not in MODES:
                errors.append(f"knowledge_modes: unsupported mode {mode!r}")
    source_mode = unit.get("source_mode")
    if source_mode not in ("synthetic", "grounded"):
        errors.append("source_mode: expected synthetic or grounded")

    sources, source_ids = _objects(unit, "sources", errors)
    claims, claim_ids = _objects(unit, "claims", errors)
    skills, skill_ids = _objects(unit, "competencies", errors)
    teaching, _ = _objects(unit, "teaching", errors)
    tasks, _ = _objects(unit, "assessments", errors)
    cards, _ = _objects(unit, "cards", errors)
    interactions, _ = _objects(unit, "interactions", errors)

    for name, seq in (("competencies", skills), ("teaching", teaching), ("assessments", tasks)):
        if not seq:
            errors.append(f"{name}: at least one required")
    if source_mode == "grounded" and not sources:
        errors.append("grounded mode requires identified sources")

    for item in sources:
        key = item.get("id")
        if not _text(item.get("locator")):
            errors.append(f"sources.{key}: locator required")
        if source_mode == "synthetic" and item.get("kind") != "synthetic":
            errors.append(f"sources.{key}: synthetic mode forbids lecture/external sources")
        if source_mode == "grounded" and item.get("kind") == "synthetic":
            errors.append(f"sources.{key}: grounded mode cannot rely on synthetic evidence")

    _check_prerequisites(skills, skill_ids, errors)
    for claim in claims:
        key = claim.get("id")
        if not _text(claim.get("text")):
            errors.append(f"claims.{key}: proposition required")
        refs = claim.get("source_refs")
        _references(refs, source_ids, f"claims.{key}.source_refs", errors)
        if not refs:
            errors.append(f"claims.{key}: ungrounded claim")
        status = claim.get("evidence_status")
        if status not in ("synthetic", "verified", "unverified"):
            errors.append(f"claims.{key}: unknown evidence status")
        if source_mode == "synthetic" and status != "synthetic":
            errors.append(f"claims.{key}: fabricated verification status")
        if source_mode == "grounded" and status == "synthetic":
            errors.append(f"claims.{key}: synthetic status in grounded mode")
        if status == "unverified":
            warnings.append(f"claims.{key}: not independently verified")

    coverage = {"teaching": set(), "assessments": set(), "anki": set(), "interactive": set()}
    for section, objects, target in (
        ("teaching", teaching, "teaching"), ("assessments", tasks, "assessments"),
        ("cards", cards, "anki"), ("interactions", interactions, "interactive"),
    ):
        for item in objects:
            key = item.get("key") if section == "cards" else item.get("id")
            refs = item.get("competency_ids")
            _references(refs, skill_ids, f"{section}.{key}.competency_ids", errors)
            if not refs:
                errors.append(f"{section}.{key}: competency association required")
            elif isinstance(refs, list):
                coverage[target].update(x for x in refs if isinstance(x, str) and x in skill_ids)
            if section == "teaching":
                if not _text(item.get("content")):
                    errors.append(f"teaching.{key}: explanation required")
                _references(item.get("claim_ids", []), claim_ids, f"teaching.{key}.claim_ids", errors)
            elif section == "assessments":
                if not all(_text(item.get(n)) for n in ("prompt", "solution")):
                    errors.append(f"assessments.{key}: prompt and full worked solution required")
                rubric = item.get("rubric")
                if not isinstance(rubric, list) or not rubric or not all(
                    isinstance(r, dict) and _text(r.get("criterion"))
                    and isinstance(r.get("points"), (int, float))
                    and not isinstance(r.get("points"), bool) and r["points"] > 0 for r in rubric
                ):
                    errors.append(f"assessments.{key}: criterion-level positive rubric required")
                if item.get("attempt_before_reveal") is not True:
                    errors.append(f"assessments.{key}: independent attempt required before reveal")
            elif section == "cards":
                from ..anki_v2 import card_lint
                for issue in card_lint(item):
                    errors.append(f"cards.{key}: {issue}")
            elif section == "interactions":
                if item.get("type") not in INTERACTIONS:
                    errors.append(f"interactions.{key}: unsupported interaction type")
                for field in ("prediction_prompt", "feedback_rule", "transfer_prompt", "model_ref"):
                    if not _text(item.get(field)):
                        errors.append(f"interactions.{key}: {field} required")

    for section in ("teaching", "assessments"):
        missing = skill_ids - coverage[section]
        if missing:
            errors.append(f"{section}: uncovered competencies: {', '.join(sorted(missing))}")
    for section, objects, reason in (
        ("cards", cards, "anki_not_applicable_reason"),
        ("interactions", interactions, "interaction_not_applicable_reason"),
    ):
        if not objects and not _text(unit.get(reason)):
            errors.append(f"{section}: entries or {reason} required")
    for target, objects in (("anki", cards), ("interactive", interactions)):
        missing = skill_ids - coverage[target]
        if objects and missing:
            warnings.append(f"{target}: some competencies do not need dedicated coverage: {', '.join(sorted(missing))}")

    return {
        "valid": not errors, "errors": sorted(set(errors)), "warnings": sorted(set(warnings)),
        "coverage": {"competencies": len(skill_ids), **{k: len(v) for k, v in coverage.items()}},
    }


def plan(unit):
    """Offline four-product contract; paths do not represent generated artifacts."""
    result = validate(unit)
    if not result["valid"]:
        raise ValueError("Invalid experience: " + "; ".join(result["errors"]))
    return {
        "schema": "em-experience-plan-v1", "unit_id": unit["unit_id"],
        "products": {name: {"path": path, "status": "NOT_BUILT"} for name, path in PRODUCTS.items()},
        "source_mode": unit["source_mode"], "model_calls": 0, "network_calls": 0,
        "obsidian": {"role": "OPTIONAL_VIEW", "scheduler": "ANKI_ONLY"},
        "validation": result,
    }


def obsidian_note(unit):
    """A single navigation note; no duplicate content or independent review schedule."""
    if not validate(unit)["valid"]:
        raise ValueError("Cannot export an invalid experience")
    lines = [
        "---", "exam_mastery_id: " + json.dumps(unit["unit_id"]),
        "exam_mastery_schema: em-experience-v1", "review_scheduler: anki",
        "---", "", "# " + unit["title"], "",
        "> Generated navigation view. Edit canonical content in Exam Mastery.", "",
        "## Kompetenzen", "",
    ]
    lines.extend("- " + x["id"] + " — " + x["operation"] for x in unit["competencies"])
    lines += ["", "## Lernprodukte", ""]
    lines.extend("- " + name + ": " + path for name, path in PRODUCTS.items())
    lines += ["", "## Herkunft", ""]
    lines.extend("- " + x["id"] + " (" + x.get("kind", "unknown") + "): " + x["locator"] for x in unit["sources"])
    lines += ["", "Die Wiederholungsplanung bleibt ausschließlich in Anki.", ""]
    return "\n".join(lines)


def command(args):
    """CLI: exam-mastery experience validate|plan|obsidian|render unit.json [--out dir]."""
    parser = argparse.ArgumentParser(prog="exam-mastery experience")
    parser.add_argument("action", choices=("validate", "plan", "obsidian", "render", "anki"))
    parser.add_argument("input")
    parser.add_argument("--out")
    a = parser.parse_args(args)
    unit = json.loads(Path(a.input).read_text(encoding="utf-8"))
    if a.action == "validate":
        result = validate(unit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    if a.action == "plan":
        print(json.dumps(plan(unit), ensure_ascii=False, indent=2))
        return 0
    if a.action == "anki":
        if not a.out:
            parser.error("anki requires --out <directory>")
        from .experience_anki import publish
        print(json.dumps(publish(unit, a.out), ensure_ascii=False, indent=2))
        return 0
    if a.action == "render":
        if not a.out:
            parser.error("render requires --out <directory>")
        from .interactive_reference import publish
        print(json.dumps(publish(unit, a.out), ensure_ascii=False, indent=2))
        return 0
    if not a.out or Path(a.out).suffix.lower() != ".md":
        parser.error("obsidian requires --out <file.md>")
    destination = Path(a.out)
    content = obsidian_note(unit)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or destination.read_text(encoding="utf-8") != content:
        destination.write_text(content, encoding="utf-8")
    print(json.dumps({"file": str(destination), "scheduler": "ANKI_ONLY"}))
    return 0
