"""P3.6: subject-neutral review overlay (em-review-annotations-v1). Offline; synthetic manifests and fake providers only."""
import contextlib, copy, io, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from test_p3_2_chapter_filter import three_chapters
from exam_mastery.common import ContractError
from exam_mastery.chapters import chapter_context, dry_run, planned_actions
from exam_mastery.runtime import run_chapters
from exam_mastery import review_overlay as R

SHA_A = 'a' * 64; SHA_B = 'b' * 64; IMG = 'c' * 64


def manifest():
    """Two paginated sources: a lecture deck and a practice catalogue with three sessions."""
    els = [
        {'element_id': 'el-t1', 'source_id': 'src-a', 'kind': 'heading', 'text': 'Variant one', 'locator': {'page': 3}},
        {'element_id': 'el-t2', 'source_id': 'src-a', 'kind': 'heading', 'text': 'Variant two', 'locator': {'page': 4}},
        {'element_id': 'el-img', 'source_id': 'src-a', 'kind': 'image', 'text': '', 'locator': {'page': 5},
         'asset': {'sha256': IMG}},
        {'element_id': 'el-rp', 'source_id': 'src-a', 'kind': 'rendered_page', 'text': '', 'locator': {'page': 5},
         'asset': {'sha256': 'd' * 64}},
        {'element_id': 'el-goal', 'source_id': 'src-a', 'kind': 'heading', 'text': 'Goal one\nWhy?', 'locator': {'page': 2}},
        {'element_id': 'el-tab', 'source_id': 'src-a', 'kind': 'heading', 'text': 'Sum 110', 'locator': {'page': 9}},
        {'element_id': 'el-s1', 'source_id': 'src-b', 'kind': 'heading', 'text': 'Session 1', 'locator': {'page': 1}},
        {'element_id': 'el-s2', 'source_id': 'src-b', 'kind': 'heading', 'text': 'Session 2', 'locator': {'page': 2}},
        {'element_id': 'el-s2q1', 'source_id': 'src-b', 'kind': 'heading', 'text': '1. Q', 'locator': {'page': 2}},
    ]
    return {'sources': [{'source_id': 'src-a', 'relative_path': 'deck.pdf', 'raw_sha256': SHA_A},
                        {'source_id': 'src-b', 'relative_path': 'catalogue.pdf', 'raw_sha256': SHA_B}], 'elements': els}


PLAN = {'chapters': [{'chapter_id': 'ch-00000000000001'}, {'chapter_id': 'ch-00000000000002'}],
        'assessment_items': [{'item_id': 'q-1'}, {'item_id': 'q-2'}]}


def ann(**kw):
    a = {'annotation_id': 'a1', 'chapter_id': 'ch-00000000000001', 'source_ref': 'A', 'page': 3, 'anchor_kind': 'TEXT_ELEMENTS',
         'element_ids': ['el-t1'], 'finding_type': 'DIAGRAM_STRUCTURE', 'reviewer_type': 'MODEL',
         'review_status': 'PROPOSED_PENDING_HUMAN_APPROVAL', 'provenance': 'ORIGINAL_CONTENT', 'content': {'x': 'y'},
         'asset_ref': {'kind': 'NONE', 'sha256': None}, 'version': 'v1'}
    a.update(kw); return a


def overlay(*anns, sha_a=SHA_A):
    return {'schema': R.SCHEMA, 'overlay_id': 'o', 'version': 'v1',
            'sources': [{'source_ref': 'A', 'relative_path': 'deck.pdf', 'sha256': sha_a},
                        {'source_ref': 'B', 'relative_path': 'catalogue.pdf', 'sha256': SHA_B}], 'annotations': list(anns)}


def codes(ev):
    return {e['code'] for r in ev['rejected'] for e in r['errors']}


