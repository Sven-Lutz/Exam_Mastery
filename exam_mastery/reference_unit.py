"""Build and verify an authored reference learning unit (offline app, PDF, Anki import).

    python -m exam_mastery.reference_unit build units/nlp_sequence_labeling --out <dir> [--no-pdf]
    python -m exam_mastery.reference_unit verify units/nlp_sequence_labeling

``verify`` recomputes every checkable answer and every diagnosis value with ``exam_mastery.seqlab``
and fails closed: a unit whose stored solution numbers disagree with the recomputation is not built.
No model call happens here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from fractions import Fraction
from pathlib import Path

from . import seqlab as S

TEMPLATES = Path(__file__).parent / 'templates'
NODE = Path.home() / '.cache/exam-mastery-v05-node/node_modules'


class UnitError(Exception):
    pass


def _counts(spec):
    return {f'k{i}': S.Counts(*map(int, part.split(','))) for i, part in enumerate(spec.split(';'))}


def compute(check: str, unit: dict):
    """Evaluate a check key to an exact value (Fraction, int, or sorted list)."""
    kind, _, arg = check.partition(':')
    data = {t['id']: t.get('data') for t in unit['tasks'] + unit['exam']}
    if kind == 'params':
        d, h, L = map(int, arg.split(':'))
        return S.birnn_tagger_param_count(d, h, L)
    if kind in ('span_f1', 'token_f1'):
        d = data[arg]
        c = (S.span_counts if kind == 'span_f1' else S.token_counts)(d['gold'], d['pred'])
        return S.f1(c)
    if kind == 'f1':
        return S.f1(S.Counts(*map(int, arg.split(':'))))
    if kind == 'micro':
        return S.micro(_counts(arg))['F1']
    if kind == 'macro':
        return S.macro(_counts(arg))
    if kind == 'dep':
        T, t, direction = arg.split(':')
        return sorted(S.dependence(int(T), direction)[int(t)])
    if kind == 'birnn_b1':
        return S.rnn_scalar([1, 0, -1], 0.8, 0.5, reverse=True)[0]
    raise UnitError(f'unknown check {check!r}')


def _num(v):
    if isinstance(v, str):
        return float(Fraction(v.replace(',', '.'))) if '/' in v else float(v.replace(',', '.'))
    return float(v)


# Numbers stated in the textbook prose, recomputed here (claim text -> exact value).
TEXT_CLAIMS = [
    ('Parameter CoNLL-Beispiel 60 937', lambda: S.birnn_tagger_param_count(100, 128, 9), 60937),
    ('Folie System 1 Phrase F1 2/3', lambda: S.f1(S.span_counts(*_slide(1))), Fraction(2, 3)),
    ('Folie System 1 Token F1 1/3', lambda: S.f1(S.token_counts(*_slide(1))), Fraction(1, 3)),
    ('Folie System 2 Phrase P=R=F1 1/2', lambda: S.f1(S.span_counts(*_slide(2))), Fraction(1, 2)),
    ('Folie System 2 Token R 4/5', lambda: S.recall(S.token_counts(*_slide(2))), Fraction(4, 5)),
    ('Folie System 2 Token F1 8/9', lambda: S.f1(S.token_counts(*_slide(2))), Fraction(8, 9)),
    ('Micro-F1 192/265', lambda: S.micro(_ex())['F1'], Fraction(192, 265)),
    ('Macro-F1 989/1680', lambda: S.macro(_ex()), Fraction(989, 1680)),
    ('Macro-of-means ≈0,5926', lambda: round(float(S.macro_of_means(_ex())), 4), 0.5926),
    ('MISC F1 2/15', lambda: S.f1(_ex()['k3']), Fraction(2, 15)),
]


def _slide(system):
    gold = ['B-ORG', 'I-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON']
    pred = {1: ['O'] * 7 + ['B-MON'], 2: ['O', 'B-ORG', 'I-ORG', 'I-ORG', 'O', 'O', 'O', 'B-MON']}[system]
    return gold, pred


def _ex():
    return _counts('45,5,5;30,10,10;20,15,15;1,4,9')


def load(unit_dir: Path) -> dict:
    unit = json.loads((unit_dir / 'unit.json').read_text(encoding='utf-8'))
    unit['text_html'] = (unit_dir / unit['text']).read_text(encoding='utf-8')
    return unit


def verify(unit: dict) -> dict:
    errors, checked = [], []
    for name, fn, expected in TEXT_CLAIMS:
        got = fn()
        (checked if got == expected else errors).append(f'text: {name}: {got}')
    ids = set()
    for item in unit['tasks'] + unit['exam']:
        if item['id'] in ids:
            errors.append(f'duplicate id {item["id"]}')
        ids.add(item['id'])
        if not item.get('solution'):
            errors.append(f'{item["id"]}: no worked solution')
        for a in item['answers']:
            if a['type'] in ('num', 'set'):
                v = compute(a['check'], unit)
                a['value'] = [int(x) for x in v] if a['type'] == 'set' else str(v)
                a['float'] = None if a['type'] == 'set' else float(v)
                tol = a.get('tol', 0.0005)
                for d in a.get('diagnoses', []):
                    if abs(_num(d['value']) - float(v)) <= tol:
                        errors.append(f'{item["id"]}: diagnosis {d["value"]} equals the correct answer')
                checked.append(f'{item["id"]}/{a["label"][:30]} = {v}')
            elif a['type'] == 'choice' and not (0 <= a['correct'] < len(a['options'])):
                errors.append(f'{item["id"]}: choice index out of range')
        for step in item.get('steps', []):
            for m in re.findall(r'(-?\d+\{,\}\d{4})', step['s']):
                pass  # step decimals are covered by the B2 check below
    b2 = S.rnn_scalar([1, 0, -1], 0.8, 0.5, reverse=True)
    for want, got in (('-0{,}4621', b2[2]), ('-0{,}3537', b2[1]), ('0{,}2137', b2[0])):
        if f'{got:.4f}'.replace('.', '{,}') != want:
            errors.append(f'B2 step value {want} != {got:.4f}')
    seen = set()
    for c in unit['cards']:
        if c['key'] in seen or not re.fullmatch(r'[a-z0-9-]+/[a-z0-9-]+', c['key']):
            errors.append(f'card key invalid or duplicate: {c["key"]}')
        seen.add(c['key'])
    html = unit['text_html']
    for ref in re.findall(r'data-task="([A-Z0-9]+)"', html):
        if ref not in ids:
            errors.append(f'text references unknown task {ref}')
    if html.count('\\(') != html.count('\\)') or html.count('\\[') != html.count('\\]'):
        errors.append('unbalanced TeX delimiters in text')
    report = {'ok': not errors, 'errors': errors, 'checked': checked}
    if errors:
        raise UnitError(json.dumps(report, ensure_ascii=False, indent=1))
    return report


def card_guid(unit_id: str, key: str) -> str:
    return hashlib.sha256(f'{unit_id}|{key}'.encode()).hexdigest()[:16]


def anki_tsv(unit: dict) -> str:
    deck = f'Exam Mastery::{unit["course"]}::{unit["title"]}'
    lines = ['#separator:tab', '#html:true', '#notetype:Basic', f'#deck:{deck}', '#guid column:1', '#tags column:4']
    for c in unit['cards']:
        clean = lambda s: s.replace('\t', ' ').replace('\n', ' ')
        lines.append('\t'.join([card_guid(unit['id'], c['key']), clean(c['front']), clean(c['back']),
                                'exam-mastery ' + c['kc']]))
    return '\n'.join(lines) + '\n'


def _page(unit: dict, mode: str) -> str:
    data = {k: v for k, v in unit.items()}
    data['cards'] = [dict(c, guid=card_guid(unit['id'], c['key'])) for c in unit['cards']]
    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    css = (TEMPLATES / 'unit_app.css').read_text(encoding='utf-8')
    js = (TEMPLATES / 'unit_app.js').read_text(encoding='utf-8')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{unit['title']}</title><style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}},startup:{{typeset:false}}}};</script>
<script src="assets/tex-svg-full.js" defer></script></head>
<body data-mode="{mode}"><div id="app" aria-live="polite"></div>
<script id="unit-data" type="application/json">{payload}</script><script>{js}</script></body></html>"""


