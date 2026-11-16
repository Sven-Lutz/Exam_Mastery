"""Figure kit (B32): data-driven teaching illustrations for any subject. Every figure is drawn from a declared spec;
nothing is invented here. Kinds registered into figures_svg.RENDER:

  state_graph  states, decision points and probabilistic transitions (MDPs, Markov chains, automata, flows)
  backup_tree  one- or multi-level look-ahead tree with max/average operators and computed values
  grid_world   cell grid with values (diverging heat colours + printed numbers), walls, terminals, policy arrows,
               slip arrows for stochastic moves
  panels       several specs side by side or stacked, each with its own title (comparisons, before/after, sweeps)
  regime_line  parameter axis with regions, thresholds and labels (phase/regime diagrams)
  flow         vertical algorithm / decision flow with loop-back arrow
  loop         two-actor interaction loop (agent-environment, controller-plant, producer-consumer)
  stems        stem plot of one or more weight sequences (discount weights, probabilities, kernels)

Colour carries meaning only together with text: every value is printed, every arrow is labelled or listed in the
legend, and line styles differ between series.
"""
import math
import re
from html import escape as E

from .design_tokens import TOKENS as T, FONT_SANS, diverging

INK, MUTED, LINE = T['ink'], T['muted'], T['line']


def _svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" role="img" '
            f'aria-label="{E(title)}" style="font-family:{FONT_SANS};max-width:100%;height:auto">'
            f'<title>{E(title)}</title><defs>'
            + ''.join(f'<marker id="ah-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                      f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for k, c in
                      (('ink', INK), ('petrol', T['petrol']), ('coral', T['coral']), ('gold', T['gold']), ('blue', T['blue']), ('muted', MUTED)))
            + f'</defs>{body}</svg>')


_SCRIPT = re.compile(r'([_^])(\{[^{}]*\}|[A-Za-z0-9\u03b1-\u03c9*′]+)')


def rich(s):
    """Light math in figure labels: x_t, s_{t+1}, V^π, γ^k become real sub-/superscripts (tspan), never raw '_'/'^'."""
    out, pos = [], 0
    s = str(s)
    for m in _SCRIPT.finditer(s):
        if m.start() == 0 or not re.match(r'[\w\u0370-\u03ff)′]', s[m.start() - 1]):
            continue
        out.append(E(s[pos:m.start()]))
        inner = m[2][1:-1] if m[2].startswith('{') else m[2]
        shift = 'sub' if m[1] == '_' else 'super'
        out.append(f'<tspan baseline-shift="{shift}" font-size="72%">{E(inner)}</tspan>')
        pos = m.end()
    return ''.join(out) + E(s[pos:])


def _t(x, y, s, size=13, anchor='middle', weight=400, fill=INK, italic=False, cls=''):
    st = ' font-style="italic"' if italic else ''
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}"{st}>{rich(s)}</text>'


def _lines(x, y, lines, size=12, lh=None, **kw):
    lh = lh or size * 1.25
    return ''.join(_t(x, y + i * lh, ln, size, **kw) for i, ln in enumerate(lines))


def _wrap(text, chars):
    out, cur = [], ''
    for w in str(text).split():
        if len(cur) + len(w) + 1 > chars and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return out + ([cur] if cur else [])


COLORS = {'ink': INK, 'petrol': T['petrol'], 'coral': T['coral'], 'gold': T['gold'], 'blue': T['blue'], 'muted': MUTED,
          'green': T['green'], 'violet': T['violet'], 'navy': T['navy']}


