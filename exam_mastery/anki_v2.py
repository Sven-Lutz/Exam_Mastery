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

CSS = r"""
@font-face{font-family:"EM Sans";src:url("_em-sans-400.woff2") format("woff2");font-weight:400}
@font-face{font-family:"EM Sans";src:url("_em-sans-600.woff2") format("woff2");font-weight:600}
@font-face{font-family:"EM Sans";src:url("_em-sans-700.woff2") format("woff2");font-weight:700}
.card{font-family:"EM Sans","Source Sans 3","Helvetica Neue","Segoe UI",Roboto,Arial,sans-serif;font-size:19px;line-height:1.5;
 color:#18212b;background:#fbfbfa;text-align:left;margin:0;padding:0}
.em{max-width:640px;margin:0 auto;padding:22px 20px 26px;border-top:5px solid #1B2A41}
.em-meta{margin-top:10px;font-size:12px;color:#7a8592;border-top:1px dashed #d5dce4;padding-top:6px}
.em-kind{display:inline-block;font-size:11px;border:1px solid #c9d6de;border-radius:2px;padding:1px 6px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#1f5673;margin-bottom:10px}
.em-q{font-size:22px;font-weight:600;line-height:1.36;color:#18212b;letter-spacing:-.005em}
.em-ctx{margin-top:12px;font-size:16.5px;color:#46525f}
.em-ctx img,.em-x img{max-width:100%;height:auto;display:block;margin:10px auto;border-radius:6px;background:#fff}
hr#answer{border:none;border-top:1px solid #d5dce4;margin:20px 0 16px}
.em-a{font-size:19px;font-weight:600;color:#18212b;border-left:5px solid #2E7D4F;background:#E5F2EA;padding:6px 10px 6px 12px;border-radius:0 6px 6px 0}
.em-x{margin-top:14px;font-size:16.5px;color:#2c3a4b}
.em-ex{margin-top:12px;font-size:16px;color:#2c3a4b;background:#fbf3e8;border-radius:6px;padding:9px 12px}
.em-pit{margin-top:12px;font-size:16px;color:#2c3a4b;border-left:4px solid #C8483A;background:#FBE9E5;padding:6px 10px 6px 12px;border-radius:0 6px 6px 0}
.em-lab{display:block;font-size:11.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#5b6878;margin-bottom:2px}
.em-src{margin-top:18px;font-size:12.5px;color:#7a8592}
.em ul,.em ol{margin:6px 0 6px;padding-left:22px}.em li{margin:3px 0}
.em table{border-collapse:collapse;width:100%;font-size:15px;margin:8px 0;display:block;overflow-x:auto}
.em th{text-align:left;border-bottom:1.5px solid #18212b;padding:4px 8px}.em td{border-bottom:1px solid #d5dce4;padding:4px 8px;vertical-align:top}
.cloze{font-weight:700;color:#1f5673}
mjx-container{overflow-x:auto;overflow-y:hidden;max-width:100%}
.nightMode.card,.night_mode.card,.card.nightMode,.card.night_mode{background:#16191d;color:#dbe2ea}
.nightMode .em-q,.night_mode .em-q,.nightMode .em-a,.night_mode .em-a{color:#e8edf2}
.nightMode .em-kind,.night_mode .em-kind{color:#8fb4dc}
.nightMode .em-ctx,.night_mode .em-ctx,.nightMode .em-x,.night_mode .em-x{color:#c3ccd5}
.nightMode .em-a,.night_mode .em-a{border-left-color:#8fb4dc}
.nightMode .em-ex,.night_mode .em-ex{background:#20262d;color:#c3ccd5}
.nightMode .em-pit,.night_mode .em-pit{color:#c3ccd5;border-left-color:#d08a62}
.nightMode hr#answer,.night_mode hr#answer{border-top-color:#2d3640}
.nightMode .em th,.night_mode .em th{border-bottom-color:#c3ccd5}.nightMode .em td,.night_mode .em td{border-bottom-color:#2d3640}
.nightMode .cloze,.night_mode .cloze{color:#8fb4dc}
.nightMode .em-ctx img,.night_mode .em-ctx img,.nightMode .em-x img,.night_mode .em-x img{background:#f6f7f9;padding:4px}
@media (max-width:480px){.card{font-size:17px}.em{padding:16px 14px 20px}.em-q{font-size:19px}.em-a{font-size:17.5px}}
"""

BASIC_Q = ('<div class="em"><div class="em-kind">{{Kind}}</div><div class="em-q">{{Front}}</div>'
           '{{#Context}}<div class="em-ctx">{{Context}}</div>{{/Context}}</div>')
BASIC_A = ('<div class="em"><div class="em-kind">{{Kind}}</div><div class="em-q">{{Front}}</div>'
           '{{#Context}}<div class="em-ctx">{{Context}}</div>{{/Context}}<hr id="answer"><div class="em-a">{{Answer}}</div>'
           '{{#Explanation}}<div class="em-x">{{Explanation}}</div>{{/Explanation}}'
           '{{#Example}}<div class="em-ex"><span class="em-lab">Beispiel</span>{{Example}}</div>{{/Example}}'
           '{{#Pitfall}}<div class="em-pit"><span class="em-lab">Typischer Denkfehler</span>{{Pitfall}}</div>{{/Pitfall}}'
           '{{#Source}}<div class="em-src">{{Source}}</div>{{/Source}}{{#Meta}}<div class="em-meta">{{Meta}}</div>{{/Meta}}</div>')
CLOZE_Q = '<div class="em"><div class="em-kind">{{Kind}}</div><div class="em-q" style="font-weight:500">{{cloze:Text}}</div></div>'
CLOZE_A = ('<div class="em"><div class="em-kind">{{Kind}}</div><div class="em-q" style="font-weight:500">{{cloze:Text}}</div>'
           '{{#Extra}}<hr id="answer"><div class="em-x">{{Extra}}</div>{{/Extra}}{{#Source}}<div class="em-src">{{Source}}</div>{{/Source}}'
           '{{#Meta}}<div class="em-meta">{{Meta}}</div>{{/Meta}}</div>')


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
    """Visible card provenance on the back: learning objective, card type rationale, difficulty, source status."""
    bits = []
    if c.get('learning_objective'):
        bits.append('Lernziel: ' + c['learning_objective'])
    if c.get('why'):
        bits.append('Warum diese Karte: ' + c['why'])
    if c.get('difficulty'):
        bits.append('Stufe: ' + DIFF.get(c['difficulty'], str(c['difficulty'])))
    if c.get('provenance'):
        bits.append({'course': 'Vorlesung', 'didactic': 'eigene Übung', 'supplement': 'Fachliteratur'}.get(c['provenance'], c['provenance']))
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
                            'Source': _html(c.get('source', '')), 'Kind': KIND_LABEL['cloze'], 'Meta': meta}
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
                            'Kind': KIND_LABEL[c['kind']], 'Meta': meta}
                bad = render_lint(c, vals)
                if bad:
                    gate['fail'][c['key']] = bad
                gate['checked'] += 1
                for k, v in vals.items():
                    n[k] = v
                n.tags = [f'em::{chapter_slug}', f'em::typ::{KIND_LABEL[c["kind"]].lower()}'] + [f'em::{t}' for t in c.get('tags', [])]
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
