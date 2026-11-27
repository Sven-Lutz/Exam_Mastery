"""P1: source-faithful, element-level inventory of ONE arbitrary course root (em-source-v1).

Guarantees
- Exactly one input: a local root directory. No subject, path convention or file selection.
- Every file becomes a source record; every non-ok outcome is an explicit gap (no silent drops).
- Elements carry locators (page/slide/cell/paragraph/line/row), raw and normalized text, separate
  raw_span_hash / extraction_hash, parse method, status and confidence.
- Visual content (PDF images/vector drawings, PPTX pictures/charts/shapes, DOCX images, notebook
  plots, image files) is recorded as its own element with an asset where one can be exported.
  A PDF raster is NEVER used as a substitute for a missing PPTX slide render.
- Originals are read-only; output must live outside the root. Normalization never overwrites raw text.
- Source content is untrusted data. Nothing is executed; instruction-like text is only flagged.
- Online references are recorded. Without an injected fetcher (default) nothing is downloaded and the
  status is NOT_FETCHED_OFFLINE_POLICY - never a fabricated success.
"""
from __future__ import annotations
import ast, csv, hashlib, io, json, mimetypes, os, re, zipfile
from pathlib import Path
from .common import write_json, sha_file, sha_bytes, ContractError, is_transient_file, SYSTEM_METADATA_NAMES
from .source_schema import SOURCE_SCHEMA, BLOCKING_GAPS, validate_source_manifest
from .discovery import classify, TextHTML, clean_url, URL

PARSER_VERSION = 'em-fidelity-1'
MAX_FILE = 40 * 1024 * 1024
MAX_TABLE_ROWS = 5000
TEXT_EXT = {'.txt', '.md', '.markdown', '.rst'}
TEX_EXT = {'.tex'}
CODE_EXT = {'.py', '.r', '.sql', '.js', '.ts', '.c', '.cpp', '.h', '.java', '.sh', '.m', '.jl', '.rs', '.go'}
DATA_TEXT_EXT = {'.json', '.yaml', '.yml', '.xml', '.bib'}
TABLE_EXT = {'.csv', '.tsv'}
RASTER_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff', '.bmp', '.jpe'}
VECTOR_IMAGE_EXT = {'.svg'}
HTML_EXT = {'.html', '.htm'}
SUPPORTED = {'.pdf': 'pdf', '.pptx': 'pptx', '.docx': 'docx', '.ipynb': 'notebook', '.xlsx': 'spreadsheet',
             '.xlsm': 'spreadsheet', **{e: 'text' for e in TEXT_EXT}, **{e: 'tex' for e in TEX_EXT},
             **{e: 'code' for e in CODE_EXT}, **{e: 'structured_text' for e in DATA_TEXT_EXT},
             **{e: 'table' for e in TABLE_EXT}, **{e: 'image' for e in RASTER_EXT},
             **{e: 'vector_image' for e in VECTOR_IMAGE_EXT}, **{e: 'html' for e in HTML_EXT}}
MATH_CHARS = set('∑∫∏√∞≤≥≠≈∈∉∀∃∂∇→⇒⇔αβγδεθλμσφψωΣΠΩ±×÷⊂⊆∪∩')
INSTRUCTION_LIKE = re.compile(
    r'ignore (all |any )?(previous|prior|above) instructions|disregard .{0,30}instructions|system prompt|'
    r'you are now|ignoriere .{0,40}anweisungen|vergiss .{0,30}anweisungen|führe .{0,40}(befehl|code) aus|'
    r'run the following command|rm -rf|curl .{0,80}\| ?sh', re.I)
OMML_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
EMU_PER_PT = 12700


def _h(text):
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def _norm(text):
    return re.sub(r'\s+', ' ', (text or '')).strip()


def _sid(rel):
    return 'src-' + _h('local|' + rel)[:16]


class _Collector:
    """Accumulates elements, assets and gaps for one source."""

    def __init__(self, sid, out_assets):
        self.sid = sid; self.elements = []; self.gaps = []; self.out_assets = out_assets; self.links = []

    def element(self, kind, locator, text='', status='ok', confidence='HIGH', parse_method='', structure=None,
                asset=None, fidelity=None, flags=None, raw_bytes=None, auto_links=True):
        loc_str = self.sid + '/' + '/'.join(f'{k}-{v}' for k, v in locator.items() if k != 'bbox')
        n = sum(1 for e in self.elements if e['locator_str'].startswith(loc_str + '#'))
        loc_str = f'{loc_str}#{kind}-{n + 1}'
        flags = list(flags or [])
        if text and INSTRUCTION_LIKE.search(text):
            flags.append('instruction_like_untrusted_text')
            self.gap('UNTRUSTED_INSTRUCTION_LIKE_TEXT', 'info', 'Instruction-like text kept as inert data', loc_str)
        raw_hash = sha_bytes(raw_bytes) if raw_bytes is not None else _h(text)
        e = {'element_id': 'el-' + _h(loc_str)[:16], 'source_id': self.sid, 'locator': locator, 'locator_str': loc_str,
             'kind': kind, 'text': text, 'normalized_text': _norm(text), 'structure': structure, 'asset': asset,
             'raw_span_hash': raw_hash, 'extraction_hash': _h(PARSER_VERSION + '|' + kind + '|' + _norm(text) + '|' +
                                                              json.dumps(structure, sort_keys=True, default=str)),
             'status': status, 'confidence': confidence, 'parse_method': parse_method,
             'fidelity': fidelity or {}, 'flags': flags}
        self.elements.append(e)
        for u in (URL.findall(text or '') if auto_links else []):
            self.links.append((clean_url(u), e['element_id'], ''))
        return e

    def gap(self, code, severity, detail, locator=None):
        self.gaps.append({'source_id': self.sid, 'code': code, 'severity': severity, 'detail': detail,
                          'locator_str': locator})

    def asset(self, data: bytes, ext, origin):
        digest = sha_bytes(data)
        target = self.out_assets / self.sid / (digest[:20] + ext)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(data)
        info = {'path': str(target.relative_to(self.out_assets.parent)), 'sha256': digest, 'bytes': len(data),
                'mime': mimetypes.types_map.get(ext, 'application/octet-stream'), 'origin': origin}
        try:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as im:
                info['width'], info['height'] = im.size
        except Exception:
            info['width'] = info['height'] = None
        return info


