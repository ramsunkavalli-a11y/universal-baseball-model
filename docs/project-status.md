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

Baseline 1 has a strong three-year Aug. 1 confirmation over Baseline 0 using unchanged candidate settings. A controlled translation ablation is complete, and July 1 has now been tested where the historical translation graph supports a universal fit.

### Baseline 1 vs Baseline 0 — fixed settings

Aug. 1:

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

July 1 where structurally supported:

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2022-07-01 | 448,049 | **-0.015154** | **-0.003995** |
| 2023-07-01 | 444,276 | **-0.015839** | **-0.004079** |

Lower is better. The candidate settings were unchanged across all successful folds:

- season-to-date evidence;
- 90-day recency half-life;
- Baseline 1 prior strength = 100 effective core events;
- Baseline 0 age-band width = 2 years;
- minimum preferred age-level peers = 12.

**2021-07-01 is not a universal comparable fitted-translation cutoff.** The pre-cutoff matched-transition graph has no learned `ROOKIE_COMPLEX` offset, so the pipeline correctly fails closed when it encounters actual Rookie predictor evidence. This is a historical support boundary, not a code/model-score failure, and the translation rules must not be weakened to force July 1 to pass.

### Translation ablation — fitted CLR level effects vs zero offsets

Aug. 1 run: `31994550684`.

The ablation holds the Baseline 0/1 and scoring pipeline fixed and replaces only fitted `clr_environment_effect` values with zero. Baseline 0 still knows current level through its peer prior; this isolates the learned observation-layer translation.

Baseline 1 fitted-minus-zero at Aug. 1:

| Cutoff | Log loss delta | Brier delta | Strata LL wins | Strata Brier wins | Component LL wins | Component Brier wins |
|---|---:|---:|---:|---:|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 | 13/21 | 12/21 | 9/12 | 6/12 |
| 2022-08-01 | **-0.000838** | **-0.000246** | 17/21 | 17/21 | 3/12 | 9/12 |
| 2023-08-01 | **-0.001093** | **-0.000263** | 16/21 | 15/21 | 6/12 | 8/12 |

At July 1:

- 2022 B1 fitted-minus-zero: **-0.000409 log loss / -0.000130 Brier**, with fitted translation winning 16/21 log-loss strata, 17/21 Brier strata, 6/12 component log-loss contributions, and 8/12 component Brier contributions.
- 2023 B1 fitted-minus-zero: **-0.000566 log loss / -0.000160 Brier**, with fitted translation winning 15/21 strata on both metrics and 7/12 components on both metrics.

Interpretation remains stable:

- the much larger B1-vs-B0 gain comes primarily from **player-specific recent evidence + empirical-Bayes shrinkage**;
- fitted translation gives B1 a small aggregate benefit in the successful July and August folds, especially on log loss;
- translation gains are not universal across components/strata;
- fitted translation remains a candidate, not a frozen requirement.

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

Historical support is cutoff-dependent. In particular, the 2021 graph does not yet have a Rookie/complex translation at July 1.

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

Baseline 0 — `loo_age_level_population_prior_v1`: age + current-level leave-one-out population prior, no player-specific recent Performance.

Baseline 1 — `translated_recency_empirical_bayes_v1`: recency-weighted player evidence, player×level handling before pooling, empirical-Bayes shrinkage toward Baseline 0.

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
- 2022/2023 confirmation: `31994079021`

B1 beats B0 in all three years with unchanged settings.

### 11. Controlled translation ablation — completed

Run: `31994550684`.

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

Result: fitted translation provides a small repeatable aggregate B1 log-loss benefit at Aug. 1, with mixed component/stratum results.

### 12. July 1 fixed-setting validation — partial universal gate, informative boundary

Run: **`31994814042`**.

- targeted regression suite: 24/24 passed in each matrix job before live materialization;
- 2022: passed, artifact `current-talent-july-validation-2022-2022-07-01` (artifact ID `9276488114`);
- 2023: passed, artifact `current-talent-july-validation-2023-2023-07-01` (artifact ID `9276486631`);
- 2021: fail-closed structural boundary — no fitted `ROOKIE_COMPLEX` offset before July 1.

The workflow `.github/workflows/current-talent-july-validation.yml` was restored to **manual-only** after the gate. Deletion of the one-time file was connector-blocked, so it remains as a reproducible manual workflow rather than an auto-trigger.

2022/2023 July results reinforce two earlier findings:

1. B1's player-evidence/shrinkage advantage is not specific to Aug. 1.
2. Fitted translation adds only a small incremental aggregate advantage over zero offsets.

## Important boundaries / not complete

Still not frozen or validated:

- earliest 2021 in-season cutoff where all six translation levels are supported;
- stability at a common July cutoff across all three years;
- selected recency window / half-life;
- selected EB prior strength;
- age-band width / peer threshold;
- multi-year/multi-cutoff calibration stability;
- whether a simpler/partial translation would beat both current fitted and zero-offset variants;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not tune or add richer features yet.**

1. Probe **2021-07-15** with the same translation support rules and fixed B0/B1 settings to find the earliest universal six-level 2021 cutoff.
2. If Rookie/complex is still unsupported, move the probe later in July without lowering the 20-core-event stint threshold or weakening graph-connectivity rules.
3. Once a universal 2021 July date is found, run the same date in 2022/2023 for an apples-to-apples three-year July confirmation, carrying fitted and zero-offset variants.
4. Document that gate before any hyperparameter selection.
5. Then compare a small predeclared set of recency half-lives / EB prior strengths chronologically.
6. Freeze the simple baseline only if proper-score gains and calibration remain acceptable across time, level, evidence volume, and transitions.

## Useful workflows / scripts

Manual live/reuse workflows:

- `.github/workflows/current-talent-historical-milb-one-level.yml`
- `.github/workflows/current-talent-historical-mlb-season.yml`
- `.github/workflows/current-talent-validation-snapshot-one-level.yml`
- `.github/workflows/current-talent-validation-snapshot-multilevel.yml`
- `.github/workflows/current-talent-translation-support.yml`
- `.github/workflows/current-talent-age-coverage.yml`
- `.github/workflows/current-talent-baseline-validation.yml`
- `.github/workflows/current-talent-july-validation.yml`

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
4. Inspect current `source-certification-poc` head before editing.
5. Continue with the **2021-07-15 six-level support / validation probe**. Do not weaken translation support rules just to make an early cutoff pass.
