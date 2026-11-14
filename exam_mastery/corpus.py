"""Complete, content-addressed corpus index. No global model-context cutoff."""
from pathlib import Path
import json,sqlite3,hashlib,io,base64,re,collections
from .discovery import ingest,IMAGES
from .common import write_json,sha_file,stable_id

SEGMENT_CHARS=6000
UNIT_CHARS=18000

def build(root,out,cache):
    manifest=ingest(root,out/'source_manifest.json',max_chars=2**63-1,extraction_cache=cache)
    db=sqlite3.connect(out/'corpus.sqlite3')
    db.executescript('DROP TABLE IF EXISTS segment_search; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS segments; DROP TABLE IF EXISTS links; CREATE TABLE sources(id TEXT PRIMARY KEY, payload TEXT); CREATE TABLE segments(id TEXT PRIMARY KEY, source_id TEXT, source_sha256 TEXT, locator TEXT, text TEXT, sha256 TEXT, visual INTEGER); CREATE TABLE links(url TEXT PRIMARY KEY, payload TEXT); CREATE VIRTUAL TABLE segment_search USING fts5(id UNINDEXED,locator UNINDEXED,text);')
    by={s['id']:s for s in manifest['sources'] if 'id' in s}
    for sid,s in by.items():db.execute('INSERT INTO sources VALUES (?,?)',(sid,json.dumps(s,ensure_ascii=False)))
    segments=[]
    for page in manifest['chunks']:
        sid=page['locator'].split(':')[0];source=by[sid];text=page['excerpt']
        for offset in range(0,max(1,len(text)),SEGMENT_CHARS):
            part=text[offset:offset+SEGMENT_CHARS];loc=page['locator']+f':char{offset+1}-{offset+len(part)}'
            segment={'id':stable_id('seg',source['sha256']+'|'+loc),'source_id':sid,'source_sha256':source['sha256'],'locator':loc,'page_locator':page['locator'],'excerpt':part,'images':page['images'],'visual':bool(page['images'] or (source['format'] in {'.pdf','.pptx','.docx','.xlsx','.xlsm'} and source.get('requires_visual_review')))}
            segments.append(segment)
            db.execute('INSERT INTO segments VALUES (?,?,?,?,?,?,?)',(segment['id'],sid,source['sha256'],loc,part,hashlib.sha256(part.encode()).hexdigest(),int(segment['visual'])))
    db.executemany('INSERT INTO segment_search VALUES (?,?,?)',[(s['id'],s['locator'],s['excerpt']) for s in segments])
    for link in manifest.get('online_sources',[]):db.execute('INSERT INTO links VALUES (?,?)',(link['url'],json.dumps(link,ensure_ascii=False)))
    db.commit();db.close()
    # Batch boundaries are transport limits, not course or competence boundaries.
    # The architect and learner designer derive actual competencies inside each batch.
    units=[];current=[];size=0;visual_pages=set()
    for s in segments:
        vp={s['page_locator']} if s['visual'] else set()
        if current and (size+len(s['excerpt'])>UNIT_CHARS or len(visual_pages|vp)>4):
            units.append(current);current=[];size=0;visual_pages=set()
        current.append(s);size+=len(s['excerpt']);visual_pages|=vp
    if current:units.append(current)
    work=[{'id':stable_id('unit','|'.join(s['id'] for s in group)),'segments':group,'source_ids':sorted({s['source_id'] for s in group})} for group in units]
    manifest['chunks']=[{'locator':s['locator'],'excerpt':s['excerpt'],'images':s['images']} for s in segments]
    write_json(out/'source_manifest.json',manifest)
    write_json(out/'work_units.json',work)
    write_json(out/'corpus_coverage.json',{'schema':'em-corpus-coverage-v4','source_count':len(by),'segment_count':len(segments),'indexed_characters':sum(len(s['excerpt']) for s in segments),'global_truncation':False,'transport_unit_count':len(work),'unprocessed_sources':[s for s in by.values() if s['status'] not in ('extracted','ignored_metadata')],'unavailable_online':[s for s in manifest.get('online_sources',[]) if s['status']!='fetched']})
    return manifest,work

