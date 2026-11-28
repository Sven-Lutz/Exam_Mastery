"""Mastery V1 command line: start | build | status | export, and the course import: import | courses | course | plan |
packet | build-chapter | quality | reimport. build-chapter and quality exit with 3 when the machine quality gates
(mastery-quality-v1) find a blocker, unless --allow-blockers. German user messages; no network beyond 127.0.0.1 (exception: `--materialize` asks
iCloud to download the user's own placeholder files, with that explicit consent)."""
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
        print("Bibliothek fehlt oder ist veraltet – wird erstellt (offline, ohne Modellaufrufe) …", flush=True)
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
    print(f"Mastery läuft offline unter {url}  (Bibliothek: {root})", flush=True)
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


def _print_course(s, full=False):
    n = s["counts"]
    print(f"Kurs {s['slug']}: {s['title']}")
    print(f"  Dateien {n['files']} (lokal {n['local']}, nicht lokal {n['not_local']}, nicht unterstützt "
          f"{n['unsupported']}, unlesbar {n['unreadable']}, Duplikate {n['duplicates']}, ignoriert {n['ignored']})")
    print(f"  Seiten/Folien {n['pages']} (mit Text {n['text_pages']}, brauchen Bildverständnis {n['vision_pages']})")
    print("  Arten: " + ", ".join(f"{k} {v}" for k, v in n["kinds"].items()))
    warns = s["warnings"]
    print(f"  Warnungen: {len(warns)}")
    for w in warns if full else [w for w in warns if w["severity"] != "info"][:25]:
        print(f"    [{w['code']}] {w['message']}")
    print(f"  Kapitel: {len(s['chapters'])}")
    for ch in s["chapters"]:
        flags = (" ÜBERSPRUNGEN" if ch["skip"] else "") + (" VERALTET" if ch["stale"] else "")
        author = f" ({ch['author_label']})" if ch["author"] else ""
        print(f"    {ch['order']:>2}. {ch['id']:<40} {ch['status']}{author}{flags}  Übungen {len(ch['exercises'])}, "
              f"Kompetenz-Vorschläge {len(ch['competencies_proposed'])}")


def cmd_import(args):
    from .courses import import_course
    s = import_course(args.folder, slug=args.slug, title=args.title, home=args.home,
                      materialize_files=args.materialize)
    _print_course(s)
    if s["counts"]["not_local"]:
        print(f"Hinweis: {s['counts']['not_local']} Datei(en) liegen nur in iCloud und wurden NICHT gelesen. "
              f"Mit Ihrer Zustimmung herunterladen: mastery reimport {s['slug']} --materialize")
    print(f"Weiter: mastery packet {s['slug']} <kapitel>   (Kapitel-IDs oben)")
    return 0


def cmd_courses(args):
    from .courses import list_courses
    for s in list_courses(args.home):
        built = sum(c["status"] in ("GEBAUT", "PRÜFUNG_AUSSTEHEND") for c in s["chapters"])
        print(f"{s['slug']:<20} {s['title']:<40} {len(s['chapters'])} Kapitel, {built} gebaut, "
              f"{len(s['warnings'])} Warnungen")
    return 0


def cmd_course(args):
    from .courses import course_status
    s = course_status(args.slug, args.home)
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        _print_course(s, full=True)
    return 0


def cmd_plan(args):
    from .courses import plan
    _print_course(plan(args.slug, args.home))
    return 0


def cmd_packet(args):
    from .courses import course_status, make_packet
    result = make_packet(args.slug, args.chapter, args.home, force=args.force)
    for w in result["warnings"]:
        print("  Hinweis: " + w)
    ch = next(c for c in course_status(args.slug, args.home)["chapters"] if c["id"] == args.chapter)
    ins = ch["instruction"]
    if ins:
        print(ins["statement"])
        print("Auftrag für die Sitzung: " + ins["prompt"])
        print("Danach: " + ins["then"])
    return 0


def cmd_card_feedback(args):
    from .card_feedback import author_export
    print(author_export(args.slug, args.chapter, args.home))
    return 0


def cmd_build_chapter(args):
    from .courses import build_chapter
    r = build_chapter(args.slug, args.chapter, args.home)
    for note in r["notes"]:
        print("  Hinweis: " + note)
    if r["built"]:
        print(f"Gebaut und eingetragen als '{r['library_slug']}': Anki {r['anki']['notes']} Notizen "
              f"({r['anki']['package_status']}, {r['anki']['restamped']} neu gestempelt). Fachliche Prüfung: ausstehend.")
    else:
        print(f"Unverändert – '{r['library_slug']}' ist aktuell, nichts neu gebaut. Fachliche Prüfung: ausstehend.")
    for key in r["anki"]["restamped_keys"]:
        print(f"  Neu gestempelt: {key}")
    for k, v in r["products"].items():
        print(f"  {k}: {v}")
    return _print_quality(r["quality"], args.allow_blockers)


