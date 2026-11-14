"""Lab 'cap_table' (finance): funding rounds, option pool before or after the money, ownership per round, dilution and a
1x non-participating liquidation preference waterfall. Browser mirror: templates/em_labs.js (EM.models.cap*).

Conventions (stated in the lab):
- pool_pct is the size of the NEW option pool of a round as a share of the fully diluted shares after the round.
- 'pre': the pool is created before the investment (it is part of the pre-money; only existing holders are diluted;
  price = pre-money / (shares before + new pool)). 'post': created after the investment (dilutes everyone, investor too;
  price = pre-money / shares before).
- Shares are whole numbers (round half up). Pool options count as issued common stock in the waterfall (strike ignored).
- Waterfall: each preferred investor takes max(invested amount, pro-rata share as common); pari passu; if the exit does
  not cover all preferences they are paid in proportion to the invested amounts.
"""
import math

from . import build as B

DEFAULT = {'founders': [{'name': 'Gründerin A', 'shares': 600000}, {'name': 'Gründer B', 'shares': 400000}],
           'rounds': [{'name': 'Seed', 'pre_money': 4000000, 'investment': 1000000, 'pool_pct': 0.10, 'pool_mode': 'pre'},
                      {'name': 'Serie A', 'pre_money': 12000000, 'investment': 4000000, 'pool_pct': 0.05, 'pool_mode': 'pre'}],
           'exit': 60000000, 'unit': '€'}
POOL = 'Optionspool'


class CapError(B.LabError):
    pass


def rnd(x):
    return int(math.floor(x + 0.5))


def check_data(d):
    try:
        F = [{'name': str(f['name']), 'shares': int(f['shares'])} for f in d['founders']]
        R = [{'name': str(r['name']), 'pre_money': float(r['pre_money']), 'investment': float(r['investment']),
              'pool_pct': float(r.get('pool_pct', 0)), 'pool_mode': r.get('pool_mode', 'pre')} for r in d['rounds']]
    except (KeyError, TypeError, ValueError):
        raise CapError('cap_table braucht founders [{name, shares}] und rounds [{name, pre_money, investment, pool_pct, pool_mode}]')
    if not 1 <= len(F) <= 5 or any(f['shares'] <= 0 for f in F):
        raise CapError('1 bis 5 Gründer mit positiver Aktienzahl')
    if not 1 <= len(R) <= 4:
        raise CapError('1 bis 4 Finanzierungsrunden')
    names = [f['name'] for f in F] + [r['name'] for r in R] + [POOL]
    if len(set(names)) != len(names):
        raise CapError('Namen von Gründern und Runden müssen eindeutig sein')
    for r in R:
        if not (r['pre_money'] > 0 and r['investment'] > 0 and 0 <= r['pool_pct'] < 0.5 and r['pool_mode'] in ('pre', 'post')):
            raise CapError(f'Runde {r["name"]}: Bewertung und Investment > 0, Pool 0 bis 50 %, pool_mode pre oder post')
        if r['pool_mode'] == 'pre' and r['pool_pct'] * (r['pre_money'] + r['investment']) / r['pre_money'] >= 1:
            raise CapError(f'Runde {r["name"]}: Pool zu groß für die Pre-Money-Bewertung')
    return {'founders': F, 'rounds': R}


def rounds(d, mode=None):
    """Ownership after founding and after each round. mode overrides every round's pool_mode ('pre'/'post')."""
    held = {f['name']: f['shares'] for f in d['founders']}; held[POOL] = 0
    out = [{'name': 'Gründung', 'holders': dict(held), 'total': sum(held.values())}]
    for r in d['rounds']:
        S0 = sum(held.values()); pm = mode or r['pool_mode']; pct = r['pool_pct']; post = r['pre_money'] + r['investment']
        if pm == 'pre':
            q = post / r['pre_money']; P = rnd(pct * S0 * q / (1 - pct * q)); price = r['pre_money'] / (S0 + P); I = rnd(r['investment'] / price)
        else:
            price = r['pre_money'] / S0; I = rnd(r['investment'] / price); P = rnd(pct * (S0 + I) / (1 - pct))
        held[POOL] += P; held[r['name']] = I; T = S0 + P + I
        out.append({'name': r['name'], 'price': price, 'new_pool': P, 'inv_shares': I, 'total': T, 'pre_money': r['pre_money'],
                    'investment': r['investment'], 'post_money': post, 'post_effective': price * T, 'mode': pm, 'holders': dict(held)})
    for o in out:
        o['pct'] = {k: v / o['total'] for k, v in o['holders'].items()}
        o['founders_pct'] = sum(o['pct'][f['name']] for f in d['founders'])
    return out


