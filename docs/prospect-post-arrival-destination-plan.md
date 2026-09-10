# Post-arrival advancement destination plan

**Frozen before first score:** 2026-09-10

## Question

The validated post-arrival equation predicts whether a fringe MLB player advances,
but an advancing player may move to meaningful or directly to established. Choose a
simple destination rule without changing the separately modeled advancement chance.

## Test

- Use the same cutoff-safe annual transition rows as the workload test.
- Exclude the shortened 2020 outcome and all current 2026 data.
- Keep only observed advances from `FRINGE_MLB`.
- Compare a Jeffreys-smoothed pooled probability of direct established advancement
  with separate hitter and pitcher probabilities.
- Fit through 2022 and select on 2023. For 2024 and 2025, refit only on prior years
  and score the next year.
- Score identical players with log loss and Brier score.

Use the player-type split only if it improves both scores in 2023 and in each later
year. Otherwise retain the pooled destination probability. This test cannot alter the
chance of advancement, current WAR, FV or rankings. A destination rule that passes is
only an input to the still-required linked historical simulator replay.
