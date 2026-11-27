"""Deterministic scene models for Mastery Motion (Python reference; mirrored in templates/mastery_motion.js).

A model maps a parameter dict to a state dict of named quantities (numbers, vectors, point lists). Every number a
scene shows is read from such a state (V10). The browser runtime evaluates the same functions on every animation
frame; tests compare both runtimes at every keyframe.

softmax_simplex_pg reuses the trusted bandit model of labs/policy_gradient.py (softmax, score function, mulberry32
sampler with the same draw order, exact gradient and variance formulas).
linear_map_2d is the single plane-transformation model of the engine (it replaced labs/plane_map.py): the straight
morph M(t) = (1 - t) I + t A with columns, test vector, signed area, exact rank/kernel/image (rational arithmetic on the
decimal inputs), the singular times of the morph and the display strings of its readouts. The browser mirror decides
rank with a relative tolerance; at every keyframe (decimal inputs) both agree, which the parity tests check.
"""
from __future__ import annotations

import math
from fractions import Fraction

from ..labs.policy_gradient import exact, mulberry32, score, softmax

MAX_SAMPLES = 400
MAX_ITER = 40


def _num(params, name, low, high):
    value = params.get(name)
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"motion model: parameter {name} must be a finite number in [{low}, {high}]")
    return float(value)


def _vec(params, name, length, low, high):
    value = params.get(name)
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"motion model: parameter {name} must be a list of {length} numbers")
    return [_num({name: v}, name, low, high) for v in value]


def _fsum(xs):
    return math.fsum(xs)


def softmax_simplex_pg(params):
    """Softmax policy over 3 actions on the probability simplex with exact gradient ascent and REINFORCE samples.

    Parameters: theta0 (3 logits), rewards (3 means), noise_sd, alpha (step size), k (gradient-ascent iterations,
    fractional = linear progress of the current step in logit space), n (samples shown), seed, b0 (constant baseline),
    lam (baseline mix: b = (1 - lam) * b0 + lam * J), g_vis (0..1 visibility/length of the exact gradient arrow).
    """
    theta0 = _vec(params, "theta0", 3, -8, 8)
    rewards = _vec(params, "rewards", 3, -20, 20)
    sd = _num(params, "noise_sd", 0, 10)
    alpha = _num(params, "alpha", 0, 10)
    k = _num(params, "k", 0, MAX_ITER)
    n = int(_num(params, "n", 0, MAX_SAMPLES))
    seed = params.get("seed")
    if type(seed) is not int or not 0 <= seed < 2 ** 32:
        raise ValueError("motion model: seed must be an unsigned 32-bit integer")
    b0 = _num(params, "b0", -20, 20)
    lam = _num(params, "lam", 0, 1)
    g_vis = _num(params, "g_vis", 0, 1)

    # exact gradient ascent; fractional k moves linearly in logit space along the current step
    thetas = [theta0]
    whole = int(math.floor(k))
    for _ in range(min(whole + 1, MAX_ITER)):
        t = thetas[-1]
        g = exact(t, rewards)["grad"]
        thetas.append([a + alpha * b for a, b in zip(t, g)])
    frac = k - whole
    base = thetas[whole]
    theta = [a + frac * (c - a) for a, c in zip(base, thetas[min(whole + 1, len(thetas) - 1)])] if frac > 0 else list(base)
    ex = exact(theta, rewards, sd)
    pi, J, grad = ex["pi"], ex["J"], ex["grad"]
    b = (1.0 - lam) * b0 + lam * J

    # REINFORCE single-sample estimates at the current policy (same draw order as labs/policy_gradient.compute)
    draw = mulberry32(seed)
    samples, actions, returns = [], [], []
    for _ in range(n):
        u = draw()
        a, acc = 2, 0.0
        for j, prob in enumerate(pi):
            acc += prob
            if u < acc:
                a = j
                break
        u1, u2 = draw(), draw()
        eps = math.sqrt(-2.0 * math.log(1.0 - u1)) * math.cos(2.0 * math.pi * u2)
        ret = rewards[a] + sd * eps
        actions.append(a)
        returns.append(ret)
        samples.append([(ret - b) * s for s in score(pi, a)])
    if n:
        mean = [_fsum(s[j] for s in samples) / n for j in range(3)]
        spread = math.sqrt(_fsum(_fsum((s[j] - mean[j]) ** 2 for j in range(3)) for s in samples) / n)
    else:
        mean, spread = [0.0, 0.0, 0.0], 0.0
    var_b = ex["variance"](b)
    var_none = ex["variance"](0.0)
    var_opt = ex["variance"](ex["b_opt"])
    # first-order motion of pi under one exact step: d pi = alpha * (diag(pi) - pi pi^T) grad J
    mass = _fsum(p * w for p, w in zip(pi, ex["weights"]))
    pg = _fsum(p * g for p, g in zip(pi, grad))
    dpi = [alpha * p * (g - pg) for p, g in zip(pi, grad)]
    trail = [softmax(t) for t in thetas[: whole + 1]] + ([pi] if frac > 0 else [])
    b_seg = _level_segment(rewards, b)
    levels = []
    for level in _levels(rewards):
        seg = _level_segment(rewards, level)
        if seg:
            levels.append({"level": level, "points": seg})
    return {
        "theta": theta, "pi": pi, "J": J, "grad": grad, "grad_shown": [g_vis * x for x in grad],
        "grad_norm": math.sqrt(_fsum(x * x for x in grad)),
        "argmax_grad": max(range(3), key=lambda j: grad[j]),
        "b": b, "b_opt": ex["b_opt"], "n": n, "samples": samples, "actions": actions, "returns": returns,
        "sample_mean": mean, "sample_spread": spread,
        "var_b": var_b, "var_none": var_none, "var_opt": var_opt,
        "sd_b": math.sqrt(max(var_b, 0.0)), "sd_none": math.sqrt(max(var_none, 0.0)), "sd_opt": math.sqrt(max(var_opt, 0.0)),
        "var_delta": var_b - var_none,
        # exact mean of the estimator with baseline minus without: -b * E[e_A - pi] = -b * (pi - pi) = 0
        "mean_shift": abs(b) * math.sqrt(_fsum(_fsum(p * score(pi, a)[j] for a, p in enumerate(pi)) ** 2
                                               for j in range(3))),
        "dpi": dpi, "pi_next": [p + d for p, d in zip(pi, dpi)],
        "pi_trail": trail, "J_levels": levels, "b_line": [{"level": b, "points": b_seg}] if b_seg else [],
        "score_rays": _score_rays(pi, actions, returns, b),
        # b* is a weighted mean of the rewards: weights pi_a |e_a - pi|^2 (normalised), see labs/policy_gradient.exact
        "b_weights": [p * w / mass for p, w in zip(pi, ex["weights"])],
        "mean_err": math.sqrt(_fsum((x - g) ** 2 for x, g in zip(mean, grad))) if n else 0.0, "k": k, "alpha": alpha, "g_vis": g_vis, "lam": lam, "b0": b0,
    }


