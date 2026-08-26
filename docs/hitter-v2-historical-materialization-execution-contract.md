# Hitter v2 historical materialization execution contract

Date: 2026-08-25

Status: frozen before full historical source execution

## Boundary

This is a source-only execution gate. It creates complete 2019 MiLB terminal
outcome evidence and independently certifies the 2020 MLB source. The resulting
tables are quarantined research inputs, not authorized model predictors.

No candidate may be fit or scored in this gate. Protected 2026 outcomes and
participant membership remain sealed.

## 2019 MiLB execution

Run every public 2019 PBP and player-game asset for `aaa`, `aa`, `a+`, `a`, and
`rk`. Keep `game_type == R`; exhibition and postseason records remain source
provenance but do not enter regular-season output.

For each filename level:

1. record release metadata, bytes, retrieval vintage, and SHA-256;
2. project one maximum-pitch terminal row per game and at-bat, failing on
   substantive narrative conflicts;
3. retain source batter identity only when terminal snapshots agree;
4. obtain actual league ID solely from a unique same-game player-game map;
5. resolve official player-game snapshots only by consensus or unique
   component-wise dominance;
6. build the exhaustive Hitter v2 outcome taxonomy from official counts and
   supported terminal-contact narratives;
7. preserve every unresolved or non-reconcilable player-game as failed closed;
8. assert nonnegative, unique, exhaustive player-game and player-season output;
9. report coverage and exceptions by actual league, filename level, source
   status, and asset.

Filename level is a processing partition, never league authority. Unsupported
PBP narratives do not become zero outcomes; official BB, HBP, K, hit, SF, bunt,
and interference counts complete the taxonomy under the frozen Stage 1 policy.

## 2020 MLB execution

Use only the official 2020 regular-season schedule window. Fetch Savant in
bounded date chunks, retain raw response hashes, require unique canonical pitch
keys, assign actual AL/NL identity from the official team authority, and
reconcile player-game outcomes to official league-season hitting totals.

The shortened schedule is a source property. No exposure normalization,
reliability weight, aging adjustment, or comparison with other seasons occurs
here. The absence of 2020 MiLB remains an observation gap.

## Acceptance

- 2019: every selected regular-season source asset parses; every supported PBP
  game has same-game league authority; taxonomy invariants pass; exceptions are
  retained and quantified; canonical artifacts are hash-pinned.
- 2020: schedule and source vintages are pinned; AL and NL are present; pitch
  keys are unique; official outcome reconciliation is exact under the existing
  certified definition; canonical artifacts are hash-pinned.
- canonical lint and the full repository suite pass.

If either lane fails, freeze the failure independently. One lane cannot certify
or rescue the other.

## Exact stop

After reporting results, stop for review. Historical model use requires a new
contract that defines chronology, observation-gap handling, shortened-season
reliability, folds, and the exact comparison against Marcel before loading any
evaluation target.
