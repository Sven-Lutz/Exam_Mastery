"""Reference models of the interactive labs (B13). Pure Python, no dependencies.

The browser runtime (templates/em_labs.js) implements the same models; tests run both on the same inputs and require
identical results. Every lab task's expected answer is computed here, never typed into a spec by hand.
"""
import math
import random


# ------------------------------------------------------------------ cash flow / liquidity

def cashflow(orders, delay, cost, invest, start_cash=0.0, horizon=None):
    """Period model (periods 1..T). A customer order of period t is paid in period t + delay.
    orders, cost, invest: lists per period (missing entries count as 0). Returns all series and the key figures.
    - inflow_t   = orders_{t-delay}
    - outflow_t  = cost_t + invest_t
    - cf_t       = inflow_t - outflow_t
    - balance_t  = start_cash + sum_{s<=t} cf_s           (cumulative liquidity)
    - min_balance = min_t balance_t ; financing_need = max(0, -min_balance)
    - first_shortfall = first t with balance_t < 0 (None if never)
    """
    if delay < 0 or int(delay) != delay:
        raise ValueError('delay must be a non-negative integer number of periods')
    T = int(horizon or max(len(orders), len(cost), len(invest)))
    if T <= 0:
        raise ValueError('horizon must be positive')
    g = lambda xs, i: float(xs[i]) if 0 <= i < len(xs) else 0.0
    inflow = [g(orders, t - int(delay)) for t in range(T)]
    outflow = [g(cost, t) + g(invest, t) for t in range(T)]
    cf = [a - b for a, b in zip(inflow, outflow)]
    bal, s = [], float(start_cash)
    for x in cf:
        s += x
        bal.append(s)
    m = min(bal)
    k = min(range(T), key=lambda t: (bal[t], t))
    return {'inflow': inflow, 'outflow': outflow, 'cf': cf, 'balance': bal, 'min_balance': m,
            'min_period': k + 1, 'final_balance': bal[-1], 'financing_need': max(0.0, -m),
            'first_shortfall': next((t + 1 for t, b in enumerate(bal) if b < 0), None),
            'unpaid_orders': sum(g(orders, t) for t in range(T) if t + int(delay) >= T)}


# ------------------------------------------------------------------ small neural network (2-H-1, MSE)

ACT = {
    'sigmoid': (lambda z: 1 / (1 + math.exp(-z)), lambda z, a: a * (1 - a)),
    'tanh': (math.tanh, lambda z, a: 1 - a * a),
    'relu': (lambda z: max(0.0, z), lambda z, a: 1.0 if z > 0 else 0.0),
    'linear': (lambda z: z, lambda z, a: 1.0),
}


def mlp_forward(p, x, hidden_act='sigmoid', out_act='sigmoid'):
    """p = {'W1': [[w_j1, w_j2] for each hidden j], 'b1': [b_j], 'W2': [v_j], 'b2': c}.
    z_j = sum_i W1[j][i] x_i + b1[j]; a_j = f(z_j); z_o = sum_j W2[j] a_j + b2; y = g(z_o)."""
    f, g = ACT[hidden_act][0], ACT[out_act][0]
    z1 = [sum(w * xi for w, xi in zip(row, x)) + b for row, b in zip(p['W1'], p['b1'])]
    a1 = [f(z) for z in z1]
    zo = sum(v * a for v, a in zip(p['W2'], a1)) + p['b2']
    return {'z1': z1, 'a1': a1, 'zo': zo, 'y': g(zo)}


def mlp_loss(y, t):
    """Squared error L = 1/2 (y - t)^2 (the 1/2 makes dL/dy = y - t)."""
    return 0.5 * (y - t) ** 2


def mlp_backward(p, x, t, hidden_act='sigmoid', out_act='sigmoid'):
    """Exact gradients by the chain rule. delta_o = (y-t) g'(z_o); dL/dW2_j = delta_o a_j; dL/db2 = delta_o;
    delta_j = delta_o W2_j f'(z_j); dL/dW1_ji = delta_j x_i; dL/db1_j = delta_j."""
    fw = mlp_forward(p, x, hidden_act, out_act)
    dg, df = ACT[out_act][1], ACT[hidden_act][1]
    d_o = (fw['y'] - t) * dg(fw['zo'], fw['y'])
    dW2 = [d_o * a for a in fw['a1']]
    d_h = [d_o * v * df(z, a) for v, z, a in zip(p['W2'], fw['z1'], fw['a1'])]
    dW1 = [[dj * xi for xi in x] for dj in d_h]
    return {'forward': fw, 'loss': mlp_loss(fw['y'], t), 'delta_o': d_o, 'delta_h': d_h,
            'grad': {'W1': dW1, 'b1': list(d_h), 'W2': dW2, 'b2': d_o}}


