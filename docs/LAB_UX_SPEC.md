# MDP Studio — interactive lab for finite MDPs (B32/B33)

`exam_mastery/labs/mdp_studio.py`; built by `labs/integrate.py` from a chapter's (or edition's) lab requests with
`model: mdp` (graph) or `mdp_grid` (grid). All MDP requests of a chapter become scenarios of **one** studio page.

## Learning path per scenario

Start (goal, how to work, glossary) → Model (graph/grid, editable rewards/probabilities with validation) →
Policy explorer (choose actions, see V^π, Q^π, improvement hint, Bellman backup of the marked state) →
Value iteration (single sweep / 10 / to tolerance, value table, residual and a-posteriori bound plot, backup) →
Policy iteration (evaluate vs. improve as separate steps, changed actions highlighted, stop criterion, tie rule) →
Discount γ (regime bar over γ, numeric threshold by bisection, exact value from the book if declared) →
Tasks (Predict → Explore → Explain → Check, with transfer question).

## Validation

Server side (`validate`): unique states, 0 ≤ γ < 1, probability rows sum to 1, no unknown successors, policy uses
available actions, grid ≤ 8×8, noise in [0,1). Client side: edits are checked again (row sums, reward range
[−20, 20]) and rejected with a message; reset restores the course model and keeps the current mode.
Golden values (`golden`) come from the exact oracle (`mdp_oracle`, rational arithmetic).

## Subject routing

Catalogue labs declare `subjects`; `catalog_requests` routes a lab out of a chapter whose recognised subject differs
(recorded in `publish_report.labs_routed_out`). Example: the analysis lab `folgen-epsilon` is never attached to an
RL chapter.

## Tests

Unit/contract: `tests/test_b32_quality_reset.py`. Browser E2E on the published page (robot, corridor, grid; wrong
prediction, invalid input, reset, threshold, keyboard, 390 px width): per release, results in the release package.
