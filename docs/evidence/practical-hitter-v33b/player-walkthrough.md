# Corrected practical hitter comparison and player review

Retain corrected pooled evidence plus draft-context PA, combined with a safely scaled, PA-weighted linear batting head, as the working research baseline. It improves workload meaningfully and contribution against the corrected same-fold tree control. It is not a certified full hitter model: stronger old-reference contribution gains remain uncertain, public PA MAE misses the declared target, and cohort/entry/availability gaps remain.

Targets: next-calendar-year MLB PA and batting-plus-replacement wins. Not full WAR, pure current minor-league talent, six club-control years or trade value. All 30,506 identities/non-arrivals retained; no 2026 outcomes or frozen forecast changes.

## What changed and what was repaired

Three-year actual event counts are pooled at 1/.8/.6 by source league before one fixed prior. Existing cutoff-known draft picks/attached school classes provide entry context; unavailable pedigree stays unknown. A linear diagnostic uses fixed physical scales rather than rare-league training standard deviations. Temporary-absence, foreign production, park/opponent and job-context gaps remain.

The earlier broad expansion wrongly admitted 597 incomplete origin-2020 training identities. Their absent roster capture became listing zero. Those rows are now explicitly excluded from every training set, not deleted from source history or testing. All later candidate fits AND a matched direct control were refitted. Original V31/V32 and interrupted V33 artifacts remain qualified/preserved. Earlier results cannot be called adopted gains.

## Scores on identical populations

| Scope / model | PA RMSE | PA MAE | Batting + replacement RMSE | Value MAE |
|---|---:|---:|---:|---:|
| all / pooled | 61.76 | 21.31 | 0.44862 | 0.13207 |
| all / pedigree | 61.62 | 21.33 | 0.44795 | 0.13267 |
| all / pooled_product | 61.76 | 21.31 | 0.44602 | 0.12708 |
| all / pedigree_product | 61.62 | 21.33 | 0.44555 | 0.12713 |
| all / safe_ridge | 61.62 | 21.33 | 0.44121 | 0.12725 |
| all / repaired_direct | 61.92 | 21.24 | 0.45170 | 0.13356 |
| v24_matched / pooled | 124.79 | 82.44 | 0.92555 | 0.53440 |
| v24_matched / pedigree | 124.65 | 82.54 | 0.92461 | 0.53511 |
| v24_matched / pooled_product | 124.79 | 82.44 | 0.91616 | 0.51817 |
| v24_matched / pedigree_product | 124.65 | 82.54 | 0.91499 | 0.51765 |
| v24_matched / safe_ridge | 124.65 | 82.54 | 0.90951 | 0.51936 |
| v24_matched / v24 | 128.62 | 86.74 | 0.91725 | 0.52121 |
| legacy_n_matched / pooled | 61.33 | 20.87 | 0.45216 | 0.13218 |
| legacy_n_matched / pedigree | 61.22 | 20.89 | 0.45209 | 0.13299 |
| legacy_n_matched / pooled_product | 61.33 | 20.87 | 0.44898 | 0.12793 |
| legacy_n_matched / pedigree_product | 61.22 | 20.89 | 0.44844 | 0.12807 |
| legacy_n_matched / safe_ridge | 61.22 | 20.89 | 0.44458 | 0.12844 |
| legacy_n_matched / legacy_n | 62.33 | 21.33 | 0.44582 | 0.12826 |
| public_active / pooled | 144.27 | 110.78 | 1.04127 | 0.70454 |
| public_active / pedigree | 143.96 | 110.56 | 1.03814 | 0.70335 |
| public_active / pooled_product | 144.27 | 110.78 | 1.02698 | 0.68452 |
| public_active / pedigree_product | 143.96 | 110.56 | 1.02550 | 0.68312 |
| public_active / safe_ridge | 143.96 | 110.56 | 1.01787 | 0.68331 |
| public_active / v24 | 149.12 | 116.01 | 1.02262 | 0.68342 |
| public_active / steamer | 135.02 | 92.40 | 1.04348 | 0.68482 |
| public_legacy_n / pooled | 137.80 | 103.86 | 1.00850 | 0.66534 |
| public_legacy_n / pedigree | 137.80 | 103.94 | 1.00991 | 0.66702 |
| public_legacy_n / pooled_product | 137.80 | 103.86 | 0.98505 | 0.64753 |
| public_legacy_n / pedigree_product | 137.80 | 103.94 | 0.98240 | 0.64603 |
| public_legacy_n / safe_ridge | 137.80 | 103.94 | 0.97833 | 0.65261 |
| public_legacy_n / legacy_n | 139.53 | 109.20 | 0.97138 | 0.65680 |
| public_legacy_n / steamer | 133.30 | 89.01 | 1.00596 | 0.65785 |

On the unchanged 4,396-row V24 comparison, PA RMSE improves 128.62 to 124.65, with a player-cluster interval favoring the new workload model. Contribution RMSE improves 0.91725 to 0.90951 but its interval includes no improvement. On 1,789 public-matched forecasts, PA RMSE is 143.96 versus Steamer 135.02 (6.6% higher); MAE is 110.56 versus 92.40 (19.7% higher), failing the predeclared 15% MAE tolerance. Converted contribution RMSE is 1.01787 versus V24 1.02262, an uncertain difference. The linear assembly beats the corrected same-fold direct control on all 30,506 rows (0.44121 versus 0.45170, nominal cluster interval excluding zero), but its 0.44458 versus older N 0.44582 advantage is uncertain. Draft-only gains over pooled evidence also remain uncertain. Development comparisons are not untouched confirmatory tests.

Public forecasts have different preseason/December knowledge dates; their raw-count conversion uses origin environment versus realized target environment. Converted value has a substantial mean offset. Do not infer superior pure batting-talent accuracy from that loss. Older N has different fitting provenance; it remains a demanding reference, not an isolated causal comparison.

## All-origin totals and reasonability

| Origin | Actual PA | Pooled PA gap | Draft PA gap | Control PA gap | Actual value | Linear assembly value gap |
|---|---:|---:|---:|---:|---:|---:|
| origin_2016 | 179968 | -5029 | -4451 | -3804 | 636.62 | -24.42 |
| origin_2017 | 179643 | -3654 | -2657 | -3086 | 631.96 | -2.96 |
| origin_2018 | 181308 | -5408 | -4505 | -5269 | 635.03 | -11.14 |
| origin_2021 | 181583 | -15196 | -14663 | -14652 | 567.85 | 28.18 |
| origin_2022 | 182917 | -6964 | -6349 | -6614 | 565.39 | 13.52 |
| origin_2023 | 182194 | 415 | 728 | -1314 | 569.58 | 23.62 |
| origin_2024 | 182880 | -4100 | -3118 | -7213 | 570.18 | -13.43 |

The 2021-origin draft model is short 14,663 PA, and the corrected control is similarly short: removing bad training rows and pooling counts do not fix the pandemic-era opportunity regime. Across origins the upper-minor cohort is short 10,306 PA, while lower minors receive 4,768 excess PA against 6,072 actual. Their tiny overall error is dominated by non-arrivals and must not be sold as good prospect discrimination. The linear assembly nearly matches McLain's delivered value while missing his workload badly; cancellation is not success. Judge, Kurtz, McNeil and Tatis expose distinct unresolved talent, fast-entry and temporary-absence gaps. Fixed-scale linear coefficients can still have baseball-unhelpful partial signs among correlated inputs. Pre-DH hitter totals need not equal 570 because omitted pitcher batting can be negative. No outcome-total normalization has been applied.

## Player walkthroughs

Fixed diagnostic identities plus each arm’s largest gain/harm against the corrected direct control, false high/low, ordinary partial-workload example and the largest linear rate. Origin-only nearest peers also include draft-knownness/rank/college background. Selected outcomes diagnose mechanics, not independent validation.

### Matt Olson — 2017 → 2018

Selection: fixed diagnostic.

Inputs: age 23, MLB PA 216/28/0, current observed quality 0.7046, pooled MLB quality 0.6428; captured listing 1 (not certified rights). Draft known 1, year 2012, pick 47, class unknown, rank 0.4935, rank × low-exposure 0.0272.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2015 | AA | 585 | 17 | 139 | 99 |
| 2016 | AAA | 540 | 17 | 132 | 69 |
| 2016 | MLB | 28 | 0 | 4 | 7 |
| 2017 | AAA | 343 | 23 | 83 | 45 |
| 2017 | MLB | 216 | 24 | 60 | 21 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 326.66 | 1.8140 | — |
| pooled | 313.37 | 2.2962 | 0.6003 |
| pedigree | 315.55 | 2.5452 | 0.7503 |
| pooled_product | 313.37 | 1.2775 | — |
| pedigree_product | 315.55 | 1.3653 | — |
| safe_ridge | 315.55 | 1.6057 | 1.2075 |

Actual: 660 PA / 3.4816 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 301.4671999969106, "value": 1.6353931660196022, "rate": 0.5241724124032249}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The 24 MLB HR in 216 PA and 23 AAA HR in 343 PA are present. The draft model's 316 PA/2.55 contribution and linear assembly's 316/1.61 still miss 660/3.48. Clearing draft inputs reduces PA to 301: a modest entry-context effect, not recognition of a full-time job. Winker, Nick Williams and Fisher have mixed workloads; this remains an opportunity miss, and linear shrinkage also lowers the batting estimate.

Peers selected without future outcomes: Jesse Winker (age 23, current MLB 137 PA, draft pick 49; actual next 334 PA / 2.40); Nick Williams (age 23, current MLB 343 PA, draft pick 93; actual next 448 PA / 1.80); Derek Fisher (age 23, current MLB 166 PA, draft pick 37; actual next 86 PA / -0.17).

Training profile support: all=201 distinct people; active=172 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 63.20 | 238.40 | 0.2300 | 0.254728 |
| MLB / BB | 26.60 | 238.40 | 0.0800 | 0.102246 |
| MLB / HBP | 5.00 | 238.40 | 0.0100 | 0.017730 |
| MLB / HR | 24.00 | 238.40 | 0.0300 | 0.079787 |
| MLB / BABIP | 26.60 | 118.60 | 0.3000 | 0.258920 |
| MLB / 2B | 2.80 | 238.40 | 0.0500 | 0.023050 |
| MLB / 3B | 0.00 | 238.40 | 0.0050 | 0.001478 |
| AAA / K | 188.60 | 775.00 | 0.2300 | 0.241829 |
| AAA / BB | 100.20 | 775.00 | 0.0800 | 0.123657 |
| AAA / HBP | 1.00 | 775.00 | 0.0100 | 0.002286 |
| AAA / HR | 36.60 | 775.00 | 0.0300 | 0.045257 |
| AAA / BABIP | 130.60 | 445.40 | 0.3000 | 0.294463 |
| AAA / 2B | 43.20 | 775.00 | 0.0500 | 0.055086 |
| AAA / 3B | 1.80 | 775.00 | 0.0050 | 0.002629 |
| AA / K | 83.40 | 351.00 | 0.2300 | 0.235920 |
| AA / BB | 59.40 | 351.00 | 0.0800 | 0.149446 |
| AA / HBP | 3.60 | 351.00 | 0.0100 | 0.010200 |
| AA / HR | 10.20 | 351.00 | 0.0300 | 0.029268 |
| AA / BABIP | 59.40 | 190.80 | 0.3000 | 0.307428 |
| AA / 2B | 22.20 | 351.00 | 0.0500 | 0.060310 |
| AA / 3B | 0.00 | 351.00 | 0.0050 | 0.001109 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.64280 | 0.64280 | 0.66755 | 0.42910 |
| age_centered | -0.80000 | -0.80000 | -0.49175 | 0.39340 |
| quality_0 | 0.70465 | 0.70465 | 0.42556 | 0.29987 |
| work_0 | 216.00000 | 216.00000 | 0.00071 | 0.15352 |
| position_3 | 1.00000 | 1.00000 | 0.15110 | 0.15110 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.14653 | -0.14653 |
| draft_known | 1.00000 | 1.00000 | 0.12202 | 0.12202 |
| pooled_MLB_HR | 0.07979 | 0.49787 | 0.23961 | 0.11930 |

Linear intercept: -0.713868. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Jeff McNeil — 2018 → 2019

Selection: fixed diagnostic.

Inputs: age 26, MLB PA 248/0/0, current observed quality 0.4199, pooled MLB quality 0.4199; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 356, class unknown, rank 0.2271, rank × low-exposure 0.0242.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 14 | 1 | 1 | 2 |
| 2017 | AAA | 78 | 1 | 10 | 3 |
| 2017 | Aplus | 116 | 3 | 19 | 6 |
| 2018 | AA | 241 | 14 | 23 | 21 |
| 2018 | AAA | 143 | 5 | 19 | 13 |
| 2018 | MLB | 248 | 3 | 24 | 13 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 364.61 | 2.2706 | — |
| pooled | 393.99 | 1.6234 | 0.6426 |
| pedigree | 399.17 | 1.7226 | 0.6513 |
| pooled_product | 393.99 | 1.6350 | — |
| pedigree_product | 399.17 | 1.6623 | — |
| safe_ridge | 399.17 | 1.0794 | -0.2247 |

Actual: 567 PA / 4.9043 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 399.16982478206336, "value": 1.737259143077359, "rate": 0.6513183147010042}. Artificial input probe, not a causal effect or independently validated replacement forecast.

His excellent contact is visible: 42 minor strikeouts in 384 PA plus 24 in 248 MLB PA. Yet the linear assembly gives 399 PA/1.08 versus 567/4.90. The conditional AA K coefficient is positive, so McNeil's low strikeout input contributes negatively. That partial coefficient is not a causal claim that strikeouts help, but correlated league/current/pooled predictors and the active-player target have produced a baseball-unhelpful estimate in this important case. Mullins and O'Brien fail while Lowe succeeds; neither blanket debut optimism nor the aggregate linear-model gain resolves this talent miss.

