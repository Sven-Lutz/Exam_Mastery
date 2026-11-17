"""B35 learning-task model for interactive labs (domain-neutral; validator 'lab_task_model' of the profiles).

V4 defect this answers: lab tasks were multiple-choice items with a FIXED answer index and FIXED explanation text,
while the learner could edit the model (rewards, probabilities). After an edit the lab could mark a correct
prediction wrong and print an explanation that no longer held. A lab task must instead name a learning objective and
an observable success criterion, and every answer and every feedback sentence must be COMPUTED from the current model.

Sequence schema (lab-agnostic; the lab runtime supplies the 'compute' functions by name):
  {id, objective, prerequisites: [..], problem, method: [..], success: {criterion, max_hints},
   steps: [{id, kind, prompt, compute, diagnose?: [error models], hints?: [..], transfer?: bool}]}
  kind in: worked_example (shown, no answer), predict (choice; truth = compute), numeric (number; truth = compute,
           tolerance), explore (learner manipulates a parameter to reach a target computed by 'compute'), explain
           (free text, compared to a computed reference explanation), transfer (any of the above on a changed model)
Rules:
  T1 objective, problem and an observable success criterion are present
  T2 every answerable step names a 'compute' function the runtime provides (no literal answers, no 'answer' index)
  T3 numeric steps declare a tolerance and at least one diagnosable error model (feedback beyond right/wrong)
  T4 numeric/predict steps provide a hint ladder (>= 2 hints) so a learner can continue after an error
  T5 the sequence moves from guided to independent: a worked_example or hinted step before the first unhinted
     step, and at least one transfer step
  T6 no fixed feedback text that states a result ('explain' strings with numbers are rejected; numbers must come
     from compute)
"""
from __future__ import annotations
import re

KINDS = {'worked_example', 'predict', 'numeric', 'explore', 'explain', 'transfer'}
ANSWERABLE = {'predict', 'numeric', 'explore', 'explain', 'transfer'}


def validate(seq, runtime_functions):
    F = []
    def f(code, msg, step=None):
        F.append({'code': code, 'msg': msg, 'step': step, 'sequence': seq.get('id')})
    for k in ('objective', 'problem'):
        if not (seq.get(k) or '').strip():
            f('T1', f'missing {k}')
    if not ((seq.get('success') or {}).get('criterion') or '').strip():
        f('T1', 'missing observable success criterion')
    steps = seq.get('steps') or []
    for s in steps:
        sid, kind = s.get('id'), s.get('kind')
        if kind not in KINDS:
            f('T2', f'unknown step kind {kind!r}', sid); continue
        if 'answer' in s:
            f('T2', 'literal answer in a lab task (must be computed from the model)', sid)
        if kind in ANSWERABLE or (kind == 'transfer'):
            if s.get('compute') not in runtime_functions:
                f('T2', f'compute function {s.get("compute")!r} not provided by the lab runtime', sid)
        if kind == 'numeric':
            if 'tolerance' not in s:
                f('T3', 'numeric step without tolerance', sid)
            if not s.get('diagnose'):
                f('T3', 'numeric step without diagnosable error models', sid)
        if kind in ('numeric', 'predict') and len(s.get('hints') or []) < 2:
            f('T4', 'fewer than two hints: no way to continue after an error except seeing the solution', sid)
        for fld in ('explain', 'feedback'):
            if re.search(r'\d', str(s.get(fld) or '')):
                f('T6', f'fixed {fld} text contains a number; numbers must come from compute', sid)
    kinds = [s.get('kind') for s in steps]
    if steps and kinds[0] not in ('worked_example',) and not (steps[0].get('hints')):
        f('T5', 'sequence does not start guided (worked example or hinted step)')
    if not any(s.get('kind') == 'transfer' or s.get('transfer') for s in steps):
        f('T5', 'no transfer step')
    return F
