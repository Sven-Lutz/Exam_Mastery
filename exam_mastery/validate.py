from __future__ import annotations
import ast, math, collections
from .common import ContractError, enforce_keys

ALLOWED_AST=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Constant,ast.Name,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow,ast.UAdd,ast.USub,ast.Load)

def numeric_ast(expression: str, names):
    if len(expression)>180: raise ContractError('Expression too long')
    try: tree=ast.parse(expression,mode='eval')
    except SyntaxError as e: raise ContractError('Invalid arithmetic expression') from e
    for node in ast.walk(tree):
        if not isinstance(node,ALLOWED_AST): raise ContractError('Disallowed expression node '+type(node).__name__)
        if isinstance(node,ast.Name) and node.id not in names: raise ContractError('Unknown variable '+node.id)
        if isinstance(node,ast.Constant) and (not isinstance(node.value,(int,float)) or isinstance(node.value,bool)):
            raise ContractError('Nonnumeric value in expression')
        if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Pow):
            if not isinstance(node.right,ast.Constant) or abs(node.right.value)>8: raise ContractError('Exponent not safely bounded')
    return tree

def check_numeric_interval(expression,env):
    """Conservative interval arithmetic rejects possible poles anywhere in slider range."""
    tree=numeric_ast(expression,set(env))
    def bounds(node):
        if isinstance(node,ast.Expression):return bounds(node.body)
        if isinstance(node,ast.Constant):return (node.value,node.value)
        if isinstance(node,ast.Name):return env[node.id]
        if isinstance(node,ast.UnaryOp):
            lo,hi=bounds(node.operand)
            return (-hi,-lo) if isinstance(node.op,ast.USub) else (lo,hi)
        a,b=bounds(node.left);c,d=bounds(node.right)
        if isinstance(node.op,ast.Add):lo,hi=a+c,b+d
        elif isinstance(node.op,ast.Sub):lo,hi=a-d,b-c
        elif isinstance(node.op,ast.Mult):lo,hi=min(a*c,a*d,b*c,b*d),max(a*c,a*d,b*c,b*d)
        elif isinstance(node.op,ast.Div):
            if c<=0<=d:raise ContractError('Possible zero denominator in numeric lab interval; choose safer range or quiz')
            lo,hi=min(a/c,a/d,b/c,b/d),max(a/c,a/d,b/c,b/d)
        else:
            power=c
            if not float(power).is_integer() and a<0:raise ContractError('Possible complex power in numeric lab')
            if power<0 and a<=0<=b:raise ContractError('Possible pole in negative power')
            vals=[a**power,b**power]
            if a<=0<=b and power>0:vals.append(0)
            lo,hi=min(vals),max(vals)
        if not math.isfinite(lo) or not math.isfinite(hi) or max(abs(lo),abs(hi))>1e15:raise ContractError('Unsafe numeric interval')
        return lo,hi
    return bounds(tree)

def evaluate_numeric(expression,env):
    tree=numeric_ast(expression,set(env))
    def ev(node):
        if isinstance(node,ast.Expression): return ev(node.body)
        if isinstance(node,ast.Constant): return node.value
        if isinstance(node,ast.Name): return float(env[node.id])
        if isinstance(node,ast.UnaryOp): return ev(node.operand)*(1 if isinstance(node.op,ast.UAdd) else -1)
        a=ev(node.left); b=ev(node.right)
        if isinstance(node.op,ast.Add): x=a+b
        elif isinstance(node.op,ast.Sub): x=a-b
        elif isinstance(node.op,ast.Mult): x=a*b
        elif isinstance(node.op,ast.Div): x=a/b
        elif isinstance(node.op,ast.Pow): x=a**b
        else: raise ContractError('operator')
        if not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>1e15: raise ContractError('Unstable numeric result')
        return x
    return ev(tree)

def _locators(manifest): return {c['locator'] for c in manifest['chunks']}

