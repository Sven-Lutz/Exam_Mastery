"""Professional typesetting of the learning products (B9).

One design system, five separate documents per chapter, each with its own cover and its own page numbering:
  1_Lehrbuch (textbook), 2_Arbeitsbuch (workbook), 3_Musterloesungen (worked solutions),
  4_Probeklausur (mock exam, questions only), 5_Probeklausur_Loesungen (exam solutions with rubrics).
Plus kapitel.html (the textbook for screens).

Input is a book model (em-book-v1, see `book_from_ast`). Math is TeX (\\( \\) and \\[ \\]) typeset by MathJax inside
Chromium; figures are SVG from `figures_svg`. The table of contents gets real page numbers in a second pass, and the
PDF gets bookmarks. Nothing here decides content; it only lays it out, and it refuses inconsistent exams.
"""
import html
import json
import math
import re
import shutil
from pathlib import Path

from .common import ContractError
from . import figures_svg

E = html.escape

# Print geometry (A4, margins as in _pdf): the body measure beside the side-note column, and the full text block.
PX_PER_MM = 96 / 25.4
MEASURE_PX = (210 - 20 - 16 - 43 - 7) * PX_PER_MM      # main column (side column + gap reserved)
WIDE_PX = (210 - 20 - 16 - 6) * PX_PER_MM               # full text block, minus a safety margin for nested boxes
FIGURE_LABEL_FLOOR_PT = 6.4                              # print gate PG-FONT-FLOOR is 6 pt; keep a margin
_VIEWBOX = re.compile(r'<svg\b[^>]*\bviewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)')
_FONT_ATTR = re.compile(r'(font-size=")([\d.]+)(")')
_FONT_CSS = re.compile(r'(font-size:\s*)([\d.]+)(px)?(?=[;"\s}])')


def _label_pt(size, width, avail):
    return size * min(1.0, avail / width) * 0.75


def fit_figure_labels(svg):
    """Keep every SVG label at or above the print floor once the figure is scaled to the page.

    A figure wider than the body measure is scaled down by the browser, and its labels with it. First choice: let
    the figure use the full text block (print class ``wide``, into the side-note column, which figure blocks never
    use). Only if that is not enough are the remaining too-small font sizes raised to the floor; nothing else changes.
    Returns (svg, wide)."""
    m = _VIEWBOX.search(svg)
    sizes = [float(x[1]) for x in _FONT_ATTR.findall(svg)] + [float(x[1]) for x in _FONT_CSS.findall(svg)]
    if not m or not sizes:
        return svg, False
    width = float(m.group(1))
    smallest = min(sizes)
    if _label_pt(smallest, width, MEASURE_PX) >= FIGURE_LABEL_FLOOR_PT:
        return svg, False
    wide = width > MEASURE_PX
    avail = WIDE_PX if wide else MEASURE_PX
    if _label_pt(smallest, width, avail) >= FIGURE_LABEL_FLOOR_PT:
        return svg, wide
    floor = FIGURE_LABEL_FLOOR_PT / (0.75 * min(1.0, avail / width))

    def lift(mm):
        v = float(mm.group(2))
        return mm.group(0) if v >= floor else f"{mm.group(1)}{math.ceil(floor * 100) / 100:g}{mm.group(3) or ''}"
    return _FONT_CSS.sub(lift, _FONT_ATTR.sub(lift, svg)), wide
NODE = Path.home() / '.cache/exam-mastery-v05-node/node_modules'
FONTS = [('Source Serif 4', 'source-serif-4', ['400-normal', '400-italic', '600-normal', '700-normal']),
         ('Source Sans 3', 'source-sans-3', ['400-normal', '400-italic', '600-normal', '700-normal']),
         ('JetBrains Mono', 'jetbrains-mono', ['400-normal'])]
PROV = {'course': 'Vorlesung', 'supplement': 'Fachliche Ergänzung', 'didactic': 'Didaktisches Beispiel (selbst entworfen)',
        'interpretation': 'Einordnung (nicht aus der Vorlesung)', 'unconfirmed': 'Nicht bestätigt',
        'derivation': 'Eigene Herleitung (rechnerisch geprüft)', 'vision': 'Abbildung der Vorlesung (vom Agenten ausgewertet)'}
BOX = {'note': 'Hinweis', 'research': 'Forschungskontext', 'law': 'Rechtslage', 'pitfall': 'Typischer Fehler', 'key': 'Kernaussage', 'remark': 'Anmerkung',
       'limit': 'Modellgrenze', 'question': 'Leitfrage'}


# ------------------------------------------------------------------ inline markup

MATH = re.compile(r'(\\\[.+?\\\]|\\\(.+?\\\))', re.S)


def _mt(s):
    """Lab texts use the lab notation V_k, V^π (labs.build.MT): escaped text with real sub-/superscripts."""
    from .labs.build import MT
    return MT(s)


# bare notation the author wrote without \\( \\): V_2, V_{k+1}, V^{π_neu}, γ^k (single-letter base, not snake_case)
_BARE = re.compile(r'(?<![\w\\])([A-Za-z\u0391-\u03a9\u03b1-\u03c9])([_^])(\{[^{}]*\}|-?\d+|[A-Za-z\u03b1-\u03c9*\u2032]{1,3})(?![\w{])')


def _bare(p):
    def one(m):
        tag = 'sub' if m[2] == '_' else 'sup'
        inner = m[3][1:-1] if m[3].startswith('{') else m[3]
        return f'{m[1]}<{tag}>{_bare(inner)}</{tag}>'
    return _BARE.sub(one, p)


