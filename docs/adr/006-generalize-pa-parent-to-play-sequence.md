# ADR 006: Generalize the event parent from plate appearance to play sequence

- Status: Accepted for foundation design
- Date: 2026-08-15
- Refines: ADR 002

## Context

ADR 002 correctly established that a pitch-grain table cannot be the sole source of plate appearances because a valid PA can contain zero physical pitches. The canonical design therefore separated plate appearances from pitches.

Further source certification found the opposite edge case: a physical pitch can exist inside an MLB Stats API `allPlays` sequence that **does not become a plate appearance**. In 2023 ACL game `743157`, `atBatIndex=26` contains a physical ball to Quinn McDaniel and ends with Charlie Szykowny caught stealing second. MLB's official event semantics classify the sequence result `caught_stealing_2b` as a non-PA. The reusable pitch source correctly retains the pitch.

Therefore the relationship in ADR 002—`plate_appearance -> 0..N pitches`—is still incomplete. It handles zero-pitch PAs, but it cannot represent pitches from an unfinished batting confrontation without inventing a PA that official scoring says never occurred.

The Stats API already provides a natural broader grouping: `game_pk + atBatIndex`. This groups a matchup/play sequence whether its final structured result is a true PA, a runner event, or another known non-PA event.

## Decision

The canonical event foundation will use a **play/matchup sequence** as the parent grain above pitches.

### `play_sequence`

One row per official Stats API `allPlays` sequence, keyed by `game_pk + atBatIndex` (with provenance/source version fields in the real schema).

It owns structured sequence-level evidence such as:

- official result event code and description;
- matchup batter/pitcher identities as represented by the official sequence;
- inning/half-inning/context;
- official `is_plate_appearance` classification from the versioned event-type semantics;
- source/provenance and data-quality flags.

A sequence may be a true plate appearance or a known non-PA event.

### `pitch`

Zero or more physical pitch rows attach to a play sequence by `game_pk + atBatIndex`, with `pitch_number` (and source provenance) distinguishing pitches.

A sequence can therefore have:

- zero pitches and `is_plate_appearance=true` — e.g. a signaled intentional walk;
- one or more pitches and `is_plate_appearance=true` — the ordinary case;
- one or more pitches and `is_plate_appearance=false` — e.g. an inning-ending caught stealing before the batter completes a PA;
- zero pitches and `is_plate_appearance=false` — runner/game actions that still need structured classification if retained.

### `plate_appearance`

A plate appearance is a **classified subset/view of play sequences**, not the universal parent of every pitch.

It may later be materialized for convenience, but its membership is governed by the frozen official event-type semantics from ADR 004.

The relationship is therefore conceptually:

`game -> play_sequence -> 0..N pitches`

with:

`plate_appearance = play_sequence where is_plate_appearance = true`

rather than requiring every pitch to have a PA parent.

## Why this is preferable to inventing synthetic PAs

Creating a synthetic PA for a pitch followed by a caught stealing would distort PA denominators and make reconciliation disagree with official boxscores. Dropping the pitch would lose real pitch evidence. The broader sequence grain preserves both facts without contradiction.

## Identity consequence

The reusable historical pitch source carries a raw `batter` field, but certification found that its upstream parser changes `batter_id` on **every** `offensive_substitution`, including position-code 12 pinch-runners. Three sampled batter mismatches were exactly pinch-runners incorrectly replacing the real batter in the source row.

Canonical sequence-level batter identity therefore comes from the official structured sequence, not the reusable source's mutated `batter` column. The raw source value remains provenance/debugging evidence. Pitch-level participant changes inside genuinely unusual mid-sequence substitutions may require a separate targeted reconstruction later; they should not be guessed during baseline normalization.

## Consequences

- Zero-pitch PAs remain representable without synthetic pitches.
- Physical pitches from non-PA sequences remain representable without synthetic PAs.
- PA denominators remain governed by official event semantics and continue to reconcile to boxscores.
- The reusable pitch bootstrap can be joined to official sequence/PA evidence without treating its grouping labels as scoring semantics.
- Source-only `atBatIndex` groups should be called **pitch-bearing sequences**, not source PAs.
- Canonical schemas should keep raw source participant IDs separately from resolved/canonical identities.
- ADR 002 remains correct about separating PA-level and pitch-level evidence, but its parent-child relationship is superseded by this broader sequence grain.

## Non-decision

This ADR does not require a complete baserunning/actions model now. It establishes only the minimum parent grain necessary to represent the edge cases already observed without data loss or false scoring records.
