# Prospect position-history challenger

**Decision:** `withhold_position_history`

A player's most-used official MiLB position is compared only with earlier MLB arrivals at the same level and position. Small groups shrink toward the level average, then conditional position value is multiplied by the separately estimated arrival probability.

| Target | Coverage | Position MAE vs baseline | Combined MAE vs baseline | Pass |
|---:|---:|---:|---:|---:|
| 2013 | 99.8% | 0.042 vs 0.040 | 0.201 vs 0.201 | False |
| 2018 | 99.8% | 0.045 vs 0.041 | 0.212 vs 0.212 | False |
| 2021 | 100.0% | 0.058 vs 0.053 | 0.236 vs 0.237 | False |

The 2008 target is excluded because StatsAPI has no 2003 MiLB fielding source. FV, public ranks, names and current-player results were not used.
