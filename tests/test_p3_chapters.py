"""P3 acceptance: one-root chapter path, chapter fusion/order, fidelity gate, ContentAST gates, action audit.
All model output is SYNTHETIC_FIXTURE (tests/p3_fixtures.py). No provider process, no network."""
import contextlib, copy, io, json, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from exam_mastery.chapters import dry_run, ast_validity, planned_actions, fidelity_gate, CHAPTER_ROLES
from exam_mastery.curriculum import SemanticDecisions
from exam_mastery.runtime import run_chapters
from exam_mastery.validate import check_content_ast, check_shapes
from exam_mastery.budget import BUDGET_BLOCKED


@contextlib.contextmanager
def no_process_no_network():
    with patch('exam_mastery.providers.execute', side_effect=AssertionError('provider process started')) as ex, \
            patch('subprocess.Popen', side_effect=AssertionError('subprocess started')), \
            patch('socket.socket.connect', side_effect=AssertionError('network used')), \
            patch('exam_mastery.production.produce_unit', side_effect=AssertionError('legacy per-chunk chain used')):
        yield ex


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def root(self, builder, *a):
        return builder(F.random_root(self.d / 'src'), *a)

    def dry(self, root, decisions=None, name=None):
        out = self.d / 'out' / (name or root.name)
        return dry_run(root, out, decisions)

    def chapter(self, plan, title_part):
        return next(c for c in plan['chapters'] if title_part in c['title'])


class E1_E2_EntryAndCourses(Base):
    def test_cli_dry_run_random_root_no_provider_and_old_commands(self):
        from exam_mastery.runtime import main
        from exam_mastery.cli import main as cli
        root = F.make('math', str(self.d / 'r'))
        out = self.d / 'dry'
        with no_process_no_network(), contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(main([str(root), '--dry-run', '--out', str(out)]), 0)
            self.assertEqual(cli(['start', str(root), '--dry-run', '--out', str(self.d / 'dry2')]), 0)
            self.assertEqual(cli(['inventory', str(root), '--out', str(self.d / 'inv')]), 0)
            self.assertEqual(cli(['plan', str(root), '--out', str(self.d / 'pl')]), 0)
        rep = json.loads((out / 'dry_run_report.json').read_text())
        self.assertEqual(rep['provider_calls_made'], 0); self.assertTrue(rep['originals_unchanged'])
        for f in ('source_inventory.json', 'curriculum.json', 'chapter_gates.json', 'planned_actions.json'):
            self.assertTrue((out / f).exists(), f)
        self.assertFalse(rep['claims']['course_complete'])
        self.assertNotEqual(rep['readiness'], 'READY_FOR_APPROVAL')  # math fixture has real gaps
        self.assertTrue(rep['source_gaps'] and rep['blockers'])
        self.assertTrue((self.d / 'pl' / 'curriculum.json').exists())

    def test_three_contrasting_courses_without_configuration(self):
        seen = {}
        for kind in ('math', 'law', 'ml'):
            rep, plan, m, gates, actions = self.dry(F.make(kind, str(self.d / kind)))
            self.assertEqual(rep['provider_calls_made'], 0)
            self.assertTrue(plan['chapters'])
            seen[kind] = set(plan['domain_profile']['active_profiles'])
            for c in rep['chapters']:
                self.assertIn(c['gate'], ('READY', 'READY_WITH_OPEN_ISSUES', 'PARTIAL', 'BLOCKED'))
        self.assertIn('formal_mathematics', seen['math']); self.assertIn('law', seen['law']); self.assertIn('computing', seen['ml'])
        # law: SUBSUME competency carries the norm-verification open issue; ml: executable tests are a risk review
        rep, plan, m, gates, _ = self.dry(F.make('law', str(self.d / 'law2')))
        self.assertIn('NORM_TEXT_NOT_VERIFIED', rep['chapters'][0]['open_issue_codes'])
        rep, plan, m, gates, actions = self.dry(F.make('ml', str(self.d / 'ml2')))
        self.assertIn('chapter_risk_review', {a['role'] for a in actions})


