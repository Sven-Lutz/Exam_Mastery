"""B14: learning sequence of every lab (DR-1.2, rules L1-L15). Deterministic: every number in a mission, choice item
or takeaway is computed with labs/models.py; every exploration mission carries a witness (parameter setting) that the
validator replays through the reference model, and the mission must NOT already hold in the starting state.

Phases rendered by templates/em_labs.js:
1 Vorhersagen (with confidence)  2 Beobachten  3 Erklären (own explanation first, then the expert explanation)
4 Erkunden (missions checked live against the simulation state)  5 Üben (numeric + concept items with diagnostic
feedback)  6 Übertragen (transfer item)  7 Sichern (own summary first, then the takeaways; spaced repetition via Anki)
"""
import math

from . import models as M

OPS = {'<': lambda a, b: a < b, '<=': lambda a, b: a <= b, '==': lambda a, b: a == b, '!=': lambda a, b: a != b,
       '>': lambda a, b: a > b, '>=': lambda a, b: a >= b}


class PedagogyError(ValueError):
    pass


def defaults(spec):
    return {d['id']: d['default'] for d in spec['params']}


def metrics(spec, params):
    """Metric values with exactly the names the browser view writes to the lab element's data-* attributes."""
    m, k = spec['model'], spec['model']['kind']
    if k == 'cashflow':
        T = int(params.get('horizon', len(m['orders'])))
        ext = lambda xs, fill_last: [xs[i] if i < len(xs) else (xs[-1] if (fill_last and xs) else 0) for i in range(T)]
        o, c, inv = ext(m['orders'], True), ext(m['cost'], True), ext(m['invest'], False)
        a = M.cashflow(o, int(params['delay']), c, inv, float(params.get('start_cash', 0)), T)
        b = M.cashflow(o, int(params['delayB']), c, inv, float(params.get('start_cash', 0)), T)
        return {'need': a['financing_need'], 'minPeriod': a['min_period'], 'final': a['final_balance'], 'needB': b['financing_need']}
    if k == 'risk':
        a, b = M.risk_matrix(int(params['l']), int(params['i']), m['classes']), M.risk_matrix(int(params['l2']), int(params['i2']), m['classes'])
        return {'score': a['score'], 'cls': a['class'], 'scoreB': b['score'], 'clsB': b['class'],
                'rank': M.CLASS_RANK[a['class']], 'rankB': M.CLASS_RANK[b['class']],
                'eHi': M.expected_loss_range(int(params['l']), float(params['loss']))[1],
                'eHiB': M.expected_loss_range(int(params['l2']), float(params['loss2']))[1]}
    if k == 'van_westendorp':
        r = M.van_westendorp(m['rows'], params['method'], params['segment'], float(params['te_shift']))
        return {**r['points'], 'width': r['range_width'], 'nValid': r['n_valid']}
    if k == 'mlp':
        p = {'W1': [[params['w11'], params['w12']], [params['w21'], params['w22']]], 'b1': [params['b1'], params['b2']],
             'W2': [params['v1'], params['v2']], 'c': None}
        p = {'W1': p['W1'], 'b1': p['b1'], 'W2': p['W2'], 'b2': params['c']}
        x, t, lr = [params['x1'], params['x2']], params['t'], params['lr']
        out, last = {}, None
        for _ in range(int(params.get('steps', 0))):
            before = M.mlp_loss(M.mlp_forward(p, x, params['ha'], params['oa'])['y'], t)
            p, _bw = M.mlp_step(p, x, t, lr, params['ha'], params['oa'])
            last = M.mlp_loss(M.mlp_forward(p, x, params['ha'], params['oa'])['y'], t) - before
        out['loss'] = M.mlp_loss(M.mlp_forward(p, x, params['ha'], params['oa'])['y'], t)
        out['steps'] = int(params.get('steps', 0))
        if last is not None:
            out['lastDelta'] = last
        return out
    if k == 'mdp':
        from . import mdp as MDP
        return MDP.metrics(spec, params)
    if k in ('sequence', 'cap_table'):
        from .build import generic
        return generic(k).metrics(spec, params)
    raise PedagogyError(f'no metrics for {k}')


