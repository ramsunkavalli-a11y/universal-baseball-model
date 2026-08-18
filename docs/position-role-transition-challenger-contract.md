# Position / role transition-smoothing challenger contract

Last updated: 2026-08-18

Status: **DEVELOPMENT-ONLY CHALLENGER — 2025 POSITION SOURCE UNTOUCHED.**

Upstream evidence:

- `docs/position-role-historical-source-result.json`
- `docs/position-role-batting-profile-stability-result.json`

## Question

Does one transparent, chronology-safe transition-smoothing rule predict next-season batting position/role profiles better than carrying the observed role profile forward unchanged?

This gate is deliberately narrow. It does not authorize a general position model, a defense model, a team allocator, or 2025 position-source access.

## Target profile

Use the frozen nine-position batting-role profile:

- C
- 1B
- 2B
- 3B
- SS
- LF
- CF
- RF
- DH

Pitcher usage remains excluded from the batting-role channel.

## Baseline

For every scored player, Baseline 0 is the current-season role vector carried forward unchanged.

## Challenger

The challenger has no tuned hyperparameters.

For each training transition, group players by their **current-season primary position** and compute the mean next-season nine-position role vector for that group.

For a scored player:

- `x` = current-season nine-position role vector;
- `s` = current-season primary-position share;
- `mu_p` = historical mean next-season role vector for players whose current primary position was `p`.

Predict:

`candidate = s * x + (1 - s) * mu_p`

Interpretation: concentrated current roles receive more carry-forward weight; multi-position current roles receive more historical transition smoothing.

If a primary-position training group is unexpectedly absent, fail closed rather than substitute another position or future data.

## Chronology-safe folds

The 2021 -> 2022 transition is training warm-up only.

Score exactly two folds:

1. **2022 -> 2023**
   - train transition means on 2021 -> 2022 only;
   - score players present in both 2022 and 2023.
2. **2023 -> 2024**
   - train transition means on 2021 -> 2022 plus 2022 -> 2023;
   - score players present in both 2023 and 2024.

No 2025 fielding/position source may be queried or loaded.

## Frozen metrics

Primary metric:

- mean total-variation distance between predicted and observed next-season nine-position role vectors.

Secondary proper vector-error metric:

- mean sum of squared error across the nine position shares.

Diagnostics only:

- exact predicted-primary-position match rate;
- player counts;
- training counts by current primary position;
- mean current primary-position share.

## Frozen promotion rule

The challenger passes development only if **both** of these are true in **each** scored fold:

1. challenger mean total-variation distance is strictly lower than Baseline 0;
2. challenger mean summed squared error is strictly lower than Baseline 0.

No pooled-only rescue is allowed. Primary-position accuracy is diagnostic and cannot rescue a failed full-profile metric.

## Decision boundary

If the challenger passes both scored folds, freeze this exact candidate form and authorize a separate untouched-2025 position-role confirmation contract.

If it fails either scored fold, do not access 2025 position-role outcomes. Inspect the failure and define at most one next development challenger before reconsidering architecture.

Regardless of the result:

- Playing Time v1 remains frozen;
- batting Projection v1 remains frozen;
- no team allocator is authorized;
- no defensive-value model is authorized.
