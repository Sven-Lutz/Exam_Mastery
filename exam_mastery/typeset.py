"""Professional typesetting of the learning products (B9).

One design system, five separate documents per chapter, each with its own cover and its own page numbering:
  1_Lehrbuch (textbook), 2_Arbeitsbuch (practice stages + integrated mock exam + all solutions at the end),
  3_Probeklausur_einzeln (optional stand-alone exam booklet).
Plus kapitel.html (the textbook for screens).

Input is a book model (em-book-v1, see `book_from_ast`). Math is TeX (\\( \\) and \\[ \\]) typeset by MathJax inside
Chromium; figures are SVG from `figures_svg`. The table of contents gets real page numbers in a second pass, and the
PDF gets bookmarks. Nothing here decides content; it only lays it out, and it refuses inconsistent exams.
"""
import html
import json
import re
import shutil
from pathlib import Path

from .common import ContractError
from . import figures_svg

E = html.escape
NODE = Path.home() / '.cache/exam-mastery-v05-node/node_modules'
FONTS = [('Source Serif 4', 'source-serif-4', ['400-normal', '400-italic', '600-normal', '700-normal']),
         ('Source Sans 3', 'source-sans-3', ['400-normal', '400-italic', '600-normal', '700-normal']),
         ('JetBrains Mono', 'jetbrains-mono', ['400-normal'])]
PROV = {'course': 'Vorlesung', 'supplement': 'Fachliche Ergänzung', 'didactic': 'Didaktisches Beispiel (selbst entworfen)',
        'interpretation': 'Einordnung (nicht aus der Vorlesung)', 'unconfirmed': 'Nicht bestätigt', 'vision': 'Abbildung der Vorlesung (vom Agenten ausgewertet)'}
