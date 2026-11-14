"""Lab 'legal_check' (law): a generic Prüfungsschema. The spec lists the elements (Tatbestandsmerkmale / Prüfungspunkte)
in their order of examination, each with norm, definition, a reference decision (erfüllt / nicht erfüllt / problematisch
plus the outcome of the discussion) and justification options with exactly one correct one. The lab is deterministic:
it never judges free text; it checks the learner's choices against the reference, enforces the order (Gutachtenstil:
one element after the other) and derives the overall result (all elements -> Rechtsfolge; the first element that is
not met ends the examination). Browser mirror: templates/em_labs.js (EM.models.legal*).
"""
from . import build as B

DECISIONS = ('erfuellt', 'nicht_erfuellt', 'problematisch')
LABEL = {'erfuellt': 'erfüllt', 'nicht_erfuellt': 'nicht erfüllt', 'problematisch': 'problematisch (ausführlich erörtern)'}

DEFAULT = {
    'scheme': 'Patentfähigkeit einer Erfindung (EPÜ)', 'norm': 'Art. 52–57 EPÜ',
    'question': 'Ist die Erfindung von K patentfähig?',
    'rechtsfolge': 'Die Erfindung ist patentfähig (Art. 52 Abs. 1 EPÜ); ein europäisches Patent kann erteilt werden.',
    'negative': 'Die Erfindung ist nicht patentfähig; ein Patent kann nicht erteilt werden.',
    'case': {'title': 'Fall „Notruf-Helm“', 'self_designed': True,
             'facts': ['Die Ingenieurin K entwickelt einen Fahrradhelm mit Beschleunigungssensor. Erkennt der Sensor einen Sturz, setzt der Helm über das gekoppelte Smartphone automatisch einen Notruf mit dem Standort ab.',
                       'K hält die Entwicklung geheim und reicht am 1. März 2026 eine europäische Patentanmeldung ein.',
                       'Stand der Technik: D1 (Fachaufsatz 2023) beschreibt einen Motorradhelm mit Sturzsensor, der nach einem Sturz eine Warnleuchte einschaltet. '
                       'D2 (Patentschrift 2022) beschreibt eine Smartwatch, die nach einem erkannten Sturz automatisch einen Notruf mit Standort sendet.',
                       'Fahrradhelme werden industriell in Serie gefertigt.']},
    'elements': [
        {'id': 'erfindung', 'label': 'Erfindung auf einem Gebiet der Technik', 'norm': 'Art. 52 Abs. 1 EPÜ',
         'definition': 'Erfindung ist eine Lehre zum technischen Handeln: Sie löst eine Aufgabe mit technischen Mitteln (technischer Charakter).',
         'decision': 'erfuellt', 'explanation': 'Der Helm ist ein Gegenstand mit Sensor und Funkverbindung; technische Mittel lösen die technische Aufgabe, einen Sturz zu erkennen und zu melden.',
         'reasons': [{'id': 'r1', 'text': 'Erfüllt: ein Gegenstand, bei dem technische Mittel (Sensor, Funk) eine technische Aufgabe lösen.', 'correct': True},
                     {'id': 'r2', 'text': 'Erfüllt, weil die Idee nützlich ist und Leben retten kann.', 'feedback': 'Nützlichkeit ist kein Merkmal der Erfindung; maßgeblich ist der technische Charakter.'},
                     {'id': 'r3', 'text': 'Nicht erfüllt, weil Software für die Sturzerkennung beteiligt ist.', 'feedback': 'Programme sind nur „als solche“ ausgeschlossen (Art. 52 Abs. 2, 3 EPÜ); ein Helm mit Sensor hat technischen Charakter.'}]},
        {'id': 'ausschluss', 'label': 'Kein Ausschluss von der Patentierbarkeit', 'norm': 'Art. 52 Abs. 2, 3, Art. 53 EPÜ',
         'definition': 'Ausgeschlossen sind u. a. Entdeckungen, mathematische Methoden, Programme und geschäftliche Methoden als solche sowie die Fälle des Art. 53 (z. B. Verstoß gegen die öffentliche Ordnung, medizinische Verfahren am Körper).',
         'decision': 'erfuellt', 'explanation': 'Beansprucht wird ein Erzeugnis, kein Verfahren am menschlichen Körper und kein Gegenstand „als solcher“ der Ausschlussliste.',
         'reasons': [{'id': 'r1', 'text': 'Kein Ausschluss: beansprucht ist ein technisches Erzeugnis, keine der Kategorien des Art. 52 Abs. 2 oder Art. 53.', 'correct': True},
                     {'id': 'r2', 'text': 'Ausgeschlossen als Diagnostizierverfahren, weil ein Sturz erkannt wird.', 'feedback': 'Art. 53 lit. c erfasst Diagnostizierverfahren am menschlichen Körper, nicht ein Erzeugnis, das einen Sturz meldet.'},
                     {'id': 'r3', 'text': 'Ausgeschlossen als geschäftliche Methode, weil K den Helm verkaufen will.', 'feedback': 'Die Verkaufsabsicht macht aus einem technischen Gegenstand keine geschäftliche Methode.'}]},
        {'id': 'neuheit', 'label': 'Neuheit', 'norm': 'Art. 54 EPÜ',
         'definition': 'Neu ist, was nicht zum Stand der Technik gehört; das ist alles, was vor dem Anmeldetag der Öffentlichkeit zugänglich gemacht wurde. Verglichen wird mit jeder Entgegenhaltung einzeln.',
         'decision': 'problematisch', 'resolution': 'erfuellt',
         'explanation': 'D1 zeigt den Helm mit Sturzsensor, aber keinen Notruf; D2 zeigt den automatischen Notruf, aber keinen Helm. Keine einzelne Entgegenhaltung offenbart alle Merkmale: neu.',
         'reasons': [{'id': 'r1', 'text': 'Neu: keine einzelne Entgegenhaltung zeigt Helm, Sturzerkennung und automatischen Notruf mit Standort zusammen.', 'correct': True},
                     {'id': 'r2', 'text': 'Nicht neu, weil D1 und D2 zusammen alle Merkmale zeigen.', 'feedback': 'Bei der Neuheit ist eine Mosaikbetrachtung unzulässig; das Kombinieren von Entgegenhaltungen gehört zur erfinderischen Tätigkeit.'},
                     {'id': 'r3', 'text': 'Neu, weil K ihre Entwicklung geheim gehalten hat.', 'feedback': 'Die Geheimhaltung verhindert nur eigene Vorveröffentlichungen; sie sagt nichts über den Stand der Technik aus D1 und D2.'}]},
        {'id': 'erfinderisch', 'label': 'Erfinderische Tätigkeit', 'norm': 'Art. 56 EPÜ',
         'definition': 'Eine Erfindung beruht auf erfinderischer Tätigkeit, wenn sie sich für den Fachmann nicht in naheliegender Weise aus dem Stand der Technik ergibt (Aufgabe-Lösungs-Ansatz: nächstliegender Stand der Technik, objektive Aufgabe, naheliegend?).',
         'decision': 'problematisch', 'resolution': 'nicht_erfuellt',
         'explanation': 'Nächstliegender Stand der Technik ist D1. Objektive Aufgabe: nach einem Sturz Hilfe herbeirufen. D2 lehrt genau diese Lösung für ein am Körper getragenes Gerät; der Fachmann hätte sie ohne Weiteres auf den Helm übertragen. Naheliegend: nicht erfinderisch.',
         'reasons': [{'id': 'r1', 'text': 'Erfinderisch, weil keine Entgegenhaltung alle Merkmale zusammen zeigt.', 'feedback': 'Das ist das Kriterium der Neuheit. Hier ist zu fragen, ob die Kombination von D1 und D2 für den Fachmann naheliegt.'},
                     {'id': 'r2', 'text': 'Nicht erfinderisch: Ausgehend von D1 ist die Aufgabe „Hilfe nach Sturz“; D2 lehrt die Lösung, der Fachmann hätte sie übertragen.', 'correct': True},
                     {'id': 'r3', 'text': 'Erfinderisch, weil der Helm voraussichtlich ein großer Markterfolg wird.', 'feedback': 'Kommerzieller Erfolg ist allenfalls ein Hilfsindiz und ersetzt nicht die Prüfung, ob die Lösung naheliegt.'}]},
        {'id': 'gewerblich', 'label': 'Gewerbliche Anwendbarkeit', 'norm': 'Art. 57 EPÜ',
         'definition': 'Gewerblich anwendbar ist eine Erfindung, wenn ihr Gegenstand auf irgendeinem gewerblichen Gebiet hergestellt oder benutzt werden kann.',
         'decision': 'erfuellt', 'explanation': 'Helme werden industriell gefertigt.',
         'reasons': [{'id': 'r1', 'text': 'Erfüllt: Der Helm kann industriell hergestellt werden.', 'correct': True},
                     {'id': 'r2', 'text': 'Nicht erfüllt, weil Privatleute den Helm benutzen.', 'feedback': 'Es genügt, dass der Gegenstand gewerblich hergestellt werden kann.'}]}],
    'transfer': {'prompt': 'Abwandlung: K hat den Helm mit allen Merkmalen drei Monate vor der Anmeldung in ihrem öffentlich zugänglichen Blog beschrieben. An welchem Prüfungspunkt scheitert die Patentfähigkeit jetzt zuerst?',
                 'options': [{'value': 'neuheit', 'label': 'Neuheit (Art. 54 EPÜ)', 'feedback': ''},
                             {'value': 'erfinderisch', 'label': 'Erst an der erfinderischen Tätigkeit', 'feedback': 'Schon die Neuheit fehlt: Der Blogbeitrag ist vor dem Anmeldetag öffentlich und zeigt alle Merkmale. Das EPÜ kennt keine allgemeine Neuheitsschonfrist für eigene Veröffentlichungen.'},
                             {'value': 'keiner', 'label': 'Nirgends: Eigene Veröffentlichungen schaden nicht.', 'feedback': 'Auch eigene Veröffentlichungen gehören zum Stand der Technik (Art. 55 EPÜ erfasst nur Missbrauch und bestimmte Ausstellungen).'}],
                 'correct': 'neuheit', 'explanation': 'Stand der Technik ist alles vor dem Anmeldetag öffentlich Zugängliche – auch die eigene Veröffentlichung.'}}


