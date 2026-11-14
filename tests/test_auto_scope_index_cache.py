"""Performance hotfix: auto_scope builds its element lookups once per manifest object (was once per chapter gate and
once per competency; ~2 h on a 67k-element course). Results must be identical and a cache may never leak across
manifests."""
import copy, json, time, unittest
from exam_mastery import auto_scope as A
from exam_mastery import examples as X
from tests.test_b7_auto_scope import fixture, el, WORDS


def classify_uncached(plan, m, g):
    A._INDEX.clear()
    try:
        return A.classify(plan, m, g)
    finally:
        A._INDEX.clear()


class IndexCache(unittest.TestCase):
    def test_same_result_as_fresh_index(self):
        plan, m, g = fixture()
        fresh = classify_uncached(plan, m, g)
        A.classify(plan, m, g)                       # warm
        self.assertEqual(A.classify(plan, m, g), fresh)
        self.assertEqual(A.apply(plan, m, {'c1': g}), A.apply(plan, m, {'c1': g}))

    def test_other_manifest_never_hits(self):
        plan, m, g = fixture(text_on_rich_page=True)
        rich = A.classify(plan, m, g)
        _, thin_m, _ = fixture(text_on_rich_page=False)
        thin = A.classify(plan, thin_m, g)           # different object: must be rebuilt, not reused
        self.assertEqual(thin, classify_uncached(plan, thin_m, g))
        self.assertNotEqual(rich['k-text']['category'], thin['k-text']['category'])

    def test_grown_manifest_rebuilds(self):
        plan, m, g = fixture(text_on_rich_page=False)
        before = A.classify(plan, m, g)
        m['elements'].append(el('p9', 'paragraph', 1, WORDS))   # same object, new element (e.g. visual import)
        after = A.classify(plan, m, g)
        self.assertEqual(after, classify_uncached(plan, m, g))
        self.assertNotEqual(before['k-text']['category'], after['k-text']['category'])

    def test_continuation_index_equivalent(self):
        els = [{'element_id': f'e{p}{i}', 'locator': f's1/page-{p}', 'source': 's1', 'text': t, 'status': 'ok', 'kind': 'paragraph'}
               for p, t in ((1, 'Beispiel Teil 1: 10 + 20 = 30'), (2, 'Beispiel Teil 2 (Fortsetzung): 30 + 5 = 35'), (3, 'Anderes'))
               for i in range(2)]
        idx = ({e['element_id']: e for e in els}, *X.groups(els))
        for anchors in (['e10'], ['e20'], ['e30'], ['missing']):
            self.assertEqual(X.continuation_elements(anchors, els), X.continuation_elements(anchors, els, index=idx))

    def test_scales_linearly(self):
        """60 chapters x 20 competencies over 20k elements: must finish in seconds (was quadratic)."""
        els = [el(f'x{i}', 'paragraph', i // 10, WORDS) for i in range(20000)]
        kcs = [{'kc_id': f'k{c}-{j}', 'statement': 's', 'operations': ['EXPLAIN'], 'source_anchor_ids': [f'x{(c * 20 + j) * 10}']}
               for c in range(60) for j in range(20)]
        plan = {'competencies': kcs, 'chapters': [{'chapter_id': f'c{c}', 'kc_ids': [f'k{c}-{j}' for j in range(20)]} for c in range(60)]}
        gates = {f'c{c}': {'chapter_id': f'c{c}', 'status': 'PARTIAL', 'producible_kc_ids': [], 'blocked_kcs': {}, 'findings': [],
                           'review_required_kcs': {f'k{c}-{j}': ['VISUAL_RELEVANCE_UNKNOWN'] for j in range(20)}} for c in range(60)}
        m = {'elements': els}
        t = time.time()
        rows = A.coverage_report(plan, m, gates, A.apply(plan, m, gates))
        self.assertEqual(len(rows), 1200)
        self.assertLess(time.time() - t, 30)


if __name__ == '__main__':
    unittest.main()
