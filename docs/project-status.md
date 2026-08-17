# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- **Pause at meaningful project junctures to update this handoff before continuing.** Update after a major gate, a material model/architecture decision, or a changed recommended next batch.

## Current stage

The project is in **chronological Current Talent model validation**. Source/data plumbing is no longer the active bottleneck.

Implemented and certified foundations:

1. reuse-first canonical data/provenance/identity architecture;
2. production-shaped 2024 affiliated-MiLB batting Performance;
3. certified 2021–2023 affiliated-MiLB Current Talent evidence;
4. certified 2021–2023 MLB Current Talent evidence with official reconciliation;
5. leakage-safe predictor snapshots and future targets;
6. training-only MLB-anchored matched-transition environment translation;
7. exact Chadwick DOB → age-as-of enrichment;
8. Baseline 0 / Baseline 1 results-only Current Talent estimators;
9. proper future-environment scoring, calibration diagnostics, and translation ablation.

There is **no frozen/promoted Current Talent estimator yet**.

## Baseline definitions

Core latent batting profile: 12 components — BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB.

**Baseline 0 — `loo_age_level_population_prior_v1`**

- no player-specific recent Performance;
- exact age-as-of + current unambiguous level;
- leave-one-out age+level population prior;
- default 2-year age band;
- minimum 12 preferred age+level peers;
- same-level then global fallback only when needed.

**Baseline 1 — `translated_recency_empirical_bayes_v1`**

- season-to-date player core-profile evidence;
- default 90-day recency half-life;
- player×level evidence handled before multi-level pooling;
- candidate level translation to MLB latent scale;
- empirical-Bayes shrinkage toward B0;
- default prior strength = 100 effective core events.

These settings are **candidate settings, not frozen hyperparameters**.

## Fixed-setting Baseline 1 vs Baseline 0 results

Lower is better.

### Aug. 1

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier | Fixed-strata wins | Component wins |
|---|---:|---:|---:|---:|---:|
| 2021-08-01 | 344,391 | **-0.015896** | **-0.004284** | 21/21 | 12/12 |
| 2022-08-01 | 280,640 | **-0.018520** | **-0.004706** | 21/21 | 12/12 |
| 2023-08-01 | 275,511 | **-0.018226** | **-0.004638** | 21/21 | 12/12 |

Runs:

- 2021 diagnostic: `31993773737`
- 2022/2023 confirmation: `31994079021`

### July 1 where structurally supported

| Cutoff | Future core events | B1-B0 log loss | B1-B0 Brier |
|---|---:|---:|---:|
| 2022-07-01 | 448,049 | **-0.015154** | **-0.003995** |
| 2023-07-01 | 444,276 | **-0.015839** | **-0.004079** |

Run: `31994814042`.

`2021-07-01` is **not** a valid universal fitted-translation fold. The pre-cutoff matched-transition graph has no `ROOKIE_COMPLEX` effect, so the pipeline correctly fails closed when actual Rookie predictor evidence is encountered. This is a historical support boundary, not a code/model-score failure. Do **not** lower translation support rules or omit Rookie to force an earlier fold.

### First universal 2021 July cutoff found: 2021-07-15

Probe run: **`31995116901`**  
Artifact: `current-talent-2021-july-probe-2021-07-15` (artifact ID `9276574830`).

By July 15 the training-only translation graph supports all six levels:

- fitted levels: **6**;
- eligible cross-level pairs: **479**;
- cross-level players: **419**;
- max graph distance to MLB: **2**;
- all levels connected to MLB: **true**.

Coverage / score surface:

- predictor players: 3,970;
- B0/B1 profile players: 3,957;
- scored players: 3,558;
- scored target-environment rows: 4,753;
- future core events: **435,778**.

Fitted-translation scores:

| Model | Log loss | Brier |
|---|---:|---:|
| B0 | 2.274519 | 0.874039 |
| B1 | **2.260882** | **0.870396** |

B1-B0:

- log loss: **-0.013638**;
- Brier: **-0.003643**.

So the main B1 signal remains strong at the first universal 2021 July fold.

## Translation ablation

Implementation:

- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_translation_ablation.py`
- `tests/test_current_talent_ablation.py`

The controlled ablation replaces fitted `clr_environment_effect` values with zero while leaving recency, B0 peer rules, B1 shrinkage, player coverage, and future scoring unchanged. B0 still knows current level through its peer prior.

### Aug. 1 B1 fitted-minus-zero

| Cutoff | Log loss | Brier |
|---|---:|---:|
| 2021-08-01 | **-0.000328** | +0.000003 |
| 2022-08-01 | **-0.000838** | **-0.000246** |
| 2023-08-01 | **-0.001093** | **-0.000263** |

Run: `31994550684`.

### July 1 B1 fitted-minus-zero

- 2022: **-0.000409 log loss / -0.000130 Brier**;
- 2023: **-0.000566 log loss / -0.000160 Brier**.

### 2021-07-15 B1 fitted-minus-zero

- log loss: **+0.000997**;
- Brier: **+0.000336**;
- fitted translation wins only 10/21 descriptive strata on each aggregate metric;
- component wins: 7/12 log-loss contributions, 5/12 Brier contributions.

At this cutoff **zero offsets beat the fitted translation** for both B0 and B1.

### Translation interpretation

The large B1-vs-B0 gain is clearly driven primarily by **player-specific recent evidence + empirical-Bayes shrinkage**, not by the level translation layer.

Translation has shown small aggregate gains in several July/August folds, but the 2021-07-15 result demonstrates that its incremental value is **not temporally stable enough to freeze**. Carry fitted and zero-offset variants into the same-date three-year July comparison before deciding whether this translation form earns its complexity.

## Governing validation rules

`docs/current-talent-validation-contract.md` is authoritative.

Important frozen rules:

- Current Talent = latent rate/profile ability now, conditional on opportunity;
- predictor evidence strictly before cutoff;
- environment effects training-only;
- future outcomes scored in their realized environment;
- primary horizon = next 90 calendar days;
- zero future PA is not bad talent;
- chronological / rolling-origin validation only;
- proper scoring and calibration outrank correlation;
- richer evidence must beat simple baselines out of time.

## Key implementation files

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_translation.py`
- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_ablation.py`
- `scripts/materialize_current_talent_baseline_validation.py`
- `scripts/materialize_current_talent_translation_ablation.py`

Key checkpoint docs:

- `docs/current-talent-validation-contract.md`
- `docs/current-talent-baseline-checkpoint.md`
- `docs/current-talent-historical-milb-checkpoint.md`
- `docs/current-talent-historical-mlb-checkpoint.md`
- `docs/performance-2024-affiliated-checkpoint.md`

Manual workflows include:

- `.github/workflows/current-talent-baseline-validation.yml`
- `.github/workflows/current-talent-july-validation.yml`
- `.github/workflows/current-talent-2021-july-probe.yml`
- `.github/workflows/current-talent-translation-support.yml`
- `.github/workflows/current-talent-age-coverage.yml`

All bootstrap triggers used for the completed gates above have been restored to **manual-only**.

## Important boundaries / not complete

Still unresolved:

- same-date 2021–2023 July 15 confirmation;
- translation model selection: fitted current level-only effects vs zero offsets vs possibly a simpler/partial translation;
- additional within-season cutoffs;
- selected recency half-life;
- selected EB prior strength;
- age-band width / peer threshold;
- multi-year/multi-cutoff calibration stability;
- final uncertainty model;
- Baseline 2 / richer process-tracking-scouting inputs;
- Projection, future aging/development, playing time/role, defense, WAR/value, or final ranking.

The exact 200-PA player-aggregate diagnostic cap is not yet applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the horizon.

## Recommended next batch

**Do not tune or add richer features yet.**

1. Run **2022-07-15 and 2023-07-15** with the same fixed B0/B1 settings and fitted-vs-zero translation variants.
2. Compare all three seasons at the same July 15 cutoff.
3. Document whether the B1-vs-B0 signal and translation ablation are stable across the common cutoff.
4. Then add another cutoff if useful before hyperparameter selection.
5. Only after cutoff stability, compare a small predeclared set of recency half-lives / EB prior strengths chronologically.
6. Freeze the simple baseline only if proper scores and calibration justify it; only then test richer inputs.

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-baseline-checkpoint.md`.
4. Inspect current `source-certification-poc` head.
5. Continue with the **2022/2023 July 15 same-date validation**; do not re-audit closed source/certification work or weaken translation support rules.
