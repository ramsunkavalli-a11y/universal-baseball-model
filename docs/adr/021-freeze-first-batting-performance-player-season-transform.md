# ADR 021 — Freeze the first batting Performance player-season transform

**Status:** Accepted  
**Date:** 2026-08-16

## Context

The foundation branch had already certified the source roles, exhaustive/screened Performance taxonomy, state replay, RE24 mechanics, level-specific bin-value regularization, season-player aggregate backbone, and exception-only contact-participant authority policy. The remaining architectural question was whether those pieces could be assembled into a reproducible player-level output without silently reintroducing an all-history official-PBP dependency or collapsing Performance into Current Talent.

The first production POC therefore targeted one completed, independently well-certified environment family: **2024 AAA** (Pacific Coast League + International League).

## Production evidence split

The accepted batting Performance transform uses:

1. **season-player aggregates** for PA, BB, HBP, K, and broad contact totals;
2. **resolved reusable armstjc PBP** for physical contact, trajectory, coordinates, and certified result narrative;
3. **resolved player-game batting controls** to detect contact-participant attribution defects;
4. **official MLB Stats API matchup batter** only for games triggered by the ADR 020 residual rule;
5. the final screened contact classifier for Pull/Center/Opposite × GB/LD/OFFB plus IFFB;
6. sampled official state transitions + RE24 for contextual league-season bin means; and
7. the frozen level-specific bin-value policy before player aggregation.

No age adjustment, talent shrinkage, projection, playing-time forecast, defense, WAR conversion, or overall ranking is part of this transform.

## Canonical player grain

The first output grain is:

`season + actual league + MLBAM player`

Team rows in the season aggregate backbone are summed before player-level Performance output, so a player traded or reassigned between teams inside the same actual league has one player-league-season row.

The long-form companion profile adds:

`core_bin`

and retains bin occurrence count, share of PA, calibrated mean run value, expected run-value contribution, and estimator provenance.

## Core-bin production vocabulary

The descriptive direction layer remains:

- `pull`
- `center`
- `opposite`

The compact production bin vocabulary is:

- `BB_HBP`
- `K`
- `IFFB`
- `PULL_OFFB`, `CENTER_OFFB`, `OPPO_OFFB`
- `PULL_LD`, `CENTER_LD`, `OPPO_LD`
- `PULL_GB`, `CENTER_GB`, `OPPO_GB`

Earlier audit artifacts emitted `OPPOSITE_*` because they concatenated the descriptive direction string directly. Production calibration normalizes that legacy label one-to-one to `OPPO_*`; event membership and prior shrinkage evidence are unchanged.

## 2024 AAA end-to-end result

Successful workflow run: `31944146638`.

The POC produced:

- **922** player × actual-league × season rows;
- **172,462** total PA;
- **111,884** resolved reusable physical contacts;
- **244** games triggered for official participant authority;
- **12,725** contacts under official participant overlay;
- **254** contact batter IDs changed by the overlay;
- **111,884** final classified contacts;
- total reusable-contact minus season-aggregate broad-contact residual: **+6**;
- **168,193** core Performance events;
- core-profile coverage: **97.52% of PA**;
- non-core contacts: **1,299 bunts**, **2,872 foul-air exclusions**, **23 unknown contact classifications**;
- **24** calibrated AAA league-bin rows (12 bins × 2 leagues);
- **0** unvalued core events;
- **922/922** unique DuckDB player-season keys after Parquet round trip.

The +6 total contact residual is not missing source evidence. ADR 020 independently showed the same +6 difference between official PBP `isInPlay` contacts and boxscore-style `AB - SO + SF + SH` accounting in the exception set. Production therefore preserves that definition residual instead of forcing equality.

## Calibration details

The first production artifact used the already-certified deterministic 45-game-per-league 2024 AAA calibration sample. Both PCL and IL observed all 24 base-out states and had full screened-core RE24 coverage in the calibration frame.

Direct league-season means are then passed through the frozen AAA policy:

- same-bin peer-AAA prior;
- `lambda = 25` prior-equivalent occurrences;
- no adjacent-level or universal-MiLB fallback.

The 25-occurrence prior strength had already survived 2025 split-half/five-fold testing and a pre-specified independent 2024 AAA confirmation before this player-season transform was built.

## Decision

1. Accept the 2024 AAA POC as the first production-valid batting **Performance** player-season transform.
2. Keep the aggregate outcome backbone, reusable contact layer, participant authority, contact classification, bin calibration, and player aggregation as separate production modules.
3. Preserve both summary and long-form player-bin outputs.
4. Expose coverage and authority metadata in player outputs, including contact residual, core-profile coverage, unknown contact count, and official-overlay contact count.
5. Keep contextual expected run-value totals separate from later player-talent shrinkage. A high or low Performance value is an observed/contextual output, not yet Current Talent.
6. Preserve non-core/special/unknown events rather than forcing them into the 12-bin value profile.
7. Treat `OPPO_*` as the canonical compact production name for opposite-field bins; normalize legacy `OPPOSITE_*` audit labels at the calibration boundary only.
8. Do not scale historical backfill blindly from this one environment family. The next validation is a completed multi-level season using the already-frozen level-specific value policies and level/era evidence capability rules.

## Consequences

- The project has crossed from source certification into a real player-level Performance artifact without skipping the layer boundaries in the charter.
- Historical player-season Performance can be built largely from reusable public files plus a narrow official exception queue, rather than all-game official replay.
- Production tables carry enough evidence metadata for later Current Talent modeling to distinguish performance, sample size, coverage, and source quality.
- The next scale gate can focus on cross-level generality rather than reopening AAA source semantics.

## Supporting implementation

- `src/universal_baseball/armstjc_contacts.py`
- `src/universal_baseball/contact_identity_overlay.py`
- `src/universal_baseball/contact_profile.py`
- `src/universal_baseball/bin_value_calibration.py`
- `src/universal_baseball/performance_season.py`
- `scripts/build_batting_performance_season_poc.py`
- `.github/workflows/batting-performance-season-poc.yml`