def _formula_like(text):
    return sum(ch in MATH_CHARS for ch in text) >= 2 or bool(re.search(r'[A-Za-z]\s*[_^]\s*\{?\w', text) and '=' in text)


# ---------------------------------------------------------------- format parsers

_PROBE = ("import sys,pymupdf\n"
          "for pg in pymupdf.open(sys.argv[1]):\n"
          "    pg.find_tables()\n")


def layout_tables_safe(path):
    """PyMuPDF's ONNX layout model (used by find_tables) can crash the whole interpreter (SIGSEGV) on some PDFs,
    which cannot be caught in-process. Probe each PDF once in a child process (cached by content hash); a crash
    means table detection for that file runs without the layout model. Unaffected files keep identical results."""
    import subprocess, sys
    sha = sha_file(path)
    cache = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'exam-mastery-layout-probe' / f'{sha}.json'
    if cache.exists():
        try:
            return json.loads(cache.read_text())['safe']
        except (ValueError, KeyError):
            pass
    try:
        r = subprocess.run([sys.executable, '-c', _PROBE, str(path)], capture_output=True, timeout=900)
        safe = r.returncode == 0 or r.returncode > 0 and b'Traceback' in r.stderr
    except subprocess.TimeoutExpired:
        safe = False
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({'safe': safe, 'file': Path(path).name}))
    return safe


def _parse_pdf(path, c):
    import pymupdf
    method = f'pymupdf-{pymupdf.VersionBind}'
    use_layout = layout_tables_safe(path)
    if not use_layout:
        c.gap('TABLE_LAYOUT_MODEL_UNSTABLE', 'info', 'PyMuPDF layout model crashed on this file; tables detected from ruling lines only')
    with pymupdf.open(path) as doc:
        if doc.page_count == 0:
            c.gap('EMPTY_SOURCE', 'blocking', 'PDF has no pages')
        for pno, page in enumerate(doc, 1):
            loc = {'page': pno}
            d = page.get_text('dict')
            text_blocks = [b for b in d['blocks'] if b.get('type') == 0]
            has_text = False
            for b in text_blocks:
                text = '\n'.join(''.join(s['text'] for s in line['spans']) for line in b['lines']).strip()
                if not text:
                    continue
                has_text = True
                sizes = [s['size'] for line in b['lines'] for s in line['spans']]
                bbox = [round(x, 1) for x in b['bbox']]
                kind = 'heading' if sizes and max(sizes) >= 15 and len(text) < 160 else 'paragraph'
                c.element(kind, {**loc, 'bbox': bbox}, text, parse_method=method + '.text_dict',
                          structure={'font_size': round(max(sizes), 1)} if sizes else None)
                if _formula_like(text):
                    c.element('formula', {**loc, 'bbox': bbox}, text, status='uncertain', confidence='LOW',
                              parse_method=method + '.text_dict', fidelity={'structure_preserved': False,
                              'representation': 'linearized_text_layer', 'note': 'PDF text layer has no math structure'})
                    c.gap('FORMULA_LINEARIZED', 'info', 'Formula only as linearized PDF text', c.elements[-1]['locator_str'])
            images = page.get_images(full=True)
            for img in images:
                xref = img[0]
                try:
                    ext_img = doc.extract_image(xref)
                    rects = page.get_image_rects(xref)
                    bbox = [round(x, 1) for x in rects[0]] if rects else None
                    asset = c.asset(ext_img['image'], '.' + ext_img.get('ext', 'png'), 'pdf_embedded_image')
                    c.element('image', {**loc, 'bbox': bbox, 'xref': xref}, '', status='uncertain', confidence='UNKNOWN',
                              parse_method=method + '.extract_image', asset=asset, raw_bytes=ext_img['image'],
                              fidelity={'structure_preserved': False, 'note': 'Embedded raster exported unchanged; not interpreted'})
                except Exception as e:
                    c.element('image', {**loc, 'xref': xref}, '', status='failed', confidence='UNKNOWN',
                              parse_method=method, fidelity={'error': f'{type(e).__name__}: {e}'})
                    c.gap('VISUAL_UNCERTAIN', 'blocking', f'Embedded image could not be exported: {e}')
            try:
                tables = (page.find_tables() if use_layout else page.find_tables(use_layout=False)).tables
            except Exception:
                tables = []
            for t in tables:
                rows = t.extract()
                c.element('table', {**loc, 'bbox': [round(x, 1) for x in t.bbox]},
                          '\n'.join(' | '.join(str(x or '') for x in r) for r in rows), status='partial', confidence='MEDIUM',
                          parse_method=method + '.find_tables', structure={'rows': rows},
                          fidelity={'structure_preserved': True, 'note': 'Grid recovered heuristically from ruling lines'})
            drawings = page.get_drawings()
            needs_render = bool(images) or len(drawings) >= 3 or any(e['kind'] == 'formula' and e['locator'].get('page') == pno
                                                                    for e in c.elements)
            if len(drawings) >= 3:
                rects = [dr['rect'] for dr in drawings]
                bbox = [round(min(r.x0 for r in rects), 1), round(min(r.y0 for r in rects), 1),
                        round(max(r.x1 for r in rects), 1), round(max(r.y1 for r in rects), 1)]
                c.element('diagram', {**loc, 'bbox': bbox}, '', status='uncertain', confidence='LOW',
                          parse_method=method + '.get_drawings', structure={'vector_paths': len(drawings)},
                          fidelity={'structure_preserved': False, 'note': 'Vector graphic detected; semantics not extracted'})
                c.gap('VISUAL_UNCERTAIN', 'blocking', f'Page {pno}: vector diagram requires visual review',
                      c.elements[-1]['locator_str'])
            if needs_render:
                png = page.get_pixmap(matrix=pymupdf.Matrix(1.25, 1.25)).tobytes('png')
                c.element('rendered_page', loc, '', status='uncertain', confidence='UNKNOWN', parse_method=method + '.pixmap',
                          asset=c.asset(png, '.png', 'pdf_page_render'),
                          fidelity={'structure_preserved': False, 'note': 'Raster for visual review only; not structure'})
            if not has_text:
                if images or drawings:
                    c.gap('TEXT_LAYER_MISSING', 'blocking', f'Page {pno}: no text layer (scan?); OCR not available offline')
                else:
                    c.gap('EMPTY_PAGE', 'info', f'Page {pno}: empty')


