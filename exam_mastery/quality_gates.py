"""P3.1: explainable quality gates for a chapter ContentAST (em-content-v1).

Purpose: a structurally valid but didactically empty, unspecified, unsupported or mislabelled chapter can never be
reported as content- or release-ready. Every gate emits machine-readable GateFindings; gates that could not run are
NOT_TESTED and inapplicable gates NOT_APPLICABLE with a reason. No result of this module is a subject-matter release:
the best automatic outcome is MACHINE_CHECKS_PASSED with semantic review still PENDING.

What is checked here is consistency and specification (is the target stated, is the data in the prompt, does the item
demand the operation, does the evidence chain end in a real anchor, is a status backed by a review record). Whether a
proof is valid, a solution correct or a legal assessment sound is NOT decided here (G4.PROOF_VALIDITY is NOT_TESTED).
"""
import re
from .curriculum import operations_in, satisfied, MC_PATTERN, CASE_PATTERN, NORM_PATTERN, terms, source_support
from .validate import check_content_ast, check_shapes, evaluate_numeric
from .derivation_check import check_steps, SCOPE as STEP_SCOPE

REPORT_SCHEMA = 'em-quality-gate-report-v1'
STATUS_ORDER = ['FAIL', 'BLOCKED', 'PENDING', 'PASS', 'NOT_APPLICABLE', 'NOT_TESTED']
FINDING_STATUS = {'PASS', 'FAIL', 'BLOCKED', 'PENDING', 'NOT_TESTED', 'NOT_APPLICABLE'}
GATES = {
    'G0.STRUCTURE': 'P3 structural/evidence/operational data-model checks (validate.check_content_ast)',
    'G1.ITEM_TARGET': 'item states an identifiable target (term cue, statement, quantity, artefact, legal question)',
    'G1.ITEM_DATA': 'data/context required to solve the item is stated in the item itself',
    'G1.ITEM_OPERATION': 'wording demands the declared operation; demanding KCs covered by a matching item',
    'G1.ITEM_SOLUTION': 'reference solution exists, is linked and has justified steps and an answer',
    'G1.ITEM_RUBRIC': 'rubric discriminates, carries partial points and sums to the item points',
    'G1.ITEM_TRANSFER': 'transfer label has a resolvable origin, a stated variation and a non-recall operation',
    'G2.EVIDENCE_CHAIN': 'item -> substantive block of the same KC -> valid source anchor / verified supplement',
    'G2.SOURCE_SUPPORT': 'support level per block: SOURCE_EXISTS < SOURCE_SUPPORT_LEXICAL < SOURCE_SUPPORT_CONFIRMED (human only)',
    'G3.REVIEW_RECORDS': 'every review status is backed by a complete review record; fakes are TEST_ONLY',
    'G3.STATUS_LABELS': 'no forbidden release/verification label and no self-certification',
    'G4.DIMENSIONS': 'matrix/vector dimension consistency (says nothing about algebraic correctness)',
    'G4.NUMERIC': 'declared numeric checks of solutions recompute to the stated values',
    'G4.ANSWER_CONSISTENCY': 'each recomputed numeric value is the one the solution text actually states',
    'G4.STEP_ARITHMETIC': 'arithmetic of equation chains written in calculation blocks/solutions (not the set-up)',
    'G4.DERIVATION_SETUP': 'whether the chosen relation/model/approach is the right one (needs independent review)',
    'G4.PROOF_VALIDITY': 'logical validity of proofs/derivations (needs independent expert review)',
    'G4.DOMAIN_FORMAL': 'formal blocks state assumptions/domain of validity',
    'G4.DOMAIN_LAW': 'subsumption names norm, element and fact per step; norm wording/legal status checked',
    'G4.DOMAIN_COMPUTING': 'implementation items carry executable test cases; execution itself in isolation',
    'G4.DOMAIN_QUANT': 'calculations state assumptions and interpret the result',
    'G5.SOURCE_FIDELITY': 'partial/uncertain source elements mapped to the blocks and KCs that rely on them',
    'G5.SOURCE_NUMBERS': 'every number in a COURSE_SOURCE block occurs in its anchored source elements',
    'G5.FIGURES': 'used figures resolvable, captioned, with alt text and review status; necessary open visuals stay open',
    'G5.NOTATION': 'notation conflicts stay visible or are resolved with an evidenced official-precedence basis',
}
FORBIDDEN_LABELS = {'ACADEMIC_VERIFIED', 'ACADEMICALLY_VERIFIED', 'RELEASE_GO', 'CONTENT_GO', 'RELEASED', 'VERIFIED',
                    'SUPPORTED', 'COVERED', 'CONFIRMED', 'SOURCE_SUPPORT_CONFIRMED', 'APPROVED'}
NON_SUBSTANTIVE = {'MOTIVATION', 'INTUITION', 'SUMMARY', 'REMARK'}
SUBSTANTIVE_FORMAL = {'DEFINITION', 'THEOREM', 'PROOF', 'DERIVATION', 'MODEL', 'ASSUMPTIONS'}
TARGET_KINDS = {'TERM', 'STATEMENT', 'QUANTITY', 'ARTIFACT', 'LEGAL_QUESTION', 'EXPLANANDUM'}
ITEM_PROVENANCE = {'COURSE_SOURCE', 'EXAM_ADAPTED', 'AUTHOR_CREATED', 'VERIFIED_SUPPLEMENT'}
REVIEWER_KINDS = {'MODEL', 'HUMAN_EXPERT', 'TEST_FIXTURE'}
REVIEW_FIELDS = ('review_id', 'reviewer_kind', 'reviewer_id', 'provider', 'assertion_id', 'evidence_refs', 'verdict',
                 'timestamp', 'build_id')
