"""P3.2: --only-chapter. Offline; fake providers only; random roots; no network."""
import contextlib, io, json, os, signal, sys, tempfile, time, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from test_p0_resource_budget import cfg
from exam_mastery.chapters import dry_run, ChapterSelectionError
from exam_mastery.runtime import run_chapters, main
from exam_mastery.budget import BudgetBlocked, BUDGET_BLOCKED
from exam_mastery.providers import Provider


def three_chapters(root):
    root = Path(root)
    for n, (t, obj) in enumerate([('Lineare Ausgleichsrechnung', 'Berechnen Sie eine Ausgleichsgerade für gegebene Messpunkte.'),
                                  ('QR-Zerlegung', 'Erklären Sie die QR-Zerlegung einer Matrix.'),
                                  ('Eigenwerte', 'Berechnen Sie die Eigenwerte einer gegebenen Matrix.')], 1):
        (root / f'{"zyx"[n - 1]}_{n}.md').write_text(f'# Kapitel {n}: {t}\n\n## Lernziele\n- {obj}\n\nText zu {t} mit Details.\n', encoding='utf-8')
    return root


class Recorder(P.SyntheticChapterModel):
    def ask(self, role, prompt, run_dir, images=None):
        self.chapters = getattr(self, 'chapters', [])
        self.chapters.append(P.context_of(prompt)['chapter_id'])
        return super().ask(role, prompt, run_dir, images)


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()) as b:
        yield b


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def course(self, builder=three_chapters):
        return builder(F.random_root(self.d / 'src'))

    def plan(self, root, name='p'):
        return dry_run(root, self.d / ('dry-' + name))


class Selection(Base):
    def test_middle_chapter_only(self):
        root = self.course(); _, plan, _, gates, _ = self.plan(root)
        self.assertEqual(len(plan['chapters']), 3)
        self.assertTrue(all(g['status'] != 'BLOCKED' for g in gates.values()))
        first, mid, last = [c['chapter_id'] for c in plan['chapters']]
        model = Recorder()
        with quiet():
            out, st = run_chapters(root, provider=model, output_base=self.d / 'runs', only_chapter=mid)
        self.assertTrue(model.calls); self.assertEqual(set(model.chapters), {mid})
        self.assertEqual(sorted(p.name for p in (out / 'chapters').iterdir()), [mid])   # no other chapter checkpoint
        self.assertEqual(st['selected_chapter_ids'], [mid]); self.assertEqual(sorted(st['excluded_chapter_ids']), sorted([first, last]))
        self.assertEqual(set(st['chapters']), {mid})                                    # excluded: neither processed nor failed
        self.assertEqual(st['chapter_failures'], [], st.get('chapters')); self.assertEqual(len(st['chapters_analyzed']), 3)
        self.assertEqual(st['scope']['chapter_id'], mid); self.assertTrue(st['scope']['plan_fingerprint'])
        self.assertEqual(st['technical_status'], 'PASS', {'failures': st['chapter_failures'], 'chapters': st['chapters']})

    def test_invalid_selections_make_zero_calls(self):
        root = self.course(); _, plan, _, _, _ = self.plan(root)
        for bad, state in (('ch-ffffffffffffff', 'CHAPTER_NOT_FOUND'), ('Lineare Ausgleichsrechnung', 'CHAPTER_ID_INVALID'),
                           ('2', 'CHAPTER_ID_INVALID'), (' ' + plan['chapters'][0]['chapter_id'], 'CHAPTER_ID_INVALID')):
            model = Recorder()
            with quiet():
                out, st = run_chapters(root, provider=model, output_base=self.d / ('r' + state), only_chapter=bad)
            self.assertEqual(model.calls, [], bad); self.assertEqual(st['run_state'], state, bad)
            self.assertFalse(st['resumable']); self.assertEqual(st['technical_status'], 'FAIL')
            self.assertFalse((out / 'chapters').exists())
        with self.assertRaises(ChapterSelectionError):
            run_chapters(root, provider=Recorder(), output_base=self.d / 'e', only_chapter='')

    def test_id_from_old_plan_after_replanning(self):
        root = self.course(); _, plan, _, _, _ = self.plan(root)
        old = plan['chapters'][1]['chapter_id']
        md = next(p for p in root.iterdir() if p.read_text().startswith('# Kapitel 2'))
        md.write_text(md.read_text().replace('QR-Zerlegung', 'Householder-Verfahren'))   # topic renamed -> new id
        model = Recorder()
        with quiet():
            _, st = run_chapters(root, provider=model, output_base=self.d / 'runs', only_chapter=old)
        self.assertEqual(model.calls, []); self.assertEqual(st['run_state'], 'CHAPTER_NOT_FOUND')

    def test_blocked_chapter_zero_calls(self):
        root = F.make('math', str(self.d / 'm')); _, plan, _, gates, _ = self.plan(root)
        blocked = next(c for c, g in gates.items() if g['status'] == 'BLOCKED')
        model = Recorder()
        with quiet():
            _, st = run_chapters(root, provider=model, output_base=self.d / 'runs', only_chapter=blocked)
        self.assertEqual(model.calls, []); self.assertEqual(st['run_state'], 'SELECTED_CHAPTER_BLOCKED')
        self.assertEqual(st['selected_chapter_ids'], [blocked]); self.assertEqual(st['chapters'], {})

    def test_contrasting_courses(self):
        for kind in ('math', 'law', 'ml'):
            root = F.make(kind, str(self.d / kind)); _, plan, _, gates, actions = self.plan(root, kind)
            target = [c['chapter_id'] for c in plan['chapters'] if gates[c['chapter_id']]['status'] != 'BLOCKED'][-1]
            model = Recorder()
            with quiet():
                _, st = run_chapters(root, provider=model, output_base=self.d / ('r' + kind), only_chapter=target)
            self.assertEqual(set(model.chapters), {target}, kind)
            self.assertEqual(len(model.calls), sum(1 for a in actions if a['chapter_id'] == target and not a['conditional']), kind)


