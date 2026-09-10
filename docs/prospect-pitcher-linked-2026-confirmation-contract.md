# Prospect pitcher linked-path protected 2026 confirmation

**Frozen before final 2026 outcomes:** 2026-09-10  
**Status:** forecast inputs and evaluator frozen; evaluation waits for final regular-season totals

## Forecasts

Use the exact non-debuted pitcher IDs in the protected 2025 snapshot. Both forecasts
share the already-frozen 2026 opportunity probability.

- Incumbent: its frozen Tango-aged player WAR rate, hurdle/negative-binomial workload,
  event variance and posterior rate variance.
- Linked challenger: the cutoff-valid empirical first-year component-WAR distribution
  of historical prospect pitchers with positive MLB workload, with non-arrival kept as
  an exact zero mass.

No name, team, contract, outside FV, or 2026 outcome enters this package.

## Target and decision

After the 2026 regular season is complete and official totals stabilize, join official
MLB component outcomes to every frozen ID; absence is zero. Score both complete
distributions with CRPS on identical players. Promote the linked performance pool only
if its player-paired CRPS upper 95% bound is below zero, its expected-WAR paired squared-
error upper bound is below zero, absolute aggregate bias is no worse, and no frozen
source-level group with at least 100 players has mean CRPS more than 5% worse. MAE is
descriptive only.

There is no rescue tuning, blend, player exclusion, or subgroup override. This test can
confirm only one-year pre-MLB pitcher performance linkage, not multi-year value.

The target input must contain all 2026 MLB pitchers, not only these prospects, because
the component-WAR calculation needs the full league environment. Required fields are
`season`, `player_id`, `pitching_bf`, `pitching_so`, `pitching_ubb`, `pitching_hbp`,
and `pitching_hr`. The evaluator also requires a final schedule report showing all
scheduled league games complete; it refuses partial-season scoring.
