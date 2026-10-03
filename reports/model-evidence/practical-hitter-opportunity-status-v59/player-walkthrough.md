# Player review of dated hitter opportunity records

All 30,506 historical next-year forecasts remain. Batting talent is exact; this tests appearance and workload only.
The twelve cases include seven fixed diagnostics, largest delivered gain/harm, false high/low and an ordinary case.
Peers use only same-origin stage/debut, age, current/prior MLB exposure, minor exposure and roster-listing distance.
They are baseball-use comparisons, not matched medical/legal cases. Outcomes never select peers.
Captured transaction versions are cutoff-eligible, not certified original historical publication snapshots.
Current roster non-listing is not loss of organizational rights. Activation is not medical recovery.
Full inputs, eligibility, support and both saved-model decompositions are in cases.json.

## Aaron Judge using information through 2022

Forecast for MLB 2023; selection: fixed diagnostic.
Age 30; stage Current MLB; historical position code 8; roster flag 0.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 114 | 32 | 10 | 9 |
| 2021 | MLB | 633 | 158 | 73 | 39 |
| 2022 | MLB | 696 | 175 | 92 | 62 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (320.60 + 23) / (1270.80 + 100) = 0.250657. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (0.00 + 23) / (0.00 + 100) = 0.230000. Missing exposure returns the fixed prior, not observed average ability.

Captured context: organization_acquired; medical scope True; captured absence days 12; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 7935 | 1047 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 997 | 771 | enabled [True, True]; on path [False, True] |
| status_acquired | 1.000 | 2444 | 543 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 1852 | 167 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 699 | 388 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 2.565 | 609 | 516 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 36 | 34 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 9 | 6 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 161 | 140 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 28 | 14 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2021-07-16; event 2021-07-16: New York Yankees placed RF Aaron Judge on the 10-day injured list..
- Known by record date 2021-07-27; event 2021-07-27: New York Yankees activated RF Aaron Judge from the 10-day injured list..
- Known by record date 2021-07-27; event 2021-07-27: New York Yankees activated RF Aaron Judge from the 10-day injured list..
- Known by record date 2022-11-06; event 2022-11-06: RF Aaron Judge elected free agency..
- Known by record date 2022-12-20; event 2022-12-20: New York Yankees signed free agent RF Aaron Judge..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 95.87% | 96.07% | 1 |
| PA conditional on any appearance | 529.15 | 525.86 | 458 |
| Expected PA | 507.29 | 505.19 | 458 |
| Batting wins per 600 PA | 3.259 | 3.259 | 5.312 |
| Batting plus replacement | 4.344 | 4.326 | 5.489 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.090535, additive output 3.196049.
Largest count-weighted tree-path terms (not causal attribution):
- games_mlb_0 = 157.000000: +3.428179.
- games_pool_MLB = 320.760000: +1.118722.
- on_40man = 0.000000: -1.017199.
- quality_0 = 2.408333: +0.935511.
- work_0 = 696.000000: +0.687840.
Status path terms: status_log_absence730 +0.027323.
Fixed-fit neutralized-status probe: 0.959271; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 277.339191, additive output 525.864861.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 696.000000: +141.934111.
- role_pool_MLB = 4.337525: +38.418087.
- quality_0 = 2.408333: +32.420325.
- role_mlb_0 = 4.407186: +22.162562.
- pooled_MLB_K = 0.250657: -21.969346.
Status path terms: status_medical_scope +2.817123; status_log_absence730 +2.532764; status_ordinary_departure +0.746095; status_capture_scope +0.167643; status_open_medical +0.076226.
Fixed-fit neutralized-status probe: 524.411055; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 77 people, conditional_pa 76 people.

December 20 re-signing is captured, despite roster flag zero. The acquisition input is available but contributes no split along his actual paths; arrival rises only 95.87% to 96.07%, conditional PA falls 529 to 526, and expected PA falls 507 to 505 versus 458. That is a slightly better workload miss but worse delivered offense because fixed batting rate 3.26 is below realized 5.31. Do not credit a repaired roster membership or better talent estimate. Mancini/Hernandez/Profar/Grossman peers include zero and substantial returns; ordinary acquisition is not proof a star has the same job risk.

Origin-known peers (baseline to status expected PA, then actual):
- Trey Mancini: 349.9 to 367.9; 263 actual.
- César Hernández: 360.3 to 355.4; 0 actual.
- Jurickson Profar: 490.8 to 465.4; 521 actual.
- Robbie Grossman: 242.5 to 244.6; 420 actual.

## Matt McLain using information through 2024

Forecast for MLB 2025; selection: fixed diagnostic.
Age 24; stage Inactive / unknown; historical position code 6; roster flag 0.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 127 | 69 | 17 |
| 2023 | AAA | 180 | 37 | 29 | 12 |
| 2023 | MLB | 403 | 115 | 31 | 16 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (92.00 + 23) / (322.40 + 100) = 0.272254. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (29.60 + 23) / (144.00 + 100) = 0.215574. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 224; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 9167 | 1201 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 1191 | 898 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 3482 | 674 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 2870 | 221 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 838 | 444 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 5.416 | 685 | 564 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 47 | 41 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 1.000 | 10 | 6 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 1.000 | 208 | 178 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 31 | 17 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2023-05-15; event 2023-05-15: Cincinnati Reds selected the contract of SS Matt McLain from Louisville Bats..
- Known by record date 2023-08-28; event 2023-08-28: Cincinnati Reds placed SS Matt McLain on the 10-day injured list. Right oblique strain..
- Known by record date 2023-10-02; event 2023-10-02: Cincinnati Reds activated SS Matt McLain from the 10-day injured list..
- Known by record date 2024-03-27; event 2024-03-27: Cincinnati Reds placed SS Matt McLain on the 10-day injured list. Left shoulder surgery..
- Known by record date 2024-03-28; event 2024-03-28: Cincinnati Reds transferred SS Matt McLain from the 10-day injured list to the 60-day injured list. Left shoulder surgery..
- Known by record date 2024-10-28; event 2024-10-28: Cincinnati Reds activated SS Matt McLain..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 53.60% | 53.26% | 1 |
| PA conditional on any appearance | 323.94 | 330.32 | 577 |
| Expected PA | 173.62 | 175.91 | 577 |
| Batting wins per 600 PA | 0.251 | 0.251 | -1.140 |
| Batting plus replacement | 0.615 | 0.623 | 0.707 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.020849, additive output 0.130448.
Largest count-weighted tree-path terms (not causal attribution):
- games_pool_MLB = 71.200000: +1.103592.
- role_pool_AA = 4.334262: +0.608600.
- on_40man = 0.000000: -0.566386.
- pooled_mlb_quality = 0.566746: +0.534154.
- draft_rank = 0.627253: +0.503983.
Status path terms: status_log_absence730 +0.051215.
Fixed-fit neutralized-status probe: 0.518776; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 278.566693, additive output 330.315190.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 0.000000: -92.739192.
- role_pool_MLB = 4.463054: +39.229876.
- pooled_mlb_quality = 0.566746: +37.318306.
- on_40man = 0.000000: -22.385778.
- pooled_AAA_HR = 0.051639: +16.633721.
Status path terms: status_ordinary_departure +0.765582; status_medical_scope +0.348002; status_capture_scope +0.166460; status_log_absence730 -0.140894; status_open_medical +0.062353.
Fixed-fit neutralized-status probe: 330.233240; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 0 people, conditional_pa 0 people.

