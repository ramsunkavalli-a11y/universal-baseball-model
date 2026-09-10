# Prospect conditional career-hurdle audit result

Status: core conditional hurdle accepted for a private current-value sensitivity; richer challengers rejected.

## Outer 2023 result

The outer test trains on the 2018 and 2021 snapshots, then evaluates two-year outcomes from the 2023 snapshot through completed 2025.

| Player type | Conditional stage | Players | Positives | Observed rate | Core log loss | Core Brier |
|---|---|---:|---:|---:|---:|---:|
| Hitter | Meaningful given arrival | 206 | 63 | 30.58% | 0.5725 | 0.1946 |
| Hitter | Established given meaningful | 63 | 30 | 47.62% | 0.6707 | 0.2389 |
| Pitcher | Meaningful given arrival | 252 | 76 | 30.16% | 0.5832 | 0.1986 |
| Pitcher | Established given meaningful | 76 | 34 | 44.74% | 0.6352 | 0.2189 |

The conditional rates are large enough to distinguish credible arrivals from the full non-arrival population. They also create the required ordering by multiplication rather than repairing contradictory unconditional probabilities after the fact.

The hitter meaningful-stage interaction candidate improved outer log loss by 0.0035 and Brier by 0.0013, but both paired intervals crossed zero. The hitter established candidate and pitcher established candidate reversed and became worse than core. Pitcher meaningful selection retained core. Therefore none of the richer candidates is promoted.

Core calibration is usable for this limited next step. Meaningful-stage calibration slopes were 0.97 for hitters and 0.88 for pitchers. Established-stage samples are smaller and slopes are less certain; the hitter slope of 3.56 warns that its predictions are compressed. This requires wide uncertainty and later confirmation.

## Decision

Use the core conditional models only in a private sensitivity:

`P(arrival) × P(meaningful | arrival) × P(established | meaningful)`

Keep the existing time-ordered feature set. Do not add pedigree, demographic, country, physical, position-preference, or outside-FV adjustments to the conditional quality stages. Do not change published or organization-neutral values until the multiplied current distribution passes its own checks.

Machine-readable detail: `docs/prospect-conditional-career-hurdle-result.json`.

