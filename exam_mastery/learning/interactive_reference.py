"""Deterministic, offline explorable explanations for source-free development.

The model library contains only trusted algorithms. It NEVER evaluates learner
code or dynamically executes code carried in a course document. The authoring
contract is independent of a particular discipline; new scientific models must
provide their own independently tested traces.
"""
from __future__ import annotations

from .publication_lock import locked_publisher

import argparse
import html
import json
import math
import os
from pathlib import Path
import tempfile

SCHEMA = "em-interactive-v1"


class InteractionError(ValueError):
    pass


def _number(v, name):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise InteractionError(f"{name}: finite numeric value required")
    return float(v)


def binary_search_trace(parameters):
    """Lower bound on a sorted sequence, half-open interval [lo, hi)."""
    if not isinstance(parameters, dict):
        raise InteractionError("binary_search: parameters must be an object")
    values = parameters.get("values")
    if not isinstance(values, list) or len(values) > 64:
        raise InteractionError("binary_search: values must be a list of at most 64 numbers")
    xs = [_number(v, "values") for v in values]
    if any(xs[i] > xs[i + 1] for i in range(len(xs) - 1)):
        raise InteractionError("binary_search: values must be sorted ascending")
    target = _number(parameters.get("target"), "target")
    lo, hi, steps = 0, len(xs), []
    while lo < hi:
        mid = lo + (hi - lo) // 2
        old_lo, old_hi = lo, hi
        if xs[mid] < target:
            lo = mid + 1
            rule = "value < target, so move lo to mid + 1"
        else:
            hi = mid
            rule = "value >= target, so move hi to mid"
        steps.append({
            "title": f"Iteration {len(steps) + 1}",
            "body": f"Inspect index {mid} with value {xs[mid]:g}; {rule}.",
            "state": {
                "kind": "array", "values": xs,
                "lo": old_lo, "hi": old_hi, "mid": mid,
                "next_lo": lo, "next_hi": hi,
            },
        })
        if len(steps) > 64:
            raise InteractionError("binary_search: exceeded progress bound")
    expected = next((i for i, v in enumerate(xs) if v >= target), len(xs))
    if lo != expected:
        raise InteractionError("binary_search: reference mismatch")
    return {
        "model": "binary_search_lower_bound",
        "result": lo, "result_label": "lower_bound index",
        "steps": steps or [{"title": "Empty interval", "body": "No elements to inspect.",
                            "state": {"kind": "array", "values": xs, "lo": 0, "hi": 0, "mid": -1}}],
        "invariant": "All values before lo are < target; all values at/after hi are >= target.",
    }


def discounted_return_trace(parameters):
    """Finite-horizon discounted return, backward dynamic programming."""
    if not isinstance(parameters, dict):
        raise InteractionError("discounted_return: parameters must be an object")
    rewards = parameters.get("rewards")
    if not isinstance(rewards, list) or not (1 <= len(rewards) <= 64):
        raise InteractionError("discounted_return: rewards must have 1..64 entries")
    xs = [_number(x, "reward") for x in rewards]
    gamma = _number(parameters.get("gamma"), "gamma")
    if gamma < 0 or gamma >= 1:
        raise InteractionError("discounted_return: expected 0 <= gamma < 1")
    steps, current = [], 0.0
    for t in range(len(xs) - 1, -1, -1):
        old = current
        current = xs[t] + gamma * current
        if not math.isfinite(current):
            raise InteractionError("discounted_return: numerical overflow")
        steps.append({
            "title": f"Backward step t={t}",
            "body": f"V({t}) = reward({t}) + gamma * V({t+1}) = "
                    f"{xs[t]:g} + {gamma:g} * {old:.6g} = {current:.6g}.",
            "state": {"kind": "rewards", "values": xs, "index": t, "partial": current},
        })
    direct = math.fsum(v * gamma ** i for i, v in enumerate(xs))
    if not math.isclose(current, direct, rel_tol=1e-10, abs_tol=1e-10):
        raise InteractionError("discounted_return: reference mismatch")
    return {
        "model": "finite_discounted_return",
        "result": current, "result_label": "finite discounted return",
        "steps": steps, "invariant": "Backward recursion includes exactly the rewards from t to the horizon.",
    }


def binomial_area_trace(parameters):
    """Exact partition of a square with side a+b into four rectangles.

    This trusted oracle only supports positive bounded real side lengths. Its
    underlying polynomial identity is independently checked in the semantic
    proof fixture; the numerical trace is a visual reference, not a proof.
    """
    if not isinstance(parameters, dict) or set(parameters) != {"a", "b"}:
        raise InteractionError("binomial_area: only a and b parameters permitted")
    a = _number(parameters["a"], "a")
    b = _number(parameters["b"], "b")
    if not 0.5 <= a <= 6 or not 0.5 <= b <= 6:
        raise InteractionError("binomial_area: side lengths must be in [0.5, 6]")
    parts = [a*a, a*b, b*a, b*b]
    expanded = math.fsum(parts)
    total = (a + b)**2
    if not math.isclose(expanded, total, rel_tol=1e-13, abs_tol=1e-13):
        raise InteractionError("binomial_area: independent numeric oracle mismatch")
    names = ["a²", "ab", "ab", "b²"]
    base = {"kind": "area", "a": a, "b": b}
    return {
        "model": "binomial_area_partition",
        "result": total,
        "result_label": "(a+b)^2 square area",
        "steps": [
            {
                "title": "Ausgangsfrage: eine Quadratfläche",
                "body": f"Die Seitenlänge ist a+b={a:g}+{b:g}={a+b:g}. "
                        "Welche Fläche hat das gesamte Quadrat?",
                "state": {**base, "highlight": "all"},
            },
            {
                "title": "Zerlegen: vier Rechtecke",
                "body": "Die Seiten werden jeweils bei a und b geteilt. "
                        "Die vier Teilflächen haben die Inhalte a², ab, ab und b². "
                        "Jeder Teil ist disjunkt; zusammen bedecken sie das Quadrat.",
                "state": {**base, "highlight": "parts"},
            },
            {
                "title": "Zusammenführen: distributive Identität",
                "body": f"Die Summe der vier Flächen ist {parts[0]:g} + "
                        f"{parts[1]:g} + {parts[2]:g} + {parts[3]:g} = "
                        f"{expanded:g}. Damit gilt (a+b)² = a² + 2ab + b².",
                "state": {**base, "highlight": "all"},
            },
        ],
        "invariant": (
            "Die vier disjunkten Teilrechtecke füllen exakt das Quadrat "
            "mit der Seite a+b; es wird weder Fläche überlappt noch ausgelassen."
        ),
    }


def attention_trace(parameters):
    from ..labs.models import scaled_attention
    from .. import figures_svg
    try:
        data = scaled_attention(parameters)
    except ValueError as exc:
        raise InteractionError(str(exc)) from exc
    return {'model':'scaled_dot_product_attention','result':data['output'][0][0],
            'result_label':'erste Komponente der ersten Ausgabe',
            'invariant':'Jede Gewichtszeile summiert sich zu eins; maskierte Positionen tragen null bei.',
            'steps':[{'title':'Vergleichen → gewichten → mischen',
                      'body':'Scores bestimmen Gewichte; die Ausgabe mischt Values, nicht Keys.',
                      'state':{'kind':'attention', 'svg':figures_svg.render({'type':'scaled_dot_product_attention','parameters':parameters,'title':'Attention-Zwischenwerte','alt':'Zwischenwerte der ersten Query'}), **data}}]}


