from __future__ import annotations
import hashlib, json, re
from pathlib import Path

SYSTEM_METADATA_NAMES = frozenset({'.DS_Store', 'Thumbs.db', 'desktop.ini'})


def is_transient_file(name):
    """B6.3 discovery: OS metadata and editor/Office lock files are not course material. They are recorded but never
    parsed, and they do not count as a change of the source root (a lock file appears whenever a document is open)."""
    n = str(name).rsplit('/', 1)[-1]
    return n in SYSTEM_METADATA_NAMES or n.startswith(('~$', '.~lock.', '._')) or (n.startswith('~') and n.endswith('.tmp'))


class ContractError(Exception): pass

def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha_bytes(data: bytes): return hashlib.sha256(data).hexdigest()

def sha_file(path: Path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def stable_id(prefix: str, body: str):
    return prefix + '-' + hashlib.sha256(body.encode('utf-8')).hexdigest()[:12]

def extract_json(text: str):
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I)
    try: return json.loads(text)
    except json.JSONDecodeError:
        dec = json.JSONDecoder()
        for index,char in enumerate(text):
            if char == '{':
                try:
                    val, end = dec.raw_decode(text[index:])
                    if isinstance(val, dict): return val
                except json.JSONDecodeError: continue
        raise ContractError('No parseable JSON object in provider response')

def enforce_keys(obj, required, stage):
    if not isinstance(obj, dict): raise ContractError(f'{stage}: JSON object required')
    absent = sorted(set(required)-set(obj))
    if absent: raise ContractError(f'{stage}: missing fields {absent}')
    return obj


def version_info():
    """Installed engine version (package metadata) and the release label of the install, if any. No side effects."""
    import json as _j
    from importlib import metadata as _m
    from pathlib import Path as _P
    try:
        pkg = _m.version('exam-mastery-engine')
    except _m.PackageNotFoundError:
        pkg = 'unknown'
    inst = _P.home() / '.local/share/exam-mastery/INSTALLED.json'
    try:
        rel = _j.loads(inst.read_text()).get('version')
    except (OSError, ValueError):
        rel = None
    return {'engine': pkg, 'release': rel, 'package_path': str(_P(__file__).resolve().parent)}
