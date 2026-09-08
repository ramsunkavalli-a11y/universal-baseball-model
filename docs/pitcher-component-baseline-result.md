# Pitcher component baseline result

Completed 2026-09-07 on the frozen 2015–2024 MLB pitching outcome inventory.

## Method

The transparent baseline uses three prior seasons with 3/2/1 recency weights,
regresses K, unintentional walk, HBP, HR and other-BF rates toward role-specific MLB
populations with a fixed 200-BF prior, and estimates starter share separately with a
fixed 20-game prior. Players without usable history receive the global population
prior and zero reliability. No target-season membership, role or workload is used as
a predictor.

## Rolling-origin result

On target pitchers with positive BF, every 2018–2024 fold beat the global-population
comparator on BF-weighted component log loss.

| Target season | Log-loss improvement vs global |
|---:|---:|
| 2018 | 0.004813 |
| 2019 | 0.005632 |
| 2020 | 0.005507 |
| 2021 | 0.004663 |
| 2022 | 0.004378 |
| 2023 | 0.003605 |
| 2024 | 0.003352 |

Equal-fold mean log loss is `0.9804403` for the component baseline versus
`0.9850046` for the global comparator. Between 155 and 222 scored pitchers per fold
had no prior three-year BF and therefore received the declared fallback.

Prediction hash:
`7201459f5f614c3ffa74d4498de245fa870ef22ced8a7b3abe10adb602ab02ad`.

## Decision and boundary

Adopt this as the Phase 1 pitcher-rate competence baseline. It is intentionally not a
pitcher production model: arrival, participation, workload, role transitions, aging,
run conversion, WAR and value remain separate work. Target-season membership is used
only to define the historical scoring cohort.

Reproduction: `python scripts/score_pitcher_component_baseline.py` after materializing
the career MLB outcome inventory.
