"""P3: chapter-level production planning between the curriculum (P2) and the editorial producer.

Everything here is offline and deterministic: no provider, no network, no subprocess.
- fidelity_gate(): per chapter, which competencies can be drafted and which are BLOCKED by source fidelity
- chapter_context(): the evidence bundle one chapter author receives (source text is untrusted data)
- planned_actions(): the audit of every provider action a real run would make (per chapter, never per chunk)
- dry_run(): root -> inventory -> curriculum -> chapter plan -> gate -> action audit, with explicit gaps
- ast_validity(): a persisted ContentAST is STALE as soon as any source element it depends on changed
"""
from pathlib import Path
import json
import re
from .common import ContractError, write_json
from .checkpoints import digest
from .curriculum import compile_curriculum, NORM_PATTERN, SemanticDecisions, scan_scope
from .fidelity import inventory
from .review_overlay import context_block as review_context_block, evaluate as review_evaluate, load as review_load
from . import review_decisions as rdec

GATE_VERSION = 'em-chapter-gate-1'
CHAPTER_ROLES = ('chapter_author', 'chapter_assessment', 'chapter_solutions', 'chapter_semantic_review')
RISK_ROLE = 'chapter_risk_review'
REVISION_ROLE = 'chapter_revision'
RISK_REVIEWS = {'SYMBOLIC_WITH_DOMAIN', 'LEGAL_NORM', 'EXECUTABLE_TESTS'}
MAX_ACTIONS_PER_CHAPTER = len(CHAPTER_ROLES) + 2
VISUAL_KINDS = {'image', 'figure', 'diagram', 'chart'}          # rendered_page is a review aid, not content
CRITICAL_OPS = {'DERIVE', 'PROVE', 'CALCULATE'}
REQUIRED_MARK = re.compile(r'pflicht|required|mandatory|obligatorisch|prüfungsrelevant|must[- ]read|verbindlich', re.I)
SOURCE_BLOCKERS = {'TEXT_LAYER_MISSING': 'SCANNED_PAGE_NO_OCR', 'PARSE_FAILED': 'SOURCE_PARSE_FAILED',
                   'EMPTY_SOURCE': 'SOURCE_EMPTY', 'TOO_LARGE': 'SOURCE_TOO_LARGE', 'TRUNCATED_TABLE': 'SOURCE_TRUNCATED'}
GATE_RULES = {
    'ESSENTIAL_VISUAL_UNRESOLVED': 'image/diagram/chart on the same slide/page as a competency anchor is not visually '
                                   'understood (status != ok or deck not renderable) -> that competency is BLOCKED',
    'CRITICAL_FORMULA_UNRELIABLE': 'formula within 2 elements of an anchor of a DERIVE/PROVE/CALCULATE competency exists '
                                   'only as linearised extraction text -> BLOCKED',
    'SCANNED_PAGE_NO_OCR': 'a source of the competency has pages without a text layer (no OCR offline) -> BLOCKED',
    'REQUIRED_SOURCE_UNAVAILABLE': 'an online/linked source marked as required (Pflicht/required/...) referenced by the '
                                   'chapter is not fetched -> whole chapter BLOCKED',
    'SOURCE_GAP': 'P2 coverage BLOCKED_SOURCE_GAP for the competency -> BLOCKED',
}


def _unit(e):
    loc = e.get('locator') or {}
    for k in ('slide', 'page'):
        if k in loc:
            return (e['source_id'], k, loc[k])
    return None


def _uncertain_formula(e):
    return e['kind'] == 'formula' and (e['status'] == 'uncertain' or
                                       (e.get('fidelity') or {}).get('representation') == 'linearized_text_layer')


def _unresolved_visual(e, src):
    return e['kind'] in VISUAL_KINDS and (e['status'] != 'ok' or src.get('visual_status') == 'RENDER_UNAVAILABLE')