def inline(s):
    """Text with \\(..\\)/\\[..\\] math, **bold**, *italic*, `code`. Math and code are held as placeholders so
    markup can span a formula (\"**Lesarten von \\(\\gamma\\)**\" used to leave the asterisks visible)."""
    keep = []
    def hold(x):
        keep.append(x); return f'\x02{len(keep) - 1}\x03'
    t = MATH.sub(lambda m: hold(E(m[0], quote=False)), str(s or ''))
    t = re.sub(r'`([^`]+)`', lambda m: hold(f'<code>{E(m[1], quote=False)}</code>'), t)
    t = E(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = _bare(t)
    return re.sub(r'\x02(\d+)\x03', lambda m: keep[int(m[1])], t)


def md(s):
    """Paragraphs, '- ' bullets, '1. ' numbered lists, display math on its own line."""
    s = str(s or '').strip()
    code = []
    def keep(m):                       # fenced code blocks are kept verbatim
        code.append(m.group(2)); return f'\n\n\x00CODE{len(code) - 1}\x00\n\n'
    s = re.sub(r'```(\w*)\n(.*?)```', keep, s, flags=re.S)
    blocks, out = re.split(r'\n\s*\n', s), []
    for b in blocks:
        lines = [l.rstrip() for l in b.split('\n') if l.strip()]
        if not lines:
            continue
        if len(lines) == 1 and re.fullmatch(r'\x00CODE(\d+)\x00', lines[0].strip()):
            out.append(f'<pre class="code"><code>{E(code[int(lines[0].strip()[5:-1])])}</code></pre>')
        elif all(l.strip().startswith('|') for l in lines):
            rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines if not re.fullmatch(r'\|?[\s:|-]+\|?', l.strip())]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>'
                       + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:]) + '</tbody></table>')
        elif all(re.match(r'\s*[-•] ', l) for l in lines):
            out.append('<ul>' + ''.join(f'<li>{inline(re.sub(r"^\s*[-•] ", "", l))}</li>' for l in lines) + '</ul>')
        elif all(re.match(r'\s*\d+[.)] ', l) for l in lines):
            out.append('<ol>' + ''.join(f'<li>{inline(re.sub(r"^\s*\d+[.)] ", "", l))}</li>' for l in lines) + '</ol>')
        elif len(lines) == 1 and lines[0].strip().startswith('\\[') and lines[0].strip().endswith('\\]'):
            out.append(f'<div class="dmath">{E(lines[0].strip(), quote=False)}</div>')
        else:
            out.append('<p>' + inline(' '.join(lines)) + '</p>')
    return ''.join(out)


# ------------------------------------------------------------------ design system

def font_css(rel):
    out = []
    for fam, pkg, variants in FONTS:
        for v in variants:
            w, st = v.split('-')
            out.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};"
                       f"src:url('{rel}/{pkg}-latin-{v}.woff2') format('woff2')}}")
    return ''.join(out)


