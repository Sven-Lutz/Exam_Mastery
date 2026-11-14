"""P2: course-wide competency/assessment/chapter planning with operation-true coverage."""
import json, shutil, socket, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
from exam_mastery.fidelity import inventory
from exam_mastery.curriculum import (compile_curriculum, SemanticDecisions, satisfied, operations_in, source_support)
from exam_mastery.source_schema import validate_curriculum
from exam_mastery.common import ContractError


def plan(kind, decisions=None, root=None):
    root = root or F.make(kind, tempfile.mkdtemp(prefix='p2-'))
    out = Path(tempfile.mkdtemp(prefix='p2out-'))
    m = inventory(root, out / 'inv')
    return root, m, compile_curriculum(m, out, decisions=decisions)


def kc(p, needle):
    return next(k for k in p['competencies'] if needle.lower() in k['statement'].lower())


def cov(p, k):
    return next(r for r in p['coverage'] if r['kc_id'] == k['kc_id'])


def item(p, label):
    return next(q for q in p['assessment_items'] if q['label'] == label)


class P2Curriculum(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.math = plan('math'); cls.law = plan('law'); cls.ml = plan('ml')

    def test_contracts_valid_and_no_provider_calls(self):
        for root, m, p in (self.math, self.law, self.ml):
            validate_curriculum(p, m)
            self.assertEqual(p['provider_calls'], 0)
            self.assertTrue(all(c['generation_plan']['provider_calls_in_p2'] == 0 for c in p['chapters']))
        with self.assertRaises(ContractError):
            compile_curriculum(self.math[1], provider=object())

    def test_offline_end_to_end_without_process_or_network(self):
        boom = AssertionError('forbidden side effect')
        with patch.object(subprocess, 'Popen', side_effect=boom), patch.object(socket, 'socket', side_effect=boom), \
                patch('exam_mastery.providers.Provider.ask', side_effect=boom, create=True):
            for kind in ('math', 'law', 'ml'):
                plan(kind)

    def test_derive_not_covered_by_name(self):
        root, m, p = self.math
        derive = kc(p, 'Leiten Sie die Normalengleichung')
        self.assertEqual(derive['operations'], ['DERIVE'])
        q1b = item(p, '1b'); self.assertEqual(q1b['actual_operations'], ['RECALL'])
        row = cov(p, derive)
        self.assertNotIn(q1b['item_id'], row['evidence_item_ids'])
        self.assertTrue(any(r['item_id'] == q1b['item_id'] and 'requires DERIVE' in r['reason'] for r in row['rejected_links']))
        self.assertIn(item(p, '1a')['item_id'], row['evidence_item_ids'])
        # Same course, but the only linked item is the naming task (asserted by a fixture decision):
        root2 = F.random_root(tempfile.mkdtemp()); shutil.rmtree(root2); shutil.copytree(root, root2)
        (root2 / 'Altklausur_2025.pdf').unlink()
        (root2 / 'Altklausur_2025.md').write_text('Altklausur\n\nAufgabe 1\nb) Nennen Sie die Variable, die bei der Ausgleichsrechnung minimiert wird. (1 P)\n')
        _, m2, p2 = plan('math', root=root2)
        nb = item(p2, '1b')
        d = SemanticDecisions([{'kind': 'link', 'subject_id': derive['kc_id'], 'value': [nb['item_id']],
                                'rationale': 'fixture claims coverage by ID link only', 'decided_by': 'fixture'}])
        p3 = compile_curriculum(m2, decisions=d)
        row = cov(p3, kc(p3, 'Leiten Sie die Normalengleichung'))
        self.assertEqual(row['status'], 'OPERATION_MISMATCH'); self.assertEqual(row['evidence_item_ids'], [])

    def test_prove_not_covered_by_multiple_choice_and_apply_needs_instance(self):
        root, m, p = self.math
        mc = item(p, '3'); self.assertEqual(mc['format'], 'multiple_choice')
        ok, why = satisfied('PROVE', ['PROVE'], {**mc, 'actual_operations': ['PROVE']})
        self.assertFalse(ok); self.assertIn('multiple-choice', why)
        prove = kc(p, 'Beweisen Sie die Eindeutigkeit')
        self.assertNotIn(mc['item_id'], cov(p, prove)['evidence_item_ids'])
        self.assertIn(item(p, '2')['item_id'], cov(p, prove)['evidence_item_ids'])
        ok, why = satisfied('APPLY', ['APPLY'], {'format': 'open', 'has_concrete_instance': False, 'norm_refs': []})
        self.assertFalse(ok); self.assertIn('concrete', why)
        self.assertTrue(item(p, '4')['has_concrete_instance']); self.assertFalse(item(p, '1a')['has_concrete_instance'])

    def test_legal_subsumption_requires_case_and_norm(self):
        root, m, p = self.law
        sub = kc(p, 'Subsumieren Sie'); self.assertEqual(sub['operations'], ['SUBSUME']); self.assertTrue(sub['official'])
        a, b = item(p, '1a'), item(p, '1b')
        self.assertIn('SUBSUME', a['actual_operations']); self.assertEqual(a['norm_refs'], ['§ 433 Abs. 2 BGB'])
        row = cov(p, sub)
        self.assertEqual(row['evidence_item_ids'], [a['item_id']])
        self.assertTrue(any(r['item_id'] == b['item_id'] for r in row['rejected_links']))
        ok, why = satisfied('SUBSUME', ['SUBSUME'], {'format': 'open', 'has_concrete_instance': True, 'norm_refs': []})
        self.assertFalse(ok); self.assertIn('norm', why)
        self.assertIn('LEGAL_NORM', p['chapters'][0]['requirements']['review_requirements'])
        self.assertEqual(a['solution_status'], 'SOLUTION_SOURCE_FOUND_UNVERIFIED')
        self.assertEqual(item(p, '2')['solution_status'], 'NO_SOLUTION_SOURCE')

    def test_exam_subquestions_points_and_operations(self):
        root, m, p = self.ml
        labels = {q['label']: q for q in p['assessment_items']}
        self.assertEqual(sorted(labels), ['1a', '1b', '1c', '1d'])
        self.assertEqual(labels['1a']['actual_operations'], ['DERIVE']); self.assertEqual(labels['1a']['points'], 4.0)
        self.assertEqual(labels['1b']['actual_operations'], ['IMPLEMENT'])
        self.assertEqual(labels['1c']['format'], 'multiple_choice')
        for q in labels.values():
            self.assertTrue(q['anchor_element_ids'])
        impl = kc(p, 'implement gradient descent')
        self.assertEqual(cov(p, impl)['evidence_item_ids'], [labels['1b']['item_id']])
        self.assertIn('EXECUTABLE_TESTS', next(c for c in p['chapters'] if impl['kc_id'] in c['kc_ids'])['requirements']['review_requirements'])

    def test_missing_evidence_is_explicit(self):
        root, m, p = self.math
        qr = kc(p, 'QR-Zerlegung')
        self.assertEqual(cov(p, qr)['status'], 'NO_ASSESSMENT_EVIDENCE')
        self.assertTrue(all(r['status'] != 'COVERED' for r in p['coverage']))
        self.assertTrue(all('PENDING' in r['status'] or r['status'] in ('OPERATION_MISMATCH', 'NO_ASSESSMENT_EVIDENCE') for r in p['coverage']))
        mse = kc(self.ml[2], 'Mean squared error')
        self.assertEqual(cov(self.ml[2], mse)['status'], 'OPERATION_MISMATCH')

    def test_ambiguous_single_term_link_is_not_evidence(self):
        root = F.make('math', tempfile.mkdtemp())
        exam = root / 'Altklausur_2025.pdf'; exam.unlink()
        (root / 'Klausur_kurz.md').write_text('Klausur\n\nAufgabe 1\nLeiten Sie die Normalengleichung her. (6 P)\n')
        _, m, p = plan('math', root=root)
        q = item(p, '1')
        self.assertEqual(q['link_status'], 'AMBIGUOUS_TOPIC_PENDING_SEMANTIC_DECISION')
        self.assertTrue(all(q['item_id'] not in r['evidence_item_ids'] for r in p['coverage']))

    def test_source_anchor_present_but_unrelated_is_not_supported(self):
        self.assertEqual(source_support('Leite die Normalengleichung her', []), 'UNVERIFIED')
        self.assertEqual(source_support('Leite die Normalengleichung der Ausgleichsrechnung her',
                                        ['Die Katze sitzt auf der Matte.']), 'SOURCE_EXISTS')
        self.assertEqual(source_support('Leite die Normalengleichung der Ausgleichsrechnung her',
                                        ['Normalengleichung der linearen Ausgleichsrechnung']), 'SOURCE_SUPPORT_LEXICAL')

    def test_blocked_when_source_text_layer_missing(self):
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        import io
        root = F.random_root(tempfile.mkdtemp())
        cv = canvas.Canvas(str(root / 'Vorlesung_Thermo.pdf'))
        t = cv.beginText(40, 760)
        for ln in ['Vorlesung Thermodynamik', 'Lernziele:', '- Leiten Sie den Wirkungsgrad des Carnot-Prozesses her.']:
            t.textLine(ln)
        cv.drawText(t); cv.showPage()
        cv.drawImage(ImageReader(io.BytesIO(F._png('gray', (200, 200)))), 50, 400, 200, 200); cv.showPage(); cv.save()
        _, m, p = plan('x', root=root)
        k = kc(p, 'Carnot')
        self.assertEqual(cov(p, k)['status'], 'BLOCKED_SOURCE_GAP'); self.assertIn('TEXT_LAYER_MISSING', cov(p, k)['blocking_source_gaps'])

    def test_notation_registry_and_conflicts(self):
        root, m, p = self.math
        reg = {n['symbol']: n for n in p['notation_registry']}
        self.assertEqual(reg['r']['status'], 'CONFLICT_REVIEW_REQUIRED')
        self.assertEqual(len({u['chapter_id'] for u in reg['r']['uses']}), 2)
        self.assertEqual(reg['A']['status'], 'CONSISTENT')
        self.assertIn('\\eta', {n['symbol'] for n in self.ml[2]['notation_registry']})

    def test_prerequisites_stated_inferred_and_chapter_order(self):
        root, m, p = self.math
        stated = [e for e in p['prerequisite_edges'] if e['basis'] == 'stated_prerequisite']
        self.assertTrue(stated and all(not e['inferred'] for e in stated))
        pos = {c['chapter_id']: c['position'] for c in p['chapters']}
        for c in p['chapters']:
            for d in c['narrative_dependencies']:
                self.assertLess(pos[d], pos[c['chapter_id']])
        qr = next(c for c in p['chapters'] if c['title'] == 'QR-Zerlegung')
        self.assertTrue(qr['narrative_dependencies'])
        inferred = [e for e in self.ml[2]['prerequisite_edges'] if e['basis'] == 'term_defined_earlier_used_later']
        self.assertTrue(inferred and all(e['inferred'] for e in inferred))

    def test_chapter_requirements_are_didactic_not_titles(self):
        root, m, p = self.math
        ch = next(c for c in p['chapters'] if c['title'] == 'Lineare Ausgleichsrechnung')
        r = ch['requirements']
        self.assertTrue(r['explanation_depth'].startswith('formal'))
        self.assertTrue({x['operation'] for x in r['proof_and_derivation_depth']} >= {'DERIVE', 'PROVE'})
        self.assertTrue(any(x['min_count'] >= 2 for x in r['worked_examples']))
        self.assertTrue(any(v['asset'] for v in r['visualizations']))
        self.assertTrue(any(v['source_status'] == 'unavailable' for v in r['visualizations']))
        self.assertTrue(all(len(x['stages']) >= 2 for x in r['exercise_progression']))
        self.assertIn('rubric', r['model_solutions']['form'])
        self.assertIn('SYMBOLIC_WITH_DOMAIN', r['review_requirements'])
        self.assertGreater(ch['exam_relevance']['points'], 0)
        self.assertEqual(ch['source_package']['role'], 'data_supply_only_not_a_planning_unit')
        gp = ch['generation_plan']
        self.assertEqual(gp['unit'], 'chapter'); self.assertFalse(gp['per_transport_unit_role_chain'])

    def test_chapters_independent_of_transport_units(self):
        from exam_mastery import corpus
        root, m, p = self.math
        counts = []
        for size in (300, 18000):
            out = Path(tempfile.mkdtemp())
            with patch.object(corpus, 'UNIT_CHARS', size):
                _, units = corpus.build(root, out, out / 'cache')
            counts.append(len(units))
        self.assertNotEqual(counts[0], counts[1])
        again = compile_curriculum(inventory(root, Path(tempfile.mkdtemp()) / 'i'))
        self.assertEqual([c['chapter_id'] for c in again['chapters']], [c['chapter_id'] for c in p['chapters']])

    def test_stable_ids_across_random_roots_and_renamed_files(self):
        root, m, p = self.law
        other = F.random_root(tempfile.mkdtemp()); shutil.rmtree(other); shutil.copytree(root, other)
        (other / 'Vorlesung_Kaufrecht.docx').rename(other / 'Vorlesung_00_Kaufrecht.docx')
        _, m2, p2 = plan('law', root=other)
        self.assertEqual({k['kc_id'] for k in p['competencies']}, {k['kc_id'] for k in p2['competencies']})
        self.assertEqual({c['chapter_id'] for c in p['chapters']}, {c['chapter_id'] for c in p2['chapters']})
        rep = compile_curriculum(m)
        self.assertEqual(json.dumps(rep, sort_keys=True), json.dumps(compile_curriculum(m), sort_keys=True))

    def test_subject_adaptive_profile_without_configuration(self):
        self.assertIn('formal_mathematics', self.math[2]['domain_profile']['active_profiles'])
        self.assertIn('law', self.law[2]['domain_profile']['active_profiles'])
        self.assertIn('computing', self.ml[2]['domain_profile']['active_profiles'])
        self.assertNotIn('law', self.math[2]['domain_profile']['active_profiles'])

    def test_semantic_decision_contract_validation(self):
        root, m, p = self.math
        eids = {e['element_id'] for e in m['elements']}
        for bad in ({'kind': 'link', 'subject_id': 'kc-x', 'value': [], 'rationale': ''},
                    {'kind': 'operation', 'subject_id': 'kc-x', 'value': ['GUESS'], 'rationale': 'r'},
                    {'kind': 'link', 'subject_id': 'kc-x', 'value': [], 'rationale': 'r', 'decided_by': 'model'},
                    {'kind': 'link', 'subject_id': 'kc-x', 'value': [], 'rationale': 'r', 'evidence_element_ids': ['el-nope']}):
            with self.assertRaises(ContractError):
                SemanticDecisions([bad]).validate(eids)
        k = kc(p, 'Definition: Residuum')
        d = SemanticDecisions([{'kind': 'operation', 'subject_id': k['kc_id'], 'value': ['EXPLAIN'], 'rationale': 'fixture', 'decided_by': 'fixture'}])
        p2 = compile_curriculum(m, decisions=d)
        self.assertEqual(kc(p2, 'Definition: Residuum')['operation_basis'], 'semantic_decision:fixture')

    def test_operation_lexicon_examples(self):
        self.assertEqual(operations_in('Nennen Sie die Variable.'), ['RECALL'])
        self.assertEqual(operations_in('Leiten Sie die Formel her.'), ['DERIVE'])
        self.assertEqual(operations_in('Zeigen Sie, dass f stetig ist.'), ['PROVE'])
        self.assertEqual(operations_in('Hat V gegen K einen Anspruch aus § 433 BGB?'), ['SUBSUME'])
        self.assertEqual(operations_in('Implement the function in Python.'), ['IMPLEMENT'])


if __name__ == '__main__':
    unittest.main()
