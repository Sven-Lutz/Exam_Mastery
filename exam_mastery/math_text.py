"""Formula rendering for the chapter path (B6.6).

Contract: model text marks mathematics as TeX, inline between \\( and \\), display between \\[ and \\]. Everything
else stays plain text. One renderer (the MathJax SVG runtime of math_publishing) serves both channels:
- HTML: the SVG inline, role="math", the TeX as accessible label;
- PDF: a 3x PNG raster of the same SVG, inline in the paragraph (display formulas on their own line).

A formula that does not render is never dropped or silently shown as broken markup: it stays visible as TeX with a
marker, and the renderer reports it, so publishing can fail the math check instead of shipping a bad page.
"""
from __future__ import annotations
import hashlib, html, re, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

MATH = re.compile(r'\\\((.+?)\\\)|\\\[(.+?)\\\]', re.S)
ESC = lambda x: html.escape(str(x), quote=True)
# Model numbers are written as in the course (7,700,000 or 0,85). In TeX a bare comma is punctuation and gets a
# space after it ("7, 700, 000"); grouping the comma between digits keeps the number intact.
DIGIT_COMMA = re.compile(r'(?<=\d),(?=\d)')


def has_math(text):
    return bool(MATH.search(str(text or '')))


def _tex_fix(tex):
    return DIGIT_COMMA.sub('{,}', tex.strip())


class MathRenderer:
    def __init__(self, asset_dir):
        self.dir = Path(asset_dir); self.cache = {}; self.failed = []; self.rendered = 0

    def _render(self, tex, display):
        key = (tex, display)
        if key in self.cache:
            return self.cache[key]
        from .math_publishing import _render_svg
        from .common import ContractError
        try:
            raw, w, h = _render_svg(_tex_fix(tex), display)
        except (ContractError, ValueError, ET.ParseError, subprocess.TimeoutExpired, OSError) as e:
            self.failed.append({'tex': tex, 'display': display, 'error': str(e)[-300:]}); self.cache[key] = None
            return None
        name = 'math-' + hashlib.sha256(f'{display}|{tex}'.encode()).hexdigest()[:20]
        self.dir.mkdir(parents=True, exist_ok=True)
        svg = self.dir / f'{name}.svg'; svg.write_text(raw, encoding='utf-8')
        self.rendered += 1
        self.cache[key] = {'svg': svg, 'raw': raw, 'w': w, 'h': h, 'png': None}
        return self.cache[key]

    def _png(self, a):
        if a['png'] is None:
            import pymupdf
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF
            png = a['svg'].with_suffix('.png')
            doc = pymupdf.open(stream=renderPDF.drawToString(svg2rlg(str(a['svg']))), filetype='pdf')
            doc[0].get_pixmap(matrix=pymupdf.Matrix(4, 4), alpha=True).save(png); doc.close()
            a['png'] = png
        return a['png']

    def _split(self, text):
        text = str(text or ''); last = 0
        for m in MATH.finditer(text):
            yield 'text', text[last:m.start()]
            yield ('inline', m.group(1)) if m.group(1) is not None else ('display', m.group(2))
            last = m.end()
        yield 'text', text[last:]

    def html(self, text):
        out = []
        for kind, part in self._split(text):
            if kind == 'text':
                out.append(ESC(part).replace('\n', '<br>')); continue
            a = self._render(part, kind == 'display')
            if a is None:
                out.append(f'<code class="math-fail" title="Formel nicht darstellbar">{ESC(part)}</code>'); continue
            svg = a['raw'].replace('<svg', f'<svg role="img" aria-label="{ESC(part)}"', 1)
            out.append(f'<div class="math-d">{svg}</div>' if kind == 'display' else f'<span class="math-i">{svg}</span>')
        return ''.join(out)

    def rl(self, text, max_width=470):
        """ReportLab paragraph markup."""
        out = []
        for kind, part in self._split(text):
            if kind == 'text':
                out.append(ESC(part).replace('\n', '<br/>')); continue
            a = self._render(part, kind == 'display')
            if a is None:
                out.append(f'<font face="Courier" color="#a3261d">[Formel nicht darstellbar: {ESC(part)}]</font>'); continue
            k = min(1.0, max_width / a['w']); w, h = a['w'] * k, a['h'] * k
            img = f'<img src="{ESC(self._png(a))}" width="{w:.1f}" height="{h:.1f}" valign="{-h * 0.28:.1f}"/>'
            out.append(f'<br/>{img}<br/>' if kind == 'display' else img)
        return ''.join(out)

    def flow(self, text, style, max_width=470):
        """ReportLab flowable for a text: one Paragraph, or (with display formulas) paragraphs and centred formula
        images as separate flowables, so a tall formula never overlaps the neighbouring lines."""
        from reportlab.platypus import Paragraph, Image, Spacer
        parts, buf = [], ''
        for kind, part in self._split(text):
            if kind != 'display':
                buf += part if kind == 'text' else f'\\({part}\\)'; continue
            a = self._render(part, True)
            if a is None:
                buf += f'\\[{part}\\]'; continue
            if buf.strip():
                parts.append(Paragraph(self.rl(buf, max_width), style))
            buf = ''
            k = min(1.0, max_width / a['w'])
            parts += [Spacer(1, 3), Image(str(self._png(a)), width=a['w'] * k, height=a['h'] * k, hAlign='CENTER'), Spacer(1, 5)]
        if buf.strip() or not parts:
            parts.append(Paragraph(self.rl(buf, max_width), style))
        return parts[0] if len(parts) == 1 else _group(parts)

    def report(self):
        return {'renderer': 'MathJax 3 SVG (HTML) / same SVG rasterised 4x (PDF)', 'formulas_rendered': self.rendered,
                'formulas_failed': len(self.failed), 'failures': self.failed[:20],
                'status': 'FAIL' if self.failed else 'PASS' if self.rendered else 'NOT_APPLICABLE'}


def _group(parts):
    """Flowables measured and drawn as one unit inside a block, splittable at a page end (unlike a nested
    KeepTogether, whose huge reported height pushes a whole block onto the next page)."""
    from reportlab.platypus import Flowable

    class Group(Flowable):
        def __init__(self, parts):
            Flowable.__init__(self); self.parts = parts

        def _space(self, p):
            return p.getSpaceBefore() + p.getSpaceAfter()

        def wrap(self, aw, ah):
            self._sizes = [p.wrap(aw, ah) for p in self.parts]; self._aw = aw
            self.width, self.height = aw, sum(h + self._space(p) for p, (w, h) in zip(self.parts, self._sizes))
            return self.width, self.height

        def draw(self):
            y = self.height
            for p, (w, h) in zip(self.parts, self._sizes):
                y -= p.getSpaceBefore() + h
                x = (self._aw - w) / 2 if getattr(p, 'hAlign', 'LEFT') == 'CENTER' else 0
                p.drawOn(self.canv, x, y); y -= p.getSpaceAfter()

        def split(self, aw, ah):
            # The first part must fit (or split) in the space left; otherwise move the whole group to the next frame.
            # Returning all parts unconditionally made ReportLab abort with 'Splitting error' (Stage A, 2026-11-06).
            first = self.parts[0]
            if first.wrap(aw, ah)[1] + self._space(first) <= ah:
                return list(self.parts)
            head = first.split(aw, ah)
            return list(head) + list(self.parts[1:]) if head else []

    return Group(parts)