# ------------------------------------------------------------------ state graph
def state_graph(spec):
    """{'nodes': [{'id','label','x','y','kind': state|action|terminal,'sub': str,'highlight': bool}],
        'edges': [{'from','to','label','kind': choice|transition,'bend': float,'loop': 'top'|'bottom','color','width'}],
        'w','h','title','legend': [[colour, text]]}"""
    W, H = spec.get('w', 640), spec.get('h', 300)
    nodes = {n['id']: n for n in spec['nodes']}
    r_of = lambda n: 30 if n.get('kind', 'state') in ('state', 'terminal') else 7
    body = []
    for e in spec['edges']:
        a, b = nodes[e['from']], nodes[e['to']]
        col = COLORS.get(e.get('color') or ('petrol' if e.get('kind') == 'transition' else 'navy'))
        mk = next(k for k, v in COLORS.items() if v == col and k in ('ink', 'petrol', 'coral', 'gold', 'blue', 'muted')) if col in (INK, T['petrol'], T['coral'], T['gold'], T['blue'], MUTED) else 'ink'
        dash = ' stroke-dasharray="5 4"' if e.get('kind') == 'transition' and e.get('dashed', True) else ''
        sw = e.get('width', 1.8)
        if e.get('loop') or e['from'] == e['to']:
            up = -1 if e.get('loop', 'top') == 'top' else 1
            r = r_of(a); x, y = a['x'], a['y'] + up * r
            d = f'M{x - 12:.1f},{y:.1f} C{x - 40:.1f},{y + up * 52:.1f} {x + 40:.1f},{y + up * 52:.1f} {x + 12:.1f},{y:.1f}'
            body.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}"{dash} marker-end="url(#ah-{mk})"/>')
            if e.get('label'):
                body.append(_lines(x, y + up * 50 + (-6 if up < 0 else 14), str(e['label']).split('\n'), 11.5, weight=600, fill=col))
            continue
        dx, dy = b['x'] - a['x'], b['y'] - a['y']; L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        x1, y1 = a['x'] + ux * r_of(a), a['y'] + uy * r_of(a)
        x2, y2 = b['x'] - ux * (r_of(b) + 2), b['y'] - uy * (r_of(b) + 2)
        bend = e.get('bend', 0)
        mx, my = (x1 + x2) / 2 - uy * bend, (y1 + y2) / 2 + ux * bend
        body.append(f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{col}" stroke-width="{sw}"{dash} marker-end="url(#ah-{mk})"/>')
        if e.get('label'):
            lx, ly = (x1 + 2 * mx + x2) / 4, (y1 + 2 * my + y2) / 4
            off = e.get('label_offset', 12)
            lx -= uy * off * (1 if bend >= 0 else -1); ly += ux * off * (1 if bend >= 0 else -1)
            lines = str(e['label']).split('\n')
            wd = max(len(s) for s in lines) * 6.4 + 8
            body.append(f'<rect x="{lx - wd / 2:.1f}" y="{ly - 12:.1f}" width="{wd:.1f}" height="{14 * len(lines) + 4:.1f}" rx="3" fill="#fff" opacity=".9"/>')
            body.append(_lines(lx, ly, lines, 11.5, 14, weight=600, fill=col))
    for n in spec['nodes']:
        k = n.get('kind', 'state')
        if k == 'action':
            body.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r="7" fill="{T["navy"]}"/>')
            if n.get('label'):
                body.append(_t(n['x'] + n.get('lx', 0), n['y'] + n.get('ly', -13), n['label'], 11.5, weight=700, fill=T['navy']))
            continue
        fill = T['petrol_l'] if k == 'state' else T['wash']
        stroke = T['coral'] if n.get('highlight') else (T['petrol'] if k == 'state' else MUTED)
        dash = ' stroke-dasharray="4 3"' if k == 'terminal' else ''
        body.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r="30" fill="{fill}" stroke="{stroke}" stroke-width="{3 if n.get("highlight") else 2}"{dash}/>')
        body.append(_t(n['x'], n['y'] + (0 if n.get('sub') else 5), n['label'], 14, weight=700, fill=T['navy']))
        if n.get('sub'):
            body.append(_t(n['x'], n['y'] + 15, n['sub'], 10.5, fill=MUTED))
    body.extend(_legend(spec.get('legend'), 14, H - 10, W))
    return _svg(W, H, ''.join(body), spec.get('title', 'Zustandsgraph'))


def _legend(items, x, y, W):
    out = []
    for col, text in items or []:
        c = COLORS.get(col, col)
        out.append(f'<rect x="{x}" y="{y - 9}" width="12" height="12" rx="2" fill="{c}"/>' + _t(x + 17, y + 1, text, 11, 'start', fill=MUTED))
        x += 30 + 5.6 * len(text)
    return out


# ------------------------------------------------------------------ backup tree
def backup_tree(spec):
    """{'root': node, 'title', 'w', 'op_label': {state: 'max'|'Σ π'}} with node = {'label','value','kind': state|action,
        'edge': 'p = 0.7, r = 2' (label of the edge from the parent), 'children': [...], 'best': bool}"""
    W = spec.get('w', 640)
    levels = []

    def depth(n, d=0):
        levels.append(d)
        for c in n.get('children', []):
            depth(c, d + 1)
    depth(spec['root']); D = max(levels) + 1
    H = spec.get('h', 70 + 92 * (D - 1) + 40)
    leaves = []

    def leafs(n):
        if not n.get('children'):
            leaves.append(n)
        for c in n.get('children', []):
            leafs(c)
    leafs(spec['root'])
    step = (W - 60) / max(1, len(leaves)); pos = {}
    k = [0]

    def place(n, d):
        if not n.get('children'):
            x = 30 + step * (k[0] + .5); k[0] += 1
        else:
            xs = [place(c, d + 1) for c in n['children']]; x = sum(xs) / len(xs)
        pos[id(n)] = (x, 40 + d * 92)
        return x
    place(spec['root'], 0)
    body = []

    def draw(n):
        x, y = pos[id(n)]
        for c in n.get('children', []):
            cx, cy = pos[id(c)]
            best = c.get('best')
            col = T['coral'] if best else (T['petrol'] if c.get('kind') == 'state' else T['navy'])
            body.append(f'<line x1="{x:.1f}" y1="{y + 16:.1f}" x2="{cx:.1f}" y2="{cy - 16:.1f}" stroke="{col}" stroke-width="{2.6 if best else 1.4}"/>')
            if c.get('edge'):
                body.append(_t((x + cx) / 2 + (8 if cx >= x else -8), (y + cy) / 2 + 2, c['edge'], 10.5, 'start' if cx >= x else 'end', fill=MUTED))
            draw(c)
        if n.get('kind', 'state') == 'state':
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="{T["petrol_l"]}" stroke="{T["petrol"]}" stroke-width="1.8"/>'
                        + _t(x, y + 4.5, n['label'], 12, weight=700, fill=T['navy']))
        else:
            body.append(f'<rect x="{x - 26:.1f}" y="{y - 12:.1f}" width="52" height="24" rx="12" fill="{T["navy"]}"/>'
                        + _t(x, y + 4.5, n['label'], 11, weight=700, fill='#fff'))
        if n.get('value') is not None:
            body.append(_t(x + (21 if n.get('kind', 'state') == 'state' else 30), y - 14, n['value'], 11.5, 'start', weight=700,
                           fill=T['coral'] if n.get('best') else T['blue']))
        if n.get('op'):
            body.append(_t(x - (22 if n.get('kind', 'state') == 'state' else 31), y - 14, n['op'], 11, 'end', weight=700, fill=T['gold']))
    draw(spec['root'])
    if spec.get('note'):
        body.append(_t(14, H - 10, spec['note'], 11, 'start', fill=MUTED))
    return _svg(W, H, ''.join(body), spec.get('title', 'Backup-Baum'))


# ------------------------------------------------------------------ grid world
ARROW = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}


def grid_world(spec):
    """{'cols','rows','cell': px,'values': {"c,r": v},'kinds': {"c,r": wall|terminal|start},'arrows': {"c,r": dir|[dirs]},
        'labels': {"c,r": text},'decimals','highlight': ["c,r"],'slip': {'cell','dir'},'title','caption_coords': bool}
        Coordinates (column,row) counted from the bottom left, row 1 at the bottom."""
    C, R, s = spec['cols'], spec['rows'], spec.get('cell', 84)
    pad, top = 34, 14
    W, H = pad + C * s + 14, top + R * s + 30
    vals = {k: v for k, v in (spec.get('values') or {}).items() if v is not None}
    lo, hi = min(list(vals.values()) + [0]), max(list(vals.values()) + [0])
    dec = spec.get('decimals', 2)
    body = []
    xy = lambda c, r: (pad + (c - 1) * s, top + (R - r) * s)
    for r in range(1, R + 1):
        body.append(_t(pad - 12, top + (R - r) * s + s / 2 + 4, r, 11, fill=MUTED))
        for c in range(1, C + 1):
            key = f'{c},{r}'; x, y = xy(c, r); k = (spec.get('kinds') or {}).get(key)
            if k == 'wall':
                body.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{T["navy"]}" opacity=".82"/>'
                            f'<path d="M{x},{y + s} L{x + s},{y}" stroke="#fff" stroke-width="1" opacity=".25"/>')
                continue
            fill = diverging(vals.get(key), lo, hi) if spec.get('heat', True) else '#fff'
            body.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{fill}" stroke="{LINE}" stroke-width="1"/>')
            if k == 'terminal':
                body.append(f'<rect x="{x + 4}" y="{y + 4}" width="{s - 8}" height="{s - 8}" fill="none" stroke="{T["navy"]}" stroke-width="2.2"/>')
            if key in (spec.get('highlight') or []):
                body.append(f'<rect x="{x + 1.5}" y="{y + 1.5}" width="{s - 3}" height="{s - 3}" fill="none" stroke="{T["coral"]}" stroke-width="3"/>')
            if key in vals:
                v = vals[key]
                body.append(_t(x + s / 2, y + s / 2 + (13 if (spec.get('arrows') or {}).get(key) else 5), f'{v:.{dec}f}'.replace('-', '−'),
                               13 if s >= 70 else 11, weight=700, fill=T['navy']))
            if (spec.get('labels') or {}).get(key):
                body.append(_t(x + 6, y + 13, spec['labels'][key], 10, 'start', weight=700, fill=MUTED))
            arr = (spec.get('arrows') or {}).get(key)
            for d_ in ([arr] if isinstance(arr, str) else arr or []):
                dx, dy = ARROW[d_]; cx, cy = x + s / 2, y + s / 2 - 9
                body.append(f'<line x1="{cx - dx * 11:.1f}" y1="{cy - dy * 11:.1f}" x2="{cx + dx * 13:.1f}" y2="{cy + dy * 13:.1f}" '
                            f'stroke="{T["navy"]}" stroke-width="2.4" marker-end="url(#ah-ink)"/>')
    for c in range(1, C + 1):
        body.append(_t(pad + (c - 1) * s + s / 2, top + R * s + 16, c, 11, fill=MUTED))
    if spec.get('slip'):
        c, r = map(int, spec['slip']['cell'].split(',')); x, y = xy(c, r); d_ = spec['slip']['dir']
        dx, dy = ARROW[d_]; cx, cy = x + s / 2, y + s / 2
        side = [k for k, v in ARROW.items() if v[0] == dy or v[1] == dx]
        side = [k for k, (ax, ay) in ARROW.items() if ax * dx + ay * dy == 0]
        body.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + dx * s * .85:.1f}" y2="{cy + dy * s * .85:.1f}" stroke="{T["coral"]}" stroke-width="3" marker-end="url(#ah-coral)"/>'
                    + _t(cx + dx * s * .55 + (8 if dx == 0 else 0), cy + dy * s * .55 - (8 if dy == 0 else 0), '0.8', 12, 'start', 800, T['coral']))
        for k in side:
            ax, ay = ARROW[k]
            body.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + ax * s * .6:.1f}" y2="{cy + ay * s * .6:.1f}" stroke="{T["coral"]}" stroke-width="1.8" '
                        f'stroke-dasharray="4 3" marker-end="url(#ah-coral)"/>' + _t(cx + ax * s * .3, cy + ay * s * .3 + 16, '0.1', 12, weight=800, fill=T['coral']))
    return _svg(W, H, ''.join(body), spec.get('title', 'Gitterwelt'))


