"""B15: integrated learning environment of a chapter (Lernumgebung/index.html). Deterministic, offline, no model call.

One self-contained page built from the book model (the same content as the PDFs) plus competencies, labs and
materials. Areas: Lernen (interactive textbook with embedded labs and quick checks), Üben, Klausur, Lernstand,
Tutor-Briefing, Material. Routing, progress, feedback and export/import run in templates/em_app.js.

Data separation: course/competency data, content (HTML rendered by typeset.Doc), items, labs (standalone em-lab-v1
pages embedded as iframes in embed mode), learning events (browser storage, em-learn-v2). Security: CSP with hashed
inline script/style; images, scripts and frames only from local files ('self' for http, file: for file://);
no network access; all text is escaped by the renderer; the runtime builds DOM with textContent except for the
engine-rendered content HTML.
"""
import base64
import hashlib
import html
import json
import re
from pathlib import Path

from . import typeset

TEMPLATES = Path(__file__).resolve().parent / 'templates'
E = lambda s: html.escape(str(s), quote=True)
SCHEMA = 'em-learn-app-v1'
LAB_SECTION = 'Interaktive Labs'


def _sha(s):
    return "'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'"


def _words(t):
    """Word stems (first six letters of words with at least five letters) for a robust, deterministic overlap."""
    return {w[:6] for w in re.findall(r'[a-zäöüß]{5,}', re.sub(r'<[^>]+>', ' ', t).lower())}


def _fix_paths(h):
    """Content HTML is rendered for the artefacts root; the app lives one folder below."""
    return re.sub(r'(src|href)="(?!https?:|#|data:|\.\./|/)([^"]+)"', r'\1="../\2"', h)


def _given(d, it):
    """Data tables and scaffolds that belong to the task (same rendering as the workbook)."""
    h = d.table(it['table']) if it.get('table') else ''
    if it.get('scaffold'):
        h += '<ol class="scaffold">' + ''.join(f'<li><span>{typeset.inline(x).replace("___", "<span class=blank></span>")}</span></li>' for x in it['scaffold']) + '</ol>'
    return h


