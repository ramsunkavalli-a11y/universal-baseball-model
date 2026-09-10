# Joint pitcher aging and opportunity replay — 2025

**Status:** Tango aging supported; no production change  
**Population:** All 5,090 pitcher rows in the frozen March 27, 2025 forecast

## Test

The frozen opportunity, workload, role, replacement and run-environment inputs were
held constant. The incumbent uses Tango's regressed adjacent-pitching aging. The only
counterfactual removed that one-year rate adjustment. Both versions were scored on
the same zero-inclusive player universe; all pitchers who produced no 2025 MLB BF
remained in the WAR score.

| Result | Tango aging | No aging |
|---|---:|---:|
| Component log loss | 0.967163 | 0.967542 |
| Predicted pitcher WAR | 418.0 | 437.1 |
| Observed neutral pitcher WAR | 383.1 | 383.1 |
| Zero-inclusive WAR MAE | 0.10550 | 0.10653 |
| Zero-inclusive WAR RMSE | 0.30822 | 0.30973 |

Tango aging lowered the forecast by 19.0 WAR, moved it closer to the observed total,
and improved every point metric. The paired player bootstrap places the no-aging
minus-Tango MAE difference between 0.00058 and 0.00151 WAR, entirely above zero. The
MSE interval crosses zero, so the RMSE evidence is positive but not decisive.

## Decision

Retain Tango pitcher aging. This is the first direct evidence that its conditional
rate adjustment also helps after the separate opportunity model is applied and
non-returners are retained. It does not justify a new curve or any player-value
change: 2025 was already disclosed and the no-aging comparison was constructed after
that disclosure.

The next aging challenger must be frozen before another target is opened and must
beat Tango on both conditional component accuracy and this zero-inclusive production
score. Outside FV and 2026 outcomes were not used.

Machine-readable detail: `docs/joint-pitcher-aging-2025-result.json`.
