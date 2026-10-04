# Separating player contribution from league scoring changes

2026-10-03. Add a declared reasonability sensitivity before any new forecast
scores are inspected. Preserve the original contract, all fits and its primary
common-origin score. Do not tune, refit, change eligibility or substitute a more
favorable target after seeing results.

The existing common-origin response values actual next-year batting against
the MLB average at the forecast origin. That is a valid fixed-baseline production
question, but it also includes the league-wide change in hitting conditions.
For a WAR-like season-relative contribution question, the observed batting
response should instead be centered on that target season's MLB average. The
target average can be used in a historical outcome label without being known to
the earlier forecasting model. Neither measure is full published WAR.

The already audited compatible-value source preserves both responses. Their
difference is actual PA times the change in the league event index divided by
11.93, with the same corrected origin replacement reference. Independently
verify this identity. Missing participation remains zero under both measures.

For example, 2018-origin never-debut players deliver 64.277 common-origin custom
wins but 48.922 season-relative custom wins in the higher-scoring 2019 league.
That explains 15.356 of the former total, not the playing-time deficit: actual
15,836 PA versus current 10,032 PA is unaffected. For origin 2021, totals are
35.362 common versus 46.257 relative; for origin 2023 they are 5.119 versus
14.323. The direction varies. This is a measurement issue alongside the real
readiness/cohort misses, not evidence that the model should know future ball
properties or a reason to excuse every error.

Score the SAME saved numerical forecasts against the season-relative response
as an explicitly separate sensitivity, with the same scopes, equal-year losses,
paired player intervals and cohort totals. Do not subtract the realized future
league environment from a predicted count vector: that would give the forecast
oracle information. Predicted count value continues to use only the known origin
environment; interpreting that number as season-relative assumes the projected
future league reference equals the origin reference. The signed heads were
trained on the common-origin response, so this sensitivity is not a matched
training-target tournament or a blanket rejection of season-relative modeling.

Common-origin improvements cannot by themselves prove better player talent or
WAR-like value. If conclusions reverse or league changes explain material gains,
flag that limitation before any candidate selection. A subsequent season-relative
training comparison requires its own declared contract and completed player
reviews of this batch first. The existing matched ZiPS artifact supplies rate
context, not PA: do not invent a ZiPS season workload/value benchmark.

All protected 2026 outcomes and the frozen forecast stay untouched. This check
strengthens interpretation of the current integration experiment rather than
opening another feature or algorithm sweep.
