# Hitter v2 historical expansion source contract

Date: 2026-08-25

Status: source-audit contract; no model fit or score authorized

## Scientific purpose

Older history can add repeated player seasons, movement pairs, and evidence for
component stability. It is not assumed to be exchangeable with 2021-2025.
Before it enters a forecast, the source must pass the same fail-closed terminal
PA and official-count accounting used by Hitter v2 Stage 1.

This gate tests source compatibility only. It does not estimate whether older
history improves a projection and it does not open protected 2026 outcomes.

## Separate source lanes

### MiLB 2017-2019

The public armstjc release is the candidate PBP mirror and its player-game
release is the independent structured accounting authority. Filename month and
level are inventory labels, not canonical league or participant authority.

- **2019 first:** PBP and player-game periods match at AAA, AA, High-A, A, and
  rookie. This is the first proposed full backfill.
- **2017 second:** periods also match at all five levels. It is held behind 2019
  so the nearest pre-2021 season establishes the historical workflow first.
- **2018 conditional:** AAA and AA have paired period coverage. High-A, A, and
  rookie have only a small overlapping portion of player-game authority and
  remain excluded unless another certified official source closes the gap.
- **2020:** no affiliated MiLB season occurred, so no MiLB rows, neutral values,
  or synthetic continuity records may be manufactured.

Every accepted MiLB terminal PA must retain the raw asset, season, game,
at-bat, terminal pitch, batter authority, actual league ID, narrative result,
classification status, and exception status. Actual league comes from a unique
same-game structured value; filename level is never a substitute.

### MLB 2020

MLB played a shortened 2020 regular season. It is a real outcome season in a
separate lane, not a replacement for the missing MiLB season. The proposed
source is the existing MLB Hitter v2 architecture: pitch/PA evidence from a
checksum-pinned public Statcast/Savant extract, official player-game and season
totals as reconciliation authorities, and an explicit team-to-league map.

The 2020 lane is not certified by this audit because the current committed MLB
artifact registry begins in 2021. A later source-only checkpoint must pin the
2020 files and prove exact player-game and season reconciliation before any
model can use them.

## Reused cleanup and accounting rules

1. Read quarantined CSV fields as text before making type decisions.
2. Normalize only declared aliases (`leauge_id` to `league_id` and
   `leauge_name` to `league_name`); an alias/canonical conflict fails.
3. Use `(game_pk, at_bat_number, pitch_number)` as the raw PBP key and retain
   duplicate/revision metrics.
4. Define the terminal pitch as the maximum structured pitch number per game
   and at-bat. Collapse exact/repeated terminal snapshots only when normalized
   narratives agree; substantive conflicts fail.
5. Repair only narrow whitespace and demonstrated UTF-8/Latin-1 display
   artifacts for duplicate comparison. Never reinterpret baseball semantics.
6. Require source terminal batter agreement unless a certified participant
   overlay supplies the identity. Unresolved identity fails closed.
7. Derive actual league only from a unique same-game player-game value and
   validate any native PBP league value against it.
8. Resolve overlapping official player-game snapshots only by exact consensus
   or unique component-wise dominance. Non-monotonic totals, conflicting game
   metadata, or conflicting positive-PA teams fail closed.
9. Reconcile PA and every terminal outcome at player-game and player-season
   grain, retaining declared unique repairs and all exceptions.
10. Preserve source vintage, retrieval time, bytes, SHA-256, filename period,
    and coverage/exclusion metrics for every asset.
11. Treat exhibition- and postseason-only filename periods as distinct source
    capabilities. They cannot stand in for a regular-season compatibility
    sample or enter a regular-season forecast history silently.

## Historical acceptance gates

A season-level/level-level cell may enter a later materialization only if:

- all intended PBP periods have an independent player-game authority or an
  explicitly bounded missing-period exclusion;
- the required PBP and official batting fields parse without silent defaults;
- regular-season PBP games have unique same-game league authority;
- terminal descriptions are unique after only the declared normalization;
- terminal batter authority and the exhaustive Hitter v2 taxonomy pass;
- official player-game snapshots resolve or are retained as failed-closed
  exceptions;
- coverage and exceptions are reported by season, level, league, period, and
  source asset; and
- the full repository tests and lint pass.

Passing these gates certifies source accounting, not predictive usefulness.

## Later model-use contract

No historical row may enter a candidate until full materialization is separately
authorized and frozen. If authorized later, 2020 must receive a declared
short-season reliability/exposure treatment; the missing 2020 MiLB season must
be represented as an observation gap, not zero talent; chronology must remain
strict; and promotion must still be determined only by the frozen out-of-time
comparison against Marcel and the permanent baselines.

## Current boundary

This contract authorizes representative compatibility auditing only. Bulk
download/materialization, estimator changes, hyperparameter changes, scoring,
and protected 2026 access remain closed.
