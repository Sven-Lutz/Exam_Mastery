"""Deterministic didactic figures and separate book/task/solution products."""
from pathlib import Path
import html,json,textwrap
from .common import write_json,ContractError

def check_visuals(plan,manifest):
    valid={c['locator'] for c in manifest['chunks']}
    if not isinstance(plan.get('visuals'),list):raise ContractError('Learning plan must include visuals (possibly empty with explanation)')
    for visual in plan['visuals']:
        if visual.get('kind') not in ('flow','table'):raise ContractError('Only safe flow/table figure specifications supported')
        if not visual.get('source_refs') or not set(visual['source_refs'])<=valid:raise ContractError('Figure requires exact source provenance')
        if not visual.get('title') or not visual.get('alt_text'):raise ContractError('Figure needs title and accessible description')
        if visual['kind']=='flow':
            if not 2<=len(visual.get('nodes',[]))<=8:raise ContractError('Flow must contain 2..8 complete labels')
            for a,b in visual.get('edges',[]):
                if not 0<=a<len(visual['nodes']) or not 0<=b<len(visual['nodes']):raise ContractError('Unknown flow node')
        else:
            if not visual.get('headers') or not visual.get('rows'):raise ContractError('Table cannot be empty')
            if any(len(row)!=len(visual['headers']) for row in visual['rows']):raise ContractError('Ragged didactic table')

def figures(out,plan):
    from playwright.sync_api import sync_playwright
    target=out/'artifacts/figures';target.mkdir(parents=True,exist_ok=True);records=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        for index,v in enumerate(plan.get('visuals',[])):
            title=html.escape(v['title']);esc=lambda x:html.escape(str(x))
            if v['kind']=='table':
                body='<table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in v['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in v['rows'])+'</tbody></table>'
            else:
                boxes=[];centers=[];y=30
                for label in v['nodes']:
                    lines=textwrap.wrap(str(label),48) or [''];height=32+26*len(lines);centers.append((y+height/2,y,height))
                    boxes.append(f'<rect x="35" y="{y}" width="580" height="{height}" rx="10" fill="#e9f1f6" stroke="#246987" stroke-width="2"/>')
                    boxes.append(f'<text x="55" y="{y+30}" font-size="20" fill="#14263c">'+''.join(f'<tspan x="55" dy="{0 if i==0 else 26}">{esc(line)}</tspan>' for i,line in enumerate(lines))+'</text>');y+=height+38
                edges=[]
                for a,b in v.get('edges',[]):
                    ya=centers[a][0];yb=centers[b][0]
                    if b==a+1:
                        edges.append(f'<path d="M325 {centers[a][1]+centers[a][2]} V{centers[b][1]-4}" stroke="#246987" stroke-width="3" fill="none" marker-end="url(#arrow)"/>');continue
                    edges.append(f'<path d="M615 {ya} H650 V{yb} H618" stroke="#246987" stroke-width="3" fill="none" marker-end="url(#arrow)"/>')
                body=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 {y}" role="img" aria-label="{html.escape(v["alt_text"],quote=True)}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 Z" fill="#246987"/></marker></defs>'+''.join(edges+boxes)+'</svg>' 
            document='<!doctype html><html lang="en"><meta charset="utf-8"><style>body{margin:0;font:18px/1.55 system-ui;color:#14263c;background:#fff}figure{margin:0;padding:28px;max-width:720px;overflow-wrap:anywhere}h2{font:600 27px/1.2 Georgia}table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #8095a8;text-align:left}th{background:#e9f1f6}li{border:2px solid #246987;padding:12px;margin:14px 0;border-radius:8px}</style><figure><h2>'+title+'</h2>'+body+'<figcaption>'+esc(v['alt_text'])+'</figcaption></figure></html>'
            raw=target/f'figure-{index+1}.html';raw.write_text(document)
            page=browser.new_page(viewport={'width':720,'height':900},device_scale_factor=2);page.goto(raw.as_uri());png=target/f'figure-{index+1}.png';page.locator('svg' if v['kind']=='flow' else 'table').screenshot(path=str(png));page.close()
            records.append({'path':str(png),'title':v['title'],'alt_text':v['alt_text'],'source_refs':v['source_refs'],'origin':'authored source-grounded schematic, not a source scan'})
        browser.close()
    if records:
        web=out/'artifacts/web/index.html';doc=web.read_text();gallery='<section id="figures"><h2>Learning figures</h2>'+''.join('<figure><img style="max-width:100%;height:auto" src="../figures/'+Path(r['path']).name+'" alt="'+html.escape(r['alt_text'],quote=True)+'"><figcaption>'+html.escape(r['title'])+' — '+html.escape(', '.join(r['source_refs']))+'</figcaption></figure>' for r in records)+'</section>';web.write_text(doc.replace('</main>',gallery+'</main>'))
    write_json(out/'figure_register.json',records);return records

