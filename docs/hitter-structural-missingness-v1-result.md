# Structural missingness: source outage versus individual absence

2026-09-23. Sequential exposed development experiment; no live forecasts changed.

## Why a second test was needed

The [first targeted experiment](hitter-canceled-season-v1-result.md) removed canceled-year
inputs rather than labeling them as ordinary missing history. It improved 2021 next-year
arrival Brier/log loss by 13.1%/15.3% and raised expected arrivals from 58 to 93 versus
157 observed, but applying the same rule to 2022 raised arrivals to 176 versus 106.
Its historical missing-input stress improved in all four cases. That supported the
mechanism, but the proposed two-year routing failed its acceptance rule.

This follow-up was specified only after that result; it is not untouched confirmation.
It tests one source-outage augmentation, with no weight, model-setting or calibration search.

## What was tested

- R: original rich model.
- T: duplicate-only control with two dated source-outage flags.
- A: same training copies/weights, with older annual inputs deliberately hidden and flagged as source outages.

For each eligible prospect snapshot, the original receives half its weight and each of
two masked copies one quarter. Total weight per original snapshot, identity and outcome
class is unchanged. Other players keep a single row. The duplicate control uses the same
copies and weights with inputs intact, isolating effects of duplication on tree fitting.
Actual queries are never artificially masked. No future outcomes, fake batting lines,
probability multipliers or player-specific corrections are used. Cumulative career
summaries remain in all copies: this tests lost annual inputs, not lost development.

## Scores

Counts sum probabilities over player-season cases. Lower Brier/log loss are better.
Year refers to the forecast origin: 2021 next-year outcomes occur in 2022.

### next_year

Status: **not_confirmed_no_upgrade**.

| Model | Observed | Expected | Equal-origin Brier | Equal-origin log loss |
|---|---:|---:|---:|---:|
| R | 677 | 600.6 | 0.023948 | 0.083329 |
| T | 677 | 597.2 | 0.023999 | 0.083281 |
| A | 677 | 676.4 | 0.023730 | 0.081901 |

| Origin | Observed | R expected | T expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2017 | 95 | 92.5 | 93.9 | 94.9 | 0.997 | 0.995 |
| 2018 | 108 | 90.9 | 90.4 | 96.2 | 0.991 | 0.995 |
| 2021 | 157 | 58.1 | 57.2 | 83.9 | 0.890 | 0.872 |
| 2022 | 106 | 112.5 | 110.9 | 159.7 | 1.102 | 1.075 |
| 2023 | 107 | 145.3 | 143.8 | 140.3 | 1.012 | 1.004 |
| 2024 | 104 | 101.3 | 101.0 | 101.5 | 1.013 | 1.013 |

2021 count-error reduction: 26.1%.

Gates: 2021_intervals=True, 2021_count_error_reduction_25pct=True, pooled_R_T_intervals=False, other_origins_stage_guards=False, stronger_ensemble_points=True, sufficient_origins=True.

| Comparison / score | Difference | Player-cluster 95% interval |
|---|---:|---|
| 2021 A–R / brier | -0.003900 | [-0.004914, -0.002946] |
| 2021 A–R / log_loss | -0.015327 | [-0.018938, -0.011928] |
| pooled A–R / brier | -0.000218 | [-0.000516, +0.000088] |
| pooled A–R / log_loss | -0.001428 | [-0.002376, -0.000523] |
| pooled A–T / brier | -0.000269 | [-0.000575, +0.000040] |
| pooled A–T / log_loss | -0.001379 | [-0.002276, -0.000479] |

| 2021 group | Cases | Observed | R expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 157 | 58.1 | 83.9 | 0.890 | 0.872 |
| young_advancing | 609 | 75 | 27.0 | 38.3 | 0.862 | 0.859 |
| short_current | 2911 | 64 | 24.5 | 36.9 | 0.913 | 0.886 |
| first_at_level | 2300 | 120 | 45.3 | 65.1 | 0.878 | 0.868 |
| substantial_repeat | 775 | 19 | 6.2 | 9.1 | 0.957 | 0.898 |
| partial_promotion_return | 74 | 8 | 3.5 | 5.2 | 0.915 | 0.898 |
| upper | 847 | 142 | 51.4 | 76.4 | 0.875 | 0.854 |
| lower | 2403 | 15 | 6.6 | 7.6 | 0.990 | 0.965 |

| Matched reference | Cases | A / reference Brier | A / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 19247 | 0.023730 / 0.024420 | 0.081901 / 0.085182 |
| logistic_B2 | 19247 | 0.023730 / 0.025795 | 0.081901 / 0.087768 |
| accepted_C2 | 13127 | 0.024357 / 0.028905 | 0.084452 / 0.104671 |
| earlier_ensemble | 13127 | 0.024357 / 0.024927 | 0.084452 / 0.085709 |

### arrival_three

Status: **not_confirmed_no_upgrade**.

| Model | Observed | Expected | Equal-origin Brier | Equal-origin log loss |
|---|---:|---:|---:|---:|
| R | 649 | 460.0 | 0.064260 | 0.213320 |
| T | 649 | 461.6 | 0.064107 | 0.213162 |
| A | 649 | 477.4 | 0.063051 | 0.209777 |

| Origin | Observed | R expected | T expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 352 | 200.5 | 202.3 | 213.2 | 0.965 | 0.968 |
| 2022 | 297 | 259.5 | 259.3 | 264.1 | 1.001 | 1.002 |

2021 count-error reduction: 8.4%.

Gates: 2021_intervals=True, 2021_count_error_reduction_25pct=False, pooled_R_T_intervals=True, other_origins_stage_guards=True, stronger_ensemble_points=None, sufficient_origins=False.