class DryRun(Base):
    def test_dry_run_with_and_without_selection(self):
        root = self.course()
        with patch('exam_mastery.providers.execute', side_effect=AssertionError('provider')), quiet():
            self.assertEqual(main([str(root), '--dry-run', '--out', str(self.d / 'all')]), 0)
            allr = json.loads((self.d / 'all' / 'dry_run_report.json').read_text())
            mid = allr['chapters'][1]['chapter_id']
            self.assertEqual(main([str(root), '--dry-run', '--out', str(self.d / 'one'), '--only-chapter', mid]), 0)
            self.assertEqual(main([str(root), '--dry-run', '--out', str(self.d / 'bad'), '--only-chapter', 'ch-00000000000000']), 2)
        one = json.loads((self.d / 'one' / 'dry_run_report.json').read_text())
        acts = json.loads((self.d / 'one' / 'planned_actions.json').read_text())
        self.assertEqual(allr['selection'], {'mode': 'ALL_CHAPTERS'})
        self.assertEqual(len({a['chapter_id'] for a in json.loads((self.d / 'all' / 'planned_actions.json').read_text())}), 3)
        self.assertEqual(one['selection']['selected_chapter_id'], mid); self.assertEqual(one['selection']['status'], 'SELECTED')
        self.assertEqual(len(one['selection']['excluded_chapter_ids']), 2)
        self.assertEqual({a['chapter_id'] for a in acts}, {mid})
        self.assertEqual({a['chapter_id'] for a in one['selection']['planned_requests_for_selected_chapter']}, {mid})
        self.assertEqual(len(one['chapters']), 3)                       # global context retained
        self.assertEqual(one['provider_calls_made'], 0)
        bad = json.loads((self.d / 'bad' / 'dry_run_report.json').read_text())
        self.assertEqual(bad['readiness'], 'SELECTION_ERROR'); self.assertEqual(bad['selection']['state'], 'CHAPTER_NOT_FOUND')
        self.assertEqual(json.loads((self.d / 'bad' / 'planned_actions.json').read_text()), [])

    def test_legacy_with_selection_rejected_and_duplicate_flag(self):
        root = self.course()
        with patch('exam_mastery.runtime.run', side_effect=AssertionError('legacy ran')) as legacy, \
                patch('exam_mastery.providers.execute', side_effect=AssertionError('provider')), quiet() as out:
            self.assertEqual(main([str(root), '--legacy-packages', '--only-chapter', 'ch-00000000000000']), 2)
            self.assertIn('INCOMPATIBLE_OPTIONS', out.getvalue())
            self.assertEqual(main([str(root), '--only-chapter', 'ch-00000000000000', '--only-chapter', 'ch-11111111111111']), 2)
            legacy.assert_not_called()

    def test_default_without_flag_unchanged(self):
        root = self.course(); model = Recorder()
        with quiet():
            out, st = run_chapters(root, provider=model, output_base=self.d / 'runs')
        self.assertEqual(st['scope'], {'mode': 'ALL_CHAPTERS'}); self.assertEqual(len(set(model.chapters)), 3)
        self.assertEqual(st['excluded_chapter_ids'], []); self.assertTrue((out.parent / 'active_chapters.json').exists())


