# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active branch / PR

- Working branch: `source-certification-poc`
- Open draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly **2–3 steps** and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate until their contracts justify combination.
- **Pause at meaningful project junctures to update repository documentation before continuing.** Refresh this file after a major gate passes, a material modeling/architecture decision is frozen, or the recommended next batch changes.

## Current project stage

The project is in **chronological Current Talent model validation**.

Baseline 1 has a strong three-year Aug. 1 confirmation over Baseline 0 using unchanged candidate settings. A controlled translation ablation is now also complete.

### Baseline 1 vs Baseline 0 — fixed settings

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

Lower is better. Settings were unchanged across years:

- season-to-date evidence;
- 90-day recency half-life;
- Baseline 1 prior strength = 100 effective core events;
- Baseline 0 age-band width = 2 years;
- minimum preferred age-level peers = 12.

### Translation ablation — fitted CLR level effects vs zero offsets

Run: **`31994550684`**.

The ablation holds the entire Baseline 0/1 and scoring pipeline fixed and replaces only fitted `clr_environment_effect` values with zero. Baseline 0 still knows current level through its peer prior; this isolates the learned observation-layer translation rather than removing all level information.

Baseline 1 fitted-translation minus zero-offset results:

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 | 13/21 | 12/21 | 9/12 | 6/12 |
| 2022-08-01 | **-0.000838** | **-0.000246** | 17/21 | 17/21 | 3/12 | 9/12 |
| 2023-08-01 | **-0.001093** | **-0.000263** | 16/21 | 15/21 | 6/12 | 8/12 |

Interpretation:

- fitted translation improves Baseline 1 aggregate **log loss in all three years**, but by a small amount;
- Brier is effectively flat/slightly worse in 2021 and modestly better in 2022/2023;
- gains are not universal across components or strata;
- Baseline 0 translation effects are inconsistent across years;
- therefore the much larger Baseline 1-vs-Baseline 0 gain is primarily from **player-specific recent evidence + empirical-Bayes shrinkage**, not the current level-only translation layer.

**Decision:** keep fitted translation as a candidate because it has a small repeatable aggregate log-loss benefit for Baseline 1, but do not freeze or treat it as essential yet. Additional chronological cutoffs should carry both fitted and zero-offset variants before deciding whether the added complexity earns its place.

There is still **no promoted/frozen Current Talent estimator**.

## Governing Current Talent contract

`docs/current-talent-validation-contract.md` remains authoritative.

Key boundaries:

- Current Talent = latent rate/profile ability **now**, conditional on opportunity.
- Preserve the 12-component profile first; scalar value is secondary.
- Predictor evidence must be strictly pre-cutoff.
- Environment effects are learned from training-period data only.
- Future outcomes are scored in the environment where they actually occur.
- Primary target = next 90 calendar days.
- Zero future PA is not poor talent.
- Validation is chronological / rolling-origin, never random split.
- Proper scoring and calibration outrank prettier correlation.
- Richer evidence must beat simple results-only baselines out of time.

## Completed milestones

### 1. Canonical/reuse-first foundation

Source roles, provenance, canonical schemas, identity handling, event semantics, contact reconstruction, state replay/RE24, level/season capability gates, contextual bin-value policies, and typed persistence are implemented and tested.

References: `docs/source-audit.md`, `docs/source-certification-current.md`, `docs/canonical-data-contract.md`, `docs/adr/`.

### 2. 2024 affiliated-MiLB batting Performance

Checkpoint: `docs/performance-2024-affiliated-checkpoint.md`  
Run: `31948208695`

- 14 actual leagues / 5 level groups
- 4,995 player × league × season rows
- 784,285 PA
- 764,713 screened core Performance events
- 97.50% core-profile PA coverage
- 0 unvalued core events

### 3. Historical affiliated-MiLB Current Talent evidence, 2021–2023

Checkpoint: `docs/current-talent-historical-milb-checkpoint.md`

Certified runs:

- 2021: `31979609553`
- 2022: `31971662070`
- 2023: `31971923778`

All five post-reorganization affiliated level groups are certified independently for each season.

### 4. Leakage-safe snapshots / future targets

