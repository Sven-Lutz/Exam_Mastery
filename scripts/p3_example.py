"""Write the P3 SYNTHETIC_FIXTURE example (chapter plan + ContentAST) offline. No provider, no network."""
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import p1p2_fixtures as F, p3_fixtures as P
from exam_mastery.runtime import run_chapters

dest = ROOT / 'docs' / 'p3_example'; dest.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as d:
    root = F.make('math', d + '/src')
    out, status = run_chapters(root, provider=P.SyntheticChapterModel(), output_base=Path(d) / 'runs')
    rep = json.loads((out / 'plan' / 'dry_run_report.json').read_text())
    plan = json.loads((out / 'plan' / 'curriculum.json').read_text())
    c = next(x for x in plan['chapters'] if 'Ausgleich' in x['title'])
    ast_ = json.loads((out / 'chapters' / c['chapter_id'] / 'content_ast.json').read_text())
    mark = {'SYNTHETIC_FIXTURE': True, 'warning': 'Generated offline from synthetic test fixtures and a fake model. '
            'Not academic content, not a quality signal, no release. Local temp paths removed.'}
    rep.pop('source_gaps', None)
    for g in rep.get('unattributed_blocking_gaps', []):
        g['detail'] = str(g['detail']).split('/')[-1]
    (dest / 'chapter_plan.SYNTHETIC_FIXTURE.json').write_text(json.dumps({**mark, 'dry_run_report': rep, 'chapter': c}, ensure_ascii=False, indent=2))
    (dest / 'content_ast.SYNTHETIC_FIXTURE.json').write_text(json.dumps({**mark, **ast_}, ensure_ascii=False, indent=2))
    print(status['technical_status'], ast_['status'], len(ast_['blocks']), len(ast_['assessments']))
