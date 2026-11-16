"""Campaign dashboard: one start page for several produced chapter packages (no model call).

Input: a campaign JSON
{"title": "...", "output_root": "/…/Exam_Mastery_Output", "ledger": "/…/call_ledger.json",
 "courses": [{"tag": "RL", "name": "Reinforcement Learning", "folder": "/…/RL", "chapter_id": "ch-…",
              "domain": "Informatik / ML", "review": "/…/review_findings.json" (optional, independent agent review),
              "human_checks": ["…"] (optional, what a person still has to check)}]}

For every course the newest run that published the chapter is located in the course output folder; the page shows
status, the delivered products (links), the essential quality results and the human checks still required. Technical
detail (gates, ledger rows, review findings) sits in collapsible sections. Everything is read from files the engine
wrote; nothing is re-judged here, and nothing is shown as passed that the files do not say passed.
"""
import html
import json
import os
from pathlib import Path

E = lambda s: html.escape(str(s), quote=True)
PRODUCTS = [('1_Lehrbuch.pdf', 'Lehrbuch'), ('2_Arbeitsbuch.pdf', 'Arbeitsbuch'), ('3_Probeklausur_einzeln.pdf', 'Probeklausur (Einzelheft)'),

            ('Anki_Karten.apkg', 'Anki-Deck'), ('Lernumgebung/index.html', 'Lernumgebung'),
            ('6_Quellenabbildungen.pdf', 'Quellenabbildungen')]
DIM = {'rendering': 'Rendering', 'formulas_and_figures': 'Formeln & Abbildungen', 'anki': 'Anki', 'coverage': 'Kompetenzabdeckung',
       'didactic_completeness': 'Didaktik', 'items_and_solutions': 'Aufgaben & Lösungen', 'math_numeric': 'Rechnungen',
       'subject_correctness': 'Fachliche Richtigkeit'}


def _course_out(root, folder):
    from .incremental import course_id
    return Path(root) / course_id(folder)


def latest_publication(course_out, chapter_id):
    """Newest run directory whose status.json shows the chapter published, with its LERNMATERIAL folder."""
    runs = sorted((p for p in Path(course_out).glob('ch-*') if (p / 'status.json').exists()), key=lambda p: p.name, reverse=True)
    for r in runs:
        try:
            st = json.loads((r / 'status.json').read_text(encoding='utf-8'))
        except ValueError:
            continue
        c = (st.get('chapters') or {}).get(chapter_id) or {}
        pub = c.get('publish') or {}
        if pub.get('status', '').startswith('PUBLISHED'):
            mats = [d for d in (r / 'LERNMATERIAL').glob('*') if d.is_dir()] if (r / 'LERNMATERIAL').is_dir() else []
            return r, st, c, (mats[0] if mats else None)
    return None, None, None, None


def _pdf_pages(p):
    try:
        import pymupdf
        with pymupdf.open(p) as d:
            return d.page_count
    except Exception:
        return None


