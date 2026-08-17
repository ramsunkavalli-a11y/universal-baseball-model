# Current Talent Baseline 2 confirmation checkpoint

Last updated: 2026-08-16  
Status: **CONFIRMED ON HELD-OUT 2023.**

## Decision

The fixed multi-season results-only challenger **confirmed on 2023** and is promoted as the universal results-only comparator for the next Current Talent tier.

Method: `translated_multiseason_recency_empirical_bayes_v1`.

No Baseline 2 grid or parameter search was run on 2023. The confirmation workflow evaluated only:

- frozen season-to-date B1 `hl180_ps100_fitted`;
- fixed B2 from the passed 2022 development gate.

Workflow run: **31998882475**.  
Machine-readable result: `docs/current-talent-baseline2-confirmation-result.json`.

## Fixed B2 specification

The only change from frozen B1 is player-specific history depth:

- maximum results history: **1,095 calendar days**;
- recency half-life: **180 days**;
- empirical-Bayes prior strength: **100 effective core events**;
- same fold-specific fitted level translation as B1;
- same frozen Baseline 0 prior as B1;
- same 12-component Current Talent profile and 90-day future scoring target.

No Statcast, pitch-level, swing, scouting, Projection, playing-time, defense, or WAR information entered this confirmation.

## 2023 fold results

| cutoff | frozen B1 log loss | B2 log loss | B2 - B1 | frozen B1 Brier | B2 Brier | B2 - B1 |
|---|---:|---:|---:|---:|---:|---:|
| 2023-07-15 | 2.254303 | 2.250495 | -0.003807 | 0.870022 | 0.869275 | -0.000747 |
| 2023-08-01 | 2.250926 | 2.248013 | -0.002913 | 0.869251 | 0.868688 | -0.000563 |
| 2023-09-01 | 2.251711 | 2.249416 | -0.002296 | 0.869687 | 0.869274 | -0.000413 |

Equal-fold means:

- frozen B1 log loss: **2.252313**;
- B2 log loss: **2.249308**;
- B2 minus B1 log loss: **-0.003005**;
- frozen B1 Brier: **0.869653**;
- B2 Brier: **0.869079**;
- B2 minus B1 Brier: **-0.000574**;
- B2 wins: **3/3** log loss and **3/3** Brier.

The 2023 improvement is slightly larger than the 2022 development improvement rather than shrinking or reversing.

## League breadth

The improvement remained universal across every meaningfully supported non-MLB target level:

- AAA: B2 better on both scores in all 3 folds;
- AA: better on both in all 3;
- High-A: better on both in all 3;
- Single-A: better on both in all 3;
- Rookie Complex: better on both in every available scored fold.

No meaningfully supported non-MLB level triggered the predeclared reversal guardrail.

This is important for the project boundary: the gain from prior-season results does **not** depend on MLB-only tracking availability.

## Component breadth

Across the 36 component × confirmation-fold comparisons:

- B2 improved multinomial log-loss contribution in **25/36**;
- B2 improved binary Brier contribution in **36/36**;
- no component was worse on both proper scores in all three confirmation folds.

Across development plus confirmation combined:

- component log-loss wins: **51/72**;
- component Brier wins: **72/72**.

BB/HBP and some directional contact components can still lose the component log-loss comparison in individual/all folds, but those losses do not reproduce on Brier and do not create a broad proper-score reversal. They remain diagnostics for later challengers rather than reasons to tune B2 after confirmation.

## Calibration

All component calibration fits converged.

On 2023, mean absolute calibration error improved materially:

- intercept: **0.5223 -> 0.3496**;
- slope: **0.1907 -> 0.1300**.

Fixed-bin ECE moved slightly the other way (**0.002615 -> 0.002734**), echoing the earlier finding that coarse ECE can disagree with intercept/slope calibration. This does not invalidate the proper-score result and was not a hard gate under the predeclared plan.

Across the six 2022–2023 folds, B1 and B2 have essentially identical mean fixed-bin ECE (~0.002560 vs ~0.002563), while B2 is substantially better on calibration intercept and slope.

## Six-fold development + confirmation view

Across all six B2 evaluation folds:

- frozen B1 mean log loss: **2.254417**;
- B2 mean log loss: **2.251603**;
- delta: **-0.002814**;
- frozen B1 mean Brier: **0.869698**;
- B2 mean Brier: **0.869166**;
- delta: **-0.000532**;
- B2 fold wins: **6/6** log loss, **6/6** Brier.

Mean absolute calibration error across those six folds:

- intercept: **0.5233 -> 0.3676**;
- slope: **0.1917 -> 0.1386**.

## Baseball interpretation

The evidence says the frozen B1 was forgetting useful information too quickly at the **season boundary**, even though its within-history 180-day decay was sensible.

In practical terms: a hitter's previous-season K/BB/contact-shape record still contains real information about his current underlying batting profile after controlling for age/level, translating environments, heavily down-weighting old events, and adding the current season.

At the 2022 development snapshots, about **82.6%** of model-eligible players had useful prior-season evidence. On 2023 confirmation that was **82.5%**, with about **56 additional effective core events per player** on average after recency decay. The effect is therefore both broad and materially sized.

## Promotion boundary

Promote B2 as the fixed **universal results-only Current Talent comparator** for richer challengers.

Keep B1 frozen as the simpler season-to-date reference. Do not retrofit B1 or retune B2 when richer process/tracking/scouting models are tested.

The next gate is not another results-only search. It is a **source-capability and richer-evidence challenger design**, beginning with one evidence family at a time. Because tracking/process coverage can differ materially by league, the next architecture may be tiered, but players without richer evidence must fall back to the validated universal results-only comparator rather than receive synthetic MLB-derived features.
