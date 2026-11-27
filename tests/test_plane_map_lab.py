"""Plane transformation scene (reusable engine model, no course material): exact model vs sympy, browser mirror parity,
book/card figure from the same model, and the explorable in a real browser (predict -> step/scrub/play -> feedback)."""
import copy
import json
import random
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest
import sympy as sp

from exam_mastery import figures_svg
from exam_mastery.labs.plane_map import compute, singular_times
from exam_mastery.learning.interactive_reference import MODELS, build_interaction

ROOT = Path(__file__).resolve().parents[1]
CASES = [{"matrix": [[2, -1], [1, 1]], "vector": [1, 2]},
         {"matrix": [[1, 2], [2, 4]], "vector": [2, -1]},
         {"matrix": [[0, 1], [1, 0]], "vector": [1, 2], "t": 0.5},
         {"matrix": [[0, 0], [0, 0]], "vector": [1, 1]},
         {"matrix": [[1.5, 0.5], [-0.5, 2]], "vector": [-1, 0.5], "t": 0.25}]


def _sym(p):
    A = sp.Matrix([[sp.nsimplify(Fraction(str(x))) for x in r] for r in p["matrix"]])
    t = sp.nsimplify(Fraction(str(p.get("t", 1))))
    return A, (1 - t) * sp.eye(2) + t * A, sp.Matrix([sp.nsimplify(Fraction(str(x))) for x in p["vector"]])


@pytest.mark.parametrize("p", CASES + [{"matrix": [[random.Random(s).randint(-4, 4) / 2 for _ in range(2)] for _ in range(2)],
                                        "vector": [1, -1], "t": random.Random(s).choice([0, 0.5, 1])} for s in range(12)])
def test_model_matches_sympy(p):
    m = compute(p)
    A, M, v = _sym(p)
    assert sp.Rational(m["det_exact"]) == M.det()
    assert m["rank"] == M.rank()
    assert [sp.nsimplify(x) for x in m["Mv"]] == list(M * v)
    assert m["e1"] == [float(M[0, 0]), float(M[1, 0])] and m["e2"] == [float(M[0, 1]), float(M[1, 1])]
    for k in m["kernel"]:
        assert M * sp.Matrix(k) == sp.zeros(2, 1) and any(k)
    assert len(m["kernel"]) == 2 - M.rank() and len(m["image"]) == M.rank()
    if M.rank() == 1:   # image direction is a column direction
        assert sp.Matrix.hstack(M, sp.Matrix(m["image"][0])).rank() == 1
    tt = sp.symbols("t")
    roots = sorted(float(r) for r in sp.solve(((1 - tt) * sp.eye(2) + tt * A).det(), tt)
                   if r.is_real and 0 <= r <= 1) if ((1 - tt) * sp.eye(2) + tt * A).det().free_symbols else []
    assert all(abs(a - b) < 1e-9 for a, b in zip(singular_times(_frac(p["matrix"])), roots))
    assert len(singular_times(_frac(p["matrix"]))) == len(roots)


def _frac(mat):
    return [[Fraction(str(x)) for x in r] for r in mat]


def test_negative_determinant_forces_a_collapse_on_the_way():
    m = compute({"matrix": [[0, 1], [1, 0]], "vector": [1, 0]})
    assert m["det_A"] == -1 and m["singular_times"] == [0.5]
    mid = compute({"matrix": [[0, 1], [1, 0]], "vector": [1, 0], "t": 0.5})
    assert mid["rank"] == 1 and mid["kernel"] == [[1.0, -1.0]] and mid["image"] == [[1.0, 1.0]]


@pytest.mark.parametrize("bad", [{"matrix": [[1, 2]], "vector": [1, 1]}, {"matrix": [[1, 2], [3, 4]], "vector": [1]},
                                 {"matrix": [[1, 2], [3, 40]], "vector": [1, 1]}, {"matrix": [[1, 2], [3, 4]], "vector": [1, 1], "t": 2},
                                 {"matrix": [[1, True], [3, 4]], "vector": [1, 1]}, {"matrix": [[1, 2], [3, 4]], "vector": [1, 1], "x": 1}])
def test_invalid_parameters_are_rejected(bad):
    with pytest.raises(ValueError):
        compute(bad)


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_browser_mirror_has_parity_with_python(tmp_path):
    script = tmp_path / "run.js"
    script.write_text("const M=require(process.argv[2]);console.log(JSON.stringify(JSON.parse(process.argv[3]).map(M.compute)));")
    out = subprocess.run(["node", str(script), str(ROOT / "exam_mastery/templates/plane_map_math.js"), json.dumps(CASES)],
                         capture_output=True, text=True, check=True).stdout
    for js, p in zip(json.loads(out), CASES):
        py = compute(p)
        for key in ("M", "e1", "e2", "Mv", "Av"):
            assert json.dumps(js[key]) == json.dumps(py[key]) or all(
                abs(a - b) < 1e-12 for a, b in zip(sum(js[key], []) if key == "M" else js[key],
                                                   sum(py[key], []) if key == "M" else py[key])), key
        for key in ("rank", "rank_A", "orientation", "kernel", "image", "kernel_A", "image_A"):
            assert js[key] == py[key], key
        assert abs(js["det"] - py["det"]) < 1e-12 and len(js["singular_times"]) == len(py["singular_times"])


