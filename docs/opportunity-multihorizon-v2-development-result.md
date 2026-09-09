# Opportunity multi-horizon v2 development result

**Decision:** use direct selected models provisionally for horizons 2–4  
**Horizons 5–6:** retain historical fallbacks  
**Production status:** not confirmed

The source gate excluded incomplete 2003–2008 roster/40-man history and every pair
crossing the canceled 2020 minor-league season. This left four chronology-safe rolling
tests for horizons 2, 3 and 4. Horizons 5 and 6 could not meet that minimum and were not
scored.

## Result against the incumbent

The recent-opportunity plus 40-man form passed every precommitted gate for hitters and
pitchers at all three evaluated horizons. It beat its level baseline on distribution
loss in all 24 component/fold comparisons and also beat the existing cohort fallback.

| Component | Horizon | Incumbent Brier | v2 Brier | Incumbent MAE | v2 MAE |
|---|---:|---:|---:|---:|---:|
| Hitter PA | 2 | 0.07465 | 0.06527 | 45.61 | 36.46 |
| Hitter PA | 3 | 0.08631 | 0.08004 | 50.17 | 42.99 |
| Hitter PA | 4 | 0.09123 | 0.08581 | 53.21 | 46.60 |
| Pitcher BF | 2 | 0.08124 | 0.07697 | 39.55 | 36.23 |
| Pitcher BF | 3 | 0.09292 | 0.09037 | 44.48 | 41.70 |
| Pitcher BF | 4 | 0.09723 | 0.09424 | 47.35 | 44.27 |

No selected model was more than 10% worse than the incumbent MAE in any fold; every
worst-fold ratio was below 0.95. The final packages use 35,485–52,885 hitter snapshots
and 39,256–60,324 pitcher snapshots, depending on horizon.

## Boundary

These are direct forecasts from current observed evidence, not recursive forecasts.
They do not use team depth, future team, future level, future role or 2026 outcomes.
Pitcher future-role probabilities remain on the existing historical transition path.

Exact packages and hashes are stored under
`model_artifacts/opportunity-multihorizon-v2-development-2026-09-09/`. The models may
enter only the provisional scenario. Horizons 5 and 6 keep the incumbent fallback.

