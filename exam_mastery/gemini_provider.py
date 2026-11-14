"""Direct Google Gemini API provider (official Google GenAI SDK, `google-genai`), same contract as Provider.ask().

Guarantees (mirroring the codex path):
- fail-closed: no request without an attached ResourceBudget reservation; the model id is checked first;
- exactly one HTTP attempt per reservation: the SDK's own retries (default up to 5 on 408/429/5xx) are disabled;
- hard per-request timeout = min(provider timeout, remaining budget seconds), passed to the SDK in milliseconds;
- max_output_tokens is enforced by the API (output incl. thinking is charged; see normalize_usage('gemini'));
- structured output: response_mime_type=application/json plus the role's JSON schema (role_schemas.py); the existing
  contract validators still run afterwards, so a schema is never trusted on its own;
- usage, cached tokens, finish reason, HTTP error code/status and an estimated cost are recorded per request;
- the API key comes from the environment (GEMINI_API_KEY / GOOGLE_API_KEY) or a 0600 key file; it is never written
  to evidence, logs or artifacts (redact() also masks *API_KEY* environment values).
"""
from __future__ import annotations
import hashlib, json, os, re, stat, time
from pathlib import Path
from .common import ContractError, extract_json, write_json
from .budget import BudgetBlocked, normalize_usage, BUDGET_BLOCKED
from .providers import ProviderError, ModelUnavailable, MODEL_UNAVAILABLE, redact

# Model ids and list prices (USD per 1M tokens, paid tier, standard), from ai.google.dev/gemini-api/docs/models and
# /pricing as read on 2026-11-06. Prices change: 'valid_until' marks announced changes; cost is always an ESTIMATE.
PRICING_AS_OF = '2026-11-06'
GEMINI_MODELS = {
    'gemini-3.8-flash': {'input': 0.75, 'cached_input': 0.075, 'output': 3.75, 'max_output': 65536, 'valid_until': '2026-12-31',
                         'thinking_levels': ('low', 'medium', 'high')},
    'gemini-4-argon': {'input': 2.00, 'cached_input': 0.10, 'output': 10.00, 'max_output': 65536, 'valid_until': '2026-11-30',
                       'thinking_levels': ('low', 'medium', 'high'), 'paid_tier_only': True},
    'gemini-3.5-flash-lite': {'input': 0.30, 'cached_input': 0.03, 'output': 2.50, 'max_output': 65536, 'valid_until': None,
                              'thinking_levels': ()},
    'gemini-3.1-pro-preview': {'input': 2.00, 'cached_input': 0.20, 'output': 12.00, 'max_output': 65536, 'valid_until': None,
                               'thinking_levels': (), 'preview': True, 'long_context_price': {'over_tokens': 200000, 'input': 4.00,
                                                                                            'cached_input': 0.40, 'output': 18.00}},
}
_MODEL_RE = re.compile(r'gemini-[a-z0-9][a-z0-9.\-]{1,60}')
RATE_LIMIT, QUOTA_BLOCKED_STATE = 'RATE_LIMITED', 'QUOTA_BLOCKED'
BLOCKING_FINISH = {'SAFETY', 'RECITATION', 'BLOCKLIST', 'PROHIBITED_CONTENT', 'SPII', 'LANGUAGE', 'OTHER', 'MALFORMED_RESPONSE'}


def check_gemini_model(model, allow_unlisted=False):
    """Fail-closed id check before any reservation. Unlisted ids need explicit opt-in (no price known)."""
    if not isinstance(model, str) or not _MODEL_RE.fullmatch(model):
        raise ModelUnavailable(model, 'invalid Gemini model id')
    if model not in GEMINI_MODELS and not allow_unlisted:
        raise ModelUnavailable(model, f'not in the reviewed Gemini model list {sorted(GEMINI_MODELS)} (pricing unknown); '
                                      'set allow_unlisted_model in the product config to use it')
    return model


def estimate_cost(model, usage):
    """USD estimate from normalized usage; None when the model has no reviewed price."""
    p = GEMINI_MODELS.get(model)
    if not p or not usage:
        return None
    if p.get('long_context_price') and usage['input'] > p['long_context_price']['over_tokens']:
        p = {**p, **p['long_context_price']}
    fresh = usage['input'] - usage['cached_input']
    return round((fresh * p['input'] + usage['cached_input'] * p['cached_input'] + usage['output'] * p['output']) / 1e6, 6)


