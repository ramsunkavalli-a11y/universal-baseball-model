# Current Talent batted-ball development execution contract

Last updated: 2026-08-17  
Status: **FROZEN BEFORE 2022 RICHER DEVELOPMENT SCORING.**

This document operationalizes the already-predeclared promotion language in `docs/current-talent-batted-ball-quality-challenger-plan.md`. It does not change the feature family, BBE definition, eligibility threshold, fit chronology, model form, or confirmation boundary.

No 2022 richer proper score had been observed when these definitions were frozen.

## Purpose

The challenger plan already requires:

1. lower equal-fold mean log loss than frozen B2;
2. no worse equal-fold mean Brier than B2;
3. at least 2/3 fold log-loss wins;
4. identical paired scoring coverage;
5. improvement that is not solely an MLB artifact;
6. no meaningfully supported non-MLB capability tier that is worse on both proper scores in at least 2/3 folds;
7. no broad new calibration failure and converged required fits.

This contract removes discretion from items 4–7 before the first development run.

## Offline evaluator boundary

Development evaluator: `scripts/materialize_current_talent_batted_ball_development.py`.

The evaluator itself performs **no network requests** and accepts no 2023 input.

Required local inputs:

- certified 2021 MiLB Current Talent evidence;
- certified 2021 MLB Current Talent evidence;
- certified 2022 MiLB Current Talent evidence;
- certified 2022 MLB Current Talent evidence;
- pre-materialized reconciled 2021 tracked-BBE parquet;
- pre-materialized reconciled 2022 tracked-BBE parquet;
- pinned local Chadwick register archive.

Tracked-BBE inputs must conform to `RECONCILED_TRACKED_BBE_SCHEMA` and contain exactly their declared season. Wrong-season artifacts fail closed.

Source acquisition/materialization is a separate manual gate. The evaluator must not fetch Savant, Chadwick, or any other external source during scoring.

## Frozen training / development chronology

Training fit:

- `2021-07-15` predictor snapshot only;
- feature standardization fit from richer-eligible B2 players at that snapshot only;
- residual coefficients fit from the same snapshot plus its 90-day future **contact** outcomes only;
- fixed L2 = `0.01`;
- no 2022 outcomes used in fitting.

Development folds:

- `2022-07-15`;
- `2022-08-01`;
- `2022-09-01`.

All three use the unchanged 2021-fitted standardization and residual coefficients.

## Primary paired cohort

At each development cutoff:

1. build frozen B2 normally for every model-eligible player;
2. build pre-cutoff EV/sweet-spot features under the corrected tracked-BBE contract;
3. apply the richer residual only to players meeting the >=20 complete tracked-BBE rule;
4. primary B2-vs-richer scoring includes **only players for whom the richer adjustment is actually applied**;
5. B2 and richer are then projected into the same realized future environments and scored on identical future events.

Players falling back to exact B2 remain valid universal production outputs but are excluded from the incremental-value comparison so exact fallbacks cannot dilute or inflate the richer result.

The paired coverage check compares:

- unique scored players;
- target-environment rows;
- future core events.

All three must match exactly within every fold.

## Equal-fold aggregation

Development selection uses the arithmetic mean of the three fold-level event-weighted proper scores.

A large fold does not receive a second weighting merely because it contains more future events. Event weighting occurs **inside each fold**; selection then gives the three chronological folds equal weight.

## Operational definition: “not solely an MLB artifact”

A player belongs to the **any observed MiLB richer-evidence cohort** at a cutoff when at least one of the result-producing, non-bunt tracked BBE contributing to the player’s pre-cutoff richer feature came from `MILB_SAVANT_TRACKED`.

This cohort can include:

- MiLB-only tracking histories;
- mixed MiLB + MLB tracking histories after promotion/demotion.

Development satisfies the not-MLB-only requirement only when:

1. the any-MiLB-evidence cohort contributes at least **1,000 future core events across the three development folds**, measured on the B2 side of the identical pair; and
2. the richer model has **lower equal-fold mean event-weighted log loss than B2** within that cohort.

If the cohort has fewer than 1,000 future core events, transport outside MLB is not established and this hard development condition fails rather than being waived.

This is intentionally stricter than merely requiring the aggregate richer model to win.

## Individual non-MLB capability-tier guardrail

Every reconciled model BBE retains an exact observed source capability token such as:

`MILB_SAVANT_TRACKED:2022:<league_id>:AAA`

For diagnostic transport checks, a player/target environment is included in a capability-tier exposure cohort when that player’s pre-cutoff richer evidence contains at least one model BBE with that exact token.

Players with mixed tracked histories may therefore appear in more than one capability-tier diagnostic. These overlapping diagnostics are **not summed into the primary model score** and are not interpreted as causal attribution to one league. They answer the narrower question: “among players whose richer evidence included this observed tracked environment, did the challenger transport acceptably?”

For each exact non-MLB capability token:

- total support is the B2-side future core-event count across all three folds;
- a tier is meaningfully supported at **>=1,000 future core events**;
- a meaningfully supported tier fails the guardrail if richer is worse than B2 on **both** log loss and Brier in at least **2 of 3** development folds.

Lower-support tiers remain reported diagnostics and cannot create or erase a hard pass/fail result.

## Calibration guardrail

Use the same pragmatic broad-failure tolerance already used in the Baseline 2 development gate.

Across the three development folds:

- all required component calibration fits must converge;
- richer mean absolute calibration-intercept error must be <= **1.25 ×** B2 mean absolute calibration-intercept error;
- richer mean absolute calibration-slope error must be <= **1.25 ×** B2 mean absolute calibration-slope error.

Fixed-bin ECE remains diagnostic rather than a standalone hard gate, consistent with prior Current Talent calibration work.

The 25% tolerance is a broad-failure guardrail, not a target to optimize against.

## Capability provenance carried into diagnostics

Player-level richer features must retain separate descriptive provenance including:

- observed model-BBE count;
- observed tracked-game count;
- MLB BBE count;
- MiLB BBE count;
- source-family group: MLB-only / MiLB-only / mixed;
- exact observed source-capability tokens;
- observed level groups;
- observed league IDs.

A source-capability label describes only observed source evidence. It never implies that all games at the same level/league were tracked.

## Development output requirements

The offline development artifact must persist at minimum:

- 2021 training features;
- frozen training standardization parameters;
- target-environment-aware residual training table;
- fitted residual coefficients and optimizer metrics;
- per-fold B2/richer aggregate proper scores;
- component proper-score/calibration diagnostics;
- standard age/B2-evidence/tracked-BBE/source-family strata;
- exact capability-tier exposure diagnostics;
- combined any-MiLB-evidence cohort diagnostics;
- player feature/provenance surface;
- explicit promotion-check booleans;
- one final `eligible_for_fixed_2023_confirmation` boolean.

## Decision boundary

Only a development artifact satisfying **every** hard promotion condition may authorize the already-fixed 2023 confirmation workflow.

A development failure means:

- retain B2;
- do not inspect 2023 richer performance to rescue the candidate;
- do not change EV/LA features, BBE semantics, >=20 threshold, penalty, training date, or model form in response to 2023.

Any later alternative is a new challenger with a new predeclared development protocol.