Prior 403 MLB PA with 16 HR and 180 AAA PA with 12 HR survive; known March surgery and October activation are captured. Full-season medical-absence input is disabled for sparse distinct-player support. No actual postseason-return field splits along his path. Current zero workload subtracts about 93 conditional PA and roster non-listing about 22. Arrival remains 53%, expected PA 174 to 176 versus 577. The seemingly close batting value 0.62 versus 0.71 is cancellation of underforecast PA and an overoptimistic hitting rate, not a successful comeback projection. The young inactive medical profile has zero training people; generic inactive peers include Franco and Marcano and are not medically comparable.

Origin-known peers (baseline to status expected PA, then actual):
- Wander Franco: 83.5 to 76.1; 0 actual.
- Tucupita Marcano: 0.0 to 0.0; 0 actual.
- Sherten Apostel: 0.7 to 0.6; 0 actual.
- Mario Feliciano: 5.7 to 5.1; 0 actual.

## Gavin Lux using information through 2023

Forecast for MLB 2024; selection: fixed diagnostic.
Age 25; stage Inactive / unknown; historical position code 4; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 15 | 6 | 1 |
| 2021 | MLB | 381 | 83 | 38 | 7 |
| 2022 | MLB | 471 | 95 | 47 | 6 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (125.80 + 23) / (605.40 + 100) = 0.210944. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (9.00 + 23) / (44.40 + 100) = 0.221607. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 187; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 8581 | 1138 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 1121 | 868 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 3004 | 631 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 2366 | 193 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 787 | 422 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 5.236 | 662 | 559 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 41 | 38 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 1.000 | 10 | 7 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 1.000 | 196 | 173 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 31 | 16 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2023-03-30; event 2023-03-30: Los Angeles Dodgers placed SS Gavin Lux on the 60-day injured list. Right knee surgery..
- Known by record date 2023-11-06; event 2023-11-06: Los Angeles Dodgers activated SS Gavin Lux from the 60-day injured list..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 78.09% | 80.30% | 1 |
| PA conditional on any appearance | 277.40 | 279.14 | 487 |
| Expected PA | 216.62 | 224.14 | 487 |
| Batting wins per 600 PA | -0.243 | -0.243 | -0.388 |
| Batting plus replacement | 0.583 | 0.603 | 1.193 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.062957, additive output 1.404922.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +3.603763.
- work_0 = 0.000000: -0.597506.
- games_pool_MLB = 164.400000: +0.524422.
- games_mlb_0 = 0.000000: -0.347318.
- pooled_MLB_pa = 605.400000: +0.327795.
Status path terms: status_log_absence730 +0.098409.
Fixed-fit neutralized-status probe: 0.780236; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 277.663742, additive output 279.137540.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 0.000000: -89.229073.
- pooled_mlb_quality = 0.150719: +40.270039.
- regular_window_scaled = 0.333333: +16.781073.
- age_centered = -0.400000: +14.381837.
- on_40man = 1.000000: +13.560870.
Status path terms: status_medical_scope +2.795498; status_log_absence730 +2.719955; status_ordinary_departure +1.099275; status_capture_scope +0.420176; status_open_medical +0.124306.
Fixed-fit neutralized-status probe: 274.909793; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 4 people, conditional_pa 3 people.

471/381 prior MLB PA and dated knee surgery/November IL activation survive. Arrival rises 78.1% to 80.3%, conditional PA only 277 to 279; expected PA 217 to 224 versus 487. Captured absence has a small positive path contribution; full-season absence is disabled and offseason activation contributes no actual split. Only four profile people and three active people support this age/stage/absence intersection. Neuse/Barrera/Aquino/Plummer peers all fail to return but are not matched surgical cases. A seven-PA gain is not a recovered-player model.

Origin-known peers (baseline to status expected PA, then actual):
- Sheldon Neuse: 15.9 to 16.6; 0 actual.
- Luis Barrera: 11.8 to 11.4; 0 actual.
- Aristides Aquino: 7.9 to 7.3; 0 actual.
- Nick Plummer: 14.2 to 14.5; 0 actual.

## Fernando Tatis Jr. using information through 2022

Forecast for MLB 2023; selection: fixed diagnostic.
Age 23; stage Upper minors; historical position code 6; roster flag 0.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 61 | 26 | 17 |
| 2021 | MLB | 546 | 153 | 56 | 42 |
| 2022 | AA | 14 | 2 | 4 | 0 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (159.00 + 23) / (591.00 + 100) = 0.263386. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (0.00 + 23) / (0.00 + 100) = 0.230000. Missing exposure returns the fixed prior, not observed average ability.

