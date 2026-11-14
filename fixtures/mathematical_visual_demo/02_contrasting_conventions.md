# Synthetic contrasting conventions and diagram requirements
This is development material, with no real-world authority.

## Statistical display
Synthetic dose-response-style values: input q in arbitrary units (a.u.) [1,2,3], synthetic means z in a.u. [2.0,3.0,3.5], illustrative symmetric half-widths [0.3,0.4,0.5]. These half-widths are supplied illustrative uncertainty, not estimated confidence intervals: no sample size or probabilistic coverage is given. Plot the three means with error bars and an explicit caption describing that limitation. Never call them 95% confidence intervals. A legend must say synthetic means. No causal effect follows from these three invented values.

## Other notation examples
Physics: E=1/2 m v^2 for a positive mass m (kg) and speed v (m/s), so E has dimension M L^2 T^-2 and unit joule. Finance: a nominal one-period accumulation F=P(1+i), principal P and final value F in EUR and dimensionless period rate i; no recommendation or price forecast. Chemistry: balanced stoichiometric notation 2 H2 + O2 -> 2 H2O, only a formal equation here, not a procedure or experimental claim. Use proper subscripts and upright species notation.

## Synthetic rule-based case, not real law
A fictional rule grants a refund exactly when delivery is late AND a notice is received within two days. In the synthetic case delivery is late but notice arrives on day three. Under this invented rule refund is not available. Distinguish facts, rule, application, conclusion. Show a decision/process scheme with explicit labeled conditions and a timeline (day 0 due, day 2 notice deadline, day 3 actual notice). Do not cite legislation or claim this is real legal advice. The purpose is to test that a rule-based solution has a different reading structure from a mathematical derivation.

## Algorithm and architecture convention
For a finite list of numbers a_1,...,a_n, running-sum algorithm: initialize s=0; for each index k=1,...,n set s<-s+a_k; return s. Loop invariant after k items: s equals their sum. Show initialization, update and result as an algorithm diagram with clear flow. A source-to-product architecture overview, when useful, must distinguish source evidence, canonical math/figure data and generated views; it is not evidence that an arbitrary external system was executed.