class LegalError(B.LabError):
    pass


def check_data(d):
    try:
        els = d['elements']; q = str(d['question']); rf = str(d['rechtsfolge']); case = d['case']; facts = [str(x) for x in case['facts']]
    except (KeyError, TypeError):
        raise LegalError('legal_check braucht question, rechtsfolge, case.facts und elements')
    if not 2 <= len(els) <= 10 or not facts:
        raise LegalError('2 bis 10 Prüfungspunkte und mindestens eine Sachverhaltsangabe')
    ids = [e.get('id') for e in els]
    if len(set(ids)) != len(ids) or any(not i for i in ids):
        raise LegalError('Prüfungspunkte brauchen eindeutige ids')
    for e in els:
        if e.get('decision') not in DECISIONS or not e.get('label') or not e.get('definition') or not e.get('explanation'):
            raise LegalError(f'Prüfungspunkt {e["id"]}: label, definition, explanation und decision (erfuellt/nicht_erfuellt/problematisch) nötig')
        if e['decision'] == 'problematisch' and e.get('resolution') not in ('erfuellt', 'nicht_erfuellt'):
            raise LegalError(f'Prüfungspunkt {e["id"]}: problematisch braucht resolution erfuellt oder nicht_erfuellt')
        rs = e.get('reasons') or []
        if not 2 <= len(rs) <= 5 or sum(1 for r in rs if r.get('correct')) != 1 or len({r.get('id') for r in rs}) != len(rs):
            raise LegalError(f'Prüfungspunkt {e["id"]}: 2 bis 5 Begründungen mit eindeutiger id, genau eine richtig')
        if any(not r.get('correct') and not r.get('feedback') for r in rs):
            raise LegalError(f'Prüfungspunkt {e["id"]}: jede falsche Begründung braucht eine Rückmeldung')
    return d


