# Testing uncertainty around the current playing time forecast

2026-10-03. Saved before new fits. The source-qualified handoff is complete;
earlier paired-forest and exact-mixture results have been reviewed. This is one
bounded active-workload risk comparison under the practical hitter plan, not
another point-model tournament or a claim of full hitter value completion.

## Question and fixed forecasts

Can a separately estimated positive-workload spread give useful next-calendar-year
MLB playing-time probabilities and ranges around the current candidate's means?
Keep its appearance probability, conditional PA mean, expected PA, hitting rate
and delivered-offense mean exactly unchanged for every forecast. Retain the same
30,506 player origins, non-arrivals, exits, seven origins and 35 whole-player
chronological cells. The latest target is 2025. Do not access 2026 outcomes.

This deliberately cannot repair underpredicted means or claim better batting
talent. A good workload-risk result advances uncertainty; it cannot waive the
public playing-time benchmark or produce full offense, WAR, career-control or
trade-value uncertainty. Availability/source qualifications remain visible.

## One candidate and two references

The candidate has exact probability 1-p at zero. Given appearance, model
PA as 1 plus a beta-binomial count with n=799. For conditional mean c, the
beta mean is (c-1)/799. One positive concentration parameter controls spread;
estimate it from earlier, genuinely nested held-player active outcomes only.
Use a single global concentration per outer cell, bounded [.1,1000], estimated
by weighted negative log likelihood with deterministic scalar optimization.
No stage-specific tuning, width multiplier or post-result concentration sweep.
At c=1 or c=800 use the corresponding deterministic boundary distribution.
Keep boundary observations; any scoring floor must be reported separately.

The support [1,800] is the existing engineering bound and must be checked against
all source targets before fitting. It is not a claim that more than 800 PA is
physically impossible. A target outside that bound requires a documented design
amendment before fitting, not deleting the player.

Reference one uses the same zero probability and mean, with positive PA equal to
1 plus Binomial(799,(c-1)/799). It supplies a minimal parametric spread, not a
strong public-system uncertainty model. Reference two is the preserved paired
forest's saved PA P10/P50/P90 on the exact same cohort. Its means, features and
participation probabilities differ, so that comparison does not isolate spread
alone. Its known source/support qualifications remain. No calibrated public
ranges are available; public point estimates are not uncertainty targets.

## Nested estimation without outer player leakage

Use the current 251 opportunity inputs and the exact existing outer training
row IDs; keep all dated source and scouting-vintage qualifications. For outer
fold k, pick inner held-player group (k+1) modulo 5, using the existing permanent
player-fold assignment. The outer tested players must never enter any inner
fit, transformation or dispersion-estimation label.

For each of the three most recent possible inner origin years before the outer
origin, use inner validation rows from the outer training IDs whose origin is
that year and whose player fold is the selected inner group. Their outcomes
must be mature by the outer cutoff. Exclude target 2020 as in the existing
candidate. Fit the inner conditional PA head only on active rows from outer
training IDs with target year no later than that inner origin, excluding every
inner held player's entire group. Use exactly the current conditional-head
settings and equal-origin weights. Do not substitute current in-sample forecasts
or another outer fold's old predictions for these nested forecasts.

For each nonempty inner subset, save identities, actual chronology and distinct
profile support before any fit. Check scout release dates do not cross the inner
information date. Active validation outcomes estimate concentration using the
inner head's bounded mean, not the final head's fitted values. Weight represented
validation target years equally. Inactive validation rows remain in source and
support receipts but do not become positive-workload labels.

Empty or weak inner support is an explicit gap. Do not silently borrow an outer
test outcome or change the held group to improve results. If the construction
cannot estimate a concentration, preserve that forecast under a separately
declared unestimated-reference fallback, report its identities and counts, and
do not claim candidate validation for it. A pre-fit amendment must state that
fallback before results; do not fabricate one during scoring.

## Scoring and review

Primary distribution comparison is the equal-target-year average pinball loss
at PA quantiles .1, .5 and .9, computed identically for the beta-binomial,
mean-matched binomial and saved paired-forest reference. Also report the proper
80% interval score, interval width and inclusive coverage; do not interpret
near-100% lower-minors coverage as proof of nominal 80% calibration. Report
active outcomes separately as a diagnostic, without using actual activity to
generate forecasts. Discrete CRPS against the mean-matched binomial is a
supplementary full-distribution check. Brier/log loss for any PA must remain
identical to current by design; assess at least 400 PA as an additional event.
Continuous and event scores must retain all non-arrivals and boundary cases.

Show all players, current MLB, never-debut upper/lower minors, current absences,
thin newly drafted players, each origin, probability bands and the fixed public
matches. Use nominal paired player-clustered intervals and report conditional
support gaps. Totals and current public point errors must be identical to the
candidate, not silently improved by replacing mean with median. Keep exposed
development results distinct from an untouched test.

Fixed player walks: Kurtz 2024, Langford 2023, Alonso 2018, Judge 2016 and 2024,
McLain 2024, Belt 2023 and Franco 2023 when in the fixed cohort. Add the largest
pinball gain and deterioration, false high/low and an ordinary case. Follow
the required stats-to-inputs-to-saved-fit checkpoint: actual dated level counts,
point-head outputs, nested calibration identities and concentration, complete
distribution arithmetic, quantiles and event chances, observed outcome and
origin-selected successful/unsuccessful comparisons. Report uncertain source
and absent matching support; do not tune to famous misses.

Only retain as a workload-risk research component if proper scores, major-stage
and player checks support it against both references. A crossed interval or
material systematic failure leaves it provisional or rejected, not auto-promoted.
No new explorer ranges or frozen forecast changes before completed review and
separate authorization where required. Batting-performance spread remains a
separate unfinished part of the full practical goal.

## Literature and earlier work

[Gneiting and Raftery](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)
support proper probability, quantile and interval scoring rather than judging
coverage alone. The mixture shape follows the useful distinction in the
[earlier exact-mixture review](rolling-combined-war-uncertainty-result.md), not
its numeric scale factors. The [paired forest](practical-hitter-joint-forest-v43-result.md)
and its sixteen player walks remain a substantive empirical reference; its
failed mean forecasts do not reject every uncertainty approach, nor do its
coarse-reference gains establish calibrated risks for this current model.
