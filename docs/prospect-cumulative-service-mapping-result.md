# Prospect cumulative service mapping

The endpoint audit covers 547 players with exact FanGraphs 2025 opening service balances.

| Target | Full-season shortcut MAE | Workload-map MAE | Full-season RMSE | Workload-map RMSE |
|---|---:|---:|---:|---:|
| Raw cumulative days | 215.1 | 99.2 | 270.1 | 136.8 |
| Six-year capped days | 97.2 | 47.8 | 177.1 | 90.0 |

Control-exhaustion accuracy is 92.5% for the workload map versus 70.0% for the shortcut.

This remains diagnostic. Zero-workload seasons are forced to zero because the current historical roster feed cannot distinguish an injured controlled player from someone out of baseball. That choice is conservative and its undercount remains visible in bias.
