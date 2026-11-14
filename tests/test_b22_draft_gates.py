"""B22: fixable publishing-gate defects are reported to the one bounded revision instead of ending in GATE_FAILED."""
from exam_mastery.production import draft_gate_findings

KCS = [{'kc_id': 'kc-calc', 'operations': ['EXPLAIN', 'CALCULATE']}, {'kc_id': 'kc-exp', 'operations': ['EXPLAIN']}]


def codes(product):
    return sorted((f['code'], f['object_id']) for f in draft_gate_findings(product, KCS))


def triggers(product):
    return sorted(f['code'] for f in draft_gate_findings(product, KCS) if f['trigger'])


def test_clean_draft_has_no_findings():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'assumptions': ['γ = 0.9'], 'interpretation': 'x'}],
         'solutions': [{'solution_id': 's1', 'answer': 'V = 8.064516129', 'steps': [],
                        'numeric_checks': [{'expression': '2/0.248', 'expected': 8.064516129032258}]}]}
    assert codes(p) == []


def test_rounded_expected_value_and_missing_statement_are_reported():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'assumptions': ['a'], 'interpretation': 'x'}],
         'solutions': [{'solution_id': 's1', 'answer': 'etwa 8.06', 'steps': [], 'numeric_checks': [{'expression': '2/0.248', 'expected': 8.0645}]},
                       {'solution_id': 's2', 'answer': 'gamma ist 0.19', 'steps': [], 'numeric_checks': [{'expression': '2*0.5', 'expected': 1}]}]}
    assert codes(p) == [('ANSWER_CONSISTENCY', 's2'), ('NUMERIC_CHECK_MISMATCH', 's1')]


def test_calculation_without_assumptions_and_missing_exposition():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'interpretation': 'x'}], 'solutions': []}
    assert codes(p) == [('CALCULATION_WITHOUT_ASSUMPTIONS', 'b1')]
    p = {'blocks': [{'block_id': 'b1', 'kind': 'EXPLANATION', 'kc_ids': ['kc-calc']}], 'solutions': []}
    assert codes(p) == [('MISSING_EXPOSITION_CALCULATE', 'kc-calc')]


def test_only_blocking_findings_start_a_revision():
    p = {'blocks': [{'block_id': 'b1', 'kind': 'WORKED_EXAMPLE', 'kc_ids': ['kc-calc'], 'interpretation': 'x'}],
         'solutions': [{'solution_id': 's2', 'answer': 'x', 'steps': [], 'numeric_checks': [{'expression': '2*0.5', 'expected': 1}]}]}
    assert triggers(p) == []          # assumptions / answer consistency ride along only
    p['solutions'][0]['numeric_checks'][0]['expected'] = 1.01
    assert triggers(p) == ['NUMERIC_CHECK_MISMATCH']


def test_equation_checker_ignores_fragments_but_keeps_real_errors():
    from exam_mastery.numeric_checks import equations
    ok = lambda t: [(e, s, good) for e, s, _, good in equations(t)]
    # fragments of correct computations are not recomputed on their own (were false FAILs before B22)
    assert ok('\\(V_2(H) = 2 + 0.5(0.7 \\cdot 2 + 0.3 \\cdot 0) = 2.7\\)') == []
    assert ok('\\(V(H)(1 - 0.63 - 0.243) = 2\\)') == []
    assert ok('Probe: \\(0.5^3 \\cdot 8 = 1 = 0.5 \\cdot 2\\)') == []
    # in a chain only complete links are checked
    assert ok('\\(2 + 0.8 \\cdot (0.7 \\cdot 2 + 0.3 \\cdot 0) = 2 + 0.8 \\cdot 1.4 = 3.12\\)') == [('2 + 0.8 * 1.4', '3.12', True)]
    # real errors and plain computations are still found
    assert ok('Kosten 3 + 4 = 8 Euro') == [('3 + 4', '8', False)]
    assert ok('a=1+1=3') == [('1+1', '3', False)]
    assert ok('Summe 1,000 + 500 = 1,500') == [('1,000 + 500', '1,500', True)]
    assert ok('74 / 100 = 74 %') == [('74 / 100', '74', True)]
