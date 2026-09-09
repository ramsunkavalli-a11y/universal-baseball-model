# Hitter Opportunity v1

**Status:** historical cohorts fitted; current league path pending
**Date:** 2026-09-08

## What it does

Every hitter receives an MLB-arrival and plate-appearance path for every requested
forecast year. The path keeps these two quantities separate:

- probability of any MLB PA; and
- expected PA conditional on reaching MLB.

Expected PA is their product. The module does not use current-team depth and does not
cap forecasts.

For the next season, the frozen selected Playing Time v1 forecast is used when its
required prediction is supplied. Every unsupported player and every later season uses
pre-cutoff historical cohorts. Cohorts are grouped by forecast horizon, broad level and
two-year age band. Small age/level cells shrink toward their level cohort; level cohorts
shrink toward the full horizon population. Missing age, inactive and unknown-level
players fall back explicitly rather than disappearing or becoming zero.

The horizon-specific design allows lower-level players to arrive later and established
players to leave MLB over time. These are observed cohort outcomes, not manually chosen
career curves.

## Required inputs

1. Dated historical affiliated-hitter snapshots containing player ID, age and level.
2. Complete future MLB PA totals for each target season. A player absent from a
   certified complete MLB season is retained with zero PA.
3. The current hitter universe with player ID, age and level.
4. Optional frozen Playing Time v1 next-season predictions.

`materialize_hitter_opportunity_paths.py` builds the zero-inclusive history, fits the
fallback hierarchy, scores every current hitter and writes coverage/source reports.
`compose_hitter_projection_paths` then joins opportunity to conditional WAR/600 and
team-control seasons in the shared Projection v1 schema.

## Boundary and next action

The 2018–2024 official source history is now collected and the zero-inclusive fallback
fit is materialized with 2020 excluded. This is still not a claimed current league
forecast. The public checkout does not contain the frozen Playing Time v1 coefficient
tables. Do not substitute made-up coefficients. Build the current snapshot, attach the
selected model only where its real output is available, inspect broad coverage and
calibration, and then proceed to hitter aging and conditional WAR-rate assembly.
Protected 2026 outcomes remain closed.