def holds(cond, met, par):
    for c in cond:
        if 'm' in c:
            if c['m'] not in met:
                return False
            a = met[c['m']]
        else:
            a = par.get(c['p'])
        b = met.get(c['ref']) if 'ref' in c else c['v']
        if a is None or b is None:
            return False
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            a, b = float(a), float(b)
        else:
            a, b = str(a), str(b)
        if not OPS[c['op']](a, b):
            return False
    return True


def validate(spec):
    s = spec['sequence']
    ph = s.get('phases') or ALL_PHASES
    if not set(ph) <= set(ALL_PHASES) or not {'predict', 'observe', 'practice'} <= set(ph):
        raise PedagogyError('phases must be a subset of the seven blocks and contain predict, observe and practice')
    for key, phase in (('explore', 'explore'), ('takeaways', 'summary')):
        if phase in ph and not s.get(key):
            raise PedagogyError(f'sequence.{key} missing for phase {phase} (DR-1.2 L11-L15)')
    p = s['predict']
    if not p.get('explain_prompt') or not p.get('explain_keys'):
        raise PedagogyError('prediction needs explain_prompt and explain_keys (self-explanation before the expert explanation)')
    if 'summary' in ph and not s.get('summary_prompt'):
        raise PedagogyError('summary_prompt missing')
    d0 = defaults(spec)
    for mi in (s.get('explore') or []) if 'explore' in ph else []:
        base_m = metrics(spec, d0)
        if holds(mi['cond'], base_m, d0):
            raise PedagogyError(f'mission {mi["id"]} already holds in the starting state')
        w = {**d0, **mi['witness']}
        if not holds(mi['cond'], metrics(spec, w), w):
            raise PedagogyError(f'mission {mi["id"]}: witness does not satisfy the condition (not solvable as stated)')
    choice = [t for t in s['tasks'] if t.get('type') == 'choice']
    if not choice:
        raise PedagogyError('at least one concept item (type choice) is required')
    for t in choice:
        vals = [o['value'] for o in t['options']]
        if t['correct'] not in vals or len(set(vals)) != len(vals) or len(vals) < 3:
            raise PedagogyError(f'choice {t["id"]}: options invalid')
        if any(not o.get('feedback') for o in t['options'] if o['value'] != t['correct']):
            raise PedagogyError(f'choice {t["id"]}: every wrong option needs diagnostic feedback')
    if ('transfer' in ph) != (sum(1 for t in s['tasks'] if t.get('transfer')) == 1):
        raise PedagogyError('exactly one transfer item is required')
    return True


def _f(x, d=0):
    s = f'{x:,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


# ------------------------------------------------------------------ per lab

