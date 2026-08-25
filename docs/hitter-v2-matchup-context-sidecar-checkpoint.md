# Hitter v2 matchup-context sidecar checkpoint

Date: 2026-08-24  
Gate: source-only PA sidecar materialization and reconciliation  
Decision: accepted with exact neutral fallback outside reconciled player-games

## Scientific outcome

The disclosed 2021-2024 affiliated PBP now has a terminal-PA matchup sidecar.
It contains 3,810,001 unique `(game_pk, at_bat_index)` rows and preserves the
terminal pitch, officially attributed outcome batter where available, completing
pitcher, observed batter side, observed pitcher hand, league/level, provenance,
conflict flags, and chronology-safe prior evidence counts.

Of those rows:

- 3,809,992 are source-matchup ready; only nine have conflicting repeated
  terminal source rows;
- 3,691,876 are both matchup ready and in a player-game whose terminal-PA count
  agrees exactly with the existing accepted Hitter v2 outcome authority;
- 937,255 player-games reconcile exactly and are accepted for a future optional
  opponent-context channel;
- 31,922 player-game reconciliation rows fail closed;
- 3,370,050 PAs have at least 50 strictly earlier outcome-ready pitcher PAs and
  3,015,365 have at least 100.

No hitter candidate was fitted or scored. No future-offense target, model
prediction, run value, ranking, tracking feature, or protected 2026 outcome was
opened.

## Why the sidecar has fewer rows than the initial source audit

The source-readiness audit counted 3,811,570 regular-season raw PBP PA keys. The
sidecar is narrower by 1,569 rows because it binds to certified terminal-PA
authority rather than treating every maximum pitch sequence as a true modeled
PA:

- MLB uses the existing structured Savant true-PA terminal policy, excluding
  `truncated_pa` and other non-PA terminal markers; and
- the 2024 MiLB path excludes 81 rookie/complex PA keys from game 774353 because
  that game lacks reusable league authority, matching the existing quarantine.

This is a semantic restriction, not a coverage loss introduced by a candidate.

## Reconciliation policy and result

The sidecar is unique one-to-one with its certified terminal authority. It then
reconciles terminal-row counts to the existing player-game outcome artifact on
`season + league_id + game_id + player_id`.

| Status | Player-games | Official PA | Sidecar PA |
|---|---:|---:|---:|
| Exact accepted player-game | 937,255 | 3,691,884 | 3,691,884 |
| Existing player-game failed closed | 246 | 803 | 803 |
| Player-game without sidecar PA | 1,525 | 3,129 | 0 |
| Sidecar without player-game authority | 3,806 | 0 | 3,810 |
| Terminal-PA count mismatch | 26,345 | 101,092 | 113,504 |

The eight-PA difference between exact accepted player-game PA and
`modeling_join_ready` PA is caused by the nine terminal-source conflicts, one of
which is already outside an accepted exact player-game. Conflicts are never
resolved by row order.

MLB reconciles at 100% in every season. MiLB modeling-join readiness ranges from
94.50% (2024 rookie/complex) to 97.14% (2021 AAA). The dominant MiLB mismatch is
exactly plus or minus one raw terminal sequence within a player-game. Because
the current outcome authority is aggregated at player-game grain, it cannot
identify which individual PA should be added or removed. The entire mismatched
player-game therefore receives an exact neutral opponent-context fallback.
This does not remove the player or PA from the universal PBP batting baseline.

## Chronology and reliability

Two evidence counts are retained:

1. `prior_pitcher_pa` counts all source-valid matchups on dates strictly before
   the current game date.
2. `prior_outcome_ready_pitcher_pa` counts only earlier matchups that also pass
   player-game outcome reconciliation.

Same-day evidence is excluded wholesale, including earlier doubleheader games.
Future opponent-quality estimation must use the second count for likelihood
evidence and may use the first only as source-availability metadata. Neither is
a pitcher-quality estimate in this gate.

Rookie/complex coverage remains materially sparser than full-season levels.
Any eventual opponent effect must therefore use smooth empirical-Bayes
shrinkage toward league-season-level context. A hard 50- or 100-PA cutoff is
forbidden because it would create discontinuities and cohort selection.

## Artifacts and reproducibility

Command:

```powershell
.venv\Scripts\python.exe scripts/materialize_hitter_v2_matchup_context_sidecar.py
```

Committed machine-readable result:
`docs/hitter-v2-matchup-context-sidecar-result.json`.

Generated immutable tables:

- `hitter_v2_matchup_context_sidecar_2021_2024.parquet`: 3,810,001 rows,
  SHA-256 `c18e6e09b3a015d5b973f537f928b9afc5b2dd0eaae11f4ee7ddcf882e440b53`;
- `hitter_v2_matchup_context_reconciliation_2021_2024.parquet`: 969,177 rows,
  SHA-256 `625e2f93f8303a86e92b1e5cb0f8c45371acb2ec820c0653f671ed52047053ef`;
- generated report SHA-256
  `1dbb821701783e5ba0863c746b06ce2e9e94019bb29b0298f68dbf8154af749e`.

The generated tables remain under `reports/generated/` and are not committed.
Their hashes, schemas, row counts, and source provenance are committed in the
machine-readable result.

## Authorization boundary

This source gate is complete. It does not authorize an immediate fit. The exact
next gate is to pre-register the new joint contextual candidate contract:
candidate family, standardized/effect-unit priors, prior-only pitcher-quality
construction, platoon terms, folds, metrics, fallback identity, subgroup
guardrails, and promotion rule. That contract must be frozen and hashed before
any new candidate fit or disclosed-outcome score. E1 remains a documented
failure and cannot be repaired or rescored; tracking, 2026, Stage 3, and WAR
remain unauthorized.
