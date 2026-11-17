"""B35 lab learning sequences: task-model rules (negative fixtures), and browser E2E against independent Python
reference values, including a model edit that must change answers and explanations consistently."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery.labs import mdp_studio as MS
from exam_mastery.labs.task_model import validate
from exam_mastery.labs.mdp_sequences import SEQUENCES, RUNTIME
from exam_mastery import typeset
from test_b35_vi_pi_comparison import ROBOT


def T(sc):
    return {(t['s'], t['a']): t for t in sc['transitions']}


def V1(sc):
    g, TT = sc['gamma'], T(sc)
    q0 = lambda s, a: TT[(s, a)]['r']
    return {s: max(q0(s, a) for (x, a) in TT if x == s) for s in sc['states']}


def qv(sc, V, s, a):
    t = T(sc)[(s, a)]; return t['r'] + sc['gamma'] * sum(p * V[n] for n, p in t['next'].items())


def opt_action(sc, s, g):
    sc = dict(sc, gamma=g); V = {x: 0.0 for x in sc['states']}
    for _ in range(3000):
        V = {x: max(qv(sc, V, x, a) for (y, a) in T(sc) if y == x) for x in sc['states']}
    return max((a for (y, a) in T(sc) if y == s), key=lambda a: qv(sc, V, s, a))


def vi_ratio_bin(sc):
    g = sc['gamma']
    def sweeps(eps):
        thr, V, k = eps * (1 - g) / (2 * g), {x: 0.0 for x in sc['states']}, 0
        while True:
            W = {x: max(qv(sc, V, x, a) for (y, a) in T(sc) if y == x) for x in sc['states']}; k += 1
            d = max(abs(W[x] - V[x]) for x in V); V = W
            if d < thr: return k
    r = sweeps(1e-6) / sweeps(1e-2)
    return 'etwa gleich (× 1)' if r < 1.4 else 'etwa × 2' if r < 2.5 else 'etwa × 3' if r < 3.6 else 'mehr als × 4'


class TaskModelRules(unittest.TestCase):
    def test_shipped_sequences_valid(self):
        self.assertEqual([f for q in SEQUENCES for f in validate(q, RUNTIME)], [])

    def test_negative_fixtures(self):
        base = copy.deepcopy(SEQUENCES[0])
        cases = {'T1': lambda q: q['success'].pop('criterion'),
                 'T2': lambda q: q['steps'][1].update(answer=3),
                 'T3': lambda q: q['steps'][1].pop('diagnose'),
                 'T4': lambda q: q['steps'][1].update(hints=['h_reward']),
                 'T5': lambda q: q.update(steps=[s for s in q['steps'] if s['kind'] != 'transfer']),
                 'T6': lambda q: q['steps'][1].update(explain='Die Antwort ist 3.4')}
        for code, f in cases.items():
            q = copy.deepcopy(base); f(q)
            self.assertIn(code, {x['code'] for x in validate(q, RUNTIME)}, code)
        q = copy.deepcopy(base); q['steps'][1]['compute'] = 'nope'
        self.assertIn('T2', {x['code'] for x in validate(q, RUNTIME)})


class Browser(unittest.TestCase):
    def test_sequences_end_to_end(self):
        from playwright.sync_api import sync_playwright
        d = Path(tempfile.mkdtemp()); typeset._assets(d)
        (d / 's.html').write_text(MS.page([MS.validate(json.loads(json.dumps(ROBOT)))], 'Studio', 'Kurs', mathjax='assets/tex-svg-full.js'))
        V = V1(ROBOT); s, a = 'H', 'wait'                     # focus = first state with >1 actions; A2 uses its 2nd action
        truth = qv(ROBOT, V, s, a); no_gamma = T(ROBOT)[(s, a)]['r'] + sum(p * V[n] for n, p in T(ROBOT)[(s, a)]['next'].items())
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto((d / 's.html').as_uri()); pg.wait_for_timeout(400)
            pg.click('nav.md button[data-m="seq"]'); pg.click('#sq-next')                     # A1 worked example
            pg.fill('#sq-in', f'{no_gamma:.4f}'); pg.click('#sq-check')                      # typical error
            self.assertIn('Diskont', pg.inner_text('#sq-fb'))
            self.assertNotIn(f'{truth:.4f}', pg.inner_text('#view'), 'solution must not be revealed after an error')
            pg.click('#sq-hint'); self.assertIn('Sofortbelohnung', pg.inner_text('#view'))
            pg.fill('#sq-in', f'{truth:.4f}'.replace('.', ',')); pg.click('#sq-check')       # German decimal comma
            self.assertIn('Richtig', pg.inner_text('#sq-fb'))
            # model edit -> computed truth follows the model (no stale answer)
            got = pg.evaluate("() => { st.transitions.find(t => t.s === 'H' && t.a === 'wait').r = 5; return RT.q_value(model(sc)).truth; }")
            mod = copy.deepcopy(ROBOT); next(t for t in mod['transitions'] if t['s'] == 'H' and t['a'] == 'wait')['r'] = 5
            self.assertAlmostEqual(got, qv(mod, V1(mod), 'H', 'wait'), places=9)
            pg.click('nav.md button[data-m="tasks"]') if pg.query_selector('nav.md button[data-m="tasks"]') else None
            self.assertTrue(pg.query_selector('#tasks-orig') is not None or 'Keine Aufgaben' in pg.inner_text('#view'),
                            'legacy fixed-answer tasks must say they use the original model after an edit')
            pg.click('nav.md button[data-m="seq"]')
            pg.evaluate("() => { st.transitions.find(t => t.s === 'H' && t.a === 'wait').r = 0.5; }")
            # sequence B: predicted action at gamma 0.1 equals independent optimum
            pg.click('[data-seq="B"]')
            choices = pg.eval_on_selector_all('input[name=sqc]', 'els => els.map(e => e.value)')
            pg.check(f'input[name=sqc][value="{opt_action(ROBOT, "H", 0.1)}"]'); pg.click('#sq-check')
            self.assertIn('Richtig', pg.inner_text('#sq-fb'), choices)
            # sequence C: PI iterations do not depend on epsilon
            pg.click('[data-seq="C"]'); pg.check(f'input[name=sqc][value="{vi_ratio_bin(ROBOT)}"]'); pg.click('#sq-check')
            fb = pg.inner_text('#sq-fb')
            b.close()
        self.assertEqual(errs, [])
        self.assertIn('Richtig', fb); self.assertRegex(fb, r'Gemessen: \d+ Sweeps')


if __name__ == '__main__':
    unittest.main()
