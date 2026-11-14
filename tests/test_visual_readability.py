import unittest,tempfile,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from exam_mastery.common import read_json
from exam_mastery.publish import publish_html
from exam_mastery.editorial import figures
ENGINE=Path(__import__('exam_mastery').__file__).resolve().parents[1]
class ReadabilityTests(unittest.TestCase):
 def data(self):
  f=ENGINE/'fixtures/synthetic_responses'
  return {n:read_json(f/(n+'.json')) for n in ('architect','author','assessment','cards','interaction','design')}
 def test_scientific_diagram_retains_legible_label_scale_at_320(self):
  data=self.data();v=dict(id='synthetic-flow',kind='algorithm',title='Synthetic update sequence',caption='Three explicitly defined stages, synthetic.',alt_text='Initialize, update, return.',source_refs=['s:p1'],data_origin='synthetic',nodes=['Initialize the current state','Apply the defined update','Return the result'],edges=[[0,1],[1,2]],edge_labels=['then','then'])
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);web=publish_html(*[data[n] for n in ('architect','author','assessment','cards','interaction','design')],out/'artifacts/web');figures(out,{'visuals':[v],'mathematics':[]})
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page(viewport={'width':320,'height':800});page.goto(web.as_uri())
    image=page.locator('#scientific-figures img');width=image.evaluate('(e)=>e.getBoundingClientRect().width')
    self.assertGreaterEqual(16*width/780,12,'Diagram labels must not shrink below 12 screen pixels')
    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
    self.assertGreater(page.locator('#scientific-figures [tabindex="0"]').count(),0,'Local scrolling must be keyboard accessible')
    b.close()
 def test_lab_has_visible_named_axes_and_readable_chart_container(self):
  data=self.data()
  with tempfile.TemporaryDirectory() as d:
   web=publish_html(*[data[n] for n in ('architect','author','assessment','cards','interaction','design')],Path(d))
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page(viewport={'width':320,'height':800});page.goto(web.as_uri())
    page.locator('input[name=prediction][value=down]').check();page.locator('textarea[aria-label="Prediction reasoning"]').fill('A fixed profit and share count make retained profit fall as tax rises.');page.locator('#lab-root button').click()
    chart=page.locator('#lab-root svg').first
    self.assertIn(data['interaction']['numeric']['label'],chart.text_content())
    self.assertIn(data['interaction']['numeric']['value_label'],chart.text_content())
    self.assertGreaterEqual(chart.evaluate('(e)=>e.getBoundingClientRect().width'),560)
    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
    b.close()
 def test_constant_lab_response_uses_a_finite_visible_axis_range(self):
  data=self.data();data['interaction']['numeric']['constants']['profit']=0;data['interaction']['numeric']['reference_at_default']=0
  with tempfile.TemporaryDirectory() as d:
   web=publish_html(*[data[n] for n in ('architect','author','assessment','cards','interaction','design')],Path(d))
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page(viewport={'width':320,'height':800});page.goto(web.as_uri())
    page.locator('input[name=prediction][value=same]').check();page.locator('textarea[aria-label="Prediction reasoning"]').fill('Zero profit makes the response zero at all tax rates.');page.locator('#lab-root button').click()
    chart=page.locator('#lab-root svg').first
    self.assertNotIn('NaN',chart.locator('polyline').get_attribute('points'))
    self.assertAlmostEqual(float(chart.locator('circle').first.get_attribute('cy')),130)
    self.assertIn('Prediction confirmed.',page.locator('#lab-root').inner_text());b.close()
