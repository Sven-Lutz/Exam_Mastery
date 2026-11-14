"""Regression for actual freshly produced retention lab: question .8->.6, renderer .8->.9."""
import copy,tempfile,unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
from exam_mastery.common import read_json,ContractError
from exam_mastery.publish import publish_html
from exam_mastery.validate import check_interaction
ENGINE=Path(__import__('exam_mastery').__file__).resolve().parents[1]
class PredictionContractTests(unittest.TestCase):
 def data(self):
  f=ENGINE/'fixtures/synthetic_responses'
  data={n:read_json(f/(n+'.json')) for n in ('architect','author','assessment','cards','interaction','design')}
  data['interaction'].update(prediction_question='Compare retention 0.8 with 0.6: does second-hour loss rise?',numeric=dict(variable='r',constants={'initial_mass':10},expression='initial_mass*r*(1-r)',min=0.1,max=0.9,step=0.1,default=0.8,prediction_target=0.6,reference_at_default=1.6,label='Retention',value_label='Second-hour loss (mg)'))
  return data
 def test_declared_target_drives_fixed_feedback_and_survives_slider_changes(self):
  a=self.data()
  with tempfile.TemporaryDirectory() as d:
   path=publish_html(*[a[n] for n in ('architect','author','assessment','cards','interaction','design')],Path(d))
   with sync_playwright() as p:
    b=p.chromium.launch();page=b.new_page();page.goto(path.as_uri())
    page.locator('input[name=prediction][value=up]').check()
    page.locator('textarea[aria-label="Prediction reasoning"]').fill('6 times 0.4 gives 2.4 mg, exceeding 1.6 mg.')
    page.locator('#lab-root button').click()
    self.assertIn('Locked target r=0.6',page.locator('#lab-root').inner_text())
    self.assertIn('Prediction confirmed.',page.locator('#lab-root').inner_text())
    slider=page.locator('input[type=range]');slider.fill('0.9');slider.dispatch_event('input')
    self.assertIn('Prediction confirmed.',page.locator('#lab-root').inner_text())
    self.assertAlmostEqual(float(page.locator('.measure').inner_text().rsplit(':',1)[1]),0.9)
    b.close()
 def test_target_must_be_reachable_and_differ_from_baseline(self):
  a=self.data();check_interaction(a['interaction'],a['architect'])
  for target in (0.8,1.0,0.65,float('nan')):
   bad=copy.deepcopy(a['interaction']);bad['numeric']['prediction_target']=target
   with self.subTest(target=target),self.assertRaises(ContractError):check_interaction(bad,a['architect'])
if __name__=='__main__':unittest.main()
