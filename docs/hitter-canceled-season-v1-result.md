# Canceled-season input routing: result

2026-09-23. Exposed historical development experiment; live models remain unchanged.

## What the repair does

A year with no minor-league season is not the same as a player individually missing
a year. The original inputs encoded both as missing annual history. History summaries
added in the last experiment did not remove that misleading block.

O fits a forecast using the same eligible training players and settings, but leaves
out the exogenously unavailable annual block in both training and prediction. For
2021, it uses current evidence and correctly dated 2019 evidence; for 2022 it uses
current evidence and 2021 evidence. It never relabels 2019 as 2020, invents a stat line,
scales PA, or learns a probability boost from the observed test totals. Valid cumulative
career/level-path information remains available. Only never-debuted minor leaguers
with no record in the canceled slot are routed to O. Other forecasts equal R exactly.

N removes both prior annual blocks as a diagnostic, not a candidate selected after scoring.
R is the original full-detail model. O was the primary repair specified before fitting.

Official background and plan: [canceled-season experiment](hitter-canceled-season-v1-plan.md).
The cancellation, shorter 2021 schedules and affiliate reorganization were known at
the cutoff. This experiment isolates an input-meaning mismatch, not every era effect.

## Outcome comparisons

Counts are sums of probabilities over player-season cases, not a hard classification.
A 2021 origin predicts 2022 arrivals or outcomes in 2022–2024. Lower proper scores are better.

### next_year

Status: **partial_or_unsupported_repair_no_promotion**.

| Origin | Cases | Observed | Original R expected | Outage O expected | No-prior N expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 3250 | 157 | 58.1 | 93.5 | 82.0 | 0.869 | 0.847 |
| 2022 | 3188 | 106 | 112.5 | 176.2 | 174.4 | 1.159 | 1.115 |

2021 absolute count-error reduction: 35.8%.

Gates: 2021_both_intervals=True, 2021_count_error_reduction_25pct=True, 2022_and_stage_guard=False, historical_recovery=True, three_year_confirmation=True.

| Origin / score | O minus R | Paired player-cluster 95% interval |
|---|---:|---|
| 2021 / brier | -0.004625 | [-0.005921, -0.003418] |
| 2021 / log_loss | -0.018339 | [-0.022936, -0.013822] |
| 2022 / brier | +0.003573 | [+0.002155, +0.005008] |
| 2022 / log_loss | +0.009535 | [+0.005522, +0.013441] |

| 2021 group | Cases | Observed | R expected | O expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 157 | 58.1 | 93.5 | 0.869 | 0.847 |
| young_advancing | 609 | 75 | 27.0 | 40.5 | 0.835 | 0.831 |
| short_current | 2911 | 64 | 24.5 | 42.7 | 0.894 | 0.856 |
| first_at_level | 2300 | 120 | 45.3 | 71.4 | 0.854 | 0.842 |
| substantial_repeat | 775 | 19 | 6.2 | 10.6 | 0.962 | 0.886 |
| partial_promotion_return | 74 | 8 | 3.5 | 6.4 | 0.888 | 0.864 |
| upper | 847 | 142 | 51.4 | 85.6 | 0.852 | 0.827 |
| lower | 2403 | 15 | 6.6 | 7.9 | 0.987 | 0.951 |

Groups overlap; they are descriptive, not model-selection opportunities. 2022 groups are in score-report.json.

| Matched full-window reference | Cases | O / reference Brier | O / reference log loss |
|---|---:|---:|---:|
| history_H | 19247 | 0.023772 / 0.023681 | 0.081862 / 0.082354 |
| lightgbm_B2 | 19247 | 0.023772 / 0.024420 | 0.081862 / 0.085182 |
| logistic_B2 | 19247 | 0.023772 / 0.025795 | 0.081862 / 0.087768 |
| accepted_C2 | 13127 | 0.024559 / 0.028905 | 0.084701 / 0.104671 |
| earlier_ensemble | 13127 | 0.024559 / 0.024927 | 0.084701 / 0.085709 |

2021 top-5% capture of observed successes:

- R: 91/157.
- O: 91/157.
- N: 92/157.

### arrival_three

Status: **partial_or_unsupported_repair_no_promotion**.

| Origin | Cases | Observed | Original R expected | Outage O expected | No-prior N expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 3250 | 352 | 200.5 | 221.8 | 221.1 | 0.941 | 0.943 |
| 2022 | 3188 | 297 | 259.5 | 259.7 | 269.1 | 1.003 | 0.999 |

2021 absolute count-error reduction: 14.1%.

Gates: 2021_both_intervals=True, 2021_count_error_reduction_25pct=False, 2022_and_stage_guard=True, historical_recovery=True, three_year_confirmation=False.

| Origin / score | O minus R | Paired player-cluster 95% interval |
|---|---:|---|
| 2021 / brier | -0.004187 | [-0.005163, -0.003256] |
| 2021 / log_loss | -0.013376 | [-0.016309, -0.010460] |
| 2022 / brier | +0.000148 | [-0.000363, +0.000655] |
| 2022 / log_loss | -0.000144 | [-0.001786, +0.001408] |

| 2021 group | Cases | Observed | R expected | O expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 352 | 200.5 | 221.8 | 0.941 | 0.943 |
| young_advancing | 609 | 138 | 97.1 | 103.1 | 0.937 | 0.947 |
| short_current | 2911 | 194 | 105.1 | 114.6 | 0.964 | 0.958 |
| first_at_level | 2300 | 294 | 167.1 | 183.4 | 0.942 | 0.947 |
| substantial_repeat | 775 | 31 | 18.8 | 20.5 | 0.953 | 0.942 |
| partial_promotion_return | 74 | 15 | 7.2 | 9.3 | 0.921 | 0.897 |
| upper | 847 | 225 | 114.0 | 136.8 | 0.903 | 0.901 |
| lower | 2403 | 127 | 86.5 | 85.0 | 0.994 | 0.992 |

