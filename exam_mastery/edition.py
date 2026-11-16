"""B20: editorial editions — a curated, versioned layer over a produced chapter, applied at publish time without any
model call.

An edition lives OUTSIDE the lecture folder, next to the errata: <course output>/editions/<chapter_id>.json
(schema em-edition-v1). It never changes content_ast.json; it changes the book model (em-book-v1) that the typesetter,
the learning environment and the Anki builder consume. This is how a reviewed improvement (scientific supplements,
new worked examples, a blueprint-based exam, revised cards) is published reproducibly and re-applied after every
re-publish, instead of regenerating the chapter.

Fail-closed rules:
- every operation must address an existing block id / item id / card key (no silent no-ops);
- a block with provenance 'supplement' must cite at least one id of a verified subject-source register
  (exam_mastery/knowledge/subject/*.json); a source whose `use` forbids numbers must not be the only basis of a block
  that states effect sizes (checked by the author, recorded in the report);
- a 'didactic' block (self-designed example) must carry `checks`: the ids of numeric reference checks that passed
  (the edition's own check script writes them into `numeric_checks`);
- course content (prov 'course') cannot be added by an edition: an edition may only supplement, restructure and
  correct, never invent lecture content.
"""
import copy
import json
from pathlib import Path

from .common import ContractError

SCHEMA = 'em-edition-v1'
KB = Path(__file__).parent / 'knowledge'


def edition_path(chapter_dir):
    ch = Path(chapter_dir)
    return ch.parent.parent.parent / 'editions' / f'{ch.name}.json'


def load(chapter_dir):
    p = edition_path(chapter_dir)
    if not p.exists():
        return None
    e = json.loads(p.read_text(encoding='utf-8'))
    if e.get('schema') != SCHEMA:
        raise ContractError(f'EDITION_SCHEMA: {p} is not {SCHEMA}')
    if e.get('chapter_id') != Path(chapter_dir).name:
        raise ContractError(f'EDITION_CHAPTER_MISMATCH: {e.get("chapter_id")} != {Path(chapter_dir).name}')
    return e


def subject_sources():
    out = {}
    for f in sorted((KB / 'subject').glob('*.json')):
        for s in json.loads(f.read_text(encoding='utf-8'))['sources']:
            out[s['id']] = s
    ver = json.loads((KB / 'verification.json').read_text(encoding='utf-8'))['sources']
    return {k: dict(v, verdict=ver.get(k, {}).get('verdict', 'UNVERIFIED')) for k, v in out.items()}


def _check_block(b, src, checks, where, course_blocks=()):
    if b.get('prov') == 'course' and b.get('type') == 'figure' and b.get('derived_from_block') in course_blocks:
        return                      # a visualisation of lecture data already in the chapter, named by its block id
    if b.get('prov') == 'course' and b.get('restructures') and set(b['restructures']) <= set(course_blocks):
        return                      # B32: re-written presentation of lecture content already in the chapter; anchors are copied by the engine
    if b.get('prov') == 'course':
        raise ContractError(f'EDITION_COURSE_CONTENT: {where} — an edition cannot add lecture content')
    if b.get('prov') == 'supplement':
        ids = b.get('sources') or []
        if not ids:
            raise ContractError(f'EDITION_SUPPLEMENT_UNSOURCED: {where}')
        for i in ids:
            if i not in src:
                raise ContractError(f'EDITION_UNKNOWN_SOURCE: {where} cites {i}')
            if src[i]['verdict'] not in ('VERIFIED', 'PRIMARY_TEXT_READ'):
                raise ContractError(f'EDITION_SOURCE_UNVERIFIED: {where} cites {i} ({src[i]["verdict"]})')
        b.setdefault('refs', [_short(src[i]) for i in ids])
    if b.get('prov') == 'didactic' and b.get('type') in ('example', 'table') and b.get('numeric'):
        missing = [c for c in b.get('checks') or [] if checks.get(c) != 'PASS']
        if not b.get('checks') or missing:
            raise ContractError(f'EDITION_NUMBERS_UNCHECKED: {where} {missing or "no checks declared"}')


