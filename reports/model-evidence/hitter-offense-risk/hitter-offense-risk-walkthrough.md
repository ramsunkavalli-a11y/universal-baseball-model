# Player checks for next year offense ranges

Seventeen historical player checks trace actual source statistics, current point forecasts,
nested calibration and new offense ranges. These forecasts use information available at
the end of the stated origin season plus the documented following preseason information
date, and predict the following calendar year. No 2026 outcomes are used.

All offense numbers below are custom fixed-event batting plus replacement wins, not full WAR.
Hit/600 is the current hitting-rate forecast. For active observed players the actual rate
uses the common-origin environment; an inactive player has no observed hitting rate.
The three distributions have the same mean. The table shows their P10, median and P90.

Cases include nine fixed players, score gains and harms, false highs/lows, an ordinary
final-value case with compensating errors, and the largest physical-tail failure.
Complete model inputs, additive Ridge contributions, opportunity tree paths, calibration
paths, per-PA probability mass and independent scalar quantiles are saved in
[the reviewed evidence](../reports/model-evidence/hitter-offense-risk/reviewed-cases.json).

## Aaron Judge after 2024

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 696 | 62 | 92 | 175 |
| 2023 | MLB | 458 | 37 | 79 | 130 |
| 2024 | MLB | 704 | 58 | 113 | 171 |

Current forecast: 99.07% chance of any MLB PA, 535.74 PA conditional on appearing, 530.75 expected PA, +4.534 Hit/600 and +5.668 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +3.364 | +5.895 | +7.689 |
| Constant hitting spread | +0.144 | +5.252 | +11.818 |
| Sample dependent spread | +2.888 | +5.670 | +8.455 |

Reality: 679 MLB PA, +6.427 actual Hit/600 and +9.393 delivered offense.

Calibration: 177 distinct earlier active players; 19 share the refined origin-known profile. Rate variance is 0.6303 + 1.4742 times 600/PA; the constant reference variance is 21.8654. The uncentered nested residual bias is -1.589. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.922; its largest signed input contributions are pooled_mlb_quality +2.683, quality_0 +1.300, work_0 +0.845, age_centered -0.541, quality_2 +0.479, work_2 +0.433. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 0.02%; probability of at least two custom offense wins is 95.68%. Impossible conditional PA/offense probability is 0.00%.

Judge's 62, 37 and 58 HR across three MLB seasons feed the pooled/current quality terms that dominate his saved Ridge rate. This test does not change the 531 expected PA or +4.534 hitting rate. Adding sample-dependent spread raises P90 offense from 7.69 to 8.45, still short of 9.39 actual; constant spread reaches 11.82 but has much worse population sharpness. This is a persistent upper-tail miss, not a repaired superstar forecast. The 19 refined calibration people are not 19 Judge-equivalent hitters. The selected Ohtani/Freeman/Betts/Alvarez peers retain a short-workload outcome and are broad talent controls, not matched body size or injury histories.

Origin-selected comparisons: Shohei Ohtani: 727 subsequent PA, +8.05 offense; Freddie Freeman: 627 subsequent PA, +4.93 offense; Mookie Betts: 663 subsequent PA, +2.56 offense; Yordan Alvarez: 199 subsequent PA, +0.97 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Juan Soto after 2023

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 654 | 29 | 122 | 93 |
| 2022 | MLB | 664 | 27 | 129 | 96 |
| 2023 | MLB | 708 | 35 | 121 | 129 |

Current forecast: 99.31% chance of any MLB PA, 638.36 PA conditional on appearing, 633.93 expected PA, +3.941 Hit/600 and +6.126 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +4.271 | +6.465 | +7.518 |
| Constant hitting spread | +0.324 | +5.875 | +12.288 |
| Sample dependent spread | +3.620 | +6.173 | +8.590 |

Reality: 713 MLB PA, +5.044 actual Hit/600 and +8.201 delivered offense.

Calibration: 188 distinct earlier active players; 4 share the refined origin-known profile. Rate variance is 0.6060 + 1.2056 times 600/PA; the constant reference variance is 17.2274. The uncentered nested residual bias is -1.078. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.809; its largest signed input contributions are pooled_mlb_quality +1.595, work_0 +1.110, quality_0 +0.497, quality_2 +0.458, work_2 +0.447, age_centered +0.314. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 0.01%; probability of at least two custom offense wins is 97.98%. Impossible conditional PA/offense probability is 0.00%.

Soto's sustained walks and HR make pooled MLB quality the largest rate contribution. Sample-dependent spread gives 3.62 to 8.59 custom offense versus 8.20 actual, with little negative-offense probability; the constant spread's 0.32 to 12.29 is much broader. The 634 expected PA and 3.941 rate remain unchanged. This is a useful range example, not evidence that all superstar risks are calibrated: only four people share the refined calibration profile, and the outcome-selected success is not independent validation. Acuna, Guerrero, Riley and Carroll peers include both a short season and strong seasons.