def outcome(e):
    return e['resolution'] if e['decision'] == 'problematisch' else e['decision']


def result(elements):
    """Reference result: Rechtsfolge iff every element is met; the first element not met ends the examination."""
    for i, e in enumerate(elements):
        if outcome(e) == 'nicht_erfuellt':
            return {'positive': False, 'stop': e['id'], 'checked': [x['id'] for x in elements[:i + 1]]}
    return {'positive': True, 'stop': None, 'checked': [x['id'] for x in elements]}


def progress(elements, committed):
    """Consistency of the learner's path: committed ids must follow the order of the scheme (no skipping); after the
    stopping element nothing more is required. Returns {'next': id|None, 'done': bool}; raises on a wrong order."""
    ids = [e['id'] for e in elements]
    if list(committed) != ids[:len(committed)]:
        raise LegalError('Reihenfolge: Prüfungspunkte werden in der Reihenfolge des Schemas entschieden')
    need = result(elements)['checked']
    done = len(committed) >= len(need)
    return {'next': None if done else ids[len(committed)], 'done': done}


def grade(e, decision, reason):
    """'correct' | 'partial' (result right, but the element should have been discussed as problematic, or vice versa) | 'wrong'."""
    r = next((x for x in e['reasons'] if x['id'] == reason), None)
    if decision not in DECISIONS or r is None:
        raise LegalError('Entscheidung und Begründung wählen')
    ok_r = bool(r.get('correct'))
    if decision == e['decision']:
        return 'correct' if ok_r else 'partial'
    if outcome(e) == decision or (decision == 'problematisch' and e['decision'] != 'problematisch'):
        return 'partial' if ok_r else 'wrong'
    return 'wrong'


