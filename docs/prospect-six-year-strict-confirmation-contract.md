# Strict six-year prospect outcome contract

**Frozen:** 2026-09-13 before scoring the corrected six-year folds

## Question

Can the unchanged historical-comparable method extend from four to six calendar years
without overlapping outcomes, self-comparisons, or a guessed FV-to-WAR conversion?

## Fixed design

- Targets: 2013, 2016, 2018 and 2019 pre-MLB snapshots.
- Outcome: complete next-six-calendar-year batting/pitching plus replacement WAR;
  non-arrivals remain zero.
- A reference origin is eligible only when its entire six-year outcome ends before the
  target origin.
- Every target player is removed from that target's reference pool.
- Keep the frozen 150 neighbors, exact primary level, age, log workload and four
  regressed basic production rates.
- Public FV, public ranks, names, current values and 2026 outcomes are forbidden.

## Phase 1 decision rule

For both hitters and pitchers in every fold:

1. expected-WAR RMSE must beat the population-mean baseline;
2. absolute expected-WAR bias may not exceed baseline by more than 0.01 WAR per
   player over six years;
3. arrival Brier score and log loss must both beat the population-rate baseline; and
4. among targets with at least ten arrived neighbors, conditional-rate RMSE must beat
   the arrived-population baseline with at least 20 actual arrivals.

MAE remains reported but does not veto an expected-mean forecast. Passing authorizes
only the six-year partial outcome distribution; it does not create whole-player WAR,
full controlled WAR, dollars or FV.
