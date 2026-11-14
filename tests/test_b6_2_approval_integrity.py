"""B6.2: approvals are bound to the exact content they approve. Offline; synthetic approvals only (reviewer 'u1' is a
test fixture, never a real person). A change after approval must invalidate the approval, never pass silently."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p3_fixtures as P
import p3_3_fixtures as T
from test_b6_review_decisions import (manifest as kc_manifest, plan as kc_plan, gates as kc_gates, dec, dia, HUMAN, MODEL,
                                      APPROVE, CID, SHA)
from test_b6_1_chapter_page_gate import (manifest as pg_manifest, plan as pg_plan, gates as pg_gates, overlay as pg_overlay, pr,
                                         excl, OV)
from test_p3_6_review_overlay import quiet
from exam_mastery import review_decisions as D
from exam_mastery.chapters import production_preflight, dry_run
from exam_mastery.runtime import run_chapters
from exam_mastery.curriculum import SemanticDecisions


def data(*ds, bundles=(), reviews=(), overlay_sha=None, reviewers=(HUMAN, MODEL)):
    return {'schema': D.SCHEMA, 'decision_set_id': 's', 'version': 'v1', 'overlay_sha256': overlay_sha,
            'sources': [{'source_ref': 'A', 'relative_path': 'deck.pdf', 'sha256': SHA}], 'reviewers': list(reviewers),
            'decisions': list(ds), 'bundle_approvals': list(bundles), 'page_reviews': list(reviews)}


def sign(d, plan):
    """Test-only: what a human does after reading the content - copy the content hash into the approval."""
    d = copy.deepcopy(d); h = D.content_hashes(d, plan)
    for x in d['decisions']:
        if (x.get('pilot_scope_approval') or {}).get('approved') is True:
            x['pilot_scope_approval']['approved_content_sha256'] = h['decisions'][x['decision_id']]
    for b in d['bundle_approvals']:
        if (b.get('pilot_scope_approval') or {}).get('approved') is True:
            b['pilot_scope_approval']['approved_content_sha256'] = h['bundles'][b['bundle_id']]
    for r in d['page_reviews']:
        if (r.get('pilot_scope_approval') or {}).get('approved') is True:
            r['pilot_scope_approval']['approved_content_sha256'] = h['page_reviews'][r['review_id']]
    return d


def kc_eval(d, plan=None):
    p = plan or kc_plan()
    ev = D.evaluate((d, 'f' * 64), kc_manifest(), p, kc_gates())
    return ev, D.apply(kc_gates(), ev)[CID]


def codes(ev, part=None):
    rej = ev['rejected'] if part is None else ev['page_reviews']['rejected']
    return {e['code'] for r in rej for e in r['errors']}


class ContentBinding(unittest.TestCase):
    def test_01_signed_approval_works_and_unsigned_hash_is_refused(self):
        d = sign(data(dec(), dia()), kc_plan())
        ev, g = kc_eval(d)
        self.assertEqual(ev['rejected'], []); self.assertIn('kc-vis', g['producible_kc_ids'])
        ev, g = kc_eval(data(dec(), dia()))                                   # approval without content hash
        self.assertIn('APPROVAL_NOT_CONTENT_BOUND', codes(ev)); self.assertIn('kc-vis', g['review_required_kcs'])

    def test_02_restriction_changed_after_approval_is_detected(self):
        d = sign(data(dec(restrictions=['A']), dia()), kc_plan())
        d['decisions'][0]['restrictions'] = []                                  # someone drops a restriction later
        ev, g = kc_eval(d)
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev)); self.assertIn('kc-vis', g['review_required_kcs'])

    def test_03_claim_changed_after_approval_stays_locked(self):
        d = sign(data(dec(), dia()), kc_plan())
        d['decisions'][0]['claim']['text'] = 'a broader claim'
        ev, g = kc_eval(d)
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev)); self.assertNotIn('kc-vis', g['producible_kc_ids'])
        d = sign(data(dec(), dia()), kc_plan()); d['decisions'][0]['decision_type'] = 'TEXT_REDUNDANT_FOR_THIS_CLAIM'
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(kc_eval(d)[0]))

    def test_04_bundle_bound_to_exact_set_and_content(self):
        b = {'bundle_id': 'B1', 'decision_ids': ['d1'], 'pilot_scope_approval': dict(APPROVE)}
        d = sign(data(dec(pilot_scope_approval=None), dia(decision_type='DECORATIVE_FOR_THIS_CLAIM', pilot_scope_approval=None),
                      bundles=[b]), kc_plan())
        ok, _ = kc_eval(d); self.assertEqual(ok['rejected'], [])
        added = copy.deepcopy(d); added['bundle_approvals'][0]['decision_ids'].append('d2')     # set grows after signing
        self.assertIn('BUNDLE_CONTENT_CHANGED', codes(kc_eval(added)[0]))
        edited = copy.deepcopy(d); edited['decisions'][0]['reason'] = 'other reason'           # content of a member changes
        self.assertIn('BUNDLE_CONTENT_CHANGED', codes(kc_eval(edited)[0]))
        self.assertEqual(kc_eval(edited)[0]['counts']['effective_unlocks'], 0)

    def test_05_verification_is_content_bound_too(self):
        hv = {'verified': True, 'verifier_id': 'u1', 'date': '2026-11-01', 'method': 'compared', 'compared_against_page_render_sha256': '5' * 64}
        d = data(dec(source_claim_human_verification=dict(hv)), dia())
        d = sign(d, kc_plan()); ev, _ = kc_eval(d)
        self.assertIn('VERIFICATION_NOT_CONTENT_BOUND', codes(ev))
        h = D.content_hashes(d, kc_plan())['decisions']['d1']
        d['decisions'][0]['source_claim_human_verification']['verified_content_sha256'] = h
        d = sign(d, kc_plan()); ev, g = kc_eval(d)
        self.assertEqual(ev['rejected'], [])
        self.assertTrue(next(a for a in ev['accepted'] if a['decision_id'] == 'd1')['source_claim_human_verified'])
        d['decisions'][0]['claim']['text'] = 'changed'
        self.assertTrue({'VERIFICATION_CONTENT_CHANGED', 'APPROVAL_CONTENT_CHANGED'} <= codes(kc_eval(d)[0]))

    def test_06_chapter_session_scope_change_invalidates_approvals(self):
        p = kc_plan(); p['chapters'][0]['exam_relevance'] = {'section_number': 6, 'linked_item_ids': ['q1'],
                                                              'section_mismatch_item_ids': [], 'section_unlinked_item_ids': []}
        d = sign(data(dec(), dia()), p)
        self.assertEqual(kc_eval(d, p)[0]['rejected'], [])
        p2 = copy.deepcopy(p); p2['chapters'][0]['exam_relevance']['section_number'] = 5   # e.g. another file shifted order
        ev, g = kc_eval(d, p2)
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev)); self.assertIn('kc-vis', g['review_required_kcs'])

    def test_07_page_review_bound_to_overlay_source_and_text(self):
        def ev_pg(d, ov=None):
            return D.evaluate((d, 'f' * 64), pg_manifest(), pg_plan(), pg_gates(), ov or pg_overlay())
        base = {**data(reviews=[pr()], overlay_sha=OV), 'sources': [{'source_ref': 'A', 'relative_path': 'deck.pdf', 'sha256': SHA}]}
        d = sign(base, pg_plan())
        self.assertEqual(ev_pg(d)['page_reviews']['rejected'], [])
        x = copy.deepcopy(d); x['page_reviews'][0]['uncertainty_statement'] = 'nothing is uncertain'
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev_pg(x), 'pages'))
        x = copy.deepcopy(d); x['overlay_sha256'] = '1' * 64                    # owner switches to another overlay
        ov2 = dict(pg_overlay(), overlay_sha256='1' * 64)
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev_pg(x, ov2), 'pages'))
        x = copy.deepcopy(d); x['page_reviews'][0]['annotation_ids'] = ['pg6', 'other']
        self.assertIn('APPROVAL_CONTENT_CHANGED', codes(ev_pg(x), 'pages'))

    def test_08_hashes_are_reported_and_nothing_is_approved_by_default(self):
        d = data(dec(pilot_scope_approval=None), dia(pilot_scope_approval=None))
        ev, _ = kc_eval(d)
        self.assertEqual(ev['counts']['effective_unlocks'], 0)
        self.assertEqual(set(ev['content_hashes']['decisions']), {'d1', 'd2'})
        self.assertNotIn('approved_content_sha256', json.dumps(d))


class OrderAndIdentity(unittest.TestCase):
    def test_10_unresolved_course_order_blocks_session_mapped_chapter(self):
        from test_b6_1_chapter_page_gate import plan as p1, gates as g1
        p = p1(); p['chapter_ordering'] = {'status': 'UNRESOLVED_REVIEW_REQUIRED'}
        p['chapters'][0]['exam_relevance']['section_number'] = 5
        pf = production_preflight(p, g1(), [CID])['chapters'][CID]
        self.assertIn('COURSE_ORDER_UNRESOLVED', {o['code'] for o in pf['open']})
        self.assertEqual(pf['exam_section']['section_number'], 5)
        p['chapter_ordering'] = {'status': 'CONFLICT_REVIEW_REQUIRED'}
        self.assertNotIn('COURSE_ORDER_UNRESOLVED', {o['code'] for o in production_preflight(p, g1(), [CID])['chapters'][CID]['open']})

    def test_11_semantic_link_decisions_are_part_of_the_run_identity(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t); root = d / 'src'; root.mkdir(); T.lecture_deck(root, n=12)
            rep, plan, *_ = dry_run(root, d / 'dry')
            cid = plan['chapters'][0]['chapter_id']; kc = plan['chapters'][0]['kc_ids'][0]
            sd = lambda r: SemanticDecisions([{'kind': 'link', 'subject_id': kc, 'value': [], 'decided_by': 'fixture', 'rationale': r}])
            with quiet():
                run_chapters(root, provider=P.SyntheticChapterModel(), output_base=d / 'r', only_chapter=cid, decisions=sd('a'))
            ptr = next((d / 'r').glob('course-*/active_chapters-*.json')); id1 = json.loads(ptr.read_text())['identity']
            with quiet():
                run_chapters(root, provider=P.SyntheticChapterModel(), output_base=d / 'r', only_chapter=cid, decisions=sd('b'))
            self.assertNotEqual(json.loads(ptr.read_text())['identity'], id1)


if __name__ == '__main__':
    unittest.main()
