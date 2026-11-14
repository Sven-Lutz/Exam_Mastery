"""B16: mathematical scenes (schema em-scene-v1). Deterministic: no model call, no hand-typed numbers.

A scene explains how a result arises. It is a declarative, optional part of a lab spec (spec['scene']):
  type          generic renderer in templates/em_scene.js (network | chord | cashflow); reusable across courses
  didactics     concept made visible, linked representations, misconception, what to manipulate, predict, conclude
  objects       graphic objects (id, colour role, label); the renderer marks them with data-ref
  params        lab parameters the scene depends on; dependencies: which object/value depends on which parameter
  vars          learner selections, substituted into ids and paths as {j} and {J} (= j + 1)
  steps         title, text, formula tokens, targets, reveal, zoom, anim, camera; 'repeat' expands a step per row
  expect        every value token of the default state, recomputed here with labs/models.py (browser tests compare)
  assumptions, sources, status ('exploration' where a numerical search is shown, never a proof)

Formula tokens: {'t': text} | {'o': operator} | {'s': symbol, 'sub', 'sup', 'ref', 'role'} | {'v': path, 'd': digits,
'ref', 'role', 'e': exponent notation}. A value token never carries a number, only a path into the model's trace.
"""
import itertools
import math

from . import models as M

SCHEMA = 'em-scene-v1'
ROLES = {'input', 'weight', 'bias', 'sum', 'activation', 'output', 'target', 'loss', 'gradient', 'update',
         'point_p', 'point_q', 'point_u', 'midpoint', 'distance', 'lift', 'curve',
         'sale', 'term', 'inflow', 'outflow', 'invest', 'balance', 'need'}
TYPES = {'network': {'flow', 'back', 'act', 'update'}, 'chord': {'camera', 'lift', 'seek'}, 'cashflow': {'arcs', 'period'}}
DIDACTICS = ('concept', 'representations', 'misconception', 'manipulate', 'predict', 'conclusion')


class SceneError(ValueError):
    pass


# ------------------------------------------------------------------ token helpers

def T(x):
    return {'t': x}


def O(x):
    return {'o': x}


def Sy(s, sub=None, ref=None, role=None, sup=None):
    d = {'s': s}
    if sub is not None:
        d['sub'] = sub
    if sup is not None:
        d['sup'] = sup
    if ref:
        d['ref'] = ref
    if role:
        d['role'] = role
    return d


def V(path, d=3, ref=None, role=None, unit=None, e=False):
    x = {'v': path, 'd': d}
    if ref:
        x['ref'] = ref
    if role:
        x['role'] = role
    if unit:
        x['unit'] = unit
    if e:
        x['e'] = True
    return x


def sub(s, vars_):
    out = str(s)
    for k, v in vars_.items():
        out = out.replace('{' + k + '}', str(v)).replace('{' + k.upper() + '}', str(v + 1))
    return out


def get(obj, path):
    for k in str(path).split('.'):
        if obj is None:
            return None
        if isinstance(obj, (list, tuple)):
            if not k.isdigit() or int(k) >= len(obj):
                return None
            obj = obj[int(k)]
        elif isinstance(obj, dict):
            obj = obj.get(k)
        else:
            return None
    return obj


# ------------------------------------------------------------------ traces (the only source of scene numbers)

def trace(spec, params=None):
    m, k = spec['model'], spec['model']['kind']
    d = {p['id']: p['default'] for p in spec['params']}
    d.update(params or {})
    if k == 'mlp':
        p = {'W1': [[d['w11'], d['w12']], [d['w21'], d['w22']]], 'b1': [d['b1'], d['b2']], 'W2': [d['v1'], d['v2']], 'b2': d['c']}
        return M.mlp_trace(p, [d['x1'], d['x2']], d['t'], d['lr'], d['ha'], d['oa'])
    if k == 'chord':
        return M.chord_trace(d['s'], d['t'])
    if k == 'cashflow':
        T_ = int(d.get('horizon', len(m['orders'])))
        ext = lambda xs, fill_last: [xs[i] if i < len(xs) else (xs[-1] if (fill_last and xs) else 0) for i in range(T_)]
        return M.cash_trace(ext(m['orders'], True), int(d['delay']), ext(m['cost'], True), ext(m['invest'], False),
                            float(d.get('start_cash', 0)), T_, int(d['delayB']))
    raise SceneError(f'no scene trace for {k}')


def expand(scene, tr):
    out = []
    for st in scene['steps']:
        if not st.get('repeat'):
            out.append((st, {}))
            continue
        for n in range(len(get(tr, st['repeat']) or [])):
            out.append((st, {st.get('var', 'k'): n}))
    return out


def _objects(scene, tr):
    ids = set()
    for o in scene['objects']:
        if o.get('repeat'):
            for n in range(len(get(tr, o['repeat']) or [])):
                ids.add(sub(o['id'], {o.get('var', 'k'): n}))
        else:
            ids.add(o['id'])
    return ids


