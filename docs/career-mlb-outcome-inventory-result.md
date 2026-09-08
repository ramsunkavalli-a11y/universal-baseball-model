# MLB career-outcome inventory result

Completed 2026-09-07 from the official MLB Stats API. This is a Phase 1 outcome
backbone, not a player-universe or forecast result.

## Frozen materialization

- Complete calendar seasons: 2015–2024
- Raw source captures: 52
- Batting player-seasons: 10,585
- Pitching player-seasons: 8,095
- Distinct players with an observed MLB batting or pitching outcome: 3,777
- Total batting plate appearances: 1,722,088
- Total pitching batters faced: 1,722,088
- Protected 2026 accessed: no
- Incomplete current season accessed: no

The matching batting-PA and pitching-BF totals provide a high-level conservation
check. Canonical output hashes are:

- batting: `6d1ebcc11e01a9aa9a38a9a998b29be5fd063cf51b607926d168a7f65d2e2f66`
- pitching: `e762cdf92d7a2d5c5ee0a81211a67e15b3a4a3cfa8b228fe623cb58df6298e5c`
- observed careers: `4a1625de69d497374a328395c6de4ddaec5b9becc828415609feaea66dffd844`

## Interpretation

The materialization provides mature aggregate MLB batting, pitching and opportunity
labels. The career-panel builder completes player × future-season grids: absence in
an already complete season is an observed zero, while seasons beyond the complete
observation prefix are explicitly right-censored. Two-way batting and pitching
outcomes remain separate.

It does not identify pre-MLB non-arrivals because that requires a dated historical
affiliated-player denominator. It also does not infer retirement from disappearance,
or convert calendar seasons to service/control years. Those are later joins, not safe
inferences from MLB outcomes alone.

Reproduction: `python scripts/materialize_career_mlb_outcome_inventory.py`.
Generated data and raw captures remain ignored; the script, contract and hashes are
the committed audit trail.
