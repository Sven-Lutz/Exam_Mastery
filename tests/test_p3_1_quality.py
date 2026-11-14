"""P3.1 acceptance: content quality gates on ContentAST. Offline; random roots; no provider process."""
import contextlib, copy, io, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
import p3_1_fixtures as Q
from exam_mastery.chapters import dry_run
from exam_mastery.quality_gates import quality_report, validate_gate_report, GATES
from exam_mastery.runtime import run_chapters


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def ref(self, kind):
        root = Q.course(F.random_root(self.d / ('src-' + kind)), kind)
        _, plan, m, gates, _ = dry_run(root, self.d / ('out-' + kind))
        c = plan['chapters'][0]
        return Q.positive_ast(kind, plan, m), c, plan, m

    def codes(self, rep, statuses=('FAIL', 'BLOCKED')):
        return {(f['gate_id'], f['object_id']) for f in rep['findings'] if f['status'] in statuses}

    def gate_fail(self, rep, gate, obj=None):
        return any(f['gate_id'] == gate and f['status'] in ('FAIL', 'BLOCKED') and (obj is None or f['object_id'] == obj)
                   for f in rep['findings'])


class OriginalFixture(Base):
    def test_p3_synthetic_fixture_is_technical_go_but_academic_no_go(self):
        root = F.make('math', str(self.d / 'r'))
        with contextlib.redirect_stdout(io.StringIO()):
            out, status = run_chapters(root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs')
        plan = json.loads((out / 'plan' / 'curriculum.json').read_text())
        c = next(x for x in plan['chapters'] if 'Ausgleich' in x['title'])
        a = json.loads((out / 'chapters' / c['chapter_id'] / 'content_ast.json').read_text())
        q = a['quality_report']
        self.assertEqual(a['status'], 'DRAFT_TECHNICAL_PASS_PENDING_REVIEW')       # data model still valid (P3 unchanged)
        self.assertEqual(q['technical_status'], 'TECHNICAL_GO')
        self.assertEqual(q['academic_status'], 'ACADEMIC_NO_GO'); self.assertFalse(q['content_go'] or q['release_go'])
        self.assertTrue(q['test_only']); self.assertEqual(validate_gate_report(q), [])
        self.assertEqual(a['academic_status'], 'ACADEMIC_NO_GO')
        # the weaknesses found in the independent review are reported, per item
        res = {r['item_id']: r for r in q['assessment_quality']}
        self.assertEqual(len(res), 10); self.assertTrue(all(r['status'] == 'BLOCKED' for r in res.values()))
        self.assertTrue(all(r['checks']['target'] == 'BLOCKED' for r in res.values()))   # "den zentralen Begriff" etc.
        self.assertTrue(all(r['checks']['evidence'] == 'BLOCKED' for r in res.values()))
        self.assertEqual(res['q-0-main']['checks']['transfer'], 'FAIL')                   # DEFINE item labelled transfer
        self.assertTrue(self.gate_fail(q, 'G5.FIGURES'))                                   # reused image without caption/review
        self.assertIn(q['gates']['G4.PROOF_VALIDITY']['status'], ('NOT_TESTED', 'PENDING'))
        self.assertEqual(q['gates']['G4.DIMENSIONS']['status'], 'PASS')                    # consistent shapes ...
        self.assertTrue(any('not a proof' in f['reason'] for f in q['findings'] if f['gate_id'] == 'G4.DIMENSIONS'))  # ... prove nothing
        self.assertTrue((out / 'chapters' / c['chapter_id'] / 'quality_gate_report.json').exists())
        self.assertTrue(all(r['reviewer_kind'] == 'TEST_FIXTURE' for r in a['reviews']))


class Positive(Base):
    def test_reference_examples_pass_machine_checks_but_stay_pending(self):
        for kind in ('math', 'law', 'ml'):
            a, c, plan, m = self.ref(kind)
            q = quality_report(a, c, plan, m)
            self.assertEqual(validate_gate_report(q), [], kind)
            self.assertEqual(q['machine_quality_status'], 'MACHINE_CHECKS_PASSED', (kind, [f for f in q['findings'] if f['status'] in ('FAIL', 'BLOCKED')]))
            self.assertEqual(q['technical_status'], 'TECHNICAL_GO', kind)
            self.assertEqual(q['academic_status'], 'ACADEMIC_RELEASE_NOT_TESTED', kind)
            self.assertEqual(q['semantic_status'], 'SEMANTIC_PENDING', kind)
            self.assertFalse(q['content_go'] or q['release_go'])
            self.assertTrue(all(r['status'] == 'PENDING_SEMANTIC_REVIEW' for r in q['assessment_quality']), kind)
            self.assertEqual(set(q['gates']), set(GATES))
        a, c, plan, m = self.ref('math')
        q = quality_report(a, c, plan, m)
        self.assertEqual(q['gates']['G4.NUMERIC']['status'], 'PASS')
        self.assertEqual(q['gates']['G5.NOTATION']['status'], 'PENDING')       # r conflict stays visible
        self.assertEqual(q['gates']['G4.DOMAIN_LAW']['status'], 'NOT_APPLICABLE')
        a, c, plan, m = self.ref('law'); q = quality_report(a, c, plan, m)
        self.assertEqual(q['gates']['G4.DOMAIN_LAW']['status'], 'PENDING')      # legal status NOT_TESTED, never PASS
        a, c, plan, m = self.ref('ml'); q = quality_report(a, c, plan, m)
        self.assertEqual(q['gates']['G4.DOMAIN_COMPUTING']['status'], 'PENDING')  # tests stated, code not executed
        self.assertTrue(any(f['gate_id'] == 'G4.DOMAIN_COMPUTING' and f['status'] == 'NOT_TESTED' for f in q['findings']))

    def test_author_created_item_without_source_refs_is_allowed_with_basis(self):
        a, c, plan, m = self.ref('math')
        self.assertTrue(all(x['source_refs'] == [] and x['provenance'] == 'AUTHOR_CREATED' for x in a['assessments']))
        q = quality_report(a, c, plan, m)
        self.assertTrue(all(r['checks']['evidence'] == 'PENDING' for r in q['assessment_quality']))
        b = copy.deepcopy(a); b['assessments'][0]['provenance'] = 'COURSE_SOURCE'
        self.assertTrue(self.gate_fail(quality_report(b, c, plan, m), 'G2.EVIDENCE_CHAIN', 'q-explain'))


class Negative(Base):
    def run_case(self, case):
        a, c, plan, m = self.ref('math')
        q = quality_report(Q.negative(a, case, m), c, plan, m)
        self.assertEqual(validate_gate_report(q), [], case)
        self.assertEqual(q['academic_status'], 'ACADEMIC_NO_GO', case)
        return q

    def test_a_unsolvable_item(self):
        q = self.run_case('a_unsolvable')
        self.assertTrue(self.gate_fail(q, 'G1.ITEM_TARGET', 'q-calc')); self.assertTrue(self.gate_fail(q, 'G1.ITEM_DATA', 'q-calc'))
        a, c, plan, m = self.ref('math')
        for prompt in ('Nennen Sie den zentralen Begriff.', 'Beweisen Sie die Aussage für den angegebenen Fall vollständig.'):
            b = copy.deepcopy(a); b['assessments'][1].update(prompt=prompt, target=None)
            self.assertTrue(self.gate_fail(quality_report(b, c, plan, m), 'G1.ITEM_TARGET', 'q-derive'), prompt)

    def test_b_derive_not_by_define(self):
        q = self.run_case('b_derive_by_define')
        self.assertTrue(self.gate_fail(q, 'G1.ITEM_OPERATION', 'q-derive'))
        kc = next(k for k in q['assessment_quality'] if k['item_id'] == 'q-derive')['kc_ids'][0]
        self.assertTrue(self.gate_fail(q, 'G1.ITEM_OPERATION', kc))

    def test_c_false_transfer_label(self):
        self.assertTrue(self.gate_fail(self.run_case('c_transfer_label'), 'G1.ITEM_TRANSFER', 'q-explain'))

    def test_d_motivation_only_link(self):
        q = self.run_case('d_motivation_only')
        self.assertTrue(all(r['checks']['evidence'] == 'BLOCKED' for r in q['assessment_quality']))

    def test_e_invented_anchor(self):
        q = self.run_case('e_invented_anchor')
        self.assertTrue(self.gate_fail(q, 'G0.STRUCTURE', 'b-der'))

    def test_f_unresolvable_essential_image(self):
        self.assertTrue(self.gate_fail(self.run_case('f_essential_image'), 'G5.FIGURES', 'fig-res'))

    def test_g_conflicting_notation_not_averaged(self):
        q = self.run_case('g_notation')
        self.assertTrue(any(f['gate_id'] == 'G5.NOTATION' and f['status'] == 'FAIL' for f in q['findings']))

    def test_h_fake_model_self_release(self):
        q = self.run_case('h_self_release')
        self.assertTrue(self.gate_fail(q, 'G3.STATUS_LABELS', 'academic_status'))
        self.assertTrue(self.gate_fail(q, 'G3.REVIEW_RECORDS', 'b-der'))       # MODEL_REVIEWED without record
        self.assertTrue(any(f['gate_id'] == 'G3.STATUS_LABELS' and 'ACADEMIC_VERIFIED' in f['reason'] for f in q['findings']))
        self.assertTrue(q['test_only']); self.assertFalse(q['release_go'])

    def test_i_incomplete_or_dishonest_gate_report_rejected(self):
        a, c, plan, m = self.ref('math')
        q = quality_report(Q.negative(a, 'a_unsolvable', m), c, plan, m)
        bad = copy.deepcopy(q); del bad['gates']['G4.NUMERIC']
        self.assertIn('gate G4.NUMERIC missing', validate_gate_report(bad))
        bad = copy.deepcopy(q); bad['machine_quality_status'] = 'MACHINE_CHECKS_PASSED'; bad['academic_status'] = 'ACADEMIC_RELEASE_NOT_TESTED'
        self.assertTrue(any('swallowed' in p for p in validate_gate_report(bad)))
        bad = copy.deepcopy(q); bad['gates']['G1.ITEM_TARGET']['status'] = 'PASS'
        self.assertTrue(any('hides' in p for p in validate_gate_report(bad)))
        bad = copy.deepcopy(q); bad['gates']['G4.PROOF_VALIDITY'] = {'status': 'PASS', 'reason': 'x', 'checks_executed': []}
        self.assertTrue(any('PASS without executed checks' in p for p in validate_gate_report(bad)))
        bad = copy.deepcopy(q); bad['release_go'] = True
        self.assertTrue(any('content/release go' in p for p in validate_gate_report(bad)))

    def test_partial_source_blocks_only_affected_kc(self):
        a, c, plan, m = self.ref('math')
        by = {e['element_id']: e for e in m['elements']}
        weak = copy.deepcopy(m); fig = next(e for e in weak['elements'] if e['kind'] == 'figure')
        b = copy.deepcopy(a); b['blocks'][2]['source_refs'] = [fig['element_id']]   # derivation now rests only on an unavailable element
        q = quality_report(b, c, plan, weak)
        self.assertTrue(self.gate_fail(q, 'G5.SOURCE_FIDELITY', 'b-der'))
        self.assertFalse(self.gate_fail(q, 'G5.SOURCE_FIDELITY', 'b-ex'))   # calculation KC unaffected


if __name__ == '__main__':
    unittest.main()