CSS = r"""
/* Exam Mastery book design v0.20 "Folio": text column + side column (sources, provenance, glosses), numbered
   definitions/examples/figures, calm ink + one cool accent + one warm accent. Print first; the same HTML reads on screen. */
:root{--ink:#18212b;--ink2:#36424f;--muted:#66717d;--line:#d9dee4;--hair:#e9ecef;--soft:#f5f6f4;--paper:#ffffff;
 --accent:#1f5673;--accent-soft:#e8f0f4;--warm:#a8641c;--warm-soft:#fbf3e8;--warn:#9b3d23;--warn-soft:#f9ece7;--ok:#3d6b4f;
 --serif:'Source Serif 4','Iowan Old Style',Georgia,serif;--sans:'Source Sans 3','Helvetica Neue',Arial,sans-serif;
 --mono:'JetBrains Mono',Menlo,monospace;--side:43mm;--gap:7mm}
*{box-sizing:border-box}
html{font-size:10.4pt}
body{margin:0;color:var(--ink);background:var(--paper);font-family:var(--serif);line-height:1.5;font-kerning:normal;
 font-variant-numeric:oldstyle-nums proportional-nums;hyphens:auto;-webkit-hyphens:auto;text-rendering:optimizeLegibility}
main{padding-right:calc(var(--side) + var(--gap))}
h1,h2,h3,h4,.sans{font-family:var(--sans);font-variant-numeric:lining-nums}
h1{font-size:2.1rem;line-height:1.12;margin:0 0 .4em;font-weight:700;letter-spacing:-.012em}
h2{font-size:1.5rem;line-height:1.2;margin:2.2em 0 .7em;font-weight:700;break-after:avoid;position:relative;letter-spacing:-.005em}
h2 .no{color:var(--accent);font-weight:700;margin-right:.5em}
h2::after{content:'';display:block;width:14mm;height:2.5px;background:var(--accent);margin-top:.35em}
h3{font-size:1.1rem;margin:1.7em 0 .45em;break-after:avoid;font-weight:600;color:var(--ink)}
h3 .no{color:var(--muted);font-weight:600;margin-right:.45em}
h4{font-size:.98rem;margin:1.1em 0 .3em;break-after:avoid;font-weight:600}
p{margin:0 0 .7em;orphans:3;widows:3}
ul,ol{margin:.2em 0 .8em;padding-left:1.3em}li{margin:.2em 0}li::marker{color:var(--muted)}
strong{font-weight:600}
a{color:var(--accent)}
pre.code{font-family:var(--mono);font-size:.8rem;line-height:1.45;background:var(--soft);border-radius:3px;padding:.7em .9em;overflow-x:auto;break-inside:avoid;white-space:pre}
code{font-family:var(--mono);font-size:.86em;background:var(--soft);padding:.05em .3em;border-radius:3px}
.dmath{margin:.8em 0 1em;text-align:center;overflow-x:auto}
/* B22: a display formula wider than its box (theorem/definition boxes are narrower than the text) is scaled to fit
   instead of running across the box border in print */
mjx-container[display="true"]{display:block;max-width:100%}mjx-container[display="true"]>svg{max-width:100%;height:auto}
/* side column */
.blk{position:relative}
.blk::after{content:'';display:table;clear:both}
.side,.src{float:right;clear:right;width:var(--side);margin-right:calc(-1 * (var(--side) + var(--gap)));margin-top:.2em;
 font-family:var(--sans);font-size:.72rem;line-height:1.38;color:var(--muted);font-variant-numeric:lining-nums;hyphens:none;text-align:left}
.side .prov,.src b{display:block;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:.64rem;margin-bottom:.15em}
.prov.course{color:var(--accent)}.prov.supplement{color:var(--ok)}.prov.didactic{color:var(--warm)}.prov.interpretation,.prov.vision,.prov.unconfirmed{color:var(--muted)}
.side .ref{display:block;margin-top:.15em}
.lead{font-size:1.08rem;line-height:1.55;color:var(--ink2)}
/* chapter opener */
.opener{break-after:page;padding-top:8mm}
.opener .chno{font:700 5.2rem/1 var(--sans);color:var(--accent);letter-spacing:-.03em}
.opener h1{font-size:2.5rem;margin:.15em 0 .5em;max-width:16em}
.opener .goals{border-top:1px solid var(--ink);padding-top:.8em;margin-top:1.4em}
.opener .goals h4,.opener .road h4{margin:0 0 .5em;font-size:.75rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.opener .goals ol{columns:1;padding-left:1.4em}.opener .goals li{margin:.3em 0}
.opener .road{margin-top:1.4em;display:grid;grid-template-columns:repeat(3,1fr);gap:.4em 1.2em;font-family:var(--sans);font-size:.86rem}
.opener .road div{border-top:1px solid var(--line);padding-top:.35em}.opener .road b{color:var(--accent);margin-right:.35em}
/* semantic blocks */
.def,.box,.ex,.mis,.case,.sum{break-inside:avoid-page;margin:1.1em 0 1.2em}
.ex{break-inside:auto}.ex>h4,.ex>.lab,.ex>.given{break-after:avoid}.ex ol.steps>li,.ex .res{break-inside:avoid}
.keephead,.ex-intro{break-inside:avoid-page}
.ex ol.steps.continued{counter-reset:s 1}
.lab{font-family:var(--sans);font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3em}
.def{background:var(--accent-soft);border-top:2px solid var(--accent);padding:.6em .95em .3em}
.def .lab{color:var(--accent)}
.def .term{font-family:var(--sans);font-weight:700;color:var(--ink);margin-right:.35em}
.box{background:var(--soft);padding:.6em .95em .35em;border-left:3px solid var(--line)}
.box.law{border-left-color:var(--warm);background:var(--warm-soft)}.box.law .lab{color:var(--warm)}
.box.pitfall,.box.limit{border-left-color:var(--warn);background:var(--warn-soft)}.box.pitfall .lab,.box.limit .lab{color:var(--warn)}
.box.key{border-left-color:var(--ink);background:#fff;border:1px solid var(--ink);border-left-width:3px}
.box.research{border-left-color:var(--ok);background:#f1f6f2}.box.research .lab{color:var(--ok)}
.ex{border-top:2px solid var(--warm);border-bottom:1px solid var(--line);padding:.55em 0 .35em}
.ex>.lab{color:var(--warm)}
.ex h4{margin:.05em 0 .45em;font-size:1.02rem}
.ex .given{background:var(--warm-soft);padding:.5em .8em;border-radius:2px;margin:.3em 0 .7em}
.ex .given p:last-child{margin-bottom:0}
.ex ol.steps{counter-reset:s;list-style:none;padding-left:0;margin:.4em 0}
/* B22: wrapping row instead of a fixed grid - a formula wider than its column pushes the reason onto its own line
   (the fixed grid let MathJax SVG overflow into the reason column, e.g. Bellman derivation steps) */
.ex ol.steps>li{counter-increment:s;display:flex;flex-wrap:wrap;align-items:baseline;column-gap:1em;padding:.38em 0;border-top:1px solid var(--hair)}
.ex ol.steps>li:first-child{border-top:none}
.ex ol.steps>li::before{content:counter(s);flex:0 0 1.7em;font:700 .78rem/1.6 var(--sans);color:var(--warm)}
.ex ol.steps>li .why{display:block;flex:1 1 13em;color:var(--muted);font-size:.88em;font-family:var(--sans);line-height:1.4}
.ex ol.steps>li>.do{flex:1.45 1 auto;max-width:100%}
.ex .res{border-top:1px solid var(--ink);padding-top:.45em;margin-top:.4em}
.ex .res::before{content:'Ergebnis';font:700 .7rem var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--ink);display:block;margin-bottom:.2em}
.mis{display:grid;grid-template-columns:1fr 1fr;gap:.2em 1.4em;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:.55em 0}
.mis .lab{grid-column:1/3}
.mis .wrong::before{content:'Fehlvorstellung'}.mis .right::before{content:'Richtig ist'}
.mis .wrong::before,.mis .right::before{display:block;font:600 .8rem var(--sans);margin-bottom:.15em}
.mis .wrong{color:var(--ink2)}.mis .wrong::before{color:var(--warn)}.mis .right::before{color:var(--ok)}
.mis .why{grid-column:1/3;color:var(--muted);font-size:.95em}
.case{border-left:3px solid var(--muted);padding:.2em 0 .1em .95em}
.sum{border-top:2px solid var(--ink);border-bottom:2px solid var(--ink);padding:.6em 0 .2em}
.sum .lab{color:var(--ink)}
figure{margin:1.3em 0 1.4em;break-inside:avoid}
@media print{figure.wide{margin-right:calc(-1 * (var(--side) + var(--gap)))}}
figure .fig{text-align:center}
figure .fig svg{max-width:100%}
figcaption,.tcap{font-family:var(--sans);font-size:.8rem;color:var(--ink2);margin-top:.5em;line-height:1.42}
figcaption b,.tcap b{color:var(--accent);margin-right:.3em}
.twrap{overflow-x:auto;margin:1em 0 1.2em;break-inside:avoid}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:.85rem;font-variant-numeric:lining-nums tabular-nums}
th{text-align:left;font-weight:600;border-bottom:1.5px solid var(--ink);padding:.32em .5em;vertical-align:bottom;hyphens:none;-webkit-hyphens:none}
td{hyphens:manual;-webkit-hyphens:manual}
td{border-bottom:1px solid var(--hair);padding:.3em .5em;vertical-align:top}
td.num,th.num{text-align:right}td.num{white-space:nowrap}
tr.total td{border-top:1.5px solid var(--ink);font-weight:600}
tr.neg td.num{color:var(--warn)}
.tcap{margin:0 0 .35em}
/* cover & toc */
.cover{height:252mm;display:flex;flex-direction:column;justify-content:space-between;padding:6mm 0 0}
.cover .band{height:3px;background:var(--accent);width:100%}
.cover .kicker{font:600 .82rem var(--sans);letter-spacing:.16em;text-transform:uppercase;color:var(--accent);margin-top:28mm}
.cover h1{font-size:3.1rem;margin:.25em 0 .2em;max-width:13em}
.cover .sub{font:400 1.3rem var(--sans);color:var(--ink2)}
.cover .rule{height:1px;background:var(--ink);width:100%;margin:1.4em 0}
.cover .meta{font:400 .8rem var(--sans);color:var(--muted);line-height:1.55;border-top:1px solid var(--line);padding-top:.8em;max-width:150mm}
.toc{break-after:page}
.toc h2::after{display:none}
.toc a{color:inherit;text-decoration:none;display:flex;gap:.4em}
.toc .e{display:flex;align-items:baseline;margin:.3em 0;font-family:var(--sans)}
.toc .e.l1{font-weight:600;margin-top:.7em}
.toc .e.l2{padding-left:1.8em;font-size:.93em;color:var(--ink2)}
.toc .e .t{flex:0 1 auto}.toc .e .d{flex:1 1 auto;border-bottom:1px dotted #a6afb8;margin:0 .4em;transform:translateY(-.3em)}
.toc .e .pg{flex:0 0 auto;font-variant-numeric:lining-nums}
/* workbook */
.item{break-inside:avoid-page;margin:0 0 1.5em}
.item .head{font-family:var(--sans);display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid var(--ink);margin-bottom:.45em;padding-bottom:.1em}
.item .head .id{font-weight:700}.item .head .meta{font-size:.76rem;color:var(--muted);font-variant-numeric:lining-nums}
.item .head .meta .op{display:inline-block;border:1px solid var(--line);border-radius:2px;padding:0 .35em;margin-right:.4em;color:var(--ink2);text-transform:uppercase;letter-spacing:.06em;font-size:.68rem}
.space{border:1px solid var(--line);border-radius:2px;background:repeating-linear-gradient(transparent,transparent 7.4mm,#e9ecef 7.4mm,#e9ecef 7.55mm);margin:.5em 0 0}
.scaffold{counter-reset:s;list-style:none;padding:0;margin:.5em 0}
.scaffold li{counter-increment:s;display:grid;grid-template-columns:1.6em 1fr;padding:.3em 0;border-top:1px solid var(--hair)}
.scaffold li::before{content:counter(s);font:700 .78rem/1.6 var(--sans);color:var(--warm)}
.scaffold .blank{display:inline-block;min-width:26mm;border-bottom:1px solid var(--ink);height:1.1em;vertical-align:baseline}
.stage{break-before:page}.stage.first{break-before:auto}
.stage .intro{font-family:var(--sans);font-size:.88rem;color:var(--ink2);border-left:3px solid var(--accent);padding-left:.8em;margin-bottom:1.2em}
.rub td:last-child,.rub th:last-child{text-align:right;width:5em;white-space:nowrap;hyphens:none}
.hint{font-family:var(--sans);font-size:.85rem;color:var(--muted)}
.alt{border-left:3px solid var(--accent);padding-left:.8em;margin:.6em 0}
.examhead{border:1.5px solid var(--ink);padding:.7em 1em;font-family:var(--sans);margin-bottom:1.2em}
.examhead table{font-size:.9rem}.examhead td{border:none;padding:.15em .4em}
.namefield{display:grid;grid-template-columns:1fr 1fr;gap:1em;margin:0 0 1.2em;font-family:var(--sans);font-size:.85rem}
.namefield div{border-bottom:1px solid var(--ink);padding-top:1.6em;color:var(--muted)}
.exam .item .head{border-bottom-width:2px}
.ptsbox{float:right;border:1.5px solid var(--ink);font-family:var(--sans);font-size:.8rem;padding:.15em .5em;margin-left:1em}
@page{size:A4;margin:22mm 16mm 22mm 20mm}
@media print{a{color:inherit;text-decoration:none}main{max-width:none}}
@media screen{body{background:#f7f7f5}main{max-width:62rem;margin:0 auto;padding:2.5em 1.5em 5em;padding-right:calc(var(--side) + var(--gap) + 1.5em);background:#fff}
 .cover{height:auto;min-height:70vh}}
@media screen and (max-width:760px){main{padding-right:1.2em}.side,.src{float:none;width:auto;margin:.2em 0 .6em}.opener .road{grid-template-columns:1fr}
 .ex ol.steps>li .why{flex-basis:100%;padding-left:2.7em}}
@media screen and (prefers-color-scheme:dark){body{background:#12171c;color:#dde3e9}main{background:#171d23}
 :root{--ink:#dde3e9;--ink2:#c3ccd5;--muted:#9aa6b2;--line:#2e3740;--hair:#252d35;--soft:#1d242b;--accent:#8cc0dc;--accent-soft:#1a2a33;--warm:#e0a660;--warm-soft:#2a2219;--warn:#e08b70;--warn-soft:#2c1d18}
 .lead{color:#c9d2db}figure svg{background:#f6f7f9;border-radius:6px;padding:4px}.box.key{background:transparent}.box.research{background:#18241c}}
"""


