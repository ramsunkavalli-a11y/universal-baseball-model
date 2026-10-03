# V39: completed current-MLB workload walkthrough

Expected next-calendar-year MLB PA. Future exits are included in training, and the head is chosen only from positive origin MLB PA. Nine fixed cases plus PA/value gains, harms, false highs/lows and ordinary cases; non-MLB predictions remain exactly unchanged. Same strongest batting-rate head. No protected 2026.

Exact tree-path accounting reconstructs each saved prediction but is order/correlation dependent, not SHAP or causal feature attribution. Origins, profiles and comparison distance never use subsequent success. Medical/job analogues are not supplied merely by same-stage/exposure peers.

## Aaron Judge: 2016 → 2017

Selection: Fixed diagnostic; value false low.

Age 24, current stage Current MLB, source position 9, soft roster listing 1; draft pick 32 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

Actual game/role inputs: games_mlb_0=27, role_mlb_0=3.6486, games_minor_0=93, role_minor_0=4.3689, games_mlb_1=0, role_mlb_1=4, games_minor_1=124, role_minor_1=4.3284, games_mlb_2=0, role_mlb_2=4, games_minor_2=131, role_minor_2=4.2766, games_pool_MLB=27, role_pool_MLB=3.6486, games_pool_AAA=141.8, role_pool_AAA=4.3347, games_pool_AA=50.4, role_pool_AA=4.3709, games_pool_Aplus=39.6, role_pool_Aplus=4.254, games_pool_A=39, role_pool_A=4.2204, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 143.966 | -0.05720 | 0.43085 |
| cohort | 143.966 | -0.05720 | 0.43085 |
| games | 150.205 | -0.05720 | 0.44953 |
| domain | 182.794 | -0.05720 | 0.54706 |
| Actual | 678 | 5.32988 | 8.10841 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00308809). Not full WAR or joint uncertainty.

Shared workload: reference 38.3571, raw prediction 150.2046.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 75.49870 |
| role_pool_AAA | 4.33465 | 38.92823 |
| MLB_0_pa | 95.00000 | 24.51202 |
| pooled_MLB_K | 0.33333 | -12.96341 |
| pooled_AAA_2B | 0.04318 | -12.71063 |
| age_centered | -0.60000 | 12.46271 |
| pooled_Aplus_K | 0.24428 | 9.26423 |
| role_pool_A | 4.22041 | 7.66876 |
| pooled_AA_BABIP | 0.32601 | -6.86149 |
| role_pool_AA | 4.37086 | -6.56203 |
| work_0 | 95.07825 | -6.52633 |
| pooled_A_3B | 0.00637 | 6.37567 |

Origin-domain workload: reference 253.3935, raw prediction 182.7937.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 95.00000 | -76.25987 |
| pooled_A_3B | 0.00637 | 35.09348 |
| on_40man | 1.00000 | 30.90432 |
| pooled_A_BB | 0.11544 | -25.99470 |
| pooled_A_HBP | 0.00825 | 22.25000 |
| quality_0 | -0.17509 | -22.19408 |
| role_pool_MLB | 3.64865 | 13.65231 |
| pooled_Aplus_K | 0.24428 | 13.28595 |
| work_0 | 95.07825 | -13.09001 |
| age_centered | -0.60000 | 12.49082 |
| pooled_MLB_K | 0.33333 | -11.85831 |
| role_mlb_0 | 3.64865 | -11.51915 |

Dedicated origin-MLB mapping raises PA 150→183 toward actual 678, but the 95-PA current debut remains a strong negative workload input relative to the subset reference. The unchanged near-zero batting rate also misses the later historic breakout. Decker/Marrero/Cowart receive 62/188/117 PA later; Cowart's lowered prediction is sensible while Marrero remains too low. The improvement does not justify promising a full season for every brief debut.

Origin-selected comparisons: Jaff Decker (age 26, MLB/AAA/AA PA 57/417.0/0.0; shared→domain→actual PA 32.1→31.2→62; realized contribution -0.115); Deven Marrero (age 25, MLB/AAA/AA PA 14/388.0/0.0; shared→domain→actual PA 51.3→64.5→188; realized contribution -0.447); Kaleb Cowart (age 24, MLB/AAA/AA PA 87/458.0/0.0; shared→domain→actual PA 141.7→128.8→117; realized contribution 0.123).

Dedicated training profile: 212 distinct people.

## Aaron Judge: 2024 → 2025

Selection: Fixed diagnostic.

Age 32, current stage Current MLB, source position 8, soft roster listing 1; draft pick 32 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 696 | 157 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 106 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 158 | 58 | 171 | 113 |

Actual game/role inputs: games_mlb_0=158, role_mlb_0=4.4286, games_minor_0=0, role_minor_0=4, games_mlb_1=106, role_mlb_1=4.2931, games_minor_1=0, role_minor_1=4, games_mlb_2=157, role_mlb_2=4.4072, games_minor_2=0, role_minor_2=4, games_pool_MLB=337, role_pool_MLB=4.4035, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 534.275 | 4.50176 | 5.67779 |
| cohort | 548.496 | 4.55334 | 5.87607 |
| games | 547.389 | 4.55334 | 5.86421 |
| domain | 553.210 | 4.55334 | 5.92657 |
| Actual | 679 | 6.28743 | 9.23105 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00312416). Not full WAR or joint uncertainty.

Shared workload: reference 39.3058, raw prediction 547.3890.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 704.28983 | 319.67012 |
| quality_0 | 2.79442 | 57.07445 |
| role_mlb_0 | 4.42857 | 55.27955 |
| games_mlb_2 | 157.00000 | 24.64558 |
| pooled_mlb_quality | 3.64857 | 24.50784 |
| age_centered | 1.00000 | -17.61614 |
| pooled_MLB_K | 0.25378 | -15.61215 |
| role_pool_MLB | 4.40346 | 12.92363 |
| regular_window_scaled | 1.00000 | 10.48557 |
| MLB_0_pa | 704.00000 | 9.17945 |
| on_40man | 1.00000 | 6.88015 |
| pooled_MLB_pa | 1488.00000 | 6.59268 |

Origin-domain workload: reference 255.6017, raw prediction 553.2097.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 704.28983 | 168.03638 |
| role_mlb_0 | 4.42857 | 41.73626 |
| quality_0 | 2.79442 | 32.42414 |
| role_pool_MLB | 4.40346 | 31.63342 |
| age_centered | 1.00000 | -21.76661 |
| pooled_MLB_K | 0.25378 | -15.13578 |
| games_mlb_2 | 157.00000 | 11.69001 |
| pooled_MLB_pa | 1488.00000 | 10.35332 |
| work_2 | 696.00000 | 9.43752 |
| on_40man | 1.00000 | 8.32652 |
| pooled_mlb_quality | 3.64857 | 6.65488 |
| MLB_0_pa | 704.00000 | 6.28526 |

PA rises only 547→553 against 679. The dedicated head retains positive current workload, role and production effects, with a negative age effect. Batting +4.553 remains identical. Olson falls 630→614 despite 724 actual; Castellanos falls 542→528 against 589, while Chapman rises toward a slightly lower actual. Separating origin MLB players is not a general fix for established regular PA conservatism.

Origin-selected comparisons: Nick Castellanos (age 32, MLB/AAA/AA PA 659/0.0/0.0; shared→domain→actual PA 541.5→528.4→589; realized contribution 1.309); Matt Olson (age 30, MLB/AAA/AA PA 685/0.0/0.0; shared→domain→actual PA 629.8→613.6→724; realized contribution 5.517); Matt Chapman (age 31, MLB/AAA/AA PA 647/0.0/0.0; shared→domain→actual PA 550.7→556.3→535; realized contribution 2.761).

Dedicated training profile: 239 distinct people.

## Masyn Winn: 2023 → 2024

Selection: Fixed diagnostic.

Age 21, current stage Current MLB, source position 6, soft roster listing 1; draft pick 54 (HS SR). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 284 | 61 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 37 | 2 | 40 | 6 |
| 2022 | AA | 403 | 86 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 33 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 105 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 37 | 2 | 26 | 10 |

