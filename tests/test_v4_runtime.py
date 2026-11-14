"""Scripted fault-injection only; never used as real-model acceptance evidence."""
import copy,json,re,tempfile,unittest
from pathlib import Path
from exam_mastery.runtime import run
from exam_mastery.common import read_json
FIX=Path(__file__).resolve().parents[1]/'fixtures'
class Scripted:
 def __init__(self):self.fail=True;self.calls=[]
 def fingerprint(self):return {'name':'scripted-test-only','model':'no-real-model'}
 def ask(self,role,prompt,out,**kwargs):
  self.calls.append(role)
  if role=='assessment' and self.fail:self.fail=False;raise RuntimeError('injected failure')
  if role.startswith('render_audit_'):
   pages=[x['page'] for x in kwargs.get('images',[])] if kwargs.get('images') and isinstance(kwargs['images'][0],dict) else []
   pages=json.loads(re.search(r'"reviewed_pages":(\[[^\]]+\])',prompt).group(1))
   return {'verdict':'NEEDS_REVIEW','reviewed_pages':pages,'findings':[],'limitations':['Scripted layout test; actual model acceptance is separate']}
  if role.startswith('course_audit_'):
   payload=json.loads(prompt.split('\n',1)[1]);return {'verdict':'NEEDS_REVIEW','findings':[],'reviewed_unit_ids':[u['unit_id'] for u in payload['units']],'limitations':['Scripted test, no academic verification']}
  if role=='learning_designer':
   payload=json.loads(prompt.split('CURRENT VERIFIED STRUCTURE (not externally verified facts)\n')[1]);return {'competency_methods':[{'competency_id':c['id'],'method':'Worked example then independent transfer','assessment_evidence':'Source-linked correct calculation','retrieval_suitable':False,'retrieval_rationale':'Scripted transport test; no cognitive suitability claim'} for c in payload['blueprint']['competencies']],'card_policy':'Bounded recall','visual_policy':'No additional figure needed in this transport-only test','visuals':[],'limits':['scripted'],'prerequisite_checks':[dict(unit_id=u['id'],prerequisite='percentage conversion',prompt='Convert 20% to a decimal',solution='20/100=0.2',pass_criterion='0.2',error_diagnosis='20 means missing division by 100',remediation='Percent means per hundred: 20/100=0.2',retry_prompt='Convert 30% to a decimal',retry_solution='30/100=0.3') for u in payload['blueprint']['units']]}
  source=re.search(r'\[(src-[^\]\s]+)\]',prompt).group(1);prefix=re.search(r'(unit-[a-f0-9]{12}):C\d',prompt)
  file='assessment' if role=='solutions' else 'audit' if role.endswith('_audit') else role
  obj=read_json(FIX/'synthetic_responses'/(file+'.json'));text=json.dumps(obj).replace('src-9b0c7b56ccbb:p1',source)
  if role!='architect' and prefix:
   for cid in ('C1','C2','C3'):text=text.replace('"'+cid+'"','"'+prefix.group(1)+':'+cid+'"')
  obj=json.loads(text)
  if role=='solutions':
   for item in obj['items']:
    item['marking_policy']=dict(method_credit='Credit correct method separately from arithmetic',follow_through='Deduct originating arithmetic error once; credit subsequent valid steps',alternatives='Accept equivalent algebraic methods')
    item['error_diagnoses']=[dict(error='Using tax rate as net fraction',diagnosis='Confuses retained and deducted quantities',remediation='Compute 1 minus the rate first')]
    for r in item['rubric']:r['partial_credit']='Award stated points for criterion; zero if absent'
  if role=='solutions':obj.update(numeric_checks=[{'assessment_id':'A1','expression':'120*(1-0.2)/30','expected':3.2,'constants':{}}],non_numeric_verification='Scripted transport test only')
  if role=='interaction':obj['transfer_solution']='Worked comparison under fixed pretax profit and shares; a changed rate changes the retained fraction.'
  if role.endswith('_audit'):obj.update(verdict='NEEDS_REVIEW',findings=[],unverified_claims=['Scripted evidence'])
  return obj
class RuntimeResumeTests(unittest.TestCase):
 def test_same_one_path_resumes_failed_assessment_and_finishes_audit(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);source=p/'any-name/deeper';source.mkdir(parents=True);(source/'lecture.md').write_text((FIX/'synthetic_course/lecture.md').read_text())
   provider=Scripted()
   first,s1=run(p/'any-name',provider,p/'output')
   self.assertEqual(s1['status'],'NO_GO');self.assertTrue(s1['resumable'])
   second,s2=run(p/'any-name',provider,p/'output')
   self.assertEqual(first,second);self.assertTrue(s2['resumed']);self.assertTrue(s2.get('final_audit_reached'),s2)
   self.assertEqual(s2['technical_status'],'PASS',s2);self.assertFalse(s2['academic_release'])
   self.assertEqual(provider.calls.count('architect'),1);self.assertEqual(provider.calls.count('assessment'),2)
   self.assertTrue((second/'artifacts/Lehrbuch.pdf').exists());self.assertTrue((second/'artifacts/Aufgaben.pdf').exists());self.assertTrue((second/'artifacts/Loesungen.pdf').exists())
   self.assertTrue((second/'status_history').exists())
   # A late visual failure must override earlier passing technical checks in
   # BOTH terminal status and the durable quality report.
   from unittest.mock import patch
   finding={'verdict':'FAIL','reviewed_pages':[1],'findings':[{'severity':'major','description':'Injected clipped diagram','object_id':'page 1','source_refs':[]}],'limitations':['Fault injection only']}
   with patch('exam_mastery.layout_review.inspect_layout',return_value=[finding]):
    third,s3=run(p/'any-name',provider,p/'output')
   self.assertEqual(s3['status'],'NO_GO');self.assertEqual(s3['technical_status'],'FAIL')
   final=read_json(third/'quality_report.json')
   self.assertEqual(final['technical_checks_status'],'PASS')
   self.assertEqual(final['technical_status'],'FAIL');self.assertEqual(final['pipeline_status'],'NO_GO')
