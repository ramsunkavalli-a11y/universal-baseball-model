# Current Talent development-grid selection checkpoint

Status: **selected from the predeclared 2021–2022 grid; 2023 alternative-grid configurations have not been inspected.**

Selection plan: `docs/current-talent-baseline-selection-plan.md`.

## Preselected primary candidate

- Candidate: `hl180_ps100_fitted`
- Recency half-life: **180 days**
- EB prior strength: **100 effective core events**
- Translation variant: **`fitted_translation`**
- 2021–2022 equal-fold mean log loss: **2.255543**
- 2021–2022 equal-fold mean Brier: **0.869233**
- Mean B1−B0 log-loss delta: **-0.017598**
- Mean B1−B0 Brier delta: **-0.004643**
- B1 log-loss fold wins vs B0: **6/6**
- B1 Brier fold wins vs B0: **6/6**

### Versus existing 90/100/fitted reference

- Reference: `hl90_ps100_fitted`
- Selected minus reference mean log loss: **-0.000262**
- Selected minus reference mean Brier: **-0.000133**

### Calibration guardrails on development folds

- Mean absolute intercept error: **0.565721**
- Mean absolute slope error: **0.206129**
- Mean fixed-bin ECE: **0.003174**

## Top five by the predeclared primary objective

| Rank | Candidate | Half-life | Prior | Translation | Mean log loss | Mean Brier | Pareto |
|---:|---|---:|---:|---|---:|---:|---|
| 1 | `hl180_ps100_fitted` | 180 | 100 | `fitted_translation` | 2.255543 | 0.869233 | yes |
| 2 | `hl90_ps100_fitted` | 90 | 100 | `fitted_translation` | 2.255806 | 0.869366 | no |
| 3 | `hl180_ps100_zero` | 180 | 100 | `zero_offset_translation` | 2.256025 | 0.869345 | no |
| 4 | `hl90_ps100_zero` | 90 | 100 | `zero_offset_translation` | 2.256266 | 0.869474 | no |
| 5 | `hl180_ps200_fitted` | 180 | 200 | `fitted_translation` | 2.256398 | 0.869705 | no |

## Confirmation boundary

The primary candidate above was selected using **only the six 2021–2022 development folds**. Do not replace it after inspecting 2023. The next gate may evaluate this one preselected candidate on 2023 and compare it with Baseline 0 and the existing 90/100/fitted reference configuration.

If 2023 confirmation fails, record hyperparameter instability; **do not reselect using 2023**.
