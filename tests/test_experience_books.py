"""Reuses the existing typeset pipeline; exactly two visible PDF products."""
import copy
import json
from pathlib import Path
import re

import pytest

from exam_mastery.learning import experience_books as books


def fixture():
    return json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "experience_reference.json")
        .read_text(encoding="utf-8")
    )


def test_book_model_keeps_sources_and_complete_solutions():
    unit = fixture()
    book = books.book_model(unit)
    assert book["meta"]["course"].endswith("synthetische Referenz")
    assert "SYNTHETISCHES TESTMATERIAL" in book["meta"]["status_line"]
    assert book["exam"] is None  # No automatic unwanted mock-exam product.
    assert book["stages"][0]["items"][0]["solution"]["answer"] == unit["assessments"][0]["solution"]
    assert book["stages"][0]["items"][0]["solution"]["rubric"]
    assert any("Synthetisch" in b["src"] for s in book["sections"] for b in s["blocks"])
    assert [b["kc_ids"] for s in book["sections"] for b in s["blocks"]] == [
        x["competency_ids"] for x in unit["teaching"]
    ]


def test_combined_workbook_has_questions_followed_by_solutions_and_unique_anchors():
    body, toc = books._combined_workbook(books.book_model(fixture()))
    assert "Teil I" in body and "Teil II" in body
    assert body.index("Teil I") < body.index("Teil II")
    assert "Vollständige Musterlösungen" in body
    ids = re.findall(r'id="([^"]+)"', body)
    assert len(ids) == len(set(ids))
    assert "loesung-" in body
    assert len(toc) >= 3
    assert "Aufgabe" in body


def test_unmanaged_and_modified_outputs_are_never_overwritten(tmp_path):
    lesson = fixture()
    (tmp_path / "Lehrbuch.pdf").write_bytes(b"personal document")
    with pytest.raises(ValueError, match="unmanaged"):
        books.publish(lesson, tmp_path)
    assert (tmp_path / "Lehrbuch.pdf").read_bytes() == b"personal document"


def test_real_pdf_rendering_and_zero_duplicate_visible_files(tmp_path):
    pytest.importorskip("playwright.sync_api")
    fitz = pytest.importorskip("pymupdf")
    lesson = fixture()
    report = books.publish(lesson, tmp_path)
    assert report["status"] == "CREATED_OR_UPDATED"
    assert report["model_calls"] == 0
    assert report["academic_status"] == "HUMAN_REVIEW_PENDING"
    for file in ["Lehrbuch.pdf", "Arbeitsbuch.pdf"]:
        with fitz.open(tmp_path / file) as pdf:
            assert pdf.page_count >= 2
            text = "\n".join(page.get_text() for page in pdf)
            assert lesson["title"] in text
    with fitz.open(tmp_path / "Arbeitsbuch.pdf") as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        assert "Musterlösungen" in text
        assert "Binary" in text
    mtime = {file: (tmp_path / file).stat().st_mtime_ns for file in report["products"]}
    other = books.publish(lesson, tmp_path)
    assert other["status"] == "UNCHANGED"
    assert {file: (tmp_path / file).stat().st_mtime_ns for file in report["products"]} == mtime
    assert sorted(p.name for p in tmp_path.iterdir() if p.is_file()) == ["Arbeitsbuch.pdf", "Lehrbuch.pdf"]
    assert not list(tmp_path.glob(".em-books-build-*"))
    (tmp_path / "Lehrbuch.pdf").write_bytes(b"unexpected local change")
    with pytest.raises(ValueError, match="modified"):
        books.publish(lesson, tmp_path)


def test_derivation_and_provenance_share_the_existing_pdf_model():
    unit = fixture()
    assert "derivation" in unit["teaching"][1]
    model = books.book_model(unit)
    steps = [block for section in model["sections"] for block in section["blocks"]
             if block["type"] == "example"]
    assert len(steps) == 1
    block = steps[0]
    proof = unit["teaching"][1]["derivation"]
    assert block["title"] == proof["title"]
    assert block["result"] == proof["result"]
    assert block["steps"] == [[s["statement"], s["justification"]]
                              for s in proof["steps"]]
    assert "Synthetisch" in block["src"]