def test_figure_and_trace_use_the_same_model():
    p = {"matrix": [[1, 2], [2, 4]], "vector": [2, -1]}
    svg = figures_svg.render({"type": "plane_linear_map", "parameters": p, "title": "t", "alt": "a"})
    assert svg.startswith("<svg") and "<script" not in svg
    assert "Kern = span(2; −1)" in svg and "Bild = span(1; 2)" in svg and "Rang M = 1" in svg
    neg = figures_svg.render({"type": "plane_linear_map", "parameters": {"matrix": [[0, 1], [1, 0]], "vector": [1, 2]},
                              "title": "t", "alt": "a"})
    assert "Orientierung umgekehrt" in neg and "#be123c" in neg
    spec = build_interaction({"id": "i/plane", "type": "explorable_model", "model_ref": "plane_linear_map",
                              "prediction_prompt": "p", "feedback_rule": "f", "transfer_prompt": "t",
                              "variants": [{"label": "A, t = 1", "parameters": {"matrix": [[2, -1], [1, 1]], "vector": [1, 2]}}]})
    assert "plane_linear_map" in MODELS and spec["variants"][0]["result"] == 3.0
    assert spec["variants"][0]["steps"][3]["body"].endswith("0 + 2 = 2.")


def _unit_with_plane_lab():
    from exam_mastery.learning.experience import validate
    unit = copy.deepcopy(json.loads((ROOT / "fixtures/experience_attention_reference.json").read_text(encoding="utf-8")))
    inter = unit["interactions"][0]
    inter.update(model_ref="plane_linear_map", prediction_prompt="Wohin landet v?", transfer_prompt="Transfer.",
                 variants=[{"label": "Scherung, t = 0", "parameters": {"matrix": [[2, -1], [1, 1]], "vector": [1, 2], "t": 0}},
                           {"label": "Scherung, t = 1", "parameters": {"matrix": [[2, -1], [1, 1]], "vector": [1, 2], "t": 1}},
                           {"label": "Spiegelung", "parameters": {"matrix": [[0, 1], [1, 0]], "vector": [1, 2], "t": 1}}])
    for g in unit.get("graphics", []):
        g.update(model_ref="plane_linear_map", keyframes=[0, 1])
    assert validate(unit)["valid"], validate(unit)["errors"]
    return unit


def test_explorable_in_a_real_browser(tmp_path):
    pw = pytest.importorskip("playwright.sync_api")
    from exam_mastery.learning.interactive_reference import render_html
    from exam_mastery.learning.experience_graphics import specifications
    unit = _unit_with_plane_lab()
    assert len(specifications(unit)) == 2 * len(unit["graphics"])        # book keyframes from the same variants
    page_html = render_html(unit)
    assert page_html.count('class="plane-lab card"') == 1
    (tmp_path / "index.html").write_text(page_html, encoding="utf-8")
    errors, requests = [], []
    with pw.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 1400})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda r: requests.append(r.url) if not r.url.startswith(("file:", "data:", "about:")) else None)
        page.goto((tmp_path / "index.html").as_uri())
        lab = page.locator(".plane-lab")
        assert lab.locator(".pl-t").is_disabled() and lab.locator(".pl-step").is_disabled()   # predict first
        assert len(lab.locator(".pl-presets button").all()) == 2                             # one button per matrix
        lab.locator(".pl-guess-x").fill("0")
        lab.locator(".pl-guess-y").fill("3")
        lab.locator(".pl-sign input[value='+']").check()
        lab.locator(".pl-commit").click()
        for _ in range(4):
            lab.locator(".pl-step").click()
        text = lab.locator(".pl-feedback").inner_text()
        assert "✓ Treffer" in text and "Av = (0; 3)" in text and "✓ Vorzeichen" in text
        assert "det M = 2·1 − (−1)·1 = 3" in lab.locator(".pl-eq").inner_text()
        lab.locator(".pl-presets button").nth(1).click()                                  # reflection: new round
        assert lab.locator(".pl-t").is_disabled()
        lab.locator(".pl-skip").click()
        lab.locator(".pl-t").fill("0.49")                                                  # snaps to the singular time
        eq = lab.locator(".pl-eq").inner_text()
        assert "t = 0.5" in eq and "Rang M = 1" in eq and "Kern = span(1; −1)" in eq
        lab.locator(".pl-play").click()
        page.wait_for_function("document.querySelector('.plane-lab .pl-t-out').textContent==='t = 1'", timeout=8000)
        assert "Orientierung umgekehrt" in lab.locator(".pl-eq").inner_text()
        assert lab.locator(".pl-mark").count() == 1
        browser.close()
    assert not errors and not requests
