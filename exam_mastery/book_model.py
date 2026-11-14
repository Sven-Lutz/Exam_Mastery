"""ContentAST (em-content-v1, model-produced) -> book model (em-book-v1) for `typeset` and `anki_v2` (B9).

Lets every chapter the pipeline produces use the new typesetting, the exam integrity rules and the Anki v2 deck,
whatever the subject. Mapping rules:
- block kinds become the matching book forms: definition, worked example, misconception, limitation box, summary, …;
- provenance becomes a visible label (Vorlesung / Ergänzung / Beispiel / Einordnung);
- assessments become workbook stages by difficulty; exam items (with points, solution and rubric, no evidence gap)
  become the mock exam;
- cards: authored cards (`ast['cards']`, rule set C1–C5) are used as they are. Without authored cards, only
  definition and misconception cards are derived; their keys come from the term, never from an item number.
  Every card that fails the card rules is dropped and reported, never published.
"""
import re

from .anki_v2 import card_lint, slug

PROV = {'COURSE_SOURCE': 'course', 'VERIFIED_SUPPLEMENT': 'supplement', 'AUTHOR_INFERENCE': 'interpretation',
        'DIDACTIC_EXAMPLE': 'didactic', 'UNCONFIRMED': 'unconfirmed'}
STAGES = [('recall', 1, 'Grundverständnis'), ('guided', 2, 'Geführte Anwendung'), ('standard', 3, 'Selbstständige Anwendung'),
          ('transfer', 4, 'Transfer'), ('exam', 5, 'Klausurtraining')]
EXAMPLE_KINDS = {'WORKED_EXAMPLE', 'CALCULATION', 'DERIVATION', 'PROOF', 'SUBSUMPTION', 'ALGORITHM'}
BOX = {'LIMITATION': 'limit', 'REMARK': 'remark', 'ASSUMPTIONS': 'note', 'THEOREM': 'key', 'COUNTEREXAMPLE': 'pitfall',
       'NORM_STRUCTURE': 'law', 'COMPLEXITY': 'note'}


def _t(v):
    return '' if v is None else str(v)


def _src(b, anchor_label):
    return anchor_label(b.get('source_refs') or [])


def block(b, anchor_label, vision_ids=()):
    k = b.get('kind'); prov = PROV.get(b.get('provenance'), 'interpretation')
    if set(b.get('source_refs') or []) & set(vision_ids):
        prov = 'vision'
    src = _src(b, anchor_label)
    title, body = _t(b.get('title')), _t(b.get('body'))
    if k == 'DEFINITION':
        return {'type': 'definition', 'term': title or 'Definition', 'md': body or _t(b.get('result')), 'prov': prov, 'src': src}
    if k in EXAMPLE_KINDS and (b.get('steps') or b.get('problem')):
        steps = [[_t(s.get('statement')), _t(s.get('justification'))] for s in b.get('steps') or [] if isinstance(s, dict)]
        res = ' '.join(x for x in (_t(b.get('result')), _t(b.get('interpretation'))) if x)
        return {'type': 'example', 'label': {'PROOF': 'Beweis', 'DERIVATION': 'Herleitung', 'SUBSUMPTION': 'Prüfung am Fall', 'ALGORITHM': 'Algorithmus'}.get(k, 'Durchgerechnetes Beispiel'),
                'title': title or 'Beispiel', 'given': _t(b.get('problem')) or body, 'steps': steps or [[body, '']], 'result': res, 'prov': prov, 'src': src}
    if k == 'MISCONCEPTION':
        return {'type': 'misconception', 'wrong': title or body, 'right': _t(b.get('result')) or body, 'why': _t(b.get('interpretation'))}
    if k == 'SUMMARY':
        return {'type': 'summary', 'md': body}
    if k in BOX:
        return {'type': 'box', 'kind': BOX[k], 'title': title or None, 'md': body or _t(b.get('result')), 'prov': prov, 'src': src}
    text = (f'**{title}.** ' if title else '') + body
    extra = ' '.join(x for x in (_t(b.get('result')), _t(b.get('interpretation'))) if x and x not in body)
    return {'type': 'text', 'md': text + (('\n\n' + extra) if extra else ''), 'prov': prov, 'src': src}


