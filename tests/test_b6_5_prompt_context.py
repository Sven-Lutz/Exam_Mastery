"""B6.5: the compact prompt context is lossless and keeps every source, restriction and review finding visible."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from exam_mastery.chapters import dry_run
from exam_mastery.prompt_context import compact, expand, dumps


def contexts():
    """Real chapter contexts as the engine writes them for a selected chapter (dry run, no provider)."""
    out = []
    for kind in ('math', 'law', 'ml'):
        root = F.make(kind, tempfile.mkdtemp(prefix='b65-'))
        o = Path(tempfile.mkdtemp(prefix='b65o-'))
        plan = dry_run(root, o / 'all')[1]
        for c in plan['chapters']:
            dry_run(root, o / c['chapter_id'], only_chapter=c['chapter_id'])
            f = o / c['chapter_id'] / 'selected_chapter_context.json'
            if f.exists():
                out.append((kind, json.loads(f.read_text())))
    return out


class Lossless(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctxs = contexts()

    def test_round_trip_on_real_fixture_contexts(self):
        self.assertTrue(self.ctxs)
        for kind, ctx in self.ctxs:
            with self.subTest(kind=kind, chapter=ctx.get('chapter_id')):
                c = compact(ctx)
                self.assertEqual(expand(json.loads(dumps(c))), ctx)              # exact, after a JSON round trip
                self.assertLessEqual(len(dumps(c)), len(json.dumps(ctx, ensure_ascii=False, sort_keys=True)))

    def test_edge_cases_fall_back_or_stay_exact(self):
        kind, base = self.ctxs[0]
        cases = []
        x = copy.deepcopy(base); x['source_elements'] = list(reversed(x['source_elements'])); cases.append(x)   # non-sorted order
        x = copy.deepcopy(base)
        if x['source_elements']:
            x['source_elements'][0]['status'] = 'uncertain'; x['source_elements'][0]['flags'] = ['SCAN']
            x['source_elements'][-1].pop('text', None)
        cases.append(x)
        x = copy.deepcopy(base); x['allowed_source_refs'] = x['allowed_source_refs'][:1]; cases.append(x)       # refs differ
        x = copy.deepcopy(base)
        if x['source_elements']: x['source_elements'][0]['unexpected'] = 1                                      # unknown field
        cases.append(x)
        for i, ctx in enumerate(cases):
            with self.subTest(case=i):
                self.assertEqual(expand(json.loads(dumps(compact(ctx)))), ctx)

    def test_restrictions_and_review_findings_stay_visible_in_the_prompt(self):
        kind, ctx = self.ctxs[0]
        ctx = copy.deepcopy(ctx)
        ctx['review_decisions'] = {'accepted': [{'decision_id': 'd1', 'restrictions': ['Q17_GRADING_ACCEPT_EITHER_TIED_RANK_5_OR_6', 'NO_RESOLUTION_OF_CAP_TABLE']}]}
        ctx['review_evidence'] = {'annotations': [{'annotation_id': 'D3-p49', 'content': {'resolution': 'OPEN - no rule is chosen here'}}]}
        text = dumps(compact(ctx))
        for needle in ('Q17_GRADING_ACCEPT_EITHER_TIED_RANK_5_OR_6', 'NO_RESOLUTION_OF_CAP_TABLE', 'OPEN - no rule is chosen here'):
            self.assertIn(needle, text)
        for e in ctx['source_elements']:
            self.assertIn(json.dumps(e['element_id']), text)
            if e.get('text'): self.assertIn(json.dumps(e['text'], ensure_ascii=False), text)


if __name__ == '__main__':
    unittest.main()
