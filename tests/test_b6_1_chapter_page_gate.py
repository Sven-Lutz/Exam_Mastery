"""B6.1: chapter-level review of textless pages + fail-closed production preflight. Offline; synthetic data, generated
PDFs and fake providers only. No real provider, no network."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p3_fixtures as P
import p3_3_fixtures as T
from test_b6_review_decisions import manifest as b6_manifest, gates as b6_gates, HUMAN, MODEL, APPROVE, CID, SHA, RP6
from test_p3_6_review_overlay import quiet
from test_p0_resource_budget import cfg
from exam_mastery import review_decisions as D
from exam_mastery.chapters import dry_run, production_preflight, chapter_context, PilotReviewOpen
from exam_mastery.runtime import run_chapters, main

IMG6 = 'e' * 64; OV = '0f' * 32; COURSE = 'course-test00000000'


def manifest():
    m = b6_manifest()
    m['elements'].append({'element_id': 'el-img6', 'source_id': 'src-a', 'kind': 'image', 'text': '', 'locator': {'page': 6},
                          'status': 'uncertain', 'asset': {'sha256': IMG6}})
    return m


def plan():
    kc = lambda k, a: {'kc_id': k, 'statement': k, 'source_anchor_ids': [a], 'operations': ['EXPLAIN'],
                       'origin': 'stated_learning_objective'}
    return {'course_id': COURSE, 'source_roles': {},
            'chapters': [{'chapter_id': CID, 'source_ids': ['src-a'], 'kc_ids': ['kc-vis', 'kc-nb', 'kc-law', 'kc-ok', 'kc-blk'],
                          'exam_relevance': {'linked_item_ids': ['q1']}}],
            'competencies': [kc('kc-vis', 'el-h5'), kc('kc-nb', 'el-h4'), kc('kc-law', 'el-h7'), kc('kc-ok', 'el-h4'),
                             kc('kc-blk', 'el-h1')], 'assessment_items': [{'item_id': 'q1'}]}


PAGE_FINDING = {'code': 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN', 'severity': 'review', 'kc_ids': [], 'element_ids': [],
                'detail': 'deck.pdf: pages [6] have no text layer; their content is unknown', 'rule': 'S3_SCAN_CHAPTER_REVIEW',
                'source_id': 'src-a', 'pages': [6]}


def gates(extra=()):
    g = b6_gates()
    g[CID]['findings'] += [copy.deepcopy(PAGE_FINDING), *extra]
    return g


def overlay(anchor='PAGE_IMAGE', asset=RP6, verified=False):
    return {'overlay_sha256': OV, 'accepted': [{'annotation_id': 'pg6', 'chapter_id': CID, 'page': 6, 'anchor_kind': anchor,
                                                 'source': {'source_id': 'src-a'}, 'asset_ref': {'sha256': asset},
                                                 'human_verified': verified}]}


def pr(**kw):
    r = {'review_id': 'p6', 'course_id': COURSE, 'chapter_id': CID, 'source_ref': 'A', 'page': 6,
         'cause_code': 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN', 'page_render_element_id': 'el-rp6', 'page_render_sha256': RP6,
         'image_asset_sha256': IMG6, 'annotation_ids': ['pg6'], 'decision_type': 'PAGE_ESSENTIAL_TRANSCRIBED_UNCERTAIN_FOR_PILOT',
         'reason': 'textless page is essential; only the qualitative overlay reading may be used',
         'uncertainty_statement': 'no values, positions or boundaries can be established',
         'model_review': {'status': 'MODEL_REVIEWED'}, 'pilot_scope_approval': dict(APPROVE),
         'source_claim_human_verification': None}
    r.update(kw); return r


def excl(kid, did):
    return {'decision_id': did, 'chapter_id': CID, 'kc_id': kid, 'source_ref': 'A', 'page': 4 if kid in ('kc-nb',) else 5 if kid == 'kc-vis' else 7,
            'decision_type': 'PILOT_SCOPE_EXCLUDED_WITH_REASON', 'claim': {'claim_id': did, 'text': 'out of pilot', 'kind': 'QUALITATIVE'},
            'reason': 'not in pilot', 'coverage_consequences': ['objective not covered'],
            'page_render_sha256': {'kc-nb': '4' * 64, 'kc-vis': '5' * 64}.get(kid, '7' * 64),
            'model_review': None, 'pilot_scope_approval': dict(APPROVE), 'source_claim_human_verification': None}


def dset(*reviews, decisions=(), reviewers=(HUMAN, MODEL), sha=SHA, overlay_sha=OV):
    return ({'schema': D.SCHEMA, 'decision_set_id': 's', 'version': 'v1', 'overlay_sha256': overlay_sha,
             'sources': [{'source_ref': 'A', 'relative_path': 'deck.pdf', 'sha256': sha}], 'reviewers': list(reviewers),
             'decisions': list(decisions), 'page_reviews': list(reviews)}, 'f' * 64)


def run(*reviews, ov=None, extra=(), **kw):
    ev = P.evaluate_signed(dset(*reviews, **kw), manifest(), plan(), gates(extra), overlay() if ov is None else ov)
    g = D.apply(gates(extra), ev)
    return ev, g, production_preflight(plan(), g, [CID])['chapters'][CID]


def page_codes(ev):
    return {e['code'] for r in ev['page_reviews']['rejected'] for e in r['errors']}


def open_codes(pf):
    return {o['code'] for o in pf['open']}


class PageReviewContract(unittest.TestCase):
    def test_01_no_review_or_unconfirmed_keeps_chapter_blocked_and_no_default_approval(self):
        ev, g, pf = run()
        self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf)); self.assertEqual(pf['status'], 'PILOT_BLOCKED')
        ev, g, pf = run(pr(pilot_scope_approval=None))
        self.assertEqual(ev['page_reviews']['accepted'][0]['effect'], 'NONE_UNCONFIRMED_PROPOSAL')
        self.assertFalse(ev['page_reviews']['accepted'][0]['scope_approved_for_experimental_pilot'])
        self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))
        self.assertEqual(g[CID]['review_decision_effects']['chapter_page_reviews']['open'], ['page:src-a:6'])

    def test_02_valid_scope_review_clears_only_this_page_and_stays_uncertain(self):
        ev, g, pf = run(pr())
        self.assertNotIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))
        a = ev['page_reviews']['accepted'][0]
        self.assertEqual(a['effect'], 'CLEARS_PAGE_FOR_EXPERIMENTAL_PILOT')
        self.assertFalse(a['source_claim_human_verified']); self.assertEqual(a['academic_release'], 'NOT_TESTED')
        self.assertTrue({'PAGE_TRANSCRIPTION_UNCERTAIN', 'OVERLAY_NOT_HUMAN_VERIFIED', 'QUALITATIVE_ONLY_AS_ANNOTATED'} <= set(a['restrictions']))
        f = next(x for x in g[CID]['findings'] if x['code'] == 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN')
        self.assertEqual(f['severity'], 'review')                       # the finding is kept, annotated, never deleted
        self.assertIn('PAGE_TRANSCRIPTION_UNCERTAIN', f['pilot_scope_page_reviews'][0]['restrictions'])
        self.assertEqual(g[CID]['status'], 'PARTIAL'); self.assertIn('kc-blk', g[CID]['blocked_kcs'])
        self.assertIn('KC_REVIEW_UNDECIDED', open_codes(pf))             # KC causes are not touched by a page review
        self.assertNotIn('"source_claim_human_verified": true', json.dumps(ev))
        self.assertNotIn('"human_verified": true', json.dumps(ev)); self.assertNotIn('ACADEMIC_RELEASE_GO', json.dumps(ev))

    def test_03_invalid_types_including_decorative_or_irrelevant(self):
        for t in ('DECORATIVE_FOR_THIS_CLAIM', 'PAGE_IRRELEVANT', 'TEXT_REDUNDANT_FOR_THIS_CLAIM', None):
            ev, _, pf = run(pr(decision_type=t))
            self.assertIn('INVALID_PAGE_REVIEW_TYPE', page_codes(ev)); self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))

    def test_04_model_unknown_or_unnamed_approver_and_bad_dates(self):
        nameless = dict(HUMAN, display_name=None)
        cases = [(pr(pilot_scope_approval=dict(APPROVE, approver_id='m1')), {}, 'APPROVER_NOT_HUMAN'),
                 (pr(pilot_scope_approval=dict(APPROVE, approver_id='ghost')), {}, 'UNKNOWN_APPROVER'),
                 (pr(), {'reviewers': (nameless, MODEL)}, 'APPROVER_NOT_HUMAN'),
                 (pr(pilot_scope_approval=dict(APPROVE, date='2099-01-01')), {}, 'INVALID_APPROVAL_DATE'),
                 (pr(pilot_scope_approval=dict(APPROVE, date='2026-13-40')), {}, 'INVALID_APPROVAL_DATE'),
                 (pr(pilot_scope_approval=dict(APPROVE, human_verified=True)), {}, 'SCOPE_APPROVAL_SETS_OTHER_FIELDS')]
        for r, kw, code in cases:
            ev, _, pf = run(r, **kw)
            self.assertIn(code, page_codes(ev)); self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))

    def test_05_wrong_source_render_asset_overlay_course_and_changed_page(self):
        cases = [({'sha': '9' * 64}, pr(), 'STALE_SOURCE_HASH'),
                 ({}, pr(page_render_sha256='0' * 64), 'PAGE_RENDER_HASH_MISMATCH'),
                 ({}, pr(image_asset_sha256='0' * 64), 'ASSET_HASH_MISMATCH'),
                 ({'overlay_sha': '1' * 64}, pr(), 'STALE_OVERLAY'),
                 ({}, pr(course_id='course-other'), 'COURSE_MISMATCH'),
                 ({}, pr(page=5, page_render_element_id='el-rp5', page_render_sha256='5' * 64, image_asset_sha256='c' * 64), 'CAUSE_NOT_IN_GATE'),
                 ({}, pr(page_render_element_id='el-rp5'), 'PAGE_RENDER_ELEMENT_INVALID')]
        for kw, r, code in cases:
            ev, _, pf = run(r, **kw)
            self.assertIn(code, page_codes(ev), code); self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))

    def test_06_transcription_needs_page_image_annotation_and_uncertainty(self):
        for ov, r, code in [(overlay(anchor='TEXT_ELEMENTS'), pr(), 'ANNOTATION_WRONG_ANCHOR'),
                            (overlay(asset='3' * 64), pr(), 'ANNOTATION_WRONG_ANCHOR'),
                            (overlay(), pr(annotation_ids=['missing']), 'ANNOTATION_NOT_ACCEPTED'),
                            (overlay(), pr(annotation_ids=[]), 'TRANSCRIPTION_WITHOUT_ANNOTATION'),
                            (overlay(), pr(uncertainty_statement=' '), 'MISSING_UNCERTAINTY_STATEMENT')]:
            ev, _, _ = run(r, ov=ov)
            self.assertIn(code, page_codes(ev))
        ev = P.evaluate_signed(dset(pr()), manifest(), plan(), gates(), None)
        self.assertIn('OVERLAY_MISSING', page_codes(ev))

    def test_07_collision_duplicate_and_unresolved_type(self):
        ev, _, pf = run(pr(), pr(review_id='p6b'))
        self.assertIn('COLLISION', page_codes(ev)); self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))
        ev, _, _ = run(pr(), pr())
        self.assertIn('DUPLICATE_REVIEW_ID', page_codes(ev))
        ev, _, pf = run(pr(decision_type='PAGE_ESSENTIAL_UNRESOLVED'))
        self.assertEqual(ev['page_reviews']['accepted'][0]['effect'], 'NONE_STAYS_REVIEW')
        self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))

    def test_08_full_clear_needs_every_reason_decided_and_never_verifies(self):
        exc = [excl('kc-vis', 'x1'), excl('kc-nb', 'x2'), excl('kc-law', 'x3')]
        ev, g, pf = run(pr(), decisions=exc)
        self.assertEqual(pf['status'], 'PILOT_SCOPE_CLEARED_EXPERIMENTAL', pf['open'])
        self.assertEqual(pf['eligibility'], 'PENDING_REVIEW')            # eligibility is reported unchanged
        self.assertEqual(pf['academic_release'], 'NOT_TESTED')
        self.assertIn('kc-blk', g[CID]['blocked_kcs']); self.assertNotIn('kc-vis', g[CID]['producible_kc_ids'])
        ev, g, pf = run(decisions=exc)                                   # same, but without the page review
        self.assertEqual(open_codes(pf), {'CHAPTER_PAGE_REVIEW_OPEN'})

    def test_09_independent_chapter_blockers_stay_effective(self):
        exc = [excl('kc-vis', 'x1'), excl('kc-nb', 'x2'), excl('kc-law', 'x3')]
        merge = {'code': 'CHAPTER_MERGE_REVIEW', 'severity': 'open_issue', 'kc_ids': [], 'element_ids': [], 'detail': 'merge?'}
        other = {'code': 'SOMETHING_NEW', 'severity': 'review', 'kc_ids': [], 'element_ids': [], 'detail': 'x'}
        for f in (merge, other):
            _, _, pf = run(pr(), decisions=exc, extra=(f,))
            self.assertEqual(pf['status'], 'PILOT_BLOCKED'); self.assertIn('CHAPTER_REVIEW_OPEN', open_codes(pf))
        p = plan(); p['chapters'][0]['exam_relevance']['linked_item_ids'] = []
        ev = P.evaluate_signed(dset(pr(), decisions=exc), manifest(), p, gates(), overlay())
        pf = production_preflight(p, D.apply(gates(), ev), [CID])['chapters'][CID]
        self.assertIn('ELIGIBILITY_NO_EXAM_EVIDENCE', open_codes(pf))

class Ext(P.SyntheticChapterModel):
    external = True
    model = P.FAKE_MODEL       # B6.4: external path needs an explicit model


class ProductionPreflight(unittest.TestCase):
    """Real generated PDF with a textless page: the open chapter-level review stops an external provider before any
    checkpoint, run directory or resume pointer exists. --budget never clears it."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.root = self.d / 'src'; self.root.mkdir(); T.lecture_deck(self.root, n=12, scan_page=6)
        rep, self.plan, self.m, self.gates, _ = dry_run(self.root, self.d / 'dry0')
        self.cid = self.plan['chapters'][0]['chapter_id']; self.rep = rep

    def tearDown(self):
        self.tmp.cleanup()

    def test_20_finding_is_structured_and_dry_run_reports_blocked_preflight(self):
        f = next(x for x in self.gates[self.cid]['findings'] if x['code'] == 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN')
        self.assertEqual(f['pages'], [6]); self.assertTrue(f['source_id'].startswith('src-'))
        self.assertEqual(self.rep['production_preflight']['result'], 'BLOCKED')
        self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(self.rep['production_preflight']['chapters'][self.cid]))

    def test_21_pending_review_with_budget_never_reaches_provider_or_checkpoint(self):
        self.assertEqual(self.rep['chapters'][0]['academic_pilot_eligibility'], 'PENDING_REVIEW')
        model = Ext()
        with quiet(), self.assertRaises(PilotReviewOpen) as e:
            run_chapters(self.root, provider=model, output_base=self.d / 'runs', budget_config=cfg(), only_chapter=self.cid)
        self.assertEqual(model.calls, [])                                   # Provider.ask never reached
        self.assertFalse((self.d / 'runs').exists())                        # no course dir, lock, pointer or run dir
        self.assertIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(e.exception.preflight['chapters'][self.cid]))
        with quiet(), self.assertRaises(PilotReviewOpen):                   # all-chapters mode is gated as well
            run_chapters(self.root, provider=Ext(), output_base=self.d / 'runs', budget_config=cfg())
        self.assertFalse((self.d / 'runs').exists())

    def test_22_cli_with_budget_file_stops_with_pilot_review_open(self):
        b = self.d / 'budget.json'; b.write_text(json.dumps(cfg()))
        with patch('exam_mastery.runtime.Provider', side_effect=lambda *a, **k: Ext()), quiet():
            rc = main([str(self.root), '--only-chapter', self.cid, '--budget', str(b)])
        self.assertEqual(rc, 2); self.assertFalse(any(self.d.glob('**/active_chapters*.json')))

    def test_23_real_provider_path_makes_no_process(self):
        from exam_mastery.providers import Provider
        with patch('exam_mastery.providers.execute') as ex, patch('exam_mastery.providers.shutil.which', return_value='/offline/x'), \
                quiet(), self.assertRaises(PilotReviewOpen):
            run_chapters(self.root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 'runs', budget_config=cfg(), only_chapter=self.cid)
        ex.assert_not_called()

    def test_24_budget_check_still_comes_first_and_offline_fake_is_not_gated(self):
        from exam_mastery.budget import BudgetBlocked
        with self.assertRaises(BudgetBlocked):
            run_chapters(self.root, provider=Ext(), output_base=self.d / 'runs', only_chapter=self.cid)
        with quiet():                                                        # offline synthetic model: gate reported, not enforced
            _, st = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs2', only_chapter=self.cid)
        self.assertEqual(st['production_preflight']['result'], 'BLOCKED'); self.assertFalse(st['production_preflight']['enforced'])

    def test_25_changed_page_review_starts_a_new_run(self):
        src = next(s for s in self.m['sources'])
        rp = next(e for e in self.m['elements'] if e['kind'] == 'rendered_page' and e['locator'].get('page') == 6)
        img = next((e['asset']['sha256'] for e in self.m['elements'] if e['kind'] == 'image' and e['locator'].get('page') == 6
                    and e.get('asset')), None)
        ds = {'schema': D.SCHEMA, 'decision_set_id': 'it', 'version': 'v1', 'overlay_sha256': None,
              'sources': [{'source_ref': 'S', 'relative_path': src['relative_path'], 'sha256': src['raw_sha256']}],
              'reviewers': [HUMAN], 'decisions': [],
              'page_reviews': [pr(course_id=self.plan['course_id'], chapter_id=self.cid, source_ref='S',
                                  page_render_element_id=rp['element_id'], page_render_sha256=rp['asset']['sha256'],
                                  image_asset_sha256=img, decision_type='PAGE_ESSENTIAL_UNRESOLVED', pilot_scope_approval=None)]}
        f = self.d / 'dec.json'; f.write_text(json.dumps(ds))
        rep, *_ = dry_run(self.root, self.d / 'dry1', only_chapter=self.cid, review_decisions=f)
        self.assertEqual(rep['review_decisions']['page_reviews']['rejected'], [])
        with quiet():
            out1, _ = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'r', only_chapter=self.cid, review_decisions=f)
        ptr = next((self.d / 'r').glob('course-*/active_chapters-*.json')); id1 = json.loads(ptr.read_text())['identity']
        ds['page_reviews'][0]['reason'] = 'changed'; f.write_text(json.dumps(ds))
        with quiet():
            out2, _ = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'r', only_chapter=self.cid, review_decisions=f)
        self.assertNotEqual(json.loads(ptr.read_text())['identity'], id1); self.assertNotEqual(out1, out2)


    def test_26_approved_page_review_on_real_pdf_clears_page_and_context_shows_uncertainty(self):
        from exam_mastery.common import sha_file
        from exam_mastery import review_overlay as R
        src = self.m['sources'][0]
        rp = next(e for e in self.m['elements'] if e['kind'] == 'rendered_page' and e['locator'].get('page') == 6)
        img = next((e['asset']['sha256'] for e in self.m['elements'] if e['kind'] == 'image' and e['locator'].get('page') == 6
                    and e.get('asset')), None)
        ov = {'schema': R.SCHEMA, 'overlay_id': 'o', 'version': 'v1',
              'sources': [{'source_ref': 'S', 'relative_path': src['relative_path'], 'sha256': src['raw_sha256']}],
              'annotations': [{'annotation_id': 'pg6', 'chapter_id': self.cid, 'source_ref': 'S', 'page': 6,
                               'anchor_kind': 'PAGE_IMAGE', 'element_ids': [rp['element_id']], 'finding_type': 'INTERPRETATION',
                               'reviewer_type': 'MODEL', 'review_status': 'PROPOSED_PENDING_HUMAN_APPROVAL',
                               'provenance': 'DERIVED_EXPLANATION', 'content': {'reading': 'a qualitative picture only'},
                               'asset_ref': {'kind': 'rendered_page', 'sha256': rp['asset']['sha256']}, 'version': 'v1'}]}
        of = self.d / 'ov.json'; of.write_text(json.dumps(ov))
        ds = {'schema': D.SCHEMA, 'decision_set_id': 'it', 'version': 'v1', 'overlay_sha256': sha_file(of),
              'sources': [{'source_ref': 'S', 'relative_path': src['relative_path'], 'sha256': src['raw_sha256']}],
              'reviewers': [HUMAN], 'decisions': [],
              'page_reviews': [pr(course_id=self.plan['course_id'], chapter_id=self.cid, source_ref='S',
                                  page_render_element_id=rp['element_id'], page_render_sha256=rp['asset']['sha256'],
                                  image_asset_sha256=img)]}
        ds = P.signed(ds, self.plan)                     # synthetic approval bound to the current content (B6.2)
        f = self.d / 'dec.json'; f.write_text(json.dumps(ds))
        rep, *_ = dry_run(self.root, self.d / 'dry2', only_chapter=self.cid, review_overlay=of, review_decisions=f)
        self.assertEqual(rep['review_decisions']['page_reviews']['rejected'], [])
        self.assertEqual(rep['review_decisions']['counts']['page_reviews_effective'], 1)
        pf = rep['production_preflight']['chapters'][self.cid]
        self.assertNotIn('CHAPTER_PAGE_REVIEW_OPEN', open_codes(pf))
        self.assertIn('PAGE_CLEARED_FOR_EXPERIMENTAL_PILOT', {c['code'] for c in pf['cleared']})
        self.assertEqual(rep['selection']['academic_pilot_eligibility'], 'PENDING_REVIEW')   # not upgraded
        ctx = (self.d / 'dry2' / 'selected_chapter_context.json').read_text()
        for s in ('PAGE_TRANSCRIPTION_UNCERTAIN', 'OVERLAY_NOT_HUMAN_VERIFIED', 'no values, positions or boundaries can be established'):
            self.assertIn(s, ctx)
        self.assertNotIn('"source_claim_human_verified": true', ctx)


    def test_27_cli_legacy_path_cannot_bypass_the_preflight(self):
        b = self.d / 'budget.json'; b.write_text(json.dumps(cfg()))
        with patch('exam_mastery.providers.shutil.which', return_value='/offline/x'), \
                patch('exam_mastery.providers.execute') as ex, quiet():
            rc = main([str(self.root), '--legacy-packages', '--budget', str(b)])
        self.assertEqual(rc, 2); ex.assert_not_called()
        self.assertFalse(any(self.d.glob('**/status.json')))

def setUpModule():
    P.install_fake_codex_home()


def tearDownModule():
    P.remove_fake_codex_home()


if __name__ == '__main__':
    unittest.main()
