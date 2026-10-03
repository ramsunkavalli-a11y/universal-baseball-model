# V38: completed games/role player walkthrough

Same historical rows/folds and unchanged batting head. Six fixed cases plus the largest PA/value gains, harms, false highs/lows and ordinary cases. Source-level review was completed before fitting. Every forecast head replays. Team game counts are not starts or healthy days. No protected 2026 outcomes.

Path accounting exactly reconstructs raw tree predictions from a count-weighted node reference and split-path effects. It is order/correlation dependent, not SHAP, a causal game effect, a fixed-feature ablation or an independent forecast. Refitting also changes the old features' mapping. Peers use origin year/stage/debut, age, PA and draft inputs, never later outcomes.

## Aaron Judge: 2016 → 2017

Selection: Fixed diagnostic; value false low.

Age 24; stage Current MLB; source position 9; draft pick 32, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

New workload inputs: games_mlb_0=27, role_mlb_0=3.6486, games_minor_0=93, role_minor_0=4.3689, games_mlb_1=0, role_mlb_1=4, games_minor_1=124, role_minor_1=4.3284, games_mlb_2=0, role_mlb_2=4, games_minor_2=131, role_minor_2=4.2766, games_pool_MLB=27, role_pool_MLB=3.6486, games_pool_AAA=141.8, role_pool_AAA=4.3347, games_pool_AA=50.4, role_pool_AA=4.3709, games_pool_Aplus=39.6, role_pool_Aplus=4.254, games_pool_A=39, role_pool_A=4.2204, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| safe_ridge | 143.966 | -0.05720 | 0.43085 |
| games | 150.205 | -0.05720 | 0.44953 |
| Actual | 678 | 5.32988 | 8.10841 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00308809). Not full WAR or joint uncertainty.

Old workload: reference 38.3607, raw prediction 143.9656, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 72.97105 |
| MLB_0_pa | 95.00000 | 27.20382 |
| age_centered | -0.60000 | 13.66875 |
| pooled_MLB_K | 0.33333 | -9.54310 |
| pooled_A_3B | 0.00637 | 7.59533 |
| quality_0 | -0.17509 | -6.73486 |
| pooled_AA_BABIP | 0.32601 | -6.40358 |
| pooled_Aplus_BB | 0.13801 | 6.23760 |
| pooled_AA_HR | 0.03889 | 6.03501 |
| pooled_mlb_quality | -0.17509 | -4.92872 |
| pooled_AA_K | 0.24383 | -3.97212 |
| work_0 | 95.07825 | -3.69580 |

Games workload: reference 38.3571, raw prediction 150.2046, games/role path effects 43.1575.

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

AAA regular-use evidence contributes positively in the saved tree paths, but PA only rises 144→150 against actual 678. The new inputs do not solve brief-debut opportunity or later exceptional hitting; the unchanged rate near zero remains far below the breakout. Decker/Marrero/Cowart later receive 62/188/117 PA, so raising every comparable debut to a full season would be unjustified. Path effects are accounting within a refitted tree, not the causal gain from games.

Origin-selected peers: Jaff Decker (MLB/AAA/AA PA 57/417.0/0.0; control→games→actual PA 36.3→32.1→62; realized value -0.115); Deven Marrero (MLB/AAA/AA PA 14/388.0/0.0; control→games→actual PA 58.0→51.3→188; realized value -0.447); Kaleb Cowart (MLB/AAA/AA PA 87/458.0/0.0; control→games→actual PA 178.7→141.7→117; realized value 0.123).

Games/role training profile: 215 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Aaron Judge: 2024 → 2025

Selection: Fixed diagnostic.

Age 32; stage Current MLB; source position 8; draft pick 32, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 696 | 157 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 106 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 158 | 58 | 171 | 113 |

New workload inputs: games_mlb_0=158, role_mlb_0=4.4286, games_minor_0=0, role_minor_0=4, games_mlb_1=106, role_mlb_1=4.2931, games_minor_1=0, role_minor_1=4, games_mlb_2=157, role_mlb_2=4.4072, games_minor_2=0, role_minor_2=4, games_pool_MLB=337, role_pool_MLB=4.4035, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| safe_ridge | 534.275 | 4.50176 | 5.67779 |
| games | 547.389 | 4.55334 | 5.86421 |
| Actual | 679 | 6.28743 | 9.23105 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00312416). Not full WAR or joint uncertainty.

Old workload: reference 39.3165, raw prediction 548.4957, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 704.28983 | 349.20054 |
| pooled_mlb_quality | 3.64857 | 59.62465 |
| quality_0 | 2.79442 | 38.85197 |
| regular_window_scaled | 1.00000 | 28.64786 |
| work_2 | 696.00000 | 23.83576 |
| age_centered | 1.00000 | -23.71747 |
| MLB_0_pa | 704.00000 | 16.91504 |
| pooled_MLB_pa | 1488.00000 | 12.05754 |
| pooled_MLB_K | 0.25378 | -10.74476 |
| on_40man | 1.00000 | 8.42684 |
| quality_1 | 1.31713 | 5.77395 |
| quality_2 | 2.40833 | 5.40438 |

Games workload: reference 39.3058, raw prediction 547.3890, games/role path effects 97.9518.

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

158 current MLB games and regular PA/appearance have positive path contributions, yet the refitted total stays 547 versus old 548 and actual 679. Correlated workload features redistribute attribution without improving this forecast. The intact batting rate +4.553 is sensible; the miss still mixes conservative PA with an exceptional future rate. Castellanos/Chapman/Olson later receive 589/535/724 PA, illustrating actual uncertainty within regular-role profiles.

Origin-selected peers: Nick Castellanos (MLB/AAA/AA PA 659/0.0/0.0; control→games→actual PA 529.0→541.5→589; realized value 1.309); Matt Olson (MLB/AAA/AA PA 685/0.0/0.0; control→games→actual PA 629.9→629.8→724; realized value 5.517); Matt Chapman (MLB/AAA/AA PA 647/0.0/0.0; control→games→actual PA 516.8→550.7→535; realized value 2.761).

