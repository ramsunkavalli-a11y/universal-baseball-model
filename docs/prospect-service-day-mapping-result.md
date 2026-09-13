# Prospect service-day mapping result

**Decision:** `retain_for_next_joint_path_replay`

The test replaces the old assumption that any active MLB season earns 172 service days. It uses only workload, player type and whether the season is the player's first MLB season.

| Test season | Players | Old MAE | Candidate MAE | Old RMSE | Candidate RMSE |
|---:|---:|---:|---:|---:|---:|
| 2023_first_mlb_season | 243 | 102.3 | 22.4 | 113.6 | 30.7 |
| 2024_first_mlb_season | 235 | 106.6 | 21.6 | 118.9 | 30.4 |
| 2024_returning_player | 1,217 | 35.2 | 27.5 | 66.2 | 42.4 |

This is not a controlled-value result. The labeled sample omits players absent from the following opening tracker, so the mapping must next be tested inside the complete career path.
