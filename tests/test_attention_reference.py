"""Separate arithmetic paths, adversarial examples and real learner interactions.

These establish bounded model/renderer facts, not full proof review or learning
outcomes. Decimal reference does not call the production attention algorithm.
"""
import copy
from decimal import Decimal, localcontext
from itertools import product
import json
from pathlib import Path
import random
import subprocess

import pytest
from exam_mastery.labs.models import scaled_attention
from exam_mastery.learning import experience as ex
from exam_mastery.learning import interactive_reference as ir

ROOT = Path(__file__).resolve().parents[1]


def unit(): return json.loads((ROOT/'fixtures/experience_attention_reference.json').read_text())
def parameters(): return unit()['interactions'][0]['variants'][0]['parameters']


def decimal_reference(p):
    with localcontext() as ctx:
        ctx.prec=65
        q,k,v=[[[Decimal(str(x)) for x in r] for r in p[name]] for name in ('Q','K','V')]
        divisor=Decimal(len(q[0])).sqrt() if p.get('scaled',True) else Decimal(1)
        temp=Decimal(str(p.get('temperature',1)))
        mask=p.get('mask',[[True]*len(k) for _ in q])
        a=[]
        for i,row in enumerate(q):
            # Independent direct Decimal exponentiation, no max-shift.
            e=[(sum(x*y for x,y in zip(row,key))/divisor/temp).exp() if mask[i][j] else Decimal(0)
               for j,key in enumerate(k)]
            a.append([x/sum(e) for x in e])
        out=[[sum(a[i][j]*v[j][r] for j in range(len(k))) for r in range(len(v[0]))] for i in range(len(q))]
        return [[float(x) for x in r] for r in a],[[float(x) for x in r] for r in out]


def test_full_example_against_independent_decimal_and_dimensions():
    p=parameters();m=scaled_attention(p);weights,out=decimal_reference(p)
    assert m['shape']=={'n_q':2,'n_k':3,'d_k':2,'d_v':2}
    assert m['raw']==[[1,0,-1],[0,1,0]]
    for x,y in zip(m['weights'],weights):assert x==pytest.approx(y,abs=2e-15)
    for x,y in zip(m['output'],out):assert x==pytest.approx(y,abs=2e-15)
    assert m['output'][0]==pytest.approx([1.43200918051748,0.848049309569276])


def test_browser_model_matches_decimal_across_shapes_and_masks():
    randomizer=random.Random(20261126);cases=[]
    for _ in range(35):
        m,n,d,v=[randomizer.randint(1,4) for _ in range(4)]
        p={name:[[randomizer.uniform(-3,3) for _ in range(cols)] for _ in range(rows)]
           for name,rows,cols in [('Q',m,d),('K',n,d),('V',n,v)]}
        p.update(scaled=randomizer.choice([True,False]),temperature=randomizer.choice([.05,1,20]))
        p['mask']=[[j==0 or randomizer.choice([True,False]) for j in range(n)] for _ in range(m)]
        cases.append(p)
    js=(ROOT/'exam_mastery/templates/attention_math.js').read_text()
    run=subprocess.run(['node','-e',js+';const fs=require("fs");process.stdout.write(JSON.stringify(JSON.parse(fs.readFileSync(0,"utf8")).map(EMAttention.compute)));'],input=json.dumps(cases),capture_output=True,text=True,check=True)
    for p,actual in zip(cases,json.loads(run.stdout)):
        weights,out=decimal_reference(p);py=scaled_attention(p)
        for expected,jsrow,pyrow in zip(weights,actual['weights'],py['weights']):
            assert jsrow==pytest.approx(expected,abs=2e-13)
            assert pyrow==pytest.approx(expected,abs=2e-13)
        for expected,jsrow in zip(out,actual['output']):assert jsrow==pytest.approx(expected,abs=2e-12)


@pytest.mark.parametrize('change',[
 {'Q':[[True,0]]},{'K':[[1],[2]]},{'V':[[1]]},{'Q':[[float('nan'),0]]},
 {'Q':[[float('inf'),0]]},{'Q':[[10001,0]]},{'temperature':0},{'temperature':True},
 {'mask':[[False]*3,[True]*3]},{'mask':[[1]*3,[True]*3]},{'Q':[[1],[1,2]]},{'evil':'code'}])
def test_unsafe_or_undefined_model_is_rejected(change):
    p=parameters();p.update(change)
    with pytest.raises(ValueError):scaled_attention(p)
    # JSON serializable cases are also checked in JS; nonfinite values covered separately by real input tests.
    if not any('nan' in str(v).lower() or 'inf' in str(v).lower() for v in change.values()):
        js=(ROOT/'exam_mastery/templates/attention_math.js').read_text()
        code=js+';try{EMAttention.compute('+json.dumps(p)+');process.exit(1)}catch(e){process.exit(0)}'
        assert subprocess.run(['node','-e',code]).returncode==0


