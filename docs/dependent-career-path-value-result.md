# Dependent career-path value: first research result

**As of:** 2026-09-08  
**Status:** research only; not used to rank players

## What changed

The simulator now joins arrival, role, workload, performance, attrition, control,
cost and market value in the same path. It samples a complete six-year historical
career shape rather than drawing six unrelated seasons. Zero seasons and later
returns stay in the path. A late arrival shifts the full six-year career into an
11-year calendar window instead of cutting it off.

The historical library contains 3,945 player/type career paths and 23,670 annual
rows from complete 2009-2020 debut cohorts. The run covers 6,719 current pre-MLB
players with 2,048 deterministic draws per player. No publication FV or ranking is
an input.

## Main result

Across all pre-MLB players, simulated controlled WAR is 92.1% of the existing point
estimate and simulated value is 68.3% of the existing benchmark. Most of the value
distribution is rightly concentrated in a small number of players: 6,498 players
have a median outcome of zero, while their nonzero right tails remain in their mean
values.

Examples:

| Player | Arrival | Mean WAR | WAR P10/P50/P90 | Mean value | Value P10/P50/P90 |
|---|---:|---:|---:|---:|---:|
| Caden Bodine | 97.8% | 9.4 | 0.2 / 9.1 / 18.2 | $66.6M | $0.2M / $59.4M / $138.4M |
| Rainiel Rodriguez | 92.3% | 8.3 | 0.0 / 7.2 / 18.1 | $57.1M | $0 / $43.8M / $132.9M |
| Josuar Gonzalez | 20.0% | 1.7 | 0.0 / 0.0 / 8.1 | $10.8M | $0 / $0 / $46.1M |

Josuar illustrates why a single point estimate is misleading: the most likely path
has no MLB value, but a real high-value tail keeps his mean near $10.8M.

## Statistical and Tango-style checks

- Forecast inputs stop before the outcome period; 2026 partial results are excluded.
- Failures and zero seasons remain in the sample, so survivor bias is not hidden.
- Whole careers are sampled, preserving attrition, returns and pitcher role changes.
- Persistent skill uncertainty is shared across a career; annual event noise is not.
- WAR is not clipped. Only the declared market pricing rule floors negative free-agent
  equivalent production.
- Same-season realized WAR never decides that season's tender.
- Output probability identities, finite values, nonnegative costs, ordered quantiles,
  deterministic reruns and 21 existing model-law checks pass.

## What is still provisional

Do not promote this result to the main ranking yet. Arrival timing uses a constant
annual hazard. Any active season currently counts as a full service year. Super Two,
partial service, forecast-time non-tender rules, guarantees/options and the post-2026
CBA still need explicit treatment. The 2025 origin has already influenced development;
later rolling origins must select the method and a subsequent untouched origin must
confirm it.

Machine-readable details are in `dependent-career-path-value-result.json`.