def _solution(a, s):
    rub = [[_t(r.get('criterion')), float(r.get('points') or 0)] for r in s.get('rubric') or [] if isinstance(r, dict)]
    return {'approach': '', 'steps': [[_t(x.get('statement')), _t(x.get('justification'))] for x in s.get('steps') or [] if isinstance(x, dict)],
            'answer': _t(s.get('answer')), 'errors': [str(e) for e in s.get('typical_errors') or []],
            'hints': [_t(h) for h in s.get('hint_ladder') or [] if _t(h)],
            'rubric': rub if rub and a.get('points') is not None else []}


_TR = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'ae', 'Ö': 'oe', 'Ü': 'ue'})


def _key(text):
    """ASCII key part for derived cards (rule C5 allows [a-z0-9/_-]); 'Zufälle' -> 'zufaelle'."""
    import unicodedata
    t = unicodedata.normalize('NFKD', str(text).translate(_TR)).encode('ascii', 'ignore').decode()
    return slug(t)[:60]


def _topic(prompt, n=60):
    """Short exam-overview topic: first sentence, cut at a word boundary (was a hard cut mid-word)."""
    t = re.split(r'(?<=[.?!])\s', str(prompt).strip(), maxsplit=1)[0]
    if len(t) <= n:
        return t
    cut = t[:n]
    # never cut inside a formula: an unclosed \\( or \\[ moves the cut in front of it (or behind it if short)
    o = max(cut.rfind('\\('), cut.rfind('\\['))
    if o > max(cut.rfind('\\)'), cut.rfind('\\]')):
        close = re.search(r'\\[)\]]', t[o:])
        cut = t[:o + close.end()] if close and o + close.end() <= n + 40 else t[:o]
        return (cut.rstrip(' ,;:') + ' …') if cut.strip() else t[:n + 40]
    return cut.rsplit(' ', 1)[0].rstrip(',;:') + ' …'


def derived_cards(blocks, chapter_slug):
    """Conservative fallback: definitions and misconceptions only; key from the term (rule C5)."""
    out = []
    for b in blocks:
        if b['type'] == 'definition':
            ans = re.split(r'(?<=[.!?])\s', b['md'].strip(), maxsplit=1)[0]
            out.append({'key': f'def/{_key(b["term"])}', 'kind': 'concept', 'front': f'Was bedeutet „{b["term"]}“?',
                        'answer': ans, 'explanation': b['md'][len(ans):].strip()[:400], 'source': b.get('src', '')})
        elif b['type'] == 'misconception':
            out.append({'key': f'mis/{_key(b["wrong"])}', 'kind': 'misconception', 'front': f'Stimmt das: {b["wrong"].rstrip(".")}?',
                        'answer': b['right'], 'explanation': b.get('why', ''), 'source': ''})
    return out