Origin-selected comparisons: Ronald Acuña Jr.: 222 subsequent PA, +0.78 offense; Vladimir Guerrero Jr.: 697 subsequent PA, +6.37 offense; Austin Riley: 469 subsequent PA, +2.21 offense; Corbin Carroll: 684 subsequent PA, +2.43 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Nick Kurtz after 2024

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 10 | 7 |
| 2024 | AA | 15 | 0 | 2 | 3 |

Current forecast: 6.06% chance of any MLB PA, 168.16 PA conditional on appearing, 10.18 expected PA, -0.063 Hit/600 and +0.031 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.000 | +0.000 |
| Constant hitting spread | +0.000 | +0.000 | +0.000 |
| Sample dependent spread | +0.000 | +0.000 | +0.000 |

Reality: 489 MLB PA, +5.289 actual Hit/600 and +5.838 delivered offense.

Calibration: 186 distinct earlier active players; 0 share the refined origin-known profile. Rate variance is 0.7013 + 1.2553 times 600/PA; the constant reference variance is 14.2652. The uncentered nested residual bias is -1.137. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.985; its largest signed input contributions are age_centered +0.619, reorganized -0.263, draft_rank +0.165, position_3 +0.135, age_squared +0.078, absence_window_scaled -0.061. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 1.47%; probability of at least two custom offense wins is 0.29%. Impossible conditional PA/offense probability is 0.02%.

Kurtz had only 50 A/AA PA, but was a fourth overall college pick with known prospect ranking; this is not a newly discovered missing-pedigree case. The current rate fit receives those inputs, with age and draft rank positive contributions, yet shrinks to -0.063. The appearance model remains 6.06 percent and 10 expected PA. The zero atom therefore contains P10, median and P90 even after hitting spread is added. His actual 489 PA and 5.84 custom offense remain a major readiness and talent miss. There are zero refined calibration analogues. The mechanical closest peers include unranked Ariza/Avila/Chevalier and catcher Quero, not comparable elite college picks; their zero MLB outcomes cannot explain away Kurtz.

Origin-selected comparisons: Luis Ariza: 0 subsequent PA, +0.00 offense; Carlos Avila: 0 subsequent PA, +0.00 offense; Luis Chevalier: 0 subsequent PA, +0.00 offense; Jeferson Quero: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Wyatt Langford after 2023

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 11 | 7 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 1 | 3 |

Current forecast: 59.91% chance of any MLB PA, 358.74 PA conditional on appearing, 214.92 expected PA, +0.688 Hit/600 and +0.912 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.823 | +2.219 |
| Constant hitting spread | -0.411 | +0.000 | +3.615 |
| Sample dependent spread | +0.000 | +0.354 | +2.698 |

Reality: 557 MLB PA, +0.077 actual Hit/600 and +1.796 delivered offense.

Calibration: 176 distinct earlier active players; 0 share the refined origin-known profile. Rate variance is 0.9752 + 1.1369 times 600/PA; the constant reference variance is 12.4060. The uncentered nested residual bias is -1.030. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.903; its largest signed input contributions are age_centered +0.674, reorganized -0.191, position_7 +0.187, draft_college +0.161, pooled_AAA_BB +0.102, age_squared +0.099. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 4.84%; probability of at least two custom offense wins is 18.72%. Impossible conditional PA/offense probability is 0.00%.

Langford's 200 professional PA include 80 AA/AAA PA and ten HR. Age, college pedigree and upper-level walk evidence contribute to the 0.688 rate, but expected PA remains only 215 versus 557 actual. The sample-dependent median falls from 0.82 to 0.35 as positive-workload negative batting outcomes put more probability below the zero atom; P90 rises from 2.22 to 2.70. Actual offense 1.80 was already inside the workload-only range, so added spread worsens his quantile score. This is a real tradeoff, not a reason to tune his width. Refined support is zero; Crews and three non-arrivals keep timing variation visible.

Origin-selected comparisons: Dylan Crews: 132 subsequent PA, +0.02 offense; Colson Montgomery: 0 subsequent PA, +0.00 offense; Chase DeLauter: 0 subsequent PA, +0.00 offense; Kyle Teel: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Pete Alonso after 2018

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 123 | 5 | 11 | 22 |
| 2017 | AA | 47 | 2 | 2 | 7 |
| 2017 | Aplus | 346 | 16 | 24 | 64 |
| 2018 | AA | 273 | 15 | 40 | 50 |
| 2018 | AAA | 301 | 21 | 33 | 78 |

Current forecast: 80.36% chance of any MLB PA, 267.58 PA conditional on appearing, 215.03 expected PA, +0.286 Hit/600 and +0.765 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.708 | +1.633 |
| Constant hitting spread | -0.985 | +0.218 | +3.253 |
| Sample dependent spread | -0.063 | +0.508 | +2.138 |

Reality: 693 MLB PA, +3.865 actual Hit/600 and +6.598 delivered offense.

