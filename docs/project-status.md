# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active branch / PR

- Working branch: `source-certification-poc`
- Open draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind. Inspect current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly **2–3 steps** and verify before expanding.
- Prefer mature public datasets, parsers, packages, and prior public work over rebuilding raw cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests belong in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate until their contracts justify combination.

## Current project stage

The source/data foundation, first batting Performance layer, historical affiliated-MiLB and MLB Current Talent evidence, chronological validation plumbing, MLB-anchored environment translation, exact age-as-of enrichment, and the first two results-only Current Talent baseline primitives are implemented.

The candidate translation has shown **independent Aug. 1 stability in 2021, 2022, and 2023**. The strongest outcome components (K and BB/HBP) recover a coherent MLB difficulty ladder in all three seasons. Contact-shape components are materially noisier and are **not** being forced monotonic or promoted merely for aesthetics.

**Baseline 0 and Baseline 1 are now implemented and unit-tested, but they have not yet been run through the real chronological future-target scoring gate. There is still no promoted Current Talent estimator.**

The next modeling gate is therefore **real 2021 Baseline 0 / Baseline 1 materialization, mapping latent predictions into actual future environments, and 90-day proper-score/calibration validation**.

## Completed milestones

### 1. Reuse-first canonical foundation

Source roles, provenance, canonical schemas, identity handling, event semantics, contact reconstruction, state replay, RE24, level/season capability gates, contextual bin-value policies, and typed persistence are implemented and tested.

Primary references:

- `docs/source-audit.md`
- `docs/source-certification-current.md`
- `docs/canonical-data-contract.md`
- `docs/adr/`

### 2. 2024 affiliated-MiLB batting Performance

Checkpoint: `docs/performance-2024-affiliated-checkpoint.md`  
Certified workflow: `31948208695`

- 14 actual leagues / 5 level groups
- 4,995 player × actual-league × season rows
- 784,285 PA
- 494,884 reusable contact events
- 764,713 screened core Performance events
- 97.50% core-profile PA coverage
- 156 unknown contacts
- 0 unvalued core events

### 3. Historical affiliated-MiLB Current Talent evidence, 2021–2023

All five post-reorganization affiliated level groups are certified for **2021, 2022, and 2023**.

Runs:

- 2021: `31979609553`
- 2022: `31971662070`
- 2023: `31971923778`

2021 combined evidence: 180,523 player-games, 4,214 players, 704,360 PA.

Checkpoint: `docs/current-talent-historical-milb-checkpoint.md`.

### 4. Leakage-safe snapshot / future-target surface

