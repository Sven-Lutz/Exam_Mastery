"""B6: structured review decisions that may open the REVIEW_REQUIRED gate of single competencies for a pilot.

Subject-neutral, offline, deterministic. Four separate levels that never imply each other:
- model_review                     MODEL_REVIEWED proposal; never has an effect on any gate
- pilot_scope_approval             a named HUMAN reviewer allows an experimental pilot to work on this claim/KC.
                                   It is a scope choice, NOT a statement that the claim is true.
- source_claim_human_verification  a named HUMAN reviewer compared this concrete claim with the original page.
                                   Recorded and passed on; never required for, and never set by, a scope approval.
- academic release                 not part of this contract at all (separate decision after generation).

A decision binds to: chapter_id + kc_id + one gate cause (element_id of the visual, or the rendered page of a
textless neighbour page) + source SHA-256 + page + page-render SHA-256 (+ visual asset SHA-256 when it has one)
+ claim + decision_type + reason + reviewer identity/version/date. Anything missing, stale, orphaned, unapproved,
contradictory or forged fails closed: the decision is rejected or has no effect, and the KC stays REVIEW_REQUIRED.

A KC leaves REVIEW_REQUIRED only if EVERY review cause the gate found for it is covered by an effective unlocking
decision. BLOCKED KCs are never unlocked; they can only be recorded as excluded from the pilot scope (they stay
in the inventory and in the gate). Nothing here changes chapter eligibility rules or academic_release.
"""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path
from .common import ContractError, sha_file
from .checkpoints import digest

SCHEMA = 'em-review-decisions-v1'
UNLOCKING = {'DECORATIVE_FOR_THIS_CLAIM', 'TEXT_REDUNDANT_FOR_THIS_CLAIM', 'VISUAL_TRANSCRIBED_FOR_PILOT'}
NON_UNLOCKING = {'ESSENTIAL_VISUAL_UNRESOLVED', 'PILOT_SCOPE_EXCLUDED_WITH_REASON'}
DECISION_TYPES = UNLOCKING | NON_UNLOCKING
CLAIM_KINDS = {'QUALITATIVE', 'QUANTITATIVE', 'DEFINITION', 'STRUCTURE', 'CALCULATION', 'LEGAL_NORM'}
CAUSE_CODES = {'VISUAL_RELEVANCE_UNKNOWN', 'ADJACENT_PAGE_UNREADABLE'}
REVIEWER_TYPES = {'HUMAN', 'MODEL'}
APPROVAL_KEYS = {'approved', 'approver_id', 'date', 'statement', 'approved_content_sha256'}
VERIFICATION_KEYS = {'verified', 'verifier_id', 'date', 'method', 'compared_against_page_render_sha256', 'verified_content_sha256'}
LEGAL_VERIFIED = 'HUMAN_VERIFIED_AGAINST_OFFICIAL_NORM'
PAGE_CAUSE = 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN'
PAGE_UNLOCKING = {'PAGE_ESSENTIAL_TRANSCRIBED_UNCERTAIN_FOR_PILOT'}
PAGE_REVIEW_TYPES = PAGE_UNLOCKING | {'PAGE_ESSENTIAL_UNRESOLVED'}   # no 'decorative'/'irrelevant' type on purpose
PAGE_REVIEW_FIELDS = ('review_id', 'course_id', 'chapter_id', 'source_ref', 'page', 'cause_code', 'page_render_element_id',
                      'page_render_sha256', 'image_asset_sha256', 'annotation_ids', 'decision_type', 'reason',
                      'uncertainty_statement', 'model_review', 'pilot_scope_approval', 'source_claim_human_verification')
PAGE_RESTRICTIONS = ['PAGE_HAS_NO_TEXT_LAYER', 'PAGE_CONTENT_ONLY_FROM_REVIEW_OVERLAY', 'QUALITATIVE_ONLY_AS_ANNOTATED',
                     'NO_VALUES_POSITIONS_OR_BOUNDARIES_BEYOND_ANNOTATION']
ISO_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
NUM = re.compile(r'\d[\d.,]*')
POLICY = ('Review decisions record a human pilot-scope choice per claim. PILOT_SCOPE_APPROVED_BY_USER means: an '
          'experimental pilot may write about exactly the stated claim. It does not mean the claim is verified; only '
          'source_claim_human_verified=true says a human compared the claim with the original page. Decorative or '
          'text-redundant visuals are not sources of numbers. Restrictions listed per KC are binding for this draft. '
          'LEGAL_STATUS_NOT_VERIFIED: present the lecture statement as lecture content, do not give a binding legal '
          'model answer. AS_OF_SOURCE_DATE: numbers are historical survey values, never current figures.')


def _norm_num(s):
    return re.sub(r'[.,\s]', '', s)


def load(path, source_root=None):
    path = Path(path).expanduser().resolve()
    if source_root is not None:
        root = Path(source_root).expanduser().resolve()
        if path == root or root in path.parents:
            raise ContractError('review decisions must not live inside the source root')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != SCHEMA:
        raise ContractError(f'review decisions schema must be {SCHEMA}')
    for f in ('decision_set_id', 'version', 'sources', 'reviewers', 'decisions'):
        if f not in data:
            raise ContractError(f'review decisions lack {f}')
    return data, sha_file(path)


# B6.2 content binding: an approval names the SHA-256 of exactly what was approved. The hash covers the whole entry
# (claim, type, restrictions, reasons, anchors, ...) except the approval/verification fields themselves, plus the
# decision set identity, the overlay SHA, the source entry and the chapter scope (KCs, source package, session
# assignment). Any later change makes the approval mismatch -> rejected, never silently accepted.
_UNBOUND = {'pilot_scope_approval', 'source_claim_human_verification'}


