# Hurdle WAR uncertainty candidate plan

**Status:** frozen before candidate construction and scoring

## Purpose

Replace the *research representation* of one symmetric annual WAR band with the
two-part process the point model already uses:

1. an exact probability of no MLB appearance and therefore zero modeled WAR;
2. a conditional WAR distribution when the player appears.

This is a distribution-form audit. It does not refit arrival, workload, skill, aging
or value, and it cannot change production output from the already inspected 2025
result.

## Candidate

For each player-season, retain the existing `mlb_active_probability`, conditional
workload mean and variance, conditional WAR rate, event-run variance and posterior
run-rate variance.

- No-appearance mass: `1 - mlb_active_probability` at exactly zero WAR.
- Active mean: `conditional workload × conditional WAR rate / workload unit`.
- Active variance: conditional workload variance propagated through the WAR rate,
  plus finite-event and posterior-rate variance conditional on appearing.
- Active shape: a Normal moment approximation with no clipping.
- Combined P10, P50 and P90: exact quantiles of the point-mass/Normal mixture,
  respecting the jump in its cumulative distribution at zero.

The combined expected WAR must reproduce the existing point estimate to numerical
tolerance. Probability, variance and quantile ordering must fail closed when invalid.

## Frozen comparison

Use the same March 27, 2025 forecast universe and like-for-like completed 2025 neutral
WAR target as the prior uncertainty audit. Compare the candidate P10-P90 range with
the current symmetric central 80% range for:

- all hitters, pitchers and whole players;
- observed active/inactive players as descriptive diagnostics;
- the predeclared expected-workload bands already used in the prior audit.

Report coverage with 95% Wilson intervals, lower/upper miss rates and interval width.
Also report mean preservation and the share of candidate medians equal to zero.

## Decision rule and limits

The candidate may be retained for Phase 2 research if it preserves every point mean,
keeps valid ordered quantiles and makes the no-appearance mass explicit. It cannot be
promoted or tuned from this comparison because 2025 has already been inspected.

Coverage alone cannot select between discrete distributions: a large zero mass can
make exact central intervals conservative. Arrival must separately be judged by log
loss, Brier error and calibration; workload and performance must be judged conditional
on forecast-time states. A later rolling-origin build and untouched confirmation are
required before these quantiles become published probability intervals or drive
option exercise and contract value.
