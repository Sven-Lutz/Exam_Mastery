"""Write P3.1 SYNTHETIC_FIXTURE quality gate reports offline (no provider, no network)."""
import contextlib, io, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import p1p2_fixtures as F, p3_fixtures as P, p3_1_fixtures as Q
from exam_mastery.chapters import dry_run
from exam_mastery.quality_gates import quality_report
from exam_mastery.runtime import run_chapters

dest = ROOT / 'docs' / 'p3_1_example'; dest.mkdir(parents=True, exist_ok=True)
MARK = {'SYNTHETIC_FIXTURE': True, 'warning': 'Offline report on synthetic fixtures. Not academic evidence; no release.'}
def small(q):
    return {**MARK, 'stages': q['stages'], 'academic_status': q['academic_status'], 'content_go': q['content_go'], 'release_go': q['release_go'],
            'gates': {g: v['status'] for g, v in q['gates'].items()},
            'failing_findings': [f for f in q['findings'] if f['status'] in ('FAIL', 'BLOCKED')]}
with tempfile.TemporaryDirectory() as d:
    root = F.make('math', d + '/src')
    with contextlib.redirect_stdout(io.StringIO()):
        out, _ = run_chapters(root, provider=P.SyntheticChapterModel(), output_base=Path(d) / 'runs')
    plan = json.loads((out / 'plan' / 'curriculum.json').read_text())
    c = next(x for x in plan['chapters'] if 'Ausgleich' in x['title'])
    q = json.loads((out / 'chapters' / c['chapter_id'] / 'quality_gate_report.json').read_text())
    (dest / 'quality_gate_report.SYNTHETIC_FIXTURE.json').write_text(json.dumps({**MARK, 'subject': 'P3 synthetic fixture chapter (Lineare Ausgleichsrechnung)', **q}, ensure_ascii=False, indent=2))
    for kind in ('math', 'law', 'ml'):
        r = Q.course(F.random_root(Path(d) / ('p' + kind)), kind)
        _, plan, m, _, _ = dry_run(r, Path(d) / ('o' + kind))
        a = Q.positive_ast(kind, plan, m); ch = plan['chapters'][0]
        (dest / f'positive_{kind}.SYNTHETIC_FIXTURE.json').write_text(json.dumps(small(quality_report(a, ch, plan, m)), ensure_ascii=False, indent=2))
        if kind == 'math':
            neg = {case: small(quality_report(Q.negative(a, case, m), ch, plan, m)) for case in
                   ('a_unsolvable', 'b_derive_by_define', 'c_transfer_label', 'd_motivation_only', 'e_invented_anchor',
                    'f_essential_image', 'g_notation', 'h_self_release')}
            (dest / 'negative_math.SYNTHETIC_FIXTURE.json').write_text(json.dumps(neg, ensure_ascii=False, indent=2))
print('written', sorted(p.name for p in dest.iterdir()))
