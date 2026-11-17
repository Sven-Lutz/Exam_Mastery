"""B35 Answerability gate for retrieval cards (Anki), domain-neutral.

Why: V4 cards passed every format rule (one question mark, <= 30 words, balanced delimiters) and were still partly
unanswerable: they named a figure that was not on the question side, relied on a lecture convention ("six
components") or on hidden context ("cell (3,2)", "the grid"), used undefined symbols, or asked for a computation
without the numbers. Format conformity is not answerability.

What this module checks (deterministic, on what the learner actually SEES on the question side):
  VISUAL_DEPENDENCY  question points at a visual (figure, diagram, slide, graph, "shown above") that is not on the
                     front, or the referenced image file is missing/unreadable
  ANSWERABILITY      computation requested without given quantities; symbols in the question that are neither
                     defined on the card nor in the deck notation list; deictic reference to context the card does
                     not contain; enumeration with a fixed count of a convention-dependent definition without naming
                     the convention/source
  QUESTION_VALIDITY  no question / several questions; answer leaked on the front
  REDUNDANCY         near-duplicate questions in the deck
  COGNITIVE_VALUE    deck-level share of pure recall cards (reported, WARN only)
  RENDERING          delegated to anki_v2.render_lint (reported separately by the deck builder)
  ANSWER_CORRECTNESS NOT_VERIFIED unless the card carries an executable check ('check': {expr, value}) that passes
  SOURCE_FIDELITY    NOT_VERIFIED unless a source anchor is present; a present anchor is still only 'ANCHORED',
                     never 'VERIFIED' (that needs a reader of the source passage)

What it does NOT do: judge whether an answer is didactically good or factually correct in general. Those dimensions
stay NOT_VERIFIED and must be reviewed by a human; the gate never upgrades them.
"""
from __future__ import annotations
import re
from fractions import Fraction

DIMENSIONS = ('QUESTION_VALIDITY', 'ANSWER_CORRECTNESS', 'ANSWERABILITY', 'COGNITIVE_VALUE', 'VISUAL_DEPENDENCY',
              'REDUNDANCY', 'RENDERING', 'SOURCE_FIDELITY')

# language-neutral-ish cue lists (German + English); extend per language, never per subject
_VISUAL = re.compile(r'\b(Abbildung|Abb\.|Bild|Grafik|Diagramm|Skizze|Schaubild|Darstellung|Folie\s*\d+|Slide\s*\d+|figure|fig\.|'
                     r'diagram|graphic|picture|plot|chart|(?:gezeigte[nmrs]?|abgebildete[nmrs]?|obige[nmrs]?)\s+Graph\w*|(?:oben|unten|links|rechts)\s+(?:dargestellt|gezeigt|abgebildet)|'
                     r'(?:dargestellt|gezeigt|abgebildet)e[nmrs]?\b|shown (?:above|below|here))', re.I)
_COMPUTE = re.compile(r'\b(berechne|berechnen Sie|bestimme|bestimmen Sie|wie gro(?:ß|ss)|welchen Wert|was ergibt|wie viel(?:e)?|'
                      r'ermittle|ermitteln Sie|compute|calculate|evaluate|how (?:much|large|many))\b', re.I)
_GREEK = re.compile(r'[\u0370-\u03ff]')
_DEICTIC = re.compile(r'\b(im|in der|in dem|aus dem|aus der|beim|für das|für die|des)\s+(obigen|vorigen|genannten|gezeigten|'
                      r'Beispiel|Gitter|Graphen?|Fall|Szenario|Aufgabe\s*\d*|Tabelle|Modell)\b|\b(this|the above|the previous)\s+'
                      r'(example|grid|graph|table|case|exercise)\b|\b(Zelle|Feld|cell)\s*\(\s*\d+\s*,\s*\d+\s*\)', re.I)
_COUNTED_ENUM = re.compile(r'\b(welche|aus welchen|nenne(?:n Sie)? die|which|name the)\s+(zwei|drei|vier|fünf|sechs|sieben|acht|\d+)\b', re.I)
_CONVENTION = re.compile(r'(laut|nach|gemäß|in der|in dieser|im)\s+(Vorlesung|Skript|Lehrbuch|Kurs|Definition|Konvention|Sutton|'
                         r'[A-ZÄÖÜ][a-zäöü]+\s*(?:&|und)\s*[A-ZÄÖÜ])|according to|as defined (?:in|by)|in (?:this|the) (?:course|lecture)', re.I)
_MATH = re.compile(r'\\\((.*?)\\\)|\\\[(.*?)\\\]', re.S)
_NUM = re.compile(r'(?<![A-Za-z_\\])\d+(?:[.,]\d+)?')
_STOP = set('der die das ein eine einer eines und oder ist sind wird werden von zu mit für auf im in den dem des nicht nur '
            'the a an and or is are of to in on for with by as be not only was'.split())


def _text(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or '')).strip()


