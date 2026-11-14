"""P3.3: source-role triage, KC quality, segmentation, scan/visual propagation, question kinds, domain profile,
pilot eligibility. Offline, random roots, no provider."""
import contextlib, io, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
import p3_3_fixtures as T
from exam_mastery.chapters import dry_run
from exam_mastery.runtime import run_chapters


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def root(self):
        return F.random_root(self.d / 'src')

    def dry(self, root, name='o'):
        rep, plan, m, gates, actions = dry_run(root, self.d / name)
        return rep, plan, m, gates, actions

    def role(self, plan, m, path):
        sid = next(s['source_id'] for s in m['sources'] if s['relative_path'] == path)
        return plan['source_roles'][sid]['role']


class Roles(Base):
    def test_templates_and_admin_never_become_chapters(self):
        r = self.root(); T.templates(r); T.admin_briefing(r); T.lecture_deck(r)
        rep, plan, m, gates, _ = self.dry(r)
        self.assertEqual(self.role(plan, m, 'Template_Presentation.pptx'), 'TEMPLATE_LAYOUT')
        self.assertEqual(self.role(plan, m, 'Vorlage_Hausarbeit.docx'), 'TEMPLATE_LAYOUT')
        self.assertEqual(self.role(plan, m, 'organisation_slides.pdf'), 'COURSE_ADMINISTRATION')
        self.assertEqual(self.role(plan, m, 'lecture_markets.pdf'), 'ACADEMIC_CONTENT')
        titles = [c['title'] for c in rep['chapters']]
        self.assertEqual(len(titles), 1, titles); self.assertIn('Market Dynamics', titles[0])
        self.assertFalse(any('Sample headline' in t or 'Chapter heading' in t for t in titles))
        self.assertFalse(any('ELIGIBLE' == c['academic_pilot_eligibility'] and 'Template' in c['title'] for c in rep['chapters']))
        self.assertTrue(all(len(m['sources']) == len(rep['triage']['source_roles']) for _ in [0]))   # nothing dropped
        ev = plan['source_roles'][next(s['source_id'] for s in m['sources'] if s['relative_path'] == 'Template_Presentation.pptx')]['evidence']
        self.assertTrue(any(e['signal'] == 'placeholder_text' and e.get('element_id') for e in ev))

    def test_placeholder_text_without_template_filename_is_detected(self):
        r = self.root()
        from docx import Document
        d = Document(); d.add_heading('Headline', 1); d.add_paragraph('Sample text: Arial 24pt bold. Lorem ipsum dolor.'); d.save(r / 'handout.docx')
        rep, plan, m, _, _ = self.dry(r)
        self.assertEqual(self.role(plan, m, 'handout.docx'), 'TEMPLATE_LAYOUT')

    def test_template_name_without_placeholders_is_review_not_silent(self):
        r = self.root(); (r / 'template_notes.md').write_text('# Kostenrechnung\n\nFixkosten und variable Kosten bestimmen den Gewinn je Einheit genau.\n')
        rep, plan, m, _, _ = self.dry(r)
        self.assertEqual(self.role(plan, m, 'template_notes.md'), 'REVIEW_REQUIRED')
        self.assertTrue(any(q['kind'] == 'SOURCE_ROLE' and q['priority'] == 'P1' for q in rep['triage']['review_queue']))


