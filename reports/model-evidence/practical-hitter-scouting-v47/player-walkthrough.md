# Historical scouting and MLB playing time

Historical rankings improve readiness forecasts for some highly ranked prospects, but stale preseason absence harms newly drafted and rising prospects. This review covers fifteen actual model cases after nine source cases. The comparison predicts next-calendar-year MLB PA and batting-plus-replacement contribution, not full WAR, a guaranteed role, present-day MLB skill or six years of club control.

All 30,506 forecasts are retained, including non-arrivals and 218 unverified roster-only cases. Origins 2016–2018 and 2021–2024 predict 2017–2019 and 2022–2025. Target 2020 is excluded; its source MLB evidence is preserved and canceled MiLB is not zero performance. Each model excludes the held player group and future labels. Twelve rank inputs are added to 239 count/games/draft inputs; hitting rate is exactly unchanged.

Peers use origin age, stage, debut status, workload, quality and ranking distance without future outcomes; they do not guarantee identical draft pedigree or contact shape. The full 251 inputs, tree paths, history and support are in cases.json. Path terms reconstruct a fitted mean, not causal changes between two refitted ensembles. Unknown list evidence is -1, not zero talent. Annual rank tables are retrospective reproductions, not certified archived editions; the Brinson source disagreement remains disclosed.

## Aaron Judge 2016 to 2017

Player 592450, row 23934, fold 3; fixed diagnostic, value false low. Age 24.0; Current MLB; career observed MLB PA 95.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

