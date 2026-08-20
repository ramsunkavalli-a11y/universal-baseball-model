# Defense v1 repaired framing 2025 confirmation contract

## Scope

This contract is frozen after the repaired pre-2025 framing development gate and before any 2025 framing target is accessed.

The repaired historical gate selected MLB tracked framing F1. MiLB transfer had only two eligible players and is therefore insufficient; tracked framing remains MLB-only for Defense v1.

## Frozen pre-2025 parameter fit

Before any 2025 framing target access:

1. use the certified 2021-2023 tracked-framing predictor artifact unchanged;
2. use only the certified repaired 2022-2024 framing targets;
3. recreate tracked framing z exactly as in the original challenger:
   - `takes >= 500`;
   - finite `tracked_framing_per_1000_takes`;
   - standardize within source season x level group;
   - require cell count >= 15 and finite, nondegenerate population SD;
4. retain only the original MLB framing rows with input-season catcher fielding outs >= 300;
5. fit the original unregularized F1 linear model on all authorized 2022-2024 target seasons at once;
6. freeze the resulting intercept, tracked-framing-z coefficient, training population, and source hashes.

No feature, regularization, exposure threshold, target construction, or model family may change.

## 2024 confirmation predictor source

After the parameter freeze and still before any 2025 framing target access, materialize 2024 MLB tracked framing from pitch-level Baseball Savant data using the same frozen tracked-framing construction used in development.

The 2024 predictor source is target-free and must:

- use only 2024 regular-season MLB pitches;
- compute framing with the same certified SportsDataverse 0.0.75 `mlb_catcher_framing` function used for the historical tracked source;
- construct `tracked_framing_per_1000_takes` identically;
- require `takes >= 500`;
- standardize within 2024 MLB using population SD;
- require at least 15 eligible MLB catchers and finite, nondegenerate SD;
- persist source dates, package version, row counts, hashes, and the final player-level predictor table;
- perform no model fitting or 2025 target access.

## 2025 framing target

Only after both the F1 parameter package and 2024 predictor source are certified may the 2025 framing target be materialized.

Query Baseball Savant `/leaderboard/catcher-framing` directly with framing-specific season semantics:

- `type=catcher`
- `seasonStart=2025`
- `seasonEnd=2025`
- `team=`
- permissive source-side `min=1`
- `sortColumn=rv_tot`
- `sortDirection=desc`
- `csv=true`

Apply the unchanged target construction:

- valid MLBAM catcher id;
- finite `rv_tot` and `pitches`;
- `pitches >= 1000`;
- `target_raw = 1000 * rv_tot / pitches`;
- standardize globally within the eligible 2025 catcher population with population SD (`ddof=0`).

## Frozen confirmation population

A catcher is included only when all of the following are true:

- a 2024 historical catcher profile exists;
- 2024 catcher fielding outs >= 300;
- a certified finite 2024 MLB `tracked_framing_z` value exists;
- an eligible finite 2025 framing target exists.

F0 and F1 must score the exact same rows.

## One-shot 2025 confirmation gate

The gate is `insufficient` if fewer than 30 catchers are eligible.

Otherwise F1 confirms only if all are true:

- F1 MSE is strictly lower than F0 MSE;
- F1 MAE is no more than 7.5% worse than F0 MAE;
- F1 Spearman correlation with the 2025 target is at least 0.10;
- all predictions and metrics are finite;
- F0 and F1 have identical coverage.

This is the same catcher-component confirmation philosophy already used for repaired throwing/blocking: meaningful MSE improvement, bounded MAE downside, positive ranking signal, adequate sample, and identical rows.

## Binding fallback

- pass -> retain MLB F1 framing in Defense v1;
- fail -> MLB framing falls back to F0 neutral;
- insufficient -> MLB framing falls back to F0 neutral for v1;
- MiLB tracked framing remains unavailable regardless of the MLB 2025 result because the frozen development transfer gate was insufficient.

## Closed paths

After 2025 framing target access there is no refit, rescue, recalibration, threshold movement, alternate target, alternate feature, or second confirmation attempt.

This work does not modify general range, throwing, blocking, Playing Time v1, Position/Role v1, or batting models. It does not perform run-value conversion, positional adjustment, WAR, or player-value calculation.