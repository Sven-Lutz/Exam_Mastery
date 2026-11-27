"""Mastery Motion: generic, offline scene system that shows mathematics as continuous motion (standard §4, V1-V10).

A scene (schema ``mastery-motion-v1``, JSON) declares a deterministic model, its parameters, visual objects bound to
model quantities, an equation whose terms are bound to objects, a timeline of steps with transitions, prediction
checkpoints and slider missions. This module is the Python reference: it validates scenes, evaluates the state of
every step, compiles the same display list as the browser runtime (templates/mastery_motion.js) and exports
keyframes as standalone SVG for textbook figures and Anki cards (V8). Tests compare both runtimes keyframe by keyframe.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from html import escape
from pathlib import Path

from .models import MODELS

SCHEMA = "mastery-motion-v1"
SCENES = Path(__file__).resolve().parent / "scenes"
ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
REF = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TEMPLATE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?:\.(\d))?(?::(\d))?\}")

# Mastery's own palette (not derived from any other product). Each token carries a second, non-colour channel:
# dash pattern for strokes and a marker shape for points, so colour is never the only carrier (V9). Light colours keep
# >= 4.5:1 contrast on white; "dark" is the same hue lifted for the dark stage (#12161f). Context tokens (ink, muted)
# stay neutral so that the saturated tokens carry the objects in focus.
PALETTE = {
    "ink":      {"color": "#1b1f2a", "dark": "#e6e8ee", "dash": "", "shape": "circle", "name": "Bezug"},
    "muted":    {"color": "#8b91a0", "dark": "#5f6678", "dash": "", "shape": "circle", "name": "Hilfslinie"},
    "policy":   {"color": "#007d71", "dark": "#34d1bf", "dash": "", "shape": "circle", "name": "Policy"},
    "grad":     {"color": "#d23c14", "dark": "#ff7b54", "dash": "", "shape": "triangle", "name": "Gradient"},
    "sample":   {"color": "#5b45d6", "dark": "#a597ff", "dash": "", "shape": "ring", "name": "Stichprobe"},
    "mean":     {"color": "#5b45d6", "dark": "#a597ff", "dash": "", "shape": "square", "name": "Mittelwert"},
    "baseline": {"color": "#9a6100", "dark": "#f2b544", "dash": "6 4", "shape": "diamond", "name": "Baseline"},
    "value":    {"color": "#a3358f", "dark": "#ea8bd8", "dash": "2 4", "shape": "circle", "name": "Wert J"},
    "step":     {"color": "#007d71", "dark": "#34d1bf", "dash": "7 4", "shape": "circle", "name": "Schritt"},
    "basis1":   {"color": "#d23c14", "dark": "#ff7b54", "dash": "", "shape": "triangle", "name": "erste Spalte"},
    "basis2":   {"color": "#1f64d1", "dark": "#6ea8ff", "dash": "", "shape": "triangle", "name": "zweite Spalte"},
    "area":     {"color": "#9a6100", "dark": "#f2b544", "dash": "", "shape": "square", "name": "Fläche"},
    "score":    {"color": "#1f64d1", "dark": "#6ea8ff", "dash": "5 3", "shape": "circle", "name": "Score-Richtung"},
    "vec":      {"color": "#007d71", "dark": "#34d1bf", "dash": "", "shape": "circle", "name": "Testvektor"},
    "kernel":   {"color": "#a3358f", "dark": "#ea8bd8", "dash": "8 5", "shape": "diamond", "name": "Kern"},
    "image":    {"color": "#237a34", "dark": "#69d37f", "dash": "", "shape": "square", "name": "Bild"},
}
STAGE = {"light": {"bg": "#ffffff", "ink": "#1b1f2a"}, "dark": {"bg": "#12161f", "ink": "#e6e8ee"}}
FONT = 14          # label size in view units (keyframes and runtime)
OBJECT_TYPES = {"simplex", "point", "points", "vector", "circle", "curve", "lines", "polygon", "grid", "bars",
                "graph", "label"}
TRANSITIONS = {"none", "interpolate", "morph", "iterate", "sample", "highlight"}
ANSWER_TYPES = {"direction", "sign", "choice", "number", "point"}
EASINGS = {"smooth", "linear"}
DIRECTIONS = {"E": 0, "NE": 45, "N": 90, "NW": 135, "W": 180, "SW": 225, "S": 270, "SE": 315}
SQ3 = math.sqrt(3.0) / 2.0
TRI = ((-SQ3, -0.5), (0.0, 1.0), (SQ3, -0.5))  # unit directions of the three simplex vertices a1, a2, a3


class SceneError(ValueError):
    pass


def _fail(msg):
    raise SceneError("motion scene: " + msg)


# ------------------------------------------------------------------ parameters and evaluation

def preset_of(scene, preset):
    if preset is None:
        return None
    for item in scene.get("presets", []):
        if item["id"] == preset:
            return item
    _fail("unknown preset " + str(preset))


def params_at(scene, index, preset=None):
    """Parameter set of step `index`: defaults, the preset's values, then every step's `set` up to `index`."""
    params = {k: copy.deepcopy(v["value"]) for k, v in scene["params"].items()}
    if preset is not None:
        params.update(copy.deepcopy(preset_of(scene, preset)["set"]))
    for step in scene["steps"][: index + 1]:
        params.update(copy.deepcopy(step.get("set", {})))
    return params


def evaluate(scene, params):
    return MODELS[scene["model"]](params)


def states(scene, preset=None):
    return [evaluate(scene, params_at(scene, i, preset)) for i in range(len(scene["steps"]))]


def panels_for(scene, preset=None):
    """Panels with a preset's domain overrides (one scale per preset, shared by all its keyframes)."""
    over = (preset_of(scene, preset) or {}).get("domain", {}) if preset is not None else {}
    return [{**p, "domain": over.get(p["id"], p["domain"])} for p in scene["view"]["panels"]]


