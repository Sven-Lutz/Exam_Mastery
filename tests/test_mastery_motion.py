"""Mastery Motion (standard §4): scene grammar, Python reference vs. browser runtime parity at every keyframe (V10),
computed checkpoint answers, keyframe SVG export (V8) and the RL flagship scene's mathematics (synthetic numbers)."""
import copy
import json
import math
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest

from exam_mastery import motion as M
from exam_mastery.labs.policy_gradient import compute, exact
from exam_mastery.motion import embed
from exam_mastery.motion.models import linear_map_2d, softmax_simplex_pg

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "exam_mastery/templates"
RL = "rl-softmax-simplex"
PLANE = "plane-linear-map"
HAVE_NODE = shutil.which("node") is not None


def scene():
    return M.load(RL)


def _node(script, *args):
    return subprocess.run(["node", "-e", script, *args], capture_output=True, text=True, check=True, timeout=60).stdout


NODE_PRELUDE = ("global.EMPolicyGradient=require(process.argv[1]);const MM=require(process.argv[2]);"
                "const sc=JSON.parse(require('fs').readFileSync(process.argv[3],'utf8'));")


# ------------------------------------------------------------------ grammar

def test_flagship_scene_validates_and_is_public_safe():
    sc = scene()
    states = M.validate(sc)
    assert len(states) == len(sc["steps"]) >= 6
    assert sc["public"] is True and sc["model"] == "softmax_simplex_pg"
    text = json.dumps(sc, ensure_ascii=False)
    for forbidden in ("/Users/", "Vorlesung", "Folie", "http"):
        assert forbidden not in text
    # every checkpoint is a prediction before a reveal; every term is coupled to objects of its own colour token
    kinds = [q["type"] for st in sc["steps"] if st.get("checkpoint") for q in st["checkpoint"]["predict"]]
    assert "direction" in kinds and kinds.count("choice") == 2
    for t in sc["terms"].values():
        assert all(next(o for o in sc["objects"] if o["id"] == oid)["token"] == t["token"] for oid in t["objects"])
    assert all(len(m["sliders"]) <= 3 for m in sc["missions"])


@pytest.mark.parametrize("mutate, message", [
    (lambda s: s.update(schema="x"), "schema"),
    (lambda s: s.update(extra=1), "unknown fields"),
    (lambda s: s["objects"].append({"id": "x", "type": "teapot", "panel": "grad", "meaning": "m"}), "object type"),
    (lambda s: s["objects"][1].update(token="rainbow"), "colour token"),
    (lambda s: s["terms"]["grad"].update(objects=["cloud"]), "share the term's colour token"),
    (lambda s: s["equation"]["segments"].pop(0), "every term must appear"),
    (lambda s: s["steps"][2]["checkpoint"]["predict"][0]["correct"].update(rule="literal"), "computed correct rule"),
    (lambda s: s["steps"][5]["checkpoint"]["predict"][0]["correct"]["map"].update({"0": "nope"}), "not an option"),
    (lambda s: s["steps"][3].update(set={"unknown": 1}), "unknown parameter"),
    (lambda s: s["steps"][3].update(set={"n": 10_000}), "parameter n"),
    (lambda s: s["steps"][0].update(checkpoint=s["steps"][2]["checkpoint"]), "first step"),
    (lambda s: s["missions"][0]["sliders"].extend([{"param": "b0", "label": "x"}] * 3), "1..3 sliders"),
    (lambda s: s["objects"][6].update(text="{nonexistent:2}"), "unknown state quantity"),
    (lambda s: s["steps"][1].update(caption="J = {missing}"), "unknown state quantity"),
])
def test_invalid_scenes_are_rejected(mutate, message):
    sc = copy.deepcopy(scene())
    mutate(sc)
    with pytest.raises(M.SceneError) as err:
        M.validate(sc)
    assert message in str(err.value)


