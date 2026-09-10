# Linked pitcher path replay

Status: **promising development replay; not promoted**.

The replay fits the hurdle on the 2018 snapshot, forecasts every eligible 2021
pre-MLB pitcher, uses only six-year career paths complete by the 2021 cutoff, and
scores actual 2022-2025 MLB component WAR. Non-arrivals remain zero.

| Players | Observed mean WAR | Linked predicted | Bias | Linked RMSE | Arrival-only RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|
| 3,649 | 0.090 | 0.105 | +0.016 | 0.553 | 0.551 | 0.576 |

The linked construction is directionally coherent and its broad scale is plausible in
this replay: predicted mean WAR is close to observed and it beats predicting zero.
The tiered path changes MSE versus an arrival-only pooled path by
+0.002193, with a 95% interval of
[-0.005169, +0.008346]. This cohort and hurdle have already
been used in development, so this is not fresh confirmation. No current player value
or rank changes.

The simpler arrival-only path changes MSE versus zero by
-0.028296, with a 95% interval of
[-0.047425, -0.011677].
