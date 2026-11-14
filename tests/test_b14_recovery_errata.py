"""B14: deterministic scope-reduction recovery, documented errata, and the coverage rule for title-slide headings."""
import json
import tempfile
import unittest
from pathlib import Path

from exam_mastery import errata, scope_recovery as sr
from exam_mastery.common import ContractError

CTX = {'competencies': [{'kc_id': 'kc-a', 'statement': 'A'}, {'kc_id': 'kc-x', 'statement': 'X'}],
       'exam_items': [{'item_id': 'q-1', 'kc_ids': ['kc-a']}, {'item_id': 'q-x', 'kc_ids': ['kc-x']}],
       'source_elements': [{'element_id': 'el-1', 'text': 'a'}, {'element_id': 'el-x', 'text': 'x'}], 'allowed_source_refs': ['el-1', 'el-x']}
NEW = {'competencies': [{'kc_id': 'kc-a', 'statement': 'A'}], 'exam_items': [{'item_id': 'q-1', 'kc_ids': ['kc-a']}],
       'source_elements': [{'element_id': 'el-1', 'text': 'a'}], 'allowed_source_refs': ['el-1']}
AUTHOR = {'blocks': [{'block_id': 'b1', 'kc_ids': ['kc-a'], 'body': 'keep'}, {'block_id': 'b9', 'kc_ids': ['kc-x'], 'body': 'drop'}],
          'exam_answers': [{'item_id': 'q-1'}, {'item_id': 'q-x'}],
          'open_issues': [{'issue_id': 'o1', 'object_id': 'b9', 'detail': 'about b9'}, {'issue_id': 'o2', 'object_id': 'b1'}]}
REVIEW = {'claim_reviews': [{'block_id': 'b1', 'element_ids': ['el-1']}, {'block_id': 'b9', 'element_ids': ['el-x']}],
          'findings': [{'object_id': 'kc-x'}, {'object_id': 'b1'}]}


class Delta(unittest.TestCase):
    def test_pure_removal_is_recoverable(self):
        removed, problems = sr.removal_delta(CTX, NEW)
        self.assertEqual(problems, []); self.assertEqual(removed, {'kc-x', 'q-x', 'el-x'})

    def test_added_or_changed_content_is_refused(self):
        add = json.loads(json.dumps(NEW)); add['competencies'].append({'kc_id': 'kc-new', 'statement': 'N'})
        self.assertTrue(any(p.startswith('ADDED_ID') for p in sr.removal_delta(CTX, add)[1]))
        chg = json.loads(json.dumps(NEW)); chg['competencies'][0]['statement'] = 'A changed'
        self.assertIn('CONTEXT_CHANGED_BEYOND_REMOVAL', sr.removal_delta(CTX, chg)[1])

    def test_strip_is_transitive_over_dropped_blocks(self):
        rm = {'kc-x', 'q-x', 'el-x'}
        a, dropped, derived = sr.strip_all(AUTHOR, rm)
        self.assertEqual([b['block_id'] for b in a['blocks']], ['b1']); self.assertEqual(derived, {'b9'})
        self.assertEqual([o['issue_id'] for o in a['open_issues']], ['o2'])     # issue about the dropped block goes too
        r, _, _ = sr.strip_all(REVIEW, rm, derived)
        self.assertEqual([c['block_id'] for c in r['claim_reviews']], ['b1']); self.assertEqual(r['findings'], [{'object_id': 'b1'}])


class Provider(unittest.TestCase):
    def make(self, td):
        src = Path(td) / 'old' / 'chapters' / 'ch-1'; (src / 'agent_io').mkdir(parents=True)
        (src / 'chapter_context.json').write_text(json.dumps(CTX))
        for role in sr.ROLES:
            f = src / 'agent_io' / f'{role}-abc.answer.json'; f.write_text(json.dumps(AUTHOR if role == 'chapter_author' else REVIEW if role.endswith('review') else {}))
            ev = src / 'provider_evidence' / role; ev.mkdir(parents=True); (ev / 'agent-abc.json').write_text(json.dumps({'answer_file': str(f)}))
        new = Path(td) / 'new' / 'chapters' / 'ch-1'; new.mkdir(parents=True)
        return src, new

    def test_answers_are_stripped_recorded_and_never_repaired(self):
        with tempfile.TemporaryDirectory() as td:
            src, new = self.make(td)
            (new / 'chapter_context.json').write_text(json.dumps(NEW))
            p = sr.ScopeRecoveryProvider(src)
            a = p.ask('chapter_author', 'prompt', new)
            self.assertEqual(len(a['blocks']), 1)
            rec = json.loads((new / 'scope_recovery.json').read_text())
            self.assertEqual(rec['model_calls'], 0); self.assertEqual(rec['roles'][0]['status'], 'SCOPE_RECOVERED')
            self.assertFalse(list((new / 'agent_io').glob('*.answer.json')))       # never disguised as an agent answer
            with self.assertRaisesRegex(ContractError, 'CANNOT_REPAIR'):
                p.ask('chapter_author', 'prompt v2', new)

    def test_changed_context_refuses(self):
        with tempfile.TemporaryDirectory() as td:
            src, new = self.make(td)
            chg = json.loads(json.dumps(NEW)); chg['competencies'][0]['statement'] = 'other'
            (new / 'chapter_context.json').write_text(json.dumps(chg))
            with self.assertRaisesRegex(ContractError, 'REFUSED'):
                sr.ScopeRecoveryProvider(src).ask('chapter_author', 'p', new)


