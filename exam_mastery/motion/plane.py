"""The plane-transformation scene of Mastery Motion (one model, one scene grammar for app, book and card).

`build_scene` turns a list of presets (matrix A, test vector v) into a mastery-motion-v1 scene: the straight morph
M(t) = (1 - t) I + t A in five linear keyframes, a prediction of A v and sign(det A) before the morph, kernel and image
lines whenever M(t) is singular (the scrubber snaps onto those times), draggable column tips after the reveal and number
inputs for own matrices. The public demo scene (scenes/plane-linear-map.json) is this builder's output for DEMO_PRESETS;
experience units with model_ref plane_linear_map get the same scene with their own variants as presets, and their book
figures and card images are keyframes of it (V8). No course content lives here.
"""
from __future__ import annotations

import hashlib
import json
import re

from . import SCHEMA, panels_for, state_svg, validate
from .models import linear_map_2d, plane_extent, plane_params

TITLE = "Lineare Abbildung als stetige Verformung der Ebene"
CLAIM = ("Die Spalten von A sind die Bilder von e₁ und e₂; Av kombiniert sie mit den Koordinaten von v. det A ist die "
         "vorzeichenbehaftete Fläche des Bildquadrats; wo det M(t) = 0 wird, fällt die Ebene auf eine Gerade (Kern ≠ {0}).")
DEMO_PRESETS = [
    {"id": "allgemein", "label": "Allgemein", "matrix": [[2, -1], [1, 1]], "vector": [1, 2]},
    {"id": "scherung", "label": "Scherung", "matrix": [[1, 1], [0, 1]], "vector": [1, 2]},
    {"id": "drehung", "label": "Drehung um 90°", "matrix": [[0, -1], [1, 0]], "vector": [2, 1]},
    {"id": "spiegelung", "label": "Spiegelung", "matrix": [[0, 1], [1, 0]], "vector": [1, 2]},
    {"id": "rang-1", "label": "Rang 1", "matrix": [[1, 2], [2, 4]], "vector": [2, -1]},
    {"id": "null", "label": "Nullabbildung", "matrix": [[0, 0], [0, 0]], "vector": [1, 1]},
]
STEPS_T = (("identity", 0.0), ("quarter", 0.25), ("half", 0.5), ("three-quarters", 0.75), ("image", 1.0))
FOCUS = ["grid", "square", "kernel", "image", "col1", "col2", "mv", "v0"]


def _preset(item):
    p = plane_params({"matrix": item["matrix"], "vector": item["vector"]})
    r = plane_extent(linear_map_2d({**p, "t": 1.0}))
    return {"id": item["id"], "label": item["label"], "set": {"A": p["A"], "v": p["v"]},
            "domain": {"plane": [-r, r, -r, r]}}


def _read(oid, y, text, token, meaning):
    return {"id": oid, "type": "label", "panel": "read", "x": 0, "y": y, "text": text, "token": token, "meaning": meaning}


