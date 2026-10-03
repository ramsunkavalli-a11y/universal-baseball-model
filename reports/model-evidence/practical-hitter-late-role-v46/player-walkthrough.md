# Late-season opportunity: eighteen actual player reviews

Next-calendar-year MLB expected PA and batting-plus-replacement contribution, not full WAR. Same batting head, identities, availability policies and learner settings; ten reliable MLB PA-timing features are added. The new window-game predictors were withheld before fits under the source amendment. Peers are selected by origin age/workload/quality, not outcomes.

Tree-path terms exactly reconstruct each fitted forecast but are descriptive, not causal. Their sum inside the new fit is not a decomposition of the old-to-new change, because all trees are refitted. All 249 actual inputs and full saved traces are preserved in cases.json.

## Nick Kurtz 2024 to 2025

Player 701762, row 57052; fixed diagnostic; age 21.0, Upper minors.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| Certified no own MLB PA within captured years | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 29.9431 | -0.13556 | 0.086782 |
| late | 24.9204 | -0.13556 | 0.072225 |
| retired_safe_ridge | 50.4937 | -0.11288 | 0.148251 |
| Actual | 489 | 5.150009420178844 | 5.720989 |

Candidate raw mean 24.920404, bounded/availability-adjusted mean 24.920404. Contribution = 24.920404 × (-0.135562/600 + 0.00312416). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.289435 plus all full-record path terms = raw PA 29.943090.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 26.886700 |
| work_0 | 0.0 | -22.958102 |
| on_40man | 0.0 | -6.293909 |
| pooled_AA_BABIP | 0.3090909090909091 | 2.118989 |
| quality_0 | 0.0 | -1.687118 |
| role_pool_AA | 3.6666666666666665 | -1.463170 |
| pooled_MLB_BABIP | 0.3 | 1.427221 |
| pooled_AA_BB | 0.08695652173913043 | 1.418949 |

### Late-role candidate: exact path accounting

Reference 39.291975 plus all full-record path terms = raw PA 24.920404.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 27.283141 |
| work_0 | 0.0 | -17.301377 |
| on_40man | 0.0 | -6.395396 |
| late_usage_0_late_pa | 0.0 | -5.915777 |
| age_centered | -1.2 | 3.225986 |
| pooled_AA_HR | 0.02608695652173913 | -2.729357 |
| quality_0 | 0.0 | -1.844592 |
| pooled_AA_BB | 0.08695652173913043 | -1.635497 |
| late_usage_1_late_pa | 0.0 | -0.547512 |
| late_usage_1_preceding_pa | 0.0 | -0.298102 |
| late_usage_0_late_pace | 0.0 | -0.082166 |
| late_usage_1_preceding_pace | 0.0 | -0.059321 |
| late_usage_0_preceding_pa | 0.0 | 0.020721 |
| late_usage_0_preceding_pace | 0.0 | -0.015089 |