Source ranks: [{'season': 2015, 'player_id': 592450, 'rank': 68, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Aaron Judge'}, {'season': 2016, 'player_id': 592450, 'rank': 31, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Aaron Judge'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.7, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.33, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 150.2046 | -0.05720 | 0.449525 |
| scout | 208.0137 | -0.05720 | 0.622533 |
| retired_safe_ridge | 143.9656 | -0.05720 | 0.430853 |
| Actual | 678 | 5.329875619792154 | 8.108407 |

Raw candidate PA 208.013735; bounded and availability-adjusted PA 208.013735. Contribution = 208.013735 × (-0.057204/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 38.357092 plus the complete stored terms reconstructs raw PA 150.204635.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| on_40man | 1.0 | 75.498701 |
| role_pool_AAA | 4.334650856389986 | 38.928232 |
| MLB_0_pa | 95.0 | 24.512022 |
| pooled_MLB_K | 0.3333333333333333 | -12.963409 |
| pooled_AAA_2B | 0.04317548746518106 | -12.710632 |
| age_centered | -0.6 | 12.462715 |
| pooled_Aplus_K | 0.244280442804428 | 9.264230 |
| role_pool_A | 4.220408163265306 | 7.668758 |

### Ranking candidate fitted path

Reference 38.360995 plus the complete stored terms reconstructs raw PA 208.013735.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| on_40man | 1.0 | 77.809688 |
| scout_rank_score_0 | 0.7 | 68.831333 |
| role_pool_AAA | 4.334650856389986 | 29.398771 |
| MLB_0_pa | 95.0 | 21.200273 |
| pooled_MLB_K | 0.3333333333333333 | -11.369663 |
| pooled_AA_K | 0.24382716049382716 | -10.481138 |
| pooled_AA_BABIP | 0.3260135135135135 | -10.423347 |
| age_centered | -0.6 | 9.059207 |
| scout_rank_score_1 | 0.33 | -0.001083 |

General distinct-player profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Rank-specific profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 53}]. Actual mature training support: [{'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 181, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Judge had 19 AAA home runs in 410 PA but struck out 42 times in his 95-PA MLB debut. The unchanged shrinkage-based MLB batting head is only -0.057 batting wins/600; the ranking experiment cannot repair that talent estimate. His rank 31 score enters the new path positively (68.83 PA accounting), while roster and AAA exposure remain major terms. Expected PA rises 150 to 208, still far below 678; expected contribution rises only .45 to .62 versus 8.11 observed. This is an opportunity improvement and a continuing talent/arrival miss, not prediction of his historic breakout. Origin-selected Reed, Bell, Moya and Austin subsequently produced 6, 620, 0 and 46 PA: a promising debut is not a guaranteed regular job. The rank-profile fold has 53 people, not 53 Judge-like superstars.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AJ Reed | 23.0 | 141 | 296 | 1.0 | 0.61 | 202.74 | 200.89 | 6 | -0.14152 |
| Josh Bell | 23.0 | 152 | 484 | 1.0 | 0.52 | 221.71 | 247.53 | 620 | 2.87812 |
| Steven Moya | 24.0 | 100 | 426 | 0.0 | 0.0 | 203.47 | 199.05 | 0 | 0.00000 |
| Tyler Austin | 24.0 | 90 | 444 | 0.0 | 0.0 | 144.43 | 144.07 | 46 | 0.05556 |

## Cody Bellinger 2016 to 2017

Player 641355, row 24967, fold 3; fixed diagnostic, pa false low. Age 20.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 51 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 128 | 30 | 150 | 51 |
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 7.7613 | 0.08471 | 0.025064 |
| scout | 2.7257 | 0.08471 | 0.008802 |
| retired_safe_ridge | 35.5162 | 0.08471 | 0.114692 |
| Actual | 548 | 2.700470664969068 | 4.152174 |

Raw candidate PA 2.725669; bounded and availability-adjusted PA 2.725669. Contribution = 2.725669 × (0.084712/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 38.357092 plus the complete stored terms reconstructs raw PA 7.761347.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 0.0 | -12.271751 |
| work_0 | 0.0 | -9.937320 |
| on_40man | 0.0 | -6.100592 |
| pooled_AA_HR | 0.04601769911504425 | 4.731895 |
| pooled_Aplus_K | 0.26718983557548576 | 2.960506 |
| pooled_Aplus_HR | 0.050448430493273536 | 2.615448 |
| role_pool_AAA | 4.0 | -2.265421 |
| quality_0 | 0.0 | -2.147850 |

### Ranking candidate fitted path

Reference 38.360995 plus the complete stored terms reconstructs raw PA 2.725669.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 0.0 | -12.257004 |
| work_0 | 0.0 | -9.844864 |
| on_40man | 0.0 | -6.002622 |
| pooled_Aplus_HR | 0.050448430493273536 | 2.342788 |
| quality_0 | 0.0 | -2.129351 |
| role_pool_AAA | 4.0 | -1.590428 |
| pooled_AAA_HR | 0.05357142857142857 | -1.497736 |
| role_mlb_0 | 4.0 | -1.314036 |
| scout_rank_score_0 | 0.0 | -0.474847 |
| scout_listed_0 | 0.0 | -0.014551 |
| scout_rank_score_2 | 0.0 | -0.004789 |
| scout_rank_score_1 | 0.0 | -0.001083 |

General distinct-player profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 744}]. Rank-specific profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1030}]. Actual mature training support: [{'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Bellinger's 2016 evidence includes 23 AA HR, 94 K and 57 BB in 465 PA, plus three AAA homers in only 12 PA; the latter is not a reliable full-season rate. The preseason lists show no ranking even though the reviewed scouting dataset contains a 2016 report. The fitted no-MLB/no-roster branches dominate, and the new fit reduces PA 7.76 to 2.73 versus 548 observed. No-listing is not absence of scouting or zero talent; it is stale preseason evidence. The fixed rate .085 batting wins/600 also substantially misses his actual 2.70. Rijo, Verdugo, Leyba and Urena are age/exposure/rank-selected peers with 0, 25, 0 and 75 next-year PA, supporting uncertainty but not excusing the lost fast-mover representation. Broad not-listed training support does not establish support for Bellinger's precise combination of age, AA power and rapid advancement.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Wendell Rijo | 20.0 | 0 | 441 | 0.0 | 0.0 | 0.37 | 0.77 | 0 | 0.00000 |
| Alex Verdugo | 20.0 | 0 | 529 | 0.0 | 0.0 | 38.52 | 18.93 | 25 | -0.08615 |
| Domingo Leyba | 20.0 | 0 | 548 | 0.0 | 0.0 | 64.61 | 66.50 | 0 | 0.00000 |
| Richard Urena | 20.0 | 0 | 563 | 0.0 | 0.0 | 85.86 | 73.74 | 75 | -0.17775 |

## Anthony Volpe 2022 to 2023

Player 683011, row 48516, fold 4; fixed diagnostic, pa largest gain. Age 21.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 257 | 54 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 55 | 15 | 58 | 26 |
| 2022 | AA | 497 | 110 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 22 | 3 | 30 | 8 |

Source ranks: [{'season': 2022, 'player_id': 683011, 'rank': 8, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Anthony Volpe'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.93, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 99.0, 'scout_listed_1': -1.0, 'scout_rank_score_1': -1.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 166.1382 | -0.14770 | 0.479277 |
| scout | 415.7351 | -0.14770 | 1.199317 |
| retired_safe_ridge | 63.2182 | -0.07924 | 0.189585 |
| Actual | 601 | -1.3447727729230707 | 0.513728 |

Raw candidate PA 415.735103; bounded and availability-adjusted PA 415.735103. Contribution = 415.735103 × (-0.147697/600 + 0.00313097). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 38.773582 plus the complete stored terms reconstructs raw PA 166.138177.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| role_pool_AAA | 4.34375 | 59.842622 |
| age_centered | -1.2 | 38.942856 |
| role_pool_AA | 4.475 | 28.539544 |
| work_0 | 0.0 | -23.047864 |
| Aplus_1_pa | 256.0 | 10.573611 |
| pooled_A_3B | 0.014725130890052354 | 8.985924 |
| pooled_AA_K | 0.18592964824120603 | 7.545442 |
| on_40man | 0.0 | -6.124249 |

### Ranking candidate fitted path

Reference 38.775575 plus the complete stored terms reconstructs raw PA 415.735103.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| scout_rank_score_0 | 0.93 | 272.195242 |
| role_pool_AAA | 4.34375 | 50.403268 |
| role_pool_AA | 4.475 | 27.078973 |
| age_centered | -1.2 | 24.166000 |
| work_0 | 0.0 | -22.444608 |
| Aplus_1_pa | 256.0 | 7.540895 |
| pooled_AA_K | 0.18592964824120603 | 6.405259 |
| on_40man | 0.0 | -6.235464 |
| scout_rank_score_1 | -1.0 | -0.023936 |

General distinct-player profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1502}]. Rank-specific profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 15}]. Actual mature training support: [{'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10086, 'current_players': 10584, 'regular_players': 10685, 'joint_players': 8356, 'quality_joint_players': 10163, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Volpe had 596 minor PA, mostly AA, with 21 HR, 118 K and 65 BB across AA/AAA. Verified preseason rank 8 supplies information not contained in his draft pick 30 or no-MLB state. The new rank-score path accounts for 272 PA within the refitted model; the net change is 249.60 PA, not that path term interpreted causally. Expected PA rises 166 to 416 versus 601, the largest PA gain. Yet contribution worsens .479 to 1.199 versus .514 because the unchanged rate -.148 is much more optimistic than the actual -1.345 batting wins/600. A workload win does not guarantee a value win. Only 15 distinct people match the coarse top20/stage/debut/age profile. Valera, Walker, Veen and Hassell have 0, 465, 0 and 0 next-year PA; rankings help opportunity, not certainty. Partial 2020/21 list absence remains unknown, not negative evidence.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| George Valera | 21.0 | 0 | 566 | 1.0 | 0.54 | 152.04 | 147.43 | 0 | 0.00000 |
| Jordan Walker | 20.0 | 0 | 536 | 1.0 | 0.71 | 64.91 | 80.14 | 465 | 2.39119 |
| Zac Veen | 20.0 | 0 | 541 | 1.0 | 0.65 | 29.90 | 73.48 | 0 | 0.00000 |
| Robert Hassell III | 20.0 | 0 | 513 | 1.0 | 0.64 | 42.54 | 53.12 | 0 | 0.00000 |

## Nick Kurtz 2024 to 2025

Player 701762, row 57052, fold 2; fixed diagnostic. Age 21.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 29.9431 | -0.13556 | 0.086782 |
| scout | 2.9477 | -0.13556 | 0.008543 |
| retired_safe_ridge | 50.4937 | -0.11288 | 0.148251 |
| Actual | 489 | 5.150009420178844 | 5.720989 |

Raw candidate PA 2.947721; bounded and availability-adjusted PA 2.947721. Contribution = 2.947721 × (-0.135562/600 + 0.00312416). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.289435 plus the complete stored terms reconstructs raw PA 29.943090.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 26.886700 |
| work_0 | 0.0 | -22.958102 |
| on_40man | 0.0 | -6.293909 |
| pooled_AA_BABIP | 0.3090909090909091 | 2.118989 |
| quality_0 | 0.0 | -1.687118 |
| role_pool_AA | 3.6666666666666665 | -1.463170 |
| pooled_MLB_BABIP | 0.3 | 1.427221 |
| pooled_AA_BB | 0.08695652173913043 | 1.418949 |

### Ranking candidate fitted path

Reference 39.295575 plus the complete stored terms reconstructs raw PA 2.947721.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 0.0 | -22.724470 |
| on_40man | 0.0 | -6.341280 |
| draft_rank | 0.8176145045277415 | 3.707225 |
| quality_0 | 0.0 | -1.632186 |
| role_pool_AAA | 4.0 | -1.394480 |
| regular_window_scaled | 0.0 | -1.125509 |
| pooled_mlb_quality | 0.0 | -0.761626 |
| pooled_AAA_HR | 0.03 | -0.645434 |
| scout_rank_score_0 | 0.0 | -0.565014 |
| scout_rank_score_1 | 0.0 | -0.037519 |
| scout_listed_1 | 0.0 | -0.018149 |
| scout_rank_score_2 | 0.0 | 0.001703 |

General distinct-player profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1744}]. Rank-specific profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 2137}]. Actual mature training support: [{'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11239, 'current_players': 11751, 'regular_players': 11845, 'joint_players': 9411, 'quality_joint_players': 11314, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Kurtz was drafted fourth and reached AA but had only 50 pro PA; 4 HR and 12 BB are encouraging, not enough to estimate elite MLB talent. Preseason 2024 rankings necessarily predate that draft. The source truth is not-listed then, but its interpretation at the end-of-year forecast is stale/uninformative about his post-draft standing. In the refitted model the draft-rank path term falls from 26.89 to 3.71 PA and expected PA falls 29.94 to 2.95 versus 489. This is a meaningful lost representation, not proof that Kurtz's later elite outcome was fully predictable. His fixed -.136 batting wins/600 also misses actual 5.15. Montgomery, Hartl, Soto and Tapia are exposure/age-selected peers with zero next-year MLB PA; these comparisons omit draft-pedigree similarity and cannot justify treating every 50-PA player alike. The large unranked training count masks the narrower newly drafted top-pick profile. Preserve this failed case and repair source applicability before treating rankings as a complete readiness model.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benny Montgomery | 21.0 | 0 | 48 | 0.0 | 0.0 | 40.93 | 9.43 | 0 | 0.00000 |
| Ben Hartl | 21.0 | 0 | 57 | 0.0 | 0.0 | 0.00 | 0.00 | 0 | 0.00000 |
| Wally Soto | 21.0 | 0 | 85 | 0.0 | 0.0 | 8.74 | 0.63 | 0 | 0.00000 |
| Sergio Tapia | 21.0 | 0 | 103 | 0.0 | 0.0 | 0.00 | 0.01 | 0 | 0.00000 |

## Carlos Concepcion 2024 to 2025

Player 808393, row 57990, fold 4; fixed diagnostic. Age 18.0; Lower minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | DSL | 133 | 33 | 4 | 29 | 13 |
| 2024 | DSL | 199 | 47 | 3 | 61 | 23 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 0.0000 | 0.21322 | 0.000000 |
| scout | 0.0000 | 0.21322 | 0.000000 |
| retired_safe_ridge | 0.0000 | 0.22668 | 0.000000 |
| Actual | 0 | Unobserved at zero PA | 0.000000 |

Raw candidate PA -0.114657; bounded and availability-adjusted PA 0.000000. Contribution = 0.000000 × (0.213215/600 + 0.00312416). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.691709 plus the complete stored terms reconstructs raw PA -0.172250.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 0.0 | -22.510160 |
| on_40man | 0.0 | -6.473896 |
| role_pool_AAA | 4.0 | -1.427338 |
| quality_0 | 0.0 | -1.243405 |
| MLB_0_pa | 0.0 | -1.158994 |
| regular_window_scaled | 0.0 | -1.077427 |
| role_pool_AA | 4.0 | -0.868240 |
| pooled_mlb_quality | 0.0 | -0.682089 |

### Ranking candidate fitted path

Reference 39.700184 plus the complete stored terms reconstructs raw PA -0.114657.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 0.0 | -22.047531 |
| on_40man | 0.0 | -6.104559 |
| role_pool_AAA | 4.0 | -1.356524 |
| MLB_0_pa | 0.0 | -1.310058 |
| regular_window_scaled | 0.0 | -1.282305 |
| quality_0 | 0.0 | -1.069435 |
| pooled_mlb_quality | 0.0 | -0.770164 |
| pooled_MLB_K | 0.23 | -0.711762 |
| scout_rank_score_0 | 0.0 | -0.470884 |
| scout_listed_0 | 0.0 | -0.153081 |
| scout_rank_score_1 | 0.0 | -0.021315 |
| scout_rank_score_2 | 0.0 | 0.006502 |

General distinct-player profile: [{'row_id': 57990, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'current_work_band': 'absent', 'draft_known': 0, 'profile_players': 4513}]. Rank-specific profile: [{'row_id': 57990, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'not_listed', 'rank_profile_players': 4891}]. Actual mature training support: [{'row_id': 57990, 'horizon': 1, 'player_id': 808393, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11349, 'current_players': 11852, 'regular_players': 11954, 'joint_players': 9494, 'quality_joint_players': 11427, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Concepcion's actual captured history is 133 DSL PA in 2023 and 199 in 2024, including 61 K and 3 HR in 2024. No older season is fabricated; this panel does not prove his full DSL tenure. His no-MLB/no-roster inputs produce a negative raw mean clipped to zero PA in both fits, correctly matching no 2025 MLB appearance. The unchanged positive .213 batting wins/600 should not be described as a directly validated MLB-ready skill grade: a zero-PA target cannot validate conditional talent or longer-term prospect value. Similar-age DSL/exposure peers also have no next-year MLB PA. Their 4,891-person coarse rank profile establishes broad sample coverage, not confidence in a six-year valuation. There is no defensive or position-value boost in this test.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hector Liriano | 18.0 | 0 | 199 | 0.0 | 0.0 | 0.00 | 0.00 | 0 | 0.00000 |
| Gery Holguin | 18.0 | 0 | 201 | 0.0 | 0.0 | 0.00 | 0.00 | 0 | 0.00000 |
| Jesus Alexander | 18.0 | 0 | 197 | 0.0 | 0.0 | 0.00 | 0.01 | 0 | 0.00000 |
| Angel Guzman | 18.0 | 0 | 201 | 0.0 | 0.0 | 0.00 | 0.00 | 0 | 0.00000 |

## Lewis Brinson 2016 to 2017

Player 621446, row 24603, fold 0; fixed diagnostic. Age 22.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 186 | 43 | 10 | 46 | 18 |
| 2014 | Aplus | 199 | 46 | 3 | 50 | 15 |
| 2015 | AA | 121 | 28 | 6 | 28 | 6 |
| 2015 | AAA | 37 | 8 | 1 | 6 | 7 |
| 2015 | Aplus | 298 | 64 | 13 | 64 | 31 |
| 2016 | AA | 326 | 77 | 11 | 64 | 17 |
| 2016 | AAA | 93 | 23 | 4 | 21 | 2 |
| 2016 | RK121 | 15 | 4 | 0 | 2 | 2 |

Source ranks: [{'season': 2016, 'player_id': 621446, 'rank': 16, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Lewis Brinson'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.85, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 120.7498 | -0.13099 | 0.346525 |
| scout | 253.7918 | -0.13099 | 0.728325 |
| retired_safe_ridge | 137.3620 | -0.13099 | 0.394198 |
| Actual | 55 | -4.87094776737043 | -0.277314 |

Raw candidate PA 253.791760; bounded and availability-adjusted PA 253.791760. Contribution = 253.791760 × (-0.130991/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 37.909396 plus the complete stored terms reconstructs raw PA 120.749824.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| on_40man | 1.0 | 78.125317 |
| MLB_0_pa | 0.0 | -35.265317 |
| pooled_AAA_HR | 0.03504043126684636 | 9.780883 |
| pooled_AAA_2B | 0.06648697214734951 | 9.054763 |
| pooled_AAA_HBP | 0.004492362982929021 | 7.038236 |
| work_0 | 0.0 | -6.751535 |
| pooled_AAA_BABIP | 0.37744034707158347 | 6.524917 |
| pooled_Aplus_BB | 0.09130624726955001 | 5.138240 |

### Ranking candidate fitted path

Reference 37.917160 plus the complete stored terms reconstructs raw PA 253.791760.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| scout_rank_score_0 | 0.85 | 159.314372 |
| on_40man | 1.0 | 80.288386 |
| MLB_0_pa | 0.0 | -31.772168 |
| pooled_AAA_2B | 0.06648697214734951 | 9.776971 |
| pooled_AAA_HR | 0.03504043126684636 | 7.570819 |
| work_0 | 0.0 | -7.444056 |
| games_mlb_0 | 0.0 | -5.737643 |
| pooled_mlb_quality | 0.0 | -4.549504 |
| scout_rank_score_1 | 0.0 | 0.032848 |
| scout_rank_score_2 | 0.0 | 0.007851 |

General distinct-player profile: [{'row_id': 24603, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 730}]. Rank-specific profile: [{'row_id': 24603, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 9}]. Actual mature training support: [{'row_id': 24603, 'horizon': 1, 'player_id': 621446, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Brinson had meaningful AA/AAA experience, 15 HR there in 2016 and a roster flag, plus verified rank 16 in the retrospective table. The source review separately documents disagreement with a contemporary launch narrative; rank vintage remains qualified. New rank-score accounting is +159 PA inside the fit, pushing the actual mean from 121 to 254 versus 55 next year; contribution worsens .347 to .728 versus -.277. This is the intended opposite-risk case: scouting confidence can overpredict even with reassuring production. Only nine people match the coarse top20 profile. Winker, Phillips, Williams and Meadows have next-year PA 137, 98, 343 and 0, making the observed range clear. Do not label Brinson a source error or use his later failure to erase the origin ranking.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jesse Winker | 22.0 | 0 | 463 | 1.0 | 0.67 | 144.23 | 221.21 | 137 | 1.14962 |
| Brett Phillips | 22.0 | 0 | 517 | 1.0 | 0.69 | 84.06 | 146.19 | 98 | 0.38347 |
| Nick Williams | 22.0 | 0 | 527 | 1.0 | 0.37 | 74.25 | 140.42 | 343 | 1.82007 |
| Austin Meadows | 21.0 | 0 | 352 | 1.0 | 0.81 | 50.94 | 194.97 | 0 | 0.00000 |

## Clint Frazier 2016 to 2017

Player 640449, row 24933, fold 0; fixed diagnostic. Age 21.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 542 | 120 | 13 | 161 | 55 |
| 2015 | Aplus | 588 | 133 | 16 | 125 | 66 |
| 2016 | AA | 391 | 89 | 13 | 86 | 41 |
| 2016 | AAA | 129 | 30 | 3 | 36 | 7 |

Source ranks: [{'season': 2014, 'player_id': 640449, 'rank': 48, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}, {'season': 2015, 'player_id': 640449, 'rank': 53, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}, {'season': 2016, 'player_id': 640449, 'rank': 27, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.74, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.48, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.53}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 145.2902 | -0.00117 | 0.448386 |
| scout | 236.1163 | -0.00117 | 0.728689 |
| retired_safe_ridge | 137.9509 | -0.00117 | 0.425736 |
| Actual | 142 | -0.9678557871572135 | 0.207758 |

Raw candidate PA 236.116290; bounded and availability-adjusted PA 236.116290. Contribution = 236.116290 × (-0.001169/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 37.909396 plus the complete stored terms reconstructs raw PA 145.290247.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| draft_rank | 0.7882569969815056 | 40.203498 |
| role_pool_AAA | 4.225 | 26.129291 |
| role_pool_AA | 4.353535353535354 | 20.127765 |
| role_minor_0 | 4.341085271317829 | 16.311629 |
| MLB_0_pa | 0.0 | -15.669638 |
| pooled_AAA_3B | 0.019650655021834062 | 12.001395 |
| Aplus_1_pa | 588.0 | 11.399855 |
| pooled_Aplus_2B | 0.05925666199158484 | 9.361382 |

### Ranking candidate fitted path

Reference 37.917160 plus the complete stored terms reconstructs raw PA 236.116290.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| scout_rank_score_0 | 0.74 | 140.800604 |
| role_pool_AAA | 4.225 | 21.830666 |
| role_pool_AA | 4.353535353535354 | 16.775448 |
| Aplus_1_pa | 588.0 | 14.641297 |
| MLB_0_pa | 0.0 | -14.225339 |
| pooled_AAA_3B | 0.019650655021834062 | 11.056810 |
| role_minor_0 | 4.341085271317829 | 8.076240 |
| work_0 | 0.0 | -7.444056 |
| scout_rank_score_1 | 0.48 | 0.027725 |

General distinct-player profile: [{'row_id': 24933, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 730}]. Rank-specific profile: [{'row_id': 24933, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 43}]. Actual mature training support: [{'row_id': 24933, 'horizon': 1, 'player_id': 640449, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Frazier had 520 AA/AAA PA in 2016, 16 HR, 122 K and 48 BB; rank 27 followed earlier ranks 48 and 53. Adding rankings increases expected PA 145 to 236 versus 142 actual. The old forecast was already close on workload; the rank path accounts for +140.80 PA inside a refitted ensemble, partly replacing draft/age/exposure accounting rather than representing a causal additional 141 PA. Contribution also worsens .448 to .729 versus .208, because rate remains -.001 while actual rate is -.968. Rank-specific support is 43 distinct people. McMahon, Crawford, Smith and Meadows produce 24, 87, 183 and 0 PA, so a high-ranked upper-minor hitter still has appreciable delay/non-arrival risk. Player ID is the verified Clint Frazier 640449, not Adam Frazier.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ryan McMahon | 21.0 | 0 | 535 | 1.0 | 0.53 | 24.36 | 57.56 | 24 | -0.02515 |
| J.P. Crawford | 21.0 | 0 | 551 | 1.0 | 0.96 | 105.85 | 275.86 | 87 | 0.15713 |
| Dominic Smith | 21.0 | 0 | 542 | 1.0 | 0.5 | 37.19 | 42.90 | 183 | 0.00276 |
| Austin Meadows | 21.0 | 0 | 352 | 1.0 | 0.81 | 50.94 | 194.97 | 0 | 0.00000 |

## Corey Seager 2016 to 2017

Player 608369, row 24459, fold 0; fixed diagnostic. Age 22.0; Current MLB; career observed MLB PA 800.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | AA | 161 | 38 | 2 | 39 | 10 |
| 2014 | Aplus | 365 | 80 | 18 | 76 | 28 |
| 2015 | AA | 86 | 20 | 5 | 11 | 4 |
| 2015 | AAA | 464 | 105 | 13 | 65 | 30 |
| 2015 | MLB | 113 | 27 | 4 | 19 | 13 |
| 2016 | MLB | 687 | 157 | 26 | 133 | 49 |

Source ranks: [{'season': 2014, 'player_id': 608369, 'rank': 34, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}, {'season': 2015, 'player_id': 608369, 'rank': 7, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}, {'season': 2016, 'player_id': 608369, 'rank': 1, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 1.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.94, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.67}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 607.8318 | 1.69974 | 3.598970 |
| scout | 641.9172 | 1.69974 | 3.800790 |
| retired_safe_ridge | 575.7635 | 1.69974 | 3.409093 |
| Actual | 613 | 2.1848833518965316 | 4.117918 |

Raw candidate PA 641.917239; bounded and availability-adjusted PA 641.917239. Contribution = 641.917239 × (1.699743/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 37.909396 plus the complete stored terms reconstructs raw PA 607.831756.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 687.0 | 234.736840 |
| work_0 | 687.5658978583195 | 75.186336 |
| role_mlb_0 | 4.3532934131736525 | 57.560439 |
| regular_window_scaled | 0.3333333333333333 | 37.141496 |
| quality_0 | 0.9963063950369828 | 36.313494 |
| role_pool_MLB | 4.334040296924709 | 28.112321 |
| games_mlb_0 | 157.0 | 23.676215 |
| role_pool_AAA | 4.3744680851063835 | 22.329887 |

### Ranking candidate fitted path

Reference 37.917160 plus the complete stored terms reconstructs raw PA 641.917239.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 687.0 | 207.466096 |
| work_0 | 687.5658978583195 | 82.898379 |
| scout_rank_score_0 | 1.0 | 77.734453 |
| role_mlb_0 | 4.3532934131736525 | 56.706067 |
| quality_0 | 0.9963063950369828 | 48.019472 |
| regular_window_scaled | 0.3333333333333333 | 38.213046 |
| games_mlb_0 | 157.0 | 26.464457 |
| role_pool_AAA | 4.3744680851063835 | 22.781142 |
| scout_rank_score_1 | 0.94 | -9.488035 |

General distinct-player profile: [{'row_id': 24459, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 45}]. Rank-specific profile: [{'row_id': 24459, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 22}]. Actual mature training support: [{'row_id': 24459, 'horizon': 1, 'player_id': 608369, 'origin_year': 2016, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 22.0, 'quality_0': 0.9963063950369828, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 399, 'current_players': 307, 'regular_players': 269, 'joint_players': 14, 'quality_joint_players': 111, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False}].

Seager's 687 MLB PA, 26 HR and strong MLB quality already establish him as a regular. His preseason rank 1 is real but largely superseded by that season's MLB evidence. Expected PA rises 608 to 642 versus 613, a workload deterioration, while contribution rises 3.599 to 3.801 versus 4.118 and therefore improves through compensation for an underestimated fixed hitting rate (1.70 versus 2.18 actual). Do not describe both endpoints as a win. New rank accounting is +77.73 within the model, while the net change is only 34.09 because other terms change. The coarse rank profile has 22 people. Mazara, Lindor, Odor and Machado span 616 to 723 PA with very different batting results; ranking should not indefinitely dominate established production.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nomar Mazara | 21.0 | 568 | 13 | 1.0 | 0.83 | 445.55 | 485.39 | 616 | 1.73244 |
| Francisco Lindor | 22.0 | 684 | 0 | 0.0 | 0.0 | 569.86 | 585.80 | 723 | 4.03895 |
| Rougned Odor | 22.0 | 632 | 0 | 0.0 | 0.0 | 592.32 | 586.49 | 651 | -0.58638 |
| Manny Machado | 23.0 | 696 | 0 | 0.0 | 0.0 | 621.90 | 608.32 | 690 | 2.62526 |

## Wyatt Langford 2023 to 2024

Player 694671, row 53164, fold 4; pa largest harm. Age 21.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | AA | 54 | 12 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 5 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 24 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 3 | 1 | 3 | 1 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 216.8065 | 0.64269 | 0.903483 |
| scout | 116.4268 | 0.64269 | 0.485178 |
| retired_safe_ridge | 104.9757 | 0.65624 | 0.439827 |
| Actual | 557 | 0.5490777231604176 | 2.249169 |

Raw candidate PA 116.426835; bounded and availability-adjusted PA 116.426835. Contribution = 116.426835 × (0.642693/600 + 0.00309608). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.261690 plus the complete stored terms reconstructs raw PA 216.806522.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| role_pool_AAA | 4.4 | 63.982854 |
| age_centered | -1.2 | 55.948880 |
| draft_rank | 0.8176145045277415 | 34.291347 |
| work_0 | 0.0 | -23.131149 |
| role_pool_AA | 4.2727272727272725 | 17.936033 |
| pooled_AA_HR | 0.045454545454545456 | 11.960028 |
| pooled_Aplus_2B | 0.06310679611650485 | 8.988449 |
| on_40man | 0.0 | -6.246637 |

### Ranking candidate fitted path

Reference 39.266734 plus the complete stored terms reconstructs raw PA 116.426835.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| role_pool_AAA | 4.4 | 54.317507 |
| work_0 | 0.0 | -22.003749 |
| age_centered | -1.2 | 19.389707 |
| role_pool_AA | 4.2727272727272725 | 16.375098 |
| on_40man | 0.0 | -6.211989 |
| pooled_Aplus_2B | 0.06310679611650485 | 5.903926 |
| pooled_AA_HR | 0.045454545454545456 | 4.785144 |
| pooled_AAA_BB | 0.1111111111111111 | 4.732983 |
| scout_rank_score_0 | 0.0 | -2.215434 |
| scout_rank_score_1 | 0.0 | -1.043326 |
| scout_listed_0 | 0.0 | -0.275882 |
| scout_listed_1 | 0.0 | -0.008416 |
| scout_rank_score_2 | -1.0 | 0.002049 |

General distinct-player profile: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1650}]. Rank-specific profile: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1972}]. Actual mature training support: [{'row_id': 53164, 'horizon': 1, 'player_id': 694671, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10725, 'current_players': 11226, 'regular_players': 11325, 'joint_players': 8919, 'quality_joint_players': 10803, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Langford's first pro season includes 200 PA across rookie/Aplus/AA/AAA, 10 HR and 36 BB, with AA/AAA advancement already visible. Pick four is known. Like Kurtz, he could not appear as a pro in that year's preseason list. The new fit lowers expected PA 217 to 116 versus 557, the largest PA deterioration; contribution falls .903 to .485 versus 2.249. Draft/age accounting shrinks despite unchanged source production. Bannister, Wilken, Morales and Bush are age/exposure/rank-selected but not equivalent top-four pedigree peers, and all have zero next-year MLB PA. Their outcomes illustrate why rare entrants are difficult, not why Langford's evidence should be compressed into the generic unlisted group. This recurring newly drafted fast-mover harm motivates a source-applicability correction, not tuning specifically to his outcome.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Zion Bannister | 21.0 | 0 | 200 | 0.0 | 0.0 | 9.63 | 4.58 | 0 | 0.00000 |
| Brock Wilken | 21.0 | 0 | 203 | 0.0 | 0.0 | 9.54 | 1.38 | 0 | 0.00000 |
| Yohandy Morales | 21.0 | 0 | 189 | 0.0 | 0.0 | 2.18 | 2.06 | 0 | 0.00000 |
| Homer Bush Jr. | 21.0 | 0 | 187 | 0.0 | 0.0 | 0.78 | 1.55 | 0 | 0.00000 |

## Miguel Andujar 2018 to 2019

Player 609280, row 33062, fold 4; pa false high. Age 23.0; Current MLB; career observed MLB PA 614.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | AA | 319 | 72 | 2 | 42 | 21 |
| 2016 | Aplus | 251 | 58 | 10 | 30 | 18 |
| 2017 | AA | 272 | 67 | 7 | 38 | 12 |
| 2017 | AAA | 250 | 58 | 9 | 33 | 16 |
| 2017 | MLB | 8 | 5 | 0 | 0 | 1 |
| 2018 | MLB | 606 | 149 | 27 | 97 | 23 |

Source ranks: [{'season': 2018, 'player_id': 609280, 'rank': 65, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Miguel Andujar'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.36, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 568.3532 | 0.97225 | 2.670793 |
| scout | 613.9356 | 0.97225 | 2.884992 |
| retired_safe_ridge | 579.5494 | 0.97225 | 2.723405 |
| Actual | 49 | -10.043988716563746 | -0.670576 |

Raw candidate PA 613.935608; bounded and availability-adjusted PA 613.935608. Contribution = 613.935608 × (0.972246/600 + 0.00307877). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 38.550161 plus the complete stored terms reconstructs raw PA 568.353225.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 606.0 | 169.194657 |
| work_0 | 605.7507198683669 | 133.885995 |
| quality_0 | 0.7932473892702949 | 55.295569 |
| role_mlb_0 | 4.062893081761007 | 49.419999 |
| regular_window_scaled | 0.3333333333333333 | 25.074856 |
| age_centered | -0.8 | 18.111731 |
| role_pool_MLB | 4.002453987730061 | 16.685569 |
| pooled_mlb_quality | 0.8431366300375014 | 15.321020 |

### Ranking candidate fitted path

Reference 38.551099 plus the complete stored terms reconstructs raw PA 613.935608.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 606.0 | 170.945544 |
| work_0 | 605.7507198683669 | 124.467881 |
| quality_0 | 0.7932473892702949 | 54.908858 |
| role_mlb_0 | 4.062893081761007 | 49.037481 |
| regular_window_scaled | 0.3333333333333333 | 30.430728 |
| scout_rank_score_0 | 0.36 | 22.160268 |
| age_centered | -0.8 | 20.664360 |
| role_pool_MLB | 4.002453987730061 | 19.446151 |
| scout_listed_0 | 1.0 | 1.285788 |
| scout_rank_score_1 | 0.0 | -0.000654 |

General distinct-player profile: [{'row_id': 33062, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 48}]. Rank-specific profile: [{'row_id': 33062, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 86}]. Actual mature training support: [{'row_id': 33062, 'horizon': 1, 'player_id': 609280, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.7932473892702949, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 556, 'current_players': 365, 'regular_players': 344, 'joint_players': 114, 'quality_joint_players': 156, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Andujar had 606 MLB PA, 27 HR and only 97 K in 2018 after a short 2017 debut; rank 65 adds weaker historical confidence. New PA 614 versus old 568 is the largest false-high workload, actual 49. MLB exposure/work/quality dominate both paths. The origin record alone does not establish a dated injury or loss of job, so the observed collapse is not retrospectively inserted as a forecast input. Contribution worsens 2.671 to 2.885 versus -.671. Benintendi, Moncada, Mazara and Bellinger are ordinary young established-player comparators with 615, 559, 469 and 661 PA. The conditional forecast is baseball-plausible given the provided record, but uncertainty/health/job information remains missing; this case cannot establish preventability from rankings.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Andrew Benintendi | 23.0 | 661 | 0 | 0.0 | 0.0 | 641.09 | 616.72 | 615 | 2.39410 |
| Yoán Moncada | 23.0 | 650 | 0 | 0.0 | 0.0 | 513.69 | 473.77 | 559 | 4.57716 |
| Nomar Mazara | 23.0 | 536 | 20 | 0.0 | 0.0 | 529.05 | 529.26 | 469 | 1.77004 |
| Cody Bellinger | 22.0 | 632 | 0 | 0.0 | 0.0 | 533.53 | 531.50 | 661 | 6.76875 |

## Wenceel Pérez 2024 to 2025

Player 672761, row 55592, fold 3; pa ordinary. Age 24.0; Current MLB; career observed MLB PA 425.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | AA | 171 | 39 | 5 | 23 | 14 |
| 2022 | Aplus | 236 | 55 | 9 | 38 | 27 |
| 2023 | A | 22 | 5 | 0 | 5 | 1 |
| 2023 | AA | 343 | 76 | 6 | 52 | 35 |
| 2023 | AAA | 160 | 35 | 3 | 29 | 27 |
| 2024 | AAA | 63 | 15 | 2 | 15 | 8 |
| 2024 | MLB | 425 | 112 | 9 | 92 | 32 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 381.6683 | -0.47116 | 0.892680 |
| scout | 383.2828 | -0.47116 | 0.896457 |
| retired_safe_ridge | 388.6567 | -0.42684 | 0.937738 |
| Actual | 383 | 0.3412356590537692 | 1.411256 |

Raw candidate PA 383.282818; bounded and availability-adjusted PA 383.282818. Contribution = 383.282818 × (-0.471162/600 + 0.00312416). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.305820 plus the complete stored terms reconstructs raw PA 381.668327.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 425.17496912309593 | 301.842061 |
| role_mlb_0 | 3.8114754098360657 | -34.453324 |
| on_40man | 1.0 | 25.703696 |
| age_centered | -0.6 | 21.661162 |
| quality_0 | -0.14191357438478308 | -13.893743 |
| regular_window_scaled | 0.3333333333333333 | 11.906819 |
| role_pool_AAA | 4.3584905660377355 | 10.541839 |
| pooled_MLB_K | 0.21904761904761905 | 8.808511 |

### Ranking candidate fitted path

Reference 39.313177 plus the complete stored terms reconstructs raw PA 383.282818.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 425.17496912309593 | 300.715716 |
| role_mlb_0 | 3.8114754098360657 | -34.670426 |
| on_40man | 1.0 | 25.971798 |
| age_centered | -0.6 | 19.116580 |
| quality_0 | -0.14191357438478308 | -13.524596 |
| regular_window_scaled | 0.3333333333333333 | 13.500842 |
| role_pool_AAA | 4.3584905660377355 | 11.922715 |
| pooled_MLB_K | 0.21904761904761905 | 10.449953 |
| scout_rank_score_0 | 0.0 | -0.409006 |
| scout_listed_0 | 0.0 | -0.068781 |
| scout_rank_score_2 | 0.0 | -0.024351 |
| scout_rank_score_1 | 0.0 | 0.016359 |

General distinct-player profile: [{'row_id': 55592, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 79}]. Rank-specific profile: [{'row_id': 55592, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 555}]. Actual mature training support: [{'row_id': 55592, 'horizon': 1, 'player_id': 672761, 'origin_year': 2024, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 24.0, 'quality_0': -0.14191357438478308, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 1019, 'current_players': 546, 'regular_players': 555, 'joint_players': 24, 'quality_joint_players': 49, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Perez had 425 MLB PA and 63 AAA PA after several upper-minor seasons. Unlisted status does not erase his established MLB evidence. Work/role/roster paths dominate, and the rank candidate moves PA only 381.67 to 383.28 versus 383 actual, the mechanically selected ordinary PA case. Contribution remains .896 versus 1.411 because fixed batting rate -.471 misses actual +.341; accurate PA is not accurate talent. The 555-person coarse profile is populated. Gorman, Wells, Kelenic and Perdomo produce 402, 448, 65 and 720 PA despite comparable origin workload, underscoring that one near-exact point forecast is diagnostic, not proof of calibrated individual uncertainty.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nolan Gorman | 24.0 | 402 | 98 | 0.0 | 0.0 | 334.13 | 322.36 | 402 | 0.56052 |
| Austin Wells | 24.0 | 414 | 0 | 0.0 | 0.0 | 410.87 | 405.35 | 448 | 1.01665 |
| Jarred Kelenic | 24.0 | 449 | 0 | 0.0 | 0.0 | 366.33 | 367.67 | 65 | -0.20396 |
| Geraldo Perdomo | 24.0 | 388 | 27 | 0.0 | 0.0 | 454.15 | 457.14 | 720 | 5.51700 |

## Julio Rodríguez 2021 to 2022

Player 677594, row 44122, fold 1; value largest gain. Age 20.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | A | 295 | 67 | 10 | 66 | 19 |
| 2019 | Aplus | 72 | 17 | 2 | 10 | 5 |
| 2021 | AA | 206 | 46 | 7 | 37 | 28 |
| 2021 | Aplus | 134 | 28 | 6 | 29 | 14 |

Source ranks: [{'season': 2020, 'player_id': 677594, 'rank': 18, 'list_capacity': 99, 'list_complete': False, 'player_name': 'Julio Rodríguez'}, {'season': 2021, 'player_id': 677594, 'rank': 5, 'list_capacity': 99, 'list_complete': False, 'player_name': 'Julio Rodríguez'}].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 99.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.96, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 99.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.83, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 103.1077 | 0.80651 | 0.461839 |
| scout | 284.2261 | 0.80651 | 1.273103 |
| retired_safe_ridge | 91.8617 | 0.76276 | 0.404767 |
| Actual | 560 | 2.683148599795411 | 4.257617 |

Raw candidate PA 284.226078; bounded and availability-adjusted PA 284.226078. Contribution = 284.226078 × (0.806514/600 + 0.00313500). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.485376 plus the complete stored terms reconstructs raw PA 103.107728.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| on_40man | 1.0 | 85.029535 |
| work_0 | 0.0 | -23.135175 |
| role_pool_AA | 4.392857142857143 | 15.926892 |
| pooled_Aplus_2B | 0.059884559884559894 | 9.919610 |
| MLB_0_pa | 0.0 | -9.854880 |
| pooled_MLB_pa | 0.0 | -7.352903 |
| pooled_Aplus_BABIP | 0.36856875584658555 | 7.347975 |
| age_centered | -1.4 | 5.908255 |

### Ranking candidate fitted path

Reference 39.492474 plus the complete stored terms reconstructs raw PA 284.226078.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| scout_rank_score_0 | 0.96 | 189.874192 |
| on_40man | 1.0 | 87.491464 |
| work_0 | 0.0 | -22.888988 |
| MLB_0_pa | 0.0 | -11.102416 |
| role_pool_AA | 4.392857142857143 | 10.187652 |
| pooled_Aplus_2B | 0.059884559884559894 | 9.772061 |
| pooled_MLB_pa | 0.0 | -8.206719 |
| role_minor_0 | 4.523809523809524 | 7.644529 |
| scout_rank_score_1 | 0.83 | 2.459223 |
| scout_rank_score_2 | 0.0 | -0.002690 |

General distinct-player profile: [{'row_id': 44122, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 0, 'profile_players': 549}]. Rank-specific profile: [{'row_id': 44122, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 16}]. Actual mature training support: [{'row_id': 44122, 'horizon': 1, 'player_id': 677594, 'origin_year': 2021, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 9307, 'current_players': 9836, 'regular_players': 9920, 'joint_players': 7588, 'quality_joint_players': 9389, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Rodriguez had 340 Aplus/AA PA in 2021, 13 HR, 66 K and 42 BB; canceled 2020 MiLB is missing production, not failure. Verified positive ranks 18 in 2020 and 5 in 2021 remain usable even though those lists are partial. The current rank path accounts for +189.87 PA within the fit. Expected PA rises 103 to 284 versus 560, and contribution .462 to 1.273 versus 4.258, the largest value gain, but the unchanged rate .807 still misses actual 2.683. This is meaningful readiness evidence and continuing superstar underestimation. Only 16 distinct people match his rank profile. Abrams, Greene, Torkelson and Casas have 302, 418, 404 and 95 PA and a wide batting range; prospect reputation signals opportunity more reliably than an assured elite outcome.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CJ Abrams | 20.0 | 0 | 183 | 1.0 | 0.93 | 45.00 | 234.88 | 302 | -0.10310 |
| Riley Greene | 20.0 | 0 | 558 | 1.0 | 0.8 | 204.98 | 269.78 | 418 | 1.15395 |
| Spencer Torkelson | 21.0 | 0 | 530 | 1.0 | 0.98 | 125.36 | 270.13 | 404 | 0.07614 |
| Triston Casas | 21.0 | 0 | 371 | 1.0 | 0.57 | 95.27 | 137.20 | 95 | 0.57970 |

## Pete Alonso 2018 to 2019

Player 624413, row 33263, fold 1; value largest harm. Age 23.0; Upper minors; career observed MLB PA 0.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 30 | 5 | 22 | 11 |
| 2017 | AA | 47 | 11 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 82 | 16 | 64 | 24 |
| 2018 | AA | 273 | 65 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 67 | 21 | 78 | 33 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 215.2303 | 0.25988 | 0.755868 |
| scout | 154.9817 | 0.25988 | 0.544281 |
| retired_safe_ridge | 157.8898 | 0.25988 | 0.554494 |
| Actual | 693 | 3.2827570240246495 | 5.908536 |

Raw candidate PA 154.981682; bounded and availability-adjusted PA 154.981682. Contribution = 154.981682 × (0.259881/600 + 0.00307877). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.743210 plus the complete stored terms reconstructs raw PA 215.230347.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| role_pool_AAA | 4.428571428571429 | 72.333487 |
| pooled_AAA_HR | 0.059850374064837904 | 31.013366 |
| draft_known | 1.0 | 26.754360 |
| age_centered | -0.8 | 18.870140 |
| MLB_0_pa | 0.0 | -18.611716 |
| pooled_Aplus_2B | 0.062101910828025485 | 15.107572 |
| role_pool_AA | 4.183770883054893 | 13.060455 |
| pooled_AA_HR | 0.047735021919142716 | 10.113093 |

### Ranking candidate fitted path

Reference 39.748896 plus the complete stored terms reconstructs raw PA 154.981682.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| role_pool_AAA | 4.428571428571429 | 49.194312 |
| draft_known | 1.0 | 30.036065 |
| pooled_AAA_HR | 0.059850374064837904 | 26.761763 |
| MLB_0_pa | 0.0 | -18.000151 |
| age_centered | -0.8 | 15.419333 |
| role_pool_AA | 4.183770883054893 | 9.842056 |
| pooled_AA_pa | 310.6 | 6.586384 |
| on_40man | 0.0 | -6.225943 |
| scout_rank_score_0 | 0.0 | -1.688363 |
| scout_rank_score_2 | 0.0 | 0.072499 |
| scout_rank_score_1 | 0.0 | 0.014231 |

General distinct-player profile: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1035}]. Rank-specific profile: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1417}]. Actual mature training support: [{'row_id': 33263, 'horizon': 1, 'player_id': 624413, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 7455, 'current_players': 7925, 'regular_players': 8044, 'joint_players': 2929, 'quality_joint_players': 7535, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Alonso had 574 AA/AAA PA with 36 HR, 128 K and 73 BB, strong end-of-year performance not represented in the stale preseason top100 list. The new fit lowers PA 215 to 155 versus 693; contribution falls .756 to .544 versus 5.909, the largest value deterioration. AAA role and HR remain positive paths but their accounting decreases. This is not absence of production evidence: it is a lost rising-prospect representation and a fixed-rate miss (.260 versus 3.283 actual). Edman, Thaiss, Rooker and Lopez provide 349, 164, 0 and 402 next-year PA. The 1,417-person unlisted profile is broad, not assurance that this power/advancement combination is adequately represented. A draft-only missing-rank fix would not address Alonso; dated within-season ranking changes or a production-preserving model are distinct needs.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tommy Edman | 23.0 | 0 | 574 | 0.0 | 0.0 | 64.03 | 48.62 | 349 | 2.23511 |
| Matt Thaiss | 23.0 | 0 | 576 | 0.0 | 0.0 | 125.74 | 93.61 | 164 | 0.30654 |
| Brent Rooker | 23.0 | 0 | 568 | 0.0 | 0.0 | 24.92 | 27.43 | 0 | 0.00000 |
| Nicky Lopez | 23.0 | 0 | 581 | 0.0 | 0.0 | 88.17 | 63.96 | 402 | -0.83941 |

## Yordan Alvarez 2024 to 2025

Player 670541, row 55521, fold 2; value false high. Age 27.0; Current MLB; career observed MLB PA 2668.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 577.4905 | 3.70970 | 5.374704 |
| scout | 579.4166 | 3.70970 | 5.392630 |
| retired_safe_ridge | 601.3075 | 3.76103 | 5.647804 |
| Actual | 199 | 0.919648372891386 | 0.925104 |

Raw candidate PA 579.416612; bounded and availability-adjusted PA 579.416612. Contribution = 579.416612 × (3.709704/600 + 0.00312416). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.289435 plus the complete stored terms reconstructs raw PA 577.490453.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 635.2614244545081 | 322.222292 |
| role_mlb_0 | 4.2993630573248405 | 57.464999 |
| quality_0 | 1.415653196303136 | 52.228185 |
| pooled_mlb_quality | 2.457088938891907 | 23.983220 |
| role_pool_MLB | 4.278250303766707 | 18.921383 |
| quality_1 | 1.3830873087907403 | 15.954412 |
| regular_window_scaled | 1.0 | 13.701698 |
| MLB_0_pa | 635.0 | 12.903590 |

### Ranking candidate fitted path

Reference 39.295575 plus the complete stored terms reconstructs raw PA 579.416612.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| work_0 | 635.2614244545081 | 320.249534 |
| role_mlb_0 | 4.2993630573248405 | 58.120386 |
| quality_0 | 1.415653196303136 | 49.371579 |
| pooled_mlb_quality | 2.457088938891907 | 24.638936 |
| role_pool_MLB | 4.278250303766707 | 16.703717 |
| regular_window_scaled | 1.0 | 15.818298 |
| quality_1 | 1.3830873087907403 | 14.830341 |
| pooled_MLB_HR | 0.05788613456823753 | 14.628676 |
| scout_list_capacity_2 | 100.0 | 2.965245 |
| scout_rank_score_0 | 0.0 | -0.241132 |
| scout_rank_score_1 | 0.0 | -0.022617 |
| scout_listed_1 | 0.0 | -0.018149 |
| scout_rank_score_2 | 0.0 | 0.001703 |

General distinct-player profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 173}]. Rank-specific profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'rank_profile_players': 1078}]. Actual mature training support: [{'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 903, 'current_players': 538, 'regular_players': 310, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Alvarez had 635 MLB PA, 35 HR, 95 K and 53 BB in 2024, following 561 and 496 PA. Both fits sensibly recognize an elite established hitter on the supplied production record. New expected PA 579 versus old 577 is nearly unchanged, but actual PA is 199 and contribution .925 versus predicted 5.393, the largest value false high. The known production supports the rate, not certainty about future health; no later injury cause is invented from this table. Devers, India, Donovan and Bohm have 729, 567, 515 and 504 actual PA. Rankings neither caused nor repair this large exposure collapse. Future availability distributions and genuinely dated health evidence remain relevant, without automatically docking every elite hitter.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rafael Devers | 27.0 | 601 | 0 | 0.0 | 0.0 | 566.99 | 566.85 | 729 | 5.23429 |
| Jonathan India | 27.0 | 637 | 0 | 0.0 | 0.0 | 545.44 | 549.55 | 567 | 1.28649 |
| Brendan Donovan | 27.0 | 652 | 0 | 0.0 | 0.0 | 570.90 | 563.34 | 515 | 2.59344 |
| Alec Bohm | 27.0 | 606 | 4 | 0.0 | 0.0 | 590.93 | 589.28 | 504 | 2.05959 |

## Adeiny Hechavarría 2016 to 2017

Player 588751, row 23878, fold 1; value ordinary. Age 27.0; Current MLB; career observed MLB PA 2335.

| Season | Level | PA | Source games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | Aplus | 8 | 2 | 0 | 1 | 0 |
| 2014 | MLB | 574 | 146 | 1 | 86 | 21 |
| 2015 | MLB | 499 | 130 | 5 | 78 | 19 |
| 2016 | MLB | 547 | 155 | 3 | 73 | 26 |

Source ranks: [].

Actual twelve added inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}.

| Forecast | Expected MLB PA | Batting wins per 600 PA | Batting plus replacement wins |
|---|---:|---:|---:|
| retired_games | 388.3216 | -1.35528 | 0.322030 |
| scout | 391.8653 | -1.35528 | 0.324968 |
| retired_safe_ridge | 369.1054 | -1.35528 | 0.306094 |
| Actual | 348 | -1.2852206812068887 | 0.325081 |

Raw candidate PA 391.865348; bounded and availability-adjusted PA 391.865348. Contribution = 391.865348 × (-1.355283/600 + 0.00308809). The separate working assembly uses its own different fixed rate; it is not silently mixed into the rank comparison.

### Count and games control fitted path

Reference 39.639329 plus the complete stored terms reconstructs raw PA 388.321569.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 547.0 | 247.362343 |
| role_mlb_0 | 3.5575757575757576 | -59.056102 |
| quality_0 | -0.978461962097713 | -41.453331 |
| work_0 | 547.4505766062603 | 39.407056 |
| on_40man | 1.0 | 34.066810 |
| MLB_1_pa | 499.0 | 32.607477 |
| regular_window_scaled | 1.0 | 32.219218 |
| games_mlb_0 | 155.0 | 23.183974 |

### Ranking candidate fitted path

Reference 39.647587 plus the complete stored terms reconstructs raw PA 391.865348.

| Input | Encoded value | Path accounting in PA |
|---|---:|---:|
| MLB_0_pa | 547.0 | 247.385250 |
| role_mlb_0 | 3.5575757575757576 | -61.334977 |
| quality_0 | -0.978461962097713 | -38.123127 |
| on_40man | 1.0 | 36.887287 |
| work_0 | 547.4505766062603 | 36.844001 |
| MLB_1_pa | 499.0 | 33.808385 |
| regular_window_scaled | 1.0 | 33.645621 |
| games_mlb_0 | 155.0 | 20.189161 |
| scout_list_capacity_0 | 100.0 | 0.465771 |
| scout_rank_score_0 | 0.0 | -0.386450 |
| scout_rank_score_2 | 0.0 | 0.023165 |

General distinct-player profile: [{'row_id': 23878, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 118}]. Rank-specific profile: [{'row_id': 23878, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'rank_profile_players': 553}]. Actual mature training support: [{'row_id': 23878, 'horizon': 1, 'player_id': 588751, 'origin_year': 2016, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': -0.978461962097713, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 317, 'regular_players': 179, 'joint_players': 125, 'quality_joint_players': 242, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Hechavarria had three substantial MLB seasons, low HR/BB totals and 547 PA in 2016. The no-rank candidate relies on MLB workload, role and below-average quality and moves expected PA 388 to 392 versus 348. The fixed batting rate -1.355 is close to actual -1.285; contribution .32497 almost exactly matches .32508 only because somewhat excessive PA offsets a slightly worse batting rate. This ordinary value-selected case is not two accurate component forecasts or a scouting mechanism. Gonzalez, Pillar, Norris and Dickerson span 198 to 632 next-year PA and markedly different contribution, showing uncertainty even among established similar-age hitters. Rank-profile support is 553 people; source ranks add no specific new prospect information here.

| Origin selected peer | Age | MLB PA | Minor PA | Listed | Rank score | Control PA | Candidate PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Marwin Gonzalez | 27.0 | 518 | 0 | 0.0 | 0.0 | 352.44 | 351.50 | 515 | 4.14189 |
| Kevin Pillar | 27.0 | 584 | 9 | 0.0 | 0.0 | 440.04 | 438.34 | 632 | 1.06308 |
| Derek Norris | 27.0 | 458 | 0 | 0.0 | 0.0 | 299.59 | 311.14 | 198 | -0.15537 |
| Corey Dickerson | 27.0 | 548 | 0 | 0.0 | 0.0 | 417.83 | 423.47 | 629 | 2.97277 |

## Cohort findings and decision

The broad incremental games-control intervals include no gain, while listed and top20 intervals favor rankings. Public workload MAE is 110.553 versus Steamer 92.399 and still fails the predeclared 15 percent tolerance. Upper-minor individual error improves but total expected PA falls to 95,576 versus 102,951 actual, farther below the control. Lower-minor expected PA is 10,509 versus 6,072 actual; the small pooled score does not establish calibration. Origins 2017 and 2024 worsen versus games, while 2021 improves on PA but contribution totals remain high.

Retain ranked-prospect readiness evidence as qualified research, not the unmodified whole-population forecast. Do not replace working V33b plus retirement, the frozen 2026 forecast or its deployed explorer. Stale absence for new draftees and fast movers, elite conditional-rate compression, sparse ranked training profiles and current-MLB availability remain unresolved. A justified next bounded repair is to prevent a stale absent ranking from overwriting the count-based fallback; test that explicit source-applicability policy as development evidence, not a new algorithm sweep or independent confirmation. All fifteen player reviews are complete before this decision.
