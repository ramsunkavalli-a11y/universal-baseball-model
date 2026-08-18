# Batting Projection v1 Plan

Last updated: 2026-08-17 19:42 PT

Status: **IMPLEMENTATION / DEVELOPMENT-DATA ASSEMBLY — 2025 OUTCOMES QUARANTINED**

## Purpose

Projection is the layer after frozen Current Talent.

It answers:

> Given a player's estimated present batting talent at an as-of date, how should that rate/profile ability be expected to change over future time?

Projection is not:

- observed Performance;
- Current Talent itself;
- playing time or roster opportunity;
- defensive value;
- WAR;
- an overall ranking.

The first Projection implementation is deliberately rate-only. Playing time / role probability remains a separate future channel so lack of opportunity is never treated as bad batting skill.

## Current implementation status

The design has moved beyond pre-development planning, but model development scoring has **not** started.

Completed / passing deterministic work:

- chronological Projection fold/window contracts;
- next-year dataset contract;
- development-evidence materializer compilation/contract coverage;
- exact-game official outcome fallback behavior;
- exact-game league fallback behavior;
- exact source-only residual quarantine policy;
- cross-grain quarantine propagation across outcome/contact evidence;
- fail-closed quarantine for PBP games whose same-game league cannot be authorized because the exact official game endpoint returns 404.

Recent passing runs include `32092505104`, `32092672387`, and `32092714174` for the quarantine/source-authority layer.

### 2024 discrepancy diagnosis

Earlier historical runs failed. Official-feed recovery run `32091704947` demonstrated that `game_pk 755829` returns **404 Not Found** from `https://statsapi.mlb.com/api/v1/game/755829/feed/live`, so direct official PBP cannot adjudicate that game via the expected surface.

Source-only residual audit `32092166134` then **passed** and localized the observed aggregate discrepancy to exactly two deterministic source-only rows:

- High-A player `669233`, game `755829`: `PA=1, AB=1`, with no BB/HBP/SO/SF/SH/CI.
- Single-A player `686541`, game `754395`: `PA=1, AB=1, SO=1`, with no BB/HBP/SF/SH/CI.

For both rows, season totals mismatch before removal, match after removal, and post-removal totals match the official gameLog control. Audit artifact `9308734004`; digest `sha256:574f6f7bd6eb0278ea3a654cb97762ce7fbed07c912e32261f2da5883435a466`.

### Exact residual quarantine policy

Primary helper:

`src/universal_baseball/current_talent_source_residual_quarantine.py`

Frozen policy name:

`single_source_only_exact_season_and_official_residual_v1`

A reusable player-game row may be quarantined only when:

1. it is the **single** positive-PA source game absent from official gameLog for that player/league;
2. its PA/BB/HBP/SO vector exactly equals the independent season-player aggregate residual;
3. removing its complete PA/AB/BB/HBP/SO/SF/SH/CI vector makes the remaining player-game totals exactly equal the official gameLog aggregate.

Anything less remains unresolved. The helper does not guess identity, league, or outcome values and does not reassign source values.

The historical wrapper now carries proven quarantined player/game keys across all dependent evidence grains:

- outcome rows;
- player-game contact controls;
- same-player PBP contacts.

For league identity, an exact official-game 404 is recorded and that unauthorizable PBP game is quarantined rather than inheriting filename-level league identity.

Cross-grain implementation: commit `be8eb1b781fcc8560e1ac2caec2413a2cc4ea2c3`.

Fast CI runs `32092672387` and `32092714174` both passed.

### Full 2024 historical gate

The quarantine-enabled historical path has now been launched:

- run `32092672369` — **Quarantine exact 2024 source residuals across evidence grains**;
- run `32092745178` — **Gate 2024 MiLB on exact source quarantine tests**.

At this documentation cutoff they were queued. Their live state is recorded in `docs/projection-recovery-status.json`.

The current task is therefore to evaluate those runs and require a clean certified 2024 historical artifact before any Projection model scoring.

Machine-readable status:

- `docs/projection-status.json`
- `docs/projection-recovery-status.json`

Canonical human handoff:

