"""Experience Anki adapter tests: stable output, reuse, no collection mutation."""
import copy
import json
from pathlib import Path
import zipfile

import pytest

from exam_mastery.learning import experience as ex
from exam_mastery.learning import experience_anki as bridge


def synthetic_unit():
    return {
        "schema": "em-experience-v1", "unit_id": "cs/trace-demo",
        "title": "Trace Demo", "source_mode": "synthetic",
        "knowledge_modes": ["computational"],
        "sources": [{"id": "synthetic/trace", "kind": "synthetic", "locator": "Synthetic reference"}],
        "claims": [{"id": "synthetic/claim", "text": "Verified synthetic property",
                    "evidence_status": "synthetic", "source_refs": ["synthetic/trace"]}],
        "competencies": [{"id": "skill/trace", "operation": "trace", "prerequisites": []}],
        "teaching": [{"id": "teaching/explain", "content": "A precise independent explanation.",
                      "competency_ids": ["skill/trace"], "claim_ids": ["synthetic/claim"]}],
        "assessments": [{"id": "task/solve", "prompt": "Derive the correct result.",
                         "solution": "Apply the invariant, then verify the result.",
                         "rubric": [{"criterion": "Correct argument", "points": 2}],
                         "attempt_before_reveal": True, "competency_ids": ["skill/trace"]}],
        "cards": [{"key": "trace/why", "kind": "concept", "front": "Why must the index increase?",
                   "answer": "Because the candidate interval becomes strictly shorter.",
                   "competency_ids": ["skill/trace"]}],
        "interactions": [],
        "interaction_not_applicable_reason": "This unit tests only the Anki exporter.",
    }


def test_lint_and_refusal_without_cards(tmp_path):
    lesson = synthetic_unit()
    assert ex.validate(lesson)["valid"]
    lesson["cards"] = []
    lesson["anki_not_applicable_reason"] = "Not appropriate to memorise."
    with pytest.raises(ValueError, match="empty Anki"):
        bridge.publish(lesson, tmp_path)


def test_single_public_package_and_idempotent_reexport(tmp_path):
    pytest.importorskip("anki")
    unit = synthetic_unit()
    first = bridge.publish(unit, tmp_path)
    pkg = tmp_path / "Anki.apkg"
    assert first["status"] == "CREATED_OR_UPDATED"
    assert first["notes"] == 1
    assert first["model_calls"] == 0
    assert first["user_collection_touched"] is False
    assert pkg.is_file()
    with zipfile.ZipFile(pkg) as z:
        assert any("collection." in n for n in z.namelist())
    mtime = pkg.stat().st_mtime_ns
    second = bridge.publish(unit, tmp_path)
    assert second["status"] == "UNCHANGED"
    assert pkg.stat().st_mtime_ns == mtime
    visible = sorted(p.name for p in tmp_path.iterdir() if not p.name.startswith("."))
    assert visible == ["Anki.apkg"]


def test_unmanaged_or_modified_package_is_never_overwritten(tmp_path):
    unit = synthetic_unit()
    (tmp_path / "Anki.apkg").write_bytes(b"personal data")
    with pytest.raises(ValueError, match="unmanaged"):
        bridge.publish(unit, tmp_path)
    assert (tmp_path / "Anki.apkg").read_bytes() == b"personal data"


def test_changed_card_keeps_semantic_identity(tmp_path):
    pytest.importorskip("anki")
    unit = synthetic_unit()
    bridge.publish(unit, tmp_path)
    from exam_mastery import anki_v2
    old_guid = anki_v2.guid("cs", "trace-demo-" +
                            __import__("hashlib").sha256(b"cs/trace-demo").hexdigest()[:8], "trace/why")
    changed = copy.deepcopy(unit)
    changed["cards"][0]["answer"] = "The interval's nonnegative length strictly decreases."
    result = bridge.publish(changed, tmp_path)
    assert result["status"] == "CREATED_OR_UPDATED"
    assert result["update_delta"]["changed"] == ["trace/why"]
    new_guid = anki_v2.guid("cs", "trace-demo-" +
                            __import__("hashlib").sha256(b"cs/trace-demo").hexdigest()[:8], "trace/why")
    assert old_guid == new_guid