def waterfall(d, last, exit_value, pref=True):
    """Payout per holder at an exit (cap table 'last' = rounds(...)[-1]). Returns {payout, pref_taken:[names]}."""
    H = last['holders']; inv = {r['name']: r['investment'] for r in d['rounds']}
    E = max(0.0, float(exit_value)); pay = {k: 0.0 for k in H}
    if not pref:
        T = sum(H.values())
        return {'payout': {k: E * v / T for k, v in H.items()}, 'pref_taken': []}
    takers = set()
    while True:
        prefs = sum(inv[k] for k in takers)
        if prefs >= E:
            takers = set(inv); prefs = sum(inv.values())
            for k in takers:
                pay[k] = E * inv[k] / prefs
            for k in H:
                if k not in takers:
                    pay[k] = 0.0
            break
        rest = E - prefs; common = {k: v for k, v in H.items() if k not in takers}; T = sum(common.values())
        new = {k for k in inv if k not in takers and rest * H[k] / T < inv[k] - 1e-9}
        if not new:
            for k in takers:
                pay[k] = inv[k]
            for k, v in common.items():
                pay[k] = rest * v / T
            break
        takers |= new
    return {'payout': pay, 'pref_taken': [r['name'] for r in d['rounds'] if r['name'] in takers]}


def _eur(x):
    return B._fmt(x, 0) + ' €'


def _price(x):
    """Price per share: 2 decimals, 4 only below 0,01 € (same rule as the browser view)."""
    return B._fmt(x, 2 if x >= 0.01 else 4) + ' €'


def _pc(x, d=1):
    return B._fmt(100 * x, d) + ' %'


def metrics(spec, params):
    d = spec['model']['cap']; mode = None if params.get('poolmode', 'data') == 'data' else params['poolmode']
    R = rounds(d, mode); k = min(2, len(R) - 1)
    w = waterfall(d, R[-1], float(params['exit']), params.get('pref', 'ja') == 'ja')
    return {'founders2': round(R[k]['founders_pct'], 9), 'prefTaken': len(w['pref_taken'])}


def _step(x):
    return 10 ** max(0, math.floor(math.log10(max(x, 1) / 100)))


