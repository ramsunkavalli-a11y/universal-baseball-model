# Certify MLB defensive measurements by actual position

2026-10-06. After the completed support audit, test the official Fielding Run
Value leaderboard's position grouping on 2022 and 2025 only. This is a source
pilot, not a fit or an accuracy experiment. No 2026 results or forecasts are used.

The saved historical page exposes `group-by-position`; its public query builder
joins selected splits into `groupBy`. Request `type=fielder`, explicit matching
`seasonStart` and `seasonEnd`, `groupBy=position`, zero minimum innings/results.
Download same-vintage unsplit totals for both years as independent recomposition
anchors, preserving the earlier certified aggregates unchanged.

Require the response to confirm the requested year and position grouping, unique
player-position rows, valid position IDs, and position-specific exposure—not
the player's full-season innings repeated at every position. Sum split defensive
outs and range runs to the same-vintage player totals. Report nulls separately;
an absent component at catcher/pitcher is not measured zero infield range.
Verify the split position's exposure against dated official usage and the
unsplit source's position-out columns. Keep revisions from old captures distinct
from split errors. Use 1e-6 runs and exact native outs as recomposition tolerances;
official/native out differences are reported, not automatically assumed bugs.

Fixed source walkthroughs are Witt, Mateo, Edwards and Rafaela at each pilot
season, without forcing missing rows. Show actual positional outs and range
runs, summed totals, and the difference from the earlier purity rule. No gains,
misses or downstream projections are invented for a source audit.

If the source truly separates measurements, it is eligible for a dated-source
extension and fresh support audit, not automatic talent-model use. Otherwise
record the exact mismatch rather than apportion aggregate runs or loosen purity.
Origin metadata repair and the missing older long-window inputs remain separate
open tasks. Preserve all existing results and production files.
