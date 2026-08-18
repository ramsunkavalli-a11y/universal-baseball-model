# Projection batting v1 — 2022 candidate-selection checkpoint

Last updated: 2026-08-17

Status: **SELECTION PASSED; FORM/LAMBDA FROZEN BEFORE OUT-OF-TIME VALIDATION.**

## Decision

The pre-registered 2022-only five-fold candidate-selection gate selected:

- form: `projection_age_level_ilr_ridge_v1`;
- ridge lambda: `0.01`.

This selection is now frozen. It may not be changed in response to 2023 or 2024 validation results.

## Selection evidence

Workflow run: `32100650512`  
Artifact: `9311436954`  
Digest: `sha256:9c1402ea735634451e2eae00b043e7cb3ff4fe5941a4cc9e32479a7bb044812b`

The grid contained exactly the two pre-registered forms and four lambdas, evaluated with deterministic five-fold player-held-out CV on the `2021-10-15 -> 2022` fold only.

Selected candidate versus frozen B2 carry-forward:

- log loss: `2.255059193` vs `2.256566323`;
- log-loss delta: **-0.001507130**;
- multinomial Brier: `0.869316644` vs `0.869611383`;
- Brier delta: **-0.000294739**.

The selected configuration was the unique log-loss and Brier tie-eligible configuration under the frozen tolerances. The predeclared early-reject rule therefore did **not** fire.

## Boundary

At selection time:

- 2023 candidate scores had not been accessed;
- 2024 candidate scores had not been accessed;
- 2025 outcomes remained untouched;
- future level was used only as realized scoring environment, never as a predictor;
- playing time was not modeled.

Machine-readable binding result: `docs/projection-batting-v1-selection-result.json`.

## Next gate

Run **only** `2022-10-15 -> 2023` out-of-time validation using the frozen form/lambda above.

Fit on all authorized 2022-response training rows, predict the `2022-10-15` B2 states, and score on 2023 outcomes. If 2023 log loss is not lower than carry-forward B2, the final two-fold promotion rule cannot pass; reject Projection Baseline 1 without using 2024 to rescue it. If 2023 passes, proceed to the fixed rolling-origin 2024 validation fit on 2022 + 2023 training rows.
