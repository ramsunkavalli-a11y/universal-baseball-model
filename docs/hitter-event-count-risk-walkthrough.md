# Player checks for integer hitting outcome ranges

Historical forecasts use the documented season-end plus following preseason information
date and predict the following calendar year. Every mean stays fixed. Offense is custom
fixed-event batting plus replacement, not full WAR or six years of club control.

The count distributions generate actual integer events. Their reference profile is a
working distribution shape, not a player-specific K, BB or HR projection. The associated
version links possible workload and hitting while preserving total expected offense.

Case selection includes thirteen fixed player-origin cases, largest score gains and harms,
false high and low mean forecasts, and an ordinary active result. Player judgments below
are reviewed separately from the mechanical replay. Full input and saved-model traces are
[in the evidence](../reports/model-evidence/hitter-event-count-risk/reviewed-cases.json).

## Aaron Judge after 2024

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 696 | 62 | 92 | 175 |
| 2023 | MLB | 458 | 37 | 79 | 130 |
| 2024 | MLB | 704 | 58 | 113 | 171 |

Current forecast: 99.07% chance of MLB PA, 535.74 PA conditional on appearing, 530.75 expected PA, +4.534 Hit/600 and +5.668 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +3.364 | +5.895 | +7.689 |
| Prior Normal law | +2.888 | +5.670 | +8.455 |
| Independent counts | +2.793 | +5.531 | +8.764 |
| Associated counts | +2.575 | +5.618 | +8.763 |

Reality: 679 MLB PA, +6.427 actual Hit/600 and +9.393 delivered offense.

The independent concentration is 464.22. The associated concentration is 603.12 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.3263. The refined calibration intersection contains 19 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.922; largest signed input contributions are pooled_mlb_quality +2.683, quality_0 +1.300, work_0 +0.845, age_centered -0.541, quality_2 +0.479, work_2 +0.433. All saved contributions together reproduce the unchanged point rate.

Judge's three recent MLB seasons contain 696, 458 and 704 PA with 62, 37 and 58 HR. The actual saved Ridge receives that history: pooled MLB quality and current quality add large positive contributions, while age subtracts. The unchanged point is 531 expected PA and 5.668 custom offense wins, versus 679 and 9.393 observed. Integer counts raise the associated P90 from the Normal 8.455 to 8.763 and reduce pinball loss, but still miss the upper outcome. The lower quantile also moves downward, so this is not simply raising Judge's forecast. Nineteen earlier refined calibration people and the global slope bound cannot certify superstar-specific uncertainty. Ohtani/Freeman/Betts/Alvarez are useful origin-selected contrasts with widely varying outcomes, not proof that his miss is unfixable.

Origin-selected comparisons: Shohei Ohtani: 727 subsequent PA, +8.05 offense; Freddie Freeman: 627 subsequent PA, +4.93 offense; Mookie Betts: 663 subsequent PA, +2.56 offense; Yordan Alvarez: 199 subsequent PA, +0.97 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Juan Soto after 2023

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 654 | 29 | 122 | 93 |
| 2022 | MLB | 664 | 27 | 129 | 96 |
| 2023 | MLB | 708 | 35 | 121 | 129 |

Current forecast: 99.31% chance of MLB PA, 638.36 PA conditional on appearing, 633.93 expected PA, +3.941 Hit/600 and +6.126 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +4.271 | +6.465 | +7.518 |
| Prior Normal law | +3.620 | +6.173 | +8.590 |
| Independent counts | +3.415 | +6.077 | +8.816 |
| Associated counts | +3.381 | +6.095 | +8.836 |

Reality: 713 MLB PA, +5.044 actual Hit/600 and +8.201 delivered offense.

The independent concentration is 804.23. The associated concentration is 1157.63 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.4821. The refined calibration intersection contains 4 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.809; largest signed input contributions are pooled_mlb_quality +1.595, work_0 +1.110, quality_0 +0.497, quality_2 +0.458, work_2 +0.447, age_centered +0.314. All saved contributions together reproduce the unchanged point rate.

Soto already supplied 654, 664 and 708 MLB PA with 29, 27 and 35 HR and more than 120 unintentional walks each season. His point forecast remains 634 PA, 3.941 Hit/600 and 6.126 custom offense wins. The actual 713 PA and 8.201 offense are inside both the old and new central ranges. The associated median falls from 6.173 to 6.095 and P90 rises from 8.590 to 8.836; because the old range already covered the outcome, the extra spread worsens this player's pinball loss from .504 to .533. A wider plausible range is not automatically a better forecast. Only four refined calibration people support this profile; selected Acuna, Guerrero, Riley and Carroll retain both interrupted and regular seasons.

Origin-selected comparisons: Ronald Acuña Jr.: 222 subsequent PA, +0.78 offense; Vladimir Guerrero Jr.: 697 subsequent PA, +6.37 offense; Austin Riley: 469 subsequent PA, +2.21 offense; Corbin Carroll: 684 subsequent PA, +2.43 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Nick Kurtz after 2024

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 10 | 7 |
| 2024 | AA | 15 | 0 | 2 | 3 |

