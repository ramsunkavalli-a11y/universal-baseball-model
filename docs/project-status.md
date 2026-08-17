# Project status and handoff

Last updated: 2026-08-17

This is the **start-here file for a new chat, coding agent, or contributor**.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- Work in small verified batches; inspect current branch head before editing.
- Prefer certified/reusable public data + existing repo adapters over rebuilding raw-source cleanup.
- Fail closed on source ambiguity.
- Keep Performance, Current Talent, Projection, and Player Value / Overall Ranking separate.

## Current stage

Universal results-only **Current Talent Baseline 2 remains frozen**:

`translated_multiseason_recency_empirical_bayes_v1`

Richer Challenger 1 (`baseline2_plus_ev_sweet_spot_contact_residual_v1`) completed its fixed 2022 development gate and **failed**. It is closed.

Richer Challenger 2:

`baseline2_plus_ev_sweet_spot_contact_value_residual_v1`

has now **passed every frozen 2022 development gate**. The authorized 2021+2022 confirmation refit is also complete and frozen. The project is now preparing the **single fixed 2023 confirmation**. No Challenger-2 2023 performance score has been computed yet.

### Immediate task

Build the fixed 2023 confirmation source surfaces before any confirmation scoring:

1. reuse certified 2023 historical results evidence:
   - MiLB run `31971923778`
   - MLB run `31989561396`;
2. extend the already-certified richer tracking layer for confirmation chronology:
   - retain/carry 2021 tracking from run `32046012977`;
   - complete 2022 MiLB tracking beyond the development-only `2022-08-31` cutoff;
   - materialize 2023 MLB retained Savant tracking;
   - capture 2023 MiLB tracking through the latest required confirmation as-of date (`2023-09-01`, so pre-cutoff history through `2023-08-31`);
   - preserve exact `source_capability_tier` provenance and no imputation;
3. materialize 2023 contact-value target history with the already-frozen terminal mapper/value scale;
4. prove 2023 baseline `< cutoff`, future `[cutoff, cutoff+90d)`, feature chronology, identical paired coverage, and frozen confirmation coefficients;
5. then run exactly one confirmation on `2023-07-15`, `2023-08-01`, `2023-09-01`, with no search/reselection.

Do **not** tune the candidate after seeing 2023.

## Frozen Baseline 2

- 1,095-day eligible results history
- 180-day exponential half-life
- EB prior strength 100 effective core events
- training-only MLB-anchored level translation
- frozen age/current-level Baseline 0 prior
- frozen 12-component profile
- 90-day future target

B2 beat B1 on all six frozen 2022-development / 2023-confirmation folds for log loss and Brier.

Freeze: `docs/current-talent-results-only-baseline-freeze.md`

## Challenger 2 governing contract

Plan: `docs/current-talent-batted-ball-contact-value-challenger-plan.md`

Frozen features:

- 180-day recency-weighted mean EV
- 180-day recency-weighted sweet-spot share, LA 8–32° inclusive
- eligibility >=20 complete canonical tracked BBE
- tracking epoch `2021-01-01`
- no tracking imputation/search

Frozen conditional value gate:

- fixed nine-group MLB-scale terminal values
- additive control `terminal_value ~ contact_bin + level_group`
- references `IFFB` / `MLB`
- residual `beta_EV*z_EV + beta_SS*z_SS`, no intercept/no penalty
- primary MSE, MAE no-worse guard
- exact paired target coverage
- MiLB/capability-tier transport checks
- calibration guardrails

## Completed Challenger 2 gates

### 1. Terminal value scale — PASSED

Run `32056682313`, attempt 5. Retrosheet evidence strictly before `2021-07-15`.

Frozen values:

| Group | Value |
|---|---:|
| `1B` | 0.4651970407443663 |
| `2B` | 0.7665843002990237 |
| `3B` | 1.0004100521698496 |
| `HR` | 1.3834396983847337 |
| `ROE` | 0.43273757678346964 |
| `FC_REACH` | 0.1558534038205505 |
| `SF` | -0.06260868067734615 |
| `MULTI_OUT` | -0.8151401718384932 |
| `OUT` | -0.24975231369042597 |

### 2. Historical terminal semantics — PASSED

MiLB uses one terminal pitch per PA + conservative PA-result narrative fallback, reconciled to official structured semantics before freezing. Important distinctions: `force_out -> OUT`, `fielders_choice_out -> OUT`, plain `fielders_choice -> FC_REACH`. Exact duplicate release rows are harmless; substantive conflicts fail closed.

### 3. 2021–22 MiLB target materialization — PASSED

Run `32070152452`:

- 901,015 terminal core contacts
- 900,742 supported targets (99.9697%)
- 273 explicit exclusions
- all 10 season/level slices passed

### 4. 2021–22 MLB target materialization — PASSED

Run `32074097045`:

- 236,599 core contacts
- 236,596 supported
- only 3 explicit 2021 exclusions

### 5. Combined chronology — PASSED