class E3_Merge(Base):
    def test_same_topic_in_two_sources_is_one_chapter_with_multi_source_anchors(self):
        root = self.root(P.merge_course)
        rep, plan, m, gates, _ = self.dry(root)
        eig = [c for c in plan['chapters'] if 'Eigenvektoren' in c['title']]
        self.assertEqual(len(eig), 1)
        c = eig[0]
        paths = {s['relative_path'] for s in m['sources'] if s['source_id'] in c['source_package']['source_ids']}
        self.assertTrue({'a/skript_eigen.md', 'b/folien_eigen.md', 'klausur.md'} <= paths, paths)
        self.assertTrue(c['source_package']['assessment_element_ids'])
        self.assertEqual(c['merged_from'][0]['title'], 'Folien: Eigenwerte und Eigenvektoren')
        merged = [x for x in plan['chapter_merges'] if x['decision'] == 'MERGED']
        self.assertEqual(merged[0]['rule'], 'M1_same_topic_title')
        # 'Eigenwerte symmetrischer Matrizen' overlaps but is not provably the same chapter -> review, not merged
        amb = [x for x in plan['chapter_merges'] if x['decision'] == 'SEMANTIC_REVIEW_REQUIRED']
        self.assertTrue(amb); self.assertEqual(len(plan['chapters']), 2)
        self.assertIn('CHAPTER_MERGE_REVIEW', next(x for x in rep['chapters'] if 'symmetrischer' in x['title'])['open_issue_codes'])

    def test_merge_and_keep_separate_decisions(self):
        root = self.root(P.merge_course)
        _, plan, m, _, _ = self.dry(root, name='a')
        sym = self.chapter(plan, 'symmetrischer')['chapter_id']; eig = self.chapter(plan, 'Eigenvektoren')['chapter_id']
        anchor = self.chapter(plan, 'symmetrischer')['anchor_element_ids'][:1]
        d = SemanticDecisions([{'kind': 'chapter_merge', 'subject_id': sym, 'value': eig, 'rationale': 'fixture: same chapter',
                                'evidence_element_ids': anchor, 'decided_by': 'fixture'}])
        _, plan2, _, _, _ = self.dry(root, d, name='b')
        self.assertEqual(len(plan2['chapters']), 1)
        d = SemanticDecisions([{'kind': 'chapter_keep_separate', 'subject_id': sym, 'value': eig, 'rationale': 'fixture: different',
                                'evidence_element_ids': anchor, 'decided_by': 'fixture'}])
        _, plan3, _, _, _ = self.dry(root, d, name='c')
        self.assertFalse([x for x in plan3['chapter_merges'] if x['decision'] == 'SEMANTIC_REVIEW_REQUIRED'])
        with self.assertRaises(Exception):
            SemanticDecisions([{'kind': 'chapter_merge', 'subject_id': sym, 'value': eig, 'rationale': 'x',
                                'decided_by': 'model'}]).validate({e['element_id'] for e in m['elements']})


class E4_Order(Base):
    def order(self, mode):
        _, plan, _, _, _ = self.dry(self.root(P.order_course, mode), name=mode)
        return [c['title'] for c in plan['chapters']], plan

    def test_adversarial_file_names_do_not_decide_order(self):
        for mode, basis in (('numbered', 'SOURCE_STATED_HEADING_NUMBER'), ('toc', 'SOURCE_STATED_TOC'), ('prereq', None)):
            titles, plan = self.order(mode)
            self.assertIn('Ausgleichsrechnung', titles[0], mode); self.assertIn('QR', titles[1], mode)
            self.assertEqual(len(titles), 2, mode)  # the syllabus is ordering evidence, not a chapter
            if basis:
                self.assertEqual(plan['chapter_ordering']['primary_basis'], basis)
            else:
                self.assertIn(plan['chapters'][1]['order_basis']['basis'], ('STATED_PREREQUISITE', 'INFERRED_PREREQUISITE'))
            self.assertNotIn('UNRESOLVED_FILENAME_FALLBACK', plan['chapter_ordering']['per_chapter'].values(), mode)

    def test_no_evidence_is_reported_unresolved(self):
        titles, plan = self.order('none')
        self.assertEqual(plan['chapter_ordering']['status'], 'UNRESOLVED_REVIEW_REQUIRED')
        self.assertTrue(all(v == 'UNRESOLVED_FILENAME_FALLBACK' for v in plan['chapter_ordering']['per_chapter'].values()))


