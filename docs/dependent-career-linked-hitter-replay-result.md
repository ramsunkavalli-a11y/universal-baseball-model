# Linked hitter path replay

Status: **development replay complete; not promoted**.

This scores batting plus replacement only. Defense, baserunning and position are
excluded from both predictions and outcomes because matching historical components
are not available at the required player-season grain.

| Players | Observed mean WAR | Incumbent mean | Linked mean | Incumbent RMSE | Linked RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|
| 3,251 | 0.144 | 0.211 | 0.062 | 0.958 | 0.979 | 1.005 |

The direct-evidence cap applied to the tier-linked path predicts
0.056 mean WAR with 0.976 RMSE and
0.216 MAE.

The arrival-only linked path changes MSE versus the cutoff-reconstructed incumbent by
+0.041123, with a player-bootstrap 95% interval
of [-0.067171, +0.163011]. The 2021 cohort has already
been used in development, so this cannot promote a model or change current values.

The common-cohort guardrail finds the opposite metric tradeoff from pitchers: MAE
improves from 0.313 to
0.221, but RMSE and absolute mean bias worsen. The path
mostly improves the large non-arrival group while underpredicting the smaller group
that reaches MLB, so it remains rejected.

The same pattern persists from one through four years: candidate RMSE is worse at
every prefix. MAE improves after year one because forecasts move toward zero, not
because the model captures the positive MLB tail.

A fixed 25% linked / 75% incumbent blend is promising development evidence: RMSE
improves 0.958 to 0.946, MAE
improves 0.313 to 0.288, and
absolute bias improves. Its paired MSE interval still crosses zero, and the exposed
cohort was used to view the weight, so it is not promoted or used in current values.
