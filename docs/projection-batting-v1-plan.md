# Batting Projection v1 Plan

Last updated: 2026-08-17 21:13 PT

Status: **MODEL IMPLEMENTATION — DEVELOPMENT SURFACES VERIFIED; 2025 OUTCOMES QUARANTINED**

## Purpose

Projection is the layer after frozen Current Talent.

It answers:

> Given a player's estimated present batting talent at an as-of date, how should that rate/profile ability be expected to change over future time?

Projection v1 is deliberately rate/profile only. It is not observed Performance, Current Talent, playing time/role, defense, WAR, or an overall ranking.

Players with zero future batting opportunities are not assigned bad rate outcomes. Opportunity/role probability remains a separate later channel.

## Governing records

Use these in order for Projection v1 modeling decisions:

1. `docs/projection-batting-v1-development-contract.md` — **binding candidate/search/promotion contract**;
2. `docs/projection-v1-methodology-review.md` — literature/methodology review completed before scoring;
3. this plan — architecture and stage boundaries;
4. `docs/projection-b2-history-reproduction-contract.md` — frozen B2 source-history interpretation;
5. `docs/project-status.md` — current handoff / next batch.

If an older section/checkpoint conflicts with the pre-registered development contract, the development contract governs Projection v1.

## Starting point

Projection v1 starts from frozen Current Talent Baseline 2:

`translated_multiseason_recency_empirical_bayes_v1`

Frozen B2 provides the common MLB-scale 12-component batting profile plus evidence/provenance context. Failed richer Current Talent challengers are not integrated.

The B2 1,095-day value is a maximum history cap. Reproduction uses current season plus prior **certified** seasons where available; the certified universal source epoch begins in 2021. Do not backfill 2018–2020 into frozen B2.

## Primary v1 question

Can a simple, leakage-safe population age/development adjustment improve next-season batting-profile prediction over carrying frozen Current Talent forward unchanged?

Answer this before adding tracking, scouting, prospect rankings, future role, or complicated machine learning.

## Output representation

Preserve the same 12-component probability profile:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

For the Projection adjustment, the composition is represented in a fixed 11-dimensional **ILR** basis and transformed back to a valid 12-part probability composition. Existing Current Talent environment translation remains frozen on its CLR contract.

A scalar MLB-equivalent expected run value may be derived as a secondary diagnostic, but model selection is based on proper scoring of the full future profile.

## Snapshot / target semantics

Primary snapshot date: **October 15**.

For snapshot year `Y`, the target is all eligible regular-season batting events in calendar year `Y+1`:

`[Y+1-01-01, Y+2-01-01)`

Predictors may use only evidence available before the snapshot. No target-year outcome, target-year role, future level, future playing time, or future public ranking/scouting update may enter predictors.

Future outcomes are scored in the actual environment where they occur. Future level is evaluation context, not a predictor.

## Chronological folds

Authorized pre-confirmation folds:

1. `2021-10-15 -> 2022` — **training / candidate-selection fold**;
2. `2022-10-15 -> 2023` — **out-of-time validation fold 1**;
3. `2023-10-15 -> 2024` — **out-of-time validation fold 2**.

Untouched confirmation:

4. `2024-10-15 -> 2025` — **quarantined confirmation**.

The three pre-2025 folds no longer share equal model-selection roles. Candidate form and lambda may be chosen only from held-out CV inside the 2022 target fold. The selected form/hyperparameter then moves unchanged through rolling-origin 2023 and 2024 validation.

## Data / source status — COMPLETE

The source/data prerequisite is no longer the active blocker.

### 2024 affiliated MiLB

Final exact report-level gate:

- run `32095039114` — success.

The accepted path requires exact aggregate reconciliation, zero unresolved residuals, exact independent proof for applied source-row quarantines, and consistent propagation of proven quarantine keys across dependent evidence grains.

### 2024 MLB

A legacy 2024 MLB game-evidence artifact used an older schema. It was not coerced into the current universal contract.