def test_masked_maximum_and_identical_values_do_not_produce_false_explanations():
    p={'Q':[[1]],'K':[[10000],[-10000]],'V':[[9],[4]],'mask':[[False,True]]}
    assert scaled_attention(p)['weights']==[[0,1]]
    assert scaled_attention(p)['output']==[[4]]
    p=parameters();p['V']=[[2,-1]]*3
    assert scaled_attention(p)['output'][0]==pytest.approx([2,-1])
    p['Q']=[[9,-4],[8,1]]
    assert scaled_attention(p)['output'][0]==pytest.approx([2,-1])


def test_joint_permutation_and_value_only_intervention():
    p=parameters();m=scaled_attention(p);order=[2,0,1]
    p['K']=[p['K'][i] for i in order];p['V']=[p['V'][i] for i in order]
    p['mask']=[[r[i] for i in order] for r in p['mask']]
    for a,b in zip(scaled_attention(p)['output'],m['output']):assert a==pytest.approx(b)
    p=parameters();p['V'][0][0]+=2
    changed=scaled_attention(p)
    assert changed['weights']==m['weights']
    assert changed['output'][0][0]-m['output'][0][0]==pytest.approx(2*m['weights'][0][0])


def test_independent_discrete_variance_and_correlated_counterexample():
    d=3
    independent=[sum(q[i]*k[i] for i in range(d)) for q in product([-1,1],repeat=d) for k in product([-1,1],repeat=d)]
    assert sum(x*x for x in independent)/len(independent)==d
    correlated=[d*x*y for x,y in product([-1,1],repeat=2)]
    assert sum(x*x for x in correlated)/len(correlated)==d*d
    assert sum((x/d**.5)**2 for x in correlated)/len(correlated)==pytest.approx(d)


def test_registry_security_and_graphic_reference_fail_closed():
    u=unit();assert ex.validate(u)['valid']
    u['mathematics'][0]['tex']=r'\href{https://evil.invalid}{x}'
    assert not ex.validate(u)['valid']
    u=unit();u['graphics'][0]['keyframes']=[99]
    assert not ex.validate(u)['valid']
    u=unit();u['teaching'][0]['content']='[[math:missing]]'
    assert not ex.validate(u)['valid']


def test_real_browser_math_interventions_and_mask_error(tmp_path):
    from playwright.sync_api import sync_playwright
    ir.publish(unit(),tmp_path)
    with sync_playwright() as pw:
        browser=pw.chromium.launch();page=browser.new_page(viewport={'width':390,'height':850})
        errors=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r: requests.append(r.url) if r.url.startswith(('http:','https:')) else None)
        page.goto((tmp_path/'Interaktiv/index.html').as_uri())
        assert page.locator('.em-math svg').count()>15
        assert page.locator('a[href="https://arxiv.org/pdf/1909.03469"]').count()==1
        assert page.locator('.proof-equation code').count()==0
        root=page.locator('.attention-lab');before=json.loads(root.get_attribute('data-model'))
        root.locator('input[data-matrix=V]').first.fill('4')
        after=json.loads(root.get_attribute('data-model'))
        assert after['weights']==before['weights']
        assert after['output'][0][0]>before['output'][0][0]
        root.locator('input[data-matrix=Q]').first.fill('2')
        assert json.loads(root.get_attribute('data-model'))['weights']!=before['weights']
        root.locator('summary').filter(has_text='Maske:').click()
        for check in root.locator('.attention-masks input').all()[:3]:check.uncheck()
        assert 'undefiniert' in root.locator('.attention-status').inner_text()
        assert root.get_attribute('data-model')==''
        root.locator('.attention-reset').click()
        assert json.loads(root.get_attribute('data-model'))['output']==before['output']
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
        assert not errors and not requests
        browser.close()


def test_softmax_jacobian_exact_symbolic_reference():
    import sympy as sp
    a,b,c=sp.symbols('a b c',real=True)
    zs=[a,b,c];den=sum(sp.exp(x) for x in zs);weights=[sp.exp(x)/den for x in zs]
    for j in range(3):
        for ell in range(3):
            assert sp.simplify(sp.diff(weights[j],zs[ell])-weights[j]*((1 if j==ell else 0)-weights[ell]))==0


def test_graphic_is_shared_with_pdf_and_workbook():
    from exam_mastery.learning.experience_books import book_model, _combined_workbook
    from exam_mastery import typeset
    u=json.loads((ROOT/'fixtures/experience_binomial_reference.json').read_text())
    book=book_model(u)
    assert len(book['figures'])==1
    body,_=typeset.textbook(book);work,_=_combined_workbook(book)
    assert '<svg' in body and '<svg' in work
    assert 'Vier disjunkte Teilflächen' in body and 'Vier disjunkte Teilflächen' in work
    assert 'Vier disjunkte Teilflächen' in ir.render_html(u)


def test_authorship_disclosure_reaches_published_book_model():
    from exam_mastery.learning.experience_books import book_model
    model=book_model(unit())
    assert 'keine automatische Kursautorenschaft' in model['production_notes']
    assert 'keine unabhängige Person oder Fachabnahme' in model['production_notes']
