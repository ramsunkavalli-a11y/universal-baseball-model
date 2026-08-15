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
- 66 carry later values in one or more non-key fields.

The 66 revisions are narrow in this audit: 65 change only `play_end_datetime`; one pitch changes `release_spin_rate` from 738 to 744 and `spin_axis`/`spin_dir` from 17 to 20. No outcome, player identity, pitch-number, velocity, movement, location, or batted-ball field changed among the overlapping rows.

Release metadata also shows that these assets were produced after the nominal filename month rather than being frozen month-end extracts. The filename is therefore source metadata, not a safe temporal boundary for our canonical database.

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

If the same natural key appears in multiple source assets, both source observations remain auditable.

A current working view may select the latest successfully normalized observation for that key, provided no certification rule marks the conflict as unresolved or invalid. This selection is a view/transform, not deletion of earlier source state.

### Historical/as-of analysis must remain reconstructable

Backtests and frozen historical rankings must be able to use only evidence that was available by the relevant cutoff. Later source corrections must not silently leak into earlier model snapshots.

The data foundation therefore needs two distinct temporal concepts:

- event time: when the baseball event occurred (`game_date`, pitch/play timestamps where useful);
- knowledge time: when this project could have known a particular source observation (`source_updated_at`/`retrieved_at` and provenance).

### Conflicts are measured, not assumed harmless

Later observations are not automatically declared more correct. Cross-snapshot differences are profiled by field and can trigger source-specific certification rules. Core identity/outcome/key conflicts receive more scrutiny than late-filled tracking or timing metadata.

For the tested March-April overlap, the observed revisions are compatible with using the later observation in a current view while retaining the earlier observation for provenance/as-of reconstruction.

## Consequences

- Upstream collection quirks cannot create duplicate canonical pitches merely because assets overlap.
- We can take advantage of later feed corrections without destroying historical reproducibility.
- Source filenames remain useful for retrieval/provenance but are decoupled from canonical storage layout.
- Certification must inspect adjacent/successive source assets before a new source is promoted.
- The eventual normalized storage design should support a source-observation layer plus resolved/current PA and pitch views rather than one destructive deduplication pass.

## Non-decision

This ADR does not yet freeze the complete observation-table schema, the final conflict-resolution hierarchy, or retention policy for large raw files. Those will be designed after cross-level and historical certification show how often revisions occur and which fields are affected.
