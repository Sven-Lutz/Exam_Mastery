"""v0.21: chapter titles and merges for courses whose decks share a course-header title slide (found on a real
RL course: five lectures collapsed into one chapter, one lecture vanished into another by title overlap)."""
import unittest

from exam_mastery.curriculum import (SemanticDecisions, _course_header_titles, _full_title, _merge_chapters, _stem_title,
                                     _whole_deck)


def el(eid, text, kind='heading'):
    return {'element_id': eid, 'text': text, 'normalized_text': text, 'kind': kind}


class Titles(unittest.TestCase):
    def test_wrapped_title_is_joined(self):
        self.assertEqual(_full_title(el('h', 'Reinforcement Learning for'), [el('a', 'Large Language Models')]),
                         'Reinforcement Learning for Large Language Models')
        self.assertEqual(_full_title(el('h', 'Decision Making under Uncertainty -'), [el('a', 'The K-armed Bandit Problem')]),
                         'Decision Making under Uncertainty – The K-armed Bandit Problem')

    def test_complete_title_is_not_extended(self):
        self.assertEqual(_full_title(el('h', 'Value-Based Methods'), [el('a', 'Reinforcement Learning WS2025/26')]),
                         'Value-Based Methods')

    def test_stem_title_decodes_url_blanks_and_numbering(self):
        self.assertEqual(_stem_title('Lecture/10_20-_20Offline_20RL.pdf'), 'Offline RL')
        self.assertEqual(_stem_title('Lecture/14 Diffusion Part 1.pdf'), 'Diffusion Part 1')
        self.assertEqual(_stem_title('03 Entrepreneurial Marketing.pdf'), 'Entrepreneurial Marketing')

    def test_course_header_shared_by_different_decks_only(self):
        hdr = el('h', 'Reinforcement Learning WS 25/26 Prof. X')
        decks = [{'source_id': f's{i}', 'relative_path': p} for i, p in
                 enumerate(['09 - Imitation.pdf', '13 - Transformers.pdf', 'a/05 - PG.pdf', 'b/05 - PG.pdf'])]
        secs = {'s0': [(hdr, [], None)], 's1': [(hdr, [], None)],
                's2': [(el('p', 'Policy Gradients'), [], None)], 's3': [(el('q', 'Policy Gradients'), [], None)]}
        got = _course_header_titles(decks, secs)
        self.assertIn('reinforcement learning ws # # prof x', got)  # 46c45c6: headers compared without session numbers
        self.assertNotIn('policy gradients', got, 'two copies of one deck are versions, not a course header')


class Merges(unittest.TestCase):
    def chapter(self, cid, title, sid, text, status='SOURCE_UNIT'):
        return {'chapter_id': cid, 'title': title, 'source_ids': [sid], 'anchor_element_ids': [cid + '-a'], 'official': True,
                'segmentation': [{'source_id': sid, 'status': status, 'pages': [1, 9]}]}, {cid + '-a': {'normalized_text': text}}

    def run_merge(self, a, b):
        (ca, ba), (cb, bb) = a, b
        src_by = {s: {'authority': 'OFFICIAL_LECTURE'} for s in ca['source_ids'] + cb['source_ids']}
        return _merge_chapters([ca, cb], {}, {**ba, **bb}, src_by, SemanticDecisions())

    def test_two_whole_lecture_decks_with_subtopic_title_stay_separate(self):
        text = 'policy gradient likelihood ratio baseline variance return estimator'
        out, log = self.run_merge(self.chapter('c1', 'Policy Gradients', 's1', text),
                                  self.chapter('c2', 'Trust Regions for Policy Gradients', 's2', text + ' kl trust region'))
        self.assertEqual(len(out), 2)
        self.assertEqual(log[0]['decision'], 'SEMANTIC_REVIEW_REQUIRED')

    def test_split_sections_still_merge_on_title_and_content(self):
        text = 'policy gradient likelihood ratio baseline variance return estimator'
        out, log = self.run_merge(self.chapter('c1', 'Policy Gradients', 's1', text, 'SPLIT_AT_NUMBERED_DIVIDERS'),
                                  self.chapter('c2', 'Trust Regions for Policy Gradients', 's2', text))
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out[0]['segmentation']), 2, 'merged chapter keeps the segmentation of both members')

    def test_whole_deck(self):
        self.assertTrue(_whole_deck({'official': True, 'segmentation': [{'status': 'SOURCE_UNIT_WITH_SECTIONS'}]}))
        self.assertFalse(_whole_deck({'official': False, 'segmentation': [{'status': 'SOURCE_UNIT'}]}))


if __name__ == '__main__':
    unittest.main()


class PartTitles(unittest.TestCase):
    def test_merged_parts_drop_the_part_number(self):
        mk = lambda cid, title, sid: {'chapter_id': cid, 'title': title, 'source_ids': [sid], 'anchor_element_ids': [cid + '-a'],
                                      'official': True, 'segmentation': [{'source_id': sid, 'status': 'SOURCE_UNIT'}]}
        by = {'c1-a': {'normalized_text': 'diffusion score denoising'}, 'c2-a': {'normalized_text': 'diffusion score denoising'}}
        src = {'s1': {'authority': 'OFFICIAL_LECTURE'}, 's2': {'authority': 'OFFICIAL_LECTURE'}}
        out, _ = _merge_chapters([mk('c1', 'Diffusion Part 1', 's1'), mk('c2', 'Diffusion Part 2', 's2')], {}, by, src, SemanticDecisions())
        self.assertEqual([c['title'] for c in out], ['Diffusion'])


class Versions(unittest.TestCase):
    def setUp(self):
        from exam_mastery.triage import _term_key, _version_pass
        self.tk, self.vp = _term_key, _version_pass

    def test_term_key(self):
        self.assertEqual(self.tk('Reinforcement Learning WS2026/27 Prof.'), 2026.5)
        self.assertEqual(self.tk('SoSe 2025'), 2025.0)
        self.assertIsNone(self.tk('Optimal Sequential Decision Making'))

    def manifest(self, t1, t2):
        els = [{'element_id': 'e1', 'text': t1}, {'element_id': 'e2', 'text': t2}]
        srcs = [{'source_id': 'a', 'relative_path': '02 - MDP.pdf', 'element_ids': ['e1']},
                {'source_id': 'b', 'relative_path': 'Lecture/02 - MDP.pdf', 'element_ids': ['e2']}]
        roles = {s['source_id']: {'role': 'ACADEMIC_CONTENT', 'evidence': []} for s in srcs}
        self.vp({'sources': srcs}, roles, {e['element_id']: e for e in els})
        return roles

    def test_newest_term_teaches(self):
        r = self.manifest('MDPs WS2026/27', 'MDPs WS2025/26')
        self.assertEqual(r['a']['role'], 'ACADEMIC_CONTENT')
        self.assertEqual((r['b']['role'], r['b']['superseded_by']), ('SUPERSEDED_VERSION', 'a'))

    def test_no_term_evidence_decides_nothing(self):
        r = self.manifest('MDPs', 'MDPs again')
        self.assertEqual({x['role'] for x in r.values()}, {'ACADEMIC_CONTENT'})
        self.assertTrue(all(any(e['signal'] == 'version_variants' for e in x['evidence']) for x in r.values()))
