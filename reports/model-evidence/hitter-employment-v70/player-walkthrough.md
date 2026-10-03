# Roster and employment source review

No new model fitted and no existing forecast changed. Initial all-fields-maximum source audit is preserved; repaired employment announcements use recorded dates with qualified publication vintages. Nine fixed cases trace actual sources, inputs, saved paths and outcomes.

## Harrison Bader / 2023 to 2024

Player 664056, row 51242, fold 1, age 29.0. Latest captured employment: [{'transaction_id': 730389, 'player_id': 664056, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'CF Harrison Bader elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | A | 11 | 0 | 1 | 1 |
| 2021 | AAA | 3 | 0 | 1 | 1 |
| 2021 | MLB | 401 | 16 | 85 | 21 |
| 2022 | AA | 23 | 1 | 3 | 2 |
| 2022 | AAA | 4 | 0 | 0 | 1 |
| 2022 | MLB | 313 | 5 | 62 | 15 |
| 2023 | AA | 18 | 0 | 5 | 0 |
| 2023 | AAA | 21 | 0 | 3 | 2 |
| 2023 | MLB | 344 | 7 | 59 | 17 |

Existing appearance 0.656696 × active PA 213.686 = expected PA 140.326; fixed hitting -1.240591/600; offense 0.144315. Actual 437 PA and offense 0.145911. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2023, 'fold': 1, 'participation_people': 262, 'active_people': 193, 'zero_people': 111, 'source_origins': [2015, 2016, 2017, 2018, 2020, 2021, 2022]}.

Saved participation: reference -4.033199; raw additive 0.648606; linked probability 0.6566962109195358. Largest path terms:
- games_mlb_0: input 98.000000; path term +2.133544.
- games_pool_MLB: input 228.600000; path term +1.080716.
- on_40man: input 0.000000; path term -1.054582.
- work_0: input 344.000000; path term +0.705119.
- pooled_MLB_pa: input 835.000000; path term +0.428118.
- draft_rank: input 0.394128; path term +0.372404.
- quality_0: input -0.519569; path term -0.289135.
- age_centered: input 0.400000; path term +0.260778.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -1.0545824766187355}]

Saved conditional_pa: reference 283.910666; raw additive 213.685535; linked probability None. Largest path terms:
- on_40man: input 0.000000; path term -45.430389.
- work_0: input 344.000000; path term +38.241481.
- quality_0: input -0.519569; path term -34.674806.
- role_mlb_0: input 3.555556; path term -30.268869.
- regular_window_scaled: input 0.333333; path term +15.219887.
- role_pool_MLB: input 3.667225; path term -10.165473.
- pooled_MLB_K: input 0.195294; path term +7.420954.
- pooled_mlb_quality: input -0.443048; path term -7.374069.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -45.430389413060574}]

Bader elected free agency November 2; neither adapter invents a future signing. His MLB workloads 401, 313 and 344 PA support more than a fringe role, but saved roster-zero effects are -1.055 log odds and -45.43 active PA. Existing .657 appearance times 213.69 active PA gives 140.33 versus 437. The near-correct offense total remains a rate/workload cancellation. Gallo plays 260 and Vogelbach only 79; Castro plays none and Anderson five. Those failed origin-selected peers prevent granting all unsigned hitters regular jobs. Source is coherent here; the expectation needs a matched employment-context test, not flipping roster membership.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Joey Gallo | 332 | 192.17 | 260 | 0.616 | -0.104 |
| Harold Castro | 270 | 65.28 | 0 | 0.010 | 0.000 |
| Brian Anderson | 361 | 161.25 | 5 | 0.262 | -0.116 |
| Daniel Vogelbach | 319 | 192.62 | 79 | 0.700 | -0.118 |

## Bryce Harper / 2018 to 2019

