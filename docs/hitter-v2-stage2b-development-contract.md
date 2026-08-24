# Hitter v2 Stage 2b calibration/contact-shape development contract

Status: **PRE-REGISTERED BEFORE STAGE 2b FIT OR SCORE**  
Date: 2026-08-24  
Machine contract: `docs/hitter-v2-stage2b-development-contract.json`

## Why a new version is justified

Stage 2 v1 remains a failed experiment. This contract does not relabel C0 or
C1, change their thresholds, or tune them after failure. The post-result audit
found two narrower facts:

1. C0 was exactly identical to B0 in V2022, then improved proper scores in both
   V2023 and V2024.
2. C1's failure came from its combined context adjustments. Direction and
   trajectory were never part of the scored implementation.

The next experiment therefore keeps terminal outcomes as the base, removes the
failed C1 park/movement/age/GIDP bundle, calibrates the outcome probabilities,
and introduces contact shape only as a reliability-weighted residual.

## Independent-evidence boundary

V2022-V2024 are now disclosed development evidence. They can diagnose and
develop this new version, but cannot promote it to production. V2022 is an
identity/training-origin diagnostic; V2023 and V2024 are the only Stage 2b
development-evaluation folds. Previously accessed 2025 remains diagnostic-only
and cannot select, promote, reject, or reweight the model.

Completed 2026 offense remains the protected one-shot confirmation. It cannot
be opened until the development method, selected candidate, refit protocol,
sources, eligible population, and scorer are frozen and review explicitly
authorizes access. Stage 2b development success would authorize only that
future confirmation package—not tracking, Stage 3, or WAR.

## Candidate ladder

`D0_NODE_CALIBRATED_C0` applies a small, identity-anchored multinomial
calibration at each C0 nested node. The fit minimizes mean future-event log loss
with a fixed `0.01` ridge penalty toward the identity transform. There is no
hyperparameter search.

`D1_TRAJECTORY_RESIDUAL` adds four PBP shape groups—`IFFB`, `OFFB`, `LD`, and
`GB`—only to contact-conditional nodes. `D2_DIRECTION_TRAJECTORY_RESIDUAL` uses
all ten direction-by-trajectory bins. D1 and D2 share:

- two-season contact-shape half-life;
- 200-event Dirichlet shrinkage;
- reliability `n_eff / (n_eff + 200)`;
- fixed `0.01` ridge penalty;
- no search over those constants;
- no effect on K, UBB, or HBP branches; and
- exact zero residual when shape evidence is absent.

This ladder answers three separate questions: does calibration help, does
trajectory add information, and does direction add information beyond
trajectory? A richer model cannot hide behind a changed cohort because every
comparison uses identical outcomes and fallback rows.

## Chronology and fitting

- V2022: no earlier forecast-target origin exists, so each new layer is the
  exact identity fallback.
- V2023: coefficients use only V2022 forecast-target pairs.
- V2024: coefficients use only V2022 and V2023 pairs.
- Any later confirmation refit uses V2022-V2024 pairs under this unchanged
  protocol. It may not use 2025 to choose or reweight the method.

Player identity, target membership, tracking availability, and missingness are
not predictors. Shape features use only seasons at or before the predictor
cutoff. Target outcomes never enter their own forecast.

## Development advance rule

On each of V2023 and V2024, in both PA- and player-weighted views, an advancing
candidate must improve terminal log loss and Brier score over the strongest
simple outcome baseline. Pooled across those folds it must also improve
wOBA/runs RMSE, improve calibration over C0, and avoid a material supported
level reversal.

D1 or D2 can advance over D0 only if, on identical rows, both proper event
scores improve and wOBA RMSE worsens by no more than 0.25%. The least complex
candidate clearing every rule is selected. A failure is documented and stops;
the fixed constants cannot be tuned on the disclosed result.

## Source conclusion

The frozen ten-bin PBP surface has 2,328,735 shape events across 6,793 players,
50,563 games, and 16 leagues in 2021-2024. It covers 99.4188% of player-games
with terminal contact and 97.1073% of terminal-contact events. Counts are an
auxiliary view, not a replacement for the exhaustive terminal outcome table.
The roughly 2.9% event-count gap is retained as source uncertainty; it is never
filled with literal zeros or allowed to become a talent feature.
