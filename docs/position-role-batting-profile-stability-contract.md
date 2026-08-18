# Batting position / role profile stability audit contract

Last updated: 2026-08-18

Status: **DEVELOPMENT-ONLY DESCRIPTIVE AUDIT — 2025 UNTOUCHED.**

Upstream certified source: `docs/position-role-historical-source-result.json`.

## Question

Before introducing another predictive model, measure how much a hitter's observed position/role profile changes from one completed season to the next.

This audit does not select hyperparameters, fit a statistical model, or access 2025.

## Batting-role positions

Use only:

- C
- 1B
- 2B
- 3B
- SS
- LF
- CF
- RF
- DH

Pitcher (`P`) usage is excluded from the batting position-role channel. A two-way player's batting role can still be represented by any non-P/DH position evidence; pitching value remains a separate future channel.

## Player-season role profile

Aggregate certified fielding usage across all teams and actual leagues within the season.

For each player-season:

1. If total batting-position `games_started > 0`, role events are `games_started` by position.
2. Otherwise, if total batting-position `games_played > 0`, use normalized `games_played` as an explicit fallback for players with no starts.
3. Otherwise, the player has no batting-role profile and is excluded from pairwise stability scoring rather than assigned a guessed role.

`role_probability = position_role_events / total_role_events`.

The evidence mode (`games_started` or `games_played_fallback`) must remain explicit.

## Primary position

Primary position is the position with the largest role-event count.

Deterministic tie break, in order:

1. larger `games_started`;
2. larger `fielding_outs`;
3. larger `games_played`;
4. lower numeric position code.

This primary-position label is diagnostic only; the full profile remains the preferred role representation.

## Defensive-position profile

Separately, for C through RF only, normalize certified `fielding_outs` when a player has positive defensive outs.

Do not mix defensive outs and games started into one weight. DH has no defensive outs.

## Development transitions

Audit only:

- 2021 -> 2022
- 2022 -> 2023
- 2023 -> 2024

A player enters one transition only if the relevant profile exists in both seasons.

No 2025 fielding/position source may be queried.

## Frozen metrics

For each transition and pooled across all three:

- paired player count;
- current and next-season evidence-mode distribution;
- exact primary-position match rate;
- primary-position transition matrix;
- mean and median total-variation distance of the full 9-position batting-role profile;
- 75th and 90th percentile total-variation distance;
- current-season primary-position concentration (mean/median top share);
- exact primary-position match among players whose current primary share is at least 0.75;
- defensive-profile paired count;
- mean/median defensive-profile total-variation distance.

Also report player-season source coverage and fallback-mode frequency for each season.

## Interpretation boundary

This audit is intended to decide architecture, not to crown a model.

After the results are persisted:

- if year-to-year role profiles are highly stable, prefer a transparent carry-forward/smoothing design and freeze its confirmation rule before 2025 access;
- if instability is material and systematic, define a separate development contract for a richer position projection before touching 2025.

No team allocator is authorized by this audit.
