# First MiLB Source POC Findings

## Status

This document records empirical findings from the source-certification proof of concept. It is evidence for architecture decisions, not a declaration that the source is fully certified.

Primary reusable source under test: `armstjc/milb-data-repository`.

Official comparison source: MLB Stats API `game/{gamePk}/playByPlay`, fetched through the stable low-level `MlbDataAdapter` transport from `python-mlb-statsapi` and projected into a deliberately small set of PA and pitch-event fields by this project.

The tests now cover recent Triple-A, Double-A, High-A, Single-A, and Rookie/complex/DSL source files, plus an official PBP-to-boxscore batting reconciliation across MLB through Rookie-level games. Older-history, batted-ball, identity, and finer tracking-coverage certification remain open.

## Triple-A bootstrap slice

The first asset, `2025_3_aaa_pbp.csv`, has:

- 25,636 rows and 103 columns;
- 43 unique games;
- 12,818 exact duplicate extra rows;
- 12,818 duplicate natural-key extra rows using `(game_pk, at_bat_number, pitch_number)`;
- zero conflicting natural-key duplicates.

The duplication is therefore deterministic in this slice: removing exact duplicate rows for **comparison only** leaves 12,818 unique pitch rows. Code review of the upstream collector found a matching cause: a successful game dataframe is concatenated once inside the `try` block and again immediately afterward.

This does **not** authorize destructive raw-data deduplication. The raw release remains quarantined and its checksum/provenance must be retained. If armstjc is promoted later, duplicate collapse will be an explicit, tested source-normalization transform.

## PA outcome field defect

The release's `events` column is not a usable PA-outcome field in the tested slices. The upstream parser reads the PA result but later writes a pitch-event variable into `events`; ordinary pitch rows therefore leave it blank.

The official feed's PA result fields (`result.event`, `result.eventType`, description) are present and cleanly keyed by `game_pk + atBatIndex`. The reusable source should therefore be treated as a useful **pitch-grain historical table**, not as the sole authority for PA outcomes.

## Triple-A official comparison

Using all 43 games in the original AAA asset, the narrow official adapter successfully read all 43 games, including irregular MiLB payloads that broke the high-level typed client.

At the official-feed state used by that POC:

- 3,282 official PAs were observed;
- 3,281 had a corresponding armstjc pitch-grain PA key;
- all shared PAs had matching current official physical-pitch counts;
- the one official-only PA occurred in game `779653` and was a zero-pitch intentional walk;
- no positive-pitch PA omission was identified in that release slice.

A later routine five-game AAA smoke test again matched 372/372 PAs with zero pitch-count mismatches.

The official feed can be corrected after a game is played, so these are retrieval-time comparisons rather than a promise that a future retrieval will be byte-for-byte identical. This reinforces the requirement to record retrieval time, source asset/version, and checksum for historical validation.

## Why the canonical model needs separate PA and pitch grains

An edge-case audit of game `779653` found a signaled intentional walk at `atBatIndex=69` with zero events marked as pitches. A table whose grain is one row per pitch cannot represent that PA at all.

This is not a defect that should be "fixed" by inventing a pitch row. The canonical data model needs a PA table that exists independently of the pitch table. Pitch rows attach to PAs when pitches exist; a valid PA may have zero pitch children.

See ADR 002.

## Validation bug found in our own POC

The first comparison incorrectly used the MLB feed's `pitchIndex` list length as the official pitch count and reported 28 mismatched PAs in a five-game sample. Inspecting the actual `playEvents` showed that `pitchIndex` can retain references that do not correspond one-for-one with the current events marked `isPitch=true`.

After changing the comparison to count current `playEvents` where `isPitch=true`, the five-game sample and then the full 43-game comparison showed zero pitch-count disagreements among shared PAs.

This is an important certification precedent: discrepancies are investigated before either source is "repaired." In this case the reused source was right and our first validator was wrong.

## Official Python client evaluation

### High-level `python-mlb-statsapi` objects

The high-level typed `get_game_play_by_play()` path is too strict to be the foundation for universal MiLB ingestion. Game `780856` contains legitimate pitch-type objects such as `{"description": "Unknown"}` without a `code`. The Pydantic model requires the code and rejects the entire game.

### SportsDataverse

SportsDataverse successfully handled both tested edge games, including game `780856`, and remains a strong candidate for Baseball Savant / Minor League Statcast enrichment. Installing the full package solely for official PBP verification, however, pulls a much larger scientific/modeling dependency graph than the narrow job requires.

### Chosen official PBP utility for this stage

Use the stable public low-level `MlbDataAdapter` from `python-mlb-statsapi` for HTTP sessions, retries, timeouts, and structured failures, but do **not** use its strict high-level PBP object model. The project owns only a small projection of raw `playByPlay` JSON into fields needed for certification and PA enrichment.

This is intentionally not a custom full-feed parser. It is a narrow adapter over already-solved HTTP plumbing, and it tolerates optional/missing nested fields rather than encoding the complete MLB JSON schema.

