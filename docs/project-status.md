# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read this before reconstructing project state from old commits or conversation history.

## Active branch / PR

- Working branch: `source-certification-poc`
- Open draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind the active work. Do not assume `main` represents current project state.

## Collaboration / execution rules

- Work in small batches of roughly **2–3 steps** and verify each batch before expanding scope.
- Prefer mature public datasets, parsers, packages, and prior public work over rebuilding raw-source cleanup from scratch.
- When raw play-by-play becomes necessary, deliberately evaluate reusable options first.
- Surface early errors instead of compounding them through large multi-step changes.
- Heavy live-source certification workflows should remain **manual-only after their gate passes**; deterministic regression tests belong in normal CI.
- Do not collapse **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** into one model layer.

## What is complete

### 1. Reuse-first source / canonical foundation

The source architecture is sufficiently frozen for current modeling work. Official MLB data is reconciliation authority, while reusable historical datasets/parsers are preferred working inputs when they survive certification. Canonical schemas, provenance, event semantics, identity handling, contact reconstruction, state replay, RE24, level/season capability gates, and contextual bin-value policies are implemented and tested.

Primary references:

- `docs/source-audit.md`
- `docs/source-certification-current.md` — foundation/source snapshot; its old roadmap language should not override this file
- `docs/canonical-data-contract.md`
- `docs/adr/`

### 2. First production-shaped batting Performance layer

Completed-2024 affiliated batting Performance is materialized across **14 actual leagues / 5 affiliated level groups**.

Certified workflow run: `31948208695` (`affiliated-batting-performance-2024`).

Key totals:

- 4,995 player × actual-league × season rows
- 784,285 PA
- 494,884 classified reusable contact events
- 764,713 screened core Performance events
- 97.50% core-profile PA coverage
- 52,634 player-bin rows
- 168 league-bin value rows
- 156 unknown contacts (0.032%)
- 0 unvalued core events

See `docs/performance-2024-affiliated-checkpoint.md`.

### 3. Historical Current Talent evidence foundation

Post-reorganization affiliated-MiLB historical player-game evidence is certified for **2021–2023**, all five level groups.

Full-season validation runs:

- 2021: `31979609553`
- 2022: `31971662070`
- 2023: `31971923778`

2021 final combined evidence totals:

- 180,523 player-game rows
- 4,214 players
- 14 actual leagues / 5 level groups
- 704,360 PA
- 438,970 expected result contacts
- 439,034 observed physical contacts
- +64 net contact residual
- 686,903 core profile events
- 554 unknown contacts
- +8 summed PA-accounting residual

The historical evidence uses **retrospective event-cutoff corrected history, not a vintage information set**.

See `docs/current-talent-historical-milb-checkpoint.md` and ADRs 024–027.

### 4. Leakage-safe Current Talent snapshot / target surface

The validation contract is implemented far enough to build deterministic predictor snapshots and future target windows without fitting talent.

Important modules:

- `src/universal_baseball/current_talent_evidence.py`
  - validates player-game evidence
  - keeps PA/result and contact/profile denominators separate
  - builds pre-cutoff predictor snapshots
  - supports hard lookbacks and recency weighting
- `src/universal_baseball/current_talent_validation.py`
  - freezes date-only cutoff semantics
  - defines 30/90/180/365-day horizons
  - contains future-window / aggregate-cap helpers
- `src/universal_baseball/current_talent_validation_dataset.py`
  - builds predictor + target datasets
  - preserves the actual target environment
  - freezes actual as-of environment
  - labels same-level, promotion, demotion, MLB debut, MLB-to-MiLB, and ambiguous transitions
- `src/universal_baseball/current_talent_universal_evidence.py`
  - combines source-specific player-game evidence on the universal contract

Current cutoff semantics:

- predictor evidence: `game_date < as_of_date`
- future target evidence: `game_date >= as_of_date` and before the exclusive horizon end
- do not invent within-day chronology from game PK or row order

### 5. First real multilevel validation checkpoint

A real five-level affiliated-MiLB snapshot was validated for **2021-08-01**, primary **90-day** future horizon.

