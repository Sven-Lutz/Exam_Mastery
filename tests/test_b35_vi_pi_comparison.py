"""B35 regression for the V4 P1 defect 'methodically misleading VI/PI cost comparison' (MDP studio).
The V4 page mixed an estimated n^3/3 cost with counted transitions, stopped VI with the oracle V* and PI exactly, and
declared the result 'fair'. These tests pin the repaired method: practical stopping rules, instrumented counts that
match an independent Python count, separated quantities, declared cost model, verdict derived from the numbers."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_mastery.labs import mdp_studio as MS
from exam_mastery import typeset

ROBOT = {'id': 'robot', 'title': 'Robot', 'kind': 'graph', 'states': ['H', 'L'], 'gamma': 0.9, 'policy': {'H': 'search', 'L': 'wait'},
         'transitions': [{'s': 'H', 'a': 'search', 'r': 2, 'next': {'H': 0.7, 'L': 0.3}},
                         {'s': 'H', 'a': 'wait', 'r': 1, 'next': {'H': 1}},
                         {'s': 'L', 'a': 'search', 'r': -1, 'next': {'H': 0.4, 'L': 0.6}},
                         {'s': 'L', 'a': 'wait', 'r': 1, 'next': {'L': 1}},
                         {'s': 'L', 'a': 'recharge', 'r': 0, 'next': {'H': 1}}]}


def py_counts(sc):
    """Independent re-implementation of the declared cost model (float mul/div executed)."""
    S, g = sc['states'], sc['gamma']; T = {(t['s'], t['a']): t for t in sc['transitions']}
    A = {s: [a for (x, a) in T if x == s] for s in S}
    def q(V, s, a, c):
        t = T[(s, a)]; c[0] += 2 * len(t['next']); return t['r'] + sum(g * p * V[n] for n, p in t['next'].items())
    c = [0]; V = {s: 0.0 for s in S}; k = 0; thr = 1e-6 * (1 - g) / (2 * g)
    while True:
        W = {s: max(q(V, s, a, c) for a in A[s]) for s in S}; k += 1
        d = max(abs(W[s] - V[s]) for s in S); V = W
        if d < thr: break
    for s in S:                       # greedy policy extraction after stopping is part of VI's work
        for a in A[s]: q(V, s, a, c)
    return k, c[0]


class Comparison(unittest.TestCase):
    def test_source_no_longer_claims_fairness(self):
        src = Path(MS.__file__).read_text()
        self.assertNotIn('der Vergleich ist fair', src)
        self.assertIn('Kostenmodell (deklariert)', src)
        self.assertNotIn('n * n * n / 3', src, 'estimated Gauss cost must not be mixed with counted work')

    def test_browser_counts_match_independent_count_and_verdict_is_consistent(self):
        from playwright.sync_api import sync_playwright
        d = Path(tempfile.mkdtemp()); typeset._assets(d)
        html = MS.page([MS.validate(json.loads(json.dumps(ROBOT)))], 'Studio', 'Kurs', mathjax='assets/tex-svg-full.js')
        (d / 's.html').write_text(html, encoding='utf-8')
        k_py, ops_py = py_counts(ROBOT)
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto((d / 's.html').as_uri()); pg.wait_for_timeout(500)
            pg.click('nav.md button[data-m="compare"]'); pg.click('[data-cmp="eq"]')
            k = int(pg.inner_text('#cmp-vi')); ops = int(pg.inner_text('#cmp-work-vi'))
            it = int(pg.inner_text('#cmp-pi')); pops = int(pg.inner_text('#cmp-work-pi'))
            mvi = int(pg.inner_text('#cmp-model-vi')); mpi = int(pg.inner_text('#cmp-model-pi'))
            verdict = pg.inner_text('#cmp-verdict'); table = pg.inner_text('#cmp-table'); b.close()
        self.assertGreaterEqual(mvi, ops, 'model is an upper bound of the instrumented VI count')
        self.assertGreaterEqual(mpi, pops, 'model is an upper bound of the instrumented PI count')
        self.assertEqual(errs, [])
        self.assertEqual((k, ops), (k_py, ops_py), 'VI iterations/operations must equal the independent count')
        self.assertGreater(pops, 0); self.assertGreaterEqual(it, 1)
        win = 'Wertiteration' if ops / pops < 0.8 else 'Policy Iteration' if ops / pops > 1.25 else 'keines deutlich'
        self.assertIn(win, verdict)
        self.assertIn(str(k), verdict); self.assertIn(str(it), verdict)
        for row in ('Abbruchregel', 'Theoretische Kosten', 'Modellierte Kosten', 'Iterationen', 'Instrumentierte', 'Erreichter Fehler', 'Laufzeit'):
            self.assertIn(row, table)


if __name__ == '__main__':
    unittest.main()
