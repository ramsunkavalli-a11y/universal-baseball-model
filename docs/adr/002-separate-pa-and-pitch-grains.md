# ADR 002: Keep Plate Appearances and Pitches as Separate Canonical Grains

- Status: Accepted for foundation design
- Date: 2026-08-15

## Context

The first MiLB source POC tested a public historical pitch-level dataset against official MLB Stats API play-by-play.

The reusable source represents physical pitch events well in the tested AAA slice after deterministic exact-duplicate normalization, but it cannot represent a valid plate appearance that contains no pitch rows. The official feed for game `779653` contains a signaled intentional walk with zero events marked `isPitch=true`. That PA is therefore correctly absent from a pitch-grain table.

The public source also does not reliably preserve the PA outcome code in its `events` field, while the official feed exposes PA results independently of pitch events.

## Decision

The canonical event foundation will contain at least two separate grains:

### `plate_appearance`

One row per official PA/play record, keyed independently of pitch existence. It owns PA-level result/outcome and matchup/context fields.

A valid PA may have zero pitches.

### `pitch`

Zero or more rows attached to a plate appearance. It owns pitch-sequence, pitch-result, location/shape/tracking fields where available.

Pitch existence must never be used as the test for whether a PA exists.

The relationship is therefore:

`game -> plate_appearance -> 0..N pitches`

not:

`game -> pitches -> reconstructed plate_appearance`

as the sole canonical path.

## Consequences

- A historical pitch bootstrap can remain useful even if it is not a complete PA source.
- Zero-pitch intentional walks and any future no-pitch PA/event types are represented without synthetic pitch rows.
- PA outcomes can be certified/enriched independently of pitch-level history.
- Pitch-level source defects do not automatically invalidate PA-level evidence, and vice versa.
- Reconciliation can explicitly test both grains: PA completeness and pitch completeness.
- Downstream Performance features can choose the correct denominator instead of inferring PA counts from pitch rows.

## Non-decision

This ADR does not freeze the complete canonical schema or every event type. It establishes only the grain boundary that the POC demonstrated is necessary.
