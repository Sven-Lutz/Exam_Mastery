"""Local Anki previews and a learner-owned feedback journal, independent of builds."""
import os
import re
import tempfile
from collections import Counter
from pathlib import Path

from ..anki_v2 import preview_html
from ..learning.publication_lock import publication_lock
from . import MasteryError, _read_json, _write_json, now, resolve_home
from .courses import _chapter, _sha_file, load_course

KINDS = ("unklar", "zu schwer", "doppelt", "Kontext fehlt", "fachlich falsch", "Abbildung vorschlagen")
SCHEMA = "mastery-card-feedback-v1"


def chapter_dir(root, slug, cid):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,70}", cid):
        raise MasteryError("Ungültiger Kapitelname")
    cdir, course = load_course(slug, root)
    _chapter(course, cid)
    return confined(root, cdir / "chapters" / cid)


def confined(root, path):
    if path.resolve() != path or not path.is_relative_to(root):
        raise MasteryError("Ungültiger lokaler Pfad")
    return path


def preview(root, slug, cid):
    chapter = chapter_dir(root, slug, cid)
    package = confined(root, chapter / "build" / "Anki.apkg")
    if not package.is_file():
        raise MasteryError("Zuerst das Kapitel bauen.")
    digest = _sha_file(package)
    cache = confined(root, chapter / "card-previews")
    dest = cache / digest
    with publication_lock(cache):
        index = _read_json(confined(root, dest / "index.json"))
        if index is None:
            with tempfile.TemporaryDirectory(dir=cache) as tmp:
                staging = Path(tmp) / "pages"
                cards = []
                preview_html(package, staging, card_index=cards)
                if _sha_file(package) != digest:
                    raise MasteryError("Kapitel wurde neu gebaut. Vorschau erneut öffnen.")
                index = {"package": digest, "cards": cards, "files": sorted(p.name for p in staging.iterdir())}
                _write_json(staging / "index.json", index)
                os.rename(staging, dest)
    return dest, index


def journal_path(root, slug, cid):
    return confined(root, root / "state" / "card-feedback" / slug / (cid + ".json"))


def report(root, slug, cid):
    journal = _read_json(journal_path(root, slug, cid)) or {"schema": SCHEMA, "course": slug, "chapter": cid, "events": []}
    events = journal["events"]
    counts = Counter(e["kind"] for e in events)
    affected = sorted({(e["key"], e["ordinal"]) for e in events})
    return {**journal, "counts": {k: counts[k] for k in KINDS},
            "affected": [{"key": k, "ordinal": o} for k, o in affected]}


def record(root, slug, cid, body):
    if not isinstance(body, dict) or set(body) != {"package", "key", "ordinal", "kind", "text"}:
        raise MasteryError("Ungültige Feedbackfelder")
    if (body["kind"] not in KINDS or type(body["ordinal"]) is not int or not isinstance(body["text"], str)
            or len(body["text"]) > 2000 or not isinstance(body["key"], str)):
        raise MasteryError("Ungültige Karte, Feedback-Art oder Textlänge")
    _, index = preview(root, slug, cid)
    if body["package"] != index["package"] or not any(
        (c["key"], c["ordinal"]) == (body["key"], body["ordinal"]) for c in index["cards"]
    ):
        raise MasteryError("Kartenversion geändert. Vorschau neu laden.")
    path = journal_path(root, slug, cid)
    with publication_lock(path.parent):
        journal = _read_json(path) or {"schema": SCHEMA, "course": slug, "chapter": cid, "events": []}
        journal["events"].append({**body, "at": now(), "revision": len(journal["events"]) + 1})
        _write_json(path, journal)
        return report(root, slug, cid)


def author_export(slug, cid, home=None):
    root = resolve_home(home)
    chapter = chapter_dir(root, slug, cid)
    target = chapter / "feedback.json"
    _write_json(target, report(root, slug, cid))
    return target