NEEDS_DATA = {'CALCULATE', 'APPLY', 'SUBSUME', 'IMPLEMENT', 'EVALUATE', 'INTERPRET'}
TARGET_FOR = {'PROVE': {'STATEMENT'}, 'DERIVE': {'STATEMENT'}, 'CALCULATE': {'QUANTITY'}, 'IMPLEMENT': {'ARTIFACT'},
              'SUBSUME': {'LEGAL_QUESTION'}}


def _covered(text, prompt):
    """A stated phrase is identifiable in the prompt (normalised substring or >= half of its content terms)."""
    t, p = (text or '').strip().lower(), (prompt or '').lower()
    if not t:
        return False
    if t in p:
        return True
    tt = terms(t)
    return bool(tt) and len(tt & terms(p)) * 2 >= len(tt)


class Report:
    def __init__(self):
        self.findings, self.executed = [], {g: [] for g in GATES}
        self.not_applicable, self.not_tested = {}, {}

    def ran(self, gate, what):
        self.executed[gate].append(what)

    def add(self, gate, obj, status, severity, reason, evidence=(), action=''):
        assert gate in GATES and status in FINDING_STATUS
        self.findings.append({'finding_id': f'gf-{len(self.findings) + 1:04d}', 'gate_id': gate, 'object_id': obj,
                              'status': status, 'severity': severity, 'reason': reason,
                              'evidence_refs': sorted({str(e) for e in evidence if e}), 'recommended_action': action})

    def na(self, gate, reason):
        self.not_applicable[gate] = reason

    def nt(self, gate, reason):
        self.not_tested[gate] = reason