Games/role training profile: 640 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Masyn Winn: 2023 → 2024

Selection: Fixed diagnostic.

Age 21; stage Current MLB; source position 6; draft pick 54, class HS SR; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 284 | 61 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 37 | 2 | 40 | 6 |
| 2022 | AA | 403 | 86 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 33 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 105 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 37 | 2 | 26 | 10 |

New workload inputs: games_mlb_0=37, role_mlb_0=3.766, games_minor_0=105, role_minor_0=4.6783, games_mlb_1=0, role_mlb_1=4, games_minor_1=119, role_minor_1=4.5736, games_mlb_2=0, role_mlb_2=4, games_minor_2=98, role_minor_2=4.4259, games_pool_MLB=37, role_pool_MLB=3.766, games_pool_AAA=105, role_pool_AAA=4.6783, games_pool_AA=68.8, role_pool_AA=4.599, games_pool_Aplus=48.6, role_pool_Aplus=4.2662, games_pool_A=36.6, role_pool_A=4.515, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 305.512 | -0.79671 | 0.54021 |
| safe_ridge | 302.679 | -0.79951 | 0.53379 |
| games | 308.296 | -0.79671 | 0.54514 |
| Actual | 637 | 0.25454 | 2.25951 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00309608). Not full WAR or joint uncertainty.

Old workload: reference 39.2619, raw prediction 305.5124, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 96.15729 |
| age_centered | -1.20000 | 58.82237 |
| MLB_0_pa | 137.00000 | 26.04380 |
| pooled_AAA_HR | 0.03512 | 17.08807 |
| pooled_A_3B | 0.00851 | 16.86926 |
| work_0 | 137.00000 | 15.82579 |
| pooled_MLB_K | 0.20675 | 15.32337 |
| pooled_mlb_quality | -0.55760 | -15.20695 |
| quality_0 | -0.55760 | -14.97421 |
| pooled_A_BB | 0.11834 | 13.27152 |
| AAA_0_pa | 498.00000 | 12.74494 |
| AAA_1_pa | 0.00000 | 5.89620 |

Games workload: reference 39.2617, raw prediction 308.2962, games/role path effects 63.4009.

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

105 AAA games and high AAA PA/appearance have positive path contributions, but expected PA barely changes 306→308 versus actual 637. The model recognizes regular minor use but does not translate the promotion into a full major role. The unchanged batting rate −0.797 is also pessimistic relative to +0.254 actual. Meadows/Edwards/Ornelas later receive 298/303/40 PA; Ornelas' forecast increases 51→142 despite the small later role. This is not a uniform arrival win.

Origin-selected peers: Xavier Edwards (MLB/AAA/AA PA 84/433.0/0.0; control→games→actual PA 162.4→192.9→303; realized value 2.187); Parker Meadows (MLB/AAA/AA PA 145/517.0/0.0; control→games→actual PA 213.1→248.0→298; realized value 1.211); Jonathan Ornelas (MLB/AAA/AA PA 8/517.0/0.0; control→games→actual PA 50.6→141.6→40; realized value -0.134).

Games/role training profile: 389 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Spencer Steer: 2022 → 2023

Selection: Fixed diagnostic.

Age 24; stage Current MLB; source position 5; draft pick 90, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 280 | 65 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 45 | 10 | 32 | 35 |
| 2022 | AA | 156 | 35 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 71 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 28 | 2 | 26 | 11 |

New workload inputs: games_mlb_0=28, role_mlb_0=3.8947, games_minor_0=106, role_minor_0=4.5862, games_mlb_1=0, role_mlb_1=4, games_minor_1=110, role_minor_1=4.4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=28, role_pool_MLB=3.8947, games_pool_AAA=71, role_pool_AAA=4.642, games_pool_AA=87, role_pool_AA=4.3299, games_pool_Aplus=36, role_pool_Aplus=4.487, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 180.375 | -0.23663 | 0.49361 |
| safe_ridge | 183.018 | -0.23850 | 0.50027 |
| games | 232.946 | -0.23663 | 0.63748 |
| Actual | 665 | 1.90921 | 4.17493 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00313097). Not full WAR or joint uncertainty.

Old workload: reference 38.7682, raw prediction 180.3748, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 91.66036 |
| MLB_0_pa | 108.00000 | 17.75129 |
| pooled_AA_HR | 0.04625 | 14.72886 |
| work_0 | 108.00000 | 9.20373 |
| pooled_AAA_HR | 0.04128 | 8.67915 |
| pooled_mlb_quality | -0.08442 | -8.30052 |
| pooled_AA_2B | 0.05583 | 5.51633 |
| pooled_MLB_pa | 108.00000 | 5.24096 |
| pooled_MLB_K | 0.23558 | -4.69745 |
| age_centered | -0.60000 | 4.19739 |
| draft_rank | 0.40799 | -2.95958 |
| pooled_AAA_BB | 0.10092 | 2.48392 |

Games workload: reference 38.7736, raw prediction 232.9461, games/role path effects 61.3648.

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

High pooled AAA PA/appearance contributes about +51 PA in path accounting and the actual forecast rises 180→233 toward 665. That is a useful directional change, not a solved starting-role projection. Rate remains −0.237 against a positive later season, so total contribution still undershoots 0.64 versus 4.17. Brennan improves toward 455, Freeman is raised too far versus 168, and Henderson falls 393→358 despite 622 actual. Shared role evidence has genuine tradeoffs.

Origin-selected peers: Tyler Freeman (MLB/AAA/AA PA 86/343.0/0.0; control→games→actual PA 186.2→247.1→168; realized value 0.094); Gunnar Henderson (MLB/AAA/AA PA 132/295.0/208.0; control→games→actual PA 392.5→357.5→622; realized value 3.402); Will Brennan (MLB/AAA/AA PA 45/433.0/157.0; control→games→actual PA 242.3→321.1→455; realized value 0.166).

