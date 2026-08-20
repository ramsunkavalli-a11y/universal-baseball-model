# Player Value v1 batting projected-runs contract

Last updated: 2026-08-19

## Status

**FROZEN.** Player Value v1 batting runs reuse the certified batting Performance RE24/bin-value infrastructure and the frozen batting Projection composition. No second batting run-value model is fit.

## Frozen upstream inputs

Player Value v1 consumes, without refitting:

1. frozen Projection v1 batting composition: `frozen_current_talent_carry_forward_v1`;
2. frozen Playing Time v1 expected MLB plate appearances;
3. certified MLB batting Performance summary/profile/bin-value surfaces under `batting_performance_v1`;
4. the existing 12 mutually exclusive core bins from `ALL_CORE_BINS`.

The Projection probabilities are a simplex **conditional on a core event**. They are not PA shares. Performance separately preserves the fraction of PA covered by the core taxonomy.

## MLB reference environment

For a Player Value snapshot, use the **latest certified MLB Performance materialization available to that snapshot**. It must contain both MLB league IDs `103` and `104`, and only evidence available by the Player Value as-of boundary may be used.

Pool AL/NL into one MLB reference as follows.

For league `l` and core bin `b`:

- `N[l,b]` = aggregate certified Performance `occurrence_count`;
- `V[l,b]` = certified Performance `estimated_mean_run_value`.

Then:

`N[b] = sum_l N[l,b]`

`V_mlb[b] = sum_l(N[l,b] * V[l,b]) / N[b]`

`N_core = sum_b N[b]`

`PA_mlb = aggregate certified MLB batting_plate_appearances`

`coverage_mlb = N_core / PA_mlb`

`P_ref[b] = N[b] / N_core`

`RV_ref_core = sum_b(P_ref[b] * V_mlb[b])`

The pooled reference must reconcile exactly: aggregate profile core events must equal aggregate summary `core_profile_event_count`. All bin values used by the reference must be certified.

## Why MLB coverage is fixed across players

The frozen batting Projection models the conditional 12-bin core composition, not a separate future core-event/PA process. The uncovered PA bucket includes taxonomy exclusions and source/accounting coverage diagnostics as well as rare event classes. A player-specific carry-forward of `core_events / PA` would therefore allow source coverage and excluded-event mix to alter projected batting value without a validated talent model.

Player Value v1 instead uses the single pooled MLB `coverage_mlb` for every projected hitter. This places every player in the same MLB opportunity/reporting environment and leaves only the frozen projected core composition to differentiate batting skill.

No extra core-event-rate selection gate is authorized for v1.

## Player projected batting runs

For player `i`:

- `P_i[b]` = frozen Projection probability for bin `b`;
- `PA_i` = frozen Playing Time v1 expected MLB PA;
- `V_mlb[b]`, `coverage_mlb`, and `RV_ref_core` are the pooled MLB reference above.

First compute projected value per core event:

`RV_i_core = sum_b(P_i[b] * V_mlb[b])`

Then batting runs above the pooled MLB reference are:

`Rbat_i = PA_i * coverage_mlb * (RV_i_core - RV_ref_core)`

Equivalent per-PA form:

`Rbat_i = PA_i * (coverage_mlb * RV_i_core - coverage_mlb * RV_ref_core)`

Properties that are binding:

- a player with the MLB reference core composition receives exactly zero batting runs above reference;
- zero projected MLB PA produces zero batting runs;
- the same MLB coverage rate is applied to player and reference, so coverage itself cannot create player value;
- no league centering, replacement runs, positional adjustment, or runs-per-win conversion is included here;
- no 2025 Defense/Position confirmation outcomes or other downstream confirmation residuals may tune this transform.

## Production output

Persist at least:

- `projected_batting_runs_above_mlb_reference`;
- `projected_expected_mlb_pa`;
- `projected_core_run_value_per_event`;
- `mlb_reference_core_run_value_per_event`;
- `mlb_reference_core_event_rate_per_pa`;
- reference Performance season/materialization provenance;
- batting projection method/provenance.

## Sensitivity before final WAR freeze

Before final WAR/value aggregation, report a non-binding sensitivity using an alternate recent certified MLB reference season when one is available. This may quantify era/reference drift but may not be used to retune the frozen formula after seeing ranking outcomes.

## Boundary

This contract closes Player Value v1 batting projected-run conversion. Replacement level remains a separate next gate. Runs per win and WAR remain closed until replacement level is frozen.
