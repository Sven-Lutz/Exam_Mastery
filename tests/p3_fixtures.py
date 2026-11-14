"""P3 test helpers. EVERYTHING the 'model' says here is SYNTHETIC_FIXTURE text written for contract tests.
It is not academic content, not a recorded model output, and must never count as a quality or release signal.

- SyntheticChapterModel: offline fake provider (external=False) that answers chapter roles from the prompt context.
- variants inject defects so the gates can be shown to fire (empty proof, wrong matrix shapes, invented anchor, ...).
"""
import io, json, re
from pathlib import Path

SYNTHETIC = 'SYNTHETIC_FIXTURE: contract-test text, not academic content.'
WORDING = {
    'DERIVE': 'Leiten Sie für die Designmatrix mit neuen Daten die Bedingung her, die ein Minimierer erfüllen muss.',
    'PROVE': 'Beweisen Sie die Aussage für den angegebenen Fall vollständig.',
    'CALCULATE': 'Gegeben sind die Messpunkte (0,2), (1,3), (3,7). Berechnen Sie die gesuchte Größe.',
    'APPLY': 'Gegeben ist ein neuer Fall mit Wert 5. Wenden Sie das Verfahren darauf an.',
    'SUBSUME': 'Sachverhalt: A verkauft B ein Buch für 20 Euro; B zahlt nicht. Hat A gegen B einen Anspruch aus § 433 Abs. 2 BGB? Prüfen Sie gutachterlich.',
    'IMPLEMENT': 'Implementieren Sie das Verfahren als Funktion und geben Sie drei Testfälle an.',
    'DEFINE': 'Definieren Sie den Begriff präzise.',
    'EXPLAIN': 'Erklären Sie den Zusammenhang mit eigenen Worten.',
    'EVALUATE': 'Bewerten Sie die Annahmen kritisch.',
    'COMPARE': 'Vergleichen Sie die beiden Verfahren.',
    'INTERPRET': 'Interpretieren Sie das Ergebnis.',
    'RECALL': 'Nennen Sie den zentralen Begriff.',
}
EXPO = {'PROVE': 'PROOF', 'DERIVE': 'DERIVATION', 'SUBSUME': 'SUBSUMPTION', 'IMPLEMENT': 'ALGORITHM',
        'CALCULATE': 'WORKED_EXAMPLE', 'APPLY': 'WORKED_EXAMPLE', 'DEFINE': 'DEFINITION'}


def context_of(prompt, name='CHAPTER_CONTEXT'):
    m = re.search(name + r'_JSON_BEGIN\n(.*?)\n' + name + '_JSON_END', prompt, re.S)
    obj = json.loads(m.group(1))
    if isinstance(obj, dict) and obj.get('compact_schema'):   # B6.5: the fake model decodes the compact prompt form
        from exam_mastery.prompt_context import expand
        obj = expand(obj)
    return obj


def _steps(n=3):
    return [{'statement': f'{SYNTHETIC} Schritt {i}', 'justification': f'{SYNTHETIC} Begründung {i}'} for i in range(1, n + 1)]


