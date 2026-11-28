"""Optional, permission-gated Anki statistics from an export the learner made themselves (R8-POL-12, standard §5.6).

Mastery never opens the live Anki collection. The learner exports a deck package (.apkg, "Planungsdaten einschließen")
or a collection package (.colpkg) in Anki and hands that one file to Mastery after an explicit consent click. The file
is unpacked into a private temporary directory, read with SQLite in read-only mode and the temporary copy is deleted.
Only cards of Mastery decks ("Exam Mastery::...") are reported, with descriptive counts: reviews, lapses, current
interval, queue. These are Anki scheduling data, never evidence of competence; Anki/FSRS remains the only scheduler.

Supported containers: legacy SQLite (collection.anki21 / collection.anki2, Anki's "support older versions" export) for
.apkg and .colpkg; the current compressed format (collection.anki21b) for .apkg through the anki Python library, by
importing into a throwaway collection inside the temporary directory. Not supported: compressed .colpkg without the
legacy option, CSV/text exports (they carry no review history).
"""
from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

SCHEMA = "mastery-anki-stats-v1"
LABEL = "Anki-Planungsdaten, kein Kompetenznachweis"
MAX_FILE_BYTES = 30_000_000
MAX_UNPACKED_BYTES = 400_000_000
MASTERY_DECK = re.compile(r"^(Exam Mastery|Mastery)(::|$)")
QUEUE = {-3: "buried", -2: "buried", -1: "suspended", 0: "new", 1: "learning", 2: "review", 3: "learning", 4: "preview"}
TAG = re.compile(r"<[^>]*>")


class AnkiStatsError(ValueError):
    pass


def _iso_ms(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _front(flds):
    text = TAG.sub(" ", (flds or "").split("\x1f", 1)[0]).replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:80] + ("…" if len(text) > 80 else "")


def _deck_names(db):
    tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    if "decks" in tables:
        return {did: name.replace("\x1f", "::") for did, name in db.execute("select id, name from decks")}
    raw = db.execute("select decks from col").fetchone()[0]
    return {int(k): v["name"] for k, v in json.loads(raw).items()}


def _read_db(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True)
    try:
        names = _deck_names(db)
        mastery = {did for did, name in names.items() if MASTERY_DECK.match(name)}
        total = db.execute("select count() from cards").fetchone()[0]
        reviews = {}
        for cid, rid, ease, rtype in db.execute("select cid, id, ease, type from revlog"):
            if ease and ease > 0 and rtype != 4:
                reviews.setdefault(cid, []).append(rid)
        cards = []
        for cid, did, odid, ord_, queue, ivl, lapses, guid, flds in db.execute(
                "select c.id, c.did, c.odid, c.ord, c.queue, c.ivl, c.lapses, n.guid, n.flds "
                "from cards c join notes n on n.id = c.nid order by c.id"):
            deck = did if did in mastery else odid if odid in mastery else None
            if deck is None:
                continue
            rs = sorted(reviews.get(cid, []))
            cards.append({"deck": names[deck], "note_guid": guid, "ord": ord_, "front": _front(flds),
                          "queue": QUEUE.get(queue, "unknown"), "reviews": len(rs), "lapses": lapses,
                          "interval_days": ivl if ivl > 0 else 0,
                          "first_review": _iso_ms(rs[0]) if rs else None, "last_review": _iso_ms(rs[-1]) if rs else None})
    finally:
        db.close()
    decks = {}
    for c in cards:
        d = decks.setdefault(c["deck"], {"name": c["deck"], "cards": 0, "reviews": 0, "lapses": 0})
        d["cards"] += 1
        d["reviews"] += c["reviews"]
        d["lapses"] += c["lapses"]
    return {"decks": [decks[k] for k in sorted(decks)], "cards": cards, "other_cards_ignored": total - len(cards)}


