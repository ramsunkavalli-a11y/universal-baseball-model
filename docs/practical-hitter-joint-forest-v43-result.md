# Paired playing time and batting value test

2026-10-03. The paired forest does not improve the working expected-value
forecast. Keep the current forecast, and retain the new distribution machinery
as qualified research. All sixteen player reviews are complete. The practical
hitter goal is still incomplete; this is not a finished full-WAR model.

## What was tested

The candidate uses the same 199 count, age, listed-position and draft inputs,
the same 30,506 historical forecasts and 35 chronological whole-player-held-out
folds as the source-repaired control. It learns paired following-year MLB PA
and batting-plus-replacement wins from weighted historical outcomes. Those
same outcome weights supply participation probabilities and ranges. There is
no new injury diagnosis, foreign batting source, depth chart or contact input.
The [contract](practical-hitter-joint-forest-v43-contract.md) was saved before
fitting. This is an ordinary Extra Trees empirical outcome distribution, not
an implementation of specialized distribution-sensitive forest splitting.

The separately fitted control batting rate is weighted by actual future PA.
It is therefore wrong to assume it must fail because it multiplies independent
unweighted means. Under compatible populations and weights, that rate targets
expected PA-weighted production. Its finite model remains approximate, but
the joint architecture is not algebraically guaranteed to beat it. See the
[rate weighting explanation](practical-hitter-rate-weighting-and-risk.md).

## Expected forecasts get worse

Scores weight target years equally. Public comparisons use the unchanged
1,789 matched current-MLB forecasts and retain the snapshot/environment
qualifications. Batting-plus-replacement contribution is not full WAR.

| Measure | Working model | Source-repaired control | Joint forest | Steamer |
|---|---:|---:|---:|---:|
| All-player PA RMSE | 61.619 | 61.652 | 62.262 | Not matched |
| All-player contribution RMSE | 0.44121 | 0.44060 | 0.45175 | Not matched |
| Public matched PA RMSE | 143.965 | 144.487 | 145.276 | 135.019 |
| Public matched PA MAE | 110.563 | 111.577 | 113.151 | 92.399 |
| Public matched contribution RMSE | 1.01787 | 1.01638 | 1.03216 | 1.04348 |

The nominal player-clustered interval for the all-player joint-minus-control
contribution MSE difference is +0.00995, with 95% bounds +0.00646 to +0.01386:
the deterioration is not merely an insignificant pooled wiggle. PA MSE also
worsens by 75.62, with bounds 22.17 to 132.62. Public PA deterioration is less
certain; public contribution deterioration has positive nominal bounds. These
are development intervals, not independent certification after many experiments.

The median forecast has lower public PA MAE, 106.593, but worse RMSE, 149.266.
It still misses the declared MAE tolerance and cannot be relabeled expected PA:
the median and mean answer different questions. No post-result model blending,
output rescaling or threshold change is used to manufacture a pass.

## Reasonable league totals can hide bad allocation

Across the fixed cohort, predicted PA rises from 1,240,495 to 1,250,196 toward
actual 1,270,493. But upper-minor allocation falls from 93,314 to 88,102 against
actual 102,951. Current-MLB PA improves in total while individual workload error
gets worse. Predicted contribution rises to 4,370 against actual 4,177, compared
with the control's 4,215. Contribution RMSE worsens in every testing origin.
The 2023-origin PA excess also grows. Better aggregate PA is not a sufficient win.

These totals refer to the fixed evaluated cohort. They are not a claim that
all worldwide players, future entrants or future club ownership are observed.

## The probability forecasts contain useful information but are not fully reliable

On public matches, participation Brier improves from a simple stage/debut
reference's 0.15374 to 0.09044; 400-PA Brier improves 0.20408 to 0.12235.
Negative-contribution and two-contribution-win event scores also improve.
This reference is deliberately coarse, not Steamer's uncertainty model or the
strongest possible fitted probability benchmark. No public risk superiority
is claimed. The candidate forecasts 307 two-win outcomes versus 300 observed
on the public sample, but a good total does not establish individual calibration.

