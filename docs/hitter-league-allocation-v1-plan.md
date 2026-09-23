# Bounded Year-2 league allocation screen

Frozen before new scoring, 2026-09-22. One candidate; no parameter search.

Question: can a cutoff-safe league opportunity budget improve individual PA and
batting-plus-replacement value, with participation and batting ability unchanged?
This is not a team-job model, full WAR reconciliation, or health inference.

## Data and chronology

Reuse the exact accepted-v2 Year-2 PA rows and independently estimated performance
anchors from the saved opportunity/calendar audit. Earlier origins 2016/2017
provide calibration only after their target years are complete. Score origins
2018, 2019, 2021, 2022, retaining every player and zero-play outcome. Ordinary
targets 2023/2024 are primary; target 2020 and pandemic bridge 2021 are separate
stress tests. Exclude pandemic-crossing origins from calibration; never use
future realized schedule length to set forecast exposure. No 2026 outcomes.

## One fixed candidate

- Group by cutoff stage and accepted predicted PA bands [0,50), [50,200),
  [200,400), [400,infinity). These are opportunity groups, not talent labels.
- For each group, estimate actual/predicted total PA using only archived forecasts
  whose target year is <= the new origin. Shrink toward 1 using 100 pseudo-players
  at the group's mean predicted PA; clip multipliers to [0.5,2]. Missing groups
  get 1. No individual residual memorization or hand adjustment for stars/youth.
- Expected full-league pool: median of the latest three completed non-2020
  season PA totals normalized by certified schedule fractions, known at cutoff.
- Reserve: median outside-cohort PA fraction in the latest five mature Year-2
  cohorts from the same panel definition, excluding pandemic-crossing windows.
  Estimate only from historical target seasons already completed at cutoff.
- Allocate the remaining pool proportionally to corrected PA, capped at the
  unchanged participation probability times 800 conditional PA. If capacity is
  insufficient, leave explicit slack. Keep all probabilities and batting rates
  fixed. Score unmodified accepted PA and uniform-budget scaling as benchmarks;
  uniform scaling is a diagnostic, not an alternate candidate to select.

## Evaluation and decision

Report equal-origin PA RMSE/MAE/bias, fixed-anchor partial-value RMSE, and the
separately delivered direct-value benchmark. Report stages, current-MLB ages,
predefined Year-1 top 50 and under-26 top 50 without changing membership. Show
paired player-cluster MSE intervals (1,000 draws, existing fixed seed), per-origin
results, allocation ledgers, group calibration support, and outside-reserve error.
Intervals condition on the observed years; they do not estimate new-year shocks.

Promotion would require lower PA and fixed-rate value MSE with paired 95% upper
bounds below zero, majority-origin gains, no ordinary top-50/young-top-50 worsening,
and at least three ordinary evaluation origins. Only two are currently available,
so this screen cannot authorize delivery even if promising. Do not retune after
seeing results. Original 2026 freeze, delivered multi-year means and explorer stay
unchanged. Save reproducible artifacts, leakage/accounting tests, and a concise
result explaining whether a larger replay is justified.