Calibration: 180 distinct earlier active players; 0 share the refined origin-known profile. Rate variance is 0.9751 + 1.0939 times 600/PA; the constant reference variance is 17.0620. The uncentered nested residual bias is -0.787. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.668; its largest signed input contributions are age_centered +0.415, position_3 +0.174, draft_known +0.155, draft_class_unknown -0.139, pooled_AAA_HR +0.123, pooled_AA_BB +0.092. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 11.85%; probability of at least two custom offense wins is 11.74%. Impossible conditional PA/offense probability is 0.02%.

Alonso's 574 AA/AAA PA and 36 HR are present; upper-level HR and walk inputs contribute positively, but the current rate is only 0.286 and expected PA 215. Sample-dependent P90 rises from 1.63 to 2.14, still far below 6.60 actual over 693 PA. The broader constant range is closer for this case but is worse overall. Variance cannot replace a better hitting/regular-workload center. Zero refined calibration support qualifies the specific risk estimate. Thaiss and Rooker/Craig/Lester are broad same-position controls, not equally productive upper-level bats.

Origin-selected comparisons: Matt Thaiss: 164 subsequent PA, +0.47 offense; Brent Rooker: 0 subsequent PA, +0.00 offense; Will Craig: 0 subsequent PA, +0.00 offense; Josh Lester: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Bryan Reynolds after 2018

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | A | 66 | 1 | 2 | 20 |
| 2016 | Aminus | 171 | 5 | 11 | 41 |
| 2017 | Aplus | 541 | 10 | 37 | 106 |
| 2018 | AA | 383 | 7 | 40 | 73 |

Current forecast: 15.64% chance of any MLB PA, 81.02 PA conditional on appearing, 12.67 expected PA, -0.430 Hit/600 and +0.030 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.000 | +0.054 |
| Constant hitting spread | +0.000 | +0.000 | +0.000 |
| Sample dependent spread | +0.000 | +0.000 | +0.000 |

Reality: 546 MLB PA, +3.312 actual Hit/600 and +4.696 delivered offense.

Calibration: 179 distinct earlier active players; 1 share the refined origin-known profile. Rate variance is 1.2275 + 1.1867 times 600/PA; the constant reference variance is 16.5155. The uncentered nested residual bias is -0.948. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.749; its largest signed input contributions are age_centered +0.396, draft_class_unknown -0.174, pooled_Aplus_BABIP +0.153, draft_known +0.141, pooled_AA_BABIP +0.103, pooled_AA_pa -0.074. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 5.67%; probability of at least two custom offense wins is 0.17%. Impossible conditional PA/offense probability is 0.64%.

Reynolds's 383 AA PA and prior 541 A-plus PA are present. The rate fit uses positive BABIP evidence but retains -0.430, while arrival is only 15.64 percent and conditional workload 81 PA. Adding negative batting risk reduces positive-offense probability enough that P90 moves from 0.054 to exactly zero: this follows the mixture CDF, not an inverse-CDF coding failure. Actual 546 PA and 4.70 offense remain nowhere near the forecast. A wider positive distribution cannot cure the readiness center. Only one refined calibration person exists; Milone/Montgomery/Lund/DeLuzio are not demonstrated equivalent performance prospects, so their zero outcomes are not a justification.

Origin-selected comparisons: Thomas Milone: 0 subsequent PA, +0.00 offense; Troy Montgomery: 0 subsequent PA, +0.00 offense; Brennon Lund: 0 subsequent PA, +0.00 offense; Ben DeLuzio: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Jackson Holliday after 2023

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | A | 57 | 0 | 14 | 10 |
| 2022 | RK124 | 33 | 1 | 10 | 2 |
| 2023 | A | 67 | 2 | 14 | 13 |
| 2023 | AA | 164 | 3 | 19 | 34 |
| 2023 | AAA | 91 | 2 | 16 | 17 |
| 2023 | Aplus | 259 | 5 | 50 | 54 |

Current forecast: 88.68% chance of any MLB PA, 396.01 PA conditional on appearing, 351.19 expected PA, +0.621 Hit/600 and +1.451 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +1.508 | +2.511 |
| Constant hitting spread | -2.057 | +0.861 | +5.789 |
| Sample dependent spread | +0.000 | +1.293 | +3.259 |

Reality: 208 MLB PA, -3.310 actual Hit/600 and -0.503 delivered offense.

Calibration: 179 distinct earlier active players; 1 share the refined origin-known profile. Rate variance is 0.5655 + 1.3782 times 600/PA; the constant reference variance is 23.4396. The uncentered nested residual bias is -1.443. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.910; its largest signed input contributions are age_centered +0.890, position_6 -0.259, reorganized -0.200, pooled_AA_BABIP +0.196, draft_rank +0.190, pooled_Aplus_BB +0.162. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 6.97%; probability of at least two custom offense wins is 31.36%. Impossible conditional PA/offense probability is 0.00%.

