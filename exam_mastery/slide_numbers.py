"""Printed slide numbers vs. PDF pages (B34).

Lecture PDFs often print a slide number that differs from the PDF page: hidden or removed slides shift the count,
and title or section slides carry no number. A reference "Folie 23" that actually means "PDF page 23" sends the
student to the wrong slide. This module reads the printed number from the footer band of every page and returns
a verified mapping. Pages without a readable number get an inferred number from their neighbours' offset and are
marked as such.

Subject-independent: it only assumes that a slide number is a bare integer in the bottom band of the page.
"""
import re

FOOT = 0.85          # bottom band (fraction of page height) where slide numbers are printed
MAX_OFFSET = 5       # |printed - pdf_page| larger than this is not taken as a slide number


def read_page_numbers(pdf_path):
    """[(pdf_page, [candidate integers in the footer band, top to bottom])]"""
    import pymupdf
    out = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc):
            h = page.rect.height
            cands = sorted((w[1], int(w[4])) for w in page.get_text('words')
                           if w[1] > h * FOOT and re.fullmatch(r'\d{1,4}', w[4]))
            out.append((i + 1, [n for _, n in cands]))
    return out


def build_map(pages):
    """pages: [(pdf_page, candidates)] -> {pdf_page: {'slide': n, 'basis': 'printed'|'inferred'|'none'}}.

    A candidate counts as the printed slide number when it is within MAX_OFFSET of the page and does not break the
    monotone order. Missing numbers are inferred only when the previous and next printed pages have the same offset
    (otherwise the page stays 'none': guessing across a jump would put a wrong number in the book)."""
    res, last = {}, 0
    for pg, cands in pages:
        hit = next((c for c in reversed(cands) if abs(c - pg) <= MAX_OFFSET and c > last), None)
        if hit is not None:
            res[pg] = {'slide': hit, 'basis': 'printed'}
            last = hit
        else:
            res[pg] = {'slide': None, 'basis': 'none'}
    keys = sorted(res)
    for i, pg in enumerate(keys):
        if res[pg]['basis'] != 'none':
            continue
        prev = next((k for k in reversed(keys[:i]) if res[k]['basis'] == 'printed'), None)
        nxt = next((k for k in keys[i + 1:] if res[k]['basis'] == 'printed'), None)
        offs = {res[k]['slide'] - k for k in (prev, nxt) if k is not None}
        if prev is not None and nxt is not None and len(offs) == 1:
            res[pg] = {'slide': pg + offs.pop(), 'basis': 'inferred'}
    return res


def summary(mapping):
    """Offset segments, for the source report: [(first_pdf_page, last_pdf_page, offset)]."""
    segs = []
    for pg in sorted(mapping):
        s = mapping[pg]['slide']
        if s is None:
            continue
        off = s - pg
        if segs and segs[-1][2] == off and segs[-1][1] == pg - 1:
            segs[-1] = (segs[-1][0], pg, off)
        else:
            segs.append((pg, pg, off))
    return segs


REF = re.compile(r'(?P<file>[^;]+?\.pdf) S\. (?P<page>\d+)')


def label(src, maps):
    """'02 - X.pdf S. 23; 02 - X.pdf S. 25' -> 'Folie 24, 26' using maps {file name: mapping}. Pages without a known
    slide number keep the PDF page ('PDF-S. 13'), so nothing is silently renumbered."""
    slides, pdfp = [], []
    for m in REF.finditer(str(src or '')):
        mp = maps.get(m['file'].strip())
        pg = int(m['page'])
        n = (mp or {}).get(pg, {}).get('slide')
        (slides if n is not None else pdfp).append(n if n is not None else pg)
    parts = []
    if slides:
        u = sorted(set(slides))
        parts.append(('Folie ' if len(u) == 1 else 'Folien ') + ', '.join(map(str, u)))
    if pdfp:
        parts.append('PDF-S. ' + ', '.join(map(str, sorted(set(pdfp)))))
    return ' · '.join(parts)


def is_slide_deck(pdf_path):
    """A deck of slides is (mostly) landscape. Portrait documents (scripts, sheets) keep page references."""
    import pymupdf
    with pymupdf.open(pdf_path) as doc:
        n = doc.page_count
        land = sum(1 for p in doc if p.rect.width > p.rect.height)
    return n > 0 and land / n >= 0.8


def course_maps(manifest, root=None, source_ids=None):
    """{pdf file name: {pdf_page: {...}}} for every slide deck of the course that is readable; plus a report.
    A deck is only used when its bytes still match the inventory hash (the numbers must belong to the analysed file).
    References in the book name a file only by its base name, so a base name shared by two decks in scope is ambiguous:
    such decks get no map at all (their references stay PDF pages) instead of borrowing the other deck's numbers.
    `source_ids` restricts the scope to the chapter's own sources."""
    import hashlib
    from pathlib import Path
    root = Path(str(root or manifest.get('root') or ''))
    maps, report = {}, []
    scope = [s for s in manifest.get('sources', []) if source_ids is None or s.get('source_id') in set(source_ids)]
    names = [Path(str(s.get('relative_path') or '')).name for s in scope]
    for s in scope:
        rel = str(s.get('relative_path') or '')
        if rel.lower().endswith('.pdf') and names.count(Path(rel).name) > 1:
            report.append({'file': rel, 'error': 'AMBIGUOUS_FILE_NAME'})
            continue
        f = root / rel
        if not rel.lower().endswith('.pdf') or not f.is_file():
            continue
        if s.get('raw_sha256') and hashlib.sha256(f.read_bytes()).hexdigest() != s['raw_sha256']:
            report.append({'file': Path(rel).name, 'error': 'SOURCE_CHANGED_SINCE_INVENTORY'})
            continue
        try:
            if not is_slide_deck(f):
                continue
            mp = build_map(read_page_numbers(f))
        except Exception as e:                          # unreadable deck: references stay PDF pages
            report.append({'file': Path(rel).name, 'error': type(e).__name__})
            continue
        maps[Path(rel).name] = {str(k): v for k, v in mp.items()}
        report.append({'file': Path(rel).name, 'pages': len(mp), 'printed': sum(v['basis'] == 'printed' for v in mp.values()),
                       'inferred': sum(v['basis'] == 'inferred' for v in mp.values()), 'none': sum(v['basis'] == 'none' for v in mp.values()),
                       'offset_segments': summary(mp)})
    return maps, report