Peers selected without future outcomes: Cedric Mullins (age 23, current MLB 191 PA, draft pick 403; actual next 74 PA / -0.80); Brandon Lowe (age 23, current MLB 148 PA, draft pick 87; actual next 327 PA / 2.04); Peter O'Brien (age 27, current MLB 74 PA, draft pick 94; actual next 47 PA / -0.19).

Training profile support: all=354 distinct people; active=279 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 24.00 | 248.00 | 0.2300 | 0.135057 |
| MLB / BB | 13.00 | 248.00 | 0.0800 | 0.060345 |
| MLB / HBP | 5.00 | 248.00 | 0.0100 | 0.017241 |
| MLB / HR | 3.00 | 248.00 | 0.0300 | 0.017241 |
| MLB / BABIP | 71.00 | 198.00 | 0.3000 | 0.338926 |
| MLB / 2B | 11.00 | 248.00 | 0.0500 | 0.045977 |
| MLB / 3B | 6.00 | 248.00 | 0.0050 | 0.018678 |
| AAA / K | 27.00 | 205.40 | 0.2300 | 0.163720 |
| AAA / BB | 15.40 | 205.40 | 0.0800 | 0.076621 |
| AAA / HBP | 2.60 | 205.40 | 0.0100 | 0.011788 |
| AAA / HR | 5.80 | 205.40 | 0.0300 | 0.028815 |
| AAA / BABIP | 54.60 | 153.60 | 0.3000 | 0.333596 |
| AAA / 2B | 14.00 | 205.40 | 0.0500 | 0.062213 |
| AAA / 3B | 2.00 | 205.40 | 0.0050 | 0.008186 |
| AA / K | 23.60 | 249.40 | 0.2300 | 0.133371 |
| AA / BB | 22.20 | 249.40 | 0.0800 | 0.086434 |
| AA / HBP | 5.00 | 249.40 | 0.0100 | 0.017172 |
| AA / HR | 14.60 | 249.40 | 0.0300 | 0.050372 |
| AA / BABIP | 57.20 | 183.00 | 0.3000 | 0.308127 |
| AA / 2B | 16.60 | 249.40 | 0.0500 | 0.061820 |
| AA / 3B | 3.00 | 249.40 | 0.0050 | 0.010017 |
| Aplus / K | 15.20 | 92.80 | 0.2300 | 0.198133 |
| Aplus / BB | 4.80 | 92.80 | 0.0800 | 0.066390 |
| Aplus / HBP | 3.20 | 92.80 | 0.0100 | 0.021784 |
| Aplus / HR | 2.40 | 92.80 | 0.0300 | 0.028008 |
| Aplus / BABIP | 24.80 | 66.40 | 0.3000 | 0.329327 |
| Aplus / 2B | 5.60 | 92.80 | 0.0500 | 0.054979 |
| Aplus / 3B | 0.00 | 92.80 | 0.0050 | 0.002593 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.41986 | 0.41986 | 0.68771 | 0.28874 |
| work_0 | 247.89798 | 247.89798 | 0.00079 | 0.19652 |
| quality_0 | 0.41986 | 0.41986 | 0.42312 | 0.17765 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.15629 | -0.15629 |
| pooled_AA_K | 0.13337 | -0.96629 | 0.14902 | -0.14399 |
| position_4 | 1.00000 | 1.00000 | -0.13985 | -0.13985 |
| prior_debut | 1.00000 | 1.00000 | 0.11956 | 0.11956 |
| age_centered | -0.20000 | -0.20000 | -0.52320 | 0.10464 |

Linear intercept: -0.852402. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Spencer Steer — 2022 → 2023

Selection: fixed diagnostic.

Inputs: age 24, MLB PA 108/0/0, current observed quality -0.0844, pooled MLB quality -0.0844; captured listing 1 (not certified rights). Draft known 1, year 2019, pick 90, class unknown, rank 0.4080, rank × low-exposure 0.0343.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 197.75 | 0.6609 | — |
| pooled | 184.61 | 0.5616 | 0.0626 |
| pedigree | 183.02 | 0.4876 | 0.0199 |
| pooled_product | 184.61 | 0.5973 | — |
| pedigree_product | 183.02 | 0.5791 | — |
| safe_ridge | 183.02 | 0.5003 | -0.2385 |

Actual: 665 PA / 4.1749 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 180.4831651043233, "value": 0.48758953872372685, "rate": 0.03980802790269522}. Artificial input probe, not a causal effect or independently validated replacement forecast.

His 23 upper-minor HR and weak 108-PA MLB debut are both present. The corrected draft model gives 183 PA/0.49 and linear assembly 183/0.50 versus 665/4.17. Removing draft evidence barely changes 183 PA to 180. Henderson becomes a regular, Brennan gets 455 PA with little contribution, and Stowers gets 33 PA. This model still misses both regular opportunity and batting production; the qualified earlier V31 result must not be used to claim this repair solved Steer.

Peers selected without future outcomes: Gunnar Henderson (age 21, current MLB 132 PA, draft pick 42; actual next 622 PA / 3.40); Will Brennan (age 24, current MLB 45 PA, draft pick 250; actual next 455 PA / 0.17); Kyle Stowers (age 24, current MLB 98 PA, draft pick 71; actual next 33 PA / -0.45).

Training profile support: all=322 distinct people; active=282 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 26.00 | 108.00 | 0.2300 | 0.235577 |
| MLB / BB | 11.00 | 108.00 | 0.0800 | 0.091346 |
| MLB / HBP | 2.00 | 108.00 | 0.0100 | 0.014423 |
| MLB / HR | 2.00 | 108.00 | 0.0300 | 0.024038 |
| MLB / BABIP | 18.00 | 67.00 | 0.3000 | 0.287425 |
| MLB / 2B | 5.00 | 108.00 | 0.0500 | 0.048077 |
| MLB / 3B | 0.00 | 108.00 | 0.0050 | 0.002404 |
| AAA / K | 66.00 | 336.00 | 0.2300 | 0.204128 |
| AAA / BB | 36.00 | 336.00 | 0.0800 | 0.100917 |
| AAA / HBP | 7.00 | 336.00 | 0.0100 | 0.018349 |
| AAA / HR | 15.00 | 336.00 | 0.0300 | 0.041284 |
| AAA / BABIP | 60.00 | 211.00 | 0.3000 | 0.289389 |
| AAA / 2B | 17.00 | 336.00 | 0.0500 | 0.050459 |
| AAA / 3B | 1.00 | 336.00 | 0.0050 | 0.003440 |
| AA / K | 81.40 | 380.00 | 0.2300 | 0.217500 |
| AA / BB | 29.20 | 380.00 | 0.0800 | 0.077500 |
| AA / HBP | 8.00 | 380.00 | 0.0100 | 0.018750 |
| AA / HR | 19.20 | 380.00 | 0.0300 | 0.046250 |
| AA / BABIP | 70.80 | 241.40 | 0.3000 | 0.295255 |
| AA / 2B | 21.80 | 380.00 | 0.0500 | 0.055833 |
| AA / 3B | 2.60 | 380.00 | 0.0050 | 0.006458 |
| Aplus / K | 25.60 | 166.40 | 0.2300 | 0.182432 |
| Aplus / BB | 28.00 | 166.40 | 0.0800 | 0.135135 |
| Aplus / HBP | 3.20 | 166.40 | 0.0100 | 0.015766 |
| Aplus / HR | 8.00 | 166.40 | 0.0300 | 0.041291 |
| Aplus / BABIP | 28.80 | 101.60 | 0.3000 | 0.291667 |
| Aplus / 2B | 5.60 | 166.40 | 0.0500 | 0.039790 |
| Aplus / 3B | 0.80 | 166.40 | 0.0050 | 0.004880 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.53992 | 0.32395 |
| position_5 | 1.00000 | 1.00000 | 0.15645 | 0.15645 |
| reorganized | 1.00000 | 1.00000 | -0.12582 | -0.12582 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.12289 | -0.12289 |
| work_0 | 108.00000 | 108.00000 | 0.00104 | 0.11249 |
| pooled_AA_HR | 0.04625 | 0.16250 | 0.44147 | 0.07174 |
| pooled_Aplus_BB | 0.13514 | 0.55135 | 0.12790 | 0.07052 |
| pooled_AAA_BB | 0.10092 | 0.20917 | 0.33343 | 0.06974 |

Linear intercept: -0.761394. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Masyn Winn — 2023 → 2024

Selection: fixed diagnostic.

Inputs: age 21, MLB PA 137/0/0, current observed quality -0.5576, pooled MLB quality -0.5576; captured listing 1 (not certified rights). Draft known 1, year 2020, pick 54, class HS SR, rank 0.4752, rank × low-exposure 0.0276.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 291.13 | 0.8107 | — |
| pooled | 285.41 | 0.6469 | -0.7521 |
| pedigree | 302.68 | 0.5374 | -0.6958 |
| pooled_product | 285.41 | 0.5259 | — |
| pedigree_product | 302.68 | 0.5861 | — |
| safe_ridge | 302.68 | 0.5338 | -0.7995 |

Actual: 637 PA / 2.2595 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 280.3963777296361, "value": 0.5374400049428385, "rate": -0.7896791406265573}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The inputs contain 498 AAA PA with 18 HR and 83 K, alongside a weak 137-PA MLB debut. Draft evidence raises expected PA from 280 to 303; the linear assembly gives 0.53 contribution against 637 PA/2.26 actual. Low current and pooled MLB quality overwhelm much of the positive age term. Meadows and Edwards advance but Adams does not. Entry context helps modestly without solving reliability of a brief debut or the subsequent regular job.

Peers selected without future outcomes: Parker Meadows (age 23, current MLB 145 PA, draft pick 44; actual next 298 PA / 1.21); Xavier Edwards (age 23, current MLB 84 PA, draft pick 38; actual next 303 PA / 2.19); Jordyn Adams (age 23, current MLB 40 PA, draft pick 17; actual next 38 PA / 0.00).

Training profile support: all=371 distinct people; active=326 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 26.00 | 137.00 | 0.2300 | 0.206751 |
| MLB / BB | 10.00 | 137.00 | 0.0800 | 0.075949 |
| MLB / HBP | 0.00 | 137.00 | 0.0100 | 0.004219 |
| MLB / HR | 2.00 | 137.00 | 0.0300 | 0.021097 |
| MLB / BABIP | 19.00 | 97.00 | 0.3000 | 0.248731 |
| MLB / 2B | 2.00 | 137.00 | 0.0500 | 0.029536 |
| MLB / 3B | 0.00 | 137.00 | 0.0050 | 0.002110 |
| AAA / K | 83.00 | 498.00 | 0.2300 | 0.177258 |
| AAA / BB | 44.00 | 498.00 | 0.0800 | 0.086957 |
| AAA / HBP | 7.00 | 498.00 | 0.0100 | 0.013378 |
| AAA / HR | 18.00 | 498.00 | 0.0300 | 0.035117 |
| AAA / BABIP | 110.00 | 346.00 | 0.3000 | 0.313901 |
| AAA / 2B | 15.00 | 498.00 | 0.0500 | 0.033445 |
| AAA / 3B | 7.00 | 498.00 | 0.0050 | 0.012542 |
| AA / K | 68.80 | 322.40 | 0.2300 | 0.217330 |
| AA / BB | 40.00 | 322.40 | 0.0800 | 0.113636 |
| AA / HBP | 0.80 | 322.40 | 0.0100 | 0.004261 |
| AA / HR | 8.80 | 322.40 | 0.0300 | 0.027936 |
| AA / BABIP | 62.40 | 202.40 | 0.3000 | 0.305556 |
| AA / 2B | 20.00 | 322.40 | 0.0500 | 0.059186 |
| AA / 3B | 0.80 | 322.40 | 0.0050 | 0.003078 |
| Aplus / K | 47.20 | 210.00 | 0.2300 | 0.226452 |
| Aplus / BB | 14.00 | 210.00 | 0.0800 | 0.070968 |
| Aplus / HBP | 0.80 | 210.00 | 0.0100 | 0.005806 |
| Aplus / HR | 2.00 | 210.00 | 0.0300 | 0.016129 |
| Aplus / BABIP | 52.60 | 145.20 | 0.3000 | 0.336868 |
| Aplus / 2B | 11.20 | 210.00 | 0.0500 | 0.052258 |
| Aplus / 3B | 6.80 | 210.00 | 0.0050 | 0.023548 |
| A / K | 36.00 | 170.40 | 0.2300 | 0.218195 |
| A / BB | 24.00 | 170.40 | 0.0800 | 0.118343 |
| A / HBP | 1.80 | 170.40 | 0.0100 | 0.010355 |
| A / HR | 1.80 | 170.40 | 0.0300 | 0.017751 |
| A / BABIP | 35.40 | 106.80 | 0.3000 | 0.316248 |
| A / 2B | 9.00 | 170.40 | 0.0500 | 0.051775 |
| A / 3B | 1.80 | 170.40 | 0.0050 | 0.008506 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.55153 | 0.66183 |
| pooled_mlb_quality | -0.55760 | -0.55760 | 0.74867 | -0.41746 |
| position_6 | 1.00000 | 1.00000 | -0.27030 | -0.27030 |
| quality_0 | -0.55760 | -0.55760 | 0.46702 | -0.26041 |
| reorganized | 1.00000 | 1.00000 | -0.18086 | -0.18086 |
| work_0 | 137.00000 | 137.00000 | 0.00115 | 0.15702 |
| pooled_MLB_BABIP | 0.24873 | -0.51269 | -0.24318 | 0.12468 |
| pooled_A_BB | 0.11834 | 0.38343 | 0.27049 | 0.10371 |

Linear intercept: -0.830418. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Aaron Judge — 2016 → 2017

Selection: fixed diagnostic; pooled false low; pedigree false low; pooled_product false low; pedigree_product false low; safe_ridge false low.

Inputs: age 24, MLB PA 95/0/0, current observed quality -0.1751, pooled MLB quality -0.1751; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 32, class unknown, rank 0.5440, rank × low-exposure 0.0319.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 122.37 | 0.2201 | — |
| pooled | 150.91 | 0.3319 | -0.1182 |
| pedigree | 143.97 | 0.2392 | -0.1176 |
| pooled_product | 150.91 | 0.4363 | — |
| pedigree_product | 143.97 | 0.4164 | — |
| safe_ridge | 143.97 | 0.4309 | -0.0572 |

