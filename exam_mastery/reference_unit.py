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
import math
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


def case_emissions(unit, sent):
    labels = unit['case']['labels']
    return [[float(row.get(l, 0.0)) for l in labels] for row in sent['emissions']]


def case_predictions(unit, mode):
    """Gold and predicted tags of the whole case study, concatenated; mode 'greedy' or 'viterbi'."""
    labels = unit['case']['labels']; gold, pred = [], []
    for sent in unit['case']['sentences']:
        em = case_emissions(unit, sent)
        p = S.greedy(em, labels) if mode == 'greedy' else S.viterbi(em, labels)[1]
        gold += sent['gold'] + ['O']; pred += p + ['O']      # sentence separator keeps spans apart
    return gold, pred


def exam_items(unit):
    return [it for form in unit.get('exam_forms', {}).values() for it in form] + unit.get('exam', [])


def toy_states(unit, sentence, direction):
    toy = unit['toy']
    xs = [toy['emb'][w] for w in ('Washington', sentence)]
    a = toy['a_fw'] if direction == 'fw' else toy['a_bw']
    comps = [S.rnn_scalar([x[k] for x in xs], a, 1.0, reverse=direction == 'bw') for k in range(2)]
    return [(comps[0][i], comps[1][i]) for i in range(len(xs))]


def compute(check: str, unit: dict):
    """Evaluate a check key to an exact value (Fraction, int, float or sorted list)."""
    kind, _, arg = check.partition(':')
    data = {t['id']: t.get('data') for t in unit['tasks'] + exam_items(unit)}
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
    if kind == 'toy':
        direction, sentence, t, comp = arg.split(':')
        return toy_states(unit, sentence, direction)[int(t) - 1][int(comp)]
    if kind == 'fpr':
        p, r = (Fraction(x) for x in arg.split(':'))
        return S.f_beta(p, r, 1)
    if kind == 'labels':
        scheme, k = arg.split(':')
        return {'IO': 1, 'BIO': 2, 'BILOU': 4}[scheme] * int(k) + 1
    if kind == 'int':
        return int(arg)
    if kind == 'attn':
        tid, what, idx = arg.split(':')
        d = data[tid]; X = d['X']; i = d['i'] - 1
        _, w, o = S.attention_row(X[i], X, X)
        return (w if what == 'w' else o)[int(idx)]
    if kind == 'attnq':
        spec, idx = arg.rsplit(':', 1)
        q, keys = spec.split('|')
        q = [float(x) for x in q.split(',')]; keys = [[float(x) for x in k.split(',')] for k in keys.split(';')]
        return S.attention_row(q, keys, keys)[1][int(idx)]
    if kind == 'rope':
        theta, m, n = (float(x) for x in arg.split(':'))
        return math.cos((n - m) * theta)
    if kind == 'sinpos':
        i, d, dm = (int(x) for x in arg.split(':'))
        return math.sin(i / 10000 ** (d / dm)) if d % 2 == 0 else math.cos(i / 10000 ** ((d - 1) / dm))
    if kind == 'viterbi':
        d = data[arg]
        return round(S.viterbi(d['emissions'], d['labels'])[0], 10)
    if kind == 'microweight':
        spec, k = arg.rsplit(':', 1)
        cs = list(_counts(spec).values()); D = [2 * c.tp + c.fp + c.fn for c in cs]
        return Fraction(D[int(k)], sum(D))
    if kind == 'case':
        mode, metric = arg.split(':')
        g, p = case_predictions(unit, mode)
        if metric == 'span_f1':
            return S.f1(S.span_counts(g, p))
        if metric == 'token_f1':
            return S.f1(S.token_counts(g, p))
        return S.error_taxonomy(g, p)[metric]
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


PLACEHOLDER = re.compile(r'(?i)\bsiehe\s+(die\s+)?(schritte|oben|lösung|text)\b|\bTODO\b|\bTBD\b|\?\?\?')
CONTROL = re.compile(r'[\r\t\x07\x08\x0b\x0c]')
YESNO = re.compile(r'^(Ist|Sind|Gibt es|Kann|Können|Hat|Haben|Stimmt|Gilt)\b')


def _decimals(x):
    out = set()
    for d in (1, 2, 3, 4):
        out.add(f'{abs(float(x)):.{d}f}'.replace('.', ','))
    return out


