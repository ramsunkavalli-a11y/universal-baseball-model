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

## Member workbook validation

User-downloaded member workbooks add a 2023 source and preserve historical projected
PA, projected IP and age. The private normalized coverage is:

| Season | Unique players | Service balances | Option counts | Projected PA | Projected IP |
|---|---:|---:|---:|---:|---:|
| 2023 | 2,065 | 1,673 | 1,288 | 463 | 491 |
| 2024 | 2,009 | 1,631 | 1,232 | 534 | 578 |
| 2025 | 2,019 | 1,610 | 1,193 | 610 | 684 |

The 2024 workbook is an exact subset of the public capture: all 2,009 common MLBAM
rows agree on service, options/Rule 5 state, projected role, team, name and FanGraphs
ID. The 2025 workbook has the same exact agreement for all 2,019 common rows. The
public captures contain three and five additional players, respectively, so they
remain the primary 2024–2025 control source. The workbooks are independent validation
copies and add historical workload projections. The 2023 workbook is the primary
available Opening Day source for that earlier retrospective checkpoint.

Workbook rows do not expose FanGraphs team ID, 40-man flag or raw roster status.
The importer leaves those fields unknown rather than inferring them from projected
role. Raw workbooks and normalized bulk tables remain private.

## Use and limits

This closes most of the verified opening-service gap for MLB and near-MLB players
at the first two historical checkpoints. Players outside the tracker still remain
in the official affiliated universe. They receive zero opening service only when
official no-debut evidence supports it; an earlier debut without a tracker balance
remains review.

The pages and workbooks were retrieved in 2026. They support
`retrospective_event_cutoff`, not a claim that the exact source was publicly known in
the same form on the original opening date. Raw files and normalized bulk records
remain private pending terms review.

This source does not include salary or future contract obligations. Historical
contract reconstruction remains the other material Step 8 input.

Implementation: `src/universal_baseball/fangraphs_opening_day_source.py` and
`scripts/capture_fangraphs_opening_day_tracker.py`. Local member workbooks use
`scripts/import_fangraphs_opening_day_workbook.py`.
