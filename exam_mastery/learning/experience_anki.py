"""One-product Anki publishing adapter, reusing the existing Anki v2 engine.

No scheduler and no access to a user's Anki collection. Imports are handled by
Anki itself. Persistent state remains separate from the visible deck package.
"""
from __future__ import annotations

from .publication_lock import locked_publisher

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .. import anki_v2
from .experience import validate


def _hash_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".em-anki-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@locked_publisher
def publish(unit, output_dir, state_dir=None):
    """Create or update ONLY Anki.apkg in the user-visible output directory.

    Refuses to overwrite unknown files or files modified since the last
    managed export. Anki's stable note GUIDs and scheduling remain untouched.
    """
    check = validate(unit)
    if not check["valid"]:
        raise ValueError("Invalid learning unit: " + "; ".join(check["errors"]))
    from .experience_math import project
    unit = project(unit)
    cards = []
    claims = {claim["id"]: claim for claim in unit.get("claims", [])}
    sources = {source["id"]: source for source in unit.get("sources", [])}
    for original in unit.get("cards", []):
        card = dict(original)
        references = []
        for claim_id in card.get("claim_ids", []):
            for source_id in claims[claim_id]["source_refs"]:
                locator = sources[source_id]["locator"]
                if locator not in references:
                    references.append(locator)
        if references:
            explicit_source = card.get("source", "").strip()
            card["source"] = "; ".join(([explicit_source] if explicit_source else []) + references)
        cards.append(card)
    if not cards:
        raise ValueError("No retrieval cards: refusing to publish an empty Anki package")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    state = Path(state_dir) if state_dir is not None else output / ".em-state"
    state.mkdir(parents=True, exist_ok=True)
    unit_id = unit["unit_id"]
    digest_id = hashlib.sha256(unit_id.encode()).hexdigest()[:12]
    tokens = unit_id.split("/")
    course = re.sub(r"[^a-z0-9_-]", "-", tokens[0])
    chapter = re.sub(r"[^a-z0-9_-]", "-", "-".join(tokens[1:])) + "-" + digest_id[:8]
    # stable across title and content changes
    deck = "Exam Mastery::" + unit["title"]
    from .experience_runtime import fingerprint as runtime_fingerprint, fonts
    from . import experience_anki
    from ..typeset import NODE
    runtime = runtime_fingerprint(
        [experience_anki, anki_v2],
        assets=fonts(NODE, [("source-sans-3", ["400-normal", "600-normal", "700-normal"])]),
        packages=["anki"], settings=[("css", anki_v2.CSS),
            ("basic_q", anki_v2.BASIC_Q), ("basic_a", anki_v2.BASIC_A),
            ("cloze_q", anki_v2.CLOZE_Q), ("cloze_a", anki_v2.CLOZE_A)])
    fingerprint = hashlib.sha256(json.dumps(
        {"cards": cards, "course": course, "chapter": chapter, "deck": deck, "notetype": "v2", "runtime": runtime},
        sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    package = output / "Anki.apkg"
    manifest = state / ("anki-" + digest_id + ".json")
    old = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else None
    if package.exists():
        if not old:
            raise ValueError("Refusing to overwrite an unmanaged Anki.apkg")
        if _hash_file(package) != old.get("package_sha256"):
            raise ValueError("Refusing to overwrite a manually modified Anki.apkg")
    if old and package.exists() and old.get("fingerprint") == fingerprint:
        return {"status": "UNCHANGED", "package": str(package),
                "package_sha256": old["package_sha256"], "model_calls": 0,
                "user_collection_touched": False}
    with tempfile.TemporaryDirectory(dir=output, prefix=".em-anki-build-") as work:
        report = anki_v2.build_deck(
            cards, deck, course, chapter, Path(work), state_dir=state)
        source = Path(report["package"])
        pkg_hash = _hash_file(source)
        os.replace(source, package)  # temp folder is on the same filesystem
    record = {
        "schema": "em-experience-anki-v1", "unit_id": unit_id,
        "fingerprint": fingerprint, "package_sha256": pkg_hash,
        "note_count": report["notes"], "card_count": report["cards"],
        "source_mode": unit["source_mode"],
        "academic_status": "HUMAN_REVIEW_PENDING",
    }
    _write_atomic(manifest, (json.dumps(record, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
    return {"status": "CREATED_OR_UPDATED", "package": str(package),
            "notes": report["notes"], "cards": report["cards"],
            "update_delta": report["update_delta"], "package_sha256": pkg_hash,
            "model_calls": 0, "user_collection_touched": False,
            "academic_status": "HUMAN_REVIEW_PENDING"}
