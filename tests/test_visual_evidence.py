"""B8: figure content read by the calling agent: validation, integration, scope, gates, labels, invalidation."""
import json, unittest
from exam_mastery import auto_scope as A, visual_evidence as V
from exam_mastery.chapter_publish import author_draft_checks, model


def el(eid, kind, page, text='', asset=None):
    return {'element_id': eid, 'source_id': 's1', 'kind': kind, 'status': 'ok', 'text': text, 'locator': {'page': page},
            'locator_str': f'deck.pdf/page-{page}#{kind}', 'flags': [], 'asset': asset}


def fixture():
    els = [el('h1', 'heading', 1, 'Startup investments'), el('img1', 'image', 1),
           el('r1', 'rendered_page', 1, asset={'path': 'a/1.png', 'sha256': 'AAA'}),
           el('h2', 'heading', 2, 'Think positive'), el('p2', 'paragraph', 2, 'See opportunities rather than problems.'),
           el('p3', 'paragraph', 2, 'Be proactive and give your best every day.'), el('img2', 'image', 2),
           el('r2', 'rendered_page', 2, asset={'path': 'a/2.png', 'sha256': 'BBB'})]
    m = {'sources': [{'source_id': 's1', 'relative_path': 'deck.pdf', 'element_ids': [e['element_id'] for e in els], 'authority': 'OFFICIAL'}],
         'elements': els}
    kcs = [{'kc_id': 'k-chart', 'statement': 'explain investments', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h1']},
           {'kc_id': 'k-deco', 'statement': 'explain think positive', 'operations': ['EXPLAIN'], 'source_anchor_ids': ['h2']}]
    plan = {'competencies': kcs, 'chapters': [{'chapter_id': 'c1', 'title': 'Funding', 'kc_ids': ['k-chart', 'k-deco'],
                                               'source_package': {'element_ids': [e['element_id'] for e in els]}}]}
    gate = {'chapter_id': 'c1', 'status': 'BLOCKED', 'producible_kc_ids': [],
            'blocked_kcs': {'k-chart': ['ESSENTIAL_VISUAL_UNRESOLVED'], 'k-deco': ['ESSENTIAL_VISUAL_UNRESOLVED']},
            'review_required_kcs': {}, 'findings': []}
    return plan, m, gate


def evidence(**over):
    p1 = {'source': 'deck.pdf', 'page': 1, 'render_sha256': 'AAA', 'classification': 'CONTENT', 'visual_type': 'bar chart',
          'statements': [{'text': 'Investments peaked in 2021 at 14.6 bn €.', 'confidence': 'HIGH', 'numbers': ['2021', '14.6']},
                         {'text': 'Rounds 2020: 732 + 413 + 613 = 1758.', 'confidence': 'HIGH', 'numbers': ['2020', '732', '413', '613', '1758']},
                         {'text': 'Maybe a trend to 20 bn.', 'confidence': 'LOW', 'numbers': ['20']}],
          'arithmetic': [{'expression': '732+413+613', 'stated': '1758'}]}
    p2 = {'source': 'deck.pdf', 'page': 2, 'render_sha256': 'BBB', 'classification': 'DECORATIVE', 'statements': []}
    p1.update(over)
    return {'schema': V.SCHEMA, 'reader': {'agent': 'test', 'model': 'm', 'human_verified': False}, 'pages': [p1, p2]}


class Validation(unittest.TestCase):
    def test_accepts_checks_numbers_and_keeps_low_out(self):
        _, m, _ = fixture()
        acc, rep = V.validate(evidence(), m)
        self.assertEqual([r['result'] for r in rep], ['ACCEPTED', 'DECORATIVE'])
        self.assertEqual(len(acc[0]['statements']), 2)
        self.assertIn('LOW confidence', rep[0]['rejected'][0]['reason'])
        self.assertEqual(rep[0]['arithmetic'][0]['result'], 'PASS')

    def test_wrong_sum_rejects_statements_using_it(self):
        _, m, _ = fixture()
        ev = evidence(arithmetic=[{'expression': '732+413+613', 'stated': '1785'}])
        ev['pages'][0]['statements'][1] = {'text': 'Rounds 2020 total 1785.', 'confidence': 'HIGH', 'numbers': ['2020', '1785']}
        acc, rep = V.validate(ev, m)
        self.assertEqual(rep[0]['arithmetic'][0]['result'], 'FAIL')
        self.assertTrue(any('failed arithmetic' in r['reason'] for r in rep[0]['rejected']))

    def test_undeclared_number_and_stale_render_and_human_claim(self):
        _, m, _ = fixture()
        ev = evidence(); ev['pages'][0]['statements'][0]['numbers'] = ['2021']
        _, rep = V.validate(ev, m)
        self.assertIn('not declared', rep[0]['rejected'][0]['reason'])
        _, rep = V.validate(evidence(render_sha256='OLD'), m)
        self.assertEqual(rep[0]['result'], 'REJECTED_STALE_RENDER')
        bad = evidence(); bad['reader']['human_verified'] = True
        with self.assertRaises(Exception):
            V.validate(bad, m)

    def test_unreadable_stays_open(self):
        plan, m, g = fixture()
        acc, rep = V.validate(evidence(classification='UNREADABLE'), m)
        store = {'pages': acc}
        plan2, m2, _ = V.integrate(plan, m, store)
        self.assertEqual(A.classify(plan2, m2, g)['k-chart']['category'], A.VISUAL_REVIEW)


class Integration(unittest.TestCase):
    def setUp(self):
        plan, m, self.g = fixture()
        acc, _ = V.validate(evidence(), m)
        self.plan, self.m, self.sum = V.integrate(plan, m, {'pages': acc})
        self.orig = fixture()

    def test_scope_categories(self):
        c = A.classify(self.plan, self.m, self.g)
        self.assertEqual(c['k-chart']['category'], A.VISION)
        self.assertEqual(c['k-deco']['category'], A.TEXT_ONLY)          # decorative figure, complete text
        out = A.apply(self.plan, self.m, {'c1': self.g})['c1']
        self.assertEqual(sorted(out['producible_kc_ids']), ['k-chart', 'k-deco'])
        self.assertEqual(json.dumps(fixture()[1], sort_keys=True), json.dumps(self.orig[1], sort_keys=True))  # input unchanged

    def test_numbers_gate_and_label(self):
        from exam_mastery.chapters import chapter_context
        vid = self.sum['element_ids']['deck.pdf:1']
        g = A.apply(self.plan, self.m, {'c1': self.g})['c1']
        ctx = {'source_elements': [{'element_id': e['element_id'], 'text': e['text'], 'kind': e['kind'], 'locator': e['locator_str']}
                                   for e in self.m['elements']], 'allowed_source_refs': [e['element_id'] for e in self.m['elements']],
               'produce_kc_ids': g['producible_kc_ids'], 'competencies': []}
        ok = {'block_id': 'b1', 'kind': 'EXPLANATION', 'kc_ids': ['k-chart'], 'provenance': 'COURSE_SOURCE', 'source_refs': [vid],
              'body': 'Investments peaked in 2021 at 14.6 bn €.'}
        bad = dict(ok, block_id='b2', body='Investments peaked in 2021 at 16.2 bn €.')
        res = {c['object_id']: c['status'] for c in author_draft_checks({'blocks': [ok, bad]}, ctx, self.m) if c['check'] == 'SOURCE_NUMBERS'}
        self.assertEqual(res, {'b1': 'PASS', 'b2': 'FAIL'})
        mm = model({'blocks': [ok], 'assessments': [], 'solutions': []}, self.m)
        self.assertIn('vom Agenten ausgewertet', mm['blocks'][0]['status_label'])

    def test_changed_slide_invalidates_reading(self):
        plan, m, g = fixture()
        acc, _ = V.validate(evidence(), m)
        m['elements'][2]['asset']['sha256'] = 'NEW'            # slide 1 re-rendered after a change
        _, m2, s = V.integrate(plan, m, {'pages': acc})
        self.assertEqual(s['stale'], ['deck.pdf:1'])
        self.assertFalse(any(e['kind'] == V.KIND for e in m2['elements']))


if __name__ == '__main__':
    unittest.main()