def spec(lab_id, title, kc_ids, sources, data, course=''):
    data = dict(data or {})
    if 'elements' not in data:
        data = {**DEFAULT, **data}
    d = check_data(data); els = d['elements']; res = result(els)
    self_made = bool(d['case'].get('self_designed'))
    m = {'kind': 'legal_check', 'scheme': d.get('scheme', 'Prüfungsschema'), 'norm': d.get('norm', ''), 'question': d['question'],
         'rechtsfolge': d['rechtsfolge'], 'negative': d.get('negative', 'Die Rechtsfolge tritt nicht ein.'), 'case': d['case'], 'elements': els,
         'equations': ['Rechtsfolge  ⇔  Merkmal 1 ∧ Merkmal 2 ∧ … ∧ Merkmal n  (Prüfung in dieser Reihenfolge)',
                       'Gutachtenstil je Merkmal: Obersatz → Definition → Subsumtion unter den Sachverhalt → Ergebnis',
                       'Das erste nicht erfüllte Merkmal beendet die Prüfung (weitere Punkte allenfalls hilfsgutachtlich)']}
    params = [{'id': 'hilfs', 'label': 'Nach dem ersten nicht erfüllten Merkmal', 'type': 'select', 'default': 'nein',
               'options': [{'value': 'nein', 'label': 'Prüfung beenden'}, {'value': 'ja', 'label': 'hilfsgutachtlich weiterprüfen'}]}]
    sp = {'schema': B.SCHEMA, 'id': lab_id, 'version': 1, 'title': title, 'domain': 'law', 'course': course, 'kc_ids': list(kc_ids),
          'model': m, 'params': params,
          'objective': f'Sie können einen Fall nach dem Schema „{m["scheme"]}“ Merkmal für Merkmal im Gutachtenstil prüfen, '
                       'problematische Punkte erkennen, jede Entscheidung mit dem Sachverhalt begründen und das Gesamtergebnis ableiten.',
          'prerequisites': [f'Normen: {m["norm"]}' if m['norm'] else 'die einschlägigen Normen', 'Gutachtenstil (Obersatz, Definition, Subsumtion, Ergebnis)'],
          'assumptions': (['Der Fall ist selbst konstruiert (Übungsfall, keine reale Entscheidung) und bewusst vereinfacht.'] if self_made else ['Der Fall stammt aus den angegebenen Quellen.'])
                         + ['Referenzentscheidungen und Begründungen sind im Lab hinterlegt; das Lab bewertet keine Freitexte und ersetzt keine Rechtsberatung.',
                            '„Problematisch“ heißt: Hier liegt ein Schwerpunkt, der im Gutachten ausführlich zu erörtern ist; das Lab nennt danach das Ergebnis der Erörterung.'],
          'sources': list(sources) + ['Referenzmodell: exam_mastery/labs/legal_check.py'] + (['Fall: selbst konstruiert (fiktiv)'] if self_made else []),
          'explanations': ['Ein Merkmal nach dem anderen: Erst wenn ein Merkmal entschieden und begründet ist, folgt das nächste. Das erste nicht erfüllte Merkmal entscheidet das Ergebnis.']}
    sq = _sequence(sp, d, res); sq['_choice'] = sq.pop('choice')
    sp['sequence'] = sq
    sp['tests'] = [{'params': {'hilfs': 'nein'}, 'positive': res['positive'], 'stop': res['stop']}]
    return sp


