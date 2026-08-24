# Hitter v2 Stage 2 source-readiness checkpoint

Recorded: 2026-08-23  
Branch: `hitter-v2-pbp-outcomes`  
Implementation commit: `cd7a527a27c343598ffb389368d9dffb825fd9a1`  
Development-contract SHA-256: `4f0e0bde4ac903145ea133f4cb57027f2566668cf36f3847621a42646393fe40`

## Scientific outcome

The disclosed 2024 terminal-outcome target is source-ready for the frozen
`V2024` rolling-origin fold. This is a source checkpoint, not a model result.
No Hitter v2 candidate has been fit or scored, no tracking feature has been
opened, and completed 2026 offense remains protected.

The universal 2024 table contains 243,735 player-games, 5,599 unique
player-league-seasons, 12,895 games, 3,760 players and 966,808 official PA.
Of those, 960,362 PA are model-ready (99.3332699%). The remaining 1,614
player-games and 6,446 PA are retained with explicit failed-closed statuses.

MLB has zero blocking official-season reconciliation mismatches. Five GIDP
definition mismatches remain a diagnostic because the structured terminal-PBP
and official-season GIDP fields do not use an identical definition. They do not
alter the exhaustive batter terminal-outcome taxonomy.

## Source policy decisions

- The 2024 adapter reuses checksum-certified historical player-game artifacts,
  the existing terminal-PA parser, participant authority, identity corrections,
  official reconciliation and canonical storage code.
- Public MiLB PBP bytes are captured with a raw-file manifest inside the
  generated report; their content is bound by the report SHA-256.
- Declared historical residuals remain failed closed. The pipeline stops if the
  observed missing-adjudication count differs from the certified declaration.
- Game `774353` has no reusable same-game league authority and its exact
  official endpoint returned 404. Its terminal rows are quarantined rather than
  assigned a league from the filename or neighboring games.
- The single unresolved official snapshot remains failed closed. Source-file
  ordering is not treated as chronology or authority.

## Chronology boundary

The 2024 outcome table may be used only as the target of `V2024`; its rows,
participants, playing time and environment cannot enter predictors, priors,
translations, parks, centering or weights. Predictor history for that fold ends
after 2023. The earlier folds remain `V2022` (history through 2021) and `V2023`
(history through 2022). No 2025 data was accessed in this batch. Completed 2026
offense remains unopened.

## Reproduction and hashes

The machine-readable record is
`docs/hitter-v2-stage2-source-readiness-result.json`. The ignored generated
universal report is
`reports/generated/hitter-v2-stage2-2024-universal/report.json`, SHA-256
`9d559a9057e00ad9308306c07fe35be5230e03686280352450ff1d9b47e46ac8`.
It freezes the input reports, raw manifest, coverage tables, exception counts
and canonical artifact hashes.

Validation passed:

- `python -m ruff check src scripts tests`;
- `python -m pytest` — 832 passed in 30.63 seconds;
- `python -m pytest tests/test_hitter_v2_outcomes.py -q` — 10 passed.

## Gate state

Source readiness is accepted. Candidate scoring is still closed until neutral
historical wOBA/run weights, exact fold manifests and all pre-score scientific
invariants are frozen and verified. Tracking, 2026 confirmation, baserunning,
defense, playing time and WAR remain outside the authorized gate.