Run `32074805618`:

- 1,137,338 valued 2021–22 contacts
- zero duplicate target keys
- all 10 bins / all 6 levels
- all 60 bin×level baseline cells
- exact half-open chronology

### 6. Additive baseline — PASSED

Run `32075112279`. All four fits are 60-cell / 15-parameter / full-rank / cutoff-safe. Sufficient-statistics implementation is coefficient-equivalent to the original event-wise OLS.

### 7. Richer feature/provenance attachment — PASSED

Run `32075892988`.

2021-only development standardization:

- 649 eligible players
- EV mean 88.09960095932205; scale 2.887465116853261
- sweet-spot mean 0.3470054876008983; scale 0.06391355546209573

Paired target contacts:

- 2021-07-15: 69,382 / 621 players
- 2022-07-15: 97,004 / 976
- 2022-08-01: 77,859 / 957
- 2022-09-01: 37,629 / 933

Any-observed-MiLB paired contacts in 2022: 49,247 / 39,401 / 18,400.

### 8. Frozen 2021 residual fit — PASSED

Persisted result: `docs/current-talent-contact-value-residual-fit-result.json`

- 69,382 contacts / 621 players
- beta EV = `0.020808202510874292`
- beta sweet-spot = `-0.0032619728296970248`
- determinant = `3906075044.1483107`
- 2022 outcomes not accessed

### 9. Prediction geometry — PASSED

Persisted result: `docs/current-talent-contact-value-prediction-geometry-result.json`

- 2022 paired counts unchanged: 97,004 / 77,859 / 37,629
- comparator/richer keys identical
- finite predictions
- no MSE/MAE/calibration
- no coefficient refit
- no 2023

### 10. Fixed 2022 development — PASSED ALL GATES

Persisted result: `docs/current-talent-contact-value-development-result.json`

Equal-fold means:

- baseline MSE `0.19983482558337698`
- richer MSE `0.19947804003888056`
- delta `-0.00035678554449641853`
- baseline MAE `0.35317026840563903`
- richer MAE `0.3528114760321568`
- delta `-0.0003587923734822418`
- richer MSE wins **3/3**

Any-observed-MiLB:

- 107,048 total fold contacts
- baseline mean MSE `0.2017534561593921`
- richer mean MSE `0.20141942641402558`
- delta `-0.00033402974536653196`

Calibration mean absolute errors also improved:

- intercept: baseline `0.009059769936977567`, richer `0.008572858096503674`
- slope: baseline `0.0037337420889670034`, richer `0.003119243058711215`

All exact non-MLB capability-tier guardrails passed. `eligible_for_fixed_2023_confirmation = true`.

### 11. Authorized confirmation refit — PASSED / FROZEN

Persisted result: `docs/current-talent-contact-value-confirmation-refit-result.json`

Training snapshots: `2021-07-15` + `2022-07-15` only.

Pooled confirmation standardization:

- 1,718 eligible player-snapshot rows
- EV mean `89.14153098440633`
- EV scale `2.7378059749661574`
- sweet-spot mean `0.3441350187274813`
- sweet-spot scale `0.06085059101688322`

Frozen confirmation residual fit:

- beta EV `0.019444323416633432`
- beta sweet-spot `-0.0016659093644997295`
- determinant `24131877108.23486`
- 166,386 future-contact weight
- 1,597 fitted player-snapshots

No 2023 evidence was accessed during refit.

## Reusable 2023 infrastructure

Existing results-only confirmation workflow proves certified 2023 historical source artifacts already exist:

- MiLB run `31971923778`
- MLB run `31989561396`

The richer V2 tracking run `32046012977` is authoritative for 2021–22 development tracking, but its MiLB 2022 capture stops at `2022-08-31`. Therefore confirmation tracking must extend 2022 chronology and add 2023 tracking rather than pretending the development artifact is sufficient.

## Governing docs for a new chat

Read in this order:

1. `docs/project-status.md`
2. `docs/current-talent-batted-ball-contact-value-challenger-plan.md`
3. `docs/current-talent-contact-value-development-result.json`
4. `docs/current-talent-contact-value-confirmation-refit-result.json`
5. `docs/current-talent-contact-value-prediction-geometry-result.json`
6. `docs/current-talent-contact-value-residual-fit-result.json`
7. `docs/current-talent-contact-value-feature-attachment-checkpoint.md`
8. `docs/current-talent-contact-value-baseline-fit-checkpoint.md`
9. `docs/current-talent-contact-value-chronology-checkpoint.md`
10. `docs/current-talent-contact-value-source-materialization-checkpoint.md`
11. `docs/current-talent-contact-value-mlb-source-checkpoint.md`
12. `docs/current-talent-results-only-baseline-freeze.md`

Do not redo B1/B2 selection, Challenger-1 development, Challenger-2 2022 selection, or confirmation refit absent a concrete implementation failure. The next confirmation is fixed and one-shot; no 2023 tuning/reselection.
