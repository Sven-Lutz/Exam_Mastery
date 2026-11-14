"""Arithmetic of written calculation steps, independent of the model's own numeric_checks (B6.6, exact since B6.7).

What this checks: in an equation chain written in the text (``CON = 1/0.85*(0.15*7,700,000 € - 900,000 €) =
300,000 €``) every side that evaluates to a number is computed exactly (fractions, no floats), and consecutive sides
must agree within the precision the shown literal is written with (``≈ 44,467`` → ±0.5; ``44,466.666…`` → truncated).
Symbols defined by a numeric chain (``POM = ... = 8,000,000``, also in a later step) are substituted into the other
steps of the same text sequence, so algebra such as ``0.85 CON = 255,000`` is checked once ``CON = 300,000`` is known.

Number formats: ``7,700,000`` / ``1.7`` (English) and ``0,85`` / ``1.234,5`` (German) are unambiguous. ``1,857`` and
``1.234`` are ambiguous; they are read in both conventions and a step whose verdict depends on the reading stays
NOT_TESTED (reason AMBIGUOUS_NUMBER_FORMAT). Scale words (k, Mio, Mrd) are applied; a chain that uses one scale
throughout is compared in that scale; different currencies in one chain are NOT_TESTED (UNIT_MISMATCH).

What this does NOT check, and never reports as checked:
- whether the relation set up is the right one for the problem (model choice, which share, pre- vs. post-money);
- economic or legal meaning;
- steps that still contain unknown symbols (NOT_TESTED, not PASS).
So PASS means "the written arithmetic is consistent", never "the derivation is correct".
"""
from __future__ import annotations
import ast, operator, re
from collections import Counter
from fractions import Fraction

SCOPE = ('arithmetic consistency of written steps only (exact); correctness of the set-up (chosen relation/model) '
         'and interpretation are NOT verified')
SCALE = {'mio': 10 ** 6, 'million': 10 ** 6, 'millionen': 10 ** 6, 'mrd': 10 ** 9, 'bn': 10 ** 9, 'billion': 10 ** 9,
         'k': 10 ** 3, 'tsd': 10 ** 3}
CURRENCY = {'€': '€', 'eur': '€', 'euro': '€', '$': '$', 'usd': '$'}
_NUM = re.compile(r'\d+(?:[.,]\d+)*')
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.USub: operator.neg, ast.UAdd: operator.pos}


def _readings(tok):
    """(english, german) decimal strings for one numeral; equal when the numeral is unambiguous."""
    if re.fullmatch(r'0[.,]\d+', tok):
        v = tok.replace(',', '.'); return v, v                                 # 0.333 / 0,333: a group never starts with 0
    if re.fullmatch(r'\d{1,3}(,\d{3}){2,}(\.\d+)?|\d{1,3},\d{3}\.\d+', tok):
        return tok.replace(',', ''), tok.replace(',', '')                      # 7,700,000 / 44,466.67
    if re.fullmatch(r'\d{1,3}(\.\d{3}){2,}(,\d+)?|\d{1,3}\.\d{3},\d+', tok):
        v = tok.replace('.', '').replace(',', '.'); return v, v                # 7.700.000 / 1.234,5
    if re.fullmatch(r'\d{1,3},000', tok):
        return tok.replace(',', ''), tok.replace(',', '')                      # 300,000: a decimal ',000' is never written
    if re.fullmatch(r'\d{1,3},\d{3}', tok):
        return tok.replace(',', ''), tok.replace(',', '.')                     # 1,857: thousands or decimal comma
    if re.fullmatch(r'\d{1,3}\.\d{3}', tok):
        return tok, tok.replace('.', '')                                       # 1.234: decimal point or thousands
    if re.fullmatch(r'\d+,\d+', tok):
        v = tok.replace(',', '.'); return v, v                                 # 0,85
    if re.fullmatch(r'\d+(\.\d+)?', tok):
        return tok, tok
    return None


def _grouping(text):
    """'en' / 'de' when the text shows unambiguous thousands grouping of only one convention, else None."""
    t = _detex(str(text or ''))
    en = bool(re.search(r'\d,\d{3},\d{3}|\d,\d{3}\.\d|\d,000(?![\d.,])', t))   # ',000' is grouping, never a decimal
    de = bool(re.search(r'\d\.\d{3}\.\d{3}|\d\.\d{3},\d', t))
    return 'en' if en and not de else 'de' if de and not en else None


