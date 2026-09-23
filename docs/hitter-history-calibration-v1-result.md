# History continuity and prospect probability calibration: results

2026-09-23. Exposed historical development tests; no production forecasts changed.

## Plain-language decision

The combined change is not a model upgrade. History summaries alone improve next-year
arrival Brier by 1.11% and log loss by 1.17%, in five of six origins, with favorable
paired player-cluster intervals. Keep that diagnostic arm as a follow-up candidate,
not a post-hoc substitute for the primary combined arm. Its 2021 arrival count only
moves from 58 to 61 versus 157 observed: missing-calendar-history summaries do not
resolve the major pandemic-era failure.

Past-only calibration raises the one-year probabilities too much in later cohorts.
The combined method expects about 650 arrivals outside 2021 versus 520 observed,
compared with the original 543. A global historical adjustment does not transfer
reliably across these eras.

For becoming a regular, the combined total moves from 19 to 30 versus 31 observed,
but Brier gets slightly worse and log loss slightly better, both uncertain. It still
underpredicts 2021 (11 versus 17) while overpredicting 2022 (19 versus 14). This is
a concrete example of a close total hiding errors in who succeeds and when.

Three-year arrival improves on average, but only one of the two origins improves
on both scores, and the simpler logistic coverage benchmark remains better. No
regular-workload or delivered-player-value claim is supported.

## What changed in the experiment

Added 25 inputs summarizing actually observed recent seasons, retaining elapsed calendar
time and leaving all original exact-season lags intact. Short current seasons can draw
on older performance; no missing season is invented and low PA is not labeled an injury.
Separately calibrated each model using only older out-of-time forecasts with fully
mature outcomes. The transformation adjusts probability levels, not within-year rankings.
The combined history-plus-calibration model was declared primary before these fits.

Training settings, player-identity weighting, cohorts and outcome definitions remain
fixed. New history is assembled from the existing 2009–2024 snapshot archive; early
history can be left-censored, and levels are retained rather than treated as equivalent.
Calibration uses equal-origin weights, not outcome prevalence from the current test.

## Main results

Expected counts sum probabilities over player-season cases. The same player can appear
in multiple origins. Lower Brier and log loss are better; scores weight origins equally.

### next_year

Decision: **not_confirmed_no_upgrade**. 19,247 never-debuted prospect snapshots; 6 test origins; 677 observed successes.

| Method | Expected successes | Brier | Log loss |
|---|---:|---:|---:|
| Original rich model | 600.6 | 0.023948 | 0.083329 |
| Original + past-only calibration | 716.6 | 0.024243 | 0.084250 |
| + observed-history summaries | 608.6 | 0.023681 | 0.082354 |
| History + past-only calibration (primary) | 717.3 | 0.024005 | 0.083314 |

Primary HC minus original R, paired player-cluster 95% intervals:

- brier: +0.000057 [-0.000277, +0.000382]; 3/6 improving origins.
- log_loss: -0.000015 [-0.000994, +0.000998]; 3/6 improving origins.

Gates: support=True, both_paired_intervals=False, majority_origins=False, calibration=True, stage_guards=True, B2_point_scores=True, ensemble_point_scores=True.

| Origin | Observed | R expected | RC expected | H expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017 | 95 | 92.5 | 106.6 | 91.0 | 103.3 | 1.003 | 1.001 |
| 2018 | 108 | 90.9 | 102.5 | 91.8 | 102.6 | 0.958 | 0.960 |
| 2021 | 157 | 58.1 | 64.7 | 60.8 | 67.5 | 0.943 | 0.943 |
| 2022 | 106 | 112.5 | 147.4 | 120.7 | 157.0 | 1.066 | 1.050 |
| 2023 | 107 | 145.3 | 179.8 | 144.2 | 174.4 | 1.088 | 1.072 |
| 2024 | 104 | 101.3 | 115.6 | 100.1 | 112.5 | 0.988 | 0.998 |

