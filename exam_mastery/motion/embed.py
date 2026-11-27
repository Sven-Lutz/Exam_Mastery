"""Embedding Mastery Motion scenes: a scene section for any HTML page, the standalone demo page of the Mastery app
and the thin hook that lets experience units (Interaktiv) show the motion scene that belongs to their model."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from . import available, keyframe_svg, load, payload

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
ASSETS = ("mastery_motion.css", "policy_gradient_math.js", "mastery_motion.js")
# Which public motion scenes belong to which interaction model of an experience unit (generic, no course content).
MODEL_SCENES = {"softmax_policy_gradient": ("rl-softmax-simplex",)}


def _json_script(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e") \
        .replace("&", "\\u0026")


def scene_section(scene_id, equation_svg=True):
    """A self-contained <section> for a stored scene: static keyframes as no-JS fallback, scene data for the runtime."""
    return section(load(scene_id), equation_svg)


def section(scene, equation_svg=True):
    """Section for a (validated) scene dict, e.g. a plane scene built from an experience unit's variants."""
    frames = scene.get("keyframes", {}).get("textbook") or [scene["steps"][0]["id"]]
    first = (scene.get("presets") or [{}])[0].get("id")
    fallback = "".join(f"<figure>{keyframe_svg(scene, sid, preset=first)}</figure>" for sid in frames)
    return (f'<section class="mm-scene" id="motion-{escape(scene["id"])}" aria-label="Mastery Motion: {escape(scene["title"])}">'
            f'<div class="mm-fallback">{fallback}</div>'
            f'<script type="application/json" class="mm-data">{_json_script(payload(scene, equation_svg))}</script>'
            '</section>')


def scenes_for_unit(unit):
    ids = []
    for interaction in unit.get("interactions", []) or []:
        for sid in MODEL_SCENES.get(interaction.get("model_ref"), ()):
            if sid not in ids:
                ids.append(sid)
    return ids


def unit_html(unit, runtime=False):
    """Hook for experience units: inline CSS + scripts + sections (the Interaktiv page is one self-contained file).
    runtime=True adds CSS and runtime even without model scenes (sections placed elsewhere on the page)."""
    ids = scenes_for_unit(unit)
    if not ids and not runtime:
        return ""
    css = (TEMPLATES / "mastery_motion.css").read_text(encoding="utf-8")
    js = (TEMPLATES / "mastery_motion.js").read_text(encoding="utf-8")
    return ('<style>' + css + '</style>' + "".join(scene_section(i) for i in ids) +
            '<script>' + js + '</script>')


def demo_page(scene_id, assets="../assets"):
    """Standalone page for the Mastery app (served under /motion/<id>.html; CSP: only same-origin scripts)."""
    scene = load(scene_id)
    csp = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; "
           "connect-src 'self'; base-uri 'none'; form-action 'none'")
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">'
            f'<title>Mastery Motion – {escape(scene["title"])}</title>'
            f'<link rel="stylesheet" href="{assets}/em_tokens.css"><link rel="stylesheet" href="{assets}/mastery_home.css">'
            f'<link rel="stylesheet" href="{assets}/mastery_motion.css"></head><body>'
            '<header class="m-top"><a class="m-brand" href="../index.html#start">Mastery</a>'
            '<nav class="m-nav" aria-label="Bereiche"><a href="../index.html#start">Start</a></nav></header>'
            '<main class="m-shell"><p class="m-note">Mastery Motion (Demo-Szene, synthetische Zahlen). Schritt für Schritt '
            'oder an der Zeitachse ziehen; an Wendepunkten zuerst vorhersagen. Tastatur: ← → zwischen Schritten.</p>'
            + scene_section(scene_id) +
            f'</main><script src="{assets}/policy_gradient_math.js"></script>'
            f'<script src="{assets}/mastery_motion.js"></script></body></html>\n')


def write_demo_pages(root):
    """Copy runtime assets and write motion/<id>.html for every public scene; returns the listed demos."""
    root = Path(root)
    (root / "assets").mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        (root / "assets" / name).write_bytes((TEMPLATES / name).read_bytes())
    out = root / "motion"
    out.mkdir(parents=True, exist_ok=True)
    demos = []
    for sid in available():
        scene = load(sid)
        if not scene.get("public"):
            continue
        (out / f"{sid}.html").write_text(demo_page(sid), encoding="utf-8")
        demos.append({"id": sid, "title": scene["title"], "claim": scene["claim"], "href": f"motion/{sid}.html"})
    return demos
