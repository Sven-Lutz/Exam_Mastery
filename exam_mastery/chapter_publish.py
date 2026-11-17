"""Publishing for the standard chapter path: ContentAST -> textbook, workbook, solutions, mock exam, competency
matrix (HTML + PDF + CSV) and Anki (TSV + isolated, tested .apkg). Deterministic, offline, no model calls.

Everything rendered keeps its provenance visible: course source vs. author inference vs. verified supplement,
the claim-support status, the source anchors (file + page) and every open issue. Nothing is upgraded: a technical
export is never a source verification or an academic release.
"""
from __future__ import annotations
import csv, html, json, re
from pathlib import Path
from .common import write_json, ContractError
from .math_text import MathRenderer, MATH as MATH_RE

ESC = lambda x: html.escape(str(x), quote=True)
PROVENANCE_LABEL = {'COURSE_SOURCE': 'Vorlesung', 'SOURCE_PARAPHRASE': 'Vorlesung (sinngemäß)', 'AUTHOR_INFERENCE': 'Erklärung (Modell, nicht aus der Vorlesung)',
                    'VERIFIED_SUPPLEMENT': 'Externe Ergänzung', 'EXAM_ADAPTED': 'Prüfungsnah adaptiert',
                    'AUTHOR_CREATED': 'Neu erstellt (Modell)'}
STATUS_LABEL = {'PENDING_SEMANTIC_REVIEW': 'ungeprüft', 'MODEL_REVIEWED_SUPPORTED': 'vom Modell gegen Quelle geprüft (nicht menschlich)',
                'MODEL_REVIEWED_UNSUPPORTED': 'vom Modell als NICHT gestützt markiert', 'OPEN_SUPPLEMENT_SOURCE_REQUIRED': 'Quelle fehlt'}
KIND_LABEL = {'MOTIVATION': 'Motivation', 'DEFINITION': 'Definition', 'THEOREM': 'Satz', 'PROOF': 'Beweis',
              'DERIVATION': 'Herleitung', 'MODEL': 'Modell', 'WORKED_EXAMPLE': 'Durchgerechnetes Beispiel',
              'COUNTEREXAMPLE': 'Gegenbeispiel', 'MISCONCEPTION': 'Typischer Fehler', 'ALGORITHM': 'Algorithmus',
              'SUBSUMPTION': 'Subsumtion', 'CASE': 'Fall', 'EXPLANATION': 'Erklärung', 'SUMMARY': 'Zusammenfassung',
              'LIMITATION': 'Grenzen'}
DIFFICULTY_ORDER = ['recall', 'guided', 'standard', 'transfer', 'exam']


def _kb_stamp():
    from . import knowledge
    return {'version': knowledge.load()['principles']['version'], 'fingerprint': knowledge.fingerprint()}


def _anchor_index(manifest):
    src = {s['source_id']: s['relative_path'] for s in manifest.get('sources', [])}
    out = {}
    for e in manifest.get('elements', []):
        loc = e.get('locator') or {}
        page = loc.get('page') if isinstance(loc, dict) else None
        out[e['element_id']] = (src.get(e.get('source_id'), e.get('source_id')), page)
    return out


DOC_LABEL = {'1_Lehrbuch.pdf': 'Lehrbuch (PDF)', '2_Arbeitsbuch.pdf': 'Arbeitsbuch mit Probeklausur und Lösungen', '3_Probeklausur_einzeln.pdf': 'Probeklausur (Einzelheft)',
             '6_Quellenabbildungen.pdf': 'Quellenabbildungen'}


def display_name(name):
    """Readable source name: a download artefact like '07 Planning aamp; Effectuation.pdf' shows as '&'."""
    import html as _html
    return _html.unescape(re.sub(r'(?<=\s)a?amp;(?=\s)', '&', str(name))) if name else name


def course_title(manifest, chapter_dir=None):
    """Course title for covers: course_profile.json in the course output folder (set with `exam-mastery course-title`),
    else the folder name without underscores. The folder name itself stays the identity (course_id hash)."""
    try:
        prof = Path(chapter_dir).resolve().parents[2] / 'course_profile.json'
        if prof.exists():
            t = json.loads(prof.read_text(encoding='utf-8')).get('course_title')
            if t:
                return str(t)
    except (IndexError, OSError, ValueError):
        pass
    return (manifest.get('root_name') or 'Kurs').replace('_', ' ')


def _anchors(refs, index):
    parts = []
    for r in refs or []:
        f, p = index.get(r, (None, None))
        f = display_name(f)
        parts.append(f'{f} S. {p}' if f and p else f or r)
    return '; '.join(dict.fromkeys(parts))


def _txt(v):
    return '' if v is None else str(v)


def _steps(steps):
    return [(_txt(s.get('statement')), _txt(s.get('justification'))) for s in steps or [] if isinstance(s, dict)]


def model(ast, manifest, plan=None):
    """One normalized view used by every renderer, so all products show the same content."""
    idx = _anchor_index(manifest)
    sol = {s['item_id']: s for s in ast.get('solutions', [])}
    # B8: blocks resting on a figure reading by the agent are labelled visibly, whatever the author wrote
    vision = {e['element_id'] for e in manifest.get('elements', []) if e.get('kind') == 'visual_transcription'}
    blocks = []
    for b in ast.get('blocks', []):
        vis_note = ' · Abbildung vom Agenten ausgewertet, nicht menschlich geprüft' if set(b.get('source_refs') or []) & vision else ''
        blocks.append({'id': b['block_id'], 'kind': b.get('kind', ''), 'label': KIND_LABEL.get(b.get('kind'), b.get('kind', '').title()),
                       'title': _txt(b.get('title')), 'body': _txt(b.get('body')), 'steps': _steps(b.get('steps')),
                       'problem': _txt(b.get('problem')), 'result': _txt(b.get('result')), 'interpretation': _txt(b.get('interpretation')),
                       'assumptions': [str(a) for a in b.get('assumptions') or []], 'norm_refs': [str(n) for n in b.get('norm_refs') or []],
                       'kc_ids': b.get('kc_ids', []), 'provenance': b.get('provenance', ''),
                       'provenance_label': PROVENANCE_LABEL.get(b.get('provenance'), b.get('provenance', '')),
                       'status': b.get('claim_support_status', ''), 'status_label': STATUS_LABEL.get(b.get('claim_support_status'), b.get('claim_support_status', '')) + vis_note,
                       'anchors': _anchors(b.get('source_refs'), idx), 'external_refs': b.get('external_refs') or []})
    from .production import evidence_gap_items
    gaps = set(evidence_gap_items(ast.get('assessments', []), ast.get('exam_answers')))
    items = []
    for a in sorted(ast.get('assessments', []), key=lambda a: (DIFFICULTY_ORDER.index(a['difficulty']) if a.get('difficulty') in DIFFICULTY_ORDER else 9, a['item_id'])):
        s = sol.get(a['item_id'], {})
        items.append({'id': a['item_id'], 'prompt': _txt(a.get('prompt')), 'difficulty': a.get('difficulty', ''), 'points': a.get('points'),
                      'points_basis': a.get('points_basis'), 'section': a.get('workbook_section') or ('MOCK_EXAM' if a.get('difficulty') == 'exam' else ''), 'faded_steps': [str(x) for x in a.get('faded_steps') or []], 'evidence_gap': a['item_id'] in gaps,
                      'operation': a.get('required_operation'), 'format': a.get('format', ''), 'kc_ids': a.get('kc_ids', []),
                      'provenance': a.get('provenance', ''), 'anchors': _anchors(a.get('source_refs'), idx),
                      'exam_links': a.get('exam_link_item_ids') or [], 'blocks': a.get('refers_to_block_ids') or [],
                      'solution': {'steps': _steps(s.get('steps')), 'answer': _txt(s.get('answer')), 'alternatives': [str(x) for x in s.get('alternatives') or []],
                                   'hints': [str(x) for x in s.get('hint_ladder') or []], 'typical_errors': [str(x) for x in s.get('typical_errors') or []],
                                   'rubric': [(_txt(r.get('criterion')), r.get('points'), _txt(r.get('evidence_of'))) for r in s.get('rubric') or []]}})
    objectives = {o.get('kc_id'): o for o in ast.get('learning_objectives', [])}
    cov = {r['kc_id']: r for r in ast.get('kc_coverage', [])}
    plan_cov = {r['kc_id']: r for r in (plan or {}).get('coverage', [])}
    plan_kc = {k['kc_id']: k for k in (plan or {}).get('competencies', [])}
    matrix = []
    for k in sorted(set(cov) | set(objectives)):
        pc = plan_cov.get(k, {})
        matrix.append({'kc_id': k, 'statement': (objectives.get(k) or {}).get('statement') or (plan_kc.get(k) or {}).get('statement', ''),
                       'required_operations': ','.join(pc.get('required_operations') or (plan_kc.get(k) or {}).get('operations') or []),
                       'in_chapter': k in ast.get('kc_ids', []), 'blocked': k in ast.get('blocked_kc_ids', []),
                       'treated_in_blocks': ' '.join(b['id'] for b in blocks if k in b['kc_ids']),
                       'practised_by_items': ' '.join(i['id'] for i in items if k in i['kc_ids']),
                       'official_exam_evidence': ' '.join(pc.get('evidence_item_ids') or []),
                       'recall_only_exam_items': ' '.join(pc.get('recall_only_item_ids') or []),
                       'coverage_status': (cov.get(k) or {}).get('status') or pc.get('status', '')})
    return {'title': ast.get('title', ''), 'course_id': ast.get('course_id', ''), 'chapter_id': ast.get('chapter_id', ''),
            'origin': ast.get('content_origin', ''), 'status': ast.get('status', ''), 'academic_status': ast.get('academic_status', ''),
            'objectives': [(o.get('kc_id'), _txt(o.get('statement')), ','.join(o.get('operations') or [])) for o in ast.get('learning_objectives', [])],
            'notation': [(_txt(n.get('symbol')), _txt(n.get('meaning')), _txt(n.get('status'))) for n in ast.get('notation', [])],
            'blocks': blocks, 'items': items, 'matrix': matrix,
            'figures': [{'id': f.get('figure_id'), 'status': f.get('status'), 'purpose': _txt(f.get('purpose')), 'caption': _txt(f.get('caption')),
                         'spec': f.get('spec'), 'alt': _txt(f.get('alt_text')), 'blocks': f.get('linked_block_ids') or [],
                         'answers_item_ids': f.get('answers_item_ids') or [],
                         'anchors': _anchors([f.get('source_element_id')] + list(f.get('source_element_ids') or []), idx),
                         'label_check': figure_label_check(f, manifest)} for f in ast.get('figures', [])],
            'exam_answers': [{'item_id': e.get('item_id'), 'question': _txt(e.get('question')), 'answer': _txt(e.get('answer')),
                              'points': [str(x) for x in e.get('answer_points') or []], 'status': _txt(e.get('status')),
                              'anchors': _anchors(e.get('source_refs'), idx), 'supplement': e.get('supplement')}
                             for e in ast.get('exam_answers', [])],
            'errata': ast.get('errata', []),
            'open_issues': [(_txt(o.get('code')), _txt(o.get('severity')), _txt(o.get('detail')), _txt(o.get('origin'))) for o in ast.get('open_issues', [])],
            'blocked_kc_ids': ast.get('blocked_kc_ids', []),
            'sources': [(s['relative_path'], s['raw_sha256'][:12]) for s in ast.get('sources', [])]}