def _get(state, ref):
    if isinstance(ref, (list, int, float)):
        return ref
    if ref not in state:
        _fail(f"unknown state quantity {ref!r}")
    return state[ref]


def fmt(x, d):
    """Fixed decimals, decimal comma, typographic minus; identical in mastery_motion.js."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return "–"
    s = f"{x:.{d}f}"
    if float(s) == 0:
        s = s.lstrip("-")
    return s.replace("-", "−").replace(".", ",")


def text_of(template, state):
    def sub(m):
        value = _get(state, m.group(1))
        if m.group(2) is not None:
            value = value[int(m.group(2))]
        if isinstance(value, str):  # model-computed display strings (e.g. "det M = 2·1 − (−1)·1 = 3")
            return value
        if m.group(3) is None and not isinstance(value, bool) and float(value).is_integer() and abs(value) < 1e15:
            return str(int(value))
        return fmt(value, int(m.group(3) or 2))
    return TEMPLATE.sub(sub, template)


# ------------------------------------------------------------------ geometry and display list

def _frame(panel):
    x0, x1, y0, y1 = panel["domain"]
    s = min(panel["w"] / (x1 - x0), panel["h"] / (y1 - y0))
    ox = panel["x"] + (panel["w"] - s * (x1 - x0)) / 2 - s * x0
    oy = panel["y"] + (panel["h"] - s * (y1 - y0)) / 2 + s * y1
    return s, ox, oy


def _world(p, coords):
    if coords == "tri3":
        return [sum(p[a] * TRI[a][0] for a in range(3)), sum(p[a] * TRI[a][1] for a in range(3))]
    return [p[0], p[1]]


def _screen(panel, p, coords="xy"):
    s, ox, oy = _frame(panel)
    w = _world(p, coords)
    return [ox + s * w[0], oy - s * w[1]]


def _box(x, y, s, a):
    w = 0.56 * FONT * len(s)
    x0 = x if a == "start" else (x - w / 2 if a == "middle" else x - w)
    return [x0, y - 0.8 * FONT, x0 + w, y + 0.25 * FONT]


def _free(box, boxes):
    return all(box[2] <= b[0] or box[0] >= b[2] or box[3] <= b[1] or box[1] >= b[3] for b in boxes)


LABEL_SPOTS = {"point": ((10, -10, "start"), (10, 22, "start"), (-10, -10, "end"), (-10, 22, "end")),
               "vector": ((8, -6, "start"), (8, 18, "start"), (-8, -6, "end"), (-8, 18, "end"))}


def display(scene, state, panels=None):
    """Display list: drawing primitives in view coordinates, one group per object (same in JS). Object labels take the
    first of four spots around their anchor that does not collide with text or marks already placed in the panel."""
    panels = {p["id"]: p for p in (panels or scene["view"]["panels"])}
    out, boxes = [], {}
    for obj in scene["objects"]:
        panel = panels[obj["panel"]]
        tok, coords, oid = obj.get("token", "ink"), obj.get("coords", "xy"), obj["id"]
        sc = obj.get("scale", 1.0)
        taken = boxes.setdefault(obj["panel"], [])

        def P(p):
            return _screen(panel, p, coords)

        def add(kind, **geo):
            out.append({"o": oid, "k": kind, "t": tok, **geo})
            if kind == "text":
                taken.append(_box(geo["x"], geo["y"], geo["s"], geo["a"]))
            elif kind == "mark":
                taken.append([geo["x"] - geo["r"], geo["y"] - geo["r"], geo["x"] + geo["r"], geo["y"] + geo["r"]])

        def label(x, y, text, kind):
            spots = LABEL_SPOTS[kind]
            for dx, dy, a in spots:
                if _free(_box(x + dx, y + dy, text, a), taken):
                    break
            else:
                dx, dy, a = spots[0]
            add("text", x=x + dx, y=y + dy, s=text, a=a)
        typ = obj["type"]
        if typ == "simplex":
            corners = [_screen(panel, [1 if a == j else 0 for a in range(3)], "tri3") for j in range(3)]
            if obj.get("style") == "axes":
                cx, cy = _screen(panel, [0, 0], "xy")
                for x, y in corners:
                    add("line", x1=cx, y1=cy, x2=x, y2=y)
            else:
                add("poly", pts=[c for xy in corners for c in xy], closed=True)
            for j, (x, y) in enumerate(corners):
                dy = 18 if j != 1 else -9
                add("text", x=x, y=y + dy, s=obj["labels"][j], a="middle")
        elif typ == "point":
            x, y = P(_get(state, obj["at"]))
            add("mark", x=x, y=y, r=obj.get("size", 6))
            if obj.get("label"):
                label(x, y, text_of(obj["label"], state), "point")
        elif typ == "points":
            pts = _get(state, obj["of"])
            off = _get(state, obj["offset"]) if obj.get("offset") is not None else None
            for p in pts:
                q = [v * sc for v in p]
                if off is not None:
                    q = [a + b for a, b in zip(q, off)]
                x, y = P(q)
                add("mark", x=x, y=y, r=obj.get("size", 3))
        elif typ == "vector":
            base = _get(state, obj.get("from", [0, 0, 0] if coords == "tri3" else [0, 0]))
            if "by" in obj:
                d = _get(state, obj["by"])
                tip = [a + sc * b for a, b in zip(base, d)]
            else:
                tip = _get(state, obj["to"])
            (x1, y1), (x2, y2) = P(base), P(tip)
            add("arrow", x1=x1, y1=y1, x2=x2, y2=y2)
            if obj.get("label"):
                label(x2, y2, text_of(obj["label"], state), "vector")
        elif typ == "circle":
            c = _get(state, obj["center"])
            if "scale" in obj:
                c = [v * sc for v in c]
            r = _get(state, obj["radius"]) * obj.get("radius_scale", 1.0)
            s, _, _ = _frame(panel)
            factor = math.sqrt(1.5) if coords == "tri3" else 1.0  # tri3 maps the sum-zero plane with factor sqrt(3/2)
            x, y = P(c)
            add("circle", x=x, y=y, r=r * s * factor)
        elif typ == "curve":
            pts = [P(p) for p in _get(state, obj["points"])]
            add("poly", pts=[c for xy in pts for c in xy], closed=bool(obj.get("closed")))
        elif typ == "lines":
            for item in _get(state, obj["of"]):
                pts = [P(p) for p in item["points"]]
                add("poly", pts=[c for xy in pts for c in xy], closed=False)
        elif typ == "polygon":
            pts = [P(p) for p in _get(state, obj["points"])]
            orient = _get(state, obj["orientation"]) if obj.get("orientation") else 1
            add("area", pts=[c for xy in pts for c in xy], neg=orient < 0)
        elif typ == "grid":
            m = _get(state, obj["matrix"])
            lo, hi = obj.get("range", [-4, 4])
            for i in range(int(lo), int(hi) + 1):
                for a, b in (([i, lo], [i, hi]), ([lo, i], [hi, i])):
                    (x1, y1) = P([m[0] * a[0] + m[1] * a[1], m[2] * a[0] + m[3] * a[1]])
                    (x2, y2) = P([m[0] * b[0] + m[1] * b[1], m[2] * b[0] + m[3] * b[1]])
                    add("line", x1=x1, y1=y1, x2=x2, y2=y2)
        elif typ == "bars":
            vals = _get(state, obj["of"])
            x0, y0, w, h = panel["x"], panel["y"], panel["w"], panel["h"]
            bw = w / len(vals)
            top = obj.get("max", 1.0)
            for j, v in enumerate(vals):
                bh = max(0.0, min(1.0, v / top)) * (h - 24)
                add("rect", x=x0 + j * bw + 6, y=y0 + h - 18 - bh, w=bw - 12, h=bh)
                add("text", x=x0 + (j + 0.5) * bw, y=y0 + h - 4, s=obj["labels"][j], a="middle")
                add("text", x=x0 + (j + 0.5) * bw, y=y0 + h - 22 - bh, s=fmt(v, obj.get("digits", 2)), a="middle")
        elif typ == "graph":
            nodes = {n["id"]: n for n in obj["nodes"]}
            vals = _get(state, obj["values"]) if obj.get("values") else None
            for e in obj["edges"]:
                (x1, y1), (x2, y2) = P(nodes[e["from"]]["at"]), P(nodes[e["to"]]["at"])
                add("arrow", x1=x1, y1=y1, x2=x2, y2=y2)
            for j, n in enumerate(obj["nodes"]):
                x, y = P(n["at"])
                add("circle", x=x, y=y, r=16)
                add("text", x=x, y=y + 4, s=n["label"] if vals is None else fmt(vals[j], 2), a="middle")
        elif typ == "label":
            x, y = obj["x"], obj["y"]
            add("text", x=panel["x"] + x, y=panel["y"] + y, s=text_of(obj["text"], state), a=obj.get("anchor", "start"))
    return out


def direction_deg(scene, state, object_id):
    """Screen angle (degrees, counter-clockwise, y up) of a vector object's arrow; used by direction checkpoints."""
    for prim in display(scene, state):  # angles do not depend on the (uniform) panel scale
        if prim["o"] == object_id and prim["k"] == "arrow":
            return math.degrees(math.atan2(-(prim["y2"] - prim["y1"]), prim["x2"] - prim["x1"])) % 360.0
    _fail(f"direction checkpoint needs vector object {object_id!r}")


