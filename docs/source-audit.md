# Source Audit

## Purpose

Before writing play-by-play ingestion or parsing code, determine how much of the difficult collection, cleanup, identity resolution, event reconstruction, and historical backfill has already been solved well enough by public projects.

The default is **reuse first**. We should only build source-specific ingestion where an existing option is unavailable, materially incomplete, unreliable, poorly documented, or unsuitable for reproducible historical work.

This document records the research audit. It is intentionally upstream of pipeline design: the pipeline should reflect the sources that survive certification rather than assuming in advance that we will parse every official feed ourselves.

## Working decision

The current source strategy is:

1. **Official source = reconciliation authority, not necessarily working input.** MLB Stats API and Baseball Savant are the authoritative references for the modern data they expose.
2. **Use mature public work to avoid re-solving collection and parsing.** In particular, evaluate `armstjc/milb-data-repository` as the historical MiLB PBP bootstrap rather than immediately rebuilding its backfill.
3. **Never trust a reusable dataset merely because it is convenient.** Certify it against official game and season totals and inspect known parser edge cases before promotion to a production input.
4. **Keep our own canonical model-facing schema.** Upstream packages are adapters or inputs; their column names and object models do not become our architecture.
5. **Keep source-specific raw/bronze material separable from standardized/silver data.** This lets us replace an upstream source without rebuilding downstream modeling logic.
6. **Tracking is an enrichment tier, not a universal requirement.** Minor League Statcast coverage is structurally incomplete by level, park, and season.
7. **Do not redistribute bulk source data by default.** Software licenses and source-data usage rights are separate questions. Raw/source-derived data remain private during development until redistribution terms are reviewed.

## Evaluation criteria

For each candidate source/package, evaluate:

- Coverage by season and level: MLB, AAA, AA, A+, A, complex leagues, DSL.
- Grain: season, game, plate appearance, pitch, batted ball, tracking.
- Historical availability and whether past data can be reproduced.
- Update cadence and suitability for incremental ingestion.
- Player/game identity fields and cross-source compatibility.
- Important fields exposed for the first Performance model.
- Known missingness, park/level biases, schema changes, or recording-quality issues.
- Ease of use from Python, regardless of the implementation language of the upstream project.
- Licensing, terms, attribution, and redistribution considerations.
- Maintenance/activity and likelihood the project remains usable.
- Amount of transformation we would still need to own.
- Ability to reconcile against official MLB/MiLB totals.

## Candidate assessment

### 1. `armstjc/milb-data-repository`

**Provisional role: first-choice historical MiLB PBP bootstrap candidate, quarantined until certification.**

Why it is attractive:

- It already publishes schedules, season stats, game stats, teams, and pitch-level PBP across AAA, AA, A+, A, historical short-season A, and Rookie-ball groupings.
- Its PBP files are split by season/month/level and expose MLBAM batter/pitcher IDs, `game_pk`, PA/pitch sequence fields, event descriptions, batted-ball type, pitch locations, pitch physics where present, hit coordinates, and tracking fields where the source feed contains them.
- The collection logic is inspectable Python rather than an opaque download.
- It ultimately reads the same MLB Stats API live-game feed we would otherwise have to parse ourselves.
- Historical PBP release assets extend much farther back than we would want to reconstruct manually for a first implementation.
- Its GitHub Actions PBP jobs are still running successfully in 2026, so this is not merely an abandoned historical archive.

Why it cannot be trusted blindly:

- The current `get_month_milb_pbp()` source appears to concatenate a successfully fetched game dataframe once inside the `try` block and then again immediately after the block. If the published release files are generated from this exact path without later correction, that could duplicate rows. **This is a code-review warning, not yet a claim that the release files are duplicated.** The release data must be tested empirically.
- The lineup reconstruction contains at least one suspicious assignment in the home-pitcher branch (`away_fielders[0]` rather than `home_fielders[0]`). It may not affect the core batter/pitcher IDs we need, but it demonstrates that field-level assumptions should be certified rather than inherited.
- The repository groups current rookie-level schedules under Stats API `sportId=16` and labels files `rk`. That does not by itself give us the explicit DSL vs ACL/FCL distinction the project requires. We should use the row-level league/team metadata to recover and validate those distinctions.
- Recent workflows report successful execution and release upload, while the PBP release-asset enumeration inspected during this audit did not obviously expose 2026 files. That publishing/update path should be treated as unresolved until the POC verifies where current files land and whether historical assets are immutable or overwritten.
- Some tracking-style columns exist in the schema even where the underlying park/level does not measure them. Coverage must be measured, not inferred from column existence.

