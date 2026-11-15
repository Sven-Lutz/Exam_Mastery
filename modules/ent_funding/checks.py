"""Unabhängige Prüfung der Entrepreneurship-Beispiele: exakte Brüche, eigene Herleitung (nicht der JS-Kern)."""
from fractions import Fraction as Fr

BASE = dict(founders=[600000, 400000], pool0=0, safe=500000, cap=5000000, disc=Fr(1, 5), pre=8000000, inv=2000000, pool=Fr(1, 10), pre2=24000000, inv2=6000000)


def captable(s):
    """Löst das Gleichungssystem direkt: Unbekannte x (SAFE-Aktien), P (neue Pool-Aktien), D (Aktien vor Seed-Geld)."""
    S0 = Fr(sum(s['founders']) + s['pool0']); A, C, d, V, I, p = (Fr(s[k]) for k in ('safe', 'cap', 'disc', 'pre', 'inv', 'pool'))
    xc = S0 * A / (C - A)
    assert xc / (S0 + xc) == A / C, 'Post-Money-SAFE: Anteil = Betrag / Cap'

    def solve(x_of_D):
        # D = S0 + x + P,  (pool0 + P) = p * D * (1 + I/V)  ->  D = S0 + x(D) + p*D*(1+I/V) - pool0 ; x linear in D
        a, b = x_of_D  # x = a + b*D
        D = (S0 + a - s['pool0']) / (1 - b - p * (1 + I / V))
        return D, a + b * D
    Dc, x_cap = solve((xc, Fr(0)))
    Dd, x_disc = solve((Fr(0), A / ((1 - d) * V)))
    D, x, regime = (Dd, x_disc, 'discount') if x_disc > x_cap else (Dc, x_cap, 'cap')
    price = V / D; P = D - S0 - x; nI = I / price; T = D + nI
    assert (s['pool0'] + P) / T == p, 'Pool-Ziel exakt'
    assert nI / T == I / (V + I), 'Investoranteil = I/(V+I)'
    price2 = Fr(s['pre2']) / T; n2 = Fr(s['inv2']) / price2; T2 = T + n2
    F = sum(s['founders'])
    return dict(regime=regime, x=x, x_cap=x_cap, P=P, price=price, nI=nI, T=T, price2=price2, n2=n2, T2=T2,
                founder_share_seed=F / T, founder_share_A=F / T2, founder_value_seed=F * price, founder_value_A=F * price2,
                safe_share_seed=x / T)


def rounds():
    """X1: SAFE + Seed + Serie A; Up-Round erhöht den Gründerwert trotz Verwässerung; Down-Round senkt ihn; Cap/Rabatt-Wechsel."""
    r = captable(BASE)
    assert r['regime'] == 'cap'
    assert r['founder_share_seed'] == Fr(63, 100) and r['price'] == Fr(63, 10) and r['price2'] == Fr(378, 25) and r['founder_share_A'] == Fr(63, 125)  # 0,63 · 24/30 = 0,504
    assert r['founder_value_A'] > r['founder_value_seed'], 'Up-Round: Anteil sinkt, Wert steigt'
    down = captable(dict(BASE, pre2=6000000))
    assert down['founder_value_A'] < r['founder_value_seed'], 'Down-Round: Wertverlust'
    low = captable(dict(BASE, pre=5000000))
    assert low['regime'] == 'discount', 'niedrige Seed-Bewertung -> Rabatt greift'
    hi_cap = captable(dict(BASE, cap=6000000))
    assert hi_cap['x'] <= r['x'], 'höherer Cap gibt nie mehr SAFE-Aktien'
    return {k: (f'{float(v):.6g}' if not isinstance(v, str) else v) for k, v in r.items()} | {'down_round_founder_value_A': f'{float(down["founder_value_A"]):.6g}', 'discount_case_regime': low['regime']}


def fund():
    """X2: 100 Mio. €-Fonds, 25 Beteiligungen, 15 % Anteil bei Exit, 20 % Carry."""
    size, own, carry = Fr(100_000_000), Fr(15, 100), Fr(1, 5)
    need = size / own
    assert round(float(need)) == 666666667
    def net(gross): return gross - carry * max(Fr(0), gross - size)
    solid = own * 25 * 40_000_000
    assert solid == 150_000_000 and net(solid) / size == Fr(7, 5)
    gross3 = (3 * size - carry * size) / (1 - carry)          # net(gross) = 3*size
    assert gross3 == 350_000_000 and net(gross3) == 3 * size
    winner = gross3 / own
    assert round(float(winner) / 1e9, 2) == 2.33
    return {'single_exit_returns_fund': float(need), 'solid_portfolio_multiple': float(net(solid) / size), 'exit_for_3x_net': float(winner)}


def tasks():
    """Zahlen in EN1–EN3."""
    r = captable(BASE)
    assert round(float(r['x']), 1) == 111111.1 and round(float(r['T'] - r['nI']), 1) == 1269841.3 and round(float(r['P']), 1) == 158730.2 and round(float(r['nI']), 1) == 317460.3
    low = captable(dict(BASE, pre=5000000))
    assert low['regime'] == 'discount'
    S0 = Fr(1000000); cap_price = Fr(5000000) / (S0 + S0 * Fr(500000) / Fr(4500000))
    assert cap_price == Fr(9, 2)
    size, own, c = Fr(150_000_000), Fr(12, 100), Fr(1, 5)
    assert size / own == 1_250_000_000
    B = (2 * size - c * size) / (1 - c)
    assert B == Fr(675_000_000, 2) and B / own == Fr(2_812_500_000)
    return {'EN1_D': float(r['T'] - r['nI']), 'EN2_regime': low['regime'], 'EN3_gross_for_2x': float(B)}


def portfolio_skew():
    """EN5: Median vs. Mittel (Kerr, Nanda & Rhodes-Kropf 2014: niedriger Median, hohe Varianz)."""
    import statistics
    mult = [0] * 14 + [1] * 4 + [5, 60]
    assert statistics.median(mult) == 0
    assert Fr(sum(mult), 20) == Fr(69, 20)
    assert round(60 / 69, 3) == 0.870
    assert Fr(sum(mult) - 60, 19) == Fr(9, 19)
    return {'median': 0, 'gross_multiple': 3.45, 'outlier_share': 0.870, 'without_outlier': 9 / 19}
