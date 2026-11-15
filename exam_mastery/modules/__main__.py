"""CLI: python -m exam_mastery.modules build <modul-ordner> --out <ziel> [--state lernstand.json]
        python -m exam_mastery.modules build-unit <referenz-einheit> --out <ziel>   (Adapter für units/*)
Keine Netz- oder Provider-Aufrufe."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from . import contract as C, sources as SRC, tutor as TU

TPL = Path(__file__).resolve().parents[1] / 'templates'
NODE_MJ = Path.home() / '.cache/exam-mastery-v05-node/node_modules/mathjax-full/es5/tex-svg-full.js'
FORBIDDEN_IN_LAB = re.compile(r'Leitner|Karteikarte|flashcard|due\s*cards|Wiederholungsplan|spaced', re.I)


def build_lab(m: dict, out: Path, core_files=('lab_core.js',), extra_js: list[Path] | None = None) -> tuple:
    """Fachunabhängiger Labor-Builder: gemeinsamer Kern (Bühne, Pfad, Challenges, Hypothesen) + fachspezifische Labore."""
    js = [TPL / f for f in core_files] + [Path(m['_dir']) / f for l in m.get('labs', []) for f in l.get('js', [])] + (extra_js or []) + [TPL / 'lab_boot.js']
    code = '\n'.join(p.read_text(encoding='utf-8') for p in js)
    hits = FORBIDDEN_IN_LAB.findall(code)
    payload = {'id': m['id'], 'title': m['title'], 'chapter': m['title'], 'book_href': None,
               'kc_labels': {k['id']: k['label'] for k in m['kcs']}, 'kc_map': {k['id']: {'sections': [k['id']]} for k in m['kcs']}}
    css = (TPL / 'unit_app.css').read_text(encoding='utf-8') + (TPL / 'lab.css').read_text(encoding='utf-8')
    (out / 'assets').mkdir(parents=True, exist_ok=True)
    if NODE_MJ.exists():
        shutil.copy2(NODE_MJ, out / 'assets' / 'tex-svg-full.js')
    html = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Interaktives Labor – {m['title']}</title><style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']]}},svg:{{fontCache:'global'}}}};</script><script src="assets/tex-svg-full.js" defer></script></head>
<body class="lab"><noscript>Das Labor benötigt JavaScript.</noscript><script id="unit-data" type="application/json">{json.dumps(payload, ensure_ascii=False).replace('</', '<\\/')}</script>
<script>{code}</script></body></html>"""
    (out / 'labor.html').write_text(html, encoding='utf-8')
    status = ('FAIL', f'Karteikarten-/Wiederholungsbegriffe im Labor-Code: {hits}') if hits else ('PASS', f'{len(m.get("labs", []))} Labor(e); keine Karteikarten- oder Wiederholungsfunktion im Code')
    return status