## Adjacent-file / snapshot audit

The `2025_3_aaa_pbp.csv` and `2025_4_aaa_pbp.csv` assets do not behave like disjoint calendar partitions.

After duplicate collapse **for comparison only**:

- the March asset contains 12,818 pitch keys from March 28-30 plus 729 pitch keys dated April 23;
- the April asset contains 114,003 pitch keys spanning April 1 through May 1;
- the same 729 April 23 natural keys occur in both assets;
- 663 overlapping rows are identical across the two source snapshots;
- 66 overlapping rows have one or more changed values.

The changed values are narrow:

- 65 overlapping pitches differ only in `play_end_datetime`;
- one pitch changes `release_spin_rate` from 738 to 744 and `spin_axis` / `spin_dir` from 17 to 20;
- no observed overlapping row changes player identity, PA outcome, pitch number, velocity, movement, plate location, or batted-ball fields.

This supports treating upstream release files as **versioned source snapshots**, not as canonical month partitions. Source filename/month remains provenance only. Normalized data should be organized by actual event date/season/level, while repeated observations of the same natural key retain source asset, retrieval time, and checksum so later corrections do not contaminate historical as-of backtests.

See ADR 003.

## Cross-level certification

A second audit tested one recent source asset at each lower affiliated level, using three date-spread games per asset against the current official feed.

| Source slice | Raw rows | Unique games | Exact duplicate extra rows | Conflicting pitch-key groups | Official PAs sampled | Pitch-count mismatches |
|---|---:|---:|---:|---:|---:|---:|
| 2025 April Double-A | 206,574 | 339 | 104,490 | 3,286 | 241 | 2 |
| 2025 April High-A | 210,356 | 342 | 103,820 | 4,186 | 212 | 0 |
| 2025 April Single-A | 213,492 | 345 | 103,554 | 4,923 | 227 | 0 |
| 2024 Rookie/complex/DSL asset | 337,308 | 818 | 177,544 | 0 | 233 | 0 |

Across these samples, **913/913 official PA keys were present in the reusable source**. There were no source-only PAs and no positive-pitch official-only PAs in the selected games. Two shared Double-A PAs had one more physical pitch in the current official feed than in the reusable source.

This is strong evidence that the reusable files preserve the underlying PA/pitch sequence well enough to continue evaluating them as a historical bootstrap, but it is not yet full historical certification.

### Natural-key conflicts at AA, High-A, and Single-A

The lower-level assets reveal an important distinction between exact duplicate rows and multiple payload versions for one pitch key.

After exact duplicates are removed for diagnosis only:

- Double-A has 3,286 pitch keys with two distinct payload rows;
- High-A has 4,186;
- Single-A has 4,923;
- every tested conflict has exactly two payload variants;
- in all three files, the **only field that changes across those variants is `play_start_datetime`**.

A pitch therefore cannot be counted by the number of distinct payload rows. For comparison and eventual resolved views, the baseball grain is the natural key `(game_pk, at_bat_number, pitch_number)`. Multiple source observations of that key remain preserved for provenance; they do not become multiple pitches.

The certification code now explicitly profiles these conflicts and counts pitch sequence at natural-key grain rather than relying on whole-row deduplication.

### Two Double-A current-feed pitch differences

The three-game Double-A sample found two PAs in game `783272` where the current official feed contains one physical pitch that is absent from the reusable asset:

- PA 43: pitch 6, `W`, "Swinging Strike (Blocked)";
- PA 6: pitch 2, `X`, "In play, out(s)".

Both current official events contain pitch data but no pitch-type code. Upstream parser review shows that a missing pitch-type code alone should not cause an `isPitch=true` event to be skipped, so these cannot yet be attributed to a simple parser filter. The most plausible classes are a source-snapshot/feed-revision difference or another upstream collection edge case; that remains an inference until more examples are tested.

The practical design implication is to treat official reconciliation mismatches as explicit quality evidence rather than forcing exact historical identity to the current feed. Two missing pitch events in a small sample are worth flagging, but they do not justify rebuilding the historical collector from scratch.

## Rookie/complex/DSL identification

The available `2024_6_rk_pbp.csv` asset demonstrates that the upstream `rk` bucket is not one homogeneous league and is not a literal June partition:

- actual game dates run from June 1 through August 8, 2024;
- `game_month` contains June, July, and August;
- `league_name` explicitly contains Arizona Complex League, Florida Complex League, and **Dominican Summer League**;
- the common `league_level_name` is `Rookie`.

This resolves one earlier source-audit uncertainty: DSL games are present inside the reusable Rookie grouping and can be recovered from row-level league/team metadata. Canonical level/league classification must therefore use those row-level fields, never the filename's `rk` label alone.

## Tracking coverage is structurally heterogeneous

The presence of a column in the 103-column source schema does not imply that the measurement exists for that level, park, or season.

Observed row coverage in these slices illustrates the problem:

