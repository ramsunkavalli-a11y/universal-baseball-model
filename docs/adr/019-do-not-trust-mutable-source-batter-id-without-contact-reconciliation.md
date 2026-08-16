# ADR 019 — Do not trust mutable source batter ID without contact reconciliation

**Status:** Accepted  
**Date:** 2026-08-15

## Context

The reusable armstjc PBP parser starts each official play sequence with the
correct top-level matchup batter, but inside the same sequence it mutates its
local `batter_id` variable for every `offensive_substitution` playEvent. That is
not semantically safe: an offensive substitution can be a pinch-runner replacing
a baserunner rather than a new batter.

Because later exported pitch rows reuse that mutable variable, a pinch-runner can
be exported as the batter on physical pitches or on the terminal ball in play.
The raw source must therefore not be assumed to carry authoritative participant
identity merely because its pitch/event geometry is reusable.

## Certification evidence

A deterministic audit sampled **20 games from every actual affiliated league**
represented by recent AAA, AA, High-A, Single-A, and Rookie source assets:

- 280 games total;
- 21,201 pitch-bearing official true PAs with comparable batter identity;
- 13,045 source in-play contacts with comparable identity.

Against current official top-level matchup batter IDs:

- source sequences containing more than one exported batter ID: 2 / 21,201;
- first exported pitch batter mismatch: 48 / 21,201 (**0.2264%**);
- last exported pitch batter mismatch: 50 / 21,201;
- in-play pitch batter mismatch: 28 / 13,045 (**0.2146%**).

The two multi-ID sequences behaved exactly as expected: the first physical pitch
retained the true batter while a later pinch-runner substitution changed the
subsequent exported ID.

A second diagnostic froze all 48 first-pitch mismatch cases *before* inspecting
their official substitution details. Every single case — **48 / 48** — was then
classified as the **same-sequence offensive-substitution player**, with official
narratives such as `Pinch-runner ... replaces ...`. None required an atBatIndex
shift or a separate snapshot-index-drift explanation.

Thus the observed source participant defect is narrow and understood, but a
simple "use first pitch" repair is not sufficient: some pinch-runner substitutions
occur before the first exported physical pitch in the source sequence.

## Decision

1. **Never treat armstjc per-pitch `batter` as authoritative canonical batter
   identity.** Preserve it as source evidence/provenance.
2. Do not adopt a blanket "first physical pitch batter" rule. It fixes the
   within-sequence mutation seen after an earlier pitch, but it still failed on
   48 audited sequences because the pinch-runner substitution preceded all
   exported physical pitches.
3. Standard PA outcomes (K, BB, HBP, etc.) continue to use the certified
   season-player aggregate backbone and/or official PA semantics, so this source
   mutation does not contaminate those counts.
4. The unresolved production problem is therefore much narrower: **participant
   attribution for source-derived contact trajectory/direction events**.
5. Before requiring official PBP for every historical game, test a source-heavy
   reconciliation strategy: aggregate canonical source in-play contacts by
   player/league/season and compare them with the independently certified season
   aggregate `batting_balls_in_play` totals.
6. If contact-count discrepancies are sparse and diagnostic of the known
   pinch-runner mutation, official PBP should be fetched only for the affected
   exception set. If reconciliation is broad/noisy, retain an official
   participant overlay instead.
7. No fuzzy-name correction or inferred substitution repair is allowed. Any
   exception repair promoted later must use deterministic evidence and preserve
   the original source ID.

## Why season `ballsInPlay` is a useful reconciliation target

ADR 018 established that hitter season `ballsInPlay` in the reusable aggregate
source is a broad contact count, essentially:

`AB - SO + SF + SH`

so it includes home runs and sacrifice bunts. That is much closer to the
source PBP parser's structured `details.isInPlay` concept than the usual BABIP
denominator. It therefore provides a mature, independently certified player-
season total against which source contact attribution can be checked without
replaying official PBP for every standard outcome.

## Consequences

- Reusable PBP remains accepted for physical contact geometry, trajectory, and
  spray direction.
- Player attribution for those contact events is explicitly **not yet frozen**.
- The next gate is full-season contact-count reconciliation, not a wholesale
  rebuild of historical official PBP.
- A successful exception-only strategy would materially reduce API traffic and
  implementation complexity while still refusing silent identity corruption.

## Supporting artifacts

- `scripts/audit_source_batter_identity_fidelity.py`
- `scripts/diagnose_source_batter_identity_mismatches.py`
- first audit workflow run `31925278425`
- frozen mismatch diagnostic workflow run `31925463061`
