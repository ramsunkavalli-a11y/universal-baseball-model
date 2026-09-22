# Hitter contact neutralization v2 result

## Plain-language result

Park adjustment matters when judging an individual batted ball. It does not,
by itself, make the hitter's following-year value projection better. The useful
forecast signal in this experiment is the hitter's mix of pulled, centered, and
opposite-field ground balls, line drives, outfield flies, and popups—not the
detailed residual between the observed result and its park-adjusted expectation.

## What was built

- 4,522,737 eligible batted balls from 2016-2019 and 2021-2024.
- Ten contact-shape bins: pull/center/opposite crossed with ground ball, line
  drive, and outfield fly ball, plus infield fly balls.
- Nine results: single, double, triple, home run, reached on error, fielder's
  choice reach, sacrifice fly, multi-out, and other out.
- A player-held-out contact expectation using contact shape, spray, batter and
  pitcher handedness, level, inning, outs, bases, and score state.
- A player-held-out park correction estimated as a shrunk multiplicative change
  in outcome odds for venue × contact shape × batter side.
- Annual hitter features for contact shape and each observed-minus-expected
  contact/result cell, attached at lags 0, 1, and 2 to the existing value panel.

Every event for a hitter is assigned to the same cross-fit fold. The model that
scores the hitter therefore never trains on that hitter's outcomes. The missing
2020 minor-league season stays missing. No 2026 outcome is read.

## Why the method changed

Putting raw venue, pitcher, and defense identifiers directly into one gradient
model failed. Across all seasons, it worsened event log loss by 0.01976 and
Brier score by 0.00666 versus contact shape alone. The failure grew in the
lower-volume modern seasons, which is the signature of sparse categorical
overfit.

A probability-additive hierarchical correction improved Brier but worsened log
loss because it sometimes made rare outcomes implausibly unlikely. Recasting the
same idea as a shrunk multiplicative odds correction fixed that calibration
problem.

## Event-level result

The locked park correction improved both proper scoring rules in all eight
seasons. Pooled across the 4.52 million contacts:

- log loss improved by 0.001535;
- multiclass Brier score improved by 0.000893.

The park-only layer beat versions that also added defense-team and pitcher-ID
effects in both pilot seasons. Pitcher handedness remains in the physical-contact
expectation, but the additional sparse opponent identifiers were rejected.

## Following-year projection result

All variants used the same expanding chronological folds and LightGBM value
model. The target is next-season MLB component WAR.

| Variant | WAR RMSE | Change vs base | Arrival Brier change | Arrival log-loss change |
|---|---:|---:|---:|---:|
| Existing base | 0.439518 | — | — | — |
| Contact shape only | 0.439154 | -0.000364 | +0.000139 | +0.000218 |
| Park-neutral outcome residuals only | 0.439640 | +0.000122 | +0.000453 | +0.001339 |
| Shape plus park-neutral residuals | 0.439895 | +0.000377 | +0.000503 | +0.001424 |

Contact shape won four of six chronological folds. Its player-clustered 95%
interval for the RMSE change was -0.001612 to +0.000922, so the gain is small
and not yet decisive. The park-neutral residuals did not help next-year value
and worsened arrival scoring.

## Decision

1. Keep the park correction as the correct way to describe and audit contact
   outcomes, and as infrastructure for future component targets.
2. Do not add park-neutral outcome residuals to the current hitter value model.
3. Retain contact shape as a development challenger, not a promoted production
   feature, because its small WAR gain is not yet statistically secure and its
   arrival scores are slightly worse.
4. Do not modify the frozen 2026 forecast.

The main modeling lesson is that a variable can be essential for fair event
evaluation without its residual being stable hitter talent. Park tells us why a
ball became a hit; contact shape is the part that showed more repeatable value
for the next-year player forecast.
