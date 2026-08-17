# Current Talent Baseline 2 development checkpoint

Last updated: 2026-08-16  
Status: **PASSED DEVELOPMENT; ELIGIBLE FOR FIXED 2023 CONFIRMATION.**

## Question tested

Does carrying prior-season results forward improve present batting Current Talent estimates beyond the frozen season-to-date Baseline 1?

The predeclared challenger changed only player-specific history depth:

- frozen B1: current-season evidence only;
- B2: current season plus prior certified seasons within a 1,095-day calendar lookback;
- both use a 180-day exponential half-life;
- both use the same 100-event empirical-Bayes prior strength;
- both use the same fold-specific fitted translation;
- both use the same frozen Baseline 0 prior;
- no tracking, Statcast, pitch-level, scouting, Projection, playing-time, defense, or WAR inputs were added.

Predeclared plan: `docs/current-talent-baseline2-plan.md`.
Machine-readable result: `docs/current-talent-baseline2-development-result.json`.
Workflow run: **31998668697**.

## Development folds

Only 2022 was used for the incremental multi-season test:

- 2022-07-15;
- 2022-08-01;
- 2022-09-01.

B2 could use certified 2021 history plus eligible pre-cutoff 2022 evidence. The development workflow did not download or evaluate 2023 evidence.

## Proper-score result

Baseline 2 improved both proper scores in all three folds.

| cutoff | frozen B1 log loss | B2 log loss | B2 - B1 | frozen B1 Brier | B2 Brier | B2 - B1 |
|---|---:|---:|---:|---:|---:|---:|
| 2022-07-15 | 2.257885 | 2.254772 | -0.003113 | 0.870021 | 0.869423 | -0.000597 |
| 2022-08-01 | 2.256096 | 2.253350 | -0.002746 | 0.869709 | 0.869192 | -0.000517 |
| 2022-09-01 | 2.255578 | 2.253572 | -0.002007 | 0.869500 | 0.869142 | -0.000358 |

Equal-fold means:

- frozen B1 log loss: **2.256520**;
- B2 log loss: **2.253898**;
- B2 minus B1 log loss: **-0.002622**;
- frozen B1 Brier: **0.869743**;
- B2 Brier: **0.869252**;
- B2 minus B1 Brier: **-0.000491**;
- B2 wins: **3/3** log loss and **3/3** Brier.

The gain is materially larger than the tiny hyperparameter differences that separated the final frozen B1 candidate from its 90/100/fitted reference during the earlier simple-baseline grid.

## Breadth / league guardrail

The result was not an MLB-only artifact. Every meaningfully supported non-MLB target level improved on both proper scores in every available 2022 fold:

- AAA;
- AA;
- High-A;
- Single-A;
- Rookie Complex.

No meaningfully supported non-MLB level failed the predeclared reversal guardrail.

Across 36 component × fold comparisons:

- B2 improved multinomial log-loss contribution in **26/36**;
- B2 improved binary Brier contribution in **36/36**.

The component result is broad but not universal on log loss, which remains visible for confirmation rather than being patched after the fact.

## Calibration

All component calibration fits converged.

Equal-fold mean absolute calibration error improved rather than merely staying inside the guardrail:

- intercept: **0.5242 -> 0.3857**;
- slope: **0.1927 -> 0.1473**.

Fixed-bin ECE also improved on the first two folds and was essentially flat on the September fold. No new structural calibration failure appeared.

## How much prior-year evidence mattered

Across the three development snapshots, about **82.6%** of model-eligible players had positive effective prior-season evidence in B2. The added history contributed about **45.2 effective core events per model-eligible player on average** after the frozen 180-day decay.

This is enough to be a meaningful test of the multi-season idea rather than a near-duplicate of B1.

## Development decision

Every predeclared promotion check passed:

- lower equal-fold mean log loss;
- no worse equal-fold mean Brier;
- at least 2/3 fold log-loss wins (observed 3/3);
- identical scored coverage;
- no consistent lower-level reversal;
- all calibration fits converged;
- intercept and slope calibration stayed comfortably inside the 25% deterioration guardrail and in fact improved.

Therefore **the exact fixed B2 challenger advances to 2023 confirmation**.

## Holdout boundary

Do not change the 1,095-day lookback, 180-day half-life, 100-event prior, translation treatment, B0 prior, or other model rules in response to 2023.

The 2023 gate may evaluate only:

1. frozen season-to-date B1 `hl180_ps100_fitted`;
2. fixed B2 `translated_multiseason_recency_empirical_bayes_v1`.

If B2 reverses on 2023, reject it and retain frozen B1. Do not search a nearby multi-season weighting on the confirmation period.
