# Prospect stolen-base value audit

**Decision:** `withhold_steal_value`

The already-frozen portable steal model is applied to old prospect cohorts. Expected future MLB PA comes from chronology-safe comparables; actual future steal value is centered within each MLB season and translated with one fixed run environment.

| Target | Evidence | Steal RMSE vs neutral | Combined RMSE vs batting only | Pass |
|---:|---:|---:|---:|---:|
| 2008 | 3192/3192 | 0.0475 vs 0.0487 | 0.7833 vs 0.7842 | False |
| 2013 | 3183/3183 | 0.0370 vs 0.0382 | 0.8992 vs 0.9005 | False |
| 2018 | 3270/3270 | 0.0412 vs 0.0425 | 1.0348 vs 1.0351 | False |
| 2021 | 3244/3244 | 0.0712 vs 0.0737 | 0.9568 vs 0.9572 | True |

This covers stolen-base value only. Non-steal advancement remains unavailable in the broad history and is not inferred. MAE is reported but does not veto an expected-mean forecast.
