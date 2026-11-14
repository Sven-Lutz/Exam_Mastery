"""B21: finite-MDP reference model and lab.

Reference values were recomputed independently with NumPy (linear solve / synchronous sweeps) and agree with the
slides of RL lecture 02 "Optimal Decision Making" (WS 2026/27): cleaning robot (slides 16-33) and the 4x3 grid world
(noise 0.2, gamma 0.9, living reward 0; Russell & Norvig convention, exits valued at their reward).
"""
import json
import math
import random

import pytest

from exam_mastery.labs import build as B, models as M, pedagogy as P

ROBOT = {'states': ['High', 'Low'], 'gamma': 0.9, 'policy': {'High': 'search', 'Low': 'search'}, 'focus': 'High',
         'transitions': [{'s': 'High', 'a': 'search', 'r': 2, 'next': {'High': .7, 'Low': .3}},
                         {'s': 'High', 'a': 'wait', 'r': .5, 'next': {'High': 1}},
                         {'s': 'Low', 'a': 'search', 'r': -2, 'next': {'Low': .6, 'High': .4}},
                         {'s': 'Low', 'a': 'wait', 'r': .5, 'next': {'Low': 1}},
                         {'s': 'Low', 'a': 'recharge', 'r': 0, 'next': {'High': 1}}]}


def r2(V):
    return {s: round(v, 2) for s, v in V.items()}


def test_robot_policy_evaluation_exact():
    m = M.mdp_check(ROBOT)
    assert r2(M.mdp_eval_exact(m, {'High': 'search', 'Low': 'search'})) == {'High': 5.21, 'Low': -0.27}
    assert r2(M.mdp_eval_exact(m, {'High': 'wait', 'Low': 'wait'})) == {'High': 5.0, 'Low': 5.0}
    assert r2(M.mdp_eval_exact(m, {'High': 'search', 'Low': 'recharge'})) == {'High': 15.75, 'Low': 14.17}


def test_robot_sweeps_value_iteration_and_improvement():
    m = M.mdp_check(ROBOT); pol = {'High': 'search', 'Low': 'recharge'}
    pe = M.mdp_eval_sweeps(m, pol, 10)
    assert [r2(pe[k]) for k in (1, 2, 3)] == [{'High': 2.0, 'Low': 0.0}, {'High': 3.26, 'Low': 1.8}, {'High': 4.54, 'Low': 2.93}]
    assert r2(pe[10]) == {'High': 10.38, 'Low': 8.81}
    vi = M.mdp_value_iteration(m, 100)
    assert {s: round(v, 3) for s, v in vi[2].items()} == {'High': 3.395, 'Low': 1.8}
    assert vi[3]['High'] == pytest.approx(4.625, abs=6e-4) and vi[3]['Low'] == pytest.approx(3.0555, abs=6e-4)
    assert r2(M.mdp_optimal(m)) == {'High': 15.75, 'Low': 14.17}
    # one improvement step from "always search" already reaches the optimal policy
    v0 = M.mdp_eval_exact(m, {'High': 'search', 'Low': 'search'})
    assert round(M.mdp_q(m, v0, 'Low', 'recharge'), 2) == 4.68 and round(M.mdp_q(m, v0, 'High', 'wait'), 2) == 5.18
    assert M.mdp_greedy(m, v0) == pol
    assert M.mdp_policy_iteration(m, {'High': 'search', 'Low': 'search'})[-1]['policy'] == pol


def _gridworld():
    S = [(c, r) for c in range(1, 5) for r in range(1, 4) if (c, r) != (2, 2)]
    ex = {(4, 3): 1.0, (4, 2): -1.0}; D = {'N': (0, 1), 'E': (1, 0), 'S': (0, -1), 'W': (-1, 0)}; side = {'N': 'EW', 'S': 'EW', 'E': 'NS', 'W': 'NS'}
    name = lambda s: f'{s[0]}{s[1]}'
    mv = lambda s, d: (lambda n: n if n in S else s)((s[0] + D[d][0], s[1] + D[d][1]))
    T = []
    for s in S:
        if s in ex:
            T.append({'s': name(s), 'a': 'exit', 'r': ex[s], 'next': {'done': 1}}); continue
        for a in 'NESW':
            nxt = {}
            for d, p in ((a, .8), (side[a][0], .1), (side[a][1], .1)):
                nxt[name(mv(s, d))] = nxt.get(name(mv(s, d)), 0) + p
            T.append({'s': name(s), 'a': a, 'r': 0, 'next': nxt})
    return {'states': [name(s) for s in S] + ['done'], 'gamma': 0.9, 'transitions': T}


def test_gridworld_value_iteration_matches_slides():
    m = M.mdp_check(_gridworld()); h = M.mdp_value_iteration(m, 100)
    row = lambda V: [round(V[f'{c}{r}'], 2) for r in (3, 2, 1) for c in range(1, 5) if (c, r) != (2, 2)]
    assert row(h[2]) == [0.0, 0.0, 0.72, 1.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0]
    assert row(h[5]) == [0.51, 0.72, 0.84, 1.0, 0.27, 0.55, -1.0, 0.0, 0.22, 0.37, 0.13]
    assert row(h[100]) == [0.64, 0.74, 0.85, 1.0, 0.57, 0.57, -1.0, 0.49, 0.43, 0.48, 0.28]
    assert M.mdp_greedy(m, h[100])['32'] == 'N' and M.mdp_greedy(m, h[100])['21'] == 'W'


