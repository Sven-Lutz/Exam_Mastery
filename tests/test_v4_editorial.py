import unittest,copy,tempfile
from pathlib import Path
from exam_mastery.editorial import check_visuals
from exam_mastery.common import ContractError,read_json
class EditorialTests(unittest.TestCase):
 def test_invalid_edges_and_ragged_tables_do_not_render(self):
  local={'chunks':[{'locator':'source:p1'}]}
  v={'kind':'flow','nodes':['Assumption','Conclusion'],'edges':[[0,8]],'source_refs':['source:p1'],'title':'Reasoning','alt_text':'An assumption connects to a conclusion'}
  with self.assertRaises(ContractError):check_visuals({'visuals':[v]},local)
  v.update(kind='table',headers=['t','m'],rows=[['1']])
  with self.assertRaises(ContractError):check_visuals({'visuals':[v]},local)
 def test_numeric_prediction_target_is_not_regraded_when_slider_reverses(self):
  from playwright.sync_api import sync_playwright
  from exam_mastery.publish import publish_html
  f=Path(__file__).resolve().parents[1]/'fixtures/synthetic_responses';a={n:read_json(f/(n+'.json')) for n in ('architect','author','assessment','cards','interaction','design')}
  with tempfile.TemporaryDirectory() as d:
   path=publish_html(*[a[n] for n in ('architect','author','assessment','cards','interaction','design')],Path(d))
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page();page.goto(path.as_uri());page.locator('input[name=prediction][value=down]').check();page.locator('textarea[aria-label="Prediction reasoning"]').fill('Same profit and shares imply EPS decreases when tax increases.');page.locator('#lab-root button').click()
    slider=page.locator('input[type=range]');slider.fill(str(a['interaction']['numeric']['min']));slider.dispatch_event('input')
    self.assertIn('Prediction confirmed.',page.locator('#lab-root').inner_text());self.assertIn('Locked target',page.locator('#lab-root').inner_text());b.close()

 def test_math_markup_preserves_identifiers_and_escapes_source_html(self):
  from exam_mastery.publish import rich_text
  text=rich_text('M_(n+1)=M_0r^(n+1); rM_n; unverified_claims <script>evil()</script>')
  self.assertIn('M<sub>n+1</sub>=M<sub>0</sub>r<super>n+1</super>',text)
  self.assertIn('rM<sub>n</sub>',text)
  self.assertIn('unverified_claims',text)
  self.assertNotIn('<script>',text)
  self.assertIn('&lt;script&gt;',text)
