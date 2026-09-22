# Pitcher role and workload transition result

Date: 2026-09-22
Status: **promote into the leading pitcher development ensemble**

## Question

The clean-slate pitcher model already receives three years of games, starts, batters
faced, and levels. Does it make better future-value decisions when the important
transitions are stated directly—starter-to-reliever movement, workload interruption
or rebound, workload trend and peak, level movement, and prior MLB exposure?

## Test

Fifteen derived features were calculated only from the three seasons available at
each historical forecast date. The same six expanding forward tests and the same
zero-inclusive next-season pitcher-value target were used. Ridge, CatBoost, and
LightGBM were tested with the block in arrival, conditional value, and both parts.
No future role, future team, or 2026 outcome was used.

## Engine result

- Ridge improved from 0.31248 to 0.31191 with the block in both parts. Using it only
  for arrival reached 0.31177, and that arrival improvement had a fully favorable
  player-clustered interval.
- CatBoost improved from 0.31282 to 0.31181 with the block in both parts.
- LightGBM improved from 0.31377 to 0.31249 with the block in both parts. Its clearest
  gain came from conditional value after arrival.

This is useful baseball separation: recent role and workload history helps decide
whether a pitcher gets an MLB opportunity, while nonlinear models also use it to
estimate how much work and value an active pitcher will receive.

## Ensemble result

The predeclared ensemble update replaces the ridge, CatBoost, and LightGBM members
with their role-enhanced, two-part versions. All other model members remain unchanged.

| Pitcher development forecast | RMSE |
|---|---:|
| Previous equal nine-model average | 0.31138 |
| Role-enhanced equal average | **0.31109** |
| Previous chronology-pruned average | 0.31128 |
| Role-enhanced chronology-pruned average | **0.31092** |

The equal-average gain is 0.00029 RMSE with a fully favorable 95% interval of roughly
-0.00051 to -0.00006. The best chronology-pruned forecast improves by 0.00036, though
its narrower comparison interval still crosses zero.

## Decision

Use the role-enhanced chronology-pruned ensemble as the leading pitcher development
model. The role block improves all three tested engines, improves the robust equal
average, and has a clear baseball mechanism. It remains a development model rather
than a 2026 forecast because the pitcher target is still defense-independent and does
not yet represent complete pitcher WAR.
