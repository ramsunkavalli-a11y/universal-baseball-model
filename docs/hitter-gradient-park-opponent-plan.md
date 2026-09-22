# Hitter gradient park/opponent plan

Status: **park/opponent component complete; first gradient projection test passed;
no 2026 outcomes accessed**

Data readiness was subsequently audited against the actual local artifacts. The
affiliated challenger has 1,851,325 terminal contact/result events over 2021-2024,
complete age coverage, venue coverage above 99.5% in every year, and 9,157 frozen
next-season benchmark rows. See `hitter-gradient-data-readiness.md`. The first fixed
gradient tree improved all three pooled measures. The next step
is feature materialization, not additional source collection.

## Plain-language purpose

We need to answer two different questions in order:

1. Given the same kind of contact and matchup, how did the park change the chance
   of a single, double, triple, homer, reach-on-error, or out?
2. Once those park and opponent effects are removed, do the resulting player
   skills predict the following season better than the current hitter model?

The old player test mostly judged the second question. A bad forecast integration
could therefore reject a real park effect. The new design gives park measurement
its own validation gate before it is allowed into a player projection.

## What the literature says

- MLB's public Statcast park factors compare a player's outcomes in a park with
  the same player's outcomes elsewhere and split by batter handedness. That
  supports controlling personnel and handedness rather than treating raw home
  results as park talent.
- Jonathan Judge's Baseball Prospectus park work treats park effects as latent
  inside batter and pitcher performance and estimates them simultaneously. Its
  component models separate singles, doubles, triples, and homers; include a
  park-by-batter-side effect; and avoid repeated home/road correction passes.
- Baseball Prospectus DRC/DRA use event-level mixed models to separate batter,
  pitcher, park, platoon, and other context. The lesson for UBM is the separation
  of causes, not the use of proprietary inputs.
- FanGraphs publishes multi-year, regressed park factors and component,
  batted-ball, and handedness splits. That supports shrinkage and component
  factors instead of one all-purpose run factor.
- Recent personnel-adjusted research likewise models who batted, who pitched,
  handedness, and uncertainty. Pairwise-comparison research shows that park can
  be estimated from plate appearances while accounting for batter-team and
  pitcher-team strength.

We will borrow that structure but not Statcast measurements. UBM's universal
inputs remain official outcome, Gameday trajectory, spray direction, batter side,
pitcher hand, venue, level/league, and strictly prior opponent evidence.

## What Eephus publicly shows

Eephus describes a veteran LightGBM forecast stacked against a Marcel-style
baseline, with rolling history, aging, and uncertainty heads. It reports that an
added Statcast feature group did not improve its held-out forecast and was
rejected. Its public source page names FanGraphs as the source for park factors.

The public material does **not** expose an event-level Eephus park or opponent
estimator. The defensible comparison is therefore: Eephus appears to consume an
upstream park adjustment in a gradient forecast, while UBM is building and
validating its own event-level neutralization because minor-league parks and
level changes are central to this project.

## Required event grain

One row per terminal plate appearance, joined exactly to:

- outcome: UBB, IBB, HBP, K, HR, 3B, 2B, 1B, ROE, FC reach, SF,
  multi-out, other out, or special;
- terminal contact shape when applicable: IFFB, or pull/center/opposite crossed
  with OFFB, LD, or GB;
- venue and venue era;
- batter side, pitcher hand, and their platoon cell;
- batter and pitcher identifiers for grouping, but strictly prior skill summaries
  rather than unrestricted identity memorization in the forecast;
- league, level, date, and reliability counts.

Weather and defensive quality are later additions only if their historical
coverage passes a source audit. Inning, score, lineup slot, and similar game-state
variables may explain an observed event, but must not become projected player
talent unless we can also forecast that future context.

## Two-stage model

### A. Context and neutralization model

Estimate terminal results conditional on contact type/direction, venue,
batter side, pitcher hand, platoon, league/level, and strictly prior batter and
pitcher component strength. Venue-by-batter-side and venue-by-contact-shape are
the central effects. Produce a counterfactual probability vector for the same
event in a neutral venue against a neutral opponent.

