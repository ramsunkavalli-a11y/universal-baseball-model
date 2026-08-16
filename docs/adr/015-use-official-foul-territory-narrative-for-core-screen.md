# ADR 015: Use official `foul territory` narrative for the 12-bin foul-air screen

**Status:** Accepted for foundation architecture  
**Date:** 2026-08-15

## Context

ADR 008 requires exhaustive Performance accounting for every official true PA but excludes PA-ending airborne foul outs from the narrower 12-bin FaBIO-style skill view. The unresolved question was how to identify those foul-air events without deriving fair/foul status from approximate spray geometry.

A production rule based on spray angle is rejected. Gameday `hc_x/hc_y` is excellent for Pull/Center/Opposite direction but the coordinate transform is not an official fair/foul boundary, and foul-line/pole language can describe fair contact near a boundary.

The reusable PBP releases preserve a PA narrative `description`. Because that field is intended to mirror the Stats API play result description, the candidate approach was to audit the actual narrative vocabulary first and then reconcile it to official `allPlay.result.description`.

### Cross-era/level vocabulary audit

Four representative source assets were collapsed at natural physical-pitch grain using the accepted non-null field-consensus logic:

- 2005 AAA: `2005_9_aaa_pbp.csv`;
- 2015 AAA: `2015_9_aaa_pbp.csv`;
- 2024 Rookie/complex: `2024_6_rk_pbp.csv`;
- 2025 AAA: `2025_3_aaa_pbp.csv`.

The candidate universe included `popup`, `fly_ball`, and `line_drive` trajectory evidence. Across **27,985** candidate batted balls:

- descriptions present: **27,985 / 27,985**;
- description conflicts at natural pitch grain: **0**;
- descriptions containing word-boundary `foul`: **1,257**;
- descriptions containing explicit `foul territory`: **1,257**;
- broad `foul` descriptions without explicit territory/ground: **0**;
- `foul line` mentions: **0**;
- `foul pole` mentions: **0**;
- `foul ball` mentions: **0**.

A diagnostic `foul ground` pattern was also searched, but it was not observed in the audited sources. It is therefore **not** silently added to the production allowlist.

Adding line drives to the candidate universe produced no additional positive foul-territory examples in these source samples, but line drives remain in the eligible trajectory family because the architectural exclusion is based on a caught ball in foul territory rather than height/launch-shape alone.

### Official authority reconciliation

For each representative asset, six explicit foul-territory candidates and six ordinary airborne candidates were selected deterministically, preferring different games. The reusable natural PA key and narrative were compared with current MLB Stats API `allPlay.result` data.

Across **48 sampled PAs**:

- official sequence found: **48 / 48**;
- official true-PA semantics: **48 / 48**;
- explicit foul-territory classification agreement: **48 / 48**;
- normalized reusable description equals normalized official result description: **48 / 48**.

The line-drive-expanded reconciliation also passed in all four source environments; the sampled ordinary class included line drives. Thus the reusable narrative is useful mirror evidence, while the canonical official play-sequence `result_description` remains the authority used by the Performance mapper.

## Decision

For the **12-bin Performance skill view**, classify an otherwise clean, core-eligible `IFFB`, `OFFB`, or `LD` PA-ending batted ball as a foul-air out **only** when the canonical official play-sequence `result_description` contains the case-insensitive word-boundary phrase:

`foul territory`

The implementation uses the equivalent regex:

`(?i)\bfoul\s+territory\b`

Rules:

1. The exhaustive Performance row is always retained. Foul-air affects only the narrower 12-bin core eligibility/bin.
2. The screen applies to clean PA-ending batted balls mapped to `IFFB`, `OFFB`, or `LD`. Bunts are already excluded separately from the core taxonomy.
3. A matching official `foul territory` narrative sets `is_foul_air_out=true` and leaves the final core bin null.
4. An official result description that is present but does not contain the certified phrase sets `is_foul_air_out=false`; the pre-screen core bin may remain eligible.
5. If the official result description is missing on an otherwise core-eligible airborne candidate, foul-air status is unknown and the final core bin remains null. Missing evidence is never interpreted as fair contact.
6. Spray angle, `hc_x/hc_y`, a generic occurrence of `foul`, `foul line`, `foul pole`, and other unvalidated narrative phrases are not production fair/foul classifiers.
7. `foul ground` is not accepted merely because the diagnostic searched for it. If a new phrase appears in future evidence, it must be audited/reconciled before the allowlist changes.
8. Reusable source `description` remains certified mirror/provenance evidence, but canonical classification uses official `result_description` where the play-sequence layer is materialized.

The Performance event schema exposes both views:

- `fabio_core_bin_pre_foul_screen` / `core_profile_eligible_pre_foul_screen` for diagnostic lineage;
- `foul_air_status` / nullable `is_foul_air_out` for evidence state;
- `fabio_core_bin` / `core_profile_eligible` for the screened 12-bin skill view.

## Consequences

- The final 12-bin eligibility rule no longer depends on approximate field geometry.
- Historical/recent source vocabulary and current official authority agree on the certified phrase in the tested evidence.
- Unknown official narratives reduce core coverage explicitly instead of creating silent fair/foul guesses.
- The next value-estimator gate must be rerun on **screened `fabio_core_bin` events**. Existing pre-foul-screen stability/pooling results remain valuable architecture evidence but cannot alone certify the final production Performance-value transform.
