"""Real offline learning output from synthetic programming/RL fixtures.

No lecture files, external assets, network, model APIs, or unsafe code execution.
"""
import bisect
import copy
import json
import math
import re

import pytest

from exam_mastery.learning import experience as ex
from exam_mastery.learning import interactive_reference as ir


def synthetic_unit():
    return {
        "schema": "em-experience-v1", "unit_id": "cs/verified-algorithms",
        "title": "Verified Algorithms and Returns", "source_mode": "synthetic",
        "knowledge_modes": ["computational", "formal_reasoning"],
        "sources": [{"id": "synthetic/model", "kind": "synthetic",
                     "locator": "Pure Python reference algorithms in this synthetic fixture"}],
        "claims": [{"id": "synthetic/invariant",
                    "text": "The lower bound preserves a half-open search interval.",
                    "source_refs": ["synthetic/model"], "evidence_status": "synthetic"}],
        "competencies": [{"id": "skill/tracing", "operation": "trace", "prerequisites": []}],
        "teaching": [{"id": "teaching/algorithm", "content": (
            "Prediction first: inspect an ordered sequence. "
            "A half-open interval [lo, hi) is reduced while retaining the "
            "first index whose value is at least the target. A finite return "
            "is calculated backward by V(t)=reward(t)+gamma*V(t+1)."),
            "competency_ids": ["skill/tracing"], "claim_ids": ["synthetic/invariant"]}],
        "assessments": [{"id": "assessment/transfer", "competency_ids": ["skill/tracing"],
                         "prompt": "Trace a search with duplicate elements and prove termination.",
                         "solution": "The interval is half-open. The upper bound never grows; "
                         "lo becomes mid+1 when a[mid]<target, otherwise hi becomes mid. "
                         "Each step reduces hi-lo, so termination follows.",
                         "rubric": [{"criterion": "States invariant", "points": 1},
                                   {"criterion": "Shows strict progress", "points": 1}],
                         "attempt_before_reveal": True}],
        "cards": [{"key": "tracing/search-invariant", "kind": "concept",
                   "front": "Which interval does lower-bound binary search maintain?",
                   "answer": "The half-open search interval [lo, hi).",
                   "competency_ids": ["skill/tracing"]}],
        "interactions": [
            {"id": "interaction/binary", "type": "code_trace",
             "competency_ids": ["skill/tracing"], "model_ref": "binary_search_lower_bound",
             "prediction_prompt": "Predict the lower-bound index before stepping.",
             "feedback_rule": "Check the invariant after every update.",
             "transfer_prompt": "What changes when the array has repeated values?",
             "variants": [
                 {"label": "Target 7", "parameters": {"values": [2, 5, 8, 12], "target": 7}},
                 {"label": "Absent target", "parameters": {"values": [2, 5, 8, 12], "target": 99}},
                 {"label": "Duplicate values", "parameters": {"values": [2, 5, 5, 12], "target": 5}},
             ]},
            {"id": "interaction/return", "type": "explorable_model",
             "competency_ids": ["skill/tracing"], "model_ref": "finite_discounted_return",
             "prediction_prompt": "Predict the finite discounted return before revealing it.",
             "feedback_rule": "Compare the backward recursion to the direct sum.",
             "transfer_prompt": "What happens to delayed rewards when gamma decreases?",
             "variants": [
                 {"label": "Undiscounted in effect", "parameters": {
                     "rewards": [1, 2, 3], "gamma": 0}},
                 {"label": "Moderate discount", "parameters": {
                     "rewards": [1, 2, 3], "gamma": 0.5}},
             ]},
        ],
    }


@pytest.mark.parametrize("values", [
    [], [1], [2, 2, 2], [1, 3, 6, 10],
    [-4, -1, 0, 0, 9], list(range(25)),
])
def test_binary_search_matches_bisect_left(values):
    for target in [-10, -1, 0, 1, 2, 5, 6, 99]:
        trace = ir.binary_search_trace({"values": values, "target": target})
        assert trace["result"] == bisect.bisect_left(values, target)
        assert len(trace["steps"]) <= 7
        for step in trace["steps"]:
            state = step["state"]
            if not values:
                assert state["mid"] == -1
                assert state["lo"] == state["hi"] == 0
            else:
                assert state["lo"] <= state["mid"] < state["hi"]
                assert state["next_hi"] - state["next_lo"] < state["hi"] - state["lo"]


@pytest.mark.parametrize("gamma", [0, .25, .5, .8, .99])
def test_discounted_return_matches_direct_sum(gamma):
    rewards = [-4, 0, 12, 2, -5, 1]
    trace = ir.discounted_return_trace({"rewards": rewards, "gamma": gamma})
    expected = math.fsum(x * gamma ** t for t, x in enumerate(rewards))
    assert trace["result"] == pytest.approx(expected)
    assert len(trace["steps"]) == len(rewards)


@pytest.mark.parametrize("parameters", [
    {"values": [3, 1], "target": 2},
    {"values": [1, 2], "target": float("nan")},
    {"values": [True], "target": 2},
    {"values": [1] * 65, "target": 1},
    {"values": "1,2,3", "target": 1},
])
def test_binary_search_fail_closed(parameters):
    with pytest.raises(ir.InteractionError):
        ir.binary_search_trace(parameters)


