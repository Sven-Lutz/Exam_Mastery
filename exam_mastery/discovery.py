"""Read-only recursive inventory. Sources are data, never executable instructions."""
from __future__ import annotations
import ast, csv, hashlib, html, ipaddress, json, mimetypes, re, socket, ssl, http.client, datetime
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from html.parser import HTMLParser
from .common import write_json, sha_file, stable_id, ContractError
from .ingest_legacy import _read

TEXT={'.txt','.md','.markdown','.rst','.tex','.bib','.json','.yaml','.yml','.xml','.r','.sql','.js','.ts','.c','.cpp','.java','.sh','.ipynb','.py','.csv','.tsv','.html','.htm'}
IMAGES={'.png','.jpg','.jpeg','.webp','.gif','.tif','.tiff','.bmp','.svg','.heic','.avif','.jpe'}
URL=re.compile(r'https?://[^\s<>\[\]"\x27`]+')
def clean_url(value):
    value=value.rstrip('.,;:')
    while value.endswith(')') and value.count(')')>value.count('('):value=value[:-1]
    return value

MAX_FILE=40*1024*1024
class TextHTML(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[];self.links=[];self.hidden=0
    def handle_starttag(self,t,a):
        if t in ('script','style'): self.hidden+=1
        for k,v in a:
            if k in ('href','src') and v:self.links.append(v)
    def handle_endtag(self,t):
        if t in ('script','style'):self.hidden=max(0,self.hidden-1)
    def handle_data(self,d):
        if not self.hidden:self.parts.append(d)

def fetch_public(url, max_bytes=8*1024*1024):
    """No proxies/cookies; every redirect revalidated; DNS pinned through TLS connect."""
    chain=[]
    for _ in range(6):
        u=urlsplit(url)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password or u.port not in (None,80,443):
            raise ValueError('Only public HTTP(S) on standard ports is allowed')
        addresses=socket.getaddrinfo(u.hostname,u.port or (443 if u.scheme=='https' else 80),type=socket.SOCK_STREAM)
        ips=[a[4][0] for a in addresses]
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips): raise ValueError('Non-public destination blocked')
        host=u.hostname;port=u.port or (443 if u.scheme=='https' else 80);ip=ips[0]
        conn=http.client.HTTPConnection(host,port,timeout=20)
        sock=socket.create_connection((ip,port),timeout=20)
        if u.scheme=='https':sock=ssl.create_default_context().wrap_socket(sock,server_hostname=host)
        conn.sock=sock
        try:
            conn.request('GET',(u.path or '/')+('?' + u.query if u.query else ''),headers={'Host':u.netloc,'User-Agent':'ExamMastery/0.3 source-reader','Accept-Encoding':'identity'})
            response=conn.getresponse();chain.append({'url':url,'status':response.status,'peer_ip':ip})
            if response.status in (301,302,303,307,308):
                url=urljoin(url,response.getheader('Location',''));continue
            if response.status!=200:raise ValueError(f'HTTP {response.status}')
            if response.getheader('Content-Encoding','identity')!='identity':raise ValueError('Encoded response not accepted')
            data=response.read(max_bytes+1)
            if len(data)>max_bytes:raise ValueError('Online source exceeds byte limit')
            return data,response.getheader('Content-Type',''),url,chain
        finally:conn.close()
    raise ValueError('Redirect limit exceeded')