Games/role training profile: 333 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Nick Kurtz: 2024 → 2025

Selection: Fixed diagnostic.

Age 21; stage Upper minors; source position 3; draft pick 4, class 4YR JR; soft roster listing 0.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

New workload inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=12, role_minor_0=4.0909, games_mlb_1=0, role_mlb_1=4, games_minor_1=0, role_minor_1=4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=5, role_pool_AA=3.6667, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=7, role_pool_A=4.4118, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| safe_ridge | 50.494 | -0.11288 | 0.14825 |
| games | 29.943 | -0.13556 | 0.08678 |
| Actual | 489 | 5.15001 | 5.72099 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00312416). Not full WAR or joint uncertainty.

Old workload: reference 39.2997, raw prediction 42.4946, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| draft_rank | 0.81761 | 34.48497 |
| work_0 | 0.00000 | -23.69925 |
| age_centered | -1.20000 | 8.73600 |
| on_40man | 0.00000 | -6.57513 |
| pooled_AA_BB | 0.08696 | 2.00453 |
| AAA_0_pa | 0.00000 | -1.88272 |
| regular_window_scaled | 0.00000 | -1.84388 |
| pooled_MLB_BB | 0.08000 | -1.69242 |
| pooled_AA_pa | 15.00000 | -1.66366 |
| pooled_AA_2B | 0.05217 | 1.39249 |
| pooled_MLB_BABIP | 0.30000 | 1.38655 |
| pooled_AAA_HR | 0.03000 | -1.28157 |

Games workload: reference 39.2894, raw prediction 29.9431, games/role path effects -4.5297.

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

Only 12 professional games receive little positive role evidence; forecast falls 42→30 against actual 489. Draft pedigree remains a positive input, but the first short professional season is still not translated into rapid next-year arrival. This is a consequential newcomer miss; do not interpret twelve games as diagnosed poor durability. The three origin-selected young high-pick minor peers all have zero next-year MLB PA, so the exceptional entrant cannot simply be assumed typical.

Origin-selected peers: Benny Montgomery (MLB/AAA/AA PA 0/0.0/48.0; control→games→actual PA 37.2→40.9→0; realized value 0.000); Termarr Johnson (MLB/AAA/AA PA 0/0.0/57.0; control→games→actual PA 26.9→21.8→0; realized value 0.000); Walker Jenkins (MLB/AAA/AA PA 0/0.0/28.0; control→games→actual PA 44.8→46.6→0; realized value 0.000).

Games/role training profile: 2394 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Gavin Lux: 2023 → 2024

Selection: Fixed diagnostic.

Age 25; stage Inactive / unknown; source position 4; draft pick 20, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AAA | 74 | 17 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 102 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 129 | 6 | 95 | 47 |

New workload inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=0, role_minor_0=4, games_mlb_1=129, role_mlb_1=3.6763, games_minor_1=0, role_minor_1=4, games_mlb_2=102, role_mlb_2=3.7589, games_minor_2=17, role_minor_2=4.2222, games_pool_MLB=164.4, role_pool_MLB=3.7007, games_pool_AAA=10.2, role_pool_AAA=4.1782, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 215.427 | -0.23943 | 0.58101 |
| safe_ridge | 199.701 | -0.31786 | 0.51249 |
| games | 201.958 | -0.23943 | 0.54469 |
| Actual | 487 | 0.08394 | 1.58897 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00309608). Not full WAR or joint uncertainty.

Old workload: reference 38.9865, raw prediction 215.4274, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 95.82727 |
| work_0 | 0.00000 | -37.30317 |
| regular_window_scaled | 0.33333 | 27.27942 |
| pooled_mlb_quality | 0.15072 | 26.70309 |
| age_centered | -0.40000 | 22.89426 |
| pooled_MLB_3B | 0.01205 | 11.99984 |
| pooled_MLB_K | 0.21094 | 11.43548 |
| work_1 | 471.00000 | 10.45716 |
| pooled_MLB_pa | 605.40000 | 7.04483 |
| work_2 | 381.15685 | -2.70473 |
| pooled_AAA_HBP | 0.00693 | 1.97288 |
| pooled_MLB_BABIP | 0.32057 | 1.28596 |

Games workload: reference 38.9774, raw prediction 201.9575, games/role path effects 5.2265.

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

Current absence and preserved prior 129/102-game MLB seasons produce 202 PA versus old 215 and actual 487. The role extension does not distinguish a temporary medical return from generic inactivity, and the review must not claim it does. Plummer/Ciuffo/Craig have zero later PA; their source profiles are not proper medical-return analogues. Unchanged batting rate −0.239 also understates the realized +0.084, but games were not tested as talent inputs.

Origin-selected peers: Nick Ciuffo (MLB/AAA/AA PA 0/0.0/0.0; control→games→actual PA 9.5→3.2→0; realized value 0.000); Will Craig (MLB/AAA/AA PA 0/0.0/0.0; control→games→actual PA 5.9→12.2→0; realized value 0.000); Nick Plummer (MLB/AAA/AA PA 0/0.0/0.0; control→games→actual PA 20.7→18.8→0; realized value 0.000).

Games/role training profile: 388 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Chase Meidroth: 2024 → 2025

Selection: pa largest gain.

Age 22; stage Upper minors; source position 6; draft pick 129, class 4YR SR; soft roster listing 0.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | A | 85 | 19 | 4 | 9 | 12 |
| 2022 | RK124 | 11 | 3 | 0 | 2 | 2 |
| 2023 | AA | 396 | 91 | 7 | 78 | 59 |
| 2023 | Aplus | 97 | 20 | 2 | 20 | 21 |
| 2024 | AAA | 558 | 122 | 7 | 71 | 105 |

