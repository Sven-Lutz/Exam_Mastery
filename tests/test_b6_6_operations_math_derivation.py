"""B6.6: competency operations from page content and decided questions, TeX rendering in HTML/PDF, and the limits of
numeric validation (arithmetic of written steps is not a correct derivation). Offline, synthetic fixtures only."""
import contextlib, io, json, shutil, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import slide_fixture as S
import p1p2_fixtures as F
import p3_fixtures as P
import test_p3_1_quality as T
from exam_mastery.curriculum import compile_curriculum, operations_in, topic_operations, SemanticDecisions, semantic_key
from exam_mastery.fidelity import inventory
from exam_mastery.derivation_check import check_steps
from exam_mastery.math_text import MathRenderer


def kc(plan, topic):
    return next(k for k in plan['competencies'] if topic in k['statement'])


class Operations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); d = Path(cls.tmp.name)
        cls.m = inventory(S.make(d / 'c'), d / 'inv')
        cls.p = compile_curriculum(cls.m)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_calculation_pages_demand_calculate(self):
        self.assertEqual(kc(self.p, 'Example: Second Round')['operations'], ['EXPLAIN', 'CALCULATE'])     # equation
        self.assertEqual(kc(self.p, 'Cap Table after Round 1')['operations'], ['EXPLAIN', 'CALCULATE'])   # totals row
        self.assertEqual(kc(self.p, 'How much must the investor pay?')['operations'], ['CALCULATE'])      # quantity question
        for k in [kc(self.p, 'Example: Second Round'), kc(self.p, 'Cap Table')]:
            self.assertTrue(all(e['basis'] for e in k['operation_evidence']))
            self.assertTrue(k['statement'].startswith('Erkläre/explain · Berechne/calculate: '))

    def test_figures_alone_or_charts_do_not_become_calculations(self):
        for t in ('Market Volume', 'Fund Facts', 'Valuation Basics', 'Top Reasons for Failure'):
            self.assertEqual(kc(self.p, t)['operations'], ['EXPLAIN'], t)

    def test_operation_wording_does_not_change_the_competency_id(self):
        k = kc(self.p, 'Example: Second Round')
        self.assertEqual(k['semantic_key'], semantic_key('Erkläre/explain: Example: Second Round'))

    def test_lexicon_multiple_operations_and_specific_verbs_win(self):
        self.assertEqual(operations_in('Name and explain the several exit events.'), ['RECALL', 'EXPLAIN'])
        self.assertEqual(operations_in('What are the (rounded) nominal shares?'), ['CALCULATE'])
        self.assertEqual(operations_in('What are the three reasons for insolvency?'), ['RECALL'])
        self.assertEqual(operations_in('How much money must the fund convert?'), ['CALCULATE'])
        self.assertEqual(operations_in('What is the definition of risk according to X?'), ['DEFINE'])
        self.assertEqual(operations_in('What is the post-money valuation?'), [])        # ambiguous: no guess
        ops, ev = topic_operations('Investment Terms', ['595,000 EUR as convertible loan', 'Interest rate of 6% p.a.'])
        self.assertEqual(ops, ['EXPLAIN'])

    def test_decided_recall_question_adds_recall_but_never_evidences_explain(self):
        k = kc(self.p, 'Top Reasons for Failure')
        q = next(q for q in self.p['assessment_items'] if 'reasons' in q['own_wording'])
        p2 = compile_curriculum(self.m, decisions=SemanticDecisions([
            {'kind': 'link', 'subject_id': k['kc_id'], 'value': [q['item_id']], 'decided_by': 'owner', 'rationale': 'list slide'},
            {'kind': 'operation', 'subject_id': q['item_id'], 'value': ['RECALL'], 'decided_by': 'owner', 'rationale': 'recall'}]))
        k2 = next(x for x in p2['competencies'] if x['kc_id'] == k['kc_id'])
        self.assertEqual(k2['operations'], ['EXPLAIN', 'RECALL'])
        self.assertIn(f"decided_link_to_item:{q['item_id']}", [e['basis'] for e in k2['operation_evidence']])
        row = next(r for r in p2['coverage'] if r['kc_id'] == k['kc_id'])
        self.assertEqual(row['status'], 'OPERATION_MISMATCH')
        self.assertEqual(row['evidence_item_ids'], []); self.assertIn(q['item_id'], row['recall_only_item_ids'])

    def test_decided_kc_operation_is_never_overridden(self):
        k = kc(self.p, 'Cap Table')
        p2 = compile_curriculum(self.m, decisions=SemanticDecisions([
            {'kind': 'operation', 'subject_id': k['kc_id'], 'value': ['EXPLAIN'], 'decided_by': 'owner', 'rationale': 'owner'}]))
        self.assertEqual(next(x for x in p2['competencies'] if x['kc_id'] == k['kc_id'])['operations'], ['EXPLAIN'])

    def test_other_subject_fixtures_keep_their_operations(self):
        for kind, expect in (('math', {'PROVE', 'DEFINE'}), ('law', {'SUBSUME'}), ('ml', {'DERIVE', 'IMPLEMENT'})):
            with self.subTest(kind=kind):
                m = inventory(F.make(kind, tempfile.mkdtemp(prefix='b66-')), Path(tempfile.mkdtemp(prefix='b66o-')) / 'inv')
                ops = {o for k in compile_curriculum(m)['competencies'] for o in k['operations']}
                self.assertTrue(expect & ops, (kind, ops))


