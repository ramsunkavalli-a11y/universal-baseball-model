# Career outcome panel contract v0.1

**Status:** Implemented structural foundation; 2015–2024 MLB outcomes materialized
**Roadmap step:** Phase 1, Step 2

## Decision

Use a fixed player denominator crossed with future calendar seasons. Join certified
complete MLB batting and pitching season outcomes onto that grid.

- No MLB batting PA and no MLB pitching BF in a certified complete season is an
  observed zero-participation outcome.
- A season beyond the certified complete-data boundary is right censored. Its outcome
  fields remain null and cannot be interpreted as failure or zero production.
- Hitting and pitching remain separate count families while sharing one player-season
  participation row, so two-way players are represented without duplication.
- Multiple team/league rows may sum to player-season totals before panel construction.
- Completed seasons must be a contiguous prefix of the requested horizon. This prevents
  a partial or unavailable intervening season from being silently treated as complete.

The initial horizon is calendar-season follow-up, not a claim about MLB service years
or years of club control. Those are later rights/cost-path fields.

## Source boundary

The builder does not declare a source season complete. A source-certification step must
make that assertion and provide standardized nonnegative counts. Existing certified
MLB batting and pitching aggregate adapters should be reused. Full pitch-by-pitch
materialization is unnecessary for this career-label backbone.

## Next materialization

Inventory the longest mutually usable aggregate MLB batting and pitching history, then
materialize older cutoff cohorts whose entire declared follow-up window is complete.
Report source start/end, missing seasons, player counts, non-arrivals and censored rows.
Do not access protected 2026 evaluation outcomes.