def _refs(obj,valid,at):
    refs=obj.get('source_refs',[])
    if not isinstance(refs,list): raise ContractError(f'{at}: source_refs must be list')
    if any(not isinstance(r,str) or r not in valid for r in refs): raise ContractError(f'{at}: invalid source locator {refs}')
    if not refs: raise ContractError(f'{at}: missing source refs')

def check_blueprint(bp,manifest):
    enforce_keys(bp,{'title','knowledge_operations','skills','risk','competencies','units','interaction_choice'},'blueprint')
    ids=set(); loc=_locators(manifest)
    if not bp['competencies'] or not bp['units']: raise ContractError('Course has no measurable competencies or units')
    for c in bp['competencies']:
        enforce_keys(c,{'id','statement','operation','source_refs'},'competency')
        _refs(c,loc,c['id']); ids.add(c['id'])
        if not c['operation'].strip() or not c['statement'].strip(): raise ContractError('Empty operation or competency')
    if len(ids)!=len(bp['competencies']): raise ContractError('Duplicate competency IDs')
    for u in bp['units']:
        if not set(u.get('competency_ids',[]))<=ids: raise ContractError('Unit references unknown competency')
    if bp['risk'] not in ('low','medium','high'): raise ContractError('Invalid risk classification')
    return ids

def check_author(author,manifest):
    from .math_publishing import validate_registry,validate_renderability,TOKEN
    math_errors=[]
    for verify in (lambda:validate_registry(author.get('mathematics',[]),[c['locator'] for c in manifest['chunks']]),lambda:validate_renderability(author.get('mathematics',[]))):
        try:verify()
        except (ContractError,ValueError,TypeError,KeyError) as error:math_errors.append(str(error))
    if math_errors:raise ContractError('; '.join(math_errors))
    known={r['id'] for r in author.get('mathematics',[])}
    import json
    for match in TOKEN.finditer(json.dumps(author,ensure_ascii=False)):
        if match[2] not in known:raise ContractError('Undefined mathematical reference '+match[2])
    enforce_keys(author,{'claims','sections','limitations'},'author')
    loc=_locators(manifest)
    if len(author['sections'])<2: raise ContractError('Instructional manuscript too thin: fewer than 2 sections')
    for c in author['claims']:
        enforce_keys(c,{'id','text','kind','source_refs'},'claim'); _refs(c,loc,c['id'])
        if c['kind'] not in ('official','inference','uncertain'): raise ContractError('Unmarked source provenance class')
    for i,s in enumerate(author['sections']):
        enforce_keys(s,{'title','intuition','formal','worked_example','misconceptions','source_refs'},'section')
        _refs(s,loc,f'section {i}')
        if any(len(s.get(k,'').strip())<40 for k in ('intuition','formal','worked_example')):
            raise ContractError('Section lacks substantial intuition, formal reasoning or worked example')

def check_assess(assess,bp,manifest):
    enforce_keys(assess,{'items'},'assessment')
    if not assess['items']: raise ContractError('No assessments')
    cm={c['id']:c for c in bp['competencies']}; loc=_locators(manifest)
    validated=set(); ids=set(); modes=set()
    for a in assess['items']:
        enforce_keys(a,{'id','prompt','solution','competency_ids','required_operations','points','rubric','difficulty','source_refs'},'assessment item')
        _refs(a,loc,a['id'])
        if a['id'] in ids: raise ContractError('Duplicate assessment ID')
        ids.add(a['id']); modes.add(a['difficulty'])
        if not a['prompt'].strip() or len(a['solution'].strip())<30: raise ContractError('Empty assessment prompt or thin solution')
        if not set(a['competency_ids'])<=set(cm): raise ContractError('Assessment references unknown competency')
        if not a['rubric'] or sum(r.get('points',0) for r in a['rubric']) != a['points'] or a['points']<=0:
            raise ContractError('Rubric points do not reconcile')
        if any(not r.get('criterion') or r.get('points',0)<=0 for r in a['rubric']): raise ContractError('Invalid rubric criterion')
        for cid in a['competency_ids']:
            # This is only a syntactic minimum; independent auditor tests semantics.
            if cm[cid]['operation'] not in a['required_operations']: raise ContractError(f'{a["id"]}: claims {cid} but does not require operation {cm[cid]["operation"]}')
            validated.add(cid)
    if set(cm)-validated: raise ContractError(f'Missing assessment competence evidence: {set(cm)-validated}')
    if 'transfer' not in modes: raise ContractError('No independent transfer task')