# ------------------------------------------------------------------ panels
_VB = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def panels(spec):
    """{'panels': [spec], 'titles': [str], 'cols': n, 'gap': px, 'title'} — composes rendered sub-figures."""
    from .figures_svg import render
    subs = [render(p) for p in spec['panels']]
    sizes = [tuple(float(v) for v in _VB.search(s).groups()) for s in subs]
    cols = spec.get('cols', len(subs)); gap = spec.get('gap', 22); head = 26 if spec.get('titles') else 0
    rows = [sizes[i:i + cols] for i in range(0, len(sizes), cols)]
    scale = spec.get('scale', 1.0)
    W = max(sum(w for w, _ in r) * scale + gap * (len(r) - 1) for r in rows)
    body, y, i = [], 0, 0
    for r in rows:
        x = 0; rh = max(h for _, h in r) * scale
        for (w, h) in r:
            inner = re.sub(r'^<svg[^>]*>', '', subs[i]).rsplit('</svg>', 1)[0]
            if spec.get('titles'):
                body.append(_t(x + w * scale / 2, y + 17, spec['titles'][i], 13, weight=700, fill=T['navy']))
            body.append(f'<svg x="{x:.1f}" y="{y + head:.1f}" width="{w * scale:.1f}" height="{h * scale:.1f}" viewBox="0 0 {w:.0f} {h:.0f}">{inner}</svg>')
            x += w * scale + gap; i += 1
        y += rh + head + gap
    return _svg(W, y - gap, ''.join(body), spec.get('title', 'Vergleich'))


