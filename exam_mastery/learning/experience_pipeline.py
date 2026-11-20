"""Single CLI build command for the four canonical learning products.

Each publisher is independent, idempotent and offline. Preflight all existing
outputs before touching any so an unknown or modified file blocks the build.
A process interruption may leave a resumable partial build; no academic GO is
asserted without successful completion and explicit human review.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .experience import PRODUCTS, validate


def _hash(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _load(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def preflight(unit, output_dir):
    """Check all four existing targets against *their* publisher manifests."""
    valid = validate(unit)
    if not valid["valid"]:
        raise ValueError("Invalid learning unit: " + "; ".join(valid["errors"]))
    root = Path(output_dir)
    suffix = hashlib.sha256(unit["unit_id"].encode()).hexdigest()[:12]
    records = {
        "books": _load(root / ".em-state" / ("books-" + suffix + ".json")),
        "anki": _load(root / ".em-state" / ("anki-" + suffix + ".json")),
        "interactive": _load(root / ".em-state" / ("interactive-" + suffix + ".json")),
    }
    expected = {
        "Lehrbuch.pdf": (records["books"] or {}).get("files", {}).get("Lehrbuch.pdf"),
        "Arbeitsbuch.pdf": (records["books"] or {}).get("files", {}).get("Arbeitsbuch.pdf"),
        "Anki.apkg": (records["anki"] or {}).get("package_sha256"),
        "Interaktiv/index.html": (records["interactive"] or {}).get("sha256"),
    }
    for relative, checksum in expected.items():
        path = root / relative
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Refusing to overwrite nonregular output {relative}")
            if not checksum:
                raise ValueError(f"Refusing to overwrite unmanaged {relative}")
            if _hash(path) != checksum:
                raise ValueError(f"Refusing to overwrite manually modified {relative}")
    return {"status": "PREFLIGHT_PASS", "existing_products": [
        key for key in expected if (root / key).is_file()
    ], "expected_products": list(expected), "model_calls": 0}


def build(unit, output_dir):
    """Render four products, preserving the existing domain-specific pipelines."""
    check = preflight(unit, output_dir)
    from . import experience_books, experience_anki, interactive_reference

    # Reusable publishers skip unchanged products without rerendering.
    books = experience_books.publish(unit, output_dir)
    anki = experience_anki.publish(unit, output_dir)
    interaction = interactive_reference.publish(unit, output_dir)
    produced = [
        *books["products"], "Anki.apkg", "Interaktiv/index.html",
    ]
    expected = ["Lehrbuch.pdf", "Arbeitsbuch.pdf", "Anki.apkg", "Interaktiv/index.html"]
    if produced != expected or any(not (Path(output_dir) / p).is_file() for p in expected):
        raise RuntimeError("Incomplete four-product build; release withheld")
    return {
        "schema": "em-experience-build-v1", "status": "READY_FOR_TECHNICAL_REVIEW",
        "academic_status": "HUMAN_REVIEW_PENDING", "products": dict(zip(PRODUCTS, produced)),
        "changes": {"books": books["status"], "anki": anki["status"],
                    "interactive": interaction["status"]},
        "model_calls": 0, "network_calls": 0,
        "source_mode": unit["source_mode"], "preflight": check["status"],
    }
