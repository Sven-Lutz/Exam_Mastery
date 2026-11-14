"""B6.7: exact step arithmetic (number formats, units, symbols), formulas in tables, verifiable figures from
structured specs, concise exam answers, reviewer errata. Offline, synthetic data only."""
import json, re, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from exam_mastery.derivation_check import check_steps, declared_number_format, summary
from exam_mastery.chapter_publish import model, publish_html, publish_pdf, figure_label_check, exam_answer_rows
from exam_mastery.math_text import MathRenderer
from exam_mastery.common import ContractError


def st(texts, **kw):
    return [(r['status'], r['reason']) for r in check_steps(texts, **kw)]


class ExactArithmetic(unittest.TestCase):
    def test_trailing_period_units_and_scale(self):
        r = check_steps([r'\[60+40+20+50+30+15+10=225\text{ k€}.\]', r'\[25,000\text{ €}+3,350\text{ €}+6,650\text{ €}+9,500\text{ €}=44,500\text{ €}.\]'])
        self.assertEqual([x['status'] for x in r], ['PASS', 'PASS'])

    def test_mixed_scales_are_converted(self):
        self.assertEqual(st(['x = 6 Mio € + 1.7 Mio € + 300,000 € = 8,000,000 €'])[0][0], 'PASS')
        self.assertEqual(st(['x = 1.5 Mio € + 500 k€ = 2,000,000 €'])[0][0], 'PASS')
        self.assertEqual(st(['x = 1.5 Mio € + 500 k€ = 2,100,000 €'])[0][0], 'FAIL')

    def test_exact_fractions_and_truncation(self):
        self.assertEqual(st([r'\[\frac{8,000,000}{6,000,000}\times33,350\text{ €}=44,466.666\ldots\text{ €}\approx44,467\text{ €}.\]'])[0][0], 'PASS')
        self.assertEqual(st([r'\(\frac{1}{3} = 0.333\ldots\)'])[0][0], 'PASS')
        self.assertEqual(st([r'\(\frac{1}{3} = 0.334\)'])[0][0], 'FAIL')        # 0.3333 rounds to 0.333, not 0.334

    def test_german_and_english_formats(self):
        self.assertEqual(st(['a = 1.234,5 + 0,5 = 1.235'])[0][0], 'PASS')
        self.assertEqual(st(['a = 1,234.5 + 0.5 = 1,235'])[0][0], 'PASS')
        self.assertEqual(st(['CON = 1/0,85*(0,15*7,700,000 € - 900,000 €) = 300,000 €'])[0][0], 'PASS')   # slide notation

    def test_ambiguous_format_stays_not_tested_unless_declared(self):
        self.assertEqual(st(['b = 13/7 ≈ 1,857']), [('NOT_TESTED', 'AMBIGUOUS_NUMBER_FORMAT')])
        self.assertEqual(st(['d = 44,500 - 44,467 = 33']), [('NOT_TESTED', 'AMBIGUOUS_NUMBER_FORMAT')])
        self.assertEqual(st(['d = 44,500 - 44,467 = 33'], number_format='en')[0][0], 'PASS')
        self.assertEqual(st(['b = 13/7 ≈ 1,857'], number_format='de')[0][0], 'PASS')
        self.assertEqual(declared_number_format(['Note: In the exam we use the English number format!']), 'en')
        self.assertIsNone(declared_number_format(['English number format', 'deutsches Zahlenformat']))

    def test_currency_mismatch_is_not_tested(self):
        self.assertEqual(st([r'x = 2 € + 3 \$ = 5']), [('NOT_TESTED', 'UNIT_MISMATCH')])

    def test_symbols_from_later_steps_verify_algebra_and_definitions(self):
        r = check_steps([r'\[\frac{900,000\text{ €}+CON}{7,700,000\text{ €}+CON}=0.15.\]', r'\[900,000\text{ €}+CON=1,155,000\text{ €}+0.15CON.\]',
                         r'\[0.85CON=255,000\text{ €},\qquad CON=300,000\text{ €}.\]'])
        self.assertEqual([x['status'] for x in r], ['PASS', 'PASS', 'PASS', 'PASS'])
        self.assertIn('satisfies', r[-1]['detail'])
        bad = check_steps([r'\[0.85CON=255,000\text{ €},\qquad CON=310,000\text{ €}.\]'])
        self.assertEqual([x['status'] for x in bad], ['FAIL', 'NOT_TESTED'])         # a wrong solution is not "verified"

    def test_a_defining_step_is_never_checked_against_itself(self):
        r = check_steps(['POM = 6 Mio € + 1.7 Mio € + CON', 'CON = 300,000 €'])
        self.assertEqual(r[0]['status'], 'NOT_TESTED')

    def test_restated_wrong_result_fails(self):
        r = check_steps([r'\[NNC=\frac{8,000,000}{6,000,000}\times33,350=44,466.67\]', r'\[NNC\approx44,470\]'])
        self.assertEqual([x['status'] for x in r], ['PASS', 'FAIL'])

    def test_multi_line_and_chained_expressions(self):
        r = check_steps(['\\[400,000\\text{ €}+CON=490,000\\text{ €}+0.10CON,\\quad0.90CON=90,000\\text{ €},\\quad CON=100,000\\text{ €}.\\]'])
        self.assertEqual([x['status'] for x in r], ['PASS', 'PASS', 'PASS'])
        r = check_steps(['\\[a = 2 + 3 \\\\ = 5\\]'])
        self.assertIn(r[0]['status'], ('PASS', 'NOT_TESTED'))

    def test_summary_separates_counts(self):
        s = summary(check_steps(['x = 1 + 1 = 2', 'y = 2 + 2 = 5', 'b = 13/7 ≈ 1,857']))
        self.assertEqual((s['recognised_steps'], s['verified_pass'], s['arithmetic_fail'], s['not_tested']), (3, 1, 1, 1))
        self.assertEqual(s['not_tested_reasons'], {'AMBIGUOUS_NUMBER_FORMAT': 1})


