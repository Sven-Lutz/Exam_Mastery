"""Chapter integration of labs (B13). The author role proposes labs as structured requests with data taken from the
sources; the engine builds them deterministically. A request for a model the engine does not have is reported as
NOT_AVAILABLE: no code is generated for it and nothing is improvised.

Request (author output, list "labs"):
{"model": "cashflow"|"risk"|"mlp"|"van_westendorp"|"mdp"|"sequence"|"attention"|"cap_table"|"legal_check", "lab_id": "topic/name", "title": "...", "kc_ids": [...], "source_refs": [...],
 "data": {...model data...}}
"""
import json
import re
from pathlib import Path

from . import build as B

DATA = {
    'cashflow': {'orders', 'delay', 'cost', 'invest'},
    'risk': set(),
    'mlp': set(),
    'van_westendorp': set(),
    'mdp': {'states', 'transitions', 'gamma', 'policy'},
    'mdp_grid': {'cols', 'rows', 'terminals', 'gamma'},
    # generic labs: every data key is optional; data={} builds the engine's documented default example
    'sequence': set(),      # {"expr": "(-1)^n/n" | "rec": "sqrt(2+a)", "a1": 1, "limit": 0, "eps": 0.1, "horizon": 200, "label", "examples": [...]}
    'attention': set(),     # {"tokens": [...], "X": n×d, "heads": [{"Wq","Wk","Wv"}] (1 or 2), "query": i}
    'cap_table': set(),     # {"founders": [{"name","shares"}], "rounds": [{"name","pre_money","investment","pool_pct","pool_mode"}], "exit"}
    'legal_check': set(),   # {"scheme","norm","question","rechtsfolge","negative","case": {"title","facts","self_designed"}, "elements": [...], "transfer"}
}
GENERIC = ('sequence', 'attention', 'cap_table', 'legal_check')

# B14: engine lab catalogue. A lab is attached without any model call when a competency of the chapter names the
# method explicitly; its kc_ids and source anchors are that competency's own (from the course's source inventory).
CATALOG = {'van_westendorp': {'pattern': re.compile(r'van[\s-]*westendorp|price\s+sensitivity\s+meter', re.I), 'lab_id': 'pricing/van-westendorp',
                              'title': 'Van Westendorp: Wo liegt der akzeptable Preisbereich?'},
           # conservative: bare "Folge(n)" (also "consequences"), "attention" (AIDA), "Bewertung" and "Neuheit" are too broad alone
           'sequence': {'pattern': re.compile(r'Konvergenz|konvergen|Grenzwert|Cauchy|convergen|\b(Zahlen|Teil)folgen?\b|\bFolgen?\s+(reeller|komplexer|von\s+Zahlen|a_?n|\(a)|\b(sub)?sequences?\s+of\s+(real|numbers)|limit\s+of\s+a\s+sequence|\bepsilon[\s-]+N\b|ε[\s-]*N', re.I),
                        'lab_id': 'analysis/folgen-epsilon', 'title': 'Folgen: Ab welchem N bleibt die Folge im ε-Band?', 'subjects': ('analysis', 'mathematics')},
           'attention': {'pattern': re.compile(r'self[\s-]?attention|multi[\s-]?head|scaled\s+dot[\s-]product|attention[\s-](mechanism|weights?|heads?|layer)|Aufmerksamkeitsmechanismus|Attention[\s-]Mechanismus|\bTransformer[\s-]?(Architektur|Modell|model|architecture|encoder|decoder|Encoder|Decoder)', re.I),
                         'lab_id': 'nlp/self-attention', 'title': 'Self-Attention: Worauf achtet ein Token?', 'subjects': ('nlp', 'machine_learning', 'reinforcement_learning')},
           'cap_table': {'pattern': re.compile(r'pre[\s-]?money|post[\s-]?money|cap[\s-]?table|Verwässerung|dilution|Finanzierungsrunde|funding\s+round|Beteiligungsquote|liquidation\s+preference|Liquidationspräferenz|(Start-?up|Venture)[\w\s-]{0,20}Bewertung|valuation\s+of\s+(a\s+)?start-?ups?', re.I),
                         'lab_id': 'finance/cap-table', 'title': 'Cap Table: Was bleibt den Gründern nach zwei Runden?'},
           'legal_check': {'pattern': re.compile(r'Patentfähigkeit|Patentierbarkeit|patentab|erfinderische[nr]?\s+Tätigkeit|inventive\s+step|Prüfungsschema|Neuheit\W.{0,40}(Patent|Erfindung|Stand\s+der\s+Technik)', re.I),
                           'lab_id': 'recht/patentfaehigkeit', 'title': 'Patentfähigkeit: Merkmal für Merkmal prüfen'}}


