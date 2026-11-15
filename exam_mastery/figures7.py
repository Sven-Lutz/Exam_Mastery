"""Originalgrafiken der Referenzsequenz „Self-Attention: Softmax und Konvexkombination“ (v7).

Alle Zahlen werden hier aus denselben Gleichungen berechnet wie im Text (reference_unit.attn_full) – keine
handgesetzten Werte. Ausgabe: inline-SVG mit semantischen CSS-Klassen aus design_tokens.css, damit Farben in
HTML, PDF und Dunkelmodus identisch zur Formel sind (Query blau, Keys bernstein, Values petrol, Gewichte violett,
Ausgabe karmin). Platzhalter im Text: <div class="fig-ph" data-fig="NAME"></div>.
"""
from __future__ import annotations

import math
import random


def de(x, d=2):
    s = f'{x:.{d}f}'.replace('.', ',')
    return s.replace('-', '−')


def sub(base, idx):
    """Echter Index statt Unicode-Tiefstellung (die in vielen Schriften schlecht setzt)."""
    return f'{base}<tspan baseline-shift="sub" font-size="72%">{idx}</tspan>'


def _title(W, title, subtitle=None):
    s = f'<text x="20" y="26" class="t-lab">{title}</text>'
    if subtitle:
        s += f'<text x="20" y="46" class="t-small t-mute">{subtitle}</text>'
    return s


def _svg(w, h, body, label):
    return f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def _arrow(x1, y1, x2, y2, cls, w=2.6, head=10, dash=None):
    L = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    bx, by = x2 - ux * head, y2 - uy * head
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" class="{cls}" stroke-width="{w}" stroke-linecap="round"{d}/>'
            f'<polygon points="{x2:.1f},{y2:.1f} {bx - uy * head * .45:.1f},{by + ux * head * .45:.1f} {bx + uy * head * .45:.1f},{by - ux * head * .45:.1f}" class="{cls.replace("s-", "f-")}"/>')


def fig_projection(bank, R):
    """Skalarprodukt als Projektion: q und drei Keys, Lote auf die q-Gerade; Scores in einer Legende (keine Kollisionen)."""
    W, H, sc = 720, 430, 100
    ox, oy = 280, 250                      # Ursprung; Zeichenfläche y ∈ [70, 400]
    P = lambda x, y: (ox + x * sc, oy - y * sc)
    q, K, names = bank['q'], bank['K'], ['Fluss', 'Geld', 'der']
    nq = math.hypot(*q); u = (q[0] / nq, q[1] / nq)
    b = _title(W, 'Skalarprodukt = Länge von q × vorzeichenbehafteter Schatten', 'Gestrichelt: Lot von jedem Key auf die Gerade durch q. Schatten hinter dem Ursprung ⇒ negativer Score.')
    clip = '<clipPath id="pc"><rect x="20" y="62" width="500" height="352"/></clipPath>'
    g = ''
    for gx in range(-2, 3):
        g += f'<line x1="{P(gx, -1.5)[0]}" y1="{P(gx, -1.5)[1]}" x2="{P(gx, 1.5)[0]}" y2="{P(gx, 1.5)[1]}" class="grid"/>'
    for gy in range(-1, 2):
        g += f'<line x1="{P(-2.4, gy)[0]}" y1="{P(-2.4, gy)[1]}" x2="{P(2, gy)[0]}" y2="{P(2, gy)[1]}" class="grid"/>'
    a1, a2 = P(-u[0] * 2.4, -u[1] * 2.4), P(u[0] * 2.2, u[1] * 2.2)
    g += f'<line x1="{a1[0]:.1f}" y1="{a1[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" class="s-q" stroke-width="1.2" stroke-dasharray="2 5"/>'
    lab_off = {'Fluss': (-4, -14, 'end'), 'Geld': (-12, 6, 'end'), 'der': (-14, 26, 'end')}
    foot_off = {0: (-12, -8), 1: (-12, -8), 2: (14, 20)}
    for j, (k, nm) in enumerate(zip(K, names)):
        tproj = k[0] * u[0] + k[1] * u[1]; foot = (u[0] * tproj, u[1] * tproj)
        kx, ky = P(*k); fx, fy = P(*foot)
        g += f'<line x1="{kx:.1f}" y1="{ky:.1f}" x2="{fx:.1f}" y2="{fy:.1f}" class="s-k" stroke-width="1.3" stroke-dasharray="4 3"/>'
        g += f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="4.5" class="f-k"/><text x="{fx + foot_off[j][0]:.1f}" y="{fy + foot_off[j][1]:.1f}" text-anchor="middle" class="t-small f-k" font-weight="700">{j + 1}</text>'
        g += _arrow(*P(0, 0), kx, ky, 's-k', 2.4)
        dx, dy, anc = lab_off[nm]
        g += f'<text x="{kx + dx:.1f}" y="{ky + dy:.1f}" class="t-lab f-k" text-anchor="{anc}">{sub("k", nm)}</text>'
    qx, qy = P(*q)
    g += _arrow(*P(0, 0), qx, qy, 's-q', 3.6)
    g += f'<text x="{qx - 26:.1f}" y="{qy + 6:.1f}" class="t-lab f-q">q</text>'
    b += clip + f'<g clip-path="url(#pc)">{g}</g>'
    # Legende rechts
    lx = 540
    b += f'<text x="{lx}" y="90" class="t-lab">Scores q·k</text>'
    for j, nm in enumerate(names):
        y = 120 + j * 34
        b += f'<circle cx="{lx + 6}" cy="{y - 5}" r="9" class="f-k"/><text x="{lx + 6}" y="{y - 1}" text-anchor="middle" font-size="11" fill="#fff" font-weight="700">{j + 1}</text>'
        b += f'<text x="{lx + 22}" y="{y}" class="t-small">{nm}: <tspan font-weight="700">{de(R["raw"][j], 2)}</tspan></text>'
    b += f'<text x="{lx}" y="240" class="t-small t-mute">q = ({de(q[0], 1)}; {de(q[1], 1)}), ‖q‖ = {de(nq, 3)}</text>'
    b += f'<text x="{lx}" y="262" class="t-small t-mute">Score = ‖q‖ · Schatten</text>'
    return _svg(W, H, b, 'Query q und drei Keys mit ihren Projektionen auf die Richtung von q')


