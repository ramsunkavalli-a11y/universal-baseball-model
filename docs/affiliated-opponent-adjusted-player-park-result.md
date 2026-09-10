# Opponent-adjusted player park test

Status: future-player gate complete; no current value changed.

Exact player home exposure is neutralized with component park effects after correcting
each team-season for its actual home and road opponent mix. The full level translation
is refit at each cutoff and scored on next-season MLB player components. Negative
deltas are better.

| Group | 2024 log-loss delta | 2024 Brier delta | 2025 log-loss delta | 2025 Brier delta | Decision |
|---|---:|---:|---:|---:|---|
| Hitter | -0.000046 | -0.000011 | +0.000019 | -0.000017 | Reject |
| Pitcher | -0.000296 | -0.000084 | -0.000146 | +0.000029 | Reject |

Schedule opponents are game-weighted, not exact matchup-PA weighted. Both time-ordered
years and both proper scores must improve before any current player rate can change.
No outside FV enters the test.
