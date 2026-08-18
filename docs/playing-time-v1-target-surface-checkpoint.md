# Playing-time v1 target-surface checkpoint

Last updated: 2026-08-17

Status: **PASS — NEXT-SEASON MLB PA TARGET IS PRODUCTION-SHAPED FOR 2022–2024 DEVELOPMENT; NO MODEL FIT.**

Binding result:

`docs/playing-time-v1-target-surface-result.json`

## Target

For every frozen B2 October snapshot player:

`Y = next-calendar-year regular-season MLB PA`

including explicit `Y = 0`.

The surface is built entirely from already-certified pre-2025 development artifacts. Batting rate was not modified and no playing-time model was fit.

## Distributional result

| fold | snapshot players | players with MLB PA | zero MLB PA | positive PA mean | positive PA median | positive variance/mean |
|---|---:|---:|---:|---:|---:|---:|
| 2021 -> 2022 | 4,702 | 685 | 85.43% | 264.7 | 221.0 | 170.7 |
| 2022 -> 2023 | 4,040 | 644 | 84.06% | 282.4 | 251.5 | 165.3 |
| 2023 -> 2024 | 3,985 | 645 | 83.81% | 280.9 | 249.0 | 166.8 |

The target is therefore both **strongly zero-heavy** and **strongly overdispersed among positive counts**.

This supports the pre-model methodology decision to separate:

1. probability of any next-season MLB PA; and
2. positive MLB PA amount/distribution.

A single ordinary all-player PA regression is not the preferred first family.

## Level separation

As-of level is strongly informative about next-season MLB participation in all three folds.

Examples:

- 2022 target: MLB snapshot players `50.4%`, AAA `24.2%`, AA `9.5%`, High-A `2.9%`, Single-A/Rookie `0%` received MLB PA;
- 2023 target: MLB `85.0%`, AAA `24.1%`, AA `9.2%`, High-A `1.5%`, Single-A `0.5%`, Rookie `0%`;
- 2024 target: MLB `85.9%`, AAA `30.5%`, AA `6.5%`, High-A `1.1%`, Single-A/Rookie `0%`.

These are descriptive target rates only. They do not authorize a particular level coefficient or interaction before the model contract is frozen.

The unusually low 2022 follow-on rate for players whose 2021 as-of level was MLB is visible and must remain part of chronological validation rather than being smoothed away by hand.

## Boundary

- 2025 accessed: **False**;
- playing-time model fit: **False**;
- role thresholds applied: **False**;
- batting-rate model changed: **False**.

## Next gate

Resolve the historical roster-source audit. Only after that result should the project decide whether exact 40-man status enters the frozen v1 feature set.

Then freeze the exact two-part baseline/candidate models, feature sets, development metrics, promotion rules, and 2025 confirmation contract before fitting.
