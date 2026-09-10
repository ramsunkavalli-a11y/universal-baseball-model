# Prospect shortstop-retention plan

Status: preregistered before candidate fitting or scoring.

## Question

Can universally available, cutoff-safe player evidence improve the position value
assigned to arriving hitter prospects, especially players whose minor-league usage is
led by shortstop?

This is a position-persistence test, not a talent model. It is conditional on a player
later recording MLB fielding usage, so it must not change arrival probability, batting
quality, or playing time.

## Evidence and chronology

- Origin evidence: official minor-league fielding usage in one season.
- Fixed features: age on July 1, highest level reached, log total fielding exposure,
  exact-position exposure shares, number of positions used, and the origin weighted
  positional-run value.
- Target: exposure-weighted MLB positional runs per 162 games in the next season.
- Development: train on 2021-2022 origins and select on 2023 origins using MLB
  outcomes through 2024 only.
- Outer check: refit on 2021-2023 origins and score once on 2024 origins whose MLB
  fielding usage occurs in 2025.
- Birth date comes from the pinned historical people source. No future performance,
  organization depth, public FV, or named-player adjustment is allowed.

## Fixed candidate ladder

The baseline carries the origin season's exact-position weighted positional runs
forward. Ridge candidates use standardized features and alpha values 1, 10, and 100:

1. `workload`: baseline runs, age, level, and log exposure.
2. `role_detail`: workload plus exact-position shares and position count.

Select the development candidate with the lowest overall MAE among candidates that
also beat the baseline on overall RMSE and on both MAE and RMSE for players whose
dominant origin position is shortstop. Ties choose the simpler feature set and then
the stronger ridge penalty.

## Promotion gate

The selected candidate passes only if the untouched outer group improves:

- overall MAE and RMSE; and
- shortstop-origin MAE and RMSE.

Report bias, bootstrap uncertainty, and shortstop retention calibration as
diagnostics. Failure leaves production unchanged. A passing result authorizes only a
private value sensitivity; it does not directly authorize a published value change.

The next-season horizon is deliberate. The earlier exploratory position-transition
audit used two-season destination windows that overlap later origin cutoffs. That
design remains useful as a descriptive transition table but is not eligible to train
or promote this player-level challenger.