def _sequence(sp, d, res):
    els = d['elements']; byid = {e['id']: e for e in els}; pos = res['positive']
    stop_i = len(res['checked']) - 1
    opts = []
    for i, e in enumerate(els):
        if e['id'] == res['stop']:
            fb = ''
        elif i < stop_i or pos:
            fb = f'{e["label"]} ist erfüllt: {e["explanation"]}'
        else:
            fb = 'Dieser Punkt wird nicht mehr erreicht: Die Prüfung endet beim ersten nicht erfüllten Merkmal.'
        opts.append({'value': e['id'], 'label': f'Sie scheitert an: {e["label"]}', 'feedback': fb})
    stop_e = byid.get(res['stop'])
    opts.append({'value': '__all', 'label': 'Alle Merkmale sind erfüllt; die Rechtsfolge tritt ein.',
                 'feedback': '' if pos else f'{stop_e["label"]} ist nicht erfüllt: {stop_e["explanation"]}'})
    t_res = {'id': 'result', 'type': 'choice', 'title': 'Gesamtergebnis',
             'prompt': f'{d["question"]} Wählen Sie das Ergebnis der Prüfung.', 'options': opts, 'correct': '__all' if pos else res['stop'],
             'explanation': (d['rechtsfolge'] if pos else f'{d.get("negative", "Die Rechtsfolge tritt nicht ein.")} Grund: {stop_e["explanation"]}')}
    style = {'id': 'style', 'type': 'choice', 'title': 'Gutachtenstil',
             'prompt': 'In welcher Reihenfolge prüfen Sie ein einzelnes Merkmal im Gutachtenstil?',
             'options': [{'value': 'g', 'label': 'Obersatz (Frage) → Definition → Subsumtion unter den Sachverhalt → Ergebnis', 'feedback': ''},
                         {'value': 'u', 'label': 'Ergebnis → Definition → Subsumtion', 'feedback': 'Das ist der Urteilsstil: Er stellt das Ergebnis voran und passt für Entscheidungen, nicht für die Falllösung.'},
                         {'value': 's', 'label': 'Sachverhalt nacherzählen → Ergebnis', 'feedback': 'Ohne Definition fehlt der Maßstab, an dem der Sachverhalt gemessen wird.'},
                         {'value': 'n', 'label': 'Norm zitieren → Ergebnis', 'feedback': 'Die Norm allein entscheidet nichts; erst die Subsumtion des Sachverhalts unter die Definition trägt das Ergebnis.'}],
             'correct': 'g', 'explanation': 'Unproblematische Merkmale dürfen kurz festgestellt werden; problematische werden in allen vier Schritten ausführlich erörtert.'}
    tr = d.get('transfer')
    if tr:
        transfer = {'id': 'transfer', 'type': 'choice', 'title': 'Transfer: Abwandlung des Falls', 'prompt': tr['prompt'],
                    'options': tr['options'], 'correct': tr['correct'], 'explanation': tr.get('explanation', '')}
    else:
        first = els[0]
        transfer = {'id': 'transfer', 'type': 'choice', 'title': 'Transfer: Abwandlung des Falls',
                    'prompt': f'Abwandlung: Der Sachverhalt wird so geändert, dass „{first["label"]}“ nicht erfüllt ist. Was folgt für die Prüfung?',
                    'options': [{'value': 'stop', 'label': 'Die Prüfung endet dort; die Rechtsfolge tritt nicht ein.', 'feedback': ''},
                                {'value': 'rest', 'label': 'Man prüft alle weiteren Merkmale und wägt ab.', 'feedback': 'Die Merkmale sind kumulativ: Fehlt eines, kann keine Abwägung die Rechtsfolge retten.'},
                                {'value': 'same', 'label': 'Nichts, die anderen Merkmale tragen das Ergebnis.', 'feedback': 'Jedes Merkmal ist notwendig; schon eines, das fehlt, schließt die Rechtsfolge aus.'}],
                    'correct': 'stop', 'explanation': 'Alle Merkmale müssen kumulativ vorliegen; das erste fehlende beendet die Prüfung.'}
    for o in transfer['options']:
        if o['value'] != transfer['correct'] and not o.get('feedback'):
            raise LegalError('Transfer: jede falsche Option braucht eine Rückmeldung')
    predict = {'question': f'{d["question"]} Ihre erste Einschätzung nach dem Lesen des Sachverhalts:',
               'options': [{'value': 'ja', 'label': 'Ja – die Rechtsfolge tritt ein.'}, {'value': 'nein', 'label': 'Nein – mindestens ein Merkmal fehlt.'}],
               'correct': 'ja' if pos else 'nein', 'change': [{'param': 'hilfs', 'to': 'nein'}],
               'result_text': 'Prüfen Sie jetzt Merkmal für Merkmal; das Gesamtergebnis erscheint erst, wenn alle nötigen Punkte entschieden sind.',
               'explanation': 'Das Ergebnis folgt aus den Merkmalen in ihrer Reihenfolge: Sind alle erfüllt, tritt die Rechtsfolge ein; das erste nicht erfüllte Merkmal beendet die Prüfung.'}
    return {'predict': predict, 'tasks': [t_res, transfer], 'choice': style}