def _chapter_binding(plan, chapter_id):
    c = next((c for c in plan.get('chapters', []) if c.get('chapter_id') == chapter_id), None)
    if c is None:
        return None
    er = c.get('exam_relevance') or {}
    return {'course_id': plan.get('course_id'), 'chapter_id': chapter_id, 'planner': plan.get('planner_version'),
            'kc_ids': sorted(c.get('kc_ids', [])), 'source_elements': sorted((c.get('source_package') or {}).get('element_ids', [])),
            'exam_section': {k: sorted(er[k]) if isinstance(er.get(k), list) else er.get(k)
                             for k in ('section_number', 'linked_item_ids', 'section_mismatch_item_ids', 'section_unlinked_item_ids')}}


def _entry_sha(kind, entry, data, plan):
    body = {k: v for k, v in entry.items() if k not in _UNBOUND and not str(k).startswith('_')}
    src = next((s for s in data.get('sources', []) if s.get('source_ref') == entry.get('source_ref')), None)
    return digest({'kind': kind, 'schema': data.get('schema'), 'decision_set_id': data.get('decision_set_id'),
                   'overlay_sha256': data.get('overlay_sha256'), 'source': src, 'entry': body,
                   'chapter': _chapter_binding(plan, entry.get('chapter_id'))})


def _didactic_binding(data, plan, s):
    """Scope set also binds what the chapter's questions are taken to demand and how coverage reads them, so a later
    change of operation/link decisions invalidates the one signature."""
    by_dec = {d.get('decision_id'): d for d in data.get('decisions', []) if isinstance(d, dict)}
    by_pr = {r.get('review_id'): r for r in data.get('page_reviews') or [] if isinstance(r, dict)}
    cids = sorted({by_dec[i].get('chapter_id') for i in s.get('decision_ids') or [] if i in by_dec} |
                  {by_pr[i].get('chapter_id') for i in s.get('page_review_ids') or [] if i in by_pr} - {None})
    chapters = {c.get('chapter_id'): c for c in plan.get('chapters', [])}
    items = {q.get('item_id'): q for q in plan.get('assessment_items', [])}
    cov = {r.get('kc_id'): r for r in plan.get('coverage', [])}
    out = {}
    for cid in cids:
        c = chapters.get(cid) or {}
        qids = sorted((c.get('exam_relevance') or {}).get('linked_item_ids') or [])
        out[cid] = {'items': {q: [sorted((items.get(q) or {}).get('actual_operations') or []), (items.get(q) or {}).get('operation_basis')] for q in qids},
                    'coverage': {k: [(cov.get(k) or {}).get('status'), sorted((cov.get(k) or {}).get('evidence_item_ids') or []),
                                     sorted((cov.get(k) or {}).get('recall_only_item_ids') or [])] for k in sorted(c.get('kc_ids', []))}}
    return out


def content_hashes(data, plan):
    """SHA-256 a human copies into approved_content_sha256 (or verified_content_sha256) AFTER reading the content.
    Computing it approves nothing. Bundles hash their exact member set and each member's content hash."""
    if isinstance(data, tuple):
        data = data[0]
    dec = {d.get('decision_id'): _entry_sha('decision', d, data, plan) for d in data.get('decisions', []) if isinstance(d, dict)}
    bundles = {b.get('bundle_id'): digest({'kind': 'bundle', 'bundle_id': b.get('bundle_id'),
                                           'decision_ids': sorted(b.get('decision_ids') or []),
                                           'members': {i: dec.get(i) for i in sorted(b.get('decision_ids') or [])}})
               for b in data.get('bundle_approvals') or [] if isinstance(b, dict)}
    pages = {r.get('review_id'): _entry_sha('page_review', r, data, plan) for r in data.get('page_reviews') or [] if isinstance(r, dict)}
    out_set = None
    s = data.get('pilot_scope_set_approval')
    if isinstance(s, dict):   # B6.4: one scope signature over an explicit member list; binds every member's content hash
        out_set = digest({'kind': 'scope_set', 'set_id': s.get('set_id'), 'decision_set_id': data.get('decision_set_id'),
                          'decision_ids': sorted(s.get('decision_ids') or []), 'page_review_ids': sorted(s.get('page_review_ids') or []),
                          'members': {i: dec.get(i) for i in sorted(s.get('decision_ids') or [])},
                          'page_members': {i: pages.get(i) for i in sorted(s.get('page_review_ids') or [])},
                          'didactics': _didactic_binding(data, plan, s)})
    return {'decisions': dec, 'bundles': bundles, 'page_reviews': pages, 'scope_set': out_set,
            'note': 'content fingerprints only; copying one into an approval is the human act, computing it approves nothing'}


def gate_causes(gate):
    """{kc_id: {cause_key: cause}} for every review finding of the gate. cause_key is 'element:<id>' for a visual
    or 'page:<source_id>:<page>' for a textless neighbour page."""
    out = {}
    for f in gate['findings']:
        if f['severity'] != 'review' or not f['kc_ids'] or f['code'] not in CAUSE_CODES:
            continue
        kid = f['kc_ids'][0]
        if f['code'] == 'VISUAL_RELEVANCE_UNKNOWN':
            for e in f['element_ids']:
                out.setdefault(kid, {})['element:' + e] = {'code': f['code'], 'element_id': e, 'rule': f['rule']}
        else:
            for p in f.get('pages', []):
                out.setdefault(kid, {})[f"page:{f['source_id']}:{p}"] = {'code': f['code'], 'source_id': f['source_id'],
                                                                        'page': p, 'rule': f['rule']}
    return out


