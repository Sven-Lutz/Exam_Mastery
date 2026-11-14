"""Minimal infrastructure for a later controlled comparison (static sequence A vs adaptive track B).

Provides: parallel test forms generated from the same models (isomorphic items, different numbers), a deterministic
counterbalanced assignment, and the analysis plan as data. It contains NO participant data and NO simulated results.
See docs/EVALUATION_PROTOCOL.md.
"""
import hashlib

from ..labs import models as M


def assign(participant_code, stratum=''):
    """Deterministic 2x2 counterbalancing: condition (A/B) x form order (X->Y / Y->X), balanced within strata by hash
    parity. participant_code must be a pseudonym, never a name."""
    h = int(hashlib.sha256((stratum + '|' + participant_code).encode()).hexdigest(), 16)
    return {'condition': 'A_static' if h % 2 == 0 else 'B_adaptive', 'form_order': ['X', 'Y'] if (h >> 1) % 2 == 0 else ['Y', 'X']}


def _cf_item(form, orders, delay, cost, invest, start=0):
    r = M.cashflow(orders, delay, cost, invest, start)
    return {'form': form, 'kc': 'liquidity/financing-need', 'prompt': f'Aufträge {orders}, Zahlungsziel {delay}, Kosten {cost}, Investitionen {invest}, Anfangsbestand {start}. Finanzierungsbedarf?',
            'expected': r['financing_need'], 'lure_end_balance': -r['final_balance'], 'transfer': False}


def _bp_item(form, x, t, act):
    p = M.mlp_init(seed=11 if form == 'X' else 13)
    g = M.mlp_backward(p, x, t, act, 'sigmoid')['grad']['W1'][0][0]
    return {'form': form, 'kc': 'ml/backpropagation', 'prompt': f'2-2-1-Netz, Parameter {p}, x = {x}, t = {t}, verdeckt {act}: ∂L/∂w₁₁?', 'expected': g, 'transfer': act != 'sigmoid'}


def forms():
    """Two parallel forms X and Y. Item difficulty equivalence is a design intention and must be checked in a pilot."""
    X = [_cf_item('X', [0, 80, 120, 150, 170, 190], 3, [90, 100, 110, 110, 120, 120], [150, 200]),
         _cf_item('X', [0, 60, 90, 120], 1, [50, 60, 60, 70], [100], start=50),
         _bp_item('X', [0.4, -0.6], 0.9, 'sigmoid'), _bp_item('X', [1.0, 0.3], 0.1, 'tanh')]
    Y = [_cf_item('Y', [0, 90, 110, 160, 160, 200], 3, [100, 95, 115, 105, 125, 115], [140, 210]),
         _cf_item('Y', [0, 70, 80, 130], 1, [55, 55, 65, 65], [90], start=60),
         _bp_item('Y', [-0.5, 0.7], 0.2, 'sigmoid'), _bp_item('Y', [0.8, -0.4], 0.7, 'tanh')]
    return {'X': X, 'Y': Y}


PLAN = {
    'design': 'randomised 2-group comparison (A static sequence, B adaptive track), pretest, immediate posttest, delayed posttest 7-14 days',
    'measures': ['pretest score (prior knowledge, covariate)', 'immediate posttest without help', 'delayed posttest without help',
                 'transfer items (structurally different)', 'time on task (event timestamps)', 'help dependence (hints, solutions per item)',
                 'error categories (engine diagnosis)', 'mental effort: 9-point single item (Paas 1992) after each phase'],
    'controls': ['parallel forms X/Y counterbalanced', 'same content and time budget in A and B', 'pseudonymous codes only', 'pre-registered hypotheses and analysis'],
    'analysis': 'ANCOVA (posttest ~ condition + pretest); report effect sizes with CIs; delayed test separately; no claims from a pilot with n < 30 per group',
    'status': 'NOT_RUN',
}