def pedagogy(spec):
    return {'explain_prompt': 'Erklären Sie, welches Merkmal das Ergebnis trägt und warum gerade dort der Schwerpunkt der Prüfung liegt.',
            'explain_keys': [{'label': 'Merkmale kumulativ / Reihenfolge', 'terms': ['kumulativ', 'alle', 'reihenfolge', 'scheitert', 'endet']},
                             {'label': 'Definition auf den Sachverhalt angewandt', 'terms': ['definition', 'sachverhalt', 'subsum']},
                             {'label': 'Schwerpunkt beim problematischen Merkmal', 'terms': ['problemat', 'schwerpunkt', 'erörter', 'streit']}],
            'explore': [], 'choice': spec['sequence'].pop('_choice'),
            'takeaways': ['Ein Prüfungsschema ist eine Kette notwendiger Bedingungen: Die Rechtsfolge tritt nur ein, wenn alle Merkmale erfüllt sind.',
                          'Geprüft wird in der Reihenfolge des Schemas; das erste nicht erfüllte Merkmal beendet die Prüfung.',
                          'Unproblematisches kurz feststellen, problematische Merkmale im Gutachtenstil ausführlich erörtern.'],
            'summary_prompt': 'Fassen Sie in einem Satz zusammen, wie man mit einem Prüfungsschema zu einem Ergebnis kommt.',
            'transfer_id': 'transfer'}