def _decimals(s):
    return len(s.split('.')[1]) if '.' in s else 0


def _detex(s):
    s = re.sub(r'\\(?:text|mathrm|textrm|operatorname|mbox)\{([^{}]*)\}', r' \1 ', s)
    for _ in range(3):
        s = re.sub(r'\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}', r'((\1)/(\2))', s)
    s = s.replace('{,}', ',').replace(r'\cdot', '*').replace(r'\times', '*').replace(r'\div', '/')
    s = re.sub(r'\\(?:l|c)?dots', ' … ', s).replace('...', ' … ')
    s = re.sub(r'\\left|\\right|\\[,;!: ]|\\quad|\\qquad', ' ', s)
    s = s.replace('\\%', '%').replace('\\$', '$').replace('{', '(').replace('}', ')').replace('^', '**')
    return s


class _Unknown(Exception):
    pass


def _parse(side, env, reading):
    """Tokens of one side as an exact expression; raises _Unknown(reason) when it is not purely numeric."""
    s = _detex(side).replace('×', '*').replace('·', '*').replace('÷', '/').replace('−', '-').replace('–', '-')
    s = re.sub(r'[\s.,;:]+$', '', s.strip())
    toks = re.findall(r'\d+(?:[.,]\d+)*|…|[A-Za-zÄÖÜäöü_]+|€|\$|\*\*|[-+*/()%]|\S', s)
    out, units, used, nums, trunc = [], set(), [], [], False
    for t in toks:
        prev = out[-1] if out else None
        val_before = prev is not None and (prev == ')' or prev.startswith('F('))
        if _NUM.fullmatch(t):
            r = _readings(t)
            if r is None:
                raise _Unknown('UNREADABLE_NUMBER')
            if val_before:
                out.append('*')
            out.append(f'F("{r[reading]}")'); nums.append([len(out) - 1, r[reading], 1, False])
        elif t == '…':
            trunc = True
        elif t.lower() in SCALE and nums and nums[-1][0] == len(out) - 1:
            nums[-1][2] = SCALE[t.lower()]; nums[-1][3] = True
        elif t.lower() in CURRENCY:
            units.add(CURRENCY[t.lower()])
            if nums and nums[-1][0] == len(out) - 1:
                nums[-1][3] = True                                             # this number carries a unit
        elif t == '%':
            out.append('*F(1,100)')
        elif t in env:
            if val_before:
                out.append('*')                                                # 0.15CON
            out.append(f'F({env[t].numerator},{env[t].denominator})'); used.append(t)
        elif t in ('+', '-', '*', '/', '(', ')', '**'):
            if t == '(' and val_before:
                out.append('*')                                                # implicit product (13/7)(4/3)
            out.append(t)
        elif re.fullmatch(r'[A-Za-zÄÖÜäöü_]+', t):
            raise _Unknown('UNKNOWN_SYMBOL')
        else:
            raise _Unknown('UNREADABLE_EXPRESSION')
    if not nums and not used:
        raise _Unknown('NO_NUMBER')
    return {'out': out, 'nums': nums, 'units': units, 'used': used, 'trunc': trunc}


def _evaluate(p, common_scale):
    out = list(p['out'])
    for pos, v, scale, _ in p['nums']:
        if scale != 1 and not common_scale:
            out[pos] = f'(F("{v}")*{scale})'
    tree = ast.parse(''.join(out), mode='eval')

    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'F':
            return Fraction(*[a.value for a in n.args])
        if isinstance(n, ast.Constant) and isinstance(n.value, int): return Fraction(n.value)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            b, e = ev(n.left), ev(n.right)
            if e.denominator != 1 or abs(e) > 64: raise ValueError('non-integer power')
            return b ** int(e)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS: return _OPS[type(n.op)](ev(n.operand))
        raise ValueError('not arithmetic')
    return ev(tree)


def _literal(p):
    """(decimals, percent) when a side is one plain number (with unit/scale/…), else None."""
    o = p['out']
    if len(p['nums']) == 1 and not p['used'] and o and o[0].startswith('F(') and (len(o) == 1 or o[1:] == ['*F(1,100)']):
        return _decimals(p['nums'][0][1]), len(o) == 2
    return None