def fig_pipeline(R):
    """Scores → Exponenten → Gewichte: drei Balkengruppen mit allen Zwischenzahlen."""
    names = ['Fluss', 'Geld', 'der']
    W, H = 700, 380
    cols = [('Score s = q·k / √2', R['e'], 's', 2), ('exp(s)', R['exp'], 'k', 4), ('Gewicht w = exp(s) / Σ', R['w'], 'w', 4)]
    b = ''
    base = 175
    for c, (title, vals, cls, dg) in enumerate(cols):
        x0 = 24 + c * 228
        mx = max(abs(v) for v in vals) or 1
        b += f'<text x="{x0}" y="32" class="t-lab">{title}</text>'
        b += f'<line x1="{x0}" y1="{base}" x2="{x0 + 190}" y2="{base}" class="ax"/>'
        for j, v in enumerate(vals):
            hgt = 95 * v / mx; x = x0 + 12 + j * 60
            y = base - hgt if hgt >= 0 else base
            b += f'<rect x="{x}" y="{y:.1f}" width="42" height="{abs(hgt):.1f}" class="f-{cls}" opacity=".88"/>'
            ty = (y - 7) if hgt >= 0 else (base + abs(hgt) + 17)
            b += f'<text x="{x + 21}" y="{ty:.1f}" text-anchor="middle" class="t-small">{de(v, dg)}</text>'
            b += f'<text x="{x + 21}" y="300" text-anchor="middle" class="t-small t-mute">{names[j]}</text>'
        if c < 2:
            b += _arrow(x0 + 196, 110, x0 + 222, 110, 's-q' if c == 0 else 's-w', 2, 8)
    b += f'<text x="24" y="{H - 44}" class="t-small">Σ exp(s) = {de(R["Z"][0], 4)}   ·   Σ w = {de(sum(R["w"]), 4)}   ·   Reihenfolge erhalten, alle Gewichte positiv.</text>'
    b += f'<text x="24" y="{H - 20}" class="t-small t-mute">Der negative Score (Geld) wird zu einem kleinen, aber positiven Gewicht.</text>'
    return _svg(W, H, b, 'Rechenkette von den Scores über die Exponentialwerte zu den Gewichten')