# ------------------------------------------------------------------ blocks

class Doc:
    def __init__(self, book, kind):
        self.book, self.kind = book, kind
        self.fig_no, self.tab_no, self.toc = 0, 0, []
        self.def_no, self.ex_no = 0, 0

    def side(self, b):
        """Side-column note: provenance label, source anchor and (for supplements) literature references."""
        prov = b.get('prov')
        if not prov and not b.get('src') and not b.get('refs'):
            return ''
        lab = PROV.get(prov, '')
        out = f'<span class="prov {E(prov or "")}">{E(lab)}</span>' if lab else ''
        if b.get('src'):
            out += f'<span class="ref">{E(b["src"])}</span>'
        for r in b.get('refs') or []:
            out += f'<span class="ref">{inline(r)}</span>'
        return f'<aside class="side">{out}</aside>'

    def src(self, b):
        return self.side(b)

    def _capsrc(self, b):
        lab = PROV.get(b.get('prov'), '')
        # engine-internal module paths are not a reader's source: shown as "eigenes, getestetes Referenzmodell"
        refs = [('Eigenes, getestetes Referenzmodell' if 'exam_mastery/' in str(x) else x) for x in [*str(b.get('src') or '').split('; '), *(b.get('refs') or [])]]
        bits = list(dict.fromkeys(x for x in [lab, *refs] if x))
        return f' <span style="color:var(--muted)">({inline("; ".join(bits))})</span>' if bits else ''

    def figure(self, b):
        spec = self.book['figures'][b['id']]
        self.fig_no += 1
        svg, wide = fit_figure_labels(figures_svg.render(spec))
        cap = f'<b>Abbildung {self.book["meta"]["chapter_no"]}.{self.fig_no}</b> {inline(b.get("caption") or spec.get("caption") or spec.get("title", ""))}'
        return f'<figure id="fig-{E(b["id"])}"{" class=\"wide\"" if wide else ""}><div class="fig">{svg}</div><figcaption>{cap}{self._capsrc(b)}</figcaption></figure>'

    def table(self, b):
        self.tab_no += 1
        cols = b['columns']; num = set(b.get('numeric') or [])
        head = ''.join(f'<th class="{"num" if i in num else ""}">{inline(c)}</th>' for i, c in enumerate(cols))
        rows = ''
        for r in b['rows']:
            total = isinstance(r, dict) and r.get('total')
            cells = r['cells'] if isinstance(r, dict) else r
            rows += f'<tr class="{"total" if total else ""}{" neg" if isinstance(r, dict) and r.get("neg") else ""}">' + ''.join(
                f'<td class="{"num" if i in num else ""}">{inline(c)}</td>' for i, c in enumerate(cells)) + '</tr>'
        cap = f'<div class="tcap"><b>Tabelle {self.book["meta"]["chapter_no"]}.{self.tab_no}</b> {inline(b.get("caption", ""))}</div>'
        return f'<div class="twrap">{cap}<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>{("<div class=\"tcap\" style=\"margin-top:.35em\">" + self._capsrc(b) + "</div>") if self._capsrc(b) else ""}</div>'

    def block(self, b):
        """Every block is wrapped with its side note first, so the note floats beside the block's first line."""
        h = self._block(b)
        side = '' if b['type'] in ('figure', 'table', 'lab', 'lead', 'summary', 'misconception') else self.side(b)
        return f'<div class="blk">{side}{h}</div>'

    def _block(self, b):
        t = b['type']
        if t == 'text':
            return md(b['md'])
        if t == 'lead':
            return f'<div class="lead">{md(b["md"])}</div>'
        if t == 'definition':
            self.def_no += 1
            body = md(b["md"])
            return (f'<div class="def"><span class="lab">Definition {self.book["meta"]["chapter_no"]}.{self.def_no}</span>'
                    f'<span class="term">{inline(b["term"])}</span>{body[3:] if body.startswith("<p>") else body}</div>')
        if t == 'box':
            return f'<div class="box {E(b.get("kind","note"))}"><span class="lab">{E(b.get("title") or BOX.get(b.get("kind"), "Hinweis"))}</span>{md(b["md"])}</div>'
        if t == 'example':
            self.ex_no += 1
            step_parts = [f'<li><span class="do">{inline(s[0])}</span>' + (f'<span class="why">{inline(s[1])}</span>' if len(s) > 1 and s[1] else '') + '</li>'
                            for s in b['steps']]
            tab = self.table(b['table']) if b.get('table') else ''
            fig = self.figure({'id': b['figure']}) if b.get('figure') else ''
            return (f'<div class="ex"><div class="ex-intro"><span class="lab">{E(b.get("kind_label", "Beispiel"))} {self.book["meta"]["chapter_no"]}.{self.ex_no} · {E(b.get("label", "Durchgerechnet"))}</span><h4>{inline(b["title"])}</h4>'
                    f'<div class="given">{md(b["given"])}</div>{tab}<ol class="steps">{"".join(step_parts[:1])}</ol></div>'
                    + (f'<ol class="steps continued">{"".join(step_parts[1:])}</ol>' if len(step_parts) > 1 else '')
                    + (f'<div class="res">{md(b["result"])}</div>' if b.get('result') else '') + f'{fig}</div>')
        if t == 'table':
            return self.table(b)
        if t == 'figure':
            return self.figure(b)
        if t == 'lab':  # B13: static state of an interactive lab (PDF/print); the HTML links to the lab itself
            self.fig_no += 1
            cap = (f'<b>Abbildung {self.book["meta"]["chapter_no"]}.{self.fig_no}</b> {inline(b["title"])}{"" if b["title"].rstrip().endswith(("?", "!", ".")) else "."} {inline(b.get("caption", ""))} '
                   f'<i>Interaktiv</i> in der Lernumgebung (<a href="{E(b["href"])}">Lab öffnen</a>). Modellannahmen: {_mt(" ".join(a.rstrip(".") + "." for a in b.get("assumptions", [])))}')
            svg, wide = fit_figure_labels(b["svg"])
            return f'<figure class="lab-fig{" wide" if wide else ""}"><div class="fig">{svg}</div><figcaption>{cap}{self._capsrc(b)}</figcaption></figure>'
        if t == 'misconception':
            return (f'<div class="mis"><span class="lab">Häufige Fehlvorstellung</span><div class="wrong">{md(b["wrong"])}</div>'
                    f'<div class="right">{md(b["right"])}</div>' + (f'<div class="why">{md(b["why"])}</div>' if b.get('why') else '') + '</div>')
        if t == 'case':
            return f'<div class="case"><span class="lab">{E(b.get("label","Fall"))}</span><h4>{inline(b["title"])}</h4>{md(b["md"])}</div>'
        if t == 'summary':
            return f'<div class="sum"><span class="lab">{E(b.get("title","Zusammenfassung"))}</span>{md(b["md"])}</div>'
        raise ContractError(f'unknown book block type {t!r}')