def _page_render(by_page, sid, page):
    return next((e for e in by_page.get((sid, page), []) if e['kind'] == 'rendered_page' and e.get('asset')), None)


def _valid_date(s):
    if not isinstance(s, str) or not ISO_DATE.match(s):
        return False
    try:
        return date.fromisoformat(s) <= date.today()
    except ValueError:
        return False


def _check(d, ctx):
    """-> (errors, info). info carries the resolved cause key and engine-derived restrictions."""
    errs = []
    for f in ('decision_id', 'chapter_id', 'kc_id', 'source_ref', 'page', 'decision_type', 'claim', 'reason',
              'page_render_sha256', 'model_review', 'pilot_scope_approval', 'source_claim_human_verification'):
        if f not in d:
            errs.append(('MISSING_FIELD', f))
    if errs:
        return errs, None
    if d['decision_type'] not in DECISION_TYPES:
        errs.append(('INVALID_DECISION_TYPE', repr(d['decision_type'])))
    claim = d['claim'] if isinstance(d['claim'], dict) else {}
    if not claim.get('claim_id') or not str(claim.get('text', '')).strip() or claim.get('kind') not in CLAIM_KINDS:
        errs.append(('INVALID_CLAIM', 'claim needs claim_id, text and kind in ' + '/'.join(sorted(CLAIM_KINDS))))
    if not str(d['reason']).strip():
        errs.append(('MISSING_REASON', d['decision_id']))
    gate = ctx['gates'].get(d['chapter_id'])
    if gate is None:
        return errs + [('CHAPTER_NOT_IN_PLAN', d['chapter_id'])], None
    chapter = ctx['chapters'][d['chapter_id']]
    if d['kc_id'] not in chapter['kc_ids']:
        return errs + [('ORPHAN_KC', f"{d['kc_id']} is not a competency of {d['chapter_id']}")], None
    src = ctx['srcmap'].get(d['source_ref'])
    if src is None:
        return errs + [('SOURCE_NOT_IN_MANIFEST', d['source_ref'])], None
    if src['stale']:
        errs.append(('STALE_SOURCE_HASH', f"{src['relative_path']}: decision file {str(src['sha256'])[:12]} != manifest "
                                          f"{str(src['manifest_sha256'])[:12]}"))
    sid, page = src['source_id'], d['page']
    render = _page_render(ctx['by_page'], sid, page)
    if render is None:
        errs.append(('NO_PAGE_RENDER', f'page {page} has no rendered page to bind the decision to'))
    elif render['asset']['sha256'] != d['page_render_sha256']:
        errs.append(('PAGE_RENDER_HASH_MISMATCH', f'page {page}: decision {str(d["page_render_sha256"])[:12]} != '
                                                  f'render {render["asset"]["sha256"][:12]}'))
    kc_causes = ctx['causes'].get(d['chapter_id'], {}).get(d['kc_id'], {})
    cause_key, restrictions = None, set(d.get('restrictions') or [])
    if d['decision_type'] == 'PILOT_SCOPE_EXCLUDED_WITH_REASON':
        kc = ctx['kcs'][d['kc_id']]
        anchor_pages = {(ctx['by'][a].get('locator') or {}).get('page') for a in kc['source_anchor_ids']
                        if a in ctx['by'] and ctx['by'][a]['source_id'] == sid}
        if page not in anchor_pages:
            errs.append(('EXCLUSION_NOT_ON_ANCHOR_PAGE', f'page {page} is not an anchor page of {d["kc_id"]}'))
        if d['kc_id'] not in gate['blocked_kcs'] and d['kc_id'] not in gate.get('review_required_kcs', {}):
            errs.append(('EXCLUSION_OF_PRODUCIBLE_KC', 'only BLOCKED/REVIEW_REQUIRED competencies can be excluded'))
        if not d.get('coverage_consequences'):
            errs.append(('EXCLUSION_WITHOUT_CONSEQUENCES', 'state which objectives/questions lose coverage'))
        cause_key = 'kc:' + d['kc_id']
    else:
        eid = d.get('cause_element_id')
        el = ctx['by'].get(eid)
        if el is None:
            return errs + [('UNKNOWN_ELEMENT_ID', repr(eid))], None
        if el['source_id'] != sid or (el.get('locator') or {}).get('page') != page:
            errs.append(('ELEMENT_WRONG_PAGE', f'{eid} is not on page {page} of {d["source_ref"]}'))
        if el['kind'] == 'rendered_page':
            cause_key = f'page:{sid}:{page}'
        else:
            cause_key = 'element:' + eid
            if el.get('asset') and d.get('asset_sha256') != el['asset']['sha256']:
                errs.append(('ASSET_HASH_MISMATCH', f'{eid}: asset {str(d.get("asset_sha256"))[:12]} != {el["asset"]["sha256"][:12]}'))
        if cause_key not in kc_causes:
            errs.append(('CAUSE_NOT_IN_GATE', f'{cause_key} is not a review cause of {d["kc_id"]} in the current gate'))
        if d['kc_id'] in gate['blocked_kcs']:
            errs.append(('KC_BLOCKED', 'a BLOCKED competency cannot be opened by a review decision'))
        kind = claim.get('kind')
        if d['decision_type'] == 'DECORATIVE_FOR_THIS_CLAIM' and kind in ('QUANTITATIVE', 'CALCULATION'):
            errs.append(('QUANTITATIVE_CLAIM_FROM_DECORATIVE_VISUAL', 'a decorative visual cannot support numbers; '
                                                                      'use TEXT_REDUNDANT with text evidence or a transcription'))
        if d['decision_type'] == 'TEXT_REDUNDANT_FOR_THIS_CLAIM':
            tev = d.get('text_evidence_element_ids') or []
            tels = [ctx['by'].get(t) for t in tev]
            if not tev or any(t is None or t['source_id'] != sid or not (t.get('text') or '').strip() for t in tels):
                errs.append(('TEXT_EVIDENCE_INVALID', 'needs existing text elements of the same source'))
            elif kind in ('QUANTITATIVE', 'CALCULATION'):
                text = ' '.join(t['text'] for t in tels)
                have = {_norm_num(n) for n in NUM.findall(text)}
                missing = [v for v in claim.get('required_values', []) if _norm_num(str(v)) not in have]
                if not claim.get('required_values') or missing:
                    errs.append(('VALUES_NOT_IN_TEXT_EVIDENCE', f'required_values missing from text evidence: {missing or "none listed"}'))
        if d['decision_type'] == 'VISUAL_TRANSCRIBED_FOR_PILOT':
            ann = d.get('annotation_ids') or []
            if not ann:
                errs.append(('TRANSCRIPTION_WITHOUT_ANNOTATION', 'cite accepted overlay annotations'))
            elif ctx['overlay'] is None:
                errs.append(('OVERLAY_MISSING', 'decision cites annotations but no review overlay is active'))
            else:
                if ctx['data'].get('overlay_sha256') != ctx['overlay']['overlay_sha256']:
                    errs.append(('STALE_OVERLAY', 'decision file names another overlay SHA-256 than the active one'))
                acc = {a['annotation_id']: a for a in ctx['overlay']['accepted']}
                for aid in ann:
                    a = acc.get(aid)
                    if a is None:
                        errs.append(('ANNOTATION_NOT_ACCEPTED', aid))
                    elif a['source']['source_id'] != sid or a['page'] != page or a['chapter_id'] != d['chapter_id']:
                        errs.append(('ANNOTATION_WRONG_ANCHOR', f'{aid} is not on page {page} of this chapter/source'))
        if kind == 'LEGAL_NORM':
            lv = d.get('legal_verification') or {}
            if lv.get('status') == LEGAL_VERIFIED:
                r = ctx['reviewers'].get(lv.get('verifier_id'))
                if not (r and r.get('type') == 'HUMAN' and lv.get('norm_ref') and lv.get('official_url') and _valid_date(lv.get('as_of_date'))):
                    errs.append(('UNSUPPORTED_LEGAL_VERIFICATION', 'needs HUMAN verifier, norm_ref, official_url, as_of_date'))
            else:
                restrictions |= {'LEGAL_STATUS_NOT_VERIFIED', 'NO_BINDING_LEGAL_MODEL_SOLUTION'}
    if claim.get('as_of'):
        restrictions.add('AS_OF_SOURCE_DATE')
    mr = d['model_review'] or {}
    if mr and mr.get('status') not in (None, 'MODEL_REVIEWED'):
        errs.append(('MODEL_REVIEW_OVERCLAIMS', 'model_review.status can only be MODEL_REVIEWED'))
    approved = _approval(d['pilot_scope_approval'], ctx, errs, d.get('_expected_approval_sha'), d.get('_set_code') or bool(d.get('_bundle_id')))
    verified = _verification(d['source_claim_human_verification'], d['page_render_sha256'], ctx, errs, d.get('_content_sha'))
    return errs, {'cause_key': cause_key, 'approved': approved, 'verified': verified, 'restrictions': sorted(restrictions)}


