# Free-agent market source — 2026-09-08

**Status:** public contract facts accepted; historical signing-time forecasts must be rebuilt

The public FanGraphs free-agent tracker can support the first market-price study
without 60 manual team downloads. Seven season pages (2020–2026) produced 350 top-50
free-agent rows and 335 reported contracts. The source is a selected top-50 sample,
not the full free-agent population.

Stable FanGraphs player IDs are retained from the player links. A crosswalk pinned to
Chadwick commit `2e8e73355f9c77b963115377bd98c784cfeec10f` maps all 350 rows to one
MLBAM ID without name matching. All 155 reported one-year contract rows map as well.
Exact duplicate HTML tables are collapsed; genuine repeat contracts for the same
player and class remain visible.

## What the source can and cannot do

The tracker supplies reported years, total value, AAV, signing team, age, position,
service time and stable identity. When AAV is present, `years × AAV` is retained as
the effective total so a displayed deferral-adjusted AAV is not silently replaced by
headline dollars.

The mutable historical pages do **not** preserve a reliable archive of the forecast
available at signing. Projected WAR is populated for all 50 current 2026-class rows
but blank for 2020–2025. Those blanks will not be backfilled with realized WAR or a
current projection.

## Phase 1 fitting population

The first fit will use clean reported one-year major-league deals. This removes
multi-year aging, options, opt-outs and most deferral assumptions from the initial
question. Duplicate player/class contracts, minor-league deals, unreported terms and
implausible below-minimum values are review exclusions, not zeros.

Each player's signing-time WAR forecast will be recreated from official StatsAPI
history available before that season. It will use the existing team-neutral hitter
and pitcher rate methods plus a transparent prior-three-year workload estimate.
Defense and baserunning are neutral in this historical fit because equivalent dated
inputs are not yet available. That is a disclosed limitation, not hidden precision.

The initial price will be adopted only if a fixed development-period method behaves
reasonably in a later-season check. A single dollars-per-WAR number is not assumed in
advance. Full-population member exports and multi-year contract modeling belong in
Phase 2 if they materially improve the one-year reference.

## Reproduction

Run `scripts/materialize_free_agent_market_source.py --as-of-date 2026-09-08`, then
`scripts/materialize_free_agent_market_identity.py --as-of-date 2026-09-08`. Generated
source captures, normalized tables, hashes and coverage reports remain outside git.

Sources:

- FanGraphs RosterResource public free-agent tracker, season pages 2020–2026
- Chadwick Bureau register, pinned by commit and archive hash
