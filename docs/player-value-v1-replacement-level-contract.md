# Player Value v1 replacement-level contract

Last updated: 2026-08-19

## Status

**FROZEN.** Position-player replacement runs use a fixed public replacement gap of **20.5 runs per 600 projected MLB plate appearances**.

This is a convention layer, not a fitted performance model. No ranking outcomes, 2025 confirmation residuals, or player-level performance outcomes are used to select or tune it.

## Public-methodology basis

Established public WAR systems agree on the conceptual baseline: replacement credit is the difference between an average player and a freely available replacement player, scaled by playing time.

For v1, use the current Baseball-Reference position-player convention of **20.5 replacement runs per 600 PA**. This direct run-scale convention is preferred here because it can be fixed independently of the still-closed runs-per-win gate.

FanGraphs instead derives position-player replacement runs from its allocated share of league WAR, league PA, and runs per win. Preserve that as a required non-binding sensitivity after the runs-per-win convention is frozen; do not use it now to reopen or tune the binding replacement rate.

## Binding formula

Let:

- `PA_i` = frozen Playing Time v1 `projected_expected_mlb_pa` for player `i`;
- `replacement_runs_per_600_pa = 20.5`.

Then:

`Rrep_i = PA_i * 20.5 / 600`

Equivalent rate:

`replacement_runs_per_pa = 0.034166666666666665`.

## Exposure semantics

Replacement runs accrue only on **projected MLB plate appearances**.

Therefore:

- zero projected MLB PA -> zero replacement runs;
- MiLB PA, projected affiliated opportunity, defensive outs, catcher opportunities, and Position/Role shares do not independently generate replacement credit;
- no position-specific replacement rate is added because positional difficulty is already handled in the separate frozen positional-adjustment layer;
- no league centering or roster-population adjustment occurs inside this layer.

## Production output

Persist at least:

- `replacement_runs`;
- `projected_expected_mlb_pa`;
- `replacement_runs_per_600_pa`;
- `replacement_level_convention_id`.

Binding convention ID:

`baseball_reference_20_5_runs_per_600_pa_v1`

## Required sensitivity before final WAR freeze

After runs per win is frozen, calculate a non-binding FanGraphs-style position-player replacement allocation sensitivity using the public 570-WAR position-player allocation formula and the relevant MLB PA/run environment. Report the difference but do not retune the binding 20.5/600 rate after ranking outcomes are seen.

## Boundary

This closes replacement level for Player Value v1.

Runs per win is now the next unopened gate. WAR/value aggregation remains unauthorized until runs per win is frozen and required pre-WAR sensitivities are calculated.
