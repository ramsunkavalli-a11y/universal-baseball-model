# Current baserunning rates — 2026-09-08

Status: **frozen Player Value v1 model reused in the Phase 1 hitter path**

The current hitter forecast now uses the repo's already-selected baserunning models:

- `B2_k5` for steal attempts;
- `B2_k45` for steal success;
- `A2_k25` for non-steal advancement; and
- no separate GIDP residual, matching the frozen v1 decision.

No new candidate was fit. Official StatsAPI component counts provide 2023–2026 steal
history for MLB and all affiliated levels. Four league-wide Baseball Savant downloads
provide runner advancement runs and opportunities. The incomplete 2026 season is
predictor evidence only.

## Current result

The model produces one centered run rate for every one of 3,940 hitters in each season
from 2027 through 2032. Coverage is:

| Evidence | Player-years |
|---|---:|
| Steal and advancement | 2,022 |
| Steal only | 9,239 |
| Population neutral | 12,379 |

In 2027, 3,776 hitters have recent evidence. The observed range is -5.43 to +6.18
runs per 600 PA. It narrows in 2028 and 2029 as older evidence receives less weight.
The frozen model has a three-season lookback, so 2030–2032 return to the centered
population value rather than carrying stale speed evidence indefinitely.

## Source boundary

The current StatsAPI bulk table identifies minor-league level, not the exact league
used in the original research files. Current MiLB environment adjustment is therefore
done at the StatsAPI sport/level group. This is disclosed source adaptation, not a
claim of byte-for-byte reproduction of the earlier research input.

The 2025 completed MLB environment supplies the league reference: 182,926 PA, 4,429
steal attempts, 3,440 successful steals and 12,993 non-steal advancement opportunities.
Rates remain centered against that environment. No value is capped or manually edited.

## Remaining gap

Defense remains the only blanket zero hitter component. Baserunning is now added to
conditional WAR before participation and workload are applied.
