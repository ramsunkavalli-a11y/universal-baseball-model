# Pitcher workload environment as-of plan

Status: frozen before scoring.

## Question

Does separating the changing MLB pitcher-usage environment from a pitcher's relative
career path improve the conditional six-year workload distribution?

## Frozen comparison

Evaluate the 2018 and 2019 debut cohorts. A training path is eligible only when its
complete six-year window ended before the evaluation year. Compare three empirical
distributions on identical pitchers:

1. raw historical workload within eventual outcome tier;
2. each historical annual workload divided by that season's MLB mean BF per active
   pitcher, then mapped into the forecast environment; and
3. the same environment-relative path with a supported granular role cell.

The forecast environment is a five-year log-linear trend in MLB mean BF per active
pitcher, using seasons strictly before the forecast date. Annual change is bounded to
five percent. The role cells are rotation, opener, bulk/swing and relief. Rotation
requires at least half of appearances to be starts and at least 18 BF per start;
otherwise a majority-start path is an opener. Cells with fewer than 30 complete
training careers fall back to outcome tier.

## Score and boundary

Use empirical CRPS, P10-P90 coverage, median error and tier/role diagnostics. This is
conditional on the evaluation player's eventual career tier and role, so it tests the
workload distribution only. It cannot validate role prediction, arrival, skill or
value. The already inspected 2018-2019 cohorts are development evidence, not an
untouched promotion gate. No 2026 outcome or outside FV enters the test.
