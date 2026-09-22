# Exact pitcher opponent-quality result

Date: 2026-09-22
Status: **retain for descriptive adjustment; do not add to future value model**

## Question

Does knowing the exact quality of the hitters a minor-league pitcher faced improve
next-season MLB pitcher value beyond his own age, level, role, workload, and results?

## Test

Every affiliated plate appearance from 2016-24 was linked to the batter's strictly
prior three-year profile. The profile included strikeout, control, home-run, hit,
damage, ground-ball, air-ball, line-drive, and popup tendencies, both overall and
against the pitcher's handedness. These actual opponent exposures were averaged to a
pitcher-season and added as a separate optional feature block.

The same six expanding forward tests and zero-inclusive pitcher-value target were
used. Missing context was neutral. The context block covered 27,919 of 29,491 scored
rows. No 2026 result was used.

## Result

| Engine | Baseline RMSE | Exact-opponent RMSE | Change |
|---|---:|---:|---:|
| Ridge | **0.31248** | 0.31520 | +0.00271 |
| CatBoost | **0.31282** | 0.31286 | +0.00004 |
| LightGBM | **0.31377** | 0.31435 | +0.00058 |

Putting opponent context only into conditional value did not rescue the result. Ridge
was clearly worse with a fully unfavorable uncertainty interval; the nonlinear models
were flat to worse.

## Decision

Do not add average exact-opponent quality to the pitcher value forecast. Keep it in
the event-level evaluation layer, where it makes comparisons of past performance
fairer. Once a pitcher's own level-relative outcomes are already present, his average
opponent mix does not add stable information about future MLB value.

This does not reject individual hitter-pitcher matchup effects. It rejects the simpler
idea that the average strength and type of hitters faced should be carried forward as
additional pitcher talent.
