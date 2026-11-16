"""Independent exact MDP oracle (B30). Shares no code with labs/models.py on purpose: rational arithmetic
(fractions.Fraction), policy evaluation by Gaussian elimination, optimality by exhaustive policy enumeration.

Input format = the lab format the author already emits: {"states":[...], "gamma": g,
"transitions":[{"s","a","r","next":{s': p}}]}. Terminal states have no transitions (value 0).

Claims (author/solutions output, list "model_claims"):
 {"claim_id","model_id","quantity": "V_pi"|"Q_pi"|"V_star"|"Q_star"|"VI_k"|"PE_k"|"greedy"|"optimal_policy",
  "state","action","policy":{s:a},"k","gamma"(optional override),"value","object_ids":[...]}
"""
from fractions import Fraction as F
from itertools import product


class OracleError(ValueError):
    pass


def _q(x):
    if isinstance(x, bool):
        raise OracleError('boolean is not a number')
    if isinstance(x, str):
        return F(x.replace(',', '.')) if '/' not in x else F(x)
    return F(str(x)) if isinstance(x, float) else F(x)


def normalise(mdp, gamma=None):
    S = list(mdp.get('states') or [])
    if not S or len(S) != len(set(S)):
        raise OracleError('states must be non-empty and unique')
    g = _q(mdp['gamma'] if gamma is None else gamma)
    if not (0 <= g < 1):
        raise OracleError('gamma must lie in [0,1) for the infinite-horizon discounted setting')
    A = {s: [] for s in S}; T = {}
    for t in mdp.get('transitions') or []:
        s, a = t['s'], t['a']
        if s not in A or a in A[s]:
            raise OracleError(f'unknown state or duplicate action {s}/{a}')
        nxt = {k: _q(v) for k, v in t['next'].items() if _q(v) != 0}
        if set(nxt) - set(S) or any(p < 0 for p in nxt.values()) or sum(nxt.values()) != 1:
            raise OracleError(f'p(.|{s},{a}) is not an exact probability distribution')
        A[s].append(a); T[s, a] = (_q(t['r']), nxt)
    return {'S': S, 'A': A, 'T': T, 'g': g}


def q_value(m, V, s, a):
    r, nxt = m['T'][s, a]
    return r + m['g'] * sum(p * V[t] for t, p in nxt.items())


def _dist(pi, s):
    d = pi[s]
    return {d: F(1)} if isinstance(d, str) else {a: _q(w) for a, w in d.items()}


def evaluate(m, pi):
    """Solve (I - g P_pi) V = r_pi exactly."""
    S = m['S']; n = len(S); idx = {s: i for i, s in enumerate(S)}
    M = [[F(0)] * (n + 1) for _ in range(n)]
    for s in S:
        i = idx[s]; M[i][i] = F(1)
        if not m['A'][s]:
            continue
        for a, w in _dist(pi, s).items():
            if a not in m['A'][s]:
                raise OracleError(f'policy chooses unavailable action {a} in {s}')
            r, nxt = m['T'][s, a]
            M[i][n] += w * r
            for t, p in nxt.items():
                M[i][idx[t]] -= w * m['g'] * p
    for c in range(n):
        piv = next(r for r in range(c, n) if M[r][c] != 0)
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return {s: M[idx[s]][n] / M[idx[s]][idx[s]] for s in S}


def deterministic_policies(m):
    dec = [s for s in m['S'] if m['A'][s]]
    for combo in product(*[m['A'][s] for s in dec]):
        yield dict(zip(dec, combo))


def optimal(m):
    """V* by enumeration (exact; exponential, fine for course-size MDPs) — returns V*, set of optimal policies."""
    best, pols = None, []
    for pi in deterministic_policies(m):
        V = evaluate(m, pi)
        if best is None or any(V[s] > best[s] for s in m['S']) and all(V[s] >= best[s] for s in m['S']):
            best, pols = V, [pi]
        elif all(V[s] == best[s] for s in m['S']):
            pols.append(pi)
    # verify Bellman optimality exactly (also guards against non-dominating enumeration order)
    for s in m['S']:
        if m['A'][s] and max(q_value(m, best, s, a) for a in m['A'][s]) != best[s]:
            raise OracleError('enumeration did not reach a Bellman-optimal value function')
    return best, pols


