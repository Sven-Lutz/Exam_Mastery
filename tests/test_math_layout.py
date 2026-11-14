import sys,unittest,tempfile,copy,json
from pathlib import Path
s=Path(__file__).resolve().parents[1];sys.path.insert(0,str(s))
from exam_mastery.publish import publish_all
from playwright.sync_api import sync_playwright
import pymupdf

def collisions(path):
 result=[]
 with pymupdf.open(path) as doc:
  for i,page in enumerate(doc):
   images=[pymupdf.Rect(img['bbox']) for img in page.get_image_info()]
   glyphs=[pymupdf.Rect(d['rect']) for d in page.get_drawings() if d['type'] in ('f','fs') and 1<d['rect'].width<60 and 1<d['rect'].height<30 and any(item[0]!='re' for item in d['items'])]
   images+=glyphs
   texts=[pymupdf.Rect(span['bbox']) for block in page.get_text('dict')['blocks'] if block['type']==0 for line in block['lines'] for span in line['spans']]
   for a in images:
    for b in texts:
     box=a&b
     if not box.is_empty and box.width>1 and box.height>1:result.append({'page':i+1,'image':list(a),'text':list(b)})
 return result
class MathLayoutTests(unittest.TestCase):
 def test_multiline_inline_equations_do_not_overlap_pdf_text(self):
  f=s/'fixtures/synthetic_responses';data={n:json.loads((f/(n+'.json')).read_text()) for n in ('architect','author','assessment','cards','interaction','design')}
  source=json.loads((s/'fixtures/math_visual_benchmark/after_author.json').read_text());data['author']=source
  with tempfile.TemporaryDirectory() as d:
   publish_all(*[data[n] for n in ('architect','author','assessment','cards','interaction','design')],Path(d))
   pdf=Path(d)/'artifacts/learning_package.pdf'
   with pymupdf.open(pdf) as doc:self.assertGreater(sum(len(page.get_drawings()) for page in doc),50,'Actual formula vectors must exist; an empty-image check is insufficient')
   self.assertEqual(collisions(pdf),[])
if __name__=='__main__':unittest.main()
