"""One small live Gemini call (B6.8). Sends NO course material: a synthetic two-sentence text only.

Checks: API key and model accepted; structured output with the real chapter_author schema; the answer passes the
author contract; usage fields (prompt, cached, candidates, thoughts) are present; the cost estimate; whether
candidates + thoughts stay within max_output_tokens (i.e. whether the cap covers thinking tokens).

Requires GEMINI_API_KEY (or GOOGLE_API_KEY) in the environment and the flag --i-consent.
Hard limits: 1 request, 0 retries, max_output_tokens 4096, max cost 0.10 USD, 120 s.

  ~/.local/share/exam-mastery/dev-venv/bin/python scripts/gemini_smoke_test.py --model gemini-3.8-flash --i-consent
"""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery.gemini_provider import GeminiProvider, GEMINI_MODELS
from exam_mastery.budget import ResourceBudget
from exam_mastery.production import validate_author

PROMPT = """ROLE: chapter author. Synthetic smoke test, not course material.
SOURCE ELEMENTS: el-1: "Equity capital implies co-ownership and participation in success and failure."
el-2: "Loans carry repayment and interest obligations; lenders hold no shares."
EXAM ITEMS: q-1: "Name two differences between equity and loans."
Write one EXPLANATION block for kc_ids ["kc-1"] with source_refs ["el-1","el-2"], provenance SOURCE_PARAPHRASE,
claim_support_status PENDING_SEMANTIC_REVIEW; one learning objective; empty notation, figures and open_issues;
one exam_answers entry for q-1 with status ANSWERED_FROM_SOURCE and source_refs. Return JSON only."""


def main(argv):
    if '--i-consent' not in argv:
        print('Refused: pass --i-consent (sends a synthetic prompt, no course material, to the Gemini API).'); return 2
    model = argv[argv.index('--model') + 1] if '--model' in argv else 'gemini-3.8-flash'
    price = GEMINI_MODELS.get(model)
    with tempfile.TemporaryDirectory(prefix='em-gemini-smoke-') as td:
        cfg = {'approval_id': 'gemini-smoke', 'max_requests': 1, 'max_retries': 0, 'max_wall_seconds': 120,
               'max_input_tokens': 20000, 'max_input_tokens_per_call': 20000, 'max_output_tokens': 4096, 'max_output_tokens_per_call': 4096,
               'input_overhead_tokens_per_call': 0, 'image_input_tokens': 0}
        if price:
            cfg.update(max_cost_usd=0.10, pricing={'input': price['input'], 'output': price['output']})
        p = GeminiProvider(model, timeout=120, budget=ResourceBudget(cfg, Path(td) / 'budget'), max_output_tokens=4096)
        result = {'model': model, 'course_material_sent': False}
        try:
            obj = p.ask('chapter_author', PROMPT, td)
            validate_author(obj); result['author_contract'] = 'PASS'
            result['exam_answers'] = len(obj.get('exam_answers') or [])
        except Exception as e:
            result['error'] = f'{type(e).__name__}: {e}'
        rec = json.loads(next(Path(td).glob('provider_evidence/chapter_author/attempt-*/process.json')).read_text())
        u = rec.get('usage') or {}
        out_total = (u.get('candidates_token_count') or 0) + (u.get('thoughts_token_count') or 0)
        result.update({k: rec.get(k) for k in ('status', 'classification', 'finish_reason', 'model_version', 'structured_output', 'http_code',
                                               'max_output_tokens', 'usage_normalized', 'cost_usd_estimate', 'duration_seconds', 'api_key_source')})
        result['raw_usage_fields'] = sorted(u)
        result['thinking_within_max_output_tokens'] = None if not u else out_total <= rec.get('max_output_tokens', 0)
        result['budget'] = p.budget.summary()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get('author_contract') == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
