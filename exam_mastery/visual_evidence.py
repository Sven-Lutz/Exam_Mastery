"""Figure content read by the calling agent (B8): no second model provider, no OCR-only shortcut.

The engine cannot see images. The agent host that runs the skill (e.g. Claude Code) can. The loop is:

1. `exam-mastery visuals [folder]` writes a worklist: every slide whose competency is blocked by a figure, with its
   rendered page image, the page's text layer and the render hash.
2. The agent looks at each image and writes `em-visual-evidence-v1`: per page a classification (CONTENT, DECORATIVE,
   UNREADABLE), the visual type and atomic statements with a confidence. Numbers must be listed explicitly, and every
   computation the figure states is written down as an arithmetic check.
3. `exam-mastery visuals --import file.json` validates deterministically and stores accepted evidence in the course
   output folder (never in the lecture folder):
   - the render hash must match the current page (a changed slide invalidates its evidence);
   - every number in a statement must be declared, and is marked confirmed when the page's text layer contains it;
   - every arithmetic check is recomputed, and a wrong one rejects the statements that use its result;
   - LOW-confidence statements are kept in the report and never taught;
   - DECORATIVE pages contribute nothing; UNREADABLE pages stay VISUAL_REVIEW_REQUIRED.
4. Planning (dry run, product run, update) adds one `visual_transcription` element per accepted page to the
   inventory. It carries the same page anchor, a visible label and `not_human_verified`. The element is attached to
   the competencies and chapters of that page. The auto scope then makes the competency producible
   (AUTO_VISION_TRANSCRIBED). The source-number gate accepts only numbers that occur in these texts.
"""
import ast
import hashlib
import json
import operator
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .common import ContractError, write_json

SCHEMA = 'em-visual-evidence-v1'
CLASSES = {'CONTENT', 'DECORATIVE', 'UNREADABLE'}
CONF = {'HIGH', 'MEDIUM', 'LOW'}
TEACHABLE = {'HIGH', 'MEDIUM'}
KIND = 'visual_transcription'
NUM = re.compile(r'(?<![\w.])[-+]?\d+(?:[.,]\d+)*(?:\s?%)?')
VISUAL_CODES = {'ESSENTIAL_VISUAL_UNRESOLVED', 'SCANNED_PAGE_NO_OCR', 'VISUAL_RELEVANCE_UNKNOWN', 'ADJACENT_PAGE_UNREADABLE'}


def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()


def _norm_num(s):
    # agents write numbers as JSON numbers (2009) or strings ("2009", "1,027"); both are valid
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        s = repr(s) if isinstance(s, float) else str(s)
    s = str(s).replace('%', '').replace(' ', '').lstrip('+')
    if re.fullmatch(r'-?\d{1,3}([.,]\d{3})+', s):          # thousands separators
        s = re.sub(r'[.,]', '', s)
    return s.replace(',', '.')


def _page_key(e):
    loc = e.get('locator') or {}
    p = loc.get('page', loc.get('slide'))
    return (e['source_id'], p) if p is not None else None


def page_index(manifest):
    """{(relative_path, page): {'source_id', 'render', 'text', 'element_ids'}}."""
    src = {s['source_id']: s['relative_path'] for s in manifest.get('sources', [])}
    out = {}
    for e in manifest.get('elements', []):
        k = _page_key(e)
        if not k or k[0] not in src:
            continue
        d = out.setdefault((src[k[0]], k[1]), {'source_id': k[0], 'render': None, 'text': [], 'element_ids': []})
        d['element_ids'].append(e['element_id'])
        if e['kind'] == 'rendered_page' and e.get('asset'):
            d['render'] = e['asset']
        elif e.get('text') and e['kind'] != KIND:
            d['text'].append(e['text'])
    return out


# ------------------------------------------------------------------ worklist