MANIFEST = {'sources': [{'source_id': 'S1', 'relative_path': 'deck.pdf'}],
            'elements': [{'element_id': 'e1', 'source_id': 'S1', 'locator': {'page': 3}, 'text': 'Early Stages\nSeed & \nStartup Phase\nLater Stages'},
                         {'element_id': 'e2', 'source_id': 'S1', 'locator': {'page': 3}, 'text': 'Growth Phase'},
                         {'element_id': 'e3', 'source_id': 'S1', 'locator': {'page': 4}, 'text': 'Sum 350 k€'}]}


def ast(**over):
    a = {'title': 'T', 'blocks': [{'block_id': 'b1', 'kind': 'CALCULATION', 'title': 'Cap table', 'body': r'Es gilt \(x^2\).',
                                   'source_refs': ['e1'], 'provenance': 'SOURCE_PARAPHRASE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW',
                                   'steps': [{'statement': r'\[25,000\text{ €}+3,350\text{ €}=28,350\text{ €}.\]', 'justification': 'add'}],
                                   'assumptions': ['Amounts in euros.', 'No fees.']}],
         'notation': [{'symbol': r'\(CON\)', 'meaning': r'converted amount, \(\frac{a}{b}\)', 'status': 'OK'}],
         'open_issues': [{'code': 'X', 'severity': 'minor', 'detail': r'stated \(44,467\text{ €}\)'}],
         'figures': [{'figure_id': 'f1', 'caption': 'Lifecycle', 'source_element_id': 'e1', 'linked_block_ids': ['b1'],
                      'spec': {'order': ['Early Stages', 'Later Stages'], 'labels': [['Seed & Startup Phase'], ['Growth Phase']],
                               'constraints': ['keep order']}}],
         'exam_answers': [{'item_id': 'q1', 'answer': 'Self-financing and Boot-Strapping.', 'source_refs': ['e1'], 'status': 'ANSWERED_FROM_SOURCE'},
                          {'item_id': 'q2', 'answer': '', 'status': 'SOURCE_MISSING'}],
         'errata': [{'object_id': 'b1', 'text': r'Gap \(225-150=75\) k€.', 'origin': 'Review'}]}
    a.update(over); return a


