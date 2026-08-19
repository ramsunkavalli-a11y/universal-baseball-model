# Player Value v1 runs-per-win contract

Last updated: 2026-08-19

## Status

**FROZEN METHOD — RETAINED AFTER WAR LITERATURE REVIEW.**

Position-player runs are converted to wins with the public FanGraphs/Tango league-wide hitter runs-per-win convention.

The broader literature review reopened replacement level and added required baserunning, MLB-reference centering, and park-neutrality gates, but it did **not** identify a reason to reopen the runs-per-win method.

Binding literature record: `docs/player-value-v1-war-literature-review.md`.

Implementation verification: `docs/player-value-v1-runs-per-win-verification.json`, Actions run `32275833614`.

## Binding public convention

For the MLB reference environment:

`RPW = 9 * (MLB_runs_scored / MLB_innings_pitched) * 1.5 + 3`

Equivalent form:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Binding convention ID:

`fangraphs_tango_league_rpw_v1`

## Reference environment

Use the **latest completed certified MLB regular season available to the Player Value snapshot**.

Requirements:

- pool AL and NL into one MLB run environment;
- use actual regular-season MLB runs scored;
- use actual regular-season MLB innings pitched;
- do not use a partial current season when a completed-season reference is required;
- persist the source season and provenance with calculated RPW.

The same RPW applies to every position player in the same Player Value snapshot.

A 2024 MLB reference materialization has been certified from MLB Stats API evidence at 21,343 runs over 43,116 1/3 innings, implying approximately `9.68263` runs per win. Preserve the exact materialized value from the certified artifact when production code consumes it rather than rounding this documentation value.

## Why this form remains binding

The public literature supports retaining one league-wide position-player conversion because it:

- preserves the additive run decomposition;
- adapts to the league scoring environment;
- does not make the conversion itself a player-quality model;
- is transparent and deterministic;
- integrates directly with the FanGraphs-style replacement allocation now predeclared for the reopened replacement gate.

Baseball-Reference's player-aware PythagenPat conversion remains an informative sensitivity. It is not binding for v1 because it makes wins conversion depend on the individual player's contribution and therefore removes the simple common divisor used by this projected-value architecture.

## Final WAR formula boundary

The old formula omitting baserunning and league/reference centering is superseded.

Once every pre-WAR gate is frozen, the intended decomposable form is:

`runs_above_replacement = batting_runs + baserunning_runs + gidp_runs_if_separate + defense_runs + positional_adjustment_runs + mlb_reference_centering_runs + replacement_runs`

`WAR = runs_above_replacement / RPW`

No baserunning, GIDP, centering, park, or replacement term may be silently absorbed into another component.

A park term is **not** automatically required: the park-neutrality audit must first determine whether the frozen batting projection already removes the relevant context. If a correction is justified, it must remain explicit.

## Validation requirements

The production RPW calculator must reject:

- non-finite or negative runs scored;
- non-finite or non-positive innings pitched;
- resulting non-finite or non-positive RPW.

It must persist:

- MLB runs scored;
- MLB innings pitched;
- MLB runs per nine innings;
- runs per win;
- reference season;
- convention ID/source provenance.

## Required sensitivities before final WAR freeze

Without retuning the binding method from ranking outcomes, final QA should include:

1. Baseball-Reference player-aware/PythagenPat runs-to-wins comparison if practical;
2. Baseball-Reference positional-adjustment schedule sensitivity;
3. alternate recent certified MLB batting reference season when available;
4. replacement-level allocation sensitivities required by the reopened replacement contract.

## Boundary

Runs-per-win **method is closed**. WAR/value aggregation remains unauthorized until:

- replacement level is refrozen;
- baserunning/GIDP is resolved;
- MLB-reference centering is frozen;
- park neutrality is audited;
- required sensitivities are completed.