def fig_temperature(bank):
    """Gewichte als Funktion der Temperatur T (logarithmisch), mit Grenzfällen."""
    from .reference_unit import attn_full
    W, H, x0, y0, w, h = 680, 330, 70, 40, 560, 220
    Ts = [10 ** (-1.3 + 2.6 * i / 200) for i in range(201)]
    curves = [[attn_full(dict(bank, T=T))['w'][j] for T in Ts] for j in range(3)]
    X = lambda T: x0 + (math.log10(T) + 1.3) / 2.6 * w
    Y = lambda p: y0 + h - p * h
    b = f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" class="ax"/>'
    for p in (0, .25, .5, .75, 1):
        b += f'<line x1="{x0}" y1="{Y(p)}" x2="{x0 + w}" y2="{Y(p)}" class="grid"/><text x="{x0 - 8}" y="{Y(p) + 4}" text-anchor="end" class="t-small t-mute">{de(p, 2)}</text>'
    for T in (0.1, 0.3, 1, 3, 10):
        b += f'<line x1="{X(T)}" y1="{y0}" x2="{X(T)}" y2="{y0 + h}" class="grid"/><text x="{X(T)}" y="{y0 + h + 18}" text-anchor="middle" class="t-small t-mute">{de(T, 1) if T < 1 else int(T)}</text>'
    b += f'<line x1="{x0}" y1="{Y(1 / 3)}" x2="{x0 + w}" y2="{Y(1 / 3)}" class="s-w" stroke-dasharray="3 4" stroke-width="1"/><text x="{x0 + 8}" y="{Y(1 / 3) - 6}" class="t-small f-w">1/3 (Grenzwert für T → ∞)</text>'
    styles = [('s-v', '', 'Fluss'), ('s-k', '6 4', 'Geld'), ('s-o', '2 3', 'der')]
    for j, (cls, dash, nm) in enumerate(styles):
        pts = ' '.join(f'{X(T):.1f},{Y(p):.1f}' for T, p in zip(Ts, curves[j]))
        b += f'<polyline points="{pts}" fill="none" class="{cls}" stroke-width="2.6"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'
        ly = y0 + 62 + j * 22
        b += f'<line x1="{x0 + 24}" y1="{ly - 4}" x2="{x0 + 54}" y2="{ly - 4}" class="{cls}" stroke-width="2.6"' + (f' stroke-dasharray="{dash}"' if dash else '') + f'/><text x="{x0 + 62}" y="{ly}" class="t-small">{nm}</text>'
    w1 = attn_full(dict(bank, T=1))['w']
    b += f'<line x1="{X(1)}" y1="{y0}" x2="{X(1)}" y2="{y0 + h}" class="s-q" stroke-width="1.5"/><text x="{X(1) + 6}" y="{y0 + 14}" class="t-small f-q">T = 1: ({de(w1[0], 3)}; {de(w1[1], 3)}; {de(w1[2], 3)})</text>'
    b += f'<text x="{x0}" y="22" class="t-lab">Gewichte w(T) für die Scores des Bank-Beispiels</text>'
    b += f'<text x="{x0 + w / 2}" y="{H - 8}" text-anchor="middle" class="t-small t-mute">Temperatur T (logarithmische Achse)  ·  T → 0: alles Gewicht auf den größten Score</text>'
    return _svg(W, H, b, 'Verlauf der drei Gewichte in Abhängigkeit von der Temperatur')


def fig_simplex(bank):
    """Wahrscheinlichkeitssimplex Δ²: jeder Gewichtsvektor ist ein Punkt im Dreieck; Bahn über T."""
    from .reference_unit import attn_full
    W, H = 700, 440
    A, B, C = (350, 92), (110, 380), (590, 380)        # Ecken: Fluss, Geld, der
    pt = lambda w: (w[0] * A[0] + w[1] * B[0] + w[2] * C[0], w[0] * A[1] + w[1] * B[1] + w[2] * C[1])
    b = _title(W, f'Der Simplex: alle ({sub("w", 1)}, {sub("w", 2)}, {sub("w", 3)}) mit {sub("w", "j")} ≥ 0 und Summe 1',
               'Jeder Punkt im Dreieck ist eine mögliche Verteilung der Aufmerksamkeit; Ecken = alles auf ein Wort.')
    b += f'<polygon points="{A[0]},{A[1]} {B[0]},{B[1]} {C[0]},{C[1]}" fill="none" class="s-w" stroke-width="1.6"/>'
    for (x, y), nm, dx, dy, anc in ((A, 'Ecke „Fluss“: w = (1, 0, 0)', 14, 4, 'start'), (B, 'Ecke „Geld“', 0, 24, 'middle'), (C, 'Ecke „der“', 0, 24, 'middle')):
        b += f'<circle cx="{x}" cy="{y}" r="4.5" class="f-w"/><text x="{x + dx}" y="{y + dy}" text-anchor="{anc}" class="t-small">{nm}</text>'
    Ts = [10 ** (-1.2 + 2.4 * i / 120) for i in range(121)]
    path = [pt(attn_full(dict(bank, T=T))['w']) for T in Ts]
    b += '<polyline points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in path) + '" fill="none" class="s-w" stroke-width="2.6"/>'
    for T, lab in ((0.25, 'T = 0,25'), (1, 'T = 1 (Beispiel)'), (4, 'T = 4')):
        w_ = attn_full(dict(bank, T=T))['w']; x, y = pt(w_)
        b += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6.5 if T == 1 else 5}" class="f-o"/><text x="{x + 12:.1f}" y="{y + 5:.1f}" class="t-small">{lab}</text>'
    g = pt([1 / 3] * 3)
    b += f'<circle cx="{g[0]:.1f}" cy="{g[1]:.1f}" r="5" fill="none" class="s-w" stroke-width="1.8"/><text x="{g[0] - 10:.1f}" y="{g[1] + 22:.1f}" text-anchor="end" class="t-small t-mute">Mitte: Gleichverteilung (T → ∞)</text>'
    b += f'<text x="20" y="{H - 14}" class="t-small t-mute">Violette Bahn: Softmax-Gewichte des Bank-Beispiels für T von 0,06 bis 16 (logarithmisch abgetastet).</text>'
    return _svg(W, H, b, 'Wahrscheinlichkeitssimplex mit der Bahn der Gewichte bei variabler Temperatur')


