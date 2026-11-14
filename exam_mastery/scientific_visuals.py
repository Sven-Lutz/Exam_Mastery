"""Reproducible vector-first figures from bounded declarative specifications."""
from pathlib import Path
import html,math,json,hashlib,textwrap,xml.etree.ElementTree as ET
from .common import ContractError,write_json
KINDS={'function','statistical','flow','table','algorithm','architecture','decision_tree','timeline','legal_schema','structure'}
GRAPH=KINDS-{'function','statistical','table','timeline'}

def validate(visual,locators,math_records=()):
 kind=visual.get('kind')
 if kind not in KINDS:raise ContractError('Unsupported scientific figure kind')
 for field in ('title','alt_text','caption'):
  if not isinstance(visual.get(field),str) or not visual[field].strip():raise ContractError('Scientific figure needs '+field)
 if not visual.get('source_refs') or not set(visual['source_refs'])<=set(locators):raise ContractError('Figure source references missing/unknown')
 if visual.get('data_origin') not in ('source','synthetic','inference'):raise ContractError('Explicit figure data_origin required')
 if kind in ('function','statistical'):
  for axis in ('x','y'):
   if not visual.get(axis+'_label') or not visual.get(axis+'_unit'):raise ContractError('Axes require labels and units (1 if dimensionless)')
   if visual.get(axis+'_scale','linear') not in ('linear','log'):raise ContractError('Invalid axis scale')
  if kind=='function':
   ids={r['id'] for r in math_records}
   if visual.get('formula_id') not in ids:raise ContractError('Function plot must use a canonical formula ID')
   if not visual.get('variable') or not -1e6<=visual.get('min',0)<visual.get('max',0)<=1e6:raise ContractError('Bad function interval')
   if not 2<=visual.get('samples',101)<=201:raise ContractError('Function sample limit')
  else:
   if visual.get('style') not in ('scatter','line','bar','errorbar','histogram'):raise ContractError('Invalid statistical plot style')
   if not 1<=len(visual.get('series',[]))<=6:raise ContractError('Statistical figure needs bounded series')
   if visual['style']=='histogram' and (visual['y_unit']!='1' or type(visual.get('bins',10))!=int or not 2<=visual.get('bins',10)<=20):raise ContractError('Histogram frequency needs count unit 1 and 2–20 bins')
   for s in visual['series']:
    if visual['style']=='histogram':
     values=s.get('values',[])
     if not s.get('label') or not 1<=len(values)<=201 or any(type(v) not in (int,float) or not math.isfinite(v) for v in values) or 'x' in s or 'y' in s:raise ContractError('Histogram requires labeled raw values, not x/y pairs; bins is 2–20')
     if visual.get('x_scale')=='log' and any(v<=0 for v in values):raise ContractError('Log histogram input requires positive values')
     continue
    if not s.get('label') or not 1<=len(s.get('x',[]))<=201 or len(s['x'])!=len(s.get('y',[])):raise ContractError('Series data/legend mismatch')
    if any(type(x) not in (int,float) or not math.isfinite(x) for x in s['x']+s['y']):raise ContractError('Nonfinite figure data')
    if visual['style']=='errorbar' and (len(s.get('yerr',[]))!=len(s['y']) or any(v<0 or not math.isfinite(v) for v in s['yerr'])):raise ContractError('Invalid uncertainty data')
    for axis in ('x','y'):
     if visual.get(axis+'_scale')=='log' and any(v<=0 for v in s[axis]):raise ContractError('Log axis requires positive data')
 if kind in GRAPH:
  nodes=visual.get('nodes',[])
  if not 2<=len(nodes)<=12 or any(not isinstance(x,str) or not x.strip() or len(x)>400 for x in nodes):raise ContractError('Diagram needs 2–12 bounded, complete labels')
  for edge in visual.get('edges',[]):
   if len(edge)!=2 or any(type(i)!=int or not 0<=i<len(nodes) for i in edge):raise ContractError('Invalid diagram edge')
  estimated_height=48+sum(30+23*max(1,len(textwrap.wrap(label,64)))+64 for label in nodes)
  if estimated_height>860:raise ContractError('Diagram too dense for readable PDF; split into multiple figures')
  for index,edge in enumerate(visual.get('edges',[])):
   labels=visual.get('edge_labels',[])
   if labels and edge[1]!=edge[0]+1 and len(labels[index])>12:raise ContractError('Branch label too long for available gutter')
  labels=visual.get('edge_labels',[])
  if labels and len(labels)!=len(visual.get('edges',[])):raise ContractError('Missing edge labels')
  if kind in ('decision_tree','legal_schema') and not labels:raise ContractError('Decision/legal diagram requires explicit edge reasoning')
 if kind=='table':
  if not visual.get('headers') or not visual.get('rows') or any(len(x)!=len(visual['headers']) for x in visual['rows']):raise ContractError('Ragged or empty figure table')
 if kind=='timeline':
  events=visual.get('events',[])
  if not 2<=len(events)<=12 or any(not x.get('label') or type(x.get('time')) not in (int,float) or not math.isfinite(x['time']) for x in events):raise ContractError('Timeline needs timed labeled events')
  if not visual.get('time_unit'):raise ContractError('Timeline requires time unit')


