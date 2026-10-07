# Keep annual and game pitching starts separate

2026-10-07. The source audit stopped before emitting a corrected ledger: its
merged record used `pitching_starts` for both the annual inventory and the
individual boxscore. Python rejected the duplicate field. The captured runner
is archived. The amended runner names the per-game evidence
`box_pitching_starts`, leaving annual reconciliation unchanged. No source,
selection rule, forecast or model parameter changes.
