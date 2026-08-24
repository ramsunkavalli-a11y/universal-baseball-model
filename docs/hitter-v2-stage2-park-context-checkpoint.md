# Hitter v2 Stage 2 park-context checkpoint

Recorded: 2026-08-23  
Implementation commit: `67ecda4449d10838e7d81d26bb972f2871d56ff3`  
Candidate fit/scored: **no / no**  
Protected 2026 opened: **no**

## Scientific outcome

Chronology-safe historical venue context is source-ready for C1. Official
2021–2023 schedules for MLB, AAA, AA, High-A, A, and complex leagues cover
714,474 model-ready player-games and 2,808,923 PA: 99.7980% and 99.8237% of
the historical source, respectively. The accepted games span 185 official
venue IDs.

The capture intentionally stops after 2023. No target-season park metadata,
park outcome, participant membership, or protected 2026 information was
opened. C1 must slice this source at each fold's predictor cutoff.

## Authority and failure policy

The Stats API retains stale postponed schedule entries under the same game ID.
The adapter reuses the repository's established completed-game authority:
`codedGameState == F`. This prevents a postponed venue from conflicting with
the venue where the game was actually completed.

Venue and home/away team fields must be unique among completed records. The
source retains and excludes 1,387 player-games with a missing or conflicting
completed-game venue and 59 whose game ID is absent from the official schedule.
These rows are not imputed as a league-average park or zero effect.

## Reproduction and validation

The exact official response bytes are stored outside Git and checksum-bound.
After capture, the source reproduces offline with:

`python scripts/materialize_hitter_v2_stage2_park_context.py --reuse-captured`

The machine-readable result is
`docs/hitter-v2-stage2-park-context-result.json`. The ignored generated report
is `reports/generated/hitter-v2-stage2-park-context/report.json`, SHA-256
`340f9bdbb0bea25e34fb9ae1b114fc337dc6dbc69fe8d9210c870ab92a4bb617`.
The player-game context artifact SHA-256 is
`8639ab2b2b03fcad5e9ba9d50a79d48ed8f3616ad626f56c3fc85d4e16da30cf`.

Ruff passed, and all 850 tests passed in 9.53 seconds.

## Gate state

All declared C1 source inputs—age, movement, GIDP opportunities, and park
context—are now available. C1 is still unfit and unscored. The next gate is to
implement C1 and freeze its candidate-specific invariants before disclosed
validation scoring. Tracking, protected 2026 outcomes, and Stage 3+ remain
closed.
