"""Synthetic, cross-domain contract tests; never use lecture files or paid models."""
import copy
import json

from exam_mastery.learning import experience as ex


def unit(mode="computational", operation="implement"):
    return {
        "schema": "em-experience-v1",
        "unit_id": "cs/binary-search" if mode == "computational" else "law/contract-formation",
        "title": "Binary Search" if mode == "computational" else "Vertragsschluss",
        "source_mode": "synthetic",
        "knowledge_modes": [mode],
        "sources": [{"id": "synthetic/reference", "kind": "synthetic", "locator": "synthetic contract fixture"}],
        "claims": [{"id": "synthetic/claim", "text": "Synthetic fact for testing",
                    "source_refs": ["synthetic/reference"], "evidence_status": "synthetic"}],
        "competencies": [{"id": "skill/core", "operation": operation, "prerequisites": []}],
        "teaching": [{"id": "section/explanation", "competency_ids": ["skill/core"],
                      "claim_ids": ["synthetic/claim"], "content": "A complete example and its assumptions."}],
        "assessments": [{"id": "exercise/transfer", "competency_ids": ["skill/core"],
                         "prompt": "Solve the novel problem.", "solution": "Derive the result with all steps.",
                         "rubric": [{"criterion": "Correct method", "points": 2}],
                         "attempt_before_reveal": True}],
        "cards": [{"key": "core/retrieval", "kind": "concept",
                   "front": "Which invariant is preserved?", "answer": "The invariant holds at every iteration.",
                   "competency_ids": ["skill/core"]}],
        "interactions": [{"id": "interactive/trace", "type": "code_trace" if mode == "computational" else "case_reasoning",
                          "competency_ids": ["skill/core"], "prediction_prompt": "Predict the next state.",
                          "feedback_rule": "Use a checked deterministic reference model.",
                          "transfer_prompt": "Analyze a changed case.", "model_ref": "synthetic/reference"}],
    }


def test_four_outputs_and_no_unverified_build_claim():
    r = ex.validate(unit())
    assert r["valid"], r["errors"]
    p = ex.plan(unit())
    assert set(p["products"]) == {"textbook", "workbook", "anki", "interactive"}
    assert {v["status"] for v in p["products"].values()} == {"NOT_BUILT"}
    assert (p["model_calls"], p["network_calls"]) == (0, 0)
    assert p["obsidian"] == {"role": "OPTIONAL_VIEW", "scheduler": "ANKI_ONLY"}
    assert r["coverage"] == {"competencies": 1, "teaching": 1, "assessments": 1,
                             "anki": 1, "interactive": 1}


def test_law_is_not_forced_into_coding_template():
    u = unit("legal_reasoning", "subsume")
    assert ex.validate(u)["valid"]


def test_uncited_claim_blocked():
    u = unit()
    u["claims"][0]["source_refs"] = ["unknown/ref"]
    assert any("unknown reference" in e for e in ex.validate(u)["errors"])


def test_missing_solution_and_premature_reveal_blocked():
    u = unit()
    u["assessments"][0]["solution"] = ""
    u["assessments"][0]["attempt_before_reveal"] = False
    report = ex.validate(u)
    assert any("full worked solution" in e for e in report["errors"])
    assert any("independent attempt" in e for e in report["errors"])


def test_dependency_cycle_blocked():
    u = unit()
    u["competencies"] += [{"id": "skill/other", "operation": "explain",
                           "prerequisites": ["skill/core"]}]
    u["competencies"][0]["prerequisites"] = ["skill/other"]
    assert any("cycle" in e for e in ex.validate(u)["errors"])


def test_justified_not_needed_without_forcing_a_card_or_animation():
    u = unit("clinical_reasoning", "diagnose")
    u["cards"] = []
    u["interactions"] = []
    u["anki_not_applicable_reason"] = "Not suitable for atomic retrieval."
    u["interaction_not_applicable_reason"] = "No medically validated simulation model available."
    assert ex.validate(u)["valid"]
    assert len(ex.plan(u)["products"]) == 4


def test_grounded_mode_cannot_claim_synthetic_evidence():
    u = unit()
    u["source_mode"] = "grounded"
    assert any("cannot rely on synthetic" in e for e in ex.validate(u)["errors"])


def test_duplicate_card_keys_blocked():
    u = unit()
    u["cards"].append(copy.deepcopy(u["cards"][0]))
    assert any("duplicate semantic ID" in e for e in ex.validate(u)["errors"])


def test_invalid_reference_object_rejected_without_exception():
    u = unit()
    u["claims"][0]["source_refs"] = [{"id": "synthetic/reference"}]
    assert not ex.validate(u)["valid"]


def test_obsidian_export_idempotent_and_optional(tmp_path):
    u = unit()
    spec = tmp_path / "unit.json"
    spec.write_text(json.dumps(u), encoding="utf-8")
    target = tmp_path / "vault" / "Binary Search.md"
    assert ex.command(["obsidian", str(spec), "--out", str(target)]) == 0
    before = target.read_bytes()
    assert b"review_scheduler: anki" in before
    assert b"exam_mastery_id" in before
    assert ex.command(["obsidian", str(spec), "--out", str(target)]) == 0
    assert target.read_bytes() == before
    assert len(list(target.parent.iterdir())) == 1


def test_no_external_sources_required_before_lecture_ingestion():
    u = unit()
    assert all(s["kind"] == "synthetic" for s in u["sources"])
    assert ex.plan(u)["source_mode"] == "synthetic"