# ------------------------------------------------------------------ figures from structured specs (B6.7)

def _as_list(v):
    """B7: 'constraints' may be one string; joining a string printed it character by character in a live run."""
    return [v] if isinstance(v, str) else list(v or [])


SPEC_META_KEYS = {'constraints', 'note', 'notes', 'layout', 'direction', 'source_page', 'source_element_ids'}


def _norm(t):
    return re.sub(r'[\s%€]+', '', str(t)).lower()      # units sit in column headers on slides; compare the values


def _meta(key):
    return key is not None and (key in SPEC_META_KEYS or bool(re.search(r'note|constraint|position|scope|rule|comment|caption', str(key))))


def _structural(key):
    return bool(re.fullmatch(r'[a-z][a-z0-9_]*', str(key)))      # 'columns', 'labels', 'financing_labels_in_source_order'


def _labels(spec, key=None):
    """All label strings of a figure spec (tree keys written as labels, leaf strings), without structure keys and
    constraint/meta text. 'Name: value' labels are checked as their two parts."""
    if _meta(key):
        return []
    if isinstance(spec, str):
        t = re.sub(r'\\text\{([^{}]*)\}', r'\1', spec).replace('\\(', '').replace('\\)', '').replace('\\%', '%')
        return [] if t.strip() in ('…', '...', '') else [x for x in re.split(r':\s+', t) if x.strip()]
    if isinstance(spec, (int, float)):
        return [str(spec)]
    if isinstance(spec, list):
        return [x for v in spec for x in _labels(v)]
    if isinstance(spec, dict):
        return [x for k, v in spec.items() if not _meta(k) for x in ([] if _structural(k) else [k]) + _labels(v, k)]
    return []


def _page_of(e):
    loc = (e or {}).get('locator') or {}
    return ((e or {}).get('source_id'), loc.get('page')) if isinstance(loc, dict) else (None, None)


def figure_label_check(f, manifest):
    """Every label of a structured figure must occur verbatim (whitespace-insensitive) on its source page(s).
    Labels that do not are paraphrases or additions and need review; nothing is drawn as source content unchecked."""
    spec = f.get('spec')
    if not isinstance(spec, (dict, list)):
        return {'status': 'NOT_APPLICABLE', 'missing': [], 'labels': 0}
    els = {e['element_id']: e for e in manifest.get('elements', [])}
    pages = {_page_of(els[r]) for r in [f.get('source_element_id')] + list(f.get('source_element_ids') or []) if r in els}
    text = _norm(' '.join(str(e.get('text') or '') for e in els.values() if _page_of(e) in pages))
    labels = list(dict.fromkeys(_labels(spec)))
    missing = [l for l in labels if _norm(l) not in text]
    if not pages or not labels:
        return {'status': 'NOT_TESTED', 'missing': labels, 'labels': len(labels)}
    return {'status': 'PASS' if not missing else 'REVIEW_REQUIRED', 'missing': missing, 'labels': len(labels)}


def _spec_html(spec, T):
    if isinstance(spec, str):
        return T(spec)
    if isinstance(spec, list) and spec and all(isinstance(x, dict) for x in spec):
        keys = list(dict.fromkeys(k for x in spec for k in x if not _meta(k)))
        cell = lambda v: '<br>'.join(T(str(y)) for y in v) if isinstance(v, list) else T(str(v if v is not None else ''))
        return ('<div class="wrap"><table class="fig"><tr>' + ''.join(f'<th>{ESC(k)}</th>' for k in keys) + '</tr>' +
                ''.join('<tr>' + ''.join(f'<td>{cell(x.get(k))}</td>' for k in keys) + '</tr>' for x in spec) + '</table></div>')
    if isinstance(spec, list):
        return ' · '.join(_spec_html(x, T) for x in spec)
    if isinstance(spec, dict):
        if isinstance(spec.get('order'), list) and isinstance(spec.get('labels'), list):
            return _spec_html([{'stage': o, 'labels': l} for o, l in zip(spec['order'], spec['labels'])], T)
        out = []
        for k, v in spec.items():
            if _meta(k):
                continue
            if isinstance(v, list) and not all(isinstance(y, dict) for y in v):
                out.append(f'<li><b>{ESC(k)}</b><ul>' + ''.join(f'<li>{_spec_html(y, T)}</li>' for y in v) + '</ul></li>')
            else:
                out.append(f'<li><b>{ESC(k)}</b>: {_spec_html(v, T)}</li>')
        return '<ul class="fig">' + ''.join(out) + '</ul>'
    return ESC(spec)


def _check_text(lc):
    return {'PASS': 'alle Beschriftungen wörtlich auf der Quellseite',
            'REVIEW_REQUIRED': 'nicht wörtlich in der Quelle, Prüfung nötig: ' + ', '.join(lc['missing'][:8])}.get(lc['status'], 'nicht prüfbar')


def _figure_html(f, T):
    spec = f['spec']
    body = _spec_html(spec, T) if isinstance(spec, (dict, list)) else '<p class="meta">Keine strukturierte Vorlage; nicht gezeichnet.</p>'
    constraints = _as_list(spec.get('constraints')) if isinstance(spec, dict) else None
    return (f'<figure class="block fig" id="{ESC(f["id"])}"><figcaption><b>{ESC(f["caption"] or f["purpose"])}</b></figcaption>{body}'
            + (f'<p class="meta">Darstellungsregeln: {ESC("; ".join(map(str, constraints)))}</p>' if constraints else '')
            + f'<p class="meta">Quelle: {ESC(f["anchors"] or "–")} · Beschriftungen: {ESC(_check_text(f["label_check"]))}</p></figure>')


EXAM_STATUS = {'ANSWERED_FROM_SOURCE': 'aus der Vorlesung', 'SOURCE_MISSING': 'Antwort nicht in den Kursquellen',
               'SUPPLEMENT_REQUIRED': 'nur mit ergänzender Quelle beantwortbar'}


def exam_answer_rows(m, exam_items):
    """One row per official question: the author's concise answer, or explicitly missing."""
    by = {e['item_id']: e for e in m['exam_answers']}
    rows = []
    for q in exam_items:
        e = by.get(q['item_id'])
        rows.append({'item_id': q['item_id'], 'question': q.get('wording', ''),
                     'answer': (e or {}).get('answer', ''), 'points': (e or {}).get('points', []),
                     'status': (e or {}).get('status') or 'MISSING_IN_AUTHOR_OUTPUT', 'anchors': (e or {}).get('anchors', ''),
                     'supplement': (e or {}).get('supplement')})
    return rows


def banner(m):
    synthetic = m['origin'] == 'SYNTHETIC_FIXTURE'
    return ('SYNTHETISCHES TESTMATERIAL – kein Lerninhalt' if synthetic else 'MODELLGENERIERTER ENTWURF') + \
        f" · Status {m['status']} · akademische Freigabe: {m['academic_status'] or 'NOT_TESTED'} · keine menschliche Quellenverifikation"


# ------------------------------------------------------------------ HTML

CSS = """:root{--ink:#16243a;--mut:#56657a;--acc:#1f5f99;--line:#d9dee6;--warn:#8a5a00;--bad:#a3261d;--bg:#fbfaf7;--card:#fff}
@media (prefers-color-scheme:dark){:root{--ink:#e8eaee;--mut:#a9b2bf;--acc:#8fb8ea;--line:#3a4250;--warn:#f0b85a;--bad:#ff8a80;--bg:#15181d;--card:#1d2128}}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.6 Georgia,serif}main{max-width:780px;margin:0 auto;padding:24px 16px 80px}
h1{font:700 30px/1.25 system-ui,sans-serif}h2{font:700 21px/1.3 system-ui,sans-serif;margin-top:40px;border-bottom:1px solid var(--line)}
h3{font:600 17px/1.35 system-ui,sans-serif;margin:0 0 6px}.banner{font:13px system-ui;color:var(--warn);border:1px solid var(--warn);padding:8px 10px;border-radius:6px}
.block{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:14px 0}
.meta{font:12.5px system-ui;color:var(--mut)}.prov-AUTHOR_INFERENCE{border-left:4px solid var(--warn)}.prov-COURSE_SOURCE{border-left:4px solid var(--acc)}
.prov-VERIFIED_SUPPLEMENT{border-left:4px solid #3b8f5a}.unsupported{border-left:4px solid var(--bad)}
ol.steps li{margin:4px 0}.just{color:var(--mut);font-size:15px}table{border-collapse:collapse;width:100%;font:14px system-ui}
td,th{border-top:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}details{margin:8px 0}summary{cursor:pointer;font:600 14px system-ui}
.wrap{overflow-x:auto}.math-i svg{vertical-align:-0.3em;max-width:100%}.math-d{overflow-x:auto;margin:10px 0;text-align:center}
.math-fail{color:var(--bad);border:1px dashed var(--bad);padding:0 3px}.errata{border:1px solid var(--bad);border-radius:6px;padding:8px 10px;margin:8px 0}
table.fig th{background:var(--line)}ul.fig{font:15px system-ui}figure.fig{margin:14px 0}nav a{margin-right:12px;font:14px system-ui;color:var(--acc)}"""