# ------------------------------------------------------------------ documents

def _cover(book, product, sub, extra=''):
    m = book['meta']
    return (f'<section class="cover"><div><div class="band"></div><div class="kicker">{E(m["course"])} · Kapitel {E(str(m["chapter_no"]))}</div>'
            f'<h1>{E(m["title"])}</h1><div class="sub">{E(product)}</div><div class="rule"></div>'
            f'<div class="sub" style="font-size:1rem">{E(sub)}</div>{extra}</div>'
            f'<div class="meta">{inline(m["status_line"])}<br>Stand {E(m["date"])} · Exam Mastery {E(m["engine"])}'
            f'{("<br>" + inline(m["lecturer_line"])) if m.get("lecturer_line") else ""}</div></section>')


def _toc(entries, title='Inhalt'):
    rows = ''.join(f'<div class="e l{lv}"><a href="#{E(i)}"><span class="t">{inline(t)}</span></a><span class="d"></span>'
                   f'<span class="pg" data-for="{E(i)}">00</span></div>' for lv, i, t in entries)
    return f'<section class="toc"><h2>{E(title)}</h2>{rows}</section>'


def _page(title, body, assets='assets'):
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title><style>{font_css(assets + "/fonts")}{CSS}</style>'
            '<script>window.MathJax={tex:{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]]},'
            'svg:{fontCache:"global"},startup:{typeset:true}};</script>'
            f'<script src="{assets}/tex-svg-full.js"></script></head><body><main>{body}</main></body></html>')


OPS = {'RECALL': 'wiedergeben', 'EXPLAIN': 'erklären', 'CALCULATE': 'berechnen', 'APPLY': 'anwenden', 'ANALYZE': 'analysieren',
       'EVALUATE': 'beurteilen', 'COMPARE': 'vergleichen', 'DESIGN': 'entwerfen', 'CRITIQUE': 'kritisch prüfen', 'DERIVE': 'herleiten',
       'INTERPRET': 'interpretieren', 'CLASSIFY': 'einordnen', 'DIAGNOSE': 'Fehler finden', 'TRANSFER': 'übertragen'}


