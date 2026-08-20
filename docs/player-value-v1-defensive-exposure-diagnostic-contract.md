# Player Value v1 — defensive exposure diagnostic contract

Last updated: 2026-08-19

Status: **PREDECLARED DEVELOPMENT DIAGNOSTIC; NOT A PRODUCTION FREEZE.**

This contract defines the first forward **total MLB defensive-outs** bridge diagnostic under
`docs/player-value-v1-defense-exposure-contract.md`. It does not alter frozen Playing Time,
Position/Role, or Defense models and does not authorize run conversion, positional adjustment,
replacement level, runs per win, or WAR.

## Scope

The target is next-season MLB position-player defensive exposure measured as official
`fielding_outs`, summed over:

`C, 1B, 2B, 3B, SS, LF, CF, RF`.

DH and P are excluded from the target.

Development folds:

1. 2022 inputs -> 2023 MLB defensive outs;
2. 2023 inputs -> 2024 MLB defensive outs.

No 2025 data may be accessed by this diagnostic. These folds are development evidence for the
new exposure-mapping question; the result must not be described as an untouched confirmation.

The scored population for each fold is the exact frozen Playing Time v1 validation population.
Players with no target-year MLB fielding row receive observed defensive outs = 0. Players with no
source-year MLB fielding row receive prior defensive outs = 0.

## Frozen upstream inputs

For each fold, consume without refitting:

- frozen Playing Time v1 `predicted_expected_mlb_pa`;
- frozen as-of `current_season_mlb_pa` from the immutable Playing Time selection predictors;
- certified historical official fielding usage from run `32148467330`, artifact
  `position-role-historical-source-2021-2024`.

No Position/Role forecast is used in this first total-outs diagnostic. Position allocation is a
separate later gate.

## Candidate forms

### B0 — raw persistence

`predicted_defensive_outs = prior_season_mlb_defensive_outs`

This is the required simple persistence baseline.

### P1 — projected-PA global scale

For each source season, calculate one deterministic contemporaneous scale on the exact scored
population:

`source_outs_per_pa = sum(prior_season_mlb_defensive_outs) / sum(current_season_mlb_pa)`

Then:

`predicted_defensive_outs = predicted_expected_mlb_pa * source_outs_per_pa`

No fitted regression, player-specific ratio, cap, winsorization, or tuned threshold is allowed.

### H1 — fixed 50/50 hybrid

`predicted_defensive_outs = 0.5 * B0 + 0.5 * P1`

The 0.5 weight is fixed before scoring. It may not be changed after results are opened.

## Metrics

For each fold and form report:

- MAE;
- RMSE;
- observed and predicted mean defensive outs;
- MAE among target-year positive defenders;
- MAE among incumbents (`prior_outs > 0`);
- MAE among entrants (`prior_outs == 0 and target_outs > 0`);
- MAE among exits (`prior_outs > 0 and target_outs == 0`);
- row counts for each subgroup.

Also report equal-fold means for MAE and RMSE.

## Recommendation rule

B0 is retained unless P1 or H1 satisfies all of:

1. fold-specific overall MAE is no more than 2% worse than B0 in both 2023 and 2024;
2. equal-fold mean overall MAE is strictly lower than B0;
3. equal-fold mean overall RMSE is strictly lower than B0;
4. entrant MAE is strictly lower than B0 in both folds when each fold has entrants.

If both challengers pass, recommend the one with the lower equal-fold mean overall MAE.
If equal within `1e-9`, prefer P1 over H1 because P1 is simpler.

A recommendation from this diagnostic is **not yet the full production exposure bridge**.
Position allocation and any component-native opportunity denominators remain open and must be
handled under separate gates.

## Required output and boundaries

Persist a binding diagnostic result containing:

- source run IDs/artifact names;
- contract SHA-256;
- fold/candidate metrics;
- recommendation rule outcomes;
- recommended total-outs form;
- explicit boundary flags.

Boundary flags must confirm:

- 2025 accessed = false;
- Playing Time refit = false;
- Position/Role refit = false;
- Defense refit = false;
- position allocation selected = false;
- run conversion performed = false;
- positional adjustment calculated = false;
- WAR/value calculated = false.
