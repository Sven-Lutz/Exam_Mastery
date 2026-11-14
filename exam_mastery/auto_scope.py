"""Product mode: automatic text-only scope for competencies that only await a visual/neighbour-page review.

A competency is REVIEW_REQUIRED when a visual of unknown relevance sits on its anchor page
(VISUAL_RELEVANCE_UNKNOWN) or a textless page lies next to it (ADJACENT_PAGE_UNREADABLE). Earlier, product mode
dropped these competencies. Here they are produced from the readable text of their own anchor pages only:

- the visual and the textless neighbour page are never interpreted, described or cited;
- numbers come only from the anchor text (the existing SOURCE_NUMBERS gate enforces this);
- the competency keeps a visible scope label; nothing is marked as human-verified.

A competency stays excluded (VISUAL_REVIEW_REQUIRED) when its anchor pages carry too little text to teach from, or
when its content lives in a figure/scan. The only blocking cause handled here is a figure judged dominant by rule V2
next to substantial slide text (B7): it is taught from the text with a visible label that figure values were not used.
Scanned anchor pages, source gaps and other blockers are never touched.
"""
import json
import re

TEXT_KINDS = {'heading', 'paragraph', 'table', 'notes', 'formula', 'visual_transcription'}
AUTO_CAUSES = {'VISUAL_RELEVANCE_UNKNOWN', 'ADJACENT_PAGE_UNREADABLE'}
QUANT_OPS = {'CALCULATE', 'DERIVE', 'PROVE'}
# Conservative floor for "the slide text itself teaches something": a title alone is never enough.
MIN_TEXT_ELEMENTS = 3
MIN_WORDS = 30
# B8: figure confirmed decorative by the agent reading: title + one complete statement or list is enough
MIN_TEXT_ELEMENTS_DECORATIVE = 2
MIN_WORDS_DECORATIVE = 12

# Category per competency (shown in reports and the quality dossier)
SOURCE_DIRECT = 'SOURCE_DIRECT'                     # producible from the sources without restriction
TEXT_ONLY = 'AUTO_TEXT_ONLY'                         # producible from anchor text; visual not used
TEXT_ONLY_LABELLED = 'AUTO_TEXT_ONLY_UNCERTAINTY_LABEL'  # as above, quantitative: values in the visual may be missing
SUPPLEMENT_REQUIRED = 'SUPPLEMENT_REQUIRED'          # needs a verified external/missing source
VISUAL_REVIEW = 'VISUAL_REVIEW_REQUIRED'             # content (also) lives in a figure/scan the engine cannot read
NO_OBJECTIVE = 'NO_LEARNING_OBJECTIVE'               # heading artefact: chapter title slide, citation, reading list
HUMAN_DECISION = 'HUMAN_DECISION_REQUIRED'           # any other cause without an automatic resolution
VISION = 'AUTO_VISION_TRANSCRIBED'                    # B8: figure read by the calling agent, validated, labelled
VISUAL_CODES = {'ESSENTIAL_VISUAL_UNRESOLVED', 'SCANNED_PAGE_NO_OCR', 'VISUAL_RELEVANCE_UNKNOWN', 'ADJACENT_PAGE_UNREADABLE'}
# a formula that exists only as linearised text (sub/superscripts, overlines lost) can be resolved like a figure: the
# calling agent reads the rendered page, the validated reading becomes a labelled transcription, never human-verified
FORMULA_CODES = {'CRITICAL_FORMULA_UNRELIABLE'}
# B7: a figure judged dominant (rule V2) next to substantial slide text is taught from the text, always labelled
V2_RULE = 'V2_VISUAL_DOMINANT'
HEADING_ORIGINS = {'heading_topic', 'slide_title_topic'}
CITATION = re.compile(r'(^|\|)\s*(source:|further read|literature|literatur|references)|,\s*(19|20)\d\d\s*$', re.I)

RESTRICTIONS = ['USE_ONLY_TEXT_ELEMENTS_LISTED', 'DO_NOT_DESCRIBE_OR_INTERPRET_EXCLUDED_VISUALS',
                'DO_NOT_USE_NEIGHBOUR_TEXTLESS_PAGES', 'NUMBERS_ONLY_FROM_LISTED_TEXT']


def _norm(t):
    return re.sub(r'\W+', ' ', t).strip().lower()


def _unit(e):
    loc = e.get('locator') or {}
    for k in ('slide', 'page'):
        if k in loc:
            return (e['source_id'], k, loc[k])
    return None