def test_grammar_expresses_the_plane_transformation_primitives():
    """Not a shipped scene: proves grid, basis vectors, linear-map interpolation and signed area are expressible."""
    sc = {"schema": M.SCHEMA, "id": "plane-probe", "title": "Probe", "claim": "Die Spalten von A sind die Bilder der Basis.",
          "model": "linear_map_2d", "params": {"A": {"value": [1.0, 2.0, 1.0, 1.0], "min": -3, "max": 3},
                                               "t": {"value": 0.0, "min": 0, "max": 1},
                                               "v": {"value": [1.0, 1.0]}},
          "view": {"width": 400, "height": 400, "panels": [{"id": "plane", "x": 0, "y": 0, "w": 400, "h": 400,
                                                             "domain": [-4, 4, -4, 4], "clip": True}]},
          "objects": [{"id": "grid", "type": "grid", "panel": "plane", "matrix": "M", "token": "muted", "meaning": "Gitter"},
                      {"id": "square", "type": "polygon", "panel": "plane", "points": "square", "orientation": "orientation",
                       "token": "area", "meaning": "Bild des Einheitsquadrats"},
                      {"id": "e1", "type": "vector", "panel": "plane", "to": "e1", "token": "basis1", "label": "Ae₁", "meaning": "m"},
                      {"id": "e2", "type": "vector", "panel": "plane", "to": "e2", "token": "basis2", "label": "Ae₂", "meaning": "m"},
                      {"id": "det", "type": "label", "panel": "plane", "x": 8, "y": 20, "text": "det = {det:2}", "meaning": "m"}],
          "terms": {"det": {"name": "Determinante", "token": "area", "objects": ["square"]}},
          "equation": {"label": "Fläche", "segments": [{"tex": "\\det A", "text": "det A", "term": "det"}]},
          "steps": [{"id": "id", "title": "Identität", "caption": "det = {det:2}", "aria": "Gitter"},
                    {"id": "map", "title": "A", "caption": "det = {det:2}", "aria": "Gitter",
                     "set": {"t": 1.0}, "transition": {"kind": "interpolate", "animate": ["t"], "ms": 1500},
                     "checkpoint": {"predict": [{"id": "sign", "type": "sign", "prompt": "Vorzeichen von det?",
                                                 "correct": {"rule": "sign", "of": "det"}}], "explain": "det = {det:2}"}}],
          "missions": [{"id": "flatten", "from_step": "map", "prompt": "Bringe die Determinante auf 0.", "hint": "Spalten parallel.",
                        "feedback": "det = {det:2}", "sliders": [{"param": "A", "index": 1, "label": "a₁₂"}],
                        "goal": {"of": "det", "op": "abs<=", "value": 0.05}}]}
    states = M.validate(sc)
    flat = M.evaluate(sc, {**M.params_at(sc, 1), "A": [1.0, 1.0, 1.0, 1.0]})
    assert M.goal_met(flat, sc["missions"][0]["goal"]) and not M.goal_met(states[1], sc["missions"][0]["goal"])
    bad = copy.deepcopy(sc)
    del bad["missions"][0]["sliders"][0]["index"]
    with pytest.raises(M.SceneError, match="needs an index"):
        M.validate(bad)
    assert states[0]["det"] == 1.0 and math.isclose(states[1]["det"], -1.0)
    assert M.correct_answer(sc, states[1], sc["steps"][1]["checkpoint"]["predict"][0]) == "-"
    assert states[1]["e1"] == [1.0, 1.0] and states[1]["e2"] == [2.0, 1.0]  # columns of A
    prims = M.display(sc, states[1])
    assert any(p["k"] == "area" and p["neg"] for p in prims)  # orientation flip is drawn hatched, not only coloured
    assert sum(p["k"] == "line" for p in prims) == 18
    half = linear_map_2d({"A": [1.0, 2.0, 1.0, 1.0], "t": 1 / math.sqrt(2), "v": [1.0, 1.0]})  # det M(t) = 1 - 2t^2
    assert math.isclose(half["det"], 0.0, abs_tol=1e-12)  # the plane collapses on the way ...
    assert len(half["singular_times"]) == 1 and math.isclose(half["singular_times"][0], 1 / math.sqrt(2), rel_tol=1e-12)
    flat = linear_map_2d({"A": [1.0, 2.0, 1.0, 1.0], "t": 0.5, "v": [1.0, 1.0]})  # ... and exactly where it is rational:
    assert linear_map_2d({"A": [0.0, 1.0, 1.0, 0.0], "t": 0.5, "v": [1.0, 0.0]})["orientation"] == 0 and flat["rank"] == 2


# ------------------------------------------------------------------ mathematics of the flagship scene (V10)

