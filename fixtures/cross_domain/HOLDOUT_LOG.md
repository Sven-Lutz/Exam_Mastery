# B35 holdout log

| Holdout | Mechanism | Evaluated | Result (before any change caused by it) | Consequence |
|---|---|---|---|---|
| `objectives_holdout.json` (24 objectives, 8+ disciplines; written before tuning, same author) | subject profiles | 2026-11-17, once | 24/24 lenient match; 2/24 with discipline-specific extra packs, 1 real false positive ("sensitivity analysis" -> clinical) | clinical signal fixed -> holdout CONSUMED |
| NLP reference unit deck (50 cards, never used in B35 development) | answerability gate + deck reader | 2026-11-17, once | reader crashed on the current Anki package format (zstd, schema 18, foreign note type); after reader fixes: 7 blocking, of which ~1-2 real (two targets), 5 false positives (leak rule on formula/tag answers, imperative task cards), ~30 symbol warnings with parser noise (\mapsto, \partial, \top) | leak rule, imperative prompts, symbol parser fixed -> holdout CONSUMED; after fixes 1 blocking (two targets, arguable) |

Rule: a mechanism changed because of a holdout result needs a NEW, independently written holdout before any further generality claim.
Calibration sets (tuned on, no generality evidence): RL V4 deck, Analysis 1 / Entrepreneurship / Patentrecht decks, reviewer corpus of 42 objectives.