Holliday's 581 multi-level PA, 99 walks and 118 K feed strong age and walk/BABIP contributions. Current rate 0.621 and 351 expected PA are optimistic versus the next year's 208 PA and -3.310 common-origin rate. The sample-dependent lower displayed bound stays zero because the nonarrival atom plus negative batting mass crosses P10; actual -0.50 offense remains below it. Negative-offense probability is about seven percent, so a poor hitting season is possible but still underweighted in this case. Constant spread includes it but is broadly too diffuse. Merrill succeeds while three origin-selected peers do not arrive; one refined calibration analogue does not validate a specific elite-teen distribution.

Origin-selected comparisons: Jackson Merrill: 593 subsequent PA, +3.30 offense; Carson Williams: 0 subsequent PA, +0.00 offense; Jett Williams: 0 subsequent PA, +0.00 offense; Edwin Arroyo: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Brandon Belt after 2023

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 15 | 0 | 2 | 3 |
| 2021 | MLB | 381 | 29 | 45 | 103 |
| 2022 | MLB | 298 | 8 | 35 | 81 |
| 2023 | MLB | 404 | 19 | 60 | 141 |

Current forecast: 64.63% chance of any MLB PA, 377.77 PA conditional on appearing, 244.16 expected PA, +0.686 Hit/600 and +1.035 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +1.013 | +2.370 |
| Constant hitting spread | -1.284 | +0.000 | +4.747 |
| Sample dependent spread | +0.000 | +0.600 | +2.900 |

Reality: 0 MLB PA, unobserved actual Hit/600 and +0.000 delivered offense.

Calibration: 179 distinct earlier active players; 3 share the refined origin-known profile. Rate variance is 0.5655 + 1.3782 times 600/PA; the constant reference variance is 23.4396. The uncentered nested residual bias is -1.443. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.910; its largest signed input contributions are age_centered -0.890, pooled_mlb_quality +0.717, work_0 +0.497, quality_0 +0.286, position_10 +0.271, work_2 +0.260. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 5.08%; probability of at least two custom offense wins is 22.05%. Impossible conditional PA/offense probability is 0.00%.

Belt had 19 HR and 60 unintentional walks in 404 MLB PA after weaker/shorter prior seasons. The model preserves good hitting evidence, 64.63 percent appearance probability and 244 expected PA. Sample-dependent median offense falls from 1.01 to 0.60 and the actual zero is inside the range, but this is not a new unsigned-player or retirement penalty. The nonarrival probability was already present. Martinez, Blackmon, Canha and McCutchen all receive meaningful future PA, preserving the user's point that Belt's failure to sign was an unusual miss rather than proof that older good hitters should be written off. Three refined calibration people imply a qualified range.

Origin-selected comparisons: J.D. Martinez: 495 subsequent PA, +1.45 offense; Charlie Blackmon: 499 subsequent PA, +1.71 offense; Mark Canha: 462 subsequent PA, +1.11 offense; Andrew McCutchen: 515 subsequent PA, +1.85 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Wander Franco after 2023

Selection: fixed before fits.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 180 | 7 | 14 | 21 |
| 2021 | MLB | 308 | 7 | 24 | 37 |
| 2022 | AAA | 25 | 0 | 4 | 3 |
| 2022 | MLB | 344 | 6 | 25 | 33 |
| 2022 | RK124 | 7 | 0 | 0 | 2 |
| 2023 | MLB | 491 | 17 | 39 | 69 |

Current forecast: 99.05% chance of any MLB PA, 564.86 PA conditional on appearing, 559.49 expected PA, +1.035 Hit/600 and +2.698 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.688 | +2.816 | +3.553 |
| Constant hitting spread | -1.977 | +2.465 | +7.783 |
| Sample dependent spread | +0.748 | +2.623 | +4.741 |

Reality: 0 MLB PA, unobserved actual Hit/600 and +0.000 delivered offense.

Calibration: 186 distinct earlier active players; 0 share the refined origin-known profile. Rate variance is 0.6404 + 1.3428 times 600/PA; the constant reference variance is 15.8928. The uncentered nested residual bias is -1.229. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.958; its largest signed input contributions are work_0 +0.631, age_centered +0.520, pooled_mlb_quality +0.457, position_6 -0.295, work_2 +0.270, prior_debut +0.210. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 2.59%; probability of at least two custom offense wins is 65.75%. Impossible conditional PA/offense probability is 0.00%.

Franco's 491 MLB PA, 17 HR and low strikeouts support the saved performance center, but this experiment leaves a 99.05 percent appearance probability and 559 expected PA before zero actual. Sample-dependent spread improves the quantile loss without bringing zero into its 0.75 to 4.74 interval. Constant batting spread contains zero for the wrong mechanism: a possible poor hitting season is not an estimate of legal availability. No mean or availability assumption is repaired. McLain's zero, Witt's strong season and Duran/Neto's varied production show distinct future paths, not equivalent legal risks. Refined calibration support is zero.