def policy_gradient_trace(parameters):
    """Softmax bandit: exact gradient, one seeded REINFORCE batch and exact estimator variances."""
    from ..labs.policy_gradient import compute
    from .. import figures_svg
    try:
        m = compute(parameters)
    except ValueError as exc:
        raise InteractionError(str(exc)) from exc
    f = lambda xs: "(" + "; ".join(f"{x:.4g}" for x in xs) + ")"
    svg = figures_svg.render({"type": "softmax_policy_gradient", "parameters": parameters,
                              "title": "Politik, Gradient und Varianz",
                              "alt": "Politik, exakter Gradient und Schätzervarianz über der Baseline"})
    state = {"kind": "svg", "svg": svg}
    return {
        "model": "softmax_policy_gradient", "result": m["grad"][0],
        "result_label": "exakte Gradientenkomponente ∂J/∂θ₁",
        "invariant": "Die Komponenten von ∇J summieren sich zu null; eine von der Aktion unabhängige Baseline "
                     "ändert den Erwartungswert der Schätzung nicht, nur ihre Varianz.",
        "steps": [
            {"title": "1 · Politik aus Logits", "state": state,
             "body": f"π = softmax(θ) = {f(m['pi'])}; J(θ) = Σ π(a) r(a) = {m['J']:.4g}."},
            {"title": "2 · Exakter Gradient", "state": state,
             "body": f"∂J/∂θₖ = πₖ (rₖ − J) = {f(m['grad'])}. Arme mit r > J gewinnen Wahrscheinlichkeit."},
            {"title": "3 · REINFORCE mit N Episoden", "state": state,
             "body": f"Gezogene Häufigkeiten {m['counts']}; Baseline b = {m['baseline']:.4g}; "
                     f"ĝ = {f(m['estimate'])}; Update θ ← θ + αĝ = {f(m['theta_new'])}, J = {m['J_new']:.4g}."},
            {"title": "4 · Varianz mit und ohne Baseline", "state": state,
             "body": f"Spur der Kovarianz von ĝ: ohne Baseline {m['variance_none']:.4g}, mit b {m['variance_baseline']:.4g}, "
                     f"mit b = J {m['variance_expected']:.4g}, minimal bei b* = {m['b_opt']:.4g}: {m['variance_optimal']:.4g}."},
        ],
    }


