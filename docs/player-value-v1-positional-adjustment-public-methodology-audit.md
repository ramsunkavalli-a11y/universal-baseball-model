# Player Value v1 — positional-adjustment public methodology audit

Last updated: 2026-08-19

Status: **RESEARCH AUDIT; RECOMMENDATION ONLY, NOT YET A BINDING V1 FREEZE.**

## Purpose

Compare the two most transparent current public position-player WAR positional-adjustment conventions and identify which architecture is the cleaner fit for a forward universal projection model.

This audit does not calculate Player Value, replacement level, runs per win, or WAR.

## Public sources

### FanGraphs

Official FanGraphs Library:

- https://library.fangraphs.com/misc/war/positional-adjustment/
- https://library.fangraphs.com/war/war-position-players/

FanGraphs documents a fixed full-season schedule per 1,458 defensive innings / 162 nine-inning games:

| Position | Runs / full season |
|---|---:|
| C | +12.5 |
| 1B | -12.5 |
| 2B | +2.5 |
| 3B | +2.5 |
| SS | +7.5 |
| LF | -7.5 |
| CF | +2.5 |
| RF | -7.5 |
| DH | -17.5 |

For multi-position players FanGraphs prorates each position separately and sums the adjustments. Its WAR architecture treats any league-wide balancing adjustment as a separate league-adjustment layer rather than modifying the positional schedule itself.

FanGraphs also explicitly notes that the schedule is an estimate based on historical position-switching work and may not be perfectly current.

### Baseball-Reference

Official Baseball-Reference WAR methodology:

- https://www.baseball-reference.com/about/war_explained_position.shtml

Baseball-Reference currently documents these raw values per 1,350 innings / 150 nine-inning games:

| Position | Runs / 1,350 innings |
|---|---:|
| C | +9.0 |
| 1B | -9.5 |
| 2B | +3.0 |
| 3B | +2.0 |
| SS | +7.0 |
| LF | -7.0 |
| CF | +2.5 |
| RF | -7.0 |
| DH | -15.0 |

Baseball-Reference states that its values can vary across eras and adds a final league-wide centering step so positional-adjustment runs sum effectively to zero. The centering allocation is itself part of the realized-season WAR calculation.

## Same-denominator comparison

Scaling FanGraphs to 1,350 innings for an apples-to-apples comparison gives approximately:

| Position | FanGraphs scaled to 1,350 | Baseball-Reference current | Difference FG - BRef |
|---|---:|---:|---:|
| C | +11.574 | +9.0 | +2.574 |
| 1B | -11.574 | -9.5 | -2.074 |
| 2B | +2.315 | +3.0 | -0.685 |
| 3B | +2.315 | +2.0 | +0.315 |
| SS | +6.944 | +7.0 | -0.056 |
| LF | -6.944 | -7.0 | +0.056 |
| CF | +2.315 | +2.5 | -0.185 |
| RF | -6.944 | -7.0 | +0.056 |
| DH | -16.204 | -15.0 | -1.204 |

The systems agree closely at SS, 3B, CF, LF, and RF. The meaningful differences are mostly the magnitude of catcher, first-base, and DH adjustments and, to a lesser extent, second base.

## Fit to this project

Player Value v1 has several constraints that differ from a retrospective single-season WAR table:

1. it is a forward projection model;
2. it must work for a universal player pool, including players outside the current MLB roster population;
3. general Defense skill is already position-relative, so positional difficulty must remain a separate additive layer;
4. non-DH forward positional exposure is already frozen as projected fielding outs by position;
5. DH has no fielding outs and therefore needs one separately validated role-exposure forecast;
6. the project has intentionally kept league adjustment, replacement level, and runs per win closed as later layers.

A league-population-dependent centering step inside positional adjustment would make a player's positional value depend on the composition and completeness of the projected league pool. That is undesirable for a universal projection surface and would also blur the boundary between positional adjustment and any later league-average balancing decision.

## Recommended v1 convention

**Recommendation: use the fixed FanGraphs positional schedule as the v1 reference convention, with no league-wide centering inside the positional-adjustment layer.**

Reasons:

- fixed and deterministic across projection runs;
- naturally prorates by position-specific playing time;
- directly compatible with the existing separation of position-relative Defense and positional difficulty;
- handles multi-position players transparently by summation;
- does not require the full projected league population to be complete before an individual player's positional adjustment can be computed;
- keeps any future league-wide balancing adjustment in its own explicit layer rather than hiding it inside position value.

This recommendation is not a claim that the older FanGraphs multipliers are more empirically current than Baseball-Reference's. Baseball-Reference should remain the primary **sensitivity schedule** because its current raw values are public, transparent, and materially milder at C/1B/DH.

## Proposed exposure interface if selected

For non-DH positions, use the already-frozen projected fielding outs:

`position_games_equivalent[p] = projected_position_fielding_outs[p] / 27`.

FanGraphs positional runs for a defensive position would therefore be:

`position_runs[p] = FG_full_season_adjustment[p] * projected_position_fielding_outs[p] / 4374`.

For DH, use the separately selected projected DH role-equivalent games:

`DH_runs = -17.5 * projected_DH_role_events / 162`.

Total raw positional adjustment:

`Rpos_raw = sum(defensive_position_runs) + DH_runs`.

Do not renormalize a player's defensive shares to make room for DH. Defensive fielding exposure and DH batting-role exposure are separate observed quantities and can coexist in a season when a player changes roles.

## Required sensitivity after the production surface exists

Before opening replacement level / WAR aggregation, report the same projected player positional adjustments under:

1. selected FanGraphs fixed schedule; and
2. Baseball-Reference current raw schedule on the same frozen exposure surface.

This is a sensitivity diagnostic only. Do not choose whichever schedule makes particular players rank better.

## Boundaries

- This file is a methodology audit/recommendation, not the binding positional-adjustment freeze.
- Do not modify frozen Defense skill or exposure.
- Do not use 2025 outcomes to tune positional multipliers.
- Do not empirically fit new positional constants in v1 unless a separately preregistered public-data study is opened first.
- League adjustment remains a separate possible future layer.
- Replacement level, runs per win, WAR/value, and final ranking remain closed.