New workload inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=122, role_minor_0=4.5303, games_mlb_1=0, role_mlb_1=4, games_minor_1=111, role_minor_1=4.405, games_mlb_2=0, role_mlb_2=4, games_minor_2=22, role_minor_2=4.25, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=122, role_pool_AAA=4.5303, games_pool_AA=72.8, role_pool_AA=4.3092, games_pool_Aplus=16, role_pool_Aplus=4.5231, games_pool_A=11.4, role_pool_A=4.2523, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=1.8, role_pool_RK124=3.9492, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 40.360 | -0.33695 | 0.10343 |
| safe_ridge | 49.994 | -0.32269 | 0.12930 |
| games | 147.381 | -0.33695 | 0.37767 |
| Actual | 505 | -0.90862 | 0.80883 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00312416). Not full WAR or joint uncertainty.

Old workload: reference 39.3165, raw prediction 40.3603, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 0.00000 | -23.11047 |
| age_centered | -1.00000 | 13.38600 |
| pooled_MLB_BB | 0.08000 | 6.44434 |
| pooled_AAA_K | 0.14286 | 6.22192 |
| AAA_0_pa | 558.00000 | 5.69247 |
| on_40man | 0.00000 | -5.29352 |
| pooled_AAA_BB | 0.17173 | 3.13836 |
| pooled_AAA_HR | 0.01520 | -2.76075 |
| pooled_AAA_BABIP | 0.32543 | 2.38641 |
| position_6 | 1.00000 | 1.88254 |
| regular_window_scaled | 0.00000 | -1.84050 |
| pooled_AA_2B | 0.04271 | -1.66910 |

Games workload: reference 39.3058, raw prediction 147.3811, games/role path effects 109.0202.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| role_pool_AAA | 4.53030 | 82.16376 |
| age_centered | -1.00000 | 26.27651 |
| work_0 | 0.00000 | -23.15888 |
| role_pool_AA | 4.30918 | 18.80421 |
| pooled_MLB_BB | 0.08000 | 8.39504 |
| on_40man | 0.00000 | -6.23456 |
| role_pool_Aplus | 4.52308 | 3.25656 |
| role_pool_MLB | 4.00000 | 2.45254 |
| Aplus_1_pa | 97.00000 | -2.36888 |
| games_pool_AAA | 122.00000 | 2.12312 |
| pooled_AAA_K | 0.14286 | 2.00053 |
| quality_0 | 0.00000 | -1.58227 |

Largest PA gain. Sustained AAA 558 PA/122 games and high PA/appearance contribute strongly in the new path accounting; PA rises 40→147 toward actual 505. Value improves 0.10→0.38 against 0.81 with unchanged rate. This is a sensible recognition of regular AAA use, but does not imply a guaranteed job. Peters/Lavigne/Caissie later receive only 12/0/27 PA and the model preserves mixed forecasts for them.

Origin-selected peers: Tristan Peters (MLB/AAA/AA PA 0/478.0/0.0; control→games→actual PA 42.5→54.4→12; realized value -0.273); Grant Lavigne (MLB/AAA/AA PA 0/530.0/0.0; control→games→actual PA 33.8→20.4→0; realized value 0.000); Owen Caissie (MLB/AAA/AA PA 0/549.0/0.0; control→games→actual PA 166.7→154.7→27; realized value -0.064).

Games/role training profile: 2017 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Matt Davidson: 2018 → 2019

Selection: pa largest harm.

Age 27; stage Current MLB; source position 10; draft pick 35, class HS; soft roster listing 0.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | AAA | 326 | 75 | 10 | 86 | 30 |
| 2016 | MLB | 2 | 1 | 0 | 1 | 0 |
| 2017 | AAA | 3 | 1 | 0 | 3 | 0 |
| 2017 | MLB | 443 | 118 | 26 | 165 | 19 |
| 2018 | MLB | 496 | 126 | 20 | 165 | 52 |

New workload inputs: games_mlb_0=126, role_mlb_0=3.9412, games_minor_0=0, role_minor_0=4, games_mlb_1=118, role_mlb_1=3.7734, games_minor_1=1, role_minor_1=3.9091, games_mlb_2=1, role_mlb_2=3.8182, games_minor_2=75, role_minor_2=4.3059, games_pool_MLB=221, role_pool_MLB=3.8597, games_pool_AAA=45.8, role_pool_AAA=4.2652, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 304.487 | 0.26743 | 1.07316 |
| safe_ridge | 304.487 | 0.26743 | 1.07316 |
| games | 405.093 | 0.26743 | 1.42775 |
| Actual | 0 | 0.00000 | 0.00000 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00307877). Not full WAR or joint uncertainty.

Old workload: reference 39.7467, raw prediction 304.4867, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 496.00000 | 240.28392 |
| on_40man | 0.00000 | -82.76330 |
| work_0 | 495.79597 | 43.60380 |
| regular_window_scaled | 0.66667 | 39.71327 |
| quality_0 | 0.14165 | 23.30600 |
| age_centered | 0.00000 | 22.52118 |
| pooled_MLB_K | 0.33691 | -10.37387 |
| pooled_AAA_3B | 0.00168 | -8.44061 |
| pooled_MLB_3B | 0.00137 | -7.76973 |
| MLB_1_pa | 443.00000 | 4.56849 |
| pooled_mlb_quality | -0.05541 | -3.72677 |
| pooled_MLB_pa | 851.60000 | 3.51417 |

Games workload: reference 39.7432, raw prediction 405.0925, games/role path effects 37.0003.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 496.00000 | 234.39128 |
| work_0 | 495.79597 | 52.97881 |
| on_40man | 0.00000 | -44.49603 |
| role_mlb_0 | 3.94118 | 40.80831 |
| quality_0 | 0.14165 | 40.13750 |
| age_centered | 0.00000 | 27.11345 |
| regular_window_scaled | 0.66667 | 24.46202 |
| pooled_MLB_pa | 851.60000 | 7.51585 |
| pooled_AAA_3B | 0.00168 | -7.11033 |
| MLB_1_pa | 443.00000 | 6.78398 |
| pooled_MLB_K | 0.33691 | -5.80995 |
| pooled_AAA_2B | 0.05705 | -4.93387 |