Player 547180, row 32553, fold 2, age 25.0. Latest captured employment: [{'transaction_id': 381699, 'player_id': 547180, 'available_date': '2018-10-29', 'recorded_date': '2018-10-29', 'effective_date': '2018-10-29', 'resolution_date': '2018-10-29', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'RF Bryce Harper elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | MLB | 627 | 24 | 117 | 88 |
| 2017 | MLB | 492 | 29 | 99 | 57 |
| 2018 | MLB | 695 | 34 | 169 | 114 |

Existing appearance 0.931897 × active PA 578.867 = expected PA 539.445; fixed hitting 2.774512/600; offense 4.156004. Actual 682 PA and offense 5.223538. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2018, 'fold': 2, 'participation_people': 127, 'active_people': 81, 'zero_people': 59, 'source_origins': [2015, 2016, 2017]}.

Saved participation: reference -4.075952; raw additive 2.616206; linked probability 0.9318973169372777. Largest path terms:
- games_mlb_0: input 159.000000; path term +2.739951.
- MLB_0_pa: input 695.000000; path term +0.971607.
- on_40man: input 0.000000; path term -0.903873.
- games_pool_MLB: input 336.000000; path term +0.810781.
- quality_0: input 1.013842; path term +0.623833.
- pooled_MLB_pa: input 1464.800000; path term +0.487680.
- pooled_mlb_quality: input 1.508592; path term +0.419560.
- games_mlb_1: input 111.000000; path term +0.356938.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.903873475649195}]

Saved conditional_pa: reference 282.952438; raw additive 578.867455; linked probability None. Largest path terms:
- work_0: input 694.714109; path term +82.210283.
- MLB_0_pa: input 695.000000; path term +65.143013.
- role_mlb_0: input 4.349112; path term +36.711555.
- quality_0: input 1.013842; path term +34.694794.
- age_centered: input -0.400000; path term +20.851308.
- regular_window_scaled: input 1.000000; path term +20.393387.
- pooled_mlb_quality: input 1.508592; path term +18.180850.
- on_40man: input 0.000000; path term -16.948176.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -16.94817618842978}]

Harper elected free agency October 29 after 695 MLB PA/34 HR, with earlier 627 and 492 PA. Existing .932 appearance times 578.87 active PA gives 539.45 versus 682. The roster-zero path is negative, but strong production preserves substantial opportunity; the model does not universally lose free-agent stars. Machado also gets less PA than he delivers, Galvis 411 versus 589, while Davidson gets 327 versus zero and Russell 290 versus 241. Prior captured free-agent active exposure is 82 people in this actual fold, but that count is not matched elite-star support. His source zero is correct. A blanket penalty removal would not account for the weaker failures or talent differences.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Manny Machado | 709 | 587.85 | 661 | 3.465 | 3.596 |
| Addison Russell | 465 | 290.08 | 241 | 0.787 | 0.479 |
| Freddy Galvis | 656 | 410.78 | 589 | 0.603 | 1.856 |
| Matt Davidson | 496 | 327.16 | 0 | 1.122 | 0.000 |

## J.D. Martinez / 2017 to 2018

Player 502110, row 27850, fold 2, age 29.0. Latest captured employment: [{'transaction_id': 335902, 'player_id': 502110, 'available_date': '2017-11-02', 'recorded_date': '2017-11-02', 'effective_date': '2017-11-02', 'resolution_date': '2017-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'RF J.D. Martinez elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 657 | 38 | 178 | 46 |
| 2016 | AAA | 38 | 0 | 11 | 1 |
| 2016 | MLB | 517 | 22 | 128 | 47 |
| 2017 | AAA | 18 | 1 | 6 | 2 |
| 2017 | Aplus | 8 | 1 | 1 | 0 |
| 2017 | MLB | 489 | 45 | 128 | 45 |

Existing appearance 0.915062 × active PA 559.299 = expected PA 511.793; fixed hitting 3.216742/600; offense 4.318208. Actual 649 PA and offense 7.360072. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2017, 'fold': 2, 'participation_people': 88, 'active_people': 54, 'zero_people': 39, 'source_origins': [2015, 2016]}.

Saved participation: reference -4.002427; raw additive 2.377069; linked probability 0.9150618945105294. Largest path terms:
- games_mlb_0: input 119.000000; path term +2.038575.
- games_pool_MLB: input 309.800000; path term +1.493290.
- on_40man: input 0.000000; path term -0.905473.
- quality_0: input 1.546489; path term +0.896051.
- work_0: input 489.000000; path term +0.583978.
- MLB_0_pa: input 489.000000; path term +0.535912.
- games_mlb_1: input 120.000000; path term +0.367442.
- pooled_MLB_pa: input 1296.800000; path term +0.276101.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9054729022732911}]

