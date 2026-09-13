# Six-calendar-year prospect comparable test

**Decision:** Do not promote the six-calendar-year comparable total as controlled WAR.

The experiment extended the existing comparable outcome from four to six calendar
years. It retained every player, counted non-arrivals as zero and continued to use
only batting-plus-replacement or pitching-plus-replacement production.

The longer horizon failed even as an optimistic retrospective diagnostic. The
reference outcome window overlaps the diagnostic target origin, so these numbers are
not a chronology-safe held-out gate and cannot authorize production use. Despite that
advantage, comparable matching had worse RMSE and worse arrival probability scores
than a population average for both hitters and pitchers. Conditional production among
players who reached MLB improved, but that does not repair the all-player result.

| Type | Total MAE | Baseline MAE | Total RMSE | Baseline RMSE | Arrival Brier | Baseline Brier |
|---|---:|---:|---:|---:|---:|---:|
| Hitters | 0.580 | 0.596 | 1.408 | 1.324 | 0.126 | 0.116 |
| Pitchers | 0.350 | 0.353 | 0.878 | 0.840 | 0.142 | 0.126 |

These are calendar-year outcomes, not six MLB service seasons. They omit hitter
defense, baserunning and position. Therefore they cannot define controlled WAR or an
FV scale. The explorer instead shows the repo's separately validated six-year MLB
arrival probability, the four-year historical comparable outcome, and conditional
MLB quality as distinct fields.

No public FV grade was used to fit or change the model.
