# Testing Statcast for next year MLB hitting

2026-10-04. Freeze this comparison before fitting. The source review is complete;
the question is whether launch measurements improve next-year MLB hitting beyond
the current production/history model. This is the first MLB-covered phase of the
integration plan. Minor tracking remains a separate source/calibration phase;
not having it does not prevent an explicitly MLB-only incremental comparison.

## Population and targets

Keep all 30,506 current historical evaluation forecasts, seven origins 2016–18
and 2021–24, and the same thirty-five chronological whole-player folds. Keep all
63,282 source rows. Train only on future-active MLB players with complete targets
at or before the evaluation origin, excluding target 2020 and the entire held
player group. Do not select evaluation players by future participation. Source
features use each row's own origin and previous two seasons, never test-origin
measurements for older training rows. Use actual 2020 MLB samples where they fall
inside the predictor history, and no invented canceled MiLB production.

The fitted response is future-season-relative custom MLB batting wins per 600 PA
among future participants. Evaluation also scores the existing common-origin
delivered batting contribution for everyone: unchanged current expected PA times
(candidate rate/600 plus origin replacement). Non-arrivals have zero delivered
contribution and no observed rate. This is not full WAR or six years of player value.

## Features and fixed comparisons

Keep the current 199 rate inputs and their existing deterministic scaling. Add
three separate season lags, not a chosen new recency weight. Each lag contains
mean EV, linearly interpolated EV95, hard-hit fraction, mean angle, angle standard
deviation, sweet-spot fraction and hard-air fraction. EV is centered at 90 or 105
mph and divided by 10; angles divided by 20; fractions retain their natural units.
Missing metrics are encoded as a centered neutral value plus explicit known flags,
not falsely observed average measurements. Counts use log(1+n)/log(601); counts
and known flags stay separate from quality. Preserve raw counts in the feature
artifact. Add only two predeclared sample interactions per lag: EV95 times its EV
sample feature, and hard-air fraction times the complete-pair sample feature.

The coverage controls contain per-lag EV, angle and complete-pair sample features,
pair coverage, source-year availability and seven metric-known indicators. The
measurement arms add the seven metrics and two sample interactions. The exact
column lists are persisted before any fit. No current xwOBA, speed/angle outcome
estimates, future-game intervals, bat tracking, player-name indicators or new
team-record features. These raw launch summaries are not separately park- or
opponent-neutralized. Existing production context remains identical in every arm.

Retain the exact current rate as anchor, then fit four heads per outer cell:

- Ridge coverage control and Ridge measurements, both alpha 100.
- Histogram gradient boosting coverage control and measurements, both 150
  iterations, depth 2, minimum leaf 30, learning rate .05, L2 20, no early stopping,
  squared-error loss and fixed seed 724.

Use the same full active training rows and current equal-origin times actual-PA
weights in all four heads, normalized to mean one. These fixed settings are a
bounded capacity choice, not a tournament or a claim of optimal tuning. No nested
tuning is performed because there are no data-selected settings. Save all heads,
input/weight/cutoff hashes, prediction receipts and control contrasts. For people
with no valid own-MLB EV in the three-year history, override every experimental
forecast to the exact current rate. Keep their PA, value, eligibility and losses.
Do not grant value merely for coverage. The measurement-vs-coverage contrast
isolates contact values; the measurement-vs-current contrast answers usefulness.
Preserve the already completed prospect alternative as external development
evidence, without refitting it or assigning its gain to Statcast.

## Support and decision rules

Before fitting all cells, run the established forecast integrity/profile checks
and count distinct tracked active people by stage, five-year age band and contact
sample band (under 50, 50–199, 200+). Record feature-range extrapolation and sparse
profiles; never remove them to improve the score. A support warning stays separate
from predictive success. Require exact identities, labels, chronology and fallback
before accepting any score. Missing prior source years are flagged, not invented.

Primary contact endpoint is PA-weighted rate MSE among tracked future participants,
giving each origin equal total weight. Also score equal-origin all-player delivered
contribution MSE. Compute paired player-cluster nominal 95% intervals with 2,000
resamples, fixed seed 724. There are two measurement candidates: their development
intervals are not multiple-testing-adjusted or independent confirmation.

For a useful development candidate require lower primary loss against BOTH its
coverage control and the current model, with a paired interval below zero against
current; rate MAE may not worsen more than 1%. All-player contribution MSE may
not worsen more than .5%. An origin's tracked rate MSE worsening more than 5%, or
an unexplained cohort/physical failure, blocks an unqualified adoption claim even
if pooled results improve. These practical tolerances are judgments declared now,
not natural statistical laws. Report 2021 separately, current MLB, tracked players
with minor exposure, all never-debut players, sample bands, older/younger source
eras and matched public forecasts; unchanged PA is not a playing-time improvement.

Keep actual observed totals, predicted totals, large gains and harms. An unexplained
change in untracked prospect forecasts is an implementation failure. New launch
values do not prove original historical preseason availability because provider
estimation/reprocessing vintage remains unknown. A positive result is qualified
development evidence, not a camera-only causal improvement or deployed forecast.

## Required player review and stop

Review the ten fixed source cases, including both Judge origins, Soto, Torkelson,
Belt, McLain, Kurtz, Caceres, Friedl and Siani. Add the biggest contribution gain
and harm, the largest false high/low and an ordinary low-error case, using stable
row-ID tie breaks. Retain four origin-only peers from the source manifest for fixed
cases; added cases select peers by stage, age, current MLB/minor PA and origin
quality without future outcomes. Save dated stats, all actual inputs, source
measurements, fitted terms or tree-path replay, predictions and observed outcomes.
Review high contact with poor future results as well as successful power hitters.
No final disposition or next modeling experiment before that walkthrough.

No protected 2026 outcomes, frozen forecast/explorer changes, subgroup-selected
rescue, post-result hyperparameter tuning or reopened team-record testing. A
source check or complete walkthrough does not certify predictive improvement.
