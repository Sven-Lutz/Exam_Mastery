"""Exact algebraic identity gates; no claims that all proofs are verified."""
import copy
import json
from pathlib import Path

import pytest

from exam_mastery.learning.experience import validate
from exam_mastery.learning.experience_proof_checks import (
    ProofCheckError, verify,
)
from exam_mastery.learning.experience_books import book_model
from exam_mastery.learning import interactive_reference as ir


UNIT = Path(__file__).resolve().parents[1] / "fixtures" / "experience_binomial_reference.json"


def unit():
    return json.loads(UNIT.read_text(encoding="utf-8"))


def poly(left, right, variables=("a", "b")):
    return {
        "kind": "polynomial_identity", "lhs": left,
        "rhs": right, "variables": list(variables),
    }


@pytest.mark.parametrize("left,right,vars", [
    ("(a+b)^2", "a^2+2*a*b+b^2", ("a", "b")),
    ("(a+b)*(a-b)", "a^2-b^2", ("a", "b")),
    ("(a+b)^2", "(a+b)*(a+b)", ("a", "b")),
    ("x^5", "x*x*x*x*x", ("x",)),
    ("x+y", "y+x", ("x", "y")),
    ("0.1*x+0.2*x", "0.3*x", ("x",)),
])
def test_exact_polynomial_identities_over_reals(left, right, vars):
    result = verify(poly(left, right, vars))
    assert result["status"] == "VERIFIED_POLYNOMIAL_IDENTITY"
    assert result["method"] == "EXACT_SYMPY_POLY_QQ"
    assert result["scope"] == "ONLY_THE_DISPLAYED_EQUATION_OVER_REAL_VARIABLES"
    assert result["latex"].startswith(r"\(")


@pytest.mark.parametrize("invalid,needle", [
    (poly("(a+b)^2", "a^2+b^2"), "identity is false"),
    (poly("(a+b)^2", "(a-b)^2"), "identity is false"),
    (poly("a/a", "1", ("a",)), "unsupported"),
    (poly("a^-1", "1/a", ("a",)), "positive integer powers"),
    (poly("a^7", "a^7", ("a",)), "positive integer powers"),
    (poly("a^5*b^4", "a^5*b^4"), "degree limit"),
    (poly("a^b", "b^a"), "positive integer powers"),
    (poly("a+a", "2*a", ("a", "b")), "variables must match"),
    (poly("__import__('os')", "a", ("a",)), "unsafe or invalid"),
    (poly("a+a", "2*a", ("a", "a")), "unique bounded variable"),
    ({"kind": "polynomial_identity", "lhs": "a", "rhs": "a",
      "variables": ["a"], "verified": True}, "exact polynomial-check fields"),
    (poly("a" * 300, "a", ("a",)), "bounded expression required"),
])
def test_false_unsafe_unbounded_or_ambiguous_checks_fail_closed(invalid, needle):
    with pytest.raises(ProofCheckError, match=needle):
        verify(invalid)


def test_reference_unit_exact_checks_and_shared_pdf_html_statements():
    u = unit()
    report = validate(u)
    assert report["valid"], report["errors"]
    proof = u["teaching"][1]["derivation"]
    assert len(proof["steps"]) == 3
    assert all(verify(step["math_check"])["status"] == "VERIFIED_POLYNOMIAL_IDENTITY"
               for step in proof["steps"])
    book = book_model(u)
    equations = [b for section in book["sections"] for b in section["blocks"]
                 if b["type"] == "example"]
    assert len(equations) == 1
    assert len(equations[0]["steps"]) == 3
    assert all(r"\(" in row[0] and row[1] for row in equations[0]["steps"])

    html = ir.render_html(u)
    assert html.count('class="proof-equation"') == 3
    assert "nicht der gesamte Beweis" in html
    assert "binomial_area_partition" in html


def test_false_equation_blocks_entire_learning_unit_and_publish(tmp_path):
    u = unit()
    u["teaching"][1]["derivation"]["steps"][1]["math_check"]["rhs"] = "a^2+b^2"
    errors = validate(u)["errors"]
    assert any("polynomial identity is false" in e for e in errors)
    from exam_mastery.learning.experience_pipeline import build
    with pytest.raises(ValueError, match="polynomial identity is false"):
        build(u, tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("a,b", [(0.5, 0.5), (1, 2), (2, 3), (4, 1), (6, 6)])
def test_area_oracle_matches_independent_sum(a, b):
    trace = ir.binomial_area_trace({"a": a, "b": b})
    assert trace["result"] == pytest.approx((a+b)**2)
    assert trace["result"] == pytest.approx(a*a+a*b+a*b+b*b)
    assert len(trace["steps"]) == 3
    assert all(s["state"]["kind"] == "area" for s in trace["steps"])


@pytest.mark.parametrize("bad", [
    {"a": 0, "b": 2}, {"a": -1, "b": 2}, {"a": float("nan"), "b": 2},
    {"a": 100, "b": 1}, {"a": 1}, {"a": True, "b": 1},
    {"a": 1, "b": 2, "script": "alert(1)"},
])
def test_area_oracle_rejects_unsafe_or_unsupported_parameters(bad):
    with pytest.raises(ir.InteractionError):
        ir.binomial_area_trace(bad)


def test_real_browser_displays_proportionate_area_geometry(tmp_path):
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    ir.publish(unit(), tmp_path)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.goto((tmp_path / "Interaktiv" / "index.html").as_uri())
            root = page.locator("#interaction-interaction-binomial-area")
            assert root.locator(".reveal").is_disabled()
            root.locator(".prediction").fill("9")
            root.locator(".check").click()
            assert root.locator(".area-grid").count() == 1
            assert root.locator(".area-region").count() == 4
            labels = root.locator(".area-region").evaluate_all(
                "(nodes)=>nodes.map(n=>n.getAttribute('aria-label'))"
            )
            assert all("Teilfläche" in label for label in labels)
            assert root.locator(".area-grid").evaluate(
                "(el)=>el.style.gridTemplateColumns"
            ) == "1fr 2fr"
            root.locator(".reveal").click()
            assert "Prediction matches" in root.locator(".result").inner_text()
            root.locator(".variant-picker").select_option("1")
            assert root.locator(".reveal").is_disabled()
            assert root.locator(".story-scenes").is_hidden()
            root.locator(".prediction").fill("25")
            root.locator(".check").click()
            assert root.locator(".area-grid").evaluate(
                "(el)=>el.style.gridTemplateColumns"
            ) == "2fr 3fr"
        finally:
            browser.close()


def test_real_four_product_publish_with_polynomial_derivations(tmp_path):
    pytest.importorskip("playwright.sync_api")
    fitz = pytest.importorskip("pymupdf")
    pytest.importorskip("anki")
    from exam_mastery.learning.experience_pipeline import build, preflight

    u = unit()
    report = build(u, tmp_path)
    assert report["publication"]["status"] == "STAGED_COMMIT"
    assert preflight(u, tmp_path)["status"] == "PREFLIGHT_PASS"
    with fitz.open(tmp_path / "Lehrbuch.pdf") as pdf:
        assert pdf.page_count >= 2
        text = "\n".join(page.get_text() for page in pdf)
        assert "Quadrat" in text
    with fitz.open(tmp_path / "Arbeitsbuch.pdf") as pdf:
        assert pdf.page_count >= 2
        assert "Musterlösungen" in "\n".join(page.get_text() for page in pdf)
    assert (tmp_path / "Anki.apkg").stat().st_size > 0
    assert (tmp_path / "Interaktiv" / "index.html").stat().st_size > 0
