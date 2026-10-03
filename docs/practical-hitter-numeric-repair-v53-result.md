# Numeric history repair and the remaining prospect gap

2026-10-03. The numeric correction is retained, but it did not materially improve
the candidate. All 30,506 historical forecasts remain, 105 fitted heads replay,
and ten actual player reviews are complete. No frozen forecast or protected
2026 result was changed.

Time since draft had been truncated in 23,401 drafted source rows. Rebuilding
all pooled counts also restores fractional PA in DSL and three rookie buckets.
Every reconstructed component rate agrees with the old source; unrelated inputs,
labels and identities are unchanged. Explicit floating-point types now prevent
the initial unknown rows from deciding later numeric precision.

On 2,627 public matches, hitting-rate RMSE changes from 1.7452 to 1.7435 versus
Steamer 1.7746 and ZiPS 1.7534 on the shared fixed-event metric. PA RMSE worsens
138.28 to 138.49 versus Steamer 135.38; MAE is 106.87 versus 92.08. Full-cohort
offense RMSE barely changes, .45387 to .45383, with no clear paired improvement.
These are repeated historical development comparisons, not fresh validation.
Exact public snapshot dates and park-neutral talent remain qualified.

Kurtz still gets two expected PA versus 489 actual; Langford 43 versus 557,
Bellinger 15 versus 548 and Alonso 127 versus 693. Kurtz's own input did not
change: the broad matching training profile has four people and no conditional
participants. Langford's has two conditional participants. Bellinger and Alonso
have many more broad matches and still fail, so rare coverage is not the only
issue. No-MLB-workload reductions and compressed upper-minor power remain.

The reviews also keep failures visible. Olson loses a small amount of projected
offense against a large actual breakout. Davis has close workload but severely
overpredicted hitting. Bader's nearly exact offense result hides two opposing
component errors: 143 expected PA versus 437 actual and optimistic hitting.
Salas's low immediate MLB probability is reasonable, not a career-value verdict.

Keep the corrected source as the next research baseline and preserve the old
candidate/explorer. Next compare one regularized prospect-specific hurdle model
that shares information across related level/exposure/pedigree profiles, keeping
established MLB forecasts exact. Do not create an unsupported tiny fast-draft
leaf, boost named players, or claim a prospect-only repair fixes MLB availability.

[Contract](practical-hitter-numeric-repair-v53-contract.md) ·
[Ten detailed player reviews](../reports/model-evidence/practical-hitter-numeric-repair-v53/player-walkthrough.md) ·
[Actual source and fit evidence](../reports/model-evidence/practical-hitter-numeric-repair-v53/cases.json).