def _bbox(shape):
    try:
        return [round(shape.left / EMU_PER_PT, 1), round(shape.top / EMU_PER_PT, 1),
                round((shape.left + shape.width) / EMU_PER_PT, 1), round((shape.top + shape.height) / EMU_PER_PT, 1)]
    except Exception:
        return None


def _omml(xml_el, c, loc, method):
    found = 0
    for m in xml_el.iter('{%s}oMath' % OMML_NS):
        linear = ''.join(t.text or '' for t in m.iter('{%s}t' % OMML_NS))
        from lxml import etree
        raw = etree.tostring(m, encoding='unicode')
        c.element('formula', loc, linear, status='partial', confidence='MEDIUM', parse_method=method + '.omml',
                  structure={'omml': raw[:20000], 'omml_truncated': len(raw) > 20000},
                  fidelity={'structure_preserved': True, 'representation': 'OMML (raw XML kept) + linear text',
                            'note': 'No OMML->LaTeX conversion; linear text loses layout'})
        found += 1
    return found


MAX_OFFICE_MEMBERS = 20000
MAX_OFFICE_EXPANDED_BYTES = 200 * 1024 * 1024


def _check_office_archive(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_OFFICE_MEMBERS or sum(item.file_size for item in members) > MAX_OFFICE_EXPANDED_BYTES:
            raise ValueError('Office archive expansion exceeds safety limits')


def _parse_pptx(path, c, sibling_pdfs):
    _check_office_archive(path)
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    import pptx as _pptx
    method = f'python-pptx-{_pptx.__version__}'
    prs = Presentation(str(path))
    if not len(prs.slides):
        c.gap('EMPTY_SOURCE', 'blocking', 'Presentation has no slides')

    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from walk(sh.shapes)
            else:
                yield sh

    for sno, slide in enumerate(prs.slides, 1):
        loc = {'slide': sno}
        content = 0; plain_shapes = []
        title_id = slide.shapes.title.shape_id if slide.shapes.title is not None else None
        for sh in walk(slide.shapes):
            sloc = {**loc, 'shape': sh.shape_id, 'bbox': _bbox(sh)}
            if getattr(sh, 'has_text_frame', False) and sh.has_text_frame and sh.text_frame.text.strip():
                kind = 'heading' if sh.shape_id == title_id else 'paragraph'
                c.element(kind, sloc, sh.text_frame.text, parse_method=method + '.text_frame'); content += 1
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(sh, 'image') and sh.shape_type != MSO_SHAPE_TYPE.PLACEHOLDER:
                try:
                    img = sh.image
                    c.element('image', sloc, getattr(sh, 'name', ''), status='uncertain', confidence='UNKNOWN',
                              parse_method=method + '.picture_blob', raw_bytes=img.blob,
                              asset=c.asset(img.blob, '.' + img.ext, 'pptx_picture_blob'),
                              fidelity={'structure_preserved': False, 'note': 'Original slide image exported from PPTX package'})
                    content += 1
                except Exception:
                    pass
            if getattr(sh, 'has_table', False) and sh.has_table:
                rows = [[cell.text for cell in r.cells] for r in sh.table.rows]
                c.element('table', sloc, '\n'.join(' | '.join(r) for r in rows), parse_method=method + '.table',
                          structure={'rows': rows}, fidelity={'structure_preserved': True}); content += 1
            if getattr(sh, 'has_chart', False) and sh.has_chart:
                ch = sh.chart
                try:
                    cats = [str(x) for x in ch.plots[0].categories]
                except Exception:
                    cats = []
                series = []
                for plot in ch.plots:
                    for s in plot.series:
                        try:
                            series.append({'name': s.name, 'values': list(s.values)})
                        except Exception:
                            series.append({'name': getattr(s, 'name', None), 'values': None})
                title = ch.chart_title.text_frame.text if ch.has_title else ''
                c.element('chart', sloc, title, status='partial', confidence='MEDIUM', parse_method=method + '.chart',
                          structure={'chart_type': str(ch.chart_type), 'categories': cats, 'series': series},
                          fidelity={'structure_preserved': True, 'note': 'Chart data from embedded XML; styling not kept'})
                content += 1
            if sh.shape_type in (MSO_SHAPE_TYPE.AUTO_SHAPE, MSO_SHAPE_TYPE.FREEFORM, MSO_SHAPE_TYPE.LINE) or \
                    getattr(sh, 'shape_type', None) is None and not getattr(sh, 'has_text_frame', False):
                plain_shapes.append(sh)
        content += _omml(slide.element, c, loc, method)
        if len(plain_shapes) >= 2:
            c.element('diagram', loc, ' / '.join(s.text_frame.text for s in plain_shapes if getattr(s, 'has_text_frame', False)),
                      status='uncertain', confidence='LOW', parse_method=method + '.autoshapes',
                      structure={'shapes': [{'id': s.shape_id, 'type': str(s.shape_type), 'bbox': _bbox(s)} for s in plain_shapes]},
                      fidelity={'structure_preserved': False, 'note': 'Shape geometry kept; diagram meaning not inferred'})
            c.gap('VISUAL_UNCERTAIN', 'blocking', f'Slide {sno}: shape diagram requires visual review',
                  c.elements[-1]['locator_str'])
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            c.element('notes', loc, slide.notes_slide.notes_text_frame.text, parse_method=method + '.notes')
        if not content:
            c.gap('EMPTY_PAGE', 'info', f'Slide {sno}: no extractable content')
    # Faithful slide rendering needs an office renderer, which is not part of this engine.
    # A same-named PDF is recorded as a candidate relation only, never as a substitute render.
    c.gap('SLIDE_RENDER_UNAVAILABLE', 'blocking',
          'No faithful PPTX slide renderer available; slide layout not visually verified. '
          + ('PDF export candidates (NOT used as substitute): ' + ', '.join(sibling_pdfs) if sibling_pdfs else ''))


def _parse_docx(path, c):
    _check_office_archive(path)
    from docx import Document
    import docx as _docx
    method = f'python-docx-{getattr(_docx, "__version__", "?")}'
    doc = Document(str(path))
    c.gap('PAGE_UNKNOWN', 'info', 'DOCX has no fixed pages; paragraph locators used')
    for i, p in enumerate(doc.paragraphs, 1):
        loc = {'paragraph': i}
        style = p.style.name if p.style is not None else ''
        if p.text.strip():
            kind = 'heading' if style.lower().startswith(('heading', 'überschrift', 'title')) else \
                'list_item' if 'list' in style.lower() else 'paragraph'
            lvl = re.search(r'(\d+)$', style) if kind == 'heading' else None
            c.element(kind, loc, p.text, parse_method=method + '.paragraph',
                      structure={'style': style, 'level': int(lvl.group(1)) if lvl else (0 if style.lower().startswith('title') else None)})
        _omml(p._p, c, loc, method)
        for blip in p._p.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            rid = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            try:
                part = doc.part.related_parts[rid]
                c.element('image', loc, '', status='uncertain', confidence='UNKNOWN', parse_method=method + '.blip',
                          raw_bytes=part.blob, asset=c.asset(part.blob, Path(part.partname).suffix or '.bin', 'docx_inline_image'),
                          fidelity={'structure_preserved': False})
            except Exception as e:
                c.gap('VISUAL_UNCERTAIN', 'blocking', f'DOCX image not exportable: {e}')
    for t, tbl in enumerate(doc.tables, 1):
        rows = [[cell.text for cell in r.cells] for r in tbl.rows]
        c.element('table', {'table': t}, '\n'.join(' | '.join(r) for r in rows), parse_method=method + '.table',
                  structure={'rows': rows}, fidelity={'structure_preserved': True})


FORMULA_BLOCK = re.compile(r'\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\begin\{(equation|align|gather|multline)\*?\}(.+?)\\end\{\3\*?\}', re.S)
INLINE_FORMULA = re.compile(r'(?<![\\$])\$([^$\n]+?)\$(?!\$)')
MD_IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)\)')
TEX_IMAGE = re.compile(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')


HEADING_LINE = re.compile(r'^\s*(#{1,6}\s|\\(chapter|section|subsection)\*?\{)')


def _text_blocks(text):
    """Blank-line separated blocks with 1-based line ranges; fenced code kept intact."""
    lines = text.splitlines(); blocks = []; start = None; buf = []; fence = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('```'):
            fence = not fence
        if not fence and HEADING_LINE.match(line):  # a heading is always its own block
            if buf:
                blocks.append((start, i - 1, '\n'.join(buf))); buf = []
            blocks.append((i, i, line)); continue
        if not line.strip() and not fence:
            if buf:
                blocks.append((start, i - 1, '\n'.join(buf))); buf = []
            continue
        if not buf:
            start = i
        buf.append(line)
    if buf:
        blocks.append((start, len(lines), '\n'.join(buf)))
    return blocks


def _parse_markup(path, c, root, tex=False):
    text = path.read_text(encoding='utf-8-sig')
    method = PARSER_VERSION + ('.tex' if tex else '.markdown')
    if not text.strip():
        c.gap('EMPTY_SOURCE', 'blocking', 'File contains no text'); return
    for a, b, block in _text_blocks(text):
        loc = {'lines': f'{a}-{b}'}
        first = block.lstrip()
        if tex:
            m = re.match(r'\\(chapter|section|subsection)\*?\{(.+?)\}', first)
            kind = 'heading' if m else 'code' if first.startswith('\\begin{lstlisting}') else 'paragraph'
            env = re.match(r'\\begin\{(definition|theorem|lemma|proof|satz|beweis|example|corollary)\}', first)
            struct = {'level': {'chapter': 1, 'section': 2, 'subsection': 3}[m.group(1)]} if m else {'environment': env.group(1)} if env else None
            c.element(kind, loc, m.group(2) if m else block, parse_method=method, structure=struct)
        else:
            m = re.match(r'(#{1,6})\s+(.+)', first)
            if m:
                c.element('heading', loc, m.group(2).strip(), parse_method=method, structure={'level': len(m.group(1))})
            elif first.startswith('```'):
                c.element('code', loc, block, parse_method=method, flags=['code_not_executed'])
            elif re.match(r'([-*•]|\d+[.)])\s', first):
                for j, item in enumerate(re.split(r'\n(?=\s*(?:[-*•]|\d+[.)])\s)', block), 1):
                    c.element('list_item', {**loc, 'item': j}, re.sub(r'^\s*(?:[-*•]|\d+[.)])\s+', '', item), parse_method=method)
            else:
                c.element('paragraph', loc, block, parse_method=method)
        for fm in FORMULA_BLOCK.finditer(block):
            latex = next(g for g in (fm.group(1), fm.group(2), fm.group(4)) if g)
            c.element('formula', {**loc, 'display': True}, latex.strip(), parse_method=method + '.latex',
                      structure={'latex': latex.strip()}, fidelity={'structure_preserved': True, 'representation': 'LaTeX source'})
        for fm in INLINE_FORMULA.finditer(FORMULA_BLOCK.sub('', block)):
            c.element('formula', {**loc, 'display': False}, fm.group(1), parse_method=method + '.latex',
                      structure={'latex': fm.group(1)}, fidelity={'structure_preserved': True, 'representation': 'LaTeX source'})
        refs = [(m.group(2), m.group(1)) for m in MD_IMAGE.finditer(block)] + [(m.group(1), '') for m in TEX_IMAGE.finditer(block)]
        for ref, alt in refs:
            if ref.startswith(('http://', 'https://')):
                c.links.append((ref, None, alt)); continue
            target = (path.parent / ref).resolve()
            if tex and not target.suffix:
                target = next((target.with_suffix(s) for s in ('.png', '.pdf', '.jpg') if target.with_suffix(s).exists()), target)
            inside = root == target or root in target.parents
            ok = inside and target.is_file()
            e = c.element('figure', loc, alt or ref, status='ok' if ok else 'unavailable', confidence='HIGH' if ok else 'UNKNOWN',
                          parse_method=method + '.image_ref',
                          structure={'reference': ref, 'resolved_relative_path': str(target.relative_to(root)) if inside else None,
                                     'linked_source_id': _sid(str(target.relative_to(root))) if ok else None},
                          fidelity={'structure_preserved': False, 'note': 'Figure is a reference to a separate source file'})
            if not ok:
                c.gap('MISSING_LINKED_ASSET', 'blocking', f'Referenced figure not found inside root: {ref}', e['locator_str'])


def _parse_notebook(path, c):
    nb = json.loads(path.read_text(encoding='utf-8-sig'))
    method = PARSER_VERSION + '.ipynb'
    cells = nb.get('cells', [])
    if not cells:
        c.gap('EMPTY_SOURCE', 'blocking', 'Notebook has no cells')
    for i, cell in enumerate(cells, 1):
        src = ''.join(cell.get('source', [])) if isinstance(cell.get('source'), list) else str(cell.get('source', ''))
        loc = {'cell': i}
        if cell.get('cell_type') == 'code':
            c.element('code', loc, src, parse_method=method, structure={'language': nb.get('metadata', {}).get('kernelspec', {}).get('language')},
                      flags=['code_not_executed'])
        elif src.strip():
            for a, b, block in _text_blocks(src):
                m = re.match(r'(#{1,6})\s+(.+)', block.lstrip())
                c.element('heading' if m else 'paragraph', {**loc, 'lines': f'{a}-{b}'}, m.group(2) if m else block, parse_method=method)
                for fm in FORMULA_BLOCK.finditer(block):
                    latex = next(g for g in (fm.group(1), fm.group(2), fm.group(4)) if g)
                    c.element('formula', {**loc, 'lines': f'{a}-{b}'}, latex.strip(), parse_method=method + '.latex',
                              structure={'latex': latex.strip()}, fidelity={'structure_preserved': True})
        for j, out in enumerate(cell.get('outputs', []), 1):
            oloc = {**loc, 'output': j}
            data = out.get('data', {})
            if out.get('text'):
                c.element('code_output', oloc, ''.join(out['text']), status='partial', confidence='MEDIUM', parse_method=method,
                          flags=['saved_output_not_reproduced'])
            for mime, value in data.items():
                if mime in ('image/png', 'image/jpeg'):
                    import base64
                    try:
                        raw = base64.b64decode(''.join(value) if isinstance(value, list) else value, validate=True)
                        c.element('image', oloc, '', status='uncertain', confidence='UNKNOWN', parse_method=method + '.output_image',
                                  raw_bytes=raw, asset=c.asset(raw, '.png' if mime == 'image/png' else '.jpg', 'notebook_saved_output'),
                                  flags=['saved_output_not_reproduced'], fidelity={'structure_preserved': False})
                    except Exception as e:
                        c.gap('VISUAL_UNCERTAIN', 'blocking', f'Notebook image undecodable: {e}')
                elif mime == 'text/plain' and not out.get('text'):
                    c.element('code_output', oloc, ''.join(value) if isinstance(value, list) else str(value), status='partial',
                              confidence='MEDIUM', parse_method=method, flags=['saved_output_not_reproduced'])
                elif mime == 'text/html':
                    p = TextHTML(); p.feed(''.join(value) if isinstance(value, list) else value)
                    c.element('code_output', oloc, '\n'.join(p.parts), status='partial', confidence='LOW', parse_method=method + '.html',
                              flags=['saved_output_not_reproduced'])
                    c.links.extend((u, None, '') for u in p.links if u.startswith(('http://', 'https://')))
                elif mime.startswith('image/'):
                    c.gap('VISUAL_UNCERTAIN', 'blocking', f'Cell {i} output {j}: {mime} not rendered (active/vector content)')
    c.gap('CODE_NOT_EXECUTED', 'info', 'Notebook code is never executed; saved outputs are not reproduced')


def _parse_code(path, c):
    text = path.read_text(encoding='utf-8-sig')
    method = PARSER_VERSION + '.code'
    if not text.strip():
        c.gap('EMPTY_SOURCE', 'blocking', 'Empty code file'); return
    n = len(text.splitlines())
    c.element('code', {'lines': f'1-{n}'}, text, parse_method=method, structure={'language': path.suffix.lstrip('.')},
              flags=['code_not_executed'])
    if path.suffix == '.py':
        try:
            tree = ast.parse(text)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    seg = '\n'.join(text.splitlines()[node.lineno - 1:node.end_lineno])
                    c.element('code', {'lines': f'{node.lineno}-{node.end_lineno}'}, seg, parse_method=method + '.python_ast',
                              structure={'symbol': node.name, 'type': type(node).__name__,
                                         'docstring': ast.get_docstring(node)}, flags=['code_not_executed'])
        except SyntaxError as e:
            c.gap('PARSE_FAILED', 'info', f'Python syntax not parseable (kept as text): {e}')
    c.gap('CODE_NOT_EXECUTED', 'info', 'Source code is never executed')


def _parse_table(path, c):
    text = path.read_text(encoding='utf-8-sig')
    if not text.strip():
        c.gap('EMPTY_SOURCE', 'blocking', 'Empty table'); return
    rows = list(csv.reader(io.StringIO(text), delimiter='\t' if path.suffix == '.tsv' else ','))
    header = rows[0] if rows else []
    kept = rows[:MAX_TABLE_ROWS]
    c.element('table', {'rows': f'1-{len(kept)}'}, '\n'.join(' | '.join(r) for r in kept), status='ok' if len(rows) <= MAX_TABLE_ROWS else 'partial',
              parse_method=PARSER_VERSION + '.csv', structure={'header': header, 'rows': kept}, fidelity={'structure_preserved': True},
              auto_links=False)  # URLs get exact row/column link elements below
    if len(rows) > MAX_TABLE_ROWS:
        c.gap('TRUNCATED_TABLE', 'blocking', f'Only first {MAX_TABLE_ROWS} of {len(rows)} rows in element')
    for r, row in enumerate(rows[1:], 2):
        for col, cell in enumerate(row):
            for u in URL.findall(cell):
                label = ' | '.join(x for k, x in enumerate(row) if k != col and x.strip())
                e = c.element('link', {'row': r, 'column': col + 1}, clean_url(u), parse_method=PARSER_VERSION + '.csv_url',
                              structure={'label': label, 'header': header[col] if col < len(header) else None}, auto_links=False)
                c.links.append((clean_url(u), e['element_id'], label))


def _parse_spreadsheet(path, c):
    _check_office_archive(path)
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=False, data_only=False, keep_links=False)
    for i, ws in enumerate(wb, 1):
        rows = [['' if x.value is None else str(x.value) for x in r] for r in ws.iter_rows()]
        c.element('table', {'sheet': i}, '\n'.join(' | '.join(r) for r in rows), parse_method=PARSER_VERSION + '.openpyxl',
                  structure={'sheet': ws.title, 'rows': rows[:MAX_TABLE_ROWS]}, flags=['formulas_not_recalculated'],
                  fidelity={'structure_preserved': True})
        if len(ws._images) + len(ws._charts):
            c.gap('VISUAL_UNCERTAIN', 'blocking', f'Sheet {ws.title}: embedded charts/images not exported')
    wb.close()


