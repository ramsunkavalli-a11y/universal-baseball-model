# Pitcher contact increment audit

Status: **rejected**; production model unchanged.

- Development: 2021 inputs predict 2022 (1632 pitchers).
- Frozen outer test: 2022 inputs predict 2023 (1688 pitchers).
- Untouched confirmation: 2023 inputs predict 2024; model remains fit on 2021 only (1656 pitchers).
- Development-selected contact path: `ground`.

| Model | Outer RMSE | Outer MSE change [95% interval] | Confirm RMSE | Confirm MSE change [95% interval] |
|---|---:|---:|---:|---:|
| baseline | 0.22529 | — | 0.20984 | — |
| ground | 0.22415 | -0.000512 [-0.000972, -0.000063] | 0.21057 | +0.000309 [-0.000099, +0.000732] |
| popup | 0.22439 | -0.000403 [-0.000877, +0.000057] | 0.21068 | +0.000356 [-0.000079, +0.000792] |
| pulled_air | 0.22409 | -0.000538 [-0.001033, -0.000063] | 0.21042 | +0.000244 [-0.000191, +0.000701] |
| pulled_ground | 0.22379 | -0.000675 [-0.001194, -0.000190] | 0.21013 | +0.000124 [-0.000324, +0.000598] |

Features were fixed in baseball order: ground rate, popup rate, pulled-air rate, then pulled-ground rate. Rates were exposure-shrunk; missing or sparse evidence did not receive favorable values. Selection used only the development transition. A research signal required negative full confidence intervals in both later transitions. It still must beat the existing level-translated projection before production use.

This is a level-and-season-adjusted conditional-quality test among pre-MLB pitchers with at least 100 BF in the next season. It does not estimate arrival or workload; those outcomes remain in the separate hurdle model.

## Selected ground-rate path by prior level

| Period | Prior level | Pitchers | MSE change [95% interval] |
|---|---|---:|---:|
| outer | ROOKIE_COMPLEX | 376 | +0.000373 [-0.000391, +0.001162] |
| outer | SINGLE_A | 303 | +0.000827 [-0.000188, +0.001841] |
| outer | HIGH_A | 357 | -0.001621 [-0.002692, -0.000516] |
| outer | AA | 347 | -0.000994 [-0.002039, +0.000008] |
| outer | AAA | 305 | -0.001084 [-0.002391, +0.000148] |
| confirmation | ROOKIE_COMPLEX | 379 | +0.000722 [-0.000073, +0.001554] |
| confirmation | SINGLE_A | 321 | +0.000386 [-0.000502, +0.001308] |
| confirmation | HIGH_A | 336 | +0.000014 [-0.001002, +0.001074] |
| confirmation | AA | 323 | +0.000408 [-0.000532, +0.001378] |
| confirmation | AAA | 297 | -0.000077 [-0.001180, +0.000997] |
