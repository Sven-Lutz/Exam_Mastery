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
                     r'diagram|graphic|picture|lesen Sie\b[^?.]*\bab\b|im (?:Plot|Diagramm)|(?:this|that|the following|the above) (?:image|figure|plot|chart|ECG|EKG|graph|photo|micrograph|scan)|(?:gezeigte[nmrs]?|abgebildete[nmrs]?|obige[nmrs]?)\s+Graph\w*|(?:oben|unten|links|rechts)\s+(?:dargestellt|gezeigt|abgebildet)|'
                     r'(?:dargestellt|gezeigt|abgebildet)e[nmrs]?\b|shown (?:above|below|here))', re.I)
_COMPUTE = re.compile(r'\b(berechne|berechnen Sie|bestimme|bestimmen Sie|welchen Wert|was ergibt|ermittle|ermitteln Sie|'
                      r'compute|calculate)\b', re.I)          # 'evaluate' is an essay verb in many subjects
# a quantity question may be a recall fact ('Wie viel investiert X üblicherweise?') or need hidden data: WARN, not FAIL
_QUANTITY = re.compile(r'\b(wie viel(?:e)?|wie gro(?:ß|ss)|how (?:much|large|many))\b', re.I)
_GREEK = re.compile(r'[\u0370-\u03ff]')
_DEICTIC = re.compile(r'\b(?:des|im|beim|aus dem|in dem|vom)\s+[\wÄÖÜäöüß]+-(?:Beispiels?|Gitters?|Falls?|Szenarios?|Modells?)\b|'
                      r'\b(im|in der|in dem|aus dem|aus der|beim|für das|für die|des)\s+(obigen|vorigen|genannten|gezeigten|'
                      r'Beispiel|Gitter|Graphen?|Fall|Szenario|Aufgabe\s*\d*|Tabelle|Modell)\b|\b(this|the above|the previous)\s+'
                      r'(example|grid|graph|table|case|exercise)\b|\b(Zelle|Feld|cell)\s*\(\s*\d+\s*,\s*\d+\s*\)', re.I)
_COUNTED_ENUM = re.compile(r'\b(welche|aus welchen|nenne(?:n Sie)? die|which|name the|list the|what are the)\s+(zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn|two|three|four|five|six|seven|eight|nine|ten|\d+)\b', re.I)
_CONVENTION = re.compile(r'\b(Vorlesung|Skript|Lehrbuch|Kurs|Konvention|Definition (?:von|nach)|laut|gemäß|according to|as defined|lecture|course|textbook)\b'
                         r'|[A-ZÄÖÜ][\wäöüß-]+(?: et al\.| (?:und|and|&) [A-ZÄÖÜ][\wäöüß-]+)? \(\d{4}[a-z]?\)'   # author (year)
                         r'|§§?\s*\d+|\bArt\.\s*\d+', re.I)                                          # statute anchors
_TWO_TARGETS = re.compile(r'\?[^?]*\b(Schreiben|Nennen|Geben|Begründen|Erklären|Zeigen|Berechnen|Skizzieren) Sie\b|'
                          r'\s[–-]\s*und\s+(welche|warum|wie|was|wann|wo)\b|\?\s*(?:Write|Name|Give|Explain|Show|Compute) ', re.I)
_IMPERATIVE = re.compile(r'^\s*(?:[\w-]+\s+)?(?:finden|bestimmen|berechnen|nennen|zeigen|beweisen|erklären|korrigieren|ordnen|ergänzen|skizzieren)\b[^.]*:|'
                         r'\b(?:Bestimmen|Berechnen|Nennen|Zeigen|Beweisen|Erklären|Korrigieren|Ordnen|Ergänzen|Skizzieren|Begründen|Geben) Sie\b|'
                         r'^\s*(?:find|determine|compute|name|show|prove|explain|correct|identify|fix)\b', re.I)
_THIS = re.compile(r'\b(this|that|these|those)\s+(?!is\b|are\b|means?\b|way\b|case\b)[a-z]{3,}', re.I)
_MATH = re.compile(r'\\\((.*?)\\\)|\\\[(.*?)\\\]', re.S)
_NUM = re.compile(r'(?<![A-Za-z_\\])\d+(?:[.,]\d+)?')
_STOP = set('der die das ein eine einer eines und oder ist sind wird werden von zu mit für auf im in den dem des nicht nur '
            'the a an and or is are of to in on for with by as be not only was'.split())


def _text(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or '')).strip()


