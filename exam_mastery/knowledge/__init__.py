"""Scientific Knowledge & Pedagogy Base (KB).

Versioned JSON files in this package:
  sources.json     verified bibliography (DOI/ISBN, study design, what was actually read)
  principles.json  learning principles: claims -> sources, evidence status, conditions, limits, engine rules
  specs.json       reusable didactic specifications (worked-example fading, tutor hints, item and exam schemas, ...)
  verification.json  output of scripts/verify_sources.py (Crossref/OpenAlex/OpenLibrary, cached)

Agents receive only the compact slice they need (context_for), so course production does not re-derive
didactics. fingerprint() changes whenever a rule changes; artefacts built with an older fingerprint can be
selected for targeted re-checks instead of regenerating everything.
"""
import hashlib, importlib, json, re
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).parent
STATUSES = {'EMPIRICAL_STRONG', 'EMPIRICAL_CONDITIONAL', 'THEORETICAL_MODEL', 'DESIGN_HYPOTHESIS', 'UNVALIDATED_FEATURE', 'REJECTED'}
BASES = {'abstract_checked', 'metadata_only', 'fulltext_checked'}
SEMVER = re.compile(r'^\d+\.\d+\.\d+$')


@lru_cache(maxsize=None)
def load():
    read = lambda n: json.loads((HERE / n).read_text(encoding='utf-8'))
    kb = {'sources': read('sources.json'), 'principles': read('principles.json'), 'specs': read('specs.json')}
    v = HERE / 'verification.json'
    kb['verification'] = json.loads(v.read_text(encoding='utf-8')) if v.exists() else None
    return kb


def fingerprint():
    """Content hash of the rule files (not of verification or cache)."""
    h = hashlib.sha256()
    for n in ('sources.json', 'principles.json', 'specs.json'):
        h.update((HERE / n).read_bytes())
    return 'kb-' + h.hexdigest()[:16]


def validate(kb=None, require_verification=True):
    """Integrity problems as a list of strings; empty list = valid."""
    kb = kb or load()
    errs = []
    src = {s['id']: s for s in kb['sources']['sources']}
    if len(src) != len(kb['sources']['sources']):
        errs.append('duplicate source id')
    for s in src.values():
        if not (s.get('doi') or s.get('isbn')):
            errs.append(f"{s['id']}: neither DOI nor ISBN")
    pids, cids = set(), set()
    for p in kb['principles']['principles']:
        pid = p['id']
        if pid in pids:
            errs.append(f'duplicate principle {pid}')
        pids.add(pid)
        if p['status'] not in STATUSES:
            errs.append(f'{pid}: unknown status {p["status"]}')
        if not SEMVER.match(p.get('version', '')):
            errs.append(f'{pid}: version not semver')
        if not p['claims']:
            errs.append(f'{pid}: no claims')
        for c in p['claims']:
            if c['id'] in cids:
                errs.append(f"duplicate claim {c['id']}")
            cids.add(c['id'])
            if c['basis'] not in BASES:
                errs.append(f"{c['id']}: unknown basis")
            for sid in c['sources']:
                if sid not in src:
                    errs.append(f"{c['id']}: unknown source {sid}")
            if c['basis'] == 'fulltext_checked':
                fe = c.get('fulltext_evidence') or []
                if not fe or any(not e.get('location') or e.get('source') not in c['sources'] for e in fe):
                    errs.append(f"{c['id']}: fulltext_checked without located fulltext_evidence from a cited source")
                if any(src.get(e.get('source'), {}).get('access') != 'fulltext' for e in fe):
                    errs.append(f"{c['id']}: fulltext evidence from a source not marked access=fulltext")
            ev = c.get('abstract_evidence', [])
            if c['basis'] == 'abstract_checked' and not ev:
                errs.append(f"{c['id']}: abstract_checked without abstract_evidence")
            for e in ev:
                if e['source'] not in c['sources']:
                    errs.append(f"{c['id']}: evidence from uncited source {e['source']}")
                if src.get(e['source'], {}).get('access') == 'metadata':
                    errs.append(f"{c['id']}: abstract evidence from metadata-only source {e['source']}")
            if p['status'] in ('EMPIRICAL_STRONG',) and src and all(src[s]['kind'] in ('popular_science',) for s in c['sources'] if s in src):
                errs.append(f"{c['id']}: strong status resting on popular science only")
        for r in p['engine_rules']:
            m = re.match(r'deterministic:([a-z_]+)\.([a-z_]+)$', r['enforcement'])
            if m and not _resolves(*m.groups()):
                errs.append(f"{r['id']}: enforcement {r['enforcement']} does not resolve")
    for sp in kb['specs']['specs']:
        for d in sp.get('derived_from', []):
            if d not in pids:
                errs.append(f"spec {sp['id']}: unknown principle {d}")
        if sp['status'] not in STATUSES:
            errs.append(f"spec {sp['id']}: unknown status")
    if require_verification:
        v = kb['verification']
        if not v:
            errs.append('verification.json missing: run scripts/verify_sources.py')
        else:
            if v.get('problems'):
                errs.extend('verification: ' + x for x in v['problems'])
            missing = set(src) - set(v['sources'])
            if missing:
                errs.append(f'unverified sources: {sorted(missing)}')
    return errs


def _resolves(module, func):
    for name in (f'exam_mastery.{module}', f'exam_mastery.knowledge'):
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        if module == 'knowledge' or name.endswith(module):
            if hasattr(mod, func):
                return True
    return False


def principle(pid):
    return next(p for p in load()['principles']['principles'] if p['id'] == pid)


