# Native defensive range: baseline and reliability comparison

Locked before fitting, 2026-10-06. Follow the defense-layer V3 plan. This is a
development comparison, not a fresh final holdout or deployment authorization.

## Question, population and units

Estimate a player's later MLB range quality at a stated position, in native
range runs per 500 defensive innings (1,500 outs). Origins are end-of-season
2016–2024. Include every player-position with at least 25 measured defensive
outs within the preceding three calendar years at positions 3–9. Eligibility
uses only information known by that origin, not subsequent survival.

The fixed outcome window is the following three calendar years. Quality requires
the whole window to have elapsed by 2025, at least two measured seasons and 1,500
pooled same-position defensive outs, with no positive official exposure missing
its range measurement. Quality is the ratio of pooled runs to pooled outs, not
the player's best season. Position converts, exits and short cameos remain in
the coverage/prediction ledger with unknown quality rather than a zero label.
Report observed position changes. This conditional same-position population is
not proof of transport to players who never reach MLB or switch position.

Source: existing hashed Savant position and aggregate responses, 2016–2025, and
independent official fielding exposure. The pre-existing qualification allows
at most five outs discrepancy AND 1% of the larger denominator; use native outs.
Metric absence remains unknown. Source files are retrospective revisions, not
archived contemporaneous captures. Birth dates are immutable identity facts;
where unavailable use the dated origin-panel age, explicitly marked, or a
missing-age flag. No future performance/participation supplies an origin feature.

Exclude 2020 origins and any three-year label window crossing the shortened 2020
season from primary fitting/scoring. Retain their source/coverage rows. The 2021
origin is a separately reported COVID-era stress check, not a tuning target.

## Three matched references, no parameter search

- Neutral: zero position-relative range runs.
- Transparent history: latest three calendar years, weights 1, 0.5, 0.25;
  1,500 times weighted range runs divided by weighted defensive outs plus 3,000.
  The 3,000-out shrinkage is a fixed rough season-equivalent prior, not a fitted
  Statcast stabilization claim. Short history must not become an elite grade.
- Calibrated history: a single small model of that history rate and age/position.
  Features are history rate; reliability n/(n+3,000); age centered at 27 divided
  by ten, its square, an age-missing flag; six position indicators (1B reference);
  and history rate × reliability. Ridge alpha=10 after weighted standardization,
  with each training person receiving total weight one across repeated origins
  and positions. No candidate tuning or additional feature tournament.

Models use only three-year labels fully mature at the origin and exclude every
record for the held player's five-way ID fold. Persist actual training and test
membership, distinct-player counts and position × age-band × prior-exposure-band
support before any fit. Fit requires 100 people and two mature origin years;
otherwise use transparent history, flag it and retain the prediction. Sparse
profiles (<20 training people), feature-range extrapolation and missing ages are
visible. They are not automatic exclusions from scoring.

## Evaluation and stopping

Primary: matched player-balanced RMSE of quality for ordinary origins 2022 and
later with mature windows. Report each origin, every position, age/exposure bands,
neutral/history/calibrated errors, bias and paired person-cluster intervals.
Report 2021 separately, all origin-eligible counts and measurement-selection rates.
No pooled survivor score is an unconditional prospect/talent certification.

Assess practical magnitude, interval width and systematic group/player failures
together; no microscopic-bias veto or new weights after results. A baseline
beating neutral is useful even if the calibrated model loses to it. Prediction
and realized native run totals under actual future exposure are an explicitly
oracle-exposure diagnostic, NOT a playing-time or delivered-value forecast.

Before disposition, trace fixed cases Kiermaier, Castellanos, Arenado, Semien,
Witt and Tovar when eligible; add largest gain/loss, false high/low and median
case. Include origin-only nearest peers, some unmeasured if selected, full annual
sources, weighted inputs, fitted contributions and actual future paths. Recent
prospects without a complete quality window are shown as unknown, not forced
into scoring. Preserve both improvement and failure explanations.

Success establishes an MLB range research baseline, not full defense/WAR. The
next component/integration requires its own locked target and opportunity
qualification after this walkthrough. Frozen forecasts, 2026 results and current
explorer stay unchanged. Do not add DP/arms/catcher totals to a FanGraphs-WAR
target without a documented reconciliation.

## Pre-fit calendar clarification

The earlier blanket exclusion of label windows crossing 2020 is superseded
before fitting: MLB actually played in 2020, and this target pools measured
runs/defensive outs rather than assuming a full season of opportunities. Keep
those genuine MLB observations in historical training, naturally weighted less
by their smaller exposure. They cannot stand in for the nonexistent 2020 minor
season. Retain the two-measured-season/1,500-out rule, omit the 2020 forecast
origin, and report historical windows containing 2020 separately. Primary
evaluation remains ordinary origins 2022 onward, with 2021 a separate stress
check. Excluding all such training windows would leave just one mature origin
for 2022; that would recreate the support error rather than improve the test.
