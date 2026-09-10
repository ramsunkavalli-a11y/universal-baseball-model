# Ordered four-year prospect transition path

Status: research comparison complete; no player value changed.

The challenger fits forward-only annual transitions among no MLB, fringe,
meaningful and established career milestones, then propagates one probability
simplex for four years. It is compared with a direct four-year endpoint model using
the same initial level/exposure features. Regularization was selected on the 2019
cohort; the 2021 cohort and 2022-2025 outcomes were then scored unchanged.

| Group | 2019 log-loss delta | 2019 Brier delta | 2021 log-loss delta | 2021 Brier delta | Decision |
|---|---:|---:|---:|---:|---|
| Hitter | +0.015489 | +0.003470 | -0.013260 | -0.005083 | Reject |
| Pitcher | +0.014419 | +0.003036 | -0.004420 | -0.001413 | Reject |

The path is coherent and cannot move backward. It does not yet model future MiLB
production or post-arrival MLB skill, so it cannot replace the current safeguard
unless both proper scores improve. No outside FV enters the test.
