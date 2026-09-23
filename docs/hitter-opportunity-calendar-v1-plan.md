# Hitter opportunity and calendar exposure: bounded diagnostic

Fixed 2026-09-22 before this decomposition. This follows the rejected
[anchored-development experiment](hitter-anchored-development-v1-result.md).
The previous whole-sample and combined nonpandemic scores are already known.
This is development diagnosis, not a fresh confirmation or model-selection run.

## Scope and target rules

Do not fit, tune, promote, or change current forecasts. Compare saved accepted-v2
and anchored-challenger Year-2 opportunity predictions on identical player/origin
rows. Six archived matched origins are 2016–19, 2021, 2022. The challenger has
2023 as well, but there is no accepted-v2 opportunity replay for it: report that
omission and retain the previous seven-origin value result, not invented forecasts.

The ordinary-season question is expected MLB PA in the target year under an
ordinary schedule, decomposed into probability of any MLB play and PA conditional
on play. Observed historical PA remains the label; no-play is zero and missing is
not zero. Historical normal-window scoring is a diagnostic for that question,
not evidence identifying the unobserved ordinary-season 2020 counterfactual.

Keep actual calendar production as a separate full-sample stress test. Use these
fixed regimes based on calendar alone, never outcomes or favorable scores:

- origin 2018 -> target 2020: shortened target season;
- origin 2019 -> target 2021: pandemic between cutoff and target;
- origins 2016/2017 -> 2018/2019: ordinary pre-pandemic windows;
- origins 2021/2022 -> 2023/2024: ordinary post-pandemic forecast windows.

The latter can still have pandemic-affected input history. Call them ordinary
forecast windows, not pandemic-free careers. Report both pre/post and combined
ordinary windows, plus every origin and all origins. Keep all declared rows.

For the 2020 target only, add a clearly labeled **hindsight exposure sensitivity**:
multiply both models' conditional PA by certified completed MLB team-games /
(162 x teams), from the existing schedule artifact. Leave activity probabilities
and actual labels unchanged. This is not a forecast made in 2018, not a fitting
feature, and not a full adjustment for opt-outs, roster rules or participation.
Do not scale observed 2020 PA up and call it a real full-season outcome.

## Metrics and exact decomposition

Reconstruct accepted v2 by overlaying the accepted P1 activity update on original
opportunity rows; conditional PA remains the accepted original head. Validate the
join keys, label agreement, maturity, finite outputs and complete six-origin coverage.

Groups are fixed before swaps using cutoff stage/age and original Year-1 top-50
forecasts. Report all, stages, MLB age groups, top 50, and top 50 under 26. Never
rerank groups after changing opportunity, rates or future outcomes.

Report equal-origin means: activity Brier/log loss, predicted versus actual activity,
unconditional PA RMSE/MAE/bias, active-only conditional PA RMSE/MAE/bias and support.
Retain zero-play rows in activity and total-PA/value metrics, not conditional metrics.

With old/new activity p and conditional PA q, form all four diagnostic combinations
p0*q0, p1*q0, p0*q1, p1*q1. For squared PA loss L, attribute the total change exactly:

- participation contribution = ((L10-L00)+(L11-L01))/2;
- conditional-PA contribution = ((L01-L00)+(L11-L10))/2.

Contributions sum to L11-L00 on every row. They describe saved-head swaps, not
causal effects or separately validated new models. Report the same decomposition
for value loss with the unchanged carry-forward rate in every combination. Never
divide the separate delivered value mean by opportunity and call it hitting talent.

Player-cluster paired 95% intervals (1,000 draws, seed 417) accompany unconditional
PA MSE changes for all/top-50/young-top-50 in all/ordinary windows only when at least
100 rows and three origins exist. Small groups and single disrupted seasons remain
descriptive; resampling players does not identify uncertainty over rare season shocks.

## Deliverable and stop

Save a hash-checked package of keyed rows, exact contributions, schedule sensitivity,
support and scores; test ordering invariance, zero-play handling, join/label failures,
decomposition identities, unchanged saved forecasts and no protected-year access.
Keep 2026 outcomes closed and all current forecasts unchanged. Explain which
component and calendar regime account for the observed regression. Select only a
next *question*, not a winning swapped combination or changed acceptance gate.
