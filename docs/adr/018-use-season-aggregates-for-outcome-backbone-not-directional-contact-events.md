# ADR 018 — Use season aggregates for the outcome backbone, not directional contact-event counts

**Status:** Accepted  
**Date:** 2026-08-15

## Context

ADR 013 accepted reusable armstjc season-player batting/pitching releases for
mutually available standard outcome counts after a completed-2024 AAA/Rookie
gate. Before designing the production historical Performance backfill, we tested
whether those files could replace substantially more play-by-play work.

The upstream extractor already preserves fields beyond PA/BF, K, BB, HBP, and
hits: ground/air/fly/pop/line outs, trajectory-specific hits, balls in play,
pitch count, swings, and whiffs. If those fields represented certified
one-contact-per-row event counts, they could have supplied much of the
FaBIO-style profile without historical PBP.

A completed-2024 audit therefore covered all current affiliated levels:
Triple-A, Double-A, High-A, Single-A, and Rookie. Ten source assets (batting and
pitching at each level) were checked for grain, arithmetic semantics, and a
deterministic official player-season sample from every actual league.

## Evidence

Across the ten files there were no duplicate groups at
`season + league + team + player` grain. The independent official sample covered
28 player-league records and every mutually exposed field matched exactly:
**28/28**.

The official person-season representation independently exposed six additional
fields beyond the previously certified outcome backbone:

- hitter ground outs;
- hitter air outs;
- hitter pitch count;
- pitcher ground outs;
- pitcher air outs;
- pitcher pitch count.

Those six fields matched exactly in every applicable sampled league.

### Batter `ballsInPlay` has broader semantics than the BABIP denominator

For 2024 batting rows, the source `ballsInPlay` field is almost exactly:

`AB - SO + SF + SH`

rather than the common fieldable-BIP/BABIP denominator:

`AB - SO - HR + SF`.

Equivalently, the difference from the BABIP denominator is `HR + SH` in every
row except one Double-A residual case described below. Thus the source field is
a broad contact count that includes home runs and sacrifice bunts. It must not
be silently substituted for a fieldable-BIP denominator.

Pitcher `ballsInPlay`, by contrast, exactly satisfied
`AB - SO - HR + SF` in all 2024 audited rows. This is useful as a consistency
check but adds little independent information because the components are already
available.

### Trajectory hit/out columns are not contact-event counts

For batters, `groundOuts`, `flyOuts`, `popOuts`, and `lineOuts` count **outs
recorded**, not guaranteed one-per-batted-ball events. Summing trajectory hits,
trajectory outs, and reached-on-error values did not reproduce the source BIP
count, and subtracting GIDP did not resolve the difference. Double plays and
other scoring semantics make a naive reconstruction invalid.

For pitchers, the reusable season file does not export `groundHits` at all, so a
complete trajectory distribution cannot be reconstructed from the aggregate
file even before addressing the out-count issue.

Therefore the detailed aggregate trajectory columns are descriptive source
fields, not a substitute for the certified PBP contact-event mapper.

### Swings and whiffs remain process candidates, not certified physical evidence

Aggregate pitch, swing, and whiff fields are structurally present and satisfy
basic inequalities (`whiffs <= swings <= pitches`) throughout the 2024 files.
However, the independent person-season endpoint exposes pitch count but not the
swing/whiff totals used by the upstream BDFED extractor.

More importantly, ADR 016 demonstrates that some Rookie league-seasons contain
synthetic outcome-minimal intermediate pitch sequences. Presence of an aggregate
swing/whiff field therefore does not prove the underlying physical sequence is
reliable. Those fields remain candidates for a later Current Talent/process gate
and are not promoted by this ADR.

### Rare PA residuals must remain explicit

The familiar batting identity

`PA = AB + BB + HBP + SH + SF + CI`

was exact in all 2024 audited batting rows except one Double-A player-team row:
247 PA versus 246 accounted standard components. The same row also had one extra
broad BIP beyond the usual aggregate formula.

The architecture therefore preserves a signed
`batting_other_plate_appearances = PA - standard_components` residual rather
than forcing equality or guessing the rare event type. Negative residuals are
quality flags, not values to clamp away.

## Decision

1. **Use season-player aggregates as the historical standard-outcome backbone**
   across AAA, AA, High-A, Single-A, and Rookie where the completed-season file
   is available and passes asset validation.
2. Standardize and allow production use of **ground outs, air outs, and pitch
   count** as auxiliary aggregate fields because they are independently exposed
   and reconciled.
3. Preserve an explicit signed **batting other-PA residual** instead of assuming
   the standard PA component identity is universally exhaustive.
4. Do **not** use aggregate ground/fly/pop/line hit/out columns as FaBIO
   trajectory-event counts.
5. Do **not** infer Pull/Center/Opposite direction from aggregate fields;
   direction remains PBP-derived.
6. Do **not** promote aggregate swings/whiffs to physical-process evidence until
   a separate league-season fidelity gate supports them.
7. Keep pitching sacrifice-bunt absence explicit; do not invent complete BF
   decomposition from the current pitching aggregate files.

## Consequences for the historical Performance backfill

The production historical pipeline no longer needs official all-game PBP merely
to recover standard player outcome totals. It should combine:

- certified season aggregates for PA/BF and standard outcome counts;
- reusable armstjc play/pitch evidence for contact-event trajectory and
  Pull/Center/Opposite direction;
- targeted official play-sequence evidence for authoritative participants,
  rare/special PA semantics, foul-air screening, and reconciliation;
- sampled official state/PBP evidence for league-season RE24/bin-value
  calibration rather than replaying every game solely for standard totals.

This is deliberately narrower than the initially tempting interpretation of the
rich season files. Reuse is maximized where the semantics are certified, while
PBP remains responsible for information that aggregates cannot faithfully
represent.

## Implementation

- `src/universal_baseball/season_stats.py` standardizes the certified auxiliary
  fields and exposes `with_batting_pa_residual`.
- `tests/test_season_aggregate_reuse.py` protects those semantics.
- `scripts/audit_all_level_season_profile_reuse.py` is the supporting live-source
  audit; after passing, its workflow is manual-only.
- ADR 016 remains the governing pitch-process fidelity boundary.