class E5_E7_ContentAST(Base):
    """Synthetic fixture model -> chapter ContentAST; negative variants trip the gates."""

    def produce(self, variant=None, kind='math', title='Ausgleich'):
        root = F.make(kind, str(self.d / (variant or 'ok') / kind))
        model = P.SyntheticChapterModel(variant)
        with no_process_no_network():
            out, status = run_chapters(root, provider=model, output_base=self.d / 'runs' / (variant or 'ok'))
        rep, plan, m, gates, actions = json.loads((out / 'plan' / 'dry_run_report.json').read_text()), \
            json.loads((out / 'plan' / 'curriculum.json').read_text()), json.loads((out / 'plan' / 'source_inventory.json').read_text()), None, None
        c = self.chapter(plan, title)
        ast_ = json.loads((out / 'chapters' / c['chapter_id'] / 'content_ast.json').read_text())
        return ast_, status, plan, m, c, model, out

    def codes(self, ast_):
        r = ast_['gate_report']
        return {f['code'] for k in ('structural', 'evidence', 'operational') for f in r[k]}

    def test_coherent_chapter_with_full_provenance(self):
        ast_, status, plan, m, c, model, out = self.produce()
        self.assertEqual(ast_['content_origin'], 'SYNTHETIC_FIXTURE')
        self.assertEqual(ast_['gate_report']['technical_status'], 'PASS', ast_['gate_report'])
        self.assertEqual(ast_['status'], 'DRAFT_TECHNICAL_PASS_PENDING_REVIEW')
        self.assertEqual(ast_['release_status'], 'DRAFT'); self.assertEqual(ast_['gate_report']['academic_release'], 'NOT_TESTED')
        self.assertEqual(status['academic_release'], 'NOT_TESTED')
        sol = {s['solution_id'] for s in ast_['solutions']}
        for a in ast_['assessments']:
            self.assertIn(a['solution_id'], sol)
            self.assertIn({'from': a['item_id'], 'to': a['solution_id'], 'type': 'solved_by'}, ast_['relations'])
        for s in ast_['solutions']:
            self.assertTrue(s['rubric'] and s['hint_ladder'] and s['steps'])
        self.assertTrue(set(b for x in ast_['blocks'] for b in x['source_refs']) <= set(c['source_package']['element_ids']))
        self.assertTrue(all(k['status'] not in ('COVERED', 'VERIFIED') for k in ast_['kc_coverage']))
        self.assertTrue(all(b['claim_support_status'] != 'SUPPORTED' for b in ast_['blocks']))
        self.assertIn('MODEL_REVIEWED_SUPPORTED', {b['claim_support_status'] for b in ast_['blocks']})
        self.assertEqual(ast_['semantic_decisions']['schema'], 'em-semantic-decisions-v1')
        self.assertTrue({o['code'] for o in ast_['open_issues']} >= {'NOTATION_CONFLICT', 'NONESSENTIAL_ASSET_MISSING'})
        self.assertEqual(status['chapters'][self.chapter(plan, 'Geometrie')['chapter_id']]['status'], 'BLOCKED')
        self.assertTrue(status['originals_unchanged']); self.assertEqual(status['child_processes']['alive_after_stop'], [])
        self.assertEqual(ast_validity(ast_, m)['status'], 'VALID')

    def test_negative_fixtures_trip_gates(self):
        expect = {'empty_proof': 'EMPTY_PROOF', 'bad_shapes': 'DIMENSION_MISMATCH',
                  'no_rubric': 'MISSING_RUBRIC',
                  'name_for_derive': 'OPERATION_NOT_ASSESSED', 'mc_for_prove': 'OPERATION_NOT_ASSESSED'}
        for variant, code in expect.items():
            ast_, status, *_ = self.produce(variant)
            self.assertEqual(ast_['status'], 'GATE_FAILED', variant)
            self.assertIn(code, self.codes(ast_), variant)
            self.assertEqual(status['technical_status'], 'FAIL', variant)
        # B6.7: critical author defects stop at the stage gate, before any further provider process
        for variant, check in {'invented_anchor': 'ANCHORS_ALLOWED', 'false_verified': 'NO_SELF_CERTIFICATION'}.items():
            root = F.make('math', str(self.d / variant / 'math'))
            model = P.SyntheticChapterModel(variant)
            with no_process_no_network():
                out, status = run_chapters(root, provider=model, output_base=self.d / 'runs' / variant)
            self.assertNotIn('chapter_assessment', model.calls, variant)
            stopped = [c for c in (out / 'chapters').iterdir() if (c / 'stage_gates.json').exists()
                       and json.loads((c / 'stage_gates.json').read_text())[-1]['result'] == 'STOP']
            self.assertTrue(stopped, variant)
            g = json.loads((stopped[0] / 'stage_gates.json').read_text())[-1]
            self.assertEqual(g['after'], 'chapter_author'); self.assertIn(check, {c['check'] for c in g['critical']})
            self.assertFalse((stopped[0] / 'content_ast.json').exists())
            self.assertIn('StageGateFailed', {f['error_type'] for f in status['chapter_failures']})

    def test_subsume_not_by_paragraph_mention(self):
        ast_, *_ = self.produce('paragraph_for_subsume', 'law', 'Kaufvertrag')
        self.assertIn('OPERATION_NOT_ASSESSED', self.codes(ast_))
        ok, *_ = self.produce(None, 'law', 'Kaufvertrag')
        self.assertEqual(ok['gate_report']['technical_status'], 'PASS', ok['gate_report'])
        self.assertIn('NORM_TEXT_NOT_VERIFIED', {o['code'] for o in ok['open_issues']})

    def test_validator_is_not_length_based_and_checks_shapes(self):
        self.assertEqual(check_shapes({'symbols': {'A': [3, 2], 'x': [2, 1], 'b': [3, 1]}, 'equations': [{'lhs': 'A^T A x', 'rhs': 'A^T b'}]}), [])
        self.assertTrue(check_shapes({'symbols': {'A': [3, 2], 'x': [3, 1], 'b': [3, 1]}, 'equations': [{'lhs': 'A x', 'rhs': 'b'}]}))
        ast_, status, plan, m, c, *_ = self.produce()
        bad = copy.deepcopy(ast_)
        for b in bad['blocks']:
            if b['kind'] == 'PROOF':
                b['steps'] = [{'statement': 'x' * 5000, 'justification': 'trivial'}] * 1
                b['steps'] = [{'statement': 'trivial', 'justification': 'trivial'}]
        self.assertIn('PLACEHOLDER_ARGUMENT', {f['code'] for f in check_content_ast(bad, c, plan, m)['structural']})
        stale = copy.deepcopy(ast_); k = next(iter(stale['version']['source_fingerprint'])); stale['version']['source_fingerprint'][k] = 'old|old'
        self.assertEqual(ast_validity(stale, m)['status'], 'STALE_SOURCE_CHANGED')


