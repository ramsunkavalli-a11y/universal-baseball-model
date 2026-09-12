# Peak pitcher talent ranking audit

Last updated: 2026-09-12  
Status: **PRECISE PITCHER ORDERING NOT VALIDATED; NO BLEND PROMOTED**

## Why this test was needed

The peak pitcher component model passed player-level and event-level probability
scores. That establishes a useful mean forecast, but it does not prove that sorting
those forecasts identifies the best future pitchers. The current top list exposed
that gap: several highly placed pitchers had ordinary strikeout/walk profiles.

This audit directly tests ordering against translated performance at ages 24–26.
Public ranks, FV and future workload weights are excluded. Run weights are estimated
from prior rows only.

## Method

Three families were compared:

- age and level only;
- the validated component-development model;
- fixed blends containing 25%, 50% or 75% component-model output, with the rest from
  age and level.

The 2018 and 2019 peak-window cohorts select the blend. The untouched 2023–2025
cohorts confirm it. The selection criterion is the realized future run quality of the
predicted top decile. Confirmation also requires no material loss in overall rank
correlation or top-decile precision.

## Result

After correcting the run-value reference to the fixed 2016–2020 MLB environment, the
25% component blend was selected. Against age/level alone on confirmation:

| Peak window | Rank correlation change | Top-decile precision change | Actual runs in selected top decile |
|---|---:|---:|---:|
| 2023 | +0.0068 | +2.3 points | +1.71 runs |
| 2024 | -0.0009 | 0.0 points | -0.01 runs |
| 2025 | +0.0073 | 0.0 points | -0.78 runs |

The full component model improved overall rank correlation in four of five replay
cohorts, but it improved realized top-decile quality in only two of five. The selected
blend exceeded the frozen 0.5-run non-inferiority limit in 2025. Precise ordering by
either the component mean or a tested blend is therefore rejected.

## Product decision

Pitcher peak rates continue to use the validated component model as the displayed
mean. The current order remains an inspection aid, not a validated ordinal ranking,
and no tested blend changes production. Age/level clearly identifies useful broad
groups; measured components add some ordering information, but the correct balance is
not yet stable at the top tail.

The external FanGraphs list remains audit-only. Missing pitch velocity, movement and
arsenal evidence remains the main reason some individual pitcher disagreements cannot
yet be resolved.