def _cashflow(spec):
    m = spec['model']; d0 = defaults(spec)
    need0 = metrics(spec, d0)['need']
    start = math.ceil(need0)
    # mission 2: the shortest payment delay whose financing need exceeds a round threshold
    needs = {d: metrics(spec, {**d0, 'delay': d})['need'] for d in range(0, 9)}
    dstar = next((d for d in range(d0['delay'] + 2, 9) if needs[d] > needs[d - 1]), None)
    ex = [{'id': 'nocredit', 'title': 'Ohne Kredit durch die Anlaufphase',
           'prompt': f'Ausgangsfall (Zahlungsziel A = {d0["delay"]}): Stellen Sie die kleinste Anfangsliquidität ein, mit der die kumulierte Liquidität nie unter null fällt.',
           'hint': 'Der tiefste Stand der kumulierten Liquidität muss genau ausgeglichen werden.',
           'success': f'Genau {_f(start)} {m["unit"]}: Die Anfangsliquidität muss den tiefsten Stand decken, nicht den Endsaldo.',
           'cond': [{'m': 'need', 'op': '==', 'v': 0}, {'p': 'start_cash', 'op': '<=', 'v': start}, {'p': 'delay', 'op': '==', 'v': d0['delay']}],
           'witness': {'start_cash': start}}]
    if dstar is not None:
        thr = math.floor((needs[dstar - 1] + needs[dstar]) / 2 / 50) * 50
        if needs[dstar - 1] < thr < needs[dstar]:
            ex.append({'id': 'critical', 'title': 'Kritisches Zahlungsziel',
                       'prompt': f'Ohne Anfangsliquidität: Ab welchem Zahlungsziel A übersteigt der Finanzierungsbedarf {_f(thr)} {m["unit"]}? Stellen Sie das kürzeste solche Zahlungsziel ein.',
                       'hint': 'Erhöhen Sie das Zahlungsziel Schritt für Schritt und beobachten Sie die Kennzahl „Finanzierungsbedarf A“.',
                       'success': f'Ab Zahlungsziel {dstar} liegt der Bedarf bei {_f(needs[dstar])} {m["unit"]}. Jede Periode Verzug kostet Vorfinanzierung.',
                       'cond': [{'p': 'delay', 'op': '==', 'v': dstar}, {'m': 'need', 'op': '>', 'v': thr}, {'p': 'start_cash', 'op': '==', 'v': 0}],
                       'witness': {'delay': dstar, 'start_cash': 0}})
    return {
        'explain_prompt': 'Erklären Sie in ein bis zwei Sätzen, warum ein späteres Zahlungsziel den Finanzierungsbedarf verändert.',
        'explain_keys': [{'label': 'Einzahlungen kommen später', 'terms': ['später', 'verschieb', 'verzög', 'nach hinten']},
                         {'label': 'Auszahlungen fallen weiter sofort an', 'terms': ['kosten', 'auszahl', 'sofort', 'weiter']},
                         {'label': 'der tiefste kumulierte Stand entscheidet', 'terms': ['tiefst', 'minimum', 'kumul', 'laufende summe']}],
        'explore': ex,
        'choice': {'id': 'concept', 'type': 'choice', 'title': 'Konzeptfrage: Endsaldo oder Tiefpunkt?',
                   'prompt': 'Ein Start-up erwartet für das Jahr einen positiven Endsaldo. Was folgt daraus für die Finanzierung?',
                   'options': [{'value': 'none', 'label': 'Es braucht keine Finanzierung, weil am Ende Geld übrig ist.',
                                'feedback': 'Der Endsaldo verschweigt die Zwischenstände. Fällt die kumulierte Liquidität vorher unter null, ist das Unternehmen in dieser Periode zahlungsunfähig.'},
                               {'value': 'min', 'label': 'Es braucht den Betrag des tiefsten kumulierten Standes, falls dieser negativ ist.', 'feedback': ''},
                               {'value': 'worst', 'label': 'Es braucht so viel wie der größte negative Cashflow einer einzelnen Periode.',
                                'feedback': 'Ein einzelner Periodensaldo reicht nicht: Negative Cashflows summieren sich, bis Zahlungen eingehen.'},
                               {'value': 'all', 'label': 'Es braucht die Summe aller Auszahlungen.',
                                'feedback': 'Einzahlungen im Zeitraum decken einen Teil der Auszahlungen; zu finanzieren ist nur die Lücke.'}],
                   'correct': 'min', 'explanation': 'Maßgeblich ist der tiefste Punkt der laufenden Summe der Cashflows; das zeigt die Linie im Diagramm.'},
        'takeaways': ['Liquidität ist nicht Gewinn: Ein Auftrag bringt erst mit der Zahlung Geld.',
                      'Der Finanzierungsbedarf ist der Betrag des tiefsten kumulierten Liquiditätsstands – nicht der Endsaldo.',
                      'Spätere Zahlungsziele verschieben Einzahlungen nach hinten und erhöhen in der Regel den Bedarf.'],
        'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie man aus einem Zahlungsplan den Finanzierungsbedarf bestimmt.',
        'transfer_id': 'transfer'}


