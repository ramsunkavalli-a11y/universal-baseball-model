# Prospect upper-tail calibration result

Status: all recalibration candidates rejected; deployed probabilities unchanged.

## Outer result

Every stage selected regularized Platt calibration on the 2021 development predictions.
None passed both proper scores when those frozen calibration parameters were applied
to the later 2023-origin outer group.

| Player type / stage | Raw log loss | Calibrated | Raw Brier | Calibrated |
|---|---:|---:|---:|---:|
| Hitter arrival | 0.16531 | 0.18623 | 0.04588 | 0.05262 |
| Hitter meaningful given arrival | 0.57503 | 0.58333 | 0.19562 | 0.19855 |
| Hitter established given meaningful | 0.68222 | 0.69307 | 0.24450 | 0.24996 |
| Pitcher arrival | 0.17208 | 0.17168 | 0.04861 | 0.04886 |
| Pitcher meaningful given arrival | 0.58322 | 0.59675 | 0.19859 | 0.20382 |
| Pitcher established given meaningful | 0.63522 | 0.64819 | 0.21894 | 0.22787 |

Pitcher arrival log loss improves by less than 0.0005 but Brier worsens, so it fails
the frozen no-harm gate. The hitter-arrival bootstrap interval is wholly unfavorable;
the other stages are smaller and their intervals generally cross zero.

## Upper tail

For hitter arrival, the raw top decile predicted 53.5% and observed 43.2%. The raw top
1% predicted 87.1% and observed 81.3% across 32 players. Thus the upper decile is
somewhat optimistic, but the most extreme historical group supports genuinely high
probabilities. The earlier-cohort calibration made the later top-decile forecast more
optimistic at 61.8%, not less.

Conditional-stage extreme-tail samples are too small to support special handling.
For example, the hitter established top 1% contains only one player.

## Decision

Keep the raw deployed hurdle probabilities. Do not add a manual probability ceiling,
isotonic tail fit, or outside-FV correction. High individual estimates should remain
visible with uncertainty, while future completed cohorts provide a cleaner calibration
test. The result supports Tango-style regression discipline: apparent calibration in
one cohort is not enough when it fails the next cohort's proper scores.

Machine-readable detail: `docs/prospect-upper-tail-calibration-result.json`.