Largest PA harm. Two fairly regular MLB seasons give positive role effects, and PA rises 304→405 despite a soft roster listing of zero and later zero MLB PA. Missing next-year job/security dominates. The model sees prior production/use but does not adequately distinguish an unlisted former regular from a secure regular. Grichuk/Judge/Bradley do play 628/447/567 PA later; peers were selected without job/transaction matching, so this is a contextual gap, not evidence all prior regulars should be penalized.

Origin-selected peers: Randal Grichuk (MLB/AAA/AA PA 462/9.0/8.0; control→games→actual PA 493.7→440.7→628; realized value 1.386); Aaron Judge (MLB/AAA/AA PA 498/0.0/0.0; control→games→actual PA 536.7→578.0→447; realized value 3.680); Jackie Bradley Jr. (MLB/AAA/AA PA 535/0.0/0.0; control→games→actual PA 418.2→408.1→567; realized value 1.397).

Games/role training profile: 422 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Matt McLain: 2023 → 2024

Selection: pa false high.

Age 23; stage Current MLB; source position 6; draft pick 17, class 4YR JR; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | Aplus | 119 | 29 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 2 | 0 | 0 | 0 |
| 2022 | AA | 452 | 103 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 40 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 89 | 16 | 115 | 31 |

New workload inputs: games_mlb_0=89, role_mlb_0=4.4747, games_minor_0=40, role_minor_0=4.4, games_mlb_1=0, role_mlb_1=4, games_minor_1=103, role_minor_1=4.354, games_mlb_2=0, role_mlb_2=4, games_minor_2=31, role_minor_2=4.0488, games_pool_MLB=89, role_pool_MLB=4.4747, games_pool_AAA=40, role_pool_AAA=4.4, games_pool_AA=82.4, role_pool_AA=4.3463, games_pool_Aplus=17.4, role_pool_Aplus=4.0657, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=1.2, role_pool_RK121=3.9464, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 561.901 | 0.88467 | 2.56818 |
| safe_ridge | 517.689 | 0.88748 | 2.36854 |
| games | 564.580 | 0.88467 | 2.58042 |
| Actual | 0 | 0.00000 | 0.00000 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00309608). Not full WAR or joint uncertainty.

Old workload: reference 39.1208, raw prediction 561.9014, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 403.00000 | 266.37366 |
| age_centered | -0.80000 | 65.58975 |
| quality_0 | 0.67281 | 42.31839 |
| pooled_mlb_quality | 0.67281 | 32.86964 |
| pooled_AAA_HR | 0.05357 | 30.57394 |
| regular_window_scaled | 0.33333 | 30.52685 |
| on_40man | 1.00000 | 22.71650 |
| pooled_MLB_K | 0.27435 | -19.00861 |
| pooled_AA_3B | 0.00975 | 10.17008 |
| draft_rank | 0.62725 | 9.14698 |
| pooled_MLB_3B | 0.00895 | 7.79345 |
| pooled_AA_BB | 0.13692 | 6.46319 |

Games workload: reference 39.1181, raw prediction 564.5798, games/role path effects 69.3615.

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

Largest false-high PA forecast, 565 versus actual zero, is essentially unchanged from 562. His 403 PA/89 MLB games plus strong AAA use justify expecting a role from origin production. Later absence is not inferable as a certainty from these counts; it remains health/availability risk. Pratto/Baty/Walker later get 0/171/178 PA despite their own recent debuts. The model still overstates some young established opportunities, not solely McLain.

Origin-selected peers: Nick Pratto (MLB/AAA/AA PA 345/131.0/0.0; control→games→actual PA 271.6→309.0→0; realized value 0.000); Brett Baty (MLB/AAA/AA PA 389/121.0/0.0; control→games→actual PA 375.3→402.9→171; realized value 0.126); Jordan Walker (MLB/AAA/AA PA 465/135.0/0.0; control→games→actual PA 478.8→532.2→178; realized value -0.048).

Games/role training profile: 933 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Cody Bellinger: 2016 → 2017

Selection: pa false low.

Age 20; stage Upper minors; source position 3; draft pick 124, class unknown; soft roster listing 0.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 51 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 128 | 30 | 150 | 51 |
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |

New workload inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=117, role_minor_0=4.0709, games_mlb_1=0, role_mlb_1=4, games_minor_1=128, role_minor_1=4.2319, games_mlb_2=0, role_mlb_2=4, games_minor_2=51, role_minor_2=4.4754, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=3, role_pool_AAA=4, games_pool_AA=114, role_pool_AA=4.0726, games_pool_Aplus=102.4, role_pool_Aplus=4.2278, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=30.6, role_pool_RK128=4.4286, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 35.516 | 0.08471 | 0.11469 |
| safe_ridge | 35.516 | 0.08471 | 0.11469 |
| games | 7.761 | 0.08471 | 0.02506 |
| Actual | 548 | 2.70047 | 4.15217 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00308809). Not full WAR or joint uncertainty.

Old workload: reference 38.3607, raw prediction 35.5162, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| MLB_0_pa | 0.00000 | -12.89185 |
| pooled_AA_HR | 0.04602 | 12.86375 |
| pooled_Aplus_BB | 0.09118 | 10.52235 |
| work_0 | 0.00000 | -10.08227 |
| age_centered | -1.40000 | 6.23479 |
| on_40man | 0.00000 | -6.09691 |
| pooled_Aplus_HR | 0.05045 | 4.06849 |
| pooled_AAA_K | 0.20536 | 3.31981 |
| regular_window_scaled | 0.00000 | -2.05062 |
| pooled_Aplus_K | 0.26719 | 2.03489 |
| pooled_AAA_pa | 12.00000 | -1.97293 |
| quality_0 | 0.00000 | -1.66151 |

Games workload: reference 38.3571, raw prediction 7.7613, games/role path effects -2.2142.

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

