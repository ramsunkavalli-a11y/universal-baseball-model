# Position / role historical source certification contract

Last updated: 2026-08-18

Status: **FROZEN BEFORE FULL 2021–2024 HISTORICAL SOURCE PULL.**

Upstream readiness checkpoint: `docs/position-role-coherence-readiness.md`.

Binding 2024 representative-league POC: `docs/position-role-fielding-source-poc-result.json`.

## Purpose

Certify a chronology-safe official historical source for player position/role usage. This gate does **not** fit a position model, project a future role, alter Playing Time v1, or authorize a team-allocation optimizer.

## Source

Official MLB Stats API bulk season endpoint:

`/api/v1/stats`

For each authorized season × actual league:

- `stats=season`
- `group=fielding` and a same-league `group=hitting` coverage surface
- `season=<year>`
- `leagueId=<actual league>`
- `playerPool=ALL`
- `gameType=R`
- paginated with `limit=500`
- no `sportIds` parameter

Raw response bytes and SHA-256 hashes must be retained.

## Authorized historical seasons

- 2021
- 2022
- 2023
- 2024

All are completed regular seasons before the October 15 Projection/Playing-Time snapshots used by the project. No 2025 source may be queried by this gate.

## Authorized actual leagues

MLB:

- 103 — American League
- 104 — National League

Affiliated MiLB, reusing the repo’s already-frozen actual-league map:

- AAA: 112, 117
- AA: 109, 111, 113
- High-A: 116, 118, 126
- Single-A: 110, 122, 123
- Rookie/complex: 121, 124, 130

No filename-level or inferred league identity may replace the requested actual league ID.

## Canonical fielding-usage row

One source row at:

`season × league_id × team_id × player_id × position_code`

Required source fields:

- exact `player.id`;
- exact `team.id`;
- `position.code`;
- `position.abbreviation`;
- `position.name`;
- `stat.games`;
- `stat.gamesPlayed`;
- `stat.gamesStarted`;
- `stat.innings`.

Frozen position code mapping:

- 1 = P
- 2 = C
- 3 = 1B
- 4 = 2B
- 5 = 3B
- 6 = SS
- 7 = LF
- 8 = CF
- 9 = RF
- 10 = DH

Unexpected or missing position codes fail closed.

## Frozen count semantics

### Starting-role evidence

`games_started` is retained directly as a nonnegative integer for all positions, including DH.

This is the future candidate source for a **starting-role profile**, but this certification gate does not yet construct or select a projection method.

### Defensive-workload evidence

Stats API `innings` uses baseball innings notation, not a decimal fraction. It must be converted deterministically to defensive outs:

- `N.0 -> 3N` outs
- `N.1 -> 3N + 1` outs
- `N.2 -> 3N + 2` outs

Any other fractional suffix fails closed.

For DH rows, `fielding_outs` must be zero. DH starting-role evidence remains available through `games_started`; DH is never assigned defensive outs.

### Games fields

`stat.games` and `stat.gamesPlayed` must both be nonnegative integers and must agree exactly. `games_started` cannot exceed `games_played`.

## Coverage diagnostics

For each season × league, same-league hitting player IDs are used only to measure source coverage.

Persist:

- hitting unique players;
- fielding unique players;
- hitters with no fielding row;
- examples of missing hitter IDs;
- fielding split count;
- position distribution;
- players with zero total `games_started` despite a fielding row;
- raw capture/page counts and hashes.

A hitter missing from fielding is **not** automatically classified as DH. The 2024 POC already showed explicit DH fielding rows, so absence remains an unresolved/missing-usage diagnostic.

Missing hitter coverage does not invalidate otherwise exact fielding rows by itself; it remains visible for the later predictor-coverage/fallback contract.

## Acceptance criteria

Historical source certification passes only if, for every authorized season × league:

1. both fielding and hitting requests succeed;
2. pagination is complete and nonempty;
3. every fielding row has exact player, team, and authorized position identity;
4. required games/start/innings fields are present and parse under frozen semantics;
5. `games == gamesPlayed`;
6. `0 <= gamesStarted <= gamesPlayed`;
7. baseball innings notation converts exactly to nonnegative defensive outs;
8. DH defensive outs are exactly zero;
9. player × team × position grain is unique within season × league;
10. no source value is guessed, reassigned, or silently dropped to manufacture acceptance.

If any condition fails, persist diagnostics and stop before any position-profile modeling.

## Hard boundary after source certification

A successful source gate authorizes only the next **position-profile design/development contract**.

It does not authorize:

- choosing a lookback or recency curve after examining future validation outcomes;
- fitting future position shares;
- combining `games_started` and `fielding_outs` into one undocumented weight;
- predicting defense;
- changing Playing Time v1;
- forcing player forecasts into team totals;
- building a team allocator.