def _known_decimals(unit):
    """Every decimal the prose may show: recomputed values plus declared inputs found in task data."""
    vals = set()
    add = lambda x: vals.update(_decimals(x))
    for sentence in ('signed', 'state'):
        for direction in ('fw', 'bw'):
            for h in toy_states(unit, sentence, direction):
                for v in h:
                    add(v)
        add(unit['toy']['a_bw'] * toy_states(unit, sentence, 'bw')[1][1])
        add(unit['toy']['a_fw'] * toy_states(unit, sentence, 'fw')[0][0])
    for _, fn, exp in TEXT_CLAIMS:
        add(float(fn()))
    ex = _ex()
    for c in ex.values():
        add(S.f1(c))
    D = [2 * c.tp + c.fp + c.fn for c in ex.values()]
    add(Fraction(D[3], sum(D)))                                       # MISC weight 15/265
    add(S.micro({k: v for k, v in ex.items() if k != 'k3'})['F1']); add(S.macro({k: v for k, v in ex.items() if k != 'k3'}))
    add(S.f_beta(Fraction(1, 10), Fraction(1), 1)); add(Fraction(11, 20))
    items = unit['tasks'] + exam_items(unit)
    for it in items:
        for a in it['answers']:
            if a['type'] == 'num':
                add(compute(a['check'], unit))
        d = it.get('data') or {}
        for row in d.get('emissions', []):                            # given inputs
            for v in row:
                add(v)
        if 'X' in d:
            sc, w, o = S.attention_row(d['X'][d['i'] - 1], d['X'], d['X'])
            for v in sc + w + o:
                add(v)
            for v in (math.exp(x) for x in sc):
                add(v)
            add(sum(math.exp(x) for x in sc))
            for v in S.attention_row(d['X'][d['i'] - 1], d['X'], d['X'], scale=False)[1]:
                add(v)
        if 'emissions' in d:                                          # path scores of candidate sequences
            for path in __import__('itertools').product(range(len(d['labels'])), repeat=len(d['emissions'])):
                add(sum(d['emissions'][t][k] for t, k in enumerate(path)))
        for k, v in (it.get('givens') or {}).items():
            if isinstance(v, (int, float)):
                add(v)
    for spec in ('80,10,20;50,25,5;0,3,7', '60,15,10;40,20,30;70,5,5', '50,10,10;10,30,10;90,10,10'):
        cs = list(_counts(spec).values())
        for c in cs:
            add(S.f1(c)); add(Fraction(c.tp + c.fn, sum(x.tp + x.fn for x in cs)))
    add(Fraction(9, 10) * Fraction(3, 10)); add(Fraction(6, 5)); add(Fraction(1, 10) + 1); add(Fraction(1, 5) + 1)
    for mode in ('greedy', 'viterbi'):
        g, pr = case_predictions(unit, mode)
        for c in (S.span_counts(g, pr), S.token_counts(g, pr)):
            add(S.f1(c)); add(S.precision(c)); add(S.recall(c))
        per = S.per_type(g, pr); add(S.micro(per)['F1']); add(S.macro(per))
    add(math.exp(2 / math.sqrt(2))); add(2 / math.sqrt(2))
    add(1.1 ** 10); add(0.1)                                           # residual example
    for th, m, n in ((0.5, 2, 5), (0.25, 1, 5)):
        add(math.cos((n - m) * th)); add((n - m) * th); add(math.cos(n * th))
    add(0.03)
    return vals


GIVEN_DECIMALS = {'0,5': 'W = 0,5 I', '0,8': "W' = 0,8 I", '0,25': 'given theta', '1,0': 'given emission',
                  '200,000': 'currency literal from the lecture example', '0,1': 'given P / Jacobian'}


