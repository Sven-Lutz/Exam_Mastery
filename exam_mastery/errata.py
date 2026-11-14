"""B14: documented editorial corrections (errata) applied at publish time, without any model call.

An erratum file lives OUTSIDE the lecture folder, in the course output folder: errata/<chapter_id>.json
{"schema": "em-errata-v1", "chapter_id": "...", "errata": [
  {"id": "E1", "target": "solutions[solution_id=sol-a-20].answer", "old": "exact text", "new": "replacement",
   "reason": "why", "basis": ["§ 5a Abs. 3 GmbHG", "Folie 26"], "author": "calling agent", "human_reviewed": false}]}

Rules (fail-closed): the target must resolve to a string and `old` must occur in it exactly once; otherwise publishing
stops with ERRATUM_NOT_APPLICABLE. The produced content_ast.json is never modified; the correction is applied to the
published products only and listed in the publish report, the dossier and LIES_MICH.md. An erratum is not a review:
human_reviewed stays false unless a person sets it.
"""
import copy
import json
import re
from pathlib import Path

from .common import ContractError

SCHEMA = 'em-errata-v1'
_STEP = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]|\[([A-Za-z_][A-Za-z0-9_]*)=([^\]]+)\]|\.')


def errata_path(chapter_dir):
    ch = Path(chapter_dir)
    return ch.parent.parent.parent / 'errata' / f'{ch.name}.json'


def load(chapter_dir):
    p = errata_path(chapter_dir)
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding='utf-8'))
    if d.get('schema') != SCHEMA or d.get('chapter_id') != Path(chapter_dir).name:
        raise ContractError(f'ERRATUM_FILE_INVALID: {p} (schema or chapter_id)')
    for e in d.get('errata') or []:
        miss = [k for k in ('id', 'target', 'old', 'new', 'reason', 'basis') if not e.get(k)]
        if miss:
            raise ContractError(f'ERRATUM_FILE_INVALID: {e.get("id")} lacks {miss}')
    return d.get('errata') or []


def _resolve(obj, target):
    """Returns (container, key) for a target such as solutions[solution_id=sol-a-20].steps[2].statement."""
    toks = [m for m in _STEP.finditer(target) if m.group(0) != '.']
    if ''.join(m.group(0) for m in _STEP.finditer(target)) != target:
        raise ContractError(f'ERRATUM_NOT_APPLICABLE: bad target syntax {target!r}')
    cur, parent, key = obj, None, None
    for m in toks:
        parent = cur
        if m.group(1):
            key = m.group(1)
            if not isinstance(cur, dict) or key not in cur:
                raise ContractError(f'ERRATUM_NOT_APPLICABLE: {target}: no field {key!r}')
        elif m.group(2):
            key = int(m.group(2))
            if not isinstance(cur, list) or key >= len(cur):
                raise ContractError(f'ERRATUM_NOT_APPLICABLE: {target}: index {key} out of range')
        else:
            f, v = m.group(3), m.group(4)
            hits = [i for i, x in enumerate(cur if isinstance(cur, list) else []) if isinstance(x, dict) and str(x.get(f)) == v]
            if len(hits) != 1:
                raise ContractError(f'ERRATUM_NOT_APPLICABLE: {target}: {f}={v} matches {len(hits)} entries')
            key = hits[0]
        cur = parent[key]
    return parent, key


def apply(ast, errata):
    """Returns (corrected copy of ast, applied records)."""
    if not errata:
        return ast, []
    out, applied = copy.deepcopy(ast), []
    for e in errata:
        parent, key = _resolve(out, e['target'])
        val = parent[key]
        if not isinstance(val, str):
            raise ContractError(f'ERRATUM_NOT_APPLICABLE: {e["id"]}: target is not text')
        n = val.count(e['old'])
        if n != 1:
            raise ContractError(f'ERRATUM_NOT_APPLICABLE: {e["id"]}: old text found {n} times in {e["target"]} (content changed?)')
        parent[key] = val.replace(e['old'], e['new'])
        applied.append({'id': e['id'], 'target': e['target'], 'reason': e['reason'], 'basis': e['basis'],
                        'author': e.get('author', 'unknown'), 'human_reviewed': bool(e.get('human_reviewed', False)),
                        'old': e['old'], 'new': e['new']})
    return out, applied