def app_model(book, labs=(), materials=(), anki=None, chapter_id='', lab_dir='labs'):
    d = typeset.Doc(book, 'textbook'); m = book['meta']
    kc_labels = dict(book.get('kc_labels') or {})
    sections, lab_blocks = [], {}
    for sec in book['sections']:
        if sec['title'] == LAB_SECTION:
            for b in sec['blocks']:
                lab_blocks[b.get('href', '').split('/')[-1]] = b
    si = 0
    for sec in book['sections']:
        if sec['title'] == LAB_SECTION:
            continue
        si += 1
        blocks = [b for sub in (sec.get('subsections') or [{'blocks': sec.get('blocks', [])}]) for b in sub['blocks']]
        parts = [{'html': _fix_paths(d.block(b)), 'kc_ids': b.get('kc_ids') or [], 'type': b['type']} for b in blocks]
        kcs = []
        for b in blocks:
            for k in b.get('kc_ids') or []:
                if k not in kcs:
                    kcs.append(k)
        srcs = []
        for b in blocks:
            for s in re.split(r';\s*', b.get('src') or ''):
                if s and s not in srcs:
                    srcs.append(s)
        sections.append({'id': f's{si}', 'no': f'{m["chapter_no"]}.{si}', 'title': sec['title'], 'parts': parts, 'kc_ids': kcs, 'sources': srcs[:12],
                         'labs': [], 'cards': [], 'items': []})
    # labs: into the section whose blocks share most competencies, after the last block that teaches one of them
    lab_rows = []
    for lb in labs:
        fname = lb['file'].split('/')[-1]
        best, score = None, 0
        for s in sections:
            sc = len(set(lb['kc_ids']) & set(s['kc_ids']))
            if sc > score:
                best, score = s, sc
        if best is None:
            continue   # no competency link: never placed artificially (stays reachable under Material)
        after = max((i for i, p in enumerate(best['parts']) if set(p['kc_ids']) & set(lb['kc_ids'])), default=len(best['parts']) - 1)
        static = lab_blocks.get(fname, {}).get('svg', '')
        row = {'id': fname[:-5], 'title': lb['title'], 'href': f'{lab_dir}/{fname}', 'kc_ids': lb['kc_ids'], 'section': best['id'], 'after': after,
               'static_svg': static}
        best['labs'].append(row['id']); lab_rows.append(row)
    # quick checks: authored cards go to the section with the largest word overlap (deterministic)
    cards = []
    for n, c in enumerate(book.get('cards') or []):
        front, back = c.get('front') or c.get('Front') or '', c.get('back') or c.get('answer') or c.get('Back') or ''
        if not front or not back:
            continue
        wf = _words(front + ' ' + back)
        best = max(sections, key=lambda s: len(wf & _words(' '.join(p['html'] for p in s['parts'])))) if sections else None
        cid = f'c{n + 1}'
        cards.append({'id': cid, 'front': typeset.inline(front), 'back': typeset.md(back) + (typeset.md(c.get('explanation') or '') if c.get('explanation') else ''),
                      'section': best['id'] if best else None, 'source': c.get('source') or ''})
        if best:
            best['cards'].append(cid)
    # items: all workbook stages + exam flags
    exam_ids = {i['id'] for i in ((book.get('exam') or {}).get('items') or [])}
    items = []
    for st in book.get('stages') or []:
        for it in st['items']:
            s = it['solution']
            nums = sorted({x for x in re.findall(r'-?\d+(?:[.,]\d+)?', re.sub(r'\\\(|\\\)', ' ', s.get('answer') or ''))}) if it.get('operation') in ('CALCULATE', 'APPLY') else []
            sec = max(sections, key=lambda x: len(set(it.get('kc_keys') or []) & set(x['kc_ids']))) if sections else None
            if sec is not None and not set(it.get('kc_keys') or []) & set(sec['kc_ids']):
                sec = None
            sol_html = typeset._item_html(d, {'id': it['id'], 'no': it['id'], 'prompt': '', 'solution': s}, solution=True).split('</div>', 1)[1][:-len('</div>')] if s.get('answer') else ''
            items.append({'id': it['id'], 'stage': it.get('stage_label') or st['title'], 'stage_title': st['title'], 'level': st.get('level'),
                          'prompt': _fix_paths(typeset.md(it['prompt']) + _given(d, it)), 'points': it.get('points'), 'operation': it.get('operation'),
                          'title': it.get('title') or '', 'minutes': it.get('minutes'),
                          **({'transfer_dimension': it['transfer_dimension']} if it.get('transfer_dimension') else {}),
                          'kc_ids': it.get('kc_keys') or [], 'hints': [typeset.inline(h) for h in s.get('hints') or []],
                          'solution': _fix_paths(sol_html), 'rubric': [[typeset.inline(c), p] for c, p in s.get('rubric') or []],
                          'numbers': nums, 'exam': it['id'] in exam_ids, 'section': sec['id'] if sec else None,
                          'evidence_gap': bool(it.get('evidence_gap'))})
            if sec:
                sec['items'].append(it['id'])
    exam = book.get('exam') or {}
    known = {i['id'] for i in items}
    for it in exam.get('items') or []:          # edition exams carry their own items (not part of the workbook)
        if it['id'] in known:
            continue
        s_ = it['solution']
        sol_html = typeset._item_html(d, {'id': it['id'], 'no': it['id'], 'prompt': '', 'solution': s_}, solution=True).split('</div>', 1)[1][:-len('</div>')]
        items.append({'id': it['id'], 'stage': 'exam', 'stage_title': 'Probeklausur', 'level': 5, 'prompt': _fix_paths(typeset.md(it['prompt']) + _given(d, it)),
                      'points': it.get('points'), 'operation': it.get('operation'), 'title': it.get('title') or '', 'minutes': it.get('minutes'),
                      'kc_ids': it.get('kc_keys') or [], 'hints': [], 'solution': _fix_paths(sol_html), 'rubric': [[typeset.inline(c), p] for c, p in s_.get('rubric') or []],
                      'numbers': [], 'exam': True, 'section': None, 'evidence_gap': False})
    return {'schema': SCHEMA, 'course': m['course'], 'chapter': {'id': chapter_id, 'title': m['title'], 'no': m['chapter_no'], 'status': m.get('status_line', '')},
            'kcs': {k: kc_labels.get(k, '') for s in sections for k in s['kc_ids']} | {k: kc_labels.get(k, '') for i in items for k in i['kc_ids']},
            'sections': sections, 'labs': lab_rows, 'cards': cards, 'items': items,
            'exam': {'items': [i['id'] for i in exam.get('items') or []], 'total_points': exam.get('total_points'), 'subtitle': exam.get('subtitle', ''),
                     'minutes': exam.get('minutes'), 'aids': exam.get('aids'), 'blueprint': [dict(r, operator=typeset.OPS.get(r['operator'], r['operator']))
                                                                                             for r in (exam.get('blueprint') or {}).get('rows', [])]},
            'materials': list(materials), 'anki': anki}


