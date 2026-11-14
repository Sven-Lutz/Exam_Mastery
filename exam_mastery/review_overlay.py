"""P3.6: external review annotations ("evidence overlay") for one chapter. Subject-neutral, offline, deterministic.

A reviewer (human or model) records findings about source pages that the parser cannot express: diagram structure,
textless raster images, calculation checks, inconsistencies, practice-question inventories. This module only
validates and passes them on; it never promotes a review status, never changes a fidelity gate and never turns an
inferred competency into an official objective.

Validation against the current source manifest (fail closed, per annotation):
- the source file's SHA-256 must equal the manifest's raw_sha256 (otherwise STALE_SOURCE_HASH),
- every element_id must exist, belong to that source and sit on the stated page (no invented parser ids),
- a PAGE_IMAGE anchor needs a rendered_page/image element on that page whose asset SHA-256 matches,
- interpretations of elements without a text layer must not contain numbers (no invented quantities),
- HUMAN_VERIFIED needs reviewer_type HUMAN plus a named approval record; anything else stays non-approving,
- checks of kind 'expression' are recomputed here (+ - * / and numbers only) and their result is recorded.
"""
from __future__ import annotations
import ast
import json
import operator
import re
from pathlib import Path
from .common import ContractError, sha_file

SCHEMA = 'em-review-annotations-v1'
FINDING_TYPES = {'TRANSCRIPTION', 'DIAGRAM_STRUCTURE', 'CALCULATION', 'INTERPRETATION', 'UNCERTAINTY'}
REVIEWER_TYPES = {'HUMAN', 'MODEL'}
NON_APPROVING = {'PROPOSED_PENDING_HUMAN_APPROVAL', 'MODEL_REVIEWED', 'REJECTED'}
REVIEW_STATUSES = NON_APPROVING | {'HUMAN_VERIFIED'}
PROVENANCE = {'ORIGINAL_CONTENT', 'DERIVED_EXPLANATION'}
ANCHOR_KINDS = {'TEXT_ELEMENTS', 'PAGE_IMAGE'}
LINK_BASES = {'OFFICIAL_OBJECTIVE', 'OFFICIAL_SUB_OBJECTIVE', 'GUIDING_QUESTION', 'INFERRED_FROM_LECTURE_EXAMPLE',
              'DIDACTIC_OPERATIONALISATION', 'PRACTICE_QUESTION_TOPIC'}
