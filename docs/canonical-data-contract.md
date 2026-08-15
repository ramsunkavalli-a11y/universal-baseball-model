# Canonical Data Contract

Status: foundation contract, version 0.1  
Date: 2026-08-15

This document defines the minimum durable data contract that the historical backfill and later modeling layers must obey. It intentionally freezes **grains, identities, provenance, temporal semantics, and resolution rules** before freezing every possible baseball field.

The goal is not to build a complete baseball warehouse before modeling. The goal is to prevent the first backfill from baking source quirks, silent repairs, or hindsight assumptions into tables that later models cannot unwind.

## 1. Architectural layers

### Quarantine / raw

Original upstream bytes are immutable.

Examples:

- armstjc release CSV;
- MLB Stats API response captured by the official adapter;
- Chadwick Register archive;
- later Savant / tracking exports.

Raw files are **not** canonical tables. Exact duplicate rows, bad source columns, overlapping release assets, and later source corrections remain intact here.

### Observation / normalized source

A source observation is what one immutable source snapshot says about one baseball natural key.

Normalization may:

- standardize known column aliases;
- type fields;
- collapse byte-identical repeated rows while recording their duplicate count;
- expose multiple distinct payload variants for one natural key.

Normalization may **not** silently choose a winner among conflicting source payloads or rewrite an upstream value because another source disagrees.

### Resolved canonical

Resolved tables answer a specific question such as “what is the current preferred representation of this pitch?” or “what representation was available in an archived vintage?”

Resolution is explicit and reproducible. A resolved record always retains the snapshot/source evidence from which it was chosen.

### Derived/model

Plate-appearance views, batted-ball direction, Performance events, skill estimates, Current Talent, Projection, and Value sit above the canonical event layer. Derived model logic never modifies source observations.

---

## 2. Time semantics

Baseball data has more than one relevant clock. These columns must not be collapsed into a single ambiguous `date`.

### `event_date` / `event_time`

When the baseball event occurred.

### `source_published_at_utc`

When the upstream artifact/version was published, when that timestamp is defensible. May be null for sources that do not expose a historical publication time.

### `retrieved_at_utc`

When our pipeline retrieved the exact source bytes/API response.

### `knowledge_available_at_utc`

Earliest defensible time at which **this exact source representation** was publicly available. This is only populated when the source vintage is actually known. It is not backfilled to the baseball event date merely because the event was observable then.

## 3. Two backtest modes — do not conflate them

### Retrospective event-cutoff backtest

Use current/certified historical data, but only baseball events with `event_date <= cutoff`.

This prevents future **baseball performance** from entering predictors, but the underlying historical feed can include corrections made after the cutoff. This is the primary practical mode for large historical model development unless archived source vintages exist.

Report it as **retrospective event-cutoff**, not strict as-of.

### Vintage / information-set backtest

Require `knowledge_available_at_utc <= cutoff` (or another demonstrably archived snapshot rule) in addition to the baseball event cutoff.

This is the standard required when we claim to recreate the exact public information set available at the time. It is especially important for benchmarking against contemporary prospect lists or projection snapshots.

If the project does not possess an archived data vintage, it must not manufacture one by assigning historical events a fake historical knowledge timestamp.

---

## 4. Source snapshot registry

### `source_snapshot`

One row per immutable upstream artifact/API capture used by normalized data.

Required fields:

| Field | Meaning |
|---|---|
| `source_snapshot_id` | Deterministic snapshot identifier derived from source + content identity |
| `source_name` | Stable source family, e.g. `armstjc_milb_pbp`, `mlb_stats_api`, `chadwick_register` |
| `source_role` | `historical_bootstrap`, `official_authority`, `crosswalk`, `tracking_enrichment`, etc. |
| `upstream_locator` | URL / endpoint / release asset identity |
| `upstream_version` | Commit, release, endpoint semantics version, or null |
| `content_sha256` | SHA-256 of immutable retrieved content when content is file-like |
| `source_published_at_utc` | Upstream publication time if known |
| `retrieved_at_utc` | Pipeline retrieval time |
| `knowledge_available_at_utc` | Defensible public-availability time or null |
| `parser_name` | Normalizer/adapter producing observations |
| `parser_version` | Code/schema version |
| `license_id` | MIT, ODC-By, source terms identifier, etc. |
| `raw_object_key` | Storage locator for immutable quarantine bytes |

`source_snapshot_id` must change if the underlying bytes or semantically relevant API capture changes.

A filename such as `2025_3_aaa_pbp.csv` is provenance only. It does not define canonical event month or level.

---

## 5. Natural event grains

### `game`

Natural key: `game_pk`.

Minimum canonical fields:

