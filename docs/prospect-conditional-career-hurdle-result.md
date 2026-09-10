# Prospect conditional career-hurdle audit result

Status: corrected core conditional hurdle accepted for the private current-value sensitivity; richer feature families rejected.

## Outer 2023 result

The outer test trains on the 2018 and 2021 snapshots, then evaluates two-year outcomes from the 2023 snapshot through completed 2025.

| Player type | Conditional stage | Players | Positives | Observed rate | Core log loss | Core Brier |
|---|---|---:|---:|---:|---:|---:|
| Hitter | Meaningful given arrival | 206 | 63 | 30.58% | 0.5750 | 0.1956 |
| Hitter | Established given meaningful | 63 | 30 | 47.62% | 0.7028 | 0.2533 |
| Pitcher | Meaningful given arrival | 252 | 76 | 30.16% | 0.5832 | 0.1986 |
| Pitcher | Established given meaningful | 76 | 34 | 44.74% | 0.6352 | 0.2189 |

The conditional rates are large enough to distinguish credible arrivals from the full non-arrival population. They also create the required ordering by multiplication rather than repairing contradictory unconditional probabilities after the fact.

The hitter meaningful-stage interaction candidate reversed on the outer check: log loss worsened from 0.5750 to 0.5837 and Brier worsened from 0.1956 to 0.1991. The pitcher established interaction candidate also reversed. Pitcher meaningful selection retained core.

The development-selected hitter established model stayed inside the core feature family but used stronger regularization and 50 PA of rate regression. Its outer point scores improved to 0.6822 log loss and 0.2445 Brier, although both paired intervals cross zero. It is retained as cautious shrinkage, not as proof of a new signal. No richer feature family is promoted.

Core calibration is usable for this limited next step. Meaningful-stage calibration slopes were 1.05 for hitters and 0.88 for pitchers. Established-stage samples are smaller and less certain. The selected hitter shrinkage has a 1.16 outer calibration slope, compared with 0.35 for the less-regularized core fit. This still requires wide uncertainty and later confirmation.

## Decision

Use the conditional models only in a private sensitivity:

`P(arrival) × P(meaningful | arrival) × P(established | meaningful)`

Use core `C=1` for both meaningful-given-arrival stages and pitcher established-given-meaningful. Use core `C=.1` plus 50 PA of production regression for hitter established-given-meaningful. Keep the existing time-ordered feature set. Do not add pedigree, demographic, country, physical, position-preference, or outside-FV adjustments to the conditional quality stages.

Machine-readable detail: `docs/prospect-conditional-career-hurdle-result.json`.
