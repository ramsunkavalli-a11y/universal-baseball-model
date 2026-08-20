# Projection batting v1 development contract

Last updated: 2026-08-17

Status: **PRE-REGISTERED BEFORE PROJECTION MODEL SCORING. 2025 OUTCOMES REMAIN QUARANTINED.**

Governing methodology review: `docs/projection-v1-methodology-review.md`.

## Purpose

Test one narrow question:

> Does a transparent population age/development adjustment improve next-season batting-profile prediction beyond carrying frozen Current Talent Baseline 2 forward unchanged?

No tracking, scouting, prospect rankings, future level, future role, future playing time, defense, WAR, or overall-ranking information is allowed.

## Fixed source / chronology boundary

Frozen Current Talent starting state:

`translated_multiseason_recency_empirical_bayes_v1`

Authorized pre-confirmation folds:

1. `2021-10-15 -> 2022` — **training / candidate-selection fold**;
2. `2022-10-15 -> 2023` — **out-of-time validation fold 1**;
3. `2023-10-15 -> 2024` — **out-of-time validation fold 2**.

Untouched confirmation:

4. `2024-10-15 -> 2025` — **quarantined until this contract, selected form, selected hyperparameters, promotion decision, and confirmation-refit parameters are frozen.**

No 2025 outcome table may be opened during candidate implementation, fitting, selection, or pre-confirmation validation.

## Projection Baseline 0

Method:

`frozen_current_talent_carry_forward_v1`

At the October 15 snapshot, carry the player's frozen B2 MLB-scale latent 12-component profile forward unchanged.

For scoring only, map that latent profile into the actual future target environment using the already-frozen training-only Current Talent level-translation contract. Actual future level is evaluation context, not a predictor.

## Projection Baseline 1 candidate family

### Common representation

Let `p_i` be the frozen 12-component B2 latent probability composition for player `i` at the snapshot.

Use a fixed 11-dimensional **isometric log-ratio (ILR)** basis over the canonical `ALL_CORE_BINS` order. The exact basis implementation must be deterministic and tested; changing the basis must not materially change fitted/predicted compositions under the shared ridge penalty.

Candidate prediction:

`ILR(p_future_i) = ILR(p_i) + delta_i`

then inverse-ILR back to a valid 12-part probability composition.

### Training response

For a training player with observed future core events:

1. aggregate future outcomes by actual target environment;
2. within each environment, form the observed 12-part target composition using the frozen Current Talent pseudocount `0.5`;
3. invert the **pre-snapshot fitted** Current Talent level translation:
   - `CLR(observed level L) = CLR(latent MLB) + beta[L]`;
   - therefore `CLR(latent target) = CLR(observed level L) - beta[L]`;
4. softmax back to a latent MLB-scale target composition for that environment;
5. multiply by that environment's future core-event count, pool translated effective counts across the player's future environments, and renormalize;
6. transform the pooled latent target composition to ILR coordinates;
7. response is `target_ILR - snapshot_B2_ILR`.

Training weight is the player's total observed future core-event count. Zero-future-opportunity players are not assigned an artificial response.

## Candidate forms

Exactly two forms may be compared.

### Form A — age only

Method label:

`projection_age_ilr_ridge_v1`

One shared predictor design is fit as a multi-output ridge regression for all 11 ILR deltas.

Age basis, with snapshot age in years:

- intercept, unpenalized;
- `(age - 27) / 5`;
- `max(age - 20, 0) / 5`;
- `max(age - 23, 0) / 5`;
- `max(age - 26, 0) / 5`;
- `max(age - 29, 0) / 5`;
- `max(age - 32, 0) / 5`;
- `max(age - 35, 0) / 5`.

This is a continuous piecewise-linear age curve with linear tails. No integer-age cells and no higher-order polynomial are allowed.

### Form B — age + as-of level

Method label:

`projection_age_level_ilr_ridge_v1`

Use the identical age basis plus main-effect indicators for the player's **as-of** level group:

- Rookie Complex;
- Single-A;
- High-A;
- AA;
- AAA;
- MLB is the reference level.

No age × level interaction is allowed.

## Ridge fitting contract

For each fit:

- standardize every non-intercept predictor using the training rows' future-event-weighted mean and RMS scale;
- retain and reuse those training-only centering/scaling values when predicting held-out rows;
- intercept is unpenalized;
- all other coefficients share one ridge penalty;
- if a non-intercept predictor has zero weighted RMS after centering in a training split, retain the predictor in its frozen design position, set its stored scale to `1.0`, transform it to all zeros for that fit, and therefore leave its ridge coefficient at zero; do not drop/reorder predictors or borrow a scale from held-out data;
- minimize

`weighted mean squared ILR-delta error + lambda * squared Frobenius norm of penalized coefficients`.

Allowed `lambda` grid, and no others:

`{0.001, 0.01, 0.1, 1.0}`

No component-specific lambda, knot search, level interaction, age-boundary search, or rescue grid is permitted in v1.

## Candidate selection — 2022 fold only

Use only `2021-10-15 -> 2022` target outcomes to choose Form A/B and lambda.

Run deterministic 5-fold player-held-out cross-validation:

