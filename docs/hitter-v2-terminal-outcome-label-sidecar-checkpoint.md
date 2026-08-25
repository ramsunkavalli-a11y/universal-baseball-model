# Hitter v2 terminal-outcome label sidecar checkpoint

Status: **SOURCE GATE PASSED; J0 IMPLEMENTATION NOT YET AUTHORIZED**  
Date: 2026-08-24

## Scientific outcome

The source gate supplies one deterministic 14-category terminal outcome for
3,796,988 of 3,810,001 certified matchup-sidecar PAs (99.6585%). It then applies
the stricter rule: a PA becomes context-label ready only when every direct label
in that player-game exactly reproduces all 14 independently certified outcome
counts and the prior matchup/source gate also passed. Under that rule, 3,657,915
PAs in 929,254 player-games are ready (96.0082%).

All frozen thresholds pass. MLB is 100% ready in all four seasons. The lowest
MLB-through-Single-A cell is 2024 Single-A at 94.2576%, above 90%. The lowest
rookie/complex cell is 2024 at 93.6710%, above 85%. No player is removed from the
universal B1 forecast when a label or reconciliation fails.

## Source-semantic correction

The first source-only run failed: direct labeling was 94.72%, but whole-game
reconciliation retained only 2,989,895 PAs (78.4749%). Inspection of unresolved
source descriptions showed that the literal, unambiguous phrase `called out on
strikes` was not included in the conservative K vocabulary. The classifier was
amended to map that exact phrase to K, then the source gate was rerun.

This correction occurred before candidate implementation, fitting, scoring, or
target evaluation. It did not use player-game residual totals to choose labels.
The failed report hash and both before/after counts are preserved in the machine
result. Runner-only terminal records such as caught stealing, pickoffs, wild
pitches, and status changes remain unresolved rather than being forced into a
hitter outcome category.

## Remaining exclusions

The sidecar fails closed for 39,923 reconciliation rows. These include 21,529
direct outcome-count mismatches, 12,866 player-games with at least one unresolved
direct label, 3,806 sidecar-only authority rows, 197 prior-source or matchup
failures, and 1,525 official player-games with no sidecar PA. Their players retain
the exact B1 outcome-only forecast.

## Boundary

This gate used only 2021–2024 source records and existing certified player-game
outcome authority. It loaded no forecast target, implemented/fitted/scored no
candidate, and did not open protected 2026 outcomes.

The exact next gate is review of this source result, followed—only if authorized—
by implementation of J0 against synthetic and chronology-invariant checks. J0 fit
and scoring would remain separate later gates.