def mlp_step(p, x, t, lr, hidden_act='sigmoid', out_act='sigmoid'):
    """One gradient-descent step: theta <- theta - lr * dL/dtheta."""
    bw = mlp_backward(p, x, t, hidden_act, out_act)
    g = bw['grad']
    q = {'W1': [[w - lr * gw for w, gw in zip(row, grow)] for row, grow in zip(p['W1'], g['W1'])],
         'b1': [b - lr * gb for b, gb in zip(p['b1'], g['b1'])],
         'W2': [v - lr * gv for v, gv in zip(p['W2'], g['W2'])], 'b2': p['b2'] - lr * g['b2']}
    return q, bw


def mlp_train(p, x, t, lr, steps, hidden_act='sigmoid', out_act='sigmoid'):
    losses = []
    for _ in range(steps):
        p, bw = mlp_step(p, x, t, lr, hidden_act, out_act)
        losses.append(bw['loss'])
    losses.append(mlp_loss(mlp_forward(p, x, hidden_act, out_act)['y'], t))
    return p, losses


def mlp_numeric_grad(p, x, t, eps=1e-6, hidden_act='sigmoid', out_act='sigmoid'):
    """Central finite differences for every parameter (independent check of backpropagation)."""
    def L(q):
        return mlp_loss(mlp_forward(q, x, hidden_act, out_act)['y'], t)

    def copy(q):
        return {'W1': [list(r) for r in q['W1']], 'b1': list(q['b1']), 'W2': list(q['W2']), 'b2': q['b2']}
    out = {'W1': [[0.0] * len(r) for r in p['W1']], 'b1': [0.0] * len(p['b1']), 'W2': [0.0] * len(p['W2']), 'b2': 0.0}
    for j, row in enumerate(p['W1']):
        for i in range(len(row)):
            a, b = copy(p), copy(p)
            a['W1'][j][i] += eps; b['W1'][j][i] -= eps
            out['W1'][j][i] = (L(a) - L(b)) / (2 * eps)
    for key in ('b1', 'W2'):
        for j in range(len(p[key])):
            a, b = copy(p), copy(p)
            a[key][j] += eps; b[key][j] -= eps
            out[key][j] = (L(a) - L(b)) / (2 * eps)
    a, b = copy(p), copy(p)
    a['b2'] += eps; b['b2'] -= eps
    out['b2'] = (L(a) - L(b)) / (2 * eps)
    return out


def mlp_init(hidden=2, inputs=2, seed=7, scale=0.8):
    """Reproducible initial weights (Python's Mersenne Twister with a fixed seed)."""
    r = random.Random(seed)
    u = lambda: round(r.uniform(-scale, scale), 3)
    return {'W1': [[u() for _ in range(inputs)] for _ in range(hidden)], 'b1': [u() for _ in range(hidden)],
            'W2': [u() for _ in range(hidden)], 'b2': u()}


# ------------------------------------------------------------------ ordinal risk matrix vs. expected value

# Cell classes of the lecture's matrix (slide 29, read from the figure by the agent; rows = likelihood 1..5,
# columns = consequence 1..5). The class depends on the cell, not on the product alone (10 is High at (2,5) but
# Moderate at (5,2)).
LECTURE_CLASSES = [['Low', 'Low', 'Low', 'Moderate', 'Moderate'],
                   ['Low', 'Low', 'Moderate', 'Moderate', 'High'],
                   ['Low', 'Moderate', 'Moderate', 'High', 'High'],
                   ['Low', 'Moderate', 'High', 'High', 'Critical'],
                   ['Moderate', 'Moderate', 'High', 'Critical', 'Critical']]
CLASS_RANK = {'Low': 1, 'Moderate': 2, 'High': 3, 'Critical': 4}


def risk_matrix(likelihood, impact, classes=None):
    """Ordinal heuristic of the lecture: score = consequence level x likelihood level (both 1..5); the class is read
    from the cell of the class table (default: the lecture's matrix)."""
    for v in (likelihood, impact):
        if v not in (1, 2, 3, 4, 5):
            raise ValueError('levels are integers 1..5')
    t = classes or LECTURE_CLASSES
    return {'score': likelihood * impact, 'class': t[likelihood - 1][impact - 1]}


# Likelihood bands of the lecture (slide 31), as probability intervals.
LIKELIHOOD_BANDS = {1: (0.0, 0.05), 2: (0.05, 0.30), 3: (0.30, 0.70), 4: (0.70, 0.95), 5: (0.95, 1.0)}


def expected_loss_range(likelihood, loss_eur):
    """Quantitative comparison: expected loss E = p * loss for the probability band of a likelihood level.
    Shows why equal ordinal scores can hide very different expected losses."""
    lo, hi = LIKELIHOOD_BANDS[likelihood]
    return (lo * loss_eur, hi * loss_eur)


