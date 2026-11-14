"""B6.4: one content-bound pilot-scope signature for an explicit set of decisions + page reviews, and owner operation
decisions on assessment items (Recall questions never evidence EXPLAIN competencies). Offline; reviewer 'u1' is a
test fixture, never a real person."""
import copy, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from test_b6_review_decisions import HUMAN, MODEL, APPROVE, CID
from test_b6_1_chapter_page_gate import manifest, plan, gates, overlay, pr, excl, dset, open_codes, OV
from exam_mastery import review_decisions as D
from exam_mastery.chapters import production_preflight
from exam_mastery.curriculum import SemanticDecisions, compile_curriculum
from exam_mastery.fidelity import inventory
import p1p2_fixtures as F

MEMBERS = ['x1', 'x2', 'x3']


def scope_data(approval=APPROVE, members=MEMBERS, pages=('p6',), **kw):
    d, _ = dset(pr(pilot_scope_approval=None), decisions=[dict(excl(k, i), pilot_scope_approval=None) for k, i in
                                                          zip(('kc-vis', 'kc-nb', 'kc-law'), MEMBERS)], **kw)
    d['pilot_scope_set_approval'] = {'set_id': 'S1', 'decision_ids': list(members), 'page_review_ids': list(pages),
                                     'statement': 'experimental pilot only',
                                     'pilot_scope_approval': dict(approval) if approval else None}
    return d


def sign_set(d, p=None):
    d = copy.deepcopy(d)
    ap = d['pilot_scope_set_approval']['pilot_scope_approval']
    if ap and ap.get('approved') is True:
        ap['approved_content_sha256'] = D.content_hashes(d, p or plan())['scope_set']
    return d


def run(d, p=None):
    p = p or plan()
    ev = D.evaluate((d, 'f' * 64), manifest(), p, gates(), overlay())
    g = D.apply(gates(), ev)
    return ev, g, production_preflight(p, g, [CID])['chapters'][CID]


def codes(ev):
    return {e['code'] for r in ev['rejected'] + ev['page_reviews']['rejected'] for e in r['errors']}


class ScopeSet(unittest.TestCase):
    def test_01_one_signature_clears_pilot_scope_but_never_verifies(self):
        ev, g, pf = run(sign_set(scope_data()))
        self.assertEqual(codes(ev), set())
        self.assertEqual(pf['status'], 'PILOT_SCOPE_CLEARED_EXPERIMENTAL', pf['open'])
        self.assertEqual(ev['counts']['source_claim_human_verified'], 0)          # scope approval is not verification
        self.assertTrue(all(a['approved_via_bundle'] == 'S1' for a in ev['accepted']))
        self.assertEqual(ev['page_reviews']['accepted'][0]['approved_via_scope_set'], 'S1')
        self.assertFalse(ev['page_reviews']['accepted'][0]['source_claim_human_verified'])
        self.assertIn('PAGE_TRANSCRIPTION_UNCERTAIN', ev['page_reviews']['accepted'][0]['restrictions'])
        self.assertEqual(pf['academic_release'], 'NOT_TESTED')

    def test_02_unsigned_or_unbound_set_approves_nothing(self):
        ev, _, pf = run(scope_data(approval=None))
        self.assertEqual(pf['status'], 'PILOT_BLOCKED'); self.assertEqual(ev['counts']['effective_unlocks'], 0)
        ev, _, pf = run(scope_data())                                            # approved=True but no content hash
        self.assertIn('APPROVAL_NOT_CONTENT_BOUND', codes(ev)); self.assertEqual(pf['status'], 'PILOT_BLOCKED')

    def test_03_any_member_change_invalidates_the_whole_set(self):
        d = sign_set(scope_data())
        for mutate in (lambda x: x['decisions'][1].update(reason='another reason'),
                       lambda x: x['page_reviews'][0].update(uncertainty_statement='nothing is uncertain'),
                       lambda x: x['pilot_scope_set_approval']['decision_ids'].pop(),
                       lambda x: x.update(overlay_sha256='1' * 64)):
            x = copy.deepcopy(d); mutate(x)
            ev, _, pf = run(x)
            self.assertIn('SCOPE_SET_CONTENT_CHANGED', codes(ev)); self.assertEqual(pf['status'], 'PILOT_BLOCKED')

    def test_04_double_unknown_invalid_and_non_human_are_refused(self):
        d = scope_data(); d['decisions'][0]['pilot_scope_approval'] = dict(APPROVE)
        self.assertIn('DOUBLE_APPROVAL', codes(run(sign_set(d))[0]))
        d = scope_data(); d['bundle_approvals'] = [{'bundle_id': 'B', 'decision_ids': ['x1'], 'pilot_scope_approval': None}]
        self.assertIn('DOUBLE_APPROVAL', codes(run(sign_set(d))[0]))
        self.assertIn('SCOPE_SET_UNKNOWN_MEMBER', codes(run(sign_set(scope_data(members=['x1', 'nope'])))[0]))
        d = scope_data(); d['pilot_scope_set_approval']['source_claim_human_verification'] = {'verified': True}
        self.assertIn('INVALID_SCOPE_SET', codes(run(sign_set(d))[0]))             # the set cannot verify sources
        self.assertIn('INVALID_SCOPE_SET', codes(run(sign_set(scope_data(members=['x1', 'x1'])))[0]))
        ev, _, pf = run(sign_set(scope_data(approval=dict(APPROVE, approver_id='m1'))))
        self.assertIn('APPROVER_NOT_HUMAN', codes(ev)); self.assertEqual(pf['status'], 'PILOT_BLOCKED')

    def test_05_partial_set_leaves_the_rest_open(self):
        ev, _, pf = run(sign_set(scope_data(members=['x1', 'x2'])))
        self.assertEqual(codes(ev), set()); self.assertEqual(pf['status'], 'PILOT_BLOCKED')
        self.assertEqual(ev['counts']['unconfirmed'], 1)

    def test_06_set_hash_binds_question_operations_and_coverage(self):
        p = plan(); p['chapters'][0]['exam_relevance'] = {'linked_item_ids': ['q1']}
        p['assessment_items'] = [{'item_id': 'q1', 'actual_operations': ['RECALL'], 'operation_basis': 'semantic_decision:owner'}]
        p['coverage'] = [{'kc_id': 'kc-ok', 'status': 'OPERATION_MISMATCH', 'evidence_item_ids': [], 'recall_only_item_ids': ['q1']}]
        d = sign_set(scope_data(), p)
        self.assertEqual(codes(run(d, p)[0]), set())
        p2 = copy.deepcopy(p); p2['assessment_items'][0]['actual_operations'] = ['RECALL', 'EXPLAIN']
        p2['coverage'][0].update(status='EVIDENCED_PENDING_SEMANTIC_REVIEW', evidence_item_ids=['q1'])
        self.assertIn('SCOPE_SET_CONTENT_CHANGED', codes(run(d, p2)[0]))


class RecallOperationDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = F.make('math', tempfile.mkdtemp(prefix='b64-'))
        cls.m = inventory(root, Path(tempfile.mkdtemp(prefix='b64out-')) / 'inv')
        cls.p = compile_curriculum(cls.m)

    def test_recall_decision_removes_explain_evidence_but_keeps_wording(self):
        row = next(r for r in self.p['coverage'] if r['evidence_item_ids'])
        kid, qid = row['kc_id'], row['evidence_item_ids'][0]
        def compiled(item_ops):
            return compile_curriculum(self.m, decisions=SemanticDecisions([
                {'kind': 'operation', 'subject_id': kid, 'value': ['EXPLAIN'], 'decided_by': 'fixture', 'rationale': 'KC explains'},
                {'kind': 'operation', 'subject_id': qid, 'value': item_ops, 'decided_by': 'owner', 'rationale': 'owner classification'}]))
        base, p2 = compiled(['EXPLAIN']), compiled(['RECALL'])
        r1 = next(r for r in base['coverage'] if r['kc_id'] == kid); r2 = next(r for r in p2['coverage'] if r['kc_id'] == kid)
        self.assertIn(qid, r1['evidence_item_ids'])                                    # baseline: EXPLAIN item evidences
        q0 = next(q for q in base['assessment_items'] if q['item_id'] == qid)
        q = next(q for q in p2['assessment_items'] if q['item_id'] == qid)
        self.assertEqual((q['actual_operations'], q['operation_basis']), (['RECALL'], 'semantic_decision:owner'))
        self.assertEqual((q['text'], q['own_wording']), (q0['text'], q0['own_wording']))   # wording unchanged
        self.assertNotIn(qid, r2['evidence_item_ids']); self.assertIn(qid, r2['recall_only_item_ids'])
        if not r2['evidence_item_ids']:
            self.assertNotEqual(r2['status'], 'EVIDENCED_PENDING_SEMANTIC_REVIEW')
        self.assertIn('competency requires EXPLAIN', ' '.join(x['reason'] for x in r2['rejected_links'] if x['item_id'] == qid))

    def test_unknown_operation_is_refused(self):
        with self.assertRaises(Exception):
            SemanticDecisions([{'kind': 'operation', 'subject_id': 'q-x', 'value': ['GUESS'], 'rationale': 'r'}]).validate(set())


if __name__ == '__main__':
    unittest.main()
