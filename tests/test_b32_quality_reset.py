"""B32/B33 quality reset: design tokens, figure kit, MDP studio validation/golden values, subject lab routing,
Anki render gate for absolute-value bars and norms, layout-lint report status. All models here are author-made toy
models (no course material)."""
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

from exam_mastery import design_tokens as T
from exam_mastery import figure_kit as K
from exam_mastery.labs import mdp_studio as MS

TOY = {'id': 'toy', 'title': 'Toy', 'kind': 'graph', 'states': ['A', 'B'], 'gamma': 0.5, 'policy': {'A': 'go', 'B': 'stay'},
       'transitions': [{'s': 'A', 'a': 'go', 'r': 1, 'next': {'B': 1}}, {'s': 'A', 'a': 'stay', 'r': 0, 'next': {'A': 1}},
                       {'s': 'B', 'a': 'stay', 'r': 2, 'next': {'B': 1}}, {'s': 'B', 'a': 'back', 'r': 0, 'next': {'A': 0.5, 'B': 0.5}}]}


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class DesignTokens(unittest.TestCase):
    def test_every_semantic_role_is_readable_on_white_and_on_its_tint(self):
        for role, tok in T.ROLE.items():
            self.assertGreaterEqual(contrast(T.TOKENS[tok], '#FFFFFF'), 4.5, role)
            if tok + '_l' in T.TOKENS:
                self.assertGreaterEqual(contrast(T.TOKENS[tok], T.TOKENS[tok + '_l']), 4.0, role)

    def test_roles_are_distinguishable_in_greyscale(self):
        lums = sorted(_lum(T.TOKENS[t]) for t in T.ROLE.values())
        self.assertEqual(len(lums), len(T.ROLE))           # each role also carries a label/border cue; colours are distinct
        self.assertGreater(len({round(x, 3) for x in lums}), 4)

    def test_heatmap_colour_is_symmetric_and_neutral_at_zero(self):
        self.assertEqual(T.diverging(0, -1, 1).lower(), '#ffffff')
        self.assertNotEqual(T.diverging(1, -1, 1), T.diverging(-1, -1, 1))


class FigureKit(unittest.TestCase):
    def svg_ok(self, svg):
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith('svg'))
        self.assertIn('<title', svg)
        return svg

    def test_grid_world_prints_values_not_only_colour(self):
        svg = self.svg_ok(K.grid_world({'cols': 2, 'rows': 1, 'values': {'1,1': 0.25, '2,1': -1.0}, 'kinds': {'2,1': 'terminal'},
                                        'arrows': {'1,1': 'E'}, 'decimals': 2, 'title': 'toy grid'}))
        self.assertIn('0.25', svg)
        self.assertTrue('−1.00' in svg or '-1.00' in svg)

    def test_generic_kinds_render_for_non_rl_content(self):
        # reuse outside RL: a legal decision path and a two-step loop
        self.svg_ok(K.flow({'w': 520, 'box_w': 300, 'title': 'Prüfschema', 'steps': [
            {'label': 'Ist der Anspruch entstanden?', 'kind': 'decision', 'yes': 'ja', 'note': 'nein: kein Anspruch'},
            {'label': 'Anspruch durchsetzbar', 'kind': 'end'}]}))
        self.svg_ok(K.loop({'title': 'Markt', 'left': {'title': 'Anbieter', 'lines': ['setzt Preis']}, 'right': {'title': 'Nachfrage', 'lines': ['reagiert']},
                            'top': 'Preis', 'bottom': ['Absatz']}))

    def test_state_graph_contains_every_label(self):
        svg = self.svg_ok(K.state_graph({'w': 400, 'h': 200, 'title': 'toy', 'nodes': [{'id': 'A', 'label': 'A', 'x': 80, 'y': 100}, {'id': 'B', 'label': 'B', 'x': 320, 'y': 100}],
                                         'edges': [{'from': 'A', 'to': 'B', 'kind': 'transition', 'label': '0.3'}]}))
        for s in ('A', 'B', '0.3'):
            self.assertIn(s, svg)