def _score_rays(pi, actions, returns, b):
    """Only the score lines that carry drawn samples, and only as far as the samples reach (declutter, V2)."""
    rays = []
    for a in range(3):
        cs = [r - b for x, r in zip(actions, returns) if x == a]
        if not cs:
            continue
        lo, hi = min(min(cs), 0.0), max(max(cs), 0.0)
        pad = 0.08 * (hi - lo)
        s = score(pi, a)
        rays.append({"action": a, "points": [[(lo - pad) * x for x in s], [(hi + pad) * x for x in s]]})
    return rays


def _levels(rewards):
    lo, hi = min(rewards), max(rewards)
    return [lo + (hi - lo) * i / 6 for i in range(1, 6)]


def _level_segment(rewards, level):
    """Intersection of the line {pi : pi . r = level} with the simplex boundary (J is linear in pi)."""
    pts = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        ri, rj = rewards[i], rewards[j]
        if ri == rj:
            continue
        t = (level - ri) / (rj - ri)
        if 0.0 <= t <= 1.0:
            p = [0.0, 0.0, 0.0]
            p[i], p[j] = 1.0 - t, t
            pts.append(p)
    return pts[:2] if len(pts) >= 2 else None


PLANE_LIMIT = 6       # |entries| of A and |components| of v in experience-unit parameters (readable scenes)
LINE_REACH = 60.0     # half length of drawn kernel/image lines in world units (panels clip them)


def _q(x):
    """Exact rational value of a decimal input (0.1 -> 1/10, as written by the author)."""
    return Fraction(x) if isinstance(x, int) else Fraction(repr(float(x)))