def _risk(spec):
    m = spec['model']; d0 = defaults(spec); cl = m['classes']
    pair = next(((a, b) for a in [(l, i) for l in range(1, 6) for i in range(1, 6)] for b in [(l, i) for l in range(1, 6) for i in range(1, 6)]
                 if a[0] * a[1] == b[0] * b[1] and a[0] * a[1] != 10 and cl[a[0] - 1][a[1] - 1] != cl[b[0] - 1][b[1] - 1]), None)
    eHiB = M.expected_loss_range(d0['l2'], d0['loss2'])[1]
    rankB = M.CLASS_RANK[cl[d0['l2'] - 1][d0['i2'] - 1]]
    low = next(((l, i) for l in range(1, 6) for i in range(1, 6) if M.CLASS_RANK[cl[l - 1][i - 1]] < rankB), None)
    ex = []
    if pair:
        ex.append({'id': 'sameScore', 'title': 'Gleicher Punktwert, andere Klasse',
                   'prompt': 'Stellen Sie A und B so ein, dass beide denselben Punktwert haben (nicht 10), die Matrix sie aber verschiedenen Klassen zuordnet.',
                   'hint': 'Suchen Sie Produkte, die auf zwei Wegen entstehen, z. B. 1 × 4 und 4 × 1.',
                   'success': 'Gefunden: Die Klasse hängt am Feld, nicht am Produkt.',
                   'cond': [{'m': 'score', 'op': '==', 'ref': 'scoreB'}, {'m': 'cls', 'op': '!=', 'ref': 'clsB'}, {'m': 'score', 'op': '!=', 'v': 10}],
                   'witness': {'l': pair[0][0], 'i': pair[0][1], 'l2': pair[1][0], 'i2': pair[1][1]}})
    if low:
        loss = 10 ** math.ceil(math.log10(eHiB / M.LIKELIHOOD_BANDS[low[0]][1] * 1.01 + 1))
        ex.append({'id': 'lowClassHighLoss', 'title': 'Niedrigere Klasse, höherer Schaden',
                   'prompt': 'Lassen Sie B unverändert. Stellen Sie A so ein, dass A in einer niedrigeren Klasse liegt als B, aber einen höheren maximal erwarteten Schaden hat.',
                   'hint': 'Die Matrix kennt keine Euro-Beträge: Eine seltene Stufe mit sehr großer Schadenshöhe kann B übertreffen.',
                   'success': 'Genau das verdeckt eine reine Rangliste: Die Schadenshöhe steckt weder im Punktwert noch in der Klasse.',
                   'cond': [{'m': 'rank', 'op': '<', 'ref': 'rankB'}, {'m': 'eHi', 'op': '>', 'ref': 'eHiB'}],
                   'witness': {'l': low[0], 'i': low[1], 'loss': loss}})
    return {
        'explain_prompt': 'Erklären Sie, warum zwei Risiken mit gleichem Punktwert in der Matrix der Vorlesung verschieden eingestuft werden können.',
        'explain_keys': [{'label': 'die Klasse hängt am Feld der Matrix', 'terms': ['feld', 'zelle', 'position', 'matrix']},
                         {'label': 'große Auswirkungen wiegen schwerer', 'terms': ['auswirkung', 'schaden', 'schwer', 'folgen']},
                         {'label': 'die Stufen sind nur Ränge', 'terms': ['rang', 'ordinal', 'stufe', 'kategor']}],
        'explore': ex,
        'choice': {'id': 'concept', 'type': 'choice', 'title': 'Konzeptfrage: Was leistet der Punktwert?',
                   'prompt': 'Ein Team sortiert seine Risiken nur nach dem Punktwert (Auswirkungsstufe × Wahrscheinlichkeitsstufe). Was ist die wichtigste Grenze dieses Vorgehens?',
                   'options': [{'value': 'ev', 'label': 'Keine – der Punktwert ist der erwartete Schaden.',
                                'feedback': 'Der Punktwert multipliziert Rangstufen, keine Wahrscheinlichkeiten und Euro-Beträge; er ist kein Erwartungswert.'},
                               {'value': 'hide', 'label': 'Gleiche Punktwerte können verschiedene Klassen und sehr verschiedene erwartete Schäden verdecken.', 'feedback': ''},
                               {'value': 'double', 'label': 'Die Wahrscheinlichkeit wird doppelt gezählt.',
                                'feedback': 'Jede Achse geht genau einmal ein. Das Problem ist die Rangskala, nicht eine Doppelzählung.'},
                               {'value': 'rare', 'label': 'Er bevorzugt immer seltene Risiken.',
                                'feedback': 'Eine solche feste Richtung gibt es nicht. Entscheidend ist, dass der Rang die Schadenshöhe nicht abbildet.'}],
                   'correct': 'hide', 'explanation': 'Die Matrix ist eine Priorisierungshilfe. Für Entscheidungen über Geld braucht man zusätzlich Wahrscheinlichkeit × Schadenshöhe.'},
        'takeaways': ['Die Klasse eines Risikos steht im Feld der Matrix, nicht im Punktwert.',
                      'Punktwert = Produkt zweier Rangstufen: gut zum groben Sortieren, kein Risikomaß in Euro.',
                      'Für Entscheidungen über Geld braucht man Wahrscheinlichkeit × Schadenshöhe – die Matrix ergänzt, ersetzt das nicht.'],
        'summary_prompt': 'Fassen Sie in einem Satz zusammen, was die Risikomatrix leistet und was nicht.',
        'transfer_id': 'ev'}


