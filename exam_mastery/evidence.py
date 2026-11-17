"""B35 Scientific Claim Evidence Registry (domain-neutral).

Problem it solves: V4 recorded evidence per SOURCE ("Crossref: VERIFIED", "Abstract gelesen"), not per CLAIM. A
verified DOI then looked like support for whatever the text said about the paper, and nothing stopped a sentence
from asserting a constant, a table entry or a proof detail that only the inaccessible full text could contain.

A claim record:
  {id, statement, claim_type, concept, source: {id, citation, doi?, url?},
   locator,                        # page / section / slide / § / table where the support is
   access,                         # ACCESS level below: what was REALLY read
   accessed_text,                  # the passage that was read (abstract text, quoted excerpt); may be a file path
   quote,                          # the exact supporting words inside accessed_text
   derivation_ref,                 # AUTHOR_DERIVATION: id of an argument graph (exam_mastery.argument_graph)
   limitations, counterpoints, uncertainty,
   valid_as_of, jurisdiction, study_design, ...   # required per claim_type, see CLAIM_TYPES
   review: {status: UNREVIEWED|MODEL_REVIEWED|HUMAN_REVIEWED, by, date, note}}

Rules (each FAIL is a publication blocker for the sentence that carries the claim):
  E1 access must be a known level; METADATA_ONLY supports only BIBLIOGRAPHIC claims (who published what, when)
  E2 ABSTRACT_ONLY / *_FULLTEXT need a quote that occurs verbatim in the accessed text
  E3 every number in the statement must occur in the quote/accessed text (details beyond the read passage FAIL)
  E4 ABSTRACT_ONLY may not assert proof/theorem/table/constant/experiment-setup details (detail vocabulary) unless
     those words are in the quote
  E5 *_FULLTEXT and OFFICIAL_COURSE need a locator
  E6 AUTHOR_DERIVATION needs a derivation_ref whose audit did not FAIL; the claim is then 'AUTHOR_DERIVATION_AUDITED'
     and only becomes 'AUTHOR_DERIVATION_REVIEWED' with a recorded human review
  E7 per-claim_type required fields (CLAIM_TYPES) - e.g. legal: jurisdiction + valid_as_of; clinical: valid_as_of +
     evidence grade; empirical: study_design
  E8 MODEL_INFERENCE / UNVERIFIED claims must be published with a visible marker (publish_label)
A DOI/metadata match never raises the access level (legacy 'VERIFIED' verdicts map to METADATA_ONLY, see
from_legacy_verification).
"""
from __future__ import annotations
import re

ACCESS = ('OFFICIAL_COURSE', 'PRIMARY_FULLTEXT', 'SECONDARY_FULLTEXT', 'ABSTRACT_ONLY', 'METADATA_ONLY',
          'AUTHOR_DERIVATION', 'MODEL_INFERENCE', 'UNVERIFIED')
REVIEW = ('UNREVIEWED', 'MODEL_REVIEWED', 'HUMAN_REVIEWED')

# what each kind of claim must carry beyond a source; extended by subject profiles, never by per-course if-chains
CLAIM_TYPES = {
    'BIBLIOGRAPHIC': {'requires': [], 'note': 'who published what, when, where'},
    'DEFINITIONAL': {'requires': [], 'note': 'definition or notation as used by a source'},
    'MATHEMATICAL': {'requires': [], 'note': 'theorem, bound, identity; needs a proof (source passage or audited derivation)'},
    'ALGORITHMIC': {'requires': [], 'note': 'algorithm property (correctness, complexity); theory separate from benchmarks'},
    'EMPIRICAL': {'requires': ['study_design'], 'note': 'observed result; design, sample, effect size, uncertainty'},
    'BENCHMARK': {'requires': ['study_design'], 'note': 'reported performance in a specific experimental setup'},
    'HISTORICAL': {'requires': [], 'note': 'origin or development of an idea'},
    'NORMATIVE_LEGAL': {'requires': ['jurisdiction', 'valid_as_of'], 'note': 'norm content / case law with version'},
    'CLINICAL': {'requires': ['valid_as_of', 'evidence_grade'], 'note': 'guideline or clinical evidence with date and grade'},
    'INTERPRETATION': {'requires': [], 'note': 'own reading or classification of a source; never attributed to it'},
}
_DETAIL = re.compile(r'\b(Beweis|beweist|Theorem|Satz\s+\d|Lemma|Korollar|Tabelle|Konstante|Abschnitt|Experiment(?:e|aufbau)?|'
                     r'Hyperparameter|proof|proves|theorem|lemma|table|constant|section|experimental setup)\b', re.I)
