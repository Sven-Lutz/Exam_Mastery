"""Single CLI build command for the four canonical learning products.

Each publisher is independent, idempotent and offline. Preflight all existing
outputs before touching any so an unknown or modified file blocks the build.
A process interruption may leave a resumable partial build; no academic GO is
asserted without successful completion and explicit human review.
"""
from __future__ import annotations

from .publication_lock import locked_publisher

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
    if list(Path(output_dir).glob(".em-recovery-*")):
        raise ValueError("Pending publication recovery; run experience recover before rebuilding")
    valid = validate(unit)
    if not valid["valid"]:
        raise ValueError("Invalid learning unit: " + "; ".join(valid["errors"]))
    root = Path(output_dir)
    # A symlinked managed directory could redirect files outside the requested
    # publication directory, even when index.html itself is a regular file.
    for managed in (root / ".em-state", root / "Interaktiv"):
        if managed.is_symlink() or (managed.exists() and not managed.is_dir()):
            raise ValueError(f"Refusing nonregular managed directory {managed.name}")
    _snapshot(root)  # Reject redirected metadata before reading any manifest.
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
    for managed in (root, root / ".em-state", root / "Interaktiv"):
        if managed.is_symlink() or (managed.exists() and not managed.is_dir()):
            raise ValueError(f"Refusing nonregular or redirected output directory {managed}")
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


@locked_publisher
def recover(output_dir):
    """Explicitly restore a process-interrupted publication, never user edits.

    The journal and every recovery source/live destination are checked before
    the first write. Recovery copies backups rather than consuming them, so a
    second interruption can be retried. This covers process termination, not
    power-loss durability or hostile concurrent filesystem mutation.
    """
    root = Path(output_dir)
    current = _snapshot(root)
    pending = sorted(root.glob(".em-recovery-*"))
    if not pending:
        return {"status": "NO_RECOVERY_NEEDED"}
    if len(pending) != 1:
        raise ValueError("Multiple recovery directories require manual inspection")
    backup = pending[0]
    if backup.is_symlink() or not backup.is_dir():
        raise ValueError("Refusing redirected recovery directory")
    journal = backup / "transaction.json"
    if journal.is_symlink() or not journal.is_file():
        raise ValueError("Missing or redirected recovery journal; manual inspection required")
    record = _load(journal)
    if not isinstance(record, dict) or set(record) != {"schema", "before", "after"} or record["schema"] != "em-publication-recovery-v1":
        raise ValueError("Invalid recovery journal")
    before, after = record["before"], record["after"]
    for manifest in (before, after):
        if not isinstance(manifest, dict):
            raise ValueError("Invalid recovery manifest")
        for name, checksum in manifest.items():
            path = Path(name)
            allowed = name in PRODUCTS.values() or (
                len(path.parts) > 1 and path.parts[0] == ".em-state")
            if (not allowed or path.is_absolute() or ".." in path.parts
                    or path.as_posix() != name or not isinstance(checksum, str)
                    or len(checksum) != 64 or any(c not in "0123456789abcdef" for c in checksum)):
                raise ValueError("Invalid recovery path or checksum")
    if not set(before).issubset(after):
        raise ValueError("Invalid recovery file set")
    if set(current) - set(after):
        raise ValueError("Managed state modified after interruption")
    for name in after:
        live_hash = current.get(name)
        if live_hash not in {before.get(name), after[name]}:
            raise ValueError("Managed output modified after interruption: " + name)
        if name in before and live_hash is None:
            raise ValueError("Managed output modified after interruption: " + name)
    for name, checksum in before.items():
        source = backup / name
        if any(parent.is_symlink() for parent in source.parents if parent != root.parent):
            raise ValueError("Refusing symlinked recovery source")
        if not source.is_file() or source.is_symlink() or _hash(source) != checksum:
            raise ValueError("Recovery backup modified or missing: " + name)
    # Keep the journal and all original backups intact until restoration ends.
    for name in sorted(after, key=lambda p: (p.startswith(".em-state/"), p)):
        target = root / name
        if current.get(name) == before.get(name):
            continue
        if name not in before:
            target.unlink()
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = backup / "restore.tmp"
            shutil.copy2(backup / name, temporary)
            os.replace(temporary, target)
    if _snapshot(root) != before:
        raise RuntimeError("Recovery verification failed; backups retained")
    shutil.rmtree(backup)
    return {"status": "RECOVERED_PREVIOUS_RELEASE", "restored_files": len(before)}


def _commit_staged(root, stage, before):
    """Publish a fully prepared group with rollback and explicit crash recovery.

    This is NOT an atomic multi-file filesystem transaction. If the process is
    forcibly terminated during replacement, an incomplete group can remain.
    Original bytes and a hash journal remain in a hidden recovery directory
    until commit completes; recover() can restore a process-interrupted group.
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
        for relative in sorted(before):
            if relative in before:
                target = backup / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / relative, target)
        journal = backup / "transaction.json"
        journal.write_text(json.dumps({
            "schema": "em-publication-recovery-v1", "before": before, "after": staged,
        }, sort_keys=True), encoding="utf-8")
        # All backups and the closed journal exist before the first replacement.
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
                    temporary = backup / "restore.tmp"
                    shutil.copy2(backup / relative, temporary)
                    os.replace(temporary, target)
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


@locked_publisher
def build(unit, output_dir):
    """Stage all four publishers before any visible product is changed.

    On a normal publisher error, the existing four products and their metadata
    remain byte-for-byte intact. Reuse of prior Anki state preserves semantic
    note identity. Process interruption requires explicit recovery before rebuild;
    concurrent writers and power-loss atomicity are not guaranteed.
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
            "guarantee": "STAGED_WITH_EXPLICIT_PROCESS_RECOVERY_NOT_CRASH_ATOMIC",
        },
        "model_calls": 0,
        "network_calls": 0,
        "source_mode": unit["source_mode"],
        "preflight": check["status"],
    }