def _var_space(scene):
    keys = sorted(scene.get('vars') or {})
    for combo in itertools.product(*[[o['value'] for o in scene['vars'][k]['options']] for k in keys]):
        yield dict(zip(keys, combo))


def values(scene, tr, vars_):
    """Every value token of every step for one selection: {path: value}."""
    out = {}
    for st, sv in expand(scene, tr):
        v = {**vars_, **sv}
        for f in ('formula', 'formula2'):
            for tk in st.get(f) or []:
                if 'v' in tk:
                    pth = sub(tk['v'], v)
                    out[pth] = get(tr, pth)
    return out


def validate(spec):
    """Structure, roles, renderer animations, object references, didactic card and every value against the trace."""
    sc = spec.get('scene')
    if sc is None:
        return True
    if sc.get('schema') != SCHEMA or sc.get('type') not in TYPES:
        raise SceneError('unknown scene schema or type')
    if any(not sc.get('didactics', {}).get(k) for k in DIDACTICS):
        raise SceneError('scene needs its didactic function (concept, representations, misconception, manipulate, predict, conclusion)')
    if not sc.get('steps') or not sc.get('sources') or not sc.get('assumptions'):
        raise SceneError('scene needs steps, sources and assumptions')
    pids = {p['id'] for p in spec['params']}
    if not set(sc.get('params') or []) <= pids:
        raise SceneError('scene names unknown parameters')
    for a, b in sc.get('dependencies') or []:
        if a not in pids:
            raise SceneError(f'dependency from unknown parameter {a}')
    for o in sc['objects']:
        if o.get('role') not in ROLES:
            raise SceneError(f'object {o["id"]}: unknown colour role {o.get("role")}')
    tr = trace(spec)
    known = _objects(sc, tr)
    for vars_ in _var_space(sc):
        for st, sv in expand(sc, tr):
            v = {**vars_, **sv}
            if st.get('anim') and st['anim'].get('kind') not in TYPES[sc['type']]:
                raise SceneError(f'step {st["id"]}: renderer {sc["type"]} has no animation {st["anim"].get("kind")}')
            refs = [*(st.get('targets') or []), *(st.get('zoom') or []), *((st.get('anim') or {}).get('edges') or [])]
            for f in ('formula', 'formula2'):
                for tk in st.get(f) or []:
                    if tk.get('role') and tk['role'] not in ROLES:
                        raise SceneError(f'step {st["id"]}: unknown role {tk["role"]}')
                    if tk.get('ref'):
                        refs.append(tk['ref'])
                    if 'v' in tk:
                        x = get(tr, sub(tk['v'], v))
                        if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
                            if x is None and tk.get('optional'):
                                continue
                            raise SceneError(f'step {st["id"]}: path {sub(tk["v"], v)} is not a finite number of the trace')
            for r in refs:
                if sub(r, v) not in known:
                    raise SceneError(f'step {st["id"]}: reference {sub(r, v)} is not an object of the scene')
    exp = sc.get('expect') or {}
    want = values(sc, tr, exp.get('vars') or {})
    if exp.get('values') != want:
        raise SceneError('expected values of the default state disagree with the reference model')
    return True


def _finish(spec, sc):
    tr = trace({**spec, 'scene': sc})
    defaults = {k: v['default'] for k, v in (sc.get('vars') or {}).items()}
    sc['expect'] = {'vars': defaults, 'values': values(sc, tr, defaults)}
    spec['scene'] = sc
    validate(spec)
    return spec


# ------------------------------------------------------------------ reference scene A: one neuron, step by step

