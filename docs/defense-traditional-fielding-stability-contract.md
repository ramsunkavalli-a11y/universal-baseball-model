# Defense traditional-fielding stability screen contract

Last updated: 2026-08-18

Status: **DEVELOPMENT-ONLY RELIABILITY SCREEN — NO DEFENSIVE VALUE MODEL.**

## Question

Do any broadly available traditional fielding rates in the already-certified 2021–2024 official source show enough adjacent-year player signal to justify a later chronology-safe predictive test against tracked defensive outcomes?

This is a reliability screen, not an accuracy/value test.

## Frozen source

Reuse only the immutable 2021–2024 official fielding captures from workflow run `32148467330` / artifact `position-role-historical-source-2021-2024`.

Do not re-fetch source and do not access 2025.

## Player-season-position construction

Aggregate all team/league rows for the same player × completed season × defensive position across affiliated baseball. Exclude P and DH.

Use exact fielding outs as the exposure denominator. Convert source baseball innings notation to outs before aggregation.

## General candidate rates

Construct from counts rather than trusting source-precomputed rate strings:

- `fielding_pct = (putOuts + assists) / chances` when chances > 0;
- `range_factor_per_9 = 27 * (putOuts + assists) / fielding_outs`;
- `errors_per_9 = 27 * errors / fielding_outs`;
- `throwing_errors_per_9 = 27 * throwingErrors / fielding_outs`;
- `double_plays_per_9 = 27 * doublePlays / fielding_outs`.

Score only adjacent-year same-player/same-position pairs with at least **300 defensive outs in both seasons**. For `fielding_pct`, also require at least 100 chances in both seasons.

## Catcher-only candidate rates

For C only:

- `caught_stealing_pct = caughtStealing / (caughtStealing + stolenBases)`;
- `passed_balls_per_9 = 27 * passedBall / fielding_outs`;
- `catcher_interference_per_9 = 27 * catchersInterference / fielding_outs`.

For catcher rate scoring require at least 300 defensive outs in both seasons. For `caught_stealing_pct`, also require at least 10 steal attempts (`caughtStealing + stolenBases`) in both seasons.

`wildPitches` and `catcherERA` are deliberately excluded from the first reliability screen because they are especially pitcher/context dependent.

## Frozen transitions

- 2021 → 2022
- 2022 → 2023
- 2023 → 2024

## Frozen metrics

For each feature and transition report:

- eligible paired player-position count;
- Pearson correlation;
- Spearman rank correlation;
- mean and median current value;
- mean and median next-year value.

Also report pooled metrics across the three transitions, with each player-transition counted once.

## Reliability screen

A feature is `predictive_target_test_warranted = true` only if:

1. at least 100 eligible pairs exist in **each** of the three transitions;
2. Spearman correlation is at least **0.10 in at least two of three** transitions; and
3. pooled Spearman correlation is at least **0.15**.

These are deliberately modest screening thresholds. Passing only authorizes a later predictive-target test; it does not authorize inclusion in Defense v1.

Do not alter thresholds after seeing results.

## Boundary

- no tracked OAA/framing target is opened by this screen;
- no regression/model is fit;
- no traditional-stat weight is selected;
- no Tier-C fallback is frozen;
- no Defense v1 projection or WAR/value calculation is authorized.
