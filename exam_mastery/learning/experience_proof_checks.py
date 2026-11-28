"""Bounded exact checks for *polynomial identity steps* in authored derivations.

A checked step certifies only the displayed algebraic identity over the real
numbers. It does NOT verify its textual explanation, external premises,
application to a theorem, or the entire proof. Rational expressions,
inequalities, limits and probability arguments require different oracles.
In particular, x/x = 1 is not accepted without domain reasoning.

Untrusted expressions go through the existing closed grammar in learning.expr,
never eval(), Python source execution or unrestricted sympify().
"""
from __future__ import annotations

import math
import re

from . import expr

SCHEMA = "em-proof-check-v1"
VARIABLE = re.compile(r"^[A-Za-z][A-Za-z_0-9]{0,23}$")
MAX_SYMBOLS = 5
MAX_EXPRESSION_CHARS = 220
MAX_AST_NODES = 90
MAX_DEPTH = 24
MAX_DEGREE = 8
MAX_POWER = 5
MAX_COEFFICIENT = 1_000_000


class ProofCheckError(ValueError):
    """Invalid, unsupported or disproved symbolic equality."""


class FalseIdentity(ProofCheckError):
    """Both polynomials are supported and their exact difference is nonzero."""


def _inspect(ast, names, budget, depth=0):
    if depth > MAX_DEPTH:
        raise ProofCheckError("excessive expression depth")
    budget[0] += 1
    if budget[0] > MAX_AST_NODES:
        raise ProofCheckError("excessive expression size")
    kind = ast[0]
    if kind == "n":
        value = ast[1]
        if (type(value) not in (float, int) or
                not math.isfinite(value) or abs(value) > MAX_COEFFICIENT):
            raise ProofCheckError("bounded finite numeric coefficient required")
        return 0
    if kind == "v":
        if ast[1] not in names:
            raise ProofCheckError("undeclared variable")
        return 1
    if kind == "neg":
        return _inspect(ast[1], names, budget, depth + 1)
    if kind in ("+", "-"):
        return max(
            _inspect(ast[1], names, budget, depth + 1),
            _inspect(ast[2], names, budget, depth + 1),
        )
    if kind == "*":
        degree = (
            _inspect(ast[1], names, budget, depth + 1) +
            _inspect(ast[2], names, budget, depth + 1)
        )
        if degree > MAX_DEGREE:
            raise ProofCheckError("polynomial degree limit exceeded")
        return degree
    if kind == "^":
        base_degree = _inspect(ast[1], names, budget, depth + 1)
        exponent = ast[2]
        budget[0] += 1
        if (budget[0] > MAX_AST_NODES or exponent[0] != "n"
                or type(exponent[1]) not in (float, int)
                or not float(exponent[1]).is_integer()
                or not 1 <= exponent[1] <= MAX_POWER):
            raise ProofCheckError("only bounded positive integer powers are supported")
        degree = base_degree * int(exponent[1])
        if degree > MAX_DEGREE:
            raise ProofCheckError("polynomial degree limit exceeded")
        return degree
    # No rational expressions, variable exponents, functions or inequalities.
    raise ProofCheckError(f"unsupported polynomial operation {kind!r}")


def _convert(ast, symbols):
    """Convert only the inspected AST subset, using exact rationals."""
    import sympy as sp

    kind = ast[0]
    if kind == "n":
        return sp.Rational(str(ast[1]))
    if kind == "v":
        return symbols[ast[1]]
    if kind == "neg":
        return -_convert(ast[1], symbols)
    left = _convert(ast[1], symbols)
    right = _convert(ast[2], symbols)
    if kind == "+":
        return left + right
    if kind == "-":
        return left - right
    if kind == "*":
        return left * right
    if kind == "^":
        return left ** int(ast[2][1])
    raise ProofCheckError("unsupported operator")


def verify(check):
    """Prove a bounded polynomial identity *exactly*; fail closed otherwise.

    SymPy builds polynomials over QQ, so the zero difference certifies a
    polynomial identity for every real value of all declared variables.
    A source/model generated identity is *not* evidence that prose is sound.
    """
    if not isinstance(check, dict) or set(check) != {
        "kind", "lhs", "rhs", "variables",
    }:
        raise ProofCheckError("expected exact polynomial-check fields")
    if check["kind"] != "polynomial_identity":
        raise ProofCheckError("unsupported math-check kind")
    names = check["variables"]
    if (not isinstance(names, list) or not 1 <= len(names) <= MAX_SYMBOLS
            or len(set(map(str, names))) != len(names)
            or any(not isinstance(v, str) or not VARIABLE.fullmatch(v) for v in names)):
        raise ProofCheckError("1..5 unique bounded variable identifiers required")
    asts = []
    for field in ("lhs", "rhs"):
        text = check[field]
        if not isinstance(text, str) or not 0 < len(text) <= MAX_EXPRESSION_CHARS:
            raise ProofCheckError(f"{field}: bounded expression required")
        try:
            parsed = expr.parse(text, set(names))
        except (expr.ExprError, TypeError, ValueError, RecursionError) as exc:
            raise ProofCheckError(f"{field}: unsafe or invalid polynomial expression") from exc
        degree = _inspect(parsed, set(names), [0])
        if degree > MAX_DEGREE:
            raise ProofCheckError("polynomial degree limit exceeded")
        asts.append(parsed)
    used = set().union(*(expr.symbols(a) for a in asts))
    if used != set(names):
        raise ProofCheckError("declared variables must match expression variables")
    import sympy as sp

    symbols = {name: sp.Symbol(name, real=True) for name in names}
    left, right = (_convert(a, symbols) for a in asts)
    delta = sp.Poly(left - right, *[symbols[v] for v in names], domain="QQ")
    if not delta.is_zero:
        raise FalseIdentity("polynomial identity is false: nonzero exact difference")
    return {
        "schema": SCHEMA,
        "status": "VERIFIED_POLYNOMIAL_IDENTITY",
        "scope": "ONLY_THE_DISPLAYED_EQUATION_OVER_REAL_VARIABLES",
        "variables": names,
        "latex": r"\(" + sp.latex(left) + " = " + sp.latex(right) + r"\)",
        "method": "EXACT_SYMPY_POLY_QQ",
    }