def split_products(out):
    import pymupdf
    path=out/'artifacts/learning_package.pdf'
    with pymupdf.open(path) as doc:
        task=next((i for i,p in enumerate(doc) if 'Übungs- und Aufgabenbuch' in p.get_text()),None)
        solutions=next((i for i,p in enumerate(doc) if 'Musterlösungen und Rubrics' in p.get_text()),None)
        if task is None or solutions is None or not 0<task<solutions:raise ContractError('Book section boundaries not found; cannot claim separate products')
        figure_pages=[i for i,p in enumerate(doc) if 'Exam Mastery - learning figure' in p.get_text()]
        solution_end=(min(figure_pages)-1) if figure_pages else len(doc)-1
        bounds=[('Lehrbuch.pdf',0,task-1),('Aufgaben.pdf',task,solutions-1),('Loesungen.pdf',solutions,solution_end)]
        for name,start,end in bounds:
            with pymupdf.open() as target:
                target.insert_pdf(doc,from_page=start,to_page=end)
                if name=='Lehrbuch.pdf':
                    for page in figure_pages:target.insert_pdf(doc,from_page=page,to_page=page)
                target.save(out/'artifacts'/name)
    return [x[0] for x in bounds]

# Legacy figures remain available for the unchanged regression corpus.
_legacy_figures=figures
_legacy_check_visuals=check_visuals

def check_visuals(plan,manifest):
    from .scientific_visuals import validate
    legacy=[];modern=[]
    for visual in plan.get('visuals',[]):
        (modern if 'data_origin' in visual or visual.get('kind') not in ('flow','table') else legacy).append(visual)
    _legacy_check_visuals({**plan,'visuals':legacy},manifest)
    locators={c['locator'] for c in manifest['chunks']}
    for visual in modern:
        validate(visual,locators,[{'id':v.get('formula_id')} for v in modern if v.get('formula_id')])
    ids=[v.get('id') for v in modern]
    if modern and (any(not x for x in ids) or len(set(ids))!=len(ids)):raise ContractError('Scientific figures require unique stable IDs')
    for decision in plan.get('visual_decisions',[]):
        if not decision.get('reason'):raise ContractError('Visual decision needs didactic reason')
        if decision.get('required') and (not decision.get('visual_ids') or not set(decision['visual_ids'])<=set(ids)):raise ContractError('Required visual missing from actual specifications')

def figures(out,plan):
    from .scientific_visuals import validate,render,raster
    from .common import sha_file
    legacy=[v for v in plan.get('visuals',[]) if 'data_origin' not in v and v.get('kind') in ('flow','table')]
    modern=[v for v in plan.get('visuals',[]) if v not in legacy]
    ids=[v.get('id') for v in modern]
    if len(set(ids))!=len(ids):raise ContractError('Duplicate scientific figure IDs across units; explicit namespacing required')
    records=_legacy_figures(out,{**plan,'visuals':legacy}) if legacy or not modern else []
    target=out/'artifacts/figures';target.mkdir(parents=True,exist_ok=True)
    evidence=[]
    for index,v in enumerate(modern):
        validate(v,v['source_refs'],plan.get('mathematics',[]))
        svg=target/('scientific-'+str(index+1)+'.svg');qa=render(v,svg,plan.get('mathematics',[]));png=raster(svg)
        timeline_note=' Ordered events; spacing is not a proportional time scale.' if v['kind']=='timeline' else ''
        record={'id':v['id'],'path':str(svg),'png':str(png),'title':v['title'],'caption':v['caption']+timeline_note,'alt_text':v['alt_text']+timeline_note,'source_refs':v['source_refs'],'origin':v['data_origin'],'svg_sha256':sha_file(svg),'specification':v}
        records.append(record);evidence.append(qa)
    if modern:
        web=out/'artifacts/web/index.html';doc=web.read_text();gallery='<section id="scientific-figures"><h2>Scientific figures</h2>'+''.join('<figure style="margin:24px 0;max-width:100%" id="figure-'+html.escape(r['id'],quote=True)+'"><div tabindex="0" role="region" aria-label="Scrollable scientific figure" style="max-width:100%;overflow-x:auto"><img style="display:block;min-width:650px;width:100%;max-width:none;height:auto;background:white" src="../figures/'+Path(r['path']).name+'" alt="'+html.escape(r['alt_text'],quote=True)+'"></div><figcaption>'+html.escape(r['title']+' — '+r['caption'])+'<br>Data: '+html.escape(r['origin'])+' · '+html.escape(', '.join(r['source_refs']))+'</figcaption></figure>' for r in records if r.get('id'))+'</section>';web.write_text(doc.replace('</main>',gallery+'</main>'))
    web=out/'artifacts/web/index.html'
    doc=web.read_text()
    for record in records:
        if not record.get('id'):continue
        marker='<div data-solution-figure="'+html.escape(record['id'],quote=True)+'"></div>'
        attached='<figure class="solution-scientific-figure"><div tabindex="0" role="region" aria-label="Scrollable solution figure" style="max-width:100%;overflow-x:auto"><img style="display:block;min-width:650px;width:100%;max-width:none;height:auto;background:white" src="../figures/'+Path(record['path']).name+'" alt="'+html.escape(record['alt_text'],quote=True)+'"></div><figcaption>'+html.escape(record['title']+' — '+record['caption'])+'</figcaption></figure>'
        doc=doc.replace(marker,attached)
    if 'data-solution-figure=' in doc:raise ContractError('Solution references an unrendered scientific figure')
    web.write_text(doc)
    write_json(out/'figure_register.json',records);write_json(out/'figure_evidence.json',evidence);return records
