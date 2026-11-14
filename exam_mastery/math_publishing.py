"""Canonical, offline mathematical assets and bounded, non-evaluating verification."""
from pathlib import Path
import ast,copy,hashlib,html,json,math,os,re,subprocess,xml.etree.ElementTree as ET
from functools import lru_cache
from .common import ContractError,write_json
TOKEN=re.compile(r'\[\[(math|ref):([A-Za-z0-9_:.-]+)\]\]')
FORBIDDEN=re.compile(r'\\(?:href|url|html\w*|style|class|cssId|includegraphics|input|write|require|def|newcommand|renewcommand|catcode)\b')

def _validate_registry_impl(records,source_refs=None):
 if not isinstance(records,list):raise ContractError('mathematics must be an array')
 seen=set()
 for r in records:
  for key in ('id','tex','alt','symbols','domain','assumptions','source_refs'):
   if key not in r:raise ContractError('Math contract missing '+key)
  if not re.fullmatch(r'[A-Za-z0-9_:.-]+',r['id']) or r['id'] in seen:raise ContractError('Duplicate/invalid equation ID')
  seen.add(r['id'])
  if not isinstance(r['tex'],str) or not 0<len(r['tex'])<=10000 or FORBIDDEN.search(r['tex']):raise ContractError('Unsafe/empty/oversized TeX')
  if not r['alt'].strip() or not r['domain'].strip() or not isinstance(r['assumptions'],list):raise ContractError('Math requires meaning, domain and assumptions')
  if not r['source_refs'] or source_refs is not None and not set(r['source_refs'])<=set(source_refs):raise ContractError('Math lacks exact source provenance')
  names=set()
  for symbol in r['symbols']:
   if not symbol.get('name') or symbol['name'] in names or not symbol.get('definition') or not symbol.get('domain') or not symbol.get('unit'):raise ContractError('Missing/inconsistent symbol definition, domain or unit')
   names.add(symbol['name'])
  if r.get('notation_kind','mathematical')!='chemistry':
   text=r['tex']
   text=re.sub(r'\\(?:begin|end|text|mathrm|operatorname|mathbb)\{[^{}]*\}', '', text)
   greek=set(re.findall(r'\\(alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|omega|pi)\b',text))
   text=re.sub(r'\\mathsf\s*(?:\{T\}|T)', '', text)
   text=re.sub(r'\\[A-Za-z]+', '', text)
   actual=set(re.findall(r'[A-Za-z]',text))|greek
   if not actual<=names:raise ContractError('TeX contains undefined symbols: '+', '.join(sorted(actual-names)))
  declared=r.get('used_symbols',[])
  if set(declared)!=names:raise ContractError('used_symbols and symbol definitions disagree')
  # Mathematical correctness is separate from TeX rendering. Checks are bounded evidence.
  verify_checks(r)

def validate_registry(records,source_refs=None):
 if not isinstance(records,list):raise ContractError('mathematics must be an array')
 ids=[r.get('id') for r in records if isinstance(r,dict)]
 if len(ids)!=len(records) or len(set(ids))!=len(ids):raise ContractError('Duplicate or malformed mathematical record')
 errors=[]
 for record in records:
  try:_validate_registry_impl([record],source_refs)
  except (ContractError,KeyError,ValueError,TypeError) as error:errors.append(str(record.get('id'))+': '+str(error))
 if errors:raise ContractError('Mathematical contract errors: '+'; '.join(errors))

def symbolic(expression,symbols):
 import sympy as sp
 if not isinstance(expression,str) or len(expression)>400:raise ContractError('Symbolic expression too long')
 try:tree=ast.parse(expression,mode='eval')
 except SyntaxError as e:raise ContractError('Symbolic syntax error') from e
 if len(list(ast.walk(tree)))>120:raise ContractError('Symbolic expression complexity limit')
 allowed={'sin':sp.sin,'cos':sp.cos,'exp':sp.exp,'log':sp.log,'sqrt':sp.sqrt,'Abs':sp.Abs}
 def convert(n):
  if isinstance(n,ast.Expression):return convert(n.body)
  if isinstance(n,ast.Constant) and type(n.value) in (int,float) and math.isfinite(n.value):return sp.Rational(str(n.value))
  if isinstance(n,ast.Name) and n.id in symbols:return symbols[n.id]
  if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):return convert(n.operand)*(-1 if isinstance(n.op,ast.USub) else 1)
  if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Pow)):
   a,b=convert(n.left),convert(n.right)
   if isinstance(n.op,ast.Add):return a+b
   if isinstance(n.op,ast.Sub):return a-b
   if isinstance(n.op,ast.Mult):return a*b
   if isinstance(n.op,ast.Div):return a/b
   if not b.is_number or abs(float(b))>8:raise ContractError('Only bounded constant symbolic powers supported')
   return a**b
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in allowed and len(n.args)==1 and not n.keywords:return allowed[n.func.id](convert(n.args[0]))
  raise ContractError('Disallowed symbolic syntax or undefined symbol')
 return convert(tree)