Saved conditional_pa: reference 282.363885; raw additive 559.298645; linked probability None. Largest path terms:
- MLB_0_pa: input 489.000000; path term +71.964318.
- quality_0: input 1.546489; path term +36.410954.
- work_0: input 489.000000; path term +35.618814.
- role_pool_MLB: input 4.180113; path term +21.342705.
- pooled_MLB_K: input 0.257875; path term -20.348390.
- games_mlb_2: input 158.000000; path term +19.563924.
- role_mlb_0: input 4.100775; path term +18.435855.
- pooled_MLB_HR: input 0.063288; path term +17.140359.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -2.9971398545904817}]

Martinez elected free agency November 2 after 489 PA/45 HR, with previous workloads 657 and 517. Existing .915 appearance and 559.30 active PA give 511.79 versus 649; fixed hitting +3.217/600 also underestimates delivered offense 4.318 versus 7.360. The roster-zero conditional path is only -2.997 PA, far smaller than Wieters/Bader, while its appearance effect is -.905 log odds. Do not assign one penalty to every free agent. Goins 204 versus 120 and Morrison 466 versus 359 fail the naive more-opportunity rule; Nunez and Maybin play more. Fifty-five earlier active exposed people come from only two captured origins. A new employment representation must preserve these differences and chronology.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ryan Goins | 459 | 204.38 | 120 | 0.220 | -0.389 |
| Eduardo Núñez | 491 | 448.12 | 502 | 1.407 | 0.344 |
| Cameron Maybin | 450 | 269.08 | 384 | 0.737 | 0.371 |
| Logan Morrison | 601 | 466.28 | 359 | 2.121 | -0.003 |

## Matt Wieters / 2016 to 2017

Player 446308, row 22904, fold 3, age 30.0. Latest captured employment: [{'transaction_id': 292088, 'player_id': 446308, 'available_date': '2016-11-03', 'recorded_date': '2016-11-03', 'effective_date': '2016-11-03', 'resolution_date': '2016-11-03', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'C Matt Wieters elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | MLB | 112 | 5 | 19 | 6 |
| 2015 | AA | 13 | 0 | 0 | 1 |
| 2015 | AAA | 6 | 1 | 0 | 1 |
| 2015 | MLB | 282 | 8 | 67 | 21 |
| 2016 | MLB | 464 | 17 | 85 | 31 |

Existing appearance 0.819058 × active PA 326.397 = expected PA 267.338; fixed hitting -0.612663/600; offense 0.551905. Actual 465 PA and offense -0.233265. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2016, 'fold': 3, 'participation_people': 43, 'active_people': 25, 'zero_people': 18, 'source_origins': [2015]}.

Saved participation: reference -4.078610; raw additive 1.509979; linked probability 0.8190581458817314. Largest path terms:
- games_mlb_0: input 124.000000; path term +1.999160.
- games_pool_MLB: input 199.600000; path term +1.350464.
- on_40man: input 0.000000; path term -0.910270.
- MLB_0_pa: input 464.000000; path term +0.841811.
- pooled_MLB_pa: input 756.800000; path term +0.616043.
- draft_rank: input 0.788257; path term +0.543814.
- position_2: input 1.000000; path term +0.379769.
- age_centered: input 0.600000; path term +0.304604.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9102697831828568}]