Origin-selected comparisons: Matt McLain: 0 subsequent PA, +0.00 offense; Bobby Witt Jr.: 709 subsequent PA, +7.24 offense; Ezequiel Duran: 285 subsequent PA, -0.24 offense; Zach Neto: 602 subsequent PA, +2.31 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Whit Merrifield after 2017

Selection: largest gain versus fixed.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | AAA | 594 | 5 | 38 | 66 |
| 2016 | AAA | 304 | 8 | 21 | 55 |
| 2016 | MLB | 332 | 2 | 18 | 72 |
| 2017 | AAA | 37 | 3 | 1 | 4 |
| 2017 | MLB | 630 | 19 | 29 | 88 |

Current forecast: 99.07% chance of any MLB PA, 580.56 PA conditional on appearing, 575.14 expected PA, -0.376 Hit/600 and +1.409 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.892 | +1.477 | +1.837 |
| Constant hitting spread | -3.567 | +1.257 | +6.601 |
| Sample dependent spread | -0.552 | +1.329 | +3.519 |

Reality: 707 MLB PA, +1.391 actual Hit/600 and +3.814 delivered offense.

Calibration: 174 distinct earlier active players; 15 share the refined origin-known profile. Rate variance is 1.3681 + 1.1790 times 600/PA; the constant reference variance is 16.7244. The uncentered nested residual bias is -0.566. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.772; its largest signed input contributions are work_0 +0.507, draft_class_unknown -0.202, pooled_AAA_K -0.186, prior_debut +0.163, draft_known +0.145, pooled_mlb_quality +0.118. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 18.21%; probability of at least two custom offense wins is 33.98%. Impossible conditional PA/offense probability is 0.00%.

Merrifield's 630 MLB PA and 19 HR in the origin season are observed alongside AAA history. The saved rate remains -0.376, with workload and prior-debut terms offsetting the negative intercept and other terms. Fixed-rate P90 is only 1.84 offense; sample-dependent P90 rises to 3.52, closer to 3.81 actual over 707 PA, supplying the largest gain against workload only. The constant spread is much wider, -3.57 to 6.60. This shows why batting spread matters but does not repair the low average rate. Hernandez's productive season and the weaker Gordon/Harrison/Solarte seasons remain in the outcome-blind peer set.

Origin-selected comparisons: César Hernández: 708 subsequent PA, +2.10 offense; Dee Strange-Gordon: 588 subsequent PA, -0.50 offense; Josh Harrison: 374 subsequent PA, -0.01 offense; Yangervis Solarte: 506 subsequent PA, -0.03 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Brian Dozier after 2016

Selection: largest harm versus fixed.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | MLB | 707 | 23 | 88 | 129 |
| 2015 | MLB | 704 | 28 | 59 | 148 |
| 2016 | MLB | 691 | 42 | 55 | 138 |

Current forecast: 99.10% chance of any MLB PA, 625.00 PA conditional on appearing, 619.36 expected PA, +2.024 Hit/600 and +4.000 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +2.590 | +4.263 | +5.038 |
| Constant hitting spread | -1.633 | +3.727 | +10.159 |
| Sample dependent spread | +1.474 | +3.920 | +6.634 |

Reality: 705 MLB PA, +2.309 actual Hit/600 and +4.889 delivered offense.

Calibration: 182 distinct earlier active players; 17 share the refined origin-known profile. Rate variance is 1.6999 + 1.0267 times 600/PA; the constant reference variance is 18.7278. The uncentered nested residual bias is -0.975. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.536; its largest signed input contributions are work_2 +0.688, pooled_mlb_quality +0.679, work_0 +0.501, quality_0 +0.430, draft_college +0.212, age_centered -0.173. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 1.03%; probability of at least two custom offense wins is 83.85%. Impossible conditional PA/offense probability is 0.00%.

Dozier entered with three nearly full MLB seasons and 42 origin-season HR. His workload/quality inputs produce a 2.024 rate and 619 expected PA; actual 705 PA and 4.89 offense were already near the fixed-rate upper range. Adding sample-dependent batting spread widens 2.59 to 5.04 into 1.47 to 6.63 and worsens quantile loss, the largest harm versus workload only. This is the expected sharpness cost of uncertain forecasts on a realized near-center case, not evidence that uncertainty should be removed only for Dozier. Seventeen refined calibration people and mixed Kipnis/Forsythe/LeMahieu/Murphy outcomes remain visible.

Origin-selected comparisons: Jason Kipnis: 373 subsequent PA, +0.70 offense; Logan Forsythe: 439 subsequent PA, +1.09 offense; DJ LeMahieu: 682 subsequent PA, +3.62 offense; Daniel Murphy: 593 subsequent PA, +4.95 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Rafael Devers after 2022

Selection: largest gain versus constant.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 248 | 11 | 13 | 67 |
| 2021 | MLB | 664 | 38 | 55 | 143 |
| 2022 | MLB | 614 | 27 | 39 | 114 |