The existing historical MLB materializer was reused to create/certify v2 evidence:

- run `32096473700` — success;
- artifact `current-talent-historical-mlb-2024`;
- artifact id `9310382371`.

### Universal 2021–2024 development surfaces

Final corrected evidence-only build:

- run `32097702869` — success;
- artifact `projection-batting-v1-development-evidence`;
- artifact id `9310520964`.

This materializes the three authorized pre-confirmation snapshot/next-year surfaces. It does not fit or score a Projection model and does not access 2025.

Fast contract CI associated with the final history interpretation:

- run `32097702874` — success.

## Projection baselines

### Baseline 0 — frozen Current Talent carry-forward

Method:

`frozen_current_talent_carry_forward_v1`

At October 15, predict the next season with the player's frozen B2 latent profile unchanged.

### Baseline 1 — pre-registered age/development family

The binding specification is in `docs/projection-batting-v1-development-contract.md`.

Exactly two candidate forms are allowed:

- `projection_age_ilr_ridge_v1` — smooth piecewise-linear age main effect;
- `projection_age_level_ilr_ridge_v1` — same age basis plus as-of-level main effects.

No age × level interaction, player-specific aging slope, tracking, scouting, future level/role, or playing-time feature is allowed in v1.

Allowed ridge grid only:

`{0.001, 0.01, 0.1, 1.0}`

## Methodology rationale

`docs/projection-v1-methodology-review.md` freezes the main implications of the pre-scoring literature review:

- use partial pooling / a smooth population age structure rather than noisy single-age cells;
- respect the 12-part profile as compositional data;
- keep v1 low-dimensional because individual athletic trajectories are sparse;
- separate future-opportunity selection from conditional batting-rate skill;
- use chronological held-out future outcomes rather than in-sample fit as the decision evidence.

## Metrics / guardrails

Primary:

- future-core-event-weighted multinomial log loss.

Secondary proper score:

- future-core-event-weighted multinomial Brier.

Required diagnostics include calibration, as-of level, future level, age, evidence strength, transition class, prior MLB evidence where available, and opportunity/censoring rates.

The numeric promotion thresholds, level-reversal definition, calibration tolerance, selection tie-breaks, and confirmation refit rule are already frozen in `docs/projection-batting-v1-development-contract.md`. Do not change them after seeing 2023/2024 validation outcomes.

## 2025 confirmation boundary

**2025 regular-season outcomes remain quarantined.**

No 2025 outcome table may be opened for feature choice, candidate selection, hyperparameter selection, threshold setting, rescue tuning, or pre-confirmation validation.

If development passes, the selected exact model is refit once on all three authorized pre-2025 folds, and its coefficients/standardization/ILR basis/translation identifiers/input hashes are persisted and reproduced before 2025 access is authorized.

If fixed 2025 confirmation fails, reject Baseline 1 and retain carry-forward Baseline 0. Do not tune on 2025.

## Current implementation sequence

1. **DONE:** chronology and next-year dataset contracts.
2. **DONE:** exact source-authority/quarantine work and certified 2024 MiLB all-level gate.
3. **DONE:** certified 2024 MLB v2 evidence.
4. **DONE:** universal canonical-schema guard.
5. **DONE:** complete/verified 2021–2024 Projection development surfaces.
6. **DONE:** settle frozen B2 certified-history reproduction boundary.
7. **DONE:** complete methodology review and pre-register candidate/search/promotion contract before model scoring.
8. **CURRENT:** materialize exact frozen B2 snapshot probabilities + fold-specific translation artifacts; implement deterministic ILR and ridge design primitives.
9. **NEXT:** run 2022-only held-out candidate selection under the frozen grid.
10. **ONLY IF 2022 CV BEATS BASELINE 0:** run fixed rolling-origin 2023 and 2024 validation.
11. **ONLY IF DEVELOPMENT PROMOTION PASSES:** freeze/reproduce the all-pre-2025 refit, then authorize one 2025 confirmation.

No 2025 outcome materialization belongs in the current batch.