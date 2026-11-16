"""Reproducible SVG figures from declared data (B9). No data is invented here: every figure is drawn from a spec whose
values come from the ContentAST (source-anchored or labelled as a didactic example). The same SVG is used in the PDF,
the HTML and the Anki deck, so all products show identical figures.

Spec types: bar, stacked_bar, process, cycle_hub, phases, ladder, share_bars, line, heat_matrix, gantt, adoption_curve.
All text uses the design system's sans font; colours are a calm, print-safe palette that also works in dark mode
(text and strokes use currentColor where the background is transparent).
"""
from html import escape as E

INK = '#1d2a3a'
MUTED = '#5b6878'
LINE = '#c9d1db'
ACCENT = ['#2f5d8a', '#7a9cc0', '#c7a24a', '#8a5a44', '#4e7d6b', '#9a8fbf']
FONT = "'Source Sans 3','Helvetica Neue',Arial,sans-serif"


def _svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{E(title)}" style="font-family:{FONT};max-width:100%;height:auto">'
            f'<title>{E(title)}</title>{body}</svg>')


def _t(x, y, s, size=13, anchor='middle', weight=400, fill=INK, italic=False):
    st = ' font-style="italic"' if italic else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{st}>{E(str(s))}</text>'


def _fmt(v, dec):
    s = f'{v:,.{dec}f}'
    return s.replace(',', ' ')  # thin space as thousands separator, decimal point kept (course: English format)


