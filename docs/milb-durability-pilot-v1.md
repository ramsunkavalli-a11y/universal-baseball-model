# Small minor-league availability pilot

Fixed before scoring, 2026-09-22. One screen, no model rollout or broad new system.

Use recovered 2021–2024 all-level fielding positions and affiliated season batting.
Eligible origins 2022–2024: no prior MLB PA, >=100 PA in each of the last two years,
all affiliated PA at one of AAA/AA/High-A/Single-A in each year, the same level in
both years, and known historical positions. Sum team stints within that level.
Exclude movers, short-season leagues and rookies from this narrow screen rather
than misclassifying partial promoted stints or 2020 cancellation as durability.
Two observed seasons still do not certify full-year roster assignment or health.

Reference workload is the contemporaneous level/position 75th percentile among
players with >=100 PA at that level; require >=20 peers, otherwise fall back to the
level-season group. All inputs are already observed at December 31. Shortfall is
max(0, 1 - observed PA/reference). Repeated shortfall is the minimum of the two
seasonal gaps. It is an availability/role proxy, never an injury diagnosis.

"Productive" is current OPS >= the level-season 67th percentile among >=100-PA
players. This is a small unadjusted screen, not park-neutral talent certification.
Retain all eligible players for fitting; score the productive subgroup separately.
Never select players using future MLB outcomes.

Chronological predictions: train 2022 to predict origin 2023's 2024 outcome; train
2022–2023 to predict origin 2024's 2025 outcome. Each training next-year label is
already mature at the prediction cutoff. All 2026 outcomes remain protected.

Fixed standardized/imputed logistic C=.1, max_iter=2000, seed 417. Baseline uses
the existing 77 age/level/performance/PA-history/40-man features plus position
indicators and the two reference workloads. Candidate adds the two gaps and their
minimum. No tuning or threshold search. Targets: any MLB PA next year (primary)
and >=200 MLB PA next year (secondary opportunity, NOT proof of career durability).

Report both folds, Brier/log loss, player-cluster intervals for loss changes, support,
and productive subgroup results. Call it promising only if primary Brier/log loss
improve in both folds and pooled productive-player intervals favor the candidate.
Sparse support, ambiguous signs or failure means no integration and no claim of
benefit. No model/forecast changes even if promising. A negative result does not
resolve injured players with <100 PA, promoted players, earlier eras, or long-term
career survival. Save the small script, predictions, checks and concise result.
