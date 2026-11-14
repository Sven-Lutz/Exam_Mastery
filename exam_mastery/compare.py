"""Reproducible provider comparison on one already scoped chapter (B6.8).

replay: send EXACTLY the recorded author request of an earlier run (same sources, competencies, review restrictions,
        prompt bytes; verified against the recorded request SHA-256) to another provider, under a fail-closed budget.
        The answer must pass the same author contract; then the same offline preview and checks are produced.
report: compare runs on identical rubrics: deterministic checks (anchors, competencies, exam answers, figures, step
        arithmetic), reviewer-authored error probes, tokens, cost and duration. Probes and checks are evidence of
        specific properties, not a verdict on overall subject quality.

  python -m exam_mastery.compare replay --source <chapter_dir> --out <dir> --provider gemini --model <id> --budget b.json
  python -m exam_mastery.compare report --run name=<chapter_dir> --run name=<chapter_dir> [--probes p.json] --out <dir>
"""
from __future__ import annotations
import hashlib, json, re, shutil, sys
from pathlib import Path
from .common import ContractError, write_json


def recorded_request(chapter_dir, role='chapter_author'):
    att = sorted((Path(chapter_dir) / 'provider_evidence' / role).glob('attempt-*'))
    ok = [a for a in att if json.loads((a / 'process.json').read_text()).get('status') == 'SUCCEEDED']
    if not ok:
        raise ContractError(f'no successful recorded {role} request in {chapter_dir}')
    a = ok[-1]; rec = json.loads((a / 'process.json').read_text()); prompt = (a / 'request.txt').read_text()
    if hashlib.sha256(prompt.encode()).hexdigest() != rec.get('request_sha256'):
        raise ContractError('recorded request differs from its SHA-256 (redacted or changed); not a reproducible replay')
    return prompt, rec


def replay_author(source, out, provider, budget_config):
    """Same request bytes to another provider; the result is checked and previewed offline exactly like Stage A."""
    from .budget import ResourceBudget
    from .production import validate_author
    from .checkpoints import Checkpoints
    source, out = Path(source), Path(out)
    prompt, rec = recorded_request(source)
    out.mkdir(parents=True, exist_ok=True)
    for f in ('chapter_context.json',):
        shutil.copy2(source / f, out / f)
    provider.budget = ResourceBudget(budget_config, out / 'budget')
    obj = Checkpoints(out).invoke('chapter_author', prompt, provider, validate_author)
    write_json(out / 'chapter_author.json', obj)
    write_json(out / 'replay.json', {'source_run': str(source), 'request_sha256': rec['request_sha256'], 'source_provider': rec.get('provider'),
                                     'source_model': rec.get('model'), 'provider': provider.fingerprint(), 'budget': provider.budget.summary()})
    return obj


def _usage(chapter_dir):
    recs = [json.loads(p.read_text()) for p in sorted((Path(chapter_dir) / 'provider_evidence' / 'chapter_author').glob('attempt-*/process.json'))]
    recs = [r for r in recs if r.get('status') == 'SUCCEEDED'] or recs
    if not recs:
        return {}
    r = recs[-1]; u = r.get('usage_normalized') or {}
    return {'provider': r.get('provider'), 'model': r.get('model'), 'duration_seconds': round(r.get('duration_seconds') or 0, 1),
            'input_tokens': u.get('input'), 'cached_input_tokens': u.get('cached_input'), 'output_tokens': u.get('output'),
            'cost_usd_estimate': r.get('cost_usd_estimate'),
            'cost_note': 'estimate from list prices' if r.get('cost_usd_estimate') is not None else 'not measurable (subscription quota)'}


def run_probes(author, probes):
    """Reviewer-authored probes: a regex that must (or must not) occur in the text of the named blocks."""
    out = []
    for p in probes:
        blocks = [b for b in author.get('blocks', []) if not p.get('block_regex') or re.search(p['block_regex'], (b.get('title') or '') + ' ' + (b.get('block_id') or ''), re.I)]
        text = ' '.join(json.dumps(b, ensure_ascii=False) for b in blocks)
        bad = bool(p.get('must_not_match') and re.search(p['must_not_match'], text, re.I | re.S))
        good = bool(p.get('must_match') and re.search(p['must_match'], text, re.I | re.S))
        status = 'NOT_TESTED' if not blocks else 'FAIL' if bad or (p.get('must_match') and not good) else 'PASS'
        out.append({'probe_id': p['probe_id'], 'description': p['description'], 'status': status, 'blocks': len(blocks)})
    return out