def sweeps(m, k, pi=None, V0=None):
    V = dict(V0) if V0 else {s: F(0) for s in m['S']}; hist = [V]
    for _ in range(k):
        W = {}
        for s in m['S']:
            if not m['A'][s]:
                W[s] = F(0)
            elif pi is None:
                W[s] = max(q_value(m, V, s, a) for a in m['A'][s])
            else:
                W[s] = sum(w * q_value(m, V, s, a) for a, w in _dist(pi, s).items())
        V = W; hist.append(V)
    return hist


def policy_iteration(m, pi0):
    pi = dict(pi0); trace = []
    for _ in range(10000):
        V = evaluate(m, pi); trace.append({'policy': dict(pi), 'V': V})
        new = {}
        for s in m['S']:
            if not m['A'][s]:
                continue
            qs = {a: q_value(m, V, s, a) for a in m['A'][s]}; b = max(qs.values())
            new[s] = pi[s] if isinstance(pi[s], str) and qs[pi[s]] == b else next(a for a in m['A'][s] if qs[a] == b)
        if new == pi:
            return trace
        pi = new
    raise OracleError('policy iteration did not terminate')


def contraction_report(m, k=25):
    """Checks ||T V - T U||_inf <= g ||V - U||_inf on VI iterates and the a-priori bound
    ||V_k - V*|| <= g^k ||V_0 - V*||, plus the a-posteriori bound ||V_k - V*|| <= g/(1-g) ||V_k - V_{k-1}||."""
    Vs, _ = optimal(m); h = sweeps(m, k); nrm = lambda X, Y: max(abs(X[s] - Y[s]) for s in m['S'])
    out = []
    for i in range(1, k + 1):
        e = nrm(h[i], Vs)
        ok1 = e <= m['g'] ** i * nrm(h[0], Vs)
        ok2 = m['g'] == 0 or e <= m['g'] / (1 - m['g']) * nrm(h[i], h[i - 1])
        out.append({'k': i, 'error': float(e), 'a_priori_ok': ok1, 'a_posteriori_ok': ok2})
    return out


def _close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def check_claim(models, c):
    if c.get('model_id') not in models:
        raise OracleError(f"claim {c.get('claim_id')}: unknown model_id {c.get('model_id')}")
    m = normalise(models[c['model_id']], c.get('gamma'))
    q, s, tol = c['quantity'], c.get('state'), float(c.get('tolerance', 0.006))
    if q == 'V_pi':
        got = evaluate(m, c['policy'])[s]
    elif q == 'Q_pi':
        got = q_value(m, evaluate(m, c['policy']), s, c['action'])
    elif q == 'V_star':
        got = optimal(m)[0][s]
    elif q == 'Q_star':
        got = q_value(m, optimal(m)[0], s, c['action'])
    elif q == 'VI_k':
        got = sweeps(m, int(c['k']))[int(c['k'])][s]
    elif q == 'PE_k':
        got = sweeps(m, int(c['k']), c['policy'])[int(c['k'])][s]
    elif q == 'optimal_policy':
        ok = any(all(p[x] == a for x, a in c['policy'].items()) for p in optimal(m)[1])
        return {'claim_id': c['claim_id'], 'status': 'PASS' if ok else 'FAIL', 'detail': f"claimed optimal policy {c['policy']}"}
    elif q == 'greedy':
        V = evaluate(m, c['policy']); qs = {a: q_value(m, V, s, a) for a in m['A'][s]}
        ok = qs[c['action']] == max(qs.values())
        return {'claim_id': c['claim_id'], 'status': 'PASS' if ok else 'FAIL', 'detail': f'Q values {{{", ".join(f"{a}: {float(v):.6g}" for a, v in qs.items())}}}'}
    else:
        raise OracleError(f'unknown quantity {q}')
    ok = _close(got, c['value'], tol)
    return {'claim_id': c['claim_id'], 'status': 'PASS' if ok else 'FAIL', 'expected_exact': str(got),
            'expected': float(got), 'claimed': c['value'], 'detail': f'{q} {s} {c.get("action", "")}'.strip()}


