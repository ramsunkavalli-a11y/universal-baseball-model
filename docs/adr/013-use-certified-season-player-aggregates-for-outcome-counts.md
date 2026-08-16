# ADR 013: Use certified season-player aggregates for reusable historical outcome counts

**Status:** Accepted for foundation architecture  
**Date:** 2026-08-15

## Context

The canonical foundation should not fetch and replay every historical official game when a mature reusable aggregate can supply the same player-season outcome counts accurately.

`armstjc/milb-data-repository` publishes season-player batting and pitching releases in addition to pitch-level history. The files use compact source names (`batting_PA`, `pitching_BF`, and similar) and player/team/league/season grain. Before reuse, the repository required an explicit schema adapter and a completed-season comparison to current official totals.

The newest uniformly populated completed season across the four target source classes is **2024**. The 2025 Rookie batting asset is a one-byte placeholder, so 2025 cannot be used as a uniform completed-season certification set.

The completed 2024 gate covered:

- AAA batting: **965** rows;
- Rookie batting: **1,762** rows;
- AAA pitching: **1,377** rows;
- Rookie pitching: **2,151** rows;
- total: **6,255** player/team/league/season rows.

All four source classes had zero duplicate groups at the standardized `season + league_id + team_id + player_id` grain.

Batting exposes every component required for the exact identity `PA = AB + BB + HBP + SH + SF + CI`. All **2,727** audited batting rows satisfied that identity exactly.

Pitching does not expose `pitching_SH`, so exact source-only decomposition of `BF = AB + BB + HBP + SH + SF + CI` is not available and is not inferred.

For official reconciliation, the gate deterministically selected one high-volume player from every actual league represented in each source class. Players who appeared in multiple actual leagues in the same source class were excluded because the official person-season endpoint is queried at the broader sport level (Triple-A or Rookie).

The final gate produced **10/10** exact player-season reconciliations:

- five batting samples, each matching **14** mutually available official fields with zero differences;
- five pitching samples, each matching **13** mutually available official fields with zero differences;
- sample coverage complete for every actual league represented by the four source files.

The certification script now fails if source grain is not unique, available accounting identities fail, a source league lacks a deterministic official sample, or any sampled mutual field differs.

## Decision

Use standardized armstjc season-player aggregates as the preferred reusable historical backbone for **mutually available player/team/league/season outcome counts** when a populated asset exists.

The adapter must:

1. preserve the upstream files as immutable evidence;
2. explicitly map source aliases to descriptive canonical fields;
3. preserve the `season + league + team + player` grain;
4. parse integer-like serialized values such as `125.0` without silently truncating genuinely fractional values;
5. leave absent fields absent rather than fabricating zeros or derived events;
6. record source snapshot/provenance and adapter version.

The accepted aggregate role includes counts such as PA/BF, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SF, games and games started where present, plus other fields that receive separate field-level certification before model use.

The aggregate role does **not** replace pitch/play-sequence evidence needed for:

- Pull/Center/Opposite direction;
- exact contact-event mapping;
- foul-air eligibility;
- state transitions or RE24 estimation;
- conflict adjudication at pitch/play-sequence grain;
- any field absent upstream, including pitching sacrifice bunts in the audited schema.

## Consequences

- Historical Performance backfills do not need official all-game PBP merely to recover standard non-contact outcome totals.
- Official PBP can remain targeted to state/run-value calibration, source certification, and fields that genuinely require play-level evidence.
- Pitch-level reusable history remains necessary for contact trajectory/direction and other event-shape features.
- Empty or placeholder release assets are data-availability failures, not zero-stat seasons; downstream ingestion must reject them.
- Heavy source/reconciliation audits are manual after certification, while deterministic adapter/unit tests remain in normal CI.