def _approval(ap, ctx, errs, expected=None, bundle=False):
    """pilot_scope_approval: True only for a registered HUMAN with name, identity_version, a valid past date and the
    content hash of exactly the approved entry (bundle/scope set: of the exact member set and contents).
    bundle: False, True (bundle) or the error code to report for a scope set."""
    if ap is None:
        return False
    if not isinstance(ap, dict) or set(ap) - APPROVAL_KEYS:
        errs.append(('SCOPE_APPROVAL_SETS_OTHER_FIELDS', f'pilot_scope_approval may only contain {sorted(APPROVAL_KEYS)}'))
        return False
    if ap.get('approved') is True:
        r = ctx['reviewers'].get(ap.get('approver_id'))
        if r is None:
            errs.append(('UNKNOWN_APPROVER', repr(ap.get('approver_id'))))
        elif r.get('type') != 'HUMAN' or not r.get('identity_version') or not r.get('display_name'):
            errs.append(('APPROVER_NOT_HUMAN', f"{ap.get('approver_id')} is {r.get('type')}"))
        elif not _valid_date(ap.get('date')):
            errs.append(('INVALID_APPROVAL_DATE', repr(ap.get('date'))))
        elif not ap.get('approved_content_sha256'):
            errs.append(('APPROVAL_NOT_CONTENT_BOUND', 'approved_content_sha256 missing: copy the content hash of what you approved'))
        elif ap['approved_content_sha256'] != expected:
            errs.append((bundle if isinstance(bundle, str) else 'BUNDLE_CONTENT_CHANGED' if bundle else 'APPROVAL_CONTENT_CHANGED',
                         f"approved {str(ap['approved_content_sha256'])[:12]} != current {str(expected)[:12]}: content changed after approval"))
        else:
            return True
    elif ap.get('approved') not in (False, None):
        errs.append(('INVALID_APPROVAL', repr(ap.get('approved'))))
    return False


