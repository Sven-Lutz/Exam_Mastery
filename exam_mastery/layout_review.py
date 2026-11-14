"""Actual model inspection of every rendered course-PDF page in bounded image batches."""
from pathlib import Path
from .common import sha_file,ContractError
from .checkpoints import atomic

def inspect_layout(out,checkpoints,provider):
    pages=sorted((out/'rendered').glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]));reviews=[]
    for offset in range(0,len(pages),4):
        batch=pages[offset:offset+4];ids=[int(p.stem.split('-')[-1]) for p in batch]
        prompt='ROLE: independent rendered-book quality auditor. Inspect each attached page image for legibility, clipped or missing text/glyphs, overlaps, margins, hierarchy and meaningful readable figures. Do not claim external independent scientific approval or unexecuted software tests. Compare facts only where relevant original evidence is explicitly supplied; otherwise limit the factual claim and review layout. Return JSON {"verdict":"PASS|FAIL|NEEDS_REVIEW","reviewed_pages":'+str(ids)+',"findings":[{"severity":"blocker|major|minor|info","description":"...","object_id":"page N","source_refs":[]}],"limitations":["..."]}. Review precisely the attached pages, never approve unread pages. Do not use tools.'
        import json
        source_path=out/'work_units.json'
        if source_path.exists():
            import pymupdf
            with pymupdf.open(out/'artifacts/learning_package.pdf') as pdf:
                actual='\n'.join(pdf[number-1].get_text() for number in ids)
            units=json.loads(source_path.read_text())
            related=[segment for unit in units for segment in unit['segments'] if segment['locator'] in actual or segment['source_id'] in actual]
            prompt+='\nActual product text and relevant ORIGINAL source evidence; distinguish factual comparison from layout checks. Check rendered formulas, units, captions, derivations and figure values against this evidence; flag contradictions or missing definitions. If no relevant source evidence is supplied, explicitly limit factual claims.\n'+json.dumps({'product_text':actual,'original_evidence':related},ensure_ascii=False)
        def validate(obj):
            if obj.get('verdict') not in ('PASS','FAIL','NEEDS_REVIEW') or set(obj.get('reviewed_pages',[]))!=set(ids):raise ContractError('Rendered audit omitted pages or verdict')
            if not isinstance(obj.get('findings'),list) or not isinstance(obj.get('limitations'),list):raise ContractError('Invalid rendered audit contract')
            if obj['verdict']=='PASS' and any(f['severity'] in ('blocker','major') for f in obj['findings']):raise ContractError('Layout PASS contradicts severe defects')
        reviews.append(checkpoints.invoke('render_audit_'+str(offset//4),prompt,provider,validate,[{'path':str(p.resolve()),'sha256':sha_file(p),'page':number} for p,number in zip(batch,ids)]))
    atomic(out/'render_audit.json',{'pages':len(pages),'reviews':reviews,'all_pages_reviewed':len({n for r in reviews for n in r['reviewed_pages']})==len(pages)})
    return reviews
