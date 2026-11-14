"""Counterexamples to MV-03 and MV-17; never infer scientific equivalence from IDs."""
import copy,unittest
from exam_mastery.common import ContractError
from exam_mastery.math_visual_qa import check_lab_scope
from exam_mastery.scientific_visuals import check_solution_figures

class AcceptanceBlockerTests(unittest.TestCase):
 def test_selected_pairs_do_not_exhaust_retention_lab(self):
  lab={'kind':'numeric','math_id':'retention','numeric':{'variable':'M','min':5,'max':20,'step':1,'constants':{'r':.8},'expression':'M*r*(1-r)'}}
  record={'id':'retention','example_scope':{'kind':'exhaustive','variable':'M','inputs':[5,10,15,20]}}
  with self.assertRaisesRegex(ContractError,'not an exhaustive'):check_lab_scope(lab,[record])
  record['example_scope'].update(kind='selected',non_example_probe={'input':6,'expected':.96})
  check_lab_scope(lab,[record])
  bad=copy.deepcopy(record);bad['example_scope']['non_example_probe']['expected']=.8
  with self.assertRaisesRegex(ContractError,'incorrect value'):check_lab_scope(lab,[bad])
  bad=copy.deepcopy(record);bad['example_scope']['non_example_probe']['input']=10
  with self.assertRaisesRegex(ContractError,'interior probe'):check_lab_scope(lab,[bad])
 def test_required_case_diagrams_cannot_be_omitted_or_replaced_by_other_ids(self):
  plan={'visuals':[{'id':'day3-example'},{'id':'alpha-day2'},{'id':'beta-day1'}]}
  item={'solution':'Alpha meets the inclusive deadline; Beta fails lateness.','figure_ids':['day3-example'],'visual_requirements':[{'purpose':'Separate case timelines','case_scope':'Alpha notice day2; Beta notice day1','figure_ids':['alpha-day2','beta-day1']}]}
  with self.assertRaisesRegex(ContractError,'not attached'):check_solution_figures({'items':[item]},plan)
  item['figure_ids']=['alpha-day2','beta-day1'];check_solution_figures({'items':[item]},plan)
  missing=copy.deepcopy(plan);missing['visuals'].pop()
  with self.assertRaises(ContractError):check_solution_figures({'items':[item]},missing)

 def test_explicit_global_usage_limit_is_classified_without_retry(self):
  import tempfile
  from pathlib import Path
  from unittest.mock import patch
  from exam_mastery.providers import Provider,ProviderError
  with tempfile.TemporaryDirectory() as d,patch('exam_mastery.providers.shutil.which',return_value='/test/codex'),patch('exam_mastery.providers.execute',return_value=(1,"You've hit your usage limit. Try later.",'',False)) as execute:
   from exam_mastery.budget import ResourceBudget
   with self.assertRaises(ProviderError) as raised:Provider(budget=ResourceBudget({'approval_id':'test','max_requests':5,'max_input_tokens':10**6,'max_output_tokens':10**6,'max_wall_seconds':600,'max_retries':1,'max_input_tokens_per_call':10**5,'max_output_tokens_per_call':10**4,'input_overhead_tokens_per_call':0,'image_input_tokens':0},Path(d)/'budget')).ask('probe','JSON only',d)
   self.assertEqual(raised.exception.record['classification'],'USAGE_LIMIT')
   self.assertEqual(execute.call_count,1)

 def test_pending_diagram_can_reach_revision_but_cannot_publish(self):
  item={'solution':'Required exact new-case timeline remains pending.','visual_requirements':[{'purpose':'Timeline','case_scope':'Alpha notice day2','figure_ids':[]}]}
  check_solution_figures({'items':[item]},{'visuals':[]},allow_pending=True)
  with self.assertRaisesRegex(ContractError,'lacks figure identities'):check_solution_figures({'items':[item]},{'visuals':[]})

 def test_original_unqualified_finite_membership_cannot_bypass_scope_metadata(self):
  lab={'kind':'numeric','math_id':'retention','numeric':{'variable':'M','min':5,'max':20,'step':1,'constants':{'r':.8},'expression':'M*r*(1-r)'}}
  record={'id':'retention','tex':r'(M,L_1)\in\{(5,.8),(10,1.6),(15,2.4),(20,3.2)\}'}
  with self.assertRaisesRegex(ContractError,'requires explicit example_scope'):check_lab_scope(lab,[record])

 def test_partial_production_quota_stops_before_aggregate_model_calls(self):
  import tempfile,json
  from pathlib import Path
  from unittest.mock import patch,Mock
  from exam_mastery.runtime import run
  from exam_mastery.providers import ProviderError
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'source';root.mkdir();(root/'lecture.md').write_text('Synthetic quota boundary')
   provider=Mock();provider.fingerprint.return_value={'name':'isolated-test'}
   def build(root,out,cache):
    manifest={'sources':[],'online_sources':[]};units=[{'id':'u1','segments':[{'id':'s1'}]},{'id':'u2','segments':[{'id':'s2'}]},{'id':'u3','segments':[{'id':'s3'}]}]
    (out/'source_manifest.json').write_text(json.dumps(manifest));(out/'work_units.json').write_text(json.dumps(units));(out/'corpus.sqlite3').write_bytes(b'test-only')
    return manifest,units
   calls=[]
   def produce(root,manifest,unit,out,provider,course,plan_only=False):
    out.mkdir(parents=True,exist_ok=True)
    if plan_only:
     bp={'competencies':[{'id':unit['id']+':C'}],'units':[]};(out/'blueprint_namespaced.json').write_text(json.dumps(bp));return bp,None
    calls.append(unit['id'])
    if unit['id']=='u2':raise ProviderError('Explicit global usage limit',{'classification':'USAGE_LIMIT'})
    (out/'architect.json').write_text('{"title":"Synthetic unit"}')
    return {'source_segment_ids':['s1']},{'technical_status':'PASS'}
   with patch('exam_mastery.runtime.build',side_effect=build),patch('exam_mastery.runtime.produce_unit',side_effect=produce),patch('exam_mastery.runtime.engine_snapshot',return_value={'test-only':'stable'}):
    out,status=run(root,provider,Path(d)/'output')
   self.assertEqual(calls,['u1','u2']);provider.ask.assert_not_called()
   self.assertTrue(status['resumable']);self.assertEqual(status['status'],'NO_GO')
   coverage=json.loads((out/'production_coverage.json').read_text())
   self.assertFalse(coverage['all_segments_processed']);self.assertEqual(coverage['processed_segment_ids'],['s1'])

 def test_separate_package_rebuild_updates_under_native_default_no_merge(self):
  import tempfile,json
  from pathlib import Path
  from anki.collection import Collection,ImportAnkiPackageRequest,ImportAnkiPackageOptions
  from exam_mastery.publish import publish_cards
  from exam_mastery.anki_qa import verify
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);bp={'title':'Synthetic independent rebuild','course_id':'acceptance-stable-model'}
   design={'theme':{'ink':'#123456','surface':'#ffffff','paper':'#ffffff','accent':'#225588'}}
   paths=[]
   for variant,answer in [('base','Initial answer'),('update','Changed independent export')]:
    out=root/variant;out.mkdir();(out/'architect.json').write_text(json.dumps(bp))
    cards={'cards':[{'id':'stable-operation','question':'What is the controlled test answer?','answer':answer,'explanation':'Synthetic regression only.','source_refs':['synthetic:p1'],'competency_ids':['C1']}]}
    publish_cards(bp,cards,design,out/'artifacts/anki');verify(out);paths.append(out/'artifacts/anki/Anki_Karten.apkg')
   target=Collection(str(root/'native-default.anki2'))
   try:
    options=ImportAnkiPackageOptions(merge_notetypes=False,with_scheduling=False,with_deck_configs=False)
    target.import_anki_package(ImportAnkiPackageRequest(package_path=str(paths[0]),options=options))
    nid=target.db.scalar('select id from notes');note=target.get_note(nid);mid=note.mid
    card=note.cards()[0];card.reps=4;card.ivl=9;target.update_card(card)
    target.db.execute('insert into revlog(id,cid,usn,ease,ivl,lastIvl,factor,time,type) values(?,?,?,?,?,?,?,?,?)',123456789,card.id,-1,4,9,0,2500,1000,1)
    before=target.db.all('select id,nid,reps,ivl from cards order by id');logs=target.db.all('select * from revlog')
    target.import_anki_package(ImportAnkiPackageRequest(package_path=str(paths[1]),options=options))
    self.assertEqual(target.note_count(),1);self.assertEqual(target.get_note(nid).mid,mid)
    self.assertEqual(target.get_note(nid)['Answer'],'Changed independent export')
    self.assertEqual(target.db.all('select id,nid,reps,ivl from cards order by id'),before)
    self.assertEqual(target.db.all('select * from revlog'),logs)
   finally:target.close()

 def test_entire_available_course_is_planned_before_any_products(self):
  import tempfile,json
  from pathlib import Path
  from unittest.mock import patch,Mock
  from exam_mastery.runtime import run
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'sources';root.mkdir();(root/'lecture.md').write_text('Synthetic index ordering')
   calls=[];provider=Mock();provider.fingerprint.return_value={'name':'test-only'}
   def build(root,out,cache):
    manifest={'sources':[],'online_sources':[],'coverage_complete':True};units=[{'id':u,'segments':[{'id':u+':S'}]} for u in ['u1','u2']]
    (out/'source_manifest.json').write_text(json.dumps(manifest));(out/'work_units.json').write_text(json.dumps(units));(out/'corpus.sqlite3').write_bytes(b'flow-only')
    return manifest,units
   def produce(root,manifest,unit,out,provider,course,plan_only=False):
    out.mkdir(parents=True,exist_ok=True);calls.append(('plan' if plan_only else 'produce',unit['id']))
    if plan_only:
     bp={'competencies':[{'id':unit['id']+':C'}],'units':[]};(out/'blueprint_namespaced.json').write_text(json.dumps(bp));return bp,None
    index=json.loads((out.parents[1]/'course_competency_index.json').read_text())
    self.assertTrue(index['all_indexed_transport_units_planned']);self.assertEqual(len(index['competencies']),2)
    raise RuntimeError('Deliberate stop after verifying the index barrier; no fake product')
   with patch('exam_mastery.runtime.build',side_effect=build),patch('exam_mastery.runtime.produce_unit',side_effect=produce),patch('exam_mastery.runtime.engine_snapshot',return_value={'synthetic':'stable'}):
    out,status=run(root,provider,Path(d)/'output')
   self.assertEqual(calls,[('plan','u1'),('plan','u2'),('produce','u1'),('produce','u2')]);provider.ask.assert_not_called()
   self.assertFalse(status['academic_release'])
 def test_source_image_cache_rejects_missing_coverage_and_corrupt_png(self):
  import tempfile,json,pymupdf
  from pathlib import Path
  from exam_mastery.corpus import prepare_visuals
  from exam_mastery.common import sha_file
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pdf=root/'lecture.pdf';doc=pymupdf.open();page=doc.new_page();page.insert_text((50,50),'Synthetic source image');doc.save(pdf);doc.close()
   manifest={'sources':[{'id':'src-demo','path':'lecture.pdf','origin':'local','format':'.pdf','sha256':sha_file(pdf)}]}
   unit={'segments':[{'id':'S1','source_id':'src-demo','source_sha256':sha_file(pdf),'locator':'src-demo:p1:char1-22','page_locator':'src-demo:p1','visual':True}]}
   out=root/'run/units/u1';out.mkdir(parents=True)
   images,gaps=prepare_visuals(root,manifest,unit,out);image=Path(images[0]['path']);original=sha_file(image);modified=image.stat().st_mtime_ns
   prepare_visuals(root,manifest,unit,out);self.assertEqual(image.stat().st_mtime_ns,modified)
   image.write_bytes(b'corrupt');restored,_=prepare_visuals(root,manifest,unit,out);self.assertEqual(sha_file(Path(restored[0]['path'])),original)
   register=json.loads((out/'visual_register.json').read_text());register['images']=[];(out/'visual_register.json').write_text(json.dumps(register))
   rebuilt,_=prepare_visuals(root,manifest,unit,out);self.assertEqual(len(rebuilt),1);self.assertEqual(sha_file(Path(rebuilt[0]['path'])),original)
