# Hitter v2 matchup-context source audit

Date: 2026-08-24  
Gate: source-only matchup-context readiness  
Decision: source capable; matchup-preserving sidecar not yet certified

## Scientific outcome

Affiliated PBP can support a contextual hitter model. Across 3,811,570
regular-season 2021-2024 PAs from MLB through the rookie/complex levels, every
PA had a batter identity, pitcher identity, observed batter side, observed
pitcher hand, and game date. After failing closed on within-PA conflicts,
3,810,808 PAs (99.9800%) remain matchup-ready.

The existing Hitter v2 Stage 1 terminal-PA and contact artifacts do **not**
retain pitcher identity or pitcher hand. Therefore this audit does not authorize
a candidate. The next safe implementation is a checksum-bound, matchup-
preserving PA sidecar joined one-to-one to the existing terminal outcome table.

No terminal outcome, future-offense target, candidate prediction, or protected
2026 information was read. No model was fitted or scored.

## Source and grain

- MiLB: retained ARMSTJC PBP, 2021-2024, AAA/AA/High-A/Single-A/rookie-complex.
- MLB: retained Baseball Savant pitch-level CSVs, 2021-2024.
- Canonical source grain: one row per `(game_pk, at_bat_number)` after limiting
  to regular-season games.
- Fields read: `game_pk`, `at_bat_number`, `pitch_number`, `game_date`,
  `batter`, `pitcher`, `stand`, `p_throws`, and `game_type` only.
- Handedness is the side actually observed in the matchup, not a player bio
  default. Valid values are `L` and `R`; switch hitters therefore resolve to
  their observed side for that PA.

The machine-readable result is
`docs/hitter-v2-matchup-context-source-result.json`. The reproducible command is:

```powershell
.venv\Scripts\python.exe scripts/audit_hitter_v2_matchup_context_source.py
```

Generated detail is written under
`reports/generated/hitter-v2-matchup-context-source-audit/` and remains outside
version control. The committed result SHA-256 is
`089f75ea7cb8c144ef1b45e5cd63a72f2fdb6125c6edff667455f55f3a54e304`;
the audit-script SHA-256 is
`696116c822cb7d12629c354cc1f4a88219f0f3e83c32c8a2fd93cff42857457d`.

## Coverage

All 24 season-level cells have 100% raw presence for the four matchup fields.
Conflict-free rates range from 99.9539% to 99.9954%. In total, the fail-closed
conflict screen found 472 PAs with more than one batter ID, 283 with more than
one pitcher ID, 63 with more than one batter side, and 109 with more than one
pitcher hand. These categories can overlap; the union is 762 PAs. They must not
be silently resolved by taking the last pitch.

| Season | Level | PA | Conflict-free | Prior 50 BF | Prior 100 BF |
|---:|---|---:|---:|---:|---:|
| 2021 | MLB | 182,131 | 99.9539% | 83.91% | 70.26% |
| 2021 | AAA | 146,193 | 99.9918% | 79.87% | 62.13% |
| 2021 | AA | 129,887 | 99.9923% | 77.77% | 58.74% |
| 2021 | High-A | 134,296 | 99.9881% | 76.77% | 57.37% |
| 2021 | Single-A | 136,330 | 99.9868% | 68.65% | 45.22% |
| 2021 | Rookie/complex | 160,066 | 99.9738% | 50.29% | 20.89% |
| 2022 | MLB | 182,433 | 99.9583% | 99.26% | 98.41% |
| 2022 | AAA | 172,055 | 99.9895% | 98.07% | 95.96% |
| 2022 | AA | 156,955 | 99.9892% | 98.52% | 96.46% |
| 2022 | High-A | 147,267 | 99.9878% | 97.13% | 91.82% |
| 2022 | Single-A | 149,936 | 99.9887% | 90.58% | 79.97% |
| 2022 | Rookie/complex | 168,796 | 99.9704% | 74.68% | 55.32% |
| 2023 | MLB | 184,478 | 99.9550% | 99.54% | 99.40% |
| 2023 | AAA | 174,093 | 99.9954% | 98.97% | 98.15% |
| 2023 | AA | 156,056 | 99.9853% | 99.48% | 98.56% |
| 2023 | High-A | 147,177 | 99.9905% | 97.43% | 93.84% |
| 2023 | Single-A | 148,229 | 99.9838% | 89.23% | 78.87% |
| 2023 | Rookie/complex | 165,102 | 99.9715% | 77.44% | 61.00% |
| 2024 | MLB | 182,869 | 99.9617% | 99.60% | 99.43% |
| 2024 | AAA | 172,800 | 99.9902% | 99.29% | 98.87% |
| 2024 | AA | 153,314 | 99.9863% | 99.58% | 99.05% |
| 2024 | High-A | 147,617 | 99.9925% | 97.88% | 94.98% |
| 2024 | Single-A | 148,944 | 99.9859% | 90.38% | 81.19% |
| 2024 | Rookie/complex | 164,546 | 99.9727% | 78.45% | 61.73% |

## Chronology-safe opponent evidence

For this readiness check, prior pitcher evidence is only the number of PAs
against that pitcher on dates strictly before the current PA date. All same-day
evidence is excluded, including earlier games of a doubleheader. This is a
count, not a quality estimate, and it is not scored against batter outcomes.

Overall coverage is 98.12% with at least one prior BF, 88.85% with 50, 79.83%
with 100, and 64.59% with 200. The 2021 rows are deliberately conservative
because the disclosed audit starts in 2021. By 2022, 50-BF coverage exceeds 90%
at every full-season level and reaches 99.26% in MLB. Rookie/complex coverage is
materially lower in every season, so opponent effects require smooth shrinkage
to a league-season-level prior and an exact neutral fallback; a hard evidence
threshold would create artificial jumps and selection bias.

## Required sidecar contract

Before any new candidate is specified, the source implementation should create
one immutable row per canonical terminal PA with:

- season, date, game, PA sequence, league, and level;
- batter ID, pitcher ID, observed batter side, and pitcher hand;
- authority/source tier and source-asset provenance;
- raw conflict flags and a `matchup_ready` fail-closed flag;
- strictly prior-date pitcher evidence counts and source seasons;
- exact join status to the existing Hitter v2 terminal-outcome row.

Required invariants are uniqueness at `(game_pk, at_bat_number)`, a one-to-one
join with no cohort gain, no same-date or future evidence in prior pitcher
features, no player-name predictor, and exact neutral fallback for conflicted or
missing matchup rows. Pitcher quality itself must later be estimated from
chronology-safe prior outcomes with shrinkage; this audit did not estimate it.

## Decision and boundary

The source is capable, but opponent adjustment is **not model-ready** until the
sidecar is certified and reconciled. The exact next authorized gate is source
implementation only: materialize and validate that sidecar for disclosed
2021-2024 data. It must not fit or score a hitter candidate, alter E1, access
2026, authorize tracking, or proceed to Stage 3/WAR.
