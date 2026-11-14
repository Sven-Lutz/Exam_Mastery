"""P1/P2 data contracts (em-source-v1, em-curriculum-v1) and referential validation.

Plain dicts keep the contracts JSON-native; this module only checks them.
Validation is structural and referential. It never certifies semantic correctness.
"""
from __future__ import annotations
from .common import ContractError

SOURCE_SCHEMA = 'em-source-v1'
CURRICULUM_SCHEMA = 'em-curriculum-v1'

SOURCE_STATUS = {'extracted', 'partial', 'empty', 'unsupported', 'failed', 'too_large',
                 'symlink_skipped', 'ignored_metadata', 'ignored_temporary'}
ELEMENT_STATUS = {'ok', 'partial', 'uncertain', 'unavailable', 'failed'}
ELEMENT_KINDS = {'heading', 'paragraph', 'list_item', 'table', 'figure', 'image', 'formula', 'chart',
                 'diagram', 'code', 'code_output', 'notes', 'link', 'rendered_page', 'definition_block'}
AUTHORITY = {'OFFICIAL_LECTURE', 'OFFICIAL_EXAM', 'OFFICIAL_EXERCISE', 'OFFICIAL_SOLUTION',
             'SUPPLEMENTARY', 'STUDENT_NOTES', 'DATA', 'CODE', 'UNKNOWN'}
GAP_CODES = {'UNSUPPORTED_FORMAT', 'TABLE_LAYOUT_MODEL_UNSTABLE', 'PARSE_FAILED', 'EMPTY_SOURCE', 'EMPTY_PAGE', 'TEXT_LAYER_MISSING',
             'VISUAL_UNCERTAIN', 'FORMULA_LINEARIZED', 'SLIDE_RENDER_UNAVAILABLE', 'PAGE_UNKNOWN',
             'MISSING_LINKED_ASSET', 'SOURCE_UNAVAILABLE', 'NOT_FETCHED_OFFLINE_POLICY', 'INVALID_URL',
             'TOO_LARGE', 'SYMLINK_SKIPPED', 'SCAN_ERROR', 'TRUNCATED_TABLE', 'ACTIVE_CONTENT_NOT_RENDERED',
             'CODE_NOT_EXECUTED', 'UNTRUSTED_INSTRUCTION_LIKE_TEXT'}
# Gaps that make course coverage incomplete (informational codes do not).
BLOCKING_GAPS = {'UNSUPPORTED_FORMAT', 'PARSE_FAILED', 'EMPTY_SOURCE', 'TEXT_LAYER_MISSING', 'SOURCE_UNAVAILABLE',
                 'NOT_FETCHED_OFFLINE_POLICY', 'INVALID_URL', 'TOO_LARGE', 'SCAN_ERROR', 'MISSING_LINKED_ASSET',
                 'SLIDE_RENDER_UNAVAILABLE', 'VISUAL_UNCERTAIN', 'TRUNCATED_TABLE'}

OPERATIONS = ('RECALL', 'DEFINE', 'EXPLAIN', 'INTERPRET', 'COMPARE', 'CALCULATE', 'APPLY', 'SUBSUME',
              'IMPLEMENT', 'DERIVE', 'PROVE', 'EVALUATE')
COVERAGE_STATUS = {'EVIDENCED_PENDING_SEMANTIC_REVIEW', 'OPERATION_MISMATCH', 'NO_ASSESSMENT_EVIDENCE',
                   'SOURCE_UNSUPPORTED', 'BLOCKED_SOURCE_GAP'}
SOURCE_SUPPORT = {'UNVERIFIED', 'SOURCE_EXISTS', 'SOURCE_SUPPORT_LEXICAL'}  # *_CONFIRMED is reserved for review


def _need(obj, keys, where):
    missing = [k for k in keys if k not in obj]
    if missing:
        raise ContractError(f'{where}: missing fields {missing}')