BOX = {'note': 'Hinweis', 'law': 'Rechtslage', 'pitfall': 'Typischer Fehler', 'key': 'Kernaussage', 'remark': 'Anmerkung',
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
        elif len(lines) >= 2 and all(l.strip().startswith('|') and l.strip().endswith('|') for l in lines) and \
                any(re.fullmatch(r'\|?[\s:|-]+\|?', l.strip()) and '-' in l for l in lines):
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
/* Exam Mastery editorial design system "Atlas" (B32). Tokens come from design_tokens.py; every semantic role has a
   colour AND a non-colour cue (label, border style, glyph), so meaning survives greyscale print and colour-vision
   deficiency. Layout: text column + side column; figure/text spreads; numbered components; print first. */
:root{--ink:#1F2933;--ink2:#3A4652;--muted:#5B6878;--line:#CBD3DC;--hair:#E4E8EC;--soft:#F5F7FA;--paper:#FFFFFF;
 --navy:#1B2A41;--petrol:#0F6E73;--petrol-l:#E2F0F0;--blue:#2F5D8A;--blue-l:#E8F0F8;--gold:#8C6416;--gold-l:#FBF2DE;
 --coral:#C8483A;--coral-l:#FBE9E5;--green:#2E7D4F;--green-l:#E5F2EA;--violet:#5B4B9A;--violet-l:#EEEBF7;
 --accent:var(--navy);--accent-soft:var(--petrol-l);--warm:var(--gold);--warm-soft:var(--gold-l);--warn:var(--coral);--warn-soft:var(--coral-l);--ok:var(--green);
 --serif:'Source Serif 4','Iowan Old Style',Georgia,serif;--sans:'Source Sans 3','Helvetica Neue',Arial,sans-serif;
 --mono:'JetBrains Mono',Menlo,monospace;--side:40mm;--gap:7mm}
*{box-sizing:border-box}
html{font-size:10.6pt}
body{margin:0;color:var(--ink);background:var(--paper);font-family:var(--serif);line-height:1.5;font-kerning:normal;
 font-variant-numeric:oldstyle-nums proportional-nums;hyphens:auto;-webkit-hyphens:auto;text-rendering:optimizeLegibility}
main{padding-right:calc(var(--side) + var(--gap))}
h1,h2,h3,h4,.sans{font-family:var(--sans);font-variant-numeric:lining-nums;color:var(--navy)}
h1{font-size:2.2rem;line-height:1.1;margin:0 0 .4em;font-weight:700;letter-spacing:-.015em}
h2{font-size:1.6rem;line-height:1.18;margin:0 0 .8em;font-weight:700;break-before:page;break-after:avoid;letter-spacing:-.008em;
 padding-top:2mm;border-top:5px solid var(--navy)}
h2 .no{display:inline-block;color:#fff;background:var(--navy);font-weight:700;padding:.05em .38em;margin-right:.45em;border-radius:2px}
h3{font-size:1.16rem;margin:1.8em 0 .5em;break-after:avoid;font-weight:700;color:var(--navy)}
h3 .no{color:var(--petrol);font-weight:700;margin-right:.45em}
h4{font-size:1rem;margin:1.1em 0 .3em;break-after:avoid;font-weight:700}
p{margin:0 0 .7em;orphans:3;widows:3}
ul,ol{margin:.2em 0 .8em;padding-left:1.3em}li{margin:.22em 0}li::marker{color:var(--petrol)}
strong{font-weight:600;color:var(--navy)}
a{color:var(--blue)}
pre.code{font-family:var(--mono);font-size:.8rem;line-height:1.45;background:var(--soft);border-radius:3px;padding:.7em .9em;overflow-x:auto;break-inside:avoid;white-space:pre}
code{font-family:var(--mono);font-size:.86em;background:var(--soft);padding:.05em .3em;border-radius:3px}
.dmath{margin:.8em 0 1em;text-align:center;overflow-x:auto}
mjx-container{font-size:104%!important}
mjx-container[display="true"]{display:block;max-width:100%}mjx-container[display="true"]>svg{max-width:100%;height:auto}
/* side column */
.blk{position:relative}.blk::after{content:'';display:table;clear:both}
.side,.src{float:right;clear:right;width:var(--side);margin-right:calc(-1 * (var(--side) + var(--gap)));margin-top:.2em;
 font-family:var(--sans);font-size:.72rem;line-height:1.38;color:var(--muted);font-variant-numeric:lining-nums;hyphens:none;text-align:left;
 border-top:1px solid var(--line);padding-top:.25em}
.side .prov,.src b{display:block;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:.62rem;margin-bottom:.15em}
.prov.course{color:var(--navy)}.prov.supplement{color:var(--gold)}.prov.didactic{color:var(--blue)}.prov.interpretation,.prov.vision,.prov.unconfirmed{color:var(--muted)}
.side .ref{display:block;margin-top:.15em}
.lead{font-size:1.12rem;line-height:1.55;color:var(--ink2);border-left:4px solid var(--gold);padding:.1em 0 .1em .9em;margin:.4em 0 1.2em}
/* chapter opener */
.opener{break-after:page;padding-top:4mm;margin-right:calc(-1 * (var(--side) + var(--gap)))}
.opener .chno{font:800 4.4rem/1 var(--sans);color:var(--petrol);letter-spacing:-.04em}
.opener h1{font-size:2.6rem;margin:.1em 0 .45em;max-width:16em}
.opener .goals{background:var(--soft);border-top:4px solid var(--petrol);padding:.8em 1em .5em;margin-top:1.2em}
.opener .goals h4,.opener .road h4{margin:0 0 .5em;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--petrol)}
.opener .goals ol{padding-left:1.4em;columns:2;column-gap:2em}.opener .goals li{margin:.3em 0;break-inside:avoid;font-size:.94rem}
.opener .road{margin-top:1em;break-inside:avoid;display:grid;grid-template-columns:repeat(5,1fr);gap:.5em .8em;font-family:var(--sans);font-size:.84rem}
.opener .road div{border-top:3px solid var(--navy);padding-top:.35em;color:var(--ink2)}.opener .road b{display:block;color:var(--petrol);font-size:1.1rem}
/* semantic components: role colour + label + border style */
.def,.box,.ex,.mis,.case,.sum,.thm,.prf,.intu,.res-w,.rec,.take,.algo,.cmp,.ftx{margin:1.15em 0 1.25em}
.def,.thm,.box,.intu,.rec,.take,.algo,.sum,.mis{break-inside:avoid-page}
.keephead{break-inside:avoid-page}
.lab{font-family:var(--sans);font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.3em}
.lab .g{font-size:.95rem;margin-right:.35em;letter-spacing:0}
.def{background:var(--petrol-l);border-left:5px solid var(--petrol);padding:.6em 1em .35em}
.def .lab{color:var(--petrol)}.def .term{font-family:var(--sans);font-weight:700;color:var(--navy);margin-right:.35em}
.thm{border:2px solid var(--petrol);border-radius:3px;padding:.6em 1em .35em;background:#fff}
.thm .lab{color:var(--petrol)}.thm .name{font-family:var(--sans);font-weight:700;color:var(--navy)}
.thm .ass{font-family:var(--sans);font-size:.84rem;color:var(--ink2);border-top:1px dashed var(--line);margin-top:.4em;padding-top:.3em}
.prf{border-left:2px solid var(--petrol);padding:.1em 0 .2em 1em}
.prf .lab{color:var(--petrol)}.prf .qed{float:right;color:var(--petrol);font-size:1.1rem;line-height:1}
.prf ol.steps,.ex ol.steps{counter-reset:s;list-style:none;padding-left:0;margin:.4em 0}
.prf ol.steps>li,.ex ol.steps>li{counter-increment:s;display:flex;flex-wrap:wrap;align-items:baseline;column-gap:1em;padding:.38em 0;border-top:1px solid var(--hair);break-inside:avoid}
.prf ol.steps>li:first-child,.ex ol.steps>li:first-child{border-top:none}
.prf ol.steps>li::before,.ex ol.steps>li::before{content:counter(s);flex:0 0 1.9em;font:700 .74rem/1.75 var(--sans);color:#fff;background:var(--blue);border-radius:50%;
 width:1.65em;height:1.65em;text-align:center;margin-right:.25em}
.prf ol.steps>li::before{background:var(--petrol)}
.prf ol.steps>li .why,.ex ol.steps>li .why{display:block;flex:1 1 13em;color:var(--muted);font-size:.86em;font-family:var(--sans);line-height:1.4}
.prf ol.steps>li>.do,.ex ol.steps>li>.do{flex:1.45 1 auto;max-width:100%}
.ex{background:#fff;border:1px solid var(--blue);border-top:5px solid var(--blue);border-radius:3px;padding:.6em 1em .5em;break-inside:auto}
.ex>.lab{color:var(--blue)}.ex h4{margin:.05em 0 .45em;font-size:1.04rem;color:var(--navy)}
.ex>h4,.ex>.lab,.ex>.given{break-after:avoid}
.ex .given{background:var(--blue-l);padding:.5em .8em;border-radius:2px;margin:.3em 0 .7em}.ex .given p:last-child{margin-bottom:0}
.ex .res{border-top:2px solid var(--navy);padding-top:.45em;margin-top:.4em;break-inside:avoid}
.ex .res::before{content:'Ergebnis';font:700 .68rem var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--green);display:block;margin-bottom:.2em}
.intu{background:var(--gold-l);border-left:5px solid var(--gold);padding:.6em 1em .35em}
.intu .lab{color:var(--gold)}
.res-w{border:2px solid var(--gold);border-radius:4px;padding:0;break-inside:avoid-page;background:#fff}
.res-w .rh{background:var(--gold);color:#fff;font-family:var(--sans);padding:.35em .9em;display:flex;justify-content:space-between;align-items:baseline;gap:1em}
.res-w .rh b{font-size:.98rem}.res-w .rh span{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;opacity:.92}
.res-w .rb{padding:.6em .95em .3em}
.res-w .rq{font-family:var(--sans);font-weight:700;color:var(--navy);margin-bottom:.35em}
.res-w .grid{display:grid;grid-template-columns:1fr 1fr;gap:.3em 1.2em;font-size:.93rem}
.res-w .grid h5{margin:.2em 0 .1em;font:700 .66rem var(--sans);letter-spacing:.12em;text-transform:uppercase;color:var(--gold)}
.res-w .cite{border-top:1px dashed var(--line);margin-top:.5em;padding-top:.35em;font-family:var(--sans);font-size:.76rem;color:var(--ink2)}
.res-w .tag{display:inline-block;border:1px solid var(--gold);color:var(--gold);border-radius:2px;padding:0 .35em;font:700 .62rem var(--sans);letter-spacing:.08em;text-transform:uppercase;margin-right:.4em}
.rec{border:2px dashed var(--violet);border-radius:4px;padding:.55em 1em .35em;background:var(--violet-l)}
.rec .lab{color:var(--violet)}.rec ol{margin:.2em 0 .3em}.rec .ans{font-family:var(--sans);font-size:.78rem;color:var(--muted)}
.take{border-left:5px double var(--green);background:var(--green-l);padding:.55em 1em .3em}
.take .lab{color:var(--green)}.take ul{margin-bottom:.3em}
.algo{border:1px solid var(--navy);border-radius:3px;font-family:var(--sans)}
.algo .ah{background:var(--navy);color:#fff;padding:.3em .8em;font-weight:700;font-size:.92rem}
.algo ol{margin:.5em 0 .5em;padding-left:2.4em;font-size:.94rem}.algo ol li::marker{color:var(--navy);font-weight:700}
.algo .io{padding:.3em .8em;border-top:1px solid var(--line);font-size:.86rem;color:var(--ink2)}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:0;border:1px solid var(--line);border-radius:3px;break-inside:avoid-page}
.cmp>div{padding:.55em .9em .3em}.cmp>div+div{border-left:1px solid var(--line)}
.cmp h5{margin:0 0 .3em;font:700 .9rem var(--sans);color:var(--navy);border-bottom:3px solid var(--petrol);padding-bottom:.2em}
.cmp>div:nth-child(2) h5{border-bottom-color:var(--gold)}
.cmp .row{display:contents}
.ftx{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:1.1em;align-items:start;break-inside:avoid-page}
.ftx.left{grid-template-columns:minmax(0,1fr) minmax(0,1.05fr)}.ftx.left .ftx-fig{order:-1}
.ftx.stack{display:block}.ftx.stack .ftx-fig{margin-top:.6em}.ftx.stack figure{margin-right:calc(-1 * (var(--side) + var(--gap)))}.ftx.stack .ftx-txt{break-after:avoid}
.ftx figure{margin:0}.ftx .ftx-txt>:first-child{margin-top:0}
.box{background:var(--soft);padding:.6em .95em .35em;border-left:5px solid var(--line)}
.box.law{border-left-color:var(--gold);background:var(--gold-l)}.box.law .lab{color:var(--gold)}
.box.pitfall,.box.limit{border-left-color:var(--coral);background:var(--coral-l)}.box.pitfall .lab,.box.limit .lab{color:var(--coral)}
.box.key{border:2px solid var(--navy);border-left-width:6px;background:#fff}.box.key .lab{color:var(--navy)}
.box.research{border-left-color:var(--gold);background:var(--gold-l)}.box.research .lab{color:var(--gold)}
.box.question{border-left-color:var(--violet);background:var(--violet-l)}.box.question .lab{color:var(--violet)}
.mis{display:grid;grid-template-columns:1fr 1fr;gap:.2em 1.2em;border:1px solid var(--coral);border-top:5px solid var(--coral);border-radius:3px;padding:.55em .95em}
.mis .lab{grid-column:1/3;color:var(--coral)}
.mis .wrong::before{content:'✗ Fehlvorstellung'}.mis .right::before{content:'✓ Richtig ist'}
.mis .wrong::before,.mis .right::before{display:block;font:700 .8rem var(--sans);margin-bottom:.15em}
.mis .wrong{color:var(--ink2);text-decoration:none}.mis .wrong::before{color:var(--coral)}.mis .right::before{color:var(--green)}
.mis .why{grid-column:1/3;color:var(--ink2);font-size:.94em;border-top:1px dashed var(--line);padding-top:.3em}
.case{border-left:4px solid var(--muted);padding:.2em 0 .1em .95em}
.sum{border-top:4px solid var(--navy);border-bottom:4px solid var(--navy);padding:.6em 0 .2em}.sum .lab{color:var(--navy)}
figure{margin:1.3em 0 1.4em;break-inside:avoid}
figure .fig{text-align:center;background:#fff}
figure .fig svg{max-width:100%}
/* B33: stand-alone figures use text + margin column (wide figure); vector graphics scale to the measure, capped in height */
figure{margin-right:calc(-1 * (var(--side) + var(--gap)))}figure .fig svg{width:100%;height:auto;max-height:118mm}
.ftx figure{margin-right:0}.ftx figure .fig svg{max-height:95mm}
figcaption,.tcap{font-family:var(--sans);font-size:.8rem;color:var(--ink2);margin-top:.5em;line-height:1.42;border-left:3px solid var(--petrol);padding-left:.6em}
figcaption b,.tcap b{color:var(--petrol);margin-right:.3em}
figcaption .msg{font-weight:700;color:var(--navy)}
.twrap{overflow-x:auto;margin:1em 0 1.2em;break-inside:avoid}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:.86rem;font-variant-numeric:lining-nums tabular-nums}
th{text-align:left;font-weight:700;color:#fff;background:var(--navy);padding:.36em .55em;vertical-align:bottom;hyphens:none;-webkit-hyphens:none}
td{hyphens:manual;-webkit-hyphens:manual;border-bottom:1px solid var(--hair);padding:.32em .55em;vertical-align:top}
tbody tr:nth-child(even) td{background:var(--soft)}
td.num,th.num{text-align:right}td.num{white-space:nowrap}
tr.total td{border-top:2px solid var(--navy);font-weight:700}
tr.neg td.num{color:var(--coral)}
.tcap{margin:0 0 .35em}
/* cover & toc */
.cover{height:252mm;display:flex;flex-direction:column;justify-content:space-between;padding:0;position:relative}
.cover .band{height:58mm;background:var(--navy);margin:0 -1px;position:relative}
.cover .band::after{content:'';position:absolute;left:0;bottom:-6px;width:42%;height:6px;background:var(--gold)}
.cover .kicker{font:700 .82rem var(--sans);letter-spacing:.18em;text-transform:uppercase;color:var(--petrol);margin-top:14mm}
.cover h1{font-size:3.2rem;margin:.2em 0 .2em;max-width:13em}
.cover .sub{font:400 1.3rem var(--sans);color:var(--ink2)}
.cover .rule{height:2px;background:var(--navy);width:100%;margin:1.3em 0}
.cover .meta{font:400 .8rem var(--sans);color:var(--muted);line-height:1.55;border-top:1px solid var(--line);padding-top:.8em;max-width:150mm}
.toc{break-after:page}
.toc h2{border-top:none;break-before:auto}
.toc a{color:inherit;text-decoration:none;display:flex;gap:.4em}
.toc .e{display:flex;align-items:baseline;margin:.3em 0;font-family:var(--sans)}
.toc .e.l1{font-weight:700;margin-top:.8em;color:var(--navy)}
.toc .e.l2{padding-left:1.8em;font-size:.93em;color:var(--ink2)}
.toc .e .t{flex:0 1 auto}.toc .e .d{flex:1 1 auto;border-bottom:1px dotted #a6afb8;margin:0 .4em;transform:translateY(-.3em)}
.toc .e .pg{flex:0 0 auto;font-variant-numeric:lining-nums}
/* workbook */
.item{break-inside:avoid-page;margin:0 0 1.4em}
#sec-psol .item,.item.sol{break-inside:auto}.item .head{break-after:avoid}.rubk{break-inside:avoid-page}
.part>.ph{break-inside:avoid;break-after:avoid}.part .ph h2{break-before:avoid!important}
.item .head{font-family:var(--sans);display:flex;justify-content:space-between;align-items:baseline;border-bottom:2px solid var(--violet);margin-bottom:.45em;padding-bottom:.12em}
.item .head .id{font-weight:700;color:var(--navy)}.item .head .meta{font-size:.76rem;color:var(--muted);font-variant-numeric:lining-nums}
.item .head .meta .op{display:inline-block;background:var(--violet-l);color:var(--violet);border-radius:2px;padding:0 .4em;margin-right:.4em;text-transform:uppercase;letter-spacing:.06em;font-size:.66rem;font-weight:700}
.space{border:1px solid var(--line);border-radius:2px;background:repeating-linear-gradient(transparent,transparent 7.4mm,#e9ecef 7.4mm,#e9ecef 7.55mm);margin:.5em 0 0}
.scaffold{counter-reset:s;list-style:none;padding:0;margin:.5em 0}
.scaffold li{counter-increment:s;display:grid;grid-template-columns:1.6em 1fr;padding:.3em 0;border-top:1px solid var(--hair)}
.scaffold li::before{content:counter(s);font:700 .78rem/1.6 var(--sans);color:var(--violet)}
.scaffold .blank{display:inline-block;min-width:26mm;border-bottom:1px solid var(--ink);height:1.1em;vertical-align:baseline}
.stage{break-before:page}.stage.first{break-before:auto}
.stage h2{break-before:auto}
.stage .intro{font-family:var(--sans);font-size:.88rem;color:var(--ink2);border-left:4px solid var(--violet);padding-left:.8em;margin-bottom:1.2em}
.part{break-before:page}.part>.ph{background:var(--navy);color:#fff;font-family:var(--sans);padding:6mm 7mm;margin-bottom:6mm}
.part>.ph .k{font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;opacity:.8}.part>.ph h2{color:#fff;border:none;margin:.2em 0 0;break-before:auto}
.rub td:last-child,.rub th:last-child{text-align:right;width:5em;white-space:nowrap;hyphens:none}
.evid{font-family:var(--sans);font-size:.78rem;color:var(--gold);border-left:3px solid var(--gold);padding:.1em .6em;margin:.2em 0 .5em}
.hint{font-family:var(--sans);font-size:.85rem;color:var(--muted)}
.alt{border-left:3px solid var(--blue);padding-left:.8em;margin:.6em 0}
.examhead{border:2px solid var(--navy);padding:.7em 1em;font-family:var(--sans);margin-bottom:1.2em}
.examhead table{font-size:.9rem}.examhead td{border:none;padding:.15em .4em;background:none!important}
.namefield{display:grid;grid-template-columns:1fr 1fr;gap:1em;margin:0 0 1.2em;font-family:var(--sans);font-size:.85rem}
.namefield div{border-bottom:1px solid var(--ink);padding-top:1.6em;color:var(--muted)}
.exam .item .head{border-bottom-color:var(--navy)}
.ptsbox{float:right;border:1.5px solid var(--ink);font-family:var(--sans);font-size:.8rem;padding:.15em .5em;margin-left:1em}
@page{size:A4;margin:22mm 16mm 22mm 20mm}
@media print{a{color:inherit;text-decoration:none}main{max-width:none}}
@media screen{body{background:#eef1f4}main{max-width:64rem;margin:0 auto;padding:2.5em 1.5em 5em;padding-right:calc(var(--side) + var(--gap) + 1.5em);background:#fff}
 .cover{height:auto;min-height:70vh}h2{break-before:auto;margin-top:2.4em}}
@media screen and (max-width:760px){main{padding-right:1.2em}figure,.opener,.ftx.stack figure{margin-right:0}.side,.src{float:none;width:auto;margin:.2em 0 .6em}.opener .road{grid-template-columns:1fr 1fr}
 .opener .goals ol{columns:1}.ftx,.cmp,.res-w .grid,.mis{grid-template-columns:1fr}.cmp>div+div{border-left:none;border-top:1px solid var(--line)}
 .ex ol.steps>li .why,.prf ol.steps>li .why{flex-basis:100%;padding-left:2.7em}}
html.grey{filter:grayscale(1)}
"""


# ------------------------------------------------------------------ blocks

class Doc:
    def __init__(self, book, kind):
        self.book, self.kind = book, kind
        self.fig_no, self.tab_no, self.toc = 0, 0, []
        self.def_no, self.ex_no = 0, 0
        self.thm_no, self.rec_no, self.res_no, self.algo_no = 0, 0, 0, 0
        self.fig_index = {}

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
        svg = figures_svg.render(spec)
        self.fig_index[b['id']] = f'{self.book["meta"]["chapter_no"]}.{self.fig_no}'
        msg = b.get('message') or spec.get('message')
        cap = (f'<b>Abbildung {self.book["meta"]["chapter_no"]}.{self.fig_no}</b> ' + (f'<span class="msg">{inline(msg)}</span> ' if msg else '')
               + inline(b.get("caption") or spec.get("caption") or spec.get("title", "")))
        return f'<figure id="fig-{E(b["id"])}"><div class="fig">{svg}</div><figcaption>{cap}{self._capsrc(b)}</figcaption></figure>'

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
        side = '' if b['type'] in ('figure', 'table', 'lab', 'lead', 'summary', 'misconception', 'research', 'figtext', 'compare') else self.side(b)
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
            steps = ''.join(f'<li><span class="do">{inline(s[0])}</span>' + (f'<span class="why">{inline(s[1])}</span>' if len(s) > 1 and s[1] else '') + '</li>'
                            for s in b['steps'])
            tab = self.table(b['table']) if b.get('table') else ''
            fig = self.figure({'id': b['figure']}) if b.get('figure') else ''
            return (f'<div class="ex"><span class="lab">Beispiel {self.book["meta"]["chapter_no"]}.{self.ex_no} · {E(b.get("label", "Durchgerechnet"))}</span><h4>{inline(b["title"])}</h4>'
                    f'<div class="given">{md(b["given"])}</div>{tab}<ol class="steps">{steps}</ol>'
                    + (f'<div class="res">{md(b["result"])}</div>' if b.get('result') else '') + f'{fig}</div>')
        if t == 'table':
            return self.table(b)
        if t == 'figure':
            return self.figure(b)
        if t == 'lab':  # B13: static state of an interactive lab (PDF/print); the HTML links to the lab itself
            self.fig_no += 1
            cap = (f'<b>Abbildung {self.book["meta"]["chapter_no"]}.{self.fig_no}</b> {inline(b["title"])}{"" if b["title"].rstrip().endswith(("?", "!", ".")) else "."} {inline(b.get("caption", ""))} '
                   f'<i>Interaktiv</i> in der Lernumgebung (<a href="{E(b["href"])}">Lab öffnen</a>). Modellannahmen: {_mt(" ".join(a.rstrip(".") + "." for a in b.get("assumptions", [])))}')
            return f'<figure class="lab-fig"><div class="fig">{b["svg"]}</div><figcaption>{cap}{self._capsrc(b)}</figcaption></figure>'
        if t == 'misconception':
            return (f'<div class="mis"><span class="lab">Häufige Fehlvorstellung</span><div class="wrong">{md(b["wrong"])}</div>'
                    f'<div class="right">{md(b["right"])}</div>' + (f'<div class="why">{md(b["why"])}</div>' if b.get('why') else '') + '</div>')
        if t == 'case':
            return f'<div class="case"><span class="lab">{E(b.get("label","Fall"))}</span><h4>{inline(b["title"])}</h4>{md(b["md"])}</div>'
        if t == 'summary':
            return f'<div class="sum"><span class="lab">{E(b.get("title","Zusammenfassung"))}</span>{md(b["md"])}</div>'
        if t == 'theorem':
            self.thm_no += 1
            ass = b.get('assumptions') or []
            return (f'<div class="thm"><span class="lab"><span class="g">◆</span>{E(b.get("label", "Satz"))} {self.book["meta"]["chapter_no"]}.{self.thm_no}</span>'
                    + (f'<span class="name">{inline(b["name"])}.</span> ' if b.get('name') else '') + md(b['md'])
                    + (f'<div class="ass"><b>Voraussetzungen:</b> {inline("; ".join(ass))}</div>' if ass else '') + '</div>')
        if t == 'proof':
            steps = ''.join(f'<li><span class="do">{inline(x[0])}</span>' + (f'<span class="why">{inline(x[1])}</span>' if len(x) > 1 and x[1] else '') + '</li>' for x in b.get('steps', []))
            return (f'<div class="prf"><span class="lab">{E(b.get("label", "Beweis"))}{(" · " + inline(b["title"])) if b.get("title") else ""}</span>'
                    + md(b.get('md', '')) + (f'<ol class="steps">{steps}</ol>' if steps else '') + '<span class="qed">∎</span><div style="clear:both"></div></div>')
        if t == 'intuition':
            return f'<div class="intu"><span class="lab"><span class="g">◐</span>{E(b.get("title", "Intuition"))}</span>{md(b["md"])}</div>'
        if t == 'takeaway':
            pts = ''.join(f'<li>{inline(x)}</li>' for x in b.get('points', []))
            return f'<div class="take"><span class="lab"><span class="g">✓</span>{E(b.get("title", "Das Wichtigste"))}</span>{md(b.get("md", ""))}' + (f'<ul>{pts}</ul>' if pts else '') + '</div>'
        if t == 'recall':
            self.rec_no += 1
            qs = ''.join(f'<li>{inline(q[0])}</li>' for q in b['questions'])
            self.book.setdefault('_recall_answers', []).append((f'{self.book["meta"]["chapter_no"]}.{self.rec_no}', b['questions']))
            return (f'<div class="rec"><span class="lab"><span class="g">?</span>Kontrollfragen {self.book["meta"]["chapter_no"]}.{self.rec_no} – erst antworten, dann weiterlesen</span>'
                    f'<ol>{qs}</ol><div class="ans">Antworten am Kapitelende (Abschnitt „Antworten zu den Kontrollfragen“).</div></div>')
        if t == 'research':
            self.res_no += 1
            g = lambda k, h: f'<div><h5>{E(h)}</h5>{md(b[k])}</div>' if b.get(k) else ''
            tags = ''.join(f'<span class="tag">{E(x)}</span>' for x in b.get('tags', []))
            return (f'<div class="res-w"><div class="rh"><b>{inline(b["title"])}</b><span>Forschungsfenster {self.book["meta"]["chapter_no"]}.{self.res_no}</span></div>'
                    f'<div class="rb"><div class="rq">Frage: {inline(b["question"])}</div><div class="grid">{g("finding", "Befund")}{g("link", "Bezug zum Kapitel")}'
                    f'{g("limits", "Grenzen der Übertragung")}{g("status", "Einordnung")}</div>'
                    f'<div class="cite">{tags}{"; ".join(inline(r) for r in b.get("refs", []))}</div></div></div>')
        if t == 'algorithm':
            self.algo_no += 1
            steps = ''.join(f'<li>{inline(x)}</li>' for x in b['steps'])
            return (f'<div class="algo"><div class="ah">Algorithmus {self.book["meta"]["chapter_no"]}.{self.algo_no} · {inline(b["title"])}</div>'
                    + (f'<div class="io"><b>Eingabe:</b> {inline(b["input"])}</div>' if b.get('input') else '') + f'<ol>{steps}</ol>'
                    + (f'<div class="io"><b>Ausgabe:</b> {inline(b["output"])}</div>' if b.get('output') else '')
                    + (f'<div class="io"><b>Aufwand:</b> {inline(b["cost"])}</div>' if b.get('cost') else '') + '</div>')
        if t == 'compare':
            cols = ''.join(f'<div><h5>{inline(c["title"])}</h5>{md(c["md"])}</div>' for c in b['columns'])
            return (f'<div class="cmp">{cols}</div>' + (f'<p class="hint">{inline(b["note"])}</p>' if b.get('note') else ''))
        if t == 'figtext':
            fig = self.figure({'id': b['figure'], 'caption': b.get('caption'), 'message': b.get('message'), 'prov': b.get('prov'), 'src': b.get('src'), 'refs': b.get('refs')})
            # B33: a wide figure (aspect > 1.45) would shrink below legibility in a half column; it is set as a
            # stacked text-figure unit instead (text, then the figure at full measure, kept together)
            m_ = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', fig)
            wide = bool(m_) and float(m_.group(1)) / max(1.0, float(m_.group(2))) > 1.45
            cls = 'ftx stack' if wide else 'ftx' + (' left' if b.get('side') == 'left' else '')
            return f'<div class="{cls}"><div class="ftx-txt">{md(b["md"])}</div><div class="ftx-fig">{fig}</div></div>'
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
    if book.get('_recall_answers'):
        toc.append((1, 'kontrolle', 'Antworten zu den Kontrollfragen'))
        back.append('<h2 id="kontrolle">Antworten zu den Kontrollfragen</h2>' + ''.join(
            f'<h4>Kontrollfragen {E(no)}</h4><ol>' + ''.join(f'<li><b>{inline(q[0])}</b><br>{inline(q[1])}</li>' for q in qs) + '</ol>'
            for no, qs in book.pop('_recall_answers')))
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
        back.append('<h2 id="entstehung">Anhang: Entstehung und Qualitätsstatus</h2>' + md(book['production_notes']))
    body = _cover(book, 'Lehrbuch', m.get('subtitle', '')) + _toc(toc) + _opener(book) + ''.join(parts) + ''.join(back)
    return body, toc


def _item_html(d, it, solution=False, space=True, exam=False):
    meta = ([] if exam or it.get('stage_label') in ('exam', 'recall', 'guided', 'standard', 'transfer') else [it.get('stage_label', '')]) + ([f'≈ {it["minutes"]:g} Min.'] if it.get('minutes') else []) + ([f'{it["points"]:g} P.'] if it.get('points') else [])
    op = OPS.get(it.get('operation') or '', '')
    h = (f'<div class="item" id="{E(it["id"])}"><div class="head"><span class="id">{"Aufgabe " + E(it["no"])}{(" · " + inline(it["title"])) if it.get("title") else ""}</span>'
         f'<span class="meta">{f"<span class=op>{E(op)}</span>" if op else ""}{E(" · ".join(x for x in meta if x))}</span></div>'
         # B33: provenance of the task itself (official exam evidence vs. author-created practice) is printed, not only stored
         + (f'<p class="evid"><b>Offizielle Beispielfrage</b> · {inline(it.get("source_note") or "")}</p>' if it.get('evidence') == 'OFFICIAL_EXAM_EVIDENCE' else '')
         + md(it["prompt"]))
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
            h += ('<div class="rubk"><h4>Bewertung</h4><div class="twrap"><table class="rub"><thead><tr><th>Kriterium</th><th>Punkte</th></tr></thead><tbody>'
                  + ''.join(f'<tr><td>{inline(c)}</td><td>{p:g}</td></tr>' for c, p in s['rubric'])
                  + f'<tr class="total"><td>Summe</td><td>{tot:g}</td></tr></tbody></table></div></div>')
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


ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']


def workbook_integrated(book):
    """B32: ONE workbook — practice stages, the integrated mock exam, and all solutions at the END (never interleaved).
    Item ids and numbering are identical in the task and the solution part."""
    d = Doc(book, 'workbook'); m = book['meta']; parts, toc = [], []
    stages = book.get('stages') or []
    def part(k, kicker, title, inner, pid):
        toc.append((1, pid, f'Teil {ROMAN[k]}\u2002{E(title)}'))
        return f'<section class="part" id="sec-{pid}"><div class="ph"><div class="k">{E(kicker)}</div><h2 id="{pid}">Teil {ROMAN[k]} · {inline(title)}</h2></div>{inner}</section>'
    for k, st in enumerate(stages):
        inner = (f'<div class="stage-intro">{md(st.get("intro", ""))}</div>' if st.get('intro') else '') + ''.join(_item_html(d, it) for it in st['items'])
        parts.append(part(k, 'Üben', st['title'], inner, f'p{k + 1}'))
    k = len(stages)
    ex = book.get('exam')
    if ex:
        probs = exam_check(book)
        if probs:
            raise ContractError('EXAM_INTEGRITY: ' + '; '.join(probs))
        head = ('<div class="namefield"><div>Name</div><div>Matrikelnummer</div></div><div class="examhead"><table>'
                + ''.join(f'<tr><td><b>{E(a)}</b></td><td>{inline(b_)}</td></tr>' for a, b_ in ex['header']) + '</table></div>' + md(ex['self_designed_notice']))
        parts.append(part(k, 'Prüfungssimulation – ohne Hilfen bearbeiten', 'Probeklausur', head + '<div class="exam">' + ''.join(_item_html(d, it, exam=True) for it in ex['items']) + '</div>', 'pexam'))
        k += 1
    sol = ''.join(f'<h3>{E(st["title"])}</h3>' + ''.join(_item_html(d, it, solution=True) for it in st['items']) for st in stages)
    if ex:
        sol += '<h3>Probeklausur</h3>' + ''.join(_item_html(d, it, solution=True, exam=True) for it in ex['items'])
    parts.append(part(k, 'Erst nach eigener Bearbeitung lesen', 'Lösungen', sol, 'psol'))
    intro = book.get('workbook_intro', '')
    body = _cover(book, 'Arbeitsbuch', 'Üben in fünf Stufen · integrierte Probeklausur · alle Lösungen am Ende') + _toc(toc) + (f'<section>{md(intro)}</section>' if intro else '') + ''.join(parts)
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


LAYOUT_LINT_JS = r'''() => {
  const out = {inline_math_reflowed: [], overflow: [], broken_images: []};
  const box = el => { let p = el.parentElement; while (p && getComputedStyle(p).display.startsWith('inline')) p = p.parentElement; return p; };
  for (const m of document.querySelectorAll('mjx-container:not([display="true"])')) {
    const p = box(m); if (!p) continue;
    const pr = p.getBoundingClientRect(), r = m.getBoundingClientRect();
    if (r.right > pr.right + 1 || r.width > pr.width) {
      m.setAttribute('display', 'true'); m.style.display = 'block'; m.style.margin = '.35em 0';
      const svg = m.querySelector('svg'); if (svg) { svg.style.maxWidth = '100%'; svg.style.height = 'auto'; }
      out.inline_math_reflowed.push((m.getAttribute('aria-label') || m.textContent || '').slice(0, 80));
    }
  }
  const vw = document.documentElement.clientWidth;
  for (const el of document.querySelectorAll('figure, table, .ftx, .cmp, mjx-container[display="true"], svg')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > vw + 2) out.overflow.push({tag: el.tagName.toLowerCase(), cls: String(el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className).slice(0, 40), right: Math.round(r.right), page_width: vw});
  }
  for (const img of document.images) if (!img.complete || img.naturalWidth === 0) out.broken_images.push(img.getAttribute('src'));
  return out;
}'''


def _pdf(page, html_path, pdf_path, footer):
    page.goto(Path(html_path).resolve().as_uri())
    page.wait_for_function('window.MathJax && MathJax.startup && MathJax.startup.promise', timeout=60000)
    page.evaluate('MathJax.startup.promise')
    page.evaluate('document.fonts.ready')
    # B33 layout lint: inline formulas wider than their text block are set as scaled display formulas (no clipping,
    # no running into the margin); figures/tables that overflow are reported. The result is written next to the PDF.
    page.emulate_media(media='print')
    page.set_viewport_size({'width': 658, 'height': 1000})
    lint = page.evaluate(LAYOUT_LINT_JS)
    Path(pdf_path).with_name('.' + Path(pdf_path).stem + '.layout_lint.json').write_text(json.dumps(lint, ensure_ascii=False, indent=1), encoding='utf-8')
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
        body, toc = workbook_integrated(book)
        out['2_Arbeitsbuch'] = render_document(body, toc, f'{m["title"]} – Arbeitsbuch', out_dir, '2_Arbeitsbuch', left + ' · Arbeitsbuch')
    if book.get('exam'):   # optional stand-alone exam booklet (the workbook already contains it)
        body, _ = exam(book)
        out['3_Probeklausur_einzeln'] = render_document(body, [], f'{m["title"]} – Probeklausur', out_dir, '3_Probeklausur_einzeln', left + ' · Probeklausur')
    return out
