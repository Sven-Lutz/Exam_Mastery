"""Plane transformation scene: a real 2x2 matrix A acting on the plane, shown as a continuous morph from the identity.

The scene state at time t in [0, 1] is M(t) = (1 - t) I + t A (entrywise straight path). Everything the book figure,
the explorable and the card show is computed here (and mirrored 1:1 in templates/plane_map_math.js, parity-tested):
images of the standard basis (= columns of M), the image of a test vector, det M(t) as the signed area of the image of
the unit square, rank, kernel and image (exact rational arithmetic), and the times at which the straight path is
singular. A path from I to a matrix with det A < 0 must cross det = 0 (intermediate value theorem), so such scenes
always contain a collapse to a line or point. No course content lives here; it is a reusable domain model.
"""
from fractions import Fraction
import math

LIMIT = 6          # |entries| and |vector components| (keeps every scene readable)
EPS = 1e-12


def _q(x, name):
    if isinstance(x, bool) or not isinstance(x, (int, float, str)):
        raise ValueError(f"{name}: number required")
    try:
        q = Fraction(str(x)) if not isinstance(x, int) else Fraction(x)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"{name}: number required") from None
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{name}: finite number required")
    if abs(q) > LIMIT:
        raise ValueError(f"{name}: |value| <= {LIMIT} required")
    return q


def parse(parameters):
    if not isinstance(parameters, dict) or not {"matrix", "vector"} <= set(parameters) or \
            set(parameters) - {"matrix", "vector", "t"}:
        raise ValueError("plane map: parameters {matrix, vector[, t]} required")
    m = parameters["matrix"]
    if not (isinstance(m, list) and len(m) == 2 and all(isinstance(r, list) and len(r) == 2 for r in m)):
        raise ValueError("plane map: matrix must be 2x2")
    v = parameters["vector"]
    if not (isinstance(v, list) and len(v) == 2):
        raise ValueError("plane map: vector must have 2 components")
    t = _q(parameters.get("t", 1), "t")
    if not 0 <= t <= 1:
        raise ValueError("plane map: t in [0, 1] required")
    return ([[_q(m[i][j], f"matrix[{i}][{j}]") for j in range(2)] for i in range(2)],
            [_q(v[i], f"vector[{i}]") for i in range(2)], t)


def at(A, t):
    """M(t) = (1 - t) I + t A."""
    return [[(1 - t) * (1 if i == j else 0) + t * A[i][j] for j in range(2)] for i in range(2)]


def apply(M, v):
    return [M[0][0] * v[0] + M[0][1] * v[1], M[1][0] * v[0] + M[1][1] * v[1]]


def det(M):
    return M[0][0] * M[1][1] - M[0][1] * M[1][0]


def primitive(u):
    """Scale a nonzero rational vector to coprime integers with a positive first nonzero entry: (1/2, -1/2) -> (1, -1)."""
    q = [Fraction(x) for x in u]
    den = math.lcm(*(x.denominator for x in q))
    ints = [int(x * den) for x in q]
    g = math.gcd(*ints) or 1
    ints = [x // g for x in ints]
    sign = -1 if next(x for x in ints if x) < 0 else 1
    return [sign * x for x in ints]


def kernel_image(M):
    """Exact rank, a kernel basis and an image basis of a 2x2 matrix."""
    if det(M) != 0:
        return 2, [], [[1, 0], [0, 1]]
    if all(x == 0 for row in M for x in row):
        return 0, [[1, 0], [0, 1]], []
    row = M[0] if M[0] != [0, 0] else M[1]
    ker = [row[1], -row[0]]                     # orthogonal to the nonzero row: M ker = 0 since rows are dependent
    col = [M[0][0], M[1][0]] if [M[0][0], M[1][0]] != [0, 0] else [M[0][1], M[1][1]]
    return 1, [primitive(ker)], [primitive(col)]


def singular_times(A):
    """All t in [0, 1] with det M(t) = 0: det = 1 + t (tr A - 2) + t^2 (1 - tr A + det A)."""
    tr, D = A[0][0] + A[1][1], det(A)
    a, b, c = 1 - tr + D, tr - 2, Fraction(1)
    if a == 0:
        return [] if b == 0 else [float(r) for r in [-c / b] if 0 <= -c / b <= 1]
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    root = math.sqrt(disc)
    roots = sorted({(-float(b) - root) / (2 * float(a)), (-float(b) + root) / (2 * float(a))})
    return [r for r in roots if -EPS <= r <= 1 + EPS]


def compute(parameters):
    A, v, t = parse(parameters)
    M = at(A, t)
    rank, ker, img = kernel_image(M)
    d = det(M)
    f = lambda xs: [float(x) for x in xs]  # noqa: E731
    return {
        "parameters": {"matrix": [f(r) for r in A], "vector": f(v), "t": float(t)},
        "t": float(t), "M": [f(r) for r in M], "A": [f(r) for r in A],
        "e1": f([M[0][0], M[1][0]]), "e2": f([M[0][1], M[1][1]]), "v": f(v), "Mv": f(apply(M, v)),
        "Av": f(apply(A, v)), "det": float(d), "det_A": float(det(A)),
        "det_exact": str(d), "det_A_exact": str(det(A)),
        "orientation": "positiv" if d > 0 else ("negativ" if d < 0 else "kollabiert"),
        "rank": rank, "kernel": [f(k) for k in ker], "image": [f(c) for c in img],
        "rank_A": kernel_image(A)[0], "kernel_A": [f(k) for k in kernel_image(A)[1]],
        "image_A": [f(c) for c in kernel_image(A)[2]],
        "singular_times": singular_times(A),
    }
