# First MiLB Source POC Findings

## Status

This document records empirical findings from the first source-certification proof of concept. It is evidence for architecture decisions, not a declaration that the source is fully certified.

Source under test: `armstjc/milb-data-repository` release asset `2025_3_aaa_pbp.csv`.

Official comparison source: MLB Stats API `game/{gamePk}/playByPlay`, fetched through the stable low-level `MlbDataAdapter` transport from `python-mlb-statsapi` and projected into a deliberately small set of PA and pitch-event fields by this project.

## What the release contains

The tested asset has:

- 25,636 rows and 103 columns;
- 43 unique games;
- 12,818 exact duplicate extra rows;
- 12,818 duplicate natural-key extra rows using `(game_pk, at_bat_number, pitch_number)`;
- zero conflicting natural-key duplicates.

The duplication is therefore deterministic in this slice: removing exact duplicate rows for **comparison only** leaves 12,818 unique pitch rows. Code review of the upstream collector found a matching cause: a successful game dataframe is concatenated once inside the `try` block and again immediately afterward.

This does **not** authorize silent production deduplication yet. The raw release remains quarantined and its checksum/provenance must be retained. If armstjc is promoted later, exact-deduplication will be an explicit, tested source-normalization transform.

## PA outcome field defect

The release's `events` column is not a usable PA-outcome field in this slice. The upstream parser reads the PA result but writes a pitch-event variable into `events`; ordinary pitch rows therefore leave it blank.

The official feed's PA result fields (`result.event`, `result.eventType`, description) are present and cleanly keyed by `game_pk + atBatIndex`. The source should therefore be treated as a useful **pitch-grain historical table**, not as the sole authority for PA outcomes.

## Full-release official comparison

Using all 43 games in the asset, the narrow official adapter successfully read all 43 games, including irregular MiLB payloads that broke the high-level typed client.

At the current official-feed state used by the POC:

- 3,282 official PAs were observed;
- 3,281 PAs had a corresponding armstjc pitch-grain PA key after exact deduplication for comparison;
- all shared PAs had matching current official pitch counts;
- the one official-only PA occurred in game `779653` and is a zero-pitch intentional walk;
- no positive-pitch PA omission has been identified in this release slice.

The exact official feed can be corrected after a game is played, so these counts are evidence from the retrieval-time feed rather than a promise that a future retrieval will be byte-for-byte identical. This reinforces the project's requirement to record retrieval time and source version/checksum for historical validation.

## Why one PA is structurally absent from the pitch table

A separate edge-case audit of game `779653` found a signaled intentional walk at `atBatIndex=69` with zero events marked as pitches. A table whose grain is one row per pitch cannot represent that PA at all.

This is not a defect that should be "fixed" by inventing a pitch row. It establishes an architectural requirement: the canonical data model needs a PA table that exists independently of the pitch table. Pitch rows attach to PAs when pitches exist; a valid PA may have zero pitch children.

## Validation bug found in our own POC

The first comparison incorrectly used the MLB feed's `pitchIndex` list length as the official pitch count and reported 28 mismatched PAs in a five-game sample. Inspecting the actual `playEvents` showed that `pitchIndex` can retain references that do not correspond one-for-one with the current events marked `isPitch=true`.

After changing the comparison to count current `playEvents` where `isPitch=true`, the five-game sample and then the full 43-game comparison showed zero pitch-count disagreements among shared PAs.

This is a useful precedent for the certification framework: discrepancies are investigated before either source is "repaired." In this case the reused source was right and our validator was wrong.

## Official Python client evaluation

### High-level `python-mlb-statsapi` objects

The high-level typed `get_game_play_by_play()` path is too strict to be the foundation for universal MiLB ingestion. Game `780856` contains legitimate pitch-type objects such as `{"description": "Unknown"}` without a `code`. The Pydantic model requires the code and rejects the entire game.

### SportsDataverse

SportsDataverse successfully handled both tested edge games, including game `780856`, and remains a strong candidate for Baseball Savant / Minor League Statcast enrichment. However, installing the full package for this PBP task pulls a large scientific/modeling dependency graph (including pandas, SciPy, scikit-learn, XGBoost, PyArrow, Matplotlib and platform-specific XGBoost dependencies). That is unnecessary weight for the narrow official PBP verification role.

### Chosen official PBP utility for this stage

Use the stable public low-level `MlbDataAdapter` from `python-mlb-statsapi` for HTTP sessions, retries, timeouts and structured failures, but do **not** use its strict high-level PBP object model. The project owns only a small projection of raw `playByPlay` JSON into fields needed for certification and PA enrichment.

This is intentionally not a custom full-feed parser. It is a narrow adapter over already-solved HTTP plumbing, and it tolerates optional/missing nested fields rather than encoding the complete MLB JSON schema.

## Remaining concerns before promotion

The asset is still **quarantined**. The POC has not yet completed:

- adjacent-file overlap/partition testing;
- official statistical reconciliation for AB, H, 2B, 3B, HR, BB, HBP and K;
- cross-level testing at AA, A+, A and rookie/complex levels;
- explicit DSL identification/coverage;
- older historical-slice testing;
- batted-ball direction/category validation;
- player identity crosswalk validation;
- tracking availability profiling by league/park/season;
- source-data terms/redistribution review.

The next source-level question is the partition anomaly: `2025_3_aaa_pbp.csv` contains row dates/month values extending into April. The next test should compare adjacent release assets by natural keys and row dates before treating filename month as partition truth.

## Current provisional conclusion

`armstjc/milb-data-repository` remains promising as a **historical pitch-level bootstrap**. The tested slice suggests that, after a deterministic exact-duplicate normalization, its underlying pitch sequence agrees extremely well with the current official feed. It should not be used alone for PA reconstruction because zero-pitch PAs and its broken PA outcome field require an independent PA layer.

The likely architecture is therefore:

1. quarantined reusable pitch-grain history from armstjc, explicitly normalized and certified;
2. canonical PA records keyed independently and enriched/certified from the official feed;
3. canonical pitch records attached to PA records where pitches exist;
4. official MLB API access through a narrow low-level adapter for verification, gap filling and incremental updates;
5. richer tracking sources such as Savant/SportsDataverse added later as optional evidence tiers.