def _opener(book):
    """Chapter opener: number, title, learning objectives and a section roadmap (only when objectives are declared)."""
    m = book['meta']; goals = book.get('objectives') or []
    if not goals:
        return ''
    road = ''.join(f'<div><b>{m["chapter_no"]}.{i}</b>{inline(s_["title"])}</div>' for i, s_ in enumerate(book['sections'], 1))
    return (f'<section class="opener"><div class="chno">{E(str(m["chapter_no"]))}</div><h1>{inline(m["title"])}</h1>'
            + (f'<div class="lead">{md(book["opener_lead"])}</div>' if book.get('opener_lead') else '')
            + f'<div class="goals"><h4>Nach diesem Kapitel können Sie</h4><ol>' + ''.join(f'<li>{inline(g)}</li>' for g in goals) + '</ol></div>'
            + f'<div class="road">{road}</div></section>')


def textbook(book):
    d = Doc(book, 'textbook'); m = book['meta']; parts, toc = [], []
    head = []   # headings waiting for their first block: printed together, so no heading ends a page alone
    def emit(html_):
        if head:
            parts.append('<div class="keephead">' + ''.join(head) + html_ + '</div>'); head.clear()
        else:
            parts.append(html_)
    for si, sec in enumerate(book['sections'], 1):
        sid = f's{si}'; toc.append((1, sid, f'{m["chapter_no"]}.{si}\u2002{E(sec["title"])}'))
        head.append(f'<h2 id="{sid}"><span class="no">{m["chapter_no"]}.{si}</span>{inline(sec["title"])}</h2>')
        for sj, sub in enumerate(sec.get('subsections') or [{'title': None, 'blocks': sec.get('blocks', [])}], 1):
            if sub.get('title'):
                ssid = f's{si}-{sj}'; toc.append((2, ssid, f'{m["chapter_no"]}.{si}.{sj}\u2002{E(sub["title"])}'))
                head.append(f'<h3 id="{ssid}"><span class="no">{m["chapter_no"]}.{si}.{sj}</span>{inline(sub["title"])}</h3>')
            for b in sub['blocks']:
                emit(d.block(b))
    if head:
        parts.append(''.join(head)); head.clear()
    back = []
    if book.get('glossary'):
        toc.append((1, 'glossar', 'Begriffe und Symbole'))
        back.append('<h2 id="glossar">Begriffe und Symbole</h2><div class="twrap"><table><thead><tr><th>Begriff / Symbol</th><th>Bedeutung</th></tr></thead><tbody>'
                    + ''.join(f'<tr><td><b>{inline(a)}</b></td><td>{inline(b)}</td></tr>' for a, b in book['glossary']) + '</tbody></table></div>')
    if book.get('references'):
        toc.append((1, 'quellen', 'Quellen'))
        back.append('<h2 id="quellen">Quellen</h2>' + ''.join(f'<h4>{E(g)}</h4><ul>' + ''.join(f'<li>{inline(r)}</li>' for r in refs) + '</ul>'
                                                          for g, refs in book['references']))
    if book.get('production_notes'):
        toc.append((1, 'entstehung', 'Anhang: Entstehung und Qualitätsstatus'))
        back.append('<section class="keephead"><h2 id="entstehung">Anhang: Entstehung und Qualitätsstatus</h2>' + md(book['production_notes']) + '</section>')
    body = _cover(book, 'Lehrbuch', m.get('subtitle', '')) + _toc(toc) + _opener(book) + ''.join(parts) + ''.join(back)
    return body, toc


def _item_html(d, it, solution=False, space=True, exam=False):
    meta = ([] if exam or it.get('stage_label') in ('exam', 'recall', 'guided', 'standard', 'transfer') else [it.get('stage_label', '')]) + ([f'≈ {it["minutes"]:g} Min.'] if it.get('minutes') else []) + ([f'{it["points"]:g} P.'] if it.get('points') else [])
    op = OPS.get(it.get('operation') or '', '')
    h = (f'<div class="item" id="{E(it["id"])}"><div class="head"><span class="id">{"Aufgabe " + E(it["no"])}{(" · " + inline(it["title"])) if it.get("title") else ""}</span>'
         f'<span class="meta">{f"<span class=op>{E(op)}</span>" if op else ""}{E(" · ".join(x for x in meta if x))}</span></div>{md(it["prompt"])}')
    if it.get('figure'):
        h += d.figure({'id': it['figure']})
    if it.get('table'):
        h += d.table(it['table'])
    if it.get('scaffold') and not solution:
        h += '<ol class="scaffold">' + ''.join(f'<li><span>{inline(x).replace("___", "<span class=blank></span>")}</span></li>' for x in it['scaffold']) + '</ol>'
    if not solution and space and it.get('space'):
        h += f'<div class="space" style="height:{float(it["space"]):.0f}mm"></div>'
    if solution:
        s = it['solution']
        if s.get('approach'):
            h += f'<h4>Lösungsidee</h4>{md(s["approach"])}'
        if s.get('steps'):
            h += '<div class="ex" style="border:none;padding:0"><ol class="steps">' + ''.join(
                f'<li><span class="do">{inline(x[0])}</span>' + (f'<span class="why">{inline(x[1])}</span>' if len(x) > 1 and x[1] else '') + '</li>' for x in s['steps']) + '</ol></div>'
        h += f'<div class="box key"><span class="lab">Ergebnis</span>{md(s["answer"])}</div>'
        for alt in s.get('alternatives') or []:
            h += f'<div class="alt"><span class="lab">Alternativer Lösungsweg</span>{md(alt)}</div>'
        if s.get('errors'):
            h += '<h4>Typische Fehler und ihre Diagnose</h4><ul>' + ''.join(f'<li>{inline(e)}</li>' for e in s['errors']) + '</ul>'
        if s.get('rubric'):
            tot = sum(r[1] for r in s['rubric'])
            h += ('<h4>Bewertung</h4><div class="twrap"><table class="rub"><thead><tr><th>Kriterium</th><th>Punkte</th></tr></thead><tbody>'
                  + ''.join(f'<tr><td>{inline(c)}</td><td>{p:g}</td></tr>' for c, p in s['rubric'])
                  + f'<tr class="total"><td>Summe</td><td>{tot:g}</td></tr></tbody></table></div>')
    return h + '</div>'


