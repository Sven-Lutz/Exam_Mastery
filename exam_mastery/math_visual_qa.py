"""Executed artifact-level mathematics/figure checks; never a scientific self-approval."""
from pathlib import Path
import json,re,math,hashlib
from .common import ContractError,sha_file
from .math_publishing import validate_registry,prepare,symbolic,TOKEN

def check_lab_scope(interaction,records):
    """Check a declared finite example set against the complete slider domain.
    This is a bounded contract check, not automatic interpretation of all TeX/prose.
    """
    if interaction.get('kind')!='numeric':return
    record=next((r for r in records if r.get('id')==interaction.get('math_id')),None)
    if record is None:return  # Existing canonical identity gate reports this.
    scope=record.get('example_scope')
    if scope is None:
        if re.search(r'\\in\s*\\\{',record.get('tex','')):raise ContractError('Finite mathematical membership in a numeric lab requires explicit example_scope')
        return  # Legacy formulas without finite membership make no added scope claim.
    n=interaction['numeric'];values=scope.get('inputs',[])
    if scope.get('kind') not in ('selected','exhaustive') or not values or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):raise ContractError('Invalid finite example scope')
    if scope.get('variable')!=n['variable'] or any(not n['min']<=v<=n['max'] for v in values):raise ContractError('Example variable/range disagrees with lab')
    steps=(n['max']-n['min'])/n['step']
    if steps>100000:raise ContractError('Example domain too large to enumerate safely')
    reachable=[n['min']+i*n['step'] for i in range(int(steps+1e-8)+1)]
    absent=[v for v in reachable if not any(math.isclose(v,x,rel_tol=0,abs_tol=1e-8) for x in values)]
    if scope['kind']=='exhaustive' and absent:raise ContractError('Finite examples omit admissible lab inputs; not an exhaustive domain')
    if scope['kind']=='selected':
        probe=scope.get('non_example_probe',{})
        v=probe.get('input')
        if type(v) not in (int,float) or not n['min']<v<n['max'] or any(math.isclose(v,x,abs_tol=1e-8) for x in values) or not any(math.isclose(v,x,abs_tol=1e-8) for x in reachable):raise ContractError('Selected examples require a reachable non-example interior probe')
        from .validate import evaluate_numeric
        expected=evaluate_numeric(n['expression'],{**n['constants'],n['variable']:v})
        if type(probe.get('expected')) not in (int,float) or not math.isclose(expected,probe['expected'],rel_tol=1e-8,abs_tol=1e-8):raise ContractError('Non-example probe has incorrect value')

def verify(out):
    import sympy as sp
    out=Path(out);author=json.loads((out/'author.json').read_text());records=author.get('mathematics',[])
    if not records:return {'status':'NOT_TESTED','scope':'Legacy/no canonical mathematical contract; no claim of advanced mathematical validation'}
    validate_registry(records)
    registry=prepare(records,out/'artifacts/math')
    # Every formula is derived once and has the same content hash in all channels.
    carddir=out/'artifacts/anki';assets=[]
    for ident,a in registry.items():
        counterpart=carddir/'media'/Path(a['svg']).name
        if not counterpart.exists() or sha_file(counterpart)!=a['sha256']:raise ContractError('PDF/web/Anki canonical formula asset mismatch')
        png_counterpart=carddir/'media'/Path(a['png']).name
        if not png_counterpart.exists() or sha_file(png_counterpart)!=a['png_sha256']:raise ContractError('Anki raster differs from canonical mathematical image')
        assets.append({'id':ident,'tex':a['tex'],'svg_sha256':a['sha256'],'checks':a['checks']})
    interaction=json.loads((out/'interaction.json').read_text())
    # Aggregate products have per-unit labs. Check each real lab against its canonical expression.
    interactions=[interaction]
    model=json.loads((out/'learning_model.json').read_text())
    interactions += [i for u in model.get('units',[]) for i in u.get('interactions',[])]
    for inter in interactions:
        if inter.get('kind')!='numeric':continue
        if not inter.get('math_id') or inter['math_id'] not in registry:raise ContractError('Numeric lab lacks canonical mathematical link')
        check_lab_scope(inter,records)
        r=registry[inter['math_id']]['record'];symbols={s['name']:sp.Symbol(s['name'],**s.get('properties',{})) for s in r['symbols']}
        if sp.simplify(symbolic(r['expression'],symbols)-symbolic(inter['numeric']['expression'],symbols))!=0:raise ContractError('Lab and canonical formula disagree')
    figures=json.loads((out/'figure_register.json').read_text())
    figure_ids={f['id'] for f in figures if f.get('id')}
    for card in json.loads((out/'cards.json').read_text())['cards']:
        if not set(card.get('figure_ids',[]))<=figure_ids:raise ContractError('Anki card references an unrendered scientific figure')
    for figure in figures:
        if not Path(figure['path']).is_file():raise ContractError('Specified figure was not rendered')
        if figure.get('svg_sha256') and sha_file(Path(figure['path']))!=figure['svg_sha256']:raise ContractError('Figure bytes differ from QA record')
    for doc in (out/'artifacts/web/index.html',carddir/'anki_import.tsv'):
        if 'data-solution-figure=' in doc.read_text():raise ContractError('Unrendered solution figure placeholder')
        if TOKEN.search(doc.read_text()):raise ContractError('Unresolved mathematical token in published product')
    import pymupdf
    overlaps=[]
    with pymupdf.open(out/'artifacts/learning_package.pdf') as doc:
        for number,page in enumerate(doc,1):
            images=[pymupdf.Rect(info['bbox']) for info in page.get_image_info()]
            images += [pymupdf.Rect(d['rect']) for d in page.get_drawings() if d['type'] in ('f','fs') and 1<d['rect'].width<60 and 1<d['rect'].height<30 and any(item[0]!='re' for item in d['items'])]
            texts=[pymupdf.Rect(span['bbox']) for block in page.get_text('dict')['blocks'] if block['type']==0 for line in block['lines'] for span in line['spans']]
            for image in images:
                for text in texts:
                    intersection=image&text
                    if not intersection.is_empty and intersection.width>1 and intersection.height>1:overlaps.append(number)
    if overlaps:raise ContractError('PDF mathematical image/text overlap on pages '+str(sorted(set(overlaps))))
    return {'status':'PASS','formulas':assets,'figures':len(figures),'scope':'Canonical asset identity, declared symbol contracts, bounded algebra/numerics/dimensions, actual SVG existence; not proof or external source validation'}