Actual game/role inputs: games_mlb_0=37, role_mlb_0=3.766, games_minor_0=105, role_minor_0=4.6783, games_mlb_1=0, role_mlb_1=4, games_minor_1=119, role_minor_1=4.5736, games_mlb_2=0, role_mlb_2=4, games_minor_2=98, role_minor_2=4.4259, games_pool_MLB=37, role_pool_MLB=3.766, games_pool_AAA=105, role_pool_AAA=4.6783, games_pool_AA=68.8, role_pool_AA=4.599, games_pool_Aplus=48.6, role_pool_Aplus=4.2662, games_pool_A=36.6, role_pool_A=4.515, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 302.679 | -0.79951 | 0.53379 |
| cohort | 305.512 | -0.79671 | 0.54021 |
| games | 308.296 | -0.79671 | 0.54514 |
| domain | 323.978 | -0.79671 | 0.57287 |
| Actual | 637 | 0.25454 | 2.25951 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00309608). Not full WAR or joint uncertainty.

Shared workload: reference 39.2617, raw prediction 308.2962.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 94.81458 |
| age_centered | -1.20000 | 55.68056 |
| role_pool_AAA | 4.67826 | 41.17222 |
| quality_0 | -0.55760 | -24.26382 |
| work_0 | 137.00000 | 23.11482 |
| MLB_0_pa | 137.00000 | 20.68704 |
| AAA_0_pa | 498.00000 | 15.42243 |
| pooled_AAA_HR | 0.03512 | 13.39410 |
| pooled_MLB_K | 0.20675 | 11.72036 |
| role_pool_AA | 4.59898 | 9.62029 |
| pooled_MLB_3B | 0.00211 | -8.97209 |
| Aplus_1_pa | 147.00000 | 8.45085 |

Origin-domain workload: reference 257.5841, raw prediction 323.9779.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 137.00000 | -89.78229 |
| age_centered | -1.20000 | 52.50345 |
| on_40man | 1.00000 | 44.57892 |
| quality_0 | -0.55760 | -27.23175 |
| role_minor_0 | 4.67826 | 18.73121 |
| role_pool_MLB | 3.76596 | 15.71200 |
| Aplus_1_pa | 147.00000 | 14.34655 |
| pooled_mlb_quality | -0.55760 | -13.47532 |
| role_pool_AAA | 4.67826 | 11.97589 |
| pooled_MLB_K | 0.20675 | 11.39277 |
| role_pool_AA | 4.59898 | 10.34644 |
| pooled_MLB_2B | 0.02954 | -10.19011 |

PA rises 308→324 against 637. Current 137 MLB PA still has a negative workload effect, while age, roster listing and regular minor use are positive. His 498 AAA PA/105 games are present; the regular-role transition is still understated. Meadows improves toward 298, Edwards falls farther below 303, Ornelas falls toward his eventual 40. The change trades off different brief-debut outcomes rather than certifying a new arrival model.

Origin-selected comparisons: Xavier Edwards (age 23, MLB/AAA/AA PA 84/433.0/0.0; shared→domain→actual PA 192.9→175.6→303; realized contribution 2.187); Parker Meadows (age 23, MLB/AAA/AA PA 145/517.0/0.0; shared→domain→actual PA 248.0→264.1→298; realized contribution 1.211); Jonathan Ornelas (age 23, MLB/AAA/AA PA 8/517.0/0.0; shared→domain→actual PA 141.6→112.6→40; realized contribution -0.134).

Dedicated training profile: 452 distinct people.

## Spencer Steer: 2022 → 2023

Selection: Fixed diagnostic.

Age 24, current stage Current MLB, source position 5, soft roster listing 1; draft pick 90 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 280 | 65 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 45 | 10 | 32 | 35 |
| 2022 | AA | 156 | 35 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 71 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 28 | 2 | 26 | 11 |

Actual game/role inputs: games_mlb_0=28, role_mlb_0=3.8947, games_minor_0=106, role_minor_0=4.5862, games_mlb_1=0, role_mlb_1=4, games_minor_1=110, role_minor_1=4.4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=28, role_pool_MLB=3.8947, games_pool_AAA=71, role_pool_AAA=4.642, games_pool_AA=87, role_pool_AA=4.3299, games_pool_Aplus=36, role_pool_Aplus=4.487, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 183.018 | -0.23850 | 0.50027 |
| cohort | 180.375 | -0.23663 | 0.49361 |
| games | 232.946 | -0.23663 | 0.63748 |
| domain | 270.240 | -0.23663 | 0.73954 |
| Actual | 665 | 1.90921 | 4.17493 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00313097). Not full WAR or joint uncertainty.

Shared workload: reference 38.7736, raw prediction 232.9461.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 92.51759 |
| role_pool_AAA | 4.64198 | 51.32603 |
| MLB_0_pa | 108.00000 | 13.85093 |
| pooled_AA_HR | 0.04625 | 13.15550 |
| work_0 | 108.00000 | 8.67763 |
| age_centered | -0.60000 | 8.49756 |
| pooled_Aplus_K | 0.18243 | 8.47130 |
| pooled_mlb_quality | -0.08442 | -6.38608 |
| quality_0 | -0.08442 | -6.10891 |
| pooled_AAA_HR | 0.04128 | 5.68050 |
| pooled_MLB_3B | 0.00240 | -4.64255 |
| Aplus_1_pa | 208.00000 | 3.65488 |

Origin-domain workload: reference 258.8194, raw prediction 270.2403.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 108.00000 | -90.07416 |
| on_40man | 1.00000 | 44.39568 |
| pooled_Aplus_HR | 0.04129 | 21.07724 |
| role_mlb_0 | 3.89474 | 16.47875 |
| age_centered | -0.60000 | 13.76233 |
| pooled_Aplus_K | 0.18243 | 13.16227 |
| pooled_mlb_quality | -0.08442 | -13.14350 |
| role_pool_MLB | 3.89474 | 11.27868 |
| role_pool_AAA | 4.64198 | 10.70830 |
| quality_0 | -0.08442 | -8.81658 |
| pooled_AA_BB | 0.07750 | -7.90258 |
| role_pool_Aplus | 4.48696 | 7.86154 |

PA rises 233→270 against 665, with the prior upper-minor power and origin roster listing positively used. Current 108 MLB PA remains a major negative workload effect within the new subset. Freeman's reduced PA 247→176 is closer to 168, Henderson improves toward 622, but Brennan falls 321→279 despite actual 455. The branching direction is sensible for some cases but not a clear cohort improvement.

Origin-selected comparisons: Tyler Freeman (age 23, MLB/AAA/AA PA 86/343.0/0.0; shared→domain→actual PA 247.1→176.0→168; realized contribution 0.094); Gunnar Henderson (age 21, MLB/AAA/AA PA 132/295.0/208.0; shared→domain→actual PA 357.5→397.5→622; realized contribution 3.402); Will Brennan (age 24, MLB/AAA/AA PA 45/433.0/157.0; shared→domain→actual PA 321.1→278.7→455; realized contribution 0.166).

Dedicated training profile: 396 distinct people.

## Mark Vientos: 2022 → 2023

Selection: Fixed diagnostic.

Age 22, current stage Current MLB, source position 5, soft roster listing 1; draft pick 59 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 306 | 72 | 22 | 87 | 24 |
| 2021 | AAA | 43 | 11 | 3 | 13 | 7 |
| 2022 | AAA | 427 | 101 | 24 | 122 | 42 |
| 2022 | MLB | 41 | 16 | 1 | 12 | 5 |

Actual game/role inputs: games_mlb_0=16, role_mlb_0=3.1154, games_minor_0=101, role_minor_0=4.2072, games_mlb_1=0, role_mlb_1=4, games_minor_1=83, role_minor_1=4.1828, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=16, role_pool_MLB=3.1154, games_pool_AAA=109.8, role_pool_AAA=4.1853, games_pool_AA=57.6, role_pool_AA=4.213, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 244.284 | 0.26685 | 0.87349 |
| cohort | 251.473 | 0.22926 | 0.88344 |
| games | 232.806 | 0.22926 | 0.81787 |
| domain | 134.948 | 0.22926 | 0.47408 |
| Actual | 233 | -2.46020 | -0.23399 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00313097). Not full WAR or joint uncertainty.