def chapter_subjects(competencies):
    """B32: subjects of a chapter from the verified subject registers (knowledge/subject/*.json keywords); empty = unknown."""
    kb = Path(__file__).resolve().parent.parent / 'knowledge' / 'subject'
    text = ' '.join(str(k.get('statement') or '') + ' ' + str(k.get('topic_text') or '') for k in competencies).lower()
    out = set()
    for f in sorted(kb.glob('*.json')):
        d = json.loads(f.read_text(encoding='utf-8'))
        if sum(1 for w in d.get('keywords', []) if w.lower() in text) >= 2:
            out.add(d['subject'])
    return out


ROUTED_OUT = []


def catalog_requests(competencies, requested_models=()):
    """Catalogue labs whose method a competency names. B32 subject routing: a lab that declares its subjects is not
    attached to a chapter whose recognised subject is different (an RL 'convergence' slide is not a sequence chapter)."""
    out = []; subj = chapter_subjects(competencies); ROUTED_OUT.clear()
    for model, c in CATALOG.items():
        if model in requested_models:
            continue
        if subj and c.get('subjects') and not subj & set(c['subjects']):
            ROUTED_OUT.append({'model': model, 'lab_id': c['lab_id'], 'reason': f'chapter subject {sorted(subj)} not in lab subjects {list(c["subjects"])}'})
            continue
        hit = [k for k in competencies if c['pattern'].search(k.get('statement') or '') or c['pattern'].search(k.get('topic_text') or '')]
        hit = [k for k in hit if k.get('source_anchor_ids')]
        if hit:
            out.append({'model': model, 'lab_id': c['lab_id'], 'title': c['title'], 'kc_ids': [k['kc_id'] for k in hit],
                        'source_refs': list(dict.fromkeys(a for k in hit for a in k.get('source_anchor_ids') or [])), 'data': {}, 'origin': 'engine_catalog'})
    return out


def build_spec(req, course, sources_label):
    m, d = req.get('model'), req.get('data') or {}
    if m not in DATA:
        raise B.LabError(f'no deterministic model {m!r}')
    miss = DATA[m] - set(d)
    if miss:
        raise B.LabError(f'missing data {sorted(miss)}')
    if m == 'cashflow':
        num = lambda xs: [float(x) for x in xs]
        return B.cashflow_spec(req['lab_id'], req['title'], req['kc_ids'], sources_label, num(d['orders']), int(d['delay']), num(d['cost']),
                               num(d['invest']), float(d.get('start_cash', 0)), d.get('unit', 'k€'), course, d.get('transfer_delay'))
    if m == 'mdp':
        return B.mdp_spec(req['lab_id'], req['title'], req['kc_ids'], sources_label, d, course, d.get('unit', ''))
    if m in GENERIC:
        return getattr(B, f'{m}_spec')(req['lab_id'], req['title'], req['kc_ids'], sources_label, d, course)
    if m == 'risk':
        return B.risk_spec(req['lab_id'], req['title'], req['kc_ids'], sources_label, course)
    if m == 'van_westendorp':
        if not req.get('kc_ids') or not req.get('source_refs'):
            raise B.LabError('PSM requires course competencies and method source references')
        if d:
            raise B.LabError('reference PSM uses only declared synthetic defaults')
        return B.vw_spec(req['lab_id'], req['title'], req['kc_ids'], sources_label, course)
    s = B.mlp_spec(req['lab_id'], int(d.get('seed', 7)), tuple(d.get('x', (0.5, -1.0))), float(d.get('target', 0.8)), float(d.get('lr', 0.5)), course)
    s['kc_ids'] = req['kc_ids'] or s['kc_ids']
    return s


def build_chapter_labs(requests, out_dir, course, anchor_label, allowed_kcs, kc_labels=None, decimal=','):
    """Returns (report, lab_blocks). lab_blocks are book-model blocks of type 'lab' (static SVG + link).
    `decimal` is the book's own decimal separator, so lab and book never disagree (0,70 vs 0.7).
    The separator applies only to this chapter's labs: the module default is restored afterwards, so a later
    chapter (or any other lab rendered in the same process) never inherits it."""
    previous = B.DECIMAL['sep']
    B.DECIMAL['sep'] = '.' if decimal == '.' else ','
    try:
        return _build_chapter_labs(requests, out_dir, course, anchor_label, allowed_kcs, kc_labels)
    finally:
        B.DECIMAL['sep'] = previous


