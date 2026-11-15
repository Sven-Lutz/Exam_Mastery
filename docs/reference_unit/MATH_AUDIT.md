# Mathematical audit: NLP reference unit v4 (2026-11-14)

This is the author's own audit; it does **not** replace the independent expert review. Machine checks are listed exactly as they were run.

| Claim (section) | Argument in the text | Independent check | Assumptions / limits stated | Source |
|---|---|---|---|---|
| Satz A: IO not injective, BIO injective on valid sequences (§2) | counterexample + decoding argument | `seqlab.spans` round trip; JS/Python parity on 150 random BIO pairs | validity = no `I-X` without a preceding B/I of type X | SLP3 §9.5.2 p. 239; slides PDF pp. 15–18 |
| Receptive field $L(w-1)+1$ (§3) | induction over $L$ | SymPy induction step | stride 1 | – |
| Satz 1: $h^{\rightarrow}_t=F_t(x_{1:t})$ (§4) | aligned induction | toy experiment ($h^{\rightarrow}_1$ equal in A and B); holds for any recurrence $f$ | $h_0$ independent of the input | SLP3 §14.4.2 Eq. 14.16 p. 313 |
| Satz 2: BiRNN depends on the whole sentence (§5) | reversal + union | toy backward state flips sign; counterexample $W'=0$ | "function of" ≠ actual sensitivity (stated) | SLP3 §14.4.2 pp. 313–314 |
| Latency / independent outputs (§5) | conditional statements | – | **standard** full-sentence BiRNN; **independent** per-token softmax (conditions in the text and cards) | slides PDF p. 83 |
| Parameter count (§5, W1, B1, A3, B-3) | matrix by matrix | SymPy expansion; verifier for 4 configurations; givens rule | Elman cell, no embedding matrix; LSTM ≈ 4× (stated) | – |
| Satz 3: $\operatorname{Var}(q^\top k)=d_k$ (§6) | aligned variance computation | Monte Carlo $d_k=64$: 63.77 (scaled 0.996) | independent components, mean 0, variance 1 (stated: learned projections do not satisfy this exactly) | Vaswani et al. 2017 §3.2.1 fn. 1 |
| Attention example AT1, scene (§6) | numbers | verifier (128 values incl. 0.2483/0.5035/0.7517) | $W=I$ | – |
| Multi-head parameters unchanged (§6, B-5) | count | verifier | **without** output matrix $W_O$ (stated; Transformer adds $d^2$) | slides PDF p. 58; SLP3 Eq. 7.35 p. 188 |
| Satz 4: permutation equivariance (§7) | aligned matrix argument | 50 random property tests (exact up to 1e-12); attention scene step 8 | no positional encoding; row-wise softmax | slides PDF pp. 60–62 |
| Sinusoid: $PE(i+\Delta)$ linear in $PE(i)$ (§7) | addition theorems | SymPy identity; 50 numeric cases | per frequency pair | Vaswani et al. 2017 §3.5 |
| RoPE: depends only on $n-m$ (§7) | rotation group | SymPy identity; 50 numeric cases | 2D pairs | slides PDF p. 69 (Su et al. 2024) |
| Residual gradient $\prod(I+J_l)$ (§8) | chain rule | scalar example $1.1^{10}\approx2.5937$ (verifier) | illustration, not a bound for matrix products | SLP3 §7.2 pp. 184–187 |
| CRF score / Viterbi (§9, C1, A9, B-9, case study) | definition | `seqlab.viterbi` (exhaustive path scores in the verifier); JS Viterbi in scene and case study | hard constraints give validity only (shown in the case study) | SLP3 §18.4.5–18.5 |
| CRF probability (9.2), forward algorithm, $Z\approx200{,}2664$, $p\approx0{,}4495$, $\log p=S-\log Z$ (§9, C2, C3, cards) | definition + recursion | full enumeration of all 27 paths = forward value (`_crf_z`); app scene compares with the reference (test) | hard BIO constraints; transitions 0 | SLP3 §18.4.5–18.5 |
| Sinusoid shift as rotation, worked example (§7) | matrix–vector product | verifier recomputes sin/cos(1), sin/cos(2) and the product | $\omega=1$, $\Delta=1$ | – |
| Label bias vs. exposure bias (§9) | prose | **not machine-checkable** | – | Lafferty et al. 2001; Andor et al. 2016 abstract p. 2442 |
| Greedy decoding comparable to Viterbi (§9) | literature claim | page read | their system only | Ratinov & Roth 2009 p. 148 |
| $F_1$ as harmonic mean of effort; Satz 5 (count form incl. $TP=0$) (§10) | aligned derivations, case table (i)–(v) | SymPy; 2,000 random cases; JS definedness per case | – | SLP3 §4.9 Eq. 4.42–4.44 p. 114 |
| Satz 6: bounds of $F_1$ (§10) | equivalence chains | SymPy factorisations; 2,000 random cases | $P,R\in(0,1]$ | – |
| Phrase/token counting (§11, scene) | explicit lists | verifier; JS/Python parity | conlleval convention | slides PDF pp. 21–22 (values match) |
| Micro-$F_1$ = $D_k$-weighted mean of type $F_1$ (§12, B6, B-18) | aligned identity | SymPy identity; 200 random exact cases | $D_k>0$; types with $D_k=0$ drop out | – (own derivation; SLP3 §4.9.1 for micro/macro) |
| Satz 7: micro-$F_1$ = accuracy (§12) | aligned proof | 300 random sequences | one label per token, O pooled | – |
| Case study numbers (§13, F1) | panel | verifier recomputes greedy/Viterbi decoding and taxonomy | synthetic emissions | – |

**Every decimal** in the text, the solutions and the cards is recomputed or declared as an input (`GIVEN_DECIMALS`); a changed digit fails the build.
**Not machine-checkable:** prose explanations, the didactic adequacy of examples, and literature interpretations beyond the quoted passages.