class KcQuality(Base):
    def test_no_kc_inflation_from_footers_citations_numbers_duplicates(self):
        r = self.root(); T.inflation_deck(r)
        rep, plan, m, _, _ = self.dry(r)
        st = [k['statement'] for k in plan['competencies']]
        self.assertFalse(any('Footer' in s or 'Smith' in s or 'References' in s or s.endswith(': 2') or '(€' in s for s in st), st)
        self.assertEqual(sum('Funding Sources' in s for s in st), 1)                    # repeated title -> one cluster
        fs = next(k for k in plan['competencies'] if 'Funding Sources' in k['statement'])
        self.assertGreaterEqual(len(fs['source_anchor_ids']), 3)
        rej = {r['reason'] for r in plan['rejected_kc_candidates']}
        self.assertTrue({'DUPLICATE_MERGED', 'NON_CONTENT_PAGE'} <= rej, rej)
        self.assertLessEqual(len(plan['competencies']), 9)                              # <= pages, not spans
        self.assertTrue(all(k['origin'] == 'slide_title_topic' and k['inferred'] for k in plan['competencies']))

    def test_objective_slide_bullets_become_stated_objectives(self):
        r = self.root()
        T.lecture_deck(r, extra={2: {'title': 'Learning objectives', 'body': ['- Calculate the break-even point of a venture', '- Explain pricing strategies']}})
        _, plan, _, _, _ = self.dry(r)
        stated = [k for k in plan['competencies'] if k['origin'] == 'stated_learning_objective']
        self.assertEqual(len(stated), 2); self.assertIn('CALCULATE', stated[0]['operations'] + stated[1]['operations'])
        self.assertFalse(any('Learning objectives' in k['statement'] for k in plan['competencies']))


class Segmentation(Base):
    def test_split_only_at_explicit_chapter_dividers_else_review(self):
        r = self.root()
        pages = [{'title': 'Course Pack Economics'}, {'title': 'Part 1: Supply and Demand'}] + \
                [{'title': f'Demand curve {i}', 'body': T.BODY} for i in range(3)] + [{'title': 'Part 2: Market Entry'}] + \
                [{'title': f'Entry barrier {i}', 'body': T.BODY} for i in range(3)]
        T.slide_pdf(r / 'pack.pdf', pages)
        bare = [{'title': 'Customer Development'}, {'title': '1. Starting point'}] + [{'title': f'Interview {i}', 'body': T.BODY} for i in range(3)] + \
               [{'title': '2. Harvest findings'}] + [{'title': f'Synthesis {i}', 'body': T.BODY} for i in range(3)]
        T.slide_pdf(r / 'process.pdf', bare)
        rep, plan, m, _, _ = self.dry(r)
        titles = sorted(c['title'] for c in plan['chapters'])
        self.assertIn('Part 1: Supply and Demand', titles); self.assertIn('Part 2: Market Entry', titles)
        proc = [c for c in plan['chapters'] if 'Customer Development' in c['title']]
        self.assertEqual(len(proc), 1)
        self.assertEqual(proc[0]['segmentation'][0]['status'], 'NUMBERED_SECTIONS_SEMANTIC_REVIEW_REQUIRED')
        rep2, plan2, *_ = self.dry(r, 'again')
        self.assertEqual([c['chapter_id'] for c in plan['chapters']], [c['chapter_id'] for c in plan2['chapters']])   # stable
        anchored = {e for c in plan['chapters'] for e in c['source_package']['element_ids']}
        lost = [e['element_id'] for e in m['elements'] if e['source_id'] in {s['source_id'] for s in m['sources']}
                and e['kind'] in ('heading', 'paragraph') and e['element_id'] not in anchored]
        self.assertEqual(lost, [])                                                   # no silent loss of text