def _studio(reqs, out, course, anchor_label, allowed_kcs, report, blocks):
    """B32: all MDP requests of a chapter become scenarios of ONE MDP Studio page (graph and grid models)."""
    from . import mdp_studio as MS
    from .. import figure_kit
    scen = []
    for req in reqs:
        d = dict(req.get('data') or {})
        try:
            if not set(req.get('kc_ids') or []) <= set(allowed_kcs):
                raise MS.StudioError('lab names competencies outside this chapter')
            sc = {'id': req['lab_id'], 'title': d.pop('studio_title', None) or req.get('title', req['lab_id']), 'kc_ids': req.get('kc_ids') or [],
                  'kind': 'grid' if req.get('model') == 'mdp_grid' else 'graph', **d}
            sc.pop('focus', None)
            MS.validate(sc); sc['sources'] = anchor_label(req.get('source_refs') or []) if req.get('source_refs') else 'Eigenes Modell zur Veranschaulichung'
            scen.append(sc)
            report.append({'lab_id': req['lab_id'], 'status': 'BUILT', 'origin': req.get('origin', 'author_request'), 'title': sc['title'],
                           'file': 'Lernumgebung/labs/mdp-studio.html', 'kc_ids': sc['kc_ids'], 'model': 'mdp_studio:' + sc['kind'],
                           'golden': MS.golden(sc), 'challenges': len(sc.get('challenges') or [])})
        except (MS.StudioError, KeyError, TypeError, ValueError) as e:
            report.append({'lab_id': req.get('lab_id', '?'), 'status': 'NOT_AVAILABLE', 'reason': str(e)})
    if not scen:
        return
    (out / 'labs').mkdir(parents=True, exist_ok=True)
    (out / 'labs' / 'mdp-studio.html').write_text(MS.page(scen, 'MDP-Studio: optimal planen', course, mathjax='../../assets/tex-svg-full.js'), encoding='utf-8')
    g = next((x for x in scen if x['kind'] == 'graph' and x.get('pos')), None)
    if g:
        nodes = [{'id': s_, 'label': (g.get('labels') or {}).get(s_, s_), 'x': g['pos'][s_][0], 'y': g['pos'][s_][1]} for s_ in g['states'] if s_ in g['pos']]
        edges = []
        for t in g['transitions']:
            ap = (g.get('apos') or {}).get(f"{t['s']}|{t['a']}")
            if not ap:
                continue
            aid = f"{t['s']}|{t['a']}"; nodes.append({'id': aid, 'label': f"{t['a']} · r={t['r']:g}", 'x': ap[0], 'y': ap[1], 'kind': 'action',
                                                      'ly': 20 if ap[1] > g['pos'][t['s']][1] else -13})
            edges.append({'from': t['s'], 'to': aid, 'kind': 'choice'})
            edges += [{'from': aid, 'to': n, 'kind': 'transition', 'label': f'{float(pv):g}', 'bend': 18} for n, pv in t['next'].items()]
        svg = figure_kit.state_graph({'nodes': nodes, 'edges': edges, 'w': g.get('w', 580), 'h': g.get('h', 360), 'title': g['title']})
        blocks.append({'type': 'lab', 'title': 'MDP-Studio: ' + ', '.join(x['title'] for x in scen), 'svg': svg, 'href': 'Lernumgebung/labs/mdp-studio.html',
                       'kc_ids': sorted({k for x in scen for k in x.get('kc_ids', [])}),
                       'caption': 'Policy-Explorer, Wertiteration und Policy Iteration Schritt für Schritt, Diskont-Regime und Vorhersage-Aufgaben.',
                       'assumptions': ['endliche Zustände und Aktionen', '0 ≤ γ < 1', 'Übergänge wie im jeweiligen Modell'], 'prov': 'interpretation',
                       'src': '; '.join(dict.fromkeys(str(x['sources']) for x in scen))})


def _build_chapter_labs(requests, out_dir, course, anchor_label, allowed_kcs, kc_labels=None):
    out = Path(out_dir); report, blocks = [], []
    mdp = [r for r in requests or [] if r.get('model') in ('mdp', 'mdp_grid')]
    if mdp:
        _studio(mdp, out, course, anchor_label, allowed_kcs, report, blocks)
    for req in [r for r in requests or [] if r.get('model') not in ('mdp', 'mdp_grid')]:
        rid = req.get('lab_id', '?')
        try:
            if not set(req.get('kc_ids') or []) <= set(allowed_kcs):
                raise B.LabError('lab names competencies outside this chapter')
            spec = build_spec(req, course, [anchor_label(req.get('source_refs') or [])] if req.get('source_refs') else ['Eigenes Modell zur Veranschaulichung'])
            if kc_labels:
                spec['kc_labels'] = {k: kc_labels[k] for k in spec['kc_ids'] if k in kc_labels}
            path = B.render(spec, out / 'labs', fonts='../../assets/fonts', back_label='Zur Lernumgebung')
            rel = f'Lernumgebung/labs/{path.name}'
            report.append({'lab_id': rid, 'status': 'BUILT', 'origin': req.get('origin', 'author_request'), 'title': spec['title'], 'file': rel, 'kc_ids': spec['kc_ids'], 'model': spec['model']['kind']})
            blocks.append({'type': 'lab', 'title': spec['title'], 'svg': B.static_svg(spec), 'href': rel, 'kc_ids': spec['kc_ids'],
                           'caption': spec['objective'], 'assumptions': spec['assumptions'], 'prov': 'interpretation',
                           'src': '; '.join(spec['sources'])})
        except (B.LabError, KeyError, TypeError, ValueError) as e:
            report.append({'lab_id': rid, 'status': 'NOT_AVAILABLE', 'reason': str(e)})
    (out).mkdir(parents=True, exist_ok=True)
    (out / 'labs_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return report, blocks