def _verification(hv, render_sha, ctx, errs, expected=None):
    """source_claim_human_verification: separate from scope; True only if a HUMAN compared against this page render."""
    if hv is None:
        return False
    if not isinstance(hv, dict) or set(hv) - VERIFICATION_KEYS:
        errs.append(('INVALID_VERIFICATION', 'unexpected fields'))
    elif hv.get('verified') is True:
        r = ctx['reviewers'].get(hv.get('verifier_id'))
        if not (r and r.get('type') == 'HUMAN' and r.get('identity_version')):
            errs.append(('VERIFIER_NOT_HUMAN', repr(hv.get('verifier_id'))))
        elif not _valid_date(hv.get('date')) or not str(hv.get('method', '')).strip():
            errs.append(('INVALID_VERIFICATION', 'needs date and method'))
        elif hv.get('compared_against_page_render_sha256') != render_sha:
            errs.append(('VERIFICATION_NOT_AGAINST_THIS_PAGE', 'compared_against_page_render_sha256 must equal page_render_sha256'))
        elif not hv.get('verified_content_sha256'):
            errs.append(('VERIFICATION_NOT_CONTENT_BOUND', 'verified_content_sha256 missing'))
        elif hv['verified_content_sha256'] != expected:
            errs.append(('VERIFICATION_CONTENT_CHANGED', 'claim/entry changed after verification'))
        else:
            return True
    return False


def page_causes(gate):
    """{'page:<source_id>:<page>': finding} for every chapter-level textless-page finding of the gate."""
    out = {}
    for f in gate['findings']:
        if f['code'] == PAGE_CAUSE and f['severity'] == 'review' and not f['kc_ids']:
            for p in f.get('pages') or []:
                out[f"page:{f.get('source_id')}:{p}"] = f
    return out


def _check_page(r, ctx):
    """A chapter-level review of one textless page. Binding: course, chapter, source SHA, page, rendered-page element
    and SHA, image asset SHA, overlay SHA + PAGE_IMAGE annotations, decision type, reason, HUMAN approver/date."""
    errs = [('MISSING_FIELD', f) for f in PAGE_REVIEW_FIELDS if f not in r]
    if errs:
        return errs, None
    if r['decision_type'] not in PAGE_REVIEW_TYPES:
        errs.append(('INVALID_PAGE_REVIEW_TYPE', f"{r['decision_type']!r}; allowed: {sorted(PAGE_REVIEW_TYPES)}"))
    if r['cause_code'] != PAGE_CAUSE:
        errs.append(('INVALID_CAUSE_CODE', repr(r['cause_code'])))
    if not str(r['reason']).strip():
        errs.append(('MISSING_REASON', r['review_id']))
    if r['course_id'] != ctx['course_id']:
        errs.append(('COURSE_MISMATCH', f"{r['course_id']!r} != {ctx['course_id']!r}"))
    gate = ctx['gates'].get(r['chapter_id'])
    if gate is None:
        return errs + [('CHAPTER_NOT_IN_PLAN', r['chapter_id'])], None
    src = ctx['srcmap'].get(r['source_ref'])
    if src is None:
        return errs + [('SOURCE_NOT_IN_MANIFEST', r['source_ref'])], None
    if src['stale']:
        errs.append(('STALE_SOURCE_HASH', f"{src['relative_path']}: {str(src['sha256'])[:12]} != {str(src['manifest_sha256'])[:12]}"))
    sid, page = src['source_id'], r['page']
    el = ctx['by'].get(r['page_render_element_id'])
    if el is None or el['kind'] != 'rendered_page' or el['source_id'] != sid or (el.get('locator') or {}).get('page') != page:
        errs.append(('PAGE_RENDER_ELEMENT_INVALID', f"{r['page_render_element_id']!r} is not the rendered page {page}"))
    elif (el.get('asset') or {}).get('sha256') != r['page_render_sha256']:
        errs.append(('PAGE_RENDER_HASH_MISMATCH', f"page {page}: {str(r['page_render_sha256'])[:12]} != {el['asset']['sha256'][:12]}"))
    imgs = {e['asset']['sha256'] for e in ctx['by_page'].get((sid, page), []) if e['kind'] == 'image' and e.get('asset')}
    if imgs and r['image_asset_sha256'] not in imgs:
        errs.append(('ASSET_HASH_MISMATCH', f"image_asset_sha256 {str(r['image_asset_sha256'])[:12]} matches no image on page {page}"))
    if not imgs and r['image_asset_sha256'] is not None:
        errs.append(('ASSET_HASH_MISMATCH', f'page {page} has no image element'))
    key = f'page:{sid}:{page}'
    if key not in page_causes(gate):
        errs.append(('CAUSE_NOT_IN_GATE', f'{key} is not an open textless-page finding of {r["chapter_id"]}'))
    restrictions = list(PAGE_RESTRICTIONS)
    if r['decision_type'] in PAGE_UNLOCKING:
        if not str(r['uncertainty_statement'] or '').strip():
            errs.append(('MISSING_UNCERTAINTY_STATEMENT', 'state what the reading cannot establish'))
        ann = r['annotation_ids'] or []
        if not ann:
            errs.append(('TRANSCRIPTION_WITHOUT_ANNOTATION', 'cite accepted PAGE_IMAGE overlay annotations of this page'))
        elif ctx['overlay'] is None:
            errs.append(('OVERLAY_MISSING', 'page review cites annotations but no review overlay is active'))
        else:
            if ctx['data'].get('overlay_sha256') != ctx['overlay']['overlay_sha256']:
                errs.append(('STALE_OVERLAY', 'decision file names another overlay SHA-256 than the active one'))
            acc = {a['annotation_id']: a for a in ctx['overlay']['accepted']}
            for aid in ann:
                a = acc.get(aid)
                if a is None:
                    errs.append(('ANNOTATION_NOT_ACCEPTED', aid))
                elif (a['source']['source_id'] != sid or a['page'] != page or a['chapter_id'] != r['chapter_id']
                      or a['anchor_kind'] != 'PAGE_IMAGE'
                      or (a.get('asset_ref') or {}).get('sha256') not in {r['page_render_sha256']} | imgs):
                    errs.append(('ANNOTATION_WRONG_ANCHOR', f'{aid} is not a PAGE_IMAGE reading of this page/render'))
                elif not a['human_verified']:
                    restrictions.append('OVERLAY_NOT_HUMAN_VERIFIED')
    mr = r['model_review'] or {}
    if mr and mr.get('status') not in (None, 'MODEL_REVIEWED'):
        errs.append(('MODEL_REVIEW_OVERCLAIMS', 'model_review.status can only be MODEL_REVIEWED'))
    expected = ctx['hashes']['page_reviews'].get(r['review_id'])
    approved = _approval(r['pilot_scope_approval'], ctx, errs, r.get('_expected_approval_sha', expected), r.get('_set_code', False))
    verified = _verification(r['source_claim_human_verification'], r['page_render_sha256'], ctx, errs, expected)
    if not verified:
        restrictions.append('PAGE_TRANSCRIPTION_UNCERTAIN')
    return errs, {'cause_key': key, 'approved': approved, 'verified': verified, 'restrictions': sorted(set(restrictions))}


