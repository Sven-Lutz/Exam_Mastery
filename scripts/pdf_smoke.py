import argparse,sys
from pathlib import Path
import fitz
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);args=p.parse_args()
f=args.run/'artifacts'/'learning_package.pdf';doc=fitz.open(f);issues=[]
for n,page in enumerate(doc,1):
    if not page.get_text().strip():issues.append(f'page {n} empty')
    for b in page.get_text('blocks'):
        if len(b)<5 or not b[4].strip():continue
        x0,y0,x1,y1=b[:4]
        if x0 < 20 or y0<15 or x1>page.rect.width-15 or y1>page.rect.height-10:issues.append(f'page {n}: text outside margin {(x0,y0,x1,y1)}')
print('PDF QA', 'PASS' if not issues else 'FAIL', 'pages',len(doc))
for issue in issues:print(' -',issue)
sys.exit(1 if issues else 0)