def correct_answer(scene, state, question):
    """The computed correct answer of a prediction question (never a literal; V10)."""
    rule = question["correct"]
    kind = rule["rule"]
    if kind == "angle":
        return {"deg": direction_deg(scene, state, rule["object"]), "tol_deg": rule.get("tol_deg", 27.5)}
    value = _get(state, rule["of"])
    if kind == "value":
        return {"value": value, "tol": rule["tol"]}
    if kind == "point":
        return {"point": [float(value[0]), float(value[1])], "tol": rule["tol"]}
    if kind == "argmax":
        return rule["map"][max(range(len(value)), key=lambda j: value[j])]
    if kind == "sign":
        tol = rule.get("tol", 1e-9)
        key = "0" if abs(value) <= tol else ("+" if value > 0 else "-")
        return rule.get("map", {"+": "+", "-": "-", "0": "0"})[key]
    if kind == "index":
        return rule["map"][int(value)]
    _fail("unknown answer rule " + kind)


def is_correct(scene, state, question, answer):
    want = correct_answer(scene, state, question)
    if question["type"] == "direction":
        diff = abs((DIRECTIONS[answer] - want["deg"] + 180.0) % 360.0 - 180.0)
        return diff <= want["tol_deg"]
    if question["type"] == "number":
        return abs(float(answer) - want["value"]) <= want["tol"]
    if question["type"] == "point":
        return math.hypot(float(answer[0]) - want["point"][0], float(answer[1]) - want["point"][1]) <= want["tol"]
    return answer == want


