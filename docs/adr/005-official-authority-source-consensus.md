# ADR 005 — Source consensus with narrow official adjudication

Status: accepted foundation decision  
Date: 2026-08-15

## Decision

Overlapping reusable MiLB PBP assets are **not** ordered into a global winner by filename period, GitHub asset timestamps, retrieval time, or row order.

The working pitch view is derived in stages:

1. preserve each upstream asset as an immutable source snapshot;
2. normalize every snapshot through the same versioned canonical adapter;
3. compact exact duplicate payloads but preserve distinct payload variants;
4. resolve fields by non-null consensus across comparable normalized snapshots;
5. when two non-null reusable-source values disagree, leave that source-only field unresolved and emit explicit conflict evidence;
6. allow a separately versioned **official structured source** to adjudicate only fields it directly defines, without rewriting the reusable-source observations.

Official evidence is therefore an authority overlay, not a blanket row-replacement rule.

## Evidence

The 2023 Rookie July/August raw assets shared 5,524 natural pitch keys. Raw row comparison marked all 5,524 as changed because presentation fields and string encodings drifted between assets. After canonical normalization and field-level resolution, only 16 pitches (0.29%) retained a non-null conflict: 14 in `pitcher_hand` and 2 in `batter_side`.

All 16 conflict pitches had official true-PA matchup evidence. The current official Stats API feed agreed with one reusable-source value in every case and with neither value in zero cases. This demonstrates that source-level disagreement can be kept explicit and adjudicated using a field-specific authority rather than an inferred asset chronology.

The earlier 2025 AAA March/April overlap gives the same architectural lesson: most overlap was identical, while a tiny number of fields were revised. A whole-file winner would unnecessarily replace stable evidence.

## Consequences

- Source observations remain immutable and auditable.
- A source-only derived view may contain nulls where evidence genuinely disagrees.
- The model-ready view may use official sequence identity, batter side, pitcher hand, and PA result semantics where those fields are available from official structured evidence.
- A current official value does **not** establish historical information availability. Strict vintage backtests remain governed by provenance/knowledge timestamps.
- New authority overlays must be explicit, field-scoped, versioned, and tested; they cannot silently override arbitrary reusable-source fields.
- If official evidence is unavailable or itself conflicts with certified evidence, the field remains unresolved/flagged rather than guessed.
