# Prospect workload as-of validation result

Status: conditional workload method passes the chronology-safe historical replay.

The test evaluates 2018 and 2019 debut cohorts. For each year, every training career's
six-year outcome window ended before January of the evaluation year. The replay covers
372 hitters and 354 pitchers.

| Player type | Players | P25-P75 coverage | 95% Wilson interval | P10-P90 coverage | 95% Wilson interval |
|---|---:|---:|---:|---:|---:|
| Hitter | 372 | 53.2% | 48.1%-58.2% | 90.6% | 87.2%-93.2% |
| Pitcher | 354 | 47.7% | 42.6%-52.9% | 81.1% | 76.7%-84.8% |

Pitcher coverage retains both stated targets. Hitter central coverage retains 50%,
while its nominal 80% range is conservative and covers about 91%. The hitter
over-coverage is concentrated in fringe and meaningful-only careers; established
hitter coverage retains 80% within sampling uncertainty.

Pitcher established and pooled/role-source groups retain both targets. The 43-player
meaningful-only pitcher group covers 67.4% at P10-P90 and its Wilson upper bound is
just below 80%; this remains a disclosed small subgroup weakness.

## Decision

Retain the current empirical workload layer as a labeled conditional reference
distribution. Remove the prior screen warning that pitcher ranges are too narrow;
that conclusion came from a cohort comparison whose training paths were not mature at
the claimed forecast dates. Do not call the displayed mixture a full confidence
interval: arrival, predicted tier/role, skill, aging, injury, and value calibration
remain separate.

Machine-readable evidence: `docs/prospect-workload-asof-validation-result.json`.
Frozen protocol: `docs/prospect-workload-asof-validation-plan.md`.