def test_flagship_model_reuses_the_trusted_bandit_model():
    sc = scene()
    i = [s["id"] for s in sc["steps"]].index("cloud-grows")
    p = M.params_at(sc, i)
    st = softmax_simplex_pg(p)
    lab = compute({"theta": p["theta0"], "rewards": p["rewards"], "noise_sd": p["noise_sd"], "baseline_mode": "none",
                   "batch": p["n"], "seed": p["seed"], "step": p["alpha"]})
    assert st["actions"] == lab["actions"] and np.allclose(st["returns"], lab["returns"], atol=1e-12)
    assert np.allclose(st["grad"], lab["grad"], atol=1e-15)
    assert np.allclose(st["sample_mean"], lab["estimate_none"], atol=1e-12)  # the cloud's mean is the REINFORCE estimate
    assert math.isclose(st["var_none"], lab["variance_none"] * p["n"], rel_tol=1e-12)


def test_exact_gradient_and_first_order_motion_match_numpy():
    th, r = np.array([0.6, -0.2, 0.3]), np.array([1.0, 2.0, 0.2])
    st = softmax_simplex_pg({"theta0": th.tolist(), "rewards": r.tolist(), "noise_sd": 0.5, "alpha": 1.5, "k": 0, "n": 0,
                             "seed": 2, "b0": 0.0, "lam": 0.0, "g_vis": 1.0})
    pi = np.exp(th) / np.exp(th).sum()
    jac = np.diag(pi) - np.outer(pi, pi)
    assert np.allclose(st["grad"], jac @ r, atol=1e-14)  # dJ/dtheta = (diag pi - pi pi^T) r
    assert np.allclose(st["dpi"], 1.5 * jac @ (jac @ r), atol=1e-14)
    eps = 1e-6
    for j in range(3):
        e = np.eye(3)[j] * eps
        fd = (exact((th + e).tolist(), r.tolist())["J"] - exact((th - e).tolist(), r.tolist())["J"]) / (2 * eps)
        assert math.isclose(st["grad"][j], fd, abs_tol=1e-9)


def test_baseline_keeps_the_mean_and_shrinks_the_spread_symbolically():
    sp = pytest.importorskip("sympy")
    p1, p2, r1, r2, r3, b = sp.symbols("p1 p2 r1 r2 r3 b", real=True)
    pi = [p1, p2, 1 - p1 - p2]
    r = [r1, r2, r3]
    score = [[(1 if j == a else 0) - pi[j] for j in range(3)] for a in range(3)]
    for j in range(3):  # E[(R - b) s_j] does not depend on b
        mean = sum(pi[a] * (r[a] - b) * score[a][j] for a in range(3))
        assert sp.simplify(sp.diff(mean, b)) == 0
    # numerically at the scene's policy: spread with b = J is smaller than without; b_opt is the minimiser
    sc = scene()
    st = M.states(sc)[[s["id"] for s in sc["steps"]].index("baseline-on")]
    assert st["var_b"] < st["var_none"] and st["var_opt"] <= st["var_b"] + 1e-15
    assert st["mean_shift"] < 1e-12 and st["var_delta"] < 0


def test_sample_cloud_variance_matches_the_formula_monte_carlo():
    sc = scene()
    p = {**M.params_at(sc, 0), "n": 400, "lam": 1.0}
    spreads = [softmax_simplex_pg({**p, "seed": s})["sample_spread"] ** 2 for s in range(150)]
    st = softmax_simplex_pg(p)
    assert math.isclose(np.mean(spreads), st["var_b"] * (1 - 1 / 400), rel_tol=0.03)


def test_gradient_ascent_moves_pi_towards_the_best_action_and_raises_j():
    sc = scene()
    states = M.states(sc)
    j_values = [s["J"] for s in states]
    assert j_values[-1] > j_values[-2] > j_values[0]
    assert states[-1]["pi"][1] > 0.85 and len(states[-1]["pi_trail"]) == 7
    mid = softmax_simplex_pg({**M.params_at(sc, len(sc["steps"]) - 1), "k": 2.5})
    a, b = softmax_simplex_pg({**M.params_at(sc, 0), "k": 2}), softmax_simplex_pg({**M.params_at(sc, 0), "k": 3})
    assert np.allclose(mid["theta"], (np.array(a["theta"]) + np.array(b["theta"])) / 2)  # fractional k: linear in theta


