# Hitter role and workload research milestone

Frozen before new challenger scores, 2026-09-22. Research only: no delivered
2026–2028 forecast changes and no 2026 outcomes.

## What the literature actually supports

- [PECOTA playing time, Austin 2021](https://www.baseballprospectus.com/news/article/64321/pecota-week-a-depth-chart-playing-time-primer/): human depth charts assign positional opportunities using roster and team context. This is not a published automated injury/PA equation.
- [ZiPS variants, Szymborski 2021](https://blogs.fangraphs.com/instagraphs/updates-to-zips-three-year-and-zips-depth-chart-projections/): standalone talent projections and depth-chart-adjusted playing time are different products. Do not benchmark a talent-only line as an expected workload.
- [Wang 2009](https://tht.fangraphs.com/projecting-playing-time/): age, prior workload, prior performance, injury history and preseason starter status were useful in a restricted regular-player regression. Its reported in-sample fit is not an out-of-time accuracy standard. Prior-season starts are our available proxy, not the same as knowing next Opening Day's lineup.
- [ATC, Cohen 2017](https://fantasy.fangraphs.com/the-atc-projection-system/): combining forecasts and manual preseason playing-time changes is relevant, but does not establish optimal weights for our model.
- [Forecast evaluation, Hyndman and Athanasopoulos](https://otexts.com/fpp3/tscv.html): expanding historical cutoffs must respect each forecast horizon. We apply this to player panels; repeated player histories are clustered for uncertainty.

Our adaptation: compare a role-feature ablation and a workload-state mixture.
The mixture is an experiment, not an assertion that PECOTA or ZiPS uses it.
The expected PA is the probability-weighted mean across states, not the workload
of the most likely state. A healthy-season workload must not replace an expectation.

## Source audit and existing work

The existing roster-aware five-member next-year ensemble is a mandatory additional
benchmark wherever populations overlap. Its previously reported 60.816 PA RMSE
is from another cohort and cannot be compared directly to multi-year results.
The delivered multi-year PA model is a separate universal hurdle with the accepted
established-player probability update. Batting-value means are modeled separately.
Broad injury counts, availability gaps and league allocation already failed or
were uncertain; do not retune them here.

Official MLB fielding-usage history has starts by position including DH, 2004–2025.
Sum starts across non-pitcher positions and teams, never sum games played across
positions. Test prior two seasons of starts (schedule normalized), positional
start shares, positional breadth, and smoothed PA per start. Check duplicate keys,
negative counts, year coverage and impossible summed starts. These are role proxies,
not diagnoses. Zero MLB starts for minor leaguers is not zero minor-league usage.
No new all-level lineup/platoon feature is claimed in this milestone.

Private historical Opening Day workbooks cover 2023–2025. They were retrieved in
2026 and have limited projected-PA coverage. Audit their aggregate coverage and
forecast error only as an archival reference; no matched-vintage head-to-head claim
against December models. Do not train on them, replace missing projections with
zero, or publish their bulk records. A genuinely matched-date human/model test
remains conditional on verifying frozen forecast vintage and roster information.

## Fixed experiment

Same multi-year universal hitter panel and mature targets, origins
2016, 2017, 2018, 2019, 2021, 2022, 2023; horizons 1 and 2. Independent historical
performance anchor is held identical across PA candidates for partial-value tests.
Train only origin+horizon <= forecast origin. Exclude pandemic-crossing training
rows (origin < 2020 <= origin+horizon). Report pandemic-crossing test folds
separately, never normalize a future pandemic with hindsight. Existing schedule
normalization is allowed only for already completed input seasons.

Fixed candidates, no hyperparameter or bin search:

1. Base: LightGBM binary participation and positive-PA regression, existing
   77 full-panel predictors (includes batting performance, age, level and 40-man).
2. Role: same learner and targets, adding the audited role features.
3. Mixture: role predictors, classify future PA as 0, 1–199, 200–449, 450+;
   regress PA separately in each positive state, then probability-weight.
   These are workload ranges, not inferred injury labels.

Use existing balanced LightGBM parameters, seed 417, four threads; positive
predictions bounded 1–750 and mixture means within their fixed state supports.
Same known players can contribute earlier history, but no player ID is a feature,
no future labels or identity random effects, and no random row validation.
Since settings are fixed, there is no tuning stage requiring nested selection.

## Scoring and decision

Equal-origin PA MSE (also RMSE/MAE/bias) and fixed-anchor batting-plus-replacement
value MSE, not full WAR. Primary normal-calendar folds; pandemic stress separate.
Participation Brier/log loss; mixture state probabilities receive multiclass Brier
and log loss, not a claim of calibrated within-state predictive distributions.
Stars are top 50 by the pre-existing year-one value forecast, never actual WAR.
Report young stars, MLB age groups, upper/lower minors and per-origin results.
Paired player-cluster 95% intervals condition on fitted models and observed seasons.

Compare role minus base, mixture minus role, and each versus accepted multi-year PA.
Also compare next-year candidates to saved roster-ensemble forecasts on their exact
intersection, reporting omitted counts. Do not call improvement over a weaker
baseline a production win. Require PA and value improvement, majority improving
normal folds, no point worsening for top-50/young-star PA or value, and no reversal
against the stronger overlap benchmark before recommending a separate confirmation.
All results are exposed development evidence, not final validation. No automatic
promotion or more candidate tuning after these scores.

Deliver source audit, tested implementation, prediction artifacts, reproducible
metrics, limitations and next decision. Preserve original forecast hashes.
