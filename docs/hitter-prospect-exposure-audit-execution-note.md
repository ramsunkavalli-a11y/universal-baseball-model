# Prospect diagnosis input replay correction

2026-10-05. The initial read-only diagnosis completed its source and accounting
checks but stopped at the first player replay: the historical prediction export
does not include `games_mlb_0` and several other fitted input columns. The saved
actual model-input frame does contain them. This is an audit-script assumption
error, not evidence that the fitted model lacked game information.

Preserve the interrupted output directory
`reports/generated/hitter-prospect-exposure-allocation-audit`. The corrected
diagnosis writes a separate `hitter-prospect-exposure-allocation-audit-reviewed`
directory. Replays load actual input rows from the sealed input frame, verify
every shared input against the prediction export, and never fill missing inputs
with zero. No fit, forecast, membership, source counts or grouping rule changed.
The initial accounting is not a completed player review or adoption decision.

The first correction then stopped on a different check: six shared columns in
the inherited prediction export do not represent the current fitted inputs.
They preserve older baseline evidence. Counts of differing records are
`pooled_DSL_pa` 3,960, `pooled_RK120_pa` 672, `pooled_RK134_pa` 76,
`draft_elapsed` 11,417, `scout_listed_0` 4,619 and `scout_rank_score_0` 4,824.
For Kurtz at origin 2024, the old export columns say unlisted, whereas the actual
preseason input says listed with rank score .63. Existing bridge code explicitly
uses separate `new_scout` evidence and the actual input frame for its walks.
This does not establish that the fitted model lacked his ranking.

The source-aligned diagnosis preserves both interrupted directories, uses a
third output directory and joins all 251 actual input columns by unique row ID.
Old export columns remain labeled as legacy evidence in memory. Saved forecasts
and scores do not change. Rank summaries and peer selection must use these
actual inputs; the interrupted rank summaries must not steer decisions.
Year, PA totals and non-rank exposure definitions did not depend on those six
columns. Exact input and model replays remain mandatory before interpretation.
