"""B35 subject-adaptive requirements, derived from competencies (not from course names).

Root cause addressed: in the V4 RL chapter 43 of 44 competencies carried the operation EXPLAIN although ~20 of them
demand "herleiten", "beweisen" or "berechnen". With a flat operation nothing downstream could require a proof, a
counterexample or a worked calculation, so the products defaulted to explanations.

Mechanism (data in profiles.json, packs are combinable):
  operations(objective)  = declared operations  ∪  operations suggested by pack "signals" in the objective text
                           (signals only ADD; a declared operation is never removed; EXPLAIN alone is treated as
                           'unspecified' and reported)
  packs(objective)       = every pack whose operations intersect -> one ML objective can activate formal
                           mathematics + computational reasoning + empirical research at once
  requirements           = union of the packs' "requires" for exactly those operations
  coverage(book)         = per objective: required components present? Workbook items are linked by kc_keys; text
                           blocks are not linked in current books, so their presence is checked chapter-wide and the
                           result is labelled UNLINKED (weaker evidence than a linked block).
No subject names, no per-course branches: a new discipline = new pack data.
"""
from __future__ import annotations
import json, re
from functools import lru_cache
from pathlib import Path

# which book artefacts count as a component (generic vocabulary of the engine's block / item / box kinds)
COMPONENTS = {
    'theorem_statement': {'blocks': {'theorem'}},
    'proof': {'blocks': {'proof'}},
    'derivation': {'blocks': {'derivation', 'proof'}},
    'counterexample': {'blocks': {'counterexample'}, 'box_kinds': {'counterexample', 'limit'}, 'text': r'Gegenbeispiel|counterexample'},
    'worked_example': {'blocks': {'example', 'worked_example'}},
    'practice_task': {'items': {'CALCULATE', 'DERIVE', 'APPLY', 'PROVE', 'SUBSUME', 'IMPLEMENT', 'ANALYZE'}},
    'intuition': {'blocks': {'intuition', 'figtext'}},
    'comparison': {'blocks': {'compare', 'table'}},
    'limits': {'box_kinds': {'limit'}, 'text': r'Grenzen|limitation'},
    'algorithm': {'blocks': {'algorithm'}},
    'complexity_statement': {'text': r'O\(|Laufzeit|Komplexität|complexity'},
    'transfer_task': {'box_kinds': {'transfer'}, 'items': {'TRANSFER'}},
    'justified_answer': {'items': {'EXPLAIN', 'JUSTIFY', 'ARGUE'}},
    'retrieval_card': {'cards': True},
    'lab_task': {'labs': True},
    'case_solution': {'blocks': {'case', 'case_solution'}, 'items': {'SUBSUME', 'CASE', 'DIAGNOSE'}},
    'norm_text': {'blocks': {'norm', 'law'}, 'box_kinds': {'law', 'norm'}},
    'competing_views': {'blocks': {'debate', 'competing_views'}},
    'uncertainty_note': {'box_kinds': {'uncertainty'}},
    'guideline_reference': {'blocks': {'guideline'}},
    'sensitivity': {'blocks': {'sensitivity'}},
}


@lru_cache(maxsize=1)
def packs():
    return json.loads((Path(__file__).parent / 'profiles.json').read_text(encoding='utf-8'))['packs']


def _matches(text):
    """{(pack_id, op)} whose signal occurs in the text."""
    return {(p['id'], op) for p in packs() for op, rx in (p.get('signals') or {}).items() if re.search(rx, text or '', re.I)}


def operations(text, declared=()):
    """(operations, inferred_only) for one objective."""
    found = {op for _, op in _matches(text)}
    dec = {d.lower() for d in declared if d and d.upper() != 'EXPLAIN'}
    if not found and not dec:
        found.add('explain')
    return dec | found, found - dec


