# Next prerequisite: dated projection states for development paths

2026-09-23. Input-building checkpoint, **not an approved model or a new fit contract**.
Read the population-repair result and `c1-feasibility.json` first. A population
repair result must not determine a convenient new target or a post-hoc blend.

## What to build

One keyed, documented archive of forecasts that could actually have been made at
each historical snapshot. Begin with a three-year scope, not unsupported full
control value. Recover the accepted algorithms and their vintage training rules;
do not just apply today's fitted coefficients to old players.

Each row needs origin, player identity, source cutoff, training-label cutoff,
forecast horizon, model/version, and separate outputs for:

- predicted MLB participation and conditional workload;
- the explicitly defined conditional batting/replacement rate;
- unconditional delivered batting/replacement value;
- known current role/exposure and missingness, without future-derived career tiers.

Those outputs are not interchangeable. In particular, unconditional value divided
by expected PA is not an independently identified talent estimate. A rate learned
only from later MLB participants has a selection limitation for never-debuted
players, even when it is evaluated as part of a useful all-player value model.

## Reuse, then fill only genuine gaps

- Existing H1 rate anchors cover 2012 onward, apart from the documented missing
  seasons, and carry explicit vintage fields. Preserve these as research inputs;
  the rejected H2 change model does not become the accepted development model.
- Existing H1–H3 opportunity replays start in 2016. Backfill earlier supported
  origins from the source panel with date-safe training. Verify the recovered
  recipe on existing overlap before claiming equivalent older forecasts.
- Earlier unconditional quantiles exist, but they do not supply conditional rate
  states or joint career dependence. Reuse them only for their actual target.
- The annual panel starts in 2009. Do not fabricate a trained 2009 anchor without
  earlier training data. Explicitly inventory which early donor origins must be
  unavailable, and whether the remaining support is sufficient before fitting.

## Completion checks before C1

1. Unique origin/player/horizon keys, immutable source hashes, and training labels
   never later than the origin. Mutating later outcomes must not change a forecast.
2. Full starting populations include no-play, never-debuted and inactive states.
   Missing conditional rate remains unknown, never a zero-talent observation.
3. Reproduce available overlap forecasts; document any necessary software or source
   difference rather than silently calling a changed recipe the same baseline.
4. Inventory the eligible training support at each outer cutoff, especially young
   brief-MLB and never-debuted groups. A 2016 outer forecast cannot train on a 2016
   forecast error whose outcome was not yet known then.
5. Freeze one new path specification only after the archive passes. Specify how
   current performance, development and availability influence one another; which
   uncertainty persists; and which realized noise is already present in residuals.
6. Compare against the stronger delivered model and the completed distribution
   controls. No new success threshold, public-FV floor or forced mean alignment.

This checkpoint does not certify six-year accuracy, full WAR, service/rights,
salary obligations, future entrant ownership or the beyond-2031 liability tail.
Those remain separately required before player dollar values.