def parsons_reference(parameters):
    """Check the ordering of provided code blocks, never execute learner code.

    The exercise checks one supplied reference sequence, not the semantic
    equivalence of independently authored implementations.
    """
    import re

    if not isinstance(parameters, dict):
        raise InteractionError("parsons: parameters must be an object")
    lines = parameters.get("lines")
    if not isinstance(lines, list) or not (3 <= len(lines) <= 12):
        raise InteractionError("parsons: 3..12 code fragments required")
    seen = set()
    for item in lines:
        if not isinstance(item, dict):
            raise InteractionError("parsons: fragment must be an object")
        key = item.get("id")
        if not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{1,40}", key):
            raise InteractionError("parsons: invalid fragment ID")
        if key in seen:
            raise InteractionError("parsons: duplicate fragment ID")
        seen.add(key)
        for field in ("code", "why"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 300:
                raise InteractionError(f"parsons: fragment {key} requires bounded {field}")
    expected = parameters.get("solution_order")
    initial = parameters.get("initial_order")
    if not (isinstance(expected, list) and isinstance(initial, list)
            and len(expected) == len(initial) == len(lines)
            and all(isinstance(v, str) for v in [*expected, *initial])
            and len(set(expected)) == len(set(initial)) == len(lines)
            and set(expected) == set(initial) == seen):
        raise InteractionError("parsons: initial/solution orders must be ID permutations")
    if expected == initial:
        raise InteractionError("parsons: the initial order must not already be solved")
    return {
        "model": "parsons_reference", "lines": lines,
        "solution_order": expected, "initial_order": initial,
        "assessment_scope": "exact reference sequence, not arbitrary code semantics",
    }


MODELS = {
    "scaled_dot_product_attention": attention_trace,
    "parsons_reference": parsons_reference,
    "binary_search_lower_bound": binary_search_trace,
    "finite_discounted_return": discounted_return_trace,
    "binomial_area_partition": binomial_area_trace,
    "softmax_policy_gradient": policy_gradient_trace,
}


def build_interaction(interaction):
    """Compile one declarative interaction into bounded, checked trace variants."""
    ref = interaction.get("model_ref")
    if ref not in MODELS:
        raise InteractionError(f"Unsupported executable model {ref!r}; refusing invented feedback")
    if (interaction.get("type") == "code_parsons") != (ref == "parsons_reference"):
        raise InteractionError("parsons model requires code_parsons interaction type")
    variants = interaction.get("variants")
    if not isinstance(variants, list) or not (1 <= len(variants) <= 12):
        raise InteractionError("interaction.variants: 1..12 variants required")
    outputs = []
    seen = set()
    for idx, candidate in enumerate(variants):
        if not isinstance(candidate, dict):
            raise InteractionError(f"variant {idx}: expected object")
        name = candidate.get("label")
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise InteractionError(f"variant {idx}: short label required")
        if name in seen:
            raise InteractionError(f"variant {idx}: duplicate label")
        seen.add(name)
        data = MODELS[ref](candidate.get("parameters"))
        outputs.append({"label": name, "parameters": candidate["parameters"], **data})
    return {
        "id": interaction["id"], "type": interaction["type"],
        "prediction_prompt": interaction["prediction_prompt"],
        "feedback_rule": interaction["feedback_rule"],
        "transfer_prompt": interaction["transfer_prompt"],
        "variants": outputs,
    }


STYLES = r"""
.attention-graphic {overflow-x:auto} .attention-graphic svg{min-width:640px} .attention-alternative dl{padding:.7rem;background:#f2f7fc;border-radius:8px} .attention-alternative dt{font-weight:650} .attention-alternative dd{margin:0 0 .4rem} .semantic-figure{overflow-x:auto} .semantic-figure svg{min-width:580px} .task-prompt {font-weight:650;font-size:1.1rem} .attention-editors {display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem} .attention-editors fieldset {border:1px solid #cad5e3;border-radius:8px} .attention-editors label {display:inline-block;width:45%;margin:.3rem} .attention-lab input[type=checkbox] {width:auto} .attention-lab svg,.semantic-figure svg {height:auto;max-width:100%} .semantic-figure {margin:1.5rem 0;padding:1rem;background:white;border:1px solid #d9e2ef;border-radius:12px} .semantic-figure figcaption {font-size:.9rem;color:#405778}
.pg-controls {display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:.3rem 1rem} .pg-control {font-weight:600;font-size:.9rem} .pg-control input[type=range]{padding:0} .pg-control output{font-variant-numeric:tabular-nums;color:var(--muted)} .pg-equations{font-family:ui-monospace,Menlo,monospace;font-size:.86rem;background:#f2f7fc;border-radius:10px;padding:.7rem .9rem;margin:.8rem 0;overflow-x:auto;white-space:pre-wrap} .pg-choice{display:inline-block;border:1px solid var(--line);border-radius:8px;margin:.2rem .4rem .2rem 0} .pg-choice label{display:inline;font-weight:500;margin-right:.6rem} .pg-choice input{width:auto} .pg-feedback div{font-family:ui-monospace,Menlo,monospace;font-size:.85rem} .pg-plot svg{width:100%;height:auto;background:white;border:1px solid var(--line);border-radius:10px} .pg-plot text{font-size:11px;fill:#1d2a3a} .pg-plot .pg-title{font-weight:700;font-size:12px} .pg-error{color:#a3341f}
.em-math { display:inline-block; max-width:100%; overflow-x:auto; vertical-align:middle; }
.em-math svg { max-width:none; }
.dmath { margin:1rem 0; overflow-x:auto; }

:root { color-scheme: light; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  --ink:#14243a; --muted:#50647a; --line:#d9e2ec; --paper:#f7f9fc; --blue:#155ee7;
  --accent:#0d7a70; background:var(--paper); color:var(--ink); }
* { box-sizing:border-box; }
body { margin:0; line-height:1.65; }
main { max-width:1120px; margin:auto; padding:clamp(1rem,4vw,3rem); }
h1 { font-size:clamp(2rem,5vw,3.4rem); line-height:1.12; letter-spacing:-.04em; }
h2 { font-size:clamp(1.4rem,3vw,2rem); line-height:1.2; }
p { max-width:70ch; }
.subtitle { color:var(--muted); max-width:66ch; }
.eyebrow { font-size:.78rem; font-weight:750; letter-spacing:.13em; text-transform:uppercase; color:var(--blue); }
.card { background:white; border:1px solid var(--line); border-radius:17px; padding:clamp(1rem,2.5vw,1.7rem); margin:1rem 0; }
.badge { display:inline-block; border:1px solid var(--line); background:var(--paper); border-radius:100px; padding:.1rem .6rem; font-size:.78rem; color:var(--muted); }
.experience { margin-top:3rem; border-top:2px solid var(--line); padding-top:2rem; }
.experience-grid { display:grid; grid-template-columns:minmax(0,1fr) minmax(280px,.9fr); gap:2rem; }
.story-scenes { min-width:0; }
.scene { margin:0 0:1.5rem; min-height:clamp(180px,38vh,360px); padding:1.5rem; border-left:4px solid var(--line);
  transition:border-color .2s,background .2s; border-radius:0 12px 12px 0; }
.scene.is-active { border-color:var(--blue); background:#eaf1ff; }
.stage { position:sticky; top:1rem; align-self:start; background:#11223a; color:#f1f6ff; border-radius:18px; padding:1.4rem; }
.stage .visual { display:flex; flex-wrap:wrap; gap:.4rem; margin:1rem 0; min-height:58px; }
.cell { padding:.5rem .7rem; min-width:2.5rem; text-align:center; border:1px solid #6c809f; border-radius:8px; }
.cell.inside { border-color:#91adf5; }
.cell.mid { color:#081c3b; background:#a8d8fd; border-color:#a8d8fd; font-weight:750; }
.cell.done { background:#173c47; border-color:#5dcfba; }
.area-grid { display:grid; width:min(100%,320px); aspect-ratio:1;
  border:2px solid #a8d8fd; border-radius:8px; overflow:hidden; margin:.7rem 0; }
.area-region { display:flex; align-items:center; justify-content:center;
  padding:.2rem; overflow:hidden; font-size:clamp(.68rem,1.7vw,.95rem);
  text-align:center; font-weight:700; border:1px solid #11223a; }
.area-region.pure { background:#96bff8; color:#0b2448; }
.area-region.mixed { background:#3da7a2; color:#052f34; }
.area-guide { font-size:.82rem; color:#c0d6f8; }
.controls { display:flex; gap:.6rem; flex-wrap:wrap; margin:.8rem 0; }
button,select,input,textarea { font:inherit; }
button { background:var(--blue); color:white; border:0; padding:.6rem .9rem; border-radius:10px; cursor:pointer; }
button.secondary { background:#e8efff; color:#183b78; }
button:disabled { cursor:not-allowed; opacity:.5; }
button:focus-visible,select:focus-visible,input:focus-visible,textarea:focus-visible { outline:3px solid #f7a941; outline-offset:3px; }
label { display:block; margin:.5rem 0; font-weight:650; }
input,select,textarea { border:1px solid #94a5ba; border-radius:8px; background:white; color:#162c48; padding:.6rem; width:100%; }
textarea { min-height:90px; }
.help { color:var(--muted); font-size:.9rem; }
.answer { margin-top:.75rem; border-left:4px solid var(--accent); padding:.65rem 1rem; background:#effaf6; }
.attempt-status { color:var(--muted); font-size:.9rem; }
.adaptive-guidance { background:#f2f7fc; border-left:3px solid var(--blue); padding:.65rem .85rem; margin:.8rem 0; font-size:.94rem; }
.adaptive-guidance a { color:var(--blue); text-decoration:underline; }
.misconception-example { margin-top:.85rem; padding:.75rem; border:1px solid var(--line); border-radius:10px; background:white; }
.misconception-example details { margin-top:.65rem; }
.misconception-example summary { cursor:pointer; font-weight:650; }
.misconception-example p { margin:.55rem 0; }
.misconception-actions { display:flex; flex-wrap:wrap; gap:1rem; margin-top:.7rem; }
.hint-text { border-left:3px solid var(--blue); padding:.6rem 1rem; background:#edf3ff; }
.proof-steps { padding-left:1.4rem; }
.proof-steps li { padding:.4rem 0; }
.proof-statement { font-weight:650; margin-bottom:.25rem; }
.proof-equation { display:block; font-size:1.08rem; white-space:normal; overflow-wrap:anywhere; padding:.4rem .65rem; background:#edf4fd; border-radius:8px; margin:.35rem 0; }
.proof-verification { display:block; font-size:.78rem; color:var(--muted); margin-bottom:.35rem; }
.proof-steps summary { cursor:pointer; color:var(--blue); font-size:.93rem; }
.proof-steps details[open] { border-left:3px solid var(--accent); padding-left:.75rem; }
.parsons-lines { padding-left:1.5rem; }
.parsons-lines li { background:#f0f5fc; margin:.5rem 0; padding:.6rem .8rem; border:1px solid var(--line); border-radius:10px; }
.parsons-lines code { display:block; white-space:pre-wrap; overflow-wrap:anywhere; color:#173554; }
.parsons-lines .controls { margin-bottom:0; }
.parsons-reasons li { margin:.5rem 0; }
.parsons-reasons code { font-size:.9rem; }
.hidden { display:none!important; }
.tutor-panel { margin:.6rem 0; } .tutor-panel summary { cursor:pointer; color:var(--blue); }
.tutor-brief { white-space:pre-wrap; max-height:16rem; overflow:auto; font-size:.8rem; background:#f4f6f9; padding:.6rem; border-radius:6px; }
.file-button { display:inline-block; padding:.45rem .8rem; border-radius:6px; background:#e8efff; color:#183b78; cursor:pointer; }
.file-button input { position:absolute; width:1px; height:1px; opacity:0; }
.small { font-size:.85rem; color:#c0d6f8; }
@media (max-width:800px) { .experience-grid { grid-template-columns:1fr; } .stage { top:.5rem; order:-1; }
 .scene { min-height:180px; } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { transition:none!important; scroll-behavior:auto!important; } }
"""


RUNTIME = r"""(function () {
"use strict";
const script = document.getElementById("em-interactive-data");
const model = JSON.parse(script.textContent);
// Learner state persists in this browser (localStorage, versioned key), per unit and assessment
// revision. Changed tasks never inherit old progress: the old record is archived, not reused.
const KEY = "em-practice-v1", FUTURE_SKEW_MS = 5 * 60e3;
function readStore() {
  try { const d = JSON.parse(localStorage.getItem(KEY) || "null");
    if (d && d.schema === 1 && d.units && typeof d.units === "object") return d; } catch (e) { }
  return {schema:1, units:{}};
}
const store = readStore();
let record = store.units[model.unit_id], archivedNote = "";
if (record && record.assessment_revision !== model.assessment_revision) {
  (store.archived = store.archived || {})[model.unit_id + "@" + record.assessment_revision] = record;
  record = null;
  archivedNote = "Die Aufgaben wurden geändert; der frühere Verlauf ist archiviert und zählt nicht für sie. ";
}
if (!record || !Array.isArray(record.events) || !Array.isArray(record.policy)) {
  record = {assessment_revision:model.assessment_revision, events:[], policy:[]};
}
store.units[model.unit_id] = record;
let persisted = false;
function save() {
  store.units[model.unit_id] = record;
  try { localStorage.setItem(KEY, JSON.stringify(store)); persisted = true; } catch (e) { persisted = false; }
}
save();
const practice = {schema:"em-practice-evidence-v1",unit_id:model.unit_id,
  assessment_revision:model.assessment_revision,events:record.events};
const evidenceStatus = document.getElementById("evidence-status");
function statusLine() {
  return archivedNote + practice.events.length + " Aktionen "
    + (persisted ? "in diesem Browser gespeichert (bleiben nach dem Neuladen erhalten)"
                 : "nur in dieser Sitzung erfasst – Browserspeicher nicht verfügbar")
    + "; keine Antwort wird übertragen, Freitext bleibt unbewertet. Sicherung als JSON exportieren.";
}
evidenceStatus.textContent = practice.events.length ? statusLine()
  : archivedNote + "Noch keine Lernhandlungen erfasst."
    + (persisted ? " Sie werden in diesem Browser gespeichert." : "");
function recordPractice(event) {
  if (practice.events.length >= 10000) {
    evidenceStatus.textContent = "Protokollgrenze erreicht. Bitte jetzt exportieren.";
    return;
  }
  practice.events.push({...event,at:new Date().toISOString()});
  save();
  evidenceStatus.textContent = statusLine();
}
function download(name, text) {
  const url = URL.createObjectURL(new Blob([text], {type:"application/json"}));
  const link = document.createElement("a");
  link.href = url; link.download = name; document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
const fileSlug = model.unit_id.replace(/[^a-z0-9_-]/g,"-");
document.getElementById("practice-backup-export").addEventListener("click", () => {
  download("mastery-" + fileSlug + "-sicherung.json", JSON.stringify({schema:"em-practice-backup-v1",
    unit_id:model.unit_id, assessment_revision:model.assessment_revision, exported:new Date().toISOString(),
    events:record.events, policy:record.policy}, null, 1) + "\n");
});
const PRACTICE_TYPES = ["attempt","hint","solution_reveal","tutor_brief"], POLICY_TYPES = ["attempt","hint","solution","tutor"];
document.getElementById("practice-backup-import").addEventListener("change", ev => {
  const file = ev.target.files[0];
  if (!file || file.size > 4e6) return;
  file.text().then(text => {
    const o = JSON.parse(text), known = new Set(model.assessments.map(a => a.id)), latest = Date.now() + FUTURE_SKEW_MS;
    if (!o || o.schema !== "em-practice-backup-v1" || o.unit_id !== model.unit_id
        || o.assessment_revision !== model.assessment_revision || !Array.isArray(o.events) || !Array.isArray(o.policy)) {
      throw new Error("Keine Sicherung dieser Einheit und Aufgabenfassung (em-practice-backup-v1).");
    }
    const merge = (cur, add, types, taskKey, timeKey) => {
      const key = e => [e[timeKey], e.type, e[taskKey]].join("|"), have = new Set(cur.map(key)); let n = 0;
      for (const e of add) {
        if (!e || typeof e !== "object" || !types.includes(e.type) || !known.has(e[taskKey])
            || typeof e[timeKey] !== "string" || !(Date.parse(e[timeKey]) <= latest) || have.has(key(e))) continue;
        cur.push(e); have.add(key(e)); n++;
      }
      cur.sort((a, b) => a[timeKey] < b[timeKey] ? -1 : a[timeKey] > b[timeKey] ? 1 : 0); return n;
    };
    const n = merge(record.events, o.events, PRACTICE_TYPES, "task_id", "at") + merge(record.policy, o.policy, POLICY_TYPES, "task", "t");
    save();
    evidenceStatus.textContent = n + " Einträge übernommen; vorhandene bleiben erhalten. Seite wird neu geladen.";
    setTimeout(() => location.reload(), 600);
  }).catch(e => { evidenceStatus.textContent = "Import abgelehnt: " + e.message; });
});
document.getElementById("evidence-export").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify(practice,null,2)+"\n"],{type:"application/json"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "exam-mastery-" + model.unit_id.replace(/[^a-z0-9_-]/g,"-") + "-evidence.json";
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
});
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = String(text);
  return e;
}
function fmt(x) { return Number.isInteger(x) ? String(x) : Number(x).toPrecision(7); }
function draw(stage, step) {
  const heading = stage.querySelector(".stage-title");
  const info = stage.querySelector(".stage-info");
  const visual = stage.querySelector(".visual");
  heading.textContent = step.title;
  info.textContent = step.body;
  visual.replaceChildren();
  const s = step.state || {};
  if (s.kind === "array") {
    (s.values || []).forEach((v, i) => {
      const cell = el("span", "cell" + (i >= s.lo && i < s.hi ? " inside" : "")
          + (i === s.mid ? " mid" : ""), fmt(v));
      cell.setAttribute("aria-label", "index " + i + ", value " + v
          + (i === s.mid ? ", current midpoint" : ""));
      visual.append(cell);
    });
  } else if (s.kind === "area") {
    const grid = el("div", "area-grid");
    // Exact ratio of physical segment lengths; the semantic oracle supplies
    // positive bounded sides and the four area terms, not arbitrary HTML.
    grid.style.gridTemplateColumns = s.a + "fr " + s.b + "fr";
    grid.style.gridTemplateRows = s.a + "fr " + s.b + "fr";
    const regions = [
      ["a²", s.a * s.a, "pure"],
      ["ab", s.a * s.b, "mixed"],
      ["ab", s.a * s.b, "mixed"],
      ["b²", s.b * s.b, "pure"],
    ];
    regions.forEach(([label,value,kind],index)=>{
      const region = el("div", "area-region " + kind, label);
      region.setAttribute("aria-label", "Teilfläche " + (index + 1) +
        ": " + label + " = " + fmt(value));
      region.title = label + " = " + fmt(value);
      grid.append(region);
    });
    visual.append(grid);
    visual.append(el("span", "area-guide",
      "Seiten a = " + fmt(s.a) + ", b = " + fmt(s.b) +
      ". Die Breiten und Höhen stehen im Verhältnis a : b."));
  } else if (s.kind === "attention" || s.kind === "svg") {
    const parsed = new DOMParser().parseFromString(s.svg, "image/svg+xml");
    visual.append(document.importNode(parsed.documentElement, true));
  } else if (s.kind === "rewards") {
    (s.values || []).forEach((v, i) => {
      const cell = el("span", "cell" + (i >= s.index ? " done" : "")
          + (i === s.index ? " mid" : ""), fmt(v));
      cell.setAttribute("aria-label", "reward t=" + i + ": " + v);
      visual.append(cell);
    });
  }
}
function setup(spec) {
  const root = document.getElementById("interaction-" + spec.id.replace(/[^a-z0-9_-]/g, "-"));
  const picker = root.querySelector(".variant-picker");
  const input = root.querySelector(".prediction");
  const check = root.querySelector(".check");
  const reveal = root.querySelector(".reveal");
  const result = root.querySelector(".result");
  const story = root.querySelector(".story-scenes");
  const stage = root.querySelector(".stage");
  const previous = root.querySelector(".previous");
  const next = root.querySelector(".next");
  let current = null, steps = [], stepIndex = 0, predicted = null;
  spec.variants.forEach((v, i) => {
    const o = document.createElement("option"); o.value = String(i); o.textContent = v.label;
    picker.add(o);
  });
  function show(index, scroll) {
    stepIndex = Math.max(0, Math.min(index, steps.length - 1));
    const sections = story.querySelectorAll(".scene");
    sections.forEach((s, i) => s.classList.toggle("is-active", i === stepIndex));
    draw(stage, steps[stepIndex]);
    previous.disabled = stepIndex === 0;
    next.disabled = stepIndex === steps.length - 1;
    if (scroll && sections[stepIndex]) sections[stepIndex].scrollIntoView({behavior:"auto",block:"nearest"});
  }
  function unlock() {
    story.replaceChildren();
    steps = current.steps.map(s => s);
    steps.forEach((s, index) => {
      const box = el("section", "scene");
      box.dataset.index = String(index);
      box.append(el("p", "eyebrow", "Step " + (index + 1) + " / " + steps.length),
                 el("h3", "", s.title), el("p", "", s.body));
      story.append(box);
    });
    show(0, false);
    story.classList.remove("hidden");
    previous.classList.remove("hidden");
    next.classList.remove("hidden");
    reveal.disabled = false;
    if ("IntersectionObserver" in window) {
      if (root._observer) root._observer.disconnect();
      root._observer = new IntersectionObserver(entries => {
        const visible = entries.filter(e => e.isIntersecting).sort((a,b) =>
          b.intersectionRatio - a.intersectionRatio);
        if (visible.length) show(Number(visible[0].target.dataset.index), false);
      }, {rootMargin:"-15% 0px -50% 0px", threshold:[0,.2,.5,.8]});
      story.querySelectorAll(".scene").forEach(x => root._observer.observe(x));
    }
  }
  function reset() {
    current = spec.variants[Number(picker.value)];
    input.value = "";
    predicted = null;
    story.replaceChildren();
    story.classList.add("hidden");
    previous.classList.add("hidden");
    next.classList.add("hidden");
    result.replaceChildren();
    result.classList.add("hidden");
    reveal.disabled = true;
    draw(stage, {title:"Prediction first",
      body:spec.prediction_prompt,
      state:{kind:"empty"}});
  }
  picker.addEventListener("change",reset);
  check.addEventListener("click",() => {
    const n = Number(String(input.value).replace(",","."));
    if (!input.value.trim() || !Number.isFinite(n)) {
      result.textContent = "Enter a finite numerical prediction first.";
      result.classList.remove("hidden");
      return;
    }
    predicted = n;
    result.textContent = "Prediction recorded. Explore the verified trace before revealing the answer.";
    result.classList.remove("hidden");
    unlock();
  });
  previous.addEventListener("click",()=>show(stepIndex-1,true));
  next.addEventListener("click",()=>show(stepIndex+1,true));
  reveal.addEventListener("click",()=> {
    if (predicted === null) return;
    const correct = Math.abs(predicted-current.result) <=
      1e-8*Math.max(1, Math.abs(current.result));
    result.textContent = (correct ? "Prediction matches. " : "Prediction differs. ")
      + current.result_label + " = " + fmt(current.result)
      + ". Invariant: " + current.invariant + " " + spec.feedback_rule;
    result.classList.remove("hidden");
  });
  picker.value = "0";
  reset();
}
function setupParsons(spec) {
  const root = document.getElementById("interaction-" + spec.id.replace(/[^a-z0-9_-]/g, "-"));
  const picker = root.querySelector(".variant-picker");
  const list = root.querySelector(".parsons-lines");
  const feedback = root.querySelector(".parsons-feedback");
  const reasons = root.querySelector(".parsons-reasons");
  let variant = null, order = [];
  spec.variants.forEach((v, i) => {
    const o = document.createElement("option");
    o.value = String(i); o.textContent = v.label; picker.add(o);
  });
  function redraw() {
    list.replaceChildren();
    const byId = new Map(variant.lines.map(line => [line.id, line]));
    order.forEach((id, i) => {
      const item = byId.get(id);
      const li = document.createElement("li");
      li.dataset.id = id;
      li.append(el("code", "", item.code));
      const buttons = el("div", "controls");
      const up = el("button", "secondary up", "Nach oben");
      const down = el("button", "secondary down", "Nach unten");
      up.type = "button"; down.type = "button";
      up.disabled = i === 0; down.disabled = i === order.length - 1;
      up.setAttribute("aria-label", "Baustein " + item.code.trim() + " nach oben");
      down.setAttribute("aria-label", "Baustein " + item.code.trim() + " nach unten");
      function move(direction) {
        const j = i + direction;
        const old = order[i]; order[i] = order[j]; order[j] = old;
        feedback.textContent = "";
        reasons.classList.add("hidden");
        redraw();
      }
      up.addEventListener("click", () => move(-1));
      down.addEventListener("click", () => move(1));
      buttons.append(up, down); li.append(buttons); list.append(li);
    });
  }
  function reset() {
    variant = spec.variants[Number(picker.value)];
    order = variant.initial_order.slice();
    feedback.textContent = "";
    reasons.replaceChildren();
    reasons.classList.add("hidden");
    redraw();
  }
  picker.addEventListener("change", reset);
  root.querySelector(".check-order").addEventListener("click", () => {
    const correct = order.every((id, i) => id === variant.solution_order[i]);
    if (!correct) {
      feedback.textContent = "Noch nicht die vorgegebene Referenzreihenfolge. "
        + "Prüfe Initialisierung, Schleifenkörper und Rückgabe.";
      reasons.classList.add("hidden");
      return;
    }
    feedback.textContent = "Referenzreihenfolge getroffen. "
      + "Begründe jeden Schritt; das ist noch kein Test selbst geschriebenen Codes. "
      + spec.feedback_rule;
    reasons.replaceChildren();
    const byId = new Map(variant.lines.map(line => [line.id, line]));
    variant.solution_order.forEach(id => {
      const li = el("li");
      li.append(el("code", "", byId.get(id).code),
                el("p", "", byId.get(id).why));
      reasons.append(li);
    });
    reasons.classList.remove("hidden");
  });
  picker.value = "0"; reset();
}

model.interactions.forEach(spec => {
  if (spec.type === "code_parsons") setupParsons(spec);
  else setup(spec);
});
const byTask = new Map(model.assessments.map(x=>[x.id,x]));
// Persisted with the attempt text in this browser only; diagnostics and answers never enter the exported evidence log.
const policyEvents = record.policy;
const competencyText = id => (model.competencies || {})[id] || id;
function explainPolicy(taskId, diagnosis, container) {
  const decision = window.EMT.decide(model.adaptive_track, policyEvents);
  container.replaceChildren();
  container.dataset.rule = decision.rule;
  if (diagnosis.result === "unverified") {
    container.append(el("strong", "", "Fachliche Prüfung erforderlich. "));
    container.append(el("span", "", "Die Antwort wurde nicht bewertet; Regel " +
      decision.rule + ". Keine Kompetenzfreigabe, kein Mastery-Nachweis."));
    return;
  }
  if (diagnosis.result === "invalid") {
    container.textContent = "Die Eingabe ist numerisch ungültig. " +
      "Korrigiere deine Eingabe und beginne einen neuen Versuch.";
    return;
  }
  const labels = {
    correct:"Numerisch passend", incorrect:"Numerische Abweichung",
    partial:"Numerisch teilweise passend"
  };
  container.append(el("strong", "", (labels[diagnosis.result] || "Geprüft") +
    " (lokaler Autoren-Referenzwert). "));
  container.append(el("span", "", decision.rationale + " " + decision.uncertainty));
  const category = diagnosis.error_category
    ? model.adaptive_track.categories[diagnosis.error_category] : null;
  if (category && (diagnosis.result === "incorrect" || diagnosis.result === "partial")) {
    const panel = el("section", "misconception-example");
    panel.append(el("strong", "", "Mögliche Fehlstrategie: " + category.label));
    panel.append(el("p", "", category.feedback));
    const details = document.createElement("details");
    const head = document.createElement("summary");
    head.textContent = "Beispiel einer Fehlstrategie und begründete Korrektur";
    details.append(head,
      el("p", "", category.wrong_example),
      el("p", "", category.corrected_example),
      el("p", "", category.explanation));
    panel.append(details);
    const actions = el("div", "misconception-actions");
    if (category.support && category.support.type === "worked_example") {
      const id = "teaching-" + category.support.ref.replace(/[^a-z0-9_-]/g,"-");
      if (document.getElementById(id)) {
        const link = document.createElement("a");
        link.href = "#" + id; link.textContent = "Herleitung im Lehrtext";
        actions.append(link);
      }
    }
    if (category.visual && category.visual.type === "interactive_reference") {
      const id = "interaction-" + category.visual.ref.replace(/[^a-z0-9_-]/g,"-");
      if (document.getElementById(id)) {
        const link = document.createElement("a");
        link.href = "#" + id; link.textContent = "Modell untersuchen";
        actions.append(link);
      }
    }
    panel.append(actions);
    container.append(panel);
  }
  const nextId = decision.next_task;
  if (nextId && byTask.has(nextId)) {
    const slug = nextId.replace(/[^a-z0-9_-]/g,"-");
    const target = document.getElementById("exercise-" + slug);
    if (target) {
      const jump = document.createElement("a");
      jump.href = "#exercise-" + slug;
      jump.textContent = " Nächste Lernhandlung öffnen";
      container.append(jump);
    }
  }
}
document.querySelectorAll(".assessment").forEach(root=>{
  const taskId = root.dataset.taskId;
  const definition = byTask.get(taskId);
  const input = root.querySelector("textarea");
  const submit = root.querySelector(".submit-attempt");
  const retry = root.querySelector(".retry-attempt");
  const reveal = root.querySelector(".answer-button");
  const solution = root.querySelector(".answer");
  const hintButton = root.querySelector(".hint-button");
  const hintText = root.querySelector(".hint-text");
  const status = root.querySelector(".attempt-status");
  const guidance = root.querySelector(".adaptive-guidance");
  const tutorButton = root.querySelector(".tutor-button");
  const tutorQuestion = root.querySelector(".tutor-question");
  const tutorStatus = root.querySelector(".tutor-status");
  const tutorBrief = root.querySelector(".tutor-brief");
  let submitted = false, hintIndex = 0, solutionSeen = false;
  // Restore from this browser: the evidence log's order rules (hint indices, one reveal) stay valid.
  hintIndex = Math.min(definition.hints.length,
    practice.events.filter(e => e.type === "hint" && e.task_id === taskId).length);
  solutionSeen = practice.events.some(e => e.type === "solution_reveal" && e.task_id === taskId);
  const priorAttempts = policyEvents.filter(e => e.type === "attempt" && e.task === taskId);
  if (priorAttempts.length) {
    const tutors = policyEvents.filter(e => e.type === "tutor" && e.task === taskId).length;
    submitted = true;
    input.value = priorAttempts[priorAttempts.length - 1].observed || "";
    input.readOnly = true; submit.disabled = true; retry.disabled = false; reveal.disabled = false;
    if (hintButton && hintIndex < definition.hints.length) hintButton.disabled = false;
    if (tutorButton) tutorButton.disabled = false;
    if (hintIndex > 0 && hintText) {
      hintText.textContent = definition.hints[hintIndex - 1]; hintText.classList.remove("hidden");
    }
    status.textContent = "Wiederhergestellt: " + priorAttempts.length + " Versuch(e)"
      + (hintIndex ? ", " + hintIndex + " Hinweis(e)" : "")
      + (solutionSeen ? ", Musterlösung eingesehen" : "")
      + (tutors ? ", Tutor-Brief erstellt" : "")
      + ". Freitext bleibt unbewertet.";
    root.dataset.restored = String(priorAttempts.length);
  }

  input.addEventListener("input",()=>{
    if (!submitted) submit.disabled = !input.value.trim();
  });
  submit.addEventListener("click",()=>{
    const answer = input.value.trim();
    if (submitted || !answer || answer.length > 20000) return;
    submitted = true;
    input.readOnly = true;
    submit.disabled = true;
    retry.disabled = false;
    reveal.disabled = false;
    if (hintButton && hintIndex < definition.hints.length) hintButton.disabled = false;
    // Reuse the existing, browser/Python-parity-tested diagnosis and policy.
    // Numeric results are formative; authored expected values are not
    // independent proof of scientific correctness.
    const spec = definition.machine_check;
    const checked = spec ? window.EMT.diagnose({
      ...spec, id:taskId, kc_id:definition.competency_ids[0]
    }, answer) : {
      task_id:taskId, result:"unverified", error_category:null,
      method:"open", evidence:"UNVERIFIED"
    };
    const diagnosis = {
      task_id:taskId, result:checked.result,
      error_category:checked.error_category,
      method:checked.method, evidence:checked.evidence
    }; // deliberately omit observed raw response
    status.textContent = diagnosis.result === "unverified"
      ? "Versuch dokumentiert; Freitext ist noch nicht bewertet."
      : "Numerisch formativ geprüft; die wissenschaftliche Referenzprüfung bleibt offen.";
    // Export records the action and length only, not the answer or grade.
    recordPractice({type:"attempt",task_id:taskId,response_chars:answer.length});
    policyEvents.push({type:"attempt",task:taskId,t:new Date().toISOString(),diagnosis,observed:answer});
    save();
    if (tutorButton) tutorButton.disabled = false;
    explainPolicy(taskId, diagnosis, guidance);
  });
  retry.addEventListener("click",()=>{
    if (!submitted) return;
    submitted = false;
    input.readOnly = false;
    input.value = "";
    submit.disabled = true;
    retry.disabled = true;
    reveal.disabled = true;
    solution.classList.add("hidden");
    status.textContent = "Neuer Lösungsversuch. Frühere Hilfen bleiben im Protokoll.";
    guidance.replaceChildren();
    if (hintButton) hintButton.disabled = true;
    input.focus();
  });
  if (hintButton) hintButton.addEventListener("click",()=>{
    if (!submitted || hintIndex >= definition.hints.length) return;
    hintText.textContent = definition.hints[hintIndex];
    hintText.classList.remove("hidden");
    recordPractice({type:"hint",task_id:taskId,hint_index:hintIndex});
    policyEvents.push({type:"hint",task:taskId,t:new Date().toISOString()});
    save();
    hintIndex += 1;
    hintButton.disabled = hintIndex >= definition.hints.length;
    status.textContent = "Hinweis verwendet. Die nächste Antwort gilt nicht als unabhängig.";
  });
  reveal.addEventListener("click",()=>{
    if (!submitted) return;
    solution.classList.remove("hidden");
    if (!solutionSeen) {
      recordPractice({type:"solution_reveal",task_id:taskId});
      policyEvents.push({type:"solution",task:taskId,t:new Date().toISOString()});
      save();
      solutionSeen = true;
    }
    status.textContent = "Lösung eingesehen – kein Nachweis selbstständiger Beherrschung.";
  });
  // Tutor brief for Claude/ChatGPT: R9 rules + this task + own attempts + hints + sources. Evidence roles carry no
  // model solution (CD-7). Preparing it counts as help for this task (logged as tutor_brief / tutor).
  if (tutorButton) tutorButton.addEventListener("click", () => {
    const attempts = policyEvents.filter(e => e.type === "attempt" && e.task === taskId);
    if (!attempts.length) return;
    const cats = model.adaptive_track.categories || {};
    const sibling = model.assessments.find(a => a.id !== taskId
      && a.competency_ids.some(c => definition.competency_ids.includes(c))
      && !policyEvents.some(e => e.type === "attempt" && e.task === a.id));
    const text = window.EMT.portableBrief({
      title: model.title, objective: "", competency: definition.competency_ids.map(competencyText).join("; "),
      task: {id: taskId, role: definition.role, prompt: definition.prompt},
      attempts: attempts.map(e => ({t: e.t, observed: e.observed || "", result: e.diagnosis.result,
        category: e.diagnosis.error_category ? ((cats[e.diagnosis.error_category] || {}).label || e.diagnosis.error_category) : null})),
      hints: definition.hints.slice(0, hintIndex), solution_viewed: solutionSeen,
      solution: definition.solution ? [definition.solution] : null,
      sources: definition.sources || [], source_status: model.source_status,
      parallel: sibling ? "Aufgabe " + sibling.id + " im Explorable, ohne Tutor." : null,
      question: tutorQuestion ? tutorQuestion.value : ""});
    tutorBrief.textContent = text; tutorBrief.classList.remove("hidden");
    recordPractice({type:"tutor_brief",task_id:taskId});
    policyEvents.push({type:"tutor",task:taskId,t:new Date().toISOString()});
    save();
    status.textContent = "Tutor-Brief erstellt – diese Aufgabe gilt ab jetzt als mit Hilfe bearbeitet.";
    window.EMT.copyText(text).then(ok => {
      tutorStatus.textContent = (ok ? "In die Zwischenablage kopiert. " : "Kopieren nicht möglich – Text unten markieren und kopieren. ")
        + "In Claude oder ChatGPT einfügen; erst dann verlässt er den Rechner.";
    });
  });
});
})();"""


def _json_script(obj):
    # Protect </script> and HTML special characters, even for untrusted source text.
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace(
        "&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _h(value):
    return html.escape(str(value), quote=True)


def render_html(unit):
    from .experience import validate
    from .experience_math import markup
    rich = lambda text: markup(unit, text)
    from .experience_evidence import assessment_revision
    from .experience_adaptation import track_for_unit

    # Bundle the already-tested legacy diagnosis/policy runtime once, instead
    # of implementing a second JS evaluator or decision engine.
    tutor_js = (Path(__file__).resolve().parents[1] /
                "templates" / "em_tutor.js").read_text(encoding="utf-8")
    if "</script" in tutor_js.lower():
        raise InteractionError("Unsafe script delimiter in trusted tutor runtime")

    report = validate(unit)
    if not report["valid"]:
        raise InteractionError("Invalid learning unit: " + "; ".join(report["errors"]))
    compiled = []
    for i in unit["interactions"]:
        compiled.append(build_interaction(i))
    from .experience_proof_checks import verify as verify_polynomial
    if not compiled:
        raise InteractionError("No executable interactions; cannot claim an interactive learning product")
    parts = [
        '<!doctype html><html lang="de"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>' + _h(unit["title"]) + ' · Exam Mastery</title>',
        '<style>' + STYLES + '</style></head><body><main>',
        '<p class="eyebrow">Exam Mastery · Explorable Explanation</p>',
        '<h1>' + _h(unit["title"]) + '</h1>',
        '<p class="subtitle">Von der Erklärung zur eigenen Vorhersage, '
        'zum verifizierten Experiment und zum Transfer.</p>',
        '<p class="badge">' + ('Synthetische Referenzeinheit – keine Vorlesungsquellen'
        if unit["source_mode"] == "synthetic" else 'Quellengebundene Einheit – Fachprüfung erforderlich') + '</p>',
        '<section class="card" aria-label="Lernprotokoll"><h2>Lokal üben</h2>',
        '<p>Versuche, Hinweise, eingesehene Lösungen und Tutor-Briefs werden in diesem Browser gespeichert',
        ' (localStorage, Schlüssel em-practice-v1) und bleiben nach dem Neuladen erhalten.',
        ' Keine Antworten werden übertragen. Freitext bleibt unbewertet;',
        ' rein numerische Aufgaben können lokal gegen Autoren-Sollwerte geprüft werden.',
        ' Browserdaten können gelöscht werden: Sicherung regelmäßig exportieren.</p>',
        '<button type="button" id="evidence-export">Lernprotokoll als JSON exportieren</button>',
        ' <button type="button" id="practice-backup-export" class="secondary">Sicherung exportieren</button>',
        ' <label class="file-button secondary">Sicherung importieren',
        '<input type="file" id="practice-backup-import" accept=".json,application/json"></label>',
        '<p id="evidence-status" class="attempt-status" role="status" aria-live="polite">',
        'Noch keine Lernhandlungen erfasst.</p></section>',
        '<section aria-label="Wissenschaftliche Erklärung"><h2>Verstehen</h2>',
    ]
    from .experience_graphics import html_frames
    for block in unit["teaching"]:
        parts.append('<article class="card" id="teaching-' + re_slug(block["id"]) +
                     '" data-competencies="' + _h(",".join(block["competency_ids"])) +
                     '" data-claims="' + _h(",".join(block.get("claim_ids", []))) +
                     '"><div>' + rich(block["content"]) + '</div></article>')
        for extra in block.get("blocks", []):
            if extra["type"] == "definition":
                parts.append('<article class="card"><p class="eyebrow">Definition</p><h3>' + _h(extra["term"]) +
                             '</h3><div>' + rich(extra["md"]) + '</div></article>')
            elif extra["type"] in ("box", "summary"):
                label = extra.get("title") or ("Zusammenfassung" if extra["type"] == "summary" else "Hinweis")
                parts.append('<article class="card"><p class="eyebrow">' + _h(label) + '</p><div>' +
                             rich(extra["md"]) + '</div></article>')
        parts.append(html_frames(unit, block["id"]))
        proof = block.get("derivation")
        if proof:
            parts.extend([
                '<article class="card derivation" data-claims="' +
                _h(",".join(block.get("claim_ids", []))) + '">',
                '<p class="eyebrow">Herleitung und Begründung</p>',
                '<h3>' + _h(proof["title"]) + '</h3>',
                '<div>' + rich(proof["given"]) + '</div>',
                '<ol class="proof-steps">',
            ])
            for step in proof["steps"]:
                parts.append('<li><div class="proof-statement">' +
                             rich(step["statement"]) + '</div>')
                if "math_check" in step:
                    proof_check = step["math_check"]
                    # Exactly the same authored identity is checked in the
                    # canonical validator and typeset into the PDF.
                    verify_polynomial(proof_check)
                    parts.append(
                        '<div class="proof-equation">' +
                        rich(verify_polynomial(proof_check)["latex"]) +
                        '</div><small class="proof-verification">'
                        'Exakt symbolisch geprüft: nur diese Polynomgleichung, '
                        'nicht der gesamte Beweis.</small>'
                    )
                parts.append(
                    '<details><summary>Warum ist dieser Schritt zulässig?</summary>' +
                    '<div>' + rich(step["justification"]) + '</div></details></li>'
                )
            parts.extend(['</ol><div class="answer"><strong>Ergebnis:</strong> ' +
                          rich(proof["result"]) + '</div></article>'])
    parts.append('</section>')
    for spec in compiled:
        slug = re_slug(spec["id"])
        if spec["type"] == "code_parsons":
            parts.extend([
                '<section class="experience" id="interaction-' + slug + '">',
                '<p class="eyebrow">Programmieren · Code rekonstruieren</p>',
                '<h2>' + _h(spec["prediction_prompt"]) + '</h2>',
                '<div class="card">',
                '<label for="variant-' + slug + '">Referenzaufgabe wählen</label>',
                '<select id="variant-' + slug + '" class="variant-picker"></select>',
                '<p class="help">Bringe die vorgegebenen Codebausteine mit den Tasten '
                'in die richtige Reihenfolge. Es wird kein eingegebener Code ausgeführt.</p>',
                '<ol class="parsons-lines" aria-label="Sortierbare Codebausteine"></ol>',
                '<button type="button" class="check-order">Reihenfolge prüfen</button>',
                '<p class="parsons-feedback" role="status" aria-live="polite"></p>',
                '<ol class="parsons-reasons hidden" aria-label="Begründung jedes Schrittes"></ol>',
                '</div><article class="card"><h3>Transfer</h3><p>' +
                _h(spec["transfer_prompt"]) + '</p></article></section>',
            ])
            continue
        parts.extend([
            '<section class="experience" id="interaction-' + slug + '">',
            '<p class="eyebrow">Vorhersagen · experimentieren · erklären</p>',
            '<h2>' + _h(spec["prediction_prompt"]) + '</h2>',
            '<div class="card"><label for="variant-' + slug + '">Experiment wählen</label>',
            '<select class="variant-picker" id="variant-' + slug + '"></select>',
            '<label for="prediction-' + slug + '">Deine numerische Vorhersage</label>',
            '<input id="prediction-' + slug + '" class="prediction" type="text" inputmode="decimal" ',
            'autocomplete="off" aria-describedby="prediction-help-' + slug + '">',
            '<p class="help" id="prediction-help-' + slug + '">Erst eigene Vorhersage eingeben. '
            'Danach werden die geprüften Rechenschritte sichtbar.</p>',
            '<div class="controls"><button class="check" type="button">Vorhersage abgeben</button>',
            '<button class="reveal secondary" type="button" disabled>Ergebnis aufdecken</button></div>',
            '<p class="result answer hidden" role="status" aria-live="polite"></p></div>',
            '<div class="experience-grid"><div class="story-scenes hidden" aria-label="Schrittweise Erklärung"></div>',
            '<aside class="stage" aria-label="Mathematisches Modell">',
            '<p class="eyebrow">Dynamische Visualisierung</p>',
            '<h3 class="stage-title"></h3><p class="stage-info"></p>',
            '<div class="visual" role="img" aria-label="Zustandsdarstellung"></div>',
            '<div class="controls"><button class="previous secondary hidden" type="button">Zurück</button>',
            '<button class="next secondary hidden" type="button">Weiter</button></div>',
            '<p class="small">Zahlen stammen aus einem deterministisch geprüften Referenzmodell.</p>',
            '</aside></div><article class="card"><h3>Transfer</h3><p>' +
            _h(spec["transfer_prompt"]) + '</p></article></section>',
        ])
    from .. import figures_svg
    for spec in compiled:
        if spec['variants'][0].get('model') != 'scaled_dot_product_attention':
            continue
        parameters = spec['variants'][0]['parameters']
        parts.extend([
            '<section class="attention-lab card" aria-label="Freies Attention-Experiment">',
            '<p class="eyebrow">Freies Experiment · Q, K und V verändern</p>',
            '<h2>Vergleichen ist nicht Mischen</h2>',
            '<p>Ändere zuerst nur einen Value. Die Gewichte sollten gleich bleiben, die Ausgabe kann sich bewegen. '
            'Ändere danach eine Query oder einen Key: Welche Gewichte ändern sich? '
            'Konstruiere anschließend eine vollständig maskierte Zeile und begründe die Fehlermeldung.</p>',
            '<div class="attention-graphic" tabindex="0" aria-label="Schaubild horizontal erkunden">'+figures_svg.render({'type':'scaled_dot_product_attention','parameters':parameters,
                                'title':'Attention aus denselben Modellobjekten','alt':'Scores, Gewichte, Values und Beiträge der ersten Query'})+'</div>',
            '<details><summary>Alle Zwischenwerte als lesbarer Text</summary><div class="attention-alternative"></div></details><div class="attention-editors"></div><details><summary>Maske: erlaubte Verbindungen</summary><div class="attention-masks"></div></details>',
            '<label>Temperatur T (0,05 bis 20)<input class="attention-temperature" type="number" min="0.05" max="20" step="0.05"></label>',
            '<label><input class="attention-scale" type="checkbox"> Durch die Quadratwurzel der Key-Dimension skalieren</label>',
            '<p class="attention-status" role="status" aria-live="polite"></p><p class="attention-readout" aria-live="polite"></p>',
            '<button class="attention-reset" type="button">Ausgangsbeispiel wiederherstellen</button> ',
            '<button class="attention-export secondary" type="button">Experimentparameter speichern</button>',
            '<script class="attention-parameters" type="application/json">'+_json_script(parameters)+'</script></section>',
        ])
    for spec in compiled:
        if spec['variants'][0].get('model') != 'softmax_policy_gradient':
            continue
        parameters = spec['variants'][0]['parameters']
        parts.extend([
            '<section class="pg-lab card" id="pg-lab-' + re_slug(spec['id']) + '" aria-label="Freies Policy-Gradient-Experiment">',
            '<p class="eyebrow">Freies Experiment · vorhersagen, sampeln, aktualisieren</p>',
            '<h2>Gradientenrichtung vorhersagen, dann REINFORCE beobachten</h2>',
            '<p>1. Regler einstellen. 2. Für jeden Arm vorhersagen, ob sein Logit beim exakten Gradientenschritt steigt. '
            '3. Episoden ziehen: Die Balken zeigen die Schätzung ĝ, die schwarzen Striche den exakten Gradienten. '
            '4. Wiederholt sampeln und die Streuung ohne und mit Baseline vergleichen. 5. Updates anwenden und die Lernkurve verfolgen.</p>',
            '<div class="pg-controls"></div>',
            '<div class="pg-equations" aria-live="polite"></div>',
            '<div class="pg-predict"></div><div class="pg-feedback" role="status" aria-live="polite"></div>',
            '<div class="controls"><button type="button" class="pg-sample" disabled>Stichprobe ziehen</button>',
            '<button type="button" class="pg-update secondary" disabled>Update θ ← θ + αĝ</button>',
            '<button type="button" class="pg-run secondary" disabled>20 Updates</button>',
            '<button type="button" class="pg-reset secondary">Zurücksetzen</button></div>',
            '<div class="pg-plot"></div><p class="pg-status attempt-status" role="status" aria-live="polite"></p>',
            '<script class="pg-parameters" type="application/json">' + _json_script(parameters) + '</script></section>',
        ])
    parts.append('<section aria-label="Selbstständige Übungsaufgaben"><h2>Selbstständig anwenden</h2>')
    for task in unit["assessments"]:
        slug = re_slug(task["id"])
        parts.extend([
            '<article class="card assessment" id="exercise-' + slug + '" data-task-id="' +
            _h(task["id"]) + '">',
            '<p class="eyebrow">Erst selbst lösen</p><div class="task-prompt">' + rich(task["prompt"]) + '</div>',
            '<label for="attempt-' + slug + '">Dein Lösungsversuch</label>',
            '<textarea id="attempt-' + slug + '" maxlength="20000"></textarea>',
            '<div class="controls">',
            '<button class="submit-attempt" type="button" disabled>Versuch abgeben</button>',
            '<button class="retry-attempt secondary" type="button" disabled>Neuer Versuch</button>',
            ('<button class="hint-button secondary" type="button" disabled>Hinweis</button>'
             if task.get("hints") else ''),
            '<button class="answer-button secondary" type="button" disabled>Musterlösung anzeigen</button>',
            '</div><p class="attempt-status" role="status" aria-live="polite"></p>',
            '<details class="tutor-panel"><summary>Tutor fragen (Claude oder ChatGPT)</summary>',
            '<p class="help">Erst nach einem eigenen Versuch. Der Brief enthält Tutor-Regeln, Aufgabe, Ihre Versuche, ',
            'genutzte Hinweise und Quellen' + ('; keine Musterlösung, weil diese Aufgabe selbstständiges Lösen prüft'
            if task.get("role", "core") in ("similar", "transfer", "retest") else '') +
            '. Er zählt als Hilfe für diese Aufgabe.</p>',
            '<label for="tutor-q-' + slug + '">Ihre Frage (optional)</label>',
            '<input type="text" class="tutor-question" id="tutor-q-' + slug + '" maxlength="2000" autocomplete="off">',
            '<button class="tutor-button" type="button" disabled>Tutor-Brief kopieren</button>',
            '<p class="tutor-status" role="status" aria-live="polite"></p><pre class="tutor-brief hidden"></pre></details>',
            '<div class="adaptive-guidance" role="status" aria-live="polite"></div>',
            ('<p class="hint-text hidden" role="status" aria-live="polite"></p>'
             if task.get("hints") else ''),
            '<div class="answer hidden"><strong>Musterlösung</strong><div>' + rich(task["solution"]) + '</div>',
            '<strong>Bewertungskriterien</strong><ul>',
        ])
        for part in task["rubric"]:
            parts.append('<li>' + _h(part["criterion"]) + ' (' + _h(part["points"]) + ' Punkte)</li>')
        parts.append('</ul></div></article>')
    parts.append('</section><section aria-label="Quellen und Erstellung"><h2>Quellen und Erstellung</h2>')
    import re as source_re
    for source in unit['sources']:
        parts.append('<article class="card" id="source-'+re_slug(source['id'])+'"><p>'+_h(source['locator'])+'</p>')
        for url in source_re.findall(r'https?://[^\s<>]+', source['locator']):
            parts.append('<a rel="noopener noreferrer" href="'+_h(url)+'">Öffentliches Original öffnen</a>')
        parts.append('</article>')
    if unit.get('authorship'):
        parts.append('<div class="card"><h3>Wie diese Einheit entstand</h3>')
        for key in ('content','automatic','independent'):
            parts.append('<p>'+_h(unit['authorship'].get(key,''))+'</p>')
        parts.append('<p>Fachliche und menschliche Abnahme: ausstehend.</p></div>')
    parts.extend([
        '</section><p class="help">Diese Seite speichert Lernhandlungen nur lokal',
        ' in diesem Browser, führt keinen fremden Code aus und zertifiziert',
        ' keine fachliche Qualität.</p>',
        '<script id="em-interactive-data" type="application/json">',
        _json_script({"schema": SCHEMA, "unit_id": unit["unit_id"],
                      "title": unit["title"], "source_status": _source_status(unit),
                      "assessment_revision": assessment_revision(unit),
                      "interactions": compiled,
                      "adaptive_track": track_for_unit(unit),
                      "competencies": {c["id"]: c.get("description", c["id"])
                                       for c in unit["competencies"]},
                      "assessments": [_tutor_view(unit, x) for x in unit["assessments"]]}),
        '</script><script>' + tutor_js + '</script><script>' + RUNTIME +
        '</script><script>' + (Path(__file__).resolve().parents[1] / 'templates/attention_math.js').read_text() + '</script><script>' + (Path(__file__).resolve().parents[1] / 'templates/attention_experience.js').read_text() + '</script><script>' + (Path(__file__).resolve().parents[1] / 'templates/policy_gradient_math.js').read_text() + '</script><script>' + (Path(__file__).resolve().parents[1] / 'templates/policy_gradient_lab.js').read_text() + '</script></main></body></html>',
    ])
    return "".join(parts)


EVIDENCE_ROLES = ("similar", "transfer", "retest")  # mirrors tutor.KEY_WITHHELD_ROLES


def _source_status(unit):
    return ("Synthetische Referenzeinheit, fachlich nicht unabhängig geprüft" if unit["source_mode"] == "synthetic"
            else "Quellengebundene Einheit, fachliche Prüfung ausstehend")


def _tutor_view(unit, task):
    """Browser data for one assessment. Evidence roles never carry the model solution (CD-7)."""
    claims = {c["id"]: c for c in unit.get("claims", [])}
    sources = {s["id"]: s["locator"] for s in unit.get("sources", [])}
    locators = []
    for claim_id in task.get("claim_ids", []):
        for ref in claims.get(claim_id, {}).get("source_refs", []):
            if ref in sources and sources[ref] not in locators:
                locators.append(sources[ref])
    role = task.get("role", "core")
    view = {"id": task["id"], "hints": task.get("hints", []), "machine_check": task.get("machine_check"),
            "competency_ids": task["competency_ids"], "role": role, "prompt": task["prompt"],
            "sources": locators or [sources[k] for k in sorted(sources)]}
    if role not in EVIDENCE_ROLES:
        view["solution"] = task["solution"]
    return view


def re_slug(name):
    import re
    return re.sub(r"[^a-z0-9_-]", "-", name)


@locked_publisher
def publish(unit, out_dir):
    """Write exactly one offline HTML and an internal integrity manifest.

    Never overwrite unknown or manually modified study content. Identical
    builds do not rewrite the file. No model calls or network access.
    """
    import hashlib

    content = render_html(unit)
    data = content.encode("utf-8")
    sha = hashlib.sha256(data).hexdigest()
    root = Path(out_dir)
    folder = root / "Interaktiv"
    target = folder / "index.html"
    key = hashlib.sha256(unit["unit_id"].encode()).hexdigest()[:12]
    state = root / ".em-state" / ("interactive-" + key + ".json")
    prev = json.loads(state.read_text(encoding="utf-8")) if state.exists() else None
    if target.exists():
        if not prev:
            raise ValueError("Refusing to overwrite unmanaged Interaktiv/index.html")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != prev.get("sha256") or prev.get("unit_id") != unit["unit_id"]:
            raise ValueError("Refusing to overwrite modified Interaktiv/index.html")
        if actual == sha:
            return {"status": "UNCHANGED", "path": str(target),
                    "bytes": target.stat().st_size, "sha256": sha, "model_calls": 0}
    folder.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".em-interactive-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    state.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "em-interactive-publish-v1",
        "unit_id": unit["unit_id"], "sha256": sha,
        "academic_status": "HUMAN_REVIEW_PENDING",
    }
    fd, temporary = tempfile.mkstemp(prefix=".em-state-", suffix=".tmp", dir=state.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, state)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"status": "CREATED_OR_UPDATED", "path": str(target),
            "bytes": target.stat().st_size, "sha256": sha, "model_calls": 0}
