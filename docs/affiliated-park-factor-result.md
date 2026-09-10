# Affiliated park-factor result

Status: preliminary outer signal only; superseded by component source.

The test estimates a venue effect from total runs in a team's home games divided by
total runs in that same team's road games. Venue estimates are shrunk toward neutral.
The shrinkage amount was selected on 2024, then frozen and checked on 2025.

| Period | Baseline MAE | Park MAE | Baseline RMSE | Park RMSE |
|---|---:|---:|---:|---:|
| 2024 development | 0.1112 | 0.0887 | 0.1406 | 0.1133 |
| 2025 confirmation | 0.1203 | 0.0973 | 0.1527 | 0.1243 |

Selected prior: 50.0 games. The source covers
51,301 official games and 189 venues in the final fit.

This shows persistence of the run environment, but scheduled innings do not equal
actual outs in extra-inning or shortened games. It does not authorize a player
projection change and is superseded by the exact home/away component source.
Opponent strength, weather, and altitude are not separately modeled.
