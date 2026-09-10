# Pitcher aging protected 2026 confirmation contract

**Frozen before reading 2026 targets:** 2026-09-10  
**Status:** Forecast freeze authorized; evaluation waits for final regular-season data

## Forecasts

Use the frozen October 15, 2025 pitcher opportunity and conditional-rate path. Store
the incumbent Tango regressed adjacent-pitching age curve and an exact no-aging
counterfactual. Opportunity, workload, role, replacement, run environment, player
denominator and all other inputs remain identical. Do not refit either forecast.

## Fixed decision rule

Retain Tango aging only if, after final official 2026 regular-season totals are joined
with missing players set to zero production:

1. component log loss is no worse than no aging;
2. zero-inclusive neutral-WAR squared error is no worse and its paired player-
   bootstrap 95% upper bound for Tango minus no-aging is at or below zero; and
3. absolute aggregate neutral-WAR bias is no worse.

Supported age bands with at least 100 positive-BF pitchers are guardrails: none may
have WAR mean squared error more than 5% worse. MAE may be reported descriptively but
cannot select an expected-WAR forecast because it targets the median. There is no
rescue tuning, blending, clipping,
subgroup override or player exclusion after targets are read. Failure selects no
aging provisionally and requires a separate contract before fitting another curve.

No 2026 outcome, team-depth, name, contract or outside-FV field may enter the freeze.
This test confirms only one-year MLB pitcher component aging.