- `docs/project-status.md`

## Starting point

Projection v1 starts from frozen Current Talent Baseline 2:

`translated_multiseason_recency_empirical_bayes_v1`

No Challenger-1 or Challenger-2 richer contact residual is integrated.

The Current Talent state includes the common MLB-anchored 12-component batting profile plus evidence/provenance fields.

## Primary v1 question

Can a simple, leakage-safe age/development adjustment improve **next-season batting-rate/profile prediction** over carrying frozen Current Talent forward unchanged?

The first Projection gate should answer this before adding tracking, scouting, prospect rankings, role information, or complicated machine learning.

## Output representation

Preserve the same core batting probability/profile language used by Current Talent:

- BB/HBP;
- K;
- IFFB;
- Pull / Center / Opposite × OFFB / LD / GB.

A scalar MLB-equivalent expected run value may be derived as a secondary diagnostic, but model selection remains based primarily on proper scoring of the full future outcome profile.

## Snapshot semantics

Primary v1 snapshot date:

`October 15`

for each source season.

This is intentionally after the affiliated/MLB regular-season evidence used by the model while avoiding dependence on a particular league's opening/closing-day calendar.

Predictors at an October 15 snapshot may use only eligible baseball evidence with:

`occurred_at <= October 15`

under the same retrospective event-cutoff semantics already used by Current Talent.

No target-year outcomes, target-year role, future level, future playing time, or future public ranking/scouting updates may enter predictors.

## Primary target horizon

For an October 15 snapshot in year `Y`, the primary rate target is all eligible regular-season batting events in calendar year `Y+1`:

`[Y+1-01-01, Y+2-01-01)`

This is a one-season / approximately one-year Projection target.

Players with zero future batting opportunities are not assigned bad rate outcomes. Their absence is an opportunity/role observation and is reported separately.

Future outcomes are scored at the actual environment in which they occur. Promotion or demotion is not itself a prediction error.

## Development folds

Projection v1 development may use exactly these three chronological folds:

1. as-of `2021-10-15` -> 2022 regular-season outcomes;
2. as-of `2022-10-15` -> 2023 regular-season outcomes;
3. as-of `2023-10-15` -> 2024 regular-season outcomes.

The 2023 Challenger-2 confirmation outcomes are no longer untouched and are therefore eligible development evidence for this genuinely new Projection question.

2024 has already been source-certified for Performance work, but no Projection v1 model has been selected against 2024 outcomes. It remains a development fold, not confirmation.

## Untouched confirmation

**2025 regular-season batting outcomes are quarantined for Projection v1 confirmation.**

Before any 2025 outcome table is opened or scored, the following must be frozen and persisted:

- v1 target definition;
- predictor set;
- candidate model forms;
- any hyperparameter/search grid;
- development folds;
- primary/secondary metrics;
- promotion guardrails;
- confirmation refit rule.

No 2025 outcome inspection is allowed to choose features, change model form, change thresholds, or rescue a failed confirmation.

If 2025 evidence is accidentally accessed for model selection, it loses confirmation status and a later untouched period must replace it.

## Projection baselines

### Projection Baseline 0 — frozen Current Talent carry-forward

At October 15, predict the next season with the player's frozen Baseline-2 Current Talent profile unchanged.

This is the required comparator.

It answers how much one-year future movement can already be handled by a strong present-talent estimate without any explicit aging/development model.

### Projection Baseline 1 — simple age/development adjustment

The first candidate adds only a training-derived expected one-year profile change based on variables available at the snapshot:

- age;
- current competitive level/environment;
- frozen Baseline-2 Current Talent profile;
- Current Talent evidence strength / uncertainty fields where needed for shrinkage.

The initial statistical form should remain transparent and low-dimensional. Preferred starting family:

- estimate expected one-year **change** in centered-log-ratio profile space;
- smooth/pool age effects rather than using unstable single-year cells;
- include current level/environment as a training-only development context;
- shrink sparse age/level adjustments toward a global age curve;
- no future level, future role, tracking metrics, scouting grades, or prospect rankings.