Shared workload: reference 38.7736, raw prediction 232.8059.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 91.77802 |
| age_centered | -1.00000 | 49.56699 |
| pooled_AAA_HR | 0.05237 | 22.78740 |
| pooled_AA_HR | 0.05974 | 16.76993 |
| MLB_0_pa | 41.00000 | 13.85093 |
| work_0 | 41.00000 | -9.98284 |
| draft_rank | 0.46355 | 9.58862 |
| role_pool_AAA | 4.18531 | 8.74373 |
| pooled_MLB_pa | 41.00000 | -6.53868 |
| pooled_mlb_quality | -0.09169 | -6.40904 |
| pooled_AAA_3B | 0.00267 | 6.18297 |
| pooled_AAA_pa | 461.40000 | 4.43909 |

Origin-domain workload: reference 258.8194, raw prediction 134.9478.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 41.00000 | -112.47784 |
| on_40man | 1.00000 | 38.97665 |
| pooled_AAA_HR | 0.05237 | 17.20816 |
| age_centered | -1.00000 | 16.60934 |
| role_pool_MLB | 3.11538 | -12.14705 |
| pooled_mlb_quality | -0.09169 | -11.73073 |
| quality_0 | -0.09169 | -9.70256 |
| pooled_MLB_pa | 41.00000 | -7.75180 |
| AAA_0_pa | 427.00000 | -5.72907 |
| role_mlb_0 | 3.11538 | -5.62514 |
| pooled_AA_3B | 0.00145 | -4.27138 |
| pooled_MLB_K | 0.24823 | -4.16882 |

The formerly accurate 233-PA forecast drops to 135 against actual 233. Low current MLB exposure and a lower PA/appearance role now receive more influence in the current-MLB mapping. Delivered value moves closer only because the unchanged batting rate was too optimistic, not because both components improved. Campusano improves, Burleson loses opportunity and Lee is lowered toward 70. This is a concrete brief-debut harm, not an abstract score objection.

Origin-selected comparisons: Luis Campusano (age 23, MLB/AAA/AA PA 50/358.0/0.0; shared→domain→actual PA 162.4→184.9→174; realized contribution 1.224); Alec Burleson (age 23, MLB/AAA/AA PA 53/470.0/0.0; shared→domain→actual PA 202.5→178.6→347; realized contribution 0.503); Korey Lee (age 23, MLB/AAA/AA PA 26/446.0/0.0; shared→domain→actual PA 136.5→110.6→70; realized contribution -0.849).

Dedicated training profile: 396 distinct people.

## Franmil Reyes: 2021 → 2022

Selection: Fixed diagnostic.

Age 25, current stage Current MLB, source position 10, soft roster listing 1; draft pick None (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | MLB | 548 | 150 | 37 | 156 | 46 |
| 2020 | MLB | 241 | 59 | 9 | 69 | 24 |
| 2021 | AA | 7 | 3 | 2 | 3 | 0 |
| 2021 | AAA | 12 | 4 | 1 | 2 | 0 |
| 2021 | MLB | 466 | 115 | 30 | 149 | 40 |

Actual game/role inputs: games_mlb_0=115, role_mlb_0=4.048, games_minor_0=7, role_minor_0=3.4706, games_mlb_1=159.3, role_mlb_1=4.0725, games_minor_1=0, role_minor_1=4, games_mlb_2=150, role_mlb_2=3.675, games_minor_2=0, role_minor_2=4, games_pool_MLB=332.44, role_pool_MLB=3.9191, games_pool_AAA=4, role_pool_AAA=3.7143, games_pool_AA=3, role_pool_AA=3.6154, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 440.662 | 1.51282 | 2.49255 |
| cohort | 462.358 | 1.59790 | 2.68083 |
| games | 573.546 | 1.59790 | 3.32552 |
| domain | 579.789 | 1.59790 | 3.36171 |
| Actual | 473 | -1.42460 | 0.35789 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00313500). Not full WAR or joint uncertainty.

Shared workload: reference 38.7679, raw prediction 573.5465.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 466.19185 | 317.77793 |
| quality_0 | 0.55836 | 61.08480 |
| games_mlb_1 | 159.30000 | 41.26924 |
| role_mlb_0 | 4.04800 | 36.89854 |
| games_mlb_2 | 150.00000 | 21.62623 |
| pooled_mlb_quality | 0.68599 | 20.35523 |
| age_centered | -0.40000 | 19.97575 |
| pooled_MLB_K | 0.29496 | -17.49711 |
| pooled_MLB_HR | 0.05737 | 6.81892 |
| pooled_MLB_3B | 0.00230 | 6.80275 |
| on_40man | 1.00000 | 6.69071 |
| role_pool_MLB | 3.91915 | -6.64444 |

Origin-domain workload: reference 259.3207, raw prediction 579.7886.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 466.19185 | 120.26651 |
| role_mlb_0 | 4.04800 | 47.95400 |
| games_mlb_1 | 159.30000 | 36.43996 |
| quality_0 | 0.55836 | 31.29995 |
| age_centered | -0.40000 | 27.47258 |
| pooled_mlb_quality | 0.68599 | 25.97356 |
| pooled_MLB_K | 0.29496 | -17.97915 |
| games_mlb_2 | 150.00000 | 14.57694 |
| pooled_AAA_HR | 0.03571 | 11.00698 |
| MLB_0_pa | 466.00000 | 9.42576 |
| pooled_MLB_HR | 0.05737 | 9.15906 |
| role_pool_AAA | 3.71429 | -8.72888 |

PA remains excessive, 574→580 against 473. Sustained game use, current role and favorable recent production stay positive; 2020 games exposure is explicitly schedule-scaled. The unchanged +1.598 batting rate badly misses the subsequent decline, so the new workload makes value slightly worse. Dedicated MLB training does not infer loss of future performance or fix the previous games-driven overestimate.

Origin-selected comparisons: Manuel Margot (age 26, MLB/AAA/AA PA 464/15.0/0.0; shared→domain→actual PA 402.8→386.0→363; realized contribution 1.140); Luis Arraez (age 24, MLB/AAA/AA PA 479/9.0/0.0; shared→domain→actual PA 491.6→486.6→603; realized contribution 3.953); Willi Castro (age 24, MLB/AAA/AA PA 450/23.0/0.0; shared→domain→actual PA 349.9→353.9→392; realized contribution 0.469).

Dedicated training profile: 249 distinct people.

## Matt McLain: 2023 → 2024

Selection: Fixed diagnostic; pa false high.

Age 23, current stage Current MLB, source position 6, soft roster listing 1; draft pick 17 (4YR JR). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | Aplus | 119 | 29 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 2 | 0 | 0 | 0 |
| 2022 | AA | 452 | 103 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 40 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 89 | 16 | 115 | 31 |

Actual game/role inputs: games_mlb_0=89, role_mlb_0=4.4747, games_minor_0=40, role_minor_0=4.4, games_mlb_1=0, role_mlb_1=4, games_minor_1=103, role_minor_1=4.354, games_mlb_2=0, role_mlb_2=4, games_minor_2=31, role_minor_2=4.0488, games_pool_MLB=89, role_pool_MLB=4.4747, games_pool_AAA=40, role_pool_AAA=4.4, games_pool_AA=82.4, role_pool_AA=4.3463, games_pool_Aplus=17.4, role_pool_Aplus=4.0657, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=1.2, role_pool_RK121=3.9464, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 517.689 | 0.88748 | 2.36854 |
| cohort | 561.901 | 0.88467 | 2.56818 |
| games | 564.580 | 0.88467 | 2.58042 |
| domain | 566.636 | 0.88467 | 2.58982 |
| Actual | 0 | 0.00000 | 0.00000 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00309608). Not full WAR or joint uncertainty.