Actual: 678 PA / 8.1084 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 143.58002672705, "value": 0.23916122952753385, "rate": -0.2539931841545696}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The known pick 32 and 19 AAA HR in 410 PA do not overcome 42 strikeouts in a 95-PA MLB debut. The draft model gives 144 PA/0.24 and linear assembly 144/0.43 versus 678/8.11. Cowart, Marrero and Nimmo have mixed limited opportunities. This is a large opportunity and talent false low, not an excuse to manually turn every high-power brief debut into a superstar.

Peers selected without future outcomes: Kaleb Cowart (age 24, current MLB 87 PA, draft pick 18; actual next 117 PA / 0.12); Deven Marrero (age 25, current MLB 14 PA, draft pick 24; actual next 188 PA / -0.45); Brandon Nimmo (age 23, current MLB 80 PA, draft pick 13; actual next 215 PA / 1.14).

Training profile support: all=186 distinct people; active=159 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 42.00 | 95.00 | 0.2300 | 0.333333 |
| MLB / BB | 9.00 | 95.00 | 0.0800 | 0.087179 |
| MLB / HBP | 1.00 | 95.00 | 0.0100 | 0.010256 |
| MLB / HR | 4.00 | 95.00 | 0.0300 | 0.035897 |
| MLB / BABIP | 11.00 | 39.00 | 0.3000 | 0.294964 |
| MLB / 2B | 2.00 | 95.00 | 0.0500 | 0.035897 |
| MLB / 3B | 0.00 | 95.00 | 0.0050 | 0.002564 |
| AAA / K | 157.20 | 618.00 | 0.2300 | 0.250975 |
| AAA / BB | 70.20 | 618.00 | 0.0800 | 0.108914 |
| AAA / HBP | 8.00 | 618.00 | 0.0100 | 0.012535 |
| AAA / HR | 25.40 | 618.00 | 0.0300 | 0.039554 |
| AAA / BABIP | 110.40 | 357.20 | 0.3000 | 0.307087 |
| AAA / 2B | 26.00 | 618.00 | 0.0500 | 0.043175 |
| AAA / 3B | 1.00 | 618.00 | 0.0050 | 0.002089 |
| AA / K | 56.00 | 224.00 | 0.2300 | 0.243827 |
| AA / BB | 18.40 | 224.00 | 0.0800 | 0.081481 |
| AA / HBP | 2.40 | 224.00 | 0.0100 | 0.010494 |
| AA / HR | 9.60 | 224.00 | 0.0300 | 0.038889 |
| AA / BABIP | 47.20 | 136.80 | 0.3000 | 0.326014 |
| AA / 2B | 12.80 | 224.00 | 0.0500 | 0.054938 |
| AA / 3B | 2.40 | 224.00 | 0.0050 | 0.008951 |
| Aplus / K | 43.20 | 171.00 | 0.2300 | 0.244280 |
| Aplus / BB | 29.40 | 171.00 | 0.0800 | 0.138007 |
| Aplus / HBP | 0.60 | 171.00 | 0.0100 | 0.005904 |
| Aplus / HR | 4.80 | 171.00 | 0.0300 | 0.028782 |
| Aplus / BABIP | 34.80 | 92.40 | 0.3000 | 0.336798 |
| Aplus / 2B | 5.40 | 171.00 | 0.0500 | 0.038376 |
| Aplus / 3B | 1.20 | 171.00 | 0.0050 | 0.006273 |
| A / K | 35.40 | 166.80 | 0.2300 | 0.218891 |
| A / BB | 22.80 | 166.80 | 0.0800 | 0.115442 |
| A / HBP | 1.20 | 166.80 | 0.0100 | 0.008246 |
| A / HR | 5.40 | 166.80 | 0.0300 | 0.031484 |
| A / BABIP | 41.40 | 101.40 | 0.3000 | 0.354518 |
| A / 2B | 9.00 | 166.80 | 0.0500 | 0.052474 |
| A / 3B | 1.20 | 166.80 | 0.0050 | 0.006372 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.47804 | 0.28682 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.20421 | -0.20421 |
| position_9 | 1.00000 | 1.00000 | 0.16556 | 0.16556 |
| pooled_mlb_quality | -0.17509 | -0.17509 | 0.68008 | -0.11908 |
| pooled_Aplus_BB | 0.13801 | 0.58007 | 0.19515 | 0.11320 |
| pooled_Aplus_BABIP | 0.33680 | 0.36798 | 0.24641 | 0.09067 |
| work_0 | 95.07825 | 95.07825 | 0.00088 | 0.08346 |
| AA_1_pa | 280.00000 | 0.46667 | -0.16792 | -0.07836 |

Linear intercept: -0.746346. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Aaron Judge — 2021 → 2022

Selection: fixed diagnostic; pooled largest harm vs repaired_direct; safe_ridge largest harm vs repaired_direct.

Inputs: age 29, MLB PA 633/114/447, current observed quality 1.2786, pooled MLB quality 1.5617; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 32, class unknown, rank 0.5440, rank × low-exposure 0.0414.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 19 | 1 | 7 | 3 |
| 2019 | MLB | 447 | 27 | 141 | 60 |
| 2020 | MLB | 114 | 9 | 32 | 10 |
| 2021 | MLB | 633 | 39 | 158 | 73 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 491.62 | 3.6671 | — |
| pooled | 470.53 | 2.9274 | 2.4705 |
| pedigree | 462.28 | 3.1881 | 2.4622 |
| pooled_product | 470.53 | 3.4125 | — |
| pedigree_product | 462.28 | 3.3463 | — |
| safe_ridge | 462.28 | 2.9827 | 1.9902 |

Actual: 696 PA / 9.7895 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 462.53174251988224, "value": 2.958042119714287, "rate": 2.4627901297761743}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The model sees 633 current MLB PA/39 HR, the actual short-2020 sample, and strong pooled quality. Nevertheless it gives 462 PA/2.98 in the linear assembly versus 696/9.79; this is a largest-harm case against the corrected direct control. Olson and Turner retain big workloads while Castellanos' batting declines. Both opportunity and elite performance are too conservative. The historic 62-HR breakout was not guaranteed, but missing input data is not the explanation here.

Peers selected without future outcomes: Matt Olson (age 27, current MLB 673 PA, draft pick 47; actual next 699 PA / 4.00); Trea Turner (age 28, current MLB 646 PA, draft pick 13; actual next 708 PA / 4.54); Nick Castellanos (age 29, current MLB 585 PA, draft pick 44; actual next 558 PA / 1.57).

Training profile support: all=412 distinct people; active=334 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 268.20 | 992.40 | 0.2300 | 0.266569 |
| MLB / BB | 117.00 | 992.40 | 0.0800 | 0.114427 |
| MLB / HBP | 6.40 | 992.40 | 0.0100 | 0.006774 |
| MLB / HR | 62.40 | 992.40 | 0.0300 | 0.059868 |
| MLB / BABIP | 178.20 | 532.60 | 0.3000 | 0.329118 |
| MLB / 2B | 37.20 | 992.40 | 0.0500 | 0.038631 |
| MLB / 3B | 0.60 | 992.40 | 0.0050 | 0.001007 |
| AAA / K | 4.20 | 11.40 | 0.2300 | 0.244165 |
| AAA / BB | 1.80 | 11.40 | 0.0800 | 0.087971 |
| AAA / HBP | 0.00 | 11.40 | 0.0100 | 0.008977 |
| AAA / HR | 0.60 | 11.40 | 0.0300 | 0.032316 |
| AAA / BABIP | 0.60 | 4.80 | 0.3000 | 0.291985 |
| AAA / 2B | 0.00 | 11.40 | 0.0500 | 0.044883 |
| AAA / 3B | 0.00 | 11.40 | 0.0050 | 0.004488 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.56168 | 1.56168 | 0.69176 | 1.08030 |
| work_0 | 633.26060 | 633.26060 | 0.00092 | 0.58365 |
| quality_0 | 1.27862 | 1.27862 | 0.44604 | 0.57032 |
| age_centered | 0.40000 | 0.40000 | -0.54223 | -0.21689 |
| work_1 | 308.48552 | 308.48552 | 0.00070 | 0.21482 |
| work_2 | 447.18403 | 447.18403 | 0.00042 | 0.18624 |
| position_9 | 1.00000 | 1.00000 | 0.15162 | 0.15162 |
| quality_2 | 0.84332 | 0.84332 | 0.16580 | 0.13982 |

Linear intercept: -0.783180. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Brent Rooker — 2022 → 2023

Selection: fixed diagnostic.

Inputs: age 27, MLB PA 36/213/21, current observed quality -0.1738, pooled MLB quality -0.1788; captured listing 1 (not certified rights). Draft known 1, year 2017, pick 35, class unknown, rank 0.5322, rank × low-exposure 0.0531.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 21 | 1 | 5 | 0 |
| 2021 | AAA | 267 | 20 | 80 | 36 |
| 2021 | MLB | 213 | 9 | 70 | 15 |
| 2022 | AAA | 365 | 28 | 103 | 44 |
| 2022 | MLB | 36 | 0 | 11 | 3 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 112.32 | 0.1852 | — |
| pooled | 105.62 | 0.0316 | -0.5987 |
| pedigree | 112.99 | 0.0626 | -0.5508 |
| pooled_product | 105.62 | 0.2253 | — |
| pedigree_product | 112.99 | 0.2501 | — |
| safe_ridge | 112.99 | 0.2798 | -0.3929 |

Actual: 526 PA / 2.9817 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 94.55143270953671, "value": 0.0074182340499050195, "rate": -0.6513804040956023}. Artificial input probe, not a causal effect or independently validated replacement forecast.

His 28 AAA HR in 365 PA and earlier 20 in 267 AAA PA are known. Draft evidence adds about 18 expected PA, leaving 113 PA/0.28 in the linear assembly versus 526/2.98. Richie Martin and Monte Harrison do not play, while Thaiss gets 307 PA with modest value. This is an unresolved late-emerging regular and job-context miss; a blanket boost for older minor-league power would also create false positives.

Peers selected without future outcomes: Richie Martin Jr. (age 27, current MLB 33 PA, draft pick 20; actual next 0 PA / 0.00); Monte Harrison (age 26, current MLB 14 PA, draft pick 50; actual next 0 PA / 0.00); Matt Thaiss (age 27, current MLB 81 PA, draft pick 16; actual next 307 PA / 0.38).

Training profile support: all=573 distinct people; active=453 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 70.00 | 219.00 | 0.2300 | 0.291536 |
| MLB / BB | 15.00 | 219.00 | 0.0800 | 0.072100 |
| MLB / HBP | 9.40 | 219.00 | 0.0100 | 0.032602 |
| MLB / HR | 7.80 | 219.00 | 0.0300 | 0.033856 |
| MLB / BABIP | 30.20 | 116.80 | 0.3000 | 0.277675 |
| MLB / 2B | 10.20 | 219.00 | 0.0500 | 0.047649 |
| MLB / 3B | 0.00 | 219.00 | 0.0050 | 0.001567 |
| AAA / K | 167.00 | 578.60 | 0.2300 | 0.279988 |
| AAA / BB | 72.80 | 578.60 | 0.0800 | 0.119069 |
| AAA / HBP | 13.80 | 578.60 | 0.0100 | 0.021810 |
| AAA / HR | 44.00 | 578.60 | 0.0300 | 0.069260 |
| AAA / BABIP | 88.20 | 277.40 | 0.3000 | 0.313196 |
| AAA / 2B | 33.40 | 578.60 | 0.0500 | 0.056587 |
| AAA / 3B | 0.80 | 578.60 | 0.0050 | 0.001916 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| position_7 | 1.00000 | 1.00000 | 0.22877 | 0.22877 |
| pooled_AAA_HR | 0.06926 | 0.39260 | 0.47960 | 0.18829 |
| pooled_mlb_quality | -0.17881 | -0.17881 | 0.71661 | -0.12814 |
| reorganized | 1.00000 | 1.00000 | -0.12584 | -0.12584 |
| pooled_AAA_BB | 0.11907 | 0.39069 | 0.24445 | 0.09550 |
| quality_present_2 | 1.00000 | 1.00000 | -0.07743 | -0.07743 |
| pooled_MLB_K | 0.29154 | 0.61536 | -0.12052 | -0.07416 |
| quality_0 | -0.17385 | -0.17385 | 0.36489 | -0.06344 |

Linear intercept: -0.704728. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Matt McLain — 2024 → 2025

Selection: fixed diagnostic.

Inputs: age 24, MLB PA 0/403/0, current observed quality 0.0000, pooled MLB quality 0.5667; captured listing 0 (not certified rights). Draft known 1, year 2021, pick 17, class 4YR JR, rank 0.6273, rank × low-exposure 0.0553.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 95.83 | 0.8083 | — |
| pooled | 174.46 | 1.6929 | 0.7276 |
| pedigree | 155.44 | 1.5964 | 0.8595 |
| pooled_product | 174.46 | 0.7566 | — |
| pedigree_product | 155.44 | 0.7083 | — |
| safe_ridge | 155.44 | 0.5369 | 0.1978 |

Actual: 577 PA / 0.5681 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 130.53086568634043, "value": 1.4790928853844396, "rate": 0.6976440108942173}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Zero current MLB PA follows 403 PA/16 HR in the prior season; that talent evidence is retained, while a captured listing zero is not certified lost rights. The linear assembly's 155 PA/0.54 almost matches 0.57 contribution but badly misses 577 actual PA. This is cancellation of workload and performance errors, not a successful full forecast. Clearing draft evidence reduces PA to 130. Swaggerty, Walker and Proctor do not return; only four active training people share this coarse profile, so temporary absence cannot be treated as ordinary exit.