def check_cards(cards,bp,manifest):
    enforce_keys(cards,{'cards','not_needed_reason'},'cards')
    cm={c['id'] for c in bp['competencies']}; loc=_locators(manifest); ids=set(); qs=set()
    if not cards['cards'] and not cards['not_needed_reason'].strip(): raise ContractError('Zero cards without justification')
    for c in cards['cards']:
        enforce_keys(c,{'id','question','answer','explanation','competency_ids','source_refs'},'card')
        _refs(c,loc,c['id'])
        if c['id'] in ids: raise ContractError('Duplicate card IDs')
        ids.add(c['id']); q=c['question'].strip().casefold()
        if q in qs: raise ContractError('Duplicate card prompts')
        qs.add(q)
        if not set(c['competency_ids'])<=cm: raise ContractError('Card references unknown competency')
        if not c.get('answer','').strip() or any(len(c.get(k,'').strip())<8 for k in ('question','explanation')): raise ContractError('Empty card answer or inadequate prompt/feedback')
        if '<script' in str(c).lower(): raise ContractError('Script prohibited in card content')

def check_interaction(interaction,bp):
    enforce_keys(interaction,{'kind','reason','competency_ids'},'interaction')
    ids={c['id'] for c in bp['competencies']}
    if not set(interaction['competency_ids'])<=ids: raise ContractError('Interaction references unknown competency')
    kind=interaction['kind']
    if kind=='none':
        if not interaction['reason'].strip(): raise ContractError('Missing no-lab justification')
    elif kind=='quiz':
        q=interaction['quiz']; opts=q['options']; i=q['correct_index']
        if len(opts)<2 or len(set(opts))!=len(opts) or not isinstance(i,int) or i not in range(len(opts)):
            raise ContractError('Invalid quiz distractors or answer')
        for k in ('question','feedback_correct','feedback_wrong'):
            if len(q.get(k,'').strip())<10: raise ContractError('Quiz feedback too short')
    elif kind=='numeric':
        n=interaction['numeric']; var=n['variable']; constants=n['constants']
        if not var.isidentifier() or var in constants or any(not x.isidentifier() for x in constants):
            raise ContractError('Bad numeric variable names')
        if n['min']>=n['max'] or n['step']<=0 or not n['min']<=n['default']<=n['max']: raise ContractError('Bad numeric bounds')
        target=n.get('prediction_target')
        if isinstance(target,bool) or not isinstance(target,(int,float)) or not math.isfinite(target):
            raise ContractError('Numeric lab requires a finite explicit prediction_target')
        if not n['min']<=target<=n['max'] or math.isclose(target,n['default'],abs_tol=1e-9):
            raise ContractError('Prediction target must be in slider bounds and differ from default')
        target_step=(target-n['min'])/n['step']
        if not math.isclose(target_step,round(target_step),rel_tol=0,abs_tol=1e-8):
            raise ContractError('Prediction target must be reachable using the slider step')
        for v in [n['default']]+[n['min']+(n['max']-n['min'])*i/100 for i in range(101)]:
            env={**constants,var:v}; value=evaluate_numeric(n['expression'],env)
            if not math.isfinite(value): raise ContractError('Nonfinite numeric lab')
        check_numeric_interval(n['expression'],{**{k:(v,v) for k,v in constants.items()},var:(n['min'],n['max'])})
        expected=evaluate_numeric(n['expression'],{**constants,var:n['default']})
        if not math.isclose(expected,n['reference_at_default'],rel_tol=1e-7,abs_tol=1e-7):
            raise ContractError(f'Lab reference mismatch: {expected} vs {n["reference_at_default"]}')
    else: raise ContractError('Unknown interaction kind')