Captured context: suspended_unspecified; medical scope True; captured absence days 164; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 7987 | 1070 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 1011 | 777 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 2467 | 541 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 1889 | 167 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 701 | 399 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 5.106 | 596 | 502 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 34 | 31 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 11 | 7 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 158 | 136 | enabled [True, True]; on path [False, True] |
| status_nonmedical_unresolved | 1.000 | 34 | 18 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2021-04-06; event 2021-04-06: San Diego Padres placed SS Fernando Tatis Jr. on the 10 day injured list. Left shoulder inflammation..
- Known by record date 2021-04-16; event 2021-04-16: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known by record date 2021-05-11; event 2021-05-11: San Diego Padres placed SS Fernando Tatis Jr. on the 10-day injured list..
- Known by record date 2021-05-19; event 2021-05-19: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known by record date 2021-07-31; event 2021-07-31: San Diego Padres placed SS Fernando Tatis Jr. on the 10-day injured list. Left shoulder inflammation..
- Known by record date 2021-08-15; event 2021-08-15: San Diego Padres activated SS Fernando Tatis Jr. from the 10-day injured list..
- Known by record date 2022-04-07; event 2022-04-07: San Diego Padres placed SS Fernando Tatis Jr. on the 60-day injured list. Left wrist fracture..
- Known by record date 2022-08-12; event 2022-08-12: sourced game-count suspension.

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 12.60% | 13.82% | 1 |
| PA conditional on any appearance | 275.95 | 304.96 | 635 |
| Expected PA | 34.77 | 42.15 | 635 |
| Batting wins per 600 PA | 1.289 | 1.289 | 1.271 |
| Batting plus replacement | 0.184 | 0.223 | 3.333 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.060569, additive output -1.830219.
Largest count-weighted tree-path terms (not causal attribution):
- games_pool_MLB = 199.580000: +1.155777.
- on_40man = 0.000000: -0.555267.
- games_mlb_1 = 130.000000: +0.502120.
- pooled_MLB_pa = 591.000000: +0.494390.
- absence_window_scaled = 0.333333: +0.294134.
Status path terms: status_log_absence730 +0.054400.
Fixed-fit neutralized-status probe: 0.128868; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 278.089060, additive output 304.960884.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 0.000000: -91.013678.
- pooled_mlb_quality = 1.367368: +79.028592.
- role_pool_MLB = 4.223561: +19.358437.
- role_mlb_0 = 4.000000: +18.510524.
- on_40man = 0.000000: -17.187437.
Status path terms: status_log_absence730 +5.708996; status_capture_scope -1.146777; status_ordinary_departure +1.140026; status_offseason_activation -0.426540; status_medical_scope +0.275503; status_open_medical +0.059701.
Fixed-fit neutralized-status probe: 298.094023; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 52 people, conditional_pa 31 people.

Prior 546 MLB PA/42 HR, short-season 257/17 and fourteen AA rehab PA remain. Known wrist injury and eighty-game suspension are separate from ordinary departure; departure is correctly zeroed without inventing eighty calendar days. Expected PA rises 35 to 42 versus 635, mostly through a different conditional head; appearance stays only 13.8%. Fixed hitting rate 1.289 is close to realized 1.271, so this is overwhelmingly opportunity, not erased hitting ability. The ordinary young upper-minor return profile has 52/31 people but does not identify suspended established stars. Unsuccessful peers remain. No full-absence medical signal is assigned through interrupted scope.

Origin-known peers (baseline to status expected PA, then actual):
- DJ Peters: 6.2 to 7.1; 0 actual.
- Jake Bauers: 7.3 to 8.2; 272 actual.
- Jahmai Jones: 8.5 to 8.7; 11 actual.
- Justin Williams: 4.4 to 5.9; 0 actual.

## Wander Franco using information through 2023

Forecast for MLB 2024; selection: fixed diagnostic.
Age 22; stage Current MLB; historical position code 6; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 180 | 21 | 14 | 7 |
| 2021 | MLB | 308 | 37 | 24 | 7 |
| 2022 | AAA | 25 | 3 | 4 | 0 |
| 2022 | MLB | 344 | 33 | 25 | 6 |
| 2022 | RK124 | 7 | 2 | 0 | 0 |
| 2023 | MLB | 491 | 69 | 39 | 17 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (117.60 + 23) / (951.00 + 100) = 0.133777. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (15.00 + 23) / (128.00 + 100) = 0.166667. Missing exposure returns the fixed prior, not observed average ability.

Captured context: administrative_leave; medical scope True; captured absence days 89; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 8537 | 1112 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 1105 | 824 | enabled [True, True]; on path [False, False] |
| status_acquired | 0.000 | 2964 | 611 | enabled [True, True]; on path [False, True] |
| status_minor_contract | 0.000 | 2356 | 192 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 791 | 424 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 4.500 | 631 | 513 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 40 | 36 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 8 | 5 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 193 | 164 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 1.000 | 31 | 17 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2022-05-31; event 2022-05-31: Tampa Bay Rays placed SS Wander Franco on the 10-day injured list. Right quadriceps strain..
- Known by record date 2022-06-26; event 2022-06-26: Tampa Bay Rays activated SS Wander Franco..
- Known by record date 2022-07-10; event 2022-07-10: Tampa Bay Rays placed SS Wander Franco on the 10-day injured list. Right wrist discomfort..
- Known by record date 2022-09-09; event 2022-09-09: Tampa Bay Rays activated SS Wander Franco from the 10-day injured list..
- Known by record date 2023-08-14; event 2023-08-14: Tampa Bay Rays placed SS Wander Franco on the restricted list..
- Known by record date 2023-08-22; event 2023-08-22: sourced administrative_leave.

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 98.99% | 99.05% | 0 |
| PA conditional on any appearance | 548.07 | 553.33 | not observable at zero PA |
| Expected PA | 542.52 | 548.07 | 0 |
| Batting wins per 600 PA | 1.035 | 1.035 | unobserved |
| Batting plus replacement | 2.616 | 2.643 | 0.000 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.041179, additive output 4.645677.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +2.544170.
- work_0 = 491.000000: +1.294311.
- games_mlb_0 = 112.000000: +1.235364.
- absence_window_scaled = 0.000000: +0.719221.
- pooled_mlb_quality = 0.591221: +0.497375.
Status path terms: status_log_absence730 +0.002670.
Fixed-fit neutralized-status probe: 0.990488; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 279.272710, additive output 553.328426.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 491.000000: +103.125716.
- age_centered = -1.000000: +39.722620.
- quality_0 = 0.436266: +34.343313.
- role_mlb_0 = 4.352459: +30.701343.
- role_pool_MLB = 4.301215: +25.814864.
Status path terms: status_log_absence730 +4.401921; status_ordinary_departure +0.809457; status_capture_scope +0.495868; status_acquired -0.307619; status_open_medical +0.173697.
Fixed-fit neutralized-status probe: 548.652504; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 232 people, conditional_pa 224 people.

Known August restricted-list/administrative-leave records reach the source, but the unresolved nonmedical feature has no actual path contribution. Arrival remains 99%; expected PA rises 543 to 548 versus zero. Existing games, recent workload and positive roster listing overwhelm a rare unresolved status. This is not a reasonable stand-alone availability mean. Legal uncertainty does not justify retroactively applying a permanent-zero rule; it needs an explicitly unresolved scenario with authority to change presentation. Greene/Gorman/Harris/Abrams are useful baseball-use peers, not legal-risk comparables. Their healthy career risk must not teach indefinite leave.