Peers selected without future outcomes: Travis Swaggerty (age 26, current MLB 0 PA, draft pick 10; actual next 0 PA / 0.00); Steele Walker (age 27, current MLB 0 PA, draft pick 46; actual next 0 PA / 0.00); Ford Proctor (age 27, current MLB 0 PA, draft pick 92; actual next 0 PA / 0.00).

Training profile support: all=5 distinct people; active=4 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 92.00 | 322.40 | 0.2300 | 0.272254 |
| MLB / BB | 24.80 | 322.40 | 0.0800 | 0.077652 |
| MLB / HBP | 5.60 | 322.40 | 0.0100 | 0.015625 |
| MLB / HR | 12.80 | 322.40 | 0.0300 | 0.037405 |
| MLB / BABIP | 72.00 | 187.20 | 0.3000 | 0.355153 |
| MLB / 2B | 18.40 | 322.40 | 0.0500 | 0.055398 |
| MLB / 3B | 3.20 | 322.40 | 0.0050 | 0.008759 |
| AAA / K | 29.60 | 144.00 | 0.2300 | 0.215574 |
| AAA / BB | 23.20 | 144.00 | 0.0800 | 0.127869 |
| AAA / HBP | 4.00 | 144.00 | 0.0100 | 0.020492 |
| AAA / HR | 9.60 | 144.00 | 0.0300 | 0.051639 |
| AAA / BABIP | 29.60 | 76.80 | 0.3000 | 0.337104 |
| AAA / 2B | 9.60 | 144.00 | 0.0500 | 0.059836 |
| AAA / 3B | 0.80 | 144.00 | 0.0050 | 0.005328 |
| AA / K | 76.20 | 271.20 | 0.2300 | 0.267241 |
| AA / BB | 41.40 | 271.20 | 0.0800 | 0.133082 |
| AA / HBP | 4.80 | 271.20 | 0.0100 | 0.015625 |
| AA / HR | 10.20 | 271.20 | 0.0300 | 0.035560 |
| AA / BABIP | 41.40 | 138.00 | 0.3000 | 0.300000 |
| AA / 2B | 12.60 | 271.20 | 0.0500 | 0.047414 |
| AA / 3B | 3.00 | 271.20 | 0.0050 | 0.009429 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.56675 | 0.56675 | 0.77797 | 0.44091 |
| age_centered | -0.60000 | -0.60000 | -0.55871 | 0.33522 |
| position_6 | 1.00000 | 1.00000 | -0.27638 | -0.27638 |
| reorganized | 1.00000 | 1.00000 | -0.26366 | -0.26366 |
| pooled_MLB_BABIP | 0.35515 | 0.55153 | -0.36573 | -0.20171 |
| pooled_AA_BB | 0.13308 | 0.53082 | 0.33178 | 0.17611 |
| quality_1 | 0.67281 | 0.67281 | 0.26087 | 0.17552 |
| quality_present_1 | 1.00000 | 1.00000 | 0.17299 | 0.17299 |

Linear intercept: -0.927759. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Fernando Tatis Jr. — 2022 → 2023

Selection: fixed diagnostic.

Inputs: age 23, MLB PA 0/546/257, current observed quality 0.0000, pooled MLB quality 1.3674; captured listing 0 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |
| 2022 | AA | 14 | 0 | 2 | 4 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 136.64 | 1.7562 | — |
| pooled | 152.45 | 2.5184 | 1.6117 |
| pedigree | 150.15 | 2.1551 | 1.6421 |
| pooled_product | 152.45 | 0.8868 | — |
| pedigree_product | 150.15 | 0.8810 | — |
| safe_ridge | 150.15 | 0.7711 | 1.2029 |

Actual: 635 PA / 2.7352 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 150.1491090438067, "value": 2.155142409413028, "rate": 1.6420560198169822}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Prior 546 PA/42 HR and actual short-2020 257 PA/17 HR survive in pooled quality. The 2022 zero-MLB season and missing listing are nonetheless treated as weak opportunity: 150 PA/0.77 linear contribution versus 635/2.74. Basabe, Apostel and Grullon do not return and are weak substantive analogues to a young star under a finite suspension. This is an availability-state and workload gap, not vanished batting history or a case for inventing a roster listing.

Peers selected without future outcomes: Luis Alexander Basabe (age 25, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Sherten Apostel (age 23, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Deivy Grullón (age 26, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00).

Training profile support: all=22 distinct people; active=13 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 159.00 | 591.00 | 0.2300 | 0.263386 |
| MLB / BB | 60.40 | 591.00 | 0.0800 | 0.098987 |
| MLB / HBP | 4.60 | 591.00 | 0.0100 | 0.008104 |
| MLB / HR | 43.80 | 591.00 | 0.0300 | 0.067728 |
| MLB / BABIP | 101.40 | 317.80 | 0.3000 | 0.314505 |
| MLB / 2B | 31.40 | 591.00 | 0.0500 | 0.052677 |
| MLB / 3B | 1.20 | 591.00 | 0.0050 | 0.002460 |
| AA / K | 2.00 | 14.00 | 0.2300 | 0.219298 |
| AA / BB | 4.00 | 14.00 | 0.0800 | 0.105263 |
| AA / HBP | 1.00 | 14.00 | 0.0100 | 0.017544 |
| AA / HR | 0.00 | 14.00 | 0.0300 | 0.026316 |
| AA / BABIP | 2.00 | 7.00 | 0.3000 | 0.299065 |
| AA / 2B | 1.00 | 14.00 | 0.0500 | 0.052632 |
| AA / 3B | 1.00 | 14.00 | 0.0050 | 0.013158 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.36737 | 1.36737 | 0.71661 | 0.97987 |
| age_centered | -0.80000 | -0.80000 | -0.51241 | 0.40993 |
| quality_1 | 1.34788 | 1.34788 | 0.24371 | 0.32850 |
| work_2 | 695.44543 | 695.44543 | 0.00047 | 0.32494 |
| position_6 | 1.00000 | 1.00000 | -0.27939 | -0.27939 |
| quality_2 | 0.64772 | 0.64772 | 0.31154 | 0.20179 |
| work_1 | 546.22478 | 546.22478 | 0.00030 | 0.16245 |
| regular_window_scaled | 0.66667 | 0.66667 | -0.22157 | -0.14771 |

Linear intercept: -0.704728. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### David Ortiz — 2016 → 2017

Selection: fixed diagnostic; pooled_product largest gain vs repaired_direct.

Inputs: age 40, MLB PA 626/614/602, current observed quality 1.6130, pooled MLB quality 1.9309; captured listing 0 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | MLB | 602 | 35 | 95 | 53 |
| 2015 | MLB | 614 | 37 | 95 | 61 |
| 2016 | MLB | 626 | 38 | 86 | 65 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 373.75 | 3.3469 | — |
| pooled | 323.42 | 2.9827 | 1.8613 |
| pedigree | 336.59 | 3.0697 | 1.7543 |
| pooled_product | 323.42 | 2.0021 | — |
| pedigree_product | 336.59 | 2.0236 | — |
| safe_ridge | 336.59 | 2.3660 | 2.3648 |

Actual: 0 PA / 0.0000 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 336.58843934954064, "value": 3.069723980824797, "rate": 1.7543437090631342}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The model sees three productive, high-workload MLB seasons at age 40 but does not consume his known retirement. Its linear forecast remains 337 PA/2.37 against zero. Reduced value can win the loss comparison without recognizing retirement. Beltre, Beltran and Victor Martinez still play: age or a December nonlisting alone cannot encode definitive departure. A dated, affirmative status rule is warranted; a blanket old-player penalty is not.

Peers selected without future outcomes: Adrian Beltré (age 37, current MLB 640 PA, draft pick None; actual next 389 PA / 3.31); Carlos Beltrán (age 39, current MLB 593 PA, draft pick None; actual next 509 PA / 0.04); Victor Martinez (age 37, current MLB 610 PA, draft pick None; actual next 435 PA / 0.73).

Training profile support: all=8 distinct people; active=5 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 219.00 | 1478.40 | 0.2300 | 0.153320 |
| MLB / BB | 145.60 | 1478.40 | 0.0800 | 0.097314 |
| MLB / HBP | 3.80 | 1478.40 | 0.0100 | 0.003041 |
| MLB / HR | 88.60 | 1478.40 | 0.0300 | 0.058033 |
| MLB / BABIP | 277.20 | 980.40 | 0.3000 | 0.284339 |
| MLB / 2B | 93.80 | 1478.40 | 0.0500 | 0.062595 |
| MLB / 3B | 1.00 | 1478.40 | 0.0050 | 0.000950 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.93095 | 1.93095 | 0.71850 | 1.38740 |
| age_centered | 2.60000 | 2.60000 | -0.43609 | -1.13384 |
| quality_0 | 1.61299 | 1.61299 | 0.46678 | 0.75292 |
| work_2 | 602.00000 | 602.00000 | 0.00097 | 0.58322 |
| work_0 | 626.51565 | 626.51565 | 0.00073 | 0.45518 |
| age_squared | 6.76000 | 6.76000 | 0.04647 | 0.31412 |
| quality_1 | 0.96842 | 0.96842 | 0.23898 | 0.23144 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.21958 | -0.21958 |

Linear intercept: -0.537526. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Nelson Cruz — 2018 → 2019

Selection: fixed diagnostic.

Inputs: age 37, MLB PA 591/645/667, current observed quality 0.7483, pooled MLB quality 1.5853; captured listing 0 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | MLB | 667 | 43 | 159 | 57 |
| 2017 | MLB | 645 | 39 | 140 | 63 |
| 2018 | MLB | 591 | 37 | 122 | 50 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 348.45 | 2.3418 | — |
| pooled | 340.07 | 2.3996 | 1.2275 |
| pedigree | 338.85 | 2.4979 | 1.1782 |
| pooled_product | 340.07 | 1.7427 | — |
| pedigree_product | 338.85 | 1.7086 | — |
| safe_ridge | 338.85 | 1.9925 | 1.6808 |

Actual: 521 PA / 5.7414 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 338.84988215979837, "value": 2.4978838283728844, "rate": 1.178158494417159}. Artificial input probe, not a causal effect or independently validated replacement forecast.

His 37/39/43 HR over three high-workload seasons remain visible, yet the linear assembly gives 339 PA/1.99 against 521/5.74. The negative age term is large. Zobrist plays less, but Encarnacion and Choo still contribute substantially. Unlike Ortiz, Cruz is not retired: missing December listing is not lack of rights or lack of a future job. This opposite case rules out using generic old-player attrition as a retirement fix.

Peers selected without future outcomes: Ben Zobrist (age 37, current MLB 520 PA, draft pick None; actual next 176 PA / 0.31); Edwin Encarnación (age 35, current MLB 579 PA, draft pick None; actual next 486 PA / 3.34); Shin-Soo Choo (age 35, current MLB 665 PA, draft pick None; actual next 660 PA / 3.92).

Training profile support: all=111 distinct people; active=62 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 329.40 | 1507.20 | 0.2300 | 0.219263 |
| MLB / BB | 134.60 | 1507.20 | 0.0800 | 0.088726 |
| MLB / HBP | 29.00 | 1507.20 | 0.0100 | 0.018666 |
| MLB / HR | 94.00 | 1507.20 | 0.0300 | 0.060353 |
| MLB / BABIP | 268.40 | 906.60 | 0.3000 | 0.296443 |
| MLB / 2B | 56.60 | 1507.20 | 0.0500 | 0.038328 |
| MLB / 3B | 1.60 | 1507.20 | 0.0050 | 0.001307 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.58525 | 1.58525 | 0.67899 | 1.07638 |
| age_centered | 2.00000 | 2.00000 | -0.51138 | -1.02275 |
| work_0 | 590.75689 | 590.75689 | 0.00124 | 0.73094 |
| quality_1 | 1.11504 | 1.11504 | 0.26742 | 0.29818 |
| quality_2 | 1.16557 | 1.16557 | 0.25571 | 0.29805 |
| position_10 | 1.00000 | 1.00000 | 0.28402 | 0.28402 |
| quality_0 | 0.74825 | 0.74825 | 0.35956 | 0.26904 |
| work_1 | 645.00000 | 645.00000 | 0.00039 | 0.25154 |

Linear intercept: -0.615875. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Bryce Eldridge — 2024 → 2025

Selection: fixed diagnostic.

Inputs: age 19, MLB PA 0/0/0, current observed quality 0.0000, pooled MLB quality 0.0000; captured listing 0 (not certified rights). Draft known 1, year 2023, pick 16, class HS SR, rank 0.6352, rank × low-exposure 0.0848.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2023 | A | 69 | 1 | 18 | 11 |
| 2023 | RK121 | 61 | 5 | 16 | 8 |
| 2024 | A | 229 | 10 | 61 | 17 |
| 2024 | AA | 40 | 1 | 8 | 2 |
| 2024 | AAA | 35 | 0 | 11 | 4 |
| 2024 | Aplus | 215 | 12 | 52 | 33 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 6.76 | -0.0091 | — |
| pooled | 28.26 | 0.0459 | -0.5867 |
| pedigree | 42.53 | 0.1635 | -0.5339 |
| pooled_product | 28.26 | 0.0606 | — |
| pedigree_product | 42.53 | 0.0950 | — |
| safe_ridge | 42.53 | 0.1499 | 0.2404 |

Actual: 37 PA / -0.0927 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 13.227742108828744, "value": 0.06393686423675857, "rate": -0.6840966595993925}. Artificial input probe, not a causal effect or independently validated replacement forecast.

His pick 16, age 19 and 23 HR while progressing through four affiliated levels are known. Clearing draft inputs reduces PA from 43 to 13; the linear assembly gives 43/0.15 versus 37/-0.09. Miller, Romero and Isaac do not reach MLB next year, and only three active training people share the coarse profile. The opportunity estimate is plausible for this horizon, but a one-year contribution near zero is not a low career-value verdict or a validated current MLB-equivalent grade.

Peers selected without future outcomes: Aidan Miller (age 20, current MLB 0 PA, draft pick 27; actual next 0 PA / 0.00); Mikey Romero (age 20, current MLB 0 PA, draft pick 24; actual next 0 PA / 0.00); Xavier Isaac (age 20, current MLB 0 PA, draft pick 29; actual next 0 PA / 0.00).

