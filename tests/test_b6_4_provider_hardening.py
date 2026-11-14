"""B6.4 provider hardening. Offline only: codex is never executed (execute and which are patched);
the model catalog is a temporary fake CODEX_HOME."""
import contextlib, io, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

import p3_fixtures as P
from test_p0_resource_budget import cfg, codex_ok, USAGE
from exam_mastery.budget import ResourceBudget, BudgetBlocked, BUDGET_BLOCKED
from exam_mastery.providers import Provider, ProviderError, ModelUnavailable, MODEL_UNAVAILABLE, check_model


def setUpModule():
    P.install_fake_codex_home(slugs=(P.FAKE_MODEL, 'other-listed-model'))


def tearDownModule():
    P.remove_fake_codex_home()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)
        self.which = patch('exam_mastery.providers.shutil.which', return_value='/offline/fake-codex'); self.which.start()

    def tearDown(self):
        self.which.stop(); self.tmp.cleanup()

    def budget(self, **kw):
        return ResourceBudget(cfg(**kw), self.d / 'budget')


class ModelGate(Base):
    def test_listed_model_is_passed_once_as_codex_model(self):
        seen = []
        def fake(cmd, prompt, cwd, timeout):
            seen.append(cmd); return codex_ok(USAGE)(cmd, prompt, cwd, timeout)
        b = self.budget(max_requests=1, max_retries=0)
        with patch('exam_mastery.providers.execute', side_effect=fake) as ex:
            Provider('codex', model=P.FAKE_MODEL, budget=b).ask('chapter_author', 'x', self.d)
        self.assertEqual(ex.call_count, 1)
        cmd = seen[0]
        self.assertEqual(cmd.count('--model'), 1)
        self.assertEqual(cmd[cmd.index('--model') + 1], P.FAKE_MODEL)
        self.assertEqual(cmd[-1], '-')                                  # prompt via stdin, model before it
        self.assertIn('--ignore-user-config', cmd)                       # user config cannot override the model

    def test_unlisted_invalid_or_missing_model_aborts_before_reservation_and_process(self):
        for model, why in (('not-in-catalog', 'not in the local'), ('--sandbox', 'invalid'), ('a b', 'invalid'), ('', 'invalid')):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as d:
                b = ResourceBudget(cfg(max_requests=1, max_retries=0), Path(d) / 'b')
                with patch('exam_mastery.providers.execute') as ex, self.assertRaises(ModelUnavailable) as e:
                    Provider('codex', model=model, budget=b).ask('chapter_author', 'x', d)
                ex.assert_not_called()
                self.assertIn(why, e.exception.reason)
                s = b.summary(); self.assertEqual((s['requests'], s['state'], s['open_reservations']), (0, 'ACTIVE', 0))
                rec = json.loads(next(Path(d).glob('provider_evidence/*/attempt-*/process.json')).read_text())
                self.assertEqual(rec['classification'], MODEL_UNAVAILABLE)

    def test_missing_catalog_fails_closed(self):
        with tempfile.TemporaryDirectory() as home, patch.dict('os.environ', {'CODEX_HOME': home}):
            with self.assertRaises(ModelUnavailable) as e: check_model('codex', P.FAKE_MODEL)
            self.assertIn('catalog unreadable', e.exception.reason)
        with self.assertRaises(ModelUnavailable): check_model('codex', None)

    def test_provider_reports_model_not_found_controlled_and_sticky(self):
        def gone(cmd, prompt, cwd, timeout):
            ev = [{'type': 'error', 'message': 'model_not_found: The model does not exist'}, {'type': 'turn.failed'}]
            return 1, '\n'.join(json.dumps(e) for e in ev), '', False
        b = self.budget(max_requests=3, max_retries=0)
        p = Provider('codex', model=P.FAKE_MODEL, budget=b)
        with patch('exam_mastery.providers.execute', side_effect=gone) as ex:
            with self.assertRaises(ProviderError) as e: p.ask('chapter_author', 'x', self.d)
            self.assertEqual(e.exception.record['classification'], MODEL_UNAVAILABLE)
            with self.assertRaises(BudgetBlocked): p.ask('chapter_assessment', 'x', self.d)   # no further process
            self.assertEqual(ex.call_count, 1)
        s = b.summary()
        self.assertEqual(s['state'], BUDGET_BLOCKED); self.assertIn('model', s['blocked_reason'])
        self.assertEqual(s['usage_uncertain_calls'], 1)                 # started process: worst case charged

    def test_one_request_limit_counts_processes_and_blocks_contract_repair(self):
        from exam_mastery.checkpoints import Checkpoints
        b = self.budget(max_requests=1, max_retries=0)
        p = Provider('codex', model=P.FAKE_MODEL, budget=b)
        def invalid(_): raise ValueError('contract')
        with patch('exam_mastery.providers.execute', side_effect=codex_ok(USAGE)) as ex:
            with self.assertRaises(BudgetBlocked): Checkpoints(self.d / 'u').invoke('chapter_author', 'p', p, invalid)
        self.assertEqual(ex.call_count, 1)                                # repair attempt never started a process
        self.assertTrue(list((self.d / 'u').glob('chapter_author.invalid-*.json')))


class EntryPoints(Base):
    def run_main(self, *extra):
        from exam_mastery.runtime import main
        b = self.d / 'budget.json'; b.write_text(json.dumps(cfg(max_requests=1, max_retries=0)))
        root = self.d / 'course'; root.mkdir()
        out = io.StringIO()
        with patch('exam_mastery.providers.execute') as ex, patch('exam_mastery.chapters.dry_run') as plan, contextlib.redirect_stdout(out):
            rc = main([str(root), '--budget', str(b), *extra])
        ex.assert_not_called(); plan.assert_not_called()                 # stopped before preflight, lock or run dir
        return rc, json.loads(out.getvalue())

    def test_cli_without_model_is_refused(self):
        rc, msg = self.run_main()
        self.assertEqual((rc, msg['status'], msg['provider_calls_made']), (2, MODEL_UNAVAILABLE, 0))

    def test_cli_with_unlisted_model_is_refused(self):
        rc, msg = self.run_main('--model', 'not-in-catalog')
        self.assertEqual((rc, msg['status'], msg['model']), (2, MODEL_UNAVAILABLE, 'not-in-catalog'))

    def test_budget_gate_still_comes_first(self):
        from exam_mastery.runtime import run_chapters
        root = self.d / 'c2'; root.mkdir()
        with self.assertRaises(BudgetBlocked): run_chapters(root, provider=Provider('codex'), output_base=self.d / 'r')
        self.assertFalse((self.d / 'r').exists())

    def test_model_is_part_of_run_identity(self):
        self.assertNotEqual(Provider('codex', model=P.FAKE_MODEL).fingerprint(), Provider('codex', model='other-listed-model').fingerprint())


if __name__ == '__main__':
    unittest.main()