def test_checkpoint_answers_are_computed_not_written():
    sc = scene()
    states = M.states(sc)
    ids = [s["id"] for s in sc["steps"]]
    grad_q = sc["steps"][ids.index("exact-gradient")]["checkpoint"]["predict"][0]
    st = states[ids.index("exact-gradient")]
    deg = M.correct_answer(sc, st, grad_q)["deg"]
    g = st["grad"]  # independent: world direction of sum_a g_a u_a (screen y is flipped twice)
    wx = sum(g[a] * M.TRI[a][0] for a in range(3))
    wy = sum(g[a] * M.TRI[a][1] for a in range(3))
    assert math.isclose(deg, math.degrees(math.atan2(wy, wx)) % 360, abs_tol=1e-9)
    assert M.is_correct(sc, st, grad_q, "NW") and not M.is_correct(sc, st, grad_q, "SE")
    base = sc["steps"][ids.index("baseline-on")]["checkpoint"]["predict"]
    st = states[ids.index("baseline-on")]
    assert [M.correct_answer(sc, st, q) for q in base] == ["same", "smaller"]
    m = sc["missions"][0]
    p = {**M.params_at(sc, ids.index(m["from_step"])), **m["fixed"]}
    assert not M.goal_met(softmax_simplex_pg({**p, "b0": 0.0}), m["goal"])
    b_opt = softmax_simplex_pg(p)["b_opt"]
    assert M.goal_met(softmax_simplex_pg({**p, "b0": round(b_opt / 0.05) * 0.05}), m["goal"])  # reachable on the slider grid


# ------------------------------------------------------------------ keyframes (V8)

def test_keyframe_svg_is_deterministic_and_standalone(tmp_path):
    sc = scene()
    a = M.export_keyframes(sc, tmp_path / "a", "textbook")
    b = M.export_keyframes(sc, tmp_path / "b", "textbook")
    assert [p.name for p in a] == [f"{RL}-{s}.svg" for s in sc["keyframes"]["textbook"]]
    for x, y in zip(a, b):
        text = x.read_text()
        assert text == y.read_text()
        tree = ET.fromstring(text)
        assert tree.tag.endswith("svg") and not any(e.tag.split("}")[-1] in ("script", "foreignObject", "image") for e in tree.iter())
        assert "http" not in text.replace("http://www.w3.org/2000/svg", "")
    svg = M.keyframe_svg(sc, "baseline-on")
    for token in ("grad", "sample", "baseline", "policy"):
        assert M.PALETTE[token]["color"] in svg  # same palette as the interactive scene
    assert "<desc" in svg and "0,63" in svg  # computed numbers in the description and readouts
    hidden = M.keyframe_svg(sc, "policy-point")
    assert "∇J" not in hidden.split("</desc>")[1]  # objects hidden at a step are not exported


def test_embedding_hook_for_units_and_demo_page(tmp_path):
    assert embed.scenes_for_unit({"interactions": [{"model_ref": "softmax_policy_gradient"}]}) == [RL]
    assert embed.unit_html({"interactions": [{"model_ref": "binomial_area_partition"}]}) == ""
    html = embed.unit_html({"interactions": [{"model_ref": "softmax_policy_gradient"}]})
    assert 'class="mm-scene"' in html and "MasteryMotion" in html and "</script><" in html
    data = html.split('class="mm-data">', 1)[1].split("</script>", 1)[0]
    assert "<" not in data and json.loads(data)["revision"] == M.revision(scene())
    demos = {d["id"]: d for d in embed.write_demo_pages(tmp_path)}
    assert set(demos) == {RL, PLANE} and demos[RL]["href"] == f"motion/{RL}.html" and (tmp_path / demos[RL]["href"]).is_file()
    page = (tmp_path / demos[PLANE]["href"]).read_text()
    assert "script-src 'self'" in page and "<script>" not in page  # CSP: no inline scripts on the demo page
    assert all((tmp_path / "assets" / n).is_file() for n in embed.ASSETS)


# ------------------------------------------------------------------ JS <-> Python parity (V10)