- `game_pk`
- `official_date`
- `season`
- `game_type`
- official level/sport ID + normalized level label
- league ID/name when available
- home/away team IDs
- parent organization IDs when applicable

Game metadata may initially be resolved from official Stats API evidence with reusable-source metadata retained as observations/cross-checks.

### `play_sequence`

Natural key:

`game_pk + at_bat_index`

This is the universal parent above pitches, per ADR 006.

Minimum canonical fields:

- `game_pk`
- `at_bat_index`
- `result_event_type`
- `result_event`
- `result_description` (debug/audit; never preferred over structured code)
- `is_plate_appearance`
- `event_semantics_snapshot_id`
- `batter_mlbam_id`
- `pitcher_mlbam_id`
- `batter_side`
- `pitcher_hand`
- `inning`
- `half_inning`
- `sequence_start_time`
- `sequence_end_time`
- `official_physical_pitch_count`
- resolution/provenance fields

`is_plate_appearance` is determined from versioned official event semantics, not from source pitch existence and not from `result.type`.

A sequence can be:

- true PA + zero pitches;
- true PA + one or more pitches;
- non-PA + one or more pitches;
- non-PA + zero pitches.

If the historical pitch source contains a sequence key that has not yet been enriched by official structured evidence, it may exist in staging as `classification_status = unclassified_source_sequence`. It is **not** assumed to be a PA.

### `pitch`

Natural key:

`game_pk + at_bat_index + pitch_number`

The table contains **physical pitch events**. Nonphysical automatic strikes/balls remain play-sequence/action evidence and are not fabricated into physical pitch rows.

Universal/source-PBP fields include, when available:

- pitch result/call code;
- count state;
- event-level batter side and pitcher hand;
- `is_in_play`;
- Gameday `bb_type`;
- Gameday `hit_location`;
- Gameday `hc_x`, `hc_y`;
- inning/context fields that are already present and certified.

Optional evidence fields include:

- pitch type/name;
- release velocity;
- release coordinates;
- plate location;
- movement;
- spin;
- extension;
- EV/launch angle/distance;
- richer tracking fields added from later sources.

**Column presence does not imply evidence availability.** Optional fields carry structural coverage metadata by source/season/league/park.

Raw participant IDs copied by a reusable parser are named as source evidence, e.g. `source_batter_mlbam_id`, not silently promoted to canonical participant identity. The known pinch-runner bug makes that distinction mandatory.

---

## 6. Immutable observation tables

The normalized source layer should use immutable observations rather than updating rows in place.

### `play_sequence_observation`

Natural observation key begins with:

`source_snapshot_id + game_pk + at_bat_index`

If one snapshot somehow contains multiple distinct payload representations for the same sequence key, retain a `payload_hash`/variant rather than overwriting.

### `pitch_observation`

Natural observation key begins with:

`source_snapshot_id + game_pk + at_bat_index + pitch_number + payload_hash`

Required bookkeeping:

- `payload_hash`
- `duplicate_row_count`
- source-specific raw participant IDs
- normalized event/PBP fields

Exact duplicate upstream rows can therefore compact to one normalized observation with `duplicate_row_count > 1`, while immutable quarantine bytes still prove what the source contained.

Multiple **different** payloads for one pitch key remain separate observations.

### `player_crosswalk_observation`

Keyed by crosswalk snapshot + MLBAM ID + crosswalk identity.

Chadwick-derived fields include:

- MLBAM ID
- Chadwick UUID/person key
- FanGraphs ID
- Baseball-Reference IDs
- Retrosheet ID
- relevant name/birth/pro-career metadata for audit only

No fuzzy-name resolution occurs in this table.

---

## 7. Resolution rules

Resolution is source-specific; there is no global “newest value from anywhere wins” rule.

### Play sequence

Official MLB Stats API structured evidence is the authority for modern sequence result semantics and matchup identity.

Current view: latest accepted official snapshot for the sequence under the selected resolution policy.

Vintage view: latest accepted official snapshot whose source vintage satisfies the requested information cutoff, when such an archived vintage exists.

### Historical pitch core

For historical affiliated MiLB, certified armstjc data is the preferred physical-pitch bootstrap.

Within a source snapshot:

1. byte-identical duplicates compact with count;
2. stable fields shared by all variants can resolve;
3. conflicting core fields are null/flagged unless a documented field-specific rule exists;
4. no arbitrary first-row selection.

Across snapshots:

- current resolved history may choose the latest accepted observation of the natural pitch key from the same source family;
- do not backfill a missing value from an older snapshot into a newer snapshot unless an explicit enrichment rule says to do so;
- retain the exact snapshot used by the resolved record.

### Official gap fill

