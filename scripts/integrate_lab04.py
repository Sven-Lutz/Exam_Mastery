#!/usr/bin/env python3
"""Deterministic Lab04 acceptance build from an existing ENT run. Never calls a model/provider.
Inputs and historical products are read-only. Output must be a new directory.
"""
import argparse
import hashlib
import html
import json
import shutil
import time
from pathlib import Path

from exam_mastery.labs import build as B
from exam_mastery.labs.integrate import catalog_requests, build_spec
from exam_mastery.chapter_publish import publish_chapter, _anchor_index, _anchors
from exam_mastery import typeset


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for arg in ('course-run', 'source-root', 'references', 'archive', 'output'):
        ap.add_argument('--'+arg, required=True, type=Path)
    args = ap.parse_args(); start = time.monotonic()
    run, root, out = args.course_run.resolve(), args.source_root.resolve(), args.output.resolve()
    if out.exists():
        ap.error('output exists; historical artifacts must not be overwritten')
    if shutil.disk_usage(out.parent).free < 16*1024**3:
        ap.error('15 GiB system reserve plus 1 GiB build allowance required')
    mp, cp = run/'plan/source_inventory.json', run/'plan/curriculum.json'
    man, plan = json.loads(mp.read_text()), json.loads(cp.read_text())
    originals = {}
    for src in man['sources']:
        p = root / src['relative_path']
        if sha(p) != src['raw_sha256']:
            raise ValueError('original hash mismatch: '+str(p))
        originals[str(p)] = sha(p)
    chapters = list(run.glob('chapters/*/content_ast.json'))
    candidates = []
    for path in chapters:
        ast = json.loads(path.read_text())
        kcs = [k for k in plan['competencies'] if k['kc_id'] in ast['kc_ids']]
        reqs = catalog_requests(kcs)
        if reqs: candidates.append((path,ast,kcs,reqs))
    if len(candidates) != 1:
        raise ValueError('expected one chapter with source-backed Van Westendorp competency')
    ast_path, ast, kcs, reqs = candidates[0]; req = reqs[0]
    idx = _anchor_index(man)
    if not req['source_refs'] or any(a not in idx for a in req['source_refs']):
        raise ValueError('unresolvable method source anchors')
    spec = build_spec(req, 'Entrepreneurship', [_anchors(req['source_refs'],idx)])
    out.mkdir(parents=True)
    saved = out/'inputs'; saved.mkdir()
    for p in (mp,cp,ast_path,ast_path.parent/'chapter_context.json'):
        shutil.copy2(p,saved/p.name)
    old = [json.loads(p.read_text()) for p in sorted((args.references/'labs').glob('*.json'))]
    if {s['model']['kind'] for s in old} != {'cashflow','risk','mlp'}:
        raise ValueError('reference environment must contain the three existing labs')
    labs = []
    for s in old+[spec]:
        p = B.render(s,out/'Lernumgebung/labs')
        labs.append((s['title'],'labs/'+p.name,s['kc_ids']))
    # Existing chapter publishing: unmodified AST plus deterministic source-bound lab catalogue.
    ch = out/'chapter_07'; ch.mkdir()
    for name in ('content_ast.json','chapter_context.json'):
        shutil.copy2(ast_path.parent/name,ch/name)
    report = publish_chapter(ch,man,plan,verify_anki=True,assets_root=run/'plan')
    built = [r for r in report['labs'] if r['status']=='BUILT' and r['model']=='van_westendorp']
    if len(built)!=1:
        raise ValueError('chapter publishing did not build the fourth model')
    # Static standalone companion using the SAME typesetter (no separate lab PDF stack).
    E = html.escape
    body = '<section class="cover"><h1>'+E(spec['title'])+'</h1><p>Lab 04 · Exam Mastery v0.14.0-preview</p><p>Statischer Fallback</p><p>'+E(spec['model']['data_label'])+'</p></section>'
    body += '<h1>Ausgangszustand und Rechenkonvention</h1>'+B.static_svg(spec)
    body += '<p>'+E(spec['objective'])+'</p><ul>'+''.join('<li>'+E(t)+'</li>' for t in spec['assumptions'])+'</ul>'
    body += '<h2>Kompetenzen und methodische Quellen</h2><p>'+E(', '.join(spec['kc_ids']))+'</p>'
    body += ''.join('<p>'+E(t)+'</p>' for t in spec['sources'])
    body += '<p>Quellen belegen das Verfahren. Die 240 Antworten sind erfunden; sie sind keine Vorlesungsergebnisse. Keine fachliche Gesamtfreigabe des Kapitels.</p>'
    pdf = typeset.render_document(body,[],spec['title'],out/'Lernumgebung','Lab04_Van_Westendorp','Exam Mastery · synthetische Demonstrationsdaten')
    B.environment(out/'Lernumgebung','Vier Referenz-Labs','Exam Mastery v0.14.0-preview',
        [('Lab 04: statischer PDF-Fallback','Lab04_Van_Westendorp.pdf'),
         ('Kapitel 07: deterministisch neu veröffentlicht (keine Gesamtfreigabe)','../chapter_07/publish/artifacts/Lernumgebung/index.html')],labs,
        ['Lab 04: Methode aus ENT-Quellen; Preisantworten synthetisch. Kapitel-E2E weiterhin PARTIAL/NOT_RELEASED.'])
    quality=json.loads((ast_path.parent/'quality_gate_report.json').read_text())
    dossier=json.loads((run/'quality_dossier.json').read_text())
    binding = {'request':req,'competencies':[k for k in kcs if k['kc_id'] in req['kc_ids']],
        'elements':[e for e in man['elements'] if e['element_id'] in req['source_refs']],
        'method_source_originals':originals,'source_inventory':str(mp),'source_inventory_sha256':sha(mp),
        'curriculum_sha256':sha(cp),'archive':str(args.archive),'archive_sha256':sha(args.archive),
        'data_origin':'SYNTHETIC_DEMO_NOT_LECTURE_RESULTS','human_source_review':'NOT_PERFORMED'}
    (out/'source_binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2))
    if any(sha(p)!=h for p,h in originals.items()) or sha(ast_path)!=sha(ch/'content_ast.json'):
        raise ValueError('input immutability check failed')
    receipt={'schema':'em-lab04-integration-v1','model_calls':0,'new_productions':0,
        'source_originals_unchanged':True,'ast_unchanged':True,'chapter_publishing':'EXECUTED',
        'historical_run':str(run),'historical_dimensions':dossier['dimensions'],
        'historical_release':dossier['release'],'historical_gate_counts':quality['counts'],
        'historical_gates':{k:v['status'] for k,v in quality['gates'].items()},
        'chapter_e2e':'NOT_RELEASED_NOT_RERUN','new_publishing_gates':{k:report[k] for k in ('didactic_rules','numeric_checks','semantic_checks','documents','labs')},
        'wall_seconds':round(time.monotonic()-start,3),'free_bytes_after':shutil.disk_usage(out).free,
        'outputs_sha256':{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
    (out/'integration_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
    print(json.dumps({'output':str(out),'labs':len(labs),'model_calls':0,'chapter_e2e':receipt['chapter_e2e'],'seconds':receipt['wall_seconds']}))

if __name__=='__main__': main()