def fig_hull(bank, R):
    """Werteraum: Values, konvexe Hülle, nummerierte Pfeilkette w_j v_j, Ausgabe o; Legende statt Beschriftung an den Pfeilen."""
    W, H, sc, ox, oy = 740, 440, 150, 70, 370
    P = lambda x, y: (ox + x * sc, oy - y * sc)
    V, names = bank['V'], ['Fluss', 'Geld', 'der']
    b = _title(W, 'Werteraum: Die Ausgabe ist ein gewichteter Mittelwert der Values', 'Getönt: konvexe Hülle – alle Mischungen mit Gewichten ≥ 0 und Summe 1.')
    for gx in range(0, 3):
        b += f'<line x1="{P(gx, -0.15)[0]}" y1="{P(gx, -0.15)[1]}" x2="{P(gx, 2.05)[0]}" y2="{P(gx, 2.05)[1]}" class="grid"/><text x="{P(gx, 0)[0]}" y="{P(gx, 0)[1] + 34}" text-anchor="middle" class="t-small t-mute">{gx}</text>'
    for gy in range(0, 3):
        b += f'<line x1="{P(-0.1, gy)[0]}" y1="{P(-0.1, gy)[1]}" x2="{P(2.6, gy)[0]}" y2="{P(2.6, gy)[1]}" class="grid"/>'
    b += '<polygon points="' + ' '.join(f'{P(*v)[0]:.1f},{P(*v)[1]:.1f}' for v in V) + '" class="f-hull" opacity=".95"/>'
    offs = {'Fluss': (10, 22, 'start'), 'Geld': (12, 4, 'start'), 'der': (-10, -10, 'end')}
    for v, nm in zip(V, names):
        x, y = P(*v); dx, dy, anc = offs[nm]
        b += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" class="f-v"/><text x="{x + dx:.1f}" y="{y + dy:.1f}" text-anchor="{anc}" class="t-lab f-v">{sub("v", nm)}</text>'
    acc = (0.0, 0.0)
    b += f'<circle cx="{P(0, 0)[0]}" cy="{P(0, 0)[1]}" r="3" class="f-s"/><text x="{P(0, 0)[0] - 8}" y="{P(0, 0)[1] + 4}" text-anchor="end" class="t-small t-mute">0</text>'
    for j, v in enumerate(V):
        nxt = (acc[0] + R['w'][j] * v[0], acc[1] + R['w'][j] * v[1])
        b += _arrow(*P(*acc), *P(*nxt), 's-w', 2.6, 9)
        acc = nxt
    ox_, oy_ = P(*R['o'])
    b += f'<circle cx="{ox_:.1f}" cy="{oy_:.1f}" r="7.5" class="f-o"/><text x="{ox_ + 12:.1f}" y="{oy_ - 12:.1f}" class="t-lab f-o">o</text>'
    zx, zy = P(2.4, 1.6)
    b += f'<circle cx="{zx}" cy="{zy}" r="9" fill="none" class="s-err" stroke-width="2.6"/><text x="{zx}" y="{zy + 28}" text-anchor="middle" class="t-small f-err">Z</text>'
    lx = 500
    b += f'<text x="{lx}" y="120" class="t-lab">Pfeilkette o = Σ w·v</text>'
    for j, nm in enumerate(names):
        y = 148 + j * 26
        b += f'<line x1="{lx}" y1="{y - 5}" x2="{lx + 22}" y2="{y - 5}" class="s-w" stroke-width="2.6"/><text x="{lx + 30}" y="{y}" class="t-small">{j + 1}. {de(R["w"][j], 3)} · {sub("v", nm)}</text>'
    b += f'<text x="{lx}" y="240" class="t-small f-o" font-weight="700">o = ({de(R["o"][0], 3)}; {de(R["o"][1], 3)})</text>'
    b += f'<text x="{lx}" y="266" class="t-small f-err">Z = (2,4; 1,6) liegt außerhalb:</text><text x="{lx}" y="284" class="t-small f-err">keine Query, keine Temperatur</text><text x="{lx}" y="302" class="t-small f-err">erreicht diesen Punkt.</text>'
    return _svg(W, H, b, 'Konvexe Hülle der Values, Ausgabe o als Pfeilkette und ein unerreichbarer Zielpunkt')