def author(ctx, variant):
    blocks, figures, issues = [], [], []
    kcs = [k for k in ctx['competencies'] if k['kc_id'] in ctx['produce_kc_ids']]
    allowed = set(ctx['allowed_source_refs'])
    blocks.append({'block_id': 'b-motivation', 'kind': 'MOTIVATION', 'kc_ids': [k['kc_id'] for k in kcs], 'body': SYNTHETIC,
                   'source_refs': [], 'provenance': 'AUTHOR_INFERENCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'})
    for i, k in enumerate(kcs):
        refs = [a for a in k['source_anchor_ids'] if a in allowed] or ctx['allowed_source_refs'][:1]
        if variant == 'invented_anchor' and i == 0:
            refs = ['el-ffffffffffffffff']
        for op in k['operations']:
            kind = EXPO.get(op, 'REMARK')
            b = {'block_id': f'b-{i}-{op.lower()}', 'kind': kind, 'kc_ids': [k['kc_id']], 'title': SYNTHETIC, 'body': SYNTHETIC,
                 'steps': _steps(), 'source_refs': refs, 'provenance': 'COURSE_SOURCE',
                 'claim_support_status': 'SUPPORTED' if variant == 'false_verified' else 'PENDING_SEMANTIC_REVIEW'}
            if kind == 'PROOF' and variant == 'empty_proof':
                b['steps'] = []
            if kind == 'SUBSUMPTION':
                b['norm_refs'] = k['norm_refs'] or ['§ 433 Abs. 2 BGB']
                b['steps'] = [{**s, 'element': f'Tatbestandsmerkmal {j}'} for j, s in enumerate(b['steps'], 1)]
            if kind == 'WORKED_EXAMPLE':
                b.update(problem=SYNTHETIC, result=SYNTHETIC, interpretation=SYNTHETIC)
            if kind in ('DERIVATION', 'PROOF') and 'formal_mathematics' in ctx['domain_profile']['active_profiles']:
                b['shape_checks'] = {'symbols': {'A': [3, 2], 'x': [3 if variant == 'bad_shapes' else 2, 1], 'b': [3, 1]},
                                     'equations': [{'lhs': 'A^T A x', 'rhs': 'A^T b'}]}
            blocks.append(b)
        blocks.append({'block_id': f'b-{i}-example', 'kind': 'WORKED_EXAMPLE', 'kc_ids': [k['kc_id']], 'problem': SYNTHETIC,
                       'steps': _steps(), 'result': SYNTHETIC, 'interpretation': SYNTHETIC, 'source_refs': refs,
                       'provenance': 'AUTHOR_INFERENCE', 'claim_support_status': 'PENDING_SEMANTIC_REVIEW'})
    for j, v in enumerate(ctx['requirements']['visualizations']):
        if v.get('source_element_id') and v['kind'] in ('image', 'figure', 'diagram', 'chart'):
            ok = v['source_status'] == 'ok'
            fid = f'fig-{j}'
            figures.append({'figure_id': fid, 'purpose': SYNTHETIC, 'didactic_rationale': SYNTHETIC,
                            'source_element_id': v['source_element_id'],
                            'status': 'SOURCE_ASSET_REUSED' if ok else 'OPEN_NOT_GENERATED', 'linked_block_ids': ['b-motivation']})
            if not ok:
                issues.append({'issue_id': f'oi-fig-{j}', 'object_id': fid, 'code': 'FIGURE_NOT_GENERATED', 'detail': SYNTHETIC})
    notation = [{'notation_id': n['notation_id'], 'symbol': n['symbol'], 'meaning': n['authority_resolution'].get('preferred_meaning'),
                 'status': n['status']} for n in ctx['notation']]
    return {'learning_objectives': [{'kc_id': k['kc_id'], 'statement': k['statement'], 'operations': k['operations']} for k in kcs],
            'notation': notation, 'blocks': blocks, 'figures': figures, 'open_issues': issues}


def assessment(ctx, variant):
    items = []
    kcs = [k for k in ctx['competencies'] if k['kc_id'] in ctx['produce_kc_ids']]
    for i, k in enumerate(kcs):
        op = k['operations'][0]
        wording = WORDING[op]
        if variant == 'name_for_derive' and op == 'DERIVE':
            wording = 'Nennen Sie die Normalengleichung.'
        if variant == 'mc_for_prove' and op == 'PROVE':
            wording = 'Kreuzen Sie an: Welche der folgenden Aussagen ist bewiesen? [ ] a [ ] b'
        if variant == 'paragraph_for_subsume' and op == 'SUBSUME':
            wording = 'Nennen Sie die Anspruchsgrundlage § 433 Abs. 2 BGB.'
        items.append({'item_id': f'q-{i}-recall', 'kc_ids': [k['kc_id']], 'prompt': WORDING['RECALL'], 'format': 'open',
                      'difficulty': 'recall', 'required_operation': None, 'points': 1, 'transfer_relation': None,
                      'source_refs': [], 'solution_id': f's-{i}-recall', 'actual_operation_review': 'PENDING'})
        items.append({'item_id': f'q-{i}-main', 'kc_ids': [k['kc_id']], 'prompt': wording, 'format': 'open',
                      'difficulty': 'transfer' if i == 0 else 'standard', 'required_operation': op, 'points': 6,
                      'transfer_relation': 'NEW_PARAMETERS' if i == 0 else None, 'source_refs': [],
                      'refers_to_block_ids': ['b-motivation'], 'solution_id': f's-{i}-main', 'actual_operation_review': 'PENDING'})
    return {'assessments': items}


