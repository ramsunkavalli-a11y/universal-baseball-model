# Context-neutral pitcher contact result

Date: 2026-09-22
Status: **retain as descriptive evidence; do not promote to pitcher value**

## Question

Raw singles, doubles, and triples allowed did not improve the pitcher model. Can we
recover pitcher-owned contact skill by judging each ball in play against similar
contact and then removing park, team defense, and batter effects?

## Test

The existing all-level play-by-play contact model was rebuilt from the pitcher's
point of view. Every event for a pitcher was held out together, so the model scoring
that pitcher never learned from his own outcomes. It estimated the expected result
from contact type and direction, level, handedness, inning, base/out state, and score,
then added separate strongly regressed adjustments for park, defense team, and batter.

The sample contains **4,522,737** eligible minor-league balls in play from 2016-2019
and 2021-2024. The missing 2020 minor-league season remains missing. Four fixed views
were tested: contact shape only, park-neutral, park-and-defense-neutral, and
park/defense/batter-neutral. Only the resulting actual-minus-expected value, its
sample size, and availability were exposed to the final clean test.

## Whole full-result target

The target values next-season MLB singles, doubles, triples, home runs, walks, hit
batters, and workload, including zero for players who do not reach MLB.

- Ridge base RMSE: **0.386052**
- Best Ridge context RMSE: **0.385742** with park/defense/batter neutralization
- LightGBM base RMSE: **0.387210**
- Best LightGBM context RMSE: **0.386802** with park/defense neutralization

The gains are about 0.00031 and 0.00041 WAR RMSE. Both player-clustered uncertainty
intervals cross zero. The LightGBM park-and-defense version improves four of six
chronological folds, concentrated in the four modern folds.

## Separate contact reconciliation

A second architecture left the leading defense-independent, role-enhanced pitcher
forecast unchanged. A separate model predicted only the difference between complete
hit-type value and the defense-independent value, and that correction was added at
the end.

- Unchanged clean role ensemble against the full target: **0.385465 RMSE**
- Ridge contact reconciliation: 0.385518
- LightGBM contact reconciliation: 0.385786

Against the same reconciliation without play-by-play contact, the contact residual
worsened Ridge by **0.000143**, with a fully unfavorable 95% interval. It improved
LightGBM by only **0.000094**, with an interval spanning zero. Neither reconciled
forecast beat the unchanged clean role ensemble reliably.

## Decision

Keep park and defense neutralization as the fair way to describe past contact. Do not
add this residual to projected pitcher value. The detailed event information is not
useless—it modestly helps one noisy full-result learner—but it does not survive the
more defensible test in which contact must add independent future value to the strong
defense-independent forecast.

The leading pitcher development model therefore continues to treat non-home-run
contact at average value. Revisit only with a new untouched season, better portable
contact-quality measurements, or a materially different target; do not tune more
park/defense/batter blends on these exposed folds.