Shared workload: reference 39.1181, raw prediction 564.5798.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 403.00000 | 269.54832 |
| role_mlb_0 | 4.47475 | 54.42858 |
| quality_0 | 0.67281 | 48.02410 |
| age_centered | -0.80000 | 40.61560 |
| pooled_mlb_quality | 0.67281 | 37.86742 |
| pooled_AAA_HR | 0.05357 | 17.40213 |
| regular_window_scaled | 0.33333 | 16.11125 |
| role_pool_AAA | 4.40000 | 13.25228 |
| on_40man | 1.00000 | 11.97627 |
| draft_rank | 0.62725 | 11.35211 |
| MLB_0_pa | 403.00000 | -5.65265 |
| pooled_AAA_2B | 0.06071 | -5.10817 |

Origin-domain workload: reference 255.2548, raw prediction 566.6358.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 403.00000 | 74.86235 |
| role_mlb_0 | 4.47475 | 65.52446 |
| quality_0 | 0.67281 | 43.55459 |
| pooled_AAA_HR | 0.05357 | 26.96042 |
| age_centered | -0.80000 | 26.69828 |
| pooled_mlb_quality | 0.67281 | 17.10987 |
| on_40man | 1.00000 | 12.74954 |
| role_minor_0 | 4.40000 | 12.53519 |
| role_pool_MLB | 4.47475 | 11.16131 |
| AAA_0_pa | 180.00000 | -11.00536 |
| games_mlb_1 | 0.00000 | -8.63486 |
| position_6 | 1.00000 | 7.98194 |

False-high PA remains 565→567 against zero. Strong current debut production/role are positive origin-known signals; the later absence remains uncertain and is not conditioned away in training. Pratto/Baty/Walker are all lowered, with 0/171/178 later PA, showing that the model can reduce some risky debuts but not reliably identify this future absence. This is not a claim that McLain should have had zero forecast PA.

Origin-selected comparisons: Nick Pratto (age 24, MLB/AAA/AA PA 345/131.0/0.0; shared→domain→actual PA 309.0→270.9→0; realized contribution 0.000); Brett Baty (age 23, MLB/AAA/AA PA 389/121.0/0.0; shared→domain→actual PA 402.9→334.0→171; realized contribution 0.126); Jordan Walker (age 21, MLB/AAA/AA PA 465/135.0/0.0; shared→domain→actual PA 532.2→501.0→178; realized contribution -0.048).

Dedicated training profile: 96 distinct people.

## Gavin Lux: 2023 → 2024

Selection: Fixed diagnostic.

Age 25, current stage Inactive / unknown, source position 4, soft roster listing 1; draft pick 20 (unknown). Actual head: unchanged shared non-MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AAA | 74 | 17 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 102 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 129 | 6 | 95 | 47 |

Actual game/role inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=0, role_minor_0=4, games_mlb_1=129, role_mlb_1=3.6763, games_minor_1=0, role_minor_1=4, games_mlb_2=102, role_mlb_2=3.7589, games_minor_2=17, role_minor_2=4.2222, games_pool_MLB=164.4, role_pool_MLB=3.7007, games_pool_AAA=10.2, role_pool_AAA=4.1782, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 199.701 | -0.31786 | 0.51249 |
| cohort | 215.427 | -0.23943 | 0.58101 |
| games | 201.958 | -0.23943 | 0.54469 |
| domain | 201.958 | -0.23943 | 0.54469 |
| Actual | 487 | 0.08394 | 1.58897 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00309608). Not full WAR or joint uncertainty.

Shared workload: reference 38.9774, raw prediction 201.9575.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 90.29878 |
| work_0 | 0.00000 | -35.96423 |
| pooled_mlb_quality | 0.15072 | 29.85204 |
| age_centered | -0.40000 | 23.15710 |
| regular_window_scaled | 0.33333 | 12.96416 |
| pooled_MLB_K | 0.21094 | 11.53253 |
| role_pool_AAA | 4.17822 | 10.66561 |
| work_1 | 471.00000 | 8.54323 |
| pooled_MLB_3B | 0.01205 | 7.06104 |
| pooled_MLB_pa | 605.40000 | 7.05804 |
| games_mlb_2 | 102.00000 | -4.26213 |
| MLB_2_pa | 381.00000 | 4.05517 |

Origin-domain workload: reference 38.9774, raw prediction 201.9575.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 90.29878 |
| work_0 | 0.00000 | -35.96423 |
| pooled_mlb_quality | 0.15072 | 29.85204 |
| age_centered | -0.40000 | 23.15710 |
| regular_window_scaled | 0.33333 | 12.96416 |
| pooled_MLB_K | 0.21094 | 11.53253 |
| role_pool_AAA | 4.17822 | 10.66561 |
| work_1 | 471.00000 | 8.54323 |
| pooled_MLB_3B | 0.01205 | 7.06104 |
| pooled_MLB_pa | 605.40000 | 7.05804 |
| games_mlb_2 | 102.00000 | -4.26213 |
| MLB_2_pa | 381.00000 | 4.05517 |

Exactly unchanged 202 PA against 487 because no current MLB participation selects the old shared head. Preserved prior regular MLB game counts do not solve the absent-return job/medical context. Plummer/Ciuffo/Craig remain unchanged and have no later PA; they are generic inactive peers, not equivalent return-health profiles. The branch definition's deliberate scope limitation must remain visible.

Origin-selected comparisons: Nick Ciuffo (age 28, MLB/AAA/AA PA 0/0.0/0.0; shared→domain→actual PA 3.2→3.2→0; realized contribution 0.000); Will Craig (age 28, MLB/AAA/AA PA 0/0.0/0.0; shared→domain→actual PA 12.2→12.2→0; realized contribution 0.000); Nick Plummer (age 26, MLB/AAA/AA PA 0/0.0/0.0; shared→domain→actual PA 18.8→18.8→0; realized contribution 0.000).

No dedicated current-MLB head: unchanged previously reviewed shared-head support applies.

## Nick Kurtz: 2024 → 2025

Selection: Fixed diagnostic.

Age 21, current stage Upper minors, source position 3, soft roster listing 0; draft pick 4 (4YR JR). Actual head: unchanged shared non-MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

Actual game/role inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=12, role_minor_0=4.0909, games_mlb_1=0, role_mlb_1=4, games_minor_1=0, role_minor_1=4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=5, role_pool_AA=3.6667, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=7, role_pool_A=4.4118, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 50.494 | -0.11288 | 0.14825 |
| cohort | 42.495 | -0.13556 | 0.12316 |
| games | 29.943 | -0.13556 | 0.08678 |
| domain | 29.943 | -0.13556 | 0.08678 |
| Actual | 489 | 5.15001 | 5.72099 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00312416). Not full WAR or joint uncertainty.

Shared workload: reference 39.2894, raw prediction 29.9431.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| draft_rank | 0.81761 | 26.88670 |
| work_0 | 0.00000 | -22.95810 |
| on_40man | 0.00000 | -6.29391 |
| pooled_AA_BABIP | 0.30909 | 2.11899 |
| quality_0 | 0.00000 | -1.68712 |
| role_pool_AA | 3.66667 | -1.46317 |
| pooled_MLB_BABIP | 0.30000 | 1.42722 |
| pooled_AA_BB | 0.08696 | 1.41895 |
| role_pool_AAA | 4.00000 | -1.39732 |
| regular_window_scaled | 0.00000 | -0.97962 |
| pooled_AA_HR | 0.02609 | -0.97956 |
| pooled_MLB_BB | 0.08000 | -0.78981 |

Origin-domain workload: reference 39.2894, raw prediction 29.9431.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| draft_rank | 0.81761 | 26.88670 |
| work_0 | 0.00000 | -22.95810 |
| on_40man | 0.00000 | -6.29391 |
| pooled_AA_BABIP | 0.30909 | 2.11899 |
| quality_0 | 0.00000 | -1.68712 |
| role_pool_AA | 3.66667 | -1.46317 |
| pooled_MLB_BABIP | 0.30000 | 1.42722 |
| pooled_AA_BB | 0.08696 | 1.41895 |
| role_pool_AAA | 4.00000 | -1.39732 |
| regular_window_scaled | 0.00000 | -0.97962 |
| pooled_AA_HR | 0.02609 | -0.97956 |
| pooled_MLB_BB | 0.08000 | -0.78981 |

