# Prospect development-state test plan

Status: frozen before scoring.

## Question

Do cutoff-safe development-path facts improve the next-season four-state prospect
forecast beyond the existing level/exposure model?

The four exclusive outcomes remain no MLB, fringe MLB, meaningful MLB and established
MLB. The added facts are fixed before the target season: recent level movement,
seasons since affiliated activity, total affiliated workload and active affiliated
seasons. Organization and outside FV are excluded.

## Frozen comparison

- Train initially on 2018, 2019 and 2021 snapshots.
- Select regularization from `0.03, 0.1, 0.3, 1.0` on the 2022 snapshot predicting
  2023.
- Refit cumulatively and score 2023-to-2024 and 2024-to-2025 without changing the
  selected regularization.
- Compare ordered binary level/exposure (baseline), ordered binary development path,
  joint multinomial level/exposure and joint multinomial development path.
- Use identical players and multiclass log loss and Brier score. Report deterministic
  player-paired 95% bootstrap intervals for every challenger-minus-baseline result.

A challenger passes only if its development point scores improve and the upper bound
of both paired intervals is below zero in both later seasons, for the same player
type. Hitter and pitcher decisions remain separate. The shortened 2020 snapshot and
all 2026 outcomes are excluded. Passing would authorize a future confirmation
candidate, not a current value change, because these later cohorts have already been
inspected by related models.

