"""Gemeinsamer Modulvertrag und modulunabhängige Qualitätsprüfung."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

DOMAINS = {'mathematics', 'nlp', 'business', 'law', 'other'}
TIERS = {'core', 'deep', 'frontier'}
STAGES = {'worked', 'faded', 'guided', 'independent', 'proof', 'error', 'transfer', 'case', 'issue-spotting', 'model'}

# Gleiche Dimensionen für jedes Fach; Methode je Domäne
QC_DIMENSIONS = [
    ('scope', 'Offizieller Rahmen: jede Kernkompetenz verweist auf eine offizielle Kursquelle (Lokator).'),
    ('sources', 'Eigenständig recherchierte, geprüfte Ergänzungsquellen mit gelesener Passage, Evidenzgrad, Grenzen, didaktischer Funktion.'),
    ('claims', 'Zahlen und Behauptungen der eigenen Beispiele unabhängig geprüft (fachspezifische Methode).'),
    ('examples', 'Mindestens zwei originelle, geprüfte Anwendungen mit Gegenbeispiel bzw. Grenzfall.'),
    ('tasks', 'Aufgaben mit Kurzschlüssel, ausführlicher Lösung und Bewertungsschema; keine Selbstbewertung.'),
    ('lab', 'Labor ist ein Experiment mit kausaler Rückmeldung, ohne Karteikarten-/Wiederholungsfunktion.'),
    ('tutor', 'Portabler Tutor-Kontext vollständig; keine Lösungen im Kontext; Lernstand nur, wenn real erhoben.'),
    ('channels', 'Kanäle getrennt: Labor ≠ Anki ≠ Lehrbuch ≠ Tutor.'),
    ('human_review', 'Freigabe nur durch menschliche Bewertung.'),
]
METHODS = {
    'mathematics': 'Beweisschritte gegen Lehrbuchsatz; Zahlen mit exakter Arithmetik (fractions) und Gleitkomma-Orakel',
    'nlp': 'Rechenorakel (Python) gegen JS-Kern; vollständige Aufzählung; Primärpaper',
    'business': 'Kapitalisierungstabelle mit exakten Brüchen, Invarianten (Summe 100 %), datierte Praxisquellen, Annahmen explizit',
    'law': 'Normtext in geltender Fassung mit Stand-Datum, Leitentscheidungen mit Aktenzeichen',
    'other': 'fachspezifisch festzulegen',
}


class ModuleError(Exception):
    pass


def load(module_dir: Path) -> dict:
    module_dir = Path(module_dir)
    m = json.loads((module_dir / 'module.json').read_text(encoding='utf-8'))
    reg = module_dir / 'sources.registry.json'
    m['_sources'] = json.loads(reg.read_text(encoding='utf-8')) if reg.exists() else []
    m['_dir'] = str(module_dir)
    return m


def validate(m: dict) -> list[str]:
    """Strukturelle Regeln des Vertrags (schlägt fehl statt zu raten)."""
    err = []
    for k in ('id', 'title', 'domain', 'scope', 'kcs', 'notation', 'exam'):
        if k not in m:
            err.append(f'module: missing {k}')
    if m.get('domain') not in DOMAINS:
        err.append(f'module: unknown domain {m.get("domain")}')
    ids = {k['id'] for k in m.get('kcs', [])}
    src_ids = {s['id'] for s in m.get('_sources', [])}
    for k in m.get('kcs', []):
        if k.get('tier') not in TIERS:
            err.append(f'kc {k.get("id")}: tier must be one of {sorted(TIERS)}')
        for p in k.get('prerequisites', []):
            if p not in ids and not p.startswith('ext:'):
                err.append(f'kc {k["id"]}: unknown prerequisite {p} (use ext: for outside knowledge)')
        for s in k.get('sources', []):
            if s not in src_ids:
                err.append(f'kc {k["id"]}: unknown source {s}')
    for t in m.get('tasks', []):
        if t.get('kc') not in ids:
            err.append(f'task {t.get("id")}: unknown kc')
        if t.get('stage') not in STAGES:
            err.append(f'task {t.get("id")}: unknown stage {t.get("stage")}')
        for f in ('prompt', 'key', 'worked', 'rubric'):
            if not t.get(f):
                err.append(f'task {t.get("id")}: missing {f}')
        if t.get('self_assessment'):
            err.append(f'task {t.get("id")}: self-assessment is not allowed')
    for e in m.get('examples', []):
        if e.get('kc') not in ids:
            err.append(f'example {e.get("id")}: unknown kc')
        if not e.get('check'):
            err.append(f'example {e.get("id")}: no independent check')
    return err


def run_checks(m: dict) -> list[dict]:
    """Führt die unabhängigen Prüfungen der Beispiele aus (check = 'datei.py::funktion', liefert dict oder wirft)."""
    out = []
    for e in m.get('examples', []):
        f, _, fn = e['check'].partition('::')
        p = Path(m['_dir']) / f
        spec = importlib.util.spec_from_file_location(f'check_{m["id"]}_{p.stem}', p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            res = getattr(mod, fn)()
            out.append({'example': e['id'], 'ok': True, 'facts': res})
        except AssertionError as ex:
            out.append({'example': e['id'], 'ok': False, 'error': str(ex)})
    return out


def qc(m: dict, extra: dict | None = None) -> dict:
    """Einheitliches QC-Schema. Automatisch prüfbare Dimensionen erhalten PASS/FAIL, didaktische Güte bleibt NOT_RATED."""
    from . import sources as S
    extra = extra or {}
    res = {}
    core = [k for k in m['kcs'] if k['tier'] == 'core']
    off = {s['id'] for s in m['_sources'] if s['tier'] == 'official'}
    miss = [k['id'] for k in core if not set(k.get('sources', [])) & off]
    res['scope'] = ('PASS' if not miss else 'FAIL', f'{len(core) - len(miss)}/{len(core)} Kernkompetenzen mit offizieller Quelle' + (f'; fehlt: {miss}' if miss else ''))
    serr = S.validate(m['_sources'])
    ext = [s for s in m['_sources'] if s['tier'] != 'official' and S.is_verified(s)]
    gaps = S.gaps(m)
    res['sources'] = ('PASS' if not serr and ext else 'FAIL', f'{len(ext)} geprüfte Ergänzungsquellen; Regelverstöße {len(serr)}; Lücken {len(gaps)}' + (f': {serr[:3]}' if serr else ''))
    checks = run_checks(m)
    bad = [c for c in checks if not c['ok']]
    res['claims'] = ('PASS' if checks and not bad else 'FAIL', f'{len(checks) - len(bad)}/{len(checks)} Beispielprüfungen grün ({METHODS[m["domain"]]})')
    ex = [e for e in m.get('examples', []) if e.get('original') and e.get('counterexample')]
    res['examples'] = ('PASS' if len(ex) >= 2 else 'FAIL', f'{len(ex)} originelle Beispiele mit Grenzfall/Gegenbeispiel')
    tasks = m.get('tasks', [])
    res['tasks'] = ('PASS' if tasks and not [e for e in validate(m) if e.startswith('task')] else 'FAIL', f'{len(tasks)} Aufgaben mit Schlüssel, ausführlicher Lösung, Rubrik')
    lab = extra.get('lab')
    res['lab'] = lab or ('NOT_BUILT', 'kein Labor erzeugt')
    tut = extra.get('tutor')
    res['tutor'] = tut or ('NOT_BUILT', 'kein Tutor-Kontext erzeugt')
    res['channels'] = extra.get('channels', ('NOT_CHECKED', ''))
    res['human_review'] = ('PENDING', m.get('status', 'HUMAN_REVIEW_PENDING'))
    return {'module': m['id'], 'domain': m['domain'], 'method': METHODS[m['domain']], 'dimensions': {k: {'status': v[0], 'evidence': v[1]} for k, v in res.items()},
            'didactic_quality': 'NOT_RATED (nur menschliche Bewertung)', 'checks': checks}