Current forecast: 6.06% chance of MLB PA, 168.16 PA conditional on appearing, 10.18 expected PA, -0.063 Hit/600 and +0.031 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.000 | +0.000 |
| Prior Normal law | +0.000 | +0.000 | +0.000 |
| Independent counts | +0.000 | +0.000 | +0.000 |
| Associated counts | +0.000 | +0.000 | +0.000 |

Reality: 489 MLB PA, +5.289 actual Hit/600 and +5.838 delivered offense.

The independent concentration is 679.21. The associated concentration is 1021.34 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.4025. The refined calibration intersection contains 0 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.02%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.985; largest signed input contributions are age_centered +0.619, reorganized -0.263, draft_rank +0.165, position_3 +0.135, age_squared +0.078, absence_window_scaled -0.061. All saved contributions together reproduce the unchanged point rate.

Kurtz had only 50 professional PA, four HR, twelve walks and ten strikeouts across A and AA at the origin. The actual rate inputs still give substantial relative weight to age, draft information, position and era, rather than validating an elite MLB-ready hitting center from this tiny sample. The existing 6.06 percent arrival probability, 10.18 expected PA and .031 expected offense stay exactly unchanged; the actual outcome is 489 PA and 5.838 offense. All three reported quantiles remain zero because the non-arrival mass exceeds ninety percent. Integer support cannot repair the readiness estimate, and this fixed case has zero matching calibration people. The selected Ariza/Avila/Chevalier/Quero controls are broad origin-known matches, not elite college-bat analogues; their zero outcomes do not explain away Kurtz.

Origin-selected comparisons: Luis Ariza: 0 subsequent PA, +0.00 offense; Carlos Avila: 0 subsequent PA, +0.00 offense; Luis Chevalier: 0 subsequent PA, +0.00 offense; Jeferson Quero: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Wyatt Langford after 2023

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 11 | 7 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 1 | 3 |

Current forecast: 59.91% chance of MLB PA, 358.74 PA conditional on appearing, 214.92 expected PA, +0.688 Hit/600 and +0.912 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.823 | +2.219 |
| Prior Normal law | +0.000 | +0.354 | +2.698 |
| Independent counts | +0.000 | +0.317 | +2.656 |
| Associated counts | +0.000 | +0.220 | +2.832 |

Reality: 557 MLB PA, +0.077 actual Hit/600 and +1.796 delivered offense.

The independent concentration is 643.55. The associated concentration is 832.83 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.9839. The refined calibration intersection contains 0 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.903; largest signed input contributions are age_centered +0.674, reorganized -0.191, position_7 +0.187, draft_college +0.161, pooled_AAA_BB +0.102, age_squared +0.099. All saved contributions together reproduce the unchanged point rate.

Langford's 200 professional PA across rookie, A-plus, AA and AAA included ten HR, 36 walks and 34 strikeouts. Those counts are retained, but the scalar hitting point remains .688 Hit/600 and opportunity remains 215 expected PA against 557 actual. The associated median drops from the Normal .354 to .220 while P90 rises from 2.698 to 2.832. His actual 1.796 custom offense was already inside the old range, so loss worsens .330 to .357. The low-workload rate shift and compensating larger-workload upside preserve the mean; they do not make his rate or readiness more accurate. There are no matching calibration people. Crews/Montgomery/DeLauter/Teel remain timing controls with zero outcomes preserved, not evidence that all elite recent draftees share this law.

Origin-selected comparisons: Dylan Crews: 132 subsequent PA, +0.02 offense; Colson Montgomery: 0 subsequent PA, +0.00 offense; Chase DeLauter: 0 subsequent PA, +0.00 offense; Kyle Teel: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Pete Alonso after 2018

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 123 | 5 | 11 | 22 |
| 2017 | AA | 47 | 2 | 2 | 7 |
| 2017 | Aplus | 346 | 16 | 24 | 64 |
| 2018 | AA | 273 | 15 | 40 | 50 |
| 2018 | AAA | 301 | 21 | 33 | 78 |

Current forecast: 80.36% chance of MLB PA, 267.58 PA conditional on appearing, 215.03 expected PA, +0.286 Hit/600 and +0.765 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.708 | +1.633 |
| Prior Normal law | -0.063 | +0.508 | +2.138 |
| Independent counts | -0.058 | +0.526 | +2.129 |
| Associated counts | -0.159 | +0.413 | +2.249 |

Reality: 693 MLB PA, +3.865 actual Hit/600 and +6.598 delivered offense.

The independent concentration is 678.40. The associated concentration is 905.56 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.7557. The refined calibration intersection contains 0 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.02%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.668; largest signed input contributions are age_centered +0.415, position_3 +0.174, draft_known +0.155, draft_class_unknown -0.139, pooled_AAA_HR +0.123, pooled_AA_BB +0.092. All saved contributions together reproduce the unchanged point rate.

Alonso's origin record includes 574 AA/AAA PA, 36 HR, 73 walks and 128 strikeouts, after meaningful previous minor seasons. The unchanged point of 215 expected PA and .286 Hit/600 is much too low against 693 PA and 3.865 observed Hit/600. Associated count risk raises P90 modestly from 2.138 to 2.249 custom offense, but the actual 6.598 remains far outside it. Pinball loss improves slightly, not enough to call the entry forecast repaired. Zero refined calibration people and the working league event profile qualify the range. Thaiss, Rooker, Craig and Lester were selected without future outcomes; their varied timing is useful context, but not an explanation for discarding Alonso's substantial upper-minors production.

