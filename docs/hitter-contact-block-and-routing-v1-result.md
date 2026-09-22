# Hitter contact block and routing result

Status: **current five-model batting baseline retained; 2026 outcomes remain sealed**

## Plain-language conclusion

The detailed contact-result history is earning its place in the hitter model. Removing
it makes the next-year value forecast worse. A smaller summary of where hitters put
the ball does not recover the lost accuracy, and adding that summary on top of the
detailed cells also does not help.

The best current batting model therefore remains the equal average of direct
LightGBM, three-part LightGBM, two-part XGBoost, two-part EBM, and two-part ridge,
using three years of age, level, workload, ordinary batting, and detailed contact
results.

## Contact-information ablation

Every challenger used the same five model families, target, player population, and
six chronological forecast seasons. Only the input information changed.

| Information supplied | RMSE |
|---|---:|
| Current detailed contact cells | **0.432116** |
| Ordinary stats only | 0.433919 |
| Ordinary stats plus compact contact shape | 0.433649 |
| Detailed contact cells plus compact contact shape | 0.432722 |

Removing detailed contact worsened RMSE by 0.001803. The player-clustered 95% range
was 0.000044 to 0.003567 worse, so this is small but credible evidence that the
detailed cells improve the value forecast.

The benefit is concentrated among players already in MLB, whose RMSE was 0.970405
with detailed contact and 0.974873 without it. Detailed contact was essentially
neutral for the low-minors population. This makes baseball sense: contact history can
separate the future production of players likely to receive meaningful MLB playing
time, while it cannot solve the arrival problem by itself.

## Why the compact contact summary stays out

The park-neutral contact-shape block describes ground balls, line drives, outfield
balls, popups, and field direction with far fewer fields. It did not improve direct
next-year MLB outcome composition, and it did not improve the five-model value
ensemble either.

- Replacing detailed contact with shape: 0.001533 worse RMSE; uncertainty included a
  very small possible gain but favored harm.
- Adding shape to detailed contact: 0.000606 worse RMSE; uncertainty crossed zero.
- Arrival Brier score and log loss both worsened when shape was included.

The park adjustment itself remains useful for describing past events. This result
says the compact adjusted player summary is not an additional forecasting signal in
the present model.

## Feature routing

Ordinary stats estimated next-year MLB participation very slightly better than the
detailed-contact model. A routed challenger therefore used ordinary-stat arrival
probabilities for the four decomposed ensemble members while retaining their
detailed-contact conditional-value estimates. The direct LightGBM member was left
unchanged.

| Model | RMSE |
|---|---:|
| Current baseline | 0.432116 |
| Routed arrival challenger | **0.431932** |

The routed model improved four of six seasons and all three player-stage groups, but
the pooled gain was only 0.000184 RMSE and its 95% range ran from 0.000542 better to
0.000180 worse. Its Brier and log-loss gains were also uncertain. Keep this as a
principled 2026 confirmation challenger, not as a replacement for the base.

## Dedicated current-MLB expert

Because current MLB hitters account for most squared error, a separate five-model
expert was trained only on player-seasons that already had MLB plate appearances.
That hard split lost useful information from the larger mixed population.

| Current-MLB hitter model | RMSE |
|---|---:|
| Shared population baseline | **0.970405** |
| Dedicated incumbent expert | 0.976385 |

The incumbent expert was 0.005980 worse, with a fully unfavorable 95% range of
0.002282 to 0.009912 worse. Routing it into the full population worsened total RMSE
from 0.432116 to 0.434497. Close this branch; the broad models already learn the
useful stage differences while benefiting from more training data.

## Decision

1. Retain the current equal-weight five-model batting baseline.
2. Retain the existing detailed contact-result cells.
3. Do not add or substitute the compact contact-shape block.
4. Do not use a hard current-MLB specialist.
5. Preserve stats-only arrival routing as an unpromoted 2026 challenger.
6. Continue to keep 2026 outcomes untouched until the protected confirmation test.
