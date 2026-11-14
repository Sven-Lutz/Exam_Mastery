"""Structured diagnosis (schema em-diagnosis-v1). Deterministic; mirrors templates/em_tutor.js (EMT.diagnose).

Levels (the 'method' of a diagnosis):
  numeric      L1  value, tolerance, unit scale, sign, known wrong values (bug library)
  expression   L2  algebraic equivalence by randomised identity testing; known wrong expressions (missing factor ...)
  steps        L3  each intermediate result checked; the first wrong step is located (model tracing, reduced)
  choice /
  constraints  L4  conceptual choice with one misconception per option; argument checked against constraints
                   (constraint-based modelling: relevance condition -> satisfaction condition)
  open         L5  free text: never graded here -> result UNVERIFIED, offered to the tutor (model judgement)

There is no confidence number. 'evidence' names what the verdict rests on:
  DETERMINISTIC             exact rule on the given input
  RANDOMIZED_IDENTITY_TEST  expression agreed/disagreed at 12 random points (probabilistic, see expr.py)
  UNVERIFIED                nothing checked
A recognised error category is a hypothesis about the cause that fits the observed answer; the same wrong value can
arise from another slip. Feedback therefore names the category as 'likely' and asks for the learner's own check.
"""
import math
import re

from . import expr as X

SCHEMA = 'em-diagnosis-v1'
UNIT_WORDS = re.compile(r'(k€|t€|€|eur|euro|tsd\.?|prozent|%)', re.I)


def parse_number(s):
    """German and English notation: '2.144' (thousands) = 2144, '2144,5', '-0,25', '2 144'. Returns float or None."""
    if s is None:
        return None
    t = UNIT_WORDS.sub('', str(s)).strip().replace(' ', '').replace(' ', '').replace('−', '-')
    if not t:
        return None
    if re.fullmatch(r'[-+]?\d{1,3}(\.\d{3})+(,\d+)?', t):
        t = t.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[-+]?\d{1,3}(,\d{3})+(\.\d+)?', t) and t.count(',') >= 1 and '.' in t:
        t = t.replace(',', '')
    else:
        t = t.replace(',', '.')
    try:
        v = float(t)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def _out(task, observed, method, result, category, evidence, detail='', correct_steps=None):
    return {'schema': SCHEMA, 'task_id': task['id'], 'kc_id': task['kc_id'], 'observed': observed, 'method': method,
            'result': result, 'error_category': category, 'evidence': evidence, 'detail': detail,
            'correct_steps': correct_steps or []}


def _numeric(task, raw, spec=None):
    spec = spec or task
    v = parse_number(raw)
    if v is None:
        return 'invalid', None, 'Keine Zahl erkannt.'
    exp, tol = spec['expected'], spec.get('tolerance', 1e-6)
    if abs(v - exp) <= tol:
        return 'correct', None, ''
    for e in spec.get('errors', []):
        if abs(v - e['value']) <= tol:
            return 'incorrect', e['category'], ''
    if exp != 0 and abs(abs(v) - abs(exp)) <= tol:
        return 'incorrect', 'sign_error', ''
    for f in (1000, 0.001, 100, 0.01):
        if exp != 0 and abs(v - exp * f) <= tol * max(1, abs(f)):
            return 'incorrect', 'unit_scale', f'Faktor {f:g}'
    if abs(v - exp) <= 10 * tol:
        return 'partial', 'rounding', 'Abweichung nur in der Rundung.'
    return 'incorrect', 'unclassified', ''


