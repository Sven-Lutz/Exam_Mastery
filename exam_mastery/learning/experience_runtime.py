"""Content fingerprints for renderer code, templates and local dependencies.

No timestamps, absolute installation paths, network or model calls enter the
cache key. Missing optional font files are represented explicitly.
"""
import hashlib
from importlib.metadata import version
from pathlib import Path


def fingerprint(modules, assets=(), packages=(), settings=()):
    digest = hashlib.sha256()
    def add(label, data):
        # Length framing avoids ambiguous concatenations.
        for value in (label.encode(), data):
            digest.update(len(value).to_bytes(8, "big"))
            digest.update(value)
    add("fingerprint-implementation", Path(__file__).read_bytes())
    for module in modules:
        add(module.__name__, Path(module.__file__).read_bytes())
    for label, path in assets:
        path = Path(path)
        add(label, path.read_bytes() if path.is_file() else b"MISSING")
    for package in packages:
        add(package, version(package).encode())
    for label, value in settings:
        add(label, value.encode())
    return digest.hexdigest()


def fonts(node, specifications):
    return [(f"font/{package}/{variant}", node / "@fontsource" / package /
             "files" / f"{package}-latin-{variant}.woff2")
            for package, variants in specifications for variant in variants]
