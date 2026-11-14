#!/usr/bin/env python3
"""Verify the knowledge-base source register against Crossref (DOI) and OpenLibrary (ISBN).

Deterministic and cached: each lookup is stored under knowledge/cache/<sha256(url)>.json, so a rerun makes no
network calls unless --refresh is given. Writes exam_mastery/knowledge/verification.json with, per source:
  found / title match / year match / abstract stored, and per claim in principles.json whether every
  'abstract_evidence' snippet occurs in the stored abstract (a mechanical check that the cited number or
  phrase is really in the source's own summary; it is not a check of the full paper).

Usage: python scripts/verify_sources.py [--refresh] [--offline]
Exit code 1 if any source is not found, mismatches, or any abstract_evidence snippet is missing.
"""
import hashlib, html, json, re, sys, time, urllib.request
from pathlib import Path

KB = Path(__file__).resolve().parents[1] / 'exam_mastery' / 'knowledge'
CACHE = KB / 'cache'
UA = 'exam-mastery-kb-verifier/1.0 (local research tool)'


def fetch(url, refresh=False, offline=False):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:24] + '.json')
    if f.exists() and not refresh:
        return json.loads(f.read_text())
    if offline:
        return {'_status': 'not_cached'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=20) as r:
            data = {'_status': 200, 'body': json.loads(r.read().decode())}
    except urllib.error.HTTPError as e:
        data = {'_status': e.code}
    except Exception as e:  # network down: do not cache
        return {'_status': 'error', 'error': str(e)}
    f.write_text(json.dumps(data, ensure_ascii=False))
    time.sleep(0.2)
    return data


def norm(s):
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s or ''))
    s = re.sub('[‐‑‒−]', '-', s)
    s = s.replace('−', '-').replace('–', '-').replace(' ', ' ')
    return re.sub(r'\s+', ' ', s).lower()


def check_doi(src, **kw):
    d = fetch('https://api.crossref.org/works/' + src['doi'], **kw)
    if d.get('_status') != 200:
        return {'found': False, 'status': d.get('_status')}
    m = d['body']['message']
    title = ' '.join(m.get('title') or [])
    year = (m.get('issued', {}).get('date-parts') or [[None]])[0][0]
    pub = (m.get('published-print') or m.get('published-online') or {}).get('date-parts', [[None]])[0][0]
    return {'found': True, 'title': title, 'container': ' '.join(m.get('container-title') or []),
            'title_match': norm(src['title_key']) in norm(title),
            'year_match': src['year'] in {year, pub} or abs((year or 0) - src['year']) <= 1,
            'abstract': norm(m.get('abstract', '')) or openalex_abstract(src['doi'], **kw), }


def openalex_abstract(doi, **kw):
    """OpenAlex stores abstracts as an inverted index; rebuild the word order."""
    d = fetch('https://api.openalex.org/works/doi:' + doi, **kw)
    inv = (d.get('body') or {}).get('abstract_inverted_index') if d.get('_status') == 200 else None
    if not inv:
        return ''
    pos = sorted((i, w) for w, idx in inv.items() for i in idx)
    return norm(' '.join(w for _, w in pos))


def check_isbn(src, **kw):
    d = fetch(f"https://openlibrary.org/isbn/{src['isbn']}.json", **kw)
    if d.get('_status') != 200:
        return {'found': False, 'status': d.get('_status')}
    title = d['body'].get('title', '') + ' ' + d['body'].get('subtitle', '')
    return {'found': True, 'title': title.strip(), 'title_match': norm(src['title_key']) in norm(title),
            'year_match': True, 'abstract': ''}


def main(argv):
    kw = {'refresh': '--refresh' in argv, 'offline': '--offline' in argv}
    sources = json.loads((KB / 'sources.json').read_text())['sources']
    # subject registers (knowledge/subject/*.json): same checks; statutes and official web pages are read primary texts
    for f in sorted((KB / 'subject').glob('*.json')):
        sources += [dict(x, _register=f.stem) for x in json.loads(f.read_text())['sources']]
    principles = json.loads((KB / 'principles.json').read_text())['principles']
    out, problems, abstracts = {}, [], {}
    for s in sources:
        if not s.get('doi') and not s.get('isbn'):
            out[s['id']] = {'verdict': 'PRIMARY_TEXT_READ', 'url': s.get('url'), 'accessed': s.get('accessed'), 'abstract_stored': False}
            continue
        r = check_doi(s, **kw) if s.get('doi') else check_isbn(s, **kw)
        if s.get('doi') and s.get('isbn') and not r.get('found'):
            r = check_isbn(s, **kw)
        abstracts[s['id']] = r.pop('abstract', '')
        r['abstract_stored'] = bool(abstracts[s['id']])
        ok = r.get('found') and r.get('title_match') and r.get('year_match')
        r['verdict'] = 'VERIFIED' if ok else 'PROBLEM'
        if not ok:
            problems.append(f"{s['id']}: {r}")
        out[s['id']] = r
    claims = {}
    for p in principles:
        for c in p['claims']:
            for ev in c.get('abstract_evidence', []):
                hit = norm(ev['snippet']) in abstracts.get(ev['source'], '')
                claims.setdefault(c['id'], []).append({'source': ev['source'], 'snippet': ev['snippet'], 'found_in_abstract': hit})
                if not hit:
                    problems.append(f"{c['id']}: snippet not in abstract of {ev['source']}: {ev['snippet']!r}")
    report = {'schema': 'em-kb-verification-v1', 'checked_on': time.strftime('%Y-%m-%d'),
              'method': 'Crossref /works and OpenLibrary /isbn; cached under knowledge/cache',
              'sources': out, 'claim_snippets': claims, 'problems': problems,
              'summary': {'sources': len(out), 'verified': sum(v['verdict'] == 'VERIFIED' for v in out.values()),
                          'primary_text_read': sum(v['verdict'] == 'PRIMARY_TEXT_READ' for v in out.values()),
                          'with_abstract': sum(v['abstract_stored'] for v in out.values()),
                          'snippets_checked': sum(len(v) for v in claims.values()),
                          'snippets_found': sum(x['found_in_abstract'] for v in claims.values() for x in v)}}
    (KB / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps(report['summary']))
    for p in problems:
        print('PROBLEM', p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