def _items_results(ast_, chapter, plan, manifest, R, kcs, blocks, pkg, by):
    sol = {s.get('solution_id'): s for s in ast_['solutions']}
    exam_ids = {q['item_id'] for q in plan['assessment_items']}
    results = []
    for a in ast_['assessments']:
        aid, prompt = a.get('item_id'), a.get('prompt', '')
        res = {'schema': 'em-assessment-quality-v1', 'item_id': aid, 'kc_ids': a.get('kc_ids', []),
               'declared_operation': a.get('required_operation'), 'demanded_operations': operations_in(prompt),
               'checks': {}, 'covers_kc_operation': {}, 'finding_ids': []}
        start = len(R.findings)

        def chk(name, status, gate, severity, reason, evidence=(), action=''):
            res['checks'][name] = status
            if status != 'PASS':
                R.add(gate, aid, status, severity, reason, evidence, action)
        op = a.get('required_operation') or (res['demanded_operations'][:1] or [None])[0]
        tgt = a.get('target') if isinstance(a.get('target'), dict) else None
        # ---- G1 target
        R.ran('G1.ITEM_TARGET', aid)
        if not tgt or tgt.get('kind') not in TARGET_KINDS or not str(tgt.get('text', '')).strip():
            chk('target', 'BLOCKED', 'G1.ITEM_TARGET', 'major', 'no identifiable target: the item does not say which term, '
                'statement, quantity or artefact is meant', [], 'state target {kind,text}; the text must appear in the prompt')
        elif not _covered(tgt['text'], prompt):
            chk('target', 'BLOCKED', 'G1.ITEM_TARGET', 'major', f"declared target '{tgt['text']}' is not stated in the prompt "
                '(a learner cannot identify it)', [], 'put the concrete target into the item wording')
        elif op in TARGET_FOR and tgt['kind'] not in TARGET_FOR[op]:
            chk('target', 'BLOCKED', 'G1.ITEM_TARGET', 'major', f"{op} needs a target of kind {sorted(TARGET_FOR[op])}, got {tgt['kind']}")
        else:
            chk('target', 'PASS', 'G1.ITEM_TARGET', '', '')
        # ---- G1 data
        R.ran('G1.ITEM_DATA', aid)
        given = a.get('given') or []
        if op in NEEDS_DATA and not given:
            chk('data', 'BLOCKED', 'G1.ITEM_DATA', 'major', f'{op} item without stated data/case', [], 'state data or Sachverhalt in the item')
        elif any(not _covered(g, prompt) for g in given):
            chk('data', 'BLOCKED', 'G1.ITEM_DATA', 'major', 'declared data is not contained in the item text',
                [g for g in given if not _covered(g, prompt)], 'put all required data into the prompt')
        else:
            chk('data', 'PASS', 'G1.ITEM_DATA', '', '')
        # ---- G1 operation (wording-based; semantic confirmation stays pending)
        R.ran('G1.ITEM_OPERATION', aid)
        q = {'format': 'multiple_choice' if a.get('format') == 'multiple_choice' or MC_PATTERN.search(prompt) else 'open',
             'has_concrete_instance': bool(CASE_PATTERN.search(prompt)), 'norm_refs': NORM_PATTERN.findall(prompt)}
        if op:
            ok, why = satisfied(op, res['demanded_operations'], q)
            chk('operation', 'PASS' if ok else 'FAIL', 'G1.ITEM_OPERATION', 'major', why)
        else:
            chk('operation', 'BLOCKED', 'G1.ITEM_OPERATION', 'major', 'no operation declared or recognisable')
        for kid in a.get('kc_ids', []):
            if kid in kcs:
                res['covers_kc_operation'][kid] = all(satisfied(o, res['demanded_operations'], q)[0] for o in kcs[kid]['operations'])
        # ---- G1 solution / rubric
        R.ran('G1.ITEM_SOLUTION', aid); R.ran('G1.ITEM_RUBRIC', aid)
        s = sol.get(a.get('solution_id'))
        if not s or s.get('item_id') not in (None, aid):
            chk('solution', 'BLOCKED', 'G1.ITEM_SOLUTION', 'major', 'no reference solution linked to this item')
            chk('rubric', 'BLOCKED', 'G1.ITEM_RUBRIC', 'major', 'no rubric without solution')
        else:
            steps = s.get('steps') or []
            if not steps or not str(s.get('answer', '')).strip() or any(not str(x.get('justification', '')).strip() for x in steps):
                chk('solution', 'BLOCKED', 'G1.ITEM_SOLUTION', 'major', 'solution lacks justified steps or an answer')
            else:
                chk('solution', 'PENDING', 'G1.ITEM_SOLUTION', 'info', 'solution correctness not machine-decidable; blind re-solve '
                    'by an independent reviewer required', [s['solution_id']], 'independent review')
            rub, pts = s.get('rubric') or [], a.get('points')
            crit = [str(r.get('criterion', '')).strip().lower() for r in rub]
            if not rub or any(not c for c in crit) or any(not isinstance(r.get('points'), (int, float)) or r['points'] <= 0 for r in rub):
                chk('rubric', 'BLOCKED', 'G1.ITEM_RUBRIC', 'major', 'rubric missing or criteria without positive points')
            elif len(set(crit)) < len(crit) or any(not str(r.get('evidence_of', '')).strip() for r in rub):
                chk('rubric', 'FAIL', 'G1.ITEM_RUBRIC', 'major', 'rubric criteria are not discriminating (duplicate or no '
                    'observable evidence_of per criterion)')
            elif pts and abs(sum(r['points'] for r in rub) - pts) > 1e-9:
                chk('rubric', 'FAIL', 'G1.ITEM_RUBRIC', 'major', 'rubric points do not sum to item points')
            elif pts and pts > 1 and len(rub) < 2:
                chk('rubric', 'FAIL', 'G1.ITEM_RUBRIC', 'major', 'scored item without partial credit (single all-or-nothing criterion)')
            else:
                chk('rubric', 'PASS', 'G1.ITEM_RUBRIC', '', '')
        # ---- G1 transfer
        if a.get('transfer_relation') or a.get('difficulty') == 'transfer':
            R.ran('G1.ITEM_TRANSFER', aid)
            v = a.get('variation') if isinstance(a.get('variation'), dict) else {}
            origin_ok = v.get('from_ref') in blocks or v.get('from_ref') in pkg or v.get('from_ref') in exam_ids
            if op in ('RECALL', 'DEFINE') or set(res['demanded_operations']) <= {'RECALL', 'DEFINE'}:
                chk('transfer', 'FAIL', 'G1.ITEM_TRANSFER', 'major', 'transfer label on a recall/definition item', [],
                    'relabel difficulty or write a real transfer task')
            elif not origin_ok or not v.get('changed'):
                chk('transfer', 'FAIL', 'G1.ITEM_TRANSFER', 'major', 'transfer without resolvable origin or stated variation',
                    [v.get('from_ref')], 'state variation.from_ref and variation.changed')
            else:
                chk('transfer', 'PENDING', 'G1.ITEM_TRANSFER', 'info', 'novelty and difficulty of transfer need independent review',
                    [v['from_ref']], 'independent review')
        # ---- G2 evidence chain
        R.ran('G2.EVIDENCE_CHAIN', aid)
        prov = a.get('provenance')
        basis = [blocks[b] for b in (a.get('basis_block_ids') or a.get('refers_to_block_ids') or []) if b in blocks]
        good = [b for b in basis if b.get('kind') not in NON_SUBSTANTIVE and set(b.get('kc_ids', [])) & set(a.get('kc_ids', []))
                and b.get('source_refs') and set(b['source_refs']) <= pkg]
        refs = a.get('source_refs') or []
        if prov not in ITEM_PROVENANCE:
            chk('evidence', 'BLOCKED', 'G2.EVIDENCE_CHAIN', 'major', 'item provenance missing (COURSE_SOURCE|EXAM_ADAPTED|AUTHOR_CREATED|VERIFIED_SUPPLEMENT)')
        elif any(r not in pkg for r in refs):
            chk('evidence', 'FAIL', 'G2.EVIDENCE_CHAIN', 'blocker', 'item cites unknown source anchor', [r for r in refs if r not in pkg])
        elif prov in ('COURSE_SOURCE', 'EXAM_ADAPTED') and not refs:
            chk('evidence', 'BLOCKED', 'G2.EVIDENCE_CHAIN', 'major', f'{prov} item without source_refs')
        elif not good and not refs:
            chk('evidence', 'BLOCKED', 'G2.EVIDENCE_CHAIN', 'major', 'only link is to a non-substantive or unanchored block '
                f"({[b.get('block_id') for b in basis] or 'none'}); not evidence for the task", [b.get('block_id') for b in basis],
                'link the substantive, anchored block of the same KC')
        else:
            chk('evidence', 'PENDING', 'G2.EVIDENCE_CHAIN', 'info', 'chain resolves to anchors; semantic support not confirmed',
                refs + [r for b in good for r in b['source_refs']])
        res['finding_ids'] = [f['finding_id'] for f in R.findings[start:]]
        st = set(res['checks'].values())
        res['machine_checks'] = 'FAILED' if st & {'FAIL', 'BLOCKED'} else 'PASSED'
        res['status'] = 'BLOCKED' if st & {'FAIL', 'BLOCKED'} else 'PENDING_SEMANTIC_REVIEW'
        results.append(res)
    return results


INSTANCE_KINDS = {'WORKED_EXAMPLE', 'SUBSUMPTION', 'CASE', 'COUNTEREXAMPLE'}
NUMBER = re.compile(r'(?<![\w.,])\d[\d.,\u202f\u00a0]*\d|(?<![\w.,])\d')


def _numkey(s):
    return re.sub(r'[.,\s\u202f\u00a0]', '', s)


