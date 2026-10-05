# Keep original origin weights in component uncertainty estimates

2026-10-04. The component review preserves 253 original forecasts, with hitting
unobserved for 225 non-arrivals and 28 observed MLB batting seasons. Its point
scores correctly average players within origin, then origins equally.

The initial bootstrap renormalizes each sampled origin independently and drops
an origin when no sampled person remains. Preserve those initial intervals,
but do not use them for the final uncertainty statement: that procedure changes
the origin weights during the resample.

For the corrected diagnostic, assign each original scored row weight
1 / (number of observed origins * original scored rows in that origin).
Resample the twenty player clusters 2,000 times with seed 84. Multiply the
fixed row weights by sampled person multiplicities, and calculate the paired
loss difference divided by their total weight. Independently reconstruct each
draw from the row-level scores and the player-level weighted sums.

The resampled population can have a different mix of years, but the observation
weights are not rebuilt from its realized year sample sizes. Report these as
nominal player-cluster development intervals, not coverage for season shocks,
international selection or repeated model choices. No fit, profile, forecast,
primary point score, cohort or protected data changes. A future-100-PA diagnostic
may explain small-sample influence, but does not replace the declared cohort.