def extract(path):
    ext=path.suffix.lower();flags=[];links=[]
    if ext in {'.docx','.pptx','.xlsx','.xlsm'}:
        import zipfile
        with zipfile.ZipFile(path) as archive:
            entries=archive.infolist()
            if len(entries)>20000 or sum(x.file_size for x in entries)>200*1024*1024:raise ValueError('Office archive expansion exceeds safety limits')
    if ext in {'.pdf','.docx','.pptx'}:
        pages=_read(path)
        # PDF/PPTX vectors, formulas and layout cannot be certified by image counts.
        if ext in {'.pdf','.pptx'}:flags.append('visual_layout_review_required')
        return pages,flags,links
    if ext in IMAGES:
        return [{'page':1,'text':'[VISUAL SOURCE: image interpretation required]','images':1}],['visual_review_required'],links
    if ext in {'.xlsx','.xlsm'}:
        from openpyxl import load_workbook
        wb=load_workbook(path,read_only=False,data_only=False,keep_links=False)
        pages=[]
        for i,s in enumerate(wb,1):
            rows=[]
            for row in s.iter_rows():
                rows.append(' | '.join('' if c.value is None else str(c.value) for c in row))
                links.extend(c.hyperlink.target for c in row if c.hyperlink and c.hyperlink.target)
            pages.append({'page':i,'text':'SHEET '+s.title+'\n'+'\n'.join(rows),'images':len(s._images)+len(s._charts)})
        wb.close();return pages,['spreadsheet_formulas_not_recalculated'],links
    if ext not in TEXT:raise ValueError('Unsupported format; inventoried without semantic extraction')
    text=path.read_text(encoding='utf-8-sig')
    if ext=='.ipynb':
        nb=json.loads(text);pages=[];flags=['code_not_executed','saved_outputs_not_independently_reproduced']
        for i,cell in enumerate(nb.get('cells',[]),1):
            pages.append({'page':len(pages)+1,'text':f'CELL {i} {cell.get("cell_type")}\n'+''.join(cell.get('source',[])),'images':0})
            for j,output in enumerate(cell.get('outputs',[]),1):
                parts=[f'CELL {i} OUTPUT {j}: saved, not re-executed'];data=output.get('data',{})
                if output.get('text'):parts.append(''.join(output['text']))
                for mime,value in data.items():
                    if mime.startswith('image/'):continue
                    if mime=='text/html':
                        parser=TextHTML();parser.feed(''.join(value));parts.extend(parser.parts);links.extend(parser.links)
                    elif isinstance(value,list):parts.append(''.join(str(v) for v in value))
                    elif isinstance(value,str):parts.append(value)
                    else:parts.append(json.dumps(value,ensure_ascii=False))
                count=int(any(mime.startswith('image/') for mime in data))
                pages.append({'page':len(pages)+1,'text':'\n'.join(parts),'images':count})
        if any(p['images'] for p in pages):flags.append('notebook_output_visual_review_required')
        return pages,flags,links
    if ext in {'.py','.sh','.js','.ts','.r','.sql','.c','.cpp','.java'}:
        flags.append('code_not_executed')
        if ext=='.py':
            try:
                tree=ast.parse(text)
                calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
                if any(any(k in c for k in ('exec','eval','system','subprocess','unlink','remove','open','request','socket')) for c in calls):flags.append('code_security_review_required')
            except SyntaxError:flags.append('code_parse_failed')
    if ext in {'.html','.htm'}:
        parser=TextHTML();parser.feed(text);links=parser.links;text='\n'.join(parser.parts)
    if ext in {'.csv','.tsv'}:
        rows=list(csv.reader(text.splitlines(),delimiter='\t' if ext=='.tsv' else ','))
        text='\n'.join(' | '.join(r) for r in rows)
    return [{'page':1,'text':text,'images':0}],flags,links

def classify(rel,text,ext,links):
    """Provisional evidence, not authority inferred from extension."""
    probe=(rel+'\n'+text[:24000]).casefold();roles=[];evidence=[]
    rules={'solutions':r'musterlösung|musterloesung|solution|answer key','past_exam':r'altklausur|past exam|klausur \d|examination','exercise':r'übungsblatt|uebungsblatt|exercise|problem set','lecture':r'vorlesung|lecture|lernziele|learning objectives','literature':r'literatur|bibliograph|recommended reading','paper':r'abstract\b.*|doi.org|arxiv','notes':r'mitschrift|notizen|notes'}
    for role,pattern in rules.items():
        m=re.search(pattern,probe)
        if m:roles.append(role);evidence.append({'role':role,'matched':m.group(0)[:100]})
    if ext in {'.py','.ipynb','.r','.sql','.js','.sh','.c','.cpp','.java'}:roles.append('code_candidate')
    if ext in {'.csv','.tsv','.xlsx','.xlsm'}:roles.append('tabular_data_candidate')
    if ext in IMAGES:roles.append('visual')
    if links:roles.append('online_references')
    return roles or ['unclassified'],evidence

