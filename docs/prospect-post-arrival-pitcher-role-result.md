# Prospect post-arrival pitcher-role result

Status: research test complete; no current value changed.

The challenger adds only prior-season start share and batters faced per game to the
already accepted age, elapsed-time and total-workload model. Regularization was
selected on 2023; 2024 and 2025 were scored unchanged. Negative is better.

| Origin | Outcome | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---:|---:|---:|---|
| FRINGE_MLB | 2024 | -0.006442 [-0.023089, +0.009074] | -0.002869 [-0.009319, +0.003402] | Reject |
| MEANINGFUL_MLB | 2024 | -0.002669 [-0.035252, +0.030565] | -0.002997 [-0.017251, +0.011086] | Reject |
| FRINGE_MLB | 2025 | +0.003991 [-0.008303, +0.015584] | +0.001055 [-0.003696, +0.005722] | Reject |
| MEANINGFUL_MLB | 2025 | -0.000657 [-0.034572, +0.033220] | -0.000747 [-0.015562, +0.013901] | Reject |

The features describe prior usage; they do not claim starter use causes development.
The 2020 target, current 2026 data, organization, future workload and outside FV are
excluded.

Decision: reject role as an independent career-state advancement input. Continue to
use starter/reliever evidence where it belongs—in pitcher workload and WAR paths—but
do not let it also raise the advancement hazard after total workload is known.
