"""Guided learning (schema em-lesson-v1): prerequisite micro-lessons with a deterministic check question, the
prerequisite graph per task, hint-ladder levels and brief modes. Deterministic, no model call, no network.
Mirrors EMT.guided in templates/em_tutor.js; tests run both on the same inputs and require equal results.

A lesson is data on a track (`track['lessons']`) or an experience unit (`unit['lessons']`), both optional
(backward compatible). Links point from the lesson to what it is a prerequisite of, so tasks, categories and
misconceptions stay unchanged (an explorable's assessment revision does not move):

  id         stable id, e.g. 'prereq/sigmoid-derivative' (may equal a track competency id)
  title      short title
  explain    what it is and why the task needs it (1-3 sentences)
  formula    the central formula (Unicode text)
  example    worked mini-example, concrete numbers before symbols (list of steps)
  check      one quick check, checked by the same diagnosis as tasks:
             {type: numeric, prompt, expected, tolerance, errors: [{value, category, feedback}], explain} or
             {type: choice, prompt, options: [{value, label, category?, feedback?}], correct, explain}
  for        {kcs, categories} on a track; {competencies, misconceptions} on a unit
  requires   lesson ids that come first (prerequisites of the prerequisite), optional
  taught_in  where it is taught in full: [{kind, ref, label}]; kinds: worked_example, task, external (track);
             section, assessment, external (unit)

A lesson check is teaching, not evidence: it is logged as a 'guided' help event, never as an attempt, so it never
changes a competency state (R5-POL-04, R9-POL-10). Opening a lesson for a task makes that task, and the competency
the lesson teaches, assisted (CD-9).
"""
import re

from . import diagnose as D

SCHEMA = 'em-lesson-v1'
EVIDENCE_ROLES = ('similar', 'transfer', 'retest')   # mirrors tutor.KEY_WITHHELD_ROLES
LADDER = ('orientation', 'strategy', 'step')         # R5-POL-03 levels; the last hint is the bottom-out hint
TAUGHT_IN = {'track': ('worked_example', 'task', 'external'), 'unit': ('section', 'assessment', 'external')}


class LessonError(ValueError):
    pass


def _lessons(c):
    return c.get('lessons') or []


def task_kcs(task):
    """Competencies of a track task (kc_id) or of an explorable assessment (competency_ids)."""
    return [task['kc_id']] if task.get('kc_id') else list(task.get('competency_ids') or [])


def task_categories(task):
    """Error categories a task can diagnose (track bug libraries or an explorable machine check)."""
    t = task.get('machine_check') or task
    out = [e['category'] for e in t.get('errors', []) if e.get('category')]
    out += [b['category'] for b in t.get('bugs', []) if b.get('category')]
    out += [o['category'] for o in t.get('options', []) if o.get('category')]
    out += [c['category'] for c in t.get('constraints', []) if c.get('category')]
    for s in t.get('steps', []):
        out += [e['category'] for e in s.get('errors', []) if e.get('category')]
    return out


def _for(lesson, key):
    f = lesson.get('for') or {}
    if key == 'kcs':
        return list(f.get('kcs', [])) + list(f.get('competencies', []))
    return list(f.get('categories', [])) + list(f.get('misconceptions', []))


def lessons_for_task(c, task):
    """Ordered prerequisite lesson ids of one task: lessons declared for its competency or for an error category it
    can diagnose, and the lesson that teaches the task's own competency. Each lesson's `requires` come first
    (depth first, declaration order); no duplicates."""
    ls = _lessons(c); by = {l['id']: l for l in ls}
    kcs, cats = set(task_kcs(task)), set(task_categories(task))
    hit = [l for l in ls if l['id'] in kcs or kcs & set(_for(l, 'kcs')) or cats & set(_for(l, 'categories'))]
    out = []

    def visit(l, seen):
        if l['id'] in seen:
            return
        for r in l.get('requires', []):
            if r in by:
                visit(by[r], seen | {l['id']})
        if l['id'] not in out:
            out.append(l['id'])
    for l in hit:
        visit(l, frozenset())
    return out


