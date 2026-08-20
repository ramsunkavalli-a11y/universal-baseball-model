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
- the certified MLB Stats API pooled player grain is the membership authority: **651 positive-PA players and 182,449 PA**;
- membership must reconcile to the official/certified 2024 MLB hitting population used by the existing Player Value reference infrastructure;
- the historical Playing Time 2024 validation surface is an exposure source for its frozen eligible 2023-10-15 B2 snapshot population, not the authority for official 2024 MLB membership or realized PA accounting;
- players may not be dropped because an upstream component uses a neutral/fallback path. The frozen universal fallback is part of the component definition.

The frozen Playing Time 2024 validation surface contains 3,985 eligible 2023-10-15 B2 snapshot players. An official 2024 positive-PA MLB member who is outside that frozen snapshot has no chronology-safe Playing Time model row. For such a member, the binding centering fallback is:

- retain the player in the 651-player official reference cohort;
- set `projected_expected_mlb_pa = 0.0` for the reference exposure surface;
- mark the row as an explicit outside-snapshot zero-exposure fallback;
- do not use realized 2024 PA, future roster information, a manual forecast, or a newly refit Playing Time model to fill the missing exposure.

This fallback is structural, not player-specific: it applies to any official reference member absent from the frozen eligible Playing Time snapshot. It keeps membership complete while preserving the chronology and eligibility rules of the already-frozen Playing Time model.

This fixed MLB cohort is a calibration reference only. **Never** derive the centering constant from whichever MLB/MiLB/prospect rows happen to be loaded for a universal ranking run.

## Frozen historical component surface

For every reference player, assemble the 2024 historical projection surface using the already-frozen v1 methods and their historical inputs. Reuse the existing historical predictor/reference artifacts; do not refit a ranking-specific population.

Required row fields are:

- `projected_expected_mlb_pa` from the frozen Playing Time form `playing_time_recent_opportunity_40man_b2_hurdle_v1`, with the explicit zero-exposure fallback above for official members outside the frozen eligible snapshot;
- `Rbat` from the frozen batting Projection form `frozen_current_talent_carry_forward_v1` and the existing pooled MLB batting run conversion;
- `Rbr` from `B2_k5` steal attempts, `B2_k45` steal success, `A2_k25` non-steal advancement, and the frozen baserunning run conversion;
- `Rdef` from the frozen Defense v1 skill/exposure hierarchy and native run conversion;
- `Rpos` from the frozen FanGraphs positional schedule and frozen non-DH/DH exposure rules.

The historical surface must preserve the as-of discipline of each frozen predictor. Realized 2024 membership is allowed only to define the fixed MLB reference cohort. Do not use realized 2024 component outcomes to replace projected component values.

Environment constants that are explicitly defined as the certified 2024 MLB reference environment may be used where the frozen Player Value contracts require a reference environment; they are not talent-model refits.

For an official reference member with zero projected PA under the outside-snapshot fallback, PA-scaled offensive/replacement/centering terms are zero by construction. Any other component lacking an authorized historical projection row must use that component's already-frozen neutral/fallback path; do not infer a realized 2024 value.

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

1. reference membership is unique by player and reconciles to the fixed 651-player 2024 MLB positive-PA cohort;
2. official pooled MLB PA reconciles to 182,449;
3. every reference row has finite, nonnegative projected MLB PA, with outside-snapshot zero exposure explicit and enumerated;
4. every included component is finite;
5. no reference player is dropped for missing/fallback component evidence;
6. aggregate projected reference PA is positive;
7. the persisted raw total equals the sum of the four persisted component totals;
8. `aggregate_Rlg = PA_ref * centering_runs_per_pa`;
9. `Ravg_raw_ref + aggregate_Rlg` is zero within absolute tolerance `1e-10` runs;
10. replacement, park, and WAR fields are absent from the centering calculation path.

## Required materialization

Persist `docs/player-value-v1-mlb-centering-2024.json` with at least:

- schema/status/centering identifiers;
- reference season and membership definition;
- reference player count;
- aggregate official MLB PA membership anchor;
- aggregate projected MLB PA;
- outside-snapshot zero-exposure player IDs/count;
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
