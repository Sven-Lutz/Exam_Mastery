"""Two user-facing PDF books from the same canonical experience unit.

This adapter deliberately reuses the existing exam_mastery.typeset design,
MathJax/Chromium renderer and document model. It does not create a second
PDF engine, and it never pretends a synthetic fixture is an academic release.
"""
from __future__ import annotations

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


def book_model(unit):
    """Adapt an evidence-linked unit to the *existing* typeset.em-book-v1 model."""
    checked = validate(unit)
    if not checked["valid"]:
        raise ValueError("Invalid learning unit: " + "; ".join(checked["errors"]))
    from .experience_proof_checks import verify as verify_polynomial
    source_map = {s["id"]: s for s in unit["sources"]}
    claim_map = {c["id"]: c for c in unit["claims"]}
    synthetic = unit["source_mode"] == "synthetic"
    sections = []
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
                prefix = ("Synthetisch" if synthetic else
                          "Ungeprüft" if claim_map[claim_id]["evidence_status"] == "unverified"
                          else "Verifiziert (Statusangabe)")
                label = prefix + ": " + source["locator"]
                if label not in provenance:
                    provenance.append(label)
        section_blocks = [{"type": "lead" if i == 1 else "text", "md": item["content"],
                           "kc_ids": item["competency_ids"], "block_id": item["id"],
                           "prov": "didactic" if synthetic else "unconfirmed",
                           "src": "; ".join(provenance)}]
        if item.get("derivation"):
            derivation = item["derivation"]
            section_blocks.append({
                "type": "example", "label": "Herleitung · Schritt für Schritt",
                "title": derivation["title"], "given": derivation["given"],
                "steps": [[
                    step["statement"] + (
                        " " + verify_polynomial(step["math_check"])["latex"]
                        if "math_check" in step else ""
                    ),
                    step["justification"],
                ] for step in derivation["steps"]],
                "result": derivation["result"], "kc_ids": item["competency_ids"],
                "block_id": item["id"] + "/derivation",
                "prov": "didactic" if synthetic else "unconfirmed",
                "src": "; ".join(provenance),
            })
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
            section_blocks.append({
                "type": "misconception",
                "wrong": spec["wrong_example"],
                "right": spec["corrected_example"],
                "why": spec["explanation"],
                "kc_ids": spec["competency_ids"],
                "block_id": spec["id"],
                "prov": "didactic" if synthetic else "unconfirmed",
                "src": "; ".join(cited),
            })
        sections.append({
            "title": item.get("section_title") or
                     item["id"].rsplit("/", 1)[-1].replace("-", " ").capitalize(),
            "blocks": section_blocks,
        })
    items = []
    for index, task in enumerate(unit["assessments"], 1):
        rubric = [[x["criterion"], x["points"]] for x in task["rubric"]]
        items.append({
            "id": task["id"], "no": str(index), "prompt": task["prompt"],
            "stage_label": "transfer", "operation": task.get("operation") or "",
            "kc_keys": task["competency_ids"], "space": 26,
            "points": sum(x["points"] for x in task["rubric"]),
            "solution": {"answer": task["solution"], "rubric": rubric},
        })
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
        "figures": {}, "sections": sections,
        "stages": [{"title": "Selbstständige Anwendung und Transfer", "level": 4, "items": items}],
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
        ),
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
    for idx, stage in enumerate(book["stages"], 1):
        tag = f"aufgaben-{idx}"
        toc.append((2, tag, stage["title"]))
        parts = [f'<section class="stage{" first" if idx == 1 else ""}"><h2 id="{tag}">{typeset.inline(stage["title"])}</h2>']
        for task in stage["items"]:
            parts.append(typeset._item_html(d, task, solution=False))
        parts.append("</section>")
        sections.extend(parts)
    sections.append('<section style="break-before:page"><h2 id="loesungen">'
                    'Teil II · Vollständige Musterlösungen</h2>'
                    '<p>Die angegebenen Bewertungskriterien sind Teil der Übung '
                    'und keine offiziellen Prüfungsvorgaben.</p></section>')
    toc.append((1, "loesungen", "Teil II · Vollständige Musterlösungen"))
    for idx, stage in enumerate(book["stages"], 1):
        tag = f"loesungen-{idx}"
        toc.append((2, tag, stage["title"] + " · Lösungen"))
        parts = [f'<section class="stage{" first" if idx == 1 else ""}"><h2 id="{tag}">{typeset.inline(stage["title"])}</h2>']
        for task in stage["items"]:
            # The same semantic task receives a distinct PDF anchor for the solution.
            copy = dict(task, id="loesung-" + task["id"])
            parts.append(typeset._item_html(d, copy, solution=True, space=False))
        parts.append("</section>")
        sections.extend(parts)
    body = (
        typeset._cover(book, "Arbeitsbuch", "Aufgaben und vollständige Musterlösungen")
        + typeset._toc(toc) + "".join(sections)
    )
    return body, toc


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
    from . import experience_books, experience_proof_checks
    runtime = fingerprint(
        [experience_books, experience_proof_checks, typeset, typeset.figures_svg],
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