def _print_quality(q, allow_blockers):
    print(q["line"])
    for f in [f for f in q["findings"] if f["severity"] != "minor"][:12]:
        print(f"  [{f['severity']}] {f['gate']} {f['location']}: {f['message']}")
    rest = len(q["findings"]) - min(12, sum(f["severity"] != "minor" for f in q["findings"]))
    if rest > 0:
        print(f"  … {rest} weitere Befunde im Bericht.")
    print(f"Qualitätsbericht: {q['report']}  (maschinell; ersetzt nicht die Abnahme durch den Owner)")
    if q["counts"]["blocker"] and not allow_blockers:
        print("Mastery: Blocker gefunden – Kapitel nicht an den Owner geben (oder bewusst: --allow-blockers).",
              file=sys.stderr)
        return 3
    return 0


def cmd_quality(args):
    from .courses import check_chapter
    q = check_chapter(args.slug, args.chapter, args.home)
    if args.json:
        print(json.dumps(q["data"], ensure_ascii=False, indent=1))
        return 3 if q["counts"]["blocker"] and not args.allow_blockers else 0
    return _print_quality(q, args.allow_blockers)


def cmd_reimport(args):
    from .courses import reimport
    s = reimport(args.slug, args.home, materialize_files=args.materialize)
    imp = s["impact"]
    print(f"Geändert {len(imp['changed_files'])}, neu {len(imp['added_files'])}, entfernt {len(imp['removed_files'])}; "
          f"veraltete Kapitel: {', '.join(imp['stale_chapters']) or 'keine'}")
    _print_course(s)
    return 0