Saved conditional_pa: reference 276.994851; raw additive 326.397024; linked probability None. Largest path terms:
- MLB_0_pa: input 464.000000; path term +87.813806.
- work_0: input 464.382208; path term +56.092583.
- role_mlb_0: input 3.761194; path term -30.826768.
- on_40man: input 0.000000; path term -17.674140.
- quality_0: input -0.132015; path term -15.980059.
- draft_elapsed: input 0.900000; path term -11.054635.
- role_pool_MLB: input 3.801527; path term -10.996335.
- pooled_MLB_HR: input 0.034314; path term +8.353914.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -17.674140338111155}]

Wieters elected free agency November 3 after 464 PA/17 HR, following 112 and 282 PA. His .819 appearance times 326.40 active PA gives 267.34 versus 465, but predicted offense +.552 versus actual -.233 shows that more PA alone can worsen offense with an optimistic fixed hitting rate. The roster-zero path contributes -.910 log odds and -17.67 active PA. Rasmus 215 versus 129 and Alvarez 285 versus 34 are failed unsigned peers, Bourjos 164 versus 203 is nearer and Plouffe 369 versus 313 also fails a universal boost. The earliest actual training head has only 25 exposed active people, all from 2015; support is materially limited. His separate 2015 conflict is cleared by November 13 MLB activation in the repaired adapter, without changing this 2016 source or forecast.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Colby Rasmus | 417 | 215.21 | 129 | 0.619 | 0.904 |
| Peter Bourjos | 383 | 164.31 | 203 | 0.258 | 0.044 |
| Trevor Plouffe | 344 | 368.81 | 313 | 1.308 | -0.523 |
| Pedro Álvarez | 376 | 285.16 | 34 | 1.165 | 0.186 |

## Jackie Bradley Jr. / 2022 to 2023

Player 598265, row 46588, fold 2, age 32.0. Latest captured employment: [{'transaction_id': 658443, 'player_id': 598265, 'available_date': '2022-11-07', 'recorded_date': '2022-11-07', 'effective_date': '2022-11-07', 'resolution_date': '2022-11-07', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'CF Jackie Bradley Jr. elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 217 | 7 | 48 | 22 |
| 2021 | MLB | 428 | 6 | 132 | 28 |
| 2022 | MLB | 370 | 4 | 77 | 24 |

Existing appearance 0.670462 × active PA 193.547 = expected PA 129.766; fixed hitting -1.951917/600; offense -0.015860. Actual 113 PA and offense -0.840479. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2022, 'fold': 2, 'participation_people': 236, 'active_people': 165, 'zero_people': 111, 'source_origins': [2015, 2016, 2017, 2018, 2020, 2021]}.

Saved participation: reference -4.106626; raw additive 0.710275; linked probability 0.670461900597898. Largest path terms:
- games_mlb_0: input 132.000000; path term +2.382579.
- on_40man: input 0.000000; path term -0.955947.
- games_pool_MLB: input 328.300000; path term +0.944318.
- work_0: input 370.000000; path term +0.652941.
- absence_window_scaled: input 0.000000; path term +0.528647.
- draft_rank: input 0.514679; path term +0.384305.
- games_mlb_1: input 134.000000; path term +0.335553.
- age_centered: input 1.000000; path term +0.320078.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9559474750244967}]

Saved conditional_pa: reference 279.630460; raw additive 193.546957; linked probability None. Largest path terms:
- work_0: input 370.000000; path term +102.994672.
- role_mlb_0: input 2.887324; path term -64.424231.
- on_40man: input 0.000000; path term -47.930906.
- quality_0: input -0.673977; path term -31.811198.
- age_centered: input 1.000000; path term -20.863546.
- regular_window_scaled: input 0.666667; path term +13.817001.
- pooled_mlb_quality: input -1.150958; path term -13.774268.
- pooled_MLB_pa: input 842.600000; path term +10.462687.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -47.930906293001954}]