def course_card(c, root, ledger):
    out = _course_out(root, c['folder'])
    run, st, ch, mat = latest_publication(out, c['chapter_id'])
    card = {'tag': c['tag'], 'name': c['name'], 'domain': c.get('domain', ''), 'chapter_id': c['chapter_id'],
            'run': str(run) if run else None, 'material': str(mat) if mat else None, 'products': [], 'dims': {},
            'calls': [x for x in ledger.get('calls', []) if x.get('course') == c['tag']],
            'human_checks': c.get('human_checks') or [], 'review': None, 'title': c.get('chapter_title', '')}
    if not run:
        card['status'] = 'NICHT PRODUZIERT'
        return card
    dossier = {}
    try:
        dossier = json.loads((run / 'quality_dossier.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    chd = (dossier.get('chapters') or {}).get(c['chapter_id']) or {}
    card['dims'] = {k: (v.get('status') if isinstance(v, dict) else v) for k, v in (chd.get('dimensions') or dossier.get('dimensions') or {}).items()}
    card['academic'] = chd.get('academic_release') or (dossier.get('release') or {}).get('academic')
    card['gate'] = ch.get('gate')
    if mat:
        card['title'] = card['title'] or mat.name.split('_', 1)[-1].replace('_', ' ')
        for f, label in PRODUCTS:
            p = mat / f
            if p.exists():
                card['products'].append({'label': label, 'path': str(p), 'pages': _pdf_pages(p) if f.endswith('.pdf') else None})
        labs = sorted((mat / 'Lernumgebung' / 'labs').glob('*.html')) if (mat / 'Lernumgebung' / 'labs').is_dir() else []
        card['labs'] = [str(x) for x in labs]
    if c.get('review') and Path(c['review']).exists():
        try:
            rv = json.loads(Path(c['review']).read_text(encoding='utf-8'))
            f = rv.get('findings') or []
            card['review'] = {'path': c['review'], 'verified': len(rv.get('verified') or []),
                              'open': [x for x in f if x.get('severity') in ('P0', 'P1') and not x.get('resolved')],
                              'open_all': [x for x in f if not x.get('resolved')],
                              'resolved': [x for x in f if x.get('resolved')], 'all': f}
        except ValueError:
            card['review'] = {'path': c['review'], 'error': 'unreadable'}
    fails = [k for k, v in card['dims'].items() if v == 'FAIL']
    open_p = card['review']['open'] if card['review'] and 'open' in card['review'] else None
    untested = [k for k, v in card['dims'].items() if v in ('NOT_TESTED', 'PARTIAL', None)]
    card['dims_not_tested'] = untested
    complete_gate = card['gate'] in ('READY', 'PUBLISHED', 'PASS')
    # never shown as fully checked while a gate is partial or a quality dimension was not tested
    card['status'] = ('FEHLER' if fails else 'OFFENE P0/P1-FACHBEFUNDE' if open_p else
                      'FACHREVIEW FEHLT' if open_p is None else
                      'TEILWEISE GEPRÜFT – MENSCHLICHE ABNAHME OFFEN' if (untested or not complete_gate) else
                      'TECHNISCH GEPRÜFT – MENSCHLICHE ABNAHME OFFEN')
    return card


def _rel(p, base):
    return os.path.relpath(p, base)


CSS = """:root{--bg:#f6f7f9;--card:#fff;--ink:#16243a;--muted:#5b6778;--line:#dde2ea;--accent:#1f5f99;--ok:#1d7a46;--warn:#9a6200;--bad:#b42318;--chip:#eef2f7}
@media (prefers-color-scheme:dark){:root{--bg:#0f141b;--card:#171e28;--ink:#e6ebf2;--muted:#9aa6b6;--line:#2a3442;--accent:#6aa9e8;--ok:#58c08a;--warn:#e0a640;--bad:#f07a6e;--chip:#222c39}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 60px}h1{font-size:1.6rem;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 22px}
.grid{display:grid;align-items:start;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;display:flex;flex-direction:column;gap:10px}
.card h2{font-size:1.05rem;margin:0}.dom{color:var(--muted);font-size:.85rem}.chap{font-weight:600}
.st{display:inline-block;font-size:.75rem;font-weight:700;letter-spacing:.02em;padding:3px 8px;border-radius:99px;background:var(--chip)}
.st.ok{color:var(--ok)}.st.warn{color:var(--warn)}.st.bad{color:var(--bad)}
ul.prod{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}ul.prod a{display:inline-block;padding:4px 9px;border:1px solid var(--line);border-radius:6px;color:var(--accent);text-decoration:none;font-size:.85rem}
ul.prod a:hover{border-color:var(--accent)}.pg{color:var(--muted);font-size:.75rem}
.q{display:grid;grid-template-columns:1fr auto;gap:2px 10px;font-size:.85rem}.q .v{font-weight:600}.v.PASS{color:var(--ok)}.v.FAIL{color:var(--bad)}.v.NOT_TESTED,.v.PARTIAL{color:var(--warn)}
h3{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:4px 0 0}
ol.hc{margin:0;padding-left:20px;font-size:.88rem}details{font-size:.82rem;color:var(--muted)}details summary{cursor:pointer}
details pre{white-space:pre-wrap;word-break:break-word;font-size:.75rem}table{border-collapse:collapse;width:100%;font-size:.8rem}td,th{border-bottom:1px solid var(--line);padding:3px 4px;text-align:left}
.top{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:22px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:1.4rem}.kpi span{color:var(--muted);font-size:.82rem}"""


def render(campaign, out_dir):
    root = campaign['output_root']
    ledger = json.loads(Path(campaign['ledger']).read_text(encoding='utf-8')) if campaign.get('ledger') and Path(campaign['ledger']).exists() else {}
    cards = [course_card(c, root, ledger) for c in campaign['courses']]
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    produced = sum(1 for c in cards if c['run'])
    open_p = sum(len(c['review']['open']) for c in cards if c.get('review') and 'open' in c['review'])
    open_all = sum(len(c['review']['open_all']) for c in cards if c.get('review') and 'open_all' in c['review'])
    no_review = [c['tag'] for c in cards if c['run'] and not (c.get('review') and 'open' in c['review'])]
    from datetime import datetime
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    hc = sum(len(c['human_checks']) for c in cards)
    parts = [f'<h1>{E(campaign["title"])}</h1><p class="sub">{E(campaign.get("subtitle", ""))}</p>',
             '<div class="top">'
             f'<div class="kpi"><b>{produced}/{len(cards)}</b><span>Kapitelpakete produziert</span></div>'
             f'<div class="kpi"><b>{len(ledger.get("calls", []))}/{ledger.get("limit", "–")}</b><span>neue Engine-Modellaufrufe (Budget)</span></div>'
             f'<div class="kpi"><b>{open_p}</b><span>offene P0/P1-Fachbefunde' + (f' (ohne Review: {", ".join(no_review)})' if no_review else '') + '</span></div>'
             f'<div class="kpi"><b>{open_all}</b><span>offene Fachbefunde gesamt (P0–P3)</span></div>'
             f'<div class="kpi"><b>{hc}</b><span>menschliche Prüfpunkte</span></div></div>'
             f'<p class="sub">Datenstand: {E(stamp)} · Ledger {len(ledger.get("calls", []))} Einträge · erzeugt aus status.json, quality_dossier.json, Reviews und Ledger</p><div class="grid">']
    for c in cards:
        cls = 'bad' if c['status'] in ('FEHLER', 'OFFENE P0/P1-FACHBEFUNDE', 'NICHT PRODUZIERT') else 'ok' if c['status'].startswith('TECHNISCH') else 'warn'
        h = (f'<section class="card"><div><h2>{E(c["name"])}</h2><div class="dom">{E(c["domain"])}</div></div>'
             f'<div class="chap">{E(c["title"])}</div><div><span class="st {cls}">{E(c["status"])}</span></div>')
        if c['products']:
            h += '<h3>Lernprodukte</h3><ul class="prod">' + ''.join(
                f'<li><a href="{E(_rel(p["path"], out_dir))}">{E(p["label"])}</a>' + (f' <span class="pg">{p["pages"]} S.</span>' if p['pages'] else '') + '</li>'
                for p in c['products']) + ''.join(
                f'<li><a href="{E(_rel(l, out_dir))}">Lab: {E(Path(l).stem.split("__")[-1].replace("-", " "))}</a></li>' for l in c.get('labs') or []) + '</ul>'
        if c['dims'] or c.get('review'):
            npass = sum(v == 'PASS' for v in c['dims'].values())
            nfail = sum(v == 'FAIL' for v in c['dims'].values())
            nt = c.get('dims_not_tested') or []
            h += ('<h3>Qualität</h3><div class="q">'
                  f'<span>Kapitel-Gate</span><span class="v {"PASS" if c.get("gate") in ("READY", "PUBLISHED", "PASS") else "PARTIAL"}">{E(c.get("gate"))}</span>'
                  f'<span>Automatische Prüfdimensionen</span>'
                  f'<span class="v {"FAIL" if nfail else "NOT_TESTED" if nt else "PASS"}">{npass} bestanden · {nfail} fehlgeschlagen · {len(nt)} nicht geprüft</span>')
            if nt:
                h += f'<span style="grid-column:1/-1;color:var(--muted)">nicht geprüft: {E(", ".join(DIM.get(k, k) for k in nt))}</span>'
            if c.get('review') and 'open' in c['review']:
                rv = c['review']
                h += (f'<span>Unabhängiger Agenten-Fachreview</span><span class="v {"FAIL" if rv["open"] else "NOT_TESTED" if rv["open_all"] else "PASS"}">'
                      f'{len(rv["all"])} Befunde · {len(rv["open"])} offen P0/P1 · {len(rv["open_all"]) - len(rv["open"])} offen P2/P3 · {len(rv["resolved"])} behoben</span>')
            h += '<span>Menschliche Fachabnahme</span><span class="v NOT_TESTED">offen</span></div>'
        if c['human_checks']:
            h += '<h3>Menschliche Prüfung erforderlich</h3><ol class="hc">' + ''.join(f'<li>{E(x)}</li>' for x in c['human_checks']) + '</ol>'
        det = {'run': c['run'], 'chapter_id': c['chapter_id'], 'gate': c.get('gate'), 'academic_release': c.get('academic'),
               'engine_calls': [{k: x.get(k) for k in ('n', 'role', 'at')} for x in c['calls']]}
        h += f'<details><summary>Technische Details</summary><pre>{E(json.dumps(det, ensure_ascii=False, indent=1))}</pre>'
        if c.get('review') and c['review'].get('all'):
            h += '<table><tr><th>Befund</th><th>Schwere</th><th>Status</th></tr>' + ''.join(
                f'<tr><td>{E((x.get("problem") or x.get("claim") or "")[:160])}</td><td>{E(x.get("severity"))}</td>'
                f'<td>{E("behoben" if x.get("resolved") else "offen")}</td></tr>' for x in c['review']['all']) + '</table>'
        h += '</details></section>'
        parts.append(h)
    parts.append('</div>')
    page = ('<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(campaign.get("short_title", "Exam Mastery Piloten"))}</title><style>{CSS}</style></head><body><main>' + ''.join(parts) + '</main></body></html>')
    (out_dir / 'index.html').write_text(page, encoding='utf-8')
    (out_dir / 'dashboard_data.json').write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding='utf-8')
    return out_dir / 'index.html', cards


def main(argv):
    if len(argv) < 2:
        print('usage: python -m exam_mastery.campaign <campaign.json> <out_dir>'); return 2
    p, cards = render(json.loads(Path(argv[0]).read_text(encoding='utf-8')), argv[1])
    print(json.dumps({'dashboard': str(p), 'courses': [{k: c.get(k) for k in ('tag', 'status', 'run')} for c in cards]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
