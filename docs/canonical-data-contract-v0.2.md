# Canonical Data Contract v0.2

Status: current foundation contract  
Date: 2026-08-15  
Supersedes: `canonical-data-contract.md` v0.1 where this document differs

The v0.1 contract correctly separated raw observations from resolved/model data, but its `source_snapshot` table mixed **upstream evidence identity** with **our parser version**. Those are different things: the same immutable source bytes can be re-normalized by improved code. v0.2 fixes that before any historical backfill.

## 1. Layers

### Quarantine / raw
Original upstream bytes or captured API payloads. Immutable. Source defects remain intact.

### Source registry
Describes exactly which upstream representation was retrieved.

### Normalization definition
Describes exactly which version of our source adapter/schema interpreted that source snapshot.

### Observation tables
Immutable normalized statements produced from one source snapshot under one normalization definition. Conflicting payload variants coexist; they are not overwritten.

### Resolved canonical views
Explicit current/vintage resolution over observations.

### Derived/model tables
PA view, batted-ball evidence, Performance/Profile, Current Talent, Projection, Value.

---

## 2. Provenance identities

### `source_snapshot`

One row per exact upstream representation.

Required identity:

- `source_snapshot_id`: deterministic hash of source family + upstream version + exact content digest;
- `source_name`;
- `source_role`;
- `upstream_locator`;
- `upstream_version` when available;
- `content_sha256`;
- `source_published_at_utc` when defensible;
- `retrieved_at_utc`;
- `knowledge_available_at_utc` when defensible;
- `license_id`;
- `raw_object_key`.

**Parser/normalizer version is not part of this table.** If the bytes did not change, the source snapshot did not change.

### `normalization_definition`

One deterministic interpretation of one source snapshot.

- `normalization_id`;
- `source_snapshot_id`;
- `normalizer_name`;
- `normalizer_version`;
- `canonical_schema_version`.

A code/schema change creates a new `normalization_id` while preserving the same `source_snapshot_id`.

Every observation carries both IDs. Cross-table validation must prove that its `normalization_id` points to the same `source_snapshot_id` recorded on the observation.

---

## 3. Temporal semantics

Keep separate:

- `event_date` / event time — when baseball happened;
- `source_published_at_utc` — when the upstream representation was published, if known;
- `retrieved_at_utc` — when we captured it;
- `knowledge_available_at_utc` — earliest defensible public availability of that exact representation, if known.

Do not fabricate historical `knowledge_available_at_utc` values for current corrected history.

Validation modes follow ADR 009:

- **retrospective_event_cutoff**: current/certified history, only events through the forecast cutoff;
- **vintage_information_set**: additionally requires a defensible source vintage available by the cutoff.

---

## 4. Canonical event grains

### `game`
Natural key: `game_pk`.

### `play_sequence`
Natural key: `game_pk + at_bat_index`.

This is the universal parent above physical pitches (ADR 006). It may be a true PA or a known non-PA sequence.

Minimum resolved fields:

- structured result/event code;
- `is_plate_appearance` from versioned official event semantics;
- official batter/pitcher MLBAM identity;
- event-level handedness;
- inning/half-inning;
- sequence timing;
- official physical-pitch count;
- resolution/provenance.

Allowed classification states in normalized observations:

- `official_true_pa` → `is_plate_appearance=true`;
- `official_non_pa` → `is_plate_appearance=false`;
- `unclassified_source_sequence` → `is_plate_appearance=null`.

A source pitch-sequence is never promoted to a PA merely because pitches exist.

### `pitch`
Natural key: `game_pk + at_bat_index + pitch_number`.

Contains physical pitch events only. Automatic balls/strikes and runner actions are sequence/action evidence, not invented physical pitches.

Raw participant IDs copied from reusable source files are explicitly named `source_*_mlbam_id`. Canonical sequence identity comes from official structured evidence; source parser identities remain auditable evidence.

Universal PBP evidence includes pitch result/call and Gameday BIP fields when available (`bb_type`, `hit_location`, `hc_x`, `hc_y`, handedness). Sensor/tracking fields remain optional evidence.

---

## 5. Observation keys

### `play_sequence_observation`

At minimum:

`normalization_id + game_pk + at_bat_index + payload_hash`

A source snapshot can retain multiple payload variants for one baseball natural key.

### `pitch_observation`

At minimum:

`normalization_id + game_pk + at_bat_index + pitch_number + payload_hash`

