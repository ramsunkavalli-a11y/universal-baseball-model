# Current Talent simple-baseline freeze

Last updated: 2026-08-16  
Status: **FROZEN as the simple results-only Current Talent baseline.**

## Decision

Freeze **`hl180_ps100_fitted`** as the simple Current Talent baseline against which future challengers must be evaluated out of time.

Selected settings:

- predictor recency half-life: **180 days**;
- Baseline 1 empirical-Bayes prior strength: **100 effective core events**;
- environment translation: **`fitted_translation`**;
- Baseline 0 age-band width: **2.0 years**;
- Baseline 0 minimum preferred age+level peers: **12**.

All other observation, temporal, scoring, target-horizon, component, identity, and source-authority rules remain those frozen by `docs/current-talent-validation-contract.md` and `docs/current-talent-baseline-selection-plan.md`. This freeze does not claim every fixed rule is globally optimal; it establishes the reproducible simple baseline that richer models must beat.

## Why the freeze gate passes

### Development selection — 2021–2022 only

The predeclared 18-candidate grid selected `hl180_ps100_fitted` on six chronological development folds without using alternative 2023 grid results.

- mean B1 log loss: **2.255543**;
- mean B1 Brier: **0.869233**;
- mean B1−B0 log loss: **-0.017598**;
- mean B1−B0 Brier: **-0.004643**;
- B1 wins vs B0: **6/6** folds on log loss and **6/6** on Brier;
- selected minus 90/100/fitted reference: **-0.000262** log loss and **-0.000133** Brier.

Development breadth guardrails were also favorable: **72/72** component log-loss wins, **66/72** component Brier wins, and **125/125** stratum wins on both log loss and Brier versus B0.

Source: `docs/current-talent-development-selection-checkpoint.md` and `docs/current-talent-development-selected-candidate.json`.

### Held-out-for-grid confirmation — 2023

The selected candidate was then evaluated on only the three 2023 confirmation folds, alongside B0 and the fixed 90/100/fitted reference. The full 18-candidate grid was not evaluated on 2023.

- mean B1 log loss: **2.252313**;
- mean B1 Brier: **0.869653**;
- mean B1−B0 log loss: **-0.018814**;
- mean B1−B0 Brier: **-0.004777**;
- B1 wins vs B0: **3/3** folds on log loss and **3/3** on Brier;
- selected minus fixed reference: **-0.000245** log loss and **-0.000105** Brier;
- component wins vs B0: **36/36** log loss and **35/36** Brier;
- stratum wins vs B0: **62/62** on both proper scores.

The confirmation workflow also enforced equal candidate coverage and converged calibration diagnostics. No structural coverage failure appeared.

Source: `docs/current-talent-2023-confirmation-checkpoint.md` and `docs/current-talent-2023-confirmation-result.json`.

## Calibration guardrail

Calibration is imperfect but interpretable and does not invalidate the proper-score result.

For the selected candidate, combining the six development folds with the three 2023 confirmation folds gives equal-fold mean diagnostics of approximately:

- mean absolute calibration-intercept error: **0.5513**;
- mean absolute calibration-slope error: **0.2010**;
- mean fixed-bin ECE: **0.00299**.

The broader nine-fold calibration review already established that B1 materially improves intercept/slope calibration over B0 even though coarse ECE can be slightly worse. Known component defects remain visible: K has mean-rate bias / slopes above 1, while several LD/OFFB directional components have slopes below 1 and are too dispersed. These are documented challenger targets, not reasons to retrofit the frozen baseline after seeing confirmation results.

Source: `docs/current-talent-calibration-checkpoint.md`.

## Freeze boundary

This decision freezes the **simple results-only Current Talent baseline**, not the full player-ranking system.

Still unfrozen and requiring separate validation:

- Baseline 2 or any richer process / tracking / scouting evidence;
- component-specific shrinkage or post-hoc recalibration;
- a final uncertainty model;
- Projection / future aging and development;
- playing time or role;
- defense;
- WAR / value conversion;
- final cross-player ranking.

Do not tune the frozen baseline in response to a richer challenger. Any proposed change to its settings is itself a new challenger and must earn out-of-time value under the same chronological protocol.

## Next gate

Use `hl180_ps100_fitted` as the fixed comparator and define the first **Baseline 2 / richer-evidence challenger** narrowly. Add one evidence family or modeling change at a time, predeclare its comparison protocol, preserve the same eligible population where possible, and require an out-of-time proper-score improvement before promotion.