Largest false-low PA forecast. Strong 465-PA/23-HR AA season plus a twelve-PA AAA finish produces only 8 PA, down from 36, versus actual 548. Pooled AAA role ratio equals the prior 4 because 12 PA/3 games; game inputs do not capture how unusual his AA power/age and promotion path were. Westbrook/Wong/Kiner-Falefa all have zero next-year PA, but they are exposure/draft peers, not matched power/talent grades. This is a continuing prospect-arrival gap, not a missing games source.

Origin-selected peers: Jamie Westbrook (MLB/AAA/AA PA 0/0.0/473.0; control→games→actual PA 10.0→4.9→0; realized value 0.000); Kean Wong (MLB/AAA/AA PA 0/0.0/492.0; control→games→actual PA 20.3→28.1→0; realized value 0.000); Isiah Kiner-Falefa (MLB/AAA/AA PA 0/0.0/457.0; control→games→actual PA 6.7→12.7→0; realized value 0.000).

Games/role training profile: 939 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Mark Vientos: 2022 → 2023

Selection: pa ordinary.

Age 22; stage Current MLB; source position 5; draft pick 59, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 306 | 72 | 22 | 87 | 24 |
| 2021 | AAA | 43 | 11 | 3 | 13 | 7 |
| 2022 | AAA | 427 | 101 | 24 | 122 | 42 |
| 2022 | MLB | 41 | 16 | 1 | 12 | 5 |

New workload inputs: games_mlb_0=16, role_mlb_0=3.1154, games_minor_0=101, role_minor_0=4.2072, games_mlb_1=0, role_mlb_1=4, games_minor_1=83, role_minor_1=4.1828, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=16, role_pool_MLB=3.1154, games_pool_AAA=109.8, role_pool_AAA=4.1853, games_pool_AA=57.6, role_pool_AA=4.213, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 251.473 | 0.22926 | 0.88344 |
| safe_ridge | 244.284 | 0.26685 | 0.87349 |
| games | 232.806 | 0.22926 | 0.81787 |
| Actual | 233 | -2.46020 | -0.23399 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00313097). Not full WAR or joint uncertainty.

Old workload: reference 38.7682, raw prediction 251.4727, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| on_40man | 1.00000 | 92.72003 |
| age_centered | -1.00000 | 68.18169 |
| pooled_AA_HR | 0.05974 | 24.94836 |
| pooled_AAA_HR | 0.05237 | 24.82481 |
| MLB_0_pa | 41.00000 | 11.98071 |
| draft_rank | 0.46355 | 10.15264 |
| pooled_AAA_3B | 0.00267 | 6.55370 |
| pooled_mlb_quality | -0.09169 | -6.40130 |
| pooled_MLB_K | 0.24823 | -5.56135 |
| work_0 | 41.00000 | -4.06807 |
| pooled_MLB_pa | 41.00000 | -3.71027 |
| regular_window_scaled | 0.00000 | -2.22260 |

Games workload: reference 38.7736, raw prediction 232.8059, games/role path effects 10.7057.

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

Ordinary PA example: 233 predicted versus 233 actual, down from 251. A short MLB role (41 PA/16 games) follows 427 AAA PA/101 games. The game evidence modestly lowers opportunity, consistent with the observed partial role. Batting remains too optimistic +0.229 versus realized poor production, so value 0.82 still misses −0.23; correct PA is not an accurate whole forecast. Campusano/Burleson/Lee have varied later opportunity and success.

Origin-selected peers: Luis Campusano (MLB/AAA/AA PA 50/358.0/0.0; control→games→actual PA 163.5→162.4→174; realized value 1.224); Alec Burleson (MLB/AAA/AA PA 53/470.0/0.0; control→games→actual PA 207.7→202.5→347; realized value 0.503); Korey Lee (MLB/AAA/AA PA 26/446.0/0.0; control→games→actual PA 134.2→136.5→70; realized value -0.849).

Games/role training profile: 333 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Aaron Judge: 2021 → 2022

Selection: value largest gain.

Age 29; stage Current MLB; source position 9; draft pick 32, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | AAA | 19 | 5 | 1 | 7 | 3 |
| 2019 | MLB | 447 | 102 | 27 | 141 | 60 |
| 2020 | MLB | 114 | 28 | 9 | 32 | 10 |
| 2021 | MLB | 633 | 148 | 39 | 158 | 73 |

New workload inputs: games_mlb_0=148, role_mlb_0=4.2595, games_minor_0=0, role_minor_0=4, games_mlb_1=75.6, role_mlb_1=4.0526, games_minor_1=0, role_minor_1=4, games_mlb_2=102, role_mlb_2=4.3482, games_minor_2=5, role_minor_2=3.9333, games_pool_MLB=269.68, role_pool_MLB=4.2732, games_pool_AAA=3, role_pool_AAA=3.9538, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 482.210 | 2.04558 | 3.15572 |
| safe_ridge | 462.283 | 1.99020 | 2.98265 |
| games | 521.339 | 2.04558 | 3.41180 |
| Actual | 696 | 6.56063 | 9.78949 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00313500). Not full WAR or joint uncertainty.

Old workload: reference 38.1822, raw prediction 482.2098, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 633.26060 | 352.45688 |
| quality_0 | 1.27862 | 58.99274 |
| pooled_mlb_quality | 1.56168 | 42.49013 |
| pooled_MLB_K | 0.26657 | -35.16598 |
| regular_window_scaled | 0.66667 | 23.54573 |
| on_40man | 1.00000 | 11.78920 |
| pooled_MLB_HR | 0.05987 | 8.22728 |
| pooled_MLB_pa | 992.40000 | -7.47310 |
| MLB_0_pa | 633.00000 | 7.16639 |
| MLB_2_pa | 447.00000 | -5.28300 |
| pooled_MLB_3B | 0.00101 | -4.33291 |
| pooled_AAA_K | 0.24417 | -3.85237 |

