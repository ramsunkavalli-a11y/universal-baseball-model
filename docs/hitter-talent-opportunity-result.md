# Completed comparison of hitting estimates and playing time

2026-10-03. Keep the existing hitter research candidate. Supplying its separately
generated hitting estimate to both opportunity models produces a very small,
uncertain gain, not a meaningful solution to prospect readiness or return
workload. Sixteen actual player reviews are complete. No forecast is promoted.

## The test and integrity checks

The [locked contract](hitter-talent-opportunity-contract.md) compares current,
known-indicator control and known-plus-hitting constructions. It retains exactly
30,506 forecasts for 11,020 people, seven origins, all exits and non-arrivals,
and the original 63,282 input rows. The target is next-calendar-year MLB PA and
fixed-yield delivered offense, not eventual prospect success or full WAR.
Only outcomes mature at each forecast date enter training; target 2020 is
excluded, while raw short-season history and canceled-minor missingness remain.
Coming-season ranking release dates still qualify the information cutoff.

All nested memberships preceded fitting. There are 155 rate contexts: 135 fitted
and twenty explicitly unestimated at early 2011/12 origins. Every tested player
has a generated rate that reproduces the existing hitting forecast. All 140
second-stage full/active checks preceded opportunity fitting. Independent
scoring replays 135 rate heads, 140 new opportunity heads and seventy current
heads. Every original forecast column is exact; hitting yield remains unchanged.
Integrity does not establish baseball or predictive merit.

The control's predictions equal the anchor exactly. Its extra known indicator
does not supply a forecast change. The talent arm's effect therefore cannot
be credited to the fallback/coverage flag. Three talent conditional predictions
are below one PA and use the existing clip; Shepherd, Navas and Turner all
have zero subsequent PA. No prediction exceeds 800. No difficult row is removed.

## Matched scores and uncertainty

Lower is better; losses give each represented target year equal weight.
Value units are custom common-origin fixed-event batting plus replacement,
not provider-native WAR. Current and coverage scores are identical.

| Population | Current PA RMSE | Talent PA RMSE | Current PA MAE | Talent PA MAE |
| --- | ---: | ---: | ---: | ---: |
| All 30,506 forecasts | 60.4991 | 60.4295 | 20.6124 | 20.5734 |
| Public 2,627 matches | 138.3298 | 138.0067 | 106.4108 | 106.1410 |
| Upper minors never debuted | 55.1267 | 55.1010 | 18.7321 | 18.7103 |
| Lower minors never debuted | 7.9664 | 7.9712 | .6217 | .6241 |
| Previously debuted but absent | 43.8443 | 43.8591 | 13.1387 | 13.0862 |
| Thin new draftees | 20.2905 | 20.2981 | 1.6197 | 1.6305 |

Overall PA RMSE improves about .115%; offense RMSE .453384 to .453114,
about .059%. The nominal paired player-clustered PA MSE difference is -8.412
with 95% interval [-18.285, +1.526]; offense MSE difference -.0002444,
interval [-.0006465, +.0001049]. Both allow harm. Public PA MSE is -89.295,
interval [-179.635, +2.751]; public offense interval also crosses zero.
Upper-minors PA MSE interval [-16.849, +11.638] does not establish improvement.
All seven principal scope intervals for both metrics cross zero. These are
nominal exposed-development intervals, not an independent test or protection
against repeated historical experimentation.

Overall appearance Brier/log loss worsen .0335405/.1147361 to
.0335504/.1147565. Public appearance scores improve slightly, but upper minors
worsen. Five of seven origins improve PA RMSE, while 2018 and 2024 worsen;
offense worsens in 2021, 2023 and 2024. A single aggregate number is insufficient.

On the identical public matches, Steamer PA RMSE/MAE remains 135.3795/92.0828.
Talent is about 1.94% worse on RMSE and 15.27% worse on MAE: within the
10% RMSE allowance, still outside the 15% MAE allowance. Small gains and
uncertain archive vintages do not waive that goal. ZiPS workload is not
invented from rate-only exports. Existing public hitting/offense conversion
and snapshot-date qualifications still apply.

## Totals and actual player findings

Expected all-population PA falls 1,228,733 to 1,227,006 against 1,270,493 actual.
Expected appearances 4,391.86 to 4,390.70 against 4,538. Upper-minors PA falls
74,239 to 74,005 against 92,891. Lower minors rises 7,055 to 7,099 against
5,194, so its overcount is not repaired. In the origin-2021 debut cohort,
expected PA rises 10,432 to 10,589 against 18,944, and appearances 77.63 to
77.77 against 158. The severe cohort miss remains; it cannot be explained
away as harmless shrinkage on individual players.

The [sixteen player walkthroughs](hitter-talent-opportunity-player-walkthrough.md)
trace dated level counts, actual 253 inputs, generated-rate coefficients and
membership, saved opportunity paths, probabilities, active workload, fixed
value yield and reality, with four outcome-blind peers each. Langford improves
215 to 221 PA before 557; Alonso 215 to 227 before 693; Peña 47 to 50 before
558. Kurtz worsens ten to nine before 489, McLain's return 132 to 126 before
577, and Tatis remains forty before 635. The largest gain, Cruz 475 to 444
before forty, is not an injury forecast. The largest harm, Encarnacion-Strand
445 to 485 before 123, follows a plausible stronger-hitting/workload mechanism
that loses in reality. Garcia gets PA almost exactly right but misses production.

The supplementary lower-level case exposes a substantive interpretation limit:
16-year-old Caceres's +.499 MLB hitting estimate is driven mostly by an age
polynomial, with no refined active/rate training analogue. All DSL-specific
terms contribute about +.032. Sensibly forecasting immediate non-arrival
does not validate that positive MLB ability estimate. Preserve the original
case-selection ID error and its Peña correction; models and scores were not
confused or changed. No older comparison is retroactively recertified.

## Decision and coherent next step

Do not retain this additional feature as an improved candidate. Preserve the
completed comparison as uncertain development evidence. This rejects neither
talent-to-opportunity dependence nor using richer historical performance.
The added rate is a compressed prediction from already available inputs,
not new baseball information, and may inherit the rate model's weaknesses.

Before another modeling fit, audit the underlying cross-level rate's target
support and representation: what its participant-trained age/level curves
actually identify, which older contact/talent winners have compatible future
MLB labels and provenance, and which displayed lower-level ability claims are
unsupported. This is the practical plan's talent milestone, not another tiny
context feature or library sweep. Any subsequent comparison must fix that
identified issue, preserve the full-history anchor and all non-arrivals, and
include the required player review. Known administrative/medical and rights
coverage limits remain explicit rather than erased by a batting feature.

The full hitter goal, public MAE gap, prospect readiness, conditional batting
uncertainty and complete player-value integration remain unresolved. Protected
2026, frozen forecasts and explorers are unchanged. No deployment is approved.

Evidence: [scores](../reports/model-evidence/hitter-talent-opportunity/scores.json),
[intervals](../reports/model-evidence/hitter-talent-opportunity/intervals.json),
[independent verification](../reports/model-evidence/hitter-talent-opportunity/verification.json),
[completed review](../reports/model-evidence/hitter-talent-opportunity/final-report.json).