Bradley elected free agency November 7 after 370 PA/four HR, following 428 PA/six HR. Existing .670 appearance times 193.55 active PA gives 129.77 versus 113, a reasonable workload estimate despite off-roster status. Fixed hitting is still too favorable: predicted offense -.016 versus actual -.840. His roster-zero -47.93 conditional-PA term therefore cannot simply be removed because Bader was low. Segura 357 versus 326 is near, Hosmer 300 versus 100 is too high, Ortega 172 versus 136 nearer and Naquin 197 versus eight a strong failure. The actual head has 168 exposed active people. Graduation or unsigned status is context, not proof of an enduring major-league role.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Jean Segura | 387 | 357.10 | 326 | 1.006 | -0.545 |
| Eric Hosmer | 419 | 300.30 | 100 | 0.808 | 0.009 |
| Rafael Ortega | 371 | 172.26 | 136 | 0.327 | 0.205 |
| Tyler Naquin | 334 | 197.01 | 8 | 0.551 | -0.179 |

## Brandon Belt / 2022 to 2023

Player 474832, row 46338, fold 3, age 34.0. Latest captured employment: [{'transaction_id': 658242, 'player_id': 474832, 'available_date': '2022-11-06', 'recorded_date': '2022-11-06', 'effective_date': '2022-11-06', 'resolution_date': '2022-11-06', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 179 | 9 | 36 | 29 |
| 2021 | AAA | 15 | 0 | 3 | 2 |
| 2021 | MLB | 381 | 29 | 103 | 45 |
| 2022 | MLB | 298 | 8 | 81 | 35 |

Existing appearance 0.411813 × active PA 273.409 = expected PA 112.593; fixed hitting 0.873587/600; offense 0.516461. Actual 404 PA and offense 3.363732. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2022, 'fold': 3, 'participation_people': 240, 'active_people': 171, 'zero_people': 110, 'source_origins': [2015, 2016, 2017, 2018, 2020, 2021]}.

Saved participation: reference -4.132366; raw additive -0.356477; linked probability 0.41181270672226444. Largest path terms:
- games_mlb_0: input 78.000000; path term +2.591331.
- games_pool_MLB: input 238.220000; path term +1.036271.
- on_40man: input 0.000000; path term -0.969836.
- games_mlb_1: input 97.000000; path term +0.319943.
- pooled_MLB_pa: input 710.200000; path term +0.318013.
- draft_rank: input 0.343442; path term +0.298000.
- pooled_AAA_pa: input 12.000000; path term +0.293248.
- age_squared: input 1.960000; path term -0.248378.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9698362717007196}]

Saved conditional_pa: reference 277.296431; raw additive 273.409336; linked probability None. Largest path terms:
- pooled_mlb_quality: input 0.980568; path term +47.298893.
- role_mlb_0: input 3.840909; path term +34.690393.
- age_centered: input 1.400000; path term -30.448295.
- on_40man: input 0.000000; path term -26.034607.
- quality_0: input -0.060737; path term -15.367508.
- role_pool_AAA: input 3.714286; path term -14.200920.
- regular_window_scaled: input 0.333333; path term +12.890862.
- MLB_0_pa: input 298.000000; path term +9.977014.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -26.034606689226464}]

Belt elected free agency November 6. At 34 his known history contains 381 PA/29 HR followed by 298 PA/eight HR; the short 2020 workload is 179 PA/nine HR, not a normal full-season failure. Existing .412 appearance times 273.41 active PA gives 112.59 versus 404 and offense .516 versus 3.364. Roster-zero terms are -.970 log odds and -26.03 active PA, but production, age and absence also contribute; changing a single flag is not a validated solution. Solano 129 versus 450 and Moustakas 81 versus 386 are analogous low forecasts; Hernandez gets 111 versus zero and Dickerson 96 versus 152 retains weaker comparables. The next Belt case is an essential same-player failure control for any increased confidence.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Donovan Solano | 304 | 128.57 | 450 | 0.377 | 2.585 |
| Yadiel Hernandez | 327 | 110.97 | 0 | 0.191 | 0.000 |
| Corey Dickerson | 297 | 96.33 | 152 | 0.187 | 0.112 |
| Mike Moustakas | 285 | 80.64 | 386 | 0.143 | 0.802 |