def ingest(folder:Path,out:Path,max_chars=90000, extraction_cache=None):
    folder=folder.expanduser().resolve();out=out.resolve()
    if not folder.is_dir():raise ContractError('Source root must be an existing directory')
    if folder==out.parent or folder in out.parents:raise ContractError('Output must be outside original source tree')
    out.parent.mkdir(parents=True,exist_ok=True);cache=out.parent/'extracted';cache.mkdir(exist_ok=True)
    sources=[];chunks=[];online=[];total=0;truncated=False;seen_hash={};url_origins={};scan_errors=[]
    def error(e):scan_errors.append(str(e))
    import os
    paths=[]
    for base,dirs,files in os.walk(folder,followlinks=False,onerror=error):
        for d in list(dirs):
            if (Path(base)/d).is_symlink():
                sources.append({'path':str((Path(base)/d).relative_to(folder)),'status':'symlink_directory_skipped','requires_visual_review':False});dirs.remove(d)
        paths.extend(Path(base)/f for f in files)
    for path in sorted(paths):
        rel=str(path.relative_to(folder));ext=path.suffix.lower()
        s={'id':stable_id('src',rel),'path':rel,'origin':'local','format':ext,'content_type':mimetypes.guess_type(path.name)[0] or 'application/octet-stream','source_roles':[],'relationships':[],'requires_visual_review':False}
        sources.append(s)
        if path.is_symlink():s['status']='symlink_skipped';continue
        try:
            s['sha256']=sha_file(path);s['bytes']=path.stat().st_size
            if s['sha256'] in seen_hash:s['relationships'].append({'kind':'duplicate_of','id':seen_hash[s['sha256']]})
            seen_hash[s['sha256']]=s['id']
            if path.name=='.DS_Store':s.update(status='ignored_metadata',source_roles=['filesystem_metadata']);continue
            if s['bytes']>MAX_FILE:raise ValueError('File size exceeds safety limit')
            pages,flags,extra_links=cached_extract(path,extraction_cache)
            text='\n'.join(p['text'] for p in pages)
            urls=set(URL.findall(text))|{u for u in extra_links if u.startswith(('http://','https://'))}
            urls={clean_url(u) for u in urls}
            for u in sorted(urls):url_origins.setdefault(u,[]).append(s['id'])
            roles,evidence=classify(rel,text,ext,urls)
            s.update(source_roles=roles,role_evidence=evidence,authority='unverified',flags=flags,pages=len(pages),images=sum(p['images'] for p in pages),status='extracted')
            s['requires_visual_review']=bool(s['images'] or any('visual' in f for f in flags))
            write_json(cache/(s['id']+'.json'),pages)
            for p in pages:
                t=p['text'];remaining=max(0,max_chars-total);included=t[:remaining];total+=len(included)
                if len(included)<len(t):truncated=True;s['status']='partial_context'
                chunks.append({'locator':f'{s["id"]}:p{p["page"]}','excerpt':included or '[NO TEXT IN CONTEXT; extraction/visual review required]','images':p['images']})
        except Exception as e:s.update(status='unprocessed',error=f'{type(e).__name__}: {e}')
    journal_path=out.parent/'online_journal.json'
    journal=json.loads(journal_path.read_text()) if journal_path.exists() else {}
    # User-root references are fetched once per snapshot; nested web links are inventoried without crawling.
    for i,(url,origins) in enumerate(sorted(url_origins.items())):
        record={'url':url,'origin_ids':origins,'status':'pending'};online.append(record)
        # Every identified public URL is attempted; failures remain explicit.
        try:
            previous=journal.get(url,{})
            cached=out.parent/previous.get('cache_path','missing')
            if previous.get('status')=='fetched' and cached.is_file() and sha_file(cached)==previous.get('sha256'):
                data=cached.read_bytes();ctype=previous['content_type'];final=previous['final_url'];chain=previous['redirect_chain']
            else:
                data,ctype,final,chain=fetch_public(url)
                previous={'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
            digest=hashlib.sha256(data).hexdigest();sid=stable_id('web',url)
            ext='.pdf' if 'application/pdf' in ctype else '.html' if 'html' in ctype else '.json' if 'application/json' in ctype else (mimetypes.guess_extension(ctype.split(';')[0]) or '.bin') if ctype.startswith('image/') else '.txt' if 'text/' in ctype else '.bin'
            saved=cache/(sid+ext);saved.write_bytes(data)
            pages,flags,linked=cached_extract(saved,extraction_cache)
            s={'id':sid,'path':url,'origin':'public_web','sha256':digest,'content_type':ctype,'format':ext,'source_roles':['online_source'],'authority':'unverified','relationships':[{'kind':'referenced_by','id':x} for x in origins],'status':'extracted','flags':flags,'requires_visual_review':bool(flags or any(p['images'] for p in pages)),'pages':len(pages),'images':sum(p['images'] for p in pages)}
            sources.append(s)
            for p in pages:
                t=p['text'];inc=t[:max(0,max_chars-total)];total+=len(inc)
                if len(inc)<len(t):truncated=True;s['status']='partial_context'
                chunks.append({'locator':f'{sid}:p{p["page"]}','excerpt':inc or '[NOT INCLUDED IN CONTEXT]','images':p['images']})
            record.update(status='fetched',retrieved_at_utc=previous.get('retrieved_at_utc','unknown_legacy_cache'),final_url=final,sha256=digest,redirect_chain=chain,source_id=sid,license='not_verified',content_type=ctype,cache_path=str(saved.relative_to(out.parent)),nested_public_references=sorted({clean_url(x) for p in pages for x in URL.findall(p['text'])}|{x for x in linked if x.startswith(('https://','http://'))}))
        except Exception as e:record.update(status='failed',error=f'{type(e).__name__}: {e}')
        journal[url]=record.copy();write_json(journal_path,journal)
    # Same-directory stem matches are candidate relations, never asserted solution mappings.
    for s in sources:
        if s.get('origin')=='local':
            stem=Path(s['path']).stem.casefold()
            for other in sources:
                if s is not other and other.get('origin')=='local' and stem and stem in Path(other['path']).stem.casefold():
                    s['relationships'].append({'kind':'name_related_candidate','id':other['id']})
    m={'schema':'em-source-manifest-v2','root':str(folder),'sources':sources,'chunks':chunks,'online_sources':online,'scan_errors':scan_errors,'truncated':truncated,'extracted_chars':total,'requires_visual_review':any(s['requires_visual_review'] for s in sources),'coverage_complete':not scan_errors and not truncated and all(s['status'] in ('extracted','ignored_metadata') for s in sources) and all(r['status']=='fetched' for r in online)}
    write_json(out,m)
    if not chunks:raise ContractError('No readable source text; see inventory for extraction gaps')
    return m


def cached_extract(path,cache):
    if cache is None:return extract(path)
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    key=sha_file(path)+'-'+sha_file(Path(__file__))[:12]+path.suffix.lower()+'.json'
    target=cache/key
    if target.exists():
        value=json.loads(target.read_text());return value['pages'],value['flags'],value['links']
    pages,flags,links=extract(path)
    write_json(target,{'pages':pages,'flags':flags,'links':links})
    return pages,flags,links
