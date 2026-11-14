"""Small, safe expression language for learner input (no eval). Mirrors templates/em_tutor.js (EMT.expr).

Grammar: sum = prod (('+'|'-') prod)*; prod = unary (('*'|'/'|implicit) unary)*; unary = '-' unary | pow;
pow = atom ('^' unary)?; atom = number | identifier | '(' sum ')'.
Notation that learners actually type is normalised first: · × − ′ subscripts, δ_o, f'(z1), decimal comma.

Equivalence is decided two ways:
- randomised identity testing (same seeded generator as the browser): evaluate both expressions at 12 points;
  agreement at all points of two rational functions of this size is overwhelming evidence of identity,
  but it is a probabilistic check (labelled RANDOMIZED_IDENTITY_TEST);
- exact symbolic check with sympy where available (Python side, used in tests and in the CLI).
"""
import math
import re

SUB = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')


class ExprError(ValueError):
    pass


def normalise(s, aliases=None):
    s = (s or '').strip().translate(SUB)
    for a, b in (('·', '*'), ('×', '*'), ('⋅', '*'), ('−', '-'), ('–', '-'), ('′', "'"), ('’', "'"), ('²', '^2'), ('δ', 'delta'), ('Δ', 'delta')):
        s = s.replace(a, b)
    s = re.sub(r"\b([fg])'\s*\(\s*z_?o\s*\)", r'\1po', s)       # g'(z_o) -> gpo
    s = re.sub(r"\b([fg])'\s*\(\s*z_?(\d)\s*\)", r'\1p\2', s)   # f'(z1) -> fp1
    s = re.sub(r"\bsigma'\s*\(\s*z_?(\d)\s*\)", r'fp\1', s)
    s = re.sub(r'\bdelta_?o\b|\bdeltao\b', 'delta_o', s)
    s = re.sub(r'\bdelta_?(\d)\b', r'delta_\1', s)
    s = re.sub(r'(\d),(\d)', r'\1.\2', s)
    for a, b in (aliases or {}).items():
        s = re.sub(r'\b' + re.escape(a) + r'\b', b, s)
    return s


TOK = re.compile(r'\s*(?:(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z_0-9]*)|(.))')


def tokens(s):
    out = []
    for m in TOK.finditer(s):
        num, ident, op = m.groups()
        if num is not None:
            out.append(('n', float(num)))
        elif ident is not None:
            out.append(('v', ident))
        elif op is not None and op.strip():
            if op not in '+-*/^()':
                raise ExprError(f'Unerlaubtes Zeichen: {op}')
            out.append(('o', op))
    return out


def parse(s, variables, aliases=None):
    """Returns an AST (nested tuples). Raises ExprError for syntax errors or unknown symbols."""
    ts = tokens(normalise(s, aliases)); i = [0]
    if not ts:
        raise ExprError('Leere Eingabe')
    peek = lambda: ts[i[0]] if i[0] < len(ts) else ('e', None)

    def take():
        t = peek(); i[0] += 1; return t

    def atom():
        t = take()
        if t[0] == 'n':
            return ('n', t[1])
        if t[0] == 'v':
            if t[1] not in variables:
                raise ExprError(f'Unbekanntes Symbol: {t[1]}')
            return ('v', t[1])
        if t == ('o', '('):
            e = sum_()
            if take() != ('o', ')'):
                raise ExprError('Klammer nicht geschlossen')
            return e
        raise ExprError('Ausdruck unvollständig')

    def pow_():
        b = atom()
        if peek() == ('o', '^'):
            take(); return ('^', b, unary())
        return b

    def unary():
        if peek() == ('o', '-'):
            take(); return ('neg', unary())
        if peek() == ('o', '+'):
            take(); return unary()
        return pow_()

    def prod():
        e = unary()
        while True:
            t = peek()
            if t in (('o', '*'), ('o', '/')):
                take(); e = (t[1], e, unary())
            elif t[0] in ('n', 'v') or t == ('o', '('):
                e = ('*', e, unary())          # implicit multiplication: 2a, a1(1-a1)
            else:
                return e

    def sum_():
        e = prod()
        while peek() in (('o', '+'), ('o', '-')):
            op = take()[1]; e = (op, e, prod())
        return e
    e = sum_()
    if i[0] != len(ts):
        raise ExprError('Unerwartetes Zeichen nach dem Ausdruck')
    return e


