"""B35 exam timing and task-quality audit (domain-neutral).

V4 finding: both mock exams state "Bearbeitungszeit 60 Minuten" with per-item minutes that were chosen to sum to 60.
Nothing was measured; the header nevertheless read like a fact.

Calibration status (exam['calibration']['status'], printed in the header):
  EMPIRICAL           measured solve times of real learners (n, median, spread recorded)
  INDEPENDENT_SOLVE   timed solve attempts by independent solvers (who, n recorded) - not students
  MODEL_ESTIMATE      workload model below (parameters declared) - an estimate, never a measurement
  AUTHOR_ASSUMPTION   chosen by the author (default when nothing else is recorded)

Workload model (MODEL_ESTIMATE; every parameter declared, deliberately simple, NOT validated against learners):
  minutes = prompt_words / READ_WPM + answer_words / WRITE_WPM + formulas * MIN_PER_FORMULA
            + numeric_ops * MIN_PER_OP + rubric_parts * MIN_PER_DECISION
It is used only to flag items whose stated minutes or points are implausible RELATIVE to the other items of the same
exam (ratio outside [1/RATIO, RATIO] of the exam median). It does not certify any time.
"""
from __future__ import annotations
import re
from statistics import median

MODES = {'written': 1.0, 'essay': 1.4, 'case': 1.3}          # planning/outlining share on top of writing (declared assumption)
PARAMS = {'READ_WPM': 120, 'WRITE_WPM': 12, 'MIN_PER_FORMULA': 0.6, 'MIN_PER_OP': 0.2, 'MIN_PER_DECISION': 1.0, 'RATIO': 1.8}
STATUS = ('EMPIRICAL', 'INDEPENDENT_SOLVE', 'MODEL_ESTIMATE', 'AUTHOR_ASSUMPTION')
LABEL = {'EMPIRICAL': 'empirisch kalibriert', 'INDEPENDENT_SOLVE': 'aus unabhängigen Lösungsversuchen geschätzt, nicht an Studierenden gemessen',
         'MODEL_ESTIMATE': 'Modellschätzung, nicht gemessen', 'AUTHOR_ASSUMPTION': 'Übungsannahme, nicht kalibriert'}
_MATH = re.compile(r'\\\(.*?\\\)|\\\[.*?\\\]', re.S)
_OP = re.compile(r'\d\s*[-+*/·×]\s*\d')


def _words(s):
    return len(re.findall(r'[^\W\d_]{2,}', _MATH.sub(' ', s or '')))           # any script, accents included


def workload(item):
    sol = item.get('solution') or {}
    steps = ' '.join(' '.join(map(str, st)) if isinstance(st, (list, tuple)) else str(st) for st in sol.get('steps') or [])
    text = ' '.join([steps, str(sol.get('answer') or '')])
    f = dict(prompt_words=_words(item.get('prompt')), answer_words=_words(text), formulas=len(_MATH.findall(text)) + text.count('='),
             numeric_ops=len(_OP.findall(text)), rubric_parts=len(sol.get('rubric') or []))
    P = PARAMS
    f['model_minutes'] = round(f['prompt_words'] / P['READ_WPM'] + f['answer_words'] / P['WRITE_WPM'] + f['formulas'] * P['MIN_PER_FORMULA']
                               + f['numeric_ops'] * P['MIN_PER_OP'] + f['rubric_parts'] * P['MIN_PER_DECISION'], 1)
    return f


def audit_exam(exam):
    items, F = exam.get('items') or [], []
    mode = exam.get('mode', 'written')
    if mode not in MODES:                        # performance exams (OSCE, lab practical, sport): no writing-time model exists
        return {'calibration': (exam.get('calibration') or {}).get('status', 'AUTHOR_ASSUMPTION'), 'header_time': header_time(exam),
                'items': [], 'findings': [{'code': 'X0', 'severity': 'WARN', 'msg': f'no workload model for exam mode {mode!r}: timing needs station-level or empirical calibration'}],
                'model_total_minutes': None, 'params': PARAMS, 'scope': 'not applicable'}
    st = (exam.get('calibration') or {}).get('status', 'AUTHOR_ASSUMPTION')
    if st not in STATUS:
        F.append({'code': 'X1', 'severity': 'FAIL', 'msg': f'unknown calibration status {st}'})
    if st == 'EMPIRICAL' and not (exam.get('calibration') or {}).get('n'):
        F.append({'code': 'X1', 'severity': 'FAIL', 'msg': 'EMPIRICAL calibration without recorded sample size'})
    rows = []
    for it in items:
        w = workload(it); w['model_minutes'] = round(w['model_minutes'] * MODES[mode], 1); m = it.get('minutes'); pts = it.get('points')
        rows.append(dict(w, no=it.get('no'), minutes=m, points=pts, ratio=round(m / w['model_minutes'], 2) if m and w['model_minutes'] else None))
    stated = [r['minutes'] for r in rows if r['minutes']]
    if exam.get('minutes') and stated and abs(sum(stated) - exam['minutes']) < 1e-9 and st == 'AUTHOR_ASSUMPTION':
        F.append({'code': 'X2', 'severity': 'WARN', 'msg': 'item minutes sum exactly to the exam time: distributed, not measured'})
    total_model = round(sum(r['model_minutes'] for r in rows), 1)
    if exam.get('minutes') and total_model > 1.5 * exam['minutes']:
        F.append({'code': 'X6', 'severity': 'WARN', 'msg': f'workload model {total_model} min vs stated {exam["minutes"]} min: exam probably '
                  'overloaded (model counts the full model solution, so it overestimates) - needs timed independent solves'})
    rs = [r['ratio'] for r in rows if r['ratio']]
    if rs:
        med = median(rs)
        for r in rows:
            if r['ratio'] and not (1 / PARAMS['RATIO'] <= r['ratio'] / med <= PARAMS['RATIO']):
                F.append({'code': 'X3', 'severity': 'WARN', 'item': r['no'],
                          'msg': f'stated {r["minutes"]} min vs workload model {r["model_minutes"]} min: out of line with the other items'})
    pm = [(r['points'] / r['model_minutes'], r['no']) for r in rows if r['points'] and r['model_minutes']]
    if pm:
        med = median(x for x, _ in pm)
        for x, no in pm:
            if not (1 / PARAMS['RATIO'] <= x / med <= PARAMS['RATIO']):
                F.append({'code': 'X4', 'severity': 'WARN', 'item': no, 'msg': 'points out of line with the workload of the other items'})
    for it in items:
        if not (it.get('solution') or {}).get('rubric'):
            F.append({'code': 'X5', 'severity': 'FAIL', 'item': it.get('no'), 'msg': 'no rubric (points per partial performance)'})
    return {'calibration': st, 'header_time': header_time(exam), 'items': rows, 'model_total_minutes': total_model, 'findings': F, 'params': PARAMS,
            'scope': 'relative plausibility of stated minutes/points against a declared workload model; NOT a measured solve time'}


def header_time(exam):
    if not exam.get('minutes'):
        return 'keine Vorgabe'
    st = (exam.get('calibration') or {}).get('status', 'AUTHOR_ASSUMPTION')
    return f'{exam["minutes"]:g} Minuten ({LABEL.get(st, st)})'