def _text_on_anchor_units(kc, by, units):
    els, seen = [], set()
    for a in kc['source_anchor_ids']:
        if a not in by:
            continue
        for e in units.get(_unit(by[a]), [by[a]]):
            if e['element_id'] in seen or e['kind'] not in TEXT_KINDS or e.get('status') != 'ok' or not (e.get('text') or '').strip():
                continue
            if e['kind'] == 'formula' and (e.get('fidelity') or {}).get('representation') == 'linearized_text_layer':
                continue
            seen.add(e['element_id']); els.append(e)
    return els


_INDEX = {}  # single entry: the manifest object currently being classified -> derived lookups (pure, read-only)


def _index(manifest):
    """Element lookups derived from one manifest, built once per manifest object instead of once per chapter/KC.
    Keyed by object identity and holding a reference to it, so a different (or new) manifest never hits."""
    hit = _INDEX.get('m')
    if hit is not None and hit[0] is manifest and hit[1] == len(manifest['elements']):
        return hit[2]
    from .examples import groups
    by = {e['element_id']: e for e in manifest['elements']}
    units = {}
    for e in manifest['elements']:
        u = _unit(e)
        if u:
            units.setdefault(u, []).append(e)
    els = [{'element_id': e['element_id'], 'locator': e.get('locator_str') or '', 'source': e['source_id'],
            'text': e.get('text') or '', 'status': e.get('status'), 'kind': e['kind']}
           for e in manifest['elements'] if e['kind'] in TEXT_KINDS]
    grp, pages = groups(els)
    idx = {'by': by, 'units': units, 'ctx': els, 'ctx_index': ({e['element_id']: e for e in els}, grp, pages)}
    _INDEX['m'] = (manifest, len(manifest['elements']), idx)
    return idx


def _with_continuation(kc, text, manifest):
    """B7.1: add the text of the other slides of the same multi-slide example (live run: the 'after' slide alone
    led the author to recombine totals). Only text elements; figures stay excluded."""
    from .examples import continuation_elements
    idx = _index(manifest)
    have = {e['element_id'] for e in text}
    return text + [e for e in continuation_elements(kc['source_anchor_ids'], idx['ctx'], index=idx['ctx_index'])
                   if e['element_id'] not in have]


def _formula_pages(kid, gate, by):
    """(source_id, page) of every formula element that blocks this competency as CRITICAL_FORMULA_UNRELIABLE."""
    out = set()
    for f in gate.get('findings') or []:
        if f.get('code') in FORMULA_CODES and f.get('kc_ids') == [kid]:
            for eid in f.get('element_ids') or []:
                if eid in by:
                    loc = by[eid].get('locator') or {}
                    out.add((by[eid]['source_id'], loc.get('page', loc.get('slide'))))
    return out