def diagnose(task, answer):
    """answer: str (numeric/expression/open), dict step_id -> str (steps), str option (choice), list of ids (constraints)."""
    t = task['type']
    if t == 'numeric':
        r, cat, d = _numeric(task, answer)
        if r == 'invalid':
            return _out(task, answer, 'numeric', 'invalid', None, 'DETERMINISTIC', d)
        return _out(task, answer, 'numeric', r, cat, 'DETERMINISTIC', d)
    if t == 'expression':
        vs = set(task['variables'])
        try:
            f = X.parse(answer, vs)
        except X.ExprError as e:
            return _out(task, answer, 'expression', 'invalid', None, 'DETERMINISTIC', str(e))
        pts = X.sample_points(vs, task.get('defs'))
        g = X.parse(task['expected_expr'], vs)
        bad = [env for env in pts if not math.isfinite(X.evaluate(f, env))]
        if bad:   # division by zero / undefined at a sample point: no verdict on equivalence
            return _out(task, answer, 'expression', 'invalid', None, 'DETERMINISTIC', 'Ausdruck ist an Prüfstellen nicht definiert (z. B. Division durch null).')
        if X.same(f, g, pts):
            return _out(task, answer, 'expression', 'correct', None, 'RANDOMIZED_IDENTITY_TEST')
        for b in task.get('bugs', []):
            if X.same(f, X.parse(b['expr'], vs), pts):
                return _out(task, answer, 'expression', 'incorrect', b['category'], 'RANDOMIZED_IDENTITY_TEST')
        k = X.ratio_constant(f, g, pts)
        if k is not None and abs(k + 1) < 1e-9:
            return _out(task, answer, 'expression', 'incorrect', 'sign_error', 'RANDOMIZED_IDENTITY_TEST')
        if k is not None:
            return _out(task, answer, 'expression', 'partial', 'constant_factor', 'RANDOMIZED_IDENTITY_TEST', f'Faktor {k:.4g}')
        return _out(task, answer, 'expression', 'incorrect', 'unclassified', 'RANDOMIZED_IDENTITY_TEST')
    if t == 'steps':
        ok, first = [], None
        for s in task['steps']:
            r, cat, _ = _numeric(task, (answer or {}).get(s['id']), s)
            if r == 'correct':
                ok.append(s['id'])
            elif first is None:
                first = (s, r, cat)
        if first is None:
            return _out(task, answer, 'steps', 'correct', None, 'DETERMINISTIC', correct_steps=ok)
        s, r, cat = first
        cat = cat if cat not in (None, 'unclassified') else s.get('default_category', 'unclassified')
        return _out(task, answer, 'steps', 'invalid' if r == 'invalid' else 'partial' if ok else 'incorrect', cat, 'DETERMINISTIC',
                    f'erster abweichender Schritt: {s["label"]}', correct_steps=ok)
    if t == 'choice':
        opt = next((o for o in task['options'] if o['value'] == answer), None)
        if opt is None:
            return _out(task, answer, 'choice', 'invalid', None, 'DETERMINISTIC', 'Keine Option gewählt.')
        if answer == task['correct']:
            return _out(task, answer, 'choice', 'correct', None, 'DETERMINISTIC')
        return _out(task, answer, 'choice', 'incorrect', opt.get('category', 'unclassified'), 'DETERMINISTIC')
    if t == 'constraints':
        sel = set(answer or [])
        if not sel:
            return _out(task, answer, 'constraints', 'invalid', None, 'DETERMINISTIC', 'Keine Voraussetzung gewählt.')
        violated = [c for c in task['constraints'] if (c['kind'] == 'requires' and c['premise'] not in sel) or (c['kind'] == 'forbids' and c['premise'] in sel)]
        if not violated:
            return _out(task, sorted(sel), 'constraints', 'correct', None, 'DETERMINISTIC')
        satisfied = [c['id'] for c in task['constraints'] if c not in violated]
        return _out(task, sorted(sel), 'constraints', 'partial' if satisfied else 'incorrect', violated[0]['category'], 'DETERMINISTIC',
                    'verletzt: ' + ', '.join(c['id'] for c in violated), correct_steps=satisfied)
    if t == 'open':
        return _out(task, answer, 'open', 'unverified', None, 'UNVERIFIED', 'Freitext wird nicht automatisch bewertet.')
    raise ValueError(f'unknown task type {t}')
