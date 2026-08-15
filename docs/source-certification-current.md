# Current Source Certification State

Last updated: 2026-08-15

This document is the current checkpoint for the foundation-layer source work. Earlier POC reports remain useful evidence, but this file reflects the latest semantics and architecture decisions after the edge cases found during live certification.

## Current source roles

| Need | Current preferred source / method | Status |
|---|---|---|
| Historical affiliated MiLB physical-pitch bootstrap | `armstjc/milb-data-repository` release assets | Viable with explicit normalization/certification; still quarantined |
| Official modern play/result authority | MLB Stats API | Accepted authority |
| Official HTTP utility | low-level `python-mlb-statsapi` `MlbDataAdapter` | Accepted for narrow transport; strict high-level PBP objects rejected |
| PA / non-PA semantics | versioned MLB Stats API `/eventTypes` snapshot | Accepted |
| Cross-system player IDs | pinned public Chadwick Register | Accepted enrichment/crosswalk strategy |
| Richer Minor Statcast later | Baseball Savant, likely via SportsDataverse/helper logic | Evaluated but not yet promoted |
| Historical MLB backtesting | Retrosheet + Chadwick | Planned; not part of the MiLB bootstrap gate |

The governing principle remains:

> **Canonical authority: MLB Stats API. Canonical working data: our normalized tables, built wherever practical from mature public parsers/datasets and continuously certified against official representations.**

## What is established about the reusable MiLB pitch source

### Sequence and pitch fidelity

The reusable source preserves physical pitch sequence very well in the tested samples.

Recent testing spans AAA, AA, High-A, Single-A, ACL, FCL, and DSL. Explicit Rookie-league checks matched the official feed in both 2023 and 2024 samples, including:

- 2024 DSL game `773530`: 83/83 official true-PA sequence keys represented, zero pitch-count disagreements;
- 2024 ACL game `772320`: 64/64, zero disagreements;
- 2024 FCL game `771821`: 81/81, zero disagreements;
- 2023 DSL game `741849`: 69/69, zero pitch-count disagreements in the original sequence audit;
- 2023 ACL game `743157`: 74/74;
- 2023 FCL game `742555`: 87/87.

Older-era testing also remained structurally strong:

- 2015 September AAA: sampled official sequences matched with zero pitch-count disagreement;
- 2005 September AAA: after applying correct official PA semantics, 161/161 true official PAs shared the source sequence key and every shared sequence matched physical-pitch count.

The historical bootstrap is therefore not a recent-season-only convenience.

### Deterministic duplicates and mutable snapshots

Released files cannot be treated as canonical monthly partitions.

Observed examples include:

- `2025_3_aaa_pbp.csv`: 25,636 raw rows → 12,818 exact-unique rows, a perfect 2× duplication;
- `2005_9_aaa_pbp.csv`: 32,292 raw rows → 16,146 exact-unique rows, also a perfect 2× duplication;
- adjacent 2025 AAA assets overlap on actual game date and can carry revised values for the same natural pitch key.

The source natural pitch key is:

`game_pk + at_bat_number + pitch_number`

Raw observations are preserved with source asset, retrieval time, and checksum. Resolved/current views may collapse repeated observations deterministically, but raw source history is never destructively “cleaned.”

See ADR 003.

### PA outcome column is not reusable

The upstream source's `events` field is not a trustworthy PA outcome. Code review shows the parser reads the PA result but later writes a pitch-event variable into the exported `events` column.

PA/result semantics therefore come from the official play-sequence layer, not from this source column.

### Known batter-ID parser defect

The upstream parser changes `batter_id` for every `offensive_substitution`. This includes pinch-runners, which are not the batter.

Live identity comparison found exactly three batter mismatches in the first targeted audit and all three were explained by this same bug:

- 2025 AAA `781756:47`: source batter `687714` is pinch-runner Jackson Cluff; official batter `656448` is Stone Garrett;
- 2023 DSL `741849:14`: source batter `808695` is pinch-runner Enmanuel Santos; official batter `808665` is Angel Acosta;
- 2023 ACL `743157:59`: source batter `699108` is pinch-runner Eddy Isturiz; official batter `665912` is Miguel Hernandez.

Across those samples, pitcher identity was 601/601 against the official true-PA matchup identity. Raw source participant IDs remain provenance/debug evidence; canonical sequence batter identity comes from the official structured play sequence.

This defect is a reason to use the hybrid architecture, **not** a reason to rebuild the entire historical parser.

## Canonical event grain is now `play_sequence`, not PA

Two opposite edge cases are both real:

1. A true PA can have **zero physical pitches**, e.g. a signaled intentional walk.
2. A physical pitch can occur in a sequence that **does not become a PA**, e.g. 2023 ACL game `743157`, atBatIndex `26`: a ball is thrown and the inning ends on `caught_stealing_2b` before the batter completes a PA.

