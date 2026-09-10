# Prospect development-state result

Status: research test complete; no current value changed.

The test adds four cutoff-safe development-history facts to the next-season ordered
career-state forecast and also checks whether a joint multinomial structure helps.
Regularization was selected on 2022-to-2023, then frozen for rolling 2023-to-2024 and
2024-to-2025 evaluation. Negative deltas beat the ordered level/exposure baseline.

| Group | Target | Candidate | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---:|---|---:|---:|---|
| Hitter | 2024 | ordered_development_path | +0.000659 [-0.001318, +0.002481] | -0.000072 [-0.000772, +0.000677] | Reject |
| Hitter | 2024 | joint_level_exposure | +0.000129 [-0.001456, +0.001544] | -0.000020 [-0.000477, +0.000400] | Reject |
| Hitter | 2024 | joint_development_path | +0.001711 [-0.000804, +0.004150] | -0.000031 [-0.000981, +0.000895] | Reject |
| Hitter | 2025 | ordered_development_path | +0.000516 [-0.001019, +0.001827] | +0.000043 [-0.000562, +0.000585] | Reject |
| Hitter | 2025 | joint_level_exposure | +0.000380 [-0.000950, +0.001638] | +0.000337 [-0.000076, +0.000748] | Reject |
| Hitter | 2025 | joint_development_path | +0.002319 [+0.000316, +0.004330] | +0.000660 [-0.000110, +0.001478] | Reject |
| Pitcher | 2024 | ordered_development_path | -0.000725 [-0.001814, +0.000339] | -0.000255 [-0.000665, +0.000148] | Reject |
| Pitcher | 2024 | joint_level_exposure | -0.000586 [-0.001390, +0.000179] | +0.000066 [-0.000212, +0.000341] | Reject |
| Pitcher | 2024 | joint_development_path | -0.001616 [-0.002734, -0.000482] | -0.000480 [-0.000864, -0.000110] | Reject |
| Pitcher | 2025 | ordered_development_path | -0.001602 [-0.002414, -0.000765] | -0.000535 [-0.000849, -0.000220] | Reject |
| Pitcher | 2025 | joint_level_exposure | -0.001226 [-0.001978, -0.000478] | -0.000226 [-0.000472, +0.000021] | Reject |
| Pitcher | 2025 | joint_development_path | -0.002294 [-0.003312, -0.001369] | -0.000574 [-0.000949, -0.000220] | Reject |

The gate requires development point improvement and both later paired intervals below
zero for both scores. These cohorts were previously inspected by related models, so a
passing result would only define a future confirmation candidate. It cannot change
current values. No 2026 outcome, organization, or outside FV is used.