Training profile support: all=14 distinct people; active=3 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| AAA / K | 11.00 | 35.00 | 0.2300 | 0.251852 |
| AAA / BB | 4.00 | 35.00 | 0.0800 | 0.088889 |
| AAA / HBP | 0.00 | 35.00 | 0.0100 | 0.007407 |
| AAA / HR | 0.00 | 35.00 | 0.0300 | 0.022222 |
| AAA / BABIP | 8.00 | 20.00 | 0.3000 | 0.316667 |
| AAA / 2B | 0.00 | 35.00 | 0.0500 | 0.037037 |
| AAA / 3B | 0.00 | 35.00 | 0.0050 | 0.003704 |
| AA / K | 8.00 | 40.00 | 0.2300 | 0.221429 |
| AA / BB | 2.00 | 40.00 | 0.0800 | 0.071429 |
| AA / HBP | 0.00 | 40.00 | 0.0100 | 0.007143 |
| AA / HR | 1.00 | 40.00 | 0.0300 | 0.028571 |
| AA / BABIP | 9.00 | 28.00 | 0.3000 | 0.304688 |
| AA / 2B | 2.00 | 40.00 | 0.0500 | 0.050000 |
| AA / 3B | 1.00 | 40.00 | 0.0050 | 0.010714 |
| Aplus / K | 52.00 | 215.00 | 0.2300 | 0.238095 |
| Aplus / BB | 33.00 | 215.00 | 0.0800 | 0.130159 |
| Aplus / HBP | 2.00 | 215.00 | 0.0100 | 0.009524 |
| Aplus / HR | 12.00 | 215.00 | 0.0300 | 0.047619 |
| Aplus / BABIP | 46.00 | 114.00 | 0.3000 | 0.355140 |
| Aplus / 2B | 11.00 | 215.00 | 0.0500 | 0.050794 |
| Aplus / 3B | 1.00 | 215.00 | 0.0050 | 0.004762 |
| A / K | 75.40 | 284.20 | 0.2300 | 0.256117 |
| A / BB | 25.80 | 284.20 | 0.0800 | 0.087975 |
| A / HBP | 3.00 | 284.20 | 0.0100 | 0.010411 |
| A / HR | 10.80 | 284.20 | 0.0300 | 0.035919 |
| A / BABIP | 56.80 | 169.20 | 0.3000 | 0.322437 |
| A / 2B | 15.60 | 284.20 | 0.0500 | 0.053618 |
| A / 3B | 0.00 | 284.20 | 0.0050 | 0.001301 |
| RK121 / K | 12.80 | 48.80 | 0.2300 | 0.240591 |
| RK121 / BB | 6.40 | 48.80 | 0.0800 | 0.096774 |
| RK121 / HBP | 0.00 | 48.80 | 0.0100 | 0.006720 |
| RK121 / HR | 4.00 | 48.80 | 0.0300 | 0.047043 |
| RK121 / BABIP | 8.00 | 24.80 | 0.3000 | 0.304487 |
| RK121 / 2B | 2.40 | 48.80 | 0.0500 | 0.049731 |
| RK121 / 3B | 0.00 | 48.80 | 0.0050 | 0.003360 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.60000 | -1.60000 | -0.54470 | 0.87153 |
| reorganized | 1.00000 | 1.00000 | -0.27170 | -0.27170 |
| pooled_Aplus_BABIP | 0.35514 | 0.55140 | 0.29642 | 0.16345 |
| age_squared | 2.56000 | 2.56000 | 0.04545 | 0.11636 |
| pooled_Aplus_BB | 0.13016 | 0.50159 | 0.21162 | 0.10615 |
| draft_rank | 0.63523 | 0.63523 | 0.14549 | 0.09242 |
| position_3 | 1.00000 | 1.00000 | 0.08524 | 0.08524 |
| pooled_AAA_BABIP | 0.31667 | 0.16667 | 0.38446 | 0.06408 |

Linear intercept: -0.825629. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Nick Kurtz — 2024 → 2025

Selection: fixed diagnostic.

Inputs: age 21, MLB PA 0/0/0, current observed quality 0.0000, pooled MLB quality 0.0000; captured listing 0 (not certified rights). Draft known 1, year 2024, pick 4, class 4YR JR, rank 0.8176, rank × low-exposure 0.5451.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 0.99 | 0.0053 | — |
| pooled | 6.00 | 0.0099 | -0.7010 |
| pedigree | 50.49 | 0.0659 | -0.7281 |
| pooled_product | 6.00 | 0.0117 | — |
| pedigree_product | 50.49 | 0.0965 | — |
| safe_ridge | 50.49 | 0.1483 | -0.1129 |

Actual: 489 PA / 5.7210 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 14.251256750370286, "value": 0.005521327339732538, "rate": -0.7744788872728774}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Pick 4 and college-junior entry accompany only 50 professional PA. Draft inputs lift expected PA from 14 to 50, but the linear assembly's 50/0.15 still misses 489/5.72 badly. Origin-selected college-entry peers include Christian Moore (184 PA), Cam Smith (493) and DeLauter (zero), so meaningful success and failure are both represented. There are zero active training people in Kurtz's coarse local profile. Entry evidence helps directionally; unsupported fast-arrival opportunity and conditional talent remain major gaps, not solved pedigree effects.

Peers selected without future outcomes: Christian Moore (age 21, current MLB 0 PA, draft pick 8; actual next 184 PA / 0.20); Cam Smith (age 21, current MLB 0 PA, draft pick 14; actual next 493 PA / 1.01); Chase DeLauter (age 22, current MLB 0 PA, draft pick 16; actual next 0 PA / 0.00).

Training profile support: all=10 distinct people; active=0 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| AA / K | 3.00 | 15.00 | 0.2300 | 0.226087 |
| AA / BB | 2.00 | 15.00 | 0.0800 | 0.086957 |
| AA / HBP | 0.00 | 15.00 | 0.0100 | 0.008696 |
| AA / HR | 0.00 | 15.00 | 0.0300 | 0.026087 |
| AA / BABIP | 4.00 | 10.00 | 0.3000 | 0.309091 |
| AA / 2B | 1.00 | 15.00 | 0.0500 | 0.052174 |
| AA / 3B | 0.00 | 15.00 | 0.0050 | 0.004348 |
| A / K | 7.00 | 35.00 | 0.2300 | 0.222222 |
| A / BB | 10.00 | 35.00 | 0.0800 | 0.133333 |
| A / HBP | 0.00 | 35.00 | 0.0100 | 0.007407 |
| A / HR | 4.00 | 35.00 | 0.0300 | 0.051852 |
| A / BABIP | 6.00 | 14.00 | 0.3000 | 0.315789 |
| A / 2B | 2.00 | 35.00 | 0.0500 | 0.051852 |
| A / 3B | 0.00 | 35.00 | 0.0050 | 0.003704 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.55871 | 0.67045 |
| reorganized | 1.00000 | 1.00000 | -0.26366 | -0.26366 |
| draft_rank | 0.81761 | 0.81761 | 0.15290 | 0.12501 |
| position_3 | 1.00000 | 1.00000 | 0.10497 | 0.10497 |
| age_squared | 1.44000 | 1.44000 | 0.06537 | 0.09413 |
| draft_college | 1.00000 | 1.00000 | 0.07994 | 0.07994 |
| draft_known | 1.00000 | 1.00000 | -0.07391 | -0.07391 |
| absence_window_scaled | 1.00000 | 1.00000 | -0.07065 | -0.07065 |

Linear intercept: -0.927759. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Jesús Made — 2024 → 2025

Selection: fixed diagnostic.

Inputs: age 17, MLB PA 0/0/0, current observed quality 0.0000, pooled MLB quality 0.0000; captured listing 0 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | DSL | 216 | 6 | 28 | 39 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 0.65 | 0.0009 | — |
| pooled | 0.42 | 0.0003 | -0.3767 |
| pedigree | 0.00 | 0.0000 | -0.2931 |
| pooled_product | 0.42 | 0.0011 | — |
| pedigree_product | 0.00 | 0.0000 | — |
| safe_ridge | 0.00 | 0.0000 | -0.0598 |

Actual: 0 PA / 0.0000 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 0.0, "value": 0, "rate": -0.2931375042400004}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Age 17, SS usage and DSL 216 PA with 6 HR, 28 K and 39 BB are present; international investment remains unknown. A zero next-year MLB forecast matches the actual zero, as do the nearest DSL peers. The conditional rate has only eight locally active training people and is not a certified current talent grade. This next-calendar-year test cannot establish that the model identifies a future superstar or fairly values his career.

Peers selected without future outcomes: Frederi Montero (age 17, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Jeremy Rodriguez (age 17, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Jhonny Level (age 17, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00).

Training profile support: all=3714 distinct people; active=8 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| DSL / K | 28.00 | 216.00 | 0.2300 | 0.161392 |
| DSL / BB | 39.00 | 216.00 | 0.0800 | 0.148734 |
| DSL / HBP | 2.00 | 216.00 | 0.0100 | 0.009494 |
| DSL / HR | 6.00 | 216.00 | 0.0300 | 0.028481 |
| DSL / BABIP | 52.00 | 141.00 | 0.3000 | 0.340249 |
| DSL / 2B | 9.00 | 216.00 | 0.0500 | 0.044304 |
| DSL / 3B | 6.00 | 216.00 | 0.0050 | 0.020570 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -2.00000 | -2.00000 | -0.54689 | 1.09378 |
| position_6 | 1.00000 | 1.00000 | -0.24209 | -0.24209 |
| reorganized | 1.00000 | 1.00000 | -0.19849 | -0.19849 |
| age_squared | 4.00000 | 4.00000 | 0.04853 | 0.19411 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.07786 | -0.07786 |
| absence_window_scaled | 1.00000 | 1.00000 | -0.03092 | -0.03092 |
| pooled_DSL_BB | 0.14873 | 0.68734 | 0.02799 | 0.01924 |
| pooled_DSL_K | 0.16139 | -0.68608 | -0.02653 | 0.01820 |

Linear intercept: -0.837910. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Leo De Vries — 2024 → 2025

Selection: fixed diagnostic.

Inputs: age 17, MLB PA 0/0/0, current observed quality 0.0000, pooled MLB quality 0.0000; captured listing 0 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 360 | 11 | 84 | 50 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 0.59 | 0.0010 | — |
| pooled | 0.37 | -0.0002 | -0.5078 |
| pedigree | 0.00 | 0.0000 | -0.5463 |
| pooled_product | 0.37 | 0.0008 | — |
| pedigree_product | 0.00 | 0.0000 | — |
| safe_ridge | 0.00 | 0.0000 | -0.1296 |

Actual: 0 PA / 0.0000 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 0.0, "value": 0, "rate": -0.546252473681947}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The model sees a 17-year-old SS with 360 A-ball PA, 11 HR, 84 K and 50 BB; international pedigree is unknown. Zero next-year MLB PA matches reality and the selected young-minor peers, but active-rate support is only nine people. Relative age and strong performance are available, not absent. A correct near-term zero says little about his eventual MLB ceiling or six-year value.

Peers selected without future outcomes: Eduardo Tait (age 17, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Pablo Guerrero (age 17, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); John Gil (age 18, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00).

Training profile support: all=3722 distinct people; active=9 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| A / K | 84.00 | 360.00 | 0.2300 | 0.232609 |
| A / BB | 50.00 | 360.00 | 0.0800 | 0.126087 |
| A / HBP | 9.00 | 360.00 | 0.0100 | 0.021739 |
| A / HR | 11.00 | 360.00 | 0.0300 | 0.030435 |
| A / BABIP | 60.00 | 206.00 | 0.3000 | 0.294118 |
| A / 2B | 22.00 | 360.00 | 0.0500 | 0.058696 |
| A / 3B | 3.00 | 360.00 | 0.0050 | 0.007609 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -2.00000 | -2.00000 | -0.54470 | 1.08941 |
| position_6 | 1.00000 | 1.00000 | -0.28248 | -0.28248 |
| reorganized | 1.00000 | 1.00000 | -0.27170 | -0.27170 |
| age_squared | 4.00000 | 4.00000 | 0.04545 | 0.18181 |
| pooled_A_BB | 0.12609 | 0.46087 | 0.16070 | 0.07406 |
| absence_window_scaled | 1.00000 | 1.00000 | -0.04114 | -0.04114 |
| pooled_A_pa | 360.00000 | 0.60000 | -0.04920 | -0.02952 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.02366 | -0.02366 |

Linear intercept: -0.825629. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Matt Olson — 2022 → 2023

Selection: pooled largest gain vs repaired_direct; pedigree largest gain vs repaired_direct; pedigree_product largest gain vs repaired_direct; safe_ridge largest gain vs repaired_direct.

Inputs: age 28, MLB PA 699/673/245, current observed quality 0.5736, pooled MLB quality 1.0332; captured listing 1 (not certified rights). Draft known 1, year 2012, pick 47, class unknown, rank 0.4935, rank × low-exposure 0.0287.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 530.90 | 2.4704 | — |
| pooled | 565.63 | 3.7280 | 1.3982 |
| pedigree | 572.22 | 3.7320 | 1.5409 |
| pooled_product | 565.63 | 3.0890 | — |
| pedigree_product | 572.22 | 3.2612 | — |
| safe_ridge | 572.22 | 3.4539 | 1.7430 |

Actual: 720 PA / 7.7142 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 572.2266850176923, "value": 3.625548998442879, "rate": 1.4361437088460385}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The pooled evidence preserves 39 HR in the prior full season alongside current 699 PA/34 HR and actual 2020 counts. The linear assembly improves to 572 PA/3.45 from control 531/2.47, versus 720/7.71 actual; this is the largest control-comparison gain. Removing draft evidence leaves the workload essentially unchanged, so this is continuity of performance, not a new pedigree discovery. Bell, Chapman and Seager remain productive with differing ceilings. The change makes baseball sense but does not predict a 54-HR breakout with certainty.

Peers selected without future outcomes: Josh Bell (age 29, current MLB 647 PA, draft pick 61; actual next 617 PA / 2.12); Matt Chapman (age 29, current MLB 621 PA, draft pick 25; actual next 581 PA / 2.34); Corey Seager (age 28, current MLB 663 PA, draft pick 18; actual next 536 PA / 5.89).

Training profile support: all=558 distinct people; active=435 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 306.60 | 1384.40 | 0.2300 | 0.222043 |
| MLB / BB | 149.00 | 1384.40 | 0.0800 | 0.105767 |
| MLB / HBP | 11.80 | 1384.40 | 0.0100 | 0.008623 |
| MLB / HR | 73.60 | 1384.40 | 0.0300 | 0.051603 |
| MLB / BABIP | 221.40 | 826.60 | 0.3000 | 0.271314 |
| MLB / 2B | 74.40 | 1384.40 | 0.0500 | 0.053490 |
| MLB / 3B | 0.60 | 1384.40 | 0.0050 | 0.000741 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.03318 | 1.03318 | 0.75838 | 0.78355 |
| work_0 | 699.00000 | 699.00000 | 0.00097 | 0.67929 |
| work_2 | 662.97327 | 662.97327 | 0.00059 | 0.39232 |
| quality_0 | 0.57358 | 0.57358 | 0.42210 | 0.24211 |
| quality_1 | 1.07747 | 1.07747 | 0.21883 | 0.23578 |
| regular_window_scaled | 1.00000 | 1.00000 | -0.16089 | -0.16089 |
| reorganized | 1.00000 | 1.00000 | -0.13328 | -0.13328 |
| work_1 | 673.27707 | 673.27707 | 0.00019 | 0.12846 |

Linear intercept: -0.649993. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Yordan Alvarez — 2024 → 2025

Selection: pooled false high; pooled_product false high; pedigree_product false high; safe_ridge false high.

Inputs: age 27, MLB PA 635/496/561, current observed quality 1.4157, pooled MLB quality 2.4571; captured listing 1 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 593.63 | 6.0672 | — |
| pooled | 617.20 | 5.2317 | 3.8150 |
| pedigree | 601.31 | 4.9951 | 3.7507 |
| pooled_product | 617.20 | 5.8526 | — |
| pedigree_product | 601.31 | 5.6374 | — |
| safe_ridge | 601.31 | 5.6478 | 3.7610 |

Actual: 199 PA / 0.9251 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 601.3074637120812, "value": 4.995112788190476, "rate": 3.7506915006591193}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Three elite batting seasons and 635 current PA support a regular-player forecast. The linear assembly gives 601 PA/5.65 versus 199/0.93, a major false high. Guerrero, Contreras and Devers retain high workloads among origin-selected peers. The source history is good; unexpected absence or collapse is not evidence for globally deflating elite hitters. This case exposes the need for calibrated opportunity risk, not an obvious bad-count repair.

