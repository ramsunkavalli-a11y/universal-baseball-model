# Prospect PBP plus pedigree stacking result

Status: **MIXED; REJECTED FOR THE CURRENT OPPORTUNITY MODEL**

This is the descriptive check frozen in
[`prospect-pbp-pedigree-stack-plan.md`](prospect-pbp-pedigree-stack-plan.md). The
2024 outcome had already been viewed in the earlier core-comparator test, so this is
not confirmation and could not authorize a model change.

## Result

The 2022 selection fold again chose combined trajectory and direction, 50-contact
regression and logistic `C = 1.0`. The comparator now included the stronger
baseball-development and draft/signing pedigree features.

- Selection log loss: **0.031505 incumbent -> 0.031087 candidate**.
- Selection Brier: **0.007024 -> 0.006980**.
- Descriptive outer log loss: **0.022501 -> 0.022283**.
- Descriptive outer Brier: **0.004800 -> 0.004820**, a reversal.
- Paired log-loss difference: **-0.000218**, 95% interval
  **[-0.000465, +0.000007]**.
- Paired Brier difference: **+0.0000200**, 95% interval
  **[-0.0000182, +0.0000621]**; candidate better in only **15.7%** of resamples.
- The supported **300+ MiLB PA** group was worse on both scores: 846 players and 14
  positive outcomes.
- Overall calibration intercept/slope improved modestly, but that does not override
  the proper-score and subgroup failures.

## Decision

Do not add these PBP contact-shape features to the current pedigree-inclusive
opportunity model. They contain some ranking/log-loss information, but the incremental
gain is not consistent across proper scores and harms the best-supported high-workload
group. This is exactly the kind of small, mixed result that the model-search policy
requires us to reject.

The useful work is retained: certified contact evidence, chronology-safe aggregation,
missing-source handling and reusable tests. A future process challenger should use a
different baseball question or genuinely new season, not rescue-tune these contact
shares on 2024. No FV or player value changes.

Machine-readable detail:
[`prospect-pbp-pedigree-stack-result.json`](prospect-pbp-pedigree-stack-result.json).
