"""B14: deterministic scope-reduction recovery of one chapter, without any model call.

When a planning fix only REMOVES competencies, items or source elements from a chapter (sources unchanged, nothing
added or altered), the role answers of the last complete run stay valid for everything that remains. This module
re-runs the chapter through the normal engine pipeline (every contract check and quality gate) with a provider that
returns those stored answers, minus exactly the entries that refer to removed ids.

Fail-closed:
- the new chapter context must equal the old context with the removed ids stripped (checked at every role call);
- nothing may be added; a single changed value refuses the recovery;
- a contract repair cannot be answered (stored answers cannot change): the run stops instead.
Provenance: every role answer is recorded as SCOPE_RECOVERED with source run, source answer hash and the dropped
paths; reviews are marked as performed on the pre-change superset of the content.
"""
import hashlib
import json
from pathlib import Path

from .common import ContractError, extract_json, write_json

ROLES = ('chapter_author', 'chapter_assessment', 'chapter_solutions', 'chapter_semantic_review', 'chapter_risk_review')
ID_KEYS = ('kc_id', 'item_id', 'object_id', 'element_id', 'block_id')
BLOCK_KEY = 'block_id'


def ids_in(x, acc=None):
    """All competency, item and element ids mentioned in a JSON value."""
    acc = set() if acc is None else acc
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ID_KEYS and isinstance(v, str):
                acc.add(v)
            ids_in(v, acc)
    elif isinstance(x, list):
        for v in x:
            ids_in(v, acc)
    elif isinstance(x, str) and x.startswith(('kc-', 'q-', 'el-')) and ' ' not in x:
        acc.add(x)
    return acc


def strip_all(x, removed, derived=None):
    """strip() until no further block is dropped (transitive). Returns (value, dropped paths, derived block ids)."""
    derived = set() if derived is None else set(derived)
    while True:
        dropped, new = [], set()
        out = strip(x, removed | derived, '', dropped, new)
        if new <= derived:
            return out, dropped, derived
        derived |= new


def strip(x, removed, path='', dropped=None, derived=None):
    """Remove every list entry that IS a removed id, or a dict owned by one (its own kc/item/object/element id, or
    kc_ids entirely removed), and every dict key that is a removed id. Records the dropped paths."""
    dropped = [] if dropped is None else dropped
    derived = set() if derived is None else derived
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k in removed:
                dropped.append(f'{path}.{k}'); continue
            out[k] = strip(v, removed, f'{path}.{k}', dropped, derived)
        return out
    if isinstance(x, list):
        out = []
        for i, v in enumerate(x):
            p = f'{path}[{i}]'
            if isinstance(v, str) and v in removed:
                dropped.append(p); continue
            if isinstance(v, dict):
                own = {v.get(k) for k in ID_KEYS} & removed
                kcs, els = v.get('kc_ids'), v.get('element_ids')
                if own or (isinstance(kcs, list) and kcs and set(kcs) <= removed) or (isinstance(els, list) and els and set(els) <= removed):
                    dropped.append(p)
                    if isinstance(v.get(BLOCK_KEY), str):
                        derived.add(v[BLOCK_KEY])        # a dropped block takes its reviews and issues with it
                    continue
            out.append(strip(v, removed, p, dropped, derived))
        return out
    return x


def removal_delta(old_ctx, new_ctx):
    """Returns (removed ids, problems). Recoverable only if problems is empty."""
    old_ids, new_ids = ids_in(old_ctx), ids_in(new_ctx)
    added, removed = new_ids - old_ids, old_ids - new_ids
    problems = [f'ADDED_ID {i}' for i in sorted(added)]
    if strip(old_ctx, removed) != new_ctx:
        problems.append('CONTEXT_CHANGED_BEYOND_REMOVAL')
    return removed, problems


