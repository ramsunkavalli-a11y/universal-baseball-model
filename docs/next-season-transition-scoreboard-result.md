# Complete next-season transition scoreboard

**Status:** Denominator ready; no playable value changed  
**Source:** Retained official MLB season totals, 2009–2025

## Result

The new table contains 21,742 observed next-season player transitions from 2009–2024.
Of those, 5,018 (23.1%) have no MLB batting or pitching workload in the following
season. The overall next-season return rate is 76.9%.

Another 1,469 source players from 2025 are retained as right censored. Their 2026
outcomes are null rather than zero and are not scored.

This closes the denominator problem in the old adjacent-season aging test. That test
correctly estimated component-rate aging only among players who returned, but its
score could not show the production lost when a player did not return.

## Modeling boundary

- Conditional component skill is scored only when the player has a valid next-season
  workload in that role.
- Return probability and workload remain separate models.
- The combined production score includes every observed source player, with
  non-returners contributing zero production.
- A row with both batting PA and pitching BF is labeled `both_workloads`; this is an
  observed-stat state and not a claim that every such player had a true two-way role.

## Next test

Attach cutoff-safe ages and the incumbent opportunity predictions. Compare no aging,
Tango aging and any new fitted curve on identical rows using both conditional
component loss and unconditional production error. Then run the same joint score for
the component-specific shrinkage challenger. No current player value changes until a
candidate passes both sides.

Reproduce with `scripts/audit_next_season_transitions.py`. The generated transition
table is intentionally outside version control; the builder and exact semantics are
versioned and tested.