_NUM = re.compile(r'(?<![\w.])\d+(?:[.,]\d+)?(?![\w])')


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '').replace('­', '')).strip().lower()


_WORDS = {w: str(i) for i, ws in enumerate([('zero', 'null'), ('one', 'eins'), ('two', 'zwei'), ('three', 'drei'),
          ('four', 'vier'), ('five', 'fünf'), ('six', 'sechs'), ('seven', 'sieben'), ('eight', 'acht'), ('nine', 'neun'), ('ten', 'zehn')]) for w in ws}


def _numbers(s):
    s = re.sub(r'\b(' + '|'.join(_WORDS) + r')\b', lambda m: ' ' + _WORDS[m.group(1).lower()] + ' ', s or '', flags=re.I)
    s = re.sub(r'\\\(.*?\\\)', ' ', s)                       # numbers inside formulas are the author's own notation
    s = re.sub(r'\(\s*(?:19|20)\d{2}[a-z]?\s*\)|\b(?:19|20)\d{2}\b', ' ', s)   # citation years are bibliographic
    return {n.replace(',', '.') for n in _NUM.findall(s)}


def level(c, graphs=None):
    """Effective, honest evidence level of one claim after the rules (what a reader may be told)."""
    a = c.get('access')
    if a == 'AUTHOR_DERIVATION':
        rv = (c.get('review') or {}).get('status')
        return 'AUTHOR_DERIVATION_REVIEWED' if rv == 'HUMAN_REVIEWED' else 'AUTHOR_DERIVATION_AUDITED'
    return a


def check_claim(c, graphs=None):
    """Findings for one claim: [{code, severity, msg}]."""
    F = []
    def f(code, sev, msg):
        F.append({'code': code, 'severity': sev, 'msg': msg, 'claim': c.get('id')})
    a, t, st = c.get('access'), c.get('claim_type'), c.get('statement') or ''
    if a not in ACCESS:
        f('E1', 'FAIL', f'unknown access level {a!r}'); return F
    if t not in CLAIM_TYPES:
        f('E7', 'FAIL', f'unknown claim type {t!r}')
    if a == 'METADATA_ONLY' and t != 'BIBLIOGRAPHIC':
        f('E1', 'FAIL', 'metadata (DOI/title/year) cannot support a content claim')
    txt, quote = c.get('accessed_text') or '', c.get('quote') or ''
    if a in ('ABSTRACT_ONLY', 'PRIMARY_FULLTEXT', 'SECONDARY_FULLTEXT'):
        if not quote:
            f('E2', 'FAIL', 'no supporting quote from the accessed text')
        elif txt and _norm(quote) not in _norm(txt):
            f('E2', 'FAIL', 'quote does not occur in the accessed text')
        elif not txt:
            f('E2', 'WARN', 'accessed text not stored; quote cannot be re-checked')
        missing = _numbers(st) - _numbers(quote + ' ' + txt + ' ' + (c.get('locator') or ''))   # locator numbers are anchors
        if missing:
            f('E3', 'FAIL', 'statement contains details not in the read passage: ' + ', '.join(sorted(missing)))
    if a == 'ABSTRACT_ONLY':
        d = _DETAIL.search(st)
        if d and d.group(0).lower() not in _norm(quote + ' ' + txt):
            f('E4', 'FAIL', f'asserts a full-text detail ("{d.group(0)}") from an abstract')
    if a in ('PRIMARY_FULLTEXT', 'SECONDARY_FULLTEXT', 'OFFICIAL_COURSE') and not c.get('locator'):
        f('E5', 'FAIL', 'no locator (page/section/slide/§)')
    if a == 'AUTHOR_DERIVATION':
        ref = c.get('derivation_ref')
        if not ref:
            f('E6', 'FAIL', 'author derivation without a derivation_ref')
        elif graphs is not None:
            if ref not in graphs:
                f('E6', 'FAIL', f'derivation {ref} not found')
            else:
                from .argument_graph import audit
                if audit(graphs[ref])['status'] == 'FAIL':
                    f('E6', 'FAIL', f'derivation {ref} fails its proof audit')
    for req in CLAIM_TYPES.get(t, {}).get('requires', []):
        if not c.get(req):
            f('E7', 'FAIL', f'{t} claim requires {req}')
    if a in ('MODEL_INFERENCE', 'UNVERIFIED'):
        f('E8', 'WARN', 'must be published with a visible "not verified" marker')
    if (c.get('review') or {}).get('status', 'UNREVIEWED') not in REVIEW:
        f('E1', 'FAIL', 'unknown review status')
    return F


