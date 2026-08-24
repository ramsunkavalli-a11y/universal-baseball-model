# Hitter v2 Stage 2 pre-score checkpoint

Recorded: 2026-08-23  
Implementation commit: `16e25061018ab644aeccd9301c9c84b621f503fc`  
Candidate fit/scored: **no / no**  
Protected 2026 opened: **no**

The neutral evaluation environment and all three rolling-origin fold surfaces
are frozen before candidate implementation or scoring. One common pre-target
environment is used across the folds: the arithmetic mean of FanGraphs'
published 2016–2020 wOBA constants. The resulting neutral values are league
wOBA `0.3188`, scale `1.193`, and event weights UBB `0.6926`, HBP `0.7222`,
1B `0.8776`, 2B `1.2352`, 3B `1.5572`, HR `1.989`.

This choice predates V2022, V2023 and V2024. Target-year constants, run
environment, participant membership, playing time and level exposure cannot
alter predictors, priors, translations, centering or evaluation weights.

The exact fold surfaces are:

| Fold | Training cutoff | Training rows / players / PA | Target rows / players / PA |
|---|---:|---:|---:|
| V2022 | 2021 | 6,876 / 4,705 / 875,644 | 6,165 / 4,039 / 964,697 |
| V2023 | 2022 | 13,041 / 5,568 / 1,840,341 | 6,014 / 3,985 / 962,375 |
| V2024 | 2023 | 19,055 / 6,381 / 2,802,716 | 5,597 / 3,759 / 956,151 |

Training uses every accepted, positive-denominator historical row through the
cutoff. It is not restricted to players later observed in the target. Target
rows are kept at canonical player-league-season grain for level calibration and
also aggregated to one player for equal-player scoring. A direct mutation test
proves that changing target membership/outcomes leaves the training slice
unchanged.

The generated report is
`reports/generated/hitter-v2-stage2-prescore/report.json`, SHA-256
`0b47c0aa8654f84b78c457f77672c61e661f39149649e15b784b500ac0325c24`.
The committed machine record is `docs/hitter-v2-stage2-prescore-result.json`.

Full validation passed: Ruff and 837 tests. Candidate scoring remains closed
until B0, B1, C0 and C1 are implemented, their fixed search is persisted, and
the remaining candidate-specific invariants pass. Tracking and every later
hitter/WAR gate remain closed.