def _numbers_in(text):
    """(value, decimals) for numbers in English (1,234.5) or German (1.234,5) notation, or plain.
    Both readings are kept when ambiguous; the caller accepts a match under either."""
    out = []
    for m in NUMBER.finditer(text):
        raw = m.group(0)
        r = raw.replace('\u202f', '').replace('\u00a0', '').replace(' ', '')
        # B12: a minus sign directly before the number belongs to it ("= -130", "−130"); without this no negative
        # result could ever be found in a solution. A minus between two numbers ("50 - 30") is an operator.
        before = text[:m.start()]
        neg = before.endswith(('-', '−', '–')) and (len(before) == 1 or before[-2] in ' \t\n(=,[{:;/')
        for cand in (r.replace(',', ''), r.replace('.', '').replace(',', '.')):
            try:
                v = float(cand.replace('−', '-'))
                out.append((-v if neg else v, len(cand.split('.')[1]) if '.' in cand else 0))
            except ValueError:
                pass
    return out


def _states(text, val):
    """True if the text states val, rounded to the precision it is written with (44,467 states 44,466.67)."""
    return any(abs(v - val) <= 1e-9 * max(1, abs(val)) or abs(round(val, d) - v) <= 1e-9 * max(1, abs(v)) for v, d in _numbers_in(text))