# ------------------------------------------------------------------ Van Westendorp price sensitivity meter (PSM)

PSM_KEYS = ('tc', 'cheap', 'exp', 'te')   # too cheap (quality doubts), cheap/bargain, expensive but acceptable, too expensive
# Crossings per convention. 'standard' uses complementary border curves (R pricesensitivitymeter original);
# 'alternative' uses raw curves (narrower). Lecture associations are declared separately through source anchors.
PSM_CROSSINGS = {'standard': {'pmc': ('tc', 'not_cheap'), 'opp': ('tc', 'te'), 'ipp': ('cheap', 'exp'), 'pme': ('te', 'not_exp')},
                 'alternative': {'pmc': ('tc', 'exp'), 'opp': ('tc', 'te'), 'ipp': ('cheap', 'exp'), 'pme': ('te', 'cheap')}}
_EPS = 1e-9


def psm_clean(rows):
    """A respondent is valid if all four prices are finite and positive and 0 < tc <= cheap <= exp <= te.
    Returns (valid rows, 1-based numbers of the invalid rows)."""
    valid, invalid = [], []
    for n, r in enumerate(rows, 1):
        try:
            if any(isinstance(r[k], bool) for k in PSM_KEYS):
                raise ValueError('boolean price')
            v = [float(r[k]) for k in PSM_KEYS]
        except (KeyError, TypeError, ValueError):
            invalid.append(n); continue
        if all(math.isfinite(x) and x > 0 for x in v) and v[0] <= v[1] <= v[2] <= v[3]:
            valid.append(dict(r, **dict(zip(PSM_KEYS, v))))
        else:
            invalid.append(n)
    return valid, invalid


def psm_shares(rows, p):
    """Shares of the valid respondents at price p. Falling curves count answers >= p, rising ones answers <= p:
    whoever names 40 € as 'too expensive' already finds 40 € too expensive."""
    n = len(rows)
    if not n:
        raise ValueError('no valid respondents')
    c = lambda k, up: sum(1 for r in rows if (r[k] >= p - _EPS if up else r[k] <= p + _EPS)) / n
    tc, cheap, ex, te = c('tc', True), c('cheap', True), c('exp', False), c('te', False)
    return {'tc': tc, 'cheap': cheap, 'exp': ex, 'te': te, 'not_cheap': 1 - cheap, 'not_exp': 1 - ex}


def psm_knots(rows):
    """Evaluation prices: 0, every distinct answer, and an upper end (10 % above the maximum, rounded up to 10)."""
    pts = {0.0}
    for r in rows:
        pts.update(r[k] for k in PSM_KEYS)
    mx = max([1.0] + list(pts))
    pts.add(math.ceil(mx * 1.1 / 10) * 10)
    return sorted(pts)


def psm_crossing(xs, ya, yb):
    """First crossing of two curves given at the knots xs, with linear interpolation between knots. If the curves
    coincide over a stretch, the midpoint of that stretch is returned. None if they never meet."""
    if not xs or len(xs) != len(ya) or len(xs) != len(yb) or any(a >= b for a,b in zip(xs,xs[1:])):
        raise ValueError('crossing needs nonempty, increasing aligned knots')
    d = [a - b for a, b in zip(ya, yb)]
    def run_end(i):
        while i + 1 < len(xs) and abs(d[i + 1]) < 1e-10:
            i += 1
        return i
    for i in range(len(xs)):
        if abs(d[i]) < 1e-10:
            return (xs[i] + xs[run_end(i)]) / 2
        if i + 1 < len(xs) and abs(d[i + 1]) >= 1e-10 and d[i] * d[i + 1] < 0:
            return xs[i] + (xs[i + 1] - xs[i]) * d[i] / (d[i] - d[i + 1])
    return None