_GREEK_NAMES = {'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'varepsilon', 'zeta', 'eta', 'theta', 'vartheta', 'iota', 'kappa', 'lambda',
                'mu', 'nu', 'xi', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'varphi', 'chi', 'psi', 'omega',
                'Gamma', 'Delta', 'Theta', 'Lambda', 'Xi', 'Pi', 'Sigma', 'Phi', 'Psi', 'Omega'}


def _symbols(tex):
    """Single-letter identifiers and Greek letters in a TeX fragment. Every other command (\\mapsto, \\partial, \\top,
    \\operatorname{..}, \\mathrm{..}, \\text{..}) is notation, not a symbol to be defined; sub/superscripts are indices."""
    tex = re.sub(r'\\(?:text|mathrm|operatorname|mathbf|mathit|textrm)\{[^}]*\}', ' ', tex)
    greek = {g for g in re.findall(r'\\([a-zA-Z]+)', tex) if g in _GREEK_NAMES}
    t = re.sub(r'\\[a-zA-Z]+', ' ', tex)
    t = re.sub(r'_\{[^}]*\}|_\w|\^\{[^}]*\}|\^\w', ' ', t)
    return {*(re.findall(r'(?<![^\W\d_])[A-Za-z](?![^\W\d_])', t)), *greek}


def _content_words(s):
    return {w for w in re.findall(r'[a-zäöüß0-9]{4,}', _text(s).lower()) if w not in _STOP}


def _norm(x):
    return re.sub(r'\s+', ' ', _text(x)).strip().lower()


def example_line(c, examples):
    """Definition lines of named course examples ({name: definition}) that a card mentions but does not define."""
    seen = ' '.join(_text(c.get(k)) for k in ('front', 'text', 'answer'))
    ctx = _norm(c.get('context'))
    hit = [d for n, d in examples.items() if re.search(r'(?<![\w])' + re.escape(n) + r'(?![\w])', seen, re.I) and _norm(d) not in ctx]
    return ' '.join(dict.fromkeys(hit))                        # one line per definition, even if several names hit


def notation_line(c, notation):
    """'Notation: V = Wertfunktion; γ = Diskont' for the symbols the question side uses but does not define, so a card
    stays answerable out of chapter context. notation: {symbol (TeX name or letter): meaning}."""
    front = (c.get('text') if c.get('kind') == 'cloze' else c.get('front')) or ''
    used = set().union(*[_symbols(a or b) for a, b in _MATH.findall(front)]) if _MATH.search(front) else set()
    have = set().union(*[_symbols(a or b) for a, b in _MATH.findall(c.get('context') or '')]) if _MATH.search(c.get('context') or '') else set()
    need = [k for k in sorted(used - have - set(c.get('defines') or [])) if k in notation]
    show = lambda k: '\\(\\' + k + '\\)' if len(k) > 1 else '\\(' + k + '\\)'
    return ('Notation: ' + '; '.join(f'{show(k)} = {notation[k]}' for k in need)) if need else ''


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


def audit_card(v, notation=frozenset(), examples=None):
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
        if q == 0 and not _IMPERATIVE.search(_MATH.sub('X', _text(front))):
            flag('QUESTION_VALIDITY', 'FAIL', 'no question or task on the front')
        elif q > 1:
            flag('QUESTION_VALIDITY', 'FAIL', f'{q} questions on one card')
        elif _TWO_TARGETS.search(_MATH.sub(' ', _text(front))):
            flag('QUESTION_VALIDITY', 'FAIL', 'two retrieval targets on one card (question plus a second task)')
    at = _text(v['answer'])                                           # leak = a verbal answer that adds no token the front lacks
    tok = lambda x: set(re.findall(r'[^\W_]+(?:-[^\W_]+)*', x.lower()))
    ans = _content_words(_MATH.sub(' ', at))
    if v['kind'] != 'cloze' and len(ans) >= 1 and len(ans) <= 12 and not _MATH.search(at) and not re.search(r'\d', at) \
            and not (tok(at) - tok(seen_plain) - _STOP):
        flag('QUESTION_VALIDITY', 'FAIL', 'answer is already given on the front')
    if not _text(v['answer']) and v['kind'] != 'cloze':
        flag('QUESTION_VALIDITY', 'FAIL', 'no answer')
    # ANSWERABILITY
    if _COMPUTE.search(seen_plain) and not _NUM.search(_MATH.sub(lambda m: ' ' + (m.group(1) or m.group(2) or '') + ' ', seen)) \
            and not _MATH.search(seen) and not _GREEK.search(seen):     # symbolic questions ('in terms of gamma') are answerable
        flag('ANSWERABILITY', 'FAIL', 'computation requested but no quantities given on the question side')
    if _QUANTITY.search(seen_plain) and not _COMPUTE.search(seen_plain) and not _NUM.search(seen) and not _MATH.search(seen) \
            and not _GREEK.search(seen):
        flag('ANSWERABILITY', 'WARN', 'quantity asked without given data: a recall fact, or hidden data the card lacks - check')
    m = _DEICTIC.search(seen_plain)
    if m and not _text(ctx) and not v['front_has_image']:
        flag('ANSWERABILITY', 'FAIL', f'refers to context the card does not contain ("{m.group(0)}")')
    if _THIS.search(seen_plain) and not _text(ctx) and not v['front_has_image']:
        flag('ANSWERABILITY', 'WARN', f'refers to "{_THIS.search(seen_plain).group(0)}" without context: check that it is defined on the card')
    for name, definition in (examples or {}).items():          # named course examples must be defined on the card
        if re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', seen_plain + ' ' + _text(v['answer']), re.I) and _norm(definition) not in _norm(ctx):
            flag('ANSWERABILITY', 'FAIL', f'names the course example "{name}" without its definition on the question side')
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


