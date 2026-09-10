# Pitcher workload era candidate result

Status: all simple era candidates rejected; timing defect blocks selection use.

The six-year paths of earlier debut cohorts were not complete at each later cohort's
debut date. These are retrospective cohort comparisons, not true forward forecasts.
The scores below remain diagnostic and cannot authorize any candidate.

The frozen test compared 226 pitcher careers across the 2017, 2018, and 2019
debut cohorts using earlier-debut cohorts. The incumbent's mean
CRPS was 333.88 and its P10-P90 coverage was 68.1%.

The strongest overall challenger used a one-year recency half-life while retaining
supported role cells. CRPS improved to 329.60, including 468.73 to 460.68 among
established pitchers. It failed the predeclared safety gate because fringe-pitcher
CRPS worsened from 95.43 to 97.59, more than 1%. Its P10-P90 coverage barely moved,
from 68.1% to 68.6%.

Always pooling roles made ranges wider and raised coverage to 74.8%, but CRPS worsened
materially to 372.47. Wider alone is not better calibrated. The latest-two-cohort and
two-year-half-life candidates also failed the full gate.

## Decision

Reject all eight candidates. Independently measured pitcher usage across eras is real evidence, but
neither simple recency weighting nor removing role information solves both accuracy
and coverage. Retain the current point model and the explicit under-coverage warning.

The next workload candidate should first build a valid as-of outcome replay, then model the annual MLB pitcher-usage environment
separately from player rank/role, then combine environment uncertainty with a
role-specific relative workload distribution. Freeze it before scoring. No current
player value, outside FV, or 2026 outcome entered this test.

Machine-readable evidence: `docs/pitcher-workload-era-candidate-result.json`.
Frozen protocol: `docs/pitcher-workload-era-candidate-plan.md`.
