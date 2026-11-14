from __future__ import annotations
from pathlib import Path
import mimetypes
from .common import stable_id, sha_file, write_json, ContractError

SUPPORTED = {'.md','.txt','.pdf','.pptx','.docx'}

def _read(path: Path):
    suf = path.suffix.lower()
    if suf in ('.md','.txt'):
        return [{'page':1,'text':path.read_text(encoding='utf-8-sig'),'images':0}]
    if suf == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        out=[]
        for n,p in enumerate(reader.pages,1):
            try: nimg = len(p.images)
            except Exception: nimg=0
            out.append({'page':n,'text':p.extract_text(extraction_mode='layout') or '', 'images':nimg})
        return out
    if suf == '.pptx':
        from pptx import Presentation
        prs = Presentation(str(path))
        out=[]
        for n,slide in enumerate(prs.slides,1):
            texts=[]; imgs=0
            for shape in slide.shapes:
                if shape.has_text_frame: texts.append(shape.text)
                if shape.shape_type == 13: imgs+=1
                if shape.has_table:
                    texts.extend(' | '.join(cell.text for cell in row.cells) for row in shape.table.rows)
            # Speaker notes if present
            if slide.has_notes_slide:
                try: texts.append('NOTES: '+slide.notes_slide.notes_text_frame.text)
                except Exception: pass
            out.append({'page':n,'text':'\n'.join(texts),'images':imgs})
        return out
    if suf == '.docx':
        from docx import Document
        doc=Document(str(path)); texts=[p.text for p in doc.paragraphs]
        for tbl in doc.tables:
            texts.extend(' | '.join(c.text for c in row.cells) for row in tbl.rows)
        imgs=len(doc.inline_shapes)
        return [{'page':1,'text':'\n'.join(texts),'images':imgs}]
    raise ContractError(f'Unsupported source {path.name}')

def ingest(folder: Path, out: Path, max_chars: int = 90000):
    folder=folder.resolve()
    if not folder.is_dir(): raise ContractError('Input directory does not exist')
    paths=sorted(p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED and not p.name.startswith('.'))
    if not paths: raise ContractError('No supported source files found')
    sources=[]; chunks=[]; total=0; truncated=False
    for path in paths:
        rel=str(path.relative_to(folder)); sid=stable_id('src',rel+'|'+sha_file(path))
        pages=_read(path); nonempty=sum(bool(p['text'].strip()) for p in pages)
        images=sum(p['images'] for p in pages)
        sources.append({'id':sid,'path':rel,'sha256':sha_file(path),'pages':len(pages),'images':images,
          'nonempty_pages':nonempty,'format':path.suffix.lower(),'requires_visual_review': bool(images or nonempty!=len(pages))})
        for p in pages:
            locator=f'{sid}:p{p["page"]}'
            txt=p['text'].strip()
            if not txt:
                chunks.append({'locator':locator,'excerpt':'[NO EXTRACTABLE TEXT: visual inspection required]','images':p['images']})
                continue
            # Do not silently cut source corpus: mark explicitly
            remaining=max_chars-total
            if remaining<=0:
                truncated=True
                chunks.append({'locator':locator,'excerpt':'[NOT INCLUDED IN LLM CONTEXT: course partitioning required]','images':p['images']})
            else:
                included=txt[:remaining]; total+=len(included)
                if len(included)!=len(txt): truncated=True
                chunks.append({'locator':locator,'excerpt':included,'images':p['images']})
    manifest={'sources':sources,'chunks':chunks,'truncated':truncated,'extracted_chars':total,
      'requires_visual_review':any(s['requires_visual_review'] for s in sources)}
    write_json(out,manifest)
    return manifest
