# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active branch / PR

- Working branch: `source-certification-poc`
- Open draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect the current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly **2–3 steps** and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate until their contracts justify combination.
- **Pause at meaningful project junctures to update repository documentation before continuing.** Refresh this file after a major gate passes, a material modeling/architecture decision is frozen, or the recommended next batch changes.

## Current project stage

The project is in **chronological Current Talent model validation**.

The simple results-only baseline now has a meaningful three-year confirmation: using the **same fixed candidate settings** at Aug. 1 cutoffs in 2021, 2022, and 2023, Baseline 1 beats Baseline 0 on both event-weighted multinomial log loss and Brier in every year.

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

Lower is better. The candidate settings were **not retuned between years**:

- season-to-date evidence;
- 90-day recency half-life;
- Baseline 1 prior strength = 100 effective core events;
- Baseline 0 age-band width = 2 years;
- minimum preferred age-level peers = 12.

This is strong evidence that player-specific translated/recent results add signal beyond the age+level population prior. It is **not yet enough to freeze/promote Baseline 1**, because all three confirmations use the same Aug. 1 calendar position, the environment-translation contribution has not yet been ablated, candidate hyperparameters have not been compared chronologically, and calibration still needs explicit multi-year review.

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

- training-only chronological player environment stints;
- adjacent observed stints only;
- same-day multi-environment ambiguity breaks continuity;
- symmetric CLR pseudocount `0.5`;
- weighted graph least squares with MLB = 0;
- fail closed unless every fitted level connects to MLB.

Independent Aug. 1 fits in 2021–2023 all connected the six levels to MLB. K and BB/HBP recover a coherent difficulty ladder; contact-shape effects are noisier and are not forced monotonic.

**Translation is still a candidate observation layer until predictive ablation measures its incremental value.**

### 7. Exact age-as-of enrichment

Implementation:

- `src/universal_baseball/chadwick.py`
- `scripts/audit_current_talent_age_coverage.py`
- `.github/workflows/current-talent-age-coverage.yml` — manual-only

Pinned Chadwick DOB is converted to age at the explicit cutoff. No mutable current-age field is stored and no partial DOB is silently imputed.

Exact age coverage at the baseline folds:

- 2021-08-01: 4,315 / 4,315
- 2022-08-01: 3,756 / 3,756
- 2023-08-01: 3,853 / 3,853

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
- translate each level segment to MLB scale **before** multi-level pooling;
- empirical-Bayes shrinkage toward Baseline 0.

### 9. Real future-environment scoring and diagnostics

Implementation:

- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `tests/test_current_talent_scoring.py`
- `tests/test_current_talent_score_diagnostics.py`
- `.github/workflows/current-talent-baseline-validation.yml` — manual-only

A latent MLB-scale profile is mapped to the realized target environment by adding that level's fitted CLR observation effect and softmaxing back to component probabilities. Proper scoring uses all eligible future core events in the 90-day horizon.

Diagnostics persist:

- aggregate event-weighted log loss and multinomial Brier;
- target-level and transition strata;
- fixed descriptive age/evidence bands;
- 12 component score contributions;
- reliability-bin calibration tables.

### 10. Three-year fixed-parameter Aug. 1 stability gate — passed

2021 primary diagnostic run: `31993773737`  
2022/2023 confirmation matrix: **`31994079021`**

#### 2021-08-01

- scored players: 3,722
- target-environment rows: 4,634
- future core events: 344,391
- B0 log loss / Brier: 2.268828 / 0.872730
- B1 log loss / Brier: **2.252931 / 0.868446**
- B1-B0: **-0.015896 / -0.004284**
- 21/21 separate fixed strata and 12/12 components favor B1 on both metrics.

#### 2022-08-01

- predictor players: 3,756; exact age 3,756/3,756
- scored players: 3,357
- target-environment rows: 4,134
- future core events: 280,640
- B0 log loss / Brier: 2.274821 / 0.874528
- B1 log loss / Brier: **2.256301 / 0.869822**
- B1-B0: **-0.018520 / -0.004706**
- 21/21 separate fixed strata and 12/12 components favor B1 on both metrics.

#### 2023-08-01

- predictor players: 3,853; exact age 3,853/3,853
- scored players: 3,418
- target-environment rows: 4,154
- future core events: 275,511
- B0 log loss / Brier: 2.269383 / 0.874000
- B1 log loss / Brier: **2.251158 / 0.869362**
- B1-B0: **-0.018226 / -0.004638**
- 21/21 separate fixed strata and 12/12 components favor B1 on both metrics.

The temporary two-season matrix workflow used for this one-time confirmation was removed after the gate; the permanent per-season baseline-validation workflow remains manual and reproducible.

## Important boundaries / not complete

Still not frozen or validated:

- **translation ablation** versus a simpler/no-translation observation treatment;
- stability at additional within-season cutoff dates rather than Aug. 1 only;
- selected recency window / half-life;
- selected EB prior strength;
- age-band width / peer threshold;
- multi-year calibration stability, especially by component;
- whether actual league/season residual effects add value beyond level-only translation;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not add richer features yet.**

1. Add a clean **translation ablation** so the predictive contribution of the environment observation layer is measured rather than assumed.
2. Run the ablation on the fixed 2021–2023 Aug. 1 folds.
3. Then add additional in-season chronological cutoffs with the same fixed baseline settings.
4. Only after those gates, compare a small predeclared set of recency half-lives / EB prior strengths inside chronology.
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

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect the current `source-certification-poc` head before editing.
5. Continue with **translation ablation across the fixed 2021–2023 Aug. 1 folds**. Do not re-audit closed source/certification/age/baseline-stability questions unless a regression specifically fails.
