# Prospect workload distribution validation plan

Status: original protocol frozen before scoring; chronology claim retracted after audit.

Correction: a six-year workload path for a 2015-2017 debut cohort contains outcomes
through 2020-2022. Those outcomes were not all available at a 2018 forecast date.
The split below is therefore an early-versus-late cohort stability test, not a
forecast-time backtest. This correction changes no calculated result.

## Question

Does the empirical six-year workload distribution used by the prospect model retain
reasonable coverage in later MLB debut cohorts?

## Cohort split

- Train distributions on players debuting in 2015-2017.
- Evaluate once on players debuting in 2018-2019.
- Retain the established `162/60` normalization for the shortened 2020 season.
- Do not use current players, partial 2026 outcomes, names, values, or outside FV.

## Method

Within player type and observed career-outcome tier, use the career-role distribution
only when the training cell has at least 30 players; otherwise use the pooled tier.
This is the same full-pooling rule as the current workload model.

Measure later-cohort coverage for the training P10-P90 and P25-P75 intervals, plus
median absolute error. Report player type, outcome tier, and supported role cells.
Use a Wilson 95% interval around observed coverage to show sampling uncertainty.

The 80% interval passes a descriptive calibration check when its Wilson interval
contains 80%; the 50% interval uses the same rule around 50%. No parameter or
fallback threshold may change after scoring.

## Boundary

This describes cohort stability conditional on eventual MLB debut, career tier, and role. It
does not validate prospect arrival probabilities, skill projections, WAR, or the
combined end-to-end range, and it is not chronology-safe model confirmation. A failure changes no production value automatically; it
identifies the workload layer that needs a separately frozen replacement test.
