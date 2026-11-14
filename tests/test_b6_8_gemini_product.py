import unittest
import importlib.util
"""B6.8: Gemini adapter (mock responses only, no network), product mode, quality dossier, provider comparison."""
import contextlib, hashlib, io, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).parent))
import p1p2_fixtures as F
import p3_fixtures as P
from exam_mastery.gemini_provider import GeminiProvider, estimate_cost, GEMINI_MODELS, _default_client
from exam_mastery.budget import ResourceBudget, BudgetBlocked, normalize_usage, validate_config
from exam_mastery.providers import ProviderError, ModelUnavailable
from exam_mastery.role_schemas import SCHEMAS, schema_for
from exam_mastery.common import ContractError

KEY = 'AIzaTEST-secret-key-0123456789abcdef'
MODEL = 'gemini-3.8-flash'


class APIError(Exception):
    def __init__(self, code, status, msg='err'):
        super().__init__(f'{code} {status}. {msg}'); self.code = code; self.status = status


class Resp:
    def __init__(self, text, usage, finish='STOP', block=None):
        self.text = text; self.usage_metadata = usage; self.model_version = MODEL + '-001'
        self.candidates = [type('C', (), {'finish_reason': finish})()]
        self.prompt_feedback = {'block_reason': block} if block else None


class FakeClient:
    """models.generate_content(model, contents, config) -> Resp; records every call."""
    def __init__(self, behaviour, log):
        self.models = self; self.behaviour = behaviour; self.log = log

    def generate_content(self, model, contents, config):
        self.log.append({'model': model, 'config': config, 'prompt_len': len(contents)})
        return self.behaviour(model, contents, config)


def usage(i=1000, c=200, o=300, t=50):
    return {'prompt_token_count': i, 'cached_content_token_count': c, 'candidates_token_count': o, 'thoughts_token_count': t, 'total_token_count': i + o + t}


def budget(d, **kw):
    cfg = {'approval_id': 'g', 'max_requests': 3, 'max_retries': 0, 'max_wall_seconds': 600, 'max_input_tokens': 10 ** 6,
           'max_input_tokens_per_call': 4 * 10 ** 5, 'max_output_tokens': 10 ** 5, 'max_output_tokens_per_call': 32000,
           'input_overhead_tokens_per_call': 0, 'image_input_tokens': 0}
    cfg.update(kw)
    return ResourceBudget(cfg, Path(d) / 'budget')


class Base(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix='b68-'))
        self.env = mock.patch.dict(os.environ, {'GEMINI_API_KEY': KEY}, clear=False); self.env.start(); self.addCleanup(self.env.stop)
        os.environ.pop('GOOGLE_API_KEY', None)
        self.log = []; self.factory_args = []

    def provider(self, behaviour, b=None, **kw):
        def factory(key, timeout_ms):
            self.factory_args.append((key == KEY, timeout_ms)); return FakeClient(behaviour, self.log)
        return GeminiProvider(kw.pop('model', MODEL), budget=b if b is not None else budget(self.d), client_factory=factory, **kw)

    def evidence_text(self):
        return ''.join(p.read_text() for p in self.d.rglob('*') if p.is_file())