class StepArithmetic(unittest.TestCase):
    def test_pass_fail_and_untested_are_distinguished(self):
        r = check_steps(['CON = 1/0,85*(0,15*7,700,000 € - 900,000 €) = 300,000 €', 'POM = 6 Mio € + 1.7 Mio € + CON',
                         r'\(\mathrm{NNC} = \frac{8\,\text{Mio €}}{6\,\text{Mio €}} \cdot 33{,}350\,\text{€} = 44{,}467\,\text{€}\)',
                         'Share = 25,000/44,467 = 56.22 %', 'wrong: 0.15 * 900,000 = 140,000'])
        self.assertEqual([x['status'] for x in r], ['PASS', 'NOT_TESTED', 'PASS', 'PASS', 'FAIL'])

    def test_a_correct_number_from_a_wrong_setup_still_passes_arithmetic_only(self):
        # wrong relation (pre-money share instead of post-money), arithmetic itself consistent: PASS is arithmetic only
        r = check_steps(['CON = 0.15 * 6,000,000 = 900,000'])
        self.assertEqual(r[0]['status'], 'PASS'); self.assertIn('arithmetic only', r[0]['detail'])


class NumericValueIsNotDerivation(T.Base):
    def test_wrong_intermediate_step_passes_value_checks_but_fails_step_arithmetic(self):
        # The P3.1 reference regression example carried S_xy = 26/3 for (0,2),(1,3),(3,7); the true value is 8.
        # G4.NUMERIC only recomputed (26/3)/(14/3) and passed. This is the gap between a correct number and a
        # correct calculation; G4.STEP_ARITHMETIC must catch it, and the set-up stays NOT_TESTED either way.
        import copy
        from exam_mastery.quality_gates import quality_report
        a, c, plan, m = self.ref('math')
        a = copy.deepcopy(a)
        s = next(x for x in a['solutions'] if x['solution_id'] == 's-calc')
        s['steps'][2]['statement'] = 'S_xy = (−4/3)(−2) + (−1/3)(−1) + (5/3)(3) = 26/3'
        s['steps'][3]['statement'] = 'b = (26/3)/(14/3) = 13/7, a = 4 − (13/7)(4/3) = 32/21'
        s['answer'] = 'b = 13/7 ≈ 1,857; a = 32/21 ≈ 1,524'
        s['numeric_checks'] = [{'expression': '(26/3)/(14/3)', 'expected': 13 / 7}, {'expression': '4 - (13/7)*(4/3)', 'expected': 32 / 21}]
        q = quality_report(a, c, plan, m)
        self.assertEqual(q['gates']['G4.NUMERIC']['status'], 'PASS')
        self.assertEqual(q['gates']['G4.ANSWER_CONSISTENCY']['status'], 'PASS')
        self.assertEqual(q['gates']['G4.STEP_ARITHMETIC']['status'], 'FAIL')
        self.assertEqual(q['machine_quality_status'], 'MACHINE_CHECKS_FAILED')
        self.assertIn(q['gates']['G4.DERIVATION_SETUP']['status'], ('NOT_TESTED', 'PENDING'))
        self.assertIn('NOT_VERIFIED', q['verification_scope']['subject_matter'])

    def test_corrected_example_passes_arithmetic_but_setup_stays_untested(self):
        from exam_mastery.quality_gates import quality_report
        q = quality_report(*self.ref('math'))
        steps = [f for f in q['findings'] if f['gate_id'] == 'G4.STEP_ARITHMETIC']
        self.assertFalse([f for f in steps if f['status'] == 'FAIL'])
        self.assertTrue([f for f in steps if f['status'] == 'PASS'])
        # symbolic steps are NOT_TESTED, so the gate is PENDING, never PASS
        self.assertEqual(q['gates']['G4.STEP_ARITHMETIC']['status'], 'PENDING')
        self.assertNotEqual(q['gates']['G4.DERIVATION_SETUP']['status'], 'PASS')