def network_scene(spec):
    w, x_ = (lambda j, i: Sy('w', j + i, 'w' + j + i, 'weight')), (lambda i: Sy('x', i, 'x' + i, 'input'))
    sc = {
        'schema': SCHEMA, 'type': 'network', 'title': 'Ein Neuron rechnet – Schritt für Schritt',
        'lead': 'Formel und Netz sind gekoppelt: Ein Klick auf einen farbigen Term hebt das zugehörige Objekt hervor. Gewichte lassen sich im Bild ziehen.',
        'didactics': {
            'concept': 'Wie aus Eingaben, Gewichten und Bias über die Aktivierung eine Vorhersage wird, und wie die Kettenregel ein einzelnes Gewicht für den Fehler verantwortlich macht.',
            'representations': ['Netzdiagramm', 'Formel mit eingesetzten Zahlen', 'Aktivierungskurve', 'Verlustwert vorher/nachher'],
            'misconception': 'Backpropagation sei ein eigener Lernalgorithmus mit Sonderregeln; tatsächlich ist jeder Gradient ein Produkt lokaler Ableitungen entlang des Pfades.',
            'manipulate': 'Neuron (h₁/h₂) wählen, Gewichte ziehen oder per Pfeiltaste ändern, Eingaben, Zielwert, Lernrate und Aktivierung im Regler-Bereich.',
            'predict': 'Ob ein Gewichtsschritt den Verlust senkt, folgt aus dem Vorzeichen von ∂L/∂w, bevor das Update ausgeführt wird.',
            'conclusion': 'Der Gradient eines Gewichts ist (Fehlersignal am Ausgang) × (Gewicht zum Ausgang) × (Steigung der Aktivierung) × (Eingabe); ist ein Faktor 0, lernt das Gewicht nicht.'},
        'objects': [{'id': 'x1', 'role': 'input'}, {'id': 'x2', 'role': 'input'}, {'id': 'h1', 'role': 'activation'}, {'id': 'h2', 'role': 'activation'},
                    {'id': 'o', 'role': 'output'}, {'id': 'L', 'role': 'loss'}, {'id': 't', 'role': 'target'}, {'id': 'act', 'role': 'activation'},
                    {'id': 'a', 'role': 'activation'}, {'id': 'z', 'role': 'sum'}, {'id': 'b1', 'role': 'bias'}, {'id': 'b2', 'role': 'bias'}, {'id': 'c', 'role': 'bias'},
                    *[{'id': f'w{j}{i}', 'role': 'weight'} for j in (1, 2) for i in (1, 2)], {'id': 'v1', 'role': 'weight'}, {'id': 'v2', 'role': 'weight'}],
        'params': ['x1', 'x2', 't', 'lr', 'ha', 'oa', 'w11', 'w12', 'w21', 'w22', 'b1', 'b2', 'v1', 'v2', 'c'],
        'dependencies': [['w11', 'z1'], ['w12', 'z1'], ['w21', 'z2'], ['w22', 'z2'], ['b1', 'z1'], ['b2', 'z2'], ['x1', 'z1'], ['x2', 'z2'],
                         ['ha', 'a1'], ['v1', 'y'], ['v2', 'y'], ['c', 'y'], ['oa', 'y'], ['t', 'L'], ['lr', 'new']],
        'vars': {'j': {'label': 'Neuron', 'default': 0, 'options': [{'value': 0, 'label': 'h₁'}, {'value': 1, 'label': 'h₂'}]},
                 'i': {'label': 'Eingang des betrachteten Gewichts', 'default': 0, 'options': [{'value': 0, 'label': 'x₁'}, {'value': 1, 'label': 'x₂'}]}},
        'steps': [
            {'id': 'arch', 'title': 'Eingaben und Architektur', 'targets': ['x1', 'x2'],
             'formula': [Sy('x', ref='x1', role='input'), O(' = ('), V('x.0', 2, 'x1', 'input'), O('; '), V('x.1', 2, 'x2', 'input'), O(')   '), Sy('t', ref='t', role='target'), O(' = '), V('t', 2, 't', 'target')],
             'text': 'Zwei Eingaben, zwei verdeckte Neuronen, eine Ausgabe. Jede Linie ist ein Gewicht; ihre Dicke zeigt den Betrag, die Farbe das Vorzeichen.'},
            {'id': 'select', 'title': 'Neuron h{J} auswählen', 'targets': ['h{J}', 'w{J}1', 'w{J}2', 'b{J}'], 'zoom': ['x1', 'x2', 'h{J}'],
             'formula': [Sy('z', '{J}', 'z', 'sum'), O(' = '), w('{J}', '1'), O(' · '), x_('1'), O(' + '), w('{J}', '2'), O(' · '), x_('2'), O(' + '), Sy('b', '{J}', 'b{J}', 'bias')],
             'text': 'Ein Neuron sieht nur seine eingehenden Gewichte und seinen Bias. Klicken Sie im Bild auf h₁ oder h₂, um das andere Neuron zu verfolgen.'},
            {'id': 'term1', 'title': 'Erster Beitrag: Gewicht mal Eingabe', 'targets': ['w{J}1', 'x1'], 'zoom': ['x1', 'h{J}'], 'anim': {'kind': 'flow', 'edges': ['w{J}1']},
             'formula': [w('{J}', '1'), O(' · '), x_('1'), O(' = '), V('W1.{j}.0', 3, 'w{J}1', 'weight'), O(' · '), V('x.0', 2, 'x1', 'input'), O(' = '), V('prod.{j}.0', 4, 'z', 'sum')],
             'text': 'Das Signal läuft entlang der Verbindung und wird mit dem Gewicht skaliert. Ein negatives Gewicht kehrt das Vorzeichen um.'},
            {'id': 'term2', 'title': 'Zweiter Beitrag und Zwischensumme', 'targets': ['w{J}2', 'x2'], 'zoom': ['x2', 'h{J}'], 'anim': {'kind': 'flow', 'edges': ['w{J}2']},
             'formula': [V('prod.{j}.0', 4, 'z', 'sum'), O(' + '), V('W1.{j}.1', 3, 'w{J}2', 'weight'), O(' · '), V('x.1', 2, 'x2', 'input'), O(' = '), V('part.{j}.1', 4, 'z', 'sum')],
             'text': 'Die Beiträge aller Eingaben werden addiert – die gewichtete Summe.'},
            {'id': 'bias', 'title': 'Bias addieren', 'targets': ['b{J}', 'h{J}'], 'reveal': ['z{J}'], 'zoom': ['h{J}', 'b{J}'],
             'formula': [Sy('z', '{J}', 'z', 'sum'), O(' = '), V('part.{j}.1', 4, 'z', 'sum'), O(' + '), V('b1.{j}', 3, 'b{J}', 'bias'), O(' = '), V('z1.{j}', 4, 'z', 'sum')],
             'text': 'Der Bias verschiebt die Summe unabhängig von den Eingaben – er legt fest, ab wann das Neuron „anspringt“.'},
            {'id': 'act', 'title': 'Aktivierungsfunktion', 'targets': ['act', 'h{J}'], 'reveal': ['a{J}'], 'zoom': ['act', 'h{J}'], 'anim': {'kind': 'act'},
             'formula': [Sy('a', '{J}', 'a', 'activation'), O(' = f('), V('z1.{j}', 4, 'z', 'sum'), O(') = '), V('a1.{j}', 4, 'a', 'activation'), O('    f′('), Sy('z', '{J}'), O(') = '), V('fprime.{j}', 4, 'act', 'activation')],
             'text': 'Der Punkt läuft auf der z-Achse zur Summe und steigt zur Kurve: Das ist die Ausgabe des Neurons. Die Steigung f′ dort wird beim Lernen wichtig.'},
            {'id': 'output', 'title': 'Weiter zur Ausgabe', 'targets': ['v1', 'v2', 'o', 'c'], 'reveal': ['a1', 'a2', 'y'], 'anim': {'kind': 'flow', 'edges': ['v1', 'v2']},
             'formula': [Sy('ŷ', ref='o', role='output'), O(' = g('), V('vprod.0', 4, 'v1', 'weight'), O(' + '), V('vprod.1', 4, 'v2', 'weight'), O(' + '), V('b2', 3, 'c', 'bias'), O(') = g('), V('zo', 4, 'o', 'sum'), O(') = '), V('y', 4, 'o', 'output')],
             'text': 'Beide verdeckten Neuronen rechnen gleichzeitig; ihre Aktivierungen werden mit v₁, v₂ gewichtet, summiert und durch g geschickt.'},
            {'id': 'loss', 'title': 'Verlust berechnen', 'targets': ['L', 'o', 't'], 'reveal': ['L'], 'zoom': ['o', 'L'],
             'formula': [Sy('L', ref='L', role='loss'), O(' = ½ ('), V('y', 4, 'o', 'output'), O(' − '), V('t', 2, 't', 'target'), O(')² = '), V('loss', 6, 'L', 'loss')],
             'text': 'Der Verlust misst den Abstand zwischen Vorhersage und Zielwert. Das ½ sorgt dafür, dass die Ableitung einfach ŷ − t ist.'},
            {'id': 'delta', 'title': 'Fehlersignal am Ausgang', 'targets': ['o', 'L'], 'zoom': ['o', 'L'], 'anim': {'kind': 'back', 'edges': []},
             'formula': [Sy('δ', 'o', 'o', 'gradient'), O(' = (ŷ − t) · g′(zₒ) = '), V('err', 5, 'L', 'loss'), O(' · '), V('gprime', 5, 'o', 'output'), O(' = '), V('delta_o', 6, 'o', 'gradient')],
             'text': 'Kettenregel, erstes Glied: Wie stark ändert sich L, wenn sich die Summe am Ausgang ändert?'},
            {'id': 'grad', 'title': 'Gradient von w{J}{I}: die Kette zurück', 'targets': ['w{J}{I}', 'v{J}', 'h{J}', 'o', 'L'], 'anim': {'kind': 'back', 'edges': ['v{J}', 'w{J}{I}']},
             'formula': [Sy('∂L/∂w', '{J}{I}', 'w{J}{I}', 'gradient'), O(' = '), Sy('δ', 'o', 'o', 'gradient'), O(' · '), Sy('v', '{J}', 'v{J}', 'weight'), O(' · '), Sy('f′(z', '{J}', 'act', 'activation'), O(') · '), Sy('x', '{I}', 'x{I}', 'input')],
             'formula2': [O('= '), V('delta_o', 5, 'o', 'gradient'), O(' · '), V('W2.{j}', 3, 'v{J}', 'weight'), O(' · '), V('fprime.{j}', 4, 'act', 'activation'), O(' · '), V('x.{i}', 2, 'x{I}', 'input'), O(' = '), V('grad.W1.{j}.{i}', 6, 'w{J}{I}', 'gradient')],
             'text': 'Das Fehlersignal wandert rückwärts: über v{J} zum Neuron, durch die Steigung der Aktivierung, bis zur Eingabe. Jeder Faktor ist eine lokale Ableitung.'},
            {'id': 'update', 'title': 'Parameterupdate', 'targets': ['w{J}{I}'], 'anim': {'kind': 'update'},
             'formula': [Sy('w', '{J}{I}', 'w{J}{I}', 'weight'), O(' ← '), V('W1.{j}.{i}', 4, 'w{J}{I}', 'weight'), O(' − '), V('lr', 3, None, 'update'), O(' · '), V('grad.W1.{j}.{i}', 6, 'w{J}{I}', 'gradient'), O(' = '), V('new.W1.{j}.{i}', 4, 'w{J}{I}', 'update')],
             'text': 'Gradientenabstieg geht gegen den Gradienten. Alle neun Parameter werden im selben Schritt mit ihrem eigenen Gradienten verändert – die Linien zeigen es.'},
            {'id': 'after', 'title': 'Wirkung: vorher und nachher', 'targets': ['o', 'L'], 'reveal': ['after'],
             'formula': [Sy('ŷ', ref='o', role='output'), O(': '), V('y', 5, 'o', 'output'), O(' → '), V('after.y', 5, 'o', 'output'), O('   (t = '), V('t', 2, 't', 'target'), O(')')],
             'formula2': [Sy('L', ref='L', role='loss'), O(': '), V('loss', 6, 'L', 'loss'), O(' → '), V('after.loss', 6, 'L', 'loss'), O('   Δ = '), V('dloss', 6, 'L', 'loss')],
             'text': 'Nach einem Schritt wird erneut vorwärts gerechnet. Die blassen Linien zeigen die alten Gewichte. Mit „Einen Lernschritt ausführen“ übernehmen Sie das Update und können den nächsten Schritt verfolgen.'}],
        'assumptions': ['Netz 2-2-1 mit genau einem Trainingsbeispiel; quadratischer Verlust L = ½(ŷ − t)².',
                        'Alle Parameter werden gleichzeitig mit dem Gradienten des aktuellen Zustands aktualisiert (ein Schritt Gradientenabstieg).',
                        'Die angezeigten Zahlen sind gerundet; gerechnet wird mit voller Genauigkeit (Gleitkomma).'],
        'sources': ['Eigenes Referenzmodell (exam_mastery/labs/models.py), Gradienten gegen finite Differenzen geprüft',
                    'Gestalterische Anregung: 3Blue1Brown, Lektionen „Neural networks“ (3blue1brown.com, Lektion neural-networks); kein Code und keine Szenen übernommen'],
        'status': 'computation'}
    return _finish(spec, sc)