`cv_fold = int(first_8_hex(SHA256(str(player_id))), 16) % 5`

Requirements:

- a player appears in exactly one CV fold;
- each held-out fold is predicted by a fit that excludes that player's 2022 target response;
- current B2 state and pre-snapshot translation are allowed because they predate the target;
- future 2022 opportunity/counts are used only as target response/scoring evidence.

For every form/lambda pair, score held-out future events in their actual target environments using the same proper-score machinery as Baseline 0.

Selection order:

1. lowest pooled event-weighted multinomial log loss across all 5 held-out folds;
2. if log-loss values differ by no more than `1e-5`, lowest pooled event-weighted multinomial Brier;
3. if still tied within `1e-6` Brier, prefer **Form A (age only)**;
4. if form is also tied, prefer the **larger lambda**.

Early reject rule:

- if the selected candidate does not beat Baseline 0 on pooled 2022 CV log loss, stop Projection v1 development and retain carry-forward Baseline 0; do not inspect 2023/2024 to rescue the candidate.

## Out-of-time validation

Only after candidate form/lambda are selected on 2022:

### Validation fold 1 — 2023 outcomes

- fit the selected fixed form/lambda on all authorized `2021-10-15 -> 2022` training rows;
- predict the `2022-10-15` B2 states;
- score on 2023 outcomes.

### Validation fold 2 — 2024 outcomes

- keep the same form/lambda unchanged;
- refit on all chronologically prior authorized training rows from the 2022 and 2023 outcome folds;
- predict the `2023-10-15` B2 states;
- score on 2024 outcomes.

This is a rolling-origin validation. 2024 is never used to fit its own prediction.

## Primary / secondary scores

Primary:

- future-core-event-weighted multinomial log loss.

Secondary proper score:

- future-core-event-weighted multinomial Brier score.

Report each validation fold separately and the equal-fold mean.

Scalar run-value MAE/RMSE/correlation may be reported only as secondary diagnostics and cannot promote a candidate that fails the proper-score gate.

## Promotion rule to 2025 confirmation

The selected Baseline 1 advances only if **all** conditions pass:

1. validation-fold log loss is lower than Baseline 0 in **both** 2023 and 2024;
2. equal-fold mean Brier is no worse than Baseline 0;
3. paired scored-player / target-environment / future-core-event coverage is exactly identical;
4. no meaningfully supported as-of-level stratum has a repeated material reversal:
   - meaningful support = at least `1,000` future core events in each validation fold;
   - material reversal in a fold = candidate minus Baseline 0 log loss `> +0.002` **and** candidate minus Baseline 0 Brier `> +0.0004`;
   - fail if the same meaningful as-of-level stratum has a material reversal in both validation folds;
5. all identifiable component calibration fits converge;
6. across identifiable components, the equal-fold mean absolute calibration-intercept error and mean absolute calibration-slope error are each no more than **20% worse** than Baseline 0;
7. fixed-bin ECE is reported but is not a hard promotion gate;
8. opportunity-selection diagnostics are reported by age band and as-of level, including predictor-without-target rates; no zero-PA player is converted into a bad-skill target;
9. no implementation path accesses 2025 outcomes or future level/role as predictors.

A candidate that fails is rejected. Do not search new knots, lambdas, interactions, transformations, evidence-strength terms, or component-specific adjustments on the 2023/2024 validation results.

## Required diagnostics

At minimum retain:

- aggregate proper scores by fold;
- as-of level;
- future actual level;
- transition class: same level / promotion / demotion / MLB debut / MLB-to-MiLB;
- age bands;
- B2 effective-evidence bands;
- with/without prior MLB evidence where available;
- component proper scores;
- calibration intercept/slope and fixed-bin reliability;
- predictor-without-target and target-without-predictor counts/rates;
- coefficient tables and age-curve displays for all 11 ILR coordinates plus back-transformed representative compositions.

## Confirmation refit rule

If and only if development promotion passes:

1. freeze the selected form and lambda permanently for Projection v1;
2. refit that exact model once on **all three** authorized pre-2025 folds (2022, 2023, 2024 outcomes);
3. persist coefficient matrix, predictor standardization values, ILR basis definition/order, translation artifact identifiers, training row counts, and content hashes;
4. verify deterministic reproduction from those persisted inputs;
5. only then authorize opening/scoring 2025 outcomes;
6. run one fixed `2024-10-15 -> 2025` confirmation;
7. require lower aggregate log loss, no-worse aggregate Brier, identical coverage, the same level-reversal definition, and the same 20% calibration guardrail;
8. if confirmation fails, reject Baseline 1 and retain carry-forward Baseline 0. Do not tune on 2025.

## Explicit exclusions from v1

Do not add during this gate:

- player-specific aging slopes;
- comparable-player nearest-neighbor systems;
- age × level interactions;
- position/body-size inputs;
- tracking/process metrics;
- scouting grades/prospect ranks;
- future level or roster role;
- playing-time probability;
- injury information;
- imputed pseudo-performance for seasons with zero future opportunity;
- neural nets, boosted trees, random forests, or other high-capacity learners.

Those may be separate future challengers after the simple age/development question is answered.