**Decision:** do not fork or rewrite this parser yet. First download small certified slices from its releases, detect duplicates/coverage issues, and compare them against official schedules/boxscores/live feeds. If the data pass, use the release files as a historical bootstrap and own only the normalization/certification layer. If a defect is systematic and cheaply correctable, correct it in our normalization layer rather than rebuilding the whole collector.

### 2. `baseballr`

**Provisional role: reference parser / independent implementation oracle, not a production runtime dependency.**

Why it matters:

- `mlb_pbp()` explicitly supports Major and Minor League games from MLB's live-game feed and flattens pitch-level data into a wide table.
- It represents years of community work understanding the feed's nested structure and edge cases.
- Its documentation explicitly warns that many sensor fields are unavailable in minor-league parks and that its very wide output retains source naming/duplication rather than pretending the data are uniformly clean.
- The project is mature, widely used, MIT-licensed, and actively maintained.

Limitations for us:

- It is an R package while our production stack is Python.
- Its wide output is useful for exploration but should not dictate our canonical schema.
- It still consumes the same underlying official feed, so agreement between it and another Stats API parser is not independent evidence of source correctness; it is mainly evidence about parsing semantics.

**Decision:** use its code/output as a test oracle when an event interpretation is unclear. Do not port the entire package and do not add R to the production stack solely for PBP.

### 3. SportsDataverse / `sportsdataverse-py`

**Provisional role: strong Python utility/enrichment candidate; especially attractive for Stats API metadata and Minor League Statcast.**

Strengths:

- Current Python project with Polars-native outputs and optional raw JSON.
- Broad MLB Stats API surface for schedules, people, teams, rosters, stats, boxscores, and game data.
- Provides Baseball Savant MLB and Minor League Statcast search wrappers.
- Its current Statcast search implementation explicitly handles Savant's 25,000-row response cap by date-chunking, recursively reducing chunk sizes when the cap is hit, and warning if a single day can still truncate. This is exactly the sort of already-solved operational detail we should reuse rather than rediscover.
- Minor-league Statcast returns the standard pitch-level Savant CSV shape and fits our Polars-oriented stack.

Important limitation:

- Its dedicated parsed `mlb_play_by_play()` surface is primarily play/at-bat oriented rather than a complete flattening of every pitch event. It does not, by itself, replace the pitch-level historical MiLB PBP layer.

**Decision:** put SportsDataverse on the short list for the official-source utility layer and make it the leading candidate for Minor League Statcast enrichment. Do not require it to solve the historical universal PBP problem.

### 4. `python-mlb-statsapi`

**Provisional role: strong candidate for reliable direct Stats API transport/typed access and official-source verification.**

Strengths:

- Actively maintained Python wrapper with Pydantic models.
- Recent releases provide shared HTTP sessions, explicit connect/read timeouts, bounded retries, structured HTTP/transport/decode exceptions, and a documented public API contract.
- Exposes game play-by-play along with broad Stats API entities.
- MIT-licensed code.

Limitations:

- It is an API client, not a historical cleaned MiLB database.
- Typed models are useful only if they preserve the fields we need across older and lower-level feeds; this must be tested rather than assumed.
- Its own documentation appropriately separates the wrapper's license from MLB data usage terms.

**Decision:** compare it directly with SportsDataverse during the POC for schedule/game/person/verification tasks. We do not need to pick one permanently before seeing which gives cleaner failure handling and raw-data access for our exact workload.

### 5. `baseball-stats-python`

**Provisional role: secondary Minor League Statcast reference; SportsDataverse currently preferred.**

Strengths:

- Python package focused on Baseball Savant/FanGraphs retrieval.
- Has a dedicated `minor_statcast_search()` against Savant's MiLB CSV endpoint and returns pitch-level data.
- Small, inspectable implementation and MIT-licensed code.

Limitations:

- Its minor search currently exposes only the levels Savant itself tracks through that interface (`AAA` and `A` in its documented enum).
- The implementation performs a single HTTP request for the requested range and does not contain the explicit 25,000-row truncation detection/chunking present in SportsDataverse.
- It is a smaller project with less battle-tested surface area.

**Decision:** retain as an independent reference/fallback, but prefer SportsDataverse's truncation-aware implementation if empirical results agree.

