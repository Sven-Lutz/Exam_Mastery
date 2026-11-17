"""Generic numeric consistency checks on a book model (B9). Two defect classes from real course material:

1. TABLE_TOTAL: a table with a total row whose numeric columns do not add up (slide 49: 44,500 vs 44,467;
   percentages 100.06 %). Rows marked `excluded_from_total` are skipped; a table marked `known_inconsistency` is
   reported as DOCUMENTED instead of FAIL (the inconsistency is reproduced from the source and explained in the text).
2. EQUATION: every written computation "a op b ... = c" in prose, steps, results and solutions is recomputed.

Number format: the course uses the English format (1,000.5). LaTeX thin spacing ({,}) and \\cdot, \\frac{a}{b} are
normalised before parsing.
"""
import re

NUM = r'-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?'


def _num(s):
    s = s.strip().replace(',', '')
    return float(s)


def _norm(t):
    t = str(t or '')
    t = t.replace('\\%', '%').replace('{,}', ',').replace('\\,', ' ').replace('\\cdot', '*').replace('·', '*').replace('×', '*').replace('−', '-')
    t = re.sub(r'\\d?frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', t)
    t = re.sub(r'\\(?:text|mathrm)\{[^}]*\}', ' ', t)
    t = re.sub(r'\\[()\[\]]', ' ', t)
    return t


EQ = re.compile(r'((?:\(?\s*(?:' + NUM + r')\s*\)?\s*[-+*/]\s*)+\(?\s*(?:' + NUM + r')\s*\)?)\s*=\s*(' + NUM + r')(?![.\d])(\s*%)?(?!\s*[-+*/(^\d])')
# B22: a match is only a complete computation if nothing that belongs to the expression stands right before it
# (implicit product 0.5(..., symbol V(H)(..., exponent 0.5^3 * 8, an operator of a longer chain). Before B22 such
# fragments were recomputed on their own and reported as FAIL although the written computation was right.
_GLUED = re.compile(r'(?:[\w.)\]}^]|[*/+\-]\s*)$|[\d)]\s+$')
# B33: a glued match is not skipped blindly: the arithmetic prefix in front of it (e.g. "2 + 0.9 (" of a Bellman
# backup "2 + 0.9 (0.7 * 0 + 0.3 * 0) = 2") is taken into the expression, implicit products become explicit, and the
# whole written computation is checked. Only if no balanced arithmetic expression results is the match dropped.
_PREFIX = re.compile(r'[\d.\s+\-*/()]*$')


def _extend(t, start, expr):
    pre = _PREFIX.search(t[:start]).group(0)
    while pre and pre[0] in ')*/+ ':
        pre = pre[1:]
    if pre[:1] == '-' and len(pre) > 1 and pre[1] == ' ':
        pre = pre[1:].lstrip()
    if not pre or re.search(r'[\w.)\]}^]$', t[:start - len(pre)].rstrip()[-1:] or ''):
        return None
    full = pre + expr
    if full.count('(') != full.count(')'):
        return None
    full = re.sub(r'(\d)\s*\(', r'\1*(', full)
    full = re.sub(r'\)\s*\(', ')*(', full)
    return full


def equations(text):
    """[(expression, stated, computed, ok)] for computations written in the text."""
    out = []
    t = _norm(text)
    pos = 0
    while True:
        m = EQ.search(t, pos)
        if not m:
            break
        pos = m.start(2)          # a chain a = b + c = d: the next computation may start at the stated value
        start = m.start(1) + len(m.group(1)) - len(m.group(1).lstrip())
        expr, stated = m.group(1), m.group(2)
        if _GLUED.search(t[:start]):
            expr = _extend(t, start, expr.strip())
            if expr is None:
                continue
        py = re.sub(NUM, lambda x: repr(_num(x.group(0))), expr)
        if not re.fullmatch(r'[\d.eE+\-*/() ]+', py):
            continue
        try:
            val = eval(py, {'__builtins__': {}})       # only digits, operators and parentheses reach this point
        except (SyntaxError, ZeroDivisionError):
            continue
        st = _num(stated)
        if m.group(3):            # "= 74.96 %": the left side is a ratio
            val *= 100
        dec = len(stated.split('.')[1]) if '.' in stated else 0
        tol = 0.5 * 10 ** -dec + 1e-9 + abs(st) * 1e-9
        out.append((expr.strip(), stated, round(val, 6), abs(val - st) <= tol))
    return out


def _cells_num(c):
    m = re.search(NUM, str(c).replace(' ', ''))
    return _num(m.group(0)) if m and re.search(r'\d', str(c)) else None


def table_total(block):
    rows = block['rows']
    total = next((r for r in rows if isinstance(r, dict) and r.get('total')), None)
    if total is None:
        return []
    body = [r for r in rows if r is not total and not (isinstance(r, dict) and r.get('excluded_from_total'))]
    out = []
    skip = {tuple(x) for x in block.get('exclude_cells') or []}      # [row index, column] not part of the total
    for i in block.get('numeric') or []:
        vals = [_cells_num((r['cells'] if isinstance(r, dict) else r)[i]) for k, r in enumerate(rows)
                if r in body and (k, i) not in skip]
        vals = [v for v in vals if v is not None]
        stated = _cells_num(total['cells'][i])
        if stated is None or not vals:
            continue
        s = sum(vals); dec = max((len(str(x).split('.')[1]) if '.' in str(x) else 0) for x in [total['cells'][i]])
        ok = abs(s - stated) <= 0.5 * 10 ** -dec + 1e-6
        out.append({'column': block['columns'][i], 'sum': round(s, 6), 'stated': stated, 'ok': ok})
    return out


def _blocks(book):
    for s in book.get('sections', []):
        for sub in s.get('subsections') or [{'blocks': s.get('blocks', [])}]:
            yield from sub['blocks']


def _texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in ('id', 'key', 'src', 'source', 'figure', 'type', 'kind'):
                yield from _texts(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _texts(v)


def check_book_numbers(book):
    res = []
    tables = [b for b in _blocks(book) if b.get('type') == 'table'] + \
             [it['table'] for st in book.get('stages', []) for it in st['items'] if it.get('table')]
    for t in tables:
        for r in table_total(t):
            status = 'PASS' if r['ok'] else 'DOCUMENTED' if t.get('known_inconsistency') else 'FAIL'
            res.append({'check': 'TABLE_TOTAL', 'object': t.get('caption', '')[:60], 'status': status, 'documented': bool(t.get('known_inconsistency')),
                        'detail': f"{r['column']}: rows sum to {r['sum']:g}, total row states {r['stated']:g}"})
    seen = set()
    for src in (list(_blocks(book)), book.get('stages', []), *(book.get('exams') or [book.get('exam', {})]), book.get('cards', [])):
        for text in _texts(src):
            for expr, stated, val, ok in equations(text):
                if (expr, stated) in seen:
                    continue
                seen.add((expr, stated))
                res.append({'check': 'EQUATION', 'object': f'{expr} = {stated}', 'status': 'PASS' if ok else 'FAIL', 'detail': f'computed {val:g}'})
    return res