def source_answers(chapter_dir):
    """role -> path of the answer the earlier run actually used (latest provider evidence per role)."""
    out = {}
    for role in ROLES:
        # only answers an agent/model actually gave for this chapter; a recovery never builds on another recovery
        ev = sorted((p for p in (Path(chapter_dir) / 'provider_evidence' / role).glob('*.json') if 'answer_file' in json.loads(p.read_text())),
                    key=lambda p: p.stat().st_mtime)
        if not ev:
            raise ContractError(f'SCOPE_RECOVERY_SOURCE_INCOMPLETE: no stored answer for {role} in {chapter_dir}')
        f = Path(json.loads(ev[-1].read_text())['answer_file'])
        if not f.is_file():
            f = Path(chapter_dir) / 'agent_io' / f.name
        if not f.is_file():
            raise ContractError(f'SCOPE_RECOVERY_SOURCE_INCOMPLETE: answer file for {role} missing')
        out[role] = f
    return out


def find_source_chapter(course_out, chapter_id, exclude=()):
    """Latest earlier run whose chapter was published and holds stored answers for all roles."""
    runs = sorted((p for p in Path(course_out).glob('ch-*/chapters/' + chapter_id) if p.parent.parent not in exclude),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for ch in runs:
        if (ch / 'publish' / 'artifacts' / '1_Lehrbuch.pdf').exists() and (ch / 'chapter_context.json').exists():
            try:
                source_answers(ch)
                return ch
            except ContractError:
                continue
    return None


class ScopeRecoveryProvider:
    name = 'scope_recovery'; model = 'stored-answers'; external = False; budget = None

    def __init__(self, source_chapter_dir):
        self.src = Path(source_chapter_dir)
        self.answers = source_answers(self.src)
        self.old_ctx = json.loads((self.src / 'chapter_context.json').read_text(encoding='utf-8'))
        self.asked = set()
        self.derived = set()      # block ids dropped from the author answer; later roles drop what refers to them
        self.records = []

    def fingerprint(self):
        return {'name': 'scope_recovery', 'model': 'stored-answers', 'protocol': 4, 'source_chapter': str(self.src)}

    def ask(self, role, prompt, run_dir, fixture_dir=None, images=None):
        run_dir = Path(run_dir)
        if role not in self.answers:
            raise ContractError(f'SCOPE_RECOVERY_UNSUPPORTED_ROLE: {role} has no stored answer; a model run is required')
        if role in self.asked:
            raise ContractError(f'SCOPE_RECOVERY_CANNOT_REPAIR: the engine asked {role} again (contract repair); stored answers cannot change')
        self.asked.add(role)
        new_ctx = json.loads((run_dir / 'chapter_context.json').read_text(encoding='utf-8'))
        removed, problems = removal_delta(self.old_ctx, new_ctx)
        if problems:
            raise ContractError('SCOPE_RECOVERY_REFUSED: ' + '; '.join(problems[:5]))
        raw = self.answers[role].read_bytes()
        obj, dropped, self.derived = strip_all(extract_json(raw.decode('utf-8')), removed, self.derived)
        rec = {'provider': 'scope_recovery', 'role': role, 'status': 'SCOPE_RECOVERED',
               'request_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
               'source_answer': str(self.answers[role]), 'source_answer_sha256': hashlib.sha256(raw).hexdigest(),
               'removed_ids': sorted(removed), 'derived_removed_blocks': sorted(self.derived), 'dropped_paths': dropped,
               'note': ('review performed by the earlier run on the pre-change content (a superset of this content)'
                        if role.endswith('_review') else 'content generated by the earlier run; entries of removed ids dropped')}
        ev = run_dir / 'provider_evidence' / role; ev.mkdir(parents=True, exist_ok=True)
        write_json(ev / f'scope-recovery-{rec["request_sha256"][:16]}.json', rec)
        rd = run_dir / 'agent_io' / 'recovered'; rd.mkdir(parents=True, exist_ok=True)   # not answer files: never replayed as agent answers
        write_json(rd / f'{role}.json', obj)
        self.records.append(rec)
        write_json(run_dir / 'scope_recovery.json', {'schema': 'em-scope-recovery-v1', 'source_chapter': str(self.src),
                                                     'model_calls': 0, 'roles': self.records})
        return obj
