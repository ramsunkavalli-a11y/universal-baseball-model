# Minor-league infield range RE24 and hitter-value result

Review qualification (2026-09-25): the [deep audit](baseball-methodology-deep-review-2026-09-25.md)
finds that first-touch attribution excludes many through-ground-ball hits from
infield chances. The scores below stand for that restricted measurement, not
certified complete range skill. Reopen the opportunity definition before drawing
a broad conclusion from the failed MLB bridge. No forecast is promoted.

Date: 2026-09-22
Status: **retain as a diagnostic; keep general defense neutral in projected WAR**

## What changed

The earlier infield model measured outs above expectation. This milestone converts
those outs to runs. For every ground ball assigned to a second baseman, third baseman,
or shortstop, it estimates the RE24 difference between a comparable out and non-out
in that base/out situation. The player's park-adjusted out residual is multiplied by
that local run difference.

Park difficulty is estimated from visiting defenses, so a good home defense does not
automatically make its park appear easy. Every future-player test uses only earlier
player seasons. The player regression is selected from older folds, with the already
established 1,200-opportunity regression as the first-fold default.

## Does the run-valued skill persist?

Yes.

- Infield ground-ball opportunities: 1,299,756
- Later player-position tests: 9,155
- Neutral RMSE: 0.04036 runs per opportunity
- Projected-range RMSE: **0.03982**
- Improvement: 0.00054 runs per opportunity
- Prediction/actual correlation: 0.165
- Player-clustered 95% interval for the RMSE change: **-0.00067 to -0.00041**
- Average contextual value of an out versus a non-out: 0.716 runs

The projected range rate beat neutral in every target season from 2017 through 2024,
excluding the missing 2020 minor-league season. This confirms that the earlier
out-based result survives conversion to baseball run value.

## Does it improve total hitter value?

No. The 2025 development test used the new range forecast only as a fallback for
players without prior MLB general-defense exposure. It retained the old forecast for
MLB-informed players and for all non-infield positions. Expected ground-ball chances
were derived from the player's projected defensive outs and observed position-level
chance rates.

| 2025 full hitter forecast | RMSE |
|---|---:|
| Neutral general defense | **0.45166** |
| Old general-defense model | 0.45224 |
| New MiLB infield fallback | 0.45243 |

The new fallback slightly improved the defense component over neutral, but it was
worse than the old defense component and worsened total value. Small blends between
the old and new estimates also worsened monotonically, so this is not merely a bad
full-replacement weight.

## Decision

Keep the park-adjusted RE24 infield range rating as a real, auditable description of
minor-league skill. Do not add it to official projected WAR. Translation from minor-
league range to next-season MLB defensive value remains too uncertain, and the full
player forecast is better when general defense is neutral.

The result does not say minor-league defense is random. It says a repeatable minor-
league range rating has not yet earned a numerical MLB WAR adjustment.
