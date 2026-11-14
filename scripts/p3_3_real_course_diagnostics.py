"""Before/after diagnostics for a real course dry run, WITHOUT source text bodies.

usage: python scripts/p3_3_real_course_diagnostics.py <before_dryrun_dir> <after_dryrun_dir> <out.json>
Writes ids, roles, counts, rules, chapter titles and file names only. No provider, no network.
"""
import collections, json, sys
from pathlib import Path


def load(d):
    d = Path(d)
    return {n: json.loads((d / f).read_text()) for n, f in (('rep', 'dry_run_report.json'), ('plan', 'curriculum.json'),
                                                           ('inv', 'source_inventory.json'), ('gates', 'chapter_gates.json'))}


def metrics(x):
    p, inv, g = x['plan'], x['inv'], x['gates']
    st = collections.Counter(v['status'] for v in g.values())
    blk = collections.Counter(c for v in g.values() for codes in v['blocked_kcs'].values() for c in codes)
    rev = collections.Counter(c for v in g.values() for codes in v.get('review_required_kcs', {}).values() for c in codes)
    return {'sources': inv['source_count'], 'elements': inv['element_count'], 'source_gaps': len(inv['gaps']),
            'source_gaps_by_code': dict(collections.Counter(g_['code'] for g_ in inv['gaps'])),
            'chapters': len(p['chapters']), 'competencies': len(p['competencies']),
            'competencies_by_origin': dict(collections.Counter(k['origin'] for k in p['competencies'])),
            'assessment_items': len(p['assessment_items']),
            'assessment_items_by_kind': dict(collections.Counter(q.get('assessment_kind', q.get('kind')) for q in p['assessment_items'])),
            'chapter_gate_status': dict(st), 'kc_blocker_assignments': dict(blk), 'kc_review_assignments': dict(rev),
            'domain_profile': p['domain_profile']['active_profiles'], 'chapter_order_status': p['chapter_ordering']['status'],
            'open_uncertain_elements': sum(1 for e in inv['elements'] if e['status'] != 'ok')}


def main(before, after, out):
    b, a = load(before), load(after)
    t = a['rep']['triage']
    src = {s['source_id']: s['relative_path'] for s in a['inv']['sources']}
    chapters = []
    for c in a['rep']['chapters']:
        pc = next(x for x in a['plan']['chapters'] if x['chapter_id'] == c['chapter_id'])
        chapters.append({'position': c['position'], 'chapter_id': c['chapter_id'], 'title': c['title'],
                         'sources': [src[s] for s in c['source_ids']], 'source_roles': c['source_roles'],
                         'order_basis': c['order_basis'], 'segmentation': [{k: v for k, v in s.items() if k != 'dividers'} | {'divider_pages': [d['page'] for d in s.get('dividers', [])]} for s in c['segmentation']],
                         'kc_count': len(c['kc_ids']),
                         'kc_by_origin': dict(collections.Counter(k['origin'] for k in a['plan']['competencies'] if k['chapter_id'] == c['chapter_id'])),
                         'fidelity_status': c['gate'], 'blocked_kc_count': len(c['blocked_kcs']), 'review_required_kc_count': c['review_required_kc_count'],
                         'items_by_kind': {k: len(v) for k, v in pc['exam_relevance']['items_by_kind'].items()},
                         'academic_pilot_eligibility': c['academic_pilot_eligibility'], 'eligibility_reasons': c['eligibility_reasons'],
                         'pilot_candidate_score': c['pilot_candidate_score'], 'academic_release': c['academic_release']})
    doc = {'schema': 'em-p3_3-real-course-diagnostics-v1', 'content_policy': 'no source text bodies; ids, roles, counts, titles, file names only',
           'provider_calls_made': 0, 'network_calls_made': 0,
           'before': {'run': Path(before).name, **metrics(b)}, 'after': {'run': Path(after).name, **metrics(a)},
           'source_roles': [{'relative_path': r['relative_path'], 'role': r['role'], 'confidence': r['confidence'], 'authority': r['authority'],
                             'evidence': [{k: v for k, v in e.items() if k in ('signal', 'element_id', 'locator', 'pages')} |
                                          ({'detail': e['detail']} if e['signal'] not in ('placeholder_text',) else {}) for e in r['evidence']]}
                            for r in t['source_roles']],
           'kc_candidates': t['kc_candidates'], 'domain_profile': t['domain_profile'], 'chapter_ordering': {k: v for k, v in a['rep']['chapter_ordering'].items()},
           'chapters': chapters,
           'gap_accounting': {k: v for k, v in t['gap_accounting'].items() if k != 'gaps'},
           'gap_records': t['gap_accounting']['gaps'],
           'propagation_rules': t['propagation_rules'], 'propagation_summary': t['propagation_summary'],
           'kc_level_assignments_after': t['kc_level_assignments'],
           'review_queue': t['review_queue'], 'semantic_review_contract': t['semantic_review_contract'],
           'planned_actions_if_all_chapters': a['rep']['planned_actions']}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(json.dumps({'before': doc['before'], 'after': doc['after']}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