Old distinct-player profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1744}]. Late-stage/debut/age/exposure profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'late_band': 'absent', 'late_profile_players': 2579}]. Actual mature fold support: [{'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11239, 'current_players': 11751, 'regular_players': 11845, 'joint_players': 9411, 'quality_joint_players': 11314, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Kurtz's four HR and ten walks in 35 A PA, followed by 15 AA PA, remain in the old inputs. Both MLB windows are certified zero, not missing minor history. Expected PA falls 29.94 to 24.92 against 489, contribution .0868 to .0722 against 5.721. The new current late-PA path contributes -5.92, while pick-four pedigree contributes +27.28; these are within-fit accounting terms, not a causal decomposition of the five-PA net change. Broad support has 2,579 same late-band training people, not comparable elite college hitters. Montgomery, Hartl, Soto and Quero all do not arrive next year under the origin-only comparison. This addition worsens an already important fast-entry miss and has no direct signal about his AA readiness.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Benny Montgomery | 21.0 | 0 | 48 | 40.93 | 32.19 | 0 | 0.00000 |
| Ben Hartl | 21.0 | 0 | 57 | 0.00 | 0.00 | 0 | 0.00000 |
| Wally Soto | 21.0 | 0 | 85 | 8.74 | 1.14 | 0 | 0.00000 |
| Jeferson Quero | 21.0 | 0 | 1 | 76.59 | 76.54 | 0 | 0.00000 |

## Anthony Volpe 2022 to 2023

Player 683011, row 48516; fixed diagnostic; age 21.0, Upper minors.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 257 | 54 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 55 | 15 | 58 | 26 |
| 2022 | AA | 497 | 110 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 22 | 3 | 30 | 8 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| Certified no own MLB PA within captured years | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 166.1382 | -0.14770 | 0.479277 |
| late | 140.0376 | -0.14770 | 0.403982 |
| retired_safe_ridge | 63.2182 | -0.07924 | 0.189585 |
| Actual | 601 | -1.3447727729230707 | 0.513728 |

Candidate raw mean 140.037571, bounded/availability-adjusted mean 140.037571. Contribution = 140.037571 × (-0.147697/600 + 0.00313097). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.773582 plus all full-record path terms = raw PA 166.138177.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| role_pool_AAA | 4.34375 | 59.842622 |
| age_centered | -1.2 | 38.942856 |
| role_pool_AA | 4.475 | 28.539544 |
| work_0 | 0.0 | -23.047864 |
| Aplus_1_pa | 256.0 | 10.573611 |
| pooled_A_3B | 0.014725130890052354 | 8.985924 |
| pooled_AA_K | 0.18592964824120603 | 7.545442 |
| on_40man | 0.0 | -6.124249 |

### Late-role candidate: exact path accounting

Reference 38.773074 plus all full-record path terms = raw PA 140.037571.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| role_pool_AAA | 4.34375 | 59.487901 |
| role_pool_AA | 4.475 | 29.612180 |
| age_centered | -1.2 | 18.182980 |
| work_0 | 0.0 | -17.302636 |
| pooled_A_3B | 0.014725130890052354 | 8.714412 |
| Aplus_1_pa | 256.0 | 8.532447 |
| late_usage_0_late_pa | 0.0 | -6.426867 |
| on_40man | 0.0 | -5.957494 |
| late_usage_1_preceding_pa | 0.0 | -0.366583 |
| late_usage_0_late_pace | 0.0 | -0.210483 |
| late_usage_1_late_pa | 0.0 | -0.130822 |
| late_usage_0_preceding_pa | 0.0 | 0.115802 |
| late_usage_0_preceding_pace | 0.0 | 0.024094 |

Old distinct-player profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1502}]. Late-stage/debut/age/exposure profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'late_band': 'absent', 'late_profile_players': 2189}]. Actual mature fold support: [{'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10086, 'current_players': 10584, 'regular_players': 10685, 'joint_players': 8356, 'quality_joint_players': 10163, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Volpe has 497 AA PA with 18 HR and 99 AAA PA with three HR after a strong A/A-plus year. The added MLB windows are zero because he has not debuted. Expected PA falls 166.14 to 140.04 against 601; contribution .4793 to .4040 against .5137. That superficially small value error still masks severely understated opportunity multiplied by overly optimistic realized batting yield. Positive AAA/AA role accounting remains, while new absent late-MLB PA contributes -6.43 inside the refitted model. Rocchio/Tena/Pages/Valera mostly have little or no later PA, so indiscriminately raising all upper-minor players is not justified. The measured never-debut upper-minor group worsens versus the games control. This timing source does not establish a future spring starting job.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Brayan Rocchio | 21.0 | 0 | 584 | 169.51 | 159.53 | 86 | -0.11915 |
| José Tena | 21.0 | 0 | 573 | 116.38 | 101.55 | 34 | -0.04262 |
| Andy Pages | 21.0 | 0 | 571 | 97.63 | 96.24 | 0 | 0.00000 |
| George Valera | 21.0 | 0 | 566 | 152.04 | 143.67 | 0 | 0.00000 |

## Aaron Judge 2016 to 2017

Player 592450, row 23934; fixed diagnostic, value false low; age 24.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 95.0 | 63.0 | 32.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 32.0, 'late_usage_0_preceding_pa': 63.0, 'late_usage_0_late_pace': 1.1455847255369929, 'late_usage_0_preceding_pace': 2.3333333333333335, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 150.2046 | -0.05720 | 0.449525 |
| late | 162.2537 | -0.05720 | 0.485585 |
| retired_safe_ridge | 143.9656 | -0.05720 | 0.430853 |
| Actual | 678 | 5.329875619792154 | 8.108407 |

Candidate raw mean 162.253687, bounded/availability-adjusted mean 162.253687. Contribution = 162.253687 × (-0.057204/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 150.204635.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| on_40man | 1.0 | 75.498701 |
| role_pool_AAA | 4.334650856389986 | 38.928232 |
| MLB_0_pa | 95.0 | 24.512022 |
| pooled_MLB_K | 0.3333333333333333 | -12.963409 |
| pooled_AAA_2B | 0.04317548746518106 | -12.710632 |
| age_centered | -0.6 | 12.462715 |
| pooled_Aplus_K | 0.244280442804428 | 9.264230 |
| role_pool_A | 4.220408163265306 | 7.668758 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 162.253687.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| on_40man | 1.0 | 77.200892 |
| role_pool_AAA | 4.334650856389986 | 30.848197 |
| MLB_0_pa | 95.0 | 19.214533 |
| pooled_MLB_K | 0.3333333333333333 | -11.840091 |
| late_usage_0_late_pa | 32.0 | 11.821485 |
| pooled_Aplus_K | 0.244280442804428 | 11.747646 |
| pooled_AA_BABIP | 0.3260135135135135 | -10.683110 |
| role_minor_0 | 4.368932038834951 | 9.212936 |
| late_usage_0_preceding_pa | 63.0 | -0.821794 |
| late_usage_1_preceding_pa | 0.0 | -0.387386 |
| late_usage_0_preceding_pace | 2.3333333333333335 | -0.066982 |
| late_usage_1_late_pa | 0.0 | -0.023438 |
| late_usage_1_preceding_pace | 0.0 | -0.004093 |

Old distinct-player profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Late-stage/debut/age/exposure profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'late_band': '1-49', 'late_profile_players': 166}]. Actual mature fold support: [{'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 181, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Judge has 410 AAA PA and 19 HR, then 95 MLB PA with 42 K. His last windows contain 63 preceding and 32 late PA: actual late usage is declining. Candidate PA nevertheless rises 150.20 to 162.25 against 678, with a positive 11.82 late-PA tree-path term alongside roster/AAA involvement. The increase is small and the fixed -0.057 batting-wins/600 head still gives only .486 contribution against 8.108. Moya later gets zero, Austin 46, Cowart 117 and Difo 365, illustrating that brief debuts need uncertainty rather than automatic regular status. The new late-exposure support count is 166 distinct broad-profile people. No later injury/recovery or breakout fact has entered the input.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steven Moya | 24.0 | 100 | 426 | 203.47 | 168.52 | 0 | 0.00000 |
| Tyler Austin | 24.0 | 90 | 444 | 144.43 | 154.08 | 46 | 0.05556 |
| Kaleb Cowart | 24.0 | 87 | 458 | 141.72 | 174.31 | 117 | 0.12269 |
| Wilmer Difo | 24.0 | 66 | 456 | 217.86 | 221.30 | 365 | 0.11034 |

## Aaron Judge 2024 to 2025

Player 592450, row 54849; fixed diagnostic; age 32.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 696 | 157 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 106 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 158 | 58 | 171 | 113 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2023 | 458.0 | 113.0 | 111.0 | 26.46667 | 27.06667 |
| 2024 | 704.0 | 117.0 | 105.0 | 27.20000 | 25.66667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 105.0, 'late_usage_0_preceding_pa': 117.0, 'late_usage_0_late_pace': 4.090909090909091, 'late_usage_0_preceding_pace': 4.301470588235294, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 111.0, 'late_usage_1_preceding_pa': 113.0, 'late_usage_1_late_pace': 4.100985221674877, 'late_usage_1_preceding_pace': 4.269521410579346}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 547.3890 | 4.55334 | 5.864212 |
| late | 566.4897 | 4.55334 | 6.068838 |
| retired_safe_ridge | 534.2750 | 4.50176 | 5.677793 |
| Actual | 679 | 6.287431083532908 | 9.231050 |

Candidate raw mean 566.489683, bounded/availability-adjusted mean 566.489683. Contribution = 566.489683 × (4.553340/600 + 0.00312416). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.305820 plus all full-record path terms = raw PA 547.389035.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 704.2898312062578 | 319.670118 |
| quality_0 | 2.794424993741549 | 57.074454 |
| role_mlb_0 | 4.428571428571429 | 55.279547 |
| games_mlb_2 | 157.0 | 24.645577 |
| pooled_mlb_quality | 3.6485663788613953 | 24.507835 |
| age_centered | 1.0 | -17.616136 |
| pooled_MLB_K | 0.25377833753148615 | -15.612146 |
| role_pool_MLB | 4.403458213256484 | 12.923628 |

### Late-role candidate: exact path accounting

Reference 39.303721 plus all full-record path terms = raw PA 566.489683.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 704.2898312062578 | 242.850272 |
| late_usage_0_late_pa | 105.0 | 97.530551 |
| quality_0 | 2.794424993741549 | 42.431985 |
| role_mlb_0 | 4.428571428571429 | 38.627714 |
| games_mlb_2 | 157.0 | 25.074303 |
| age_centered | 1.0 | -22.074996 |
| pooled_mlb_quality | 3.6485663788613953 | 19.436161 |
| late_usage_1_late_pa | 111.0 | 12.793600 |
| late_usage_0_preceding_pace | 4.301470588235294 | 10.060715 |
| late_usage_0_late_pace | 4.090909090909091 | 9.147883 |
| late_usage_1_preceding_pa | 113.0 | 4.763605 |
| late_usage_1_preceding_pace | 4.269521410579346 | 2.956446 |
| late_usage_1_late_pace | 4.100985221674877 | 2.333444 |
| late_usage_0_preceding_pa | 117.0 | -2.050176 |

Old distinct-player profile: [{'row_id': 54849, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 87}]. Late-stage/debut/age/exposure profile: [{'row_id': 54849, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'late_band': '100plus', 'late_profile_players': 142}]. Actual mature fold support: [{'row_id': 54849, 'horizon': 1, 'player_id': 592450, 'origin_year': 2024, 'elapsed': 8, 'current_state': 3, 'regular_window': 3, 'age': 32.0, 'quality_0': 2.794424993741549, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 407, 'current_players': 546, 'regular_players': 300, 'joint_players': 294, 'quality_joint_players': 80, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': True, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': True, 'profile_check_pass': False}].

Judge's three-year 696/458/704 PA and 62/37/58 HR remain unchanged. Current preceding/late PA are 117/105 and prior-year 113/111, with current late pace about 4.09 PA per scheduled average team game. Candidate PA rises 547.39 to 566.49 against 679 and contribution 5.864 to 6.069 against 9.231, a sensible but incomplete regular-job improvement. The late-PA path contributes +97.53, replacing some old annual workload accounting; that is not a claim it causes a 97-PA net gain. Ozuna benefits, Schwarber is lowered despite later 724 PA, Harper changes little and Profar falls alongside later lower workload. The 142-person timing profile is not a Judge-upside calibration sample. Elite hitting and opportunity compression remain.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Marcell Ozuna | 33.0 | 688 | 0 | 544.03 | 570.80 | 592 | 2.91697 |
| Kyle Schwarber | 31.0 | 692 | 0 | 585.90 | 575.16 | 724 | 6.83256 |
| Bryce Harper | 31.0 | 631 | 0 | 527.02 | 529.95 | 580 | 4.01831 |
| Jurickson Profar | 31.0 | 668 | 0 | 506.43 | 492.82 | 371 | 2.24270 |

## Brent Rooker 2022 to 2023

Player 667670, row 47398; fixed diagnostic; age 27.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 21 | 7 | 1 | 5 | 0 |
| 2021 | AAA | 267 | 62 | 20 | 80 | 36 |
| 2021 | MLB | 213 | 58 | 9 | 70 | 15 |
| 2022 | AAA | 365 | 81 | 28 | 103 | 44 |
| 2022 | MLB | 36 | 16 | 0 | 11 | 3 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2021 | 213.0 | 74.0 | 59.0 | 26.53333 | 27.26667 |
| 2022 | 36.0 | 29.0 | 0.0 | 26.73333 | 27.60000 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 29.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 1.084788029925187, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 59.0, 'late_usage_1_preceding_pa': 74.0, 'late_usage_1_late_pace': 2.1638141809290956, 'late_usage_1_preceding_pace': 2.78894472361809}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 164.4636 | -0.37321 | 0.412633 |
| late | 155.0368 | -0.37321 | 0.388981 |
| retired_safe_ridge | 112.9894 | -0.39287 | 0.279783 |
| Actual | 526 | 1.5435493625116004 | 2.981714 |

Candidate raw mean 155.036826, bounded/availability-adjusted mean 155.036826. Contribution = 155.036826 × (-0.373208/600 + 0.00313097). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.199607 plus all full-record path terms = raw PA 164.463635.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| on_40man | 1.0 | 85.342605 |
| role_pool_AAA | 4.399715504978663 | 48.552768 |
| pooled_AAA_HR | 0.06926024167403477 | 27.453673 |
| age_centered | 0.0 | -21.363681 |
| draft_rank | 0.5322465877685258 | 14.092101 |
| pooled_MLB_K | 0.29153605015673983 | -13.779018 |
| MLB_0_pa | 36.0 | 12.451330 |
| work_0 | 36.0 | -9.604670 |

### Late-role candidate: exact path accounting

Reference 38.196378 plus all full-record path terms = raw PA 155.036826.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| on_40man | 1.0 | 83.489618 |
| role_pool_AAA | 4.399715504978663 | 38.585682 |
| pooled_AAA_HR | 0.06926024167403477 | 24.562307 |
| pooled_MLB_K | 0.29153605015673983 | -19.783772 |
| draft_rank | 0.5322465877685258 | 13.295281 |
| MLB_0_pa | 36.0 | 12.098710 |
| age_centered | 0.0 | -12.088941 |
| pooled_mlb_quality | -0.17881157361760908 | -7.985005 |
| late_usage_0_late_pa | 0.0 | -5.518593 |
| late_usage_0_late_pace | 0.0 | -2.020220 |
| late_usage_1_late_pa | 59.0 | 1.872881 |
| late_usage_1_late_pace | 2.1638141809290956 | 0.750986 |
| late_usage_1_preceding_pa | 74.0 | -0.083493 |
| late_usage_0_preceding_pa | 29.0 | 0.031931 |

Old distinct-player profile: [{'row_id': 47398, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 481}]. Late-stage/debut/age/exposure profile: [{'row_id': 47398, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': 'absent', 'late_profile_players': 407}]. Actual mature fold support: [{'row_id': 47398, 'horizon': 1, 'player_id': 667670, 'origin_year': 2022, 'elapsed': 2, 'current_state': 1, 'regular_window': 0, 'age': 27.0, 'quality_0': -0.17384904561086884, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 800, 'current_players': 1174, 'regular_players': 10740, 'joint_players': 236, 'quality_joint_players': 524, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Rooker has 365 AAA PA with 28 HR but only 36 MLB PA, including 29 preceding and zero late PA. The candidate lowers 164.46 to 155.04 PA against 526, contribution .413 to .389 against 2.982. That direction follows real declining MLB use, with a negative current late-PA path, but fails to anticipate his subsequent breakthrough. The unchanged batting estimate is also low. Hernandez, Aguilar and Martin do not return to MLB next year, while Batten gets 139, so the ordinary older upper-minor risk is real. There are 407 same broad absent-late/debut/age training people, not exact Rooker starting-job comparables. More precise past usage is not itself a future competition translation or job guarantee.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Elier Hernandez | 27.0 | 35 | 351 | 15.20 | 14.60 | 0 | 0.00000 |
| Ryan Aguilar | 27.0 | 26 | 364 | 0.00 | 0.00 | 0 | 0.00000 |
| Richie Martin Jr. | 27.0 | 33 | 334 | 60.60 | 63.38 | 0 | 0.00000 |
| Matthew Batten | 27.0 | 22 | 378 | 77.03 | 84.42 | 139 | 0.45753 |

## Albert Pujols 2021 to 2022

Player 405395, row 42072; fixed diagnostic; age 41.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | MLB | 545 | 131 | 23 | 68 | 42 |
| 2020 | MLB | 163 | 39 | 6 | 25 | 8 |
| 2021 | MLB | 296 | 109 | 17 | 45 | 11 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2020 | 163.0 | 69.0 | 76.0 | 25.46667 | 28.86667 |
| 2021 | 296.0 | 28.0 | 28.0 | 26.53333 | 27.26667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 28.0, 'late_usage_0_preceding_pa': 28.0, 'late_usage_0_late_pace': 1.0268948655256724, 'late_usage_0_preceding_pace': 1.0552763819095476, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 76.0, 'late_usage_1_preceding_pa': 69.0, 'late_usage_1_late_pace': 2.6327944572748265, 'late_usage_1_preceding_pace': 2.7094240837696337}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 52.7555 | -0.93123 | 0.083510 |
| late | 62.8528 | -0.93123 | 0.099493 |
| retired_safe_ridge | 43.1485 | -1.12375 | 0.054457 |
| Actual | 351 | 3.4063842632657733 | 3.091707 |

Candidate raw mean 62.852756, bounded/availability-adjusted mean 62.852756. Contribution = 62.852756 × (-0.931230/600 + 0.00313500). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.485376 plus all full-record path terms = raw PA 52.755530.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 296.12186084808565 | 204.629974 |
| on_40man | 0.0 | -101.404218 |
| role_mlb_0 | 2.823529411764706 | -63.373410 |
| age_centered | 2.8 | -30.467767 |
| regular_window_scaled | 0.6666666666666666 | 21.042623 |
| MLB_0_pa | 296.0 | -11.164290 |
| pooled_MLB_3B | 0.0005858917272088118 | -11.122953 |
| pooled_MLB_pa | 753.4 | 10.094140 |

### Late-role candidate: exact path accounting

Reference 39.494203 plus all full-record path terms = raw PA 62.852756.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 296.12186084808565 | 177.937381 |
| on_40man | 0.0 | -80.544594 |
| role_mlb_0 | 2.823529411764706 | -49.091363 |
| age_centered | 2.8 | -25.639725 |
| regular_window_scaled | 0.6666666666666666 | 17.167890 |
| late_usage_0_late_pa | 28.0 | -17.067556 |
| elapsed_scaled | 2.0 | -14.113967 |
| pooled_MLB_pa | 753.4 | 8.734424 |
| late_usage_1_late_pa | 76.0 | 7.919368 |
| late_usage_0_late_pace | 1.0268948655256724 | 2.156957 |
| late_usage_0_preceding_pace | 1.0552763819095476 | 1.323304 |
| late_usage_1_preceding_pa | 69.0 | -0.605158 |
| late_usage_0_preceding_pa | 28.0 | -0.167982 |

Old distinct-player profile: [{'row_id': 42072, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 8.0, 'current_work_band': 'partial', 'draft_known': 0, 'profile_players': 5}]. Late-stage/debut/age/exposure profile: [{'row_id': 42072, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 8.0, 'late_band': '1-49', 'late_profile_players': 9}]. Actual mature fold support: [{'row_id': 42072, 'horizon': 1, 'player_id': 405395, 'origin_year': 2021, 'elapsed': 20, 'current_state': 2, 'regular_window': 2, 'age': 41.0, 'quality_0': -0.12593132806633103, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 4, 'current_players': 570, 'regular_players': 372, 'joint_players': 286, 'quality_joint_players': 425, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False}].

Pujols has 296 PA and 17 HR in 2021, with 28 PA in each final window, versus 69/76 in shortened 2020. No retirement applies. Candidate PA increases 52.76 to 62.85 against 351 and contribution .0835 to .0995 against 3.092: a small improvement without solving his final-year surge. Current late PA still contributes negatively inside the candidate, while annual history and prior usage offset it; do not attribute the whole net increase to one path term. Only nine timing-profile and five old-profile training people support this age-40-plus partial-workload case. Cruz and Cabrera continue substantially; Molina and Suzuki have smaller roles. Old age or low late use is not retirement.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nelson Cruz | 40.0 | 584 | 0 | 310.02 | 314.25 | 507 | 0.83625 |
| Yadier Molina | 38.0 | 473 | 0 | 303.86 | 291.23 | 270 | -0.79611 |
| Miguel Cabrera | 38.0 | 526 | 0 | 302.95 | 295.82 | 433 | 0.15391 |
| Kurt Suzuki | 37.0 | 247 | 0 | 21.97 | 42.00 | 159 | -0.22900 |

## Dansby Swanson 2016 to 2017

Player 621020, row 24571; fixed diagnostic; age 22.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2015 | Aminus | 99 | 22 | 1 | 14 | 12 |
| 2016 | AA | 377 | 84 | 8 | 71 | 33 |
| 2016 | Aplus | 93 | 21 | 1 | 13 | 13 |
| 2016 | MLB | 145 | 38 | 3 | 34 | 8 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 145.0 | 51.0 | 94.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 94.0, 'late_usage_0_preceding_pa': 51.0, 'late_usage_0_late_pace': 3.3651551312649164, 'late_usage_0_preceding_pace': 1.8888888888888888, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 226.7206 | -0.37130 | 0.559831 |
| late | 273.5748 | -0.37130 | 0.675526 |
| retired_safe_ridge | 282.2756 | -0.37130 | 0.697010 |
| Actual | 551 | -2.3649172779607905 | -0.476809 |

Candidate raw mean 273.574751, bounded/availability-adjusted mean 273.574751. Contribution = 273.574751 × (-0.371302/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 226.720600.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| on_40man | 1.0 | 79.832011 |
| MLB_0_pa | 145.0 | 34.457339 |
| role_pool_AA | 4.4361702127659575 | 21.502884 |
| age_centered | -1.0 | 13.298664 |
| role_mlb_0 | 3.8541666666666665 | 12.557965 |
| quality_0 | 0.030552515736128192 | 10.645853 |
| pooled_MLB_BB | 0.0653061224489796 | 6.344317 |
| pooled_mlb_quality | 0.030552515736128192 | -6.231140 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 273.574751.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| late_usage_0_late_pa | 94.0 | 111.356216 |
| on_40man | 1.0 | 61.943255 |
| role_pool_AA | 4.4361702127659575 | 20.049944 |
| MLB_0_pa | 145.0 | 15.697489 |
| role_minor_0 | 4.434782608695652 | 10.598747 |
| role_pool_MLB | 3.8541666666666665 | -9.175990 |
| draft_rank | 1.0 | 6.911664 |
| pooled_AA_3B | 0.011530398322851153 | 6.101407 |
| late_usage_1_preceding_pa | 0.0 | -1.334579 |
| late_usage_0_preceding_pa | 51.0 | -0.162624 |
| late_usage_0_preceding_pace | 1.8888888888888888 | -0.066982 |
| late_usage_1_late_pa | 0.0 | -0.023438 |
| late_usage_1_preceding_pace | 0.0 | -0.004093 |

Old distinct-player profile: [{'row_id': 24571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Late-stage/debut/age/exposure profile: [{'row_id': 24571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'late_band': '50-99', 'late_profile_players': 108}]. Actual mature fold support: [{'row_id': 24571, 'horizon': 1, 'player_id': 621020, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.030552515736128192, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 69, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Swanson's 145 MLB debut PA contain 51 preceding and 94 late PA after 377 AA and 93 A-plus PA. The timing signal reflects a genuinely increasing job. Candidate PA rises 226.72 to 273.57 against 551, and current late PA is its largest positive path term. This is the intended mechanism, but contribution worsens .560 to .676 against actual negative -.477 because the fixed batting head is not poor enough. Almora, Bregman and Bell subsequently receive substantial PA while Dahl gets zero. The 108-person timing profile supports an ordinary young late debut, not deterministic regular status. A workload improvement must not be summarized as an unconditional player-value improvement for this person.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Albert Almora Jr. | 22.0 | 117 | 336 | 254.25 | 236.26 | 323 | 1.31527 |
| Alex Bregman | 22.0 | 217 | 368 | 445.74 | 442.75 | 626 | 3.58203 |
| Josh Bell | 23.0 | 152 | 484 | 221.71 | 262.39 | 620 | 2.87812 |
| David Dahl | 22.0 | 237 | 400 | 387.02 | 334.49 | 0 | 0.00000 |

## David Dahl 2016 to 2017

Player 621311, row 24584; fixed diagnostic; age 22.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 422 | 90 | 10 | 65 | 23 |
| 2014 | Aplus | 125 | 29 | 4 | 27 | 5 |
| 2015 | AA | 302 | 73 | 6 | 72 | 11 |
| 2015 | Aminus | 24 | 6 | 0 | 9 | 0 |
| 2016 | AA | 332 | 76 | 13 | 85 | 38 |
| 2016 | AAA | 68 | 16 | 5 | 11 | 5 |
| 2016 | MLB | 237 | 63 | 7 | 59 | 15 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2016 | 237.0 | 112.0 | 87.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 87.0, 'late_usage_0_preceding_pa': 112.0, 'late_usage_0_late_pace': 3.1145584725536994, 'late_usage_0_preceding_pace': 4.148148148148148, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 387.0174 | 0.68761 | 1.638675 |
| late | 334.4917 | 0.68761 | 1.416275 |
| retired_safe_ridge | 391.8919 | 0.68761 | 1.659314 |
| Actual | 0 | unobserved at zero PA | 0.000000 |

Candidate raw mean 334.491657, bounded/availability-adjusted mean 334.491657. Contribution = 334.491657 × (0.687612/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.639329 plus all full-record path terms = raw PA 387.017416.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 237.0 | 114.514300 |
| quality_0 | 0.4303166325984906 | 107.754857 |
| on_40man | 1.0 | 47.361371 |
| work_0 | 237.1952224052718 | 29.023403 |
| pooled_MLB_K | 0.2433234421364985 | -22.302570 |
| age_centered | -1.0 | 21.022397 |
| role_mlb_0 | 3.7945205479452055 | 19.349856 |
| pooled_AAA_BABIP | 0.3767123287671233 | -9.578688 |

### Late-role candidate: exact path accounting

Reference 39.650255 plus all full-record path terms = raw PA 334.491657.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| late_usage_0_late_pa | 87.0 | 95.730724 |
| quality_0 | 0.4303166325984906 | 78.432241 |
| MLB_0_pa | 237.0 | 76.606252 |
| on_40man | 1.0 | 40.067162 |
| work_0 | 237.1952224052718 | 34.113061 |
| age_centered | -1.0 | 20.534326 |
| pooled_AAA_HBP | 0.005952380952380952 | -14.842933 |
| pooled_MLB_K | 0.2433234421364985 | -13.414243 |
| late_usage_0_preceding_pa | 112.0 | -10.436219 |
| late_usage_0_preceding_pace | 4.148148148148148 | 0.759765 |
| late_usage_1_late_pa | 0.0 | -0.322697 |
| late_usage_1_preceding_pa | 0.0 | -0.156801 |
| late_usage_1_late_pace | 0.0 | -0.035926 |
| late_usage_0_late_pace | 3.1145584725536994 | 0.015953 |

Old distinct-player profile: [{'row_id': 24584, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'partial', 'draft_known': 1, 'profile_players': 52}]. Late-stage/debut/age/exposure profile: [{'row_id': 24584, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'late_band': '50-99', 'late_profile_players': 115}]. Actual mature fold support: [{'row_id': 24584, 'horizon': 1, 'player_id': 621311, 'origin_year': 2016, 'elapsed': 0, 'current_state': 2, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.4303166325984906, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 415, 'current_players': 367, 'regular_players': 6496, 'joint_players': 15, 'quality_joint_players': 61, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False}].

Dahl has 237 MLB PA after strong AA/AAA results, with 112 preceding and 87 late PA. Candidate workload falls 387.02 to 334.49 and contribution 1.639 to 1.416 against zero actual, improving the absence miss. His timing remains a large positive within-model term, but the full refit redistributes annual and quality terms; the total reduction is not a causal effect of declining use. Bregman, Peraza, Polanco and Swanson all actually continue with large workloads. Nothing in these PA counts diagnoses the later cause of Dahl's absence. It is reasonable to retain a substantial pre-season expectation while acknowledging this realized miss; lowered PA alone does not validate medical prediction.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Alex Bregman | 22.0 | 217 | 368 | 445.74 | 442.75 | 626 | 3.58203 |
| José Peraza | 22.0 | 256 | 322 | 380.10 | 383.12 | 518 | -0.45891 |
| Jorge Polanco | 22.0 | 270 | 325 | 460.91 | 464.71 | 544 | 1.08853 |
| Dansby Swanson | 22.0 | 145 | 470 | 226.72 | 273.57 | 551 | -0.47681 |

## Fernando Tatis Jr. 2022 to 2023

Player 665487, row 47261; fixed diagnostic; age 23.0, Upper minors.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 257 | 59 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 130 | 42 | 153 | 56 |
| 2022 | AA | 14 | 4 | 0 | 2 | 4 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2021 | 546.0 | 74.0 | 106.0 | 26.53333 | 27.26667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 106.0, 'late_usage_1_preceding_pa': 74.0, 'late_usage_1_late_pace': 3.8875305623471883, 'late_usage_1_preceding_pace': 2.78894472361809}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 140.1497 | 1.27950 | 0.737674 |
| late | 162.3736 | 1.27950 | 0.854649 |
| retired_safe_ridge | 150.1491 | 1.20289 | 0.771134 |
| Actual | 635 | 0.7268065858888001 | 2.735212 |

Candidate raw mean 162.373613, bounded/availability-adjusted mean 162.373613. Contribution = 162.373613 × (1.279500/600 + 0.00313097). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.199607 plus all full-record path terms = raw PA 140.149676.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.3673684989925885 | 35.265844 |
| age_centered | -0.8 | 27.615191 |
| regular_window_scaled | 0.6666666666666666 | 24.137649 |
| role_pool_MLB | 4.223560910307898 | 19.672920 |
| work_0 | 0.0 | -19.594744 |
| on_40man | 0.0 | -18.644224 |
| games_mlb_2 | 159.3 | 17.810031 |
| pooled_MLB_K | 0.2633863965267728 | -15.994417 |

### Late-role candidate: exact path accounting

Reference 38.196378 plus all full-record path terms = raw PA 162.373613.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| pooled_mlb_quality | 1.3673684989925885 | 38.595035 |
| age_centered | -0.8 | 32.987063 |
| regular_window_scaled | 0.6666666666666666 | 28.988997 |
| on_40man | 0.0 | -20.566651 |
| games_mlb_2 | 159.3 | 19.384804 |
| late_usage_1_late_pa | 106.0 | 19.149165 |
| work_0 | 0.0 | -16.851058 |
| pooled_MLB_K | 0.2633863965267728 | -14.886758 |
| late_usage_0_late_pa | 0.0 | -4.841051 |
| late_usage_0_preceding_pa | 0.0 | 3.157278 |
| late_usage_1_late_pace | 3.8875305623471883 | 2.537597 |
| late_usage_1_preceding_pa | 74.0 | -0.076955 |
| late_usage_0_late_pace | 0.0 | -0.017126 |

Old distinct-player profile: [{'row_id': 47261, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 0, 'profile_players': 26}]. Late-stage/debut/age/exposure profile: [{'row_id': 47261, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 4.0, 'late_band': 'absent', 'late_profile_players': 52}]. Actual mature fold support: [{'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 797, 'current_players': 10645, 'regular_players': 385, 'joint_players': 26, 'quality_joint_players': 812, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Tatis has 546 PA and 42 HR in 2021, but zero MLB PA in 2022 and only 14 AA PA. Prior-year late PA is 106, current-year zero. Candidate PA rises 140.15 to 162.37 against 635 and contribution .738 to .855 against 2.735; the earlier substantial late-role path is +19.15. The two-year input recovers a little career-role evidence, but neither remaining suspension nor return date is explicitly encoded. Broad timing support is 52 people; Apostel, Welker, Marchan and Jones are age/workload-selected peers, not comparably established former stars. The large finite-absence return gap remains, rather than being explained away by a correct source join.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sherten Apostel | 23.0 | 0 | 77 | 0.00 | 0.00 | 0 | 0.00000 |
| Colton Welker | 24.0 | 0 | 45 | 27.15 | 21.68 | 0 | 0.00000 |
| Rafael Marchán | 23.0 | 0 | 278 | 97.92 | 103.71 | 0 | 0.00000 |
| Jahmai Jones | 24.0 | 0 | 118 | 24.65 | 17.46 | 11 | -0.02098 |

## B.J. Upton 2016 to 2017

Player 425834, row 22813; pa largest gain; age 31.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | MLB | 582 | 141 | 12 | 173 | 52 |
| 2015 | AAA | 55 | 13 | 1 | 12 | 4 |
| 2015 | MLB | 228 | 87 | 5 | 62 | 19 |
| 2016 | MLB | 539 | 149 | 20 | 155 | 36 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2015 | 228.0 | 63.0 | 60.0 | 26.73333 | 27.93333 |
| 2016 | 539.0 | 97.0 | 50.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 50.0, 'late_usage_0_preceding_pa': 97.0, 'late_usage_0_late_pace': 1.7899761336515514, 'late_usage_0_preceding_pace': 3.5925925925925926, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 60.0, 'late_usage_1_preceding_pa': 63.0, 'late_usage_1_late_pace': 2.1479713603818618, 'late_usage_1_preceding_pace': 2.3566084788029924}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 373.3961 | -0.57650 | 0.794313 |
| late | 271.0731 | -0.57650 | 0.576645 |
| retired_safe_ridge | 411.5728 | -0.57650 | 0.875525 |
| Actual | 0 | unobserved at zero PA | 0.000000 |

Candidate raw mean 271.073128, bounded/availability-adjusted mean 271.073128. Contribution = 271.073128 × (-0.576496/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 373.396106.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 539.0 | 153.889342 |
| work_0 | 539.4439868204283 | 137.858945 |
| games_mlb_0 | 149.0 | 35.136177 |
| role_mlb_0 | 3.641509433962264 | -34.932023 |
| pooled_MLB_pa | 1070.6 | 30.176357 |
| quality_0 | -0.2985877279800739 | -21.293913 |
| on_40man | 1.0 | 21.028904 |
| regular_window_scaled | 0.6666666666666666 | 15.860918 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 271.073128.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 539.0 | 127.312178 |
| work_0 | 539.4439868204283 | 106.989077 |
| role_mlb_0 | 3.641509433962264 | -38.006327 |
| pooled_MLB_pa | 1070.6 | 31.913334 |
| on_40man | 1.0 | 30.158850 |
| late_usage_0_late_pa | 50.0 | -25.133135 |
| regular_window_scaled | 0.6666666666666666 | 20.853204 |
| late_usage_0_preceding_pa | 97.0 | -14.298116 |
| late_usage_0_preceding_pace | 3.5925925925925926 | 3.204494 |
| late_usage_1_late_pace | 2.1479713603818618 | -1.289016 |
| late_usage_1_late_pa | 60.0 | 1.099142 |
| late_usage_1_preceding_pa | 63.0 | -0.191703 |
| late_usage_1_preceding_pace | 2.3566084788029924 | -0.004093 |

Old distinct-player profile: [{'row_id': 22813, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 103}]. Late-stage/debut/age/exposure profile: [{'row_id': 22813, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'late_band': '50-99', 'late_profile_players': 114}]. Actual mature fold support: [{'row_id': 22813, 'horizon': 1, 'player_id': 425834, 'origin_year': 2016, 'elapsed': 12, 'current_state': 3, 'regular_window': 2, 'age': 31.0, 'quality_0': -0.2985877279800739, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 74, 'current_players': 304, 'regular_players': 217, 'joint_players': 149, 'quality_joint_players': 222, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Upton has 539 MLB PA and 20 HR in 2016, following 228 in 2015 and 582 in 2014. Within 2016, preceding PA is 97 but late PA only 50. Candidate PA falls 373.40 to 271.07 against zero, the largest workload improvement, and contribution .794 to .577 also improves. Late/preceding counts have negative within-fit terms despite a positive annual history. This is plausible diminished-role evidence, not a prediction of confirmed retirement or an automatic zero. Vogt, Garcia and Tulowitzki later have reduced but positive workload, while Valencia gets 500 PA. The new timing sample has 114 broad-profile people. Keep the residual false-positive expectation visible.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Stephen Vogt | 31.0 | 532 | 0 | 402.30 | 421.13 | 303 | 0.42034 |
| Adonis García | 31.0 | 563 | 80 | 387.21 | 417.56 | 183 | -0.18719 |
| Troy Tulowitzki | 31.0 | 544 | 4 | 523.88 | 548.20 | 260 | 0.22244 |
| Danny Valencia | 31.0 | 517 | 7 | 464.66 | 484.90 | 500 | 1.24733 |

## Logan Morrison 2016 to 2017

Player 489149, row 23215; pa largest harm; age 28.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | AAA | 77 | 18 | 3 | 8 | 10 |
| 2014 | MLB | 365 | 99 | 11 | 59 | 23 |
| 2015 | MLB | 511 | 146 | 17 | 81 | 42 |
| 2016 | Aplus | 15 | 4 | 0 | 0 | 2 |
| 2016 | MLB | 398 | 107 | 14 | 89 | 36 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2015 | 511.0 | 57.0 | 66.0 | 26.73333 | 27.93333 |
| 2016 | 398.0 | 44.0 | 25.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 25.0, 'late_usage_0_preceding_pa': 44.0, 'late_usage_0_late_pace': 0.8949880668257757, 'late_usage_0_preceding_pace': 1.6296296296296295, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 66.0, 'late_usage_1_preceding_pa': 57.0, 'late_usage_1_late_pace': 2.3627684964200477, 'late_usage_1_preceding_pace': 2.1321695760598502}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 277.1830 | 0.05380 | 0.880821 |
| late | 212.0564 | 0.05380 | 0.673865 |
| retired_safe_ridge | 289.5689 | 0.05380 | 0.920181 |
| Actual | 601 | 2.038170731694412 | 3.890349 |

Candidate raw mean 212.056389, bounded/availability-adjusted mean 212.056389. Contribution = 212.056389 × (0.053802/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 277.182994.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 398.0 | 134.448759 |
| work_0 | 398.32784184514003 | 131.753524 |
| on_40man | 0.0 | -72.872721 |
| games_mlb_1 | 146.0 | 19.251691 |
| role_mlb_0 | 3.7435897435897436 | -19.237968 |
| pooled_MLB_pa | 1025.8 | 18.620986 |
| age_centered | 0.2 | 18.159902 |
| regular_window_scaled | 0.3333333333333333 | 15.860918 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 212.056389.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 398.0 | 116.723241 |
| work_0 | 398.32784184514003 | 105.896212 |
| on_40man | 0.0 | -73.492351 |
| pooled_MLB_pa | 1025.8 | 31.049965 |
| late_usage_0_late_pa | 25.0 | -25.521355 |
| role_mlb_0 | 3.7435897435897436 | -24.562296 |
| age_centered | 0.2 | 15.748235 |
| regular_window_scaled | 0.3333333333333333 | 12.625421 |
| late_usage_1_preceding_pa | 57.0 | -1.350196 |
| late_usage_0_preceding_pace | 1.6296296296296295 | -0.066982 |
| late_usage_0_preceding_pa | 44.0 | 0.064402 |
| late_usage_1_late_pa | 66.0 | -0.014996 |
| late_usage_1_preceding_pace | 2.1321695760598502 | -0.013987 |

Old distinct-player profile: [{'row_id': 23215, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': 'partial', 'draft_known': 0, 'profile_players': 106}]. Late-stage/debut/age/exposure profile: [{'row_id': 23215, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': '1-49', 'late_profile_players': 313}]. Actual mature fold support: [{'row_id': 23215, 'horizon': 1, 'player_id': 489149, 'origin_year': 2016, 'elapsed': 6, 'current_state': 2, 'regular_window': 1, 'age': 28.0, 'quality_0': 0.027122014088184175, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 226, 'current_players': 376, 'regular_players': 274, 'joint_players': 92, 'quality_joint_players': 251, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Morrison has 398 MLB PA and 14 HR in 2016 after 511 PA in 2015, plus a 15-PA A-plus stint. The last windows are 44 preceding and 25 late PA. Candidate PA falls 277.18 to 212.06 against 601, the largest workload harm; contribution falls .881 to .674 against 3.890. Current late PA has a -25.52 within-fit path, alongside a large negative imperfect roster-membership term. Both are origin input signals, not evidence he could not regain a job. Nieuwenhuis and Giavotella subsequently get almost no PA, Solarte gets 512 and Kim 239, so reduced recent use mixes lost jobs with recoverable situations. The broad 313-person timing support does not certify a cause-specific return forecast. This is a consequential counterexample to a blanket late-role penalty.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kirk Nieuwenhuis | 28.0 | 392 | 0 | 259.28 | 221.17 | 31 | -0.09461 |
| Johnny Giavotella | 28.0 | 367 | 30 | 225.02 | 198.97 | 10 | -0.16231 |
| Yangervis Solarte | 28.0 | 443 | 9 | 502.39 | 494.33 | 512 | 1.20229 |
| Hyun Soo Kim | 28.0 | 346 | 7 | 371.29 | 355.21 | 239 | -0.30255 |

## Rhys Hoskins 2022 to 2023

Player 656555, row 46991; pa false high; age 29.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 185 | 41 | 10 | 43 | 29 |
| 2021 | MLB | 443 | 107 | 27 | 108 | 47 |
| 2022 | MLB | 672 | 156 | 30 | 169 | 72 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2021 | 443.0 | 14.0 | 0.0 | 26.53333 | 27.26667 |
| 2022 | 672.0 | 119.0 | 104.0 | 26.73333 | 27.60000 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 104.0, 'late_usage_0_preceding_pa': 119.0, 'late_usage_0_late_pace': 3.7681159420289854, 'late_usage_0_preceding_pace': 4.451371571072319, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 14.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.5276381909547738}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 543.0676 | 1.57308 | 3.124147 |
| late | 554.8107 | 1.57308 | 3.191702 |
| retired_safe_ridge | 533.5826 | 1.50238 | 3.006706 |
| Actual | 0 | unobserved at zero PA | 0.000000 |

Candidate raw mean 554.810724, bounded/availability-adjusted mean 554.810724. Contribution = 554.810724 × (1.573082/600 + 0.00313097). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.773582 plus all full-record path terms = raw PA 543.067624.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 672.0 | 307.118223 |
| role_mlb_0 | 4.289156626506024 | 44.018721 |
| quality_0 | 0.6375899566656552 | 36.312907 |
| pooled_mlb_quality | 1.0618680306599833 | 34.355563 |
| regular_window_scaled | 1.0 | 24.057615 |
| MLB_0_pa | 672.0 | 21.998047 |
| pooled_MLB_K | 0.2458380475189914 | -19.870191 |
| role_pool_MLB | 4.2628530050687905 | 15.958934 |

### Late-role candidate: exact path accounting

Reference 38.773074 plus all full-record path terms = raw PA 554.810724.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 672.0 | 231.270755 |
| late_usage_0_late_pa | 104.0 | 89.537116 |
| quality_0 | 0.6375899566656552 | 40.239108 |
| role_mlb_0 | 4.289156626506024 | 33.861973 |
| regular_window_scaled | 1.0 | 29.166793 |
| MLB_0_pa | 672.0 | 18.149795 |
| role_pool_MLB | 4.2628530050687905 | 13.589109 |
| pooled_MLB_pa | 1137.4 | 10.606313 |
| late_usage_0_preceding_pa | 119.0 | 9.297176 |
| late_usage_0_late_pace | 3.7681159420289854 | 1.872139 |
| late_usage_0_preceding_pace | 4.451371571072319 | 0.344656 |
| late_usage_1_preceding_pa | 14.0 | -0.285163 |
| late_usage_1_late_pa | 0.0 | -0.048019 |

Old distinct-player profile: [{'row_id': 46991, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 171}]. Late-stage/debut/age/exposure profile: [{'row_id': 46991, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': '100plus', 'late_profile_players': 236}]. Actual mature fold support: [{'row_id': 46991, 'horizon': 1, 'player_id': 656555, 'origin_year': 2022, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 29.0, 'quality_0': 0.6375899566656552, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 723, 'current_players': 455, 'regular_players': 275, 'joint_players': 260, 'quality_joint_players': 369, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Hoskins has 672 PA with 30 HR in 2022, including 119 preceding and 104 late PA, after 443 PA in 2021. Current sustained opportunity reasonably supports an active forecast. The candidate raises 543.07 to 554.81 expected PA and contribution 3.124 to 3.192 against zero, becoming the largest PA false high. The added late-PA term is positive and no future health event is in this model. Schwarber, Nimmo, Ramirez and Bell all subsequently have substantial PA, making a roughly regular-role mean plausible at this origin even though it misses badly. This does not prove avoidable injury prediction or calibrated downside risk; it remains an important realized error.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kyle Schwarber | 29.0 | 669 | 0 | 568.00 | 563.97 | 720 | 4.08771 |
| Brandon Nimmo | 29.0 | 673 | 0 | 592.33 | 591.16 | 682 | 4.47591 |
| José Ramírez | 29.0 | 685 | 0 | 604.91 | 627.23 | 691 | 3.18422 |
| Josh Bell | 29.0 | 647 | 0 | 582.61 | 568.72 | 617 | 2.11561 |

## Cody Bellinger 2016 to 2017

Player 641355, row 24967; pa false low; age 20.0, Upper minors.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 51 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 128 | 30 | 150 | 51 |
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| Certified no own MLB PA within captured years | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 0.0, 'late_usage_0_preceding_pa': 0.0, 'late_usage_0_late_pace': 0.0, 'late_usage_0_preceding_pace': 0.0, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 0.0, 'late_usage_1_preceding_pa': 0.0, 'late_usage_1_late_pace': 0.0, 'late_usage_1_preceding_pace': 0.0}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 7.7613 | 0.08471 | 0.025064 |
| late | 9.7559 | 0.08471 | 0.031505 |
| retired_safe_ridge | 35.5162 | 0.08471 | 0.114692 |
| Actual | 548 | 2.700470664969068 | 4.152174 |

Candidate raw mean 9.755928, bounded/availability-adjusted mean 9.755928. Contribution = 9.755928 × (0.084712/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 7.761347.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -12.271751 |
| work_0 | 0.0 | -9.937320 |
| on_40man | 0.0 | -6.100592 |
| pooled_AA_HR | 0.04601769911504425 | 4.731895 |
| pooled_Aplus_K | 0.26718983557548576 | 2.960506 |
| pooled_Aplus_HR | 0.050448430493273536 | 2.615448 |
| role_pool_AAA | 4.0 | -2.265421 |
| quality_0 | 0.0 | -2.147850 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 9.755928.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -10.031991 |
| work_0 | 0.0 | -8.084785 |
| on_40man | 0.0 | -5.737251 |
| pooled_AA_HR | 0.04601769911504425 | 5.542193 |
| pooled_Aplus_K | 0.26718983557548576 | 5.012176 |
| late_usage_0_late_pa | 0.0 | -4.743360 |
| role_pool_AAA | 4.0 | -3.011315 |
| pooled_Aplus_HR | 0.050448430493273536 | 2.884820 |
| late_usage_1_preceding_pa | 0.0 | -0.253929 |
| late_usage_0_preceding_pace | 0.0 | -0.066982 |
| late_usage_1_preceding_pace | 0.0 | -0.048040 |
| late_usage_1_late_pa | 0.0 | -0.031862 |
| late_usage_0_preceding_pa | 0.0 | 0.010235 |

Old distinct-player profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 744}]. Late-stage/debut/age/exposure profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'late_band': 'absent', 'late_profile_players': 1065}]. Actual mature fold support: [{'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Bellinger has 465 AA PA with 23 HR and just 12 AAA PA with three HR, after 544 A-plus PA and 30 HR the year before. He has no MLB timing record yet. Candidate PA rises only 7.76 to 9.76 against 548 and contribution .0251 to .0315 against 4.152, the largest PA false low. The new absent-MLB timing term is negative, while AA power and young age cannot overcome the low entry prior and absent roster flag. Rijo does not arrive, Barreto gets 76, Rosario 170 and Verdugo 25 under the ordinary origin comparison. Their results do not make Bellinger's clear AA power meaningless, nor supply an actual scouting-quality match. This is another missing readiness/pedigree discrimination issue that MLB usage timing cannot directly solve.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wendell Rijo | 20.0 | 0 | 441 | 0.37 | 0.00 | 0 | 0.00000 |
| Franklin Barreto | 20.0 | 0 | 525 | 96.31 | 88.38 | 76 | -0.14223 |
| Amed Rosario | 20.0 | 0 | 527 | 112.67 | 120.58 | 170 | 0.02193 |
| Alex Verdugo | 20.0 | 0 | 529 | 38.52 | 39.41 | 25 | -0.08615 |

## Salvador Perez 2016 to 2017

Player 521692, row 23473; pa ordinary; age 26.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | MLB | 606 | 150 | 17 | 85 | 20 |
| 2015 | MLB | 553 | 142 | 21 | 82 | 9 |
| 2016 | MLB | 546 | 139 | 22 | 119 | 19 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2015 | 553.0 | 84.0 | 95.0 | 26.73333 | 27.93333 |
| 2016 | 546.0 | 96.0 | 80.0 | 27.00000 | 27.93333 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 80.0, 'late_usage_0_preceding_pa': 96.0, 'late_usage_0_late_pace': 2.863961813842482, 'late_usage_0_preceding_pace': 3.5555555555555554, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 95.0, 'late_usage_1_preceding_pa': 84.0, 'late_usage_1_late_pace': 3.4009546539379474, 'late_usage_1_preceding_pace': 3.1421446384039897}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 520.6660 | -0.15574 | 1.472718 |
| late | 498.9999 | -0.15574 | 1.411435 |
| retired_safe_ridge | 494.2910 | -0.15574 | 1.398116 |
| Actual | 499 | 0.44624554633157776 | 1.906139 |

Candidate raw mean 498.999898, bounded/availability-adjusted mean 498.999898. Contribution = 498.999898 × (-0.155738/600 + 0.00308809). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.357092 plus all full-record path terms = raw PA 520.665983.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 546.0 | 153.072737 |
| work_0 | 546.4497528830312 | 137.858945 |
| pooled_MLB_pa | 1352.0 | 27.919301 |
| games_mlb_2 | 150.0 | 27.530247 |
| role_mlb_0 | 3.9328859060402683 | 27.159088 |
| games_mlb_0 | 139.0 | 23.970820 |
| quality_0 | -0.14380183590430334 | -17.269135 |
| regular_window_scaled | 1.0 | 15.860918 |

### Late-role candidate: exact path accounting

Reference 38.363379 plus all full-record path terms = raw PA 498.999898.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 546.0 | 124.540046 |
| work_0 | 546.4497528830312 | 106.989077 |
| late_usage_0_late_pa | 80.0 | 64.031271 |
| games_mlb_2 | 150.0 | 30.722014 |
| pooled_MLB_pa | 1352.0 | 30.013280 |
| role_mlb_0 | 3.9328859060402683 | 28.650042 |
| quality_0 | -0.14380183590430334 | -18.225846 |
| age_centered | -0.2 | 13.060926 |
| late_usage_0_preceding_pa | 96.0 | -2.330023 |
| late_usage_0_preceding_pace | 3.5555555555555554 | -1.820637 |
| late_usage_1_preceding_pa | 84.0 | 1.417463 |
| late_usage_0_late_pace | 2.863961813842482 | -0.335605 |
| late_usage_1_preceding_pace | 3.1421446384039897 | -0.004093 |

Old distinct-player profile: [{'row_id': 23473, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 106}]. Late-stage/debut/age/exposure profile: [{'row_id': 23473, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': '50-99', 'late_profile_players': 207}]. Actual mature fold support: [{'row_id': 23473, 'horizon': 1, 'player_id': 521692, 'origin_year': 2016, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 26.0, 'quality_0': -0.14380183590430334, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 323, 'current_players': 304, 'regular_players': 161, 'joint_players': 118, 'quality_joint_players': 222, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Perez has 606/553/546 annual MLB PA, with 96 preceding and 80 late PA in 2016. Candidate PA falls 520.67 to 499.00 against 499, an excellent workload result. Contribution falls 1.473 to 1.411 against 1.906, so the unchanged batting forecast makes whole value worse. Late PA remains a positive fitted path and the annual/role terms are redistributed; do not call a +64 late-path term a negative net effect. Gennett, Shaw, Iglesias and Gregorius all continue but with varied batting output and PA. There are 207 timing-profile training people, not a catcher-only health or defense validation. This ordinary case reinforces that PA and hitting targets must be inspected separately.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Scooter Gennett | 26.0 | 542 | 7 | 429.04 | 426.77 | 497 | 3.55321 |
| Travis Shaw | 26.0 | 530 | 0 | 365.28 | 351.97 | 606 | 3.86122 |
| Jose Iglesias | 26.0 | 513 | 16 | 291.83 | 347.69 | 489 | 0.03116 |
| Didi Gregorius | 26.0 | 597 | 0 | 510.29 | 507.61 | 570 | 2.52377 |

## Aaron Judge 2023 to 2024

Player 592450, row 50698; value largest gain; age 31.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | MLB | 633 | 148 | 39 | 158 | 73 |
| 2022 | MLB | 696 | 157 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 106 | 37 | 130 | 79 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2022 | 696.0 | 118.0 | 119.0 | 26.73333 | 27.60000 |
| 2023 | 458.0 | 113.0 | 111.0 | 26.46667 | 27.06667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 111.0, 'late_usage_0_preceding_pa': 113.0, 'late_usage_0_late_pace': 4.100985221674877, 'late_usage_0_preceding_pace': 4.269521410579346, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 119.0, 'late_usage_1_preceding_pa': 118.0, 'late_usage_1_late_pace': 4.311594202898551, 'late_usage_1_preceding_pace': 4.413965087281795}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 532.3853 | 3.39964 | 4.664834 |
| late | 569.4593 | 3.39964 | 4.989681 |
| retired_safe_ridge | 552.2933 | 3.37269 | 4.814467 |
| Actual | 704 | 7.557649414891916 | 11.066146 |

Candidate raw mean 569.459289, bounded/availability-adjusted mean 569.459289. Contribution = 569.459289 × (3.399637/600 + 0.00309608). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.977363 plus all full-record path terms = raw PA 532.385334.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 458.0 | 281.369195 |
| quality_0 | 1.3171302607418005 | 59.995703 |
| role_mlb_0 | 4.293103448275862 | 39.975580 |
| role_pool_MLB | 4.342009685230024 | 24.912992 |
| pooled_mlb_quality | 2.791561646517844 | 24.814333 |
| work_1 | 696.0 | 20.500409 |
| pooled_MLB_K | 0.25946741603104506 | -16.454581 |
| games_mlb_2 | 148.0 | 12.460655 |

### Late-role candidate: exact path accounting

Reference 38.980142 plus all full-record path terms = raw PA 569.459289.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 458.0 | 221.489227 |
| late_usage_0_late_pa | 111.0 | 105.246376 |
| quality_0 | 1.3171302607418005 | 45.904232 |
| role_mlb_0 | 4.293103448275862 | 24.876148 |
| games_mlb_2 | 148.0 | 20.967579 |
| role_pool_MLB | 4.342009685230024 | 19.076064 |
| pooled_mlb_quality | 2.791561646517844 | 14.353013 |
| regular_window_scaled | 1.0 | 14.045512 |
| late_usage_1_late_pa | 119.0 | 13.013754 |
| late_usage_0_late_pace | 4.100985221674877 | 9.498291 |
| late_usage_1_late_pace | 4.311594202898551 | 7.056412 |
| late_usage_0_preceding_pace | 4.269521410579346 | 6.949290 |
| late_usage_1_preceding_pace | 4.413965087281795 | 4.730456 |
| late_usage_0_preceding_pa | 113.0 | -3.599001 |
| late_usage_1_preceding_pa | 118.0 | -1.092804 |

Old distinct-player profile: [{'row_id': 50698, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 70}]. Late-stage/debut/age/exposure profile: [{'row_id': 50698, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'late_band': '100plus', 'late_profile_players': 129}]. Actual mature fold support: [{'row_id': 50698, 'horizon': 1, 'player_id': 592450, 'origin_year': 2023, 'elapsed': 7, 'current_state': 3, 'regular_window': 3, 'age': 31.0, 'quality_0': 1.3171302607418005, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 464, 'current_players': 500, 'regular_players': 288, 'joint_players': 277, 'quality_joint_players': 78, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Judge's current 458 annual PA include 113 preceding and 111 late PA; the prior year has 696 total with 118/119 in the windows. This is a player with strong late opportunity despite a reduced annual total. Candidate PA rises 532.39 to 569.46 against 704 and contribution 4.665 to 4.990 against 11.066, the largest contribution improvement. Late PA is a prominent positive fitted term, consistent with the intended timing mechanism, but the fixed 3.400 batting-wins/600 head still misses extraordinary hitting. Flores, Contreras, Grichuk and Trout all have lower actual next workload, so those nearby partial-year comparators do not guarantee Judge's return. The 129-person timing support is broad, not a recovered-superstar stratum.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Wilmer Flores | 31.0 | 454 | 0 | 390.25 | 391.13 | 242 | -0.18421 |
| Willson Contreras | 31.0 | 495 | 0 | 433.66 | 434.17 | 358 | 2.89664 |
| Randal Grichuk | 31.0 | 471 | 36 | 343.78 | 357.76 | 279 | 2.34830 |
| Mike Trout | 31.0 | 362 | 0 | 417.09 | 404.05 | 126 | 0.94104 |

## Cody Bellinger 2018 to 2019

Player 641355, row 33345; value largest harm; age 22.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |
| 2017 | AAA | 77 | 18 | 5 | 22 | 8 |
| 2017 | MLB | 548 | 132 | 39 | 146 | 51 |
| 2017 | RK121 | 4 | 1 | 1 | 1 | 0 |
| 2018 | MLB | 632 | 162 | 25 | 151 | 60 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2017 | 548.0 | 69.0 | 116.0 | 27.40000 | 27.73333 |
| 2018 | 632.0 | 97.0 | 90.0 | 27.06667 | 26.20000 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 90.0, 'late_usage_0_preceding_pa': 97.0, 'late_usage_0_late_pace': 3.435114503816794, 'late_usage_0_preceding_pace': 3.583743842364532, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 116.0, 'late_usage_1_preceding_pa': 69.0, 'late_usage_1_late_pace': 4.1826923076923075, 'late_usage_1_preceding_pace': 2.5182481751824817}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 533.5256 | 2.15788 | 3.561412 |
| late | 500.2780 | 2.15788 | 3.339477 |
| retired_safe_ridge | 607.7787 | 2.15788 | 4.057070 |
| Actual | 661 | 4.311240130418111 | 6.768749 |

Candidate raw mean 500.278003, bounded/availability-adjusted mean 500.278003. Contribution = 500.278003 × (2.157885/600 + 0.00307877). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 38.330428 plus all full-record path terms = raw PA 533.525578.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 632.0 | 213.989160 |
| work_0 | 631.7400246812011 | 110.035516 |
| quality_0 | 0.48801679633942663 | 59.704991 |
| pooled_MLB_pa | 1070.4 | 26.973838 |
| role_mlb_0 | 3.9069767441860463 | 25.313719 |
| age_centered | -1.0 | 23.044293 |
| pooled_MLB_K | 0.24846206425153794 | -12.894827 |
| pooled_AAA_BABIP | 0.33771929824561403 | 9.933308 |

### Late-role candidate: exact path accounting

Reference 38.328402 plus all full-record path terms = raw PA 500.278003.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| MLB_0_pa | 632.0 | 153.890624 |
| work_0 | 631.7400246812011 | 95.227241 |
| late_usage_0_late_pa | 90.0 | 82.655131 |
| quality_0 | 0.48801679633942663 | 48.655729 |
| role_mlb_0 | 3.9069767441860463 | 29.789961 |
| pooled_MLB_pa | 1070.4 | 20.276656 |
| age_centered | -1.0 | 18.887705 |
| role_pool_MLB | 4.0 | -12.427983 |
| late_usage_0_preceding_pa | 97.0 | -8.135261 |
| late_usage_1_preceding_pa | 69.0 | 2.502001 |
| late_usage_1_late_pa | 116.0 | -2.398836 |
| late_usage_1_preceding_pace | 2.5182481751824817 | 0.449240 |
| late_usage_0_preceding_pace | 3.583743842364532 | -0.062652 |
| late_usage_0_late_pace | 3.435114503816794 | -0.011617 |

Old distinct-player profile: [{'row_id': 33345, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 59}]. Late-stage/debut/age/exposure profile: [{'row_id': 33345, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'late_band': '50-99', 'late_profile_players': 147}]. Actual mature fold support: [{'row_id': 33345, 'horizon': 1, 'player_id': 641355, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 2, 'age': 22.0, 'quality_0': 0.48801679633942663, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 576, 'current_players': 363, 'regular_players': 280, 'joint_players': 26, 'quality_joint_players': 161, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Established Bellinger has 632 MLB PA and 25 HR in 2018 after 548 and 39 in 2017. His preceding/late PA are 97/90 versus prior 69/116. Candidate PA falls 533.53 to 500.28 against 661 and contribution 3.561 to 3.339 against 6.769, the largest contribution harm. Both models retain a positive 2.158 batting-wins/600 estimate. The fitted current late term is positive but does not offset lower redistributed annual/other terms; no single-feature causal claim explains the net fall. Rosario continues strongly, Andujar barely plays, Benintendi stays regular and Moncada gets 559 PA. The 147-person broad timing profile does not identify which young regular will break out. Record the missed upside instead of hiding it behind aggregate gain.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Amed Rosario | 22.0 | 592 | 0 | 494.82 | 507.93 | 655 | 1.94130 |
| Miguel Andujar | 23.0 | 606 | 0 | 568.35 | 600.50 | 49 | -0.67058 |
| Andrew Benintendi | 23.0 | 661 | 0 | 641.09 | 618.95 | 615 | 2.39410 |
| Yoán Moncada | 23.0 | 650 | 0 | 513.69 | 496.09 | 559 | 4.57716 |

## Yordan Alvarez 2024 to 2025

Player 670541, row 55521; value false high; age 27.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2023 | 496.0 | 115.0 | 114.0 | 26.46667 | 27.06667 |
| 2024 | 635.0 | 106.0 | 87.0 | 27.20000 | 25.66667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 87.0, 'late_usage_0_preceding_pa': 106.0, 'late_usage_0_late_pace': 3.3896103896103895, 'late_usage_0_preceding_pace': 3.8970588235294117, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 114.0, 'late_usage_1_preceding_pa': 115.0, 'late_usage_1_late_pace': 4.211822660098522, 'late_usage_1_preceding_pace': 4.345088161209068}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 577.4905 | 3.70970 | 5.374704 |
| late | 567.6722 | 3.70970 | 5.283325 |
| retired_safe_ridge | 601.3075 | 3.76103 | 5.647804 |
| Actual | 199 | 0.919648372891386 | 0.925104 |

Candidate raw mean 567.672221, bounded/availability-adjusted mean 567.672221. Contribution = 567.672221 × (3.709704/600 + 0.00312416). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.289435 plus all full-record path terms = raw PA 577.490453.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 635.2614244545081 | 322.222292 |
| role_mlb_0 | 4.2993630573248405 | 57.464999 |
| quality_0 | 1.415653196303136 | 52.228185 |
| pooled_mlb_quality | 2.457088938891907 | 23.983220 |
| role_pool_MLB | 4.278250303766707 | 18.921383 |
| quality_1 | 1.3830873087907403 | 15.954412 |
| regular_window_scaled | 1.0 | 13.701698 |
| MLB_0_pa | 635.0 | 12.903590 |

### Late-role candidate: exact path accounting

Reference 39.291975 plus all full-record path terms = raw PA 567.672221.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 635.2614244545081 | 241.835232 |
| late_usage_0_late_pa | 87.0 | 82.510445 |
| role_mlb_0 | 4.2993630573248405 | 46.964371 |
| quality_0 | 1.415653196303136 | 45.049969 |
| regular_window_scaled | 1.0 | 17.832653 |
| pooled_MLB_HR | 0.05788613456823753 | 12.870831 |
| late_usage_0_preceding_pace | 3.8970588235294117 | 12.320388 |
| quality_1 | 1.3830873087907403 | 10.659359 |
| late_usage_0_late_pace | 3.3896103896103895 | 9.313401 |
| late_usage_1_late_pa | 114.0 | 8.002033 |
| late_usage_1_preceding_pa | 115.0 | 7.587064 |
| late_usage_1_late_pace | 4.211822660098522 | 1.442043 |
| late_usage_0_preceding_pa | 106.0 | 0.462217 |

Old distinct-player profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 173}]. Late-stage/debut/age/exposure profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': '50-99', 'late_profile_players': 492}]. Actual mature fold support: [{'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 903, 'current_players': 538, 'regular_players': 310, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Alvarez has 635 annual PA and 35 HR in 2024, after 561/496 PA. Current preceding/late PA are 106/87, versus 115/114 in 2023. Candidate PA falls 577.49 to 567.67 and contribution 5.375 to 5.283 against 199 and .925 actual, a small improvement that leaves the largest contribution false high. His sustained historical role and strong unchanged hitting rate are plausible origin evidence. Devers, India, Donovan and Bohm all subsequently have much more workload than Alvarez, so this group is not uniformly fragile. No specific later diagnosis or medical outcome is supplied. The 492-person timing profile is broad; this case requires honest health uncertainty, not hindsight zeroing.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rafael Devers | 27.0 | 601 | 0 | 566.99 | 571.25 | 729 | 5.23429 |
| Jonathan India | 27.0 | 637 | 0 | 545.44 | 523.68 | 567 | 1.28649 |
| Brendan Donovan | 27.0 | 652 | 0 | 570.90 | 564.27 | 515 | 2.59344 |
| Alec Bohm | 27.0 | 606 | 4 | 590.93 | 562.75 | 504 | 2.05959 |

## Jake Fraley 2023 to 2024

Player 641584, row 50949; value ordinary; age 28.0, Current MLB.

| Season | Level | PA | Source games | HR | K | BB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AAA | 51 | 13 | 3 | 15 | 9 |
| 2021 | MLB | 265 | 78 | 9 | 71 | 45 |
| 2022 | AAA | 48 | 12 | 1 | 14 | 7 |
| 2022 | Aplus | 3 | 1 | 0 | 0 | 1 |
| 2022 | MLB | 247 | 68 | 12 | 54 | 25 |
| 2023 | AAA | 8 | 2 | 0 | 1 | 0 |
| 2023 | MLB | 380 | 111 | 15 | 71 | 35 |

| Season | Annual MLB PA | Preceding window PA | Late window PA | Preceding average team games | Late average team games |
|---|---:|---:|---:|---:|---:|
| 2022 | 247.0 | 98.0 | 88.0 | 26.73333 | 27.60000 |
| 2023 | 380.0 | 9.0 | 48.0 | 26.46667 | 27.06667 |

Actual added inputs: {'late_usage_0_available': 1.0, 'late_usage_0_late_pa': 48.0, 'late_usage_0_preceding_pa': 9.0, 'late_usage_0_late_pace': 1.7733990147783252, 'late_usage_0_preceding_pace': 0.3400503778337532, 'late_usage_1_available': 1.0, 'late_usage_1_late_pa': 88.0, 'late_usage_1_preceding_pa': 98.0, 'late_usage_1_late_pace': 3.1884057971014492, 'late_usage_1_preceding_pace': 3.6658354114713214}.

| Forecast | PA | Unchanged batting wins/600 | Contribution |
|---|---:|---:|---:|
| retired_games | 359.4118 | 0.57412 | 1.456674 |
| late | 343.5468 | 0.57412 | 1.392375 |
| retired_safe_ridge | 376.1573 | 0.63284 | 1.561360 |
| Actual | 382 | 0.3126179605850409 | 1.391972 |

Candidate raw mean 343.546821, bounded/availability-adjusted mean 343.546821. Contribution = 343.546821 × (0.574118/600 + 0.00309608). Old working rate differs from the fixed V34/V38 rate and is shown as a separate complete assembly, not silently mixed.

### Games control: exact path accounting

Reference 39.118145 plus all full-record path terms = raw PA 359.411766.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 380.0 | 263.217063 |
| quality_0 | 0.24069267645248177 | 58.622412 |
| role_mlb_0 | 3.4710743801652892 | -55.870542 |
| pooled_mlb_quality | 0.44176004579608247 | 31.117004 |
| on_40man | 1.0 | 24.484623 |
| pooled_MLB_K | 0.21491752330863018 | 7.943258 |
| role_pool_MLB | 3.4950495049504955 | -6.463722 |
| age_centered | 0.2 | 5.413154 |

### Late-role candidate: exact path accounting

Reference 39.122601 plus all full-record path terms = raw PA 343.546821.

| Input | Actual encoded value | Path PA accounting |
|---|---:|---:|
| work_0 | 380.0 | 217.043946 |
| quality_0 | 0.24069267645248177 | 60.139348 |
| role_mlb_0 | 3.4710743801652892 | -52.280668 |
| pooled_mlb_quality | 0.44176004579608247 | 31.618716 |
| on_40man | 1.0 | 24.708394 |
| pooled_MLB_K | 0.21491752330863018 | 8.026695 |
| late_usage_1_late_pa | 88.0 | 5.570475 |
| late_usage_0_late_pa | 48.0 | 5.461841 |
| late_usage_1_preceding_pa | 98.0 | 4.214635 |
| late_usage_1_late_pace | 3.1884057971014492 | -0.618583 |
| late_usage_0_late_pace | 1.7733990147783252 | -0.309561 |
| late_usage_1_preceding_pace | 3.6658354114713214 | -0.023379 |
| late_usage_0_preceding_pa | 9.0 | 0.004361 |

Old distinct-player profile: [{'row_id': 50949, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': 'partial', 'draft_known': 1, 'profile_players': 254}]. Late-stage/debut/age/exposure profile: [{'row_id': 50949, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'late_band': '1-49', 'late_profile_players': 643}]. Actual mature fold support: [{'row_id': 50949, 'horizon': 1, 'player_id': 641584, 'origin_year': 2023, 'elapsed': 4, 'current_state': 2, 'regular_window': 0, 'age': 28.0, 'quality_0': 0.24069267645248177, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 838, 'current_players': 707, 'regular_players': 11213, 'joint_players': 218, 'quality_joint_players': 512, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True}].

Fraley has 380 MLB PA and 15 HR in 2023, after 265 and 247 in the prior seasons. Current windows contain nine preceding and 48 late PA; prior windows contain 98/88. Candidate PA falls 359.41 to 343.55 against 382 while contribution becomes almost exact 1.3924 against 1.3920, an ordinary value result. The more accurate contribution partly reflects offsetting changes: the workload estimate worsens and the retained batting rate is too high for the realized yield. A good value score is not proof the job forecast improved. Raley, Rogers, Moncada and Biggio later have widely different workloads. The 643-person timing support is ordinary broad context, not a validated medical-return model. Keep separate forecast arithmetic and outcomes visible.

| Origin-selected comparison | Age | Origin MLB PA | Minor PA | Games mean PA | Late mean PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| Luke Raley | 28.0 | 406 | 0 | 349.59 | 318.52 | 455 | 2.49605 |
| Jake Rogers | 28.0 | 365 | 0 | 267.27 | 266.13 | 337 | -0.21645 |
| Yoán Moncada | 28.0 | 357 | 50 | 397.17 | 423.37 | 45 | 0.23516 |
| Cavan Biggio | 28.0 | 338 | 0 | 249.97 | 321.96 | 224 | 0.18162 |

## Reviewed decision

Retain the reliable timing source and this modestly improved broad-population point candidate as research. Do not replace the working assembly or frozen/deployed forecast: incremental games-control intervals include no improvement, public PA MAE is worse than working V33b and far above Steamer, the 2021-origin workload error worsens and never-debut upper minors slightly deteriorate. Strong late-debut mechanism examples do not override those groups. Source execution passes are not predictive certification. The practical goal remains incomplete. All eighteen reviews are complete before a next-model choice.
