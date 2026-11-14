"""Reference computations for sequence-labelling evaluation and bidirectional RNNs.

Every number printed in the NLP reference unit is recomputed from these functions by
``exam_mastery.reference_unit.verify``. Exact arithmetic uses ``fractions.Fraction``.

Conventions (stated explicitly because libraries differ):
- BIO decoding follows the CoNLL ``conlleval`` reading: an ``I-X`` that does not continue a
  span of type X opens a new span of type X.
- Span (phrase) level: a predicted span is a true positive only if start, end and type match
  a gold span exactly. Otherwise it is a false positive, and the unmatched gold span a false
  negative (a type or boundary error therefore costs one FP *and* one FN).
- Token level: each token whose gold or predicted label is not ``O`` is compared by entity
  type (B/I prefix ignored). gold==pred!=O -> TP; pred!=O and pred!=gold -> FP;
  gold!=O and gold!=pred -> FN. A token with gold LOC and pred ORG is FP for ORG and FN for LOC.
- 0/0 is reported as ``None`` (undefined); callers decide the convention and must say so.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math


def spans(tags):
    """Return the set of (start, end_exclusive, type) spans encoded by a BIO tag list."""
    out, cur = [], None
    for i, t in enumerate(list(tags) + ['O']):
        if t == 'O' or t.startswith('B-') or (t.startswith('I-') and (cur is None or cur[2] != t[2:])):
            if cur is not None:
                out.append((cur[0], i, cur[2]))
                cur = None
            if t != 'O':
                cur = [i, None, t[2:]]
        elif not (t.startswith('I-') and cur is not None):
            raise ValueError(f'invalid tag {t!r}')
    return set(out)


@dataclass(frozen=True)
class Counts:
    tp: int
    fp: int
    fn: int

    def __add__(self, o):
        return Counts(self.tp + o.tp, self.fp + o.fp, self.fn + o.fn)


def ratio(a, b):
    return None if b == 0 else Fraction(a, b)


def precision(c: Counts):
    return ratio(c.tp, c.tp + c.fp)


def recall(c: Counts):
    return ratio(c.tp, c.tp + c.fn)


def f1(c: Counts):
    """Count form 2TP/(2TP+FP+FN); defined whenever at least one gold or predicted item exists."""
    return ratio(2 * c.tp, 2 * c.tp + c.fp + c.fn)


def f_beta(p, r, beta):
    if p is None or r is None:
        return None
    b2 = Fraction(beta) ** 2
    den = b2 * p + r
    return None if den == 0 else (1 + b2) * p * r / den


def span_counts(gold, pred, types=None):
    g, p = spans(gold), spans(pred)
    if types is not None:
        g = {s for s in g if s[2] in types}
        p = {s for s in p if s[2] in types}
    return Counts(len(g & p), len(p - g), len(g - p))


def _typ(t):
    return 'O' if t == 'O' else t[2:]


def token_counts(gold, pred, types=None):
    tp = fp = fn = 0
    for g, p in zip(gold, pred, strict=True):
        g, p = _typ(g), _typ(p)
        if g == p:
            if g != 'O' and (types is None or g in types):
                tp += 1
            continue
        if p != 'O' and (types is None or p in types):
            fp += 1
        if g != 'O' and (types is None or g in types):
            fn += 1
    return Counts(tp, fp, fn)


def per_type(gold, pred, level='span'):
    fn_ = span_counts if level == 'span' else token_counts
    types = sorted({s[2] for s in spans(gold) | spans(pred)})
    return {t: fn_(gold, pred, {t}) for t in types}


def micro(per: dict):
    total = Counts(0, 0, 0)
    for c in per.values():
        total = total + c
    return {'P': precision(total), 'R': recall(total), 'F1': f1(total), 'counts': total}


def macro(per: dict, zero_division=0):
    """Macro-F1 as the unweighted mean of per-class F1 (an undefined class F1 counts as ``zero_division``)."""
    vals = [f1(c) for c in per.values()]
    vals = [Fraction(zero_division) if v is None else v for v in vals]
    return sum(vals, Fraction(0)) / len(vals)


def macro_of_means(per: dict, zero_division=0):
    """Alternative definition: harmonic mean of macro-averaged P and macro-averaged R."""
    z = Fraction(zero_division)
    ps = [z if precision(c) is None else precision(c) for c in per.values()]
    rs = [z if recall(c) is None else recall(c) for c in per.values()]
    mp, mr = sum(ps, Fraction(0)) / len(ps), sum(rs, Fraction(0)) / len(rs)
    return None if mp + mr == 0 else 2 * mp * mr / (mp + mr)


def rnn_scalar(xs, a, b, c=0.0, reverse=False, h0=0.0):
    """Scalar Elman RNN h_t = tanh(a*h_prev + b*x_t + c); returns states aligned to positions."""
    seq = list(reversed(xs)) if reverse else list(xs)
    h, out = h0, []
    for x in seq:
        h = math.tanh(a * h + b * x + c)
        out.append(h)
    return list(reversed(out)) if reverse else out


def rnn_param_count(d_in, d_h):
    """Parameters of one Elman RNN direction: W_hh (d_h x d_h), W_xh (d_h x d_in), bias d_h."""
    return d_h * d_h + d_h * d_in + d_h


def birnn_tagger_param_count(d_in, d_h, n_labels):
    return 2 * rnn_param_count(d_in, d_h) + n_labels * 2 * d_h + n_labels


def dependence(T, direction):
    """Indices of inputs (1-based) that the state at each position t can depend on."""
    if direction == 'forward':
        return {t: set(range(1, t + 1)) for t in range(1, T + 1)}
    if direction == 'backward':
        return {t: set(range(t, T + 1)) for t in range(1, T + 1)}
    return {t: set(range(1, T + 1)) for t in range(1, T + 1)}
