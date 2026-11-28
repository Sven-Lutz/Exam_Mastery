"""Two user-facing PDF books from the same canonical experience unit.

This adapter deliberately reuses the existing exam_mastery.typeset design,
MathJax/Chromium renderer and document model. It does not create a second
PDF engine, and it never pretends a synthetic fixture is an academic release.
"""
from __future__ import annotations

from .publication_lock import locked_publisher

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .. import typeset
from .experience import validate

SCHEMA = "em-experience-books-v1"


def _safe_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for data in iter(lambda: file.read(1 << 20), b""):
            digest.update(data)
    return digest.hexdigest()


def _atomic_bytes(path, body):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".em-state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


STAGE_TITLES = {
    "worked_example": "Stufe 1 · Durchgerechnete Beispiele",
    "guided": "Stufe 2 · Geführte Aufgaben",
    "independent": "Stufe 3 · Selbstständige Aufgaben",
    "transfer": "Stufe 4 · Transfer",
    "exam": "Stufe 5 · Klausurniveau",
}
SOURCE_PROVENANCE = {"lecture": "course", "lecture_slides": "course", "script": "course", "exercise": "course",
                     "paper": "supplement", "book": "supplement", "literature": "supplement",
                     "original_derivation": "derivation"}


def _provenance(item, claim_map, source_map):
    """Side label of a grounded section: unverified claims dominate, then lecture, literature, own derivation."""
    claims = [claim_map[c] for c in item.get("claim_ids", [])]
    if not claims or any(c["evidence_status"] != "verified" for c in claims):
        return "unconfirmed"
    kinds = {SOURCE_PROVENANCE.get(source_map[s].get("kind"), "unconfirmed")
             for c in claims for s in c["source_refs"]}
    for label in ("unconfirmed", "course", "supplement", "derivation"):
        if label in kinds:
            return label
    return "unconfirmed"


