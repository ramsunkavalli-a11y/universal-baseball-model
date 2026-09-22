# Hitter level tenure and development path result

Status: **useful for MLB-arrival probability; not selected as a general hitting-skill adjustment**

## What was built

The historical hitter data now produces explicit, chronology-safe fields for:

- plate appearances and share of playing time at every level;
- primary, highest, and end-of-season level;
- years, consecutive years, and career plate appearances at the current level;
- same-level repeats and third-or-later seasons at a level;
- promotions, demotions, returns to the prior terminal level, and previous peaks;
- the difference between a full repeat and returning after a short late promotion;
- advancement speed across a player's affiliated career.

The end-of-season level comes from the last dated contact when that evidence is
available. Annual level plate appearances determine whether the terminal stint was a
brief exposure or a substantial part of the season. Missing terminal evidence remains
explicit rather than being presented as exact.

Carlos Concepcion's 2025 row now correctly says that he had:

- three seasons at the rookie level;
- three consecutive seasons there;
- 528 career plate appearances at that level;
- 196 current-season plate appearances;
- no level advancement;
- a substantial same-level repeat, not a return after a partial promotion.

## What was tested

Every test used the incumbent six forward-test seasons and the same five-model
ensemble. The frozen 2026 forecast and all 2026 results remained untouched.

### Adding the entire path block everywhere

| Model | Expected-WAR RMSE |
|---|---:|
| Incumbent | 0.432116 |
| Full path block | 0.432599 |

This worsened established-MLB forecasts enough to outweigh small improvements for
upper- and lower-minors hitters.

### Compact nonredundant path block

The compact version removed fields that largely duplicated existing PA and level
inputs. It retained only tenure, terminal-level, repeat, partial-promotion, prior-peak,
and advancement-speed information.

| Model | Expected-WAR RMSE |
|---|---:|
| Incumbent | 0.432116 |
| Compact path block everywhere | 0.432437 |

It improved arrival-probability Brier score from 0.049975 to 0.049924 and log loss
from 0.165267 to 0.164773, but allowing the path fields to refit hitting strength still
worsened overall expected-WAR RMSE.

### Dedicated pre-MLB model

A separate model trained only on pre-MLB hitters improved lower-minors error but
materially worsened upper-minors error. Its routed whole-population RMSE was 0.433362,
so stage-specific training is not selected.

### Arrival-only use

The final test froze the incumbent direct and conditional hitting-strength estimates.
The compact path model was allowed to change only the probability of MLB activity.

| Model | Expected-WAR RMSE |
|---|---:|
| Incumbent | 0.432116 |
| Path-enhanced arrival only | **0.431916** |

The RMSE improvement was 0.000200. Its player-clustered 95% interval ran from a
0.000409 improvement to a 0.000012 worsening. It improved expected-WAR RMSE in five
of six forecast seasons; 2024 was the lone small reversal. Brier score and log loss
both improved.

## Decision

Retain the compact level-path block as a development challenger for MLB-arrival
probability. Do not let it alter hitting-strength estimates and do not modify the
frozen 2026 forecast.

The tests do **not** validate a manual repeat-level penalty to Hit/600. That display is
a conditional MLB hitting estimate, and very low-arrival players such as DSL hitters
provide almost no next-season MLB evidence with which to validate it.

The follow-up all-level test is now complete. It translated each player's actual
next-season performance, at whatever affiliated level he reached, onto one common MLB
scale. The compact path block slightly worsened overall RMSE (0.035152 to 0.035178).
It made only a very small improvement for third-or-later rookie-level hitters and did
not justify changing the hitting-strength model. See
`docs/hitter-future-translated-performance-result.md`.

## Files

- Feature construction: `src/universal_baseball/hitter_level_path_features.py`
- Full and compact evaluation: `scripts/evaluate_hitter_level_path_features_v2.py`
- Pre-MLB routing test: `scripts/evaluate_hitter_level_path_routing_v2.py`
- Arrival-only test: `scripts/evaluate_hitter_level_path_arrival_only_v2.py`
- Full results: `reports/generated/hitter-level-path-feature-ablation-v2/`
- Compact results: `reports/generated/hitter-level-path-compact-ablation-v2/`
- Routed results: `reports/generated/hitter-level-path-routing-v2/`
- Arrival-only results: `reports/generated/hitter-level-path-arrival-only-v2/`