def _parse_image(path, c):
    data = path.read_bytes()
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im.verify()
    asset = c.asset(data, path.suffix.lower(), 'original_image_file')
    c.element('image', {'file': 1}, path.stem, status='uncertain', confidence='UNKNOWN', parse_method='Pillow.verify',
              asset=asset, raw_bytes=data, fidelity={'structure_preserved': False, 'note': 'Image content not interpreted'})
    c.gap('VISUAL_UNCERTAIN', 'blocking', 'Image needs visual interpretation; no automatic understanding claimed')


def _parse_svg(path, c):
    text = path.read_text(encoding='utf-8-sig', errors='replace')
    labels = re.findall(r'<text[^>]*>([^<]+)</text>', text)
    c.element('image', {'file': 1}, '\n'.join(labels), status='uncertain', confidence='LOW', parse_method=PARSER_VERSION + '.svg_text',
              raw_bytes=path.read_bytes(), structure={'text_labels': labels},
              fidelity={'structure_preserved': False, 'note': 'SVG not rendered (may contain active content); text labels only'})
    c.gap('ACTIVE_CONTENT_NOT_RENDERED', 'info', 'SVG not rendered for safety')
    c.gap('VISUAL_UNCERTAIN', 'blocking', 'SVG figure needs visual review')


def _parse_html(path, c):
    p = TextHTML(); p.feed(path.read_text(encoding='utf-8-sig', errors='replace'))
    text = '\n'.join(x for x in p.parts if x.strip())
    if not text.strip():
        c.gap('EMPTY_SOURCE', 'blocking', 'HTML without visible text')
    else:
        c.element('paragraph', {'document': 1}, text, status='partial', confidence='MEDIUM', parse_method=PARSER_VERSION + '.html_text',
                  fidelity={'structure_preserved': False, 'note': 'Scripts/styles ignored; layout dropped'})
    c.links.extend((u, None, '') for u in p.links if u.startswith(('http://', 'https://')))


