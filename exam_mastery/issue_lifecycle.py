"""B33: issue lifecycle — every open issue of a chapter gets an explicit, evidenced state instead of a growing list.

States
  OPEN            not decided, or a decision's recheck failed (then `recheck_failed` says why)
  RESOLVED        fixed; a machine recheck against the PUBLISHED products confirms it
  DUPLICATE       same code and same objects as an earlier issue (automatic)
  REASSIGNED      belongs to another chapter/source (exam items, foreign figures); target recorded
  NOT_APPLICABLE  the concern does not apply (decorative visual, announcement, unused source formula); reason required
  ACCEPTED_RISK   known limitation that stays visible in every report; reason required, never counted as fixed

Decisions live outside the lecture folder next to the edition: <course>/editions/<chapter_id>.issues.json
(schema em-issue-decisions-v1): {"decisions": {issue_id: {...}}, "rules": [{...}]}. A rule applies one decision to
all issues matching code (+ optional page/element/object pattern); explicit per-issue decisions win. RESOLVED decisions
must name a recheck; the recheck is executed here on every publish, so a later regression re-opens the issue.

Rechecks (all evaluated on the published book model):
  book_contains {pattern}            regex over all learner text (sections, items, cards)
  figure_in_book {figures: [...]}    every figure id is used by a block or item
  kc_worked_example {kc}             an example block teaches the competency
  item_in_workbook {items: [...]}    the items exist in the published workbook
  gate_rerun {codes: [...]}          the deterministic draft gates, rerun on the final stage output, no longer report
                                     any of these codes (the final authoring product, not the draft)
Gate: OPEN issues with severity 'blocker' -> BLOCKED; otherwise PASS (ACCEPTED_RISK count is reported separately).
"""
import json
import re
from pathlib import Path

SCHEMA = 'em-issue-decisions-v1'
STATES = ('OPEN', 'RESOLVED', 'DUPLICATE', 'REASSIGNED', 'NOT_APPLICABLE', 'ACCEPTED_RISK')
NEEDS_REASON = ('REASSIGNED', 'NOT_APPLICABLE', 'ACCEPTED_RISK')


def decisions_path(chapter_dir):
    ch = Path(chapter_dir)
    return ch.parent.parent.parent / 'editions' / f'{ch.name}.issues.json'


def _text(book):
    parts = []

    def walk(o):
        if isinstance(o, str):
            parts.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                if k not in ('svg', 'figures'):
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk({k: book.get(k) for k in ('sections', 'stages', 'exam', 'cards')})
    return '\n'.join(parts)


def _figures_used(book):
    used = set()
    for s in book.get('sections', []):
        for b in s['blocks']:
            if b.get('type') == 'figure':
                used.add(b.get('id'))
            if b.get('figure'):
                used.add(b['figure'])
    for st in book.get('stages', []):
        for it in st['items']:
            if it.get('figure'):
                used.add(it['figure'])
    return used


def _recheck(rc, book, ctx):
    kind = (rc or {}).get('kind')
    if kind == 'book_contains':
        ok = bool(re.search(rc['pattern'], ctx['text']))
        return ok, f"pattern {rc['pattern']!r} {'found' if ok else 'NOT found'} in the published text"
    if kind == 'figure_in_book':
        miss = [f for f in rc['figures'] if f not in ctx['figures']]
        return not miss, f"figures {rc['figures']} used" if not miss else f'figures missing: {miss}'
    if kind == 'kc_worked_example':
        hit = [b.get('title') for s in book.get('sections', []) for b in s['blocks'] if b.get('type') == 'example' and rc['kc'] in (b.get('kc_ids') or [])]
        return bool(hit), f"worked example(s) for {rc['kc']}: {hit[:3]}" if hit else f"no worked example tagged {rc['kc']}"
    if kind == 'item_in_workbook':
        have = {i['id'] for st in book.get('stages', []) for i in st['items']}
        miss = [i for i in rc['items'] if i not in have]
        return not miss, f"items {rc['items']} present" if not miss else f'items missing: {miss}'
    if kind == 'gate_rerun':
        left = sorted({c for c in rc['codes'] if c in ctx.get('gate_codes', set())})
        if ctx.get('gate_codes') is None:
            return False, 'gate rerun not possible (no final stage output)'
        return not left, 'draft gates rerun on the final authoring output: ' + ('none of ' + str(rc['codes']) + ' reported' if not left else f'still reported: {left}')
    return False, f'unknown or missing recheck {kind!r}'


