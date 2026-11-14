"""Semantic consistency checks (rule set DR-1.1) on a book model.

They target defect classes that passed DR-1.0 and were found by an independent review of the Funding v2 package:

S1 COUNT_CLAIM      a sentence states "k of the n …" while the table it refers to shows a different count.
S2 STAT_INFERENCE   an inferential statement (significant, robust, "kaum belastbar", reliable ranking …) without the
                    information it needs (sample size, test, interval) and without an explicit hedge.
S3 CAUSE_CLAIM      a cause is asserted for a source inconsistency or an observed pattern without evidence or hedge.
S4 TERM_CONFLICT    a table column names a concept that a cell or another block says the value is not
                    ("kein Agio"), or a block equates two terms that another block distinguishes.
S5 LEGAL_SUBSUMPTION a solution cites a norm and treats its elements as met, but the item states no facts or
                    assumptions for them; or a statutory prohibition is stated as absolute although the cited
                    provision contains an exception the text never mentions.
S6 BOOK_CARD        a number on a card that the book never states (cards must not carry facts the book lacks).
C6 RETRIEVAL_GRAIN  a card asks for a list of 4 or more elements without a stated reason (`list_reason`).
C7 EXPLANATION      mechanism, comparison and misconception cards need an explanation, example or pitfall.
C8 VISUAL_LABEL     a card labelled as visual recall must show its figure on the front.
C9 ANSWER_CUE       the front already contains the answer.

A check returns PASS, FAIL (blocking), or REVIEW. REVIEW means a reliable automatic decision is impossible:
it is listed for a targeted review and never counted as PASS.
"""
import re

VERSION = 'DR-1.1'

NUMWORD = {'zwei': 2, 'drei': 3, 'vier': 4, 'fünf': 5, 'sechs': 6, 'sieben': 7, 'acht': 8, 'neun': 9, 'zehn': 10,
           'elf': 11, 'zwölf': 12, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8,
           'nine': 9, 'ten': 10}
_NW = '|'.join(NUMWORD)
COUNT = re.compile(r'\b(\d+|' + _NW + r')\s+(?:der|von|of the|of)\s+(\d+|' + _NW + r')\b', re.I)
HEDGE = re.compile(r'(lässt sich (?:aus [^.]* )?nicht (?:beurteilen|ableiten|sagen)|nicht belegt|nicht ableiten|vermutlich|'
                   r'plausibel|möglicherweise|nennt (?:die Folie|die Quelle) (?:keine|nicht)|unklar|offen|Hypothese|cannot be judged|not established)', re.I)
INFER = re.compile(r'(signifikant|statistisch (?:gesichert|belastbar|unterscheidbar)|(?:kaum|nicht|wenig) belastbar|'
                   r'zufällig (?:entstanden|bedingt)|verlässliche Rangfolge|statistically|significantly (?:higher|lower|different|better|worse|more|less|larger|smaller)|significant (?:difference|effect|increase|decrease))', re.I)
INFER_BASIS = re.compile(r'(\bn\s*=\s*\d|Stichprobe(?:numfang)?\s+(?:von|n)|Konfidenz|p\s*[<=]\s*0|t-Test|Standardfehler|confidence interval)', re.I)
CAUSE = re.compile(r'\b(ist (?:meist |oft |in der Regel )?die \*?Folge\*?|Die Ursache (?:ist|liegt)|Ursache ist|liegt (?:daran|an der)|is caused by|the cause is)\b', re.I)
# B14: "Folge" also means "sequence". "X ist die Folge der Ein- und Auszahlungen" defines a series of events of one kind
# (no causal claim). A causal reading remains for everything else, e.g. "die Folge der späten Zahlungen" (an attribute
# names a cause) or "die Folge von Zahlungsverzug".
SERIES_NOUN = r'(?:Ein-\s+und\s+Auszahlungen|(?:Ein|Aus)?[Zz]ahlungen|Schritte|Werte|Zahlen|Ereignisse|Perioden|Buchungen|Bestellungen|Termine|Zustände|Glieder|Elemente)'
SEQUENCE = re.compile(r'\bdie \*?Folge\*? (?:der|von) ' + SERIES_NOUN + r'(?=[\s.,;:)]|$)')
CONCLUDE = re.compile(r'(→|liegt vor|ist erfüllt|ist gegeben|sind erfüllt)', re.I)
NORM = re.compile(r'§+\s*\d+[a-z]?')
ASSUME = re.compile(r'(Annahme|angenommen|Sachverhalt|laut Fall|nach den Fallangaben|Fallannahmen|unter den Annahmen)', re.I)
ABSOLUTE = re.compile(r'\b(darf|dürfen)\s+(?:[^.]{0,60}?)\b(keine|nicht mehr)\b', re.I)
EXCEPT = re.compile(r'(grundsätzlich|außer|ausgenommen|Ausnahme|es sei denn|gilt nicht)', re.I)
NUM = re.compile(r'(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d+(?:\.\d+)?')


def _n(w):
    return int(w) if w.isdigit() else NUMWORD.get(w.lower())