Start with a regularized statistical baseline, then compare LightGBM and XGBoost
using the identical rows and folds. A tree is not allowed to substitute raw IDs,
future-season aggregates, or target-season opponent results for real information.

### B. Player forecast model

Aggregate the neutral probability vectors into player-season component rates,
keeping denominators and reliability. Join age, prior workload, level transitions,
and the current structured hitter baseline. Fit the gradient model as a challenger
that predicts the residual over the current model, so it must demonstrate added
information rather than rebuild everything opaquely.

## Chronology and evaluation

- Development folds: train before 2022/test 2022, train before 2023/test 2023,
  train before 2024/test 2024. Exposed 2025 results are confirmation/development
  evidence, not a fresh final test. The 2026 season remains protected.
- Every opponent-strength value for an event uses games strictly before that
  event date. Same-day games are excluded from the prior.
- Every park estimate used at a forecast origin is fitted only from information
  available before that origin. New or sparse venues fall back toward the
  league-season-level mean.
- Player-grouped evaluation prevents one player's events from appearing as both
  the evidence and validation unit where the test is intended to measure
  generalization to players.

## Gates

1. **Park gate:** improve held-out event log loss/Brier and calibration over
   contact shape + handedness + league/level without venue; show stable component
   direction across years and sensible uncertainty.
2. **Neutralization gate:** remove the relationship between a player's supposedly
   neutral production and his past park exposure; improve away-park or park-mover
   prediction without erasing persistent contact skill.
3. **Projection gate:** improve next-season component and expected-WAR accuracy
   over the current hitter model, overall and in predeclared cohorts (level
   advancers, park movers, established players, and small samples). Report both
   player-weighted and opportunity-weighted scores.

Passing Gate 1 does not guarantee Gate 3. Failure at Gate 3 means revise or reject
the forecast integration, not claim that parks do not matter.

## Completed park/opponent checkpoint

`hitter_gradient_context.py` builds an exact PA-level table joining canonical
outcomes to official venue, handedness/platoon, and optional result-producing
contact bins. It rejects duplicate rows and rejects all-pitches contact data that
would incorrectly attach a foul contact to a later strikeout. Its chronological
split fails closed on 2026 input or evaluation.

The affiliated park estimator passed its separate future-season environment gate
in both 2024 and 2025. Its deterministic player neutralization did not pass the
future-player gate, so it is not allowed to replace current player projections.

The external audit found strong agreement with Baseball America across 119
minor-league parks and good agreement with FanGraphs across 29 MLB parks. The
systems need not have identical numbers: UBM adjusts personnel/opponent mix and
uses different pooling and time windows. See
`park-opponent-component-final-result.md` for the comparisons and decision.

`park_gradient_features.py` packages only a strictly prior factor vintage,
component effects, training support, reliability, and an explicit unknown-park
fallback. The gradient model may use these features, but must earn their weight
in the next-season projection test.

Next implementation: build strictly-prior batter/pitcher component summaries,
then fit the non-venue baseline versus venue-by-hand/contact challengers on the
frozen 2022-2024 folds. Park-adjusted and raw component histories remain separate
inputs so the learner can reject a harmful correction.

## Public references

- MLB Statcast Park Factors: https://baseballsavant.mlb.com/leaderboard/statcast-park-factors
- Baseball Prospectus, updated park factors: https://www.baseballprospectus.com/news/article/64534/an-updated-system-of-park-factors-and-volatility/
- Baseball Prospectus, DRC breakdown: https://www.baseballprospectus.com/news/article/48293/entirely-beyond-wowy-a-breakdown-of-drc/
- Baseball Prospectus, DRA: https://www.baseballprospectus.com/news/article/26195/prospectus-feature-introducing-deserved-run-average-draand-all-its-friends/
- FanGraphs park-factor principles: https://library.fangraphs.com/principles/park-factors/
- Personnel-adjusted home-run park effects: https://arxiv.org/abs/2506.22350
- Pairwise comparison for player/park effects: https://arxiv.org/abs/2109.09287
- Eephus projections/accountability: https://eephus.io/projections/#view=accountability
- Eephus data sources: https://eephus.io/sources/