def goal_met(state, goal):
    left = _get(state, goal["of"])
    right = _get(state, goal["ref"]) * goal.get("factor", 1.0) if "ref" in goal else goal["value"]
    return {"<=": left <= right, ">=": left >= right, "abs<=": abs(left) <= right}[goal["op"]]


# ------------------------------------------------------------------ validation

def _need(cond, msg):
    if not cond:
        _fail(msg)


def _text(value, field, limit=600):
    _need(isinstance(value, str) and value.strip() and len(value) <= limit, f"{field} must be a non-empty text")


def validate(scene):
    """Strict structural validation plus evaluation of every step, checkpoint and mission (raises SceneError)."""
    _need(isinstance(scene, dict) and scene.get("schema") == SCHEMA, "schema must be " + SCHEMA)
    allowed = {"schema", "id", "title", "claim", "model", "params", "view", "objects", "equation", "terms", "steps",
               "missions", "keyframes", "lang", "public", "presets", "edit", "drag", "snap"}
    _need(set(scene) <= allowed, "unknown fields " + ", ".join(sorted(set(scene) - allowed)))
    _need(isinstance(scene.get("id"), str) and ID.fullmatch(scene["id"]), "id must be a lowercase slug")
    for f in ("title", "claim"):
        _text(scene.get(f), f)
    _need(scene.get("model") in MODELS, "model must be one of " + ", ".join(sorted(MODELS)))
    params = scene.get("params")
    _need(isinstance(params, dict) and params, "params required")
    for name, spec in params.items():
        _need(REF.fullmatch(name) and isinstance(spec, dict) and "value" in spec
              and set(spec) <= {"value", "min", "max", "int", "label"}, f"param {name}: value (+min/max/int/label)")
    view = scene.get("view")
    _need(isinstance(view, dict) and isinstance(view.get("panels"), list) and view["panels"], "view.panels required")
    _need(all(type(view.get(k)) in (int, float) and 100 <= view[k] <= 2000 for k in ("width", "height")), "view size")
    panel_ids = set()
    for p in view["panels"]:
        _need(isinstance(p, dict) and ID.fullmatch(str(p.get("id"))) and p["id"] not in panel_ids, "panel id")
        panel_ids.add(p["id"])
        _need(all(type(p.get(k)) in (int, float) for k in ("x", "y", "w", "h")) and p["w"] > 0 and p["h"] > 0, "panel box")
        d = p.get("domain")
        _need(isinstance(d, list) and len(d) == 4 and d[1] > d[0] and d[3] > d[2], "panel domain [x0,x1,y0,y1]")
        _need(set(p) <= {"id", "title", "x", "y", "w", "h", "domain", "clip"}, "panel: unknown fields")
    objects = scene.get("objects")
    _need(isinstance(objects, list) and objects, "objects required")
    oids = set()
    for o in objects:
        _need(isinstance(o, dict) and o.get("type") in OBJECT_TYPES, "object type must be one of " + ", ".join(sorted(OBJECT_TYPES)))
        _need(ID.fullmatch(str(o.get("id"))) and o["id"] not in oids, "object ids must be unique slugs")
        oids.add(o["id"])
        _need(o.get("panel") in panel_ids, f"object {o['id']}: unknown panel")
        _need(o.get("token", "ink") in PALETTE, f"object {o['id']}: unknown colour token")
        _need(o.get("coords", "xy") in ("xy", "tri3"), f"object {o['id']}: coords must be xy or tri3")
        _text(o.get("meaning"), f"object {o['id']}.meaning")
    terms = scene.get("terms")
    _need(isinstance(terms, dict) and terms, "terms required (formula-object coupling, V3)")
    for tid, t in terms.items():
        _need(REF.fullmatch(tid) and isinstance(t, dict) and set(t) <= {"name", "token", "objects"}, f"term {tid}")
        _text(t.get("name"), f"term {tid}.name")
        _need(t.get("token") in PALETTE, f"term {tid}: unknown token")
        _need(isinstance(t.get("objects"), list) and t["objects"] and set(t["objects"]) <= oids, f"term {tid}: objects")
        _need(all(next(o for o in objects if o["id"] == x).get("token", "ink") == t["token"] for x in t["objects"]),
              f"term {tid}: bound objects must share the term's colour token")
    eq = scene.get("equation")
    _need(isinstance(eq, dict) and isinstance(eq.get("segments"), list) and eq["segments"], "equation.segments")
    _text(eq.get("label"), "equation.label")
    used = set()
    for seg in eq["segments"]:
        _need(isinstance(seg, dict) and set(seg) <= {"tex", "text", "term"} and isinstance(seg.get("text"), str)
              and isinstance(seg.get("tex"), str), "equation segment needs tex and text")
        if "term" in seg:
            _need(seg["term"] in terms, "equation segment: unknown term " + str(seg["term"]))
            used.add(seg["term"])
    _need(used == set(terms), "every term must appear in the equation")
    steps = scene.get("steps")
    _need(isinstance(steps, list) and 2 <= len(steps) <= 40, "2..40 steps")
    sids = set()
    computed = []
    for i, st in enumerate(steps):
        _need(isinstance(st, dict) and set(st) <= {"id", "title", "caption", "aria", "set", "transition", "focus",
                                                   "checkpoint", "hidden"}, f"step {i}: unknown fields")
        _need(ID.fullmatch(str(st.get("id"))) and st["id"] not in sids, f"step {i}: unique id")
        sids.add(st["id"])
        for f in ("title", "caption", "aria"):
            _text(st.get(f), f"step {st['id']}.{f}", 900)
        _need(set(st.get("set", {})) <= set(params), f"step {st['id']}: sets unknown parameter")
        tr = st.get("transition", {"kind": "none"})
        _need(isinstance(tr, dict) and tr.get("kind") in TRANSITIONS, f"step {st['id']}: transition kind")
        _need(set(tr.get("animate", [])) <= set(params), f"step {st['id']}: animates unknown parameter")
        _need(type(tr.get("ms", 900)) is int and 0 <= tr.get("ms", 900) <= 6000, f"step {st['id']}: ms")
        _need(tr.get("ease", "smooth") in EASINGS, f"step {st['id']}: ease must be smooth or linear")
        _need(set(st.get("focus", [])) <= oids, f"step {st['id']}: focus names unknown object")
        _need(set(st.get("hidden", [])) <= oids, f"step {st['id']}: hides unknown object")
        _need(i > 0 or "checkpoint" not in st, "the first step cannot be a reveal")
        try:
            state = evaluate(scene, params_at(scene, i))
            display(scene, state)
            for o in objects:
                if o["type"] == "label":
                    text_of(o["text"], state)
            for f in ("caption", "aria"):
                text_of(st[f], state)
            if st.get("checkpoint"):
                text_of(st["checkpoint"].get("explain", ""), state)
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            _fail(f"step {st['id']}: {exc}")
        computed.append(state)
        cp = st.get("checkpoint")
        if cp is not None:
            _need(isinstance(cp, dict) and set(cp) <= {"predict", "explain", "feedback_step"}
                  and isinstance(cp.get("predict"), list)
                  and 1 <= len(cp["predict"]) <= 3, f"step {st['id']}: checkpoint needs 1..3 predict questions")
            if "feedback_step" in cp:  # feedback shown when the learner arrives where the answer becomes visible
                later = [x.get("id") for x in steps[i:]]
                _need(cp["feedback_step"] in later, f"step {st['id']}: feedback_step must be this or a later step")
            _text(cp.get("explain"), f"step {st['id']}.checkpoint.explain", 1200)
            for q in cp["predict"]:
                _need(isinstance(q, dict) and q.get("type") in ANSWER_TYPES and ID.fullmatch(str(q.get("id"))),
                      f"step {st['id']}: question type/id")
                _text(q.get("prompt"), "question prompt")
                _need(isinstance(q.get("correct"), dict) and q["correct"].get("rule") in
                      {"angle", "value", "argmax", "sign", "index", "point"}, "question: computed correct rule required")
                if q["type"] == "choice":
                    opts = q.get("options")
                    _need(isinstance(opts, list) and 2 <= len(opts) <= 5, "choice: 2..5 options")
                    want = correct_answer(scene, state, q)
                    _need(want in [o["id"] for o in opts], "choice: computed answer is not an option")
                elif q["type"] == "sign":
                    _need(correct_answer(scene, state, q) in ("+", "-", "0"), "sign: answer must be +, - or 0")
                elif q["type"] in ("number", "point"):
                    _need(type(q["correct"].get("tol")) in (int, float) and q["correct"]["tol"] > 0, "number: tol")
                    _need((q["type"] == "point") == (q["correct"]["rule"] == "point"), "point questions use the point rule")
                    correct_answer(scene, state, q)
                else:
                    _need(q["correct"]["rule"] == "angle" and q["correct"].get("object") in oids, "direction: object")
                    correct_answer(scene, state, q)
    for m in scene.get("missions", []):
        _need(isinstance(m, dict) and ID.fullmatch(str(m.get("id"))), "mission id")
        _text(m.get("prompt"), "mission prompt")
        _text(m.get("hint"), "mission hint")
        _need(set(m) <= {"id", "prompt", "hint", "feedback", "from_step", "sliders", "fixed", "goal"}, "mission: unknown fields")
        _need(m.get("from_step") in sids, "mission.from_step")
        sl = m.get("sliders")
        _need(isinstance(sl, list) and 1 <= len(sl) <= 3, "missions have 1..3 sliders (V6)")
        for s in sl:
            spec = params.get(s.get("param"))
            _need(spec is not None and "min" in spec and "max" in spec and isinstance(s.get("label"), str)
                  and set(s) <= {"param", "label", "step", "index"}, "mission slider needs a bounded parameter and a label")
            if "index" in s:  # one component of a vector parameter, e.g. an entry of a matrix
                _need(isinstance(spec["value"], list) and type(s["index"]) is int and 0 <= s["index"] < len(spec["value"]),
                      "mission slider index must name a component of a vector parameter")
            else:
                _need(not isinstance(spec["value"], list), "mission slider on a vector parameter needs an index")
        g = m.get("goal")
        _need(isinstance(g, dict) and g.get("op") in ("<=", ">=", "abs<=") and ("ref" in g or "value" in g), "goal")
        idx = [s["id"] for s in steps].index(m["from_step"])
        p = {**params_at(scene, idx), **m.get("fixed", {})}
        goal_met(evaluate(scene, p), g)
        if m.get("feedback"):
            text_of(m["feedback"], evaluate(scene, p))
    kf = scene.get("keyframes", {})
    _need(isinstance(kf, dict) and all(isinstance(v, list) and set(v) <= sids for v in kf.values()), "keyframes")
    _validate_interaction(scene, params, oids, sids)
    return computed