def _blocks(book):
    for s in book.get('sections', []):
        for sub in s.get('subsections') or [{'blocks': s.get('blocks', [])}]:
            for b in sub['blocks']:
                yield s['title'], b


def _text(b):
    parts = [b.get(k) for k in ('md', 'given', 'result', 'wrong', 'right', 'why', 'caption')]
    parts += [' '.join(map(str, s)) for s in b.get('steps') or []]
    return ' '.join(str(p) for p in parts if p)


def _rows(t):
    return [[str(x) for x in (r['cells'] if isinstance(r, dict) else r)] for r in t.get('rows', [])
            if not (isinstance(r, dict) and r.get('total'))]


def _sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', text)) if s]


def count_claims(book):
    """S1: a "k der n" sentence is checked against the nearest preceding table with n data rows. The counted
    property is the capitalised word of the sentence that occurs in the table cells (e.g. a city)."""
    out, last_table = [], None
    for sec, b in _blocks(book):
        if b.get('type') == 'table':
            last_table = b
            continue
        for s in _sentences(_text(b)):
            for m in COUNT.finditer(s):
                k, n = _n(m.group(1)), _n(m.group(2))
                if not k or not n or k > n:
                    continue
                t = last_table if last_table and len(_rows(last_table)) == n else None
                if not t:
                    out.append(('S1', 'REVIEW', sec, f'count claim "{m.group(0)}" without a table of {n} rows to check against: "{s[:90]}"'))
                    continue
                words = [w for w in re.findall(r'\b[A-ZÄÖÜ][\wäöüß-]{2,}', s) if w.lower() not in NUMWORD]
                hits = [w for w in words if any(w in c for r in _rows(t) for c in r[1:]) and not any(w in r[0] for r in _rows(t))]
                if not hits:
                    out.append(('S1', 'REVIEW', sec, f'count claim "{m.group(0)}": counted property not found in the table: "{s[:90]}"'))
                    continue
                prop = hits[0]
                real = sum(1 for r in _rows(t) if any(prop in c for c in r[1:]))
                out.append(('S1', 'PASS' if real == k else 'FAIL', sec,
                            f'"{m.group(0)}" with property {prop}: table shows {real} of {n}' + ('' if real == k else f' – text says {k}')))
    return out


def stat_inference(book):
    out = []
    for sec, b in _blocks(book):
        t = _text(b)
        for s in _sentences(t):
            if INFER.search(s):
                ok = INFER_BASIS.search(t) or HEDGE.search(s)
                out.append(('S2', 'PASS' if ok else 'FAIL', sec,
                            ('hedged or supported' if ok else 'inferential claim without sample size, test or interval') + f': "{s[:100]}"'))
    return out


def cause_claims(book):
    out, prev_inconsistent = [], False
    for sec, b in _blocks(book):
        t = _text(b)
        for s in _sentences(t):
            if CAUSE.search(s) and not HEDGE.search(s) and not (SEQUENCE.search(s) and not re.search(r'Ursache|liegt (?:daran|an)|caused|cause', s, re.I)):
                src = b.get('src') or ''
                st = 'FAIL' if prev_inconsistent else ('PASS' if src and b.get('prov') in ('course', 'supplement') else 'REVIEW')
                out.append(('S3', st, sec, f'cause asserted{" for a source inconsistency" if prev_inconsistent else ""}: "{s[:100]}"'))
        prev_inconsistent = bool(b.get('known_inconsistency')) if b.get('type') == 'table' else (prev_inconsistent and b.get('type') != 'text')
    return out


def term_conflicts(book):
    out = []
    blocks = list(_blocks(book))
    for sec, b in blocks:
        if b.get('type') != 'table':
            continue
        cols = [str(c) for c in b.get('columns', [])]
        for r in _rows(b):
            for c in r:
                q = re.search(r'„([^“]+)“\s+ist hier (?:ein|eine|der|die|das)\b', c)
                if q and any(h.startswith(q.group(1)) for h in cols):
                    out.append(('S4', 'FAIL', sec, f'column "{q.group(1)}" is used for something else in row {r[0]}: "{c[:60]}"'))
                for m in re.finditer(r'\bkein(?:e|en)?\s+([A-ZÄÖÜ][\wäöüß-]+)', c):
                    term = m.group(1)
                    bad = [h for h in cols if re.fullmatch(rf'{term}\b.*', h)]
                    if bad:
                        out.append(('S4', 'FAIL', sec, f'column "{bad[0]}" holds a value the table itself calls "kein {term}" ({r[0]})'))
    # a block that denies "X ist kein T" while another block counts X into T ("… plus T", "T zusammen")
    denials = {}
    for sec, b in blocks:
        for m in re.finditer(r'\b(?:ist|sind)\s+\*{0,2}kein(?:e)?\*{0,2}\s+([A-ZÄÖÜ][\wäöüß-]+)', _text(b)):
            denials.setdefault(m.group(1), sec)
        for m in re.finditer(r'\bDer ([A-ZÄÖÜ][\wäöüß]+)-Betrag[^.]{0,80}?\b(?:ist|sind)\s+\*{0,2}kein', _text(b)):
            denials.setdefault(m.group(1), sec)
    for term, where in denials.items():
        for sec, b in blocks:
            if re.search(rf'\(Eigenkapital plus {term}\)|plus {term}\)|{term} insgesamt', _text(b)):
                out.append(('S4', 'FAIL', sec, f'"{term}" is aggregated here although section "{where}" says a component is not {term}'))
    if not any(o[0] == 'S4' for o in out):
        out.append(('S4', 'PASS', 'chapter', 'no table column or block contradicts a term distinction'))
    return out


