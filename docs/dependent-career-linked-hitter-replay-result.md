# Linked hitter path replay

Status: **development replay complete; not promoted**.

This scores batting plus replacement only. Defense, baserunning and position are
excluded from both predictions and outcomes because matching historical components
are not available at the required player-season grain.

| Players | Observed mean WAR | Incumbent mean | Linked mean | Incumbent RMSE | Linked RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|
| 3,260 | 0.144 | 0.207 | 0.060 | 0.955 | 0.978 | 1.004 |

The arrival-only linked path changes MSE versus the cutoff-reconstructed incumbent by
+0.043290, with a player-bootstrap 95% interval
of [-0.062613, +0.167608]. The 2021 cohort has already
been used in development, so this cannot promote a model or change current values.

The common-cohort guardrail finds the opposite metric tradeoff from pitchers: MAE
improves from 0.310 to
0.220, but RMSE and absolute mean bias worsen. The path
mostly improves the large non-arrival group while underpredicting the smaller group
that reaches MLB, so it remains rejected.
