# ADR 010: Reconstruct reusable-source in-play semantics from D/E/X plus preserved hitData

**Status:** Accepted  
**Date:** 2026-08-15

## Context

The reusable MiLB source exports MLB play-event `details.code` as its `type` column but does not export the upstream `details.isInPlay` boolean directly. The source column guide describes `type` too narrowly as B/S/X.

The first universal Performance mapper therefore made an incorrect assumption: `type == "X"` was treated as the only positive in-play code. A six-game live audit immediately exposed the problem. Among 283 official BIP-expected PAs with preserved reusable-source batted-ball evidence:

- 150 used `X`;
- 77 used `D`;
- 56 used `E`.

The 133 D/E contacts were exactly the PAs the first mapper had falsely labeled `missing_in_play_pitch`.

This was not a modern-only convention. Historical release audits found:

- `2005_9_aaa_pbp.csv`: 5,905 rows with batted-ball trajectory, with codes D=1,478, E=731, X=3,696 and zero unexpected codes;
- `2015_9_aaa_pbp.csv`: 8,196 rows with batted-ball trajectory, with codes D=1,991, E=984, X=5,221 and zero unexpected codes.

Code review of the reusable-source parser provides an additional invariant: it populates exported hitData-derived fields such as `bb_type`, hit location, coordinates, distance, exit velocity and launch angle only inside the upstream branch where `details.isInPlay == True`.

A narrow reuse audit also confirmed that `baseballr::mlb_pbp()` preserves MLB's `details.isInPlay` field directly by flattening the full Stats API play-event payload. That is useful corroborating implementation precedent, but the historical reusable files already retain enough information to reconstruct the positive in-play signal without adding another historical ingestion dependency.

## Decision

For `armstjc/milb-data-repository` pitch observations, canonical `is_in_play` is reconstructed as follows:

1. `True` when exported `type` is one of `{D, E, X}`;
2. `True` when any preserved hitData-derived field is non-null, even if a future/unreviewed code is encountered;
3. `False` when `type` is nonblank, is not D/E/X, and no preserved hitData field is present;
4. `null` when both `type` and all preserved hitData evidence are absent.

The raw `pitch_code` remains preserved separately. The reconstruction is part of the versioned normalization definition, not a mutation of the source file.

The Performance layer does not infer BIP existence from pitch code alone. Official play-sequence outcome semantics determine whether a PA is BIP-expected; the resolved reusable pitch evidence identifies the contact pitch and supplies trajectory/direction evidence.

## Validation

After changing the adapter from X-only to the accepted D/E/X + hitData rule, the same live Performance audit changed from:

- 2025 AAA: 68.72% core eligible, 65 false `missing_in_play_pitch` cases;
- 2024 Rookie/complex/DSL: 70.18% core eligible, 68 false `missing_in_play_pitch` cases;

to:

- 2025 AAA: 209/211 PAs (99.05%) core eligible before the foul-air screen; the only two exclusions were explicit bunts;
- 2024 ACL/DSL/FCL: 228/228 PAs (100%) core eligible before the foul-air screen;
- zero structural PA/contact mapping failures across all six games.

Historical end-to-end Performance checks also passed:

- 2005 AAA: 159/161 PAs (98.76%) core eligible before foul-air screening; two bunts excluded; zero structural mapping failures;
- 2015 AAA: 146/146 PAs (100%) core eligible; zero structural mapping failures.

## Rejected alternatives

### Treat only `X` as in play

Rejected. It drops nearly half of the observed batted-ball sequences in the recent six-game sample and is contradicted by both 2005 and 2015 release data.

### Use only nonblank `bb_type`

Rejected as the sole rule. It is strong positive evidence, but one 2005 D/E/X row lacked trajectory. Code semantics plus any preserved hitData provide a more complete reconstruction.

### Re-fetch every historical game's raw Stats API PBP just to recover `details.isInPlay`

Rejected for the universal historical bootstrap. It would discard the main value of the reusable source even though the exported data already preserve an empirically certifiable equivalent signal. Official PBP remains the authority layer for PA/result semantics and targeted adjudication.

## Consequences

- The historical MiLB pitch bootstrap remains viable; no new full-history PBP parser is required for this issue.
- `type` must be treated as MLB `details.code`, not as a documented three-value B/S/X field.
- Future unseen codes that carry hitData are still recoverable as positive in-play evidence and remain visible for audit through the raw code field.
- Changes to this reconstruction require a new normalization version and renewed cross-era certification.
