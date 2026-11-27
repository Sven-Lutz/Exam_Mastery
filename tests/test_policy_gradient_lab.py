"""Softmax policy-gradient explorable, graduated workbook and Anki figures (engine only, no course material)."""
import copy
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from exam_mastery import figures_svg
from exam_mastery.labs.policy_gradient import compute, exact
from exam_mastery.learning import experience_books
from exam_mastery.learning.experience import validate
from exam_mastery.learning.interactive_reference import MODELS, build_interaction

ROOT = Path(__file__).resolve().parents[1]
P = {"theta": [0.0, 0.5, -0.5], "rewards": [1.0, 2.0, 0.5], "noise_sd": 0.5,
     "baseline_mode": "expected", "batch": 64, "seed": 7, "step": 0.3}


def test_exact_gradient_matches_finite_differences():
    m = compute(P)
    for j in range(3):
        up, down = list(P["theta"]), list(P["theta"])
        up[j] += 1e-6; down[j] -= 1e-6
        fd = (exact(up, P["rewards"])["J"] - exact(down, P["rewards"])["J"]) / 2e-6
        assert math.isclose(m["grad"][j], fd, abs_tol=1e-8)
    assert abs(sum(m["grad"])) < 1e-12


def test_variance_formula_matches_monte_carlo():
    rng = np.random.default_rng(0)
    theta, rewards, sd = np.array(P["theta"]), np.array(P["rewards"]), P["noise_sd"]
    pi = np.exp(theta) / np.exp(theta).sum()
    a = rng.choice(3, size=300000, p=pi)
    ret = rewards[a] + sd * rng.standard_normal(a.size)
    for b in (0.0, float(pi @ rewards), -1.0):
        g = (ret - b)[:, None] * (np.eye(3)[a] - pi)
        assert math.isclose(g.var(0).sum(), exact(list(theta), list(rewards), sd)["variance"](b), rel_tol=0.02)
    ex = exact([1.0986122886681098, 0.0], [1.0, -1.0])
    assert math.isclose(ex["b_opt"], -0.5, abs_tol=1e-12) and abs(ex["variance"](ex["b_opt"])) < 1e-12
    assert ex["variance"](0.5) > ex["variance"](0.0)  # b = J is not always better


def test_sampled_estimate_is_reproducible_and_unbiased_on_average():
    assert compute(P)["estimate"] == compute(P)["estimate"]
    runs = [compute({**P, "seed": s, "batch": 200})["estimate"] for s in range(200)]
    assert np.allclose(np.mean(runs, axis=0), compute(P)["grad"], atol=0.01)


@pytest.mark.parametrize("bad", [{"theta": [0]}, {"theta": [0, 0], "rewards": [1]}, {**P, "batch": 0},
                                 {**P, "baseline_mode": "other"}, {**P, "theta": [0, float("nan"), 0]}, {**P, "code": 1}])
def test_invalid_parameters_are_rejected(bad):
    with pytest.raises(ValueError):
        compute({"rewards": [1, 2], **bad} if "rewards" not in bad else bad)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_browser_mirror_has_parity_with_python(tmp_path):
    script = tmp_path / "run.js"
    script.write_text("const M=require(process.argv[2]);const r=M.compute(JSON.parse(process.argv[3]));"
                      "delete r.variance_curve;console.log(JSON.stringify(r));")
    for params in (P, {**P, "baseline_mode": "constant", "baseline": 1.5, "batch": 300, "seed": 11},
                   {"theta": [1.0, 0.0], "rewards": [1.0, -1.0], "batch": 5}):
        out = subprocess.run(["node", str(script), str(ROOT / "exam_mastery/templates/policy_gradient_math.js"),
                              json.dumps(params)], capture_output=True, text=True, check=True).stdout
        js, py = json.loads(out), compute(params)
        assert js["actions"] == py["actions"]
        for key in ("pi", "grad", "estimate", "estimate_none", "theta_new", "returns"):
            assert np.allclose(js[key], py[key], rtol=1e-12, atol=1e-12), key
        for key in ("J", "variance_none", "variance_baseline", "variance_first_none", "variance_first_baseline", "b_opt"):
            assert math.isclose(js[key], py[key], rel_tol=1e-12, abs_tol=1e-12), key


