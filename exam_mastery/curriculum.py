"""P2: course-wide, subject-adaptive competency, assessment and chapter planning (em-curriculum-v1).

Separation of concerns (never conflated):
- transport/retrieval units  -> corpus.py; NOT used here and never determine chapter count
- competencies (KC)          -> statement + required cognitive operation(s) + anchors + prerequisites
- editorial chapters         -> narrative units with explicit didactic requirements and a source package
- assessment items           -> exam/exercise (sub)questions with the operation their WORDING actually demands
- coverage evidence          -> recomputed from wording; an ID link alone never counts

Deterministic offline planner. Where a semantic model decision will later be needed, the
``SemanticDecisions`` contract below is the only entry point; tests use fixture decisions.
No provider is called in P2 (``provider_calls`` is always 0 and asserted).
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from .common import write_json, ContractError
from .source_schema import CURRICULUM_SCHEMA, OPERATIONS, BLOCKING_GAPS, validate_curriculum

PLANNER_VERSION = 'em-curriculum-planner-1'

# Verb lexicon (de/en). Patterns are matched on lower-cased text. Order inside a text decides the
# primary operation of a learning objective; assessment items keep the full set they demand.
OPERATION_LEXICON = {
    'PROVE': [r'\bbeweis(e|en|t)\b', r'\bzeig(e|en sie|t),? (dass|daß)', r'\bprove\b', r'\bshow that\b'],
    'DERIVE': [r'\bleit\w* .{0,80}?\bher\b', r'\bherleit', r'\bherzuleiten', r'\bderiv(e|ation)\b'],
    'SUBSUME': [r'\bsubsumi', r'\bprüf\w* .{0,60}(anspruch|strafbar|zulässig|wirksam|begründet)', r'\bhat .{1,40} gegen .{1,40} (einen )?anspruch',
                r'\bgutachten', r'\bist .{1,40} strafbar', r'\bwie ist die rechtslage', r'\bassess (whether|the claim)'],
    'IMPLEMENT': [r'\bimplementier', r'\bprogrammier', r'\bimplement\b', r'\bwrite (a |the )?(function|program|code)', r'\bschreib\w* .{0,30}funktion'],
    'EVALUATE': [r'\bevaluier', r'\bbewert', r'\bbeurteil', r'\bevaluate\b', r'\bassess\b', r'\bcritically', r'\bdiskutier', r'\bdiscuss\b'],
    'COMPARE': [r'\bvergleich', r'\bcompare\b', r'\bcontrast\b', r'\bunterscheid', r'\bdistinguish\b'],
    'INTERPRET': [r'\binterpretier', r'\binterpret\b', r'\bdeut(e|en sie)\b'],
    'APPLY': [r'\bwend\w* .{0,60}\ban\b', r'\banwend', r'\bapply\b', r'\bsolve\b', r'\blös(e|en sie)\b', r'\buse .{0,40} to\b'],
    'CALCULATE': [r'\bberechn', r'\bcompute\b', r'\bcalculate\b', r'\bbestimm(e|en sie)\b', r'\bwert\w* .{0,30}\baus\b',
                  r'\bhow (much|many)\b', r'\bwie (viel|hoch|groß)\w*', r'\b(rounded|gerundet\w*)\b'],
    'EXPLAIN': [r'\berklär', r'\berläuter', r'\bbeschreib', r'\bexplain\b', r'\bdescribe\b', r'\bbegründ', r'\bwarum\b', r'\bwhy\b', r'\bjustify\b'],
    'DEFINE': [r'\bdefinier', r'\bdefine\b', r'\bwas versteht man unter', r'\bgive the definition', r'\bdefinition of\b',
               r'\bdefinition (von|der|des)\b'],
    'RECALL': [r'\bnenn(e|en sie)?\b', r'\bgib .{0,40}\ban\b', r'\bgeben sie .{0,40}\ban\b',
               r'\bwiedergeben\b', r'\bgeben sie .{0,160}\bwieder\b', r'\bgib .{0,160}\bwieder\b',  # B7.4 operator "wiedergeben"
               r'\bname\b', r'\blist\b', r'\bstate\b',
               r'\bidentify\b', r'\bwhich\b', r'\bwelche[rs]?\b', r'\bzähl\w* .{0,20}auf\b'],
}
# B6.6: generic open questions ('What are the three reasons ...?') ask for recall only when nothing more specific
# is demanded; they never override a stronger verb ('What are the (rounded) shares?' stays CALCULATE).
INTERROGATIVE_RECALL = [r'\bwhat (are|were) the\b', r'\bwelche sind\b', r'\bwas sind die\b']
# B6.6: quantitative work a page demands beyond its title. Only signals that are reliable in extracted text:
# an equation or arithmetic between figures, a totals row over figures, or a quantity question on the page.
# Charts whose numbers are not in the text layer and pages that merely state figures do not qualify.
QUANT_QUESTION = re.compile(r'\bhow (much|many)\b|\bwie (viel|hoch|groß)\w*|\b(rounded|gerundet\w*)\b', re.I)
EQUATION = re.compile(r'(?:\d|\b[A-Za-z]{1,8}\b)\s*=\s*\(?\s*-?\d|\d\s*(?:%|€|\$|k€|EUR|Mio)?\s*\)?\s*[*×·÷+]\s*\(?\s*\d')
TOTAL_LINE = re.compile(r'^\s*(sum|total|summe|gesamt|insgesamt)\b', re.I | re.M)
NUM_TOKEN = re.compile(r'\d[\d.,]*')
OP_LABEL = {'RECALL': 'Nenne/name', 'DEFINE': 'Definiere/define', 'EXPLAIN': 'Erkläre/explain', 'CALCULATE': 'Berechne/calculate',
            'APPLY': 'Wende an/apply', 'COMPARE': 'Vergleiche/compare', 'INTERPRET': 'Interpretiere/interpret',
            'EVALUATE': 'Bewerte/evaluate', 'DERIVE': 'Leite her/derive', 'PROVE': 'Beweise/prove', 'SUBSUME': 'Subsumiere/subsume',
            'IMPLEMENT': 'Implementiere/implement'}


def content_operations(texts):
    """[(operation, basis)] a page's own content demands (B6.6). Detects quantitative work only; everything else
    (explaining, comparing, evaluating) cannot be read reliably from slide text and stays with the title/default."""
    t = '\n'.join(x for x in texts if x)
    nums = len(NUM_TOKEN.findall(t))
    if EQUATION.search(t) and nums >= 3:
        return [('CALCULATE', 'page_equation_or_arithmetic')]
    if TOTAL_LINE.search(t) and nums >= 4:
        return [('CALCULATE', 'page_totals_over_figures')]
    if QUANT_QUESTION.search(t):
        return [('CALCULATE', 'page_quantity_question')]
    return []


def topic_operations(title, page_texts):
    """Operations of a topic competency from its page: verbs/questions of the title, quantitative page content,
    and EXPLAIN as the default understanding goal when the title demands nothing specific. Multiple operations
    are kept; each carries its basis so a reviewer can see why it was demanded."""
    ev = [(op, 'page_title_wording') for op in operations_in(title)]
    if not ev:
        ev.append(('EXPLAIN', 'default_topic_understanding'))
    for op, basis in content_operations(page_texts):
        if op not in [o for o, _ in ev]:
            ev.append((op, basis))
    return [o for o, _ in ev], [{'operation': o, 'basis': b} for o, b in ev]


# Which ACTUAL item operations can evidence a REQUIRED competency operation.
SATISFIES = {
    'RECALL': set(OPERATIONS),
    'DEFINE': {'DEFINE'},
    'EXPLAIN': {'EXPLAIN', 'DERIVE', 'PROVE', 'EVALUATE', 'COMPARE', 'INTERPRET'},
    'INTERPRET': {'INTERPRET', 'EVALUATE'},
    'COMPARE': {'COMPARE', 'EVALUATE'},
    'CALCULATE': {'CALCULATE', 'APPLY'},
    'APPLY': {'APPLY', 'CALCULATE', 'SUBSUME', 'IMPLEMENT'},
    'SUBSUME': {'SUBSUME'},
    'IMPLEMENT': {'IMPLEMENT'},
    'DERIVE': {'DERIVE', 'PROVE'},
    'PROVE': {'PROVE'},
    'EVALUATE': {'EVALUATE'},
}
LINK_RELATIVE = 0.3  # heuristic; documented in P1_P2_ABNAHME.md
DEMANDING = {'DERIVE', 'PROVE', 'SUBSUME', 'IMPLEMENT', 'APPLY', 'EVALUATE'}
STOP = set('''aber alle auch beim bitte damit dann dass dem den der des die dies diese diesem dieser doch durch eine einem einen
einer eines fuer für gegen ihre ihrer jede jeder kann kein mit nach nicht oder ohne sein seine sich sie sind soll sowie über unter
und von vom was weil wenn werden wie wird zum zur zwischen about after also and are been both but can each for from have how into
its may more must not one only other such than that the their them then there these they this those use used using when where
which while will with would your gegeben given following folgenden folgende aufgabe problem question frage task punkte points
leiten leite herleiten beweisen beweise nennen nenne zeigen zeige erklären erkläre definieren definiere prove derive show explain
define name state implement implementieren berechnen berechne compute calculate apply anwenden subsumieren prüfen prüfe sollen
können koennen warum definition satz theorem lemma korollar corollary proposition erkläre erklären anwendung subsumtion lernziele learning objectives able students studierende'''.split())
MC_PATTERN = re.compile(r'kreuzen sie|multiple.choice|which of the following|welche der folgenden|^\s*(\[ \]|\( \)|□)', re.I | re.M)
CASE_PATTERN = re.compile(r'sachverhalt|\bfall\b|\bcase\b|scenario|gegeben (sei|ist|sind)|given\b|\b\d+([.,]\d+)?\b', re.I)
NORM_PATTERN = re.compile(r'(§§?\s*\d+[a-z]?(\s*(abs\.|absatz)\s*\d+)?(\s*(s\.|satz)\s*\d+)?\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöü]{1,8})|(art\.\s*\d+\s*[A-Z]{2,})', re.I)
ITEM_HEAD = re.compile(r'^\s*(?:#+\s*)?(Aufgabe|Problem|Exercise|Frage|Question|Task)\s*(\d+)\b', re.I | re.M)
SUB_HEAD = re.compile(r'^\s*(?:[-*]\s*)?\(?([a-h])\)\s+', re.M)
POINTS = re.compile(r'\((\d+(?:[.,]\d+)?)\s*(?:P|Pkt|Punkte|points|pts|marks)\.?\)', re.I)
OBJ_HEAD = re.compile(r'lernziel|learning (objective|outcome)|^\s*(objectives?|ziele)\s*:|kompetenzziel|sie können|you will be able|students (can|will)|ziele der', re.I)
FORMAL_HEAD = re.compile(r'^\s*\**\s*(Definition|Satz|Theorem|Lemma|Korollar|Corollary|Proposition)\b\s*(?:\(([^)]{1,80})\))?\s*[.:]?\s*\**\s*[.:]?\s*(.*)', re.I | re.S)
PREREQ_HEAD = re.compile(r'^\s*(?:\*\*)?(Voraussetzung(en)?|Prerequisites?|Vorwissen)\s*[:.]\s*(.*)', re.I | re.S)
NOTATION = re.compile(r'\$([^$]{1,30})\$\s+(?:bezeichnet|bezeichne|ist|sei|denotes|is|be)\s+(?:die|der|das|den|the|a|an|eine[nr]?|ein)?\s*([^.;,\n$]{3,70})', re.I)
NOTATION_LET = re.compile(r'\b(?:sei|seien|let|es bezeichne)\s+\$([^$]{1,30})\$\s+(?:die|der|das|the|a|an|eine[nr]?|ein)?\s*([^.;,\n$]{3,70})', re.I)


def _h(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def operations_in(text):
    """All operations demanded by a text, in order of first occurrence."""
    low = (text or '').lower(); hits = []
    for op, pats in OPERATION_LEXICON.items():
        pos = min((m.start() for p in pats for m in [re.search(p, low)] if m), default=None)
        if pos is not None:
            hits.append((pos, op))
    if not hits:
        pos = min((m.start() for p in INTERROGATIVE_RECALL for m in [re.search(p, low)] if m), default=None)
        if pos is not None:
            hits.append((pos, 'RECALL'))
    return [op for _, op in sorted(hits)]


def terms(text):
    words = re.findall(r'[^\W\d_]{4,}', (text or '').lower(), flags=re.UNICODE)
    return {w[:7] for w in words if w not in STOP}


def semantic_key(statement):
    return ' '.join(sorted(terms(statement))[:10]) or _h(statement)[:12]


def source_support(statement, anchor_texts):
    """UNVERIFIED (no anchor) < SOURCE_EXISTS (anchor, no topical match) < SOURCE_SUPPORT_LEXICAL.
    SOURCE_SUPPORT_CONFIRMED is reserved for a semantic reviewer and never set here."""
    if not anchor_texts:
        return 'UNVERIFIED'
    st = terms(statement); at = terms(' '.join(anchor_texts))
    return 'SOURCE_SUPPORT_LEXICAL' if st and len(st & at) >= min(2, len(st)) else 'SOURCE_EXISTS'


def satisfied(required, actual_ops, item):
    """Return (ok, reason). Wording-based, conservative."""
    acceptable = SATISFIES[required] & set(actual_ops)
    if not acceptable:
        return False, f'item demands {sorted(actual_ops) or ["NONE"]}, competency requires {required}'
    if required in ('PROVE', 'DERIVE') and item['format'] == 'multiple_choice':
        return False, f'{required} cannot be evidenced by a multiple-choice item'
    if required in ('APPLY', 'CALCULATE', 'SUBSUME') and not item['has_concrete_instance']:
        return False, f'{required} requires a concrete new case/instance in the item'
    if required == 'SUBSUME' and not item['norm_refs']:
        return False, 'SUBSUME requires a norm to subsume under'
    return True, 'operation and item format match'


class SemanticDecisions:
    """Contract for later model-made planning decisions (P3+). P2 only loads fixtures.

    {"schema":"em-semantic-decisions-v1","decisions":[{"kind":"operation|link|prerequisite|chapter",
      "subject_id":"...", "value":..., "rationale":"...", "evidence_element_ids":[...], "decided_by":"fixture|model"}]}
    Decisions can add links/prerequisites or override an inferred KC operation, but the coverage
    gate re-checks every link against the item wording; a decision can never force coverage.
    """
    KINDS = {'operation', 'link', 'prerequisite', 'chapter', 'chapter_merge', 'chapter_keep_separate', 'chapter_order', 'competency'}

    def __init__(self, decisions=None):
        self.decisions = list(decisions or [])

    @classmethod
    def from_file(cls, path):
        d = json.loads(Path(path).read_text(encoding='utf-8'))
        if d.get('schema') != 'em-semantic-decisions-v1':
            raise ContractError('semantic decisions: wrong schema')
        return cls(d['decisions'])

    def validate(self, element_ids):
        for d in self.decisions:
            if d.get('kind') not in self.KINDS or not d.get('subject_id') or not d.get('rationale', '').strip():
                raise ContractError('semantic decision lacks kind/subject/rationale')
            if d.get('decided_by') == 'model' and not d.get('evidence_element_ids'):
                raise ContractError('model decision without evidence anchors')
            if not set(d.get('evidence_element_ids', [])) <= element_ids:
                raise ContractError('semantic decision cites unknown element')
            if d['kind'] == 'operation' and any(o not in OPERATIONS for o in d['value']):
                raise ContractError('semantic decision uses unknown operation')
            if d.get('decided_by') == 'model' and d.get('status') in ('VERIFIED', 'CONFIRMED', 'SUPPORTED'):
                raise ContractError('a model decision cannot verify or confirm itself')
            if d['kind'] == 'competency':
                # scope decision: a person adds a competency the planner missed; anchored, never model-made
                v = d.get('value') or {}
                if d.get('decided_by') != 'human':
                    raise ContractError('a competency can only be added by a human scope decision')
                if not str(v.get('statement') or '').strip() or not v.get('operations') or any(o not in OPERATIONS for o in v['operations']):
                    raise ContractError('competency decision needs statement and known operations')
                if not v.get('anchor_element_ids') or not set(v['anchor_element_ids']) <= element_ids:
                    raise ContractError('competency decision needs anchor elements from the sources')

    def of(self, kind):
        return [d for d in self.decisions if d['kind'] == kind]


# ---------------------------------------------------------------- helpers over the manifest

def _level(e):
    lvl = (e.get('structure') or {}).get('level') if isinstance(e.get('structure'), dict) else None
    return lvl if isinstance(lvl, int) else 1


CHAPTER_OPENER = re.compile(r'(kapitel|chapter)\s*\d{1,2}\.?', re.I)
CHAPTER_DIVIDER = re.compile(r'^\s*(kapitel|chapter|part|teil|lecture|vorlesung|lektion|session|unit|week|woche|einheit)\s*\d+\b', re.I)


def _paged_sections(manifest, source, pm):
    """Paged source (PDF/PPTX): page titles from the page model. Split into several chapters ONLY at >=2 numbered
    divider pages (title like 'Part 2 ...'/'3. ...' on a page with <=3 text elements); otherwise one chapter whose
    divider/section titles are recorded as topic candidates."""
    from .triage import _norm
    by = {e['element_id']: e for e in manifest['elements']}
    info = pm[source['source_id']]; pages = info['pages']; order = sorted(pages)
    def text_els(p):
        return [e for e in pages[p]['elements'] if e['kind'] in ('heading', 'paragraph', 'list_item') and e['text'].strip()
                and _norm(e['text']) not in info['boilerplate']]
    dividers = [p for p in order if pages[p]['title'] and len(text_els(p)) <= 3]
    numbered = [p for p in dividers if CHAPTER_DIVIDER.match(pages[p]['title']['text'])]
    bare = [p for p in dividers if NUMBERED_TITLE.match(pages[p]['title']['text']) and p not in numbered]
    seg = {'dividers': [{'page': p, 'title': pages[p]['title']['text'][:80], 'element_id': pages[p]['title']['element_id']}
                        for p in dividers]}
    # book-like scripts: a chapter starts mid-document on a page whose first text line is a bare 'KAPITEL 2' /
    # 'Chapter 3' (the page itself is full of text, so it is no divider page). Numbers must strictly increase.
    openers, titles, last = [], {}, -1
    for p in order:
        te = text_els(p)
        if te and CHAPTER_OPENER.fullmatch(te[0]['text'].strip()):
            n = int(re.search(r'\d+', te[0]['text']).group())
            if n > last and len(te) > 1:
                openers.append(p); titles[p] = te[1]; last = n
    if len(numbered) >= 2:
        cuts = numbered
        seg['status'] = 'SPLIT_AT_NUMBERED_DIVIDERS'
    elif len(openers) >= 2:
        cuts = openers
        seg['status'] = 'SPLIT_AT_CHAPTER_OPENERS'
        seg['dividers'] = [{'page': p, 'title': titles[p]['text'][:80], 'element_id': titles[p]['element_id']} for p in openers]
    else:
        cuts = [order[0]] if order else []
        seg['status'] = ('NUMBERED_SECTIONS_SEMANTIC_REVIEW_REQUIRED' if len(bare) >= 2 else
                         'SOURCE_UNIT_WITH_SECTIONS' if dividers else 'SOURCE_UNIT')
        if len(bare) >= 2:
            seg['note'] = 'bare-numbered divider pages (process steps or chapters?) not split automatically'
    first_title = next((pages[p]['title'] for p in order if pages[p]['title']), None)
    sections = []
    for i, c in enumerate(cuts):
        end = cuts[i + 1] if i + 1 < len(cuts) else None
        span = [p for p in order if (p >= c or i == 0) and (end is None or p < end)]
        head = (titles[c] if c in titles and seg['status'] == 'SPLIT_AT_CHAPTER_OPENERS' else pages[c]['title']) if len(cuts) > 1 else first_title
        els = [e for p in span for e in pages[p]['elements'] if head is None or e['element_id'] != head['element_id']]
        sections.append((head, els, {**seg, 'pages': [span[0], span[-1]] if span else []}))
    unpaged = [by[i] for i in source['element_ids'] if (by[i].get('locator') or {}).get(info['page_key']) is None]
    if sections and unpaged:
        sections[0][1].extend(unpaged)
    return sections


_TITLE_DANGLING = re.compile(r'(\b(to|for|of|and|or|in|on|with|the|a|an|und|oder|für|der|die|das|des|von|mit|zu|im|in)|[-–—:&+,])\s*$', re.I)


def _title_key(t):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w ]', ' ', (t or '').lower())).strip()


def _full_title(head, els):
    """Slide titles are often wrapped over two text lines; a first line ending in a connector or dash continues."""
    t = re.sub(r'\s+', ' ', head['normalized_text']).strip()
    nxt = next((e for e in els[:2] if e['kind'] in ('heading', 'paragraph') and e['text'].strip()), None)
    if nxt and _TITLE_DANGLING.search(t):
        cont = re.sub(r'\s+', ' ', nxt['text']).strip()
        if 0 < len(cont) <= 80 and '\n' not in nxt['text'].strip():
            t = (t.rstrip(' -–—') + (' – ' if re.search(r'[-–—]\s*$', t) else ' ') + cont).strip()
    return t


def _stem_title(relative_path):
    """Readable title from a file name: URL-escaped blanks ('_20', '%20') decoded, leading lecture number removed."""
    st = Path(relative_path).stem
    st = re.sub(r'(_|%)20', ' ', st).replace('_', ' ')
    st = re.sub(r'^\s*\d{4}-\d{2}-\d{2}\s*[-–]?\s*', '', st)          # leading ISO date '2026-06-23 - '
    m = re.match(r'^[^\d,]{2,40}?\s\d{1,2}\s*,\s*(.+)$', st)             # 'Patentrecht 02, Patentierungsvoraussetzungen'
    if m:
        st = m.group(1)
    st = re.sub(r'^\s*\d{1,3}\s*[-–.:)]?\s*', '', st)
    return re.sub(r'\s+', ' ', st).strip(' -–') or Path(relative_path).stem


def _course_header_titles(lecture_like, secs_by):
    """Normalised first titles that open two or more DIFFERENT lecture decks (different file stems): course headers
    such as 'Reinforcement Learning WS 25/26 Prof. X'. Same-stem copies (versions of one deck) do not count."""
    seen = {}
    for s in lecture_like:
        secs = secs_by[s['source_id']]
        if len(secs) != 1 or not secs[0][0]:
            continue
        seen.setdefault(_header_key(secs[0][0]['normalized_text']), set()).add(_title_key(_stem_title(s['relative_path'])))
    return {k for k, stems in seen.items() if k and len(stems) >= 2}


def _header_key(t):
    """Course-header comparison ignores session numbers: 'Patentrecht - Termin 01' and '... Termin 02' are one header."""
    return re.sub(r'\d+', '#', _title_key(t))


def _sections(manifest, source, pm=None):
    """Ordered (heading_element_or_None, [elements]) top-level sections of one source."""
    by = {e['element_id']: e for e in manifest['elements']}
    if pm and source['source_id'] in pm:
        return [(h, e) for h, e, _ in _paged_sections(manifest, source, pm)]
    els = [by[i] for i in source['element_ids']]
    heads = [e for e in els if e['kind'] == 'heading']
    if source['format'] in ('.pptx', '.pdf') or not heads:  # a deck/PDF is one narrative; slide titles are sub-topics
        return [(heads[0] if heads else None, [e for e in els if not heads or e is not heads[0]])]
    top = min(_level(h) for h in heads)
    sections = []; cur = [None, []]
    for e in els:
        if e['kind'] == 'heading' and _level(e) == top:
            if cur[0] is not None or cur[1]:
                sections.append(tuple(cur))
            cur = [e, []]
        else:
            cur[1].append(e)
    if cur[0] is not None or cur[1]:
        sections.append(tuple(cur))
    return sections


BUSINESS_RX = re.compile(r'\b(markets?|customers?|revenues?|investors?|investments?|financing|funding|business models?|pricing|'
                         r'valuation|ventures?|start-?ups?|profits?|equity|competitors?|marketing|cash flow|'
                         r'markt|kunden?|umsatz|investoren?|finanzierung|kosten|gewinn|geschäftsmodell|wettbewerb|bilanz)\b')


def _domain_profile(manifest, roles=None):
    """Subject signals per source; a profile is active only with >=2 signals in total AND evidence in at least
    max(1, round(0.3 * academic sources)) sources. Otherwise UNRESOLVED (no subject preset, no single-word guess)."""
    roles = roles or {}
    by_src = {}
    for e in manifest['elements']:
        by_src.setdefault(e['source_id'], []).append(e)
    counted = [s for s in manifest['sources'] if roles.get(s['source_id'], {}).get('role') not in
               ('COURSE_ADMINISTRATION', 'TEMPLATE_LAYOUT', 'CASE_STUDY_BRIEF')]
    academic = [s for s in counted if roles.get(s['source_id'], {}).get('role', 'ACADEMIC_CONTENT') in ('ACADEMIC_CONTENT', 'REVIEW_REQUIRED')]
    per = {}
    for s in counted:
        els = by_src.get(s['source_id'], [])
        text = ' '.join(e['normalized_text'] for e in els if e['kind'] != 'code')[:400000].lower()
        per[s['source_id']] = {
            'formal_mathematics': len(re.findall(r'\b(satz|theorem|lemma|beweis|proof|korollar|corollary)\b', text)) +
                                  sum(1 for e in els if e['kind'] == 'formula') // 3,
            'law': len(NORM_PATTERN.findall(text)) + len(re.findall(r'\b(anspruch|sachverhalt|tatbestand|rechtsfolge|subsum)', text)),
            'computing': sum(1 for e in els if e['kind'] == 'code') +
                         len(re.findall(r'\b(algorithm|algorithmus|implement|function|python|dataset|training)\b', text)),
            'empirical_science': len(re.findall(r'\b(experiment|hypothes|messung|measurement|stichprobe|sample)\w*', text)),
            'business_economics': len(BUSINESS_RX.findall(text)) // 3}
    need = max(1, round(0.3 * len(academic)))
    signals = {k: sum(v[k] for v in per.values()) for k in ('formal_mathematics', 'law', 'computing', 'empirical_science', 'business_economics')}
    spread = {k: sum(1 for v in per.values() if v[k] >= 3) for k in signals}
    single = len(academic) <= 1
    active = sorted(k for k in signals if (signals[k] >= 2 if single else signals[k] >= 5) and
                    (spread[k] >= need or single and any(v[k] >= 2 for v in per.values())))
    return {'signals': signals, 'sources_with_signal': spread, 'required_source_spread': need,
            'active_profiles': active or ['UNRESOLVED'],
            'per_source': {sid: {k: v for k, v in d.items() if v} for sid, d in per.items()},
            'basis': 'per-source lexical/structural signals; active only with spread across sources; '
                     'administration/template sources excluded; UNRESOLVED instead of a guess'}

def _assessment_items(manifest, sources):
    items = []; src_by = {s['source_id']: s for s in sources}
    solutions = [s for s in sources if s['authority'] == 'OFFICIAL_SOLUTION']
    by = {e['element_id']: e for e in manifest['elements']}
    sol_text = {s['source_id']: '\n'.join(by[i]['text'] for i in s['element_ids']) for s in solutions}
    for s in sources:
        if s['authority'] not in ('OFFICIAL_EXAM', 'OFFICIAL_EXERCISE'):
            continue
        els = [by[i] for i in s['element_ids'] if by[i]['kind'] in ('paragraph', 'heading', 'list_item')]
        # Map each line of concatenated text to its element for anchors.
        lines = []
        for e in els:
            for ln in e['text'].splitlines():
                lines.append((ln, e['element_id']))
        blocks = []; cur = None
        for ln, eid in lines:
            m = ITEM_HEAD.match(ln)
            if m:
                cur = {'number': m.group(2), 'lines': [(ln, eid)]}; blocks.append(cur)
            elif cur:
                cur['lines'].append((ln, eid))
        for b in blocks:
            parts = []; head = []; sub = None
            for ln, eid in b['lines']:
                m = SUB_HEAD.match(ln)
                if m:
                    sub = {'label': m.group(1), 'lines': [(ln, eid)]}; parts.append(sub)
                elif sub:
                    sub['lines'].append((ln, eid))
                else:
                    head.append((ln, eid))
            stem = '\n'.join(l for l, _ in head)
            for p in (parts or [{'label': None, 'lines': []}]):
                own = '\n'.join(l for l, _ in p['lines'])
                full = (stem + '\n' + own).strip()
                ops = operations_in(own or stem)  # operation from the item's own wording
                label = f"{b['number']}{p['label'] or ''}"
                pts = POINTS.search(own or stem)
                anchors = sorted({e for _, e in head + p['lines']})
                stem_terms = set(re.findall(r'[a-z0-9]+', Path(s['relative_path']).stem.lower()))
                cands = sorted(((len(stem_terms & set(re.findall(r'[a-z0-9]+', Path(src_by[sid]['relative_path']).stem.lower()))), sid)
                                for sid, t in sol_text.items()
                                if re.search(rf'(Aufgabe|Problem|Exercise|Frage|Question|Task)\s*{b["number"]}\b', t, re.I)), reverse=True)
                sol = cands[0][1] if cands and cands[0][0] > 0 else None  # same-number match AND shared file-name token
                items.append({
                    'item_id': 'q-' + _h(s['source_id'] + '|' + label)[:14], 'label': label, 'source_id': s['source_id'],
                    'kind': 'past_exam' if s['authority'] == 'OFFICIAL_EXAM' else 'exercise',
                    'text': full, 'own_wording': own or stem, 'anchor_element_ids': anchors,
                    'actual_operations': ops, 'operation_basis': 'lexicon_on_item_wording',
                    'format': 'multiple_choice' if MC_PATTERN.search(full) else 'open',
                    'has_concrete_instance': bool(CASE_PATTERN.search(ITEM_HEAD.sub('', POINTS.sub('', full)))),
                    'norm_refs': sorted({m.group(0).strip() for m in NORM_PATTERN.finditer(full)}),
                    'points': float(pts.group(1).replace(',', '.')) if pts else None,
                    'solution_source_id': sol,
                    'solution_status': 'SOLUTION_SOURCE_FOUND_UNVERIFIED' if sol else 'NO_SOLUTION_SOURCE',
                    'official': True})
    return items



def _formal_name(body, label=None):
    """Name of a formal object (Satz/Lemma/Definition ...). A number like '2.29' is part of the name, never all of it:
    'Lemma 2.29. Seien (a_n) ...' -> '2.29 Seien (a_n) ...' (before, every 'Lemma 2.x' collapsed into 'Lemma: 2')."""
    if label:
        return label.strip()
    num = re.match(r'(\d+(?:\.\d+)*)\.?\s+', body)
    if num:
        clause = re.split(r'(?<=[0-9a-zäöüß)])[.:]\s|\n', body[num.end():])[0][:90].strip()
        return f"{num.group(1)} {clause}".strip()
    return (re.split(r'[.:\n]', body)[0][:120] or body[:120]).strip()

def _kc(statement, ops, basis, anchors, source, origin, inferred, by):
    st = re.sub(r'\s+', ' ', statement).strip(' -*•:')
    anchor_text = ' '.join(by[a]['normalized_text'] for a in anchors)
    return {'kc_id': 'kc-' + _h(semantic_key(st))[:14], 'semantic_key': semantic_key(st), 'statement': st,
            'operations': ops, 'operation_basis': basis, 'source_anchor_ids': anchors,
            'source_ids': [source['source_id']] if source else [], 'official': bool(source and source['authority'].startswith('OFFICIAL')),
            'status_official_vs_supplementary': 'official' if source and source['authority'].startswith('OFFICIAL') else 'supplementary',
            'inferred': inferred, 'origin': origin, 'norm_refs': sorted({m.group(0).strip() for m in NORM_PATTERN.finditer(st + ' ' + anchor_text)}),
            'prerequisite_kc_ids': [], 'prerequisite_basis': {}, 'cross_references': [], 'chapter_id': None,
            'notation_refs': [], '_terms': terms(st)}


def _bullet_lines(text):
    """(line, is_sub) for objective slides: a line after a bare bullet glyph line or starting with a bullet is a
    sub-item of the preceding non-bullet line."""
    out, pending = [], False
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if re.fullmatch(r'[▪•\-–·]', ln):
            pending = True; continue
        m = re.match(r'^[▪•\-–·]\s+(.*)$', ln)
        if m:
            out.append((m.group(1).strip(), True)); pending = False; continue
        out.append((ln, pending)); pending = False
    return out


def scan_scope(manifest, sid):
    """TEXT_LAYER_MISSING pages of a source and whether the gap is source-wide (>=20% of pages or a source of <=5
    pages: locality cannot be established) or local (only the page and its neighbours depend on it)."""
    pages = sorted({int(m.group(1)) for g in manifest['gaps'] if g['source_id'] == sid and g['code'] == 'TEXT_LAYER_MISSING'
                    for m in [re.search(r'Page (\d+)', str(g['detail']))] if m})
    if not pages:
        return None, []
    total = len({(e.get('locator') or {}).get('page') for e in manifest['elements'] if e['source_id'] == sid} - {None}) + len(pages)
    wide = total <= 5 or len(pages) >= 0.2 * total
    return ('SOURCE_WIDE' if wide else 'LOCAL'), pages


def scan_affects(manifest, sid, anchor_ids, by, neighbours=0):
    scope, pages = scan_scope(manifest, sid)
    if scope is None:
        return False
    if scope == 'SOURCE_WIDE':
        return True
    anchor_pages = {(by[a].get('locator') or {}).get('page') for a in anchor_ids if a in by and by[a]['source_id'] == sid}
    return any(ap is not None and any(abs(ap - p) <= neighbours for p in pages) for ap in anchor_pages)


SECTION_END = re.compile(r'^\s*(?:#+\s*)?(case study|case studies|fallstudie|appendix|anhang)\b', re.I)
SECTION_LABEL = re.compile(r'\b(session|lecture|chapter|kapitel|vorlesung|woche|week|unit|lektion|einheit|sitzung)\s*(\d{1,2})\b', re.I)


def _question_items(manifest, sources, roles):
    """Questions inside any non-exam source, typed by the source's role: PRACTICE (question catalogue/exercise),
    CASE_STUDY, TEMPLATE_QUESTION, LECTURE_QUESTION (in lecture material; never exam weight or coverage evidence).
    Points only when stated in the item wording."""
    from .triage import NUMBERED_Q, _is_question
    by = {e['element_id']: e for e in manifest['elements']}
    kind_of = {'PRACTICE_QUESTIONS': 'PRACTICE', 'CASE_STUDY_BRIEF': 'CASE_STUDY', 'TEMPLATE_LAYOUT': 'TEMPLATE_QUESTION',
               'ACADEMIC_CONTENT': 'LECTURE_QUESTION', 'REVIEW_REQUIRED': 'LECTURE_QUESTION'}
    items = []
    for s in sources:
        role = roles[s['source_id']]['role']
        if role not in kind_of or s['authority'] in ('OFFICIAL_EXAM', 'OFFICIAL_EXERCISE'):
            continue
        kind = kind_of[role]
        # Flatten all text lines of the source (reading order) so that a number standing alone in one block joins
        # the question text in the next block; keep (element, line index) for anchors and stable ids.
        seq, section = [], None
        # On paged sources a section label is a page heading wherever it sits in reading order: it applies to the
        # whole page. Elsewhere (Markdown etc.) a label applies to what follows it.
        page_label = {}
        for i in s['element_ids']:
            e = by[i]; pg = (e.get('locator') or {}).get('page', (e.get('locator') or {}).get('slide'))
            sm = SECTION_LABEL.search(e['text']) if e['kind'] in ('heading', 'paragraph') and len(e['text']) < 80 else None
            if sm and pg is not None:
                page_label.setdefault(pg, (sm.group(0).strip(), int(sm.group(2))))
            elif pg is not None and e['kind'] in ('heading', 'paragraph') and len(e['text']) < 80 and SECTION_END.search(e['text']):
                page_label.setdefault(pg, (SECTION_END.search(e['text']).group(0).strip(), None))   # B14: case study / appendix
        for i in s['element_ids']:
            e = by[i]
            if e['kind'] not in ('heading', 'paragraph', 'list_item'):
                continue
            pg = (e.get('locator') or {}).get('page', (e.get('locator') or {}).get('slide'))
            sm = SECTION_LABEL.search(e['text'])
            if pg is not None and pg in page_label:
                section = page_label[pg] if page_label[pg][1] is not None else None
            elif sm and len(e['text']) < 80:
                section = (sm.group(0).strip(), int(sm.group(2)))
            elif e['kind'] == 'heading' and len(e['text']) < 80 and SECTION_END.search(e['text']):
                section = None
            for n, ln in enumerate(e['text'].splitlines()):
                if ln.strip():
                    seq.append({'text': ln.strip(), 'eids': [e['element_id']], 'id': f"{e['element_id']}|{n}", 'e': e,
                                'list_item': e['kind'] == 'list_item', 'section': section})
        merged = []
        for x in seq:
            prev = merged[-1] if merged else None
            if prev and re.fullmatch(r'\d{1,3}[.)]', prev['text']):
                prev.update(text=prev['text'] + ' ' + x['text'], eids=prev['eids'] + x['eids']); continue
            if prev and re.match(r'^\d{1,3}[.)]\s+\S', prev['text']) and not re.match(r'^\d{1,3}[.)](\s|$)', x['text']) \
                    and (not prev['text'].endswith(('?', '.')) or kind == 'PRACTICE') and len(prev['text']) < 400 and x['e'] is prev['e']:
                prev.update(text=prev['text'] + ' ' + x['text']); continue   # wrapped line inside the same block
            merged.append(dict(x))
        for x in merged:
            ln, e, section = x['text'], x['e'], x['section']
            m = NUMBERED_Q.match(ln)
            if kind == 'LECTURE_QUESTION':
                ok = ln.endswith('?') and len(ln) >= 12
            else:
                # in a practice-question source a numbered entry is a task by role (stem + instruction need no '?')
                ok = (kind == 'PRACTICE' and bool(m) and len(ln.split()) >= 4) or \
                     (bool(m) or (x['list_item'] and kind == 'PRACTICE')) and _is_question(ln) or \
                     (ln.endswith('?') and len(ln) >= 12 and kind != 'PRACTICE')
            if not ok:
                continue
            own = NUMBERED_Q.sub(r'\2', ln) if m else ln
            pts = POINTS.search(own)
            items.append({'item_id': 'q-' + _h(x['id'])[:14],
                          'label': (m.group(1) if m else ('L' if x['list_item'] else '?')) + '@' + e['locator_str'].split('/', 1)[-1][:40],
                          'source_id': s['source_id'], 'kind': kind.lower(), 'assessment_kind': kind,
                          'evidence_eligible': kind == 'PRACTICE', 'text': ln, 'own_wording': own,
                          'anchor_element_ids': sorted(set(x['eids'])), 'actual_operations': operations_in(own),
                          'operation_basis': 'lexicon_on_item_wording',
                          'format': 'multiple_choice' if MC_PATTERN.search(own) else 'open',
                          'has_concrete_instance': bool(CASE_PATTERN.search(POINTS.sub('', own))),
                          'norm_refs': sorted({x.group(0).strip() for x in NORM_PATTERN.finditer(own)}),
                          'points': float(pts.group(1).replace(',', '.')) if pts else None,
                          'points_basis': 'STATED_IN_ITEM' if pts else 'NOT_STATED',
                          'solution_source_id': None, 'solution_status': 'NO_SOLUTION_SOURCE',
                          'official': s['authority'].startswith('OFFICIAL'),
                          'classification_basis': f"source role {role}",
                          'section_label': section[0] if section else None, 'section_number': section[1] if section else None})
    # B14: a truncated copy of another item of the same source (e.g. a task repeated beside a case-study canvas, cut by
    # the layout) is the same task, not a second one: keep the complete wording only.
    norm = lambda t: re.sub(r'\s+', ' ', t).strip().casefold()
    keep = []
    for a in items:
        wa = norm(a['own_wording'])
        dup = len(wa) >= 40 and any(b is not a and b['source_id'] == a['source_id'] and len(norm(b['own_wording'])) > len(wa)
                                    and norm(b['own_wording']).startswith(wa) for b in items)
        if not dup:
            keep.append(a)
    return keep


def compile_curriculum(manifest, out=None, decisions: SemanticDecisions | None = None, provider=None):
    if provider is not None:
        raise ContractError('P2 planning is offline: no provider may be passed')
    decisions = decisions or SemanticDecisions()
    eids = {e['element_id'] for e in manifest['elements']}
    decisions.validate(eids)
    by = {e['element_id']: e for e in manifest['elements']}
    sources = manifest['sources']
    src_by = {s['source_id']: s for s in sources}
    gap_by_source = {}
    for g in manifest['gaps']:
        gap_by_source.setdefault(g['source_id'], set()).add(g['code'])
    from .triage import page_model, source_roles, source_classification, candidate_reject, admin_page, CHAPTER_ROLES, _norm as _tnorm
    pages_m = page_model(manifest)
    roles = source_roles(manifest, pages_m)
    items = _assessment_items(manifest, sources) + _question_items(manifest, sources, roles)
    for q in items:
        q.setdefault('assessment_kind', 'OFFICIAL_EXAM' if q['kind'] == 'past_exam' else 'PRACTICE')
        q.setdefault('evidence_eligible', True)
        q.setdefault('points_basis', 'STATED_IN_ITEM' if q['points'] is not None else 'NOT_STATED')
    kcs = {}; chapters = []; notation = {}; stated_prereqs = []

    def add(kc):
        if kc['kc_id'] in kcs:
            old = kcs[kc['kc_id']]
            old['source_anchor_ids'] = sorted(set(old['source_anchor_ids']) | set(kc['source_anchor_ids']))
            old['source_ids'] = sorted(set(old['source_ids']) | set(kc['source_ids']))
            return old
        kcs[kc['kc_id']] = kc; return kc

    textual = lambda s: sum(len(by[i]['normalized_text']) for i in s['element_ids']
                            if by[i]['kind'] in ('heading', 'paragraph', 'list_item')) >= 40
    # P3.3: chapters come from sources whose ROLE is academic content (authority is not relevance). Administration,
    # templates, case-study briefs and question catalogues stay in the inventory but never form chapters.
    lecture_like = [s for s in sources if roles[s['source_id']]['role'] in CHAPTER_ROLES and textual(s)]
    supporting = [s for s in sources if s not in lecture_like and s['element_ids'] and
                  roles[s['source_id']]['role'] == 'SUPPORTING_MATERIAL']
    rejected_candidates, segmentation = [], {}
    secs_by = {s['source_id']: (_paged_sections(manifest, s, pages_m) if s['source_id'] in pages_m else
                                [(h, e, None) for h, e in _sections(manifest, s)]) for s in lecture_like}
    header_titles = _course_header_titles(lecture_like, secs_by)
    for s in lecture_like:
        secs = secs_by[s['source_id']]
        for head, els, seg in secs:
            if head and TOC_HEAD.search(head['normalized_text'][:60]) and not any(
                    OBJ_HEAD.search(e['text'][:80]) or FORMAL_HEAD.match(e['text']) for e in els):
                continue  # a table of contents / syllabus is ordering evidence, not a subject chapter
            title = _full_title(head, els) if head else ''
            title_basis = 'SOURCE_TITLE'
            if not title or _header_key(title) in header_titles or _header_key(head['normalized_text'] if head else '') in header_titles:
                # A title shared by several separate lecture decks is a course header, not the subject of this deck.
                title, title_basis = _stem_title(s['relative_path']), ('FILENAME_STEM_COURSE_HEADER' if title else 'FILENAME_STEM')
            ch = {'chapter_id': 'ch-' + _h(re.sub(r'^\W*(\d+[.)]?\s*)?', '', title.lower()))[:14], 'title': title,
                  'source_ids': [s['source_id']], 'anchor_element_ids': ([head['element_id']] if head else []) + [e['element_id'] for e in els],
                  'kc_ids': [], 'origin': 'source_structure', 'official': s['authority'].startswith('OFFICIAL'),
                  'title_basis': title_basis}
            existing = next((c for c in chapters if c['chapter_id'] == ch['chapter_id']), None)
            if existing:
                existing['source_ids'] = sorted(set(existing['source_ids']) | {s['source_id']})
                existing['anchor_element_ids'] += ch['anchor_element_ids']; ch = existing
            else:
                chapters.append(ch)
            ch['source_role'] = roles[s['source_id']]['role']
            if seg:
                ch.setdefault('segmentation', []).append({'source_id': s['source_id'], **seg})
            in_objectives = bool(head and OBJ_HEAD.search(head['text'][:80]))
            for idx, e in enumerate(els):
                t = e['text']
                if e['kind'] in ('heading', 'paragraph') and OBJ_HEAD.search(t[:80]):
                    in_objectives = True
                    # Objectives can follow inline: listed lines, or one sentence joined by and/und.
                    rest = re.split(r'[:\n]', t, maxsplit=1)[1] if re.search(r'[:\n]', t) else ''
                    listed = [ln.strip() for ln in rest.splitlines() if re.match(r'\s*([-*•]|\d+[.)])\s', ln)]
                    if not listed and operations_in(rest):
                        sentence = re.sub(r'^\s*(you will be able to|sie können|students (can|will))\s*', '', re.sub(r'\s+', ' ', rest).strip(), flags=re.I)
                        pieces = [x.strip() for x in re.split(r'\s*;\s*|\s+(?:and|und|sowie)\s+(?=\w+)', sentence) if x.strip()]
                        listed = [x for x in pieces if operations_in(x)] if all(operations_in(x) for x in pieces) else [sentence]
                    for ln in listed:
                        if ln:
                            ops = operations_in(ln)
                            kc = add(_kc(re.sub(r'^([-*•]|\d+[.)])\s+', '', ln), ops or ['EXPLAIN'],
                                         'stated_objective_verb' if ops else 'default_EXPLAIN_no_verb', [e['element_id']], s,
                                         'stated_learning_objective', not ops, by))
                            kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']
                    continue
                if in_objectives and e['kind'] == 'list_item':
                    ops = operations_in(t)
                    kc = add(_kc(t, ops or ['EXPLAIN'], 'stated_objective_verb' if ops else 'default_EXPLAIN_no_verb',
                                 [e['element_id']], s, 'stated_learning_objective', not ops, by))
                    kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']; continue
                if e['kind'] != 'list_item':
                    in_objectives = False
                fm = FORMAL_HEAD.match(t) if e['kind'] in ('paragraph', 'definition_block', 'heading') else None
                env = (e.get('structure') or {}).get('environment') if isinstance(e.get('structure'), dict) else None
                if fm or env in ('definition', 'theorem', 'lemma', 'satz'):
                    kind = (fm.group(1) if fm else env).lower()
                    body = (fm.group(3) if fm else re.sub(r'\\(begin|end)\{\w+\}', '', t)).strip()
                    name = _formal_name(body, fm.group(2) if fm else None)
                    if kind == 'definition':
                        ops, stmt = ['DEFINE'], f'Definition: {name}'
                    else:
                        following = [x for x in els[idx + 1:] if x['kind'] != 'formula'][:2]
                        nxt = ' '.join(x['text'][:30].lower() for x in following)
                        has_proof = bool(re.search(r'beweis|proof', nxt)) or any(
                            (x.get('structure') or {}).get('environment') in ('proof', 'beweis') for x in following
                            if isinstance(x.get('structure'), dict))
                        ops, stmt = (['PROVE'] if has_proof else ['EXPLAIN']), f'{kind.capitalize()}: {name}'
                    kc = add(_kc(stmt, ops, 'inferred_from_formal_object', [e['element_id']] + [x['element_id'] for x in els[idx + 1:idx + 2]],
                                 s, 'formal_object', True, by))
                    kc['defined_term'] = (re.sub(r'^\d+(?:\.\d+)*\s*', '', name).lower() or name.lower()) if kind == 'definition' else None
                    kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']
                pm = PREREQ_HEAD.match(t)
                if pm:
                    stated_prereqs.append((ch['chapter_id'], terms(pm.group(3) or ' '.join(x['text'] for x in els[idx + 1:idx + 4])),
                                           e['element_id']))
                for rx in (NOTATION, NOTATION_LET):
                    for nm in rx.finditer(t):
                        sym = nm.group(1).strip(); meaning = re.sub(r'\s+', ' ', nm.group(2)).strip().lower()
                        notation.setdefault(sym, []).append({'meaning': meaning, 'element_id': e['element_id'],
                                                             'source_id': s['source_id'], 'chapter_id': ch['chapter_id']})
            for e in els:  # definitions of norms in law material
                if e['kind'] in ('heading', 'paragraph') and NORM_PATTERN.match(e['text'].strip()):
                    kc = add(_kc(f"Anwendung/Subsumtion: {e['normalized_text'][:120]}", ['SUBSUME'], 'inferred_from_norm_heading',
                                 [e['element_id']], s, 'norm', True, by))
                    kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']
            if s['source_id'] in pages_m:  # objective slides: bullets under a 'Learning objectives' page title
                pinfo = pages_m[s['source_id']]
                span = {(e.get('locator') or {}).get(pinfo['page_key']) for e in els + ([head] if head else [])}
                for pg in sorted(x for x in span if x is not None):
                    t_el = pinfo['pages'][pg]['title']
                    if not t_el or not OBJ_HEAD.search(t_el['text'][:80]):
                        continue
                    parent = None   # hierarchy spans the text blocks of one objective slide
                    for o in pinfo['pages'][pg]['elements']:
                        if o is t_el or o['kind'] not in ('heading', 'paragraph', 'list_item') or _tnorm(o['text']) in pinfo['boilerplate']:
                            continue
                        for ln, is_sub in _bullet_lines(o['text']):
                            if len(ln) < 12 or candidate_reject(ln, pinfo['boilerplate']) in ('NON_LEXICAL', 'URL_OR_EMAIL', 'CITATION_OR_SOURCE_LINE'):
                                continue
                            if ln.rstrip().endswith('?') or re.match(r'(what|why|how|which|who|when|where|was|warum|wie|welche[rs]?|wer|wann|wo)\b', ln, re.I):
                                continue  # a guiding question under an objective is not an objective (kept as LECTURE_QUESTION)
                            ops = operations_in(ln)
                            kc = add(_kc(ln, ops or ['EXPLAIN'], 'stated_objective_verb' if ops else 'default_EXPLAIN_no_verb',
                                         [o['element_id']], s, 'stated_learning_objective', not ops, by))
                            kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']
                            kc['objective_level'] = 'SUB_OBJECTIVE' if is_sub and parent else 'OBJECTIVE'
                            if is_sub and parent:
                                kc['parent_objective_kc_id'] = parent
                            else:
                                parent = kc['kc_id']
            explicit = any(k['chapter_id'] == ch['chapter_id'] for k in kcs.values())
            # Paged sources: pages without an explicit-KC anchor still get page-title topic candidates, otherwise one
            # stated objective would leave the rest of a long deck without any competency (silent loss).
            if not explicit or s['source_id'] in pages_m:
                # Topic candidates become inferred EXPLAIN KCs, flagged for review.
                # Paged sources: one candidate per page TITLE (not every large-font span); all: filtered with a reason.
                if s['source_id'] in pages_m:
                    pinfo = pages_m[s['source_id']]
                    span = {(e.get('locator') or {}).get(pinfo['page_key']) for e in els + ([head] if head else [])}
                    covered = {(by[a].get('locator') or {}).get(pinfo['page_key']) for k in kcs.values()
                               if k['chapter_id'] == ch['chapter_id'] for a in k['source_anchor_ids'] if by[a]['source_id'] == s['source_id']}
                    cands = [(pinfo['pages'][p]['title'], admin_page(pinfo['pages'][p]),
                              [o['text'] for o in pinfo['pages'][p]['elements'] if o is not pinfo['pages'][p]['title']])
                             for p in sorted(x for x in span if x is not None) if pinfo['pages'][p]['title'] and p not in covered]
                    boiler = pinfo['boilerplate']; origin, basis = 'slide_title_topic', 'inferred_from_page_title'
                else:
                    heads = [x for x in els if x['kind'] == 'heading' and not OBJ_HEAD.search(x['text'])] or ([head] if head else [])
                    cands = [(x, False, [y['text'] for y in els[els.index(x) + 1:] if y['kind'] != 'heading'][:12] if x in els else [])
                             for x in heads]
                    boiler = frozenset(); origin, basis = 'heading_topic', 'inferred_from_heading_only'
                seen_keys = set()
                for e, is_admin, page_texts in cands:
                    why = candidate_reject(e['text'], boiler, is_admin)
                    key = semantic_key(e['normalized_text'][:120])
                    if not why and key in seen_keys:
                        why = 'DUPLICATE_MERGED'  # same topic again: its anchor joins the existing cluster
                    if why:
                        rejected_candidates.append({'element_id': e['element_id'], 'source_id': s['source_id'],
                                                    'chapter_id': ch['chapter_id'], 'reason': why})
                        if why != 'DUPLICATE_MERGED':
                            continue
                    seen_keys.add(key)
                    ops, op_ev = topic_operations(e['normalized_text'], page_texts)
                    # The id stays derived from the topic (verbs are stop words), so decisions bound to it survive.
                    fresh = _kc(f"Erkläre/explain: {e['normalized_text'][:120]}", ops, basis, [e['element_id']], s, origin, True, by)
                    kc = add(fresh)
                    if kc is fresh:
                        kc['topic_text'] = re.sub(r'\s+', ' ', e['normalized_text'][:120]).strip(' -*•:')
                        kc['operation_evidence'] = op_ev
                    else:
                        for o in ops:
                            if o not in kc['operations']:
                                kc['operations'].append(o); kc.setdefault('operation_evidence', []).append({'operation': o, 'basis': 'merged_topic_page'})
                    kc['chapter_id'] = kc['chapter_id'] or ch['chapter_id']; kc['confidence'] = 'LOW'
                ch['kc_extraction_status'] = ('EXPLICIT_OBJECTIVES_PLUS_PAGE_TOPIC_CANDIDATES' if explicit else
                                              'NO_EXPLICIT_COMPETENCY_SIGNALS_TOPIC_CANDIDATES_ONLY')
            else:
                ch['kc_extraction_status'] = 'EXPLICIT_OBJECTIVES_OR_FORMAL_OBJECTS'

    # Supporting sources (code, data, notebooks, figures) feed the best-matching chapter's source package.
    for s in supporting:
        st = terms(' '.join(by[i]['normalized_text'] for i in s['element_ids']))
        best = max(chapters, key=lambda c: len(st & terms(' '.join(by[a]['normalized_text'] for a in c['anchor_element_ids']))), default=None)
        if best is not None and st & terms(' '.join(by[a]['normalized_text'] for a in best['anchor_element_ids'])):
            best.setdefault('supporting_source_ids', []).append(s['source_id'])
            best['anchor_element_ids'] += s['element_ids']
    for c in chapters:  # figures referenced from a chapter pull in the image file's elements
        for a in list(c['anchor_element_ids']):
            linked = (by[a].get('structure') or {}).get('linked_source_id') if isinstance(by[a].get('structure'), dict) else None
            if linked and linked in src_by:
                c['anchor_element_ids'] += [x for x in src_by[linked]['element_ids'] if x not in c['anchor_element_ids']]

    chapters, merge_log = _merge_chapters(chapters, kcs, by, src_by, decisions)
    alias = {m['merged']: m['into'] for m in merge_log if m['decision'] == 'MERGED'}
    stated_prereqs = [(alias.get(c, c), t, e) for c, t, e in stated_prereqs]
    for uses in notation.values():
        for u in uses:
            u['chapter_id'] = alias.get(u['chapter_id'], u['chapter_id'])

    # Human scope decisions: competencies the planner missed, anchored in the sources, assigned to an existing chapter.
    for d in decisions.of('competency'):
        v = d['value']; anchors = [a for a in v['anchor_element_ids'] if a in by]
        if not anchors or not any(c['chapter_id'] == d['subject_id'] for c in chapters):
            continue
        k = add(_kc(v['statement'], list(v['operations']), 'semantic_decision:human', anchors, src_by.get(by[anchors[0]]['source_id']),
                    'human_scope_decision', False, by))
        k['chapter_id'] = d['subject_id']; k['chapter_assignment_basis'] = 'semantic_decision'
        k['scope_decision_rationale'] = d['rationale']
    for d in decisions.of('operation'):
        if d['subject_id'] in kcs:
            kcs[d['subject_id']].update(operations=list(d['value']), operation_basis='semantic_decision:' + d.get('decided_by', 'fixture'),
                                        inferred=d.get('decided_by') != 'reviewer')
    # B6.4: an operation decision may also name an assessment item: it replaces the lexicon reading of what the item
    # demands (e.g. 'reasons why ...' is not an EXPLAIN task). The wording stays unchanged; the coverage gate still
    # checks the decided operations against every KC, so a decision can only narrow, never force, coverage.
    item_ids = {q['item_id']: q for q in items}
    for d in decisions.of('operation'):
        if d['subject_id'] in item_ids:
            item_ids[d['subject_id']].update(actual_operations=sorted(set(d['value'])),
                                             operation_basis='semantic_decision:' + d.get('decided_by', 'fixture'),
                                             operation_decision_rationale=d['rationale'])

    # Links item <-> KC: lexical topic overlap (inferred) plus explicit decisions. Never coverage by itself.
    links = {}
    term_chapters = {}
    for k in kcs.values():
        for t in k['_terms'] | terms(' '.join(by[a]['normalized_text'] for a in k['source_anchor_ids'])):
            term_chapters.setdefault(t, set()).add(k['chapter_id'])
    for q in items:
        q['candidate_kc_ids'] = []; q['link_status'] = 'LINKED_OR_DERIVED'
        qt = terms(q['own_wording'])
        scored = []
        for k in kcs.values():
            kt = k['_terms'] | terms(' '.join(by[a]['normalized_text'] for a in k['source_anchor_ids']))
            overlap = qt & kt
            scored.append((len(overlap) / (len(qt | kt) or 1), overlap, k))
        best = max((x[0] for x in scored), default=0)
        for sim, overlap, k in scored:
            shared_norms = set(q['norm_refs']) & set(k['norm_refs'])
            # Relative Jaccard: only KCs close to the item's best topical match are linked (inferred, review pending).
            if overlap and best >= 0.15 and sim >= LINK_RELATIVE * best and len(overlap) == 1 and \
                    len(term_chapters.get(next(iter(overlap)), ())) > 1:
                q['candidate_kc_ids'].append(k['kc_id'])  # one non-specific shared term: never evidence
                q['link_status'] = 'AMBIGUOUS_TOPIC_PENDING_SEMANTIC_DECISION'
            elif overlap and best >= 0.15 and sim >= LINK_RELATIVE * best:
                links.setdefault(k['kc_id'], {})[q['item_id']] = {'basis': 'lexical_overlap', 'inferred': True, 'shared_terms': sorted(overlap), 'jaccard': round(sim, 3)}
            elif shared_norms:
                links.setdefault(k['kc_id'], {})[q['item_id']] = {'basis': 'shared_norm_reference', 'inferred': True, 'shared_norms': sorted(shared_norms)}
    for d in decisions.of('link'):
        if d['subject_id'] in kcs:
            for qid in d['value']:
                links.setdefault(d['subject_id'], {})[qid] = {'basis': 'semantic_decision:' + d.get('decided_by', 'fixture'),
                                                              'inferred': True, 'rationale': d['rationale']}
    # Exam items without any competency become exam-derived KCs so the exam scope is planned, not dropped.
    linked_items = {qid for v in links.values() for qid in v}
    for q in items:
        if q['item_id'] not in linked_items and q['actual_operations'] and not q['candidate_kc_ids'] and q['evidence_eligible']:
            kc = add(_kc(re.sub(r'^\s*\(?[a-h]\)\s*', '', ITEM_HEAD.sub('', POINTS.sub('', q['own_wording']))).strip()[:200], q['actual_operations'][-1:] if q['actual_operations'][-1] in DEMANDING else q['actual_operations'][:1],
                         'inferred_from_exam_item_wording', q['anchor_element_ids'], src_by[q['source_id']],
                         'exam_derived' if q['assessment_kind'] == 'OFFICIAL_EXAM' else 'practice_derived', True, by))
            links.setdefault(kc['kc_id'], {})[q['item_id']] = {'basis': 'derived_from_item', 'inferred': True}
            best = max(chapters, key=lambda c: len(kc['_terms'] & terms(' '.join(by[a]['normalized_text'] for a in c['anchor_element_ids']))),
                       default=None)
            if best and kc['_terms'] & terms(' '.join(by[a]['normalized_text'] for a in best['anchor_element_ids'])):
                kc['chapter_id'] = best['chapter_id']; kc['chapter_assignment_basis'] = 'lexical_overlap_inferred'
            else:
                kc['chapter_id'] = 'ch-exam-scope-unanchored'; kc['chapter_assignment_basis'] = 'no_lecture_anchor'
    if any(k['chapter_id'] == 'ch-exam-scope-unanchored' for k in kcs.values()):
        chapters.append({'chapter_id': 'ch-exam-scope-unanchored', 'title': 'Prüfungsstoff ohne Vorlesungsanker (Quellenlücke)',
                         'source_ids': [], 'anchor_element_ids': [], 'kc_ids': [], 'origin': 'exam_gap', 'official': False})
    for d in decisions.of('chapter'):
        if d['subject_id'] in kcs and any(c['chapter_id'] == d['value'] for c in chapters):
            kcs[d['subject_id']]['chapter_id'] = d['value']; kcs[d['subject_id']]['chapter_assignment_basis'] = 'semantic_decision'

    # Prerequisites: stated (chapter-level) and inferred (term defined earlier, used later). Kept acyclic.
    order = {c['chapter_id']: i for i, c in enumerate(chapters)}
    edges = []

    def creates_cycle(a, b):  # adding b -> a (a is prerequisite of b)
        stack = [a]; seen = set()
        while stack:
            x = stack.pop()
            if x == b:
                return True
            if x in seen:
                continue
            seen.add(x); stack.extend(kcs[x]['prerequisite_kc_ids'])
        return False

    def edge(pre, post, basis, inferred, evidence):
        if pre == post or pre in kcs[post]['prerequisite_kc_ids']:
            return
        if creates_cycle(pre, post):
            edges.append({'from': pre, 'to': post, 'basis': basis, 'inferred': inferred, 'status': 'REJECTED_CYCLE', 'evidence': evidence}); return
        kcs[post]['prerequisite_kc_ids'].append(pre); kcs[post]['prerequisite_basis'][pre] = basis
        edges.append({'from': pre, 'to': post, 'basis': basis, 'inferred': inferred, 'status': 'ACTIVE', 'evidence': evidence})

    defs = [k for k in kcs.values() if k.get('defined_term')]
    for d in defs:
        dterms = terms(d['defined_term'])
        for k in kcs.values():
            if k is d or not dterms:
                continue
            body = k['_terms'] | terms(' '.join(by[a]['normalized_text'] for a in k['source_anchor_ids']))
            if dterms <= body and 'DEFINE' not in k['operations']:
                edge(d['kc_id'], k['kc_id'], 'term_defined_earlier_used_later', True, sorted(dterms))
    for chapter_id, pterms, eid in stated_prereqs:
        for d in kcs.values():
            if d['chapter_id'] != chapter_id and d['_terms'] & pterms:
                for k in kcs.values():
                    if k['chapter_id'] == chapter_id:
                        edge(d['kc_id'], k['kc_id'], 'stated_prerequisite', False, [eid])
    for d in decisions.of('prerequisite'):
        if d['subject_id'] in kcs and d['value'] in kcs:
            edge(d['value'], d['subject_id'], 'semantic_decision:' + d.get('decided_by', 'fixture'), True, d.get('evidence_element_ids', []))

    # Notation registry with conflict detection.
    registry = []
    for sym, uses in sorted(notation.items()):
        meanings = sorted({u['meaning'] for u in uses})
        conflict = len({semantic_key(m) for m in meanings}) > 1
        official = sorted({u['meaning'] for u in uses if src_by[u['source_id']]['authority'] == 'OFFICIAL_LECTURE'})
        if not conflict:
            resolution = {'status': 'CONSISTENT', 'preferred_meaning': meanings[0] if meanings else None}
        elif len({semantic_key(m) for m in official}) == 1:
            # Official course notation has precedence; the deviation is still reported, never averaged.
            resolution = {'status': 'OFFICIAL_PRECEDENCE_DEVIATION_REPORTED', 'preferred_meaning': official[0]}
        else:
            resolution = {'status': 'CONFLICTING_OFFICIAL_SOURCES' if len(official) > 1 else 'NO_OFFICIAL_DEFINITION',
                          'preferred_meaning': None}
        registry.append({'notation_id': 'nt-' + _h(sym)[:12], 'symbol': sym, 'meanings': meanings, 'uses': uses,
                         'status': 'CONFLICT_REVIEW_REQUIRED' if conflict else 'CONSISTENT',
                         'authority_resolution': resolution})
    for k in kcs.values():
        for n in registry:
            if any(u['chapter_id'] == k['chapter_id'] for u in n['uses']):
                k['notation_refs'].append(n['notation_id'])

    # Same defined term in several sources with incompatible wording: report, never average.
    definition_conflicts = []
    for k in kcs.values():
        if k.get('defined_term') and len(k['source_ids']) > 1:
            per_src = {}
            for a in k['source_anchor_ids']:
                if src_by[by[a]['source_id']]['authority'] in ('OFFICIAL_EXAM', 'OFFICIAL_EXERCISE', 'OFFICIAL_SOLUTION'):
                    continue  # a task asking for a definition is not a competing definition
                per_src.setdefault(by[a]['source_id'], set()).update(terms(by[a]['normalized_text']))
            vals = list(per_src.values())
            worst = min((len(x & y) / (len(x | y) or 1) for i, x in enumerate(vals) for y in vals[i + 1:]), default=1)
            if worst < 0.3:
                k['conflict_status'] = 'CONFLICT_REVIEW_REQUIRED'
                definition_conflicts.append({'kc_id': k['kc_id'], 'term': k['defined_term'], 'source_ids': sorted(per_src),
                                             'min_term_overlap': round(worst, 3), 'status': 'CONFLICT_REVIEW_REQUIRED'})

    # B6.6: a decided link to an evidence-eligible question adds what that question demands to an INFERRED topic
    # competency (e.g. a list slide whose official question asks to name the items: RECALL besides EXPLAIN). Adding
    # a requirement can only make coverage stricter; decided KC operations are never touched.
    item_by = {q['item_id']: q for q in items}
    for k in kcs.values():
        if str(k.get('operation_basis', '')).startswith('semantic_decision') or k.get('origin') not in ('slide_title_topic', 'heading_topic'):
            continue
        for qid, link in sorted(links.get(k['kc_id'], {}).items()):
            q = item_by.get(qid)
            if not q or not q['evidence_eligible'] or not str(link.get('basis', '')).startswith('semantic_decision'):
                continue
            for o in q['actual_operations']:
                if o not in k['operations']:
                    k['operations'].append(o)
                    k.setdefault('operation_evidence', []).append({'operation': o, 'basis': f'decided_link_to_item:{qid}'})
    for k in kcs.values():   # topic statements name every demanded operation (wording only; the id stays the topic's)
        if k.get('topic_text'):
            k['statement'] = ' · '.join(OP_LABEL.get(o, o.title()) for o in k['operations']) + ': ' + k['topic_text']
    # Source support (provenance) and coverage gate.
    coverage = []
    for k in kcs.values():
        anchor_text = ' '.join(by[a]['normalized_text'] for a in k['source_anchor_ids'])
        k['source_support'] = source_support(k['statement'], [by[a]['normalized_text'] for a in k['source_anchor_ids']])
        blocking = sorted({c for sid in k['source_ids'] for c in gap_by_source.get(sid, set())
                           if c in ('PARSE_FAILED', 'EMPTY_SOURCE', 'SOURCE_UNAVAILABLE')} |
                          ({'TEXT_LAYER_MISSING'} if any(scan_affects(manifest, sid, k['source_anchor_ids'], by) for sid in k['source_ids']) else set()))
        evidence, mismatches, recall_only = [], [], []
        for qid, link in sorted(links.get(k['kc_id'], {}).items()):
            q = item_by.get(qid)
            if q is None:
                mismatches.append({'item_id': qid, 'reason': 'linked item does not exist'}); continue
            if not q['evidence_eligible']:
                mismatches.append({'item_id': qid, 'link_basis': link['basis'],
                                   'reason': f"{q['assessment_kind']} is not assessment evidence (no exam weight)"}); continue
            ok_all = []
            for op in k['operations']:
                ok, why = satisfied(op, q['actual_operations'], q)
                ok_all.append((op, ok, why))
            if all(ok for _, ok, _ in ok_all):
                evidence.append(qid)
            else:
                mismatches.append({'item_id': qid, 'link_basis': link['basis'],
                                   'reason': '; '.join(why for _, ok, why in ok_all if not ok)})
                if 'RECALL' in q['actual_operations']:
                    recall_only.append(qid)   # tests recall of the content only; the higher operation stays unevidenced
        if blocking:
            status = 'BLOCKED_SOURCE_GAP'
        elif k['source_support'] != 'SOURCE_SUPPORT_LEXICAL':
            status = 'SOURCE_UNSUPPORTED'
        elif evidence:
            status = 'EVIDENCED_PENDING_SEMANTIC_REVIEW'
        elif mismatches:
            status = 'OPERATION_MISMATCH'
        else:
            status = 'NO_ASSESSMENT_EVIDENCE'
        coverage.append({'kc_id': k['kc_id'], 'required_operations': k['operations'], 'status': status,
                         'evidence_item_ids': evidence if status == 'EVIDENCED_PENDING_SEMANTIC_REVIEW' else [],
                         'operation_matched_item_ids': evidence, 'rejected_links': mismatches, 'blocking_source_gaps': blocking,
                         'recall_only_item_ids': recall_only,
                         'source_support': k['source_support'],
                         'note': 'Deterministic gate; semantic/academic confirmation is still required. Never COVERED by ID link alone.'})
        k['linked_item_ids'] = sorted(links.get(k['kc_id'], {}))

    # Chapter requirements, ordering and chapter-level generation plan.
    for c in chapters:
        c['kc_ids'] = sorted(k['kc_id'] for k in kcs.values() if k['chapter_id'] == c['chapter_id'])
    chapters = [c for c in chapters if c['kc_ids'] or c['origin'] == 'source_structure' and c['anchor_element_ids']]
    cid = {c['chapter_id'] for c in chapters}
    for c in chapters:
        deps = sorted({kcs[p]['chapter_id'] for k in c['kc_ids'] for p in kcs[k]['prerequisite_kc_ids']} - {c['chapter_id']})
        c['narrative_dependencies'] = [d for d in deps if d in cid]
    chapters, ordering = _order_chapters(chapters, manifest, by, decisions, edges, kcs)
    # P3.4: an item from an explicitly labelled section ('Session 3') whose number differs from the position of a
    # chapter with source-stated order is not evidence for that chapter (review instead). Never adds links.
    stated = {'SOURCE_STATED_TOC', 'SOURCE_STATED_HEADING_NUMBER', 'SOURCE_STATED_SCHEDULE_TABLE', 'SEMANTIC_DECISION'}
    pos = {cid: v['number'] for cid, v in ordering.get('session_identity', {}).items() if v['basis'] in stated}
    # B12: a competency derived only from the wording of an item of ANOTHER session was attached to this chapter by
    # word overlap alone. Its lecture is not in this chapter (e.g. a folder with one lecture plus the full question
    # catalogue): it becomes exam scope without a lecture anchor (a visible source gap) instead of chapter content.
    moved = []
    by_session = {}
    for cid_, n_ in pos.items():
        by_session.setdefault(n_, []).append(cid_)
    by_session = {n_: v[0] for n_, v in by_session.items() if len(v) == 1}
    for k in kcs.values():
        if k.get('chapter_assignment_basis') != 'lexical_overlap_inferred' or k['chapter_id'] not in pos:
            continue
        derived = [qid for qid, v in links.get(k['kc_id'], {}).items() if v.get('basis') == 'derived_from_item']
        secs = {item_by[q].get('section_number') for q in derived if q in item_by} - {None}
        if derived and secs and pos[k['chapter_id']] not in secs:
            target = by_session.get(next(iter(secs))) if len(secs) == 1 else None
            moved.append((k['kc_id'], k['chapter_id'], sorted(secs), target or 'ch-exam-scope-unanchored'))
            if target:      # the chapter of that session exists: the item's competency belongs there
                k['chapter_id'] = target; k['chapter_assignment_basis'] = 'item_session_matches_chapter_session'
            else:
                k['chapter_id'] = 'ch-exam-scope-unanchored'; k['chapter_assignment_basis'] = 'other_session_no_lecture_anchor'
    if moved:
        if any(m_[3] == 'ch-exam-scope-unanchored' for m_ in moved) and not any(c['chapter_id'] == 'ch-exam-scope-unanchored' for c in chapters):
            chapters.append({'chapter_id': 'ch-exam-scope-unanchored', 'title': 'Prüfungsstoff ohne Vorlesungsanker (Quellenlücke)',
                             'source_ids': [], 'anchor_element_ids': [], 'kc_ids': [], 'origin': 'exam_gap', 'official': False,
                             'narrative_dependencies': [], 'order_basis': {'basis': 'EXAM_GAP', 'inferred': False}})
        for c in chapters:
            c['kc_ids'] = sorted(k['kc_id'] for k in kcs.values() if k['chapter_id'] == c['chapter_id'])
        ordering['moved_other_session_kcs'] = [{'kc_id': a, 'from_chapter': b, 'item_sections': s_, 'to_chapter': t_} for a, b, s_, t_ in moved]
    for r in coverage:
        cidk = kcs[r['kc_id']]['chapter_id']
        if cidk not in pos:
            continue
        for qid in list(r['evidence_item_ids']):
            q = item_by[qid]
            if q.get('section_number') and q['section_number'] != pos[cidk]:
                r['evidence_item_ids'].remove(qid)
                if qid in r['operation_matched_item_ids']:
                    r['operation_matched_item_ids'].remove(qid)
                r['rejected_links'].append({'item_id': qid, 'link_basis': 'lexical', 'reason':
                                            f"SECTION_MISMATCH: item from '{q['section_label']}', chapter at stated position {pos[cidk]}"})
        if r['status'] == 'EVIDENCED_PENDING_SEMANTIC_REVIEW' and not r['evidence_item_ids']:
            r['status'] = 'OPERATION_MISMATCH'
    cov_by = {r['kc_id']: r for r in coverage}
    profile = _domain_profile(manifest, roles)
    for i, c in enumerate(chapters, 1):
        c['position'] = i
        ck = [kcs[k] for k in c['kc_ids']]
        ops = {o for k in ck for o in k['operations']}
        anchors = sorted(set(c['anchor_element_ids']) | {a for k in ck for a in k['source_anchor_ids']})
        visuals = [by[a] for a in anchors if by[a]['kind'] in ('image', 'figure', 'diagram', 'chart', 'formula', 'table', 'rendered_page')]
        linked = sorted({q for k in ck for q in k['linked_item_ids']})
        c['requirements'] = {
            'explanation_depth': ('formal: motivation, precise definitions, every derivation/proof step justified, assumptions explicit'
                                  if ops & {'DERIVE', 'PROVE'} else
                                  'case method: norm structure, element-wise subsumption, counter-arguments' if 'SUBSUME' in ops else
                                  'implementation: algorithm idea, complexity, tested reference code, failure modes' if 'IMPLEMENT' in ops else
                                  'conceptual: intuition, definition, examples and non-examples, misconceptions'),
            'proof_and_derivation_depth': [{'kc_id': k['kc_id'], 'operation': o, 'requirement': 'complete stepwise argument; no skipped steps'}
                                           for k in ck for o in k['operations'] if o in ('DERIVE', 'PROVE')],
            'worked_examples': [{'kc_id': k['kc_id'], 'operation': o, 'min_count': 2 if o in DEMANDING else 1,
                                 'requirement': 'fully worked, source-consistent notation, new parameters vs. source example'}
                                for k in ck for o in k['operations'] if o not in ('RECALL',)],
            'visualizations': [{'source_element_id': v['element_id'], 'kind': v['kind'], 'asset': (v.get('asset') or {}).get('path'),
                                'source_status': v['status'], 'requirement': 'reuse or faithfully redraw with source check; place at relevant paragraph'}
                               for v in visuals] or
                              ([{'source_element_id': None, 'kind': 'suggested', 'requirement': 'inferred: derivation/process needs a diagram'}]
                               if ops & {'DERIVE', 'PROVE', 'IMPLEMENT', 'SUBSUME'} else []),
            'exercise_progression': [{'kc_id': k['kc_id'], 'stages': _stages(k)} for k in ck],
            'model_solutions': {'required_for': 'every exercise and exam-like item', 'form': 'complete stepwise solution + rubric + typical errors',
                                'exam_items_with_solution_source': [q for q in linked if item_by[q]['solution_source_id']],
                                'exam_items_without_solution_source': [q for q in linked if not item_by[q]['solution_source_id']]},
            'review_requirements': sorted({'SOURCE_SEMANTIC', 'EDITORIAL'} |
                                          ({'SYMBOLIC_WITH_DOMAIN'} if ops & {'DERIVE', 'PROVE', 'CALCULATE'} else set()) |
                                          ({'LEGAL_NORM'} if 'SUBSUME' in ops else set()) |
                                          ({'EXECUTABLE_TESTS'} if 'IMPLEMENT' in ops else set()) |
                                          ({'VISUAL_RENDER'} if visuals else set())),
        }
        c['exam_relevance'] = {'linked_item_ids': linked,
                               'section_mismatch_item_ids': sorted(q for q in linked if item_by[q].get('section_number') and c['chapter_id'] in pos
                                                                   and item_by[q]['section_number'] != pos[c['chapter_id']]),
                               'section_number': pos.get(c['chapter_id']),
                               'session_basis': (ordering.get('session_identity', {}).get(c['chapter_id']) or {}).get('basis') if c['chapter_id'] in pos else None,
                               'section_unlinked_item_ids': sorted(q['item_id'] for q in items if c['chapter_id'] in pos
                                                                   and q.get('section_number') == pos[c['chapter_id']]
                                                                   and q['item_id'] not in linked
                                                                   and q.get('assessment_kind') in ('PRACTICE', 'OFFICIAL_EXAM')),
                               'points': sum(item_by[q]['points'] or 0 for q in linked if item_by[q]['assessment_kind'] == 'OFFICIAL_EXAM'),
                               'points_basis': 'only points stated in OFFICIAL_EXAM items; nothing estimated',
                               'items_by_kind': {kd: sorted(q for q in linked if item_by[q]['assessment_kind'] == kd)
                                                 for kd in sorted({item_by[q]['assessment_kind'] for q in linked})},
                               'demanded_operations': sorted({o for q in linked for o in item_by[q]['actual_operations']}),
                               'kc_coverage': {k['kc_id']: cov_by[k['kc_id']]['status'] for k in ck}}
        assessment_anchors = sorted({a for q in linked for a in item_by[q]['anchor_element_ids']} - set(anchors))
        anchors = sorted(set(anchors) | set(assessment_anchors))
        c['source_package'] = {'role': 'data_supply_only_not_a_planning_unit', 'element_ids': anchors,
                               'assessment_element_ids': assessment_anchors,
                               'source_ids': sorted({by[a]['source_id'] for a in anchors}),
                               'uncertain_element_ids': [a for a in anchors if by[a]['status'] != 'ok']}
        c['notation_ids'] = sorted({n for k in ck for n in k['notation_refs']})
        c['open_gaps'] = sorted({g for sid in c['source_package']['source_ids'] for g in gap_by_source.get(sid, set()) if g in BLOCKING_GAPS})
        c['generation_plan'] = {'unit': 'chapter', 'per_transport_unit_role_chain': False, 'steps':
                                ['chapter_author', 'assessment_and_independent_solutions'] +
                                [f'review:{r}' for r in c['requirements']['review_requirements']],
                                'semantic_decisions_pending': ['confirm KC operations', 'confirm item<->KC links',
                                                               'confirm visual interpretation'] if c['source_package']['uncertain_element_ids'] else
                                ['confirm KC operations', 'confirm item<->KC links'],
                                'provider_calls_in_p2': 0, 'status': 'PLANNED_PENDING_SEMANTIC_REVIEW'}
    for k in kcs.values():
        k.pop('_terms', None)
        k['cross_references'] = sorted({kk['kc_id'] for kk in kcs.values() if kk is not k and kk['chapter_id'] != k['chapter_id']
                                        and set(kk['source_anchor_ids']) & set(k['source_anchor_ids'])})
    plan = {'schema': CURRICULUM_SCHEMA, 'planner_version': PLANNER_VERSION,
            'course_id': 'course-' + _h(manifest.get('root_name', '') + '|' + '|'.join(sorted(s['relative_path'] for s in sources if s['authority'].startswith('OFFICIAL'))[:3]))[:14],
            'domain_profile': profile, 'competencies': sorted(kcs.values(), key=lambda k: (order.get(k['chapter_id'], 999), k['kc_id'])),
            'assessment_items': items, 'chapters': chapters, 'prerequisite_edges': edges, 'notation_registry': registry,
            'source_roles': roles, 'source_classification': source_classification(manifest, roles), 'rejected_kc_candidates': rejected_candidates,
            'non_chapter_sources': [{'source_id': r['source_id'], 'role': r['role'], 'reason': 'role does not form subject chapters'}
                                    for r in roles.values() if r['role'] not in CHAPTER_ROLES],
            'chapter_merges': merge_log, 'chapter_ordering': ordering, 'definition_conflicts': definition_conflicts,
            'coverage': sorted(coverage, key=lambda r: r['kc_id']),
            'summary': {'competencies': len(kcs), 'chapters': len(chapters), 'assessment_items': len(items),
                        'coverage_status_counts': {s: sum(r['status'] == s for r in coverage) for s in sorted({r['status'] for r in coverage})},
                        'chapter_merge_review_required': sum(m['decision'] == 'SEMANTIC_REVIEW_REQUIRED' for m in merge_log),
                        'chapter_order_status': ordering['status'],
                        'unanchored_exam_scope': any(c['chapter_id'] == 'ch-exam-scope-unanchored' for c in chapters),
                        'source_inventory_complete': manifest['coverage_complete']},
            'provider_calls': 0,
            'scope_note': 'Deterministic draft plan. Competency operations and links are lexically inferred where marked; '
                          'academic release requires semantic review. Transport units play no role in chapter count.'}
    validate_curriculum(plan, manifest)
    if out is not None:
        write_json(Path(out) / 'curriculum.json', plan)
    return plan


def _stages(k):
    stages = [{'level': 1, 'operation': 'RECALL', 'purpose': 'retrieve definitions/notation needed'}]
    for o in k['operations']:
        if o not in ('RECALL',):
            stages.append({'level': 2, 'operation': o, 'purpose': 'guided practice with worked-example fading'})
    if set(k['operations']) & DEMANDING:
        stages.append({'level': 3, 'operation': k['operations'][0], 'purpose': 'transfer: new instance, exam format and points'})
    return stages


def _topo(chapters):
    ids = [c['chapter_id'] for c in chapters]; by = dict(zip(ids, chapters)); done = []; seen = set()

    def visit(cid, stack=()):
        if cid in seen or cid in stack:
            return
        for d in by[cid]['narrative_dependencies']:
            visit(d, stack + (cid,))
        seen.add(cid); done.append(by[cid])
    for cid in ids:
        visit(cid)
    return done


# ---------------------------------------------------------------- P3: chapter fusion and ordering evidence

TITLE_NOISE = re.compile(r'\b(vorlesung(en)?|folien(satz)?|skript|kapitel|chapter|lecture|slides?|teil|part|einheit|unit|woche|week|'
                         r'(ü|ue)bung(sblatt)?|exercises?|tutorium|tutorial|notes?|handout|vl|kap|lektion|session|zusammenfassung)\b', re.I)
AUTH_RANK = {'OFFICIAL_LECTURE': 0, 'STUDENT_NOTES': 2, 'SUPPLEMENTARY': 3}
MERGE_RULES = {
    'M0_same_source': 'Sections of one source are never auto-merged (the author separated them); candidate only.',
    'M1_same_topic_title': 'Normalised titles (numbering and genre words such as Vorlesung/Folien/Skript removed) are identical -> MERGE.',
    'M2_title_and_content': 'Title term Jaccard >= 0.5 and content term Jaccard >= 0.2 -> MERGE (not between two complete '
                            'official lecture decks: a sub-topic title such as "Policy Gradients" vs "Trust Regions for '
                            'Policy Gradients" marks a later session, so that pair is a review candidate).',
    'M3_ambiguous': 'Any title overlap, or content Jaccard >= 0.3 without title match -> SEMANTIC_REVIEW_REQUIRED, kept separate.',
    'D_decision': 'em-semantic-decisions-v1 chapter_merge / chapter_keep_separate override M1-M3 (recorded with rationale).',
    'survivor': 'Merged chapter keeps the id of the most authoritative member (OFFICIAL_LECTURE first), then the smallest id; '
                'ids derive from topic titles, never from paths, so they are stable under renames.'}


def _title_terms(title):
    return terms(re.sub(r'\d+', ' ', TITLE_NOISE.sub(' ', title.lower())))


def _overlap(a, b):
    return max(_jac(a, b), len(a & b) / (min(len(a), len(b)) or 1)) if a and b else 0.0


def _jac(a, b):
    return len(a & b) / (len(a | b) or 1)


def _whole_deck(c):
    """An official chapter made of complete, unsplit source units (one lecture deck each)."""
    segs = c.get('segmentation') or []
    return bool(c.get('official') and segs and all(g.get('status') != 'SPLIT_AT_NUMBERED_DIVIDERS' for g in segs))


def _merge_chapters(chapters, kcs, by, src_by, decisions):
    content = {c['chapter_id']: terms(' '.join(by[a]['normalized_text'] for a in c['anchor_element_ids'])) for c in chapters}
    title = {c['chapter_id']: _title_terms(c['title']) for c in chapters}
    forced = {frozenset((d['subject_id'], d['value'])): d for d in decisions.of('chapter_merge')}
    keep = {frozenset((d['subject_id'], d['value'])): d for d in decisions.of('chapter_keep_separate')}
    rank = lambda c: (min(AUTH_RANK.get(src_by[s]['authority'], 5) for s in c['source_ids']) if c['source_ids'] else 9, c['chapter_id'])
    log, alias = [], {}

    def find(x):
        while x in alias:
            x = alias[x]
        return x
    for i, a in enumerate(chapters):
        for b in chapters[i + 1:]:
            ra, rb = find(a['chapter_id']), find(b['chapter_id'])
            if ra == rb:
                continue
            pair = frozenset((a['chapter_id'], b['chapter_id']))
            tj, cj = _jac(title[a['chapter_id']], title[b['chapter_id']]), _jac(content[a['chapter_id']], content[b['chapter_id']])
            rec = {'chapters': sorted(pair), 'title_jaccard': round(tj, 3), 'content_jaccard': round(cj, 3)}
            if pair in keep:
                log.append({**rec, 'decision': 'KEPT_SEPARATE', 'rule': 'D_decision', 'rationale': keep[pair]['rationale']}); continue
            if pair in forced:
                decision, rule = 'MERGED', 'D_decision'
            elif set(a['source_ids']) & set(b['source_ids']):
                decision, rule = ('SEMANTIC_REVIEW_REQUIRED', 'M0_same_source') if tj >= 0.5 else (None, None)
            elif title[a['chapter_id']] and title[a['chapter_id']] == title[b['chapter_id']]:
                decision, rule = 'MERGED', 'M1_same_topic_title'
            elif tj >= 0.5 and cj >= 0.2 and not (_whole_deck(a) and _whole_deck(b)):
                decision, rule = 'MERGED', 'M2_title_and_content'
            elif tj > 0 or cj >= 0.3:
                decision, rule = 'SEMANTIC_REVIEW_REQUIRED', 'M3_ambiguous'
            else:
                decision = None
            if decision == 'MERGED':
                ca = next(c for c in chapters if c['chapter_id'] == ra); cb = next(c for c in chapters if c['chapter_id'] == rb)
                keep_c, drop_c = sorted((ca, cb), key=rank)
                alias[drop_c['chapter_id']] = keep_c['chapter_id']
                log.append({**rec, 'decision': 'MERGED', 'rule': rule, 'into': keep_c['chapter_id'], 'merged': drop_c['chapter_id'],
                            'rationale': forced[pair]['rationale'] if pair in forced else MERGE_RULES[rule]})
            elif decision:
                log.append({**rec, 'decision': decision, 'rule': rule, 'rationale': MERGE_RULES[rule]})
    # Review candidates and decisions refer to the surviving chapter of every merge; duplicates collapse.
    resolved_keep = {frozenset(find(x) for x in pair) for pair in keep}
    seen, final = set(), []
    for rec in log:
        if rec['decision'] == 'SEMANTIC_REVIEW_REQUIRED':
            pair = frozenset(find(x) for x in rec['chapters'])
            if len(pair) < 2 or pair in seen or pair in resolved_keep:
                continue
            seen.add(pair); rec = {**rec, 'chapters': sorted(pair)}
        final.append(rec)
    log = final
    out = []
    for c in chapters:
        target = find(c['chapter_id'])
        if target == c['chapter_id']:
            out.append(c); continue
        t = next(x for x in chapters if x['chapter_id'] == target)
        t['source_ids'] = sorted(set(t['source_ids']) | set(c['source_ids']))
        t['anchor_element_ids'] += [x for x in c['anchor_element_ids'] if x not in t['anchor_element_ids']]
        t['supporting_source_ids'] = sorted(set(t.get('supporting_source_ids', [])) | set(c.get('supporting_source_ids', [])))
        t.setdefault('merged_from', []).append({'chapter_id': c['chapter_id'], 'title': c['title']})
        t.setdefault('segmentation', []).extend(g for g in c.get('segmentation', []) if g not in t.get('segmentation', []))
        # 'Diffusion Part 1' + 'Diffusion Part 2' -> 'Diffusion': a merged chapter is not named after one of its parts.
        part = re.compile(r'\s*[-–:,(]?\s*\b(part|teil|pt\.?)\s*\d+\)?\s*$', re.I)
        if part.search(t['title']) and part.search(c['title']) and part.sub('', t['title']).lower() == part.sub('', c['title']).lower():
            t['title'] = part.sub('', t['title']).strip()
        t['official'] = t['official'] or c['official']
    for k in kcs.values():
        if k.get('chapter_id'):
            k['chapter_id'] = find(k['chapter_id'])
    for c in out:
        c['kc_extraction_status'] = c.get('kc_extraction_status')
    return out, log


TOC_HEAD = re.compile(r'inhalts?(verzeichnis)?\b|gliederung|syllabus|table of contents|\bcontents\b|course outline|semesterplan|'
                      r'themen(übersicht|plan)|schedule|ablaufplan', re.I)
NUMBERED_TITLE = re.compile(r'^\s*(?:(?:kapitel|chapter|lecture|vorlesung|teil|part|lektion|session|week|woche|einheit|unit)\s*)?'
                            r'(\d{1,3})(?:\s*[.:)\-]|\s+[A-ZÄÖÜa-zäöü])', re.I)


def _order_chapters(chapters, manifest, by, decisions, edges, kcs):
    """Order from evidence, in precedence: (1) official table of contents / syllabus element, (2) numbering stated in
    the chapter heading text (never in the file name), (3) prerequisite edges; only then the inventory order of
    source files, which is a documented emergency fallback and marked UNRESOLVED."""
    ids = [c['chapter_id'] for c in chapters]
    toc_rank, toc_eids = {}, []
    for s in manifest['sources']:
        if s['authority'] in ('OFFICIAL_EXAM', 'OFFICIAL_SOLUTION', 'OFFICIAL_EXERCISE'):
            continue
        els = [by[i] for i in s['element_ids']]
        for i, e in enumerate(els):
            if e['kind'] in ('heading', 'paragraph') and TOC_HEAD.search(e['text'][:60]):
                lines = [ln for ln in e['text'].splitlines()[1:] if ln.strip()]
                for x in els[i + 1:i + 60]:
                    if x['kind'] == 'heading' and _level(x) <= _level(e):
                        break
                    if x['kind'] in ('list_item', 'paragraph'):
                        lines += [ln for ln in x['text'].splitlines() if ln.strip()]
                for pos, ln in enumerate(lines):
                    lt = _title_terms(ln)
                    best = max(chapters, key=lambda c: _jac(lt, _title_terms(c['title'])), default=None)
                    if best and lt and _jac(lt, _title_terms(best['title'])) >= 0.5 and best['chapter_id'] not in toc_rank:
                        toc_rank[best['chapter_id']] = pos
                toc_eids.append(e['element_id'])
    # P3.3: a schedule/syllabus TABLE with a topic column in a non-assessment source is ordering evidence too.
    # Rows are matched to chapter titles by term overlap (>=0.5) and must match exactly one chapter uniquely.
    sched_rank, sched_matches, sched_session, session_conflicts = {}, [], {}, []
    sched_hits = {}        # chapter -> number of schedule rows that match it uniquely (identity needs exactly one)
    if len(toc_rank) < 2:
        for s in manifest['sources']:
            if s['authority'] in ('OFFICIAL_EXAM', 'OFFICIAL_SOLUTION', 'OFFICIAL_EXERCISE'):
                continue
            for i in s['element_ids']:
                t = by[i]
                rows = (t.get('structure') or {}).get('rows') if t['kind'] == 'table' else None
                if not rows or not any(re.search(r'topic|thema|themen|inhalt|content|lecture|vorlesung|session|einheit', str(x or ''), re.I)
                                       for x in rows[0]):
                    continue
                col = next(k for k, x in enumerate(rows[0]) if re.search(r'topic|thema|themen|inhalt|content|lecture|vorlesung|session|einheit', str(x or ''), re.I))
                topic_ord = 0
                for pos, r in enumerate(rows[1:]):
                    raw = r[col] if col < len(r) else None
                    cell = '' if raw is None else str(raw)        # B6.3: an empty cell is no topic (was the string 'None')
                    lt = _title_terms(cell)
                    if not lt:
                        continue
                    topic_ord += 1        # B6.3: session identity = ordinal among the rows that name a topic (evidence)
                    scored = sorted(((_overlap(lt, _title_terms(c['title'])), c['chapter_id']) for c in chapters), reverse=True)
                    if scored and scored[0][0] >= 0.5 and len(scored) > 1 and scored[1][0] == scored[0][0]:
                        tied = [cid for sc, cid in scored if sc == scored[0][0]]
                        session_conflicts.append({'status': 'AMBIGUOUS_SCHEDULE_ROW', 'row': pos + 1, 'topic': cell.strip(), 'session': topic_ord,
                                                  'element_id': i, 'candidates': [{'chapter_id': cid, 'title': next(c['title'] for c in chapters if c['chapter_id'] == cid)}
                                                                                  for cid in tied],
                                                  'resolution': 'no chapter gets this session; review required'})
                        continue
                    if scored and scored[0][0] >= 0.5 and (len(scored) == 1 or scored[1][0] < scored[0][0]):
                        sched_hits[scored[0][1]] = sched_hits.get(scored[0][1], 0) + 1
                    if scored and scored[0][0] >= 0.5 and (len(scored) == 1 or scored[1][0] < scored[0][0]) and scored[0][1] not in sched_rank:
                        sched_rank[scored[0][1]] = pos; sched_session[scored[0][1]] = topic_ord
                        sched_matches.append({'chapter_id': scored[0][1], 'row': pos + 1, 'session': topic_ord, 'score': round(scored[0][0], 2), 'element_id': i})
                if len(sched_rank) >= 2:
                    toc_eids.append(i)
    num_rank = {}
    for c in chapters:
        head = next((by[a] for a in c['anchor_element_ids'] if by[a]['kind'] == 'heading'), None)
        m = NUMBERED_TITLE.match(head['text']) if head else None
        if m and not re.match(r'^\s*\d+\s*[.,]\d', head['text']):
            num_rank[c['chapter_id']] = int(m.group(1))
    order_decision = next((d for d in decisions.of('chapter_order')), None)
    if order_decision:
        rank, kind = {cid: i for i, cid in enumerate(order_decision['value'])}, 'SEMANTIC_DECISION'
    elif len(toc_rank) >= 2:
        rank, kind = toc_rank, 'SOURCE_STATED_TOC'
    elif len(sched_rank) >= 2:
        rank, kind = sched_rank, 'SOURCE_STATED_SCHEDULE_TABLE'
    elif len(num_rank) >= 2:
        rank, kind = num_rank, 'SOURCE_STATED_HEADING_NUMBER'
    else:
        rank, kind = {}, None
    deps = {c['chapter_id']: set(c['narrative_dependencies']) for c in chapters}
    stated_edge = {(kcs[e['from']]['chapter_id'], kcs[e['to']]['chapter_id']) for e in edges
                   if e['status'] == 'ACTIVE' and not e['inferred']}
    conflicts = []
    for c, ds in deps.items():
        for d in list(ds):
            if c in rank and d in rank and rank[d] > rank[c]:
                ds.discard(d)
                conflicts.append({'chapter': c, 'prerequisite_chapter': d, 'stated_order_basis': kind,
                                  'prerequisite_basis': 'stated' if (d, c) in stated_edge else 'inferred',
                                  'status': 'ORDER_CONFLICT_REVIEW_REQUIRED', 'resolution': 'stated order kept; conflict reported'})
    inv = {cid: i for i, cid in enumerate(ids)}
    key = lambda cid: (rank.get(cid, float('inf')), inv[cid])
    placed, result = set(), []
    while len(result) < len(ids):
        ready = [cid for cid in ids if cid not in placed and deps[cid] <= placed]
        if not ready:  # residual cycle: fall back deterministically and report
            ready = [min((cid for cid in ids if cid not in placed), key=key)]
            conflicts.append({'chapter': ready[0], 'status': 'DEPENDENCY_CYCLE_REVIEW_REQUIRED'})
        nxt = min(ready, key=key); placed.add(nxt); result.append(nxt)
    by_id = {c['chapter_id']: c for c in chapters}
    out = [by_id[c] for c in result]
    basis = {}
    for c in out:
        cid = c['chapter_id']
        if cid in rank:
            b = {'basis': kind, 'inferred': (kind == 'SEMANTIC_DECISION' and order_decision.get('decided_by') == 'model') or
                 kind == 'SOURCE_STATED_SCHEDULE_TABLE'}
            if kind == 'SOURCE_STATED_SCHEDULE_TABLE':
                b['match'] = next(m for m in sched_matches if m['chapter_id'] == cid)
        elif deps[cid] or any(cid in deps[o] for o in deps):
            stated = any((d, cid) in stated_edge for d in deps[cid]) or any((cid, o) in stated_edge for o in ids)
            b = {'basis': 'STATED_PREREQUISITE' if stated else 'INFERRED_PREREQUISITE', 'inferred': not stated}
        else:
            b = {'basis': 'UNRESOLVED_FILENAME_FALLBACK', 'inferred': True,
                 'note': 'no table of contents, heading number or prerequisite; inventory (path) order is NOT evidence'}
        c['order_basis'] = b; basis[cid] = b['basis']
    unresolved = sum(v == 'UNRESOLVED_FILENAME_FALLBACK' for v in basis.values())
    status = ('UNRESOLVED_REVIEW_REQUIRED' if unresolved >= 2 or (unresolved and len(out) > 1 and not rank and
                                                                   not any(deps.values())) else
              'CONFLICT_REVIEW_REQUIRED' if conflicts else
              'SCHEDULE_MATCHED_PENDING_REVIEW' if kind == 'SOURCE_STATED_SCHEDULE_TABLE' else
              'SOURCE_STATED' if kind and kind != 'SEMANTIC_DECISION' and len(rank) == len(out) else
              'PARTIALLY_INFERRED' if len(out) > 1 else 'SINGLE_CHAPTER')
    # B6.3: session identity from the ordering evidence itself, never from the position in the sorted chapter list,
    # so documents added elsewhere in the root cannot shift it.
    if kind == 'SOURCE_STATED_SCHEDULE_TABLE':
        ident = {cid: {'number': n, 'basis': kind, 'evidence': next(m for m in sched_matches if m['chapter_id'] == cid)} for cid, n in sched_session.items()}
    elif kind == 'SOURCE_STATED_TOC':
        ident = {cid: {'number': r + 1, 'basis': kind, 'evidence': {'toc_element_ids': toc_eids, 'line': r + 1}} for cid, r in rank.items()}
    elif kind == 'SOURCE_STATED_HEADING_NUMBER':
        ident = {cid: {'number': r, 'basis': kind, 'evidence': {'heading_number': r}} for cid, r in rank.items()}
    elif kind == 'SEMANTIC_DECISION':
        ident = {cid: {'number': r + 1, 'basis': kind, 'evidence': {'decided_by': order_decision.get('decided_by')}} for cid, r in rank.items()}
    else:
        # B12: ordering needs two matched chapters, a session identity does not. With fewer (e.g. a course folder that
        # holds one lecture plus the schedule), a chapter keeps the session of the one schedule row that names it
        # uniquely; a chapter matched by several rows gets none (review stays open).
        ident = {cid: {'number': n, 'basis': 'SOURCE_STATED_SCHEDULE_TABLE', 'evidence': next(m for m in sched_matches if m['chapter_id'] == cid)}
                 for cid, n in sched_session.items() if sched_hits.get(cid) == 1}
    return out, {'status': status, 'primary_basis': kind, 'schedule_matches': sched_matches, 'per_chapter': basis, 'conflicts': conflicts,
                 'session_identity': ident, 'session_conflicts': session_conflicts,
                 'toc_element_ids': toc_eids,
                 'precedence': ['semantic decision (em-semantic-decisions-v1)', 'official TOC/syllabus element',
                                'numbering in heading text', 'prerequisite edges', 'UNRESOLVED filename fallback']}
