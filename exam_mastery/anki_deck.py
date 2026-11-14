"""Premium Anki package for a reference unit: versioned custom note types, HTML/CSS templates, media, .apkg.

Identity rules (verified by tests/test_reference_unit.py::AnkiPackage against a disposable collection):
- note GUID   = sha256(unit id | card key)[:20]   -> stable across wording and style changes
- notetype id = fixed 13-digit number per notetype -> template/CSS updates replace the old version on import
- deck id     = fixed per unit
Templates use Anki's native MathJax (\\( \\)) and plain HTML/CSS. No JavaScript, no network, no external fonts.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import re
import shutil
import tempfile
from pathlib import Path

TEMPLATE_VERSION = '1.0.0'
FIELDS = ['StableID', 'Course', 'Chapter', 'KC', 'Prerequisites', 'Prompt', 'CanonicalAnswer', 'Why',
          'MicroExample', 'Misconception', 'Source', 'DiagramMedia', 'Version']
CLOZE_FIELDS = ['Text'] + [f for f in FIELDS if f not in ('Prompt', 'CanonicalAnswer')]

CSS = r"""
/* Exam Mastery card design v{v}. Tokens mirror the offline app. No JavaScript, no web fonts. */
.card{--bg:#fbfaf7;--panel:#ffffff;--ink:#1d1f24;--mute:#5d6470;--line:#e2ded5;--accent:#2756c4;--accent2:#c2410c;--ok:#15803d;--soft:#eef2fb;
 font-family:"Iowan Old Style","Charter",Georgia,serif;font-size:19px;line-height:1.55;color:var(--ink);background:var(--bg);text-align:left;margin:0;padding:0}