### 6. `pybaseball`

**Provisional role: secondary MLB/Statcast/FanGraphs convenience package, not a core MiLB PBP dependency.**

Strengths:

- Mature, popular Python package with familiar Statcast and leaderboard access.
- Useful for independent MLB-level comparisons and exploratory work.

Limitations:

- It does not solve the universal affiliated MiLB historical PBP problem.
- Using it as a foundational dependency would still leave the hardest lower-level work unresolved.

**Decision:** keep available for research/benchmarking; do not architect the core warehouse around it.

### 7. Retrosheet

**Provisional role: high-quality independent MLB historical benchmark and reconciliation source.**

Strengths:

- Long historical MLB play-by-play and parsed event data.
- Independent representation is valuable for validating our MLB event reconstruction rather than comparing two wrappers around the same live feed.
- Useful for long-horizon model backtesting, historical outcomes, parks, and player/event reconciliation.

Limitations:

- It does not solve affiliated MiLB history.
- Its event schema is different from modern Stats API/Savant data and should remain source-specific until standardized.

**Decision:** use for MLB historical validation and eventually for longer history, but do not let Retrosheet requirements complicate the first MiLB POC.

### 8. Chadwick Register

**Provisional role: primary public cross-source identity authority, alongside our own immutable internal player key.**

Strengths:

- Provides a stable UUID-oriented authority file and cross-references for MLBAM, Retrosheet, Baseball Reference, minor-league Baseball Reference, FanGraphs, and other systems.
- Public version is regularly refreshed and explicitly documents how identities can merge or split as source records improve.
- Public dataset has an attribution license and published history.

Design implication:

- Do **not** make a short Chadwick key, FanGraphs ID, or player name our internal primary key.
- Maintain an internal immutable `player_id`, store `mlbam_id` as the most important modern affiliated-baseball source ID, and attach Chadwick UUID plus other IDs as crosswalks.
- Preserve the version/date of the Chadwick snapshot used so later identity corrections are auditable.

### 9. Direct MLB Stats API

**Provisional role: canonical modern authority and fallback, not the default place to reinvent parsing.**

Strengths:

- Source used by the strongest MiLB public parsers we found.
- Stable game IDs and modern affiliated sport/league/team/person metadata.
- Full live-game JSON exposes more structure than any single standardized table needs.

Costs:

- Direct historical backfill means owning retries, caching, schedule edge cases, nested event reconstruction, schema drift, and correction handling.
- The API's existence does not imply that every tracking field exists at every level/park/season.

**Decision:** preserve the ability to fetch official raw JSON for certification, debugging, and incremental gaps. Do not begin by writing a full historical raw-feed pipeline.

### 10. Baseball Savant Minor League Statcast

**Provisional role: tracking enrichment, never universal evidence.**

Current public coverage is structurally limited. The documented coverage includes all Triple-A beginning in 2023 (with narrower 2022 coverage) and Florida State League Single-A games beginning in 2021. Therefore a missing Statcast field can mean "not measured" rather than "player did not exhibit the skill."

**Decision:** maintain explicit tracking-coverage metadata by season/level/park. Models using these fields belong to richer evidence tiers and must fall back cleanly to universal outcome/PBP models.

### 11. `mcbarlowe/mlb`

**Provisional role: schema/ETL precedent, not a data dependency.**

This public project is MLB-focused but is useful as a worked example of converting the same live-game feed into raw JSON, normalized dimensions, pitch facts, Parquet/database outputs, resumable backfills, and verification tests. Of particular interest, its pitch transformer uses each play's `pitchIndex` to select pitch events and separately reconstructs base/out state rather than blindly flattening every `playEvent`.

**Decision:** borrow lessons and test cases, not its MLB-only warehouse wholesale. It reinforces that raw feeds can remain replayable while the analytical schema stays narrow and explicit.

### 12. `baseballquery`

**Status: unresolved / deprioritized.**

The name from the original candidate list is ambiguous. The readily identifiable GitHub project with that name is not relevant to this use case, and no clearly superior MiLB PBP package was established from the name alone.

**Decision:** do not spend foundation time on it unless an exact package/repository is identified later.

## Source assignment by layer

This is a **provisional POC assignment**, not a permanent dependency lock-in.

