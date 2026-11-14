"""Multi-slide worked examples: grouping and a deterministic total-consistency check (B7.1).

A course example often runs over consecutive slides ("before" / "after"). Slide text gives labelled values
("Sales contract A 150 k€") and stated sums ("Sum 350 k€"); a strike-through or arrow lives only in the figure.
The check rejects a computed total that the source never states and that combines values the source never
counts together, e.g. 150 + 100 = 250 when the slides only ever count {150, 200} = 350 and {150} = 150.
"""
import re
from itertools import combinations

# label (may contain digits, e.g. "Supplier 1") + value WITH a unit; unitless digits are treated as part of labels
VALUE = re.compile(r'([A-Za-zÄÖÜäöüß][^\n]{0,60}?)[ \t]*(?:\n[ \t]*)*(\d[\d.,]*)[ \t]*(k€|T€|Mio\.? ?€|€|EUR|%)', re.M)
SUM_LABEL = re.compile(r'^\s*(sum|total|summe|gesamt)\b', re.I)
TERM = re.compile(r'\d[\d.,]*')
MAX_ITEMS = 16  # subset search bound per stated sum


def _num(s):
    s = s.replace(',', '').strip('.')
    try:
        return float(s)
    except ValueError:
        return None


def _page(e):
    m = re.search(r'/page-(\d+)#', e.get('locator') or '')
    return (e.get('source'), int(m.group(1))) if m else None


def parse(element):
    """[(label, value, is_sum)] from one text element."""
    out = []
    for lab, val, _unit in VALUE.findall(element.get('text') or ''):
        v = _num(val)
        if v is not None:
            lab = ' '.join(lab.split())
            out.append((lab, v, bool(SUM_LABEL.match(lab))))
    return out


def groups(elements):
    """Consecutive pages of one source that share >= 2 identical labelled values: {page_key: [page_keys of group]}."""
    pages = {}
    for e in elements:
        k = _page(e)
        if k and e.get('status') == 'ok':
            pages.setdefault(k, []).append(e)
    pairs = {k: {(l, v) for e in es for l, v, s in parse(e) if not s} for k, es in pages.items()}
    out = {}
    for (src, p) in sorted(pages):
        nxt = (src, p + 1)
        if nxt in pairs and len(pairs[(src, p)] & pairs[nxt]) >= 2:
            g = sorted(set(out.get((src, p), [(src, p)])) | {nxt})
            for k in g:
                out[k] = g
    return out, pages


def counted_sets(group_pages, pages):
    """Value multisets the source itself counts: for each stated sum, the decompositions using the fewest elements."""
    sets = []
    for k in group_pages:
        items = [(i, v) for i, e in enumerate(pages[k]) for _l, v, s in parse(e) if not s]
        sums = {v for e in pages[k] for _l, v, s in parse(e) if s}
        if len(items) > MAX_ITEMS:
            continue
        for total in sums:
            found = []
            for n in range(1, len(items) + 1):
                for c in combinations(items, n):
                    if abs(sum(v for _i, v in c) - total) < 1e-9:
                        found.append((len({i for i, _v in c}), sorted(v for _i, v in c)))
            if found:
                best = min(f[0] for f in found)
                sets += [vals for n, vals in found if n == best]
    return sets


def check_block(block, ctx_elements):
    """[(status, detail)] for sums written in a block whose anchors lie in a multi-slide example."""
    by = {e['element_id']: e for e in ctx_elements}
    grp, pages = groups(ctx_elements)
    keys = {_page(by[r]) for r in block.get('source_refs') or [] if r in by}
    gpages = sorted({p for k in keys if k in grp for p in grp[k]})
    if not gpages:
        return []
    values = {v for k in gpages for e in pages[k] for _l, v, _s in parse(e)}
    stated = {v for k in gpages for e in pages[k] for _l, v, s in parse(e) if s}
    allowed = counted_sets(gpages, pages)
    texts = [str(block.get(f) or '') for f in ('body', 'problem', 'result', 'interpretation')] + \
            [str(s.get('statement') or '') for s in block.get('steps') or [] if isinstance(s, dict)]
    out = []
    for t in texts:
        for m in re.finditer(r'((?:\d[\d.,]*\s*\+\s*)+\d[\d.,]*)\s*=\s*(\d[\d.,]*)', t.replace('\\,', '')):
            terms = [_num(x) for x in TERM.findall(m.group(1))]
            res = _num(m.group(2))
            if None in terms or res is None or not all(x in values for x in terms):
                continue
            ok = res in stated or any(_sub(sorted(terms), a) for a in allowed)
            out.append(('PASS' if ok else 'FAIL',
                        f"{m.group(0)}: " + ('consistent with the stated sums' if ok else
                        f'combines values the slides never count together (stated sums {sorted(stated)}; '
                        f'counted sets {allowed}); pages {[p for _s, p in gpages]}')))
    return out


def _sub(small, big):
    big = list(big)
    for x in small:
        if x in big:
            big.remove(x)
        else:
            return False
    return True


def continuation_elements(anchor_ids, ctx_elements, index=None):
    """Text elements of the other slides of the same multi-slide example (read together, B6.7).
    index: optional precomputed (by, grp, pages) for these ctx_elements (same result, no rescan)."""
    if index is None:
        by = {e['element_id']: e for e in ctx_elements}
        grp, pages = groups(ctx_elements)
    else:
        by, grp, pages = index
    keys = {_page(by[a]) for a in anchor_ids if a in by}
    return [e for k in keys if k in grp for p in grp[k] if p not in keys for e in pages[p]]