def candidate_figures(manifest, min_area=0.04, min_paths=10):
    """B13 deterministic pre-triage for `visuals --all`: elements that can carry subject content.
    Kept: embedded images covering >= 4 % of the page and vector drawings with >= 10 paths on >= 4 % of the page.
    Dropped: images whose identical bytes appear on 3+ pages (logos, templates) and small or simple drawings.
    The agent still classifies every kept page (CONTENT, DECORATIVE or UNREADABLE); size is no proof of content."""
    from collections import Counter, defaultdict
    els = [e for e in manifest['elements'] if e['kind'] in ('image', 'diagram', 'chart', 'figure') and _page_key(e)]
    size = defaultdict(lambda: [1.0, 1.0])
    for e in manifest['elements']:
        b = (e.get('locator') or {}).get('bbox')
        if b:
            sz = size[e['source_id']]; sz[0] = max(sz[0], b[2]); sz[1] = max(sz[1], b[3])
    reuse = Counter((e.get('asset') or {}).get('sha256') for e in els if e.get('asset'))
    out = []
    for e in els:
        b = (e.get('locator') or {}).get('bbox') or [0, 0, 0, 0]
        w, h = size[e['source_id']]
        area = max(0.0, (b[2] - b[0]) * (b[3] - b[1])) / (w * h)
        if e['kind'] == 'image':
            sha = (e.get('asset') or {}).get('sha256')
            if area >= min_area and not (sha and reuse[sha] >= 3):
                out.append(e)
        elif area >= min_area and ((e.get('structure') or {}).get('vector_paths') or 0) >= min_paths and area < 0.98:
            out.append(e)
    return out


def worklist(plan, manifest, gates, assets_root, include_all=False, done=()):
    """Pages the agent must look at: anchor pages of every competency whose blocking cause is a figure.
    include_all (B13): additionally every page with an image, diagram, chart or figure element that has no stored
    reading yet (`done`), so figures that block nothing are triaged too (CONTENT, DECORATIVE or UNREADABLE)."""
    kcs = {k['kc_id']: k for k in plan['competencies']}
    by = {e['element_id']: e for e in manifest['elements']}
    src = {s['source_id']: s['relative_path'] for s in manifest['sources']}
    pages = page_index(manifest)
    want = {}
    for cid, g in gates.items():
        causes = dict(g.get('blocked_kcs') or {}); causes.update(g.get('review_required_kcs') or {})
        for kid, codes in causes.items():
            if not set(codes) & (VISUAL_CODES | {'CRITICAL_FORMULA_UNRELIABLE'}):
                continue
            for a in kcs[kid]['source_anchor_ids']:
                k = _page_key(by[a]) if a in by else None
                if k:
                    want.setdefault((src[k[0]], k[1]), set()).add(kid)
            if 'CRITICAL_FORMULA_UNRELIABLE' in codes:   # pages of the blocking (linearised) formulas
                for f in g.get('findings') or []:
                    if f.get('code') == 'CRITICAL_FORMULA_UNRELIABLE' and f.get('kc_ids') == [kid]:
                        for eid in f.get('element_ids') or []:
                            k = _page_key(by[eid]) if eid in by else None
                            if k:
                                want.setdefault((src[k[0]], k[1]), set()).add(kid)
    if include_all:
        anchored = {}
        for k in kcs.values():
            for a in k['source_anchor_ids']:
                pk = _page_key(by[a]) if a in by else None
                if pk:
                    anchored.setdefault((src[pk[0]], pk[1]), set()).add(k['kc_id'])
        for e in candidate_figures(manifest):
            key = (src[e['source_id']], _page_key(e)[1])
            if key not in done:
                want.setdefault(key, set()).update(anchored.get(key, set()))
    out = []
    for (path, page), kids in sorted(want.items()):
        p = pages.get((path, page)) or {}
        r = p.get('render') or {}
        out.append({'source': path, 'page': page, 'kc_ids': sorted(kids),
                    'competencies': [kcs[k]['statement'] for k in sorted(kids)],
                    'image': str(Path(assets_root) / r['path']) if r.get('path') else None,
                    'render_sha256': r.get('sha256'), 'text_layer': '\n'.join(p.get('text') or [])[:4000]})
    return out


