# V42: consistent draft-age evidence, not hindsight breakout targeting

2026-10-03. Contract before fitting. This closes one identifiable representation
gap in the practical hitter program. It is not a college-data collection or a new
algorithm tournament. V41's completed player review remains the previous checkpoint.

## Question and fair comparison

Does consistently available approximate age at draft work better than four school
class flags whose coverage changes sharply across draft years? The targets remain
next calendar year's expected MLB PA, conditional MLB batting wins above average
per 600 PA, and batting-plus-replacement contribution. These are not current
MLB-equivalent prospect grades, full WAR, six years of control or trade value.

Use the exact V34 source-corrected 30,506 evaluation rows, 35 chronological,
whole-player-held-out folds and training row IDs. Preserve zero future MLB PA,
exits, unknown ages, incomplete history flags and the 2020 cohort repair. Only
mature target years at or before each cutoff train; target 2020 stays excluded.
No protected 2026 source or outcomes. Retain V33b and historical public forecasts
as matched anchors. Public snapshot timing/environment limits are unchanged.

Replace `draft_hs`, `draft_jc`, `draft_college`, `draft_class_unknown` with three
inputs: known approximate draft age, (draft age minus 21)/5 when known, and that
scaled age times the existing draft-rank/low-professional-exposure feature.
Approximate draft age = known origin season age minus years since the latest
cutoff-eligible draft. Never infer it from the default age of 27. Unknown values
have zero centered input and a false known flag. Do not relabel age as actual
school type. Keep draft pick/rank, elapsed time, the original low-exposure rank
input, all level-specific counts and all other context unchanged. No new prior,
selection, training weight, age cutoff, sample threshold or favorable-player rule.

Fit the same fixed histogram PA head and scaled ridge batting head (alpha 100),
with V34's equal-origin weights and future-active PA weighting for batting.
Scaling of original features remains identical. The added inputs already have
their physical scale; no full-dataset normalization. Value multiplies these two
means, an acknowledged approximation. Also score isolated PA and batting changes
using the other control head to show which part drives a combined difference.
These mechanical contrasts are not new fitted contenders or joint distributions.

## Source/support review before fit

Save draft-year class availability, approximate-age range and within-player drift,
the exact formula/source hashes, and fixed source walks. Inspect Kurtz (2024),
Kjerstad (2023), Burger (2021), Volpe (2022), Judge (2016/2024) and a same-year
low-pro-exposure draft peer set, including subsequent non-arrivals. These examples
are diagnostics, not rules. Audit distinct training players and future-active
training players by draft-known/age-known, age band, recent exposure and debut
status in each actual fold; retain sparse/absent profiles in headline evaluation.
Check age plausibility without clipping or inventing classes. Most early college
draftees with small first-year pro samples do not appear in MLB next calendar
year; a large realized breakout miss is not by itself proof a low mean was wrong.

## Scoring, walkthrough and decision

Report identical-cohort PA RMSE/MAE, conditional batting RMSE and delivered-value
RMSE, paired player-cluster development intervals, public matches, origin/stage
totals, limited-exposure drafted entrants, brief debuts and inactive returns.
The controlling plan's public tolerance (PA RMSE within 10%, MAE within 15%) stays
unchanged. No victory from a tiny subgroup, favorable totals, a known star or
source integrity alone. A model-wide gain must not hide meaningful public or
baseball harms. Uncertainty is nominal development evidence after many tests.

Review the fixed cases plus largest combined gains/harms, false highs/lows and an
ordinary case through official dated counts, exact added inputs, saved PA tree
paths, saved ridge coefficient accounting, arithmetic and actual outcomes.
Origin-selected peers use only age, level exposure and pedigree before outcomes
are displayed. No next experiment/disposition until those walks are completed.
Reject/retain/promote the representation only at that checkpoint; deployment and
the frozen 2026 forecast still require separate authorization.
