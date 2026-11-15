"""Portabler Tutor-Kontext je Modul (ChatGPT Projects oder Study mode in einem normalen Chat).

Erzeugt:
  tutor/PROJECT_INSTRUCTIONS.md   gemeinsame, modulunabhängige Anweisung (identisch für alle Module)
  tutor/tutor_context.md / .json  Kompetenzen, Voraussetzungen, Notation, Prüfungsrahmen, geprüfte Quellen,
                                  Aufgaben (ohne Lösungen), Produkt-IDs, Lernstand nur wenn real erhoben
  tutor/answer_key.md             Kurzschlüssel und Rubriken – separat, nur bei Bedarf hochladen
  tutor/README.md                 Einrichtung und Startsätze je Lernabsicht
Es gibt keine Synchronisierung mit ChatGPT; kein Netz- oder Provider-Aufruf.
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

SHARED = Path(__file__).resolve().parents[1] / 'tutor' / 'PROJECT_INSTRUCTIONS.md'
INTENTS = [
    ('Erkunden', 'Ich möchte {kc} verstehen. Stell mir zuerst eine Frage, die zeigt, was ich schon weiß.'),
    ('Gemeinsam herleiten', 'Lass uns {kc} gemeinsam herleiten. Ich mache jeden Schritt selbst; gib nur Hinweise.'),
    ('Fehler finden', 'Hier ist mein Lösungsversuch zu Aufgabe {task}: … Finde den ersten falschen Schritt, ohne die Lösung zu verraten.'),
    ('Active Recall', 'Frag mich fünf Abrufe zu {kc} ab, einen nach dem anderen, mit Rückmeldung nach jeder Antwort.'),
    ('Mündliche Prüfung', 'Simuliere eine 10-minütige mündliche Prüfung zum Klausurkern. Bewerte erst am Ende nach dem Schema im Kontext.'),
    ('Transfer', 'Gib mir ein anspruchsvolles Transferproblem zu {kc}, das nicht im Arbeitsbuch steht. Keine Hinweise, bis ich frage.'),
    ('Forschungsgespräch', 'Diskutiere mit mir die Grenzen der Quelle {src}. Trenne, was die Quelle belegt und was nicht.'),
]


def learner_state(path: Path | None, m: dict) -> dict | None:
    """Nur tatsächlich erhobener Lernstand (Export aus der Lernplattform). Ohne Datei: None – es wird nichts erfunden."""
    if not path:
        return None
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    tasks = {t['id']: t['kc'] for t in m.get('tasks', [])}
    per = {}
    for a in d.get('attempts', []):
        kc = a.get('kc') or tasks.get(a.get('task'))
        r = per.setdefault(kc or '?', {'attempts': 0, 'correct_unaided': 0, 'with_help': 0, 'errors': []})
        r['attempts'] += 1
        if a.get('correct') and not a.get('hints') and not a.get('revealed'):
            r['correct_unaided'] += 1
        elif a.get('hints') or a.get('revealed'):
            r['with_help'] += 1
        if not a.get('correct'):
            r['errors'].append(a.get('task'))
    return {'source': str(Path(path).name), 'exported': d.get('exported'), 'per_kc': per, 'exams': d.get('exams', []),
            'note': 'Selbst erhobene Versuche aus der lokalen Lernplattform; keine Fremdbewertung.'}


def build(m: dict, out: Path, state_path: Path | None = None) -> dict:
    out = Path(out) / 'tutor'
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SHARED, out / 'PROJECT_INSTRUCTIONS.md')
    srcs = [s for s in m['_sources'] if s.get('status') == 'verified']
    st = learner_state(state_path, m)
    ctx = {
        'module': {k: m[k] for k in ('id', 'title', 'domain', 'language') if k in m},
        'generated': date.today().isoformat(),
        'scope': m['scope'], 'exam': m['exam'], 'notation': m['notation'],
        'kcs': [{k: c.get(k) for k in ('id', 'label', 'tier', 'prerequisites', 'objectives', 'misconceptions', 'products', 'sources')} for c in m['kcs']],
        'tasks': [{'id': t['id'], 'kc': t['kc'], 'stage': t['stage'], 'prompt': t['prompt'], 'hints': t.get('hints', [])} for t in m.get('tasks', [])],
        'examples': [{'id': e['id'], 'kc': e['kc'], 'title': e['title'], 'summary': e['summary']} for e in m.get('examples', [])],
        'sources': [{k: s.get(k) for k in ('id', 'tier', 'type', 'citation', 'url', 'doi', 'date', 'access_level', 'passages', 'evidence', 'limits', 'function')} for s in srcs],
        'labs': [{k: v for k, v in l.items() if k != 'js'} for l in m.get('labs', [])],   # keine lokalen Pfade
        'learner_state': st,
        'integration': 'Keine automatische Synchronisierung. Lernstand nur über manuell exportierte Datei.',
    }
    (out / 'tutor_context.json').write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding='utf-8')
    L = [f'# Tutor-Kontext: {m["title"]}', '', f'Modul `{m["id"]}` · Fach: {m["domain"]} · erzeugt {ctx["generated"]}', '',
         '## Offizieller Rahmen', m['scope']['summary'], '', 'Offizielle Kursquellen (definieren den Prüfungsstoff): ' + '; '.join(m['scope'].get('official', [])), '',
         '## Prüfung', m['exam']['summary'], '', '## Notation', *[f'- {n["symbol"]}: {n["meaning"]}' for n in m['notation']], '', '## Kompetenzen']
    for c in m['kcs']:
        L += [f'### {c["id"]} · {c["label"]} ({ {"core": "Klausurkern", "deep": "Vertiefung", "frontier": "Forschung"}[c["tier"]]})',
              f'Voraussetzungen: {", ".join(c.get("prerequisites", [])) or "–"}', *[f'- Ziel: {o}' for o in c.get('objectives', [])],
              *[f'- Typische Fehlvorstellung: {x}' for x in c.get('misconceptions', [])],
              f'Lernprodukte: {json.dumps(c.get("products", {}), ensure_ascii=False)}', f'Quellen: {", ".join(c.get("sources", []))}', '']
    L += ['## Übungsaufgaben (ohne Lösungen; Schlüssel separat in answer_key.md)']
    for t in ctx['tasks']:
        L += [f'- **{t["id"]}** ({t["kc"]}, {t["stage"]}): {t["prompt"]}']
    L += ['', '## Eigene, geprüfte Beispiele']
    L += [f'- **{e["id"]}** ({e["kc"]}): {e["title"]} – {e["summary"]}' for e in ctx['examples']]
    L += ['', '## Geprüfte Quellen (nur diese zitieren)']
    for s in ctx['sources']:
        L += [f'- **{s["id"]}** [{s["tier"]}, {s["type"]}, Zugriff: {s["access_level"]}] {s["citation"]} {s.get("url") or ""}',
              *[f'  - {p["locator"]}: {p["content"]}' for p in s.get('passages', [])], f'  - Grenzen: {s.get("limits")}', f'  - Funktion: {s.get("function")}']
    L += ['', '## Labore', *[f'- {l["id"]}: {l["title"]} – {l.get("purpose", "")}' for l in m.get('labs', [])], '', '## Lernstand']
    if st:
        L += [f'Quelle: {st["source"]} (exportiert {st["exported"]}). {st["note"]}', *[f'- {k}: {v["attempts"]} Versuche, {v["correct_unaided"]} ohne Hilfe richtig, {v["with_help"]} mit Hilfe; Fehler bei {v["errors"]}' for k, v in st['per_kc'].items()]]
    else:
        L += ['Kein Lernstand erhoben. Beginne mit einer kurzen Diagnose; erfinde keinen Lernstand.']
    (out / 'tutor_context.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    K = [f'# Lösungsschlüssel {m["title"]}', '', 'Nur hochladen, wenn der Tutor Antworten prüfen soll. Der Tutor gibt Lösungen erst nach eigenem Versuch preis.', '']
    for t in m.get('tasks', []):
        K += [f'## {t["id"]}', f'**Kurzschlüssel.** {t["key"]}', '', f'**Ausführliche Lösung.** {t["worked"]}', '', '**Bewertung.** ' + ' · '.join(t['rubric']), '']
    (out / 'answer_key.md').write_text('\n'.join(K), encoding='utf-8')
    kc0 = m['kcs'][0]['label']; t0 = (m.get('tasks') or [{'id': '–'}])[0]['id']; s0 = (srcs or [{'id': '–'}])[0]['id']
    R = [f'# Tutor einrichten: {m["title"]}', '',
         '**Variante A – ChatGPT-Projekt (dauerhaft):** Neues Projekt anlegen → Inhalt von `PROJECT_INSTRUCTIONS.md` in die Projektanweisungen kopieren → `tutor_context.md` als Projektdatei hochladen (optional `answer_key.md`, `lernstand_*.json`). Jeder neue Chat im Projekt startet mit diesem Wissen.',
         '', '**Variante B – Lernmodus (Study mode):** Der Lernmodus ist laut OpenAI-Hilfe in Projekten nicht verfügbar. Dafür einen normalen Chat außerhalb des Projekts öffnen, den Lernmodus aktivieren, `PROJECT_INSTRUCTIONS.md` und `tutor_context.md` anhängen und einen Startsatz unten verwenden.',
         '', 'Dateigrenzen und Verfügbarkeit hängen vom Tarif ab; vor Nutzung in der OpenAI-Hilfe prüfen. Es gibt keine automatische Rückmeldung an Exam Mastery: Ergebnisse bitte selbst in der Lernplattform üben bzw. als Notiz übernehmen.', '', '## Startsätze']
    R += [f'- **{n}:** „{s.format(kc=kc0, task=t0, src=s0)}“' for n, s in INTENTS]
    (out / 'README.md').write_text('\n'.join(R) + '\n', encoding='utf-8')
    if m.get('tutor_test_protocol'):
        shutil.copy2(Path(m['_dir']) / m['tutor_test_protocol'], out / 'TESTPROTOKOLL.md')
    leak = [t['id'] for t in m.get('tasks', []) if t['key'] and t['key'] in (out / 'tutor_context.md').read_text(encoding='utf-8')]
    return {'files': sorted(p.name for p in out.iterdir()), 'answer_leak': leak, 'learner_state': bool(st), 'chars_instructions': len(SHARED.read_text(encoding='utf-8'))}
