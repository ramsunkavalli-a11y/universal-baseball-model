# Player Value v1 — fixed-reference MLB centering contract

Last updated: 2026-08-19

Status: **PREDECLARED / ACTIVE.** The centering formula and reference-population semantics are frozen here before the numerical constant is materialized. The constant is not binding until the reference assembly passes the mechanical checks below.

## Purpose

Add one explicit league-average balancing layer after the frozen above-average components. This prevents independent batting, baserunning, Defense, and positional constructions from being assumed to sum to exactly zero.

This layer may not alter any upstream skill, exposure, run-conversion, positional, replacement, or runs-per-win decision.

## Fixed reference season and population

The binding v1 reference season is **2024**.

Reference membership is the fixed 2024 MLB hitter population:

- one row per player with positive official MLB plate appearances in 2024;
- pooled AL/NL rather than separately centered leagues;
- membership must reconcile to the official/certified 2024 MLB hitting population used by the existing Player Value reference infrastructure;
- the historical Playing Time 2024 validation target may be used to identify the same positive-MLB-PA cohort, but realized 2024 PA or other realized 2024 outcomes may not be substituted for frozen projected component exposure;
- players may not be dropped because an upstream component uses a neutral/fallback path. The frozen universal fallback is part of the component definition.

This fixed MLB cohort is a calibration reference only. **Never** derive the centering constant from whichever MLB/MiLB/prospect rows happen to be loaded for a universal ranking run.

## Frozen historical component surface

For every reference player, assemble the 2024 historical projection surface using the already-frozen v1 methods and their historical inputs. Reuse the existing historical predictor/reference artifacts; do not refit a ranking-specific population.

Required row fields are:

- `projected_expected_mlb_pa` from the frozen Playing Time form `playing_time_recent_opportunity_40man_b2_hurdle_v1`;
- `Rbat` from the frozen batting Projection form `frozen_current_talent_carry_forward_v1` and the existing pooled MLB batting run conversion;
- `Rbr` from `B2_k5` steal attempts, `B2_k45` steal success, `A2_k25` non-steal advancement, and the frozen baserunning run conversion;
- `Rdef` from the frozen Defense v1 skill/exposure hierarchy and native run conversion;
- `Rpos` from the frozen FanGraphs positional schedule and frozen non-DH/DH exposure rules.

The historical surface must preserve the as-of discipline of each frozen predictor. Realized 2024 membership is allowed only to define the fixed MLB reference cohort. Do not use realized 2024 component outcomes to replace projected component values.

Environment constants that are explicitly defined as the certified 2024 MLB reference environment may be used where the frozen Player Value contracts require a reference environment; they are not talent-model refits.

## Binding centering formula

For reference player `j`:

`Ravg_raw_j = Rbat_j + Rbr_j + Rdef_j + Rpos_j`

GIDP is omitted for v1 and therefore contributes exactly zero.

Aggregate only over the fixed reference cohort:

`Ravg_raw_ref = sum_j Ravg_raw_j`

`PA_ref = sum_j projected_expected_mlb_pa_j`

Then:

`centering_runs_per_pa = -Ravg_raw_ref / PA_ref`

For any production player `i`:

`Rlg_i = projected_expected_mlb_pa_i * centering_runs_per_pa`

The denominator is the **same frozen projected-PA exposure used by the reference component surface**, not observed 2024 PA and not the total PA of a loaded ranking population.

## Explicit exclusions

The centering total contains exactly four terms: `Rbat`, `Rbr`, `Rdef`, and `Rpos`.

Do not include:

- replacement runs;
- runs per win;
- any park adjustment;
- WAR/RAR;
- a raw GIDP term;
- any post-hoc ranking/population normalization.

Replacement remains a separate below-average baseline. Park neutrality is the next independent gate.

## Mechanical verification required before freeze

The materializer must fail rather than publish a constant unless all of the following hold:

1. reference membership is unique by player and reconciles to the fixed 2024 MLB positive-PA cohort;
2. every reference row has finite, nonnegative projected MLB PA;
3. every included component is finite;
4. no reference player is dropped for missing/fallback component evidence;
5. aggregate projected reference PA is positive;
6. the persisted raw total equals the sum of the four persisted component totals;
7. `aggregate_Rlg = PA_ref * centering_runs_per_pa`;
8. `Ravg_raw_ref + aggregate_Rlg` is zero within absolute tolerance `1e-10` runs;
9. replacement, park, and WAR fields are absent from the centering calculation path.

## Required materialization

Persist `docs/player-value-v1-mlb-centering-2024.json` with at least:

- schema/status/centering identifiers;
- reference season and membership definition;
- reference player count;
- aggregate projected MLB PA;
- aggregate `Rbat`, `Rbr`, `Rdef`, and `Rpos`;
- aggregate raw above-average runs;
- `centering_runs_per_pa`;
- aggregate `Rlg`;
- post-centering residual;
- exact upstream artifact/run/digest provenance used for each component/reference surface;
- verification flags and tolerance;
- source commit/run for the materialization.

The JSON result, not a number copied into prose, is the binding numerical record.

## Sensitivity

Before final WAR freeze, report at least one non-binding centering sensitivity using an alternate recent certified MLB reference season if the full comparable historical component surface is available. Do not manufacture a partial alternate season solely to satisfy this sensitivity.

## Boundary

After the 2024 reference assembly is materialized and mechanically verified, this centering gate may be marked **DONE / FROZEN / VERIFIED** and the park-neutrality audit becomes active.

Until then:

- park correction remains closed;
- WAR/value aggregation remains closed;
- final rankings remain closed.
