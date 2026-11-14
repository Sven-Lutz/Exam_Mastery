import copy,json,tempfile,unittest
from pathlib import Path
from exam_mastery.common import ContractError
from exam_mastery.math_publishing import validate_registry,asset,verify_checks,markup
from exam_mastery.scientific_visuals import validate,render,raster

def record(tex=r'\frac{x+x}{2}=x'):
 return dict(id='eq-mean',tex=tex,alt='The mean of two equal quantities is that quantity',symbols=[dict(name='x',definition='quantity',domain='real',unit='m',dimension={'L':1})],used_symbols=['x'],domain='x real',assumptions=['same unit'],source_refs=['synthetic:p1'],checks=[dict(kind='equivalence',lhs='(x+x)/2',rhs='x'),dict(kind='dimensions',expression='(x+x)/2',expected={'L':1})])

class MathematicalContractTests(unittest.TestCase):
 def test_undefined_symbols_missing_units_duplicate_ids_and_unsafe_tex_fail(self):
  validate_registry([record()])
  bad=record('x+y')
  with self.assertRaises(ContractError):validate_registry([bad])
  bad=record();del bad['symbols'][0]['unit']
  with self.assertRaises(ContractError):validate_registry([bad])
  with self.assertRaises(ContractError):validate_registry([record(),record()])
  with self.assertRaises(ContractError):validate_registry([record(r'\href{javascript:alert(1)}{x}')])
 def test_false_equivalence_bad_dimension_and_numeric_reference_fail(self):
  for check in [dict(kind='equivalence',lhs='x+x',rhs='x'),dict(kind='dimensions',expression='x+1',expected={'L':1}),dict(kind='numeric',expression='x*x',values={'x':2},expected=5),dict(kind='equivalence',lhs="__import__('os').getcwd()",rhs='x')]:
   bad=record();bad['checks']=[check]
   with self.subTest(check=check),self.assertRaises(ContractError):verify_checks(bad)
 def test_advanced_tex_actual_svg_raster_and_invalid_macro(self):
  examples=[(r'\begin{aligned}x+x&=2x\\\frac{2x}{2}&=x\end{aligned}',['x']),
   (r'A=\begin{pmatrix}1&0\\0&1\end{pmatrix},\quad\mathbf{x}=\begin{pmatrix}1\\2\end{pmatrix}',['A','x']),
   (r'\sum_{k=1}^{n}k=\frac{n(n+1)}2,\quad\int_0^1 x^2\,\mathrm{d}x=\frac13',['k','n','x']),
   (r'\lim_{h\to0}\frac{(x+h)^2-x^2}{h}=2x',['h','x']),
   (r'f(x)=\begin{cases}x^2&x\ge0\\-x&x<0\end{cases}',['f','x']),
   (r'\min_{x\in\mathbb{R}} (x-b)^2',['x','b']),
   (r'\ce{2 H2 + O2 -> 2 H2O}',[])]
  with tempfile.TemporaryDirectory() as d:
   for index,(tex,names) in enumerate(examples):
    r=record(tex);r.update(id='eq-'+str(index),symbols=[dict(name=n,definition=n+' definition',domain='real',unit='1') for n in names],used_symbols=names,checks=[])
    if not names:r['notation_kind']='chemistry'
    a=asset(r,Path(d));self.assertGreater(Path(a['svg']).stat().st_size,200);self.assertGreater(Path(a['png']).stat().st_size,200)
   bad=record(r'\thisIsNotARealMathCommand{x}')
   with self.assertRaises(ContractError):asset(bad,Path(d))
 def test_formula_references_are_resolved_and_unresolved_fail(self):
  with self.assertRaises(ContractError):markup('[[math:missing]]',{},'web',str)

class ScientificFigureTests(unittest.TestCase):
 def base(self,kind):return dict(id='fig-one',kind=kind,title='Synthetic reference',caption='Synthetic demonstration, not observations.',alt_text='A labeled scientific reference with defined axes.',source_refs=['synthetic:p1'],data_origin='synthetic')
 def test_function_uses_canonical_formula_and_preserves_data_axes(self):
  r=record('x^2');r.update(expression='x*x',checks=[])
  v=self.base('function');v.update(formula_id=r['id'],variable='x',min=0,max=2,samples=5,x_label='Length',x_unit='m',y_label='Squared length',y_unit='m²')
  validate(v,['synthetic:p1'],[r])
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'plot.svg';qa=render(v,p,[r]);self.assertEqual(qa['y'],[0,.25,1,2.25,4]);self.assertIn('Squared length',p.read_text());self.assertTrue(raster(p).exists())
   before=p.read_bytes();render(v,p,[r]);self.assertEqual(before,p.read_bytes())
 def test_bad_axes_log_data_uncertainty_and_missing_required_figure_fail(self):
  from exam_mastery.editorial import check_visuals
  v=self.base('statistical');v.update(style='errorbar',x_label='Time',x_unit='s',y_label='Distance',y_unit='m',series=[dict(label='Synthetic',x=[0,1],y=[1,2],yerr=[-1,1])])
  with self.assertRaises(ContractError):validate(v,['synthetic:p1'])
  v['style']='line';v['y_scale']='log';v['series'][0]['y']=[0,2]
  with self.assertRaises(ContractError):validate(v,['synthetic:p1'])
  with self.assertRaises(ContractError):check_visuals({'visuals':[],'visual_decisions':[dict(required=True,reason='Necessary comparison',visual_ids=['absent'])]},{'chunks':[{'locator':'synthetic:p1'}]})
 def test_contrasting_diagram_types_are_actual_vectors(self):
  for kind in ('algorithm','architecture','decision_tree','legal_schema','structure','timeline'):
   v=self.base(kind)
   if kind=='timeline':v.update(events=[dict(time=0,label='Notice'),dict(time=2,label='Deadline')],time_unit='days')
   else:v.update(nodes=['Prerequisite / rule','Evidence / application','Result'],edges=[[0,1],[1,2]],edge_labels=['met','then'])
   validate(v,['synthetic:p1'])
   with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'diagram.svg';render(v,p);self.assertTrue(raster(p).exists());self.assertIn('<svg',p.read_text())