Origin-selected comparisons: Matt Thaiss: 164 subsequent PA, +0.47 offense; Brent Rooker: 0 subsequent PA, +0.00 offense; Will Craig: 0 subsequent PA, +0.00 offense; Josh Lester: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Bryan Reynolds after 2018

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | A | 66 | 1 | 2 | 20 |
| 2016 | Aminus | 171 | 5 | 11 | 41 |
| 2017 | Aplus | 541 | 10 | 37 | 106 |
| 2018 | AA | 383 | 7 | 40 | 73 |

Current forecast: 15.64% chance of MLB PA, 81.02 PA conditional on appearing, 12.67 expected PA, -0.430 Hit/600 and +0.030 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.000 | +0.054 |
| Prior Normal law | +0.000 | +0.000 | +0.000 |
| Independent counts | +0.000 | +0.000 | +0.000 |
| Associated counts | +0.000 | +0.000 | +0.000 |

Reality: 546 MLB PA, +3.312 actual Hit/600 and +4.696 delivered offense.

The independent concentration is 460.74. The associated concentration is 684.74 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 4.9881. The refined calibration intersection contains 1 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.64%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.749; largest signed input contributions are age_centered +0.396, draft_class_unknown -0.174, pooled_Aplus_BABIP +0.153, draft_known +0.141, pooled_AA_BABIP +0.103, pooled_AA_pa -0.074. All saved contributions together reproduce the unchanged point rate.

Reynolds had 383 AA PA with seven HR, forty walks and 73 strikeouts after 541 A-plus PA. The saved rate inputs show a modest positive A-plus BABIP contribution but retain a -.430 Hit/600 point, and the opportunity fit gives only 12.67 expected PA. Against 546 actual PA and 4.696 offense, this is still a major readiness and talent miss. The 84.36 percent zero-PA atom alone explains the median; zero P90 also depends on the negative-offense mass reducing positive outcome probability below ten percent. Count risk changes event support, not that arrival atom. Only one refined calibration person exists. Broad Milone/Montgomery/Lund/DeLuzio controls cannot establish that Reynolds's actual AA performance was uninformative.

Origin-selected comparisons: Thomas Milone: 0 subsequent PA, +0.00 offense; Troy Montgomery: 0 subsequent PA, +0.00 offense; Brennon Lund: 0 subsequent PA, +0.00 offense; Ben DeLuzio: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Jackson Holliday after 2023

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | A | 57 | 0 | 14 | 10 |
| 2022 | RK124 | 33 | 1 | 10 | 2 |
| 2023 | A | 67 | 2 | 14 | 13 |
| 2023 | AA | 164 | 3 | 19 | 34 |
| 2023 | AAA | 91 | 2 | 16 | 17 |
| 2023 | Aplus | 259 | 5 | 50 | 54 |

Current forecast: 88.68% chance of MLB PA, 396.01 PA conditional on appearing, 351.19 expected PA, +0.621 Hit/600 and +1.451 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +1.508 | +2.511 |
| Prior Normal law | +0.000 | +1.293 | +3.259 |
| Independent counts | +0.000 | +1.254 | +3.352 |
| Associated counts | +0.000 | +1.212 | +3.448 |

Reality: 208 MLB PA, -3.310 actual Hit/600 and -0.503 delivered offense.

The independent concentration is 598.01. The associated concentration is 833.04 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.0742. The refined calibration intersection contains 1 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.910; largest signed input contributions are age_centered +0.890, position_6 -0.259, reorganized -0.200, pooled_AA_BABIP +0.196, draft_rank +0.190, pooled_Aplus_BB +0.162. All saved contributions together reproduce the unchanged point rate.

Holliday had 581 PA across four levels, twelve HR, 99 walks and 118 strikeouts at age nineteen. His unchanged point is 351 PA, .621 Hit/600 and 1.451 custom offense, whereas he delivered 208 PA and -.503 offense. The associated median falls from 1.293 to 1.212 and negative-offense probability rises to roughly nine percent, giving a small proper-score improvement. Nevertheless P10 remains zero, so the observed negative outcome is still outside the central range. One matching calibration person is not adequate evidence for an elite teenage profile. Merrill is a successful outcome-blind comparison while Williams/Williams/Arroyo have zero next-year PA; both paths remain visible. This modest distribution gain does not validate the original positive hitting center.

Origin-selected comparisons: Jackson Merrill: 593 subsequent PA, +3.30 offense; Carson Williams: 0 subsequent PA, +0.00 offense; Jett Williams: 0 subsequent PA, +0.00 offense; Edwin Arroyo: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Brandon Belt after 2023

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 15 | 0 | 2 | 3 |
| 2021 | MLB | 381 | 29 | 45 | 103 |
| 2022 | MLB | 298 | 8 | 35 | 81 |
| 2023 | MLB | 404 | 19 | 60 | 141 |