| Prospect group | Cases | Observed | R expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 19247 | 677 | 600.6 | 717.3 | 1.002 | 1.000 |
| young_advancing | 3968 | 297 | 280.3 | 332.4 | 1.005 | 1.012 |
| short_current | 16191 | 217 | 170.4 | 208.6 | 0.992 | 0.986 |
| first_at_level | 9959 | 359 | 304.6 | 360.8 | 0.998 | 0.995 |
| substantial_repeat | 7261 | 163 | 135.7 | 161.8 | 0.994 | 0.993 |
| partial_promotion_return | 1061 | 111 | 121.5 | 146.4 | 1.030 | 1.015 |
| upper | 5043 | 637 | 552.7 | 663.3 | 1.001 | 0.995 |
| lower | 14204 | 40 | 47.9 | 54.0 | 1.010 | 1.030 |

Groups overlap and are descriptive. Do not sum them or select a model per subgroup.

| Matched reference | Cases | HC / reference Brier | HC / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 19247 | 0.024005 / 0.024420 | 0.083314 / 0.085182 |
| logistic_B2 | 19247 | 0.024005 / 0.025795 | 0.083314 / 0.087768 |
| accepted_C2 | 13127 | 0.024484 / 0.028905 | 0.085523 / 0.104671 |
| earlier_ensemble | 13127 | 0.024484 / 0.024927 | 0.085523 / 0.085709 |

Ranking, pooled captures within each origin:

- R: top 5% captures 429/677; top 10% captures 565/677.
- H: top 5% captures 429/677; top 10% captures 563/677.

### arrival_three

Decision: **not_confirmed_no_upgrade**. 6,438 never-debuted prospect snapshots; 2 test origins; 649 observed successes.

| Method | Expected successes | Brier | Log loss |
|---|---:|---:|---:|
| Original rich model | 460.0 | 0.064260 | 0.213320 |
| Original + past-only calibration | 526.4 | 0.062817 | 0.209103 |
| + observed-history summaries | 451.4 | 0.063654 | 0.211852 |
| History + past-only calibration (primary) | 508.9 | 0.062244 | 0.207901 |

Primary HC minus original R, paired player-cluster 95% intervals:

- brier: -0.002015 [-0.003008, -0.001123]; 1/2 improving origins.
- log_loss: -0.005419 [-0.008327, -0.002820]; 1/2 improving origins.

Gates: support=False, both_paired_intervals=True, majority_origins=False, calibration=True, stage_guards=True, B2_point_scores=True, ensemble_point_scores=None.

| Origin | Observed | R expected | RC expected | H expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 352 | 200.5 | 228.6 | 197.9 | 222.1 | 0.939 | 0.947 |
| 2022 | 297 | 259.5 | 297.8 | 253.5 | 286.8 | 1.005 | 1.007 |

| Prospect group | Cases | Observed | R expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 6438 | 649 | 460.0 | 508.9 | 0.969 | 0.975 |
| young_advancing | 1315 | 276 | 236.1 | 269.2 | 0.953 | 0.966 |
| short_current | 5591 | 306 | 194.8 | 204.4 | 0.974 | 0.978 |
| first_at_level | 3848 | 472 | 320.1 | 360.8 | 0.955 | 0.968 |
| substantial_repeat | 2033 | 98 | 68.8 | 68.0 | 1.002 | 0.990 |
| partial_promotion_return | 294 | 58 | 53.7 | 62.1 | 0.995 | 0.969 |
| upper | 1668 | 427 | 281.9 | 313.5 | 0.943 | 0.955 |
| lower | 4770 | 222 | 178.1 | 195.4 | 1.006 | 0.998 |

Groups overlap and are descriptive. Do not sum them or select a model per subgroup.

| Matched reference | Cases | HC / reference Brier | HC / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 6438 | 0.062244 / 0.064982 | 0.207901 / 0.215716 |
| logistic_B2 | 6438 | 0.062244 / 0.060176 | 0.207901 / 0.203176 |
| F1 | 6438 | 0.062244 / 0.082608 | 0.207901 / 0.313373 |
| A1 | 6438 | 0.062244 / 0.080486 | 0.207901 / 0.281470 |

Ranking, pooled captures within each origin:

- R: top 5% captures 219/649; top 10% captures 349/649.
- H: top 5% captures 221/649; top 10% captures 362/649.

