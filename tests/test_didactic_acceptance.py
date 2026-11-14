import copy,unittest
from exam_mastery.didactics import check_prerequisites,check_marking,coverage_matrix
from exam_mastery.common import ContractError
class DidacticGateTests(unittest.TestCase):
 def test_entry_checks_require_repair_and_new_retry(self):
  bp={'units':[{'id':'unit:U1'}]}
  c={k:'concrete response' for k in ('prerequisite','prompt','solution','pass_criterion','error_diagnosis','remediation','retry_solution')};c.update(unit_id='unit:U1',retry_prompt='new task')
  check_prerequisites({'prerequisite_checks':[c]},bp)
  for field in ('solution','remediation','retry_solution'):
   bad=copy.deepcopy(c);del bad[field]
   with self.assertRaises(ContractError):check_prerequisites({'prerequisite_checks':[bad]},bp)
  c['retry_prompt']=c['prompt']
  with self.assertRaises(ContractError):check_prerequisites({'prerequisite_checks':[c]},bp)
 def test_final_solver_cannot_discard_marking_rules(self):
  a={'rubric':[{'partial_credit':'1 for correct method, 1 for result'}],'marking_policy':dict(method_credit='credit method',follow_through='penalize once',alternatives='equivalent proof'),'error_diagnoses':[dict(error='wrong base',diagnosis='uses final value',remediation='divide by initial value')]}
  check_marking({'items':[a]});del a['marking_policy']['follow_through']
  with self.assertRaises(ContractError):check_marking({'items':[a]})
 def test_anki_omission_needs_per_competency_justification(self):
  bp={'competencies':[dict(id='u:C3',operation='critique',source_refs=['s:p1'])]};tasks={'items':[dict(id='A3',competency_ids=['u:C3'],required_operations=['critique'])]};cards={'cards':[]}
  plan={'competency_methods':[dict(competency_id='u:C3',retrieval_suitable=True,retrieval_rationale='retrieve evidence distinction')]}
  with self.assertRaises(ContractError):coverage_matrix(bp,tasks,cards,plan)
  plan['competency_methods'][0]['retrieval_suitable']=False
  self.assertEqual(coverage_matrix(bp,tasks,cards,plan)['rows'][0]['status'],'JUSTIFIED_NO_CARDS')

class NumericOracleTests(unittest.TestCase):
 def test_actual_javascript_evaluator_matches_independent_iterated_losses(self):
  import json,subprocess
  from decimal import Decimal
  from pathlib import Path
  from exam_mastery.publish import _ast_json
  from exam_mastery.validate import numeric_ast,evaluate_numeric
  expression='initial_mass*retention*(1-retention)'
  tree=_ast_json(numeric_ast(expression,{'initial_mass','retention'}))
  js=(Path(__file__).resolve().parents[1]/'exam_mastery/templates/lab.js').read_text()
  evaluator=js[js.index('function ev('):js.index('const predict=')]
  cases=[]
  for r in ('0','0.6','0.8','1'):
   for mass in range(5,21):
    initial=Decimal(mass);retention=Decimal(r)
    first=initial*retention;second=first*retention
    oracle=float(first-second)
    env={'initial_mass':mass,'retention':float(r)}
    self.assertAlmostEqual(evaluate_numeric(expression,env),oracle,places=10)
    cases.append(dict(env=env,expected=oracle))
  program=evaluator+'\nconst tree='+json.dumps(tree)+';const cases='+json.dumps(cases)+';for(const c of cases){if(Math.abs(ev(tree,c.env)-c.expected)>1e-10)throw Error("Independent oracle mismatch")}process.stdout.write(String(cases.length));'
  result=subprocess.run(['node','-e',program],capture_output=True,text=True,check=True)
  self.assertEqual(result.stdout,'64')

class RenderEvidenceTests(unittest.TestCase):
 def test_shorter_rerender_cannot_leave_stale_pages_for_visual_audit(self):
  import tempfile
  from pathlib import Path
  from exam_mastery.quality import retire_rendered_pages
  with tempfile.TemporaryDirectory() as d:
   run=Path(d);pages=run/'rendered';pages.mkdir();(pages/'page-14.png').write_bytes(b'old page evidence')
   retire_rendered_pages(run)
   self.assertFalse(list(pages.glob('page-*.png')))
   history=list((run/'rendered_history').glob('page-14-*.png'))
   self.assertEqual(len(history),1);self.assertEqual(history[0].read_bytes(),b'old page evidence')
