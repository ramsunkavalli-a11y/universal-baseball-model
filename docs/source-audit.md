# Source Audit

## Purpose

Before writing play-by-play ingestion or parsing code, determine how much of the difficult collection, cleanup, identity resolution, and event reconstruction has already been solved well enough by public projects.

The default is **reuse first**. We should only build source-specific ingestion where an existing option is unavailable, materially incomplete, unreliable, poorly documented, or unsuitable for reproducible historical work.

## Evaluation criteria

For each candidate source/package, record:

- Coverage by season and level: MLB, AAA, AA, A+, A, complex leagues, DSL.
- Grain: season, game, plate appearance, pitch, batted ball, tracking.
- Historical availability and whether past data can be reproduced.
- Update cadence and suitability for incremental ingestion.
- Player/game identity fields and cross-source compatibility.
- Important fields exposed for the first Performance model.
- Known missingness, park/level biases, schema changes, or recording-quality issues.
- Ease of use from Python, regardless of the implementation language of the upstream project.
- Licensing, terms, attribution, and redistribution considerations.
- Maintenance/activity and likelihood the project remains usable.
- Amount of transformation we would still need to own.
- Ability to reconcile against official MLB/MiLB totals.

## Initial candidates

Evaluate before selecting a PBP path:

1. `armstjc/milb-data-repository`
2. `baseballr`
3. MLB Stats API directly
4. `python-mlb-statsapi`
5. `pybaseball`
6. SportsDataverse / `sportsdataverse-py`
7. Retrosheet + Chadwick tools/register where relevant
8. `baseballquery`

Add other credible reusable sources discovered during the audit.

## Decision principle

The official feed can remain the **reconciliation authority** without being the system we parse from scratch. A mature cleaned source may become the working historical input if sampled games and aggregate totals demonstrate that it is sufficiently faithful.

## First proof-of-concept gate

Do not build the full pipeline until we have selected one or two promising reusable approaches and tested a small slice of data for:

- expected games and players;
- PA/BF counts;
- AB, H, 2B, 3B, HR, BB, HBP, and K reconciliation;
- event completeness needed for the initial Performance taxonomy;
- obvious level/park/season-specific data-quality problems.

Document discrepancies rather than immediately writing custom fixes. Custom source parsing comes only after we know the reusable approaches cannot solve the problem acceptably.