Current forecast: 64.63% chance of MLB PA, 377.77 PA conditional on appearing, 244.16 expected PA, +0.686 Hit/600 and +1.035 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +1.013 | +2.370 |
| Prior Normal law | +0.000 | +0.600 | +2.900 |
| Independent counts | +0.000 | +0.585 | +2.919 |
| Associated counts | +0.000 | +0.514 | +2.967 |

Reality: 0 MLB PA, unobserved actual Hit/600 and +0.000 delivered offense.

The independent concentration is 598.01. The associated concentration is 833.04 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.0356. The refined calibration intersection contains 3 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.910; largest signed input contributions are age_centered -0.890, pooled_mlb_quality +0.717, work_0 +0.497, quality_0 +0.286, position_10 +0.271, work_2 +0.260. All saved contributions together reproduce the unchanged point rate.

Belt's latest MLB season has 404 PA, nineteen HR and sixty unintentional walks after 381 and 298 PA in the preceding seasons. The current point remains 244 expected PA and 1.035 custom offense, with a 35.37 percent zero-PA probability. His actual zero season was the unexpected failure to find a new club that the user identified, not evidence for imposing a blanket retirement or talent-collapse penalty on productive older hitters. The associated median decreases .600 to .514 and all arms include zero, producing a small risk-score gain without changing his availability forecast. Only three refined calibration people match. Martinez, Blackmon, Canha and McCutchen actually received substantial PA, underscoring the need to keep this as an unusual roster outcome rather than a universal age rule.

Origin-selected comparisons: J.D. Martinez: 495 subsequent PA, +1.45 offense; Charlie Blackmon: 499 subsequent PA, +1.71 offense; Mark Canha: 462 subsequent PA, +1.11 offense; Andrew McCutchen: 515 subsequent PA, +1.85 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Wander Franco after 2023

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 180 | 7 | 14 | 21 |
| 2021 | MLB | 308 | 7 | 24 | 37 |
| 2022 | AAA | 25 | 0 | 4 | 3 |
| 2022 | MLB | 344 | 6 | 25 | 33 |
| 2022 | RK124 | 7 | 0 | 0 | 2 |
| 2023 | MLB | 491 | 17 | 39 | 69 |

Current forecast: 99.05% chance of MLB PA, 564.86 PA conditional on appearing, 559.49 expected PA, +1.035 Hit/600 and +2.698 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.688 | +2.816 | +3.553 |
| Prior Normal law | +0.748 | +2.623 | +4.741 |
| Independent counts | +0.646 | +2.569 | +4.862 |
| Associated counts | +0.684 | +2.599 | +4.841 |

Reality: 0 MLB PA, unobserved actual Hit/600 and +0.000 delivered offense.

The independent concentration is 631.30. The associated concentration is 989.97 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.3723. The refined calibration intersection contains 0 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.958; largest signed input contributions are work_0 +0.631, age_centered +0.520, pooled_mlb_quality +0.457, position_6 -0.295, work_2 +0.270, prior_debut +0.210. All saved contributions together reproduce the unchanged point rate.

Franco's actual origin counts still reach the point model as 491 MLB PA, seventeen HR and relatively low strikeouts. The model assigns a 99.05 percent appearance chance and 559 expected PA, although subsequent PA are zero. This remains a specific availability-representation failure, not something a generic continuous or count hitting spread solves. The associated P10 is .684 offense, still above zero, and expected offense remains 2.698. Its slight risk-score improvement versus Normal does not repair the problem; the independent count reference scores this case better still. No refined calibration people support the profile. McLain's zero season and Witt/Duran/Neto's active seasons are broad controls, not substitutes for handling this player's own cutoff-known availability evidence.

Origin-selected comparisons: Matt McLain: 0 subsequent PA, +0.00 offense; Bobby Witt Jr.: 709 subsequent PA, +7.24 offense; Ezequiel Duran: 285 subsequent PA, -0.24 offense; Zach Neto: 602 subsequent PA, +2.31 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Ronald Acuña Jr. after 2022

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 202 | 14 | 36 | 60 |
| 2021 | MLB | 360 | 24 | 47 | 85 |
| 2022 | AAA | 25 | 0 | 5 | 6 |
| 2022 | MLB | 533 | 15 | 49 | 126 |

Current forecast: 98.78% chance of MLB PA, 531.19 PA conditional on appearing, 524.72 expected PA, +2.090 Hit/600 and +3.471 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.938 | +3.625 | +4.795 |
| Prior Normal law | +1.311 | +3.402 | +5.719 |
| Independent counts | +1.189 | +3.307 | +5.949 |
| Associated counts | +1.123 | +3.350 | +5.865 |

Reality: 735 MLB PA, +6.001 actual Hit/600 and +9.653 delivered offense.

The independent concentration is 632.61. The associated concentration is 908.15 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.3240. The refined calibration intersection contains 1 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.853; largest signed input contributions are pooled_mlb_quality +0.905, work_0 +0.652, work_2 +0.346, age_centered +0.337, quality_1 +0.284, work_1 +0.188. All saved contributions together reproduce the unchanged point rate.