class Adapter(Base):
    def test_success_records_usage_cost_schema_and_never_the_key(self):
        p = self.provider(lambda m, c, cfg: Resp('{"verdict":"PASS","findings":[]}', usage()))
        obj = p.ask('chapter_risk_review', 'ROLE: domain risk reviewer', self.d)
        self.assertEqual(obj['verdict'], 'PASS')
        cfg = self.log[0]['config']
        self.assertEqual(cfg['response_mime_type'], 'application/json'); self.assertIs(cfg['response_json_schema'], SCHEMAS['chapter_risk_review'])
        self.assertEqual(cfg['max_output_tokens'], 32000)
        self.assertTrue(self.factory_args[0][0]); self.assertTrue(590000 <= self.factory_args[0][1] <= 600000)   # key from env, timeout in ms
        s = p.budget.summary()
        self.assertEqual((s['requests'], s['input_tokens'], s['cached_input_tokens'], s['output_tokens']), (1, 1000, 200, 350))  # thoughts are output
        rec = json.loads(next(self.d.rglob('process.json')).read_text())
        self.assertEqual(rec['usage_status'], 'MEASURED'); self.assertEqual(rec['api_key_source'], 'env:GEMINI_API_KEY')
        self.assertAlmostEqual(rec['cost_usd_estimate'], (800 * 0.75 + 200 * 0.075 + 350 * 3.75) / 1e6, places=5)
        self.assertNotIn(KEY, self.evidence_text())

    def test_rate_limit_is_sticky_quota_block_and_no_retry(self):
        def boom(m, c, cfg): raise APIError(429, 'RESOURCE_EXHAUSTED')
        p = self.provider(boom)
        with self.assertRaises(ProviderError) as e:
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(e.exception.record['classification'], 'USAGE_LIMIT'); self.assertEqual(e.exception.record['http_code'], 429)
        self.assertEqual(len(self.log), 1)
        self.assertEqual(p.budget.summary()['state'], 'QUOTA_BLOCKED')
        with self.assertRaises(BudgetBlocked):
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(len(self.log), 1)                                   # nothing sent after the block

    def test_truncated_output_and_safety_stop_fail_with_measured_usage(self):
        p = self.provider(lambda m, c, cfg: Resp('{"verdict":', usage(o=32000, t=0), finish='MAX_TOKENS'))
        with self.assertRaises(ProviderError) as e:
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertIn('max_output_tokens', str(e.exception)); self.assertEqual(p.budget.summary()['output_tokens'], 32000)
        p2 = self.provider(lambda m, c, cfg: Resp('', usage(o=0, t=0), finish='SAFETY'), b=budget(self.d / 'b2'))
        with self.assertRaises(ProviderError):
            p2.ask('chapter_risk_review', 'x', self.d)
        p3 = self.provider(lambda m, c, cfg: Resp('', usage(o=0, t=0), block='SAFETY'), b=budget(self.d / 'b3'))
        with self.assertRaises(ProviderError):
            p3.ask('chapter_risk_review', 'x', self.d)

    def test_model_not_found_blocks_budget(self):
        def nf(m, c, cfg): raise APIError(404, 'NOT_FOUND')
        p = self.provider(nf)
        with self.assertRaises(ProviderError) as e:
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(e.exception.record['classification'], 'MODEL_UNAVAILABLE'); self.assertEqual(p.budget.summary()['state'], 'BUDGET_BLOCKED')

    def test_fail_closed_before_any_request(self):
        sent = lambda m, c, cfg: self.fail('must not send')
        with self.assertRaises(BudgetBlocked):
            GeminiProvider(MODEL, budget=None, client_factory=lambda k, t: FakeClient(sent, self.log)).ask('chapter_risk_review', 'x', self.d)
        p = self.provider(sent, model='gemini-unknown-9')
        with self.assertRaises(ModelUnavailable):
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(p.budget.summary()['requests'], 0)
        os.environ.pop('GEMINI_API_KEY')
        p = self.provider(sent)
        with self.assertRaises(ProviderError):
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(p.budget.summary()['requests'], 0); self.assertEqual(self.log, [])

    def test_key_file_must_be_private(self):
        os.environ.pop('GEMINI_API_KEY')
        f = self.d / 'k'; f.write_text(KEY); f.chmod(0o644)
        from exam_mastery.gemini_provider import load_api_key
        with self.assertRaises(ContractError):
            load_api_key(f)
        f.chmod(0o600); self.assertEqual(load_api_key(f), (KEY, 'file:k'))

    def test_cost_cap_refuses_worst_case_before_sending(self):
        pr = GEMINI_MODELS[MODEL]
        b = budget(self.d, max_cost_usd=0.01, pricing={'input': pr['input'], 'output': pr['output']})   # 32k output alone = 0.12 USD
        p = self.provider(lambda m, c, cfg: self.fail('must not send'), b=b)
        with self.assertRaises(BudgetBlocked) as e:
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertIn('max_cost_usd', str(e.exception)); self.assertEqual(self.log, [])

    @unittest.skipUnless(importlib.util.find_spec('google') and importlib.util.find_spec('google.genai'), 'optional extra [gemini] not installed')
    def test_real_sdk_client_disables_retries_and_uses_ms_timeout(self):
        c = _default_client('dummy-key-not-used', 123000)                 # constructing the client makes no request
        ho = c._api_client._http_options
        self.assertEqual(ho.timeout, 123000); self.assertEqual(ho.retry_options.attempts, 1)

    def test_thinking_level_validated_per_model(self):
        p = self.provider(lambda m, c, cfg: Resp('{"verdict":"PASS","findings":[]}', usage()), thinking_level='minimal')
        with self.assertRaises(ProviderError):
            p.ask('chapter_risk_review', 'x', self.d)
        self.assertEqual(self.log, [])

    def test_usage_normalization_and_cost(self):
        self.assertEqual(normalize_usage('gemini', usage(1000, 200, 300, 50)), {'input': 1000, 'cached_input': 200, 'cache_creation_input': 0, 'output': 350})
        self.assertIsNone(normalize_usage('gemini', {'candidates_token_count': 5}))
        self.assertIsNone(normalize_usage('gemini', usage(100, 200)))
        self.assertIsNone(estimate_cost('gemini-unlisted', {'input': 1, 'cached_input': 0, 'output': 1}))