def van_westendorp(rows, method='standard', segment=None, te_shift=0.0):
    """Price sensitivity meter. rows: dicts with tc, cheap, exp, te (and optionally 'group').
    segment: keep only rows of that group; te_shift: add to every 'too expensive' answer (what-if of the lab).
    Returns valid/invalid counts, knots, curves and the four price points PMC, OPP, IPP, PME."""
    if method not in PSM_CROSSINGS:
        raise ValueError('method is standard or alternative')
    if isinstance(te_shift, bool) or not isinstance(te_shift, (int, float)) or not math.isfinite(te_shift):
        raise ValueError('finite shift required')
    sel = [r for r in rows if segment in (None, 'all') or isinstance(r, dict) and r.get('group') == segment]
    if te_shift:
        shifted = []
        for r in sel:
            try:
                shifted.append(dict(r, te=float(r['te']) + te_shift) if not isinstance(r['te'], bool) else r)
            except (KeyError, TypeError, ValueError):
                shifted.append(r)
        sel = shifted
    valid, invalid = psm_clean(sel)
    if not valid:
        raise ValueError('no valid respondents')
    xs = psm_knots(valid)
    cur = {k: [] for k in ('tc', 'cheap', 'exp', 'te', 'not_cheap', 'not_exp')}
    for p in xs:
        for k, v in psm_shares(valid, p).items():
            cur[k].append(v)
    pts = {k: psm_crossing(xs, cur[a], cur[b]) for k, (a, b) in PSM_CROSSINGS[method].items()}
    return {'n_valid': len(valid), 'n_invalid': len(invalid), 'invalid_rows': invalid, 'knots': xs, 'curves': cur,
            'points': pts, 'method': method, 'range_width': (pts['pme'] - pts['pmc']) if None not in (pts['pme'], pts['pmc']) else None}


def _mulberry32(seed):
    s = seed & 0xffffffff
    def nxt():
        nonlocal s
        s = (s + 0x6d2b79f5) & 0xffffffff
        t = s
        t = _imul(t ^ (t >> 15), 1 | t)
        t ^= (t + _imul(t ^ (t >> 7), 61 | t)) & 0xffffffff
        return ((t ^ (t >> 14)) & 0xffffffff) / 4294967296
    return nxt


def _imul(a, b):
    return (a * b) & 0xffffffff


def _round2(x):   # JavaScript Math.round(x*100)/100 (halves round up)
    return math.floor(x * 100 + 0.5) / 100


def psm_synthetic(seed=20261109, n=240):
    """SYNTHETIC demo answers (two segments A and B), identical to the stand-alone Lab 04 delivered with the brief.
    These are not survey results of any course."""
    rnd, out = _mulberry32(seed), []
    for i in range(n):
        g = 'A' if i < n // 2 else 'B'
        b = (44 if g == 'A' else 67) * (0.78 + rnd() * 0.44)
        tc = _round2(b * (0.51 + rnd() * .13))
        cheap = _round2(max(tc + .5, b * (.75 + rnd() * .10)))
        ex = _round2(max(cheap + .5, b * (1.07 + rnd() * .15)))
        te = _round2(max(ex + .5, b * (1.35 + rnd() * .20)))
        out.append({'tc': tc, 'cheap': cheap, 'exp': ex, 'te': te, 'group': g})
    return out


# ------------------------------------------------------------------ B16: traces for mathematical scenes
# A scene never computes on its own: every value it shows is a field of one of these traces. The browser mirrors
# them in EM.models (mlpTrace, chordLift, rectSearch, cashflowLedger) and the tests require identical values.

def mlp_trace(p, x, t, lr, hidden_act='sigmoid', out_act='sigmoid'):
    """Every intermediate quantity of one forward pass, the backward pass and one gradient step (all parameters).
    prod[j][i] = W1[j][i]*x[i]; part[j][i] = running sum of those products; fprime[j] = f'(z_j);
    path[j][i] = dL/dW1[j][i] written as its chain-rule factors delta_o * W2[j] * f'(z_j) * x_i."""
    bw = mlp_backward(p, x, t, hidden_act, out_act)
    fw, g = bw['forward'], bw['grad']
    df, dg = ACT[hidden_act][1], ACT[out_act][1]
    prod = [[w * xi for w, xi in zip(row, x)] for row in p['W1']]
    part = []
    for row in prod:
        s, acc = 0.0, []
        for v in row:
            s += v
            acc.append(s)
        part.append(acc)
    vprod = [v * a for v, a in zip(p['W2'], fw['a1'])]
    q, _ = mlp_step(p, x, t, lr, hidden_act, out_act)
    fa = mlp_forward(q, x, hidden_act, out_act)
    la = mlp_loss(fa['y'], t)
    return {'x': list(x), 't': t, 'lr': lr, 'W1': p['W1'], 'b1': p['b1'], 'W2': p['W2'], 'b2': p['b2'],
            'prod': prod, 'part': part, 'z1': fw['z1'], 'a1': fw['a1'], 'fprime': [df(z, a) for z, a in zip(fw['z1'], fw['a1'])],
            'vprod': vprod, 'zo': fw['zo'], 'y': fw['y'], 'err': fw['y'] - t, 'gprime': dg(fw['zo'], fw['y']), 'loss': bw['loss'],
            'delta_o': bw['delta_o'], 'delta_h': bw['delta_h'], 'grad': g,
            'new': q, 'step': {'W1': [[n - o for n, o in zip(rn, ro)] for rn, ro in zip(q['W1'], p['W1'])], 'b1': [n - o for n, o in zip(q['b1'], p['b1'])],
                               'W2': [n - o for n, o in zip(q['W2'], p['W2'])], 'b2': q['b2'] - p['b2']},
            'after': {'z1': fa['z1'], 'a1': fa['a1'], 'zo': fa['zo'], 'y': fa['y'], 'loss': la}, 'dloss': la - bw['loss']}


