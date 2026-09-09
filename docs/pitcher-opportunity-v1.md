# Pitcher Opportunity v1

**Status:** historical cohorts fitted; 2027–2032 current baseline materialized
**Date:** 2026-09-08

Pitcher Opportunity v1 keeps four questions separate for every forecast year:

- probability of appearing in MLB;
- batters faced conditional on appearing;
- starter, swingman and reliever probabilities conditional on appearing; and
- conditional pitching WAR per 800 BF, joined only after opportunity is forecast.

The cohort fallback is horizon-specific. It uses starting level, recent role and a
two-year age band, shrinking sparse cells toward level/role, level, and full-population
cohorts in that order. Missing age, unknown role, inactive players and unsupported
levels remain in the output through labeled fallbacks. Current-team depth and workload
caps are not used.

Observed role has one disclosed definition: starter when at least half of games are
starts, reliever with no starts, and swingman otherwise. The forecast retains all three
probabilities even though the highest-probability label is used for the shared
guardrail row.

The implementation rejects future-crossing evidence, inconsistent games/starts/BF,
missing horizons and incomplete player-year coverage. It composes directly with
conditional WAR/800 BF and team-control seasons in the Projection v1 schema.

The zero-inclusive 2018–2024 historical pitcher panel and six-horizon fallback fit are
now materialized, excluding the structurally abnormal 2020 snapshot. This is not yet a
current league result. Build and score the current pitcher snapshot, run broad
calibration and coverage checks, then connect the existing component-rate baseline and
pitcher aging/run conversion.
