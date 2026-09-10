# Prospect player-level position result

Status: passed as a private sensitivity; not promoted to the playable model.

## Historical result

The chronology-safe test trained only on completed next-season outcomes. It selected
the exact-position, age, level, and workload model on 2023-to-2024 evidence, then
scored it once on 455 arriving hitters from 2024-to-2025.

| Group | Baseline MAE | Candidate MAE | Baseline RMSE | Candidate RMSE |
|---|---:|---:|---:|---:|
| All 455 hitters | 4.020 | 3.568 | 5.424 | 4.935 |
| 69 shortstop-origin hitters | 3.104 | 2.392 | 4.200 | 3.307 |

All four required errors improved. Player bootstraps favored the candidate in at
least 99.7% of samples. A separate shortstop-retention diagnostic improved log loss
from 0.670 to 0.530 and Brier score from 0.238 to 0.179. Only 36.2% of the outer
group's shortstop-origin players remained primarily at shortstop in MLB the next
season.

The candidate also improved MAE for 2B, C, CF, DH, LF, RF, and SS origins. It worsened
1B MAE/RMSE, 3B MAE, and RF RMSE. Those subgroup misses block a production change
even though the predeclared overall and shortstop gate passed.

## Current-player sensitivity

The private sensitivity covers 2,024 current pre-MLB hitters with exact birth date,
level, and fielding usage. It changes only the position-run part of each player's
existing nested career WAR, then uses the same FV-to-dollar benchmark as the playable
model.

- FanGraphs top-50 overlap moves from 10 to 12 as a diagnostic, not a target.
- Top-50 composition moves from 49 hitters / 1 pitcher to 48 hitters / 2 pitchers.
- Diego Velasquez, Brandon Butterworth, Dub Gleed, and Jett Williams leave the top 50
  for explainable position-usage reasons.
- Jesús Made and Leo De Vries remain near the top even after roughly 0.6-0.7 WAR is
  removed, because their value is not solely position-driven.
- Several unranked hitters still enter as other players fall. That confirms the next
  structural issue is arrival/workload versus demonstrated skill, not position alone.

No public FV, public rank, organization depth, quota, or named-player adjustment was
used. Production remains unchanged. Machine-readable results are in
`docs/prospect-shortstop-retention-result.json` and
`docs/prospect-shortstop-sensitivity-result.json`.