def _match(rule, iss, elmap):
    if rule.get('code') and iss.get('code') != rule['code']:
        return False
    if rule.get('codes') and iss.get('code') not in rule['codes']:
        return False
    if rule.get('detail_pattern') and not re.search(rule['detail_pattern'], iss.get('detail') or ''):
        return False
    if rule.get('pages') is not None:
        pages = {elmap.get(e) for e in iss.get('element_ids') or []}
        if not pages & {tuple(p) for p in rule['pages']}:
            return False
    if rule.get('object_ids') and iss.get('object_id') not in rule['object_ids']:
        return False
    if rule.get('source_not'):                       # all referenced elements come from other sources than this one
        srcs = {elmap[e][0] for e in iss.get('element_ids') or [] if e in elmap}
        if not srcs or rule['source_not'] in srcs:
            return False
    return True


def evaluate(chapter_dir, book, decisions=None, elements=None, gate_codes=None):
    """Returns the lifecycle report (em-issue-lifecycle-v1). `elements`: {element_id: (source_id, page)}."""
    ch = Path(chapter_dir)
    ast = json.loads((ch / 'content_ast.json').read_text(encoding='utf-8'))
    issues = ast.get('open_issues') or []
    if decisions is None:
        p = decisions_path(ch)
        decisions = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'schema': SCHEMA, 'decisions': {}, 'rules': []}
    if decisions.get('schema') != SCHEMA:
        raise ValueError(f'issue decisions must use schema {SCHEMA}')
    elmap = elements or {}
    ctx = {'text': _text(book), 'figures': _figures_used(book), 'gate_codes': gate_codes}
    seen, rows = {}, []
    for iss in issues:
        key = (iss.get('code'), tuple(sorted(iss.get('element_ids') or [])), iss.get('object_id'), iss.get('detail'))
        row = {k: iss.get(k) for k in ('issue_id', 'code', 'severity', 'origin', 'object_id', 'element_ids', 'detail')}
        row['pages'] = sorted({f'{elmap[e][0]}:{elmap[e][1]}' for e in iss.get('element_ids') or [] if e in elmap})
        if key in seen and (iss.get('element_ids') or iss.get('object_id')):
            row.update(state='DUPLICATE', duplicate_of=seen[key], decided_by='engine (identical code, objects and detail)')
            rows.append(row); continue
        seen[key] = iss['issue_id']
        dec = (decisions.get('decisions') or {}).get(iss['issue_id'])
        if dec is None:
            dec = next((r for r in decisions.get('rules') or [] if _match(r, iss, elmap)), None)
        if not dec:
            row.update(state='OPEN', decided_by=None)
            rows.append(row); continue
        state = dec['state']
        if state not in STATES:
            raise ValueError(f'unknown issue state {state!r} for {iss["issue_id"]}')
        row.update(state=state, reason=dec.get('reason'), evidence=dec.get('evidence'), decided_by=dec.get('decided_by'),
                   target=dec.get('target'), rule=dec.get('rule_id'))
        if state in NEEDS_REASON and not dec.get('reason'):
            row.update(state='OPEN', recheck_failed=f'{state} without a reason')
        if state == 'RESOLVED':
            ok, why = _recheck(dec.get('recheck'), book, ctx)
            row['recheck'] = why
            if not ok:
                row.update(state='OPEN', recheck_failed=why)
        rows.append(row)
    counts = {s: sum(r['state'] == s for r in rows) for s in STATES}
    blockers = [r['issue_id'] for r in rows if r['state'] == 'OPEN' and r.get('severity') == 'blocker']
    return {'schema': 'em-issue-lifecycle-v1', 'chapter_id': ch.name, 'total': len(rows), 'counts': counts,
            'open_blockers': blockers, 'gate': 'BLOCKED' if blockers else 'PASS',
            'accepted_risks': [{'issue_id': r['issue_id'], 'code': r['code'], 'reason': r.get('reason')} for r in rows if r['state'] == 'ACCEPTED_RISK'],
            'issues': rows}


def final_gate_codes(chapter_dir, curriculum):
    """Codes the deterministic draft gates still report on the final authoring output (revision, else author)."""
    from .production import draft_gate_findings
    ch = Path(chapter_dir)
    ast = json.loads((ch / 'content_ast.json').read_text(encoding='utf-8'))
    for f in ('chapter_revision', 'chapter_author'):
        p = ch / 'stage_outputs' / f'{f}.json'
        if p.exists():
            d = json.loads(p.read_text(encoding='utf-8'))
            prod = d.get('output') or d.get('product') or d
            comps = [k for k in (curriculum or {}).get('competencies', []) if k['kc_id'] in set(ast.get('kc_ids') or [])]
            try:
                return {x.get('code') for x in draft_gate_findings(prod, comps)}
            except Exception:                         # noqa: BLE001 - an unreadable output means: no recheck possible
                return None
    return None


def element_pages(source_inventory):
    return {e['element_id']: (e['source_id'], (e.get('locator') or {}).get('page')) for e in (source_inventory or {}).get('elements') or []}