class Schemas(unittest.TestCase):
    def test_schemas_cover_chapter_roles_and_accept_fixture_outputs(self):
        import jsonschema
        for role in ('chapter_author', 'chapter_assessment', 'chapter_solutions', 'chapter_semantic_review', 'chapter_risk_review', 'chapter_revision'):
            jsonschema.Draft202012Validator.check_schema(schema_for(role))
        a = {'learning_objectives': [{'kc_id': 'k', 'statement': 's'}], 'notation': [], 'figures': [{'figure_id': 'f', 'status': 'REDRAW_FROM_SOURCE_SPEC', 'spec': {'x': ['y']}}],
             'open_issues': [], 'exam_answers': [{'item_id': 'q', 'status': 'SOURCE_MISSING'}],
             'blocks': [{'block_id': 'b', 'kind': 'EXPLANATION', 'kc_ids': ['k'], 'provenance': 'SOURCE_PARAPHRASE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW',
                         'steps': [{'statement': 's', 'justification': 'j'}]}]}
        jsonschema.validate(a, SCHEMAS['chapter_author'])
        bad = dict(a); bad.pop('exam_answers')
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(bad, SCHEMAS['chapter_author'])
        allowed = {'type', 'properties', 'required', 'items', 'enum', 'description', 'additionalProperties'}
        def keys(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k != 'properties': self.assertIn(k, allowed)
                    keys(v) if k != 'properties' else [keys(x) for x in v.values()]
            elif isinstance(o, list):
                [keys(x) for x in o]
        [keys(s) for s in SCHEMAS.values()]                                  # Gemini JSON-schema subset only


def role_from(config):
    return next(r for r, s in SCHEMAS.items() if s is config.get('response_json_schema'))


class ProductMode(Base):
    def cfg(self, **pol):
        from exam_mastery.product import setup
        p, c = setup('gemini', MODEL, True, policy=pol or None, path=self.d / 'config.json')
        return c

    def test_setup_needs_consent_and_never_stores_a_key(self):
        from exam_mastery.product import setup, load_config
        with self.assertRaises(ContractError):
            setup('gemini', MODEL, False, path=self.d / 'c.json')
        c = self.cfg(); txt = (self.d / 'config.json').read_text()
        self.assertNotIn(KEY, txt); self.assertEqual(oct((self.d / 'config.json').stat().st_mode & 0o777), '0o600')
        self.assertTrue(c['data_transfer_consent']['accepted'])
        bad = dict(c, api_key='x'); (self.d / 'bad.json').write_text(json.dumps(bad))
        with self.assertRaises(ContractError):
            load_config(self.d / 'bad.json')

    def test_policy_budget_is_fail_closed_with_cost_cap(self):
        from exam_mastery.product import policy_budget
        b = validate_config(policy_budget(self.cfg(max_cost_usd_per_run=2.5)))
        self.assertEqual((b['max_retries'], b['max_cost_usd']), (2, 2.5))  # B7: bounded contract repairs; self.assertTrue(b['approval_id'].startswith('policy-'))

    def test_folder_to_learning_product_without_signatures(self):
        from exam_mastery.product import run_product
        root = F.make('math', str(self.d / 'course'))
        answer = lambda m, prompt, cfg: Resp(json.dumps(P.answer(role_from(cfg), prompt)), usage(5000, 0, 2000, 100))
        prov = self.provider(answer, b=None)
        prov.budget = None
        with contextlib.redirect_stdout(io.StringIO()):
            out, status, dossier = run_product(root, self.cfg(), output_base=self.d / 'runs', provider=prov)
        self.assertNotEqual(status['run_state'], 'PILOT_REVIEW_OPEN')
        self.assertEqual(status['mode_policy'], 'production')
        self.assertTrue(status['budget']['approval_id'].startswith('policy-'))
        self.assertGreater(status['budget']['cost_usd_estimate'], 0)
        self.assertEqual(set(dossier['dimensions']), {'coverage', 'subject_correctness', 'math_numeric', 'didactic_completeness',
                                                      'items_and_solutions', 'formulas_and_figures', 'anki', 'rendering'})
        self.assertTrue(set(dossier['dimensions'].values()) <= {'PASS', 'FAIL', 'NOT_TESTED'})
        self.assertEqual(dossier['release']['academic'], 'ACADEMIC_RELEASE_NOT_GRANTED')
        self.assertEqual(dossier['dimensions']['subject_correctness'], 'NOT_TESTED')   # a model review is never proof
        self.assertTrue((Path(out) / 'quality_dossier.json').exists())
        self.assertNotIn(KEY, ''.join(p.read_text(errors='ignore') for p in Path(out).rglob('*.json')))

    def test_auto_preflight_excludes_uncertain_content_and_escalates_the_rest(self):
        from exam_mastery import chapters as C
        fake = {'chapters': {'a': {'status': 'PILOT_BLOCKED', 'open': [{'code': 'KC_REVIEW_UNDECIDED', 'kc_id': 'k1'},
                                                                        {'code': 'CHAPTER_PAGE_REVIEW_OPEN', 'key': 'page:s:3'}], 'cleared': []},
                             'b': {'status': 'PILOT_BLOCKED', 'open': [{'code': 'SESSION_IDENTITY_UNRESOLVED'}], 'cleared': []}}}
        with mock.patch.object(C, 'production_preflight', return_value=fake):
            r = C.production_preflight_auto(None, None, ['a', 'b'])
        self.assertEqual(r['producible_chapters'], ['a']); self.assertEqual(r['result'], 'PARTIAL_ESCALATION')
        self.assertEqual([o['resolution'] for o in r['chapters']['a']['auto_resolved']], ['AUTO_EXCLUDED_NOT_PRODUCED', 'AUTO_PAGE_NOT_USED'])
        self.assertEqual(r['chapters']['b']['status'], 'ESCALATED_HUMAN_DECISION_REQUIRED')

    def test_cli_unconfigured_is_fail_closed(self):
        from exam_mastery.runtime import main
        root = F.make('math', str(self.d / 'c2'))
        with mock.patch.dict(os.environ, {'EXAM_MASTERY_CONFIG': str(self.d / 'missing.json')}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(root)]), 3)


