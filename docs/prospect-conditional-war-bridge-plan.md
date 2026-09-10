# Prospect conditional-WAR bridge plan

**Status:** frozen before scoring

## Question

Can cutoff-known, universal affiliated performance and development evidence improve
the amount of two-year MLB component WAR expected after arrival, without changing the
separately estimated arrival probability?

This directly targets the linked-path failure: pooled paths overvalue many pitcher
non-arrivals and undervalue the positive hitter tail. It is not another arrival,
demographic, FV-grade or contract model.

## Chronology and population

- Fit on every eligible pre-MLB player in the 2018 snapshot.
- Training outcomes are MLB component WAR in 2019-2020.
- Score every eligible pre-MLB player in the 2021 snapshot on 2022-2023 outcomes.
- Preserve non-arrivals as zero in end-to-end scoring.
- Separately report conditional error among players who actually record MLB workload.
- Scale 2020 workload by the existing `162/60` rule in both target construction and
  league replacement context.

The 2021 cohort has been used in other development work. This is a chronology-safe
retrospective development test, not fresh confirmation and not a production gate.

## Frozen models

Both models use the same core two-year arrival probability fit on the 2018 cohort.

1. **Pooled conditional baseline:** arrival probability multiplied by mean two-year
   component WAR among 2018 players who reach MLB.
2. **Regressed core candidate:** arrival probability multiplied by a standardized
   ridge estimate of conditional two-year WAR. Ridge penalty is fixed at `100` before
   scoring. Predictors are age, level, current and prior affiliated workload, number
   of prior affiliated seasons, dated 40-man status, broad role and the four core
   event rates regressed with `200` opportunities toward the 2018 population.

No target or player prediction is clipped. Birth country, city, state, height, weight,
strike-zone bounds, handedness-only bonuses, draft/FV opinions, organization and depth
charts are excluded. They cannot directly add talent in this test.

## Evaluation

- End-to-end mean, bias, MAE and RMSE on the identical full player cohort.
- The same measures conditional on observed MLB arrival.
- Paired player bootstrap differences for MSE and absolute error.
- Prespecified diagnostics by level, role, evidence volume and handedness where at
  least 100 players are available; diagnostics cannot select a separate model.
- Record source, experiment and exact player-cohort hashes.

The candidate is only promising development evidence if end-to-end RMSE and MAE both
improve at the point estimate, absolute bias does not worsen, and the arrived-player
RMSE does not worsen. Any result remains outside current values until a later untouched
confirmation exists.

