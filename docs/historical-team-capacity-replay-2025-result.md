# Historical team-capacity replay — 2025 result

Status: broad team cap supported; rigid and flexible group constraints rejected.

## What was tested

The already frozen 2025 Opening Day forecasts were assigned to their known Opening Day organizations and scored against full-season 2025 MLB PA or BF. Capacity and position/role shares came only from 2021-2024. Missing outcome rows stayed zero.

- Hitters scored: 3,461; unresolved organization: 430.
- Pitchers scored: 4,570; unresolved organization: 520.
- Unchanged forecasts, team-capped forecasts, and position/role-capped forecasts used identical player cohorts.

## Main scores

Lower is better.

| Players | Version | RMSE | MAE | Predicted / actual workload |
|---|---|---:|---:|---:|
| Hitters | Original | 80.071 | 32.435 | 98.71% |
| Hitters | Team cap | 80.031 | 32.276 | 95.42% |
| Hitters | Team + position cap | 81.488 | 32.426 | 86.34% |
| Pitchers | Original | 79.836 | 30.996 | 96.55% |
| Pitchers | Team cap | 79.481 | 30.804 | 94.20% |
| Pitchers | Team + role cap | 80.069 | 30.604 | 86.82% |

The team-only pitcher improvement survived the 30-team clustered bootstrap:

- RMSE change: -0.355 BF; 95% interval -0.721 to -0.063.
- MAE change: -0.192 BF; 95% interval -0.391 to -0.045.

The team-only hitter changes were small and uncertain:

- RMSE change: -0.040 PA; 95% interval -0.232 to 0.178.
- MAE change: -0.160 PA; 95% interval -0.411 to 0.029.

## Decision

Keep the broad team-cap layer. It modestly improved the pitcher forecast and did not materially harm hitters. Treat its hitter benefit as unproven because both intervals include zero.

Reject the rigid primary-position hitter layer for display. It worsened RMSE by 1.417 PA, with the 95% interval entirely above zero (0.257 to 2.666). Middle infield and corner infield were the largest harms. It turned a nearly balanced full-cohort hitter forecast into a 13.66% workload shortfall.

Do not promote the rigid pitcher-role layer. It improved MAE by 0.392 BF, but RMSE worsened by 0.233 and its interval crossed zero. Every scored pitcher was reduced because every player carried some probability in a crowded role. It created a 13.18% workload shortfall.

## Lesson and next design

The failure is structural, not a reason to retune the historical shares. Real rosters move unused opportunity across positions and pitcher roles. A strict set of independent caps throws away workload even when another bucket has space.

The next challenger should therefore:

1. preserve the broad team cap;
2. represent multi-position and multi-role flexibility using only dated StatsAPI usage;
3. reassign unused capacity before reducing a player's total;
4. develop the transition/eligibility rules on pre-2025 seasons;
5. score once on the same 2025 replay without tuning on these results.

This remains team context only. No skill, WAR rate, contract value, Model FV, or organization-neutral trade value changed.

A later flexible challenger used supported 2021–2024 multi-position and adjacent-role
movement to reassign unused capacity before cutting players. It removed most of the
rigid-cap damage, but still did not beat the broad team cap on both RMSE and MAE for
either component. Aggregate group-cap research is therefore closed on 2025. See the
[flexible result](flexible-team-capacity-replay-2025-result.md).

Machine-readable detail: `docs/historical-team-capacity-replay-2025-result.json`.
