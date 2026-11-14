"""`exam-mastery status` and `exam-mastery update`: what is produced, what changed in the sources, what must be redone.

Both are offline. `status` only reads. `update` plans the current sources again (the same planning as a dry run, no
provider), compares every chapter with the run that produced its learning materials and writes one report into the
course output folder. Earlier runs and their LERNMATERIAL are never modified: a chapter whose sources changed is
reported as STALE, and only `update --produce` (a paid run, needs the user's go-ahead) regenerates exactly those
chapters, each in a new run directory, through the normal product path.

Chapter comparison: chapter ids come from the chapter title, element ids from file path and page, so an unchanged
chapter keeps its ids. Its content fingerprint covers its competencies and the extraction hash (= normalized text) of
every source element in its package. A chapter is
  CURRENT        same fingerprint as when its materials were produced,
  STALE          same chapter, but a competency or a source element changed,
  SOURCE_REMOVED it was produced, but the current plan no longer contains it,
  NEW            planned now, never produced.
"""
import json
import os
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path

from .checkpoints import digest
from .common import ContractError, sha_file, write_json

SOURCE_SUFFIXES = {'.pdf', '.pptx', '.docx', '.md', '.txt', '.tex', '.csv', '.xlsx', '.png', '.jpg', '.jpeg', '.html'}


# ------------------------------------------------------------------ locating a course

def course_id(root):
    return 'course-' + digest(str(Path(root).expanduser().resolve()))[:12]


def output_bases():
    """Where course folders may live: the configured base first, then the installed default."""
    from .runtime import default_output_base
    seen, out = set(), []
    for b in (default_output_base(), Path.home() / 'Exam_Mastery_Output'):
        if b.resolve() not in seen:
            seen.add(b.resolve()); out.append(b)
    return out


def course_dir(root):
    cid = course_id(root)
    for b in output_bases():
        if (b / cid).is_dir():
            return b / cid
    return output_bases()[0] / cid


def looks_like_course(root):
    """True if a folder holds lecture-like files (searched 3 levels deep). Refuses home and filesystem roots."""
    root = Path(root).expanduser().resolve()
    if root in (Path.home().resolve(), Path('/')) or not root.is_dir():
        return False
    for dirpath, dirs, files in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        dirs[:] = [d for d in dirs if not d.startswith('.')] if depth < 3 else []
        if any(Path(f).suffix.lower() in SOURCE_SUFFIXES and not f.startswith('.') for f in files):
            return True
    return False


