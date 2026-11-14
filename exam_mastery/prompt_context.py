"""Lossless compact encoding of a chapter context for model prompts.

The full context (chapter_context.json) stays the reference for validators. The prompt carries the same
information without repetition: elements grouped by source (file name, authority and locator prefix once),
default fields omitted, identical requirement texts grouped, allowed_source_refs left out when it equals the
element ids. expand(compact(ctx)) == ctx is a tested invariant, so no source, restriction or review finding is lost.
"""
from __future__ import annotations
import json

SCHEMA = 'em-prompt-context-compact-v1'
LEGEND = ('COMPACT CONTEXT (lossless). source_elements: per source_id -> file, authority, rows '
          '[element_id, kind, locator_suffix, text, extra]; full locator = source_id + "/" + locator_suffix; extra holds '
          'non-default fields (status other than "ok", flags). allowed_source_refs: if "ALL_SOURCE_ELEMENTS", every '
          'element_id listed in source_elements is allowed and nothing else. Grouped requirement lists: every listed '
          'kc_id / item carries the group\'s fields.')
_ELEMENT_KEYS = {'authority', 'element_id', 'flags', 'kind', 'locator', 'source', 'status', 'text'}


def _group(items, keys, member):
    """Group dicts that share all `keys`; members keep only `member` fields (in order). Returns None if lossy."""
    groups, order = {}, []
    for it in items:
        if not isinstance(it, dict) or set(it) != set(keys) | set(member):
            return None
        g = json.dumps([it[k] for k in keys], ensure_ascii=False, sort_keys=True)
        if g not in groups:
            groups[g] = {**{k: it[k] for k in keys}, 'members': []}; order.append(g)
        groups[g]['members'].append([it[m] for m in member] if len(member) > 1 else it[member[0]])
    return {'group_keys': list(keys), 'member_fields': list(member), 'groups': [groups[g] for g in order]}


def _ungroup(enc):
    out = []
    for g in enc['groups']:
        for m in g['members']:
            vals = m if len(enc['member_fields']) > 1 else [m]
            out.append({**{k: g[k] for k in enc['group_keys']}, **dict(zip(enc['member_fields'], vals))})
    return out


def _compact_elements(elements):
    by_src, order = {}, []
    for e in elements:
        if set(e) - _ELEMENT_KEYS or not {'element_id', 'kind', 'locator', 'source', 'authority'} <= set(e):
            return None
        sid, sep, suffix = e['locator'].partition('/')
        if not sep:
            return None
        key = (sid, e['source'], e['authority'])
        if key not in by_src:
            by_src[key] = []; order.append(key)
        extra = {k: e[k] for k in ('status', 'flags') if k in e and not (k == 'status' and e[k] == 'ok') and not (k == 'flags' and e[k] == [])}
        # keep presence information: a missing status/flags field is not the same as a default value
        extra['_has'] = [k for k in ('status', 'flags', 'text') if k in e]
        # row extra is {} in the common case
        by_src[key].append([e['element_id'], e['kind'], suffix, e.get('text'), extra])
    blocks = [{'source_id': s, 'file': f, 'authority': a, 'rows': by_src[(s, f, a)]} for s, f, a in order]
    ids = [e['element_id'] for e in elements]
    if ids != sorted(ids):   # keep the original order explicitly when it is not the element_id order
        pos = {i: n for n, i in enumerate(ids)}
        for b in blocks:
            for r in b['rows']: r[4]['_pos'] = pos[r[0]]
    # presence of optional fields: stored once when uniform, per row otherwise
    has = {json.dumps(r[4].get('_has')) for b in blocks for r in b['rows']}
    if len(has) == 1:
        uniform = json.loads(has.pop())
        for b in blocks:
            for r in b['rows']: r[4].pop('_has', None)
        return {'fields_present': uniform, 'order': 'element_id' if ids == sorted(ids) else 'position', 'blocks': blocks}
    return {'fields_present': None, 'order': 'element_id' if ids == sorted(ids) else 'position', 'blocks': blocks}


def _expand_elements(enc):
    out = []
    for b in enc['blocks']:
        for eid, kind, suffix, text, extra in b['rows']:
            has = enc['fields_present'] if enc['fields_present'] is not None else extra.get('_has', [])
            e = {'authority': b['authority'], 'element_id': eid, 'kind': kind, 'locator': b['source_id'] + '/' + suffix, 'source': b['file']}
            if 'flags' in has: e['flags'] = extra.get('flags', [])
            if 'status' in has: e['status'] = extra.get('status', 'ok')
            if 'text' in has: e['text'] = text
            out.append((extra.get('_pos', eid), e))
    return [e for _, e in sorted(out, key=lambda x: x[0])]


def compact(ctx):
    """Return the compact prompt form. Falls back to the unchanged field for anything it cannot encode losslessly."""
    c = {'compact_schema': SCHEMA, 'legend': LEGEND, 'encoded': []}
    rest = dict(ctx)
    els = ctx.get('source_elements')
    enc = _compact_elements(els) if isinstance(els, list) else None
    if enc is not None and _expand_elements(enc) == els:
        c['source_elements'] = enc; c['encoded'].append('source_elements'); rest.pop('source_elements')
        refs = ctx.get('allowed_source_refs')
        if isinstance(refs, list) and refs == [e['element_id'] for e in els]:
            c['allowed_source_refs'] = 'ALL_SOURCE_ELEMENTS'; c['encoded'].append('allowed_source_refs'); rest.pop('allowed_source_refs')
    req = ctx.get('requirements')
    if isinstance(req, dict):
        r2 = dict(req); done = []
        for field, keys, member in (('visualizations', ('kind', 'requirement', 'source_status'), ('source_element_id', 'asset')),
                                    ('worked_examples', ('min_count', 'operation', 'requirement'), ('kc_id',)),
                                    ('exercise_progression', ('stages',), ('kc_id',))):
            v = req.get(field)
            if isinstance(v, list) and v:
                g = _group(v, keys, member)
                if g is not None and _ungroup(g) == v:
                    r2[field] = g; done.append(field)
        if done:
            r2['_grouped'] = done; c['requirements'] = r2; c['encoded'].append('requirements'); rest.pop('requirements')
    c['rest'] = rest
    return c


def expand(c):
    if c.get('compact_schema') != SCHEMA:
        raise ValueError('not a compact prompt context')
    ctx = dict(c['rest'])
    if 'source_elements' in c['encoded']:
        ctx['source_elements'] = _expand_elements(c['source_elements'])
    if 'allowed_source_refs' in c['encoded']:
        ctx['allowed_source_refs'] = [e['element_id'] for e in ctx['source_elements']]
    if 'requirements' in c['encoded']:
        r = dict(c['requirements'])
        for f in r.pop('_grouped'):
            r[f] = _ungroup(r[f])
        ctx['requirements'] = r
    return ctx


def dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