Peers selected without future outcomes: Vladimir Guerrero Jr. (age 25, current MLB 697 PA, draft pick None; actual next 680 PA / 4.97); William Contreras (age 26, current MLB 679 PA, draft pick None; actual next 659 PA / 3.10); Rafael Devers (age 27, current MLB 601 PA, draft pick None; actual next 729 PA / 5.23).

Training profile support: all=433 distinct people; active=342 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 232.20 | 1368.40 | 0.2300 | 0.173795 |
| MLB / BB | 145.60 | 1368.40 | 0.0800 | 0.104604 |
| MLB / HBP | 24.00 | 1368.40 | 0.0100 | 0.017025 |
| MLB / HR | 82.00 | 1368.40 | 0.0300 | 0.057886 |
| MLB / BABIP | 270.40 | 859.20 | 0.3000 | 0.313178 |
| MLB / 2B | 70.60 | 1368.40 | 0.0500 | 0.051485 |
| MLB / 3B | 4.00 | 1368.40 | 0.0050 | 0.003065 |
| AAA / K | 0.80 | 8.80 | 0.2300 | 0.218750 |
| AAA / BB | 1.60 | 8.80 | 0.0800 | 0.088235 |
| AAA / HBP | 0.00 | 8.80 | 0.0100 | 0.009191 |
| AAA / HR | 0.00 | 8.80 | 0.0300 | 0.027574 |
| AAA / BABIP | 2.40 | 6.40 | 0.3000 | 0.304511 |
| AAA / 2B | 0.80 | 8.80 | 0.0500 | 0.053309 |
| AAA / 3B | 0.00 | 8.80 | 0.0050 | 0.004596 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 2.45709 | 2.45709 | 0.77797 | 1.91155 |
| quality_0 | 1.41565 | 1.41565 | 0.45316 | 0.64151 |
| work_0 | 635.26142 | 635.26142 | 0.00099 | 0.63054 |
| work_2 | 561.00000 | 561.00000 | 0.00078 | 0.43904 |
| quality_1 | 1.38309 | 1.38309 | 0.26087 | 0.36081 |
| quality_2 | 1.73811 | 1.73811 | 0.19751 | 0.34330 |
| position_10 | 1.00000 | 1.00000 | 0.31604 | 0.31604 |
| reorganized | 1.00000 | 1.00000 | -0.26366 | -0.26366 |

Linear intercept: -0.927759. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Greg Garcia — 2016 → 2017

Selection: pooled ordinary partial workload.

Inputs: age 26, MLB PA 257/87/18, current observed quality 0.1690, pooled MLB quality 0.1555; captured listing 1 (not certified rights). Draft known 1, year 2010, pick 229, class unknown, rank 0.2851, rank × low-exposure 0.0200.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AA | 17 | 0 | 4 | 1 |
| 2014 | AAA | 441 | 8 | 95 | 39 |
| 2014 | MLB | 18 | 0 | 6 | 1 |
| 2015 | AAA | 389 | 0 | 55 | 47 |
| 2015 | MLB | 87 | 2 | 12 | 9 |
| 2016 | AAA | 120 | 0 | 20 | 10 |
| 2016 | MLB | 257 | 3 | 50 | 34 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 253.58 | 0.6907 | — |
| pooled | 255.48 | 0.7261 | -0.2831 |
| pedigree | 250.75 | 0.6589 | -0.2066 |
| pooled_product | 255.48 | 0.6684 | — |
| pedigree_product | 250.75 | 0.6880 | — |
| safe_ridge | 250.75 | 0.7949 | 0.0492 |

Actual: 290 PA / 0.7284 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 250.7499069455521, "value": 0.6589115249340188, "rate": -0.20656429331666024}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The 257 current MLB PA, prior small MLB samples and AAA history support a utility-player expectation. The linear assembly gives 251 PA/0.79 versus 290/0.73. Taylor gets more opportunity and production, Asche fails, and La Stella remains part-time. This ordinary case is sensible and useful, not proof that jobs or injury risk are comprehensively modeled.

Peers selected without future outcomes: Michael A. Taylor (age 25, current MLB 237 PA, draft pick 172; actual next 432 PA / 1.96); Cody Asche (age 26, current MLB 218 PA, draft pick 151; actual next 62 PA / -0.66); Tommy La Stella (age 27, current MLB 169 PA, draft pick 266; actual next 151 PA / 1.02).

Training profile support: all=238 distinct people; active=190 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 63.20 | 337.40 | 0.2300 | 0.197074 |
| MLB / BB | 41.80 | 337.40 | 0.0800 | 0.113855 |
| MLB / HBP | 6.60 | 337.40 | 0.0100 | 0.017375 |
| MLB / HR | 4.60 | 337.40 | 0.0300 | 0.017375 |
| MLB / BABIP | 70.00 | 215.60 | 0.3000 | 0.316857 |
| MLB / 2B | 15.60 | 337.40 | 0.0500 | 0.047096 |
| MLB / 3B | 0.00 | 337.40 | 0.0050 | 0.001143 |
| AAA / K | 121.00 | 695.80 | 0.2300 | 0.180950 |
| AAA / BB | 71.00 | 695.80 | 0.0800 | 0.099271 |
| AAA / HBP | 12.60 | 695.80 | 0.0100 | 0.017090 |
| AAA / HR | 4.80 | 695.80 | 0.0300 | 0.009801 |
| AAA / BABIP | 163.20 | 473.40 | 0.3000 | 0.336938 |
| AAA / 2B | 26.40 | 695.80 | 0.0500 | 0.039457 |
| AAA / 3B | 4.40 | 695.80 | 0.0050 | 0.006157 |
| AA / K | 2.40 | 10.20 | 0.2300 | 0.230490 |
| AA / BB | 0.60 | 10.20 | 0.0800 | 0.078040 |
| AA / HBP | 0.00 | 10.20 | 0.0100 | 0.009074 |
| AA / HR | 0.00 | 10.20 | 0.0300 | 0.027223 |
| AA / BABIP | 3.00 | 7.20 | 0.3000 | 0.307836 |
| AA / 2B | 1.20 | 10.20 | 0.0500 | 0.056261 |
| AA / 3B | 0.00 | 10.20 | 0.0050 | 0.004537 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 257.21170 | 257.21170 | 0.00141 | 0.36170 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.13468 | -0.13468 |
| position_5 | 1.00000 | 1.00000 | 0.11943 | 0.11943 |
| on_40man | 1.00000 | 1.00000 | -0.11354 | -0.11354 |
| quality_present_1 | 1.00000 | 1.00000 | -0.10618 | -0.10618 |
| pooled_AAA_BABIP | 0.33694 | 0.36938 | 0.28102 | 0.10380 |
| pooled_mlb_quality | 0.15549 | 0.15549 | 0.66222 | 0.10297 |
| quality_present_2 | 1.00000 | 1.00000 | 0.10257 | 0.10257 |

Linear intercept: -0.585118. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Ronald Acuña Jr. — 2022 → 2023

Selection: pedigree largest harm vs repaired_direct.

Inputs: age 24, MLB PA 533/360/202, current observed quality 0.3847, pooled MLB quality 1.2286; captured listing 1 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 202 | 14 | 60 | 36 |
| 2021 | MLB | 360 | 24 | 85 | 47 |
| 2022 | AAA | 25 | 0 | 6 | 5 |
| 2022 | MLB | 533 | 15 | 126 | 49 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 513.40 | 3.3117 | — |
| pooled | 487.41 | 2.5596 | 1.8612 |
| pedigree | 489.77 | 2.3380 | 1.5508 |
| pooled_product | 487.41 | 3.0380 | — |
| pedigree_product | 489.77 | 2.7994 | — |
| safe_ridge | 489.77 | 3.2058 | 2.0488 |

Actual: 735 PA / 8.9605 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 489.7682247511178, "value": 2.3379630643272074, "rate": 1.5508235121185763}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Current 533 PA/15 HR follow stronger prior seasons; pooled quality preserves that evidence. The draft direct arm's 490 PA/2.34 is a largest-harm case, while the linear assembly recovers 3.21, still far below 735/8.96. Torres, Urias and Kirk have mixed opportunities and production. Neutralizing unknown draft inputs changes nothing in this probe: the miss cannot be attributed causally to an international-pedigree penalty. Recovery, workload and elite-ceiling forecasting remain weak.

Peers selected without future outcomes: Gleyber Torres (age 25, current MLB 572 PA, draft pick None; actual next 672 PA / 3.70); Luis Urías (age 25, current MLB 472 PA, draft pick None; actual next 177 PA / 0.22); Alejandro Kirk (age 23, current MLB 541 PA, draft pick None; actual next 422 PA / 0.98).

Training profile support: all=203 distinct people; active=179 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 230.00 | 942.20 | 0.2300 | 0.242756 |
| MLB / BB | 108.20 | 942.20 | 0.0800 | 0.111495 |
| MLB / HBP | 19.60 | 942.20 | 0.0100 | 0.019766 |
| MLB / HR | 42.60 | 942.20 | 0.0300 | 0.043754 |
| MLB / BABIP | 172.60 | 535.00 | 0.3000 | 0.319055 |
| MLB / 2B | 45.80 | 942.20 | 0.0500 | 0.048743 |
| MLB / 3B | 0.80 | 942.20 | 0.0050 | 0.001247 |
| AAA / K | 6.00 | 25.00 | 0.2300 | 0.232000 |
| AAA / BB | 5.00 | 25.00 | 0.0800 | 0.104000 |
| AAA / HBP | 0.00 | 25.00 | 0.0100 | 0.008000 |
| AAA / HR | 0.00 | 25.00 | 0.0300 | 0.024000 |
| AAA / BABIP | 7.00 | 13.00 | 0.3000 | 0.327434 |
| AAA / 2B | 1.00 | 25.00 | 0.0500 | 0.048000 |
| AAA / 3B | 0.00 | 25.00 | 0.0050 | 0.004000 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.22856 | 1.22856 | 0.72766 | 0.89397 |
| work_0 | 533.00000 | 533.00000 | 0.00086 | 0.45850 |
| age_centered | -0.60000 | -0.60000 | -0.56110 | 0.33666 |
| quality_1 | 1.12976 | 1.12976 | 0.25483 | 0.28789 |
| work_2 | 546.61470 | 546.61470 | 0.00044 | 0.24022 |
| work_1 | 360.14821 | 360.14821 | 0.00050 | 0.18113 |
| quality_0 | 0.38468 | 0.38468 | 0.41423 | 0.15935 |
| position_9 | 1.00000 | 1.00000 | 0.14593 | 0.14593 |

Linear intercept: -0.740135. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Miguel Andujar — 2018 → 2019

Selection: pedigree false high.

Inputs: age 23, MLB PA 606/8/0, current observed quality 0.7932, pooled MLB quality 0.8431; captured listing 1 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 319 | 2 | 42 | 21 |
| 2016 | Aplus | 251 | 10 | 30 | 18 |
| 2017 | AA | 272 | 7 | 38 | 12 |
| 2017 | AAA | 250 | 9 | 33 | 16 |
| 2017 | MLB | 8 | 0 | 0 | 1 |
| 2018 | MLB | 606 | 27 | 97 | 23 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 554.99 | 3.4343 | — |
| pooled | 586.47 | 3.5305 | 0.9715 |
| pedigree | 579.55 | 3.6047 | 0.9402 |
| pooled_product | 586.47 | 2.7552 | — |
| pedigree_product | 579.55 | 2.6924 | — |
| safe_ridge | 579.55 | 2.7234 | 0.9722 |