Games workload: reference 38.1877, raw prediction 521.3394, games/role path effects 72.3999.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 633.26060 | 310.17854 |
| quality_0 | 1.27862 | 69.85924 |
| role_mlb_0 | 4.25949 | 52.10945 |
| pooled_MLB_K | 0.26657 | -30.05671 |
| role_pool_MLB | 4.27318 | 20.16781 |
| pooled_mlb_quality | 1.56168 | 18.86427 |
| MLB_0_pa | 633.00000 | 11.71641 |
| pooled_MLB_HR | 0.05987 | 10.88409 |
| on_40man | 1.00000 | 9.07796 |
| regular_window_scaled | 0.66667 | 6.36652 |
| age_centered | 0.40000 | 5.55698 |
| draft_rank_low_exposure | 0.04143 | -3.49298 |

Largest value gain: PA rises 482→521 toward 696 after 633 PA/148 current games, with prior shortened-2020 exposure handled explicitly. Current role and high production contribute positively; rate is bit-exact +2.046. Value improves 3.16→3.41 but still misses 9.79, mostly the later historic hitting season plus low workload. Story later has 396 PA while Chapman/Castellanos have 621/558, so a regular role still carries meaningful risk.

Origin-selected peers: Nick Castellanos (MLB/AAA/AA PA 585/0.0/0.0; control→games→actual PA 528.4→553.1→558; realized value 1.570); Trevor Story (MLB/AAA/AA PA 595/0.0/0.0; control→games→actual PA 564.9→564.7→396; realized value 1.362); Matt Chapman (MLB/AAA/AA PA 622/0.0/0.0; control→games→actual PA 532.2→521.3→621; realized value 3.050).

Games/role training profile: 517 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Franmil Reyes: 2021 → 2022

Selection: value largest harm.

Age 25; stage Current MLB; source position 10; draft pick None, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | MLB | 548 | 150 | 37 | 156 | 46 |
| 2020 | MLB | 241 | 59 | 9 | 69 | 24 |
| 2021 | AA | 7 | 3 | 2 | 3 | 0 |
| 2021 | AAA | 12 | 4 | 1 | 2 | 0 |
| 2021 | MLB | 466 | 115 | 30 | 149 | 40 |

New workload inputs: games_mlb_0=115, role_mlb_0=4.048, games_minor_0=7, role_minor_0=3.4706, games_mlb_1=159.3, role_mlb_1=4.0725, games_minor_1=0, role_minor_1=4, games_mlb_2=150, role_mlb_2=3.675, games_minor_2=0, role_minor_2=4, games_pool_MLB=332.44, role_pool_MLB=3.9191, games_pool_AAA=4, role_pool_AAA=3.7143, games_pool_AA=3, role_pool_AA=3.6154, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 462.358 | 1.59790 | 2.68083 |
| safe_ridge | 440.662 | 1.51282 | 2.49255 |
| games | 573.546 | 1.59790 | 3.32552 |
| Actual | 473 | -1.42460 | 0.35789 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00313500). Not full WAR or joint uncertainty.

Old workload: reference 38.7617, raw prediction 462.3578, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 466.19185 | 306.88990 |
| quality_0 | 0.55836 | 35.94511 |
| pooled_mlb_quality | 0.68599 | 31.65802 |
| regular_window_scaled | 1.00000 | 23.02315 |
| age_centered | -0.40000 | 20.29764 |
| pooled_MLB_pa | 987.60000 | 18.14855 |
| pooled_MLB_K | 0.29496 | -13.89735 |
| on_40man | 1.00000 | 13.18721 |
| MLB_0_pa | 466.00000 | -9.13173 |
| MLB_1_pa | 241.00000 | -7.05124 |
| pooled_AAA_HR | 0.03571 | 6.80286 |
| draft_rank | 0.00000 | -5.04763 |

Games workload: reference 38.7679, raw prediction 573.5465, games/role path effects 88.8591.

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

Largest value harm. His 59-of-60-game 2020 exposure is scaled to 159.3, prior 150-game year and current role raise predicted PA 462→574 versus actual 473. The intact rate +1.598 badly overstates later production, so extra PA magnifies the value miss 2.68→3.33 versus 0.36. The previous closer PA was useful; the stronger availability-looking profile is not proof of talent retention. Margot/Arraez/Castro have mixed next-year workload.

Origin-selected peers: Manuel Margot (MLB/AAA/AA PA 464/15.0/0.0; control→games→actual PA 390.3→402.8→363; realized value 1.140); Luis Arraez (MLB/AAA/AA PA 479/9.0/0.0; control→games→actual PA 468.1→491.6→603; realized value 3.953); Willi Castro (MLB/AAA/AA PA 450/23.0/0.0; control→games→actual PA 365.3→349.9→392; realized value 0.469).

Games/role training profile: 508 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Yordan Alvarez: 2024 → 2025

Selection: value false high.

Age 27; stage Current MLB; source position 10; draft pick None, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

New workload inputs: games_mlb_0=147, role_mlb_0=4.2994, games_minor_0=0, role_minor_0=4, games_mlb_1=114, role_mlb_1=4.3226, games_minor_1=3, role_minor_1=3.9231, games_mlb_2=135, role_mlb_2=4.1448, games_minor_2=0, role_minor_2=4, games_pool_MLB=319.2, role_pool_MLB=4.2783, games_pool_AAA=2.4, role_pool_AAA=3.9355, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| safe_ridge | 601.307 | 3.76103 | 5.64780 |
| games | 577.490 | 3.70970 | 5.37470 |
| Actual | 199 | 0.91965 | 0.92510 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00312416). Not full WAR or joint uncertainty.

Old workload: reference 39.2997, raw prediction 584.7743, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 635.26142 | 351.75964 |
| pooled_mlb_quality | 2.45709 | 39.92820 |
| quality_0 | 1.41565 | 34.96710 |
| regular_window_scaled | 1.00000 | 25.91449 |
| MLB_0_pa | 635.00000 | 22.88146 |
| quality_1 | 1.38309 | 19.77083 |
| pooled_MLB_HR | 0.05789 | 16.27045 |
| age_centered | 0.00000 | 12.20331 |
| on_40man | 1.00000 | 9.69424 |
| pooled_MLB_K | 0.17379 | 9.22178 |
| pooled_MLB_pa | 1368.40000 | 6.77466 |
| pooled_MLB_3B | 0.00306 | 6.02064 |

