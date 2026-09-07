# Model development result: a useful MLB-conditional component, not a ready model

Date: 2026-09-06. Website work is paused. Three candidates were tested in two
separately declared development batches. None passed full readiness. One yielded
a meaningful batting-ability signal worth retaining for the next model.

## What changed

G0 combines outcomes accumulated at different competition levels. T2026B first
estimates level effects using the same player's performances at two levels in the
same season, then adjusts historical evidence to an MLB reference before combining
it. It changes only strikeout, walk, home-run, and non-HR reach branches. Rare
conditional outcome relationships remain intact. G0's evidence weights and prior
strengths are reused without tuning.

There were 1,371, 2,177, and 2,936 supported same-season level pairs at the respective
2021, 2022, and 2023 predictor cutoffs. No later observations enter those fits.
Original G0 predictions were reproduced within 1e-12 before fitting each fold.

All six level-conditional forecasts were saved before current-year evaluation.
The primary prospective forecast mixed these using a transition model estimated
from earlier returning players. The conditional and prospective tasks are distinct.

## What improved

On players who subsequently recorded MLB PA, the presaved MLB-conditional forecast
improved PA-weighted wOBA RMSE in every disclosed year:

| MLB performance | G0 | Transport component | Improvement |
|---|---:|---:|---:|
| 2022 | .04530 | .03975 | 12.2% |
| 2023 | .04181 | .03604 | 13.8% |
| 2024 | .04817 | .03819 | 20.7% |

The gains were not just established MLB players. For players whose dominant level
in the preceding evidence season was in the minors:

| MLB performance | Players | G0 | Transport component |
|---|---:|---:|---:|
| 2022 | 302 | .06565 | .05011 |
| 2023 | 279 | .06195 | .04502 |
| 2024 | 279 | .07260 | .04702 |
| Pooled | 586 unique | .06671 | .04734 |

That is a 29.0% pooled error reduction. A paired bootstrap clustered by player
across years gives a 95% interval of [-.02122, -.01743] for the RMSE change.
The component also beats the frozen C0 and Marcel comparators in all three of
these prior-minor cohorts. The group includes players with earlier MLB experience;
it is not a pure debut or prospect sample.

A follow-up audit restricted to players without recorded MLB evidence in the
available 2019-onward history also shows improvement in each year: .06176→.05084,
.07050→.04887, and .08205→.05461. It contains 158/109/107 players respectively.
Absence from this history is not proof of no lifetime MLB experience.

## What did not improve enough

The prospective all-level mixture failed: pooled wOBA RMSE worsened 0.065%, with
a player-cluster uncertainty interval spanning zero. It also failed calibration
and worsened supported MLB-origin and AAA-origin groups. The conditional result
does not replace that failure or turn the candidate into a promoted forecast.

The two prior output-calibration candidates also failed. A global adjustment gave
only a 0.32% pooled gain; adding origin-level adjustments worsened error by 0.60%.
No candidate was tuned again after inspecting its result.

Even the useful MLB-conditional component is not calibrated well enough. For the
prior-minor cohort its PA-weighted calibration slopes were .666, .855, and .416;
mean bias was +.0128, +.0062, and +.0128. Equal-player mean biases were still larger.
The broad translation reduces an important error but does not yet reliably separate
the strength of individual hitters. That is the next batting-model problem.

## What this means for the KATOH goal

The next model should explicitly separate:

1. Batting ability conditional on MLB competition.
2. Probability of reaching or remaining in MLB and expected opportunities.
3. Development over the defined forecast horizon, then conversion to value.

The useful signal from this work belongs in the first component. It does not
establish the second or third. Continuing to judge all three through one blended
next-year, all-level rate can hide progress and reward the wrong compromises.

Next rate-model work should target calibration and differentiation among
minor-origin MLB performers, with age/evidence effects introduced separately and
evaluated chronologically. Preserve all tested comparators and do not tune to
individual player names. A separately specified evaluation/confirmation plan is
required before treating the MLB-conditional component as ready.

## Practical limits and validation

- These are disclosed 2022–2024 development years, not fresh confirmation.
- Conditional evaluation selects players who appeared in MLB. It cannot establish
  outcomes for non-arrivals or answer who reaches MLB.
- The original G0 comparison omits 863/813/671 target players without a forecast.
  Model coverage and no-history cases require explicit handling in a prospect system.
- Within-season movers are selected players; those contrasts are not randomized
  estimates of competition effects.
- No protected 2026 outcomes, website changes, or v1 output rewrites occurred.
- 1,045 tests passed against this checkout. New tests cover analytic gradients,
  chronology, probability conservation, rare-branch preservation, zero evidence,
  level aliases, and player-cluster resampling. Python lint passes.

Two T2026B executions stopped before any candidate forecast or score was written:
historical level aliases needed the existing canonical mapping, and zero-PA rows
needed to retain zero evidence. Both input-handling fixes preserve the declared
estimator, constants, and population; no result-driven tuning occurred.

Full numeric records are in `hitter-v2-C2026A-result.json`,
`hitter-v2-T2026B-result.json`, and `hitter-v2-MLB-transport-audit.json`. Presaved
probability surfaces are retained under `reports/generated/hitter-v2-C2026A/`
and `reports/generated/hitter-v2-T2026B/`. Earlier contracts and failures stand.