def _short(s):
    a = s['cite'].split('(')[0].strip().rstrip(',')
    authors = [x.strip() for x in a.replace('&', ',').split(',') if x.strip() and '.' not in x.strip()[:2]]
    lead = authors[0] if authors else a[:30]
    return f'{lead}{" et al." if len(authors) > 2 else (" & " + authors[1]) if len(authors) == 2 else ""} ({s.get("year", "o. J.")})' \
        if s.get('year') else s['cite'][:60]


def apply(book, ed):
    """Returns (new book, report). Raises ContractError on any unresolvable or unsourced operation."""
    if not ed:
        return book, None
    b = copy.deepcopy(book)
    src = subject_sources(); checks = ed.get('numeric_checks', {})
    log = []
    blocks = {}
    for si, sec in enumerate(b['sections']):
        for bi, x in enumerate(sec['blocks']):
            if x.get('block_id'):
                blocks[x['block_id']] = (si, bi)

    def locate(bid):
        for si, sec in enumerate(b['sections']):
            for bi, x in enumerate(sec['blocks']):
                if x.get('block_id') == bid:
                    return sec['blocks'], bi
        raise ContractError(f'EDITION_UNKNOWN_BLOCK: {bid}')

    def sec_by_title(t):
        for sec in b['sections']:
            if sec['title'] == t:
                return sec
        raise ContractError(f'EDITION_UNKNOWN_SECTION: {t}')

    course_blocks = {x['block_id'] for sec in b['sections'] for x in sec['blocks'] if x.get('block_id') and x.get('prov') in ('course', 'vision', 'interpretation')}
    course_src = {x['block_id']: x.get('src') for sec in b['sections'] for x in sec['blocks'] if x.get('block_id') in course_blocks}
    b['figures'].update(ed.get('figures', {}))
    # B32: lab requests of the edition (engine-built, deterministic); same lab_id = override of the author's request data
    b['lab_requests'] = list(ed.get('labs', []))
    for n, op in enumerate(ed.get('ops', [])):
        kind = op['op']; where = f'op {n} ({kind})'
        for x in op.get('blocks', []) + ([op['block']] if op.get('block') else []):
            _check_block(x, src, checks, f'{where} {x.get("block_id", "")}', course_blocks)
            if x.get('type') == 'figure' and x['id'] not in b['figures']:
                raise ContractError(f'EDITION_UNKNOWN_FIGURE: {where} {x["id"]}')
            if x.get('type') in ('example', 'figtext') and x.get('figure') and x['figure'] not in b['figures']:
                raise ContractError(f'EDITION_UNKNOWN_FIGURE: {where} {x["figure"]}')
            if x.get('prov') == 'course' and x.get('restructures'):
                if x.get('src'):
                    raise ContractError(f'EDITION_COURSE_ANCHOR_AUTHORED: {where} — anchors of restructured lecture content come from the chapter')
                x['src'] = '; '.join(dict.fromkeys(a for r in x['restructures'] for a in str(course_src.get(r) or '').split('; ') if a))
        if kind in ('insert_after', 'insert_before'):
            lst, i = locate(op['block_id'])
            lst[i + 1 if kind == 'insert_after' else i:i + 1 if kind == 'insert_after' else i] = op['blocks']
        elif kind == 'replace':
            lst, i = locate(op['block_id'])
            if not op.get('reason'):
                raise ContractError(f'EDITION_REASON_MISSING: {where}')
            lst[i] = dict(op['block'], block_id=op['block'].get('block_id', op['block_id']), kc_ids=op['block'].get('kc_ids', lst[i].get('kc_ids', [])))
        elif kind == 'remove':
            lst, i = locate(op['block_id'])
            if not op.get('reason'):
                raise ContractError(f'EDITION_REASON_MISSING: {where}')
            del lst[i]
        elif kind == 'append_to_section':
            sec_by_title(op['section'])['blocks'].extend(op['blocks'])
        elif kind == 'add_section':
            new = {'title': op['title'], 'blocks': op['blocks']}
            idx = len(b['sections']) if not op.get('after') else b['sections'].index(sec_by_title(op['after'])) + 1
            b['sections'].insert(idx, new)
        elif kind == 'rename_section':
            sec_by_title(op['from'])['title'] = op['to']
        elif kind == 'stages':
            # the edition defines the workbook: kept v8 items by id (optionally patched) plus new items
            old = {i['id']: i for st in b['stages'] for i in st['items']}
            stages = []
            for st in op['stages']:
                items = []
                for it in st['items']:
                    if isinstance(it, str) or it.get('keep'):
                        iid = it if isinstance(it, str) else it['keep']
                        if iid not in old:
                            raise ContractError(f'EDITION_UNKNOWN_ITEM: {where} {iid}')
                        items.append(_merge(old[iid], {} if isinstance(it, str) else {k: v for k, v in it.items() if k != 'keep'}))
                    else:
                        _check_item(it, where)
                        items.append(it)
                stages.append({'title': st['title'], 'level': st.get('level', len(stages) + 1), 'intro': st.get('intro', ''), 'items': items})
            dropped = sorted(set(old) - {i['id'] for st in stages for i in st['items']})
            if dropped and not op.get('dropped_reason'):
                raise ContractError(f'EDITION_ITEMS_DROPPED_WITHOUT_REASON: {dropped}')
            b['stages'] = stages
            log.append({'op': kind, 'items': sum(len(s['items']) for s in stages), 'dropped': dropped, 'reason': op.get('dropped_reason')})
            continue
        elif kind == 'exam':
            pool = {i['id']: i for st in b['stages'] for i in st['items']}
            items = []
            for k, it in enumerate(op['items'], 1):
                if isinstance(it, str):
                    if it not in pool:
                        raise ContractError(f'EDITION_UNKNOWN_ITEM: {where} {it}')
                    it = pool[it]
                else:
                    _check_item(it, where)
                items.append(dict(it, no=str(k), topic=it.get('title') or it['prompt'][:60]))
            tot = sum(i['points'] for i in items)
            ex = {k: v for k, v in op.items() if k not in ('op', 'items')}
            ex.update(items=items, total_points=tot)
            ex.setdefault('header', [['Punkte', f'{tot:g}'], ['Bearbeitungszeit', f'{op["minutes"]:g} Minuten' if op.get('minutes') else 'keine Vorgabe'],
                                     ['Hilfsmittel', op.get('aids', 'keine')]])
            b['exam'] = ex
        elif kind == 'cards':
            cards = {c['key']: c for c in b['cards']}
            for key in op.get('remove', []):
                if key not in cards:
                    raise ContractError(f'EDITION_UNKNOWN_CARD: {key}')
                del cards[key]
            for c in op.get('replace', []):
                if c['key'] not in cards:
                    raise ContractError(f'EDITION_UNKNOWN_CARD: {c["key"]}')
                cards[c['key']] = c          # same key -> same note id -> review history is kept
            for c in op.get('add', []):
                if c['key'] in cards:
                    raise ContractError(f'EDITION_DUPLICATE_CARD: {c["key"]}')
                cards[c['key']] = c
            b['cards'] = list(cards.values())
        elif kind == 'patch':
            # B33: exact text correction inside one block / workbook item / figure spec. Fail-closed: the old text must
            # occur exactly once in the target (so a correction can never silently miss or hit twice), reason required.
            if not op.get('reason'):
                raise ContractError(f'EDITION_REASON_MISSING: {where}')
            if op.get('block_id'):
                lst, i = locate(op['block_id']); obj = lst[i]
            elif op.get('item_id'):
                hits = [(st['items'], j) for st in b['stages'] for j, it in enumerate(st['items']) if it['id'] == op['item_id']]
                if b.get('exam'):
                    hits += [(b['exam']['items'], j) for j, it in enumerate(b['exam']['items']) if it['id'] == op['item_id']]
                if not hits:
                    raise ContractError(f'EDITION_UNKNOWN_ITEM: {where} {op["item_id"]}')
                lst, i = hits[0]; obj = lst[i]
            elif op.get('figure_id'):
                if op['figure_id'] not in b['figures']:
                    raise ContractError(f'EDITION_UNKNOWN_FIGURE: {where} {op["figure_id"]}')
                obj = b['figures'][op['figure_id']]
            else:
                raise ContractError(f'EDITION_PATCH_TARGET: {where}')
            targets = hits if op.get('item_id') else [(None, None)]
            for lst_, i_ in targets:                 # an item may also sit in the exam copy: patch every occurrence
                cur = obj if lst_ is None else lst_[i_]
                j = json.dumps(cur, ensure_ascii=False)
                for old_, new_ in op['replace']:
                    o_, n_ = json.dumps(old_, ensure_ascii=False)[1:-1], json.dumps(new_, ensure_ascii=False)[1:-1]
                    if j.count(o_) != 1:
                        raise ContractError(f'EDITION_PATCH_NOT_UNIQUE: {where} {o_[:60]!r} occurs {j.count(o_)}x')
                    j = j.replace(o_, n_)
                if op.get('figure_id'):
                    b['figures'][op['figure_id']] = json.loads(j)
                elif lst_ is None:
                    lst[i] = json.loads(j)
                else:
                    lst_[i_] = json.loads(j)
            log.append({'op': kind, 'target': op.get('block_id') or op.get('item_id') or op.get('figure_id'), 'reason': op['reason'],
                        'review_finding': op.get('finding')})
            continue
        elif kind == 'meta':
            for k in ('objectives', 'opener_lead', 'glossary', 'references', 'production_notes', 'workbook_intro', 'workbook_intro_solutions'):
                if k in op:
                    b[k] = op[k]
            b['meta'].update(op.get('meta', {}))
            if op.get('kc_labels'):
                unknown = set(op['kc_labels']) - set(b.get('kc_labels') or {})
                if unknown:
                    raise ContractError(f'EDITION_UNKNOWN_KC: {sorted(unknown)}')
                b['kc_labels'].update(op['kc_labels'])
        else:
            raise ContractError(f'EDITION_UNKNOWN_OP: {kind}')
        log.append({'op': kind, 'target': op.get('block_id') or op.get('section') or op.get('title') or '', 'reason': op.get('reason', '')})
    rep = {'schema': 'em-edition-report-v1', 'edition': ed.get('edition'), 'date': ed.get('date'), 'operations': log,
           'numeric_checks': checks, 'subject_sources_cited': sorted({s for op in ed.get('ops', []) for x in op.get('blocks', []) + ([op['block']] if op.get('block') else []) for s in x.get('sources', [])}),
           'human_reviewed': bool(ed.get('human_reviewed', False))}
    return b, rep


def _merge(old, patch):
    out = copy.deepcopy(old)
    for k, v in patch.items():
        if k == 'solution':
            out['solution'] = dict(out.get('solution') or {}, **v)
        else:
            out[k] = v
    return out


def _check_item(it, where):
    for k in ('id', 'prompt', 'operation', 'solution'):
        if not it.get(k):
            raise ContractError(f'EDITION_ITEM_INCOMPLETE: {where} {it.get("id")} lacks {k}')
    s = it['solution']
    if not s.get('answer'):
        raise ContractError(f'EDITION_ITEM_NO_ANSWER: {it["id"]}')
    if it.get('points') is not None:
        tot = sum(r[1] for r in s.get('rubric') or [])
        if abs(tot - it['points']) > 1e-9:
            raise ContractError(f'EDITION_RUBRIC_SUM: {it["id"]} rubric {tot:g} != {it["points"]:g}')
    it.setdefault('no', it['id']); it.setdefault('space', 40); it.setdefault('evidence_gap', False)