def _vector_label(text,x,y,size):
 """Portable scientific labels: real local font outlines, no client font guessing."""
 import matplotlib
 from matplotlib.font_manager import FontProperties
 from matplotlib.ft2font import FT2Font
 from matplotlib.textpath import TextPath
 from matplotlib.transforms import Affine2D
 from matplotlib.path import Path as MplPath
 if not text.strip():return ''
 font=Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf'
 cmap=FT2Font(str(font)).get_charmap()
 missing={c for c in text if not c.isspace() and ord(c) not in cmap}
 if missing:raise ContractError('Unsupported scientific figure label glyphs: '+repr(sorted(missing)))
 shape=TextPath((0,0),text,size=size,prop=FontProperties(fname=str(font)),usetex=False).transformed(Affine2D().scale(1,-1).translate(x,y))
 bounds=shape.get_extents()
 if bounds.x0<0 or bounds.x1>780 or bounds.y0<0:raise ContractError('Scientific figure label clipped; shorten or split the label')
 commands=[]
 for points,code in shape.iter_segments(simplify=False):
  command={MplPath.MOVETO:'M',MplPath.LINETO:'L',MplPath.CURVE3:'Q',MplPath.CURVE4:'C',MplPath.CLOSEPOLY:'Z'}.get(code)
  if command is None:continue
  commands.append(command+(' '.join(format(float(v),'.5f') for v in points) if command!='Z' else ''))
 return '<g role="img" aria-label="'+html.escape(text,quote=True)+'"><title>'+html.escape(text)+'</title><path d="'+ ' '.join(commands)+'"/></g>'

