# Prospect post-arrival pitcher-role plan

Status: frozen before scoring.

## Question

For pitchers who have reached MLB, do prior-season starter/reliever usage details improve
the next career-state advancement forecast beyond age, elapsed time and total batters
faced?

## Frozen method

- Reuse the cutoff-safe annual post-arrival rows and all exclusions from the workload
  test.
- Use only official prior-season MLB batters faced, games and games started.
- Challenger adds start share (`starts / games`) and batters faced per game, scaled by
  25. These describe role without labels or outside opinions.
- Compare directly with the accepted age, elapsed-time and prior-workload model.
- Select regularization from `0.03, 0.1, 0.3, 1.0` on the 2023 outcome, then score
  2024 and 2025 unchanged.
- Report log loss, Brier score and deterministic player-paired 95% bootstrap intervals.

The role candidate passes a state only if both 2023 point scores improve and both
later years have upper paired bounds below zero for both proper scores. Current 2026
data, organization, future workload and outside FV are excluded. A pass changes only
the design of a future linked simulator, not current player values.