def build_scene(presets, scene_id="plane-linear-map", title=TITLE, claim=CLAIM, prompt=None, public=False):
    """A validated plane scene; presets: [{id, label, matrix, vector}] (first = start)."""
    if not presets or len(presets) > 8:
        raise ValueError("plane scene: 1..8 presets required")
    pr = [_preset(x) for x in presets]
    first = pr[0]["set"]
    steps = []
    for k, (sid, t) in enumerate(STEPS_T):
        st = {"id": sid, "focus": FOCUS}
        if k:
            st["set"] = {"t": t}
            st["transition"] = {"kind": "morph", "animate": ["t"], "ms": 900, "ease": "linear"}
        steps.append(st)
    steps[0].update(title="Vor der Abbildung (t = 0)",
                    caption="Gitter, Basisvektoren e₁ und e₂, Einheitsquadrat und Testvektor v = {v_text}. Gleich "
                            "verformt M(t) = (1 − t)·I + t·A die Ebene stetig von der Identität zu A.",
                    aria="Ein unverformtes Quadratgitter. Die Spalten Me₁ = {e1_text} und Me₂ = {e2_text} sind die "
                         "Basisvektoren, das Einheitsquadrat hat Fläche 1, der Testvektor zeigt nach {v_text}.")
    steps[1].update(title="Ein Viertel des Weges (t = 0,25)",
                    caption="Die Spalten wandern: Me₁ = {e1_text}, Me₂ = {e2_text}. det M = {det_formula}. "
                            "{orientation_text}.",
                    aria="Das Gitter ist leicht verformt; das Bild des Einheitsquadrats ist ein Parallelogramm mit "
                         "Fläche {det_formula}. {orientation_text}.",
                    checkpoint={"predict": [
                        {"id": "av", "type": "point", "short": "Av",
                         "prompt": prompt or "Vorhersage: Wohin landet v unter A? Av ≈",
                         "correct": {"rule": "point", "of": "Av", "tol": 0.25}},
                        {"id": "det-sign", "type": "sign", "short": "det A", "prompt": "Und das Vorzeichen von det A?",
                         "correct": {"rule": "sign", "of": "det_A", "tol": 1e-9}}],
                        "feedback_step": "image",
                        "explain": "Av = {Av_formula}: Av kombiniert die Spalten von A mit den Koordinaten von v. "
                                   "det A = {det_A_text}. {det_A_note}"})
    steps[2].update(title="Halber Weg (t = 0,5)",
                    caption="M(0,5) ist der Mittelwert von I und A. det M = {det_formula}. {rank_text}: "
                            "{kernel_text}, {image_text}.",
                    aria="Das Gitter auf halbem Weg; {orientation_text}. {rank_text}, {kernel_text}, {image_text}.")
    steps[3].update(title="Drei Viertel (t = 0,75)",
                    caption="det M = {det_formula}. {orientation_text}. Wo det M(t) unterwegs 0 wird, rastet die "
                            "Zeitachse ein (rote Marken): Dort zeigen Kern und Bild als Geraden, was verloren geht.",
                    aria="Das Gitter ist fast bei A angekommen. {orientation_text}.")
    steps[4].update(title="Das Bild unter A (t = 1)",
                    caption="Jetzt ist M = A: Me₁ = {e1_text} und Me₂ = {e2_text} sind die Spalten von A, "
                            "Av = {Mv_formula}. det A = {det_A_text}; {rank_text}, {kernel_text}, {image_text}. "
                            "Ziehen Sie die Spitzen der Spalten, um A zu verändern.",
                    aria="Das Gitter unter A. Die Spalten zeigen nach {e1_text} und {e2_text}, das Bild von v liegt "
                         "bei {Mv_text}. det A = {det_A_text}. {rank_text}, {kernel_text}, {image_text}.")
    objects = [
        {"id": "ghost", "type": "grid", "panel": "plane", "matrix": "I", "range": [-12, 12], "token": "muted",
         "meaning": "Das ursprüngliche Gitter (Bezug, bleibt stehen)."},
        {"id": "grid", "type": "grid", "panel": "plane", "matrix": "M", "range": [-12, 12], "token": "ink",
         "meaning": "Das Bild des Gitters unter M(t): Geraden bleiben Geraden, Parallelen bleiben parallel."},
        {"id": "square", "type": "polygon", "panel": "plane", "points": "square", "orientation": "orientation",
         "token": "area", "meaning": "Bild des Einheitsquadrats; Fläche = |det M|, schraffiert bei umgekehrter Orientierung."},
        {"id": "kernel", "type": "lines", "panel": "plane", "of": "kernel_line", "token": "kernel",
         "meaning": "Kern von M(t) (gestrichelt): alle Vektoren, die auf 0 abgebildet werden; nur bei Rang 1 eine Gerade."},
        {"id": "image", "type": "lines", "panel": "plane", "of": "image_line", "token": "image",
         "meaning": "Bild von M(t) bei Rang 1: die Gerade, auf die die ganze Ebene fällt."},
        {"id": "v0", "type": "point", "panel": "plane", "at": "v", "token": "vec", "size": 4.5, "label": "v",
         "meaning": "Der Testvektor v vor der Abbildung."},
        {"id": "col1", "type": "vector", "panel": "plane", "to": "e1", "token": "basis1", "label": "Me₁",
         "meaning": "Erste Spalte von M(t) = Bild von e₁."},
        {"id": "col2", "type": "vector", "panel": "plane", "to": "e2", "token": "basis2", "label": "Me₂",
         "meaning": "Zweite Spalte von M(t) = Bild von e₂."},
        {"id": "mv", "type": "vector", "panel": "plane", "to": "Mv", "token": "vec", "label": "Mv",
         "meaning": "Bild des Testvektors: Mv = v₁·Me₁ + v₂·Me₂."},
        _read("read-t", 14, "t = {t_text}   ·   M(t) = (1 − t)·I + t·A", "ink", "Zeit des Weges von I nach A."),
        _read("read-e1", 46, "Me₁ = {e1_text}", "basis1", "Erste Spalte."),
        _read("read-e2", 72, "Me₂ = {e2_text}", "basis2", "Zweite Spalte."),
        _read("read-mv", 104, "Mv = {Mv_text}", "vec", "Bild des Testvektors."),
        _read("read-mvf", 128, "= {Mv_formula}", "vec", "Spaltenkombination."),
        _read("read-det", 160, "det M = {det_formula}", "area", "Determinante als Formel."),
        _read("read-or", 184, "{orientation_text}", "area", "Orientierung."),
        _read("read-rank", 216, "{rank_text}", "ink", "Rang."),
        _read("read-ker", 240, "{kernel_text}", "kernel", "Kern."),
        _read("read-img", 264, "{image_text}", "image", "Bild."),
        _read("read-dim", 288, "{dim_text}", "ink", "Dimensionsformel."),
    ]
    scene = {
        "schema": SCHEMA, "id": scene_id, "lang": "de", "public": bool(public), "title": title, "claim": claim,
        "model": "linear_map_2d",
        "params": {"A": {"value": first["A"], "min": -4, "max": 4, "label": "Matrix A"},
                   "v": {"value": first["v"], "min": -3, "max": 3, "label": "Testvektor v"},
                   "t": {"value": 0.0, "min": 0, "max": 1}},
        "view": {"width": 780, "height": 470, "panels": [
            {"id": "plane", "title": "Die Ebene unter M(t)", "x": 16, "y": 30, "w": 430, "h": 430,
             "domain": pr[0]["domain"]["plane"], "clip": True},
            {"id": "read", "title": "Werte aus dem Modell", "x": 470, "y": 44, "w": 300, "h": 300, "domain": [0, 1, 0, 1]}]},
        "objects": objects,
        "terms": {"mv": {"name": "Bild des Testvektors Mv", "token": "vec", "objects": ["mv", "read-mv", "read-mvf"]},
                  "col1": {"name": "erste Spalte Me₁", "token": "basis1", "objects": ["col1", "read-e1"]},
                  "col2": {"name": "zweite Spalte Me₂", "token": "basis2", "objects": ["col2", "read-e2"]},
                  "det": {"name": "Determinante = Fläche mit Vorzeichen", "token": "area",
                          "objects": ["square", "read-det", "read-or"]},
                  "ker": {"name": "Kern (bei det = 0 eine Gerade)", "token": "kernel", "objects": ["kernel", "read-ker"]}},
        "equation": {"label": "Spaltenbild und Determinante", "segments": [
            {"tex": "M(t)\\,v", "text": "M(t)v", "term": "mv"}, {"tex": "=", "text": " = "},
            {"tex": "v_1", "text": "v₁"}, {"tex": "M e_1", "text": "Me₁", "term": "col1"}, {"tex": "+", "text": " + "},
            {"tex": "v_2", "text": "v₂"}, {"tex": "M e_2", "text": "Me₂", "term": "col2"}, {"tex": "\\qquad", "text": "   "},
            {"tex": "\\det M(t)", "text": "det M(t)", "term": "det"}, {"tex": "= 0 \\iff", "text": " = 0 ⟺ "},
            {"tex": "\\ker M(t) \\neq \\{0\\}", "text": "Kern M(t) ≠ {0}", "term": "ker"}]},
        "steps": steps,
        "missions": [{"id": "flatten", "from_step": "image",
                      "prompt": "Auftrag: Machen Sie A singulär (det A = 0), indem Sie nur den Eintrag a₁₂ verändern.",
                      "hint": "det A = a₁₁a₂₂ − a₁₂a₂₁ ist in a₁₂ linear. Bei det A = 0 sind die Spalten parallel.",
                      "feedback": "det A = {det_A_text}; {rank_text}, {kernel_text}.",
                      "sliders": [{"param": "A", "index": 1, "label": "a₁₂", "step": 0.25}],
                      "goal": {"of": "det_A", "op": "abs<=", "value": 0.05}}],
        "presets": pr,
        "edit": [{"param": "A", "index": i, "label": lab, "step": 0.5} for i, lab in enumerate(("a₁₁", "a₁₂", "a₂₁", "a₂₂"))]
        + [{"param": "v", "index": i, "label": lab, "step": 0.5} for i, lab in enumerate(("v₁", "v₂"))],
        "drag": [{"object": "col1", "param": "A", "indices": [0, 2], "step": 0.25},
                 {"object": "col2", "param": "A", "indices": [1, 3], "step": 0.25}],
        "snap": {"param": "t", "to": "singular_times", "within": 0.015},
        "keyframes": {"textbook": ["identity", "half", "image"], "anki": ["image"]},
    }
    validate(scene)
    return scene


