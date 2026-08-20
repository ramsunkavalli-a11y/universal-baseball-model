# Projection batting v1 — development checkpoint

Last updated: 2026-08-17

Status: **EXPLICIT AGE/DEVELOPMENT CHALLENGER REJECTED; CARRY-FORWARD B2 RETAINED AS PROJECTION V1 RATE MODEL.**

## Decision

Projection v1 asked whether a simple, leakage-safe population age/development adjustment improves next-season batting-profile prediction over carrying frozen Current Talent B2 forward unchanged.

The answer under the pre-registered gate is **no**.

Retain:

`frozen_current_talent_carry_forward_v1`

as the one-year batting-rate Projection v1 model.

Reject the selected challenger:

- form: `projection_age_level_ilr_ridge_v1`;
- ridge lambda: `0.01`.

Do not tune, rescue, expand, or reselect this challenger using the observed 2023/2024 validation outcomes.

## Evidence

### 2022 candidate selection

The frozen challenger was selected using only deterministic five-fold player-held-out CV inside the `2021-10-15 -> 2022` fold:

- log-loss delta vs carry-forward B2: **-0.001507130**;
- Brier delta: **-0.000294739**.

It passed the predeclared early-reject rule and advanced.

### 2023 out-of-time validation

Fit only on authorized 2022-response training rows:

- log-loss delta: **-0.000479781**;
- Brier delta: **-0.000000686**;
- future core events: `851,058`;
- scored players: `3,121`.

The candidate passed the required 2023 log-loss gate.

### 2024 rolling-origin out-of-time validation

Same form/lambda, refit on authorized 2022 + 2023 training observations:

- log-loss delta: **+0.000256881**;
- Brier delta: **+0.000156946**;
- future core events: `857,183`;
- scored players: `3,048`.

The candidate therefore failed the binding requirement to beat carry-forward B2 on log loss in **both** out-of-time validation folds. Development promotion fails immediately; no downstream calibration/stratum diagnostic can rescue a failed primary gate.

## Interpretation

The result is consistent with the pre-scoring methodology review's caution that a well-shrunk, recency-weighted present-talent estimate can be difficult to improve with a generic one-year aging adjustment.

There is evidence of a small predictable population age/level signal in the 2022 selection fold and 2023 validation fold, but it did not transport robustly to 2024. V1 therefore does not force an explicit age adjustment merely because conventional projection systems contain one.

This does **not** establish that aging/development is literally zero. It establishes that this transparent universal age+level adjustment does not clear the project's required out-of-time predictive bar beyond frozen B2 carry-forward.

## Holdout / future challenger boundary

**2025 outcomes were never accessed.**

No 2025 confirmation is authorized for the rejected Baseline 1 challenger. Preserve 2025 as untouched evidence for a future separately pre-registered Projection challenger if useful.

Potential future challengers may include richer hierarchical/comparable/process models, but they must be treated as new models with their own leakage-safe design and may not be tuned as a rescue of this failed v1 challenger.

## Next stage

Projection v1 rate/profile is now complete for the current ranking-system build.

Proceed to the separate **playing-time / role** channel. Opportunity must remain distinct from batting-rate skill so a player projected for few opportunities is not treated as a worse hitter.

Binding machine-readable result: `docs/projection-batting-v1-development-result.json`.
