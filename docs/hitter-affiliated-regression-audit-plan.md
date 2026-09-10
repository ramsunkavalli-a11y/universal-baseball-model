# Hitter affiliated component regression audit plan

Status: frozen before scoring.

## Question

Does the current 1,200-PA population prior trust translated affiliated hitter
components too much or too little when forecasting a player's first later MLB sample?

## Method

Use the existing translated seven-component profile: UBB, HBP, 1B, 2B, 3B, HR,
and other. Compare fixed regression exposures of 400, 800, 1,200, 1,600, 2,400,
and 3,600 PA. Translation offsets, three-season recency, level evidence multipliers,
player population, target, and component definitions remain identical.

- Development: forecast 2024 MLB from evidence through 2023.
- Confirmation: forecast 2025 MLB from evidence through 2024.
- Population: hitters with prior affiliated PA, no prior MLB PA, and positive target-
  year MLB PA. Non-arrivals are not silently scored as component outcomes.
- Select the lowest 2024 log loss among candidates that also improve 2024 Brier
  versus 1,200 PA. Break ties toward 1,200 PA.
- Promote only if the frozen selection improves both 2025 point scores and both
  player-bootstrap 95% upper bounds are at or below zero.

Report target exposure, calibration, and player-cluster uncertainty. No demographic,
physical, position, organization, contract, player name, outside FV, or 2026 outcome
may enter selection. A failed challenger leaves current projections unchanged.
