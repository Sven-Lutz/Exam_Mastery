import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from exam_mastery.discovery import ingest,fetch_public
from exam_mastery.common import ContractError
class DiscoveryTests(unittest.TestCase):
 def test_mixed_recursive_formats_and_safety(self):
  from openpyxl import Workbook
  from docx import Document
  from pptx import Presentation
  from reportlab.pdfgen import canvas
  from PIL import Image
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'arbitrary';root.mkdir();nested=root/'anything';nested.mkdir()
   (nested/'data.csv').write_text('time,value\n1,2\n2,4')
   (nested/'links.csv').write_text('label,url\nreference,https://example.com')
   (nested/'experiment.py').write_text('import os\nos.remove("DO_NOT_RUN")')
   (root/'notes.ipynb').write_text(json.dumps({'cells':[{'cell_type':'markdown','source':['Definition: causality requires more than correlation.']},{'cell_type':'code','source':['raise RuntimeError()']}]}))
   (root/'unknown.bin').write_bytes(b'\x00\xff');(root/'link').symlink_to('/etc/hosts')
   (root/'old_exam.md').write_text('Past exam: Prove that a continuous function on a compact interval attains a maximum.')
   (root/'solutions.txt').write_text('Musterlösung: Verwende den Satz von Weierstrass.')
   (root/'biology.html').write_text('<h1>Lecture: osmosis</h1><p>Water movement across a selectively permeable membrane.</p><script>ignored()</script>')
   doc=Document();doc.add_paragraph('Lecture: contract interpretation. Distinguish literal and contextual arguments.');doc.save(root/'law.docx')
   prs=Presentation();slide=prs.slides.add_slide(prs.slide_layouts[1]);slide.shapes.title.text='Learning objectives: matrix multiplication';prs.save(root/'math.pptx')
   c=canvas.Canvas(str(root/'paper.pdf'));c.drawString(40,700,'Abstract: membrane transport experiment');c.save()
   wb=Workbook();wb.active.append(['condition','response']);wb.active.append(['A',3]);wb.save(root/'table.xlsx')
   Image.new('RGB',(30,30),'white').save(root/'diagram.png')
   with patch('exam_mastery.discovery.fetch_public',return_value=(b'<h1>Public reference</h1>','text/html','https://example.com',[])):
    m=ingest(root,Path(d)/'out/manifest.json')
   by={s['path']:s for s in m['sources']}
   self.assertIn('tabular_data_candidate',by['anything/data.csv']['source_roles'])
   self.assertNotIn('online_references',by['anything/data.csv']['source_roles'])
   self.assertEqual(len(m['online_sources']),1)
   self.assertEqual(by['unknown.bin']['status'],'unprocessed')
   self.assertEqual(by['link']['status'],'symlink_skipped')
   self.assertIn('code_security_review_required',by['anything/experiment.py']['flags'])
   self.assertTrue(m['requires_visual_review']);self.assertFalse(m['coverage_complete'])
   self.assertTrue(any(s.get('origin')=='public_web' for s in m['sources']))
 def test_truncation_visible(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'source';root.mkdir();(root/'text.txt').write_text('A'*100)
   m=ingest(root,Path(d)/'out/manifest.json',max_chars=5)
   self.assertTrue(m['truncated']);self.assertEqual(m['sources'][0]['status'],'partial_context')
 def test_ssrf_rejected(self):
  for u in ('http://127.0.0.1','http://169.254.169.254','file:///etc/passwd','http://user:pass@example.com','https://example.com:8888'):
   with self.subTest(url=u),self.assertRaises(ValueError):fetch_public(u)
 def test_interval_pole_between_samples_blocks(self):
  from exam_mastery.validate import check_numeric_interval
  with self.assertRaises(ContractError):check_numeric_interval('1/(x-0.333333)',{'x':(0,1)})
 def test_public_redirect_to_private_blocked(self):
  from unittest.mock import MagicMock
  response=MagicMock();response.status=302;response.getheader.return_value='http://127.0.0.1/'
  conn=MagicMock();conn.getresponse.return_value=response
  public=[(2,1,6,'',('93.184.216.34',80))];private=[(2,1,6,'',('127.0.0.1',80))]
  with patch('exam_mastery.discovery.socket.getaddrinfo',side_effect=[public,private]),patch('exam_mastery.discovery.socket.create_connection'),patch('exam_mastery.discovery.http.client.HTTPConnection',return_value=conn):
   with self.assertRaises(ValueError):fetch_public('http://example.com')
 def test_unreadable_integrity_check_is_explicit(self):
  from exam_mastery.onepath import snapshot
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'blocked.txt').write_text('test')
   with patch('exam_mastery.onepath.sha_file',side_effect=PermissionError('denied')):
    result=snapshot(root)
   self.assertIn('integrity_error',result['blocked.txt'])
 def test_output_inside_sources_denied(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ContractError):ingest(Path(d),Path(d)/'output/manifest.json')
if __name__=='__main__':unittest.main()
