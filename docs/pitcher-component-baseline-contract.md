# Pitcher component baseline v0.1

**Status:** Implemented and scored on rolling 2018–2024 development folds
**Roadmap step:** Phase 1, Steps 3 and 6

## Form

- Forecast the next-season BF composition as `K / UBB / HBP / HR / OTHER_BF`.
- Use the prior three seasons with fixed 3/2/1 recency weights.
- Regress the composition toward the population for the player's projected broad role.
- Use an explicit 200 weighted-BF prior and report
  `weighted_history_bf / (weighted_history_bf + 200)` as reliability.
- Regress starter share separately using a 20-game prior, then classify the broad
  starter/reliever role for the component prior.
- Give no-history players the global component prior with zero reliability.

The 200 BF and 20 game values establish a transparent baseline; they are not claimed as
selected optima. Development scoring may replace them only through a predeclared small
sensitivity, not an open search.

## Boundaries

This baseline forecasts pitcher rate skill. It does not forecast whether the player
reaches MLB, games, batters faced, injury, role transitions beyond the broad prior, WAR
or value. Those layers remain separate so future-playing-time selection cannot leak
into rate predictors. It uses no hitter aging adjustment.

Initial scoring should use rolling-origin completed seasons, retain nonparticipants in
the opportunity denominator, and score component log loss only where BF is observed.
Report starters, relievers, sparse-history pitchers and role changers separately. The
protected 2026 surface remains closed.
