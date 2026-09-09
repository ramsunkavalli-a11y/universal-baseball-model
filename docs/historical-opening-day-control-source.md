# Historical Opening Day control source

**Status:** accepted as a retrospective Phase 1 service/options baseline source  
**Captured:** 2026-09-09

FanGraphs' historical RosterResource Opening Day Tracker exposes a league-wide,
MLBAM-keyed control snapshot. The row contract includes pre-season service time,
options or Rule 5 status, 40-man status, organization and projected opening role.
The adapter reads the server-rendered data document directly and does not require
name matching.

## Captured coverage

| Season | Unique players | Service balances | Option counts | 40-man players | Teams |
|---|---:|---:|---:|---:|---:|
| 2024 | 2,012 | 1,634 | 1,235 | 1,187 | 30 |
| 2025 | 2,024 | 1,615 | 1,198 | 1,191 | 30 |

One duplicated 2025 MLBAM identity represented two roster-role rows with identical
control facts; it was safely collapsed. Option counts remain separate from `R5`
and future `Dec'YY` Rule 5 labels.

## Use and limits

This closes most of the verified opening-service gap for MLB and near-MLB players
at the first two historical checkpoints. Players outside the tracker still remain
in the official affiliated universe. They receive zero opening service only when
official no-debut evidence supports it; an earlier debut without a tracker balance
remains review.

The pages were retrieved in 2026. They support
`retrospective_event_cutoff`, not a claim that the exact page was publicly known in
the same form on the original opening date. Raw HTML and normalized bulk records
remain private pending terms review. User-downloaded member workbooks will be used
as stable licensed validation copies, not silently substituted as a different
source.

This source does not include salary or future contract obligations. Historical
contract reconstruction remains the other material Step 8 input.

Implementation: `src/universal_baseball/fangraphs_opening_day_source.py` and
`scripts/capture_fangraphs_opening_day_tracker.py`.