Origin-known peers (baseline to status expected PA, then actual):
- Riley Greene: 508.0 to 504.8; 584 actual.
- Nolan Gorman: 414.1 to 413.3; 402 actual.
- Michael Harris II: 532.1 to 530.9; 470 actual.
- CJ Abrams: 535.8 to 544.2; 602 actual.

## Mike Ford using information through 2023

Forecast for MLB 2024; selection: fixed diagnostic.
Age 30; stage Current MLB; historical position code 10; roster flag 0.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 307 | 81 | 33 | 14 |
| 2021 | MLB | 72 | 23 | 10 | 3 |
| 2022 | AAA | 137 | 17 | 23 | 2 |
| 2022 | MLB | 149 | 40 | 17 | 3 |
| 2023 | AAA | 211 | 30 | 33 | 13 |
| 2023 | MLB | 251 | 81 | 24 | 16 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (126.80 + 23) / (413.40 + 100) = 0.291780. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (92.20 + 23) / (504.80 + 100) = 0.190476. Missing exposure returns the fixed prior, not observed average ability.

Captured context: mlb_scope_exit; medical scope True; captured absence days 9; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 8537 | 1112 | enabled [True, True]; on path [False, True] |
| status_medical_scope | 1.000 | 1105 | 824 | enabled [True, True]; on path [False, True] |
| status_acquired | 1.000 | 2964 | 611 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 1.000 | 2356 | 192 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 1.000 | 791 | 424 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 2.303 | 631 | 513 | enabled [True, True]; on path [False, True] |
| status_open_medical | 0.000 | 40 | 36 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 8 | 5 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 193 | 164 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 31 | 17 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2022-03-16; event 2022-03-16: Seattle Mariners signed free agent 1B Mike Ford to a minor league contract and invited him to spring training..
- Known by record date 2022-04-19; event 2022-04-19: Seattle Mariners selected the contract of 1B Mike Ford from Tacoma Rainiers..
- Known by record date 2022-04-25; event 2022-04-25: Seattle Mariners designated 1B Mike Ford for assignment..
- Known by record date 2022-05-11; event 2022-05-11: San Francisco Giants designated 1B Mike Ford for assignment..
- Known by record date 2022-05-12; event 2022-05-12: San Francisco Giants traded 1B Mike Ford to Seattle Mariners for cash..
- Known by record date 2022-05-13; event 2022-05-13: Seattle Mariners activated 1B Mike Ford..
- Known by record date 2022-06-05; event 2022-06-05: Seattle Mariners designated 1B Mike Ford for assignment..
- Known by record date 2022-06-10; event 2022-06-10: Atlanta Braves claimed 1B Mike Ford off waivers from Seattle Mariners..
- Known by record date 2022-06-20; event 2022-06-20: Atlanta Braves recalled 1B Mike Ford and  from Gwinnett Stripers..
- Known by record date 2022-07-08; event 2022-07-08: Atlanta Braves recalled 1B Mike Ford from Gwinnett Stripers..
- Known by record date 2022-07-24; event 2022-07-24: Atlanta Braves recalled 1B Mike Ford from Gwinnett Stripers..
- Known by record date 2022-08-02; event 2022-08-02: Atlanta Braves placed 1B Mike Ford on the 10-day injured list. Neck strain..
- Known by record date 2022-08-10; event 2022-08-10: Atlanta Braves released 1B Mike Ford..
- Known by record date 2022-08-10; event 2022-08-10: Atlanta Braves released 1B Mike Ford..
- Known by record date 2022-08-10; event 2022-08-10: Atlanta Braves designated 1B Mike Ford for assignment..
- Known by record date 2022-08-16; event 2022-08-16: Los Angeles Angels signed free agent 1B Mike Ford to a minor league contract..
- Known by record date 2022-08-25; event 2022-08-25: Los Angeles Angels selected the contract of 1B Mike Ford from Salt Lake Bees..
- Known by record date 2022-09-28; event 2022-09-28: Los Angeles Angels designated 1B Mike Ford for assignment..
- Known by record date 2023-01-09; event 2023-01-09: Seattle Mariners signed free agent 1B Mike Ford to a minor league contract..
- Known by record date 2023-06-02; event 2023-06-02: Seattle Mariners selected the contract of 1B Mike Ford from Tacoma Rainiers..
- Known by record date 2023-11-14; event 2023-11-14: Seattle Mariners designated 1B Mike Ford for assignment..
- Known by record date 2023-11-17; event 2023-11-17: 1B Mike Ford elected free agency..
- Known by record date 2022-04-25; event 2022-04-25: Seattle Mariners optioned 1B Mike Ford to Tacoma Rainiers..
- Known by record date 2022-05-03; event 2022-05-03: San Francisco Giants optioned 1B Mike Ford to Sacramento River Cats..
- Known by record date 2022-06-10; event 2022-06-10: Atlanta Braves optioned 1B Mike Ford to Gwinnett Stripers..
- Known by record date 2022-07-04; event 2022-07-04: Atlanta Braves optioned 1B Mike Ford to Gwinnett Stripers..
- Known by record date 2022-07-11; event 2022-07-11: Atlanta Braves optioned 1B Mike Ford to Gwinnett Stripers..
- Known by record date 2022-10-02; event 2022-10-02: Los Angeles Angels sent 1B Mike Ford outright to Salt Lake Bees..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 60.55% | 60.50% | 1 |
| PA conditional on any appearance | 223.48 | 223.83 | 62 |
| Expected PA | 135.31 | 135.41 | 62 |
| Batting wins per 600 PA | -0.286 | -0.286 | -6.845 |
| Batting plus replacement | 0.354 | 0.355 | -0.515 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.041179, additive output 0.426207.
Largest count-weighted tree-path terms (not causal attribution):
- games_mlb_0 = 84.000000: +1.833610.
- on_40man = 0.000000: -1.002476.
- absence_window_scaled = 0.000000: +0.719221.
- work_0 = 251.000000: +0.686820.
- games_pool_MLB = 137.200000: +0.640495.
Status path terms: none.
Fixed-fit neutralized-status probe: 0.604968; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 279.272710, additive output 223.826650.
Largest count-weighted tree-path terms (not causal attribution):
- quality_0 = 0.224978: +59.978839.
- work_0 = 251.000000: -22.073457.
- role_mlb_0 = 3.095745: -21.882763.
- on_40man = 0.000000: -21.806945.
- role_pool_MLB = 3.080163: -19.068825.
Status path terms: status_ordinary_departure -6.550612; status_log_absence730 +4.275385; status_capture_scope +0.495868; status_medical_scope +0.382282; status_open_medical +0.173697.
Fixed-fit neutralized-status probe: 225.207118; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 349 people, conditional_pa 323 people.