def _equations(text):
    t = str(text or '')
    parts = [m.group(1) or m.group(2) for m in re.finditer(r'\\\((.+?)\\\)|\\\[(.+?)\\\]', t, re.S)]
    plain = re.sub(r'\\\((.+?)\\\)|\\\[(.+?)\\\]', '\n', t, flags=re.S)
    parts += [ln for ln in re.split(r'[\n;]|(?<=[^\d])\.\s|,\s+(?=[A-Za-z][\w]{0,10}\s*=)', plain) if '=' in ln]
    for p in parts:
        for q in re.split(r'\\q?quad|\\Rightarrow|\\implies|⇒', p):
            if not re.search(r'=|≈|\\approx', q):
                continue
            q = re.split(r':\s', q)[-1] if re.search(r'^[^=]*:\s', q) else q   # 'Answer: POM = ...'
            q = re.sub(r'^[\s,;]+|[\s,;]+$', '', q)
            sides = re.split(r'(?<![<>!=])=(?!=)|≈|\\approx', q)
            if len(sides) >= 2 and all(x.strip() for x in sides):
                yield q.strip(), sides


def _symbol(side):
    m = re.fullmatch(r'\s*([A-Za-z][A-Za-z_]{0,10})\s*', _detex(side).replace('\\', ''))
    return m.group(1) if m else None


def _chain(sides, env, reading):
    parsed, reason = [], None
    for sd in sides:
        try:
            parsed.append((sd, _parse(sd, env, reading)))
        except _Unknown as e:
            reason = reason or str(e); parsed.append((sd, None))
    known = [p for _, p in parsed if p]
    if len(set().union(*[p['units'] for p in known])) > 1 if known else False:
        raise _Unknown('UNIT_MISMATCH')
    scales = {n[2] for p in known for n in p['nums'] if n[3]}          # scales of the numbers that carry a unit
    common = len(scales) <= 1 and not any(p['used'] for p in known)   # one unit scale throughout: compare as shown
    vals = []
    for sd, p in parsed:
        try:
            vals.append((sd, _evaluate(p, common) if p else None, p))
        except (ValueError, ZeroDivisionError, SyntaxError, TypeError, OverflowError):
            vals.append((sd, None, None)); reason = reason or 'UNREADABLE_EXPRESSION'
    return vals, reason


def _verdict(vals):
    known = [x for x in vals if x[1] is not None]
    if len(known) < 2:
        return None, []
    bad = []
    for (sa, a, pa), (sb, b, pb) in zip(known, known[1:]):
        tol = Fraction(0)
        for p in (pa, pb):
            lit = _literal(p)
            if lit:
                step = Fraction(1, 10 ** lit[0]) / (100 if lit[1] else 1)
                tol = max(tol, step if p['trunc'] else step / 2)
        if abs(a - b) > tol:
            bad.append(f'{sa.strip()[:50]} = {float(a):.8g} but {sb.strip()[:50]} = {float(b):.8g}')
    return ('FAIL' if bad else 'PASS'), bad


def _check(sides, env, grouping=None):
    """(status, detail, reason, defined value or None), evaluated under both readings of ambiguous numerals unless the
    step itself shows unambiguous thousands grouping of one convention."""
    sym = _symbol(sides[0]) if len(sides) > 1 else None
    g = _grouping('='.join(sides)) or grouping
    res = []
    for reading in ((0, 0) if g == 'en' else (1, 1) if g == 'de' else (0, 1)):
        try:
            vals, reason = _chain(sides, env, reading)
        except _Unknown as e:
            return 'NOT_TESTED', 'different currencies within one step', str(e), None
        defined = None
        if sym and sym not in env and all(v is not None for _, v, _ in vals[1:]):
            defined, vals = vals[1][1], vals[1:]
        verdict, bad = _verdict(vals)
        res.append((verdict, bad, reason, defined, vals))
    (v0, b0, r0, d0, vals0), (v1, _, r1, d1, _) = res
    defined = d0 if d0 is not None and d0 == d1 else None
    if v0 is None or v1 is None:
        if defined is not None:
            return 'NOT_TESTED', 'defines a symbol from a single value', 'DEFINITION', defined
        return 'NOT_TESTED', 'fewer than two evaluable sides', r0 or r1 or 'SYMBOLIC', None
    if v0 != v1:
        return 'NOT_TESTED', 'verdict depends on reading 1,234-type numerals as thousands or decimals', 'AMBIGUOUS_NUMBER_FORMAT', None
    used = sorted({u for _, _, p in vals0 if p for u in p['used']})
    via = (' using ' + ', '.join(f'{u}={float(env[u]):.10g}' for u in used)) if used else ''
    if v0 == 'FAIL':
        return 'FAIL', '; '.join(b0), 'ARITHMETIC_MISMATCH', defined
    return 'PASS', f'{sum(v is not None for _, v, _ in vals0)} numeric sides agree (arithmetic only){via}', None, defined


