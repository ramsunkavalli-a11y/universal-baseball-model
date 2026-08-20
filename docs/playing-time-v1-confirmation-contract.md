# Playing Time / Role v1 — 2025 confirmation contract

Last updated: 2026-08-18

Status: **FROZEN BEFORE 2025 PLAYING-TIME OUTCOME SOURCE ACCESS.**

Governing development contract:

`docs/playing-time-role-v1-development-contract.md`

Binding development result:

`docs/playing-time-v1-development-result.json`

Binding pre-confirmation refit:

`docs/playing-time-v1-confirmation-refit-result.json`

## Fixed confirmation question

Does the already-selected and already-refit Playing Time v1 challenger outperform the level-only B0 comparator on the untouched `2024-10-15 -> 2025` MLB-PA confirmation fold?

No feature, model setting, source rule, threshold, or parameter may be changed in response to 2025 outcomes.

## Frozen models

Comparator:

`playing_time_level_hurdle_v1`

Candidate:

`playing_time_recent_opportunity_40man_b2_hurdle_v1`

The exact coefficients, standardization values, NB2 dispersion parameters, model-library versions, and training row set are those frozen by `docs/playing-time-v1-confirmation-refit-result.json` before 2025 access.

Do not refit either model after opening 2025.

## Confirmation population / target

Snapshot:

`2024-10-15`

Target:

`2025 regular-season MLB plate appearances`

Every eligible frozen-B2 snapshot player receives a target, including explicit zero MLB PA.

Predictors are restricted to information available strictly before the 2024-10-15 snapshot under the frozen v1 feature contract:

- as-of level tier;
- age;
- current-season MLB PA;
- current-season MiLB PA;
- certified binary 40-man membership at 2024-10-15;
- the four compact frozen-B2 skill summaries used by the selected candidate.

No future team, future level, future role, 2025 transaction/roster information, 2025 batting-rate information, or player identity is a predictor.

## Source contract

### Snapshot / predictor side

Reuse the already-certified 2021-2024 universal evidence and frozen Current Talent B2 construction. The confirmation snapshot builder may explicitly opt into `PROJECTION_V1_CONFIRMATION_FOLD` only for the 2024-10-15 predictor snapshot. It must fail if any evidence date is at or after the snapshot.

The 40-man source remains the official MLB Stats API roster endpoint and retains the previously certified semantic boundary:

**authorized:** binary team 40-man membership at the exact snapshot date.

**not authorized:** active/minors status, IL status, option status, future role, or row-level status interpretation.

### 2025 target side

Use the already-certified bulk MLB Stats API season-hitting adapter in `universal_baseball.mlb_season_stats` for completed 2025 regular-season MLB plate appearances at actual AL/NL league grain.

Required source checks before scoring:

1. both MLB leagues return successfully through complete pagination;
2. player-season-league keys are unique;
3. required PA fields are present, integer-like, and nonnegative;
4. 2025 target rows are aggregated by MLBAM player ID across actual MLB leagues;
5. every snapshot player receives exactly one target after left joining and filling missing MLB PA with zero;
6. the target contains no non-2025 or non-regular-season counts.

2025 source capture hashes and row counts must be persisted before model scores are interpreted.

## Frozen confirmation scores

Report B0 and candidate on exactly identical snapshot players.

Primary:

- mean full hurdle negative log likelihood per snapshot player.

Required secondary checks:

- participation log loss;
- positive-count conditional negative log likelihood on observed `Y > 0` players;
- unconditional expected MLB-PA MAE;
- unconditional expected MLB-PA RMSE;
- participation Brier score;
- mean predicted MLB PA versus observed;
- participation calibration intercept/slope where identifiable;
- the same predeclared diagnostic strata used in development where supported.

## Binding pass / fail rule

The candidate confirms as Playing Time v1 only if **all** of the following hold on the one untouched 2025 fold:

1. candidate full hurdle NLL is strictly lower than B0;
2. candidate participation log loss is no worse than B0;
3. candidate positive-count conditional NLL is no worse than B0;
4. candidate unconditional MLB-PA MAE is no more than 2% worse than B0;
5. scored snapshot-player coverage is exactly identical;
6. participation calibration fits converge where identifiable and contain finite fitted parameters.

The development-only repeated-level-reversal rule required the same supported tier to fail in two independent validation folds. That repeated-fold condition is not redefined for a single confirmation fold; 2025 level strata remain diagnostics only.

No tolerance or rescue band is applied to the primary NLL requirement: a tie or higher candidate NLL fails confirmation.

## Binding outcome

If every confirmation gate passes:

- freeze `playing_time_recent_opportunity_40man_b2_hurdle_v1` as Playing Time v1;
- preserve the frozen pre-2025 parameter package as the confirmed model;
- proceed to the separate role/position/team-allocation coherence layer.

If any confirmation gate fails:

- retain `playing_time_level_hurdle_v1` as Playing Time v1;
- do not tune, rescue, reselect, recalibrate, or refit against 2025;
- proceed to the separate role/position/team-allocation coherence layer using B0.

In either case, 2025 outcomes must never modify frozen batting-rate Current Talent or Projection.
