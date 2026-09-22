# Hitter gradient challenger data readiness

Status: **complete; frozen joined feature table materialized and first challenger scored**

## Plain-language conclusion

The affiliated hitter challenger has the data it needs. We have exact contact type
and result, batter and pitcher identity, handedness, park, opponent, date, league,
level, age, workload, level changes, the contact-only comparison forecast, and the
following season's actual results.

The sources were materialized into one frozen table that enforces the chronology
and fallback rules below. The first fixed gradient-tree challenger has also been
scored against the contact-only model; see `hitter-gradient-challenger-v1-result.md`.

## Observed coverage

| Source season | Terminal contacts | Players | Pitchers | Parks | Strict opponent row | Exact identity/hand/outcome | Venue |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 421,085 | 4,060 | 4,580 | 144 | 96.11% | 95.89% | 99.85% |
| 2022 | 479,104 | 3,800 | 4,743 | 144 | 96.33% | 96.08% | 99.90% |
| 2023 | 475,461 | 3,756 | 4,721 | 149 | 96.14% | 95.91% | 99.84% |
| 2024 | 475,675 | 3,517 | 4,509 | 194 | 95.34% | 95.34% | 99.54% |

This supplies **1,851,325** exact terminal contact-and-result rows. The approximately
four to five percent without a stricter reconciled opponent row are not guessed or
discarded. They receive the exact contact-only fallback. The venue loss is below one
percent in every season and also falls back explicitly.

Age coverage is complete for the 2021-2025 player feature surfaces. The frozen
benchmark has **9,157** next-season player comparisons:

| Forecast origin | Players | Source contacts | Following-season contacts |
|---|---:|---:|---:|
| 2021 | 2,358 | 330,385 | 391,088 |
| 2022 | 2,269 | 366,054 | 378,509 |
| 2023 | 2,290 | 368,810 | 389,909 |
| 2024 | 2,240 | 373,395 | 386,349 |

The target table retains both source and following-season level, so promotion,
demotion, and same-level players can be scored separately without using future level
as a predictor.

## Contact-type and outcome support

All 90 combinations of the ten contact bins and nine terminal contact outcomes are
represented in the contract. Sixty-eight have at least 100 events in both 2021 and
2022. The remaining 22 are structurally rare combinations such as ground-ball home
runs, line-drive fielder's choices, and infield-fly triples.

Sparse combinations must be pooled toward their contact-type, outcome, and level
parents. They must not be dropped, selected individually after viewing results, or
encoded as observed zero talent.

## Inputs approved for the first challenger

- Raw and regressed overall outcome history.
- Ten contact-type shares and contact-type by result probabilities.
- Batter side, pitcher hand, and strictly prior pitcher component strength.
- Strictly prior park component effects and their reliability.
- Age, age relative to level, workload, source level, and prior level path.
- The current contact-only projection as the mandatory comparison and residual base.

Weather, Statcast contact quality, lineup position, inning/score state, and an assumed
future destination park are not required. The first model should project neutral
player skill; destination-park scoring remains a separate downstream step.

## Completed build

1. Materialized one event table that joins the contact/result rows to game venue,
   opponent context, handedness, and a park factor vintage fitted only through that
   source season.
2. Built batter and pitcher summaries using only events at or before each forecast
   origin. No target-season aggregate may enter a predictor.
3. Aggregated raw and context features side by side, with sample counts
   and reliability retained.
4. Froze a fold manifest for 2021-to-2022 through 2024-to-2025 and proved every
   feature date precedes its target season.
5. Recorded source paths and hashes so the scattered local artifacts can be
   reproduced or consolidated without silently changing the experiment.

The resulting table has 9,157 modeling rows and 208 columns. It matches every row
of the existing benchmark. No 2026 outcome is present.

No 2026 outcomes were read by this audit.
