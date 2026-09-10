# Pitcher controlled-WAR-to-FV mapping audit result

Status: mapping retained; compression occurs before the grade is assigned.

The pitcher mapping is monotonic and has these minimum expected six-year WAR
boundaries: 0.25 for displayed 40, 1.0 for 45, 2.6 for 50, 6.0 for 55, and 9.0
for 60. Among 3,278 current pre-MLB pitchers, 225 clear 40, 24 clear 45, and only
one clears 50. None clears 55.

That is not a rounding artifact. The maximum expected controlled WAR before mapping
is 2.664, barely above the 2.6 boundary; the 99th percentile is 0.757. Tyson Hardin,
the maximum, has strong nested probabilities and 1,151 expected BF but only 6.26 WAR
under the six-full-control-year skill path before workload probabilities are applied.

The first forecast-year affiliated-translated rate distribution is also narrow at the
top: its maximum is 2.132 conditional WAR per 800 BF and its 95th percentile is
1.830. The FV function can only label these production estimates; moving its cutoffs
would rename the compression rather than improve the baseball forecast.

## Decision

Keep the pitcher mapping. The next production challenger should let universally
available, chronology-safe information—especially age relative to level and stable
handedness—earn or lose conditional pitcher quality only if it improves later MLB
component forecasts. Do not use a target count of high grades.

Machine-readable detail: `docs/pitcher-fv-mapping-audit-result.json`.