class MathRendering(unittest.TestCase):
    def test_html_svg_pdf_raster_and_visible_failure(self):
        d = Path(tempfile.mkdtemp(prefix='b66m-'))
        mr = MathRenderer(d)
        h = mr.html(r'Es gilt \(x^2 + y^2 = r^2\) und \[\frac{a}{b} = 7,700,000\]')
        self.assertEqual(h.count('<svg'), 2); self.assertIn('role="img"', h); self.assertIn('class="math-d"', h)
        rl = mr.rl(r'Es gilt \(x^2\)')
        self.assertIn('<img src=', rl); self.assertTrue(any(d.glob('*.png')))
        bad = mr.html(r'kaputt \(\frac{a}{\)')
        self.assertIn('math-fail', bad); self.assertIn(r'\frac{a}{', bad)
        rep = mr.report()
        self.assertEqual((rep['status'], rep['formulas_failed']), ('FAIL', 1))
        self.assertGreaterEqual(rep['formulas_rendered'], 3)

    def test_formula_group_at_page_end_moves_or_splits_instead_of_aborting(self):
        # Stage A 2026-11-06: a formula group at a page end aborted the PDF with 'Splitting error'.
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        d = Path(tempfile.mkdtemp(prefix='b66g-'))
        mr = MathRenderer(d / 'math'); st = ParagraphStyle('b', fontSize=10, leading=14)
        g = mr.flow('6. ' + 'Langer Rechenschritt mit Erläuterung. ' * 12 + r'\[V_{post} = V_{pre} + I\]', st)
        self.assertEqual(g.split(470, 5), [])                     # first part cannot fit: move, not abort
        self.assertGreater(len(g.split(470, 2000)), 1)
        flow = []
        for n in range(40):
            flow += [Paragraph(f'Block {n}', st), mr.flow(f'{n}. ' + 'Text ' * (20 + 7 * n % 60) + r'\[x_{%d} = \frac{a}{b}\]' % n, st)]
        SimpleDocTemplate(str(d / 'g.pdf')).build(flow)
        self.assertTrue((d / 'g.pdf').stat().st_size > 0)

    def test_published_chapter_renders_formulas_in_html_and_pdf(self):
        import pymupdf
        from exam_mastery.runtime import run_chapters
        from exam_mastery.chapter_publish import publish_chapter
        d = Path(tempfile.mkdtemp(prefix='b66p-'))
        root = F.make('math', str(d / 'm'))
        with contextlib.redirect_stdout(io.StringIO()):
            out, st = run_chapters(root, provider=P.SyntheticChapterModel(), output_base=d / 'runs')
        ch = next(c for c in sorted((out / 'chapters').iterdir()) if (c / 'content_ast.json').exists())
        ast = json.loads((ch / 'content_ast.json').read_text())
        ast['blocks'][0]['body'] = r'Normalgleichung \(A^\top A x = A^\top b\) sowie \[\hat{x} = (A^\top A)^{-1} A^\top b\]'
        (ch / 'content_ast.json').write_text(json.dumps(ast))
        manifest = inventory(root, d / 'inv')
        rep = publish_chapter(ch, manifest, None, verify_anki=False)
        self.assertEqual(rep['math_rendering']['status'], 'PASS'); self.assertGreaterEqual(rep['math_rendering']['formulas_rendered'], 2)
        # B9: kapitel.html typesets TeX with the bundled MathJax (works offline); the PDFs contain the typeset formulas
        art = ch / 'publish/artifacts'
        html = (art / 'kapitel.html').read_text()
        self.assertIn('assets/tex-svg-full.js', html); self.assertTrue((art / 'assets/tex-svg-full.js').is_file())
        for name in ('kapitel.pdf', '1_Lehrbuch.pdf'):
            text = ''.join(p.get_text() for p in pymupdf.open(art / name))
            self.assertNotIn(r'A^\top', text, name); self.assertNotIn(r'\(', text, name)
        self.assertGreaterEqual(sum(len(p.get_drawings()) for p in pymupdf.open(art / '1_Lehrbuch.pdf')), 2)


if __name__ == '__main__':
    unittest.main()
