# Project status and handoff

Last updated: 2026-08-16

This is the **start-here file for a new chat, coding agent, or contributor**. Read it before reconstructing state from old commits or conversation history.

## Active work

- Repo: `ramsunkavalli-a11y/universal-baseball-model`
- Working branch: `source-certification-poc`
- Draft PR: **#1 — Build and certify universal baseball foundation layer**
- `main` is intentionally behind.
- Inspect the current branch head before editing because parallel work may land independently.

## Execution rules

- Work in small batches of roughly 2–3 steps and verify before expanding.
- Prefer mature public datasets/parsers/packages over rebuilding source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Pause at meaningful project junctures to update this handoff before continuing.

## Current stage

The **simple results-only Current Talent baseline is now frozen**. The selection/confirmation gate is complete.

Frozen comparator: **`hl180_ps100_fitted`**

- predictor recency half-life: **180 days**;
- Baseline 1 empirical-Bayes prior strength: **100 effective core events**;
- environment translation: **`fitted_translation`**;
- Baseline 0 age-band width: **2.0 years**;
- Baseline 0 minimum preferred age+level peers: **12**.

The age-band / peer settings were held fixed during the first hyperparameter grid rather than independently optimized. They are frozen as part of the reproducible simple comparator, not claimed to be globally optimal.

Detailed freeze decision: `docs/current-talent-simple-baseline-freeze.md`.

**Do not retune this baseline while testing richer challengers.** A proposed change to these settings is itself a new challenger and must earn out-of-time value under the same chronological protocol.

## What is already implemented / certified

1. reuse-first canonical data, provenance, and identity architecture;
2. production-shaped 2024 affiliated-MiLB batting Performance;
3. certified 2021–2023 affiliated-MiLB Current Talent evidence;
4. certified 2021–2023 MLB Current Talent evidence with official reconciliation;
5. leakage-safe predictor snapshots and 90-day future targets;
6. training-only MLB-anchored matched-transition environment translation;
7. exact Chadwick DOB → age-as-of enrichment;
8. Baseline 0 / Baseline 1 results-only Current Talent estimators;
9. proper future-environment scoring, calibration diagnostics, and controlled translation ablation;
10. nine-fold calibration review;
11. predeclared 18-candidate chronological development grid on 2021–2022 only;
12. selected-candidate confirmation on 2023 without 2023 reselection;
13. explicit simple-baseline freeze.

Source/data plumbing is no longer the active bottleneck for the simple Current Talent baseline.

## Frozen baseline definitions

Core batting profile: **12 components** — BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB.

### Baseline 0 — `loo_age_level_population_prior_v1`

- no player-specific recent Performance;
- exact age-as-of + current unambiguous level;
- leave-one-out age+level population prior;
- 2-year age band;
- minimum 12 preferred age+level peers;
- same-level then global fallback only when needed.

### Baseline 1 — `translated_recency_empirical_bayes_v1`

- season-to-date player core-profile evidence;
- **180-day** recency half-life;
- player×level evidence handled before multi-level pooling;
- **fitted training-only level translation** to the MLB latent scale;
- empirical-Bayes shrinkage toward B0;
- prior strength = **100 effective core events**.

All other temporal, observation, scoring, target-horizon, identity, source-authority, and component rules remain governed by `docs/current-talent-validation-contract.md` and `docs/current-talent-baseline-selection-plan.md`.

## Selection gate — complete

The predeclared grid searched only:

- half-life: 45 / 90 / 180 days;
- prior strength: 50 / 100 / 200 effective core events;
- translation: fitted vs zero offsets.

Selection used only six development folds:

- 2021-07-15 / 2021-08-01 / 2021-09-01;
- 2022-07-15 / 2022-08-01 / 2022-09-01.

Selected candidate: **`hl180_ps100_fitted`**.

Development summary:

- equal-fold mean B1 log loss: **2.255543**;
- equal-fold mean B1 Brier: **0.869233**;
- mean B1−B0 log loss: **-0.017598**;
- mean B1−B0 Brier: **-0.004643**;
- B1 proper-score wins vs B0: **6/6** folds on both metrics;
- selected minus prior 90/100/fitted reference: **-0.000262** log loss / **-0.000133** Brier;
- component wins vs B0: **72/72** log loss, **66/72** Brier;
- stratum wins vs B0: **125/125** on both proper scores.

Detailed checkpoint: `docs/current-talent-development-selection-checkpoint.md`.
Persisted selected candidate: `docs/current-talent-development-selected-candidate.json`.

## 2023 confirmation gate — complete

Only the preselected candidate plus the fixed 90/100/fitted reference were evaluated on the three 2023 folds. The full 18-candidate grid was **not** evaluated on 2023, and there was no 2023 reselection.

Confirmation folds:

- 2023-07-15;
- 2023-08-01;
- 2023-09-01.

Confirmation summary:

- equal-fold mean B1 log loss: **2.252313**;
- equal-fold mean B1 Brier: **0.869653**;
- mean B1−B0 log loss: **-0.018814**;
- mean B1−B0 Brier: **-0.004777**;
- B1 proper-score wins vs B0: **3/3** folds on both metrics;
- selected minus fixed reference: **-0.000245** log loss / **-0.000105** Brier;
- component wins vs B0: **36/36** log loss, **35/36** Brier;
- stratum wins vs B0: **62/62** on both proper scores.

Confirmation workflow run: **`31997270467`**.

Detailed checkpoint: `docs/current-talent-2023-confirmation-checkpoint.md`.
Machine-readable result: `docs/current-talent-2023-confirmation-result.json`.

### Workflow bootstrap note

The first 2023 confirmation run fired before the development-selection JSON had been committed and correctly failed its prerequisite check. The selection checkpoint was then committed by GitHub Actions, whose `GITHUB_TOKEN` commit did not trigger a second workflow. `.github/workflows/current-talent-2023-selected-confirmation.yml` now documents this chaining limitation; the explicit bootstrap run above passed end to end.

## Calibration guardrail

The nine-fold calibration review established that Baseline 1 materially improves calibration intercept/slope error versus Baseline 0, while its coarse fixed-bin ECE can be slightly worse. No post-hoc recalibration was applied.

For the **selected 180/100/fitted candidate**, combining its six development folds and three 2023 confirmation folds gives approximately:

- equal-fold mean absolute calibration-intercept error: **0.5513**;
- equal-fold mean absolute calibration-slope error: **0.2010**;
- equal-fold mean fixed-bin ECE: **0.00299**.

Known systematic defects remain visible and should become challenger targets rather than retrospective baseline patches:

- **K**: mean-rate bias and calibration slopes generally above 1;
- **LD/OFFB directional components**: slopes consistently below 1, indicating overly dispersed/extreme forecasts.

Detailed review: `docs/current-talent-calibration-checkpoint.md`.
Primary calibration workflow run: **`31996082936`**.

## Why the simple baseline is frozen

The predeclared freeze criteria are met:

- B1 beats B0 out of time on both proper scores;
- the selected parameterization confirms on 2023 rather than reversing its development advantage;
- no major evaluated stratum is catastrophically harmed;
- candidate coverage is held constant during confirmation and no structural coverage failure appears;
- calibration is imperfect but interpretable, with defects explicitly documented.

Freeze decision: `docs/current-talent-simple-baseline-freeze.md`.

## Governing Current Talent documents

Read these in this order when working on the next Current Talent gate:

1. `docs/project-status.md` — current handoff;
2. `docs/current-talent-validation-contract.md` — authoritative validation rules;
3. `docs/current-talent-simple-baseline-freeze.md` — frozen comparator and decision boundary;
4. `docs/current-talent-calibration-checkpoint.md` — calibration findings / known defects;
5. `docs/current-talent-development-selection-checkpoint.md` — 2021–2022 selection evidence;
6. `docs/current-talent-2023-confirmation-checkpoint.md` — held-out-for-grid confirmation evidence.

Historical source and baseline checkpoints remain useful provenance, but do not reopen their closed gates without a concrete failure.

## Key implementation / workflow files

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_translation.py`
- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_calibration.py`
- `src/universal_baseball/current_talent_selection.py`
- `scripts/materialize_current_talent_selection_grid.py`
- `scripts/materialize_current_talent_2023_confirmation.py`
- `.github/workflows/current-talent-baseline-selection-grid.yml`
- `.github/workflows/current-talent-2023-selected-confirmation.yml`

Completed live-source / heavy validation workflows should remain manual-only after their gates pass unless a new gate specifically requires them.

## Important boundaries / not complete

The simple results-only baseline freeze does **not** complete Current Talent or the player-ranking system.

Still unresolved:

- Baseline 2 / richer process, tracking, or scouting inputs;
- component-specific shrinkage or any proposed recalibration challenger;
- final uncertainty model;
- Projection / future aging and development;
- playing time / role;
- defense;
- WAR / player-value conversion;
- final cross-player ranking.

The exact 200-PA player-aggregate diagnostic cap is not applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which uses all eligible future events in the target horizon.

## Recommended next batch

**Do not retune the frozen simple baseline.**

1. Define a small, predeclared **Baseline 2 / richer-evidence challenger contract** against `hl180_ps100_fitted` before implementing the challenger.
2. Choose one evidence family or modeling addition at a time, favoring mature reusable public data/packages over new raw-source cleanup.
3. Preserve the frozen chronological scoring protocol and eligible population where possible; require an out-of-time proper-score improvement before promoting richer complexity.

Do not begin Projection, playing-time, defense, WAR, or final-ranking work inside this gate.

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-simple-baseline-freeze.md`.
4. Inspect the current `source-certification-poc` head.
5. Continue with the **Baseline 2 / richer-evidence challenger design**. Do not rerun calibration, reselect hyperparameters, evaluate the full grid on 2023, or re-audit closed source/certification work first.