class E6_Blockers(Base):
    def gate_of(self, kind):
        rep, plan, m, gates, actions = self.dry(self.root(P.blocker_course, kind), name=kind)
        return rep, gates, actions

    def test_explicit_blockers_instead_of_fictional_content(self):
        cases = {'scan': 'SCANNED_PAGE_NO_OCR', 'formula': 'CRITICAL_FORMULA_UNRELIABLE', 'required_online': 'REQUIRED_SOURCE_UNAVAILABLE'}
        for kind, code in cases.items():
            rep, gates, actions = self.gate_of(kind)
            self.assertIn(code, {b['code'] for b in rep['blockers']}, kind)
            self.assertEqual(rep['readiness'], 'BLOCKED', kind)
            self.assertEqual(actions, [], kind)
        # essential slide visual: math deck chapter blocked; its chapter never reaches a model
        rep, plan, m, gates, actions = self.dry(F.make('math', str(self.d / 'm')))
        deck = next(c for c in rep['chapters'] if 'Geometrie' in c['title'])
        self.assertEqual(deck['gate'], 'BLOCKED'); self.assertIn('ESSENTIAL_VISUAL_UNRESOLVED', sum(deck['blocked_kcs'].values(), []))
        self.assertNotIn(deck['chapter_id'], {a['chapter_id'] for a in actions})

    def test_blocked_chapter_never_calls_model(self):
        root = self.root(P.blocker_course, 'required_online')
        model = P.SyntheticChapterModel()
        with no_process_no_network():
            _, status = run_chapters(root, provider=model, output_base=self.d / 'runs')
        self.assertEqual(model.calls, []); self.assertEqual(status['technical_status'], 'FAIL')