class Propagation(Base):
    def test_textless_page_blocks_only_dependents_and_is_accounted(self):
        r = self.root(); T.lecture_deck(r, n=12, scan_page=6)
        rep, plan, m, gates, _ = self.dry(r)
        g = gates[plan['chapters'][0]['chapter_id']]
        self.assertTrue(g['producible_kc_ids'])                                     # not a global block
        near = {k for k, v in g['review_required_kcs'].items() if 'ADJACENT_PAGE_UNREADABLE' in v}
        self.assertEqual(len(near), 2)                                              # pages 5 and 7
        self.assertTrue(any(f['code'] == 'UNREADABLE_PAGE_RELEVANCE_UNKNOWN' for f in g['findings']))
        acc = rep['triage']['gap_accounting']
        self.assertEqual(acc['total_gaps'], len(m['gaps'])); self.assertEqual(acc['accounted'], len(m['gaps']))
        scan = next(x for x in acc['gaps'] if x['code'] == 'TEXT_LAYER_MISSING')
        self.assertEqual(scan['page'], 6); self.assertEqual(scan['scope'], 'LOCAL'); self.assertEqual(len(scan['kc_ids']), 2)
        self.assertNotEqual(rep['chapters'][0]['academic_pilot_eligibility'], 'ELIGIBLE')

    def test_visual_classes(self):
        r = self.root()
        T.lecture_deck(r, extra={3: {'title': 'Market size chart', 'body': ['Bars'], 'chart_paths': 40},
                                 4: {'title': 'Customer photo analysis', 'body': T.BODY, 'image': (380, 300)},
                                 5: {'title': 'Small logo slide', 'body': T.BODY, 'image': (20, 15)}})
        rep, plan, m, gates, _ = self.dry(r)
        g = gates[plan['chapters'][0]['chapter_id']]
        kc = {k['statement'].split(': ', 1)[1]: k['kc_id'] for k in plan['competencies']}
        self.assertIn('ESSENTIAL_VISUAL_UNRESOLVED', g['blocked_kcs'].get(kc['Market size chart'], []))      # chart page, little text
        self.assertIn('VISUAL_RELEVANCE_UNKNOWN', g['review_required_kcs'].get(kc['Customer photo analysis'], []))
        self.assertNotIn(kc['Small logo slide'], g['blocked_kcs']); self.assertNotIn(kc['Small logo slide'], g['review_required_kcs'])
        self.assertGreater(g['decorative_visual_candidates'], 0)                    # template lines
        acc = rep['triage']['gap_accounting']
        self.assertTrue(any(x['effect'] == 'NONE_DECORATIVE_CANDIDATE' for x in acc['gaps']))
        self.assertTrue(any(q['kind'] == 'DECORATIVE_SAMPLE' for q in rep['triage']['review_queue']))   # decoration is sampled, not trusted


class Questions(Base):
    def test_lecture_question_vs_practice_vs_exam(self):
        r = self.root(); T.question_catalogue(r)
        T.lecture_deck(r, extra={4: {'title': 'Value proposition', 'body': ['What is a value proposition?'] + T.BODY}})
        (r / 'klausur.md').write_text('# Klausur\n\nAufgabe 1\nBerechnen Sie den Break-even-Punkt bei Fixkosten 1000 und Marge 20. (5 P)\n')
        rep, plan, m, _, _ = self.dry(r)
        kinds = {}
        for q in plan['assessment_items']:
            kinds.setdefault(q['assessment_kind'], []).append(q)
        self.assertEqual(self.role(plan, m, 'question_catalogue.pdf'), 'PRACTICE_QUESTIONS')
        self.assertGreaterEqual(len(kinds['PRACTICE']), 6)
        self.assertTrue(all(q['points'] is None and q['points_basis'] == 'NOT_STATED' for q in kinds['PRACTICE']))
        lq = kinds['LECTURE_QUESTION']; self.assertTrue(lq and all(not q['evidence_eligible'] for q in lq))
        self.assertEqual([q['points'] for q in kinds['OFFICIAL_EXAM']], [5.0])
        for c in plan['chapters']:
            self.assertEqual(c['exam_relevance']['points'], sum(q['points'] for q in kinds['OFFICIAL_EXAM'] if q['item_id'] in c['exam_relevance']['linked_item_ids']))
        self.assertFalse([c for c in plan['chapters'] if 'Question Catalogue' in c['title']])


