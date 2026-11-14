import unittest,tempfile,json,copy
from pathlib import Path
from playwright.sync_api import sync_playwright
from exam_mastery.common import read_json,write_json,ContractError
from exam_mastery.publish import publish_all,publish_pdf,rich_text
from exam_mastery.editorial import figures
from exam_mastery.math_visual_qa import verify
ENGINE=Path(__import__('exam_mastery').__file__).resolve().parents[1]
class SolutionArtifactTests(unittest.TestCase):
 def data(self):
  return {n:read_json(ENGINE/'fixtures/synthetic_responses'/(n+'.json')) for n in ('architect','author','assessment','cards','interaction','design')}
 def test_unicode_indices_and_units_are_typeset_without_missing_glyphs(self):
  import pymupdf
  d=self.data();d['assessment']['items'][0]['solution']='Formal balance: 2 H₂ + O₂ → 2 H₂O. Energy: kg m² s⁻². ∇ J = 0.'
  self.assertIn('<sub>2</sub>',rich_text('H₂O'))
  self.assertIn('<super>−2</super>',rich_text('s⁻²'))
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);publish_all(*[d[n] for n in ('architect','author','assessment','cards','interaction','design')],out)
   with pymupdf.open(out/'artifacts/learning_package.pdf') as pdf:
    missing=[chr(c[0]) for page in pdf for span in page.get_texttrace() for c in span['chars'] if c[1]==0 and chr(c[0]).strip()]
   self.assertEqual(missing,[],'No .notdef glyphs in actual PDF prose')
 def test_solution_uses_the_actual_declared_vector_figure(self):
  import pymupdf
  d=self.data();d['assessment']['items'][0]['figure_ids']=['bars'];d['assessment']['items'][0]['solution']='Read the actual error bars attached to this solution.'
  v=dict(id='bars',kind='statistical',style='errorbar',title='Synthetic illustrative intervals',caption='Supplied half-widths; no confidence coverage.',alt_text='Three synthetic means with symmetric illustrative half-widths.',data_origin='synthetic',source_refs=['s:p1'],x_label='Input',x_unit='a.u.',y_label='Mean',y_unit='a.u.',series=[dict(label='Synthetic means',x=[1,2,3],y=[2,3,3.5],yerr=[.3,.4,.5])])
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);publish_all(*[d[n] for n in ('architect','author','assessment','cards','interaction','design')],out);records=figures(out,{'visuals':[v],'mathematics':[]});publish_pdf(d['architect'],d['author'],d['assessment'],d['interaction'],d['design'],out/'artifacts/learning_package.pdf',records)
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page();page.goto((out/'artifacts/web/index.html').as_uri());image=page.locator('#practice details img');self.assertEqual(image.count(),1);self.assertTrue(image.evaluate('(e)=>e.complete&&e.naturalWidth>0'));b.close()
   with pymupdf.open(out/'artifacts/learning_package.pdf') as pdf:
    pages=[p for p in pdf if 'Read the actual error bars' in p.get_text()];self.assertTrue(pages);self.assertIn('Synthetic illustrative intervals',pages[0].get_text());self.assertGreater(len(pages[0].get_drawings()),10)
 def test_actual_math_visual_gate_checks_real_figure_bytes(self):
  d=self.data();d['interaction']={'kind':'none'};d['author']['mathematics']=[dict(id='square',tex='x^2',alt='Square of a real input',domain='Real',assumptions=['Formal synthetic example'],source_refs=['s:p1'],used_symbols=['x'],symbols=[dict(name='x',definition='Real input',domain='Real',unit='1')])]
  v=dict(id='flow',kind='algorithm',title='Synthetic sequence',caption='Initialize then return.',alt_text='Initialize then return.',data_origin='synthetic',source_refs=['s:p1'],nodes=['Initialize','Return'],edges=[[0,1]],edge_labels=['then'])
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);publish_all(*[d[n] for n in ('architect','author','assessment','cards','interaction','design')],out);records=figures(out,{'visuals':[v],'mathematics':d['author']['mathematics']});publish_pdf(d['architect'],d['author'],d['assessment'],d['interaction'],d['design'],out/'artifacts/learning_package.pdf',records)
   for name in ('author','interaction','cards'):write_json(out/(name+'.json'),d[name])
   write_json(out/'learning_model.json',{'units':[]})
   self.assertEqual(verify(out)['status'],'PASS')
   Path(records[0]['path']).write_text('<svg/>')
   with self.assertRaisesRegex(ContractError,'Figure bytes'):verify(out)
 def test_solution_contract_rejects_fake_plot_and_unknown_identity_but_accepts_data_table(self):
  from exam_mastery.scientific_visuals import check_solution_figures
  plan={'visuals':[{'id':'bars'}]}
  item={'solution':'1 | 2 | 3\n2 | 3 | 4\n3 | 4 | 5\n4 | 5 | 6','figure_ids':['bars']}
  check_solution_figures({'items':[item]},plan)
  with self.assertRaisesRegex(ContractError,'unknown'):
   check_solution_figures({'items':[{**item,'figure_ids':['other']}]},plan)
  plot='4.0 |               ┬\n3.5 |               ●\n3.4 |        ┬      │\n3.0 |        ●      ┴'
  with self.assertRaisesRegex(ContractError,'Text-based'):
   check_solution_figures({'items':[{'solution':plot}]},plan)
 def test_scientific_table_labels_have_portable_font_outlines(self):
  from exam_mastery.scientific_visuals import render,raster
  v=dict(id='notation',kind='table',title='Formal notation',caption='Synthetic notation without empirical claims.',alt_text='Gradient and species notation.',source_refs=['s:p1'],data_origin='synthetic',headers=['Quantity','Notation'],rows=[['Gradient','∇J'],['Units','kg m² s⁻²'],['Species','H₂O']])
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'table.svg';render(v,path);svg=path.read_text()
   self.assertNotIn('<text',svg,'Figure labels must not depend on substitute client fonts')
   self.assertIn('∇J',svg);self.assertGreater(svg.count('<path'),5);self.assertGreater(raster(path).stat().st_size,1000)
   bad={**v,'rows':[['Unsupported','🧬']]}
   with self.assertRaisesRegex(ContractError,'glyph'):render(bad,path)
 def test_actual_pdf_retains_all_directed_edge_arrowheads(self):
  from exam_mastery.scientific_visuals import render
  from svglib.svglib import svg2rlg
  from reportlab.graphics import renderPDF
  import pymupdf
  v=dict(id='cycle',kind='algorithm',title='Synthetic control flow',caption='Defined directions.',alt_text='Initialize, test, update; update returns to test.',source_refs=['s:p1'],data_origin='synthetic',nodes=['Initialize','Test','Update','Return'],edges=[[0,1],[1,2],[2,1],[1,3]],edge_labels=['Start','Yes','Repeat','No'])
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'cycle.svg';render(v,path)
   import re
   rails=re.findall(r'H([0-9.]+) V',path.read_text());self.assertEqual(len(set(rails)),2,'Return and exit edges must not merge into one shared rail')
   pdf=renderPDF.drawToString(svg2rlg(str(path)))
   with pymupdf.open(stream=pdf,filetype='pdf') as doc:
    blue=(36/255,105/255,135/255)
    heads=[x for x in doc[0].get_drawings() if x['fill'] and all(abs(a-b)<.005 for a,b in zip(x['fill'],blue)) and x['rect'].width<=12 and x['rect'].height<=12]
    self.assertEqual(len(heads),4,'Actual PDF must retain each arrow, including distinct return and exit edges')
 def test_ordered_timeline_disclaims_nonproportional_spacing_in_actual_products(self):
  d=self.data();v=dict(id='time',kind='timeline',title='Fictional notice timeline',caption='Day 3 is after the day-2 deadline.',alt_text='Due day 0, deadline day 2, notice day 3.',source_refs=['s:p1'],data_origin='synthetic',events=[dict(time=0,label='Due'),dict(time=2,label='Deadline'),dict(time=3,label='Notice')],time_unit='days')
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);publish_all(*[d[n] for n in ('architect','author','assessment','cards','interaction','design')],out);record=figures(out,{'visuals':[v]})[0]
   self.assertIn('not a proportional time scale',record['caption'])
   self.assertIn('not a proportional time scale',Path(record['path']).read_text())
   self.assertIn('not a proportional time scale',(out/'artifacts/web/index.html').read_text())
if __name__=='__main__':unittest.main()