def solutions(draft, variant):
    out = []
    for a in draft['assessments']:
        rubric = [{'criterion': SYNTHETIC + ' Ansatz', 'points': a['points'] / 2}, {'criterion': SYNTHETIC + ' Ergebnis', 'points': a['points'] / 2}]
        if variant == 'no_rubric':
            rubric = []
        out.append({'solution_id': a['solution_id'], 'item_id': a['item_id'], 'steps': _steps(), 'answer': SYNTHETIC,
                    'alternatives': [SYNTHETIC], 'hint_ladder': [SYNTHETIC + ' Hinweis 1', SYNTHETIC + ' Hinweis 2'],
                    'rubric': rubric, 'typical_errors': [SYNTHETIC]})
    return {'solutions': out}


def review(ctx, draft):
    decisions = []
    for k in ctx['competencies']:
        if k['kc_id'] in ctx['produce_kc_ids'] and k['source_anchor_ids']:
            decisions.append({'kind': 'operation', 'subject_id': k['kc_id'], 'value': k['operations'], 'rationale': SYNTHETIC,
                              'evidence_element_ids': k['source_anchor_ids'][:1], 'decided_by': 'model'})
    return {'schema': 'em-semantic-decisions-v1', 'decisions': decisions,
            'claim_reviews': [{'block_id': b['block_id'], 'verdict': 'SUPPORTED', 'rationale': SYNTHETIC, 'element_ids': b['source_refs']}
                              for b in draft['blocks'] if b.get('provenance') == 'COURSE_SOURCE'],
            'findings': []}


def answer(role, prompt, variant=None):
    ctx = context_of(prompt); draft = context_of(prompt, 'CURRENT_DRAFT')
    if role == 'chapter_author':
        return author(ctx, variant)
    if role == 'chapter_assessment':
        return assessment(ctx, variant)
    if role == 'chapter_solutions':
        return solutions(draft, variant)
    if role == 'chapter_semantic_review':
        return review(ctx, draft)
    if role == 'chapter_risk_review':
        return {'verdict': 'NEEDS_REVIEW', 'findings': [{'severity': 'info', 'description': SYNTHETIC, 'object_id': None}]}
    raise AssertionError('unexpected role ' + role)


class SyntheticChapterModel:
    """Offline fake: never starts a process, never touches the network."""
    name = 'synthetic-fixture'; external = False; synthetic = True; budget = None

    def __init__(self, variant=None):
        self.variant = variant; self.calls = []

    def fingerprint(self):
        return {'name': self.name, 'model': 'SYNTHETIC_FIXTURE', 'variant': self.variant, 'protocol': 4}

    def ask(self, role, prompt, run_dir, images=None):
        self.calls.append(role)
        return answer(role, prompt, self.variant)


def codex_answering(variant=None):
    """Fake providers.execute for Provider('codex'): answers by role, reports usage (for budget accounting)."""
    def fake(cmd, prompt, cwd, timeout):
        role = re.search(r'ROLE: (chapter author|assessment designer|independent solution author|semantic source reviewer|domain risk reviewer)', prompt).group(1)
        r = {'chapter author': 'chapter_author', 'assessment designer': 'chapter_assessment', 'independent solution author': 'chapter_solutions',
             'semantic source reviewer': 'chapter_semantic_review', 'domain risk reviewer': 'chapter_risk_review'}[role]
        Path(cmd[cmd.index('-o') + 1]).write_text(json.dumps(answer(r, prompt, variant)))
        return 0, json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': 100, 'cached_input_tokens': 0, 'output_tokens': 50}}), '', False
    return fake


# ---------------------------------------------------------------- extra course builders (random roots via caller)

