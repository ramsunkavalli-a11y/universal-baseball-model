# Prospect post-arrival workload progression result

Status: research test complete; no current value changed.

The challenger adds only prior-season official MLB workload, normalized to mean active
workload in that season, plus an active indicator. It predicts advancement from fringe
to a higher state and from meaningful to established. Regularization was selected for
the 2023 outcome; 2024 and 2025 were then scored unchanged. Negative is better.

| Group | Origin | Outcome | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---|---:|---:|---:|---|
| Hitter | FRINGE_MLB | 2024 | -0.055171 [-0.072973, -0.037755] | -0.018320 [-0.025577, -0.011624] | Pass |
| Hitter | MEANINGFUL_MLB | 2024 | -0.029869 [-0.061271, +0.003230] | -0.010088 [-0.022526, +0.002980] | Reject |
| Hitter | FRINGE_MLB | 2025 | -0.049563 [-0.070190, -0.029902] | -0.012230 [-0.019940, -0.005042] | Pass |
| Hitter | MEANINGFUL_MLB | 2025 | -0.062590 [-0.101275, -0.024392] | -0.020687 [-0.034322, -0.005153] | Reject |
| Pitcher | FRINGE_MLB | 2024 | -0.043100 [-0.083353, -0.003800] | -0.012934 [-0.022488, -0.003762] | Pass |
| Pitcher | MEANINGFUL_MLB | 2024 | -0.036771 [-0.133596, +0.075111] | -0.020923 [-0.056022, +0.015974] | Reject |
| Pitcher | FRINGE_MLB | 2025 | -0.042343 [-0.071098, -0.010333] | -0.009909 [-0.017346, -0.003070] | Pass |
| Pitcher | MEANINGFUL_MLB | 2025 | -0.028459 [-0.115583, +0.067542] | -0.014757 [-0.048625, +0.021100] | Reject |

A pass means realized workload should be carried inside a future annually linked
career simulation. It does not authorize using future workload as if known today and
does not alter current player values. This is a predictive state-within-cell signal,
not evidence that playing time itself causes development; workload also measures how
close a player already is to the next cumulative state. The 2020 target, current 2026
data, organization and outside FV are excluded.

Verification: 1,527 tests pass. The only four failures are the already documented
research contracts whose ignored generated artifacts are not present. Static checks
and repository diff checks pass.
