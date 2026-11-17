"""Anki deck v2 (B9): authored cards, two note types, semantic identities, a calm design that works in light and dark mode.

Identity model (rule C5):
- The note GUID is derived from course slug + chapter slug + the card's semantic key (e.g. "insolvency/reasons"),
  never from a generated item number or the card text. Re-exports update the same notes; Anki keeps their cards,
  scheduling and review history.
- The note types have fixed ids and fixed field/template ids, so a new export never creates a parallel note type.
- Every export stamps note modification times later than the previous export (state file next to the deck), so
  Anki's importer treats changed notes as newer and updates them.
- Removed cards are reported as retirement candidates and never deleted by the engine.

Card kinds (shown as a small label): Begriff, Zusammenhang, Vergleich, Bedingung, Rechnen, Abbildung, Denkfehler, Lückentext.
"""
import hashlib
import json
import re
import shutil
import tempfile
import time
from pathlib import Path

from html import escape as E

from .common import ContractError, write_json

KIND_LABEL = {'concept': 'Begriff', 'mechanism': 'Zusammenhang', 'compare': 'Vergleich', 'condition': 'Bedingung',
              'math': 'Rechnen', 'visual': 'Abbildung', 'misconception': 'Denkfehler', 'cloze': 'Lückentext', 'fact': 'Kennzahl',
              # B32 card types
              'symbol': 'Symbol & Annahme', 'derivation': 'Herleitungsschritt', 'trace': 'Algorithmus-Spur', 'transfer': 'Anwenden'}
BASIC_FIELDS = ['Key', 'Front', 'Context', 'Answer', 'Explanation', 'Example', 'Pitfall', 'Source', 'Kind', 'Meta']
NOTE_BASIC, NOTE_CLOZE = 'Exam Mastery · Basis (v3)', 'Exam Mastery · Lückentext (v3)'
CLOZE_FIELDS = ['Key', 'Text', 'Extra', 'Source', 'Kind', 'Meta']

# B34: every card kind belongs to one cognitive demand; the card shows it as a coloured chip (colour + word).
COGNITIVE = {'concept': 'recall', 'symbol': 'recall', 'fact': 'recall', 'cloze': 'recall',
             'mechanism': 'concept', 'compare': 'concept', 'condition': 'concept',
             'math': 'math', 'derivation': 'math', 'trace': 'apply', 'visual': 'visual', 'misconception': 'diagnose', 'transfer': 'transfer'}
COG_LABEL = {'recall': 'Wissen abrufen', 'concept': 'Verstehen', 'math': 'Mathematik abrufen', 'apply': 'Anwenden', 'visual': 'Visuell denken',
             'diagnose': 'Fehler finden', 'transfer': 'Transfer'}


def kind_html(kind):
    cog = COGNITIVE.get(kind, 'recall')
    return f'<span class="k k-{cog}">{E(COG_LABEL[cog])}</span><span class="k2">{E(KIND_LABEL.get(kind, kind))}</span>'


