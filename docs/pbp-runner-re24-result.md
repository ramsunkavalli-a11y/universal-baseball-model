# Minor-league runner RE24 result

Date: 2026-09-22
Status: **advance to hitter-value integration**

## What changed

The first minor-league runner model scored an advancement as a simple count of extra
bases. That was useful for detecting signal but was not a baseball run value. This
test replaces it with RE24: the change in expected runs caused by the focal runner's
actual destination compared with the ordinary destination for that play.

The run-expectancy table is estimated separately by season and level from 7,034,246
terminal plays. The counterfactual keeps the batter and every other runner in the
observed post-play state, so the hitter does not receive the runner's credit and the
runner does not receive the hitter's credit. A runner who scores gets the immediate
run plus the change in the remaining base/out state; a runner thrown out is charged
for the added out and lost base state.

Expected advancement still adjusts for level, park, play type, location, outs,
batter side, and pitcher hand. Runner and outfielder effects are separated. Every
forecast uses only earlier player seasons, and the regression strength for a scored
season is selected only from older folds.

## Result

- Clean RE24-valued opportunities: 851,430
- Later player-season tests: 13,628
- Neutral RMSE: 0.02557 runs per opportunity
- Projected-runner RMSE: **0.02413**
- Improvement: 0.00145 runs per opportunity
- Prediction/actual correlation: 0.324
- Player-clustered 95% interval for the RMSE change: **-0.00164 to -0.00126**

The whole uncertainty interval favors the runner model. The selected history
regression is heavy—200 or 400 weighted opportunities—so the result still argues for
strong shrinkage, not noisy one-season leaderboards.

## Decision

The minor-league non-steal runner component now has a real run-value target and passes
chronological validation. Advance it to the hitter-value stack. The next test should
combine this prior minor-league runner evidence with the existing MLB Savant
advancement model, forecast the player's next-season advancement opportunities from
expected playing time, and score the addition on total hitter value. Do not change the
frozen 2026 forecast until that full-stack test passes.