Each observation also carries `duplicate_row_count`.

- exact duplicate upstream rows compact to one normalized observation with count;
- distinct payloads for one natural pitch key remain distinct observations;
- `duplicate_row_count` must be >= 1;
- physical `pitch_number` must be >= 1.

### `player_crosswalk_observation`

Pinned crosswalk snapshot + MLBAM identity. The first implementation enforces one Chadwick row per MLBAM ID per normalization snapshot; conflicts fail rather than fuzzy-match.

---

## 6. Resolution

There is no global “newest value from any source wins.”

### Sequence resolution
Official MLB Stats API structured evidence is the authority for modern result semantics and matchup identity.

### Historical pitch resolution
Certified armstjc history is the physical-pitch bootstrap.

Within one source snapshot:

1. compact exact duplicates;
2. accept a field only when repeated non-null observations agree, unless a specific certified rule exists;
3. conflicting core evidence becomes null/flagged rather than arbitrary first-row selection.

Across source snapshots:

- current view can select the latest accepted observation from the same source family;
- do not silently fill a newer snapshot's missing field with an older value;
- retain the exact source snapshot and normalization definition used.

### Official gap fill
A missing physical pitch can be inserted only as an explicit `official_gap_fill` origin after certification. It must never masquerade as a reusable-source row.

### Tracking enrichment
Savant/other tracking attaches as a keyed enrichment. It does not overwrite the universal PBP record.

---

## 7. Quality evidence

`quality_issue` is a first-class table rather than log-only state.

Minimum fields:

- deterministic `quality_issue_id`;
- `issue_code`;
- controlled `severity`: `info`, `warning`, `error`, `quarantine`;
- controlled `entity_type`;
- nullable natural-key columns;
- source/normalization IDs when relevant;
- check name/version;
- detection timestamp;
- compact structured details.

Known issue codes include exact duplicate rows, conflicting source payloads, source snapshot overlap, unusable source PA outcome, pinch-runner batter mutation, official-only physical pitch, unknown official event type, crosswalk pending, and structural tracking unavailability.

Downstream uncertainty can consume real evidence quality instead of a generic confidence score.

---

## 8. Performance/Profile relationship

`performance_event` is one row per **true PA**.

It preserves:

1. exhaustive outcome/value accounting for every usable PA; and
2. optional `core_profile_bin` for the FaBIO-compatible skill view.

Batted-ball evidence keeps:

- original trajectory;
- trajectory family (IFFB/OFFB/LD/GB/BUNT/UNKNOWN);
- continuous coordinate spray angle;
- Pull/Center/Opposite direction where available;
- special-event flags;
- `core_profile_eligible`;
- method/source version.

Bunts can have a valid exhaustive Performance outcome while remaining outside the ordinary 12-bin core profile (ADR 008).

---

## 9. Storage contract

Parquet is the durable analytical format; DuckDB is the lightweight local/query catalog.

First implementation requirements:

- strict typed canonical schemas;
- atomic Parquet writes;
- row count, file SHA-256, and ordered-schema fingerprint for written artifacts;
- DuckDB can query the exact Parquet file without conversion;
- actual event metadata determines partitions, not upstream asset filenames.

Preferred initial partitioning:

- large pitch observations: `season / normalized_level / event_month`;
- sequences: `season / normalized_level` until volume warrants more;
- registries/crosswalks: source snapshot/version.

Do not create finer partitions until measured file sizes justify them.

---

## 10. Schema evolution

- Natural keys and provenance are hard contracts.
- Optional evidence fields can be added compatibly.
- Semantic changes increment `canonical_schema_version`.
- Source aliases belong in explicit source adapters.
- Derived methods carry method/version IDs.
- Unknown evidence stays null; defaults must not manufacture observations.

Current code contract: `CANONICAL_SCHEMA_VERSION = "0.1"`. This document is v0.2 of the **design contract**; the physical schema remains 0.1 until a table-level semantic change requires a migration.

---

## 11. Next implementation gate

Before any production-scale historical backfill, prove a tiny end-to-end sample can:

1. register immutable source snapshots;
2. register separate normalization definitions;
3. emit validated play-sequence and pitch observations;
4. preserve duplicate counts and conflicting variants;
5. write atomic Parquet;
6. query it through DuckDB;
7. emit quality issues;
8. reconstruct current and event-cutoff views without claiming unsupported historical vintages.

Only after that sample passes should the project scale the already-certified reusable MiLB history.
