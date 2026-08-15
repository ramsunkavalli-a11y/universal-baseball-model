# Source Certification Plan

## Purpose

Reusable public baseball data should save us engineering time **without transferring unknown upstream errors into the model**. This plan defines the minimum evidence required before a source can move from candidate to production working input.

Certification is source-specific and version-specific. A source that passed for 2025 AAA is not automatically certified for 2012 A-ball or 2026 DSL.

## Source states

Every external dataset/adapter should be treated as one of four states:

1. **Candidate** — researched but not empirically tested.
2. **Quarantined** — downloaded/accessible and being tested; not allowed to feed canonical model tables.
3. **Certified with scope** — accepted only for explicitly listed seasons/levels/fields.
4. **Rejected / reference-only** — useful as an implementation oracle or benchmark but not a working input.

Certification should never be a single global boolean.

## First certification target

The first target is `armstjc/milb-data-repository` PBP because it offers the largest potential reduction in historical MiLB engineering work and therefore deserves the most scrutiny first.

The direct official-access candidates (SportsDataverse and `python-mlb-statsapi`) should be tested in the same POC as verification/fallback adapters, not as competing historical backfills.

## Test slices

Use completed seasons for the main certification so official totals are relatively stable. Add a small current-season slice separately to test incremental access/update behavior.

Initial matrix:

| Slice | Why it exists |
|---|---|
| 2025 AAA, one full month | High-volume modern MiLB; should be best-covered |
| 2025 AA, A+, A, one week each | Tests lower full-season levels and missing tracking |
| 2025 DSL + ACL/FCL, one week each if exposed | Tests the project's hardest taxonomy/coverage requirement |
| 2019 AAA + A, one week each | Pre-2021 minor-league reorganization and older feed shape |
| 2012 AAA + A, several games each | Older archive/schema behavior without making the first POC enormous |
| 2025 MLB, several games | Control sample with stronger independent comparison options |
| 2026 AAA, several recent finalized games | Current incremental/release-update behavior only |

If an intended slice does not exist in a candidate source, that is itself a coverage result. Do not silently substitute another level.

## Required provenance captured before validation

For every downloaded artifact/batch, record:

- source/project name;
- exact release asset or endpoint;
- retrieval timestamp in UTC;
- upstream commit/tag/package version where applicable;
- file size;
- SHA-256 checksum;
- expected season/month/level scope;
- local immutable raw path;
- whether the artifact was downloaded directly or generated through a package;
- package parameters used for generated data.

The first POC may store this as a small manifest file. The final pipeline can later promote the same fields into a provenance table.

## Test group A — file and row integrity

### A1. File scope

Verify that the observed `game_date`, season, and level/league metadata are consistent with the advertised filename/query scope.

**Pass:** no unexplained out-of-scope games.

### A2. Game-key uniqueness

Enumerate unique `game_pk` and compare with the official finalized schedule for the same scope.

Classify every difference as:

- cancelled/postponed/not final;
- official game with no PBP available;
- source omission;
- source extra/duplicate;
- taxonomy/filter mismatch;
- unresolved.

**Pass:** no silent unexplained games. A source may still be certified for partial historical coverage if missing games are explicitly measurable and downstream coverage flags preserve that absence.

### A3. Pitch-key duplicates

For rows representing pitches, test the strongest available natural key, expected to be approximately:

`game_pk + at_bat_number/atBatIndex + pitch_number`

also inspect source `play_id` where available.

Measure:

- exact duplicate rows;
- duplicate natural keys with identical payloads;
- duplicate natural keys with conflicting payloads.

**Pass for certified pitch input:** zero unexplained duplicate pitch keys after defining the correct source grain. If upstream duplicates are systematic and perfectly removable by a deterministic key, document the defect and certify only the normalized deduplicated representation—not the raw release as-is.

### A4. Stable row grain

Confirm whether rows are true pitches, all `playEvents`, or a mixture. Automatic strikes/balls, pitch-clock violations, pickoffs, substitutions, and non-pitch actions should not be silently misclassified as physical pitches.

**Pass:** every row type used by the model has an explicit grain and classification rule.

## Test group B — official statistical reconciliation

Aggregate PBP to player-game and team-game totals and compare against official final boxscore/stat totals.

Core fields:

- PA/BF where reconstructable;
- AB;
- H;
- 2B;
- 3B;
- HR;
- BB;
- HBP;
- K;
- runs and outs as diagnostic fields;
- pitch count where the official comparison is appropriate.

### Acceptance rule

For deterministic batting/pitching outcomes in a selected finalized game, the expectation is **exact agreement**, not an arbitrary percentage tolerance. These sources derive from the same official scoring system, so a mismatch is evidence to investigate.

A certification run can still pass with documented exceptions when the discrepancy is caused by a known scoring correction, unavailable PBP, suspended-game handling, or a definitional mismatch. The exception must be explainable and reproducible.

