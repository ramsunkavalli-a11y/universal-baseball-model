# Coherent next year MLB event forecasts

2026-10-02. Before fitting. V35's negative representation test and 17 player
reviews are complete. Keep V34's source-repaired identities/workload and V33b
working forecasts. This tests a different conditional batting likelihood, not
another linear transformation of a batting-value regression.

## Target and model

Predict eight mutually exclusive next-year MLB PA outcomes: other, strikeout,
unintentional walk, hit by pitch, single, double, triple and home run. Other
includes intentional walks and sacrifices as well as remaining outs, matching
the existing fixed-PA batting target's accounting. These are not pitch outcomes,
same-level minor performance or full WAR. Count every team stint.

Use a regularized multinomial logit with age, source position, dated draft
pedigree, observed MLB career exposure, soft roster listing, cancellation/gap
flags and the existing independently stabilized three-year per-league components
and exposure. Exclude legacy batting-value quality/workload predictors so they
cannot silently override the event approach. Preserve fourteen separate league
buckets and actual 2020 sample sizes. Learned coefficients can translate each
source's predictive information, without asserting causal/park-neutral MLEs.

Training log-odds have an offset for that mature target season's observed MLB
event environment; labels are actual counts, not a player's noisy log-rate.
Use the origin season's completed league event environment for prediction and
convert predicted probabilities relative to the same origin environment with
the existing fixed neutral wOBA weights, scale and ten runs/win. This explicit
stationarity assumption does not claim to predict future ball/park changes.
Target-environment counts are used only for mature training outcomes and label
verification, never as held-forecast inputs. Macro environment is public league
information; this does not fit to held-player future statistics.

Joint probabilities must be nonnegative and sum to one. Anchor other log-odds
at zero; unpenalized intercepts and fixed physical feature scales. Minimize the
count log likelihood with equal-origin weights multiplied by actual target PA,
normalized to equal-year contribution as in V34's active head. Fixed L2 penalty
0.001 on non-intercept coefficients; L-BFGS-B max 500 iterations, gradient
tolerance 1e-6, no tuning, random split or validation-based selection. A solver
failure must be reported, not silently deployed or retuned on evaluated losses.
Thirty-five saved heads. Gradient check and zero-effect offset tests precede
fits; distinguish numerical convergence from predictive validity.

## Contrast and coverage

Same 30,506 evaluation rows, whole-player folds, mature training memberships
and target-2020 exclusion as V34. Only future-active rows inform conditional
batting rates; all non-arrivals remain in contribution scoring. No 2026 outcomes,
new college collection, outcome-total scaling or roster/health inventions.
Reconstruct event accounting and the existing conditional target exactly from
dated MLB counts before fitting. Missing source/targets are a hard failure, not
invented zeros. Known empty target participation must agree with certified
existing target coverage. Audit new actual feature support before fits and keep
incomplete foreign/park/opponent/pedigree/support limits visible.

Retain V34 expected PA and origin replacement in the product so rate-model
changes cannot hide behind changed opportunity. Report V33b and earlier N/V24
references on matches; public PA cannot improve in this rate-only test.

## What determines the decision

Primary conditional rate RMSE/MAE/bias, actual-PA weighted within equal years,
and delivered batting-plus-replacement RMSE on fixed membership. Also count
log loss/component calibration, public matches with qualified environment/
snapshot differences, every origin/stage and brief-debut/thin-entry/absence
groups, cohort totals, and nominal paired player-cluster uncertainty. Require
baseball improvement rather than just physically valid probabilities.

Fixed cases McNeil 2018, Steer 2022, Winn 2023, Kurtz 2024, Judge 2016/2024,
Olson 2022, Lux 2023, McLain 2024 and Tatis 2022. Add largest gain/harm, false
high/low and ordinary case. Show dated stats, actual features, league offsets,
event probabilities, linear predictors, runs conversion, fixed PA, outcome and
origin-selected peers. Save the reviewed case judgments before disposition or
another experiment. No automatic research/production promotion.

A failure rejects this fixed logit specification, not all event-component
forecasting. An improvement can support a candidate batting head but cannot
resolve the public MAE opportunity gap, unavailable job/health information,
general defense, full player value or multiyear control by itself.