def _primitive(u):
    """Scale a nonzero rational vector to coprime integers with a positive first nonzero entry: (1/2, -1/2) -> (1, -1)."""
    den = math.lcm(*(x.denominator for x in u))
    ints = [int(x * den) for x in u]
    g = math.gcd(*ints) or 1
    ints = [x // g for x in ints]
    sign = -1 if next(x for x in ints if x) < 0 else 1
    return [sign * x for x in ints]


def _kernel_image(m):
    """Exact rank, kernel basis and image basis of the 2x2 matrix m (row-major list of 4 Fractions)."""
    if m[0] * m[3] - m[1] * m[2] != 0:
        return 2, [], [[1, 0], [0, 1]]
    if all(x == 0 for x in m):
        return 0, [[1, 0], [0, 1]], []
    row = m[0:2] if (m[0], m[1]) != (0, 0) else m[2:4]
    col = [m[0], m[2]] if (m[0], m[2]) != (0, 0) else [m[1], m[3]]
    return 1, [_primitive([row[1], -row[0]])], [_primitive(col)]


def singular_times(a):
    """All t in [0, 1] with det M(t) = 0 for A = a (row-major, rational): det = 1 + t (tr A - 2) + t^2 (1 - tr A + det A)."""
    tr, det_a = a[0] + a[3], a[0] * a[3] - a[1] * a[2]
    qa, qb, qc = 1 - tr + det_a, tr - 2, Fraction(1)
    if qa == 0:
        return [] if qb == 0 else [float(r) for r in [-qc / qb] if 0 <= -qc / qb <= 1]
    disc = qb * qb - 4 * qa * qc
    if disc < 0:
        return []
    root = math.sqrt(disc)
    roots = sorted({(-float(qb) - root) / (2 * float(qa)), (-float(qb) + root) / (2 * float(qa))})
    return [r for r in roots if -1e-12 <= r <= 1 + 1e-12]


def g2(x):
    """Short number for readouts: at most two decimals, decimal comma, typographic minus (same in mastery_motion.js)."""
    r = math.floor(x * 100 + 0.5) / 100
    if abs(r) < 5e-10:
        return "0"
    s = str(int(r)) if float(r).is_integer() else repr(r)
    return s.replace("-", "−").replace(".", ",")


def _par(x):
    return "(" + g2(x) + ")" if x < -5e-10 else g2(x)


def _pt(p):
    return "(" + g2(p[0]) + "; " + g2(p[1]) + ")"


def plane_texts(st):
    """Display strings of the plane readouts (pure function of the state; mirrored 1:1 in JS)."""
    m, v, rank = st["M"], st["v"], st["rank"]
    if rank == 1:
        ki = ("Kern = span" + _pt(st["kernel"][0]), "Bild = span" + _pt(st["image"][0]), "2 = 1 + 1")
    elif rank == 0:
        ki = ("Kern = ganze Ebene", "Bild = {0}", "2 = 2 + 0")
    else:
        ki = ("Kern = {0}", "Bild = ganze Ebene", "2 = 0 + 2")
    d = st["det"]
    return {
        "t_text": g2(st["t"]), "e1_text": _pt(st["e1"]), "e2_text": _pt(st["e2"]), "Mv_text": _pt(st["Mv"]),
        "Av_text": _pt(st["Av"]), "v_text": _pt(v),
        "Mv_formula": _par(v[0]) + "·" + _pt(st["e1"]) + " + " + _par(v[1]) + "·" + _pt(st["e2"]) + " = " + _pt(st["Mv"]),
        "Av_formula": _par(v[0]) + "·" + _pt(st["A_e1"]) + " + " + _par(v[1]) + "·" + _pt(st["A_e2"]) + " = " + _pt(st["Av"]),
        "det_formula": _par(m[0]) + "·" + _par(m[3]) + " − " + _par(m[1]) + "·" + _par(m[2]) + " = " + g2(d),
        "det_A_text": g2(st["det_A"]),
        "det_A_note": ("Weil det A < 0 ist, muss jeder stetige Weg von I nach A durch det = 0: Die Ebene wird unterwegs "
                       "einmal flach gedrückt." if st["det_A"] < 0 else
                       "det A = 0: Am Ende liegt die ganze Ebene auf einer Geraden oder im Nullpunkt." if st["rank_A"] < 2
                       else "det A > 0: Die Orientierung bleibt erhalten."),
        "orientation_text": ("Orientierung erhalten" if st["orientation"] > 0 else
                             "Orientierung umgekehrt (gespiegelt)" if st["orientation"] < 0 else
                             "Fläche 0: die Ebene ist kollabiert"),
        "rank_text": "Rang M = " + str(rank), "kernel_text": ki[0], "image_text": ki[1], "dim_text": "dim Kern + Rang: " + ki[2],
    }


def _line(dirs):
    if len(dirs) != 1:
        return []
    u = [float(x) for x in dirs[0]]
    k = LINE_REACH / math.hypot(*u)
    return [{"points": [[-k * u[0], -k * u[1]], [k * u[0], k * u[1]]]}]


def linear_map_2d(params):
    """M(t) = (1 - t) I + t A acting on the plane; signed area of the unit square is det M(t); exact rank/kernel/image."""
    a = _vec(params, "A", 4, -10, 10)  # row-major [a11, a12, a21, a22]
    t = _num(params, "t", 0, 1)
    v = _vec(params, "v", 2, -10, 10)
    qa, qt, qv = [_q(x) for x in a], _q(t), [_q(x) for x in v]
    qm = [(1 - qt) + qt * qa[0], qt * qa[1], qt * qa[2], (1 - qt) + qt * qa[3]]

    def ap(m, x, y):
        return [m[0] * x + m[1] * y, m[2] * x + m[3] * y]
    det_m, det_a = qm[0] * qm[3] - qm[1] * qm[2], qa[0] * qa[3] - qa[1] * qa[2]
    rank, ker, img = _kernel_image(qm)
    rank_a, ker_a, img_a = _kernel_image(qa)
    f = lambda xs: [float(x) for x in xs]  # noqa: E731
    m = f(qm)
    st = {"M": m, "A": f(qa), "I": [1.0, 0.0, 0.0, 1.0], "t": float(qt), "v": f(qv),
          "e1": f(ap(qm, 1, 0)), "e2": f(ap(qm, 0, 1)), "Mv": f(ap(qm, *qv)), "Av": f(ap(qa, *qv)),
          "A_e1": f(ap(qa, 1, 0)), "A_e2": f(ap(qa, 0, 1)),
          "square": [f(ap(qm, x, y)) for x, y in ((0, 0), (1, 0), (1, 1), (0, 1))],
          "det": float(det_m), "det_A": float(det_a), "det_exact": str(det_m), "det_A_exact": str(det_a),
          "orientation": 1 if det_m > 0 else (-1 if det_m < 0 else 0),
          "rank": rank, "kernel": [f(k) for k in ker], "image": [f(c) for c in img],
          "rank_A": rank_a, "kernel_A": [f(k) for k in ker_a], "image_A": [f(c) for c in img_a],
          "kernel_line": _line(ker), "image_line": _line(img), "singular_times": singular_times(qa)}
    st.update(plane_texts(st))
    return st


def plane_params(parameters):
    """Experience-unit parameters {matrix: 2x2, vector: 2[, t]} (schema kept from the former plane lab) -> model params."""
    if not isinstance(parameters, dict) or not {"matrix", "vector"} <= set(parameters) or \
            set(parameters) - {"matrix", "vector", "t"}:
        raise ValueError("plane map: parameters {matrix, vector[, t]} required")
    mat, vec = parameters["matrix"], parameters["vector"]
    if not (isinstance(mat, list) and len(mat) == 2 and all(isinstance(r, list) and len(r) == 2 for r in mat)):
        raise ValueError("plane map: matrix must be 2x2")
    if not (isinstance(vec, list) and len(vec) == 2):
        raise ValueError("plane map: vector must have 2 components")

    def num(x, name, low=-PLANE_LIMIT, high=PLANE_LIMIT):
        if isinstance(x, str):
            try:
                x = float(Fraction(x))
            except (ValueError, ZeroDivisionError):
                raise ValueError(f"{name}: number required") from None
        if type(x) not in (int, float) or not math.isfinite(x) or not low <= x <= high:
            raise ValueError(f"{name}: finite number in [{low}, {high}] required")
        return float(x)
    return {"A": [num(mat[i][j], f"matrix[{i}][{j}]") for i in range(2) for j in range(2)],
            "v": [num(vec[i], f"vector[{i}]") for i in range(2)],
            "t": num(parameters.get("t", 1), "t", 0, 1)}


def plane_extent(state):
    """One scale for a whole morph (every keyframe of a preset shares it): columns of A, A v, v and the image square."""
    pts = [state["A_e1"], state["A_e2"], state["v"], state["Av"],
           [state["A_e1"][0] + state["A_e2"][0], state["A_e1"][1] + state["A_e2"][1]], [1.0, 1.0]]
    return min(6.0, max(2.5, math.ceil(max(abs(c) for p in pts for c in p) + 0.6)))


MODELS = {"softmax_simplex_pg": softmax_simplex_pg, "linear_map_2d": linear_map_2d}