def _close(a, b):
    if isinstance(b, bool) or b is None or isinstance(b, str):
        return a == b
    if isinstance(b, (int, float)):
        return isinstance(a, (int, float)) and math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-12)
    if isinstance(b, list):
        return isinstance(a, list) and len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b))
    if isinstance(b, dict):
        return isinstance(a, dict) and set(a) >= set(b) and all(_close(a[k], v) for k, v in b.items())
    return a == b


@pytest.mark.skipif(not HAVE_NODE, reason="node not installed")
@pytest.mark.parametrize("sid", [RL, PLANE])
def test_browser_runtime_matches_python_at_every_keyframe(tmp_path, sid):
    """V10: every state quantity, display primitive, caption, aria text and computed answer, for every preset."""
    sc = M.payload(M.load(sid), equation_svg=False)
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(sc), encoding="utf-8")
    presets = [None] + [p["id"] for p in sc.get("presets", [])]
    out = _node(NODE_PRELUDE + "const out={};for(const pr of JSON.parse(process.argv[4])){"
                "const over=pr?sc.presets.find(x=>x.id===pr).set:null,panels=MM.panelsFor(sc,pr);"
                "out[pr||'']=sc.steps.map((st,i)=>{const s=MM.evaluate(sc,MM.paramsAt(sc,i,over));"
                "return {state:s,display:MM.display(sc,s,panels),caption:MM.textOf(st.caption,s),aria:MM.textOf(st.aria,s),"
                "labels:sc.objects.filter(o=>o.type==='label').map(o=>MM.textOf(o.text,s)),"
                "answers:st.checkpoint?st.checkpoint.predict.map(q=>MM.correctAnswer(sc,s,q)):null,"
                "explain:st.checkpoint?MM.textOf(st.checkpoint.explain,s):null};});}"
                "console.log(JSON.stringify(out));",
                str(TEMPLATES / "policy_gradient_math.js"), str(TEMPLATES / "mastery_motion.js"), str(path), json.dumps(presets))
    js = json.loads(out)
    checked = 0
    for pr in presets:
        for i, st in enumerate(sc["steps"]):
            ref, got = M.evaluate(sc, M.params_at(sc, i, pr)), js[pr or ""][i]
            where = (sid, pr, st["id"])
            assert got["caption"] == M.text_of(st["caption"], ref), where
            assert got["aria"] == M.text_of(st["aria"], ref), where
            assert got["labels"] == [M.text_of(o["text"], ref) for o in sc["objects"] if o["type"] == "label"], where
            for key, value in ref.items():
                if not key.endswith("_exact"):  # exact rational strings exist only in the Python reference
                    assert _close(got["state"][key], value), (where, key)
            prims = M.display(sc, ref, M.panels_for(sc, pr))
            assert len(got["display"]) == len(prims), where
            for a, b in zip(got["display"], prims):
                assert a["o"] == b["o"] and a["k"] == b["k"] and a["t"] == b["t"], where
                for k, v in b.items():
                    if isinstance(v, float):
                        assert math.isclose(a[k], v, abs_tol=1e-9), (where, b["o"], k)
                    elif k == "pts":
                        assert np.allclose(a[k], v, atol=1e-9)
                    else:
                        assert a[k] == v, (where, b["o"], k)
            if st.get("checkpoint"):
                assert got["explain"] == M.text_of(st["checkpoint"]["explain"], ref), where
                want = [M.correct_answer(sc, ref, q) for q in st["checkpoint"]["predict"]]
                for x, y in zip(got["answers"], want):
                    assert (math.isclose(x["deg"], y["deg"], abs_tol=1e-9) if isinstance(y, dict) and "deg" in y
                            else _close(x, y)), where
            checked += 1
    assert checked == len(presets) * len(sc["steps"])