Current forecast: 99.37% chance of any MLB PA, 618.28 PA conditional on appearing, 614.36 expected PA, +2.239 Hit/600 and +4.216 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +2.793 | +4.454 | +5.305 |
| Constant hitting spread | -2.574 | +3.931 | +11.520 |
| Sample dependent spread | +1.981 | +4.187 | +6.490 |

Reality: 656 MLB PA, +2.393 actual Hit/600 and +4.671 delivered offense.

Calibration: 155 distinct earlier active players; 2 share the refined origin-known profile. Rate variance is 0.5726 + 1.3584 times 600/PA; the constant reference variance is 27.6105. The uncentered nested residual bias is -1.751. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.853; its largest signed input contributions are pooled_mlb_quality +1.002, work_0 +0.751, work_2 +0.425, quality_0 +0.386, work_1 +0.348, quality_1 +0.256. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 0.25%; probability of at least two custom offense wins is 89.79%. Impossible conditional PA/offense probability is 0.00%.

Devers's 2020 short-season raw counts are retained separately from the following 664/614 MLB PA seasons; the saved inputs and point model are unchanged, not reinterpreted as a full missed 2020 season. His 2.239 rate and 614 expected PA give 4.22 mean offense versus 4.67 actual. Constant hitting variance learned from many tiny future samples gives an implausibly diffuse -2.57 to 11.52 interval, whereas sample-dependent spread is 1.98 to 6.49. This is the largest improvement against constant spread, mainly because a full-season hitting average is much less noisy than a brief MLB trial. Only two refined calibration analogues exist; Riley/Tucker/Bregman/Lowe show high-workload productive controls, not proof of identical talent.

Origin-selected comparisons: Austin Riley: 715 subsequent PA, +5.51 offense; Kyle Tucker: 674 subsequent PA, +5.33 offense; Alex Bregman: 724 subsequent PA, +4.98 offense; Nathaniel Lowe: 724 subsequent PA, +4.29 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Ronald Acuña Jr. after 2022

Selection: largest harm versus constant.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 202 | 14 | 36 | 60 |
| 2021 | MLB | 360 | 24 | 47 | 85 |
| 2022 | AAA | 25 | 0 | 5 | 6 |
| 2022 | MLB | 533 | 15 | 49 | 126 |

Current forecast: 98.78% chance of any MLB PA, 531.19 PA conditional on appearing, 524.72 expected PA, +2.090 Hit/600 and +3.471 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.938 | +3.625 | +4.795 |
| Constant hitting spread | -2.269 | +3.074 | +9.919 |
| Sample dependent spread | +1.311 | +3.402 | +5.719 |

Reality: 735 MLB PA, +6.001 actual Hit/600 and +9.653 delivered offense.

Calibration: 155 distinct earlier active players; 1 share the refined origin-known profile. Rate variance is 0.5726 + 1.3584 times 600/PA; the constant reference variance is 27.6105. The uncentered nested residual bias is -1.751. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.853; its largest signed input contributions are pooled_mlb_quality +0.905, work_0 +0.652, work_2 +0.346, age_centered +0.337, quality_1 +0.284, work_1 +0.188. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 0.63%; probability of at least two custom offense wins is 79.80%. Impossible conditional PA/offense probability is 0.00%.

Acuna's 533 origin MLB PA, 15 HR and productive previous seasons yield a 2.090 rate and 525 expected PA. His following 735 PA and 9.65 offense are an exceptional upper-tail miss. Constant spread's P90 of 9.92 captures it; the better overall sample-dependent construction reaches only 5.72 and supplies the largest harm against that reference. A full-season variance model need not encompass every exceptional outcome, but this case shows remaining star-tail risk. The point workload and hitting center are both too low. One refined calibration person cannot certify superstar-tail probabilities; Tucker/Vaughn/Soto/Devers provide varied outcomes without selection on future success.

Origin-selected comparisons: Kyle Tucker: 674 subsequent PA, +5.33 offense; Andrew Vaughn: 615 subsequent PA, +2.72 offense; Juan Soto: 708 subsequent PA, +7.08 offense; Rafael Devers: 656 subsequent PA, +4.67 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Chris Davis after 2017

Selection: major false high mean.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 670 | 47 | 78 | 208 |
| 2016 | MLB | 665 | 38 | 85 | 219 |
| 2017 | A | 4 | 0 | 0 | 1 |
| 2017 | Aplus | 5 | 0 | 1 | 2 |
| 2017 | MLB | 524 | 26 | 57 | 195 |

Current forecast: 97.51% chance of any MLB PA, 515.52 PA conditional on appearing, 502.67 expected PA, +1.082 Hit/600 and +2.452 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.264 | +2.571 | +3.493 |
| Constant hitting spread | -2.460 | +2.085 | +7.988 |
| Sample dependent spread | +0.475 | +2.348 | +4.535 |

Reality: 522 MLB PA, -4.102 actual Hit/600 and -1.963 delivered offense.