# ------------------------------------------------------------------ validation

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def _eval(expr):
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        raise ValueError('only + - * / and numbers')
    return ev(ast.parse(expr.replace(',', '.'), mode='eval'))


def validate(evidence, manifest):
    """(accepted_pages, report). Never raises on content; raises ContractError on a malformed file."""
    if not isinstance(evidence, dict) or evidence.get('schema') != SCHEMA:
        raise ContractError(f'visual evidence must use schema {SCHEMA}')
    reader = evidence.get('reader') or {}
    if reader.get('human_verified'):
        raise ContractError('agent evidence cannot claim human verification')
    pages = page_index(manifest)
    accepted, report = [], []
    for p in evidence.get('pages') or []:
        key = (p.get('source'), p.get('page'))
        row = {'source': key[0], 'page': key[1], 'classification': p.get('classification'), 'accepted': [], 'rejected': []}
        report.append(row)
        info = pages.get(key)
        if info is None:
            row['result'] = 'REJECTED_UNKNOWN_PAGE'; continue
        if p.get('classification') not in CLASSES:
            row['result'] = 'REJECTED_BAD_CLASSIFICATION'; continue
        if (info.get('render') or {}).get('sha256') != p.get('render_sha256'):
            row['result'] = 'REJECTED_STALE_RENDER'; continue      # the slide changed since it was read
        layer = {_norm_num(x) for t in info['text'] for x in NUM.findall(t)}
        bad_results = set()
        row['arithmetic'] = []
        for chk in p.get('arithmetic') or []:
            try:
                val = _eval(chk['expression']); stated = float(_norm_num(str(chk['stated'])))
                ok = abs(val - stated) <= max(abs(stated) * 0.005, 0.051)
            except (ValueError, SyntaxError, KeyError, ZeroDivisionError, TypeError):
                ok, val = False, None
            row['arithmetic'].append({**chk, 'computed': val, 'result': 'PASS' if ok else 'FAIL'})
            if not ok:
                bad_results.add(_norm_num(str(chk.get('stated'))))
        stmts = []
        for i, s in enumerate(p.get('statements') or []):
            text, conf = str(s.get('text') or '').strip(), s.get('confidence')
            declared = {_norm_num(x) for x in s.get('numbers') or []}
            found = {_norm_num(x) for x in NUM.findall(text)}
            why = (None if text and conf in CONF else 'missing text or confidence') or \
                  (f'numbers not declared: {sorted(found - declared)}' if found - declared else None) or \
                  (f'uses a failed arithmetic result {sorted(found & bad_results)}' if found & bad_results else None) or \
                  ('LOW confidence: reported, never taught' if conf == 'LOW' else None)
            item = {'n': i + 1, 'text': text, 'confidence': conf,
                    'numbers': [{'value': x, 'text_layer_confirmed': x in layer} for x in sorted(found)]}
            if why:
                row['rejected'].append({**item, 'reason': why})
            else:
                row['accepted'].append(item); stmts.append(item)
        if p['classification'] == 'CONTENT' and stmts:
            row['result'] = 'ACCEPTED'
            accepted.append({'source': key[0], 'page': key[1], 'source_id': info['source_id'], 'visual_type': p.get('visual_type'),
                             'render_sha256': p['render_sha256'], 'statements': stmts, 'reader': reader,
                             'open': p.get('not_readable') or []})
        elif p['classification'] == 'DECORATIVE':
            row['result'] = 'DECORATIVE'
            accepted.append({'source': key[0], 'page': key[1], 'source_id': info['source_id'], 'decorative': True,
                             'render_sha256': p['render_sha256'], 'reader': reader, 'statements': []})
        else:
            row['result'] = 'STAYS_VISUAL_REVIEW'
    return accepted, report


