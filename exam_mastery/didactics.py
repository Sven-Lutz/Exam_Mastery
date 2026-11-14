"""Falsifiable structural gates; never a scientific or learning-outcome approval."""
import html
from .common import ContractError

def check_prerequisites(plan,bp):
    units={u['id'] for u in bp['units']}
    checks=plan.get('prerequisite_checks',[])
    if {c.get('unit_id') for c in checks}!=units:
        raise ContractError('Entry checks must cover every exact learning unit ID')
    fields=('prerequisite','prompt','solution','pass_criterion','error_diagnosis','remediation','retry_prompt','retry_solution')
    for c in checks:
        if any(not isinstance(c.get(k),str) or not c[k].strip() for k in fields):
            raise ContractError('Entry check lacks answer, diagnosis, repair or retry')
        if c['prompt'].strip()==c['retry_prompt'].strip():raise ContractError('Retry must be a new task')

def check_marking(assess):
    for a in assess['items']:
        if any(not a.get('marking_policy',{}).get(k,'').strip() for k in ('method_credit','follow_through','alternatives')):
            raise ContractError('Missing method credit, follow-through or alternative marking rules')
        if any(not r.get('partial_credit','').strip() for r in a['rubric']):raise ContractError('Missing explicit partial credit')
        ds=a.get('error_diagnoses',[])
        if not ds or any(not d.get(k,'').strip() for d in ds for k in ('error','diagnosis','remediation')):
            raise ContractError('Missing actionable error diagnosis')

def coverage_matrix(bp,assess,cards,plan):
    methods={r['competency_id']:r for r in plan['competency_methods']}
    rows=[]
    for c in bp['competencies']:
        tasks=[a for a in assess['items'] if c['id'] in a['competency_ids']]
        notes=[a['id'] for a in cards['cards'] if c['id'] in a['competency_ids']]
        method=methods[c['id']]
        if not tasks:raise ContractError('Competency lacks assessment: '+c['id'])
        if not notes and (method['retrieval_suitable'] or not method.get('retrieval_rationale','').strip()):
            raise ContractError('Unjustified Anki gap: '+c['id'])
        rows.append({'competency_id':c['id'],'operation':c['operation'],'source_refs':c['source_refs'],
                     'assessment_ids':[a['id'] for a in tasks], 'required_operations':sorted({o for a in tasks for o in a['required_operations']}),
                     'card_ids':notes,'retrieval_rationale':method['retrieval_rationale'],
                     'status':'COVERED' if notes else 'JUSTIFIED_NO_CARDS',
                     'scope':'Structural links; semantic alignment and independent performance remain reviewable'})
    return {'schema':'em-competency-coverage-v1','rows':rows,'academic_release':False}

def publish_support(out,matrix):
    esc=html.escape
    table='<section id="coverage"><h2>Competency coverage</h2><p>Cards retrieve components. Full competence requires independent task performance.</p><table><thead><tr><th>Competency / operation</th><th>Tasks</th><th>Anki / rationale</th></tr></thead><tbody>'
    for r in matrix['rows']:
        table+='<tr><td>'+esc(r['competency_id']+' / '+r['operation'])+'</td><td>'+esc(', '.join(r['assessment_ids']))+'</td><td>'+esc(', '.join(r['card_ids'])+' — '+r['retrieval_rationale'])+'</td></tr>'
    table+='</tbody></table></section>'
    f=out/'artifacts/web/index.html';f.write_text(f.read_text().replace('</main>',table+'</main>'))