CSS = r"""
@font-face{font-family:"EM Sans";src:url("_em-sans-400.woff2") format("woff2");font-weight:400}
@font-face{font-family:"EM Sans";src:url("_em-sans-600.woff2") format("woff2");font-weight:600}
@font-face{font-family:"EM Sans";src:url("_em-sans-700.woff2") format("woff2");font-weight:700}
.card{--bg:#F6F7F9;--paper:#FFFFFF;--ink:#1C2430;--ink2:#3C4856;--muted:#667383;--line:#DCE2E8;--navy:#16263D;
 --a:#26704A;--a-l:#E7F3EC;--why:#24578F;--why-l:#EAF1FA;--ex:#8A5A00;--ex-l:#FBF2DF;--pit:#B53A2C;--pit-l:#FBEAE6;
 --c-recall:#16263D;--c-concept:#0B6E6E;--c-math:#3D3F96;--c-apply:#24578F;--c-visual:#7A3B76;--c-diagnose:#B53A2C;--c-transfer:#26704A;
 font-family:"EM Sans","Source Sans 3","Helvetica Neue","Segoe UI",Roboto,Arial,sans-serif;font-size:18px;line-height:1.52;
 color:var(--ink);background:var(--bg);text-align:left;margin:0;padding:0}
.nightMode.card,.night_mode.card,.card.nightMode,.card.night_mode{--bg:#121519;--paper:#1A1F25;--ink:#E4E9EF;--ink2:#C2CBD5;--muted:#8D99A6;--line:#2C343D;--navy:#C9D6E6;
 --a:#7CCB9F;--a-l:#18291F;--why:#8DB8E8;--why-l:#17222F;--ex:#E2B65C;--ex-l:#2A2416;--pit:#F0907F;--pit-l:#2C1A17;
 --c-recall:#9FB2CC;--c-concept:#5FC2BE;--c-math:#A9AAF0;--c-apply:#8DB8E8;--c-visual:#D99BD4;--c-diagnose:#F0907F;--c-transfer:#7CCB9F}
.em{max-width:660px;margin:14px auto;padding:20px 22px 18px;background:var(--paper);border-radius:10px;border:1px solid var(--line)}
.em-head{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin-bottom:12px}
.k{display:inline-block;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#fff;border-radius:4px;padding:2px 8px;background:var(--c-recall)}
.nightMode .k,.night_mode .k{color:#121519}
.k-concept{background:var(--c-concept)}.k-math{background:var(--c-math)}.k-apply{background:var(--c-apply)}.k-visual{background:var(--c-visual)}
.k-diagnose{background:var(--c-diagnose)}.k-transfer{background:var(--c-transfer)}
.k2{font-size:12px;color:var(--muted);letter-spacing:.04em}
.em-q{font-size:21px;font-weight:600;line-height:1.38;color:var(--ink)}
.em-ctx{margin-top:12px;font-size:16.5px;color:var(--ink2)}
.em img{max-width:100%;max-height:340px;height:auto;display:block;margin:12px auto;border-radius:6px;background:#fff;padding:4px}
hr#answer{border:none;border-top:1px dashed var(--line);margin:18px 0 14px}
.em-sec{margin-top:12px;padding:8px 12px 9px;border-radius:0 8px 8px 0;font-size:16.5px;color:var(--ink2)}
.em-sec>.lab{display:block;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.em-a{border-left:5px solid var(--a);background:var(--a-l);font-size:18.5px;font-weight:600;color:var(--ink)}.em-a>.lab{color:var(--a)}
.em-x{border-left:5px solid var(--why);background:var(--why-l)}.em-x>.lab{color:var(--why)}
.em-ex{border-left:5px solid var(--ex);background:var(--ex-l)}.em-ex>.lab{color:var(--ex)}
.em-pit{border-left:5px solid var(--pit);background:var(--pit-l)}.em-pit>.lab{color:var(--pit)}
.em-foot{margin-top:14px;padding-top:8px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);line-height:1.45}
.em-foot .src{color:var(--ink2);font-weight:600}
.em ul,.em ol{margin:6px 0;padding-left:22px}.em li{margin:3px 0}
.em table{border-collapse:collapse;width:100%;font-size:15px;margin:8px 0;display:block;overflow-x:auto}
.em th{text-align:left;border-bottom:1.5px solid var(--ink);padding:4px 8px}.em td{border-bottom:1px solid var(--line);padding:4px 8px;vertical-align:top}
.cloze{font-weight:700;color:var(--c-math)}
mjx-container{overflow-x:auto;overflow-y:hidden;max-width:100%}
@media (max-width:480px){.card{font-size:16.5px}.em{margin:0;border-radius:0;border-left:none;border-right:none;padding:16px 14px}.em-q{font-size:18.5px}.em-sec{font-size:15.5px}.em-a{font-size:16.5px}}
"""

_HEAD = '<div class="em-head">{{Kind}}</div>'
BASIC_Q = ('<div class="em">' + _HEAD + '<div class="em-q">{{Front}}</div>'
           '{{#Context}}<div class="em-ctx">{{Context}}</div>{{/Context}}</div>')