class Studio(unittest.TestCase):
    def test_validation_rejects_bad_models(self):
        bad = json.loads(json.dumps(TOY)); bad['transitions'][3]['next'] = {'A': 0.6, 'B': 0.6}
        with self.assertRaises(MS.StudioError):
            MS.validate(bad)
        bad = dict(TOY, gamma=1.0)
        with self.assertRaises(MS.StudioError):
            MS.validate(bad)
        bad = dict(TOY, policy={'A': 'fly'})
        with self.assertRaises(MS.StudioError):
            MS.validate(bad)

    def test_golden_values_are_exact(self):
        g = MS.golden(MS.validate(json.loads(json.dumps(TOY))))
        # V(B) = 2/(1-0.5) = 4 ; V(A) = 1 + 0.5*4 = 3 (go) vs 0.5*V(A) (stay)
        self.assertAlmostEqual(g['V_star']['B'], 4.0); self.assertAlmostEqual(g['V_star']['A'], 3.0)
        self.assertAlmostEqual(g['VI'][1]['A'], 1.0); self.assertAlmostEqual(g['VI'][2]['A'], 2.0)

    def test_page_embeds_scenario_and_all_learning_modes(self):
        html = MS.page([MS.validate(json.loads(json.dumps(TOY)))], 'Studio', 'Kurs')
        for m in ('Policy-Explorer', 'Wertiteration', 'Policy Iteration', 'Diskont', 'Aufgaben', 'studio-data'):
            self.assertIn(m, html)
        self.assertIn('mode: st && st.mode', html)          # reset keeps the learner in the current mode (E2E regression)


class LabRouting(unittest.TestCase):
    def test_sequence_lab_is_not_attached_to_an_rl_chapter(self):
        from exam_mastery.labs.integrate import catalog_requests, ROUTED_OUT
        kcs = [{'kc_id': 'k1', 'statement': 'Konvergenz der Wertiteration im Markov-Entscheidungsprozess mit Diskontfaktor und Policy',
                'topic_text': 'reinforcement learning Bellman value iteration epsilon convergence of a sequence', 'source_anchor_ids': ['x']}]
        out = catalog_requests(kcs)
        self.assertNotIn('analysis/folgen-epsilon', [r['lab_id'] for r in out])
        self.assertIn('analysis/folgen-epsilon', [r['lab_id'] for r in ROUTED_OUT])


class AnkiRenderGate(unittest.TestCase):
    def test_absolute_values_and_norms_never_become_tables(self):
        from exam_mastery.anki_v2 import _html, render_lint
        for src in ('\\(|G_t| \\le R_{\\max}/(1-\\gamma)\\)', '\\(\\|U - V\\|_\\infty\\)', '|a| und |b| sind Beträge'):
            out = _html(src)
            self.assertNotIn('<table', out, src)
            c = {'kind': 'math', 'front': 'Frage?', 'answer': src}
            self.assertEqual(render_lint(c, {'Front': 'Frage?', 'Answer': out}), [], src)

    def test_gate_catches_a_misread_table(self):
        from exam_mastery.anki_v2 import render_lint
        c = {'kind': 'math', 'front': 'F?', 'answer': '|a|b|'}
        self.assertTrue(render_lint(c, {'Front': 'F?', 'Answer': '<table><tr><td>a</td></tr></table>'}))