Successful workflow run: `31980820797`  
Artifact: `current-talent-validation-snapshot-multilevel-2021-8`

Combined evidence:

- 4,214 players
- 180,523 player-games
- 704,360 PA

Validation surface:

- predictor players: **3,828**
- future target players: **3,631**
- scored players present on both sides: **3,245**
- future players without predictor evidence: **386**
- target environment rows: **4,353**
- scoring rows: **3,882**

Real transition rows:

- SAME_LEVEL: **3,144**
- PROMOTION: **523**
- DEMOTION: **212**
- AMBIGUOUS_AS_OF_ENVIRONMENT: **3**

This confirms that cross-level future outcomes can remain in the actual environment where they occurred instead of forcing players to remain at one level.

The first multilevel attempt (`31980480645`) failed only because High-A output filenames use the sanitized token `aplus` rather than `a+`. The explicit mapping was fixed; no evidence or acceptance rule was weakened.

A one-level 2021 Rookie/complex Aug. 1 validation run also passed end-to-end: `31980211738`.

Both live validation workflows are back to **manual-only** after certification. Normal CI after cleanup passed in run `31981095926`.

## Important boundaries / things NOT complete

There is **no promoted Current Talent estimator yet**. In particular, the repo has not yet frozen or validated:

- leakage-safe environment / level translations to the MLB reporting anchor;
- age/environment priors;
- Baseline 0 (environment prior);
- Baseline 1 (Marcel-style empirical Bayes player evidence);
- rolling-origin model fits / proper-score validation;
- final uncertainty model;
- richer process/tracking/scouting evidence in Current Talent;
- Projection, playing-time/role, WAR/value, defense integration, or final overall ranking.

The current five-level checkpoint is affiliated MiLB only. **Universal historical validation still needs MLB included** so MLB-debut and MLB-to-MiLB transition strata are exercised in real data.

The 90-day future target currently uses all eligible complete future game/profile evidence for proper-score preparation. The contract's exact **200-PA player-aggregate diagnostic cap is not yet applied in `current_talent_validation_dataset.py`** because the certified historical outcome backbone is player-game aggregate. Do not fabricate within-game PA order merely to hit 200 exactly; either use a certified complete-game cap policy or a true PA-grain future event surface before claiming the exact cap.

## Current modeling contract

`docs/current-talent-validation-contract.md` governs the next layer. The key rules are:

- Current Talent = latent rate/profile ability **now**, conditional on opportunity.
- Preserve the component profile first; scalar value is secondary.
- Learn environment effects only from training-period data.
- Primary target = next 90 calendar days; secondary horizons 30/180/~365 days.
- Zero future PA is not poor talent.
- Promotions/demotions are scored in the environment where the future outcomes actually occur.
- Validation is chronological / rolling-origin, not random split.
- Proper scoring and calibration matter more than prettier correlation.
- Richer evidence must beat simple results-only baselines out of time.

## Recommended next batch

Do **not** jump directly to a complicated talent model.

1. **Environment translation foundation:** define and implement leakage-safe training-only environment/level translation with MLB as reporting anchor. Reuse matched-player transitions / repeated-player evidence where possible and preserve actual league/season context.
2. **Baseline 0 / Baseline 1 only:** environment prior, then transparent empirical-Bayes recent-performance baseline with recency and evidence strength.
3. **Validate before expanding:** run chronological snapshots across multiple cutoffs/seasons, add MLB to the historical surface, report proper scores/calibration plus transition and censoring strata, and resolve the aggregate-PA-cap diagnostic honestly.

Only after that gate passes should Baseline 2 or richer process/tracking inputs be considered.

## Useful workflows / scripts

Manual live workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`

Validation materializers:

- `scripts/materialize_current_talent_historical_milb_game_evidence.py`
- `scripts/materialize_current_talent_validation_snapshot.py`
- `scripts/materialize_current_talent_validation_snapshot_multilevel.py`

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-historical-milb-checkpoint.md` and `docs/performance-2024-affiliated-checkpoint.md` only as needed for evidence detail.
4. Inspect the current head of `source-certification-poc` before editing; the branch may advance independently.
5. Continue in a small verified batch rather than re-auditing already-closed source questions.
