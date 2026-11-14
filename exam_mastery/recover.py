"""Recovery of an interrupted chapter run without repeating successful model calls (B7.1).

Checkpoint keys bind the prompt AND the engine identity, so after an engine fix a normal resume regenerates
every role. Recovery instead reuses the RECORDED outputs of the roles that already succeeded (hash-verified
against their evidence), runs them through the CURRENT contracts and stage gates, and calls the provider only
for the roles that never produced an output. The original run directory is never modified; everything goes to
a new directory, and every reused output is listed with its origin and SHA-256.

Engine corrections of a recorded output (e.g. a wrong worked example) are applied only from an explicit
corrections file: each one replaces one block, cites source elements, names the deterministic check that failed
and keeps the original block hash. Nothing is marked as reviewed.

    python -m exam_mastery.recover <run>/chapters/<chapter_id> --out <dir> [--corrections c.json]   # offline
    python -m exam_mastery.recover ... --live [--config c.json] [--max-requests 3]                   # continue (paid)
"""
import argparse, hashlib, json, sys, time
from pathlib import Path
from .common import ContractError, write_json

REUSABLE = ('chapter_author', 'chapter_assessment', 'chapter_solutions', 'chapter_semantic_review', 'chapter_risk_review')


class LiveCallRequired(ContractError):
    def __init__(self, role):
        self.role = role
        super().__init__(f'LIVE_CALL_REQUIRED: {role} has no recorded output; offline recovery stops here')


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def recorded_outputs(chapter_dir):
    """{role: (obj, origin)} for roles with a recorded model answer. Solutions refused by the old contract count as
    recorded: the answer is the model's, unchanged (verified against the raw provider evidence)."""
    d = Path(chapter_dir); out = {}
    for role in REUSABLE:
        ok = d / (role + '.json')
        cands = [ok] if ok.exists() else sorted(d.glob(role + '.invalid-*.json'))
        if not cands:
            continue
        p = cands[0]
        raw = (d / 'provider_evidence' / role / 'attempt-001' / 'answer.txt')
        obj = json.loads(p.read_text())
        same = raw.exists() and json.loads(raw.read_text()) == obj
        out[role] = (obj, {'file': p.name, 'sha256': _sha(p.read_bytes()), 'raw_answer_sha256': _sha(raw.read_bytes()) if raw.exists() else None,
                           'matches_raw_provider_answer': same, 'refused_by_old_contract': p.name.startswith(role + '.invalid')})
    return out


def apply_corrections(author, corrections, ctx):
    """Replace blocks per correction record; returns (new_author, applied records). Original is not modified."""
    from .examples import check_block
    a = json.loads(json.dumps(author)); applied = []
    allowed = set(ctx['allowed_source_refs'])
    for c in corrections:
        i = next((k for k, b in enumerate(a['blocks']) if b['block_id'] == c['block_id']), None)
        if i is None:
            raise ContractError(f"correction for unknown block {c['block_id']}")
        old = a['blocks'][i]; new = dict(c['replacement'], block_id=c['block_id'])
        if not set(new.get('source_refs') or []) <= allowed:
            raise ContractError(f"correction {c['block_id']} cites elements outside the chapter package")
        before = check_block(old, ctx['source_elements']); after = check_block(new, ctx['source_elements'])
        if not any(s == 'FAIL' for s, _ in before) or any(s == 'FAIL' for s, _ in after):
            raise ContractError(f"correction {c['block_id']} is only accepted for a block that fails the check and must pass it")
        a['blocks'][i] = new
        applied.append({'block_id': c['block_id'], 'reason': c['reason'], 'check_before': before, 'check_after': after,
                        'original_block_sha256': _sha(json.dumps(old, sort_keys=True, ensure_ascii=False).encode()),
                        'kind': 'ENGINE_SOURCE_CORRECTION', 'reviewed': False})
    return a, applied


