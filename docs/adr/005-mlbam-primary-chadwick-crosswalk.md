# ADR 005: Use MLBAM as the event identity and Chadwick as a versioned crosswalk

- Status: Accepted for foundation work
- Date: 2026-08-15

## Context

The universal model needs one stable identity language across MLB and every affiliated minor-league level, plus links to public systems such as FanGraphs, Baseball-Reference, and Retrosheet. Identity mistakes are especially damaging because they can silently merge two players or split one player's history.

The modern MLB Stats API carries MLBAM person IDs directly in structured matchup/player fields. The reusable MiLB pitch source also carries copied MLBAM batter/pitcher fields, but source certification later found a narrow upstream mutation bug in the reusable source's batter column; that raw field therefore cannot be promoted wholesale as canonical identity.

The Chadwick Baseball Bureau public Register describes itself as a comprehensive baseball identity authority. Its public people files expose `key_uuid`, `key_person`, `key_mlbam`, `key_retro`, `key_bbref`, `key_bbref_minors`, `key_fangraphs`, and other identifiers. Chadwick also documents an important limitation: the public extract is delayed relative to its full register, and identity clusters can merge or split as source evidence improves. The public data are licensed under the Open Data Commons Attribution License.

Existing public packages confirm that we do not need to invent the mechanics of reading the Register:

- `baseballr::chadwick_player_lu()` downloads and concatenates all 16 `people-0.csv` through `people-f.csv` shards and exposes the cross-system IDs and player metadata.
- `pybaseball` also downloads the Chadwick Register for player-ID lookup, but its current loader deliberately drops rows without major-league identifiers. That behavior is reasonable for an MLB-oriented package but makes the helper unsuitable as the universal crosswalk for active minor-league and DSL players.
- `pybaseball` additionally offers fuzzy name matching. That is useful for interactive search but is not safe as an automatic canonical identity rule.

The recent public Chadwick repository has been updating periodically; current public revisions can lag newly signed or newly created minor-league identities. Missing Chadwick coverage therefore cannot be interpreted as evidence that a Stats API player ID is invalid.

## Decision

1. **MLBAM person ID from official structured evidence is the canonical modern event identity.** Official sequence/PA batter and pitcher IDs are the authority for the corresponding canonical fields.
2. **Raw participant IDs copied into reusable source files remain source evidence, not unquestioned canonical identity.** They are preserved with provenance and can be used where certified, but conflicts with official structured evidence are not silently resolved in favor of the reusable source.
3. **Chadwick is a versioned crosswalk/enrichment source, not the event authority.** Use it to attach Chadwick UUID/person keys and external IDs such as FanGraphs, Baseball-Reference, and Retrosheet.
4. **Reuse Chadwick's published data directly rather than creating a separate identity-matching system.** The ingestion pattern may follow the already-solved baseballr/pybaseball approach: fetch the public Register snapshot, concatenate the published people shards, and retain only fields needed by the model.
5. **Do not use pybaseball's MLB-filtered lookup table as the universal identity dataset.** Its filtering would structurally exclude players who have not reached MLB.
6. **Do not silently fuzzy-match names.** A missing MLBAM→Chadwick link is `crosswalk_pending`, not permission to guess. Any later manual/name-based exception must be explicit, reviewable, and separately provenance-tracked.
7. **Version every Chadwick snapshot.** Record upstream commit/release identity when available, retrieval time, and source checksum(s). Historical/as-of validation must be able to reproduce the crosswalk that was known at the time.
8. **Retain Chadwick's stable UUID when available, but do not assume it is metaphysically immutable.** Chadwick documents cluster merges/splits for sparse identities; snapshot provenance is therefore part of identity state.
9. **Preserve attribution/license metadata** for Chadwick-derived crosswalk data and do not casually redistribute a stripped derivative without the required attribution.

## Why not build our own universal person matcher?

There is no modeling advantage in recreating a mature authority-control problem. The expensive part—linking names, aliases, historical records, MLBAM IDs, FanGraphs IDs, Baseball-Reference IDs, and Retrosheet IDs—is exactly what Chadwick already maintains. Our responsibility is to ingest the public result reproducibly, measure coverage, and quarantine ambiguous/missing links rather than inventing replacements.