def demo_scene():
    return build_scene(DEMO_PRESETS, public=True)


def unit_presets(variants):
    """Experience-unit variants -> presets: one per distinct (matrix, vector); labels as before ('Scherung, t = 1')."""
    out, seen = [], set()
    for v in variants:
        p = v["parameters"]
        key = json.dumps({"matrix": p["matrix"], "vector": p["vector"]}, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append({"id": f"p{len(out) + 1}", "label": str(v["label"]).split(",")[0].strip() or f"Beispiel {len(out) + 1}",
                    "matrix": p["matrix"], "vector": p["vector"]})
    return out[:8]


def unit_scene(spec):
    """Scene of a compiled explorable_model interaction with model_ref plane_linear_map (schema unchanged)."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(spec["id"]).lower()).strip("-")[:40] or "plane"
    return build_scene(unit_presets(spec["variants"]), scene_id="plane-" + slug,
                       prompt=spec.get("prediction_prompt") or None)


def figure_svg(parameters, title=None, alt=None, theme="light"):
    """Book/card figure of one parameter set {matrix, vector[, t]}: a keyframe of the same scene (same palette, object
    ids and scale as the explorable), drawn with the readouts. Deterministic; no script, no external reference."""
    p = plane_params(parameters)
    item = {"id": "fig", "label": title or "Figur", "matrix": parameters["matrix"], "vector": parameters["vector"]}
    scene = build_scene([item])
    state = linear_map_2d(p)
    near = min(range(len(STEPS_T)), key=lambda k: abs(STEPS_T[k][1] - p["t"]))
    step = dict(scene["steps"][near], title=title or scene["steps"][near]["title"])
    if alt:
        step["aria"] = alt + " " + step["aria"]
    uid = "pm" + hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:10] + ("d" if theme == "dark" else "")
    return state_svg(scene, state, step, uid, theme, panels_for(scene, "fig"))