class Publishing(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix='b67-'))
        self.mr = MathRenderer(self.d / 'math')
        self.m = model(ast(), MANIFEST)
        self.m['errata'] = ast()['errata']
        self.m['exam_rows'] = exam_answer_rows(self.m, [{'item_id': 'q1', 'wording': 'Name internal financing.'},
                                                        {'item_id': 'q2', 'wording': 'Five team factors?'},
                                                        {'item_id': 'q3', 'wording': 'Missing one?'}])

    def test_tables_render_formulas_in_html_and_pdf(self):
        import pymupdf
        publish_html(self.m, self.d / 'x.html', self.mr); publish_pdf(self.m, self.d / 'x.pdf', self.mr)
        h = re.sub(r'aria-label="[^"]*"', '', (self.d / 'x.html').read_text())
        self.assertNotIn(r'\(', re.sub(r'<svg.*?</svg>', '', h, flags=re.S))
        text = ''.join(p.get_text() for p in pymupdf.open(self.d / 'x.pdf'))
        self.assertNotRegex(text, r'\\\(|\\frac|\\text\{')
        self.assertNotIn('.;', text)

    def test_figure_rendered_from_spec_with_label_check(self):
        f = self.m['figures'][0]
        self.assertEqual(f['label_check']['status'], 'PASS')
        bad = figure_label_check({'source_element_id': 'e1', 'spec': {'order': ['Early Stages'], 'labels': [['Invented Phase']]}}, MANIFEST)
        self.assertEqual(bad['status'], 'REVIEW_REQUIRED'); self.assertEqual(bad['missing'], ['Invented Phase'])
        publish_html(self.m, self.d / 'x.html', self.mr)
        h = (self.d / 'x.html').read_text()
        self.assertIn('<table class="fig">', h); self.assertIn('Seed &amp; Startup Phase', h); self.assertIn('keep order', h)

    def test_exam_answers_and_missing_answers_are_explicit(self):
        rows = {r['item_id']: r['status'] for r in self.m['exam_rows']}
        self.assertEqual(rows, {'q1': 'ANSWERED_FROM_SOURCE', 'q2': 'SOURCE_MISSING', 'q3': 'MISSING_IN_AUTHOR_OUTPUT'})
        publish_html(self.m, self.d / 'x.html', self.mr)
        h = (self.d / 'x.html').read_text()
        self.assertIn('Antwort nicht in den Kursquellen', h); self.assertIn('fehlt im Author-Output', h)

    def test_errata_shown_at_block_without_changing_model_text(self):
        publish_html(self.m, self.d / 'x.html', self.mr)
        h = (self.d / 'x.html').read_text()
        self.assertIn('class="errata"', h); self.assertIn('Es gilt', h)
        self.assertLess(h.index('class="errata"'), h.index('Es gilt'))


class AuthorContract(unittest.TestCase):
    def v(self, answers):
        import exam_mastery.production as P
        src = Path(P.__file__).read_text()
        self.assertIn("exam answer {e['item_id']}: SOURCE_MISSING must not carry an answer", src)
        # exercise the same rules as v_author on a minimal payload
        for e in answers:
            if e['status'] not in ('ANSWERED_FROM_SOURCE', 'SOURCE_MISSING', 'SUPPLEMENT_REQUIRED'): raise ContractError('status')
            if e['status'] == 'SOURCE_MISSING' and (e.get('answer') or e.get('answer_points')): raise ContractError('missing')
            if e['status'] == 'ANSWERED_FROM_SOURCE' and not e.get('source_refs'): raise ContractError('refs')

    def test_answer_without_source_or_invented_gap_answer_is_rejected(self):
        with self.assertRaises(ContractError): self.v([{'item_id': 'q', 'status': 'SOURCE_MISSING', 'answer': 'invented'}])
        with self.assertRaises(ContractError): self.v([{'item_id': 'q', 'status': 'ANSWERED_FROM_SOURCE', 'answer': 'x'}])
        self.v([{'item_id': 'q', 'status': 'SOURCE_MISSING', 'answer': ''}])

    def test_prompt_states_the_contract(self):
        import exam_mastery.production as P
        t = (Path(P.__file__).parent / 'prompts/chapter_author.txt').read_text()
        for k in ('exam_answers', 'SOURCE_MISSING', 'answers_item_ids', 'read consecutive slides'):
            self.assertIn(k, t)


if __name__ == '__main__':
    unittest.main()