def verify(unit: dict) -> dict:
    errors, checked = [], []
    for name, fn, expected in TEXT_CLAIMS:
        got = fn()
        (checked if got == expected else errors).append(f'text: {name}: {got}')
    items = unit['tasks'] + exam_items(unit)
    if any(CONTROL.search(x) for x in _strings({k: v for k, v in unit.items() if k != 'text_html'})):
        errors.append('control character in unit strings (TeX like \\rightarrow written without raw string?)')
    ids = set()
    for item in items:
        if item['id'] in ids:
            errors.append(f'duplicate id {item["id"]}')
        ids.add(item['id'])
        if not item.get('solution'):
            errors.append(f'{item["id"]}: no worked solution')
        elif PLACEHOLDER.search(item['solution']):
            errors.append(f'{item["id"]}: placeholder in solution')
        if 'accept' in item:
            errors.append(f'{item["id"]}: multiple accepted answers are not allowed (ambiguity)')
        g = item.get('givens') or {}
        checks = [a['check'] for a in item['answers'] if a.get('check')] + ([item['result_check']] if item.get('result_check') else [])
        for chk in checks:
            kind, _, arg = chk.partition(':')
            if kind == 'params' and g:
                d, h, L = map(int, arg.split(':'))
                if (d, h, L) != (g.get('d'), g.get('dh'), 2 * g.get('K', -1) + 1):
                    errors.append(f'{item["id"]}: check {chk} does not match givens {g} (problem/solution mismatch)')
            if kind == 'labels' and g and int(arg.split(':')[1]) != g.get('K'):
                errors.append(f'{item["id"]}: check {chk} does not match givens {g}')
            if kind == 'rope' and g:
                th, m, n = (float(x) for x in arg.split(':'))
                if (th, m, n) != (g.get('theta'), g.get('m'), g.get('n')):
                    errors.append(f'{item["id"]}: check {chk} does not match givens {g}')
        if item.get('result_check'):
            v = compute(item['result_check'], unit)
            if _fmt_int(v) not in item['solution'] and _fmt_int(v) not in json.dumps(item.get('steps', []), ensure_ascii=False):
                errors.append(f'{item["id"]}: worked result {v} not stated in its own solution/steps')
        for a in item['answers']:
            if a['type'] in ('num', 'set'):
                v = compute(a['check'], unit)
                a['value'] = [int(x) for x in v] if a['type'] == 'set' else str(v)
                a['float'] = None if a['type'] == 'set' else float(v)
                tol = a.get('tol', 0.0005)
                for d in a.get('diagnoses', []):
                    if abs(_num(d['value']) - float(v)) <= tol:
                        errors.append(f'{item["id"]}: diagnosis {d["value"]} equals the correct answer')
                if isinstance(v, int) and _fmt_int(v) not in item['solution'] and str(v) not in item['solution']:
                    errors.append(f'{item["id"]}: solution does not state the computed answer {v}')
                checked.append(f'{item["id"]}/{a["label"][:30]} = {v}')
            elif a['type'] == 'choice':
                if not isinstance(a.get('correct'), int) or not 0 <= a['correct'] < len(a['options']):
                    errors.append(f'{item["id"]}: choice needs exactly one valid correct index')
                if len(set(a['options'])) != len(a['options']):
                    errors.append(f'{item["id"]}: duplicate options')
                for d in a.get('diagnoses', []):
                    if int(d['value']) == a['correct']:
                        errors.append(f'{item["id"]}: diagnosis attached to the correct option')
    # practice vs. exam: no shared data or identical computational checks
    task_checks = {a.get('check') for t in unit['tasks'] for a in t['answers'] if a.get('check')} | {t.get('result_check') for t in unit['tasks']}
    task_data = {json.dumps(t.get('data'), sort_keys=True) for t in unit['tasks'] if t.get('data')}
    for it in exam_items(unit):
        for a in it['answers']:
            if a.get('check') and a['check'] in task_checks and not a['check'].startswith(('f1:0:0:', 'int:')):
                errors.append(f'exam {it["id"]}: reuses practice computation {a["check"]}')
        if it.get('data') and json.dumps(it['data'], sort_keys=True) in task_data:
            errors.append(f'exam {it["id"]}: reuses practice data')
    kcs = set(unit['kcs'])
    for name, form in unit.get('exam_forms', {}).items():
        per = {k: [it for it in form if it['kc'] == k] for k in kcs}
        for k, its in per.items():
            if len(its) < 2:
                errors.append(f'exam form {name}: KC {k} has {len(its)} items (need >= 2)')
            if not any(it.get('transfer') for it in its) and k in ('birnn', 'prf', 'prf-level', 'attention', 'position', 'decoding', 'spans'):
                errors.append(f'exam form {name}: KC {k} lacks a transfer item')
    for t in items + unit['cards']:
        if t['kc'] not in kcs:
            errors.append(f'{t.get("id", t.get("key"))}: unknown KC {t["kc"]}')
    for k in kcs:
        if not any(t['kc'] == k for t in unit['tasks']):
            errors.append(f'KC {k}: no workbook task')
        if sum(c['kc'] == k for c in unit['cards']) < 2:
            errors.append(f'KC {k}: fewer than 2 cards')
    # Anki card rules (exam_mastery/knowledge/specs.json anki_card AC-C1)
    seen = set()
    for c in unit['cards']:
        if c['key'] in seen or not re.fullmatch(r'[a-z0-9-]+/[a-z0-9-]+', c['key']):
            errors.append(f'card key invalid or duplicate: {c["key"]}')
        seen.add(c['key'])
        if c['type'] == 'cloze':
            if '{{c1::' not in c.get('cloze', ''):
                errors.append(f'card {c["key"]}: cloze without {{{{c1::}}}}')
            continue
        words = len(re.sub(r'\\\(.*?\\\)', ' F ', c['answer'] + ' ' + c['why']).split())
        if words > 60:
            errors.append(f'card {c["key"]}: back has {words} words (> 60)')
        if YESNO.match(re.sub('<[^>]+>', '', c['prompt'])):
            errors.append(f'card {c["key"]}: yes/no front')
        if len(c['answer']) > 12 and c['answer'][:40] in c['prompt']:
            errors.append(f'card {c["key"]}: answer leaks into front')
        if not c.get('source'):
            errors.append(f'card {c["key"]}: no source')
    known = _known_decimals(unit)
    prose = unit['text_html'] + json.dumps([t.get('steps', []) for t in unit['tasks']], ensure_ascii=False) + \
        json.dumps([t.get('solution', '') for t in items], ensure_ascii=False) + json.dumps(unit['cards'], ensure_ascii=False)
    prose = prose.replace('\\\\', '\\')
    for m in sorted(set(re.findall(r'-?\d+\{,\}\d+|-?\d+,\d+', prose))):
        n = m.replace('{,}', ',').lstrip('-')
        if n not in known and n not in GIVEN_DECIMALS:
            errors.append(f'prose decimal {n} is neither recomputed nor a declared input')
        else:
            checked.append(f'prose {n}')
    html = unit['text_html']
    for ref in re.findall(r'data-task="([A-Z0-9-]+)"', html):
        if ref not in ids:
            errors.append(f'text references unknown task {ref}')
    if html.count('\\(') != html.count('\\)') or html.count('\\[') != html.count('\\]'):
        errors.append('unbalanced TeX delimiters in text')
    report = {'ok': not errors, 'errors': errors, 'checked': checked,
              'scope': 'Recomputes numbers and checks structural consistency. Proofs and prose arguments are audited by hand: docs/reference_unit/MATH_AUDIT.md'}
    if errors:
        raise UnitError(json.dumps(report, ensure_ascii=False, indent=1))
    return report