# Closed reference curve for the chord lift: a smooth, star-shaped, deliberately asymmetric curve
# gamma(u) = r(u) (cos 2πu, sin 2πu), r(u) = R0 + sum_k (a_k cos 2πku + b_k sin 2πku).
CURVE = {'r0': 1.0, 'terms': [[2, 0.0, 0.12], [3, 0.16, 0.0], [5, 0.0, 0.04]]}


def curve_point(u, c=None):
    c = c or CURVE
    th = 2 * math.pi * u
    r = c['r0'] + sum(a * math.cos(k * th) + b * math.sin(k * th) for k, a, b in c['terms'])
    return (r * math.cos(th), r * math.sin(th))


def curve_deriv(u, c=None):
    """d gamma / du (analytic)."""
    c = c or CURVE
    th = 2 * math.pi * u
    r = c['r0'] + sum(a * math.cos(k * th) + b * math.sin(k * th) for k, a, b in c['terms'])
    dr = sum(k * (-a * math.sin(k * th) + b * math.cos(k * th)) for k, a, b in c['terms'])
    w = 2 * math.pi
    return (w * (dr * math.cos(th) - r * math.sin(th)), w * (dr * math.sin(th) + r * math.cos(th)))


def chord_lift(s, t, c=None):
    """Unordered pair of curve points {P, Q} -> (midpoint M, distance d) -> point (M_x, M_y, d) in 3-D.
    Symmetric in s and t; pairs with s == t land on the curve itself (d = 0)."""
    P, Q = curve_point(s, c), curve_point(t, c)
    m = ((P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2)
    d = math.hypot(P[0] - Q[0], P[1] - Q[1])
    return {'P': P, 'Q': Q, 'M': m, 'd': d, 'lift': (m[0], m[1], d)}


def _solve3(A, b):
    """Gaussian elimination with partial pivoting (3x3). None if singular."""
    M_ = [list(A[i]) + [b[i]] for i in range(3)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(M_[r][col]))
        if abs(M_[piv][col]) < 1e-14:
            return None
        M_[col], M_[piv] = M_[piv], M_[col]
        for r in range(col + 1, 3):
            f = M_[r][col] / M_[col][col]
            for k in range(col, 4):
                M_[r][k] -= f * M_[col][k]
    x = [0.0, 0.0, 0.0]
    for r in (2, 1, 0):
        x[r] = (M_[r][3] - sum(M_[r][k] * x[k] for k in range(r + 1, 3))) / M_[r][r]
    return x


def rect_residual(s, y, c=None):
    """F(t, u, v) = (P+Q-U-V, |P-Q|^2 - |U-V|^2): zero iff the pairs {P,Q} and {U,V} share midpoint and length."""
    t, u, v = y
    P, Q, U, V = (curve_point(z, c) for z in (s, t, u, v))
    return [P[0] + Q[0] - U[0] - V[0], P[1] + Q[1] - U[1] - V[1],
            (P[0] - Q[0]) ** 2 + (P[1] - Q[1]) ** 2 - (U[0] - V[0]) ** 2 - (U[1] - V[1]) ** 2]


def rect_search(s, c=None, n=6, iters=40):
    """Numerical search for an inscribed rectangle with one corner at parameter s (Newton's method from a fixed grid
    of n^3 start values; deterministic). Returns the solutions sorted by area (largest first), each with its
    parameters, corners, residual and area. Exploration only: finding (or not finding) one proves nothing."""
    P0 = curve_point(s, c)
    sols = []
    for a in range(n):
        for b in range(n):
            for k in range(n):
                y = [(s + (a + .5) / n) % 1, (s + (b + .25) / n) % 1, (s + (k + .75) / n) % 1]
                ok = False
                for _ in range(iters):
                    F = rect_residual(s, y, c)
                    if max(abs(f) for f in F) < 1e-13:
                        ok = True
                        break
                    t, u, v = y
                    Q, U, V = curve_point(t, c), curve_point(u, c), curve_point(v, c)
                    dQ, dU, dV = curve_deriv(t, c), curve_deriv(u, c), curve_deriv(v, c)
                    J = [[dQ[0], -dU[0], -dV[0]], [dQ[1], -dU[1], -dV[1]],
                         [-2 * ((P0[0] - Q[0]) * dQ[0] + (P0[1] - Q[1]) * dQ[1]),
                          -2 * ((U[0] - V[0]) * dU[0] + (U[1] - V[1]) * dU[1]),
                          2 * ((U[0] - V[0]) * dV[0] + (U[1] - V[1]) * dV[1])]]
                    st = _solve3(J, [-f for f in F])
                    if st is None:
                        break
                    mx = max(abs(z) for z in st)
                    if mx > 0.1:
                        st = [z * 0.1 / mx for z in st]
                    y = [(y[i] + st[i]) % 1 for i in range(3)]
                if not ok and max(abs(f) for f in rect_residual(s, y, c)) >= 1e-11:
                    continue
                t, u, v = y
                pts = [P0, curve_point(u, c), curve_point(t, c), curve_point(v, c)]   # corners in order P, U, Q, V
                cd = lambda z, w: min(abs(z - w), 1 - abs(z - w))
                if min(cd(z, w) for z, w in ((s, t), (s, u), (s, v), (t, u), (t, v), (u, v))) < 1e-4:
                    continue          # degenerate: two corners coincide or {U,V} = {P,Q}
                side1 = math.hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
                side2 = math.hypot(pts[2][0] - pts[1][0], pts[2][1] - pts[1][1])
                key = tuple(sorted(round(z, 6) for z in (u, v))) + (round(t, 6),)
                if any(sol['key'] == key for sol in sols):
                    continue
                sols.append({'key': key, 's': s, 't': t, 'u': min(u, v), 'v': max(u, v), 'corners': [P0, curve_point(min(u, v), c), curve_point(t, c), curve_point(max(u, v), c)],
                             'residual': max(abs(f) for f in rect_residual(s, y, c)), 'area': side1 * side2})
    sols.sort(key=lambda z: (-round(z['area'], 9), z['key']))
    for z in sols:
        z.pop('key')
    return sols


def rect_check(corners):
    """Independent check that four points P, U, Q, V (in this order) form a rectangle: the diagonals PQ and UV bisect
    each other and have equal length; equivalently all four angles are right angles. Returns the largest |cos|."""
    worst = 0.0
    for i in range(4):
        a, b, c = corners[i - 1], corners[i], corners[(i + 1) % 4]
        u, v = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
        worst = max(worst, abs(u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v)))
    return worst


