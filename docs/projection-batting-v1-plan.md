# Batting Projection v1 Plan

Last updated: 2026-08-17 21:35 PT

Status: **COMPLETE — CARRY-FORWARD B2 RETAINED; EXPLICIT AGE/DEVELOPMENT CHALLENGER REJECTED**

## Purpose

Projection is the layer after frozen Current Talent.

It answers:

> Given a player's estimated present batting talent at an as-of date, how should that rate/profile ability be expected to change over future time?

Projection v1 is rate/profile only. Playing time/role remains a separate channel.

## Binding result

Retain:

`frozen_current_talent_carry_forward_v1`

as the one-year batting-rate Projection v1 model.

The pre-registered explicit age/development challenger:

`projection_age_level_ilr_ridge_v1`, lambda `0.01`

was selected on 2022-only held-out CV and passed the first 2023 out-of-time fold, but reversed against carry-forward B2 on the second 2024 out-of-time fold.

Because the frozen promotion rule required lower log loss in **both** validation folds, the challenger is rejected without rescue tuning.

Binding machine-readable result:

- `docs/projection-batting-v1-development-result.json`

Human checkpoint:

- `docs/projection-batting-v1-development-checkpoint.md`

## Starting state

Projection v1 begins from frozen Current Talent Baseline 2:

`translated_multiseason_recency_empirical_bayes_v1`

Frozen B2 already provides:

- recency weighting;
- multi-season certified history where available;
- MLB-anchored environment translation;
- empirical-Bayes shrinkage;
- age/current-level population prior;
- common 12-component batting profile.

The B2 1,095-day history value is a maximum cap. The certified universal source epoch begins in 2021; no pre-2021 backfill was introduced for Projection reproduction.

## Snapshot / target semantics

Primary snapshot date: **October 15**.

For snapshot year `Y`, the target is all eligible regular-season batting events in calendar year `Y+1`.

Authorized pre-confirmation folds:

1. `2021-10-15 -> 2022` — candidate-selection fold;
2. `2022-10-15 -> 2023` — out-of-time validation 1;
3. `2023-10-15 -> 2024` — out-of-time validation 2.

Untouched period:

4. `2024-10-15 -> 2025` — never opened for this challenger.

## Methodology review / pre-registration

Before scoring, the project reviewed academic and public practitioner work including hierarchical baseball aging/projection, MARCEL, OOPSY, KATOH, Davenport, ZiPS/PECOTA/Steamer traditions, ATC/THE BAT X, Chamberlain, Ben-Porat, Max Bay, Cameron Grove, and compositional/longitudinal methods outside baseball.

Governing review:

- `docs/projection-v1-methodology-review.md`

Binding candidate/search/promotion contract:

- `docs/projection-batting-v1-development-contract.md`

Key design choices:

- model movement around frozen B2 rather than rebuild player skill;
- represent the 12-part batting profile in a fixed 11-D ILR basis;
- smooth continuous piecewise-linear population age function;
- optionally add as-of-level main effects, but no age × level interactions;
- future opportunity remains separate from rate skill;
- only 2022 outcomes may choose candidate form/lambda;
- 2023/2024 are fixed rolling-origin validation;
- no tracking, scouting, comparables, future level, future role, or playing-time features in v1.

## Selected challenger and results

### 2022 candidate selection

Selected from exactly two forms × four lambdas using deterministic five-fold player-held-out CV:

- form: `projection_age_level_ilr_ridge_v1`;
- lambda: `0.01`;
- log-loss delta vs carry-forward B2: **-0.001507130**;
- Brier delta: **-0.000294739**.

Binding selection record:

- `docs/projection-batting-v1-selection-result.json`

### 2023 validation

Fit on all authorized 2022-response rows, with no reselection:

- candidate log loss: `2.253775007`;
- B2 carry-forward log loss: `2.254254788`;
- delta: **-0.000479781**;
- Brier delta: **-0.000000686**.

Result:

- `docs/projection-batting-v1-validation-2023-result.json`

### 2024 validation

Same form/lambda, rolling-origin refit on authorized 2022 + 2023 training observations:

- candidate log loss: `2.256561150`;
- B2 carry-forward log loss: `2.256304269`;
- delta: **+0.000256881**;
- Brier delta: **+0.000156946**.

The binding primary gate fails here.

Result:

- `docs/projection-batting-v1-validation-2024-result.json`

## Interpretation

The selected age/level adjustment showed some predictive signal in 2022 and 2023 but did not transport robustly to 2024.

This does not imply literal zero aging/development. It means the tested universal low-dimensional adjustment does not improve sufficiently and consistently beyond a strong frozen Current Talent estimate to justify production promotion.

The project therefore does not force an aging adjustment simply because conventional projection systems usually include one.

## 2025 boundary

**2025 outcomes were never accessed.**

No 2025 confirmation is authorized for the rejected challenger. Preserve that untouched period for a future separately designed Projection challenger if useful.

Do not tune or rescue this v1 challenger using 2024 or 2025.

## Future Projection challengers

Possible future work could test separately pre-registered:

- hierarchical/comparable-player aging;
- richer process/tracking features with proven incremental predictive value;
- direct 2-year / 3-year horizon models;
- ensembles of genuinely independent validated projection systems.

These are not part of the current ranking-system path and must not reopen the failed v1 candidate opportunistically.

## Next stage

Projection v1 rate/profile is complete for the current build.

Proceed to **playing time / role**, keeping opportunity separate from batting-rate skill.