Actual: 49 PA / -0.6706 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 579.5494152178014, "value": 3.6046516464852973, "rate": 0.9401705709630959}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The model sees a successful 606-PA rookie season with 27 HR and good upper-minor history. The linear assembly gives 580 PA/2.72 versus 49/-0.67. Marte succeeds, Mazara is ordinary and Camargo gets less opportunity. This is a legitimate false high from good origin evidence; later injury or collapse must not be retrospectively inserted into the inputs. It is an uncertainty miss, not automatically a fixable talent-data error.

Peers selected without future outcomes: Johan Camargo (age 24, current MLB 524 PA, draft pick None; actual next 248 PA / -0.13); Ketel Marte (age 24, current MLB 580 PA, draft pick None; actual next 628 PA / 6.54); Nomar Mazara (age 23, current MLB 536 PA, draft pick None; actual next 469 PA / 1.77).

Training profile support: all=148 distinct people; active=132 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 97.00 | 612.40 | 0.2300 | 0.168445 |
| MLB / BB | 23.80 | 612.40 | 0.0800 | 0.044638 |
| MLB / HBP | 4.00 | 612.40 | 0.0100 | 0.007019 |
| MLB / HR | 27.00 | 612.40 | 0.0300 | 0.042111 |
| MLB / BABIP | 146.20 | 458.60 | 0.3000 | 0.315431 |
| MLB / 2B | 48.60 | 612.40 | 0.0500 | 0.075239 |
| MLB / 3B | 2.00 | 612.40 | 0.0050 | 0.003509 |
| AAA / K | 26.40 | 200.00 | 0.2300 | 0.164667 |
| AAA / BB | 12.80 | 200.00 | 0.0800 | 0.069333 |
| AAA / HBP | 1.60 | 200.00 | 0.0100 | 0.008667 |
| AAA / HR | 7.20 | 200.00 | 0.0300 | 0.034000 |
| AAA / BABIP | 50.40 | 151.20 | 0.3000 | 0.320064 |
| AAA / 2B | 10.40 | 200.00 | 0.0500 | 0.051333 |
| AAA / 3B | 0.80 | 200.00 | 0.0050 | 0.004333 |
| AA / K | 55.60 | 409.00 | 0.2300 | 0.154420 |
| AA / BB | 22.20 | 409.00 | 0.0800 | 0.059332 |
| AA / HBP | 5.80 | 409.00 | 0.0100 | 0.013360 |
| AA / HR | 6.80 | 409.00 | 0.0300 | 0.019253 |
| AA / BABIP | 101.40 | 318.60 | 0.3000 | 0.313903 |
| AA / 2B | 28.00 | 409.00 | 0.0500 | 0.064833 |
| AA / 3B | 2.00 | 409.00 | 0.0050 | 0.004912 |
| Aplus / K | 18.00 | 150.60 | 0.2300 | 0.163607 |
| Aplus / BB | 10.80 | 150.60 | 0.0800 | 0.075020 |
| Aplus / HBP | 1.80 | 150.60 | 0.0100 | 0.011173 |
| Aplus / HR | 6.00 | 150.60 | 0.0300 | 0.035914 |
| Aplus / BABIP | 33.00 | 114.00 | 0.3000 | 0.294393 |
| Aplus / 2B | 6.00 | 150.60 | 0.0500 | 0.043895 |
| Aplus / 3B | 1.20 | 150.60 | 0.0050 | 0.006784 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.84314 | 0.84314 | 0.70786 | 0.59682 |
| work_0 | 605.75072 | 605.75072 | 0.00085 | 0.51281 |
| age_centered | -0.80000 | -0.80000 | -0.51190 | 0.40952 |
| quality_0 | 0.79325 | 0.79325 | 0.47717 | 0.37851 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.19539 | -0.19539 |
| position_5 | 1.00000 | 1.00000 | 0.18207 | 0.18207 |
| pooled_AA_K | 0.15442 | -0.75580 | 0.17582 | -0.13289 |
| pooled_AAA_K | 0.16467 | -0.65333 | 0.12902 | -0.08429 |

Linear intercept: -0.725489. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Mike Yastrzemski — 2022 → 2023

Selection: pedigree ordinary partial workload.

Inputs: age 31, MLB PA 558/532/225, current observed quality -0.0317, pooled MLB quality 0.3238; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 429, class unknown, rank 0.2025, rank × low-exposure 0.0143.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 225 | 10 | 55 | 28 |
| 2021 | MLB | 532 | 25 | 131 | 47 |
| 2022 | MLB | 558 | 17 | 141 | 61 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 447.90 | 1.8075 | — |
| pooled | 445.77 | 1.6009 | 0.3414 |
| pedigree | 442.35 | 1.5577 | 0.3721 |
| pooled_product | 445.77 | 1.6494 | — |
| pedigree_product | 442.35 | 1.6593 | — |
| safe_ridge | 442.35 | 1.6786 | 0.3983 |

Actual: 381 PA / 1.5566 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 442.34698675006024, "value": 1.5577369773929737, "rate": 0.37209200501030215}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Age 31, 558 current PA/17 HR and stronger previous power seasons produce 442 PA/1.68 in the linear assembly versus 381/1.56. Voit loses opportunity while Brown and Farmer remain part-time. The combination of age regression and retained history gives a sensible ordinary result, though workload is not exact.

Peers selected without future outcomes: Luke Voit (age 31, current MLB 568 PA, draft pick 665; actual next 74 PA / -0.18); Seth Brown (age 29, current MLB 555 PA, draft pick 578; actual next 378 PA / 0.52); Kyle Farmer (age 31, current MLB 583 PA, draft pick 244; actual next 369 PA / 1.11).

Training profile support: all=153 distinct people; active=120 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 278.80 | 1118.60 | 0.2300 | 0.247661 |
| MLB / BB | 115.40 | 1118.60 | 0.0800 | 0.101264 |
| MLB / HBP | 14.00 | 1118.60 | 0.0100 | 0.012309 |
| MLB / HR | 43.00 | 1118.60 | 0.0300 | 0.037748 |
| MLB / BABIP | 179.20 | 661.20 | 0.3000 | 0.274829 |
| MLB / 2B | 61.80 | 1118.60 | 0.0500 | 0.054817 |
| MLB / 3B | 6.80 | 1118.60 | 0.0050 | 0.005990 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 558.00000 | 558.00000 | 0.00093 | 0.51916 |
| age_centered | 0.80000 | 0.80000 | -0.52755 | -0.42204 |
| work_2 | 608.85301 | 608.85301 | 0.00063 | 0.38115 |
| pooled_mlb_quality | 0.32377 | 0.32377 | 0.77718 | 0.25163 |
| work_1 | 532.21902 | 532.21902 | 0.00039 | 0.20905 |
| position_9 | 1.00000 | 1.00000 | 0.18532 | 0.18532 |
| quality_present_1 | 1.00000 | 1.00000 | 0.15163 | 0.15163 |
| quality_2 | 0.67451 | 0.67451 | 0.19875 | 0.13406 |

Linear intercept: -0.785700. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Aaron Judge — 2023 → 2024

Selection: pooled_product largest harm vs repaired_direct; pedigree_product largest harm vs repaired_direct.

Inputs: age 31, MLB PA 458/696/633, current observed quality 1.3171, pooled MLB quality 2.7916; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 32, class unknown, rank 0.5440, rank × low-exposure 0.0288.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 633 | 39 | 158 | 73 |
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 524.98 | 5.5013 | — |
| pooled | 549.77 | 5.3481 | 3.0483 |
| pedigree | 552.29 | 5.4185 | 3.1522 |
| pooled_product | 549.77 | 4.4952 | — |
| pedigree_product | 552.29 | 4.6115 | — |
| safe_ridge | 552.29 | 4.8145 | 3.3727 |

Actual: 704 PA / 11.0661 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 550.9503222469642, "value": 5.302621649987646, "rate": 3.127895558156688}. Artificial input probe, not a causal effect or independently validated replacement forecast.

An injury-shortened 458-PA season with 37 HR follows 696 PA/62 HR and 633/39. The linear assembly gives 552 PA/4.81 versus 704/11.07, among the largest product-assembly harms. His positive grade is not absurd; both recovery volume and elite ceiling remain understated. Seager, Murphy and Grichuk illustrate varied outcomes but are imperfect analogues to this rare elite hitter. No peer set or retrospective manual boost makes the breakout certain.

Peers selected without future outcomes: Corey Seager (age 29, current MLB 536 PA, draft pick 18; actual next 533 PA / 3.78); Sean Murphy (age 28, current MLB 438 PA, draft pick 83; actual next 264 PA / 0.21); Randal Grichuk (age 31, current MLB 471 PA, draft pick 24; actual next 279 PA / 2.35).

Training profile support: all=187 distinct people; active=143 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 364.80 | 1394.60 | 0.2300 | 0.259467 |
| MLB / BB | 196.40 | 1394.60 | 0.0800 | 0.136759 |
| MLB / HBP | 6.60 | 1394.60 | 0.0100 | 0.005085 |
| MLB / HR | 110.00 | 1394.60 | 0.0300 | 0.075606 |
| MLB / BABIP | 224.40 | 688.20 | 0.3000 | 0.322761 |
| MLB / 2B | 52.80 | 1394.60 | 0.0500 | 0.038673 |
| MLB / 3B | 0.00 | 1394.60 | 0.0050 | 0.000335 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 2.79156 | 2.79156 | 0.73110 | 2.04092 |
| quality_0 | 1.31713 | 1.31713 | 0.45039 | 0.59322 |
| quality_1 | 2.40833 | 2.40833 | 0.22148 | 0.53340 |
| age_centered | 0.80000 | 0.80000 | -0.55739 | -0.44591 |
| work_0 | 458.00000 | 458.00000 | 0.00091 | 0.41530 |
| work_2 | 633.26060 | 633.26060 | 0.00057 | 0.35832 |
| work_1 | 696.00000 | 696.00000 | 0.00048 | 0.33640 |
| quality_2 | 1.27862 | 1.27862 | 0.18723 | 0.23940 |

Linear intercept: -0.812532. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Ezequiel Duran — 2021 → 2022

Selection: pooled_product ordinary partial workload.

Inputs: age 22, MLB PA 0/0/0, current observed quality 0.0000, pooled MLB quality 0.0000; captured listing 1 (not certified rights). Draft known 0, year None, pick None, class unknown, rank 0.0000, rank × low-exposure 0.0000.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | Aminus | 277 | 13 | 77 | 24 |
| 2021 | Aplus | 471 | 19 | 130 | 37 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 64.86 | 0.1721 | — |
| pooled | 70.18 | 0.1140 | -0.0969 |
| pedigree | 68.77 | 0.1109 | -0.1593 |
| pooled_product | 70.18 | 0.2087 | — |
| pedigree_product | 68.77 | 0.1973 | — |
| safe_ridge | 68.77 | 0.1548 | -0.5299 |

Actual: 220 PA / 0.2083 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 68.765406069169, "value": 0.11090758337950232, "rate": -0.15930574591455407}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The model sees A+ 471 PA/19 HR, earlier short-season production and a canceled 2020 minor season, with no MLB debut. The linear assembly gives 69 PA/0.15 versus 220/0.21. The near contribution masks too little opportunity. Mendoza, Sanchez and Chaparro all fail to arrive next year; only 20 active training people share the coarse profile. Do not convert one advancing player's success into certainty for the entire class.

Peers selected without future outcomes: Harvin Mendoza (age 22, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Lolo Sanchez (age 22, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00); Andrés Chaparro (age 22, current MLB 0 PA, draft pick None; actual next 0 PA / 0.00).

Training profile support: all=2028 distinct people; active=20 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| Aplus / K | 130.00 | 471.00 | 0.2300 | 0.267951 |
| Aplus / BB | 37.00 | 471.00 | 0.0800 | 0.078809 |
| Aplus / HBP | 10.00 | 471.00 | 0.0100 | 0.019264 |
| Aplus / HR | 19.00 | 471.00 | 0.0300 | 0.038529 |
| Aplus / BABIP | 92.00 | 272.00 | 0.3000 | 0.327957 |
| Aplus / 2B | 22.00 | 471.00 | 0.0500 | 0.047285 |
| Aplus / 3B | 6.00 | 471.00 | 0.0050 | 0.011384 |
| Aminus / K | 46.20 | 166.20 | 0.2300 | 0.259955 |
| Aminus / BB | 14.40 | 166.20 | 0.0800 | 0.084147 |
| Aminus / HBP | 1.80 | 166.20 | 0.0100 | 0.010518 |
| Aminus / HR | 7.80 | 166.20 | 0.0300 | 0.040571 |
| Aminus / BABIP | 30.00 | 95.40 | 0.3000 | 0.307062 |
| Aminus / 2B | 7.20 | 166.20 | 0.0500 | 0.045830 |
| Aminus / 3B | 2.40 | 166.20 | 0.0050 | 0.010894 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.00000 | -1.00000 | -0.50613 | 0.50613 |
| position_6 | 1.00000 | 1.00000 | -0.28210 | -0.28210 |
| pooled_Aplus_pa | 471.00000 | 0.78500 | -0.14731 | -0.11564 |
| pooled_Aplus_BABIP | 0.32796 | 0.27957 | 0.36278 | 0.10142 |
| Aplus_0_pa | 471.00000 | 0.78500 | -0.07018 | -0.05509 |
| on_40man | 1.00000 | 1.00000 | -0.04303 | -0.04303 |
| age_squared | 1.00000 | 1.00000 | 0.03579 | 0.03579 |
| pooled_Aplus_K | 0.26795 | 0.37951 | -0.09223 | -0.03500 |

Linear intercept: -0.679520. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Enrique Hernández — 2016 → 2017

Selection: pedigree_product ordinary partial workload.

Inputs: age 24, MLB PA 244/218/134, current observed quality -0.3897, pooled MLB quality -0.0394; captured listing 1 (not certified rights). Draft known 1, year 2009, pick 191, class HS, rank 0.3090, rank × low-exposure 0.0257.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AA | 43 | 1 | 3 | 3 |
| 2014 | AAA | 373 | 10 | 38 | 27 |
| 2014 | MLB | 134 | 3 | 21 | 12 |
| 2015 | AAA | 64 | 1 | 14 | 4 |
| 2015 | MLB | 218 | 7 | 46 | 11 |
| 2016 | AA | 9 | 0 | 3 | 1 |
| 2016 | Aplus | 10 | 0 | 3 | 2 |
| 2016 | MLB | 244 | 7 | 64 | 27 |
| 2016 | RK121 | 8 | 0 | 0 | 0 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 219.74 | 0.7672 | — |
| pooled | 230.45 | 0.4040 | -0.0142 |
| pedigree | 227.76 | 0.3819 | 0.1528 |
| pooled_product | 230.45 | 0.7062 | — |
| pedigree_product | 227.76 | 0.7613 | — |
| safe_ridge | 227.76 | 0.7858 | 0.2172 |

Actual: 342 PA / 0.7635 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 227.76333254653764, "value": 0.3818582775371525, "rate": -0.09826705097571761}. Artificial input probe, not a causal effect or independently validated replacement forecast.

