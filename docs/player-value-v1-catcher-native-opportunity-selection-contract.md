# Player Value v1 — catcher native-opportunity forecast selection contract

Last updated: 2026-08-19

Status: **PREDECLARED BINDING V1 CATCHER-OPPORTUNITY SELECTION; PRE-2025 DEVELOPMENT ONLY.**

## Purpose

Freeze the forward opportunity counts required by the already-frozen catcher run conversions:
- throwing: stolen-base throw opportunities / Savant `sb_attempts`;
- blocking: Savant blocking `pitches`;
- framing: Savant framing `pitches`.

This gate does not refit Defense skill, Playing Time, Position/Role, or the run-rate constants.

## Evidence and folds

Use exactly:
1. 2022 inputs -> 2023 observed native opportunities;
2. 2023 inputs -> 2024 observed native opportunities.

No 2025 data may be queried or opened.

Reuse the exact frozen Playing Time development artifacts already used by the general defensive
exposure gate:
- selection run `32141616127`, artifact `playing-time-v1-candidate-selection`;
- 2023 validation run `32141934868`, artifact `playing-time-v1-validation-2023`;
- 2024 validation run `32142089669`, artifact `playing-time-v1-validation-2024`.

Use the repaired direct Baseball Savant year-specific catcher source semantics frozen upstream.

## Scoring population

Score only source-year players eligible for the corresponding frozen skill/opportunity channel:
- throwing: source-year `sb_attempts >= 10`;
- blocking: source-year blocking `pitches >= 500`;
- framing: source-year framing `pitches >= 1000`.

The player must be present in the exact frozen Playing Time fold population.

Target-year missing native opportunity is observed as zero, so exits remain in the score.
Do not add source-year non-eligible entrants merely to improve entry forecasting: those players do
not have a non-neutral frozen component skill requiring this opportunity forecast.

## Candidate forms

For each component independently:

### B0 — raw opportunity persistence

`B0 = prior_native_opportunity`.

### P1 — frozen Playing Time ratio scaling

If source-year MLB PA > 0:

`P1 = prior_native_opportunity * predicted_expected_mlb_pa / source_year_mlb_pa`.

If source-year MLB PA is zero or nonpositive, fail safely to B0 for that player and report it.

No cap, floor, tuned exponent, or component-specific coefficient is allowed.

### H1 — fixed 50/50 hybrid

`H1 = 0.5 * B0 + 0.5 * P1`.

The 0.5 weight is fixed before results are opened and may not be changed afterward.

## Metrics

For each component, fold, and candidate report:
- overall MAE and RMSE;
- observed and predicted mean opportunity;
- continuing-player MAE/RMSE (`target opportunity > 0`);
- exit-player MAE/RMSE (`target opportunity = 0`);
- P1 zero-PA fallback count.

Report equal-fold mean overall MAE and RMSE.

## Binding selection rule

B0 is retained for a component unless P1 or H1 satisfies all of:

1. fold-specific overall MAE is no more than 2% worse than B0 in both folds;
2. equal-fold mean overall MAE is strictly lower than B0;
3. equal-fold mean overall RMSE is strictly lower than B0; and
4. continuing-player MAE is no more than 2% worse than B0 in both folds.

If both challengers pass, select the one with lower equal-fold mean overall MAE. If tied within
`1e-9`, select P1 because it is the simpler direct use of the already-frozen Playing Time forecast.

The selection is independent by component. Do not force throwing, blocking, and framing to use the
same form.

## Required frozen output

Persist:
- selected form by catcher component;
- exact upstream run/artifact provenance;
- fold population and fallback diagnostics;
- all candidate metrics and gate outcomes;
- formula for the selected future opportunity;
- explicit boundaries.

## Boundaries

- No 2025 data.
- No Defense refit/rescore.
- No Playing Time or Position/Role refit.
- Frozen Defense run-rate constants remain unchanged.
- General defensive exposure remains unchanged.
- No positional adjustment.
- No replacement level, runs per win, WAR/value, or final ranking.