def _safe_extract(zf, name, target):
    info = zf.getinfo(name)
    if info.file_size > MAX_UNPACKED_BYTES:
        raise AnkiStatsError("Die Sammlung in der Datei ist zu groß.")
    out = Path(target) / PurePosixPath(name).name
    with zf.open(info) as src, open(out, "wb") as dst:
        copied = 0
        while chunk := src.read(1 << 20):
            copied += len(chunk)
            if copied > MAX_UNPACKED_BYTES:
                raise AnkiStatsError("Die Sammlung in der Datei ist zu groß.")
            dst.write(chunk)
    return out


def _via_anki_library(package, tmp):
    try:
        from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
    except ImportError as exc:
        raise AnkiStatsError("Dieses Exportformat ist komprimiert. Bitte in Anki beim Export zusätzlich "
                             "„Unterstützung für ältere Anki-Versionen“ ankreuzen und die neue Datei wählen.") from exc
    path = Path(tmp) / "throwaway.anki2"
    col = Collection(str(path))
    try:
        col.import_anki_package(ImportAnkiPackageRequest(package_path=str(package),
                                                         options=ImportAnkiPackageOptions(with_scheduling=True)))
    finally:
        col.close()
    return path


def parse_export(data, filename="export.apkg"):
    """Descriptive statistics of the Mastery decks in an Anki export (bytes). Reads only a temporary copy."""
    suffix = PurePosixPath(str(filename)).suffix.lower()
    if suffix not in (".apkg", ".colpkg"):
        raise AnkiStatsError("Bitte eine Anki-Exportdatei (.apkg oder .colpkg) wählen.")
    if len(data) > MAX_FILE_BYTES:
        raise AnkiStatsError("Die Datei ist größer als 30 MB. Bitte nur die Mastery-Stapel ohne Medien exportieren.")
    with tempfile.TemporaryDirectory(prefix="mastery-anki-stats-") as tmp:
        package = Path(tmp) / ("export" + suffix)
        package.write_bytes(data)
        try:
            zf = zipfile.ZipFile(package)
        except zipfile.BadZipFile as exc:
            raise AnkiStatsError("Keine Anki-Exportdatei (kein gültiges Paket).") from exc
        with zf:
            names = set(zf.namelist())
            if sum(i.file_size for i in zf.infolist()) > MAX_UNPACKED_BYTES:
                raise AnkiStatsError("Die Datei entpackt zu groß.")
            if "collection.anki21b" in names:
                if suffix != ".apkg":
                    raise AnkiStatsError("Komprimierte Sammlungspakete (.colpkg) liest Mastery noch nicht. Bitte die "
                                         "Mastery-Stapel als .apkg mit Planungsdaten exportieren.")
                kind, db = "anki21b", _via_anki_library(package, tmp)
            elif "collection.anki21" in names:
                kind, db = "anki21", _safe_extract(zf, "collection.anki21", tmp)
            elif "collection.anki2" in names:
                kind, db = "anki2", _safe_extract(zf, "collection.anki2", tmp)
            else:
                raise AnkiStatsError("In der Datei ist keine Anki-Sammlung.")
        try:
            stats = _read_db(db)
        except sqlite3.DatabaseError as exc:
            raise AnkiStatsError("Die Anki-Sammlung in der Datei ist nicht lesbar.") from exc
    return {"schema": SCHEMA, "label": LABEL,
            "imported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "file": {"name": PurePosixPath(str(filename)).name[:120], "format": suffix[1:], "collection": kind},
            "not_measured": "Wiederholungen, Lapses und Intervalle sind Planungsdaten von Anki/FSRS. Sie zeigen, wie oft "
                            "und mit welchem Ergebnis Karten wiederholt wurden – nicht, ob Sie eine Kompetenz beherrschen.",
            **stats}


def store(root, stats):
    from . import _write_json
    _write_json(Path(root) / "anki-stats" / "latest.json", stats)


def load(root):
    path = Path(root) / "anki-stats" / "latest.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def forget(root):
    path = Path(root) / "anki-stats" / "latest.json"
    if path.exists():
        path.unlink()
        return True
    return False