- AAA release speed: ~99.94%; release spin: ~87.60%; launch speed/angle: ~15.96%;
- AA release speed/spin/launch speed: 0%;
- High-A release speed/spin/launch speed: 0%;
- Single-A release speed: ~29.67%; release spin: ~27.97%; launch speed: ~4.56%;
- Rookie/complex/DSL release speed/spin: ~1.38%; launch speed: ~0.22%.

This is why tracking is an evidence tier rather than a universal feature set. Coverage metadata must be modeled by season/league/park/source, and absence cannot be imputed as ordinary missing-at-random data.

## Narrative-description differences are not a primary reconciliation key

The cross-level samples contain description-string differences even where PA keys and pitch sequence agree. The Rookie sample has 59 description differences among 233 PAs, with inspection showing formatting/whitespace differences as a major cause. Names, accents, punctuation, and text corrections can also change while the structured event remains the same.

Narrative descriptions remain useful for debugging and edge-case interpretation, but canonical reconciliation should prioritize structured IDs, event codes, counts, and baseball state rather than exact description-string equality.

## Official PBP → boxscore batting reconciliation

The first aggregate-stat reconciliation exposed another useful validator mistake before it reached the data model.

A naive version counted every Stats API `allPlays` row as a PA. That worked for the MLB and Single-A controls but over-counted selected AAA, AA, High-A, and Rookie batting lines by one or more PAs/ABs. The extra rows had structured result event types such as `pickoff_1b`, `game_advisory`, `caught_stealing_2b`, `caught_stealing_3b`, and `other_out`.

Crucially, these rows can still carry `result.type="atBat"`, so neither array row count nor `result.type` is a safe PA rule.

The Stats API's `/eventTypes` endpoint already solves this classification problem by attaching a `plateAppearance` flag to each event code. We stored a dated 2026-08-15 snapshot of those official semantics and changed reconciliation to:

1. count only result event types MLB marks as plate appearances;
2. keep known runner/game result rows but exclude them from batting PA accounting;
3. fail certification on blank or previously unseen event codes instead of guessing;
4. reconstruct AB from `PA - BB - HBP - SH - SF - CI`;
5. compare PA, AB, H, 2B, 3B, HR, BB, IBB, HBP, K, SH, SF, and CI to official team boxscore totals.

After that change, **all 22 home/away batting lines across 11 representative games reconciled exactly on all 13 audited totals**, with no blank or unknown result event types. The sample spans MLB, AAA, AA, High-A, Single-A, and Rookie-level games and includes the irregular MiLB game `780856` that broke the strict high-level PBP client.

This clears the initial aggregate-stat reconciliation gate for the narrow official PA projection. It does not prove all historical event types or source seasons behave identically, which is why unknown-code detection and older-slice testing remain required.

See ADR 004.

## What is now established

The POC has enough evidence to make several foundation decisions without pretending the source is perfect:

1. `armstjc/milb-data-repository` is viable enough to continue as the preferred **historical MiLB pitch bootstrap candidate**.
2. Raw/source observations stay quarantined and versioned; resolved views operate at explicit natural grains.
3. Canonical PAs and pitches are separate tables.
4. Official MLB Stats API is the modern reconciliation/gap-fill authority, reached through a narrow low-level adapter rather than a full custom parser.
5. Source filenames are provenance, not canonical time/level partitions.
6. DSL/ACL/FCL classification comes from row-level league metadata.
7. Tracking coverage must be explicit evidence metadata.
8. Exact narrative text is not a certification target.
9. Stats API `allPlays` rows are not automatically PAs; official event-type semantics govern PA accounting.
10. The narrow official PA projection can reproduce official boxscore batting totals in the first cross-level reconciliation suite.

## Remaining concerns before promotion

The reusable historical source is still **quarantined**. The next foundation gates are:

- older historical-slice testing for schema/behavior drift;
- explicit per-league sampling inside level buckets, especially a confirmed DSL game rather than only a mixed Rookie asset;
- batted-ball direction/category validation before a FaBIO-like profile depends on it;
- player identity crosswalk validation;
- tracking availability profiling at park/league/season grain rather than only release-slice grain;
- source-data terms/redistribution review.

Cross-level recent sequence testing, initial aggregate batting reconciliation, DSL presence/identification, adjacent-file overlap, event-type PA semantics, and natural-key conflict handling are no longer open conceptual blockers; they are now certification rules.

## Current provisional architecture

1. quarantined reusable pitch-grain history from armstjc, explicitly certified rather than trusted wholesale;
2. a source-observation/provenance layer that preserves repeated snapshots and conflicting payload versions;
3. canonical PA records keyed independently and enriched/certified from the official feed;
4. canonical pitch records attached to PA records where pitches exist, with one resolved pitch per natural pitch key in current views;
5. official MLB API access through a narrow low-level adapter for verification, PA outcomes, gap filling, and incremental updates;
6. versioned official event-type semantics for reproducible PA accounting and drift detection;
7. richer tracking sources such as Savant/SportsDataverse added later as optional evidence tiers.

The next source-certification work should focus on **older history and explicit league coverage**, not production-scale backfill yet.