def evaluate(ast, env):
    k = ast[0]
    if k == 'n':
        return ast[1]
    if k == 'v':
        return env[ast[1]]
    if k == 'neg':
        return -evaluate(ast[1], env)
    a, b = evaluate(ast[1], env), evaluate(ast[2], env)
    if k == '+': return a + b
    if k == '-': return a - b
    if k == '*': return a * b
    if k == '/': return a / b if b != 0 else math.nan
    if k == '^':
        try:
            return a ** b
        except (OverflowError, ZeroDivisionError):
            return math.nan
    raise ExprError(k)


def symbols(ast, acc=None):
    acc = set() if acc is None else acc
    if ast[0] == 'v':
        acc.add(ast[1])
    elif ast[0] in ('+', '-', '*', '/', '^'):
        symbols(ast[1], acc); symbols(ast[2], acc)
    elif ast[0] == 'neg':
        symbols(ast[1], acc)
    return acc


def mulberry32(seed):
    """Same generator as the browser (EMT.rng): identical sample points on both sides."""
    M = 0xFFFFFFFF
    imul = lambda x, y: (x * y) & M
    a = [seed & M]

    def nxt():
        a[0] = (a[0] + 0x6D2B79F5) & M
        x = a[0]
        t = imul(x ^ (x >> 15), 1 | x)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & M) ^ t
        return ((t ^ (t >> 14)) & M) / 4294967296
    return nxt


def sample_points(variables, defs=None, n=12, seed=20261110):
    """defs: {name: expression string in other variables} for derived symbols (e.g. fp1 = a1*(1-a1))."""
    r = mulberry32(seed); pts = []
    base = sorted(v for v in variables if v not in (defs or {}))
    for _ in range(n):
        env = {v: 0.15 + 0.8 * r() for v in base}
        for k, d in (defs or {}).items():
            env[k] = evaluate(parse(d, base), env)
        pts.append(env)
    return pts


def same(f_ast, g_ast, points, rel=1e-9):
    for env in points:
        a, b = evaluate(f_ast, env), evaluate(g_ast, env)
        if not (math.isfinite(a) and math.isfinite(b)):
            return False
        if abs(a - b) > rel * max(1.0, abs(a), abs(b)):
            return False
    return True


def ratio_constant(f_ast, g_ast, points, rel=1e-9):
    """If f = k * g at every point, returns k (else None)."""
    k = None
    for env in points:
        a, b = evaluate(f_ast, env), evaluate(g_ast, env)
        if not math.isfinite(a) or not math.isfinite(b) or abs(b) < 1e-12:
            return None
        q = a / b
        if k is None:
            k = q
        elif abs(q - k) > rel * max(1.0, abs(k)):
            return None
    return k


def to_sympy(ast, defs=None):
    """Exact symbolic form (derived symbols substituted). Python only."""
    import sympy as sp

    def go(a):
        k = a[0]
        if k == 'n':
            return sp.nsimplify(a[1])
        if k == 'v':
            if defs and a[1] in defs:
                return go(parse(defs[a[1]], set(_free(defs))))
            return sp.Symbol(a[1])
        if k == 'neg':
            return -go(a[1])
        x, y = go(a[1]), go(a[2])
        return {'+': x + y, '-': x - y, '*': x * y, '/': x / y, '^': x ** y}[k]
    return go(ast)


def _free(defs):
    s = set()
    for d in defs.values():
        s |= set(re.findall(r'[A-Za-z_][A-Za-z_0-9]*', d))
    return s


def exact_equal(a, b, defs=None):
    import sympy as sp
    return sp.simplify(to_sympy(a, defs) - to_sympy(b, defs)) == 0
