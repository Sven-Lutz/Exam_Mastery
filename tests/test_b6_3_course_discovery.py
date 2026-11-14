"""B6.3: stable course discovery. Discovery -> source classification -> curriculum mapping -> question linking.
Generated courses only (no real course data). New documents, sub-folders, file order, duplicates and Office lock files
must not move evidence-based session identities; unclear cases are blocked, never assigned silently."""
import json, shutil, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import p3_3_fixtures as T
from exam_mastery.chapters import dry_run, production_preflight
from exam_mastery import fidelity

TOPICS = ['Entrepreneurship Introduction', 'Pricing Strategy', 'Funding and Investors', 'Team Leadership']        # chapter titles
ROWS = ['Introduction and Basic Concepts', 'Pricing Strategy', 'Funding and Investors', 'Team Leadership']  # schedule rows
LECTURE = '''# {t}

## Lernziele
- Erklären Sie {t} anhand eines Beispiels.
- Nennen Sie die wichtigsten Begriffe zu {t}.

{t} ist ein zentrales Thema dieser Sitzung. {body}
'''
BODY = {'Entrepreneurship Introduction': 'Opportunities arise from market changes and new technology; basic concepts of entrepreneurship.',
        'Pricing Strategy': 'Pricing reflects willingness to pay, costs and competition.',
        'Funding and Investors': 'Funding comes from founders, business angels and venture capital investors.',
        'Team Leadership': 'Team leadership aligns roles, motivation and decisions in a start-up.'}


def course_info(root, name='course_information.docx'):
    from docx import Document
    d = Document(); d.add_heading('Course Information', 1)
    for ln in ('Exam date: Monday 12:00, Room 101', 'Registration via ILIAS until the deadline', 'Office hours on request',
               '6 ECTS credit points', 'Contact: office@uni.example'):
        d.add_paragraph(ln)
    t = d.add_table(rows=1, cols=2); t.rows[0].cells[0].text = 'Date'; t.rows[0].cells[1].text = 'Topics of the lecture'
    r = t.add_row(); r.cells[0].text = '18:30 case presentations'; r.cells[1].text = ''          # note row without topic
    for i, topic in enumerate(ROWS):
        r = t.add_row(); r.cells[0].text = f'{i + 1:02d}/11'; r.cells[1].text = topic
    d.save(Path(root) / name)


def catalogue(root):
    lines = ['# Question Catalogue', '']
    qs = {1: ['What is an entrepreneurial opportunity?', 'How does opportunity recognition work?'],
          2: ['Name three pricing strategies.', 'Explain willingness to pay in pricing.'],
          3: ['Name the funding sources of a start-up.', 'Explain the role of business angels and venture capital investors.',
              'Compare founders funding and investors funding.'],
          4: ['Explain team leadership in a start-up.', 'Name the roles in a start-up team.']}
    n = 1
    for s, items in qs.items():
        lines += [f'## Session {s}', '']
        for q in items:
            lines.append(f'{n}. {q}'); n += 1
        lines.append('')
    (Path(root) / 'question_catalogue.md').write_text('\n'.join(lines), encoding='utf-8')


def submission(path, variant=0):
    from docx import Document
    d = Document()                                    # like a real submission: no title style, H1 sections
    for ln in ('Funding Case Study', 'Written submission for the lecture', 'Submitted by: Student A', 'Matrikel-Nr: 0000000', 'Examiner: Prof. Example',
               'Table of contents', 'List of figures'):
        d.add_paragraph(ln)
    d.add_heading('', 1)                              # empty first heading, as in real submissions from a template
    for h, body in (('Introduction', 'This case study analyses the funding of a start-up and its investors.'),
                    ('Financing Analysis', 'The company raised money from business angels and venture capital investors.'),
                    ('Discussion', 'Funding choices depend on risk, control and timing.' + (' Revised.' if variant else '')),
                    ('Bibliography', 'Smith, J. (2015). Finance basics.'), ('Affidavit', 'I declare that I wrote this work myself.')):
        d.add_heading(h, 1); d.add_paragraph(body)
    Path(path).parent.mkdir(parents=True, exist_ok=True); d.save(path)


