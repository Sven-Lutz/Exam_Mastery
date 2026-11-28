"""Plane transformation scene (reusable engine model, no course material): exact model vs sympy, browser mirror parity,
book/card figure from the same model, and the explorable in a real browser (predict -> step/scrub/play -> feedback).
Since MOTION-2 the model is Mastery Motion's linear_map_2d (motion/models.py + templates/mastery_motion.js) and the
explorable is a Motion scene; the experience schema {matrix, vector[, t]} is unchanged."""
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
from exam_mastery.learning.interactive_reference import MODELS, build_interaction
from exam_mastery.motion import PALETTE
from exam_mastery.motion.models import linear_map_2d, plane_params, singular_times


def compute(p):
    return linear_map_2d(plane_params(p))

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
    assert m["singular_times"] == singular_times(_frac(p["matrix"]))


def _frac(mat):
    return [Fraction(str(x)) for r in mat for x in r]


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
    script.write_text("const M=require(process.argv[2]);"
                      "console.log(JSON.stringify(JSON.parse(process.argv[3]).map(M.MODELS.linear_map_2d)));")
    out = subprocess.run(["node", str(script), str(ROOT / "exam_mastery/templates/mastery_motion.js"),
                          json.dumps([plane_params(p) for p in CASES])], capture_output=True, text=True, check=True).stdout
    for js, p in zip(json.loads(out), CASES):
        py = compute(p)
        for key in ("M", "A", "e1", "e2", "Mv", "Av", "square"):
            flat = (lambda x: sum(x, [])) if key == "square" else (lambda x: x)
            assert all(abs(a - b) < 1e-12 for a, b in zip(flat(js[key]), flat(py[key]))), key
        for key in ("rank", "rank_A", "orientation", "kernel", "image", "kernel_A", "image_A", "kernel_line", "image_line"):
            assert js[key] == py[key] or json.dumps(js[key]) == json.dumps(py[key]), key
        for key in [k for k, v in py.items() if isinstance(v, str) and not k.endswith("_exact")]:   # readout strings
            assert js[key] == py[key], key
        assert abs(js["det"] - py["det"]) < 1e-12 and len(js["singular_times"]) == len(py["singular_times"])
        assert all(abs(a - b) < 1e-12 for a, b in zip(js["singular_times"], py["singular_times"]))


def test_figure_and_trace_use_the_same_model():
    p = {"matrix": [[1, 2], [2, 4]], "vector": [2, -1]}
    svg = figures_svg.render({"type": "plane_linear_map", "parameters": p, "title": "t", "alt": "a"})
    assert svg.startswith("<svg") and "<script" not in svg
    assert "Kern = span(2; −1)" in svg and "Bild = span(1; 2)" in svg and "Rang M = 1" in svg
    assert "det M = 1·4 − 2·2 = 0" in svg and "Fläche 0" in svg
    assert PALETTE["kernel"]["color"] in svg and PALETTE["image"]["color"] in svg        # kernel/image lines drawn
    assert svg == figures_svg.render({"type": "plane_linear_map", "parameters": p, "title": "t", "alt": "a"})
    neg = figures_svg.render({"type": "plane_linear_map", "parameters": {"matrix": [[0, 1], [1, 0]], "vector": [1, 2]},
                              "title": "t", "alt": "a"})
    assert "Orientierung umgekehrt" in neg and PALETTE["area"]["color"] in neg
    assert 'fill="url(#' in neg and '-hatch)"' in neg                                     # orientation flip: hatched
    long = figures_svg.render({"type": "plane_linear_map", "parameters": p, "title": "Eine sehr lange Bildunterschrift " * 12,
                               "alt": "a"})                                   # long captions/labels from real units
    assert "Rang M = 1" in long
    from exam_mastery.motion.plane import unit_scene
    sc = unit_scene({"id": "i/plane", "prediction_prompt": "x" * 900,
                     "variants": [{"label": "Sehr langer Name " * 10 + ", t = 1", "parameters": p}]})
    assert len(sc["presets"][0]["label"]) <= 80 and sc["steps"][1]["checkpoint"]["predict"][0]["prompt"].startswith("Vorhersage")
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


