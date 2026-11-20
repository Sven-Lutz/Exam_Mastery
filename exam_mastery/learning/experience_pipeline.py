"""Single CLI build command for the four canonical learning products.

Each publisher is independent, idempotent and offline. Preflight all existing
outputs before touching any so an unknown or modified file blocks the build.
A process interruption may leave a resumable partial build; no academic GO is
asserted without successful completion and explicit human review.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

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
    # A symlinked managed directory could redirect files outside the requested
    # publication directory, even when index.html itself is a regular file.
    for managed in (root / ".em-state", root / "Interaktiv"):
        if managed.is_symlink() or (managed.exists() and not managed.is_dir()):
            raise ValueError(f"Refusing nonregular managed directory {managed.name}")
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
    # Structural validity is not equivalent to publisher compatibility:
    # validate() intentionally allows NOT_APPLICABLE cards/interactions and
    # arbitrary model_ref identifiers for future domain adapters. The current
    # four-artifact builder must reject unsupported units *before* books or
    # Anki are written; later releases can implement explicit fallbacks.
    if not unit["cards"]:
        raise ValueError(
            "Four-product build not supported: no Anki cards. "
            "Valid learning units may omit cards, but the current APKG publisher cannot."
        )
    if not unit["interactions"]:
        raise ValueError(
            "Four-product build not supported: no interactive model. "
            "Valid learning units may omit interactions, but the current HTML publisher cannot."
        )
    from .interactive_reference import build_interaction
    for item in unit["interactions"]:
        # Compile trusted reference models and parameter variants without
        # producing files. Unknown models, unsorted inputs, non-finite values,
        # and invalid Parsons puzzles are rejected here, not after PDF export.
        build_interaction(item)

    return {"status": "PREFLIGHT_PASS", "existing_products": [
        key for key in expected if (root / key).is_file()
    ], "expected_products": list(expected), "model_calls": 0}


def _state_files(root):
    """Reject symlinks/special files, including nested publisher metadata."""
    root = Path(root)
    state = root / ".em-state"
    if state.is_symlink():
        raise ValueError("Refusing symlinked publisher state")
    if not state.exists():
        return []
    if not state.is_dir():
        raise ValueError("Refusing non-directory publisher state")
    files = []
    for item in state.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"Refusing symlinked publisher state entry {item}")
        if item.is_file():
            files.append(item.relative_to(root))
        elif not item.is_dir():
            raise ValueError(f"Refusing nonregular publisher state entry {item}")
    return sorted(files)


def _managed_files(root):
    """Four products plus internal publisher identity/integrity state."""
    return [Path(p) for p in PRODUCTS.values()] + _state_files(root)


def _snapshot(root):
    """Detect concurrent/manual changes before committing a complete build."""
    root = Path(root)
    files = {}
    for relative in _managed_files(root):
        candidate = root / relative
        if candidate.is_symlink():
            raise ValueError(f"Refusing symlinked managed path {relative}")
        if candidate.exists():
            if not candidate.is_file():
                raise ValueError(f"Refusing nonregular managed path {relative}")
            files[relative.as_posix()] = _hash(candidate)
    return files


def _prepare_previous(root, stage):
    """Copy already managed outputs and Anki/renderer identity state.

    Real publishers are still responsible for overwrite guards and stable note
    GUIDs. No original is moved or modified during preparation.
    """
    root, stage = Path(root), Path(stage)
    state = root / ".em-state"
    if state.is_dir():
        for relative in _state_files(root):
            source = root / relative
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for name in PRODUCTS.values():
        source = root / name
        if source.is_file():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def _commit_staged(root, stage, before):
    """Publish a fully prepared group with in-process rollback.

    This is NOT an atomic multi-file filesystem transaction. If the process is
    forcibly terminated during replacement, an incomplete group can remain.
    The unchanged original bytes are stored in a hidden recovery directory
    during commit; ordinary publisher errors never touch the visible files.
    """
    root, stage = Path(root), Path(stage)
    current = _snapshot(root)
    if current != before:
        raise ValueError("Managed outputs/state changed during build; refusing stale commit")
    staged = _snapshot(stage)
    required = {p.as_posix() for p in map(Path, PRODUCTS.values())}
    if not required.issubset(staged):
        raise RuntimeError("Cannot commit: incomplete staged learning products")
    missing_state = set(before) - set(staged)
    if missing_state:
        raise RuntimeError(
            "Cannot commit: staged publishers deleted managed files: " +
            ", ".join(sorted(missing_state))
        )
    changed = [name for name in sorted(staged)
               if staged[name] != before.get(name)]
    if not changed:
        return {"status": "UNCHANGED", "replaced_files": 0}
    backup = Path(tempfile.mkdtemp(prefix=".em-recovery-", dir=root))
    committed = []
    try:
        for relative in changed:
            if relative in before:
                target = backup / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / relative, target)
        # Retain old metadata until all new products are in place, so any
        # interruption fails closed during the next preflight.
        changed.sort(key=lambda p: (p.startswith(".em-state/"), p))
        for relative in changed:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / relative, target)
            committed.append(relative)
    except Exception as failure:
        failures = []
        for relative in reversed(committed):
            target = root / relative
            try:
                if relative in before:
                    os.replace(backup / relative, target)
                else:
                    target.unlink(missing_ok=True)
            except Exception as rollback_error:
                failures.append(f"{relative}: {rollback_error}")
        if failures:
            raise RuntimeError(
                f"ROLLBACK_FAILED; manual recovery preserved at {backup}: " +
                "; ".join(failures)
            ) from failure
        shutil.rmtree(backup)
        raise
    shutil.rmtree(backup)
    return {"status": "STAGED_COMMIT", "replaced_files": len(changed)}


def build(unit, output_dir):
    """Stage all four publishers before any visible product is changed.

    On a normal publisher error, the existing four products and their metadata
    remain byte-for-byte intact. Reuse of prior Anki state preserves semantic
    note identity. Process-kill atomicity remains a documented release blocker.
    """
    check = preflight(unit, output_dir)
    from . import experience_books, experience_anki, interactive_reference

    root = Path(output_dir)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("Refusing non-directory or symlinked publication root")
    original = _snapshot(root)
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".em-stage-", dir=root) as staging:
        stage = Path(staging)
        _prepare_previous(root, stage)
        books = experience_books.publish(unit, stage)
        anki = experience_anki.publish(unit, stage)
        interaction = interactive_reference.publish(unit, stage)
        produced = [
            *books["products"], "Anki.apkg", "Interaktiv/index.html",
        ]
        expected = list(PRODUCTS.values())
        if produced != expected or any(not (stage / p).is_file() for p in expected):
            raise RuntimeError("Incomplete staged four-product build; old release retained")
        # Verify hashes against the publishers' generated manifests BEFORE
        # installing anything user-visible.
        preflight(unit, stage)
        committed = _commit_staged(root, stage, original)

    return {
        "schema": "em-experience-build-v1",
        "status": "READY_FOR_TECHNICAL_REVIEW",
        "academic_status": "HUMAN_REVIEW_PENDING",
        "products": dict(zip(PRODUCTS, produced)),
        "changes": {"books": books["status"], "anki": anki["status"],
                    "interactive": interaction["status"]},
        "publication": {
            **committed,
            "guarantee": "STAGED_WITH_IN_PROCESS_ROLLBACK_NOT_CRASH_ATOMIC",
        },
        "model_calls": 0,
        "network_calls": 0,
        "source_mode": unit["source_mode"],
        "preflight": check["status"],
    }