def spec(sid):
    return next(s for s in load()['specs']['specs'] if s['id'] == sid)


def cite(sid):
    return next(s for s in load()['sources']['sources'] if s['id'] == sid)['cite']


def context_for(artifact, subject=None, max_chars=6000):
    """Compact rule slice for one artefact type (textbook, workbook, mock_exam, anki, lab, tutor, learn_app,
    adaptive_track, solutions). Contains rules, evidence status, conditions/limits and subject adaptations,
    plus the KB fingerprint so the producing run can record which rule version it used."""
    kb = load()
    lines = [f'# Didaktische Regeln ({kb["principles"]["version"]}, {fingerprint()}) für: {artifact}']
    for p in kb['principles']['principles']:
        rules = [r for r in p['engine_rules'] if artifact in r['applies_to']]
        if not rules:
            continue
        lines.append(f'\n## {p["title"]} [{p["status"]}]')
        lines += [f'- {r["id"]}: {r["rule"]}' for r in rules]
        if p['conditions']:
            lines.append('  Bedingungen: ' + ' '.join(p['conditions']))
        if p['limits']:
            lines.append('  Grenzen: ' + ' '.join(p['limits']))
        if subject and subject in p.get('subject_adaptations', {}):
            lines.append(f'  Fach ({subject}): ' + p['subject_adaptations'][subject])
    spec_map = {'textbook': ['worked_example_fading', 'visualization'], 'workbook': ['worked_example_fading', 'assessment_item'],
                'mock_exam': ['assessment_item', 'exam_blueprint'], 'anki': ['anki_card'], 'lab': ['visualization'],
                'tutor': ['tutor_hints', 'error_taxonomy'], 'learn_app': ['error_taxonomy'], 'adaptive_track': ['worked_example_fading', 'error_taxonomy'],
                'solutions': ['assessment_item']}
    for sid in spec_map.get(artifact, []):
        lines.append(f'\nSpezifikation: {sid} {spec(sid)["version"]} → exam_mastery/knowledge/specs.json')
    out = '\n'.join(lines)
    return out if len(out) <= max_chars else out[:max_chars - 20] + '\n[... gekürzt]'


def check_item(item):
    """Deterministic checks of one assessment item against spec assessment_item. Returns list of problems."""
    import jsonschema
    sp = spec('assessment_item')
    errs = [f'schema: {e.message}' for e in jsonschema.Draft202012Validator(sp['json_schema']).iter_errors(item)]
    if errs:
        return errs
    total = sum(r['points'] for r in item['rubric'])
    if 'points' in item and abs(total - item['points']) > 1e-9:
        errs.append(f"rubric sums to {total}, item has {item['points']} points")
    if item['purpose'] == 'transfer' and item['transfer_dimension'] == 'none':
        errs.append('transfer item without transfer_dimension')
    return errs


def _skeleton(text):
    return re.sub(r'\d+(?:[.,]\d+)?', '#', text or '')


def check_item_set(items):
    """Items of one competency that differ only in numbers (non-retrieval) are flagged."""
    errs, seen = [], {}
    for it in items:
        if it.get('purpose') == 'retrieval':
            continue
        key = (it.get('competency'), _skeleton(it.get('prompt')))
        if key in seen:
            errs.append(f"{it['id']} differs from {seen[key]} only in numbers")
        seen.setdefault(key, it['id'])
    return errs


def check_exam_against_blueprint(exam, blueprint, tolerance=0.10):
    """exam = {'minutes', 'items': [assessment_item...]}. Returns list of problems."""
    import jsonschema
    errs = [f'blueprint schema: {e.message}' for e in jsonschema.Draft202012Validator(spec('exam_blueprint')['json_schema']).iter_errors(blueprint)]
    for it in exam['items']:
        errs += [f"{it.get('id')}: {e}" for e in check_item(it)]
    errs += check_item_set(exam['items'])
    if errs:
        return errs
    pts = lambda it: it.get('points', sum(r['points'] for r in it['rubric']))
    total = sum(pts(it) for it in exam['items'])
    if abs(total - blueprint['total_points']) > 1e-9:
        errs.append(f"exam has {total} points, blueprint {blueprint['total_points']}")
    want = {}
    for r in blueprint['rows']:
        want[r['competency']] = want.get(r['competency'], 0) + r['points']
    got = {}
    for it in exam['items']:
        got[it['competency']] = got.get(it['competency'], 0) + pts(it)
    for c in sorted(set(want) | set(got)):
        w, g = want.get(c, 0), got.get(c, 0)
        if w == 0 or abs(g - w) > tolerance * w:
            errs.append(f'competency {c}: exam {g} points vs blueprint {w}')
    minutes = sum(it['minutes'] for it in exam['items'])
    if minutes > exam.get('minutes', blueprint['minutes']):
        errs.append(f"expected work time {minutes} min exceeds exam time {exam.get('minutes', blueprint['minutes'])} min")
    return errs


def evidence_summary():
    """Counts for reports: principles by status, claims by basis, verification totals."""
    kb = load()
    from collections import Counter
    ps = kb['principles']['principles']
    return {'kb_version': kb['principles']['version'], 'fingerprint': fingerprint(),
            'principles_by_status': dict(Counter(p['status'] for p in ps)),
            'claims_by_basis': dict(Counter(c['basis'] for p in ps for c in p['claims'])),
            'sources_by_kind': dict(Counter(s['kind'] for s in kb['sources']['sources'])),
            'sources_by_access': dict(Counter(s['access'] for s in kb['sources']['sources'])),
            'verification': (kb['verification'] or {}).get('summary')}