def spec(lab_id, title, kc_ids, sources, data, course=''):
    data = dict(data or {})
    if 'rounds' not in data:
        data = {**DEFAULT, **data}
    d = check_data(data)
    R = rounds(d); post = R[-1]['post_money']; st = _step(post)
    exit0 = data.get('exit') or 4 * post; exit0 = max(st, round(float(exit0) / st) * st); hi = max(exit0, math.ceil(5 * post / st) * st)
    m = {'kind': 'cap_table', 'cap': d, 'unit': '€',
         'equations': ['Post-Money = Pre-Money + Investment;  Preis je Anteil = Pre-Money / (Anteile vor der Runde [+ neuer Pool, falls vor dem Geld])',
                       'neue Investorenanteile = Investment / Preis;  Anteil = eigene Anteile / alle Anteile (voll verwässert)',
                       'Pool vor dem Geld: P = p · S_0 · q / (1 − p · q) mit q = Post / Pre (verwässert nur Altgesellschafter)',
                       'Pool nach dem Geld: P = p · (S_0 + I) / (1 − p) (verwässert alle, auch den neuen Investor)',
                       '1x nicht-partizipierende Präferenz: Investor erhält max(Investment, Anteil · Rest-Erlös)']}
    params = [{'id': 'poolmode', 'label': 'Zeitpunkt des Optionspools', 'type': 'select', 'default': 'data',
               'options': [{'value': 'data', 'label': 'wie im Fall angegeben'}, {'value': 'pre', 'label': 'alle Pools vor dem Geld (pre-money)'},
                           {'value': 'post', 'label': 'alle Pools nach dem Geld (post-money)'}]},
              {'id': 'exit', 'label': 'Exit-Erlös (€)', 'type': 'range', 'min': 0, 'max': hi, 'step': st, 'default': exit0, 'digits': 0, 'unit': '€'},
              {'id': 'pref', 'label': '1x Liquidationspräferenz', 'type': 'select', 'default': 'ja',
               'options': [{'value': 'ja', 'label': 'ja, nicht partizipierend'}, {'value': 'nein', 'label': 'nein, alle pro rata'}]}]
    sp = {'schema': B.SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'finance', 'course': course, 'kc_ids': list(kc_ids),
          'model': m, 'params': params,
          'objective': 'Sie können aus Pre-Money-Bewertung, Investment und Optionspool den Preis je Anteil, die neuen Anteile und die '
                       'Beteiligungsquoten nach jeder Runde berechnen und erklären, wie Pool-Zeitpunkt und Liquidationspräferenz die Gründer treffen.',
          'prerequisites': ['Prozentrechnung', 'Begriffe Pre-Money, Post-Money, Anteil (Share)'],
          'assumptions': ['Voll verwässerte Betrachtung: Der Optionspool zählt wie ausgegebene Anteile; der Ausübungspreis der Optionen wird ignoriert.',
                          'Der Pool-Prozentsatz einer Runde ist die Größe des NEUEN Pools in Prozent aller Anteile nach der Runde.',
                          'Anteile sind ganze Zahlen (kaufmännisch gerundet); Prozente sind auf eine Nachkommastelle gerundet.',
                          'Präferenzen aller Runden sind gleichrangig (pari passu), 1x, nicht partizipierend; keine Zinsen, keine Wandelanleihen.'],
          'sources': list(sources) + ['Referenzmodell: exam_mastery/labs/cap_table.py',
                                      'Feld & Mendelson (2019), Venture Deals, Kap. 4–5 (Bewertung, Optionspool, Liquidationspräferenz)'],
          'explanations': ['Ein Pool vor dem Geld senkt den Preis je Anteil: Die Pre-Money-Bewertung verteilt sich auf mehr Anteile, die Verwässerung tragen allein die Altgesellschafter.',
                           'Bei niedrigen Exits nimmt ein Investor seine Präferenz statt der Wandlung; dann fällt für die Stammanteile überproportional wenig ab.']}
    sq = _sequence(sp, d, R, exit0, st); sq['_explore'] = sq.pop('explore'); sq['_choice'] = sq.pop('choice')
    sp['sequence'] = sq
    sp['tests'] = [{'params': {p['id']: p['default'] for p in params}, 'founders_pct': [o['founders_pct'] for o in R], 'price': [o.get('price') for o in R]}]
    return sp