Exactly unchanged 30 PA against 489 because he has never played in MLB at origin. Twelve professional games and draft rank stay in the shared head; the dedicated current-MLB model cannot improve first-arrival inference. All three young high-pick comparison prospects have zero next-year PA. The exceptional entrant remains an important miss, not evidence that their common profile guarantees an MLB job.

Origin-selected comparisons: Benny Montgomery (age 21, MLB/AAA/AA PA 0/0.0/48.0; shared→domain→actual PA 40.9→40.9→0; realized contribution 0.000); Termarr Johnson (age 20, MLB/AAA/AA PA 0/0.0/57.0; shared→domain→actual PA 21.8→21.8→0; realized contribution 0.000); Walker Jenkins (age 19, MLB/AAA/AA PA 0/0.0/28.0; shared→domain→actual PA 46.6→46.6→0; realized contribution 0.000).

No dedicated current-MLB head: unchanged previously reviewed shared-head support applies.

## Trevor Story: 2024 → 2025

Selection: pa largest gain.

Age 31, current stage Current MLB, source position 6, soft roster listing 1; draft pick 45 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | AA | 7 | 2 | 1 | 1 | 1 |
| 2022 | MLB | 396 | 94 | 16 | 122 | 28 |
| 2023 | AA | 10 | 3 | 1 | 5 | 2 |
| 2023 | AAA | 38 | 10 | 3 | 8 | 5 |
| 2023 | MLB | 168 | 43 | 3 | 55 | 9 |
| 2024 | AAA | 16 | 4 | 0 | 2 | 0 |
| 2024 | MLB | 106 | 26 | 2 | 33 | 9 |

Actual game/role inputs: games_mlb_0=26, role_mlb_0=4.0556, games_minor_0=4, role_minor_0=4, games_mlb_1=43, role_mlb_1=3.9245, games_minor_1=13, role_minor_1=3.8261, games_mlb_2=94, role_mlb_2=4.1923, games_minor_2=2, role_minor_2=3.9167, games_pool_MLB=116.8, role_pool_MLB=4.0852, games_pool_AAA=12, role_pool_AAA=3.9273, games_pool_AA=3.6, role_pool_AA=3.8382, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 142.633 | -1.39208 | 0.11468 |
| cohort | 127.374 | -1.33350 | 0.11485 |
| games | 149.145 | -1.33350 | 0.13448 |
| domain | 247.262 | -1.33350 | 0.22295 |
| Actual | 654 | 0.39753 | 2.47118 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00312416). Not full WAR or joint uncertainty.

Shared workload: reference 39.3058, raw prediction 149.1446.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 93.95933 |
| pooled_MLB_K | 0.29965 | -20.71023 |
| role_pool_MLB | 4.08517 | 16.05151 |
| pooled_MLB_3B | 0.00087 | -11.21671 |
| pooled_MLB_pa | 478.00000 | 11.09043 |
| MLB_0_pa | 106.00000 | 9.16461 |
| age_centered | 0.80000 | -7.24211 |
| role_mlb_0 | 4.05556 | 6.54587 |
| pooled_mlb_quality | -0.23291 | -6.33892 |
| pooled_AAA_HR | 0.03689 | 6.11378 |
| games_mlb_0 | 26.00000 | 6.10098 |
| pooled_AA_HR | 0.03922 | 4.90913 |

Origin-domain workload: reference 255.6017, raw prediction 247.2621.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 106.04364 | -87.74324 |
| role_mlb_0 | 4.05556 | 48.22817 |
| on_40man | 1.00000 | 46.50318 |
| role_pool_MLB | 4.08517 | 26.64830 |
| pooled_MLB_K | 0.29965 | -21.44559 |
| quality_0 | 0.01458 | -10.47709 |
| position_6 | 1.00000 | 10.11119 |
| pooled_MLB_2B | 0.05606 | 7.05757 |
| pooled_MLB_3B | 0.00087 | -6.36390 |
| pooled_mlb_quality | -0.23291 | -5.65610 |
| work_1 | 168.00000 | -3.64163 |
| games_mlb_1 | 43.00000 | -3.44573 |

Largest PA gain: 149→247 against 654. Positive regular PA/appearance and roster listing partially offset a small 106-PA current season; the dedicated reference is much higher than the shared population. Talent stays −1.334 and still misses realized batting, so delivered value remains far too low 0.22 versus 2.47. Trout improves, Hedges falls farther below his modest role, Vogelbach remains near exit. This helps a known major leaguer's potential return without proving medical recovery prediction.

Origin-selected comparisons: Mike Trout (age 32, MLB/AAA/AA PA 126/1.0/0.0; shared→domain→actual PA 293.0→344.2→556; realized contribution 2.903); Austin Hedges (age 31, MLB/AAA/AA PA 146/0.0/0.0; shared→domain→actual PA 140.4→121.9→180; realized contribution -0.587); Daniel Vogelbach (age 31, MLB/AAA/AA PA 79/0.0/0.0; shared→domain→actual PA 30.3→34.7→0; realized contribution 0.000).

Dedicated training profile: 362 distinct people.

## Spencer Torkelson: 2022 → 2023

Selection: pa largest harm.

Age 22, current stage Current MLB, source position 3, soft roster listing 1; draft pick 1 (4YR JR). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 212 | 50 | 14 | 50 | 30 |
| 2021 | AAA | 177 | 40 | 11 | 36 | 22 |
| 2021 | Aplus | 141 | 31 | 5 | 28 | 24 |
| 2022 | AAA | 155 | 35 | 5 | 41 | 22 |
| 2022 | MLB | 404 | 110 | 8 | 99 | 37 |

Actual game/role inputs: games_mlb_0=110, role_mlb_0=3.7, games_minor_0=35, role_minor_0=4.3333, games_mlb_1=0, role_mlb_1=4, games_minor_1=121, role_minor_1=4.3511, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=110, role_pool_MLB=3.7, games_pool_AAA=67, role_pool_AAA=4.3714, games_pool_AA=40, role_pool_AA=4.192, games_pool_Aplus=24.8, role_pool_Aplus=4.3908, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 401.185 | 0.59155 | 1.65163 |
| cohort | 403.217 | 0.59906 | 1.66505 |
| games | 424.978 | 0.59906 | 1.75491 |
| domain | 335.198 | 0.59906 | 1.38417 |
| Actual | 684 | 0.42709 | 2.60459 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00313097). Not full WAR or joint uncertainty.

Shared workload: reference 38.5877, raw prediction 424.9783.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 404.00000 | 276.45982 |
| quality_0 | -0.44468 | -28.36363 |
| on_40man | 1.00000 | 27.45780 |
| games_pool_MLB | 110.00000 | 25.80594 |
| role_pool_AAA | 4.37143 | 23.57934 |
| age_centered | -1.00000 | 23.09239 |
| role_mlb_0 | 3.70000 | -21.32203 |
| draft_rank | 1.00000 | 21.10837 |
| role_minor_0 | 4.33333 | 19.47496 |
| pooled_AA_HR | 0.05267 | 13.78562 |
| regular_window_scaled | 0.33333 | 11.89432 |
| games_mlb_0 | 110.00000 | -4.63178 |

Origin-domain workload: reference 256.8989, raw prediction 335.1977.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 404.00000 | 88.54955 |
| role_mlb_0 | 3.70000 | -34.06681 |
| quality_0 | -0.44468 | -33.89613 |
| on_40man | 1.00000 | 22.58054 |
| age_centered | -1.00000 | 20.68828 |
| role_pool_AAA | 4.37143 | 9.68928 |
| role_pool_MLB | 3.70000 | 7.07441 |
| work_1 | 0.00000 | -5.44167 |
| pooled_Aplus_2B | 0.06485 | 5.26680 |
| pooled_Aplus_3B | 0.00611 | 5.03128 |
| role_minor_0 | 4.33333 | 4.86508 |
| pooled_mlb_quality | -0.44468 | -4.33901 |

