# Historical MiLB Source Drift Audit

## Purpose

Before treating `armstjc/milb-data-repository` as a historical bootstrap, test whether an older season still behaves like the recent source slices already certified. This audit deliberately samples history instead of starting a production backfill.

Audit slice: August-labeled 2023 assets for Triple-A, Double-A, High-A, Single-A, and Rookie.

Official comparison: current MLB Stats API play-by-play through the project's narrow low-level adapter. Comparisons are retrieval-time evidence; the official feed may contain later corrections that were not present when the historical source snapshot was collected.

## Result

All five historical source jobs completed. The core 103-column pitch schema and natural pitch key `(game_pk, at_bat_number, pitch_number)` remain usable across the 2023 files.

| 2023 source slice | Rows | Games | Exact-duplicate extras | Conflicting pitch keys | Official PAs sampled | Pitch-count mismatches |
|---|---:|---:|---:|---:|---:|---:|
| Triple-A | 119,339 | 386 | 0 | 0 | 162 | 0 |
| Double-A | 118,217 | 393 | 402 | 98 | 175 | 2 |
| High-A | 112,939 | 382 | 833 | 142 | 147 | 1 |
| Single-A | 112,796 | 377 | 1,326 | 0 | 123 | 0 |
| Rookie | 99,561 | 663 | 6,370 | 0 | 154 | 0 |

Across the ten date-spread games in the main historical sample, **761/761 current official PA keys were present in the reusable source**. No sampled game had a source-only PA or an official-only PA. Three shared PAs had different pitch counts versus the current official feed: two in Double-A and one in High-A.

The two Double-A differences are current official physical pitches absent from the historical snapshot: an `X` in-play out and an `S` swinging strike. The High-A difference goes the other direction: the historical source contains pitch number 6 while the current official feed ends that PA at pitch 5. These look like the same class of snapshot/feed-revision discrepancy already seen in the recent source audit, not evidence that the historical sequence is broadly unusable.

## Historical schema drift found

The 2023 files use two misspelled source columns:

- `leauge_id` instead of `league_id`;
- `leauge_name` instead of `league_name`.

Recent files use the corrected spellings. This initially caused the explicit Rookie league sampler to find no `league_name` groups even though the underlying information was present.

The project now has a small, explicit source-schema alias layer. It standardizes only known aliases and never rewrites quarantined raw files. If an old and new spelling coexist, overlapping nonblank values must agree; a disagreement is a hard error rather than a silent preference rule.

After applying those certified aliases, the 2023 Rookie file resolves the same three competitions seen in recent history:

- Arizona Complex League — sampled game `743157`: 74/74 official PA keys, zero pitch-count mismatches;
- Dominican Summer League — sampled game `741849`: 69/69 official PA keys, zero pitch-count mismatches;
- Florida Complex League — sampled game `742555`: 87/87 official PA keys, zero pitch-count mismatches.

This explicitly confirms usable DSL coverage in both the recent 2024 Rookie source and the older 2023 source.

## File labels are not partitions in 2023 either

The August-labeled Double-A, Single-A, and Rookie assets contain July game dates as well as August dates. The recent-source rule therefore holds historically too: **asset filename is provenance, not canonical event time**. Canonical partitions must come from row-level game date/season/league fields after explicit schema normalization.

## Natural-key conflict behavior is stable

Historical Double-A and High-A contain multiple distinct payload rows for some pitch keys. As in the recent lower-level audit, every tested 2023 conflicting key has exactly two payload variants and the only changed field is `play_start_datetime`.

This strengthens the existing rule that source row count is not baseball event count. Raw observations remain preserved; resolved pitch views operate at the natural pitch key and retain provenance for every source observation.

## Tracking coverage remains evidence-tiered

The 2023 files reinforce that tracking availability is structural, not ordinary missing data:

- Triple-A has essentially complete pitch tracking and about 16% row coverage for launch speed/angle;
- Double-A and High-A have no pitch tracking in this source slice;
- Single-A has pitch tracking on about 23% of rows and launch speed/angle on about 3.5%;
- Rookie has pitch tracking on about 2.1% of rows and launch speed/angle on about 0.3%.

The same canonical player model therefore cannot assume a common feature vector across levels, parks, or seasons.

## Decision after this gate

The 2023 audit does **not** reveal a historical-schema break that justifies replacing the reusable source with a ground-up collector. It does reveal exactly the kind of drift the certification layer was designed to catch: explicit column aliases, mutable/overlapping asset scope, duplicate observations, and a small number of current-feed pitch revisions.

`armstjc/milb-data-repository` remains the preferred historical MiLB pitch bootstrap candidate, still quarantined until the remaining semantic gates are completed.

The next high-value source gate is **batted-ball classification and direction**, because a FaBIO-like universal Performance/Profile layer will depend on those fields. That validation should determine whether existing structured fields/coordinates can be reused directly and where lower-level stringer quality requires uncertainty or eligibility rules before any model is built.
