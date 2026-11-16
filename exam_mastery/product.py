"""Product mode (B6.8): one folder in, learning materials out, without per-run signatures.

One-time setup writes ~/.config/exam-mastery/config.json (or $EXAM_MASTERY_CONFIG): provider, model, the user's
data-transfer consent and a usage/cost policy. Each `start <folder>` then:
  1. checks sources and scope automatically (production_preflight_auto: uncertain competencies and textless pages are
     excluded, never produced; only non-resolvable chapter problems escalate to a human);
  2. builds a fail-closed ResourceBudget from the policy (fresh approval_id per run, bound to the policy hash);
  3. generates, validates (stage gates, quality gates, one bounded revision round) and publishes chapters that pass;
  4. writes a quality dossier per chapter and for the course: eight dimensions, each PASS / FAIL / NOT_TESTED.
Experimental pilot runs with human-signed scope decisions stay available unchanged (--budget/--review-decisions).
A model review is never treated as proof: the academic release is never granted automatically.
"""
from __future__ import annotations
import hashlib, json, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from .common import ContractError, write_json

CONFIG_SCHEMA = 'em-product-config-v1'
DEFAULT_POLICY = {'max_cost_usd_per_run': 5.0, 'max_requests_per_run': 30, 'max_wall_seconds_per_run': 6 * 3600,
                  'max_input_tokens_per_call': 400000, 'max_output_tokens_per_call': 32000,
                  # B7: one contract repair costs one more call inside max_requests; 0 made any format slip fatal
                  'max_contract_repairs_per_run': 2}


def config_path():
    if os.environ.get('EXAM_MASTERY_CONFIG'):
        return Path(os.environ['EXAM_MASTERY_CONFIG']).expanduser()
    if (sys.argv and 'unittest' in str(sys.argv[0])) or 'PYTEST_CURRENT_TEST' in os.environ or 'pytest' in sys.modules:
        # never read the user's real config (and spend real money) from the offline test suite
        return Path('/nonexistent/exam-mastery-test-isolation/config.json')
    return Path.home() / '.config' / 'exam-mastery' / 'config.json'