Acuna's retained history includes the explicitly shortened 2020 season's 202 PA, then 360 and 533 PA with 24 and fifteen HR; the short season is not treated as a missing or full failed season. The current point predicts 525 PA, 2.090 Hit/600 and 3.471 custom offense, versus 735 PA, 6.001 Hit/600 and 9.653 offense. Associated P90 increases from Normal 5.719 to 5.865, providing a small gain but leaving the major upside miss intact. Independent counts have a higher P90 and better score on this case, which must not be hidden by the pooled associated win. One matching calibration person and a global slope are weak support for star recovery. Tucker/Vaughn/Soto/Devers illustrate origin-known varied outcomes, not certainty about his rebound.

Origin-selected comparisons: Kyle Tucker: 674 subsequent PA, +5.33 offense; Andrew Vaughn: 615 subsequent PA, +2.72 offense; Juan Soto: 708 subsequent PA, +7.08 offense; Rafael Devers: 656 subsequent PA, +4.67 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Aaron Judge after 2016

Selection: fixed before fitting, major false low mean.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | A | 278 | 9 | 38 | 59 |
| 2014 | Aplus | 285 | 8 | 49 | 72 |
| 2015 | AA | 280 | 12 | 23 | 70 |
| 2015 | AAA | 260 | 8 | 29 | 74 |
| 2016 | AAA | 410 | 19 | 47 | 98 |
| 2016 | MLB | 95 | 4 | 9 | 42 |

Current forecast: 92.50% chance of MLB PA, 335.05 PA conditional on appearing, 309.92 expected PA, -0.040 Hit/600 and +0.936 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.169 | +0.921 | +1.694 |
| Prior Normal law | -0.153 | +0.770 | +2.375 |
| Independent counts | -0.153 | +0.717 | +2.435 |
| Associated counts | -0.233 | +0.707 | +2.589 |

Reality: 678 MLB PA, +5.557 actual Hit/600 and +8.372 delivered offense.

The independent concentration is 796.79. The associated concentration is 1425.47 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.9483. The refined calibration intersection contains 0 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.01%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.744; largest signed input contributions are age_centered +0.283, draft_class_unknown -0.206, position_9 +0.167, draft_known +0.129, pooled_mlb_quality -0.119, pooled_Aplus_BB +0.111. All saved contributions together reproduce the unchanged point rate.

Judge's 2016 record includes 410 AAA PA and nineteen HR, but also 95 MLB PA with 42 strikeouts. The scalar fit receives both; its resulting -.040 Hit/600 center and 310 expected PA remain far below the next year's 678 PA and 8.372 custom offense. Associated P90 increases from 2.375 to 2.589 and slightly improves loss, while the actual breakthrough remains nowhere near the central range. The unchanged mean of .936 is not rehabilitated by physically possible counts. No matching calibration people exist. Renfroe's active season and Moya/Waldrop/Brito's zero outcomes preserve timing uncertainty, but do not prove that a scalar model correctly translated Judge's power or weighed his brief MLB struggle.

Origin-selected comparisons: Hunter Renfroe: 479 subsequent PA, +1.57 offense; Steven Moya: 0 subsequent PA, +0.00 offense; Kyle Waldrop: 0 subsequent PA, +0.00 offense; Sócrates Brito: 0 subsequent PA, +0.00 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Ben Rortvedt after 2023

Selection: fixed before fitting, ordinary active mean.

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

Current forecast: 87.33% chance of MLB PA, 94.22 PA conditional on appearing, 82.28 expected PA, -1.102 Hit/600 and +0.104 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.052 | +0.289 |
| Prior Normal law | -0.340 | +0.004 | +0.660 |
| Independent counts | -0.293 | +0.000 | +0.629 |
| Associated counts | -0.305 | +0.000 | +0.635 |

Reality: 328 MLB PA, -1.669 actual Hit/600 and +0.103 delivered offense.

The independent concentration is 546.33. The associated concentration is 713.09 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.0910. The refined calibration intersection contains 6 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 3.23%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.790; largest signed input contributions are pooled_mlb_quality -0.370, position_2 -0.255, age_centered +0.221, reorganized -0.189, pooled_MLB_BABIP +0.140, quality_0 -0.129. All saved contributions together reproduce the unchanged point rate.

Rortvedt's input history contains 79 current MLB PA plus 124 AAA PA with six HR, sixteen walks and 31 strikeouts. The point predicts 82 expected MLB PA against 328 actual, and -1.102 Hit/600 against -1.669 actual. These two substantial component errors compensate: expected offense .104 is nearly identical to the actual .103. Both count laws remove the old 3.23 percent physically impossible joint mass; their median is zero and associated range approximately [-.305,.635] contains the outcome. This is a successful support repair and slightly better risk score, not evidence that the workload or hitting heads were individually accurate. Six refined calibration people and Herrera/Pinto/Bart/Amaya controls remain qualified. Catcher defense is not included in this offense target.

Origin-selected comparisons: Jose Herrera: 114 subsequent PA, -0.24 offense; René Pinto: 49 subsequent PA, +0.09 offense; Joey Bart: 282 subsequent PA, +1.54 offense; Miguel Amaya: 363 subsequent PA, -0.04 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Terrance Gore after 2018

