# Player Value v1 replacement-level contract

Last updated: 2026-08-19

## Status

**REOPENED / SUPERSEDES THE EARLIER 20.5-RUN FREEZE.**

The earlier binding choice of a fixed **20.5 runs per 600 projected MLB PA** was mechanically verified in Actions run `32275638045`, but it is no longer authorized for final Player Value v1 WAR.

The implementation and verification record are retained as provenance. They document a valid calculation of the old convention, not the final replacement-level choice.

Reason for reopening: a broader review of the public WAR literature showed that Baseball-Reference does **not** simply use 20.5 runs/600 PA as an immutable final player-level replacement credit. It starts from a league replacement framework, uses 20.5 as a modern 162-game position-player multiplier, and then fine-tunes/re-centers replacement runs to the desired league WAR total. FanGraphs instead derives position-player replacement runs directly from the league WAR allocation, league PA, and runs per win.

Binding literature record: `docs/player-value-v1-war-literature-review.md`.

## Public-methodology basis

Both FanGraphs and Baseball-Reference use an overall major-league replacement level near a .294 winning percentage, implying roughly 1,000 WAR over a normal 30-team, 162-game MLB season.

Their current position-player allocations differ:

- FanGraphs: **57%** of league WAR to position players, or **570 WAR** over a full MLB season;
- Baseball-Reference: **59%** to position players, or **590 WAR**.

The v1 replacement gate will use the FanGraphs position-player allocation as the binding candidate because it gives a direct, transparent, season-environment-dependent bridge from average to replacement and integrates naturally with the already-frozen common runs-per-win method.

Baseball-Reference's 59% allocation and its 20.5-run modern multiplier remain required non-binding sensitivities.

## Predeclared binding candidate

Let:

- `PA_i` = frozen Playing Time v1 `projected_expected_mlb_pa` for player `i`;
- `MLB_games_ref` = completed certified MLB regular-season games in the reference season;
- `MLB_PA_ref` = completed certified MLB regular-season position-player plate appearances in the same reference season;
- `RPW_ref` = frozen FanGraphs/Tango league-wide runs-per-win value for that same completed MLB reference environment;
- `position_player_WAR_pool = 570` for 2,430 MLB games.

Then:

`WARrep_pool_ref = 570 * (MLB_games_ref / 2430)`

`replacement_runs_per_pa_ref = WARrep_pool_ref * RPW_ref / MLB_PA_ref`

`Rrep_i = projected_expected_mlb_pa_i * replacement_runs_per_pa_ref`

This is the FanGraphs public position-player replacement construction expressed on the project's projected-PA exposure.

## Why this form is preferred

- Replacement remains a separate credit from batting, baserunning, Defense, and position.
- Only projected **MLB** PA generate replacement credit; MiLB opportunity does not.
- The replacement rate adapts to the certified MLB run environment rather than hard-coding an approximate modern run value.
- Position does not change the replacement rate because positional difficulty is already handled in the separate positional-adjustment layer.
- The rate depends on one fixed MLB reference population, not on whichever MLB/prospect universe happens to be loaded for a ranking run.
- No final ranking outcomes are used to choose the replacement convention.

## Exposure semantics

Replacement runs accrue only on frozen Playing Time v1 `projected_expected_mlb_pa`.

Therefore:

- zero projected MLB PA -> zero replacement runs;
- MiLB PA, affiliated opportunity, defensive outs, catcher opportunities, and Position/Role shares do not independently generate replacement credit;
- no position-specific replacement baseline is added;
- no ranking-population re-centering occurs inside replacement level.

## Required materialization before refreeze

Before this gate can be marked frozen again, certify from one completed MLB reference season:

1. MLB regular-season games;
2. MLB regular-season position-player PA;
3. the already-defined league-wide RPW environment;
4. the resulting replacement runs per PA and per 600 PA.

The reference season must be the same completed certified MLB environment used for the snapshot's runs-per-win conversion unless a later contract explicitly freezes a different common reference.

## Required sensitivities before final WAR freeze

Without retuning the binding candidate from player rankings, report:

1. Baseball-Reference-style **59% / 590 position-player WAR** allocation using the same reference PA and RPW;
2. the prior **20.5 runs/600 PA** convention as an interpretive comparison;
3. if practical, the difference between direct allocation and Baseball-Reference-style league-total fine-tuning/re-centering.

## Production output

Persist at least:

- `replacement_runs`;
- `projected_expected_mlb_pa`;
- `replacement_runs_per_pa`;
- `replacement_runs_per_600_pa`;
- reference MLB season;
- reference MLB games;
- reference MLB PA;
- reference RPW;
- position-player WAR allocation;
- `replacement_level_convention_id`;
- provenance and sensitivity fields.

Candidate convention ID:

`fangraphs_570_war_pool_projected_pa_v1`

## Superseded convention

`baseball_reference_20_5_runs_per_600_pa_v1` is **superseded for final WAR**. Do not delete its implementation or verification record; keep them as an auditable development artifact.

## Boundary

Replacement level is **ACTIVE / NOT YET REFROZEN** until the reference-season PA allocation is materialized and verified.

Runs per win remains frozen as a method. WAR/value aggregation remains unauthorized until replacement level is refrozen and the newly required baserunning, MLB-reference centering, and park-neutrality gates are resolved.
