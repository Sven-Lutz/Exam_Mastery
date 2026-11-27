"""Adaptive learning policy (schema em-decision-v1): small, rule-based, explainable. Mirrors templates/em_tutor.js.

Input: a track (tasks with roles, error categories, worked examples, contrasts) and the observed events of one learner.
Output: the next learning action plus the evidence it rests on. No probabilities, no mastery score.

Rules (ids are stable and appear in the UI, the event log and the tests):
  R0   start                      no attempt yet -> diagnostic task of the prerequisites
  RA   prerequisite missing       error category of kind 'prerequisite' -> worked example, then a parallel prerequisite task
  RB   slip in a known step       kind 'slip' -> focus on that step (visual + term), then a similar task WITHOUT hints
  RC1  misconception, first time  kind 'misconception' -> targeted feedback + visual, same task again (no solution shown)
  RC2  misconception, repeated    same misconception category >= 2 times -> contrasting example + contrast task
  RU   cause unknown              unclassified wrong answer -> next hint; after 2 such answers worked example + tutor offer
  RL5  open answer                free text -> UNVERIFIED, continue; tutor review offered
  RP   prerequisite solved        -> core task
  RF   solved with help           hint or solution used -> similar task without hints (fading)
  RD   independent success       solved without help -> skip practice, go to transfer; after >= 2 independent
                                  successes incl. transfer -> harder, structurally changed task
  RE   retention unknown          everything solved today -> NOT 'mastered': later retrieval (Anki tags, retest task
                                  on a later day); a retest solved independently on a later day is reported as such

Retention evidence (kc_status) uses elapsed time, not calendar dates: RETAINED_ON_LATER_DAY needs an independent
success on a *different* task at least RETENTION_MIN_GAP_HOURS after an earlier independent success. Two
successes at 23:59 and 00:01, or the same task repeated, are not evidence of retention (R0 audit, R1 policies A01/A05).
"""
from datetime import date, datetime, timedelta, timezone

SCHEMA = 'em-decision-v1'
GENERIC = {
    'sign_error': {'kind': 'slip', 'label': 'Vorzeichen', 'feedback': 'Der Betrag stimmt, das Vorzeichen nicht. Prüfen Sie, welche Größe positiv und welche negativ gezählt wird.'},
    'unit_scale': {'kind': 'slip', 'label': 'Einheit / Größenordnung', 'feedback': 'Die Ziffern passen, die Größenordnung nicht. Prüfen Sie die Einheit der Antwort.'},
    'rounding': {'kind': 'slip', 'label': 'Rundung', 'feedback': 'Fast richtig: Die Abweichung liegt in der Rundung. Rechnen Sie mit mehr Nachkommastellen bis zum Schluss.'},
    'constant_factor': {'kind': 'slip', 'label': 'konstanter Faktor', 'feedback': 'Die Struktur Ihres Ausdrucks stimmt bis auf einen konstanten Faktor. Prüfen Sie Vorfaktoren wie ½ oder 2.'},
    'unclassified': {'kind': 'unknown', 'label': 'Ursache nicht erkannt', 'feedback': 'Ihre Antwort weicht ab, aber die Ursache passt zu keinem bekannten Fehlermuster. Prüfen Sie Ihren Rechenweg Schritt für Schritt.'},
}


# Provisional product parameter, not an empirical constant: roughly one night between the two successes.
RETENTION_MIN_GAP_HOURS = 20


