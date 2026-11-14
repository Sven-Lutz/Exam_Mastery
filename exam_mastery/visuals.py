"""Create local visual evidence without running source programs or active SVG/HTML."""
from pathlib import Path
import zipfile,io
from .common import write_json

def prepare(root,manifest,out):
    from PIL import Image
    import pymupdf
    dest=out/'visual_sources';dest.mkdir(exist_ok=True)
    queue=[];gaps=[]
    def save(image,sid,page,index=0):
        if len(queue)>=12:raise ValueError('Visual model review budget: 12 images per run')
        image.thumbnail((1800,1800));target=dest/f'{sid}-p{page}-{index}.png';image.convert('RGB').save(target)
        queue.append({'source_ref':f'{sid}:p{page}','image_path':str(target)})
    for s in manifest['sources']:
        if not s.get('requires_visual_review') or s.get('origin')!='local':continue
        path=root/s['path'];ext=s['format'];sid=s['id']
        try:
            if ext=='.pdf':
                with pymupdf.open(path) as doc:
                    for i,p in enumerate(doc):
                        pix=p.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3));save(Image.open(io.BytesIO(pix.tobytes('png'))),sid,i+1)
            elif ext in {'.png','.jpg','.jpeg','.gif','.webp','.bmp','.tif','.tiff'}:
                with Image.open(path) as img:save(img,sid,1)
            elif ext in {'.docx','.pptx','.xlsx','.xlsm'}:
                with zipfile.ZipFile(path) as z:
                    for i,name in enumerate(z.namelist()):
                        if '/media/' in name:
                            with Image.open(io.BytesIO(z.read(name))) as img:save(img,sid,1,i)
                gaps.append({'source_id':sid,'reason':'Embedded media only; vector diagrams, layout and exact media-page mapping remain unverified'})
            else:gaps.append({'source_id':sid,'reason':'No safe renderer available for this visual format'})
        except Exception as e:gaps.append({'source_id':sid,'reason':str(e)})
    result={'images':queue,'gaps':gaps,'scope':'Model observations supplement text; never independent visual clearance'}
    write_json(out/'visual_queue.json',result);return result
