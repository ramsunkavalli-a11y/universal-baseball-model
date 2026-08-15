# Current Source Certification State

Last updated: 2026-08-15

This document is the current checkpoint for the foundation-layer source work. Earlier POC reports remain useful evidence, but this file reflects the latest semantics, source-resolution rules, and canonical contracts after the edge cases found during live certification.

## Current source roles

| Need | Current preferred source / method | Status |
|---|---|---|
| Historical affiliated MiLB physical-pitch bootstrap | `armstjc/milb-data-repository` release assets | Accepted bootstrap with explicit normalization, provenance, and conflict handling |
| Official play/result authority | MLB Stats API | Accepted authority |
| Official HTTP utility | low-level `python-mlb-statsapi` `MlbDataAdapter` | Accepted for narrow transport; strict high-level PBP objects rejected |
| PA / non-PA semantics | versioned MLB Stats API `/eventTypes` snapshot | Accepted |
| Cross-system player IDs | pinned public Chadwick Register | Accepted enrichment/crosswalk strategy |
| Richer Minor Statcast later | Baseball Savant, likely via SportsDataverse/helper logic | Evaluated; optional enrichment, not a universal foundation dependency |
| Historical MLB backtesting | Retrosheet + Chadwick | Planned separately from the MiLB bootstrap |

The governing principle remains:

> **Canonical authority: MLB Stats API. Canonical working data: our normalized tables, built wherever practical from mature public parsers/datasets and continuously certified against official representations.**

## Foundation gates now passed

The reusable-source viability question is no longer open-ended package hunting. The following have been tested and promoted into explicit architecture decisions:

1. physical-pitch history is reusable across MLB-affiliated levels including DSL;
2. official PA/non-PA semantics reconcile to official boxscore batting totals;
3. source files are overlapping mutable snapshots, not trustworthy calendar partitions;
4. exact duplicates and repeated payload variants are preserved/compacted deterministically rather than silently dropped;
5. `play_sequence` is the lossless parent grain, not plate appearance;
6. MLBAM is the primary modern event identity and Chadwick is a versioned crosswalk;
7. Gameday `hc_x/hc_y` supports a near-universal coordinate-derived Pull/Center/Oppo direction signal;
8. source-only cross-snapshot resolution is field consensus, not inferred chronology;
9. source conflicts can be adjudicated by separate official authority where structured official evidence exists;
10. canonical provenance, typed schemas, Parquet persistence, DuckDB querying, and event-cutoff/vintage semantics have working tests and live POCs.

## Reusable MiLB pitch source

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

- `2025_3_aaa_pbp.csv`: 25,636 raw rows -> 12,818 exact-unique rows, a perfect 2x duplication;
- `2005_9_aaa_pbp.csv`: 32,292 raw rows -> 16,146 exact-unique rows, also a perfect 2x duplication;
- adjacent assets overlap on actual game date and can carry revised values for the same natural pitch key.

The source natural pitch key is:

`game_pk + at_bat_number + pitch_number`

Raw observations are preserved with exact source snapshot and normalization provenance. Canonical partitioning uses actual baseball event date, never the release filename period.

### PA outcome column is not reusable

The upstream source's `events` field is not a trustworthy PA outcome. Code review shows the parser reads the PA result but later writes a pitch-event variable into the exported `events` column.

PA/result semantics therefore come from the narrow official play-sequence layer. This is one of the limited places where the project uses the official feed directly because the reusable source does not contain a trustworthy structured substitute.

### Known batter-ID parser defect

The upstream parser changes `batter_id` for every `offensive_substitution`, including pinch-runners that are not the batter.

Live identity comparison found three batter mismatches in the targeted audit and all three were explained by this same bug. Pitcher identity was perfect in that sample. Raw source participant IDs remain provenance/debug evidence; canonical sequence participant identity comes from the official structured matchup.

This defect is a reason to use the hybrid architecture, **not** a reason to rebuild the entire historical parser.

## Canonical event grain

Two opposite edge cases are both real:

1. a true PA can have **zero physical pitches**, e.g. a signaled intentional walk;
2. a physical pitch can occur in a sequence that **does not become a PA**, e.g. a pitch followed by an inning-ending caught stealing before the batter completes a PA.

Therefore the minimum lossless relationship is:

`game -> play_sequence -> 0..N pitches`

with:

`plate_appearance = play_sequence where official is_plate_appearance = true`

The parent sequence is keyed by `game_pk + atBatIndex`. Source-only groupings are **pitch-bearing sequences**, not “source PAs.”

See ADR 006, which refines ADR 002.

## Official PA semantics and aggregate reconciliation

Stats API `allPlays` rows are not automatically plate appearances. Runner/game results such as pickoffs, caught stealings, substitutions and advisories can appear in the same array.

The project uses a dated snapshot of MLB's `/eventTypes` `plateAppearance` semantics. Blank or previously unseen result event types fail certification until reviewed rather than being guessed.

Using those semantics, the PBP-derived batting aggregation reconciled **22/22 home/away team batting lines across 11 representative MLB/MiLB games exactly on all 13 audited totals**:

PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SH, SF, CI.

See ADR 004.

## Batted-ball evidence and universal direction

Direct reusable-source batted-ball fields matched current official `hitData` extremely well in live comparison. One historical launch-angle observation differed from the current official feed, consistent with later feed revision rather than a reason to overwrite source history.

The universal direction transform is now accepted:

- use Gameday `hc_x/hc_y` coordinates;
- use the established Bill Petti / pybaseball spray-angle transform, including its `0.75` calibration factor;
- derive Pull/Center/Oppo relative to batter handedness;
- do **not** use `hit_location` as the production direction fallback;
- do **not** use approximate foul-line geometry to decide fair/foul status.

Coordinate coverage among in-play balls is approximately 99% in tested 2005/2015 AAA slices and essentially 100% in tested recent levels, including Rookie/complex/DSL. Coordinate direction therefore belongs in the universal PBP evidence layer rather than the optional sensor/tracking tier.

Trajectory mapping is also empirically supported:

- `popup` -> IFFB core family;
- `fly_ball` -> OFFB core family;
- bunts remain an explicit special family rather than being forced into GB/LD/IFFB;
- flagged foul airborne outs remain real Performance events but are not forced into the FaBIO 12-bin core view.

See ADR 007 and ADR 008.

## Tracking remains an enrichment tier

The common source schema does not imply common sensor availability. Release speed, spin, launch speed/angle and related tracking fields vary sharply by level, park, season and feed availability.

Structural absence is not missing-at-random and must never be imputed as though every player had equal tracking opportunity. A more detailed park/league/season coverage map remains useful before tracking features enter Current Talent models, but it is **not a blocker for the universal outcome/profile historical backfill**.

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

## Cross-snapshot resolution: no inferred “latest row”

An inventory of the public MiLB PBP release contained 624 recognized assets spanning 2005-2025. GitHub asset timestamps are useful provenance but are not a trustworthy chronology for source truth. A concrete counterexample is `2023_7_rk_pbp.csv`, which was recreated in 2025 after the original `2023_8_rk_pbp.csv` asset from 2023.

A direct comparison of those two Rookie assets found:

- 5,524 overlapping natural pitch keys;
- all 5,524 raw full rows differ, driven largely by changed team labels and other non-model source fields;
- after canonical normalization, 5,524 pitches resolve cleanly with only **16 pitches (0.29%)** retaining any canonical field conflict;
- those 16 conflicts are only `pitcher_hand` (14 pitches) and `batter_side` (2 pitches).

The source-only resolution policy is therefore `non_null_field_consensus_v1`:

- all non-null observations agree -> resolve the value;
- null plus one non-null observed value -> resolve the observed value;
- multiple distinct non-null values -> leave the field null and flag it explicitly;
- never use retrieval time, GitHub asset creation time, filename period or row order as a tie-breaker.

The 16 pitch-level hand conflicts reduce to **7 unique play-sequence/field disputes**. Current structured MLB Stats API matchup evidence matched exactly one source snapshot in **7/7** cases. In this particular audit all seven official values matched the re-uploaded July asset, but that does **not** make the July asset a global row winner. It establishes only that official structured matchup evidence can adjudicate these hand fields when source consensus fails.

See ADR 003 and the cross-snapshot resolution audit.

## Canonical provenance and storage contract

The project now separates:

- immutable `source_snapshot` identity;
- `normalization_definition` identity for our parser/schema interpretation;
- typed source observations at `game`, `play_sequence`, `pitch`, and player-crosswalk grains;
- explicit `quality_issue` records;
- derived source-consensus views rather than destructive deduplication.

A parser-version change therefore creates a new normalization without pretending the upstream bytes changed.

Canonical table writes use atomic Zstandard Parquet with schema/content fingerprints. DuckDB can query persisted canonical artifacts. Live one-game POCs have validated the real source -> canonical observation -> Parquet/DuckDB path.

The temporal contract also distinguishes:

- **event-cutoff retrospective backtests** using current corrected historical data restricted by event date;
- **true vintage information-set backtests** only when the evidence's historical availability can actually be demonstrated.

Current historical release assets are not mislabeled as true historical vintages merely because their games occurred in the past.

## Provenance and reproducibility rules

1. Preserve raw/reusable source files in quarantine with checksum and retrieval/source metadata.
2. Treat upstream assets as mutable snapshots, not canonical calendar partitions.
3. Normalize at explicit baseball natural grains rather than by whole-row count.
4. Keep official authority separate from source-only consensus; an official disagreement is explicit adjudication evidence, not permission to rewrite raw history.
5. Version event-type semantics and identity crosswalks used in historical evaluation.
6. Never silently fix unknown event codes, participant mismatches, field conflicts or ambiguous identities.
7. Keep structural missingness/coverage separate from player skill.
8. Ordinary commits should run fast deterministic CI; heavy live-source audits should be manual or narrowly triggered.

## Next foundation milestone

The next highest-value step is **not** more generic source hunting. It is a limited multi-asset historical-database POC that exercises the accepted contracts together before a large backfill:

1. ingest a deliberately awkward pair of overlapping source assets;
2. persist source snapshots and normalization definitions;
3. materialize game and pitch observations partitioned by actual event date;
4. build the field-consensus pitch view and explicit quality/conflict records;
5. retrieve and persist the narrow official play-sequence/result layer for the POC games;
6. validate official semantics and batting reconciliation;
7. round-trip the resulting Parquet tables through DuckDB and verify repeatability.

In parallel with that POC, freeze the **minimum universal Performance event taxonomy** that the first model actually needs. Do not expand the historical database just to warehouse unused source fields.

Tracking coverage maps, richer Statcast, external FanGraphs/BBRef/Retrosheet crosswalk spot checks, defense, and Current Talent enrichment remain later gates for the layers that depend on them. They are no longer blockers for the first universal outcome/profile database.