class DomainAndEligibility(Base):
    def test_business_profile_and_eligible_chapter(self):
        r = T.business_course(self.root())
        rep, plan, m, gates, _ = self.dry(r)
        self.assertIn('business_economics', plan['domain_profile']['active_profiles'])
        self.assertNotIn('law', plan['domain_profile']['active_profiles'])
        c = rep['chapters'][0]
        self.assertEqual(c['academic_pilot_eligibility'], 'ELIGIBLE', c['eligibility_reasons'])
        self.assertEqual(c['academic_release'], 'NOT_TESTED')
        self.assertEqual(self.role(plan, m, 'uebungsfragen.md'), 'PRACTICE_QUESTIONS')

    def test_contrasting_profiles_unchanged(self):
        for kind, prof in (('math', 'formal_mathematics'), ('law', 'law'), ('ml', 'computing')):
            _, plan, *_ = self.dry(F.make(kind, str(self.d / kind)), kind)
            self.assertIn(prof, plan['domain_profile']['active_profiles'], kind)
            self.assertNotIn('business_economics', plan['domain_profile']['active_profiles'], kind)

    def test_single_word_does_not_make_a_profile(self):
        r = self.root(); T.lecture_deck(r, extra={3: {'title': 'Legal claim', 'body': ['Ein Anspruch kann entstehen.'] + T.BODY}})
        T.lecture_deck(r, name='second.pdf')
        _, plan, *_ = self.dry(r)
        self.assertNotIn('law', plan['domain_profile']['active_profiles'])

    def test_inferred_only_chapter_pending_and_ineligible_selection_zero_calls(self):
        r = self.root(); T.lecture_deck(r)
        (r / 'refs.md').write_text('# References\n\nSmith, J. (2015). Finance basics. Doe, A. (2019). Startups and more.\n')
        rep, plan, m, gates, _ = self.dry(r)
        lec = next(c for c in rep['chapters'] if 'Market' in c['title'])
        self.assertEqual(lec['academic_pilot_eligibility'], 'PENDING_REVIEW')
        self.assertTrue(any('only inferred topic candidates' in x for x in lec['eligibility_reasons']))
        refs = next((c for c in rep['chapters'] if c['title'] == 'References'), None)
        if refs:
            self.assertEqual(refs['academic_pilot_eligibility'], 'INELIGIBLE')
            model = P.SyntheticChapterModel()
            with contextlib.redirect_stdout(io.StringIO()):
                _, st = run_chapters(r, provider=model, output_base=self.d / 'runs', only_chapter=refs['chapter_id'])
            self.assertEqual(model.calls, []); self.assertIn(st['run_state'], ('SELECTED_CHAPTER_BLOCKED', 'SELECTED_CHAPTER_INELIGIBLE'))


@unittest.skipUnless(os.environ.get('EM_REAL_COURSE'), 'set EM_REAL_COURSE=<course root> to run the local real-course regression')
class RealCourseLocal(Base):
    """Opt-in: reads a real course read-only; asserts only generic invariants, no course content."""
    def test_real_course_invariants(self):
        root = Path(os.environ['EM_REAL_COURSE'])
        with patch('exam_mastery.providers.execute', side_effect=AssertionError('provider')), \
                patch('socket.socket.connect', side_effect=AssertionError('net')):
            rep, plan, m, gates, _ = self.dry(root, 'real')
        bad = [c for c in rep['chapters'] if c['academic_pilot_eligibility'] == 'ELIGIBLE' and
               any(plan['source_roles'][s]['role'] != 'ACADEMIC_CONTENT' for s in c['source_ids'])]
        self.assertEqual(bad, [])
        self.assertFalse([c for c in rep['chapters'] if any(x in c['title'] for x in ('Sample headline', 'Chapter heading'))])
        self.assertEqual(rep['triage']['gap_accounting']['accounted'], len(m['gaps']))
        self.assertFalse([k for k in plan['competencies'] if k['origin'] == 'heading_topic' and len(k['statement']) > 140])


if __name__ == '__main__':
    unittest.main()
