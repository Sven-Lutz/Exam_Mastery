"""Book-like scripts split at pages that open with a bare 'KAPITEL n' line (Analysis 1 script)."""
from exam_mastery.curriculum import _paged_sections


def _el(i, p, t):
    return {'element_id': f'e{i}', 'kind': 'paragraph', 'text': t, 'locator': {'page': p}}


def _pm(pages):
    els, P, i = [], {}, 0
    for p, texts in pages.items():
        row = []
        for t in texts:
            i += 1; e = _el(i, p, t); els.append(e); row.append(e)
        P[p] = {'title': row[0] if row else None, 'elements': row}
    src = {'source_id': 's', 'element_ids': [e['element_id'] for e in els]}
    return {'elements': els}, src, {'s': {'pages': P, 'boilerplate': set(), 'page_key': 'page'}}


def test_split_at_chapter_openers():
    pages = {1: ['Inhalt', 'Kapitel 1. A 3'], 2: ['KAPITEL 1', 'Zahlen', 'Text', 'Text', 'Text'], 3: ['mehr', 'x', 'y', 'z'],
             4: ['KAPITEL 2', 'Konvergenz von Folgen', 'Def', 'Satz', 'Beweis'], 5: ['a', 'b', 'c', 'd']}
    man, src, pm = _pm(pages)
    secs = _paged_sections(man, src, pm)
    assert [h['text'] for h, _, _ in secs] == ['Zahlen', 'Konvergenz von Folgen']
    assert secs[1][2]['pages'] == [4, 5] and secs[0][2]['status'] == 'SPLIT_AT_CHAPTER_OPENERS'


def test_single_opener_or_decreasing_numbers_do_not_split():
    man, src, pm = _pm({1: ['KAPITEL 2', 'B', 'x', 'y'], 2: ['KAPITEL 1', 'A', 'x', 'y']})
    assert len(_paged_sections(man, src, pm)) == 1
