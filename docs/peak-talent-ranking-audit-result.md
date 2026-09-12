# Peak pitcher talent ranking audit

Last updated: 2026-09-12  
Status: **50/50 ranking blend promoted; component mean retained**

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

The 50/50 blend was selected. Against age/level alone on the confirmation cohorts:

| Peak window | Rank correlation change | Top-decile precision change | Actual runs in selected top decile |
|---|---:|---:|---:|
| 2023 | +0.0098 | +7.0 points | +5.86 runs |
| 2024 | -0.0005 | 0.0 points | -0.06 runs |
| 2025 | +0.0165 | +2.9 points | +0.89 runs |

The full component model improved overall rank correlation in four of five replay
cohorts, but it improved realized top-decile quality in only one of five. Precise
ordering by the component mean alone is therefore rejected.

## Product decision

Pitcher peak rates continue to use the validated component model as the displayed
mean. Pitcher prospect ordering now uses an equal blend of that estimate and the
age/level estimate. This preserves real performance information while preventing
small component differences from overwhelming the historically strong signal that a
young pitcher has already reached an advanced level.

The external FanGraphs list remains audit-only. Missing pitch velocity, movement and
arsenal evidence remains the main reason some individual pitcher disagreements cannot
yet be resolved.
