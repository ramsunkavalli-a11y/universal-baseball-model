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

## Direct multi-year extension

Separate direct models passed the frozen gate for horizons 2–4. They use only current
observed evidence and never feed an earlier forecast back as data. Horizons 5–6 retain
their existing historical fallbacks because older official source coverage cannot
support four chronology-safe tests.

Current mean changes versus the fallback are +6.99 PA and +6.00 BF at horizon 2,
-0.05 PA and +0.56 BF at horizon 3, and +0.35 PA and -0.06 BF at horizon 4. Later
league-wide means are therefore nearly unchanged; the validated gain is mostly better
player-level allocation.

## Downstream result

- Future whole-player WAR is 4,683.39, up 564.59 from the retained fallback: +177.24
  in 2027, +219.19 in 2028, +86.39 in 2029 and +81.78 in 2030.
- The v2 prior lowers the separate remaining-2026 estimate by 1.46 WAR.
- The integrated current-plus-future path has 51,076 annual rows and 8,363 fully
  calculable player paths.
- The same 16 annual contract reviews across 11 players remain unresolved.
- Discounted modeled contract/control value is $5.893 billion, versus $1.66 billion in
  the retained baseline.

The $4.24 billion difference is a sensitivity to player-level opportunity, market
tiers, arbitration salary feedback and control status. It is not a validated change in
league value and the retained baseline is not overwritten.

## Boundary

This completes the Phase 1 current-universe wiring for universal next-season hitter
and pitcher opportunity. It does not confirm either package on untouched outcomes.
Completed 2026 PA and BF remain the protected confirmation targets. Horizons 5–6
remain explicit historical fallbacks.
