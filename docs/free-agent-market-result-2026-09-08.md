# Free-agent market reference — 2026-09-08

**Status:** 2026 three-tier reference accepted; future values are a named scenario

The main Phase 1 market source is FanGraphs' published 2026 study of the RosterResource
free-agent database. It subtracts the MLB minimum salary, excludes minor-league deals,
negative projections and undisclosed terms, uses projected rather than realized WAR,
and finds that a three-tier curve describes contracts better than one flat rate.

The accepted 2026 reference is:

| Full-season projected WAR | Dollars per WAR above minimum |
|---|---:|
| under 1 | $6.74 million |
| 1 to under 2 | $8.51 million |
| 2 or more | $12.84 million |

The contract-economics engine now accepts either a dated flat rate or these dated
tiers. The tier is selected from mean full-season projected WAR and held fixed when
lower/upper WAR sensitivities are valued. Current rest-of-season WAR is forbidden as
a tier input because it would misclassify a full-season star after most games have
already been played.

## Independent check

The public tracker and pinned identity crosswalk yielded 143 clean, unique one-year
major-league deals from 2020–2026. Chronology-safe StatsAPI forecasts were available
for all 143; 142 had positive projected WAR. The forecast uses the existing team-
neutral hitter/pitcher rates and fixed-denominator 3/2/1 workload, with 2020 scaled
from 60 to 162 games. Historical defense skill and baserunning remain neutral.

For the 18 clean 2026 one-year deals, this model projects 27.05 total WAR versus 25.40
from current FanGraphs projections: a 6.5% aggregate difference. Player correlation is
0.55 and mean absolute difference is 0.58 WAR. This is good enough as a broad scale
check, not an exact player-level replacement for FanGraphs.

The one-year sample produces $6.69 million per WAR above minimum in 2026, compared
with $11.23 million for FanGraphs' full market. That gap is expected and important:
one-year top-50 rows are mostly role players and cannot identify the multi-year star
premium. The internal result therefore does not replace or average down the main
three-tier reference.

## Future seasons

The reproducible Phase 1 scenario grows each 2026 tier by 3% annually through 2032.
That rate is an explicit economic assumption, not a CBA fact or a fitted guarantee.
It can be changed without changing WAR. The unresolved successor CBA still prevents
official post-2026 minimum-salary and arbitration-cost claims.

Run `scripts/materialize_one_year_free_agent_war.py --as-of-date 2026-09-08`,
`scripts/audit_one_year_free_agent_market.py --as-of-date 2026-09-08`, and
`scripts/materialize_free_agent_market_assumptions.py --as-of-date 2026-09-08`.

Primary source: Ben Clemens, FanGraphs, *What Are Teams Paying For A Win In Free
Agency? 2026 Edition*.
