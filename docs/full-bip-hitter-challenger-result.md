# Full BIP hitter contact-talent result

**Status:** overall forecasting signal confirmed; held back by one small level reversal
**Model effect:** none

## Source and method

Hitters use the exact same screened ten-bin BIP classifier and terminal outcomes as
pitchers. There is no hand-assigned pull, fly-ball, position, demographic, or prospect
bonus. Earlier-season outcomes set neutral values for each complete BIP shape. One
bounded residual weight was fit on 2021 predicting 2022 and then frozen for 2023.

| Test | Players | Baseline MAE | BIP blend MAE | Baseline RMSE | BIP blend RMSE |
|---|---:|---:|---:|---:|---:|
| 2021 → 2022 development | 2,343 | 0.05025 | 0.04932 | 0.06398 | 0.06305 |
| 2022 → 2023 confirmation | 2,249 | 0.04943 | 0.04895 | 0.06304 | 0.06238 |

The frozen BIP weight was `0.3209`. The BIP-only estimate was worse than the
results-based baseline, while the blend was better. That is sensible: hitter results
already carry much of the contact signal, so the shape profile is supplemental rather
than a replacement.

Contact-weighted MAE and RMSE improved at A, High-A, AA, AAA, and Rookie in the
confirmation season. Equal-player scores improved at four levels. AA reversed by only
`0.00014` MAE and `0.00024` RMSE, so the predeclared no-level-reversal gate did not
pass.

## Decision

Keep the hitter candidate in research with a zero production weight. The next test is
the complete active hitter replay, with level movement and evidence bands reported.
Do not tune specifically to remove the AA result and do not change hitter talent, WAR,
FV, or value from this component test.
