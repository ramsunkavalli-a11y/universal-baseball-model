# Current Talent calibration checkpoint

Last updated: 2026-08-16  
Status: **nine-fold fixed-setting calibration review complete; Baseline 1 improves calibration intercept/slope materially over Baseline 0, while coarse reliability ECE is mixed/slightly worse. No recalibration has been applied.**

This checkpoint evaluates calibration for the simple Current Talent baselines across the nine common chronological folds already used for predictive validation:

- 2021 / 2022 / 2023;
- July 15 / August 1 / September 1;
- fitted-translation and zero-offset variants;
- Baseline 0 and Baseline 1;
- all 12 core profile components.

Primary workflow run: **`31996082936`**  
Summary artifact: `current-talent-calibration-review-summary` — artifact ID **`9276886902`**.  
Workflow: `.github/workflows/current-talent-calibration-review.yml` — **manual-only** after bootstrap cleanup.

## Calibration diagnostics

Existing reliability diagnostics use fixed 10-bin expected calibration error (ECE).

This gate adds grouped-binomial logistic calibration coefficients for every model × component × fold:

`logit(P[future component k]) = intercept + slope * logit(predicted probability k)`

Ideal calibration:

- intercept = **0**;
- slope = **1**.

Standard interpretation:

- slope < 1: predictions are generally too dispersed / too extreme for that component;
- slope > 1: predictions are generally not dispersed enough;
- intercept measures an overall calibration offset conditional on the fitted slope.

These coefficients are **diagnostics only**. They are not fed back into predictions and no post-hoc recalibration is performed in this gate.

Implementation:

- `src/universal_baseball/current_talent_calibration.py`
- `scripts/materialize_current_talent_calibration_fold.py`
- `scripts/summarize_current_talent_calibration_review.py`
- `tests/test_current_talent_calibration.py`

All 432 model × component × fold coefficient fits converged:

- 9 folds;
- 2 translation variants;
- 2 baseline models;
- 12 components.

## Overall calibration summary

Event-weighted across the nine folds and 12 components:

| Translation | Model | Mean absolute intercept error | Mean absolute slope error | Mean 10-bin ECE |
|---|---|---:|---:|---:|
| fitted | Baseline 0 | 0.8656 | 0.3397 | **0.00323** |
| fitted | Baseline 1 | **0.5312** | **0.1934** | 0.00358 |
| zero offsets | Baseline 0 | 0.8039 | 0.3067 | **0.00319** |
| zero offsets | Baseline 1 | **0.5433** | **0.1989** | 0.00381 |

Interpretation:

- Baseline 1 is **much closer to ideal intercept/slope calibration** than Baseline 0 under both translation variants.
- Baseline 1's coarse 10-bin ECE is slightly worse overall.
- This is not contradictory: B0 is highly shrunk and can look good in reliability bins because its predictions remain close to population averages, while B1 adds useful individual discrimination/sharpness. Proper scores and intercept/slope diagnostics indicate that B1's added variation is useful even though some component mean/reliability errors remain.

Across all 216 B1-vs-B0 model/component/fold comparisons (both translation variants):

- B1 has lower absolute intercept error in **138 / 216**;
- B1 has lower absolute slope error in **143 / 216**;
- B1 has lower 10-bin ECE in only **71 / 216**.

Mean B1-minus-B0 error differences:

- absolute intercept error: **-0.291**;
- absolute slope error: **-0.122**;
- ECE: **+0.00054**.

The primary proper-score result remains decisive context: B1 beat B0 on log loss and Brier in all nine common July 15 / August 1 / September 1 folds.

## Baseline 1 fitted-translation component patterns

Event-weighted across the nine folds:

