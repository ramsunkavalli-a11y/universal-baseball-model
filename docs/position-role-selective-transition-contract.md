# Selective position / role transition-smoothing challenger contract

Last updated: 2026-08-18

Status: **FINAL DEVELOPMENT CHALLENGER — 2025 POSITION SOURCE UNTOUCHED.**

Upstream evidence:

- `docs/position-role-transition-challenger-result.json`
- `docs/position-role-transition-challenger-diagnostic.json`

## Why one final challenger is justified

The first frozen transition-smoothing challenger improved summed squared error in both development folds but worsened total-variation distance in both.

The pre-specified concentration diagnostic showed the same break in both folds:

- current primary-position share `< 0.65`: smoothing worsened TV;
- current primary-position share `>= 0.65`: smoothing improved TV;
- squared error improved materially for the `>= 0.65` population.

This final challenger makes only that one evidence-supported change. No position-specific rule, extra transition family, age effect, level effect, or hyperparameter search is authorized.

## Baseline

Baseline 0 remains the current-season nine-position batting-role vector carried forward unchanged.

## Frozen final challenger

Let:

- `x` = current-season nine-position role vector;
- `s` = current-season primary-position share;
- `mu_p` = chronology-safe prior-history mean next-season role vector for the player's current primary position, exactly as fit in the first challenger.

Predict:

- if `s < 0.65`: `candidate = x`;
- if `s >= 0.65`: `candidate = s * x + (1 - s) * mu_p`.

The threshold is fixed at **0.65** from the already-persisted postmortem bins. It may not be moved after this contract is committed.

## Development scoring

Reuse the exact first-challenger chronology-safe folds and transition means:

1. 2022 -> 2023, with transition means trained only on 2021 -> 2022;
2. 2023 -> 2024, with transition means trained only on 2021 -> 2022 plus 2022 -> 2023.

No 2025 position source may be loaded.

## Frozen metrics and promotion rule

For each fold, compare against raw carry-forward on the same players.

The final challenger passes development only if, in **both** folds:

1. mean total-variation distance is strictly lower than Baseline 0;
2. mean summed squared error is strictly lower than Baseline 0.

Primary-position accuracy remains diagnostic only.

No pooled-only rescue and no further development challenger are allowed.

## Decision boundary

If this challenger passes both folds:

- freeze this exact selective-smoothing form;
- authorize a separate untouched-2025 position-role source materialization and one-shot confirmation contract;
- do not modify the model after 2025 is opened.

If it fails either fold:

- close predictive position-role development for v1;
- use transparent carry-forward for v1 rather than opening 2025 for another challenger.

Regardless of outcome, no team allocator or defensive-value model is authorized here.