def book_model(unit):
    """Adapt an evidence-linked unit to the *existing* typeset.em-book-v1 model."""
    checked = validate(unit)
    if not checked["valid"]:
        raise ValueError("Invalid learning unit: " + "; ".join(checked["errors"]))
    from .experience_math import project
    unit = project(unit)
    from .experience_proof_checks import verify as verify_polynomial
    source_map = {s["id"]: s for s in unit["sources"]}
    claim_map = {c["id"]: c for c in unit["claims"]}
    synthetic = unit["source_mode"] == "synthetic"
    sections = []
    figures = {}
    from .experience_graphics import specifications
    graphic_frames = specifications(unit)
    # Attach each authored counterexample to exactly one matching teaching
    # section; never scatter repeated errors throughout the textbook.
    placement = {}
    for spec in unit.get("misconceptions", []):
        placement[spec["id"]] = spec.get("worked_example_id") or next(
            block["id"] for block in unit["teaching"] if
            set(block["competency_ids"]).intersection(spec["competency_ids"])
        )
    for i, item in enumerate(unit["teaching"], 1):
        provenance = []
        for claim_id in item.get("claim_ids", []):
            for source_id in claim_map[claim_id]["source_refs"]:
                source = source_map[source_id]
                status = claim_map[claim_id]["evidence_status"]
                if source.get("short") and not synthetic:
                    # Short side note; the full locator stays in the reference list.
                    label = ("Ungeprüft: " if status == "unverified" else "") + source["short"]
                else:
                    prefix = ("Synthetisch" if synthetic else
                              "Ungeprüft" if status == "unverified" else "Verifiziert (Statusangabe)")
                    label = prefix + ": " + source["locator"]
                if label not in provenance:
                    provenance.append(label)
        prov = "didactic" if synthetic else _provenance(item, claim_map, source_map)
        src = "; ".join(provenance)
        rendered = {}
        if item.get("derivation"):
            derivation = item["derivation"]
            rendered["derivation"] = [{
                "type": "example", "label": "Schritt für Schritt", "kind_label": "Herleitung",
                "title": derivation["title"], "given": derivation["given"],
                "steps": [[
                    step["statement"] + (
                        " " + verify_polynomial(step["math_check"])["latex"]
                        if "math_check" in step else ""
                    ),
                    step["justification"],
                ] for step in derivation["steps"]],
                "result": derivation["result"], "kc_ids": item["competency_ids"],
                "block_id": item["id"] + "/derivation", "prov": prov, "src": src,
            }]
        for spec in unit.get("misconceptions", []):
            if placement[spec["id"]] != item["id"]:
                continue
            cited = []
            for claim_id in spec.get("claim_ids", []):
                for source_id in claim_map[claim_id]["source_refs"]:
                    label = ("Synthetische Referenz: " if synthetic else
                             "Quellenangabe (Fachprüfung erforderlich): ") + source_map[source_id]["locator"]
                    if label not in cited:
                        cited.append(label)
            rendered.setdefault("misconceptions", []).append({
                "type": "misconception",
                "wrong": spec["wrong_example"],
                "right": spec["corrected_example"],
                "why": spec["explanation"],
                "kc_ids": spec["competency_ids"],
                "block_id": spec["id"],
                "prov": "didactic" if synthetic else "unconfirmed",
                "src": "; ".join(cited),
            })
        for graphic, frame, spec in graphic_frames:
            if graphic['teaching_id'] == item['id']:
                gid = graphic['id'] + '-state-' + str(frame)
                figures[gid] = spec
                rendered.setdefault("graphic:" + graphic["id"], []).append(
                    {'type': 'figure', 'id': gid, 'caption': graphic['caption'] + ' ' + graphic['alt'],
                     'kc_ids': graphic['competency_ids'], 'prov': 'didactic'})
        section_blocks = [{"type": "lead" if i == 1 else "text", "md": item["content"],
                           "kc_ids": item["competency_ids"], "block_id": item["id"],
                           "prov": prov, "src": src}]
        # Optional authored order: definitions, boxes, the derivation and figures where the text needs them.
        for index, block in enumerate(item.get("blocks", [])):
            kind = block["type"]
            if kind == "derivation":
                section_blocks.extend(rendered.pop("derivation", []))
            elif kind == "graphic":
                section_blocks.extend(rendered.pop("graphic:" + block["id"], []))
            elif kind == "definition":
                section_blocks.append({"type": "definition", "term": block["term"], "md": block["md"],
                                       "block_id": f"{item['id']}/block-{index}", "prov": prov, "src": src})
            elif kind == "box":
                section_blocks.append({"type": "box", "kind": block.get("kind", "note"), "md": block["md"],
                                       **({"title": block["title"]} if block.get("title") else {}),
                                       "block_id": f"{item['id']}/block-{index}"})
            elif kind == "summary":
                section_blocks.append({"type": "summary", "md": block["md"],
                                       **({"title": block["title"]} if block.get("title") else {})})
        section_blocks.extend(rendered.pop("derivation", []))
        section_blocks.extend(rendered.pop("misconceptions", []))
        for key in sorted(rendered):
            section_blocks.extend(rendered[key])
        sections.append({
            "title": item.get("section_title") or
                     item["id"].rsplit("/", 1)[-1].replace("-", " ").capitalize(),
            "blocks": section_blocks,
        })
    from .experience import STAGES
    task_figure = {}
    for graphic, frame, _spec in graphic_frames:
        for task_id in graphic["assessment_ids"]:
            task_figure.setdefault(task_id, graphic["id"] + "-state-" + str(frame))
    grouped = {name: [] for name in (*STAGES, None)}
    for index, task in enumerate(unit["assessments"], 1):
        rubric = [[x["criterion"], x["points"]] for x in task["rubric"]]
        stage = task.get("stage")
        solution = {"answer": task["solution"], "rubric": rubric}
        if task.get("solution_approach"):
            solution["approach"] = task["solution_approach"]
        if task.get("solution_steps"):
            solution["steps"] = task["solution_steps"]
        if task.get("typical_errors"):
            solution["errors"] = task["typical_errors"]
        grouped[stage].append({
            "id": task["id"], "no": str(index), "prompt": task["prompt"],
            "stage_label": "transfer", "operation": task.get("operation") or "",
            "kc_keys": task["competency_ids"], "space": 0 if stage == "worked_example" else 26,
            "points": sum(x["points"] for x in task["rubric"]),
            **({"title": task["title"]} if task.get("title") else {}),
            **({"scaffold": task["scaffold"]} if task.get("scaffold") else {}),
            **({"figure": task_figure[task["id"]]} if task["id"] in task_figure else {}),
            "worked": stage == "worked_example",
            "solution": solution,
        })
    stages = [{"title": STAGE_TITLES[name], "level": level, "items": grouped[name], "key": name}
              for level, name in enumerate(STAGES, 1) if grouped[name]]
    if grouped[None]:
        stages.append({"title": "Selbstständige Anwendung und Transfer", "level": 4,
                       "items": grouped[None], "key": "unstaged"})
    keys = [s["locator"] for s in unit["sources"]]
    return {
        "meta": {
            "title": unit["title"],
            "subtitle": "Synthetische Referenzeinheit" if synthetic else "Fachliche Lernunterlagen",
            "course": "Exam Mastery · synthetische Referenz" if synthetic else
                      unit.get("course_title", "Exam Mastery"),
            "chapter_no": 1, "lang": "de", "date": "",
            "engine": "Experience Core",
            "status_line": (
                "**SYNTHETISCHES TESTMATERIAL – kein fachlich freigegebenes Lehrbuch.** "
                if synthetic else "**FACHLICH NICHT UNABHÄNGIG GEPRÜFT.** "
            ) + "Automatisch gesetzter und strukturell validierter Entwurf.",
        },
        "figures": figures, "sections": sections,
        "stages": stages,
        "exam": None, "cards": unit["cards"],
        "competencies": [{"key": c["id"], "operation": c["operation"]} for c in unit["competencies"]],
        "objectives": [c["description"] for c in unit["competencies"]
                       if isinstance(c.get("description"), str) and c["description"].strip()],
        "references": [("Synthetische Quellen – nicht als Literatur zitieren" if synthetic
                        else "Identifizierte Quellen – Verifikation im Einzelnen prüfen", keys)],
        "production_notes": (
            "Dieses Dokument ist eine synthetische Entwicklungsreferenz. "
            "Weder Quellenprüfung noch wissenschaftliche oder menschliche Abnahme liegen vor."
            if synthetic else
            "Quellenstatus und fachliche Korrektheit erfordern unabhängige Prüfung. "
            "Technische Validierung ist kein wissenschaftlicher Freigabenachweis."
        ) + ("\n\n" + "\n\n".join(unit['authorship'].get(key,'') for key in
                 ('content','automatic','independent','sources_read')) if unit.get('authorship') else ""),
    }


