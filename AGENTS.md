# Model-development guardrails

Before designing or interpreting a model experiment, read
`docs/model-experiment-review-gate.md` and `docs/project-status.md`. Follow the
controlling execution plan linked there, not an old conversational next step.

- Write the estimand, eligibility, source coverage, exact comparison and claim
  limits BEFORE fitting. Separate future MLB performance from same-level proxy
  prediction, conditional talent from unconditional contribution, calendar years
  from service years, and component value from full WAR or trade value.
- Chronology, player separation and total training counts are necessary but NOT
  sufficient. Audit forecast-time profile support in actual training folds and
  nested subsets. Missing historical coverage is unknown, not zero. Preserve
  exits/non-arrivals and fixed evaluation membership.
- For post-arrival experiments use `forecast_validation.preflight` before fits.
  Other model families require equivalent tests suited to their estimands; do
  not apply a hitter-specific schema blindly. Unsupported forecasts remain in
  overall scoring and are explicitly marked, not deleted to improve results.
- Keep execution integrity, training support, predictive performance,
  reasonability and deployment approval separate. Never summarize unit tests,
  reproducibility or a smaller pooled RMSE as full model validation.
- No protected 2026 outcome access or forecast/explorer promotion without a
  separate authorization. No post-result tuning disguised as a predeclared test.
- Report matched cohort totals, major origin/stage errors and named gains AND
  misses. State unresolved limits and whether a result is development evidence.
  A negative result with a defective experiment does not reject an entire idea.
- Every model/component experiment must be followed by the player walkthrough
  in `docs/required-player-walkthrough.md`, including failed and inconclusive
  tests. Trace actual stats through inputs, adjustments and intermediate outputs
  to predictions and reality; names beside an error leaderboard are insufficient.
  Do not close the experiment, promote/reject an approach, or choose another
  modeling experiment before this review. Missing evidence leaves it provisional.
- Do not overwrite old contracts or results. Append corrections and update the
  start-here status. Do not start an algorithm tournament to avoid a data/design
  defect. Fix that defect or explicitly limit the claim first.
