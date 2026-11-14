"""P3.4 regression tests for four generic defects found while reviewing a real chapter. Synthetic, offline."""
import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_3_fixtures as T
from exam_mastery.chapters import dry_run
from exam_mastery.triage import candidate_reject


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def dry(self, root):
        return dry_run(root, self.d / 'out')


class Fixes(Base):
    def test_parenthesised_title_prefix_is_a_title(self):
        self.assertIsNone(candidate_reject('(Simplified) Example: First Round'))
        self.assertIsNotNone(candidate_reject('(€, thousand)'))
        self.assertEqual(candidate_reject('(see appendix)'), 'CONTINUATION_FRAGMENT')
        r = F.random_root(self.d / 's')
        T.lecture_deck(r, extra={4: {'title': '(Simplified) Example: Equity round', 'body': ['Nominal capital and shares per partner']}})
        _, plan, *_ = self.dry(r)
        self.assertTrue(any('(Simplified) Example' in k['statement'] for k in plan['competencies']))

    def test_objective_slide_hierarchy_and_guiding_questions(self):
        r = F.random_root(self.d / 's')
        T.lecture_deck(r, extra={2: {'title': 'Learning objectives', 'body': [
            'Learn about financing options', '- What are typical sources of capital?',
            'Understand investment risk', '- Assess the risk of each investor class', '- What are your obligations in a crisis.']}})
        _, plan, *_ = self.dry(r)
        obj = [k for k in plan['competencies'] if k['origin'] == 'stated_learning_objective']
        self.assertFalse(any(k['statement'].endswith('?') or k['statement'].startswith('What') for k in obj), [k['statement'] for k in obj])
        tops = [k for k in obj if k['objective_level'] == 'OBJECTIVE']; subs = [k for k in obj if k['objective_level'] == 'SUB_OBJECTIVE']
        self.assertEqual(len(tops), 2); self.assertEqual(len(subs), 1)
        self.assertIn(subs[0]['parent_objective_kc_id'], {k['kc_id'] for k in tops})
        self.assertTrue(any(q['assessment_kind'] == 'LECTURE_QUESTION' and 'typical sources' in q['own_wording'] for q in plan['assessment_items']))

    def test_question_number_on_its_own_line(self):
        r = F.random_root(self.d / 's')
        T.slide_pdf(r / 'question_catalogue.pdf', [{'title': 'Question Catalogue', 'raw': True, 'body': [
            '1.', 'Name the three forms of external financing.', '2.', 'What is the definition of risk?', '3.', 'Explain dilution after a round.']}])
        T.lecture_deck(r)
        _, plan, *_ = self.dry(r)
        practice = [q for q in plan['assessment_items'] if q['assessment_kind'] == 'PRACTICE']
        self.assertEqual(sorted(q['label'].split('@')[0] for q in practice), ['1', '2', '3'])
        self.assertTrue(any(q['own_wording'].startswith('Name the three forms') for q in practice))

    def test_multiline_practice_tasks_without_question_verb(self):
        r = F.random_root(self.d / 's')
        from docx import Document
        d = Document(); d.add_heading('Question Catalogue', 1)
        d.add_paragraph('4.\nEarly stages: Why is it difficult to obtain loans? Name all\nthe mentioned aspects.')
        d.add_paragraph('5.\nThe risk depends on the type of investment:\nCategorize the types of financing (Diagram 1).\nName two key points each.')
        d.save(r / 'question_catalogue.docx'); T.lecture_deck(r)
        _, plan, *_ = self.dry(r)
        practice = {q['label'].split('@')[0]: q['own_wording'] for q in plan['assessment_items'] if q['assessment_kind'] == 'PRACTICE'}
        self.assertEqual(sorted(practice), ['4', '5'])
        self.assertIn('Name all the mentioned aspects', practice['4']); self.assertIn('Categorize the types', practice['5'])

    def test_section_label_mismatch_is_not_evidence(self):
        r = F.random_root(self.d / 's')
        (r / 'a.md').write_text('# Kapitel 1: Pricing\n\n## Lernziele\n- Erklären Sie Preisstrategien für neue Produkte.\n\nPreisstrategien bestimmen Umsatz.\n')
        (r / 'b.md').write_text('# Kapitel 2: Funding\n\n## Lernziele\n- Erklären Sie Finanzierungsquellen für Gründungen.\n\nFinanzierungsquellen sind Eigen- und Fremdkapital.\n')
        (r / 'fragenkatalog.md').write_text('# Fragenkatalog\n\n## Session 1\n\n1. Erklären Sie Finanzierungsquellen für Gründungen und ihre Risiken.\n\n'
                                            '## Session 2\n\n2. Erklären Sie Finanzierungsquellen für Gründungen im Vergleich.\n')
        _, plan, *_ = self.dry(r)
        ch2 = next(c for c in plan['chapters'] if 'Funding' in c['title'])
        self.assertEqual(ch2['position'], 2); self.assertEqual(ch2['order_basis']['basis'], 'SOURCE_STATED_HEADING_NUMBER')
        items = {q['item_id']: q for q in plan['assessment_items']}
        s1 = next(q for q in items.values() if q.get('section_number') == 1); s2 = next(q for q in items.values() if q.get('section_number') == 2)
        self.assertIn(s1['item_id'], ch2['exam_relevance']['section_mismatch_item_ids'])
        self.assertNotIn(s2['item_id'], ch2['exam_relevance']['section_mismatch_item_ids'])
        cov = [r for r in plan['coverage'] if r['kc_id'] in ch2['kc_ids']]
        self.assertFalse(any(s1['item_id'] in r['evidence_item_ids'] for r in cov))
        self.assertTrue(any(s2['item_id'] in r['evidence_item_ids'] for r in cov))
        self.assertTrue(any('SECTION_MISMATCH' in x['reason'] for r in cov for x in r['rejected_links']))


    def test_page_section_label_applies_to_whole_page(self):
        r = F.random_root(self.d / 's')
        # the label is drawn BELOW the questions (reading order after them), as on real catalogue pages
        T.slide_pdf(r / 'question_catalogue.pdf', [
            {'title': 'Question Catalogue', 'raw': True, 'body': ['1. Name three forms of financing.', '2. Define insolvency.', 'Question Catalog Session 6']},
            {'title': 'Question Catalogue', 'raw': True, 'body': ['3. Name the parts of a plan.', 'Question Catalog Session 7']}])
        T.lecture_deck(r)
        _, plan, *_ = self.dry(r)
        sec = {q['own_wording'][:12]: q['section_number'] for q in plan['assessment_items'] if q['assessment_kind'] == 'PRACTICE'}
        self.assertEqual(sec, {'Name three f': 6, 'Define insol': 6, 'Name the par': 7})


if __name__ == '__main__':
    unittest.main()
