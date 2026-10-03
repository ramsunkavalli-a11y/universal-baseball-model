# V32: reconnect improved opportunity with preserved batting estimates

Declared 2026-10-02 after V31's complete player walkthrough, before computing
these assembly scores. No new fitted models or revised evaluation membership.

V31 improves expected PA against V24 but does not improve delivered batting
value. This test asks whether that tradeoff comes from replacing the batting
estimate rather than the opportunity estimate. For each of the base and detailed
V31 workload forecasts, retain the older V24 or N forecast's implied contribution
yield: candidate value = new expected PA × old expected value / old expected PA.
This yield is a ratio of expected contribution to expected opportunities, not a
pure talent estimate. Changing one expectation while preserving the ratio is a
testable assembly approximation, not a claim of independent talent/workload.
Also score detailed workload × V31's actual-future-PA-weighted tree rate plus
origin-known replacement allocation on the full V31 population. Exclude the
ridge diagnostic with its demonstrated rare-feature extrapolation defect.

Keep V24's exact 4,396 rows, N's exact 21,819 shared rows, all 30,506 broad rows,
and the original 1,789 public rows. N's public intersection remains separate.
Archived N uses a different fitting protocol: comparisons against it cannot
isolate an individual feature effect. Never treat a missing archived forecast
as zero or choose a baseline according to its realized error. If old expected
PA is zero, verify old value is also zero; retain that zero yield and flag the
undefined-rate fallback, rather than inventing a batting grade. New zero PA
always produces zero contribution. No fits, outcome-derived rescaling, selected
weights, new clipping, or protected 2026 access.

Primary: equal-target-year delivered batting-plus-replacement value RMSE and
paired player-clustered squared-error differences against the corresponding
preserved anchor. PA is unchanged from V31 and reported alongside value. Show
MAE, bias, every origin, source stage, current PA bands, debut status and totals.
These remain next-calendar-year MLB outcomes, not full WAR, career/control value
or current MLB-equivalent ability for non-arrivals. Keep public conversion and
snapshot-timing qualifications. No pooled gain can excuse 2021's workload
shortfall, unavailable-profile assumptions or operationally unsafe availability.

Review the fixed Olson, McNeil, Steer, Winn, Judge, Rooker, McLain, Tatis,
Eldridge and Kurtz cases when eligible; add the largest value gain/harm, false
high/low and an ordinary case for each relevant assembly. Retain V31's complete
source/input/fit walkthrough and independently trace the new arithmetic with
origin-only comparison players. Complete that review before disposition.

An assembly can be retained as a matched-sample development candidate only if
it improves contribution without a material opposite-profile/cohort failure.
It cannot be a full-population production model while its older batting recipe
has not been reproduced on that population and forecast cutoff. A failure means
the simple reconnection did not work; it does not reject richer joint models or
the improved workload evidence. Frozen forecast and deployed explorer unchanged.