If certification identifies a physical pitch in official PBP that is absent from the reusable historical source, an explicit `official_gap_fill` record may be created. Its origin must remain visible. It is not silently made to look like an armstjc row.

### Tracking enrichments

Savant/other tracking data attaches as a keyed enrichment layer. It does not overwrite the universal PBP observation. A model can therefore distinguish:

- “universal PBP says this happened”
- “tracking source measured these physical properties.”

---

## 8. Current and as-of views

At minimum, the storage layer should expose logically separate views:

### `*_current`

Best accepted representation under current source snapshots and current resolution policy.

### `*_event_cutoff(cutoff)`

Current corrected history restricted by baseball event date. Used for retrospective model validation.

### `*_vintage(cutoff)`

Only observations whose exact public/source vintage was available by the requested cutoff. Used only where provenance supports the claim.

Never label `*_event_cutoff` output as strict “as of” without the vintage condition.

---

## 9. Quality issues are data

Do not encode every problem as a thrown exception or a comment in a notebook.

### `quality_issue`

Minimum fields:

- `issue_code`
- `severity` (`info`, `warning`, `error`, `quarantine`)
- `entity_type` (`source_snapshot`, `game`, `play_sequence`, `pitch`, `player_crosswalk`)
- nullable natural-key columns (`game_pk`, `at_bat_index`, `pitch_number`, `mlbam_id`)
- `source_snapshot_id`
- `check_name`
- `check_version`
- `detected_at_utc`
- compact structured detail / diagnostic text

Examples already observed:

- `exact_duplicate_source_row`
- `conflicting_source_payload`
- `source_snapshot_overlap`
- `source_pa_outcome_field_unusable`
- `source_batter_replaced_by_pinch_runner`
- `official_only_physical_pitch`
- `unknown_official_event_type`
- `crosswalk_pending`
- `structural_tracking_unavailable`

Downstream confidence/effective sample size can consume quality evidence instead of inventing a generic confidence score disconnected from source reality.

---

## 10. Derived universal batted-ball evidence

A derived batted-ball view can be keyed by the terminal in-play physical pitch and join to the official play sequence.

Minimum fields:

- source trajectory
- `trajectory_family` (`IFFB`, `OFFB`, `LD`, `GB`, `BUNT`, `UNKNOWN`)
- continuous spray angle
- `direction` (`pull`, `center`, `opposite`, null)
- bunt subtype
- later certified foul-air flag
- `core_profile_eligible`
- direct-source evidence/provenance

ADR 007 governs coordinate direction. ADR 008 governs exhaustive Performance versus the FaBIO-compatible core view.

---

## 11. Performance-event grain

The first Performance table will ultimately be **one row per true plate appearance**, not one row per pitch.

It should preserve both:

1. an exhaustive outcome/value classification that accounts for every usable true PA; and
2. an optional `core_profile_bin` for the FaBIO-compatible skill view.

A bunt or excluded foul-air event can therefore have a valid exhaustive Performance outcome while `core_profile_bin` is null.

This keeps “what happened” separate from “which subset is useful for a particular skill profile.”

---

## 12. Physical storage guidance

Do not encode armstjc asset filenames as final partitions.

Preferred Parquet partitioning is based on actual baseball event metadata, e.g.:

- large pitch observations: `season / normalized_level / event_month`;
- play sequences: `season / normalized_level` unless volume requires a monthly partition;
- small registries/crosswalks: snapshot/version rather than event month.

DuckDB is the local/query catalog over Parquet; Parquet remains the portable durable analytical format.

Do not add finer partitions until measured file sizes justify them. Avoid thousands of tiny files.

---

## 13. Schema evolution rules

1. Natural keys and provenance fields are harder contracts than optional baseball columns.
2. Adding an optional evidence field is backward-compatible.
3. Changing a field's semantics requires a schema-version increment and migration/compatibility note.
4. Source aliases are normalized in explicit source adapters, never renamed ad hoc downstream.
5. Derived fields record their method/version so a later improved formula can coexist with older historical model runs.
6. Unknown values stay null/unknown; default values must not manufacture evidence.

---

## 14. First implementation boundary

The first canonical implementation should remain deliberately small. It needs to prove:

1. deterministic `source_snapshot_id` and immutable provenance metadata;
2. play-sequence and pitch natural-key validation;
3. exact-duplicate compaction plus explicit conflicting variants;
4. true-PA classification from versioned official semantics;
5. current versus retrospective event-cutoff versus true vintage semantics;
6. Parquet round-trip and DuckDB queryability;
7. quality-issue emission.

It does **not** need to backfill every season, implement every field, or build Projection before these contracts survive a small end-to-end sample.