def _bounded(spec, field):
    _need(isinstance(spec, dict) and "min" in spec and "max" in spec, f"{field} needs a bounded parameter (min/max)")


def _validate_interaction(scene, params, oids, sids):
    """Presets (one round each), number inputs, draggable vector tips and timeline snapping."""
    presets = scene.get("presets", [])
    _need(isinstance(presets, list) and len(presets) <= 8, "presets: at most 8")
    pids = set()
    panel_ids = {p["id"] for p in scene["view"]["panels"]}
    for pr in presets:
        _need(isinstance(pr, dict) and set(pr) <= {"id", "label", "set", "domain"} and ID.fullmatch(str(pr.get("id")))
              and pr["id"] not in pids, "preset needs a unique id, a label and set")
        pids.add(pr["id"])
        _text(pr.get("label"), "preset label", 80)
        _need(isinstance(pr.get("set"), dict) and set(pr["set"]) <= set(params), f"preset {pr['id']}: sets unknown parameter")
        dom = pr.get("domain", {})
        _need(isinstance(dom, dict) and set(dom) <= panel_ids and all(
            isinstance(d, list) and len(d) == 4 and d[1] > d[0] and d[3] > d[2] for d in dom.values()), "preset domain")
        for i, st in enumerate(scene["steps"]):
            try:
                state = evaluate(scene, params_at(scene, i, pr["id"]))
                display(scene, state, panels_for(scene, pr["id"]))
                text_of(st["caption"], state)
                for q in (st.get("checkpoint") or {}).get("predict", []):
                    correct_answer(scene, state, q)
                text_of((st.get("checkpoint") or {}).get("explain", ""), state)
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                _fail(f"preset {pr['id']}, step {st['id']}: {exc}")
    for e in scene.get("edit", []):
        _need(isinstance(e, dict) and set(e) <= {"param", "index", "label", "step"} and e.get("param") in params
              and isinstance(e.get("label"), str), "edit needs param and label")
        spec = params[e["param"]]
        _bounded(spec, "edit")
        if isinstance(spec["value"], list):
            _need(type(e.get("index")) is int and 0 <= e["index"] < len(spec["value"]), "edit on a vector needs an index")
    for d in scene.get("drag", []):
        _need(isinstance(d, dict) and set(d) <= {"object", "param", "indices", "step"} and d.get("object") in oids
              and d.get("param") in params, "drag needs object, param and indices")
        obj = next(o for o in scene["objects"] if o["id"] == d["object"])
        _need(obj["type"] == "vector" and "to" in obj and obj.get("coords", "xy") == "xy", "drag: xy vector with 'to'")
        spec = params[d["param"]]
        _bounded(spec, "drag")
        _need(isinstance(d.get("indices"), list) and len(d["indices"]) == 2 and isinstance(spec["value"], list)
              and all(type(i) is int and 0 <= i < len(spec["value"]) for i in d["indices"]), "drag indices")
    snap = scene.get("snap")
    if snap is not None:
        _need(isinstance(snap, dict) and set(snap) == {"param", "to", "within"} and snap["param"] in params
              and type(snap["within"]) in (int, float) and 0 < snap["within"] < 0.5, "snap needs param, to, within")
        for pr in [None] + [x["id"] for x in presets]:
            got = _get(evaluate(scene, params_at(scene, 0, pr)), snap["to"])
            _need(isinstance(got, list) and all(type(x) in (int, float) for x in got), "snap.to must be a list of numbers")