Do not make the acceptance standard looser merely to get a source to pass.

## Test group C — event taxonomy completeness

Inventory distinct official event/result codes and map them to the first universal Performance taxonomy.

At minimum distinguish:

- strikeout and strikeout variants;
- walk / intentional walk;
- HBP;
- single / double / triple / home run;
- field out;
- force out / ground into double play / other multi-out plays;
- reached on error;
- fielder's choice;
- sacrifice bunt / sacrifice fly;
- catcher interference and other rare PA-ending events;
- non-PA events such as stolen bases, pickoffs, balks, wild pitches, substitutions, and pitch-clock violations.

**Pass:** every observed PA-ending event has either a deliberate model mapping or a deliberate excluded/other category. Unknown events are surfaced as validation failures rather than silently coerced.

## Test group D — identity integrity

For every pitch/PA row used downstream:

- batter MLBAM ID present when a batter exists;
- pitcher MLBAM ID present when a pitcher exists;
- IDs resolve to official person records;
- repeated names do not drive joins;
- Chadwick crosswalk coverage is measured separately rather than required for ingestion.

**Pass:** no model join relies on player name. Missing Chadwick mappings can be allowed and flagged; missing official source IDs in otherwise valid pitch rows require investigation.

## Test group E — level and league taxonomy

This is especially important for Rookie-ball data.

For each `game_pk`, preserve:

- source sport/level ID;
- league ID and name;
- team IDs;
- parent organization where available;
- season.

Build an observed mapping table rather than hard-coding the assumption that `sportId=16` means one homogeneous league.

**Pass:** DSL and domestic complex leagues can be separated for the seasons in which the project claims coverage. Historical leagues that do not map cleanly to the modern ladder remain explicit historical categories.

## Test group F — measurement coverage

Do not validate tracking fields through one global non-null percentage.

For fields such as:

- release velocity;
- release position;
- plate location;
- movement;
- spin;
- exit velocity;
- launch angle;
- hit coordinates;

compute coverage by at least:

`season × league/level × venue`

and where useful by month.

**Pass:** structural missingness is identifiable. The canonical layer can distinguish "not measured/not available" from ordinary missing observations.

A low tracking-coverage slice does **not** fail universal PBP certification if outcome/event data are otherwise complete; it simply remains in a lower evidence tier.

## Test group G — direct-access adapters

Compare SportsDataverse and `python-mlb-statsapi` on a small common set of games/tasks.

Evaluate:

- access to exact official `game_pk` feeds needed for reconciliation;
- preservation of raw JSON when requested;
- timeout/retry/error behavior;
- handling of missing/old fields;
- schedule queries across MiLB sport IDs;
- ease of retrieving boxscores/person metadata;
- dependency weight and API stability;
- whether output normalization obscures information we need.

For Minor League Statcast, explicitly test SportsDataverse's truncation-aware chunking against a narrow range where a direct query is known to be below the cap, then a wider range likely to require chunking.

**Decision rule:** choose the smallest stable adapter surface that solves the task. It is acceptable to use one package for Stats API transport and another for Savant tracking if that is cleaner than forcing one dependency to do everything.

## Test group H — independent MLB control

On the MLB control games:

- compare official feed-derived outcomes to Retrosheet where the event representation permits;
- compare selected pitch parsing against `baseballr` or another mature parser;
- distinguish disagreements caused by different source systems from parsing bugs.

This is not needed for every MiLB game. Its purpose is to validate our interpretation and test harness on a data environment with more independent references.

## Certification output

Every certification run should produce a compact machine-readable summary plus a human-readable report with:

- source/version/scope;
- row/game/player counts;
- duplicate diagnostics;
- reconciliation counts and mismatches;
- unmapped event codes;
- identity failures;
- coverage by level/park for important measurements;
- known exceptions;
- final status: `candidate`, `quarantined`, `certified`, or `rejected`;
- exact certified scope.

Do not rely on notebook output as the permanent record.

## Promotion rule

A source can feed canonical tables only when:

1. its row grain is understood;
2. duplicates are controlled by explicit keys;
3. core outcomes reconcile to official totals for the tested scope;
4. level/league mapping is understood for the claimed scope;
5. structural measurement coverage is documented;
6. provenance is reproducible;
7. all known exceptions are encoded as tests or source-quality flags.

Promotion does **not** mean the source is trusted forever. Scheduled ingestion should continue running lightweight reconciliation and schema/coverage drift checks.

## What we are deliberately not doing yet

- Full historical backfill.
- Production DuckDB/Parquet schema.
- Model feature engineering.
- Custom reimplementation of MLB's nested feed.
- Complex imputation for missing tracking.
- Publishing raw source data.

The certification POC should be small enough that a source decision can still be reversed cheaply.
