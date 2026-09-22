# Clean-slate pitcher model v2 milestone

Date: 2026-09-22

## What we tested

We rebuilt the one-year pitcher comparison from a common historical panel instead of
starting from the previous pitcher formula. The panel contains 66,326 pitcher-seasons,
uses up to three prior seasons, and explicitly represents the missing 2020 minor-league
season. The six forward tests score 29,491 player-seasons from 12,753 pitchers. Each
test trains only on earlier origin seasons and predicts 2018, 2019, 2022, 2023, 2024,
or 2025 MLB value. No 2026 result is used.

The common inputs are available broadly across levels: age, reported-age status,
level, role, games, starts, batters faced, and season/level-relative strikeout,
unintentional-walk, hit-batter, home-run, and other-batter rates. Detailed pitch and
contact data are deliberately excluded from this first comparison so they can be
tested later as honest additions.

The target is next-season MLB component value. It gives pitchers credit for workload,
strikeouts, walks, hit batters, and home runs while treating the remaining batters
faced at the league-average value. A pitcher absent from MLB the following year has a
zero result. This target is useful for testing defense-independent pitching talent,
but it is not yet complete pitcher WAR.

## What the evidence says

### Target design

| Design | Ridge | CatBoost | EBM | LightGBM |
|---|---:|---:|---:|---:|
| Predict total value directly | 0.3316 | 0.3146 | 0.3189 | 0.3161 |
| Arrival chance x value if active | **0.3125** | **0.3128** | **0.3131** | **0.3138** |
| Arrival chance x workload x rate | 0.3235 | 0.3184 | 0.3233 | 0.3202 |

The two-part design wins for every tested engine. Separately multiplying an arrival
estimate, workload estimate, and rate estimate compounds errors and forecasts too
little total value. Direct prediction also loses, especially for the linear model.

### Model engines on the selected two-part design

| Engine | Expected-value RMSE |
|---|---:|
| Ridge | **0.3125** |
| CatBoost | 0.3128 |
| NGBoost | 0.3131 |
| Explainable Boosting Machine | 0.3131 |
| LightGBM | 0.3138 |
| Extra Trees | 0.3145 |
| XGBoost | 0.3162 |
| Histogram gradient boosting | 0.3164 |
| GPBoost | 0.3240 |

Zero and historical-mean baselines score 0.4303 and 0.4216. XGBoost has the best
arrival probabilities, but its conditional value estimate is weak enough that it
does not win the full forecast. The nonlinear models do not uncover a large hidden
gain in these broad season-summary inputs. That is useful evidence, not a failure of
the algorithms: most of the signal in this input block is smooth, noisy, and heavily
regressed.

An equal nine-model average scores 0.3114. A chronology-pruned average, which chooses
members using only earlier completed test folds, scores 0.3113. The pruned ensemble
beats ridge in five of six seasons and in MLB, Triple-A, lower-level, starter, and
reliever subgroups. Its improvement over ridge is about 0.0012 RMSE, with a player-
clustered 95% interval of roughly -0.0033 to +0.0009. The direction is encouraging,
but the interval crosses zero.

## Decision

1. Use the two-part architecture for pitcher development: MLB arrival probability
   multiplied by total value conditional on being active.
2. Keep ridge as the leading simple model and the chronology-pruned ensemble as the
   development challenger. Do not declare the ensemble a proven promotion yet.
3. Do not freeze a 2026 pitcher forecast from this milestone. The target still omits
   the value of singles, doubles, triples, and fielding-dependent contact.
4. Add new information in named blocks and require a forward-test improvement. The
   next blocks are a richer contact/run-prevention target, high-minors pitch process,
   and prior-only park/opponent context.

## Important blind spot

The current outcome is closer to a workload-scaled defense-independent component
value than complete pitching WAR. It deliberately prevents defense and park luck from
masquerading as pitcher talent, but it also cannot reward a pitcher who persistently
allows weak contact. Before treating detailed contact as a model feature, we need a
separate, fair contact-value target that adjusts past balls in play for park,
opponent, and defensive context. Simply switching to raw ERA or runs allowed would
replace one omission with much more noise.

## Reproducibility

- `scripts/materialize_pitcher_value_panel_v2.py` builds the common panel.
- `scripts/compare_pitcher_model_engines_v2.py` runs the nine-engine tournament.
- `scripts/compare_pitcher_target_architectures_v2.py` compares the three target
  designs.
- `scripts/evaluate_pitcher_ensemble_v2.py` builds and scores the chronology-safe
  ensemble.

The generated prediction tables remain local development artifacts. Code, tests, and
this decision record are committed together; 2026 outcomes remain protected.