Therefore the minimum lossless relationship is:

`game -> play_sequence -> 0..N pitches`

with:

`plate_appearance = play_sequence where official is_plate_appearance = true`

The parent sequence is keyed by `game_pk + atBatIndex`. Source-only groupings should be called **pitch-bearing sequences**, not “source PAs.”

See ADR 006, which refines ADR 002.

## Official PA semantics and aggregate reconciliation

Stats API `allPlays` rows are not automatically plate appearances. Runner/game results such as pickoffs, caught stealings, and advisories can appear in the same array and can even carry `result.type="atBat"`.

The project now uses a dated snapshot of MLB's `/eventTypes` `plateAppearance` semantics. Blank or previously unseen result event types fail certification until reviewed rather than being guessed.

Using those semantics, the PBP-derived batting aggregation reconciled **22/22 home/away team batting lines across 11 representative MLB/MiLB games exactly on all 13 audited totals**:

PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SH, SF, CI.

See ADR 004.

## Direct batted-ball fields

The first direct-field audit compared reusable-source batted-ball fields against current official `hitData` on five AAA games.

After correcting our validator to treat categorical fielding-location values numerically (`9.0` and `9` are the same code):

- 349/349 current official in-play pitch keys were present in the source sample;
- zero source conflicts affected the audited batted-ball fields;
- batter side, trajectory, location, coordinates, distance, exit velocity, and launch angle matched whenever both snapshots had values, except one historical launch-angle value that changed from -47° to -50° in the current official feed.

That remaining difference is consistent with the broader evidence that source snapshots and the current official feed can contain later revisions. It is preserved as provenance rather than silently overwritten.

The direct fields are viable evidence. **Derived pull/center/opposite spray classification is not yet certified.**

## Tracking is an evidence tier, not a universal feature set

The common source schema does not imply common sensor availability.

Observed row coverage in representative recent assets includes roughly:

- AAA: release speed ~99.9%, spin ~87.6%, launch speed/angle ~16%;
- AA: tested slice essentially 0% for release speed/spin/launch metrics;
- High-A: tested slice essentially 0%;
- Single-A: release speed ~29.7%, spin ~28.0%, launch speed ~4.6%;
- Rookie/complex/DSL: release speed/spin ~1.4%, launch speed ~0.2%.

Structural source/park/level absence must not be imputed as ordinary missing-at-random data. The remaining tracking gate is to profile availability at park/league/season grain rather than only by release asset.

## Player identity and Chadwick

MLBAM is the canonical modern event identity. Chadwick is a versioned cross-system enrichment layer.

The first live audit pinned Chadwick public commit:

`2e8e73355f9c77b963115377bd98c784cfeec10f`

The snapshot contained:

- 518,743 public people rows;
- 129,658 MLBAM-linked rows;
- 129,658 unique MLBAM IDs;
- zero duplicate MLBAM IDs.

Official structured IDs from representative AAA, DSL, and FCL games matched Chadwick **83/83** in the first sample. Missing future links remain `crosswalk_pending`; the system never fuzzy-matches a player name automatically.

See ADR 005.

## Provenance and reproducibility rules already accepted

1. Preserve raw/reusable source files in quarantine with checksum and retrieval metadata.
2. Treat upstream assets as mutable snapshots, not canonical calendar partitions.
3. Normalize at explicit baseball natural grains rather than by whole-row count.
4. Keep official current data separate from historical source snapshots; a current-feed disagreement is evidence, not automatic permission to rewrite history.
5. Version event-type semantics and identity crosswalks used in historical/as-of evaluation.
6. Never silently fix unknown event codes, participant mismatches, or ambiguous identities.
7. Heavy live-source audits are manual workflows; ordinary commits run only fast deterministic unit CI.

## Remaining foundation gates before production-scale backfill

The historical MiLB source itself has passed enough viability testing that broad package hunting is no longer the highest-value activity. Remaining work should be focused:

1. **Derived batted-ball direction/category:** evaluate existing public implementations first, then certify any pull/center/opposite transform before a FaBIO-like Performance layer depends on it.
2. **Tracking coverage map:** profile season/league/park/source availability so every model feature knows its evidence tier.
3. **Canonical schema/provenance contract:** formalize `play_sequence`, `pitch`, source observations, current/as-of resolved views, and quality flags before a large backfill.
4. **External-ID spot checks:** verify representative Chadwick→FanGraphs/BBRef/Retrosheet links before those joins become production dependencies.
5. **Attribution/terms manifest:** carry armstjc MIT and Chadwick attribution requirements with source metadata.

Only after those gates should we do a production-scale historical backfill. The backfill should use the already-certified reusable history rather than re-downloading and re-parsing every raw MLB/MiLB game from scratch.
