# Player Value v1 replacement-level contract

Last updated: 2026-08-19

## Status

**FROZEN / VERIFIED.**

Binding convention: `fangraphs_570_war_pool_projected_pa_v1`.

Materialized reference: `docs/player-value-v1-replacement-level-2024.json`.

Verification: `docs/player-value-v1-replacement-level-verification.json`, Actions run `32280808517`.

The earlier fixed `baseball_reference_20_5_runs_per_600_pa_v1` implementation is **superseded for final WAR** but retained as development provenance.

Binding literature record: `docs/player-value-v1-war-literature-review.md`.

## Public-methodology basis

FanGraphs allocates 57% of the approximately 1,000 league WAR replacement pool to position players, or 570 WAR in a full 2,430-game MLB season. Position-player replacement runs are then derived from actual MLB games, league PA, and runs per win.

This is preferred to hard-coding 20.5 runs/600 PA because it keeps replacement tied to the certified MLB run and playing-time environment and matches the public league-WAR allocation framework.

Baseball-Reference's current 59% / 590-WAR position-player allocation and the legacy 20.5/600 convention remain non-binding sensitivities.

## Binding formula

For completed certified MLB reference season `s`:

`WARrep_pool_s = 570 * (MLB_games_s / 2430)`

`replacement_runs_per_pa_s = WARrep_pool_s * RPW_s / MLB_PA_s`

For player `i`:

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_s`

Only frozen Playing Time v1 **projected MLB PA** generate replacement credit. MiLB PA, defensive outs, catcher opportunities, and position shares do not independently generate replacement runs.

## Frozen 2024 reference

Certified 2024 MLB reference environment:

- completed regular-season games: `2429`;
- MLB PA: `182449`;
- runs per win: `9.682629939156854`;
- binding position-player allocation: `570 WAR`;
- prorated replacement WAR pool: `569.7654320987654`;
- replacement runs per PA: `0.030237643566893475`;
- replacement runs per 600 PA: `18.142586140136086`.

The 2,429-game denominator is taken from unique official MLB regular-season `gamePk` values with final coded state. Postponed schedule rows are not counted as completed games.

## Required sensitivities

Materialized without retuning from rankings:

- Baseball-Reference-style 590-WAR allocation: `18.779168109965422` runs/600 PA;
- superseded fixed 20.5 runs/600 PA convention: `20.5` runs/600 PA.

These remain diagnostics only; the 570-WAR allocation is binding.

## Production output

Persist at least:

- `replacement_runs`;
- `projected_expected_mlb_pa`;
- `replacement_runs_per_pa`;
- `replacement_runs_per_600_pa`;
- reference MLB season, games, PA, and RPW;
- position-player WAR allocation;
- convention ID and provenance.

## Boundary

Replacement level is closed. Runs per win is already frozen.

The next active Player Value gate is **baserunning / GIDP**. WAR/value aggregation remains unauthorized until baserunning, MLB-reference centering, park-neutrality audit, and remaining required sensitivities are complete.