def variance_experiment(dims=(1, 2, 4, 8, 16, 32, 64, 128, 256), m=2000, seed=11):
    """Unabhängige Python-Simulation: empirische Varianz von q·k für q, k ~ N(0, I_d)."""
    rng = random.Random(seed)
    out = []
    for d in dims:
        vals = []
        for _ in range(m):
            vals.append(sum(rng.gauss(0, 1) * rng.gauss(0, 1) for _ in range(d)))
        mu = sum(vals) / m
        out.append((d, sum((x - mu) ** 2 for x in vals) / (m - 1)))
    return out


def fig_variance():
    data = variance_experiment()
    W, H, x0, y0, w, h = 680, 320, 70, 40, 560, 220
    X = lambda d: x0 + math.log2(d) / 8 * w
    Y = lambda v: y0 + h - math.log2(v) / 8 * h
    b = f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" class="ax"/>'
    for e in range(0, 9, 2):
        b += f'<line x1="{X(2 ** e)}" y1="{y0}" x2="{X(2 ** e)}" y2="{y0 + h}" class="grid"/><text x="{X(2 ** e)}" y="{y0 + h + 18}" text-anchor="middle" class="t-small t-mute">{2 ** e}</text>'
        b += f'<line x1="{x0}" y1="{Y(2 ** e)}" x2="{x0 + w}" y2="{Y(2 ** e)}" class="grid"/><text x="{x0 - 8}" y="{Y(2 ** e) + 4}" text-anchor="end" class="t-small t-mute">{2 ** e}</text>'
    b += f'<line x1="{X(1)}" y1="{Y(1)}" x2="{X(256)}" y2="{Y(256)}" class="s-q" stroke-width="2"/><text x="{X(64) - 4}" y="{Y(64) - 10}" text-anchor="end" class="t-small f-q">Satz 3: Var(q·k) = {sub("d", "k")}</text>'
    for d, v in data:
        b += f'<circle cx="{X(d):.1f}" cy="{Y(v):.1f}" r="5" class="f-o"/>'
        b += f'<rect x="{X(d) - 4:.1f}" y="{Y(v / d) - 4:.1f}" width="8" height="8" class="f-v"/>'
    b += f'<line x1="{x0}" y1="{Y(1)}" x2="{x0 + w}" y2="{Y(1)}" class="s-v" stroke-dasharray="5 4" stroke-width="1.5"/><text x="{x0 + w - 4}" y="{Y(1) - 6}" text-anchor="end" class="t-small f-v">nach Teilen durch √{sub("d", "k")}: Varianz ≈ 1 (Quadrate)</text>'
    b += f'<text x="{x0}" y="22" class="t-lab">Gemessene Varianz von q·k (Punkte, 2000 Ziehungen je {sub("d", "k")}) gegen Satz 3</text>'
    b += f'<text x="{x0 + w / 2}" y="{H - 8}" text-anchor="middle" class="t-small t-mute">Dimension {sub("d", "k")} (beide Achsen logarithmisch, Basis 2)</text>'
    return _svg(W, H, b, 'Empirische Varianz des Skalarprodukts in Abhängigkeit von der Dimension'), data


def render_all(bank):
    from .reference_unit import attn_full
    R = attn_full(bank)
    v, _ = fig_variance()
    return {'projection': fig_projection(bank, R), 'pipeline': fig_pipeline(R), 'temperature': fig_temperature(bank),
            'simplex': fig_simplex(bank), 'hull': fig_hull(bank, R), 'variance': v}