def _combined_workbook(book):
    """One workbook with questions first, then complete worked solutions.

    Uses the existing Doc rendering, cover, TOC and item layout; no duplicate
    HTML ids and no separate fifth 'Musterloesungen' product.
    """
    d = typeset.Doc(book, "workbook")
    sections, toc = [], []
    sections.append('<section><h2 id="aufgaben">Teil I · Aufgaben</h2>'
                    '<p>Bearbeiten Sie die Aufgaben vor dem Blick auf die Musterlösungen.</p></section>')
    toc.append((1, "aufgaben", "Teil I · Aufgaben"))
    attached = {task.get("figure") for stage in book["stages"] for task in stage["items"]} - {None}
    for graphic_id, spec in book['figures'].items():
        # Figures appear inside the tasks that use them. Only a unit without any task figure keeps the
        # previous reference block before the tasks; other keyframes remain in the textbook.
        if not attached:
            sections.append(d.figure({'type':'figure','id':graphic_id,'caption':spec['title']}))
    for idx, stage in enumerate(book["stages"], 1):
        tag = f"aufgaben-{idx}"
        toc.append((2, tag, stage["title"]))
        # Stages flow on (no forced page per stage); the heading is kept with its first task.
        head = f'<h2 id="{tag}">{typeset.inline(stage["title"])}</h2>'
        parts = ['<section class="stage first">']
        for number, task in enumerate(stage["items"]):
            html_ = typeset._item_html(d, task, solution=bool(task.get("worked")), space=not task.get("worked"))
            if task.get("worked"):  # a worked example is longer than a page fragment: let it break across pages
                html_ = html_.replace('<div class="item"', '<div class="item worked" style="break-inside:auto"', 1)
            # Long worked examples would leave a nearly empty page if kept together with the heading: the stage
            # heading joins only the task head and prompt (the item's own keep group), never the whole example.
            if number == 0:
                html_ = (f'<div class="keephead">{head}{html_}</div>' if not task.get("worked")
                         else html_.replace('<div class="keephead">', '<div class="keephead">' + head, 1))
            parts.append(html_)
        parts.append("</section>")
        sections.extend(parts)
    sections.append('<section style="break-before:page"><h2 id="loesungen">'
                    'Teil II · Vollständige Musterlösungen</h2>'
                    '<p>Die angegebenen Bewertungskriterien sind Teil der Übung '
                    'und keine offiziellen Prüfungsvorgaben.</p></section>')
    toc.append((1, "loesungen", "Teil II · Vollständige Musterlösungen"))
    for idx, stage in enumerate(book["stages"], 1):
        tag = f"loesungen-{idx}"
        if all(task.get("worked") for task in stage["items"]):
            continue  # worked examples carry their solution in part I
        toc.append((2, tag, stage["title"] + " · Lösungen"))
        head = f'<h2 id="{tag}">{typeset.inline(stage["title"])}</h2>'
        parts, first = ['<section class="stage first">'], True
        for task in stage["items"]:
            if task.get("worked"):
                continue
            # The same semantic task receives a distinct PDF anchor for the solution.
            copy = dict(task, id="loesung-" + task["id"])
            html_ = typeset._item_html(d, copy, solution=True, space=False)
            parts.append(f'<div class="keephead">{head}{html_}</div>' if first else html_)
            first = False
        parts.append("</section>")
        sections.extend(parts)
    body = (
        typeset._cover(book, "Arbeitsbuch", "Aufgaben und vollständige Musterlösungen")
        + typeset._toc(toc) + "".join(sections)
    )
    return body, toc


