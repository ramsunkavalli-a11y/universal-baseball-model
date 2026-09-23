# Does detail better identify future major leaguers?

2026-09-23. Fixed, matched-population probability experiment. No live forecasts changed.
No protected 2026 outcomes used. These are exposed historical development results.

## Plain-language finding

More detail helps next-year arrival on average in the tree model: Brier improves about 1.4%
and log loss about 2.0% versus aggregate batting history. Both paired intervals favor detail.
It also beats the coverage control on those pooled scores. But only three of six years improve,
and the logistic family gets worse with the same full detail. This is a useful lead, not a stable upgrade.
Against the stronger existing probability ensemble on their shared four years, Brier is slightly
better but log loss is worse. The weak basic control is not the final benchmark.

Three-year arrival improves versus aggregate stats, but its additional gain over coverage controls
is uncertain, and it still expects only 460 arrivals versus 649 observed player-origin cases.
For becoming a regular, full detail expects 19 cases versus 31 observed; the coverage control
expects 23 and has better proper scores. Merely adding all fields does not solve that problem.
The simpler logistic coverage model also beats the rich tree model for three-year arrival,
so the remaining issue is not demonstrably just missing detail. No arm is deployed.

## What was tested

Same players, training cutoffs, identity weights and model settings; only inputs change.
The full challenger includes batting history, level progression, raw contact-type/direction ×
outcome bins, park-adjusted contact residuals, universal pitch-result rates, and available
prior-opponent context. Coverage controls isolate information from simply having more data.
No synthetic balancing of arrival counts, class weighting or post-hoc calibration was used.
LightGBM is the controlled main comparison; fixed regularized logistic models check family dependence.
The unit is a player at a season-end snapshot, not an independent career per row.

Input counts: B0=24, B1=78, B2=145, D=172, C=859, R=886.
Constant or unobserved training fields are dropped separately within each fit and recorded.

## Never-debuted minor leaguers

Lower Brier and log loss are better. Expected counts are sums of probabilities, not counts
of players above an arbitrary cutoff. A player appearing in two test seasons appears twice.

### MLB appearance next year

Status: `promising_not_confirmed`. 19,247 snapshots, 8,805 players, 6 test origins.
Observed events: **677**.

| Inputs | Expected events | Brier | Log loss |
|---|---:|---:|---:|
| Age / level / workload | 577.7 | 0.027137 | 0.097128 |
| Aggregate batting history | 546.2 | 0.024284 | 0.085010 |
| History + coverage controls | 618.4 | 0.024420 | 0.085182 |
| + development detail | 630.1 | 0.024270 | 0.083735 |
| + contact / pitch / context | 585.8 | 0.024088 | 0.084454 |
| + all detail (primary) | 600.6 | 0.023948 | 0.083329 |

Paired full-detail minus coverage-control differences (player-cluster 95% intervals):

- brier: -0.000472, [-0.000793, -0.000158]; 3/6 origins improve.
- log_loss: -0.001853, [-0.002921, -0.000773]; 3/6 origins improve.

Predeclared checks: support=pass, brier_and_log_intervals=pass, majority_origins=not passed, calibration=pass, logistic_direction=not passed, stage_guards=pass.
Logistic family check: Brier 0.025795 → 0.029792; log loss 0.087768 → 0.114722.

### MLB appearance within three years

Status: `promising_not_confirmed`. 6,438 snapshots, 4,073 players, 2 test origins.
Observed events: **649**.

| Inputs | Expected events | Brier | Log loss |
|---|---:|---:|---:|
| Age / level / workload | 370.6 | 0.076056 | 0.263144 |
| Aggregate batting history | 426.2 | 0.067062 | 0.223868 |
| History + coverage controls | 497.0 | 0.064982 | 0.215716 |
| + development detail | 515.2 | 0.063961 | 0.211639 |
| + contact / pitch / context | 448.5 | 0.064756 | 0.215230 |
| + all detail (primary) | 460.0 | 0.064260 | 0.213320 |

Paired full-detail minus coverage-control differences (player-cluster 95% intervals):

- brier: -0.000722, [-0.001669, +0.000205]; 2/2 origins improve.
- log_loss: -0.002396, [-0.005622, +0.000935]; 2/2 origins improve.

Predeclared checks: support=not passed, brier_and_log_intervals=not passed, majority_origins=pass, calibration=not passed, logistic_direction=not passed, stage_guards=pass.
Logistic family check: Brier 0.060176 → 0.070874; log loss 0.203176 → 0.243125.