def _items(book):
    for st in book.get('stages', []):
        for it in st['items']:
            yield it
    for it in (book.get('exam') or {}).get('items', []):
        yield it


def legal_subsumption(book):
    out = []
    for it in _items(book):
        s = it.get('solution') or {}
        steps = ' '.join(' '.join(map(str, x)) for x in s.get('steps') or [])
        whole = steps + ' ' + str(s.get('answer', ''))
        if not NORM.search(whole):
            continue
        if CONCLUDE.search(whole):
            facts = ASSUME.search(it['prompt']) or ASSUME.search(whole)
            out.append(('S5', 'PASS' if facts else 'FAIL', it['id'],
                        'elements subsumed under stated facts or assumptions' if facts else 'norm applied as met without stated facts/assumptions for its elements'))
        for m in ABSOLUTE.finditer(whole):
            seg = whole[max(0, m.start() - 80): m.end() + 200]
            if not EXCEPT.search(seg):
                out.append(('S5', 'REVIEW', it['id'], f'statutory prohibition stated without exception or "grundsätzlich": "{seg[:100]}"'))
    return out


def _numbers(text):
    t = re.sub(r'\{,\}', ',', str(text or ''))
    return {x.replace(',', '') for x in NUM.findall(t) if len(x.replace(',', '').replace('.', '')) >= 2}


def book_card(book):
    corpus = set()
    for _, b in _blocks(book):
        corpus |= _numbers(_text(b))
        for r in _rows(b) if b.get('type') == 'table' else []:
            for c in r:
                corpus |= _numbers(c)
        for r in (b.get('rows') or []):
            if isinstance(r, dict):
                for c in r['cells']:
                    corpus |= _numbers(c)
    for it in _items(book):
        corpus |= _numbers(it['prompt']) | _numbers(str(it.get('solution')))
    out = []
    for c in book.get('cards', []):
        txt = ' '.join(str(c.get(k, '')) for k in ('answer', 'text', 'explanation', 'example'))
        missing = sorted(n for n in _numbers(txt) - corpus if not re.fullmatch(r'(19|20)\d\d', n))
        if missing:
            out.append(('S6', 'REVIEW', c['key'], f'numbers not stated in the book: {missing[:6]}'))
    if not out:
        out.append(('S6', 'PASS', 'cards', 'every number on a card also appears in the book'))
    return out


LIST_FRONT = re.compile(r'\b(?:Welche|Nennen Sie (?:die )?)\s*(\d+|' + _NW + r')\b', re.I)


def card_quality(c):
    """C6–C9 for one card: [(rule, status, detail)]."""
    out = []
    if c.get('kind') == 'cloze':
        return out
    front, ans = str(c.get('front', '')), str(c.get('answer', ''))
    m = LIST_FRONT.search(front)
    n = _n(m.group(1)) if m else 0
    parts = len([p for p in re.split(r';|·|,(?![^()]*\))| und ', re.sub(r'\\\(.*?\\\)', 'X', ans)) if p.strip()])
    if (n >= 4 or (parts >= 5 and c.get('kind') != 'compare')) and not c.get('list_reason'):
        out.append(('C6', 'FAIL', f'asks for {max(n, parts)} elements without list_reason'))
    if c.get('kind') in ('mechanism', 'compare', 'misconception') and not (c.get('explanation') or c.get('example') or c.get('pitfall')):
        out.append(('C7', 'FAIL', f'{c["kind"]} card without explanation, example or pitfall'))
    if c.get('kind') == 'visual' and c.get('figure_side') != 'front':
        out.append(('C8', 'FAIL', 'labelled visual recall but the figure is not on the front'))
    core = [w for w in re.findall(r'[\wäöüß-]{4,}', ans.lower())]
    if core and len(core) <= 3 and ' oder ' not in front and all(w in front.lower() for w in core):
        out.append(('C9', 'FAIL', 'the front contains the answer'))
    return out


def check_cards(cards):
    out = []
    for c in cards:
        for rule, st, d in card_quality(c):
            out.append((rule, st, c.get('key'), d))
    if not out:
        out.append(('C6-C9', 'PASS', 'cards', f'{len(cards)} cards pass retrieval grain, explanation, visual label and cue checks'))
    return out


def check_book(book):
    res = count_claims(book) + stat_inference(book) + cause_claims(book) + term_conflicts(book) + \
          legal_subsumption(book) + book_card(book) + check_cards(book.get('cards', []))
    return [{'rule': r, 'status': s, 'object': o, 'detail': d} for r, s, o, d in res]