@locked_publisher
def publish(unit, output_dir):
    """Publish exactly Lehrbuch.pdf and Arbeitsbuch.pdf with reuse and overwrite guards.

    Files are staged together. If the second replacement fails, the prior
    release is restored when possible. An interrupted process may leave an
    inconsistent pair; a subsequent run fails closed on hash mismatch.
    """
    book = book_model(unit)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    unit_key = hashlib.sha256(unit["unit_id"].encode()).hexdigest()[:12]
    state_dir = root / ".em-state"
    state_dir.mkdir(parents=True, exist_ok=True)
    record_path = state_dir / f"books-{unit_key}.json"
    record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None
    from .experience_runtime import fingerprint, fonts
    from . import experience_books, experience_proof_checks, experience_math, experience_graphics
    from ..labs import models
    from .. import math_publishing, motion
    from ..motion import models as motion_models, plane as motion_plane, embed as motion_embed
    runtime = fingerprint(
        [experience_books, experience_proof_checks, experience_math, experience_graphics, models, math_publishing, typeset,
         typeset.figures_svg, motion, motion_models, motion_plane, motion_embed],
        assets=[("mathjax", typeset.NODE / "mathjax-full/es5/tex-svg-full.js"),
                *fonts(typeset.NODE, [(pkg, variants) for _, pkg, variants in typeset.FONTS])],
        packages=["playwright", "PyMuPDF"], settings=[("css", typeset.CSS)])
    inputs = hashlib.sha256(json.dumps(
        {"unit": unit, "adapter": SCHEMA, "runtime": runtime},
        sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    names = ("Lehrbuch.pdf", "Arbeitsbuch.pdf")
    for name in names:
        path = root / name
        if path.exists():
            if not record or name not in record.get("files", {}):
                raise ValueError(f"Refusing to overwrite unmanaged {name}")
            if _safe_hash(path) != record["files"][name]:
                raise ValueError(f"Refusing to overwrite modified {name}")
    if record and all((root / p).exists() for p in names) and record.get("input_sha256") == inputs:
        return {"status": "UNCHANGED", "products": list(names),
                "academic_status": "HUMAN_REVIEW_PENDING", "model_calls": 0}
    with tempfile.TemporaryDirectory(prefix=".em-books-build-", dir=root) as tmp:
        target = Path(tmp)
        text_body, text_toc = typeset.textbook(book)
        textbook_report = typeset.render_document(
            text_body, text_toc, book["meta"]["title"] + " – Lehrbuch",
            target, "Lehrbuch", book["meta"]["title"] + " · Lehrbuch")
        work_body, work_toc = _combined_workbook(book)
        workbook_report = typeset.render_document(
            work_body, work_toc, book["meta"]["title"] + " – Arbeitsbuch",
            target, "Arbeitsbuch", book["meta"]["title"] + " · Arbeitsbuch")
        staged = {n: target / n for n in names}
        if not all(path.is_file() and path.stat().st_size > 0 for path in staged.values()):
            raise ValueError("Typesetting did not produce both PDF products")
        # Preserve existing files during replacement; cleanup only after success.
        old_bytes = {n: (root / n).read_bytes() if (root / n).exists() else None
                     for n in names}
        moved = []
        try:
            for name in names:
                os.replace(staged[name], root / name)
                moved.append(name)
        except OSError:
            for name in moved:
                if old_bytes[name] is None:
                    (root / name).unlink(missing_ok=True)
                else:
                    _atomic_bytes(root / name, old_bytes[name])
            raise
    hashes = {name: _safe_hash(root / name) for name in names}
    report = {
        "schema": SCHEMA, "unit_id": unit["unit_id"],
        "input_sha256": inputs, "files": hashes,
        "pages": {"Lehrbuch.pdf": textbook_report["pages"],
                  "Arbeitsbuch.pdf": workbook_report["pages"]},
        "source_mode": unit["source_mode"],
        "academic_status": "HUMAN_REVIEW_PENDING",
    }
    _atomic_bytes(record_path, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    return {"status": "CREATED_OR_UPDATED", "products": list(names),
            "pages": report["pages"], "bytes": {n: (root / n).stat().st_size for n in names},
            "academic_status": report["academic_status"], "model_calls": 0}