Largest PA harm: 425→335 against 684. The current weak batting input and stabilized role ratio 3.700 are negative in the dedicated mapping, outweighing youth and draft pedigree. A struggling first year need not imply the organization will immediately reduce a highly invested player's role. Rutschman also loses PA despite a large subsequent role, while Bart's lower prediction is directionally useful and Greene varies. Investment/job context and young-player second chances remain omitted or compressed.

Origin-selected comparisons: Joey Bart (age 25, MLB/AAA/AA PA 291/31.0/0.0; shared→domain→actual PA 223.7→190.5→95; realized contribution -0.322); Adley Rutschman (age 24, MLB/AAA/AA PA 470/53.0/14.0; shared→domain→actual PA 620.7→553.6→687; realized contribution 3.957); Riley Greene (age 21, MLB/AAA/AA PA 418/68.0/0.0; shared→domain→actual PA 460.9→475.2→416; realized contribution 2.247).

Dedicated training profile: 93 distinct people.

## Cody Bellinger: 2016 → 2017

Selection: pa false low.

Age 20, current stage Upper minors, source position 3, soft roster listing 0; draft pick 124 (unknown). Actual head: unchanged shared non-MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 51 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 128 | 30 | 150 | 51 |
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |

Actual game/role inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=117, role_minor_0=4.0709, games_mlb_1=0, role_mlb_1=4, games_minor_1=128, role_minor_1=4.2319, games_mlb_2=0, role_mlb_2=4, games_minor_2=51, role_minor_2=4.4754, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=3, role_pool_AAA=4, games_pool_AA=114, role_pool_AA=4.0726, games_pool_Aplus=102.4, role_pool_Aplus=4.2278, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=30.6, role_pool_RK128=4.4286, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 35.516 | 0.08471 | 0.11469 |
| cohort | 35.516 | 0.08471 | 0.11469 |
| games | 7.761 | 0.08471 | 0.02506 |
| domain | 7.761 | 0.08471 | 0.02506 |
| Actual | 548 | 2.70047 | 4.15217 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00308809). Not full WAR or joint uncertainty.

Shared workload: reference 38.3571, raw prediction 7.7613.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 0.00000 | -12.27175 |
| work_0 | 0.00000 | -9.93732 |
| on_40man | 0.00000 | -6.10059 |
| pooled_AA_HR | 0.04602 | 4.73189 |
| pooled_Aplus_K | 0.26719 | 2.96051 |
| pooled_Aplus_HR | 0.05045 | 2.61545 |
| role_pool_AAA | 4.00000 | -2.26542 |
| quality_0 | 0.00000 | -2.14785 |
| role_pool_Aplus | 4.22776 | 1.55950 |
| pooled_AAA_HR | 0.05357 | -1.49223 |
| role_pool_AA | 4.07258 | 1.30862 |
| pooled_AA_BB | 0.11504 | -1.29906 |

Origin-domain workload: reference 38.3571, raw prediction 7.7613.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 0.00000 | -12.27175 |
| work_0 | 0.00000 | -9.93732 |
| on_40man | 0.00000 | -6.10059 |
| pooled_AA_HR | 0.04602 | 4.73189 |
| pooled_Aplus_K | 0.26719 | 2.96051 |
| pooled_Aplus_HR | 0.05045 | 2.61545 |
| role_pool_AAA | 4.00000 | -2.26542 |
| quality_0 | 0.00000 | -2.14785 |
| role_pool_Aplus | 4.22776 | 1.55950 |
| pooled_AAA_HR | 0.05357 | -1.49223 |
| role_pool_AA | 4.07258 | 1.30862 |
| pooled_AA_BB | 0.11504 | -1.29906 |

Unchanged false-low first arrival, 8 PA against 548, is outside the new head. The longer powerful AA season remains present; the source 40-man flag is zero and a three-game AAA finish provides little role evidence. MLB's later report describes a 2017 non-roster spring invitee, so this specific listing is not contradicted by that check; it is not a confirmed source error. Exposure/draft peers Westbrook/Wong/Kiner-Falefa do not arrive next year, but they are not matched prospect talent grades. A first-arrival translation gap remains.

Origin-selected comparisons: Jamie Westbrook (age 21, MLB/AAA/AA PA 0/0.0/473.0; shared→domain→actual PA 4.9→4.9→0; realized contribution 0.000); Kean Wong (age 21, MLB/AAA/AA PA 0/0.0/492.0; shared→domain→actual PA 28.1→28.1→0; realized contribution 0.000); Isiah Kiner-Falefa (age 21, MLB/AAA/AA PA 0/0.0/457.0; shared→domain→actual PA 12.7→12.7→0; realized contribution 0.000).

No dedicated current-MLB head: unchanged previously reviewed shared-head support applies.

## Wyatt Langford: 2024 → 2025

Selection: pa ordinary.

Age 22, current stage Current MLB, source position 7, soft roster listing 1; draft pick 4 (4YR JR). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | AA | 54 | 12 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 5 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 24 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 3 | 1 | 3 | 1 |
| 2024 | AAA | 11 | 3 | 0 | 0 | 1 |
| 2024 | MLB | 557 | 134 | 16 | 115 | 48 |

Actual game/role inputs: games_mlb_0=134, role_mlb_0=4.1458, games_minor_0=3, role_minor_0=3.9231, games_mlb_1=0, role_mlb_1=4, games_minor_1=44, role_minor_1=4.4444, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=134, role_pool_MLB=4.1458, games_pool_AAA=7, role_pool_AAA=4.2235, games_pool_AA=9.6, role_pool_AA=4.2449, games_pool_Aplus=19.2, role_pool_Aplus=4.274, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=2.4, role_pool_RK121=4.129, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 571.120 | 1.21220 | 2.93813 |
| cohort | 558.662 | 1.27456 | 2.93209 |
| games | 550.030 | 1.27456 | 2.88679 |
| domain | 572.928 | 1.27456 | 3.00697 |
| Actual | 573 | 1.21747 | 2.94816 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00312416). Not full WAR or joint uncertainty.

Shared workload: reference 39.6917, raw prediction 550.0298.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 557.22931 | 296.69449 |
| role_mlb_0 | 4.14583 | 55.40945 |
| quality_0 | 0.17407 | 31.42375 |
| age_centered | -1.00000 | 29.85122 |
| role_pool_MLB | 4.14583 | 18.71608 |
| regular_window_scaled | 0.33333 | 13.33011 |
| draft_rank | 0.81761 | 12.92322 |
| pooled_MLB_K | 0.21005 | 9.40785 |
| pooled_AA_K | 0.19972 | 7.28744 |
| on_40man | 1.00000 | 6.69009 |
| pooled_mlb_quality | 0.17407 | 5.24048 |
| role_pool_AA | 4.24490 | 4.17514 |

Origin-domain workload: reference 257.7800, raw prediction 572.9277.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 557.22931 | 139.27036 |
| role_mlb_0 | 4.14583 | 56.19724 |
| age_centered | -1.00000 | 33.70908 |
| role_pool_MLB | 4.14583 | 22.41130 |
| pooled_Aplus_HR | 0.03788 | 15.15453 |
| MLB_0_pa | 557.00000 | -12.65270 |
| pooled_MLB_K | 0.21005 | 12.48918 |
| on_40man | 1.00000 | 9.99969 |
| pooled_AA_BB | 0.11732 | 9.25205 |
| pooled_AA_BABIP | 0.32166 | 9.18453 |
| draft_rank | 0.81761 | 6.90266 |
| draft_rank_low_exposure | 0.09420 | 6.81857 |

Ordinary PA case improves 550→573 against actual 573. A 557-PA current season, regular role and youth all support retained opportunity; batting is unchanged and delivered value is slightly above realized value. Cowser barely changes and later receives only 360 PA, Abrams is lowered too far and Greene also loses PA despite 655 actual. One nearly exact outcome is an example, not independent certification.