Upper-minor participation is underpredicted: 774 expected versus 858 observed.
In the fixed 20–30% probability band, observed participation is 35.8%; in the
30–40% band it is 63.9%, albeit on only 61 forecasts. The model is not sufficiently
recognizing readiness within these groups. It forecasts only 42 upper-minor
400-PA outcomes against 62 observed. Lower-minor rare-event log loss worsens
despite tiny Brier gains. The limited-drafted cohort has just seven active
outcomes; thousands of accurate zeros cannot validate precise breakout odds.

The inclusive PA 10th–90th range covers 87.1% of public outcomes and 99.8% of
lower-minor outcomes. The latter mostly reflects a zero mass, not excellent
80% uncertainty calibration. Known regulars who miss entire seasons also fall
outside confident ranges. Retain these forecasts as a distinct research model;
do not attach its intervals to the working model's different mean forecasts.

## What the actual player reviews show

The [complete walkthrough](../model-evidence/practical-hitter-joint-forest-v43/player-walkthrough.md)
contains dated counts, actual inputs, saved control accounting, complete-weight
provenance and successful and unsuccessful future-outcome neighbors.

- Judge's first full-year opportunity moves 144 to 190 PA, closer to 678 actual,
  but both opportunity and his breakout contribution remain badly missed.
  Established Judge's PA improves while contribution falls 5.88 to 5.22 against
  9.23 actual. Betts similarly gains workload accuracy but loses batting value.
- Volpe's 497 AA plus 99 AAA PA become just 66 expected MLB PA against 601;
  Alonso's 36 upper-minor HR become 71 against 693. The neighborhoods contain
  recognizable successful entrants, but their full weighting still understates
  readiness. These misses agree with the upper-minor cohort deficit.
- Kjerstad improves in both PA and contribution; Burger improves in PA but
  loses contribution accuracy. Gurriel is an ordinary genuine two-part success,
  while Rojas' nearly exact PA still misses his batting improvement.
- McLain's lower mean is less wrong against zero PA, but 98.5% participation
  shows the candidate did not foresee his absence. Hoskins and Gennett also
  expose poorly estimated collapse/absence tails. Later injury facts cannot be
  added to an earlier cutoff to rescue those predictions.
- Ortiz's 525 PA forecast after announced retirement is a missing dated
  availability/context problem, compounded by only two matching age-profile
  people in training. It is not a task for hitting regression alone.

## A roster source qualification discovered during the fixed test

The raw requested-October-2024 Dodgers full-roster response includes Hyeseong
Kim, although his dated signing is in January 2025. The request date does not
prove returned historical membership. His actual model row has no observed
affiliated batting, age, position or organization; both models predict zero PA
against his 170 in 2025. This is missing international/context evidence, not
a justified assertion of zero talent. See the [source qualification](practical-hitter-joint-v43-source-qualification.md).

An origin-only evidence bridge flags 218 of the 30,506 forecasts as roster-only
and unverified; it does not use future success to determine eligibility.
All remain in primary scoring, and a supported-population diagnostic is reported
alongside. The public matched sample is unchanged. Genuine new international
signees may lack these bridges; do not silently discard them or declare their
histories zero. The known source defect qualifies older broad-roster claims too.

## Decision and next useful work

All 35 saved mean/event artifacts replay, 105 representative quantile checks
reconstruct independent observation weights, and all sixteen case means replay.
Six focused unit tests pass; an unavailable pytest cache creates a warning, not
a model validation claim. Execution integrity is separate from predictive success.

Keep the working expected forecasts. Keep the empirical distribution code and
evidence, without claiming calibrated uncertainty at every level. Next audit
the existing dated retirement/return evidence and explicitly scope unverified
roster-only players before another forecast comparison. Do not spend this batch
tuning contact priors, draft-age cutoffs or algorithms. Protected 2026 outcomes,
the frozen forecast and deployed explorer remain untouched.
