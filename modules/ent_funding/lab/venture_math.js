/* Entrepreneurship – Rechenkern Finanzierungsrunden und Fondslogik (rein, ohne DOM).
 * Vereinfachtes, ausdrücklich dokumentiertes Modell (keine Rechtsberatung):
 *  - Post-Money-SAFE: unter dem Cap hält der SAFE den Anteil A/C an der Kapitalisierung vor der Preisrunde (YC-Leitfaden, S. 1);
 *    S0 = Gründer + bestehender Pool; Cap-Aktien x = S0·A/(C − A).
 *  - Rabatt: Umwandlungspreis (1 − d)·Rundenpreis. Es gilt die für den Investor günstigere Variante (mehr Aktien).
 *  - Preisrunde: Pre-Money V schließt umgewandelte SAFEs und die Pool-Aufstockung ein (Ziel-Pool p nach der Runde).
 *  - Zweite Runde ohne neuen Pool. Getestet in tests/test_modules.py (exakte Brüche in Python).
 */
(function (root) {
  'use strict';
  function round1(s) {
    const S0 = s.founders.reduce((a, b) => a + b, 0) + s.pool0, A = s.safe, C = s.cap, d = s.disc, V = s.pre, I = s.inv, p = s.pool;
    const k = 1 - p * (1 + I / V);
    if (!(k > 0)) return {error: 'Pool-Ziel zu groß für diese Runde'};
    // Variante Cap
    const xc = A > 0 ? S0 * A / (C - A) : 0;
    const Dc = (S0 + xc - s.pool0) / k;
    const priceC = V / Dc;
    let regime = 'cap', x = xc, D = Dc;
    if (A > 0) {  // auch ohne Rabatt (d = 0): Umwandlung höchstens zum Rundenpreis
      const kd = k - A / ((1 - d) * V);
      if (kd > 0) {
        const Dd = (S0 - s.pool0) / kd, xd = A * Dd / ((1 - d) * V);
        if (xd > xc) { regime = 'discount'; x = xd; D = Dd; }
      }
    }
    if (A > 0 && !(C > A)) return {error: 'Cap muss größer als der SAFE-Betrag sein'};
    const price = V / D, P = D - S0 - x, nI = I / price, T = D + nI;
    return {S0, x, xCap: xc, regime, D, P, price, priceCap: priceC, nI, T, safePrice: A > 0 ? A / x : null};
  }
  function simulate(s) {
    const r1 = round1(s);
    if (r1.error) return r1;
    const F = s.founders, n = F.length;
    const st0 = {label: 'Gründung', holders: [...F.map((v, i) => ['Gründer ' + (i + 1), v]), ['Pool', s.pool0]], price: null};
    const st1 = {label: 'nach SAFE (wie umgewandelt, vor Runde)', holders: [...st0.holders, ['SAFE', r1.xCap]], price: s.safe > 0 ? s.cap / (r1.S0 + r1.xCap) : null};
    const st2 = {label: 'nach Seed-Runde', holders: [...F.map((v, i) => ['Gründer ' + (i + 1), v]), ['Pool', s.pool0 + r1.P], ['SAFE', r1.x], ['Seed-Investor', r1.nI]], price: r1.price};
    const price2 = s.pre2 / r1.T, n2 = s.inv2 / price2;
    const st3 = {label: 'nach Serie A', holders: [...st2.holders, ['Serie-A-Investor', n2]], price: price2};
    const stages = [st0, st1, st2, st3].map(st => { const tot = st.holders.reduce((a, h) => a + h[1], 0); return {...st, total: tot, share: st.holders.map(h => [h[0], h[1] / tot])}; });
    const founderSh = F.reduce((a, b) => a + b, 0);
    const fval = stages.map(st => st.price ? founderSh * st.price : null);
    return {r1, stages, price2, n2, founderShare: stages.map(st => founderSh / st.total), founderValue: fval};
  }
  /** Fondslogik: gleiche Tickets, o = Anteil bei Exit, k Gewinner mit Exitwert Ew, Rest Er; 20 % Carry über eingezahltem Kapital. */
  function fund(f) {
    const fees = f.size * f.fee * f.years, investable = f.size - fees;
    const gross = f.own * (f.k * f.ew + (f.n - f.k) * f.er);
    const carry = f.carry * Math.max(0, gross - f.size), net = gross - carry;
    return {fees, investable, gross, carry, net, tvpi: net / f.size, needWinner: f.size / f.own, share: f.k ? f.own * f.k * f.ew / gross : 0};
  }
  const API = {round1, simulate, fund};
  if (typeof module !== 'undefined' && module.exports) module.exports = API; else root.VentureMath = API;
})(typeof window !== 'undefined' ? window : globalThis);