def check_audit(audit,bp):
    enforce_keys(audit,{'verdict','findings','reviewed_competencies','unverified_claims'},'audit')
    if audit['verdict'] not in ('PASS','FAIL','NEEDS_REVIEW'): raise ContractError('Invalid audit verdict')
    valid={c['id'] for c in bp['competencies']}
    if not set(audit['reviewed_competencies'])<=valid: raise ContractError('Auditor reviewed unknown competency')
    if audit['verdict']=='PASS' and (set(audit['reviewed_competencies'])!=valid or audit['unverified_claims']):
        raise ContractError('Auditor PASS invalid: reviewed_competencies must contain ALL EXACT IDs including unit prefixes; unverified_claims MUST be []. If any unverified point remains (including software/empirical/exam checks), use NEEDS_REVIEW, not PASS. Missing IDs: '+str(sorted(valid-set(audit['reviewed_competencies'])))+'; unverified_claims: '+str(audit['unverified_claims']))
    if audit['verdict']=='PASS' and any(f['severity'] in ('blocker','major') for f in audit['findings']):
        raise ContractError('Auditor PASS contradicts severe findings')


def _luminance(hexcolor):
    channels=[int(hexcolor[i:i+2],16)/255.0 for i in (1,3,5)]
    channels=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in channels]
    return 0.2126*channels[0]+0.7152*channels[1]+0.0722*channels[2]

def check_design(design):
    enforce_keys(design,{'theme','layout','visual_rationale','anki_rationale','book_rationale'},'design')
    colors=design['theme'];enforce_keys(colors,{'ink','accent','paper','surface'},'theme')
    import re
    for name,val in colors.items():
        if not isinstance(val,str) or re.fullmatch(r'#[0-9A-Fa-f]{6}',val) is None:
            raise ContractError('Invalid theme hex color: '+name)
    for role in ('ink','accent'):
        a,b=_luminance(colors[role]),_luminance(colors['paper'])
        contrast=(max(a,b)+0.05)/(min(a,b)+0.05)
        if contrast<4.5: raise ContractError(f'Poor foreground/background contrast: {role} {contrast:.2f}')
    if design['layout'].get('heading_family') not in ('serif','sans') or design['layout'].get('density') not in ('comfortable','compact'):
        raise ContractError('Invalid layout style')
    if any(len(design.get(k,'').strip())<20 for k in ('visual_rationale','anki_rationale','book_rationale')):
        raise ContractError('Design lacks editorial rationale')


def check_research(research,manifest):
    enforce_keys(research,{'evidence_items','contradictions','external_research_needed','visual_review_needed','exam_scope_uncertainty'},'research')
    if not research['evidence_items']: raise ContractError('Researcher provided no grounded evidence')
    loc=_locators(manifest)
    for item in research['evidence_items']:
        enforce_keys(item,{'id','finding','source_refs','confidence'},'evidence item')
        _refs(item,loc,item['id'])
        if item['confidence'] not in ('high','medium','low'): raise ContractError('Invalid evidence confidence')


# ============================================================ P3: chapter ContentAST (em-content-v1)
# Three separate evidence classes. Passing all three is a TECHNICAL result, never an academic release.
CONTENT_SCHEMA = 'em-content-v1'
BLOCK_KINDS = {'MOTIVATION', 'INTUITION', 'DEFINITION', 'THEOREM', 'MODEL', 'ASSUMPTIONS', 'PROOF', 'DERIVATION',
               'SUBSUMPTION', 'NORM_STRUCTURE', 'ALGORITHM', 'COMPLEXITY', 'CALCULATION', 'WORKED_EXAMPLE',
               'COUNTEREXAMPLE', 'MISCONCEPTION', 'LIMITATION', 'INTERPRETATION', 'REMARK', 'SUMMARY',
               'EXPLANATION'}  # B7.4: rendered by the publisher already; the author prompt now lists these kinds