## Live certification evidence

### Pinned Chadwick snapshot

The first live audit pinned public Chadwick commit `2e8e73355f9c77b963115377bd98c784cfeec10f` rather than following `master` dynamically.

That snapshot produced:

- 518,743 public people rows across all 16 published shards;
- 129,658 rows with MLBAM IDs;
- 129,658 unique MLBAM IDs;
- zero duplicate MLBAM IDs in the snapshot.

Across one representative current official game at each of AAA, DSL, and FCL, the audit observed 83 distinct structured batter/pitcher MLBAM IDs and Chadwick matched **83/83** of them: 28/28 AAA, 28/28 DSL, and 27/27 FCL. No fuzzy/name matching was needed.

This is not a promise that every newly created DSL identity will always be present in the delayed public Chadwick extract. It demonstrates that the reuse strategy works cleanly in the first universal-level sample while preserving an explicit `crosswalk_pending` state for future gaps.

### Reusable-source participant IDs

A separate audit compared the batter/pitcher IDs embedded in the reusable pitch files with current official true-PA identities.

- Five sampled 2025 AAA games: 744 batter/pitcher comparisons, 743 matches; all 372 pitcher IDs matched and one batter ID disagreed.
- Explicit 2023 DSL/FCL/ACL games: 458 comparisons, 456 matches; all 229 pitcher IDs matched and two batter IDs disagreed.
- No sampled source sequence contained conflicting duplicate identity payloads.

Targeted diagnostics showed that all three batter mismatches have the **same deterministic upstream cause**. The reusable parser handles every `offensive_substitution` by assigning the substitution player's ID to `batter_id`. In the three mismatches the action was a **pinch-runner** (position code 12), so the source pitch row incorrectly carries the runner's ID while the official sequence/result correctly retains the actual batter. The source descriptions still name the real batter.

Examples:

- 2025 AAA game `781756`, atBatIndex `47`: source batter `687714` is pinch-runner Jackson Cluff; official batter `656448` is Stone Garrett.
- 2023 DSL game `741849`, atBatIndex `14`: source batter `808695` is pinch-runner Enmanuel Santos; official batter `808665` is Angel Acosta.
- 2023 ACL game `743157`, atBatIndex `59`: source batter `699108` is pinch-runner Eddy Isturiz; official batter `665912` is Miguel Hernandez.

This is exactly why reusable-source participant IDs remain raw evidence rather than the canonical identity layer. We do **not** need to rebuild the full historical parser to fix the canonical model: the official play-sequence layer already supplies the authoritative structured batter identity and can enrich the historical pitch rows by `game_pk + atBatIndex`.

Pitch-level participant changes in genuinely unusual mid-sequence substitutions remain a separate edge case; baseline normalization will flag rather than guess them.

## Certification rules before production promotion

1. Canonical modern sequence/PA identities come from official structured MLBAM fields, not names.
2. Reusable-source identity disagreements remain explicit quality evidence; raw IDs are preserved for debugging.
3. Chadwick snapshot coverage and MLBAM uniqueness are measured on every promoted snapshot.
4. Unmatched Chadwick IDs are reported explicitly rather than dropping players.
5. No automatic fuzzy-name matching is allowed in canonical joins.
6. Representative FanGraphs / Baseball-Reference / Retrosheet links should be spot-checked where Chadwick supplies them before those external joins become production dependencies.
7. The exact Chadwick snapshot, retrieval metadata, and attribution/license information are retained.

A low Chadwick match rate among very new DSL players would be a crosswalk-freshness limitation, not a reason to replace MLBAM IDs or exclude those players from the universal model.

## Consequences

- Event history remains usable immediately even when external cross-system IDs lag.
- The universal model can cover players before they have MLB, FanGraphs, or Baseball-Reference major-league records.
- External data joins become explicit enrichment steps instead of hidden name matching.
- The known reusable-source pinch-runner bug is neutralized at the canonical sequence identity layer without rewriting the historical collector.
- Identity corrections can be audited over time without rewriting raw event keys.
- The project needs only a thin, reproducible Chadwick snapshot loader and coverage validator rather than a custom identity-resolution engine.