Origin-selected comparisons: Colton Cowser (age 24, MLB/AAA/AA PA 561/0.0/0.0; shared→domain→actual PA 480.2→479.8→360; realized contribution 0.315); CJ Abrams (age 23, MLB/AAA/AA PA 602/0.0/0.0; shared→domain→actual PA 599.9→557.1→635; realized contribution 2.582); Riley Greene (age 23, MLB/AAA/AA PA 584/6.0/0.0; shared→domain→actual PA 529.9→523.4→655; realized contribution 3.722).

Dedicated training profile: 116 distinct people.

## Mike Trout: 2021 → 2022

Selection: value largest gain.

Age 29, current stage Current MLB, source position 8, soft roster listing 1; draft pick 25 (HS). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | MLB | 600 | 134 | 45 | 120 | 96 |
| 2020 | MLB | 241 | 53 | 17 | 56 | 31 |
| 2021 | MLB | 146 | 36 | 8 | 41 | 22 |

Actual game/role inputs: games_mlb_0=36, role_mlb_0=4.0435, games_minor_0=0, role_minor_0=4, games_mlb_1=143.1, role_mlb_1=4.4603, games_minor_1=0, role_minor_1=4, games_mlb_2=134, role_mlb_2=4.4444, games_minor_2=0, role_minor_2=4, games_pool_MLB=230.88, role_pool_MLB=4.3768, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 278.332 | 1.88104 | 1.74516 |
| cohort | 312.132 | 2.02658 | 2.03280 |
| games | 347.299 | 2.02658 | 2.26183 |
| domain | 413.243 | 2.02658 | 2.69130 |
| Actual | 499 | 4.95838 | 5.68608 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00313500). Not full WAR or joint uncertainty.

Shared workload: reference 37.6355, raw prediction 347.2995.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 81.61751 |
| pooled_mlb_quality | 1.95419 | 81.00586 |
| quality_0 | 0.67138 | 46.69995 |
| role_pool_MLB | 4.37678 | 34.65710 |
| regular_window_scaled | 0.66667 | 25.95995 |
| games_mlb_0 | 36.00000 | 14.80254 |
| MLB_0_pa | 146.00000 | 14.18313 |
| role_mlb_0 | 4.04348 | 7.41993 |
| work_0 | 146.06011 | 6.96017 |
| elapsed_scaled | 1.00000 | -5.79832 |
| MLB_2_pa | 600.00000 | 5.68195 |
| games_mlb_1 | 143.10000 | 5.01625 |

Origin-domain workload: reference 259.4405, raw prediction 413.2430.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 146.06011 | -78.13056 |
| pooled_mlb_quality | 1.95419 | 66.58043 |
| quality_0 | 0.67138 | 50.56112 |
| role_mlb_0 | 4.04348 | 46.86586 |
| role_pool_MLB | 4.37678 | 40.74249 |
| on_40man | 1.00000 | 34.19473 |
| role_mlb_2 | 4.44444 | 6.26509 |
| quality_2 | 1.85865 | 6.08802 |
| pooled_MLB_BABIP | 0.32226 | -5.94425 |
| age_centered | 0.40000 | 3.54395 |
| pooled_MLB_HR | 0.06460 | 3.45137 |
| elapsed_scaled | 1.00000 | -3.20893 |

Largest value gain: PA rises 347→413 toward 499 after a small 146-PA current season. High preserved MLB production and regular PA/appearance offset current workload loss; rate is unchanged +2.027. Value improves 2.26→2.69 against 5.69, not a complete return forecast. Piscotty/Knapp/Plawecki have much smaller later roles and lack equivalent star talent, illustrating limitations of exposure-based peer matching.

Origin-selected comparisons: Stephen Piscotty (age 30, MLB/AAA/AA PA 188/0.0/0.0; shared→domain→actual PA 193.1→186.7→139; realized contribution -0.169); Andrew Knapp (age 29, MLB/AAA/AA PA 159/12.0/0.0; shared→domain→actual PA 33.8→55.6→46; realized contribution -0.279); Kevin Plawecki (age 30, MLB/AAA/AA PA 173/0.0/0.0; shared→domain→actual PA 194.3→195.0→186; realized contribution -0.167).

Dedicated training profile: 443 distinct people.

## Joey Votto: 2016 → 2017

Selection: value largest harm.

Age 32, current stage Current MLB, source position 3, soft roster listing 1; draft pick None (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | AAA | 6 | 2 | 0 | 2 | 0 |
| 2014 | MLB | 272 | 62 | 6 | 49 | 45 |
| 2015 | MLB | 695 | 158 | 29 | 135 | 128 |
| 2016 | MLB | 677 | 158 | 29 | 120 | 93 |

Actual game/role inputs: games_mlb_0=158, role_mlb_0=4.2679, games_minor_0=0, role_minor_0=4, games_mlb_1=158, role_mlb_1=4.375, games_minor_1=0, role_minor_1=4, games_mlb_2=62, role_mlb_2=4.3333, games_minor_2=2, role_minor_2=3.8333, games_pool_MLB=321.6, role_pool_MLB=4.3311, games_pool_AAA=1.2, role_pool_AAA=3.8929, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 559.692 | 2.94190 | 4.47264 |
| cohort | 559.692 | 2.94190 | 4.47264 |
| games | 609.200 | 2.94190 | 4.86827 |
| domain | 563.974 | 2.94190 | 4.50686 |
| Actual | 707 | 4.96408 | 8.02420 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00308809). Not full WAR or joint uncertainty.

Shared workload: reference 37.9094, raw prediction 609.2000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 677.00000 | 221.78398 |
| work_0 | 677.55766 | 75.18634 |
| role_mlb_0 | 4.26786 | 60.69226 |
| quality_0 | 1.61657 | 41.36154 |
| regular_window_scaled | 0.66667 | 38.18476 |
| games_mlb_1 | 158.00000 | 37.74758 |
| role_pool_MLB | 4.33112 | 30.31746 |
| games_mlb_0 | 158.00000 | 27.97388 |
| age_centered | 1.00000 | -20.55579 |
| pooled_MLB_HR | 0.03930 | 12.05582 |
| on_40man | 1.00000 | 11.13719 |
| pooled_mlb_quality | 2.48869 | 7.44747 |

Origin-domain workload: reference 257.7324, raw prediction 563.9736.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 677.00000 | 114.91181 |
| role_mlb_0 | 4.26786 | 74.46905 |
| quality_0 | 1.61657 | 31.43631 |
| work_0 | 677.55766 | 27.24593 |
| role_pool_MLB | 4.33112 | 24.87593 |
| age_centered | 1.00000 | -23.52676 |
| games_mlb_1 | 158.00000 | 23.30004 |
| pooled_MLB_HR | 0.03930 | 16.88513 |
| games_mlb_0 | 158.00000 | 13.54759 |
| role_pool_AAA | 3.89286 | -12.14178 |
| on_40man | 1.00000 | 9.39277 |
| elapsed_scaled | 0.90000 | -7.44711 |

Largest value harm: PA falls 609→564 despite actual 707. High current 677 PA and favorable batting remain positive, but the dedicated subset mapping is less optimistic overall for this older regular. The unchanged +2.942 rate undershoots the later excellent season. Markakis' increased PA is useful, while Prado/Pedroia later lose workload; uncertain aging/availability is real, but this particular branch does not improve the whole cohort.

Origin-selected comparisons: Martín Prado (age 32, MLB/AAA/AA PA 658/0.0/0.0; shared→domain→actual PA 524.6→520.8→147; realized contribution -0.088); Nick Markakis (age 32, MLB/AAA/AA PA 684/0.0/0.0; shared→domain→actual PA 496.2→542.9→670; realized contribution 2.005); Dustin Pedroia (age 32, MLB/AAA/AA PA 698/0.0/0.0; shared→domain→actual PA 558.7→532.7→463; realized contribution 1.788).

Dedicated training profile: 121 distinct people.

## Yordan Alvarez: 2024 → 2025

Selection: value false high.

