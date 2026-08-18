# Projection batting v1 — 2023 out-of-time validation checkpoint

Last updated: 2026-08-17

Status: **PASSED REQUIRED 2023 LOG-LOSS GATE; 2024 ROLLING-ORIGIN VALIDATION AUTHORIZED.**

## Frozen candidate

Selection remains unchanged from the 2022-only gate:

- form: `projection_age_level_ilr_ridge_v1`;
- ridge lambda: `0.01`.

No form, lambda, age basis, level effect, or other model rule was reselected on 2023.

## 2023 result

Fit on all authorized `2021-10-15 -> 2022` response rows and evaluated on the fixed `2022-10-15 -> 2023` fold:

- candidate log loss: `2.253775007`;
- carry-forward B2 log loss: `2.254254788`;
- log-loss delta: **-0.000479781**;
- candidate multinomial Brier: `0.869857928`;
- carry-forward B2 multinomial Brier: `0.869858613`;
- Brier delta: **-0.000000686**;
- scored future core events: `851,058`;
- scored players: `3,121`.

The candidate therefore satisfies the predeclared requirement to beat carry-forward B2 on 2023 log loss. The improvement is smaller than the 2022 selection-fold improvement, so 2024 remains a meaningful independent transport test rather than a formality.

Binding machine-readable result: `docs/projection-batting-v1-validation-2023-result.json`.

## Boundary

At this checkpoint:

- 2024 candidate scores have not been accessed;
- 2025 outcomes remain untouched;
- future level was used only as realized scoring environment, not as a predictor;
- playing time was not modeled;
- the selected form/lambda cannot change in response to this result.

## Next gate

Run `2023-10-15 -> 2024` validation with the exact same form/lambda, refitting on all chronologically prior authorized training observations from the 2022 and 2023 response folds.

Because players may contribute one authorized training observation in each prior fold, the regression implementation must use a unique **training-observation key (fold + player)**. This is row-grain plumbing only; player identity is not added as a predictor and the model specification remains unchanged.

If the candidate does not beat carry-forward B2 on 2024 log loss, reject Projection Baseline 1 and retain carry-forward B2. Do not tune or rescue the model on 2024.