Selection: fixed before fitting.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | AA | 302 | 0 | 25 | 58 |
| 2016 | MLB | 3 | 0 | 0 | 1 |
| 2017 | AA | 62 | 0 | 2 | 13 |
| 2017 | AAA | 192 | 1 | 16 | 38 |
| 2017 | MLB | 5 | 0 | 1 | 2 |
| 2018 | AAA | 205 | 0 | 19 | 49 |
| 2018 | MLB | 5 | 0 | 0 | 1 |

Current forecast: 69.23% chance of MLB PA, 41.38 PA conditional on appearing, 28.65 expected PA, -1.253 Hit/600 and +0.028 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.000 | +0.001 | +0.093 |
| Prior Normal law | -0.132 | +0.000 | +0.224 |
| Independent counts | -0.119 | +0.000 | +0.189 |
| Associated counts | -0.137 | +0.000 | +0.179 |

Reality: 58 MLB PA, +0.515 actual Hit/600 and +0.228 delivered offense.

The independent concentration is 1259.18. The associated concentration is 2740.64 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 4.7577. The refined calibration intersection contains 11 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 8.62%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.611; largest signed input contributions are draft_class_unknown -0.107, draft_elapsed -0.089, pooled_AAA_HR -0.081, pooled_AA_pa -0.071, pooled_AA_2B -0.068, draft_known +0.059. All saved contributions together reproduce the unchanged point rate.

Gore's three recent MLB samples are just three, five and five PA, while he also has substantial AA/AAA exposure and almost no HR. The saved scalar rate remains -1.253 Hit/600 and expected PA 28.65. The old Normal law put 8.62 percent on impossible joint PA/offense outcomes; both integer laws eliminate those outcomes by construction and independently verified counts. But the associated P90 falls .224 to .179, against actual 58 PA and .228 offense, and pinball loss worsens .0514 to .0652. Physical validity is necessary, not sufficient for better calibration. Eleven matching calibration people do not settle this unusual role. Kaczmarski/Cordell/Adams/Robinson preserve varied timing, and Gore's baserunning value is deliberately absent from this batting-only target.

Origin-selected comparisons: Kevin Kaczmarski: 0 subsequent PA, +0.00 offense; Ryan Cordell: 247 subsequent PA, +0.06 offense; Lane Adams: 0 subsequent PA, +0.00 offense; Drew Robinson: 7 subsequent PA, -0.09 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Aaron Judge after 2023

Selection: largest gain versus normal.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 633 | 39 | 73 | 158 |
| 2022 | MLB | 696 | 62 | 92 | 175 |
| 2023 | MLB | 458 | 37 | 79 | 130 |

Current forecast: 98.51% chance of MLB PA, 544.11 PA conditional on appearing, 536.00 expected PA, +3.360 Hit/600 and +4.661 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +2.696 | +4.879 | +6.349 |
| Prior Normal law | +2.168 | +4.650 | +7.183 |
| Independent counts | +2.132 | +4.636 | +7.428 |
| Associated counts | +2.000 | +4.701 | +7.504 |

Reality: 704 MLB PA, +7.086 actual Hit/600 and +10.493 delivered offense.

The independent concentration is 598.01. The associated concentration is 833.04 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.3428. The refined calibration intersection contains 11 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.910; largest signed input contributions are pooled_mlb_quality +2.064, quality_0 +0.581, work_0 +0.564, quality_1 +0.526, age_centered -0.445, work_2 +0.432. All saved contributions together reproduce the unchanged point rate.

This outcome-selected largest gain is Judge after 2023, not an independent confirmation case. His recent seasons contain 633, 696 and 458 PA with 39, 62 and 37 HR; the saved point combines positive pooled/current quality with lower recent workload and projects 536 expected PA and 4.661 offense. Actual 2024 production is 704 PA and 10.493 custom offense. Associated P90 rises 7.183 to 7.504 and median rises 4.650 to 4.701, reducing loss 2.245 to 2.145. The upper outcome still lies far beyond the range, so the largest gain is a softened star miss, not a correct star forecast. Eleven refined calibration people and Betts/Harper/Trout/Altuve comparisons retain interrupted and regular seasons. Do not tune the risk law to this selected gain.

Origin-selected comparisons: Mookie Betts: 516 subsequent PA, +3.81 offense; Bryce Harper: 631 subsequent PA, +4.81 offense; Mike Trout: 126 subsequent PA, +0.84 offense; Jose Altuve: 682 subsequent PA, +3.56 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Austin Hedges after 2021

Selection: largest harm versus normal.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2019 | MLB | 347 | 11 | 24 | 109 |
| 2020 | MLB | 83 | 3 | 6 | 23 |
| 2021 | MLB | 312 | 10 | 14 | 87 |

Current forecast: 97.11% chance of MLB PA, 236.35 PA conditional on appearing, 229.52 expected PA, -2.189 Hit/600 and -0.118 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | -0.231 | -0.106 | -0.023 |
| Prior Normal law | -1.215 | -0.058 | +0.917 |
| Independent counts | -1.121 | -0.069 | +0.839 |
| Associated counts | -0.998 | -0.142 | +0.864 |