def render(visual,path,math_records=()):
 """Return SVG and verified geometry/data evidence; never execute source code."""
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 kind=visual['kind'];esc=lambda s:html.escape(str(s),quote=True)
 evidence={'kind':kind,'data_origin':visual['data_origin'],'source_refs':visual['source_refs']}
 if kind in ('function','statistical'):
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  from matplotlib import rc_context
  from .math_publishing import symbolic
  import sympy as sp
  with rc_context({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'path','text.usetex':False,'svg.hashsalt':'exam-mastery-v05','axes.spines.top':False,'axes.spines.right':False}):
   fig,ax=plt.subplots(figsize=(7.2,4.4),layout='constrained')
   if kind=='function':
    record=next(r for r in math_records if r['id']==visual['formula_id'])
    if not record.get('expression'):raise ContractError('Canonical formula lacks executable bounded expression')
    symbols={s['name']:sp.Symbol(s['name'],**s.get('properties',{})) for s in record['symbols']}
    expr=symbolic(record['expression'],symbols)
    constants=visual.get('constants',{})
    if set(str(s) for s in expr.free_symbols)!={visual['variable'],*constants}:raise ContractError('Function plot symbols do not match canonical expression')
    xs=[visual['min']+(visual['max']-visual['min'])*i/(visual.get('samples',101)-1) for i in range(visual.get('samples',101))]
    ys=[float(expr.subs({symbols[k]:v for k,v in {**constants,visual['variable']:x}.items()})) for x in xs]
    if any(not math.isfinite(v) for v in ys):raise ContractError('Nonfinite function plot')
    if visual.get('y_scale')=='log' and any(v<=0 for v in ys):raise ContractError('Log y requires positive function')
    if visual.get('x_scale')=='log' and min(xs)<=0:raise ContractError('Log x requires positive interval')
    ax.plot(xs,ys,color='#246987',linewidth=2.2,label=visual.get('series_label',record['alt']))
    evidence.update(formula_id=record['id'],expression=record['expression'],x=xs,y=ys,constants=constants)
   else:
    for series in visual['series']:
     style=visual['style'];label=series['label']
     if style=='histogram':
      counts,edges,_=ax.hist(series['values'],bins=visual.get('bins',10),label=label)
      if int(sum(counts))!=len(series['values']):raise ContractError('Histogram lost source values')
      if visual.get('y_scale')=='log' and any(v<=0 for v in counts):raise ContractError('Log count scale cannot represent empty bins')
      evidence.setdefault('histograms',[]).append({'label':label,'counts':counts.tolist(),'edges':edges.tolist(),'observations':len(series['values'])})
      continue
     x,y=series['x'],series['y']
     if style=='scatter':ax.scatter(x,y,label=label,s=35)
     elif style=='bar':ax.bar(x,y,label=label,alpha=.85)
     elif style=='errorbar':ax.errorbar(x,y,yerr=series['yerr'],fmt='o',capsize=4,label=label)
     else:ax.plot(x,y,marker='o',label=label)
    evidence['series']=visual['series']
   ax.set_xlabel(visual['x_label']+' ['+visual['x_unit']+']');ax.set_ylabel(visual['y_label']+' ['+visual['y_unit']+']')
   ax.set_xscale(visual.get('x_scale','linear'));ax.set_yscale(visual.get('y_scale','linear'));ax.grid(alpha=.2);ax.legend(fontsize=9,loc='best')
   fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=fig.bbox
   xticks=[label for loc,label in zip(ax.get_xticks(),ax.get_xticklabels()) if min(ax.get_xlim())<=loc<=max(ax.get_xlim())]
   yticks=[label for loc,label in zip(ax.get_yticks(),ax.get_yticklabels()) if min(ax.get_ylim())<=loc<=max(ax.get_ylim())]
   for label in [ax.xaxis.label,ax.yaxis.label,*xticks,*yticks]:
    box=label.get_window_extent(renderer)
    if box.x0<bounds.x0-1 or box.y0<bounds.y0-1 or box.x1>bounds.x1+1 or box.y1>bounds.y1+1:raise ContractError('Plot label clipped')
   fig.savefig(path,format='svg',metadata={'Date':None,'Creator':'Exam Mastery scientific visuals v0.5'});plt.close(fig)
 elif kind=='timeline':
  events=sorted(visual['events'],key=lambda e:e['time']);nodes=[str(e['time'])+' '+visual['time_unit']+' — '+e['label'] for e in events]
  proxy={**visual,'kind':'flow','alt_text':visual['alt_text']+' Ordered events; spacing is not a proportional time scale.','nodes':nodes,'edges':[[i,i+1] for i in range(len(nodes)-1)]};return render(proxy,path,math_records)
 else:
  parts=[];width=780;y=28
  if kind=='table':
   rows=[visual['headers'],*visual['rows']];columns=len(rows[0]);cw=720/columns
   for index,row in enumerate(rows):
    wrapped=[textwrap.wrap(str(x),max(8,int(cw/7.5))) or [''] for x in row];height=max(map(len,wrapped))*21+24
    for col,lines in enumerate(wrapped):
     x=28+col*cw;parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{height}" fill="'+('#e9f1f6' if index==0 else '#ffffff')+'" stroke="#9aadbc"/>')
     for line,t in enumerate(lines):parts.append(_vector_label(t,x+12,y+24+line*21,15))
    y+=height
  else:
   nodes=visual['nodes'];centers=[]
   for label in nodes:
    lines=textwrap.wrap(label,64) or [''];height=30+23*len(lines);centers.append((y,height))
    parts.append(f'<rect x="28" y="{y}" width="650" height="{height}" rx="8" fill="#edf5f7" stroke="#246987"/>')
    for i,line in enumerate(lines):parts.append(_vector_label(line,46,y+28+i*23,16))
    y+=height+64
   detours=[i for i,(a,b) in enumerate(visual.get('edges',[])) if b!=a+1]
   lanes={edge:700+60*position/max(1,len(detours)-1) for position,edge in enumerate(detours)}
   for index,(a,b) in enumerate(visual.get('edges',[])):
    ya,ha=centers[a];yb,hb=centers[b]
    if b==a+1:
     route=f'M350 {ya+ha} V{yb-7}';tx,ty=360,ya+ha+31
     head=f'345,{yb-10} 355,{yb-10} 350,{yb-1}'
    else:
     route=f'M678 {ya+ha/2} H{lanes[index]} V{yb+hb/2} H685';tx,ty=683,ya+ha/2-8
     head=f'688,{yb+hb/2-5} 688,{yb+hb/2+5} 679,{yb+hb/2}'
    parts.append(f'<path d="{route}" fill="none" stroke="#246987" stroke-width="2"/>')
    parts.append(f'<polygon points="{head}" fill="#246987"/>')
    labels=visual.get('edge_labels',[])
    if labels:
     if len(labels[index])>(12 if b!=a+1 else 38):raise ContractError('Edge label too long for diagram layout; split into nodes')
     if b!=a+1:parts.append(f'<rect x="{tx-2}" y="{ty-14}" width="{min(92,len(labels[index])*7.5+5)}" height="18" fill="#ffffff"/>')
     parts.append(_vector_label(labels[index],tx,ty,13))
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="780" height="{y+20}" viewBox="0 0 780 {y+20}" role="img"><title>{esc(visual["title"])}</title><desc>{esc(visual["alt_text"])}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0 0 L0 6 L8 3 Z" fill="#246987"/></marker></defs><g font-family="DejaVu Sans,Arial,sans-serif" fill="#14263c">'+''.join(parts)+'</g></svg>'
  path.write_text(svg)
 evidence.update(svg_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),x_label=visual.get('x_label'),y_label=visual.get('y_label'),x_unit=visual.get('x_unit'),y_unit=visual.get('y_unit'),x_scale=visual.get('x_scale','linear'),y_scale=visual.get('y_scale','linear'))
 return evidence

