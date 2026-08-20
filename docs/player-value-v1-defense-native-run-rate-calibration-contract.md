# Player Value v1 — Defense native run-rate calibration diagnostic contract

Last updated: 2026-08-19

Status: **PRE-2025 CALIBRATION DIAGNOSTIC ONLY; NO PRODUCTION RUN SCALE FROZEN.**

## Purpose

Measure whether each frozen standardized Defense target has a stable, interpretable mapping to
the public Baseball Savant seasonal run-valued field per native opportunity.

This uses the architecture's authorized path of calibration to an independently defined public
run-valued defensive target. It does not refit Defense skill and does not use 2025 confirmation
residuals.

## Evidence

Use only target seasons 2022, 2023, and 2024.

General range:
- target: Savant `diff_success_rate_formatted`, standardized exactly within target year x position;
- public seasonal run target: Savant `fielding_runs_prevented`;
- opportunity basis for this diagnostic: certified official target-year MLB `fielding_outs` at
  the matching defensive position.

Catcher throwing:
- repaired target: Savant `cs_aa_per_throw`, standardized exactly within target year;
- public seasonal run target: `catcher_stealing_runs`;
- native opportunity: `sb_attempts`.

Catcher blocking:
- repaired target: Savant `blocks_above_average_per_game`, standardized exactly within target year;
- public seasonal run target: `catcher_blocking_runs`;
- test `n_pbwp` and `pitches` as candidate native opportunity fields;
- separately test whether `blocks_above_average_per_game * n_pbwp / 40` reconstructs
  `blocks_above_average`. If that identity fails materially, do not treat `n_pbwp` as the native
  opportunity basis.

Catcher framing:
- repaired target: `1000 * rv_tot / pitches`, standardized exactly within target year;
- public seasonal run target: `rv_tot`;
- native opportunity: `pitches`.

## Calibration form

For a component/year (and for general range, position/year), define:

`x = target_z * opportunity`

and fit exactly one through-origin scalar:

`public_run_total = slope * x + residual`.

The intercept is fixed at zero. This is required by Player Value neutral-fallback semantics:
standardized neutral skill (`z = 0`) must produce zero modeled run adjustment.

The diagnostic must report:
- row count;
- through-origin slope;
- seasonal-run MAE and RMSE;
- public-run target mean/SD;
- opportunity mean/median;
- target-z x opportunity scale diagnostics.

Then report across-year slope stability:
- median slope;
- mean slope;
- population SD;
- coefficient of variation where defined;
- max/min ratio where all slopes are positive.

For general range report this separately for 1B, 2B, 3B, SS, LF, CF, RF and also diagnostic
IF/OF pooled groups.

## Public-method identities

Record the current public Statcast conversion constants as external methodology evidence:
- infield OAA range: 0.75 runs per out;
- outfield OAA range: 0.90 runs per out;
- catcher throwing: 0.65 runs per stolen base prevented / caught stealing above average;
- catcher blocking: 0.25 runs per block saved;
- catcher framing source `rv_tot` is already a run-valued seasonal total.

Where returned historical source fields permit it, verify:
- `catcher_stealing_runs ~= 0.65 * caught_stealing_above_average`;
- `catcher_blocking_runs ~= 0.25 * blocks_above_average`;
- `blocks_above_average ~= blocks_above_average_per_game * n_pbwp / 40`.

Identity checks are diagnostics and may reflect source rounding.

## No selection in this gate

This gate does not choose:
- pooled versus median versus grouped conversion scales;
- a future catcher-opportunity forecast;
- a future standardization mean/SD;
- positional adjustment;
- replacement level;
- runs per win;
- WAR/value.

A production conversion may be predeclared only after the stability and identity diagnostics are
read.

## Binding boundaries

- No 2025 data.
- No Defense refit/rescore.
- No Playing Time or Position/Role refit.
- No tuning to 2025 confirmation residuals.
- No arbitrary universal runs-per-z constant.
- No positional adjustment or WAR/value.