def _sequence(sp, d, R, exit0, st):
    k = min(2, len(R) - 1); fk = R[k]['founders_pct']; r1 = R[1]; tol = 0.006
    naive1 = r1['pre_money'] / (R[0]['total'])
    t1 = {'id': 'price', 'title': f'Preis je Anteil in der Runde {r1["name"]}',
          'prompt': f'Vor der Runde {r1["name"]} gibt es {B._fmt(R[0]["total"], 0)} Anteile. Pre-Money {_eur(r1["pre_money"])}, Investment {_eur(r1["investment"])}, '
                    f'neuer Optionspool {_pc(d["rounds"][0]["pool_pct"], 0)} nach der Runde, gebildet {"vor" if r1["mode"] == "pre" else "nach"} dem Geld '
                    f'(= {B._fmt(r1["new_pool"], 0)} Anteile). Wie hoch ist der Preis je Anteil (€, 2 Nachkommastellen)?',
          'expected': round(r1['price'], 6), 'tolerance': tol, 'unit': '€',
          'errors': _distinct(r1['price'], [(naive1, 'So wäre es ohne Pool vor dem Geld. Der neue Pool gehört hier zur Pre-Money-Bewertung und erhöht die Zahl der Anteile.'),
                                            (r1['post_money'] / R[0]['total'], 'Der Preis ergibt sich aus der Pre-Money-, nicht aus der Post-Money-Bewertung.')], tol),
          'hints': ['Preis = Pre-Money / Anteile vor dem Geld.', 'Bei einem Pool vor dem Geld zählen die neuen Pool-Anteile zu den Anteilen vor dem Geld.'],
          'solution': [f'{_eur(r1["pre_money"])} / {B._fmt(r1["total"] - r1["inv_shares"] if r1["mode"] == "pre" else R[0]["total"], 0)} = {_price(r1["price"])}.'],
          'feedback_correct': 'Richtig.'}
    naive = 1.0
    for o in R[1:k + 1]:
        naive *= 1 - o['investment'] / o['post_money']
    t2 = {'id': 'founders', 'title': f'Gründeranteil nach {R[k]["name"]}',
          'prompt': f'Welchen Anteil halten alle Gründer zusammen nach der Runde {R[k]["name"]} (in %, 1 Nachkommastelle)? Nutzen Sie die Anteile der Tabelle bis zur Vorrunde.',
          'expected': round(100 * fk, 6), 'tolerance': 0.06, 'unit': '%',
          'errors': _distinct(100 * fk, [(100 * naive, 'Das ist das Produkt (1 − Investment/Post) über die Runden: Die Optionspools fehlen.'),
                                          (100 * R[k - 1]['founders_pct'], 'Das ist der Anteil vor dieser Runde.')], 0.06),
          'hints': ['Gründeranteile ändern sich nicht – nur die Gesamtzahl der Anteile wächst.', f'Gesamtzahl nach {R[k]["name"]}: {B._fmt(R[k]["total"], 0)} Anteile.'],
          'solution': [f'{B._fmt(sum(f["shares"] for f in d["founders"]), 0)} / {B._fmt(R[k]["total"], 0)} = {_pc(fk, 2)}.'],
          'feedback_correct': 'Richtig: Verwässerung heißt, der Kuchen wächst, das eigene Stück bleibt gleich groß.'}
    # transfer: payout of the first founder at a low exit where a preference bites
    last = R[-1]; inv_tot = sum(r['investment'] for r in d['rounds']); f0 = d['founders'][0]['name']
    ex_t = next((x for x in (round(inv_tot * f / st) * st for f in (1.5, 2, 2.5, 1.2, 3, 1.1)) if x > 0 and waterfall(d, last, x)['pref_taken']), None)
    if ex_t is None:
        raise CapError('kein Exit-Wert, bei dem eine Präferenz greift; Daten prüfen')
    w = waterfall(d, last, ex_t); wp = waterfall(d, last, ex_t, False)
    t3 = {'id': 'exit', 'title': 'Transfer: Exit mit Liquidationspräferenz',
          'prompt': f'Exit zu {_eur(ex_t)} mit 1x nicht-partizipierender Präferenz für alle Investoren. Wie viel erhält {f0} (in €, auf ganze Euro)?',
          'expected': round(w['payout'][f0], 2), 'tolerance': max(1.0, 0.0005 * w['payout'][f0]), 'unit': '€',
          'errors': _distinct(w['payout'][f0], [(wp['payout'][f0], 'Das ist die Pro-rata-Verteilung ohne Präferenz. Prüfen Sie für jeden Investor: Präferenz oder Wandlung?')], max(1.0, 0.0005 * w['payout'][f0])),
          'hints': ['Jeder Investor vergleicht sein Investment mit seinem Pro-rata-Anteil am Erlös.',
                    f'Hier nehmen die Präferenz: {", ".join(w["pref_taken"])}. Der Rest wird unter den übrigen Anteilen pro rata verteilt.'],
          'solution': [f'Präferenz: {", ".join(f"{n} {_eur(w["payout"][n])}" for n in w["pref_taken"])}; Rest pro rata: {f0} erhält {_eur(w["payout"][f0])} (ohne Präferenz {_eur(wp["payout"][f0])}).'],
          'feedback_correct': 'Richtig: Bei niedrigen Exits verschiebt die Präferenz Erlös von den Stammanteilen zu den Investoren.'}
    choice = {'id': 'pool', 'type': 'choice', 'title': 'Wer trägt den Pool?',
              'prompt': 'Ein Investor verlangt, dass der neue Optionspool vor dem Geld (in der Pre-Money-Bewertung) gebildet wird. Wen verwässert der Pool?',
              'options': [{'value': 'old', 'label': 'Nur die bisherigen Gesellschafter; der Investor erhält seinen vollen Anteil Investment / Post-Money.', 'feedback': ''},
                          {'value': 'all', 'label': 'Alle gleichmäßig, auch den neuen Investor.', 'feedback': 'Das gilt für einen Pool nach dem Geld. Vor dem Geld ist er schon im Preis je Anteil enthalten.'},
                          {'value': 'inv', 'label': 'Nur den Investor.', 'feedback': 'Der Investor zahlt einen niedrigeren Preis je Anteil; die Verwässerung landet bei den Altgesellschaftern.'},
                          {'value': 'none', 'label': 'Niemanden, Optionen sind noch keine Anteile.', 'feedback': 'In der voll verwässerten Betrachtung zählen Optionen wie Anteile – genau so rechnen Investoren.'}],
              'correct': 'old', 'explanation': 'Die effektive Pre-Money-Bewertung für die Altgesellschafter sinkt um den Wert des Pools („Option Pool Shuffle“).'}
    lo = math.floor(100 * fk / 10) * 10
    predict = {'question': f'Schätzen Sie: Welchen Anteil halten die Gründer zusammen nach der Runde {R[k]["name"]}?',
               'options': [{'value': 'a', 'label': f'unter {lo - 10} %'}, {'value': 'b', 'label': f'{lo - 10} bis unter {lo} %'},
                           {'value': 'c', 'label': f'{lo} bis unter {lo + 10} %'}, {'value': 'd', 'label': f'{lo + 10} % oder mehr'}],
               'correct': 'c', 'change': [{'param': 'poolmode', 'to': 'data'}],
               'result_text': f'Zutreffend ist der Bereich {lo} bis unter {lo + 10} %. Den genauen Anteil berechnen Sie in der Simulation selbst.',
               'explanation': 'Jede Runde multipliziert den Gründeranteil mit (1 − neue Anteile / alle Anteile danach); die Optionspools kommen zu den Investorenanteilen hinzu.'}
    ex = []
    if ex_t != exit0 and not waterfall(d, last, exit0)['pref_taken']:
        ex.append({'id': 'pref', 'title': 'Wann greift die Präferenz?',
                   'prompt': 'Verringern Sie den Exit-Erlös, bis mindestens ein Investor seine Präferenz statt der Wandlung wählt.',
                   'hint': 'Ein Investor nimmt die Präferenz, sobald sein Pro-rata-Anteil unter sein Investment fällt.',
                   'success': 'Unterhalb dieser Schwelle verdient der Investor mit der Präferenz mehr als mit der Wandlung – die Gründer erhalten weniger als ihren Anteil.',
                   'cond': [{'m': 'prefTaken', 'op': '>', 'v': 0}, {'p': 'pref', 'op': '==', 'v': 'ja'}], 'witness': {'exit': ex_t}})
    for mode in ('post', 'pre'):
        f2 = rounds(d, mode)[k]['founders_pct']
        if f2 > fk + 1e-4:
            ex.append({'id': 'pooltime', 'title': 'Pool-Zeitpunkt verhandeln',
                       'prompt': f'Ändern Sie nur den Zeitpunkt der Optionspools so, dass die Gründer nach {R[k]["name"]} mehr behalten.',
                       'hint': 'Vergleichen Sie „vor dem Geld“ und „nach dem Geld“.',
                       'success': f'{_pc(f2)} statt {_pc(fk)}: Ein Pool nach dem Geld verwässert auch den Investor.',
                       'cond': [{'m': 'founders2', 'op': '>', 'v': round(fk + 1e-5, 9)}], 'witness': {'poolmode': mode}})
            break
    return {'predict': predict, 'tasks': [t1, t2, t3], 'explore': ex, 'choice': choice}