def check_steps(texts, number_format=None):
    """Check a sequence of texts (problem, body, steps, result) with a shared symbol environment.
    A symbol defined anywhere in the sequence is known to every step; a definition is never checked against itself."""
    eqs = [sides for t in texts for _, sides in _equations(t)]
    labels = [eq for t in texts for eq, _ in _equations(t)]
    # evidence comes from each step itself; otherwise only from a convention the course source declares
    grouping = number_format if number_format in ('en', 'de') else None
    env, origin = {}, {}
    for _ in range(4):
        new = False
        for i, sides in enumerate(eqs):
            d = _check(sides, env, grouping)[3]
            sym = _symbol(sides[0])
            if d is not None and sym and sym not in env:
                env[sym] = d; origin[sym] = i; new = True
        if not new:
            break
    out = []
    for i, (eq, sides) in enumerate(zip(labels, eqs)):
        sym = _symbol(sides[0]) if len(sides) > 1 else None
        own = {k: v for k, v in env.items() if k != sym}
        st, detail, reason, val = _check(sides, own, grouping)
        restated = sym in env and origin.get(sym) != i              # never check the defining step against itself
        if reason == 'DEFINITION' and restated and val != env[sym] and len(sides) > 2:
            st, detail, reason = 'FAIL', f'{sym} stated as {float(val):.10g} but derived as {float(env[sym]):.10g}', 'ARITHMETIC_MISMATCH'
        elif st == 'NOT_TESTED' and restated and len(sides) == 2:
            st, detail, reason, _ = _check(sides, env, grouping)       # a restated or rounded result: compare with the derived value
            if reason == 'DEFINITION':
                st, detail, reason = 'NOT_TESTED', f'defines {sym}={float(env[sym]):.10g}', 'DEFINITION'
        out.append({'equation': eq[:160], 'status': st, 'detail': detail, 'reason': reason, 'symbol': sym})
    # a defined value is verified when every other step that uses it is arithmetically consistent with it
    for r in out:
        if r['reason'] == 'DEFINITION':
            users = [x for x in out if x is not r and r['symbol'] and f"{r['symbol']}=" in x['detail']]
            if users and r['symbol'] in env and all(x['status'] == 'PASS' for x in users):
                r.update(status='PASS', reason=None, detail=f"{r['symbol']}={float(env[r['symbol']]):.10g} satisfies {len(users)} step(s) "
                                                             f"that use it (arithmetic only)")
    for r in out:
        r.pop('symbol', None)
    return out


def check_text(text, env=None):
    """Single-text compatibility wrapper: (results, env)."""
    return check_steps([text]), dict(env or {})


DECLARED_FORMAT = [('en', re.compile(r'english number format|englische[sn]? zahlenformat', re.I)),
                   ('de', re.compile(r'german number format|deutsche[sn]? zahlenformat', re.I))]


def declared_number_format(texts):
    """'en'/'de' when the course text explicitly declares one number format (and not both), else None."""
    t = ' '.join(str(x or '') for x in texts)
    found = {k for k, rx in DECLARED_FORMAT if rx.search(t)}
    return found.pop() if len(found) == 1 else None


def summary(results):
    """Counts for reporting: recognised, verified, arithmetic failures, not checkable (with reasons)."""
    return {'recognised_steps': len(results), 'verified_pass': sum(r['status'] == 'PASS' for r in results),
            'arithmetic_fail': sum(r['status'] == 'FAIL' for r in results),
            'not_tested': sum(r['status'] == 'NOT_TESTED' for r in results),
            'not_tested_reasons': dict(Counter(r['reason'] for r in results if r['status'] == 'NOT_TESTED'))}