def cashflow_ledger(orders, delay, cost, invest, start_cash=0.0, horizon=None):
    """Business events behind cashflow(): every sale (with invoice in the same period) and its payment after the
    payment term, every outflow, and the running balance period by period. Same numbers as cashflow()."""
    r = cashflow(orders, delay, cost, invest, start_cash, horizon)
    T = len(r['cf'])
    g = lambda xs, i: float(xs[i]) if 0 <= i < len(xs) else 0.0
    sales = [{'period': t + 1, 'amount': g(orders, t), 'paid_in': t + 1 + int(delay), 'within': t + int(delay) < T} for t in range(T) if g(orders, t)]
    prev = [float(start_cash)] + r['balance'][:-1]
    rows = [{'period': t + 1, 'prev': prev[t], 'inflow': r['inflow'][t], 'cost': g(cost, t), 'invest': g(invest, t),
             'cf': r['cf'][t], 'balance': r['balance'][t], 'from_sale': (t + 1 - int(delay)) if t - int(delay) >= 0 and g(orders, t - int(delay)) else None}
            for t in range(T)]
    return {**r, 'sales': sales, 'rows': rows}


def chord_trace(s, t, c=None):
    """Everything the chord-lift scene shows: the learner's pair and the first rectangle found through P(s)."""
    L = chord_lift(s, t, c)
    R = (rect_search(s, c) or [None])[0]
    rect = None
    if R:
        a, b = chord_lift(R['s'], R['t'], c), chord_lift(R['u'], R['v'], c)
        rect = {**R, 'liftPQ': a['lift'], 'liftUV': b['lift'], 'dPQ': a['d'], 'dUV': b['d'], 'MPQ': a['M'], 'MUV': b['M']}
    return {'s': s, 't': t, **L, 'rect': rect}


def cash_trace(orders, delay, cost, invest, start_cash=0.0, horizon=None, delay_b=None):
    """Ledger of scenario A plus the comparison scenario B (other payment term) of the cash-flow scene."""
    led = cashflow_ledger(orders, delay, cost, invest, start_cash, horizon)
    b = cashflow(orders, delay + 1 if delay_b is None else delay_b, cost, invest, start_cash, horizon)
    return {**led, 'delay': int(delay), 'delayB': int(delay + 1 if delay_b is None else delay_b), 'alt': b,
            'diff': b['financing_need'] - led['financing_need'], 'min_index': led['min_period'] - 1}