| Comparison / score | Difference | Player-cluster 95% interval |
|---|---:|---|
| 2021 A–R / brier | -0.002500 | [-0.003200, -0.001839] |
| 2021 A–R / log_loss | -0.007397 | [-0.009455, -0.005229] |
| pooled A–R / brier | -0.001208 | [-0.001658, -0.000755] |
| pooled A–R / log_loss | -0.003543 | [-0.005031, -0.002029] |
| pooled A–T / brier | -0.001056 | [-0.001488, -0.000609] |
| pooled A–T / log_loss | -0.003385 | [-0.004768, -0.001951] |

| 2021 group | Cases | Observed | R expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 352 | 200.5 | 213.2 | 0.965 | 0.968 |
| young_advancing | 609 | 138 | 97.1 | 101.0 | 0.959 | 0.971 |
| short_current | 2911 | 194 | 105.1 | 111.5 | 0.980 | 0.980 |
| first_at_level | 2300 | 294 | 167.1 | 176.5 | 0.968 | 0.974 |
| substantial_repeat | 775 | 31 | 18.8 | 20.3 | 0.946 | 0.935 |
| partial_promotion_return | 74 | 15 | 7.2 | 8.4 | 0.971 | 0.969 |
| upper | 847 | 225 | 114.0 | 127.9 | 0.941 | 0.940 |
| lower | 2403 | 127 | 86.5 | 85.3 | 0.997 | 1.002 |

| Matched reference | Cases | A / reference Brier | A / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 6438 | 0.063051 / 0.064982 | 0.209777 / 0.215716 |
| logistic_B2 | 6438 | 0.063051 / 0.060176 | 0.209777 / 0.203176 |
| F1 | 6438 | 0.063051 / 0.082608 | 0.209777 / 0.313373 |
| A1 | 6438 | 0.063051 / 0.080486 | 0.209777 / 0.281470 |

### regular_three

Status: **not_confirmed_no_upgrade**.

| Model | Observed | Expected | Equal-origin Brier | Equal-origin log loss |
|---|---:|---:|---:|---:|
| R | 31 | 19.2 | 0.004420 | 0.020267 |
| T | 31 | 17.6 | 0.004416 | 0.020409 |
| A | 31 | 18.7 | 0.004379 | 0.019676 |

| Origin | Observed | R expected | T expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 17 | 6.7 | 6.6 | 7.4 | 0.996 | 0.972 |
| 2022 | 14 | 12.5 | 11.0 | 11.2 | 0.984 | 0.969 |

2021 count-error reduction: 7.5%.

Gates: 2021_intervals=False, 2021_count_error_reduction_25pct=False, pooled_R_T_intervals=False, other_origins_stage_guards=True, stronger_ensemble_points=None, sufficient_origins=False.

| Comparison / score | Difference | Player-cluster 95% interval |
|---|---:|---|
| 2021 A–R / brier | -0.000017 | [-0.000067, +0.000027] |
| 2021 A–R / log_loss | -0.000651 | [-0.001414, +0.000024] |
| pooled A–R / brier | -0.000041 | [-0.000108, +0.000026] |
| pooled A–R / log_loss | -0.000591 | [-0.001071, -0.000154] |
| pooled A–T / brier | -0.000037 | [-0.000103, +0.000026] |
| pooled A–T / log_loss | -0.000734 | [-0.001303, -0.000212] |

| 2021 group | Cases | Observed | R expected | A expected | A/R Brier | A/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 3250 | 17 | 6.7 | 7.4 | 0.996 | 0.972 |
| young_advancing | 609 | 15 | 3.6 | 4.1 | 0.995 | 0.971 |
| short_current | 2911 | 6 | 3.1 | 3.2 | 0.998 | 0.976 |
| first_at_level | 2300 | 17 | 5.7 | 6.4 | 0.996 | 0.971 |
| substantial_repeat | 775 | 0 | 0.6 | 0.6 | 0.906 | 0.998 |
| partial_promotion_return | 74 | 0 | 0.2 | 0.2 | 1.196 | 1.136 |
| upper | 847 | 12 | 4.0 | 4.7 | 0.994 | 0.961 |
| lower | 2403 | 5 | 2.7 | 2.7 | 1.002 | 0.997 |

| Matched reference | Cases | A / reference Brier | A / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 6438 | 0.004379 / 0.004345 | 0.019676 / 0.019275 |
| logistic_B2 | 6438 | 0.004379 / 0.004599 | 0.019676 / 0.019939 |
| F1 | 6438 | 0.004379 / 0.004680 | 0.019676 / 0.027717 |
| A1 | 6438 | 0.004379 / 0.004687 | 0.019676 / 0.025528 |

## Limits

- Diagnosis and both fixes used exposed historical development results. Conditional player-cluster intervals do not capture all shared season shocks.
- The cancellation flag marks known source unavailability, not injury or the amount of actual baseball development lost. Short schedules, selection after reorganization and changing opportunity may still matter.
- The existing 2021 training records/outcomes are retained when mature. No year is discarded merely for being hard to predict.
- Only two ordinary, overlapping three-year origins exist. Any long-horizon gain remains exploratory, and regular workload is not WAR or an All-Star target.
- No blend or third tuning round is selected after these results. Passing a probability gate would still require delivered-player-value testing before deployment.
- No live forecasts, explorer or frozen 2026 artifacts changed.

Completed 20 fits plus a future-mutation refit; maximum mutation difference 0.0.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_structural_missingness_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_structural_missingness_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_structural_missingness_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_structural_missingness_v1.py
```

Use --freeze only for a fresh reproduction. Keep the existing prefit contract intact.
