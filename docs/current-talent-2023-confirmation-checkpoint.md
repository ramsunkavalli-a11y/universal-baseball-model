# Current Talent 2023 confirmation checkpoint

Status: **CONFIRMED under the predeclared selection plan.**

This gate evaluates only the candidate preselected from the 2021–2022 development grid, plus the existing 90/100/fitted reference. The 18-candidate alternative grid was **not** evaluated on 2023.

## Preselected candidate

- Candidate: `hl180_ps100_fitted`
- Half-life: **180 days**
- Prior strength: **100 effective core events**
- Translation: **`fitted_translation`**

## 2023 confirmation folds

| Cutoff | B1 log loss | B1 Brier | B1−B0 LL | B1−B0 Brier |
|---|---:|---:|---:|---:|
| 2023-07-15 | 2.254303 | 0.870022 | -0.017363 | -0.004462 |
| 2023-08-01 | 2.250926 | 0.869251 | -0.018280 | -0.004719 |
| 2023-09-01 | 2.251711 | 0.869687 | -0.020797 | -0.005152 |

## Three-fold summary

- Mean B1 log loss: **2.252313**
- Mean B1 Brier: **0.869653**
- Mean B1−B0 log loss: **-0.018814**
- Mean B1−B0 Brier: **-0.004777**
- B1 log-loss wins vs B0: **3/3**
- B1 Brier wins vs B0: **3/3**
- Selected minus reference mean log loss: **-0.000245**
- Selected minus reference mean Brier: **-0.000105**
- Mean abs calibration-intercept error: **0.522317**
- Mean abs calibration-slope error: **0.190657**
- Mean fixed-bin ECE: **0.002615**

## Breadth vs Baseline 0

- Component log-loss wins: **36/36**
- Component Brier wins: **35/36**
- Stratum log-loss wins: **62/62**
- Stratum Brier wins: **62/62**

## Decision boundary

The preselected candidate passes the proper-score confirmation rule: it remains better than its B0 comparator and does not reverse the development-grid log-loss advantage versus the fixed reference.

This is sufficient to move to an explicit **simple-baseline freeze decision** using the already predeclared guardrails. It does not by itself authorize richer inputs or Projection.