def _symbols(tex):
    """Single-letter / Greek identifiers used in a TeX fragment (without commands like \\frac, \\max)."""
    t = re.sub(r'\\(?:frac|max|min|sum|prod|mathbb|mathcal|operatorname|text|mathrm|left|right|big|Big|cdot|le|ge|leq|geq|'
               r'mid|in|to|infty|ldots|dots|sup|inf|lim|log|exp|arg|quad|qquad|lVert|rVert|Vert|tag|hat|bar|tilde|sqrt|'
               r'mathbf|boldsymbol|approx|neq|ne|sim|forall|exists|subseteq|subset|cup|cap|times|circ|star|ast|prime)\b', ' ', tex)
    greek = set(re.findall(r'\\([a-zA-Z]+)', t))
    t = re.sub(r'\\[a-zA-Z]+', ' ', t)
    t = re.sub(r'_\{[^}]*\}|_\w|\^\{[^}]*\}|\^\w', ' ', t)               # sub/superscripts are indices, not new symbols
    return {*(re.findall(r'(?<![A-Za-z])[A-Za-z](?![A-Za-z])', t)), *greek}


def _content_words(s):
    return {w for w in re.findall(r'[a-zäöüß0-9]{4,}', _text(s).lower()) if w not in _STOP}


def card_view(c, *, front_has_image=None, image_ok=True):
    """Normalise an authored card (anki_v2 schema) to what the learner sees on each side."""
    front = c.get('text') if c.get('kind') == 'cloze' else c.get('front')
    fig_front = bool(c.get('figure')) and c.get('figure_side') == 'front'
    return {'key': c.get('key', '?'), 'kind': c.get('kind', ''), 'front': front or '', 'context': c.get('context') or '',
            'answer': c.get('answer') or '', 'explanation': c.get('explanation') or '',
            'front_has_image': fig_front if front_has_image is None else front_has_image, 'image_ok': image_ok,
            'source': c.get('source') or c.get('source_ref') or '', 'check': c.get('check'),
            'defines': c.get('defines') or []}


def _eval_check(chk):
    """Executable answer check: {'expr': '1/(1-0.9)', 'value': '10'} evaluated exactly. True/False/None."""
    if not isinstance(chk, dict) or 'expr' not in chk or 'value' not in chk:
        return None
    import ast, operator as op
    ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg}
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return Fraction(str(n.value))
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            a, b = ev(n.left), ev(n.right)
            return Fraction(a) ** int(b) if isinstance(n.op, ast.Pow) else ops[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.operand))
        raise ValueError('unsupported expression')
    try:
        got, want = ev(ast.parse(str(chk['expr']), mode='eval').body), Fraction(str(chk['value']))
    except (ValueError, SyntaxError, ZeroDivisionError):
        return False
    tol = Fraction(str(chk.get('tol', 0)))
    return abs(got - want) <= tol


def audit_card(v, notation=frozenset()):
    """Per-dimension verdicts for one card view. Returns {dim: {'status', 'reasons'}}."""
    r = {d: {'status': 'PASS', 'reasons': []} for d in DIMENSIONS}
    def flag(d, status, why):
        order = {'PASS': 0, 'NOT_VERIFIED': 1, 'WARN': 2, 'FAIL': 3}
        if order[status] > order[r[d]['status']]:
            r[d]['status'] = status
        r[d]['reasons'].append(why)
    front, ctx = v['front'], v['context']
    seen = _text(front) + ' ' + _text(ctx)
    seen_plain = _MATH.sub(' ', seen)
    # VISUAL_DEPENDENCY
    if _VISUAL.search(seen_plain) and not v['front_has_image']:
        flag('VISUAL_DEPENDENCY', 'FAIL', f'question refers to a visual ("{_VISUAL.search(seen_plain).group(0)}") that is not on the question side')
    if v['front_has_image'] and not v['image_ok']:
        flag('VISUAL_DEPENDENCY', 'FAIL', 'front image missing or unreadable')
    # QUESTION_VALIDITY
    if v['kind'] != 'cloze':
        q = _MATH.sub('X', _text(front)).count('?')
        if q == 0:
            flag('QUESTION_VALIDITY', 'FAIL', 'no question on the front')
        elif q > 1:
            flag('QUESTION_VALIDITY', 'FAIL', f'{q} questions on one card')
    ans = _content_words(_MATH.sub(' ', _text(v['answer'])))          # leak = the answer adds nothing the front lacks
    if v['kind'] != 'cloze' and ans and len(ans) <= 12 and not (ans - _content_words(seen_plain)):
        flag('QUESTION_VALIDITY', 'FAIL', 'answer is already given on the front')
    if not _text(v['answer']) and v['kind'] != 'cloze':
        flag('QUESTION_VALIDITY', 'FAIL', 'no answer')
    # ANSWERABILITY
    if _COMPUTE.search(seen_plain) and not _NUM.search(_MATH.sub(lambda m: ' ' + (m.group(1) or m.group(2) or '') + ' ', seen)) \
            and not _MATH.search(seen) and not _GREEK.search(seen):     # symbolic questions ('in terms of gamma') are answerable
        flag('ANSWERABILITY', 'FAIL', 'computation requested but no quantities given on the question side')
    m = _DEICTIC.search(seen_plain)
    if m and not _text(ctx) and not v['front_has_image']:
        flag('ANSWERABILITY', 'FAIL', f'refers to context the card does not contain ("{m.group(0)}")')
    m = _COUNTED_ENUM.search(seen_plain)
    if m and not _CONVENTION.search(seen_plain):
        flag('ANSWERABILITY', 'WARN', f'fixed-count enumeration ("{m.group(0)}") of a convention-dependent definition without naming the convention/source')
    used = set().union(*[_symbols(a or b) for a, b in _MATH.findall(front)]) if _MATH.search(front) else set()
    defined = set().union(*[_symbols(a or b) for a, b in _MATH.findall(ctx)]) if _MATH.search(ctx) else set()
    undefined = sorted(used - defined - set(notation) - set(v['defines']))
    if undefined:
        flag('ANSWERABILITY', 'WARN', 'symbols not defined on the card or in the deck notation: ' + ', '.join(undefined))
    # ANSWER_CORRECTNESS / SOURCE_FIDELITY: never upgraded beyond what was executed
    ok = _eval_check(v.get('check'))
    if ok is None:
        flag('ANSWER_CORRECTNESS', 'NOT_VERIFIED', 'no executable check; needs human review')
    elif not ok:
        flag('ANSWER_CORRECTNESS', 'FAIL', 'executable answer check fails')
    flag('SOURCE_FIDELITY', 'NOT_VERIFIED', 'source anchor present, passage not machine-compared' if v['source'] else 'no source anchor')
    r['RENDERING'] = {'status': 'NOT_VERIFIED', 'reasons': ['see anki_v2.render_lint / verify_package']}
    r['COGNITIVE_VALUE'] = {'status': 'NOT_VERIFIED', 'reasons': ['deck-level only']}
    return r


