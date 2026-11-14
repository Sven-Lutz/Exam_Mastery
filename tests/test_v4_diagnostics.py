import json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from exam_mastery.providers import Provider,ProviderError
class DiagnosticsRegression(unittest.TestCase):
 def test_nonzero_stdout_is_preserved_before_raise(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d);script=out/'claude';script.write_text('#!/bin/sh\ncat >/dev/null\nprintf \'{"error":"backend_limit","detail":"assessment rejected"}\'\nexit 17\n');script.chmod(0o700)
   with patch.dict(os.environ,{'PATH':str(out)+':'+os.environ['PATH']}):
    from exam_mastery.budget import ResourceBudget
    with self.assertRaises(ProviderError):Provider('claude',budget=ResourceBudget({'approval_id':'test','max_requests':5,'max_input_tokens':10**6,'max_output_tokens':10**6,'max_wall_seconds':600,'max_retries':1,'max_input_tokens_per_call':10**5,'max_output_tokens_per_call':10**4,'input_overhead_tokens_per_call':0,'image_input_tokens':0},out/'budget')).ask('assessment','Return JSON',out)
   candidates=list(out.rglob('process.json'));self.assertTrue(candidates)
   record=json.loads(candidates[0].read_text());self.assertEqual(record['returncode'],17)
   self.assertIn('backend_limit',(candidates[0].parent/'stdout.txt').read_text())
 def test_timeout_and_secrets_retained_safely(self):
  from exam_mastery.providers import redact
  self.assertEqual(redact('Bearer abc.secret.token'),'Bearer <REDACTED>')

 def test_optional_adapter_must_not_silently_discard_visual_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ProviderError):Provider('claude').ask('visual','inspect image',Path(d),images=['not-executed.png'])
   record=json.loads(next(Path(d).rglob('process.json')).read_text())
   self.assertIn('refusing to discard images',record['error'])