class RecordedProvider:
    """Serves recorded outputs for reused roles; delegates everything else to `live` (or stops offline)."""
    external = False

    def __init__(self, recorded, live=None):
        self.recorded = recorded; self.live = live
        self.budget = getattr(live, 'budget', None)
        self.external = bool(live is not None and getattr(live, 'external', True))
        self.served = []

    def fingerprint(self):
        base = self.live.fingerprint() if self.live is not None else {'name': 'offline-recovery', 'model': None, 'protocol': 4}
        return {**base, 'recovery': {r: o[1]['sha256'] for r, o in sorted(self.recorded.items())}}

    def ask(self, role, prompt, run_dir, fixture_dir=None, images=None):
        if role in self.recorded and role not in self.served:
            self.served.append(role)       # once per role: a contract repair never re-serves the same answer
            return json.loads(json.dumps(self.recorded[role][0]))
        if self.live is None:
            raise LiveCallRequired(role)
        return self.live.ask(role, prompt, run_dir, images=images)


def recover(chapter_dir, out, corrections=None, live=None, reuse_from=(), revision=None):
    from .auto_scope import apply as auto_scope_apply
    from .chapters import chapter_context
    from .production import produce_chapter
    chapter_dir = Path(chapter_dir); run = chapter_dir.parent.parent; cid = chapter_dir.name
    out = Path(out)
    if out.resolve() == chapter_dir.resolve() or chapter_dir.resolve() in out.resolve().parents:
        raise ContractError('recovery output must be outside the original chapter directory')
    out.mkdir(parents=True, exist_ok=True)
    plan = json.loads((run / 'plan' / 'curriculum.json').read_text())
    manifest = json.loads((run / 'plan' / 'source_inventory.json').read_text())
    gates = json.loads((run / 'plan' / 'chapter_gates.json').read_text()); gates = gates.get('gates', gates)
    gate = auto_scope_apply(plan, manifest, gates)[cid]           # current engine scope
    rec = recorded_outputs(chapter_dir)
    for d in reuse_from:  # B7.3: outputs of an earlier recovery (e.g. its reviews); the original run takes precedence
        for role, v in recorded_outputs(d).items():
            if role not in rec and role != 'chapter_author':
                rec[role] = (v[0], {**v[1], 'from_dir': str(d)})
    report = {'schema': 'em-recovery-v1', 'source_chapter_dir': str(chapter_dir), 'chapter_id': cid, 'started': time.time(),
              'reused': {r: o[1] for r, o in rec.items()}, 'corrections': [], 'live_calls': [], 'academic_release': 'NOT_TESTED'}
    if revision is not None:
        # B7.4: a documented delta revision written outside the engine (e.g. in an agent session when the provider
        # quota is exhausted). It passes the same merge, contracts and post-revision gate as a provider revision.
        rec['chapter_revision'] = (revision['delta'], {'file': 'session_revision', 'sha256': _sha(json.dumps(revision, sort_keys=True).encode()),
                                                       'reviser': revision.get('reviser'), 'matches_raw_provider_answer': None,
                                                       'refused_by_old_contract': False})
    if corrections:
        ctx = chapter_context(plan, manifest, cid, gate)
        new, applied = apply_corrections(rec['chapter_author'][0], corrections, ctx)
        rec['chapter_author'] = (new, {**rec['chapter_author'][1], 'corrected': True})
        report['corrections'] = applied
        write_json(out / 'corrections_applied.json', applied)
    prov = RecordedProvider(rec, live)
    try:
        ast_, rep = produce_chapter(plan, manifest, cid, gate, out, prov)
        report.update(result='CONTENT_AST_BUILT', ast_status=ast_['status'], technical=rep['technical_status'])
    except LiveCallRequired as e:
        report.update(result='STOPPED_BEFORE_LIVE_CALL', next_role=e.role)
    except Exception as e:
        report.update(result='FAILED', error=f'{type(e).__name__}: {e}')
    report['served_from_record'] = prov.served
    report['stage_gates'] = json.loads((out / 'stage_gates.json').read_text()) if (out / 'stage_gates.json').exists() else []
    write_json(out / 'recovery_report.json', report)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(prog='exam_mastery.recover')
    ap.add_argument('chapter_dir'); ap.add_argument('--out', required=True); ap.add_argument('--corrections')
    ap.add_argument('--live', action='store_true', help='call the configured provider for the roles without a recorded output')
    ap.add_argument('--config', help='product config (default: ~/.config/exam-mastery/config.json)')
    ap.add_argument('--max-requests', type=int, default=3, help='hard cap for live calls incl. contract repairs')
    ap.add_argument('--reuse-from', action='append', default=[], help='earlier recovery dir whose recorded outputs are reused')
    ap.add_argument('--revision-file', help='documented delta revision (em-session-revision-v1) used instead of a provider revision')
    ap.add_argument('--publish', action='store_true', help='publish the chapter after a successful build (deterministic, offline)')
    a = ap.parse_args(argv)
    corr = json.loads(Path(a.corrections).read_text())['corrections'] if a.corrections else None
    live = None
    if a.live:
        from .product import load_config, make_provider, policy_budget
        from .budget import ResourceBudget, validate_config
        cfg = load_config(a.config)
        if cfg is None:
            raise ContractError('no product configuration; run exam-mastery --setup first')
        live = make_provider(cfg)
        b = validate_config(dict(policy_budget(cfg), max_requests=a.max_requests,
                                 max_retries=min(a.max_requests - 1, policy_budget(cfg)['max_retries'])))
        live.budget = ResourceBudget(b, Path(a.out) / 'budget')
    rev = json.loads(Path(a.revision_file).read_text()) if a.revision_file else None
    if rev is not None and rev.get('schema') != 'em-session-revision-v1':
        raise ContractError('revision file must use schema em-session-revision-v1')
    r = recover(a.chapter_dir, a.out, corr, live, a.reuse_from, rev)
    if a.publish and r['result'] == 'CONTENT_AST_BUILT' and r.get('ast_status') != 'DRAFT_TECHNICAL_PASS_PENDING_REVIEW':
        # B7.4: same rule as the product run: a chapter that fails a gate is never published
        r['publish'] = {'status': 'NOT_PUBLISHED_GATE_FAILED', 'ast_status': r.get('ast_status')}
        write_json(Path(a.out) / 'recovery_report.json', r)
        print(json.dumps(r['publish'], ensure_ascii=False, indent=2))
    elif a.publish and r['result'] == 'CONTENT_AST_BUILT':
        from .chapter_publish import publish_chapter
        run = Path(a.chapter_dir).parent.parent
        try:
            pr = publish_chapter(a.out, json.loads((run / 'plan' / 'source_inventory.json').read_text()),
                                 json.loads((run / 'plan' / 'curriculum.json').read_text()), assets_root=run / 'plan')
            r['publish'] = {'status': 'PUBLISHED_PREVIEW', 'products': pr['products']}
        except Exception as e:
            r['publish'] = {'status': 'FAILED', 'error': f'{type(e).__name__}: {e}'}
        write_json(Path(a.out) / 'recovery_report.json', r)
        print(json.dumps(r['publish'], ensure_ascii=False, indent=2, default=str)[:3000])
    print(json.dumps({k: r[k] for k in ('result', 'served_from_record') if k in r} | {'next_role': r.get('next_role'), 'error': r.get('error'),
                      'stage_gates': [(g['after'], g['result'], g['counts']) for g in r['stage_gates']]}, ensure_ascii=False, indent=2))
    return 0 if r['result'] in ('CONTENT_AST_BUILT', 'STOPPED_BEFORE_LIVE_CALL') else 2


if __name__ == '__main__':
    sys.exit(main())
