# One-year joint prospect career state

Status: structure test complete; no current player value changed.

The challenger predicts one mutually exclusive next-season state: no MLB, fringe
MLB, meaningful MLB, or established MLB. It is compared with three independently
fit cumulative logits forced back into that same ordered simplex. Both use the same
cutoff-safe level/exposure features. Regularization was selected on 2022-to-2023,
then frozen for rolling 2023-to-2024 and 2024-to-2025 checks. Negative is better.

| Group | Target | Players | Joint-minus-ordered log loss | Joint-minus-ordered Brier |
|---|---:|---:|---:|---:|
| Hitter | 2024 | 3168 | +0.000129 | -0.000020 |
| Hitter | 2025 | 2964 | +0.000380 | +0.000337 |
| Pitcher | 2024 | 3715 | -0.000586 | +0.000066 |
| Pitcher | 2025 | 3497 | -0.001226 | -0.000226 |

This is the first transition, not the complete six-year model. It tests whether a
joint state representation is a better foundation before adding later MLB-state
progression, attrition, workload and WAR. The 2020 snapshot is excluded because its
current workload was structurally shortened. No outside FV enters either model.
