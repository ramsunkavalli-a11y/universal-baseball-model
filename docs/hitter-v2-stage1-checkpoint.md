# Hitter v2 Stage 1 — universal terminal-PA checkpoint

Status: **SOURCE GATE COMPLETE LOCALLY / AWAITING REVIEW**  
Date: 2026-08-23  
Implementation commit: `f9abead2550e43112077e101523722ce16ffbf0d`  
Base commit: `197d21a67d707633cb47d720c84a7b126b9c4320`

## Scientific outcome

The universal 2021–2023 PBP outcome foundation is materialized at unique
player-game and player-season grains. It contains all 14 preregistered terminal
outcomes and reconciles 2,813,883 of 2,837,295 official PA (99.1748479%) as
model-ready. The remaining 23,412 PA are retained in an exception table and
fail closed. No Hitter v2 candidate was fit or scored, no target-season run
values were attached, and protected 2026 outcomes remain unopened.

The source was reproduced without GitHub authentication. Public artifacts were
accepted only when their SHA-256 digests matched the committed/frozen source
registry. Remote state was not changed.

## Materialized contract

The exhaustive mutually exclusive taxonomy is:

`UBB`, `IBB`, `HBP`, `K`, `HR`, `3B`, `2B`, `1B`, `ROE`, `FC_REACH`, `SF`,
`MULTI_OUT`, `OTHER_OUT`, and `SH_OR_SPECIAL`.

The implementation preserves raw source status, source capability, official
counts, reconciliation residuals, exclusion reasons, evidence counts, and the
special-outcome subtype. IBB is separate from UBB. Sacrifice bunts and known
interference/special events enter `SH_OR_SPECIAL`; they are retained but are not
ordinary batting opportunities for later modeling. Missing or ambiguous
terminal records never receive a guessed outcome.

The player-game key is season, game, league, team, and player. The
player-season key is season, league, and player; team is deliberately not part
of that grain so movers have one league-season row. Duplicate keys, unresolved
participant identity, non-exhaustive PA accounting, negative counts, and
official/PBP overcounts fail closed.

## Coverage

| Scope | Player-game rows | Official PA | Model-ready PA |
|---|---:|---:|---:|
| 2021 | 231,999 | 886,178 | 879,747 |
| 2022 | 246,238 | 974,413 | 968,212 |
| 2023 | 243,399 | 976,704 | 965,924 |
| **Total** | **721,636** | **2,837,295** | **2,813,883** |

The materialization spans 37,741 games, 6,391 players, and 19,074 unique
player-league-season rows. MLB accounts for 547,974 PA with zero blocking
official reconciliation mismatches. The affiliated MiLB path accounts for
2,289,321 official PA and promotes 1,415,912 supported terminal contacts into
the full PA foundation.

Model-ready outcome counts:

| Outcome | Count | Outcome | Count |
|---|---:|---|---:|
| UBB | 293,927 | IBB | 3,835 |
| HBP | 47,292 | K | 680,620 |
| HR | 71,212 | 3B | 15,925 |
| 2B | 120,884 | 1B | 394,457 |
| ROE | 33,457 | FC_REACH | 6,451 |
| SF | 20,933 | MULTI_OUT | 53,989 |
| OTHER_OUT | 1,063,569 | SH_OR_SPECIAL | 7,332 |

## Reconciliation findings

- 710,199 player-games and 2,789,474 PA reconcile exactly.
- 5,721 player-games and 24,409 PA are accepted after a unique official repair;
  5,836 individual 1B/2B/3B/HR/SF cells were repaired and tagged.
- 5,706 player-games and 23,380 PA retain unresolved MiLB non-hit ambiguity and
  fail closed.
- Nine player-games and 26 PA fail closed because terminal PBP exceeds an
  official component; one player-game and six PA fail because the official
  snapshot is unresolved.
- MLB structured and official GIDP definitions differ on 40
  player-league-season rows. This is a disclosed diagnostic, not a blocking
  batting-taxonomy mismatch, because `MULTI_OUT` is assigned from the terminal
  PBP event rather than raw official GIDP.

The earlier 99.97% coverage statement described supported rows inside a
screened terminal-contact slice. It was not whole-PA coverage. Stage 1 uses raw
terminal PBP identities plus the certified participant overlay and reports the
whole-PA denominator above.

## Canonical artifacts

- Player-game table: SHA-256
  `322587b6af6d74b14fe1b5ca925343e0cce9decfaa5252261a6e8b3681345f96`
  (721,636 rows).
- Player-season table: SHA-256
  `2be64d9041ccbe282f723d97c0f40af87d15f8f0701b111fdf2fbf74af829bde`
  (19,074 rows).
- Failed-closed exception table: SHA-256
  `0e53a8732b8b90b60ad7d99d09fbc92d761066e9e80d704d1812ac90b6d26dec`
  (5,716 rows).
- Complete generated report: SHA-256
  `b7bc41ec87c43dfff9f0bcb6665557f32e3c525978aae46624596afa089d768a`.

Coverage by season, league, level, team, capability tier, and source status is
machine-readable in
`reports/generated/hitter-v2-stage1-universal/report.json`. Raw event-grain
bytes remain in ignored quarantine; the distributable contract is the
canonical aggregates plus exact provenance and hashes.

## Decision and boundary

**Stage 1 source materialization passes and stops for review.**

Validation at this gate: Ruff passed across `src`, `scripts`, and `tests`; all
830 tests passed in 9.28 seconds, including eight focused Stage 1 invariants.

This result does not authorize Stage 2. After explicit review approval, the
next gate would implement the frozen PBP-only baselines and component candidates
and run the preregistered rolling-origin evaluation. It would still leave 2026
confirmation outcomes, tracking fusion, baserunning, defense, playing time, and
WAR closed until their respective gates.
