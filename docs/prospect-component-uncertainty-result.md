# Prospect component uncertainty result

Status: calculation complete; keep research-only pending historical coverage tests.

The calculation covers all 6,719 modeled pre-MLB players and preserves every current
point estimate. The largest absolute mean difference is `3.6e-15` WAR. Adding
performance uncertainty therefore changes neither player value nor FV.

The result is not a uniformly wider P10-P90 interval. Only 12.9% of hitter intervals
and 15.3% of pitcher intervals widen. This is mathematically possible because the
mixture has a large exact no-arrival mass and the added noise can move the discrete
10th or 90th percentile inward. It is also why interval width alone is not a valid
selection rule.

For leading prospects, the performance layer does add material upside probability:

| Player | Mean | Component P10 | P50 | P90 | P(18+ WAR) | Workload-only P(18+) |
|---|---:|---:|---:|---:|---:|---:|
| Caden Bodine | 10.06 | 0.11 | 10.00 | 19.09 | 13.03% | 9.03% |
| Rainiel Rodriguez | 9.20 | 0.00 | 8.71 | 19.13 | 12.98% | 10.97% |
| Josuar Gonzalez | 1.83 | 0.00 | 0.00 | 8.67 | 1.62% | 0.51% |
| Tyson Hardin | 3.04 | 0.00 | 2.47 | 7.02 | 0.03% | 0.00% |
| Anthony Eyanson | 2.60 | 0.00 | 1.80 | 6.76 | 0.01% | 0.00% |

These are model-generated distributions, not calibrated confidence intervals. The
next gate is chronology-safe historical coverage by player type and probability band.
Until then, the private explorer continues to show the more limited workload-only
range with its limitation label.

Machine-readable evidence: `docs/prospect-component-uncertainty-result.json`.
Frozen protocol: `docs/prospect-component-uncertainty-plan.md`.