# ------------------------------------------------------------------ B21: finite Markov decision processes
# Generic reference model for any finite MDP given by a course (states, actions, p(s'|s,a), expected reward r(s,a),
# discount gamma). States without actions are terminal (value 0). Updates are synchronous (Jacobi): V_{k+1} is computed
# from V_k only, as in the usual lecture algorithms. Mirrored 1:1 in templates/em_labs.js (EM.models.mdp*).

def mdp_check(mdp):
    """Raises ValueError for an ill-formed MDP; returns the normalised model {states, actions, T, gamma}."""
    S = list(mdp['states'])
    if not S or len(set(S)) != len(S):
        raise ValueError('states must be non-empty and unique')
    g = float(mdp['gamma'])
    if not 0 <= g < 1:
        raise ValueError('gamma must lie in [0, 1)')
    A, T = {s: [] for s in S}, {}
    for tr in mdp['transitions']:
        s, a = tr['s'], tr['a']
        if s not in A:
            raise ValueError(f'unknown state {s}')
        if a in A[s]:
            raise ValueError(f'duplicate action {a} in {s}')
        nxt = {k: float(v) for k, v in tr['next'].items() if float(v) != 0}
        if set(nxt) - set(S) or any(v < 0 for v in nxt.values()) or abs(sum(nxt.values()) - 1) > 1e-9:
            raise ValueError(f'p(.|{s},{a}) must be a probability distribution over known states')
        A[s].append(a); T[(s, a)] = (float(tr['r']), nxt)
    return {'states': S, 'actions': A, 'T': T, 'gamma': g}


def mdp_q(m, V, s, a):
    r, nxt = m['T'][(s, a)]
    return r + m['gamma'] * sum(p * V[t] for t, p in nxt.items())


def mdp_backup_terms(m, V, s, a):
    """One Bellman backup written out: [{next, p, r, v_next, term = p * (r + gamma V(s'))}] and their sum."""
    r, nxt = m['T'][(s, a)]
    terms = [{'next': t, 'p': p, 'r': r, 'v_next': V[t], 'term': p * (r + m['gamma'] * V[t])} for t, p in nxt.items()]
    return {'terms': terms, 'q': sum(x['term'] for x in terms)}


def mdp_greedy(m, V, tol=1e-9):
    """Greedy action per state; ties broken by the order of the actions in the course data."""
    out = {}
    for s in m['states']:
        if m['actions'][s]:
            qs = [(mdp_q(m, V, s, a), i, a) for i, a in enumerate(m['actions'][s])]
            best = max(q for q, _, _ in qs)
            out[s] = next(a for q, _, a in qs if q >= best - tol)
    return out


def _pi_value(m, V, s, pi):
    if not m['actions'][s]:
        return 0.0
    dist = pi[s] if isinstance(pi[s], dict) else {pi[s]: 1.0}
    return sum(w * mdp_q(m, V, s, a) for a, w in dist.items())


def mdp_eval_sweeps(m, pi, k, V0=None):
    """Iterative policy evaluation: V_0, V_1, ..., V_k (synchronous)."""
    V = dict(V0 or {s: 0.0 for s in m['states']}); hist = [dict(V)]
    for _ in range(k):
        V = {s: _pi_value(m, V, s, pi) for s in m['states']}; hist.append(dict(V))
    return hist


def mdp_eval_exact(m, pi):
    """V^pi from the linear system (I - gamma P^pi) V = r^pi (Gaussian elimination with partial pivoting)."""
    S = m['states']; n = len(S); ix = {s: i for i, s in enumerate(S)}
    A = [[float(i == j) for j in range(n)] for i in range(n)]; b = [0.0] * n
    for s in S:
        if not m['actions'][s]:
            continue
        dist = pi[s] if isinstance(pi[s], dict) else {pi[s]: 1.0}
        for a, w in dist.items():
            r, nxt = m['T'][(s, a)]; b[ix[s]] += w * r
            for t, p in nxt.items():
                A[ix[s]][ix[t]] -= m['gamma'] * w * p
    for c in range(n):
        piv = max(range(c, n), key=lambda i: abs(A[i][c])); A[c], A[piv] = A[piv], A[c]; b[c], b[piv] = b[piv], b[c]
        for i in range(n):
            if i != c and A[i][c]:
                f = A[i][c] / A[c][c]
                A[i] = [x - f * y for x, y in zip(A[i], A[c])]; b[i] -= f * b[c]
    return {s: b[ix[s]] / A[ix[s]][ix[s]] for s in S}


def mdp_value_iteration(m, k):
    V = {s: 0.0 for s in m['states']}; hist = [dict(V)]
    for _ in range(k):
        V = {s: (max(mdp_q(m, V, s, a) for a in m['actions'][s]) if m['actions'][s] else 0.0) for s in m['states']}
        hist.append(dict(V))
    return hist