Exact smoothing/pooling constants are development choices and must be frozen before 2025 confirmation.

## Why model change rather than future raw level results directly

Frozen Current Talent already performs the hard work of:

- recency weighting;
- empirical-Bayes shrinkage;
- MLB-anchored environment translation;
- common MLB-through-Rookie profile representation.

Projection should therefore learn how that latent/common-scale state moves through time rather than rebuild the entire observation model from raw future statistics.

Future realized events remain the evaluation evidence, not the training target definition for Current Talent itself.

## Metrics

### Primary

- future-event multinomial log loss;
- future-event Brier score / component proper score.

### Required calibration

- calibration intercept/slope by major component where identifiable;
- reliability by predicted-probability band;
- no material deterioration versus carry-forward Baseline 0.

### Secondary scalar diagnostics

- MLB-equivalent expected-run-value MAE;
- RMSE;
- rank correlation;
- predicted-vs-observed decile calibration.

Do not promote a candidate because scalar correlation looks attractive if proper scores or calibration worsen.

## Required stratification

At minimum report:

- snapshot level: MLB / AAA / AA / High-A / Single-A / Rookie-complex / DSL where sample permits;
- future actual level;
- age bands;
- Current Talent evidence-volume bands;
- with/without prior MLB evidence;
- same-level / promoted / demoted / MLB-debut future opportunities;
- source capability tier where relevant;
- future-opportunity counts and censoring rates.

A universal candidate cannot hide a material lower-level failure inside an aggregate win.

## Development promotion rule

Projection Baseline 1 may advance to 2025 confirmation only if, over the three fixed development folds:

1. equal-fold mean log loss is lower than carry-forward Baseline 0;
2. equal-fold mean Brier is no worse and preferably lower;
3. log loss improves in at least 2 of 3 folds;
4. paired event coverage is identical;
5. no meaningful level stratum is materially worse on both proper scores in at least 2 folds;
6. calibration does not materially deteriorate;
7. no predictor or fitted parameter uses target-period evidence;
8. opportunity/censoring diagnostics show no obvious selection artifact that explains the aggregate win.

Before development scoring begins, convert "materially worse" and calibration tolerance into explicit numeric thresholds and persist them.

## Confirmation rule

If a candidate passes development:

1. keep the model form and selected hyperparameters unchanged;
2. refit only on the authorized pre-2025 development history;
3. persist the fitted coefficients/parameters and hashes before opening 2025 outcomes;
4. run one fixed 2025 confirmation;
5. require the same frozen promotion/transport/calibration gates;
6. if confirmation fails, do not tune on 2025.

## Multi-horizon extension

Do not begin by recursively rolling one-year predictions forward multiple times.

After one-year Projection v1 is stable, add direct horizon-specific targets/models for approximately 2-year and 3-year outcomes. Direct horizon models keep error propagation visible and allow aging/development effects to differ by horizon.

Playing-time/role probability should then be added as a separate projection channel rather than folded into the rate model.

## Implementation sequence and gate

1. **DONE:** implement deterministic Projection fold/window and next-year dataset contracts.
2. **DONE:** add/verify exact-game official outcome and league fallback behavior in fast CI.
3. **DONE:** isolate the 2024 aggregate discrepancy to two exact source-only residual rows via run `32092166134`.
4. **DONE:** implement the fail-closed residual quarantine and cross-grain propagation; fast CI passed (`32092505104`, `32092672387`, `32092714174`).
5. **IN FLIGHT:** quarantine-enabled full 2024 historical runs `32092672369` and `32092745178`.
6. **NEXT IF PASS:** accept the clean certified 2024 artifact and materialize/chronology-verify the complete 2022–2024 development snapshot/outcome surfaces with explicit opportunity/censoring accounting.
7. **THEN:** implement and score carry-forward Projection Baseline 0.
8. **THEN:** implement the simple age/development Baseline 1 and run the frozen three-fold development comparison.
9. **ONLY IF DEVELOPMENT PASSES:** freeze the confirmation refit/model-selection contract before opening any 2025 outcomes.

No 2025 outcome materialization belongs in the current implementation batch.