Implemented modules:

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_universal_evidence.py`

Frozen chronology:

- predictor evidence: `game_date < as_of_date`
- future target: `game_date >= as_of_date` and before exclusive horizon end
- no fake within-day ordering from game PK / row order
- actual as-of and future environments preserved

Real 2021-08-01 → 90-day five-level MiLB validation run: `31980820797`

- predictor players: 3,828
- target players: 3,631
- players on both sides: 3,245
- scoring environment rows: 3,882
- SAME_LEVEL: 3,144
- PROMOTION: 523
- DEMOTION: 212
- AMBIGUOUS_AS_OF_ENVIRONMENT: 3

### 5. Historical MLB Current Talent evidence — 2021–2023 certified

Checkpoint: `docs/current-talent-historical-mlb-checkpoint.md`  
Workflow: `.github/workflows/current-talent-historical-mlb-season.yml` — **manual-only**.

Certified runs:

- 2021: `31986504169`
- 2022: `31988255280`
- 2023: `31989561396`

| Season | Players | Player-games | PA | BB+HBP | K | Expected contacts | Observed contacts | Contact residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1,049 | 51,476 | 181,818 | 17,906 | 42,145 | 121,705 | 121,707 | +2 |
| 2022 | 693 | 48,325 | 182,052 | 16,899 | 40,812 | 124,267 | 124,269 | +2 |
| 2023 | 656 | 48,763 | 184,104 | 17,931 | 41,843 | 124,234 | 124,236 | +2 |

Every season reconciles exactly to independent official MLB player × AL/NL × season totals for PA, BB/HBP, K, expected-contact opportunity, and special non-contact outcomes. The +2 physical-contact residuals are ADR-024 diagnostics only.

Frozen historical semantics include two-strike mid-PA batter substitution attribution, interference-error outcomes, explicit 2021–2024 `ATH -> OAK`, and bounded Savant transport retries/caching.

### 6. MLB-anchored candidate environment translation — three-year stability gate passed

Implementation:

- `src/universal_baseball/current_talent_translation.py`
- `scripts/materialize_current_talent_translation_support.py`
- `.github/workflows/current-talent-translation-support.yml` — **manual-only**

Candidate method: `matched_adjacent_stint_clr_wls_v1`

Policy:

- fit only on training games strictly before cutoff;
- chronological player environment stints;
- same-day multi-environment ambiguity breaks continuity;
- only adjacent observed stints paired;
- sparse intermediate stops cannot be skipped to manufacture a transition;
- 12-component profile uses symmetric-pseudocount CLR (`0.5`);
- pair weight = `n1*n2/(n1+n2)`;
- weighted graph least squares with `MLB = 0` anchor;
- fail closed unless every fitted level connects to MLB.

#### 2021-08-01 candidate

Run: `31992143231` (readable-offset rerun; first successful fit was `31991928288`)

- 665 eligible cross-level pairs / 562 players
- all 6 levels connected to MLB
- max graph distance to MLB: 2
- AAA→MLB: 122 pairs; MLB→AAA: 112

K CLR environment effects vs MLB:

- Rookie: **-1.015**
- Single-A: **-0.707**
- High-A: **-0.482**
- AA: **-0.418**
- AAA: **-0.365**
- MLB: 0

BB/HBP:

- Rookie: **+0.860**
- Single-A: **+0.732**
- High-A: **+0.500**
- AA: **+0.312**
- AAA: **+0.228**
- MLB: 0

#### 2022-08-01 candidate

Run: `31992265175`

- 809 eligible cross-level pairs / 637 players
- all 6 levels connected to MLB
- AAA→MLB: 161 pairs; MLB→AAA: 114

K:

- Rookie: **-0.705**
- Single-A: **-0.419**
- High-A: **-0.292**
- AA: **-0.294**
- AAA: **-0.242**
- MLB: 0

BB/HBP:

- Rookie: **+0.739**
- Single-A: **+0.673**
- High-A: **+0.450**
- AA: **+0.417**
- AAA: **+0.267**
- MLB: 0

#### 2023-08-01 candidate

Run: `31992265175`

- 825 eligible cross-level pairs / 639 players
- all 6 levels connected to MLB
- AAA→MLB: 163 pairs; MLB→AAA: 120

K:

- Rookie: **-0.844**
- Single-A: **-0.518**
- High-A: **-0.402**
- AA: **-0.279**
- AAA: **-0.286**
- MLB: 0

BB/HBP:

- Rookie: **+0.920**
- Single-A: **+0.813**
- High-A: **+0.566**
- AA: **+0.484**
- AAA: **+0.416**
- MLB: 0

Interpretation:

- **BB/HBP is monotonically ordered by level in all three independent seasons.**
- **K has the same clear ladder**, with only tiny AA/AAA inversions in 2022 (~0.002) and 2023 (~0.006).
- K is consistently the cleanest fit component (weighted residual RMSE roughly **0.39–0.43**).
- BB/HBP is also useful (roughly **0.51–0.62** RMSE).
- Contact-shape components are substantially noisier / less monotonic. Do **not** constrain or promote them merely to make the ladder prettier.
- This stability result supports carrying the candidate translation into predictive baseline testing, **not freezing it as final**.

### 7. Exact age-as-of enrichment — 2021 coverage gate passed

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — **manual-only**

Age is derived from the pinned Chadwick Register DOB fields at the explicit cutoff. Partial/missing DOB is not imputed; duplicate requested MLBAM identities or invalid complete DOBs fail closed.

2021-08-01 audit run: `31992658592`

- universal training players: **4,315**
- exact DOB / exact age-as-of: **4,315**
- coverage: **100.0%**
- missing exact age: **0**
- observed age range: approximately **16.93–41.54 years**

The first baseline fit therefore requires no age-imputation branch.

### 8. Current Talent Baseline 0 / Baseline 1 primitives implemented and tested

Checkpoint: `docs/current-talent-baseline-checkpoint.md`  
Implementation CI: **`31992880494` — passed**.

Implementation:

- `src/universal_baseball/current_talent_baselines.py`
- `tests/test_current_talent_baselines.py`

#### Baseline 0

Method: `loo_age_level_population_prior_v1`

- no player-specific recent Performance in the predicted player's prior;
- exact age-as-of + actual unambiguous current level;
- default 2-year age band;
- preferred same-level + same-age-band leave-one-out peers;
- default minimum preferred peers: 12;
- fallback to same level, then global other-player pool only if needed;
- player explicitly excluded from every peer pool;
- peer evidence is already on the MLB latent reporting scale.

#### Baseline 1

Method: `translated_recency_empirical_bayes_v1`

- recency-weighted player core-profile evidence;
- evidence is aggregated at player × level first;
- each level segment is translated to MLB scale **before** a player's multi-level evidence is pooled;
- empirical-Bayes shrinkage toward Baseline 0;
- default prior strength: **100 effective core events**.

Regression tests verify translation direction, evidence conservation, translated multi-level aggregation, leave-one-out behavior, fallback behavior, shrinkage, and profile normalization.

These are **implementation primitives, not validated model winners**. Their defaults remain candidate hyperparameters until chronological scoring is complete.

## Important boundaries / not complete

Still not frozen or validated:

- real 2021 Baseline 0 / Baseline 1 predictions on the full universal cutoff population;
- mapping the latent MLB-scale prediction into each actual future target environment for likelihood scoring;
- whether Baseline 1 beats Baseline 0 out of time;
- whether the candidate translation improves future prediction versus no-translation alternatives;
- whether level-only translation is sufficient or actual league/season residual effects add out-of-time value;
- selected recency window / half-life;
- 2-year age-band width, 12-peer threshold, and 100-core-event EB prior strength;
- rolling-origin log loss / Brier / calibration validation;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, playing time/role, WAR/value, defense integration, or final ranking.

The 90-day future target currently uses complete future player-game evidence. The contract's exact **200-PA aggregate diagnostic cap is not yet applied** because the certified backbone is player-game aggregate. Do not invent within-game PA order to force exactly 200; use a certified complete-game cap policy or true PA-grain target surface first.

## Governing Current Talent contract

`docs/current-talent-validation-contract.md` remains authoritative:

- Current Talent = latent rate/profile ability **now**, conditional on opportunity.
- Preserve component profile first; scalar value is secondary.
- Environment effects learned from training-period data only.
- Primary target = next 90 calendar days; secondary 30/180/~365.
- Zero future PA is not poor talent.
- Promotions/demotions scored in actual future environment.
- Validation is chronological / rolling-origin, never random split.
- Proper scoring and calibration outrank prettier correlation.
- Richer evidence must beat simple results-only baselines out of time.

## Recommended next batch

1. Materialize real **2021-08-01 Baseline 0 and Baseline 1** profiles from the certified universal predictor evidence, exact age-as-of context, and training-only translation fit.
2. Map each latent MLB-scale profile into the **actual target environment** represented by each future scoring row, then compute 90-day multinomial/component log loss, Brier score, and calibration.
3. Compare at minimum environment-prior vs translated empirical-Bayes variants and stratify by level, age, evidence volume, and promotion/demotion transition before adding complexity.

Do not skip directly to Baseline 2, tracking/process features, Projection, or ranking.

## Useful workflows / scripts

Manual live/reuse workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-historical-mlb-season.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`
- `.github/workflows/current-talent-translation-support.yml`
- `.github/workflows/current-talent-age-coverage.yml`

Key materializers / audits:

- `scripts/materialize_current_talent_historical_milb_game_evidence.py`
- `scripts/materialize_current_talent_historical_mlb_game_evidence.py`
- `scripts/materialize_current_talent_validation_snapshot.py`
- `scripts/materialize_current_talent_validation_snapshot_multilevel.py`
- `scripts/materialize_current_talent_translation_support.py`
- `scripts/audit_current_talent_age_coverage.py`

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect current `source-certification-poc` head before editing.
5. Continue with **real 2021 Baseline 0 / Baseline 1 materialization and chronological future-target scoring**; do not re-audit closed source, MLB certification, age-coverage, or translation-support questions.
