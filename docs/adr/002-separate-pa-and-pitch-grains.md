# ADR 002: Keep Plate Appearances and Pitches as Separate Canonical Grains

- Status: Accepted principle; parent-child relationship refined by ADR 006
- Date: 2026-08-15

## Context

The first MiLB source POC tested a public historical pitch-level dataset against official MLB Stats API play-by-play.

The reusable source represents physical pitch events well in the tested AAA slice after deterministic exact-duplicate normalization, but it cannot represent a valid plate appearance that contains no pitch rows. The official feed for game `779653` contains a signaled intentional walk with zero events marked `isPitch=true`. That PA is therefore correctly absent from a pitch-grain table.

The public source also does not reliably preserve the PA outcome code in its `events` field, while the official feed exposes PA results independently of pitch events.

## Decision at this stage

Plate-appearance evidence and pitch evidence must not be collapsed into a single pitch-grain table.

A valid PA may have zero pitches, so pitch existence must never be used as the test for whether a PA exists. PA outcomes must be certified/enriched independently of pitch-level history.

The original version of this ADR represented the relationship as:

`game -> plate_appearance -> 0..N pitches`

Further certification later found physical pitches inside official `allPlays` sequences whose final event is **not** a plate appearance, such as an inning-ending caught stealing. ADR 006 therefore refines the parent grain to:

`game -> play_sequence -> 0..N pitches`

with true plate appearances as an officially classified subset/view of play sequences.

The core principle of this ADR remains accepted: **PA-level and pitch-level evidence are separate grains and neither can be reconstructed losslessly from the other alone.**

## Consequences

- A historical pitch bootstrap can remain useful even if it is not a complete PA source.
- Zero-pitch intentional walks and any future no-pitch PA/event types are represented without synthetic pitch rows.
- PA outcomes can be certified/enriched independently of pitch-level history.
- Pitch-level source defects do not automatically invalidate PA-level evidence, and vice versa.
- Reconciliation can explicitly test true-PA completeness and pitch completeness.
- Downstream Performance features can choose the correct denominator instead of inferring PA counts from pitch rows.
- ADR 006 must be used for the canonical parent-child schema because not every pitch belongs to a completed PA.

## Non-decision

This ADR does not freeze the complete canonical schema or every event type. It establishes the grain-separation principle; ADR 006 supplies the broader sequence parent required by later evidence.
