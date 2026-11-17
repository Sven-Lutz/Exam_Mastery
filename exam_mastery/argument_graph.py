"""B35 Mathematical argument graph and proof audit (domain-neutral; used by any formal-mathematical competency).

Why: V4 derivations were (equation, short reason) chains. A step like "Kontraktion von T^pi, dann Dreiecksungleichung"
names a rule but not which assumption makes it valid, which earlier steps it rests on, or whether it is an identity,
an implication or an approximation. Such chains can look complete and still hide the decisive inference.

Representation
  graph = {id, claim: {statement, kind: theorem|lemma|derivation, assumptions: [aid]},
           assumptions: {aid: text}, definitions: {did: text}, notation: [symbols],
           steps: [{id, from, to, relation, rule, uses_assumptions: [aid], uses_definitions: [did], depends_on: [sid],
                    justification, interpretation, pitfall, check: {method, ...}, source}],
           counterexamples: {aid: text}}            # what fails without the assumption
  relation in IDENTITY (algebraic, holds unconditionally), IMPLICATION (proved under the named assumptions),
              EQUIVALENCE, APPROXIMATION, EMPIRICAL (observed in data/simulation), INTUITION (didactic only)

Proof audit (automatable parts of the ten audit questions; the others stay human review):
  A1 every step has a rule AND a justification (a numbered step without a reason is not a derivation)
  A2 dependencies point to earlier steps only (acyclic, no forward reference)
  A3 every assumption used by a step is declared in the claim (hidden premise -> FAIL)
  A4 every claim assumption is used somewhere (else WARN: superfluous or usage not shown)
  A5 a theorem/lemma chain contains no APPROXIMATION/EMPIRICAL/INTUITION step (exact vs approximate mixed -> FAIL)
  A6 symbolic checks (SymPy) run and must pass; a general IMPLICATION/EQUIVALENCE backed only by numeric tests FAILs
  A9 symbols in a step that are not in the declared notation (WARN)
  A7 the last step's target is the claim statement; every step is reachable from the conclusion (else WARN: dead step)
  A8 each claim assumption has a counterexample showing why it is needed (WARN if missing; Advanced level)
Support is reported per step as a list of TIERS, each named for what it is: FORMAL_VERIFIED (only from a recorded
proof-assistant run), SYMBOLIC_CHECKED / SYMBOLIC_PARTIAL (SymPy checked all / part of the step's algebra),
ANALYTIC_ARGUMENT (written proof with named premises: readable, not machine-checked), NUMERIC_TESTED (random
instances: a test, never a proof), MODEL_REVIEWED / HUMAN_REVIEWED (recorded reviews), UNCHECKED.
A whole proof is never reported as machine-verified.
"""
from __future__ import annotations

RELATIONS = ('IDENTITY', 'IMPLICATION', 'EQUIVALENCE', 'APPROXIMATION', 'EMPIRICAL', 'INTUITION')
EXACT = {'IDENTITY', 'IMPLICATION', 'EQUIVALENCE'}


def _sympy_check(chk):
    import sympy as sp
    syms = {s: sp.Symbol(s, **(chk.get('assume', {}).get(s, {}))) for s in chk.get('symbols', [])}
    lhs, rhs = sp.sympify(chk['lhs'], locals=syms), sp.sympify(chk['rhs'], locals=syms)
    rel = chk.get('rel', '==')
    if rel == '==':
        return sp.simplify(lhs - rhs) == 0
    d = sp.simplify(rhs - lhs) if rel == '<=' else sp.simplify(lhs - rhs)
    return bool(d.is_nonnegative)


def _prop_invertible_I_minus_gP(rng):
    """random row-stochastic P (2..6 states), g in [0, 0.999]: I - gP must be non-singular"""
    import numpy as np
    n = rng.randint(2, 6); P = np.array([[rng.random() for _ in range(n)] for _ in range(n)]); P /= P.sum(1, keepdims=True)
    return abs(np.linalg.det(np.eye(n) - rng.uniform(0, 0.999) * P)) > 1e-12


PROPERTIES = {'invertible_I_minus_gP': _prop_invertible_I_minus_gP}   # generic math properties, data refers by name


def _numeric_check(chk):
    import random
    f = chk['fn'] if callable(chk.get('fn')) else PROPERTIES[chk['property']]
    rng = random.Random(chk.get('seed', 0))
    n = chk.get('trials', 200)
    return all(f(rng) for _ in range(n)), n


TIERS = ('FORMAL_VERIFIED', 'SYMBOLIC_CHECKED', 'SYMBOLIC_PARTIAL', 'ANALYTIC_ARGUMENT', 'NUMERIC_TESTED',
         'MODEL_REVIEWED', 'HUMAN_REVIEWED', 'UNCHECKED')


def _tiers(s, sym):
    """Every kind of support a step actually has, each named for what it is. FORMAL_VERIFIED only from a recorded
    proof-assistant run; ANALYTIC_ARGUMENT = a written proof with named premises (readable, NOT machine-checked);
    reviews count only as recorded ({'by': 'model'|'human', 'verdict': 'ok'})."""
    t = []
    if (s.get('formal') or {}).get('checked') is True:
        t.append('FORMAL_VERIFIED (' + s['formal'].get('system', '?') + ')')
    if sym:
        t.append(sym)
    if s.get('relation') == 'IDENTITY' and sym == 'SYMBOLIC_CHECKED':
        pass
    elif s.get('proof') or (s.get('relation') in EXACT and len((s.get('justification') or '').split()) >= 4):
        t.append('ANALYTIC_ARGUMENT' + (' (sub-proof %d steps)' % len(s['proof']) if s.get('proof') else ''))
    for r in s.get('reviews', []):
        if r.get('verdict') == 'ok':
            t.append('HUMAN_REVIEWED' if r.get('by') == 'human' else 'MODEL_REVIEWED')
    return t or ['UNCHECKED']