def _distinct(expected, cands, tol):
    out, seen = [], [expected]
    for v, msg in cands:
        if v is None or not math.isfinite(v) or any(abs(v - w) <= 2 * tol for w in seen):
            continue
        out.append({'value': round(v, 6), 'message': msg}); seen.append(v)
    return out


def pedagogy(spec):
    s = spec['sequence']
    return {'explain_prompt': 'Erklären Sie, warum der Gründeranteil so stark (oder so wenig) gesunken ist.',
            'explain_keys': [{'label': 'neue Anteile, nicht weniger eigene Anteile', 'terms': ['neue anteile', 'mehr anteile', 'gesamtzahl', 'kuchen']},
                             {'label': 'Investment / Post-Money je Runde', 'terms': ['post', 'investment', 'bewertung']},
                             {'label': 'Optionspool verwässert zusätzlich', 'terms': ['pool', 'option']}],
            'explore': s.pop('_explore', []), 'choice': s.pop('_choice'),
            'takeaways': ['Preis je Anteil = Pre-Money / Anteile vor dem Geld; neue Anteile = Investment / Preis.',
                          'Verwässerung: Die eigene Anteilszahl bleibt, die Gesamtzahl wächst; der Pool vor dem Geld geht ganz zulasten der Altgesellschafter.',
                          'Eine 1x nicht-partizipierende Präferenz zählt nur bei niedrigen Exits: Dann nimmt der Investor sein Geld zurück statt seines Anteils.'],
            'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie eine Finanzierungsrunde die Anteile der Gründer verändert.',
            'transfer_id': 'exit'}