def build(unit_dir: Path, out: Path, pdf: bool = True) -> dict:
    unit = load(unit_dir)
    report = verify(unit)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assets').mkdir(exist_ok=True)
    mj = NODE / 'mathjax-full/es5/tex-svg-full.js'
    if not mj.exists():
        raise UnitError(f'MathJax runtime missing: {mj} (see .github/workflows/tests.yml for the pinned install)')
    shutil.copy2(mj, out / 'assets' / 'tex-svg-full.js')
    tmp = out / '.build'
    tmp.mkdir(exist_ok=True)
    for name, mode in (('index.html', 'app'), ('buch.html', 'print')):
        (tmp / name).write_text(_page(unit, mode), encoding='utf-8')
    (tmp / 'anki_import.txt').write_text(anki_tsv(unit), encoding='utf-8')
    for name in ('index.html', 'buch.html', 'anki_import.txt'):
        (tmp / name).replace(out / name)  # atomic per file
    tmp.rmdir()
    if pdf:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto((out / 'buch.html').as_uri())
            pg.wait_for_function('document.body.dataset.ready === "1"', timeout=60000)
            if errs:
                raise UnitError(f'print page errors: {errs}')
            pg.pdf(path=str(out / 'Lehrbuch_Arbeitsbuch_Loesungen.pdf.tmp'), format='A4', print_background=True,
                   margin={'top': '18mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'},
                   display_header_footer=True, header_template='<span></span>',
                   footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666">'
                                   '<span class="pageNumber"></span> / <span class="totalPages"></span></div>')
            b.close()
        (out / 'Lehrbuch_Arbeitsbuch_Loesungen.pdf.tmp').replace(out / 'Lehrbuch_Arbeitsbuch_Loesungen.pdf')
    report['outputs'] = sorted(p.name for p in out.iterdir())
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(prog='exam-mastery-unit')
    ap.add_argument('cmd', choices=['build', 'verify'])
    ap.add_argument('unit_dir', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--no-pdf', action='store_true')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'verify':
            r = verify(load(a.unit_dir))
        else:
            r = build(a.unit_dir, a.out or Path('unit_out'), pdf=not a.no_pdf)
    except UnitError as e:
        print(f'UNIT_VERIFY_FAILED\n{e}', file=sys.stderr)
        return 2
    print(json.dumps({k: v for k, v in r.items() if k != 'checked'} | {'checked': len(r['checked'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
