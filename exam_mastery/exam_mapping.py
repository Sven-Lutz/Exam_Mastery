"""B33: audit of exam/practice items that the planner linked to a chapter although they come from other sources.

Root cause found in the RL pilot: items were judged only by source-file membership ("not in the chapter's sources"
-> EXAM_ITEM_OUTSIDE_CHAPTER_SOURCES). That (a) kept headings, announcements and exercise notices as 'questions' and
(b) threw away official *example exam questions* of a tutorial that belong to the chapter by content.

`classify` returns a proposal per item with evidence; it never decides relevance on its own beyond deterministic
cases. Classes:
  NOT_AN_ASSESSMENT         heading/announcement/recap/notebook notice (no answerable task)
  OTHER_CHAPTER_SOURCE      answerable question from a lecture source that belongs to another chapter -> REASSIGN
  CANDIDATE_FOR_CHAPTER     practice/tutorial item (incl. 'example exam question' pages) whose wording overlaps the
                            chapter's competency vocabulary -> needs a content decision (agent or human)
  PRACTICE_OTHER_TOPIC      practice item without overlap -> REASSIGN to the topic's chapter when it is produced
"""
import re

NOT_TASK = re.compile(r'^\s*(?:does it work\??|questions\?|what have we learned|what you should know|notebook|exercise \d+\s*:|'
                      r'.*submission deadline|.*available on ilias|rl today)', re.I)
EXAMPLE_EXAM = re.compile(r'example exam question|beispiel[- ]?klausur|klausuraufgabe|probeklausur|exam question', re.I)
WORD = re.compile(r'[a-zA-Zäöüß]{4,}')
STOP = set('that this with from what which when where does into have will your their there about would could should these those '
           'than then them they also only over such each more most very many much some like just after before while because '
           'value values state states action actions policy policies reward rewards learning lecture question questions example exam exercise'.split())


def _vocab(texts):
    return {w.lower() for t in texts for w in WORD.findall(t or '')} - STOP


def classify(item_text, item_source, item_page_text, chapter_sources, source_owner, chapter_vocab, source_role=None):
    """item_source: source_id; source_owner: {source_id: chapter_id or None}; chapter_vocab: set of words."""
    t = (item_text or '').strip()
    ev = {'source': item_source, 'source_role': source_role}
    example = bool(EXAMPLE_EXAM.search((item_page_text or '') + ' ' + t))
    task = '?' in t or bool(re.search(r'\b(solve|compute|calculate|berechnen|bestimmen|zeigen|explain|erkl)', t, re.I))
    if example and task:                               # an official example-exam task is never discarded as a heading
        overlap = sorted(_vocab([t]) & chapter_vocab)
        cls = 'CANDIDATE_FOR_CHAPTER' if len(overlap) >= 2 else 'PRACTICE_OTHER_TOPIC'
        return cls, dict(ev, why=f'official example-exam task; vocabulary overlap {overlap[:8]}', example_exam=True)
    if NOT_TASK.match(t) or ('?' not in t and not re.search(r'\b(solve|compute|calculate|berechnen|bestimmen|zeigen|explain|erkl)', t, re.I)):
        return 'NOT_AN_ASSESSMENT', dict(ev, why='heading/announcement pattern or no task verb/question mark')
    owner = source_owner.get(item_source)
    if owner and item_source not in chapter_sources:
        return 'OTHER_CHAPTER_SOURCE', dict(ev, why=f'source belongs to chapter {owner}', target=owner)
    overlap = sorted(_vocab([t, item_page_text]) & chapter_vocab)
    example = bool(EXAMPLE_EXAM.search(item_page_text or ''))
    if len(overlap) >= 3 or (example and len(overlap) >= 2):
        return 'CANDIDATE_FOR_CHAPTER', dict(ev, why=('official example-exam page; ' if example else '') + f'vocabulary overlap {overlap[:8]}', example_exam=example)
    return 'PRACTICE_OTHER_TOPIC', dict(ev, why=f'overlap {overlap[:5]} too small', example_exam=example)


def audit(issue_rows, curriculum, inventory, chapter_id):
    """Proposals for every EXAM_ITEM_OUTSIDE_CHAPTER_SOURCES issue: [{issue_id,item_id,class,evidence}]."""
    items = {i['item_id']: i for i in curriculum.get('assessment_items') or []}
    el = {e['element_id']: e for e in inventory.get('elements') or []}
    page_text = {}
    for e in inventory.get('elements') or []:
        k = (e['source_id'], (e.get('locator') or {}).get('page'))
        page_text[k] = page_text.get(k, '') + ' ' + (e.get('text') or '')
    chap = next(c for c in curriculum['chapters'] if c['chapter_id'] == chapter_id)
    owner = {s: c['chapter_id'] for c in curriculum['chapters'] for s in c.get('source_ids') or []}
    kcs = [k for k in curriculum.get('competencies') or [] if k['kc_id'] in set(chap.get('kc_ids') or [])]
    vocab = _vocab([k.get('statement') for k in kcs] + [k.get('topic_text') for k in kcs])
    roles = curriculum.get('source_roles') or {}
    out = []
    for r in issue_rows:
        if r.get('code') != 'EXAM_ITEM_OUTSIDE_CHAPTER_SOURCES':
            continue
        it = items.get(r.get('object_id')) or {}
        anc = [el[x] for x in it.get('anchor_element_ids') or [] if x in el]
        src = anc[0]['source_id'] if anc else None
        pg = (anc[0].get('locator') or {}).get('page') if anc else None
        txt = it.get('own_wording') or ' '.join(a.get('text') or '' for a in anc)
        cls, ev = classify(txt, src, page_text.get((src, pg), ''), set(chap.get('source_ids') or []), owner, vocab,
                           (roles.get(src) or {}).get('role'))
        out.append({'issue_id': r['issue_id'], 'item_id': r.get('object_id'), 'class': cls, 'page': pg,
                    'source_path': (roles.get(src) or {}).get('relative_path'), 'wording': txt[:160], 'evidence': ev})
    return out