def setup(provider, model, accept_data_transfer, policy=None, key_file=None, thinking_level=None, allow_unlisted_model=False, path=None):
    """Write the one-time product configuration. The API key is never stored here."""
    if not accept_data_transfer:
        raise ContractError('Setup needs explicit consent to send course material to the provider (--accept-data-transfer)')
    if provider == 'claude':
        # The claude CLI adapter exists (providers.Provider) but has never run live against the product contracts;
        # it is not offered until it has. No silent substitution by another provider either.
        raise ContractError('provider claude (nested claude CLI) is not offered: inside Claude Code use --provider agent, '
                            'where the calling session answers the roles itself; or codex / gemini')
    if provider not in ('gemini', 'codex', 'agent'):
        raise ContractError('provider must be agent, codex or gemini')
    if provider == 'agent':
        model = model or 'calling-agent'
    if provider == 'gemini':
        from .gemini_provider import check_gemini_model
        check_gemini_model(model, allow_unlisted_model)
    pol = dict(DEFAULT_POLICY, **(policy or {}))
    _validate_policy(pol)
    cfg = {'schema': CONFIG_SCHEMA, 'provider': provider, 'model': model, 'key_file': key_file, 'thinking_level': thinking_level,
           'allow_unlisted_model': bool(allow_unlisted_model), 'usage_policy': pol,
           'data_transfer_consent': {'accepted': True, 'provider': provider, 'model': model,
                                     'accepted_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                                     'statement': f'Course material from folders I start is sent to {provider} ({model}) for generation.'},
           'notes': ['agent: the calling agent session (e.g. Claude Code) answers every role; no second model process is started.' if provider == 'agent' else
                     'Gemini free tier: Google may use content to improve products; paid tier: not used (ai.google.dev pricing page).',
                     'codex: token and cost limits are not enforced by the provider.' if provider == 'codex' else
                     'gemini: max_output_tokens is enforced by the API; cost is an estimate from list prices.']}
    p = Path(path) if path else config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    write_json(p, cfg)
    os.chmod(p, 0o600)
    return p, cfg


def _validate_policy(pol):
    for k in DEFAULT_POLICY:
        v = pol.get(k)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ContractError(f'usage_policy.{k} must be a positive number')


def load_config(path=None):
    p = Path(path) if path else config_path()
    if not p.exists():
        return None
    cfg = json.loads(p.read_text())
    if cfg.get('schema') != CONFIG_SCHEMA:
        raise ContractError(f'{p}: not an Exam Mastery product config')
    if 'api_key' in json.dumps(cfg).lower().replace('api_key_source', ''):
        raise ContractError(f'{p}: an API key must not be stored in the config; use GEMINI_API_KEY or a 0600 key file')
    if not (cfg.get('data_transfer_consent') or {}).get('accepted'):
        raise ContractError(f'{p}: no data-transfer consent recorded; run --setup again')
    cfg['usage_policy'] = dict({'max_contract_repairs_per_run': 2}, **cfg['usage_policy'])  # configs from B6.8
    _validate_policy(cfg['usage_policy'])
    return cfg


def make_provider(cfg):
    if cfg['provider'] == 'gemini':
        from .gemini_provider import GeminiProvider
        return GeminiProvider(cfg['model'], key_file=cfg.get('key_file'), thinking_level=cfg.get('thinking_level'),
                              max_output_tokens=cfg['usage_policy']['max_output_tokens_per_call'],
                              allow_unlisted_model=cfg.get('allow_unlisted_model', False))
    if cfg['provider'] == 'agent':
        from .providers import AgentProvider
        return AgentProvider()
    from .providers import Provider
    return Provider('codex', model=cfg['model'])


def policy_budget(cfg, resume_of=None):
    """ResourceBudget config derived from the stored policy: same fail-closed fields, fresh approval_id per run."""
    pol = cfg['usage_policy']
    h = hashlib.sha256(json.dumps({'policy': pol, 'consent': cfg['data_transfer_consent'], 'model': cfg['model']}, sort_keys=True).encode()).hexdigest()[:10]
    b = {'approval_id': f"policy-{h}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
         'max_requests': int(pol['max_requests_per_run']), 'max_retries': int(pol.get('max_contract_repairs_per_run', 2)), 'max_wall_seconds': pol['max_wall_seconds_per_run'],
         'max_input_tokens_per_call': pol['max_input_tokens_per_call'], 'max_output_tokens_per_call': pol['max_output_tokens_per_call'],
         'max_input_tokens': pol['max_input_tokens_per_call'] * int(pol['max_requests_per_run']),
         'max_output_tokens': pol['max_output_tokens_per_call'] * int(pol['max_requests_per_run']),
         'input_overhead_tokens_per_call': 0, 'image_input_tokens': 0, 'authorize_resume_of': resume_of}
    if cfg['provider'] == 'gemini':
        from .gemini_provider import GEMINI_MODELS
        price = GEMINI_MODELS.get(cfg['model'])
        if price:
            b['max_cost_usd'] = pol['max_cost_usd_per_run']; b['pricing'] = {'input': price['input'], 'output': price['output']}
    return b


def _resumable_run(root, output_base=None):
    """The interrupted product run of this folder, if any: starting the folder again is the user's consent to continue."""
    from .runtime import _base
    from .checkpoints import digest
    root = Path(root).expanduser().resolve()
    course = _base(root, output_base) / ('course-' + digest(str(root))[:12])
    ptr = course / 'active_chapters.json'
    if not ptr.exists():
        return None
    run = Path(json.loads(ptr.read_text()).get('run_dir', ''))
    st = run / 'status.json'
    return run.name if st.exists() and json.loads(st.read_text()).get('resumable') else None


def run_product(root, cfg=None, output_base=None, provider=None, only_chapter=None):
    """`start <folder>` in product mode."""
    from .runtime import run_chapters
    cfg = cfg or load_config()
    if cfg is None:
        raise ContractError('No product configuration. Run once: start --setup --provider gemini --model <id> --accept-data-transfer')
    provider = provider or make_provider(cfg)
    # human scope decisions (e.g. a competency the planner missed) live next to the course output, never in the lecture
    # folder: <course output>/scope_decisions.json (em-semantic-decisions-v1); they change the plan and the run identity
    from .incremental import course_dir
    sd = course_dir(root) / 'scope_decisions.json'
    out, status = run_chapters(root, provider=provider, output_base=output_base, budget_config=policy_budget(cfg, None if only_chapter else _resumable_run(root, output_base)),
                               mode='production', only_chapter=only_chapter, decisions=str(sd) if sd.exists() else None)
    if status.get('run_state') == 'AGENT_TURN_REQUIRED':
        nxt = sorted(Path(out).glob('chapters/*/agent_io/NEXT.json'), key=lambda p: p.stat().st_mtime)
        status['agent_next'] = str(nxt[-1]) if nxt else None
    dossier = course_dossier(out, status)
    write_json(Path(out) / 'quality_dossier.json', dossier)
    titles = {}
    try:
        titles = {c['chapter_id']: (c.get('position'), c['title']) for c in json.loads((Path(out) / 'plan' / 'curriculum.json').read_text())['chapters']}
    except (OSError, ValueError, KeyError):
        pass
    for cid, d in (dossier.get('chapters') or {}).items():
        pos, title = titles.get(cid, (None, cid))
        name = f"{int(pos):02d}_" if isinstance(pos, int) else ''
        deliver_chapter(Path(out) / 'chapters' / cid, Path(out) / 'LERNMATERIAL' / (name + re.sub(r'[^A-Za-z0-9ÄÖÜäöüß]+', '_', title).strip('_')), d, title)
    status['quality_dossier'] = {'release': dossier['release'], 'path': str(Path(out) / 'quality_dossier.json')}
    write_json(Path(out) / 'status.json', status)
    return out, status, dossier


# ------------------------------------------------------------------ delivery folder (B7.4)

DOC_NOTE = {'1_Lehrbuch.pdf': 'Lehrbuch', '2_Arbeitsbuch.pdf': 'Arbeitsbuch: Übungsstufen, integrierte Probeklausur, vollständige Lösungen am Ende',
            '3_Probeklausur_einzeln.pdf': 'Probeklausur als Einzelheft (identisch mit dem Klausurteil des Arbeitsbuchs, ohne Lösungen)',
            '6_Quellenabbildungen.pdf': 'Folien mit Abbildungen, mit Quelle, Seite und Auswertungsstatus'}


def _pages(pdf):
    """Measured page count of a delivered PDF (B32: the README states what the file really contains)."""
    try:
        import pymupdf
        with pymupdf.open(pdf) as d:
            return d.page_count
    except Exception:
        return '?'


def deliver_chapter(chapter_dir, target, dossier=None, label=None):
    """Copy one published chapter into a readable folder: numbered PDFs, HTML (with its formula images), Anki, dossier
    and LIES_MICH.md stating exactly what was checked and what was not. Nothing is re-rendered or changed."""
    import shutil
    chapter_dir, target = Path(chapter_dir), Path(target)
    art = chapter_dir / 'publish' / 'artifacts'
    if not (art / '1_Lehrbuch.pdf').exists():
        return None
    target.mkdir(parents=True, exist_ok=True)
    # B33: the learner HTML is the typeset textbook (same book model as the PDF, incl. edition); kapitel.html is an
    # internal AST overview without edition and is no longer delivered to learners
    html = art / '1_Lehrbuch.html' if (art / '1_Lehrbuch.html').exists() else art / 'kapitel.html'
    for f in sorted(art.glob('[0-9]_*.pdf')) + sorted(art.glob('[0-9]_*.html')) + ([] if html.name.startswith('1_') else [html]) + [art / 'kompetenzmatrix.csv']:
        if f.exists():
            shutil.copy2(f, target / f.name)
    for sub in ('assets', 'math', 'Lernumgebung', 'anki'):
        if (art / sub).is_dir():
            shutil.copytree(art / sub, target / sub, dirs_exist_ok=True)
    for f in (art / 'anki').glob('*.apkg'):
        shutil.copy2(f, target / f.name)
    dossier = dossier or chapter_dossier(chapter_dir)
    write_json(target / 'quality_dossier.json', dossier)
    d = dossier['dimensions']; cov = d['coverage']
    lines = [f"# {label or dossier.get('chapter_id')}", '',
             '**Status: Vorschau (Preview). Modellgenerierter Entwurf, technisch geprüft, fachlich NICHT unabhängig validiert.**', '',
             '| Prüfdimension | Ergebnis |', '|---|---|'] + [f'| {k} | {v["status"]} |' for k, v in d.items()] + ['',
             'PASS = maschinelle Prüfung bestanden; NOT_TESTED = nicht prüfbar ohne unabhängige Fachprüfung; FAIL = Lücke, siehe unten.', '',
             '## Dateien'] + [f'- `{f.name}` ({_pages(f)} Seiten)' + (f': {DOC_NOTE[f.name]}' if f.name in DOC_NOTE else '') for f in sorted(target.glob('[0-9]_*.pdf'))] + [
             ('- `1_Lehrbuch.html`: Lehrbuch als Webseite (identischer Inhalt wie das PDF)' if (target / '1_Lehrbuch.html').exists() else '- `kapitel.html`: Lehrbuch als Webseite (mit Formeln)')] + (['- `Lernumgebung/index.html`: interaktive Labs, offline im Browser'] if (target / 'Lernumgebung' / 'index.html').exists() else []) + [
             f'- `{f.name}`: Anki-Deck' for f in sorted(target.glob('*.apkg'))] + ['',
             '## Offene Punkte',
             f"- Gelehrt und geübt: {cov.get('produced', 0) - len(cov.get('content_gaps') or [])} von {cov.get('produced', 0)} produzierten Kompetenzen; "
             f"nicht produziert: {len(cov.get('excluded') or [])}; Überschriften von Titelfolien ohne eigenes Lernziel: {len(cov.get('not_learning_objectives') or [])}.",
             f"- Coverage-Prüfung: {cov['detail']} („with evidence“ = durch eine offizielle Prüfungsfrage mit passender Operation belegt).",
             f"- Nicht produziert (Inhalt nur in Abbildungen): {', '.join(cov.get('visual_review_required') or []) or 'keine'}",
             f"- Nur aus dem Folientext gelehrt: {len(cov.get('text_only_scope') or {})} Kompetenzen",
             '- Punkte in der Probeklausur sind neu entworfen, keine offiziellen Punktwerte.',
             '- Aufgaben mit fehlender Quelle sind als Evidenzlücke markiert und nicht Teil der Probeklausur.']
    pub = json.loads((chapter_dir / 'publish' / 'publish_report.json').read_text()) if (chapter_dir / 'publish' / 'publish_report.json').exists() else {}
    if pub.get('errata'):
        lines += ['', '## Redaktionelle Korrekturen (Errata, ohne Modellaufruf)',
                  'Diese Stellen wurden nach der Produktion begründet korrigiert. Sie sind nicht menschlich geprüft, sofern nicht anders vermerkt.']
        lines += [f"- {e['id']} `{e['target']}`: {e['reason']} Grundlage: {'; '.join(e['basis'])}. "
                  f"{'Menschlich geprüft.' if e['human_reviewed'] else 'Nicht menschlich geprüft.'}" for e in pub['errata']]
    sv, su = d.get('solution_verification'), d.get('setup_review')
    if sv:
        lines += ['', '## Prüfstand der Lösungen (ohne Modellaufruf, nicht unabhängig)', sv['detail'], '', '| Aufgabe | Ergebnis |', '|---|---|']
        lines += [f'| {k} | {r} |' for k, r in sorted(sv['by_item'].items())]
    if su:
        lines += ['', '### Lösungsansätze', su['detail']] + [f'- {k}: offen – {t}' for k, t in su['open'].items()]
    rec = chapter_dir / 'scope_recovery.json'
    if rec.exists():
        r = json.loads(rec.read_text())
        lines += ['', '## Wiederherstellung nach Planungskorrektur (ohne Modellaufruf)',
                  f"Inhalte aus dem früheren Lauf `{Path(r['source_chapter']).parent.parent.name}`; entfernt wurden nur Einträge zu "
                  f"{', '.join(r['roles'][0]['removed_ids'])} (und davon abhängige Blöcke {', '.join(r['roles'][-1].get('derived_removed_blocks') or []) or '–'}). "
                  'Die Prüfungen der Modellrollen wurden im früheren Lauf am vorherigen, umfangreicheren Inhalt durchgeführt.']
    (target / 'LIES_MICH.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return target


def _taught(chapter_dir):
    try:
        return json.loads((Path(chapter_dir) / 'content_ast.json').read_text()).get('kc_ids') or []
    except (OSError, ValueError):
        return []


def _evidenced(cov):
    m = re.match(r'(\d+)/(\d+)', cov.get('detail') or '')
    return int(m.group(1)) if m else 0


# ------------------------------------------------------------------ quality dossier

DIMENSIONS = ['coverage', 'competency_evidence', 'subject_correctness', 'math_numeric', 'didactic_completeness', 'items_and_solutions',
              'formulas_and_figures', 'anki', 'rendering']
TECHNICAL = ['math_numeric', 'items_and_solutions', 'formulas_and_figures', 'anki', 'rendering']


def _gate(q, prefix):
    return [g for k, g in (q.get('gates') or {}).items() if k.startswith(prefix)]


def _worst(statuses):
    s = set(statuses)
    return 'FAIL' if s & {'FAIL', 'BLOCKED'} else 'NOT_TESTED' if not s or s - {'PASS', 'NOT_APPLICABLE'} else 'PASS'


def _render_check(art):
    pdf, html = art / 'kapitel.pdf', art / 'kapitel.html'
    if not pdf.exists() or not html.exists():
        return 'FAIL', 'HTML or PDF missing'
    import pymupdf
    doc = pymupdf.open(pdf); pages = doc.page_count
    raw = [i + 1 for i, p in enumerate(doc) if re.search(r'\\\(|\\\[|\\frac\{|\\text\{|Formel nicht darstellbar', p.get_text())]
    h = html.read_text(encoding='utf-8')
    fails = h.count('class="math-fail"')
    if pages == 0 or raw or fails:
        return 'FAIL', f'{pages} pages; raw TeX/formula failures on pages {raw[:10]}; {fails} HTML formula failures'
    return 'PASS', f'{pages} PDF pages open; no raw TeX or formula failure in PDF text or HTML (machine check, no visual review)'


def _edition_supplemented_blocks(ch):
    """{block_id: [source ids]} for blocks an edition replaces by a supplement citing only verified subject sources."""
    from . import edition as _ed
    try:
        e = _ed.load(ch)
    except Exception:
        return {}
    if not e:
        return {}
    src = _ed.subject_sources(); out = {}
    for op in e.get('ops', []):
        blk = op.get('block') or {}
        ids = blk.get('sources') or []
        if op.get('op') == 'replace' and blk.get('prov') == 'supplement' and ids and \
                all(src.get(i, {}).get('verdict') in ('VERIFIED', 'PRIMARY_TEXT_READ') for i in ids):
            out[op['block_id']] = ids
    return out


def _verification_dims(ch, a):
    """B14: evidence layers that never grant a release. course/verification/<chapter>.json (em-solution-verification-v1:
    deterministic re-computation / source checks per item) and setup_review_<chapter>.json (em-setup-review-v1).
    A record whose item or solution changed since it was made is STALE. A CONTRADICTED record makes the layer FAIL."""
    from . import errata as _errata
    out, base = {}, ch.parent.parent.parent / 'verification'
    vp, sp = base / f'{ch.name}.json', base / f'setup_review_{ch.name}.json'
    if vp.exists():
        v = json.loads(vp.read_text())
        try:
            cur, _ = _errata.apply(a, _errata.load(ch))
        except Exception:
            cur = a
        sol = {x['item_id']: x for x in cur.get('solutions') or []}
        now = {i['item_id']: hashlib.sha256((i['prompt'] + '\x1f' + json.dumps(sol.get(i['item_id'], {}), ensure_ascii=False, sort_keys=True)).encode()).hexdigest()
               for i in cur.get('assessments') or []}
        rows = {r['item_id']: dict(r, result=('STALE' if now.get(r['item_id']) != r['content_sha256'] else r['result'])) for r in v.get('records') or []}
        missing = sorted(set(now) - set(rows))
        from collections import Counter
        c = Counter(r['result'] for r in rows.values())
        out['solution_verification'] = {
            'status': 'FAIL' if c.get('CONTRADICTED') else 'INFO',
            'detail': f"{len(rows)}/{len(now)} items checked without a model call: " + ', '.join(f'{k} {n}' for k, n in sorted(c.items()))
                      + (f"; not checked: {missing}" if missing else '') + '. Deterministic and source checks, NOT an independent review (gates stay pending).',
            'by_item': {k: r['result'] for k, r in rows.items()}, 'independence': v.get('independence')}
    if sp.exists():
        r = json.loads(sp.read_text()).get('records') or []
        from collections import Counter
        c = Counter(x['verdict'] for x in r)
        out['setup_review'] = {'status': 'FAIL' if c.get('CONTRADICTED') else 'INFO',
                               'detail': f"{len(r)} solution set-ups reviewed against the lecture: " + ', '.join(f'{k} {n}' for k, n in sorted(c.items())) + '. Reviewer not independent.',
                               'open': {x['id']: x['open'] for x in r if x.get('open')}}
    return out


def chapter_dossier(ch):
    """Eight separately judged dimensions for one produced chapter; never a single green score."""
    ch = Path(ch)
    a = json.loads((ch / 'content_ast.json').read_text())
    q = a.get('quality_report') or {}
    ctx = json.loads((ch / 'chapter_context.json').read_text()) if (ch / 'chapter_context.json').exists() else {}
    pub = json.loads((ch / 'publish' / 'publish_report.json').read_text()) if (ch / 'publish' / 'publish_report.json').exists() else None
    d = {}
    cov = a.get('kc_coverage') or []
    gaps = [r['kc_id'] for r in cov if r.get('status') != 'EVIDENCED_PENDING_SEMANTIC_REVIEW']
    answered = {e.get('item_id') for e in a.get('exam_answers') or []}
    # B14: a competency the planner itself classified NO_LEARNING_OBJECTIVE (heading of the chapter title slide,
    # citation, reading list) is not a coverage gap - provided every exam item linked to it is answered elsewhere.
    scope_p = ch.parent.parent / 'plan' / 'competency_scope.json'
    non_obj = set()
    if scope_p.exists():
        try:
            sc = json.loads(scope_p.read_text())
            rows = sc if isinstance(sc, list) else sc.get('competencies') or sc.get('rows') or []
            plan_p = ch.parent.parent / 'plan' / 'curriculum.json'
            exam_ids = {i['item_id'] for i in ctx.get('exam_items') or []}
            linked = {k['kc_id']: set(k.get('linked_item_ids') or []) & exam_ids
                      for k in (json.loads(plan_p.read_text()).get('competencies') or [])} if plan_p.exists() else {}
            non_obj = {r['kc_id'] for r in rows if isinstance(r, dict) and r.get('category') == 'NO_LEARNING_OBJECTIVE'
                       and r.get('chapter_id') == a.get('chapter_id') and r['kc_id'] in linked and linked[r['kc_id']] <= answered}
        except (ValueError, KeyError, TypeError):
            non_obj = set()
    excl = sorted(set(a.get('blocked_kc_ids') or []) - non_obj)
    unanswered = [i['item_id'] for i in ctx.get('exam_items') or [] if i['item_id'] not in answered]
    # B13: content coverage (taught in the book AND practised by an item) is judged separately from official exam
    # evidence (a course question exists for the competency). Missing exam evidence is reported, never invented.
    produced = list(a.get('kc_ids') or [])
    taught = {k for b in a.get('blocks') or [] for k in b.get('kc_ids') or []}
    practised = {k for i in a.get('assessments') or [] for k in i.get('kc_ids') or []}
    content_gaps = [k for k in produced if k not in taught or k not in practised]
    d['coverage'] = {'status': 'PASS' if not (content_gaps or excl or unanswered) else 'FAIL',
                     'detail': f'{len(produced) - len(content_gaps)}/{len(produced)} produced competencies taught in the book and practised by an item; '
                               f'{len(excl)} excluded or blocked (not produced); {len(non_obj & set(a.get("blocked_kc_ids") or []))} title-slide headings without a learning objective (not a gap); {len(unanswered)} official questions without an answer or an explicit SOURCE_MISSING',
                     'content_gaps': content_gaps[:40], 'gaps': gaps[:40], 'excluded': excl[:40], 'unanswered_questions': unanswered[:40],
                     'not_learning_objectives': sorted(non_obj & set(a.get('blocked_kc_ids') or [])),
                     # B7: produced from slide text only; the figure on the slide was not evaluated
                     'text_only_scope': {c['kc_id']: c['auto_scope']['basis'] for c in ctx.get('competencies') or [] if c.get('auto_scope')},
                     # B7: figure/scan content that was NOT processed; never reported as covered
                     'visual_review_required': sorted(c['kc_id'] for c in ctx.get('competencies') or []
                                                      if set(c.get('blocked') or []) & {'ESSENTIAL_VISUAL_UNRESOLVED', 'SCANNED_PAGE_NO_OCR'} and c['kc_id'] not in non_obj),
                     'produced': len(produced)}
    d['exam_evidence'] = {'status': 'INFO',
                          'detail': f'{len(cov) - len(gaps)}/{len(cov)} competencies with an official course question as evidence; the rest are taught '
                                    'from the slides without a known exam question (not a defect, nothing invented)', 'without_exam_question': gaps[:40]}
    unsupported = [r for r in a.get('reviews') or [] if r.get('verdict') == 'UNSUPPORTED']
    # A claim judged 'unsupported by the cited slides' is resolved (not approved) when a published edition replaces exactly
    # that block with a supplement citing only verified subject sources: a correct, properly sourced supplement must not be
    # rejected just because it is not on the slides. It stays visible in the detail and is never counted as a human review.
    sourced = _edition_supplemented_blocks(ch)
    resolved = [r for r in unsupported if r.get('assertion_id') in sourced]
    unsupported = [r for r in unsupported if r.get('assertion_id') not in sourced]
    human = [r for r in a.get('reviews') or [] if r.get('reviewer_kind') == 'HUMAN']
    d['subject_correctness'] = {'status': 'FAIL' if unsupported else 'PASS' if human and not unsupported else 'NOT_TESTED',
                                'resolved_by_verified_supplement': {r['assertion_id']: sourced[r['assertion_id']] for r in resolved},
                                'detail': f"{len(unsupported)} claims marked unsupported by the model review; {len(human)} human reviews. "
                                          + (f"{len(resolved)} slide-unsupported claims re-based as supplements on verified subject sources "
                                             f"({', '.join(sorted({s for r in resolved for s in sourced[r['assertion_id']]}))}); not human-reviewed. " if resolved else '')
                                          + 'A model review is not proof of correctness.'
                                          + (f" {len((pub or {}).get('errata') or [])} documented editorial corrections applied (errata; not human-reviewed)."
                                             if (pub or {}).get('errata') else '')}
    steps = _gate(q, 'G4.STEP_ARITHMETIC') + _gate(q, 'G4.NUMERIC') + _gate(q, 'G4.ANSWER_CONSISTENCY')
    setup = _gate(q, 'G4.DERIVATION_SETUP') + _gate(q, 'G4.PROOF_VALIDITY')
    arith = _worst([g['status'] for g in steps])
    d['math_numeric'] = {'status': 'FAIL' if arith == 'FAIL' else 'NOT_TESTED' if arith != 'PASS' or any(g['status'] != 'PASS' for g in setup) else 'PASS',
                         'detail': f"arithmetic {arith}; set-up/proof {_worst([g['status'] for g in setup]) if setup else 'NOT_APPLICABLE'} "
                                   '(the choice of approach is not machine-verified)'}
    d['didactic_completeness'] = {'status': _worst([g['status'] for g in _gate(q, 'G1.ITEM_OPERATION') + _gate(q, 'G1.ITEM_TRANSFER') + _gate(q, 'G5.NOTATION')]),
                                  'detail': 'operation coverage by items, transfer items, notation (G1.ITEM_OPERATION, G1.ITEM_TRANSFER, G5.NOTATION)'}
    d['items_and_solutions'] = {'status': _worst([g['status'] for g in _gate(q, 'G1.')]),
                                'detail': f"{len(a.get('assessments') or [])} items, {len(a.get('solutions') or [])} solutions; G1 gates"}
    figs = _gate(q, 'G5.FIGURES'); math = (pub or {}).get('math_rendering', {}).get('status', 'NOT_TESTED')
    diag_q = [i['item_id'] for i in ctx.get('exam_items') or [] if re.search(r'\bdiagram', i.get('wording', ''), re.I)]
    covered_q = {x for f in a.get('figures') or [] for x in f.get('answers_item_ids') or []}
    missing_fig = [x for x in diag_q if x not in covered_q]
    st = _worst([g['status'] for g in figs] + [math if math != 'NOT_APPLICABLE' else 'PASS'])
    d['formulas_and_figures'] = {'status': 'FAIL' if missing_fig else st,
                                 'detail': f'formula rendering {math}; figure gate {_worst([g["status"] for g in figs]) if figs else "NOT_APPLICABLE"}; '
                                           f'diagram questions without figure: {missing_fig}'}
    dr = (pub or {}).get('didactic_rules') or {}
    d['didactic_rules'] = {'status': 'NOT_TESTED' if not dr else 'FAIL' if dr['counts'].get('FAIL') else 'PASS',
                           'detail': f"rule set {dr.get('version')}: {dr.get('counts')}; failures: {[f['rule'] + ' ' + f['object'] for f in dr.get('fail', [])][:8]}"
                                     if dr else 'not checked'}
    sc = (pub or {}).get('semantic_checks') or {}
    d['semantic_consistency'] = {'status': 'NOT_TESTED' if not sc else 'FAIL' if sc['counts'].get('FAIL') else 'REVIEW_REQUIRED' if sc['counts'].get('REVIEW') else 'PASS',
                                 'detail': f"rule set {sc.get('version')}: {sc.get('counts')}; failures: {[f['rule'] + ' ' + str(f['object']) for f in sc.get('fail', [])][:8]}; "
                                           f"review: {[f['rule'] + ' ' + str(f['object']) for f in sc.get('review', [])][:8]}" if sc else 'not checked'}
    nc = (pub or {}).get('numeric_checks') or {}
    # B33: the dossier judges the PUBLISHED learner products (book model after errata + edition), not the raw AST, so it
    # can never contradict the publish report (V1 showed 30 items / arithmetic NOT_TESTED while 34 items were typeset).
    d['competency_evidence'] = {'status': 'NOT_TESTED', 'detail': 'no published book model (chapter not published)'}
    bk_p = ch / 'publish' / 'book.json'
    if bk_p.exists():
        bk = json.loads(bk_p.read_text())
        items = [i for st_ in bk.get('stages') or [] for i in st_['items']]
        with_sol = [i for i in items if (i.get('solution') or {}).get('answer')]
        d['items_and_solutions'] = {'status': 'FAIL' if not items or len(with_sol) != len(items) else d['items_and_solutions']['status'],
                                    'detail': f"published workbook: {len(items)} items, {len(with_sol)} with a worked solution and answer; "
                                              f"mock exam {len((bk.get('exam') or {}).get('items') or [])} items / {(bk.get('exam') or {}).get('total_points')} points; "
                                              f"AST gates G1: {d['items_and_solutions']['status']}"}
        cnt = nc.get('counts') or {}
        oracle = json.loads((ch / 'mdp_oracle_report.json').read_text()) if (ch / 'mdp_oracle_report.json').exists() else None
        d['math_numeric'] = {'status': 'FAIL' if cnt.get('FAIL') else d['math_numeric']['status'],
                             'arithmetic_published_text': f"{cnt.get('PASS', 0)} PASS / {cnt.get('FAIL', 0)} FAIL recomputed equations and table totals",
                             'edition_reference_checks': (pub or {}).get('edition', {}).get('numeric_checks') if isinstance((pub or {}).get('edition'), dict) else None,
                             'oracle': (oracle or {}).get('summary') or ((oracle or {}).get('counts') if oracle else 'NOT_RUN'),
                             'detail': f"arithmetic of the published text: {cnt.get('PASS', 0)} PASS, {cnt.get('FAIL', 0)} FAIL (scope: written computations 'a op b = c' and table totals only); "
                                       f"set-up/proof: NOT machine-verifiable -> status stays {d['math_numeric']['status']} unless a human reviews derivations"}
        # B33: competency evidence in separate fields instead of one '44/44' success line
        kcs = list(a.get('kc_ids') or [])
        taught_b = {k for s_ in bk['sections'] for b_ in s_['blocks'] for k in b_.get('kc_ids') or []}
        prac_b = {k for i in items for k in (i.get('kc_keys') or i.get('kc_ids') or [])}
        official = {r['kc_id'] for r in cov if r.get('status') == 'EVIDENCED_PENDING_SEMANTIC_REVIEW'}
        op_fail = {f.get('object') for f in ((pub or {}).get('didactic_rules') or {}).get('fail', []) if f.get('rule') == 'A1'}
        d['competency_evidence'] = {'status': 'INFO', 'produced': len(kcs),
                                    'taught': sum(k in taught_b for k in kcs), 'practised': sum(k in prac_b for k in kcs),
                                    'operation_met': 'NOT_TESTED' if not (pub or {}).get('didactic_rules') else sum(k not in op_fail for k in kcs),
                                    'official_exam_evidence': sum(k in official for k in kcs),
                                    'source_verified_by_human': 0, 'human_review': len(human),
                                    'detail': 'taught/practised from the published book; operation_met = didactic rule A1 (machine heuristic); '
                                              'official_exam_evidence = an official course question exists; nothing here is a human verification'}
    if nc.get('counts', {}).get('FAIL'):
        d['math_numeric'] = {'status': 'FAIL', 'detail': f"recomputed equations or table totals wrong: {[f['object'] for f in nc['fail']][:6]}"}
    anki = (pub or {}).get('products', {}).get('anki') or {}
    d['anki'] = {'status': 'PASS' if anki.get('reimport') and anki.get('cards') else 'NOT_TESTED' if not pub else 'FAIL',
                 'detail': anki.get('package') or 'no Anki package'}
    if pub:
        rs, rd = _render_check(ch / 'publish' / 'artifacts')
    else:
        rs, rd = 'NOT_TESTED', 'chapter not published'
    d['rendering'] = {'status': rs, 'detail': rd}
    d.update(_verification_dims(ch, a))
    tech = all(d[k]['status'] == 'PASS' for k in TECHNICAL)
    return {'schema': 'em-quality-dossier-v1', 'chapter_id': a.get('chapter_id'), 'dimensions': d,
            'technical_release': 'TECHNICAL_RELEASE_CANDIDATE' if tech and pub else 'NOT_RELEASED',
            'academic_release': 'ACADEMIC_RELEASE_NOT_GRANTED',
            'academic_reason': 'subject correctness is not independently verified (model review is not proof)'
                               if d['subject_correctness']['status'] != 'PASS' else 'automatic grant is disabled; a human decides',
            'published': bool(pub)}


def course_dossier(out, status):
    out = Path(out)
    chapters = {}
    for ch in sorted((out / 'chapters').iterdir()) if (out / 'chapters').exists() else []:
        if (ch / 'content_ast.json').exists():
            chapters[ch.name] = chapter_dossier(ch)
            write_json(ch / 'quality_dossier.json', chapters[ch.name])
    not_produced = {k: v.get('status') for k, v in (status.get('chapters') or {}).items() if k not in chapters}
    dims = {k: _worst([c['dimensions'][k]['status'] for c in chapters.values()]) if chapters else 'NOT_TESTED' for k in DIMENSIONS}
    tech = bool(chapters) and all(c['technical_release'] == 'TECHNICAL_RELEASE_CANDIDATE' for c in chapters.values()) and not not_produced
    return {'schema': 'em-course-quality-dossier-v1', 'created': time.time(), 'dimensions': dims, 'chapters': chapters,
            'chapters_not_produced': not_produced,
            'release': {'technical': 'TECHNICAL_RELEASE_CANDIDATE' if tech else 'NOT_RELEASED',
                        'academic': 'ACADEMIC_RELEASE_NOT_GRANTED'},
            'budget': status.get('budget'), 'note': 'Unit tests are not part of this verdict; each dimension is judged on the produced material.'}
