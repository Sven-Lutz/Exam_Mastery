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