def revision(scene):
    """Revision of the learner-facing timeline: changed steps/checkpoints never inherit old predictions."""
    core = {k: scene[k] for k in ("model", "params", "steps", "missions", "presets") if k in scene}
    return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def load(scene_id):
    _need(isinstance(scene_id, str) and ID.fullmatch(scene_id), "scene id")
    path = SCENES / (scene_id + ".json")
    _need(path.is_file(), "unknown scene " + scene_id)
    scene = json.loads(path.read_text(encoding="utf-8"))
    validate(scene)
    return scene


def available():
    return sorted(p.stem for p in SCENES.glob("*.json"))


# ------------------------------------------------------------------ keyframe SVG (V8)

def _n(x):
    return f"{x:.2f}".rstrip("0").rstrip(".") if abs(x) >= 0.005 else "0"


def color(tok, theme="light"):
    t = PALETTE[tok]
    return t["dark"] if theme == "dark" else t["color"]


def _mark(x, y, r, tok, theme="light"):
    c = color(tok, theme)
    shape = PALETTE[tok]["shape"]
    if shape == "square":
        return f'<rect x="{_n(x - r)}" y="{_n(y - r)}" width="{_n(2 * r)}" height="{_n(2 * r)}" fill="{c}"/>'
    if shape == "diamond":
        return f'<path d="M{_n(x)} {_n(y - r)}L{_n(x + r)} {_n(y)}L{_n(x)} {_n(y + r)}L{_n(x - r)} {_n(y)}Z" fill="{c}"/>'
    if shape == "triangle":
        return f'<path d="M{_n(x)} {_n(y - r)}L{_n(x + r)} {_n(y + r)}L{_n(x - r)} {_n(y + r)}Z" fill="{c}"/>'
    if shape == "ring":
        return f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="none" stroke="{c}" stroke-width="1.4" opacity="0.8"/>'
    return (f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(r)}" fill="{c}" stroke="{STAGE[theme]["bg"]}" '
            f'stroke-width="2"/>')


