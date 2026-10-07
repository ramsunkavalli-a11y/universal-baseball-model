# Test portable throwing and blocking skill with shrunk history

2026-10-06, after source/support review and before scoring. Keep all support-audit
origins and labels fixed. At the primary 2022 origin, 35/150 throwing and 57/162
blocking catchers have measured future quality. Held-player mature training has
only 21–27 throwing and 44–53 blocking people. Do not fit a detailed age curve
or select a tuning grid from these careers. Use one transparent recipe per
component, not another algorithm tournament.

Compare neutral skill with recent difficulty-adjusted native run history from
the three calendar years ending at each origin. Weights are 1, 0.5 and 0.25.
Add 100 neutral attempts to throwing's denominator and 3,000 neutral blocking
chances to blocking's denominator. The resulting rates are `100 * weighted
throwing runs / (weighted attempts + 100)` and `1000 * weighted blocking runs /
(weighted blocking chances + 3000)`. These are conservative initial regularization
assumptions, not proven optimal reliabilities or literature-derived constants.
They make sample-size regression part of the calculation rather than a separate
feature a learner can ignore. Do not adjust them after the result.

The comparison measures later MLB quality over the audit's three-calendar-year
window, not contemporaneous physical arm strength, deterrence, pitching control,
next-year awarded runs or future WAR. Keep tracking difficulties and selection
into the measured MLB survivor population visible. The run numerators are
already opportunity-adjusted; do not apply a second pitcher-quality adjustment.
Forecasting the future opportunity mix remains a separate integration problem.

Primary loss is equally weighted per-person quality RMSE at the 2022 origin;
also report MAE, signed bias, actual-exposure diagnostic run totals and 2,000
paired person-bootstrap draws with fixed seed 7053257. Score all earlier origins
separately, with 2021 explicitly a stress origin. Report age and origin-exposure
groups, profile support, coverage of unknown outcomes and year-by-year reality.
Later incomplete-window origins retain forecasts without invented outcome scores.

The player review includes fixed Realmuto, Sánchez, Hedges, Raleigh, Kirk and
Bailey where eligible; two smallest origin samples; largest gain/deterioration,
false high/low and an ordinary median-error player. Select three comparison peers
by origin-known age/exposure/ID. Trace the source annual counts, adjustment,
weights, exact numerator/denominator, reliability, forecasts, future annual path
and support. Outcome-selected cases diagnose; they do not validate independently.

A coherent improvement may support a practical research baseline even if small
groups remain uncertain. An uncertain loss does not reject throwing/blocking
information generally. Retain individual failures and source limitations. No
other fit or disposition precedes the complete player review. No production,
explorer or 2026 evaluation changes; quality gains are not total-value gains.