def _evaluate_pages(data, ctx, page_inject=None):
    checked, seen, ids = [], {}, set()
    page_inject = page_inject or {}
    for r in data.get('page_reviews') or []:
        if isinstance(r, dict) and r.get('review_id') in page_inject:
            r = {**r, **page_inject[r['review_id']]}
        errs, info = _check_page(r, ctx) if isinstance(r, dict) else ([('INVALID_PAGE_REVIEW', 'not an object')], None)
        if isinstance(r, dict):
            errs += list(r.get('_set_errors', []))
        rid = r.get('review_id') if isinstance(r, dict) else None
        if rid in ids:
            errs.append(('DUPLICATE_REVIEW_ID', rid))
        ids.add(rid)
        checked.append((r, errs, info))
        if info and not errs:
            seen.setdefault((r['chapter_id'], info['cause_key']), []).append(len(checked) - 1)
    for key, idx in seen.items():
        if len(idx) > 1:
            for i in idx:
                checked[i][1].append(('COLLISION', f'{len(idx)} page reviews for {key[1]}'))
    accepted, rejected = [], []
    for r, errs, info in checked:
        if errs:
            rejected.append({'review_id': r.get('review_id') if isinstance(r, dict) else None,
                             'errors': [{'code': c, 'detail': t} for c, t in errs]})
            continue
        effect = ('NONE_UNCONFIRMED_PROPOSAL' if not info['approved'] else
                  'CLEARS_PAGE_FOR_EXPERIMENTAL_PILOT' if r['decision_type'] in PAGE_UNLOCKING else 'NONE_STAYS_REVIEW')
        accepted.append({'review_id': r['review_id'], 'chapter_id': r['chapter_id'], 'cause_key': info['cause_key'],
                         'page': r['page'], 'decision_type': r['decision_type'], 'annotation_ids': r['annotation_ids'],
                         'reason': r['reason'], 'uncertainty_statement': r['uncertainty_statement'],
                         'restrictions': info['restrictions'],
                         'scope_approved_for_experimental_pilot': info['approved'],
                         'approver_id': r['pilot_scope_approval'].get('approver_id') if info['approved'] else None,
                         'source_claim_human_verified': info['verified'], 'academic_release': 'NOT_TESTED',
                         'approved_via_scope_set': r.get('_set_id'), 'effect': effect})
    return {'accepted': accepted, 'rejected': rejected}


def _expand_bundles(data, hashes):
    """bundle_approvals: one human signature for several decisions of identical provenance (same source and same
    decision_type). Every decision keeps its own claim/reason/anchors and is checked on its own."""
    decisions = [dict(d) for d in data['decisions']]
    for d in decisions:
        d['_content_sha'] = d['_expected_approval_sha'] = hashes['decisions'].get(d.get('decision_id'))
    by_id = {d.get('decision_id'): d for d in decisions}
    errs = {}
    for b in data.get('bundle_approvals') or []:
        ids = b.get('decision_ids') or []
        ds = [by_id.get(i) for i in ids]
        problem = None
        if not ids or any(d is None for d in ds):
            problem = ('BUNDLE_UNKNOWN_DECISION', f"{b.get('bundle_id')}: {[i for i in ids if i not in by_id]}")
        elif len({(d['source_ref'], d['decision_type']) for d in ds}) != 1:
            problem = ('BUNDLE_MIXED_PROVENANCE', f"{b.get('bundle_id')}: one source and one decision_type per bundle")
        elif any(d.get('pilot_scope_approval') is not None for d in ds):
            problem = ('DOUBLE_APPROVAL', f"{b.get('bundle_id')}: decision also carries its own approval")
        for i in ids:
            if i in by_id:
                if problem:
                    errs.setdefault(i, []).append(problem)
                elif b.get('pilot_scope_approval') is not None:
                    by_id[i]['pilot_scope_approval'] = b['pilot_scope_approval']; by_id[i]['_bundle_id'] = b.get('bundle_id')
                    by_id[i]['_expected_approval_sha'] = hashes['bundles'].get(b.get('bundle_id'))
    return decisions, errs


SET_CHANGED = 'SCOPE_SET_CONTENT_CHANGED'