def check(spec):
    m = spec['model']
    data = {k: m[k] for k in ('scheme', 'norm', 'question', 'rechtsfolge', 'negative', 'case', 'elements')}
    tr = next((t for t in spec['sequence']['tasks'] if t['id'] == 'transfer'), None)
    if tr and tr['prompt'] != f'Abwandlung: Der Sachverhalt wird so geändert, dass „{m["elements"][0]["label"]}“ nicht erfüllt ist. Was folgt für die Prüfung?':
        data['transfer'] = {k: tr[k] for k in ('prompt', 'options', 'correct', 'explanation')}
    ref = B.legal_check_spec(spec['id'], spec['title'], spec['kc_ids'], [], data)
    strip = lambda ts: [{k: v for k, v in t.items() if k != 'transfer'} for t in ts]
    if strip(spec['sequence']['tasks']) != strip(ref['sequence']['tasks']) or spec['sequence']['predict']['correct'] != ref['sequence']['predict']['correct']:
        raise LegalError('Prüfungsschema-Lab: Aufgaben oder Vorhersage weichen vom Referenzmodell ab')
    r = result(m['elements'])
    for case in spec.get('tests') or []:
        if case['positive'] != r['positive'] or case['stop'] != r['stop']:
            raise LegalError('Prüfungsschema-Lab: Testfall stimmt nicht')


def static_svg(spec):
    """The scheme itself (elements, norms, order, stop rule) – deliberately without the decisions of the case."""
    m = spec['model']; els = m['elements']; W = 640; bh, gap, t = 46, 22, 44
    H = t + len(els) * (bh + gap) + 60
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Prüfungsschema {B.E(m["scheme"])}">'
         f'<title>Prüfungsschema: {B.E(m["scheme"])}</title>',
         '<defs><marker id="lc-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1f5f8b"/></marker></defs>',
         f'<text x="20" y="24" font-size="14" font-weight="700" fill="#223">{B.E(m["scheme"])}</text>']
    for i, e in enumerate(els):
        y = t + i * (bh + gap)
        s.append(f'<rect x="20" y="{y}" width="430" height="{bh}" rx="6" fill="#f6efe2" stroke="#334"/>'
                 f'<text x="34" y="{y + 20}" font-size="13" font-weight="700" fill="#223">{i + 1}. {B.E(e["label"])}</text>'
                 f'<text x="34" y="{y + 37}" font-size="11" fill="#5b6876">{B.E(e.get("norm", ""))}</text>'
                 f'<line x1="450" y1="{y + bh / 2}" x2="520" y2="{y + bh / 2}" stroke="#9a3b1b" stroke-dasharray="4 3" marker-end="url(#lc-ah)"/>'
                 f'<text x="526" y="{y + bh / 2 + 4}" font-size="11" fill="#9a3b1b">nicht erfüllt: Ende</text>')
        s.append(f'<line x1="235" y1="{y + bh}" x2="235" y2="{y + bh + gap - 2}" stroke="#1f5f8b" stroke-width="2" marker-end="url(#lc-ah)"/>')
    y = t + len(els) * (bh + gap)
    s.append(f'<rect x="20" y="{y}" width="430" height="40" rx="6" fill="#dcebf5" stroke="#1f5f8b"/>'
             f'<text x="34" y="{y + 25}" font-size="13" font-weight="700" fill="#1f5f8b">alle erfüllt → Rechtsfolge</text></svg>')
    return ''.join(s)