def audit_deck(views, notation=frozenset(), dup_threshold=0.8, examples=None):
    """Audit all cards. Blocking = any FAIL in VISUAL_DEPENDENCY, ANSWERABILITY, QUESTION_VALIDITY, ANSWER_CORRECTNESS."""
    cards = {v['key']: audit_card(v, notation, examples) for v in views}
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
    col = d / 'collection.anki21'
    if (d / 'collection.anki21b').exists():                     # newer packages: zstd-compressed collection
        import shutil, subprocess
        col = d / 'collection.unzstd'
        try:
            import zstandard
            col.write_bytes(zstandard.ZstdDecompressor().decompress((d / 'collection.anki21b').read_bytes(), max_output_size=1 << 30))
        except ImportError:
            if not shutil.which('zstd'):
                raise RuntimeError('collection.anki21b needs the zstandard module or the zstd CLI')
            subprocess.run(['zstd', '-d', '-q', '-f', str(d / 'collection.anki21b'), '-o', str(col)], check=True)
    elif not col.exists():
        col = d / 'collection.anki2'
    db = sqlite3.connect(col)
    db.create_collation('unicase', lambda x, y: (x.lower() > y.lower()) - (x.lower() < y.lower()))   # Anki's collation (schema 18+)
    try:
        media = json.loads((d / 'media').read_text(encoding='utf-8') or '{}') if (d / 'media').exists() else {}
        have = set(media.values())
    except (UnicodeDecodeError, ValueError):                    # zstd/protobuf media map: existence not checkable here
        have = None
    raw = db.execute('select models from col').fetchone()[0]
    if raw:                                                     # legacy schema: note types as JSON in col
        models = json.loads(raw)
    else:                                                       # schema 18+: notetypes / fields tables
        models, rows = {}, db.execute('select ntid, ord, name from fields').fetchall()   # no WHERE: the index uses Anki's own collation
        for ntid, o, n in sorted(rows):
            models.setdefault(str(ntid), {'flds': []})['flds'].append({'name': n})
    out = []
    first = lambda f, *names: next((f[n] for n in names if f.get(n)), '')
    for mid, guid, flds in db.execute('select mid, guid, flds from notes'):
        names = [x['name'] for x in models[str(mid)]['flds']]
        f = dict(zip(names, flds.split('\x1f')))
        # field aliases of common note types (engine, Anki basic/cloze, other generators); the template itself is not parsed
        front = first(f, 'Front', 'Prompt', 'Text', 'Question', 'Frage', 'Vorderseite')
        context = first(f, 'Context', 'Kontext')
        media = first(f, 'DiagramMedia', 'Image')                 # ASSUMPTION: a filled media field is shown on the question side
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', front + context + media)
        cloze = 'Text' in f and not f.get('Front') and '{{c' in (f.get('Text') or '')
        out.append({'key': first(f, 'Key', 'StableID') or guid, 'kind': 'cloze' if cloze else (f.get('Kind') or ''), 'kind_label': f.get('Kind', ''),
                    'front': front, 'context': context, 'answer': first(f, 'Answer', 'CanonicalAnswer', 'Back', 'Extra', 'Back Extra', 'Antwort', 'Rückseite'),
                    'explanation': first(f, 'Explanation', 'Why'), 'front_has_image': bool(imgs or media), 'image_ok': True if have is None else all(i in have for i in imgs),
                    'source': f.get('Source', ''), 'check': None, 'defines': []})
    return out