def gap_for(c, diagnosis):
    """The lesson that teaches the prerequisite a diagnosis points to (first lesson declared for its category)."""
    cat = (diagnosis or {}).get('error_category')
    if not cat or (diagnosis or {}).get('result') not in ('incorrect', 'partial'):
        return None
    for l in _lessons(c):
        if cat in _for(l, 'categories'):
            return l['id']
    return None


def check_task(lesson):
    return dict(lesson['check'], id='lesson:' + lesson['id'], kc_id=lesson['id'])


def check(lesson, answer):
    """Deterministic check of a lesson question: result, error category and the matching feedback text."""
    q = lesson['check']; d = D.diagnose(check_task(lesson), answer)
    fb = None
    if d['result'] in ('incorrect', 'partial') and d['error_category']:
        src = q.get('errors', []) if q['type'] == 'numeric' else q.get('options', [])
        fb = next((e.get('feedback') for e in src if e.get('category') == d['error_category'] and e.get('feedback')), None)
    return {'result': d['result'], 'error_category': d['error_category'], 'evidence': d['evidence'], 'feedback': fb}


def hint_levels(n):
    """Ladder level of each of n hints: orientation, strategy, concrete step; the last one is the bottom-out hint."""
    if n <= 0:
        return []
    if n == 1:
        return ['step']
    if n == 2:
        return ['orientation', 'step']
    return ['orientation'] + ['strategy'] * (n - 2) + ['step']


def assist_level(k, n):
    """R5-POL-06: assist level of the k-th (1-based) of n hints; the last hint is the bottom-out hint."""
    return 'hint_bottom_out' if k >= n else 'hint_' + str(k)


def brief_mode(role, n_attempts):
    """R9-POL-04 / OD-10: 'task_withheld' for a later retest (never in a brief), 'keyless' for evidence roles and
    before an own attempt, 'with_reference' only for practice tasks after at least one logged attempt."""
    if role == 'retest':
        return 'task_withheld'
    if role in EVIDENCE_ROLES or n_attempts < 1:
        return 'keyless'
    return 'with_reference'


def _num_keys(v):
    if not isinstance(v, (int, float)) or abs(v - round(v, 2)) < 1e-9:
        return []   # integers and two-decimal values are too common to identify an answer key
    s = f'{v:.4f}'
    return [s, s.replace('.', ',')]


def evidence_keys(c):
    """Strings that identify an answer key of an evidence task (similar, transfer, retest): solution lines,
    expected expressions and expected numbers with at least three decimals (4-decimal rendering)."""
    keys = []
    for t in c.get('tasks') or c.get('assessments') or []:
        if t.get('role') not in EVIDENCE_ROLES:
            continue
        sol = t.get('solution') or []
        keys += [s for s in ([sol] if isinstance(sol, str) else sol) if s]
        if t.get('expected_expr'):
            keys.append(t['expected_expr'])
        spec = t.get('machine_check') or t
        keys += _num_keys(spec.get('expected'))
        for s in spec.get('steps', []):
            keys += _num_keys(s.get('expected'))
    return [k for k in keys if len(k) >= 4]


def leaks(c, text):
    """Evidence keys found in a text meant for the learner or an external model (deterministic guard)."""
    return [k for k in evidence_keys(c) if k in text]


def lesson_text(lesson):
    q = lesson['check']
    parts = [lesson['title'], lesson['explain'], lesson['formula'], *lesson['example'], q['prompt'], q.get('explain', '')]
    parts += [o['label'] for o in q.get('options', [])] + [e.get('feedback', '') for e in q.get('errors', []) + q.get('options', [])]
    return '\n'.join(parts)


def _answer(q):
    return repr(q['expected']) if q['type'] == 'numeric' else q['correct']


