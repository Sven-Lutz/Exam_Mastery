"""Deterministic, offline explorable explanations for source-free development.

The model library contains only trusted algorithms. It NEVER evaluates learner
code or dynamically executes code carried in a course document. The authoring
contract is independent of a particular discipline; new scientific models must
provide their own independently tested traces.
"""
from __future__ import annotations

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
    "parsons_reference": parsons_reference,
    "binary_search_lower_bound": binary_search_trace,
    "finite_discounted_return": discounted_return_trace,
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
.proof-steps summary { cursor:pointer; color:var(--blue); font-size:.93rem; }
.proof-steps details[open] { border-left:3px solid var(--accent); padding-left:.75rem; }
.parsons-lines { padding-left:1.5rem; }
.parsons-lines li { background:#f0f5fc; margin:.5rem 0; padding:.6rem .8rem; border:1px solid var(--line); border-radius:10px; }
.parsons-lines code { display:block; white-space:pre-wrap; overflow-wrap:anywhere; color:#173554; }
.parsons-lines .controls { margin-bottom:0; }
.parsons-reasons li { margin:.5rem 0; }
.parsons-reasons code { font-size:.9rem; }
.hidden { display:none!important; }
.small { font-size:.85rem; color:#c0d6f8; }
@media (max-width:800px) { .experience-grid { grid-template-columns:1fr; } .stage { top:.5rem; order:-1; }
 .scene { min-height:180px; } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { transition:none!important; scroll-behavior:auto!important; } }
"""


RUNTIME = r"""(function () {
"use strict";
const script = document.getElementById("em-interactive-data");
const model = JSON.parse(script.textContent);
const practice = {schema:"em-practice-evidence-v1",unit_id:model.unit_id,
  assessment_revision:model.assessment_revision,events:[]};
const evidenceStatus = document.getElementById("evidence-status");
function recordPractice(event) {
  if (practice.events.length >= 10000) {
    evidenceStatus.textContent = "Protokollgrenze erreicht. Bitte jetzt exportieren.";
    return;
  }
  practice.events.push({...event,at:new Date().toISOString()});
  evidenceStatus.textContent = practice.events.length
    + " Aktionen nur in dieser Sitzung erfasst; keine Antwort wird bewertet. "
    + "Zur Sicherung JSON exportieren.";
}
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
const policyEvents = []; // ephemeral: evaluated diagnostics never enter exported event logs
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
  let submitted = false, hintIndex = 0, solutionSeen = false;

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
    policyEvents.push({type:"attempt",task:taskId,t:new Date().toISOString(),diagnosis});
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
      solutionSeen = true;
    }
    status.textContent = "Lösung eingesehen – kein Nachweis selbstständiger Beherrschung.";
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
        '<p>Versuche und Hilfen werden nur im Arbeitsspeicher dieser Sitzung dokumentiert.',
        ' Keine Antworten werden übertragen. Freitext bleibt unbewertet;',
        ' rein numerische Aufgaben können lokal gegen Autoren-Sollwerte geprüft werden.',
        ' Zur Aufbewahrung das Protokoll vor dem Schließen exportieren.</p>',
        '<button type="button" id="evidence-export">Lernprotokoll als JSON exportieren</button>',
        '<p id="evidence-status" class="attempt-status" role="status" aria-live="polite">',
        'Noch keine Lernhandlungen erfasst.</p></section>',
        '<section aria-label="Wissenschaftliche Erklärung"><h2>Verstehen</h2>',
    ]
    for block in unit["teaching"]:
        parts.append('<article class="card" id="teaching-' + re_slug(block["id"]) +
                     '" data-competencies="' + _h(",".join(block["competency_ids"])) +
                     '" data-claims="' + _h(",".join(block.get("claim_ids", []))) +
                     '"><p>' + _h(block["content"]) + '</p></article>')
        proof = block.get("derivation")
        if proof:
            parts.extend([
                '<article class="card derivation" data-claims="' +
                _h(",".join(block.get("claim_ids", []))) + '">',
                '<p class="eyebrow">Herleitung und Begründung</p>',
                '<h3>' + _h(proof["title"]) + '</h3>',
                '<p>' + _h(proof["given"]) + '</p>',
                '<ol class="proof-steps">',
            ])
            for step in proof["steps"]:
                parts.append('<li><div class="proof-statement">' +
                             _h(step["statement"]) + '</div>' +
                             '<details><summary>Warum ist dieser Schritt zulässig?</summary>' +
                             '<p>' + _h(step["justification"]) + '</p></details></li>')
            parts.extend(['</ol><p class="answer"><strong>Ergebnis:</strong> ' +
                          _h(proof["result"]) + '</p></article>'])
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
    parts.append('<section aria-label="Selbstständige Übungsaufgaben"><h2>Selbstständig anwenden</h2>')
    for task in unit["assessments"]:
        slug = re_slug(task["id"])
        parts.extend([
            '<article class="card assessment" id="exercise-' + slug + '" data-task-id="' +
            _h(task["id"]) + '">',
            '<p class="eyebrow">Erst selbst lösen</p><h3>' + _h(task["prompt"]) + '</h3>',
            '<label for="attempt-' + slug + '">Dein Lösungsversuch</label>',
            '<textarea id="attempt-' + slug + '" maxlength="20000"></textarea>',
            '<div class="controls">',
            '<button class="submit-attempt" type="button" disabled>Versuch abgeben</button>',
            '<button class="retry-attempt secondary" type="button" disabled>Neuer Versuch</button>',
            ('<button class="hint-button secondary" type="button" disabled>Hinweis</button>'
             if task.get("hints") else ''),
            '<button class="answer-button secondary" type="button" disabled>Musterlösung anzeigen</button>',
            '</div><p class="attempt-status" role="status" aria-live="polite"></p>',
            '<div class="adaptive-guidance" role="status" aria-live="polite"></div>',
            ('<p class="hint-text hidden" role="status" aria-live="polite"></p>'
             if task.get("hints") else ''),
            '<div class="answer hidden"><strong>Musterlösung</strong><p>' + _h(task["solution"]) + '</p>',
            '<strong>Bewertungskriterien</strong><ul>',
        ])
        for part in task["rubric"]:
            parts.append('<li>' + _h(part["criterion"]) + ' (' + _h(part["points"]) + ' Punkte)</li>')
        parts.append('</ul></div></article>')
    parts.extend([
        '</section><p class="help">Diese Demo protokolliert nur Lernhandlungen',
        ' im Sitzungsspeicher, führt keinen fremden Code aus und zertifiziert',
        ' keine fachliche Qualität.</p>',
        '<script id="em-interactive-data" type="application/json">',
        _json_script({"schema": SCHEMA, "unit_id": unit["unit_id"],
                      "assessment_revision": assessment_revision(unit),
                      "interactions": compiled,
                      "adaptive_track": track_for_unit(unit),
                      "assessments": [{"id": x["id"], "hints": x.get("hints", []),
                                       "machine_check": x.get("machine_check"),
                                       "competency_ids": x["competency_ids"]}
                                      for x in unit["assessments"]]}),
        '</script><script>' + tutor_js + '</script><script>' + RUNTIME +
        '</script></main></body></html>',
    ])
    return "".join(parts)


def re_slug(name):
    import re
    return re.sub(r"[^a-z0-9_-]", "-", name)


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
