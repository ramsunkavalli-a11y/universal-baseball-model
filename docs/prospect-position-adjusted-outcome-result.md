# Prospect position-adjusted outcome audit

**Decision:** `withhold_position_component`

Actual MLB position usage was converted with the repo's fixed positional schedule. The local candidate and global baseline use the same batting forecast and arrival probability; only the source of expected position value differs.

| Target year | Position MAE | Baseline | Combined MAE | Baseline | Pass |
|---:|---:|---:|---:|---:|---:|
| 2008 | 0.041 | 0.037 | 0.184 | 0.183 | False |
| 2013 | 0.044 | 0.037 | 0.200 | 0.198 | False |
| 2018 | 0.046 | 0.040 | 0.213 | 0.212 | False |
| 2021 | 0.058 | 0.052 | 0.235 | 0.237 | False |

This remains partial value: defense quality and non-steal baserunning are absent. No public FV, rank, player name, or current-player result was used.