## Brandon Belt / 2023 to 2024

Player 474832, row 50571, fold 3, age 35.0. Latest captured employment: [{'transaction_id': 732859, 'player_id': 474832, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 15 | 0 | 3 | 2 |
| 2021 | MLB | 381 | 29 | 103 | 45 |
| 2022 | MLB | 298 | 8 | 81 | 35 |
| 2023 | MLB | 404 | 19 | 141 | 60 |

Existing appearance 0.646312 × active PA 377.769 = expected PA 244.156; fixed hitting 0.686486/600; offense 1.035277. Actual 0 PA and offense 0.000000. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2023, 'fold': 3, 'participation_people': 265, 'active_people': 189, 'zero_people': 122, 'source_origins': [2015, 2016, 2017, 2018, 2020, 2021, 2022]}.

Saved participation: reference -4.123068; raw additive 0.602869; linked probability 0.6463123100952929. Largest path terms:
- games_mlb_0: input 103.000000; path term +2.580560.
- on_40man: input 0.000000; path term -0.978755.
- games_pool_MLB: input 223.600000; path term +0.875240.
- quality_0: input 0.648045; path term +0.709231.
- pooled_MLB_pa: input 871.000000; path term +0.466982.
- age_squared: input 2.560000; path term -0.275326.
- pooled_AAA_pa: input 9.000000; path term +0.259565.
- draft_rank: input 0.343442; path term +0.243766.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9787546792654374}]

Saved conditional_pa: reference 277.623139; raw additive 377.768520; linked probability None. Largest path terms:
- work_0: input 404.000000; path term +87.671906.
- quality_0: input 0.648045; path term +44.240605.
- pooled_mlb_quality: input 0.969809; path term +32.012103.
- age_centered: input 1.600000; path term -31.061479.
- on_40man: input 0.000000; path term -23.505989.
- pooled_MLB_K: input 0.299279; path term -21.585037.
- regular_window_scaled: input 0.333333; path term +18.270526.
- role_pool_MLB: input 3.899829; path term -16.671716.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -23.50598879802772}]

Belt elected free agency November 2 after rebounding to 404 PA/19 HR, but also 141 strikeouts. At 35 the existing .646 appearance times 377.77 active PA gives 244.16, yet he supplies zero MLB PA. His preceding season was underpredicted, but automatic unsigned-veteran optimism would worsen this forecast. The roster-zero effects remain negative; a reasonable employment model still needs exit risk and age/role differences rather than declaring all roster zeros erroneous. Origin-selected Peralta, Solano, Martinez and Pham all play again, so their successes cannot guarantee Belt's return. Actual active exposure is 192 distinct earlier people, not evidence the individual exit was predictable. The source date repair preserves this genuinely unsigned state and both of his contrasting cases.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| David Peralta | 422 | 163.94 | 260 | 0.219 | 1.054 |
| Donovan Solano | 450 | 233.68 | 309 | 0.579 | 1.357 |
| J.D. Martinez | 479 | 311.72 | 495 | 1.431 | 1.452 |
| Tommy Pham | 481 | 238.36 | 478 | 0.523 | 0.650 |

## Ryan Zimmerman / 2021 to 2022

