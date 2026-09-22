# Pitcher contact-value block v2 result

Date: 2026-09-22
Status: **do not promote raw season-total contact detail**

## Question

If the pitcher target values singles, doubles, and triples instead of treating every
non-home-run ball in play alike, do the same detailed minor-league results improve the
next-season MLB value forecast?

## Test

The saved official source captures were reprocessed because the standardized pitcher
table had retained K, BB, HBP, and HR but discarded hits, doubles, and triples. The
test recovers those fields across the full historical panel. It adds raw and
season/level-relative single, double, triple, and non-hit-other rates to the same
three-season feature panel.

The target is also expanded to value the actual MLB hit type allowed in the following
season. It is centered within each MLB season and includes players with zero MLB value.
The six scored origins and all training cutoffs are identical between the baseline and
the challenger. No 2026 result is used.

## Result

| Engine | Baseline RMSE | With detailed contact | Change |
|---|---:|---:|---:|
| Ridge | **0.38605** | 0.38622 | +0.00017 |
| CatBoost | **0.38630** | 0.38696 | +0.00065 |
| LightGBM | **0.38721** | 0.38846 | +0.00125 |

Lower is better. All three detailed-contact versions are slightly worse overall. The
player-clustered intervals cross zero, so the ridge and CatBoost differences are too
small to distinguish confidently from noise. LightGBM is also directionally worse in
five of six folds.

The expanded full-result target is much noisier than the defense-independent target:
its best RMSE is about 0.386 instead of 0.312. Those values should not be compared as
if they were the same baseball quantity. The gap shows how much team defense, park,
opponent mix, sequencing, and random ball-in-play variation enter the fuller result.

## Decision

Do not add unadjusted season-total single/double/triple rates to the clean-slate value
model. This is not evidence that contact quality is irrelevant. It says that raw hit
types do not separate pitcher talent cleanly enough. The already-tested schedule-level
park adjustment was also mixed on its untouched confirmation year, so it is not a
sufficient repair by itself.

Keep the complete result target as a diagnostic. Revisit pitcher contact only with a
more defensible event-level separation of pitcher, park, opponent, and defense effects.
Move next to the pitch-process block, which has a cleaner mechanism and previously
improved next-year component forecasts.