@pytest.mark.parametrize("parameters", [
    {"rewards": [1], "gamma": 1},
    {"rewards": [1], "gamma": -0.01},
    {"rewards": [1], "gamma": float("inf")},
    {"rewards": [], "gamma": .5},
    {"rewards": [True], "gamma": .5},
])
def test_discounted_return_fail_closed(parameters):
    with pytest.raises(ir.InteractionError):
        ir.discounted_return_trace(parameters)


def test_pipeline_validates_and_publishes_only_one_html_file(tmp_path):
    lesson = synthetic_unit()
    assert ex.validate(lesson)["valid"]
    first = ir.publish(lesson, tmp_path)
    assert first["status"] == "CREATED_OR_UPDATED"
    filename = tmp_path / "Interaktiv" / "index.html"
    html = filename.read_text()
    assert html.startswith("<!doctype html>")
    assert "Prediction first" in html
    assert "prefers-reduced-motion" in html
    assert "Scrollytelling" not in html  # feature, not decorative marketing claim
    assert "Neue Ordner" not in html
    assert "Verstehen" in html and "Selbstständig anwenden" in html
    assert not (tmp_path / "Lehrbuch.pdf").exists()
    before = filename.stat().st_mtime_ns
    again = ir.publish(lesson, tmp_path)
    assert again["status"] == "UNCHANGED"
    assert filename.stat().st_mtime_ns == before
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")
                  if p.is_file() and ".em-state" not in p.parts) == ["Interaktiv/index.html"]
    filename.write_text("manual modification", encoding="utf-8")
    with pytest.raises(ValueError, match="modified"):
        ir.publish(lesson, tmp_path)


def test_html_embedding_is_safe_and_model_results_verified():
    lesson = synthetic_unit()
    lesson["teaching"][0]["content"] = '</script><script>alert("XSS")</script>'
    lesson["interactions"][0]["variants"][0]["label"] = "</script><svg onload=alert(1)>"
    page = ir.render_html(lesson)
    assert 'content">\\u003c' not in page  # HTML content was escaped, not copied raw
    assert "<script>alert" not in page
    assert "\\u003c/script\\u003e" in page
    match = re.search(r'<script id="em-interactive-data" type="application/json">(.*?)</script>', page, re.S)
    assert match
    data = json.loads(match.group(1))
    assert data["interactions"][0]["variants"][0]["result"] == 2
    assert data["interactions"][1]["variants"][1]["result"] == pytest.approx(2.75)


def test_reject_arbitrary_model_and_no_fake_assessment():
    lesson = synthetic_unit()
    lesson["interactions"][0]["model_ref"] = "python:eval('2+2')"
    with pytest.raises(ir.InteractionError, match="Unsupported executable model"):
        ir.render_html(lesson)
    lesson = synthetic_unit()
    lesson["assessments"][0]["attempt_before_reveal"] = False
    with pytest.raises(ir.InteractionError, match="Invalid learning unit"):
        ir.render_html(lesson)


def test_offline_cli_renders_from_one_synthetic_json(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(json.dumps(synthetic_unit()), encoding="utf-8")
    assert ex.command(["render", str(source), "--out", str(tmp_path / "output")]) == 0
    assert (tmp_path / "output" / "Interaktiv" / "index.html").exists()


def test_browser_prediction_gates_and_interaction(tmp_path):
    api = pytest.importorskip("playwright.sync_api")
    page_path = tmp_path / "Interaktiv" / "index.html"
    ir.publish(synthetic_unit(), tmp_path)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            page = browser.new_page()
            requests = []
            page.on("request", lambda request: requests.append(request.url))
            page.goto(page_path.as_uri())
            first = page.locator("#interaction-interaction-binary")
            assert first.locator(".reveal").is_disabled()
            assert first.locator(".story-scenes").is_hidden()
            first.locator(".prediction").fill("2")
            first.locator(".check").click()
            assert first.locator(".story-scenes").is_visible()
            assert first.locator(".reveal").is_enabled()
            first.locator(".reveal").click()
            assert "Prediction matches" in first.locator(".result").inner_text()
            first.locator(".variant-picker").select_option("1")
            assert first.locator(".reveal").is_disabled()
            assert first.locator(".story-scenes").is_hidden()
            assessment = page.locator(".assessment").first
            assert assessment.locator(".answer-button").is_disabled()
            assessment.locator("textarea").fill("My own reasoning")
            assert assessment.locator(".answer-button").is_enabled()
            assessment.locator(".answer-button").click()
            assert assessment.locator(".answer").is_visible()
            assert all(x.startswith("file://") for x in requests), requests
        finally:
            browser.close()


def test_checked_in_synthetic_fixture_produces_real_offline_html(tmp_path):
    from pathlib import Path
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "experience_reference.json"
    unit = json.loads(fixture.read_text(encoding="utf-8"))
    assert unit["source_mode"] == "synthetic"
    assert ex.validate(unit)["valid"]
    r = ir.publish(unit, tmp_path)
    assert r["status"] == "CREATED_OR_UPDATED"
    assert (tmp_path / "Interaktiv" / "index.html").stat().st_size > 1000


def test_reasoned_derivation_is_in_offline_story():
    from pathlib import Path
    source = Path(__file__).resolve().parents[1] / "fixtures" / "experience_reference.json"
    unit = json.loads(source.read_text(encoding="utf-8"))
    page = ir.render_html(unit)
    proof = unit["teaching"][1]["derivation"]
    assert proof["title"] in page
    for step in proof["steps"]:
        assert step["statement"].replace("<", "&lt;") in page
        assert step["justification"].replace("<", "&lt;") in page
    assert page.count("Warum ist dieser Schritt zulässig?") == len(proof["steps"])