class Errata(unittest.TestCase):
    AST = {'solutions': [{'solution_id': 'sol-1', 'answer': 'Rücklage von 25 % der Gewinne.', 'steps': [{'statement': 'x y x'}]}]}

    def test_apply_by_id_and_report(self):
        e = [{'id': 'E1', 'target': 'solutions[solution_id=sol-1].answer', 'old': '25 % der Gewinne', 'new': 'ein Viertel des Jahresüberschusses',
              'reason': 'r', 'basis': ['§ 5a GmbHG']}]
        out, app = errata.apply(self.AST, e)
        self.assertIn('ein Viertel', out['solutions'][0]['answer']); self.assertIn('25 %', self.AST['solutions'][0]['answer'])   # input untouched
        self.assertFalse(app[0]['human_reviewed'])

    def test_fail_closed(self):
        for t, old in (('solutions[solution_id=sol-1].steps[0].statement', 'x'), ('solutions[solution_id=nope].answer', 'R'), ('solutions[0].missing', 'R')):
            with self.assertRaises(ContractError):
                errata.apply(self.AST, [{'id': 'E', 'target': t, 'old': old, 'new': 'n', 'reason': 'r', 'basis': ['b']}])


class CoverageRule(unittest.TestCase):
    def chapter(self, td, answered):
        run = Path(td) / 'run'; ch = run / 'chapters' / 'ch-1'; ch.mkdir(parents=True); (run / 'plan').mkdir()
        ast = {'chapter_id': 'ch-1', 'kc_ids': ['kc-a'], 'blocked_kc_ids': ['kc-title'], 'blocks': [{'kc_ids': ['kc-a']}],
               'assessments': [{'kc_ids': ['kc-a']}], 'exam_answers': [{'item_id': 'q-1'}] if answered else [], 'kc_coverage': []}
        (ch / 'content_ast.json').write_text(json.dumps(ast))
        (ch / 'chapter_context.json').write_text(json.dumps({'exam_items': [{'item_id': 'q-1'}]}))
        (run / 'plan' / 'competency_scope.json').write_text(json.dumps([{'chapter_id': 'ch-1', 'kc_id': 'kc-title', 'category': 'NO_LEARNING_OBJECTIVE'}]))
        (run / 'plan' / 'curriculum.json').write_text(json.dumps({'competencies': [{'kc_id': 'kc-title', 'linked_item_ids': ['q-1']}]}))
        return ch

    def test_title_heading_is_not_a_gap_only_if_its_questions_are_answered(self):
        from exam_mastery.product import chapter_dossier
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(chapter_dossier(self.chapter(td, True))['dimensions']['coverage']['status'], 'PASS')
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(chapter_dossier(self.chapter(td, False))['dimensions']['coverage']['status'], 'FAIL')


class VerificationLayer(unittest.TestCase):
    def setup(self, td, result, tamper=False):
        import hashlib
        run = Path(td) / 'course' / 'ch-run'; ch = run / 'chapters' / 'ch-1'; ch.mkdir(parents=True); (run / 'plan').mkdir()
        item = {'item_id': 'a-1', 'prompt': 'P', 'kc_ids': ['k']}; sol = {'item_id': 'a-1', 'answer': 'A', 'steps': []}
        (ch / 'content_ast.json').write_text(json.dumps({'chapter_id': 'ch-1', 'kc_ids': ['k'], 'blocks': [{'kc_ids': ['k']}], 'assessments': [item], 'solutions': [sol]}))
        h = hashlib.sha256(('P' + '\x1f' + json.dumps(sol, ensure_ascii=False, sort_keys=True)).encode()).hexdigest()
        v = Path(td) / 'course' / 'verification'; v.mkdir()
        (v / 'ch-1.json').write_text(json.dumps({'records': [{'item_id': 'a-1', 'content_sha256': 'x' if tamper else h, 'result': result}]}))
        return ch

    def test_layers(self):
        from exam_mastery.product import chapter_dossier
        with tempfile.TemporaryDirectory() as td:
            d = chapter_dossier(self.setup(td, 'VERIFIED_NUMERIC'))
            self.assertEqual(d['dimensions']['solution_verification']['status'], 'INFO')
            self.assertNotIn('solution_verification', __import__('exam_mastery.product', fromlist=['TECHNICAL']).TECHNICAL)   # never a release gate
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(chapter_dossier(self.setup(td, 'CONTRADICTED'))['dimensions']['solution_verification']['status'], 'FAIL')
        with tempfile.TemporaryDirectory() as td:
            d = chapter_dossier(self.setup(td, 'CONTRADICTED', tamper=True))['dimensions']['solution_verification']
            self.assertEqual(d['by_item']['a-1'], 'STALE')       # content changed after the check: the old verdict no longer counts


class CauseRule(unittest.TestCase):
    def s3(self, text):
        from exam_mastery.semantic_checks import cause_claims
        book = {'sections': [{'title': 'T', 'blocks': [{'type': 'text', 'md': text, 'src': '', 'prov': 'interpretation'}]}]}
        return [r for r in cause_claims(book) if r[0] == 'S3']

    def test_sequence_sense_is_not_a_cause_claim(self):
        self.assertEqual(self.s3('Der **Zahlungsstrom** ist die Folge der Ein- und Auszahlungen; der Cashflow ist ihr Saldo.'), [])
        self.assertEqual(self.s3('Ein Plan ist die Folge der Schritte A, B und C.'), [])

    def test_causal_uses_stay_flagged(self):
        for t in ('Die Liquiditätslücke ist die Folge der späten Zahlungen.', 'Der Engpass ist die Folge von Zahlungsverzug.',
                  'Die Insolvenz ist meist die Folge zu geringer Liquidität.', 'Die Ursache ist der fehlende Puffer.'):
            self.assertEqual(len(self.s3(t)), 1, t)


if __name__ == '__main__':
    unittest.main()