def fidelity_gate(plan, manifest, diagnostics=None):
    by = {e['element_id']: e for e in manifest['elements']}
    src = {s['source_id']: s for s in manifest['sources']}
    order = {eid: (s['source_id'], i) for s in manifest['sources'] for i, eid in enumerate(s['element_ids'])}
    gaps_by_src = {}
    for g in manifest['gaps']:
        gaps_by_src.setdefault(g['source_id'], []).append(g)
    kcs = {k['kc_id']: k for k in plan['competencies']}
    cov = {r['kc_id']: r for r in plan['coverage']}
    items = {q['item_id']: q for q in plan['assessment_items']}
    units = {}
    for e in manifest['elements']:
        u = _unit(e)
        if u:
            units.setdefault(u, []).append(e)
    gates = {}
    attributed_sources = set()
    from .triage import page_model, visual_class
    pmodel = page_model(manifest)
    propagation, decorative = [], {}
    for c in plan['chapters']:
        findings, blocked = [], {}
        pkg = set(c['source_package']['element_ids'])
        assess_els = set(c['source_package'].get('assessment_element_ids', []))
        essential_seen = set()

        review = {}

        def block(kc_id, code, eids, detail, rule='GATE'):
            blocked.setdefault(kc_id, []).append(code)
            findings.append({'code': code, 'severity': 'blocker', 'kc_ids': [kc_id], 'element_ids': sorted(eids), 'detail': detail, 'rule': rule})
            propagation.append({'cause': code, 'rule': rule, 'element_ids': sorted(eids), 'kc_id': kc_id, 'chapter_id': c['chapter_id'], 'effect': 'BLOCK'})

        def needs_review(kc_id, code, eids, detail, rule, **where):
            review.setdefault(kc_id, []).append(code)
            findings.append({'code': code, 'severity': 'review', 'kc_ids': [kc_id], 'element_ids': sorted(eids), 'detail': detail, 'rule': rule, **where})
            propagation.append({'cause': code, 'rule': rule, 'element_ids': sorted(eids), 'kc_id': kc_id, 'chapter_id': c['chapter_id'], 'effect': 'REVIEW'})
        for kid in c['kc_ids']:
            k = kcs[kid]
            if cov[kid]['status'] == 'BLOCKED_SOURCE_GAP':
                block(kid, 'SOURCE_GAP', [], ', '.join(cov[kid]['blocking_source_gaps']), 'C0_COVERAGE_BLOCKED_SOURCE_GAP')
            for sid in k['source_ids']:
                for g in gaps_by_src.get(sid, []):
                    if g['code'] in SOURCE_BLOCKERS and g['code'] != 'TEXT_LAYER_MISSING':
                        block(kid, SOURCE_BLOCKERS[g['code']], [], f"{src[sid]['relative_path']}: {g['detail']}", 'S_SOURCE_WIDE_' + g['code'])
                scope, spages = scan_scope(manifest, sid)
                if scope == 'SOURCE_WIDE':
                    block(kid, 'SCANNED_PAGE_NO_OCR', [], f"{src[sid]['relative_path']}: pages {spages} without text layer "
                          '(>=20% of pages or <=5-page source)', 'S0_SCAN_SOURCE_WIDE')
                elif scope == 'LOCAL':
                    ap = {(by[a].get('locator') or {}).get('page') for a in k['source_anchor_ids'] if by[a]['source_id'] == sid}
                    on = sorted(p for p in spages if p in ap); near = sorted(p for p in spages if p not in ap and any(x is not None and abs(x - p) == 1 for x in ap))
                    if on:
                        block(kid, 'SCANNED_PAGE_NO_OCR', [], f"anchor on textless page(s) {on}", 'S1_SCAN_ANCHOR_PAGE')
                    elif near:
                        needs_review(kid, 'ADJACENT_PAGE_UNREADABLE', [], f"anchor next to textless page(s) {near}", 'S2_SCAN_NEIGHBOUR_PAGE',
                                     source_id=sid, pages=near)
            for a in k['source_anchor_ids']:
                ea = by[a]
                u = _unit(ea)
                for v in units.get(u, []) if u else []:
                    if _unresolved_visual(v, src[v['source_id']]):
                        sp = pmodel.get(v['source_id'])
                        if src[v['source_id']]['format'] == '.pdf' and sp and u[2] in sp['pages']:
                            cls, rule = visual_class(v, sp['pages'][u[2]], sp)
                            if cls == 'DECORATIVE_CANDIDATE':
                                decorative.setdefault(v['element_id'], rule); continue
                            essential_seen.add(v['element_id'])
                            if cls == 'ESSENTIAL':
                                block(kid, 'ESSENTIAL_VISUAL_UNRESOLVED', [v['element_id']],
                                      f"{v['kind']} {v['locator_str']}: content lives in the visual", rule)
                            else:
                                needs_review(kid, 'VISUAL_RELEVANCE_UNKNOWN', [v['element_id']],
                                             f"{v['kind']} {v['locator_str']} on the anchor's page; relevance not established", rule)
                            continue
                        essential_seen.add(v['element_id'])
                        block(kid, 'ESSENTIAL_VISUAL_UNRESOLVED', [v['element_id']],
                              f"{v['kind']} {v['locator_str']} on the anchor's slide/page is not visually understood", 'V_SLIDE_OR_NONPDF')
                for lk in ([ea] if ea['kind'] == 'figure' else []):
                    linked = (lk.get('structure') or {}).get('linked_source_id')
                    if lk['status'] != 'ok' or (linked and src[linked]['visual_status'] in ('VISUAL_UNCERTAIN', 'RENDER_UNAVAILABLE')):
                        essential_seen.add(lk['element_id'])
                        block(kid, 'ESSENTIAL_VISUAL_UNRESOLVED', [lk['element_id']], 'anchored figure is not understood')
                if set(k['operations']) & CRITICAL_OPS and a in order:
                    sid, i = order[a]
                    for eid in src[sid]['element_ids'][max(0, i - 2):i + 3]:
                        if _uncertain_formula(by[eid]):
                            essential_seen.add(eid)
                            block(kid, 'CRITICAL_FORMULA_UNRELIABLE', [eid],
                                  f"formula {by[eid]['locator_str']} is only linearised text next to a {'/'.join(k['operations'])} anchor")
        for kid in blocked:
            blocked[kid] = sorted(set(blocked[kid]))
        for kid in review:
            review[kid] = sorted(set(review[kid]))
        for sid in set(c['source_ids']):
            scope, spages = scan_scope(manifest, sid)
            if scope == 'LOCAL':
                findings.append({'code': 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN', 'severity': 'review', 'kc_ids': [], 'element_ids': [],
                                 'detail': f"{src[sid]['relative_path']}: pages {spages} have no text layer; their content is unknown",
                                 'rule': 'S3_SCAN_CHAPTER_REVIEW', 'source_id': sid, 'pages': list(spages)})
        chapter_sources = set(c['source_package']['source_ids'])
        attributed_sources |= chapter_sources
        for r in manifest.get('online_references', []):
            if r['status'] == 'FETCHED':
                continue
            if not (set(r['referenced_by_elements']) & pkg or set(r['referenced_by_sources']) & set(c['source_ids'])):
                continue
            ctx = ' '.join(r['labels']) + ' ' + ' '.join(by[e]['text'] for e in r['referenced_by_elements'] if e in by)
            if REQUIRED_MARK.search(ctx):
                for kid in c['kc_ids']:
                    blocked.setdefault(kid, [])
                    if 'REQUIRED_SOURCE_UNAVAILABLE' not in blocked[kid]:
                        blocked[kid].append('REQUIRED_SOURCE_UNAVAILABLE')
                findings.append({'code': 'REQUIRED_SOURCE_UNAVAILABLE', 'severity': 'blocker', 'kc_ids': list(c['kc_ids']),
                                 'element_ids': r['referenced_by_elements'], 'detail': f"{r['url']} ({r['status']})"})
            else:
                findings.append({'code': 'SUPPLEMENT_NOT_FETCHED', 'severity': 'open_issue', 'kc_ids': [],
                                 'element_ids': r['referenced_by_elements'], 'detail': f"{r['url']} ({r['status']})"})
        for eid in sorted(pkg - essential_seen):
            e = by[eid]
            if eid in assess_els:
                if _uncertain_formula(e) or _unresolved_visual(e, src[e['source_id']]):
                    findings.append({'code': 'ASSESSMENT_ELEMENT_UNCERTAIN', 'severity': 'open_issue', 'kc_ids': [],
                                     'element_ids': [eid], 'detail': 'exam/exercise element only partially extracted; '
                                                                     'verbatim exam reproduction not allowed'})
                continue
            if e['status'] == 'unavailable':
                findings.append({'code': 'NONESSENTIAL_ASSET_MISSING', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [eid],
                                 'detail': e['text'] or e['locator_str']})
            elif e['kind'] in VISUAL_KINDS and _unresolved_visual(e, src[e['source_id']]):
                findings.append({'code': 'VISUAL_REVIEW_PENDING', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [eid],
                                 'detail': 'not anchored to a competency; must not be interpreted without visual review'})
            elif _uncertain_formula(e):
                findings.append({'code': 'FORMULA_REVIEW_PENDING', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [eid],
                                 'detail': 'linearised formula; not used as a basis for derivations'})
        for kid in c['kc_ids']:
            k = kcs[kid]
            if 'SUBSUME' in k['operations']:
                findings.append({'code': 'NORM_TEXT_NOT_VERIFIED', 'severity': 'open_issue', 'kc_ids': [kid], 'element_ids': [],
                                 'detail': 'norm wording/current legal status must be checked against an official text (P4)'})
            if k['origin'] == 'heading_topic':
                findings.append({'code': 'KC_INFERRED_FROM_HEADINGS', 'severity': 'open_issue', 'kc_ids': [kid], 'element_ids': [],
                                 'detail': 'no stated objective; competency and operation need semantic confirmation'})
            if k.get('conflict_status'):
                findings.append({'code': 'DEFINITION_CONFLICT', 'severity': 'open_issue', 'kc_ids': [kid], 'element_ids': [],
                                 'detail': 'definitions differ between sources; reported, not averaged'})
        for n in plan['notation_registry']:
            if n['status'] != 'CONSISTENT' and n['notation_id'] in c.get('notation_ids', []):
                findings.append({'code': 'NOTATION_CONFLICT', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [u['element_id'] for u in n['uses']],
                                 'detail': f"symbol {n['symbol']}: {n['meanings']} ({n['authority_resolution']['status']})"})
        for m in plan.get('chapter_merges', []):
            if m['decision'] == 'SEMANTIC_REVIEW_REQUIRED' and c['chapter_id'] in m['chapters']:
                findings.append({'code': 'CHAPTER_MERGE_REVIEW', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [],
                                 'detail': f"possible same topic as {m['chapters']} ({m['rule']})"})
        if c.get('order_basis', {}).get('basis') == 'UNRESOLVED_FILENAME_FALLBACK' and len(plan['chapters']) > 1:
            findings.append({'code': 'ORDER_UNRESOLVED', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [],
                             'detail': 'chapter position is a file-order fallback, not evidence'})
        producible = [k for k in c['kc_ids'] if k not in blocked and k not in review]
        status = (('BLOCKED' if blocked and not review else 'REVIEW_REQUIRED') if not producible else
                  'PARTIAL' if blocked or review else 'READY_WITH_OPEN_ISSUES' if findings else 'READY')
        gates[c['chapter_id']] = {'gate_version': GATE_VERSION, 'chapter_id': c['chapter_id'], 'status': status,
                                  'producible_kc_ids': producible, 'blocked_kcs': blocked, 'review_required_kcs': review,
                                  'decorative_visual_candidates': sum(1 for e in decorative if by[e]['source_id'] in set(c['source_ids'])),
                                  'findings': findings,
                                  'rule': 'blocked competencies are reported, never filled by model text'}
    unattributed = [g for g in manifest['gaps'] if g['severity'] == 'blocking' and g['source_id'] not in attributed_sources]
    if diagnostics is not None:
        diagnostics.update(propagation=propagation, decorative_visual_candidates=decorative)
    return gates, unattributed