class Validation(unittest.TestCase):
    def ev(self, *anns, **kw):
        return R.evaluate(overlay(*anns, **kw), manifest(), PLAN, 'f' * 64)

    def test_01_sha_mismatch_blocks_stale_annotations(self):
        ev = self.ev(ann(), sha_a='0' * 64)
        self.assertEqual(ev['counts']['accepted'], 0); self.assertIn('STALE_SOURCE_HASH', codes(ev))

    def test_02_wrong_page_or_unknown_element_rejected(self):
        ev = self.ev(ann(annotation_id='p', page=4), ann(annotation_id='u', element_ids=['el-invented']),
                     ann(annotation_id='s', element_ids=['el-s1'], page=1))
        self.assertEqual(ev['counts']['accepted'], 0)
        self.assertTrue({'ELEMENT_WRONG_PAGE', 'UNKNOWN_ELEMENT_ID', 'ELEMENT_WRONG_SOURCE'} <= codes(ev))

    def test_02b_page_image_needs_matching_asset_hash(self):
        ok = ann(annotation_id='i', page=5, anchor_kind='PAGE_IMAGE', element_ids=['el-img'], finding_type='INTERPRETATION',
                 provenance='DERIVED_EXPLANATION', asset_ref={'kind': 'image', 'sha256': IMG})
        bad = dict(ok, annotation_id='j', asset_ref={'kind': 'image', 'sha256': 'e' * 64})
        none = dict(ok, annotation_id='k', page=3, element_ids=['el-t1'])
        ev = self.ev(ok, bad, none)
        self.assertEqual([a['annotation_id'] for a in ev['accepted']], ['i'])
        self.assertTrue({'ASSET_HASH_MISMATCH', 'PAGE_IMAGE_WITHOUT_IMAGE_ELEMENT'} <= codes(ev))

    def test_03_diagram_variants_stay_distinct(self):
        ev = self.ev(ann(annotation_id='v1', content={'variant': 'A', 'boxes': ['x', 'y']}),
                     ann(annotation_id='v2', page=4, element_ids=['el-t2'], content={'variant': 'B', 'boxes': ['x', 'z']}))
        block = R.context_block(ev, 'ch-00000000000001')
        self.assertEqual([a['content']['variant'] for a in block['annotations']], ['A', 'B'])
        self.assertEqual({a['page'] for a in block['annotations']}, {3, 4})

    def test_04_textless_image_interpretation_without_numbers(self):
        base = dict(page=5, anchor_kind='PAGE_IMAGE', element_ids=['el-img'], finding_type='INTERPRETATION',
                    provenance='DERIVED_EXPLANATION', asset_ref={'kind': 'image', 'sha256': IMG})
        ev = self.ev(ann(annotation_id='n', content={'curve': 'falls to about -200k at month 18'}, **base),
                     ann(annotation_id='q', content={'curve': 'falls, reaches a low point, rises again'}, **base))
        self.assertEqual([a['annotation_id'] for a in ev['accepted']], ['q'])
        self.assertIn('NUMERIC_CLAIM_WITHOUT_TEXT_LAYER', codes(ev))
        self.assertTrue(ev['accepted'][0]['anchors_textless'])

    def test_05_expression_check_detects_inconsistent_sum(self):
        ev = self.ev(ann(page=9, element_ids=['el-tab'], finding_type='CALCULATION',
                         checks=[{'check_id': 'sum', 'kind': 'expression', 'expr': '25000+3350+6650+9500', 'stated': 44467},
                                 {'check_id': 'ok', 'kind': 'expression', 'expr': '33350*8000000/6000000', 'stated': 44467, 'tolerance': 0.5}]))
        chk = {c['check_id']: c for c in ev['accepted'][0]['engine_checks']}
        self.assertEqual(chk['sum']['result'], 'CHECK_MISMATCH'); self.assertEqual(chk['sum']['difference'], 33)
        self.assertEqual(chk['ok']['result'], 'CHECK_PASS')
        with self.assertRaises(ContractError):
            R.safe_eval('__import__("os").system("x")')
        self.assertIn('INVALID_CHECK', codes(self.ev(ann(annotation_id='b', checks=[{'kind': 'expression', 'expr': 'open(1)', 'stated': 1}]))))

    def test_06_guiding_questions_not_official(self):
        links = [{'statement': 'Goal one', 'basis': 'OFFICIAL_OBJECTIVE'}, {'statement': 'Why?', 'basis': 'GUIDING_QUESTION'}]
        a = self.ev(ann(page=2, element_ids=['el-goal'], competency_links=links))['accepted'][0]
        self.assertEqual([l['official'] for l in a['competency_links']], [True, False])
        ev = self.ev(ann(page=2, element_ids=['el-goal'], competency_links=[{'statement': 'Why?', 'basis': 'GUIDING_QUESTION', 'official': True}]))
        self.assertIn('INFERRED_MARKED_OFFICIAL', codes(ev))

    def test_07_sessions_not_mixed(self):
        ev = self.ev(ann(source_ref='B', page=2, element_ids=['el-s2', 'el-s2q1', 'el-s1']))
        self.assertIn('ELEMENT_WRONG_PAGE', codes(ev))   # Session 1 heading is on another page
        ok = self.ev(ann(source_ref='B', page=2, element_ids=['el-s2', 'el-s2q1'], item_links=[{'item_id': 'q-1'}]))
        self.assertEqual(ok['counts']['accepted'], 1)
        self.assertIn('UNKNOWN_ITEM_ID', codes(self.ev(ann(source_ref='B', page=2, element_ids=['el-s2'], item_links=[{'item_id': 'q-x'}]))))

    def test_08_inferred_competency_never_official_and_status_never_promoted(self):
        a = self.ev(ann(competency_links=[{'statement': 'Compute X', 'basis': 'INFERRED_FROM_LECTURE_EXAMPLE'}]))['accepted'][0]
        self.assertFalse(a['competency_links'][0]['official'])
        self.assertEqual(a['review_status'], 'PROPOSED_PENDING_HUMAN_APPROVAL'); self.assertFalse(a['human_verified'])
        self.assertEqual(a['approval_effect'], 'NONE_PROPOSAL_ONLY')
        self.assertIn('UNSUPPORTED_HUMAN_VERIFIED', codes(self.ev(ann(review_status='HUMAN_VERIFIED'))))
        self.assertIn('UNSUPPORTED_HUMAN_VERIFIED', codes(self.ev(ann(review_status='HUMAN_VERIFIED', reviewer_type='HUMAN'))))
        h = self.ev(ann(review_status='HUMAN_VERIFIED', reviewer_type='HUMAN', human_approval={'approver': 'n', 'date': 'd'}))
        self.assertTrue(h['accepted'][0]['human_verified'])

    def test_chapter_binding_and_overlay_location(self):
        self.assertIn('CHAPTER_NOT_IN_PLAN', codes(self.ev(ann(chapter_id='ch-ffffffffffffff'))))
        ev = self.ev(ann())
        self.assertEqual(R.context_block(ev, 'ch-00000000000002')['annotation_count'], 0)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'root'; root.mkdir(); f = root / 'o.json'; f.write_text(json.dumps(overlay(ann())))
            with self.assertRaises(ContractError):
                R.load(f, root)


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


