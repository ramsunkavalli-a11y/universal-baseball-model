# Prospect early-history rate-only result

**Decision:** `reject_rate_only_family`

A rate-only model was fitted on 2003 and applied unchanged to untouched 2006 and 2007 cohorts. Negative differences favor the candidate.

| Type | Origin | Players | Brier difference | Log-loss difference | Both improve |
|---|---:|---:|---:|---:|---:|
| hitter | 2006 | 194 | -0.0033 | -0.0071 | True |
| hitter | 2007 | 186 | -0.0014 | -0.0026 | True |
| pitcher | 2006 | 215 | 0.0024 | 0.0046 | False |
| pitcher | 2007 | 210 | -0.0059 | -0.0113 | True |

## Why

- hitter: 2/2 origins improve both scores; pooled_interval_pass=False; supported_reversals=2
- pitcher: 1/2 origins improve both scores; pooled_interval_pass=False; supported_reversals=3

The production model was not changed.
