# Injury-return out-of-time result

**Status:** broad IL type and elapsed-time hierarchy validated; no new production
change required.

The existing injury-return model was fit only on official 2022–2023 transactions and
then applied unchanged to 2024–2025. It uses injured-list type and days already spent
on the list. Each small cell shrinks toward the population mean. Diagnosis, age,
recurrence, team depth and future information are not used.

## Pooled 2024–2025 result

| Measure | Population mean | IL type + elapsed time | Better |
|---|---:|---:|---|
| Return Brier | 0.1767 | 0.1596 | detailed cells |
| Return log loss | 0.5390 | 0.4894 | detailed cells |
| Availability MAE | 0.1940 | 0.1854 | detailed cells |
| Availability RMSE | 0.2657 | 0.2567 | detailed cells |

The detailed model wins all four measures in both 2024 and 2025. It also closely
matches the pooled observed return rate: **22.65% predicted** versus **22.81%
observed**. All 548 validation players received a supported cell.

## Decision

Keep this hierarchy as the injury workload baseline. The next candidate may add age
and prior IL recurrence, using immutable birth dates and only transactions known by
the forecast cutoff. It must beat this model, not the weaker population mean. Injury
diagnosis should wait until its source coverage and categories can be made consistent.

[Machine-readable result](injury-return-out-of-time-result.json)