251 MLB PA/16 HR and 211 AAA PA/13 HR survive, together with January minor contract, June selection and November DFA/free agency. Minor-contract flag is a trailing-year event, not his December contract. Ordinary departure subtracts 6.55 conditional PA along the candidate path, but absence/other refit effects offset it; expected PA is essentially unchanged at 135 versus 62. Four origin-selected marginal peers have zero future PA. Departure is relevant source information, but this fit does not meaningfully distinguish remaining organizational opportunity.

Origin-known peers (baseline to status expected PA, then actual):
- Jonathan Davis: 45.9 to 48.4; 0 actual.
- Matt Beaty: 28.0 to 27.4; 0 actual.
- Jordan Luplow: 56.9 to 60.5; 0 actual.
- Greg Allen: 34.8 to 39.1; 0 actual.

## Wyatt Langford using information through 2023

Forecast for MLB 2024; selection: fixed diagnostic.
Age 21; stage Upper minors; historical position code 7; roster flag 0.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 7 | 11 | 4 |
| 2023 | AAA | 26 | 6 | 6 | 0 |
| 2023 | Aplus | 106 | 18 | 18 | 5 |
| 2023 | RK121 | 14 | 3 | 1 | 1 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (0.00 + 23) / (0.00 + 100) = 0.230000. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (6.00 + 23) / (26.00 + 100) = 0.230159. Missing exposure returns the fixed prior, not observed average ability.

Captured context: unknown; medical scope False; captured absence days None; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 8614 | 1154 | enabled [True, True]; on path [True, True] |
| status_medical_scope | 0.000 | 1128 | 881 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 3054 | 647 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 2420 | 199 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 772 | 432 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 0.000 | 662 | 567 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 42 | 41 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 8 | 6 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 205 | 178 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 26 | 16 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- No captured eligible context. This is not evidence of health or lack of organizational interest.

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 20.18% | 21.27% | 1 |
| PA conditional on any appearance | 213.56 | 210.02 | 557 |
| Expected PA | 43.10 | 44.66 | 557 |
| Batting wins per 600 PA | 0.688 | 0.688 | 0.077 |
| Batting plus replacement | 0.183 | 0.189 | 1.796 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.070535, additive output -1.309016.
Largest count-weighted tree-path terms (not causal attribution):
- role_pool_AA = 4.272727: +0.965841.
- draft_rank = 0.817615: +0.685269.
- pooled_AA_pa = 54.000000: +0.452439.
- role_minor_0 = 4.444444: +0.402560.
- on_40man = 0.000000: -0.401907.
Status path terms: status_capture_scope +0.010503; status_log_absence730 -0.000207.
Fixed-fit neutralized-status probe: 0.212652; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 279.220757, additive output 210.020446.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 0.000000: -97.300328.
- role_pool_AAA = 4.400000: +36.974530.
- on_40man = 0.000000: -18.801622.
- age_centered = -1.200000: +16.843383.
- role_pool_AA = 4.272727: +15.452087.
Status path terms: status_capture_scope -1.119200; status_ordinary_departure +0.814632; status_log_absence730 -0.240170; status_medical_scope -0.219219; status_open_medical +0.188618.
Fixed-fit neutralized-status probe: 210.020446; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 2430 people, conditional_pa 587 people.

All two hundred minor PA, levels and fourth-overall draft evidence remain. Medical scope is unknown rather than healthy, and neutralizing status signals leaves both candidate heads exact. Expected PA changes 43 to 45 versus 557 solely through refitting the broader model, not a new injury or signing fact. Broad profile support 2430/587 people hides the rare fast-college-draft pathway; Bannister/Veen/Wilken/Morales peers selected on stage, age and exposure all have zero next-year PA and are not equally matched draft/performance prospects. This status experiment cannot settle fast-entry talent or readiness.

Origin-known peers (baseline to status expected PA, then actual):
- Zion Bannister: 0.2 to 0.2; 0 actual.
- Zac Veen: 85.2 to 84.0; 0 actual.
- Brock Wilken: 6.4 to 5.5; 0 actual.
- Yohandy Morales: 5.5 to 5.1; 0 actual.

## Christian Encarnacion-Strand using information through 2023

Forecast for MLB 2024; selection: largest delivered gain.
Age 23; stage Current MLB; historical position code 3; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | A | 92 | 26 | 5 | 4 |
| 2022 | AA | 208 | 52 | 9 | 12 |
| 2022 | Aplus | 330 | 85 | 29 | 20 |
| 2023 | AAA | 316 | 69 | 32 | 20 |
| 2023 | MLB | 241 | 69 | 14 | 13 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (69.00 + 23) / (241.00 + 100) = 0.269795. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (69.00 + 23) / (316.00 + 100) = 0.221154. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 0; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 8614 | 1154 | enabled [True, True]; on path [True, True] |
| status_medical_scope | 1.000 | 1128 | 881 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 3054 | 647 | enabled [True, True]; on path [True, False] |
| status_minor_contract | 0.000 | 2420 | 199 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 772 | 432 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 0.000 | 662 | 567 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 42 | 41 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 8 | 6 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 205 | 178 | enabled [True, True]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 26 | 16 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2022-08-02; event 2022-08-02: Cincinnati Reds traded RHP Tyler Mahle to Minnesota Twins for SS Spencer Steer, 3B Christian Encarnacion-Strand and LHP Steve Hajjar..
- Known by record date 2023-07-17; event 2023-07-17: Cincinnati Reds selected the contract of 3B Christian Encarnacion-Strand from Louisville Bats..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 96.80% | 97.29% | 1 |
| PA conditional on any appearance | 492.34 | 454.71 | 123 |
| Expected PA | 476.58 | 442.39 | 123 |
| Batting wins per 600 PA | 1.006 | 1.006 | -4.720 |
| Batting plus replacement | 2.275 | 2.112 | -0.587 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.070535, additive output 3.581257.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +3.042599.
- games_mlb_0 = 63.000000: +1.419414.
- games_pool_MLB = 63.000000: +0.650682.
- MLB_0_pa = 241.000000: +0.525303.
- quality_0 = 0.246650: +0.395164.
Status path terms: status_capture_scope +0.045363; status_acquired -0.001403; status_log_absence730 -0.000207.
Fixed-fit neutralized-status probe: 0.972913; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 279.220757, additive output 454.710823.
Largest count-weighted tree-path terms (not causal attribution):
- quality_0 = 0.246650: +56.989140.
- pooled_AAA_HR = 0.055288: +38.237543.
- pooled_mlb_quality = 0.246650: +38.134143.
- role_mlb_0 = 3.849315: +32.296347.
- age_centered = -0.800000: +32.048678.
Status path terms: status_capture_scope -1.119200; status_ordinary_departure +0.814632; status_medical_scope +0.256826; status_log_absence730 -0.240170; status_open_medical +0.168944.
Fixed-fit neutralized-status probe: 454.710823; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 255 people, conditional_pa 248 people.