def _vw(spec):
    m = spec['model']; d0 = defaults(spec); rows = m['rows']
    opp = lambda s: M.van_westendorp(rows, 'standard', 'all', s)['points']['opp']
    target = math.ceil(opp(15) * 2) / 2
    shift = next(s for s in range(0, 31) if opp(s) >= target)
    combos = [(seg, me) for seg in ['all'] + list(m['segments']) for me in ('standard', 'alternative')]
    w = {c: M.van_westendorp(rows, c[1], c[0])['range_width'] for c in combos}
    best = min(combos, key=lambda c: w[c])
    seg_label = 'alle Befragten' if best[0] == 'all' else 'Segment ' + best[0]
    return {
        'explain_prompt': 'Erklären Sie, warum genau diese Preispunkte wandern und die anderen nicht.',
        'explain_keys': [{'label': 'Preispunkte sind Schnittpunkte zweier Kurven', 'terms': ['schnitt', 'kreuz', 'kurve']},
                         {'label': 'nur Kurven mit „zu teuer“ ändern sich', 'terms': ['zu teuer']},
                         {'label': 'IPP und PMC hängen an anderen Fragen', 'terms': ['ipp', 'pmc', 'günstig', 'billig', 'andere frage']}],
        'explore': [{'id': 'oppUp', 'title': 'Den „optimalen Preis“ verschieben',
                     'prompt': f'Alle Befragten, Standardkonvention: Verschieben Sie die „zu teuer“-Antworten so wenig wie möglich, dass der OPP mindestens {_f(target, 2)} € erreicht.',
                     'hint': 'Erhöhen Sie die Verschiebung in Ein-Euro-Schritten und beobachten Sie die OPP-Kennzahl.',
                     'success': f'Mit {shift} € Verschiebung. Der OPP folgt der „zu teuer“-Kurve – er misst Wahrnehmung, kein Optimum.',
                     'cond': [{'m': 'opp', 'op': '>=', 'v': target}, {'p': 'te_shift', 'op': '==', 'v': shift}, {'p': 'segment', 'op': '==', 'v': 'all'}, {'p': 'method', 'op': '==', 'v': 'standard'}],
                     'witness': {'te_shift': shift}},
                    {'id': 'narrowest', 'title': 'Der schmalste Preisbereich',
                     'prompt': 'Ohne Verschiebung: Welche Kombination aus Segment und Konvention ergibt den schmalsten akzeptablen Bereich (PME − PMC)? Stellen Sie sie ein.',
                     'hint': 'Vergleichen Sie die Kennzahl „akzeptabler Bereich“ für jedes Segment unter beiden Konventionen.',
                     'success': f'{seg_label}, {"Standard" if best[1] == "standard" else "Praxisvariante"}: {_f(w[best], 2)} €. Die Praxisvariante schneidet die Rohkurven und ergibt engere Grenzen.',
                     'cond': [{'p': 'segment', 'op': '==', 'v': best[0]}, {'p': 'method', 'op': '==', 'v': best[1]}, {'p': 'te_shift', 'op': '==', 'v': 0}],
                     'witness': {'segment': best[0], 'method': best[1], 'te_shift': 0}}],
        'choice': {'id': 'concept', 'type': 'choice', 'title': 'Konzeptfrage: Ist der OPP optimal?',
                   'prompt': 'Ein Gründerteam setzt den Preis auf den OPP, weil er „optimaler Preis“ heißt. Was ist die beste Bewertung?',
                   'options': [{'value': 'profit', 'label': 'Richtig: Beim OPP ist der Gewinn maximal.',
                                'feedback': 'Die Methode erhebt weder Absatzmengen noch Kosten; ohne sie lässt sich kein Gewinnoptimum bestimmen.'},
                               {'value': 'revenue', 'label': 'Richtig: Beim OPP ist der Umsatz maximal.',
                                'feedback': 'Umsatz ist Preis mal Menge; die Methode misst Wahrnehmung, keine Kaufmengen.'},
                               {'value': 'balance', 'label': 'Am OPP finden gleich viele den Preis zu billig wie zu teuer – eine Orientierung zur Preiswahrnehmung, keine Optimierung.', 'feedback': ''},
                               {'value': 'mean', 'label': 'Der OPP ist der Mittelwert aller genannten Preise.',
                                'feedback': 'Der OPP ist ein Schnittpunkt zweier Anteilskurven, kein Mittelwert der Antworten.'}],
                   'correct': 'balance', 'explanation': 'Der Name stammt aus der Methode (1976). Für Preisentscheidungen braucht man zusätzlich Absatz- und Kostendaten.'},
        'takeaways': ['Jede der vier Fragen liefert eine Anteilskurve; die Preispunkte sind Schnittpunkte von Kurvenpaaren.',
                      'Der akzeptable Bereich liegt zwischen PMC und PME; seine Grenzen hängen von der Konvention ab.',
                      'Der „optimale Preis“ ist ein Methodenname: Er beschreibt Wahrnehmung, nicht Gewinn oder Umsatz.',
                      'Segmente haben eigene Bereiche; ein Durchschnitt über alle kann sie verdecken.'],
        'summary_prompt': 'Fassen Sie in einem Satz zusammen, was die Van-Westendorp-Methode liefert und was nicht.',
        'transfer_id': 'range'}


