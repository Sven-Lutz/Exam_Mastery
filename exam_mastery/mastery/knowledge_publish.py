"""Publish one Markdown tree with an atomic directory exchange on macOS/Linux."""
import ctypes
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from ..learning.publication_lock import publication_lock
from . import MasteryError
from .courses import _sha_file

MANIFEST = ".mastery-manifest.json"


def digest(data):
    if isinstance(data, Path):
        return _sha_file(data)
    return hashlib.sha256(data).hexdigest()


def _snapshot(root):
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise MasteryError("Verknüpfung oder Sonderdatei im generierten Bereich")
        if path.is_file() and path != root / MANIFEST:
            result[path.relative_to(root).as_posix()] = digest(path)
    return result


def _install(stage, target):
    if not target.exists():
        os.rename(stage, target)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        rc = libc.renamex_np(os.fsencode(stage), os.fsencode(target), 2)
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rc = libc.renameat2(-100, os.fsencode(stage), -100, os.fsencode(target), 2)
    else:
        raise MasteryError("Dieses System unterstützt keinen atomaren Verzeichnistausch.")
    if rc:
        raise OSError(ctypes.get_errno(), "Atomarer Verzeichnistausch fehlgeschlagen")


def publish(vault, files):
    target = vault / "Mastery"
    if vault.resolve() != vault:
        raise MasteryError("Umgeleiteter Exportpfad")
    with publication_lock(vault):
        if target.is_symlink() or (vault / "Mastery-Notizen").is_symlink():
            raise MasteryError("Umgeleiteter Vault-Bereich")
        (vault / "Mastery-Notizen").mkdir(exist_ok=True)
        manifest = target / MANIFEST
        if target.exists() and (manifest.is_symlink() or not manifest.is_file()):
            raise MasteryError("Vorhandener Ordner ohne Mastery-Manifest")
        previous = json.loads(manifest.read_text())["hashes"] if target.exists() else {}
        actual = _snapshot(target)
        expected = {name: digest(data) for name, data in files.items()}
        conflicts = sorted(name for name in previous.keys() | actual.keys() if previous.get(name) != actual.get(name))
        if conflicts:
            # The active graph stays complete. Save proposals outside it without replacing earlier proposals.
            folder = vault / "Konflikte"
            if folder.is_symlink():
                raise MasteryError("Umgeleiteter Konfliktordner")
            folder.mkdir(exist_ok=True)
            for name in conflicts:
                if name in files:
                    candidate = folder / (Path(name).name + "." + expected[name][:16] + ".conflict")
                    try:
                        with candidate.open("xb") as f:
                            data = files[name]
                            if isinstance(data, Path):
                                with data.open("rb") as src:
                                    shutil.copyfileobj(src, f)
                            else:
                                f.write(data)
                    except FileExistsError:
                        pass
            raise MasteryError("Exportkonflikt – Original erhalten: " + ", ".join(conflicts))
        if actual == expected and target.exists():
            return
        # A killed process can leave a private staging directory outside the vault.
        # Before exchange readers see the old graph, after exchange the complete new one.
        with tempfile.TemporaryDirectory(prefix=".mastery-export-", dir=vault.parent) as tmp:
            stage = Path(tmp) / "tree"
            stage.mkdir()
            for name, data in files.items():
                path = stage / name
                path.parent.mkdir(parents=True, exist_ok=True)
                if actual.get(name) == expected[name]:
                    os.link(target / name, path)
                elif isinstance(data, Path):
                    shutil.copyfile(data, path)
                    if digest(path) != expected[name]:
                        raise MasteryError("Produkt während des Exports verändert")
                else:
                    path.write_bytes(data)
            (stage / MANIFEST).write_text(json.dumps({"schema": 1, "hashes": expected}, sort_keys=True))
            if _snapshot(target) != actual:
                raise MasteryError("Exportdateien während der Veröffentlichung verändert")
            _install(stage, target)
