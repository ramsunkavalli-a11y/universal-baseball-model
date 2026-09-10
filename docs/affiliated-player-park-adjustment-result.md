# Player-level affiliated park adjustment

Status: tested with no current player-value change.

Each player's exact home split is neutralized with the previously selected,
league-season-centered component park effect. His away split is retained. The level
translation is then refit using only data available at the forecast cutoff and scored
on next-season MLB components. Negative score deltas are better.

| Group | 2024 players | 2024 log-loss delta | 2024 Brier delta | 2025 players | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Hitter | 132 | -0.000044 | -0.000012 | 113 | +0.000026 | -0.000016 | Reject |
| Pitcher | 199 | -0.000298 | -0.000088 | 152 | -0.000141 | +0.000029 | Reject |

The test uses no outside FV opinion and does not assume a 50/50 schedule. The park
factor is learned before each target year and applied only to observed home exposure.
Opponent mix is not yet modeled explicitly; failure of either time-ordered fold keeps
the current level-only player model unchanged.
