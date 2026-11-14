import copy
import json

import pytest

from exam_mastery import knowledge as kbm


def test_kb_is_internally_consistent_and_verified():
    assert kbm.validate() == []


def test_every_abstract_snippet_was_found():
    v = kbm.load()['verification']['summary']
    assert v['snippets_checked'] > 0 and v['snippets_found'] == v['snippets_checked']
    # statutes / official pages carry no DOI or ISBN: they count as read primary texts, everything else must resolve
    assert v['verified'] + v.get('primary_text_read', 0) == v['sources']


def test_validator_catches_unknown_source_and_missing_evidence():
    kb = copy.deepcopy(kbm.load())
    c = kb['principles']['principles'][0]['claims'][0]
    c['sources'] = ['nonexistent2099']
    c['abstract_evidence'] = []
    errs = kbm.validate(kb, require_verification=False)
    assert any('unknown source nonexistent2099' in e for e in errs)
    assert any('abstract_checked without abstract_evidence' in e for e in errs)


def test_validator_rejects_abstract_evidence_from_metadata_only_source():
    kb = copy.deepcopy(kbm.load())
    meta = next(s['id'] for s in kb['sources']['sources'] if s['access'] == 'metadata')
    c = kb['principles']['principles'][0]['claims'][0]
    c['sources'].append(meta)
    c['abstract_evidence'].append({'source': meta, 'snippet': 'x'})
    assert any('metadata-only source' in e for e in kbm.validate(kb, require_verification=False))


def test_validator_catches_unresolvable_enforcement():
    kb = copy.deepcopy(kbm.load())
    kb['principles']['principles'][0]['engine_rules'][0]['enforcement'] = 'deterministic:didactic_rules.no_such_function'
    assert any('does not resolve' in e for e in kbm.validate(kb, require_verification=False))


def test_rejected_principles_have_no_positive_rules_leaking_into_context():
    ctx = kbm.context_for('learn_app')
    assert 'LS-R1' in ctx  # the prohibition itself is passed on
    assert '[REJECTED]' in ctx


def test_context_is_compact_and_subject_adapted():
    ctx = kbm.context_for('workbook', subject='law')
    assert len(ctx) <= 6000
    assert 'Gutachtenstil' in ctx and kbm.fingerprint() in ctx
    assert 'worked_example_fading' in ctx


ITEM = {"id": "t1", "competency": "C.npv", "operator": "berechnen", "process_level": "apply", "purpose": "independent",
        "transfer_dimension": "none", "minutes": 8, "points": 6,
        "prompt": "Berechnen Sie den Kapitalwert der Zahlungsreihe -100, 60, 60 bei 10 % Zins.",
        "solution": {"strategy": "Barwerte summieren", "steps": ["-100 + 60/1.1 + 60/1.21"], "result": 4.13},
        "rubric": [{"criterion": "Ansatz", "points": 2}, {"criterion": "Rechnung", "points": 3}, {"criterion": "Interpretation", "points": 1}]}


def test_item_checks():
    assert kbm.check_item(ITEM) == []
    bad = dict(ITEM, points=7)
    assert any('rubric sums' in e for e in kbm.check_item(bad))
    assert any('transfer_dimension' in e for e in kbm.check_item(dict(ITEM, purpose='transfer')))
    assert kbm.check_item({k: v for k, v in ITEM.items() if k != 'solution'})


def test_number_only_variants_are_flagged():
    twin = dict(ITEM, id='t2', prompt=ITEM['prompt'].replace('60, 60', '70, 50'))
    assert kbm.check_item_set([ITEM, twin])
    assert kbm.check_item_set([ITEM, dict(twin, purpose='retrieval')]) == []


def test_exam_against_blueprint():
    bp = {"minutes": 20, "total_points": 6, "rows": [{"competency": "C.npv", "operator": "berechnen", "points": 6}]}
    assert kbm.check_exam_against_blueprint({"minutes": 20, "items": [ITEM]}, bp) == []
    bp2 = dict(bp, total_points=10, rows=[{"competency": "C.npv", "operator": "berechnen", "points": 6}, {"competency": "C.irr", "operator": "berechnen", "points": 4}])
    errs = kbm.check_exam_against_blueprint({"minutes": 20, "items": [ITEM]}, bp2)
    assert any('C.irr' in e for e in errs) and any('points' in e for e in errs)
    assert kbm.check_exam_against_blueprint({"minutes": 5, "items": [ITEM]}, dict(bp, minutes=5))


def test_fingerprint_changes_with_rules(tmp_path, monkeypatch):
    before = kbm.fingerprint()
    for n in ('sources.json', 'principles.json', 'specs.json'):
        (tmp_path / n).write_bytes((kbm.HERE / n).read_bytes())
    p = json.loads((tmp_path / 'principles.json').read_text())
    p['principles'][0]['engine_rules'][0]['rule'] += ' (geändert)'
    (tmp_path / 'principles.json').write_text(json.dumps(p))
    monkeypatch.setattr(kbm, 'HERE', tmp_path)
    assert kbm.fingerprint() != before


def test_audit_flags_structural_gaps(tmp_path):
    from exam_mastery.knowledge.audit import audit
    it = lambda i, op, stage, pts=2, rub=None, prompt=None: {
        'id': i, 'stage': stage, 'operation': op, 'kc_ids': ['k1'], 'points': pts, 'hints': ['h'],
        'prompt': prompt or f'<p>Erklären Sie Aspekt {i} des Konzepts ausführlich.</p>', 'solution': '<p>Lösung</p>',
        'rubric': rub if rub is not None else [['a', pts]]}
    course = {'kcs': {'k1': 'A', 'k2': 'B'}, 'labs': [], 'cards': [{'id': 'c1', 'front': 'Ist das so?', 'back': 'ja', 'source': 's'}],
              'items': [it('a1', 'EXPLAIN', 'standard'), it('a2', 'EXPLAIN', 'standard', rub=[['a', 1]]),
                        it('a3', 'CALCULATE', 'standard', prompt='<p>Berechnen Sie 5 + 7 für das Konzept hier.</p>'),
                        it('a4', 'CALCULATE', 'standard', prompt='<p>Berechnen Sie 9 + 2 für das Konzept hier.</p>')],
              'exam': {'items': ['a1'], 'total_points': 5}}
    (tmp_path / 'course.json').write_text(json.dumps(course))
    msgs = {(f['rule'], f['finding']) for f in audit(tmp_path)['findings']}
    text = ' | '.join(m for _, m in msgs)
    assert 'Rubrik summiert 1' in text
    assert 'nur in Zahlen' in text
    assert 'ohne Fading-Stufe' in text
    assert 'ohne jede Abrufaufgabe' in text
    assert 'Punktsumme 2 ≠ angegebene 5' in text
    assert 'Ja/Nein-Frage' in text


def test_fulltext_claims_require_located_evidence():
    kb = copy.deepcopy(kbm.load())
    c = next(c for p in kb['principles']['principles'] for c in p['claims'] if c['basis'] == 'fulltext_checked')
    c['fulltext_evidence'] = [{'source': c['sources'][0]}]
    assert any('located fulltext_evidence' in e for e in kbm.validate(kb, require_verification=False))