def _vision(kc, by, units, manifest, codes, gate=None):
    """B8: every anchor page of a figure-blocked competency was read by the agent (visual_evidence). At least one page
    carries accepted content and none stayed unreadable: produce from page text plus the labelled transcription.
    Only figure causes are resolved this way; source gaps or other blockers are never touched."""
    av = manifest.get('agent_vision')
    if not av or not codes or not set(codes) <= VISUAL_CODES | FORMULA_CODES:
        return None
    pages = {(by[a]['source_id'], (by[a].get('locator') or {}).get('page', (by[a].get('locator') or {}).get('slide')))
             for a in kc['source_anchor_ids'] if a in by and by[a]['kind'] != 'visual_transcription'}
    formula = bool(set(codes) & FORMULA_CODES)
    if formula:
        fpages = _formula_pages(kc['kc_id'], gate or {}, by)
        if not fpages:
            return None
        pages |= fpages
    keys = {f'{s}:{p}' for s, p in pages if p is not None}
    content, deco = set(av['content']), set(av['decorative'])
    if not keys or not keys <= content | deco:
        return None
    text = _text_on_anchor_units(kc, by, units)
    if formula and not {f'{s}:{p}' for s, p in _formula_pages(kc['kc_id'], gate or {}, by)} <= content:
        return None                # every page with a blocking formula must have been read with content
    if formula:                # the transcription of the formula pages joins the context
        text = text + [e for (s, p) in sorted(pages, key=str) for e in units.get((s, 'page', p), []) + units.get((s, 'slide', p), [])
                       if e['kind'] == 'visual_transcription' and e.get('status') == 'ok' and e not in text]
    if not keys & content:     # all figures decorative: the slide text alone must carry the competency
        # the reading confirmed that no content hides in the figure, so a complete statement or list suffices
        words = sum(len(e['text'].split()) for e in text)
        if len(text) < MIN_TEXT_ELEMENTS_DECORATIVE or words < MIN_WORDS_DECORATIVE:
            return None
        return {'category': TEXT_ONLY, 'causes': codes, 'text_element_ids': [e['element_id'] for e in text], 'text_words': words,
                'excluded_visual_element_ids': [], 'excluded_pages': [], 'restrictions': RESTRICTIONS,
                'source_claim_human_verified': False, 'reason': 'figure judged decorative by the agent reading'}
    vis = [e['element_id'] for e in text if e['kind'] == 'visual_transcription']
    return {'category': VISION, 'causes': codes, 'text_element_ids': [e['element_id'] for e in text], 'vision_element_ids': vis,
            'text_words': sum(len(e['text'].split()) for e in text), 'excluded_visual_element_ids': [], 'excluded_pages': [],
            'restrictions': (['FORMULAS_ONLY_FROM_VISUAL_TRANSCRIPTION_ELEMENTS_NOT_FROM_THE_LINEARISED_TEXT_LAYER'] if formula else []) +
                            ['USE_ONLY_TEXT_ELEMENTS_LISTED', 'FIGURE_CONTENT_ONLY_FROM_VISUAL_TRANSCRIPTION_ELEMENTS',
                             'NUMBERS_ONLY_FROM_LISTED_TEXT', 'STATE_ONCE_THAT_FIGURE_CONTENT_WAS_READ_BY_THE_AGENT_NOT_VERIFIED_BY_A_HUMAN'],
            'source_claim_human_verified': False}


def classify(plan, manifest, gate):
    """{kc_id: {'category', ...}} for every competency of the chapter behind this gate."""
    idx = _index(manifest)
    by, units = idx['by'], idx['units']
    kcs = {k['kc_id']: k for k in plan['competencies']}
    chap = next(c for c in plan['chapters'] if c['chapter_id'] == gate['chapter_id'])
    out = {}
    exam_linked = {k for k in chap['kc_ids'] if kcs[k].get('linked_item_ids')}
    for kid in chap['kc_ids']:
        topic = kcs[kid]['statement'].split(': ', 1)[-1].strip()
        # a title-slide heading matches every exam question of its chapter lexically, so that link is no evidence
        if kcs[kid].get('origin') in HEADING_ORIGINS and kid not in gate['producible_kc_ids'] and (
                _norm(topic) == _norm(chap.get('title', '')) or (CITATION.search(topic) and kid not in exam_linked)):
            out[kid] = {'category': NO_OBJECTIVE, 'causes': gate['blocked_kcs'].get(kid) or (gate.get('review_required_kcs') or {}).get(kid) or [],
                        'reason': 'heading of a chapter title slide, citation or reading list; no learning objective of its own'}
            continue
        v = _vision(kcs[kid], by, units, manifest, {**(gate.get('review_required_kcs') or {}), **gate['blocked_kcs']}.get(kid), gate)
        if v:
            out[kid] = v; continue
        if kid in gate['blocked_kcs']:
            codes = gate['blocked_kcs'][kid]
            if set(codes) <= {'REQUIRED_SOURCE_UNAVAILABLE', 'SOURCE_GAP'}:
                out[kid] = {'category': SUPPLEMENT_REQUIRED, 'causes': codes}; continue
            rules = {f.get('rule') for f in gate['findings'] if f.get('kc_ids') == [kid] and f['severity'] == 'blocker'}
            if set(codes) == {'ESSENTIAL_VISUAL_UNRESOLVED'} and rules == {V2_RULE}:
                text = _text_on_anchor_units(kcs[kid], by, units)
                words = sum(len(e['text'].split()) for e in text)
                if len(text) >= MIN_TEXT_ELEMENTS and words >= MIN_WORDS:
                    text = _with_continuation(kcs[kid], text, manifest)
                    vis = sorted({e for f in gate['findings'] if f.get('kc_ids') == [kid] for e in f['element_ids']})
                    out[kid] = {'category': TEXT_ONLY_LABELLED, 'causes': codes, 'text_element_ids': [e['element_id'] for e in text],
                                'text_words': words, 'excluded_visual_element_ids': vis, 'excluded_pages': [],
                                'restrictions': RESTRICTIONS + ['STATE_ONCE_THAT_VALUES_IN_THE_FIGURE_WERE_NOT_USED'],
                                'source_claim_human_verified': False, 'figure_dominant': True}
                    continue
            out[kid] = {'category': VISUAL_REVIEW if set(codes) & (VISUAL_CODES | FORMULA_CODES) else HUMAN_DECISION, 'causes': codes}
            continue
        review = (gate.get('review_required_kcs') or {}).get(kid)
        if review is None:
            out[kid] = {'category': (gate.get('auto_scope_kcs') or {}).get(kid, {}).get('category', SOURCE_DIRECT), 'causes': []}
            continue
        if not set(review) <= AUTO_CAUSES:
            out[kid] = {'category': VISUAL_REVIEW if set(review) & VISUAL_CODES else HUMAN_DECISION, 'causes': review, 'reason': 'review cause has no automatic text-only resolution'}
            continue
        text = _text_on_anchor_units(kcs[kid], by, units)
        words = sum(len(e['text'].split()) for e in text)
        excluded_visuals = sorted({e for f in gate['findings'] if f.get('kc_ids') == [kid] and f['code'] == 'VISUAL_RELEVANCE_UNKNOWN'
                                   for e in f['element_ids']})
        excluded_pages = sorted({f"{f['source_id']}:{p}" for f in gate['findings'] if f.get('kc_ids') == [kid]
                                 and f['code'] == 'ADJACENT_PAGE_UNREADABLE' for p in f.get('pages') or []})
        if len(text) < MIN_TEXT_ELEMENTS or words < MIN_WORDS:
            out[kid] = {'category': VISUAL_REVIEW, 'causes': review,
                        'reason': f'anchor pages carry too little readable text ({len(text)} elements, {words} words)'}
            continue
        quant = bool(set(kcs[kid]['operations']) & QUANT_OPS)
        text = _with_continuation(kcs[kid], text, manifest)
        out[kid] = {'category': TEXT_ONLY_LABELLED if quant else TEXT_ONLY, 'causes': review,
                    'text_element_ids': [e['element_id'] for e in text], 'text_words': words,
                    'excluded_visual_element_ids': excluded_visuals, 'excluded_pages': excluded_pages,
                    'restrictions': RESTRICTIONS + (['STATE_ONCE_THAT_VALUES_IN_THE_FIGURE_WERE_NOT_USED'] if quant else []),
                    'source_claim_human_verified': False}
    return out