Reality: 338 MLB PA, -4.770 actual Hit/600 and -1.628 delivered offense.

The independent concentration is 344.58. The associated concentration is 472.16 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.6746. The refined calibration intersection contains 14 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.19%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.847; largest signed input contributions are pooled_mlb_quality -1.056, quality_0 -0.454, work_0 +0.446, work_2 +0.327, position_2 -0.199, draft_elapsed -0.167. All saved contributions together reproduce the unchanged point rate.

Hedges is the largest selected harm against Normal. His origin-known MLB counts include 347, short-season 83 and 312 PA, with ten current HR, fourteen walks and 87 strikeouts. The point model already forecasts poor hitting at -2.189 Hit/600 and 230 expected PA, but reality is 338 PA and -4.770 Hit/600. Associated P10 moves from -1.215 to -.998, away from his actual -1.628 offense, and loss worsens .470 to .519. A global positive workload/rate relationship is not appropriate for every hitter; defense-first catchers can keep playing despite poor hitting. That explanation is a plausible mechanism, not a tested causal claim or permission for new catcher routing. Fourteen matching calibration people and Perez/Trevino/Alfaro/Heim controls make this a retained heterogeneity warning.

Origin-selected comparisons: Michael Pérez: 132 subsequent PA, -0.56 offense; Jose Trevino: 353 subsequent PA, +0.45 offense; Jorge Alfaro: 274 subsequent PA, +0.31 offense; Jonah Heim: 450 subsequent PA, +1.04 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Jorge Soler after 2018

Selection: largest gain versus independent.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | AA | 42 | 0 | 11 | 11 |
| 2016 | AAA | 7 | 0 | 0 | 5 |
| 2016 | MLB | 264 | 12 | 31 | 66 |
| 2017 | AAA | 327 | 24 | 50 | 82 |
| 2017 | MLB | 110 | 2 | 11 | 36 |
| 2018 | AAA | 10 | 0 | 2 | 6 |
| 2018 | MLB | 257 | 9 | 28 | 69 |

Current forecast: 95.96% chance of MLB PA, 375.14 PA conditional on appearing, 359.99 expected PA, +0.456 Hit/600 and +1.382 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.457 | +1.386 | +2.311 |
| Prior Normal law | +0.000 | +1.246 | +2.961 |
| Independent counts | +0.000 | +1.203 | +2.951 |
| Associated counts | -0.003 | +1.183 | +3.236 |

Reality: 679 MLB PA, +3.565 actual Hit/600 and +6.125 delivered offense.

The independent concentration is 1259.18. The associated concentration is 2740.64 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.0357. The refined calibration intersection contains 13 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.611; largest signed input contributions are work_0 +0.317, position_9 +0.165, quality_0 +0.136, pooled_AAA_BB +0.123, pooled_mlb_quality +0.110, pooled_AAA_HR +0.108. All saved contributions together reproduce the unchanged point rate.

Soler is the largest gain against independent counts. His recent record includes 327 AAA PA and 24 HR in 2017, followed by 257 MLB PA and nine HR in 2018. The saved point retains the AAA counts but projects only 360 expected PA and .456 Hit/600, yielding 1.382 custom offense versus 679 PA and 6.125 observed. Associated P90 rises from independent 2.951 to 3.236 while the median falls slightly; the higher upper tail reduces loss 1.977 to 1.895. The actual breakthrough remains outside the range. Thirteen matching calibration people and Naquin/Bonifacio/Altherr/Garcia comparisons show variable opportunity without certifying his power translation. The count reference is not a new own-player HR model, and this selected improvement must not be portrayed as correcting Soler's mean.

Origin-selected comparisons: Tyler Naquin: 294 subsequent PA, +1.40 offense; Jorge Bonifacio: 21 subsequent PA, +0.18 offense; Aaron Altherr: 66 subsequent PA, -0.75 offense; Avisaíl García: 530 subsequent PA, +2.86 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Ketel Marte after 2017

Selection: largest harm versus independent.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | AA | 8 | 0 | 1 | 0 |
| 2015 | AAA | 287 | 3 | 20 | 32 |
| 2015 | MLB | 247 | 2 | 24 | 43 |
| 2015 | RK121 | 3 | 0 | 0 | 0 |
| 2016 | AAA | 31 | 0 | 2 | 1 |
| 2016 | Aminus | 7 | 1 | 0 | 0 |
| 2016 | MLB | 466 | 1 | 18 | 84 |
| 2017 | AAA | 338 | 6 | 24 | 34 |
| 2017 | MLB | 255 | 5 | 26 | 37 |

Current forecast: 97.64% chance of MLB PA, 323.88 PA conditional on appearing, 316.22 expected PA, -0.832 Hit/600 and +0.534 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +0.177 | +0.521 | +0.916 |
| Prior Normal law | -0.684 | +0.418 | +1.935 |
| Independent counts | -0.649 | +0.418 | +2.018 |
| Associated counts | -0.610 | +0.325 | +1.894 |

Reality: 580 MLB PA, +0.389 actual Hit/600 and +2.160 delivered offense.