def quality_report(ast_, chapter, plan, manifest):
    R = Report()
    by = {e['element_id']: e for e in manifest['elements']}
    src = {s['source_id']: s for s in manifest['sources']}
    pkg = set(chapter['source_package']['element_ids'])
    kcs = {k['kc_id']: k for k in plan['competencies']}
    blocks = {b.get('block_id'): b for b in ast_.get('blocks', [])}
    profiles = set(plan['domain_profile']['active_profiles'])
    # ---- G0
    g0 = check_content_ast(ast_, chapter, plan, manifest)
    R.ran('G0.STRUCTURE', 'check_content_ast')
    for cls in ('structural', 'evidence', 'operational'):
        for f in g0[cls]:
            R.add('G0.STRUCTURE', f['object'], 'FAIL', 'major', f"{cls}:{f['code']} {f['detail']}".strip())
    items = _items_results(ast_, chapter, plan, manifest, R, kcs, blocks, pkg, by)
    # KC-level operation coverage by a machine-passing item
    R.ran('G1.ITEM_OPERATION', 'kc_coverage')
    for kid in ast_.get('kc_ids', []):
        ops = set(kcs[kid]['operations']) if kid in kcs else set()
        if ops & {'DERIVE', 'PROVE', 'SUBSUME', 'APPLY', 'CALCULATE', 'IMPLEMENT'}:
            ok = [r['item_id'] for r in items if r['covers_kc_operation'].get(kid) and r['machine_checks'] == 'PASSED']
            if not ok:
                R.add('G1.ITEM_OPERATION', kid, 'FAIL', 'blocker', f'no specified, solvable item demands {sorted(ops)}',
                      [r['item_id'] for r in items if kid in r['kc_ids']], 'write an item that demands the operation')
    # ---- G2 source support per block
    for bid, b in blocks.items():
        if not b.get('source_refs'):
            continue
        R.ran('G2.SOURCE_SUPPORT', bid)
        valid = [r for r in b['source_refs'] if r in by]
        level = source_support(' '.join(str(b.get(k, '')) for k in ('title', 'body')) + ' ' +
                               ' '.join(str(s.get('statement', '')) for s in b.get('steps') or []), [by[r]['normalized_text'] for r in valid]) \
            if valid else 'UNVERIFIED'
        human = [r for r in ast_.get('reviews', []) if r.get('assertion_id') == bid and r.get('reviewer_kind') == 'HUMAN_EXPERT'
                 and r.get('verdict') == 'SUPPORTED' and all(r.get(f) for f in REVIEW_FIELDS)]
        level = 'SOURCE_SUPPORT_CONFIRMED' if human else level
        b_support = {'UNVERIFIED': 'FAIL', 'SOURCE_EXISTS': 'PENDING', 'SOURCE_SUPPORT_LEXICAL': 'PENDING',
                     'SOURCE_SUPPORT_CONFIRMED': 'PASS'}[level]
        R.add('G2.SOURCE_SUPPORT', bid, b_support, 'info' if b_support != 'FAIL' else 'major',
              f'support level {level}' + ('' if human else ' (anchor existence/lexical overlap is not semantic support)'),
              valid, '' if human else 'semantic source review by an independent reviewer')
    # ---- G3 review records and labels
    R.ran('G3.REVIEW_RECORDS', 'reviews'); R.ran('G3.STATUS_LABELS', 'all status fields')
    reviews = ast_.get('reviews', [])
    test_only = any(r.get('reviewer_kind') == 'TEST_FIXTURE' for r in reviews) or ast_.get('content_origin') == 'SYNTHETIC_FIXTURE'
    for r in reviews:
        missing = [f for f in REVIEW_FIELDS if not r.get(f)]
        if missing or r.get('reviewer_kind') not in REVIEWER_KINDS:
            R.add('G3.REVIEW_RECORDS', r.get('review_id') or r.get('assertion_id'), 'FAIL', 'major',
                  f'incomplete review record (missing {missing})', [], 'record artefact id, reviewer, assertion, evidence, verdict, time, build')
        elif r.get('assertion_id') not in blocks and r.get('assertion_id') not in {a.get('item_id') for a in ast_['assessments']}:
            R.add('G3.REVIEW_RECORDS', r['review_id'], 'FAIL', 'major', 'review refers to an unknown assertion')
    gen = (ast_.get('generation') or {}).get('provider_id')
    for b in blocks.values():
        st = b.get('claim_support_status')
        if st and st.startswith('MODEL_REVIEWED'):
            rec = [r for r in reviews if r.get('assertion_id') == b.get('block_id') and r.get('reviewer_kind') in ('MODEL', 'TEST_FIXTURE')
                   and all(r.get(f) for f in REVIEW_FIELDS)]
            if not rec:
                R.add('G3.REVIEW_RECORDS', b.get('block_id'), 'FAIL', 'major', f'{st} without a backing review record')
            elif any(r.get('reviewer_id') == gen for r in rec):
                R.add('G3.REVIEW_RECORDS', b.get('block_id'), 'PENDING', 'minor', 'reviewed by the same provider that authored it '
                      '(self-review): recorded, confers no support', [r['review_id'] for r in rec], 'independent review')

    def scan(obj, path=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and ('status' in k or k in ('verdict_label', 'release', 'release_status')) and v.upper() in FORBIDDEN_LABELS \
                        and not (k == 'verdict' or path.startswith('reviews')):
                    R.add('G3.STATUS_LABELS', f'{path}.{k}', 'FAIL', 'blocker', f'forbidden label {v}: no model or engine step can '
                          'verify, confirm or release content', [], 'reset to PENDING_SEMANTIC_REVIEW/DRAFT')
                scan(v, f'{path}.{k}' if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f'{path}[{i}]')
    scan({k: v for k, v in ast_.items() if k not in ('quality_report', 'gate_report', 'semantic_decisions')})
    if ast_.get('academic_status') not in (None, 'ACADEMIC_RELEASE_NOT_TESTED', 'ACADEMIC_NO_GO', 'EXTERNAL_REVIEW_PENDING'):
        R.add('G3.STATUS_LABELS', 'academic_status', 'FAIL', 'blocker', f"self-certification: academic_status={ast_['academic_status']}")
    # ---- G4
    shaped = [b for b in blocks.values() if b.get('shape_checks')]
    if shaped:
        for b in shaped:
            R.ran('G4.DIMENSIONS', b['block_id'])
            errs = check_shapes(b['shape_checks'])
            R.add('G4.DIMENSIONS', b['block_id'], 'FAIL' if errs else 'PASS', 'major' if errs else 'info',
                  '; '.join(errs) or 'dimension-consistent (only shapes checked; not a proof of the equation)',
                  [e['lhs'] + ' = ' + e['rhs'] for e in b['shape_checks'].get('equations', [])])
    else:
        R.na('G4.DIMENSIONS', 'no block declares shape_checks')
    nums = [(s, c) for s in ast_['solutions'] for c in s.get('numeric_checks') or []]
    for s, c in nums:
        R.ran('G4.NUMERIC', s.get('solution_id'))
        try:
            ok = abs(evaluate_numeric(c['expression'], c.get('constants', {})) - float(c['expected'])) <= 1e-9 * max(1, abs(float(c['expected'])))
            R.add('G4.NUMERIC', s.get('solution_id'), 'PASS' if ok else 'FAIL', 'info' if ok else 'blocker',
                  f"{c['expression']} {'=' if ok else '!='} {c['expected']} (recomputes this expression only)", [c['expression']])
        except Exception as e:
            R.add('G4.NUMERIC', s.get('solution_id'), 'FAIL', 'major', f'numeric check not evaluable: {e}')
    calc_items = [a for a in ast_['assessments'] if a.get('required_operation') in ('CALCULATE', 'APPLY')]
    if not nums:
        (R.nt if calc_items else R.na)('G4.NUMERIC', 'calculation items without numeric_checks' if calc_items else 'no calculation items')
    for a in calc_items:
        s = next((x for x in ast_['solutions'] if x.get('solution_id') == a.get('solution_id')), {})
        if not s.get('numeric_checks'):
            R.add('G4.NUMERIC', a['item_id'], 'NOT_TESTED', 'minor', 'no numeric check declared for a calculation item', [],
                  'add numeric_checks or blind re-calculation')
    # B6.5 independent consistency: the model may not check one number and write another.
    if nums:
        for s, c in nums:
            R.ran('G4.ANSWER_CONSISTENCY', s.get('solution_id'))
            try:
                val = float(c['expected'])
            except (TypeError, ValueError):
                R.add('G4.ANSWER_CONSISTENCY', s.get('solution_id'), 'FAIL', 'major', f"expected value not numeric: {c.get('expected')!r}"); continue
            text = ' '.join([str(s.get('answer', ''))] + [str(x.get('statement', '')) for x in s.get('steps') or [] if isinstance(x, dict)])
            ok = _states(text, val)
            R.add('G4.ANSWER_CONSISTENCY', s.get('solution_id'), 'PASS' if ok else 'FAIL', 'info' if ok else 'major',
                  f"recomputed {c['expected']} {'is' if ok else 'is NOT'} stated in answer/steps", [c['expression']],
                  '' if ok else 'state the recomputed value in the answer or fix the check')
    else:
        R.na('G4.ANSWER_CONSISTENCY', 'no numeric checks declared')
    # B6.5 source-number fidelity: a block claimed as course content may not introduce numbers its anchors lack.
    course = [b for b in blocks.values() if b.get('provenance') == 'COURSE_SOURCE']
    if course:
        for b in course:
            R.ran('G5.SOURCE_NUMBERS', b.get('block_id'))
            text = ' '.join(str(b.get(k) or '') for k in ('title', 'body', 'problem', 'result', 'interpretation')) + ' ' + \
                ' '.join(str(x.get('statement', '')) for x in b.get('steps') or [] if isinstance(x, dict))
            anchor = ' '.join(by[r].get('text') or '' for r in b.get('source_refs') or [] if r in by)
            have = {_numkey(x) for x in NUMBER.findall(anchor)}
            missing = sorted({x for x in NUMBER.findall(text) if len(_numkey(x)) >= 2 and _numkey(x) not in have})
            instance = b.get('kind') in INSTANCE_KINDS   # worked examples/cases carry new instance data by design
            status = 'PASS' if not missing else 'NOT_TESTED' if instance else 'FAIL'
            R.add('G5.SOURCE_NUMBERS', b.get('block_id'), status, 'info' if not missing else 'minor' if instance else 'major',
                  ('all numbers occur in the anchors' if not missing else
                   ('instance numbers not in the source (new data by design?): ' if instance else 'numbers not in the anchored source: ') + ', '.join(missing[:12])),
                  b.get('source_refs', []), '' if not missing else 'confirm these are new instance data, not altered source values' if instance
                  else 'mark the block AUTHOR_INFERENCE or anchor the numbers')
    else:
        R.na('G5.SOURCE_NUMBERS', 'no COURSE_SOURCE block')
    # B6.6: a correct number is not a correct derivation. Written step arithmetic is checked independently of the
    # model's numeric_checks; the set-up of a calculation is never machine-verified and stays NOT_TESTED.
    calc_texts = []
    for b in blocks.values():
        if b.get('kind') in ('WORKED_EXAMPLE', 'CALCULATION', 'DERIVATION', 'MODEL') or b.get('steps'):
            calc_texts.append((b.get('block_id'), [b.get('problem'), b.get('body')] +
                               [x.get('statement') for x in b.get('steps') or [] if isinstance(x, dict)] + [b.get('result')]))
    for so in ast_['solutions']:
        calc_texts.append((so.get('solution_id'), [x.get('statement') for x in so.get('steps') or [] if isinstance(x, dict)] + [so.get('answer')]))
    any_eq = False
    for oid, texts in calc_texts:
        res = check_steps([str(t) for t in texts if t])
        if not res:
            continue
        any_eq = True; R.ran('G4.STEP_ARITHMETIC', oid)
        for r in res:
            R.add('G4.STEP_ARITHMETIC', oid, r['status'], 'info' if r['status'] == 'PASS' else 'major' if r['status'] == 'FAIL' else 'minor',
                  r['detail'] + ' [scope: ' + STEP_SCOPE + ']', [r['equation']], 'fix the step or the stated result' if r['status'] == 'FAIL' else '')
        R.add('G4.DERIVATION_SETUP', oid, 'NOT_TESTED', 'major', 'whether this relation/approach is the right one for the problem '
              'is not machine-checked; arithmetic consistency is not a correct derivation', [], 'independent subject review')
    if not any_eq:
        R.na('G4.STEP_ARITHMETIC', 'no written equation chains')
        R.na('G4.DERIVATION_SETUP', 'no calculation or derivation steps')
    else:
        R.nt('G4.DERIVATION_SETUP', 'no subject reviewer in the offline pipeline')
    proofs = [b for b in blocks.values() if b.get('kind') in ('PROOF', 'DERIVATION', 'SUBSUMPTION')]
    if proofs:
        for b in proofs:
            R.add('G4.PROOF_VALIDITY', b['block_id'], 'NOT_TESTED', 'major', 'logical/legal validity of the argument is not '
                  'machine-checked; no CAS/prover guarantee', b.get('source_refs', []), 'independent expert review')
        R.nt('G4.PROOF_VALIDITY', 'no prover/expert in the offline pipeline')
    else:
        R.na('G4.PROOF_VALIDITY', 'no proof, derivation or subsumption block')
    formal = [b for b in blocks.values() if b.get('kind') in {'THEOREM', 'PROOF', 'DERIVATION', 'MODEL'}]
    if formal:
        for b in formal:
            R.ran('G4.DOMAIN_FORMAL', b['block_id'])
            if not isinstance(b.get('assumptions'), list) or not b['assumptions']:
                R.add('G4.DOMAIN_FORMAL', b['block_id'], 'FAIL', 'major', 'formal block without stated assumptions/domain of validity')
            else:
                R.add('G4.DOMAIN_FORMAL', b['block_id'], 'PENDING', 'info', 'assumptions stated; adequacy needs review', b['assumptions'])
    else:
        R.na('G4.DOMAIN_FORMAL', 'no theorem/proof/derivation/model block')
    subs = [b for b in blocks.values() if b.get('kind') == 'SUBSUMPTION']
    if subs or 'law' in profiles:
        for b in subs:
            R.ran('G4.DOMAIN_LAW', b['block_id'])
            bad = [i for i, s in enumerate(b.get('steps') or []) if not s.get('element') or not s.get('fact')]
            if not b.get('norm_refs') or bad:
                R.add('G4.DOMAIN_LAW', b['block_id'], 'FAIL', 'major', 'subsumption step without norm, Tatbestandsmerkmal or '
                      f'Sachverhaltsbezug (steps {bad})')
            else:
                R.add('G4.DOMAIN_LAW', b['block_id'], 'PASS', 'info', 'norm, element and fact named in every step (structure only)',
                      b['norm_refs'])
            R.add('G4.DOMAIN_LAW', b['block_id'], 'NOT_TESTED', 'major', 'norm wording and current legal status not checked '
                  'against an official text', b.get('norm_refs', []), 'check official norm text and date')
        if not subs:
            R.add('G4.DOMAIN_LAW', ast_['chapter_id'], 'PENDING', 'minor', 'law profile active but no subsumption block')
    else:
        R.na('G4.DOMAIN_LAW', 'no law signal and no subsumption block')
    impl = [a for a in ast_['assessments'] if a.get('required_operation') == 'IMPLEMENT']
    if impl:
        for a in impl:
            R.ran('G4.DOMAIN_COMPUTING', a['item_id'])
            s = next((x for x in ast_['solutions'] if x.get('solution_id') == a.get('solution_id')), {})
            tests = s.get('tests') or []
            if not tests or any(not t.get('input') or 'expected' not in t for t in tests):
                R.add('G4.DOMAIN_COMPUTING', a['item_id'], 'FAIL', 'major', 'implementation item without test cases (input/expected)')
            else:
                R.add('G4.DOMAIN_COMPUTING', a['item_id'], 'PASS', 'info', f'{len(tests)} test case(s) stated (not executed)')
            R.add('G4.DOMAIN_COMPUTING', a['item_id'], 'NOT_TESTED', 'major', 'reference code not executed (requires isolated runtime, P4)')
    else:
        R.na('G4.DOMAIN_COMPUTING', 'no implementation item')
    calc_blocks = [b for b in blocks.values() if b.get('kind') in ('CALCULATION', 'WORKED_EXAMPLE') and
                   set(b.get('kc_ids', [])) & {k for k in ast_['kc_ids'] if k in kcs and set(kcs[k]['operations']) & {'CALCULATE', 'APPLY'}}]
    if calc_blocks:
        for b in calc_blocks:
            R.ran('G4.DOMAIN_QUANT', b['block_id'])
            if not b.get('assumptions') or not str(b.get('interpretation', '')).strip():
                R.add('G4.DOMAIN_QUANT', b['block_id'], 'FAIL', 'major', 'calculation without stated assumptions or interpretation')
    else:
        R.na('G4.DOMAIN_QUANT', 'no calculation/application competency in this chapter')
    # ---- G5 source fidelity mapped to blocks/KCs
    for bid, b in blocks.items():
        refs = [r for r in b.get('source_refs', []) if r in by]
        if not refs:
            continue
        R.ran('G5.SOURCE_FIDELITY', bid)
        weak = [r for r in refs if by[r]['status'] != 'ok']
        if weak and len(weak) == len(refs) and b.get('kind') in SUBSTANTIVE_FORMAL:
            R.add('G5.SOURCE_FIDELITY', bid, 'BLOCKED', 'blocker', f"essential block for {b.get('kc_ids')} rests only on "
                  'partial/uncertain source elements', weak, 'resolve the source element (render/OCR/review) first')
        elif weak:
            R.add('G5.SOURCE_FIDELITY', bid, 'PENDING', 'minor', 'some anchors are partial/uncertain; block also has reliable anchors', weak)
    for s in ast_.get('sources', []):
        if s.get('status') != 'extracted':
            used = [bid for bid, b in blocks.items() if any(by.get(r, {}).get('source_id') == s['source_id'] for r in b.get('source_refs', []))]
            R.ran('G5.SOURCE_FIDELITY', s['source_id'])
            R.add('G5.SOURCE_FIDELITY', s['source_id'], 'PENDING', 'info', f"source is {s['status']}; affects only blocks {used}" if used
                  else f"source is {s['status']}; no block relies on it", used)
    for f in ast_.get('figures', []):
        fid = f.get('figure_id'); R.ran('G5.FIGURES', fid)
        el = by.get(f.get('source_element_id')) if f.get('source_element_id') else None
        linked = (el.get('structure') or {}).get('linked_source_id') if el and isinstance(el.get('structure'), dict) else None
        asset_ok = bool(el and ((el.get('asset') or {}).get('path') or (linked and any(by[x].get('asset') for x in src[linked]['element_ids']))))
        essential = f.get('necessity') == 'ESSENTIAL'
        if f.get('status') in ('SOURCE_ASSET_REUSED', 'REDRAW_FROM_SOURCE_SPEC'):
            if f['status'] == 'SOURCE_ASSET_REUSED' and not asset_ok:
                R.add('G5.FIGURES', fid, 'FAIL', 'blocker' if essential else 'major', 'reused figure has no resolvable asset',
                      [f.get('source_element_id')], 'provide the file or mark OPEN_NOT_GENERATED')
            missing = [k for k in ('caption', 'alt_text', 'review_status') if not str(f.get(k, '')).strip()]
            if missing:
                R.add('G5.FIGURES', fid, 'FAIL', 'major', f'used figure without {missing}')
            uncertain = el and (el['status'] != 'ok' or (linked and src[linked]['visual_status'] in ('VISUAL_UNCERTAIN', 'RENDER_UNAVAILABLE')))
            if uncertain and f.get('review_status') != 'HUMAN_VISUAL_REVIEW_PASSED':
                R.add('G5.FIGURES', fid, 'PENDING' if not essential else 'BLOCKED', 'major', 'image content not understood by '
                      'the pipeline; reuse needs visual review', [f.get('source_element_id')], 'visual review')
        elif f.get('status') == 'OPEN_NOT_GENERATED':
            R.add('G5.FIGURES', fid, 'BLOCKED' if essential else 'PENDING', 'major' if essential else 'minor',
                  'necessary visual not generated' if essential else 'supplementary visual open', [f.get('source_element_id')],
                  'create/verify the figure')
    if not ast_.get('figures'):
        R.na('G5.FIGURES', 'chapter uses no figures')
    conflicts = [n for n in plan['notation_registry'] if n['status'] != 'CONSISTENT' and n['notation_id'] in chapter.get('notation_ids', [])]
    if conflicts:
        mine = {x.get('notation_id'): x for x in ast_.get('notation', [])}
        for n in conflicts:
            R.ran('G5.NOTATION', n['notation_id'])
            m = mine.get(n['notation_id'])
            keys = [terms(x) for x in n['meanings']]
            mixed = m and sum(1 for k in keys if k and k <= terms(str(m.get('meaning', '')))) > 1
            res = (m or {}).get('resolution') or {}
            if not m:
                R.add('G5.NOTATION', n['notation_id'], 'FAIL', 'major', f"notation conflict for {n['symbol']} dropped from chapter")
            elif mixed:
                R.add('G5.NOTATION', n['notation_id'], 'FAIL', 'major', f"conflicting meanings of {n['symbol']} merged into one entry")
            elif m.get('status') == 'CONSISTENT' and not (res.get('basis') == 'OFFICIAL_PRECEDENCE' and res.get('evidence_refs')
                                                          and n['authority_resolution'].get('preferred_meaning')):
                R.add('G5.NOTATION', n['notation_id'], 'FAIL', 'major', f"conflict for {n['symbol']} marked CONSISTENT without "
                      'evidenced official precedence')
            else:
                R.add('G5.NOTATION', n['notation_id'], 'PENDING', 'minor', f"conflict for {n['symbol']} visible: {n['meanings']}",
                      [u['element_id'] for u in n['uses']], 'decide notation with the lecturer/official source')
    else:
        R.na('G5.NOTATION', 'no notation conflict in this chapter')
    for g, why in (('G1.ITEM_TRANSFER', 'no item carries a transfer label'), ('G2.SOURCE_SUPPORT', 'no block cites source anchors'),
                   ('G5.SOURCE_FIDELITY', 'no block cites source anchors'), ('G3.REVIEW_RECORDS', 'no review records')):
        if not R.executed[g] and not any(f['gate_id'] == g for f in R.findings):
            R.na(g, why)
    if not ast_['assessments']:
        for g in [g for g in GATES if g.startswith('G1.') or g == 'G2.EVIDENCE_CHAIN']:
            R.na(g, 'chapter has no assessment items (G0 reports missing coverage)')
    return _assemble(R, items, g0, test_only)


def _assemble(R, items, g0, test_only):
    gates = {}
    for g in GATES:
        fs = [f for f in R.findings if f['gate_id'] == g]
        if g in R.not_applicable and not fs:
            gates[g] = {'status': 'NOT_APPLICABLE', 'reason': R.not_applicable[g], 'checks_executed': []}
            continue
        if not R.executed[g] and not fs:
            gates[g] = {'status': 'NOT_TESTED', 'reason': R.not_tested.get(g, 'gate not executed for this content'), 'checks_executed': []}
            continue
        st = {f['status'] for f in fs}
        # NOT_TESTED is never read as PASS: partially tested gates are PENDING.
        status = next((x for x in ('FAIL', 'BLOCKED', 'PENDING') if x in st), None) or \
            (('PENDING' if 'PASS' in st else 'NOT_TESTED') if 'NOT_TESTED' in st else 'PASS')
        gates[g] = {'status': status, 'reason': R.not_tested.get(g, f"{len(fs)} finding(s)" if fs else 'all executed checks passed'),
                    'checks_executed': R.executed[g] or ['findings only']}
    hard = [f for f in R.findings if f['status'] in ('FAIL', 'BLOCKED')]
    structural = 'STRUCTURAL_PASS' if g0['technical_status'] == 'PASS' else 'STRUCTURAL_FAIL'
    evidence = 'EVIDENCE_FAIL' if any(f['gate_id'].startswith('G2') and f['status'] in ('FAIL', 'BLOCKED') for f in R.findings) else 'EVIDENCE_PENDING'
    semantic = 'SEMANTIC_PENDING'
    machine = 'MACHINE_CHECKS_FAILED' if hard else 'MACHINE_CHECKS_PASSED'
    academic = 'ACADEMIC_NO_GO' if hard else 'ACADEMIC_RELEASE_NOT_TESTED'
    return {'schema': REPORT_SCHEMA, 'gates': gates, 'findings': R.findings, 'assessment_quality': items,
            'stages': [structural, evidence, semantic, machine, academic],
            'technical_status': 'TECHNICAL_GO' if structural == 'STRUCTURAL_PASS' else 'TECHNICAL_NO_GO',
            'machine_quality_status': machine, 'semantic_status': semantic, 'academic_status': academic,
            'content_go': False, 'release_go': False, 'external_review': 'EXTERNAL_REVIEW_PENDING',
            'test_only': test_only,
            'verification_scope': {'numeric_values': 'G4.NUMERIC/G4.ANSWER_CONSISTENCY: declared expressions recompute and are stated',
                                   'step_arithmetic': 'G4.STEP_ARITHMETIC: ' + STEP_SCOPE,
                                   'derivation_setup': 'NOT_VERIFIED (G4.DERIVATION_SETUP, G4.PROOF_VALIDITY)',
                                   'subject_matter': 'NOT_VERIFIED: no machine check is a subject-matter verification'},
            'counts': {s: sum(f['status'] == s for f in R.findings) for s in sorted(FINDING_STATUS)},
            'note': 'Automatic gates can only block or leave content pending. CONTENT_GO/RELEASE_GO require a documented '
                    'independent expert review and an explicit owner decision outside the engine.'}


def validate_gate_report(rep):
    """Reject reports that omit gates, swallow negatives or treat NOT_TESTED as PASS."""
    problems = []
    if rep.get('schema') != REPORT_SCHEMA:
        problems.append('wrong schema')
    for g in GATES:
        x = rep.get('gates', {}).get(g)
        if not x:
            problems.append(f'gate {g} missing'); continue
        if x.get('status') not in FINDING_STATUS:
            problems.append(f'gate {g}: invalid status {x.get("status")}')
        if x.get('status') == 'PASS' and not x.get('checks_executed'):
            problems.append(f'gate {g}: PASS without executed checks')
        if x.get('status') in ('NOT_APPLICABLE', 'NOT_TESTED') and not x.get('reason'):
            problems.append(f'gate {g}: {x.get("status")} without reason')
        fs = [f for f in rep.get('findings', []) if f.get('gate_id') == g]
        worst = min((f['status'] for f in fs if f['status'] in STATUS_ORDER[:3]), key=STATUS_ORDER.index, default=None)
        if worst and STATUS_ORDER.index(x.get('status', 'PASS')) > STATUS_ORDER.index(worst) and x.get('status') in STATUS_ORDER:
            problems.append(f'gate {g}: status {x.get("status")} hides {worst} finding')
    for f in rep.get('findings', []):
        if any(k not in f for k in ('gate_id', 'object_id', 'status', 'severity', 'reason', 'evidence_refs', 'recommended_action')):
            problems.append(f"finding {f.get('finding_id')} incomplete")
    hard = any(f.get('status') in ('FAIL', 'BLOCKED') for f in rep.get('findings', []))
    if hard and rep.get('machine_quality_status') != 'MACHINE_CHECKS_FAILED':
        problems.append('negative findings swallowed by overall status')
    if rep.get('academic_status') not in ('ACADEMIC_NO_GO', 'ACADEMIC_RELEASE_NOT_TESTED') or rep.get('content_go') or rep.get('release_go'):
        problems.append('automatic report claims content/release go')
    if hard and rep.get('academic_status') != 'ACADEMIC_NO_GO':
        problems.append('negative findings but academic status not NO_GO')
    return problems
