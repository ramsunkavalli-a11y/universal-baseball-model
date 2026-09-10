# Affiliated component park-factor result

Status: outer source test complete; no player value changed.

Home and away player splits are aggregated to team-season components. Each park
effect is a home-minus-away centered log-ratio, centered again within league-season
and partially pooled toward neutral. The prior was selected on 2024; 2025 remained
untouched. Negative score deltas are better.

| Group | Prior | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---|
| Hitter | 5000 | -0.000441 | -0.000048 | -0.000438 | -0.000106 | Pass |
| Pitcher | 5000 | -0.000466 | -0.000145 | -0.000564 | -0.000168 | Pass |

This is stricter than applying one runs factor to every event. It uses the same
component families as the player model and preserves exact player home/away splits
for the next test. Opponent strength is only controlled by comparing each team with
itself; it is not yet an explicit schedule model. A current player adjustment still
requires improvement in future MLB player forecasts.