def validate_lessons(c, kind='track'):
    """Problems of the lessons of a track or unit (empty list = valid)."""
    probs = []
    ls = _lessons(c)
    if not isinstance(ls, list):
        return ['lessons: expected a list']
    ids = [l.get('id') for l in ls]
    if len(set(ids)) != len(ids):
        probs.append('lessons: duplicate id')
    by = {l.get('id'): l for l in ls}
    if kind == 'track':
        kcs = {k['id'] for k in c.get('kcs', [])}; cats = set(c.get('categories', {}))
        refs = {'worked_example': set(c.get('worked_examples', {})), 'task': {t['id'] for t in c.get('tasks', [])}}
        prompts = {t['prompt'] for t in c.get('tasks', [])}
    else:
        kcs = {k['id'] for k in c.get('competencies', [])}; cats = {m['id'] for m in c.get('misconceptions', [])}
        refs = {'section': {t['id'] for t in c.get('teaching', [])}, 'assessment': {t['id'] for t in c.get('assessments', [])}}
        prompts = {t['prompt'] for t in c.get('assessments', [])}
    for l in ls:
        w = f'lesson {l.get("id")}'
        for key in ('id', 'title', 'explain', 'formula'):
            if not isinstance(l.get(key), str) or not l[key].strip():
                probs.append(f'{w}: {key} missing')
        if not isinstance(l.get('example'), list) or not l['example'] or not all(isinstance(s, str) and s for s in l['example']):
            probs.append(f'{w}: example must be a nonempty list of steps')
        q = l.get('check')
        if not isinstance(q, dict) or q.get('type') not in ('numeric', 'choice') or not q.get('prompt') or not q.get('explain'):
            probs.append(f'{w}: check needs type numeric|choice, prompt and explain'); continue
        if q['prompt'] in prompts:
            probs.append(f'{w}: check reuses a task prompt')
        try:
            if D.diagnose(check_task(l), _answer(q))['result'] != 'correct':
                probs.append(f'{w}: check answer not diagnosed as correct')
            wrong = ([(repr(e['value']), e) for e in q.get('errors', [])] if q['type'] == 'numeric'
                     else [(o['value'], o) for o in q.get('options', []) if o['value'] != q['correct']])
            for ans, e in wrong:
                if not e.get('category') or not e.get('feedback'):
                    probs.append(f'{w}: wrong answer {ans!r} needs category and feedback')
                elif D.diagnose(check_task(l), ans)['error_category'] != e['category']:
                    probs.append(f'{w}: wrong answer {ans!r} not diagnosed as {e["category"]}')
            if q['type'] == 'choice' and q['correct'] not in {o['value'] for o in q.get('options', [])}:
                probs.append(f'{w}: correct option missing')
        except (KeyError, TypeError, ValueError) as exc:
            probs.append(f'{w}: check not executable ({exc})')
        f = l.get('for') or {}
        allowed = ('kcs', 'categories') if kind == 'track' else ('competencies', 'misconceptions')
        if not isinstance(f, dict) or set(f) - set(allowed):
            probs.append(f'{w}: for may only contain {", ".join(allowed)}')
        for k in _for(l, 'kcs'):
            if k not in kcs:
                probs.append(f'{w}: unknown competency {k}')
        for k in _for(l, 'categories'):
            if k not in cats:
                probs.append(f'{w}: unknown category {k}')
        for r in l.get('requires', []):
            if r not in by:
                probs.append(f'{w}: requires unknown lesson {r}')
        for ti in l.get('taught_in', []):
            kd = ti.get('kind')
            if kd not in TAUGHT_IN[kind] or not ti.get('label'):
                probs.append(f'{w}: taught_in needs kind in {TAUGHT_IN[kind]} and label')
            elif kd != 'external' and ti.get('ref') not in refs.get(kd, set()):
                probs.append(f'{w}: taught_in {kd} {ti.get("ref")} not found')
        if not any(p.startswith(w + ':') for p in probs):
            found = leaks(c, lesson_text(l))
            if found:
                probs.append(f'{w}: contains an evidence answer key {found[0]!r}')
    # requires must be acyclic
    state = {}

    def cyc(i):
        if state.get(i) == 1:
            return True
        if state.get(i) == 2 or i not in by:
            return False
        state[i] = 1
        bad = any(cyc(r) for r in by[i].get('requires', []))
        state[i] = 2
        return bad
    if any(cyc(i) for i in by):
        probs.append('lessons: requires contains a cycle')
    return probs


def lesson_anchor(ref):
    """DOM id of an explorable teaching section (same slug rule as interactive_reference.re_slug)."""
    return 'teaching-' + re.sub(r'[^a-z0-9_-]', '-', ref)