Games workload: reference 39.2894, raw prediction 577.4905, games/role path effects 59.5921.

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

Largest false-high value. PA falls slightly 585→577 but remains far above later 199; batting rate is intact +3.710. Recent regular game involvement is a reasonable input, not a forecast of future health. Gleyber/Castro/De La Cruz later receive 628/454/50 PA, including another severe opportunity loss. Do not solve this by forcing all elite hitters to low expected PA or using later injury evidence.

Origin-selected peers: Gleyber Torres (MLB/AAA/AA PA 665/0.0/0.0; control→games→actual PA 573.0→591.9→628; realized value 3.070); Willi Castro (MLB/AAA/AA PA 635/0.0/0.0; control→games→actual PA 518.3→511.2→454; realized value 1.019); Bryan De La Cruz (MLB/AAA/AA PA 622/0.0/0.0; control→games→actual PA 468.2→479.6→50; realized value -0.269).

Games/role training profile: 620 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Kyle Farmer: 2024 → 2025

Selection: value ordinary.

Age 33; stage Current MLB; source position 4; draft pick 244, class unknown; soft roster listing 1.

| Year | League | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 583 | 145 | 14 | 99 | 33 |
| 2023 | AAA | 15 | 4 | 1 | 4 | 2 |
| 2023 | MLB | 369 | 120 | 11 | 86 | 23 |
| 2024 | AAA | 12 | 3 | 0 | 4 | 1 |
| 2024 | MLB | 242 | 107 | 5 | 49 | 18 |

New workload inputs: games_mlb_0=107, role_mlb_0=2.4103, games_minor_0=3, role_minor_0=4, games_mlb_1=120, role_mlb_1=3.1462, games_minor_1=4, role_minor_1=3.9286, games_mlb_2=145, role_mlb_2=4.0194, games_minor_2=0, role_minor_2=4, games_pool_MLB=290, role_pool_MLB=3.09, games_pool_AAA=6.2, role_pool_AAA=3.9506, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

| Forecast | MLB PA | Batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 234.969 | -1.25232 | 0.24365 |
| safe_ridge | 253.898 | -1.27798 | 0.25242 |
| games | 207.782 | -1.25232 | 0.21546 |
| Actual | 300 | -1.43855 | 0.21553 |

Fixed batting head; contribution = PA × (rate/600 + replacement 0.00312416). Not full WAR or joint uncertainty.

Old workload: reference 39.0655, raw prediction 234.9688, games/role path effects 0.0000.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 242.09963 | 121.76656 |
| on_40man | 1.00000 | 61.14065 |
| regular_window_scaled | 0.33333 | 36.48091 |
| quality_0 | -0.20354 | -18.90891 |
| age_centered | 1.20000 | -14.06165 |
| pooled_mlb_quality | -0.14738 | -12.48059 |
| pooled_MLB_K | 0.20284 | 10.36114 |
| work_2 | 583.00000 | 9.63848 |
| MLB_0_pa | 242.00000 | 4.40458 |
| work_1 | 369.00000 | -3.88294 |
| pooled_MLB_BB | 0.06505 | 3.71374 |
| MLB_2_pa | 583.00000 | 3.69090 |

Games workload: reference 39.0498, raw prediction 207.7823, games/role path effects -55.6350.

| Path feature | Actual input | Accounting effect (PA) |
|---|---:|---:|
| work_0 | 242.09963 | 138.95924 |
| on_40man | 1.00000 | 63.29555 |
| role_mlb_0 | 2.41026 | -51.14858 |
| regular_window_scaled | 0.33333 | 27.20089 |
| quality_0 | -0.20354 | -15.88665 |
| age_centered | 1.20000 | -15.62272 |
| MLB_0_pa | 242.00000 | 12.04308 |
| pooled_MLB_K | 0.20284 | 9.83314 |
| pooled_MLB_pa | 887.00000 | 9.37046 |
| pooled_mlb_quality | -0.14738 | -5.33284 |
| role_pool_MLB | 3.09000 | -4.31593 |
| games_mlb_0 | 107.00000 | -3.58015 |

Ordinary delivered-value case, but with cancellation. PA falls 235→208 as current role shrinks to 242 PA/107 games (stabilized 2.410 per appearance), versus later 300. New role_mlb_0 has about −51 PA path effect, a sensible downward use signal. Contribution 0.2155 nearly equals realized 0.2155 because the unchanged batting rate is less negative than the realized rate; both components are not simultaneously correct. Grossman exits, Higashioka gets 327 PA and Taylor 125, supporting varied future roles.

Origin-selected peers: Robbie Grossman (MLB/AAA/AA PA 245/12.0/0.0; control→games→actual PA 61.9→54.3→0; realized value 0.000); Kyle Higashioka (MLB/AAA/AA PA 263/0.0/0.0; control→games→actual PA 199.4→191.5→327; realized value 0.728); Chris Taylor (MLB/AAA/AA PA 246/13.0/0.0; control→games→actual PA 191.8→173.5→125; realized value -0.244).

Games/role training profile: 144 distinct players. This sparse-profile diagnostic does not certify medical/job-context support.

## Disposition

Retain as a promising research workload extension, not a promoted working forecast. All-cohort PA improves, upper-minor totals and brief-debut PA improve, but public MAE remains worse than V33b, value gains are small/uncertain, 2023 cohort over-allocation grows and major newcomer/return cases remain missed. Do not drop it as useless; do not claim it finishes the hitter model.

The remaining question is workload architecture: one shared population learner may underrepresent the different use/retention process of current MLB hitters. Next test one origin-known current-MLB workload head, keeping the existing non-MLB head and same batting rate/cohorts/settings. This is not future-outcome gating or a new algorithm sweep.
