# B35 – Root-cause matrix for V4 (owner rating ≤ 2.5/5, not released)

Baseline: commit `bed6619`, engine `0.23.0rc1`, package `RL_Kap03_OptimalDecisionMaking_v4_2026-11-17` (unchanged).
The independent V4 audit file was not present locally; its two P1 findings were reproduced from the V4 artifacts.

| # | Sev | Defect (observed) | Reproduction | Root cause (mechanism, not symptom) | Why old gates missed it | Fix / status |
|---|-----|-------------------|--------------|-------------------------------------|-------------------------|--------------|
| 1 | P1 | Proof line clipped at right margin, textbook PDF p. 49 (Satz 3.6, step 3) | `pdftoppm -f 49` on V4 PDF | `.drv .eq{overflow-x:auto}` = invisible scroll area in print; display formula wider than text block | Layout lint only measured **inline** math and compared display math against the viewport, not against its clipping container | **Fixed** (98cdaa6): scale to block width, FAIL below 0.72, every clipped scroll container FAILs the gate. Negative test from the real V4 formula fails on old code |
| 2 | P1 | MDP studio "fair" VI/PI cost comparison was misleading | Studio → "VI vs. PI" | Estimated `n³/3+n²` Gauss cost mixed with counted transitions; VI stopped with oracle V* at 1e-6, PI exactly; text asserted fairness | Test only checked that the words "Rechenoperationen" and an element id existed | **Fixed** (98cdaa6): instrumented counts (verified against independent Python count), practical stopping rules, separate iterations/ops/accuracy/runtime, declared cost model, data-derived verdict |
| 3 | P2 | Anki cards unanswerable/ambiguous (owner 3/5) | `answerability.audit_deck(views_from_apkg(V4))` | Card rules checked **form** (≤30 words, one "?") not what the question side lets a learner answer; grid/robot cards depend on models shown only in the textbook | No rule looked at hidden context, missing quantities, figure location, undefined symbols | **Gate implemented** (B35): 7 blocking V4 cards (e.g. `vi/gitter-backup` lacks γ and noise), 33 WARN (undefined symbols, convention-dependent counts); wired into publish path. Card rewrite pending |
| 4 | P2 | Derivations compact chains, not explanations | Read textbook ch. Bellman/contraction | Derivation block schema = (equation, short why); no representation of rule used, assumption used, dependency on earlier steps | Gate counted steps and checked arithmetic only (`derivation_check` scope says so explicitly) | **Open** – argument-graph schema + proof audit (next) |
| 5 | P2 | Literature claims backed by metadata/abstract only | V4 research notes | Source levels A/B/C describe the *source*, not the *access* to the supporting passage | No claim-level record of what was actually read | **Open** – evidence registry with access levels |
| 6 | P2 | Labs lack task/feedback architecture (owner 2/5) | Studio tasks tab | Lab = set of views; tasks are attached, not the organising unit; feedback mostly right/wrong | Lab tests verify numbers and buttons | Partly (comparison view now prediction → data-derived explanation); task model **open** |
| 7 | P2 | 60-min exam calibration not independent | Exam headers | Times are model estimates | No recorded solve attempts | **Open** |
| 8 | P2 | Cross-domain quality not demonstrated | – | Development on RL only | – | **Open** |

Principle applied to every fix: a new check counts only if it **fails on a known V4 defect** (negative fixture) and
does not fire on known-good cases (positive fixture).
