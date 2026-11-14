"""Deterministic audit of a published learning environment (Lernumgebung/course.json, schema em-learn-app-v1)
against the knowledge base. Every finding names the KB rule it derives from. Findings are structural signals,
not judgements of subject correctness or teaching quality; the report says so.

Usage: python -m exam_mastery.knowledge.audit <Lernumgebung dir> [--out report.json]
"""
import html, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

from . import fingerprint, load

TAG = re.compile(r'<[^>]+>')
text = lambda h: re.sub(r'\s+', ' ', html.unescape(TAG.sub(' ', h or ''))).strip()
words = lambda h: len(text(h).split())
YESNO = re.compile(r'^(ist|sind|kann|können|gibt|hat|haben|stimmt|trifft|muss|darf|is|are|can|does|do)\b', re.I)


def _pts(r):
    return r.get('points', 0) if isinstance(r, dict) else float(r[1])


def _runtime_asks_confidence(env, lab):
    """The lab runtime (em_labs.js) asks for a confidence rating in every prediction step; check the built page."""
    h = env / 'labs' / Path(lab['href']).name
    return h.exists() and 'Wie sicher sind Sie' in h.read_text(encoding='utf-8', errors='ignore')


def audit(env_dir):
    env = Path(env_dir)
    c = json.loads((env / 'course.json').read_text(encoding='utf-8'))
    F = []
    add = lambda rule, sev, obj, msg: F.append({'rule': rule, 'severity': sev, 'object': obj, 'finding': msg})
    items = {i['id']: i for i in c['items']}

    # --- assessment items (AS-R1, TR-R1, WE-R1, IL-R1)
    for i in c['items']:
        if i.get('rubric') and i.get('points') is not None:
            s = sum(_pts(r) for r in i['rubric'])
            if abs(s - i['points']) > 1e-9:
                add('AS-R1', 'major', i['id'], f'Rubrik summiert {s}, Aufgabe hat {i["points"]} Punkte')
        if not i.get('rubric'):
            add('AS-R1', 'major', i['id'], 'kein Bewertungsschema')
        if not text(i.get('solution')):
            add('AS-R1', 'critical', i['id'], 'keine Musterlösung')
        if i.get('stage') == 'transfer' and 'transfer_dimension' not in i:
            add('TR-R1', 'minor', i['id'], 'Transferaufgabe ohne deklarierte Transferdimension')
        if not i.get('hints') and i.get('stage') != 'exam':
            add('AI-R1', 'minor', i['id'], 'keine gestuften Hinweise')
    ops = Counter(i.get('operation') for i in c['items'])
    top, n = ops.most_common(1)[0]
    if n / len(c['items']) > 0.6:
        add('AS-R1', 'major', 'items', f'Operator-Monokultur: {n}/{len(c["items"])} Aufgaben sind {top}')
    skel = defaultdict(list)
    for i in c['items']:
        skel[(tuple(i.get('kc_ids', [])), re.sub(r'\d+(?:[.,]\d+)?', '#', text(i['prompt'])))].append(i['id'])
    for ids in skel.values():
        if len(ids) > 1:
            add('AS-R1', 'major', ','.join(ids), 'Aufgaben unterscheiden sich nur in Zahlen')
    stages_by_kc = defaultdict(set)
    for i in c['items']:
        for k in i.get('kc_ids', []):
            stages_by_kc[k].add(i.get('stage'))
    calc_kcs = {k for i in c['items'] if i.get('operation') == 'CALCULATE' for k in i.get('kc_ids', [])}
    for k in sorted(calc_kcs):
        if not stages_by_kc[k] & {'guided'}:
            add('WE-R1', 'major', k, 'Rechenkompetenz ohne Fading-Stufe (guided) vor selbstständiger Aufgabe')
    untested = [k for k in c['kcs'] if k not in stages_by_kc]
    if untested:
        add('RP-R1', 'major', 'kcs', f'{len(untested)} von {len(c["kcs"])} Kompetenzen ohne jede Abrufaufgabe')
    dup = [t for t, m in Counter(c['kcs'].values()).items() if m > 1]
    if dup:
        add('AS-R1', 'minor', 'kcs', f'doppelte Kompetenzbezeichnungen: {dup}')

    # --- exam (AS-R2)
    ex = c.get('exam') or {}
    ex_items = [items[e] for e in ex.get('items', []) if e in items]
    if ex_items:
        if 'blueprint' not in ex:
            add('AS-R2', 'major', 'exam', 'Probeklausur ohne Blueprint (Kompetenz × Operator × Punkte × Zeit)')
        tot = sum(i.get('points', 0) for i in ex_items)
        if ex.get('total_points') is not None and tot != ex['total_points']:
            add('AS-R2', 'critical', 'exam', f'Punktsumme {tot} ≠ angegebene {ex["total_points"]}')
        if not any('minutes' in i for i in ex_items):
            add('AS-R2', 'major', 'exam', 'keine Bearbeitungszeiten je Aufgabe')
        cov = {k for i in ex_items for k in i.get('kc_ids', [])}
        add('AS-R2', 'info', 'exam', f'Klausur deckt {len(cov)} von {len(c["kcs"])} Kompetenzen ab')

    # --- anki (anki_card spec)
    for card in c.get('cards', []):
        f, b = text(card['front']), card['back']
        if words(b) > 60:
            add('AC-C1', 'minor', card['id'], f'Rückseite {words(b)} Wörter (> 60)')
        if len(re.findall(r'<li\b', b)) > 4:
            add('AC-C1', 'minor', card['id'], 'Liste mit mehr als 4 Elementen')
        if YESNO.match(f):
            add('RP-R1', 'minor', card['id'], 'Ja/Nein-Frage statt Produktion')
        if not card.get('source'):
            add('AC-C1', 'minor', card['id'], 'kein Quellenverweis')

    # --- labs (PR-R1, VZ-C1)
    for lab in c.get('labs', []):
        p = env / 'labs' / (Path(lab['href']).stem + '.json')
        if not p.exists():
            add('VZ-C1', 'major', lab['id'], 'Lab-Spezifikation fehlt')
            continue
        L = json.loads(p.read_text(encoding='utf-8'))
        seq = json.dumps(L.get('sequence'), ensure_ascii=False).lower()
        if not re.search(r'predict|vorhersag|schätzen sie|was erwarten', seq):
            add('PR-R1', 'major', lab['id'], 'keine Vorhersage vor der ersten Manipulation')
        elif not re.search(r'sicher|confidence', seq) and not _runtime_asks_confidence(env, lab):
            add('PR-R1', 'minor', lab['id'], 'Vorhersage ohne Sicherheitsangabe (Hyperkorrektur nicht nutzbar)')
        if not L.get('tests'):
            add('VZ-C1', 'critical', lab['id'], 'keine Referenzfälle für das Rechenmodell')
        if not L.get('assumptions'):
            add('VZ-C1', 'major', lab['id'], 'keine Modellannahmen')

    sev = Counter(f['severity'] for f in F)
    return {'schema': 'em-kb-audit-v1', 'kb_version': load()['principles']['version'], 'kb_fingerprint': fingerprint(),
            'target': str(env), 'counts': dict(sev), 'findings': F,
            'scope_note': 'Strukturelle, deterministische Signale gegen KB-Regeln. Keine Aussage über fachliche Richtigkeit, '
                          'Verständlichkeit oder Lernwirksamkeit.'}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    r = audit(argv[0])
    if '--out' in argv:
        Path(argv[argv.index('--out') + 1]).write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print(json.dumps(r['counts']))
    for f in r['findings']:
        print(f"{f['severity']:8} {f['rule']:6} {f['object'][:40]:40} {f['finding']}")
    return 1 if r['counts'].get('critical') else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