def from_unit(unit_dir: Path) -> dict:
    """Adapter: bestehende NLP-Referenzeinheit -> gemeinsamer Modulvertrag (zeigt, dass NLP nur ein Fall ist)."""
    from .. import reference_unit as RU
    u = RU.load(unit_dir)
    kcs = []
    for k, label in u['kcs'].items():
        km = u['kc_map'][k]
        pre = sorted({c.get('prereq') for c in u['cards'] if c['kc'] == k and c.get('prereq')})
        lab = (u.get('lab') or {}).get(k)
        kcs.append({'id': k, 'label': label, 'tier': 'deep' if k in ('prf-edge', 'micro-macro') else 'core', 'prerequisites': [f'ext:{p}' for p in pre],
                    'objectives': [f'Vorlesung {km["lecture"]}; Lehrbuch {km["textbook"]}'], 'misconceptions': sorted({c['mistake'] for c in u['cards'] if c['kc'] == k and c.get('mistake')}),
                    'products': {'book': km['sections'], 'tasks': [t['id'] for t in u['tasks'] if t['kc'] == k], 'cards': [c['key'] for c in u['cards'] if c['kc'] == k],
                                 'lab': [{'lab': lab['lab'], 'item': i[0]} for i in lab['items']] if lab else []},
                    'sources': ['kurs'] + [s for s in km['research'] if s]})
    srcs = []
    for s in u['sources']:
        read = bool(re.search(r'Gelesen|Verwendet|verwendet:|§|S\. \d', s['ref']))
        abstract = 'Zusammenfassung' in s['ref'] or 'Abstract' in s['ref']
        private = s['kind'] == 'KURS'
        srcs.append({'id': s['id'], 'tier': 'official' if private else ('extension' if s['kind'] in ('LEHRBUCH', 'FORSCHUNG') else 'frontier'),
                     'type': 'lecture' if private else ('textbook' if s['kind'] == 'LEHRBUCH' else 'video' if s['id'].startswith('3b1b') else 'paper'),
                     'status': 'verified' if (read or private) else 'unverified', 'access_level': 'private_course_material' if private else ('abstract' if abstract else 'section'),
                     'citation': s['ref'], 'url': None if private else s.get('url'), 'doi': s.get('doi'), 'checked_on': '2026-11-14',
                     'passages': [{'locator': 'siehe Zitat', 'content': s['ref']}] if (read or private) else [],
                     'used_for': (['scope'] if private else ['context'] if abstract else ['claim']) if (read or private) else [],
                     'limits': 'Belegstellen im Lehrbuch angegeben; Nachprüfung der Lesepassagen: docs/reference_unit/MATH_AUDIT.md', 'function': 'Beleg im Lehrbuch der NLP-Einheit',
                     'creator': '3Blue1Brown' if s['id'].startswith('3b1b') else None, 'date': '2024-04-07' if s['id'].startswith('3b1b') else None})
    tasks = [{'id': t['id'], 'kc': t['kc'], 'stage': t['stage'] if t['stage'] in C.STAGES else 'independent', 'prompt': t['prompt'], 'hints': t.get('hints', []),
              'key': t['solution'], 'worked': t.get('worked') or t['solution'], 'rubric': t.get('rubric') or ['siehe Musterlösung']} for t in u['tasks']]
    return {'id': u['id'], 'title': u['title'], 'domain': 'nlp', 'language': 'de', 'status': 'HUMAN_REVIEW_PENDING',
            'scope': {'summary': u['subtitle'], 'official': ['Vorlesungsfolien NLP Kap. 09 (privat)']},
            'exam': {'summary': 'Zwei Probeklausurformen A/B; offizielle Angaben zu Dauer und Hilfsmitteln liegen nicht vor.', 'known': False},
            'notation': [{'symbol': 'Q, K, V', 'meaning': 'Zeilen = Token; Q = XW_Q usw.'}, {'symbol': 'BIO', 'meaning': 'B-X Anfang, I-X innen, O außerhalb'}, {'symbol': 'TP, FP, FN', 'meaning': 'Zählwerte auf Spannenebene (conlleval)'}],
            'kcs': kcs, 'tasks': tasks,
            'examples': [{'id': 'N1', 'kc': 'attention', 'original': True, 'counterexample': True, 'title': '„Bank“ am Fluss (Startzustand des Labors)', 'check': 'checks.py::bank',
                          'summary': 'w = (0,5904; 0,1037; 0,3059), o = (1,1343; 0,3763); gemeinsame Key-Verschiebung ändert nichts, einzelne schon.'},
                         {'id': 'N2', 'kc': 'attention', 'original': True, 'counterexample': True, 'title': 'Softmax-Jacobi bei T → 0: eindeutig vs. Gleichstand', 'check': 'checks.py::jacobian_ties',
                          'summary': 'Mit eindeutigem Maximum geht J gegen 0, bei gleich großen Maxima divergiert J (Lemma 6.4).'}],
            'labs': [{'id': 'attention', 'title': 'Self-Attention, CRF/Viterbi, BiRNN, Spannen & F1', 'purpose': 'Experimente zu Attention-Geometrie, Viterbi vs. Vorwärts, Abhängigkeitsbereich, Zählweisen',
                      'js': [str(TPL / f) for f in ('lab_math.js', 'lab_attention.js', 'lab_seq.js')]}],
            '_sources': srcs, '_dir': str(unit_dir)}


def build(m: dict, out: Path, state: Path | None, lab: bool = True) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    errs = C.validate(m)
    if errs:
        raise C.ModuleError('\n'.join(errs))
    lab_status = build_lab(m, out) if lab and any(l.get('js') for l in m.get('labs', [])) else None
    tr = TU.build(m, out, state)
    tutor_status = ('PASS' if not tr['answer_leak'] else 'FAIL', f'{len(tr["files"])} Dateien; Lösungen im Kontext: {tr["answer_leak"] or "keine"}; Lernstand: {"real erhoben" if tr["learner_state"] else "keiner (nicht erfunden)"}; gemeinsame Anweisung {tr["chars_instructions"]} Zeichen')
    plan = SRC.plan(m)
    (out / 'source_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    q = C.qc(m, {'lab': lab_status, 'tutor': tutor_status, 'channels': ('PASS', 'Labor ohne Karteikarten; Anki als eigenes Paket; Tutor als eigener Kanal') if (lab_status or ('PASS',))[0] == 'PASS' else ('FAIL', 'siehe lab')})
    (out / 'qc_report.json').write_text(json.dumps(q, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    return q


def main(argv=None):
    ap = argparse.ArgumentParser(prog='exam-mastery-modules')
    ap.add_argument('cmd', choices=['build', 'build-unit', 'validate', 'plan'])
    ap.add_argument('path', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--state', type=Path)
    a = ap.parse_args(argv)
    m = from_unit(a.path) if a.cmd == 'build-unit' else C.load(a.path)
    if a.cmd == 'validate':
        e = C.validate(m) + SRC.validate(m['_sources']); print('\n'.join(e) or 'ok'); return 1 if e else 0
    if a.cmd == 'plan':
        print(json.dumps(SRC.plan(m), ensure_ascii=False, indent=1)); return 0
    q = build(m, a.out or Path('module_out'), a.state)
    print(json.dumps({k: v['status'] for k, v in q['dimensions'].items()}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