def audit_deck(views, notation=frozenset(), dup_threshold=0.8):
    """Audit all cards. Blocking = any FAIL in VISUAL_DEPENDENCY, ANSWERABILITY, QUESTION_VALIDITY, ANSWER_CORRECTNESS."""
    cards = {v['key']: audit_card(v, notation) for v in views}
    words = {v['key']: _content_words(v['front'] + ' ' + v['context']) for v in views}
    keys = list(words)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            u = words[a] | words[b]
            if u and len(words[a] & words[b]) / len(u) >= dup_threshold:
                for k, o in ((a, b), (b, a)):
                    cards[k]['REDUNDANCY'] = {'status': 'WARN', 'reasons': cards[k]['REDUNDANCY']['reasons'] + [f'near-duplicate of {o}']}
    recall = sum(1 for v in views if re.search(r'(Wissen abrufen|recall|definition)', v.get('kind_label', '') or v['kind'], re.I))
    blocking = {'VISUAL_DEPENDENCY', 'ANSWERABILITY', 'QUESTION_VALIDITY', 'ANSWER_CORRECTNESS'}
    fails = {k: [f'{d}: {x}' for d in blocking if c[d]['status'] == 'FAIL' for x in c[d]['reasons']] for k, c in cards.items()}
    fails = {k: v for k, v in fails.items() if v}
    tally = {d: {s: sum(1 for c in cards.values() if c[d]['status'] == s) for s in ('PASS', 'WARN', 'FAIL', 'NOT_VERIFIED')} for d in DIMENSIONS}
    return {'scope': 'deterministic checks on the visible question side; correctness and didactic value need human review',
            'n_cards': len(views), 'status': 'FAIL' if fails else 'PASS_WITH_HUMAN_REVIEW_PENDING',
            'blocking': fails, 'tally': tally, 'recall_share': round(recall / len(views), 2) if views else None,
            'cards': cards}


def views_from_apkg(path):
    """Card views from a built .apkg (what the learner really sees); used to audit published decks such as V4."""
    import json, sqlite3, tempfile, zipfile
    from pathlib import Path
    d = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(path) as z:
        z.extractall(d)
    db = sqlite3.connect(d / ('collection.anki21' if (d / 'collection.anki21').exists() else 'collection.anki2'))
    media = json.loads((d / 'media').read_text() or '{}') if (d / 'media').exists() else {}
    have = set(media.values())
    models = json.loads(db.execute('select models from col').fetchone()[0])
    out = []
    for mid, flds in db.execute('select mid, flds from notes'):
        names = [f['name'] for f in models[str(mid)]['flds']]
        f = dict(zip(names, flds.split('\x1f')))
        front = f.get('Front', f.get('Text', ''))
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', front + f.get('Context', ''))
        out.append({'key': f.get('Key', '?'), 'kind': 'cloze' if 'Text' in f else (f.get('Kind') or ''), 'kind_label': f.get('Kind', ''),
                    'front': front, 'context': f.get('Context', ''), 'answer': f.get('Answer', f.get('Extra', '')),
                    'explanation': f.get('Explanation', ''), 'front_has_image': bool(imgs), 'image_ok': all(i in have for i in imgs),
                    'source': f.get('Source', ''), 'check': None, 'defines': []})
    return out