class Integration(unittest.TestCase):
    """A real (synthetic) course root through dry_run / run_chapters with the fake provider."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.root = three_chapters(F.random_root(self.d / 'src'))
        _, self.plan, self.m, self.gates, _ = dry_run(self.root, self.d / 'dry0')
        self.cid = self.plan['chapters'][1]['chapter_id']
        c = self.plan['chapters'][1]
        self.el = next(e for e in self.m['elements'] if e['element_id'] in c['source_package']['element_ids'] and e['text'])
        src = next(s for s in self.m['sources'] if s['source_id'] == self.el['source_id'])
        self.ov = {'schema': R.SCHEMA, 'overlay_id': 'it', 'version': 'v1',
                   'sources': [{'source_ref': 'S', 'relative_path': src['relative_path'], 'sha256': src['raw_sha256']}],
                   'annotations': [ann(annotation_id='marker-annotation', chapter_id=self.cid, source_ref='S',
                                       page=(self.el.get('locator') or {}).get('page'), element_ids=[self.el['element_id']],
                                       content={'marker': 'REVIEW-MARKER-7f3'})]}
        self.f = self.d / 'overlay.json'; self.f.write_text(json.dumps(self.ov))

    def tearDown(self):
        self.tmp.cleanup()

    def test_09_annotations_reach_the_chapter_context_the_author_receives(self):
        rep, plan, m, gates, actions = dry_run(self.root, self.d / 'dry1', only_chapter=self.cid, review_overlay=self.f)
        self.assertEqual(rep['review_overlay']['counts'], {'accepted': 1, 'rejected': 0})
        ctx = json.loads((self.d / 'dry1' / 'selected_chapter_context.json').read_text())
        self.assertEqual(ctx['review_evidence']['annotations'][0]['content']['marker'], 'REVIEW-MARKER-7f3')
        self.assertEqual(rep['selection']['context_bytes'], len((self.d / 'dry1' / 'selected_chapter_context.json').read_bytes()) - 1)
        model = P.SyntheticChapterModel(); seen = []
        orig = model.ask
        def ask(role, prompt, run_dir, images=None):
            seen.append((role, P.context_of(prompt)))
            return orig(role, prompt, run_dir, images)
        model.ask = ask
        with quiet():
            out, st = run_chapters(self.root, provider=model, output_base=self.d / 'runs', only_chapter=self.cid, review_overlay=self.f)
        self.assertTrue(seen)
        for role, ctx in seen:
            self.assertEqual(ctx['review_evidence']['annotations'][0]['content']['marker'], 'REVIEW-MARKER-7f3', role)
            self.assertEqual(ctx['review_evidence']['human_verified_count'], 0)
        self.assertEqual(st['review_overlay']['counts']['accepted'], 1)
        # without an overlay the context is unchanged (no review_evidence key)
        self.assertNotIn('review_evidence', chapter_context(plan, m, self.cid, gates[self.cid]))

    def test_10_overlay_never_unblocks_a_chapter(self):
        gates = copy.deepcopy(self.gates); gates[self.cid]['status'] = 'BLOCKED'
        ev = R.evaluate(R.load(self.f), self.m, self.plan)
        actions, audit = planned_actions(self.plan, gates, self.m, only=self.cid, review=ev)
        self.assertEqual(actions, []); self.assertEqual(audit['unconditional_calls'], 0)
        rep, *_ = dry_run(self.root, self.d / 'dry2', review_overlay=self.f)
        self.assertEqual({c['chapter_id']: c['gate'] for c in rep['chapters']},
                         {cid: g['status'] for cid, g in self.gates.items()})
        self.assertFalse(rep['review_overlay']['changes_gates'])

    def test_11_resume_identity_bound_to_overlay(self):
        from exam_mastery import runtime
        model = P.SyntheticChapterModel()
        with quiet():
            out1, _ = run_chapters(self.root, provider=model, output_base=self.d / 'runs', only_chapter=self.cid, review_overlay=self.f)
        ptr = next((self.d / 'runs').glob('course-*/active_chapters-*.json'))
        id1 = json.loads(ptr.read_text())['identity']
        self.ov['annotations'][0]['content'] = {'marker': 'changed'}; self.f.write_text(json.dumps(self.ov))
        with quiet():
            out2, _ = run_chapters(self.root, provider=P.SyntheticChapterModel(), output_base=self.d / 'runs', only_chapter=self.cid, review_overlay=self.f)
        self.assertNotEqual(json.loads(ptr.read_text())['identity'], id1)
        self.assertNotEqual(out1, out2)

    def test_stale_overlay_is_reported_not_silently_used(self):
        self.ov['sources'][0]['sha256'] = '0' * 64; self.f.write_text(json.dumps(self.ov))
        rep, *_ = dry_run(self.root, self.d / 'dry3', only_chapter=self.cid, review_overlay=self.f)
        self.assertEqual(rep['review_overlay']['counts'], {'accepted': 0, 'rejected': 1})
        ctx = json.loads((self.d / 'dry3' / 'selected_chapter_context.json').read_text())
        self.assertEqual(ctx['review_evidence']['annotations'], [])
        self.assertEqual(ctx['review_evidence']['rejected_annotation_ids'], ['marker-annotation'])


if __name__ == '__main__':
    unittest.main()
