# Minor-league catcher steal deterrence result

Date: 2026-09-22
Status: **reject current form**

## Question

The earlier catcher throwing model measured caught-stealing success only after a
runner tried. Can we identify catchers who prevent attempts in the first place?

## Test

Every plate appearance beginning with an open base ahead of a runner was treated as a
steal opportunity. The observed attempt rate was adjusted for destination base,
pitcher and batter handedness, outs, inning, score, available pitch window, level, and
park. A crossed model then separated catcher, pitcher, and runner effects. Prior
catcher effects were projected into later seasons with regression chosen only from
older folds.

- Terminal plays: 6,997,269
- Steal-eligible PA starts: 2,782,534
- Observed attempts: 36,367
- Attempt rate: 1.31%
- Catcher seasons: 6,835
- Later catcher-season tests: 3,130

## Result

- Neutral RMSE: **0.002531** attempt-rate residual
- Projected deterrence RMSE: 0.002539
- RMSE change: **+0.000007** (worse)
- Prediction/actual correlation: 0.046
- Player-clustered 95% interval: about -0.000005 to +0.000019

The chronology-safe selector chose the largest available regression—20,000
opportunities—in every fold. Less regression was clearly worse. In plain language,
the apparent catcher differences needed to be shrunk almost completely to zero and
still did not beat a neutral forecast.

## Decision

Do not add a minor-league catcher deterrence value. Keep the existing throwing model
limited to success after an attempt, and keep its modest evidence label. A stronger
deterrence test would need true pitch-by-pitch runner state, leads or jumps, and more
complete identification of all attempts; the current all-level PA-start denominator
is useful but not predictive enough.