def _wait(page, step):
    page.wait_for_function(f"() => document.querySelector('.plane-lab .mm-scene').dataset.step === '{step}' && "
                           "Number(document.querySelector('.plane-lab .mm-scene').dataset.pos) % 1 === 0")


def test_explorable_in_a_real_browser(tmp_path):
    pw = pytest.importorskip("playwright.sync_api")
    from exam_mastery.learning.interactive_reference import render_html
    from exam_mastery.learning.experience_graphics import specifications
    unit = _unit_with_plane_lab()
    assert len(specifications(unit)) == 2 * len(unit["graphics"])        # book keyframes from the same variants
    page_html = render_html(unit)
    assert page_html.count('class="plane-lab card"') == 1 and page_html.count('class="mm-scene"') == 1
    assert "EMPlaneMap" not in page_html                                   # one model: the Motion runtime only
    (tmp_path / "index.html").write_text(page_html, encoding="utf-8")
    errors, requests = [], []
    with pw.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 1400})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("request", lambda r: requests.append(r.url) if not r.url.startswith(("file:", "data:", "about:")) else None)
        page.goto((tmp_path / "index.html").as_uri())
        lab = page.locator(".plane-lab .mm-scene.mm-ready")
        assert lab.get_attribute("data-error") is None
        stage = lab.locator("svg.mm-stage")
        assert lab.locator("[data-action=next]").is_disabled()                                  # predict first
        lab.locator(".mm-scrub").evaluate("e => { e.value = '4'; e.dispatchEvent(new Event('input')); }")
        assert lab.get_attribute("data-pos") == "0.000"                                         # timeline locked
        assert len(lab.locator(".mm-presets button").all()) == 2                                # one button per matrix
        lab.locator('[data-question="av"] input[data-coord="0"]').fill("0")
        lab.locator('[data-question="av"] input[data-coord="1"]').fill("3")
        lab.locator('[data-question="det-sign"] [data-answer="+"]').click()
        lab.locator("[data-action=commit]").click()
        lab.locator("[data-action=reveal]").click()
        _wait(page, "quarter")
        for step in ("half", "three-quarters", "image"):
            lab.locator("[data-action=next]").click()
            _wait(page, step)
        marks = lab.locator('[data-feedback="quarter"] [data-correct]')
        assert [m.get_attribute("data-correct") for m in marks.all()] == ["true", "true"]
        text = lab.locator('[data-feedback="quarter"]').inner_text()
        assert "✓ Av: Ihre Vorhersage: (0; 3)" in text and "Av = 1·(2; 1) + 2·(−1; 1) = (0; 3)" in text
        assert "✓ det A" in text and "det A = 3" in text
        assert "det M = 2·1 − (−1)·1 = 3" in stage.text_content()
        lab.locator(".mm-presets button").nth(1).click()                                         # reflection: new round
        assert lab.locator("[data-action=next]").is_disabled() and lab.get_attribute("data-step") == "identity"
        lab.locator("[data-action=skip]").click()
        _wait(page, "quarter")
        lab.locator(".mm-scrub").evaluate("e => { e.value = '1.96'; e.dispatchEvent(new Event('input')); }")  # t = 0.49
        st = json.loads(lab.get_attribute("data-state"))
        assert st["t"] == 0.5 and st["rank"] == 1                                                # snapped onto det = 0
        txt = stage.text_content()
        assert "t = 0,5" in txt and "Rang M = 1" in txt and "Kern = span(1; −1)" in txt and "Bild = span(1; 1)" in txt
        assert lab.locator('[data-o="kernel"] polyline').count() == 1 and lab.locator('[data-o="image"] polyline').count() == 1
        lab.locator("[data-action=play]").click()
        page.wait_for_function("document.querySelector('.plane-lab .mm-scene').dataset.step === 'image'", timeout=8000)
        assert "Orientierung umgekehrt" in stage.text_content()
        assert lab.locator(".mm-snap").count() == 1
        browser.close()
    assert not errors and not requests
