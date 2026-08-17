# Current Talent Minor League Savant source checkpoint

Last updated: 2026-08-16  
Status: **SOURCE CAPABILITY PROBE PASSED.**

## Decision

The official Baseball Savant Minor League Statcast detail CSV is viable as a tracked-evidence source for a **coverage-limited richer Current Talent tier**.

It is **not** a universal MiLB tracking source for the 2021–2023 validation window. Baseline 2 remains the required fallback outside proven tracked environments.

Probe workflow: **31999568328**.  
Live source workflow has been returned to manual-only.

## Official source

Minor League Statcast Search:

`https://baseballsavant.mlb.com/statcast-search-minors`

Verified detail CSV endpoint:

`https://baseballsavant.mlb.com/statcast-search-minors/csv`

The probe used one historical date from each validation season and retained the exact raw CSV bytes before projection.

The raw detail surface contained **119 columns** in each 2021–2023 probe and included the fields needed for a first batted-ball-quality challenger:

- `game_date`;
- `game_pk`;
- `batter`;
- `at_bat_number`;
- `pitch_number`;
- `events` / `description`;
- `bb_type`;
- `launch_speed`;
- `launch_angle`;
- pitch location / velocity fields and additional Statcast columns.

Modern bat-tracking column names are also present in the current export schema, but all checked bat-tracking fields (`bat_speed`, `swing_length`, `miss_distance`, `attack_angle`, `attack_direction`, `swing_path_tilt`) were null throughout all three historical probe dates. Header presence therefore must not be confused with historical data availability.

## Reconciliation to certified evidence

For every probe year, **100% of unique Savant `game_pk + batter` pairs reconciled to the already-certified same-season MiLB Current Talent player-game evidence**.

This is a strong identity result: the official Savant detail surface can join directly onto the project's existing MLBAM/game-PK identity backbone without inventing a new player-resolution system.

## Historical probe results

### 2021-07-01

- raw pitch/detail rows: **1,789**;
- unique game+batter identity match share: **100%**;
- observed certified level: **Single-A only**;
- observed league ID: **123**;
- BBE-like rows: **472**;
- complete EV + launch angle: **434 / 472 = 91.95%**;
- tracked games in sample: **7**;
- tracked batters: **103**.

This matches MLB's published historical coverage statement that Florida State League tracking begins in 2021.

### 2022-07-01

- raw pitch/detail rows: **5,971**;
- unique game+batter identity match share: **100%**;
- observed certified levels: **AAA + Single-A**;
- BBE-like rows: **1,494**;
- complete EV + launch angle overall: **1,043 / 1,494 = 69.81%**.

The aggregate missingness is misleading because coverage is structurally different inside AAA:

| certified environment | BBE-like | complete EV+LA | share |
|---|---:|---:|---:|
| AAA league_id 112 | 491 | 489 | **99.59%** |
| AAA league_id 117 | 557 | 111 | **19.93%** |
| Single-A league_id 123 | 446 | 443 | **99.33%** |

This is exactly the sort of pattern the architecture must preserve. MLB documents 2022 tracking as Florida State League + Pacific Coast League + Charlotte home AAA games, not all AAA. The ~20% coverage in one AAA league cannot be treated as random row-level missingness.

### 2023-07-01

- raw pitch/detail rows: **5,910**;
- unique game+batter identity match share: **100%**;
- observed certified levels: **AAA + Single-A**;
- BBE-like rows: **1,814**;
- complete EV + launch angle: **1,811 / 1,814 = 99.83%**.

By certified environment:

| certified environment | BBE-like | complete EV+LA | share |
|---|---:|---:|---:|
| AAA league_id 112 | 423 | 421 | **99.53%** |
| AAA league_id 117 | 903 | 902 | **99.89%** |
| Single-A league_id 123 | 488 | 488 | **100%** |

This matches MLB's published 2023 entitlement: all AAA plus Florida State League.

## Reuse-first package audit

A useful public implementation was found after the initial inventory:

**`ss77995ss/baseball-stats-python`**  
`https://github.com/ss77995ss/baseball-stats-python`

Its `minor_statcast_search.py` implements the same official Minor League CSV endpoint directly and provides:

- date range validation;
- season / game-type / level filters;
- tracked-data flagging;
- batter and pitcher lookup helpers;
- the explicit official endpoint `https://baseballsavant.mlb.com/statcast-search-minors/csv`.

Relevant source file:

`https://github.com/ss77995ss/baseball-stats-python/blob/main/src/baseball_stats_python/statcast/minor_statcast_search.py`

The implementation adds explicit `hfFlag=is..tracked|` / `chk_is..tracked=on` parameters and is a valuable reference for the production request shape.

Decision on reuse:

- **reuse its proven request semantics / filter construction** rather than rediscovering the Savant form;
- do not automatically add the package as a runtime dependency yet, because the existing project already has a small provenance-aware Savant capture pattern and uses Polars rather than pandas;
- before production materialization, compare our thin request wrapper with this public implementation on the same tiny dates so we know we have not omitted a meaningful tracked-only filter;
- retain exact response bytes and explicit schema projection in our repo even if request construction is borrowed.

This is consistent with the project's reuse-first rule: borrow mature solved behavior without importing unnecessary runtime surface area.

## What is now proven

The source gate proves:

1. the official Minor League detail CSV endpoint is live and scriptable;
2. EV/LA fields are populated on historical tracked batted balls;
3. MLBAM batter IDs and game PKs reconcile cleanly to the certified model backbone;
4. historical tracking coverage follows league/venue entitlements rather than a universal level flag;
5. 2023 AAA/FSL EV/LA measurement completeness is extremely high in the probe;
6. 2021 FSL is usable but has visibly more measurement missingness than 2023;
7. 2022 AAA must carry finer capability metadata than `level_group=AAA`;
8. modern bat-tracking data cannot be retroactively assumed merely because new columns appear in today's CSV schema.

## What is not yet proven

Do not over-read a three-date probe. It does **not** establish:

- full-season capture completeness;
- exact tracked-venue entitlement for every 2022 game;
- exact EV/LA missingness across every park/date;
- feature stabilization thresholds;
- an EV/LA model form;
- that EV/LA improves Current Talent proper scores;
- that swing/pitch-process rows have physically faithful sequence semantics at all tracked minor-league environments.

Those are separate gates.

## Next gate

The first richer Current Talent challenger should now be designed around **batted-ball quality** rather than another source search.

Before bulk collection, predeclare:

1. exact observed features derived from EV/launch angle;
2. minimum tracked-BBE evidence required at an as-of date;
3. capability handling for 2021 FSL / 2022 FSL / 2022 partial AAA / 2023 full AAA / MLB;
4. whether richer evidence modifies the 12-component profile estimate, adds a separate contact-quality latent term, or both;
5. development and confirmation chronology that does not exploit the 2023 expansion of AAA tracking;
6. promotion metrics against frozen B2 on identical richer-eligible samples.

Do not bulk-download the entire source until this challenger contract decides what fields and dates are actually needed.