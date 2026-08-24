# Hitter v2 source contract

Status: **FROZEN FOR STAGE 1 REVIEW — SOURCE MATERIALIZATION ONLY**  
Version: `hitter_v2_source_contract_v1`  
Date: 2026-08-23

## Scope and estimand boundary

This contract defines the ordinary-PBP/official-aggregate base and the optional
tracking channel. It authorizes no Hitter v2 model fit, score, ranking, WAR
conversion, or protected confirmation access.

PBP is the guaranteed universal route wherever affiliated PBP exists. Official
player-game/season aggregates are independent reconciliation authority and may
repair an explicitly identified missing terminal event when the repair is
unique. Tracking may enrich the same terminal-outcome forecast only where its
capability and evidence are certified. Missing tracking is never a zero-valued
feature, never a reason to drop a player, and never changes the estimand.

## Canonical grains and keys

### Terminal PA

Unique key:

`source_snapshot_id + game_id + at_bat_index`

Required fields:

- source provenance: provider, asset/capture ID, source SHA-256, retrieval
  vintage, schema version;
- chronology: game date, season, as-of eligibility date;
- environment: source sport, actual league ID, level group, team, opponent,
  venue/park, game type;
- identity: canonical batter ID, source batter ID, identity authority and
  resolution status;
- terminal evidence: raw event code, raw narrative, terminal pitch key,
  structured/narrative authority, start/end outs and bases when present;
- canonical outcome, outcome status, modeling eligibility, exclusion/fallback
  reason;
- reconciliation fields for official PA/AB/H/2B/3B/HR/BB/IBB/HBP/K/SF/SH/GIDP;
- capability tier and tracking linkage counts, but no tracking value is required.

Every accepted terminal row has exactly one outcome. Raw unresolved rows remain
in the audit table with `modeling_eligible=false`; they cannot enter an accepted
player-game/season table until uniquely repaired or explicitly accounted as a
known special result.

### Player-game and player-season

Keys:

- `season + actual_league_id + game_id + player_id`;
- `season + actual_league_id + player_id`.

Aggregates retain every terminal category, accepted/unresolved counts, raw
source status, coverage, and reconciliation residuals. Multi-team/league rows
remain separate until an explicitly named aggregation view is requested.

## Exhaustive terminal taxonomy

The accepted outcome enum is:

1. `UBB`
2. `IBB`
3. `HBP`
4. `K`
5. `HR`
6. `3B`
7. `2B`
8. `1B`
9. `ROE`
10. `FC_REACH`
11. `SF`
12. `MULTI_OUT`
13. `OTHER_OUT`
14. `SH_OR_SPECIAL`

`SH_OR_SPECIAL` requires a subtype: `SH`, `CATCHER_INTERFERENCE`,
`BATTER_INTERFERENCE`, `RUNNER_INTERFERENCE`, `OTHER_KNOWN_SPECIAL`, or
`OFFICIAL_UNIQUE_REPAIR`. Blank, conflicting, or non-unique evidence is not
silently mapped to this class; it is retained as unresolved and fails the
accepted table closed.

Structured official terminal event codes are authoritative. The existing
conservative narrative mapping is permitted only where the source lacks a
structured result and maps to exactly one frozen group. The existing contact
mapping is promoted as follows:

- `single/double/triple/home_run` -> `1B/2B/3B/HR`;
- `field_error` -> `ROE`;
- plain `fielders_choice` -> `FC_REACH`;
- `sac_fly` -> `SF`;
- double/triple-play contact -> `MULTI_OUT`;
- field out, force out, and fielder's-choice out -> `OTHER_OUT`.

Strikeout-plus-runner-out plays remain `K` for the batter outcome and retain
runner outs separately; ball-in-play multi-out plays are `MULTI_OUT`. No play
may be credited twice in later batting/baserunning allocation.

## Denominator policy

Three denominators are persisted rather than conflated:

- `official_pa`: all official PA, including IBB and interference under the
  official source's PA definition;
- `observed_terminal_pa`: every PBP terminal PA row, including known specials
  and unresolved audit rows;
- `hitter_talent_pa`: `UBB + HBP + K + HR + 3B + 2B + 1B + ROE + FC_REACH + SF + MULTI_OUT + OTHER_OUT`.

`IBB` and `SH_OR_SPECIAL` are retained and projected only through separate
context/policy channels; they are excluded from the hitter batting-talent
simplex. FanGraphs-style wOBA uses `AB + UBB + HBP + SF`; IBB, SH, and catcher
interference are excluded. UBB is `BB - IBB` and must be nonnegative.

Missing terminal records count against source coverage and official
reconciliation. They never disappear from the denominator. A unique official
player-game residual may repair exactly one missing category and must be tagged
as an official repair. Multiple possible repairs fail closed.