ARGUMENT_KINDS = {'PROOF': 'EMPTY_PROOF', 'DERIVATION': 'EMPTY_DERIVATION', 'SUBSUMPTION': 'EMPTY_SUBSUMPTION'}
PROVENANCE = {'COURSE_SOURCE', 'SOURCE_PARAPHRASE', 'EXAM_ADAPTED', 'VERIFIED_SUPPLEMENT', 'AUTHOR_INFERENCE', 'AUTHOR_CREATED'}  # = role_schemas.BLOCK enum
CLAIM_STATUS = {'PENDING_SEMANTIC_REVIEW', 'MODEL_REVIEWED_SUPPORTED', 'MODEL_REVIEWED_UNSUPPORTED',
                'CONFLICT_REVIEW_REQUIRED', 'OPEN_SUPPLEMENT_SOURCE_REQUIRED'}
FORBIDDEN_STATUS = {'SUPPORTED', 'VERIFIED', 'COVERED', 'CONFIRMED', 'SOURCE_SUPPORT_CONFIRMED', 'RELEASED'}
FIGURE_STATUS = {'SOURCE_ASSET_REUSED', 'REDRAW_FROM_SOURCE_SPEC', 'OPEN_NOT_GENERATED'}
TRANSFER = {'NEW_PARAMETERS', 'NEW_CONTEXT', 'NEW_CASE', 'NEW_PROBLEM'}
DIFFICULTY = ('recall', 'guided', 'standard', 'transfer', 'exam')
EXPOSITION = {'PROVE': {'PROOF'}, 'DERIVE': {'DERIVATION', 'PROOF'}, 'SUBSUME': {'SUBSUMPTION'},
              'IMPLEMENT': {'ALGORITHM'}, 'CALCULATE': {'WORKED_EXAMPLE', 'CALCULATION'}, 'APPLY': {'WORKED_EXAMPLE', 'SUBSUMPTION'}}
PLACEHOLDER = __import__('re').compile(r'^\s*(trivial|offensichtlich|obvious(ly)?|klar|clear|left as (an )?exercise|'
                                      r'siehe (vorlesung|skript)|see (lecture|slides)|todo|tbd|\.\.\.|…|analog)\s*\.?\s*$', __import__('re').I)


def _shape(expr, symbols):
    """Shape of a product expression like 'A^T A x' (factors separated by space or *). None if not checkable."""
    import re as _re
    shape = None
    for tok in [t for t in _re.split(r'[\s*·]+', expr.strip()) if t]:
        m = _re.fullmatch(r'([A-Za-z_][A-Za-z0-9_]*)(\^(T|\{T\}|\\top|\{\\top\})|\')?', tok)
        if not m or m.group(1) not in symbols:
            return None, f'unknown factor {tok!r}'
        r, c = symbols[m.group(1)]
        if m.group(2):
            r, c = c, r
        if shape is None:
            shape = (r, c)
        elif shape[1] != r:
            return None, f'inner dimensions do not match at {tok!r}: {shape} x {(r, c)}'
        else:
            shape = (shape[0], c)
    return shape, None


def check_shapes(spec):
    """spec = {"symbols": {"A": [m, n], ...}, "equations": [{"lhs": "...", "rhs": "..."}]}; sums: terms joined by +/-."""
    import re as _re
    errors = []
    symbols = {k: tuple(v) for k, v in spec.get('symbols', {}).items()}
    for eq in spec.get('equations', []):
        shapes = []
        for side in (eq['lhs'], eq['rhs']):
            terms_ = [t for t in _re.split(r'\s[+-]\s', side) if t.strip()]
            ts = []
            for t in terms_:
                s, err = _shape(t, symbols)
                if err:
                    errors.append(f"{eq['lhs']} = {eq['rhs']}: {err}"); break
                ts.append(s)
            else:
                if len(set(ts)) > 1:
                    errors.append(f'{side}: summands have different shapes {ts}')
                shapes.append(ts[0] if ts else None)
        if len(shapes) == 2 and None not in shapes and shapes[0] != shapes[1]:
            errors.append(f"{eq['lhs']} = {eq['rhs']}: shapes differ {shapes[0]} vs {shapes[1]}")
    return errors