@pytest.mark.skipif(not HAVE_NODE, reason="node not installed")
def test_browser_interpolation_is_continuous_and_lands_on_keyframes(tmp_path):
    sc = M.payload(scene(), equation_svg=False)
    path = tmp_path / "scene.json"
    path.write_text(json.dumps(sc), encoding="utf-8")
    out = _node(NODE_PRELUDE + "const r=[];for(let i=0;i<=700;i++){const p=MM.paramsAtPosition(sc,i/100);"
                "const s=MM.evaluate(sc,p);r.push([s.pi[0],s.pi[1],s.n,s.b,s.J]);}console.log(JSON.stringify(r));",
                str(TEMPLATES / "policy_gradient_math.js"), str(TEMPLATES / "mastery_motion.js"), str(path))
    seq = np.array(json.loads(out))
    states = M.states(sc)
    for i in range(len(sc["steps"])):
        assert np.allclose(seq[i * 100, [0, 1, 4]], [states[i]["pi"][0], states[i]["pi"][1], states[i]["J"]], atol=1e-12)
    jumps = np.abs(np.diff(seq[:, [0, 1, 3, 4]], axis=0)).max(axis=0)
    assert jumps.max() < 0.08  # pi, b and J move continuously (no teleporting between keyframes)
    n = seq[:, 2]
    assert (np.diff(n[200:400]) >= 0).all() and n[300] == 12 and n[400] == 200  # the cloud grows monotonically


# ------------------------------------------------------------------ the Mastery app, end to end in a real browser

try:
    from playwright.sync_api import sync_playwright
    HAVE_BROWSER = True
except ImportError:  # pragma: no cover
    HAVE_BROWSER = False

SCENE = ".mm-scene.mm-ready"


def _wait_step(pg, step):
    pg.wait_for_function(f"() => document.querySelector('{SCENE}').dataset.step === '{step}' && "
                         f"Number(document.querySelector('{SCENE}').dataset.pos) % 1 === 0")


def _events(pg):
    return json.loads(pg.evaluate("localStorage.getItem('em-motion-v1')"))["scenes"][RL]["events"]


