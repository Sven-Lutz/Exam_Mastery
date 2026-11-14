import json,tempfile,unittest
from pathlib import Path
from exam_mastery.common import ContractError
from exam_mastery.math_publishing import asset
from exam_mastery.validate import check_author
from test_math_visual import record
from exam_mastery.scientific_visuals import validate,render
class MathematicalIntegrityTests(unittest.TestCase):
 def test_svg_and_raster_cache_corruption_is_not_accepted(self):
  for channel in ('svg','png'):
   with self.subTest(channel=channel),tempfile.TemporaryDirectory() as d:
    a=asset(record(),Path(d));path=Path(a[channel]);path.write_bytes(path.read_bytes()+b'corrupt')
    with self.assertRaises(ContractError):asset(record(),Path(d))
 def test_author_repair_reports_symbol_and_render_errors_together(self):
  first=record('x+y');first['id']='bad-symbol'
  second=record(r'\notAnActualMathCommand{x}');second['id']='bad-render'
  section=dict(title='Synthetic',intuition='Interpret',formal='Reason',worked_example='Example',misconceptions=[],source_refs=['synthetic:p1'])
  a=dict(claims=[],sections=[section,section],limitations=[],mathematics=[first,second])
  with self.assertRaises(ContractError) as caught:check_author(a,{'chunks':[{'locator':'synthetic:p1'}]})
  self.assertIn('bad-symbol',str(caught.exception));self.assertIn('bad-render',str(caught.exception));self.assertIn('MathJax',str(caught.exception))
class HistogramTests(unittest.TestCase):
 def spec(self):return dict(id='hist',kind='statistical',style='histogram',title='Synthetic frequency distribution',caption='Raw synthetic values counted in two explicit bins.',alt_text='Two observations in each of two bins.',source_refs=['s:p1'],data_origin='synthetic',x_label='Value',x_unit='1',y_label='Frequency',y_unit='1',bins=2,series=[dict(label='Synthetic values',values=[0,0,1,1])])
 def test_histogram_preserves_observations_and_reports_real_bin_counts(self):
  v=self.spec();validate(v,['s:p1'])
  with tempfile.TemporaryDirectory() as d:
   result=render(v,Path(d)/'hist.svg');self.assertEqual(result['histograms'][0]['counts'],[2,2]);self.assertEqual(result['histograms'][0]['observations'],4)
 def test_histogram_does_not_silently_ignore_y_data(self):
  v=self.spec();v['series'][0].update(x=[0,1],y=[99,99])
  with self.assertRaises(ContractError):validate(v,['s:p1'])