def dimensions(expression,definitions):
 tree=ast.parse(expression,mode='eval')
 def add(a,b,factor=1):
  result={k:a.get(k,0)+factor*b.get(k,0) for k in set(a)|set(b)}
  return {k:v for k,v in result.items() if abs(v)>1e-10}
 def dim(n):
  if isinstance(n,ast.Expression):return dim(n.body)
  if isinstance(n,ast.Constant) and type(n.value) in (int,float):return {}
  if isinstance(n,ast.Name) and n.id in definitions:return definitions[n.id]
  if isinstance(n,ast.UnaryOp):return dim(n.operand)
  if isinstance(n,ast.BinOp):
   a,b=dim(n.left),dim(n.right)
   if isinstance(n.op,(ast.Add,ast.Sub)):
    if a!=b:raise ContractError('Incompatible dimensions in sum/difference')
    return a
   if isinstance(n.op,ast.Mult):return add(a,b)
   if isinstance(n.op,ast.Div):return add(a,b,-1)
   if isinstance(n.op,ast.Pow) and isinstance(n.right,ast.Constant) and not b:return {k:v*n.right.value for k,v in a.items()}
  raise ContractError('Dimension operation unsupported; do not claim verified')
 return dim(tree)

def verify_checks(record):
 import sympy as sp
 symbols={s['name']:sp.Symbol(s['name'],**s.get('properties',{})) for s in record['symbols']}
 results=[]
 for c in record.get('checks',[]):
  if c['kind']=='equivalence':
   left,right=symbolic(c['lhs'],symbols),symbolic(c['rhs'],symbols)
   if sp.simplify(left-right)!=0:raise ContractError('Symbolic equivalence not established')
  elif c['kind']=='numeric':
   expr=symbolic(c['expression'],symbols)
   if set(c['values'])!=set(str(x) for x in expr.free_symbols):raise ContractError('Numeric reference substitutions incomplete')
   actual=float(expr.subs({symbols[k]:v for k,v in c['values'].items()}))
   if not math.isfinite(actual) or not math.isclose(actual,c['expected'],rel_tol=1e-8,abs_tol=1e-9):raise ContractError('Numeric mathematical reference mismatch')
  elif c['kind']=='dimensions':
   if any('dimension' not in s for s in record['symbols']):raise ContractError('Explicit dimensions required for every symbol in dimension check')
   actual=dimensions(c['expression'],{s['name']:s['dimension'] for s in record['symbols']})
   if actual!=c['expected']:raise ContractError('Dimension mismatch')
  else:raise ContractError('Unsupported mathematical check')
  results.append({'kind':c['kind'],'status':'PASS','scope':'Bounded symbolic/arithmetic evidence under declared assumptions, not a general proof'})
 return results

@lru_cache(maxsize=256)
def _render_svg(tex,display=True):
 runtime=Path.home()/'.cache/exam-mastery-v05-node/node_modules'
 call=subprocess.run(['node',str(Path(__file__).parent/'math_runtime/render.cjs')],input=json.dumps({'tex':tex,'display':display}),capture_output=True,text=True,env={**os.environ,'EM_MATH_NODE_MODULES':str(runtime)},timeout=30)
 if call.returncode:raise ContractError('MathJax rendering failed: '+call.stderr[-1500:])
 tree=ET.fromstring(json.loads(call.stdout)['svg'])
 if any(x.tag.split('}')[-1] in ('script','image','foreignObject','a') for x in tree.iter()):raise ContractError('Unsafe math SVG')
 view=[float(x) for x in tree.attrib['viewBox'].split()];width=view[2]/1000*11;height=view[3]/1000*11
 if width>630 or height>420:raise ContractError('Formula too large for readable print; split into aligned steps or separate records')
 tree.set('width',str(width)+'pt');tree.set('height',str(height)+'pt')
 raw=ET.tostring(tree,encoding='unicode').replace('ns0:','').replace(':ns0','')
 return raw,width,height

def validate_renderability(records):
 errors=[]
 for record in records:
  try:_render_svg(record['tex'],record.get('display',True))
  except (ContractError,ValueError,ET.ParseError,subprocess.TimeoutExpired) as error:errors.append(record['id']+': '+str(error))
 if errors:raise ContractError('Mathematical render contract errors: '+'; '.join(errors))

