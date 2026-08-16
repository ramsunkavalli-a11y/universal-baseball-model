# ADR 014: Use modest same-level pooling for AAA Performance-bin values

**Status:** Accepted for foundation architecture  
**Date:** 2026-08-15

## Context

ADR 012 froze state replay and RE24 mechanics but deliberately left production Performance-bin value estimation open. Direct league-season bin means from modest official-PBP samples were noisy enough that a pooling rule had to earn its place predictively rather than be assumed.

Three leakage-safe diagnostics now address that question for Triple-A.

### 1. 2025 AAA split-half diagnostic

Using 45 games per PCL and IL environment, alternating 23-vs-22-game halves were compared. Candidate halves supplied league estimates; reference halves were held out. The shrinkage prior for a target league/bin used only the candidate half of the *other* AAA league.

Direct AAA split-half error was:

- MAE: **0.0881 runs**;
- RMSE: **0.1112**;
- occurrence-weighted MAE: **0.0823**.

Positive prior-equivalent strengths **5, 10, 25, 50, 75, and 100** improved all three principal summaries. The lowest split-half MAE occurred at 75, but the broad robust region mattered more than that single optimum.

### 2. 2025 AAA five-fold predictive validation

The same 45 games per league were sorted chronologically and assigned to five interleaved folds. For each fold, 36 target-league games estimated its RE24 matrix and direct bin means; the other AAA league's 36 training games supplied the same-bin prior; nine target-league games were held out completely and valued with the target training RE24 matrix. Every selected game was held out once.

Direct AAA error was:

- cell MAE: **0.0563**;
- cell RMSE: **0.0735**;
- event MAE: **0.4304**;
- event RMSE: **0.5124**.

Again, positive strengths **5, 10, 25, 50, 75, and 100** improved all four summaries. Strength 25 had the lowest cell MAE among the conservative robust candidates selected by the diagnostic.

### 3. Pre-specified independent 2024 AAA confirmation

To avoid choosing a constant after observing another dataset, **25 prior-equivalent occurrences was pre-specified before the 2024 audit**. A separate `2024_6_aaa_pbp.csv` source snapshot supplied 45 PCL and 45 IL games. The same five-fold design was used.

Direct 2024 AAA error was:

- cell MAE: **0.080304**;
- cell RMSE: **0.115283**;
- event MAE: **0.324536**;
- event RMSE: **0.485045**.

With the pre-specified strength 25:

- cell MAE: **0.079219**;
- cell RMSE: **0.111472**;
- event MAE: **0.324451**;
- event RMSE: **0.484600**.

All four metrics improved. The secondary 2024 grid also placed strengths **5, 10, 25, and 50** in the robust region. Thus 25 lies inside the robust region in all three AAA tests and passed an independent-season confirmation without post-hoc re-selection.

The improvements are intentionally characterized as modest. The reason to pool is consistency and reduced estimator noise, not a claim that shrinkage creates a large predictive gain.

Rookie/complex evidence is different. Its original split-half diagnostic found no positive strength that improved MAE, RMSE, and occurrence-weighted MAE together, while the five-fold audit found only a small benefit at strengths 5–25. That disagreement is not sufficient to freeze positive Rookie/complex shrinkage.

## Decision

For **AAA league-season Performance-bin run-value estimation**, use same-bin partial pooling toward the peer AAA league with a fixed strength of **25 prior-equivalent occurrences**:

`pooled_mean = (league_mean * league_bin_n + peer_aaa_mean * 25) / (league_bin_n + 25)`

where:

1. `league_mean` and `league_bin_n` come from the target AAA league-season's certified calibration sample;
2. `peer_aaa_mean` is the same Performance bin from the other AAA league in the **same season** and certified calibration design;
3. the target league never contributes to its own prior;
4. no held-out/evaluation data contribute to the prior during validation;
5. if a same-season peer AAA estimate is unavailable, do **not** silently substitute an all-MiLB, Rookie, adjacent-season, or MLB prior; leave the value unpooled and record the reduced evidence state;
6. the fixed strength 25 applies to **bin-value estimation only**. It is not player-level projection shrinkage and is not an empirical-Bayes claim about player talent.

Use at least the validated information scale—**45 selected games per AAA league-season when available**—for the initial calibrated implementation. More certified games may be used; the fixed prior-equivalent count naturally exerts less influence as target-bin sample size grows. Fewer-game production calibration requires a separate validation rather than extrapolation from this gate.

For **Rookie/complex Performance-bin values**, retain direct league-season estimates for the first production transform. Do not apply positive shrinkage until an independent validation resolves the conflicting diagnostics.

## Consequences

- A universal MiLB pooling constant is rejected.
- AAA has a simple, interpretable, independently confirmed regularizer rather than a fitted black-box hierarchy.
- Exact sampled bin weights remain data products, not hard-coded architecture. This ADR freezes the estimator form and evidence requirements.
- The peer prior is same-season and same-level only. Missing peer evidence remains visible instead of triggering an unvalidated fallback.
- Rookie/complex direct values should carry stronger uncertainty/quality metadata because positive shrinkage has not been certified there.
- The remaining Performance-value architecture gate is the foul-air eligibility rule for the 12-bin skill view; after that, the first production Performance transform can be frozen and backfill implementation can begin.