.card.nightMode,.nightMode .card{--bg:#15171b;--panel:#1d2026;--ink:#e8e6e1;--mute:#a3a8b2;--line:#323640;--accent:#7aa2ff;--accent2:#ff9b5e;--ok:#4ade80;--soft:#232a3a}
.em{max-width:680px;margin:0 auto;padding:18px 18px 22px}
.em-ctx{font:600 12px/1.3 -apple-system,"Segoe UI",system-ui,sans-serif;letter-spacing:.04em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
.em-ctx .kc{color:var(--mute);font-weight:500;text-transform:none;letter-spacing:0}
.em-q{font-size:1.06em}
.em-type{display:inline-block;font:600 11px -apple-system,system-ui,sans-serif;padding:2px 8px;border-radius:9px;background:var(--soft);color:var(--accent);margin-bottom:8px}
.em-a{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--ok);border-radius:10px;padding:10px 14px;margin:14px 0 10px;font-size:1.04em}
.em-why{margin:8px 0}.em-why b,.em-ex b,.em-mis b{font:600 13px -apple-system,system-ui,sans-serif;color:var(--mute);margin-right:4px}
.em-ex{background:var(--soft);border-radius:8px;padding:6px 12px;margin:8px 0}
.em-mis{border-left:3px solid var(--accent2);padding:2px 0 2px 10px;margin:8px 0}
.em-diag{margin:10px 0;text-align:center}.em-diag img{max-width:100%;height:auto;background:#fff;border-radius:8px;border:1px solid var(--line)}
.em-src{font:12px/1.4 -apple-system,system-ui,sans-serif;color:var(--mute);border-top:1px solid var(--line);padding-top:6px;margin-top:12px}
.em-meta{font:10px -apple-system,system-ui,sans-serif;color:var(--mute);opacity:.7;margin-top:2px}
code{font-family:ui-monospace,Menlo,monospace;font-size:.85em;background:var(--soft);padding:1px 4px;border-radius:4px}
.cloze{font-weight:600;color:var(--accent)}
mjx-container{max-width:100%;overflow-x:auto;overflow-y:hidden}
hr#answer{border:none;border-top:1px dashed var(--line);margin:14px 0}
.mobile .card,.card.mobile{font-size:17px}.mobile .em{padding:12px 12px 16px}
""".replace('{v}', TEMPLATE_VERSION)

CTX = '<div class="em-ctx">{{Course}} · {{Chapter}}<br><span class="kc">{{KC}}</span></div>'
BACK_TAIL = ('<div class="em-why"><b>Warum</b>{{Why}}</div>'
             '{{#MicroExample}}<div class="em-ex"><b>Beispiel</b>{{MicroExample}}</div>{{/MicroExample}}'
             '{{#Misconception}}<div class="em-mis"><b>Häufiger Fehler</b>{{Misconception}}</div>{{/Misconception}}'
             '{{#DiagramMedia}}<div class="em-diag">{{DiagramMedia}}</div>{{/DiagramMedia}}'
             '<div class="em-src">Quelle: {{Source}}</div><div class="em-meta">{{StableID}} · v{{Version}}</div></div>')
NOTETYPES = {
    'concept': dict(id=1794600000001, name='Exam Mastery · Concept',
                    qfmt='<div class="em">' + CTX + '<div class="em-type">Begriff</div><div class="em-q">{{Prompt}}</div></div>',
                    afmt='<div class="em">' + CTX + '<div class="em-type">Begriff</div><div class="em-q">{{Prompt}}</div><hr id="answer"><div class="em-a">{{CanonicalAnswer}}</div>' + BACK_TAIL),
    'math': dict(id=1794600000002, name='Exam Mastery · Math & Diagram',
                 qfmt='<div class="em">' + CTX + '<div class="em-type">Formel</div><div class="em-q">{{Prompt}}</div></div>',
                 afmt='<div class="em">' + CTX + '<div class="em-type">Formel</div><div class="em-q">{{Prompt}}</div><hr id="answer"><div class="em-a">{{CanonicalAnswer}}</div>' + BACK_TAIL),
    'cloze': dict(id=1794600000003, name='Exam Mastery · Cloze',
                  qfmt='<div class="em">' + CTX + '<div class="em-type">Lücke</div><div class="em-q">{{cloze:Text}}</div></div>',
                  afmt='<div class="em">' + CTX + '<div class="em-type">Lücke</div><div class="em-q">{{cloze:Text}}</div><hr id="answer">' + BACK_TAIL),
}
DECK_ID = 1794600000100


def _stable_i64(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], 'big', signed=True)


def guid(unit_id: str, key: str) -> str:
    return hashlib.sha256(f'{unit_id}|{key}'.encode()).hexdigest()[:20]


def media_name(unit_id: str, fname: str) -> str:
    return f'em_{re.sub(r"[^a-z0-9]+", "_", unit_id)}_{fname}'


def note_fields(unit: dict, c: dict, version: str) -> dict:
    base = {'StableID': c['key'], 'Course': unit['course'], 'Chapter': unit['chapter'], 'KC': unit['kcs'][c['kc']],
            'Prerequisites': c.get('prereq', ''), 'Why': c['why'], 'MicroExample': c.get('example', ''),
            'Misconception': c.get('mistake', ''), 'Source': c['source'], 'Version': version,
            'DiagramMedia': f'<img src="{media_name(unit["id"], c["diagram"])}" alt="Diagramm">' if c.get('diagram') else ''}
    if c['type'] == 'cloze':
        return {'Text': c['cloze'], **base}
    return {'Prompt': c['prompt'], 'CanonicalAnswer': c['answer'], **base}


def inspectable(unit: dict) -> dict:
    """Transparent intermediate representation (JSON) of exactly what goes into the package."""
    version = unit.get('version', '0')
    return {'template_version': TEMPLATE_VERSION, 'deck': deck_name(unit), 'notetypes': {k: {kk: v for kk, v in n.items()} for k, n in NOTETYPES.items()},
            'css': CSS, 'notes': [{'guid': guid(unit['id'], c['key']), 'type': NOTETYPES['math' if c['type'] == 'math' else c['type']]['name'],
                                   'tags': tags(unit, c), 'fields': note_fields(unit, c, version)} for c in unit['cards']]}


def deck_name(unit):
    return f'Exam Mastery::{unit["course"]}::{unit["chapter"]}'


def tags(unit, c):
    return ['exam-mastery', f'em::{re.sub(r"[^A-Za-z0-9]+", "-", unit["id"])}', f'kc::{c["kc"]}', f'type::{c["type"]}']


def _make_notetype(col, spec, cloze=False):
    mm = col.models
    nt = mm.new(spec['name'])
    if cloze:
        nt['type'] = 1
    for f in (CLOZE_FIELDS if cloze else FIELDS):
        fld = mm.new_field(f)
        fld['id'] = _stable_i64(f'{spec["id"]}|field|{f}')        # Anki compares field ids when updating
        mm.add_field(nt, fld)
    t = mm.new_template('Karte 1')
    t['qfmt'], t['afmt'] = spec['qfmt'], spec['afmt']
    t['id'] = _stable_i64(f'{spec["id"]}|template|Karte 1')
    mm.add_template(nt, t)
    nt['css'] = CSS
    changes = mm.add_dict(nt)
    old_id = changes.id
    # Stable notetype id so that later packages update this notetype instead of creating a copy.
    # Done on an empty build collection before any note exists; verified by the reimport test.
    for table, col_name in (('notetypes', 'id'), ('fields', 'ntid'), ('templates', 'ntid')):
        col.db.execute(f'update {table} set {col_name}=? where {col_name}=?', spec['id'], old_id)
    col.models._clear_cache() if hasattr(mm, '_clear_cache') else None
    nt2 = mm.get(spec['id'])
    assert nt2 and nt2['name'] == spec['name'], 'stable notetype id could not be set'
    return nt2


def build_apkg(unit: dict, media_dir: Path, out: Path) -> dict:
    """Write a .apkg built with the real Anki library; returns a summary (counts, ids)."""
    from anki.collection import Collection, DeckIdLimit
    from anki.import_export_pb2 import ExportAnkiPackageOptions
    version = unit.get('version', '0')
    tmp = Path(tempfile.mkdtemp(prefix='em-anki-'))
    try:
        col = Collection(str(tmp / 'build.anki2'))
        nts = {k: _make_notetype(col, spec, cloze=(k == 'cloze')) for k, spec in NOTETYPES.items()}
        did = col.decks.id(deck_name(unit))
        deck = col.decks.get(did)
        for c in unit['cards']:
            nt = nts['math' if c['type'] == 'math' else c['type']]
            note = col.new_note(nt)
            for k, v in note_fields(unit, c, version).items():
                note[k] = v
            note.guid = guid(unit['id'], c['key'])
            note.tags = tags(unit, c)
            col.add_note(note, did)
        for f in sorted(media_dir.glob('*.svg')):
            target = media_name(unit['id'], f.name)
            shutil.copy2(f, Path(col.media.dir()) / target)
        out.parent.mkdir(parents=True, exist_ok=True)
        n = col.export_anki_package(out_path=str(out), options=ExportAnkiPackageOptions(with_scheduling=False, with_media=True, legacy=False),
                                    limit=DeckIdLimit(did))
        summary = {'notes': n, 'cards': col.card_count(), 'deck': deck_name(unit), 'notetypes': {k: v['id'] for k, v in nts.items()}}
        col.close()
        return summary
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------- self-authored SVG diagrams (also used by the app) ----------------
def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="Helvetica, Arial, sans-serif"><rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')


def diagrams(out: Path, unit: dict):
    out.mkdir(parents=True, exist_ok=True)
    esc = html.escape
    # 1 dependency cones for T=5, t=3
    body, T, t = '', 5, 3
    rows = [('vorwärts', set(range(1, t + 1)), '#2756c4'), ('rückwärts', set(range(t, T + 1)), '#c2410c'), ('bidirektional', set(range(1, T + 1)), '#15803d')]
    for r, (lab, dep, col) in enumerate(rows):
        y = 30 + r * 52
        body += f'<text x="10" y="{y + 22}" font-size="15" fill="#333">{esc(lab)}</text>'
        for i in range(1, T + 1):
            on = i in dep
            body += (f'<rect x="{150 + (i - 1) * 62}" y="{y}" width="50" height="34" rx="6" fill="{col if on else "#f2f2f2"}" '
                     f'stroke="{col}" stroke-width="{2.5 if i == t else 1}"/><text x="{175 + (i - 1) * 62}" y="{y + 22}" '
                     f'font-size="15" text-anchor="middle" fill="{"#fff" if on else "#999"}">x{i}</text>')
    body += '<text x="10" y="196" font-size="13" fill="#555">Gefüllt: Eingaben, von denen der Zustand an Position 3 abhängen kann (T = 5).</text>'
    (out / 'dependency_cones.svg').write_text(_svg(500, 206, body), encoding='utf-8')
    # 2 BIO / IO / BILOU on a sentence
    words = ['flights', 'on', 'Monday', 'Tuesday']
    schemes = [('IO', ['O', 'O', 'DAY', 'DAY']), ('BIO', ['O', 'O', 'B-DAY', 'B-DAY']), ('BILOU', ['O', 'O', 'U-DAY', 'U-DAY'])]
    body = ''.join(f'<text x="{120 + i * 104}" y="28" font-size="15" text-anchor="middle" fill="#111">{esc(w)}</text>' for i, w in enumerate(words))
    for r, (name, tagsq) in enumerate(schemes):
        y = 48 + r * 40
        body += f'<text x="8" y="{y + 20}" font-size="14" font-weight="bold" fill="#2756c4">{name}</text>'
        for i, tg in enumerate(tagsq):
            fill = '#fde6d8' if tg != 'O' else '#f4f4f4'
            body += f'<rect x="{72 + i * 104}" y="{y}" width="96" height="28" rx="5" fill="{fill}" stroke="#ccc"/><text x="{120 + i * 104}" y="{y + 19}" font-size="13" text-anchor="middle" fill="#222">{tg}</text>'
    body += '<text x="8" y="182" font-size="12" fill="#555">Zwei Spannen [Monday] [Tuesday]: IO ergibt DAY DAY – wie eine Spanne [Monday Tuesday]. BIO trennt sie mit B-.</text>'
    (out / 'bio_schemes.svg').write_text(_svg(560, 196, body), encoding='utf-8')
    # 3 F1 iso-lines vs arithmetic mean
    S_, pad = 260, 40
    X = lambda p: pad + p * S_
    Y = lambda r: pad + (1 - r) * S_
    body = f'<rect x="{pad}" y="{pad}" width="{S_}" height="{S_}" fill="none" stroke="#bbb"/>'
    for F in (0.2, 0.4, 0.6, 0.8):
        pts = []
        for k in range(121):
            p = F / 2 + (1 - F / 2) * k / 120 + 1e-6
            r = F * p / (2 * p - F)
            if r <= 1.0001:
                pts.append(f'{X(p):.1f},{Y(r):.1f}')
        body += f'<polyline points="{" ".join(pts)}" fill="none" stroke="#2756c4" stroke-width="1.8"/>'
        a = 2 * F
        body += f'<line x1="{X(max(0, a - 1)):.1f}" y1="{Y(min(1, a)):.1f}" x2="{X(min(1, a)):.1f}" y2="{Y(max(0, a - 1)):.1f}" stroke="#c2410c" stroke-dasharray="5 4"/>'
        body += f'<text x="{X(1) + 4}" y="{Y(F / (2 - F)) + 4:.1f}" font-size="11" fill="#2756c4">{str(F).replace(".", ",")}</text>'
    body += (f'<circle cx="{X(0.1)}" cy="{Y(1)}" r="6" fill="#c2410c"/><text x="{X(0.1) + 10}" y="{Y(1) + 16}" font-size="12" fill="#c2410c">P=0,1, R=1: F1≈0,182</text>'
             f'<text x="{pad + S_ / 2}" y="{pad + S_ + 28}" font-size="13" text-anchor="middle" fill="#555">Precision P</text>'
             f'<text x="12" y="{pad + S_ / 2}" font-size="13" fill="#555" transform="rotate(-90 12 {pad + S_ / 2})" text-anchor="middle">Recall R</text>'
             f'<text x="{pad}" y="24" font-size="12" fill="#555">blau: gleiches F1 · orange gestrichelt: gleiches arithmetisches Mittel</text>')
    (out / 'f1_contours.svg').write_text(_svg(360, 345, body), encoding='utf-8')
    # 4 Viterbi lattice for C1
    from . import seqlab as S
    L, W, E = ['O', 'B-LOC', 'I-LOC'], ['in', 'New', 'York'], [[2, 0, 0.5], [0.3, 1.0, 1.2], [0, 0.2, 1.5]]
    best = S.viterbi(E, L)[1]
    greedy = S.greedy(E, L)
    Xl = lambda t: 130 + t * 170
    Yl = lambda k: 40 + k * 60
    body = ''.join(f'<text x="10" y="{Yl(k) + 5}" font-size="14" fill="#555">{l}</text>' for k, l in enumerate(L))
    for t in range(1, 3):
        for name, path, col, dash in (('g', greedy, '#b91c1c', '6 4'), ('v', best, '#15803d', '')):
            body += f'<line x1="{Xl(t - 1) + 28}" y1="{Yl(L.index(path[t - 1]))}" x2="{Xl(t) - 28}" y2="{Yl(L.index(path[t]))}" stroke="{col}" stroke-width="3.5" stroke-dasharray="{dash}"/>'
    for t, row in enumerate(E):
        body += f'<text x="{Xl(t)}" y="222" font-size="15" text-anchor="middle" fill="#111">{W[t]}</text>'
        for k, v in enumerate(row):
            body += f'<rect x="{Xl(t) - 28}" y="{Yl(k) - 18}" width="56" height="36" rx="7" fill="#fff" stroke="#999"/><text x="{Xl(t)}" y="{Yl(k) + 5}" font-size="14" text-anchor="middle">{str(v).replace(".", ",")}</text>'
    body += '<text x="10" y="248" font-size="12" fill="#b91c1c">gestrichelt rot: gierig (O I-LOC I-LOC, ungültig)</text><text x="300" y="248" font-size="12" fill="#15803d">grün: Viterbi (O B-LOC I-LOC, Score 4,5)</text>'
    (out / 'viterbi_lattice.svg').write_text(_svg(560, 260, body), encoding='utf-8')
    return sorted(p.name for p in out.glob('*.svg'))


def render_previews(apkg: Path, out_dir: Path, mathjax_js: Path, keys=None) -> list:
    """Import the package into a disposable collection, let Anki produce question/answer HTML, and screenshot it.

    This SIMULATES the reviewer: Anki desktop uses Qt WebEngine (Chromium), AnkiMobile WKWebView (WebKit).
    The real Anki applications were not driven; their own reviewer CSS/MathJax setup may differ in details.
    """
    from anki.collection import Collection
    from anki.import_export_pb2 import ImportAnkiPackageRequest, ImportAnkiPackageOptions
    from playwright.sync_api import sync_playwright
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='em-anki-prev-'))
    shots = []
    try:
        col = Collection(str(tmp / 'prev.anki2'))
        col.import_anki_package(ImportAnkiPackageRequest(package_path=str(apkg), options=ImportAnkiPackageOptions()))
        media = Path(col.media.dir())
        for f in media.iterdir():
            shutil.copy2(f, out_dir / f.name)
        shutil.copy2(mathjax_js, out_dir / 'tex-svg-full.js')
        cards = []
        for cid in col.find_cards(''):
            c = col.get_card(cid)
            sid = c.note()['StableID']
            if keys and sid not in keys:
                continue
            cards.append((sid, c.ord, c.question(), c.answer()))
        col.close()
        page = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<script>window.MathJax={tex:{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]]},startup:{typeset:true}};</script>'
                '<script src="tex-svg-full.js"></script></head><body class="card {cls}" style="margin:0">{html}</body></html>')
        with sync_playwright() as p:
            for engine_name, engine in (('chromium', p.chromium), ('webkit', p.webkit)):
                b = engine.launch()
                for sid, ordn, q, a in cards:
                    for side, h in (('front', q), ('back', a)):
                        for theme, cls, width in (('hell', '', 720), ('dunkel', 'nightMode night_mode', 720), ('mobil', 'mobile', 390)):
                            if engine_name == 'webkit' and theme == 'hell' and width == 720:
                                pass
                            name = f'{re.sub(r"[^a-z0-9]+", "_", sid)}_{ordn}_{side}_{theme}_{engine_name}.png'
                            f = out_dir / f'_{name}.html'
                            f.write_text(page.replace('{cls}', cls).replace('{html}', h), encoding='utf-8')
                            pg = b.new_page(viewport={'width': width, 'height': 600})
                            pg.goto(f.as_uri()); pg.wait_for_timeout(600)
                            try:
                                pg.wait_for_function('!window.MathJax || !MathJax.startup || MathJax.startup.promise', timeout=5000)
                                pg.evaluate('window.MathJax && MathJax.startup && MathJax.startup.promise')
                            except Exception:
                                pass
                            pg.wait_for_timeout(300)
                            pg.screenshot(path=str(out_dir / name), full_page=True)
                            info = pg.evaluate('''() => ({overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
                                maxGlyph: Math.max(0, ...[...document.querySelectorAll('mjx-container:not([display])')].map(m => m.getBoundingClientRect().height)),
                                rawTex: /\\\\\\(|\\\\\\[/.test(document.body.innerText)})''')
                            shots.append({'card': sid, 'ord': ordn, 'side': side, 'theme': theme, 'engine': engine_name, 'file': name, **info})
                            pg.close(); f.unlink()
                b.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rows = ''.join(f'<figure><img src="{s["file"]}" loading="lazy"><figcaption>{s["card"]} · {s["side"]} · {s["theme"]} · {s["engine"]}</figcaption></figure>' for s in shots)
    (out_dir / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Anki-Kartenvorschau</title><style>body{font-family:system-ui;margin:16px;background:#ddd}'
                                        'figure{display:inline-block;margin:8px;vertical-align:top;background:#fff;padding:6px;max-width:420px}img{max-width:100%}figcaption{font-size:12px}</style>'
                                        '<h1>Anki-Kartenvorschau (simuliert)</h1><p>Von Anki erzeugtes Karten-HTML aus dem importierten Paket, gerendert in Chromium (wie Anki Desktop) und WebKit (wie AnkiMobile). '
                                        'Nicht in der echten Anki-App geprüft.</p>' + rows, encoding='utf-8')
    return shots