def _expand_scope_set(data, hashes, decisions, errs):
    """B6.4 pilot_scope_set_approval: ONE human pilot-scope signature for an explicit list of decisions and page
    reviews. The hash covers the exact member list and every member's own content hash, so any change to any member
    invalidates the whole set. Members are still checked one by one; a member may not also carry its own or a bundle
    approval. It never touches source_claim_human_verification (separate, per entry) or academic release."""
    s = data.get('pilot_scope_set_approval')
    if s is None:
        return {}
    by_id = {d.get('decision_id'): d for d in decisions}
    pages = {r.get('review_id'): r for r in data.get('page_reviews') or [] if isinstance(r, dict)}
    dids = (s.get('decision_ids') or []) if isinstance(s, dict) else []
    pids = (s.get('page_review_ids') or []) if isinstance(s, dict) else []
    in_bundle = {i for b in data.get('bundle_approvals') or [] if isinstance(b, dict) for i in b.get('decision_ids') or []}
    problem = None
    if not isinstance(s, dict) or set(s) - {'set_id', 'decision_ids', 'page_review_ids', 'statement', 'pilot_scope_approval'}:
        problem = ('INVALID_SCOPE_SET', 'pilot_scope_set_approval may only contain set_id, decision_ids, page_review_ids, statement, pilot_scope_approval')
    elif not s.get('set_id') or not (dids or pids) or len(set(dids)) != len(dids) or len(set(pids)) != len(pids):
        problem = ('INVALID_SCOPE_SET', 'set_id and a non-empty, duplicate-free explicit member list are required')
    elif any(i not in by_id for i in dids) or any(i not in pages for i in pids):
        problem = ('SCOPE_SET_UNKNOWN_MEMBER', f"{[i for i in dids if i not in by_id] + [i for i in pids if i not in pages]}")
    elif any(by_id[i].get('pilot_scope_approval') is not None or i in in_bundle for i in dids) or \
            any(pages[i].get('pilot_scope_approval') is not None for i in pids):
        problem = ('DOUBLE_APPROVAL', 'a scope-set member also carries its own or a bundle approval')
    inject = {}
    for i in dids:
        if i in by_id:
            if problem:
                errs.setdefault(i, []).append(problem)
            elif s.get('pilot_scope_approval') is not None:
                by_id[i].update(pilot_scope_approval=s['pilot_scope_approval'], _bundle_id=s['set_id'],
                                _expected_approval_sha=hashes.get('scope_set'), _set_code=SET_CHANGED)
    for i in pids:
        if problem:
            inject[i] = {'_set_errors': [problem]}
        elif s.get('pilot_scope_approval') is not None:
            inject[i] = {'pilot_scope_approval': s['pilot_scope_approval'], '_set_id': s['set_id'],
                         '_expected_approval_sha': hashes.get('scope_set'), '_set_code': SET_CHANGED}
    return inject


def evaluate(decisions, manifest, plan, gates, overlay_eval=None):
    data, sha = decisions
    msrc = {s['relative_path']: s for s in manifest['sources']}
    srcmap = {}
    for s in data['sources']:
        m = msrc.get(s.get('relative_path'))
        if m:
            srcmap[s['source_ref']] = {'relative_path': s['relative_path'], 'sha256': s.get('sha256'), 'source_id': m['source_id'],
                                       'manifest_sha256': m.get('raw_sha256'), 'stale': m.get('raw_sha256') != s.get('sha256')}
    by = {e['element_id']: e for e in manifest['elements']}
    by_page = {}
    for e in manifest['elements']:
        p = (e.get('locator') or {}).get('page')
        if p is not None:
            by_page.setdefault((e['source_id'], p), []).append(e)
    reviewers = {}
    for r in data['reviewers']:
        if r.get('reviewer_id') in reviewers:
            raise ContractError(f"review decisions: reviewer {r.get('reviewer_id')} listed twice")
        if r.get('type') not in REVIEWER_TYPES:
            raise ContractError(f"review decisions: reviewer type must be HUMAN or MODEL, got {r.get('type')!r}")
        reviewers[r['reviewer_id']] = r
    ctx = {'gates': gates, 'chapters': {c['chapter_id']: c for c in plan['chapters']},
           'kcs': {k['kc_id']: k for k in plan['competencies']}, 'srcmap': srcmap, 'by': by, 'by_page': by_page,
           'causes': {cid: gate_causes(g) for cid, g in gates.items()}, 'reviewers': reviewers, 'overlay': overlay_eval, 'data': data,
           'course_id': plan.get('course_id')}
    ctx['hashes'] = content_hashes(data, plan)
    decisions, bundle_errs = _expand_bundles(data, ctx['hashes'])
    page_inject = _expand_scope_set(data, ctx['hashes'], decisions, bundle_errs)
    checked, seen = [], {}
    for d in decisions:
        errs, info = _check(d, ctx)
        errs += bundle_errs.get(d.get('decision_id'), [])
        if d.get('decision_id') in {x['decision']['decision_id'] for x in checked if 'decision_id' in x['decision']}:
            errs.append(('DUPLICATE_DECISION_ID', d.get('decision_id')))
        checked.append({'decision': d, 'errors': errs, 'info': info})
        if info and not errs:
            seen.setdefault((d['chapter_id'], d['kc_id'], info['cause_key']), []).append(len(checked) - 1)
    for key, idx in seen.items():
        if len(idx) > 1:
            for i in idx:
                checked[i]['errors'].append(('COLLISION', f'{len(idx)} decisions for {key[1]} / {key[2]}'))
    accepted, rejected = [], []
    for x in checked:
        d, info = x['decision'], x['info']
        if x['errors']:
            rejected.append({'decision_id': d.get('decision_id'), 'kc_id': d.get('kc_id'),
                             'errors': [{'code': c, 'detail': t} for c, t in x['errors']]})
            continue
        effect = ('NONE_UNCONFIRMED_PROPOSAL' if not info['approved'] else
                  'UNLOCKS_CAUSE_FOR_PILOT' if d['decision_type'] in UNLOCKING else
                  'PILOT_SCOPE_EXCLUDED' if d['decision_type'] == 'PILOT_SCOPE_EXCLUDED_WITH_REASON' else 'NONE_STAYS_REVIEW')
        accepted.append({'decision_id': d['decision_id'], 'chapter_id': d['chapter_id'], 'kc_id': d['kc_id'],
                         'cause_key': info['cause_key'], 'decision_type': d['decision_type'], 'claim': d['claim'],
                         'reason': d['reason'], 'restrictions': info['restrictions'],
                         'annotation_ids': d.get('annotation_ids', []),
                         'coverage_consequences': d.get('coverage_consequences', []),
                         'pilot_scope_approved_by_user': info['approved'],
                         'scope_approved_for_experimental_pilot': info['approved'],
                         'approver_id': (d['pilot_scope_approval'] or {}).get('approver_id') if info['approved'] else None,
                         'approved_via_bundle': d.get('_bundle_id'),
                         'source_claim_human_verified': info['verified'], 'effect': effect})
    pages = _evaluate_pages(data, ctx, page_inject)
    return {'schema': 'em-review-decisions-eval-v1', 'decision_set_id': data['decision_set_id'], 'version': data['version'],
            'decisions_sha256': sha, 'overlay_sha256': overlay_eval['overlay_sha256'] if overlay_eval else None,
            'accepted': accepted, 'rejected': rejected,
            'counts': {'accepted': len(accepted), 'rejected': len(rejected),
                       'effective_unlocks': sum(a['effect'] == 'UNLOCKS_CAUSE_FOR_PILOT' for a in accepted),
                       'unconfirmed': sum(a['effect'] == 'NONE_UNCONFIRMED_PROPOSAL' for a in accepted),
                       'source_claim_human_verified': sum(a['source_claim_human_verified'] for a in accepted),
                       'page_reviews_accepted': len(pages['accepted']), 'page_reviews_rejected': len(pages['rejected']),
                       'page_reviews_effective': sum(p['effect'] == 'CLEARS_PAGE_FOR_EXPERIMENTAL_PILOT' for p in pages['accepted'])},
            'page_reviews': pages, 'content_hashes': ctx['hashes'], 'academic_release': 'NOT_TESTED'}