def workbook(book, solutions=False):
    d = Doc(book, 'workbook'); m = book['meta']; parts, toc = [], []
    intro = book.get('workbook_intro_solutions' if solutions else 'workbook_intro', '')
    for k, st in enumerate(book['stages'], 1):
        sid = f'st{k}'; toc.append((1, sid, f'{k}\u2002{E(st["title"])}'))
        parts.append(f'<section class="stage{" first" if k == 1 else ""}"><h2 id="{sid}"><span class="no">{k}</span>{inline(st["title"])}</h2>'
                     + ('' if solutions else md(st.get('intro', ''))))
        for it in st['items']:
            parts.append(_item_html(d, it, solution=solutions))
        parts.append('</section>')
    title = 'Musterlösungen' if solutions else 'Arbeitsbuch'
    sub = 'Lösungswege, typische Fehler und Bewertungsschemata zu allen Aufgaben des Arbeitsbuchs' if solutions else \
        'Aufgaben vom Grundverständnis bis zur Klausuraufgabe'
    body = _cover(book, title, sub) + _toc(toc) + (f'<section>{md(intro)}</section>' if intro else '') + ''.join(parts)
    return body, toc


def exam_check(book):
    """Blocking integrity rules for the mock exam (rule A5). Returns problems; empty = consistent."""
    ex, probs = book.get('exam') or {}, []
    items = ex.get('items') or []
    if not items:
        return ['EXAM_EMPTY']
    total = 0
    for it in items:
        if it.get('evidence_gap'):
            probs.append(f'{it["id"]}: evidence-gap item in the exam')
        if not it.get('points'):
            probs.append(f'{it["id"]}: no points')
        s = it.get('solution') or {}
        if not s.get('answer'):
            probs.append(f'{it["id"]}: no solution')
        rub = sum(r[1] for r in s.get('rubric') or [])
        if abs(rub - (it.get('points') or 0)) > 1e-9:
            probs.append(f'{it["id"]}: rubric sums to {rub:g}, item has {it.get("points")} points')
        total += it.get('points') or 0
    if ex.get('total_points') != total:
        probs.append(f'stated total {ex.get("total_points")} != sum of items {total}')
    if ex.get('minutes'):
        mins = sum(it.get('minutes') or 0 for it in items)
        if any(not it.get('minutes') for it in items):
            probs.append('exam declares a duration but not every item has minutes')
        elif mins > ex['minutes']:
            probs.append(f'item minutes {mins:g} exceed exam duration {ex["minutes"]:g}')
    if ex.get('blueprint'):
        from collections import defaultdict
        want, got = defaultdict(float), defaultdict(float)
        for r in ex['blueprint']['rows']:
            want[r['item']] += r['points']
        for it in items:
            got[it['id']] += it.get('points') or 0
        for k in set(want) | set(got):
            if abs(want[k] - got[k]) > 1e-9:
                probs.append(f'blueprint/item mismatch for {k}: blueprint {want[k]:g}, item {got[k]:g}')
    if not ex.get('self_designed_notice'):
        probs.append('exam is not labelled as self-designed')
    return probs


def exam(book, solutions=False):
    probs = exam_check(book)
    if probs:
        raise ContractError('EXAM_INTEGRITY: ' + '; '.join(probs))
    d = Doc(book, 'exam'); ex = book['exam']
    head = ('<div class="examhead"><table>'
            + ''.join(f'<tr><td><b>{E(k)}</b></td><td>{inline(v)}</td></tr>' for k, v in ex['header'])
            + '</table></div>' + md(ex['self_designed_notice']))
    timed = all(i.get('minutes') for i in ex['items'])
    if not solutions:
        head = '<div class="namefield"><div>Name</div><div>Matrikelnummer</div></div>' + head
        head += ('<div class="twrap"><table><thead><tr><th>Aufgabe</th><th>Thema</th>' + ('<th class="num">Zeit</th>' if timed else '')
                 + '<th class="num">Punkte</th><th class="num">Erreicht</th></tr></thead><tbody>'
                 + ''.join(f'<tr><td>{E(i["no"])}</td><td>{inline(i.get("title") or i["topic"])}</td>' + (f'<td class="num">{i["minutes"]:g} Min.</td>' if timed else '')
                           + f'<td class="num">{i["points"]:g}</td><td></td></tr>' for i in ex['items'])
                 + '<tr class="total"><td></td><td>Summe</td>' + (f'<td class="num">{sum(i["minutes"] for i in ex["items"]):g} Min.</td>' if timed else '')
                 + f'<td class="num">{ex["total_points"]:g}</td><td></td></tr></tbody></table></div>')
    elif ex.get('blueprint'):
        bp = ex['blueprint']
        head += ('<h3>Blueprint</h3>' + md(bp.get('rationale', '')) + '<div class="twrap"><table><thead><tr><th>Aufgabe</th><th>Kompetenz</th><th>Operator</th>'
                 '<th>Anforderung</th><th class="num">Punkte</th><th class="num">Zeit</th></tr></thead><tbody>'
                 + ''.join(f'<tr><td>{E(str(r.get("no", r["item"])))}</td><td>{inline(r["competency"])}</td><td>{E(OPS.get(r["operator"], r["operator"]))}</td>'
                           f'<td>{E(r.get("level", ""))}</td><td class="num">{r["points"]:g}</td><td class="num">{r.get("minutes", ""):g}</td></tr>' for r in bp['rows'])
                 + f'<tr class="total"><td></td><td>Summe</td><td></td><td></td><td class="num">{sum(r["points"] for r in bp["rows"]):g}</td>'
                 f'<td class="num">{sum(r.get("minutes", 0) for r in bp["rows"]):g}</td></tr></tbody></table></div>'
                 + (md(bp['grading']) if bp.get('grading') else ''))
    items = ''.join(_item_html(d, it, solution=solutions) for it in ex['items'])
    title = 'Probeklausur – Lösungen und Bewertung' if solutions else 'Probeklausur'
    body = _cover(book, title, ex['subtitle']) + f'<section>{head}</section><section class="exam" style="break-before:page">{items}</section>'
    return body, []


# ------------------------------------------------------------------ rendering

def _assets(out):
    a = Path(out) / 'assets'; (a / 'fonts').mkdir(parents=True, exist_ok=True)
    src = NODE / 'mathjax-full/es5/tex-svg-full.js'
    if not src.exists():
        raise ContractError('MathJax runtime missing; rerun install.sh')
    if not (a / 'tex-svg-full.js').exists():
        shutil.copy2(src, a / 'tex-svg-full.js')
    for _, pkg, variants in FONTS:
        for v in variants:
            f = NODE / f'@fontsource/{pkg}/files/{pkg}-latin-{v}.woff2'
            if f.exists() and not (a / 'fonts' / f.name).exists():
                shutil.copy2(f, a / 'fonts' / f.name)
    return a