def validate_source_manifest(m):
    _need(m, ('schema', 'sources', 'elements', 'online_references', 'gaps', 'coverage_complete'), 'manifest')
    if m['schema'] != SOURCE_SCHEMA:
        raise ContractError('manifest: wrong schema')
    sids = set()
    for s in m['sources']:
        _need(s, ('source_id', 'relative_path', 'origin', 'format', 'status', 'authority', 'element_ids',
                  'uncertainties', 'visual_status'), 'source')
        if s['source_id'] in sids:
            raise ContractError('duplicate source_id ' + s['source_id'])
        if s['status'] not in SOURCE_STATUS:
            raise ContractError('bad source status ' + s['status'])
        if s['authority'] not in AUTHORITY:
            raise ContractError('bad authority ' + s['authority'])
        sids.add(s['source_id'])
    eids = set()
    for e in m['elements']:
        _need(e, ('element_id', 'source_id', 'locator', 'locator_str', 'kind', 'status', 'parse_method',
                  'raw_span_hash', 'extraction_hash', 'confidence'), 'element')
        if e['element_id'] in eids:
            raise ContractError('duplicate element_id ' + e['element_id'])
        if e['source_id'] not in sids:
            raise ContractError('element references unknown source ' + e['source_id'])
        if e['kind'] not in ELEMENT_KINDS or e['status'] not in ELEMENT_STATUS:
            raise ContractError(f"bad element kind/status {e['kind']}/{e['status']}")
        eids.add(e['element_id'])
    for s in m['sources']:
        if not set(s['element_ids']) <= eids:
            raise ContractError('source lists unknown element ids')
    for g in m['gaps']:
        if g['code'] not in GAP_CODES:
            raise ContractError('unknown gap code ' + g['code'])
    blocking = any(g['code'] in BLOCKING_GAPS for g in m['gaps'])
    if m['coverage_complete'] and blocking:
        raise ContractError('coverage_complete contradicts blocking gaps')
    return True


def validate_curriculum(plan, manifest):
    _need(plan, ('schema', 'course_id', 'competencies', 'chapters', 'assessment_items', 'coverage',
                 'notation_registry', 'prerequisite_edges', 'domain_profile'), 'curriculum')
    if plan['schema'] != CURRICULUM_SCHEMA:
        raise ContractError('curriculum: wrong schema')
    eids = {e['element_id'] for e in manifest['elements']}
    kcs = {}
    for k in plan['competencies']:
        _need(k, ('kc_id', 'statement', 'operations', 'operation_basis', 'source_anchor_ids', 'official',
                  'inferred', 'chapter_id', 'prerequisite_kc_ids', 'source_support', 'origin'), 'competency')
        if k['kc_id'] in kcs:
            raise ContractError('duplicate kc_id ' + k['kc_id'])
        if not k['operations'] or any(o not in OPERATIONS for o in k['operations']):
            raise ContractError('competency without valid operation: ' + k['kc_id'])
        if not set(k['source_anchor_ids']) <= eids:
            raise ContractError('competency anchors unknown element: ' + k['kc_id'])
        if k['source_support'] not in SOURCE_SUPPORT:
            raise ContractError('bad source_support ' + k['source_support'])
        kcs[k['kc_id']] = k
    items = {q['item_id']: q for q in plan['assessment_items']}
    for q in items.values():
        if not set(q['anchor_element_ids']) <= eids:
            raise ContractError('assessment item anchors unknown element')
    chapters = {c['chapter_id']: c for c in plan['chapters']}
    for c in chapters.values():
        _need(c, ('chapter_id', 'title', 'kc_ids', 'requirements', 'source_package', 'exam_relevance',
                  'narrative_dependencies', 'generation_plan'), 'chapter')
        if not set(c['kc_ids']) <= set(kcs):
            raise ContractError('chapter references unknown kc')
        if not set(c['narrative_dependencies']) <= set(chapters):
            raise ContractError('chapter depends on unknown chapter')
        r = c['requirements']
        _need(r, ('explanation_depth', 'proof_and_derivation_depth', 'worked_examples', 'visualizations',
                  'exercise_progression', 'model_solutions', 'review_requirements'), 'chapter.requirements')
    for k in kcs.values():
        if k['chapter_id'] not in chapters:
            raise ContractError('competency assigned to unknown chapter ' + k['kc_id'])
        if not set(k['prerequisite_kc_ids']) <= set(kcs):
            raise ContractError('unknown prerequisite')
    for row in plan['coverage']:
        if row['status'] not in COVERAGE_STATUS:
            raise ContractError('bad coverage status ' + row['status'])
        if row['kc_id'] not in kcs or not set(row['evidence_item_ids']) <= set(items):
            raise ContractError('coverage row references unknown ids')
    return True