def merge_course(root):
    root = Path(root); (root / 'a').mkdir(); (root / 'b').mkdir()
    (root / 'a' / 'skript_eigen.md').write_text('# Kapitel 3: Eigenwerte und Eigenvektoren\n\n## Lernziele\n'
                                               '- Berechnen Sie Eigenwerte einer gegebenen 2x2-Matrix.\n\n'
                                               'Ein Eigenvektor $v$ einer Matrix erfüllt $Av = \\lambda v$ mit Eigenwert lambda.\n', encoding='utf-8')
    (root / 'b' / 'folien_eigen.md').write_text('# Folien: Eigenwerte und Eigenvektoren\n\nCharakteristisches Polynom det(A - lambda I) = 0 '
                                               'liefert die Eigenwerte der Matrix; Eigenvektor aus dem Kern.\n', encoding='utf-8')
    (root / 'b' / 'symm.md').write_text('# Eigenwerte symmetrischer Matrizen\n\nSpektralsatz: symmetrische Matrizen haben reelle '
                                       'Eigenwerte und eine Orthonormalbasis aus Eigenvektoren.\n', encoding='utf-8')
    (root / 'klausur.md').write_text('# Klausur\n\nAufgabe 1\nGegeben ist die Matrix A = [[2,1],[1,2]]. Berechnen Sie die Eigenwerte der Matrix. (4 P)\n', encoding='utf-8')
    return root


def order_course(root, mode):
    root = Path(root)
    a = '# {n}Lineare Ausgleichsrechnung\n\nDefinition (Residuum). Das Residuum ist r = b - Ax der Abweichungen.\n\n## Lernziele\n- Berechnen Sie eine Ausgleichsgerade.\n'
    q = '# {n}QR-Zerlegung\n\n{pre}## Lernziele\n- Erklären Sie die QR-Zerlegung einer Matrix.\n'
    if mode == 'numbered':
        (root / 'z_01_aaa.md').write_text(a.format(n='Kapitel 1: '), encoding='utf-8')
        (root / 'a_99_zzz.md').write_text(q.format(n='Kapitel 2: ', pre=''), encoding='utf-8')
    elif mode == 'toc':
        (root / 'z_first.md').write_text(a.format(n=''), encoding='utf-8')
        (root / 'a_second.md').write_text(q.format(n='', pre=''), encoding='utf-8')
        (root / 'm_syllabus.md').write_text('# Inhalt\n\n- Lineare Ausgleichsrechnung\n- QR-Zerlegung\n', encoding='utf-8')
    elif mode == 'prereq':
        (root / 'z_first.md').write_text(a.format(n=''), encoding='utf-8')
        (root / 'a_second.md').write_text(q.format(n='', pre='Voraussetzungen: Residuum\n\n'), encoding='utf-8')
    else:  # nothing but file names
        (root / 'z_first.md').write_text('# Thema Alpha\n\nText über Alpha und seine Eigenschaften im Detail.\n', encoding='utf-8')
        (root / 'a_second.md').write_text('# Thema Beta\n\nText über Beta und dessen Anwendungen in der Praxis.\n', encoding='utf-8')
    return root


def blocker_course(root, kind):
    root = Path(root)
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    if kind == 'scan':
        cv = canvas.Canvas(str(root / 'Vorlesung_Thermo.pdf')); t = cv.beginText(40, 760)
        for ln in ['Vorlesung Thermodynamik', 'Lernziele:', '- Leiten Sie den Wirkungsgrad des Carnot-Prozesses her.']:
            t.textLine(ln)
        cv.drawText(t); cv.showPage()
        b = io.BytesIO(); Image.new('RGB', (200, 200), 'gray').save(b, 'PNG')
        cv.drawImage(ImageReader(io.BytesIO(b.getvalue())), 50, 400, 200, 200); cv.showPage(); cv.save()
    elif kind == 'formula':
        cv = canvas.Canvas(str(root / 'Vorlesung_Regression.pdf')); y = 780
        for ln in ['Vorlesung Regression', 'Lernziele: Leiten Sie die Kleinste-Quadrate-Schätzung her.', 'Σ (y_i − a − b x_i)^2 → min',
                   'Die Schätzung minimiert die Summe der quadrierten Residuen der Regression.']:
            cv.drawString(40, y, ln); y -= 22
        cv.showPage(); cv.save()
    elif kind == 'required_online':
        (root / 'vorlesung.md').write_text('# Spieltheorie\n\n## Lernziele\n- Erklären Sie das Nash-Gleichgewicht.\n\n'
                                           'Pflichtlektüre: https://example.org/nash1950.pdf\n', encoding='utf-8')
    return root