def _strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)


def _fmt_int(v):
    if isinstance(v, Fraction) and v.denominator == 1:
        v = int(v)
    if isinstance(v, int) and abs(v) >= 1000:
        s = f'{v:,}'.replace(',', '\\,')
        return s
    return str(v)


PARTS = {'lehrbuch': 'Lehrbuch', 'arbeitsbuch': 'Arbeitsbuch', 'loesungen': 'Musterloesungen', 'klausur': 'Probeklausur', 'klausur_loesungen': 'Probeklausur_Loesungen'}


def _page(unit: dict, mode: str, part: str = '') -> str:
    data = {k: v for k, v in unit.items()}
    payload = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    css = (TEMPLATES / 'unit_app.css').read_text(encoding='utf-8')
    js = (TEMPLATES / 'unit_app.js').read_text(encoding='utf-8')
    title = unit['title'] + (f' – {PARTS[part]}' if part else '')
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{css}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}},startup:{{typeset:false}}}};</script>
<script src="assets/tex-svg-full.js" defer></script></head>
<body data-mode="{mode}" data-part="{part}"><div id="app" aria-live="polite"></div>
<script id="unit-data" type="application/json">{payload}</script><script>{js}</script></body></html>"""


def _print_pdf(html_path: Path, pdf_path: Path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(html_path.as_uri())
        pg.wait_for_function('document.body.dataset.ready === "1"', timeout=90000)
        if errs:
            raise UnitError(f'print page errors in {html_path.name}: {errs}')
        tmp = pdf_path.with_suffix('.pdf.tmp')
        pg.pdf(path=str(tmp), format='A4', print_background=True,
               margin={'top': '20mm', 'bottom': '20mm', 'left': '20mm', 'right': '18mm'},
               display_header_footer=True, header_template='<span></span>',
               footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#666;font-family:sans-serif">'
                               '<span class="title"></span> · <span class="pageNumber"></span>/<span class="totalPages"></span></div>')
        b.close()
    tmp.replace(pdf_path)


def build(unit_dir: Path, out: Path, pdf: bool = True, anki: bool = True) -> dict:
    from . import anki_deck as A
    unit = load(unit_dir)
    report = verify(unit)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'assets').mkdir(exist_ok=True)
    mj = NODE / 'mathjax-full/es5/tex-svg-full.js'
    if not mj.exists():
        raise UnitError(f'MathJax runtime missing: {mj} (see .github/workflows/tests.yml for the pinned install)')
    shutil.copy2(mj, out / 'assets' / 'tex-svg-full.js')
    report['media'] = A.diagrams(out / 'media', unit)
    tmp = out / '.build'
    tmp.mkdir(exist_ok=True)
    (tmp / 'index.html').write_text(_page(unit, 'app'), encoding='utf-8')
    for part in PARTS:
        (tmp / f'{part}.html').write_text(_page(unit, 'print', part), encoding='utf-8')
    (tmp / 'anki_import.txt').write_text(anki_tsv(unit), encoding='utf-8')
    (tmp / 'anki_notes.json').write_text(json.dumps(A.inspectable(unit), ensure_ascii=False, indent=1), encoding='utf-8')
    for f in tmp.iterdir():
        f.replace(out / f.name)  # atomic per file
    tmp.rmdir()
    for stale in ('buch.html', 'Lehrbuch_Arbeitsbuch_Loesungen.pdf'):
        if (out / stale).exists():
            (out / stale).unlink()
    if anki:
        report['anki'] = A.build_apkg(unit, out / 'media', out / f'{unit["id"]}.apkg')
    if pdf:
        for part, name in PARTS.items():
            _print_pdf(out / f'{part}.html', out / f'{name}.pdf')
    report['outputs'] = sorted(p.name for p in out.iterdir())
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return report


def anki_tsv(unit: dict) -> str:
    """Plain-text export for inspection; the .apkg is the product."""
    from . import anki_deck as A
    lines = ['#separator:tab', '#html:true', f'#deck:{A.deck_name(unit)}', '#guid column:1', '#notetype column:2', '#tags column:3']
    for c in unit['cards']:
        f = A.note_fields(unit, c, unit.get('version', '0'))
        nt = A.NOTETYPES['math' if c['type'] == 'math' else c['type']]['name']
        vals = [f[k] for k in (A.CLOZE_FIELDS if c['type'] == 'cloze' else A.FIELDS)]
        lines.append('\t'.join([A.guid(unit['id'], c['key']), nt, ' '.join(A.tags(unit, c))] + [v.replace('\t', ' ').replace('\n', ' ') for v in vals]))
    return '\n'.join(lines) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(prog='exam-mastery-unit')
    ap.add_argument('cmd', choices=['build', 'verify', 'anki-preview'])
    ap.add_argument('unit_dir', type=Path)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--no-pdf', action='store_true')
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'verify':
            r = verify(load(a.unit_dir))
        elif a.cmd == 'anki-preview':
            from . import anki_deck as A
            unit = load(a.unit_dir); out = a.out or Path('unit_out')
            shots = A.render_previews(out / f'{unit["id"]}.apkg', out / 'anki_preview', NODE / 'mathjax-full/es5/tex-svg-full.js')
            r = {'ok': not any(s['overflow'] or s['rawTex'] or s['maxGlyph'] > 60 for s in shots), 'errors': [s for s in shots if s['overflow'] or s['rawTex'] or s['maxGlyph'] > 60],
                 'checked': shots}
        else:
            r = build(a.unit_dir, a.out or Path('unit_out'), pdf=not a.no_pdf)
    except UnitError as e:
        print(f'UNIT_VERIFY_FAILED\n{e}', file=sys.stderr)
        return 2
    print(json.dumps({k: v for k, v in r.items() if k != 'checked'} | {'checked': len(r['checked'])}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