OFFICIAL_BASES = {'OFFICIAL_OBJECTIVE', 'OFFICIAL_SUB_OBJECTIVE'}
IMAGE_KINDS = {'rendered_page', 'image'}
NUMBER = re.compile(r'\d')
POLICY = ('Review annotations are reviewer findings, not source text and not approval. Only review_status '
          'HUMAN_VERIFIED is human-confirmed; PROPOSED_PENDING_HUMAN_APPROVAL and MODEL_REVIEWED are proposals. '
          'A source anchor proves location, not correctness. Links with basis INFERRED_* or DIDACTIC_* are not official '
          'objectives. Practice questions are not an official exam. Interpretations of images without a text layer are '
          'qualitative; do not add quantities, positions or boundaries that the annotation does not state. '
          'CHECK_MISMATCH means the source itself is inconsistent at that point; never present it as consistent.')

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def safe_eval(expr):
    """Numbers, + - * / and parentheses only. Anything else is a contract error."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        raise ContractError(f'expression not allowed: {expr!r}')
    return ev(ast.parse(str(expr), mode='eval'))


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def load(path, source_root=None):
    path = Path(path).expanduser().resolve()
    if source_root is not None:
        root = Path(source_root).expanduser().resolve()
        if path == root or root in path.parents:
            raise ContractError('review overlay must not live inside the source root')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != SCHEMA:
        raise ContractError(f'review overlay schema must be {SCHEMA}')
    for f in ('overlay_id', 'version', 'sources', 'annotations'):
        if f not in data:
            raise ContractError(f'review overlay lacks {f}')
    return data, sha_file(path)


def _check_annotation(a, srcmap, by, plan_chapters, plan_items):
    errs = []
    for f in ('annotation_id', 'chapter_id', 'source_ref', 'page', 'anchor_kind', 'element_ids', 'finding_type',
              'reviewer_type', 'review_status', 'provenance', 'content', 'asset_ref', 'version'):
        if f not in a:
            errs.append(('MISSING_FIELD', f))
    if errs:
        return errs, None
    for f, allowed in (('finding_type', FINDING_TYPES), ('reviewer_type', REVIEWER_TYPES),
                       ('review_status', REVIEW_STATUSES), ('provenance', PROVENANCE), ('anchor_kind', ANCHOR_KINDS)):
        if a[f] not in allowed:
            errs.append(('INVALID_VALUE', f'{f}={a[f]!r}'))
    if a['review_status'] == 'HUMAN_VERIFIED' and not (a['reviewer_type'] == 'HUMAN' and isinstance(a.get('human_approval'), dict)
                                                       and a['human_approval'].get('approver') and a['human_approval'].get('date')):
        errs.append(('UNSUPPORTED_HUMAN_VERIFIED', 'HUMAN_VERIFIED needs reviewer_type HUMAN and human_approval{approver,date}'))
    if a['chapter_id'] not in plan_chapters:
        errs.append(('CHAPTER_NOT_IN_PLAN', a['chapter_id']))
    src = srcmap.get(a['source_ref'])
    if src is None:
        return errs + [('SOURCE_NOT_IN_MANIFEST', a['source_ref'])], None
    if src.get('stale'):
        errs.append(('STALE_SOURCE_HASH', f"{src['relative_path']}: overlay {src['sha256'][:12]} != manifest {src['manifest_sha256'][:12] if src['manifest_sha256'] else None}"))
    page = a['page']
    if page is not None and (not isinstance(page, int) or isinstance(page, bool) or page < 1):
        errs.append(('INVALID_PAGE', repr(page)))  # None only for sources without pages (must match the element locator)
    if not a['element_ids']:
        errs.append(('NO_ANCHOR', 'element_ids empty'))
    for e in a['element_ids']:
        el = by.get(e)
        if el is None:
            errs.append(('UNKNOWN_ELEMENT_ID', e)); continue
        if el['source_id'] != src['source_id']:
            errs.append(('ELEMENT_WRONG_SOURCE', e))
        if (el.get('locator') or {}).get('page') != page:
            errs.append(('ELEMENT_WRONG_PAGE', f"{e} is on page {(el.get('locator') or {}).get('page')}, not {page}"))
    els = [by[e] for e in a['element_ids'] if e in by]
    textless = bool(els) and all(not (el.get('text') or '').strip() for el in els)
    if a['anchor_kind'] == 'PAGE_IMAGE':
        img = [el for el in els if el['kind'] in IMAGE_KINDS and el.get('asset')]
        if not img:
            errs.append(('PAGE_IMAGE_WITHOUT_IMAGE_ELEMENT', 'needs a rendered_page/image element with an asset'))
        elif not any(el['asset']['sha256'] == a['asset_ref'].get('sha256') for el in img):
            errs.append(('ASSET_HASH_MISMATCH', f"asset_ref {str(a['asset_ref'].get('sha256'))[:12]} matches no image element on the page"))
    if textless and a['finding_type'] in ('INTERPRETATION', 'DIAGRAM_STRUCTURE'):
        if any(NUMBER.search(s) for s in _strings(a['content'])):
            errs.append(('NUMERIC_CLAIM_WITHOUT_TEXT_LAYER', 'anchors have no text layer; numbers in an interpretation are not verifiable'))
    for link in a.get('competency_links', []):
        if link.get('basis') not in LINK_BASES:
            errs.append(('INVALID_LINK_BASIS', repr(link.get('basis'))))
        if link.get('official') and link.get('basis') not in OFFICIAL_BASES:
            errs.append(('INFERRED_MARKED_OFFICIAL', link.get('statement', '')[:60]))
    for q in a.get('item_links', []):
        if q.get('item_id') is not None and q['item_id'] not in plan_items:
            errs.append(('UNKNOWN_ITEM_ID', q['item_id']))
    checks = []
    for c in a.get('checks', []):
        if c.get('kind') != 'expression':
            errs.append(('INVALID_CHECK', repr(c.get('kind')))); continue
        try:
            value = safe_eval(c['expr'])
        except (ContractError, SyntaxError, ZeroDivisionError, KeyError) as ex:
            errs.append(('INVALID_CHECK', str(ex))); continue
        tol = float(c.get('tolerance', 0))
        ok = abs(value - float(c['stated'])) <= tol
        checks.append({**c, 'computed': round(value, 6), 'difference': round(value - float(c['stated']), 6),
                       'result': 'CHECK_PASS' if ok else 'CHECK_MISMATCH'})
    return errs, {'checks': checks, 'anchors_textless': textless}


def evaluate(overlay, manifest, plan, overlay_sha256=None):
    """-> {accepted:[...], rejected:[...]}. Accepted annotations carry engine-computed fields; review_status is
    copied unchanged and an 'approval_effect' that is never stronger than the status allows."""
    data, sha = (overlay if isinstance(overlay, tuple) else (overlay, overlay_sha256))
    msrc = {s['relative_path']: s for s in manifest['sources']}
    srcmap = {}
    for s in data['sources']:
        m = msrc.get(s.get('relative_path'))
        srcmap[s['source_ref']] = {'relative_path': s.get('relative_path'), 'sha256': s.get('sha256'),
                                   'source_id': m['source_id'] if m else None,
                                   'manifest_sha256': m.get('raw_sha256') if m else None,
                                   'stale': not m or m.get('raw_sha256') != s.get('sha256')}
        if not m:
            srcmap.pop(s['source_ref'])
    by = {e['element_id']: e for e in manifest['elements']}
    chapters = {c['chapter_id'] for c in plan['chapters']}
    items = {q['item_id'] for q in plan['assessment_items']}
    seen, accepted, rejected = set(), [], []
    for a in data['annotations']:
        errs, extra = _check_annotation(a, srcmap, by, chapters, items)
        if a.get('annotation_id') in seen:
            errs.append(('DUPLICATE_ANNOTATION_ID', a.get('annotation_id')))
        seen.add(a.get('annotation_id'))
        if errs:
            rejected.append({'annotation_id': a.get('annotation_id'), 'errors': [{'code': c, 'detail': d} for c, d in errs]})
            continue
        src = srcmap[a['source_ref']]
        accepted.append({**a, 'source': {'relative_path': src['relative_path'], 'sha256': src['sha256'],
                                         'source_id': src['source_id']},
                         'engine_checks': extra['checks'], 'anchors_textless': extra['anchors_textless'],
                         'human_verified': a['review_status'] == 'HUMAN_VERIFIED',
                         'approval_effect': 'HUMAN_CONFIRMED' if a['review_status'] == 'HUMAN_VERIFIED' else 'NONE_PROPOSAL_ONLY',
                         'competency_links': [{**l, 'official': l.get('basis') in OFFICIAL_BASES}
                                              for l in a.get('competency_links', [])]})
    return {'schema': 'em-review-overlay-eval-v1', 'overlay_id': data['overlay_id'], 'overlay_version': data['version'],
            'overlay_sha256': sha, 'accepted': accepted, 'rejected': rejected,
            'counts': {'accepted': len(accepted), 'rejected': len(rejected)}, 'changes_gates': False}


def context_block(evaluation, chapter_id):
    """The part of an overlay evaluation that belongs into one chapter context. Complete, never truncated."""
    if not evaluation:
        return None
    acc = [a for a in evaluation['accepted'] if a['chapter_id'] == chapter_id]
    return {'schema': 'em-review-evidence-v1', 'overlay_id': evaluation['overlay_id'],
            'overlay_version': evaluation['overlay_version'], 'overlay_sha256': evaluation['overlay_sha256'],
            'policy': POLICY, 'annotation_count': len(acc),
            'human_verified_count': sum(a['human_verified'] for a in acc),
            'rejected_annotation_ids': [r['annotation_id'] for r in evaluation['rejected']],
            'review_anchor_ids': sorted({e for a in acc for e in a['element_ids']}),
            'annotations': acc}
