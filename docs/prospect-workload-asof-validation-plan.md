# Prospect workload as-of validation plan

Status: frozen before scoring.

## Question

Does the conditional six-year MLB workload distribution achieve reasonable later-
cohort coverage when every training outcome was fully known before the forecast date?

## Source and timing

- Official MLB StatsAPI batting and pitching totals, 2009-2025.
- Exact official debut dates for the complete observed-player universe.
- Evaluate 2018 and 2019 debut cohorts separately.
- For evaluation year `Y`, a training path is eligible only when its six-year window
  ends before `Y`. Thus 2018 may use debut cohorts through 2012 and 2019 may use
  cohorts through 2013.
- Exclude 2020 as an evaluation debut cohort. Keep the established `162/60` workload
  normalization when 2020 occurs inside a six-year outcome path.

## Method

This validates the workload layer conditional on actual debut, eventual career tier,
and eventual pitcher role. Within player type and tier, use role-specific training
only with at least 30 eligible players; otherwise use the pooled tier. Measure P10-
P90 and P25-P75 empirical coverage, Wilson 95% intervals, median error, and median
absolute error by evaluation year, player type, tier, and source.

The descriptive 80% target is retained when 80% lies within its Wilson interval; the
50% target uses the same rule. No distribution parameter changes after scoring.

## Boundary

This is chronology-safe for the conditional workload submodel, but it uses future
evaluation outcomes to identify the evaluation player's realized tier and role. It
does not validate arrival probabilities, pre-debut tier/role prediction, skill, WAR,
or end-to-end value. Current 2026 outcomes, player names, outside FV, contracts, and
current values are excluded.
