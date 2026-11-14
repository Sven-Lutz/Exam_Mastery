#!/usr/bin/env python3
"""Visual smoke against web lab + Anki CSS using installed Playwright/Chromium.

Does not claim real AnkiMobile/AnkiDroid client compatibility.
"""
import argparse,html,sys,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args()
root=args.run/'artifacts';page_text=(root/'web'/'index.html').read_text(encoding='utf-8')
card_text=(root/'anki'/'anki_import.tsv').read_text(encoding='utf-8').splitlines()[-1].split('\t')
css=(root/'anki'/'anki_style.css').read_text(encoding='utf-8');front=(root/'anki'/'anki_front.html').read_text(encoding='utf-8').replace('{{Question}}',card_text[1]);back=(root/'anki'/'anki_back.html').read_text(encoding='utf-8').replace('{{Question}}',card_text[1]).replace('{{Answer}}',card_text[2]).replace('{{Explanation}}',card_text[3]).replace('{{Source}}',card_text[4]);errors=[]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None,headless=True,args=['--no-sandbox'])
    for width in (320,390,768,1280):
        page=browser.new_page(viewport={'width':width,'height':780})
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.set_content(page_text)
        if page.evaluate('document.documentElement.scrollWidth > innerWidth'):errors.append(f'Web overflow width={width}')
        if page.locator('#lab-root input[type=range]').count():
            page.locator('input[name=prediction][value=up]').check()
            page.locator('#lab-root button').click()
            page.locator('#lab-root input[type=range]').fill('0.1')
            if not page.locator('#lab-root .measure').inner_text().strip():errors.append('numeric result missing')
            if not page.locator('#lab-root svg[role=img]').count():errors.append('numeric response graph missing')
        if width==390:page.screenshot(path=str(args.run/'web-mobile.png'),full_page=True)
        page.close()
        for night in ('','nightMode'):
            for view in (front,back):
                card=browser.new_page(viewport={'width':width,'height':780})
                card.set_content(f'<style>{css}</style><div class="card {night}">{view}</div>')
                if card.evaluate('document.documentElement.scrollWidth > innerWidth'):errors.append(f'Anki overflow width={width} theme={night}')
                card.close()
    browser.close()
print('BROWSER QA', 'PASS' if not errors else 'FAIL', 'widths=320,390,768,1280; web + Anki front/back light/dark')
for error in errors:print(' -',error)
sys.exit(1 if errors else 0)