## Source precedence and reuse

1. Certified affiliated PBP plus canonical game/player/league resolution.
2. Structured official PBP result authority for exceptions and MLB.
3. Existing conservative terminal narrative mapping when structured result is
   absent.
4. Official player-game aggregates for unique reconciliation/repair.
5. Official player-season aggregates for final independent reconciliation.

Required existing modules to evaluate/reuse before adding parsing:

- `current_talent_contact_value_source.py`;
- `current_talent_contact_value_materialization.py`;
- `current_talent_contact_value.py`;
- `current_talent_batted_ball_quality.py`;
- `current_talent_batted_ball_scoring.py`;
- `current_talent_contact_value_features.py`;
- `current_talent_contact_value_prediction.py`;
- canonical state replay, RE24, official outcome overlays, league/level identity,
  participant identity, venue metadata, and chronology utilities.

No second player identity, game identity, league mapping, or state replay is
authorized without a documented contradiction in the existing path.

## Reconciliation and acceptance

For every supported season/league/level/team/source tier report:

- observed games and PA;
- accepted outcomes by enum;
- unresolved and excluded outcomes by exact reason;
- identity failures;
- official aggregate coverage;
- residuals for PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SF, SH, and GIDP;
- first/last event dates and source hashes.

Acceptance invariants:

- canonical keys unique;
- all counts integer and nonnegative;
- every accepted PA has exactly one enum and accepted probabilities/counts are
  exhaustive;
- `H = 1B + 2B + 3B + HR` exactly;
- `BB = UBB + IBB` exactly;
- official player-game and season totals reconcile exactly within a persisted,
  enumerated exception table;
- no unresolved identity enters a model-ready table;
- no accepted row has an unresolved terminal outcome;
- source/target joins cannot change cohort composition silently.

An unresolved source slice is still reportable but has status `failed_closed`.
Forecasting code must later fall back to older accepted evidence plus the
declared hierarchical prior; it must not drop the player or invent zero skill.

## Direction/trajectory and state fields

The v1 ten contact direction/trajectory bins remain auxiliary PBP features and
targets. They cannot substitute for terminal outcomes or define run value.
Start/end bases, outs, advances, fielding credits, batted-ball type, and location
are retained for future baserunning/defense gates but cannot be double-counted
in Stage 1 batting.

## Tracking capability channel

Tracking fields are joined only after the PBP row is accepted. Every tracking
feature must declare:

- `capability_tier`;
- provider/capture/source seasons;
- raw and recency-effective event counts;
- observed completeness and source-quality status;
- reliability weight;
- exact fallback reason.

Frozen capability evidence currently supports MLB Statcast and only observed
tracked MiLB game/venue environments (historically FSL, partial AAA in 2022,
AAA plus FSL in 2023). Level labels alone do not imply tracking.

Permitted first increment features are certified result-producing non-bunt
EV/launch-angle summaries from the existing path. Hard-hit/barrel/sweet-spot,
bat speed, discipline, and sprint speed require separate field-level source
certification before entering the fixed search. Missing values remain null and
do not create eligibility.

Production fallback is exact:

`statcast_increment = 0`  
`tracking_reliability_weight = 0`  
`fused_prediction = pbp_prediction`

when usable tracking is absent. Tracking availability itself cannot be a talent
predictor.

## Chronology and protected outcomes

Every output carries `as_of_date`, `target_season`, `data_vintage`, `estimand`,
source seasons, target environment, capability tier, evidence count, reliability
and fallback.

- 2024 offense is disclosed validation evidence.
- 2025 PA/PBP/position/defense evidence has been accessed and is diagnostic-only.
- completed 2026 offense is the protected one-shot confirmation.

No 2026 hitter outcome, participant membership, playing time, park result,
centering cohort, run-value weight, or translation may be accessed until the
fixed development candidate is frozen and review authorizes that exact source
gate.

## Output product contracts

Later products remain distinct:

1. `neutral_batting_talent`: outcome probabilities, wOBA and batting runs/600
   conditional on future PA in a neutral environment;
2. `complete_hitter_rate_value`: batting + baserunning + defense + position on
   a stated rate/exposure basis;
3. `mlb_opportunity`: probability of any MLB PA plus bounded MLB PA and position
   exposure distributions;
4. `expected_mlb_war`: opportunity-weighted WAR under explicit team/league/park
   context.

`forecast_war` and `retrospective_value` use different pipelines and estimands.
All four products require uncertainty, evidence, source tier, fallback, as-of
date, target season, and data vintage.

## Redistribution

Raw MLB/Statcast payloads remain private quarantine unless terms are reviewed.
Only hashes, aggregate coverage, contracts, and permissible model outputs are
committed. Existing MIT/ODC attribution and Retrosheet notices remain binding.