def _h_block(b, T=ESC, errata=()):
    cls = 'block prov-' + ESC(b['provenance']) + (' unsupported' if b['status'] == 'MODEL_REVIEWED_UNSUPPORTED' else '')
    parts = [f'<section class="{cls}" id="{ESC(b["id"])}"><h3>{ESC(b["label"])}{": " + ESC(b["title"]) if b["title"] else ""}</h3>']
    for e in errata:
        parts.append(f'<div class="errata"><b>Korrektur ({ESC(e.get("origin", "Review"))}, ersetzt die Modellaussage):</b> {T(e.get("text", ""))}'
                     + (f'<br><span class="meta">Quelle: {ESC(e["anchors"])}</span>' if e.get('anchors') else '') + '</div>')
    for name, val in (('Problem', b['problem']),):
        if val: parts.append(f'<p><b>{name}:</b> {T(val)}</p>')
    if b['body']: parts.append('<p>' + T(b['body']) + '</p>')
    if b['assumptions']: parts.append('<p><b>Annahmen:</b> ' + T('; '.join(x.rstrip('.;') for x in b['assumptions']) + '.') + '</p>')
    if b['steps']: parts.append('<ol class="steps">' + ''.join(f'<li>{T(s)}<br><span class="just">{T(j)}</span></li>' for s, j in b['steps']) + '</ol>')
    for name, val in (('Ergebnis', b['result']), ('Interpretation', b['interpretation'])):
        if val: parts.append(f'<p><b>{name}:</b> {T(val)}</p>')
    if b['norm_refs']: parts.append('<p class="meta">Normen: ' + ESC(', '.join(b['norm_refs'])) + '</p>')
    parts.append(f'<p class="meta">{ESC(b["provenance_label"])} · {ESC(b["status_label"])}' + (f' · Quelle: {ESC(b["anchors"])}' if b['anchors'] else ' · keine Quellenstelle') + '</p></section>')
    return ''.join(parts)


def mock_exam_items(m):
    """B7.2: exam items without an evidence gap; gap items stay in the workbook, labelled, never in the mock exam."""
    return [i for i in m['items'] if (i.get('section') == 'MOCK_EXAM' or i['difficulty'] == 'exam') and not i.get('evidence_gap')]


# B30: one workbook product, parts in this order; the mock exam is part 6, the complete solutions chapter comes last.
WORKBOOK_PARTS = [('WORKED_EXAMPLE', 'Teil 1 · Worked Examples'), ('GUIDED_FADING', 'Teil 2 · Geführte Übungen mit Fading'),
                  ('INDEPENDENT', 'Teil 3 · Eigenständige mathematische Aufgaben'), ('PROOF_DIAGNOSIS', 'Teil 4 · Beweise und Fehlerdiagnosen'),
                  ('CASE_TRANSFER', 'Teil 5 · Fallstudien und Transferprobleme')]


def workbook_parts(m):
    """[(title, items)] for parts 1-5; items without a section fall back by difficulty (legacy ASTs)."""
    exam = {i['id'] for i in mock_exam_items(m)}
    fb = {'recall': 'WORKED_EXAMPLE', 'guided': 'GUIDED_FADING', 'standard': 'INDEPENDENT', 'transfer': 'CASE_TRANSFER'}
    rest = [i for i in m['items'] if i['id'] not in exam]
    return [(t, [i for i in rest if (i.get('section') or fb.get(i['difficulty'], 'INDEPENDENT')) == k]) for k, t in WORKBOOK_PARTS]


def item_note(i):
    notes = []
    if i.get('points') is not None and i.get('points_basis') == 'NEW_DESIGN_NOT_OFFICIAL':
        notes.append('Punkte: neu entworfene Bewertung, keine offiziellen Punktwerte')
    if i.get('evidence_gap'):
        notes.append('Evidenzlücke: die nötige Quelle fehlt; nicht Teil der Probeklausur, nicht regulär bewertbar')
    return ' · '.join(notes)


def _h_item(i, with_solution, T=ESC):
    head = f'<h3>{ESC(i["id"])} · {ESC(i["difficulty"])}' + (f' · {ESC(i["points"])} P.' if i['points'] is not None else '') + '</h3>'
    note = item_note(i)
    body = f'<section class="block">{head}' + (f'<p class="meta"><b>{ESC(note)}</b></p>' if note else '') + f'<p>{T(i["prompt"])}</p><p class="meta">Operation: {ESC(i["operation"] or "–")} · {ESC(i["provenance"])}' + \
        (f' · Bezug Fragenkatalog: {ESC(", ".join(i["exam_links"]))}' if i['exam_links'] else '') + '</p>'
    if with_solution:
        s = i['solution']
        if s['hints']: body += '<details><summary>Hinweise</summary><ol>' + ''.join(f'<li>{T(h)}</li>' for h in s['hints']) + '</ol></details>'
        body += '<details><summary>Musterlösung</summary>'
        if s['steps']: body += '<ol class="steps">' + ''.join(f'<li>{T(a)}<br><span class="just">{T(b)}</span></li>' for a, b in s['steps']) + '</ol>'
        body += f'<p><b>Antwort:</b> {T(s["answer"])}</p>'
        if s['alternatives']: body += '<p><b>Alternativen:</b> ' + T('; '.join(s['alternatives'])) + '</p>'
        if s['rubric']: body += '<div class="wrap"><table><tr><th>Kriterium</th><th>P.</th><th>Erkennbar an</th></tr>' + ''.join(f'<tr><td>{T(c)}</td><td>{ESC(p)}</td><td>{T(e)}</td></tr>' for c, p, e in s['rubric']) + '</table></div>'
        if s['typical_errors']: body += '<p><b>Typische Fehler:</b> ' + T('; '.join(s['typical_errors'])) + '</p>'
        body += '</details>'
    return body + '</section>'


