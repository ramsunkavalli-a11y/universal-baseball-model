# O2026D: one-year MLB batting opportunity baseline

Frozen 2026-09-06 before fetching target participation or fitting this batch.
Development only; 2022–2024 have already been inspected for other tasks.
No 2025 or protected 2026 outcomes. No value/WAR promotion.

## Population and labels

For forecast season Y, include every player with positive official batting PA
in the existing unfiltered affiliated player-season table in Y-1, plus every
player with positive official MLB batting PA in Y-1. Do not condition membership
on future participation, modeling eligibility, or existence of an ability forecast.
This is a prior-season-active population, not a complete prospect/roster universe.
New signees without prior observed play and players inactive for the entire prior
season remain outside scope; quantify target participants outside the cohort.
Pitchers who batted remain included; the 2022 DH change is a known cohort shift.

Arrival here means **at least one regular-season MLB batting PA**, not a roster
call-up, debut, defensive appearance, or first lifetime MLB participation.
Targets: any MLB PA, at least 100 MLB PA, and total MLB PA in Y. Zero labels require
complete paginated official MLB season hitting totals. Require unique player IDs,
stable declared page totals, exact returned row counts, and exact MLB-wide vs
summed AL/NL player PA agreement (including cross-league trades). Save raw responses
and hashes. Missing or inconsistent coverage stops labeling; no PBP-absence zeros.

## Fixed baseline

2022 is training warm-up only. Predict 2023 using 2022 cohorts/outcomes; predict
2024 using 2022–2023. Every feature uses Y-1 only. No tuning or alternative search.
Primary prior level is the level with most prior-season official PA (alphabetical
tie break); replace MLB PBP totals with official bulk totals before computing it.
Prior MLB exposure is 0, 1–99, or 100+ PA.

REFERENCE: earlier-season empirical means within prior MLB exposure bucket.
LEVEL: empirical means within (primary prior level, prior MLB exposure), with
50 pseudo-players at the REFERENCE means. Unseen cells use REFERENCE; unseen
exposure buckets use earlier overall means. Apply the same formula to both binary
targets and PA. This yields nested probabilities and expected PA including zeros.
Clip probabilities to [1e-6, 1-1e-6] for log scoring only.

Save cohort/features and predictions before joining current target outcomes.
Record source hashes, learned cell means, and prediction hashes. Evaluate equal
player Brier/log loss, PA MAE/RMSE and mean bias for all players, prior MLB PA=0,
prior MLB PA>0, each prior level, and no previous ability forecast. Report counts,
base rates, calibration by predicted probability bins, and participant coverage.
No post-outcome exclusion. Show pooled paired player-cluster uncertainty for the
any-PA Brier difference (LEVEL minus REFERENCE), 1,000 draws, seed 260906.

## Decision

This establishes a reproducible benchmark, not a release gate or a claim that
opportunity explains batting error. LEVEL is useful beyond REFERENCE only if
pooled any-PA Brier improves and neither active year worsens by over 2%; also
disclose all exposure/value errors. Do not retune after failure. Before more
complex alternatives, assess cohort omissions and whether prior role/age are
available without future information. Full no-history roster coverage remains
an explicit required expansion before claiming universal prospect coverage.