Implemented in:

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_universal_evidence.py`

Frozen chronology:

- predictor: `game_date < as_of_date`;
- future target: `game_date >= as_of_date` and before the exclusive horizon end;
- no fake within-day ordering from game PK / row order;
- actual as-of and future environments preserved.

### 5. Historical MLB Current Talent evidence, 2021–2023

Checkpoint: `docs/current-talent-historical-mlb-checkpoint.md`

Certified runs:

- 2021: `31986504169`
- 2022: `31988255280`
- 2023: `31989561396`

Each season reconciles exactly to independent official MLB player × actual AL/NL × season totals for the frozen outcome backbone. Small physical-contact residuals remain ADR-024 diagnostics rather than repaired result counts.

### 6. MLB-anchored candidate environment translation

Implementation:

- `src/universal_baseball/current_talent_translation.py`
- `scripts/materialize_current_talent_translation_support.py`
- `.github/workflows/current-talent-translation-support.yml` — manual-only

Candidate: `matched_adjacent_stint_clr_wls_v1`.

Independent Aug. 1 fits in 2021–2023 connect all six levels to MLB. K and BB/HBP recover a coherent difficulty ladder; contact-shape effects are noisier and are not forced monotonic.

### 7. Exact age-as-of enrichment

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — manual-only

Pinned Chadwick DOB is converted to age at the explicit cutoff. Exact coverage at the Aug. 1 baseline folds:

- 2021: 4,315 / 4,315
- 2022: 3,756 / 3,756
- 2023: 3,853 / 3,853

### 8. Baseline 0 / Baseline 1 implementation

Checkpoint: `docs/current-talent-baseline-checkpoint.md`

Baseline 0 — `loo_age_level_population_prior_v1`:

- no player-specific recent Performance;
- exact age + current unambiguous level;
- leave-one-out age+level peers;
- same-level then global fallback only when needed.

Baseline 1 — `translated_recency_empirical_bayes_v1`:

- recency-weighted player core-profile evidence;
- aggregate at player × level first;
- translate each level segment to MLB scale before multi-level pooling;
- empirical-Bayes shrinkage toward Baseline 0.

### 9. Real future-environment scoring and diagnostics

Implementation:

- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `.github/workflows/current-talent-baseline-validation.yml` — manual-only

Diagnostics persist aggregate proper scores, target-level/transition strata, fixed age/evidence bands, 12 component score contributions, and reliability-bin calibration.

### 10. Three-year fixed-parameter Aug. 1 stability gate — passed

Runs:

- 2021 diagnostic: `31993773737`
- 2022/2023 confirmation matrix: `31994079021`

Baseline 1 beats Baseline 0 in all three years with unchanged settings; see table at top and `docs/current-talent-baseline-checkpoint.md`.

### 11. Controlled translation ablation — completed

Run: **`31994550684`**.

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

The temporary three-season workflow used to execute the ablation was deleted after the gate. Artifacts remain attached to run `31994550684`.

Result: fitted translation provides a **small, repeatable aggregate log-loss benefit for Baseline 1**, but mixed Brier/component/stratum results. It remains a candidate, not a frozen requirement.

## Important boundaries / not complete

Still not frozen or validated:

- stability at additional within-season cutoff dates rather than Aug. 1 only;
- selected recency window / half-life;
- selected EB prior strength;
- age-band width / peer threshold;
- multi-year calibration stability, especially by component;
- whether a simpler/partial translation (for example only robust components) would beat both current fitted and zero-offset variants;
- whether actual league/season residual effects add value beyond level-only translation;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not tune or add richer features yet.**

1. Run an additional **July 1** chronological cutoff in 2021–2023 using the same fixed Baseline 0/1 settings.
2. Carry both fitted-translation and zero-offset variants so the small translation effect is tested away from Aug. 1.
3. If July 1 is structurally supported and consistent, add another earlier cutoff (likely June 1) before hyperparameter selection.
4. Then compare a small predeclared set of recency half-lives / EB prior strengths inside chronology.
5. Freeze the simple baseline only if proper-score gains and calibration remain acceptable across time, level, evidence volume, and transitions.
6. Only then test Baseline 2 or richer process/tracking/scouting evidence.

## Useful workflows / scripts

Manual live/reuse workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-historical-mlb-season.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`
- `.github/workflows/current-talent-translation-support.yml`
- `.github/workflows/current-talent-age-coverage.yml`
- `.github/workflows/current-talent-baseline-validation.yml`

Key materializers:

- `scripts/materialize_current_talent_historical_milb_game_evidence.py`
- `scripts/materialize_current_talent_historical_mlb_game_evidence.py`
- `scripts/materialize_current_talent_translation_support.py`
- `scripts/audit_current_talent_age_coverage.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `scripts/materialize_current_talent_translation_ablation.py`

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect the current `source-certification-poc` head before editing.
5. Continue with **fixed-setting July 1 validation across 2021–2023, carrying fitted and zero translation variants**. Do not re-audit closed source/certification/age/Aug. 1 stability/translation-ablation questions unless a regression specifically fails.
