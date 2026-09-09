# Current workload and role signal

**Status:** accepted Phase 1 rest-of-season adjustment  
**Current snapshot:** 2026-09-08

## Decision

Use official MLB workload from the most recent 30 calendar days to redistribute the
existing rest-of-season PA and BF totals among players. Recent workload is regressed
with 25 PA/BF before it affects the allocation. The adjustment preserves the prior
league total exactly, applies no player cap, and uses no team depth chart.

This is a current usage and role signal, not a new talent estimate. Conditional WAR
rates remain separate. Current official injury evidence is applied afterward.

## Historical check

The audit uses September 8 cutoffs in 2022-2025. It compares remaining regular-season
PA/BF with the existing season-to-date/prior-year workload blend. The challenger was
selected on 2022-2024 and confirmed once on 2025.

In the 2025 confirmation:

- hitter MAE improved from 14.76 to 12.01 PA per player;
- pitcher MAE improved from 16.08 to 13.49 BF per player;
- hitter RMSE improved from 21.26 to 17.04 PA;
- pitcher RMSE improved from 23.41 to 19.00 BF; and
- total workload stayed exactly equal to the baseline forecast.

The same 25-exposure candidate was best for both components in development. Raw
recent pace was rejected because it overstated aggregate work; only the baseline-total
redistribution was promoted.

## Current effect

The live source contains 512 recent hitters and 568 recent pitchers over an average
26.93 team games. The redistribution keeps 21,596.6 hitter PA and 20,597.7 pitcher BF
unchanged. It moves at most 35.42 PA or 36.90 BF for one player. Because work shifts
toward players with different talent rates, unadjusted remaining WAR changes from the
prior 112.23 snapshot to 114.35 before availability. The injury-adjusted point is
105.13 WAR, with a 102.07 to 114.40 availability-only range.

## Boundary

The baseline total itself is not a finite-roster allocation model. Phase 2 can test
team-level conservation, transaction timing and shorter windows. Those changes must
remain separate from intrinsic future-season opportunity and must validate
chronologically before replacing this method.