### 450+ PA in at least two of three years

Status: `richer_bundle_not_supported`. 6,438 snapshots, 4,073 players, 2 test origins.
Observed events: **31**.

| Inputs | Expected events | Brier | Log loss |
|---|---:|---:|---:|
| Age / level / workload | 16.0 | 0.004664 | 0.024465 |
| Aggregate batting history | 18.2 | 0.004426 | 0.020164 |
| History + coverage controls | 23.2 | 0.004345 | 0.019275 |
| + development detail | 22.5 | 0.004332 | 0.019298 |
| + contact / pitch / context | 18.1 | 0.004449 | 0.021036 |
| + all detail (primary) | 19.2 | 0.004420 | 0.020267 |

Paired full-detail minus coverage-control differences (player-cluster 95% intervals):

- brier: +0.000074, [-0.000137, +0.000316]; 1/2 origins improve.
- log_loss: +0.000991, [-0.000247, +0.002326]; 0/2 origins improve.

Predeclared checks: support=not passed, brier_and_log_intervals=not passed, majority_origins=not passed, calibration=not passed, logistic_direction=not passed, stage_guards=pass.
Logistic family check: Brier 0.004599 → 0.005783; log loss 0.019939 → 0.039566.

## Practical references on identical available rows

These are supplementary stronger historical references, not the controlled feature experiment.
Their training recipes and weights differ. Do not read a feature win over B0 as beating the incumbent.

| Target | Reference | Rows | Full-detail Brier / reference | Full-detail log loss / reference |
|---|---|---:|---:|---:|
| next_year | accepted_C2 | 13127 | 0.024823 / 0.028905 | 0.086902 / 0.104671 |
| next_year | earlier_ensemble | 13127 | 0.024823 / 0.024927 | 0.086902 / 0.085709 |
| arrival_three | F1 | 6438 | 0.064260 / 0.082608 | 0.213320 / 0.313373 |
| arrival_three | A1 | 6438 | 0.064260 / 0.080486 | 0.213320 / 0.281470 |
| regular_three | F1 | 6438 | 0.004420 / 0.004680 | 0.020267 / 0.027717 |
| regular_three | A1 | 6438 | 0.004420 / 0.004687 | 0.020267 / 0.025528 |

## Limits and decision boundaries

- One-year normal tests: 2017, 2018, 2021–2024. Three-year normal tests: only 2021/2022; they overlap in outcome years.
- The three-year confirmation gate remains failed because fewer than three normal origins exist. The separate 2019 pandemic stress is not pooled into it.
- Raw contact history begins in 2015, park/pitch detail in 2016, prior-opponent context in 2021. At the three-year cutoffs, the latter has no mature training examples and is dropped—not tested successfully.
- Earlier history is retained for both controls and challengers; missing PBP does not remove a player. That gives baseline history, not extra early detailed examples.
- Cold-identity 2022 results and all starting-group/annual/calibration/discrimination results are in score-report.json. Auxiliary features are vintage-safe but not a fully refitted cold-identity auxiliary pipeline.
- The cold test severely underpredicts in both arms. Removing every 2022 player also removes many historical survivors: prospect training arrival frequency falls from 3.11% to 1.73%, and regular-workload frequency from 0.332% to 0.094%. This is a population-shift stress, not a random-player holdout or proof that identity leakage explains the ordinary result. See cold-population-audit.json.
- Year-end reconstruction and previous feature recipe choices are exposed development evidence, not historically issued forecasts.
- Regular workload does not measure hitting quality or full WAR. Even a probability improvement needs a separate delivered-value test before deployment.
- No after-the-fact selection of D/C, blending, probability inflation, model retuning or public-FV floor is applied.

Completed 102 fits; future-label/predictor mutation maximum probability change: 0.0.
Model settings, source hashes, dropped features, coverage and training maturity are retained in the package.

## Next bounded direction

Retain detail as an arrival research input. Before a career simulator, specify a compact,
regularized arrival/continuation comparison with calibration learned only from earlier mature
forecasts and the stronger probability benchmarks. Separately diagnose training-population and
era shifts. Do not calibrate to these exposed test totals or rescue R by selecting D/C after the fact.
A subsequent probability winner must still improve delivered player value before deployment.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_detail_arrival_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_detail_arrival_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_detail_arrival_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_detail_arrival_v1.py
```

The frozen pre-fit contract must not be overwritten. The input panel is locally reproducible from hashed sources; it is not a new external-data release.
