"""V8: an experience unit that references a Mastery Motion scene gets its textbook figures and its Anki card images
from that scene's keyframes (same palette, element ids and scale as the interactive scene). Synthetic unit of the same
shape as a plane-transformation chapter; no course material."""
import copy
import json
from pathlib import Path

import pytest

from exam_mastery import figures_svg
from exam_mastery import motion as M
from exam_mastery.learning.experience import validate
from exam_mastery.learning.experience_graphics import html_frames, specifications
from exam_mastery.motion.plane import unit_scene

ROOT = Path(__file__).resolve().parents[1]
SHEAR = {"matrix": [[2, -1], [1, 1]], "vector": [1, 2]}


def plane_unit():
    unit = copy.deepcopy(json.loads((ROOT / "fixtures/experience_attention_reference.json").read_text(encoding="utf-8")))
    inter = unit["interactions"][0]
    inter.update(model_ref="plane_linear_map", prediction_prompt="Wohin landet v?", transfer_prompt="Transfer.",
                 variants=[{"label": "Scherung, t = 0", "parameters": {**SHEAR, "t": 0}},
                           {"label": "Scherung, t = 1", "parameters": {**SHEAR, "t": 1}},
                           {"label": "Spiegelung", "parameters": {"matrix": [[0, 1], [1, 0]], "vector": [1, 2], "t": 1}}])
    graphic = unit["graphics"][0]
    graphic.update(model_ref="plane_linear_map", keyframes=[0, "image"])
    unit["cards"][0]["figure"] = graphic["id"] + "-state-image"          # a card shows the scene's anki keyframe
    check = validate(unit)
    assert check["valid"], check["errors"]
    return unit


def test_graphic_names_a_scene_keyframe_and_gets_exactly_that_keyframe():
    unit = plane_unit()
    frames = specifications(unit)
    motion = [(g, i, s) for g, i, s in frames if s["type"] == "mastery_motion"]
    assert len(frames) == 2 and len(motion) == 1 and motion[0][1] == "image"
    scene = unit_scene({**unit["interactions"][0]})
    svg = figures_svg.render(motion[0][2])
    assert svg == M.keyframe_svg(scene, "image", caption=False, preset="p1")       # the scene's own keyframe
    assert f'id="mm-{scene["id"]}-image-p1-t"' in svg                              # same element ids as the export
    for token in ("basis1", "basis2", "vec", "area"):
        assert M.PALETTE[token]["color"] in svg                                    # same palette
    state = M.evaluate(scene, M.params_at(scene, 4, "p1"))
    arrows = [p for p in M.display(scene, state, M.panels_for(scene, "p1")) if p["k"] == "arrow"]
    tip = next(p for p in arrows if p["o"] == "mv")                                # same scale: the tip of Av
    assert f'M{M._n(tip["x2"])} {M._n(tip["y2"])}L' in svg
    assert "Mv = (0; 3)" in svg and "det M = 2·1 − (−1)·1 = 3" in svg               # computed readouts
    assert "<script" not in svg and "http" not in svg.replace("http://www.w3.org/2000/svg", "")
    html = html_frames(unit, unit["graphics"][0]["teaching_id"])
    assert "Mastery Motion, Schritt „Das Bild unter A (t = 1)“" in html and "Zustand 1" in html
    bad = copy.deepcopy(unit)
    bad["graphics"][0]["keyframes"] = [0, "no-such-step"]
    bad["cards"][0]["figure"] = bad["graphics"][0]["id"] + "-state-0"
    assert any("unknown Mastery Motion keyframe" in e for e in validate(bad)["errors"])


def test_rl_unit_can_name_keyframes_of_the_public_scene():
    unit = plane_unit()
    graphic, inter = unit["graphics"][0], unit["interactions"][0]
    inter.update(model_ref="softmax_policy_gradient", variants=[{"label": "Bandit", "parameters": {
        "theta": [0.6, -0.2, 0.3], "rewards": [1.0, 2.0, 0.2], "noise_sd": 0.5, "batch": 16, "seed": 2}}])
    graphic.update(model_ref="softmax_policy_gradient", keyframes=[0, "baseline-on"])
    unit["cards"][0]["figure"] = graphic["id"] + "-state-baseline-on"
    assert validate(unit)["valid"], validate(unit)["errors"]
    spec = [s for _, _, s in specifications(unit) if s["type"] == "mastery_motion"][0]
    assert figures_svg.render(spec) == M.keyframe_svg(M.load("rl-softmax-simplex"), "baseline-on", caption=False)


def test_textbook_pdf_contains_the_motion_keyframe(tmp_path):
    pytest.importorskip("playwright.sync_api")
    fitz = pytest.importorskip("pymupdf")
    from exam_mastery.learning import experience_books as books
    unit = plane_unit()
    report = books.publish(unit, tmp_path)
    assert report["status"] == "CREATED_OR_UPDATED"
    with fitz.open(tmp_path / "Lehrbuch.pdf") as pdf:
        text = "\n".join(page.get_text() for page in pdf)
    assert "Werte aus dem Modell" in text and "Rang M = 2" in text and "Me" in text   # the keyframe, typeset as text
    assert books.publish(unit, tmp_path)["status"] == "UNCHANGED"


def test_anki_card_image_is_the_keyframe_and_an_unchanged_rebuild_restamps_nothing(tmp_path):
    pytest.importorskip("anki")
    from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
    from exam_mastery.learning import experience_anki as bridge
    unit = plane_unit()
    first = bridge.publish(unit, tmp_path / "out")
    assert first["status"] == "CREATED_OR_UPDATED"
    pkg = tmp_path / "out" / "Anki.apkg"
    stamp = (pkg.stat().st_mtime_ns, pkg.read_bytes())
    second = bridge.publish(copy.deepcopy(unit), tmp_path / "out")                  # CD-8: same unit, nothing restamped
    assert second["status"] == "UNCHANGED" and (pkg.stat().st_mtime_ns, pkg.read_bytes()) == stamp
    spec = [s for _, _, s in specifications(unit) if s["type"] == "mastery_motion"][0]
    collection = Collection(str(tmp_path / "readback.anki2"))                       # a throwaway collection only
    try:
        collection.import_anki_package(ImportAnkiPackageRequest(package_path=str(pkg), options=ImportAnkiPackageOptions()))
        media = Path(collection.media.dir())
        svgs = {p.name: p.read_text(encoding="utf-8") for p in media.glob("*.svg")}
        assert list(svgs.values()) == [figures_svg.render(spec)]
        name = next(iter(svgs))
        assert any(name in " ".join(collection.get_note(n).fields) for n in collection.find_notes(""))
    finally:
        collection.close()
