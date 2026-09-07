# C2026C result and revised next step

2026-09-06. Both fixed MLB-conditional calibration candidates are rejected.
Neither met the 5% minimum improvement or the complete subgroup guardrails.
The unchanged competition-normalized batting component remains the reference.

| Prior-minor players' MLB wOBA RMSE, PA weighted | 2023 | 2024 | Pooled gain |
|---|---:|---:|---:|
| Unchanged transport | .04502 | .04702 | — |
| MLB event calibration | .04525 | .04565 | 1.18% |
| MLB value calibration | .04516 | .04508 | 1.87% |

Both paired player-cluster uncertainty intervals include zero. Both hurt
established MLB players in 2023; value calibration also fails the all-MLB pooled
guardrail. A better-looking 2024 is not sufficient. Neither is retained or shipped.
No parameter was tuned after seeing the results.

The follow-up audit points toward the opportunity problem. For prior-minor players,
the unchanged transport component's mean wOBA error was:

| Observed MLB exposure (diagnostic only) | 2022 | 2023 | 2024 |
|---|---:|---:|---:|
| At least 100 MLB PA | +.0072 | +.0015 | +.0077 |
| Fewer than 100 MLB PA | +.0486 | +.0367 | +.0430 |

The larger-exposure groups had RMSE .0385/.0366/.0365. Brief call-up groups had
.0952/.0806/.0860 and include 165/142/153 players. These differences are descriptive:
future PA is affected by performance, roster decisions, and other selection. It
must not be inserted as a preseason predictor or used to remove difficult cases.

The age split does not establish a sufficiently strong, stable age-only remedy.
The under-24 group has only 37/31/32 MLB-observed players; it is too small for the
declared 50-player support threshold. Evidence counts are also highly concentrated
and depend on the frozen fold's recency weights. Neither audit supports opening a
large search over age/evidence interactions.

## Current plan

Stop global calibration experiments. Retain the improved competition normalization
as a developmental ability component. Next build an explicit MLB opportunity
cohort: arrival/retention and expected exposure, including players with no MLB PA.
Use only known-at-cutoff level, age, history and recent participation predictors.
Verify missing MLB PBP rows against complete official participation records before
assigning a zero outcome. Do not confuse source exclusion with non-arrival.

This is a necessary piece of the KATOH goal, and may explain part of the remaining
conditional-performance bias. It is not established as the cause by this audit.
Any joint ability/opportunity model needs chronological validation of its own.
The 2022–2024 seasons remain disclosed development data; protected 2026 stays closed.

## Reproduction and integrity

The batch's input hashes and contract were committed before execution. One initial
execution stopped before fitting because imported T2026B vectors store origin
season rather than a forecast-cutoff column. The runner now verifies the original
G0 cutoff and forecast population and restores that metadata; predictions and
parameters were not changed. The successful run retained all candidate vectors.

Full results: `hitter-v2-C2026C-result.json`. Follow-up diagnosis:
`hitter-v2-MLB-error-groups.json`. The latter is explicitly post-result, not a new
promotion test. No website, public model, or frozen v1 output was updated.
