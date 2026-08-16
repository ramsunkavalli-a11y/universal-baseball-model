# ADR 025 — Start Current Talent validation in the post-reorganization affiliated era

Status: Accepted  
Date: 2026-08-16

## Context

Current Talent requires multiple seasons of player-game outcome/contact evidence so predictors can be built strictly before an as-of cutoff and evaluated on later baseball events. The public armstjc release history reaches well before 2021, but filename presence alone is not sufficient evidence that old seasons share the same competitive-environment surface as the current affiliated minor leagues.

The historical source inventory was therefore split into two planning gates:

1. **source-family presence** — at least one PBP and one player-game asset exist for a year × filename-level cell;
2. **period parity** — the observed filename-period sets match between PBP and player-game releases at every requested current filename level.

A separate player-game-only actual-league mapping audit then sampled two large assets per year × filename level for 2019 and 2021–2024. It observed regular-season positive-PA league IDs directly from source rather than projecting the frozen 2024 map backward.

That mapping audit passed its internal gate: no missing sampled year-level cells, no cross-level league-ID conflicts within a season, no player-game league-identity conflicts, and no game-date/source-year mismatches.

The observed map nevertheless shows a real structural break:

- **2021–2024 are stable** on the current affiliated surface:
  - AAA: 112, 117
  - AA: 109, 111, 113
  - High-A filename group: 116, 118, 126
  - Single-A filename group: 110, 122, 123
  - Rookie/complex: 121, 124, 130
- **2019 is a distinct pre-reorganization era**:
  - AAA source also contains league 125;
  - the league groups represented under the `a+` and `a` filenames differ from the post-2021 mapping;
  - the historical affiliated structure also included surfaces not represented by the current five filename groups, so a complete pre-reorganization model surface requires an explicit historical extension rather than a silent cast into 2024 labels.

The project needs chronological model validation soon; it does not need every historical structural era solved before a transparent Baseline 0 / Baseline 1 can be tested.

## Decision

The **initial batting Current Talent historical materialization and rolling-origin validation era is 2021–2024**.

This means:

- 2021–2024 may share one explicit post-reorganization year × filename-level → actual-league mapping after each materialized season passes its own source/reconciliation gates;
- 2024 remains the already-certified anchor season, not a source of future information for earlier cutoffs;
- 2021–2023 game evidence must still be independently materialized and audited before entering training;
- no 2024 season-end totals, values, participant corrections, or future environment estimates may be used as predictors at an earlier cutoff unless the field is proven to be event-time-safe and the validation contract permits it;
- initial rolling-origin experiments should use the available post-reorganization sequence (for example training history through 2022 and evaluating 2023, then training through 2023 and evaluating 2024), with exact folds determined only after historical materialization coverage is measured.

**2019 is retained as a later historical-extension candidate, not rejected as bad data.** Before it may enter the universal training surface, a separate pre-reorganization gate must:

1. define the era-specific affiliated level/league map from source evidence;
2. decide how league 125 is scoped rather than inheriting the current affiliated assumption;
3. represent historical affiliated levels that disappeared or changed in the 2021 reorganization;
4. certify the same player-game/PBP/contact/participant semantics used by the post-2021 path;
5. quantify whether adding the era materially improves out-of-time Current Talent validation after accounting for structural translation uncertainty.

## Why this is preferable

Starting with 2021–2024 gives the first Current Talent baselines multiple chronological seasons while keeping the competitive-environment topology stable. It avoids spending the first model iteration on pre-reorganization taxonomy engineering and, more importantly, avoids silently treating materially different historical league structures as if they were the same environments.

This is consistent with the validation-first rule: establish a leakage-safe simple baseline on the cleanest broadly universal history, then expand the evidence surface only when the extra history can be represented rigorously and demonstrates value.

## Non-decisions

This ADR does **not**:

- certify 2021–2023 PBP or player-game evidence for modeling;
- freeze environment translation coefficients;
- choose Current Talent recency weights or shrinkage strength;
- choose age effects;
- define Projection, playing time, WAR, or rankings;
- declare 2019 unusable;
- claim source filename periods are baseball chronology.

## Required next gates

1. Generalize the 2024 MiLB player-game evidence materializer to accept an explicit season and explicit era-safe actual-league map rather than importing 2024 assumptions implicitly.
2. Run a scoped historical POC across at least one upper-minors and one Rookie/complex slice before full 2021–2023 materialization.
3. Audit historical player-game outcome resolution, contact classification, participant authority, chronology, and coverage.
4. Materialize the accepted 2021–2024 game-evidence surface.
5. Construct deterministic as-of snapshots and future windows from game evidence only.
6. Fit and evaluate Baseline 0 and Baseline 1 before adding richer process/tracking evidence.