def boundary_checks(m_raw):
    """gamma = 0 (V* = max_a r) and gamma -> 1 (values grow, still finite for g<1)."""
    out = []
    m0 = normalise(m_raw, 0); V0, _ = optimal(m0)
    ok = all(V0[s] == (max(m0['T'][s, a][0] for a in m0['A'][s]) if m0['A'][s] else 0) for s in m0['S'])
    out.append({'check': 'GAMMA_0_MYOPIC', 'status': 'PASS' if ok else 'FAIL'})
    m9 = normalise(m_raw, F(999, 1000)); V9, _ = optimal(m9)
    rmax = max([abs(r) for r, _ in m9['T'].values()] or [0])
    ok = all(abs(V9[s]) <= rmax / (1 - m9['g']) for s in m9['S'])
    out.append({'check': 'GAMMA_NEAR_1_BOUNDED', 'status': 'PASS' if ok else 'FAIL', 'detail': f'|V*| <= Rmax/(1-g) = {float(rmax / (1 - m9["g"])):.4g}'})
    return out


def audit(models, claims, labs=()):
    """Full oracle report: model validity, claims, contraction/bounds, boundary cases, lab models."""
    rep = {'schema': 'em-mdp-oracle-v1', 'models': {}, 'claims': [], 'labs': []}
    for mid, raw in (models or {}).items():
        try:
            m = normalise(raw); Vs, pols = optimal(m)
            pi0 = {s: m['A'][s][0] for s in m['S'] if m['A'][s]}
            trace = policy_iteration(m, pi0)
            rep['models'][mid] = {'status': 'PASS', 'V_star': {s: str(v) for s, v in Vs.items()},
                                  'V_star_float': {s: round(float(v), 6) for s, v in Vs.items()},
                                  'optimal_policies': pols, 'policy_iteration_steps': len(trace),
                                  'policy_iteration_reaches_optimum': trace[-1]['V'] == Vs,
                                  'contraction': contraction_report(m, 15), 'boundary': boundary_checks(raw)}
            if not rep['models'][mid]['policy_iteration_reaches_optimum'] or not all(r['a_priori_ok'] and r['a_posteriori_ok'] for r in rep['models'][mid]['contraction']) \
                    or any(b['status'] != 'PASS' for b in rep['models'][mid]['boundary']):
                rep['models'][mid]['status'] = 'FAIL'
        except (OracleError, KeyError, ZeroDivisionError, StopIteration) as e:
            rep['models'][mid] = {'status': 'FAIL', 'error': str(e)}
    for c in claims or []:
        try:
            rep['claims'].append(check_claim(models, c))
        except (OracleError, KeyError, TypeError, ValueError) as e:
            rep['claims'].append({'claim_id': c.get('claim_id'), 'status': 'FAIL', 'detail': str(e)})
    for lab in labs or []:
        if lab.get('model') != 'mdp':
            continue
        d = lab.get('data') or {}
        try:
            m = normalise(d); Vs, _ = optimal(m)
            Vp = evaluate(m, d['policy']) if d.get('policy') else None
            rep['labs'].append({'lab_id': lab.get('lab_id'), 'status': 'PASS', 'V_star': {s: round(float(v), 6) for s, v in Vs.items()},
                                'V_pi': {s: round(float(v), 6) for s, v in Vp.items()} if Vp else None})
        except (OracleError, KeyError, ZeroDivisionError, StopIteration) as e:
            rep['labs'].append({'lab_id': lab.get('lab_id'), 'status': 'FAIL', 'detail': str(e)})
    rep['status'] = 'PASS' if all(x['status'] == 'PASS' for x in list(rep['models'].values()) + rep['claims'] + rep['labs']) else 'FAIL'
    return rep


def stage_checks(author, solutions=None):
    """Stage-gate rows (check MDP_ORACLE is critical). Silent when a chapter declares no MDP models."""
    models = author.get('models') or {}
    claims = list(author.get('model_claims') or []) + list((solutions or {}).get('model_claims') or [])
    labs = [l for l in author.get('labs') or [] if l.get('model') == 'mdp']
    if not models and not claims and not labs:
        return [], None
    rep = audit(models, claims, labs)
    rows = [{'check': 'MDP_ORACLE', 'object_id': k, 'status': v['status'], 'detail': v.get('error', 'model valid, PI=VI optimum, contraction bounds')}
            for k, v in rep['models'].items()]
    rows += [{'check': 'MDP_ORACLE', 'object_id': c['claim_id'], 'status': c['status'], 'detail': str(c.get('detail')) +
              (f" expected {c['expected']:.6g} claimed {c['claimed']}" if 'expected' in c else '')} for c in rep['claims']]
    rows += [{'check': 'MDP_ORACLE', 'object_id': l['lab_id'], 'status': l['status'], 'detail': l.get('detail', 'lab model valid')} for l in rep['labs']]
    return rows, rep
