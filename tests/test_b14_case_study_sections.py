"""B14: tasks on case-study / appendix pages of a question catalogue do not inherit the preceding session label, and a
layout-truncated copy of a task is not a second task (chapter 7 E2E: the Volocopter canvas task was mis-assigned to
Session 7 and blocked coverage and DR A1)."""
import unittest

from exam_mastery.curriculum import _question_items


def el(i, page, text, kind='paragraph'):
    return {'element_id': f'el-{i}', 'kind': kind, 'text': text, 'locator': {'page': page}, 'locator_str': f'src-q/page-{page}#{kind}-{i}'}


class CaseStudySections(unittest.TestCase):
    def items(self, elements):
        man = {'elements': elements}
        src = [{'source_id': 'src-q', 'authority': 'COURSE_MATERIAL', 'element_ids': [e['element_id'] for e in elements]}]
        return _question_items(man, src, {'src-q': {'role': 'PRACTICE_QUESTIONS'}})

    def test_case_study_pages_end_the_session(self):
        full = '1. Name the nine building blocks and fill out the Business Model Canvas for Volocopter with two aspects each.'
        q = self.items([el(1, 15, 'Session 7', 'heading'), el(2, 15, '3. Explain the effectuation principle of affordable loss in your words.'),
                        el(3, 18, 'CASE STUDY', 'heading'), el(4, 22, full),
                        el(5, 23, 'CASE STUDY - VOLOCOPTER APPENDIX', 'heading'), el(6, 23, full[:70])])
        by = {x['own_wording'][:20]: x for x in q}
        self.assertEqual(by['Explain the effectua']['section_number'], 7)
        vol = [x for x in q if 'Volocopter' in x['own_wording']]
        self.assertEqual(len(vol), 1)                          # truncated copy dropped
        self.assertIsNone(vol[0]['section_number'])            # not Session 7
        self.assertTrue(vol[0]['own_wording'].endswith('each.'))

    def test_session_label_still_applies_without_case_study(self):
        q = self.items([el(1, 3, 'Session 2', 'heading'), el(2, 3, '1. Describe the lean startup build-measure-learn loop in detail.')])
        self.assertEqual(q[0]['section_number'], 2)


if __name__ == '__main__':
    unittest.main()
