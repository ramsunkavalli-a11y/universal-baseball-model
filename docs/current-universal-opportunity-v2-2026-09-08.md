# Current universal opportunity v2 integration

**As of:** 2026-09-08  
**Status:** provisional development scenario, not production-confirmed  
**2026 outcomes used for evaluation:** no

The selected hitter and pitcher packages now score the entire current affiliated
universe for 2027. Both use age, broad level, current MLB and minor-league opportunity,
and exact-date 40-man membership. Pitchers also use current role. Neither model uses
team depth, a future team, or future level.

## Current coverage

| Component | Players | Fallback mean | v2 mean | Mean change |
|---|---:|---:|---:|---:|
| Hitter expected PA | 3,940 | 40.48 | 44.84 | +4.36 |
| Pitcher expected BF | 5,276 | 29.38 | 33.04 | +3.66 |

The median player changes only +0.33 PA or +0.20 BF. The models concentrate most of
the additional workload among players whose current evidence supports MLB activity.
The 2027 role probabilities still come from the labeled historical transition model.

## Downstream result

Only 2027 uses the selected v2 workload models. The 2028–2032 paths retain their
existing horizon-specific historical fallbacks.

- Future whole-player WAR is 4,296.04, up 177.24 from the retained fallback.
- The v2 prior lowers the separate remaining-2026 estimate by 1.46 WAR.
- The integrated current-plus-future path has 51,070 annual rows and 8,362 fully
  calculable player paths.
- The same 16 annual contract reviews across 11 players remain unresolved.
- Discounted modeled contract/control value is $3.50 billion, versus $1.66 billion in
  the retained baseline.

The $1.85 billion difference is a sensitivity to player-level opportunity, market
tiers, arbitration salary feedback and control status. It is not a validated change in
league value and the retained baseline is not overwritten.

## Boundary

This completes the Phase 1 current-universe wiring for universal next-season hitter
and pitcher opportunity. It does not confirm either package on untouched outcomes.
Completed 2026 PA and BF remain the protected confirmation targets. Longer horizons
remain explicit historical fallbacks until a separately frozen multi-horizon gate is
tested.