def resolve(text, declared=()):
    """Requirements come from (pack, operation) pairs: a signal activates only ITS pack's operation, so a shared
    operation name (e.g. 'interpret' in legal and conceptual packs) never imports another discipline's demands.
    A declared operation is ambiguous by name and activates every pack that lists it."""
    ops, inferred = operations(text, declared)
    pairs = _matches(text) | {(p['id'], op) for p in packs() for op in ops - {o for _, o in _matches(text)}
                              if op in p.get('operations', [])}
    req = {}
    for pid, op in pairs:
        pk = next(p for p in packs() if p['id'] == pid)
        for comp in (pk.get('requires') or {}).get(op, []):
            req.setdefault(comp, set()).add(f'{pid}:{op}')
    active = sorted({pid for pid, _ in pairs})
    return {'operations': sorted(ops), 'inferred': sorted(inferred), 'packs': active,
            'requires': {k: sorted(v) for k, v in sorted(req.items())},
            'validators': sorted({v for p in packs() if p['id'] in active for v in p.get('validators', [])})}


def _inventory(book):
    blocks = [b for s in book.get('sections', []) for b in s.get('blocks', [])]
    text = ' '.join(json.dumps(b, ensure_ascii=False) for b in blocks)
    items = [i for st in book.get('stages', []) for i in (st.get('items') or [])]
    return {'blocks': blocks, 'types': {b.get('type') for b in blocks}, 'box_kinds': {b.get('kind') for b in blocks if b.get('type') == 'box'},
            'text': text, 'items': items, 'cards': bool(book.get('cards')), 'labs': bool(book.get('lab_requests'))}


def _present(comp, inv, kc):
    if '|' in comp:                                  # alternatives: the strongest evidence among them counts
        got = [_present(c, inv, kc) for c in comp.split('|')]
        return 'LINKED' if 'LINKED' in got else 'UNLINKED' if 'UNLINKED' in got else 'MISSING'
    spec = COMPONENTS.get(comp, {})
    if spec.get('items') and any(kc in (i.get('kc_keys') or []) and (i.get('operation') or '').upper() in spec['items'] for i in inv['items']):
        return 'LINKED'
    if any(kc in (b.get('kc_ids') or b.get('kc_keys') or []) and (b.get('type') in spec.get('blocks', set())
           or (b.get('type') == 'box' and b.get('kind') in spec.get('box_kinds', set()))) for b in inv['blocks']):
        return 'LINKED'
    hit = (spec.get('blocks', set()) & inv['types'] or spec.get('box_kinds', set()) & inv['box_kinds']
           or (spec.get('text') and re.search(spec['text'], inv['text'], re.I))
           or (spec.get('cards') and inv['cards']) or (spec.get('labs') and inv['labs']))
    return 'UNLINKED' if hit else 'MISSING'


def coverage(book):
    """Per-objective requirement coverage report for a published book.json."""
    inv, rows = _inventory(book), []
    declared = {c['key']: c.get('operation') for c in book.get('competencies', [])}
    for kc, label in (book.get('kc_labels') or {}).items():
        r = resolve(label, [declared.get(kc)])
        st = {comp: _present(comp, inv, kc) for comp in r['requires']}
        rows.append(dict(r, kc=kc, objective=label, declared=declared.get(kc), components=st,
                         missing=sorted(c for c, v in st.items() if v == 'MISSING')))
    flat = sum(1 for r in rows if (r['declared'] or 'EXPLAIN').upper() == 'EXPLAIN' and set(r['operations']) - {'explain'})
    return {'objectives': rows, 'n': len(rows),
            'operation_flattened': flat,
            'missing_total': sum(len(r['missing']) for r in rows),
            'linked_share': round(sum(v == 'LINKED' for r in rows for v in r['components'].values()) /
                                  max(1, sum(len(r['components']) for r in rows)), 2),
            'scope': 'presence of required component kinds; NOT their quality. UNLINKED = present somewhere in the chapter, not tied to the objective'}