# ------------------------------------------------------------------ store

def store_path(root):
    from .incremental import course_dir
    return course_dir(root) / 'visual_evidence.json'


def load(root):
    p = store_path(root)
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except ValueError:
        return None


def import_evidence(root, evidence, manifest):
    """Validate and merge (newer page entries replace older ones). Returns the validation report."""
    accepted, report = validate(evidence, manifest)
    old = load(root) or {'schema': SCHEMA + '-store', 'pages': []}
    keep = {(p['source'], p['page']): p for p in old['pages']}
    for p in accepted:
        keep[(p['source'], p['page'])] = {**p, 'imported': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    store = {'schema': SCHEMA + '-store', 'pages': [keep[k] for k in sorted(keep, key=lambda x: (x[0], x[1]))]}
    p = store_path(root); p.parent.mkdir(parents=True, exist_ok=True)
    write_json(p, store)
    write_json(p.with_name('visual_evidence_report.json'), report)
    return report


# ------------------------------------------------------------------ integration into planning

def element_text(p):
    lines = [f"[Bildauswertung durch den Agenten ({p.get('visual_type') or 'Abbildung'}), Folie {p['page']}; "
             f"nicht menschlich geprüft. [nur im Bild] = Zahl steht nicht in der Textschicht der Folie.]"]
    for s in p['statements']:
        only = ' [nur im Bild]' if any(not n['text_layer_confirmed'] for n in s['numbers']) else ''
        lines.append(f"- {s['text']}{only} (Konfidenz {s['confidence']})")
    return '\n'.join(lines)


def integrate(plan, manifest, store):
    """Add accepted page evidence as elements and attach them to the page's competencies and chapters.
    Pages whose render hash no longer matches are ignored (stale). Returns (plan, manifest, summary); input unchanged."""
    if not store or not store.get('pages'):
        return plan, manifest, {'pages': 0}
    plan, manifest = json.loads(json.dumps(plan)), json.loads(json.dumps(manifest))
    pages = page_index(manifest)
    by = {e['element_id']: e for e in manifest['elements']}
    summary = {'pages': 0, 'decorative': 0, 'stale': [], 'element_ids': {}}
    for p in store['pages']:
        info = pages.get((p['source'], p['page']))
        if info is None or (info.get('render') or {}).get('sha256') != p['render_sha256']:
            summary['stale'].append(f"{p['source']}:{p['page']}"); continue
        if p.get('decorative'):
            summary['decorative'] += 1
            summary['element_ids'][(p['source'], p['page'])] = None
            continue
        text = element_text(p)
        loc = f"{p['source']}/page-{p['page']}#{KIND}-1"
        eid = 'el-' + _h(loc)[:16]
        manifest['elements'].append({'element_id': eid, 'source_id': info['source_id'], 'locator': {'page': p['page']},
                                     'locator_str': loc, 'kind': KIND, 'text': text, 'normalized_text': text.lower(),
                                     'structure': {'statements': p['statements'], 'visual_type': p.get('visual_type'), 'open': p.get('open')},
                                     'asset': None, 'raw_span_hash': p['render_sha256'], 'extraction_hash': _h(KIND + '|' + text),
                                     'status': 'ok', 'confidence': 'agent_vision', 'parse_method': 'agent_vision:' + str((p.get('reader') or {}).get('model')),
                                     'flags': ['AGENT_VISION_TRANSCRIPTION', 'not_human_verified']})
        by[eid] = manifest['elements'][-1]
        summary['pages'] += 1; summary['element_ids'][(p['source'], p['page'])] = eid
        page_els = set(info['element_ids'])
        for k in plan['competencies']:
            if page_els & set(k['source_anchor_ids']) and eid not in k['source_anchor_ids']:
                k['source_anchor_ids'].append(eid)
        for c in plan['chapters']:
            pkg = c['source_package']
            if page_els & set(pkg['element_ids']) and eid not in pkg['element_ids']:
                pkg['element_ids'].append(eid)
    for s in manifest['sources']:
        s['element_ids'] = list(s.get('element_ids') or []) + [e for (src, pg), e in summary['element_ids'].items()
                                                               if e and src == s['relative_path']]
    manifest['element_count'] = len(manifest['elements'])
    manifest['agent_vision'] = {'content': sorted(f"{pages[k]['source_id']}:{k[1]}" for k, v in summary['element_ids'].items() if v),
                                'decorative': sorted(f"{pages[k]['source_id']}:{k[1]}" for k, v in summary['element_ids'].items() if v is None)}
    summary['element_ids'] = {f'{a}:{b}': v for (a, b), v in summary['element_ids'].items()}
    return plan, manifest, summary



# ------------------------------------------------------------------ commands

def plan_now(root, out, with_evidence=True):
    from .chapters import dry_run
    _, plan, m, gates, _ = dry_run(root, out, visual_evidence='auto' if with_evidence else None)
    return plan, m, gates


def cmd_worklist(root, include_all=False):
    """Write the pages still to be read (figure-blocked competencies after the stored evidence)."""
    from .incremental import course_dir
    out = course_dir(root) / ('visuals-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
    plan, m, gates = plan_now(root, out)
    # still open = figure-blocked competencies that the auto scope (incl. stored agent evidence) did not resolve
    from .auto_scope import classify, VISUAL_REVIEW
    left = {}
    for cid, g in gates.items():
        open_ = {k for k, v in classify(plan, m, g).items() if v['category'] == VISUAL_REVIEW}
        left[cid] = {**g, 'blocked_kcs': {k: v for k, v in g['blocked_kcs'].items() if k in open_},
                     'review_required_kcs': {k: v for k, v in (g.get('review_required_kcs') or {}).items() if k in open_}}
    done = {(p['source'], p['page']) for p in (load(root) or {}).get('pages', [])} if include_all else set()
    wl = worklist(plan, m, left, out, include_all, done)
    doc = {'schema': 'em-visual-worklist-v1', 'course_folder': str(Path(root).resolve()), 'pages': wl,
           'instructions': ('Look at each image yourself. Per page write classification CONTENT|DECORATIVE|UNREADABLE, visual_type, '
                            'statements [{text, confidence HIGH|MEDIUM|LOW, numbers:[every number in text]}], arithmetic '
                            '[{expression, stated}] for every sum/difference/ratio the figure states, not_readable [...]. '
                            'Copy render_sha256. Only what is visible; no outside knowledge. Then: exam-mastery visuals --import <file>'),
           'evidence_template': {'schema': SCHEMA, 'reader': {'agent': '<host>', 'model': '<model id>', 'human_verified': False},
                                 'pages': [{'source': w['source'], 'page': w['page'], 'render_sha256': w['render_sha256'],
                                            'classification': None, 'visual_type': None, 'statements': [], 'arithmetic': [], 'not_readable': []}
                                           for w in wl]}}
    write_json(out / 'visual_worklist.json', doc)
    return out / 'visual_worklist.json', doc


def cmd_import(root, path):
    from .incremental import course_dir
    out = course_dir(root) / ('visuals-import-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
    _, m, _ = plan_now(root, out, with_evidence=False)
    rep = import_evidence(root, json.loads(Path(path).read_text()), m)
    from collections import Counter
    return {'pages': len(rep), 'results': dict(Counter(r.get('result') for r in rep)),
            'statements_accepted': sum(len(r['accepted']) for r in rep), 'statements_rejected': sum(len(r['rejected']) for r in rep),
            'arithmetic_fail': [f"{r['source']}:{r['page']} {a['expression']}={a['stated']} (computed {a['computed']})" for r in rep for a in r.get('arithmetic', []) if a['result'] == 'FAIL'],
            'store': str(store_path(root)), 'report': str(store_path(root).with_name('visual_evidence_report.json'))}
