"""Trusted reference model: softmax policy gradient on a K-armed bandit.

One state, K actions, a softmax policy pi = softmax(theta) and rewards
R = r_a + sigma * eps with eps ~ N(0, 1). Everything that a learner sees in
the explorable is computed here (Python, for books and tests) and mirrored
exactly in ``templates/policy_gradient_math.js`` (browser). The sampler is a
seeded mulberry32 generator with Box-Muller noise so that both runtimes
produce bit-comparable sample paths.

Exact quantities (no sampling):
  J(theta)            = sum_a pi_a r_a
  grad J              = pi_a (r_a - J)                 (softmax score e_a - pi)
  Var-trace(b)        = sum_a pi_a ((r_a - b)^2 + sigma^2) ||e_a - pi||^2 - ||grad J||^2
  b* (trace optimal)  = sum_a pi_a w_a r_a / sum_a pi_a w_a,  w_a = ||e_a - pi||^2
The variance is the trace of the covariance of the single-sample estimator
(R - b)(e_A - pi); for a batch of N independent samples it is divided by N.
"""
from __future__ import annotations

import math

MODEL = "softmax_policy_gradient"
MAX_ARMS = 4
MAX_BATCH = 2000
BASELINE_MODES = ("none", "constant", "expected")
_FIELDS = {"theta", "rewards", "noise_sd", "baseline_mode", "baseline", "batch", "seed", "step"}


def _real(value, name, low, high):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"policy_gradient: {name} must be a finite number in [{low}, {high}]")
    return float(value)


def check(parameters):
    if not isinstance(parameters, dict) or not set(parameters) <= _FIELDS or not {"theta", "rewards"} <= set(parameters):
        raise ValueError("policy_gradient: parameters theta, rewards and optional "
                         + ", ".join(sorted(_FIELDS - {"theta", "rewards"})) + " only")
    theta, rewards = parameters["theta"], parameters["rewards"]
    if (not isinstance(theta, list) or not isinstance(rewards, list)
            or not 2 <= len(theta) <= MAX_ARMS or len(theta) != len(rewards)):
        raise ValueError(f"policy_gradient: 2..{MAX_ARMS} arms with one logit and one mean reward each")
    out = {
        "theta": [_real(x, "theta", -8, 8) for x in theta],
        "rewards": [_real(x, "reward", -20, 20) for x in rewards],
        "noise_sd": _real(parameters.get("noise_sd", 0), "noise_sd", 0, 10),
        "baseline_mode": parameters.get("baseline_mode", "none"),
        "baseline": _real(parameters.get("baseline", 0), "baseline", -20, 20),
        "step": _real(parameters.get("step", 0.5), "step", 0, 10),
    }
    if out["baseline_mode"] not in BASELINE_MODES:
        raise ValueError("policy_gradient: baseline_mode must be none, constant or expected")
    batch, seed = parameters.get("batch", 16), parameters.get("seed", 1)
    if type(batch) is not int or not 1 <= batch <= MAX_BATCH:
        raise ValueError(f"policy_gradient: batch must be an integer in [1, {MAX_BATCH}]")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("policy_gradient: seed must be an unsigned 32-bit integer")
    out["batch"], out["seed"] = batch, seed
    return out


def softmax(theta):
    top = max(theta)
    e = [math.exp(x - top) for x in theta]
    s = math.fsum(e)
    return [x / s for x in e]


def score(pi, action):
    """Gradient of log softmax_action with respect to the logits: e_action - pi."""
    return [(1.0 if j == action else 0.0) - p for j, p in enumerate(pi)]


def mulberry32(seed):
    state = seed & 0xFFFFFFFF

    def draw():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
    return draw


def exact(theta, rewards, noise_sd=0.0):
    pi = softmax(theta)
    value = math.fsum(p * r for p, r in zip(pi, rewards))
    grad = [p * (r - value) for p, r in zip(pi, rewards)]
    weights = [math.fsum(x * x for x in score(pi, a)) for a in range(len(pi))]
    norm2 = math.fsum(g * g for g in grad)

    def variance(b):
        return math.fsum(p * ((r - b) ** 2 + noise_sd ** 2) * w
                         for p, r, w in zip(pi, rewards, weights)) - norm2
    mass = math.fsum(p * w for p, w in zip(pi, weights))
    best = math.fsum(p * w * r for p, w, r in zip(pi, weights, rewards)) / mass
    return {"pi": pi, "J": value, "grad": grad, "weights": weights,
            "variance": variance, "b_opt": best}


def compute(parameters):
    p = check(parameters)
    ex = exact(p["theta"], p["rewards"], p["noise_sd"])
    pi = ex["pi"]
    b = {"none": 0.0, "constant": p["baseline"], "expected": ex["J"]}[p["baseline_mode"]]
    draw = mulberry32(p["seed"])
    k = len(pi)
    actions, returns, estimate = [], [], [0.0] * k
    counts = [0] * k
    for _ in range(p["batch"]):
        u = draw()
        a, acc = k - 1, 0.0
        for j, prob in enumerate(pi):
            acc += prob
            if u < acc:
                a = j
                break
        u1, u2 = draw(), draw()
        eps = math.sqrt(-2.0 * math.log(1.0 - u1)) * math.cos(2.0 * math.pi * u2)
        ret = p["rewards"][a] + p["noise_sd"] * eps
        actions.append(a)
        returns.append(ret)
        counts[a] += 1
        for j, s in enumerate(score(pi, a)):
            estimate[j] += (ret - b) * s / p["batch"]
    estimate_none = [0.0] * k
    for a, ret in zip(actions, returns):
        for j, s in enumerate(score(pi, a)):
            estimate_none[j] += ret * s / p["batch"]
    updated = [t + p["step"] * g for t, g in zip(p["theta"], estimate)]
    exact_step = [t + p["step"] * g for t, g in zip(p["theta"], ex["grad"])]
    new_pi = softmax(updated)
    var_b = ex["variance"](b)

    def first(base):  # variance of the first component of the single-sample estimator
        return math.fsum(q * ((r - base) ** 2 + p["noise_sd"] ** 2) * score(pi, a)[0] ** 2
                         for a, (q, r) in enumerate(zip(pi, p["rewards"]))) - ex["grad"][0] ** 2
    result = {
        "model": MODEL, "parameters": p, "pi": pi, "J": ex["J"], "grad": ex["grad"],
        "baseline": b, "b_opt": ex["b_opt"],
        "variance_none": ex["variance"](0.0) / p["batch"],
        "variance_baseline": var_b / p["batch"],
        "variance_expected": ex["variance"](ex["J"]) / p["batch"],
        "variance_optimal": ex["variance"](ex["b_opt"]) / p["batch"],
        "variance_first_none": first(0.0) / p["batch"], "variance_first_baseline": first(b) / p["batch"],
        "actions": actions, "returns": returns, "counts": counts,
        "estimate": estimate, "estimate_none": estimate_none, "theta_new": updated, "pi_new": new_pi,
        "J_new": math.fsum(q * r for q, r in zip(new_pi, p["rewards"])),
        "theta_exact_step": exact_step,
    }
    if abs(math.fsum(ex["grad"])) > 1e-12:
        raise ValueError("policy_gradient: softmax gradient components must sum to zero")
    return result
