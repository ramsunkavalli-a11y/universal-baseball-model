# Arrival timing and coherent delivered value — pre-fit contract

2026-09-23. Trigger: the six-year explorer's 2027 rookie-ball contribution and
unreconciled aggregate totals. This is exposed historical development, not a
new independent confirmation set. No 2026 outcomes or frozen-package edits.

## Fixed test

Use the existing 2009–2025 affiliated snapshot panel, all original players and
non-arrivals. Extend outcome labels through horizon 6 using the existing certified
MLB targets. Training labels must mature at each cutoff; exclude windows crossing
2020. The current scoring cutoff remains 2025-12-31. Never-debuted means no official
debut by the cutoff, verified against observed MLB PA; future debut dates are not
features. Missing age, inactive/unknown levels, and MLB returners are unchanged.

One new fixed hurdle recipe:

* Annual MLB activity probability from a hierarchical empirical rate, separately
  by horizon, exact starting level, and age bands <=18 / 19–20 / 21–22 / 23+.
  Estimate each level's rate with a Jeffreys half-success/half-failure prior.
  Shrink its age cells toward that level rate with 100 pseudo-observations.
  Missing level support falls back to the delivered forecast, not a global rate.
  This deliberately simple rare-event benchmark must earn its place; it does not
  assume a prospect's actual probability depends only on those two attributes.
* Conditional positive PA: the existing balanced LightGBM regression recipe,
  trained on all active target players with the same 77 cutoff-known features.
  Clip predicted positive PA to 1–750, as in the prior experiment.
* Conditional batting/replacement rate: same LightGBM recipe, active players only,
  outcome WAR*600/PA, training weights proportional to actual target PA; clip
  predicted rate to [-5,10]. PA weighting targets a workload-weighted rate, rather
  than giving a one-PA observation equal weight to a full season.
* Expected PA = probability × conditional PA; value = expected PA × independently
  fitted rate / 600. Never infer hitting talent by dividing the existing forecast
  by its PA. This is coherent accounting, not a fully joint career simulation.

Predeclared deployment scopes: C1 replaces **never-debuted affiliated minor
leaguers**; C2 uses the SAME fitted recipe but replaces **rookie-ball players only**.
Everyone else keeps the exact delivered numbers. Try C1 first; use C2 only if C1
fails and C2 passes its own checks. No fitted blend weights or blanket league uplift.
Sensitivity: probability prior strengths 50/200, reported but never selected.

## Benchmarks and validation

H1–3: exact delivered PA/probability and batting value from the previous opportunity
test, plus its stronger five-member PA ensemble and matching rate-anchor product
as a secondary comparator. H4–6: saved six-year extension predictions. Do not
claim disjoint validation of the inherited reference. Candidate cold-start test:
origin 2022, H1–3, omit every scoring player from candidate training.

Score all available reference origins. Primary normal H1–3 origins are the existing
2016–19/2021–22 set filtered per horizon. Later horizons have limited or no normal
path support; do not extrapolate a short-horizon pass to H4–6 adoption.

Report individual PA/value MSE, value MAE, Brier/log loss, annual participation
counts and PA/value totals by origin, level and age, including RK<=18. Aggregate
error compares the SAME starting cohort's predictions with its realized MLB
production—not a later full-league roster that includes new entrants. Absolute
league totals remain a separate sanity check. Do not force them to 570 or 183k.

For each scope, normal H1–3 adoption requires:

1. Favorable paired player-cluster 95% interval for three-year value MSE in the
   affected cohort and non-worse affected-cohort cumulative MAE.
2. No >5% value-MSE worsening in each affected annual horizon or supported
   level/age cell (>=100 rows, >=3 origins, >=10 actual active observations).
   Sparse cells remain visible, not silently declared safe.
3. No >5% PA-MSE, Brier or log-loss worsening in each annual affected cohort;
   no worse absolute aggregate PA/value error averaged across origins/horizons.
4. Non-worse overall cumulative value MSE. Report cold-start sensitivity and
   comparisons against the stronger PA ensemble; no claim to beat that ensemble
   without evidence. A targeted repair may be retained without replacing it.

Before any combined-value explorer update, hold inherited component rates fixed
and scale their totals by candidate/delivered PA only in the accepted scope.
Score that delivered ledger on identical complete component labels. Require
non-worse cumulative expanded-target MSE; otherwise update batting/PA research
only and do not imply the old component ledger is coherent with it.

If checks fail, keep the explorer forecasts unchanged and record the failure.
If H1–3 pass, publish a separate version with explicit horizon/scope labels; keep
H4–6 provisional and unchanged unless independently supported. Preserve the
original six-year package and the original one-year 2026 freeze. Record ongoing
aggregate-budget, unseen-entrant, standard-WAR normalization and service-tail gaps.
