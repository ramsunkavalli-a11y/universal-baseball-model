# Test repaired injury observations against next year MLB playing time

2026-10-05. Fixed development comparison, written before fitting.

Question: do repaired medical-observation inputs improve next-year MLB PA and
delivered batting-plus-replacement value beyond the stronger existing forecast?
The target is actual future MLB contribution, not injury days or clinical recovery.
Keep batting-rate forecasts and origin replacement conversion fixed. This is one
calendar year, not full WAR, six years of control or trade value. No 2026 results.

## Population and comparison

Retain all 30,519 existing historical forecasts: the original 30,506 plus thirteen
previously declared cases. Origins are 2016, 2017, 2018, 2021–2024; target seasons
are 2017, 2018, 2019, 2022–2025. Use the unchanged existing thirty-five held-player
chronological cells, training only on the original training row IDs with outcomes
through the origin year. The canceled 2020 target remains excluded. MLB exposure
normalization in the original source stays fixed; do not invent MiLB PA in 2020.

Medical eligibility is known at origin: prior MLB debut, at least one of the
three recent MLB seasons with normalized workload at least 300 PA, and both
recent annual transaction-source years present. It does not depend on a future
return. Include unsigned/released players and future exits. Known hard exclusion,
retirement, unresolved nonmedical restriction and finite nonmedical suspension
remain outside this adjustment and retain the stronger anchor. Minor-league-only
players retain the anchor, not a fabricated healthy history.

Arm A is a matched refit using the existing 293 playing-time predictors, including
the old six medical/capture predictors. Arm B uses the same nonmedical predictors
but replaces those six with nine repaired observation inputs: six separate source
states and the captured episode, placement-report and surgery-report counts.
No calendar observation bound becomes an injury-day or missed-games input. No
reported activation is recoded as observed play; no captured entry is not health.
Same eligible training/test rows, labels, weights and estimator settings in both
arms: histogram boosting, 250 iterations, depth 3, minimum leaf 30, learning rate
0.05, L2 10, no early stopping, seed 31. No search, blend or coefficient tuning.

This is a changed medical representation, not a causal effect of shortening a
particular span. Compare B with A to isolate representation within the refit;
compare both with the stronger frozen historical anchor to detect degradation
from narrowing the training population. A win over a weak matched refit alone
is not improvement of the project model. Do not repeat the rejected role-only
linear reference or its six-feature-removal test.

## Support and fallback before scores

Training uses only covered, medically eligible rows in each original cell. Before
fitting either arm, verify source/previous completion hashes, exact row identity,
label pairing, January cutoffs, held-player separation and outcome maturity using
`forecast_validation.preflight` plus the medical-source checks. No baseline
forecast is used as a training feature, avoiding second-stage contamination from
historical predictions whose training may include a current held player.

A cell requires at least 200 training rows and 100 distinct people in each head,
and both participation classes. Otherwise neither arm is fitted. In particular,
origin 2016 has no fully covered medical training history and stays unchanged.

Count distinct people separately in the actual participation and active-PA heads
by source state, age (through 25, 26–32, 33+), current MLB participation (zero or
positive), best recent MLB workload (300–399 or 400+), and last known MLB batting
quality (below −1, −1 through 1, above 1 in existing source units). These are broad
support diagnostics, not matched medical prognosis. A forecast is applied only
when both heads have at least twenty people in that joint profile and age,
recent workload, last batting quality and repaired counts stay within the relevant
training ranges. Twenty is a conservative sparse-data screen, not certification.
Same gate for A and B, selected without test outcomes. Unsupported players remain
in every overall score with exact anchor p, conditional PA, PA and value.

Persist raw diagnostic predictions for eligible but unsupported players separately
from applied forecasts. Score those raw predictions as well so fallback cannot
hide poor extrapolation. Counts with incomplete coverage may be placeholder zero
in the joined frame but are never used for fitting or a new applied prediction.

## Scores and judgment

Primary: equal-origin mean squared next-year PA error across medically eligible
evaluation players, including fallback rows. Report its square-root and paired
differences using a 1,000-draw player-cluster bootstrap preserving origins. Also
report full-population scores, applied rows, raw eligible forecasts, active-only
conditional PA error, MAE, participation Brier/log loss and delivered batting-plus-
replacement RMSE. Preserve non-arrivals in unconditional PA/value scores.

Report each origin (especially 2021), current/gap and source-state groups, existing
stages, matched predicted/actual PA and value totals. A development improvement
requires lower primary PA error versus the stronger anchor with a negative paired
95% MSE interval; no worse delivered-value error, participation Brier/log loss or
absolute aggregate PA bias; and no origin PA RMSE deterioration above 2%.
Still require baseball review and separate deployment approval. This criterion
is deliberately not automatic certification from one pooled metric.

Before fitting, fix Travis 2016, Tatis 2022, Hoskins 2023, Ellsbury 2018, Alvarez
2022, Franco 2017, Judge 2024 and Canha 2016, with verified IDs/names. Add largest
PA improvement, deterioration, false high and false low among eligible forecasts;
ordinary applied case nearest its actual outcome; and one origin-2024 lower-minor
case selected by smallest row ID without outcome selection. Include at least
three same-origin peers selected by age, best recent MLB workload, current/gap
and prior quality, not future success. Show actual prior stats, source joins,
support/fallback, both p/conditional PA heads, unchanged batting rate, delivered
value and reality. Reconstruct saved fits and use fixed-model input swaps only
as labeled explanations, never substitute forecasts or causal injury effects.

If the candidate fails, preserve the result and identify whether the source,
support, modeling or baseball interpretation failed. Do not tune to the reviewed
players or declare injury information useless. No clinical probability, additional
suspension deduction, explorer change or protected-2026 rescore is authorized.
