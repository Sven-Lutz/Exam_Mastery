"""B6: structured review decisions (em-review-decisions-v1). Offline; synthetic manifests, gates and fake providers only."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from test_p3_2_chapter_filter import three_chapters
from test_p3_6_review_overlay import quiet
from exam_mastery.common import ContractError
from exam_mastery.chapters import chapter_context, dry_run, planned_actions
from exam_mastery.runtime import run_chapters
from exam_mastery import review_decisions as D
from exam_mastery import review_overlay as R

SHA = 'a' * 64; RP4 = '4' * 64; RP5 = '5' * 64; RP6 = '6' * 64; RP7 = '7' * 64; IMG = 'c' * 64
CID = 'ch-00000000000001'


def manifest():
    E = lambda eid, kind, page, text='', asset=None, status='ok': {
        'element_id': eid, 'source_id': 'src-a', 'kind': kind, 'text': text, 'locator': {'page': page}, 'status': status,
        **({'asset': {'sha256': asset}} if asset else {})}
    return {'sources': [{'source_id': 'src-a', 'relative_path': 'deck.pdf', 'raw_sha256': SHA}], 'elements': [
        E('el-h5', 'heading', 5, 'Top reasons: team 23 %, money 19 %'), E('el-img5', 'image', 5, asset=IMG, status='uncertain'),
        E('el-dia5', 'diagram', 5, status='uncertain'), E('el-rp5', 'rendered_page', 5, asset=RP5),
        E('el-h4', 'heading', 4, 'Early stages'), E('el-rp4', 'rendered_page', 4, asset=RP4),
        E('el-rp6', 'rendered_page', 6, asset=RP6),                      # textless neighbour page
        E('el-h7', 'heading', 7, 'Insolvency: file within 3 weeks'), E('el-img7', 'image', 7, asset='d' * 64, status='uncertain'),
        E('el-rp7', 'rendered_page', 7, asset=RP7), E('el-h1', 'heading', 1, 'Title')]}


def plan():
    kc = lambda k, a: {'kc_id': k, 'statement': k, 'source_anchor_ids': [a], 'operations': ['EXPLAIN']}
    return {'chapters': [{'chapter_id': CID, 'kc_ids': ['kc-vis', 'kc-nb', 'kc-law', 'kc-ok', 'kc-blk']}],
            'competencies': [kc('kc-vis', 'el-h5'), kc('kc-nb', 'el-h4'), kc('kc-law', 'el-h7'), kc('kc-ok', 'el-h4'),
                             kc('kc-blk', 'el-h1')], 'assessment_items': []}


def gates():
    f = lambda k, code, eids, rule, **w: {'code': code, 'severity': 'review', 'kc_ids': [k], 'element_ids': eids,
                                          'detail': '', 'rule': rule, **w}
    return {CID: {'chapter_id': CID, 'status': 'PARTIAL', 'producible_kc_ids': ['kc-ok'],
                  'blocked_kcs': {'kc-blk': ['ESSENTIAL_VISUAL_UNRESOLVED']},
                  'review_required_kcs': {'kc-vis': ['VISUAL_RELEVANCE_UNKNOWN'], 'kc-nb': ['ADJACENT_PAGE_UNREADABLE'],
                                          'kc-law': ['VISUAL_RELEVANCE_UNKNOWN']},
                  'findings': [f('kc-vis', 'VISUAL_RELEVANCE_UNKNOWN', ['el-img5'], 'V1_LARGE_IMAGE'),
                               f('kc-vis', 'VISUAL_RELEVANCE_UNKNOWN', ['el-dia5'], 'V1_RELEVANCE_UNKNOWN'),
                               f('kc-nb', 'ADJACENT_PAGE_UNREADABLE', [], 'S2_SCAN_NEIGHBOUR_PAGE', source_id='src-a', pages=[6]),
                               f('kc-law', 'VISUAL_RELEVANCE_UNKNOWN', ['el-img7'], 'V1_RELEVANCE_UNKNOWN'),
                               {'code': 'ESSENTIAL_VISUAL_UNRESOLVED', 'severity': 'blocker', 'kc_ids': ['kc-blk'],
                                'element_ids': [], 'detail': '', 'rule': 'V2'}]}}


HUMAN = {'reviewer_id': 'u1', 'type': 'HUMAN', 'display_name': 'Course owner', 'identity_version': 'v1'}
MODEL = {'reviewer_id': 'm1', 'type': 'MODEL', 'display_name': 'model session', 'identity_version': 'v1'}
APPROVE = {'approved': True, 'approver_id': 'u1', 'date': '2026-11-01', 'statement': 'pilot may use this claim'}


def dec(**kw):
    d = {'decision_id': 'd1', 'chapter_id': CID, 'kc_id': 'kc-vis', 'source_ref': 'A', 'page': 5,
         'cause_element_id': 'el-img5', 'asset_sha256': IMG, 'page_render_sha256': RP5,
         'decision_type': 'DECORATIVE_FOR_THIS_CLAIM', 'claim': {'claim_id': 'c1', 'text': 'reasons named', 'kind': 'QUALITATIVE'},
         'reason': 'photo', 'model_review': {'status': 'MODEL_REVIEWED'}, 'pilot_scope_approval': dict(APPROVE),
         'source_claim_human_verification': None}
    d.update(kw); return d


def dia(**kw):
    return dec(**{'decision_id': 'd2', 'cause_element_id': 'el-dia5', 'asset_sha256': None, **kw})


def dset(*ds, sha=SHA, reviewers=(HUMAN, MODEL), overlay_sha=None):
    return ({'schema': D.SCHEMA, 'decision_set_id': 's', 'version': 'v1', 'overlay_sha256': overlay_sha,
             'sources': [{'source_ref': 'A', 'relative_path': 'deck.pdf', 'sha256': sha}],
             'reviewers': list(reviewers), 'decisions': list(ds)}, 'f' * 64)


def run(*ds, overlay=None, **kw):
    ev = P.evaluate_signed(dset(*ds, **kw), manifest(), plan(), gates(), overlay)
    return ev, D.apply(gates(), ev)[CID]


def codes(ev):
    return {e['code'] for r in ev['rejected'] for e in r['errors']}


class Decisions(unittest.TestCase):
    def test_01_unconfirmed_proposal_has_no_effect(self):
        ev, g = run(dec(pilot_scope_approval=None), dia(pilot_scope_approval=None))
        self.assertEqual(ev['counts']['unconfirmed'], 2); self.assertEqual(ev['counts']['effective_unlocks'], 0)
        self.assertEqual(g['producible_kc_ids'], ['kc-ok']); self.assertIn('kc-vis', g['review_required_kcs'])
        self.assertEqual(g['status'], 'PARTIAL')

    def test_02_exact_unlock_only_for_the_covered_kc(self):
        ev, g = run(dec(), dia())
        self.assertEqual(sorted(g['producible_kc_ids']), ['kc-ok', 'kc-vis'])
        self.assertEqual(set(g['review_required_kcs']), {'kc-nb', 'kc-law'})
        self.assertIn('kc-blk', g['blocked_kcs'])
        u = g['review_decision_effects']['pilot_scope_unlocked_kcs']['kc-vis']
        self.assertFalse(u['source_claim_human_verified'])            # scope approval never implies verification

    def test_03_residual_blocker_keeps_review(self):
        ev, g = run(dec())                                              # the diagram on the same page is not decided
        self.assertIn('kc-vis', g['review_required_kcs'])
        self.assertEqual(g['review_decision_effects']['still_review_required']['kc-vis'], ['element:el-dia5'])

    def test_04_forged_or_model_approver(self):
        ev, _ = run(dec(pilot_scope_approval=dict(APPROVE, approver_id='ghost')),
                    dia(pilot_scope_approval=dict(APPROVE, approver_id='m1')))
        self.assertEqual(ev['counts']['accepted'], 0)
        self.assertTrue({'UNKNOWN_APPROVER', 'APPROVER_NOT_HUMAN'} <= codes(ev))
        ev, _ = run(dec(pilot_scope_approval=dict(APPROVE, date='2099-01-01')))   # future date
        self.assertIn('INVALID_APPROVAL_DATE', codes(ev))
        with self.assertRaises(ContractError):
            P.evaluate_signed(dset(dec(), reviewers=(HUMAN, dict(HUMAN))), manifest(), plan(), gates())

    def test_05_wrong_hashes_and_stale_source(self):
        ev, _ = run(dec(asset_sha256='0' * 64), dia(page_render_sha256='0' * 64))
        self.assertTrue({'ASSET_HASH_MISMATCH', 'PAGE_RENDER_HASH_MISMATCH'} <= codes(ev))
        ev, g = run(dec(), dia(), sha='9' * 64)
        self.assertIn('STALE_SOURCE_HASH', codes(ev)); self.assertIn('kc-vis', g['review_required_kcs'])

    def test_06_scope_approval_cannot_set_human_verified(self):
        ev, _ = run(dec(pilot_scope_approval=dict(APPROVE, human_verified=True)))
        self.assertIn('SCOPE_APPROVAL_SETS_OTHER_FIELDS', codes(ev))
        hv = {'verified': True, 'verifier_id': 'm1', 'date': '2026-11-01', 'method': 'looked',
              'compared_against_page_render_sha256': RP5}
        ev, _ = run(dec(source_claim_human_verification=hv))
        self.assertIn('VERIFIER_NOT_HUMAN', codes(ev))
        ev, _ = run(dec(source_claim_human_verification=dict(hv, verifier_id='u1', compared_against_page_render_sha256=RP4)))
        self.assertIn('VERIFICATION_NOT_AGAINST_THIS_PAGE', codes(ev))
        ev, _ = run(dec(source_claim_human_verification=dict(hv, verifier_id='u1')))
        self.assertEqual(ev['counts']['source_claim_human_verified'], 1)
        ev, _ = run(dec(model_review={'status': 'HUMAN_VERIFIED'}))
        self.assertIn('MODEL_REVIEW_OVERCLAIMS', codes(ev))

    def test_07_quantitative_claim_from_decorative_visual_rejected(self):
        q = {'claim_id': 'c2', 'text': 'shares', 'kind': 'QUANTITATIVE', 'required_values': ['23', '19']}
        ev, _ = run(dec(claim=q))
        self.assertIn('QUANTITATIVE_CLAIM_FROM_DECORATIVE_VISUAL', codes(ev))
        ok = dict(decision_type='TEXT_REDUNDANT_FOR_THIS_CLAIM', text_evidence_element_ids=['el-h5'])
        ev, _ = run(dec(claim=q, **ok)); self.assertEqual(ev['counts']['rejected'], 0)
        ev, _ = run(dec(claim=dict(q, required_values=['23', '42']), **ok))
        self.assertIn('VALUES_NOT_IN_TEXT_EVIDENCE', codes(ev))

    def test_08_visual_redundant_for_one_claim_only(self):
        # the same image decided twice for the same KC/cause, differently: collision, nothing unlocks
        ev, g = run(dec(), dec(decision_id='d1b', decision_type='ESSENTIAL_VISUAL_UNRESOLVED'), dia())
        self.assertIn('COLLISION', codes(ev)); self.assertIn('kc-vis', g['review_required_kcs'])
        # a decision for kc-vis never opens another KC that shares the page
        ev, g = run(dec(), dia())
        self.assertNotIn('kc-law', g['producible_kc_ids'])
        ev, _ = run(dec(kc_id='kc-law'))                                 # cause not of that KC
        self.assertIn('CAUSE_NOT_IN_GATE', codes(ev))

    def test_09_orphans_and_blocked(self):
        ev, _ = run(dec(kc_id='kc-gone'), dec(decision_id='x', chapter_id='ch-ffffffffffffff'),
                    dec(decision_id='y', cause_element_id='el-invented'))
        self.assertTrue({'ORPHAN_KC', 'CHAPTER_NOT_IN_PLAN', 'UNKNOWN_ELEMENT_ID'} <= codes(ev))
        ev, g = run(dec(decision_id='b', kc_id='kc-blk', page=1, cause_element_id='el-h1', page_render_sha256=RP5))
        self.assertIn('kc-blk', g['blocked_kcs'])

    def test_10_textless_neighbour_page_and_transcription_need_overlay(self):
        nb = dec(decision_id='n', kc_id='kc-nb', page=6, cause_element_id='el-rp6', asset_sha256=None, page_render_sha256=RP6,
                 decision_type='VISUAL_TRANSCRIBED_FOR_PILOT', annotation_ids=['a-p6'])
        ev, g = run(nb)
        self.assertIn('OVERLAY_MISSING', codes(ev)); self.assertIn('kc-nb', g['review_required_kcs'])
        ov = {'overlay_sha256': 'o' * 64, 'accepted': [{'annotation_id': 'a-p6', 'page': 6, 'chapter_id': CID,
                                                       'source': {'source_id': 'src-a'}}]}
        ev, g = run(nb, overlay=ov, overlay_sha='x' * 64)
        self.assertIn('STALE_OVERLAY', codes(ev))
        ev, g = run(nb, overlay=ov, overlay_sha='o' * 64)
        self.assertIn('kc-nb', g['producible_kc_ids'])
        ev, g = run(dict(nb, annotation_ids=['a-other']), overlay=ov, overlay_sha='o' * 64)
        self.assertIn('ANNOTATION_NOT_ACCEPTED', codes(ev))
        ev, _ = run(dict(nb, decision_type='TEXT_REDUNDANT_FOR_THIS_CLAIM', annotation_ids=[]))   # no text evidence
        self.assertIn('TEXT_EVIDENCE_INVALID', codes(ev))

    def test_11_legal_counterexample(self):
        law = dec(decision_id='l', kc_id='kc-law', page=7, cause_element_id='el-img7', asset_sha256='d' * 64,
                  page_render_sha256=RP7, claim={'claim_id': 'c3', 'text': 'lecture says 3 weeks', 'kind': 'LEGAL_NORM'})
        ev, g = run(law)
        u = g['review_decision_effects']['pilot_scope_unlocked_kcs']['kc-law']
        self.assertIn('LEGAL_STATUS_NOT_VERIFIED', u['restrictions'])
        self.assertIn('NO_BINDING_LEGAL_MODEL_SOLUTION', u['restrictions'])
        lv = {'status': D.LEGAL_VERIFIED, 'verifier_id': 'm1', 'norm_ref': '§', 'official_url': 'u', 'as_of_date': '2026-11-01'}
        ev, _ = run(dict(law, legal_verification=lv))
        self.assertIn('UNSUPPORTED_LEGAL_VERIFICATION', codes(ev))

    def test_12_exclusion_keeps_kc_in_gate_and_needs_consequences(self):
        ex = dec(decision_id='e', kc_id='kc-blk', page=1, cause_element_id=None, asset_sha256=None,
                 page_render_sha256=RP5, decision_type='PILOT_SCOPE_EXCLUDED_WITH_REASON')
        ev, _ = run(ex)
        self.assertTrue({'NO_PAGE_RENDER', 'EXCLUSION_WITHOUT_CONSEQUENCES'} <= codes(ev))
        m = manifest(); m['elements'].append({'element_id': 'el-rp1', 'source_id': 'src-a', 'kind': 'rendered_page', 'text': '',
                                              'locator': {'page': 1}, 'asset': {'sha256': '1' * 64}})
        ok = dict(ex, page_render_sha256='1' * 64, coverage_consequences=['title slide: no objective'])
        ev = P.evaluate_signed(dset(ok), m, plan(), gates()); g = D.apply(gates(), ev)[CID]
        self.assertIn('kc-blk', g['review_decision_effects']['pilot_scope_excluded_kcs'])
        self.assertIn('kc-blk', g['blocked_kcs']); self.assertNotIn('kc-blk', g['producible_kc_ids'])
        ev = P.evaluate_signed(dset(dict(ok, kc_id='kc-ok', page=4, page_render_sha256=RP4)), manifest(), plan(), gates())
        self.assertIn('EXCLUSION_OF_PRODUCIBLE_KC', codes(ev))

    def test_13_input_gates_not_mutated_and_context_carries_scope(self):
        g0 = gates(); ev = P.evaluate_signed(dset(dec(), dia()), manifest(), plan(), g0); D.apply(g0, ev)
        self.assertEqual(g0, gates())

    def test_15_bundle_approval_same_provenance_only(self):
        a, b = dec(pilot_scope_approval=None), dia(pilot_scope_approval=None)
        ds = dset(a, b); ds[0]['bundle_approvals'] = [{'bundle_id': 'B1', 'decision_ids': ['d1', 'd2'], 'pilot_scope_approval': APPROVE}]
        ev = P.evaluate_signed(ds, manifest(), plan(), gates()); g = D.apply(gates(), ev)[CID]
        self.assertIn('kc-vis', g['producible_kc_ids']); self.assertEqual({x['approved_via_bundle'] for x in ev['accepted']}, {'B1'})
        ds = dset(a, dict(b, decision_type='ESSENTIAL_VISUAL_UNRESOLVED'))
        ds[0]['bundle_approvals'] = [{'bundle_id': 'B1', 'decision_ids': ['d1', 'd2'], 'pilot_scope_approval': APPROVE}]
        self.assertIn('BUNDLE_MIXED_PROVENANCE', codes(P.evaluate_signed(ds, manifest(), plan(), gates())))
        ds = dset(dec(), b); ds[0]['bundle_approvals'] = [{'bundle_id': 'B1', 'decision_ids': ['d1', 'd2', 'zz'], 'pilot_scope_approval': APPROVE}]
        self.assertIn('BUNDLE_UNKNOWN_DECISION', codes(P.evaluate_signed(ds, manifest(), plan(), gates())))
        ds = dset(dec(), b); ds[0]['bundle_approvals'] = [{'bundle_id': 'B1', 'decision_ids': ['d1', 'd2'], 'pilot_scope_approval': APPROVE}]
        self.assertIn('DOUBLE_APPROVAL', codes(P.evaluate_signed(ds, manifest(), plan(), gates())))
        ds = dset(a, b); ds[0]['bundle_approvals'] = [{'bundle_id': 'B1', 'decision_ids': ['d1', 'd2'],
                                                         'pilot_scope_approval': dict(APPROVE, approver_id='m1')}]
        self.assertIn('APPROVER_NOT_HUMAN', codes(P.evaluate_signed(ds, manifest(), plan(), gates())))

    def test_14_load_refuses_file_in_source_root(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); f = root / 'x.json'; f.write_text(json.dumps(dset()[0]))
            with self.assertRaises(ContractError):
                D.load(f, root)
            f.write_text(json.dumps({**dset()[0], 'schema': 'other'}))
            with self.assertRaises(ContractError):
                D.load(f)


class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.root = three_chapters(F.random_root(self.d / 'src'))
        rep, self.plan, self.m, self.gates, _ = dry_run(self.root, self.d / 'dry0')
        self.cid = self.plan['chapters'][1]['chapter_id']
        src = self.m['sources'][0]
        self.ds = {'schema': D.SCHEMA, 'decision_set_id': 'it', 'version': 'v1', 'overlay_sha256': None,
                   'sources': [{'source_ref': 'S', 'relative_path': src['relative_path'], 'sha256': src['raw_sha256']}],
                   'reviewers': [HUMAN], 'decisions': [dec(chapter_id=self.cid, kc_id=self.plan['chapters'][1]['kc_ids'][0],
                                                          source_ref='S', pilot_scope_approval=None)]}
        self.f = self.d / 'decisions.json'; self.f.write_text(json.dumps(self.ds))

    def tearDown(self):
        self.tmp.cleanup()

    def test_20_dry_run_with_unconfirmed_template_changes_nothing(self):
        rep, plan, m, gates, actions = dry_run(self.root, self.d / 'dry1', only_chapter=self.cid, review_decisions=self.f)
        self.assertEqual({c: g['status'] for c, g in gates.items()}, {c: g['status'] for c, g in self.gates.items()})
        self.assertEqual({c: g['producible_kc_ids'] for c, g in gates.items()},
                         {c: g['producible_kc_ids'] for c, g in self.gates.items()})
        self.assertEqual(rep['review_decisions']['counts']['effective_unlocks'], 0)
        self.assertEqual(rep['review_decisions']['academic_release'], 'NOT_TESTED')
        ctx = json.loads((self.d / 'dry1' / 'selected_chapter_context.json').read_text())
        self.assertIn('review_decisions', ctx)
        self.assertFalse(any('pilot_scope' in c for c in ctx['competencies']))

    def test_21_resume_identity_bound_to_decisions(self):
        with quiet():
            out1, st = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs',
                                    only_chapter=self.cid, review_decisions=self.f)
        self.assertEqual(st['review_decisions']['sha256'], D.load(self.f)[1])
        ptr = next((self.d / 'runs').glob('course-*/active_chapters-*.json'))
        id1 = json.loads(ptr.read_text())['identity']
        with quiet():
            out_same, _ = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs',
                                       only_chapter=self.cid, review_decisions=self.f)
        self.assertEqual(json.loads(ptr.read_text())['identity'], id1)
        self.ds['decisions'][0]['reason'] = 'changed'; self.f.write_text(json.dumps(self.ds))
        with quiet():
            out2, _ = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs',
                                   only_chapter=self.cid, review_decisions=self.f)
        self.assertNotEqual(json.loads(ptr.read_text())['identity'], id1); self.assertNotEqual(out1, out2)

    def test_22_budget_gate_unchanged_by_decisions(self):
        from exam_mastery.budget import BudgetBlocked
        class Ext(P.SyntheticChapterModel):
            external = True
        with self.assertRaises(BudgetBlocked):
            run_chapters(self.root, provider=Ext(), output_base=self.d / 'runs', only_chapter=self.cid, review_decisions=self.f)
        _, audit = planned_actions(self.plan, self.gates, self.m, only=self.cid)
        self.assertLessEqual(audit['max_calls'], 6)

    def test_23_cli_refuses_legacy_with_decisions(self):
        from exam_mastery.runtime import main
        with quiet():
            self.assertEqual(main([str(self.root), '--legacy-packages', '--review-decisions', str(self.f)]), 2)


class SessionContract(unittest.TestCase):
    def test_30_off_session_items_not_listed_as_own_and_unlinked_section_items_visible(self):
        plan = {'course_id': 'c', 'domain_profile': {}, 'notation_registry': [], 'planner_version': 'p',
                'chapters': [{'chapter_id': CID, 'title': 't', 'position': 6, 'kc_ids': [], 'narrative_dependencies': [],
                              'requirements': {}, 'source_package': {'element_ids': [], 'source_ids': []},
                              'exam_relevance': {'linked_item_ids': ['q-own', 'q-other'], 'section_mismatch_item_ids': ['q-other'],
                                                 'section_unlinked_item_ids': ['q-gap']}}],
                'competencies': [], 'coverage': [],
                'assessment_items': [{'item_id': q, 'own_wording': q, 'points': None, 'actual_operations': [], 'format': 'x',
                                      'section_label': s} for q, s in (('q-own', 'Session 6'), ('q-other', 'Session 5'),
                                                                        ('q-gap', 'Session 6'))]}
        ctx = chapter_context(plan, {'elements': [], 'sources': []}, CID, {'producible_kc_ids': [], 'blocked_kcs': {}, 'findings': []})
        self.assertEqual([q['item_id'] for q in ctx['exam_items']], ['q-own'])
        self.assertEqual([q['item_id'] for q in ctx['exam_items_other_section']], ['q-other'])
        self.assertEqual(ctx['exam_items_other_section'][0]['role'], 'SECTION_MISMATCH_NOT_THIS_CHAPTERS_ITEM')
        self.assertEqual([q['item_id'] for q in ctx['section_items_without_link']], ['q-gap'])


if __name__ == '__main__':
    unittest.main()