def primitive_svg(p, uid="mm", theme="light"):
    """One display primitive as SVG (identical markup in mastery_motion.js primitiveSvg)."""
    tok = PALETTE[p["t"]]
    c, dash = color(p["t"], theme), (f' stroke-dasharray="{tok["dash"]}"' if tok["dash"] else "")
    k = p["k"]
    if k == "line":
        return (f'<line x1="{_n(p["x1"])}" y1="{_n(p["y1"])}" x2="{_n(p["x2"])}" y2="{_n(p["y2"])}" stroke="{c}" '
                f'stroke-width="1" opacity="0.6"{dash}/>')
    if k == "arrow":
        dx, dy = p["x2"] - p["x1"], p["y2"] - p["y1"]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return ""
        ux, uy = dx / L, dy / L
        h = min(14.0, 0.45 * L)
        bx, by = p["x2"] - ux * h, p["y2"] - uy * h
        head = (f'M{_n(p["x2"])} {_n(p["y2"])}L{_n(bx - uy * h * 0.42)} {_n(by + ux * h * 0.42)}'
                f'L{_n(bx + uy * h * 0.42)} {_n(by - ux * h * 0.42)}Z')
        return (f'<line x1="{_n(p["x1"])}" y1="{_n(p["y1"])}" x2="{_n(bx)}" y2="{_n(by)}" stroke="{c}" '
                f'stroke-width="3.5" stroke-linecap="round"{dash}/><path d="{head}" fill="{c}"/>')
    if k == "mark":
        return _mark(p["x"], p["y"], p["r"], p["t"], theme)
    if k == "circle":
        ring = dash or ' stroke-dasharray="4 3"'
        return (f'<circle cx="{_n(p["x"])}" cy="{_n(p["y"])}" r="{_n(p["r"])}" fill="none" stroke="{c}" '
                f'stroke-width="1.8"{ring}/>')
    if k == "poly":
        pts = " ".join(_n(v) for v in p["pts"])
        tag = "polygon" if p["closed"] else "polyline"
        return f'<{tag} points="{pts}" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"{dash}/>'
    if k == "area":
        pts = " ".join(_n(v) for v in p["pts"])
        fill = f"url(#{uid}-hatch)" if p["neg"] else c
        return f'<polygon points="{pts}" fill="{fill}" fill-opacity="0.24" stroke="{c}" stroke-width="2"/>'
    if k == "rect":
        return f'<rect x="{_n(p["x"])}" y="{_n(p["y"])}" width="{_n(p["w"])}" height="{_n(p["h"])}" fill="{c}" fill-opacity="0.85"/>'
    if k == "text":
        return (f'<text x="{_n(p["x"])}" y="{_n(p["y"])}" text-anchor="{p["a"]}" fill="{c}" font-size="{FONT}" '
                f'font-weight="600">{escape(p["s"])}</text>')
    _fail("unknown primitive " + k)


