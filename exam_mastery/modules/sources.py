"""Quellenrecherche und -prüfung (fachunabhängig).

Ablauf je Modul:
  1. `plan`   – deterministischer Rechercheplan je Kernkompetenz: Lücke, domänenspezifische Suchanfragen, Zitationskette.
  2. Recherche – durch Agent oder Mensch mit echten Werkzeugen; *kein* bezahlter Provider-Aufruf.
  3. Register  – jede verwendete Quelle mit gelesener Passage (Lokator), Zugriffsniveau, Evidenzgrad, Grenzen, Funktion.
  4. `validate` – harte Regeln, z. B.: Aussagen über Ergebnisse nur mit Volltext/Abschnitt; Abstract nur als Kontext.
Nicht prüfbare Kandidaten bleiben mit Status `unverified` im Register und werden nirgends als Beleg verwendet.
"""
from __future__ import annotations

ACCESS = {'full_text', 'section', 'abstract', 'metadata', 'private_course_material'}
USE = {'claim', 'example', 'context', 'further_reading', 'scope'}
TIER = {'official', 'extension', 'frontier'}
TYPES = {'textbook', 'paper', 'working_paper', 'docs', 'case', 'video', 'blog', 'statute', 'decision', 'dataset', 'lecture', 'practice'}
STATUS = {'verified', 'unverified', 'rejected'}

POLICY = {  # domänenspezifische Recherche- und Evidenzregeln
    'mathematics': {'queries': ['"{t}" theorem proof open textbook', '"{t}" lecture notes pdf', '"{t}" counterexample', '"{t}" history'],
                    'prefer': ['kanonische Lehrbücher (offen lizenziert bevorzugt)', 'Beweis selbst prüfen', 'historische Primärquelle nur für Historisches'],
                    'reject': ['Foren ohne Beweis', 'KI-generierte Zusammenfassungen']},
    'nlp': {'queries': ['"{t}" site:aclanthology.org', '"{t}" arxiv', '"{t}" Jurafsky Martin SLP3', '"{t}" code implementation'],
            'prefer': ['ACL Anthology / Primärpaper', 'SLP3', 'Referenzimplementierung'], 'reject': ['nicht datierte Blogposts als Beleg für Ergebnisse']},
    'business': {'queries': ['"{t}" empirical study journal of finance', '"{t}" NBER working paper', '"{t}" official term sheet', '"{t}" case study'],
                 'prefer': ['empirische Primärstudien mit Stichprobe', 'datierte Originaldokumente der Praxis (Term Sheets, Musterverträge)', 'amtliche Statistik'],
                 'reject': ['Marketingtexte als Beleg für Wirkungen', 'undatierte Zahlen', 'erfundene Unternehmenshistorien']},
    'law': {'queries': ['§ {t} gesetze-im-internet.de', '"{t}" BAG Urteil Aktenzeichen', '"{t}" Kommentar'],
            'prefer': ['amtlicher Normtext mit Stand', 'Leitentscheidungen mit Aktenzeichen', 'Kommentarliteratur'],
            'reject': ['Rechtsratgeber ohne Normbezug', 'veraltete Fassungen ohne Kennzeichnung']},
}


def validate(reg: list[dict]) -> list[str]:
    err = []
    for s in reg:
        i = s.get('id', '?')
        if s.get('tier') not in TIER: err.append(f'{i}: tier')
        if s.get('type') not in TYPES: err.append(f'{i}: type')
        if s.get('access_level') not in ACCESS: err.append(f'{i}: access_level')
        if s.get('status') not in STATUS: err.append(f'{i}: status')
        if not s.get('citation'): err.append(f'{i}: citation')
        if s.get('access_level') == 'private_course_material':
            if s.get('url'): err.append(f'{i}: private course material must not carry a public URL')
        elif not (s.get('url') or s.get('doi')):
            err.append(f'{i}: url or doi required')
        if s.get('status') == 'verified':
            if not s.get('checked_on'): err.append(f'{i}: checked_on missing')
            if not s.get('passages'): err.append(f'{i}: verified without read passage')
            for p in s.get('passages', []):
                if not p.get('locator') or not p.get('content'): err.append(f'{i}: passage needs locator and content')
            for u in s.get('used_for', []):
                if u not in USE: err.append(f'{i}: unknown use {u}')
                if u == 'claim' and s.get('access_level') not in ('full_text', 'section', 'private_course_material'):
                    err.append(f'{i}: claims need full text/section, not {s.get("access_level")}')
            if not s.get('limits'): err.append(f'{i}: limits missing')
            if not s.get('function'): err.append(f'{i}: didactic function missing')
            if s.get('type') == 'video' and not (s.get('creator') and s.get('date')): err.append(f'{i}: video needs creator and date')
            if s.get('timestamps') and not s.get('timestamps_verified'): err.append(f'{i}: timestamps not verified')
        elif s.get('used_for'):
            err.append(f'{i}: {s.get("status")} source must not be used ({s.get("used_for")})')
    return err


def is_verified(s: dict) -> bool:
    return s.get('status') == 'verified'


def gaps(m: dict) -> list[dict]:
    """Kernkompetenzen ohne geprüfte Ergänzungsquelle, deren gelesene Passage genau diese Kompetenz trägt (passage.kcs).
    Eine bloße Nennung der Quelle an der Kompetenz zählt nicht."""
    covered = set()
    for s in m['_sources']:
        if is_verified(s) and s['tier'] != 'official':
            for p in s.get('passages', []):
                covered.update(p.get('kcs', []))
    return [{'kc': k['id'], 'label': k['label']} for k in m['kcs'] if k['tier'] == 'core' and k['id'] not in covered]


def plan(m: dict) -> dict:
    """Rechercheplan: für jede Kompetenz Suchanfragen nach Domänenpolitik, Zitationskette aus vorhandenen Quellen, Lücke."""
    pol = POLICY.get(m['domain'], POLICY['mathematics'])
    have = {s['id']: s for s in m['_sources']}
    g = {x['kc'] for x in gaps(m)}
    items = []
    for k in m['kcs']:
        terms = k.get('search_terms') or [k['label']]
        items.append({'kc': k['id'], 'label': k['label'], 'tier': k['tier'], 'gap': k['id'] in g,
                      'queries': [q.format(t=t) for t in terms for q in pol['queries']],
                      'citation_chaining_from': [s for s in k.get('sources', []) if s in have and is_verified(have[s])],
                      'acceptance': 'gelesene Passage mit Lokator; Evidenzgrad; Grenzen; didaktische Funktion; Datum/Version'})
    return {'module': m['id'], 'domain': m['domain'], 'prefer': pol['prefer'], 'reject': pol['reject'], 'items': items,
            'candidates_not_verified': [s['id'] for s in m['_sources'] if s.get('status') == 'unverified'],
            'note': 'Der Plan löst keine Netz- oder Provider-Aufrufe aus. Recherche erfolgt durch Agent/Mensch mit Zustimmung; Ergebnisse gehen ins Register.'}