Groups overlap; they are descriptive, not model-selection opportunities. 2022 groups are in score-report.json.

| Matched full-window reference | Cases | O / reference Brier | O / reference log loss |
|---|---:|---:|---:|
| history_H | 6438 | 0.062240 / 0.063654 | 0.206560 / 0.211852 |
| lightgbm_B2 | 6438 | 0.062240 / 0.064982 | 0.206560 / 0.215716 |
| logistic_B2 | 6438 | 0.062240 / 0.060176 | 0.206560 / 0.203176 |
| F1 | 6438 | 0.062240 / 0.082608 | 0.206560 / 0.313373 |
| A1 | 6438 | 0.062240 / 0.080486 | 0.206560 / 0.281470 |

2021 top-5% capture of observed successes:

- R: 114/352.
- O: 121/352.
- N: 120/352.

### regular_three

Status: **partial_or_unsupported_repair_no_promotion**.

| Origin | Cases | Observed | Original R expected | Outage O expected | No-prior N expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 3250 | 17 | 6.7 | 7.8 | 7.4 | 0.991 | 0.975 |
| 2022 | 3188 | 14 | 12.5 | 10.2 | 11.9 | 1.002 | 1.012 |

2021 absolute count-error reduction: 10.7%.

Gates: 2021_both_intervals=False, 2021_count_error_reduction_25pct=False, 2022_and_stage_guard=True, historical_recovery=True, three_year_confirmation=False.

| Origin / score | O minus R | Paired player-cluster 95% interval |
|---|---:|---|
| 2021 / brier | -0.000044 | [-0.000139, +0.000032] |
| 2021 / log_loss | -0.000578 | [-0.001373, +0.000157] |
| 2022 / brier | +0.000007 | [-0.000135, +0.000175] |
| 2022 / log_loss | +0.000203 | [-0.000400, +0.000876] |

| 2021 group | Cases | Observed | R expected | O expected | O/R Brier | O/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 17 | 6.7 | 7.8 | 0.991 | 0.975 |
| young_advancing | 609 | 15 | 3.6 | 4.2 | 0.987 | 0.964 |
| short_current | 2911 | 6 | 3.1 | 3.5 | 0.998 | 0.962 |
| first_at_level | 2300 | 17 | 5.7 | 6.6 | 0.991 | 0.973 |
| substantial_repeat | 775 | 0 | 0.6 | 0.7 | 1.177 | 1.083 |
| partial_promotion_return | 74 | 0 | 0.2 | 0.2 | 1.592 | 1.258 |
| upper | 847 | 12 | 4.0 | 5.0 | 0.984 | 0.959 |
| lower | 2403 | 5 | 2.7 | 2.8 | 1.006 | 1.012 |

Groups overlap; they are descriptive, not model-selection opportunities. 2022 groups are in score-report.json.

| Matched full-window reference | Cases | O / reference Brier | O / reference log loss |
|---|---:|---:|---:|
| history_H | 6438 | 0.004401 / 0.004455 | 0.020079 / 0.020503 |
| lightgbm_B2 | 6438 | 0.004401 / 0.004345 | 0.020079 / 0.019275 |
| logistic_B2 | 6438 | 0.004401 / 0.004599 | 0.020079 / 0.019939 |
| F1 | 6438 | 0.004401 / 0.004680 | 0.020079 / 0.027717 |
| A1 | 6438 | 0.004401 / 0.004687 | 0.020079 / 0.025528 |

2021 top-5% capture of observed successes:

- R: 13/17.
- O: 12/17.
- N: 14/17.

## Historical annual-input outage stress

Hide only the annual stat/PBP block in query prospects, preserving cumulative career
information in every arm. This tests source unavailability, not lost physical development.
The intact original forecast is replayed exactly before inputs are hidden.

| Origin / hidden lag | Observed | Intact R expected | Masked R expected | Available O expected | O/masked Brier | O/masked log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2017 / 1 | 95 | 92.5 | 55.6 | 90.4 | 0.923 | 0.905 |
| 2017 / 2 | 95 | 92.5 | 85.6 | 92.3 | 0.986 | 0.984 |
| 2018 / 1 | 108 | 90.9 | 65.3 | 93.7 | 0.908 | 0.913 |
| 2018 / 2 | 108 | 90.9 | 71.8 | 87.2 | 0.958 | 0.970 |

Both scores improve over masked R in 4/4 scenarios. This is not a claim that discarding available history improves forecasts.

## Limits and verification

- These are targeted development results after inspecting the 2021 error. They are not a newly protected test or a universal arrival-model replacement.
- Regular means at least 450 MLB PA in two of three years, not an All-Star, high-quality hitter, whole-career success or WAR.
- Three-year tests have only two overlapping normal origins. Their confirmation gate remains failed regardless of favorable 2021 changes.
- Non-outage years and other cohorts are unchanged by routing; equality is not independent confirmation of a general improvement.
- Model variants share the fixed dated source panel and inherit its auxiliary-feature and retrospective reconstruction limits.
- Population contraction, shorter schedules, development delays and unusually high subsequent opportunity are possible remaining causes; none is estimated by matching test totals here.
- No 2026 outcomes opened. No live forecast, explorer or delivered player value changed.

Fits: 12 targeted + 6 stress + 1 future-mutation refit.
Original replay maximum difference: 0.0; future mutation: 0.0.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_canceled_season_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_canceled_season_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_canceled_season_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_canceled_season_v1.py
```

Use --freeze only in a fresh reproduction; do not overwrite the saved prefit manifest.
