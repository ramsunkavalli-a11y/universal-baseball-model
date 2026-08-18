# Batting Projection v1 Plan

Last updated: 2026-08-17 19:34 PT

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
- combined fast-CI validation of those fallback contracts.

Recent passing runs: `32089050302`, `32089669934`, `32090401492`, `32090635490`, and `32090687671`.

The remaining blocker is the heavy 2024 MiLB historical-evidence reuse/materialization path. Historical-path runs `32089284674`, `32090307461`, `32090635458`, and `32090668312` failed.

A dedicated source-gap audit initially pursued exact official game feeds. Recovery run `32091704947` demonstrated that `game_pk 755829` returns **404 Not Found** from `https://statsapi.mlb.com/api/v1/game/755829/feed/live`, so that official PBP path cannot adjudicate the row directly.

Follow-up source-only residual audit `32092166134` then **passed** and narrowed the observed 2024 aggregate discrepancy to exactly two deterministic source-only rows:

- High-A player `669233`, game `755829`: `PA=1, AB=1`, with no BB/HBP/SO/SF/SH/CI.
- Single-A player `686541`, game `754395`: `PA=1, AB=1, SO=1`, with no BB/HBP/SF/SH/CI.

For both rows:

- the season aggregate mismatches before removal;
- the mismatch disappears after removing that exact row;
- post-removal totals match the official gameLog control;
- the audit classifies the row as an **exact removable residual**.

Audit artifact `9308734004`; digest `sha256:574f6f7bd6eb0278ea3a654cb97762ce7fbed07c912e32261f2da5883435a466`.

The current task is therefore no longer open-ended source hunting. It is to encode those two exact residuals as explicit provenance-preserving source-quality exclusions, test the rule, and rerun the complete 2024 historical evidence path. It is **not** time to fit the age curve or score Projection candidates.

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
3. **DONE:** isolate the current 2024 aggregate discrepancy to two exact source-only residual rows via run `32092166134`.
4. **CURRENT:** encode those two exclusions with explicit provenance + deterministic regression coverage, then rerun the full 2024 MiLB historical evidence path.
5. **NEXT:** require a clean certified 2024 artifact and materialize/chronology-verify the complete 2022–2024 development snapshot/outcome surfaces with explicit opportunity/censoring accounting.
6. **THEN:** implement and score carry-forward Projection Baseline 0.
7. **THEN:** implement the simple age/development Baseline 1 and run the frozen three-fold development comparison.
8. **ONLY IF DEVELOPMENT PASSES:** freeze the confirmation refit/model-selection contract before opening any 2025 outcomes.

No 2025 outcome materialization belongs in the current implementation batch.
