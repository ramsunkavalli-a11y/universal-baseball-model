# Playing time / role — current status

Last updated: 2026-08-18

Status: **PLAYING TIME v1 DONE / FROZEN — CANDIDATE CONFIRMED ON ONE-SHOT 2025 HOLDOUT.**

Canonical broader handoff remains `docs/project-status.md`.

## Frozen upstream state

- Current Talent: `translated_multiseason_recency_empirical_bayes_v1`.
- One-year batting-rate Projection: `frozen_current_talent_carry_forward_v1`.
- Explicit Projection age/development challenger is closed and must not be rescued.
- Playing time remains a separate opportunity channel; zero future MLB PA never changes batting-rate skill.

## Frozen Playing Time v1

Production model:

`playing_time_recent_opportunity_40man_b2_hurdle_v1`

Architecture:

1. L2 logistic participation model for `P(next-season MLB PA > 0)`;
2. zero-truncated NB2 positive-count model for `MLB PA | MLB PA > 0`;
3. unconditional opportunity distribution from the two components.

Frozen predictor families:

- as-of level tier;
- age;
- current-season MLB PA;
- current-season MiLB PA;
- certified binary 40-man membership at the exact October 15 snapshot;
- four compact frozen-B2 batting-skill summaries.

No future team, future level, future role, 2025 roster/transaction information, player identity, or future batting-rate information is a predictor.

## Development chain — COMPLETE

Governing contract:

`docs/playing-time-role-v1-development-contract.md`

Binding chain:

- `2021-10-15 -> 2022`: candidate selection;
- `2022-10-15 -> 2023`: fixed OOT validation — PASS;
- `2023-10-15 -> 2024`: fixed OOT validation — PASS;
- development closeout: selected form refit on all authorized 2022–2024 responses and parameters/package versions frozen before 2025 — PASS.

Key records:

- `docs/playing-time-v1-selection-result.json`
- `docs/playing-time-v1-validation-2023-result.json`
- `docs/playing-time-v1-validation-2024-result.json`
- `docs/playing-time-v1-development-result.json`
- `docs/playing-time-v1-confirmation-refit-result.json`

## 2025 confirmation — PASS / BINDING

Confirmation contract:

`docs/playing-time-v1-confirmation-contract.md`

The 2025 target was isolated from scoring first:

- pre-2025 predictor/input gate: run `32144363818`;
- isolated 2025 MLB-PA target source/materialization: run `32144918922`;
- one-shot frozen confirmation score: run `32146445795`.

The source workflow persisted the completed-2025 regular-season MLB PA target before loading any model parameters. The scoring workflow then reconstructed the exact pre-2025 frozen B0 and candidate coefficients and did **not** refit either model.

Confirmation population:

- 3,759 frozen 2024-10-15 snapshot players;
- 662 with positive 2025 MLB PA;
- 3,097 with zero 2025 MLB PA.

### Binding scores

Baseline 0 — `playing_time_level_hurdle_v1`:

- full hurdle NLL: `1.339572023`;
- participation log loss: `0.192781040`;
- positive-count NLL: `6.511763297`;
- unconditional PA MAE: `39.0475`;
- unconditional PA RMSE: `97.6879`;
- participation Brier: `0.0593648`;
- predicted mean PA: `39.2659` vs observed `48.4004`.

Confirmed candidate:

- full hurdle NLL: `1.283609009`;
- candidate minus B0 full NLL: **`-0.055963014`**;
- participation log loss: `0.152517438`;
- positive-count NLL: `6.422618149`;
- unconditional PA MAE: `30.6525`;
- unconditional PA RMSE: `78.7272`;
- participation Brier: `0.0451916`;
- predicted mean PA: `48.1512` vs observed `48.4004`.

Participation calibration converged with finite parameters for both models. The candidate passed **all six predeclared confirmation gates**.

Binding result:

`docs/playing-time-v1-confirmation-result.json`

## Historical 40-man source boundary — FROZEN

Authorized semantic:

**binary membership in the requested team's official MLB Stats API `40Man` endpoint at the exact snapshot date.**

Not authorized:

- active/minors assignment;
- IL status;
- option status;
- future role;
- row-level status interpretation;
- `parentTeamId` as a membership veto.

The confirmation gate exposed a Boston/Bryan Mata row whose `parentTeamId` reflected non-authoritative assignment metadata despite presence in Boston's official 40Man response. The projector now preserves that metadata diagnostically while membership is defined by endpoint presence; cross-team membership conflicts still fail closed.

## Hard freeze

Do not:

- refit, recalibrate, reselect, rescue, or rescore Playing Time v1 against 2025;
- change its confirmation thresholds after seeing 2025;
- use 2025 playing-time outcomes to modify Current Talent or batting-rate Projection;
- infer unavailable roster semantics from the 40Man source.

The confirmed pre-2025 parameter package is the production Playing Time v1 model.

## ACTIVE NEXT LAYER — role / position / team-allocation coherence

Playing Time v1 estimates **portable individual MLB opportunity**. It intentionally does not force all player forecasts into a finite team/position allocation.

The next layer is separate and must preserve the frozen individual opportunity model while deciding what additional role/position/team context is needed for coherent downstream value/WAR calculations.

Before fitting anything new:

1. inventory existing repo/source support for player position/role and team association at chronology-safe snapshots;
2. define the exact coherence problem and whether the first version is a deterministic allocation/constraint layer or requires a separately validated statistical model;
3. freeze its inputs, outputs, chronology, and validation checks before using future outcomes.