The history contains three MLB seasons with modest PA and uneven batting. The linear assembly's 228 PA/0.79 nearly matches actual contribution 0.76 but misses 342 PA. Altherr succeeds, Brown does not play and Mallex Smith is part-time. Retaining earlier batting evidence makes a plausible utility contribution estimate; the value agreement is not exact opportunity accuracy.

Peers selected without future outcomes: Aaron Altherr (age 25, current MLB 227 PA, draft pick 287; actual next 412 PA / 2.65); Trevor Brown (age 24, current MLB 184 PA, draft pick 328; actual next 0 PA / 0.00); Mallex Smith (age 23, current MLB 215 PA, draft pick 165; actual next 282 PA / 0.41).

Training profile support: all=177 distinct people; active=152 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 113.40 | 498.80 | 0.2300 | 0.227789 |
| MLB / BB | 43.00 | 498.80 | 0.0800 | 0.085170 |
| MLB / HBP | 2.20 | 498.80 | 0.0100 | 0.005344 |
| MLB / HR | 14.40 | 498.80 | 0.0300 | 0.029058 |
| MLB / BABIP | 94.20 | 324.00 | 0.3000 | 0.292925 |
| MLB / 2B | 21.20 | 498.80 | 0.0500 | 0.043754 |
| MLB / 3B | 3.40 | 498.80 | 0.0050 | 0.006513 |
| AAA / K | 34.00 | 275.00 | 0.2300 | 0.152000 |
| AAA / BB | 19.40 | 275.00 | 0.0800 | 0.073067 |
| AAA / HBP | 1.80 | 275.00 | 0.0100 | 0.007467 |
| AAA / HR | 6.80 | 275.00 | 0.0300 | 0.026133 |
| AAA / BABIP | 65.40 | 211.20 | 0.3000 | 0.306555 |
| AAA / 2B | 14.80 | 275.00 | 0.0500 | 0.052800 |
| AAA / 3B | 1.20 | 275.00 | 0.0050 | 0.004533 |
| AA / K | 4.80 | 34.80 | 0.2300 | 0.206231 |
| AA / BB | 2.80 | 34.80 | 0.0800 | 0.080119 |
| AA / HBP | 0.00 | 34.80 | 0.0100 | 0.007418 |
| AA / HR | 0.60 | 34.80 | 0.0300 | 0.026706 |
| AA / BABIP | 7.20 | 26.60 | 0.3000 | 0.293839 |
| AA / 2B | 1.80 | 34.80 | 0.0500 | 0.050445 |
| AA / 3B | 0.00 | 34.80 | 0.0050 | 0.003709 |
| Aplus / K | 3.00 | 10.00 | 0.2300 | 0.236364 |
| Aplus / BB | 2.00 | 10.00 | 0.0800 | 0.090909 |
| Aplus / HBP | 0.00 | 10.00 | 0.0100 | 0.009091 |
| Aplus / HR | 0.00 | 10.00 | 0.0300 | 0.027273 |
| Aplus / BABIP | 3.00 | 5.00 | 0.3000 | 0.314286 |
| Aplus / 2B | 1.00 | 10.00 | 0.0500 | 0.054545 |
| Aplus / 3B | 0.00 | 10.00 | 0.0050 | 0.004545 |
| RK121 / K | 0.00 | 8.00 | 0.2300 | 0.212963 |
| RK121 / BB | 0.00 | 8.00 | 0.0800 | 0.074074 |
| RK121 / HBP | 0.00 | 8.00 | 0.0100 | 0.009259 |
| RK121 / HR | 0.00 | 8.00 | 0.0300 | 0.027778 |
| RK121 / BABIP | 0.00 | 8.00 | 0.3000 | 0.277778 |
| RK121 / 2B | 0.00 | 8.00 | 0.0500 | 0.046296 |
| RK121 / 3B | 0.00 | 8.00 | 0.0050 | 0.004630 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.52557 | 0.31534 |
| work_0 | 244.20099 | 244.20099 | 0.00070 | 0.17147 |
| quality_0 | -0.38966 | -0.38966 | 0.42123 | -0.16414 |
| quality_present_2 | 1.00000 | 1.00000 | 0.13901 | 0.13901 |
| pooled_AAA_K | 0.15200 | -0.78000 | 0.16689 | -0.13017 |
| draft_known | 1.00000 | 1.00000 | 0.11400 | 0.11400 |
| quality_1 | 0.35960 | 0.35960 | 0.28578 | 0.10277 |
| work_2 | 134.00000 | 134.00000 | 0.00060 | 0.08022 |

Linear intercept: -0.583470. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Rhys Hoskins — 2024 → 2025

Selection: safe_ridge ordinary partial workload.

Inputs: age 31, MLB PA 517/0/672, current observed quality 0.0400, pooled MLB quality 0.3702; captured listing 1 (not certified rights). Draft known 1, year 2014, pick 142, class unknown, rank 0.3480, rank × low-exposure 0.0270.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 672 | 30 | 169 | 72 |
| 2024 | MLB | 517 | 26 | 149 | 52 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 355.52 | 1.1325 | — |
| pooled | 392.70 | 1.1348 | 0.0529 |
| pedigree | 391.56 | 1.0394 | 0.0946 |
| pooled_product | 392.70 | 1.2615 | — |
| pedigree_product | 391.56 | 1.2851 | — |
| safe_ridge | 391.56 | 1.3337 | 0.1692 |

Actual: 328 PA / 1.3336 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 390.0054950040149, "value": 1.0393715860021515, "rate": 0.2128177855050283}. Artificial input probe, not a causal effect or independently validated replacement forecast.

A 517-PA/26-HR return season and earlier 672 PA/30 HR remain known despite an intervening empty season. The linear assembly gives 392 PA/1.33 versus 328/1.33. This is an ordinary near-correct contribution, not perfect workload. DeJong, O'Hearn and Kiner-Falefa diverge. Unlike McLain's pre-return cutoff, Hoskins has already demonstrated renewed playing time, a meaningful baseball distinction.

Peers selected without future outcomes: Paul DeJong (age 30, current MLB 482 PA, draft pick 131; actual next 208 PA / 0.07); Ryan O'Hearn (age 30, current MLB 494 PA, draft pick 243; actual next 544 PA / 3.32); Isiah Kiner-Falefa (age 29, current MLB 496 PA, draft pick 130; actual next 459 PA / 0.11).

Training profile support: all=215 distinct people; active=172 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 250.40 | 920.20 | 0.2300 | 0.267987 |
| MLB / BB | 95.20 | 920.20 | 0.0800 | 0.101157 |
| MLB / HBP | 10.60 | 920.20 | 0.0100 | 0.011370 |
| MLB / HR | 44.00 | 920.20 | 0.0300 | 0.046069 |
| MLB / BABIP | 139.00 | 516.40 | 0.3000 | 0.274173 |
| MLB / 2B | 33.80 | 920.20 | 0.0500 | 0.038032 |
| MLB / 3B | 1.20 | 920.20 | 0.0050 | 0.001666 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_2 | 672.00000 | 672.00000 | 0.00089 | 0.59706 |
| work_0 | 517.21284 | 517.21284 | 0.00104 | 0.53660 |
| age_centered | 0.80000 | 0.80000 | -0.54689 | -0.43751 |
| pooled_mlb_quality | 0.37016 | 0.37016 | 0.76099 | 0.28169 |
| reorganized | 1.00000 | 1.00000 | -0.19849 | -0.19849 |
| quality_2 | 0.63759 | 0.63759 | 0.19455 | 0.12405 |
| position_3 | 1.00000 | 1.00000 | 0.11692 | 0.11692 |
| prior_debut | 1.00000 | 1.00000 | 0.08700 | 0.08700 |

Linear intercept: -0.837910. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

### Aaron Judge — 2024 → 2025

Selection: largest absolute fixed-scale linear rate.

Inputs: age 32, MLB PA 704/458/696, current observed quality 2.7944, pooled MLB quality 3.6486; captured listing 1 (not certified rights). Draft known 1, year 2013, pick 32, class unknown, rank 0.5440, rank × low-exposure 0.0278.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

| Model | Expected PA | Expected batting + replacement | Weighted conditional rate* |
|---|---:|---:|---:|
| repaired_direct | 587.01 | 5.2151 | — |
| pooled | 539.29 | 4.9011 | 3.1030 |
| pedigree | 534.27 | 4.7975 | 2.9510 |
| pooled_product | 539.29 | 4.4738 | — |
| pedigree_product | 534.27 | 4.2969 | — |
| safe_ridge | 534.27 | 5.6778 | 4.5018 |

Actual: 679 PA / 9.2310 batting-plus-replacement wins. *Rate is conditional on future activity and contribution weighted; it is not a current prospect grade.

Saved-fit unknown-pedigree probe: {"pa": 532.9470225063891, "value": 4.7991959883146, "rate": 2.9519894777408404}. Artificial input probe, not a causal effect or independently validated replacement forecast.

Current 704 PA/58 HR and the prior 37/62-HR seasons yield the largest linear rate, 4.5018 batting wins above average per 600 PA. Positive pooled and current quality terms support this finite estimate; it is not the earlier rare-league scaling explosion. The linear assembly gives 534 PA/5.68 versus 679/9.23, still materially conservative. Rooker, Lindor and Schwarber retain large workloads. Known elite performance is retained, but expected availability and peak shrinkage leave an important false-low tail.

Peers selected without future outcomes: Brent Rooker (age 29, current MLB 614 PA, draft pick 35; actual next 699 PA / 4.20); Francisco Lindor (age 30, current MLB 689 PA, draft pick 8; actual next 732 PA / 4.59); Kyle Schwarber (age 31, current MLB 692 PA, draft pick 4; actual next 724 PA / 6.83).

Training profile support: all=217 distinct people; active=168 distinct people.

Actual pooled transformations (weighted count + 100 × prior)/(weighted opportunities + 100):

| League / event | Weighted events | Weighted opportunities | Prior | Actual input |
|---|---:|---:|---:|---:|
| MLB / K | 380.00 | 1488.00 | 0.2300 | 0.253778 |
| MLB / BB | 231.40 | 1488.00 | 0.0800 | 0.150756 |
| MLB / HBP | 12.60 | 1488.00 | 0.0100 | 0.008564 |
| MLB / HR | 124.80 | 1488.00 | 0.0300 | 0.080479 |
| MLB / BABIP | 239.80 | 697.20 | 0.3000 | 0.338435 |
| MLB / 2B | 65.60 | 1488.00 | 0.0500 | 0.044458 |
| MLB / 3B | 1.00 | 1488.00 | 0.0050 | 0.000945 |

Largest saved linear contributions (fixed physical scales, not learned tiny SD):

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 3.64857 | 3.64857 | 0.72882 | 2.65915 |
| quality_0 | 2.79442 | 2.79442 | 0.47428 | 1.32535 |
| work_0 | 704.28983 | 704.28983 | 0.00089 | 0.62894 |
| age_centered | 1.00000 | 1.00000 | -0.54491 | -0.54491 |
| quality_2 | 2.40833 | 2.40833 | 0.20772 | 0.50027 |
| work_2 | 696.00000 | 696.00000 | 0.00051 | 0.35557 |
| quality_1 | 1.31713 | 1.31713 | 0.22052 | 0.29045 |
| reorganized | 1.00000 | 1.00000 | -0.26920 | -0.26920 |

Linear intercept: -0.827880. Full feature vectors and source/fit paths are in the machine-readable cases. No changed model parameters in the diagnostic probe.

## Disposition

Working research baseline only: corrected draft-context expected PA multiplied by PA-weighted fixed-scale linear batting plus origin replacement yield. Keep pooled-only and corrected direct controls visible. Do not deploy over the frozen 2026 forecast, call the conditional rate a current prospect grade, claim independent pedigree validation, or present next-year contribution as career/trade value. V31/V32 remain qualified; interrupted V33 remains preserved. The practical-model goal is active and not achieved yet.

Do not launch another model-library tournament. First repair the meaning of temporary absence versus definitive exit using dated source facts, and reconstruct a complete 2020-origin cohort with explicit missing-source flags before using that origin. Then test one predeclared opportunity/reliability assembly aimed at upper-minor arrivals and brief MLB debuts, with Olson/McNeil/Steer/Winn/Kurtz/Tatis and unsuccessful origin-only peers as mandatory checks. Evaluate workload, batting rate and delivered value separately; preserve mature whole-player chronological folds, old/public benchmarks, all non-arrivals, and the protected 2026 outcomes.

315 saved heads replay, including 135 reused identical early heads and 180 new fits. Input hashes and every evaluation target/identity stay fixed. Unit/source checks and completed player review are separate from predictive success and deployment approval.
