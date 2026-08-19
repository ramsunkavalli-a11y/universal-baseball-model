# Player Value v1 runs-per-win contract

Last updated: 2026-08-19

## Status

**FROZEN METHOD.** Position-player runs are converted to wins with the public FanGraphs league-wide hitter runs-per-win convention.

No player-specific runs-to-wins adjustment is used in v1. This keeps the already-frozen batting, Defense, positional, and replacement run components additive on one common run scale before the final division to wins.

## Binding public convention

For the MLB reference environment:

`RPW = 9 * (MLB_runs_scored / MLB_innings_pitched) * 1.5 + 3`

Equivalent form using MLB runs per nine innings:

`RPW = 1.5 * MLB_runs_per_9_innings + 3`

Binding convention ID:

`fangraphs_tango_league_rpw_v1`

## Reference environment

Use the **latest completed certified MLB regular season available to the Player Value snapshot**.

Requirements:

- pool the AL and NL into one MLB run environment;
- use actual regular-season MLB runs scored;
- use actual regular-season MLB innings pitched;
- do not use a partial current season when a completed-season reference is required;
- persist the source season and source provenance with the calculated RPW.

The same RPW applies to every position player in the same Player Value snapshot.

## Why this form is binding

The project needs a transparent forward-looking conversion after all component runs are calculated. A single league-wide RPW:

- preserves the additive run decomposition already frozen upstream;
- avoids making the run-to-win conversion itself a player-quality model;
- adapts to the MLB run environment without fitting to final rankings;
- has an established public methodology and a simple deterministic implementation.

Baseball-Reference's player-specific PythagenPat conversion remains informative methodology context but is not binding for v1 because it makes runs-to-wins depend on each player's own contribution and therefore breaks the simple common divisor used by the current Player Value architecture.

## Final WAR formula boundary

Once the required pre-WAR sensitivities are completed, position-player v1 may calculate:

`runs_above_replacement = batting_runs + defense_runs + positional_adjustment_runs + replacement_runs`

`WAR = runs_above_replacement / RPW`

No baserunning term is silently imputed. If baserunning is not modeled in v1, it must remain an explicit omitted component/coverage limitation in persisted output and documentation.

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

## Boundary

The runs-per-win **method** is closed by this contract. The exact MLB reference-environment materialization must be verified before final WAR aggregation.

Before WAR is frozen, also complete the previously required non-binding sensitivities:

1. Baseball-Reference current raw positional-adjustment schedule;
2. alternate recent certified MLB batting reference season when available;
3. FanGraphs-style replacement-allocation sensitivity using the frozen RPW and relevant MLB PA.