def mdp_policy_iteration(m, pi0, max_iter=100):
    """[(pi_i, V^{pi_i}, Q^{pi_i})] until the greedy policy no longer changes."""
    pi, out = dict(pi0), []
    for _ in range(max_iter):
        V = mdp_eval_exact(m, pi)
        Q = {s: {a: mdp_q(m, V, s, a) for a in m['actions'][s]} for s in m['states']}
        out.append({'policy': dict(pi), 'V': V, 'Q': Q})
        new = mdp_greedy(m, V)
        # keep the current action on ties (guarantees termination)
        new = {s: (pi[s] if not isinstance(pi[s], dict) and abs(Q[s].get(pi[s], -math.inf) - Q[s][new[s]]) <= 1e-9 else new[s]) for s in new}
        if new == pi:
            return out
        pi = new
    raise ValueError('policy iteration did not converge')


def mdp_optimal(m, tol=1e-12, max_iter=100000):
    V = {s: 0.0 for s in m['states']}
    for _ in range(max_iter):
        W = {s: (max(mdp_q(m, V, s, a) for a in m['actions'][s]) if m['actions'][s] else 0.0) for s in m['states']}
        if max(abs(W[s] - V[s]) for s in V) < tol:
            return W
        V = W
    raise ValueError('value iteration did not converge')


def scaled_attention(parameters):
    """Bounded real matrix attention, row-wise softmax; all-masked rows fail.

    Scaling/temperature are explicit experimental choices, not proof of training
    benefit. Max-shift avoids exponential overflow; finite input bounds prevent
    overflow in dot products. Mask True means allowed. No dropout here.
    """
    allowed = {'Q', 'K', 'V', 'mask', 'temperature', 'scaled'}
    if not isinstance(parameters, dict) or set(parameters) - allowed:
        raise ValueError('attention: unexpected fields')
    def matrix(name):
        value = parameters.get(name)
        if not isinstance(value, list) or not 1 <= len(value) <= 8:
            raise ValueError(name + ': 1..8 rows required')
        width = len(value[0]) if isinstance(value[0], list) else 0
        if not 1 <= width <= 8: raise ValueError(name + ': 1..8 columns required')
        for row in value:
            if not isinstance(row, list) or len(row) != width:
                raise ValueError(name + ': rectangular matrix required')
            if any(type(x) not in (int, float) or not math.isfinite(x) or abs(x) > 10000 for x in row):
                raise ValueError(name + ': finite entries bounded by 10000 required')
        return value
    Q, K, V = matrix('Q'), matrix('K'), matrix('V')
    if len(Q[0]) != len(K[0]) or len(K) != len(V):
        raise ValueError('attention: incompatible dimensions Q/K/V')
    temperature = parameters.get('temperature', 1)
    if type(temperature) not in (int, float) or not math.isfinite(temperature) or not 0.05 <= temperature <= 20:
        raise ValueError('attention: temperature must be in [0.05,20]')
    scaled = parameters.get('scaled', True)
    if type(scaled) is not bool: raise ValueError('attention: scaled must be boolean')
    mask = parameters.get('mask', [[True] * len(K) for _ in Q])
    if (not isinstance(mask, list) or len(mask) != len(Q) or
            any(not isinstance(row, list) or len(row) != len(K) or
                any(type(x) is not bool for x in row) for row in mask)):
        raise ValueError('attention: boolean mask must match score matrix')
    if any(not any(row) for row in mask):
        raise ValueError('attention: fully masked row is undefined, not a uniform distribution')
    divisor = math.sqrt(len(Q[0])) if scaled else 1.0
    raw = [[math.fsum(a*b for a,b in zip(q,k)) for k in K] for q in Q]
    scores = [[x/divisor/temperature for x in row] for row in raw]
    weights, shifted = [], []
    for row, on in zip(scores, mask):
        maximum = max(x for x, allowed in zip(row,on) if allowed)
        exp = [math.exp(x-maximum) if allowed else 0.0 for x, allowed in zip(row,on)]
        total = math.fsum(exp)
        weights.append([x/total for x in exp])
        shifted.append([x-maximum if allowed else None for x,allowed in zip(row,on)])
    contributions = [[[w*v for v in values] for w,values in zip(row,V)] for row in weights]
    output = [[math.fsum(c[j] for c in row) for j in range(len(V[0]))] for row in contributions]
    return {'Q':Q,'K':K,'V':V,'mask':mask,'raw':raw,'scores':scores,'shifted':shifted,
            'weights':weights,'contributions':contributions,'output':output,
            'divisor':divisor,'temperature':temperature,'scaled':scaled,
            'shape': {'n_q':len(Q),'n_k':len(K),'d_k':len(Q[0]),'d_v':len(V[0])}}
