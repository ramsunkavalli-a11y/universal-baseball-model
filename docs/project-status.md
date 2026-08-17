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
- Prefer mature public datasets/parsers/packages over rebuilding raw-source cleanup.
- Surface early errors rather than compounding them.
- Heavy live-source/reuse workflows return to **manual-only after their gate passes**; deterministic tests stay in normal CI.
- Keep **Performance**, **Current Talent**, **Projection**, and **Player Value / Overall Ranking** separate.
- Do not tune a frozen baseline in response to a richer challenger; a baseline change is itself a new challenger.
- Pause at meaningful project junctures to update this handoff before continuing.

## Current stage

The **universal results-only Current Talent baseline is now frozen**. Baseline 2 passed 2022 development and fixed 2023 confirmation.

Required comparator for richer Current Talent challengers:

**Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`**

- up to **1,095 calendar days** of eligible player results history;
- **180-day** exponential recency half-life;
- **100 effective core events** of empirical-Bayes prior strength;
- existing fitted training-only MLB-anchored level translation;
- existing leave-one-out age + current-level Baseline 0 prior;
- existing 12-component profile and 90-day future event target.

The prior season-to-date Baseline 1 `hl180_ps100_fitted` remains frozen as the simpler reference, but richer models must primarily beat **B2**.

Detailed freeze: `docs/current-talent-results-only-baseline-freeze.md`.

**Next active gate: richer process / tracking evidence source-capability inventory and first narrow challenger design.**

## What is already implemented / certified

1. reuse-first canonical data, provenance, and identity architecture;
2. production-shaped 2024 affiliated-MiLB batting Performance;
3. certified 2021–2023 affiliated-MiLB Current Talent evidence;
4. certified 2021–2023 MLB Current Talent evidence with official reconciliation;
5. leakage-safe predictor snapshots and 90-day future targets;
6. training-only MLB-anchored matched-transition environment translation;
7. exact Chadwick DOB -> age-as-of enrichment;
8. Baseline 0 / Baseline 1 results-only Current Talent estimators;
9. proper future-environment scoring, calibration diagnostics, and controlled translation ablation;
10. nine-fold B1 calibration review;
11. predeclared B1 hyperparameter grid on 2021–2022 only;
12. fixed B1 confirmation on 2023 and simple-baseline freeze;
13. predeclared Baseline 2 multi-season challenger;
14. B2 2022 development gate using 2021 + pre-cutoff 2022 history;
15. fixed B2 2023 confirmation using 2021–2022 + pre-cutoff 2023 history;
16. explicit universal results-only baseline freeze.

Source/data plumbing is no longer the active bottleneck for results-only Current Talent.

## Current Talent model ladder

Core batting profile: **12 components** — BB/HBP, K, IFFB, and Pull/Center/Oppo × OFFB/LD/GB.

### Baseline 0 — `loo_age_level_population_prior_v1`

- no player-specific recent Performance;
- exact age-as-of + current unambiguous level;
- leave-one-out age+level population prior;
- 2-year age band;
- minimum 12 preferred age+level peers;
- same-level then global fallback only when needed.

### Baseline 1 — `translated_recency_empirical_bayes_v1`

Frozen simple season-to-date reference:

- current-season player core-profile evidence;
- 180-day recency half-life;
- player×level evidence translated before multi-level pooling;
- fitted training-only level translation to the MLB latent scale;
- empirical-Bayes shrinkage toward B0;
- prior strength = 100 effective core events.

Frozen B1 candidate ID: `hl180_ps100_fitted`.

### Baseline 2 — `translated_multiseason_recency_empirical_bayes_v1`

Frozen universal results-only comparator:

- identical estimator/translation/prior machinery to B1;
- only intended modeling addition = **prior-season player results history**;
- maximum lookback = 1,095 calendar days;
- same 180-day continuous decay across season boundaries;
- same 100-event prior strength;
- same B0 prior and same fold-specific translation as comparator.

For players without eligible prior-season evidence, B2 collapses to B1 to numerical tolerance.

All temporal, observation, scoring, target-horizon, identity, source-authority, and component rules remain governed by `docs/current-talent-validation-contract.md`.

## B1 selection / confirmation — closed

The simple B1 grid searched only:

- half-life: 45 / 90 / 180 days;
- prior strength: 50 / 100 / 200 effective core events;
- translation: fitted vs zero offsets.

Development used six 2021–2022 folds. Selected candidate: `hl180_ps100_fitted`.

It then confirmed on 2023 without evaluating the full alternative grid on 2023. Confirmation workflow: **31997270467**.

Do not reopen B1 selection/calibration/translation ablation unless a concrete implementation failure is discovered.

Key docs:

- `docs/current-talent-development-selection-checkpoint.md`
- `docs/current-talent-development-selected-candidate.json`
- `docs/current-talent-2023-confirmation-checkpoint.md`
- `docs/current-talent-2023-confirmation-result.json`
- `docs/current-talent-simple-baseline-freeze.md`

## Baseline 2 development — complete

Predeclared plan: `docs/current-talent-baseline2-plan.md`.

Development used only:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

B2 could use certified 2021 history plus eligible pre-cutoff 2022 results. No 2023 data was used before the development decision.

Equal-fold B2 vs frozen B1:

- log loss: **2.253898 vs 2.256520**, delta **-0.002622**;
- Brier: **0.869252 vs 0.869743**, delta **-0.000491**;
- B2 wins: **3/3** folds on log loss and **3/3** on Brier;
- component wins: **26/36** log loss and **36/36** Brier;
- every meaningfully supported non-MLB target level improved on both proper scores in every available development fold;
- mean absolute calibration intercept: **0.5242 -> 0.3857**;
- mean absolute calibration slope: **0.1927 -> 0.1473**;
- ~**82.6%** of model-eligible players carried positive prior-season effective evidence;
- mean added history = ~**45.2 effective core events/player**.

All predeclared promotion checks passed.

Workflow run: **31998668697**.

Key docs:

- `docs/current-talent-baseline2-development-checkpoint.md`
- `docs/current-talent-baseline2-development-result.json`

## Baseline 2 held-out 2023 confirmation — complete

The exact development-passed B2 was evaluated on:

- 2023-07-15;
- 2023-08-01;
- 2023-09-01.

No 2023 Baseline 2 grid or reselection occurred.

Equal-fold B2 vs frozen B1:

- log loss: **2.249308 vs 2.252313**, delta **-0.003005**;
- Brier: **0.869079 vs 0.869653**, delta **-0.000574**;
- B2 wins: **3/3** log loss and **3/3** Brier;
- component wins: **25/36** log loss and **36/36** Brier;
- no component was worse on both proper scores in all three folds;
- every meaningfully supported non-MLB target level improved on both proper scores in every available confirmation fold;
- mean absolute calibration intercept: **0.5223 -> 0.3496**;
- mean absolute calibration slope: **0.1907 -> 0.1300**;
- fixed-bin ECE moved slightly worse (**0.002615 -> 0.002734**) but was not a hard gate and did not accompany proper-score or intercept/slope deterioration;
- ~**82.5%** of model-eligible players carried positive prior-season effective evidence;
- mean added history = ~**56.0 effective core events/player**.

All predeclared hard confirmation checks passed.

Workflow run: **31998882475**.

Key docs:

- `docs/current-talent-baseline2-confirmation-checkpoint.md`
- `docs/current-talent-baseline2-confirmation-result.json`

## Six-fold B2 interpretation

Across the three 2022 development folds plus three 2023 confirmation folds:

- B2 beats B1 **6/6** times on log loss;
- B2 beats B1 **6/6** times on Brier;
- mean log-loss delta: **-0.002814**;
- mean Brier delta: **-0.000532**;
- component wins: **51/72** log loss and **72/72** Brier;
- calibration intercept error improves **0.5233 -> 0.3676**;
- calibration slope error improves **0.1917 -> 0.1386**;
- mean fixed-bin ECE is essentially unchanged (**0.002560 vs 0.002563**).

Baseball interpretation: the 180-day within-history decay was sensible, but forcing the model to forget everything at the season boundary discarded useful talent information. Prior-season K/BB/contact-shape results retain predictive value after level translation, regression, and current-season evidence are accounted for.

## Known Current Talent diagnostics

Earlier B1 calibration work found systematic issues that remain useful richer-challenger targets:

- K mean-rate bias / slopes often above 1;
- several LD/OFFB directional components too dispersed, with slopes below 1.

B2 improves overall calibration substantially but is not a claim that every component form is optimal. Do not patch these post hoc; a component-specific shrinkage/recalibration proposal is a separate challenger.

The exact 200-PA player-aggregate diagnostic cap is still not applied because the certified backbone is player-game aggregate. Do not invent within-game PA order to force it. This does not affect event-likelihood scoring, which correctly uses all eligible future events in the target horizon.

## Governing Current Talent documents

For new work, read in this order:

1. `docs/project-status.md` — current handoff;
2. `docs/current-talent-validation-contract.md` — authoritative model/validation boundary;
3. `docs/current-talent-results-only-baseline-freeze.md` — current required comparator;
4. `docs/current-talent-baseline2-confirmation-checkpoint.md` — held-out confirmation evidence;
5. `docs/current-talent-baseline2-development-checkpoint.md` — development evidence;
6. `docs/current-talent-baseline2-plan.md` — predeclared B2 protocol;
7. `docs/current-talent-simple-baseline-freeze.md` — B1 simple reference;
8. `docs/current-talent-calibration-checkpoint.md` — known B1 component/calibration defects.

Historical source and B1 checkpoints remain provenance. Do not reopen closed gates without a concrete failure.

## Key implementation / workflow files

Core Current Talent:

- `src/universal_baseball/current_talent_evidence.py`
- `src/universal_baseball/current_talent_validation_dataset.py`
- `src/universal_baseball/current_talent_translation.py`
- `src/universal_baseball/current_talent_baselines.py`
- `src/universal_baseball/current_talent_baseline2.py`
- `src/universal_baseball/current_talent_scoring.py`
- `src/universal_baseball/current_talent_score_diagnostics.py`
- `src/universal_baseball/current_talent_calibration.py`
- `src/universal_baseball/current_talent_selection.py`

B2:

- `scripts/materialize_current_talent_baseline2_development.py`
- `scripts/materialize_current_talent_baseline2_confirmation.py`
- `tests/test_current_talent_baseline2.py`
- `.github/workflows/current-talent-baseline2-development.yml`
- `.github/workflows/current-talent-baseline2-confirmation.yml`

Both B2 heavy workflows are **manual-only** after their completed gates.

## League/source-capability boundary for the next tier

Do not confuse Baseline 2 with the upcoming richer model.

B2 remains results-only and universal because the same evidence family is available across MLB and affiliated minors.

The next process/tracking tier may have materially uneven coverage by league. Before choosing features:

1. inventory reusable public sources/packages and actual historical availability by MLB / AAA / AA / High-A / Single-A / Rookie Complex / DSL where applicable;
2. distinguish event/result coverage from true tracking/process capability;
3. do **not** infer missing lower-level tracking features from MLB distributions;
4. prefer a tiered architecture when appropriate: B2 universal fallback + richer observed evidence only where genuinely available;
5. validate incremental gain against B2 on the richer-evidence eligible population and separately by league/source-capability tier;
6. reject a richer model whose apparent win is merely an MLB-only artifact unless it is explicitly scoped as an MLB-only tier.

The first richer challenger should add **one evidence family at a time**. Likely first families to investigate include batted-ball quality (EV/launch/contact quality), then swing/contact process or pitch-level information, but source capability must be inventoried before committing to one.

## Still unresolved

- first richer process / tracking / scouting Current Talent challenger;
- final Current Talent uncertainty model;
- component-specific shrinkage or recalibration unless validated as a challenger;
- Projection / future aging and development;
- playing time / role;
- defense;
- WAR / value conversion;
- final cross-player ranking.

## Recommended next batch

**Do not retune B1 or B2.**

1. Build a concise source-capability inventory for candidate richer batting evidence, deliberately looking for mature reusable public datasets/parsers/packages before raw-source work.
2. Measure historical/player/league coverage, with special attention to whether MiLB levels actually have EV/LA or pitch-process data over the validation years.
3. Select one narrow evidence family and write its predeclared challenger contract against frozen B2 before implementation.

Do not begin Projection, playing-time, defense, WAR, or final-ranking work inside this gate.

## If starting a new chat

1. Read this file.
2. Read `docs/current-talent-validation-contract.md`.
3. Read `docs/current-talent-results-only-baseline-freeze.md`.
4. Inspect the current `source-certification-poc` head.
5. Continue with the **richer-evidence source-capability inventory**. Do not rerun B1 calibration/grid/confirmation or B2 development/confirmation first.