def publish_html(m, out, mr=None):
    T = mr.html if mr else ESC
    exam = mock_exam_items(m)
    nav = '<nav><a href="#lehrbuch">Lehrbuch</a><a href="#arbeitsbuch">Arbeitsbuch</a><a href="#loesungen">Lösungen</a>' + \
          ('<a href="#probeklausur">Probeklausur</a>' if exam else '') + '<a href="#matrix">Kompetenzmatrix</a><a href="#offen">Offene Punkte</a></nav>'
    p = [f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>{ESC(m["title"])}</title><style>{CSS}</style></head><body><main><p class="banner">{ESC(banner(m))}</p><h1>{ESC(m["title"])}</h1>{nav}']
    if m['objectives']:
        p.append('<h2>Lernziele</h2><ol>' + ''.join(f'<li>{T(s)} <span class="meta">({ESC(o)})</span></li>' for _, s, o in m['objectives']) + '</ol>')
    if m['notation']:
        p.append('<h2>Notation</h2><div class="wrap"><table><tr><th>Symbol</th><th>Bedeutung</th><th>Status</th></tr>' + ''.join(f'<tr><td>{T(a)}</td><td>{T(b)}</td><td>{ESC(c)}</td></tr>' for a, b, c in m['notation']) + '</table></div>')
    err = {}
    for e in m.get('errata', []):
        err.setdefault(e.get('object_id'), []).append(e)
    figs = {}
    for f in m['figures']:
        figs.setdefault(f['blocks'][0] if f['blocks'] else None, []).append(f)
    p.append('<h2 id="lehrbuch">Lehrbuch</h2>' + ''.join(_h_block(b, T, err.get(b['id'], ())) + ''.join(_figure_html(f, T) for f in figs.get(b['id'], []))
                                                       for b in m['blocks']))
    if figs.get(None):
        p.append('<h2>Weitere Abbildungen</h2>' + ''.join(_figure_html(f, T) for f in figs[None]))
    if m.get('exam_rows'):
        p.append('<h2 id="pruefung">Prüfungsfragen: Kurzantworten</h2><p class="meta">Offizielle Fragen des Kurses. Antworten vom Modell, '
                 'nicht menschlich geprüft. Ergänzende Quellen sind getrennt gekennzeichnet.</p>' + ''.join(
            f'<section class="block"><h3>{T(r["question"])}</h3>' +
            (f'<p>{T(r["answer"])}</p>' if r['answer'] else '') +
            (('<ul>' + ''.join(f'<li>{T(x)}</li>' for x in r['points']) + '</ul>') if r['points'] else '') +
            (f'<p class="meta">Ergänzung (externe Quelle, nicht Vorlesung): {T(str(r["supplement"]))}</p>' if r.get('supplement') else '') +
            f'<p class="meta">{ESC(r["item_id"])} · {ESC(EXAM_STATUS.get(r["status"], "fehlt im Author-Output (Neugenerierung nötig)"))}'
            + (f' · Quelle: {ESC(r["anchors"])}' if r['anchors'] else '') + '</p></section>' for r in m['exam_rows']))
    p.append('<h2 id="arbeitsbuch">Arbeitsbuch</h2>' + ''.join(_h_item(i, False, T) for i in m['items']))
    p.append('<h2 id="loesungen">Musterlösungen</h2>' + ''.join(_h_item(i, True, T) for i in m['items']))
    if exam:
        total = sum(i['points'] or 0 for i in exam)
        p.append(f'<h2 id="probeklausur">Probeklausur ({total} Punkte)</h2>' + ''.join(_h_item(i, False, T) for i in exam))
    p.append('<h2 id="matrix">Kompetenzmatrix</h2><div class="wrap"><table><tr><th>KC</th><th>Kompetenz</th><th>Operation</th><th>Lehrbuch</th><th>Übung</th><th>Prüfungsbeleg</th><th>Nur Recall</th><th>Status</th></tr>' +
             ''.join(f'<tr><td>{ESC(r["kc_id"])}</td><td>{T(r["statement"])}{" (blockiert)" if r["blocked"] else ""}</td><td>{ESC(r["required_operations"])}</td><td>{ESC(r["treated_in_blocks"])}</td><td>{ESC(r["practised_by_items"])}</td><td>{ESC(r["official_exam_evidence"])}</td><td>{ESC(r["recall_only_exam_items"])}</td><td>{ESC(r["coverage_status"])}</td></tr>' for r in m['matrix']) + '</table></div>')
    p.append('<h2 id="offen">Offene Punkte und Unsicherheiten</h2><div class="wrap"><table><tr><th>Code</th><th>Schwere</th><th>Detail</th><th>Herkunft</th></tr>' +
             ''.join(f'<tr><td>{ESC(a)}</td><td>{ESC(b)}</td><td>{T(c)}</td><td>{ESC(d)}</td></tr>' for a, b, c, d in m['open_issues']) + '</table></div>')
    p.append('<p class="meta">Quellen: ' + ESC('; '.join(f'{a} ({b}…)' for a, b in m['sources'])) + '</p></main></body></html>')
    out.write_text(''.join(p), encoding='utf-8')
    return out


# ------------------------------------------------------------------ PDF

def publish_pdf(m, out, mr=None):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, LongTable, TableStyle, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from .publish import register_fonts
    font, bold = register_fonts()
    ink, acc, mut, warn = (colors.HexColor(c) for c in ('#16243a', '#1f5f99', '#56657a', '#8a5a00'))
    st = {'title': ParagraphStyle('t', fontName=bold, fontSize=21, leading=27, textColor=ink, spaceAfter=10),
          'h1': ParagraphStyle('h1', fontName=bold, fontSize=15, leading=20, textColor=ink, spaceBefore=14, spaceAfter=8, keepWithNext=True),
          'h2': ParagraphStyle('h2', fontName=bold, fontSize=10.5, leading=14, textColor=acc, spaceBefore=8, spaceAfter=4, keepWithNext=True),
          'body': ParagraphStyle('b', fontName=font, fontSize=10, leading=14.5, spaceAfter=5),
          'small': ParagraphStyle('s', fontName=font, fontSize=8, leading=10.5, textColor=mut, spaceAfter=6),
          'warn': ParagraphStyle('w', fontName=font, fontSize=8.5, leading=11, textColor=warn, spaceAfter=8),
          'cell': ParagraphStyle('c', fontName=font, fontSize=7.5, leading=9.5)}
    P = lambda t, s='body': mr.flow(t, st[s]) if mr else Paragraph(ESC(t).replace('\n', '<br/>'), st[s])
    # table cells (PDF display only): reportlab breaks lines at spaces, so codes show '_' as a space instead of
    # being split letter by letter; identifiers stay exact in HTML, CSV and JSON.
    def C(t, w=470):
        if mr and MATH_RE.search(str(t)):                   # formulas in cells are rendered like in the text (B6.7)
            return Paragraph(mr.rl(str(t), max_width=max(20, w - 8)), st['cell'])
        return Paragraph(ESC(re.sub(r',(?![\d\s])', ', ', str(t).replace('_', ' '))).replace('\n', '<br/>'), st['cell'])

    def table(rows, widths):
        t = LongTable([[C(c, w) for c, w in zip(r, widths)] for r in rows], colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, 0), 0.6, acc),
                               ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f4f7')])]))
        return t

    def spec_flow(spec):
        if isinstance(spec, list) and spec and all(isinstance(x, dict) for x in spec):
            keys = list(dict.fromkeys(k for x in spec for k in x if not _meta(k)))
            w = [503 / max(1, len(keys))] * len(keys)
            return [table([keys] + [['\n'.join(map(str, x.get(k))) if isinstance(x.get(k), list) else str(x.get(k) or '') for k in keys] for x in spec], w)]
        if isinstance(spec, dict) and isinstance(spec.get('order'), list) and isinstance(spec.get('labels'), list):
            return spec_flow([{'stage': o, 'labels': l} for o, l in zip(spec['order'], spec['labels'])])
        if isinstance(spec, dict):
            out = []
            for k, v in spec.items():
                if _meta(k): continue
                if isinstance(v, list) and not all(isinstance(y, dict) for y in v):
                    out.append(P(f'<b>{ESC(k)}</b>: ' + ' · '.join(ESC(json.dumps(y, ensure_ascii=False) if not isinstance(y, str) else y) for y in v)) if not mr else
                               P(f'{k}: ' + ' · '.join(y if isinstance(y, str) else json.dumps(y, ensure_ascii=False) for y in v)))
                else:
                    out += [P(f'{k}:')] + spec_flow(v)
            return out
        return [P(spec if isinstance(spec, str) else json.dumps(spec, ensure_ascii=False))]

    def figure(fg):
        f = [P('Abbildung: ' + (fg['caption'] or fg['purpose']), 'h2')]
        f += spec_flow(fg['spec']) if isinstance(fg['spec'], (dict, list)) else [P('Keine strukturierte Vorlage; nicht gezeichnet.', 'small')]
        cons = _as_list(fg['spec'].get('constraints')) if isinstance(fg['spec'], dict) else None
        if cons: f.append(P('Darstellungsregeln: ' + '; '.join(map(str, cons)), 'small'))
        f.append(P(f"Quelle: {fg['anchors'] or '–'} · Beschriftungen: {_check_text(fg['label_check'])}", 'small'))
        return f

    def block(b, errata=()):
        f = [P(b['label'] + (': ' + b['title'] if b['title'] else ''), 'h2')]
        for e in errata:
            f.append(P(f"Korrektur ({e.get('origin', 'Review')}, ersetzt die Modellaussage): {e.get('text', '')}", 'warn'))
        if b['problem']: f.append(P('Problem: ' + b['problem']))
        if b['body']: f.append(P(b['body']))
        if b['assumptions']: f.append(P('Annahmen: ' + '; '.join(a.rstrip('.;') for a in b['assumptions']) + '.'))
        for n, (s, j) in enumerate(b['steps'], 1):
            s = re.sub(r'^\s*\\\[(.+)\\\]\s*$', lambda g: '\\(' + g.group(1) + '\\)', s, flags=re.S)   # a lone display formula flows inline after its number
            f.append(P(f'{n}. {s}  –  {j}'))
        if b['result']: f.append(P('Ergebnis: ' + b['result']))
        if b['interpretation']: f.append(P('Interpretation: ' + b['interpretation']))
        f.append(P(f"{b['provenance_label']} · {b['status_label']} · " + (('Quelle: ' + b['anchors']) if b['anchors'] else 'keine Quellenstelle'), 'small'))
        return KeepTogether(f) if sum(len(x.text) for x in f if hasattr(x, 'text')) < 1500 else f

    def item(i, sol):
        f = [P(f"{i['id']} · {i['difficulty']}" + (f" · {i['points']} P." if i['points'] is not None else ''), 'h2')]
        if item_note(i): f.append(P(item_note(i), 'small'))
        f.append(P(i['prompt']))
        if not sol:
            return f + [Spacer(1, 18)]
        s = i['solution']
        for n, (a, b) in enumerate(s['steps'], 1): f.append(P(f'{n}. {a}  –  {b}'))
        f.append(P('Antwort: ' + s['answer']))
        if s['alternatives']: f.append(P('Alternativen: ' + '; '.join(s['alternatives'])))
        if s['rubric']: f.append(table([['Kriterium', 'P.', 'Erkennbar an']] + [[c, str(p), e] for c, p, e in s['rubric']], [290, 30, 183]))
        if s['typical_errors']: f.append(P('Typische Fehler: ' + '; '.join(s['typical_errors'])))
        return f

    flow = [P(banner(m), 'warn'), P(m['title'], 'title')]
    if m['objectives']:
        flow.append(P('Lernziele', 'h1')); flow += [P(f'{n}. {s} ({o})') for n, (_, s, o) in enumerate(m['objectives'], 1)]
    if m['notation']:
        flow += [P('Notation', 'h1'), table([['Symbol', 'Bedeutung', 'Status']] + [list(x) for x in m['notation']], [80, 330, 93])]
    flow.append(P('Lehrbuch', 'h1'))
    err, figs = {}, {}
    for e in m.get('errata', []): err.setdefault(e.get('object_id'), []).append(e)
    for fg in m['figures']: figs.setdefault(fg['blocks'][0] if fg['blocks'] else None, []).append(fg)
    for b in m['blocks']:
        x = block(b, err.get(b['id'], ())); flow += x if isinstance(x, list) else [x]
        for fg in figs.get(b['id'], []): flow += figure(fg)
    for fg in figs.get(None, []): flow += figure(fg)
    if m.get('exam_rows'):
        flow += [PageBreak(), P('Prüfungsfragen: Kurzantworten', 'title'),
                 P('Offizielle Fragen des Kurses. Antworten vom Modell, nicht menschlich geprüft. Ergänzende Quellen sind getrennt gekennzeichnet.', 'small')]
        for r in m['exam_rows']:
            flow.append(P(r['question'], 'h2'))
            if r['answer']: flow.append(P(r['answer']))
            flow += [P('• ' + x) for x in r['points']]
            if r.get('supplement'): flow.append(P('Ergänzung (externe Quelle, nicht Vorlesung): ' + str(r['supplement']), 'small'))
            flow.append(P(f"{r['item_id']} · {EXAM_STATUS.get(r['status'], 'fehlt im Author-Output (Neugenerierung nötig)')}" +
                          (f" · Quelle: {r['anchors']}" if r['anchors'] else ''), 'small'))
    flow += [PageBreak(), P('Arbeitsbuch', 'title'),
             P('Ein zusammenhängendes Arbeitsbuch: Teile 1–5 steigern die Selbstständigkeit, Teil 6 ist die integrierte Probeklausur, '
               'Teil 7 enthält alle vollständigen Lösungen mit Zwischenrechnungen und Bewertungsschema.')]
    for title, its in workbook_parts(m):
        if not its: continue
        flow.append(P(title, 'h1'))
        for i in its:
            flow += item(i, False)
            if i.get('faded_steps'): flow.append(P('Offene Schritte: ' + '; '.join(i['faded_steps']), 'small'))
    exam = mock_exam_items(m)
    if exam:
        flow += [PageBreak(), P(f"Teil 6 · Probeklausur ({sum(i['points'] or 0 for i in exam)} Punkte)", 'h1'),
                 P('Bearbeitungszeit und Hilfsmittel wie in der Klausur; Lösungen in Teil 7.', 'small')]
        for i in exam: flow += item(i, False)
    flow += [PageBreak(), P('Teil 7 · Lösungen', 'h1')]
    for title, its in workbook_parts(m) + [('Teil 6 · Probeklausur', exam)]:
        if not its: continue
        flow.append(P('Lösungen zu ' + title, 'h2'))
        for i in its: flow += item(i, True)
    flow += [PageBreak(), P('Kompetenzmatrix', 'title'),
             table([['KC', 'Kompetenz', 'Op.', 'Lehrbuch', 'Übung', 'Prüfungsbeleg', 'Nur Recall', 'Status']] +
                   [[r['kc_id'][-8:], r['statement'] + (' (blockiert)' if r['blocked'] else ''), r['required_operations'], r['treated_in_blocks'],
                     r['practised_by_items'], r['official_exam_evidence'], r['recall_only_exam_items'], r['coverage_status']] for r in m['matrix']],
                   [40, 118, 44, 66, 56, 52, 50, 77]),
             P('Offene Punkte und Unsicherheiten', 'h1'),
             table([['Code', 'Schwere', 'Detail', 'Herkunft']] + [list(x) for x in m['open_issues']], [112, 52, 264, 75]),
             P('Quellen: ' + '; '.join(f'{a} ({b}…)' for a, b in m['sources']), 'small')]
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=46, rightMargin=46, topMargin=50, bottomMargin=50,
                            title=m['title'] + ' | Exam Mastery', author='Exam Mastery Studio')

    def footer(c, d):
        c.setFont(font, 7.5); c.setFillColor(mut)
        c.drawString(46, 30, ('SYNTHETISCHES TESTMATERIAL' if m['origin'] == 'SYNTHETIC_FIXTURE' else 'MODELLENTWURF') +
                     ' · nicht menschlich verifiziert · ' + m['title'][:60]); c.drawRightString(A4[0] - 46, 30, str(d.page))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    return out