def evaluate(chapter_dir, manifest, plan=None, probes=()):
    from .chapter_publish import publish_author_preview
    ch = Path(chapter_dir)
    work = ch / 'comparison_preview'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    shutil.copy2(ch / 'chapter_author.json', work / 'chapter_author.json'); shutil.copy2(ch / 'chapter_context.json', work / 'chapter_context.json')
    rep = publish_author_preview(work, manifest, plan)
    author = json.loads((ch / 'chapter_author.json').read_text())
    ctx = json.loads((ch / 'chapter_context.json').read_text())
    produce = set(ctx.get('produce_kc_ids') or [])
    covered = {k for b in author.get('blocks', []) for k in b.get('kc_ids') or []} & produce
    by = {}
    for c in rep['checks']:
        by.setdefault(c['check'], []).append(c['status'])
    count = lambda k, s: sum(x == s for x in by.get(k, []))
    words = sum(len(str(b.get(f) or '').split()) for b in author.get('blocks', []) for f in ('body', 'problem', 'result', 'interpretation'))
    return {'blocks': len(author.get('blocks', [])), 'words': words,
            'block_kinds': sorted({b.get('kind') for b in author.get('blocks', [])}),
            'competencies_treated': f'{len(covered)}/{len(produce)}',
            'anchors_allowed': f"{count('ANCHORS_ALLOWED', 'PASS')}/{len(by.get('ANCHORS_ALLOWED', []))}",
            'exam_answer_coverage': next((c['detail'] for c in rep['checks'] if c['check'] == 'EXAM_ANSWER_COVERAGE'), None),
            'figures': len(author.get('figures', [])), 'figures_labels_verbatim': f"{count('FIGURE_LABELS_VERBATIM', 'PASS')}/{len(by.get('FIGURE_LABELS_VERBATIM', []))}",
            'arithmetic': rep['arithmetic'], 'math_rendering': rep['math_rendering']['status'],
            'failed_checks': rep['failed'], 'probes': run_probes(author, probes), 'usage': _usage(ch), 'preview': str(work / 'preview')}


def report(runs, manifest, plan=None, probes=(), out=None):
    res = {name: evaluate(d, manifest, plan, probes) for name, d in runs.items()}
    doc = {'schema': 'em-provider-comparison-v1', 'runs': res,
           'note': 'Same request bytes and same deterministic checks for every run. Checks and probes test specific properties; '
                   'subject-matter quality still needs an independent reviewer.'}
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        write_json(Path(out) / 'comparison.json', doc)
        keys = ['blocks', 'words', 'competencies_treated', 'anchors_allowed', 'figures', 'figures_labels_verbatim', 'math_rendering', 'failed_checks']
        lines = ['| Kriterium | ' + ' | '.join(res) + ' |', '|---|' + '---|' * len(res)]
        lines += [f'| {k} | ' + ' | '.join(str(r[k]) for r in res.values()) + ' |' for k in keys]
        lines += ['| arithmetic verified / fail / open | ' + ' | '.join(f"{r['arithmetic']['verified_pass']}/{r['arithmetic']['arithmetic_fail']}/{r['arithmetic']['not_tested']} of {r['arithmetic']['recognised_steps']}" for r in res.values()) + ' |']
        for f in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'duration_seconds', 'cost_usd_estimate'):
            lines.append(f'| {f} | ' + ' | '.join(str(r['usage'].get(f)) for r in res.values()) + ' |')
        for p in probes:
            lines.append(f"| probe {p['probe_id']} | " + ' | '.join(next(x['status'] for x in r['probes'] if x['probe_id'] == p['probe_id']) for r in res.values()) + ' |')
        (Path(out) / 'COMPARISON.md').write_text('# Provider-Vergleich (gleicher Request, gleiche Prüfungen)\n\n' + '\n'.join(lines) + '\n\n' + doc['note'] + '\n')
    return doc


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] not in ('replay', 'report'):
        print(__doc__); return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == 'replay':
        from .budget import load_budget_config
        from .gemini_provider import GeminiProvider
        from .providers import Provider
        prov = GeminiProvider(opt('--model')) if opt('--provider') == 'gemini' else Provider('codex', model=opt('--model'))
        replay_author(opt('--source'), opt('--out'), prov, load_budget_config(opt('--budget')))
        print(json.dumps(json.loads((Path(opt('--out')) / 'replay.json').read_text()), indent=2)); return 0
    from .chapters import dry_run
    runs = dict(x.split('=', 1) for x in [a[i + 1] for i, v in enumerate(a) if v == '--run'])
    probes = json.loads(Path(opt('--probes')).read_text())['probes'] if opt('--probes') else []
    plan_dir = Path(opt('--out')) / 'plan'
    if not opt('--root'):
        raise ContractError('--root <lecture folder> is needed to rebuild the manifest offline')
    _, plan, manifest, _, _ = dry_run(Path(opt('--root')), plan_dir, None)
    doc = report(runs, manifest, plan, probes, opt('--out'))
    print(json.dumps({k: {x: v[x] for x in ('competencies_treated', 'failed_checks', 'usage')} for k, v in doc['runs'].items()}, indent=2)); return 0


if __name__ == '__main__':
    raise SystemExit(main())
