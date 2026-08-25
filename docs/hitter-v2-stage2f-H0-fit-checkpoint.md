# Hitter v2 Stage 2f H0 fit-only checkpoint

## Scientific outcome

The chronology-safe H0 source and fit gate completed. Real historical predictor
data can support the neutral-reference architecture in V2023 and V2024, and the
resulting probability vectors are numerically coherent for every predeclared
forecast player. This checkpoint contains no evidence yet that H0 predicts
future offense better than Marcel or C0 because validation outcomes were not
loaded and no accuracy metric was computed.

V2022 correctly remains the exact untranslated C0 base: a 2021 cutoff contains
no adjacent prior seasons from which to learn translation or development. V2023
fits translation and development from 3,176 adjacent player-season pairs.
V2024 fits those surfaces from 6,297 pairs and adds calibration using 34,892
component rows from the strictly earlier V2023 origin.

## Source audit

The runner reused the certified Stage 1 player-game outcome table, frozen park
context, chronology-safe forecast populations and ages, unscored B0/B1/C0
forecasts, and retained Chadwick register. The foundational hashes match their
earlier certifications. Nothing was downloaded or reclassified, and the runner
contains no loader for validation-player or target-outcome tables.

Park-neutral player-season outcome probabilities are reduced to one primary
level per player-season using the existing PA-first deterministic rule. Level
movement uses consecutive player seasons, minimum two-season PA as evidence,
and destination age for the frozen translation age band. Development is fit
after both sides of each pair are translated to the common MLB reference.

## Fit artifacts and numerical findings

- V2022: 4,705 forecasts; exact C0 fallback for all players.
- V2023: 5,568 forecasts, 8,744 player-seasons, 15,268 component translation
  rows, and 34,936 development rows.
- V2024: 6,381 forecasts, 12,729 player-seasons, 29,447 component translation
  rows, 69,267 development rows, and 34,892 earlier-origin calibration rows.
- All 16,654 forecast probability vectors are finite, nonnegative, and
  normalized; the maximum simplex error is `4.44e-16`.
- Forecast membership exactly matches the previously frozen predictor-only
  population in every fold.
- The complete 37-artifact output is 18,084,691 bytes. A clean repeat run
  reproduced the exact report hash.

The configuration is deliberately a conservative numerical sentinel, not a
selected production configuration. Its prior choices come from the already
frozen grid, but it is ineligible for validation scoring until training-origin
selection is separately authorized and the final parameters are frozen.

## Implementation incident

The initial run completed V2022 but was stopped during V2023 because forecast
application repeatedly scanned immutable parameter tables. No partial result
was used. Parameter tables are now compiled once per fold into lookup maps. A
scientific invariant proves that compiled application is numerically identical
to the audited primitive implementation.

## Validation and boundary

Canonical lint passed, the focused Stage 2f fit/contract suite passed 19 tests,
and the full repository suite passed 973 tests.

Stop here for review. The next statistically sensible gate is training-origin
configuration selection and final parameter freeze without opening validation
outcomes. Disclosed validation scoring requires a later, separate authorization.
H1, tracking, protected 2026, Stage 3, and WAR remain closed.