Largest delivered-value gain, but not an identified injury win. AAA 316 PA/20 HR and MLB 241/13 feed the unchanged positive hitting projection; expected PA falls 477 to 442 versus 123 and fixed batting rate remains +1.006 versus realized -4.720. His status signals are neutral and the fixed-fit neutralization leaves both heads exact. It is a refit tradeoff that reduces a major false high, not evidence a later injury was known. Naylor/Gelof/Vientos/Henry Davis peers have varied opportunities; retain all of them.

Origin-known peers (baseline to status expected PA, then actual):
- Bo Naylor: 386.2 to 381.7; 389 actual.
- Zack Gelof: 466.2 to 484.6; 547 actual.
- Mark Vientos: 243.2 to 259.4; 454 actual.
- Henry Davis: 295.0 to 283.7; 122 actual.

## Yordan Alvarez using information through 2022

Forecast for MLB 2023; selection: largest delivered harm.
Age 25; stage Current MLB; historical position code 10; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 9 | 1 | 0 | 1 |
| 2021 | MLB | 598 | 145 | 47 | 33 |
| 2022 | MLB | 561 | 106 | 69 | 37 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (222.60 + 23) / (1044.80 + 100) = 0.214535. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (0.00 + 23) / (0.00 + 100) = 0.230000. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 102; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 7902 | 1026 | enabled [True, True]; on path [False, False] |
| status_medical_scope | 1.000 | 982 | 730 | enabled [True, True]; on path [False, False] |
| status_acquired | 0.000 | 2414 | 526 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 1848 | 169 | enabled [True, True]; on path [True, False] |
| status_ordinary_departure | 0.000 | 706 | 390 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 4.635 | 581 | 473 | enabled [True, True]; on path [True, True] |
| status_open_medical | 1.000 | 35 | 32 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 8 | 5 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 154 | 129 | enabled [True, True]; on path [True, False] |
| status_nonmedical_unresolved | 0.000 | 26 | 14 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2021-04-14; event 2021-04-14: Houston Astros placed 1B Yordan Alvarez on the 10 day injured list..
- Known by record date 2021-04-20; event 2021-04-20: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known by record date 2021-04-28; event 2021-04-28: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list..
- Known by record date 2021-04-30; event 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known by record date 2021-04-30; event 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known by record date 2021-04-30; event 2021-04-30: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known by record date 2021-07-05; event 2021-07-05: Houston Astros activated 1B Yordan Alvarez from the paternity list..
- Known by record date 2022-04-15; event 2022-04-15: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list..
- Known by record date 2022-04-18; event 2022-04-18: Houston Astros activated 1B Yordan Alvarez from the 10-day injured list..
- Known by record date 2022-07-10; event 2022-07-10: Houston Astros placed 1B Yordan Alvarez on the 10-day injured list. Right hand inflammation..
- Known by record date 2022-07-21; event 2022-07-21: Houston Astros activated 1B Yordan Alvarez from the reserve list..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 98.96% | 98.86% | 1 |
| PA conditional on any appearance | 516.95 | 494.46 | 496 |
| Expected PA | 511.58 | 488.81 | 496 |
| Batting wins per 600 PA | 2.814 | 2.814 | 5.273 |
| Batting plus replacement | 4.001 | 3.823 | 5.912 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.052710, additive output 4.460478.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +2.689550.
- games_mlb_0 = 135.000000: +2.161034.
- work_0 = 561.000000: +0.995232.
- games_pool_MLB = 253.440000: +0.616291.
- quality_0 = 1.738114: +0.586629.
Status path terms: status_minor_contract +0.003489; status_log_absence730 +0.002342; status_offseason_activation +0.001914.
Fixed-fit neutralized-status probe: 0.988575; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 279.661910, additive output 494.455131.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 561.000000: +115.684333.
- role_mlb_0 = 4.144828: +25.351012.
- quality_0 = 1.738114: +23.310951.
- pooled_mlb_quality = 1.967171: +22.058387.
- status_open_medical = 1.000000: -20.166466.
Status path terms: status_open_medical -20.166466; status_ordinary_departure +0.966057; status_log_absence730 +0.505611.
Fixed-fit neutralized-status probe: 513.572087; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 513 people, conditional_pa 477 people.

Largest delivered-value harm is not the largest PA harm. Expected PA falls 512 to 489 versus 496, improving workload while making offense 4.00 to 3.82 versus 5.91 because fixed hitting rate +2.814 is well below realized +5.273. The open-medical flag subtracts about twenty conditional PA. July hand IL placement is followed by a reserve-list activation rather than explicitly named IL activation; the conservative ledger leaves a captured spell open. That does not certify he remained injured at December. Recorded subsequent MLB appearances should be checked before using this stale status as a current medical signal. This is a source qualification, not a declaration the sensible uncertainty or PA reduction was wrong.

Origin-known peers (baseline to status expected PA, then actual):
- Ryan Mountcastle: 494.4 to 498.2; 470 actual.
- Kyle Tucker: 560.7 to 557.0; 674 actual.
- Trent Grisham: 361.9 to 371.5; 555 actual.
- Gleyber Torres: 509.0 to 504.7; 672 actual.

## Chris Davis using information through 2017