def _parse_structured_text(path, c):
    text = path.read_text(encoding='utf-8-sig')
    if not text.strip():
        c.gap('EMPTY_SOURCE', 'blocking', 'Empty file'); return
    c.element('paragraph', {'lines': f'1-{len(text.splitlines())}'}, text, parse_method=PARSER_VERSION + '.plain')


# ---------------------------------------------------------------- orchestration

AUTHORITY_BY_ROLE = [('solutions', 'OFFICIAL_SOLUTION'), ('past_exam', 'OFFICIAL_EXAM'), ('exercise', 'OFFICIAL_EXERCISE'),
                     ('lecture', 'OFFICIAL_LECTURE'), ('notes', 'STUDENT_NOTES'), ('literature', 'SUPPLEMENTARY'),
                     ('paper', 'SUPPLEMENTARY'), ('tabular_data_candidate', 'DATA'), ('code_candidate', 'CODE')]


EXTRA_ROLES = {'solutions': r'musterl(ö|oe)sung|l(ö|oe)sungsskizze|solutions?\b|answer key',
               'past_exam': r'klausur|prüfung|pruefung|\bexams?\b|past[ _-]?exams?|midterm|final exam|question[ _-]sheet',
               'literature': r'zusatzliteratur|(^|/)literatur(e)?/|further[ _-]reading|supplementary[ _-]reading',
               'exercise': r'übung|uebung|tutorium|aufgabenblatt|homework|assignment|exercise sheet',
               'lecture': r'vorlesung|lecture|skript|folien|slides|lernziele|learning objectives'}