def raster(svg):
 import pymupdf
 from svglib.svglib import svg2rlg
 from reportlab.graphics import renderPDF
 drawing=svg2rlg(str(svg));pdf=renderPDF.drawToString(drawing);doc=pymupdf.open(stream=pdf,filetype='pdf');png=Path(svg).with_suffix('.png');doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2)).save(png);doc.close();return png


def check_solution_figures(assessment,plan,allow_pending=False):
 """Require explicit figure identities; never infer a match from similar prose."""
 available={v.get('id') for v in plan.get('visuals',[]) if v.get('id')}
 for item in assessment['items']:
  refs=item.get('figure_ids',[])
  requirements=item.get('visual_requirements',[])
  if not isinstance(requirements,list):raise ContractError('Solution visual requirements must be an array')
  for requirement in requirements:
   if not isinstance(requirement,dict) or not requirement.get('purpose') or not requirement.get('case_scope'):raise ContractError('Required solution diagram lacks exact case scope')
   if not requirement.get('figure_ids'):
    if allow_pending:continue
    raise ContractError('Required solution diagram lacks figure identities')
   if not set(requirement['figure_ids'])<=set(refs):raise ContractError('Required solution diagram is not attached to this solution')
  if not isinstance(refs,list) or any(not isinstance(r,str) or r not in available for r in refs) or len(set(refs))!=len(refs):raise ContractError('Solution references an unknown/duplicate scientific figure')
  rows=__import__('re').findall(r'(?m)^\s*[-+]?\d+(?:\.\d+)?\s*[|│]\s*[│|●┬┴*]',item['solution'])
  if len(rows)>=4:raise ContractError('Text-based scientific plot is not supported; use an explicit declared figure reference and numeric explanation')