class Comparison(Base):
    def test_replay_requires_identical_request_bytes_and_probes_are_explicit(self):
        from exam_mastery.compare import recorded_request, run_probes
        att = self.d / 'run' / 'provider_evidence' / 'chapter_author' / 'attempt-001'; att.mkdir(parents=True)
        (att / 'request.txt').write_text('PROMPT')
        (att / 'process.json').write_text(json.dumps({'status': 'SUCCEEDED', 'request_sha256': hashlib.sha256(b'PROMPT').hexdigest()}))
        self.assertEqual(recorded_request(self.d / 'run')[0], 'PROMPT')
        (att / 'request.txt').write_text('PROMPT <REDACTED>')
        with self.assertRaises(ContractError):
            recorded_request(self.d / 'run')
        author = {'blocks': [{'block_id': 'b-mature-lead', 'title': 'Mature lead', 'body': 'A plus C gives 250 k€'}]}
        probes = [{'probe_id': 'p', 'description': 'd', 'block_regex': 'mature', 'must_not_match': r'A\s*(\+|plus)\s*C', 'must_match': r'75'}]
        self.assertEqual(run_probes(author, probes)[0]['status'], 'FAIL')
        author['blocks'][0]['body'] = 'Gap 225 - 150 = 75 k€'
        self.assertEqual(run_probes(author, probes)[0]['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
