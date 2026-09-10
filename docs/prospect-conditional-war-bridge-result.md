# Prospect conditional-WAR bridge result

Status: **retrospective development; no production change**.

The fixed candidate uses only cutoff-known core baseball evidence to estimate two-year
component WAR conditional on arrival, then multiplies by the unchanged arrival
probability. Non-arrivals remain zero in the end-to-end score.

| Type | Players | Arrivals | Baseline RMSE | Ridge RMSE | Baseline MAE | Ridge MAE |
|---|---:|---:|---:|---:|---:|---:|
| Hitters | 3,260 | 259 | 0.428 | 0.414 | 0.091 | 0.084 |
| Pitchers | 3,649 | 273 | 0.234 | 0.231 | 0.057 | 0.050 |

Hitter promising gate: **False**. Pitcher
promising gate: **False**. These are development
decisions only; the 2021 cohort is already exposed and cannot promote a model.

Both candidates improve end-to-end RMSE and MAE with wholly favorable paired
intervals, and both improve RMSE among players who actually arrive. The frozen gate
still fails because absolute mean bias moves slightly farther from zero. Preserve the
form for later confirmation; do not recalibrate it on this exposed cohort.

Largest standardized hitter coefficients: production_rate_4 (+0.210), production_rate_3 (+0.194), age (-0.140), level_A_OR_BELOW (-0.103), role_CORNER (+0.078). Largest standardized
pitcher coefficients: production_rate_4 (-0.108), role_STARTER (+0.092), production_rate_3 (-0.067), production_rate_1 (+0.061), age (+0.047). These are predictive diagnostics, not causal
effects or player bonuses.
