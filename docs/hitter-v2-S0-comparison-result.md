# Hitter v2 S0 comparison result

Date: 2026-08-25  
Status: failed final; no retuning

## Scientific outcome

S0 did not pass any disclosed fold and failed the pooled gate. The result is
final under the preregistration.

V2022 was predetermined to fail strict improvement because the no-origin rule
made S0 exactly equal to C0. It tied C0 on wOBA and runs/600 RMSE while losing
proper scores to Marcel.

The informative result is 2023-2024. Adding 12.5% Marcel improved terminal log
loss in both weighting views in both folds. However:

- In V2023, the blend worsened player-weighted Brier, wOBA RMSE, and runs/600
  RMSE. It did improve all four PA-weighted metrics, but that is insufficient
  under the predeclared both-view rule.
- In V2024, the blend worsened Brier, wOBA RMSE, and runs/600 RMSE in both
  views. Player-weighted wOBA RMSE increased by 0.000197 and runs/600 RMSE by
  0.099; PA-weighted wOBA RMSE increased by 0.000174 and runs/600 by 0.087.
- In the pooled comparison, only PA-weighted terminal log loss cleared its
  required relative-improvement threshold. The other seven primary
  metric/view cells failed.

The simple interpretation is that Marcel's extra shrinkage makes S0 slightly
less surprised by the full outcome distribution, but it washes out some of
C0's useful player-level signal for future offensive value. A global blend is
therefore not the needed improvement.

S0 also failed every calibration family in every fold. V2023 and V2024 had no
material supported-subgroup reversal, so the central problem is aggregate
performance rather than a single level or age group.

## Gate consequence

S0 cannot be retuned or rescued. Because the preregistered L0 level residual
required S0 to pass, L0 does not advance. The aging, contact-shape, and tracking
increments also remain closed. Protected 2026, Stage 3, and WAR remain closed.

Further model fitting requires a distinct preregistered candidate informed by
this failure. The corrected generated report SHA-256 is
`99af58cbbccea1f5a552100e73ed01d1b835cfdc0c4c605bad6492f6ebf37446`.

Validation completed with all 1,003 repository tests passing and canonical
lint passing across `src`, `scripts`, and `tests`.
