# ADR 005: Use MLBAM as the event identity and Chadwick as a versioned crosswalk

- Status: Accepted for foundation work
- Date: 2026-08-15

## Context

The universal model needs one stable identity language across MLB and every affiliated minor-league level, plus links to public systems such as FanGraphs, Baseball-Reference, and Retrosheet. Identity mistakes are especially damaging because they can silently merge two players or split one player's history.

The modern MLB Stats API and the reusable MiLB PBP source both carry MLBAM person IDs directly in structured batter/pitcher fields. Those IDs therefore require no name matching for event attribution.

The Chadwick Baseball Bureau public Register describes itself as a comprehensive baseball identity authority. Its public people files expose `key_uuid`, `key_person`, `key_mlbam`, `key_retro`, `key_bbref`, `key_bbref_minors`, `key_fangraphs`, and other identifiers. Chadwick also documents an important limitation: the public extract is delayed relative to its full register, and identity clusters can merge or split as source evidence improves. The public data are licensed under the Open Data Commons Attribution License.

Existing public packages confirm that we do not need to invent the mechanics of reading the Register:

- `baseballr::chadwick_player_lu()` downloads and concatenates all 16 `people-0.csv` through `people-f.csv` shards and exposes the cross-system IDs and player metadata.
- `pybaseball` also downloads the Chadwick Register for player-ID lookup, but its current loader deliberately drops rows without major-league identifiers. That behavior is reasonable for an MLB-oriented package but makes the helper unsuitable as the universal crosswalk for active minor-league and DSL players.
- `pybaseball` additionally offers fuzzy name matching. That is useful for interactive search but is not safe as an automatic canonical identity rule.

The recent public Chadwick repository has been updating periodically; current public revisions can lag newly signed or newly created minor-league identities. Missing Chadwick coverage therefore cannot be interpreted as evidence that a Stats API player ID is invalid.

## Decision

1. **MLBAM person ID is the canonical modern event identity.** Batter, pitcher, runner, and fielder identities sourced from MLB Stats API data remain keyed by their structured MLBAM IDs.
2. **Chadwick is a versioned crosswalk/enrichment source, not the event authority.** Use it to attach Chadwick UUID/person keys and external IDs such as FanGraphs, Baseball-Reference, and Retrosheet.
3. **Reuse Chadwick's published data directly rather than creating a separate identity-matching system.** The ingestion pattern may follow the already-solved baseballr/pybaseball approach: fetch the public Register snapshot, concatenate the published people shards, and retain only fields needed by the model.
4. **Do not use pybaseball's MLB-filtered lookup table as the universal identity dataset.** Its filtering would structurally exclude players who have not reached MLB.
5. **Do not silently fuzzy-match names.** A missing MLBAM→Chadwick link is `crosswalk_pending`, not permission to guess. Any later manual/name-based exception must be explicit, reviewable, and separately provenance-tracked.
6. **Version every Chadwick snapshot.** Record upstream commit/release identity when available, retrieval time, and source checksum(s). Historical/as-of validation must be able to reproduce the crosswalk that was known at the time.
7. **Retain Chadwick's stable UUID when available, but do not assume it is metaphysically immutable.** Chadwick documents cluster merges/splits for sparse identities; snapshot provenance is therefore part of identity state.
8. **Preserve attribution/license metadata** for Chadwick-derived crosswalk data and do not casually redistribute a stripped derivative without the required attribution.

## Why not build our own universal person matcher?

There is no modeling advantage in recreating a mature authority-control problem. The expensive part—linking names, aliases, historical records, MLBAM IDs, FanGraphs IDs, Baseball-Reference IDs, and Retrosheet IDs—is exactly what Chadwick already maintains. Our responsibility is to ingest the public result reproducibly, measure coverage, and quarantine ambiguous/missing links rather than inventing replacements.

## Certification gates before promotion

Before a production crosswalk is promoted:

1. sample structured batter/pitcher MLBAM IDs from official PBP and the reusable MiLB source across AAA and Rookie/DSL games and confirm source IDs agree with official IDs at shared PA/pitch keys;
2. measure Chadwick coverage for those observed MLBAM IDs, separately by level and recency;
3. verify that each non-null MLBAM ID maps to at most one active Chadwick identity in the chosen snapshot;
4. report unmatched IDs explicitly rather than dropping players;
5. verify representative FanGraphs / Baseball-Reference / Retrosheet links where Chadwick supplies them;
6. retain the exact Chadwick snapshot metadata used for the report.

A low Chadwick match rate among very new DSL players would be a crosswalk-freshness limitation, not a reason to replace MLBAM IDs or exclude those players from the universal model.

## Consequences

- Event history remains usable immediately even when external cross-system IDs lag.
- The universal model can cover players before they have MLB, FanGraphs, or Baseball-Reference major-league records.
- External data joins become explicit enrichment steps instead of hidden name matching.
- Identity corrections can be audited over time without rewriting historical event keys.
- The project needs only a thin, reproducible Chadwick snapshot loader and coverage validator rather than a custom identity-resolution engine.
