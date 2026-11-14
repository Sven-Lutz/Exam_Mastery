"""Render a track as one self-contained offline page (learning workbench). Deterministic, no model call.
Inline CSS/JS pinned by a Content-Security-Policy hash, no network access (same contract as the labs)."""
import html
import json
from pathlib import Path

from ..labs.build import TEMPLATES, _sha
from . import tracks as TR

E = lambda s: html.escape(str(s), quote=True)
DOMAIN = {'machine_learning': 'Machine Learning', 'business_economics': 'Finanzierung', 'mathematics': 'Mathematik'}


def page(track, back='../index.html', lab_href=None, fonts=None, back_label='Alle Experimente und Lernstrecken'):
    TR.validate(track)
    css = (TEMPLATES / 'em_tokens.css').read_text(encoding='utf-8') + (TEMPLATES / 'em_tutor.css').read_text(encoding='utf-8')
    if fonts:
        from .. import typeset
        css = typeset.font_css(fonts) + css
    js = (TEMPLATES / 'em_tutor.js').read_text(encoding='utf-8')
    csp = (f"default-src 'none'; img-src data:; font-src 'self' file: data:; style-src {_sha(css)}; script-src {_sha(js)}; "
           "base-uri 'none'; form-action 'none'")
    data = json.dumps(track, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    lab = f'<a href="{E(lab_href)}">Zum Experiment</a>' if lab_href else ''
    body = (f'<header class="wb-top"><a href="{E(back)}">← {E(back_label)}</a><span>{lab}</span></header>'
            f'<section class="wb-head"><p class="wb-kind">Adaptive Lernstrecke · {E(DOMAIN.get(track["domain"], track["domain"]))}</p>'
            f'<h1>{E(track["title"])}</h1><p>{E(track["objective"])}</p></section>'
            '<noscript><p>Diese Lernstrecke braucht JavaScript. Die Aufgaben stehen auch im Arbeitsbuch des Kurses.</p></noscript>'
            '<div id="wb"></div>'
            '<footer class="wb-foot">'
            '<section><h2>Wie diese Lernstrecke entscheidet</h2><p>Jede Antwort wird regelbasiert geprüft (Zahl, Ausdruck, Rechenschritte oder Voraussetzungen). '
            'Die nächste Aufgabe folgt aus festen, offen gelegten Regeln – unter jeder Rückmeldung steht, welche Regel gegriffen hat und was unsicher bleibt. '
            'Es gibt keinen Prozentwert für Beherrschung.</p></section>'
            '<section id="wb-history"><h2>Lernhistorie</h2><p>Bleibt in diesem Browser. Export und Import als Datei; nichts wird gesendet.</p></section>'
            '<section><h2>Quellen und Status</h2><ul>' + ''.join(f'<li>{E(s)}</li>' for s in track['sources']) + f'</ul><p>{E(track["source_status"])}</p>'
            + (('<p>Annahmen: ' + E(' '.join(track['assumptions'])) + '</p>') if track.get('assumptions') else '') + '</section></footer>'
            f'<script type="application/json" id="em-track">{data}</script>')
    return ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="no-referrer">'
            f'<title>{E(track["title"])}</title><style>{css}</style></head><body><main id="main" class="wb-shell">{body}</main>'
            f'<script>{js}</script></body></html>')


def write(track, out_dir, context=None, **kw):
    """context: storage namespace (e.g. 'referenz'), so a reference collection never mixes with a chapter's history."""
    if context:
        track = dict(track, store_ctx=context)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    name = track['id'].replace('/', '__') + '.html'
    (out / name).write_text(page(track, **kw), encoding='utf-8')
    (out / (name[:-5] + '.json')).write_text(json.dumps(track, ensure_ascii=False, indent=1), encoding='utf-8')
    return out / name