def asset(record,dest):
 """Canonical checked vector and integrity-linked raster derivative."""
 validate_registry([record]);dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
 raw,width,height=_render_svg(record['tex'],record.get('display',True))
 key=hashlib.sha256(json.dumps({'tex':record['tex'],'display':record.get('display',True),'renderer':'mathjax-3.2.2-em1'},sort_keys=True).encode()).hexdigest()[:24]
 svg=dest/('emmath-'+key+'.svg');png=svg.with_suffix('.png');meta=png.with_suffix('.provenance.json')
 if svg.exists() and svg.read_text()!=raw:raise ContractError('Cached mathematical SVG differs from canonical TeX rendering')
 if not svg.exists():svg.write_text(raw)
 svg_hash=hashlib.sha256(svg.read_bytes()).hexdigest()
 if png.exists():
  if not meta.exists():raise ContractError('Cached mathematical PNG lacks canonical provenance')
  previous=json.loads(meta.read_text())
  if previous.get('svg_sha256')!=svg_hash or previous.get('png_sha256')!=hashlib.sha256(png.read_bytes()).hexdigest():raise ContractError('Mathematical PNG/TeX asset mismatch')
 else:
  import pymupdf
  from svglib.svglib import svg2rlg
  from reportlab.graphics import renderPDF
  pdf=renderPDF.drawToString(svg2rlg(str(svg)));doc=pymupdf.open(stream=pdf,filetype='pdf');doc[0].get_pixmap(matrix=pymupdf.Matrix(3,3),alpha=True).save(png);doc.close()
  write_json(meta,{'svg_sha256':svg_hash,'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'generator':'same canonical SVG via ReportLab/PyMuPDF at 3x'})
 return {'id':record['id'],'svg':str(svg),'png':str(png),'width':width,'height':height,'sha256':svg_hash,'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'tex':record['tex'],'alt':record['alt'],'source_refs':record['source_refs'],'checks':verify_checks(record)}

def prepare(records,dest):
 validate_registry(records)
 return {r['id']:{**asset(r,dest),'number':i+1,'record':r} for i,r in enumerate(records)}

def markup(value,registry,channel,legacy):
 chunks=[];last=0
 for m in TOKEN.finditer(str(value)):
  chunks.append(legacy(str(value)[last:m.start()]));kind,ident=m.groups()
  if ident not in registry:raise ContractError('Undefined formula reference '+ident)
  a=registry[ident];label='('+str(a['number'])+')'
  if kind=='ref':chunks.append('<a href="#eq-'+html.escape(ident,quote=True)+'">Eq. '+label+'</a>' if channel=='web' else 'Eq. '+label)
  elif channel=='web':
   raw=Path(a['svg']).read_text().replace('currentColor','currentColor')
   chunks.append('<span class="em-math" tabindex="0" role="math" aria-label="'+html.escape(a['alt'],quote=True)+'">'+raw+'</span>')
  elif channel=='anki':chunks.append('<span class="em-math-scroll" tabindex="0"><img class="em-math" src="'+Path(a['png']).name+'" alt="'+html.escape(a['alt'],quote=True)+'" style="height:'+str(a['height'])+'pt;max-width:none;object-fit:contain"></span>')
  else:
   scale=min(1,480/a['width']);chunks.append('<img src="'+html.escape(a['png'],quote=True)+'" width="'+str(a['width']*scale)+'" height="'+str(a['height']*scale)+'" valign="middle"/>')
  last=m.end()
 chunks.append(legacy(str(value)[last:]))
 if '[[math:' in ''.join(chunks) or '[[ref:' in ''.join(chunks):raise ContractError('Malformed mathematical reference')
 return ''.join(chunks)

def formula_plates(registry):
 from svglib.svglib import svg2rlg
 from reportlab.platypus import Flowable,KeepTogether,Paragraph,Spacer
 from reportlab.lib.styles import ParagraphStyle
 class Equation(Flowable):
  def __init__(self,a):
   Flowable.__init__(self);self.drawing=svg2rlg(a['svg']);self.factor=min(1,470/self.drawing.width);self.width=self.drawing.width*self.factor;self.height=self.drawing.height*self.factor+12
  def draw(self):
   from reportlab.graphics import renderPDF
   self.canv.saveState();self.canv.scale(self.factor,self.factor);renderPDF.draw(self.drawing,self.canv,0,6);self.canv.restoreState()
 style=ParagraphStyle('math-caption',fontSize=9,leading=13,spaceAfter=9)
 flow=[]
 for a in registry.values():
  r=a['record'];desc='Equation ('+str(a['number'])+'): '+html.escape(r['alt'])+'<br/>Domain: '+html.escape(r['domain'])+'<br/>Assumptions: '+html.escape('; '.join(r['assumptions']))
  desc+='<br/>Source anchors: '+html.escape(', '.join(r['source_refs']))
  desc+='<br/>'+'; '.join(html.escape(x['name']+': '+x['definition']+' ['+x['unit']+']; '+x['domain']) for x in r['symbols'])
  flow.append(KeepTogether([Equation(a),Paragraph(desc,style),Spacer(1,8)]))
 return flow