def apply(plan, manifest, gates):
    """New gates where text-only competencies are producible with an 'auto_scope_kcs' record. Input is not modified."""
    out = {}
    for cid, g in gates.items():
        g = json.loads(json.dumps(g))
        auto = {}
        for kid, info in classify(plan, manifest, g).items():
            if info['category'] in (TEXT_ONLY, TEXT_ONLY_LABELLED, VISION):
                g['review_required_kcs'].pop(kid, None)
                g['blocked_kcs'].pop(kid, None)  # only V2-dominant figures with substantial text reach here
                if kid not in g['producible_kc_ids']:
                    g['producible_kc_ids'].append(kid)
                auto[kid] = info
        if auto:
            g['auto_scope_kcs'] = auto
            # same status rule as fidelity_gate; findings stay, so a fully cleared chapter is READY_WITH_OPEN_ISSUES
            g['status'] = 'PARTIAL' if (g['review_required_kcs'] or g['blocked_kcs']) else 'READY_WITH_OPEN_ISSUES'
        out[cid] = g
    return out


def coverage_report(plan, manifest, gates_before, gates_after=None):
    """Competency-by-competency scope table (before = without auto scope)."""
    gates_after = gates_after or apply(plan, manifest, gates_before)
    kcs = {k['kc_id']: k for k in plan['competencies']}
    rows = []
    for cid, g in gates_before.items():
        cls = classify(plan, manifest, g)
        after = set(gates_after[cid]['producible_kc_ids'])
        for kid, info in cls.items():
            rows.append({'chapter_id': cid, 'kc_id': kid, 'statement': kcs[kid]['statement'],
                         'operations': kcs[kid]['operations'], 'category': info['category'],
                         'produced_before': kid in g['producible_kc_ids'], 'produced_after': kid in after,
                         'causes': info.get('causes', []), 'reason': info.get('reason')})
    return rows