Calibration: 180 distinct earlier active players; 20 share the refined origin-known profile. Rate variance is 0.8687 + 1.1729 times 600/PA; the constant reference variance is 22.0516. The uncentered nested residual bias is -0.961. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.846; its largest signed input contributions are pooled_mlb_quality +0.478, work_0 +0.463, work_1 +0.409, age_centered -0.376, work_2 +0.309, position_3 +0.219. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 3.04%; probability of at least two custom offense wins is 58.78%. Impossible conditional PA/offense probability is 0.00%.

Davis's HR fell from 47 to 38 to 26, with 195 K in 524 origin MLB PA. The Ridge still gives +1.082, partly through pooled past quality and workload; expected PA 503 is relatively close to 522 actual. The large offense miss, +2.45 versus -1.96, is chiefly hitting rather than opportunity. Sample-dependent spread has only about three percent negative-offense probability and a positive P10, so it still misses the collapse. The diffuse constant model contains it but cannot justify fixing this player's mean. Twenty refined calibration people and Duda/Thames/Zimmerman/Alonso controls do not make the collapse certain from origin data; the persistent downside miss should remain in further joint-risk review.

Origin-selected comparisons: Lucas Duda: 367 subsequent PA, +0.93 offense; Eric Thames: 278 subsequent PA, +0.95 offense; Ryan Zimmerman: 323 subsequent PA, +1.79 offense; Yonder Alonso: 574 subsequent PA, +1.69 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Aaron Judge after 2016

Selection: major false low mean.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | A | 278 | 9 | 38 | 59 |
| 2014 | Aplus | 285 | 8 | 49 | 72 |
| 2015 | AA | 280 | 12 | 23 | 70 |
| 2015 | AAA | 260 | 8 | 29 | 74 |
| 2016 | AAA | 410 | 19 | 47 | 98 |
| 2016 | MLB | 95 | 4 | 9 | 42 |

Current forecast: 92.50% chance of any MLB PA, 335.05 PA conditional on appearing, 309.92 expected PA, -0.040 Hit/600 and +0.936 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.169 | +0.921 | +1.694 |
| Constant hitting spread | -2.041 | +0.501 | +4.483 |
| Sample dependent spread | -0.153 | +0.770 | +2.375 |

Reality: 678 MLB PA, +5.557 actual Hit/600 and +8.372 delivered offense.

Calibration: 184 distinct earlier active players; 0 share the refined origin-known profile. Rate variance is 0.4248 + 1.2553 times 600/PA; the constant reference variance is 21.6780. The uncentered nested residual bias is -1.065. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.744; its largest signed input contributions are age_centered +0.283, draft_class_unknown -0.206, position_9 +0.167, draft_known +0.129, pooled_mlb_quality -0.119, pooled_Aplus_BB +0.111. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 14.14%; probability of at least two custom offense wins is 15.60%. Impossible conditional PA/offense probability is 0.01%.

Judge after 2016 combines 410 AAA PA with 19 HR and a difficult 95-PA MLB trial with 42 K. The saved rate is -0.040 and expected PA 310. Adding sample-dependent risk lifts P90 offense from 1.69 to 2.37, nowhere near the next year's 8.37 over 678 PA. This is the largest false-low mean in the cohort, not a prediction repaired by greater variance. AAA performance and the brief MLB sample are represented, but the future star path remains severely underweighted. Zero refined calibration support qualifies the range; Renfroe's 479 PA and three non-arrivals preserve unsuccessful comparisons without explaining away Judge.

Origin-selected comparisons: Hunter Renfroe: 479 subsequent PA, +1.57 offense; Steven Moya: 0 subsequent PA, +0.00 offense; Kyle Waldrop: 0 subsequent PA, +0.00 offense; Sócrates Brito: 0 subsequent PA, +0.00 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Ben Rortvedt after 2023

Selection: ordinary active mean.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 136 | 5 | 10 | 35 |
| 2021 | MLB | 98 | 3 | 6 | 29 |
| 2022 | A | 5 | 1 | 1 | 1 |
| 2022 | AAA | 177 | 6 | 18 | 57 |
| 2022 | Aplus | 15 | 0 | 3 | 6 |
| 2023 | A | 11 | 0 | 1 | 1 |
| 2023 | AA | 4 | 0 | 0 | 0 |
| 2023 | AAA | 124 | 6 | 16 | 31 |
| 2023 | MLB | 79 | 2 | 11 | 19 |

Current forecast: 87.33% chance of any MLB PA, 94.22 PA conditional on appearing, 82.28 expected PA, -1.102 Hit/600 and +0.104 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.052 | +0.289 |
| Constant hitting spread | -0.555 | +0.000 | +0.908 |
| Sample dependent spread | -0.340 | +0.004 | +0.660 |

Reality: 328 MLB PA, -1.669 actual Hit/600 and +0.103 delivered offense.

