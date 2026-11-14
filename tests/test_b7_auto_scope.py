"""B7: automatic text-only scope for competencies that only await a visual/neighbour-page review."""
import json, unittest
from pathlib import Path
from exam_mastery import auto_scope as A
from exam_mastery.chapter_publish import author_draft_checks
from exam_mastery.production import STAGE_GATE_CRITICAL

FUNDING_PLAN = Path.home() / 'Developer/Exam_Mastery_Studio/runs_v0_5_1_p0_dev/course-fe494a74afef/ch-20261106T151648Z-0a55aadd/plan'


def el(eid, kind, page, text='', status='ok'):
    return {'element_id': eid, 'source_id': 's1', 'kind': kind, 'status': status, 'text': text, 'locator': {'page': page}}


WORDS = 'equity investors accept the highest risk and the lowest rank in insolvency while lenders rank first ' * 2


def fixture(text_on_rich_page=True):
    els = [el('h1', 'heading', 1, 'Risk classes'), el('p1', 'paragraph', 1, WORDS if text_on_rich_page else 'x'),
           el('p2', 'paragraph', 1, 'mezzanine sits between equity and loans'), el('v1', 'diagram', 1),
           el('h2', 'heading', 2, 'Hippodrome'), el('v2', 'image', 2),
           el('h3', 'heading', 3, 'Market size'), el('v3', 'image', 3)]
    kcs = [{'kc_id': 'k-text', 'statement': 'explain risk classes', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h1']},
           {'kc_id': 'k-calc', 'statement': 'calculate shares', 'operations': ['CALCULATE'], 'source_anchor_ids': ['h1']},
           {'kc_id': 'k-thin', 'statement': 'explain metaphor', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h2']},
           {'kc_id': 'k-ess', 'statement': 'explain market chart', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h3']},
           {'kc_id': 'k-ok', 'statement': 'name sources', 'operations': ['NAME'], 'source_anchor_ids': ['h1']}]
    plan = {'competencies': kcs, 'chapters': [{'chapter_id': 'c1', 'kc_ids': [k['kc_id'] for k in kcs]}]}
    f = lambda k, v: {'code': 'VISUAL_RELEVANCE_UNKNOWN', 'severity': 'review', 'kc_ids': [k], 'element_ids': [v]}
    gate = {'chapter_id': 'c1', 'status': 'PARTIAL', 'producible_kc_ids': ['k-ok'],
            'blocked_kcs': {'k-ess': ['ESSENTIAL_VISUAL_UNRESOLVED']},
            'review_required_kcs': {'k-text': ['VISUAL_RELEVANCE_UNKNOWN'], 'k-calc': ['VISUAL_RELEVANCE_UNKNOWN'],
                                    'k-thin': ['VISUAL_RELEVANCE_UNKNOWN']},
            'findings': [f('k-text', 'v1'), f('k-calc', 'v1'), f('k-thin', 'v2')]}
    return plan, {'elements': els}, gate


class AutoScope(unittest.TestCase):
    def test_categories(self):
        plan, m, g = fixture()
        c = A.classify(plan, m, g)
        self.assertEqual(c['k-ok']['category'], A.SOURCE_DIRECT)
        self.assertEqual(c['k-text']['category'], A.TEXT_ONLY)
        self.assertEqual(c['k-calc']['category'], A.TEXT_ONLY_LABELLED)
        self.assertEqual(c['k-thin']['category'], A.VISUAL_REVIEW)    # title only: never produced from nothing
        self.assertEqual(c['k-ess']['category'], A.VISUAL_REVIEW)     # essential visual without a V2 rule stays excluded
        self.assertEqual(c['k-text']['excluded_visual_element_ids'], ['v1'])
        self.assertNotIn('v1', c['k-text']['text_element_ids'])
        self.assertFalse(c['k-text']['source_claim_human_verified'])

    def test_apply_does_not_touch_blockers_or_input(self):
        plan, m, g = fixture()
        before = json.dumps(g, sort_keys=True)
        out = A.apply(plan, m, {'c1': g})['c1']
        self.assertEqual(json.dumps(g, sort_keys=True), before)
        self.assertEqual(sorted(out['producible_kc_ids']), ['k-calc', 'k-ok', 'k-text'])
        self.assertEqual(out['blocked_kcs'], g['blocked_kcs'])
        self.assertEqual(list(out['review_required_kcs']), ['k-thin'])
        self.assertEqual(out['status'], 'PARTIAL')

    def test_too_little_text_stays_excluded(self):
        plan, m, g = fixture(text_on_rich_page=False)
        self.assertEqual(A.classify(plan, m, g)['k-text']['category'], A.VISUAL_REVIEW)

    def test_stage_gate_blocks_cited_excluded_visual(self):
        ctx = {'allowed_source_refs': ['h1', 'p1', 'v1'], 'produce_kc_ids': ['k-text'],
               'competencies': [{'kc_id': 'k-text', 'auto_scope': {'excluded_visual_element_ids': ['v1']}}]}
        bad = {'blocks': [{'block_id': 'b1', 'kc_ids': ['k-text'], 'source_refs': ['p1', 'v1'], 'provenance': 'COURSE_SOURCE', 'body': 'x'}]}
        good = {'blocks': [{'block_id': 'b1', 'kc_ids': ['k-text'], 'source_refs': ['p1'], 'provenance': 'COURSE_SOURCE', 'body': 'x'}]}
        st = lambda a: [c['status'] for c in author_draft_checks(a, ctx, {'elements': []}) if c['check'] == 'AUTO_SCOPE_TEXT_ONLY']
        self.assertEqual(st(bad), ['FAIL']); self.assertEqual(st(good), ['PASS'])
        self.assertIn('AUTO_SCOPE_TEXT_ONLY', STAGE_GATE_CRITICAL)

    @unittest.skipUnless((FUNDING_PLAN / 'curriculum.json').exists(), 'private Funding run not available')
    def test_real_funding_scope(self):
        g = json.loads((FUNDING_PLAN / 'chapter_gates_before_review_decisions.json').read_text())
        g = g.get('gates', g)
        plan = json.loads((FUNDING_PLAN / 'curriculum.json').read_text())
        m = json.loads((FUNDING_PLAN / 'source_inventory.json').read_text())
        rows = A.coverage_report(plan, m, {'ch-cf1411d6b23210': g['ch-cf1411d6b23210']})
        self.assertEqual(sum(r['produced_before'] for r in rows), 24)
        self.assertEqual(sum(r['produced_after'] for r in rows), 41)
        self.assertEqual(sum(r['category'] == A.VISUAL_REVIEW for r in rows), 3)       # chart-only content stays visible
        self.assertEqual(sum(r['category'] == A.NO_OBJECTIVE for r in rows), 1)        # the 'Funding a Venture' title slide


class AutoPreflight(unittest.TestCase):
    def test_low_risk_items_resolve_others_escalate(self):
        from exam_mastery.chapters import _auto_resolution
        self.assertEqual(_auto_resolution({'code': 'CHAPTER_REVIEW_OPEN', 'finding': 'CHAPTER_MERGE_REVIEW'}), 'AUTO_KEPT_SEPARATE_NOT_MERGED')
        self.assertEqual(_auto_resolution({'code': 'ELIGIBILITY_ONLY_INFERRED_TOPICS'}), 'AUTO_PRODUCED_EXAM_RELEVANCE_NOT_ESTABLISHED')
        for o in ({'code': 'CHAPTER_REVIEW_OPEN', 'finding': 'OTHER'}, {'code': 'INELIGIBLE'}, {'code': 'GATE_BLOCKED'},
                  {'code': 'COURSE_ORDER_UNRESOLVED'}, {'code': 'SESSION_IDENTITY_UNRESOLVED'}):
            self.assertIsNone(_auto_resolution(o), o)


def v2_fixture(words):
    """One KC blocked by rule V2 (figure dominant) next to `words` words of slide text."""
    text = ' '.join(['pricing'] * words)
    els = [el('h', 'heading', 1, 'Pricing'), el('p1', 'paragraph', 1, text), el('p2', 'paragraph', 1, 'optimal price'),
           el('p3', 'paragraph', 1, 'upper limit'), el('fig', 'image', 1)]
    plan = {'competencies': [{'kc_id': 'k', 'statement': 'Erkläre/explain: Pricing', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h'],
                              'origin': 'slide_title_topic'}],
            'chapters': [{'chapter_id': 'c1', 'title': 'Marketing', 'kc_ids': ['k']}]}
    gate = {'chapter_id': 'c1', 'status': 'BLOCKED', 'producible_kc_ids': [], 'blocked_kcs': {'k': ['ESSENTIAL_VISUAL_UNRESOLVED']},
            'review_required_kcs': {}, 'findings': [{'code': 'ESSENTIAL_VISUAL_UNRESOLVED', 'severity': 'blocker', 'kc_ids': ['k'],
                                                     'element_ids': ['fig'], 'rule': 'V2_VISUAL_DOMINANT'}]}
    return plan, {'elements': els}, gate


class B7Corrections(unittest.TestCase):
    def test_text_rich_v2_slide_is_taught_from_text_with_label(self):
        plan, m, g = v2_fixture(40)
        c = A.classify(plan, m, g)['k']
        self.assertEqual(c['category'], A.TEXT_ONLY_LABELLED)
        self.assertEqual(c['excluded_visual_element_ids'], ['fig'])
        self.assertIn('STATE_ONCE_THAT_VALUES_IN_THE_FIGURE_WERE_NOT_USED', c['restrictions'])
        out = A.apply(plan, m, {'c1': g})['c1']
        self.assertEqual(out['producible_kc_ids'], ['k']); self.assertEqual(out['blocked_kcs'], {})

    def test_text_poor_v2_slide_stays_visual_review(self):
        plan, m, g = v2_fixture(3)
        self.assertEqual(A.classify(plan, m, g)['k']['category'], A.VISUAL_REVIEW)
        self.assertEqual(A.apply(plan, m, {'c1': g})['c1']['producible_kc_ids'], [])

    def test_other_blocking_rules_are_untouched(self):
        plan, m, g = v2_fixture(40)
        g['findings'][0]['rule'] = 'V_SLIDE_OR_NONPDF'
        self.assertEqual(A.classify(plan, m, g)['k']['category'], A.VISUAL_REVIEW)
        g['blocked_kcs']['k'] = ['SCANNED_PAGE_NO_OCR']
        self.assertEqual(A.apply(plan, m, {'c1': g})['c1']['producible_kc_ids'], [])

    def test_title_and_citation_slides_have_no_objective(self):
        for title, linked in (('Marketing', ['q1']), ('31 | Source: Researchgate', []), ('Further reads', [])):
            plan, m, g = v2_fixture(3)
            plan['competencies'][0].update(statement='Erkläre/explain: ' + title, linked_item_ids=linked)
            self.assertEqual(A.classify(plan, m, g)['k']['category'], A.NO_OBJECTIVE, title)
        plan, m, g = v2_fixture(3)
        plan['competencies'][0].update(statement='Erkläre/explain: Smith, 2020', linked_item_ids=['q1'])
        self.assertEqual(A.classify(plan, m, g)['k']['category'], A.VISUAL_REVIEW)   # exam-linked citation stays visible

    def test_course_without_past_exams_is_produced_with_label(self):
        from exam_mastery.chapters import _auto_resolution
        self.assertEqual(_auto_resolution({'code': 'ELIGIBILITY_NO_EXAM_EVIDENCE'}),
                         'AUTO_PRODUCED_NO_EXAM_EVIDENCE_EXAM_RELEVANCE_UNCONFIRMED')

    def test_real_fixture_courses_without_exams_clear(self):
        import tempfile
        from exam_mastery.chapters import dry_run, production_preflight_auto
        root = Path(__file__).parents[1] / 'fixtures'
        for course in ('mathematical_visual_demo', 'v4_courses/discrete_models', 'synthetic_course'):
            with tempfile.TemporaryDirectory() as td:
                _, plan, m, g, _ = dry_run(root / course, Path(td) / 'p', None)
                g = A.apply(plan, m, g)
                ids = [c['chapter_id'] for c in plan['chapters'] if g[c['chapter_id']]['status'] not in ('BLOCKED', 'REVIEW_REQUIRED')]
                pf = production_preflight_auto(plan, g, ids)
                self.assertEqual(pf['result'], 'AUTO_CLEARED', course)
                labels = {o['resolution'] for r in pf['chapters'].values() for o in r['auto_resolved']}
                self.assertIn('AUTO_PRODUCED_NO_EXAM_EVIDENCE_EXAM_RELEVANCE_UNCONFIRMED', labels)


class B7Contracts(unittest.TestCase):
    """Live run 2026-11-08: assessment returned solution_id null and points null; 38 valid solutions were refused."""
    def test_null_solution_id_is_assigned_and_solutions_match_by_item(self):
        from exam_mastery.production import validate_assessments, validate_solutions
        a = {'assessments': [{'item_id': 'a-01', 'kc_ids': ['k'], 'prompt': 'x', 'difficulty': 'guided', 'solution_id': None, 'points': None},
                             {'item_id': 'a-02', 'kc_ids': ['k'], 'prompt': 'y', 'difficulty': 'exam', 'solution_id': None, 'points': 6}]}
        validate_assessments(a)
        self.assertEqual([x['solution_id'] for x in a['assessments']], ['sol-a-01', 'sol-a-02'])
        sols = {'solutions': [{'solution_id': 's-02', 'item_id': 'a-02'}, {'solution_id': 's-01', 'item_id': 'a-01'}]}
        validate_solutions(sols, a['assessments'])
        self.assertEqual([x['solution_id'] for x in sols['solutions']], ['sol-a-02', 'sol-a-01'])
        from exam_mastery.common import ContractError
        for bad in ([{'item_id': 'a-01'}], [{'item_id': 'a-01'}, {'item_id': 'a-01'}], [{'item_id': 'a-01'}, {'item_id': 'zz'}]):
            with self.assertRaises(ContractError):
                validate_solutions({'solutions': bad}, a['assessments'])

    def test_exam_item_without_points_goes_to_revision_and_is_never_published(self):
        from exam_mastery.production import missing_exam_points, deterministic_findings
        items = [{'item_id': 'e%d' % i, 'difficulty': 'exam', 'points': p} for i, p in enumerate((None, 0, True, '5', 4))]
        self.assertEqual(missing_exam_points(items), ['e0', 'e1', 'e2', 'e3'])
        f = deterministic_findings([], items)
        self.assertEqual([(x['code'], x['severity']) for x in f], [('EXAM_POINTS_MISSING', 'major')])
        import tempfile
        from exam_mastery.chapter_publish import publish_chapter
        from exam_mastery.common import ContractError
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / 'content_ast.json').write_text(json.dumps({'assessments': items}))
            with self.assertRaisesRegex(ContractError, 'MOCK_EXAM_POINTS_MISSING'):
                publish_chapter(td, {'elements': [], 'sources': []})

    def test_live_run_solutions_now_validate(self):
        run = Path.home() / 'Developer/Exam_Mastery_Studio/runs_v0_5_1_p0_dev/course-fe494a74afef/ch-20261108T162621Z-a651792c/chapters/ch-cf1411d6b23210'
        if not (run / 'chapter_solutions.invalid-1-0.json').exists():
            self.skipTest('private live run not available')
        from exam_mastery.production import validate_solutions
        items = json.loads((run / 'chapter_assessment.json').read_text())['assessments']
        for a in items: a['solution_id'] = 'sol-' + a['item_id']
        sols = json.loads((run / 'chapter_solutions.invalid-1-0.json').read_text())
        validate_solutions(sols, items)
        self.assertEqual(len(sols['solutions']), 38)

class B7Rendering(unittest.TestCase):
    def test_string_constraints_are_not_split_into_characters(self):
        from exam_mastery.chapter_publish import _as_list
        self.assertEqual(_as_list('Use only listed labels'), ['Use only listed labels'])
        self.assertEqual(_as_list(['a', 'b']), ['a', 'b']); self.assertEqual(_as_list(None), [])


def slide(page, eid, text):
    return {'element_id': eid, 'locator': f'src-x/page-{page}#heading-{eid}', 'source': 'deck.pdf', 'kind': 'heading', 'status': 'ok', 'text': text}


MATURE = [slide(14, 'a14', 'Sales contract A \n150 k€\nMature Lead B \n200 k€'), slide(14, 'c14', 'New Lead C  \n 100 k€'),
          slide(14, 's14', 'Sum  \n \n  350 k€'), slide(14, 'k14', 'Bank loan \n60 k€\nSupplier 1 \n \n50 k€\nTax payments \n115 k€'),
          slide(14, 't14', 'Sum  \n \n225 k€'),
          slide(15, 'a15', 'Sales contract A \n150 k€\nMature Lead  B \n200 k€'), slide(15, 'c15', 'New Lead C  \n 100 k€'),
          slide(15, 's15', 'Sum  \n \n  150 k€'), slide(15, 'k15', 'Bank loan \n60 k€\nSupplier 1 \n \n50 k€\nTax payments \n115 k€'),
          slide(15, 't15', 'Sum  \n \n225 k€')]


class B71MultiSlideExample(unittest.TestCase):
    """Live run 2026-11-08: text-only scope saw only the 'after' slide; the author wrote 150 + 100 = 250 k€ (A + C)."""
    def block(self, *steps):
        return {'block_id': 'b', 'source_refs': ['a15', 's15'], 'steps': [{'statement': s} for s in steps]}

    def test_recombined_total_is_rejected(self):
        from exam_mastery.examples import check_block
        r = check_block(self.block('\\[150+100=250\\;\\text{k€}.\\]'), MATURE)
        self.assertEqual([x[0] for x in r], ['FAIL'])

    def test_source_reading_passes(self):
        from exam_mastery.examples import check_block
        r = check_block(self.block('150 + 200 = 350 k€ before the cancellation', '60+50+115=225 k€ creditors'), MATURE)
        self.assertEqual([x[0] for x in r], ['PASS', 'PASS'])

    def test_supplier_label_digits_are_not_values(self):
        from exam_mastery.examples import parse
        self.assertEqual(parse(MATURE[3])[1], ('Supplier 1', 50.0, False))

    def test_continuation_slide_is_read_with_the_anchor(self):
        from exam_mastery.examples import continuation_elements
        self.assertIn('s14', {e['element_id'] for e in continuation_elements(['a15'], MATURE)})

    def test_finding_goes_to_revision(self):
        from exam_mastery.production import deterministic_findings
        f = deterministic_findings([{'check': 'EXAMPLE_TOTAL_CONSISTENCY', 'status': 'FAIL', 'object_id': 'b', 'detail': 'x'}], [])
        self.assertEqual(f[0]['code'], 'EXAMPLE_TOTAL_CONSISTENCY')

    def test_live_draft_is_rejected_without_false_alarms(self):
        base = Path.home() / 'Developer/Exam_Mastery_Studio/runs_v0_5_1_p0_dev/course-fe494a74afef'
        live = base / 'ch-20261108T162621Z-a651792c/chapters/ch-cf1411d6b23210'
        if not (live / 'chapter_author.json').exists():
            self.skipTest('private live run not available')
        from exam_mastery.examples import check_block
        ctx = json.loads((live / 'chapter_context.json').read_text())
        a = json.loads((live / 'chapter_author.json').read_text())
        b = next(x for x in a['blocks'] if x['block_id'] == 'b-cancelled-lead')
        self.assertIn('FAIL', [x[0] for x in check_block(b, ctx['source_elements'])])
        others = [x[0] for y in a['blocks'] if y['block_id'] != 'b-cancelled-lead' for x in check_block(y, ctx['source_elements'])]
        self.assertNotIn('FAIL', others)


class B71RepairBudget(unittest.TestCase):
    """A contract repair is a counted request: it can never exceed max_requests."""
    def test_repairs_count_against_max_requests(self):
        import tempfile
        from exam_mastery.budget import ResourceBudget, BudgetBlocked
        cfg = {'approval_id': 'r', 'max_requests': 3, 'max_retries': 2, 'max_wall_seconds': 600, 'max_input_tokens': 10 ** 6,
               'max_output_tokens': 10 ** 6, 'max_input_tokens_per_call': 10 ** 5, 'max_output_tokens_per_call': 10 ** 4,
               'input_overhead_tokens_per_call': 0, 'image_input_tokens': 0}
        with tempfile.TemporaryDirectory() as td:
            b = ResourceBudget(cfg, Path(td))
            b.reserve('chapter_solutions', 'p'); b.reserve('chapter_solutions', 'p')   # call + repair
            b.reserve('chapter_semantic_review', 'p')
            with self.assertRaises(BudgetBlocked):
                b.reserve('chapter_semantic_review', 'p')        # repair allowed by max_retries, refused by max_requests
            st = json.loads(next(Path(td).glob('*.ledger.json')).read_text())
            self.assertEqual((st['requests'], st['retries']), (3, 1))

    def test_product_policy_keeps_zero_http_retries_and_counts_repairs(self):
        from exam_mastery.product import policy_budget, DEFAULT_POLICY
        cfg = {'provider': 'codex', 'model': 'm', 'usage_policy': dict(DEFAULT_POLICY), 'data_transfer_consent': {'accepted': True}}
        b = policy_budget(cfg)
        self.assertEqual(b['max_retries'], 2)
        self.assertEqual(b['max_requests'], DEFAULT_POLICY['max_requests_per_run'])   # repairs live inside this number


class B71Recovery(unittest.TestCase):
    def test_recorded_provider_serves_once_and_stops_offline(self):
        from exam_mastery.recover import RecordedProvider, LiveCallRequired
        p = RecordedProvider({'chapter_author': ({'x': 1}, {'sha256': 'h'})})
        self.assertEqual(p.ask('chapter_author', 'p', None), {'x': 1})
        with self.assertRaises(LiveCallRequired):    # a repair is never served the same recorded answer again
            p.ask('chapter_author', 'p', None)
        with self.assertRaises(LiveCallRequired):
            p.ask('chapter_semantic_review', 'p', None)
        self.assertFalse(p.external); self.assertIsNone(p.budget)

    def test_correction_only_for_a_failing_block_and_must_pass(self):
        from exam_mastery.recover import apply_corrections
        from exam_mastery.common import ContractError
        ctx = {'allowed_source_refs': [e['element_id'] for e in MATURE], 'source_elements': MATURE}
        bad = {'block_id': 'b', 'source_refs': ['a15', 's15'], 'steps': [{'statement': '150+100=250 k€'}]}
        good = {'source_refs': ['a14', 's14'], 'steps': [{'statement': '150+200=350 k€'}]}
        new, rec = apply_corrections({'blocks': [bad]}, [{'block_id': 'b', 'reason': 'r', 'replacement': good}], ctx)
        self.assertEqual(rec[0]['kind'], 'ENGINE_SOURCE_CORRECTION'); self.assertFalse(rec[0]['reviewed'])
        self.assertEqual(new['blocks'][0]['steps'][0]['statement'], '150+200=350 k€')
        with self.assertRaises(ContractError):        # nothing to correct
            apply_corrections({'blocks': [dict(good, block_id='b')]}, [{'block_id': 'b', 'reason': 'r', 'replacement': good}], ctx)
        with self.assertRaises(ContractError):        # foreign source
            apply_corrections({'blocks': [bad]}, [{'block_id': 'b', 'reason': 'r', 'replacement': dict(good, source_refs=['zz'])}], ctx)

    def test_real_offline_recovery_reaches_semantic_review(self):
        run = Path.home() / 'Developer/Exam_Mastery_Studio/runs_v0_5_1_p0_dev/course-fe494a74afef/ch-20261108T162621Z-a651792c/chapters/ch-cf1411d6b23210'
        corr = Path.home() / 'Developer/Exam_Mastery_Studio/review_exports/funding_b7_recovery/corrections.json'
        if not (run / 'chapter_author.json').exists() or not corr.exists():
            self.skipTest('private live run not available')
        import tempfile
        from exam_mastery.recover import recover
        before = {p.name: p.stat().st_mtime_ns for p in run.iterdir()}
        with tempfile.TemporaryDirectory() as td:
            r = recover(run, Path(td) / 'rec', json.loads(corr.read_text())['corrections'])
        self.assertEqual((r['result'], r['next_role']), ('STOPPED_BEFORE_LIVE_CALL', 'chapter_semantic_review'))
        self.assertEqual(r['served_from_record'], ['chapter_author', 'chapter_assessment', 'chapter_solutions'])
        self.assertEqual([g['result'] for g in r['stage_gates']], ['CONTINUE', 'CONTINUE'])
        self.assertEqual({p.name: p.stat().st_mtime_ns for p in run.iterdir()}, before)   # original run untouched


class B72PublishRules(unittest.TestCase):
    def test_new_points_are_labelled_never_official(self):
        from exam_mastery.production import label_points
        a = label_points([{'item_id': 'x', 'points': 6, 'exam_link_item_ids': ['q1']}, {'item_id': 'y', 'points': 4, 'exam_link_item_ids': ['q2']},
                          {'item_id': 'z', 'points': None}], [{'item_id': 'q1', 'points': None}, {'item_id': 'q2', 'points': 4}])
        self.assertEqual([i.get('points_basis') for i in a], ['NEW_DESIGN_NOT_OFFICIAL', 'OFFICIAL_EXAM_POINTS', None])

    def test_evidence_gap_item_is_not_in_mock_exam_and_needs_no_points(self):
        from exam_mastery.production import evidence_gap_items, missing_exam_points, deterministic_findings
        from exam_mastery.chapter_publish import model, mock_exam_items, item_note
        items = [{'item_id': 'a-17', 'difficulty': 'exam', 'points': None, 'exam_link_item_ids': ['q12'], 'prompt': 'p'},
                 {'item_id': 'a-35', 'difficulty': 'exam', 'points': 6, 'points_basis': 'NEW_DESIGN_NOT_OFFICIAL', 'exam_link_item_ids': ['q9'], 'prompt': 'p'}]
        answers = [{'item_id': 'q12', 'status': 'SOURCE_MISSING'}, {'item_id': 'q9', 'status': 'ANSWERED_FROM_SOURCE'}]
        self.assertEqual(evidence_gap_items(items, answers), ['a-17'])
        self.assertEqual(missing_exam_points(items, answers), [])
        self.assertIn('EXAM_ITEM_EVIDENCE_GAP', [f['code'] for f in deterministic_findings([], items, answers)])
        m = model({'assessments': items, 'exam_answers': answers}, {'elements': [], 'sources': []})
        self.assertEqual([i['id'] for i in mock_exam_items(m)], ['a-35'])
        self.assertIn('Evidenzlücke', item_note(next(i for i in m['items'] if i['id'] == 'a-17')))
        self.assertIn('neu entworfene Bewertung', item_note(next(i for i in m['items'] if i['id'] == 'a-35')))


class B73PatchRevision(unittest.TestCase):
    def test_changes_are_merged_by_id_and_cannot_add_or_drop(self):
        from exam_mastery.production import merge_revision
        from exam_mastery.common import ContractError
        prod = {'blocks': [{'block_id': 'b1', 'body': 'old'}, {'block_id': 'b2', 'body': 'keep'}],
                'assessments': [{'item_id': 'a-35', 'points': None}], 'solutions': [{'item_id': 'a-35', 'answer': 'x'}], 'figures': []}
        m = merge_revision(prod, {'changes': {'blocks': [{'block_id': 'b1', 'body': 'new'}], 'assessments': [{'item_id': 'a-35', 'points': 6}]}})
        self.assertEqual([b['body'] for b in m['blocks']], ['new', 'keep'])
        self.assertEqual(m['assessments'][0]['points'], 6); self.assertIsNone(prod['assessments'][0]['points'])
        for bad in ({'blocks': [{'block_id': 'b9'}]}, {'notes': []}, {'solutions': [{'answer': 'no id'}]}):
            with self.assertRaises(ContractError):
                merge_revision(prod, {'changes': bad})
        with self.assertRaises(ContractError):
            merge_revision(prod, {'blocks': []})          # old full-rewrite format is refused


class B74Fixes(unittest.TestCase):
    def test_german_operator_wiedergeben_is_recall(self):
        from exam_mastery.curriculum import operations_in
        self.assertEqual(operations_in('Geben Sie die fünf Exit-Ereignisse mit ihren Kurzbeschreibungen wieder.'), ['RECALL'])
        self.assertEqual(operations_in('Die Begriffe wiedergeben.'), ['RECALL'])

    def test_explanation_is_a_known_block_kind(self):
        from exam_mastery.validate import BLOCK_KINDS
        from exam_mastery.chapter_publish import KIND_LABEL
        self.assertIn('EXPLANATION', BLOCK_KINDS)
        self.assertTrue(set(KIND_LABEL) - {'CASE'} <= BLOCK_KINDS)   # everything the publisher renders is validated

    def test_recover_never_publishes_a_failed_chapter(self):
        src = (Path(__file__).parents[1] / 'exam_mastery' / 'recover.py').read_text()
        self.assertIn("r.get('ast_status') != 'DRAFT_TECHNICAL_PASS_PENDING_REVIEW'", src)


class B74Delivery(unittest.TestCase):
    def test_synthetic_chapter_gets_separate_files_and_delivery_folder(self):
        import sys, tempfile
        sys.path.insert(0, str(Path(__file__).parent))
        from test_b6_5_chapter_publish import synthetic_run
        from exam_mastery.product import deliver_chapter
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            out, st = synthetic_run('ml', Path(td))
            ch = next((c for c in sorted((out / 'chapters').iterdir()) if (c / 'publish' / 'artifacts' / '1_Lehrbuch.pdf').exists()), None)
            self.assertIsNotNone(ch, {'failures': st.get('chapter_failures'), 'chapters': st.get('chapters')})   # show the publish error, not a bare StopIteration
            art = ch / 'publish' / 'artifacts'
            for f in ('1_Lehrbuch.pdf', '2_Arbeitsbuch.pdf', '3_Musterloesungen.pdf'):
                doc = pymupdf.open(art / f)
                self.assertGreater(doc.page_count, 1, f)
                self.assertIn(f'1 / {doc.page_count - 1}', doc[1].get_text(), f)    # own numbering after the cover
            d = deliver_chapter(ch, Path(td) / 'LERNMATERIAL' / 'x', label='ML')
            names = {p.name for p in d.iterdir()}
            self.assertTrue({'LIES_MICH.md', 'quality_dossier.json', '1_Lehrbuch.pdf', 'kapitel.html', 'assets'} <= names, names)
            self.assertIn('NICHT unabhängig validiert', (d / 'LIES_MICH.md').read_text())


if __name__ == '__main__':
    unittest.main()
