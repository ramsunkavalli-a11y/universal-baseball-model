# Direct batting-value learning: useful contrast, not a replacement

2026-10-05. All 105 fixed residual-Ridge heads were fitted and independently
replayed after 105 preflight checks. The source matrices, fold memberships,
three routes and PA forecasts are unchanged from the completed count comparison.
All 30,506 original forecasts and thirteen separate additions remain. Sixteen
[source/model player walks](hitter-past-direct-value-player-review.md) are complete.
No 2026 outcomes, frozen forecasts or explorer predictions changed.

This predicts next calendar year's conditional MLB batting rate and delivered
batting-plus-replacement value, not full WAR, lifetime outcomes or club control.
The [pre-fit contract](hitter-past-direct-value-contract.md) sets the comparison.

## Result

| Original population | Incumbent | Count model | Direct-rate model |
| --- | ---: | ---: | ---: |
| Hitting RMSE, wins above MLB mean per 600 PA | 1.80481 | 1.81347 | 1.80422 |
| Delivered batting-plus-replacement RMSE | 0.43513 | 0.43811 | 0.43695 |
| Delivered mean absolute error | 0.12387 | 0.12371 | 0.12423 |
| Total predicted value | 4,155.43 | 4,117.78 | 4,187.11 |

Actual value totals 4,185.43. Expected PA is exactly 1,228,732.51 in every arm,
versus actual 1,270,493. The near-perfect direct-rate total does **not** establish
correct player allocation. Delivered error still exceeds the incumbent and
worsens in six of seven origins. Hitting improves in three of seven origins,
not a consistent broad improvement.

Versus the incumbent, hitting MSE changes −0.00213, with a nominal exposed
player-clustered 95% interval [−0.03757, +0.03405]. Delivered MSE changes +0.00158
[−0.00041, +0.00348]. These do not establish an overall accuracy gain. Versus the
count model, hitting MSE improves −0.03346 [−0.05915, −0.00722]; delivered change
−0.00102 [−0.00291, +0.00100] remains uncertain. Historical results have already
been repeatedly exposed; these intervals are descriptive, not selection-adjusted.

## Baseball and cohort checks

Players with at least 600 weighted recent MLB PA still worsen against the
incumbent: hitting 1.53723 to 1.54863, delivered value 1.33273 to 1.34642. Direct
learning recovers some of the count loss but does not solve the established-MLB
problem. Current MLB hitters similarly worsen 1.70546 to 1.70950 in hitting.
There are no physically impossible scalar rate forecasts in this run.

Upper-minor never-debut hitters improve hitting 2.56325 to 2.53946 and delivered
RMSE 0.30170 to 0.29925. Yet their expected value is only 160.28 versus 196.73
actual, below the incumbent's already low 177.49. Lower-minor hitting improves
3.17908 to 3.08251, but only 54 future-active observations support that rate
check. A one-year test with many non-arrivals cannot certify identification of
future stars from DSL. Non-arrival delivered RMSE worsens 0.06939 to 0.07215,
even while total expected value among non-arrivals falls.

The 253 original foreign-history forecasts have 28 active labels. Direct hitting
improves 1.88024 to 1.81836; delivered error barely changes 0.49309 to 0.49301.
This small group does not establish a supported MLB translation, and named
foreign cases still fail in opposite directions. Among the thirteen separate
additions, with six active labels, rate RMSE worsens from the count arm's 3.20812
to 3.43398 (7.0%, triggering the declared >5% review); delivered RMSE slightly
improves 1.43564 to 1.43357. Suzuki 2021 remains a clear hitting/workload
cancellation, not an arrival-and-talent success. There is no incumbent for those
additions, so no invented comparison or silent population change is allowed.

On the same 2,627 historical public-matched forecasts (2,088 active), the
origin-centered hitting score is incumbent 1.72848, count 1.71858, direct 1.71815,
Steamer 1.77459 and ZiPS 1.75336. Against the future-relative target on those
rows, the incumbent instead beats direct (1.66475 versus 1.67205). Release,
park and environment conventions remain unharmonized, and ZiPS workload is not
certified. Do not claim that this result beats the public projection systems.

## What changed and what can be concluded

The exact past probability baseline is retained. Instead of predicting eight
events, Ridge predicts its future batting-rate correction, with fixed alpha=100
and the same relative future-PA/equal-origin training weighting. Baseline plus
intercept plus every feature contribution replay. This changes the response
family, loss, linear correction and penalty geometry; it is not a pure isolated
likelihood comparison. It does show that the same compressed input need not
suffer the count arm's full hitting loss. It does **not** prove that the original
count architecture, four removed MLB-quality features or 1,200-PA source prior
are individually responsible, nor that a penalty search would fix the model.

Khris Davis becomes less optimistic than under counts; established Judge becomes
less optimistic too, losing a real count-model gain. Misner's batting estimate
is nearly exact, but his delivered estimate is less exact than the count arm
because the count arm benefited from cancellation. Suzuki 2022 improves
substantially versus the incumbent while Thames 2017 becomes the largest harm.
Those opposite foreign outcomes argue against choosing a flattering anecdote
or a post-result foreign branch.

Disposition: **do not adopt**. Keep the incumbent. All code/data arithmetic,
head replays and walkthroughs passed; predictive superiority and sufficient
profile support did not. Both frozen packages and the completed one-time 2026
evaluation remain final and unchanged; the long hitter goal remains active.

The coherent next question is lost MLB-production detail, not another unrelated
model family. Audit the four removed year-specific/pooled MLB-quality inputs and
their exact raw-count/reference meaning, then declare one matched restoration
contrast on this same direct-rate learner if the audit supports it. Keep source
matrices, prior, weights, alpha, PA and all anchors otherwise fixed. Foreign
context remains provisional and must not be hidden by near-correct totals.
