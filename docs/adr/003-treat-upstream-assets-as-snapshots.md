# ADR 003: Treat Reused Upstream Assets as Versioned Snapshots, Not Canonical Partitions

- Status: Accepted for foundation design
- Date: 2026-08-15

## Context

The first adjacent-file audit compared `2025_3_aaa_pbp.csv` with `2025_4_aaa_pbp.csv` from `armstjc/milb-data-repository`.

The filenames do not describe disjoint calendar partitions:

- the March asset contains games from March 28-30 plus 729 pitch keys from April 23;
- the April asset spans April 1 through May 1;
- all 729 April 23 pitch keys in the March asset also occur in the April asset;
- 663 of those overlapping rows are identical;
- 66 carry different values in one or more non-key fields.

The 66 revisions are narrow in this audit: 65 change only `play_end_datetime`; one pitch changes `release_spin_rate` from 738 to 744 and `spin_axis`/`spin_dir` from 17 to 20. No outcome, player identity, pitch-number, velocity, movement, location, or batted-ball field changed among the overlapping rows.

A later inventory audit showed that GitHub asset chronology is not a safe replacement for filename chronology. For example:

- `2025_3_aaa_pbp.csv` was created before `2025_4_aaa_pbp.csv`, matching filename-period order;
- `2023_7_rk_pbp.csv` was recreated in 2025, while `2023_8_rk_pbp.csv` was created in 2023, so asset creation order reverses filename-period order.

A direct comparison of those re-uploaded 2023 Rookie assets found 5,524 overlapping natural pitch keys. All 5,524 full rows differ because team labels changed, but among fields currently projected into the canonical pitch observation only three differ: `hit_location` on 1,747 keys, `pitcher_hand` on 14, and `batter_side` on 2. The accepted coordinate direction evidence (`hc_x`, `hc_y`), pitch characteristics, pitch result, trajectory and player IDs did not appear among the changed columns.

The source therefore behaves as a collection of overlapping, mutable snapshots with imperfect chronology metadata rather than as a clean series of disjoint monthly partitions.

## Decision

### Preserve source observations before resolving them

Every ingested upstream asset must retain provenance sufficient to distinguish observations of the same natural key, including at minimum:

- source name;
- source asset/file name;
- source asset URL or stable identifier where available;
- source asset creation/update metadata where available;
- our `retrieved_at` timestamp;
- source file checksum;
- normalization version.

Raw/quarantined data are append/preserve, not overwrite.

### Canonical partitioning uses baseball event time, not source filename

Normalized tables are partitioned/queryable by actual baseball fields such as `game_date`, season and level. A source filename month is never used as proof that a row belongs to that calendar month.

### Multiple observations of one natural key are first-class

If the same natural key appears in multiple source assets, all source observations remain auditable. No whole-row winner is chosen merely because one asset was downloaded later, created later on GitHub, or has a higher filename month.

### Current source working view uses field consensus, not inferred chronology

For overlapping snapshots from the same source family and the same normalizer/schema version, the default source-only working view is resolved field by field:

- if all non-null observations agree, that value resolves;
- null plus one non-null value resolves to the observed value;
- if two non-null observations disagree, that field remains null in the resolved source view and is explicitly flagged as a conflict;
- the contributing source snapshot and normalization IDs remain attached to the derived record;
- no asset timestamp, retrieval timestamp, filename period or row order is used as a tie-breaker.

This is intentionally conservative. It lets stable evidence such as pitch shape or Gameday coordinates survive an unrelated team-label or base-state revision without pretending that one entire source row is globally newer or more correct.

Official-source evidence may later adjudicate a conflicted field in a separate authority-aware transform. It is not silently mixed into source consensus.

### Historical/as-of analysis must remain reconstructable and honestly labeled

Backtests and frozen historical rankings must distinguish event time from knowledge time.

For source snapshots collected contemporaneously, the foundation should preserve:

- event time: when the baseball event occurred (`game_date`, pitch/play timestamps where useful);
- knowledge time: when this project could have known a particular source observation (`source_updated_at`/`retrieved_at` and provenance).

For historical assets first retrieved years after the games occurred, current corrected history cannot prove the exact information set available at the historical cutoff. Those tests are **event-cutoff retrospective backtests**, not true vintage-information-set backtests, unless a contemporaneous archive is separately available.

### Conflicts are measured, not assumed harmless

Cross-snapshot differences are profiled by field and source. Core identity/outcome/key conflicts receive more scrutiny than labels, timing metadata or optional enrichment fields. Conflict rates become explicit source-quality outputs during backfill rather than being silently repaired.

## Consequences

- Upstream collection quirks cannot create duplicate canonical pitches merely because assets overlap.
- We do not need a brittle global ordering rule for re-uploaded release assets.
- Stable fields can be used even when unrelated fields disagree across snapshots.
- Source filenames and GitHub asset timestamps remain useful provenance but are decoupled from canonical storage and row selection.
- The normalized design requires a source-observation layer plus a derived consensus view and explicit quality/conflict records.
- Official-source adjudication remains separate from source-only consensus.
- Backfill can proceed without first proving a total chronological order across all 624 historical assets.

## Non-decision

This ADR does not define an authority hierarchy for every conflicted field, nor does it claim that all historical source revisions are harmless. Those rules remain field- and source-specific and are introduced only after empirical certification supports them.