def pilot_gate_cleared_for_p0_mechanics_test():
    """TEST-ONLY: older P0 tests check budget/resume/signal mechanics with external fakes on fixture chapters that are not
    pilot-eligible. The B6.1 production preflight would (correctly) refuse them; this patch isolates the mechanics under
    test. The preflight itself is tested in test_b6_1_chapter_page_gate.py without this patch."""
    from unittest.mock import patch
    def cleared(plan, gates, chapter_ids):
        return {'schema': 'em-production-preflight-v1', 'result': 'CLEARED_EXPERIMENTAL_SCOPE',
                'chapters': {c: {'status': 'PILOT_SCOPE_CLEARED_EXPERIMENTAL', 'open': [], 'cleared': []} for c in chapter_ids},
                'note': 'TEST PATCH'}
    return patch('exam_mastery.chapters.production_preflight', side_effect=cleared)


def signed(data, plan):
    """TEST-ONLY (B6.2): fill approved_content_sha256 / verified_content_sha256 of every synthetic approval with the
    current content hash, as a human would after reading. Explicit tamper tests live in test_b6_2_approval_integrity."""
    import copy
    from exam_mastery import review_decisions as D
    tup = isinstance(data, tuple); d = copy.deepcopy(data[0] if tup else data); h = D.content_hashes(d, plan)
    def fill(entry, sha, bundle=False):
        ap = entry.get('pilot_scope_approval')
        if isinstance(ap, dict) and ap.get('approved') is True and 'approved_content_sha256' not in ap:
            ap['approved_content_sha256'] = sha
        hv = entry.get('source_claim_human_verification')
        if not bundle and isinstance(hv, dict) and hv.get('verified') is True and 'verified_content_sha256' not in hv:
            hv['verified_content_sha256'] = sha
    for x in d.get('decisions', []):
        if isinstance(x, dict): fill(x, h['decisions'].get(x.get('decision_id')))
    for b in d.get('bundle_approvals') or []:
        if isinstance(b, dict): fill(b, h['bundles'].get(b.get('bundle_id')), True)
    for r in d.get('page_reviews') or []:
        if isinstance(r, dict): fill(r, h['page_reviews'].get(r.get('review_id')))
    return (d, data[1]) if tup else d


def evaluate_signed(data, manifest, plan, *a, **k):
    from exam_mastery import review_decisions as D
    return D.evaluate(signed(data, plan), manifest, plan, *a, **k)


# B6.4: the external chapter path needs an explicit model listed in codex's local catalog.
# Tests point CODEX_HOME at a temporary fake catalog; codex itself is never executed (execute is patched).
FAKE_MODEL = 'fake-offline-model'
_FAKE_HOME = {}

def install_fake_codex_home(slugs=(FAKE_MODEL,)):
    import os, json as _json, tempfile as _tf
    d = _tf.mkdtemp(prefix='fake-codex-home-')
    with open(os.path.join(d, 'models_cache.json'), 'w') as f:
        _json.dump({'models': [{'slug': s} for s in slugs]}, f)
    _FAKE_HOME['prev'] = os.environ.get('CODEX_HOME'); _FAKE_HOME['dir'] = d
    os.environ['CODEX_HOME'] = d
    return d

def remove_fake_codex_home():
    import os, shutil as _sh
    prev = _FAKE_HOME.pop('prev', None)
    if prev is None: os.environ.pop('CODEX_HOME', None)
    else: os.environ['CODEX_HOME'] = prev
    _sh.rmtree(_FAKE_HOME.pop('dir', ''), ignore_errors=True)