Player 475582, row 42118, fold 1, age 36.0. Latest captured employment: [{'transaction_id': 523223, 'player_id': 475582, 'available_date': '2021-11-03', 'recorded_date': '2021-11-03', 'effective_date': '2021-11-03', 'resolution_date': '2021-11-03', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '3B Ryan Zimmerman elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2019 | AA | 23 | 0 | 2 | 2 |
| 2019 | Aplus | 26 | 0 | 4 | 4 |
| 2019 | MLB | 190 | 6 | 39 | 17 |
| 2021 | MLB | 273 | 14 | 77 | 16 |

Existing appearance 0.260870 × active PA 200.263 = expected PA 52.242; fixed hitting -1.101872/600; offense 0.067772. Actual 0 PA and offense 0.000000. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2021, 'fold': 1, 'participation_people': 206, 'active_people': 150, 'zero_people': 84, 'source_origins': [2015, 2016, 2017, 2018, 2020]}.

Saved participation: reference -4.036917; raw additive -1.041452; linked probability 0.2608698605987553. Largest path terms:
- games_mlb_0: input 110.000000; path term +1.742496.
- on_40man: input 0.000000; path term -0.989500.
- games_pool_MLB: input 141.200000; path term +0.817980.
- work_0: input 273.112392; path term +0.613224.
- quality_0: input 0.066084; path term +0.533467.
- pooled_MLB_pa: input 387.000000; path term +0.366516.
- absence_window_scaled: input 0.333333; path term +0.278024.
- elapsed_scaled: input 1.600000; path term -0.181301.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9894996306870338}]

Saved conditional_pa: reference 285.286365; raw additive 200.262523; linked probability None. Largest path terms:
- quality_0: input 0.066084; path term +42.206246.
- role_pool_MLB: input 2.824074; path term -23.121290.
- age_centered: input 1.800000; path term -21.632417.
- role_mlb_0: input 2.608333; path term -21.526310.
- on_40man: input 0.000000; path term -19.381010.
- work_0: input 273.112392; path term +9.977243.
- regular_window_scaled: input 0.000000; path term -8.654622.
- pooled_MLB_2B: input 0.054209; path term +8.014812.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -19.38100968635176}]

Zimmerman elected free agency November 3 after 273 PA/14 HR at 36, following a missed 2020 MLB season and only 190 MLB PA in 2019. Existing appearance .261 and 200.26 active PA give 52.24 versus zero. This modest expected contribution is an ordinary plausible retirement/exit uncertainty, not a failed star-ready projection. Removing roster-zero penalties unconditionally would increase the error. Moreland also contributes zero while Vogt, Carpenter and Suzuki play 191/154/159 PA; the source-selected peers do not permit hindsight certainty. The source says free agency at cutoff, not later retirement, and no later event is backdated. Keep exits in scoring and distinguish a low-probability optional comeback from a confirmed job.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stephen Vogt | 238 | 54.13 | 191 | 0.024 | -0.454 |
| Mitch Moreland | 252 | 36.91 | 0 | 0.087 | 0.000 |
| Matt Carpenter | 249 | 34.24 | 154 | 0.037 | 2.355 |
| Kurt Suzuki | 247 | 41.24 | 159 | 0.043 | -0.320 |

## Josh Donaldson / 2023 to 2024

Player 518626, row 50592, fold 3, age 37.0. Latest captured employment: [{'transaction_id': 730188, 'player_id': 518626, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '3B Josh Donaldson elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 543 | 26 | 114 | 72 |
| 2022 | MLB | 546 | 15 | 148 | 53 |
| 2023 | AA | 7 | 0 | 0 | 0 |
| 2023 | AAA | 35 | 3 | 6 | 9 |
| 2023 | MLB | 189 | 13 | 50 | 22 |

Existing appearance 0.371557 × active PA 167.972 = expected PA 62.411; fixed hitting -0.879579/600; offense 0.101737. Actual 0 PA and offense 0.000000. No MLB PA is not observed zero talent.

All actual input values are retained in the case file; no employment label enters these fitted heads. Captured-FA exposure in the actual earlier training fold: {'year': 2023, 'fold': 3, 'participation_people': 265, 'active_people': 189, 'zero_people': 122, 'source_origins': [2015, 2016, 2017, 2018, 2020, 2021, 2022]}.

Saved participation: reference -4.123068; raw additive -0.525544; linked probability 0.37155675011041295. Largest path terms:
- games_mlb_0: input 51.000000; path term +2.418601.
- on_40man: input 0.000000; path term -1.008084.
- games_pool_MLB: input 237.600000; path term +0.875240.
- pooled_MLB_pa: input 951.600000; path term +0.466982.
- age_squared: input 4.000000; path term -0.295079.
- draft_rank: input 0.490692; path term +0.270803.
- pooled_AAA_pa: input 35.000000; path term +0.259565.
- games_mlb_1: input 132.000000; path term +0.180530.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -1.0080836830292292}]