| Component | Mean intercept | Mean slope | Mean ECE | Slope direction across folds |
|---|---:|---:|---:|---|
| BB/HBP | -0.025 | **0.982** | 0.00254 | <1 in 7/9 |
| K | +0.251 | **1.165** | **0.01380** | >1 in 8/9 |
| IFFB | -0.649 | 0.824 | 0.00314 | <1 in 9/9 |
| Pull GB | -0.111 | 0.920 | 0.00463 | <1 in 6/9 |
| Center GB | +0.100 | 1.043 | **0.00115** | >1 in 9/9 |
| Oppo GB | +0.133 | 1.067 | 0.00315 | >1 in 8/9 |
| Pull LD | -1.022 | 0.662 | 0.00218 | <1 in 9/9 |
| Center LD | -0.571 | 0.804 | 0.00149 | <1 in 9/9 |
| Oppo LD | -0.701 | 0.823 | 0.00405 | <1 in 9/9 |
| Pull OFFB | -0.472 | 0.861 | 0.00222 | <1 in 9/9 |
| Center OFFB | -0.856 | 0.645 | 0.00285 | <1 in 9/9 |
| Oppo OFFB | -1.276 | 0.553 | 0.00174 | <1 in 9/9 |

The most important systematic patterns are therefore:

- **K:** B1 underpredicts the aggregate K rate and has slope > 1 in nearly every fold. Across the nine fitted-translation folds, predicted K rate is ~23.46% versus observed ~24.55%. K is also the dominant source of B1 ECE.
- **BB/HBP:** already close to ideal calibration on both intercept and slope.
- **Groundball direction:** generally much better calibrated than air/line-drive shape; Center GB is especially close to ideal.
- **LD/OFFB directional components:** slopes are consistently below 1, often substantially, indicating the component forecasts are too dispersed/extreme relative to realized future variation.

These patterns are stable enough to matter for model selection; they should not be hidden by aggregate Brier/log-loss wins.

## B1 fitted translation vs zero offsets — calibration

Across 108 B1 component/fold comparisons:

- fitted translation has lower absolute intercept error in **71 / 108**;
- lower absolute slope error in **65 / 108**;
- lower ECE in **70 / 108**.

Mean fitted-minus-zero calibration-error differences:

- absolute intercept error: **-0.0205**;
- absolute slope error: **-0.0086**;
- ECE: **-0.00030**.

So fitted translation is modestly favorable for B1 calibration in aggregate even though its **proper-score** contribution was small and not temporally stable at every cutoff. This does not overturn the earlier translation decision: fitted and zero-offset variants remain candidates for formal chronological selection.

## Why ECE and intercept/slope disagree

ECE is useful but should not be the sole model-selection criterion here.

A strongly regressed population prior can achieve low reliability-bin error simply by making conservative predictions near the population mean. That sacrifices individual resolution. B1 deliberately introduces player-specific signal; its broad proper-score win shows that this additional resolution is useful.

Calibration intercept/slope asks a complementary question: conditional on how much predictions vary, are their level and dispersion appropriate? On that dimension B1 is materially better than B0, though several profile components still show systematic miscalibration.

Therefore:

- do **not** choose B0 merely because its aggregate ECE is smaller;
- do **not** ignore B1's component calibration defects merely because its proper scores are better;
- model selection should jointly consider proper score, intercept/slope, reliability ECE, coverage, and stability across chronology.

## What this gate establishes

- B1's proper-score improvement is not accompanied by globally worse calibration in the stronger intercept/slope sense; it actually improves those diagnostics materially.
- B1 still has component-specific calibration defects, especially K mean bias and overly dispersed LD/OFFB directional predictions.
- Fitted translation modestly improves B1 calibration on average but is still a second-order effect.
- Calibration issues are systematic enough to use in model selection, not noise that should be patched after the fact.

## What this gate does not justify

- no post-hoc calibration transform;
- no component-specific shrinkage yet;
- no new translation complexity;
- no frozen 90-day half-life or 100-event prior strength;
- no promotion to Baseline 2 or richer inputs.

Those changes must earn out-of-time value inside the chronological model-selection process.

## Next gate

Define a **small predeclared chronological selection grid** for the simple baseline. The grid should vary only the highest-value unresolved choices:

1. recency half-life;
2. empirical-Bayes prior strength;
3. translation variant (fitted vs zero offsets).

Keep the B0 age-band / peer policy fixed initially unless the first grid exposes a clear reason to expand it.

Use earlier seasons/folds for selection and reserve a later season for confirmation; do not optimize against all nine folds simultaneously. Selection should weigh proper scores first, then calibration stability and coverage as tie-breakers/guardrails.