def prepare_visuals(root,manifest,unit,out):
    from PIL import Image
    import pymupdf
    sources={s['id']:s for s in manifest['sources'] if 'id' in s};images=[];gaps=[];seen=set()
    from .checkpoints import digest
    identity=digest({'segments':unit['segments'],'sources':{sid:sources[sid] for sid in {seg['source_id'] for seg in unit['segments']}}})
    register=out/'visual_register.json'
    if register.exists():
        try:
            previous=json.loads(register.read_text())
            expected={seg['locator'] for seg in unit['segments'] if seg['visual']}
            covered={ref for image in previous['images'] for ref in image['source_refs']}|{gap['source_ref'] for gap in previous['gaps']}
            if previous.get('input_sha256')==identity and covered==expected and all(Path(image['path']).is_file() and sha_file(Path(image['path']))==image['sha256'] for image in previous['images']):return previous['images'],previous['gaps']
        except (KeyError,TypeError,ValueError,OSError):pass
    dest=out/'source_visuals';dest.mkdir(parents=True,exist_ok=True)
    for s in unit['segments']:
        if not s['visual'] or s['page_locator'] in seen:continue
        seen.add(s['page_locator']);source=sources[s['source_id']];ext=source['format'];sid=s['source_id'];page=int(s['page_locator'].split(':p')[1])
        path=root/source['path'] if source['origin']=='local' else out.parents[1]/'extracted'/(sid+ext)
        target=dest/(sid+f'-p{page}.png')
        try:
            if ext=='.pdf':
                with pymupdf.open(path) as doc:doc[page-1].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(target)
            elif ext=='.ipynb':
                nb=json.loads(path.read_text());flat=[]
                for cell in nb.get('cells',[]):
                    flat.append(None);flat.extend(cell.get('outputs',[]))
                output=flat[page-1]
                if output is None:continue
                data=output.get('data',{});mime=next((x for x in ('image/png','image/jpeg') if x in data),None)
                if mime is None:
                    if not any(k.startswith('image/') for k in data):continue
                    raise ValueError('Saved image format has no safe raster decoder')
                raw=base64.b64decode(''.join(data[mime]),validate=True)
                if len(raw)>8*1024*1024:raise ValueError('Notebook image exceeds safety limit')
                with Image.open(io.BytesIO(raw)) as im:
                    im.thumbnail((2200,2200));im.convert('RGB').save(target)
            elif ext in IMAGES and ext!='.svg':
                with Image.open(path) as im:
                    im.thumbnail((2200,2200));im.convert('RGB').save(target)
            else:
                gaps.append({'source_ref':s['locator'],'reason':'No faithful full-layout renderer for this visual format; source remains indexed, not visually cleared'});continue
            images.append({'path':str(target.resolve()),'source_refs':[x['locator'] for x in unit['segments'] if x['page_locator']==s['page_locator']],'sha256':sha_file(target)})
        except Exception as e:gaps.append({'source_ref':s['locator'],'reason':f'{type(e).__name__}: {e}'})
    write_json(out/'visual_register.json',{'images':images,'gaps':gaps,'independent_visual_clearance':False,'input_sha256':identity})
    return images,gaps


def retrieve(out,competencies,exclude):
    words=re.findall(r'[^\W\d_]{5,}', ' '.join(c['statement'] for c in competencies).lower(),flags=re.UNICODE)
    stop={'given','which','their','there','these','those','source','state','under','using','explain','calculate','identify','model','models','between','constant','interpret','andere','einer','eines','werden','sowie','durch','diese','their'}
    terms=[w for w,_ in collections.Counter(words).most_common() if w not in stop][:16]
    db=sqlite3.connect(out/'corpus.sqlite3');results=[]
    try:
        if terms:
            rows=db.execute('SELECT id,locator,text FROM segment_search WHERE segment_search MATCH ? ORDER BY bm25(segment_search) LIMIT 24',(' OR '.join('"'+w+'"' for w in terms),)).fetchall()
            for sid,loc,text in rows:
                if sid not in exclude:
                    meta=db.execute('SELECT source_id,source_sha256 FROM segments WHERE id=?',(sid,)).fetchone()
                    results.append({'id':sid,'locator':loc,'excerpt':text,'source_id':meta[0],'source_sha256':meta[1]})
                    if len(results)==3:break
    finally:db.close()
    return terms,results