Saved conditional_pa: reference 277.623139; raw additive 167.971775; linked probability None. Largest path terms:
- on_40man: input 0.000000; path term -50.311315.
- work_0: input 189.000000; path term -36.058299.
- age_centered: input 2.000000; path term -28.042272.
- quality_0: input -0.219745; path term -22.010653.
- regular_window_scaled: input 0.666667; path term +18.270526.
- MLB_0_pa: input 189.000000; path term +7.997755.
- pooled_MLB_K: input 0.247052; path term -7.726816.
- role_pool_MLB: input 4.004847; path term +5.108171.

Roster path accounting, not a causal effect: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -50.3113147409743}]

Donaldson elected free agency November 2 after only 189 PA/13 HR at 37, following 543 and 546 PA and declining earlier power. Existing .372 appearance times 167.97 active PA gives 62.41 versus zero, with -.880 fixed hitting/600. Roster-zero effects are -1.008 log odds and -50.31 active PA, but the low workload is not automatically irrational. Longoria and Brantley also exit, while Carpenter and Crawford play 157 and 80. A free-agent signal must preserve this older weak/failed-role risk instead of granting a future contract. Historical employment captures support the unsigned classification; they do not support knowledge of his later retirement. No model or roster field is changed in this source audit.

| Origin-selected unlisted peer | Known PA | Existing expected PA | Actual PA | Existing offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Evan Longoria | 237 | 55.22 | 0 | 0.093 | 0.000 |
| Matt Carpenter | 237 | 52.16 | 157 | 0.120 | 0.273 |
| Brandon Crawford | 320 | 65.69 | 80 | 0.026 | -0.212 |
| Michael Brantley | 57 | 59.46 | 0 | 0.135 | 0.000 |

## Decision

The source-only audit and nine actual player reviews are complete with qualifications. Repairing explicit employment announcement dates and later MLB activation reduces eight roster/free-agent conflicts to two; preserve and flag the remaining conflicts. The original all-fields-maximum adapter is not suitable for employment. Do not silently change older medical date rules. Repaired documented unsigned current hitters have 313 actual participants versus 280.63 expected, but 82,189 expected PA versus 83,028 actual: probability and active-workload errors offset. Listed current hitters have the much larger 35,945-PA aggregate shortfall. This supports one bounded employment-context contrast, not a universal free-agent boost or a claim it will solve the entire playing-time gap. All existing forecasts remain exact; no predictive improvement is claimed.

Specify one matched, three-state employment-evidence addition to the existing two opportunity heads, preserving the independent roster listing and distinguishing current confirmed unsigned evidence, current attachment evidence and unknown/conflicting histories. Use capture coverage, actual fold support and the same successful/failed cases; no star overrides or penalty sweep. Keep hitting fixed and compare both original and fresher-list anchors, proper probability scores, PA means and delivered offense. Because FA totals already approximately reconcile, a better probability score cannot justify multiplying unchanged active PA blindly. Review the public information cutoff mismatch separately: ranks are preseason while jobs/health remain December. After the bounded contrast, select and hand off a coherent practical candidate with remaining limits; do not extend another micro-feature queue. Goal active; protected 2026 closed.
