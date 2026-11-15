"""Unabhängige Prüfung der eigenen Analysis-Beispiele und Aufgaben (exakte Brüche, Dezimalarithmetik hoher Präzision)."""
import math
from decimal import Decimal, getcontext
from fractions import Fraction as Fr

getcontext().prec = 60
SQRT2 = Decimal(2).sqrt()


def heron():
    """E1: Heron/Newton für √2 – exakte Glieder, Fehleridentität, Monotonie, Q unvollständig."""
    a = [Fr(2)]
    for _ in range(5):
        a.append((a[-1] + 2 / a[-1]) / 2)
    assert [str(x) for x in a[:5]] == ['2', '3/2', '17/12', '577/408', '665857/470832']
    for x, y in zip(a, a[1:]):
        assert y < x, 'monoton fallend'
        assert y * y > 2, 'a_n^2 > 2: untere Schranke √2'
        e0 = Decimal(x.numerator) / Decimal(x.denominator) - SQRT2
        e1 = Decimal(y.numerator) / Decimal(y.denominator) - SQRT2
        assert abs(e1 - e0 * e0 / (2 * Decimal(x.numerator) / Decimal(x.denominator))) < Decimal('1e-50'), 'e_{n+1} = e_n^2/(2a_n)'
    errs = [float(Decimal(x.numerator) / Decimal(x.denominator) - SQRT2) for x in a]
    # Cauchy in Q, aber Grenzwert irrational: kein Grenzwert in Q (√2 ∉ Q, klassischer Beweis im Text)
    assert all(isinstance(x, Fr) for x in a)
    neg = [-1.0]
    for _ in range(8):
        neg.append((neg[-1] + 2 / neg[-1]) / 2)
    assert abs(neg[-1] + math.sqrt(2)) < 1e-12, 'negativer Start -> -√2'
    return {'terms': [str(x) for x in a[:5]], 'errors': [f'{e:.3e}' for e in errs], 'negative_start_limit': '-√2'}


def contraction():
    """E2: cos ist auf [cos 1, 1] eine Kontraktion (q = sin 1); x + 1/x ist kontraktiv, aber keine Kontraktion und ohne Fixpunkt."""
    c = math.cos(1)
    assert c <= math.cos(c) <= 1 and c <= math.cos(1) <= 1, 'cos bildet [cos1, 1] in sich ab'
    q = math.sin(1)
    assert q < 1
    d1 = 1 - math.cos(1)
    n = 1
    while q ** (n - 1) / (1 - q) * d1 > 1e-3:
        n += 1
    assert n == 48, n
    o = [1.0]
    for _ in range(60):
        o.append(math.cos(o[-1]))
    L = 0.7390851332151607
    actual = next(i + 1 for i, v in enumerate(o) if abs(v - L) <= 1e-3)
    assert actual == 16 and actual <= n
    x = [1.0]
    for _ in range(200):
        x.append(x[-1] + 1 / x[-1])
    for i in range(1, 50):  # a_{n+1}^2 = a_n^2 + 2 + 1/a_n^2 > a_n^2 + 2
        assert x[i] ** 2 > x[i - 1] ** 2 + 2 - 1e-12
    for u, v in ((1.0, 2.0), (3.0, 10.0), (100.0, 101.0)):
        fu, fv = u + 1 / u, v + 1 / v
        assert abs(fu - fv) < abs(u - v)
    assert abs((100.0 + 1 / 100) - (101.0 + 1 / 101)) / 1.0 > 0.9999, 'Quotient -> 1: kein q < 1'
    return {'q': round(q, 4), 'apriori_n_1e-3': n, 'actual_n_1e-3': actual, 'x_plus_1_over_x_a200': round(x[200], 3)}


def task_minN():
    assert Fr(7, 698 + 3) < Fr(1, 100) and not Fr(7, 697 + 3) < Fr(1, 100)
    return {'N': 698}