### regular_three

Decision: **not_confirmed_no_upgrade**. 6,438 never-debuted prospect snapshots; 2 test origins; 31 observed successes.

| Method | Expected successes | Brier | Log loss |
|---|---:|---:|---:|
| Original rich model | 19.2 | 0.004420 | 0.020267 |
| Original + past-only calibration | 25.9 | 0.004388 | 0.019865 |
| + observed-history summaries | 20.6 | 0.004455 | 0.020503 |
| History + past-only calibration (primary) | 29.9 | 0.004464 | 0.020101 |

Primary HC minus original R, paired player-cluster 95% intervals:

- brier: +0.000045 [-0.000180, +0.000225]; 1/2 improving origins.
- log_loss: -0.000165 [-0.001271, +0.000797]; 1/2 improving origins.

Gates: support=False, both_paired_intervals=False, majority_origins=False, calibration=True, stage_guards=True, B2_point_scores=False, ensemble_point_scores=None.

| Origin | Observed | R expected | RC expected | H expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 17 | 6.7 | 9.3 | 7.1 | 10.8 | 0.994 | 0.964 |
| 2022 | 14 | 12.5 | 16.6 | 13.5 | 19.1 | 1.030 | 1.029 |

| Prospect group | Cases | Observed | R expected | HC expected | HC/R Brier | HC/R log loss |
|---|---:|---:|---:|---:|---:|---:|
| all_prospects | 6438 | 31 | 19.2 | 29.9 | 1.010 | 0.992 |
| young_advancing | 1315 | 26 | 11.4 | 17.6 | 1.008 | 0.963 |
| short_current | 5591 | 10 | 5.6 | 8.6 | 0.998 | 0.981 |
| first_at_level | 3848 | 27 | 13.7 | 21.9 | 1.007 | 0.988 |
| substantial_repeat | 2033 | 0 | 2.5 | 3.7 | 1.882 | 1.476 |
| partial_promotion_return | 294 | 4 | 2.6 | 3.7 | 1.032 | 0.988 |
| upper | 1668 | 23 | 13.7 | 21.6 | 1.018 | 0.977 |
| lower | 4770 | 8 | 5.5 | 8.3 | 0.990 | 1.025 |

Groups overlap and are descriptive. Do not sum them or select a model per subgroup.

| Matched reference | Cases | HC / reference Brier | HC / reference log loss |
|---|---:|---:|---:|
| lightgbm_B2 | 6438 | 0.004464 / 0.004345 | 0.020101 / 0.019275 |
| logistic_B2 | 6438 | 0.004464 / 0.004599 | 0.020101 / 0.019939 |
| F1 | 6438 | 0.004464 / 0.004680 | 0.020101 / 0.027717 |
| A1 | 6438 | 0.004464 / 0.004687 | 0.020101 / 0.025528 |

Ranking, pooled captures within each origin:

- R: top 5% captures 25/31; top 10% captures 29/31.
- H: top 5% captures 22/31; top 10% captures 29/31.

## Calibration support