def check_content_ast(ast_, chapter, plan, manifest):
    """Return {'structural','evidence','operational'} findings and a technical verdict. Never raises on content."""
    from .curriculum import operations_in, satisfied, MC_PATTERN, CASE_PATTERN, NORM_PATTERN, terms
    rep = {k: [] for k in ('structural', 'evidence', 'operational')}
    add = lambda cls, code, obj, detail='': rep[cls].append({'code': code, 'object': obj, 'detail': detail})
    by = {e['element_id']: e for e in manifest['elements']}
    pkg = set(chapter['source_package']['element_ids'])
    kcs = {k['kc_id']: k for k in plan['competencies']}
    ext_ok = {s['source_id'] for s in manifest['sources'] if s['authority'] == 'SUPPLEMENTARY' and s['status'] == 'extracted'} | \
             {r['ref_id'] for r in manifest.get('online_references', []) if r['status'] == 'FETCHED'}
    ext_known = {s['source_id'] for s in manifest['sources']} | {r['ref_id'] for r in manifest.get('online_references', [])}
    for key in ('schema', 'course_id', 'chapter_id', 'kc_ids', 'blocks', 'assessments', 'solutions', 'figures',
                'open_issues', 'relations', 'release_status', 'version', 'learning_objectives', 'notation'):
        if key not in ast_:
            add('structural', 'MISSING_FIELD', key)
    if rep['structural']:
        return _verdict(rep)
    if ast_['schema'] != CONTENT_SCHEMA:
        add('structural', 'WRONG_SCHEMA', ast_['schema'])
    if ast_['release_status'] != 'DRAFT':
        add('evidence', 'FALSE_RELEASE_CLAIM', ast_['release_status'])
    open_refs = {i.get('object_id') for i in ast_['open_issues']}
    ids = {}
    for b in ast_['blocks']:
        bid = b.get('block_id'); ids[bid] = 'block'
        if b.get('kind') not in BLOCK_KINDS:
            add('structural', 'UNKNOWN_BLOCK_KIND', bid, b.get('kind'))
        if b.get('kind') in ARGUMENT_KINDS:
            steps = b.get('steps') or []
            if not steps or any(not str(s.get('statement', '')).strip() or not str(s.get('justification', '')).strip() for s in steps):
                add('structural', ARGUMENT_KINDS[b['kind']], bid, 'every step needs a statement and a justification')
            elif all(PLACEHOLDER.match(str(s['justification'])) or PLACEHOLDER.match(str(s['statement'])) for s in steps):
                add('structural', 'PLACEHOLDER_ARGUMENT', bid)
            if b['kind'] == 'SUBSUMPTION' and not (b.get('norm_refs') and all(s.get('element') for s in steps)):
                add('structural', 'SUBSUMPTION_WITHOUT_ELEMENTS', bid, 'Tatbestandsmerkmale must be named per step')
        if b.get('kind') == 'WORKED_EXAMPLE':
            if not all(str(b.get(f, '')).strip() for f in ('problem', 'result', 'interpretation')) or not b.get('steps') or \
                    any(not str(s.get('justification', '')).strip() for s in b['steps']):
                add('structural', 'INCOMPLETE_WORKED_EXAMPLE', bid, 'problem, justified steps, result and interpretation required')
        if b.get('shape_checks'):
            for err in check_shapes(b['shape_checks']):
                add('structural', 'DIMENSION_MISMATCH', bid, err)
        # evidence class
        for r in b.get('source_refs', []):
            if r not in pkg:
                add('evidence', 'UNKNOWN_SOURCE_ANCHOR', bid, r)
        prov = b.get('provenance')
        if prov not in PROVENANCE:
            add('evidence', 'UNKNOWN_PROVENANCE', bid, prov)
        if prov in ('COURSE_SOURCE', 'SOURCE_PARAPHRASE', 'EXAM_ADAPTED') and not b.get('source_refs'):
            add('evidence', 'UNANCHORED_COURSE_CLAIM', bid)
        if prov == 'VERIFIED_SUPPLEMENT':
            refs = b.get('external_refs') or []
            if any(r not in ext_known for r in refs):
                add('evidence', 'UNKNOWN_EXTERNAL_REF', bid, refs)
            elif not refs or any(r not in ext_ok for r in refs):
                if b.get('claim_support_status') != 'OPEN_SUPPLEMENT_SOURCE_REQUIRED' or bid not in open_refs:
                    add('evidence', 'UNVERIFIED_SUPPLEMENT_SOURCE', bid, 'supplement needs a provided/fetched source or an OPEN_ISSUE')
        st = b.get('claim_support_status')
        if st in FORBIDDEN_STATUS:
            add('evidence', 'FALSE_VERIFICATION_CLAIM', bid, st)
        elif st not in CLAIM_STATUS:
            add('evidence', 'UNKNOWN_CLAIM_STATUS', bid, st)
        if st == 'MODEL_REVIEWED_UNSUPPORTED' and bid not in open_refs:
            add('evidence', 'UNSUPPORTED_CLAIM_NOT_FLAGGED', bid)
    sol = {s.get('solution_id'): s for s in ast_['solutions']}
    texts = [terms(by[e]['normalized_text']) for e in pkg if by[e]['normalized_text']]
    levels = set()
    for a in ast_['assessments']:
        aid = a.get('item_id'); ids[aid] = 'assessment'; levels.add(a.get('difficulty'))
        if a.get('difficulty') not in DIFFICULTY:
            add('structural', 'UNKNOWN_DIFFICULTY', aid, a.get('difficulty'))
        if a.get('actual_operation_review') != 'PENDING':
            add('evidence', 'FALSE_VERIFICATION_CLAIM', aid, 'operation review is reserved for an independent reviewer')
        s = sol.get(a.get('solution_id'))
        if s is None:
            add('structural', 'MISSING_SOLUTION', aid); continue
        if not s.get('steps') or any(not str(x.get('justification', '')).strip() for x in s['steps']) or not str(s.get('answer', '')).strip():
            add('structural', 'INCOMPLETE_SOLUTION', aid)
        if not s.get('hint_ladder'):
            add('structural', 'MISSING_HINT_LADDER', aid)
        rubric = s.get('rubric') or []
        if not rubric or any(not str(r.get('criterion', '')).strip() or not isinstance(r.get('points'), (int, float)) or r['points'] <= 0 for r in rubric):
            add('structural', 'MISSING_RUBRIC', aid, 'criteria with partial points required')
        elif a.get('points') is not None and abs(sum(r['points'] for r in rubric) - a['points']) > 1e-9:
            add('structural', 'RUBRIC_POINTS_MISMATCH', aid, f"{sum(r['points'] for r in rubric)} != {a['points']}")
        for r in a.get('source_refs', []):
            if r not in pkg:
                add('evidence', 'UNKNOWN_SOURCE_ANCHOR', aid, r)
        if a.get('transfer_relation') in TRANSFER:
            pt = terms(a.get('prompt', ''))
            if any(len(pt & t) / (len(pt | t) or 1) >= 0.8 for t in texts):
                add('operational', 'TRANSFER_COPIES_SOURCE', aid)
        # operation of the item, from its OWN wording
        q = {'format': 'multiple_choice' if a.get('format') == 'multiple_choice' or MC_PATTERN.search(a.get('prompt', '')) else 'open',
             'has_concrete_instance': bool(CASE_PATTERN.search(a.get('prompt', ''))),
             'norm_refs': NORM_PATTERN.findall(a.get('prompt', ''))}
        a['_ops'] = operations_in(a.get('prompt', '')); a['_q'] = q
        req = a.get('required_operation')
        if req:
            ok, why = satisfied(req, a['_ops'], q)
            if not ok:
                add('operational', 'OPERATION_MISMATCH', aid, why)
    for s in ast_['solutions']:
        ids[s.get('solution_id')] = 'solution'
    for f in ast_['figures']:
        fid = f.get('figure_id'); ids[fid] = 'figure'
        if f.get('status') not in FIGURE_STATUS or not str(f.get('purpose', '')).strip() or not str(f.get('didactic_rationale', '')).strip():
            add('structural', 'INCOMPLETE_FIGURE', fid)
        if f.get('source_element_id') and f['source_element_id'] not in pkg:
            add('evidence', 'UNKNOWN_SOURCE_ANCHOR', fid, f['source_element_id'])
        elif f.get('status') == 'SOURCE_ASSET_REUSED' and (not f.get('source_element_id') or by[f['source_element_id']]['status'] != 'ok'):
            add('evidence', 'FIGURE_SOURCE_UNRESOLVED', fid, 'only an understood (status ok) source asset may be reused as is')
        if f.get('status') == 'OPEN_NOT_GENERATED' and fid not in open_refs:
            add('structural', 'OPEN_FIGURE_NOT_FLAGGED', fid)
    covered_vis = {f.get('source_element_id') for f in ast_['figures']} | {e for i in ast_['open_issues'] for e in i.get('element_ids', [])}
    for v in chapter['requirements']['visualizations']:
        if v.get('source_element_id') and v['kind'] in ('image', 'figure', 'diagram', 'chart') and v['source_element_id'] not in covered_vis:
            add('structural', 'VISUAL_REQUIREMENT_DROPPED', v['source_element_id'])
    for r in ast_['relations']:
        if r.get('from') not in ids or r.get('to') not in ids:
            add('structural', 'DANGLING_RELATION', f"{r.get('from')}->{r.get('to')}")
    for n in plan['notation_registry']:
        if n['status'] != 'CONSISTENT' and n['notation_id'] in chapter.get('notation_ids', []):
            mine = next((x for x in ast_['notation'] if x.get('notation_id') == n['notation_id']), None)
            if not mine or mine.get('status') == 'CONSISTENT':
                add('evidence', 'NOTATION_CONFLICT_HIDDEN', n['notation_id'], n['symbol'])
    for c in ast_.get('kc_coverage', []):
        if c.get('status') in FORBIDDEN_STATUS:
            add('evidence', 'FALSE_VERIFICATION_CLAIM', c.get('kc_id'), c['status'])
    # operational class: each demanding competency needs exposition AND an item that demands its operation
    demanding = False
    for kid in ast_['kc_ids']:
        for op in kcs[kid]['operations'] if kid in kcs else []:
            if op not in EXPOSITION:
                continue
            demanding = True
            if not any(kid in b.get('kc_ids', []) and b.get('kind') in EXPOSITION[op] for b in ast_['blocks']):
                add('operational', 'MISSING_EXPOSITION_' + op, kid)
            linked = [a for a in ast_['assessments'] if kid in a.get('kc_ids', [])]
            reasons = []
            for a in linked:
                ok, why = satisfied(op, a['_ops'], a['_q'])
                if ok:
                    break
                reasons.append(f"{a['item_id']}: {why}")
            else:
                add('operational', 'OPERATION_NOT_ASSESSED', kid, '; '.join(reasons) or 'no item linked')
    if demanding and not any(a.get('transfer_relation') in TRANSFER and a.get('difficulty') in ('transfer', 'exam') for a in ast_['assessments']):
        add('operational', 'NO_GENUINE_TRANSFER', ast_['chapter_id'])
    if demanding and len(levels & set(DIFFICULTY)) < 2:
        add('operational', 'FLAT_PROGRESSION', ast_['chapter_id'])
    for a in ast_['assessments']:
        a.pop('_ops', None); a.pop('_q', None)
    return _verdict(rep)


def _verdict(rep):
    failed = any(rep[k] for k in ('structural', 'evidence', 'operational'))
    return {'schema': 'em-content-gate-v1', **rep,
            'technical_status': 'FAIL' if failed else 'PASS',
            'semantic_review': 'PENDING', 'academic_release': 'NOT_TESTED',
            'note': 'Automated checks are not a subject-matter release; claims stay PENDING_SEMANTIC_REVIEW or MODEL_REVIEWED.'}
