# Affiliated park-factor result

Status: source promoted for player-rate integration research.

The test estimates a venue effect from total runs in a team's home games divided by
total runs in that same team's road games. Venue estimates are shrunk toward neutral.
The shrinkage amount was selected on 2024, then frozen and checked on 2025.

| Period | Baseline MAE | Park MAE | Baseline RMSE | Park RMSE |
|---|---:|---:|---:|---:|
| 2024 development | 0.1112 | 0.0887 | 0.1406 | 0.1133 |
| 2025 confirmation | 0.1203 | 0.0973 | 0.1527 | 0.1243 |

Selected prior: 50.0 games. The source covers
51,301 official games and 189 venues in the final fit.

This validates only persistence of the run environment. It does not yet authorize a
player projection change: the next step must convert the full-game factor to a player
home/road exposure adjustment and show improvement in translated component rates.
Opponent strength, weather, and altitude are not separately modeled.