# ------------------------------------------------------------------ reference scene B: chord lift (inscribed rectangle)

def chord_scene(spec):
    P, Q = (lambda: Sy('P', ref='P', role='point_p')), (lambda: Sy('Q', ref='Q', role='point_q'))
    pt = lambda base, ref, role, d=3: [O('('), V(base + '.0', d, ref, role), O('; '), V(base + '.1', d, ref, role), O(')')]
    sc = {
        'schema': SCHEMA, 'type': 'chord', 'title': 'Vom Punktpaar zum Punkt im Raum',
        'lead': 'Ziehen Sie P und Q auf der Kurve. In der 3D-Ansicht dreht Ziehen auf freier Fläche (oder Pfeiltasten auf der Grafik) die Ansicht.',
        'didactics': {
            'concept': 'Eine Konstruktion (Paar → Mittelpunkt und Abstand) als Abbildung in einen Raum: Ein geometrisches Problem (Rechteck auf der Kurve) wird zur Frage, ob eine Fläche sich selbst trifft.',
            'representations': ['Kurve mit Punktpaar (Ebene)', 'Formel Paar ↦ (Mₓ, M_y, d)', 'Fläche aller Paare im Raum', 'Rechteck in der Ebene'],
            'misconception': 'Ein numerisch gefundenes Beispiel oder ein überzeugendes Bild sei ein Beweis.',
            'manipulate': 'Lage von P und Q auf der Kurve, Blickwinkel im Raum.',
            'predict': 'Wohin der Bildpunkt wandert, wenn Q auf P zuläuft (auf die Kurve, Höhe 0).',
            'conclusion': 'Zwei verschiedene Paare mit demselben Bildpunkt haben Diagonalen gleicher Mitte und gleicher Länge – sie bilden ein Rechteck.'},
        'objects': [{'id': i, 'role': r} for i, r in (('P', 'point_p'), ('Q', 'point_q'), ('PQ', 'distance'), ('M', 'midpoint'), ('d', 'distance'), ('X', 'lift'),
                                                     ('curve', 'curve'), ('surface', 'lift'), ('plane', 'curve'), ('zaxis', 'distance'), ('rect', 'point_u'),
                                                     ('U', 'point_u'), ('V', 'point_u'), ('UV', 'point_u'), ('Y', 'lift'))],
        'params': ['s', 't'], 'dependencies': [['s', 'P'], ['t', 'Q'], ['s', 'M'], ['t', 'M'], ['s', 'd'], ['t', 'd'], ['s', 'rect']],
        'steps': [
            {'id': 'pair', 'title': 'Zwei Punkte auf einer geschlossenen Kurve', 'targets': ['P', 'Q', 'curve'], 'camera': 'top',
             'formula': [P(), O(' = γ('), V('s', 3, 'P', 'point_p'), O(') = '), *pt('P', 'P', 'point_p')], 'formula2': [Q(), O(' = γ('), V('t', 3, 'Q', 'point_q'), O(') = '), *pt('Q', 'Q', 'point_q')],
             'text': 'γ(u) durchläuft die Kurve einmal für u von 0 bis 1. Ziehen Sie P oder Q – die Koordinaten folgen.'},
            {'id': 'chord', 'title': 'Die Sehne PQ', 'targets': ['PQ'], 'reveal': ['PQ'], 'camera': 'top',
             'formula': [T('Ein ungeordnetes Paar {'), P(), O(', '), Q(), T('} – die Reihenfolge spielt keine Rolle.')],
             'text': 'Gesucht sind vier Punkte der Kurve, die ein Rechteck bilden. Die Idee: Ein Rechteck ist durch seine beiden Diagonalen bestimmt.'},
            {'id': 'mid', 'title': 'Mittelpunkt der Sehne', 'targets': ['M'], 'reveal': ['M'], 'camera': 'top', 'zoom': ['P', 'Q', 'M'],
             'formula': [Sy('M', ref='M', role='midpoint'), O(' = ('), P(), O(' + '), Q(), O(') / 2 = '), *pt('M', 'M', 'midpoint')],
             'text': 'Die Diagonalen eines Rechtecks halbieren sich: Beide haben denselben Mittelpunkt.'},
            {'id': 'dist', 'title': 'Länge der Sehne', 'targets': ['PQ'], 'camera': 'top',
             'formula': [Sy('d', ref='PQ', role='distance'), O(' = |'), P(), O(' − '), Q(), O('| = '), V('d', 4, 'PQ', 'distance')],
             'text': 'Und die Diagonalen eines Rechtecks sind gleich lang. Mittelpunkt und Länge zusammen – das sind drei Zahlen.'},
            {'id': 'turn', 'title': 'Eine dritte Achse für den Abstand', 'targets': ['zaxis'], 'camera': '3d', 'anim': {'kind': 'camera', 'to': '3d'},
             'formula': [T('Ebene (x, y) für den Mittelpunkt, Höhe z für den Abstand d')],
             'text': 'Die Ansicht kippt: Die Kurve liegt jetzt in einer Ebene im Raum. Drei Zahlen pro Paar ergeben einen Punkt im Raum.'},
            {'id': 'lift', 'title': 'Das Paar wird zu einem Punkt im Raum', 'targets': ['X', 'd', 'M'], 'reveal': ['M', 'd', 'X'], 'camera': '3d', 'anim': {'kind': 'lift'},
             'formula': [T('{'), P(), O(', '), Q(), T('} ↦ '), O('('), V('lift.0', 3, 'M', 'midpoint'), O('; '), V('lift.1', 3, 'M', 'midpoint'), O('; '), V('lift.2', 3, 'd', 'distance'), O(')')],
             'text': 'Über dem Mittelpunkt M steigt der Punkt genau um d. Ziehen Sie P und Q und beobachten Sie, wie der Raumpunkt mitwandert.'},
            {'id': 'surface', 'title': 'Alle Paare zusammen: eine Fläche', 'targets': ['surface', 'curve'], 'reveal': ['surface'], 'camera': '3d',
             'formula': [T('Für P = Q ist d = 0: Der Rand der Fläche ist die Kurve selbst.')],
             'text': 'Jedes Paar liefert einen Punkt; alle Paare zusammen bilden eine geschlossene Fläche über der Kurve. Ein Rechteck auf der Kurve heißt: Zwei verschiedene Paare landen im selben Punkt – die Fläche trifft sich selbst.'},
            {'id': 'collision', 'title': 'Numerische Suche: zwei Paare, ein Punkt', 'targets': ['rect', 'P', 'Q', 'U', 'V', 'Y', 'X'], 'reveal': ['rect'], 'camera': '3d', 'anim': {'kind': 'seek'},
             'formula': [T('{'), P(), O(', '), Q(), T('*} ↦ '), O('('), V('rect.liftPQ.0', 4, 'X', 'lift'), O('; '), V('rect.liftPQ.1', 4, 'X', 'lift'), O('; '), V('rect.liftPQ.2', 4, 'X', 'lift'), O(')')],
             'formula2': [T('{'), Sy('U', ref='U', role='point_u'), O(', '), Sy('V', ref='V', role='point_u'), T('} ↦ '), O('('), V('rect.liftUV.0', 4, 'Y', 'lift'), O('; '), V('rect.liftUV.1', 4, 'Y', 'lift'), O('; '), V('rect.liftUV.2', 4, 'Y', 'lift'), O(')')],
             'text': 'Q wandert zum Partner Q*, für den das Newton-Verfahren ein zweites Paar {U, V} mit demselben Bildpunkt findet. Gleiche Mitte und gleiche Länge der Diagonalen: P, U, Q*, V bilden ein Rechteck.'},
            {'id': 'proof', 'title': 'Exploration ist kein Beweis', 'targets': ['rect'], 'reveal': ['rect'], 'camera': '3d',
             'formula': [T('Restfehler der Suche: '), V('rect.residual', 1, 'rect', 'point_u', e=True), T('   Fläche des Rechtecks: '), V('rect.area', 4, 'rect', 'point_u')],
             'text': 'Gezeigt ist ein numerisch gefundenes Beispiel für diese eine glatte Kurve, mit Gleitkomma-Restfehler. Dass jede geschlossene Kurve ein einbeschriebenes Rechteck hat, folgt erst aus einem topologischen Argument über diese Fläche – das Bild macht die Idee anschaulich, ersetzt den Beweis aber nicht.'}],
        'assumptions': ['Kurve: γ(u) = r(u)·(cos 2πu, sin 2πu) mit r(u) = 1 + 0,12·sin 4πu + 0,16·cos 6πu + 0,04·sin 10πu (glatt, sternförmig, absichtlich unsymmetrisch).',
                        'Rechtecksuche: Newton-Verfahren für (t, u, v) bei festem s aus 216 festen Startwerten; akzeptiert bei Restfehler < 10⁻¹¹; entartete Lösungen (zusammenfallende Ecken) werden verworfen.',
                        'Numerische Exploration: Ein gefundenes Rechteck ist ein Beispiel, kein Beweis; ein nicht gefundenes beweist nicht, dass keines existiert.'],
        'sources': ['Eigenes Referenzmodell (exam_mastery/labs/models.py: chord_lift, rect_search, rect_check)',
                    'Idee der Darstellung: 3Blue1Brown, „Who cares about topology? (Inscribed rectangle problem)“ (3blue1brown.com, Lektion inscribed-rect-v2); eigene Implementierung, keine Szenen übernommen'],
        'status': 'exploration'}
    return _finish(spec, sc)