def load_api_key(key_file=None):
    """API key from GOOGLE_API_KEY / GEMINI_API_KEY (SDK precedence) or from a key file readable only by the owner."""
    for var in ('GOOGLE_API_KEY', 'GEMINI_API_KEY'):
        if os.environ.get(var, '').strip():
            return os.environ[var].strip(), f'env:{var}'
    if key_file:
        p = Path(key_file).expanduser()
        if not p.is_file():
            raise ContractError(f'Gemini key file missing: {p}')
        if stat.S_IMODE(p.stat().st_mode) & 0o077:
            raise ContractError(f'Gemini key file {p} is readable by others; chmod 600 it')
        key = p.read_text().strip()
        if key:
            return key, f'file:{p.name}'
    raise ContractError('No Gemini API key: set GEMINI_API_KEY or configure a 0600 key file')


def _default_client(api_key, timeout_ms):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms, retry_options=types.HttpRetryOptions(attempts=1)))


def _dump(obj):
    if obj is None:
        return None
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(exclude_none=True, mode='json')
    return obj if isinstance(obj, (dict, list, str, int, float)) else str(obj)


class GeminiProvider:
    """ask(role, prompt, run_dir) -> parsed JSON object; same evidence layout as Provider (provider_evidence/<role>)."""
    name = 'gemini'; external = True; synthetic = False

    def __init__(self, model, timeout=600, budget=None, key_file=None, max_output_tokens=None, thinking_level=None,
                 structured=True, allow_unlisted_model=False, client_factory=None):
        self.model, self.timeout, self.budget = model, timeout, budget
        self.key_file, self.max_output_tokens, self.thinking_level = key_file, max_output_tokens, thinking_level
        self.structured, self.allow_unlisted_model = structured, allow_unlisted_model
        self.client_factory = client_factory or _default_client

    def fingerprint(self):
        return {'name': 'gemini', 'model': self.model, 'protocol': 5, 'structured': bool(self.structured),
                'thinking_level': self.thinking_level, 'max_output_tokens': self.max_output_tokens}

    def _config(self, role, max_out):
        from .role_schemas import schema_for
        cfg = {'response_mime_type': 'application/json', 'max_output_tokens': max_out}
        if self.structured and schema_for(role):
            cfg['response_json_schema'] = schema_for(role)
        if self.thinking_level:
            levels = GEMINI_MODELS.get(self.model, {}).get('thinking_levels') or ()
            if levels and self.thinking_level not in levels:
                raise ContractError(f'thinking level {self.thinking_level!r} not supported by {self.model} (allowed {levels})')
            cfg['thinking_config'] = {'thinking_level': self.thinking_level}
        return cfg

    def ask(self, role, prompt, run_dir, fixture_dir=None, images=None):
        run_dir = Path(run_dir); base = run_dir / 'provider_evidence' / role; base.mkdir(parents=True, exist_ok=True)
        attempt = base / f'attempt-{len(list(base.glob("attempt-*"))) + 1:03d}'; attempt.mkdir()
        (attempt / 'request.txt').write_text(redact(prompt))
        record = {'provider': 'gemini', 'model': self.model, 'role': role, 'request_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                  'started': time.time(), 'status': 'STARTED', 'http_attempts_allowed': 1, 'pricing_as_of': PRICING_AS_OF}
        write_json(attempt / 'process.json', record)
        reservation = None; sent = False; quota = False; raw_text = ''
        try:
            if images:
                raise ContractError('Gemini adapter has no validated image transport; refusing to discard images')
            if self.budget is None:
                raise BudgetBlocked(BUDGET_BLOCKED, 'no ResourceBudget attached to external provider')
            check_gemini_model(self.model, self.allow_unlisted_model)
            api_key, key_source = load_api_key(self.key_file); record['api_key_source'] = key_source   # source only, never the key
            max_out = int(min(self.max_output_tokens or 10 ** 9, self.budget.config['max_output_tokens_per_call'],
                              GEMINI_MODELS.get(self.model, {}).get('max_output', 65536)))
            cfg = self._config(role, max_out); record['max_output_tokens'] = max_out
            record['structured_output'] = 'response_json_schema' in cfg
            reservation = self.budget.reserve(role, prompt, 0, 'gemini'); record['budget_reservation'] = reservation
            timeout = min(self.timeout, self.budget.remaining_seconds())
            if timeout <= 0:
                raise BudgetBlocked(BUDGET_BLOCKED, 'max_wall_seconds reached')
            record['timeout_seconds'] = timeout
            client = self.client_factory(api_key, int(timeout * 1000))
            sent = True
            resp = client.models.generate_content(model=self.model, contents=prompt, config=cfg)
            usage = _dump(getattr(resp, 'usage_metadata', None)); record['usage'] = usage
            cands = getattr(resp, 'candidates', None) or []
            finish = str(getattr(cands[0], 'finish_reason', None) or '').split('.')[-1] if cands else None
            record['finish_reason'] = finish; record['model_version'] = getattr(resp, 'model_version', None)
            fb = _dump(getattr(resp, 'prompt_feedback', None))
            if fb and fb.get('block_reason'):
                record['prompt_block_reason'] = fb['block_reason']
                raise ContractError(f"prompt blocked by provider: {fb['block_reason']}")
            if finish == 'MAX_TOKENS':
                record['classification'] = 'OUTPUT_LIMIT'
                raise ContractError(f'output truncated at max_output_tokens={max_out}')
            if finish in BLOCKING_FINISH:
                raise ContractError(f'generation stopped by provider: {finish}')
            raw_text = getattr(resp, 'text', None) or ''
            (attempt / 'answer.txt').write_text(redact(raw_text))
            obj = extract_json(raw_text)
            record['status'] = 'SUCCEEDED'
            (attempt / 'response.json').write_text(json.dumps(obj, ensure_ascii=False, indent=2))
            return obj
        except BudgetBlocked as e:
            record.update(status=e.state, error_type='BudgetBlocked', error=redact(e), classification=e.state)
            e.record.update(record); raise
        except ModelUnavailable as e:
            record.update(status=MODEL_UNAVAILABLE, error_type='ModelUnavailable', error=redact(e), classification=MODEL_UNAVAILABLE); raise
        except Exception as e:
            code, status = getattr(e, 'code', None), getattr(e, 'status', None)
            record.update(http_code=code, http_status=status)
            if code == 429 or status == 'RESOURCE_EXHAUSTED':
                quota = True; cls = RATE_LIMIT
            elif code == 404:
                cls = MODEL_UNAVAILABLE; record['model_unavailable'] = True
            elif code in (401, 403):
                cls = 'AUTH_OR_PERMISSION'
            elif code is not None and code >= 500:
                cls = 'PROVIDER_SERVER_ERROR'
            elif 'timed out' in str(e).lower() or type(e).__name__ in ('ReadTimeout', 'TimeoutException', 'ConnectTimeout'):
                cls = 'TIMEOUT'
            else:
                cls = record.get('classification') or 'PROTOCOL_ERROR'
            record.update(status='FAILED', error_type=type(e).__name__, error=redact(e), classification=cls)
            if cls == RATE_LIMIT:
                record['classification'] = 'USAGE_LIMIT'          # same sticky QUOTA_BLOCKED handling as the codex path
            raise ProviderError(f'gemini/{role}: {redact(e)}; evidence: {attempt}', record) from e
        except BaseException as e:
            record.update(status='INTERRUPTED', error_type=type(e).__name__, classification='INTERRUPTED'); raise
        finally:
            if reservation is not None:
                if not sent:
                    self.budget.release(reservation, 'request not sent')
                else:
                    usage = normalize_usage('gemini', record.get('usage')) if record.get('usage') else None
                    cost = estimate_cost(self.model, usage)
                    record['usage_normalized'] = usage; record['cost_usd_estimate'] = cost
                    record['usage_status'] = self.budget.commit(
                        reservation, usage, 'SUCCEEDED' if record['status'] == 'SUCCEEDED' else record['status'], quota=quota,
                        block_reason='provider reported the requested model as unavailable' if record.get('model_unavailable') else None,
                        cost_usd=cost)
            record.update(finished=time.time(), duration_seconds=time.time() - record['started'])
            write_json(attempt / 'process.json', record)
