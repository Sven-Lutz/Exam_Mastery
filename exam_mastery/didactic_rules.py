"""Deterministic checks of the didactic rule set DR-1.0 (see skill references/didactic_rules.md).

They catch the defect classes found in the v0.10 products: production meta language in learner text, mixed
languages, one schematic block form for everything, essay prompts as flash cards, mock exams with gap items or
incomplete solutions, rubrics that do not add up, items that depend on an unseen slide. They cannot judge subject
correctness or teaching quality as a whole; the quality dossier says so.
"""
import re
from collections import Counter

VERSION = 'DR-1.0'

META = re.compile(r'\b(permitted text|allowed (?:material|text)|the lecture (?:states|says|text)|lecture text|slide text layer|'
                  r'read in the Claude|Claude Code session|the model|the engine|LLM|prompt|source element|'
                  r'laut Folie(?!\s*\d)|im Vorlesungstext|zulässigen Material|bereitgestellten Material|Textschicht|Modellentwurf im Text)\b', re.I)
EN = re.compile(r'\b(the|and|of|is|are|which|with|this|that|for|from|by|be|not|should)\b', re.I)
DE = re.compile(r'\b(der|die|das|und|ist|sind|nicht|mit|von|für|ein|eine|wird|werden|auch|bei|zu)\b', re.I)


def meta_language(text):
    return [m.group(0) for m in META.finditer(re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]', ' ', str(text or '')))]


def language_mix(text, lang='de'):
    """Share of foreign function words; a few English technical terms in German text are fine."""
    t = re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]|„[^“]*“|"[^"]*"|\([^)]*\)', ' ', str(text or ''))
    en, de = len(EN.findall(t)), len(DE.findall(t))
    total = en + de
    return (en / total if lang == 'de' else de / total) if total >= 12 else 0.0


def _texts(block):
    for k in ('md', 'term', 'title', 'given', 'result', 'wrong', 'right', 'why', 'caption'):
        if block.get(k):
            yield block[k]
    for s in block.get('steps') or []:
        yield ' '.join(str(x) for x in s)
    for r in block.get('rows') or []:
        yield ' '.join(str(x) for x in (r['cells'] if isinstance(r, dict) else r))


