# Count-link hitter model: fourteen actual player reviews

Next-calendar-year MLB PA and batting-plus-replacement contribution, not full WAR. Only the PA loss/link changes; batting estimates and availability policies are fixed. Cases include fixed diagnostics and largest gains, harms, false highs/lows and ordinary errors. Peers are selected using origin information, not later success.

## Nick Kurtz 2024 to 2025

Player 701762, row 57052; selected as fixed diagnostic; age 21.0, Upper minors.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 29.9431 | -0.13556 | 0.086782 |
| poisson | 5.9282 | -0.13556 | 0.017181 |
| Actual | 489 | 5.150009420178844 | 5.720989 |

Contribution arithmetic: expected PA × (-0.135562/600 + 0.00312416). Candidate raw mean 5.928214; raw log prediction 1.779723. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 26.886700 |
| work_0 | 0.0 | -22.958102 |
| on_40man | 0.0 | -6.293909 |
| pooled_AA_BABIP | 0.3090909090909091 | 2.118989 |
| quality_0 | 0.0 | -1.687118 |
| role_pool_AA | 3.6666666666666665 | -1.463170 |
| pooled_MLB_BABIP | 0.3 | 1.427221 |
| pooled_AA_BB | 0.08695652173913043 | 1.418949 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 1.002473 |
| draft_rank_low_exposure | 0.5450763363518277 | 0.478496 |
| pooled_DSL_HR | 0.03 | 0.300007 |
| games_pool_MLB | 0.0 | -0.288096 |
| work_0 | 0.0 | -0.230191 |
| pooled_AA_pa | 15.0 | -0.128692 |
| role_minor_0 | 4.090909090909091 | 0.117414 |
| role_pool_AA | 3.6666666666666665 | -0.107139 |

