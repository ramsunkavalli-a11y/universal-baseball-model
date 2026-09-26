# Minor-league outfield range RE24 and hitter-value result

Review qualification (2026-09-25): [error decomposition](baseball-methodology-deep-review-2026-09-25.md)
confirms that the whole arm's better component score is outweighed by interaction
with other-component errors. The no-deployment decision stands, but is not a
finding that defense has no predictive signal. Separate the fallback's changed
players and audit opportunity attribution before repeating this bridge.

Date: 2026-09-22
Status: **retain as a diagnostic; keep general defense neutral in projected WAR**

## Question

Can ordinary minor-league play-by-play identify outfielders who repeatedly convert
fly balls and line drives into run-saving outs, after accounting for park, contact
location, handedness, and batter mix? If so, does that skill improve next-season MLB
defensive value and total hitter value?

## Minor-league skill test

The same method used for infield range was applied to left field, center field, and
right field. Park difficulty was learned from visiting defenses. Each out residual
was multiplied by the local RE24 difference between an out and non-out, and each
future season used only earlier player seasons with regression selected from older
folds.

- Outfield fly-ball and line-drive opportunities: **1,864,695**
- Player-position seasons: **32,094**
- Later player-position tests: **11,448**
- Neutral RMSE: **0.049580** runs per opportunity
- Projected range RMSE: **0.049238**
- Improvement: **0.000342**
- Prediction/actual correlation: **0.082**
- Player-clustered 95% interval: **-0.000454 to -0.000232**

The forecast beats neutral in every tested target season from 2017 through 2024,
excluding the missing 2020 minor-league season. This is real but heavily regressed
skill: after the first fold, every chronological selection chose a 3,000-opportunity
regression.

## 2025 MLB value bridge

For players without prior MLB general-defense exposure, projected minor-league range
replaced the older fallback at the matching outfield position. Expected opportunities
were derived from projected defensive outs and observed position-level chance rates.

| 2025 full hitter forecast | RMSE |
|---|---:|
| Neutral general defense | **0.451663** |
| Old general-defense model | 0.452237 |
| New outfield fallback | 0.452303 |
| Combined infield and outfield fallback | 0.452499 |

The outfield fallback predicts the defense component about as well as the old model
(0.126213 versus 0.126202 RMSE) and better than neutral (0.128616). The combined
infield/outfield version is slightly worse than the old defense component. More
importantly, both additions worsen total hitter value, where neutral general defense
remains best.

## Decision

Keep the outfield RE24 range rating as an auditable minor-league skill measure. Do not
add it to projected MLB WAR. The failure is not that minor-league outfield defense is
random; it is that its current translation and opportunity bridge do not improve the
whole player forecast. General non-catcher defense therefore remains neutral until a
new target or independent confirmation can beat that standard.