SUBSTANTIVE_ORIGINS = {'stated_learning_objective', 'formal_object', 'norm', 'exam_derived', 'practice_derived'}
ELIGIBILITY_RULES = {
    'INELIGIBLE': 'no academic-content source, fidelity BLOCKED, or no competency at all',
    'PENDING_REVIEW': 'academic source but at least one open reason (unclear role, only inferred topic candidates, '
                      'competencies awaiting visual/scan relevance review, no exam/practice evidence, merge/segmentation review)',
    'ELIGIBLE': 'academic source, not BLOCKED, >=1 producible competency with stated objective or assessment-derived basis, '
                'linked exam/practice evidence and no open review reason. Still needs human confirmation; release stays NOT_TESTED'}


def pilot_eligibility(plan, gates):
    """Second gate level, separate from fidelity: is this chapter a sensible academic pilot candidate?"""
    from .triage import CHAPTER_ROLES
    roles = plan.get('source_roles', {})
    kcs = {k['kc_id']: k for k in plan['competencies']}
    items = {q['item_id']: q for q in plan['assessment_items']}
    out = {}
    for c in plan['chapters']:
        g = gates[c['chapter_id']]
        prim = {roles.get(s, {}).get('role', 'ACADEMIC_CONTENT') for s in c['source_ids']}
        prod = set(g['producible_kc_ids'])
        subst = [k for k in c['kc_ids'] if kcs[k]['origin'] in SUBSTANTIVE_ORIGINS]
        evid = [q for q in c['exam_relevance']['linked_item_ids'] if items[q].get('evidence_eligible', True)
                and q not in c['exam_relevance'].get('section_mismatch_item_ids', [])]
        reasons, codes = [], []
        if not prim & CHAPTER_ROLES:
            verdict = 'INELIGIBLE'; reasons.append('no source with academic-content role')
        elif g['status'] == 'BLOCKED':
            verdict = 'INELIGIBLE'; reasons.append('fidelity gate BLOCKED: ' + ', '.join(sorted({x for v in g['blocked_kcs'].values() for x in v})))
        elif not c['kc_ids']:
            verdict = 'INELIGIBLE'; reasons.append('no competency extracted')
        else:
            if 'REVIEW_REQUIRED' in prim:
                codes.append('SOURCE_ROLE_UNCLEAR'); reasons.append('source role unclear (REVIEW_REQUIRED)')
            if not subst:
                codes.append('ONLY_INFERRED_TOPICS'); reasons.append('only inferred topic candidates (page titles/headings); no stated objective or exam/practice-derived competency')
            elif not set(subst) & prod:
                codes.append('NO_SUBSTANTIVE_PRODUCIBLE'); reasons.append('substantive competencies exist but none is producible (blocked or pending review)')
            if g.get('review_required_kcs'):
                codes.append('KC_REVIEW_PENDING'); reasons.append(f"{len(g['review_required_kcs'])} competencies await visual/scan relevance review")
            if not evid:
                codes.append('NO_EXAM_EVIDENCE'); reasons.append('no exam or practice item linked')
            if any(f['code'] in ('CHAPTER_MERGE_REVIEW', 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN') for f in g['findings']):
                codes.append('MERGE_OR_UNREADABLE_PAGE'); reasons.append('merge candidate or unreadable page needs a decision')
            verdict = 'PENDING_REVIEW' if reasons else 'ELIGIBLE'
        score = 3 * len(set(subst) & prod) + 2 * len(evid) + len(prod) - len(g.get('review_required_kcs', {})) - len(g['blocked_kcs'])
        out[c['chapter_id']] = {'academic_pilot_eligibility': verdict, 'reasons': reasons, 'reason_codes': codes, 'fidelity_status': g['status'],
                                'academic_release': 'NOT_TESTED', 'substantive_kc_ids': subst, 'evidence_item_ids': evid,
                                'pilot_candidate_score': score,
                                'score_basis': '3*substantive producible KCs + 2*exam/practice items + producible KCs - review - blocked; '
                                               'ranking aid for human review only'}
    return out


class PilotReviewOpen(ContractError):
    """Production refused: a chapter that would be sent to an external provider still has an open review reason."""
    def __init__(self, preflight):
        self.state = 'PILOT_REVIEW_OPEN'; self.preflight = preflight
        opened = {cid: [o['code'] for o in r['open']] for cid, r in preflight['chapters'].items() if r['open']}
        super().__init__(f'PILOT_REVIEW_OPEN: no provider call; open review reasons: {opened}')


# Reasons that are enforced structurally below (per KC or per finding) instead of by their eligibility text.
_STRUCTURAL_REASONS = {'KC_REVIEW_PENDING', 'MERGE_OR_UNREADABLE_PAGE'}


def production_preflight(plan, gates, chapter_ids):
    """Fail-closed check before any external provider call. A chapter passes only if EVERY open reason is decided:
    - gate not BLOCKED/REVIEW_REQUIRED and eligibility not INELIGIBLE;
    - every REVIEW_REQUIRED competency carries an effective HUMAN exclusion (it is never produced either way);
    - every chapter-level textless-page finding is cleared, page by page, by an effective HUMAN page review;
    - no other chapter-level review finding, merge review or eligibility reason is open (no resolver exists here).
    Clearing is scope only: eligibility stays as computed, academic_release stays NOT_TESTED, nothing is verified."""
    elig = pilot_eligibility(plan, gates)
    out = {}
    for cid in chapter_ids:
        g, e = gates[cid], elig[cid]
        eff = g.get('review_decision_effects') or {}
        excluded = eff.get('pilot_scope_excluded_kcs') or {}
        pages = (eff.get('chapter_page_reviews') or {}).get('cleared_for_experimental_pilot') or {}
        open_, cleared = [], []
        if g['status'] in ('BLOCKED', 'REVIEW_REQUIRED'):
            open_.append({'code': 'GATE_' + g['status']})
        if e['academic_pilot_eligibility'] == 'INELIGIBLE':
            open_.append({'code': 'INELIGIBLE', 'detail': e['reasons']})
        for kid in sorted(g.get('review_required_kcs') or {}):
            if kid in excluded:
                cleared.append({'code': 'KC_EXCLUDED_BY_HUMAN', 'kc_id': kid})
            else:
                open_.append({'code': 'KC_REVIEW_UNDECIDED', 'kc_id': kid})
        for f in g['findings']:
            if f['code'] == rdec.PAGE_CAUSE and f['severity'] == 'review' and not f['kc_ids']:
                for p in f.get('pages') or [None]:
                    key = f"page:{f.get('source_id')}:{p}"
                    if key in pages:
                        cleared.append({'code': 'PAGE_CLEARED_FOR_EXPERIMENTAL_PILOT', 'key': key,
                                        'review_id': pages[key]['review_id'], 'restrictions': pages[key]['restrictions']})
                    else:
                        open_.append({'code': 'CHAPTER_PAGE_REVIEW_OPEN', 'key': key, 'detail': f['detail']})
            elif (f['severity'] == 'review' and not f['kc_ids']) or f['code'] == 'CHAPTER_MERGE_REVIEW':
                open_.append({'code': 'CHAPTER_REVIEW_OPEN', 'finding': f['code'], 'detail': f.get('detail')})
        for code, text in zip(e.get('reason_codes', []), [r for r in e['reasons']]):
            if code not in _STRUCTURAL_REASONS:
                open_.append({'code': 'ELIGIBILITY_' + code, 'detail': text})
        # B6.2: session assignment of practice items is position-based; with an unresolved course order it can shift
        # when other files are added, so it is not a stable basis for a pilot.
        chap = next((c for c in plan['chapters'] if c['chapter_id'] == cid), {})
        er = chap.get('exam_relevance') or {}
        order_status = (plan.get('chapter_ordering') or {}).get('status')
        if order_status == 'UNRESOLVED_REVIEW_REQUIRED' and er.get('section_number') is not None and not er.get('session_basis'):
            open_.append({'code': 'COURSE_ORDER_UNRESOLVED', 'detail': f"course chapter order is unresolved; the session assignment "
                          f"(position {er['section_number']}) of practice items is not stable"})
        # B6.3: a course whose practice items are organised by session needs an evidence-based session for this chapter.
        sectioned = any(q.get('section_number') for q in plan.get('assessment_items', []) if q.get('assessment_kind') in ('PRACTICE', 'OFFICIAL_EXAM'))
        if sectioned and er.get('section_number') is None:
            conf = [x for x in (plan.get('chapter_ordering') or {}).get('session_conflicts', [])
                    if any(cand['chapter_id'] == cid for cand in x.get('candidates', []))]
            open_.append({'code': 'SESSION_IDENTITY_UNRESOLVED', 'detail': 'practice items are organised by session, but this chapter '
                          'has no evidence-based session (no unique schedule/TOC/numbering match)', 'conflicts': conf})
        out[cid] = {'status': 'PILOT_BLOCKED' if open_ else 'PILOT_SCOPE_CLEARED_EXPERIMENTAL', 'open': open_,
                    'exam_section': {'section_number': er.get('section_number'), 'session_basis': er.get('session_basis'),
                                     'course_order_status': order_status,
                                     'linked_items': len(er.get('linked_item_ids', [])),
                                     'section_mismatch_items': len(er.get('section_mismatch_item_ids', [])),
                                     'section_unlinked_items': len(er.get('section_unlinked_item_ids', []))},
                    'cleared': cleared, 'eligibility': e['academic_pilot_eligibility'], 'academic_release': 'NOT_TESTED'}
    return {'schema': 'em-production-preflight-v1', 'chapters': out,
            'result': 'BLOCKED' if any(r['open'] for r in out.values()) or not out else 'CLEARED_EXPERIMENTAL_SCOPE',
            'note': 'applies to every external provider; --budget never clears it; human approval and academic release stay separate'}


# B6.8 product mode: open items that are resolved automatically WITHOUT producing the uncertain content.
#  - a competency awaiting review is never produced (it is not in producible_kc_ids anyway); it is recorded as an
#    automatic exclusion and stays a visible coverage gap;
#  - a page without text layer cannot be used (its content is unknown); it is recorded as an unused page.
# Everything else (gate BLOCKED/REVIEW_REQUIRED, ineligibility, unresolved course order or session, merge/chapter reviews)
# is not auto-resolvable and escalates THAT chapter to a human decision; other chapters proceed.
AUTO_RESOLVABLE = {'KC_REVIEW_UNDECIDED': 'AUTO_EXCLUDED_NOT_PRODUCED', 'CHAPTER_PAGE_REVIEW_OPEN': 'AUTO_PAGE_NOT_USED'}
# B7: two more low-risk items that change no content claim:
#  - a possible merge with another chapter: both chapters are kept separate (worst case some overlap), never merged;
#  - a chapter whose competencies are only inferred from headings: produced from its own slide text; the open issue
#    KC_INFERRED_FROM_HEADINGS stays on every such competency, so exam relevance is visibly not established.
AUTO_RESOLVABLE_FINDINGS = {'CHAPTER_MERGE_REVIEW': 'AUTO_KEPT_SEPARATE_NOT_MERGED'}
AUTO_RESOLVABLE.update({'ELIGIBILITY_ONLY_INFERRED_TOPICS': 'AUTO_PRODUCED_EXAM_RELEVANCE_NOT_ESTABLISHED',
                        # B7: a course without past exams is not a production blocker; the label stays visible
                        'ELIGIBILITY_NO_EXAM_EVIDENCE': 'AUTO_PRODUCED_NO_EXAM_EVIDENCE_EXAM_RELEVANCE_UNCONFIRMED'})


def _auto_resolution(o):
    if o['code'] == 'CHAPTER_REVIEW_OPEN':
        return AUTO_RESOLVABLE_FINDINGS.get(o.get('finding'))
    return AUTO_RESOLVABLE.get(o['code'])


def production_preflight_auto(plan, gates, chapter_ids):
    """Product-mode preflight: same checks as production_preflight, with the automatic resolutions above."""
    pf = production_preflight(plan, gates, chapter_ids)
    out = {}
    for cid, r in pf['chapters'].items():
        auto = [dict(o, resolution=_auto_resolution(o)) for o in r['open'] if _auto_resolution(o)]
        escalate = [o for o in r['open'] if not _auto_resolution(o)]
        out[cid] = {**r, 'status': 'ESCALATED_HUMAN_DECISION_REQUIRED' if escalate else 'AUTO_CLEARED',
                    'auto_resolved': auto, 'escalations': escalate, 'open': escalate}
    ok = [c for c, r in out.items() if r['status'] == 'AUTO_CLEARED']
    return {'schema': 'em-production-preflight-auto-v1', 'chapters': out, 'producible_chapters': ok,
            'result': 'AUTO_CLEARED' if ok and len(ok) == len(out) else 'PARTIAL_ESCALATION' if ok else 'ESCALATION_REQUIRED',
            'note': 'automatic scope: uncertain competencies and textless pages are excluded, never produced; '
                    'human decisions only for escalated chapters; academic release stays NOT_TESTED'}


def chapter_context(plan, manifest, chapter_id, gate, review=None):
    """Evidence bundle for one chapter. Source text is passed as untrusted data, never as instruction.
    review: optional evaluated review overlay (review_overlay.evaluate); its block for this chapter is added in full."""
    by = {e['element_id']: e for e in manifest['elements']}
    src = {s['source_id']: s for s in manifest['sources']}
    c = next(x for x in plan['chapters'] if x['chapter_id'] == chapter_id)
    kcs = {k['kc_id']: k for k in plan['competencies']}
    cov = {r['kc_id']: r for r in plan['coverage']}
    items = {q['item_id']: q for q in plan['assessment_items']}
    titles = {x['chapter_id']: x['title'] for x in plan['chapters']}
    mismatch = set(c['exam_relevance'].get('section_mismatch_item_ids', []))
    supplements = [{'ref_id': s['source_id'], 'relative_path': s['relative_path'], 'authority': s['authority']}
                   for s in manifest['sources'] if s['authority'] == 'SUPPLEMENTARY' and s['status'] == 'extracted']
    supplements += [{'ref_id': r['ref_id'], 'url': r['url'], 'sha256': r.get('sha256')}
                    for r in manifest.get('online_references', []) if r['status'] == 'FETCHED']
    ctx = {'schema': 'em-chapter-context-v1', 'course_id': plan['course_id'], 'chapter_id': chapter_id, 'title': c['title'],
            'position': c['position'], 'order_basis': c.get('order_basis'), 'domain_profile': plan['domain_profile'],
            'produce_kc_ids': gate['producible_kc_ids'],
            'competencies': [{'kc_id': k, 'statement': kcs[k]['statement'], 'operations': kcs[k]['operations'],
                              'operation_basis': kcs[k]['operation_basis'], 'inferred': kcs[k]['inferred'],
                              'source_anchor_ids': kcs[k]['source_anchor_ids'], 'norm_refs': kcs[k]['norm_refs'],
                              'prerequisite_kc_ids': kcs[k]['prerequisite_kc_ids'], 'coverage': cov[k]['status'],
                              'blocked': gate['blocked_kcs'].get(k)} for k in c['kc_ids']],
            'prerequisite_chapters': [{'chapter_id': d, 'title': titles.get(d)} for d in c['narrative_dependencies']],
            'notation': [n for n in plan['notation_registry'] if n['notation_id'] in c.get('notation_ids', [])],
            'exam_items': [_item(items[q]) for q in c['exam_relevance']['linked_item_ids'] if q not in mismatch],
            # same lexical link, but the item is labelled with another section/session: never this chapter's own item
            'exam_items_other_section': [{**_item(items[q]), 'section_label': items[q].get('section_label'),
                                          'role': 'SECTION_MISMATCH_NOT_THIS_CHAPTERS_ITEM'} for q in sorted(mismatch)],
            # labelled with this chapter's section but not linked to any of its competencies: shown, not dropped
            'section_items_without_link': [{**_item(items[q]), 'section_label': items[q].get('section_label'),
                                            'role': 'SECTION_ITEM_NO_COMPETENCY_LINK_ANSWER_SOURCE_GAP_CANDIDATE'}
                                           for q in c['exam_relevance'].get('section_unlinked_item_ids', [])],
            'requirements': c['requirements'],
            'allowed_source_refs': c['source_package']['element_ids'],
            'allowed_external_refs': supplements,
            'source_elements': [{'element_id': e, 'kind': by[e]['kind'], 'status': by[e]['status'],
                                 'source': src[by[e]['source_id']]['relative_path'],
                                 'authority': src[by[e]['source_id']]['authority'], 'locator': by[e]['locator_str'],
                                 'text': by[e]['text'], 'flags': by[e]['flags']} for e in c['source_package']['element_ids']],
            'gate_findings': gate['findings']}
    for comp in ctx['competencies']:
        a = (gate.get('auto_scope_kcs') or {}).get(comp['kc_id'])
        if a:
            comp['auto_scope'] = {'basis': a['category'], 'reason': a.get('reason'), 'text_element_ids': a['text_element_ids'],
                                  'excluded_visual_element_ids': a['excluded_visual_element_ids'],
                                  'excluded_pages': a['excluded_pages'], 'restrictions': a['restrictions'],
                                  'source_claim_human_verified': False}
    block = review_context_block(review, chapter_id)
    if block is not None:
        ctx['review_evidence'] = block
    eff = gate.get('review_decision_effects')
    if eff is not None:
        ctx['review_decisions'] = eff
        for comp in ctx['competencies']:
            u = eff['pilot_scope_unlocked_kcs'].get(comp['kc_id'])
            if u:
                comp['pilot_scope'] = {'basis': 'PILOT_SCOPE_APPROVED_BY_USER', 'claims': u['claims'],
                                       'restrictions': u['restrictions'],
                                       'source_claim_human_verified': u['source_claim_human_verified']}
            elif comp['kc_id'] in eff['pilot_scope_excluded_kcs']:
                comp['pilot_scope'] = {'basis': 'PILOT_SCOPE_EXCLUDED_WITH_REASON', **eff['pilot_scope_excluded_kcs'][comp['kc_id']]}
    return ctx


def _item(q):
    return {'item_id': q['item_id'], 'wording': q['own_wording'], 'points': q['points'],
            'operations': q['actual_operations'], 'format': q['format']}


def _estimate_tokens(ctx):
    return (len(str(ctx)) + 6000) // 4


class ChapterSelectionError(ContractError):
    """--only-chapter could not be resolved to exactly one chapter of the current plan. No provider call follows."""
    def __init__(self, state, reason):
        super().__init__(f'{state}: {reason}'); self.state = state; self.reason = reason


CHAPTER_ID = re.compile(r'^ch-[0-9a-f]{14}$|^ch-exam-scope-unanchored$')


def select_chapter(plan, gates, chapter_id):
    """Exact id match only: no title search, no index, no fallback to another chapter."""
    if not isinstance(chapter_id, str) or not chapter_id.strip():
        raise ChapterSelectionError('CHAPTER_ID_EMPTY', 'an exact chapter_id from the current plan is required')
    if chapter_id != chapter_id.strip() or not CHAPTER_ID.match(chapter_id):
        raise ChapterSelectionError('CHAPTER_ID_INVALID', f'{chapter_id!r} is not a chapter_id (expected ch-<14 hex>)')
    hits = [c for c in plan['chapters'] if c['chapter_id'] == chapter_id]
    if len(hits) > 1:
        raise ChapterSelectionError('CHAPTER_ID_AMBIGUOUS', f'{chapter_id} occurs {len(hits)} times in the plan')
    if not hits:
        raise ChapterSelectionError('CHAPTER_NOT_FOUND', f'{chapter_id} is not in the current chapter plan '
                                    '(unknown, merged away or changed by re-planning); nothing selected')
    c = hits[0]
    elig = pilot_eligibility(plan, gates)[chapter_id]
    return {'selected_chapter_id': chapter_id, 'title': c['title'], 'position': c['position'],
            'gate': gates[chapter_id]['status'], 'academic_pilot_eligibility': elig['academic_pilot_eligibility'],
            'eligibility_reasons': elig['reasons'], 'blocked_kcs': gates[chapter_id]['blocked_kcs'],
            'gate_findings': gates[chapter_id]['findings'],
            'excluded_chapter_ids': [x['chapter_id'] for x in plan['chapters'] if x['chapter_id'] != chapter_id],
            'plan_fingerprint': chapter_fingerprint(plan, c)}


def chapter_fingerprint(plan, chapter):
    """Identity of the selected scope: chapter, its KCs, its source package, planner version."""
    return digest({'chapter_id': chapter['chapter_id'], 'kc_ids': chapter['kc_ids'],
                   'elements': chapter['source_package']['element_ids'], 'planner': plan['planner_version']})


def planned_actions(plan, gates, manifest=None, only=None, review=None):
    """Every provider action a real chapter run would make. Depends only on chapters and their risk profile, never on
    transport units / chunks and never on budget settings."""
    actions = []
    for c in plan['chapters']:
        g = gates[c['chapter_id']]
        if g['status'] in ('BLOCKED', 'REVIEW_REQUIRED') or (only is not None and c['chapter_id'] != only):
            continue
        est = _estimate_tokens(chapter_context(plan, manifest, c['chapter_id'], g, review)) if manifest else None
        roles = list(CHAPTER_ROLES) + ([RISK_ROLE] if set(c['requirements']['review_requirements']) & RISK_REVIEWS else [])
        for r in roles:
            actions.append({'chapter_id': c['chapter_id'], 'role': r, 'conditional': False, 'estimated_input_tokens': est})
        actions.append({'chapter_id': c['chapter_id'], 'role': REVISION_ROLE, 'conditional': True,
                        'condition': 'only if a review finding is major/blocker', 'estimated_input_tokens': est})
    for i, a in enumerate(actions, 1):
        a['action_id'] = f'act-{i:04d}'
    from .production import ROLES as LEGACY_ROLES
    audit = {'unconditional_calls': sum(not a['conditional'] for a in actions), 'max_calls': len(actions),
             'chapters_planned': len({a['chapter_id'] for a in actions}),
             'chapters_blocked': sum(g['status'] == 'BLOCKED' for g in gates.values()),
             'chapters_review_required': sum(g['status'] == 'REVIEW_REQUIRED' for g in gates.values()),
             'max_calls_per_chapter': MAX_ACTIONS_PER_CHAPTER,
             'legacy_per_chunk_roles_planned': sum(a['role'] in LEGACY_ROLES for a in actions),
             'scope': 'ALL_CHAPTERS' if only is None else 'ONLY_CHAPTER:' + only,
             'depends_on_transport_units': False,
             'estimate_basis': 'chars/4 heuristic of the chapter context + fixed prompt overhead; not a provider count',
             'requires_before_external_call': ['approved budget file (--budget)', 'ResourceBudget reservation per call']}
    if any(sum(1 for a in actions if a['chapter_id'] == c) > MAX_ACTIONS_PER_CHAPTER for c in gates):
        raise ContractError('planned actions exceed the per-chapter cap')
    return actions, audit


def dry_run(root, out, decisions=None, only_chapter=None, review_overlay=None, review_decisions=None, visual_evidence='auto'):
    root = Path(root).expanduser().resolve(); out = Path(out).expanduser().resolve()
    if not root.is_dir():
        raise ContractError('Source root is not accessible')
    if out == root or root in out.parents:
        raise ContractError('Output must be outside the source root')
    if isinstance(decisions, (str, Path)):
        decisions = SemanticDecisions.from_file(decisions)
    overlay = review_load(review_overlay, root) if isinstance(review_overlay, (str, Path)) else review_overlay
    rd = rdec.load(review_decisions, root) if isinstance(review_decisions, (str, Path)) else review_decisions
    m = inventory(root, out)
    plan = compile_curriculum(m, out, decisions=decisions)
    # B8: figure content read by the calling agent (validated store in the course output folder, never the lecture folder)
    from . import visual_evidence as vev
    store = vev.load(root) if visual_evidence == 'auto' else visual_evidence
    vsum = {'pages': 0}
    if store:
        plan, m, vsum = vev.integrate(plan, m, store)
        write_json(out / 'source_inventory.json', m); write_json(out / 'curriculum.json', plan)
    write_json(out / 'agent_vision_summary.json', vsum)
    review = review_evaluate(overlay, m, plan) if overlay is not None else None
    diag = {}
    gates, unattributed = fidelity_gate(plan, m, diag)
    rd_eval = None
    if rd is not None:
        rd_eval = rdec.evaluate(rd, m, plan, gates, review)
        write_json(out / 'chapter_gates_before_review_decisions.json', gates)
        gates = rdec.apply(gates, rd_eval)
    elig = pilot_eligibility(plan, gates)
    selection, sel_error = None, None
    if only_chapter is not None:
        try:
            selection = select_chapter(plan, gates, only_chapter)
        except ChapterSelectionError as e:
            sel_error = {'state': e.state, 'reason': e.reason, 'requested_chapter_id': only_chapter}
    if sel_error:
        actions, audit = [], {'unconditional_calls': 0, 'max_calls': 0, 'chapters_planned': 0, 'scope': 'SELECTION_ERROR',
                              'depends_on_transport_units': False, 'legacy_per_chunk_roles_planned': 0}
    else:
        actions, audit = planned_actions(plan, gates, m, only=only_chapter, review=review)
    blockers = [{'chapter_id': cid, **f} for cid, g in gates.items() for f in g['findings'] if f['severity'] == 'blocker'
                and (only_chapter is None or cid == only_chapter)]
    complete = m['coverage_complete'] and not unattributed
    readiness = ('SELECTION_ERROR' if sel_error else 'BLOCKED' if not audit['chapters_planned'] else
                 'PARTIAL' if blockers or not complete or any(g['status'] != 'READY' for g in gates.values()) else 'READY_FOR_APPROVAL')
    report = {'schema': 'em-dry-run-v1', 'mode': 'DRY_RUN', 'provider_calls_made': 0, 'network_calls_made': 0,
              'course_id': plan['course_id'], 'readiness': readiness,
              'claims': {'source_inventory_complete': m['coverage_complete'], 'all_gaps_attributed_to_chapters': not unattributed,
                         'course_complete': False,
                         'note': 'A dry run never claims completeness: gaps below are open until resolved or accepted.'},
              'chapters': [{'position': c['position'], 'chapter_id': c['chapter_id'], 'title': c['title'],
                            'order_basis': c['order_basis'], 'merged_from': c.get('merged_from', []),
                            'source_ids': c['source_package']['source_ids'], 'kc_ids': c['kc_ids'],
                            'gate': gates[c['chapter_id']]['status'], 'blocked_kcs': gates[c['chapter_id']]['blocked_kcs'],
                            'review_required_kc_count': len(gates[c['chapter_id']].get('review_required_kcs', {})),
                            'academic_pilot_eligibility': elig[c['chapter_id']]['academic_pilot_eligibility'],
                            'eligibility_reasons': elig[c['chapter_id']]['reasons'],
                            'pilot_candidate_score': elig[c['chapter_id']]['pilot_candidate_score'],
                            'academic_release': 'NOT_TESTED', 'source_roles': sorted({plan['source_roles'][s]['role'] for s in c['source_ids']}),
                            'segmentation': c.get('segmentation', []),
                            'open_issue_codes': sorted({f['code'] for f in gates[c['chapter_id']]['findings'] if f['severity'] == 'open_issue'})}
                           for c in plan['chapters']],
              'chapter_ordering': plan['chapter_ordering'], 'chapter_merges': plan['chapter_merges'],
              'blockers': blockers, 'source_gaps': m['gaps'], 'unattributed_blocking_gaps': unattributed,
              'planned_actions': audit, 'gate_rules': GATE_RULES, 'eligibility_rules': ELIGIBILITY_RULES,
              'triage': triage_report(plan, m, gates, diag, elig),
              'selection': ({'mode': 'ALL_CHAPTERS'} if only_chapter is None else
                            {'mode': 'ONLY_CHAPTER', 'status': 'SELECTION_ERROR', **sel_error} if sel_error else
                            {'mode': 'ONLY_CHAPTER', 'status': 'SELECTED_BLOCKED' if selection['gate'] in ('BLOCKED', 'REVIEW_REQUIRED') else
                             'SELECTED_INELIGIBLE' if selection['academic_pilot_eligibility'] == 'INELIGIBLE' else 'SELECTED',
                             **{k: v for k, v in selection.items() if k != 'gate_findings'},
                             'planned_requests_for_selected_chapter': [a for a in actions]}),
              'global_context_note': 'chapters/blockers above describe the whole course plan (analysed); only the '
                                     'selection scope is planned for provider calls' if only_chapter else None}
    pf_targets = ([only_chapter] if selection is not None else [] if only_chapter is not None else
                  [c['chapter_id'] for c in plan['chapters'] if gates[c['chapter_id']]['status'] not in ('BLOCKED', 'REVIEW_REQUIRED')])
    report['production_preflight'] = production_preflight(plan, gates, pf_targets)
    report['review_overlay'] = None if review is None else {
        'overlay_id': review['overlay_id'], 'overlay_version': review['overlay_version'],
        'overlay_sha256': review['overlay_sha256'], 'counts': review['counts'], 'changes_gates': False,
        'rejected': review['rejected'],
        'human_verified': sum(a['human_verified'] for a in review['accepted'])}
    report['review_decisions'] = None if rd_eval is None else {
        'decision_set_id': rd_eval['decision_set_id'], 'version': rd_eval['version'],
        'decisions_sha256': rd_eval['decisions_sha256'], 'counts': rd_eval['counts'], 'rejected': rd_eval['rejected'],
        'page_reviews': rd_eval['page_reviews'],
        'unlocked_kcs': {cid: sorted(g['review_decision_effects']['pilot_scope_unlocked_kcs']) for cid, g in gates.items()
                         if g['review_decision_effects']['pilot_scope_unlocked_kcs']},
        'academic_release': 'NOT_TESTED'}
    if rd_eval is not None:
        write_json(out / 'review_decisions_eval.json', rd_eval)
    if review is not None:
        write_json(out / 'review_overlay_eval.json', review)
    if selection is not None:
        # exactly the context produce_chapter() would hand to the chapter roles for this selection
        ctx = chapter_context(plan, m, only_chapter, gates[only_chapter], review)
        write_json(out / 'selected_chapter_context.json', ctx)
        report['selection']['context_bytes'] = len(json.dumps(ctx, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8'))
    write_json(out / 'chapter_gates.json', gates)
    write_json(out / 'triage_diagnostics.json', report['triage'])
    write_json(out / 'planned_actions.json', actions)
    write_json(out / 'dry_run_report.json', report)
    return report, plan, m, gates, actions


def source_fingerprint(manifest, element_ids):
    by = {e['element_id']: e for e in manifest['elements']}
    return {e: (by[e]['raw_span_hash'] + '|' + by[e]['extraction_hash']) if e in by else None for e in sorted(element_ids)}


def ast_validity(ast, manifest):
    """Dependency check for incremental runs (full cache engine is P7): any changed/removed element -> STALE."""
    old = ast['version']['source_fingerprint']
    now = source_fingerprint(manifest, old)
    changed = sorted(e for e in old if now[e] is not None and now[e] != old[e])
    missing = sorted(e for e in old if now[e] is None)
    status = 'VALID' if not changed and not missing else 'STALE_SOURCE_CHANGED'
    return {'status': status, 'changed_element_ids': changed, 'missing_element_ids': missing,
            'action': 'none' if status == 'VALID' else 're-draft and re-review this chapter; old claims are not valid'}


def fingerprint_digest(fp):
    return digest(fp)


def triage_report(plan, m, gates, diag, elig):
    """Course-level diagnostics: roles, KC candidate rejections, items by kind, gap -> element -> KC -> chapter
    propagation (every gap accounted for), and a prioritised human/semantic review queue. No source text bodies."""
    from collections import Counter
    from .triage import VISUAL_RULES
    by = {e['element_id']: e for e in m['elements']}
    loc2el = {e['locator_str']: e['element_id'] for e in m['elements']}
    kcs = {k['kc_id']: k for k in plan['competencies']}
    prop = diag.get('propagation', []); deco = diag.get('decorative_visual_candidates', {})
    by_el = {}
    for p in prop:
        for e in p['element_ids']:
            by_el.setdefault(e, []).append(p)
    gaps = []
    for i, g in enumerate(m['gaps']):
        rec = {'gap_index': i, 'code': g['code'], 'source_id': g['source_id'], 'locator': g['locator_str'], 'severity': g['severity']}
        eid = loc2el.get(g['locator_str'])
        if eid:
            rec['element_id'] = eid
            hits = by_el.get(eid, [])
            rec['effect'] = ('BLOCK' if any(h['effect'] == 'BLOCK' for h in hits) else 'REVIEW' if hits else
                             'NONE_DECORATIVE_CANDIDATE' if eid in deco else 'NO_DEPENDENT_COMPETENCY')
            rec['rule'] = sorted({h['rule'] for h in hits}) or ([deco[eid]] if eid in deco else ['no competency anchored on this page'])
            rec['kc_ids'] = sorted({h['kc_id'] for h in hits}); rec['chapter_ids'] = sorted({h['chapter_id'] for h in hits})
        elif g['code'] == 'TEXT_LAYER_MISSING':
            pg = re.search(r'Page (\d+)', str(g['detail']))
            rec['page'] = int(pg.group(1)) if pg else None
            scope, _ = scan_scope(m, g['source_id'])
            hits = [p for p in prop if p['rule'].startswith('S') and p['cause'] in ('SCANNED_PAGE_NO_OCR', 'ADJACENT_PAGE_UNREADABLE')
                    and kcs.get(p['kc_id'], {}).get('source_ids', [None])[0] == g['source_id']]
            if scope == 'LOCAL':
                hits = [p for p in hits if any(abs(((by[a].get('locator') or {}).get('page') or -9) - rec['page']) <= 1
                                               for a in kcs[p['kc_id']]['source_anchor_ids'] if by[a]['source_id'] == g['source_id'])]
            rec.update(scope=scope, effect='BLOCK' if any(h['effect'] == 'BLOCK' for h in hits) else 'REVIEW' if hits else 'CHAPTER_REVIEW',
                       rule=sorted({h['rule'] for h in hits}) or ['S3_SCAN_CHAPTER_REVIEW'],
                       kc_ids=sorted({h['kc_id'] for h in hits}), chapter_ids=sorted({h['chapter_id'] for h in hits}))
        else:
            rec.update(effect='SOURCE_OR_LINK_LEVEL', rule=['see chapter findings'], kc_ids=[], chapter_ids=[])
        gaps.append(rec)
    summary = Counter((r['code'], r['effect']) for r in gaps)
    roles = plan['source_roles']
    queue = []
    def q(prio, kind, obj, reason, action, evidence=()):
        queue.append({'priority': prio, 'kind': kind, 'object_id': obj, 'reason': reason, 'action': action, 'evidence': list(evidence)[:10]})
    for r in roles.values():
        if r['role'] == 'REVIEW_REQUIRED':
            q('P1', 'SOURCE_ROLE', r['source_id'], 'role unclear: ' + '; '.join(e['detail'] for e in r['evidence']), 'confirm role (academic/admin/template/case/practice)')
        elif r['role'] in ('COURSE_ADMINISTRATION', 'TEMPLATE_LAYOUT', 'CASE_STUDY_BRIEF', 'PRACTICE_QUESTIONS'):
            q('P3', 'SOURCE_ROLE', r['source_id'], f"classified {r['role']} ({r['confidence']}); excluded from chapters",
              'spot-check the exclusion', [e.get('element_id') or e['detail'] for e in r['evidence']])
    ranked = sorted(elig.items(), key=lambda kv: -kv[1]['pilot_candidate_score'])
    for rank, (cid, e) in enumerate(ranked, 1):
        if e['academic_pilot_eligibility'] == 'INELIGIBLE':
            continue
        prio = 'P1' if rank <= 3 else 'P2'
        for why in e['reasons']:
            q(prio, 'CHAPTER_ELIGIBILITY', cid, why, 'resolve before pilot selection')
        rv = gates[cid].get('review_required_kcs', {})
        if rv:
            els = sorted({x for f in gates[cid]['findings'] if f['severity'] == 'review' for x in f['element_ids']})
            q(prio, 'VISUAL_OR_SCAN_REVIEW', cid, f'{len(rv)} competencies wait for relevance review of {len(els)} visual elements',
              'look at the rendered pages; mark each visual decorative / needs transcription', els)
    for sid, n in Counter(by[e]['source_id'] for e in deco).items():
        sample = [e for e in deco if by[e]['source_id'] == sid][:3]
        q('P2', 'DECORATIVE_SAMPLE', sid, f'{n} visuals classified as decoration candidates by repetition/size rules',
          'verify a sample of 3; if any carries content, the rule is wrong for this source', sample)
    for g in gaps:
        if g['code'] == 'TEXT_LAYER_MISSING':
            q('P2', 'SCAN_PAGE', g['source_id'], f"page {g.get('page')} has no text layer ({g['scope']})", 'OCR or confirm irrelevance')
    order = plan['chapter_ordering']
    if order['status'] != 'SOURCE_STATED':
        q('P2', 'CHAPTER_ORDER', 'course', f"order status {order['status']} ({order['primary_basis']})", 'confirm chapter order')
    if plan['domain_profile']['active_profiles'] == ['UNRESOLVED']:
        q('P3', 'DOMAIN_PROFILE', 'course', 'no subject profile with cross-source evidence', 'state the subject or accept UNRESOLVED')
    items = plan['assessment_items']
    return {'schema': 'em-triage-v1',
            'source_roles': [{k: v for k, v in r.items() if k != 'note'} for r in roles.values()],
            'domain_profile': {k: v for k, v in plan['domain_profile'].items() if k != 'per_source'},
            'kc_candidates': {'accepted': len(plan['competencies']),
                              'accepted_by_origin': dict(Counter(k['origin'] for k in plan['competencies'])),
                              'rejected_by_reason': dict(Counter(r['reason'] for r in plan.get('rejected_kc_candidates', [])))},
            'assessment_items_by_kind': dict(Counter(i['assessment_kind'] for i in items)),
            'assessment_items_with_points': sum(1 for i in items if i['points'] is not None),
            'gap_accounting': {'total_gaps': len(m['gaps']), 'accounted': len(gaps), 'by_code_and_effect':
                               {f'{c}|{e}': n for (c, e), n in sorted(summary.items())}, 'gaps': gaps},
            'propagation_rules': {**VISUAL_RULES, 'S0_SCAN_SOURCE_WIDE': 'textless pages >=20% of pages or <=5-page source: all KCs of the source blocked',
                                  'S1_SCAN_ANCHOR_PAGE': 'KC anchored on a textless page: BLOCKED',
                                  'S2_SCAN_NEIGHBOUR_PAGE': 'KC anchored on a page next to a textless page: REVIEW_REQUIRED',
                                  'S3_SCAN_CHAPTER_REVIEW': 'chapter with textless pages: chapter-level review (content unknown)'},
            'propagation_summary': {f"{p['cause']}|{p['rule']}|{p['effect']}": n for p, n in
                                    [(dict(zip(('cause', 'rule', 'effect'), k)), v) for k, v in
                                     Counter((p['cause'], p['rule'], p['effect']) for p in prop).items()]},
            'kc_level_assignments': len(prop),
            'review_queue': sorted(queue, key=lambda x: x['priority']),
            'semantic_review_contract': {
                'schema': 'em-semantic-decisions-v1', 'status': 'DECLARED_NOT_EXECUTED',
                'tasks': ['confirm/merge/split topic-candidate competencies per chapter (kinds operation, chapter_merge)',
                          'link PRACTICE items to competencies (kind link)',
                          'confirm chapter order against the schedule table (kind chapter_order)',
                          'confirm source roles marked REVIEW_REQUIRED'],
                'note': 'requires a separately approved model or human review; nothing here is a semantic judgement'}}
