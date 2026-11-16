"""B22: fixable publishing-gate defects are reported to the one bounded revision instead of ending in GATE_FAILED."""
from exam_mastery.production import draft_gate_findings

KCS = [{'kc_id': 'kc-calc', 'operations': ['EXPLAIN', 'CALCULATE']}, {'kc_id': 'kc-exp', 'operations': ['EXPLAIN']}]


def codes(product):
    return sorted((f['code'], f['object_id']) for f in draft_gate_findings(product, KCS))


def triggers(product):
    return sorted(f['code'] for f in draft_gate_findings(product, KCS) if f['trigger'])


WE = {'problem': 'p', 'steps': [{'statement': 's', 'justification': 'j'}], 'result': 'r'}


def test_clean_draft_has_no_findings():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'assumptions': ['γ = 0.9'], 'interpretation': 'x', **WE}],
         'solutions': [{'solution_id': 's1', 'answer': 'V = 8.064516129', 'steps': [],
                        'numeric_checks': [{'expression': '2/0.248', 'expected': 8.064516129032258}]}]}
    assert codes(p) == []


def test_rounded_expected_value_and_missing_statement_are_reported():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'assumptions': ['a'], 'interpretation': 'x', **WE}],
         'solutions': [{'solution_id': 's1', 'answer': 'etwa 8.06', 'steps': [], 'numeric_checks': [{'expression': '2/0.248', 'expected': 8.0645}]},
                       {'solution_id': 's2', 'answer': 'gamma ist 0.19', 'steps': [], 'numeric_checks': [{'expression': '2*0.5', 'expected': 1}]}]}
    assert codes(p) == [('ANSWER_CONSISTENCY', 's2'), ('NUMERIC_CHECK_MISMATCH', 's1')]


def test_calculation_without_assumptions_and_missing_exposition():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'interpretation': 'x', **WE}], 'solutions': []}
    assert codes(p) == [('CALCULATION_WITHOUT_ASSUMPTIONS', 'b1')]
    p = {'blocks': [{'block_id': 'b1', 'kind': 'EXPLANATION', 'kc_ids': ['kc-calc']}], 'solutions': []}
    assert codes(p) == [('MISSING_EXPOSITION_CALCULATE', 'kc-calc')]


def test_publish_blocking_structure_is_reported_before_the_revision():
    # B31: G0 worked-example structure, G4.DOMAIN_FORMAL and shape checks block publishing, so they start the revision
    p = {'blocks': [{'block_id': 'we', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-exp'], 'steps': [{'statement': 's', 'justification': 'j'}],
                     'result': 'r', 'interpretation': 'i'},
                    {'block_id': 'pr', 'kind': 'PROOF', 'kc_ids': ['kc-exp'], 'steps': [{'statement': 's', 'justification': 'j'}]},
                    {'block_id': 'mo', 'kind': 'MODEL', 'kc_ids': ['kc-exp'], 'assumptions': ['γ < 1'],
                     'shape_checks': {'symbols': {'P': [2, 2], 'V': [2, 1], 'r': [2, 1]}, 'equations': [{'lhs': '(I - gamma P) V', 'rhs': 'r'}]}},
                    {'block_id': 'ok', 'kind': 'THEOREM', 'kc_ids': ['kc-exp'], 'assumptions': ['γ < 1'],
                     'shape_checks': {'symbols': {'P': [2, 2], 'V': [2, 1], 'r': [2, 1]}, 'equations': [{'lhs': 'P V', 'rhs': 'r'}]}}],
         'solutions': []}
    kcs = [{'kc_id': 'kc-exp', 'operations': ['EXPLAIN']}]
    found = draft_gate_findings(p, kcs)
    assert sorted((f['code'], f['object_id']) for f in found) == [
        ('DIMENSION_MISMATCH', 'mo'), ('FORMAL_WITHOUT_ASSUMPTIONS', 'pr'), ('INCOMPLETE_WORKED_EXAMPLE', 'we')]
    assert all(f['trigger'] for f in found)


def test_only_blocking_findings_start_a_revision():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'interpretation': 'x', **WE}],
         'solutions': [{'solution_id': 's2', 'answer': 'x', 'steps': [], 'numeric_checks': [{'expression': '2*0.5', 'expected': 1}]}]}
    assert triggers(p) == []          # assumptions / answer consistency ride along only
    p['solutions'][0]['numeric_checks'][0]['expected'] = 1.01
    assert triggers(p) == ['NUMERIC_CHECK_MISMATCH']


def test_equation_checker_ignores_fragments_but_keeps_real_errors():
    from exam_mastery.numeric_checks import equations
    ok = lambda t: [(e, s, good) for e, s, _, good in equations(t)]
    # fragments of correct computations are not recomputed on their own (were false FAILs before B22)
    # B33: an implicit-product Bellman backup is checked as ONE computation (not dropped, not cut into fragments)
    assert ok('\\(V_2(H) = 2 + 0.5(0.7 \\cdot 2 + 0.3 \\cdot 0) = 2.7\\)') == [('2 + 0.5*(0.7 * 2 + 0.3 * 0)', '2.7', True)]
    assert ok('\\(V_2(H) = 2 + 0.5(0.7 \\cdot 2 + 0.3 \\cdot 0) = 2.9\\)') == [('2 + 0.5*(0.7 * 2 + 0.3 * 0)', '2.9', False)]
    assert ok('\\(V(H)(1 - 0.63 - 0.243) = 2\\)') == []
    assert ok('Probe: \\(0.5^3 \\cdot 8 = 1 = 0.5 \\cdot 2\\)') == []
    # in a chain only complete links are checked
    assert ok('\\(2 + 0.8 \\cdot (0.7 \\cdot 2 + 0.3 \\cdot 0) = 2 + 0.8 \\cdot 1.4 = 3.12\\)') == [('2 + 0.8 * 1.4', '3.12', True)]
    # real errors and plain computations are still found
    assert ok('Kosten 3 + 4 = 8 Euro') == [('3 + 4', '8', False)]
    assert ok('a=1+1=3') == [('1+1', '3', False)]
    assert ok('Summe 1,000 + 500 = 1,500') == [('1,000 + 500', '1,500', True)]
    assert ok('74 / 100 = 74 %') == [('74 / 100', '74', True)]