def _mlp(spec):
    d0 = defaults(spec)
    n = next((k for k in range(1, 400) if metrics(spec, {**d0, 'steps': k})['loss'] < 1e-3), None)
    big = next((lr for lr in (1, 2, 3, 4, 5) if metrics(spec, {**d0, 'lr': lr, 'steps': 1}).get('lastDelta', -1) > 0), None)
    ex = []
    if n:
        ex.append({'id': 'converge', 'title': 'Verlust unter 0,001',
                   'prompt': 'Trainieren Sie das Netz mit den Startwerten, bis der Verlust unter 0,001 liegt.',
                   'hint': 'Nutzen Sie „Automatisch (20 Schritte)“ mehrmals und beobachten Sie die Verlustkurve.',
                   'success': f'Nach etwa {n} Schritten mit η = {_f(d0["lr"], 3)}. Der Verlust sinkt anfangs schnell, dann immer langsamer.',
                   'cond': [{'m': 'loss', 'op': '<', 'v': 1e-3}], 'witness': {'steps': n}})
    l10 = metrics(spec, {**d0, 'steps': 10})['loss']
    fast = next((lr for lr in (1, 1.5, 2, 3, 4, 5) if metrics(spec, {**d0, 'lr': lr, 'steps': 10})['loss'] < l10 / 4), None)
    if fast:
        goal = float(f"{l10 / 3:.1g}")
        if metrics(spec, {**d0, 'lr': fast, 'steps': 10})['loss'] < goal < l10:
            ex.append({'id': 'rate', 'title': 'Lernrate wählen',
                       'prompt': f'Mit η = {_f(d0["lr"], 1)} liegt der Verlust nach 10 Schritten bei {_f(l10, 4)}. Wählen Sie eine Lernrate, mit der er nach genau 10 Schritten unter {str(goal).replace(".", ",")} liegt.',
                       'hint': 'Zurücksetzen, Lernrate ändern, dann „Automatisch“ bis 10 Schritte – oder zehnmal „Einen Lernschritt ausführen“.',
                       'success': 'Eine größere Lernrate macht größere Schritte entlang des Gradienten – solange die lineare Näherung trägt.',
                       'cond': [{'m': 'steps', 'op': '==', 'v': 10}, {'m': 'loss', 'op': '<', 'v': goal}], 'witness': {'lr': fast, 'steps': 10}})
    if big:
        ex.append({'id': 'overshoot', 'title': 'Zu große Lernrate',
                   'prompt': 'Setzen Sie die Startwerte zurück und wählen Sie eine Lernrate, bei der ein einzelner Lernschritt den Verlust erhöht.',
                   'hint': 'Probieren Sie Lernraten zwischen 1 und 5 und führen Sie jeweils genau einen Schritt aus.',
                   'success': 'Der Gradient gilt nur lokal: Ein zu großer Schritt springt über das Minimum hinaus.',
                   'cond': [{'m': 'lastDelta', 'op': '>', 'v': 0}], 'witness': {'lr': big, 'steps': 1}})
    return {
        'explain_prompt': 'Erklären Sie mit dem Gradienten, warum der Verlust so reagiert hat.',
        'explain_keys': [{'label': 'Vorzeichen des Gradienten', 'terms': ['vorzeichen', 'negativ', 'positiv', 'gradient']},
                         {'label': 'Kettenregel / Fehlersignal δ', 'terms': ['ketten', 'δ', 'delta', 'fehlersignal']},
                         {'label': 'gilt nur für kleine Änderungen', 'terms': ['klein', 'lokal', 'näherung']}],
        'explore': ex,
        'choice': {'id': 'concept', 'type': 'choice', 'title': 'Konzeptfrage: Sättigung',
                   'prompt': 'Warum lernt eine Sigmoid-Einheit kaum noch, wenn |z| sehr groß ist?',
                   'options': [{'value': 'deriv', 'label': 'Weil σ′(z) dort fast 0 ist und jeder Gradient durch diese Einheit mit σ′(z) multipliziert wird.', 'feedback': ''},
                               {'value': 'lr', 'label': 'Weil die Lernrate automatisch kleiner wird.', 'feedback': 'Die Lernrate bleibt konstant; klein wird der Gradient.'},
                               {'value': 'zero', 'label': 'Weil der Verlust dann schon 0 ist.',
                                'feedback': 'Sättigung tritt auch bei großem Verlust auf: Die Ausgabe sitzt dann am falschen Rand fest.'},
                               {'value': 'rule', 'label': 'Weil große Gewichte nicht verändert werden dürfen.',
                                'feedback': 'Eine solche Regel gibt es nicht; die Änderung ist η · Gradient, und der Gradient ist klein.'}],
                   'correct': 'deriv', 'explanation': 'Für |z| > 4 ist σ′(z) < 0,018. Das ist der Kern verschwindender Gradienten.'},
        'takeaways': ['Backpropagation ist die Kettenregel: Das Fehlersignal δ wird rückwärts mit Gewichten und Aktivierungsableitungen multipliziert.',
                      'Gradientenabstieg geht gegen den Gradienten: θ ← θ − η · ∂L/∂θ.',
                      'Zu große Lernraten können den Verlust erhöhen; gesättigte Einheiten lernen kaum.'],
        'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie ein Lernschritt die Gewichte verändert.',
        'transfer_id': 'transfer'}