# ------------------------------------------------------------------ regime line
def regime_line(spec):
    """{'min','max','label','regions': [{'from','to','label','color'}],'marks': [{'x','label','sub'}],'ticks': [..],'title','w'}"""
    W, H = spec.get('w', 640), spec.get('h', 150)
    L, R0, y = 40, 30, 70
    X = lambda v: L + (v - spec['min']) / (spec['max'] - spec['min']) * (W - L - R0)
    body = []
    for rg in spec.get('regions', []):
        c = COLORS.get(rg.get('color', 'petrol')); cl = T.get(rg.get('color', 'petrol') + '_l', T['wash'])
        body.append(f'<rect x="{X(rg["from"]):.1f}" y="{y - 26}" width="{X(rg["to"]) - X(rg["from"]):.1f}" height="26" fill="{cl}" stroke="{c}" stroke-width="1"/>')
        body.append(_lines((X(rg['from']) + X(rg['to'])) / 2, y - 31 - 14 * (len(_wrap(rg['label'], 40)) - 1), _wrap(rg['label'], 40), 12, 14, weight=700, fill=c))
    body.append(f'<line x1="{L}" y1="{y}" x2="{W - R0}" y2="{y}" stroke="{T["navy"]}" stroke-width="2" marker-end="url(#ah-ink)"/>')
    for t in spec.get('ticks', []):
        body.append(f'<line x1="{X(t):.1f}" y1="{y}" x2="{X(t):.1f}" y2="{y + 6}" stroke="{T["navy"]}"/>' + _t(X(t), y + 20, t, 11, fill=MUTED))
    for m in spec.get('marks', []):
        body.append(f'<line x1="{X(m["x"]):.1f}" y1="{y - 34}" x2="{X(m["x"]):.1f}" y2="{y + 8}" stroke="{T["coral"]}" stroke-width="2.4"/>'
                    + _t(X(m['x']), y + 38, m['label'], 12.5, weight=800, fill=T['coral']) + (_t(X(m['x']), y + 53, m['sub'], 11, fill=MUTED) if m.get('sub') else ''))
    if spec.get('label'):
        body.append(_t(W - R0, y + 20, spec['label'], 12, 'end', weight=700, fill=T['navy']))
    return _svg(W, H, ''.join(body), spec.get('title', 'Parameterbereiche'))


