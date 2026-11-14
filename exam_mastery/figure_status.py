"""One figure-status file per chapter (em-figure-triage-v1).

The source-figure PDF, the quality dossier and the competency matrix all read this file, so they cannot drift apart.
Every slide that carries a figure gets exactly one status with a reason:

CONTENT_INTEGRATED      the figure's subject content is taught in the learning material
TEXT_EQUIVALENT         the figure adds nothing beyond the slide text (no additional learning content)
DECORATIVE              photo, logo, divider or ornament without subject content
NOT_RELIABLY_EVALUATED  not (yet) reliably read; its content is not part of the material

Readings are the agent's own image understanding, never human-checked; the PDF and the dossier say so.
"""
import json
from collections import Counter
from pathlib import Path

LABEL = {'CONTENT_INTEGRATED': 'Inhalt fachlich integriert',
         'TEXT_EQUIVALENT': 'Kein zusätzlicher eigenständiger Lerninhalt (Bild entspricht dem Folientext)',
         'DECORATIVE': 'Dekorativ (kein fachlicher Inhalt)',
         'NOT_RELIABLY_EVALUATED': 'Inhalt noch nicht zuverlässig ausgewertet (nicht Teil des Materials)'}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate(triage, figure_pages=None):
    """Problems: unknown status, missing reason, duplicate slide, figure page without status."""
    p, seen = [], set()
    for s in triage.get('slides', []):
        if s.get('status') not in LABEL:
            p.append(f"slide {s.get('slide')}: unknown status {s.get('status')!r}")
        if not str(s.get('reason') or '').strip():
            p.append(f"slide {s.get('slide')}: no reason")
        if s.get('slide') in seen:
            p.append(f"slide {s.get('slide')}: listed twice")
        seen.add(s.get('slide'))
    for pg in figure_pages or []:
        if pg not in seen:
            p.append(f'slide {pg}: figure without status')
    return p


def counts(triage):
    c = Counter(s['status'] for s in triage.get('slides', []))
    return {k: c.get(k, 0) for k in LABEL}


def summary(triage):
    c = counts(triage)
    return '; '.join(f'{v} {LABEL[k].split(" (")[0]}' for k, v in c.items() if v)


_PLAIN = str.maketrans({'–': '-', '—': '-', '→': '->', '„': '"', '“': '"', '”': '"', '‘': "'", '’': "'", '…': '...', '\u2009': ' ', '\u202f': ' '})


def _plain(t):
    """The PDF base font has no typographic dashes or quotes; map them to ASCII instead of printing '?'."""
    return str(t).translate(_PLAIN)


def render_pdf(triage, source_pdf, out_pdf, title='Quellenabbildungen'):
    """Cover with the counts, then one page per slide: status, reason, the slide itself (JPEG, print quality)."""
    import pymupdf
    src = pymupdf.open(source_pdf)
    doc = pymupdf.open()
    cover = doc.new_page(width=595, height=842)
    c = counts(triage)
    lines = [title, '',
             'Alle Folien dieses Kapitels mit Abbildungen, unverändert und mit ihrem aktuellen Status. Die Einstufung beruht auf dem '
             'Bildverständnis des Agenten und ist NICHT menschlich geprüft. Derselbe Status steht im Qualitätsdossier und in der Kompetenzmatrix.', '']
    lines += [f'{c[k]:>2} Folien: {LABEL[k]}' for k in LABEL]
    lines += ['', f"Stand: {triage.get('as_of', '')}", f"{len(triage.get('slides', []))} Folien."]
    cover.insert_textbox(pymupdf.Rect(50, 60, 545, 800), _plain('\n'.join(lines)), fontsize=11)
    for s in sorted(triage['slides'], key=lambda x: x['slide']):
        pg = doc.new_page(width=842, height=595)
        head = f"{Path(source_pdf).name}, Folie {s['slide']} · {LABEL[s['status']]}\n{s['reason']}"
        pg.insert_textbox(pymupdf.Rect(30, 14, 812, 72), _plain(head), fontsize=9)
        pix = src[s['slide'] - 1].get_pixmap(dpi=110)
        pg.insert_image(pymupdf.Rect(30, 78, 812, 578), stream=pix.tobytes('jpeg', jpg_quality=85), keep_proportion=True)
    doc.set_metadata({'title': title, 'creator': 'Exam Mastery figure_status'})
    doc.save(out_pdf, garbage=3, deflate=True)
    n = doc.page_count
    doc.close(); src.close()
    return n


def matrix(triage, competencies, stages=(), cards=()):
    """Competency matrix rows that carry the figure status of the slides behind each competency."""
    rows = []
    for kc in competencies:
        sl = [s for s in triage.get('slides', []) if kc['key'] in (s.get('kc') or [])]
        items = [it['id'] for st in stages for it in st['items'] if kc['key'] in it.get('kc_keys', [])]
        rows.append({'kc': kc['key'], 'kompetenz': kc.get('label', ''), 'operation': kc.get('operation', ''),
                     'aufgaben': ' '.join(items),
                     'abbildungen': ' '.join(f"F{s['slide']}:{s['status']}" for s in sl),
                     'offene_abbildungen': ' '.join(f"F{s['slide']}" for s in sl if s['status'] == 'NOT_RELIABLY_EVALUATED')})
    return rows