Calibration: 217 distinct earlier active players; 6 share the refined origin-known profile. Rate variance is 0.8319 + 1.3238 times 600/PA; the constant reference variance is 18.4718. The uncentered nested residual bias is -1.266. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.790; its largest signed input contributions are pooled_mlb_quality -0.370, position_2 -0.255, age_centered +0.221, reorganized -0.189, pooled_MLB_BABIP +0.140, quality_0 -0.129. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 36.62%; probability of at least two custom offense wins is 0.64%. Impossible conditional PA/offense probability is 3.23%.

Rortvedt is the mechanically selected near-perfect offense-mean case, not a genuinely accurate two-component forecast. His 79 origin MLB PA and poor observed hitting feed negative pooled/current quality and catcher-position terms. Expected PA is only 82 versus 328 actual, while rate -1.102 is too optimistic versus -1.669. These errors compensate to predict +0.104 offense versus +0.103 actual. Sample-dependent range -0.34 to +0.66 contains the result, but 3.23 percent of its joint PA/offense probability is physically impossible at the smallest PA counts. Six refined calibration people, and Herrera/Pinto/Bart/Amaya's varied workloads, reinforce that a good final value alone is not model validation.

Origin-selected comparisons: Jose Herrera: 114 subsequent PA, -0.24 offense; René Pinto: 49 subsequent PA, +0.09 offense; Joey Bart: 282 subsequent PA, +1.54 offense; Miguel Amaya: 363 subsequent PA, -0.04 offense.

Comparison limit: Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched.

## Terrance Gore after 2018

Selection: largest impossible joint PA and offense probability, descriptive post-result case.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | AA | 302 | 0 | 25 | 58 |
| 2016 | MLB | 3 | 0 | 0 | 1 |
| 2017 | AA | 62 | 0 | 2 | 13 |
| 2017 | AAA | 192 | 1 | 16 | 38 |
| 2017 | MLB | 5 | 0 | 1 | 2 |
| 2018 | AAA | 205 | 0 | 19 | 49 |
| 2018 | MLB | 5 | 0 | 0 | 1 |

Current forecast: 69.23% chance of any MLB PA, 41.38 PA conditional on appearing, 28.65 expected PA, -1.253 Hit/600 and +0.028 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.001 | +0.093 |
| Constant hitting spread | -0.094 | +0.000 | +0.184 |
| Sample dependent spread | -0.132 | +0.000 | +0.224 |

Reality: 58 MLB PA, +0.515 actual Hit/600 and +0.228 delivered offense.

Calibration: 169 distinct earlier active players; 11 share the refined origin-known profile. Rate variance is 0.2960 + 1.2190 times 600/PA; the constant reference variance is 16.0158. The uncentered nested residual bias is -1.217. These numbers do not identify pure talent variance.

The saved rate fit has intercept -0.611; its largest signed input contributions are draft_class_unknown -0.107, draft_elapsed -0.089, pooled_AAA_HR -0.081, pooled_AA_pa -0.071, pooled_AA_2B -0.068, draft_known +0.059. All contributions, not only these six, reproduce the current rate exactly.

Negative-offense probability is 31.86%; probability of at least two custom offense wins is 0.08%. Impossible conditional PA/offense probability is 8.62%.

Gore's own MLB batting exposure was only three, five and five PA across the three source years despite hundreds of minor PA. The saved model reasonably expects a small batting workload, about 29 PA, though actual is 58. Sample-dependent range -0.132 to +0.224 narrowly misses +0.228 actual and appears innocuous as a marginal interval, but 8.62 percent of the joint PA/offense law is outside the allowable event-value bounds. Independent per-PA envelope sums reproduce that failure. This is an approximation defect at tiny PA, not hidden speed value: baserunning is outside this offense target. Tauchman/Kaczmarski/Jonathan Davis/Cordell have different subsequent workloads; those peers do not validate Gore's tail distribution. Preserve this case and do not repair it with a player-specific clip or promotion of a selected high-PA subgroup.

Origin-selected comparisons: Mike Tauchman: 296 subsequent PA, +2.37 offense; Kevin Kaczmarski: 0 subsequent PA, +0.00 offense; Jonathan Davis: 95 subsequent PA, -0.26 offense; Ryan Cordell: 247 subsequent PA, +0.06 offense.

Comparison limit: Same origin, broad stage and debut history; age, position, MLB exposure and quality; not speed or medical history.

## Review decision

Retain sample-dependent hitting spread as qualified development evidence that workload-only ranges omit valuable risk. Do not promote this Normal construction as a physically coherent full-population distribution or deploy it: low-PA impossible mass, PA-related residual bias, sparse profile calibration and unrepaired readiness/star misses remain. Keep every current mean, the frozen forecast and deployed explorers unchanged.

The canceled 2020 MiLB season is not treated as failed production; target 2020 is excluded.
Observed short-season MLB counts remain explicit. The mean and source limitations of the
current model remain. None of these cases authorizes deployment or a claim of full player value.
