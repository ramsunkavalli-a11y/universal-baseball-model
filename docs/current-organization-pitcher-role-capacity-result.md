# Current-organization pitcher role capacity result

Status: research layer complete; not used in portable player value.

## Result

The 2021-2024 development data produced these normalized shares of one team's pitching workload:

| Role | Frozen share | Historical 10th-90th percentile |
|---|---:|---:|
| Starter | 57.32% | 49.22%-62.97% |
| Reliever | 30.49% | 21.62%-37.03% |
| Swingman | 12.18% | 3.14%-23.29% |

The untouched 2025 season was reasonably consistent with the frozen split. Mean team total variation was 7.20 percentage points; the 90th percentile was 11.12 points. No role was consistently missed by more than 2.02 points across teams.

## Current-team effect

| Season | Team-capped BF | Role-capped BF | Further reduction |
|---|---:|---:|---:|
| 2027 | 150,467 | 142,157 | 8,310 |
| 2028 | 143,897 | 136,477 | 7,420 |
| 2029 | 133,281 | 127,454 | 5,826 |
| 2030 | 121,956 | 118,610 | 3,346 |
| 2031 | 94,715 | 94,028 | 687 |
| 2032 | 2,433 | 2,433 | 0 |

Across the six seasons, relief components exceeded their team-role capacity in 89 of 180 team-seasons and swingman components did so in 39. Starter components never exceeded capacity. The lowest team-role scales were 0.632 for relief and 0.761 for swingman.

Many player rows receive a small reduction because role probabilities are kept fractional. That is intended: the method does not falsely declare an uncertain pitcher to be a certain starter or reliever.

## Interpretation

The existing pitcher paths fit the available starter workload. Their larger roster-context conflict is accumulated relief probability. This supports using role capacity when showing how a specific current organization could fit all of its controlled pitchers.

It does not support cutting pitcher skill, WAR rate, or organization-neutral trade value. Open role capacity remains available to free agents, trades, replacement players, and pitchers outside the controlled set. Historical roster-construction replay is still required before this layer is promoted into a displayed team-fit result.

Machine-readable detail: `docs/current-organization-pitcher-role-capacity-result.json`.