# ------------------------------------------------------------------ Anki

def cards(m):
    """Deterministic cards: definitions/models from the textbook and recall/guided items with their answer.
    IDs are chapter_id:block_id / chapter_id:item_id, so rebuilds update instead of duplicating."""
    out = []
    for b in m['blocks']:
        if b['kind'] in ('DEFINITION', 'THEOREM', 'MODEL') and (b['title'] or b['body']) and b['status'] != 'MODEL_REVIEWED_UNSUPPORTED':
            q = b['title'] or (b['body'][:80] + '…')
            out.append({'id': f"{m['chapter_id']}:{b['id']}", 'question': f"{b['label']}: {q}?", 'answer': b['body'] or b['result'],
                        'explanation': f"{b['provenance_label']} · {b['status_label']}", 'source_refs': [b['anchors'] or 'keine Quellenstelle']})
    for i in m['items']:
        if i['difficulty'] in ('recall', 'guided') and i['solution']['answer']:
            out.append({'id': f"{m['chapter_id']}:{i['id']}", 'question': i['prompt'], 'answer': i['solution']['answer'],
                        'explanation': '; '.join(s for s, _ in i['solution']['steps'][:3]), 'source_refs': [i['anchors'] or i['provenance'] or 'Übung']})
    return out


def publish_anki(m, pub_dir, verify=True):
    from .publish import publish_cards
    design = {'theme': {'ink': '#16243a', 'accent': '#1f5f99', 'paper': '#ffffff', 'surface': '#f7f8fa'}}
    cs = cards(m)
    write_json(pub_dir / 'architect.json', {'course_id': m['course_id'] + ':' + m['chapter_id'], 'title': m['title']})
    publish_cards({'course_id': m['course_id'], 'title': m['title']}, {'cards': cs}, design, pub_dir / 'artifacts/anki')
    result = {'cards': len(cs)}
    if verify and cs:
        from .anki_qa import verify as anki_verify
        result.update(anki_verify(pub_dir))
    return result


# ------------------------------------------------------------------ separate product files (B7.4)

SECTION_FILES = [('Lehrbuch', '1_Lehrbuch.pdf'), ('Arbeitsbuch', '2_Arbeitsbuch.pdf'), ('Kompetenzmatrix', None)]


def split_products(pdf, out_dir, mock_ids=()):
    """Cut the chapter PDF into one file per product at its section title pages. The mock exam file also gets the
    worked solutions of its items. Same pages as kapitel.pdf, nothing re-rendered. Returns {file: page count}."""
    import pymupdf, re
    doc = pymupdf.open(pdf)
    first = lambda title: next((i for i, pg in enumerate(doc) if re.search(r'^\s*' + re.escape(title) + r'\b', pg.get_text(), re.M)
                                and (title != 'Lehrbuch' or i < 3)), None)
    starts = [(t, f, 0 if t == 'Lehrbuch' else first(t)) for t, f in SECTION_FILES]
    starts = [(t, f, i) for t, f, i in starts if i is not None]
    out = {}
    for k, (t, f, i) in enumerate(starts):
        if f is None:
            continue
        end = starts[k + 1][2] - 1 if k + 1 < len(starts) else doc.page_count - 1
        new = pymupdf.open(); new.insert_pdf(doc, from_page=i, to_page=end)
        if t == 'Probeklausur' and mock_ids:
            sol = next(x[2] for x in starts if x[0] == 'Musterlösungen'); stop = i - 1
            pages = [n for n in range(sol, stop + 1) if any(re.search(re.escape(m) + r' · ', doc[n].get_text()) for m in mock_ids)]
            for n in pages:
                new.insert_pdf(doc, from_page=n, to_page=n)
        new.save(Path(out_dir) / f); out[f] = new.page_count
    return out


def decimal_convention(ast):
    """'.' or ',' -- whichever decimal separator the authored text uses more (0.9 vs 0,9). Thousands groups like 1.000
    or 2,144 are ignored. Ties keep the German comma."""
    txt = json.dumps(ast, ensure_ascii=False)
    dot = len(re.findall(r'(?<![\d.,])\d+\.\d{1,2}(?!\d)(?![.,]\d)', txt))
    com = len(re.findall(r'(?<![\d.,])\d+,\d{1,2}(?!\d)(?![.,]\d)', txt))
    return '.' if dot > com else ','


def publish_visual_sources(ctx, manifest, assets_root, out_pdf, chapter_sources=None, evidence=None):
    """B7.4: every slide whose figure the engine did not evaluate (text-only scope or VISUAL_REVIEW_REQUIRED) is kept as
    a page image with its source, page and status, so no figure content silently disappears. Nothing is interpreted."""
    import pymupdf
    els = {e['element_id']: e for e in manifest.get('elements', [])}
    srcs = {x['source_id']: x for x in manifest.get('sources', [])}
    renders = {(e['source_id'], (e.get('locator') or {}).get('page')): e['asset']['path'] for e in manifest.get('elements', [])
               if e['kind'] == 'rendered_page' and e.get('asset')}
    # status is decided PER PAGE from the imported figure readings (visual_evidence.json), never inherited from a
    # competency: a competency status said "not evaluated" for pages whose reading was accepted, and vice versa
    read = {}
    for pg_ in (evidence or {}).get('pages') or []:
        read[(pg_.get('source_id'), pg_.get('page'))] = 'dekorativ' if pg_.get('decorative') else 'ausgewertet'
    ST = {'ausgewertet': 'Abbildung vom Agenten ausgewertet (Bildverständnis, nicht menschlich geprüft); Inhalt im Lehrtext',
          'dekorativ': 'Abbildung vom Agenten als dekorativ eingestuft; aus dem Folientext gelehrt'}
    # only the chapter's own decks: anchors into other lectures (recurring slide titles) are not this chapter's figures
    if not chapter_sources:
        from collections import Counter as _C
        cnt = _C(els[a]['source_id'] for c in ctx.get('competencies') or [] for a in c.get('source_anchor_ids') or [] if a in els)
        chapter_sources = [cnt.most_common(1)[0][0]] if cnt else []
    chapter_sources = set(chapter_sources)
    rows = []
    for c in ctx.get('competencies') or []:
        vis = set(c.get('blocked') or []) & {'ESSENTIAL_VISUAL_UNRESOLVED', 'SCANNED_PAGE_NO_OCR'}
        auto = c.get('auto_scope')
        if not vis and not auto:
            continue
        basis = (auto or {}).get('basis')
        status = ('NICHT PRODUZIERT: Inhalt liegt in der Abbildung (VISUAL_REVIEW_REQUIRED)' if vis and not auto else
                  'Abbildung vom Agenten ausgewertet (Bildverständnis, nicht menschlich geprüft); Inhalt im Lehrtext'
                  if basis == 'AUTO_VISION_TRANSCRIBED' else
                  'Abbildung vom Agenten als dekorativ eingestuft; aus dem Folientext gelehrt' if ((auto or {}).get('reason') or '').startswith('figure judged decorative') else
                  'Aus dem Folientext gelehrt; die Abbildung wurde nicht ausgewertet')
        for a in c.get('source_anchor_ids') or []:
            e = els.get(a)
            key = (e['source_id'], (e.get('locator') or {}).get('page')) if e else None
            if not key or key[0] not in chapter_sources:
                continue
            st = ST[read[key]] if key in read else status
            if evidence is not None and key not in read and st == ST['ausgewertet']:
                st = 'Aus dem Folientext gelehrt; zu dieser Seite liegt keine akzeptierte Abbildungslesung vor'
            if st.startswith('NICHT PRODUZIERT') and key in read:
                st = ST['ausgewertet']
            if key in renders and key not in [r[0] for r in rows]:
                rows.append((key, c['statement'], st))
    # pages with an accepted reading that no blocked/auto-scoped competency anchors are still figures of this chapter
    for key, kind in read.items():
        if key[0] in chapter_sources and key in renders and key not in [r[0] for r in rows]:
            rows.append((key, '', ST[kind]))
    rows.sort(key=lambda r: (r[0][0], r[0][1] or 0))
    if not rows:
        return 0
    doc = pymupdf.open()
    cover = doc.new_page(width=595, height=842)
    from collections import Counter
    n = Counter('ausgewertet' if 'vom Agenten ausgewertet' in r[2] else 'dekorativ' if 'dekorativ' in r[2] else
                'offen' if r[2].startswith('NICHT PRODUZIERT') else 'text' for r in rows)
    cover.insert_textbox(pymupdf.Rect(50, 60, 545, 800), 'Quellenabbildungen\n\n'
        'Diese Folien enthalten Abbildungen. Sie sind hier unverändert mit Quelle, Seite und Status erhalten, damit jede '
        'Aussage am Original nachgeprüft werden kann.\n\n'
        f"{n['ausgewertet']} Folien: Abbildung vom Agenten ausgewertet (Bildverständnis der Agent-Sitzung, deterministisch "
        'gegen Seitenbild, Textschicht und Rechnungen geprüft, NICHT menschlich geprüft).\n'
        f"{n['dekorativ']} Folien: Abbildung vom Agenten als dekorativ eingestuft (kein fachlicher Inhalt im Bild).\n"
        f"{n['text']} Folien: Abbildung nicht ausgewertet; gelehrt wird nur der Folientext.\n"
        f"{n['offen']} Folien: Inhalt liegt in der Abbildung und ist nicht Teil des Materials (menschliche Sichtung offen).\n\n"
        f'{len(rows)} Folien.', fontsize=11)
    for (sid, page), stmt, status in rows:
        pg = doc.new_page(width=842, height=595)
        pg.insert_textbox(pymupdf.Rect(30, 18, 812, 70), "\n".join(x for x in (f"{display_name(srcs.get(sid, {}).get('relative_path', sid))}, S. {page}", stmt, status) if x), fontsize=9)
        img = Path(assets_root) / renders[(sid, page)]
        if img.exists():
            # JPEG at print quality: the slide renders are photos/diagrams; PNG made the file ~2 MB per page
            pg.insert_image(pymupdf.Rect(30, 75, 812, 575), stream=pymupdf.Pixmap(str(img)).tobytes('jpeg', jpg_quality=85), keep_proportion=True)
    doc.save(out_pdf, garbage=3, deflate=True)
    return len(rows)


