"""Deterministic scene models for Mastery Motion (Python reference; mirrored in templates/mastery_motion.js).

A model maps a parameter dict to a state dict of named quantities (numbers, vectors, point lists). Every number a
scene shows is read from such a state (V10). The browser runtime evaluates the same functions on every animation
frame; tests compare both runtimes at every keyframe.

softmax_simplex_pg reuses the trusted bandit model of labs/policy_gradient.py (softmax, score function, mulberry32
sampler with the same draw order, exact gradient and variance formulas).
linear_map_2d is the generic plane primitive (grid, basis vectors, test vector, signed area) for linear-algebra scenes.
"""
from __future__ import annotations

import math

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
        "score_rays": [{"points": [[-3.0 * x for x in score(pi, a)], [3.0 * x for x in score(pi, a)]]} for a in range(3)],
        "mean_err": math.sqrt(_fsum((x - g) ** 2 for x, g in zip(mean, grad))) if n else 0.0, "k": k, "alpha": alpha, "g_vis": g_vis, "lam": lam, "b0": b0,
    }


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


def linear_map_2d(params):
    """M(t) = (1 - t) I + t A acting on the plane; signed area of the unit square is det M(t)."""
    a = _vec(params, "A", 4, -10, 10)  # row-major [a11, a12, a21, a22]
    t = _num(params, "t", 0, 1)
    v = _vec(params, "v", 2, -10, 10)
    m = [(1 - t) + t * a[0], t * a[1], t * a[2], (1 - t) + t * a[3]]

    def apply(x, y):
        return [m[0] * x + m[1] * y, m[2] * x + m[3] * y]
    det = m[0] * m[3] - m[1] * m[2]
    return {"M": m, "det": det, "e1": apply(1, 0), "e2": apply(0, 1), "Av": apply(*v), "v": v,
            "square": [apply(0, 0), apply(1, 0), apply(1, 1), apply(0, 1)], "t": t,
            "orientation": 1 if det > 1e-12 else (-1 if det < -1e-12 else 0)}


MODELS = {"softmax_simplex_pg": softmax_simplex_pg, "linear_map_2d": linear_map_2d}
