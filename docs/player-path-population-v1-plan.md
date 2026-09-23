# Fixed population repair A1 — execution contract

2026-09-23. Saved before any A1 fit or outcome scoring. Parent:
`projection-anchored-path-next-checkpoint.md`. Development evidence, not a new holdout.

## Fixed experiment

Same complete normal-path training filter, targets and 77 predictors as path v1.
Latest-snapshot B0/F0/F1 retained. A1 keeps every eligible origin snapshot and gives
each identity total weight one (row weight 1 / eligible snapshot count), both in
structure fitting and conditional node sampling. No outcome-based snapshot selection.
Entire identities share the same half; permutation of sorted identities with seed
417 reproduces v1 splits. Forest: 100 trees per half, depth 8, minimum 40 structure
rows per leaf, max_features .7, no bootstrap, seed 417. Weighting does not turn the
40-row leaf rule into 40 identities; independent support is recorded separately.

Node fallback: ascend until at least 21 distinct donor identities before excluding
the query. Remove all query snapshots in each tree, leaving at least 20 identities;
normalize the previously assigned row weights inside that node. Same rule for F0/F1,
where one identity is one row and this exactly equals v1's rule. No extra ESS gate:
report identity-level ESS and group borrowing, rather than tune another constraint.
Each of 200 trees has equal mixture weight. B0 retains v1's age/stage, stage, global
fallback with 40-row support. No changes to live forecasts or protected outcomes.

H3 origins 2016, 2019, 2021, 2022, 2025; H6 origins 2016, 2017, 2018, 2019, 2025.
Cold sensitivity: H3 2022 excludes all query identities from fitting. 2025 is a
research-only distribution, not scored. All H6 historical tests cross the pandemic.
Normal H3 decision uses 2016, 2021, 2022; nonoverlap check uses 2016, 2021.
Earlier-origin benchmark forecasts are absent: no new origins are invented.

## Simulation and common scoring

First reproduce the original 2016 H3 F1 seed-417 sampled donor matrix exactly.
For this test integrate forest mixture weights explicitly. Fit once per fold/method,
then independently sample whole donor paths from that fixed mixture with seeds
417,418,419,420,421 at 400 draws and seed 417 at 1600 draws. This IID sampling replaces
v1's stratified two-draws-per-tree allocation for ALL four methods; fitted F1's
distribution is unchanged. Do not compare unlike finite-draw scoring conventions.

Main means, cumulative CRPS, event probabilities, Brier and log loss are integrated
over the complete donor distribution, removing simulation error. Repeated IID
draws separately estimate them. CRPS uses the unbiased U-statistic pair term;
MSE subtracts sample variance / n; Brier subtracts p(1-p)/(n-1). These estimates may
be slightly negative. Energy uses disjoint independent pairs, no self-pairs. Log
loss clips probabilities to [.5/401,1-.5/401] at BOTH draw counts and exact scoring;
no unbiased log estimator is claimed. Intervals/coverage are simulated diagnostics.
Finite draws assess numerical stability, not additional independent evidence.

## Acceptance, frozen before fitting

Equal-origin scoring, whole-player bootstrap (1000 draws, existing seed-417 helper).
A1 must improve exact CRPS versus F1, F0 and B0 with paired 95% interval upper bound
below zero, and improve a majority of the three normal origins versus each.
Mean MSE must be <=1.05 times the delivered model and each distribution control.
Every pooled Brier and log event score must be <=1.05 times every control.
Supported starting groups (>=200 rows, >=3 origins) must have CRPS <=1.10 times
every control. Groups: never-debuted minors, recent debut, current MLB, upper minors,
lower minors, age <23, age >=23, young brief MLB (age <=23, 1–99 current MLB PA).

Events unchanged: no MLB PA anywhere; >=450 PA in >=2 years; >=6 cumulative
batting/replacement wins; >=4 batting/replacement wins in >=2 years. They overlap.
For the latter three events, pooled AND never-debuted AND recent-debut AND young
brief-MLB checks require >=30 observed positives, count ratio [.75,1.25], Brier and
log no worse than F1 AND F0. Insufficient support is explicitly unsupported, not
a pass: broad prospect-upside validation requires all these strata supported.
Report narrower supported tests even if that broad claim fails.

Repeat numerical gates with each sampled prediction set. Main paired-bootstrap
gate uses exact scores; repeat signs of paired CRPS differences and all other gate
booleans across six simulations. Any sign/gate changes with simulation are flagged
unstable and forbid promotion, never choose a best seed. Report joint energy and
interval diagnostics without selecting a winner on them. Cold/stress checks do
not override normal failures or turn inherited references into disjoint baselines.

## C1 feasibility / stopping

Existing vintage-safe 2012+ H1 conditional-rate anchors are reusable inputs, but
are not a full multi-year rate/opportunity residual vector or pure latent ability.
Inventory complete matching forecasts and early support before considering C1.
If missing, stop C1 with a concrete data/model prerequisite; no future-fitted
coefficients, stitched independent horizons, forced means or post-score rescue.
Deliver this ablation, support inventory, tests, result and feasibility decision.
Whole-WAR and control/liability-tail prerequisites still block dollar valuation.