# ------------------------------------------------------------------ entry point

def _page_kind(pg):
    import pymupdf
    col = lambda c: c is not None and len(c) == 3 and (max(c) - min(c)) > 0.08
    A = pg.rect.width * pg.rect.height
    img = max([pymupdf.Rect(i['bbox']).width * pymupdf.Rect(i['bbox']).height / A for i in pg.get_image_info()] or [0])
    dr = pg.get_drawings()
    strokes = sum(1 for x in dr if col(x.get('color')))
    fill = sum(x['rect'].width * x['rect'].height for x in dr if col(x.get('fill')) and x['rect'].height > 6) / A
    cap = bool(re.search(r'(Abbildung|Figure|Abb\.)\s+\d+\.\d+', pg.get_text()))
    return 'F' if cap or img >= 0.08 or strokes >= 15 else 'B' if fill >= 0.06 else 't'


def _layout_lint(art, name):
    """B33: what the typesetter's layout lint found and repaired (inline formulas reflowed) or could not repair."""
    f = Path(art) / f'..{name}.main.layout_lint.json'
    if not f.exists():
        return {'status': 'NOT_RUN'}
    d = json.loads(f.read_text(encoding='utf-8'))
    d['status'] = 'FAIL' if d.get('overflow') or d.get('broken_images') else 'PASS'
    pdf = Path(art) / f'{name}.pdf'
    if pdf.exists():                 # B33: near-empty pages (orphaned headings, spilled tiles, stranded rubrics); cover excluded
        import pymupdf
        doc = pymupdf.open(pdf)
        d['sparse_pages'] = [i + 1 for i in range(1, doc.page_count)
                             if len(doc[i].get_text().strip()) < 350 and not doc[i].get_images() and len(doc[i].get_drawings()) < 40]
        if d['sparse_pages'] and d['status'] == 'PASS':
            d['status'] = 'WARN'
        # B33 page audit (calibrated on the RL pilot: V1 textbook 22/29 text-only pages, V2/V3 none in the core):
        # 'F' figure page (figure caption, large image or >= 15 coloured strokes), 'B' component page (coloured boxes
        # cover >= 6 % of the page), 't' text only. Formula glyphs are black vector paths and never count.
        # A monotone stretch = >= 3 consecutive text-only pages inside the core (between the first and last visual
        # page), so table of contents, opener and back matter (answers, glossary, sources) are not penalised.
        kinds = [_page_kind(doc[i]) for i in range(1, doc.page_count)]
        vis = [i for i, k in enumerate(kinds) if k != 't']
        runs, cur = [], []
        for i, k in enumerate(kinds):
            inside = bool(vis) and vis[0] < i < vis[-1]
            if k == 't' and inside:
                cur.append(i + 2)
            else:
                if len(cur) >= 3:
                    runs.append(cur)
                cur = []
        d['page_audit'] = {'pages': len(kinds), 'profile': ''.join(kinds), 'text_only_pages': kinds.count('t'), 'figure_pages': kinds.count('F'),
                           'component_pages': kinds.count('B'), 'monotone_runs': runs,
                           'max_chars_page': max((len(doc[i].get_text()) for i in range(1, doc.page_count)), default=0)}
        if runs and d['status'] == 'PASS' and name.startswith('1_'):
            d['status'] = 'WARN'
        # B34 raw-math gate on the RENDERED pdf text: TeX that MathJax did not typeset (\\frac, \\( ...) or caret/underscore
        # notation in running text ('100^14', 'V_{k+1}') is visible to the reader and fails the document.
        raw = []
        for i in range(doc.page_count):
            t = doc[i].get_text()
            for mm in RAW_MATH.finditer(t):
                raw.append({'page': i + 1, 'text': t[max(0, mm.start() - 25):mm.end() + 25].replace('\n', ' ')})
        d['raw_math'] = raw[:40]
        if raw:
            d['status'] = 'FAIL'
        # B34 typographic discipline: distinct text sizes actually used (MathJax glyphs are paths and do not count)
        sizes = {}
        for i in range(1, doc.page_count):
            for blk in doc[i].get_text('dict')['blocks']:
                for ln in blk.get('lines', []):
                    for sp in ln.get('spans', []):
                        if sp['text'].strip():
                            k = round(sp['size'] * 2) / 2
                            sizes[k] = sizes.get(k, 0) + len(sp['text'])
        tot = sum(sizes.values()) or 1
        d['type_sizes'] = {f'{k:g}pt': round(v / tot, 4) for k, v in sorted(sizes.items())}
        d['type_sizes_main'] = sorted(f'{k:g}pt' for k, v in sizes.items() if v / tot >= 0.01)
    return d


RAW_MATH = re.compile(r'[A-Za-z0-9)\]]\^\{?[-\w(]|[A-Za-z]_\{|\\(?:frac|gamma|sum|pi|max|mathbb|mathcal|left|right|cdot)\b|\\[()\[\]]')


QUALITY_METRICS = ('numeric_fail', 'didactic_fail', 'semantic_fail', 'anki_render_fail', 'open_blockers', 'layout_fail',
                   'monotone_runs', 'items_without_solution')


def _metrics(report, book):
    docs = report.get('documents') or {}
    anki = (report.get('products') or {}).get('anki') or {}
    return {'numeric_fail': (report.get('numeric_checks') or {}).get('counts', {}).get('FAIL', 0),
            'didactic_fail': (report.get('didactic_rules') or {}).get('counts', {}).get('FAIL', 0),
            'semantic_fail': (report.get('semantic_checks') or {}).get('counts', {}).get('FAIL', 0),
            'anki_render_fail': len((anki.get('render_gate') or {}).get('fail') or {}),
            'open_blockers': len((report.get('issue_lifecycle') or {}).get('open_blockers') or []),
            'layout_fail': sum(1 for v in docs.values() if (v.get('layout_lint') or {}).get('status') == 'FAIL'),
            'monotone_runs': sum(len(((v.get('layout_lint') or {}).get('page_audit') or {}).get('monotone_runs') or []) for v in docs.values()),
            'items_without_solution': sum(1 for st in book.get('stages') or [] for i in st['items'] if not (i.get('solution') or {}).get('answer')),
            'figures_used': len({b.get('id') or b.get('figure') for s in book.get('sections') or [] for b in s['blocks'] if b.get('type') in ('figure', 'figtext')}),
            'cards': anki.get('cards', 0), 'items': sum(len(st['items']) for st in book.get('stages') or [])}


def regression_guard(chapter_dir, report, book):
    """B33 ratchet: compares the quality metrics with the last accepted baseline of this chapter (stored next to the
    edition). Any defect metric that got worse is a regression (FAIL); a drop of figures/items/cards by more than 20 %
    is reported for review. Without regressions the baseline is advanced; with regressions it is kept."""
    ch = Path(chapter_dir)
    bp = ch.parent.parent.parent / 'editions' / f'{ch.name}.quality_baseline.json'
    cur = _metrics(report, book)
    if not bp.exists():
        bp.parent.mkdir(parents=True, exist_ok=True)
        write_json(bp, {'schema': 'em-quality-baseline-v1', 'metrics': cur})
        return {'status': 'BASELINE_CREATED', 'metrics': cur}
    base = json.loads(bp.read_text(encoding='utf-8'))['metrics']
    worse = {k: [base.get(k, 0), cur[k]] for k in QUALITY_METRICS if cur[k] > base.get(k, 0)}
    shrink = {k: [base[k], cur[k]] for k in ('figures_used', 'items', 'cards') if base.get(k) and cur[k] < 0.8 * base[k]}
    if not worse:
        write_json(bp, {'schema': 'em-quality-baseline-v1', 'metrics': cur})
    return {'status': 'FAIL' if worse else 'REVIEW' if shrink else 'PASS', 'regressions': worse, 'shrinkage': shrink, 'metrics': cur, 'baseline': base}