def defs_svg(scene, uid, theme="light", panels=None):
    """Hatch pattern (negative orientation; a non-colour channel) and panel clips."""
    hatch = color("area", theme)
    return (f'<defs><pattern id="{uid}-hatch" width="7" height="7" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="{hatch}" stroke-width="2.4"/>'
            '</pattern>' + "".join(
                f'<clipPath id="{uid}-clip-{p["id"]}"><rect x="{_n(p["x"])}" y="{_n(p["y"])}" width="{_n(p["w"])}" '
                f'height="{_n(p["h"])}"/></clipPath>' for p in (panels or scene["view"]["panels"]) if p.get("clip"))
            + '</defs>')


def state_svg(scene, state, step, uid, theme="light", panels=None, caption=None):
    """Standalone, deterministic SVG of one state drawn with one step's visibility (hidden objects omitted)."""
    W, H = scene["view"]["width"], scene["view"]["height"]
    panels = panels or scene["view"]["panels"]
    extra = 44 if caption else 0
    ink, bg = STAGE[theme]["ink"], STAGE[theme]["bg"]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H + extra}" width="{W}" height="{H + extra}" '
             f'role="img" aria-labelledby="{uid}-t {uid}-d" font-family="Source Sans 3, Helvetica, Arial, sans-serif">',
             f'<title id="{uid}-t">{escape(scene["title"])} – {escape(step["title"])}</title>',
             f'<desc id="{uid}-d">{escape(text_of(step["aria"], state))}</desc>',
             defs_svg(scene, uid, theme, panels), f'<rect width="{W}" height="{H + extra}" fill="{bg}"/>']
    for p in panels:
        if p.get("title"):
            parts.append(f'<text x="{_n(p["x"])}" y="{_n(p["y"] - 8)}" fill="{ink}" font-size="14" '
                         f'font-weight="600">{escape(p["title"])}</text>')
    hidden = set(step.get("hidden", []))
    panel_of = {o["id"]: o["panel"] for o in scene["objects"]}
    is_label = {o["id"] for o in scene["objects"] if o["type"] == "label"}  # readouts sit outside the panel clip
    prims = [q for q in display(scene, state, panels) if q["o"] not in hidden]
    for p in panels:
        body = "".join(primitive_svg(q, uid, theme) for q in prims if panel_of[q["o"]] == p["id"] and q["o"] not in is_label)
        texts = "".join(primitive_svg(q, uid, theme) for q in prims if panel_of[q["o"]] == p["id"] and q["o"] in is_label)
        parts.append((f'<g clip-path="url(#{uid}-clip-{p["id"]})">{body}</g>' if p.get("clip") else body) + texts)
    if caption:
        parts.append(f'<text x="16" y="{H + 26}" fill="{ink}" font-size="15" font-weight="600">{escape(caption)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def keyframe_svg(scene, step_id, caption=True, preset=None, theme="light"):
    """Standalone, deterministic SVG of one step (same palette, objects, ids and scale as the interactive scene)."""
    ids = [s["id"] for s in scene["steps"]]
    _need(step_id in ids, "unknown keyframe step " + str(step_id))
    i = ids.index(step_id)
    step = scene["steps"][i]
    state = evaluate(scene, params_at(scene, i, preset))
    uid = f"mm-{scene['id']}-{step_id}" + (f"-{preset}" if preset else "") + ("-dark" if theme == "dark" else "")
    return state_svg(scene, state, step, uid, theme, panels_for(scene, preset),
                     f'{scene["title"]}: {step["title"]}' if caption else None)


def export_keyframes(scene, out_dir, kind=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    steps = scene.get("keyframes", {}).get(kind) if kind else [s["id"] for s in scene["steps"]]
    written = []
    for sid in steps or []:
        path = out / f"{scene['id']}-{sid}.svg"
        path.write_text(keyframe_svg(scene, sid) + "\n", encoding="utf-8")
        written.append(path)
    return written


# ------------------------------------------------------------------ runtime payload

def payload(scene, equation_svg=True):
    """Everything the browser runtime needs: the validated scene, palette, revision and optional MathJax term SVGs."""
    validate(scene)
    data = copy.deepcopy(scene)
    data["palette"] = PALETTE
    data["stage"] = STAGE
    data["revision"] = revision(scene)
    if equation_svg:
        for seg in data["equation"]["segments"]:
            try:
                from ..math_publishing import _render_svg
                # inline style attributes (vertical-align) would violate the pages' CSP; layout is done by CSS
                seg["svg"] = re.sub(r'\sstyle="[^"]*"', "", _render_svg(seg["tex"], False)[0])
            except Exception:  # node/MathJax missing: the runtime shows the Unicode text instead
                data["equation"]["renderer"] = "text"
                for s in data["equation"]["segments"]:
                    s.pop("svg", None)
                break
        else:
            data["equation"]["renderer"] = "mathjax-svg"
    return data
