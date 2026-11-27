"""Mastery V1 command line: start | build | status | export. German user messages; no network beyond 127.0.0.1."""
from __future__ import annotations

import argparse
import errno
import json
import sys
import urllib.request
import webbrowser

from . import DEFAULT_PORT, MasteryError, add_private_unit, build, export, is_outdated, resolve_home, status


def _running_mastery(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1) as response:
            return json.load(response).get("app") == "mastery"
    except Exception:
        return False


def cmd_start(args):
    from .server import make_server
    root = resolve_home(args.home)
    if args.rebuild or is_outdated(root):
        print("Bibliothek fehlt oder ist veraltet – wird erstellt (offline, ohne Modellaufrufe) …")
        build(root, force=args.rebuild)
    url = f"http://127.0.0.1:{args.port}/"
    if args.port != DEFAULT_PORT:
        print(f"Hinweis: Port {args.port} statt {DEFAULT_PORT}. Der Browser speichert den Lernstand pro Adresse – "
              "unter diesem Port sehen Sie einen anderen (meist leeren) Lernstand. Wechsel über "
              "Startseite > Sicherung (exportieren/importieren).")
    try:
        server = make_server(root, args.port, verbose=args.verbose)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE and _running_mastery(args.port):
            print(f"Mastery läuft bereits: {url}")
            if not args.no_open:
                webbrowser.open(url)
            return 0
        print(f"Port {args.port} ist belegt ({exc.strerror}). Anderen Port wählen: mastery start --port 8766 "
              "(dann anderer Browser-Speicher).", file=sys.stderr)
        return 2
    print(f"Mastery läuft offline unter {url}  (Bibliothek: {root})")
    print("Beenden mit Ctrl+C. Lernstand: im Browser; Sicherung: Startseite > Sicherung oder `mastery export`.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMastery beendet.")
    finally:
        server.server_close()
    return 0


def cmd_build(args):
    root = resolve_home(args.home)
    if args.unit:
        slug = add_private_unit(args.unit, slug=args.slug, tracks=args.track or (), home=root)
        print(f"Private Einheit '{slug}' eingetragen (nur in {root / 'library-spec.local.json'}).")
    result = build(root, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


def cmd_status(args):
    print(json.dumps(status(args.home), ensure_ascii=False, indent=1))
    return 0


def cmd_export(args):
    target = export(args.home, args.out)
    print(f"Sicherung geschrieben: {target}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="mastery", description="Mastery – lokale Lernumgebung (offline)")
    parser.add_argument("--home", help="Bibliotheksordner (Standard: $MASTERY_HOME oder ~/Mastery)")
    sub = parser.add_subparsers(dest="cmd")
    start = sub.add_parser("start", help="Bibliothek bei Bedarf erstellen, lokal bereitstellen, Browser öffnen")
    start.add_argument("--port", type=int, default=DEFAULT_PORT)
    start.add_argument("--no-open", action="store_true", help="Browser nicht öffnen")
    start.add_argument("--rebuild", action="store_true", help="alles neu erstellen")
    start.add_argument("--verbose", action="store_true")
    b = sub.add_parser("build", help="Bibliothek erstellen oder aktualisieren")
    b.add_argument("--unit", help="private Einheit (em-experience-v1 JSON) außerhalb des Repositorys hinzufügen")
    b.add_argument("--slug", help="Kurzname der privaten Einheit")
    b.add_argument("--track", action="append", help="Übungsstrecke: eingebaute ID oder Pfad zu einer em-track-v1 JSON")
    b.add_argument("--force", action="store_true", help="auch unveränderte Einheiten neu erstellen")
    sub.add_parser("status", help="Zustand der Bibliothek und letzte Sicherung")
    e = sub.add_parser("export", help="vom Server empfangenen Lernstand als Sicherungsdatei schreiben")
    e.add_argument("--out", help="Zieldatei (Standard: $MASTERY_HOME/exports/…)")
    args = parser.parse_args(argv)
    if not args.cmd:
        args = parser.parse_args([*(["--home", args.home] if args.home else []), "start"])
    try:
        return {"start": cmd_start, "build": cmd_build, "status": cmd_status, "export": cmd_export}[args.cmd](args)
    except MasteryError as exc:
        print(f"Mastery: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