| Need | Leading source(s) | Role |
|---|---|---|
| Historical affiliated MiLB PBP | `armstjc/milb-data-repository` | Bootstrap candidate, quarantined until certification |
| Official modern game truth | MLB Stats API | Reconciliation/debug/fallback authority |
| Direct Python Stats API utility | SportsDataverse and/or `python-mlb-statsapi` | POC comparison before selecting adapter(s) |
| MLB historical event benchmark | Retrosheet | Independent reconciliation / backtesting |
| Cross-source player identity | Chadwick Register + MLBAM | Crosswalk; internal ID remains ours |
| MiLB tracking enrichment | SportsDataverse → Baseball Savant Minor Statcast | Coverage-tier enrichment |
| Alternative MiLB tracking implementation | `baseball-stats-python` | Reference/fallback |
| PBP parsing reference | `baseballr`, `mcbarlowe/mlb` | Edge-case and transformation oracle |
| MLB research convenience | `pybaseball` | Secondary helper |

## Canonical data principle

The phrase **canonical source** should be avoided because it conflates authority and working representation.

Use these terms instead:

- **Authority:** source against which a fact is reconciled (for modern MLB/MiLB, usually MLB Stats API / Savant where applicable).
- **Working input:** certified dataset/package from which we may load historical data efficiently.
- **Canonical table:** our stable normalized representation used downstream.

A third-party working input can be replaced without changing the canonical tables or model features.

## Certification gate before pipeline design

No historical source is promoted directly into canonical tables. It first goes through a small certification POC.

The initial POC should include deliberately different environments rather than one convenient sample:

- a recent AAA slice;
- a recent AA/A+/A slice without assuming tracking is present;
- a recent Rookie/complex/DSL slice with explicit league identification;
- an older historical slice from the armstjc archive;
- a small MLB control sample where Retrosheet/official data provide an additional benchmark.

For each slice, test:

1. expected games and unique `game_pk` values;
2. exact duplicate pitch keys and duplicate rows;
3. unique batter/pitcher MLBAM IDs and basic identity resolution;
4. PA/BF counts reconstructed from PBP;
5. AB, H, 2B, 3B, HR, BB, HBP, and K against official totals;
6. pitch counts where an official/boxscore comparison is available;
7. event completeness for the first Performance taxonomy;
8. batted-ball type/direction availability and category stability;
9. tracking-field availability by league/park rather than global non-null rate;
10. replayability: record source URL/release asset, retrieval time, checksum, and parser/package version.

**Failure behavior:** first document the discrepancy. Do not immediately patch it. Determine whether the issue belongs to the source feed, upstream parser, our interpretation, or a known game-scoring correction. Only then decide whether to normalize, exclude, or build custom parsing.

See `docs/source-certification-plan.md` for the detailed acceptance rules.

## Architecture implications already justified by the audit

The audit supports several foundation decisions before model work begins:

- Maintain a thin **source adapter boundary**. No model imports an upstream baseball package directly.
- Preserve raw source identifiers (`game_pk`, MLBAM IDs, league/team/venue IDs) even when we also assign internal keys.
- Track **source provenance and version** at dataset/batch level.
- Treat league/level as explicit time-varying context, not a permanent player attribute.
- Maintain **data coverage facts** separately from player skill facts.
- Do not use the existence of a column as proof that a measurement exists for a player/park/season.
- Build PA/pitch/event keys deliberately so duplicate source rows cannot silently become extra evidence.
- Reconciliation tests are part of ingestion, not a one-time notebook exercise.

## Open questions that should not block the POC

1. **Public redistribution scope.** Before the repository/site becomes public, decide whether we intend to publish only derived model outputs or also bulk normalized source data. That changes the source-terms review materially.
2. **R as a development oracle.** We can compare selected games against `baseballr` without adding R to production. This is useful but not required on every CI run.
3. **Exact rookie-league taxonomy over time.** The POC must prove reliable separation of DSL, ACL/FCL, and historical rookie leagues from row-level league/team metadata.
4. **Current armstjc release publishing.** Determine where current workflow outputs land and whether tagged release assets are overwritten/immutable enough for reproducible snapshots.
5. **SportsDataverse vs `python-mlb-statsapi` for direct official access.** Choose based on empirical reliability and raw-field preservation, not aesthetics.

## Stopping rule for the source hunt

The credible candidate set is now sufficient to start certification. Do not continue searching for more packages merely to create a longer list. Re-open the source audit only when:

- a certification test fails in a way another implementation may already solve;
- a required level/season is missing;
- a source becomes unavailable or unmaintained;
- a new model layer requires data not covered here.
