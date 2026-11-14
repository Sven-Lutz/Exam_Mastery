"""A PROVE competency blocked by a linearised formula is produced only when every page with a blocking formula was
read by the agent with content; the transcription joins the context and a restriction is attached."""
import unittest
from exam_mastery import auto_scope as A


def el(eid, kind, page, text='', status='ok', fid=None):
    return {'element_id': eid, 'source_id': 's1', 'kind': kind, 'status': status, 'text': text, 'locator': {'page': page},
            'fidelity': fid or {}}


def setup(read_pages):
    els = [el('h1', 'paragraph', 1, 'Satz 2.10. Es seien (an)n und (bn)n reelle Folgen mit an gegen a.'),
           el('p1', 'paragraph', 1, 'Beweis. Wir zeigen zuerst die Monotonie und dann die Schranke fuer alle n.'),
           el('p2', 'paragraph', 1, 'Daraus folgt die Behauptung fuer jede Teilfolge der Folge und den Grenzwert.'),
           el('f1', 'formula', 1, 'limn an', fid={'representation': 'linearized_text_layer'}),
           el('f2', 'formula', 2, 'limn bn', fid={'representation': 'linearized_text_layer'}),
           el('t1', 'visual_transcription', 1, 'Satz 2.10: \\(\\lim_{n\\to\\infty} a_n = a\\)'),
           el('t2', 'visual_transcription', 2, '\\(\\lim_{n\\to\\infty} b_n = b\\)')]
    kc = {'kc_id': 'k1', 'statement': 'Satz: 2.10 Es seien', 'operations': ['PROVE'], 'source_anchor_ids': ['h1']}
    plan = {'competencies': [kc], 'chapters': [{'chapter_id': 'c1', 'title': 'Folgen', 'kc_ids': ['k1']}]}
    gate = {'chapter_id': 'c1', 'producible_kc_ids': [], 'blocked_kcs': {'k1': ['CRITICAL_FORMULA_UNRELIABLE']}, 'review_required_kcs': {},
            'findings': [{'code': 'CRITICAL_FORMULA_UNRELIABLE', 'severity': 'blocker', 'kc_ids': ['k1'], 'element_ids': ['f1', 'f2']}]}
    m = {'elements': els, 'agent_vision': {'content': [f's1:{p}' for p in read_pages], 'decorative': []}}
    return plan, m, gate


class FormulaScope(unittest.TestCase):
    def test_all_formula_pages_read(self):
        plan, m, g = setup([1, 2])
        c = A.classify(plan, m, g)['k1']
        self.assertEqual(c['category'], A.VISION)
        self.assertIn('t2', c['text_element_ids'])                     # transcription of the second formula page
        self.assertTrue(any('FORMULAS_ONLY_FROM_VISUAL_TRANSCRIPTION' in r for r in c['restrictions']))
        self.assertFalse(c['source_claim_human_verified'])
        self.assertIn('k1', A.apply(plan, m, {'c1': g})['c1']['producible_kc_ids'])

    def test_missing_formula_page_stays_blocked(self):
        plan, m, g = setup([1])
        c = A.classify(plan, m, g)['k1']
        self.assertEqual(c['category'], A.VISUAL_REVIEW)
        self.assertNotIn('k1', A.apply(plan, m, {'c1': g})['c1']['producible_kc_ids'])

    def test_no_reading_stays_blocked(self):
        plan, m, g = setup([])
        self.assertNotEqual(A.classify(plan, m, g)['k1']['category'], A.VISION)


if __name__ == '__main__':
    unittest.main()