FOOTER = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;font-size:7.5pt;color:#6b7785;padding:0 16mm 0 20mm;'
          'display:flex;justify-content:space-between;letter-spacing:.02em"><span>{left}</span><span style="font-weight:600;color:#18212b">'
          '<span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
HEADER = ('<div style="width:100%;font-family:Helvetica,Arial,sans-serif;font-size:7pt;color:#8a949e;padding:0 16mm 0 20mm;'
          'display:flex;justify-content:space-between;letter-spacing:.08em;text-transform:uppercase"><span>{left}</span><span>{right}</span></div>')


def _pdf(page, html_path, pdf_path, footer):
    page.goto(Path(html_path).resolve().as_uri())
    page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise', timeout=60000)
    page.evaluate('MathJax.startup.promise')
    page.evaluate('document.fonts.ready')
    head = '<span></span>'
    if footer and '\x1f' in footer:
        footer, head = footer.split('\x1f')
    page.pdf(path=str(pdf_path), format='A4', print_background=True, display_header_footer=bool(footer),
             header_template=head, footer_template=footer or '<span></span>',
             margin={'top': '22mm', 'bottom': '20mm', 'left': '20mm', 'right': '16mm'})


def render_document(body, toc, title, out_dir, name, footer_left):
    """Cover (no footer) + content (own page numbers). TOC page numbers in a second pass; bookmarks added."""
    import pymupdf
    from playwright.sync_api import sync_playwright
    out_dir = Path(out_dir); _assets(out_dir)
    cover_end = body.index('</section>') + len('</section>')
    cover_html, content = body[:cover_end], body[cover_end:]
    h_cover, h_main = out_dir / f'.{name}.cover.html', out_dir / f'{name}.html'
    h_cover.write_text(_page(title, cover_html), encoding='utf-8')
    h_main.write_text(_page(title, content), encoding='utf-8')
    tmp_c, tmp_m = out_dir / f'.{name}.cover.pdf', out_dir / f'.{name}.main.pdf'
    parts_ = footer_left.split(' · ')
    footer = FOOTER.format(left=E(footer_left)) + '\x1f' + HEADER.format(left=E(parts_[0]), right=E(parts_[-1]))
    pages = {}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        _pdf(pg, h_cover, tmp_c, None)
        _pdf(pg, h_main, tmp_m, footer)
        if toc:
            doc = pymupdf.open(tmp_m)
            links = []
            for n in range(doc.page_count):        # TOC entries are internal links; their targets are the real pages
                for l in doc[n].get_links():
                    if l.get('page') is not None and l['kind'] in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED):
                        links.append((n, l['from'].y0, l['page']))
                if links and n > 3:
                    break
            links.sort()
            for (_lv, i, _t), (_n, _y, target) in zip(toc, links[:len(toc)]):
                pages[i] = target + 1
            doc.close()
            fixed = content
            for i, n in pages.items():
                fixed = fixed.replace(f'<span class="pg" data-for="{E(i)}">00</span>', f'<span class="pg" data-for="{E(i)}">{n}</span>')
            h_main.write_text(_page(title, fixed), encoding='utf-8')
            _pdf(pg, h_main, tmp_m, footer)
        b.close()
    final = pymupdf.open(tmp_c)
    main = pymupdf.open(tmp_m)
    off = final.page_count
    final.insert_pdf(main, links=False)
    for n in range(main.page_count):              # insert_pdf drops internal links: re-create them with the page offset
        for l in main[n].get_links():
            if l.get('kind') in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED) and l.get('page') is not None and l['page'] >= 0:
                final[off + n].insert_link({'kind': pymupdf.LINK_GOTO, 'from': l['from'], 'page': l['page'] + off,
                                            'to': l.get('to') or pymupdf.Point(0, 0)})
            elif l.get('kind') == pymupdf.LINK_URI:
                final[off + n].insert_link({'kind': pymupdf.LINK_URI, 'from': l['from'], 'uri': l['uri']})
    if toc:
        final.set_toc([[lv, re.sub(r'<[^>]+>', '', html.unescape(t)).replace('\u2002', '  '), pages.get(i, 1) + 1]
                       for lv, i, t in toc if i in pages])
    final.set_metadata({'title': title, 'author': 'Exam Mastery (Modellentwurf)', 'subject': footer_left, 'creator': 'Exam Mastery typeset'})
    pdf = out_dir / f'{name}.pdf'
    final.save(pdf, garbage=3, deflate=True)
    n_pages = final.page_count
    final.close(); main.close()
    for f in (tmp_c, tmp_m, h_cover):
        f.unlink(missing_ok=True)
    missing = [i for _l, i, _t in toc if i not in pages]
    chk = pymupdf.open(pdf); n_links = sum(1 for pgx in chk for l in pgx.get_links() if l['kind'] == pymupdf.LINK_GOTO); chk.close()
    return {'pdf': str(pdf), 'html': str(h_main), 'pages': n_pages, 'toc_entries': len(toc), 'toc_unresolved': missing, 'internal_links': n_links}


def publish_book(book, out_dir):
    """All five learning documents. Refuses an inconsistent exam before rendering anything."""
    probs = exam_check(book) if book.get('exam') else []
    if probs:
        raise ContractError('EXAM_INTEGRITY: ' + '; '.join(probs))
    m = book['meta']; left = f'{m["title"]} · Kapitel {m["chapter_no"]}'
    out = {}
    body, toc = textbook(book)
    out['1_Lehrbuch'] = render_document(body, toc, f'{m["title"]} – Lehrbuch', out_dir, '1_Lehrbuch', left + ' · Lehrbuch')
    if book.get('stages'):
        body, toc = workbook(book)
        out['2_Arbeitsbuch'] = render_document(body, toc, f'{m["title"]} – Arbeitsbuch', out_dir, '2_Arbeitsbuch', left + ' · Arbeitsbuch')
        body, toc = workbook(book, solutions=True)
        out['3_Musterloesungen'] = render_document(body, toc, f'{m["title"]} – Musterlösungen', out_dir, '3_Musterloesungen', left + ' · Musterlösungen')
    if book.get('exam'):
        body, _ = exam(book)
        out['4_Probeklausur'] = render_document(body, [], f'{m["title"]} – Probeklausur', out_dir, '4_Probeklausur', left + ' · Probeklausur')
        body, _ = exam(book, solutions=True)
        out['5_Probeklausur_Loesungen'] = render_document(body, [], f'{m["title"]} – Probeklausur Lösungen', out_dir, '5_Probeklausur_Loesungen',
                                                          left + ' · Probeklausur, Lösungen')
    return out
