# Player-path/value bridge: fixed development experiment

2026-09-23. Saved before fitting/scoring this experiment.

## Destination

Our projection system estimates possible player careers. A separate valuation
layer prices remaining transferable rights to those careers. Expected production,
controlled production, cost, surplus and estimated market return are different
outputs. A mean six-calendar-year batting forecast is not any of the latter four.
Public FV is an external diagnostic, never a predictor or a floor.

This milestone tests whether a richer conditional distribution predicts meaningful
success and sustained high production, instead of improving mostly by shrinking
failures toward zero. It also implements a strict path-to-value interface: price
each fully specified whole-WAR/control/cost scenario before averaging. Unknown
rights, costs, whole-WAR conversion or unmodeled tail must block dollar output.
No existing forecast is replaced by this experiment. No 2026 outcomes are opened.

## Reuse and literature

- The old linked hitter replay worsened RMSE at every prefix despite improved MAE:
  `dependent-career-linked-hitter-replay-result.md`. It remains rejected.
- The old dependent simulator used rejected talent inputs and incorrect service
  shortcuts: `dependent-career-path-value-plan.md`. Do not revive it.
- Upper-tail recalibration and aggregate skill-tail experiments failed. This test
  differs by learning the joint distribution of full future annual vectors from
  the current 77-feature panel, not adjusting old stage probabilities.
- [Meinshausen (2006)](https://www.jmlr.org/papers/v7/meinshausen06a.html) motivates
  forest-based conditional distributions. We use a related empirical-path forest,
  not claim this implementation is his exact quantile-regression-forest algorithm.
- [Gneiting and Raftery (2007)](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)
  motivates proper scoring of distributions with CRPS and joint energy scores.
  Binary Brier/log loss and calibration separately test meaningful upper tails.
- [FanGraphs valuation methodology](https://blogs.fangraphs.com/introducing-an-updated-method-for-prospect-valuation/)
  separates controlled production, surplus and star probability. This is design
  literature, not a source of current player grades or protected-season outcomes.

## Data and fixed methods

Use the existing all-affiliated 2009–2025 panel, its 77 cutoff-known features,
certified zero/non-arrival labels, official cutoff-filtered debut evidence, and
the corrected actual-schedule batting/replacement targets. Retain inactive players.
Do not impute unobserved future seasons as zero. Names/IDs/FV are not predictors.

Run horizon 3 at origins 2016, 2021, 2022 (normal paths), plus 2019 as a separately
labeled pandemic stress test; horizon 6 at 2016, 2017, 2018, 2019 (all pandemic
stress tests). Produce separate 2025 research distributions for both horizons.
Training requires every annual label through origin+h <= cutoff and excludes
paths crossing 2020. Each training player contributes their latest eligible
snapshot only, preventing long careers from dominating the donor library. An
outer player's earlier legitimate history may train a forest, but they can never
be their own donor. Add a 2022/H3 fully player-disjoint sensitivity.

Three fixed methods, no hyperparameter or threshold search:

1. B0: uniform historical paths matched to starting stage and age band (<=18,
   19–22, 23–26, 27+; missing separate). Require 40 donors, else stage, else all.
2. F0: path forest using age, level, missingness and three-year PA/MLB-PA history.
3. F1: same forest with all 77 features, adding current/history hitting evidence.

Forests have 100 trees, depth 8, minimum leaf 40, 70% feature subsampling,
no bootstrap, seed 417. Fit annual batting/replacement vectors. Split training
identities deterministically into two halves; fit structure on one half and
draw outcomes from the other, then swap halves and mix equally. Traverse to the
deepest node with >=20 eligible out-of-structure donors, excluding the query
player. Each sampled donor supplies their entire annual PA/value vector together.
This preserves zero years, timing, returns and observed dependence. It cannot
extrapolate beyond historical donor outcomes. Use 400 deterministic draws per
query/method; means/probabilities are empirical Monte Carlo estimates. Save draw
donor IDs/origins, not opaque simulated totals. Report effective distinct donors.

## Fixed diagnostic events (not scouting grades)

- no MLB PA anywhere in the window;
- regular workload: >=450 PA in at least two years;
- substantial batting production: >=6 cumulative batting/replacement wins;
- sustained high batting production: >=4 batting/replacement wins in at least
  two years. This is NOT an All-Star/full-WAR label.

These events overlap; do not display them as mutually exclusive career bins.
Report cumulative value/PA means and P10/P50/P90, event probabilities, coverage,
interval widths, high-predicted-probability calibration, and level/age/recent-debut
subgroups. Never select the scored population on future success. Successful-player
diagnostics may be descriptive but cannot replace all-starting-player scoring.

## Evaluation and decision

Equal-origin cumulative CRPS is primary. Also score cumulative mean squared error,
joint annual-value energy score, and all four event Brier/log losses. Energy score
uses independent pairs of sampled paths, a fixed Monte Carlo approximation.
Compare F1 with both B0 and F0, and its mean with the delivered current-method
historical mean on identical available rows. Six-year historical means are the
existing six-year package's annual sums; H3 uses the latest arrival repair.

Development support requires: favorable player-clustered 95% CRPS differences
against both distribution baselines across >=3 normal origins; improvement in a
majority of origins; no >5% pooled event-score harm or mean-MSE harm against either
baseline or delivered mean; and no >10% CRPS harm in a supported starting group
(>=200 rows and >=3 origins). Regular/substantial/sustained-high events each need
>=30 positives across normal origins, no worse Brier/log loss than F0, and a
predicted/actual event-count ratio within [0.75,1.25]. Small or low-count cells
remain explicitly unsupported. Check nonoverlapping 2016 and 2021 outcome windows
separately; overlapping 2021/22 tests do not constitute independent confirmation.
Use 1,000 fixed-seed player-cluster bootstrap draws. No correction fitted after
viewing outer results. Cold-player sensitivity is diagnostic, since the inherited
delivered reference is not player-disjoint. All six-year claims stay exploratory
regardless of numerical wins because every scored path crosses 2020.

## Value interface and delivery

Test a generic path valuation interface accepting full annual WAR, explicit rights
coverage, explicit obligations, discount rate and an explicit continuous marginal
win-price schedule. Salary obligations persist even without player production or
rights. No hindsight release policy, automatic zero floor on surplus, generic
second prospect-risk discount, current empirical dollar curve or assumed service
path. Unknown inputs or an unresolved control tail return unavailable. A toy
nonlinear-price example may demonstrate why value-of-mean differs from mean-value;
it must not be called an empirical player price.

Deliver results, research player distributions including Eldridge, source hashes,
tests, and a concrete acceptance/rejection. Do not replace the live explorer's
means or market/control values. Future entrants need a separate historical cohort
reserve; they are not assets already owned by today's clubs. Closed-cohort totals
must not be scaled to fill future league totals. Full controlled value still
requires whole-WAR accounting, validated service/rights paths and sourced costs.