def audit(g):
    """Return {'status', 'findings': [{code, severity, step, msg}], 'verification': {step: reach}}."""
    F, ver = [], {}
    def f(code, sev, step, msg):
        F.append({'code': code, 'severity': sev, 'step': step, 'msg': msg})
    claim, steps = g['claim'], g.get('steps', [])
    declared = set(claim.get('assumptions', []))
    known_a, known_d = set(g.get('assumptions', {})), set(g.get('definitions', {}))
    for a in declared - known_a:
        f('A3', 'FAIL', None, f'claim assumption {a} is not defined')
    seen, used_a = set(), set()
    for s in steps:
        sid = s.get('id')
        if s.get('relation') not in RELATIONS:
            f('A1', 'FAIL', sid, f'unknown relation {s.get("relation")!r}')
        if not (s.get('rule') or '').strip() or len((s.get('justification') or '').split()) < 4:
            f('A1', 'FAIL', sid, 'step without rule or real justification')
        for d in s.get('depends_on', []):
            if d not in seen:
                f('A2', 'FAIL', sid, f'depends on {d}, which is not an earlier step')
        for a in s.get('uses_assumptions', []):
            used_a.add(a)
            if a not in declared:
                f('A3', 'FAIL', sid, f'uses assumption {a} that the claim does not state (hidden premise)')
        for d in s.get('uses_definitions', []):
            if d not in known_d:
                f('A3', 'FAIL', sid, f'uses undefined definition {d}')
        if claim.get('kind') in ('theorem', 'lemma') and s.get('relation') not in EXACT:
            f('A5', 'FAIL', sid, f'{s.get("relation")} step inside a {claim["kind"]}: exact and approximate/empirical reasoning mixed')
        chk = s.get('check') or {}
        m = chk.get('method')
        if m == 'sympy':
            try:
                ok = _sympy_check(chk)
            except Exception as e:                                           # an unparsable check is a failed check
                ok = False; f('A6', 'FAIL', sid, f'symbolic check not executable: {e}')
            sym = ('SYMBOLIC_CHECKED' if chk.get('scope', 'full') == 'full' else 'SYMBOLIC_PARTIAL') if ok else 'SYMBOLIC_FAILED'
            if not ok:
                f('A6', 'FAIL', sid, 'symbolic check fails')
        elif m == 'numeric':
            ok, n = _numeric_check(chk)
            sym = f'NUMERIC_TESTED ({n} random instances; a test, not a proof)' if ok else 'NUMERIC_COUNTEREXAMPLE'
            if not ok:
                f('A6', 'FAIL', sid, 'numeric property check found a counterexample')
        else:
            sym = None
        if m == 'numeric' and s.get('relation') in ('IMPLICATION', 'EQUIVALENCE') and not s.get('proof'):
            f('A6', 'FAIL', sid, 'general claim backed only by numeric tests: an analytic proof ("proof": [...]) is required')
        ver[sid] = _tiers(s, sym)
        seen.add(sid)
    from .answerability import _symbols
    known_sym = set(g.get('notation', []))
    if known_sym:
        for s in steps:
            for fld in ('from', 'to'):
                bad = sorted(_symbols(s.get(fld) or '') - known_sym)
                if bad:
                    f('A9', 'WARN', s['id'], f'{fld}: symbols not in the declared notation: {", ".join(bad)}')
    for a in declared - used_a:
        f('A4', 'WARN', None, f'assumption {a} is never used by a step (superfluous, or its use is not shown)')
    if steps and (steps[-1].get('to') or '').strip() != (claim.get('statement') or '').strip():
        f('A7', 'FAIL', steps[-1].get('id'), 'last step does not arrive at the claim statement')
    if steps:                                                                # reachability from the conclusion
        by, live, todo = {s['id']: s for s in steps}, set(), [steps[-1]['id']]
        while todo:
            x = todo.pop()
            if x in live or x not in by:
                continue
            live.add(x); todo += by[x].get('depends_on', [])
        for s in steps:
            if s['id'] not in live:
                f('A7', 'WARN', s['id'], 'step does not contribute to the conclusion')
    for a in declared:
        if a not in g.get('counterexamples', {}):
            f('A8', 'WARN', None, f'no counterexample showing why assumption {a} is needed')
    return {'status': 'FAIL' if any(x['severity'] == 'FAIL' for x in F) else 'WARN' if F else 'PASS',
            'findings': F, 'verification': ver,
            'scope': 'structure, declared premises, exact/approximate separation, executable step checks; the '
                     'mathematical validity of IMPLICATION steps is NOT machine-verified and needs a human reviewer'}


def matrix(g):
    """Argument/dependency matrix rows for publishing and review: one row per step."""
    return [{'step': s['id'], 'relation': s['relation'], 'rule': s.get('rule', ''), 'assumptions': ', '.join(s.get('uses_assumptions', [])),
             'definitions': ', '.join(s.get('uses_definitions', [])), 'depends_on': ', '.join(s.get('depends_on', [])),
             'check': (s.get('check') or {}).get('method', '—')} for s in g.get('steps', [])]