def _authority(rel, text, ext, links):
    """Authority from path + document title only. Body-text roles are kept as evidence, never as authority:
    a lecture that contains one 'Solution:' line is not a solution document."""
    roles, evidence = classify(rel, text, ext, links)
    title = next((ln for ln in text.splitlines() if ln.strip()), '').casefold()[:200]
    strong = []
    for role, pattern in EXTRA_ROLES.items():
        m = re.search(pattern, rel.casefold()) or re.search(pattern, title)
        if m:
            strong.append(role); evidence.append({'role': role, 'matched': m.group(0)[:100], 'basis': 'path_or_title'})
    if ext in CODE_EXT | {'.ipynb'} and 'lecture' in strong:
        strong.remove('lecture')
    weak = [r for r in roles if r == 'lecture' and ext not in CODE_EXT | {'.ipynb'}]  # body lecture cue = weak evidence only
    if weak and not strong:
        evidence.append({'role': 'lecture', 'basis': 'body_text_weak'})
    roles = strong + [r for r in roles if r not in strong]
    for role in strong + [r for r in roles if r in ('tabular_data_candidate', 'code_candidate')] + weak:
        auth = dict(AUTHORITY_BY_ROLE).get(role)
        if auth:
            return auth, roles, evidence
    return 'UNKNOWN', roles, evidence


