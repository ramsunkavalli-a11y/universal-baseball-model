# Test freely learned hitting against an imposed starting estimate

2026-10-05. Written before fitting, after the completed restored-error diagnosis
and seventeen actual player checks. This is one matched historical development
comparison, not a new independent holdout or a feature/algorithm tournament.

The seven-input model estimates next-calendar-year MLB batting wins above the
target league mean per 600 PA as a fixed past-production baseline plus a fitted
residual. Test the same learner without that imposed baseline: fit absolute
future batting rate and predict the fitted rate directly. Past production remains
in the identical inputs, so this does not discard history. It changes the learned
target and the regularization center, not merely a constant shift of forecasts.
The error diagnosis does not prove that the imposed baseline causes its mature
MLB weakness. This comparison can investigate that hypothesis without new data.

## Population inputs and fitting

Keep all 30,506 original forecast rows and thirteen separate source additions,
including all exits and non-arrivals. Reuse the five sealed source matrices,
exact 35 chronological whole-player cells, full/active training memberships and
123/132/186-feature base/prospect/tracking routes from the seven-input restoration.
All eligible active training rows contribute to each route as before. Preserve
the original incumbent and count, scalar and residual-restoration anchors.
Sources and outcomes end in 2025; origin years are 2016–2018 and 2021–2024.
Canceled 2020 target is absent. Short-season 2020 MLB inputs and 2021 league
changes remain real, qualified history. No 2026 outcome access or explorer change.

Use the exact fixed-unit matrix and Ridge alpha 100, intercept, Cholesky solver,
equal-origin training row weights times uncapped actual future PA, normalized
to active training-row count. The old fit learns `actual relative rate - past
baseline`; the new fit learns `actual relative rate`, with a zero offset at
both training and prediction. No coefficient/penalty/prior search or fitted
scaler. No blending, subgroup model selection or future-dependent clipping.
The model still sees past CLR production, separate MLB quality and seven event
rates, age/exposure/position/context, prospect inputs and tracking when routed.
Foreign relative dominance remains an unproven MLB transfer; removing its fixed
offset is not a new competition equivalency. Prior source masses stay unchanged.

Before fitting, independently pair all training/evaluation MLB counts and labels,
verify all previous hashes and freeze sources, contract, runner and 105 preflights.
Audit the zero-offset target mechanically on all seventeen source cases, keeping
actual old baseline, residual, raw sources and support references. A fixed-fit
subtraction of baseline is artificial and is not the candidate prediction.
Because inputs, memberships and transformations are exactly unchanged, inherit
the previous full/active distinct-player joint support and range warnings,
explicitly including sparse/absent profiles; preflight each active fold again.
Missing history is not zero talent and a populated coordinate is not support.

## Forecasts scoring and player checks

The new rate uses the unchanged routing rules. Expected PA is copied exactly
from the saved research forecast; delivered value is expected PA times rate/600
plus the authoritative forecast replacement term. Score inactive players only
in delivered contribution; no observed hitting label or fabricated count
probabilities. This target is batting plus replacement, not defense, full WAR,
multiyear control, lifetime ability or trade value. No opportunity improvement
can be claimed because no job model is refitted.

Primary scores are unchanged equal-origin actual-PA-weighted hitting RMSE and
equal-origin delivered-value RMSE on all originals. Report MAE, paired nominal
player-clustered intervals against incumbent and the matched residual arm,
all origin/stage/non-arrival/mature-MLB/foreign cohorts, PA/value totals and
qualified matched historical Steamer/ZiPS comparisons. Report thirteen additions
without inventing an incumbent. A >5% worsening in any nonempty scored cohort
requires explicit review; not all cohorts have adequate active labels. Check
the physical rate envelope and preserve warnings without clipping/deleting.

Replay all 105 heads. Retain seventeen fixed source/model cases and add a new
largest gain/harm, false high/low or ordinary 200–399-PA case if not already
covered, according to unweighted squared delivered error versus incumbent.
For every case reconstruct actual past sources and fitted contributions, show
intercept plus all feature effects and the removed old baseline separately,
retain origin-selected comparison peers, actual joint support and fixed-fit
minor/foreign removal probes. Decompose hitting/opportunity errors to expose
cancellation. Keep unfavorable cases and unsuccessful peers. Do not launch
another fit or make a disposition before readable source-to-model review.

## Decision limits

To warrant replacement consideration, beat incumbent on both primary measures,
explain changes to consequential players and pass origin/cohort reasonability
review. Integrity, support, prediction and deployment are separate. Improvement
over the residual arm alone does not certify the final hitter model; a near-tie
is not statistically decisive. Public comparisons retain existing environment,
vintage and ZiPS workload limitations. No automatic forecast/explorer promotion.
Stop after this fixed comparison and completed player review. Decide the next
action from evidence rather than another algorithm, prior or subgroup sweep.