def page(model, title):
    css = (TEMPLATES / 'em_tokens.css').read_text(encoding='utf-8') + (TEMPLATES / 'em_app.css').read_text(encoding='utf-8')
    js = (TEMPLATES / 'em_app.js').read_text(encoding='utf-8')
    # MathJax loads deferred: typeset the current view as soon as it is ready (the runtime typesets later views itself)
    mj_cfg = ('window.MathJax={tex:{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]]},svg:{fontCache:"global"},'
              'startup:{typeset:false,ready:function(){MathJax.startup.defaultReady();MathJax.startup.promise.then(function(){'
              'var m=document.getElementById("main");if(m)MathJax.typesetPromise([m]);});}}};')
    data = json.dumps(model, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    font = typeset.font_css('../assets/fonts')
    csp = ("default-src 'none'; img-src 'self' file: data:; font-src 'self' file: data:; frame-src 'self' file:; "
           f"script-src 'self' file: {_sha(js)} {_sha(mj_cfg)}; style-src 'self' file: 'unsafe-inline'; "
           "base-uri 'none'; form-action 'none'; connect-src 'none'")
    # style-src needs 'unsafe-inline': MathJax writes inline SVG styles. No script may be inline except the two hashed ones.
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">'
            f'<title>{E(title)}</title><style>{font}</style><style>{css}</style><script>{mj_cfg}</script>'
            '<script src="../assets/tex-svg-full.js" defer></script></head><body>'
            '<a class="skip" href="#main">Zum Inhalt</a><div id="app" class="app" data-ready="0">'
            '<noscript><p>Diese Lernumgebung braucht JavaScript. Die PDF-Dokumente im übergeordneten Ordner enthalten denselben Inhalt.</p></noscript></div>'
            f'<script type="application/json" id="em-course">{data}</script><script>{js}</script></body></html>')


def build(book, out_dir, labs=(), materials=(), anki=None, chapter_id=''):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    model = app_model(book, labs, materials, anki, chapter_id)
    (out / 'index.html').write_text(page(model, f'{book["meta"]["title"]} · Lernumgebung'), encoding='utf-8')
    (out / 'course.json').write_text(json.dumps({k: v for k, v in model.items() if k != 'sections'} | {'sections': [
        {k: v for k, v in s.items() if k != 'parts'} for s in model['sections']]}, ensure_ascii=False, indent=1), encoding='utf-8')
    return out / 'index.html'


def republish(src_dir, out_dir, tracks=(), fonts='../../assets/fonts'):
    """v0.19: re-render an already published learning environment with the current templates and embed the adaptive
    learning tracks whose competencies belong to this chapter. Deterministic, no model call, no content regeneration:
    the full model is read from the published index.html. Labs are re-rendered from their own spec files."""
    import shutil
    from .labs import build as LB
    from .learning import render as TRR
    src, out = Path(src_dir), Path(out_dir)
    h = (src / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<script type="application/json" id="em-course">(.*?)</script>', h, re.S)
    model = json.loads(m.group(1))
    out.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.name not in ('index.html',) and f.is_file():
            shutil.copy2(f, out / f.name)
    kcs = set(model['kcs']) | {k for s in model['sections'] for k in s['kc_ids']}
    rows = []
    for t in tracks:
        own = [k['id'] for k in t['kcs'] if k['id'] in kcs]
        if not own:
            continue
        p = TRR.write(t, out / 'lernstrecken', lab_href='../' + 'labs/' + t['lab'].replace('/', '__') + '.html', fonts=fonts, back='../index.html', back_label='Zur Lernumgebung')
        rows.append({'id': t['id'], 'title': t['title'], 'href': 'lernstrecken/' + p.name, 'kc_ids': own,
                     'case': 'Diagnose von Endsaldo/Tiefpunkt-Verwechslungen, Kontrastaufgabe, Transfer auf ein neues Zahlungsziel.' if t['domain'] == 'business_economics' else t['objective']})
    model['tracks'] = rows
    labs = []
    for js in sorted((src / 'labs').glob('*.json')):
        spec = json.loads(js.read_text(encoding='utf-8'))
        labs.append(str(LB.render(spec, out / 'labs', back_link='../index.html', fonts='../../assets/fonts', back_label='Zur Lernumgebung')))
    title = re.search(r'<title>(.*?)</title>', h, re.S).group(1)
    (out / 'index.html').write_text(page(model, html_unescape(title)), encoding='utf-8')
    return {'index': str(out / 'index.html'), 'tracks': [r['href'] for r in rows], 'labs': labs, 'model_calls': 0}


def html_unescape(s):
    import html as _h
    return _h.unescape(s)