def publish_label(c):
    """Reader-facing access label; it states what was read, never more."""
    return {'OFFICIAL_COURSE': 'Vorlesung', 'PRIMARY_FULLTEXT': 'Primärquelle, Volltext geprüft',
            'SECONDARY_FULLTEXT': 'Sekundärquelle, Volltext geprüft', 'ABSTRACT_ONLY': 'nur Abstract gelesen',
            'METADATA_ONLY': 'nur bibliografische Angaben geprüft', 'AUTHOR_DERIVATION': 'eigene Herleitung',
            'MODEL_INFERENCE': 'Modellaussage – nicht geprüft', 'UNVERIFIED': 'nicht geprüft'}[c['access']]


def audit_registry(claims, graphs=None):
    F = [x for c in claims for x in check_claim(c, graphs)]
    ids = [c.get('id') for c in claims]
    for d in {i for i in ids if ids.count(i) > 1}:
        F.append({'code': 'E0', 'severity': 'FAIL', 'msg': f'duplicate claim id {d}', 'claim': d})
    by_level = {}
    for c in claims:
        by_level[level(c, graphs)] = by_level.get(level(c, graphs), 0) + 1
    return {'status': 'FAIL' if any(x['severity'] == 'FAIL' for x in F) else 'PASS',
            'n_claims': len(claims), 'by_level': by_level, 'findings': F,
            'human_reviewed': sum(1 for c in claims if (c.get('review') or {}).get('status') == 'HUMAN_REVIEWED'),
            'scope': 'consistency of each claim with what was demonstrably read; NOT whether the source itself is right'}


def from_legacy_verification(entry):
    """Map a legacy knowledge/verification.json verdict to an access level. A Crossref/OpenLibrary 'VERIFIED' only
    proves that the bibliographic record exists; with a stored abstract the abstract MAY be quoted, nothing more."""
    if not entry.get('found'):
        return 'UNVERIFIED'
    return 'ABSTRACT_ONLY' if entry.get('abstract_stored') else 'METADATA_ONLY'


_KIND_TYPE = {'official_guideline': 'NORMATIVE_LEGAL', 'statute': 'NORMATIVE_LEGAL', 'court_decision': 'NORMATIVE_LEGAL',
              'clinical_guideline': 'CLINICAL', 'study': 'EMPIRICAL', 'textbook': 'DEFINITIONAL', 'paper': 'MATHEMATICAL'}
_ACCESS = {'fulltext': 'PRIMARY_FULLTEXT', 'abstract': 'ABSTRACT_ONLY', 'metadata': 'METADATA_ONLY'}


def from_subject_source(src):
    """Claim draft from a knowledge/subject/*.json source record ('use' = what the chapter relies on). Structured
    fields that the record does not carry stay empty, so the rules report them instead of guessing them."""
    return {'id': src['id'], 'statement': src.get('use', ''), 'claim_type': _KIND_TYPE.get(src.get('kind'), 'DEFINITIONAL'),
            'source': {'id': src['id'], 'citation': src.get('cite'), 'url': src.get('url')},
            'access': _ACCESS.get(src.get('access'), 'UNVERIFIED'), 'locator': src.get('cite') if src.get('access') == 'fulltext' else None,
            'accessed_text': src.get('text', ''), 'quote': src.get('quote', ''),
            'jurisdiction': src.get('jurisdiction'), 'valid_as_of': src.get('valid_as_of'), 'evidence_grade': src.get('evidence_grade'),
            'study_design': src.get('study_design'), 'review': {'status': 'UNREVIEWED'}}
