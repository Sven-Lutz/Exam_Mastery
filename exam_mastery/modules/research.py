"""Ende-zu-Ende-Eigenrecherche mit nachprüfbaren Belegen (keine Provider-Aufrufe, nur öffentlicher HTTP-GET).

Ablauf (jeder Schritt wird in <modul>/research_log.jsonl protokolliert):
  need      Wissensbedarf aus der Lückenanalyse (sources.gaps) oder aus einer fachlichen Frage
  search    tatsächlich ausgeführte Suchanfragen und gefundene Kandidaten (Agent/Mensch, mit Datum)
  verify    Abruf der Quelle, inhaltsadressierter Schnappschuss (SHA-256, nur lokal im Cache – urheberrechtlich
            geschützte Texte werden nicht ins Repository kopiert), Prüfung, ob konkrete Passagen wörtlich vorkommen
  decide    Aufnahme (mit Zugriffsniveau, Evidenz, Grenzen) oder Ablehnung mit Grund
  integrate Verknüpfung Quelle → Kompetenz → eigenes Beispiel → Aufgabe/Labor
`trace` erzeugt daraus einen lesbaren Nachweis. Ohne Netz (oder ohne Zustimmung --online) wird nichts abgerufen.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path.home() / '.cache' / 'exam-mastery' / 'sources'
UA = 'ExamMastery-SourceCheck/1.0 (+offline study tool)'


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log(module_dir: Path, event: dict) -> dict:
    e = {'ts': _now(), **event}
    with open(Path(module_dir) / 'research_log.jsonl', 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(e, ensure_ascii=False) + '\n')
    return e


def read_log(module_dir: Path) -> list[dict]:
    p = Path(module_dir) / 'research_log.jsonl'
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []


def _norm(t: str) -> str:
    t = t.replace('­', '').replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('’', "'").replace('“', '"').replace('”', '"')
    t = re.sub(r'-\s*\n\s*', '', t)                    # Silbentrennung am Zeilenende
    return re.sub(r'\s+', ' ', t).strip().lower()


def to_text(raw: bytes, ctype: str) -> str:
    if raw[:5] == b'%PDF-' or 'pdf' in ctype:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.pdf'; p.write_bytes(raw)
            return subprocess.run(['pdftotext', '-layout', str(p), '-'], capture_output=True, text=True, check=True).stdout
    s = raw.decode('utf-8', errors='replace')
    s = re.sub(r'(?is)<(script|style).*?</\1>', ' ', s)
    return html.unescape(re.sub(r'(?s)<[^>]+>', ' ', s))


def fetch(url: str, online: bool, timeout: int = 40) -> dict:
    """Abruf mit inhaltsadressiertem Cache. online=False: nur Cache, sonst Fehler (kein heimlicher Netzzugriff)."""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    meta_p = CACHE / f'{key}.json'
    if meta_p.exists() and not online:
        meta = json.loads(meta_p.read_text())
        return {**meta, 'text': (CACHE / meta['sha256']).read_text(encoding='utf-8'), 'from_cache': True}
    if not online:
        raise RuntimeError(f'not cached and --online not given: {url}')
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw, ctype, final = r.read(), r.headers.get('Content-Type', ''), r.geturl()
    text = to_text(raw, ctype)
    sha = hashlib.sha256(raw).hexdigest()
    (CACHE / sha).write_text(text, encoding='utf-8')
    meta = {'url': url, 'final_url': final, 'content_type': ctype, 'bytes': len(raw), 'sha256': sha, 'fetched_at': _now()}
    meta_p.write_text(json.dumps(meta))
    return {**meta, 'text': text, 'from_cache': False}


def verify(url: str, phrases: list[str], online: bool) -> dict:
    """Prüft, ob jede Passage (normalisiert) wörtlich im abgerufenen Text vorkommt; liefert kurzen Kontext (≤ 240 Zeichen)."""
    doc = fetch(url, online)
    T = _norm(doc['text'])
    out = []
    for ph in phrases:
        i = T.find(_norm(ph))
        out.append({'phrase': ph, 'found': i >= 0, 'context': T[max(0, i - 60): i + len(_norm(ph)) + 60][:240] if i >= 0 else None})
    return {k: doc[k] for k in ('url', 'final_url', 'content_type', 'bytes', 'sha256', 'fetched_at', 'from_cache')} | {'phrases': out, 'all_found': all(p['found'] for p in out)}


def trace(module_dir: Path, m: dict) -> str:
    """Lesbarer Nachweis: Bedarf → Suche → Prüfung → Entscheidung → Integration, plus Verknüpfungsgraph."""
    ev = read_log(module_dir)
    L = [f'# Recherche-Nachweis: {m["title"]}', '', 'Automatisch aus `research_log.jsonl` erzeugt. Schnappschüsse liegen nur lokal (SHA-256 angegeben).', '']
    for e in ev:
        k = e['step']
        if k == 'need': L += [f'## Bedarf ({e["ts"][:10]}): {e["kc"]}', e['question'], '']
        elif k == 'search': L += [f'**Suche** – {e["tool"]}: ' + '; '.join(f'„{q}“' for q in e['queries']), *[f'- Kandidat: {c}' for c in e['candidates']], '']
        elif k == 'verify':
            r = e['result']; L += [f'**Prüfung** {e["source"]}: {r["url"]} → {r["bytes"]} Bytes, SHA-256 `{r["sha256"][:16]}…`, {r["fetched_at"]}']
            L += [f'- {"✓" if p["found"] else "✗"} „{p["phrase"]}“' for p in r['phrases']] + ['']
        elif k == 'decide': L += [f'**Entscheidung** {e["source"]}: {e["decision"]} – {e["reason"]}', '']
        elif k == 'integrate': L += [f'**Integration** {e["source"]} → ' + ', '.join(f'{a}: {b}' for a, b in e['links'].items()), '']
    L += ['## Verknüpfungen Quelle → Kompetenz → Produkte']
    for k in m['kcs']:
        L += [f'- **{k["id"]}** ({k["label"]}): Quellen {", ".join(k.get("sources", []))}; Produkte {json.dumps(k.get("products", {}), ensure_ascii=False)}']
    return '\n'.join(L) + '\n'