def test_figure_and_trace_use_the_same_model():
    svg = figures_svg.render({"type": "softmax_policy_gradient", "parameters": P, "title": "t", "alt": "a"})
    assert svg.startswith("<svg") and "b*" in svg and "<script" not in svg
    spec = build_interaction({"id": "i/pg", "type": "explorable_model", "model_ref": "softmax_policy_gradient",
                              "prediction_prompt": "p", "feedback_rule": "f", "transfer_prompt": "t",
                              "variants": [{"label": "v", "parameters": P}]})
    assert "softmax_policy_gradient" in MODELS
    assert math.isclose(spec["variants"][0]["result"], compute(P)["grad"][0])
    assert spec["variants"][0]["steps"][0]["state"]["kind"] == "svg"


def _staged_unit():
    unit = json.loads((ROOT / "fixtures/experience_attention_reference.json").read_text(encoding="utf-8"))
    unit = copy.deepcopy(unit)
    tasks = unit["assessments"]
    tasks[0].update(stage="worked_example", solution_steps=[["Schritt", "Grund"]], title="Durchgerechnet")
    tasks[1].update(stage="guided", scaffold=["___"])
    for t in tasks[2:]:
        t["stage"] = "independent"
    tasks[-1]["stage"] = "exam"
    tasks[-1]["typical_errors"] = ["Ein typischer Fehler"]
    unit["sources"][0]["short"] = "Vaswani et al. 2017"
    unit["teaching"][0]["blocks"] = [{"type": "definition", "term": "Begriff", "md": "Text"},
                                     {"type": "box", "kind": "key", "title": "Satz", "md": "Aussage"}]
    return unit


def test_graduated_workbook_stages_and_worked_examples():
    unit = _staged_unit()
    assert validate(unit)["valid"], validate(unit)["errors"]
    book = experience_books.book_model(unit)
    assert [s["key"] for s in book["stages"]] == ["worked_example", "guided", "independent", "exam"]
    worked = book["stages"][0]["items"][0]
    assert worked["worked"] and worked["solution"]["steps"] == [["Schritt", "Grund"]]
    assert book["stages"][1]["items"][0]["scaffold"] == ["___"]
    body, toc = experience_books._combined_workbook(book)
    assert "Stufe 1 · Durchgerechnete Beispiele" in body and "Typische Fehler" in body
    assert not any("Stufe 1" in entry[2] and "Lösungen" in entry[2] for entry in toc)
    first = book["sections"][0]["blocks"]
    assert [b["type"] for b in first[:3]] == ["lead", "definition", "box"]


def test_invalid_presentation_fields_are_rejected():
    unit = _staged_unit()
    unit["assessments"][0]["stage"] = "warmup"
    unit["assessments"][1]["solution_steps"] = [["nur eins"]]
    unit["teaching"][0]["blocks"].append({"type": "graphic", "id": "graphic/unknown"})
    unit["cards"][0]["figure"] = "graphic/unknown-state-0"
    errors = " ".join(validate(unit)["errors"])
    for text in ("stage must be one of", "solution_steps", "graphic must be placed", "figure must name"):
        assert text in errors


def test_anki_cards_receive_graphic_keyframes(tmp_path):
    pytest.importorskip("anki")
    from exam_mastery.learning import experience_anki
    unit = json.loads((ROOT / "fixtures/experience_attention_reference.json").read_text(encoding="utf-8"))
    graphic = unit["graphics"][0]
    name = graphic["id"] + "-state-" + str(graphic["keyframes"][0])
    unit["cards"][0]["figure"] = name
    assert validate(unit)["valid"]
    report = experience_anki.publish(unit, tmp_path)
    assert report["status"] == "CREATED_OR_UPDATED"
    import zipfile
    with zipfile.ZipFile(tmp_path / "Anki.apkg") as z:
        media = json.loads(z.read("media"))
    assert any(v.endswith(".svg") for v in media.values())