def check_book(book):
    """Returns [{'rule','status','object','detail'}]. FAIL on blocking rules, WARN on advisory ones."""
    out = []
    add = lambda rule, status, obj, detail: out.append({'rule': rule, 'status': status, 'object': obj, 'detail': detail})
    lang = book['meta'].get('lang', 'de')
    blocks = [(s['title'], b) for s in book['sections'] for sub in (s.get('subsections') or [{'blocks': s.get('blocks', [])}]) for b in sub['blocks']]
    # T1 orientation and integrating summary
    kinds = [b['type'] for _, b in blocks]
    add('T1', 'PASS' if kinds and kinds[0] == 'lead' and 'summary' in kinds[-3:] else 'FAIL', 'chapter',
        'opens with orientation and ends with an integrating summary' if kinds and kinds[0] == 'lead' else 'missing orientation or final summary')
    # T3 form variety
    c = Counter(kinds); top, n = c.most_common(1)[0] if c else ('', 0)
    share = n / max(1, len(kinds))
    add('T3', 'PASS' if share <= 0.55 and len(c) >= 5 else 'WARN', 'chapter',
        f'{len(c)} block forms; most frequent {top} = {share:.0%} of {len(kinds)} blocks')
    # T6 meta language / T7 language
    for sec, b in blocks:
        for t in _texts(b):
            hits = meta_language(t)
            if hits:
                add('T6', 'FAIL', sec, f'meta language {hits[:3]} in "{str(t)[:60]}…"')
            mix = language_mix(t, lang)
            if mix > 0.35:
                add('T7', 'FAIL', sec, f'{mix:.0%} foreign function words in "{str(t)[:60]}…"')
    if not any(r['rule'] == 'T6' for r in out):
        add('T6', 'PASS', 'chapter', 'no production meta language in learner text')
    if not any(r['rule'] == 'T7' for r in out):
        add('T7', 'PASS', 'chapter', f'single product language ({lang})')
    # T4 worked example then faded/independent practice for quantitative chapters
    if book.get('quantitative'):
        ex = sum(1 for _, b in blocks if b['type'] == 'example')
        faded = sum(1 for st in book.get('stages', []) for it in st['items'] if it.get('faded'))
        add('T4', 'PASS' if ex >= 1 and faded >= 1 else 'FAIL', 'chapter', f'{ex} worked examples, {faded} faded items')
    # T8 figures carry a source and are used
    for fid, spec in book.get('figures', {}).items():
        used = any(b.get('id') == fid or b.get('figure') == fid for _, b in blocks) or any(it.get('figure') == fid for st in book.get('stages', []) for it in st['items'])
        add('T8', 'PASS' if spec.get('source') and used else 'FAIL', fid, 'source and use' if spec.get('source') and used else 'figure without source or unused')
    # A1 alignment: every competency practised with its operation
    # B12: an item practises a competency if it declares the operation OR its wording demands one that satisfies it
    # (same rule as the engine's item-operation gate): "Berechnen Sie ... und erklären Sie ..." practises EXPLAIN too.
    from .curriculum import operations_in, satisfied, CASE_PATTERN
    ops = set()
    for st in book.get('stages', []):
        for it in st['items']:
            acts = operations_in(it.get('prompt', ''))
            q = {'format': 'open', 'has_concrete_instance': bool(CASE_PATTERN.search(it.get('prompt', ''))), 'norm_refs': []}
            for k in it.get('kc_keys', []):
                ops.add((k, it.get('operation')))
                for kc_op in {c['operation'] for c in book.get('competencies', []) if c['key'] == k}:
                    if satisfied(kc_op, acts, q)[0]:
                        ops.add((k, kc_op))
    for kc in book.get('competencies', []):
        ok = (kc['key'], kc['operation']) in ops
        add('A1', 'PASS' if ok else 'FAIL', kc['key'], f'practised with operation {kc["operation"]}' if ok else f'no item with operation {kc["operation"]}')
    # A2 progression
    order = [st.get('level') for st in book.get('stages', [])]
    add('A2', 'PASS' if order == sorted(order) and len(order) >= 4 else 'FAIL', 'workbook', f'stage levels {order}')
    # A3/A4 items
    for st in book.get('stages', []):
        for it in st['items']:
            if re.search(r'\b(auf der Folie|siehe Folie|in der Abbildung der Vorlesung)\b', it['prompt']) and not (it.get('figure') or it.get('table')):
                add('A3', 'FAIL', it['id'], 'refers to a slide or figure the learner does not see')
            s = it.get('solution') or {}
            if not s.get('answer') or not (s.get('steps') or s.get('approach')):
                add('A4', 'FAIL', it['id'], 'solution without answer or reasoning')
            if s.get('rubric') and it.get('points') is not None and abs(sum(r[1] for r in s['rubric']) - it['points']) > 1e-9:
                add('A4', 'FAIL', it['id'], 'rubric points do not sum to item points')
            if not s.get('errors'):
                add('A4', 'WARN', it['id'], 'no typical error named')
    if not any(r['rule'] in ('A3', 'A4') and r['status'] == 'FAIL' for r in out):
        add('A4', 'PASS', 'workbook', 'every item has answer, reasoning and consistent rubric')
    # A5 exam
    if book.get('exam'):
        from .typeset import exam_check
        p = exam_check(book)
        add('A5', 'FAIL' if p else 'PASS', 'exam', '; '.join(p) if p else 'exam items complete, points consistent, labelled self-designed')
    # C1-C5 cards
    from .anki_v2 import card_lint
    bad = {c.get('key'): card_lint(c) for c in book.get('cards', [])}
    bad = {k: v for k, v in bad.items() if v}
    add('C1-C5', 'FAIL' if bad else 'PASS', 'cards', str(bad)[:400] if bad else f'{len(book.get("cards", []))} cards pass the card rules')
    return out


def blocking(results):
    return [r for r in results if r['status'] == 'FAIL']