# ------------------------------------------------------------------ flow
def flow(spec):
    """{'steps': [{'label','kind': start|op|decision|end,'note'}],'loop': {'from': i,'to': j,'label'},'title','w'}"""
    W = spec.get('w', 560); bw = spec.get('box_w', 330); x0 = (W - bw) / 2 - (60 if spec.get('loop') else 0)
    body, y, centers = [], 16, []
    for i, st in enumerate(spec['steps']):
        lines = _wrap(st['label'], int(bw / 7.1))
        h = 22 + 15 * len(lines)
        k = st.get('kind', 'op')
        cx = x0 + bw / 2
        if k == 'decision':
            body.append(f'<polygon points="{cx},{y} {x0 + bw},{y + h / 2 + 4} {cx},{y + h + 8} {x0},{y + h / 2 + 4}" fill="{T["gold_l"]}" stroke="{T["gold"]}" stroke-width="1.8"/>')
            body.append(_lines(cx, y + h / 2 + 8 - 7.5 * (len(lines) - 1), lines, 12, 15, weight=700, fill=T['navy'])); h += 8
        else:
            fill, stroke = {'start': (T['navy'], T['navy']), 'end': (T['green_l'], T['green'])}.get(k, (T['blue_l'], T['blue']))
            body.append(f'<rect x="{x0}" y="{y}" width="{bw}" height="{h}" rx="{h / 2 if k in ("start", "end") else 6}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
            body.append(_lines(cx, y + 19, lines, 12, 15, weight=700 if k != 'op' else 600, fill='#fff' if k == 'start' else T['navy']))
        if st.get('note'):
            body.append(_lines(x0 + bw + 12, y + 16, _wrap(st['note'], 24), 10.5, 13, anchor='start', fill=MUTED))
        centers.append((cx, y, y + h))
        y += h
        if i < len(spec['steps']) - 1:
            body.append(f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{y + 20}" stroke="{T["navy"]}" stroke-width="1.6" marker-end="url(#ah-ink)"/>')
            if st.get('kind') == 'decision' and st.get('yes'):
                body.append(_t(cx + 8, y + 14, st['yes'], 10.5, 'start', 700, T['green']))
            y += 22
    if spec.get('loop'):
        lp = spec['loop']; a, b = centers[lp['from']], centers[lp['to']]
        xr = x0 + bw + (196 if any(s_.get('note') for s_ in spec['steps']) else 40)
        ya, yb = (a[1] + a[2]) / 2, (b[1] + b[2]) / 2
        body.append(f'<path d="M{x0 + bw},{ya} H{xr} V{yb} H{x0 + bw + 4}" fill="none" stroke="{T["coral"]}" stroke-width="1.8" marker-end="url(#ah-coral)"/>')
        body.append(_lines(xr + 6, (ya + yb) / 2, _wrap(lp.get('label', ''), 14), 11, 13, anchor='start', weight=700, fill=T['coral']))
    extra = (60 + (130 if any(s_.get('note') for s_ in spec['steps']) else 0)) if spec.get('loop') else (110 if any(s_.get('note') for s_ in spec['steps']) else 0)
    return _svg(W + extra, y + 14, ''.join(body), spec.get('title', 'Ablauf'))


# ------------------------------------------------------------------ interaction loop
def loop(spec):
    """{'left': {'title','lines'},'right': {'title','lines'},'top': label (left->right),'bottom': [labels] (right->left),'title'}"""
    W, H = spec.get('w', 620), spec.get('h', 230)
    bw, bh = 170, 96; lx, rx, y = 30, W - 30 - 170, (H - bh) / 2
    body = []
    for x, box, fill, stroke in ((lx, spec['left'], T['petrol_l'], T['petrol']), (rx, spec['right'], T['gold_l'], T['gold'])):
        body.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
                    + _t(x + bw / 2, y + 28, box['title'], 15, weight=800, fill=T['navy'])
                    + _lines(x + bw / 2, y + 50, box.get('lines', []), 11.5, 15, fill=MUTED))
    body.append(f'<path d="M{lx + bw / 2},{y} C{lx + bw / 2},{y - 50} {rx + bw / 2},{y - 50} {rx + bw / 2},{y - 2}" fill="none" stroke="{T["navy"]}" stroke-width="2.2" marker-end="url(#ah-ink)"/>'
                + _t(W / 2, y - 40, spec['top'], 13, weight=700, fill=T['navy']))
    n = len(spec['bottom'])
    for i, lab in enumerate(spec['bottom']):
        dy = 46 + 44 * i
        c = [T['petrol'], T['coral']][i % 2]; mk = ['petrol', 'coral'][i % 2]
        body.append(f'<path d="M{rx + bw / 2 + (i * 20 - 10)},{y + bh} C{rx + bw / 2},{y + bh + dy} {lx + bw / 2},{y + bh + dy} {lx + bw / 2 + (i * 20 - 10)},{y + bh + 2}" '
                    f'fill="none" stroke="{c}" stroke-width="2.2" marker-end="url(#ah-{mk})"/>'
                    + f'<rect x="{W / 2 - 6.2 * len(lab) / 1.6 - 8:.1f}" y="{y + bh + .75 * dy - 13:.1f}" width="{12.4 * len(lab) / 1.6 + 16:.1f}" height="19" rx="3" fill="#fff"/>'
                    + _t(W / 2, y + bh + .75 * dy + 1, lab, 13, weight=700, fill=c))
    return _svg(W, H + 10 + 44 * max(0, n - 1), ''.join(body), spec.get('title', 'Interaktion'))


# ------------------------------------------------------------------ stems
def stems(spec):
    """{'k': [0..n],'series': [{'name','values','color'}],'marks': [{'x','label'}],'y_label','x_label','title','w'}"""
    W, H = spec.get('w', 640), spec.get('h', 260); L, R0, Tp, B = 54, 18, 22, 50
    ks = spec['k']; ymax = max(max(s['values']) for s in spec['series']) or 1
    X = lambda k: L + (k - ks[0]) / ((ks[-1] - ks[0]) or 1) * (W - L - R0)
    Y = lambda v: Tp + (1 - v / ymax) * (H - Tp - B)
    body = [f'<line x1="{L}" y1="{Y(0):.1f}" x2="{W - R0}" y2="{Y(0):.1f}" stroke="{T["navy"]}" stroke-width="1.4"/>']
    for t in (0, .25, .5, .75, 1.0):
        v = t * ymax
        body.append(f'<line x1="{L}" y1="{Y(v):.1f}" x2="{W - R0}" y2="{Y(v):.1f}" stroke="{LINE}" stroke-width=".6"/>' + _t(L - 6, Y(v) + 4, f'{v:.2f}', 10.5, 'end', fill=MUTED))
    n = len(spec['series']); names = []
    for j, s_ in enumerate(spec['series']):
        c = COLORS.get(s_.get('color', ['petrol', 'gold', 'coral'][j % 3])); off = (j - (n - 1) / 2) * 3.2
        for k, v in zip(ks, s_['values']):
            body.append(f'<line x1="{X(k) + off:.1f}" y1="{Y(0):.1f}" x2="{X(k) + off:.1f}" y2="{Y(v):.1f}" stroke="{c}" stroke-width="1.4"/>'
                        f'<circle cx="{X(k) + off:.1f}" cy="{Y(v):.1f}" r="{2.8 if j == 0 else 2.4}" fill="{c if j != 1 else "#fff"}" stroke="{c}" stroke-width="1.2"/>')
        names.append((s_['name'], c))
    for m in spec.get('marks', []):
        body.append(f'<line x1="{X(m["x"]):.1f}" y1="{Tp}" x2="{X(m["x"]):.1f}" y2="{Y(0):.1f}" stroke="{T["navy"]}" stroke-dasharray="3 3"/>'
                    + _t(X(m['x']) + 4, Tp + 10 + 13 * m.get('row', 0), m['label'], 11, 'start', 700, T['navy']))
    for i, k in enumerate(ks):
        if i % max(1, len(ks) // 10) == 0:
            body.append(_t(X(k), Y(0) + 16, k, 10.5, fill=MUTED))
    x = L
    for nm, c in names:
        body.append(f'<circle cx="{x + 5}" cy="{H - 12}" r="4" fill="{c}"/>' + _t(x + 14, H - 8, nm, 11.5, 'start'))
        x += 40 + 6.4 * len(nm)
    if spec.get('x_label'):
        body.append(_t(W - R0, Y(0) + 32, spec['x_label'], 11.5, 'end', fill=MUTED))
    if spec.get('y_label'):
        body.append(f'<text x="14" y="{(Tp + H - B) / 2:.1f}" font-size="11.5" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 14 {(Tp + H - B) / 2:.1f})">{E(spec["y_label"])}</text>')
    return _svg(W, H, ''.join(body), spec.get('title', 'Gewichte'))


def convergence(spec):
    """Log-scale error/residual plot: {'x': [k],'series': [{'name','values','color','style': solid|dashed}],'y_label','x_label',
        'marks': [{'x','label'}],'hline': {'y','label'},'title','w'}; values must be > 0."""
    W, H = spec.get('w', 640), spec.get('h', 300); L, R0, Tp, B = 62, 20, 22, 52
    xs = spec['x']; allv = [v for s_ in spec['series'] for v in s_['values'] if v and v > 0]
    lo, hi = math.floor(math.log10(min(allv))), math.ceil(math.log10(max(allv)))
    X = lambda v: L + (v - xs[0]) / ((xs[-1] - xs[0]) or 1) * (W - L - R0)
    Y = lambda v: Tp + (hi - math.log10(v)) / ((hi - lo) or 1) * (H - Tp - B)
    body = []
    for e in range(lo, hi + 1):
        body.append(f'<line x1="{L}" y1="{Y(10 ** e):.1f}" x2="{W - R0}" y2="{Y(10 ** e):.1f}" stroke="{LINE}" stroke-width=".7"/>'
                    + _t(L - 6, Y(10 ** e) + 4, f'1e{e}' if abs(e) > 2 else f'{10 ** e:g}', 10.5, 'end', fill=MUTED))
    for i, k in enumerate(xs):
        if i % max(1, len(xs) // 10) == 0 or i == len(xs) - 1:
            body.append(_t(X(k), H - B + 16, k, 10.5, fill=MUTED))
    if spec.get('hline'):
        hl = spec['hline']
        body.append(f'<line x1="{L}" y1="{Y(hl["y"]):.1f}" x2="{W - R0}" y2="{Y(hl["y"]):.1f}" stroke="{T["coral"]}" stroke-dasharray="6 4" stroke-width="1.4"/>'
                    + _t(W - R0, Y(hl['y']) - 6, hl['label'], 11, 'end', 700, T['coral']))
    for m in spec.get('marks', []):
        body.append(f'<line x1="{X(m["x"]):.1f}" y1="{Tp}" x2="{X(m["x"]):.1f}" y2="{H - B}" stroke="{T["navy"]}" stroke-dasharray="3 3"/>'
                    + _t(X(m['x']) + 4, Tp + 11 + 13 * m.get('row', 0), m['label'], 11, 'start', 700, T['navy']))
    lx = L
    for j, s_ in enumerate(spec['series']):
        c = COLORS.get(s_.get('color', ['petrol', 'gold', 'coral', 'blue'][j % 4]))
        pts = [(X(x), Y(v)) for x, v in zip(xs, s_['values']) if v and v > 0]
        dash = ' stroke-dasharray="7 4"' if s_.get('style') == 'dashed' else ''
        body.append(f'<path d="M{" L".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{c}" stroke-width="2.3"{dash}/>')
        if s_.get('dots'):
            body.extend(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="2.6" fill="{c}"/>' for a, b in pts)
        body.append(f'<line x1="{lx}" y1="{H - 12}" x2="{lx + 22}" y2="{H - 12}" stroke="{c}" stroke-width="2.4"{dash}/>' + _t(lx + 28, H - 8, s_['name'], 11.5, 'start'))
        lx += 46 + 6.3 * len(s_['name'])
    if spec.get('y_label'):
        body.append(f'<text x="14" y="{(Tp + H - B) / 2:.1f}" font-size="11.5" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 14 {(Tp + H - B) / 2:.1f})">{E(spec["y_label"])}</text>')
    if spec.get('x_label'):
        body.append(_t(W - R0, H - B + 32, spec['x_label'], 11.5, 'end', fill=MUTED))
    return _svg(W, H, ''.join(body), spec.get('title', 'Konvergenz'))


KINDS = {'convergence': convergence, 'state_graph': state_graph, 'backup_tree': backup_tree, 'grid_world': grid_world, 'panels': panels,
         'regime_line': regime_line, 'flow': flow, 'loop': loop, 'stems': stems}


def register(render_table):
    render_table.update(KINDS)