BASIC_A = ('<div class="em">' + _HEAD + '<div class="em-q">{{Front}}</div>'
           '{{#Context}}<div class="em-ctx">{{Context}}</div>{{/Context}}<hr id="answer">'
           '<div class="em-sec em-a"><span class="lab">Antwort</span>{{Answer}}</div>'
           '{{#Explanation}}<div class="em-sec em-x"><span class="lab">Warum</span>{{Explanation}}</div>{{/Explanation}}'
           '{{#Example}}<div class="em-sec em-ex"><span class="lab">Rechnung / Beispiel</span>{{Example}}</div>{{/Example}}'
           '{{#Pitfall}}<div class="em-sec em-pit"><span class="lab">Typischer Denkfehler</span>{{Pitfall}}</div>{{/Pitfall}}'
           '<div class="em-foot">{{#Source}}<span class="src">{{Source}}</span><br>{{/Source}}{{Meta}}</div></div>')
CLOZE_Q = '<div class="em">' + _HEAD + '<div class="em-q" style="font-weight:500">{{cloze:Text}}</div></div>'
CLOZE_A = ('<div class="em">' + _HEAD + '<div class="em-q" style="font-weight:500">{{cloze:Text}}</div>'
           '{{#Extra}}<hr id="answer"><div class="em-sec em-x"><span class="lab">Warum</span>{{Extra}}</div>{{/Extra}}'
           '<div class="em-foot">{{#Source}}<span class="src">{{Source}}</span><br>{{/Source}}{{Meta}}</div></div>')


def _id(*parts, n=8, signed=True):
    return int.from_bytes(hashlib.sha256('|'.join(parts).encode()).digest()[:n], 'big', signed=signed)


def slug(s):
    s = re.sub(r'[^a-z0-9äöüß]+', '-', str(s).lower()).strip('-')
    return s or 'x'


def guid(course_slug, chapter_slug, key):
    from anki.utils import base91
    return base91(int.from_bytes(hashlib.sha256(f'em-card-v2|{course_slug}|{chapter_slug}|{key}'.encode()).digest()[:8], 'big'))


def _html(s):
    """Card text: same light markup as the books (bold, italics, lists, line breaks); math stays as \\( \\)."""
    from .typeset import md
    out = md(s)
    # B33: a punctuation mark right after inline math must not wrap onto its own line ("… R_max" / "?")
    out = re.sub(r'(\\\(.{1,60}?\\\))([?.!,:;])', r'<span style="white-space:nowrap">\1\2</span>', out)
    return out[3:-4] if out.startswith('<p>') and out.count('<p>') == 1 and out.endswith('</p>') else out


def _notetype(col, name, fields, qfmt, afmt, cloze=False):
    mm = col.models
    nt = mm.new(name)
    nt['id'] = _id('em-notetype-v2', name, n=6, signed=False) or 1
    if cloze:
        nt['type'] = 1
    for f in fields:
        fld = mm.new_field(f); fld['id'] = _id('em-field-v2', name, f); mm.add_field(nt, fld)
    t = mm.new_template('Karte'); t['id'] = _id('em-template-v2', name); t['qfmt'] = qfmt; t['afmt'] = afmt
    mm.add_template(nt, t)
    nt['css'] = CSS; nt['sortf'] = 1
    mm.update(nt, preserve_usn=True)
    return mm.get(nt['id'])


DIFF = {1: 'Einstieg', 2: 'Standard', 3: 'Vertiefung'}


def card_meta(c):
    """Visible card provenance on the back: competency, level, source level (compact; the authoring rationale stays in
    the deck report, not on the card)."""
    bits = []
    if c.get('learning_objective'):
        bits.append('Kompetenz: ' + c['learning_objective'])
    if c.get('difficulty'):
        bits.append('Stufe: ' + DIFF.get(c['difficulty'], str(c['difficulty'])))
    if c.get('provenance'):
        bits.append({'course': 'Ebene A · Vorlesung', 'didactic': 'Ebene C · eigene Übung, nachgerechnet', 'supplement': 'Ebene B · Fachliteratur',
                     'interpretation': 'Ebene C · eigene Erklärung'}.get(c['provenance'], c['provenance']))
    return E(' · '.join(bits))