def apply(gates, evaluation):
    """New gates: a REVIEW_REQUIRED KC becomes producible for the pilot only if every review cause is covered by an
    effective unlocking decision. Everything else is unchanged. The input gates are not modified."""
    out = {}
    for cid, g in gates.items():
        g = json.loads(json.dumps(g))
        causes = gate_causes(g)
        acc = [a for a in evaluation['accepted'] if a['chapter_id'] == cid]
        unlocked, still, excluded = {}, {}, {}
        for kid in list(g.get('review_required_kcs', {})):
            eff = {a['cause_key']: a for a in acc if a['kc_id'] == kid and a['effect'] == 'UNLOCKS_CAUSE_FOR_PILOT'}
            need = causes.get(kid, {})
            missing = sorted(set(need) - set(eff))
            if need and not missing and kid not in g['blocked_kcs']:
                unlocked[kid] = {'decision_ids': sorted(eff[k]['decision_id'] for k in need),
                                 'review_codes': g['review_required_kcs'].pop(kid),
                                 'restrictions': sorted({r for k in need for r in eff[k]['restrictions']}),
                                 'claims': [eff[k]['claim'] for k in sorted(need)],
                                 'source_claim_human_verified': all(eff[k]['source_claim_human_verified'] for k in need)}
                g['producible_kc_ids'].append(kid)
            else:
                still[kid] = missing or ['NO_STRUCTURED_CAUSE']
        for a in acc:
            if a['effect'] == 'PILOT_SCOPE_EXCLUDED':
                excluded[a['kc_id']] = {'decision_id': a['decision_id'], 'reason': a['reason'],
                                        'coverage_consequences': a['coverage_consequences'],
                                        'still_in_inventory': True, 'gate_status_unchanged': True}
        cleared, page_open = {}, []
        eff_pages = {p['cause_key']: p for p in (evaluation.get('page_reviews') or {}).get('accepted', [])
                     if p['chapter_id'] == cid and p['effect'] == 'CLEARS_PAGE_FOR_EXPERIMENTAL_PILOT'}
        for key, f in page_causes(g).items():
            p = eff_pages.get(key)
            if p is None:
                page_open.append(key); continue
            info = {k: p[k] for k in ('review_id', 'page', 'decision_type', 'annotation_ids', 'uncertainty_statement',
                                      'restrictions', 'scope_approved_for_experimental_pilot', 'source_claim_human_verified',
                                      'academic_release')}
            cleared[key] = info
            f.setdefault('pilot_scope_page_reviews', []).append(info)   # the finding itself stays; the reading stays uncertain
        c = [k for k in g['producible_kc_ids']]
        blocked, review = g['blocked_kcs'], g.get('review_required_kcs', {})
        g['status'] = (('BLOCKED' if blocked and not review else 'REVIEW_REQUIRED') if not c else
                       'PARTIAL' if blocked or review else 'READY_WITH_OPEN_ISSUES' if g['findings'] else 'READY')
        g['review_decision_effects'] = {'decisions_sha256': evaluation['decisions_sha256'], 'policy': POLICY,
                                        'pilot_scope_unlocked_kcs': unlocked, 'still_review_required': still,
                                        'pilot_scope_excluded_kcs': excluded,
                                        'chapter_page_reviews': {'cleared_for_experimental_pilot': cleared,
                                                                 'open': sorted(page_open)},
                                        'note': 'pilot scope only; not source verification, not academic release'}
        out[cid] = g
    return out