def _instant(t):
    """Aware UTC instant; a bare date means 00:00 UTC of that day (same rule as em_tutor.js)."""
    if isinstance(t, datetime):
        d = t
    elif isinstance(t, date):
        d = datetime(t.year, t.month, t.day)
    else:
        d = datetime.fromisoformat(str(t).replace('Z', '+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def category(track, cid):
    return track['categories'].get(cid) or GENERIC.get(cid) or GENERIC['unclassified']


# Events that make a later attempt on the same task assisted. 'tutor' is written when the learner prepares a tutor
# context for the task (CD-7, R5-POL-04): what happens in that conversation is not observed, so it counts as help.
ASSIST_EVENTS = ('hint', 'solution', 'tutor')


def helped(events, task_id, upto=None):
    evs = events if upto is None else events[:upto + 1]
    return any(e['type'] in ASSIST_EVENTS and e.get('task') == task_id for e in evs)


# Help on ANY task of the same competency shortly before an attempt also makes that attempt assisted for the
# competency's evidence state: a worked solution of a sibling task shows the method (CD-9, R6 red team RT-26).
# Provisional design parameter (same order as the retention gap), not an evidence-based constant.
KC_HELP_WINDOW_HOURS = RETENTION_MIN_GAP_HOURS
FUTURE_SKEW_MINUTES = 5  # tolerated clock skew for event timestamps (CD-9)


def _kc_helped(events, tasks, kc_id, i, t_attempt):
    window = timedelta(hours=KC_HELP_WINDOW_HOURS)
    return any(e['type'] in ASSIST_EVENTS and tasks.get(e.get('task'), {}).get('kc_id') == kc_id
               and t_attempt - _instant(e['t']) <= window for e in events[:i])


def _solved(events, task_id):
    return any(e['type'] == 'attempt' and e['task'] == task_id and e['diagnosis']['result'] == 'correct' for e in events)


def _role(track, role, kc=None, exclude_solved=None):
    for t in track['tasks']:
        if t['role'] == role and (kc is None or t['kc_id'] == kc) and not (exclude_solved and _solved(exclude_solved, t['id'])):
            return t['id']
    return None


def _dec(rule, action, nxt, obs, why, unc, support=None, hints_allowed=True, focus=None, tutor=False, retention=None):
    return {'schema': SCHEMA, 'rule': rule, 'action': action, 'next_task': nxt, 'hints_allowed': hints_allowed,
            'support': support, 'focus': focus, 'tutor_offer': tutor, 'observation': obs, 'rationale': why,
            'uncertainty': unc, 'retention': retention}


def kc_status(track, events, today=None):
    """Observed state per competency (vocabulary of the tutor protocol). Never a percentage.

    `today` is the reference instant (ISO date or timestamp); default: now (UTC)."""
    now = _instant(today) if today else datetime.now(timezone.utc)
    gap = timedelta(hours=RETENTION_MIN_GAP_HOURS)
    latest = datetime.now(timezone.utc) + timedelta(minutes=FUTURE_SKEW_MINUTES)
    T = {t['id']: t for t in track['tasks']}
    out = {}
    for kc in track['kcs']:
        # Attempts dated after the real clock (plus a small skew) are not evidence: client or imported clocks may run
        # ahead and would turn into 'retention' later (CD-9). The reference instant keeps its CD-2 meaning.
        evs = [(i, e) for i, e in enumerate(events) if e['type'] == 'attempt' and T.get(e['task'], {}).get('kc_id') == kc['id']
               and _instant(e['t']) <= latest]
        if not evs:
            out[kc['id']] = 'NOT_ASSESSED'; continue
        indep = sorted((_instant(e['t']), e['task']) for i, e in evs
                       if e['diagnosis']['result'] == 'correct' and not helped(events, e['task'], i)
                       and not _kc_helped(events, T, kc['id'], i, _instant(e['t'])))
        aided = any(e['diagnosis']['result'] == 'correct' for i, e in evs)
        retained = any(t2 - t1 >= gap and k2 != k1 for t1, k1 in indep for t2, k2 in indep)
        if retained:
            out[kc['id']] = 'RETAINED_ON_LATER_DAY'
        elif indep and now - indep[0][0] >= gap:
            out[kc['id']] = 'RETEST_DUE'
        elif indep:
            out[kc['id']] = 'INDEPENDENT_PASS'
        elif aided:
            out[kc['id']] = 'ASSISTED'
        else:
            out[kc['id']] = 'INDEPENDENT_PARTIAL'
    return out


# Task types that only ask to recognise or select. For a competency of type 'argument' (proof) such evidence shows
# that the learner recognises premises or conclusions, not that they can build the argument (CD-11, R6 RT-10,
# R2-POL-02: comprehension, validation and construction are reported separately).
RECOGNITION_TYPES = ('choice', 'constraints')


def kc_evidence_basis(track, events, today=None):
    """Per competency: what its independent evidence consists of - 'none', 'recognition_only' or 'production'.

    Same independence rules as kc_status (per-task and competency-level help, no future-dated attempts)."""
    latest = datetime.now(timezone.utc) + timedelta(minutes=FUTURE_SKEW_MINUTES)
    T = {t['id']: t for t in track['tasks']}
    out = {}
    for kc in track['kcs']:
        types = {T[e['task']]['type'] for i, e in enumerate(events)
                 if e['type'] == 'attempt' and T.get(e['task'], {}).get('kc_id') == kc['id'] and _instant(e['t']) <= latest
                 and e['diagnosis']['result'] == 'correct' and not helped(events, e['task'], i)
                 and not _kc_helped(events, T, kc['id'], i, _instant(e['t']))}
        out[kc['id']] = 'none' if not types else 'recognition_only' if types <= set(RECOGNITION_TYPES) else 'production'
    return out


def decide(track, events, now=None):
    T = {t['id']: t for t in track['tasks']}
    flow = track['flow']
    atts = [(i, e) for i, e in enumerate(events) if e['type'] == 'attempt' and e['diagnosis']['result'] != 'invalid']
    retention = {'anki_tags': track.get('anki_tags', []), 'note': 'Heute richtig gelöst heißt nicht dauerhaft behalten. Anki plant die Wiederholung; eine Prüfaufgabe mit neuen Zahlen wird frühestens am nächsten Tag angeboten.'}
    if not atts:
        return _dec('R0', 'start', flow[0], 'Noch keine Lernhandlung beobachtet.',
                    'Zuerst wird geprüft, ob die Voraussetzung sitzt; erst dann lohnt die Hauptaufgabe.', 'Ohne Versuch ist über den Lernstand nichts bekannt.')
    i, last = atts[-1]; d = last['diagnosis']; task = T[d['task_id']]
    obs = f'Aufgabe „{task["title"]}“: Ergebnis {d["result"]}' + (f', Fehlerkategorie {category(track, d["error_category"])["label"]}' if d.get('error_category') else '') + f' (Prüfverfahren {d["method"]}, Evidenz {d["evidence"]}).'
    if d['result'] == 'unverified':
        nxt = _next_in_flow(track, events, task['id'])
        return _dec('RL5', 'continue', nxt, obs, 'Freitext wird hier nicht bewertet. Der Tutor kann eine Rückmeldung geben; sie bleibt eine Modelleinschätzung.',
                    'Ob die Begründung trägt, ist ungeprüft.', tutor=True)
    if d['result'] in ('incorrect', 'partial'):
        cid = d.get('error_category') or 'unclassified'; cat = category(track, cid)
        same = sum(1 for _, e in atts if e['diagnosis'].get('error_category') == cid)
        if cat['kind'] == 'prerequisite':
            retry = task.get('prereq_retry') or cat.get('retry_task_id') or _role(track, 'prereq_retry', exclude_solved=events) or task['id']
            return _dec('RA', 'worked_example', retry, obs, f'Die Antwort passt zu einer fehlenden Voraussetzung ({cat["label"]}). Ein durchgerechnetes Beispiel zeigt sie; danach eine parallele Aufgabe zur Voraussetzung.',
                        'Dieselbe Zahl kann auch durch einen Flüchtigkeitsfehler entstehen.', support=cat.get('support'), focus=cat.get('visual'))
        if cat['kind'] == 'misconception' and same >= 2:
            nxt = cat.get('contrast_task_id') or _role(track, 'contrast', exclude_solved=events) or _role(track, 'transfer', exclude_solved=events) or task['id']
            return _dec('RC2', 'contrast_example', nxt, obs + f' Dieselbe Verwechslung zum {same}. Mal.',
                        'Die Verwechslung wiederholt sich. Ein Kontrastbeispiel stellt beide Begriffe nebeneinander; danach eine Aufgabe, in der sie sich deutlich unterscheiden.',
                        'Zwei gleiche Fehler sind ein Muster, kein Beweis einer festen Fehlvorstellung.', support=cat.get('contrast') or cat.get('support'), focus=cat.get('visual'))
        if cat['kind'] == 'misconception':
            return _dec('RC1', 'targeted_feedback', task['id'], obs, 'Die Antwort passt zu einer bekannten Verwechslung. Die Rückmeldung benennt den Unterschied und zeigt ihn im Bild; die Lösung bleibt verborgen, damit Sie selbst korrigieren.',
                        'Die Kategorie ist die wahrscheinlichste Erklärung der Zahl, keine sichere Ursache.', support=cat.get('support'), focus=cat.get('visual'))
        if cat['kind'] == 'slip':
            nxt = task.get('similar') or _role(track, 'similar', task['kc_id'], exclude_solved=events) or task['id']
            return _dec('RB', 'focus_step', nxt, obs, f'Der Ansatz ist erkennbar, ein Schritt fehlt oder ist falsch ({cat["label"]}). Dieser Schritt wird im Bild und in der Formel hervorgehoben; danach eine ähnliche Aufgabe ohne Hinweise.',
                        'Ob es ein Flüchtigkeits- oder ein Verständnisfehler war, zeigt erst die nächste Aufgabe.', support=cat.get('support'), focus=cat.get('visual'), hints_allowed=False)
        n_unk = sum(1 for _, e in atts if e['task'] == task['id'] and e['diagnosis'].get('error_category') in (None, 'unclassified'))
        if n_unk >= 2:
            return _dec('RU', 'worked_example', task['id'], obs, 'Zweimal eine Abweichung ohne erkennbares Muster: Ein durchgerechnetes Beispiel und, wenn Sie möchten, der Tutor helfen, die Ursache zu finden.',
                        'Die Ursache ist unbekannt; das System rät nicht.', support=track['worked_examples'].get(task['kc_id']) and {'type': 'worked_example', 'ref': task['kc_id']}, tutor=True)
        return _dec('RU', 'next_hint', task['id'], obs, 'Die Antwort passt zu keinem bekannten Fehlermuster. Der nächste Hinweis gibt einen Zwischenschritt vor; versuchen Sie es erneut.',
                    'Die Ursache ist unbekannt.')
    # correct
    indep = not helped(events, task['id'], i)
    if task['role'] in ('diagnostic', 'prereq_retry'):
        return _dec('RP', 'next_task', _role(track, 'core', exclude_solved=events) or flow[1], obs, 'Die Voraussetzung sitzt. Weiter zur Hauptaufgabe.', 'Eine richtige Antwort zur Voraussetzung ist eine Stichprobe.')
    if task['role'] == 'retest':
        return _dec('RE', 'done', None, obs, 'Die Prüfaufgabe an einem späteren Tag wurde ' + ('ohne Hilfe' if indep else 'mit Hilfe') + ' gelöst.',
                    'Auch das ist eine einzelne Messung; Anki übernimmt die weitere Wiederholung.', retention=retention)
    if not indep:
        nxt = _role(track, 'similar', task['kc_id'], exclude_solved=events) or _next_in_flow(track, events, task['id'])
        return _dec('RF', 'similar_without_hints', nxt, obs + ' Mit Hilfe gelöst.', 'Mit Hilfe gelöst ist noch nicht selbstständig gelöst. Es folgt eine ähnliche Aufgabe ohne Hinweise.',
                    'Ob die Hilfe verstanden oder nur übernommen wurde, zeigt die nächste Aufgabe.', hints_allowed=False)
    n_indep = sum(1 for k, e in atts if e['diagnosis']['result'] == 'correct' and not helped(events, e['task'], k) and T[e['task']]['role'] in ('core', 'similar', 'contrast', 'transfer'))
    if task['role'] in ('core', 'similar', 'contrast'):
        nxt = _role(track, 'transfer', exclude_solved=events)
        if nxt:
            return _dec('RD', 'transfer', nxt, obs + ' Ohne Hilfe gelöst.', 'Selbstständig gelöst: weitere gleichartige Übung bringt wenig. Es folgt eine Transferaufgabe mit veränderter Struktur.',
                        'Eine selbstständige Lösung zeigt Können heute, nicht Behalten.', retention=retention)
    if task['role'] in ('transfer', 'harder') and n_indep >= 2:
        nxt = _role(track, 'harder', exclude_solved=events)
        if nxt:
            return _dec('RD', 'harder_task', nxt, obs + f' {n_indep} selbstständige Lösungen.', 'Mehrere Aufgaben ohne Hilfe gelöst: eine anspruchsvollere, strukturell veränderte Aufgabe.',
                        'Die Auswahl beruht auf einer kleinen Zahl von Aufgaben.', retention=retention)
    nxt = _next_in_flow(track, events, task['id'])
    if nxt:
        return _dec('RF' if not indep else 'RD', 'next_task', nxt, obs, 'Weiter im Lernpfad.', 'Eine einzelne Lösung ist eine Stichprobe.', retention=retention)
    return _dec('RE', 'schedule_retrieval', _role(track, 'retest'), obs, 'Alle Aufgaben dieser Lernstrecke sind bearbeitet. Ob Sie es behalten, zeigt erst ein späterer Abruf: Anki-Karten mit den angegebenen Schlagwörtern und morgen oder später die Prüfaufgabe mit neuen Zahlen.',
                'Behalten ist nicht beobachtet.', retention=retention)


def _next_in_flow(track, events, current):
    flow = track['flow']
    after = flow[flow.index(current) + 1:] if current in flow else flow
    for tid in after:
        if not _solved(events, tid):
            return tid
    return None
