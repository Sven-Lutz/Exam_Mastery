"""Executed technical evidence, explicit academic/visual/client release blockers."""
import csv,io,json,tempfile,math
from pathlib import Path
from .common import read_json,write_json,sha_file

def retire_rendered_pages(run):
    """Keep evidence from earlier renders without auditing stale trailing pages."""
    dest=run/'rendered';dest.mkdir(exist_ok=True)
    for previous in dest.glob('page-*.png'):
        history=run/'rendered_history';history.mkdir(exist_ok=True)
        previous.replace(history/(previous.stem+'-'+sha_file(previous)[:16]+'.png'))
    return dest

def quality(run):
    report={'schema':'em-qa-v2','checks':{},'technical_status':'PASS','release_approved':False}
    def check(name,fn):
        try: report['checks'][name]={'status':'PASS','evidence':fn()}
        except Exception as e:
            report['checks'][name]={'status':'FAIL','error':f'{type(e).__name__}: {e}'};report['technical_status']='FAIL'
    model=read_json(run/'learning_model.json');manifest=read_json(run/'source_manifest.json')
    report['checks']['source_coverage']={'status':'PASS' if manifest.get('coverage_complete') else 'BLOCKED','gaps':[s for s in manifest['sources'] if s['status']!='extracted'],'online':manifest.get('online_sources',[]),'truncated':manifest['truncated']}
    report['checks']['source_visuals']={'status':'BLOCKED' if manifest['requires_visual_review'] else 'NOT_APPLICABLE','reason':'Text extraction does not establish visual comprehension'}
    dispositions=read_json(run/'architect.json').get('source_dispositions',[])
    actual={s['id'] for s in manifest['sources'] if 'id' in s}
    covered={d.get('source_id') for d in dispositions if d.get('disposition')=='covered'}
    report['checks']['semantic_source_coverage']={'status':'PASS' if covered==actual else 'BLOCKED','uncovered_source_ids':sorted(actual-covered),'dispositions':dispositions}
    audit=read_json(run/'audit.json')
    report['checks']['academic_correctness']={'status':'REVIEW_REQUIRED','model_verdict':audit['verdict'],'reason':'Separate model contexts are not external scientific verification','findings':audit['findings']}
    def didactic_contracts():
        from .didactics import check_prerequisites,check_marking,coverage_matrix
        from .validate import check_assess
        units=model.get('units',[model])
        for unit in units:
            bp={'competencies':unit['competencies'],'units':unit['learning_units']}
            check_prerequisites(unit['learning_plan'],bp)
            check_marking({'items':unit['assessments']})
            check_assess({'items':unit['assessments']},bp,manifest)
            from .scientific_visuals import check_solution_figures
            check_solution_figures({'items':unit['assessments']},unit['learning_plan'])
            coverage_matrix(bp,{'items':unit['assessments']},{'cards':unit['flashcards']},unit['learning_plan'])
        return {'units':len(units),'scope':'Executed entry-check, marking and coverage contracts; semantic and empirical review remain required'}
    check('competencies_and_solutions',didactic_contracts)
    def render():
        import pymupdf as fitz
        doc=fitz.open(run/'artifacts/learning_package.pdf');dest=retire_rendered_pages(run)
        if not len(doc):raise ValueError('PDF has no pages')
        for i,page in enumerate(doc):
            if not page.get_text().strip():raise ValueError(f'Empty page {i+1}')
            missing={chr(c[0]) for span in page.get_texttrace() for c in span['chars'] if c[1]==0 and chr(c[0]).strip()}
            if missing:raise ValueError(f'Unsupported PDF prose glyphs on page {i+1}: '+repr(sorted(missing)))
            page.get_pixmap(matrix=fitz.Matrix(1,1)).save(dest/f'page-{i+1}.png')
        split_pages={}
        for name in ('Lehrbuch.pdf','Aufgaben.pdf','Loesungen.pdf'):
            path=run/'artifacts'/name
            if path.exists():
                with fitz.open(path) as split:
                    if not len(split) or any(not p.get_text().strip() for p in split):raise ValueError('Empty split PDF: '+name)
                    split_pages[name]=len(split)
        return {'split_products':split_pages,'pages':len(doc),'scope':'All pages rasterized, text present; human typography/formula review pending'}
    check('pdf_render',render)
    from .math_visual_qa import verify as math_visual_verify
    if read_json(run/'author.json').get('mathematics'):
        check('mathematical_visual_contract',lambda:math_visual_verify(run))
    else:
        report['checks']['mathematical_visual_contract']={'status':'NOT_TESTED','reason':'Legacy/no canonical formula registry; no advanced-math claim'}
    def browser():
        from playwright.sync_api import sync_playwright
        errors=[];web=run/'artifacts/web/index.html'
        cards=run/'artifacts/anki';rows=list(csv.reader(io.StringIO('\n'.join(x for x in (cards/'anki_import.tsv').read_text().splitlines() if not x.startswith('#'))),delimiter='\t'))
        with sync_playwright() as p:
            b=p.chromium.launch(headless=True)
            for width in (320,390,768,1280):
                page=b.new_page(viewport={'width':width,'height':800})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(web.as_uri());page.wait_for_timeout(100)
                if page.evaluate('document.documentElement.scrollWidth>innerWidth'):errors.append(f'web overflow {width}')
                for img in page.locator('img').all():
                    if not img.get_attribute('alt') or not img.evaluate('(e)=>e.complete && e.naturalWidth>0'):errors.append('Image missing, undecodable or without alt text')
                if not page.locator('main h1').count():errors.append('missing main heading')
                for link in page.locator('a[href^="#"]').all():
                    anchor=link.get_attribute('href')[1:]
                    if anchor and not page.locator('[id="'+anchor+'"]').count():errors.append('missing anchor '+anchor)
                for node in page.locator('input').all():
                    if node.get_attribute('type') not in ('radio','hidden') and not node.get_attribute('aria-label'):errors.append('unlabelled input')
                spec=model['interactions'][0]
                if spec['kind']=='numeric':
                    if page.locator('.measure').is_visible():errors.append('Lab reveals outcome before prediction')
                    page.locator('#lab-root button').click()
                    if page.locator('.measure').is_visible():errors.append('Lab accepts missing prediction')
                    page.locator('input[name=prediction]').first.check();page.locator('#lab-root button').click()
                    if page.locator('.measure').is_visible():errors.append('Lab accepts missing reasoning')
                    page.locator('textarea[aria-label="Prediction reasoning"]').fill('Prediction uses the fixed target and stated model assumptions.')
                    page.locator('#lab-root button').click()
                    if page.locator('input[name=prediction]:enabled').count():errors.append('Prediction is not locked')
                    slider=page.locator('input[type=range]')
                    for value in (spec['numeric']['min'],spec['numeric']['max'],spec['numeric']['default']):
                        slider.fill(str(value));slider.dispatch_event('input')
                        from .validate import evaluate_numeric
                        n=spec['numeric'];expected=evaluate_numeric(n['expression'],{**n['constants'],n['variable']:value})
                        displayed=float(page.locator('.measure').inner_text().rsplit(':',1)[1])
                        if not math.isclose(displayed,expected,rel_tol=1e-8,abs_tol=0.000051):errors.append('Wrong lab result')
                        target=n['prediction_target']
                        baseline=evaluate_numeric(n['expression'],{**n['constants'],n['variable']:n['default']})
                        end=evaluate_numeric(n['expression'],{**n['constants'],n['variable']:target})
                        actual='up' if end>baseline+1e-9 else 'down' if end<baseline-1e-9 else 'same'
                        feedback=page.locator('#lab-root').inner_text()
                        if ('Prediction confirmed.' if actual=='up' else 'Prediction not confirmed.') not in feedback:errors.append('Wrong prediction feedback')
                    # Exercise every direction, including wrong predictions, in fresh state.
                    for direction in ('down','same'):
                        page.reload();page.locator('input[name=prediction][value='+direction+']').check();page.locator('textarea[aria-label="Prediction reasoning"]').fill('A deliberate alternative prediction for feedback testing.');page.locator('#lab-root button').click()
                        message='Prediction confirmed.' if actual==direction else 'Prediction not confirmed.'
                        if message not in page.locator('#lab-root').inner_text():errors.append('Prediction feedback path missing')
                elif spec['kind']=='quiz':
                    page.locator('#lab-root button').click()
                    if 'Choose an answer first.' not in page.locator('#lab-root').inner_text():errors.append('Quiz missing-answer gate failed')
                    for index in range(len(spec['quiz']['options'])):
                        page.locator('input[name=answer]').nth(index).check();page.locator('#lab-root button').click()
                        key='feedback_correct' if index==spec['quiz']['correct_index'] else 'feedback_wrong'
                        if spec['quiz'][key] not in page.locator('#lab-root').inner_text():errors.append('Quiz feedback missing')
                if width==390:page.screenshot(path=str(run/'web-mobile.png'),full_page=True)
                page.close()
                for night in ('','nightMode'):
                    for row in rows:
                        for side in ('front','back'):
                            template=(cards/f'anki_{side}.html').read_text()
                            for key,val in zip(('ID','Question','Answer','Explanation','Source'),row):template=template.replace('{{'+key+'}}',val)
                            page=b.new_page(viewport={'width':width,'height':800})
                            page.goto((cards/'anki_front.html').as_uri());page.set_content('<base href="'+(cards/'media').as_uri()+'/"><style>'+ (cards/'anki_style.css').read_text()+'</style><div class="card '+night+'">'+template+'</div>')
                            if page.evaluate('document.documentElement.scrollWidth>innerWidth'):errors.append(f'card overflow {width}')
                            for img in page.locator('img').all():
                                if not img.get_attribute('alt') or not img.evaluate('(e)=>e.complete && e.naturalWidth>0'):errors.append('Anki formula/figure image missing or undecodable')
                            page.close()
            b.close()
        if errors:raise ValueError('; '.join(errors))
        return {'widths':[320,390,768,1280],'card_views':'all front/back light/dark','labs':'executed','accessibility':'landmarks, heading, input labels, overflow; not full WCAG certification'}
    check('browser_html_css_lab_accessibility',browser)
    from .anki_qa import verify
    check('anki_actual_import_reimport',lambda:verify(run))
    report['checks']['anki_native_clients']={'status':'REVIEW_REQUIRED','reason':'Desktop/mobile GUI not automatically verified'}
    report['checks']['didactic_quality']={'status':'REVIEW_REQUIRED','reason':'Independent model audits available; depth, prerequisite scaffolding and transfer require independent assessment'}
    report['checks']['exam_alignment']={'status':'REVIEW_REQUIRED','reason':'Original exam evidence and unknowns are in architect/research; no prediction of future exam content'}
    report['checks']['generalization']={'status':'REVIEW_REQUIRED','reason':'Synthetic contrasting fixtures do not prove universal discipline coverage'}
    dimensions={
        'source_completeness':['source_coverage','semantic_source_coverage','source_visuals'],
        'scientific_correctness':['academic_correctness','competencies_and_solutions'],
        'didactic_quality':['didactic_quality'],
        'exam_alignment':['exam_alignment'],
        'anki_quality':['anki_actual_import_reimport','anki_native_clients'],
        'publishing_quality':['pdf_render','browser_html_css_lab_accessibility'],
        'automation_reliability':['browser_html_css_lab_accessibility','anki_actual_import_reimport'],
        'generalization':['generalization']}
    reviews=run/'reviews';reviews.mkdir(exist_ok=True)
    for dimension,keys in dimensions.items():
        write_json(reviews/(dimension+'.json'),{'dimension':dimension,'release_approved':False,'evidence':{k:report['checks'][k] for k in keys}})
    write_json(run/'quality_report.json',report)
    return report
