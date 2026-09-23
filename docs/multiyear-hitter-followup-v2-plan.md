# Bounded hitter opportunity and uncertainty follow-up

Frozen before new scores, 2026-09-22. Preserve v1 point forecasts, all original
forecast packages, and the protected 2026 outcome boundary. This is exposed historical
development, not an independent confirmation. No algorithm/parameter sweep.

## Source findings

Alonso is absent from the saved 2025-10-15 Mets 40Man response itself, not lost in a
join. Membership is an endpoint-presence proxy, not proof of reserve rights. Audit
the saved 30-team responses and a bounded historical re-fetch/transaction check;
do not hand-add a player or change the frozen v1 inputs.

The earlier established-hitter audit used `season < origin` without requiring
`season + horizon <= origin` in its rolling fits. Its longer-horizon validation is
therefore contaminated. Also, its log-PA regression was retransformed without a
mean-bias correction; that estimate was not promoted originally. Reuse the feature
idea and fixed logistic settings, NOT the claimed validation or current 2026 inputs.

## P: established-player opportunity

Population: same fixed v1 cohorts. Update only players with current MLB PA > 0,
known age, and at least 200 MLB PA in either of the preceding two calendar seasons.
Everyone else retains the existing opportunity model. Fit each horizon separately,
using only labels mature at the forecast origin; exclude pandemic-crossing training
windows, matching the existing opportunity contract. Outer origins are v1's
2016, 2017, 2018, 2019, 2021, 2022. Never import the old live-preview 2026 features.

- P0: existing opportunity model, unchanged.
- P1: refit the existing five-feature logistic idea (target age, three log MLB-PA
  values, batting quality regressed by 1,200 PA), C=1, max_iter=2000, seed=417.
  Age comes from the fixed cohort's sourced season age. Retain P0 conditional PA.
- P2: P1 probability plus a standardized Poisson mean regression on active-player
  PA using the same five features, alpha=1, max_iter=2000. Predict the conditional
  arithmetic mean directly; no naive log retransformation. This is a mean model,
  not a Poisson variance claim. Clip predicted conditional PA to [1,750] as the
  existing practical workload bound; record clipped counts.

No inner tuning. Assess probability and conditional workload separately. For P1,
require paired player-cluster 95% intervals favorable for equal-origin Brier and
log-loss differences, improvement in at least four of six origins, no >5% relative
proper-score regression at any horizon, and nonpandemic sensitivity favorable.
For P2 conditional PA, require favorable paired unconditional PA-MSE interval versus
P1, lower equal-origin PA MAE, majority-origin improvement, and no >5% horizon-MAE
regression. If P1 fails retain P0; if only P2 fails use P1 with existing conditional
PA. Value forecasts remain unchanged: this is not a joint-value promotion.

## Q: conditional uncertainty

[Quantile boosting](https://scikit-learn.org/stable/auto_examples/ensemble/plot_gradient_boosting_quantile.html)
estimates outcome percentiles conditional on inputs rather than imposing equal error
spread. [Conformalized quantile regression](https://papers.neurips.cc/paper_files/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html)
motivates calibrating quantile errors. Its exchangeability guarantee does not apply
automatically to repeated players and changing baseball seasons. The rolling variant
below is evaluated empirically; do not call it distribution-free conditional coverage.

- Q0: the failed stage-residual method, refit from eligible earlier out-of-sample
  errors of the fixed delivered mean recipe. Extend earlier mean predictions with
  the same D1/B0 first-year fallback, not a new model selection.
- Q1 diagnostic: fixed LightGBM quantile models at .10 and .90, separately for
  Year 1, Year 2, Year 3 and cumulative three-year actual value. Use the same 77
  cutoff-only aggregate features, 300 trees, rate=.03, num_leaves=7, max_depth=3,
  min_child_samples=100, reg_lambda=8, seed=417, four threads. No outcome transforms.
  Sort crossed endpoints before calibration and record crossing counts.
- Q2 candidate: Q1 plus nonnegative rolling quantile-error corrections from the
  latest five fully mature earlier origins, with at least two origins. Partition
  by forecast-time stage and low/high predicted value, using the calibration pool's
  80th percentile of fixed mean forecasts. Minimum bucket=100; otherwise stage
  fallback (minimum=100). Use the finite-sample upper empirical 80% quantile of
  max(lower-actual, actual-upper, 0). Corrections may widen, never shrink.

Earlier raw quantile forecasts are refit at their own origins, starting in 2012.
Calibration never sees a partially observed target window. No sums of annual
quantiles, clipping of negative WAR, forcing the mean inside an interval, or use of
future participation. No full-distribution/CRPS claim from only two quantiles.

Only Q2 may be delivered in this batch; Q1 cannot be selected from outer scores.
Gate each horizon independently: at least three scored outer origins; paired
player-cluster 95% interval favorable for equal-origin 80% interval-score difference
versus Q0; majority-origin improvement; overall coverage >=75%; supported stage and
high-predicted-value group coverage >=75%. Supported means >=100 rows over >=3
origins; report smaller cells but do not pretend their calibration is established.
Require nonpandemic mean interval-score improvement. Interval score penalizes width
and misses, so blanket widening is not free. Report high groups both using prior-pool
thresholds and top 20% of the current forecast cohort, chosen without outcome labels.
Unaccepted horizons stay null. Acceptance is provisional development support, not
prospective coverage. No second tuning pass after failures.

## Delivery and boundaries

Keep original mean forecasts byte-identical by player. Produce versioned opportunity
and interval tables plus historical scores, roster audit, selection report and source
hashes. Update the local explorer to use only accepted components. Retain caveats
where value and workload remain separately estimated. Check established hitters,
minor-league high-value tails, missing ages, no-play zeros and protected future nulls.
Commit the contract before scoring, then commit/push the result and next direction.
