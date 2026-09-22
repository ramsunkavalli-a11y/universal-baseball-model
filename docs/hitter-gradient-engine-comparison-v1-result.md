# Hitter gradient engine comparison

Status: **complete; retain scikit-learn histogram gradient boosting**

## Plain-language conclusion

XGBoost and LightGBM were tested against the existing scikit-learn histogram
gradient booster using the same 155 inputs, the same residual targets, the same
player weights, and the same chronological outer folds. All three beat the
contact-only projection overall. Scikit-learn remained the best complete result.

| Engine | RMSE | Change vs contact-only | Log loss | Brier |
|---|---:|---:|---:|---:|
| Contact-only | 0.014597 | — | 1.253127 | 0.001888 |
| scikit-learn histogram GB | **0.014318** | **-0.000279** | **1.252908** | **0.001843** |
| LightGBM | 0.014330 | -0.000267 | 1.252984 | 0.001847 |
| XGBoost | 0.014361 | -0.000236 | 1.253004 | 0.001851 |

The scikit-learn model reduced RMSE by 1.91% versus contact-only. LightGBM reduced
it by 1.83%, and XGBoost by 1.62%.

## Direct engine comparisons

Candidate-minus-scikit-learn values below zero would favor the candidate.

| Candidate | RMSE difference | Paired 95% interval | Log-loss difference | Brier difference |
|---|---:|---:|---:|---:|
| LightGBM | +0.000012 | [-0.000001, +0.000024] | +0.000076 | +0.000004 |
| XGBoost | +0.000043 | [+0.000021, +0.000065] | +0.000097 | +0.000009 |

LightGBM is effectively tied with scikit-learn on RMSE—the interval barely crosses
zero—but scikit-learn is clearly better on log loss and Brier. XGBoost is clearly
worse than scikit-learn on all three pooled measures in this experiment.

## How tuning was kept honest

Each engine received three predeclared configurations: compact, balanced, and
broad. For each outer forecast year, configuration selection used only earlier
chronological transitions. The 2022 fold had no earlier inner transition, so every
engine used its predeclared balanced default.

- Scikit-learn selected balanced in all three outer folds.
- XGBoost selected balanced for 2022 and compact for 2023-2024.
- LightGBM selected balanced for 2022 and compact for 2023-2024.

The comparison used 6,799 out-of-sample player forecasts. Paired uncertainty was
estimated by resampling 3,613 players as whole clusters 5,000 times.

## Decision

Keep scikit-learn histogram gradient boosting as the leading hitter engine. There
is no evidence that replacing it with XGBoost improves this projection problem.
LightGBM is a credible near-peer and useful future cross-check, but it does not beat
the current model across the complete scoring rule.

The frozen 2026 forecast was not refit, overwritten, or rescored. Its SHA-256 was
identical before and after this experiment:
`2766cde0e605e09e2c878d7e58a48cfb0c0b2bfb55b2347fb4ccfe428879e61b`.
