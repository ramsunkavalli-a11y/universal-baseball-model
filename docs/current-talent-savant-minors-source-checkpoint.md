# Current Talent Minor League Savant source checkpoint

Last updated: 2026-08-17  
Status: **CORRECTED TRACKED-ONLY SOURCE GATE PASSED.**

## Authoritative live gate

Corrected manual workflow run: **32044627608**.

This run is authoritative for the first richer Current Talent challenger. Earlier capability run `31999568328` remains useful historical evidence, but it predates the final pitch-grain model-BBE and certified-game denominator contract. Green run `32043825707` is explicitly **not** accepted as the final gate because its reports were still schema 0.4 and lacked the certified-game denominator.

The accepted run produced one retained raw official Baseball Savant Minor League CSV for each fixed probe date:

- 2021-07-01
- 2022-07-01
- 2023-07-01

Every accepted report has:

- `report_schema_version = 0.5`;
- `request_semantics = tracked_only_helper_v1`;
- `canonical_model_bbe_contract = result_producing_non_bunt_pitch_grain_v1`;
- exact raw response bytes and SHA256;
- required Savant detail fields present;
- 100% reconciliation of returned `game_pk + batter` identity pairs to certified MiLB player-game evidence;
- a certified-game denominator by season / league / level;
- nonzero canonical result-producing, non-bunt complete EV+LA BBE.

## Source decision

Official Baseball Savant Minor League Statcast detail CSV is viable for a **coverage-limited richer Current Talent tier**.

It is not a universal MiLB tracking source for the validation period. Baseline 2 remains the exact fallback whenever tracked evidence is unavailable or insufficient.

Official endpoint used by the frozen helper:

`https://baseballsavant.mlb.com/statcast-search-minors/csv`

The request uses the proven tracked-only form semantics, including `hfFlag=is..tracked|` and `chk_is..tracked=on`.

## Corrected model-BBE contract

The talent feature surface is not every Savant contact with EV/LA. It is only:

- valid game / batter / PA / pitch identity;
- normalized `type == X`;
- nonblank terminal `events`;
- observed `launch_speed` and `launch_angle`;
- explicit bunt narratives excluded;
- canonical key = `game_pk + player_id + at_bat_number + pitch_number`.

Measured foul/contact rows remain broad source-completeness observations only.

## Accepted probe results

### 2021-07-01

- raw rows: **1,789**; columns: **119**;
- identity reconciliation: **100%**;
- broad BBE-like/contact observations: **472**;
- complete EV+LA observations: **434 / 472 = 91.95%**;
- canonical model BBE: **190**;
- certified games on date: **71** across all affiliated levels;
- returned tracked games: **7**;
- only tracked environment: **Single-A league 123**, **7 / 7 certified games = 100%**;
- AA, AAA, High-A, other Single-A and Rookie Complex environments: **0 returned tracked games**.

### 2022-07-01

- raw rows: **5,971**; columns: **119**;
- identity reconciliation: **100%**;
- broad BBE-like/contact observations: **1,494**;
- complete EV+LA observations: **1,043 / 1,494 = 69.81%**;
- canonical model BBE: **543**;
- certified games on date: **96** across all affiliated levels;
- returned tracked games: **20**;
- tracked environments returned: Single-A league 123 and AAA leagues 112 / 117;
- returned-game denominator on this date: league 123 **5/5**, AAA 112 **5/5**, AAA 117 **10/10**;
- crucial measurement distinction remains: complete EV+LA among broad observations is **99.59%** in AAA 112, **19.93%** in AAA 117, and **99.33%** in Single-A 123.

The game denominator and measurement-completeness diagnostic answer different questions. A game may be present in the tracked-only response while only a subset of its contact observations carry complete EV/LA. Therefore 2022 AAA must retain exact observed environment and measurement provenance; `level_group=AAA` is never a blanket capability flag.

### 2023-07-01

- raw rows: **5,910**; columns: **119**;
- identity reconciliation: **100%**;
- broad BBE-like/contact observations: **1,814**;
- complete EV+LA observations: **1,811 / 1,814 = 99.83%**;
- canonical model BBE: **962**;
- certified games on date: **98** across all affiliated levels;
- returned tracked games: **19**;
- tracked environments returned: Single-A league 123 and AAA leagues 112 / 117;
- returned-game denominator: league 123 **5/5**, AAA 112 **5/5**, AAA 117 **9/9**;
- complete EV+LA among broad observations: **100%**, **99.53%**, and **99.89%** respectively.

## What is now proven

The accepted 0.5 gate proves:

1. the official tracked-only Minor League CSV endpoint is currently live and scriptable;
2. the frozen request helper returns the expected historical detail schema;
3. exact raw bytes can be retained before projection;
4. returned game/player identities reconcile directly to the certified MLBAM/game-PK backbone;
5. complete EV/LA exists on the historical tracked source surface;
6. corrected result-producing/non-bunt pitch-grain BBE can be materialized from the live source;
7. source-game coverage and EV/LA measurement completeness can be audited separately;
8. historical coverage is structurally environment-specific and cannot be promoted to a universal level flag.

## What is not yet proven

The three-date gate does not establish:

- full-season tracked-source capture completeness;
- exact 2022 venue entitlement for every historical game;
- final full-history measurement missingness by environment;
- that EV/LA improves Current Talent proper scores.

Those are the next gates.

## Next action

Run only:

`.github/workflows/current-talent-batted-ball-tracking-materialization-v2.yml`

with:

`source_probe_run_id = 32044627608`

V2 must stop after source materialization and diagnostics. Do not run the 2022 richer development evaluator until the V2 artifact is inspected and its checkpoint confirms full 2021 prior-season MiLB capture, the 2022 development capture boundary, corrected BBE semantics, and certified-game coverage diagnostics.
