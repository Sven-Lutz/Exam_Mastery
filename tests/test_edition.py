"""B20 editions, v0.20 figures and exam blueprint integrity (no browser, no model)."""
import copy

import pytest

from exam_mastery import edition, figures_svg, typeset
from exam_mastery.common import ContractError


def book():
    sol = {'approach': '', 'steps': [['x', '']], 'answer': '42', 'errors': [], 'hints': [], 'rubric': [['a', 2.0]]}
    return {'meta': {'title': 'T', 'chapter_no': 1, 'course': 'K', 'date': '', 'engine': '', 'status_line': ''}, 'figures': {},
            'sections': [{'title': 'S1', 'blocks': [{'type': 'text', 'md': 'Vorlesungstext', 'prov': 'course', 'block_id': 'b1', 'kc_ids': ['k1']}]}],
            'stages': [{'title': 'St', 'level': 1, 'items': [{'id': 'a-01', 'no': 'a-01', 'prompt': 'P', 'operation': 'EXPLAIN', 'points': 2, 'solution': sol, 'kc_keys': ['k1']}]}],
            'exam': None, 'cards': [{'key': 'x/y', 'front': 'Was?', 'answer': 'Das.', 'kind': 'concept'}], 'kc_labels': {'k1': 'K1'}}


def ed(*ops, **kw):
    return dict({'schema': 'em-edition-v1', 'chapter_id': 'c', 'numeric_checks': {'c1': 'PASS'}, 'ops': list(ops)}, **kw)


def test_supplement_must_cite_a_verified_subject_source():
    with pytest.raises(ContractError, match='UNSOURCED'):
        edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'text', 'md': 'x', 'prov': 'supplement'}]}))
    with pytest.raises(ContractError, match='UNKNOWN_SOURCE'):
        edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'text', 'md': 'x', 'prov': 'supplement', 'sources': ['nope']}]}))
    b, rep = edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'text', 'md': 'x', 'prov': 'supplement', 'sources': ['gmbhg']}]}))
    assert b['sections'][0]['blocks'][1]['refs'] and rep['subject_sources_cited'] == ['gmbhg']


def test_edition_cannot_add_lecture_content_but_may_visualise_it():
    with pytest.raises(ContractError, match='COURSE_CONTENT'):
        edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'text', 'md': 'neu', 'prov': 'course'}]}))
    fig = {'f': {'type': 'bar', 'data': [['a', 1]]}}
    b, _ = edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [{'type': 'figure', 'id': 'f', 'prov': 'course', 'derived_from_block': 'b1'}]}, figures=fig))
    assert b['sections'][0]['blocks'][1]['id'] == 'f'


def test_unchecked_numbers_and_unknown_targets_are_refused():
    ex = {'type': 'example', 'prov': 'didactic', 'numeric': True, 'checks': ['c2'], 'title': 't', 'given': 'g', 'steps': []}
    with pytest.raises(ContractError, match='NUMBERS_UNCHECKED'):
        edition.apply(book(), ed({'op': 'insert_after', 'block_id': 'b1', 'blocks': [ex]}))
    with pytest.raises(ContractError, match='UNKNOWN_BLOCK'):
        edition.apply(book(), ed({'op': 'remove', 'block_id': 'zz', 'reason': 'r'}))
    with pytest.raises(ContractError, match='REASON'):
        edition.apply(book(), ed({'op': 'remove', 'block_id': 'b1'}))


def test_stages_keep_items_by_id_and_refuse_silent_drops():
    new = {'id': 'n-1', 'prompt': 'Q', 'operation': 'CALCULATE', 'points': 3, 'solution': {'answer': '1', 'rubric': [['r', 3]]}}
    with pytest.raises(ContractError, match='DROPPED_WITHOUT_REASON'):
        edition.apply(book(), ed({'op': 'stages', 'stages': [{'title': 'A', 'items': [new]}]}))
    b, _ = edition.apply(book(), ed({'op': 'stages', 'stages': [{'title': 'A', 'items': [copy.deepcopy(new), {'keep': 'a-01', 'transfer_dimension': 'near'}]}]}))
    assert [i['id'] for i in b['stages'][0]['items']] == ['n-1', 'a-01'] and b['stages'][0]['items'][1]['transfer_dimension'] == 'near'
    bad = dict(new, points=4)
    with pytest.raises(ContractError, match='RUBRIC_SUM'):
        edition.apply(book(), ed({'op': 'stages', 'dropped_reason': 'x', 'stages': [{'title': 'A', 'items': [bad]}]}))


def test_card_replacement_keeps_the_key_and_duplicates_fail():
    b, _ = edition.apply(book(), ed({'op': 'cards', 'replace': [{'key': 'x/y', 'front': 'Welche?', 'answer': 'Diese.', 'kind': 'concept'}]}))
    assert [c['key'] for c in b['cards']] == ['x/y'] and b['cards'][0]['front'] == 'Welche?'
    with pytest.raises(ContractError, match='DUPLICATE_CARD'):
        edition.apply(book(), ed({'op': 'cards', 'add': [{'key': 'x/y'}]}))


def test_exam_blueprint_and_time_are_enforced():
    it = {'id': 'x1', 'prompt': 'P', 'operation': 'CALCULATE', 'points': 4, 'minutes': 6, 'solution': {'answer': 'a', 'rubric': [['r', 4]]}}
    op = {'op': 'exam', 'items': [it], 'minutes': 5, 'self_designed_notice': 'selbst entworfen', 'subtitle': 's',
          'blueprint': {'rows': [{'item': 'x1', 'competency': 'k', 'operator': 'CALCULATE', 'points': 4, 'minutes': 6}]}}
    b, _ = edition.apply(book(), ed(op))
    assert any('exceed exam duration' in p for p in typeset.exam_check(b))
    op2 = dict(op, minutes=10, blueprint={'rows': [{'item': 'x1', 'competency': 'k', 'operator': 'CALCULATE', 'points': 3, 'minutes': 6}]})
    b2, _ = edition.apply(book(), ed(op2))
    assert any('blueprint/item mismatch' in p for p in typeset.exam_check(b2))
    b3, _ = edition.apply(book(), ed(dict(op, minutes=10)))
    assert typeset.exam_check(b3) == []


def test_new_figure_types_render_data_only():
    for spec in ({'type': 'line', 'x': [1, 2, 3], 'series': [{'name': 'a', 'values': [1, -2, 3]}, {'name': 'b' * 60, 'values': [0, 1, 2]}], 'band': {'from': 1.5, 'to': 2}, 'marks': [{'x': 2, 'label': 'm', 'side': 'left'}]},
                 {'type': 'heat_matrix', 'rows': ['1', '2'], 'cols': ['a', 'b'], 'classes': [['Low', 'High'], ['Critical', 'Moderate']]},
                 {'type': 'gantt', 'tasks': [{'id': 'A', 'name': 'A', 'start': 0, 'dur': 2, 'critical': True}, {'id': 'B', 'name': 'B', 'start': 2, 'dur': 1, 'float': 1}], 'deps': [['A', 'B']]},
                 {'type': 'adoption_curve', 'chasm_after': 1}):
        svg = figures_svg.render(spec)
        assert svg.startswith('<svg') and 'NaN' not in svg