def _read(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def runs(course):
    """Production runs (ch-*) newest first, with their status."""
    out = []
    for r in sorted(Path(course).glob('ch-*'), reverse=True):
        st = _read(r / 'status.json') or {}
        out.append({'run': r, 'status': st, 'has_plan': (r / 'plan' / 'curriculum.json').exists()})
    return out


def delivered(run):
    """{chapter_id: LERNMATERIAL folder} of one run (published chapters only)."""
    out = {}
    plan = _read(Path(run) / 'plan' / 'curriculum.json') or {}
    titles = {c['chapter_id']: c for c in plan.get('chapters', [])}
    lm = Path(run) / 'LERNMATERIAL'
    for cid in titles:
        if (Path(run) / 'chapters' / cid / 'publish' / 'artifacts' / 'kapitel.pdf').exists():
            pos, title = titles[cid].get('position'), titles[cid]['title']
            name = (f"{int(pos):02d}_" if isinstance(pos, int) else '') + re.sub(r'[^A-Za-z0-9ÄÖÜäöüß]+', '_', title).strip('_')
            out[cid] = lm / name if (lm / name).is_dir() else Path(run) / 'chapters' / cid / 'publish' / 'artifacts'
    return out


def produced_chapters(course):
    """Newest published version of every chapter: {chapter_id: {run, folder, fingerprint, title}}."""
    out = {}
    for r in reversed(runs(course)):          # oldest first, newer runs overwrite
        if not r['has_plan']:
            continue
        plan = _read(r['run'] / 'plan' / 'curriculum.json'); man = _read(r['run'] / 'plan' / 'source_inventory.json')
        if not plan or not man:
            continue
        fps = chapter_fingerprints(plan, man)
        for cid, folder in delivered(r['run']).items():
            out[cid] = {'run': str(r['run']), 'folder': str(folder), 'fingerprint': fps.get(cid),
                        'title': next((c['title'] for c in plan['chapters'] if c['chapter_id'] == cid), cid)}
    return out


# ------------------------------------------------------------------ fingerprints

def source_hashes(manifest):
    """{relative_path: sha256} of the parsed sources of an inventory (metadata files such as .DS_Store ignored)."""
    return {s['relative_path']: s.get('raw_sha256') for s in manifest.get('sources', []) if s.get('status') != 'ignored_metadata'}


def current_hashes(root):
    from .onepath_legacy import snapshot
    root = Path(root).expanduser().resolve()
    snap = snapshot(root, hasher=sha_file)
    return {k: v for k, v in snap.items() if not Path(k).name.startswith('.')}


def chapter_fingerprints(plan, manifest):
    els = {e['element_id']: e for e in manifest.get('elements', [])}
    kcs = {k['kc_id']: k for k in plan.get('competencies', [])}
    out = {}
    for c in plan.get('chapters', []):
        ids = sorted(set((c.get('source_package') or {}).get('element_ids') or []) |
                     {a for k in c['kc_ids'] for a in kcs.get(k, {}).get('source_anchor_ids', [])})
        out[c['chapter_id']] = digest({'kcs': sorted((k, kcs.get(k, {}).get('statement')) for k in c['kc_ids']),
                                       'elements': [(i, (els.get(i) or {}).get('extraction_hash')) for i in ids]})
    return out


def chapter_sources(plan, manifest):
    """{chapter_id: [relative_path]} of the files each chapter is built from."""
    els = {e['element_id']: e for e in manifest.get('elements', [])}
    src = {s['source_id']: s['relative_path'] for s in manifest.get('sources', [])}
    kcs = {k['kc_id']: k for k in plan.get('competencies', [])}
    out = {}
    for c in plan.get('chapters', []):
        ids = set((c.get('source_package') or {}).get('element_ids') or []) | {a for k in c['kc_ids'] for a in kcs.get(k, {}).get('source_anchor_ids', [])}
        out[c['chapter_id']] = sorted({src.get(els[i]['source_id']) for i in ids if i in els} - {None})
    return out


# ------------------------------------------------------------------ status / update

def status(root):
    """Read-only overview of one course folder. No provider, no writes."""
    root = Path(root).expanduser().resolve()
    course = course_dir(root)
    rs = runs(course) if course.is_dir() else []
    prod = produced_chapters(course) if course.is_dir() else {}
    last_plan = next((r['run'] for r in rs if r['has_plan']), None)
    changes = None
    if last_plan is not None:
        man = _read(last_plan / 'plan' / 'source_inventory.json') or {}
        old, now = source_hashes(man), current_hashes(root)
        changes = {'new': sorted(set(now) - set(old)), 'removed': sorted(set(old) - set(now)),
                   'changed': sorted(k for k in set(now) & set(old) if now[k] != old[k])}
    last = rs[0]['status'] if rs else {}
    upd = _read(course / 'update_check.json') if course.is_dir() else None
    from .product import load_config
    try:
        cfg = load_config()
    except ContractError as e:
        cfg = {'provider': 'INVALID', 'model': str(e)}
    return {'status': 'NO_RUNS' if not rs else 'HAS_RUNS', 'course_folder': str(root), 'output_folder': str(course),
            'provider': {'provider': cfg['provider'], 'model': cfg['model']} if cfg else 'NOT_CONFIGURED',
            'runs': len(rs), 'last_run': {'dir': str(rs[0]['run']), 'run_state': last.get('run_state'), 'status': last.get('status')} if rs else None,
            'chapters_with_materials': {cid: {'title': v['title'], 'folder': v['folder']} for cid, v in sorted(prod.items(), key=lambda x: x[1]['folder'])},
            'source_changes_since_last_plan': changes,
            'sources_changed': bool(changes and any(changes.values())),
            'last_update_check': {k: upd.get(k) for k in ('checked', 'summary')} if upd else None,
            'next': ('exam-mastery update' if changes and any(changes.values()) else None)}


def update(root, produce=False, cfg=None, output_base=None, provider=None):
    """Plan the current sources offline, classify every chapter, write update_check.json. With produce=True, run the
    product path for the STALE and NEW chapters only (one new run per chapter; stops at the first budget/quota stop)."""
    from .runtime import run_chapters
    root = Path(root).expanduser().resolve()
    course = course_dir(root) if output_base is None else Path(output_base) / course_id(root)
    prod = produced_chapters(course) if course.is_dir() else {}
    planned_out, report = run_chapters(root, dry_run=True, output_base=output_base or course.parent,
                                       out_dir=str(course / ('update-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])))
    plan = _read(Path(planned_out) / 'curriculum.json') or _read(Path(planned_out) / 'plan' / 'curriculum.json')
    man = _read(Path(planned_out) / 'source_inventory.json') or _read(Path(planned_out) / 'plan' / 'source_inventory.json')
    if plan is None or man is None:
        raise ContractError(f'planning wrote no curriculum/source inventory under {planned_out}')
    fps, srcs = chapter_fingerprints(plan, man), chapter_sources(plan, man)
    titles = {c['chapter_id']: c['title'] for c in plan['chapters']}
    prev_man = None
    if prod:
        newest = max((v['run'] for v in prod.values()))
        prev_man = _read(Path(newest) / 'plan' / 'source_inventory.json')
    old_src, now_src = source_hashes(prev_man or {}), source_hashes(man)
    chapters = {}
    for cid, fp in fps.items():
        p = prod.get(cid)
        state = 'NEW' if p is None else 'CURRENT' if p['fingerprint'] == fp else 'STALE'
        chapters[cid] = {'title': titles[cid], 'state': state, 'sources': srcs[cid],
                         'materials': p['folder'] if p else None,
                         'changed_sources': sorted(s for s in srcs[cid] if old_src.get(s) != now_src.get(s)) if p else []}
    for cid, p in prod.items():
        if cid not in fps:
            chapters[cid] = {'title': p['title'], 'state': 'SOURCE_REMOVED', 'sources': [], 'materials': p['folder'],
                             'changed_sources': [], 'note': 'the current sources no longer yield this chapter; its materials are kept and marked outdated'}
    todo = [c for c, v in chapters.items() if v['state'] in ('STALE', 'NEW')]
    out = {'schema': 'em-update-check-v1', 'checked': datetime.now(timezone.utc).isoformat(timespec='seconds'),
           'course_folder': str(root), 'plan_dir': str(planned_out), 'provider_calls_made': 0,
           'sources': {'new': sorted(set(now_src) - set(old_src)) if prev_man else sorted(now_src),
                       'removed': sorted(set(old_src) - set(now_src)) if prev_man else [],
                       'changed': sorted(k for k in set(now_src) & set(old_src) if now_src[k] != old_src[k])},
           'chapters': chapters,
           'summary': {s: sorted(c for c, v in chapters.items() if v['state'] == s) for s in ('CURRENT', 'STALE', 'NEW', 'SOURCE_REMOVED')},
           'to_produce': todo, 'produced': [], 'originals_unchanged': report.get('originals_unchanged'),
           # B8: a slide whose render changed invalidates its figure reading; it must be read again (exam-mastery visuals)
           'visual_evidence_stale': (_read(Path(planned_out) / 'agent_vision_summary.json') or {}).get('stale', [])}
    course.mkdir(parents=True, exist_ok=True)
    if produce and todo:
        from .budget import BudgetBlocked
        from .product import load_config, run_product
        cfg = cfg or load_config()
        if cfg is None and provider is None:
            out['produce'] = 'NOT_CONFIGURED'
        else:
            for cid in todo:
                try:
                    run, st, dossier = run_product(root, cfg, output_base=output_base or course.parent, provider=provider, only_chapter=cid)
                    out['produced'].append({'chapter_id': cid, 'run': str(run), 'run_state': st.get('run_state'), 'technical': dossier['release']['technical']})
                    if st.get('run_state') in ('BUDGET_BLOCKED', 'QUOTA_BLOCKED'):
                        out['produce'] = st['run_state']; break
                except BudgetBlocked as e:
                    out['produced'].append({'chapter_id': cid, 'run_state': e.state}); out['produce'] = e.state; break
                except Exception as e:  # earlier materials stay untouched; the next `update --produce` retries this chapter
                    out['produced'].append({'chapter_id': cid, 'run_state': 'FAILED', 'error': f'{type(e).__name__}: {e}'}); out['produce'] = 'FAILED'; break
            else:
                out['produce'] = 'DONE'
    write_json(course / 'update_check.json', out)
    return out