class E8_ActionAudit(Base):
    def test_actions_per_chapter_not_per_chunk_and_budget_independent(self):
        root = F.make('math', str(self.d / 'a'))
        _, plan, m, gates, actions = self.dry(root, name='small')
        big = F.make('math', str(self.d / 'b'))
        md = big / 'skript' / 'kapitel1_ausgleich.md'
        md.write_text(md.read_text() + ''.join(f'\nAbsatz {i}: weitere ausführliche Erläuterung der Residuen und Projektionen.\n' for i in range(400)))
        _, plan2, m2, gates2, actions2 = self.dry(big, name='big')
        from exam_mastery.corpus import build
        u_small = build(root, self.d / 'cs', self.d / 'cc1')[1]; u_big = build(big, self.d / 'cb', self.d / 'cc2')[1]
        self.assertGreater(len(u_big), len(u_small))           # many more transport units / chunks ...
        self.assertEqual(len(actions2), len(actions))            # ... same planned provider actions
        self.assertEqual(len(plan2['chapters']), len(plan['chapters']))
        roles = {a['role'] for a in actions}
        self.assertTrue(roles <= set(CHAPTER_ROLES) | {'chapter_risk_review', 'chapter_revision'})
        from exam_mastery.chapters import planned_actions as pa
        import inspect
        self.assertNotIn('budget', inspect.signature(pa).parameters)
        self.assertEqual(len(actions), sum(6 if 'SYMBOLIC_WITH_DOMAIN' in c['requirements']['review_requirements'] else 5
                                           for c in plan['chapters'] if gates[c['chapter_id']]['status'] != 'BLOCKED'))
        model = P.SyntheticChapterModel()
        with no_process_no_network():
            run_chapters(big, provider=model, output_base=self.d / 'runs')
        self.assertEqual(len(model.calls), sum(not a['conditional'] for a in actions2))
        self.assertFalse(set(model.calls) & {'architect', 'research', 'learning_designer', 'author', 'cards', 'domain_audit'})

    def test_external_chapter_path_is_budget_gated(self):
        from exam_mastery.runtime import main
        pf = P.pilot_gate_cleared_for_p0_mechanics_test(); pf.start(); self.addCleanup(pf.stop)   # P0 mechanics only
        root = F.make('math', str(self.d / 'e'))
        with patch('exam_mastery.providers.execute') as ex, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(root)]), 3)                 # standard path, no budget -> fail closed
            ex.assert_not_called()
        from test_p0_resource_budget import cfg
        from exam_mastery.providers import Provider
        with patch('exam_mastery.providers.shutil.which', return_value='/offline/fake-codex'), \
                patch('exam_mastery.providers.execute', side_effect=P.codex_answering()) as ex, contextlib.redirect_stdout(io.StringIO()):
            out, status = run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 'ext', budget_config=cfg(max_requests=3))
        self.assertEqual(status['run_state'], BUDGET_BLOCKED)
        self.assertEqual(ex.call_count, 3); self.assertEqual(status['budget']['requests'], 3)
        self.assertTrue(status['resume_marker']['requires'])
        from exam_mastery.budget import BudgetBlocked
        with patch('exam_mastery.providers.shutil.which', return_value='/offline/fake-codex'), \
                patch('exam_mastery.providers.execute', side_effect=P.codex_answering()) as ex, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(BudgetBlocked) as e:   # no silent auto-resume of model work
                run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 'ext', budget_config=cfg(approval_id='appr-2'))
            self.assertEqual(e.exception.state, 'RESUME_NOT_AUTHORIZED'); ex.assert_not_called()
            out2, st2 = run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 'ext',
                                     budget_config=cfg(approval_id='appr-3', authorize_resume_of=out.name))
        self.assertEqual(out2, out); self.assertTrue(st2['resumed']); self.assertEqual(st2['run_state'], 'COMPLETE')
        self.assertEqual(st2['technical_status'], 'PASS')

    def test_sigterm_on_chapter_path_is_clean(self):
        import os, signal, time
        root = F.make('math', str(self.d / 's'))
        class Killer(P.SyntheticChapterModel):
            def ask(self, role, prompt, run_dir, images=None):
                os.kill(os.getpid(), signal.SIGTERM); time.sleep(1); raise AssertionError('signal not delivered')
        before = signal.getsignal(signal.SIGTERM)
        with contextlib.redirect_stdout(io.StringIO()):
            _, status = run_chapters(root, provider=Killer(), output_base=self.d / 'runs')
        self.assertEqual(status['run_state'], 'INTERRUPTED'); self.assertTrue(status['resumable'])
        self.assertEqual(signal.getsignal(signal.SIGTERM), before); self.assertEqual(status['child_processes']['alive_after_stop'], [])


class StableIds(Base):
    def test_chapter_and_kc_ids_stable_under_random_roots_and_irrelevant_rename(self):
        a = F.make('math', str(self.d / 'x')); b = F.make('math', str(self.d / 'y'))
        (b / 'skript' / 'fig_projection.png').rename(b / 'skript' / 'abbildung_umbenannt.png')
        _, pa_, *_ = self.dry(a, name='a'); _, pb, *_ = self.dry(b, name='b')
        self.assertEqual([c['chapter_id'] for c in pa_['chapters']], [c['chapter_id'] for c in pb['chapters']])
        self.assertEqual(sorted(k['kc_id'] for k in pa_['competencies']), sorted(k['kc_id'] for k in pb['competencies']))

def setUpModule():
    P.install_fake_codex_home()


def tearDownModule():
    P.remove_fake_codex_home()


if __name__ == '__main__':
    unittest.main()