def test_contraction_bound_holds_on_random_mdps():
    rnd = random.Random(3)
    for _ in range(30):
        n = rnd.randint(1, 5); S = [f's{i}' for i in range(n)]; T = []
        for s in S:
            for a in 'ab'[:rnd.randint(1, 2)]:
                w = [rnd.random() for _ in S]; z = sum(w)
                T.append({'s': s, 'a': a, 'r': rnd.uniform(-3, 3), 'next': {t: x / z for t, x in zip(S, w)}})
        m = M.mdp_check({'states': S, 'gamma': rnd.uniform(0, .95), 'transitions': T}); vs = M.mdp_optimal(m)
        e = [max(abs(V[s] - vs[s]) for s in S) for V in M.mdp_value_iteration(m, 25)]
        assert all(e[k + 1] <= m['gamma'] * e[k] + 1e-9 for k in range(25))


@pytest.mark.parametrize('bad', [
    {'gamma': 1.0}, {'gamma': -0.1}, {'states': ['High', 'High']}, {'states': []},
    {'transitions': [{'s': 'High', 'a': 'x', 'r': 0, 'next': {'High': .5}}]},
    {'transitions': [{'s': 'High', 'a': 'x', 'r': 0, 'next': {'Mars': 1}}]},
    {'transitions': [{'s': 'High', 'a': 'x', 'r': 0, 'next': {'High': 1.2, 'Low': -.2}}]},
    {'transitions': [{'s': 'High', 'a': 'x', 'r': 0, 'next': {'High': 1}}, {'s': 'High', 'a': 'x', 'r': 1, 'next': {'High': 1}}]}])
def test_invalid_mdps_are_rejected(bad):
    with pytest.raises(ValueError):
        M.mdp_check({**ROBOT, **bad})


def test_spec_rejects_bad_policy_and_too_many_states():
    from exam_mastery.labs.mdp import MdpError
    MdpError = (MdpError, B.LabError)
    with pytest.raises(MdpError):
        B.mdp_spec('rl/x', 'x', ['kc'], [], {**ROBOT, 'policy': {'High': 'fly', 'Low': 'search'}})
    with pytest.raises(MdpError):
        B.mdp_spec('rl/x', 'x', ['kc'], [], _gridworld())


def test_spec_pedagogy_and_render(tmp_path):
    s = B.mdp_spec('rl/cleaning-robot', 'Reinigungsroboter', ['kc-x'], ['Vorlesung 02, Folie 16'], ROBOT, 'RL')
    P.validate(s)  # raises PedagogyError on an incomplete learning sequence
    p = B.render(s, tmp_path)
    html = p.read_text()
    assert '"kind": "mdp"' in html or '"kind":"mdp"' in html
    assert 'style="' not in html.split('<body', 1)[1]  # CSP: no inline styles in the body


def test_python_js_parity_in_browser(tmp_path):
    pw = pytest.importorskip('playwright.sync_api')
    s = B.mdp_spec('rl/cleaning-robot', 'Reinigungsroboter', ['kc-x'], ['Vorlesung 02'], ROBOT, 'RL')
    page = B.render(s, tmp_path)
    try:
        ctx = pw.sync_playwright().start(); b = ctx.chromium.launch()
    except Exception as e:  # no browser installed on this host
        pytest.skip(f'chromium unavailable: {e}')
    try:
        pg = b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(page.resolve().as_uri()); pg.wait_for_function('document.documentElement.dataset.emReady==="1"')
        rnd = random.Random(5); worst = 0.0
        for _ in range(40):
            n = rnd.randint(1, 6); S = [f's{i}' for i in range(n)]; T = []
            for st in (S[:-1] if n > 1 and rnd.random() < .3 else S):
                for a in 'abc'[:rnd.randint(1, 3)]:
                    w = [rnd.random() for _ in S]; z = sum(w)
                    T.append({'s': st, 'a': a, 'r': round(rnd.uniform(-3, 3), 2), 'next': {t: x / z for t, x in zip(S, w)}})
            d = {'states': S, 'gamma': round(rnd.uniform(0, .98), 2), 'transitions': T}; m = M.mdp_check(d)
            pol = {st: m['actions'][st][0] for st in S if m['actions'][st]}
            js = pg.evaluate('''d=>{const M=EM.models,m=M.mdpCheck(d[0]);return {ex:M.mdpEvalExact(m,d[1]),vi:M.mdpValueIteration(m,7)[7],
              pe:M.mdpEvalSweeps(m,d[1],5)[5],opt:M.mdpOptimal(m),gr:M.mdpGreedy(m,M.mdpOptimal(m)),pi:M.mdpPolicyIteration(m,d[1]).map(x=>x.policy)}}''', [d, pol])
            py = {'ex': M.mdp_eval_exact(m, pol), 'vi': M.mdp_value_iteration(m, 7)[7], 'pe': M.mdp_eval_sweeps(m, pol, 5)[5], 'opt': M.mdp_optimal(m)}
            for k in py:
                worst = max(worst, max(abs(js[k][x] - py[k][x]) for x in S))
            assert js['gr'] == M.mdp_greedy(m, py['opt'])
            assert js['pi'] == [x['policy'] for x in M.mdp_policy_iteration(m, pol)]
        assert worst < 1e-9, worst
        bad = pg.evaluate('''()=>{const out=[];for(const d of [{states:["a"],gamma:1,transitions:[]},{states:["a"],gamma:.5,transitions:[{s:"a",a:"x",r:0,next:{a:.4}}]}]){try{EM.models.mdpCheck(d);out.push("ok")}catch(e){out.push("err")}}return out}''')
        assert bad == ['err', 'err']
        assert not errs, errs
    finally:
        b.close(); ctx.stop()