| Target / origin | Arm | Calibration origins | Positive cases | Intercept | Slope | Fallback |
|---|---|---|---:|---:|---:|---|
| next_year / 2017 | R | 2013, 2014, 2015, 2016 | 392 | 0.265 | 1.033 | False |
| next_year / 2017 | H | 2013, 2014, 2015, 2016 | 392 | 0.226 | 1.024 | False |
| next_year / 2018 | R | 2013, 2014, 2015, 2016, 2017 | 487 | 0.239 | 1.037 | False |
| next_year / 2018 | H | 2013, 2014, 2015, 2016, 2017 | 487 | 0.203 | 1.024 | False |
| next_year / 2021 | R | 2014, 2015, 2016, 2017, 2018 | 500 | 0.332 | 1.082 | False |
| next_year / 2021 | H | 2014, 2015, 2016, 2017, 2018 | 500 | 0.304 | 1.072 | False |
| next_year / 2022 | R | 2015, 2016, 2017, 2018, 2021 | 558 | 0.564 | 1.074 | False |
| next_year / 2022 | H | 2015, 2016, 2017, 2018, 2021 | 558 | 0.535 | 1.067 | False |
| next_year / 2023 | R | 2016, 2017, 2018, 2021, 2022 | 572 | 0.382 | 1.014 | False |
| next_year / 2023 | H | 2016, 2017, 2018, 2021, 2022 | 572 | 0.332 | 1.005 | False |
| next_year / 2024 | R | 2017, 2018, 2021, 2022, 2023 | 573 | 0.152 | 0.976 | False |
| next_year / 2024 | H | 2017, 2018, 2021, 2022, 2023 | 573 | 0.120 | 0.971 | False |
| arrival_three / 2021 | R | 2013, 2014, 2015, 2016 | 1129 | 0.416 | 1.125 | False |
| arrival_three / 2021 | H | 2013, 2014, 2015, 2016 | 1129 | 0.384 | 1.120 | False |
| arrival_three / 2022 | R | 2013, 2014, 2015, 2016 | 1129 | 0.416 | 1.125 | False |
| arrival_three / 2022 | H | 2013, 2014, 2015, 2016 | 1129 | 0.384 | 1.120 | False |
| arrival_three / 2019 | R | 2013, 2014, 2015, 2016 | 1129 | 0.416 | 1.125 | False |
| arrival_three / 2019 | H | 2013, 2014, 2015, 2016 | 1129 | 0.384 | 1.120 | False |
| regular_three / 2021 | R | 2013, 2014, 2015, 2016 | 47 | 0.221 | 0.972 | False |
| regular_three / 2021 | H | 2013, 2014, 2015, 2016 | 47 | 0.255 | 0.955 | False |
| regular_three / 2022 | R | 2013, 2014, 2015, 2016 | 47 | 0.221 | 0.972 | False |
| regular_three / 2022 | H | 2013, 2014, 2015, 2016 | 47 | 0.255 | 0.955 | False |
| regular_three / 2019 | R | 2013, 2014, 2015, 2016 | 47 | 0.221 | 0.972 | False |
| regular_three / 2019 | H | 2013, 2014, 2015, 2016 | 47 | 0.255 | 0.955 | False |

## Limits and decision boundaries

- Only 2021/2022 ordinary three-year windows are scored; they overlap and contain just 31 regular cases. These cannot pass the >=3-origin confirmation gate.
- Regular means 450+ MLB PA in at least two of three years. It is not WAR, batting talent, an All-Star label or whole-career value.
- The 2021/2022 three-year calibrators only see pre-pandemic outcomes. This test cannot learn an unprecedented era change from future information.
- The 2019 pandemic-crossing results are separate in score-report.json; they are excluded from calibration and the main scores.
- Auxiliary raw forecasts from 2013 onward supply calibration, not extra detailed modern test seasons. Early raw-contact/pitch/context coverage is limited as in the preceding experiment.
- Player-cluster intervals do not capture every common season shock; the historical tests and diagnostic groups are already exposed development evidence.
- No automatic adoption, count-matching inflation, player-specific boosts, target redefinition or after-the-fact tuning. Any probability improvement still needs delivered-value validation.

A metadata-only runtime repair converted a NumPy boolean for JSON serialization.
The original prefit manifest is intact. runtime-repair.json records old/new hashes;
the original calibration module is reconstructed and hash-checked, then all calibrated
predictions are compared to it within 1e-12. Parquet byte identity across rewrites is
not assumed. Numerical recipes and acceptance gates were not changed.

Raw arm/fold records: 48; newly fitted: 36, plus one mutation refit.
Future-label/predictor mutation maximum probability difference: 0.0.

## Reproduce

```powershell
.venv/Scripts/python.exe -X utf8 scripts/fit_hitter_history_calibration_v1.py
.venv/Scripts/python.exe -X utf8 scripts/score_hitter_history_calibration_v1.py
.venv/Scripts/python.exe -X utf8 scripts/report_hitter_history_calibration_v1.py
.venv/Scripts/python.exe -X utf8 scripts/verify_hitter_history_calibration_v1.py
```

The existing prefit manifest must not be overwritten; use --freeze only on a fresh reproduction.