_MDTAB = re.compile(r'<table')


def render_lint(c, vals):
    """B32 render gate on the final field HTML: absolute-value bars must never become a table, math delimiters
    must balance, no markdown residue, no empty answer, cloze gaps only in cloze cards, media referenced exist."""
    p = []
    for k, v in vals.items():
        if k in ('Key', 'Kind', 'Meta'):
            continue
        src = c.get({'Front': 'front', 'Answer': 'answer', 'Text': 'text', 'Explanation': 'explanation', 'Context': 'context'}.get(k, ''), '') or ''
        if _MDTAB.search(v) and '|---' not in src.replace(' ', '') and '|:--' not in src.replace(' ', ''):
            p.append(f'{k}: table produced from text without a table separator (|...| misread)')
        if v.count('\\(') != v.count('\\)') or v.count('\\[') != v.count('\\]'):
            p.append(f'{k}: unbalanced math delimiters')
        if re.search(r'(?<![*\\])\*\*(?!\*)', re.sub(r'\\\(.*?\\\)', '', v)):
            p.append(f'{k}: markdown residue **')
        if k != 'Text' and '{{c' in v:
            p.append(f'{k}: cloze marker outside a cloze card')
    if c.get('kind') != 'cloze' and not re.sub(r'<[^>]+>', '', vals.get('Answer', '')).strip():
        p.append('Answer empty')
    return p


def card_lint(c):
    """Rules C1-C3 and C5 for one authored card. Returns problems."""
    p = []
    key = c.get('key') or ''
    if not re.fullmatch(r'[a-z0-9][a-z0-9/_-]{2,80}', key):
        p.append('C5: semantic key missing or malformed')
    if c.get('kind') == 'cloze':
        gaps = re.findall(r'\{\{c(\d+)::', c.get('text') or '')
        if not gaps:
            p.append('C3: cloze without gaps')
        if len(set(gaps)) > 3:
            p.append('C3: more than 3 cloze numbers')
        if len((c.get('text') or '').split()) > 70:
            p.append('C3: cloze text too long (> 70 words)')
        return p
    f = re.sub(r'\\\(.*?\\\)', 'X', c.get('front') or '')
    if len(f.split()) > 30:
        p.append('C1: front longer than 30 words')
    if f.count('?') != 1:
        p.append('C1: front must ask exactly one question')
    if re.search(r'(Gehen Sie|Erläutern Sie .* und .* Sie|insbesondere darauf)', f):
        p.append('C1: essay-style assignment instead of a retrieval question')
    a = re.sub(r'\\\(.*?\\\)', 'X', c.get('answer') or '')
    if len(a.split()) > 35:
        p.append('C2: direct answer longer than 35 words')
    if c.get('kind') not in KIND_LABEL:
        p.append(f'unknown kind {c.get("kind")!r}')
    from .didactic_rules import meta_language
    for fld in ('front', 'answer', 'explanation', 'example', 'pitfall', 'context'):
        if meta_language(c.get(fld) or ''):
            p.append(f'T6: production meta language in {fld}')
    return p