Forecast for MLB 2018; selection: false high.
Age 31; stage Current MLB; historical position code 3; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 670 | 208 | 78 | 47 |
| 2016 | MLB | 665 | 219 | 85 | 38 |
| 2017 | A | 4 | 1 | 0 | 0 |
| 2017 | Aplus | 5 | 2 | 1 | 0 |
| 2017 | MLB | 524 | 195 | 57 | 26 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (495.00 + 23) / (1458.00 + 100) = 0.332478. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (0.00 + 23) / (0.00 + 100) = 0.230000. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 32; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 4495 | 611 | enabled [True, True]; on path [False, False] |
| status_medical_scope | 1.000 | 587 | 413 | enabled [True, True]; on path [False, True] |
| status_acquired | 0.000 | 941 | 222 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 696 | 77 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 303 | 161 | enabled [True, True]; on path [False, False] |
| status_log_absence730 | 3.497 | 234 | 187 | enabled [True, True]; on path [True, True] |
| status_open_medical | 0.000 | 11 | 11 | enabled [False, False]; on path [False, False] |
| status_medical_full_absence | 0.000 | 1 | 0 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 22 | 16 | enabled [True, False]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 8 | 2 | enabled [False, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2016-01-21; event 2016-01-21: Baltimore Orioles signed free agent 1B Chris Davis..
- Known by record date 2017-06-14; event 2017-06-13: Baltimore Orioles placed 1B Chris Davis on the 10-day disabled list retroactive to June 13, 2017. Right oblique strain..
- Known by record date 2017-07-14; event 2017-07-14: Baltimore Orioles activated 1B Chris Davis from the 10-day injured list..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 97.77% | 97.51% | 1 |
| PA conditional on any appearance | 518.14 | 516.45 | 522 |
| Expected PA | 506.60 | 503.62 | 522 |
| Batting wins per 600 PA | 1.082 | 1.082 | -4.102 |
| Batting plus replacement | 2.472 | 2.457 | -1.963 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.069024, additive output 3.669604.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +3.340386.
- games_mlb_0 = 128.000000: +1.584598.
- MLB_0_pa = 524.000000: +0.738826.
- games_pool_MLB = 349.600000: +0.621397.
- pooled_MLB_pa = 1458.000000: +0.424519.
Status path terms: status_log_absence730 +0.006267.
Fixed-fit neutralized-status probe: 0.975147; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 278.194218, additive output 516.454970.
Largest count-weighted tree-path terms (not causal attribution):
- MLB_0_pa = 524.000000: +86.033774.
- role_pool_MLB = 4.165740: +35.251967.
- role_mlb_0 = 4.086957: +29.406720.
- work_0 = 524.000000: +27.241813.
- pooled_Aplus_K = 0.238095: +27.060947.
Status path terms: status_log_absence730 +4.814743; status_medical_scope +0.775940.
Fixed-fit neutralized-status probe: 509.560557; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 186 people, conditional_pa 168 people.

Main false high is hitting, not playing time. Source retains 47/38/26 prior HR and 208/219/195 strikeouts across 670/665/524 PA. Expected PA 507 to 504 is near 522 actual, but fixed hitting rate stays +1.082 versus -4.102, leaving +2.46 projected offense versus -1.96 actual. Oblique placement and activation are captured and closed. Current status cannot solve a major performance collapse. Age/decline and outcome uncertainty remain distinct from the tested workload sources.

Origin-known peers (baseline to status expected PA, then actual):
- Josh Donaldson: 598.6 to 598.1; 219 actual.
- Mark Trumbo: 460.3 to 456.5; 358 actual.
- Asdrúbal Cabrera: 445.4 to 447.4; 592 actual.
- Justin Turner: 477.3 to 480.4; 426 actual.

## Aaron Judge using information through 2016

Forecast for MLB 2017; selection: false low.
Age 24; stage Current MLB; historical position code 9; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 59 | 38 | 9 |
| 2014 | Aplus | 285 | 72 | 49 | 8 |
| 2015 | AA | 280 | 70 | 23 | 12 |
| 2015 | AAA | 260 | 74 | 29 | 8 |
| 2016 | AAA | 410 | 98 | 47 | 19 |
| 2016 | MLB | 95 | 42 | 9 | 4 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (42.00 + 23) / (95.00 + 100) = 0.333333. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (157.20 + 23) / (618.00 + 100) = 0.250975. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 20; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 3686 | 502 | enabled [True, True]; on path [False, False] |
| status_medical_scope | 1.000 | 0 | 0 | enabled [True, True]; on path [False, False] |
| status_acquired | 0.000 | 530 | 135 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 368 | 40 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 166 | 89 | enabled [True, True]; on path [False, False] |
| status_log_absence730 | 3.045 | 0 | 0 | enabled [False, False]; on path [False, False] |
| status_open_medical | 0.000 | 0 | 0 | enabled [False, False]; on path [False, False] |
| status_medical_full_absence | 0.000 | 0 | 0 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 0 | 0 | enabled [False, False]; on path [False, False] |
| status_nonmedical_unresolved | 0.000 | 4 | 0 | enabled [False, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2016-08-13; event 2016-08-13: New York Yankees selected the contract of RF Aaron Judge from Scranton/Wilkes-Barre RailRiders..
- Known by record date 2016-09-14; event 2016-09-14: New York Yankees placed RF Aaron Judge on the 15-day disabled list. Right oblique strain..
- Known by record date 2016-10-03; event 2016-10-03: New York Yankees activated RF Aaron Judge from the 15-day disabled list..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 92.59% | 92.59% | 1 |
| PA conditional on any appearance | 304.04 | 304.04 | 678 |
| Expected PA | 281.50 | 281.50 | 678 |
| Batting wins per 600 PA | -0.040 | -0.040 | 5.557 |
| Batting plus replacement | 0.851 | 0.851 | 8.374 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -4.021554, additive output 2.524794.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +3.130486.
- games_mlb_0 = 27.000000: +1.179131.
- games_pool_MLB = 27.000000: +0.568563.
- scout_rank_score_0 = 0.700000: +0.299440.
- MLB_0_pa = 95.000000: +0.280294.
Status path terms: none.
Fixed-fit neutralized-status probe: 0.925862; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 276.981156, additive output 304.039468.
Largest count-weighted tree-path terms (not causal attribution):
- scout_rank_score_0 = 0.700000: +125.260278.
- MLB_0_pa = 95.000000: -63.349978.
- pooled_MLB_K = 0.333333: -23.006823.
- work_0 = 95.078254: -22.663525.
- role_pool_AAA = 4.334651: +15.520093.
Status path terms: none.
Fixed-fit neutralized-status probe: 304.039468; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 225 people, conditional_pa 187 people.

Main false low remains effectively unchanged: 281 PA versus 678 and fixed batting rate -0.040 versus +5.557. Origin AAA 410 PA/19 HR/98 K versus brief MLB 95/4/42 are visible; pooled MLB K becomes (42+23)/(95+100)=0.3333. Rankings contribute +125 conditional PA, while brief MLB exposure and strikeouts pull down. Medical signals are unsupported in this early fold and cannot cause the breakout repair. Moya/Austin/Difo/Toles peers include failed and limited returns; this missed superstar does not imply all similar debuts deserved 678 PA.

Origin-known peers (baseline to status expected PA, then actual):
- Steven Moya: 231.2 to 230.4; 0 actual.
- Tyler Austin: 91.8 to 92.4; 46 actual.
- Wilmer Difo: 202.0 to 196.6; 365 actual.
- Andrew Toles: 222.8 to 215.4; 102 actual.

## Drew Waters using information through 2022

Forecast for MLB 2023; selection: ordinary.
Age 23; stage Current MLB; historical position code 8; roster flag 1.

| Season | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 459 | 142 | 47 | 11 |
| 2022 | AAA | 353 | 98 | 36 | 12 |
| 2022 | Aplus | 12 | 3 | 1 | 1 |
| 2022 | MLB | 109 | 40 | 12 | 5 |

Rates in opportunity inputs use fixed 100-opportunity event priors, with separate leagues.
Three-year pooled counts use weights 1, 0.8 and 0.6. No new park/opponent adjustment or Statcast is introduced.
MLB pooled K: (40.00 + 23) / (109.00 + 100) = 0.301435. Missing exposure returns the fixed prior, not observed average ability.
AAA pooled K: (211.60 + 23) / (720.20 + 100) = 0.286028. Missing exposure returns the fixed prior, not observed average ability.

Captured context: reported_mlb_return; medical scope True; captured absence days 0; no recovery certified.

| Added input | Value | Participation support | Conditional PA support | Used in heads |
|---|---:|---:|---:|---|
| status_capture_scope | 1.000 | 7979 | 1051 | enabled [True, True]; on path [False, False] |
| status_medical_scope | 1.000 | 1000 | 763 | enabled [True, True]; on path [False, False] |
| status_acquired | 1.000 | 2482 | 563 | enabled [True, True]; on path [False, False] |
| status_minor_contract | 0.000 | 1899 | 174 | enabled [True, True]; on path [False, False] |
| status_ordinary_departure | 0.000 | 688 | 386 | enabled [True, True]; on path [False, True] |
| status_log_absence730 | 0.000 | 612 | 511 | enabled [True, True]; on path [False, True] |
| status_open_medical | 0.000 | 41 | 38 | enabled [True, True]; on path [False, True] |
| status_medical_full_absence | 0.000 | 9 | 5 | enabled [False, False]; on path [False, False] |
| status_offseason_activation | 0.000 | 163 | 138 | enabled [True, True]; on path [False, True] |
| status_nonmedical_unresolved | 0.000 | 26 | 13 | enabled [True, False]; on path [False, False] |

Eligible captured context records (may include versioned records):
- Known by record date 2021-11-18; event 2021-11-18: Atlanta Braves selected the contract of OF Drew Waters from Gwinnett Stripers..
- Known by record date 2022-07-11; event 2022-07-11: Atlanta Braves traded OF Drew Waters, RHP Andrew Hoffmann and 3B CJ Alexander to Kansas City Royals for Draft Pick. CBA Pick # 35..
- Known by record date 2022-08-22; event 2022-08-22: Kansas City Royals activated OF Drew Waters..
- Known by record date 2022-08-22; event 2022-08-22: Kansas City Royals recalled OF Drew Waters from Omaha Storm Chasers..
- Known by record date 2022-03-24; event 2022-03-24: Atlanta Braves optioned OF Drew Waters to Gwinnett Stripers..
- Known by record date 2022-07-11; event 2022-07-11: Kansas City Royals optioned OF Drew Waters to Omaha Storm Chasers..

| Intermediate or result | Baseline | Status candidate | Observed |
|---|---:|---:|---:|
| Appearance probability | 91.17% | 90.56% | 1 |
| PA conditional on any appearance | 273.73 | 285.97 | 337 |
| Expected PA | 249.55 | 258.99 | 337 |
| Batting wins per 600 PA | -0.081 | -0.081 | -0.496 |
| Batting plus replacement | 0.748 | 0.776 | 0.776 |

Expected PA is probability times conditional PA; offense is PA times (batting rate/600 plus origin replacement). Neither is full WAR.

Actual saved participation head: reference -3.995854, additive output 2.261637.
Largest count-weighted tree-path terms (not causal attribution):
- on_40man = 1.000000: +3.087824.
- games_mlb_0 = 32.000000: +1.104763.
- games_pool_MLB = 32.000000: +0.425442.
- quality_0 = 0.144189: +0.401354.
- age_centered = -0.800000: +0.207425.
Status path terms: none.
Fixed-fit neutralized-status probe: 0.905650; not a healthy counterfactual or validated replacement.

Actual saved conditional_pa head: reference 283.466237, additive output 285.972421.
Largest count-weighted tree-path terms (not causal attribution):
- work_0 = 109.000000: -85.128494.
- quality_0 = 0.144189: +53.037284.
- pooled_mlb_quality = 0.144189: +44.693779.
- age_centered = -0.800000: +24.085139.
- role_pool_AAA = 4.409513: +11.693699.
Status path terms: status_log_absence730 -1.790730; status_ordinary_departure +1.023924; status_open_medical +0.141529; status_offseason_activation -0.137379.
Fixed-fit neutralized-status probe: 285.972421; not a healthy counterfactual or validated replacement.

Distinct profile support: participation 420 people, conditional_pa 358 people.

Ordinary close delivered-value case illustrates error cancellation again. AAA 353 PA/12 HR and brief MLB 109/5 with 40 K survive alongside July trade and August return. Expected PA rises 250 to 259 versus 337 while unchanged rate -0.081 is above realized -0.496; projected offense 0.776 nearly matches 0.776 actual. Acquisition has no path contribution and neutralizing status leaves heads exact, so the nine-PA gain is mostly refit behavior, not newly learned trade value. Freeman/Campusano/Pratto/Downs peers include only nine PA as well as useful returns. Do not mistake close product for separately calibrated talent and workload.

Origin-known peers (baseline to status expected PA, then actual):
- Tyler Freeman: 198.8 to 202.1; 168 actual.
- Luis Campusano: 210.0 to 208.5; 174 actual.
- Nick Pratto: 295.2 to 315.5; 345 actual.
- Jeter Downs: 118.8 to 111.3; 9 actual.

## Cohort and decision checks

Public common matches: PA RMSE 138.488 to 138.375, MAE 106.871 to 106.911; Steamer 135.379 and 92.083.
Exact historical release dates remain unknown. The roughly 16 percent MAE gap remains outside the declared 15 percent practical target.
All-row PA RMSE improves 0.091 PA, but batting-value RMSE slightly worsens. Nominal paired intervals include no whole-model improvement.
The 2021-origin shortfall improves, while 2023-origin overforecast worsens. More accurate overall totals do not imply correct allocation.
Keep the sources and diagnostics qualified; do not promote this as a material workload upgrade or reject injury/status modeling generally.
Specific gaps: unsupported medical comebacks, unresolved legal restrictions, possible stale captured open injury state, and job uncertainty.