Age 27, current stage Current MLB, source position 10, soft roster listing 1; draft pick None (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

Actual game/role inputs: games_mlb_0=147, role_mlb_0=4.2994, games_minor_0=0, role_minor_0=4, games_mlb_1=114, role_mlb_1=4.3226, games_minor_1=3, role_minor_1=3.9231, games_mlb_2=135, role_mlb_2=4.1448, games_minor_2=0, role_minor_2=4, games_pool_MLB=319.2, role_pool_MLB=4.2783, games_pool_AAA=2.4, role_pool_AAA=3.9355, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 601.307 | 3.76103 | 5.64780 |
| cohort | 584.774 | 3.70970 | 5.44249 |
| games | 577.490 | 3.70970 | 5.37470 |
| domain | 562.457 | 3.70970 | 5.23479 |
| Actual | 199 | 0.91965 | 0.92510 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00312416). Not full WAR or joint uncertainty.

Shared workload: reference 39.2894, raw prediction 577.4905.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 635.26142 | 322.22229 |
| role_mlb_0 | 4.29936 | 57.46500 |
| quality_0 | 1.41565 | 52.22819 |
| pooled_mlb_quality | 2.45709 | 23.98322 |
| role_pool_MLB | 4.27825 | 18.92138 |
| quality_1 | 1.38309 | 15.95441 |
| regular_window_scaled | 1.00000 | 13.70170 |
| MLB_0_pa | 635.00000 | 12.90359 |
| pooled_MLB_HR | 0.05789 | 12.80523 |
| pooled_MLB_K | 0.17379 | 9.69534 |
| role_mlb_1 | 4.32258 | -8.68616 |
| age_centered | 0.00000 | 8.61492 |

Origin-domain workload: reference 254.8770, raw prediction 562.4574.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 635.26142 | 159.68642 |
| role_mlb_0 | 4.29936 | 61.12131 |
| quality_0 | 1.41565 | 32.56420 |
| pooled_mlb_quality | 2.45709 | 19.19226 |
| role_pool_MLB | 4.27825 | 11.41933 |
| pooled_MLB_K | 0.17379 | 9.87149 |
| MLB_0_pa | 635.00000 | 9.77095 |
| age_centered | 0.00000 | 9.65189 |
| on_40man | 1.00000 | 8.05459 |
| pooled_MLB_HR | 0.05789 | 6.39386 |
| games_mlb_2 | 135.00000 | -3.88369 |
| work_1 | 496.00000 | -3.56669 |

False-high value shrinks modestly through lower PA 577→562, still far above actual 199. Favorable prior production/use are reasonable inputs; no origin-certified diagnosis identifies this later absence. The unchanged +3.710 batting rate and large role forecast create 5.23 wins versus 0.93 realized. De La Cruz is raised despite only 50 later PA, another harmful job/retention uncertainty case; the model is not selectively solving absences.

Origin-selected comparisons: Gleyber Torres (age 27, MLB/AAA/AA PA 665/0.0/0.0; shared→domain→actual PA 591.9→581.3→628; realized contribution 3.070); Willi Castro (age 27, MLB/AAA/AA PA 635/0.0/0.0; shared→domain→actual PA 511.2→508.6→454; realized contribution 1.019); Bryan De La Cruz (age 27, MLB/AAA/AA PA 622/0.0/0.0; shared→domain→actual PA 479.6→497.8→50; realized contribution -0.269).

Dedicated training profile: 345 distinct people.

## Trea Turner: 2016 → 2017

Selection: value ordinary.

Age 23, current stage Current MLB, source position 6, soft roster listing 1; draft pick 13 (unknown). Actual head: dedicated origin-current MLB.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 216 | 46 | 4 | 48 | 23 |
| 2014 | Aminus | 105 | 23 | 1 | 19 | 11 |
| 2015 | AA | 295 | 68 | 5 | 56 | 25 |
| 2015 | AAA | 205 | 48 | 3 | 41 | 13 |
| 2015 | MLB | 44 | 27 | 1 | 12 | 4 |
| 2016 | AAA | 371 | 83 | 6 | 72 | 36 |
| 2016 | MLB | 324 | 73 | 13 | 59 | 14 |

Actual game/role inputs: games_mlb_0=73, role_mlb_0=4.3855, games_minor_0=83, role_minor_0=4.4194, games_mlb_1=27, role_mlb_1=2.2703, games_minor_1=116, role_minor_1=4.2857, games_mlb_2=0, role_mlb_2=4, games_minor_2=69, role_minor_2=4.5696, games_pool_MLB=94.6, role_pool_MLB=3.8164, games_pool_AAA=121.4, role_pool_AAA=4.376, games_pool_AA=54.4, role_pool_AA=4.2857, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=27.6, role_pool_A=4.5106, games_pool_Aminus=13.8, role_pool_Aminus=4.3277, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 562.226 | 0.64911 | 2.34445 |
| cohort | 562.226 | 0.64911 | 2.34445 |
| games | 559.970 | 0.64911 | 2.33504 |
| domain | 511.269 | 0.64911 | 2.13196 |
| Actual | 447 | 1.01767 | 2.13321 |

Fixed batting rate; contribution = PA × (rate/600 + origin replacement 0.00308809). Not full WAR or joint uncertainty.

Shared workload: reference 38.7273, raw prediction 559.9698.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 324.00000 | 152.64137 |
| work_0 | 324.26689 | 86.07014 |
| quality_0 | 0.85349 | 82.87225 |
| role_mlb_0 | 4.38554 | 61.12192 |
| on_40man | 1.00000 | 23.09256 |
| age_centered | -0.80000 | 20.84181 |
| role_pool_AA | 4.28571 | 15.78749 |
| role_pool_AAA | 4.37595 | 14.46385 |
| pooled_MLB_K | 0.19948 | 14.17064 |
| pooled_mlb_quality | 0.79969 | 13.82845 |
| role_minor_0 | 4.41935 | 12.49826 |
| draft_rank | 0.66255 | 11.91308 |

Origin-domain workload: reference 259.2131, raw prediction 511.2692.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| quality_0 | 0.85349 | 60.32657 |
| role_mlb_0 | 4.38554 | 54.06593 |
| MLB_0_pa | 324.00000 | 28.61837 |
| on_40man | 1.00000 | 22.90386 |
| pooled_mlb_quality | 0.79969 | 17.75223 |
| role_minor_0 | 4.41935 | 15.85958 |
| position_6 | 1.00000 | 15.35980 |
| pooled_AA_3B | 0.01101 | 13.41201 |
| pooled_MLB_3B | 0.01851 | 12.79042 |
| age_centered | -0.80000 | 12.68183 |
| pooled_Aminus_K | 0.21104 | 11.47787 |
| pooled_A_BB | 0.09495 | -10.90966 |

Ordinary value case moves closer as PA falls 560→511 versus actual 447. Current strong batting/regular role have positive path effects; the unchanged rate is lower than actual future rate. Delivered value nearly matches because excess PA compensates for understated batting, so this is not jointly correct. Franklin gets less, DeShields more and Anderson more than their varying forecasts; peer outcomes retain the tradeoffs.

Origin-selected comparisons: Nick Franklin (age 25, MLB/AAA/AA PA 191/270.0/0.0; shared→domain→actual PA 216.0→240.8→119; realized contribution -0.314); Delino DeShields (age 23, MLB/AAA/AA PA 203/249.0/0.0; shared→domain→actual PA 210.1→210.5→440; realized contribution 0.910); Tim Anderson (age 23, MLB/AAA/AA PA 431/256.0/0.0; shared→domain→actual PA 437.3→496.1→606; realized contribution 0.342).

Dedicated training profile: 75 distinct people.

## Disposition

Do not adopt this domain-specific head. Public workload RMSE/MAE and delivered value worsen versus the shared games head; whole-cohort changes are small/uncertain. Some comeback/debut gains accompany genuine harmful losses to young regulars and prior accurate forecasts. The branch cannot address first arrival or missed-season returns. This rejects this fixed branch/settings, not the idea that role retention differs from first arrival.

Close this workload branch batch and retain the established coherent baseline plus the games challenger visibly. Next reassess compatible park/opponent-adjusted contact/PBP winner inputs for the broad batting target. Do not keep making arbitrary PA subgroup branches or event-prior changes, and do not use favorable anecdotes as validation.
