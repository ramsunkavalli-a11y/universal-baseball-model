# Hitter ball-environment test

## Decision

Keep the park-, weather-, and opponent-adjusted ball-environment features as a
development challenger. They improved next-season hitter projections in the
pooled historical test, but they did not improve every season. This historical
test stops at 2024, so it does not contain the unusually lively 2026 MiLB ball.
The frozen 2026 forecast remains unchanged.

## What the test measures

The event model asks whether an air ball became a home run more or less often
than expected after accounting for:

- contact type and spray direction;
- batter and pitcher handedness;
- park identity and available fence dimensions;
- temperature, wind, humidity, and other available game conditions; and
- the batter's and pitcher's strictly prior air-contact home-run history.

The remaining common signal is estimated separately for each level and 14-day
period. Games used to estimate that signal are kept separate from games on
which it is applied. This prevents a player's own result, or another event in
the same game, from directly defining the adjustment attached to that event.

This is best called an **air-ball environment** estimate. It can contain a ball
effect, but it can also contain unmeasured conditions, data-source changes, or
other league-wide influences. It is not proof that the manufactured baseball
caused the residual.

## Event-level result

The test used 2,104,449 minor-league air contacts from 2016-2019 and 2021-2024.
Adding the dated level-wide environment lowered event log loss from 0.187383 to
0.186917 and Brier score from 0.051902 to 0.051824. Log loss improved in all
eight seasons and at every level. The smaller Brier result was slightly worse
at short-season A and rookie ball, while improving overall.

This says a dated common environment exists after the available contact, park,
weather, batter, and pitcher controls. It does not by itself say that the
environment helps forecast a player's future talent.

## Following-season projection result

The projection test used 17,552 player-seasons from 7,483 hitters. Every test
fold predicts the following season using only information available before
that season. The target is next-season hitting quality translated to the common
MLB scale, with at least 30 affiliated plate appearances. No 2026 results were
used.

| Added evidence | RMSE | Change from 0.035152 baseline | Interpretation |
| --- | ---: | ---: | --- |
| Coverage flags only | 0.035149 | -0.000004 | No meaningful gain |
| Raw air-contact HR results | 0.035179 | +0.000027 | Worse |
| Corrected results and environment | 0.034961 | -0.000191 | Clear pooled gain |
| Full set, including raw and corrected views | **0.034942** | **-0.000210** | Best result |

For the full set, the player-clustered 95% interval for the RMSE change is
-0.000251 to -0.000169. All four model families improved when given the full
feature set. This means the gain is not just a data-availability flag or one
model exploiting a peculiar encoding.

The full challenger improved four of six individual forecast seasons. It was
slightly worse in 2017 and more clearly worse in 2021; its largest improvement
was in 2023. The pooled result is therefore strong enough to retain, but not
stable enough to declare the feature family finished.

## Baseball interpretation

A hitter should not receive full credit for a home run hit during a temporary
high-carry period, and should not be penalized as much for an identical air ball
during a low-carry period. Raw air-ball home-run rate alone was harmful. The
useful information appeared only after separating the hitter from the setting
in which his air balls occurred.

The adjustment is historical evidence about the hitter, not an assumption that
the same ball will be used next season. The projection model sees both the raw
result and the corrected result and learns how much each has carried forward in
past chronological tests.

## The 2026 MiLB ball

The reported 2026 anomaly is directly relevant to this model because it is a
minor-league ball issue, not merely an MLB issue. Public reporting describes a
historic MiLB home-run increase, especially below Triple-A, where the leagues
use the machine-stitched MiLB baseball rather than the hand-stitched MLB ball.
The effect also appears uneven across hitter contact profiles.

The local historical test is well matched to that problem, but it stops at 2024
and deliberately excludes protected 2026 results. It therefore validates the
method without estimating the 2026 effect. Unless 2026 performance is
neutralized before it enters the next projection cycle, the model could
over-credit air-ball hitters for environmentally created home runs and
over-penalize fly-ball pitchers.

## Next gate

Before promoting this feature family into the production hitter model:

1. Preserve the frozen forecast and all predeclared 2026 evaluation rules until
   the season is formally unlocked.
2. Once unlocked, ingest 2025 and 2026 MiLB play-by-play and estimate the 2026
   environment separately for Triple-A, the full-season lower levels, and the
   complex leagues. Triple-A must not be pooled with levels using the different
   MiLB baseball.
3. Neutralize every hitter's and pitcher's 2026 air-contact results for the
   dated level environment, park, weather, opponent quality, contact type, and
   spray direction before using those results as 2027 talent evidence.
4. Measure whether the adjustment behaves differently for pull/fly-ball power
   hitters and fly-ball pitchers, while retaining the common chronological
   validation and shrinkage rules.
5. Separately assemble dated MLB history through 2025 so current major leaguers
   receive comparable treatment without mixing the two baseballs.

Until those gates pass, the correct status is **promising development input and
the intended correction for 2026 MiLB statistics, but not a frozen-forecast
override**.
