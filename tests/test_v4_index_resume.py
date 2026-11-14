import json,tempfile,unittest,sqlite3
from pathlib import Path
from unittest.mock import patch
from exam_mastery.corpus import build,UNIT_CHARS
from exam_mastery.checkpoints import Checkpoints
from exam_mastery.common import ContractError
class IndexTests(unittest.TestCase):
 def test_all_large_corpus_characters_and_sources_indexed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);source=p/'arbitrary/nested';source.mkdir(parents=True)
   text=('Learning objective: derive and test a recurrence.\n'*4000).strip()
   (source/'source.md').write_text(text);(source/'.DS_Store').write_bytes(b'finder metadata')
   manifest,units=build(p/'arbitrary',p/'out',p/'cache')
   self.assertFalse(manifest['truncated']);self.assertTrue(manifest['coverage_complete']);self.assertGreater(len(units),5)
   self.assertEqual(sum(len(s['excerpt']) for u in units for s in u['segments']),len(text))
   self.assertTrue(all(sum(len(s['excerpt']) for s in u['segments'])<=UNIT_CHARS for u in units))
   db=sqlite3.connect(p/'out/corpus.sqlite3');self.assertEqual(db.execute('select count(*) from segments').fetchone()[0],sum(len(u['segments']) for u in units));db.close()
   with patch('exam_mastery.discovery.extract',side_effect=AssertionError('unchanged source reparsed')):
    again,_=build(p/'arbitrary',p/'out2',p/'cache')
   self.assertEqual(again['extracted_chars'],manifest['extracted_chars'])
 def test_online_sources_beyond_old_thirty_limit(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source').mkdir();(p/'source/links.md').write_text('\n'.join('https://example.com/'+str(i) for i in range(35)))
   with patch('exam_mastery.discovery.fetch_public',return_value=(b'<p>Source evidence.</p>','text/html','https://example.com/',[])):
    m,_=build(p/'source',p/'out',p/'cache')
   self.assertEqual(len(m['online_sources']),35);self.assertTrue(all(x['status']=='fetched' for x in m['online_sources']))
 def test_parenthesized_online_uri_is_fetched_without_losing_balanced_parentheses(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source').mkdir();(p/'source/references.md').write_text('[Reading](https://example.com/topic_(detail)).')
   with patch('exam_mastery.discovery.fetch_public',return_value=(b'<p>Evidence.</p>','text/html','https://example.com/topic_(detail)',[])) as fetch:
    manifest,_=build(p/'source',p/'out',p/'cache')
   fetch.assert_called_once_with('https://example.com/topic_(detail)')
   self.assertEqual(manifest['online_sources'][0]['status'],'fetched')
   self.assertIn('retrieved_at_utc',manifest['online_sources'][0])
 def test_notebook_saved_output_is_indexed_without_execution(self):
  import base64,io
  from PIL import Image
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source').mkdir();image=Image.new('RGB',(40,40),'white');buffer=io.BytesIO();image.save(buffer,format='PNG')
   nb={'cells':[{'cell_type':'code','source':['raise RuntimeError("must never run")'],'outputs':[{'output_type':'display_data','data':{'text/plain':['Recorded result: 42'],'image/png':base64.b64encode(buffer.getvalue()).decode()}}]}]}
   (p/'source/experiment.ipynb').write_text(json.dumps(nb))
   manifest,units=build(p/'source',p/'out',p/'cache')
   self.assertTrue(any('Recorded result: 42' in s['excerpt'] for u in units for s in u['segments']))
   from exam_mastery.corpus import prepare_visuals
   images,gaps=prepare_visuals(p/'source',manifest,units[0],p/'out/units'/units[0]['id'])
   self.assertEqual(len(images),1);self.assertFalse(gaps);self.assertTrue(Path(images[0]['path']).exists())
class ResumeTests(unittest.TestCase):
 def test_checkpoint_hashes_and_corruption_invalidate_cache(self):
  class Stub:
   calls=0
   def fingerprint(self):return {'name':'test'}
   def ask(self,*args,**kw):self.calls+=1;return {'answer':self.calls}
  with tempfile.TemporaryDirectory() as d:
   cp=Checkpoints(Path(d));p=Stub();valid=lambda x:None
   self.assertEqual(cp.invoke('role','request',p,valid)['answer'],1)
   self.assertEqual(cp.invoke('role','request',p,valid)['answer'],1);self.assertEqual(p.calls,1)
   (Path(d)/'stage_outputs/role.json').write_text('{}')
   self.assertEqual(cp.invoke('role','request',p,valid)['answer'],2)
   self.assertEqual(cp.invoke('role','changed request',p,valid)['answer'],3)
 def test_failed_node_resumes_without_repeating_completed_node(self):
  class Stub:
   calls=[];fail=True
   def fingerprint(self):return {'name':'test'}
   def ask(self,role,*a,**kw):
    self.calls.append(role)
    if role=='assessment' and self.fail:self.fail=False;raise RuntimeError('injected process failure')
    return {'ok':True}
  with tempfile.TemporaryDirectory() as d:
   cp=Checkpoints(Path(d));p=Stub();valid=lambda x:None
   cp.invoke('author','one',p,valid)
   with self.assertRaises(RuntimeError):cp.invoke('assessment','two',p,valid)
   cp.invoke('author','one',p,valid);cp.invoke('assessment','two',p,valid)
   self.assertEqual(p.calls,['author','assessment','assessment'])