def cmd_author(args):
    from . import authoring as A
    if args.action == "plan":
        p = A.plan(args.slug, args.home, args.chapters)
        print(f"Plan für {args.slug}: " + ", ".join(f"{v} {k}" for k, v in p["counts"].items() if v) or "nichts zu tun")
        for st in p["steps"]:
            print(f"  {st['chapter']}: {st['action']}")
        print(f"Modellaufrufe: mindestens {p['model_calls_min']}, höchstens {p['model_calls_max']} "
              f"(je Kapitel bis {A.MAX_ATTEMPTS} Versuche, {A.MAX_REVISIONS} Überarbeitung). Bereits fertig: "
              f"{len(p['chapters_done'])} Kapitel.")
        return 0
    if args.action == "authorize":
        o = A.authorize(args.slug, args.provider, args.max_runs, args.home, model=args.model, effort=args.effort,
                        timeout_min=args.timeout_min, command=args.command, allow_web=args.allow_web,
                        revoke=args.revoke)
        print((o["authorization"] or {}).get("statement") or "Freigabe widerrufen.")
        return 0
    if args.action == "check-draft":
        if not args.chapters or len(args.chapters) != 1:
            print("Mastery: check-draft braucht genau ein Kapitel: author <kurs> check-draft --chapter <id>", file=sys.stderr)
            return 2
        r = A.check_draft(args.slug, args.chapters[0], args.home)
        for e in r["errors"]:
            print("  Fehler: " + e)
        for f in r["blockers"]:
            print(f"  [blocker] {f['gate']} {f['location']}: {f['message']}")
        for f in r["majors"]:
            print(f"  [major] {f['gate']} {f['location']}: {f['message']}")
        print("Entwurf: " + ("ohne Fehler und Blocker" if r["ok"] else "nicht übernehmbar"))
        return 0 if r["ok"] else 3
    if args.action == "stop":
        A.stop(args.slug, args.home)
        print("Anhalten angefordert.")
        return 0
    if args.action == "run":
        if args.background:
            print(f"Erarbeitung läuft im Hintergrund (Prozess {A.spawn_background(args.slug, args.home, args.wait_for_reset)}).")
            return 0
        o = A.run(args.slug, args.home, chapters=args.chapters, max_steps=args.max_steps, new=args.new,
                  wait_for_reset=args.wait_for_reset)
        return 0 if o["job"] and o["job"]["status"] in ("DONE", "READY") else 4
    o = A.status(args.slug, args.home)
    print(json.dumps(o, ensure_ascii=False, indent=1))
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
    i = sub.add_parser("import", help="lokalen Kursordner importieren (nur lesend): Inventar, Warnungen, Kapitelplan")
    i.add_argument("folder", help="Kursordner (Folien, Skripte, Übungen, Lösungen, Literatur, Altklausuren)")
    i.add_argument("--slug", help="Kurzname des Kurses (Standard: aus dem Ordnernamen)")
    i.add_argument("--title", help="Titel des Kurses")
    i.add_argument("--materialize", action="store_true",
                   help="Zustimmung: iCloud-Platzhalter dieses Ordners herunterladen (brctl download)")
    sub.add_parser("courses", help="importierte Kurse auflisten")
    c = sub.add_parser("course", help="Zustand eines Kurses: Inventar, Warnungen, Kapitel und Status")
    c.add_argument("slug")
    c.add_argument("--json", action="store_true", help="vollständige Ausgabe als JSON")
    pl = sub.add_parser("plan", help="Kapitelplan neu berechnen (nach Änderungen in course.json: plan_overrides)")
    pl.add_argument("slug")
    pk = sub.add_parser("packet", help="Authoring-Paket eines Kapitels schreiben/erneuern (packet.json + Seitenbilder)")
    pk.add_argument("slug")
    pk.add_argument("chapter")
    pk.add_argument("--force", action="store_true", help="auch ein nicht vom Import erzeugtes packet.json ersetzen")
    feedback = sub.add_parser("card-feedback", help="Kartenfeedback für die nächste Autorenrunde exportieren")
    feedback.add_argument("slug")
    feedback.add_argument("chapter")
    bc = sub.add_parser("build-chapter", help="erarbeitete unit.json prüfen, vier Produkte bauen, in Bibliothek eintragen")
    bc.add_argument("slug")
    bc.add_argument("chapter")
    bc.add_argument("--allow-blockers", action="store_true",
                    help="trotz Blockern der Qualitätsprüfung mit Exit-Code 0 enden (Bericht bleibt)")
    qc = sub.add_parser("quality", help="Qualitätsprüfung (mastery-quality-v1) eines Kapitels ohne Neubau")
    qc.add_argument("slug")
    qc.add_argument("chapter")
    qc.add_argument("--json", action="store_true", help="vollständigen Bericht als JSON ausgeben")
    qc.add_argument("--allow-blockers", action="store_true", help="trotz Blockern mit Exit-Code 0 enden")
    r = sub.add_parser("reimport", help="Kursordner neu inventarisieren; betroffene Kapitel als veraltet markieren")
    r.add_argument("slug")
    r.add_argument("--materialize", action="store_true", help="Zustimmung: iCloud-Platzhalter herunterladen")
    au = sub.add_parser("author", help="Kurs erarbeiten (KI, nur mit Freigabe): plan | authorize | run | status | stop "
                                       "| check-draft")
    au.add_argument("slug")
    au.add_argument("action", choices=["plan", "authorize", "run", "status", "stop", "check-draft"])
    au.add_argument("--chapter", dest="chapters", action="append", help="nur dieses Kapitel (mehrfach möglich)")
    au.add_argument("--provider", default="claude_code_cli", choices=["claude_code_cli", "command", "manual"])
    au.add_argument("--max-runs", type=int, default=0, help="authorize: Höchstzahl der Modellaufrufe")
    au.add_argument("--model")
    au.add_argument("--effort")
    au.add_argument("--timeout-min", type=int, default=90)
    au.add_argument("--command", help="authorize --provider command: lokales Programm (liest den Auftrag von stdin)")
    au.add_argument("--allow-web", action="store_true", help="authorize: Websuche erlauben (Standard: aus)")
    au.add_argument("--revoke", action="store_true", help="authorize: Freigabe widerrufen")
    au.add_argument("--max-steps", type=int)
    au.add_argument("--new", action="store_true", help="run: neuen Lauf statt Fortsetzen")
    au.add_argument("--background", action="store_true", help="run: im Hintergrund")
    au.add_argument("--wait-for-reset", action="store_true",
                    help="run: bei Nutzungslimit bis zur vom Anbieter gemeldeten Freigabe warten und fortsetzen")
    args = parser.parse_args(argv)
    if not args.cmd:
        args = parser.parse_args([*(["--home", args.home] if args.home else []), "start"])
    try:
        return {"start": cmd_start, "build": cmd_build, "status": cmd_status, "export": cmd_export,
                "import": cmd_import, "courses": cmd_courses, "course": cmd_course, "plan": cmd_plan,
                "card-feedback": cmd_card_feedback, "packet": cmd_packet, "build-chapter": cmd_build_chapter,
                "reimport": cmd_reimport, "quality": cmd_quality, "author": cmd_author}[args.cmd](args)
    except MasteryError as exc:
        print(f"Mastery: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