def bar(spec):
    """{'data': [[label, value], ...], 'unit': 'bn €', 'decimals': 1, 'highlight': [labels], 'note': '...'}"""
    data, dec = spec['data'], spec.get('decimals', 0)
    w, h, left, top, bottom = 640, 300, 40, 30, 50
    n = len(data); slot = (w - left - 20) / n; vmax = max(v for _, v in data) * 1.12
    body = [f'<line x1="{left}" y1="{h-bottom}" x2="{w-20}" y2="{h-bottom}" stroke="{LINE}"/>']
    for i, (lab, v) in enumerate(data):
        bh = (h - top - bottom) * v / vmax; x = left + i * slot + slot * 0.18; bw = slot * 0.64
        col = ACCENT[2] if lab in spec.get('highlight', []) else ACCENT[0]
        body.append(f'<rect x="{x:.1f}" y="{h-bottom-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}" rx="2"/>')
        body.append(_t(x + bw / 2, h - bottom - bh - 6, _fmt(v, dec), 12, weight=600))
        body.append(_t(x + bw / 2, h - bottom + 18, lab, 12, fill=MUTED))
    if spec.get('unit'):
        body.append(_t(left, 16, spec['unit'], 12, 'start', fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Balkendiagramm'))


def stacked_bar(spec):
    """{'categories': [..], 'series': [[name, [values...]], ...], 'totals': True}"""
    cats, series = spec['categories'], spec['series']
    w, h, left, top, bottom = 640, 330, 40, 40, 70
    n = len(cats); slot = (w - left - 20) / n
    tot = [sum(s[1][i] for s in series) for i in range(n)]; vmax = max(tot) * 1.1
    body = [f'<line x1="{left}" y1="{h-bottom}" x2="{w-20}" y2="{h-bottom}" stroke="{LINE}"/>']
    for i, c in enumerate(cats):
        x = left + i * slot + slot * 0.2; bw = slot * 0.6; y = h - bottom
        for k, (name, vals) in enumerate(series):
            bh = (h - top - bottom) * vals[i] / vmax; y -= bh
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{ACCENT[k]}"/>')
            if bh > 15:
                body.append(_t(x + bw / 2, y + bh / 2 + 4, _fmt(vals[i], 0), 11, fill='#ffffff' if k == 0 else INK))
        if spec.get('totals', True):
            body.append(_t(x + bw / 2, y - 6, _fmt(tot[i], 0), 12, weight=600))
        body.append(_t(x + bw / 2, h - bottom + 18, c, 12, fill=MUTED))
    lx = left
    for k, (name, _) in enumerate(series):
        body.append(f'<rect x="{lx}" y="{h-24}" width="12" height="12" fill="{ACCENT[k]}"/>' + _t(lx + 18, h - 14, name, 12, 'start'))
        lx += 26 + 8 * len(name)
    return _svg(w, h, ''.join(body), spec.get('title', 'Gestapeltes Balkendiagramm'))


def _wrap(text, width_px, size):
    """Greedy word wrap for SVG text: about 0.52 em per character in the sans font."""
    per = max(4, int(width_px / (size * 0.52)))
    out, line = [], ''
    for w in str(text).split():
        if line and len(line) + 1 + len(w) > per:
            out.append(line); line = w
        else:
            line = (line + ' ' + w).strip()
    return out + ([line] if line else [])


def _box(x, y, w, h, lines, fill='#f3f6fa', stroke=LINE, bold_first=True):
    lines = [l for i, part in enumerate(lines) for l in (part.split('\n') if i == 0 else _wrap(part.replace('\n', ' '), w - 12, 11.5))]
    out = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="{fill}" stroke="{stroke}"/>']
    y0 = y + h / 2 - (len(lines) - 1) * 8 + 4
    for i, l in enumerate(lines):
        out.append(_t(x + w / 2, y0 + i * 16, l, 13 if i == 0 else 11.5, weight=600 if (i == 0 and bold_first) else 400,
                      fill=INK if i == 0 else MUTED))
    return ''.join(out)


def _arrow(x1, y1, x2, y2, label=None):
    s = f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{MUTED}" stroke-width="1.4" marker-end="url(#ah)"/>'
    if label:
        s += _t((x1 + x2) / 2, (y1 + y2) / 2 - 6, label, 11, fill=MUTED, italic=True)
    return s


DEFS = f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>'


def process(spec):
    """{'steps': [[title, subtitle?], ...], 'loop_label': optional, 'notes': [under each step]}"""
    steps = spec['steps']; n = len(steps)
    w = max(660, 140 * n); bw = (w - 20 - (n - 1) * 26) / n; h = 136 if not spec.get('notes') else 196
    body = [DEFS]
    for i, st in enumerate(steps):
        x = 10 + i * (bw + 26)
        body.append(_box(x, 22, bw, 92, [st[0]] + ([st[1]] if len(st) > 1 and st[1] else [])))
        if i < n - 1:
            body.append(_arrow(x + bw + 2, 68, x + bw + 24, 68))
        if spec.get('notes'):
            for j, line in enumerate(str(spec['notes'][i]).split('\n')):
                body.append(_t(x + bw / 2, 125 + j * 15, line, 11, fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Prozess'))


def cycle_hub(spec):
    """Central system with satellite markets: {'center': [lines], 'inner': [three labels], 'satellites': [[label, side], ...]}"""
    w, h = 640, 380; cx, cy = 320, 190
    body = [DEFS, f'<rect x="{cx-150}" y="{cy-95}" width="300" height="190" rx="10" fill="#f3f6fa" stroke="{LINE}"/>']
    inner = spec.get('inner', [])
    pos = [(cx - 75, cy - 35), (cx + 75, cy - 35), (cx, cy + 50)]
    for (x, y), lab in zip(pos, inner):
        for j, part in enumerate(lab.split('\n')):
            body.append(_t(x, y + j * 15, part, 13, weight=600))
    body.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="none" stroke="{ACCENT[2]}" stroke-width="3"/>'
                f'<path d="M{cx+16},{cy} l-5,-6 l10,0 z" fill="{ACCENT[2]}"/>')
    sat = {'tl': (95, 50), 'tr': (545, 50), 'bl': (95, 330), 'br': (545, 330), 'b': (320, 355)}
    corner = {'tl': (cx - 150, cy - 95), 'tr': (cx + 150, cy - 95), 'bl': (cx - 150, cy + 95), 'br': (cx + 150, cy + 95), 'b': (cx, cy + 95)}
    for lab, side in spec['satellites']:
        x, y = sat[side]; tx, ty = corner[side]
        hl = side == spec.get('highlight')
        body.append(_box(x - 85, y - 18, 170, 36, [lab], fill='#fbf5e6' if hl else '#ffffff', stroke=ACCENT[2] if hl else LINE))
        body.append(f'<line x1="{x:.1f}" y1="{y + (18 if y < cy else -18):.1f}" x2="{tx}" y2="{ty}" stroke="{LINE}" stroke-dasharray="4 3"/>')
    return _svg(w, h, ''.join(body), spec.get('title', 'Wertschöpfungssystem'))


def phases(spec):
    """Lifecycle with financing stages: {'groups': [[name, [phase,...]]], 'rows': [[row label, [[text, span_start, span_end],...]]], 'exit': 'EXIT'}"""
    groups = spec['groups']; cols = sum(len(g[1]) for g in groups)
    w = 660; left = 120; cw = (w - left - 50) / cols
    rows = spec.get('rows', []); h = 110 + 52 * len(rows)
    body = [DEFS]
    c = 0
    for k, (name, ph) in enumerate(groups):
        x = left + c * cw
        body.append(f'<rect x="{x+2:.1f}" y="10" width="{cw*len(ph)-4:.1f}" height="26" rx="4" fill="{ACCENT[k]}"/>' +
                    _t(x + cw * len(ph) / 2, 28, name, 13, weight=600, fill='#ffffff' if k == 0 else INK))
        for j, p in enumerate(ph):
            body.append(_box(x + j * cw + 3, 44, cw - 6, 46, p.split('\n'), bold_first=False))
        c += len(ph)
    body.append(_t(10, 70, spec.get('top_label', 'Lebenszyklus'), 12, 'start', fill=MUTED, weight=600))
    for r, (lab, cells) in enumerate(rows):
        y = 104 + r * 52
        body.append(_t(10, y + 26, lab, 12, 'start', fill=MUTED, weight=600))
        for text, a, b in cells:
            body.append(_box(left + a * cw + 3, y, (b - a) * cw - 6, 40, text.split('\n'), fill='#ffffff', bold_first=False))
    if spec.get('exit'):
        body.append(_arrow(w - 45, h / 2 + 20, w - 8, h / 2 + 20) + _t(w - 26, h / 2 + 10, spec['exit'], 11, weight=600))
    return _svg(w, h, ''.join(body), spec.get('title', 'Phasen'))


def ladder(spec):
    """Ranked classes: {'axis_top': 'höchster Rang', 'axis_bottom': '...', 'rows': [[name, [props...]], ...] (top first)}"""
    rows = spec['rows']; w = 640; rh = 74; h = 30 + rh * len(rows) + 10
    body = [DEFS, _arrow(40, h - 20, 40, 24), _t(30, 16, spec.get('axis_top', ''), 11, 'start', fill=MUTED),
            _t(30, h - 4, spec.get('axis_bottom', ''), 11, 'start', fill=MUTED)]
    for i, (name, props) in enumerate(rows):
        y = 26 + i * rh
        body.append(f'<rect x="60" y="{y}" width="{w-70}" height="{rh-10}" rx="6" fill="#ffffff" stroke="{LINE}"/>'
                    f'<rect x="60" y="{y}" width="8" height="{rh-10}" rx="3" fill="{ACCENT[i]}"/>')
        body.append(_t(80, y + 24, name, 14, 'start', weight=600))
        body.append(_t(80, y + 46, ' · '.join(props), 12, 'start', fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Rangfolge'))


def share_bars(spec):
    """Horizontal 100 % bars per scenario: {'rows': [[label, [[name, value], ...]]], 'unit': '%'}"""
    rows = spec['rows']; w = 640; h = 40 + 46 * len(rows) + 40; left = 120
    names = []
    body = []
    for r, (lab, parts) in enumerate(rows):
        y = 30 + r * 46; tot = sum(v for _, v in parts); x = left
        body.append(_t(left - 10, y + 20, lab, 12, 'end', weight=600))
        for name, v in parts:
            if name not in names:
                names.append(name)
            k = names.index(name); bw = (w - left - 20) * v / tot
            body.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="28" fill="{ACCENT[k]}"/>')
            if bw > 44:
                body.append(_t(x + bw / 2, y + 19, f"{v:.2f}".rstrip('0').rstrip('.') + ' %', 11, fill='#ffffff' if k in (0, 3) else INK))
            x += bw
    lx = left
    for k, name in enumerate(names):
        body.append(f'<rect x="{lx}" y="{h-22}" width="12" height="12" fill="{ACCENT[k]}"/>' + _t(lx + 18, h - 12, name, 12, 'start'))
        lx += 30 + 7 * len(name)
    return _svg(w, h, ''.join(body), spec.get('title', 'Anteile'))


RENDER = {'bar': bar, 'stacked_bar': stacked_bar, 'process': process, 'cycle_hub': cycle_hub, 'phases': phases,
          'ladder': ladder, 'share_bars': share_bars}


# ---------------------------------------------------------------- v0.20 analytic figures (shared by book, app and Anki)

def _nice(lo, hi, n=5):
    import math
    span = (hi - lo) or 1.0
    raw = span / n; mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    a = math.floor(lo / step) * step; b = math.ceil(hi / step) * step
    ticks, v = [], a
    while v <= b + step * 1e-9:
        ticks.append(round(v, 10)); v += step
    return a, b, ticks


def _num(v):
    s = f'{v:,.10g}'.replace(',', ' ')
    return s.replace('-', '−')


def line_chart(spec):
    """{'x': [..] or 'x_labels': [...], 'series': [{'name','values','style': solid|dashed|step,'color': k}],
        'y_label', 'x_label', 'zero': bool, 'marks': [{'x', 'label'}], 'points': [{'x','y','label'}],
        'band': {'from','to','label'}}  — data only, no invented values."""
    xs = spec.get('x') or list(range(1, len(spec['series'][0]['values']) + 1))
    labels = spec.get('x_labels') or [_num(v) for v in xs]
    allv = [v for s_ in spec['series'] for v in s_['values'] if v is not None] + [p['y'] for p in spec.get('points', [])]
    lo, hi = min(allv + ([0] if spec.get('zero', True) else [])), max(allv + ([0] if spec.get('zero', True) else []))
    y0, y1, yt = _nice(lo, hi)
    w, h, L, R, T, B = 640, 320, 62, 18, 26, 54
    X = lambda v: L + (v - xs[0]) / ((xs[-1] - xs[0]) or 1) * (w - L - R)
    Y = lambda v: T + (y1 - v) / ((y1 - y0) or 1) * (h - T - B)
    body = []
    if spec.get('band'):
        bd = spec['band']
        body.append(f'<rect x="{X(bd["from"]):.1f}" y="{T}" width="{X(bd["to"]) - X(bd["from"]):.1f}" height="{h-T-B}" fill="{ACCENT[1]}" opacity=".16"/>'
                    + _t((X(bd['from']) + X(bd['to'])) / 2, T + 13, bd.get('label', ''), 11, fill=MUTED, weight=600))
    for t in yt:
        body.append(f'<line x1="{L}" y1="{Y(t):.1f}" x2="{w-R}" y2="{Y(t):.1f}" stroke="{LINE}" stroke-width="{1.4 if t == 0 else .6}"/>'
                    + _t(L - 8, Y(t) + 4, _num(t), 11, 'end', fill=MUTED))
    step_lab = max(1, len(xs) // 12)
    for i, (v, lab) in enumerate(zip(xs, labels)):
        if i % step_lab == 0 or i == len(xs) - 1:
            body.append(_t(X(v), h - B + 18, lab, 11, fill=MUTED))
    for m in spec.get('marks', []):
        body.append(f'<line x1="{X(m["x"]):.1f}" y1="{T}" x2="{X(m["x"]):.1f}" y2="{h-B}" stroke="{INK}" stroke-dasharray="3 3" stroke-width=".9"/>'
                    + _t(X(m['x']) + (-4 if m.get('side') == 'left' else 4), T + 12 + 13 * m.get('row', 0), m['label'], 11, 'end' if m.get('side') == 'left' else 'start', weight=600))
    names = []
    for k, s_ in enumerate(spec['series']):
        c = ACCENT[s_.get('color', k) % len(ACCENT)]; pts = [(X(x), Y(v)) for x, v in zip(xs, s_['values']) if v is not None]
        if s_.get('style') == 'step':
            d = 'M' + ' '.join(f'{a:.1f},{b:.1f} H{pts[i+1][0]:.1f}' if i + 1 < len(pts) else f'{a:.1f},{b:.1f}' for i, (a, b) in enumerate(pts))
        else:
            d = 'M' + ' L'.join(f'{a:.1f},{b:.1f}' for a, b in pts)
        dash = ' stroke-dasharray="6 4"' if s_.get('style') == 'dashed' else ''
        body.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="2.2"{dash}/>')
        if s_.get('dots'):
            body.extend(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.8" fill="{c}"/>' for a, b in pts)
        names.append((s_['name'], c, dash))
    for p in spec.get('points', []):
        body.append(f'<circle cx="{X(p["x"]):.1f}" cy="{Y(p["y"]):.1f}" r="4.5" fill="#fff" stroke="{INK}" stroke-width="1.6"/>'
                    + _t(X(p['x']) + p.get('dx', 8), Y(p['y']) + p.get('dy', -8), p['label'], 11.5, 'start' if p.get('dx', 8) >= 0 else 'end', weight=600))
    lx, ly = L, h - 14; rows = 1
    for n_, c, dash in names:
        wd = 44 + 6.2 * len(n_)
        if lx + wd > w - R and lx > L:
            lx, ly, rows = L, ly + 17, rows + 1
        body.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+22}" y2="{ly}" stroke="{c}" stroke-width="2.4"{dash}/>' + _t(lx + 28, ly + 4, n_, 11.5, 'start'))
        lx += wd
    h0 = h
    if rows > 1:
        h += 17 * (rows - 1)
    if spec.get('y_label'):
        body.append(f'<text x="14" y="{T + (h0-T-B)/2:.1f}" font-size="11.5" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 14 {T + (h0-T-B)/2:.1f})">{E(spec["y_label"])}</text>')
    if spec.get('x_label'):
        body.append(_t(w - R, h0 - B + 34, spec['x_label'], 11.5, 'end', fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Verlauf'))


def heat_matrix(spec):
    """Risk matrix: {'rows': [labels top->bottom], 'cols': [labels left->right], 'classes': [[class per cell]],
       'palette': {class: colour-index}, 'marks': [{'r','c','label'}], 'row_title', 'col_title'}"""
    R_, C_ = spec['rows'], spec['cols']; cw, ch = 96, 46; L, T = 128, 34
    w = L + cw * len(C_) + 16; h = T + ch * len(R_) + 64
    tone = {'Critical': '#8a3b2a', 'High': '#c46b3c', 'Moderate': '#d9b25a', 'Low': '#a9c2a0'}
    body = []
    for i, rl in enumerate(R_):
        body.append(_t(L - 10, T + i * ch + ch / 2 + 4, rl, 11.5, 'end'))
        for j, _ in enumerate(C_):
            cls = spec['classes'][i][j]
            body.append(f'<rect x="{L + j*cw + 1}" y="{T + i*ch + 1}" width="{cw-2}" height="{ch-2}" rx="3" fill="{tone.get(cls, LINE)}"/>'
                        + _t(L + j * cw + cw / 2, T + i * ch + ch / 2 + 4, cls, 11, fill='#fff' if cls in ('Critical', 'High') else INK, weight=600))
    for j, cl in enumerate(C_):
        body.append(_t(L + j * cw + cw / 2, T + ch * len(R_) + 18, cl, 11.5))
    for m in spec.get('marks', []):
        x, y = L + m['c'] * cw + cw - 14, T + m['r'] * ch + 13
        body.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#fff" stroke="{INK}" stroke-width="1.5"/>' + _t(x, y + 4, m['label'], 10.5, weight=700))
    body.append(_t(L + cw * len(C_) / 2, h - 12, spec.get('col_title', ''), 12, weight=600, fill=MUTED))
    body.append(_t(L - 10, 18, spec.get('row_title', ''), 12, 'end', weight=600, fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Matrix'))


def gantt(spec):
    """{'tasks': [{'id','name','start','dur','critical': bool}], 'deps': [[from, to]], 'unit': 'Wochen'}"""
    tasks = spec['tasks']; end = max(t['start'] + t['dur'] for t in tasks)
    L, T, rh = 180, 30, 30; w = 640; h = T + rh * len(tasks) + 40; cw = (w - L - 16) / end
    pos = {}
    body = [DEFS]
    for k in range(end + 1):
        x = L + k * cw
        body.append(f'<line x1="{x:.1f}" y1="{T-6}" x2="{x:.1f}" y2="{h-34}" stroke="{LINE}" stroke-width=".6"/>' + _t(x, T - 10, str(k), 10.5, fill=MUTED))
    for i, t in enumerate(tasks):
        y = T + i * rh; x = L + t['start'] * cw; bw = t['dur'] * cw
        crit = t.get('critical')
        body.append(_t(10, y + 19, t['name'], 12, 'start', weight=600 if crit else 400))
        body.append(f'<rect x="{x:.1f}" y="{y+6}" width="{bw:.1f}" height="18" rx="3" fill="{ACCENT[3] if crit else ACCENT[1]}"/>')
        if t.get('float'):
            body.append(f'<rect x="{x+bw:.1f}" y="{y+12}" width="{t["float"]*cw:.1f}" height="6" fill="none" stroke="{MUTED}" stroke-dasharray="3 2"/>')
        pos[t['id']] = (x, y + 15, x + bw)
    for a, b in spec.get('deps', []):
        _, ya, xe = pos[a]; xb, yb, _ = pos[b]
        body.append(f'<path d="M{xe:.1f},{ya:.1f} H{xe+6:.1f} V{yb:.1f} H{xb-1:.1f}" fill="none" stroke="{MUTED}" stroke-width="1.1" marker-end="url(#ah)"/>')
    body.append(f'<rect x="{L}" y="{h-22}" width="14" height="10" fill="{ACCENT[3]}"/>' + _t(L + 20, h - 13, 'kritischer Pfad', 11.5, 'start')
                + f'<rect x="{L+130}" y="{h-22}" width="14" height="10" fill="{ACCENT[1]}"/>' + _t(L + 150, h - 13, 'mit Puffer', 11.5, 'start')
                + f'<rect x="{L+240}" y="{h-19}" width="22" height="6" fill="none" stroke="{MUTED}" stroke-dasharray="3 2"/>' + _t(L + 268, h - 13, 'Gesamtpuffer', 11.5, 'start')
                + _t(w - 16, h - 13, spec.get('unit', ''), 11.5, 'end', fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Projektplan'))


def adoption_curve(spec):
    """Rogers' adopter categories as areas under a normal curve (cut at mean ± k·sd); optional chasm gap."""
    import math
    w, h, L, B = 640, 250, 20, 46
    pdf = lambda z: math.exp(-z * z / 2)
    X = lambda z: L + (z + 3) / 6 * (w - 2 * L); Y = lambda v: h - B - v * (h - B - 24)
    cuts = [-3, -2, -1, 0, 1, 3]; names = spec.get('names', ['Innovators', 'Early Adopters', 'Early Majority', 'Late Majority', 'Laggards'])
    shares = spec.get('shares', ['2,5 %', '13,5 %', '34 %', '34 %', '16 %'])
    body = []
    gap = spec.get('chasm_after')
    for k in range(5):
        a, b = cuts[k], cuts[k + 1]; zs = [a + (b - a) * i / 40 for i in range(41)]
        off = 7 if (gap is not None and k > gap) else 0
        d = f'M{X(a)+off:.1f},{Y(0):.1f} ' + ' '.join(f'L{X(z)+off:.1f},{Y(pdf(z)):.1f}' for z in zs) + f' L{X(b)+off:.1f},{Y(0):.1f} Z'
        body.append(f'<path d="{d}" fill="{ACCENT[k % len(ACCENT)]}" opacity=".85" stroke="#fff" stroke-width="1.2"/>')
        mid = (max(a, -2.6) + b) / 2
        body.append(_t(X(mid) + off, h - B + 16, names[k], 11, weight=600) + _t(X(mid) + off, h - B + 31, shares[k], 11, fill=MUTED))
    if gap is not None:
        xg = X(cuts[gap + 1]) + 3
        body.append(f'<line x1="{xg:.1f}" y1="30" x2="{xg:.1f}" y2="{Y(0):.1f}" stroke="{INK}" stroke-width="1.2" stroke-dasharray="4 3"/>'
                    + _t(xg + 6, 40, spec.get('gap_label', 'Chasm'), 12, 'start', weight=700))
    body.append(_t(w - L, 18, spec.get('x_note', 'Zeitpunkt der Übernahme →'), 11, 'end', fill=MUTED))
    return _svg(w, h, ''.join(body), spec.get('title', 'Adoptionskurve'))


RENDER.update({'line': line_chart, 'heat_matrix': heat_matrix, 'gantt': gantt, 'adoption_curve': adoption_curve})
from .figure_kit import register as _register_kit  # noqa: E402  (B32 teaching figures)
_register_kit(RENDER)


def render(spec):
    if spec.get('type') not in RENDER:
        raise ValueError(f"unknown figure type {spec.get('type')!r}")
    return RENDER[spec['type']](spec)