def _chord(spec):
    return {
        'explain_prompt': 'Erklären Sie, warum der Raumpunkt so reagiert, wenn Q auf P zuläuft.',
        'explain_keys': [{'label': 'Abstand d geht gegen 0', 'terms': ['abstand', 'null', '0', 'höhe']},
                         {'label': 'Mittelpunkt geht gegen P', 'terms': ['mittelpunkt', 'mitte']},
                         {'label': 'Kurve ist der Rand der Fläche', 'terms': ['rand', 'kurve']}],
        'explore': [],
        'choice': {'id': 'concept', 'type': 'choice', 'title': 'Konzeptfrage: zwei Paare, ein Punkt',
                   'prompt': 'Zwei verschiedene Punktpaare {P, Q} und {U, V} der Kurve haben denselben Raumpunkt (Mₓ, M_y, d). Was bilden P, U, Q, V?',
                   'options': [{'value': 'rect', 'label': 'Ein Rechteck: Die Diagonalen PQ und UV haben dieselbe Mitte und dieselbe Länge.', 'feedback': ''},
                               {'value': 'square', 'label': 'Immer ein Quadrat.', 'feedback': 'Ein Quadrat bräuchte zusätzlich senkrechte Diagonalen; gleiche Mitte und Länge erzwingen nur ein Rechteck.'},
                               {'value': 'para', 'label': 'Ein Parallelogramm, mehr lässt sich nicht sagen.', 'feedback': 'Gleiche Mitte allein ergibt ein Parallelogramm. Die gleiche Höhe d heißt gleich lange Diagonalen – das macht es zum Rechteck.'},
                               {'value': 'proof', 'label': 'Einen Beweis, dass jede Kurve ein Rechteck enthält.', 'feedback': 'Ein gefundenes Beispiel auf einer Kurve sagt nichts über alle Kurven. Dafür braucht es ein allgemeines Argument.'}],
                   'correct': 'rect', 'explanation': 'Ein Viereck, dessen Diagonalen sich halbieren und gleich lang sind, ist ein Rechteck.'},
        'takeaways': ['Ein Punktpaar lässt sich als Punkt (Mittelpunkt, Abstand) im Raum darstellen; alle Paare bilden eine Fläche, deren Rand die Kurve ist.',
                      'Zwei Paare mit gleichem Bildpunkt sind die Diagonalen eines Rechtecks.',
                      'Numerisch gefundene Beispiele sind Exploration; die Aussage für alle Kurven braucht einen Beweis.'],
        'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie aus einem Punktpaar ein Raumpunkt wird.',
        'transfer_id': 'transfer'}


