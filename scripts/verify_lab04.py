#!/usr/bin/env python3
"""Offline browser/PDF acceptance for a local integrate_lab04 output. Usage: python scripts/verify_lab04.py OUTPUT
No provider, network or model calls. Saves technical QA, never human judgments.
"""
import json,hashlib,shutil,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import pymupdf
out=Path(sys.argv[1]).resolve(); qa=out/'qa';qa.mkdir(exist_ok=True)
lab=out/'Lernumgebung/labs/pricing__van-westendorp.html'
errors=[];requests=[];checks={}
with sync_playwright() as p:
 b=p.chromium.launch()
 c=b.new_context(offline=True,viewport={'width':1280,'height':950});pg=c.new_page()
 pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.on('console',lambda e:errors.append(e.text) if e.type=='error' else None)
 pg.on('request',lambda r:requests.append(r.url) if not r.url.startswith(('file:','data:')) else None)
 pg.goto((out/'Lernumgebung/index.html').as_uri());pg.wait_for_function('document.documentElement.dataset.emReady==="1"')
 links=pg.locator('a[href^="labs/"]');checks['four_reference_links']=links.count()==4
 for href in links.evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))'):
  checks[href]=(out/'Lernumgebung'/href).is_file()
 pg.goto(lab.as_uri());pg.wait_for_function('document.documentElement.dataset.emReady==="1"')
 pg.get_by_text('Ohne Vorhersage erkunden',exact=False).click()
 binding=json.loads((out/'source_binding.json').read_text());checks['real_ent_kc']=all(k in pg.inner_text('body') for k in binding['request']['kc_ids'])
 checks['real_source_page']='S. 24' in pg.inner_text('.em-notes')
 checks['synthetic_declared']='SYNTHETISCHE' in pg.inner_text('body')
 checks['n_valid_240']=pg.get_attribute('.em-lab','data-n-valid')=='240'
 checks['js_opp_display']='49,89' in pg.inner_text('.em-lab .em-kpi')
 pg.screenshot(path=str(qa/'desktop.png'),full_page=True)
 pg.set_viewport_size({'width':390,'height':844});pg.emulate_media(color_scheme='dark');pg.screenshot(path=str(qa/'mobile-dark.png'),full_page=True)
 checks['mobile_no_overflow']=pg.evaluate('document.documentElement.scrollWidth<=390')
 pg.goto((out/'chapter_07/publish/artifacts/Lernumgebung/index.html').as_uri());checks['canonical_chapter_lab_link']=pg.locator('a[href="labs/pricing__van-westendorp.html"]').count()==1
 c.close();b.close()
pdf=out/'Lernumgebung/Lab04_Van_Westendorp.pdf';d=pymupdf.open(pdf)
for i,pg in enumerate(d):pg.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(str(qa/f'pdf-{i+1}.png'))
text=''.join(pg.get_text() for pg in d)
checks['pdf_synthetic']='SYNTHETISCHE' in text
checks['pdf_source']='S. 24' in text
checks['pdf_opp_display']='49,89' in text
book=pymupdf.open(out/'chapter_07/publish/artifacts/1_Lehrbuch.pdf')
labpages=[(i,pg) for i,pg in enumerate(book) if 'Van Westendorp: Wo liegt' in pg.get_text()]
checks['chapter_pdf_lab_included']=bool(labpages)
for i,pg in labpages:pg.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(str(qa/f'chapter-lab-page-{i+1}.png'))
checks['no_browser_errors']=not errors;checks['zero_external_requests']=not requests
receipt={'checks':checks,'errors':errors,'external_requests':requests,'pdf_pages':len(d),'result':'PASS' if all(checks.values()) else 'FAIL','free_GiB':shutil.disk_usage(out).free/1024**3}
(qa/'browser_pdf_acceptance.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt,indent=2));assert all(checks.values())