# ------------------------------------------------------------------ reference scene C: cash flow as a process

def cashflow_scene(spec):
    u = spec['model'].get('unit', 'k€')
    sc = {
        'schema': SCHEMA, 'type': 'cashflow', 'title': 'Vom Geschäftsvorgang zum Finanzierungsbedarf',
        'lead': 'Jeder Verkauf wird erst nach dem Zahlungsziel zu Geld. Verschieben Sie das Zahlungsziel A im Regler-Bereich und beobachten Sie, wie die Zahlungseingänge wandern.',
        'didactics': {
            'concept': 'Der Finanzierungsbedarf ist kein Einzelwert einer Periode, sondern der tiefste Punkt einer Summe über die Zeit: Er entsteht, weil Auszahlungen sofort, Einzahlungen erst nach dem Zahlungsziel fließen.',
            'representations': ['Geschäftsvorgänge auf der Zeitachse', 'Rekursionsformel der Liquidität', 'Kurve der kumulierten Liquidität', 'Kennzahl Finanzierungsbedarf'],
            'misconception': 'Der Bedarf sei der Endsaldo oder der schlechteste einzelne Cashflow; oder: Umsatz sei gleich Zahlungseingang.',
            'manipulate': 'Zahlungsziel A und B, Anfangsliquidität, Horizont, Zahlenreihen.',
            'predict': 'Wie sich der tiefste Punkt verschiebt, wenn Zahlungen eine Periode später kommen.',
            'conclusion': 'Ein längeres Zahlungsziel verlängert die Phase, in der Kosten vorfinanziert werden müssen; der tiefste Stand der Summe – der Bedarf – sinkt weiter.'},
        'objects': [{'id': 'term', 'role': 'term'}, {'id': 'need', 'role': 'need'}, {'id': 'deficit', 'role': 'need'}, {'id': 'balance', 'role': 'balance'},
                    {'id': 'alt', 'role': 'balance'}, {'id': 'lane-sale', 'role': 'sale'}, {'id': 'lane-pay', 'role': 'inflow'}, {'id': 'lane-out', 'role': 'outflow'},
                    {'id': 'lane-bal', 'role': 'balance'},
                    {'id': 'col{K}', 'role': 'balance', 'repeat': 'rows'}, {'id': 'bal{K}', 'role': 'balance', 'repeat': 'rows'}, {'id': 'in{K}', 'role': 'inflow', 'repeat': 'rows'},
                    {'id': 'cost{K}', 'role': 'outflow', 'repeat': 'rows'}, {'id': 'inv{K}', 'role': 'invest', 'repeat': 'rows'}, {'id': 'sale{K}', 'role': 'sale', 'repeat': 'rows'}],
        'params': ['delay', 'delayB', 'start_cash', 'horizon'],
        'dependencies': [['delay', 'in{K}'], ['delay', 'balance'], ['delay', 'need'], ['delayB', 'alt'], ['start_cash', 'balance'], ['horizon', 'col{K}']],
        'steps': [
            {'id': 'events', 'title': 'Geschäftsvorgänge: Verkauf und Rechnung', 'targets': ['lane-sale'],
             'formula': [T('Verkauf in Periode t → Rechnung in Periode t → Geld erst in Periode t + z')],
             'text': 'Oben stehen die Aufträge je Periode. Mit dem Verkauf entsteht Umsatz und eine Forderung – aber noch kein Geld.'},
            {'id': 'term', 'title': 'Das Zahlungsziel verschiebt jede Zahlung', 'targets': ['term', 'lane-pay'], 'reveal': ['term'], 'anim': {'kind': 'arcs'},
             'formula': [Sy('E', 't', None, 'inflow'), O(' = Auftrag'), Sy('', 't − z'), O('    z = '), V('delay', 0, 'term', 'term'), T(' Perioden')],
             'text': 'Jeder Bogen führt von einem Verkauf zu seinem Zahlungseingang. Zahlungen, die nach dem Horizont kämen, enden gestrichelt am Rand.'},
            {'id': 'out', 'title': 'Auszahlungen fließen sofort', 'targets': ['lane-out'], 'reveal': ['out'],
             'formula': [Sy('A', 't', None, 'outflow'), O(' = laufende Kosten'), Sy('', 't'), O(' + Investition'), Sy('', 't')],
             'text': 'Kosten und Investitionen werden in ihrer Periode bezahlt – unabhängig davon, wann die Kunden zahlen.'},
            {'id': 'period', 'repeat': 'rows', 'var': 'k', 'title': 'Periode {K}: Liquidität fortschreiben', 'targets': ['col{K}', 'bal{K}'], 'anim': {'kind': 'period'},
             'formula': [Sy('L', '{K}', 'bal{K}', 'balance'), O(' = '), Sy('L', 'vorher', None, 'balance'), O(' + '), Sy('E', '{K}', 'in{K}', 'inflow'), O(' − '), Sy('K', '{K}', 'cost{K}', 'outflow'), O(' − '), Sy('I', '{K}', 'inv{K}', 'invest')],
             'formula2': [O('= '), V('rows.{k}.prev', 0, None, 'balance', u), O(' + '), V('rows.{k}.inflow', 0, 'in{K}', 'inflow', u), O(' − '), V('rows.{k}.cost', 0, 'cost{K}', 'outflow', u), O(' − '), V('rows.{k}.invest', 0, 'inv{K}', 'invest', u), O(' = '), V('rows.{k}.balance', 0, 'bal{K}', 'balance', u)],
             'text': 'Der neue Stand ist der alte Stand plus der Saldo dieser Periode. Die Kurve unten wächst Periode für Periode.'},
            {'id': 'need', 'title': 'Der tiefste Punkt ist der Finanzierungsbedarf', 'targets': ['need', 'deficit'], 'reveal': ['balance', 'need'],
             'formula': [T('Finanzierungsbedarf = max(0; −min L) = '), V('financing_need', 0, 'need', 'need', u)],
             'formula2': [T('tiefster Stand in Periode '), V('min_period', 0, 'need', 'need'), O(': L = '), V('min_balance', 0, 'need', 'need', u), T('   Endsaldo: '), V('final_balance', 0, 'balance', 'balance', u)],
             'text': 'Bis hierhin musste jede Auszahlung vorfinanziert werden; danach überwiegen die eintreffenden Zahlungen. Wer nur den Endsaldo finanziert, ist vorher zahlungsunfähig.'},
            {'id': 'compare', 'title': 'Vergleich: anderes Zahlungsziel', 'targets': ['alt', 'need'], 'reveal': ['balance', 'need', 'alt'],
             'formula': [T('Zahlungsziel B = '), V('delayB', 0, 'alt', 'balance'), T(': Bedarf '), V('alt.financing_need', 0, 'alt', 'need', u), T('  (Unterschied '), V('diff', 0, 'alt', 'need', u), T(')')],
             'text': 'Die gestrichelte Kurve zeigt Szenario B. Ändern Sie Zahlungsziel A: Die Zahlungseingänge oben wandern, die Kurve baut sich neu auf.'}],
        'assumptions': list(spec['assumptions']) + ['Die Rechnung wird in der Periode des Verkaufs gestellt (Annahme der Darstellung); die Quelle unterscheidet Auftrag und Zahlung, nicht Rechnungsdatum.',
                                                    'Die laufenden Kosten sind nicht weiter aufgeteilt (z. B. in Material und Personal), weil die Quelle sie nur als Summe angibt.'],
        'sources': list(spec['sources']) + ['Eigenes Referenzmodell (exam_mastery/labs/models.py: cashflow, cashflow_ledger)'],
        'status': 'computation'}
    return _finish(spec, sc)


BUILDERS = {'mlp': network_scene, 'chord': chord_scene, 'cashflow': cashflow_scene}


def add(spec):
    """Adds the matching reference scene to a lab spec (idempotent)."""
    if spec.get('scene') or spec['model']['kind'] not in BUILDERS:
        return spec
    return BUILDERS[spec['model']['kind']](spec)