ALL_PHASES = ['predict', 'observe', 'explain', 'explore', 'practice', 'transfer', 'summary']
# B15: building blocks chosen per learning goal, not one mandatory sequence. A simple ordinal classification
# (risk matrix) needs no free exploration and no separate consolidation step; models whose behaviour is the learning
# goal (cash flow, Van Westendorp, backpropagation) keep exploration and consolidation.
PROFILE = {'risk': ['predict', 'observe', 'explain', 'practice', 'transfer'],
           'cashflow': ALL_PHASES, 'van_westendorp': ALL_PHASES, 'mlp': ALL_PHASES,
           'chord': ['predict', 'observe', 'explain', 'practice', 'transfer'], 'mdp': ALL_PHASES,
           'sequence': ALL_PHASES, 'cap_table': ALL_PHASES,
           'attention': ['predict', 'observe', 'explain', 'practice', 'transfer', 'summary'],
           'legal_check': ['predict', 'observe', 'explain', 'practice', 'transfer', 'summary']}

def _mdp(spec):
    from . import mdp as MDP
    return MDP.pedagogy(spec)


def _generic(spec):
    from .build import generic
    return generic(spec['model']['kind']).pedagogy(spec)


BUILD = {'cashflow': _cashflow, 'risk': _risk, 'van_westendorp': _vw, 'mlp': _mlp, 'chord': _chord, 'mdp': _mdp,
         'sequence': _generic, 'attention': _generic, 'cap_table': _generic, 'legal_check': _generic}


def add(spec):
    """Adds the learning sequence to a spec built by labs/build.py (idempotent)."""
    s = spec['sequence']
    if s.get('explore'):
        return spec
    p = BUILD[spec['model']['kind']](spec)
    s['predict']['explain_prompt'] = p['explain_prompt']
    s['predict']['explain_keys'] = p['explain_keys']
    s['phases'] = [ph for ph in PROFILE.get(spec['model']['kind'], ALL_PHASES) if ph != 'explore' or p['explore'] or spec['model']['kind'] not in ('sequence', 'cap_table')]
    s['explore'] = p['explore'] if 'explore' in s['phases'] else []
    s['takeaways'] = p['takeaways']
    s['summary_prompt'] = p['summary_prompt']
    for t in s['tasks']:
        if t['id'] == p['transfer_id']:
            t['transfer'] = True
    tr = [t for t in s['tasks'] if t.get('transfer')]
    s['tasks'] = [t for t in s['tasks'] if not t.get('transfer')] + [p['choice']] + tr
    spec['version'] = max(spec.get('version', 1), 2) if spec['model']['kind'] != 'risk' else max(spec.get('version', 1), 3)
    return spec