def build_deck(cards, deck_name, course_slug, chapter_slug, out_dir, figures=None, state_dir=None):
    """Write <out_dir>/Anki_Karten.apkg. figures: {figure_id: svg_text} referenced by cards via 'figure'.
    Returns a report with counts, identities and the update delta against the previous export."""
    from anki.collection import Collection, ExportAnkiPackageOptions
    probs = {c.get('key', '?'): card_lint(c) for c in cards}
    probs = {k: v for k, v in probs.items() if v}
    if probs:
        raise ContractError(f'CARD_LINT: {json.dumps(probs, ensure_ascii=False)[:1500]}')
    keys = [c['key'] for c in cards]
    if len(keys) != len(set(keys)):
        raise ContractError('CARD_IDENTITY: duplicate semantic keys')
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    state_p = Path(state_dir or out_dir) / f'.anki-v2-state-{course_slug}-{chapter_slug}.json'
    prev = json.loads(state_p.read_text()) if state_p.exists() else {}
    stamp = max(int(time.time()), int(prev.get('last_export', 0)) + 1)
    with tempfile.TemporaryDirectory(prefix='em-anki2-') as td:
        col = Collection(str(Path(td) / 'c.anki2'))
        try:
            basic = _notetype(col, NOTE_BASIC, BASIC_FIELDS, BASIC_Q, BASIC_A)
            cloze = _notetype(col, NOTE_CLOZE, CLOZE_FIELDS, CLOZE_Q, CLOZE_A, cloze=True)
            did = col.decks.id(deck_name)
            media = []
            from .typeset import NODE
            for w in ('400', '600', '700'):
                f = NODE / f'@fontsource/source-sans-3/files/source-sans-3-latin-{w}-normal.woff2'
                if f.exists():
                    shutil.copy2(f, Path(col.media.dir()) / f'_em-sans-{w}.woff2'); media.append(f'_em-sans-{w}.woff2')
            for fid, svg in (figures or {}).items():
                name = f'em-{chapter_slug}-{slug(fid)}.svg'
                (Path(col.media.dir()) / name).write_text(svg, encoding='utf-8'); media.append(name)
            hashes = {}; gate = {'checked': 0, 'fail': {}}
            for c in cards:
                nt = cloze if c['kind'] == 'cloze' else basic
                n = col.new_note(nt)
                n.guid = guid(course_slug, chapter_slug, c['key'])
                meta = card_meta(c)
                if c['kind'] == 'cloze':
                    vals = {'Key': c['key'], 'Text': _html(c['text']), 'Extra': _html(c.get('extra', '')),
                            'Source': _html(c.get('source', '')), 'Kind': kind_html('cloze'), 'Meta': meta}
                else:
                    ctx = _html(c.get('context', ''))
                    img = (f'<img src="em-{chapter_slug}-{slug(c["figure"])}.svg" alt="{c.get("figure_alt","Abbildung")}">'
                           if c.get('figure') else '')
                    # rule C1: a figure that shows the answer belongs on the back; only figures that ARE the question go on the front
                    front_fig = c.get('figure_side') == 'front'
                    ctx += img if front_fig else ''
                    vals = {'Key': c['key'], 'Front': _html(c['front']), 'Context': ctx, 'Answer': _html(c['answer']),
                            'Explanation': ('' if front_fig else img) + _html(c.get('explanation', '')), 'Example': _html(c.get('example', '')),
                            'Pitfall': _html(c.get('pitfall', '')), 'Source': _html(c.get('source', '')),
                            'Kind': kind_html(c['kind']), 'Meta': meta}
                bad = render_lint(c, vals)
                if bad:
                    gate['fail'][c['key']] = bad
                gate['checked'] += 1
                for k, v in vals.items():
                    n[k] = v
                n.tags = [f'em::{chapter_slug}', f'em::typ::{KIND_LABEL[c["kind"]].lower()}', f'em::kognitiv::{COGNITIVE.get(c["kind"], "recall")}'] + [f'em::{t}' for t in c.get('tags', [])]
                col.add_note(n, did)
                hashes[c['key']] = hashlib.sha256(json.dumps(vals, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            if gate['fail']:
                raise ContractError('ANKI_RENDER_GATE: ' + json.dumps(gate['fail'], ensure_ascii=False)[:1500])
            col.db.execute('update notes set mod=?', stamp)
            for nt in (basic, cloze):
                nt['mod'] = stamp; col.models.update(nt, preserve_usn=True)
            pkg = out_dir / 'Anki_Karten.apkg'
            col.export_anki_package(out_path=str(pkg), options=ExportAnkiPackageOptions(
                with_scheduling=False, with_deck_configs=False, with_media=True, legacy=True), limit=None)
            notes, n_cards = col.note_count(), col.card_count()
        finally:
            col.close()
    old = prev.get('hashes', {})
    delta = {'new': sorted(set(hashes) - set(old)), 'changed': sorted(k for k in hashes if k in old and old[k] != hashes[k]),
             'unchanged': sorted(k for k in hashes if old.get(k) == hashes[k]),
             'retirement_candidates': sorted(set(old) - set(hashes)), 'automatic_deletion': False}
    write_json(state_p, {'schema': 'em-anki-v2-state', 'last_export': stamp, 'hashes': hashes,
                         'seen': sorted(set(prev.get('seen', [])) | set(hashes))})
    rep = {'package': str(pkg), 'notes': notes, 'cards': n_cards, 'media': media, 'deck': deck_name,
           'note_types': [NOTE_BASIC, NOTE_CLOZE], 'render_gate': gate,
           'kinds': {k: sum(1 for c in cards if c['kind'] == k) for k in sorted({c['kind'] for c in cards})},
           'identity': 'GUID = hash(course slug, chapter slug, semantic key)', 'update_delta': delta}
    write_json(out_dir / 'anki_report.json', rep)
    return rep


def preview_html(pkg, out_dir, limit_keys=None):
    """Render the real card HTML (Anki's own template engine) to standalone pages: light/dark × question/answer."""
    from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    from .typeset import NODE
    shutil.copy2(NODE / 'mathjax-full/es5/tex-svg-full.js', out_dir / 'tex-svg-full.js')
    pages = []
    with tempfile.TemporaryDirectory() as td:
        col = Collection(str(Path(td) / 'p.anki2'))
        try:
            col.import_anki_package(ImportAnkiPackageRequest(package_path=str(pkg), options=ImportAnkiPackageOptions()))
            for f in Path(col.media.dir()).iterdir():
                shutil.copy2(f, out_dir / f.name)
            for cid in col.db.list('select id from cards order by id'):
                card = col.get_card(cid); note = card.note()
                key = note['Key']
                if limit_keys and key not in limit_keys:
                    continue
                css = card.note_type()['css']
                for side, body in (('q', card.question()), ('a', card.answer())):
                    for mode in ('light', 'dark'):
                        cls = 'card' + (' nightMode night_mode' if mode == 'dark' else '')
                        page = (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                                f'<style>{css}</style><script>window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"]]}},svg:{{fontCache:"global"}}}};</script>'
                                f'<script src="tex-svg-full.js"></script></head><body class="{cls}">{body}</body></html>')
                        name = f'{slug(key)}-{card.ord}-{side}-{mode}.html'
                        (out_dir / name).write_text(page, encoding='utf-8'); pages.append(name)
        finally:
            col.close()
    return pages


def screenshot(pages_dir, names, out_dir, width=900, height=None):
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': width, 'height': height or 700})
        for n in names:
            pg.goto((Path(pages_dir) / n).resolve().as_uri())
            pg.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise', timeout=30000)
            pg.evaluate('MathJax.startup.promise')
            png = Path(out_dir) / (Path(n).stem + f'-{width}.png')
            pg.screenshot(path=str(png), full_page=True)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            out.append({'file': str(png), 'horizontal_overflow': sw > width})
        b.close()
    return out


def verify_package(pkg):
    """Import into a throw-away collection: counts, note types, media; the user's collection is never touched."""
    from anki.collection import Collection, ImportAnkiPackageRequest, ImportAnkiPackageOptions
    with tempfile.TemporaryDirectory() as td:
        col = Collection(str(Path(td) / 'v.anki2'))
        try:
            opts = ImportAnkiPackageOptions(merge_notetypes=False, with_scheduling=False, with_deck_configs=False)
            col.import_anki_package(ImportAnkiPackageRequest(package_path=str(pkg), options=opts))
            n1, c1 = col.note_count(), col.card_count()
            col.import_anki_package(ImportAnkiPackageRequest(package_path=str(pkg), options=opts))
            return {'notes': n1, 'cards': c1, 'reimport': col.note_count() == n1 and col.card_count() == c1,
                    'note_types': sorted(x.name for x in col.models.all_names_and_ids() if x.name.startswith('Exam Mastery')),
                    'media_missing': list(col.media.check().missing)}
        finally:
            col.close()
