"""Mastery V1: one local learning library (build, status, export). Offline, deterministic, no model calls.

The library lives in MASTERY_HOME (default ~/Mastery), never inside the engine repository. It is described by
data, not code: the public spec `library.json` next to this file plus an optional private spec
MASTERY_HOME/library-spec.local.json (units from paths outside the repository). Each unit gets the four products of
`learning.experience_pipeline` plus its practice workbenches (`learning.render`). Learner state stays in the browser
(localStorage of http://127.0.0.1:<port>); the local server may receive a validated copy for backup (server.py).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..learning.publication_lock import publication_lock

PKG = Path(__file__).resolve().parent
ENGINE = PKG.parent
REPO = ENGINE.parent
TEMPLATES = ENGINE / "templates"
DEFAULT_PORT = 8765
SPEC_SCHEMA = "mastery-library-spec-v1"
LIBRARY_SCHEMA = "mastery-library-v1"
STATE_SCHEMA = "mastery-state-v1"
BACKUP_SCHEMA = "mastery-backup-v1"
STORE_CONTEXT = "mastery"          # workbench storage namespace: localStorage em-tutor-v1, key "mastery|<track id>"
STORAGE_KEYS = ("em-tutor-v1", "em-practice-v1")
MAX_STATE_BYTES = 4_000_000
MAX_EVENTS = 20_000
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
ASSETS = ("em_tokens.css", "mastery_home.css", "em_tutor.js", "mastery_home.js")


class MasteryError(ValueError):
    pass


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ------------------------------------------------------------------ location and repository guard

def _inside_engine_checkout(path):
    for anc in (path, *path.parents):
        if (anc / "exam_mastery").is_dir() and (anc / "pyproject.toml").is_file():
            return anc
    if path == ENGINE or ENGINE in path.parents:
        return ENGINE
    return None


def _private_output_forbidden(path):
    return _inside_engine_checkout(path) or any((parent / ".git").exists() for parent in (path, *path.parents))


def resolve_home(home=None):
    """MASTERY_HOME (or ~/Mastery). Refuses any location inside an engine checkout or the installed package."""
    raw = home or os.environ.get("MASTERY_HOME") or (Path.home() / "Mastery")
    path = Path(raw).expanduser().resolve()
    if _private_output_forbidden(path):
        raise MasteryError("Refusing to write the Mastery library into a Git checkout or the engine package; "
                           "set MASTERY_HOME to a folder outside it (default ~/Mastery).")
    if path.exists() and not path.is_dir():
        raise MasteryError("MASTERY_HOME exists and is not a directory")
    return path


def _guard_output(path):
    path = Path(path).expanduser().resolve()
    if _private_output_forbidden(path):
        raise MasteryError("Refusing to write learner data into a Git checkout or the engine package.")
    return path


# ------------------------------------------------------------------ spec

def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def _write_json(path, obj):
    path = Path(path)
    _guard_output(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".mastery-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(obj, handle, ensure_ascii=False, indent=1, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _check_entry(entry, private):
    if not isinstance(entry, dict) or not SLUG.match(str(entry.get("slug", ""))) or not isinstance(entry.get("unit"), str):
        raise MasteryError("Invalid unit entry in library spec (slug [a-z0-9-], unit path required)")
    tracks = entry.get("tracks", [])
    if not isinstance(tracks, list) or not all(isinstance(t, dict) and (t.get("id") or t.get("path")) for t in tracks):
        raise MasteryError(f"Invalid tracks for unit {entry['slug']}")
    return dict(entry, private=private)


def load_spec(root):
    spec = _read_json(PKG / "library.json")
    if not spec or spec.get("schema") != SPEC_SCHEMA:
        raise MasteryError("Missing or invalid public library spec")
    units = [_check_entry(e, False) for e in spec["units"]]
    local = _read_json(Path(root) / "library-spec.local.json")
    if local:
        if local.get("schema") != SPEC_SCHEMA:
            raise MasteryError("Invalid private library spec")
        units += [_check_entry(e, True) for e in local.get("units", [])]
    slugs = [u["slug"] for u in units]
    if len(slugs) != len(set(slugs)):
        raise MasteryError("Duplicate unit slug in library spec")
    return units


def _unit_path(entry):
    path = Path(entry["unit"]).expanduser()
    if not path.is_absolute():
        if entry["private"]:
            raise MasteryError("Private units need an absolute path")
        path = REPO / path
    if not path.is_file():
        raise MasteryError(f"Unit file for '{entry['slug']}' not found" + ("" if entry["private"] else
                           " (run Mastery from an engine checkout: bin/mastery)"))
    return path


def _load_unit(entry):
    from ..learning.experience import validate
    unit = json.loads(_unit_path(entry).read_text(encoding="utf-8"))
    report = validate(unit)
    if not report["valid"]:
        raise MasteryError(f"Invalid learning unit '{entry['slug']}': " + "; ".join(report["errors"][:5]))
    return unit


def _load_track(ref):
    from ..learning import tracks as TR
    if ref.get("path"):
        track = json.loads(Path(ref["path"]).expanduser().read_text(encoding="utf-8"))
    else:
        found = [t for t in TR.all_tracks() if t["id"] == ref["id"]]
        if not found:
            raise MasteryError(f"Unknown practice track {ref['id']}")
        track = found[0]
    TR.validate(track)
    return track


def engine_fingerprint():
    """Hash of every engine file the products depend on (code, templates, runtime assets)."""
    h = hashlib.sha256()
    for path in sorted(ENGINE.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc"}:
            h.update(path.relative_to(ENGINE).as_posix().encode())
            h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


def _canon(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def plan(root):
    """Desired state of the library: every unit with its tracks and content hash."""
    engine = engine_fingerprint()
    out = []
    for entry in load_spec(root):
        unit = _load_unit(entry)
        tracks = [(ref, _load_track(ref)) for ref in entry.get("tracks", [])]
        content = hashlib.sha256(_canon({
            "entry": {k: v for k, v in entry.items() if k != "unit"}, "unit": unit,
            "tracks": [t for _, t in tracks], "engine": engine}).encode()).hexdigest()
        out.append({"entry": entry, "unit": unit, "tracks": tracks, "content_hash": content})
    return out


# ------------------------------------------------------------------ build

def _anki_state(unit_dir):
    state = {}
    for path in sorted((Path(unit_dir) / ".em-state").glob(".anki-v2-state-*.json")):
        data = _read_json(path) or {}
        for key, digest in (data.get("hashes") or {}).items():
            state[key] = (digest, (data.get("mods") or {}).get(key))
    return state


def _anki_report(unit_dir, unit, before, after, status):
    report_path = Path(unit_dir) / "anki_report.json"
    old = _read_json(report_path) or {}
    restamped = sorted(k for k in after if before.get(k, (None, None))[1] != after[k][1])
    delta = {"new": sorted(set(after) - set(before)),
             "changed": sorted(k for k in after if k in before and before[k][0] != after[k][0]),
             "unchanged": sorted(k for k in after if k in before and before[k][0] == after[k][0]),
             "retirement_candidates": sorted(set(before) - set(after)), "automatic_deletion": False}
    history = list(old.get("history", []))
    if restamped:
        history = (history + [{"built_at": now(), "restamped": restamped}])[-10:]
    report = {"schema": "mastery-anki-report-v1", "built_at": now(), "deck": "Exam Mastery::" + unit["title"],
              "notes": len(after), "package_status": status, "restamped": restamped, "update_delta": delta,
              "history": history, "import": "Anki: Datei > Importieren; Voreinstellung 'aktualisieren, falls neuer' lassen. "
              "Das Paket enthält keine Planungsdaten; Ihre Wiederholungshistorie bleibt erhalten."}
    _write_json(report_path, report)
    return report


def _slug_task(task_id):
    return re.sub(r"[^a-z0-9_-]", "-", task_id)


def _build_unit(root, item, log):
    from ..learning import experience_pipeline, render
    from ..learning.experience_adaptation import track_for_unit
    from ..learning.experience_evidence import assessment_revision
    entry, unit = item["entry"], item["unit"]
    unit_dir = Path(root) / "units" / entry["slug"]
    if unit_dir.is_symlink():
        raise MasteryError("Refusing symlinked unit directory")
    before = _anki_state(unit_dir)
    started = time.monotonic()
    result = experience_pipeline.build(unit, unit_dir)
    after = _anki_state(unit_dir)
    anki = _anki_report(unit_dir, unit, before, after, result["changes"]["anki"])
    tracks = []
    for ref, track in item["tracks"]:
        page = render.write(track, unit_dir / "tracks", context=STORE_CONTEXT, back="../../../index.html",
                            back_label="Mastery – Startseite")
        base = f"units/{entry['slug']}/tracks/{page.name}"
        tracks.append({"id": track["id"], "title": track["title"], "objective": track["objective"],
                       "relation": ref.get("relation", "practice"), "label": ref.get("label") or track["title"],
                       "href": base, "json": base[:-5] + ".json", "store_key": f"{STORE_CONTEXT}|{track['id']}"})
    log(f"  {entry['slug']}: Produkte {result['publication']['status']}, Anki {result['changes']['anki']}, "
        f"{len(anki['restamped'])} Karten neu gestempelt ({time.monotonic() - started:.1f} s)")
    prefix = f"units/{entry['slug']}/"
    return {
        "slug": entry["slug"], "title": unit["title"], "unit_id": unit["unit_id"], "private": entry["private"],
        "source_mode": unit["source_mode"], "academic_status": result["academic_status"],
        "content_hash": item["content_hash"], "built_at": now(),
        "products": {"textbook": prefix + "Lehrbuch.pdf", "workbook": prefix + "Arbeitsbuch.pdf",
                     "anki": prefix + "Anki.apkg", "interactive": prefix + "Interaktiv/index.html"},
        "anki": {"report": prefix + "anki_report.json", "deck": anki["deck"], "notes": anki["notes"]},
        "practice_store": {"key": "em-practice-v1", "unit_id": unit["unit_id"],
                           "assessment_revision": assessment_revision(unit)},
        "competencies": [{"id": c["id"], "label": c.get("description", c["id"])} for c in unit["competencies"]],
        "assessments": [{"id": a["id"], "role": a.get("role", "core"), "competency_ids": a["competency_ids"],
                         "anchor": "exercise-" + _slug_task(a["id"]),
                         "title": re.sub(r"\s+", " ", re.sub(r"\$[^$]*\$", "…", a["prompt"]))[:90]}
                        for a in unit["assessments"]],
        "adaptive_track": track_for_unit(unit),
        "tracks": tracks,
    }


def _write_shell(root):
    assets = Path(root) / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ASSETS:
        shutil.copyfile(TEMPLATES / name, assets / name)
    csp = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; "
           "connect-src 'self'; base-uri 'none'; form-action 'none'")
    html = ('<!doctype html><html lang="de"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">'
            '<title>Mastery</title><link rel="stylesheet" href="assets/em_tokens.css">'
            '<link rel="stylesheet" href="assets/mastery_home.css"></head><body>'
            '<header class="m-top"><a class="m-brand" href="#start">Mastery</a><nav class="m-nav" aria-label="Bereiche">'
            '<a href="#start">Start</a><a href="#lernstand">Lernstand</a><a href="#tutor">Tutor</a>'
            '<a href="#sicherung">Sicherung</a></nav></header>'
            '<main id="app" class="m-shell"><noscript><p>Mastery braucht JavaScript. Die PDFs liegen im Ordner units/.</p>'
            '</noscript><p class="m-loading">Bibliothek wird geladen …</p></main>'
            '<script src="assets/em_tutor.js"></script><script src="assets/mastery_home.js"></script></body></html>\n')
    (Path(root) / "index.html").write_text(html, encoding="utf-8")


def build(home=None, force=False, log=print):
    """Build every outdated unit (content hash) and rewrite the home shell. Idempotent; no network, no model calls."""
    root = resolve_home(home)
    root.mkdir(parents=True, exist_ok=True)
    engine = engine_fingerprint()
    old = _read_json(root / "library.json") or {}
    previous = {u["slug"]: u for u in old.get("units", [])}
    units, built = [], []
    for item in plan(root):
        slug = item["entry"]["slug"]
        prev = previous.get(slug)
        fresh = (prev and prev.get("content_hash") == item["content_hash"]
                 and all((root / p).is_file() for p in prev["products"].values())
                 and all((root / t["href"]).is_file() for t in prev["tracks"]))
        if fresh and not force:
            units.append(prev)
            continue
        log(f"Erstelle {slug} …")
        units.append(_build_unit(root, item, log))
        built.append(slug)
    _write_shell(root)
    library = {"schema": LIBRARY_SCHEMA, "app": "Mastery", "version": 1, "engine": engine, "built_at": now(),
               "default_port": DEFAULT_PORT, "units": units, "model_calls": 0, "network_calls": 0}
    _write_json(root / "library.json", library)
    return {"home": str(root), "built": built, "units": [u["slug"] for u in units]}


def is_outdated(home=None):
    root = resolve_home(home)
    lib = _read_json(root / "library.json")
    if not lib or lib.get("schema") != LIBRARY_SCHEMA or not (root / "index.html").is_file():
        return True
    if any(not (root / "assets" / a).is_file() for a in ASSETS):
        return True
    have = {u["slug"]: u for u in lib["units"]}
    for item in plan(root):
        prev = have.get(item["entry"]["slug"])
        if not prev or prev.get("content_hash") != item["content_hash"]:
            return True
        if not all((root / p).is_file() for p in prev["products"].values()):
            return True
    return len(have) != len(load_spec(root))


def add_private_unit(unit_path, slug=None, tracks=(), home=None):
    """Register a private unit (outside the repository) in MASTERY_HOME/library-spec.local.json."""
    root = resolve_home(home)
    path = Path(unit_path).expanduser().resolve()
    if _private_output_forbidden(path):
        raise MasteryError("Private units must live outside the engine repository")
    if not path.is_file():
        raise MasteryError("Unit file not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    slug = slug or re.sub(r"[^a-z0-9-]+", "-", str(data.get("unit_id", path.stem)).lower()).strip("-")[:40] or "einheit"
    if not SLUG.match(slug):
        raise MasteryError("Invalid slug (a-z, 0-9, -)")
    refs = []
    for t in tracks:
        candidate = Path(t).expanduser()
        refs.append({"path": str(candidate.resolve()), "relation": "practice"} if candidate.suffix == ".json"
                    else {"id": t, "relation": "practice"})
    entry = {"slug": slug, "unit": str(path), "tracks": refs}
    _check_entry(entry, True)
    _load_unit(dict(entry, private=True))
    root.mkdir(parents=True, exist_ok=True)
    spec_path = root / "library-spec.local.json"
    spec = _read_json(spec_path) or {"schema": SPEC_SCHEMA, "units": []}
    if slug in {u["slug"] for u in json.loads((PKG / "library.json").read_text(encoding="utf-8"))["units"]}:
        raise MasteryError("Slug already used by the public library")
    spec["units"] = [u for u in spec["units"] if u["slug"] != slug] + [entry]
    _write_json(spec_path, spec)
    return slug


# ------------------------------------------------------------------ learner state (server backup) and export

def _check_events(events, where):
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise MasteryError(f"{where}: events must be a bounded list")
    for e in events:
        if not isinstance(e, dict) or not isinstance(e.get("type"), str):
            raise MasteryError(f"{where}: invalid event")


def validate_state(obj):
    """Schema check of a browser state snapshot. Only the two known storage keys, only lists of event objects."""
    if not isinstance(obj, dict) or obj.get("schema") != STATE_SCHEMA or set(obj) - {"schema", "saved_at", "origin", "storage"}:
        raise MasteryError("Expected mastery-state-v1 with keys schema, saved_at, origin, storage")
    if not isinstance(obj.get("saved_at"), str) or len(obj["saved_at"]) > 40:
        raise MasteryError("saved_at must be a timestamp string")
    storage = obj.get("storage")
    if not isinstance(storage, dict) or set(storage) - set(STORAGE_KEYS):
        raise MasteryError("storage may only contain " + ", ".join(STORAGE_KEYS))
    tutor = storage.get("em-tutor-v1")
    if tutor is not None:
        if not isinstance(tutor, dict) or tutor.get("schema") != 1 or not isinstance(tutor.get("tracks"), dict):
            raise MasteryError("em-tutor-v1: invalid")
        for key, rec in tutor["tracks"].items():
            if not isinstance(rec, dict):
                raise MasteryError("em-tutor-v1: invalid track record")
            _check_events(rec.get("events", []), "em-tutor-v1/" + key)
    practice = storage.get("em-practice-v1")
    if practice is not None:
        if not isinstance(practice, dict) or practice.get("schema") != 1 or not isinstance(practice.get("units"), dict):
            raise MasteryError("em-practice-v1: invalid")
        for key, rec in list(practice["units"].items()) + list((practice.get("archived") or {}).items()):
            if not isinstance(rec, dict):
                raise MasteryError("em-practice-v1: invalid unit record")
            _check_events(rec.get("events", []), "em-practice-v1/" + key)
            _check_events(rec.get("policy", []), "em-practice-v1/" + key)
    return obj


def store_state(root, obj, keep=30):
    """Write a validated snapshot to MASTERY_HOME/state (latest + rotating history)."""
    validate_state(obj)
    state = Path(root) / "state"
    with publication_lock(state):
        received = now()
        record = dict(obj, received_at=received)
        history = state / "history"
        with publication_lock(history):
            prefix = "state-" + received.replace(":", "").replace("-", "")
            same_second = sorted(history.glob(prefix + "_*.json"))
            sequence = int(same_second[-1].stem.rsplit("_", 1)[1]) + 1 if same_second else 1
            _write_json(history / f"{prefix}_{sequence:012d}.json", record)
            _write_json(state / "latest.json", record)
            for old in sorted(history.glob("state-*.json"))[:-keep]:
                old.unlink()
    return received


def state_meta(root):
    latest = _read_json(Path(root) / "state" / "latest.json")
    if not latest:
        return {"received_at": None}
    storage = latest.get("storage", {})
    tutor = sum(len(r.get("events", [])) for r in ((storage.get("em-tutor-v1") or {}).get("tracks") or {}).values())
    practice = sum(len(r.get("policy", [])) for r in ((storage.get("em-practice-v1") or {}).get("units") or {}).values())
    return {"received_at": latest.get("received_at"), "saved_at": latest.get("saved_at"),
            "workbench_events": tutor, "explorable_events": practice}


def export(home=None, out=None):
    """Backup of all learner state the server received, plus the library identity (no products, no paths)."""
    root = resolve_home(home)
    latest = _read_json(root / "state" / "latest.json")
    if not latest:
        raise MasteryError("Noch kein Lernstand beim lokalen Server angekommen: `mastery start`, Startseite öffnen "
                           "(sie sichert automatisch) und dann erneut exportieren.")
    lib = _read_json(root / "library.json") or {}
    backup = {"schema": BACKUP_SCHEMA, "created": now(), "app": "Mastery",
              "library": [{"slug": u["slug"], "unit_id": u["unit_id"], "content_hash": u["content_hash"]}
                          for u in lib.get("units", [])],
              "state": {k: latest[k] for k in ("schema", "saved_at", "received_at", "storage") if k in latest}}
    target = _guard_output(out) if out else root / "exports" / ("mastery-backup-" + now().replace(":", "").replace("-", "")
                                                          + "-" + uuid.uuid4().hex + ".json")
    _write_json(target, backup)
    return target


def status(home=None):
    root = resolve_home(home)
    lib = _read_json(root / "library.json")
    try:
        outdated = is_outdated(root)
        error = None
    except MasteryError as exc:
        outdated, error = True, str(exc)
    return {"app": "Mastery", "home": str(root), "built": bool(lib), "up_to_date": not outdated, "error": error,
            "default_port": DEFAULT_PORT, "units": [{"slug": u["slug"], "title": u["title"], "private": u["private"],
                                                     "built_at": u["built_at"]} for u in (lib or {}).get("units", [])],
            "state_backup": state_meta(root)}
