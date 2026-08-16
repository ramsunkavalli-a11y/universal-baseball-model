# ADR 026 — Enrich missing historical PBP league identity only from same-game structured player-game evidence

Status: Accepted  
Date: 2026-08-16

## Context

The initial post-reorganization Current Talent history gate (ADR 025) selected 2021–2024 as the first historical validation era. When the first scoped 2022 Current Talent game-evidence POC was run, both AAA and Rookie/complex exposed a source-schema difference that was not present uniformly in the 2024 path: some armstjc PBP snapshots do not export `league_id`.

Actual league identity is required at game/evidence grain because Current Talent must preserve competitive environment explicitly. It is not safe to infer actual league from the filename level. A filename such as `aaa` is a broad release bucket, not a unique league, and historical MiLB topology changes across eras.

The reusable player-game release for the same games contains structured `game_id` and `league_id`. This supplies a reuse-first structured source for recovering the omitted PBP field without inventing league identity.

## Decision

Historical reusable PBP may receive `league_id` from player-game evidence **only** under the following same-game authority rule:

1. Build a `game_id -> league_id` map from structured player-game rows for the same season/source family.
2. All non-null player-game observations for a game must agree on one league ID. A conflict blocks enrichment.
3. For PBP rows that lack `league_id`, fill only from that unique same-game map.
4. For PBP rows that already expose a native `league_id`, retain the native value and require exact agreement with the same-game player-game map. A disagreement blocks the slice; the player-game value does not silently overwrite PBP.
5. A regular-season PBP game without same-game structured league authority is ineligible for the historical materialization path.
6. **Filename level is never used as league identity.** It remains release-discovery metadata only.
7. Preserve league-identity authority in diagnostics/provenance (`player_game_same_game_structured` or `pbp_native_validated_against_player_game_same_game`).

This is field-level source enrichment, not a whole-row source precedence rule and not an environment translation.

## Evidence

The rule was exercised in workflow run `31967143670` across all five post-reorganization MiLB level groups in a scoped 2022 POC.

Across **112 sampled games**:

- **8,450 PA**;
- **5,273 expected result contacts**;
- **5,273 observed reusable physical contacts** in aggregate;
- **8,259 core profile events**;
- **1 unknown contact**;
- **0 total PA-accounting residual**;
- **14 residual-triggered games** required official play-sequence participant authority;
- **674 / 674** source exception contact sequences received official matchup-batter coverage;
- **12 contact batter attributions** changed after official participant authority.

Level-specific result-contact residuals were small and signed rather than synthetically repaired:

- AAA: 795 expected / 795 observed, residual 0;
- AA: 1,183 / 1,183, residual 0;
- High-A: 1,132 / 1,133, residual +1;
- Single-A: 1,134 / 1,134, residual 0;
- Rookie/complex: 1,029 / 1,028, residual -1.

The strongest direct league-field cross-check occurred in 2022 AAA:

- `2022_5_aaa_pbp.csv` exposed native `league_id`; every regular-season value agreed with the same-game player-game map;
- `2022_6_aaa_pbp.csv` omitted the field; 235,394 regular-season PBP rows received league identity from the same-game structured map with zero missing authority.

Other sampled 2022 historical snapshots commonly omitted native league identity and were filled through the same rule. The player-game maps themselves had zero within-game league conflicts in the POC.

## Why this is preferable

The alternative shortcuts are worse:

- inferring league from filename collapses multiple actual leagues and becomes incorrect across historical reorganizations;
- fetching official PBP for every historical game solely to recover league identity discards a mature reusable structured source and greatly increases network/API work;
- dropping historical PBP without `league_id` would unnecessarily erase otherwise useful contact evidence;
- letting player-game rows overwrite a disagreeing native PBP field would violate the project's field-consensus/provenance architecture.

The accepted rule keeps the reusable history path cheap while remaining auditable and fail-closed.

## Non-decisions

This ADR does **not**:

- certify every 2021–2023 season for model training;
- make player-game data globally authoritative over PBP;
- use filename level as actual league identity;
- define an MLB-equivalent environment translation;
- choose Current Talent recency weights, age effects, shrinkage, or priors;
- alter the participant-authority rule in ADR 021/020;
- extend the post-reorganization map to 2019 or earlier.

## Consequences / next gates

1. Historical MiLB materialization must apply this same-game league-identity gate before projecting contact evidence when native PBP league identity is absent.
2. Full-season 2021–2023 materialization must preserve and report league-authority diagnostics by source snapshot and level.
3. Each season must still pass player-game outcome resolution, contact resolution, participant authority, evidence-contract, chronology, and coverage checks independently.
4. Historical season-level outcome rollups should be reconciled against reusable season aggregates where populated before the evidence is admitted to Current Talent training.
5. The live 2022 POC workflow is manual-only after this certification; deterministic unit tests remain in normal CI.