Distinct-player profile support: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1744}]. Actual mature-fold chronology support: [{'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11239, 'current_players': 11751, 'regular_players': 11845, 'joint_players': 9411, 'quality_joint_players': 11314, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2024, 'fit_fold': 2}].

Kurtz has 35 A PA in seven games with four HR, then 15 AA PA in five games. The same draft pick-four evidence and batting head are retained. The count-link candidate reduces expected PA from 29.94 to 5.93 against 489 actual, worsening the fast-entry miss. His absent AAA role of four PA/game is a default prior, not an observed starting job. Pooled DSL HR .03 is likewise a stabilization prior, not Kurtz playing DSL. Positive draft log-path effects do not overcome the low-exposure background. The 1,744-person support count is a broad age/stage/draft group, not 1,744 comparable elite college hitters. Low-exposure Montgomery, Hartl, Soto and Quero all fail to arrive in the following year; those origin-selected peers show uncertainty but do not certify Kurtz's readiness comparison.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Benny Montgomery | 21.0 | 0 | 48 | 40.93 | 34.19 | 0 | 0.00000 |
| Ben Hartl | 21.0 | 0 | 57 | 0.00 | 0.57 | 0 | 0.00000 |
| Wally Soto | 21.0 | 0 | 85 | 8.74 | 0.69 | 0 | 0.00000 |
| Jeferson Quero | 21.0 | 0 | 1 | 76.59 | 41.81 | 0 | 0.00000 |

## Anthony Volpe 2022 to 2023

Player 683011, row 48516; selected as fixed diagnostic; age 21.0, Upper minors.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 257 | 54 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 55 | 15 | 58 | 26 |
| 2022 | AA | 497 | 110 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 22 | 3 | 30 | 8 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 166.1382 | -0.14770 | 0.479277 |
| poisson | 159.3505 | -0.14770 | 0.459696 |
| Actual | 601 | -1.3447727729230707 | 0.513728 |

Contribution arithmetic: expected PA × (-0.147697/600 + 0.00313097). Candidate raw mean 159.350534; raw log prediction 5.071106. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| role_pool_AAA | 4.34375 | 59.842622 |
| age_centered | -1.2 | 38.942856 |
| role_pool_AA | 4.475 | 28.539544 |
| work_0 | 0.0 | -23.047864 |
| Aplus_1_pa | 256.0 | 10.573611 |
| pooled_A_3B | 0.014725130890052354 | 8.985924 |
| pooled_AA_K | 0.18592964824120603 | 7.545442 |
| on_40man | 0.0 | -6.124249 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| role_pool_AA | 4.475 | 1.381608 |
| role_pool_AAA | 4.34375 | 0.866275 |
| pooled_AA_pa | 497.0 | 0.713261 |
| age_centered | -1.2 | 0.524259 |
| draft_rank | 0.5525271637458875 | 0.340669 |
| games_pool_MLB | 0.0 | -0.238362 |
| pooled_DSL_pa | 0.0 | 0.229641 |
| role_minor_0 | 4.47887323943662 | 0.215851 |

Distinct-player profile support: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1502}]. Actual mature-fold chronology support: [{'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10086, 'current_players': 10584, 'regular_players': 10685, 'joint_players': 8356, 'quality_joint_players': 10163, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2022, 'fit_fold': 4}].

Volpe's source contains 497 AA PA in 110 games and 99 AAA PA in 22 games, following a strong A/A-plus season. Both models use the real roughly 4.4 PA/game involvement, with positive AA/AAA role accounting. The candidate changes 166.14 to 159.35 expected PA against 601 actual. Contribution falls .4793 to .4597 against .5137 actual. That relatively small value miss hides an enormous workload miss because the fixed batting estimate is below average. Rocchio and Tena receive substantially higher candidate PA but actually have 86 and 34, while Pages and Valera do not arrive. Neither this change nor the broad 1,502-person support group solves prospect starting-job allocation.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Brayan Rocchio | 21.0 | 0 | 584 | 169.51 | 304.40 | 86 | -0.11915 |
| José Tena | 21.0 | 0 | 573 | 116.38 | 318.89 | 34 | -0.04262 |
| Andy Pages | 21.0 | 0 | 571 | 97.63 | 146.71 | 0 | 0.00000 |
| George Valera | 21.0 | 0 | 566 | 152.04 | 226.79 | 0 | 0.00000 |

## Aaron Judge 2016 to 2017

Player 592450, row 23934; selected as fixed diagnostic, value false low; age 24.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 150.2046 | -0.05720 | 0.449525 |
| poisson | 233.6837 | -0.05720 | 0.699357 |
| Actual | 678 | 5.329875619792154 | 8.108407 |

Contribution arithmetic: expected PA × (-0.057204/600 + 0.00308809). Candidate raw mean 233.683683; raw log prediction 5.453968. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| on_40man | 1.0 | 75.498701 |
| role_pool_AAA | 4.334650856389986 | 38.928232 |
| MLB_0_pa | 95.0 | 24.512022 |
| pooled_MLB_K | 0.3333333333333333 | -12.963409 |
| pooled_AAA_2B | 0.04317548746518106 | -12.710632 |
| age_centered | -0.6 | 12.462715 |
| pooled_Aplus_K | 0.244280442804428 | 9.264230 |
| role_pool_A | 4.220408163265306 | 7.668758 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| on_40man | 1.0 | 1.056622 |
| MLB_0_pa | 95.0 | 1.044086 |
| games_pool_MLB | 27.0 | 0.975291 |
| games_pool_DSL | 0.0 | 0.356800 |
| pooled_A_3B | 0.006371814092953524 | 0.323527 |
| pooled_MLB_pa | 95.0 | 0.302075 |
| role_minor_0 | 4.368932038834951 | 0.227544 |
| work_0 | 95.07825370675452 | 0.218070 |

Distinct-player profile support: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Actual mature-fold chronology support: [{'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 181, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2016, 'fit_fold': 3}].

Judge's 410 AAA PA in 93 games and 19 HR precede 95 MLB PA in 27 games with four HR and 42 K. Candidate PA rises 150.21 to 233.68 against 678 actual. This is a genuine workload improvement, driven in log-space by MLB appearances, MLB games and roster membership, but still far short of his full-season job. The unchanged -0.057 batting-wins/600 estimate means contribution only rises .450 to .699 against 8.108: the breakout talent is not predicted. Similar origin brief debuts Moya, Austin and Cowart receive zero, 46 and 117 actual PA, whereas Difo gets 365. A large future star does not justify raising every briefly exposed hitter to a full-season mean. There are 141 broadly matching training people, not a tailored future-superstar sample.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steven Moya | 24.0 | 100 | 426 | 203.47 | 193.65 | 0 | 0.00000 |
| Tyler Austin | 24.0 | 90 | 444 | 144.43 | 152.93 | 46 | 0.05556 |
| Kaleb Cowart | 24.0 | 87 | 458 | 141.72 | 136.94 | 117 | 0.12269 |
| Wilmer Difo | 24.0 | 66 | 456 | 217.86 | 266.59 | 365 | 0.11034 |

## Aaron Judge 2024 to 2025

Player 592450, row 54849; selected as fixed diagnostic; age 32.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 696 | 157 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 106 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 158 | 58 | 171 | 113 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 547.3890 | 4.55334 | 5.864212 |
| poisson | 527.8527 | 4.55334 | 5.654917 |
| Actual | 679 | 6.287431083532908 | 9.231050 |

Contribution arithmetic: expected PA × (4.553340/600 + 0.00312416). Candidate raw mean 527.852664; raw log prediction 6.268817. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 704.2898312062578 | 319.670118 |
| quality_0 | 2.794424993741549 | 57.074454 |
| role_mlb_0 | 4.428571428571429 | 55.279547 |
| games_mlb_2 | 157.0 | 24.645577 |
| pooled_mlb_quality | 3.6485663788613953 | 24.507835 |
| age_centered | 1.0 | -17.616136 |
| pooled_MLB_K | 0.25377833753148615 | -15.612146 |
| role_pool_MLB | 4.403458213256484 | 12.923628 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| work_0 | 704.2898312062578 | 1.649938 |
| pooled_MLB_pa | 1488.0 | 1.101754 |
| MLB_0_pa | 704.0 | 0.756617 |
| on_40man | 1.0 | 0.456937 |
| games_pool_MLB | 337.0 | 0.431997 |
| pooled_DSL_HR | 0.03 | 0.280101 |
| role_mlb_0 | 4.428571428571429 | 0.200711 |
| role_minor_0 | 4.0 | 0.120182 |

Distinct-player profile support: [{'row_id': 54849, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 87}]. Actual mature-fold chronology support: [{'row_id': 54849, 'horizon': 1, 'player_id': 592450, 'origin_year': 2024, 'elapsed': 8, 'current_state': 3, 'regular_window': 3, 'age': 32.0, 'quality_0': 2.794424993741549, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 407, 'current_players': 546, 'regular_players': 300, 'joint_players': 294, 'quality_joint_players': 80, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': True, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': True, 'profile_check_pass': False, 'fit_year': 2024, 'fit_fold': 3}].

Judge's source has 696/458/704 MLB PA and 62/37/58 HR over the three seasons. His real recent usage is roughly 4.43 PA/game. The fixed strong batting estimate of 4.553 wins/600 is preserved, unlike the joint forest's talent compression. Nevertheless expected PA falls 547.39 to 527.85 against 679, reducing contribution 5.864 to 5.655 against 9.231. The new loss worsens an already compressed elite forecast rather than fixing it. Ozuna, Schwarber, Harper and Profar have mixed subsequent workload, so the case alone is not a universal 700-PA rule. The 87-person broad support group supports a seasoned regular comparison, not exact Judge-level upside.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Marcell Ozuna | 33.0 | 688 | 0 | 544.03 | 514.60 | 592 | 2.91697 |
| Kyle Schwarber | 31.0 | 692 | 0 | 585.90 | 563.40 | 724 | 6.83256 |
| Bryce Harper | 31.0 | 631 | 0 | 527.02 | 575.45 | 580 | 4.01831 |
| Jurickson Profar | 31.0 | 668 | 0 | 506.43 | 475.11 | 371 | 2.24270 |

## Brent Rooker 2022 to 2023

Player 667670, row 47398; selected as fixed diagnostic; age 27.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 21 | 7 | 1 | 5 | 0 |
| 2021 | AAA | 267 | 62 | 20 | 80 | 36 |
| 2021 | MLB | 213 | 58 | 9 | 70 | 15 |
| 2022 | AAA | 365 | 81 | 28 | 103 | 44 |
| 2022 | MLB | 36 | 16 | 0 | 11 | 3 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 164.4636 | -0.37321 | 0.412633 |
| poisson | 139.9202 | -0.37321 | 0.351054 |
| Actual | 526 | 1.5435493625116004 | 2.981714 |

Contribution arithmetic: expected PA × (-0.373208/600 + 0.00313097). Candidate raw mean 139.920173; raw log prediction 4.941072. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| on_40man | 1.0 | 85.342605 |
| role_pool_AAA | 4.399715504978663 | 48.552768 |
| pooled_AAA_HR | 0.06926024167403477 | 27.453673 |
| age_centered | 0.0 | -21.363681 |
| draft_rank | 0.5322465877685258 | 14.092101 |
| pooled_MLB_K | 0.29153605015673983 | -13.779018 |
| MLB_0_pa | 36.0 | 12.451330 |
| work_0 | 36.0 | -9.604670 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| games_pool_MLB | 73.74000000000001 | 0.981094 |
| on_40man | 1.0 | 0.964393 |
| work_0 | 36.0 | 0.560941 |
| pooled_MLB_pa | 219.0 | 0.535885 |
| games_mlb_0 | 16.0 | 0.354177 |
| pooled_DSL_pa | 0.0 | 0.171925 |
| role_minor_0 | 4.450549450549451 | 0.170558 |
| MLB_0_pa | 36.0 | 0.140219 |

Distinct-player profile support: [{'row_id': 47398, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 481}]. Actual mature-fold chronology support: [{'row_id': 47398, 'horizon': 1, 'player_id': 667670, 'origin_year': 2022, 'elapsed': 2, 'current_state': 1, 'regular_window': 0, 'age': 27.0, 'quality_0': -0.17384904561086884, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 800, 'current_players': 1174, 'regular_players': 10740, 'joint_players': 236, 'quality_joint_players': 524, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2022, 'fit_fold': 0}].

Rooker has 365 AAA PA in 81 games with 28 HR, but just 36 MLB PA in 16 games. Candidate PA falls 164.46 to 139.92 against 526, and contribution .413 to .351 against 2.982. Both forecast availability and the unchanged negative batting rate remain too low. His actual AAA involvement near 4.4 PA/game and HR evidence enter the source correctly; changing the count loss does not give them a new competition translation or forecast his later starting job. Hernandez, Aguilar and Martin do not play in MLB next year, while Batten gets 139 PA. The observed Rooker breakthrough is important, but unsuccessful older upper-minor peers remain part of the expectation.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Elier Hernandez | 27.0 | 35 | 351 | 15.20 | 19.74 | 0 | 0.00000 |
| Ryan Aguilar | 27.0 | 26 | 364 | 0.00 | 16.27 | 0 | 0.00000 |
| Richie Martin Jr. | 27.0 | 33 | 334 | 60.60 | 48.26 | 0 | 0.00000 |
| Matthew Batten | 27.0 | 22 | 378 | 77.03 | 89.32 | 139 | 0.45753 |

## Albert Pujols 2021 to 2022

Player 405395, row 42072; selected as fixed diagnostic; age 41.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | MLB | 545 | 131 | 23 | 68 | 42 |
| 2020 | MLB | 163 | 39 | 6 | 25 | 8 |
| 2021 | MLB | 296 | 109 | 17 | 45 | 11 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 52.7555 | -0.93123 | 0.083510 |
| poisson | 84.1590 | -0.93123 | 0.133220 |
| Actual | 351 | 3.4063842632657733 | 3.091707 |

Contribution arithmetic: expected PA × (-0.931230/600 + 0.00313500). Candidate raw mean 84.158970; raw log prediction 4.432708. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 296.12186084808565 | 204.629974 |
| on_40man | 0.0 | -101.404218 |
| role_mlb_0 | 2.823529411764706 | -63.373410 |
| age_centered | 2.8 | -30.467767 |
| regular_window_scaled | 0.6666666666666666 | 21.042623 |
| MLB_0_pa | 296.0 | -11.164290 |
| pooled_MLB_3B | 0.0005858917272088118 | -11.122953 |
| pooled_MLB_pa | 753.4 | 10.094140 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| work_0 | 296.12186084808565 | 1.895420 |
| games_pool_MLB | 271.84000000000003 | 1.075618 |
| pooled_MLB_pa | 753.4 | 0.921021 |
| on_40man | 0.0 | -0.633249 |
| games_mlb_1 | 105.30000000000001 | 0.302287 |
| games_pool_DSL | 0.0 | 0.276082 |
| role_mlb_0 | 2.823529411764706 | -0.237535 |
| age_centered | 2.8 | -0.218507 |

Distinct-player profile support: [{'row_id': 42072, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 8.0, 'current_work_band': 'partial', 'draft_known': 0, 'profile_players': 5}]. Actual mature-fold chronology support: [{'row_id': 42072, 'horizon': 1, 'player_id': 405395, 'origin_year': 2021, 'elapsed': 20, 'current_state': 2, 'regular_window': 2, 'age': 41.0, 'quality_0': -0.12593132806633103, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 4, 'current_players': 570, 'regular_players': 372, 'joint_players': 286, 'quality_joint_players': 425, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'fit_year': 2021, 'fit_fold': 1}].

Pujols has 296 MLB PA in 109 games and 17 HR in 2021, with 545 PA in 2019 and 163 in shortened 2020. No eligible retirement exists at this origin, so the policy correctly leaves him available. The count-link model raises 52.76 to 84.16 PA against 351 and contribution .0835 to .1332 against 3.0917. This modest improvement leaves both a large playing-time miss and an unchanged low batting-rate forecast. Only five distinct training people match the broad age-40 partial-workload profile. Cruz, Molina, Cabrera and Suzuki subsequently have 507/270/433/159 PA; they show older players can continue, not that every old partial-workload player is guaranteed a farewell surge.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nelson Cruz | 40.0 | 584 | 0 | 310.02 | 262.48 | 507 | 0.83625 |
| Yadier Molina | 38.0 | 473 | 0 | 303.86 | 308.19 | 270 | -0.79611 |
| Miguel Cabrera | 38.0 | 526 | 0 | 302.95 | 361.09 | 433 | 0.15391 |
| Kurt Suzuki | 37.0 | 247 | 0 | 21.97 | 66.47 | 159 | -0.22900 |

## Dansby Swanson 2016 to 2017

Player 621020, row 24571; selected as pa largest gain; age 22.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2015 | Aminus | 99 | 22 | 1 | 14 | 12 |
| 2016 | AA | 377 | 84 | 8 | 71 | 33 |
| 2016 | Aplus | 93 | 21 | 1 | 13 | 13 |
| 2016 | MLB | 145 | 38 | 3 | 34 | 8 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 226.7206 | -0.37130 | 0.559831 |
| poisson | 497.3770 | -0.37130 | 1.228150 |
| Actual | 551 | -2.3649172779607905 | -0.476809 |

Contribution arithmetic: expected PA × (-0.371302/600 + 0.00308809). Candidate raw mean 497.376959; raw log prediction 6.209348. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| on_40man | 1.0 | 79.832011 |
| MLB_0_pa | 145.0 | 34.457339 |
| role_pool_AA | 4.4361702127659575 | 21.502884 |
| age_centered | -1.0 | 13.298664 |
| role_mlb_0 | 3.8541666666666665 | 12.557965 |
| quality_0 | 0.030552515736128192 | 10.645853 |
| pooled_MLB_BB | 0.0653061224489796 | 6.344317 |
| pooled_mlb_quality | 0.030552515736128192 | -6.231140 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| MLB_0_pa | 145.0 | 1.044086 |
| games_pool_MLB | 38.0 | 0.976260 |
| on_40man | 1.0 | 0.943369 |
| work_0 | 145.11943986820427 | 0.494091 |
| games_pool_DSL | 0.0 | 0.356800 |
| pooled_MLB_pa | 145.0 | 0.317777 |
| role_minor_0 | 4.434782608695652 | 0.246324 |
| pooled_Aminus_3B | 0.016183035714285716 | 0.242120 |

Distinct-player profile support: [{'row_id': 24571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Actual mature-fold chronology support: [{'row_id': 24571, 'horizon': 1, 'player_id': 621020, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.030552515736128192, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 69, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2016, 'fit_fold': 3}].

Swanson's 377 AA PA in 84 games plus 93 A-plus PA precede 145 MLB PA in 38 games. Candidate PA rises 226.72 to 497.38 against 551, the largest PA gain. Yet contribution rises .560 to 1.228 while actual is negative -.477. The fixed -0.371 batting-wins/600 estimate is not negative enough to explain his actual offense. A clearly better opportunity number can therefore worsen delivered value. Almora, Bregman and Bell subsequently get 323/626/620 PA, but comparable brief debut Dahl gets zero. The positive MLB-exposure and roster log-path contributions are plausible job signals, not proof a cohort-wide increase is safe.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Albert Almora Jr. | 22.0 | 117 | 336 | 254.25 | 180.83 | 323 | 1.31527 |
| Alex Bregman | 22.0 | 217 | 368 | 445.74 | 534.21 | 626 | 3.58203 |
| Josh Bell | 23.0 | 152 | 484 | 221.71 | 249.88 | 620 | 2.87812 |
| David Dahl | 22.0 | 237 | 400 | 387.02 | 628.99 | 0 | 0.00000 |

## David Dahl 2016 to 2017

Player 621311, row 24584; selected as pa largest harm, pa false high; age 22.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 422 | 90 | 10 | 65 | 23 |
| 2014 | Aplus | 125 | 29 | 4 | 27 | 5 |
| 2015 | AA | 302 | 73 | 6 | 72 | 11 |
| 2015 | Aminus | 24 | 6 | 0 | 9 | 0 |
| 2016 | AA | 332 | 76 | 13 | 85 | 38 |
| 2016 | AAA | 68 | 16 | 5 | 11 | 5 |
| 2016 | MLB | 237 | 63 | 7 | 59 | 15 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 387.0174 | 0.68761 | 1.638675 |
| poisson | 628.9884 | 0.68761 | 2.663207 |
| Actual | 0 | unobserved at zero PA | 0.000000 |

Contribution arithmetic: expected PA × (0.687612/600 + 0.00308809). Candidate raw mean 628.988397; raw log prediction 6.444113. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| MLB_0_pa | 237.0 | 114.514300 |
| quality_0 | 0.4303166325984906 | 107.754857 |
| on_40man | 1.0 | 47.361371 |
| work_0 | 237.1952224052718 | 29.023403 |
| pooled_MLB_K | 0.2433234421364985 | -22.302570 |
| age_centered | -1.0 | 21.022397 |
| role_mlb_0 | 3.7945205479452055 | 19.349856 |
| pooled_AAA_BABIP | 0.3767123287671233 | -9.578688 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| MLB_0_pa | 237.0 | 1.505437 |
| games_pool_MLB | 63.0 | 1.358612 |
| on_40man | 1.0 | 0.717020 |
| work_0 | 237.1952224052718 | 0.450431 |
| games_pool_DSL | 0.0 | 0.374186 |
| pooled_MLB_pa | 237.0 | 0.223269 |
| pooled_A_HBP | 0.004530011325028313 | 0.191804 |
| pooled_Aminus_K | 0.2533557046979866 | 0.171498 |

Distinct-player profile support: [{'row_id': 24584, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'partial', 'draft_known': 1, 'profile_players': 52}]. Actual mature-fold chronology support: [{'row_id': 24584, 'horizon': 1, 'player_id': 621311, 'origin_year': 2016, 'elapsed': 0, 'current_state': 2, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.4303166325984906, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 415, 'current_players': 367, 'regular_players': 6496, 'joint_players': 15, 'quality_joint_players': 61, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'fit_year': 2016, 'fit_fold': 1}].

Dahl's 332 AA and 68 AAA PA precede 237 MLB PA in 63 games, with seven MLB HR. Candidate PA increases 387.02 to 628.99 and contribution 1.639 to 2.663 against actual zero, making this the largest workload harm and false high. Recent MLB involvement and roster membership account for much of the log-space increase. Bregman, Peraza, Polanco and Swanson subsequently play substantial amounts; the opportunity signal is not inherently absurd, but the new loss concentrates too much mean workload here. Future absence is an observed outcome, not an injury input known to this model. Do not retrofit the later zero season into the cutoff data or claim this single event proves a deterministic health model could predict it.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alex Bregman | 22.0 | 217 | 368 | 445.74 | 534.21 | 626 | 3.58203 |
| José Peraza | 22.0 | 256 | 322 | 380.10 | 376.81 | 518 | -0.45891 |
| Jorge Polanco | 22.0 | 270 | 325 | 460.91 | 512.99 | 544 | 1.08853 |
| Dansby Swanson | 22.0 | 145 | 470 | 226.72 | 497.38 | 551 | -0.47681 |

## Fernando Tatis Jr. 2022 to 2023

Player 665487, row 47261; selected as pa false low; age 23.0, Upper minors.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 257 | 59 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 130 | 42 | 153 | 56 |
| 2022 | AA | 14 | 4 | 0 | 2 | 4 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 140.1497 | 1.27950 | 0.737674 |
| poisson | 25.8822 | 1.27950 | 0.136230 |
| Actual | 635 | 0.7268065858888001 | 2.735212 |

Contribution arithmetic: expected PA × (1.279500/600 + 0.00313097). Candidate raw mean 25.882175; raw log prediction 3.253555. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| pooled_mlb_quality | 1.3673684989925885 | 35.265844 |
| age_centered | -0.8 | 27.615191 |
| regular_window_scaled | 0.6666666666666666 | 24.137649 |
| role_pool_MLB | 4.223560910307898 | 19.672920 |
| work_0 | 0.0 | -19.594744 |
| on_40man | 0.0 | -18.644224 |
| games_mlb_2 | 159.3 | 17.810031 |
| pooled_MLB_K | 0.2633863965267728 | -15.994417 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| games_pool_MLB | 199.57999999999998 | 1.003263 |
| pooled_MLB_pa | 591.0 | 0.642592 |
| games_mlb_1 | 130.0 | 0.434051 |
| work_0 | 0.0 | -0.255349 |
| on_40man | 0.0 | -0.191014 |
| pooled_DSL_pa | 0.0 | 0.171925 |
| age_centered | -0.8 | 0.124085 |
| position_6 | 1.0 | 0.098358 |

Distinct-player profile support: [{'row_id': 47261, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 0, 'profile_players': 26}]. Actual mature-fold chronology support: [{'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 797, 'current_players': 10645, 'regular_players': 385, 'joint_players': 26, 'quality_joint_players': 812, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2022, 'fit_fold': 0}].

Tatis has 546 MLB PA and 42 HR in 2021, following 257 PA and 17 HR in shortened 2020, but only 14 AA PA in four games in 2022. Candidate PA collapses 140.15 to 25.88 against 635 actual; contribution falls .738 to .136 against 2.735. The fixed batting head still recognizes positive talent. This feature branch does not encode the specific finite suspension and remaining eligibility, so the absent-season profile conflates a returning established star with marginal prior debuts. Only 26 broad matching training people exist. Apostel, Welker, Marchan and Jones are nearby under age/workload distance but are not equivalent former-star return cases. This is an availability/history representation gap, not evidence Tatis had no ability or that adding every ordinary absent player's PA would help.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sherten Apostel | 23.0 | 0 | 77 | 0.00 | 8.72 | 0 | 0.00000 |
| Colton Welker | 24.0 | 0 | 45 | 27.15 | 13.50 | 0 | 0.00000 |
| Rafael Marchán | 23.0 | 0 | 278 | 97.92 | 86.28 | 0 | 0.00000 |
| Jahmai Jones | 24.0 | 0 | 118 | 24.65 | 16.16 | 11 | -0.02098 |

## Christian Vázquez 2022 to 2023

Player 543877, row 46425; selected as pa ordinary; age 31.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 189 | 47 | 7 | 43 | 16 |
| 2021 | MLB | 498 | 138 | 6 | 84 | 33 |
| 2022 | MLB | 426 | 119 | 9 | 69 | 22 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 340.1331 | -0.83143 | 0.593621 |
| poisson | 355.2521 | -0.83143 | 0.620007 |
| Actual | 355 | -2.6916800000802774 | -0.493470 |

Contribution arithmetic: expected PA × (-0.831428/600 + 0.00313097). Candidate raw mean 355.252073; raw log prediction 5.872828. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 426.0 | 281.569818 |
| role_mlb_0 | 3.612403100775194 | -48.914533 |
| quality_0 | 0.05651852063557126 | 27.809620 |
| on_40man | 1.0 | 26.048536 |
| regular_window_scaled | 1.0 | 24.137649 |
| age_centered | 0.8 | -12.791126 |
| role_pool_MLB | 3.6539611360239164 | -11.395490 |
| pooled_MLB_K | 0.17826170745808437 | 10.987413 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| work_0 | 426.0 | 1.953490 |
| games_pool_MLB | 305.54 | 1.009750 |
| pooled_MLB_pa | 937.8000000000001 | 0.563620 |
| on_40man | 1.0 | 0.470442 |
| games_mlb_0 | 119.0 | 0.346163 |
| pooled_DSL_pa | 0.0 | 0.171925 |
| role_minor_0 | 4.0 | 0.142210 |
| role_mlb_0 | 3.612403100775194 | -0.104331 |

Distinct-player profile support: [{'row_id': 46425, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 56}]. Actual mature-fold chronology support: [{'row_id': 46425, 'horizon': 1, 'player_id': 543877, 'origin_year': 2022, 'elapsed': 8, 'current_state': 3, 'regular_window': 3, 'age': 31.0, 'quality_0': 0.05651852063557126, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 341, 'current_players': 454, 'regular_players': 271, 'joint_players': 260, 'quality_joint_players': 368, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2022, 'fit_fold': 0}].

Vazquez's source shows 498 MLB PA in 138 games followed by 426 in 119, with real PA/game involvement about 3.61. Candidate PA moves 340.13 to 355.25 against 355: an excellent individual workload result. Nevertheless contribution increases .594 to .620 while actual is negative -.493. The unchanged -.831 batting-wins/600 estimate remains too optimistic for his actual offense. Exact playing time therefore does not validate overall value or the catcher defense component, which is not part of this target. Choi, Taylor, Michael A. Taylor and Cooper receive varied next PA, and the 56-person broad support group is not a precise catcher-only model.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ji Man Choi | 31.0 | 419 | 0 | 340.04 | 387.21 | 117 | -0.12381 |
| Chris Taylor | 31.0 | 454 | 8 | 374.31 | 429.68 | 384 | 1.35401 |
| Michael A. Taylor | 31.0 | 456 | 9 | 360.43 | 376.01 | 388 | 0.82748 |
| Garrett Cooper | 31.0 | 469 | 11 | 469.50 | 463.42 | 457 | 1.25759 |

## Bo Bichette 2023 to 2024

Player 666182, row 51352; selected as value largest gain; age 25.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | MLB | 690 | 159 | 29 | 137 | 40 |
| 2022 | MLB | 697 | 159 | 24 | 155 | 41 |
| 2023 | AAA | 6 | 2 | 1 | 0 | 0 |
| 2023 | MLB | 601 | 135 | 20 | 115 | 27 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 664.7809 | 1.37928 | 3.586407 |
| poisson | 548.2781 | 1.37928 | 2.957890 |
| Actual | 336 | -2.2433501932116338 | -0.206990 |

Contribution arithmetic: expected PA × (1.379277/600 + 0.00309608). Candidate raw mean 548.278147; raw log prediction 6.306783. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 601.0 | 304.749293 |
| role_mlb_0 | 4.4206896551724135 | 58.618151 |
| games_mlb_1 | 159.0 | 44.268633 |
| quality_0 | 0.5465508522198342 | 41.345100 |
| pooled_mlb_quality | 1.0554962697761279 | 36.958260 |
| games_mlb_2 | 159.0 | 33.130992 |
| role_pool_AAA | 3.8333333333333335 | -21.064336 |
| age_centered | -0.4 | 20.742182 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| work_0 | 601.0 | 2.066558 |
| pooled_MLB_pa | 1572.6 | 0.948296 |
| games_pool_MLB | 357.59999999999997 | 0.871304 |
| games_pool_DSL | 0.0 | 0.429716 |
| on_40man | 1.0 | 0.337195 |
| role_mlb_0 | 4.4206896551724135 | 0.237748 |
| games_mlb_0 | 135.0 | 0.198801 |
| role_pool_AAA | 3.8333333333333335 | -0.138613 |

Distinct-player profile support: [{'row_id': 51352, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 186}]. Actual mature-fold chronology support: [{'row_id': 51352, 'horizon': 1, 'player_id': 666182, 'origin_year': 2023, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 25.0, 'quality_0': 0.5465508522198342, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 838, 'current_players': 499, 'regular_players': 292, 'joint_players': 84, 'quality_joint_players': 410, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2023, 'fit_fold': 2}].

Bichette's prior 690/697 MLB PA precede 601 in 2023 plus a six-PA AAA stint. The candidate lowers expected PA 664.78 to 548.28 against 336, producing the largest contribution gain: 3.586 to 2.958 against -.207 actual. Both forecasts still assume the unchanged positive 1.379 batting-wins/600 rate and miss the offensive deterioration. Lower opportunity happens to help this outcome; it is not evidence the model predicted a specific later injury or explained why the decline occurred. Robert, Contreras, Vaughn and Stott have mixed later workload. The broad 186-person support sample and log accounting support ordinary regular-player prediction, not a medical forecast.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Luis Robert Jr. | 25.0 | 595 | 0 | 531.72 | 478.16 | 425 | 0.42763 |
| William Contreras | 25.0 | 611 | 0 | 533.63 | 574.90 | 679 | 4.81251 |
| Andrew Vaughn | 25.0 | 615 | 0 | 544.78 | 610.92 | 619 | 1.68482 |
| Bryson Stott | 25.0 | 640 | 0 | 544.71 | 579.20 | 571 | 1.19955 |

## Juan Soto 2018 to 2019

Player 665742, row 34521; selected as value largest harm; age 19.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | Aminus | 24 | 6 | 0 | 4 | 3 |
| 2016 | RK124 | 183 | 45 | 5 | 25 | 14 |
| 2017 | A | 96 | 23 | 3 | 8 | 8 |
| 2017 | RK124 | 27 | 9 | 0 | 1 | 2 |
| 2018 | A | 74 | 16 | 5 | 13 | 13 |
| 2018 | AA | 35 | 8 | 2 | 7 | 4 |
| 2018 | Aplus | 73 | 15 | 7 | 8 | 11 |
| 2018 | MLB | 494 | 116 | 22 | 99 | 69 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 511.2316 | 2.39930 | 3.618292 |
| poisson | 359.7102 | 2.39930 | 2.545885 |
| Actual | 659 | 3.8198495149957985 | 6.208558 |

Contribution arithmetic: expected PA × (2.399299/600 + 0.00307877). Candidate raw mean 359.710221; raw log prediction 5.885299. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| MLB_0_pa | 494.0 | 154.019987 |
| work_0 | 493.7967914438502 | 126.077679 |
| role_mlb_0 | 4.238095238095238 | 61.661019 |
| quality_0 | 1.0403057058309162 | 56.093150 |
| regular_window_scaled | 0.3333333333333333 | 31.170735 |
| role_pool_MLB | 4.238095238095238 | 28.487953 |
| age_centered | -1.6 | 28.366639 |
| role_minor_1 | 3.880952380952381 | -15.980232 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| MLB_0_pa | 494.0 | 2.083875 |
| games_pool_MLB | 116.0 | 0.912756 |
| on_40man | 1.0 | 0.570290 |
| A_0_pa | 74.0 | -0.515983 |
| pooled_MLB_pa | 494.0 | 0.381667 |
| work_0 | 493.7967914438502 | 0.320084 |
| games_pool_DSL | 0.0 | 0.308665 |
| role_mlb_0 | 4.238095238095238 | 0.220575 |

Distinct-player profile support: [{'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 0}]. Actual mature-fold chronology support: [{'row_id': 34521, 'horizon': 1, 'player_id': 665742, 'origin_year': 2018, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 19.0, 'quality_0': 1.0403057058309162, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 2, 'elapsed_players': 579, 'current_players': 366, 'regular_players': 344, 'joint_players': 12, 'quality_joint_players': 3, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'fit_year': 2018, 'fit_fold': 0}].

Soto has 494 MLB PA in 116 games and 22 HR at age 19, in addition to short A/A-plus/AA stints during the same year. Candidate PA falls 511.23 to 359.71 against 659 and contribution 3.618 to 2.546 against 6.209, the largest contribution harm. The unchanged strong 2.399 batting-wins/600 estimate does not compensate for compressed opportunity. In the fitted log path, 74 same-year A PA contributes negatively even though he has already established MLB exposure; a level-transition feature can make an implausible allocation when support is thin. There are zero exact broad age-band/workload/draft-status matching training people, not proof no nearby younger regular existed. Acuna, Torres, Devers and Albies all continue with large workload; they are older nearby origin comparators, not exact age-19 controls. This is a support/transition warning and another reason not to promote this loss change.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ronald Acuña Jr. | 20.0 | 487 | 101 | 544.91 | 587.21 | 715 | 5.11865 |
| Gleyber Torres | 21.0 | 484 | 67 | 490.70 | 526.76 | 604 | 3.87291 |
| Rafael Devers | 21.0 | 490 | 26 | 406.85 | 480.83 | 702 | 5.47397 |
| Ozzie Albies | 21.0 | 684 | 0 | 613.85 | 651.01 | 702 | 4.15047 |

## Yordan Alvarez 2024 to 2025

Player 670541, row 55521; selected as value false high; age 27.0, Current MLB.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 577.4905 | 3.70970 | 5.374704 |
| poisson | 587.1762 | 3.70970 | 5.464849 |
| Actual | 199 | 0.919648372891386 | 0.925104 |

Contribution arithmetic: expected PA × (3.709704/600 + 0.00312416). Candidate raw mean 587.176163; raw log prediction 6.375325. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 635.2614244545081 | 322.222292 |
| role_mlb_0 | 4.2993630573248405 | 57.464999 |
| quality_0 | 1.415653196303136 | 52.228185 |
| pooled_mlb_quality | 2.457088938891907 | 23.983220 |
| role_pool_MLB | 4.278250303766707 | 18.921383 |
| quality_1 | 1.3830873087907403 | 15.954412 |
| regular_window_scaled | 1.0 | 13.701698 |
| MLB_0_pa | 635.0 | 12.903590 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| work_0 | 635.2614244545081 | 2.202188 |
| games_pool_MLB | 319.2 | 1.389152 |
| on_40man | 1.0 | 0.353166 |
| pooled_MLB_pa | 1368.4 | 0.311349 |
| pooled_DSL_HR | 0.03 | 0.300007 |
| role_mlb_0 | 4.2993630573248405 | 0.231569 |
| games_mlb_0 | 147.0 | 0.210224 |
| role_minor_0 | 4.0 | 0.104164 |

Distinct-player profile support: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 173}]. Actual mature-fold chronology support: [{'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 903, 'current_players': 538, 'regular_players': 310, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2024, 'fit_fold': 2}].

Alvarez has 561/496/635 MLB PA and 37/31/35 HR in the source window. Candidate PA rises 577.49 to 587.18, contribution 5.375 to 5.465, against 199 PA and .925 actual. The recent regular-workload signal and retained 3.710 batting-wins/600 estimate are understandable before the later outcome; the additional candidate PA still worsens the largest contribution false high. Devers, India, Donovan and Bohm mostly continue with substantial PA. No specific later health event is available in these fitted inputs, so this cannot be labeled a proven avoidable injury miss. It remains a large realized value error that annual mean and health uncertainty should acknowledge.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rafael Devers | 27.0 | 601 | 0 | 566.99 | 603.02 | 729 | 5.23429 |
| Jonathan India | 27.0 | 637 | 0 | 545.44 | 547.75 | 567 | 1.28649 |
| Brendan Donovan | 27.0 | 652 | 0 | 570.90 | 587.09 | 515 | 2.59344 |
| Alec Bohm | 27.0 | 606 | 4 | 590.93 | 616.28 | 504 | 2.05959 |

## Ryan Ritter 2024 to 2025

Player 690022, row 56348; selected as value ordinary; age 23.0, Upper minors.

| Season | Level | PA | Games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | RK121 | 29 | 8 | 1 | 3 | 2 |
| 2023 | A | 295 | 65 | 18 | 72 | 36 |
| 2023 | AA | 29 | 8 | 0 | 11 | 3 |
| 2023 | Aplus | 201 | 46 | 6 | 69 | 22 |
| 2024 | AA | 373 | 91 | 7 | 88 | 34 |

| Forecast | Expected PA | Fixed batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 2.3754 | -0.71526 | 0.004589 |
| poisson | 13.5512 | -0.71526 | 0.026182 |
| Actual | 207 | -1.7929129394467587 | 0.026460 |

Contribution arithmetic: expected PA × (-0.715264/600 + 0.00312416). Candidate raw mean 13.551189; raw log prediction 2.606474. Retirement/permanent availability policies are identical.

All 239 actual inputs and the exact two fitted-head traces are preserved in cases.json. Largest path effects below are descriptive tree accounting, not causal explanations. Candidate terms are additive in LOG mean, not additive PA. Missing-level role and rate defaults are not actual player measurements.

| Input | Actual encoded value | Identity-link path PA effect |
|---|---:|---:|
| work_0 | 0.0 | -23.158881 |
| on_40man | 0.0 | -6.570911 |
| role_pool_AAA | 4.0 | -1.659234 |
| quality_0 | 0.0 | -1.546987 |
| position_6 | 1.0 | 1.413912 |
| role_pool_AA | 4.06145251396648 | 1.316565 |
| pooled_mlb_quality | 0.0 | -0.763750 |
| regular_window_scaled | 0.0 | -0.693749 |

| Input | Actual encoded value | Count-link path LOG effect |
|---|---:|---:|
| role_pool_AA | 4.06145251396648 | 0.818005 |
| pooled_AA_pa | 396.2 | 0.667679 |
| pooled_DSL_HR | 0.03 | 0.280101 |
| age_centered | -0.8 | 0.267593 |
| role_minor_0 | 4.089108910891089 | 0.253564 |
| pooled_MLB_pa | 0.0 | -0.216295 |
| work_0 | 0.0 | -0.162229 |
| MLB_0_pa | 0.0 | -0.118293 |

Distinct-player profile support: [{'row_id': 56348, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1829}]. Actual mature-fold chronology support: [{'row_id': 56348, 'horizon': 1, 'player_id': 690022, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 11318, 'current_players': 11841, 'regular_players': 11936, 'joint_players': 4886, 'quality_joint_players': 11400, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'fit_year': 2024, 'fit_fold': 3}].

Ritter's 2023 A/A-plus/AA PA total 525, followed by 373 AA PA in 91 games with seven HR. Candidate PA rises 2.38 to 13.55 against 207; contribution .00459 to .02618 looks almost exactly right against .02646. That agreement is an offsetting-error result: far too few PA multiplied by a batting estimate too optimistic for the realized low-contribution MLB season. It is not a validated ordinary value success. Positive stabilized AA role and pooled exposure log effects raise a tiny prior; absent DSL HR .03 remains a default, not actual DSL skill. Valera gets 48 PA, while Susac, Spain and Rivera get zero, so the broad 1,829-person support group includes many non-arrivals. The actual upper-minor readiness miss remains visible even when pooled value scoring rewards the cancellation.

| Origin-selected peer | Age | Origin MLB PA | Minor PA | Games mean PA | Count mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| George Valera | 23.0 | 0 | 374 | 45.96 | 41.91 | 48 | 0.22465 |
| Daniel Susac | 23.0 | 0 | 370 | 14.69 | 30.32 | 0 | 0.00000 |
| Garrett Spain | 23.0 | 0 | 377 | 0.00 | 2.69 | 0 | 0.00000 |
| Josh Rivera | 23.0 | 0 | 368 | 0.40 | 4.25 | 0 | 0.00000 |

## Disposition

Reject this fixed count-link candidate as a working-model replacement. Overall PA and contribution worsen, all seven origin PA errors worsen, public workload does not improve, and player gains coexist with consequential harms and offsetting errors. This does not reject every count model or prove the existing baseline complete. Keep V33b plus reversible retirement as the research working assembly, with V38 a separate games candidate. Do not attach a Poisson variance, arrival probability or calibrated risk claim. No next-model decision was made before completing these fourteen reviews. Protected 2026 outcomes and frozen/deployed forecasts remain unchanged.
