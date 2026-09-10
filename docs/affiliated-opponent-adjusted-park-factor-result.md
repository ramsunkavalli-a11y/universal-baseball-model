# Opponent-adjusted affiliated component parks

Status: outer environment test complete; no player value changed.

Each team's home-minus-away component line is corrected for the component quality of
the actual opponents on its home and road schedules. Effects remain centered within
league-season and pooled toward neutral. Prior strength is selected on 2024 and
checked unchanged on 2025. Negative deltas are better.

| Group | Prior | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---:|---|
| Hitter | 5000 | -0.000446 | -0.000050 | -0.000437 | -0.000107 | Pass |
| Pitcher | 5000 | -0.000466 | -0.000141 | -0.000558 | -0.000173 | Pass |

Opponent profiles are weighted by games because exact matchup PA/BF is not present in
the season split source. This is more defensible than ignoring opponent mix, but a
passing environment test only authorizes the separate future-player gate.