class LayoutLint(unittest.TestCase):
    def test_report_status(self):
        from exam_mastery.chapter_publish import _layout_lint
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(_layout_lint(td, 'x')['status'], 'NOT_RUN')
            (Path(td) / '..x.main.layout_lint.json').write_text(json.dumps({'inline_math_reflowed': ['a'], 'overflow': [], 'broken_images': []}))
            self.assertEqual(_layout_lint(td, 'x')['status'], 'PASS')
            (Path(td) / '..x.main.layout_lint.json').write_text(json.dumps({'inline_math_reflowed': [], 'overflow': [{'tag': 'svg'}], 'broken_images': []}))
            self.assertEqual(_layout_lint(td, 'x')['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()


class TokenDrift(unittest.TestCase):
    def test_typesetter_and_studio_use_the_token_values(self):
        import re
        from exam_mastery import typeset
        src = (Path(MS.__file__).read_text() + typeset.CSS).upper()
        for name in ('navy', 'petrol', 'blue', 'gold', 'coral', 'green', 'violet'):
            self.assertIn(T.TOKENS[name].upper(), src, name)
        self.assertNotIn('#A8781E', src)                    # the old, too light gold (3.9:1 on white) must not come back


# ---------------------------------------------------------------- B33
def _book(text='Living reward erklärt', fig='f-a', kc='kc-1', items=('i1',)):
    return {'sections': [{'title': 'S', 'blocks': [{'type': 'text', 'md': text}, {'type': 'figure', 'id': fig},
                                                   {'type': 'example', 'title': 'Bsp', 'kc_ids': [kc]}]}],
            'stages': [{'title': 'St', 'items': [{'id': i, 'prompt': 'p', 'solution': {'answer': 'a'}} for i in items]}],
            'exam': {}, 'cards': [], 'figures': {}}


class IssueLifecycle(unittest.TestCase):
    def run_ast(self, issues, decisions, book):
        from exam_mastery import issue_lifecycle as IL
        with tempfile.TemporaryDirectory() as td:
            ch = Path(td) / 'run' / 'chapters' / 'ch-x'; ch.mkdir(parents=True)
            (ch / 'content_ast.json').write_text(json.dumps({'open_issues': issues}))
            return IL.evaluate(ch, book, decisions=dict({'schema': IL.SCHEMA, 'decisions': {}, 'rules': []}, **decisions),
                               elements={'e1': ('src-a', 4), 'e2': ('src-b', 9)}, gate_codes=set())

    def test_states_rechecks_duplicates_and_gate(self):
        iss = [{'issue_id': 'a', 'code': 'ESSENTIAL_VISUAL_UNRESOLVED', 'severity': 'blocker', 'element_ids': ['e1'], 'detail': 'd'},
               {'issue_id': 'b', 'code': 'ESSENTIAL_VISUAL_UNRESOLVED', 'severity': 'blocker', 'element_ids': ['e1'], 'detail': 'd'},
               {'issue_id': 'c', 'code': 'VISUAL_REVIEW_PENDING', 'element_ids': ['e2'], 'detail': 'x'},
               {'issue_id': 'd', 'code': 'NOTE', 'object_id': 'o', 'detail': 'y'}]
        dec = {'rules': [{'codes': ['ESSENTIAL_VISUAL_UNRESOLVED'], 'pages': [['src-a', 4]], 'state': 'RESOLVED', 'recheck': {'kind': 'figure_in_book', 'figures': ['f-a']}},
                         {'codes': ['VISUAL_REVIEW_PENDING'], 'source_not': 'src-a', 'state': 'REASSIGNED', 'reason': 'other lecture'}],
               'decisions': {'d': {'state': 'ACCEPTED_RISK', 'reason': 'documented'}}}
        r = self.run_ast(iss, dec, _book())
        st = {x['issue_id']: x['state'] for x in r['issues']}
        self.assertEqual(st, {'a': 'RESOLVED', 'b': 'DUPLICATE', 'c': 'REASSIGNED', 'd': 'ACCEPTED_RISK'})
        self.assertEqual(r['gate'], 'PASS')
        # regression: the figure disappears from the book -> the blocker re-opens and the gate blocks
        r = self.run_ast(iss, dec, _book(fig='f-other'))
        self.assertEqual({x['issue_id']: x['state'] for x in r['issues']}['a'], 'OPEN')
        self.assertEqual(r['gate'], 'BLOCKED')

    def test_reason_required_and_kc_example_recheck(self):
        iss = [{'issue_id': 'a', 'code': 'X', 'object_id': 'o1', 'detail': ''}, {'issue_id': 'b', 'code': 'Y', 'object_id': 'o2', 'detail': ''}]
        dec = {'decisions': {'a': {'state': 'NOT_APPLICABLE'}, 'b': {'state': 'RESOLVED', 'recheck': {'kind': 'kc_worked_example', 'kc': 'kc-9'}}}}
        r = self.run_ast(iss, dec, _book())
        self.assertEqual([x['state'] for x in r['issues']], ['OPEN', 'OPEN'])
        self.assertIn('without a reason', r['issues'][0]['recheck_failed'])


class ExamMapping(unittest.TestCase):
    def test_classes(self):
        from exam_mastery.exam_mapping import classify
        vocab = {'discount', 'corridor', 'bellman', 'iteration', 'optimal'}
        self.assertEqual(classify('Does it Work?', 's1', '', {'s0'}, {}, vocab)[0], 'NOT_AN_ASSESSMENT')
        self.assertEqual(classify('Q: What does DQN become for C to infinity?', 's2', '', {'s0'}, {'s2': 'ch-dqn'}, vocab)[0], 'OTHER_CHAPTER_SOURCE')
        c, ev = classify('Solve for the discount such that left and right are equally good in the corridor (optimal)?', 'tut', 'Example Exam Questions Q2',
                         {'s0'}, {}, vocab)
        self.assertEqual(c, 'CANDIDATE_FOR_CHAPTER'); self.assertTrue(ev['example_exam'])
        self.assertEqual(classify('a) What is the benefit of the minimum in SAC?', 'tut', 'Example Exam Questions Q4', {'s0'}, {}, vocab)[0], 'PRACTICE_OTHER_TOPIC')


class PageAuditAndGuard(unittest.TestCase):
    def test_monotone_text_stretch_is_found_only_in_the_core(self):
        import pymupdf
        from exam_mastery.chapter_publish import _layout_lint
        with tempfile.TemporaryDirectory() as td:
            doc = pymupdf.open()
            kinds = 'cFtttFtt'                      # cover, figure page, 3 text pages, figure page, back matter
            for k in kinds:
                pg = doc.new_page()
                pg.insert_text((72, 72), 'Text ' * 200 if k != 'F' else 'Abbildung 3.1 Ein Diagramm')
            doc.save(Path(td) / '1_Lehrbuch.pdf')
            (Path(td) / '..1_Lehrbuch.main.layout_lint.json').write_text(json.dumps({'inline_math_reflowed': [], 'overflow': [], 'broken_images': []}))
            r = _layout_lint(td, '1_Lehrbuch')
            self.assertEqual(r['page_audit']['monotone_runs'], [[3, 4, 5]])
            self.assertEqual(r['status'], 'WARN')

    def test_regression_guard_ratchet(self):
        from exam_mastery.chapter_publish import regression_guard
        rep = lambda fails: {'numeric_checks': {'counts': {'FAIL': fails}}, 'documents': {}, 'products': {'anki': {'cards': 10}}}
        with tempfile.TemporaryDirectory() as td:
            ch = Path(td) / 'course' / 'run' / 'chapters' / 'ch-x'; ch.mkdir(parents=True)
            self.assertEqual(regression_guard(ch, rep(0), _book())['status'], 'BASELINE_CREATED')
            self.assertEqual(regression_guard(ch, rep(0), _book())['status'], 'PASS')
            r = regression_guard(ch, rep(2), _book())
            self.assertEqual(r['status'], 'FAIL'); self.assertEqual(r['regressions'], {'numeric_fail': [0, 2]})
            self.assertEqual(regression_guard(ch, rep(2), _book())['status'], 'FAIL')     # baseline was not lowered


class B33Figures(unittest.TestCase):
    def test_timeline_marks_end_and_open_continuation(self):
        svg = K.timeline({'title': 'Episoden', 'rows': [{'label': 'episodisch', 'steps': [{'label': 's0', 'value': '0'}, {'label': 'Ende', 'kind': 'end'}]},
                                                        {'label': 'fortlaufend', 'steps': [{'label': 's0', 'value': '+1', 'weight': '1'}, {'kind': 'more'}]}]})
        ET.fromstring(svg)
        self.assertIn('Ende', svg); self.assertIn('…', svg); self.assertIn('stroke-dasharray', svg)

    def test_studio_has_comparison_mode(self):
        html = MS.page([MS.validate(json.loads(json.dumps(TOY)))], 'Studio', 'Kurs')
        self.assertIn("['compare', 'VI vs. PI']", html)
        self.assertIn('place(', html)                        # label collision avoidance in the graph


class AnkiPunctuation(unittest.TestCase):
    def test_short_math_keeps_its_punctuation_long_math_may_wrap(self):
        from exam_mastery.anki_v2 import _html
        self.assertIn('white-space:nowrap', _html('Bei \\(|r| \\le R_{\\max}\\)?'))
        long = '\\(' + ' + '.join(f'x_{i}' for i in range(30)) + '\\).'
        self.assertNotIn('white-space:nowrap', _html(long))
