# Progress on physically possible hitting uncertainty

This is the initial execution snapshot. The later
[completed comparison and player review](hitter-event-count-risk-result.md)
supersedes its pending-work status; the original checkpoint is preserved below.

2026-10-04. The new comparison is running, not validated or adopted. It fixes a
specific design defect in the previous uncertainty test: a simulated one-PA
outcome must consist of an actual baseball event, not an arbitrary continuous
hitting result. Average hitting, playing time and offense projections remain
unchanged. This is one step in the practical hitter plan, not completion of the
full hitter model or valuation system.

## What has been implemented

The [predeclared comparison](hitter-event-count-risk-contract.md) replaces the
continuous hitting distribution with eight integer event counts that add up to
each simulated PA total. One version holds expected hitting rate constant across
possible workloads. The other allows rate and workload to move together, while
preserving the same total expected offense analytically. Neither uses realized
future playing time as an input to the preseason point forecast.

All 30,506 historical forecasts, including minor leaguers and non-arrivals,
remain. There are 35 outer cells and 95 nested validation contexts. All 130
actual source, chronology and player-separation checks finished before the new
fits, and fifty saved hitting heads and fifty conditional-playing-time heads
were replayed. Reference event profiles exclude the entire outer player group
and the selected inner player group, as appropriate. These profiles describe a
working distribution shape, not a new estimate of each player's K, BB or HR mix.

Twelve focused tests check integer counts, event support, exact theoretical
mean conservation, zero-PA mass, deterministic simulation, independent proper
score calculations and covariance against the official count-distribution
formula. Passing them verifies those mechanics, not predictive accuracy.

## Warnings visible during execution

The early fits reach the predeclared maximum positive workload-related rate
slope. This suggests the one-slope relationship may be restrictive. Do not
expand the bound after inspecting results or claim that all dependence has been
solved. Keep optimizer limits, calibration bias and player examples in the final
review. The shared earlier workload fit is a calibration nuisance estimate,
not an old inner forecast with a fictitious historical publication date.

The new implementation does not repair Nick Kurtz's low readiness estimate,
Judge's point forecast, public playing-time errors, missing foreign production,
general defense or six-year club control. Sparse calibration profiles still
borrow globally. More realistic event support cannot justify calling those
remaining issues resolved.

## Remaining work in this comparison

Finish both count laws, replay every parameter fit, compare proper risk scores
with both preserved references, and run the independent simulation audit. Then
trace the thirteen fixed player-origin cases plus gains, harms, false highs,
false lows and an ordinary active case through actual statistics, saved point
models, event profiles and simulated counts to future MLB reality. The
experiment remains provisional until that review is complete. No subsequent
modeling experiment, forecast promotion or deployed explorer change is approved
by this checkpoint. Protected 2026 outcomes remain closed.

The [preparation evidence](../reports/model-evidence/hitter-event-count-risk/preparation-verification.json)
records the independent input and reference audit separately from the pending
scores and baseball review. Intermediate files may correctly continue to say
pending after a later, separate completion receipt is added; do not overwrite
their historical state.
