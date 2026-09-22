# Hitter gradient challenger v1 result

Status: **first detailed gradient challenger beats the contact-only model overall;
production promotion remains pending**

## Plain-language result

The detailed information finally produced a better next-year hitter forecast when
it was given to a nonlinear gradient-tree model as a correction to the current
contact-only projection. A simple linear ridge correction made the forecast worse.
That contrast matters: the extra information is useful, but its relationships are
not simple straight-line effects.

Across 6,799 genuinely out-of-sample player forecasts from the 2022, 2023, and 2024
origins, the gradient tree improved all three pooled measures:

| Measure | Contact-only | Gradient tree | Change | Relative change |
|---|---:|---:|---:|---:|
| Player-rate RMSE | 0.014597 | 0.014318 | -0.000279 | -1.91% |
| Multinomial log loss | 1.253127 | 1.252908 | -0.000219 | -0.02% |
| Multinomial Brier | 0.001888 | 0.001843 | -0.000045 | -2.37% |

Lower is better for all three. The RMSE improvement appeared in every annual fold:

| Forecast origin | Players | RMSE change vs contact-only |
|---|---:|---:|
| 2022 | 2,269 | -0.000072 |
| 2023 | 2,290 | -0.000364 |
| 2024 | 2,240 | -0.000399 |

## What went into the challenger

The table contains the current contact-only forecast plus 164 source-season
features: overall contact outcomes, ten contact-type shares, all 90 contact-type by
result probabilities, cell sample sizes, age and relative age, level, workload,
batter/pitcher handedness exposure, strictly prior opponent-pitcher strength, and
opponent-adjusted park effects with reliability.

Every evaluation is next season. For example, the 2024 player line predicts 2025.
Training for an evaluation origin uses only earlier origins whose following-season
results would already have been known. No 2026 result was opened.

## Why this is not promoted yet

The overall result is positive, but this is still a development result rather than
the final hitter model.

- Advancing players improved on log loss but were essentially flat/slightly worse
  on RMSE (+0.000055), while same-level and demoted players improved.
- The gain needs a paired player-level uncertainty interval.
- A small predeclared ablation must show whether the gain comes from detailed
  contact cells, opponent context, park context, or merely the tree algorithm.
- The tree settings were fixed for this run; any tuning must happen inside the
  chronological training folds, not against these outer results.

That checkpoint is now complete in `hitter-gradient-ablation-v1-result.md`. The
full model passed and is the leading development base-model candidate. Production
promotion remains reserved for the protected 2026 confirmation.