def check(spec):
    m = spec['model']; ex = next(p for p in spec['params'] if p['id'] == 'exit')['default']
    ref = B.cap_table_spec(spec['id'], spec['title'], spec['kc_ids'], [], {**m['cap'], 'exit': ex})
    strip = lambda ts: [{k: v for k, v in t.items() if k != 'transfer'} for t in ts]
    if strip(spec['sequence']['tasks']) != strip(ref['sequence']['tasks']) or spec['sequence']['predict'] != ref['sequence']['predict']:
        raise CapError('Cap-Table-Lab: Aufgaben oder Vorhersage weichen vom Referenzmodell ab')
    R = rounds(m['cap'])
    for case in spec.get('tests') or []:
        if any(abs(a - b) > 1e-12 for a, b in zip(case['founders_pct'], [o['founders_pct'] for o in R])):
            raise CapError('Cap-Table-Lab: Testfall stimmt nicht')


def static_svg(spec):
    """Funding timeline with the inputs of every round (no ownership results: those are the learner's to compute)."""
    d = spec['model']['cap']; n = len(d['rounds']) + 1; W = 640; cw = (W - 40) / n; H = 230
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Finanzierungsrunden mit Eingangsdaten">'
         '<title>Cap Table: Gründung und Finanzierungsrunden mit Bewertung, Investment und Optionspool</title>',
         f'<line x1="30" x2="{W - 30}" y1="60" y2="60" stroke="#1f5f8b" stroke-width="3"/>']
    cols = [('Gründung', [f'{B.E(f["name"])}: {B._fmt(f["shares"], 0)} Anteile' for f in d['founders']])]
    for r in d['rounds']:
        cols.append((r['name'], [f'Pre-Money {_eur(r["pre_money"])}', f'Investment {_eur(r["investment"])}',
                                 f'neuer Pool {_pc(r["pool_pct"], 0)} ({"vor" if r["pool_mode"] == "pre" else "nach"} dem Geld)']))
    for i, (name, lines) in enumerate(cols):
        x = 20 + cw * i + cw / 2
        s.append(f'<circle cx="{x:.1f}" cy="60" r="9" fill="{"#1f5f8b" if i else "#e0b04b"}"/>'
                 f'<text x="{x:.1f}" y="36" text-anchor="middle" font-size="14" font-weight="700" fill="#223">{B.E(name)}</text>')
        for k, t in enumerate(lines):
            s.append(f'<text x="{x:.1f}" y="{92 + 20 * k}" text-anchor="middle" font-size="{11 if n > 3 else 12}" fill="#223">{t}</text>')
    s.append(f'<text x="20" y="{H - 12}" font-size="11" fill="#5b6876">Voll verwässert; Anteile nach jeder Runde berechnen Sie im Lab selbst.</text></svg>')
    return ''.join(s)