class ResumeAndP0(Base):
    def setUp(self):
        super().setUp()
        self._pf = P.pilot_gate_cleared_for_p0_mechanics_test(); self._pf.start(); self.addCleanup(self._pf.stop)

    def external(self, root, mid, budget, base='ext'):
        with patch('exam_mastery.providers.shutil.which', return_value='/offline/fake-codex'), \
                patch('exam_mastery.providers.execute', side_effect=P.codex_answering()) as ex, quiet():
            try:
                out, st = run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / base, budget_config=budget, only_chapter=mid)
            except BudgetBlocked as e:
                return None, e, ex.call_count
        return out, st, ex.call_count

    def test_resume_only_same_scope_and_authorized(self):
        root = self.course(); _, plan, _, _, actions = self.plan(root)
        first, mid, last = [c['chapter_id'] for c in plan['chapters']]
        need = sum(1 for a in actions if a['chapter_id'] == mid and not a['conditional'])
        out, st, n1 = self.external(root, mid, cfg(max_requests=2))
        self.assertEqual(st['run_state'], BUDGET_BLOCKED); self.assertEqual(n1, 2); self.assertTrue(st['resumable'])
        _, e, n = self.external(root, mid, cfg(approval_id='a2'))                       # same scope, no authorization
        self.assertEqual(e.state, 'RESUME_NOT_AUTHORIZED'); self.assertEqual(n, 0)
        _, e, n = self.external(root, last, cfg(approval_id='a3', authorize_resume_of=out.name))   # other scope names old run
        self.assertEqual(e.state, 'RESUME_SCOPE_MISMATCH'); self.assertEqual(n, 0)
        _, e, n = self.external(root, None, cfg(approval_id='a4', authorize_resume_of=out.name))   # default scope names old run
        self.assertEqual(e.state, 'RESUME_SCOPE_MISMATCH'); self.assertEqual(n, 0)
        out2, st2, n2 = self.external(root, mid, cfg(approval_id='a5', authorize_resume_of=out.name))
        self.assertEqual(out2, out); self.assertTrue(st2['resumed']); self.assertEqual(st2['run_state'], 'COMPLETE')
        self.assertEqual(n1 + n2, need)                                                  # no duplicate calls
        self.assertEqual(sorted(p.name for p in (out / 'chapters').iterdir()), [mid])

    def test_b6_4_stage1_shape_one_codex_process_with_model_then_clean_stop(self):
        root = self.course(); _, plan, _, _, _ = self.plan(root); mid = plan['chapters'][1]['chapter_id']
        cmds = []
        def rec(cmd, prompt, cwd, timeout):
            cmds.append((list(cmd), timeout)); return P.codex_answering()(cmd, prompt, cwd, timeout)
        with patch('exam_mastery.providers.shutil.which', return_value='/offline/fake-codex'), \
                patch('exam_mastery.providers.execute', side_effect=rec), quiet():
            out, st = run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 's1',
                                   budget_config=cfg(max_requests=1, max_retries=0, max_wall_seconds=1200), only_chapter=mid)
        self.assertEqual(len(cmds), 1)                                                   # exactly one codex process
        cmd, timeout = cmds[0]
        self.assertEqual(cmd[cmd.index('--model') + 1], P.FAKE_MODEL); self.assertLessEqual(timeout, 600)
        self.assertEqual(st['run_state'], BUDGET_BLOCKED)
        self.assertEqual((st['budget']['requests'], st['budget']['retries']), (1, 0))
        self.assertEqual(st['provider']['model'], P.FAKE_MODEL)
        roles = sorted(p.name for p in (out / 'chapters' / mid / 'provider_evidence').iterdir()) if (out / 'chapters' / mid / 'provider_evidence').exists() \
            else sorted({x.parent.parent.name for x in out.glob('**/provider_evidence/*/attempt-*/process.json')} or set())
        self.assertEqual([r for r in roles if r.startswith('chapter_')], ['chapter_author'])
        pv = out / 'chapters' / mid / 'preview'                                         # B6.5: inspectable author draft
        self.assertTrue((pv / 'lehrbuch_vorschau.pdf').is_file() and (pv / 'lehrbuch_vorschau.html').is_file())
        rep = json.loads((pv / 'preview_report.json').read_text())
        self.assertEqual(rep['status'], 'AUTHOR_DRAFT_ONLY_NOT_REVIEWED'); self.assertIn('solutions', rep['missing_products'])
        self.assertIn('MODELLGENERIERTER ENTWURF', (pv / 'lehrbuch_vorschau.html').read_text())
        self.assertFalse((out / 'chapters' / mid / 'content_ast.json').exists())
        self.assertEqual(st['chapters'][mid]['author_preview'], 'AUTHOR_DRAFT_ONLY_NOT_REVIEWED')
        self.assertEqual(st['chapters'][mid]['status'], 'BUDGET_STOPPED')
        _, e, n = self.external(root, mid, cfg(approval_id='s1b', max_requests=1, max_retries=0), base='s1')   # no silent continuation
        self.assertEqual((e.state, n), ('RESUME_NOT_AUTHORIZED', 0))

    def test_resume_refused_when_selected_plan_changed(self):
        root = self.course(); _, plan, _, _, _ = self.plan(root)
        mid = plan['chapters'][1]['chapter_id']
        out, st, _ = self.external(root, mid, cfg(max_requests=1))
        status = json.loads((out / 'status.json').read_text()); status['scope']['plan_fingerprint'] = 'stale'
        (out / 'status.json').write_text(json.dumps(status))                            # simulate scope/plan drift
        _, st2, n = self.external(root, mid, cfg(approval_id='b2', authorize_resume_of=out.name))
        self.assertEqual(st2['run_state'], 'RESUME_SCOPE_MISMATCH'); self.assertEqual(n, 0)

    def test_sigterm_and_unknown_usage_with_selection(self):
        root = self.course(); _, plan, _, _, _ = self.plan(root); mid = plan['chapters'][1]['chapter_id']
        class Killer(Recorder):
            def ask(self, role, prompt, run_dir, images=None):
                os.kill(os.getpid(), signal.SIGTERM); time.sleep(1); raise AssertionError('no signal')
        before = signal.getsignal(signal.SIGTERM)
        with quiet():
            _, st = run_chapters(root, provider=Killer(), output_base=self.d / 'k', only_chapter=mid)
        self.assertEqual(st['run_state'], 'INTERRUPTED'); self.assertEqual(signal.getsignal(signal.SIGTERM), before)
        self.assertEqual(st['child_processes']['alive_after_stop'], [])
        def no_usage(cmd, prompt, cwd, timeout):           # usage missing -> worst case charged, never zero
            P.codex_answering()(cmd, prompt, cwd, timeout)
            return 0, json.dumps({'type': 'thread.started'}), '', False
        with patch('exam_mastery.providers.shutil.which', return_value='/x/codex'), \
                patch('exam_mastery.providers.execute', side_effect=no_usage), quiet():
            _, st = run_chapters(root, provider=Provider('codex', model=P.FAKE_MODEL), output_base=self.d / 'u', budget_config=cfg(max_requests=1), only_chapter=mid)
        self.assertGreater(st['budget']['output_tokens'], 0); self.assertGreaterEqual(st['budget']['usage_unknown_calls'], 1)

def setUpModule():
    P.install_fake_codex_home()


def tearDownModule():
    P.remove_fake_codex_home()


if __name__ == '__main__':
    unittest.main()
