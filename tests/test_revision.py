import unittest
from exam_mastery.revision import apply
from exam_mastery.common import ContractError
class RevisionTests(unittest.TestCase):
 def setUp(self):self.bundle={'blueprint':{'course_id':'course-1'},'assessment':{'items':[{'prompt':'ambiguous','points':2}]}}
 def test_patch_isolated_and_preserves_other_fields(self):
  result=apply(self.bundle,{'patches':[{'op':'replace','path':'/assessment/items/0/prompt','value':'Explicit bounded domain'}]})
  self.assertEqual(result['assessment']['items'][0]['prompt'],'Explicit bounded domain');self.assertEqual(result['assessment']['items'][0]['points'],2);self.assertEqual(self.bundle['assessment']['items'][0]['prompt'],'ambiguous')
 def test_no_source_or_code_patches(self):
  for path in ('/source_manifest/root','/../sources','/exam_mastery/workflow.py'):
   with self.subTest(path=path),self.assertRaises(ContractError):apply(self.bundle,{'patches':[{'op':'add','path':path,'value':'unsafe'}]})
 def test_identity_changes_denied(self):
  with self.assertRaises(ContractError):apply(self.bundle,{'patches':[{'op':'replace','path':'/blueprint/course_id','value':'changed'}]})
 def test_negative_indices_denied(self):
  with self.assertRaises(ContractError):apply(self.bundle,{'patches':[{'op':'remove','path':'/assessment/items/-1'}]})

class RevisionFlowTests(unittest.TestCase):
 def test_major_finding_triggers_one_revision_and_reaudit(self):
  import tempfile,json
  from pathlib import Path
  from exam_mastery.workflow import run
  from exam_mastery.providers import Provider
  root=Path(__file__).resolve().parents[1]
  class ScriptedProvider:
   name='claude';model='SCRIPTED_TEST_NOT_LIVE_CLAUDE'
   def __init__(self):self.audits=0
   def ask(self,role,prompt,out,fixtures):
    if role=='revision':return {'patches':[{'op':'replace','path':'/author/limitations/0','value':'Revised synthetic limitation; no real course verification.'}]}
    result=Provider('fixture').ask(role,prompt,out,fixtures)
    if role=='audit':
     self.audits+=1
     if self.audits==1:result.update(verdict='NEEDS_REVIEW',findings=[{'severity':'major','description':'Synthetic revision test','object_id':'test','source_refs':[]}])
    return result
  provider=ScriptedProvider()
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'run'
   status=run(root/'fixtures/synthetic_course',out,provider,provider,root/'fixtures/synthetic_responses')
   self.assertEqual(status.get('revision_count'),1,status)
   self.assertEqual(status['status'],'NEEDS_REVIEW')
   self.assertEqual(provider.audits,2)
   self.assertTrue((out/'pre_revision/artifacts/learning_package.pdf').exists())
   self.assertTrue((out/'audit_revision.json').exists())
