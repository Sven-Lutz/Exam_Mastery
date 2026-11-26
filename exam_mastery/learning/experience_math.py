"""Project the existing canonical math registry into book, web and Anki text.

TeX is presentation, never executed as code. The existing MathJax SVG renderer
provides offline, accessible web formulas; PDF/Anki keep native TeX delimiters.
"""
import html
import re
from ..common import ContractError
from .. import math_publishing, typeset

TOKEN = re.compile(r'\[\[math:([A-Za-z0-9_:.-]+)\]\]')
MATH = re.compile(r'\\\((.*?)\\\)|\\\[(.*?)\\\]', re.S)


def resolve(unit, text):
    equations = {item['id']: item for item in unit.get('mathematics', [])}
    def replace(match):
        if match[1] not in equations:
            raise ContractError('Unknown mathematical reference: ' + match[1])
        record = equations[match[1]]
        return (r'\[' + record['tex'] + r'\]' if record.get('display', True)
                else r'\(' + record['tex'] + r'\)')
    result = TOKEN.sub(replace, str(text))
    for match in MATH.finditer(result):
        tex = match[1] if match[1] is not None else match[2]
        if not 0 < len(tex) <= 10000 or math_publishing.FORBIDDEN.search(tex):
            raise ContractError('Unsafe/oversized mathematical presentation')
    return result


def validate(unit):
    records = unit.get('mathematics', [])
    if records:
        math_publishing.validate_registry(records, [s['id'] for s in unit.get('sources', [])])
    def walk(value):
        if isinstance(value, str): resolve(unit, value)
        elif isinstance(value, list):
            for item in value: walk(item)
        elif isinstance(value, dict):
            for item in value.values(): walk(item)
    walk(unit)


def project(unit):
    def walk(value):
        if isinstance(value, str): return resolve(unit, value)
        if isinstance(value, list): return [walk(x) for x in value]
        if isinstance(value, dict): return {k: walk(v) for k, v in value.items()}
        return value
    return walk(unit)


def markup(unit, text):
    """Existing safe Markdown plus existing MathJax SVG; no browser TeX execution."""
    source = typeset.md(resolve(unit, text))
    def replace(match):
        tex = html.unescape(match[1] if match[1] is not None else match[2])
        raw, _, _ = math_publishing._render_svg(tex, match[2] is not None)
        label = next((r['alt'] for r in unit.get('mathematics', []) if r['tex'] == tex), tex)
        raw = raw.replace('<svg', '<svg role="img" aria-label="' + html.escape(label, quote=True) + '"', 1)
        return '<span class="em-math">' + raw + '</span>'
    return MATH.sub(replace, source)