The independent concentration is 390.84. The associated concentration is 598.29 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 5.9077. The refined calibration intersection contains 11 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.01%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.772; largest signed input contributions are age_centered +0.359, position_6 -0.356, pooled_mlb_quality -0.285, pooled_AAA_K -0.253, quality_1 -0.207, work_0 +0.205. All saved contributions together reproduce the unchanged point rate.

Marte is the largest selected harm against independent counts. His actual history contains 466 MLB PA with one HR in 2016, then 338 AAA PA with six HR and 255 MLB PA with five HR in 2017. Age contributes positively, but position and pooled MLB quality leave a -.832 Hit/600 point and 316 expected PA. Actual next-year PA are 580 with .389 Hit/600 and 2.160 offense. Associated median .325 and P90 1.894 are below independent .418 and 2.018, so loss worsens .426 to .478. Refitting concentration while adding dependence can contract particular tails; do not describe every associated forecast as wider. Eleven matching calibration people and Moroff/Torres/Profar/Rosario retain both misses and non-arrivals. Monte Carlo case variation must be kept separate from the pooled model ranking.

Origin-selected comparisons: Max Moroff: 67 subsequent PA, -0.05 offense; Ramón Torres: 29 subsequent PA, -0.23 offense; Jurickson Profar: 594 subsequent PA, +2.83 offense; Amed Rosario: 592 subsequent PA, +0.19 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Chris Davis after 2017

Selection: major false high mean.

| Season | Level | PA | HR | Unintentional BB | K |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 670 | 47 | 78 | 208 |
| 2016 | MLB | 665 | 38 | 85 | 219 |
| 2017 | A | 4 | 0 | 0 | 1 |
| 2017 | Aplus | 5 | 0 | 1 | 2 |
| 2017 | MLB | 524 | 26 | 57 | 195 |

Current forecast: 97.51% chance of MLB PA, 515.52 PA conditional on appearing, 502.67 expected PA, +1.082 Hit/600 and +2.452 expected offense.

| Distribution | P10 | Median | P90 |
| --- | ---: | ---: | ---: |
| Workload only | +1.264 | +2.571 | +3.493 |
| Prior Normal law | +0.475 | +2.348 | +4.535 |
| Independent counts | +0.394 | +2.287 | +4.651 |
| Associated counts | +0.372 | +2.363 | +4.634 |

Reality: 522 MLB PA, -4.102 actual Hit/600 and -1.963 delivered offense.

The independent concentration is 600.19. The associated concentration is 1118.57 and slope +1.0000, within the predeclared [-1,1] interval. The positive-workload log center is 6.2996. The refined calibration intersection contains 20 earlier people. Sparse or missing intersections borrow from the global calibration.

The prior Normal impossible-outcome probability is 0.00%; integer count support permits none. Each saved arm has 4,096 verified positive draws; non-arrival is retained as a separate exact mass at zero. Sample means are not recentered.

The saved rate intercept is -0.846; largest signed input contributions are pooled_mlb_quality +0.478, work_0 +0.463, work_1 +0.409, age_centered -0.376, work_2 +0.309, position_3 +0.219. All saved contributions together reproduce the unchanged point rate.

Davis is the largest false-high point case. His latest 524 MLB PA with 26 HR, 57 walks and 195 strikeouts follow 47 and 38 HR seasons. The saved rate fit visibly carries positive pooled quality and workload contributions, partially offset by age, and retains 1.082 Hit/600 and 2.452 expected offense. His actual 522 PA are close to the forecast 503, but hitting collapses to -4.102 Hit/600 and -1.963 offense. Associated P10 .372 still fails to allow that outcome in the central range; negative-offense probability is only 3.7 percent. A modest improvement over Normal is not a successful collapse forecast, and independent counts score slightly better here. Twenty refined calibration people do not supply collapse-specific support. Duda/Thames/Zimmerman/Alonso are origin-selected controls, not hindsight evidence that every aging power hitter should be penalized similarly.

Origin-selected comparisons: Lucas Duda: 367 subsequent PA, +0.93 offense; Eric Thames: 278 subsequent PA, +0.95 offense; Ryan Zimmerman: 323 subsequent PA, +1.79 offense; Yonder Alonso: 574 subsequent PA, +1.69 offense.

Comparison limit: Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match.

## Decision and remaining limits

Retain the associated integer-count law as the next-year offense-risk research candidate, conditional on the independent Monte Carlo direction checks passing. It has coherent integer support, preserves every existing mean and shows a small development score gain against both references across all seven origins. This is a physical-distribution repair with a modest predictive benefit, not a stronger mean projection, resolved MLB readiness or full player value. All 35 slopes reach the declared bound; calibration bias, weak elite-entry support and thin-new-draftee harm remain. Preserve the independent count and physically defective Normal references, do not widen the bound or route models by favorable players, and do not deploy or change the frozen 2026 forecast. Finish the comparison evidence, then move to a clearly labeled candidate and team-filtered research explorer under the practical plan, not another uncertainty tuning sweep. Public workload, cohort totals, foreign and exceptional availability, general defense and mature long-term/control forecasts still require separate evidence.

No protected 2026 outcomes are read. The frozen forecast and deployed explorer remain
unchanged. This review does not certify public workload, elite readiness, defense,
long-term control or the complete player-value system.
