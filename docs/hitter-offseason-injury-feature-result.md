# Hitter offseason injury-history result

Status: **tested; not selected**

## What was tested

Official MLB transactions from 2015-2024 were replayed only through each October 15
forecast cutoff. The reconstruction supports both the older “disabled list” wording
and the current “injured list” wording. It measures placements, activations, days on
the list in the prior one and two years, 60-day placements, current IL state, and days
in the current spell. It does not infer a diagnosis.

The first challenger added those fields to every engine in the already-selected
roster-aware workload ensemble. Across the same six forward tests:

| Workload model | PA RMSE | PA MAE | Brier | Log loss |
|---|---:|---:|---:|---:|
| Roster-aware baseline | **60.816** | **20.843** | **0.04848** | **0.16093** |
| Add injury history to all engines | 60.701 | 20.899 | 0.04865 | 0.16151 |

RMSE improved by 0.116 PA, but its 95% range was -0.323 to +0.083. MAE and both
arrival-probability scores worsened. Three seasons improved and three worsened.

A narrower second test left arrival probability and all non-established players
unchanged. It learned a chronological ridge correction to PA only for current MLB
players with public IL days in the prior two years.

| Workload model | PA RMSE | PA MAE |
|---|---:|---:|
| Roster-aware baseline | **60.816** | **20.843** |
| Injury-only residual correction | 60.778 | 20.937 |

The 0.039 RMSE improvement was uncertain, and MAE again worsened. The correction
mostly removed average underprediction for injured established players without
improving individual accuracy enough.

## Decision

Do not add the current injury-history package to the hitter workload model. The public
history has some signal for established-player PA, but it does not improve the full
set of required measures beyond age, performance, workload, level, and 40-man status.

Keep the transaction reconstruction and disabled-list compatibility as reusable data.
A future injury challenger needs genuinely better information—consistent diagnosis or
procedure categories, recovery state, or another validated availability target—not
more tuning of the same broad counts on exposed seasons.

No 2026 result was accessed.