def book_from_ast(ast, manifest, plan=None, ctx=None, course='Kurs', engine='', date=''):
    from .chapter_publish import _anchor_index, _anchors
    idx = _anchor_index(manifest)
    anchor_label = lambda refs: _anchors(refs, idx)
    vision = {e['element_id'] for e in manifest.get('elements', []) if e.get('kind') == 'visual_transcription'}
    chap = next((c for c in (plan or {}).get('chapters', []) if c['chapter_id'] == ast.get('chapter_id')), {})
    sections, cur = [], None
    blocks = [block(b, anchor_label, vision) for b in ast.get('blocks', [])]
    for raw, b in zip(ast.get('blocks', []), blocks):
        name = raw.get('section') or (cur['title'] if cur else 'Grundlagen')
        if cur is None or cur['title'] != name:
            cur = {'title': name, 'blocks': []}; sections.append(cur)
        # B15: competency links travel with the block (used by the learning environment; ignored by the typesetter)
        b['kc_ids'] = list(raw.get('kc_ids') or []); b['block_id'] = raw.get('block_id')
        cur['blocks'].append(b)
    if sections and sections[0]['blocks'] and sections[0]['blocks'][0]['type'] == 'text':
        sections[0]['blocks'][0] = {'type': 'lead', 'md': sections[0]['blocks'][0]['md']}
    sol = {s['item_id']: s for s in ast.get('solutions', [])}
    from .production import evidence_gap_items
    gaps = set(evidence_gap_items(ast.get('assessments', []), ast.get('exam_answers')))
    items = {}
    for n, a in enumerate(ast.get('assessments', []), 1):
        it = {'id': a['item_id'], 'no': a['item_id'], 'prompt': _t(a.get('prompt')), 'stage_label': a.get('difficulty', ''),
              'operation': a.get('required_operation'), 'kc_keys': a.get('kc_ids', []), 'space': 45,
              'faded': a.get('difficulty') == 'guided', 'solution': _solution(a, sol.get(a['item_id'], {})), 'evidence_gap': a['item_id'] in gaps}
        if a.get('points') is not None:
            it['points'] = a['points']
        items.setdefault(a.get('difficulty', 'standard'), []).append(it)
    stages = [{'title': t, 'level': lv, 'items': items[d]} for d, lv, t in STAGES if items.get(d)]
    exam_items = [dict(i, topic=_topic(i['prompt']), no=str(k)) for k, i in enumerate(
        [i for i in items.get('exam', []) if i.get('points') and not i['evidence_gap'] and i['solution']['answer']
         and abs(sum(r[1] for r in i['solution']['rubric']) - i['points']) < 1e-9], 1)]
    exam = None
    if exam_items:
        tot = sum(i['points'] for i in exam_items)
        exam = {'subtitle': 'Selbst entworfene Übungsklausur – keine offizielle Prüfung', 'total_points': tot, 'items': exam_items,
                'self_designed_notice': '**Hinweis:** Diese Probeklausur wurde selbst entworfen. Punkte und Bewertung sind keine offiziellen Vorgaben; '
                                        'Bearbeitungszeit und Hilfsmittel legt allein die Prüfung fest. Sie deckt nur dieses Kapitel ab.',
                'header': [['Punkte', str(tot)], ['Bearbeitungszeit', 'keine offizielle Vorgabe'], ['Hilfsmittel', 'keine offizielle Vorgabe']]}
    cslug = slug(ast.get('title', 'kapitel'))
    authored = ast.get('cards') or []
    cards = authored or derived_cards(blocks, cslug)
    dropped = {c.get('key', '?'): card_lint(c) for c in cards if card_lint(c)}
    cards = [c for c in cards if c.get('key') not in dropped]
    kcs = {k['kc_id']: k for k in (plan or {}).get('competencies', [])}
    comps = [{'key': k, 'operation': (kcs.get(k, {}).get('operations') or ['EXPLAIN'])[0]} for k in ast.get('kc_ids', []) if k in kcs]
    meta = {'title': ast.get('title', 'Kapitel'), 'subtitle': '', 'course': course, 'chapter_no': (chap.get('exam_relevance') or {}).get('section_number') or chap.get('position') or 1, 'lang': 'de',
            'date': date, 'engine': engine,
            'status_line': ('**SYNTHETISCHES TESTMATERIAL – kein Lerninhalt.** ' if ast.get('content_origin') == 'SYNTHETIC_FIXTURE' else '')
                           + '**Status:** Lernmaterial-Entwurf, modellgeneriert aus den Vorlesungsunterlagen und maschinell geprüft; '
                           'fachlich **nicht** von einer unabhängigen Fachperson geprüft (keine menschliche Quellenverifikation).'}
    return {'meta': meta, 'figures': {}, 'sections': sections, 'stages': stages, 'exam': exam, 'cards': cards, 'competencies': comps,
            'quantitative': any((kcs.get(k, {}).get('operations') or [''])[0] in ('CALCULATE', 'DERIVE', 'PROVE') for k in ast.get('kc_ids', [])),
            'card_source': 'AUTHORED' if authored else 'DERIVED_DEFINITIONS_AND_MISCONCEPTIONS', 'cards_dropped': dropped,
            # B15: learner-facing competency names (learning objectives first, then the cleaned plan statement)
            'kc_labels': kc_labels(ast, kcs)}


def kc_labels(ast, kcs):
    """Learner-facing competency names: the authored learning objective, else the title of the first textbook block
    that teaches the competency, else the plan statement without slide numbering and bullets."""
    out, seen = {}, set()
    for k in ast.get('kc_ids', []):
        st = (kcs.get(k) or {}).get('statement') or ''
        st = re.sub(r'^[^:]*(?:/[^:]*)?:\s*', '', st)
        st = re.sub(r'^\d+\|\s*', '', st).split('▪')[0].strip(' :–-')
        out[k] = st
    for b in ast.get('blocks') or []:
        t = _t(b.get('title'))
        for k in b.get('kc_ids') or []:
            if t and k in out and k not in seen:
                out[k] = t; seen.add(k)
    for o in ast.get('learning_objectives') or []:
        if o.get('kc_id') and _t(o.get('statement')):
            out[o['kc_id']] = _t(o['statement'])
    return out