@pytest.mark.skipif(not HAVE_BROWSER, reason="playwright not installed")
def test_mastery_app_demo_scene_end_to_end(tmp_path):
    from exam_mastery.mastery import build, validate_state
    from exam_mastery.mastery.server import start_in_thread
    home = tmp_path / "Mastery"
    build(home, only="-no-unit-", log=lambda *_: None)  # shell + motion demos only (no unit build needed here)
    lib = json.loads((home / "library.json").read_text(encoding="utf-8"))
    assert lib["units"] == [] and sorted(d["id"] for d in lib["motion_demos"]) == [PLANE, RL]
    server, base = start_in_thread(home)
    errors, external = [], []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context(viewport={"width": 1280, "height": 1000})
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.on("request", lambda r: external.append(r.url) if not r.url.startswith((base, "data:", "blob:")) else None)
            pg.goto(base)
            pg.wait_for_selector('#app[data-ready="1"]')
            pg.click(f'#motion-demos a[data-motion="{RL}"]')
            pg.wait_for_selector(SCENE)
            assert pg.get_attribute(SCENE, "data-error") is None
            assert pg.is_hidden(".mm-fallback") and pg.locator(".mm-term").count() == 5
            assert pg.get_attribute(SCENE, "data-step") == "policy-point"
            assert pg.is_visible("[data-action=play]") and pg.is_disabled("[data-action=back]")

            # step forward by keyboard; the next step is a reveal, so the timeline is locked behind a prediction
            pg.focus(SCENE)
            pg.keyboard.press("ArrowRight")
            _wait_step(pg, "value-lines")
            assert pg.is_disabled("[data-action=next]") and pg.inner_text("[data-action=next]") == "Erst vorhersagen"
            pg.eval_on_selector(".mm-scrub", "e => { e.value = '6'; e.dispatchEvent(new Event('input')); }")
            assert float(pg.get_attribute(SCENE, "data-pos")) == 1.0  # scrubbing past the checkpoint is refused
            assert pg.is_disabled('[data-step="exact-gradient"] button')
            assert pg.is_disabled("[data-action=commit]") and pg.is_disabled("[data-action=reveal]")
            pg.click('[data-question="grad-direction"] [data-answer="SE"]')  # a wrong prediction is recorded honestly
            pg.click("[data-action=commit]")
            assert pg.is_enabled("[data-action=reveal]")
            pg.click("[data-action=reveal]")
            _wait_step(pg, "exact-gradient")
            fb = pg.locator('[data-feedback="exact-gradient"] [data-correct]')
            assert fb.get_attribute("data-correct") == "false" and "↖" in fb.inner_text()

            # scrub into the sampling transition: the cloud grows continuously and the coupled term lights up
            pg.eval_on_selector(".mm-scrub", "e => { e.value = '3.5'; e.dispatchEvent(new Event('input')); }")
            st = json.loads(pg.get_attribute(SCENE, "data-state"))
            assert float(pg.get_attribute(SCENE, "data-pos")) == 3.5 and 12 < st["n"] < 200
            assert pg.locator('.mm-term.mm-term-on[data-term="ret"]').count() == 1
            assert pg.locator('[data-o="cloud"] circle').count() == st["n"]
            pg.focus('.mm-term[data-term="grad"]')
            assert pg.locator('g.mm-hl[data-o="grad-arrow"]').count() == 1
            pg.eval_on_selector(".mm-scrub", "e => { e.value = '4'; e.dispatchEvent(new Event('input')); }")
            _wait_step(pg, "cloud-grows")
            pg.click('[data-question="baseline-mean"] [data-answer="same"]')
            pg.click('[data-question="baseline-spread"] [data-answer="smaller"]')
            pg.click("[data-action=commit]")
            pg.click("[data-action=reveal]")
            _wait_step(pg, "baseline-on")
            assert [x.get_attribute("data-correct") for x in pg.locator('[data-feedback="baseline-on"] [data-correct]').all()] == ["true", "true"]
            assert pg.is_enabled("[data-action=next]")

            # mission with one slider: the computed goal decides, the attempt is recorded
            ids = [s["id"] for s in scene()["steps"]]
            b_opt = softmax_simplex_pg({**M.params_at(scene(), ids.index("baseline-on")), "lam": 0.0})["b_opt"]
            pg.eval_on_selector('[data-param="b0"]', "(e, v) => { e.value = String(v); e.dispatchEvent(new Event('input')); }",
                                round(b_opt / 0.05) * 0.05)
            pg.click("[data-action=mission-check]")
            assert pg.get_attribute(".mm-mission-status", "data-met") == "true"
            ev = _events(pg)
            assert [e["type"] for e in ev] == ["predict", "reveal", "predict", "predict", "reveal", "task_attempt"]
            assert [e["correct"] for e in ev if e["type"] == "predict"] == [False, True, True]

            # reload: reveals persist, so the whole timeline is open; long jumps via the step ticks work
            pg.reload()
            pg.wait_for_selector(SCENE)
            assert pg.is_enabled('[data-step="many-steps"] button')
            pg.click('[data-step="many-steps"] button')
            _wait_step(pg, "many-steps")
            st = json.loads(pg.get_attribute(SCENE, "data-state"))
            assert math.isclose(st["J"], M.states(scene())[-1]["J"], rel_tol=1e-12)

            # home: honest progress (predictions are not evidence) and the server backup accepts em-motion-v1
            pg.goto(base + "#lernstand")
            pg.wait_for_selector('#app[data-ready="1"]')
            row = pg.locator(f'#motion-progress tr[data-motion-scene="{RL}"]')
            assert row.get_attribute("data-predictions") == "3"
            assert "kein Nachweis von Können" in pg.inner_text("#motion-progress")
            pg.wait_for_function("() => document.getElementById('backup-status').dataset.saved")
            latest = json.loads((home / "state" / "latest.json").read_text(encoding="utf-8"))
            validate_state({k: latest[k] for k in ("schema", "saved_at", "origin", "storage")})
            assert len(latest["storage"]["em-motion-v1"]["scenes"][RL]["events"]) == 6

            # reduced motion: step-only (no play button), the next keyframe is reached without animation frames
            rctx = browser.new_context(reduced_motion="reduce")
            rp = rctx.new_page()
            rp.on("pageerror", lambda e: errors.append(str(e)))
            rp.goto(base + f"motion/{RL}.html")
            rp.wait_for_selector(SCENE)
            assert rp.get_attribute(SCENE, "data-reduced-motion") == "1" and rp.is_hidden("[data-action=play]")
            rp.evaluate("() => { window.requestAnimationFrame = () => { throw new Error('animation in reduced motion'); }; }")
            rp.click("[data-action=next]")
            assert rp.get_attribute(SCENE, "data-step") == "value-lines" and rp.get_attribute(SCENE, "data-pos") == "1.000"
            assert rp.locator("svg.mm-stage title").text_content().startswith(scene()["title"])  # aria text per step
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    assert not errors, errors
    assert not external, external
