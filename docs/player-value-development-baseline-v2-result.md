# Player-value development baseline v2

Date: 2026-09-22

## Decision

Use the first reconciled hitter-plus-pitcher development baseline for continued model
building. It combines the accepted hitter partial-value stack with the role-enhanced
pitcher ensemble at one row per player and season. It is not the final complete-WAR
model, and it does not open the protected 2026 outcome season.

The reconciled point forecast improves RMSE from **0.39874** for the component-neutral
comparison to **0.38807**. The change is **-0.01067 WAR RMSE**, with a player-clustered
95% interval from **-0.01703 to -0.00455**. The improvement is present in every scored
season (2023, 2024, and 2025 outcomes from 2022-2024 forecast origins).

## What is in the baseline

The hitter side contains:

- the five-model batting and replacement-value ensemble;
- the separately selected MLB arrival and plate-appearance forecast;
- projected position value;
- projected baserunning value; and
- the provisional, conservatively shrunk public catcher-defense estimate.

The pitcher side contains:

- the chronology-pruned multi-model expected-value ensemble;
- explicit starter/reliever, workload-disruption, level-movement, and prior-MLB
  features in Ridge, CatBoost, and LightGBM;
- the ensemble probability of reaching or returning to MLB;
- the ensemble value estimate conditional on pitching in MLB; and
- stage-and-role-calibrated value ranges.

For players present in both populations, the hitter and pitcher forecasts are added.
They are not forced into one role. This matters for genuine two-way players and avoids
silently discarding a small projected contribution from either side.

## Reconciliation result

Across 25,671 player-season rows and 12,418 players:

| Forecast | RMSE | MAE | Bias |
|---|---:|---:|---:|
| Selected hitter stack + role-enhanced pitcher | 0.38807 | 0.12061 | +0.00015 |
| Selected hitter stack + older pitcher ensemble | 0.38821 | 0.12055 | -0.00043 |
| Hitter batting/replacement only + role-enhanced pitcher | 0.39861 | 0.12431 | +0.00714 |
| Hitter batting/replacement only + older pitcher ensemble | 0.39874 | 0.12426 | +0.00657 |

The accepted hitter additions account for nearly all of the combined gain: **-0.01054
RMSE**, with a 95% interval from **-0.01685 to -0.00438**. The pitcher role upgrade
remains directionally favorable at **-0.00014 RMSE**, but its interval of **-0.00040 to
+0.00011** still includes no change. It stays selected because it improves the broader
six-fold pitcher development result and has a coherent baseball mechanism, not because
this shorter three-fold reconciliation independently proves it.

## Uncertainty

Literal chronological 50/80/90% residual ranges under-covered the combined target,
especially after separating MLB players from minor leaguers. The selected development
ranges therefore use fixed 55/85/93% residual quantiles and display them as conservative
50/80/90% bands. This choice was made on exposed development seasons and is now frozen
for the protected test.

| Displayed range | Combined coverage | 2024 outcome | 2025 outcome |
|---|---:|---:|---:|
| 50% | 49.7% | 52.3% | 47.0% |
| 80% | 81.0% | 82.0% | 80.0% |
| 90% | 91.1% | 91.9% | 90.2% |

Calibration uses only residuals from forecast origins earlier than the row being
scored. It separates hitter-only and pitcher-only players by current MLB, upper-minors,
or lower-minors status, and treats players with both histories as their own group.

## Artifacts

The builder scripts are:

- `scripts/assemble_pitcher_value_development_baseline_v2.py`
- `scripts/reconcile_player_value_development_baseline_v2.py`

They create ignored, reproducible artifacts under:

- `reports/generated/pitcher-value-development-baseline-v2/`
- `reports/generated/player-value-development-baseline-v2/`

The pitcher role-ensemble artifact now also carries the arrival and conditional-value
ensemble outputs that correspond to the selected total-value forecast. This makes the
forecast decomposable instead of exposing only its final product.

## What is still missing

This is still partial value, not complete WAR. General non-catcher defense remains
neutral. Pitcher value is defense-independent and treats non-home-run contact at
league-average value. Team plate-appearance and innings constraints are not applied.
The pitcher forecast does not yet expose a separately calibrated batters-faced total.

The next reconciliation milestone is team and role capacity: test whether constraining
individual opportunity forecasts to realistic team plate appearances, innings, starts,
and relief roles improves player-level future value without changing portable talent.

