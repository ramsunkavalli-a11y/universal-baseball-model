# Catcher battery-support v1

Last updated: 2026-09-21
Status: **DEVELOPMENT SIGNAL FOUND FOR WALKS; NOT PROMOTED TO CATCHER WAR**

## Baseball question

Can broadly available affiliated play-by-play show that a catcher helps pitchers
avoid walks or otherwise improve defense-independent results, without requiring
pitch tracking, intended glove location, or pitch-type classification?

The honest name for the quantity is **battery support**. The public feed does not
identify whether a pitch was selected by the catcher, pitcher, coach, or dugout,
and it does not record the catcher's intended target.

## Prior work reviewed

- Keith Woolner's original pitcher-with/without-catcher tests found that ordinary
  catcher ERA differences looked much like random variation. This established the
  need for matched pitchers and an explicit neutral benchmark:
  https://www.baseballprospectus.com/news/article/432/field-general-or-backstop-evaluating-the-catchers-influence-on-pitcher-performance/
- The later Hardball Times matched-inning/DIPS study found possible repeatable
  differences, but regressed catcher estimates with 16,300 average plate
  appearances--more than three full seasons of catcher work--and warned that the
  statistic was much less reliable than batting value:
  https://tht.fangraphs.com/classic-tht-annual/do-catchers-have-an-era/
- Baseball Prospectus' later framing and errant-pitch work showed the right modern
  structure: crossed or mixed effects for all participants, shrinkage, and
  out-of-sample reliability rather than raw with/without splits:
  https://www.baseballprospectus.com/news/article/25514/moving-beyond-wowy-a-mixed-approach-to-measuring-catcher-framing/
  https://www.baseballprospectus.com/news/article/27849/prospectus-feature-passed-balls-and-wild-pitches-getting-it-right/
- Max Marchi's staff-handling work reported a penalty for rookie catchers and
  catchers changing organizations, which makes familiarity a separate hypothesis
  from transferable catcher talent:
  https://www.baseballprospectus.com/news/article/16199/the-stats-go-marching-in-the-hidden-helpers-of-the-pitching-staff/
- Recent pitch-level work argues for potentially meaningful pitch-calling value,
  but uses MLB tracking information unavailable across the affiliated ladder:
  https://sabr.org/journal/article/hitter-and-catcher-adaptation-in-major-league-baseball/
- A causal NPB study makes the main identification limit explicit: observed pitch
  location is not the catcher's requested location. Direct strategy evaluation
  needs intended-target data, which the public all-level source does not contain:
  https://arxiv.org/abs/2208.03492

## UBM design

The screen uses 6,957,632 completed, non-intentional plate appearances from 2016-
2019 and 2021-2024. The levels are Rookie, short-season A, Single-A, High-A, Double-A,
and Triple-A. Catcher identity coverage is 99.9997%. The 2020 MiLB season did not
exist, and no 2026 outcome was accessed.

For each season the model estimates shrunken batter, pitcher, and catcher effects
after controlling for:

- level and season;
- pitcher and batter handedness;
- park-season context; and
- the identities of the opposing batter and pitcher.

Pitcher-catcher pair residuals are estimated separately after the participant main
effects. This prevents a recurring personal-battery relationship from automatically
becoming general catcher talent.

Prior catcher effects are projected into later seasons with a regression amount
selected only from earlier evaluation seasons. Every selected fold chose the maximum
tested 16,000-PA regression. That is substantive evidence that the useful signal is
small and must be shrunk extremely heavily.

## Results

| Target | Catcher tests | Correlation | RMSE change vs neutral | Player-clustered 95% interval |
|---|---:|---:|---:|---:|
| Walk or HBP | 3,327 | 0.2683 | -0.00016063 | [-0.00022107, -0.00010104] |
| Unintentional walk | 3,327 | 0.2716 | -0.00015373 | [-0.00021215, -0.00009833] |
| Hit by pitch | 3,327 | 0.1251 | +0.00001128 | [+0.00000186, +0.00002023] |
| Defense-independent run value | 3,327 | 0.1731 | +0.00000325 | [-0.00001940, +0.00002634] |

Negative RMSE change is better. The combined control result is almost entirely a
walk result. Hit batters become worse, and the broader defense-independent outcome
does not improve.

The walk signal survives among catchers who advance a level:

- same level: -0.00019640 RMSE;
- advanced: -0.00011244 RMSE;
- moved down: +0.00004610 RMSE, only 123 tests.

However, the stricter new-pitcher test is not decisive. On 3,158 catcher-seasons
restricted to the first observed season of each pitcher-catcher pair, the walk RMSE
change is -0.00002180 with a 95% interval of [-0.00007170, +0.00002462]. Repeat-pair
walk chemistry does predict modestly better than neutral (-0.00006232 RMSE;
correlation 0.1826).

## Decision

Do **not** add a general game-calling or command-support value to catcher WAR.

The evidence supports a small, heavily regressed, catcher-associated walk signal and
a repeat-battery signal. It does not yet show that a catcher carries a general skill
to new pitchers, and walk results can include framing because a human called-strike
changes whether a plate appearance becomes a walk. The absence of HBP and broad
run-value improvement argues against interpreting this as proven target-setting or
pitcher-command coaching.

Retain the output as development evidence for two possible future uses:

1. a battery-continuity feature in pitcher projections when the future catcher is
   actually known; and
2. a catcher challenger only if a later model isolates true pitch location or wins a
   whole-player forward projection test.

The reproducible report and player-season estimates are under
`reports/generated/catcher-battery-support-v1/`.