def _snapshot(root):
    return {str(p.relative_to(root)): sha_file(p) for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()
            and not is_transient_file(p.name)}


def inventory(root, out, fetcher=None):
    """Inventory one course root into ``out`` (a directory outside the root).

    ``fetcher(url) -> (bytes, content_type, final_url)`` is optional and must be injected explicitly;
    the default performs no network access.
    """
    root = Path(root).expanduser().resolve(); out = Path(out).expanduser().resolve()
    if not root.is_dir():
        raise ContractError('Source root must be an existing directory')
    if out == root or root in out.parents:
        raise ContractError('Output must be outside the original source tree')
    out.mkdir(parents=True, exist_ok=True)
    before = _snapshot(root)
    assets = out / 'assets'
    sources, elements, gaps, links, scan_errors = [], [], [], [], []
    paths = []
    for base, dirs, files in os.walk(root, followlinks=False, onerror=lambda e: scan_errors.append(str(e))):
        dirs.sort()
        for d in list(dirs):
            if (Path(base) / d).is_symlink():
                paths.append(Path(base) / d); dirs.remove(d)
        paths.extend(Path(base) / f for f in files)
    for e in scan_errors:
        gaps.append({'source_id': None, 'code': 'SCAN_ERROR', 'severity': 'blocking', 'detail': e, 'locator_str': None})
    pdf_stems = {}
    for p in paths:
        if p.suffix.lower() == '.pdf':
            pdf_stems.setdefault(p.stem.casefold(), []).append(str(p.relative_to(root)))
    seen_hash = {}
    for path in sorted(paths):
        rel = str(path.relative_to(root)); ext = path.suffix.lower(); sid = _sid(rel)
        c = _Collector(sid, assets)
        s = {'source_id': sid, 'relative_path': rel, 'origin': 'local', 'format': ext or '(none)',
             'detected_type': SUPPORTED.get(ext, 'unsupported'), 'raw_sha256': None, 'version': None, 'bytes': None,
             'status': 'extracted', 'authority': 'UNKNOWN', 'authority_basis': 'heuristic(path+text); not proof of authority',
             'roles': [], 'role_evidence': [], 'relationships': [], 'parser': PARSER_VERSION, 'element_ids': [],
             'uncertainties': [], 'visual_status': 'NONE', 'error': None}
        sources.append(s)
        try:
            if path.is_symlink():
                s['status'] = 'symlink_skipped'; c.gap('SYMLINK_SKIPPED', 'info', 'Symlinks are not followed')
            else:
                s['raw_sha256'] = s['version'] = sha_file(path); s['bytes'] = path.stat().st_size
                if s['raw_sha256'] in seen_hash:
                    s['relationships'].append({'kind': 'duplicate_of', 'source_id': seen_hash[s['raw_sha256']]})
                seen_hash.setdefault(s['raw_sha256'], sid)
                if path.name in SYSTEM_METADATA_NAMES:
                    s['status'] = 'ignored_metadata'
                elif is_transient_file(path.name):
                    s['status'] = 'ignored_temporary'      # open-document lock / resource fork: never parsed
                elif s['bytes'] > MAX_FILE:
                    s['status'] = 'too_large'; c.gap('TOO_LARGE', 'blocking', f'{s["bytes"]} bytes exceeds limit')
                elif s['detected_type'] == 'unsupported':
                    s['status'] = 'unsupported'
                    c.gap('UNSUPPORTED_FORMAT', 'blocking', f'No parser for "{ext or "(no extension)"}"; file inventoried only')
                elif s['bytes'] == 0:
                    s['status'] = 'empty'; c.gap('EMPTY_SOURCE', 'blocking', 'Zero-byte file')
                else:
                    t = s['detected_type']
                    if t == 'pdf': _parse_pdf(path, c)
                    elif t == 'pptx': _parse_pptx(path, c, pdf_stems.get(path.stem.casefold(), []))
                    elif t == 'docx': _parse_docx(path, c)
                    elif t == 'notebook': _parse_notebook(path, c)
                    elif t == 'text': _parse_markup(path, c, root)
                    elif t == 'tex': _parse_markup(path, c, root, tex=True)
                    elif t == 'code': _parse_code(path, c)
                    elif t == 'table': _parse_table(path, c)
                    elif t == 'spreadsheet': _parse_spreadsheet(path, c)
                    elif t == 'image': _parse_image(path, c)
                    elif t == 'vector_image': _parse_svg(path, c)
                    elif t == 'html': _parse_html(path, c)
                    elif t == 'structured_text': _parse_structured_text(path, c)
                    if not c.elements and not any(g['code'] == 'EMPTY_SOURCE' for g in c.gaps):
                        c.gap('EMPTY_SOURCE', 'blocking', 'Parser found no content')
                    if any(g['code'] == 'EMPTY_SOURCE' for g in c.gaps):
                        s['status'] = 'empty'
                    elif any(g['code'] in BLOCKING_GAPS for g in c.gaps) or any(e['status'] != 'ok' for e in c.elements):
                        s['status'] = 'partial'
        except Exception as e:
            s['status'] = 'failed'; s['error'] = f'{type(e).__name__}: {e}'
            c.gap('PARSE_FAILED', 'blocking', s['error'])
        text = '\n'.join(e['text'] for e in c.elements)[:24000]
        s['authority'], s['roles'], s['role_evidence'] = _authority(rel, text, ext, [l[0] for l in c.links])
        s['element_ids'] = [e['element_id'] for e in c.elements]
        s['uncertainties'] = sorted({g['code'] for g in c.gaps})
        visual = [e for e in c.elements if e['kind'] in ('image', 'figure', 'diagram', 'chart', 'rendered_page')]
        s['visual_status'] = ('RENDER_UNAVAILABLE' if 'SLIDE_RENDER_UNAVAILABLE' in s['uncertainties'] else
                              'VISUAL_UNCERTAIN' if 'VISUAL_UNCERTAIN' in s['uncertainties'] else
                              'ASSETS_EXTRACTED_UNREVIEWED' if visual else 'NONE')
        elements.extend(c.elements); gaps.extend(c.gaps)
        links.extend((u, eid, label, sid) for u, eid, label in c.links)
    # Online references: one record per URL; never claim a download that did not happen.
    refs = {}
    for url, eid, label, sid in links:
        r = refs.setdefault(url, {'ref_id': 'web-' + _h(url)[:16], 'url': url, 'referenced_by_sources': [],
                                  'referenced_by_elements': [], 'labels': [], 'status': None})
        if sid not in r['referenced_by_sources']: r['referenced_by_sources'].append(sid)
        if eid and eid not in r['referenced_by_elements']: r['referenced_by_elements'].append(eid)
        if label and label not in r['labels']: r['labels'].append(label)
    for r in refs.values():
        if not re.match(r'https?://[^/\s]+', r['url']):
            r['status'] = 'INVALID_URL'
        elif fetcher is None:
            r['status'] = 'NOT_FETCHED_OFFLINE_POLICY'
        else:
            try:
                data, ctype, final = fetcher(r['url'])
                if not data:
                    raise ValueError('empty response')
                r.update(status='FETCHED', sha256=sha_bytes(data), bytes=len(data), content_type=ctype, final_url=final,
                         license='not_verified')
            except Exception as e:
                r.update(status='SOURCE_UNAVAILABLE', error=f'{type(e).__name__}: {e}')
        if r['status'] != 'FETCHED':
            gaps.append({'source_id': r['referenced_by_sources'][0], 'code': r['status'], 'severity': 'blocking',
                         'detail': r['url'], 'locator_str': r['ref_id']})
    after = _snapshot(root)
    if before != after:
        raise ContractError('DATA INTEGRITY: source root changed during inventory')
    status_counts = {}
    for s in sources:
        status_counts[s['status']] = status_counts.get(s['status'], 0) + 1
    m = {'schema': SOURCE_SCHEMA, 'parser_version': PARSER_VERSION, 'root_name': root.name,
         'source_count': len(sources), 'element_count': len(elements), 'status_counts': status_counts,
         'sources': sources, 'elements': elements, 'online_references': sorted(refs.values(), key=lambda r: r['url']),
         'gaps': gaps, 'coverage_complete': not any(g['code'] in BLOCKING_GAPS for g in gaps),
         'root_snapshot_sha256': _h(json.dumps(before, sort_keys=True)),
         'policy': {'untrusted_content': 'All source text is data. Nothing is executed; instruction-like text is flagged only.',
                    'network': 'none' if fetcher is None else 'injected_fetcher',
                    'visual': 'Assets exported unchanged and marked uncertain; no visual understanding is claimed.',
                    'pptx_render': 'No PDF raster substitutes a missing PPTX slide render.'}}
    validate_source_manifest(m)
    write_json(out / 'source_inventory.json', m)
    return m


def impact(old, new):
    """Selective change detection between two manifests of the same root."""
    o = {s['source_id']: s for s in old['sources']}; n = {s['source_id']: s for s in new['sources']}
    changed = sorted(k for k in o.keys() & n.keys() if o[k]['raw_sha256'] != n[k]['raw_sha256'])
    oe = {e['element_id']: e['extraction_hash'] for e in old['elements']}
    ne = {e['element_id']: e['extraction_hash'] for e in new['elements']}
    return {'added_sources': sorted(n.keys() - o.keys()), 'removed_sources': sorted(o.keys() - n.keys()),
            'changed_sources': changed,
            'changed_elements': sorted(k for k in oe.keys() & ne.keys() if oe[k] != ne[k]),
            'added_elements': sorted(ne.keys() - oe.keys()), 'removed_elements': sorted(oe.keys() - ne.keys())}