def build(root, names=None):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    names = names or [f'{i + 1:02d}_lecture.md' for i in range(len(TOPICS))]
    for n, t in zip(names, TOPICS):
        (root / n).write_text(LECTURE.format(t=t, body=BODY[t]), encoding='utf-8')
    course_info(root); catalogue(root)
    return root


def mapping(root, out):
    rep, plan, m, gates, _ = dry_run(root, out)
    by_title = {c['title']: c for c in plan['chapters']}
    items = {q['item_id']: q for q in plan['assessment_items']}
    res = {}
    for t in TOPICS:
        c = by_title.get(t)
        if c is None:
            res[t] = None; continue
        er = c['exam_relevance']
        res[t] = {'session': er['section_number'], 'basis': er.get('session_basis'),
                  'own_items': sorted(items[q]['own_wording'] for q in er['linked_item_ids'] + er['section_unlinked_item_ids']
                                      if items[q].get('section_number') == er['section_number']),
                  'mismatch': len(er['section_mismatch_item_ids'])}
    return res, plan, m, gates


class StableDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.base, self.plan0, self.m0, _ = mapping(build(self.d / 'a'), self.d / 'out_a')

    def tearDown(self):
        self.tmp.cleanup()

    def test_01_baseline_session_identity_from_schedule_evidence(self):
        self.assertEqual([self.base[t]['session'] for t in TOPICS], [1, 2, 3, 4])      # note row without topic is not a session
        self.assertEqual({self.base[t]['basis'] for t in TOPICS}, {'SOURCE_STATED_SCHEDULE_TABLE'})
        self.assertEqual(len(self.base['Funding and Investors']['own_items']), 3)

    def test_01b_item_derived_competency_sits_in_the_chapter_of_its_session(self):
        # B12 invariant: a competency created from an item's wording never sits in a chapter of another session
        items = {q['item_id']: q for q in self.plan0['assessment_items']}
        ses = {c['chapter_id']: c['exam_relevance']['section_number'] for c in self.plan0['chapters']}
        for k in self.plan0['competencies']:
            if k.get('chapter_assignment_basis') in ('lexical_overlap_inferred', 'item_session_matches_chapter_session') and ses.get(k['chapter_id']):
                secs = {items[q].get('section_number') for q in k.get('linked_item_ids', []) if q in items} - {None}
                if secs:
                    self.assertIn(ses[k['chapter_id']], secs, k['statement'])

    def test_02_case_study_submissions_root_subfolder_variant_and_export_do_not_move_sessions(self):
        r = build(self.d / 'b')
        submission(r / 'Case_Study.docx'); submission(r / 'Case Study' / 'Case_Study_v2.docx', variant=1)
        T.slide_pdf(r / 'Case Study' / 'Case_Study_export.pdf', [
            {'title': 'Funding Case Study', 'body': ['Written submission for the lecture', 'Examiner: Prof. Example', 'Table of contents', 'Affidavit'], 'raw': True},
            {'title': 'Funding and Investors', 'body': ['The company raised money from business angels and venture capital investors.'], 'raw': True},
            {'title': 'Bibliography', 'body': ['Smith, J. (2015). Finance basics.'], 'raw': True}])
        res, plan, m, _ = mapping(r, self.d / 'out_b')
        self.assertEqual(res, self.base)                                                     # sessions and question sets unchanged
        cls = {s['relative_path']: plan['source_classification']['sources'][s['source_id']] for s in m['sources']}
        for p in ('Case_Study.docx', 'Case Study/Case_Study_v2.docx', 'Case Study/Case_Study_export.pdf'):
            self.assertEqual(cls[p]['category'], 'CASE_STUDY_ASSIGNMENT', p)
            self.assertTrue(cls[p]['evidence'])
        self.assertTrue(any(v['similarity'] >= 0.8 for v in cls['Case Study/Case_Study_v2.docx']['variants']))
        self.assertFalse(any(c['title'] in ('Introduction', 'Discussion', 'Bibliography') for c in plan['chapters']))
        self.assertEqual(cls['01_lecture.md']['category'], 'OFFICIAL_LECTURE')
        self.assertEqual(cls['question_catalogue.md']['category'], 'EXERCISE_QUESTIONS')

    def test_03_file_names_and_order_do_not_matter(self):
        res, *_ = mapping(build(self.d / 'c', names=['zz_late.md', 'aa_first.md', 'mm_mid.md', 'b_b.md']), self.d / 'out_c')
        self.assertEqual(res, self.base)

    def test_04_exact_duplicate_in_subfolder_is_recorded_not_a_second_chapter(self):
        r = build(self.d / 'e'); (r / 'copy').mkdir(); shutil.copy(r / '03_lecture.md', r / 'copy' / '03_lecture.md')
        res, plan, m, _ = mapping(r, self.d / 'out_e')
        self.assertEqual(res, self.base)
        dup = next(s for s in m['sources'] if s['relative_path'] == 'copy/03_lecture.md')
        self.assertTrue(any(x['kind'] == 'duplicate_of' for x in dup['relationships']))
        self.assertEqual(plan['source_classification']['sources'][dup['source_id']]['category'], 'DUPLICATE')

    def test_05_open_office_lock_file_is_ignored_and_not_an_integrity_change(self):
        r = build(self.d / 'f'); (r / '~$se_Study.docx').write_bytes(b'\x00owner-lock')
        (r / '.~lock.notes.odt#').write_text('lock'); (r / '._01_lecture.md').write_bytes(b'\x00\x05\x16\x07')
        res, plan, m, _ = mapping(r, self.d / 'out_f')
        self.assertEqual(res, self.base)
        for name in ('~$se_Study.docx', '.~lock.notes.odt#', '._01_lecture.md'):
            s = next(s for s in m['sources'] if s['relative_path'] == name)
            self.assertEqual(s['status'], 'ignored_temporary')
            self.assertEqual(plan['source_classification']['sources'][s['source_id']]['category'], 'SYSTEM_IGNORED')
        self.assertFalse([g for g in m['gaps'] if g['code'] == 'PARSE_FAILED'])
        snap = fidelity._snapshot(r); (r / '~$other.docx').write_bytes(b'x')
        self.assertEqual(fidelity._snapshot(r), snap)                                         # a lock file appearing is no source change

    def test_06_unrelated_new_lecture_does_not_shift_and_does_not_block(self):
        r = build(self.d / 'g')
        (r / 'extra_guest_talk.md').write_text(LECTURE.format(t='Guest Talk on Sustainability', body='Sustainability matters for ventures.'), encoding='utf-8')
        res, plan, m, gates = mapping(r, self.d / 'out_g')
        self.assertEqual(res, self.base)
        cid = next(c['chapter_id'] for c in plan['chapters'] if c['title'] == 'Funding and Investors')
        pf = production_preflight(plan, gates, [cid])['chapters'][cid]
        self.assertFalse({'COURSE_ORDER_UNRESOLVED', 'SESSION_IDENTITY_UNRESOLVED'} & {o['code'] for o in pf['open']})

    def test_07_ambiguous_new_document_blocks_only_the_affected_session(self):
        r = build(self.d / 'h')
        # equally good match for the 'Funding and Investors' schedule row, but not the same title (no M1 merge)
        (r / 'notes_funding.md').write_text('# Funding Investors Overview\n\nSeed rounds, term sheets, valuation caps and liquidation '
                                            'preferences in later financing rounds.\n', encoding='utf-8')   # different content: no M2 merge
        res, plan, m, gates = mapping(r, self.d / 'out_h')
        funding = [c for c in plan['chapters'] if c['title'] in ('Funding and Investors', 'Funding Investors Overview')]
        self.assertEqual(len(funding), 2)
        for c in funding:                                                                  # no silent winner
            self.assertIsNone(c['exam_relevance']['section_number'])
            pf = production_preflight(plan, gates, [c['chapter_id']])['chapters'][c['chapter_id']]
            self.assertIn('SESSION_IDENTITY_UNRESOLVED', {o['code'] for o in pf['open']})
        self.assertEqual([res[t]['session'] for t in ('Entrepreneurship Introduction', 'Pricing Strategy', 'Team Leadership')], [1, 2, 4])
        conflicts = plan['chapter_ordering']['session_conflicts']
        self.assertTrue(any('Funding and Investors' in json.dumps(x) for x in conflicts))

    def test_08_changed_session_assignment_invalidates_bound_approvals(self):
        from exam_mastery import review_decisions as D
        cid = next(c['chapter_id'] for c in self.plan0['chapters'] if c['title'] == 'Funding and Investors')
        data = {'schema': D.SCHEMA, 'decision_set_id': 's', 'decisions': [{'decision_id': 'x', 'chapter_id': cid}], 'sources': []}
        h0 = D.content_hashes(data, self.plan0)['decisions']['x']
        r = build(self.d / 'i'); (r / 'notes_funding.md').write_text(LECTURE.format(t='Funding and Investors', body='Other.'), encoding='utf-8')
        _, plan1, _, _ = mapping(r, self.d / 'out_i')
        self.assertNotEqual(D.content_hashes(data, plan1)['decisions']['x'], h0)


    def test_09_research_brief_and_literature_list_are_classified_not_chapters(self):
        r = build(self.d / 'j'); (r / 'material').mkdir()
        (r / 'material' / 'brief.md').write_text('# Company X - Research brief\n\nCase study material\n\n## Executive Summary\n\nThree patent families.\n\n'
                                                 '## Inhaltsverzeichnis\n\n1. Scope\n\n## Appendix\n\nTables.\n', encoding='utf-8')
        (r / 'material' / 'reading.md').write_text('# Reading list\n\n' + '\n'.join(
            f'- Author{i}, A. ({2000 + i}). Title {i}. doi:10.1000/{i}' for i in range(8)), encoding='utf-8')
        res, plan, m, _ = mapping(r, self.d / 'out_j')
        self.assertEqual(res, self.base)
        cls = {s['relative_path']: plan['source_classification']['sources'][s['source_id']] for s in m['sources']}
        self.assertEqual(cls['material/brief.md']['category'], 'CASE_STUDY_ASSIGNMENT')
        self.assertEqual(cls['material/reading.md']['category'], 'REFERENCE_LITERATURE')
        self.assertFalse(any(c['title'] in ('Executive Summary', 'Reading list') for c in plan['chapters']))


    def test_10_empty_topic_cell_from_a_pdf_table_is_not_a_session(self):
        from exam_mastery.fidelity import inventory
        from exam_mastery.curriculum import compile_curriculum
        r = build(self.d / 'k'); m = inventory(r, self.d / 'out_k')
        t = next(e for e in m['elements'] if e['kind'] == 'table' and 'Topics' in str((e.get('structure') or {}).get('rows')))
        t['structure']['rows'][1] = [t['structure']['rows'][1][0], None]          # PDF tables yield None, not ''
        plan = compile_curriculum(m, self.d / 'out_k2')
        got = {c['title']: c['exam_relevance']['section_number'] for c in plan['chapters']}
        self.assertEqual([got[x] for x in TOPICS], [1, 2, 3, 4])

    def test_11_case_study_slides_derived_from_written_work(self):
        def slides(path):
            T.slide_pdf(path, [{'title': 'Entrepreneurship Introduction Kamedo GmbH', 'body': ['Student team presentation'], 'raw': True},
                               {'title': 'Financing Analysis', 'body': ['The company raised money from business angels and venture capital investors.',
                                                                        'Funding choices depend on risk, control and timing.'], 'raw': True},
                               {'title': 'Discussion', 'body': ['This analysis covers the funding of a start-up and its investors.',
                                                                'I declare that I wrote this work myself.'], 'raw': True}])
        r = build(self.d / 'l'); submission(r / 'Case Study' / 'Kamedo_report.docx')
        slides(r / 'Case Study' / 'KamedoCaseStudy_slides.pdf')                  # work signal only in the path
        slides(r / 'Case Study' / 'KamedoCaseStudy_slides_export.pdf')           # its exported twin (near-identical variant)
        res, plan, m, _ = mapping(r, self.d / 'out_l')
        self.assertEqual(res, self.base)
        cls = {s['relative_path']: plan['source_classification']['sources'][s['source_id']] for s in m['sources']}
        c = cls['Case Study/KamedoCaseStudy_slides.pdf']
        self.assertEqual(c['category'], 'CASE_STUDY_ASSIGNMENT')
        self.assertEqual(cls['Case Study/KamedoCaseStudy_slides_export.pdf']['category'], 'CASE_STUDY_ASSIGNMENT')
        self.assertTrue(any(x['kind'] == 'NEAR_IDENTICAL_VARIANT' for x in c['variants']))
        self.assertTrue(any(e['signal'] == 'vocabulary_contained_in_case_study_work' for e in c['evidence']))
        r2 = build(self.d / 'l2'); submission(r2 / 'Case Study' / 'Kamedo_report.docx'); slides(r2 / 'talk.pdf')   # no work signal
        res2, plan2, m2, _ = mapping(r2, self.d / 'out_l2')
        c2 = next(plan2['source_classification']['sources'][s['source_id']] for s in m2['sources'] if s['relative_path'] == 'talk.pdf')
        self.assertEqual(c2['category'], 'OTHER_UNRESOLVED')
        self.assertTrue(any(e['signal'] == 'conflict' for e in c2['evidence']))

    def test_12_single_lecture_with_schedule_keeps_its_session(self):
        # B12: a folder with one lecture, the schedule and the catalogue (e.g. a copy for a one-chapter run)
        root = self.d / 'single'; root.mkdir()
        (root / '03_lecture.md').write_text(LECTURE.format(t='Funding and Investors', body=BODY['Funding and Investors']), encoding='utf-8')
        course_info(root); catalogue(root)
        cat = root / 'question_catalogue.md'          # another session's question sharing words with this lecture
        cat.write_text(cat.read_text(encoding='utf-8').replace('## Session 2\n\n', '## Session 2\n\n0. Name the seven ladder tiers, rebate schemes, bundling tactics and anchoring heuristics that founders choose.\n'), encoding='utf-8')
        res, _, _, _ = mapping(root, self.d / 'out_single')
        self.assertEqual(res['Funding and Investors']['session'], 3)
        self.assertEqual(res['Funding and Investors']['basis'], 'SOURCE_STATED_SCHEDULE_TABLE')
        self.assertEqual(len(res['Funding and Investors']['own_items']), 3)
        _, plan, _, _ = mapping(root, self.d / 'out_single2')
        kcs = {k['kc_id']: k for k in plan['competencies']}
        chap = next(c for c in plan['chapters'] if c['title'] == 'Funding and Investors')
        stmts = ' '.join(kcs[k]['statement'].lower() for k in chap['kc_ids'])
        for other in ('pricing', 'willingness', 'team leadership', 'opportunity', 'ladder'):
            self.assertNotIn(other, stmts)                         # questions of other sessions are not chapter content
        gap = next((c for c in plan['chapters'] if c['chapter_id'] == 'ch-exam-scope-unanchored'), None)
        self.assertIsNotNone(gap)                                  # ... they are a visible source gap instead

    def test_13_single_lecture_matched_by_two_schedule_rows_gets_no_session(self):
        root = self.d / 'twice'; root.mkdir()
        (root / '03_lecture.md').write_text(LECTURE.format(t='Funding and Investors', body=BODY['Funding and Investors']), encoding='utf-8')
        from docx import Document
        d = Document(); t = d.add_table(rows=1, cols=2); t.rows[0].cells[0].text = 'Date'; t.rows[0].cells[1].text = 'Topics of the lecture'
        for i, topic in enumerate(['Funding and Investors', 'Pricing Strategy', 'Funding and Investors II']):
            r = t.add_row(); r.cells[0].text = f'{i + 1:02d}/11'; r.cells[1].text = topic
        d.save(root / 'course_information.docx'); catalogue(root)
        res, _, _, _ = mapping(root, self.d / 'out_twice')
        self.assertIsNone(res['Funding and Investors']['session'])        # ambiguous: stays a review, never guessed


if __name__ == '__main__':
    unittest.main()