def publish_chapter(chapter_dir, manifest, plan=None, verify_anki=True, assets_root=None, edition=None):
    chapter_dir = Path(chapter_dir)
    ast = json.loads((chapter_dir / 'content_ast.json').read_text(encoding='utf-8'))
    # B14: documented editorial corrections (outside the lecture folder); content_ast.json itself stays untouched
    from . import errata as _errata
    ast, errata_applied = _errata.apply(ast, _errata.load(chapter_dir))
    from .production import missing_exam_points
    miss = missing_exam_points(ast.get('assessments') or [], ast.get('exam_answers'))
    if miss:  # B7.1: never publish a mock exam whose items carry no points
        raise ContractError(f'MOCK_EXAM_POINTS_MISSING: exam items {miss} have no points; not published')
    m = model(ast, manifest, plan)
    ctx_p = chapter_dir / 'chapter_context.json'
    if ctx_p.exists():
        m['exam_rows'] = exam_answer_rows(m, json.loads(ctx_p.read_text(encoding='utf-8')).get('exam_items', []))
    pub = chapter_dir / 'publish'; art = pub / 'artifacts'; art.mkdir(parents=True, exist_ok=True)
    mr = MathRenderer(art / 'math')
    publish_html(m, art / 'kapitel.html', mr)
    publish_pdf(m, art / 'kapitel.pdf', mr)
    # B9: the learner documents are typeset separately (own cover, TOC, numbering); kapitel.pdf stays an internal overview
    from . import typeset, didactic_rules, numeric_checks, anki_v2, semantic_checks
    from .book_model import book_from_ast
    from datetime import date
    try:
        from importlib.metadata import version as _v
        eng = 'v' + _v('exam-mastery-engine')
    except Exception:
        eng = ''
    book = book_from_ast(ast, manifest, plan, course=course_title(manifest, chapter_dir), engine=eng, date=date.today().strftime('%d.%m.%Y'))
    # B20: curated edition (supplements, examples, blueprint exam, cards) outside the lecture folder, no model call
    from . import edition as _edition
    book, edition_report = _edition.apply(book, edition if edition is not None else _edition.load(chapter_dir))
    # B34: printed slide numbers (references read "Folie 24", not "PDF page 23"); unreadable decks keep PDF pages
    from .slide_numbers import course_maps
    _st = chapter_dir.parent.parent / 'status.json'
    try:
        _root = json.loads(_st.read_text(encoding='utf-8')).get('source_root') if _st.exists() else None
    except ValueError:
        _root = None
    _chs = next((c for c in (plan or {}).get('chapters') or [] if c.get('chapter_id') == ast.get('chapter_id')), {})
    book['slide_maps'], slide_report = course_maps(manifest or {}, _root, _chs.get('source_ids'))
    # B13: interactive labs from the author's structured requests (deterministic build; static figure in the book)
    from .labs.integrate import build_chapter_labs
    idx_ = _anchor_index(manifest)
    from .labs.integrate import catalog_requests
    _kcs = [k for k in (plan or {}).get('competencies', []) if k['kc_id'] in set(ast.get('kc_ids') or [])]
    _reqs = list(ast.get('labs') or [])
    for _er in book.get('lab_requests') or []:          # B32: edition lab requests override / extend the author's
        _old = next((r for r in _reqs if r.get('lab_id') == _er.get('lab_id')), None)
        if _old is not None:
            _old.update({k: v for k, v in _er.items() if k != 'data'}); _old['data'] = {**(_old.get('data') or {}), **(_er.get('data') or {})}
        else:
            _reqs.append(dict(_er))
    _reqs += catalog_requests(_kcs, {r.get('model') for r in _reqs})
    from .labs.integrate import ROUTED_OUT as _routed_out
    labs_report, lab_blocks = build_chapter_labs(_reqs, art / 'Lernumgebung', book['meta']['course'],
                                                 lambda refs: _anchors(refs, idx_), ast.get('kc_ids') or [],
                                                 {k['kc_id']: re.sub(r'^[^:]*(?:/[^:]*)?:\s*', '', k['statement']).strip() for k in _kcs},
                                                 decimal=decimal_convention(ast))
    if lab_blocks:
        book['sections'].insert(max(0, len(book['sections']) - 1), {'title': 'Interaktive Labs', 'blocks': lab_blocks})
    rules = didactic_rules.check_book(book); nums = numeric_checks.check_book_numbers(book)
    sem = semantic_checks.check_book(book)
    write_json(pub / 'didactic_rules.json', rules); write_json(pub / 'numeric_checks.json', nums); write_json(pub / 'semantic_checks.json', sem)
    docs = typeset.publish_book(book, art)
    files = {Path(d['pdf']).name: d['pages'] for d in docs.values()}
    (art / 'kapitel.html').write_text(typeset._page(book['meta']['title'], typeset.textbook(book)[0]), encoding='utf-8')
    root = Path(assets_root) if assets_root else chapter_dir.parent.parent / 'plan'
    if ctx_p.exists() and root.is_dir():
        _ch = next((c for c in (plan or {}).get('chapters') or [] if c.get('chapter_id') == ast.get('chapter_id')), {})
        _ev_p = chapter_dir.parents[2] / 'visual_evidence.json' if len(chapter_dir.parents) > 2 else None
        try:
            _ev = json.loads(_ev_p.read_text(encoding='utf-8')) if _ev_p and _ev_p.exists() else None
        except ValueError:
            _ev = None
        n = publish_visual_sources(json.loads(ctx_p.read_text(encoding='utf-8')), manifest, root, art / '6_Quellenabbildungen.pdf',
                                   chapter_sources=_ch.get('source_ids'), evidence=_ev)
        if n: files['6_Quellenabbildungen.pdf'] = n + 1
    with (art / 'kompetenzmatrix.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(m['matrix'][0]) if m['matrix'] else ['kc_id']); w.writeheader(); w.writerows(m['matrix'])
    anki = {'cards': 0, 'card_source': book['card_source'], 'dropped_by_card_rules': book['cards_dropped']}
    if book['cards']:
        # card identity = course FOLDER name + chapter title + key; never the display title (course-title can change)
        from . import figures_svg as _fs
        _figs = {c['figure']: _fs.render(book['figures'][c['figure']]) for c in book['cards'] if c.get('figure') in book.get('figures', {})}
        rep = anki_v2.build_deck(book['cards'], f"Exam Mastery::{book['meta']['course']}::{book['meta']['title']}",
                                 anki_v2.slug(manifest.get('root_name') or book['meta']['course']), anki_v2.slug(book['meta']['title']), art / 'anki',
                                 figures=_figs, state_dir=chapter_dir.parent)
        anki.update(rep, package=rep['package'])
        if verify_anki:
            anki.update(anki_v2.verify_package(rep['package']))
    # B15: integrated learning environment (interactive textbook, embedded labs, practice, exam, progress, tutor briefing)
    from . import learn_app
    _built = list({r_['file']: dict(r_, title='MDP-Studio' if 'mdp-studio' in r_['file'] else r_['title']) for r_ in labs_report if r_['status'] == 'BUILT'}.values())
    learn_app.build(book, art / 'Lernumgebung', labs=_built,
                    materials=[[DOC_LABEL.get(n, n), '../' + n] for n in sorted(files) if n.endswith('.pdf')] + [['Lehrbuch als Webseite', '../kapitel.html']],
                    anki=('../anki/' + Path(anki['package']).name) if anki.get('package') else None, chapter_id=m['chapter_id'])
    report = {'schema': 'em-chapter-publish-v1', 'chapter_id': m['chapter_id'], 'content_origin': m['origin'],
              'products': {'files': files, 'textbook_blocks': len(m['blocks']), 'workbook_items': len(m['items']),
                           'solutions': sum(1 for i in m['items'] if i['solution']['answer']),
                           'mock_exam_items': len(mock_exam_items(m)), 'mock_exam_excluded_evidence_gap': [i['id'] for i in m['items'] if i['evidence_gap']],
                           'competency_rows': len(m['matrix']), 'open_issues': len(m['open_issues']), 'anki': anki},
              'files': sorted(str(p.relative_to(pub)) for p in art.rglob('*') if p.is_file()),
              'figures': {f['id']: f['status'] for f in m['figures']},
              'math_rendering': mr.report(),
              'knowledge_base': _kb_stamp(),
              'didactic_rules': {'version': didactic_rules.VERSION, 'fail': [r for r in rules if r['status'] == 'FAIL'][:30],
                                 'counts': {k: sum(1 for r in rules if r['status'] == k) for k in ('PASS', 'WARN', 'FAIL')}},
              'numeric_checks': {'fail': [r for r in nums if r['status'] == 'FAIL'][:30],
                                 'counts': {k: sum(1 for r in nums if r['status'] == k) for k in ('PASS', 'FAIL', 'DOCUMENTED')}},
              'semantic_checks': {'version': semantic_checks.VERSION, 'fail': [r for r in sem if r['status'] == 'FAIL'][:30],
                                  'review': [r for r in sem if r['status'] == 'REVIEW'][:30],
                                  'counts': {k: sum(1 for r in sem if r['status'] == k) for k in ('PASS', 'REVIEW', 'FAIL')}},
              'errata': errata_applied,
              'edition': edition_report, 'slide_numbers': slide_report,
              'labs': labs_report or 'NOT_GENERATED: no lab requested by the author role (only deterministic lab models are built)',
              'labs_routed_out': list(_routed_out),
              'documents': {k: {'pages': v['pages'], 'toc_unresolved': v['toc_unresolved'], 'internal_links': v.get('internal_links'),
                                'layout_lint': _layout_lint(art, k)} for k, v in docs.items()},
              'academic_status': m['academic_status'] or 'NOT_TESTED', 'source_verification': 'NONE_HUMAN'}
    if edition_report:
        write_json(pub / 'edition_report.json', edition_report)
    write_json(pub / 'book.json', book)             # B33: always kept; dossier and issue lifecycle judge the published book
    # B33: issue lifecycle (explicit, rechecked state per open issue) and exam-item mapping audit
    from . import issue_lifecycle as _il, exam_mapping as _xm
    try:
        life = _il.evaluate(chapter_dir, book, elements=_il.element_pages(manifest), gate_codes=_il.final_gate_codes(chapter_dir, plan))
        life['exam_mapping_audit'] = _xm.audit(json.loads((chapter_dir / 'content_ast.json').read_text(encoding='utf-8')).get('open_issues') or [],
                                               plan or {}, manifest or {}, chapter_dir.name) if plan and plan.get('chapters') else []
        write_json(pub / 'issue_lifecycle.json', life)
        report['issue_lifecycle'] = {k: life[k] for k in ('total', 'counts', 'gate', 'open_blockers')}
    except (ValueError, KeyError, StopIteration) as e:
        report['issue_lifecycle'] = {'gate': 'NOT_EVALUATED', 'error': f'{type(e).__name__}: {e}'}
    report['regression_guard'] = regression_guard(chapter_dir, report, book)
    write_json(pub / 'publish_report.json', report)
    return report


# ------------------------------------------------------------------ author-only preview (Stage 1)

PREVIEW_STATUS = 'AUTHOR_DRAFT_ONLY_NOT_REVIEWED'


def author_draft_checks(author, ctx, manifest):
    """Checks that are meaningful for an author draft alone (no exercises, solutions or semantic review yet)."""
    from .quality_gates import NUMBER, _numkey, INSTANCE_KINDS, FORBIDDEN_LABELS
    from .derivation_check import check_steps, declared_number_format
    by = {e['element_id']: e for e in manifest.get('elements', [])}
    fmt = declared_number_format(e.get('text') for e in ctx.get('source_elements') or [])
    allowed = set(ctx.get('allowed_source_refs') or [])
    produce = set(ctx.get('produce_kc_ids') or [])
    out = []
    def add(code, obj, status, detail): out.append({'check': code, 'object_id': obj, 'status': status, 'detail': detail})
    auto = {c['kc_id']: c['auto_scope'] for c in ctx.get('competencies') or [] if c.get('auto_scope')}
    for b in author.get('blocks', []):
        bid = b.get('block_id')
        for k in b.get('kc_ids') or []:
            if k in auto:
                hit = [r for r in b.get('source_refs') or [] if r in set(auto[k]['excluded_visual_element_ids'])]
                add('AUTO_SCOPE_TEXT_ONLY', bid, 'FAIL' if hit else 'PASS',
                    f'cites excluded visual(s) {hit} of text-only competency {k}' if hit else f'{k}: no excluded visual cited')
        from .examples import check_block
        for st, det in check_block(b, ctx.get('source_elements') or []):
            add('EXAMPLE_TOTAL_CONSISTENCY', bid, st, det)
        bad = [r for r in b.get('source_refs') or [] if r not in allowed]
        add('ANCHORS_ALLOWED', bid, 'FAIL' if bad else 'PASS', f'unknown/foreign anchors {bad}' if bad else 'all anchors in the chapter package')
        if b.get('provenance') == 'COURSE_SOURCE' and not b.get('source_refs'):
            add('COURSE_CLAIM_ANCHORED', bid, 'FAIL', 'COURSE_SOURCE block without source_refs')
        outside = [k for k in b.get('kc_ids') or [] if k not in produce]
        if outside: add('ONLY_PRODUCIBLE_KCS', bid, 'FAIL', f'writes for blocked/foreign KCs {outside}')
        if b.get('provenance') == 'COURSE_SOURCE':
            text = ' '.join(str(b.get(k) or '') for k in ('title', 'body', 'problem', 'result', 'interpretation')) + ' ' + \
                ' '.join(str(s.get('statement', '')) for s in b.get('steps') or [] if isinstance(s, dict))
            have = {_numkey(x) for r in b.get('source_refs') or [] for x in NUMBER.findall(by.get(r, {}).get('text') or '')}
            miss = sorted({x for x in NUMBER.findall(text) if len(_numkey(x)) >= 2 and _numkey(x) not in have})
            add('SOURCE_NUMBERS', bid, 'PASS' if not miss else 'NOT_TESTED' if b.get('kind') in INSTANCE_KINDS else 'FAIL',
                'all numbers in anchors' if not miss else 'numbers not in anchors: ' + ', '.join(miss[:12]))
        texts = [b.get('problem'), b.get('body')] + [x.get('statement') for x in b.get('steps') or [] if isinstance(x, dict)] + [b.get('result')]
        for r in check_steps([str(t) for t in texts if t], number_format=fmt):
            add('STEP_ARITHMETIC', bid, r['status'], r['detail'] + ' | ' + r['equation'])
            out[-1]['reason'] = r.get('reason')
        if b.get('claim_support_status') in FORBIDDEN_LABELS or b.get('provenance') in FORBIDDEN_LABELS:
            add('NO_SELF_CERTIFICATION', bid, 'FAIL', 'forbidden verification/release label')
    kinds = [b.get('kind') for b in author.get('blocks', [])]
    inferred = sum(1 for b in author.get('blocks', []) if b.get('provenance') == 'AUTHOR_INFERENCE')
    add('DEPTH_PROFILE', 'chapter', 'INFO', f"{len(kinds)} blocks; kinds {sorted(set(k for k in kinds if k))}; "
        f"{inferred} author-inference blocks (explanation beyond the slides); covered KCs "
        f"{len({k for b in author.get('blocks', []) for k in b.get('kc_ids') or []} & produce)}/{len(produce)}")
    return out


def publish_author_preview(chapter_dir, manifest, plan=None, errata=None):
    """Render the author draft alone (Stage 1). Clearly labelled; no workbook, solutions or Anki without review."""
    chapter_dir = Path(chapter_dir)
    author = json.loads((chapter_dir / 'chapter_author.json').read_text(encoding='utf-8'))
    ctx = json.loads((chapter_dir / 'chapter_context.json').read_text(encoding='utf-8'))
    pseudo = {'title': ctx.get('title', ''), 'course_id': ctx.get('course_id', ''), 'chapter_id': ctx.get('chapter_id', ''),
              'content_origin': 'MODEL_GENERATED_UNREVIEWED', 'status': PREVIEW_STATUS, 'academic_status': 'ACADEMIC_RELEASE_NOT_TESTED',
              'learning_objectives': author.get('learning_objectives', []), 'notation': author.get('notation', []),
              'blocks': author.get('blocks', []), 'assessments': [], 'solutions': [], 'figures': author.get('figures', []),
              'open_issues': [{**o, 'origin': 'author'} for o in author.get('open_issues', [])] +
                             [{'code': f['code'], 'severity': f['severity'], 'detail': f.get('detail', ''), 'origin': 'fidelity_gate'} for f in ctx.get('gate_findings', [])],
              'kc_coverage': [], 'kc_ids': ctx.get('produce_kc_ids', []), 'blocked_kc_ids': [],
              'exam_answers': author.get('exam_answers', []), 'sources': []}
    m = model(pseudo, manifest, plan)
    idx = _anchor_index(manifest)
    # reviewer errata (B6.7): shown at the block, never merged into the model text
    m['errata'] = [dict(e, anchors=_anchors(e.get('source_refs'), idx)) for e in (errata or [])]
    m['exam_rows'] = exam_answer_rows(m, ctx.get('exam_items', []))
    pub = chapter_dir / 'preview'; pub.mkdir(parents=True, exist_ok=True)
    mr = MathRenderer(pub / 'math')
    publish_html(m, pub / 'lehrbuch_vorschau.html', mr)
    publish_pdf(m, pub / 'lehrbuch_vorschau.pdf', mr)
    checks = author_draft_checks(author, ctx, manifest)
    for fg in m['figures']:
        lc = fg['label_check']
        checks.append({'check': 'FIGURE_LABELS_VERBATIM', 'object_id': fg['id'], 'status': lc['status'],
                       'detail': f"{lc['labels']} labels; not verbatim on the source page: {lc['missing'][:10]}"})
    missing = [r['item_id'] for r in m['exam_rows'] if r['status'] == 'MISSING_IN_AUTHOR_OUTPUT']
    checks.append({'check': 'EXAM_ANSWER_COVERAGE', 'object_id': 'chapter', 'status': 'FAIL' if missing else 'PASS',
                   'detail': f"{len(m['exam_rows']) - len(missing)}/{len(m['exam_rows'])} official questions with a concise answer or an "
                             f"explicit SOURCE_MISSING; missing: {missing[:30]}"})
    steps = [c for c in checks if c['check'] == 'STEP_ARITHMETIC']
    from collections import Counter
    arith = {'recognised_steps': len(steps), 'verified_pass': sum(c['status'] == 'PASS' for c in steps),
             'arithmetic_fail': sum(c['status'] == 'FAIL' for c in steps),
             'not_tested': sum(c['status'] == 'NOT_TESTED' for c in steps),
             'not_tested_reasons': dict(Counter(c.get('reason') for c in steps if c['status'] == 'NOT_TESTED'))}
    mrep = mr.report()
    checks.append({'check': 'MATH_RENDERING', 'object_id': 'chapter', 'status': mrep['status'],
                   'detail': f"{mrep['formulas_rendered']} rendered, {mrep['formulas_failed']} failed"})
    checks.append({'check': 'VERIFICATION_SCOPE', 'object_id': 'chapter', 'status': 'INFO',
                   'detail': 'STEP_ARITHMETIC checks written arithmetic only; set-up, units, meaning and subject-matter '
                             'correctness are NOT verified by any check in this report'})
    report = {'schema': 'em-author-preview-v1', 'status': PREVIEW_STATUS, 'chapter_id': m['chapter_id'],
              'checks': checks, 'failed': sum(c['status'] == 'FAIL' for c in checks), 'math_rendering': mr.report(),
              'arithmetic': arith,
              # never a green overall score while calculation steps are unchecked or anything failed
              'overall': 'FAILED_CHECKS' if any(c['status'] == 'FAIL' for c in checks) else
                         'INCOMPLETE_UNCHECKED_STEPS' if arith['not_tested'] else 'NO_FAILED_MACHINE_CHECKS_NOT_A_QUALITY_VERDICT',
              'missing_products': ['workbook', 'solutions', 'semantic_review', 'content_ast', 'anki', 'mock_exam'],
              'note': 'Stage-1 author draft only. Not a learning product; no exercises, solutions or model/human review yet.'}
    write_json(pub / 'preview_report.json', report)
    return report
