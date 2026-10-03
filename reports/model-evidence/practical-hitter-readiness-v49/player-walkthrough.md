# MLB participation and conditional workload: actual player review

Thirty-one actual cases, with full original inputs and node paths in cases.json. Selection includes the twenty fixed fallback cases plus each binary arm’s consequential PA/contribution gains, harms, false highs/lows and ordinary outcomes. These exposed historical tests are development evidence, not a new untouched validation set.

Target: next-calendar-year MLB PA and batting-plus-replacement contribution. No full WAR, present-day MLB-equivalent talent, trade value, service/control horizon or career distribution is estimated here. Both binary arms preserve every non-arrival. The batting rate is held fixed; a better contribution number can reflect offsetting workload and rate mistakes.

Inputs are three actual source years of separate-level counts, fixed shrinkage/recency, age, observed history, position, draft/roster evidence and games/use; the scouting arm adds twelve historical ranking fields. Missing history is not zero production. Models do not add park-neutral contact, tracking quality or diagnosed future injuries. Participation path terms are log odds; conditional-use path terms are PA. Both are descriptive accounting, not causal feature effects. Equal-origin weights are recomputed within each declared training population; the two fitted heads are not claimed to constitute one exact joint weighted distribution.

Peers were selected using origin age, stage, debut, exposure, quality and rank, not future outcomes. They need not match draft pedigree. Conditional support counts only distinct people whose active MLB outcome was already known in that earlier training fold. A large coarse group does not certify a rare fast-moving prospect.

## Aaron Judge — 2016 to 2017

Player 592450; row 23934; fold 3; age 24.0; Current MLB; snapshot MLB. Selection: fixed diagnostic, value false low, carried previous review, fallback value false low, fixed previous diagnostic, binary_count value false low, binary_scout value largest gain, binary_scout value false low.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 278 | 65 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 66 | 8 | 72 | 49 |
| 2015 | AA | 280 | 63 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 61 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 93 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 27 | 4 | 42 | 9 |

Historical rank rows: [{'season': 2015, 'player_id': 592450, 'rank': 68, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Aaron Judge'}, {'season': 2016, 'player_id': 592450, 'rank': 31, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Aaron Judge'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2013/32; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 150.204635 | -0.057204 | 0.449525 |
| scout | Not estimated | Not estimated | 208.013735 | -0.057204 | 0.622533 |
| fallback | Not estimated | Not estimated | 208.013735 | -0.057204 | 0.622533 |
| binary_count | 0.880287 | 212.225277 | 186.819065 | -0.057204 | 0.559103 |
| binary_scout | 0.931614 | 308.550582 | 287.450116 | -0.057204 | 0.860267 |
| Actual | 1 | 678 | 678 | 5.329875619792154 | 8.108407 |

### binary_count: probability and workload accounting

Effective probability 0.88028659 × bounded conditional PA 212.225277 = expected PA 186.819065. Contribution = that PA × (-0.057204/600 + 0.00308809). Raw probability 0.88028659 is preserved separately from any availability override.

participation: reference -4.035729 plus all saved terms = raw 1.995147 log odds; logistic link gives probability 0.88028659. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.132028 log odds |
| games_mlb_0 | 27.0 | 1.093134 log odds |
| games_pool_MLB | 27.0 | 0.560206 log odds |
| MLB_0_pa | 95.0 | 0.306182 log odds |
| pooled_A_BABIP | 0.35451837140019865 | 0.292973 log odds |
| AAA_0_pa | 410.0 | 0.251755 log odds |
| pooled_MLB_pa | 95.0 | -0.250251 log odds |
| draft_rank | 0.5440362613193539 | 0.227223 log odds |

conditional_pa: reference 276.930516 plus all saved terms = raw 212.225277 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 95.0 | -61.003445 PA |
| pooled_MLB_K | 0.3333333333333333 | -28.283805 PA |
| work_0 | 95.07825370675452 | -25.924391 PA |
| role_pool_AAA | 4.334650856389986 | 21.022701 PA |
| pooled_Aplus_BB | 0.13800738007380073 | 18.233394 PA |
| pooled_Aplus_K | 0.244280442804428 | 13.670665 PA |
| role_minor_0 | 4.368932038834951 | 12.740002 PA |
| quality_0 | -0.17509126182885637 | -9.869483 PA |

### binary_scout: probability and workload accounting

Effective probability 0.93161424 × bounded conditional PA 308.550582 = expected PA 287.450116. Contribution = that PA × (-0.057204/600 + 0.00308809). Raw probability 0.93161424 is preserved separately from any availability override.

participation: reference -4.032416 plus all saved terms = raw 2.611754 log odds; logistic link gives probability 0.93161424. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.136733 log odds |
| games_mlb_0 | 27.0 | 1.175415 log odds |
| games_pool_MLB | 27.0 | 0.566620 log odds |
| scout_rank_score_0 | 0.7 | 0.334845 log odds |
| MLB_0_pa | 95.0 | 0.305036 log odds |
| pooled_MLB_pa | 95.0 | -0.271401 log odds |
| scout_listed_0 | 1.0 | 0.269240 log odds |
| pooled_A_BABIP | 0.35451837140019865 | 0.266006 log odds |

conditional_pa: reference 276.985230 plus all saved terms = raw 308.550582 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.7 | 126.949342 PA |
| MLB_0_pa | 95.0 | -63.368232 PA |
| pooled_MLB_K | 0.3333333333333333 | -22.851904 PA |
| work_0 | 95.07825370675452 | -22.663525 PA |
| role_pool_AAA | 4.334650856389986 | 15.964683 PA |
| pooled_Aplus_BB | 0.13800738007380073 | 14.872142 PA |
| pooled_Aplus_K | 0.244280442804428 | 14.311377 PA |
| role_minor_0 | 4.368932038834951 | 13.581704 PA |
| scout_list_capacity_2 | 100.0 | -6.873697 PA |

Full-population rank profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 53}]. Active-label conditional profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'conditional_rank_profile_players': 50}].

Actual original-fold general support: [{'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 181, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 321, 'current_players': 451, 'regular_players': 684, 'joint_players': 146, 'quality_joint_players': 239, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 411, 'current_players': 662, 'regular_players': 6446, 'joint_players': 181, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 23934, 'horizon': 1, 'player_id': 592450, 'origin_year': 2016, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 24.0, 'quality_0': -0.17509126182885637, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 321, 'current_players': 451, 'regular_players': 684, 'joint_players': 146, 'quality_joint_players': 239, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Judge's substantial AAA power and poor 95-PA MLB strikeout sample remain exactly the previous source record. Binary count estimates 88.0% participation and 212 PA if active (187 expected); scouting estimates 93.2% and 309 (287 expected), versus count-direct 150 and actual 678. Roster and observed MLB games dominate participation, while rank 31 strongly raises conditional opportunity. This is the scouting arm's largest contribution gain, .450 to .860, but actual 8.108 remains far away because the fixed -.057 batting wins/600 rate misses the breakout. The active-label rank profile has 50 people. Reed, Bell, Moya and Austin have varying eventual use; no near-certain appearance forecast guarantees a full successful season. Path ranking terms in the conditional model are PA; participation terms are log odds, not additive PA.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AJ Reed | 23.0 | 141 | 296 | 0.61 | 0.96353 | 308.02 | 296.79 | 6 | -0.14152 |
| Josh Bell | 23.0 | 152 | 484 | 0.52 | 0.95368 | 326.54 | 311.41 | 620 | 2.87812 |
| Steven Moya | 24.0 | 100 | 426 | 0.0 | 0.90364 | 251.09 | 226.89 | 0 | 0.00000 |
| Tyler Austin | 24.0 | 90 | 444 | 0.0 | 0.72832 | 138.15 | 100.62 | 46 | 0.05556 |

## Cody Bellinger — 2016 to 2017

Player 641355; row 24967; fold 3; age 20.0; Upper minors; snapshot AAA. Selection: fixed diagnostic, pa false low, carried previous review, fallback pa false low, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 51 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 128 | 30 | 150 | 51 |
| 2016 | AA | 465 | 114 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 3 | 0 | 1 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2013/124; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 7.761347 | 0.084712 | 0.025064 |
| scout | Not estimated | Not estimated | 2.725669 | 0.084712 | 0.008802 |
| fallback | Not estimated | Not estimated | 7.761347 | 0.084712 | 0.025064 |
| binary_count | 0.116043 | 139.464094 | 16.183882 | 0.084712 | 0.052262 |
| binary_scout | 0.101018 | 140.758217 | 14.219100 | 0.084712 | 0.045917 |
| Actual | 1 | 548 | 548 | 2.700470664969068 | 4.152174 |

### binary_count: probability and workload accounting

Effective probability 0.11604336 × bounded conditional PA 139.464094 = expected PA 16.183882. Contribution = that PA × (0.084712/600 + 0.00308809). Raw probability 0.11604336 is preserved separately from any availability override.

participation: reference -4.035729 plus all saved terms = raw -2.030444 log odds; logistic link gives probability 0.11604336. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.07258064516129 | 0.698419 log odds |
| pooled_AA_pa | 465.0 | 0.546649 log odds |
| games_minor_0 | 117.0 | 0.451279 log odds |
| on_40man | 0.0 | -0.425943 log odds |
| draft_rank | 0.365827730159369 | 0.370083 log odds |
| games_minor_1 | 128.0 | 0.303783 log odds |
| games_mlb_0 | 0.0 | -0.253910 log odds |
| role_pool_Aplus | 4.227758007117438 | 0.227305 log odds |

conditional_pa: reference 276.930516 plus all saved terms = raw 139.464094 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -85.415092 PA |
| age_centered | -1.4 | 33.770124 PA |
| work_0 | 0.0 | -31.405135 PA |
| on_40man | 0.0 | -16.712899 PA |
| role_pool_AAA | 4.0 | -12.130976 PA |
| pooled_Aplus_BB | 0.09118086696562033 | 12.100851 PA |
| pooled_Aplus_K | 0.26718983557548576 | 12.024031 PA |
| pooled_Aplus_BABIP | 0.3097447795823666 | -9.540752 PA |

### binary_scout: probability and workload accounting

Effective probability 0.10101791 × bounded conditional PA 140.758217 = expected PA 14.219100. Contribution = that PA × (0.084712/600 + 0.00308809). Raw probability 0.10101791 is preserved separately from any availability override.

participation: reference -4.032416 plus all saved terms = raw -2.185965 log odds; logistic link gives probability 0.10101791. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.07258064516129 | 0.699048 log odds |
| pooled_AA_pa | 465.0 | 0.547185 log odds |
| games_minor_0 | 117.0 | 0.442960 log odds |
| on_40man | 0.0 | -0.426657 log odds |
| draft_rank | 0.365827730159369 | 0.366576 log odds |
| games_minor_1 | 128.0 | 0.275206 log odds |
| games_mlb_0 | 0.0 | -0.248259 log odds |
| role_pool_Aplus | 4.227758007117438 | 0.208950 log odds |
| scout_listed_0 | 0.0 | -0.002929 log odds |
| scout_rank_score_0 | 0.0 | -0.001236 log odds |

conditional_pa: reference 276.985230 plus all saved terms = raw 140.758217 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -83.972347 PA |
| work_0 | 0.0 | -27.449139 PA |
| on_40man | 0.0 | -16.912854 PA |
| role_minor_2 | 4.475409836065574 | 14.871945 PA |
| pooled_AAA_pa | 12.0 | 12.884875 PA |
| role_pool_AAA | 4.0 | -12.323324 PA |
| pooled_Aplus_BB | 0.09118086696562033 | 11.049175 PA |
| age_centered | -1.4 | 9.789350 PA |
| scout_rank_score_0 | 0.0 | -6.009115 PA |

Full-population rank profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1030}]. Active-label conditional profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 208}].

Actual original-fold general support: [{'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 381, 'current_players': 468, 'regular_players': 684, 'joint_players': 161, 'quality_joint_players': 403, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 24967, 'horizon': 1, 'player_id': 641355, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 381, 'current_players': 468, 'regular_players': 684, 'joint_players': 161, 'quality_joint_players': 403, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Bellinger's 465 AA PA, 23 HR, 94 K and 57 BB plus 12 AAA PA are preserved. Binary scouting gives 10.1% MLB participation and 141 PA if active, only 14 expected versus 548 actual; count binary gives 16. This is slightly better than direct count 8 but still a serious arrival and workload miss. The conditional rate also misses his elite season. Broad unranked support 1,030 becomes only 208 earlier active-label people, and none of those numbers guarantee this precise young power/rapid-advancement profile. His unlisted preseason rank is stale, not absence of a scouting report. Rijo/Leyba do not arrive, Verdugo and Urena get 25/75 PA, supporting risk without making Bellinger's important production disappear.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Wendell Rijo | 20.0 | 0 | 441 | 0.0 | 0.03349 | 62.55 | 2.09 | 0 | 0.00000 |
| Alex Verdugo | 20.0 | 0 | 529 | 0.0 | 0.30548 | 101.69 | 31.06 | 25 | -0.08615 |
| Domingo Leyba | 20.0 | 0 | 548 | 0.0 | 0.73064 | 113.59 | 83.00 | 0 | 0.00000 |
| Richard Urena | 20.0 | 0 | 563 | 0.0 | 0.60664 | 114.16 | 69.26 | 75 | -0.17775 |

## Anthony Volpe — 2022 to 2023

Player 683011; row 48516; fold 4; age 21.0; Upper minors; snapshot AAA. Selection: fixed diagnostic, pa largest gain, carried previous review, fallback pa largest gain, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | A | 257 | 54 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 55 | 15 | 58 | 26 |
| 2022 | AA | 497 | 110 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 22 | 3 | 30 | 8 |

Historical rank rows: [{'season': 2022, 'player_id': 683011, 'rank': 8, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Anthony Volpe'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2019/30; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 166.138177 | -0.147697 | 0.479277 |
| scout | Not estimated | Not estimated | 415.735103 | -0.147697 | 1.199317 |
| fallback | Not estimated | Not estimated | 415.735103 | -0.147697 | 1.199317 |
| binary_count | 0.736684 | 278.979123 | 205.519538 | -0.147697 | 0.592885 |
| binary_scout | 0.835649 | 400.190077 | 334.418425 | -0.147697 | 0.964734 |
| Actual | 1 | 601 | 601 | -1.3447727729230707 | 0.513728 |

### binary_count: probability and workload accounting

Effective probability 0.73668429 × bounded conditional PA 278.979123 = expected PA 205.519538. Contribution = that PA × (-0.147697/600 + 0.00313097). Raw probability 0.73668429 is preserved separately from any availability override.

participation: reference -4.068418 plus all saved terms = raw 1.028806 log odds; logistic link gives probability 0.73668429. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.475 | 0.999636 log odds |
| pooled_AA_pa | 497.0 | 0.960802 log odds |
| games_minor_0 | 132.0 | 0.630060 log odds |
| draft_rank | 0.5525271637458875 | 0.497658 log odds |
| on_40man | 0.0 | -0.433477 log odds |
| age_centered | -1.2 | 0.377753 log odds |
| role_minor_0 | 4.47887323943662 | 0.356385 log odds |
| pooled_AAA_pa | 99.0 | 0.239228 log odds |

conditional_pa: reference 278.648619 plus all saved terms = raw 278.979123 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -103.685683 PA |
| role_pool_AAA | 4.34375 | 45.744932 PA |
| age_centered | -1.2 | 32.059387 PA |
| role_pool_AA | 4.475 | 23.865642 PA |
| on_40man | 0.0 | -18.662961 PA |
| role_minor_0 | 4.47887323943662 | 12.254956 PA |
| pooled_mlb_quality | 0.0 | -9.621878 PA |
| pooled_A_3B | 0.014725130890052354 | 9.121579 PA |

### binary_scout: probability and workload accounting

Effective probability 0.83564897 × bounded conditional PA 400.190077 = expected PA 334.418425. Contribution = that PA × (-0.147697/600 + 0.00313097). Raw probability 0.83564897 is preserved separately from any availability override.

participation: reference -4.073125 plus all saved terms = raw 1.626204 log odds; logistic link gives probability 0.83564897. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.475 | 0.971582 log odds |
| scout_rank_score_0 | 0.93 | 0.927076 log odds |
| pooled_AA_pa | 497.0 | 0.890232 log odds |
| games_minor_0 | 132.0 | 0.490423 log odds |
| scout_listed_0 | 1.0 | 0.446669 log odds |
| on_40man | 0.0 | -0.428682 log odds |
| draft_rank | 0.5525271637458875 | 0.410484 log odds |
| role_minor_0 | 4.47887323943662 | 0.353124 log odds |
| scout_list_capacity_2 | 99.0 | 0.036508 log odds |

conditional_pa: reference 278.685578 plus all saved terms = raw 400.190077 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.93 | 197.257091 PA |
| work_0 | 0.0 | -101.297405 PA |
| role_pool_AAA | 4.34375 | 31.437285 PA |
| role_pool_AA | 4.475 | 20.547352 PA |
| on_40man | 0.0 | -13.479779 PA |
| role_minor_0 | 4.47887323943662 | 13.457681 PA |
| age_centered | -1.2 | 10.553720 PA |
| role_pool_Aplus | 4.533333333333333 | 10.400905 PA |
| scout_rank_score_2 | -1.0 | 0.553071 PA |
| scout_listed_1 | -1.0 | -0.062258 PA |
| scout_rank_score_1 | -1.0 | 0.044124 PA |

Full-population rank profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 15}]. Active-label conditional profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 13}].

Actual original-fold general support: [{'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10086, 'current_players': 10584, 'regular_players': 10685, 'joint_players': 8356, 'quality_joint_players': 10163, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 854, 'current_players': 965, 'regular_players': 1216, 'joint_players': 326, 'quality_joint_players': 883, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10086, 'current_players': 10584, 'regular_players': 10685, 'joint_players': 8356, 'quality_joint_players': 10163, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 48516, 'horizon': 1, 'player_id': 683011, 'origin_year': 2022, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 854, 'current_players': 965, 'regular_players': 1216, 'joint_players': 326, 'quality_joint_players': 883, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Volpe's 596 AA/AAA PA and rank 8 are known. Rankings increase the binary estimates from 73.7% × 279 = 206 PA to 83.6% × 400 = 334, closer to 601 than count-direct 166 but lower than rank-direct 416. The rank score and sustained AA evidence support participation; rank score also raises conditional use. Only 13 earlier active-label people match the coarse ranked profile. Value .965 remains above actual .514 because the unchanged batting rate is too optimistic; reducing expected PA happens to reduce that value error but is not proof of improved hitting. Valera, Walker, Veen and Hassell show varied next-year use and failures.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| George Valera | 21.0 | 0 | 566 | 0.54 | 0.84733 | 185.46 | 157.14 | 0 | 0.00000 |
| Jordan Walker | 20.0 | 0 | 536 | 0.71 | 0.55180 | 223.90 | 123.55 | 465 | 2.39119 |
| Zac Veen | 20.0 | 0 | 541 | 0.65 | 0.43236 | 118.53 | 51.25 | 0 | 0.00000 |
| Robert Hassell III | 20.0 | 0 | 513 | 0.64 | 0.39349 | 202.89 | 79.83 | 0 | 0.00000 |

## Nick Kurtz — 2024 to 2025

Player 701762; row 57052; fold 2; age 21.0; Upper minors; snapshot AA. Selection: fixed diagnostic, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 4 | 7 | 10 |
| 2024 | AA | 15 | 5 | 0 | 3 | 2 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2024/4; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 29.943090 | -0.135562 | 0.086782 |
| scout | Not estimated | Not estimated | 2.947721 | -0.135562 | 0.008543 |
| fallback | Not estimated | Not estimated | 29.943090 | -0.135562 | 0.086782 |
| binary_count | 0.025059 | 161.336642 | 4.042937 | -0.135562 | 0.011717 |
| binary_scout | 0.017676 | 105.343956 | 1.862081 | -0.135562 | 0.005397 |
| Actual | 1 | 489 | 489 | 5.150009420178844 | 5.720989 |

### binary_count: probability and workload accounting

Effective probability 0.02505901 × bounded conditional PA 161.336642 = expected PA 4.042937. Contribution = that PA × (-0.135562/600 + 0.00312416). Raw probability 0.02505901 is preserved separately from any availability override.

participation: reference -4.010355 plus all saved terms = raw -3.661143 log odds; logistic link gives probability 0.02505901. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 1.107724 log odds |
| on_40man | 0.0 | -0.323503 log odds |
| role_pool_A | 4.411764705882353 | 0.249839 log odds |
| games_mlb_0 | 0.0 | -0.201534 log odds |
| games_pool_MLB | 0.0 | -0.200778 log odds |
| pooled_AA_pa | 15.0 | -0.156952 log odds |
| age_centered | -1.2 | 0.146614 log odds |
| role_minor_0 | 4.090909090909091 | 0.108192 log odds |

conditional_pa: reference 278.570242 plus all saved terms = raw 161.336642 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -99.841847 PA |
| draft_rank | 0.8176145045277415 | 36.425054 PA |
| age_centered | -1.2 | 28.322401 PA |
| on_40man | 0.0 | -19.860306 PA |
| quality_0 | 0.0 | -13.704345 PA |
| role_pool_AA | 3.6666666666666665 | -12.040031 PA |
| regular_window_scaled | 0.0 | -11.789987 PA |
| draft_rank_low_exposure | 0.5450763363518277 | 9.376242 PA |

### binary_scout: probability and workload accounting

Effective probability 0.01767620 × bounded conditional PA 105.343956 = expected PA 1.862081. Contribution = that PA × (-0.135562/600 + 0.00312416). Raw probability 0.01767620 is preserved separately from any availability override.

participation: reference -4.018196 plus all saved terms = raw -4.017702 log odds; logistic link gives probability 0.01767620. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 0.922715 log odds |
| on_40man | 0.0 | -0.328954 log odds |
| games_mlb_0 | 0.0 | -0.199218 log odds |
| games_pool_MLB | 0.0 | -0.188816 log odds |
| role_pool_A | 4.411764705882353 | 0.174386 log odds |
| pooled_AA_pa | 15.0 | -0.152495 log odds |
| age_centered | -1.2 | 0.125186 log odds |
| role_minor_0 | 4.090909090909091 | 0.119455 log odds |
| scout_listed_0 | 0.0 | -0.031590 log odds |
| scout_list_capacity_0 | 100.0 | -0.022113 log odds |
| scout_rank_score_0 | 0.0 | -0.018430 log odds |

conditional_pa: reference 278.535732 plus all saved terms = raw 105.343956 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -99.600000 PA |
| on_40man | 0.0 | -23.858148 PA |
| quality_0 | 0.0 | -13.312522 PA |
| draft_rank | 0.8176145045277415 | 10.956991 PA |
| age_centered | -1.2 | 10.817701 PA |
| regular_window_scaled | 0.0 | -10.311596 PA |
| role_pool_AAA | 4.0 | -9.572215 PA |
| role_pool_AA | 3.6666666666666665 | -7.482094 PA |
| scout_rank_score_0 | 0.0 | -6.222912 PA |
| scout_listed_0 | 0.0 | -0.060453 PA |

Full-population rank profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 2137}]. Active-label conditional profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 413}].

Actual original-fold general support: [{'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11239, 'current_players': 11751, 'regular_players': 11845, 'joint_players': 9411, 'quality_joint_players': 11314, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 978, 'current_players': 1098, 'regular_players': 1361, 'joint_players': 363, 'quality_joint_players': 1005, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11239, 'current_players': 11751, 'regular_players': 11845, 'joint_players': 9411, 'quality_joint_players': 11314, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 57052, 'horizon': 1, 'player_id': 701762, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 978, 'current_players': 1098, 'regular_players': 1361, 'joint_players': 363, 'quality_joint_players': 1005, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Kurtz's known fourth draft pick and 50 A/AA pro PA are intact. The binary scouting head gives only 1.77% participation and 105 PA if active, 1.86 expected versus 489 observed; even count binary is only 4 PA. Draft rank helps log odds but no roster/current MLB/meaningful upper-level exposure and stale preseason absence still dominate. This is not a satisfactory prior for every advanced new top draft pick. The large 413-person active unlisted profile does not establish support for a freshly drafted top-four college hitter with only 50 pro PA; the comparison distance also omits that pedigree. No future January ranking or elite outcome is inserted to repair him. The experiment improves lower-minor calibration but loses this fast-entry case.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Benny Montgomery | 21.0 | 0 | 48 | 0.0 | 0.07626 | 93.99 | 7.17 | 0 | 0.00000 |
| Ben Hartl | 21.0 | 0 | 57 | 0.0 | 0.00562 | 66.17 | 0.37 | 0 | 0.00000 |
| Wally Soto | 21.0 | 0 | 85 | 0.0 | 0.00208 | 74.92 | 0.16 | 0 | 0.00000 |
| Sergio Tapia | 21.0 | 0 | 103 | 0.0 | 0.00491 | 39.93 | 0.20 | 0 | 0.00000 |

## Carlos Concepcion — 2024 to 2025

Player 808393; row 57990; fold 4; age 18.0; Lower minors; snapshot ROOKIE_COMPLEX. Selection: fixed diagnostic, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | DSL | 133 | 33 | 4 | 29 | 13 |
| 2024 | DSL | 199 | 47 | 3 | 61 | 23 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 0.000000 | 0.213215 | 0.000000 |
| scout | Not estimated | Not estimated | 0.000000 | 0.213215 | 0.000000 |
| fallback | Not estimated | Not estimated | 0.000000 | 0.213215 | 0.000000 |
| binary_count | 0.001248 | 109.910502 | 0.137116 | 0.213215 | 0.000477 |
| binary_scout | 0.001214 | 83.311098 | 0.101124 | 0.213215 | 0.000352 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.00124752 × bounded conditional PA 109.910502 = expected PA 0.137116. Contribution = that PA × (0.213215/600 + 0.00312416). Raw probability 0.00124752 is preserved separately from any availability override.

participation: reference -4.060651 plus all saved terms = raw -6.685348 log odds; logistic link gives probability 0.00124752. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_pool_DSL | 73.4 | -0.560358 log odds |
| on_40man | 0.0 | -0.385184 log odds |
| games_mlb_0 | 0.0 | -0.212474 log odds |
| age_squared | 3.24 | -0.155066 log odds |
| pooled_AA_pa | 0.0 | -0.134188 log odds |
| age_centered | -1.8 | -0.129908 log odds |
| role_minor_0 | 4.192982456140351 | 0.126915 log odds |
| draft_rank | 0.0 | -0.108500 log odds |

conditional_pa: reference 279.717543 plus all saved terms = raw 109.910502 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -102.699608 PA |
| age_centered | -1.8 | 31.477818 PA |
| on_40man | 0.0 | -20.496067 PA |
| role_pool_AAA | 4.0 | -10.722403 PA |
| quality_0 | 0.0 | -9.204135 PA |
| regular_window_scaled | 0.0 | -8.683263 PA |
| pooled_MLB_pa | 0.0 | -7.571435 PA |
| pooled_mlb_quality | 0.0 | -7.078994 PA |

### binary_scout: probability and workload accounting

Effective probability 0.00121381 × bounded conditional PA 83.311098 = expected PA 0.101124. Contribution = that PA × (0.213215/600 + 0.00312416). Raw probability 0.00121381 is preserved separately from any availability override.

participation: reference -4.064249 plus all saved terms = raw -6.712779 log odds; logistic link gives probability 0.00121381. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_pool_DSL | 73.4 | -0.493933 log odds |
| on_40man | 0.0 | -0.382817 log odds |
| games_mlb_0 | 0.0 | -0.209313 log odds |
| age_squared | 3.24 | -0.184500 log odds |
| pooled_DSL_pa | 305.0 | -0.172678 log odds |
| role_minor_0 | 4.192982456140351 | 0.146180 log odds |
| pooled_AA_pa | 0.0 | -0.135782 log odds |
| age_centered | -1.8 | -0.120395 log odds |
| scout_listed_0 | 0.0 | -0.036147 log odds |
| scout_rank_score_0 | 0.0 | -0.007475 log odds |

conditional_pa: reference 279.712181 plus all saved terms = raw 83.311098 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -102.781559 PA |
| on_40man | 0.0 | -19.939531 PA |
| role_pool_AAA | 4.0 | -9.819843 PA |
| age_centered | -1.8 | 9.557921 PA |
| regular_window_scaled | 0.0 | -8.695429 PA |
| quality_0 | 0.0 | -8.605983 PA |
| pooled_mlb_quality | 0.0 | -8.367647 PA |
| pooled_MLB_pa | 0.0 | -7.743609 PA |
| scout_rank_score_0 | 0.0 | -5.240141 PA |
| scout_listed_0 | 0.0 | -0.997258 PA |

Full-population rank profile: [{'row_id': 57990, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'not_listed', 'rank_profile_players': 4891}]. Active-label conditional profile: [{'row_id': 57990, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 5}].

Actual original-fold general support: [{'row_id': 57990, 'horizon': 1, 'player_id': 808393, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11349, 'current_players': 11852, 'regular_players': 11954, 'joint_players': 9494, 'quality_joint_players': 11427, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 57990, 'horizon': 1, 'player_id': 808393, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 1019, 'current_players': 1135, 'regular_players': 1383, 'joint_players': 389, 'quality_joint_players': 1048, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 57990, 'horizon': 1, 'player_id': 808393, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11349, 'current_players': 11852, 'regular_players': 11954, 'joint_players': 9494, 'quality_joint_players': 11427, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 57990, 'horizon': 1, 'player_id': 808393, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 1019, 'current_players': 1135, 'regular_players': 1383, 'joint_players': 389, 'quality_joint_players': 1048, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Concepcion retains actual 2023/2024 DSL counts, age eighteen, no MLB exposure and no positive rank. Binary scouting separates .121% appearance probability from 83 PA if active, yielding .101 expected PA and .00035 contribution versus zero actual. That tiny nonzero annual mean is reasonable probability mass, not a declaration of MLB-ready talent or future career value. Only five earlier active-label people match his broad lower/unlisted age profile; his conditional workload/rate is especially uncertain. DSL exposure suppresses participation while same-age peers also do not arrive. The panel does not fabricate uncaptured earlier DSL history.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hector Liriano | 18.0 | 0 | 199 | 0.0 | 0.00126 | 67.09 | 0.08 | 0 | 0.00000 |
| Gery Holguin | 18.0 | 0 | 201 | 0.0 | 0.00136 | 74.31 | 0.10 | 0 | 0.00000 |
| Jesus Alexander | 18.0 | 0 | 197 | 0.0 | 0.00190 | 71.47 | 0.14 | 0 | 0.00000 |
| Angel Guzman | 18.0 | 0 | 201 | 0.0 | 0.00120 | 86.95 | 0.10 | 0 | 0.00000 |

## Lewis Brinson — 2016 to 2017

Player 621446; row 24603; fold 0; age 22.0; Upper minors; snapshot AAA. Selection: fixed diagnostic, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 186 | 43 | 10 | 46 | 18 |
| 2014 | Aplus | 199 | 46 | 3 | 50 | 15 |
| 2015 | AA | 121 | 28 | 6 | 28 | 6 |
| 2015 | AAA | 37 | 8 | 1 | 6 | 7 |
| 2015 | Aplus | 298 | 64 | 13 | 64 | 31 |
| 2016 | AA | 326 | 77 | 11 | 64 | 17 |
| 2016 | AAA | 93 | 23 | 4 | 21 | 2 |
| 2016 | RK121 | 15 | 4 | 0 | 2 | 2 |

Historical rank rows: [{'season': 2016, 'player_id': 621446, 'rank': 16, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Lewis Brinson'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2012/29; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 120.749824 | -0.130991 | 0.346525 |
| scout | Not estimated | Not estimated | 253.791760 | -0.130991 | 0.728325 |
| fallback | Not estimated | Not estimated | 253.791760 | -0.130991 | 0.728325 |
| binary_count | 0.664910 | 259.132542 | 172.299695 | -0.130991 | 0.494461 |
| binary_scout | 0.749619 | 395.642054 | 296.580930 | -0.130991 | 0.851120 |
| Actual | 1 | 55 | 55 | -4.87094776737043 | -0.277314 |

### binary_count: probability and workload accounting

Effective probability 0.66490952 × bounded conditional PA 259.132542 = expected PA 172.299695. Contribution = that PA × (-0.130991/600 + 0.00308809). Raw probability 0.66490952 is preserved separately from any availability override.

participation: reference -4.071018 plus all saved terms = raw 0.685250 log odds; logistic link gives probability 0.66490952. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.864377 log odds |
| pooled_MLB_pa | 0.0 | -0.442028 log odds |
| games_mlb_0 | 0.0 | -0.372263 log odds |
| draft_rank | 0.5569873646044212 | 0.318323 log odds |
| pooled_AA_pa | 422.8 | 0.290819 log odds |
| games_minor_0 | 104.0 | 0.286949 log odds |
| role_pool_Aplus | 4.47972972972973 | 0.209945 log odds |
| MLB_0_pa | 0.0 | -0.204504 log odds |

conditional_pa: reference 281.257322 plus all saved terms = raw 259.132542 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -72.830723 PA |
| MLB_0_pa | 0.0 | -51.514731 PA |
| pooled_Aplus_2B | 0.059851463521188294 | 25.723984 PA |
| pooled_Aplus_BB | 0.09130624726955001 | 24.888695 PA |
| age_centered | -1.0 | 24.524500 PA |
| role_pool_AAA | 4.126903553299492 | 20.467141 PA |
| pooled_Aplus_HR | 0.033202271734381825 | 16.229263 PA |
| pooled_AAA_HR | 0.03504043126684636 | 14.384866 PA |

### binary_scout: probability and workload accounting

Effective probability 0.74961933 × bounded conditional PA 395.642054 = expected PA 296.580930. Contribution = that PA × (-0.130991/600 + 0.00308809). Raw probability 0.74961933 is preserved separately from any availability override.

participation: reference -4.061750 plus all saved terms = raw 1.096583 log odds; logistic link gives probability 0.74961933. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.847547 log odds |
| scout_rank_score_0 | 0.85 | 0.496298 log odds |
| pooled_MLB_pa | 0.0 | -0.443793 log odds |
| games_mlb_0 | 0.0 | -0.323797 log odds |
| draft_rank | 0.5569873646044212 | 0.323422 log odds |
| games_minor_0 | 104.0 | 0.306805 log odds |
| pooled_AA_pa | 422.8 | 0.270568 log odds |
| MLB_0_pa | 0.0 | -0.202796 log odds |

conditional_pa: reference 281.301982 plus all saved terms = raw 395.642054 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.85 | 182.137672 PA |
| work_0 | 0.0 | -70.122276 PA |
| MLB_0_pa | 0.0 | -48.448534 PA |
| pooled_Aplus_BB | 0.09130624726955001 | 17.785422 PA |
| pooled_AAA_HR | 0.03504043126684636 | 17.225934 PA |
| pooled_Aplus_2B | 0.059851463521188294 | 14.603127 PA |
| pooled_AAA_2B | 0.06648697214734951 | 14.168449 PA |
| age_centered | -1.0 | 11.719075 PA |

Full-population rank profile: [{'row_id': 24603, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 9}]. Active-label conditional profile: [{'row_id': 24603, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 7}].

Actual original-fold general support: [{'row_id': 24603, 'horizon': 1, 'player_id': 621446, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 24603, 'horizon': 1, 'player_id': 621446, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 467, 'regular_players': 663, 'joint_players': 161, 'quality_joint_players': 409, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 24603, 'horizon': 1, 'player_id': 621446, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 24603, 'horizon': 1, 'player_id': 621446, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 22.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 467, 'regular_players': 663, 'joint_players': 161, 'quality_joint_players': 409, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Brinson's actual AA/AAA work, roster flag and source-qualified rank 16 produce 75.0% appearance probability and 396 conditional PA, 297 expected versus count-direct 121 and actual 55. Both binary architecture and scouting increase his error; predicted contribution .851 versus -.277 also worsens. A true high prospect ranking is not a source bug because the player fails. Only seven earlier active-label top20 profile people are available; conditional opportunity is not well certified. Winker, Phillips, Williams and Meadows span 0 to 343 next-year PA, including delays. This harm remains in every score and blocks any claim that rankings solve readiness for individuals.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jesse Winker | 22.0 | 0 | 463 | 0.67 | 0.80645 | 296.76 | 239.32 | 137 | 1.14962 |
| Brett Phillips | 22.0 | 0 | 517 | 0.69 | 0.62563 | 280.46 | 175.46 | 98 | 0.38347 |
| Nick Williams | 22.0 | 0 | 527 | 0.37 | 0.54745 | 201.29 | 110.20 | 343 | 1.82007 |
| Austin Meadows | 21.0 | 0 | 352 | 0.81 | 0.52526 | 344.68 | 181.05 | 0 | 0.00000 |

## Clint Frazier — 2016 to 2017

Player 640449; row 24933; fold 0; age 21.0; Upper minors; snapshot AAA. Selection: fixed diagnostic, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | A | 542 | 120 | 13 | 161 | 55 |
| 2015 | Aplus | 588 | 133 | 16 | 125 | 66 |
| 2016 | AA | 391 | 89 | 13 | 86 | 41 |
| 2016 | AAA | 129 | 30 | 3 | 36 | 7 |

Historical rank rows: [{'season': 2014, 'player_id': 640449, 'rank': 48, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}, {'season': 2015, 'player_id': 640449, 'rank': 53, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}, {'season': 2016, 'player_id': 640449, 'rank': 27, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Clint Frazier'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2013/5; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 145.290247 | -0.001169 | 0.448386 |
| scout | Not estimated | Not estimated | 236.116290 | -0.001169 | 0.728689 |
| fallback | Not estimated | Not estimated | 236.116290 | -0.001169 | 0.728689 |
| binary_count | 0.432665 | 292.360060 | 126.494059 | -0.001169 | 0.390379 |
| binary_scout | 0.501519 | 373.348284 | 187.241257 | -0.001169 | 0.577853 |
| Actual | 1 | 142 | 142 | -0.9678557871572135 | 0.207758 |

### binary_count: probability and workload accounting

Effective probability 0.43266532 × bounded conditional PA 292.360060 = expected PA 126.494059. Contribution = that PA × (-0.001169/600 + 0.00308809). Raw probability 0.43266532 is preserved separately from any availability override.

participation: reference -4.071018 plus all saved terms = raw -0.270985 log odds; logistic link gives probability 0.43266532. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| draft_rank | 0.7882569969815056 | 1.025071 log odds |
| role_pool_AA | 4.353535353535354 | 0.774720 log odds |
| pooled_AA_pa | 391.0 | 0.598838 log odds |
| on_40man | 0.0 | -0.456247 log odds |
| role_pool_Aplus | 4.384879725085911 | 0.453487 log odds |
| games_minor_0 | 119.0 | 0.407727 log odds |
| games_mlb_0 | 0.0 | -0.279969 log odds |
| role_minor_0 | 4.341085271317829 | 0.277180 log odds |

conditional_pa: reference 281.257322 plus all saved terms = raw 292.360060 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -72.830723 PA |
| MLB_0_pa | 0.0 | -45.406172 PA |
| age_centered | -1.2 | 35.923021 PA |
| pooled_Aplus_2B | 0.05925666199158484 | 31.171787 PA |
| pooled_Aplus_BB | 0.10659186535764376 | 24.888695 PA |
| role_pool_AAA | 4.225 | 20.573327 PA |
| draft_rank | 0.7882569969815056 | 19.353337 PA |
| pooled_AAA_3B | 0.019650655021834062 | 14.830875 PA |

### binary_scout: probability and workload accounting

Effective probability 0.50151900 × bounded conditional PA 373.348284 = expected PA 187.241257. Contribution = that PA × (-0.001169/600 + 0.00308809). Raw probability 0.50151900 is preserved separately from any availability override.

participation: reference -4.061750 plus all saved terms = raw 0.006076 log odds; logistic link gives probability 0.50151900. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| draft_rank | 0.7882569969815056 | 0.879124 log odds |
| role_pool_AA | 4.353535353535354 | 0.791185 log odds |
| pooled_AA_pa | 391.0 | 0.614773 log odds |
| scout_rank_score_0 | 0.74 | 0.496298 log odds |
| role_pool_Aplus | 4.384879725085911 | 0.460256 log odds |
| on_40man | 0.0 | -0.453763 log odds |
| games_minor_0 | 119.0 | 0.424481 log odds |
| role_minor_0 | 4.341085271317829 | 0.259240 log odds |

conditional_pa: reference 281.301982 plus all saved terms = raw 373.348284 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.74 | 153.887639 PA |
| work_0 | 0.0 | -70.122276 PA |
| MLB_0_pa | 0.0 | -44.083090 PA |
| Aplus_1_pa | 588.0 | 24.319153 PA |
| pooled_Aplus_2B | 0.05925666199158484 | 20.298369 PA |
| pooled_Aplus_BB | 0.10659186535764376 | 17.785422 PA |
| on_40man | 0.0 | -15.728459 PA |
| pooled_AAA_3B | 0.019650655021834062 | 14.074173 PA |

Full-population rank profile: [{'row_id': 24933, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 43}]. Active-label conditional profile: [{'row_id': 24933, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': '21plus', 'conditional_rank_profile_players': 30}].

Actual original-fold general support: [{'row_id': 24933, 'horizon': 1, 'player_id': 640449, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 24933, 'horizon': 1, 'player_id': 640449, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 467, 'regular_players': 663, 'joint_players': 161, 'quality_joint_players': 409, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 24933, 'horizon': 1, 'player_id': 640449, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5949, 'current_players': 6330, 'regular_players': 6488, 'joint_players': 4632, 'quality_joint_players': 6022, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 24933, 'horizon': 1, 'player_id': 640449, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 467, 'regular_players': 663, 'joint_players': 161, 'quality_joint_players': 409, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Frazier's rank 27 and 520 upper-minor PA produce 50.2% × 373 = 187 expected PA versus count-direct 145 and actual 142. Count-only binary is 126, showing rankings shift both occurrence and use rather than a single universal bonus. The scouting arm is better than rank-direct 236 but still worse than the original point on PA/value. Only thirty earlier active-label people match the coarse profile. Crawford/Meadows delays and Smith/McMahon low-volume appearances are valid outcomes for comparable high-regard prospects, not cherry-picked successes.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ryan McMahon | 21.0 | 0 | 535 | 0.53 | 0.36139 | 207.68 | 75.05 | 24 | -0.02515 |
| J.P. Crawford | 21.0 | 0 | 551 | 0.96 | 0.62750 | 384.23 | 241.10 | 87 | 0.15713 |
| Dominic Smith | 21.0 | 0 | 542 | 0.5 | 0.44444 | 184.55 | 82.02 | 183 | 0.00276 |
| Austin Meadows | 21.0 | 0 | 352 | 0.81 | 0.52526 | 344.68 | 181.05 | 0 | 0.00000 |

## Corey Seager — 2016 to 2017

Player 608369; row 24459; fold 0; age 22.0; Current MLB; snapshot MLB. Selection: fixed diagnostic, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | AA | 161 | 38 | 2 | 39 | 10 |
| 2014 | Aplus | 365 | 80 | 18 | 76 | 28 |
| 2015 | AA | 86 | 20 | 5 | 11 | 4 |
| 2015 | AAA | 464 | 105 | 13 | 65 | 30 |
| 2015 | MLB | 113 | 27 | 4 | 19 | 13 |
| 2016 | MLB | 687 | 157 | 26 | 133 | 49 |

Historical rank rows: [{'season': 2014, 'player_id': 608369, 'rank': 34, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}, {'season': 2015, 'player_id': 608369, 'rank': 7, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}, {'season': 2016, 'player_id': 608369, 'rank': 1, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Corey Seager'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2012/18; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 607.831756 | 1.699743 | 3.598970 |
| scout | Not estimated | Not estimated | 641.917239 | 1.699743 | 3.800790 |
| fallback | Not estimated | Not estimated | 641.917239 | 1.699743 | 3.800790 |
| binary_count | 0.992782 | 656.938522 | 652.196676 | 1.699743 | 3.861654 |
| binary_scout | 0.994196 | 669.780765 | 665.893479 | 1.699743 | 3.942753 |
| Actual | 1 | 613 | 613 | 2.1848833518965316 | 4.117918 |

### binary_count: probability and workload accounting

Effective probability 0.99278190 × bounded conditional PA 656.938522 = expected PA 652.196676. Contribution = that PA × (1.699743/600 + 0.00308809). Raw probability 0.99278190 is preserved separately from any availability override.

participation: reference -4.071018 plus all saved terms = raw 4.923920 log odds; logistic link gives probability 0.99278190. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.342696 log odds |
| games_mlb_0 | 157.0 | 2.011276 log odds |
| quality_0 | 0.9963063950369828 | 0.777902 log odds |
| MLB_0_pa | 687.0 | 0.771031 log odds |
| pooled_MLB_pa | 777.4 | 0.393269 log odds |
| position_6 | 1.0 | 0.285085 log odds |
| games_pool_MLB | 178.6 | 0.277300 log odds |
| pooled_Aplus_HR | 0.04326018808777429 | 0.200769 log odds |

conditional_pa: reference 281.257322 plus all saved terms = raw 656.938522 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 687.5658978583195 | 109.367029 PA |
| role_mlb_0 | 4.3532934131736525 | 45.212867 PA |
| MLB_0_pa | 687.0 | 34.530051 PA |
| role_pool_MLB | 4.334040296924709 | 27.109542 PA |
| age_centered | -1.0 | 27.056202 PA |
| quality_0 | 0.9963063950369828 | 21.152704 PA |
| pooled_Aplus_2B | 0.07962382445141065 | 17.556465 PA |
| role_pool_AAA | 4.3744680851063835 | 15.469324 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99419618 × bounded conditional PA 669.780765 = expected PA 665.893479. Contribution = that PA × (1.699743/600 + 0.00308809). Raw probability 0.99419618 is preserved separately from any availability override.

participation: reference -4.061750 plus all saved terms = raw 5.143419 log odds; logistic link gives probability 0.99419618. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.325866 log odds |
| games_mlb_0 | 157.0 | 1.941184 log odds |
| quality_0 | 0.9963063950369828 | 0.745052 log odds |
| MLB_0_pa | 687.0 | 0.741453 log odds |
| pooled_MLB_pa | 777.4 | 0.411714 log odds |
| scout_rank_score_0 | 1.0 | 0.394264 log odds |
| games_pool_MLB | 178.6 | 0.280727 log odds |
| position_6 | 1.0 | 0.275209 log odds |

conditional_pa: reference 281.301982 plus all saved terms = raw 669.780765 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 687.5658978583195 | 107.221166 PA |
| role_mlb_0 | 4.3532934131736525 | 44.489650 PA |
| scout_rank_score_0 | 1.0 | 32.713073 PA |
| MLB_0_pa | 687.0 | 31.399603 PA |
| role_pool_MLB | 4.334040296924709 | 28.536892 PA |
| age_centered | -1.0 | 23.474481 PA |
| quality_0 | 0.9963063950369828 | 23.234996 PA |
| pooled_AA_BABIP | 0.3652253909843607 | 15.677430 PA |

Full-population rank profile: [{'row_id': 24459, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 22}]. Active-label conditional profile: [{'row_id': 24459, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 20}].

Actual original-fold general support: [{'row_id': 24459, 'horizon': 1, 'player_id': 608369, 'origin_year': 2016, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 22.0, 'quality_0': 0.9963063950369828, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 399, 'current_players': 307, 'regular_players': 269, 'joint_players': 14, 'quality_joint_players': 111, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 24459, 'horizon': 1, 'player_id': 608369, 'origin_year': 2016, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 22.0, 'quality_0': 0.9963063950369828, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 281, 'current_players': 301, 'regular_players': 231, 'joint_players': 14, 'quality_joint_players': 110, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 24459, 'horizon': 1, 'player_id': 608369, 'origin_year': 2016, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 22.0, 'quality_0': 0.9963063950369828, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 399, 'current_players': 307, 'regular_players': 269, 'joint_players': 14, 'quality_joint_players': 111, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 24459, 'horizon': 1, 'player_id': 608369, 'origin_year': 2016, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 22.0, 'quality_0': 0.9963063950369828, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 281, 'current_players': 301, 'regular_players': 231, 'joint_players': 14, 'quality_joint_players': 110, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Seager's completed 687-PA MLB season drives appearance probability about 99.4%, not his old prospect rank alone. Scouting conditional PA 670 yields 666 expected versus 613 actual, worsening workload from count-direct 608; count binary 652 is also too high. Contribution 3.943 comes closer to 4.118 because excessive PA offsets an underestimated fixed batting rate. Twenty active-label rank-profile people are available, but the model still retains obsolete prospect information for a now-established player. No after-result graduation gate is added. His peers' strong regular use supports high participation, not an exact future PA number.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nomar Mazara | 21.0 | 568 | 13 | 0.83 | 0.97713 | 468.18 | 457.48 | 616 | 1.73244 |
| Francisco Lindor | 22.0 | 684 | 0 | 0.0 | 0.99387 | 577.95 | 574.41 | 723 | 4.03895 |
| Rougned Odor | 22.0 | 632 | 0 | 0.0 | 0.99235 | 591.73 | 587.20 | 651 | -0.58638 |
| Manny Machado | 23.0 | 696 | 0 | 0.0 | 0.99528 | 633.54 | 630.55 | 690 | 2.62526 |

## Wyatt Langford — 2023 to 2024

Player 694671; row 53164; fold 4; age 21.0; Upper minors; snapshot AAA. Selection: pa largest harm, carried previous review, fixed previous diagnostic, binary_scout pa largest harm.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | AA | 54 | 12 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 5 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 24 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 3 | 1 | 3 | 1 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2023/4; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 216.806522 | 0.642693 | 0.903483 |
| scout | Not estimated | Not estimated | 116.426835 | 0.642693 | 0.485178 |
| fallback | Not estimated | Not estimated | 216.806522 | 0.642693 | 0.903483 |
| binary_count | 0.352862 | 292.017928 | 103.042054 | 0.642693 | 0.429400 |
| binary_scout | 0.216727 | 216.599272 | 46.942857 | 0.642693 | 0.195622 |
| Actual | 1 | 557 | 557 | 0.5490777231604176 | 2.249169 |

### binary_count: probability and workload accounting

Effective probability 0.35286208 × bounded conditional PA 292.017928 = expected PA 103.042054. Contribution = that PA × (0.642693/600 + 0.00309608). Raw probability 0.35286208 is preserved separately from any availability override.

participation: reference -4.070568 plus all saved terms = raw -0.606482 log odds; logistic link gives probability 0.35286208. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| draft_rank | 0.8176145045277415 | 1.061476 log odds |
| role_pool_AA | 4.2727272727272725 | 0.968537 log odds |
| pooled_AA_pa | 54.0 | 0.480201 log odds |
| role_minor_0 | 4.444444444444445 | 0.406701 log odds |
| on_40man | 0.0 | -0.405423 log odds |
| games_mlb_0 | 0.0 | -0.235044 log odds |
| pooled_AA_HR | 0.045454545454545456 | 0.221930 log odds |
| pooled_AAA_pa | 26.0 | 0.209139 log odds |

conditional_pa: reference 279.225360 plus all saved terms = raw 292.017928 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -98.550233 PA |
| role_pool_AAA | 4.4 | 41.667189 PA |
| age_centered | -1.2 | 37.484710 PA |
| draft_rank_low_exposure | 0.27253816817591386 | 27.200368 PA |
| on_40man | 0.0 | -20.082573 PA |
| draft_rank | 0.8176145045277415 | 17.653363 PA |
| role_pool_AA | 4.2727272727272725 | 15.970927 PA |
| pooled_AA_HR | 0.045454545454545456 | 9.212068 PA |

### binary_scout: probability and workload accounting

Effective probability 0.21672676 × bounded conditional PA 216.599272 = expected PA 46.942857. Contribution = that PA × (0.642693/600 + 0.00309608). Raw probability 0.21672676 is preserved separately from any availability override.

participation: reference -4.078303 plus all saved terms = raw -1.284844 log odds; logistic link gives probability 0.21672676. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.2727272727272725 | 0.965841 log odds |
| draft_rank | 0.8176145045277415 | 0.712518 log odds |
| pooled_AA_pa | 54.0 | 0.452235 log odds |
| on_40man | 0.0 | -0.402028 log odds |
| role_minor_0 | 4.444444444444445 | 0.398565 log odds |
| games_mlb_0 | 0.0 | -0.231251 log odds |
| pooled_AAA_pa | 26.0 | 0.231139 log odds |
| pooled_AA_HR | 0.045454545454545456 | 0.176382 log odds |
| scout_listed_0 | 0.0 | -0.089209 log odds |
| scout_list_capacity_2 | 99.0 | 0.014741 log odds |
| scout_rank_score_0 | 0.0 | -0.007927 log odds |

conditional_pa: reference 279.236087 plus all saved terms = raw 216.599272 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -99.333725 PA |
| role_pool_AAA | 4.4 | 36.983065 PA |
| on_40man | 0.0 | -18.288035 PA |
| age_centered | -1.2 | 14.628176 PA |
| role_pool_AA | 4.2727272727272725 | 13.343625 PA |
| draft_rank_low_exposure | 0.27253816817591386 | 11.016157 PA |
| regular_window_scaled | 0.0 | -9.672346 PA |
| pooled_mlb_quality | 0.0 | -8.925146 PA |
| scout_rank_score_0 | 0.0 | -5.626191 PA |

Full-population rank profile: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1972}]. Active-label conditional profile: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 393}].

Actual original-fold general support: [{'row_id': 53164, 'horizon': 1, 'player_id': 694671, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10725, 'current_players': 11226, 'regular_players': 11325, 'joint_players': 8919, 'quality_joint_players': 10803, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 53164, 'horizon': 1, 'player_id': 694671, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 936, 'current_players': 1047, 'regular_players': 1298, 'joint_players': 358, 'quality_joint_players': 965, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 53164, 'horizon': 1, 'player_id': 694671, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10725, 'current_players': 11226, 'regular_players': 11325, 'joint_players': 8919, 'quality_joint_players': 10803, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 53164, 'horizon': 1, 'player_id': 694671, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 936, 'current_players': 1047, 'regular_players': 1298, 'joint_players': 358, 'quality_joint_players': 965, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Langford's fourth draft pick and immediate rookie-to-AAA progression are preserved. Count-only binary gives 35.3% × 292 = 103 PA; the scouting version gives 21.7% × 217 = 47, versus count-direct 217 and actual 557. This is the scouting arm's largest PA deterioration. The annual preseason list predates his draft, and the same stale-absence problem remains; binary decomposition alone cannot replace fresh evidence about new draftees. Unranked active support 393 is broad and the four comparison players are not equally high-pedigree. This is a lost representation that matters for prospect valuation, not something to excuse with a better pooled score.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Zion Bannister | 21.0 | 0 | 200 | 0.0 | 0.00355 | 60.50 | 0.21 | 0 | 0.00000 |
| Brock Wilken | 21.0 | 0 | 203 | 0.0 | 0.04866 | 105.95 | 5.16 | 0 | 0.00000 |
| Yohandy Morales | 21.0 | 0 | 189 | 0.0 | 0.05994 | 94.52 | 5.67 | 0 | 0.00000 |
| Homer Bush Jr. | 21.0 | 0 | 187 | 0.0 | 0.00800 | 92.92 | 0.74 | 0 | 0.00000 |

## Miguel Andujar — 2018 to 2019

Player 609280; row 33062; fold 4; age 23.0; Current MLB; snapshot MLB. Selection: pa false high, carried previous review, fallback pa false high, fallback value largest harm, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | AA | 319 | 72 | 2 | 42 | 21 |
| 2016 | Aplus | 251 | 58 | 10 | 30 | 18 |
| 2017 | AA | 272 | 67 | 7 | 38 | 12 |
| 2017 | AAA | 250 | 58 | 9 | 33 | 16 |
| 2017 | MLB | 8 | 5 | 0 | 0 | 1 |
| 2018 | MLB | 606 | 149 | 27 | 97 | 23 |

Historical rank rows: [{'season': 2018, 'player_id': 609280, 'rank': 65, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Miguel Andujar'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 568.353225 | 0.972246 | 2.670793 |
| scout | Not estimated | Not estimated | 613.935608 | 0.972246 | 2.884992 |
| fallback | Not estimated | Not estimated | 613.935608 | 0.972246 | 2.884992 |
| binary_count | 0.990613 | 533.691692 | 528.682124 | 0.972246 | 2.484371 |
| binary_scout | 0.993072 | 571.302190 | 567.344400 | 0.972246 | 2.666052 |
| Actual | 1 | 49 | 49 | -10.043988716563746 | -0.670576 |

### binary_count: probability and workload accounting

Effective probability 0.99061337 × bounded conditional PA 533.691692 = expected PA 528.682124. Contribution = that PA × (0.972246/600 + 0.00307877). Raw probability 0.99061337 is preserved separately from any availability override.

participation: reference -4.163750 plus all saved terms = raw 4.659038 log odds; logistic link gives probability 0.99061337. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.635686 log odds |
| games_mlb_0 | 149.0 | 1.520959 log odds |
| work_0 | 605.7507198683669 | 0.791006 log odds |
| quality_0 | 0.7932473892702949 | 0.714478 log odds |
| games_pool_MLB | 153.0 | 0.539568 log odds |
| MLB_0_pa | 606.0 | 0.211334 log odds |
| career_mlb_observed_pa | 614.0 | 0.205274 log odds |
| role_minor_0 | 4.0 | 0.131122 log odds |

conditional_pa: reference 283.113737 plus all saved terms = raw 533.691692 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 606.0 | 106.275072 PA |
| quality_0 | 0.7932473892702949 | 29.883186 PA |
| role_mlb_0 | 4.062893081761007 | 27.672011 PA |
| work_0 | 605.7507198683669 | 25.210806 PA |
| age_centered | -0.8 | 17.686299 PA |
| role_pool_MLB | 4.002453987730061 | -14.023088 PA |
| pooled_AA_HR | 0.01925343811394892 | -11.700356 PA |
| pooled_MLB_2B | 0.07523862998315553 | 9.895915 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99307234 × bounded conditional PA 571.302190 = expected PA 567.344400. Contribution = that PA × (0.972246/600 + 0.00307877). Raw probability 0.99307234 is preserved separately from any availability override.

participation: reference -4.172722 plus all saved terms = raw 4.965281 log odds; logistic link gives probability 0.99307234. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.614656 log odds |
| games_mlb_0 | 149.0 | 1.483718 log odds |
| work_0 | 605.7507198683669 | 0.755968 log odds |
| quality_0 | 0.7932473892702949 | 0.680695 log odds |
| games_pool_MLB | 153.0 | 0.547817 log odds |
| scout_rank_score_0 | 0.36 | 0.499279 log odds |
| MLB_0_pa | 606.0 | 0.260335 log odds |
| career_mlb_observed_pa | 614.0 | 0.209758 log odds |

conditional_pa: reference 283.076477 plus all saved terms = raw 571.302190 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 606.0 | 99.880613 PA |
| role_mlb_0 | 4.062893081761007 | 29.437155 PA |
| quality_0 | 0.7932473892702949 | 26.733604 PA |
| work_0 | 605.7507198683669 | 25.226552 PA |
| age_centered | -0.8 | 19.075296 PA |
| pooled_mlb_quality | 0.8431366300375014 | 16.235234 PA |
| scout_listed_0 | 1.0 | 15.964083 PA |
| regular_window_scaled | 0.3333333333333333 | 13.406388 PA |
| scout_rank_score_0 | 0.36 | 6.250605 PA |
| scout_rank_score_1 | 0.0 | 0.072081 PA |
| scout_listed_1 | 0.0 | -0.035852 PA |

Full-population rank profile: [{'row_id': 33062, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'rank_profile_players': 86}]. Active-label conditional profile: [{'row_id': 33062, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'conditional_rank_profile_players': 82}].

Actual original-fold general support: [{'row_id': 33062, 'horizon': 1, 'player_id': 609280, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.7932473892702949, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 556, 'current_players': 365, 'regular_players': 344, 'joint_players': 114, 'quality_joint_players': 156, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 33062, 'horizon': 1, 'player_id': 609280, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.7932473892702949, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 393, 'current_players': 360, 'regular_players': 298, 'joint_players': 113, 'quality_joint_players': 154, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 33062, 'horizon': 1, 'player_id': 609280, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.7932473892702949, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 556, 'current_players': 365, 'regular_players': 344, 'joint_players': 114, 'quality_joint_players': 156, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 33062, 'horizon': 1, 'player_id': 609280, 'origin_year': 2018, 'elapsed': 1, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.7932473892702949, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 393, 'current_players': 360, 'regular_players': 298, 'joint_players': 113, 'quality_joint_players': 154, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Andujar's 606-PA, 27-HR MLB rookie season supports about 99.3% chance of any MLB return in the scouting head. Conditional workload 571 produces 567 expected versus actual 49, still a major exposure collapse, though less than the rank-direct 614. Count binary is lower at 529. Participation correctly anticipates some appearance; the crucial miss is how much he plays and how well he hits. The case source alone does not establish which later injury was cutoff-known, so no causal injury explanation is invented. Populated active support and regular young peers do not eliminate future health/job risk.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Andrew Benintendi | 23.0 | 661 | 0 | 0.0 | 0.99310 | 637.00 | 632.60 | 615 | 2.39410 |
| Yoán Moncada | 23.0 | 650 | 0 | 0.0 | 0.97830 | 537.97 | 526.30 | 559 | 4.57716 |
| Nomar Mazara | 23.0 | 536 | 20 | 0.0 | 0.98044 | 542.58 | 531.97 | 469 | 1.77004 |
| Cody Bellinger | 22.0 | 632 | 0 | 0.0 | 0.98263 | 539.54 | 530.17 | 661 | 6.76875 |

## Wenceel Pérez — 2024 to 2025

Player 672761; row 55592; fold 3; age 24.0; Current MLB; snapshot MLB. Selection: pa ordinary, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | AA | 171 | 39 | 5 | 23 | 14 |
| 2022 | Aplus | 236 | 55 | 9 | 38 | 27 |
| 2023 | A | 22 | 5 | 0 | 5 | 1 |
| 2023 | AA | 343 | 76 | 6 | 52 | 35 |
| 2023 | AAA | 160 | 35 | 3 | 29 | 27 |
| 2024 | AAA | 63 | 15 | 2 | 15 | 8 |
| 2024 | MLB | 425 | 112 | 9 | 92 | 32 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 381.668327 | -0.471162 | 0.892680 |
| scout | Not estimated | Not estimated | 383.282818 | -0.471162 | 0.896457 |
| fallback | Not estimated | Not estimated | 381.668327 | -0.471162 | 0.892680 |
| binary_count | 0.962907 | 385.294959 | 371.003093 | -0.471162 | 0.867736 |
| binary_scout | 0.962072 | 393.947082 | 379.005297 | -0.471162 | 0.886452 |
| Actual | 1 | 383 | 383 | 0.3412356590537692 | 1.411256 |

### binary_count: probability and workload accounting

Effective probability 0.96290669 × bounded conditional PA 385.294959 = expected PA 371.003093. Contribution = that PA × (-0.471162/600 + 0.00312416). Raw probability 0.96290669 is preserved separately from any availability override.

participation: reference -4.038431 plus all saved terms = raw 3.256520 log odds; logistic link gives probability 0.96290669. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.838616 log odds |
| games_mlb_0 | 112.0 | 1.660267 log odds |
| work_0 | 425.17496912309593 | 1.285562 log odds |
| games_pool_MLB | 112.0 | 0.373331 log odds |
| pooled_MLB_pa | 425.0 | 0.315605 log odds |
| role_minor_0 | 4.12 | 0.165313 log odds |
| age_squared | 0.36 | 0.119304 log odds |
| games_pool_DSL | 0.0 | 0.103378 log odds |

conditional_pa: reference 277.953209 plus all saved terms = raw 385.294959 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 425.17496912309593 | 99.959675 PA |
| role_mlb_0 | 3.8114754098360657 | -29.103966 PA |
| age_centered | -0.6 | 18.925060 PA |
| regular_window_scaled | 0.3333333333333333 | 14.447673 PA |
| quality_0 | -0.14191357438478308 | -12.761968 PA |
| on_40man | 1.0 | 9.712627 PA |
| pooled_MLB_K | 0.21904761904761905 | 8.126946 PA |
| role_pool_MLB | 3.8114754098360657 | -6.918704 PA |

### binary_scout: probability and workload accounting

Effective probability 0.96207159 × bounded conditional PA 393.947082 = expected PA 379.005297. Contribution = that PA × (-0.471162/600 + 0.00312416). Raw probability 0.96207159 is preserved separately from any availability override.

participation: reference -4.052583 plus all saved terms = raw 3.233389 log odds; logistic link gives probability 0.96207159. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.867602 log odds |
| games_mlb_0 | 112.0 | 1.681142 log odds |
| work_0 | 425.17496912309593 | 1.291987 log odds |
| games_pool_MLB | 112.0 | 0.375744 log odds |
| pooled_MLB_pa | 425.0 | 0.255002 log odds |
| role_minor_0 | 4.12 | 0.163804 log odds |
| age_centered | -0.6 | 0.141441 log odds |
| pooled_AA_K | 0.16436058700209644 | 0.116696 log odds |
| scout_listed_0 | 0.0 | -0.043358 log odds |
| scout_rank_score_2 | 0.0 | 0.004133 log odds |
| scout_rank_score_0 | 0.0 | -0.003210 log odds |
| scout_list_capacity_0 | 100.0 | -0.002181 log odds |

conditional_pa: reference 277.961168 plus all saved terms = raw 393.947082 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 425.17496912309593 | 92.197129 PA |
| role_mlb_0 | 3.8114754098360657 | -28.935339 PA |
| age_centered | -0.6 | 19.419799 PA |
| regular_window_scaled | 0.3333333333333333 | 16.741504 PA |
| quality_0 | -0.14191357438478308 | -14.029808 PA |
| on_40man | 1.0 | 11.425212 PA |
| pooled_MLB_K | 0.21904761904761905 | 8.172579 PA |
| role_pool_MLB | 3.8114754098360657 | -6.454038 PA |
| scout_rank_score_0 | 0.0 | -0.822796 PA |
| scout_rank_score_1 | 0.0 | 0.025568 PA |

Full-population rank profile: [{'row_id': 55592, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 555}]. Active-label conditional profile: [{'row_id': 55592, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 484}].

Actual original-fold general support: [{'row_id': 55592, 'horizon': 1, 'player_id': 672761, 'origin_year': 2024, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 24.0, 'quality_0': -0.14191357438478308, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 1019, 'current_players': 546, 'regular_players': 555, 'joint_players': 24, 'quality_joint_players': 49, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 55592, 'horizon': 1, 'player_id': 672761, 'origin_year': 2024, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 24.0, 'quality_0': -0.14191357438478308, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 799, 'current_players': 537, 'regular_players': 493, 'joint_players': 23, 'quality_joint_players': 48, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 55592, 'horizon': 1, 'player_id': 672761, 'origin_year': 2024, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 24.0, 'quality_0': -0.14191357438478308, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 1019, 'current_players': 546, 'regular_players': 555, 'joint_players': 24, 'quality_joint_players': 49, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 55592, 'horizon': 1, 'player_id': 672761, 'origin_year': 2024, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 24.0, 'quality_0': -0.14191357438478308, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 799, 'current_players': 537, 'regular_players': 493, 'joint_players': 23, 'quality_joint_players': 48, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Perez's 425 MLB PA and prior upper-minor record lead to 96.2% × 394 = 379 expected PA, close to 383 actual; count binary is 371 and direct count 382. Roster/use history dominates probability and recent work dominates conditional PA. This remains an ordinary good workload case rather than a new scouting success, since he has no current rank. Fixed rate -.471 remains below actual +.341, so contribution .886 misses 1.411. A 484-person active profile is populated but comparable Kelenic and Perdomo later span 65 to 720 PA, illustrating individual uncertainty.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nolan Gorman | 24.0 | 402 | 98 | 0.0 | 0.94373 | 349.72 | 330.04 | 402 | 0.56052 |
| Austin Wells | 24.0 | 414 | 0 | 0.0 | 0.98990 | 448.55 | 444.02 | 448 | 1.01665 |
| Jarred Kelenic | 24.0 | 449 | 0 | 0.0 | 0.96305 | 391.76 | 377.28 | 65 | -0.20396 |
| Geraldo Perdomo | 24.0 | 388 | 27 | 0.0 | 0.98037 | 483.99 | 474.49 | 720 | 5.51700 |

## Julio Rodríguez — 2021 to 2022

Player 677594; row 44122; fold 1; age 20.0; Upper minors; snapshot AA. Selection: value largest gain, carried previous review, fallback value largest gain, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | A | 295 | 67 | 10 | 66 | 19 |
| 2019 | Aplus | 72 | 17 | 2 | 10 | 5 |
| 2021 | AA | 206 | 46 | 7 | 37 | 28 |
| 2021 | Aplus | 134 | 28 | 6 | 29 | 14 |

Historical rank rows: [{'season': 2020, 'player_id': 677594, 'rank': 18, 'list_capacity': 99, 'list_complete': False, 'player_name': 'Julio Rodríguez'}, {'season': 2021, 'player_id': 677594, 'rank': 5, 'list_capacity': 99, 'list_complete': False, 'player_name': 'Julio Rodríguez'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 103.107728 | 0.806514 | 0.461839 |
| scout | Not estimated | Not estimated | 284.226078 | 0.806514 | 1.273103 |
| fallback | Not estimated | Not estimated | 284.226078 | 0.806514 | 1.273103 |
| binary_count | 0.673692 | 158.201979 | 106.579359 | 0.806514 | 0.477389 |
| binary_scout | 0.807883 | 291.918827 | 235.836236 | 0.806514 | 1.056356 |
| Actual | 1 | 560 | 560 | 2.683148599795411 | 4.257617 |

### binary_count: probability and workload accounting

Effective probability 0.67369169 × bounded conditional PA 158.201979 = expected PA 106.579359. Contribution = that PA × (0.806514/600 + 0.00313500). Raw probability 0.67369169 is preserved separately from any availability override.

participation: reference -3.998672 plus all saved terms = raw 0.724930 log odds; logistic link gives probability 0.67369169. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.614183 log odds |
| role_pool_AA | 4.392857142857143 | 0.574231 log odds |
| pooled_AA_pa | 206.0 | 0.380917 log odds |
| games_mlb_0 | 0.0 | -0.336206 log odds |
| work_0 | 0.0 | -0.289625 log odds |
| role_minor_0 | 4.523809523809524 | 0.268518 log odds |
| games_pool_MLB | 0.0 | -0.245533 log odds |
| age_centered | -1.4 | 0.216929 log odds |

conditional_pa: reference 285.282036 plus all saved terms = raw 158.201979 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -107.548976 PA |
| age_centered | -1.4 | 21.576998 PA |
| quality_0 | 0.0 | -14.121701 PA |
| pooled_MLB_pa | 0.0 | -10.980405 PA |
| role_minor_0 | 4.523809523809524 | 10.454416 PA |
| on_40man | 1.0 | 10.334157 PA |
| role_pool_AAA | 4.0 | -10.036074 PA |
| career_mlb_observed_pa | 0.0 | -9.876239 PA |

### binary_scout: probability and workload accounting

Effective probability 0.80788293 × bounded conditional PA 291.918827 = expected PA 235.836236. Contribution = that PA × (0.806514/600 + 0.00313500). Raw probability 0.80788293 is preserved separately from any availability override.

participation: reference -4.003406 plus all saved terms = raw 1.436312 log odds; logistic link gives probability 0.80788293. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.638125 log odds |
| scout_rank_score_0 | 0.96 | 0.791240 log odds |
| role_pool_AA | 4.392857142857143 | 0.592788 log odds |
| pooled_AA_pa | 206.0 | 0.380288 log odds |
| games_mlb_0 | 0.0 | -0.334090 log odds |
| work_0 | 0.0 | -0.287803 log odds |
| role_minor_0 | 4.523809523809524 | 0.264099 log odds |
| games_pool_MLB | 0.0 | -0.241726 log odds |

conditional_pa: reference 285.306368 plus all saved terms = raw 291.918827 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.96 | 144.067840 PA |
| work_0 | 0.0 | -102.880012 PA |
| role_minor_0 | 4.523809523809524 | 15.145518 PA |
| quality_0 | 0.0 | -13.974593 PA |
| pooled_MLB_pa | 0.0 | -10.656039 PA |
| on_40man | 1.0 | 9.142164 PA |
| MLB_0_pa | 0.0 | -8.989246 PA |
| regular_window_scaled | 0.0 | -8.752864 PA |

Full-population rank profile: [{'row_id': 44122, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 16}]. Active-label conditional profile: [{'row_id': 44122, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 14}].

Actual original-fold general support: [{'row_id': 44122, 'horizon': 1, 'player_id': 677594, 'origin_year': 2021, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 9307, 'current_players': 9836, 'regular_players': 9920, 'joint_players': 7588, 'quality_joint_players': 9389, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 44122, 'horizon': 1, 'player_id': 677594, 'origin_year': 2021, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 718, 'current_players': 833, 'regular_players': 1080, 'joint_players': 272, 'quality_joint_players': 744, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 44122, 'horizon': 1, 'player_id': 677594, 'origin_year': 2021, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 9307, 'current_players': 9836, 'regular_players': 9920, 'joint_players': 7588, 'quality_joint_players': 9389, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 44122, 'horizon': 1, 'player_id': 677594, 'origin_year': 2021, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 718, 'current_players': 833, 'regular_players': 1080, 'joint_players': 272, 'quality_joint_players': 744, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Rodriguez's rank 5 and meaningful Aplus/AA production raise participation 67.4% to 80.8% and conditional PA 158 to 292, moving expected PA 107 to 236 versus actual 560. It is a readiness gain over direct count 103, but lower than rank-direct 284. The active ranked profile has only fourteen people and conditional use still compresses a possible regular season. The fixed batting rate understates actual talent, so delivered 1.056 remains far below 4.258. Abrams/Greene/Torkelson/Casas expose both varying use and varying batting; canceled 2020 production stays missing, while its positive ranking remains separately observed.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CJ Abrams | 20.0 | 0 | 183 | 0.93 | 0.31499 | 309.15 | 97.38 | 302 | -0.10310 |
| Riley Greene | 20.0 | 0 | 558 | 0.8 | 0.45904 | 374.58 | 171.95 | 418 | 1.15395 |
| Spencer Torkelson | 21.0 | 0 | 530 | 0.98 | 0.52553 | 376.25 | 197.73 | 404 | 0.07614 |
| Triston Casas | 21.0 | 0 | 371 | 0.57 | 0.32009 | 208.41 | 66.71 | 95 | 0.57970 |

## Pete Alonso — 2018 to 2019

Player 624413; row 33263; fold 1; age 23.0; Upper minors; snapshot AAA. Selection: value largest harm, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 30 | 5 | 22 | 11 |
| 2017 | AA | 47 | 11 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 82 | 16 | 64 | 24 |
| 2018 | AA | 273 | 65 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 67 | 21 | 78 | 33 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2016/64; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 215.230347 | 0.259881 | 0.755868 |
| scout | Not estimated | Not estimated | 154.981682 | 0.259881 | 0.544281 |
| fallback | Not estimated | Not estimated | 215.230347 | 0.259881 | 0.755868 |
| binary_count | 0.693749 | 182.093974 | 126.327526 | 0.259881 | 0.443650 |
| binary_scout | 0.729998 | 180.189571 | 131.538003 | 0.259881 | 0.461949 |
| Actual | 1 | 693 | 693 | 3.2827570240246495 | 5.908536 |

### binary_count: probability and workload accounting

Effective probability 0.69374907 × bounded conditional PA 182.093974 = expected PA 126.327526. Contribution = that PA × (0.259881/600 + 0.00307877). Raw probability 0.69374907 is preserved separately from any availability override.

participation: reference -4.028406 plus all saved terms = raw 0.817706 log odds; logistic link gives probability 0.69374907. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_minor_0 | 132.0 | 0.951473 log odds |
| role_pool_AA | 4.183770883054893 | 0.927717 log odds |
| pooled_AA_pa | 310.6 | 0.754290 log odds |
| draft_rank | 0.4528435135832247 | 0.505582 log odds |
| on_40man | 0.0 | -0.466467 log odds |
| role_minor_0 | 4.323943661971831 | 0.372902 log odds |
| AAA_0_pa | 301.0 | 0.363147 log odds |
| games_mlb_0 | 0.0 | -0.251061 log odds |

conditional_pa: reference 287.111316 plus all saved terms = raw 182.093974 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -68.607918 PA |
| work_0 | 0.0 | -45.649877 PA |
| role_pool_AAA | 4.428571428571429 | 38.511222 PA |
| pooled_AAA_HR | 0.059850374064837904 | 30.178237 PA |
| on_40man | 0.0 | -20.105929 PA |
| pooled_Aplus_2B | 0.062101910828025485 | 16.198473 PA |
| pooled_AA_HR | 0.047735021919142716 | 15.448871 PA |
| quality_0 | 0.0 | -14.607577 PA |

### binary_scout: probability and workload accounting

Effective probability 0.72999787 × bounded conditional PA 180.189571 = expected PA 131.538003. Contribution = that PA × (0.259881/600 + 0.00307877). Raw probability 0.72999787 is preserved separately from any availability override.

participation: reference -4.016897 plus all saved terms = raw 0.994612 log odds; logistic link gives probability 0.72999787. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_minor_0 | 132.0 | 0.940309 log odds |
| role_pool_AA | 4.183770883054893 | 0.929111 log odds |
| pooled_AA_pa | 310.6 | 0.739122 log odds |
| draft_rank | 0.4528435135832247 | 0.475152 log odds |
| on_40man | 0.0 | -0.466778 log odds |
| role_minor_0 | 4.323943661971831 | 0.399470 log odds |
| AAA_0_pa | 301.0 | 0.348075 log odds |
| games_mlb_0 | 0.0 | -0.243710 log odds |
| scout_rank_score_0 | 0.0 | -0.011918 log odds |

conditional_pa: reference 287.124657 plus all saved terms = raw 180.189571 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -66.383899 PA |
| work_0 | 0.0 | -42.475826 PA |
| role_pool_AAA | 4.428571428571429 | 35.617899 PA |
| pooled_AAA_HR | 0.059850374064837904 | 28.201341 PA |
| on_40man | 0.0 | -21.980379 PA |
| quality_0 | 0.0 | -16.179767 PA |
| pooled_Aplus_2B | 0.062101910828025485 | 14.026520 PA |
| pooled_AA_HR | 0.047735021919142716 | 13.319818 PA |
| scout_rank_score_0 | 0.0 | -6.302579 PA |
| scout_rank_score_2 | 0.0 | 0.042316 PA |
| scout_rank_score_1 | 0.0 | 0.019471 PA |

Full-population rank profile: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 1417}]. Active-label conditional profile: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 288}].

Actual original-fold general support: [{'row_id': 33263, 'horizon': 1, 'player_id': 624413, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 7455, 'current_players': 7925, 'regular_players': 8044, 'joint_players': 2929, 'quality_joint_players': 7535, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 33263, 'horizon': 1, 'player_id': 624413, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 551, 'current_players': 652, 'regular_players': 853, 'joint_players': 275, 'quality_joint_players': 573, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 33263, 'horizon': 1, 'player_id': 624413, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 7455, 'current_players': 7925, 'regular_players': 8044, 'joint_players': 2929, 'quality_joint_players': 7535, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 33263, 'horizon': 1, 'player_id': 624413, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 551, 'current_players': 652, 'regular_players': 853, 'joint_players': 275, 'quality_joint_players': 573, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Alonso's 36 AA/AAA homers and 574 PA lead to a fairly high 73.0% arrival probability, but only 180 conditional PA, yielding 132 expected versus actual 693. Thus his central miss is not just failure to identify eventual arrival: use conditional on arrival is too cautious as well. Count binary 126 and scouting binary 132 both lose to direct count 215. No current positive ranking captures his in-season rise. Fixed .260 batting wins/600 also understates actual 3.283. Edman, Thaiss, Rooker and Lopez range 0 to 402 PA; aggregate participant support 288 is broad and does not establish his elite power/MLB-starting-role combination.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tommy Edman | 23.0 | 0 | 574 | 0.0 | 0.52525 | 146.46 | 76.93 | 349 | 2.23511 |
| Matt Thaiss | 23.0 | 0 | 576 | 0.0 | 0.48917 | 184.15 | 90.08 | 164 | 0.30654 |
| Brent Rooker | 23.0 | 0 | 568 | 0.0 | 0.21150 | 125.75 | 26.60 | 0 | 0.00000 |
| Nicky Lopez | 23.0 | 0 | 581 | 0.0 | 0.51530 | 135.56 | 69.85 | 402 | -0.83941 |

## Yordan Alvarez — 2024 to 2025

Player 670541; row 55521; fold 2; age 27.0; Current MLB; snapshot MLB. Selection: value false high, carried previous review, fallback value false high, fixed previous diagnostic, binary_scout value false high.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 561 | 135 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 3 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 114 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 147 | 35 | 95 | 53 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 577.490453 | 3.709704 | 5.374704 |
| scout | Not estimated | Not estimated | 579.416612 | 3.709704 | 5.392630 |
| fallback | Not estimated | Not estimated | 577.490453 | 3.709704 | 5.374704 |
| binary_count | 0.990789 | 551.488065 | 546.408559 | 3.709704 | 5.085425 |
| binary_scout | 0.990115 | 559.774972 | 554.241843 | 3.709704 | 5.158329 |
| Actual | 1 | 199 | 199 | 0.919648372891386 | 0.925104 |

### binary_count: probability and workload accounting

Effective probability 0.99078945 × bounded conditional PA 551.488065 = expected PA 546.408559. Contribution = that PA × (3.709704/600 + 0.00312416). Raw probability 0.99078945 is preserved separately from any availability override.

participation: reference -4.010355 plus all saved terms = raw 4.678153 log odds; logistic link gives probability 0.99078945. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.634787 log odds |
| games_mlb_0 | 147.0 | 1.909590 log odds |
| games_pool_MLB | 319.2 | 0.940142 log odds |
| work_0 | 635.2614244545081 | 0.909201 log odds |
| pooled_mlb_quality | 2.457088938891907 | 0.578239 log odds |
| quality_0 | 1.415653196303136 | 0.453143 log odds |
| pooled_MLB_pa | 1368.4 | 0.335480 log odds |
| MLB_0_pa | 635.0 | 0.318785 log odds |

conditional_pa: reference 278.570242 plus all saved terms = raw 551.488065 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 635.2614244545081 | 146.829557 PA |
| role_mlb_0 | 4.2993630573248405 | 29.877298 PA |
| quality_0 | 1.415653196303136 | 27.557096 PA |
| role_pool_MLB | 4.278250303766707 | 25.664603 PA |
| MLB_0_pa | 635.0 | 17.950102 PA |
| regular_window_scaled | 1.0 | 15.983061 PA |
| pooled_mlb_quality | 2.457088938891907 | 15.275029 PA |
| pooled_MLB_K | 0.17379460637428493 | 8.633244 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99011544 × bounded conditional PA 559.774972 = expected PA 554.241843. Contribution = that PA × (3.709704/600 + 0.00312416). Raw probability 0.99011544 is preserved separately from any availability override.

participation: reference -4.018196 plus all saved terms = raw 4.606848 log odds; logistic link gives probability 0.99011544. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.681356 log odds |
| games_mlb_0 | 147.0 | 1.883116 log odds |
| work_0 | 635.2614244545081 | 0.957277 log odds |
| games_pool_MLB | 319.2 | 0.908016 log odds |
| pooled_mlb_quality | 2.457088938891907 | 0.503557 log odds |
| quality_0 | 1.415653196303136 | 0.470645 log odds |
| pooled_MLB_pa | 1368.4 | 0.336373 log odds |
| MLB_0_pa | 635.0 | 0.318785 log odds |
| scout_listed_0 | 0.0 | -0.028212 log odds |
| scout_list_capacity_0 | 100.0 | -0.025783 log odds |
| scout_rank_score_0 | 0.0 | -0.004107 log odds |
| scout_rank_score_2 | 0.0 | 0.000841 log odds |

conditional_pa: reference 278.535732 plus all saved terms = raw 559.774972 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 635.2614244545081 | 145.888330 PA |
| role_mlb_0 | 4.2993630573248405 | 31.040920 PA |
| quality_0 | 1.415653196303136 | 29.452773 PA |
| role_pool_MLB | 4.278250303766707 | 23.293162 PA |
| pooled_mlb_quality | 2.457088938891907 | 18.193403 PA |
| MLB_0_pa | 635.0 | 17.989611 PA |
| regular_window_scaled | 1.0 | 13.873328 PA |
| pooled_MLB_K | 0.17379460637428493 | 9.306875 PA |
| scout_rank_score_0 | 0.0 | -0.779457 PA |
| scout_rank_score_1 | 0.0 | -0.126640 PA |
| scout_listed_0 | 0.0 | -0.060453 PA |

Full-population rank profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'rank_profile_players': 1078}]. Active-label conditional profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 844}].

Actual original-fold general support: [{'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 903, 'current_players': 538, 'regular_players': 310, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 406, 'current_players': 530, 'regular_players': 306, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 903, 'current_players': 538, 'regular_players': 310, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 55521, 'horizon': 1, 'player_id': 670541, 'origin_year': 2024, 'elapsed': 5, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': 1.415653196303136, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 2, 'elapsed_players': 406, 'current_players': 530, 'regular_players': 306, 'joint_players': 261, 'quality_joint_players': 82, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Alvarez's 635 MLB PA and elite prior power/contact support 99.0% appearance probability and 560 conditional PA, 554 expected. He does appear but produces only 199 PA and .925 contribution; expected 5.158 is still the scouting arm's largest value false high. Binary structure reduces the original 577 mean slightly, not enough to model this exposure loss. Probability of any appearance is not probability of being healthy all season. His strong origin record is real and the source does not authorize inserting a future injury explanation. Populated active support and regular peers leave substantial workload/talent uncertainty.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rafael Devers | 27.0 | 601 | 0 | 0.0 | 0.99340 | 556.73 | 553.05 | 729 | 5.23429 |
| Jonathan India | 27.0 | 637 | 0 | 0.0 | 0.99262 | 558.59 | 554.47 | 567 | 1.28649 |
| Brendan Donovan | 27.0 | 652 | 0 | 0.0 | 0.99233 | 574.21 | 569.81 | 515 | 2.59344 |
| Alec Bohm | 27.0 | 606 | 4 | 0.0 | 0.99378 | 568.10 | 564.57 | 504 | 2.05959 |

## Adeiny Hechavarría — 2016 to 2017

Player 588751; row 23878; fold 1; age 27.0; Current MLB; snapshot MLB. Selection: value ordinary, carried previous review, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | Aplus | 8 | 2 | 0 | 1 | 0 |
| 2014 | MLB | 574 | 146 | 1 | 86 | 21 |
| 2015 | MLB | 499 | 130 | 5 | 78 | 19 |
| 2016 | MLB | 547 | 155 | 3 | 73 | 26 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 388.321569 | -1.355283 | 0.322030 |
| scout | Not estimated | Not estimated | 391.865348 | -1.355283 | 0.324968 |
| fallback | Not estimated | Not estimated | 388.321569 | -1.355283 | 0.322030 |
| binary_count | 0.978770 | 396.697489 | 388.275731 | -1.355283 | 0.321992 |
| binary_scout | 0.977939 | 380.490049 | 372.096147 | -1.355283 | 0.308574 |
| Actual | 1 | 348 | 348 | -1.2852206812068887 | 0.325081 |

### binary_count: probability and workload accounting

Effective probability 0.97877033 × bounded conditional PA 396.697489 = expected PA 388.275731. Contribution = that PA × (-1.355283/600 + 0.00308809). Raw probability 0.97877033 is preserved separately from any availability override.

participation: reference -3.975737 plus all saved terms = raw 3.830897 log odds; logistic link gives probability 0.97877033. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.741751 log odds |
| games_mlb_0 | 155.0 | 1.513861 log odds |
| games_mlb_1 | 130.0 | 0.631033 log odds |
| MLB_0_pa | 547.0 | 0.588518 log odds |
| pooled_MLB_pa | 1290.6 | 0.509918 log odds |
| position_6 | 1.0 | 0.254422 log odds |
| pooled_mlb_quality | -0.9273659604842267 | -0.198628 log odds |
| games_pool_MLB | 346.6 | 0.189328 log odds |

conditional_pa: reference 283.404219 plus all saved terms = raw 396.697489 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 547.0 | 146.501324 PA |
| quality_0 | -0.978461962097713 | -46.200923 PA |
| role_mlb_0 | 3.5575757575757576 | -43.535615 PA |
| games_mlb_2 | 146.0 | 18.146892 PA |
| role_pool_MLB | 3.731351654514862 | -15.676333 PA |
| pooled_MLB_HR | 0.007622608945778801 | -15.292029 PA |
| pooled_mlb_quality | -0.9273659604842267 | -14.482879 PA |
| pooled_MLB_3B | 0.012440673090752195 | 13.779475 PA |

### binary_scout: probability and workload accounting

Effective probability 0.97793923 × bounded conditional PA 380.490049 = expected PA 372.096147. Contribution = that PA × (-1.355283/600 + 0.00308809). Raw probability 0.97793923 is preserved separately from any availability override.

participation: reference -3.979519 plus all saved terms = raw 3.791647 log odds; logistic link gives probability 0.97793923. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.738433 log odds |
| games_mlb_0 | 155.0 | 1.554150 log odds |
| pooled_MLB_pa | 1290.6 | 0.546832 log odds |
| MLB_0_pa | 547.0 | 0.534997 log odds |
| games_mlb_1 | 130.0 | 0.506358 log odds |
| position_6 | 1.0 | 0.261648 log odds |
| pooled_mlb_quality | -0.9273659604842267 | -0.201064 log odds |
| games_pool_MLB | 346.6 | 0.200278 log odds |
| scout_rank_score_0 | 0.0 | -0.004238 log odds |
| scout_listed_0 | 0.0 | -0.000930 log odds |

conditional_pa: reference 283.426060 plus all saved terms = raw 380.490049 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 547.0 | 127.997869 PA |
| quality_0 | -0.978461962097713 | -45.074028 PA |
| role_mlb_0 | 3.5575757575757576 | -42.223069 PA |
| games_mlb_2 | 146.0 | 26.571297 PA |
| role_pool_MLB | 3.731351654514862 | -16.469474 PA |
| pooled_mlb_quality | -0.9273659604842267 | -14.908070 PA |
| regular_window_scaled | 1.0 | 12.993972 PA |
| pooled_MLB_HR | 0.007622608945778801 | -12.278559 PA |
| scout_rank_score_0 | 0.0 | -0.444392 PA |

Full-population rank profile: [{'row_id': 23878, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'rank_profile_players': 553}]. Active-label conditional profile: [{'row_id': 23878, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 428}].

Actual original-fold general support: [{'row_id': 23878, 'horizon': 1, 'player_id': 588751, 'origin_year': 2016, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': -0.978461962097713, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 317, 'regular_players': 179, 'joint_players': 125, 'quality_joint_players': 242, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 23878, 'horizon': 1, 'player_id': 588751, 'origin_year': 2016, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': -0.978461962097713, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 198, 'current_players': 311, 'regular_players': 176, 'joint_players': 125, 'quality_joint_players': 237, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 23878, 'horizon': 1, 'player_id': 588751, 'origin_year': 2016, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': -0.978461962097713, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 388, 'current_players': 317, 'regular_players': 179, 'joint_players': 125, 'quality_joint_players': 242, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 23878, 'horizon': 1, 'player_id': 588751, 'origin_year': 2016, 'elapsed': 4, 'current_state': 3, 'regular_window': 3, 'age': 27.0, 'quality_0': -0.978461962097713, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 198, 'current_players': 311, 'regular_players': 176, 'joint_players': 125, 'quality_joint_players': 237, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Hechavarria's extensive MLB use yields 97.8% × 380 = 372 expected PA versus 348 actual, closer than direct count 388. But contribution .309 slightly misses .325 because the fixed batting rate is somewhat low. Count binary produces 388 and nearly exact .322 through an offset, not superior component accuracy. This ordinary case shows how a workload improvement can modestly worsen the product. No rank-specific player evidence is added; 428 active-profile people and peers establish broad coverage, not certainty.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Marwin Gonzalez | 27.0 | 518 | 0 | 0.0 | 0.97924 | 359.73 | 352.27 | 515 | 4.14189 |
| Kevin Pillar | 27.0 | 584 | 9 | 0.0 | 0.97409 | 459.25 | 447.35 | 632 | 1.06308 |
| Derek Norris | 27.0 | 458 | 0 | 0.0 | 0.98357 | 342.86 | 337.23 | 198 | -0.15537 |
| Corey Dickerson | 27.0 | 548 | 0 | 0.0 | 0.98628 | 437.64 | 431.64 | 629 | 2.97277 |

## Marcelo Mayer — 2023 to 2024

Player 691785; row 52883; fold 1; age 20.0; Upper minors; snapshot AA. Selection: fallback pa largest harm, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | RK124 | 107 | 26 | 3 | 27 | 15 |
| 2022 | A | 308 | 66 | 9 | 78 | 49 |
| 2022 | Aplus | 116 | 25 | 4 | 29 | 16 |
| 2023 | AA | 190 | 43 | 6 | 49 | 15 |
| 2023 | Aplus | 164 | 35 | 7 | 37 | 17 |

Historical rank rows: [{'season': 2022, 'player_id': 691785, 'rank': 14, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Marcelo Mayer'}, {'season': 2023, 'player_id': 691785, 'rank': 9, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Marcelo Mayer'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2021/4; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 44.841167 | -0.181534 | 0.125265 |
| scout | Not estimated | Not estimated | 255.972191 | -0.181534 | 0.715063 |
| fallback | Not estimated | Not estimated | 255.972191 | -0.181534 | 0.715063 |
| binary_count | 0.370566 | 207.398282 | 76.854738 | -0.181534 | 0.214695 |
| binary_scout | 0.586157 | 321.251239 | 188.303583 | -0.181534 | 0.526030 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.37056593 × bounded conditional PA 207.398282 = expected PA 76.854738. Contribution = that PA × (-0.181534/600 + 0.00309608). Raw probability 0.37056593 is preserved separately from any availability override.

participation: reference -4.013216 plus all saved terms = raw -0.529790 log odds; logistic link gives probability 0.37056593. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.339622641509434 | 0.975825 log odds |
| draft_rank | 0.8176145045277415 | 0.949019 log odds |
| pooled_AA_pa | 190.0 | 0.724918 log odds |
| role_minor_0 | 4.4772727272727275 | 0.519347 log odds |
| on_40man | 0.0 | -0.370528 log odds |
| games_mlb_0 | 0.0 | -0.259627 log odds |
| role_pool_A | 4.560509554140126 | 0.229051 log odds |
| pooled_AA_HR | 0.03103448275862069 | 0.228597 log odds |

conditional_pa: reference 283.918062 plus all saved terms = raw 207.398282 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -96.687501 PA |
| age_centered | -1.4 | 26.325764 PA |
| on_40man | 0.0 | -23.128706 PA |
| role_pool_AA | 4.339622641509434 | 19.931773 PA |
| draft_rank | 0.8176145045277415 | 17.271135 PA |
| role_minor_0 | 4.4772727272727275 | 16.700172 PA |
| role_pool_AAA | 4.0 | -14.634072 PA |
| draft_rank_low_exposure | 0.08300654868301945 | 13.779989 PA |

### binary_scout: probability and workload accounting

Effective probability 0.58615675 × bounded conditional PA 321.251239 = expected PA 188.303583. Contribution = that PA × (-0.181534/600 + 0.00309608). Raw probability 0.58615675 is preserved separately from any availability override.

participation: reference -3.995122 plus all saved terms = raw 0.348100 log odds; logistic link gives probability 0.58615675. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| role_pool_AA | 4.339622641509434 | 0.901380 log odds |
| scout_rank_score_0 | 0.92 | 0.827315 log odds |
| draft_rank | 0.8176145045277415 | 0.751945 log odds |
| pooled_AA_pa | 190.0 | 0.733248 log odds |
| role_minor_0 | 4.4772727272727275 | 0.473090 log odds |
| scout_listed_0 | 1.0 | 0.444720 log odds |
| on_40man | 0.0 | -0.366505 log odds |
| games_mlb_0 | 0.0 | -0.264419 log odds |

conditional_pa: reference 283.918351 plus all saved terms = raw 321.251239 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.92 | 146.976748 PA |
| work_0 | 0.0 | -98.713688 PA |
| on_40man | 0.0 | -22.784554 PA |
| pooled_MLB_HBP | 0.01 | 18.288260 PA |
| role_pool_AA | 4.339622641509434 | 14.786480 PA |
| role_minor_0 | 4.4772727272727275 | 14.219489 PA |
| draft_rank_low_exposure | 0.08300654868301945 | 13.417380 PA |
| quality_0 | 0.0 | -12.946816 PA |
| scout_listed_0 | 1.0 | 5.550399 PA |
| scout_rank_score_1 | 0.87 | -4.746878 PA |

Full-population rank profile: [{'row_id': 52883, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 22}]. Active-label conditional profile: [{'row_id': 52883, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 19}].

Actual original-fold general support: [{'row_id': 52883, 'horizon': 1, 'player_id': 691785, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10795, 'current_players': 11330, 'regular_players': 11413, 'joint_players': 8928, 'quality_joint_players': 10878, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 52883, 'horizon': 1, 'player_id': 691785, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 923, 'current_players': 1042, 'regular_players': 1288, 'joint_players': 346, 'quality_joint_players': 952, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 52883, 'horizon': 1, 'player_id': 691785, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 10795, 'current_players': 11330, 'regular_players': 11413, 'joint_players': 8928, 'quality_joint_players': 10878, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 52883, 'horizon': 1, 'player_id': 691785, 'origin_year': 2023, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 20.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 923, 'current_players': 1042, 'regular_players': 1288, 'joint_players': 346, 'quality_joint_players': 952, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Mayer's rank 9, fourth draft pick and AA advancement produce 58.6% appearance probability and 321 conditional PA, 188 expected versus zero actual. This is lower than rank-direct 256 but much higher than count-direct 45 or count binary 77. The model now makes delay/non-arrival risk explicit rather than assuming a job, but still overpredicts this year. Only nineteen active-label people match the coarse ranked profile. Merrill/Wood arrive with 593/336 PA while Cartaya/Montgomery have none, so one failed annual forecast is not proof Mayer lacked talent; it is evidence that quality and timing remain uncertain. No injury cause is inferred from the stats alone.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jackson Merrill | 20.0 | 0 | 511 | 0.82 | 0.63374 | 246.95 | 156.50 | 593 | 3.78481 |
| James Wood | 20.0 | 0 | 549 | 0.84 | 0.63658 | 259.07 | 164.92 | 336 | 1.97080 |
| Diego Cartaya | 21.0 | 0 | 403 | 0.87 | 0.88869 | 240.62 | 213.84 | 0 | 0.00000 |
| Colson Montgomery | 21.0 | 0 | 294 | 0.63 | 0.34091 | 259.26 | 88.38 | 0 | 0.00000 |

## Mark Vientos — 2022 to 2023

Player 668901; row 47453; fold 4; age 22.0; Current MLB; snapshot MLB. Selection: fallback pa ordinary, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | AA | 306 | 72 | 22 | 87 | 24 |
| 2021 | AAA | 43 | 11 | 3 | 13 | 7 |
| 2022 | AAA | 427 | 101 | 24 | 122 | 42 |
| 2022 | MLB | 41 | 16 | 1 | 12 | 5 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2017/59; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 232.805850 | 0.229263 | 0.817865 |
| scout | Not estimated | Not estimated | 172.796544 | 0.229263 | 0.607048 |
| fallback | Not estimated | Not estimated | 232.805850 | 0.229263 | 0.817865 |
| binary_count | 0.870849 | 210.789636 | 183.566041 | 0.229263 | 0.644882 |
| binary_scout | 0.759519 | 177.237125 | 134.615004 | 0.229263 | 0.472913 |
| Actual | 1 | 233 | 233 | -2.460199612587475 | -0.233992 |

### binary_count: probability and workload accounting

Effective probability 0.87084946 × bounded conditional PA 210.789636 = expected PA 183.566041. Contribution = that PA × (0.229263/600 + 0.00313097). Raw probability 0.87084946 is preserved separately from any availability override.

participation: reference -4.068418 plus all saved terms = raw 1.908490 log odds; logistic link gives probability 0.87084946. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.351755 log odds |
| games_mlb_0 | 16.0 | 0.666841 log odds |
| absence_window_scaled | 0.6666666666666666 | 0.495903 log odds |
| pooled_AA_HR | 0.05974477958236659 | 0.236661 log odds |
| MLB_0_pa | 41.0 | 0.232240 log odds |
| games_minor_0 | 101.0 | 0.212157 log odds |
| role_minor_0 | 4.207207207207207 | 0.180216 log odds |
| AAA_0_pa | 427.0 | 0.164948 log odds |

conditional_pa: reference 278.648619 plus all saved terms = raw 210.789636 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 41.0 | -92.627555 PA |
| pooled_AAA_HR | 0.05236907730673317 | 18.426496 PA |
| age_squared | 1.0 | 16.705979 PA |
| age_centered | -1.0 | 16.275742 PA |
| pooled_AA_HR | 0.05974477958236659 | 14.894719 PA |
| role_pool_AAA | 4.185308848080133 | 12.063877 PA |
| pooled_mlb_quality | -0.09168674909762936 | -9.966246 PA |
| pooled_MLB_pa | 41.0 | -9.042316 PA |

### binary_scout: probability and workload accounting

Effective probability 0.75951923 × bounded conditional PA 177.237125 = expected PA 134.615004. Contribution = that PA × (0.229263/600 + 0.00313097). Raw probability 0.75951923 is preserved separately from any availability override.

participation: reference -4.073125 plus all saved terms = raw 1.150045 log odds; logistic link gives probability 0.75951923. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.338389 log odds |
| games_mlb_0 | 16.0 | 0.642714 log odds |
| absence_window_scaled | 0.6666666666666666 | 0.486030 log odds |
| MLB_0_pa | 41.0 | 0.277785 log odds |
| pooled_AA_HR | 0.05974477958236659 | 0.216686 log odds |
| pooled_AAA_pa | 461.4 | 0.164878 log odds |
| role_minor_0 | 4.207207207207207 | 0.162301 log odds |
| pooled_MLB_pa | 41.0 | -0.154728 log odds |
| scout_listed_0 | 0.0 | -0.079605 log odds |
| scout_rank_score_0 | 0.0 | -0.007612 log odds |

conditional_pa: reference 278.685578 plus all saved terms = raw 177.237125 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 41.0 | -90.997594 PA |
| pooled_AAA_HR | 0.05236907730673317 | 14.218395 PA |
| age_squared | 1.0 | 11.490307 PA |
| pooled_mlb_quality | -0.09168674909762936 | -10.253179 PA |
| age_centered | -1.0 | 9.788862 PA |
| role_pool_AAA | 4.185308848080133 | 9.203711 PA |
| pooled_AA_HR | 0.05974477958236659 | 9.145690 PA |
| on_40man | 1.0 | 8.290604 PA |
| scout_rank_score_0 | 0.0 | -5.000436 PA |

Full-population rank profile: [{'row_id': 47453, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 403}]. Active-label conditional profile: [{'row_id': 47453, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 351}].

Actual original-fold general support: [{'row_id': 47453, 'horizon': 1, 'player_id': 668901, 'origin_year': 2022, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.09168674909762936, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 788, 'current_players': 1166, 'regular_players': 10685, 'joint_players': 136, 'quality_joint_players': 633, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 47453, 'horizon': 1, 'player_id': 668901, 'origin_year': 2022, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.09168674909762936, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 623, 'current_players': 841, 'regular_players': 1216, 'joint_players': 119, 'quality_joint_players': 478, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 47453, 'horizon': 1, 'player_id': 668901, 'origin_year': 2022, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.09168674909762936, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 788, 'current_players': 1166, 'regular_players': 10685, 'joint_players': 136, 'quality_joint_players': 633, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 47453, 'horizon': 1, 'player_id': 668901, 'origin_year': 2022, 'elapsed': 0, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.09168674909762936, 'elapsed_band': 0, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 623, 'current_players': 841, 'regular_players': 1216, 'joint_players': 119, 'quality_joint_players': 478, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Vientos's 427 AAA PA with 24 HR and a 41-PA MLB debut produce 76.0% × 177 = 135 expected PA in the scouting model versus 233 actual. Count binary 184 also loses the nearly exact direct count 233. Adding the stale unlisted rank panel lowers both probability and use; the broad active profile is not equivalent to this specific power hitter's readiness. Contribution .473 is less wrong than .818 but only because reduced PA offsets an optimistic fixed rate; observed contribution is negative. Lower output must not be called a better talent estimate.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jihwan Bae | 22.0 | 37 | 473 | 0.0 | 0.53577 | 220.67 | 118.23 | 371 | -0.30172 |
| Heliot Ramos | 22.0 | 22 | 475 | 0.0 | 0.76827 | 162.57 | 124.89 | 60 | -0.21617 |
| Logan O'Hoppe | 22.0 | 16 | 447 | 0.0 | 0.87157 | 142.21 | 123.94 | 199 | 0.94749 |
| Israel Pineda | 22.0 | 14 | 400 | 0.0 | 0.84987 | 129.89 | 110.39 | 0 | 0.00000 |

## Ethan Salas — 2024 to 2025

Player 806956; row 57694; fold 3; age 18.0; Lower minors; snapshot HIGH_A. Selection: lower ranked false high, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2023 | A | 220 | 48 | 9 | 57 | 24 |
| 2023 | AA | 33 | 9 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 9 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 111 | 4 | 98 | 47 |

Historical rank rows: [{'season': 2024, 'player_id': 806956, 'rank': 8, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Ethan Salas'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 0.000000 | -0.447557 | 0.000000 |
| scout | Not estimated | Not estimated | 231.522186 | -0.447557 | 0.550613 |
| fallback | Not estimated | Not estimated | 231.522186 | -0.447557 | 0.550613 |
| binary_count | 0.010938 | 88.134636 | 0.963992 | -0.447557 | 0.002293 |
| binary_scout | 0.025652 | 278.309347 | 7.139187 | -0.447557 | 0.016979 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.01093772 × bounded conditional PA 88.134636 = expected PA 0.963992. Contribution = that PA × (-0.447557/600 + 0.00312416). Raw probability 0.01093772 is preserved separately from any availability override.

participation: reference -4.038431 plus all saved terms = raw -4.504540 log odds; logistic link gives probability 0.01093772. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_minor_0 | 111.0 | 0.401733 log odds |
| role_pool_A | 4.462809917355371 | 0.380011 log odds |
| on_40man | 0.0 | -0.378406 log odds |
| games_mlb_0 | 0.0 | -0.294401 log odds |
| position_2 | 1.0 | 0.269507 log odds |
| age_squared | 3.24 | -0.268026 log odds |
| role_minor_0 | 4.206611570247934 | 0.166348 log odds |
| pooled_AA_pa | 26.400000000000002 | -0.142827 log odds |

conditional_pa: reference 277.953209 plus all saved terms = raw 88.134636 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -94.840402 PA |
| age_centered | -1.8 | 31.305940 PA |
| on_40man | 0.0 | -23.110222 PA |
| role_pool_AAA | 4.0 | -16.105670 PA |
| games_pool_Aplus | 118.2 | -11.692378 PA |
| quality_0 | 0.0 | -10.182311 PA |
| regular_window_scaled | 0.0 | -10.091009 PA |
| pooled_A_K | 0.24855072463768113 | -9.547319 PA |

### binary_scout: probability and workload accounting

Effective probability 0.02565198 × bounded conditional PA 278.309347 = expected PA 7.139187. Contribution = that PA × (-0.447557/600 + 0.00312416). Raw probability 0.02565198 is preserved separately from any availability override.

participation: reference -4.052583 plus all saved terms = raw -3.637148 log odds; logistic link gives probability 0.02565198. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.93 | 0.524839 log odds |
| games_minor_0 | 111.0 | 0.415180 log odds |
| on_40man | 0.0 | -0.378495 log odds |
| scout_listed_0 | 1.0 | 0.307557 log odds |
| games_mlb_0 | 0.0 | -0.295031 log odds |
| position_2 | 1.0 | 0.288651 log odds |
| role_pool_A | 4.462809917355371 | 0.234268 log odds |
| role_minor_0 | 4.206611570247934 | 0.167503 log odds |
| scout_list_capacity_0 | 100.0 | -0.002181 log odds |

conditional_pa: reference 277.961168 plus all saved terms = raw 278.309347 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.93 | 189.767087 PA |
| work_0 | 0.0 | -95.679648 PA |
| on_40man | 0.0 | -22.080266 PA |
| role_pool_AAA | 4.0 | -13.591101 PA |
| pooled_MLB_HBP | 0.01 | 12.810183 PA |
| pooled_A_K | 0.24855072463768113 | -12.196582 PA |
| regular_window_scaled | 0.0 | -11.693140 PA |
| games_pool_Aplus | 118.2 | -11.579010 PA |
| scout_listed_0 | 1.0 | 5.059233 PA |
| scout_listed_2 | 0.0 | 1.415126 PA |

Full-population rank profile: [{'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'top20', 'rank_profile_players': 7}]. Active-label conditional profile: [{'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 2}].

Actual original-fold general support: [{'row_id': 57694, 'horizon': 1, 'player_id': 806956, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11318, 'current_players': 11841, 'regular_players': 11936, 'joint_players': 9474, 'quality_joint_players': 11400, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 57694, 'horizon': 1, 'player_id': 806956, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 1003, 'current_players': 1122, 'regular_players': 1388, 'joint_players': 385, 'quality_joint_players': 1033, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 57694, 'horizon': 1, 'player_id': 806956, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 11318, 'current_players': 11841, 'regular_players': 11936, 'joint_players': 9474, 'quality_joint_players': 11400, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 57694, 'horizon': 1, 'player_id': 806956, 'origin_year': 2024, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 18.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 1003, 'current_players': 1122, 'regular_players': 1388, 'joint_players': 385, 'quality_joint_players': 1033, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Salas's age eighteen and mostly High-A workload now give only 2.57% next-year MLB probability. High rank still supports 278 conditional PA if he does arrive, but multiplying yields 7.14 expected instead of the rank-direct 232, versus zero actual. This is the intended quality/readiness separation and a major improvement in baseball plausibility. Conditional-profile support drops from seven people to only two, so the hypothetical active workload is especially uncertain. Clark/Emerson/Santana/Rodriguez all fail to arrive next year. The calculation preserves future upside without claiming a calibrated career distribution or discarding Salas as a prospect.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Max Clark | 19.0 | 0 | 490 | 0.88 | 0.14872 | 296.85 | 44.15 | 0 | 0.00000 |
| Colt Emerson | 18.0 | 0 | 336 | 0.14 | 0.07120 | 95.83 | 6.82 | 0 | 0.00000 |
| Adrian Santana | 18.0 | 0 | 455 | 0.0 | 0.01873 | 82.32 | 1.54 | 0 | 0.00000 |
| Yophery Rodriguez | 18.0 | 0 | 484 | 0.0 | 0.00424 | 80.53 | 0.34 | 0 | 0.00000 |

## Rafael Devers — 2016 to 2017

Player 646240; row 25414; fold 3; age 19.0; Lower minors; snapshot HIGH_A. Selection: lower ranked gain, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | RK124 | 302 | 70 | 7 | 50 | 34 |
| 2015 | A | 508 | 115 | 11 | 84 | 24 |
| 2016 | Aplus | 546 | 128 | 11 | 94 | 38 |

Historical rank rows: [{'season': 2015, 'player_id': 646240, 'rank': 96, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Rafael Devers'}, {'season': 2016, 'player_id': 646240, 'rank': 17, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Rafael Devers'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 1.382901 | 0.181006 | 0.004688 |
| scout | Not estimated | Not estimated | 146.740599 | 0.181006 | 0.497417 |
| fallback | Not estimated | Not estimated | 146.740599 | 0.181006 | 0.497417 |
| binary_count | 0.018826 | 69.892160 | 1.315820 | 0.181006 | 0.004460 |
| binary_scout | 0.037341 | 224.340064 | 8.377074 | 0.181006 | 0.028396 |
| Actual | 1 | 240 | 240 | 1.1434277565189273 | 1.195653 |

### binary_count: probability and workload accounting

Effective probability 0.01882644 × bounded conditional PA 69.892160 = expected PA 1.315820. Contribution = that PA × (0.181006/600 + 0.00308809). Raw probability 0.01882644 is preserved separately from any availability override.

participation: reference -4.035729 plus all saved terms = raw -3.953487 log odds; logistic link gives probability 0.01882644. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_minor_0 | 128.0 | 0.780757 log odds |
| on_40man | 0.0 | -0.422451 log odds |
| games_minor_1 | 115.0 | 0.293825 log odds |
| games_mlb_0 | 0.0 | -0.253910 log odds |
| role_pool_Aplus | 4.246376811594203 | 0.195245 log odds |
| age_squared | 2.5600000000000005 | -0.185777 log odds |
| pooled_A_2B | 0.06990521327014218 | 0.156453 log odds |
| games_pool_MLB | 0.0 | -0.151014 log odds |

conditional_pa: reference 276.930516 plus all saved terms = raw 69.892160 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -85.415092 PA |
| work_0 | 0.0 | -31.405135 PA |
| pooled_Aplus_3B | 0.013157894736842105 | 28.304990 PA |
| age_centered | -1.6 | 23.491388 PA |
| on_40man | 0.0 | -16.712899 PA |
| pooled_A_BB | 0.053712480252764615 | -14.896564 PA |
| Aplus_0_pa | 546.0 | -9.703586 PA |
| quality_0 | 0.0 | -8.775990 PA |

### binary_scout: probability and workload accounting

Effective probability 0.03734096 × bounded conditional PA 224.340064 = expected PA 8.377074. Contribution = that PA × (0.181006/600 + 0.00308809). Raw probability 0.03734096 is preserved separately from any availability override.

participation: reference -4.032416 plus all saved terms = raw -3.249608 log odds; logistic link gives probability 0.03734096. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_minor_0 | 128.0 | 0.767238 log odds |
| on_40man | 0.0 | -0.423165 log odds |
| scout_rank_score_0 | 0.84 | 0.334845 log odds |
| games_minor_1 | 115.0 | 0.276606 log odds |
| scout_listed_0 | 1.0 | 0.269240 log odds |
| role_pool_Aplus | 4.246376811594203 | 0.176890 log odds |
| games_mlb_0 | 0.0 | -0.171629 log odds |
| games_pool_MLB | 0.0 | -0.151339 log odds |
| scout_list_capacity_0 | 100.0 | 0.007340 log odds |

conditional_pa: reference 276.985230 plus all saved terms = raw 224.340064 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.84 | 164.704214 PA |
| MLB_0_pa | 0.0 | -85.525918 PA |
| work_0 | 0.0 | -26.623476 PA |
| on_40man | 0.0 | -15.919929 PA |
| pooled_Aplus_3B | 0.013157894736842105 | 13.836662 PA |
| quality_0 | 0.0 | -9.457670 PA |
| RK124_2_pa | 302.0 | -9.414111 PA |
| pooled_MLB_K | 0.23 | -7.556984 PA |
| scout_list_capacity_2 | 100.0 | -6.873697 PA |

Full-population rank profile: [{'row_id': 25414, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'top20', 'rank_profile_players': 2}]. Active-label conditional profile: [{'row_id': 25414, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 1}].

Actual original-fold general support: [{'row_id': 25414, 'horizon': 1, 'player_id': 646240, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 19.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 25414, 'horizon': 1, 'player_id': 646240, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 19.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 381, 'current_players': 468, 'regular_players': 684, 'joint_players': 161, 'quality_joint_players': 403, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 25414, 'horizon': 1, 'player_id': 646240, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 19.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 5886, 'current_players': 6281, 'regular_players': 6446, 'joint_players': 4617, 'quality_joint_players': 5961, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 25414, 'horizon': 1, 'player_id': 646240, 'origin_year': 2016, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 19.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 381, 'current_players': 468, 'regular_players': 684, 'joint_players': 161, 'quality_joint_players': 403, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Devers supplies the necessary adverse tradeoff: the binary rank model assigns only 3.73% chance of next-year MLB and 224 conditional PA, 8.38 expected versus actual 240. This loses most of rank-direct's 147-PA gain. Only one earlier active-label person matches the coarse lower/top20/age profile. The problem is primarily arrival probability, not conditional opportunity. Torres/Rodgers/Tucker do not arrive and Robles gets only 27 PA, so widespread lower-minor caution makes sense, but the model has not learned which promising teenagers advance exceptionally quickly. Do not certify low-level probability calibration from Salas alone.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gleyber Torres | 19.0 | 0 | 547 | 0.73 | 0.03379 | 262.60 | 8.87 | 0 | 0.00000 |
| Brendan Rodgers | 19.0 | 0 | 491 | 0.89 | 0.05759 | 285.92 | 16.47 | 0 | 0.00000 |
| Victor Robles | 19.0 | 0 | 504 | 0.38 | 0.01283 | 198.79 | 2.55 | 27 | 0.06951 |
| Kyle Tucker | 19.0 | 0 | 497 | 0.27 | 0.04197 | 137.51 | 5.77 | 0 | 0.00000 |

## Kyle Farmer — 2024 to 2025

Player 571657; row 54824; fold 0; age 33.0; Current MLB; snapshot MLB. Selection: fallback value ordinary, fixed previous diagnostic.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2022 | MLB | 583 | 145 | 14 | 99 | 33 |
| 2023 | AAA | 15 | 4 | 1 | 4 | 2 |
| 2023 | MLB | 369 | 120 | 11 | 86 | 23 |
| 2024 | AAA | 12 | 3 | 0 | 4 | 1 |
| 2024 | MLB | 242 | 107 | 5 | 49 | 18 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2013/244; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 207.782321 | -1.252324 | 0.215461 |
| scout | Not estimated | Not estimated | 203.608621 | -1.252324 | 0.211133 |
| fallback | Not estimated | Not estimated | 207.782321 | -1.252324 | 0.215461 |
| binary_count | 0.942086 | 216.102716 | 203.587307 | -1.252324 | 0.211111 |
| binary_scout | 0.941627 | 213.892134 | 201.406520 | -1.252324 | 0.208849 |
| Actual | 1 | 300 | 300 | -1.4385545444615153 | 0.215527 |

### binary_count: probability and workload accounting

Effective probability 0.94208583 × bounded conditional PA 216.102716 = expected PA 203.587307. Contribution = that PA × (-1.252324/600 + 0.00312416). Raw probability 0.94208583 is preserved separately from any availability override.

participation: reference -4.011949 plus all saved terms = raw 2.789134 log odds; logistic link gives probability 0.94208583. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.066559 log odds |
| games_mlb_0 | 107.0 | 1.456234 log odds |
| pooled_MLB_pa | 887.0 | 0.628405 log odds |
| work_0 | 242.0996294771511 | 0.400158 log odds |
| MLB_0_pa | 242.0 | 0.308749 log odds |
| games_pool_MLB | 290.0 | 0.201389 log odds |
| role_minor_0 | 4.0 | 0.163712 log odds |
| quality_0 | -0.2035379275688247 | -0.121816 log odds |

conditional_pa: reference 278.498387 plus all saved terms = raw 216.102716 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| age_centered | 1.2 | -29.703233 PA |
| role_mlb_0 | 2.41025641025641 | -27.751346 PA |
| work_0 | 242.0996294771511 | -20.032403 PA |
| quality_0 | -0.2035379275688247 | -16.869705 PA |
| regular_window_scaled | 0.3333333333333333 | 16.220426 PA |
| role_pool_MLB | 3.09 | -16.124818 PA |
| on_40man | 1.0 | 15.862719 PA |
| pooled_MLB_pa | 887.0 | 14.146049 PA |

### binary_scout: probability and workload accounting

Effective probability 0.94162659 × bounded conditional PA 213.892134 = expected PA 201.406520. Contribution = that PA × (-1.252324/600 + 0.00312416). Raw probability 0.94162659 is preserved separately from any availability override.

participation: reference -4.027372 plus all saved terms = raw 2.780748 log odds; logistic link gives probability 0.94162659. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.087314 log odds |
| games_mlb_0 | 107.0 | 1.497083 log odds |
| pooled_MLB_pa | 887.0 | 0.523254 log odds |
| work_0 | 242.0996294771511 | 0.409753 log odds |
| MLB_0_pa | 242.0 | 0.308749 log odds |
| games_pool_MLB | 290.0 | 0.214909 log odds |
| role_minor_0 | 4.0 | 0.170399 log odds |
| draft_rank | 0.2767742706141265 | 0.130311 log odds |
| scout_listed_0 | 0.0 | -0.061212 log odds |
| scout_rank_score_0 | 0.0 | -0.007209 log odds |

conditional_pa: reference 278.496527 plus all saved terms = raw 213.892134 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| age_centered | 1.2 | -27.442560 PA |
| role_mlb_0 | 2.41025641025641 | -25.727703 PA |
| work_0 | 242.0996294771511 | -23.100695 PA |
| role_pool_MLB | 3.09 | -17.987356 PA |
| on_40man | 1.0 | 16.428565 PA |
| regular_window_scaled | 0.3333333333333333 | 15.319548 PA |
| quality_0 | -0.2035379275688247 | -15.067802 PA |
| pooled_MLB_pa | 887.0 | 12.485257 PA |
| scout_rank_score_0 | 0.0 | -1.519171 PA |
| scout_rank_score_1 | 0.0 | 0.045845 PA |

Full-population rank profile: [{'row_id': 54824, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'rank_profile_players': 563}]. Active-label conditional profile: [{'row_id': 54824, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 436}].

Actual original-fold general support: [{'row_id': 54824, 'horizon': 1, 'player_id': 571657, 'origin_year': 2024, 'elapsed': 7, 'current_state': 2, 'regular_window': 1, 'age': 33.0, 'quality_0': -0.2035379275688247, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 495, 'current_players': 748, 'regular_players': 551, 'joint_players': 374, 'quality_joint_players': 528, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 54824, 'horizon': 1, 'player_id': 571657, 'origin_year': 2024, 'elapsed': 7, 'current_state': 2, 'regular_window': 1, 'age': 33.0, 'quality_0': -0.2035379275688247, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 297, 'current_players': 667, 'regular_players': 483, 'joint_players': 303, 'quality_joint_players': 453, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 54824, 'horizon': 1, 'player_id': 571657, 'origin_year': 2024, 'elapsed': 7, 'current_state': 2, 'regular_window': 1, 'age': 33.0, 'quality_0': -0.2035379275688247, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 495, 'current_players': 748, 'regular_players': 551, 'joint_players': 374, 'quality_joint_players': 528, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 54824, 'horizon': 1, 'player_id': 571657, 'origin_year': 2024, 'elapsed': 7, 'current_state': 2, 'regular_window': 1, 'age': 33.0, 'quality_0': -0.2035379275688247, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 297, 'current_players': 667, 'regular_players': 483, 'joint_players': 303, 'quality_joint_players': 453, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Farmer's declining MLB usage and age 33 yield 94.2% chance of appearing but only 214 PA if active, 201 expected versus actual 300. The miss is role/workload, not expected total exit. Count binary 204 and direct count 208 are similarly conservative. Value .209 stays near observed .216 through understated PA and overly optimistic fixed rate; this is not a fully accurate projection. Populated active support and peers ranging 50 to 388 PA preserve the part-time/health/job ambiguity without labeling low PA as diagnosed injury.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Chris Taylor | 33.0 | 246 | 21 | 0.0 | 0.91283 | 213.76 | 195.13 | 125 | -0.24427 |
| Travis Jankowski | 33.0 | 207 | 0 | 0.0 | 0.58012 | 117.37 | 68.09 | 50 | -0.09218 |
| Michael A. Taylor | 33.0 | 300 | 0 | 0.0 | 0.62262 | 105.66 | 65.79 | 325 | -0.20782 |
| Max Muncy | 33.0 | 293 | 24 | 0.0 | 0.97470 | 456.53 | 444.98 | 388 | 2.92574 |

## Matt Davidson — 2018 to 2019

Player 571602; row 32602; fold 1; age 27.0; Current MLB; snapshot MLB. Selection: binary_count pa largest gain.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | AAA | 326 | 75 | 10 | 86 | 30 |
| 2016 | MLB | 2 | 1 | 0 | 1 | 0 |
| 2017 | AAA | 3 | 1 | 0 | 3 | 0 |
| 2017 | MLB | 443 | 118 | 26 | 165 | 19 |
| 2018 | MLB | 496 | 126 | 20 | 165 | 52 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2009/35; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 405.092516 | 0.267434 | 1.427745 |
| scout | Not estimated | Not estimated | 408.228270 | 0.267434 | 1.438797 |
| fallback | Not estimated | Not estimated | 405.092516 | 0.267434 | 1.427745 |
| binary_count | 0.755170 | 409.406812 | 309.171919 | 0.267434 | 1.089674 |
| binary_scout | 0.796106 | 417.966937 | 332.745825 | 0.267434 | 1.172760 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.75517043 × bounded conditional PA 409.406812 = expected PA 309.171919. Contribution = that PA × (0.267434/600 + 0.00307877). Raw probability 0.75517043 is preserved separately from any availability override.

participation: reference -4.028406 plus all saved terms = raw 1.126381 log odds; logistic link gives probability 0.75517043. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 126.0 | 2.025319 log odds |
| games_pool_MLB | 221.0 | 1.323656 log odds |
| on_40man | 0.0 | -0.776973 log odds |
| MLB_0_pa | 496.0 | 0.586848 log odds |
| quality_0 | 0.14165434783828937 | 0.526745 log odds |
| games_mlb_1 | 118.0 | 0.443891 log odds |
| work_0 | 495.7959687371452 | 0.373030 log odds |
| position_10 | 1.0 | -0.350167 log odds |

conditional_pa: reference 287.111316 plus all saved terms = raw 409.406812 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 496.0 | 58.352069 PA |
| work_0 | 495.7959687371452 | 52.644957 PA |
| role_mlb_0 | 3.9411764705882355 | 23.755153 PA |
| quality_0 | 0.14165434783828937 | 17.693875 PA |
| role_pool_MLB | 3.8597402597402604 | -16.065187 PA |
| on_40man | 0.0 | -13.610167 PA |
| regular_window_scaled | 0.6666666666666666 | 11.857183 PA |
| pooled_MLB_K | 0.3369062631357713 | -10.127735 PA |

### binary_scout: probability and workload accounting

Effective probability 0.79610561 × bounded conditional PA 417.966937 = expected PA 332.745825. Contribution = that PA × (0.267434/600 + 0.00307877). Raw probability 0.79610561 is preserved separately from any availability override.

participation: reference -4.016897 plus all saved terms = raw 1.362130 log odds; logistic link gives probability 0.79610561. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 126.0 | 1.979368 log odds |
| games_pool_MLB | 221.0 | 1.352770 log odds |
| on_40man | 0.0 | -0.777283 log odds |
| MLB_0_pa | 496.0 | 0.587580 log odds |
| quality_0 | 0.14165434783828937 | 0.529293 log odds |
| games_mlb_1 | 118.0 | 0.479468 log odds |
| position_10 | 1.0 | -0.385253 log odds |
| work_0 | 495.7959687371452 | 0.367660 log odds |
| scout_rank_score_0 | 0.0 | -0.008097 log odds |

conditional_pa: reference 287.124657 plus all saved terms = raw 417.966937 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 496.0 | 57.527196 PA |
| work_0 | 495.7959687371452 | 49.457933 PA |
| role_mlb_0 | 3.9411764705882355 | 26.672414 PA |
| quality_0 | 0.14165434783828937 | 18.630196 PA |
| on_40man | 0.0 | -16.106044 PA |
| regular_window_scaled | 0.6666666666666666 | 14.689323 PA |
| role_pool_MLB | 3.8597402597402604 | -14.458957 PA |
| pooled_MLB_K | 0.3369062631357713 | -10.656939 PA |
| scout_rank_score_0 | 0.0 | -0.883898 PA |
| scout_listed_0 | 0.0 | -0.315924 PA |
| scout_rank_score_2 | 0.0 | 0.042316 PA |
| scout_rank_score_1 | 0.0 | -0.011475 PA |

Full-population rank profile: [{'row_id': 32602, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'rank_profile_players': 699}]. Active-label conditional profile: [{'row_id': 32602, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 542}].

Actual original-fold general support: [{'row_id': 32602, 'horizon': 1, 'player_id': 571602, 'origin_year': 2018, 'elapsed': 5, 'current_state': 3, 'regular_window': 2, 'age': 27.0, 'quality_0': 0.14165434783828937, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 507, 'current_players': 379, 'regular_players': 295, 'joint_players': 169, 'quality_joint_players': 298, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 32602, 'horizon': 1, 'player_id': 571602, 'origin_year': 2018, 'elapsed': 5, 'current_state': 3, 'regular_window': 2, 'age': 27.0, 'quality_0': 0.14165434783828937, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 235, 'current_players': 373, 'regular_players': 255, 'joint_players': 169, 'quality_joint_players': 293, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 32602, 'horizon': 1, 'player_id': 571602, 'origin_year': 2018, 'elapsed': 5, 'current_state': 3, 'regular_window': 2, 'age': 27.0, 'quality_0': 0.14165434783828937, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 507, 'current_players': 379, 'regular_players': 295, 'joint_players': 169, 'quality_joint_players': 298, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 32602, 'horizon': 1, 'player_id': 571602, 'origin_year': 2018, 'elapsed': 5, 'current_state': 3, 'regular_window': 2, 'age': 27.0, 'quality_0': 0.14165434783828937, 'elapsed_band': 2, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 235, 'current_players': 373, 'regular_players': 255, 'joint_players': 169, 'quality_joint_players': 293, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Davidson had 496 MLB PA, 20 HR, 165 K and 52 BB in 2018 after 443 PA in 2017. The supplied roster flag is zero; games history still makes appearance plausible. Count binary estimates 75.5% × 409 = 309 expected PA versus direct 405 and actual zero, its largest PA gain, while scouting yields 333. Roster absence suppresses participation but is not certified release, free agency or permanent ineligibility. The model improves a miss without knowing his later non-arrival. Conditional workload remains high because his actual recent use supports a role if employed. The active unlisted profile has 542 people; Villar, Barnhart, Diaz and Realmuto all appear with varied PA. Removing every unlisted current hitter would be a hindsight error.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jonathan Villar | 27.0 | 515 | 11 | 0.0 | 0.98042 | 452.95 | 444.08 | 714 | 3.19170 |
| Tucker Barnhart | 27.0 | 522 | 0 | 0.0 | 0.98460 | 392.67 | 386.62 | 364 | 0.39212 |
| Aledmys Díaz | 27.0 | 452 | 10 | 0.0 | 0.98546 | 415.91 | 409.86 | 247 | 1.30445 |
| J.T. Realmuto | 27.0 | 531 | 4 | 0.0 | 0.99198 | 520.22 | 516.05 | 593 | 2.87362 |

## Fernando Tatis Jr. — 2022 to 2023

Player 665487; row 47261; fold 0; age 23.0; Upper minors; snapshot AA. Selection: binary_count pa largest harm, binary_count pa false low, binary_scout pa false low.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 257 | 59 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 130 | 42 | 153 | 56 |
| 2022 | AA | 14 | 4 | 0 | 2 | 4 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 140.149676 | 1.279500 | 0.737674 |
| scout | Not estimated | Not estimated | 133.596094 | 1.279500 | 0.703179 |
| fallback | Not estimated | Not estimated | 140.149676 | 1.279500 | 0.737674 |
| binary_count | 0.129290 | 286.737463 | 37.072412 | 1.279500 | 0.195130 |
| binary_scout | 0.121984 | 283.585083 | 34.592818 | 1.279500 | 0.182078 |
| Actual | 1 | 635 | 635 | 0.7268065858888001 | 2.735212 |

### binary_count: probability and workload accounting

Effective probability 0.12929044 × bounded conditional PA 286.737463 = expected PA 37.072412. Contribution = that PA × (1.279500/600 + 0.00313097). Raw probability 0.12929044 is preserved separately from any availability override.

participation: reference -4.062741 plus all saved terms = raw -1.907247 log odds; logistic link gives probability 0.12929044. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_pool_MLB | 199.57999999999998 | 1.059700 log odds |
| pooled_MLB_pa | 591.0 | 0.610301 log odds |
| on_40man | 0.0 | -0.541551 log odds |
| games_mlb_1 | 130.0 | 0.481581 log odds |
| absence_window_scaled | 0.3333333333333333 | 0.264826 log odds |
| games_mlb_0 | 0.0 | -0.245495 log odds |
| pooled_mlb_quality | 1.3673684989925885 | 0.234776 log odds |
| pooled_AA_BB | 0.10526315789473684 | 0.191074 log odds |

conditional_pa: reference 278.047514 plus all saved terms = raw 286.737463 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -92.320714 PA |
| pooled_mlb_quality | 1.3673684989925885 | 78.007183 PA |
| on_40man | 0.0 | -25.454151 PA |
| role_pool_MLB | 4.223560910307898 | 21.814792 PA |
| role_mlb_0 | 4.0 | 18.583961 PA |
| pooled_MLB_K | 0.2633863965267728 | -16.624689 PA |
| regular_window_scaled | 0.6666666666666666 | 14.175682 PA |
| quality_1 | 1.347878741765764 | -9.420881 PA |

### binary_scout: probability and workload accounting

Effective probability 0.12198391 × bounded conditional PA 283.585083 = expected PA 34.592818. Contribution = that PA × (1.279500/600 + 0.00313097). Raw probability 0.12198391 is preserved separately from any availability override.

participation: reference -4.060609 plus all saved terms = raw -1.973776 log odds; logistic link gives probability 0.12198391. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_pool_MLB | 199.57999999999998 | 1.197825 log odds |
| on_40man | 0.0 | -0.545526 log odds |
| pooled_MLB_pa | 591.0 | 0.496131 log odds |
| games_mlb_1 | 130.0 | 0.477597 log odds |
| pooled_mlb_quality | 1.3673684989925885 | 0.302824 log odds |
| absence_window_scaled | 0.3333333333333333 | 0.294039 log odds |
| games_mlb_0 | 0.0 | -0.248785 log odds |
| role_minor_0 | 3.857142857142857 | -0.185439 log odds |
| scout_listed_0 | 0.0 | -0.055697 log odds |
| scout_rank_score_0 | 0.0 | -0.003841 log odds |

conditional_pa: reference 278.062262 plus all saved terms = raw 283.585083 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 0.0 | -91.567413 PA |
| pooled_mlb_quality | 1.3673684989925885 | 74.963770 PA |
| role_pool_MLB | 4.223560910307898 | 24.851174 PA |
| on_40man | 0.0 | -22.656435 PA |
| role_mlb_0 | 4.0 | 21.390418 PA |
| work_1 | 546.2247838616715 | 17.712041 PA |
| pooled_MLB_K | 0.2633863965267728 | -16.077549 PA |
| quality_1 | 1.347878741765764 | -11.974251 PA |
| scout_rank_score_0 | 0.0 | -3.915725 PA |
| scout_list_capacity_2 | 99.0 | 0.260450 PA |
| scout_rank_score_1 | -1.0 | -0.064542 PA |

Full-population rank profile: [{'row_id': 47261, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 38}]. Active-label conditional profile: [{'row_id': 47261, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 22}].

Actual original-fold general support: [{'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 797, 'current_players': 10645, 'regular_players': 385, 'joint_players': 26, 'quality_joint_players': 812, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 442, 'current_players': 970, 'regular_players': 344, 'joint_players': 6, 'quality_joint_players': 121, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 797, 'current_players': 10645, 'regular_players': 385, 'joint_players': 26, 'quality_joint_players': 812, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 47261, 'horizon': 1, 'player_id': 665487, 'origin_year': 2022, 'elapsed': 3, 'current_state': 0, 'regular_window': 2, 'age': 23.0, 'quality_0': 0.0, 'elapsed_band': 2, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 442, 'current_players': 970, 'regular_players': 344, 'joint_players': 6, 'quality_joint_players': 121, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Tatis's record includes 42 MLB HR in 546 PA in 2021, a shortened 257-PA MLB season in 2020, and only fourteen AA PA in 2022. The roster flag is zero and availability is explicitly unresolved, not permanently barred. Binary scouting gives 12.2% × 284 = 35 PA versus direct count 140 and actual 635, a severe temporary-return miss; count binary is 37. Pooled MLB history raises log odds and conditional workload, but no current MLB use and the missing roster listing overwhelm it. The active returning-young-player profile has only 22 people, and selected peers have very little future use; their origin distance does not make them equivalent established stars with finite absences. This source/representation problem needs dated absence/return context, not an automatic zero or an invented healthy full-season scenario. Fixed rate 1.279 is above actual .727, so more correct PA would not necessarily give exact contribution.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sherten Apostel | 23.0 | 0 | 77 | 0.0 | 0.06003 | 79.86 | 4.79 | 0 | 0.00000 |
| Colton Welker | 24.0 | 0 | 45 | 0.0 | 0.08817 | 112.46 | 9.92 | 0 | 0.00000 |
| Rafael Marchán | 23.0 | 0 | 278 | 0.0 | 0.79239 | 136.83 | 108.43 | 0 | 0.00000 |
| Jahmai Jones | 24.0 | 0 | 118 | 0.0 | 0.10844 | 92.87 | 10.07 | 11 | -0.02098 |

## Matt McLain — 2023 to 2024

Player 680574; row 51984; fold 2; age 23.0; Current MLB; snapshot MLB. Selection: binary_count pa false high, binary_scout pa false high.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2021 | Aplus | 119 | 29 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 2 | 0 | 0 | 0 |
| 2022 | AA | 452 | 103 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 40 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 89 | 16 | 115 | 31 |

Historical rank rows: [{'season': 2022, 'player_id': 680574, 'rank': 87, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Matt McLain'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2021/17; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 564.579793 | 0.884667 | 2.580424 |
| scout | Not estimated | Not estimated | 538.504453 | 0.884667 | 2.461246 |
| fallback | Not estimated | Not estimated | 564.579793 | 0.884667 | 2.580424 |
| binary_count | 0.986530 | 589.509816 | 581.569013 | 0.884667 | 2.658074 |
| binary_scout | 0.987565 | 603.194917 | 595.693958 | 0.884667 | 2.722632 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.98652982 × bounded conditional PA 589.509816 = expected PA 581.569013. Contribution = that PA × (0.884667/600 + 0.00309608). Raw probability 0.98652982 is preserved separately from any availability override.

participation: reference -4.043086 plus all saved terms = raw 4.293715 log odds; logistic link gives probability 0.98652982. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.549057 log odds |
| games_mlb_0 | 89.0 | 1.256137 log odds |
| work_0 | 403.0 | 1.106391 log odds |
| absence_window_scaled | 0.6666666666666666 | 0.719222 log odds |
| pooled_mlb_quality | 0.6728121955092439 | 0.474652 log odds |
| quality_0 | 0.6728121955092439 | 0.391343 log odds |
| games_pool_MLB | 89.0 | 0.256489 log odds |
| role_minor_0 | 4.4 | 0.216442 log odds |

conditional_pa: reference 279.305469 plus all saved terms = raw 589.509816 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 403.0 | 99.681228 PA |
| pooled_AAA_HR | 0.05357142857142857 | 37.298293 PA |
| quality_0 | 0.6728121955092439 | 32.711787 PA |
| role_mlb_0 | 4.474747474747475 | 30.547811 PA |
| role_pool_MLB | 4.474747474747475 | 26.695681 PA |
| age_centered | -0.8 | 23.504820 PA |
| pooled_mlb_quality | 0.6728121955092439 | 20.736577 PA |
| MLB_0_pa | 403.0 | -18.337483 PA |

### binary_scout: probability and workload accounting

Effective probability 0.98756462 × bounded conditional PA 603.194917 = expected PA 595.693958. Contribution = that PA × (0.884667/600 + 0.00309608). Raw probability 0.98756462 is preserved separately from any availability override.

participation: reference -4.051937 plus all saved terms = raw 4.374696 log odds; logistic link gives probability 0.98756462. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.568757 log odds |
| games_mlb_0 | 89.0 | 1.261076 log odds |
| work_0 | 403.0 | 1.066296 log odds |
| absence_window_scaled | 0.6666666666666666 | 0.719222 log odds |
| pooled_mlb_quality | 0.6728121955092439 | 0.480851 log odds |
| quality_0 | 0.6728121955092439 | 0.412245 log odds |
| games_pool_MLB | 89.0 | 0.272133 log odds |
| role_pool_AAA | 4.4 | 0.236409 log odds |
| scout_listed_2 | -1.0 | -0.062869 log odds |
| scout_listed_0 | 0.0 | -0.050309 log odds |
| scout_list_capacity_0 | 100.0 | -0.016084 log odds |
| scout_rank_score_2 | -1.0 | 0.004329 log odds |
| scout_rank_score_0 | 0.0 | -0.004093 log odds |

conditional_pa: reference 279.276463 plus all saved terms = raw 603.194917 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 403.0 | 98.168335 PA |
| quality_0 | 0.6728121955092439 | 38.032930 PA |
| pooled_AAA_HR | 0.05357142857142857 | 36.826360 PA |
| role_mlb_0 | 4.474747474747475 | 31.067748 PA |
| role_pool_MLB | 4.474747474747475 | 26.981471 PA |
| age_centered | -0.8 | 21.171483 PA |
| regular_window_scaled | 0.3333333333333333 | 18.029592 PA |
| MLB_0_pa | 403.0 | -17.178067 PA |
| scout_listed_1 | 1.0 | 12.688729 PA |
| scout_rank_score_0 | 0.0 | -1.049634 PA |

Full-population rank profile: [{'row_id': 51984, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'rank_profile_players': 460}]. Active-label conditional profile: [{'row_id': 51984, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 396}].

Actual original-fold general support: [{'row_id': 51984, 'horizon': 1, 'player_id': 680574, 'origin_year': 2023, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.6728121955092439, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 916, 'current_players': 499, 'regular_players': 499, 'joint_players': 20, 'quality_joint_players': 41, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 51984, 'horizon': 1, 'player_id': 680574, 'origin_year': 2023, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.6728121955092439, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 705, 'current_players': 490, 'regular_players': 438, 'joint_players': 20, 'quality_joint_players': 41, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 51984, 'horizon': 1, 'player_id': 680574, 'origin_year': 2023, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.6728121955092439, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 916, 'current_players': 499, 'regular_players': 499, 'joint_players': 20, 'quality_joint_players': 41, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 51984, 'horizon': 1, 'player_id': 680574, 'origin_year': 2023, 'elapsed': 0, 'current_state': 3, 'regular_window': 1, 'age': 23.0, 'quality_0': 0.6728121955092439, 'elapsed_band': 0, 'age_band': 1, 'quality_band': 1, 'elapsed_players': 705, 'current_players': 490, 'regular_players': 438, 'joint_players': 20, 'quality_joint_players': 41, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

McLain had 403 MLB PA with 16 HR, 115 K and 31 BB, plus 180 strong AAA PA; he is roster-listed. Both binary heads give about 98.7% appearance probability and 590–603 conditional PA, 582/596 expected versus zero actual, the largest PA false high. The optimism reflects real young performance/use rather than current rank; only his old 2022 rank exists. The provided origin record does not identify a dated future-season health collapse, so injury hindsight is not added. Kelenic, Moreno, Gorman and Julien all appear the following year, supporting a regular-opportunity prior while showing varying workloads. A sensible expectation can miss a whole-season absence; the correct next question is whether cutoff-known health evidence was missing, not whether every good rookie should be penalized.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jarred Kelenic | 23.0 | 416 | 43 | 0.0 | 0.97906 | 437.52 | 428.36 | 449 | 0.81013 |
| Gabriel Moreno | 23.0 | 380 | 11 | 0.0 | 0.97054 | 363.64 | 352.92 | 351 | 1.57687 |
| Nolan Gorman | 23.0 | 464 | 0 | 0.0 | 0.97773 | 424.01 | 414.56 | 402 | 0.60634 |
| Edouard Julien | 24.0 | 408 | 170 | 0.0 | 0.98390 | 380.26 | 374.14 | 301 | 0.18702 |

## Willson Contreras — 2022 to 2023

Player 575929; row 46496; fold 0; age 30.0; Current MLB; snapshot MLB. Selection: binary_count pa ordinary.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2020 | MLB | 225 | 57 | 7 | 57 | 19 |
| 2021 | AAA | 12 | 3 | 2 | 3 | 1 |
| 2021 | MLB | 483 | 128 | 21 | 138 | 51 |
| 2022 | MLB | 487 | 113 | 22 | 103 | 45 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 509.528390 | 0.442008 | 1.970679 |
| scout | Not estimated | Not estimated | 510.399517 | 0.442008 | 1.974048 |
| fallback | Not estimated | Not estimated | 509.528390 | 0.442008 | 1.970679 |
| binary_count | 0.992263 | 498.783924 | 494.924823 | 0.442008 | 1.914198 |
| binary_scout | 0.992573 | 494.200553 | 490.530124 | 0.442008 | 1.897200 |
| Actual | 1 | 495 | 495 | 2.029635083389632 | 3.207007 |

### binary_count: probability and workload accounting

Effective probability 0.99226298 × bounded conditional PA 498.783924 = expected PA 494.924823. Contribution = that PA × (0.442008/600 + 0.00313097). Raw probability 0.99226298 is preserved separately from any availability override.

participation: reference -4.062741 plus all saved terms = raw 4.853972 log odds; logistic link gives probability 0.99226298. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.920426 log odds |
| work_0 | 487.0 | 1.322494 log odds |
| games_mlb_0 | 113.0 | 1.316331 log odds |
| quality_0 | 0.6908058188961493 | 0.581676 log odds |
| games_pool_MLB | 307.74 | 0.566372 log odds |
| pooled_MLB_pa | 1008.4000000000001 | 0.515857 log odds |
| pooled_mlb_quality | 0.793611189691906 | 0.295235 log odds |
| games_mlb_1 | 128.0 | 0.249229 log odds |

conditional_pa: reference 278.047514 plus all saved terms = raw 498.783924 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 487.0 | 109.886018 PA |
| role_mlb_0 | 4.284552845528455 | 42.153173 PA |
| pooled_mlb_quality | 0.793611189691906 | 20.494546 PA |
| quality_0 | 0.6908058188961493 | 19.190051 PA |
| regular_window_scaled | 1.0 | 14.175682 PA |
| pooled_MLB_K | 0.24413569108625044 | -13.888376 PA |
| pooled_MLB_pa | 1008.4000000000001 | 12.818831 PA |
| role_pool_MLB | 4.038520801232665 | 7.175881 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99257300 × bounded conditional PA 494.200553 = expected PA 490.530124. Contribution = that PA × (0.442008/600 + 0.00313097). Raw probability 0.99257300 is preserved separately from any availability override.

participation: reference -4.060609 plus all saved terms = raw 4.895178 log odds; logistic link gives probability 0.99257300. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.954283 log odds |
| work_0 | 487.0 | 1.363772 log odds |
| games_mlb_0 | 113.0 | 1.308220 log odds |
| games_pool_MLB | 307.74 | 0.671628 log odds |
| quality_0 | 0.6908058188961493 | 0.578880 log odds |
| pooled_MLB_pa | 1008.4000000000001 | 0.401687 log odds |
| pooled_mlb_quality | 0.793611189691906 | 0.333387 log odds |
| MLB_1_pa | 483.0 | 0.274655 log odds |
| scout_listed_0 | 0.0 | -0.053025 log odds |
| scout_rank_score_0 | 0.0 | -0.004467 log odds |

conditional_pa: reference 278.062262 plus all saved terms = raw 494.200553 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 487.0 | 108.976980 PA |
| role_mlb_0 | 4.284552845528455 | 41.869072 PA |
| pooled_mlb_quality | 0.793611189691906 | 23.990094 PA |
| quality_0 | 0.6908058188961493 | 18.431117 PA |
| pooled_MLB_K | 0.24413569108625044 | -16.074265 PA |
| pooled_MLB_pa | 1008.4000000000001 | 15.345481 PA |
| regular_window_scaled | 1.0 | 13.310116 PA |
| pooled_AAA_HR | 0.041970802919708027 | 8.732812 PA |
| scout_rank_score_0 | 0.0 | -0.458842 PA |
| scout_list_capacity_2 | 99.0 | 0.260450 PA |

Full-population rank profile: [{'row_id': 46496, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'rank_profile_players': 395}]. Active-label conditional profile: [{'row_id': 46496, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 310}].

Actual original-fold general support: [{'row_id': 46496, 'horizon': 1, 'player_id': 575929, 'origin_year': 2022, 'elapsed': 6, 'current_state': 3, 'regular_window': 3, 'age': 30.0, 'quality_0': 0.6908058188961493, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 480, 'current_players': 454, 'regular_players': 271, 'joint_players': 260, 'quality_joint_players': 368, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 46496, 'horizon': 1, 'player_id': 575929, 'origin_year': 2022, 'elapsed': 6, 'current_state': 3, 'regular_window': 3, 'age': 30.0, 'quality_0': 0.6908058188961493, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 279, 'current_players': 447, 'regular_players': 268, 'joint_players': 254, 'quality_joint_players': 362, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 46496, 'horizon': 1, 'player_id': 575929, 'origin_year': 2022, 'elapsed': 6, 'current_state': 3, 'regular_window': 3, 'age': 30.0, 'quality_0': 0.6908058188961493, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 480, 'current_players': 454, 'regular_players': 271, 'joint_players': 260, 'quality_joint_players': 368, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 46496, 'horizon': 1, 'player_id': 575929, 'origin_year': 2022, 'elapsed': 6, 'current_state': 3, 'regular_window': 3, 'age': 30.0, 'quality_0': 0.6908058188961493, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 279, 'current_players': 447, 'regular_players': 268, 'joint_players': 254, 'quality_joint_players': 362, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Contreras had 487 MLB PA, 22 HR, 103 K and 45 BB at age thirty after a similar 483-PA prior season. Count binary gives 99.2% × 499 = 494.92 PA versus 495 actual; scouting gives 491. This is the ordinary count-arm workload case, with populated 310-person active-profile support and use/role dominating the paths. Fixed batting rate .442 is below actual 2.030, so value 1.914 misses 3.207 despite nearly exact PA. Position is listed context, not a defense/positional bonus here; catcher defense is not in the target. Similar-age peers Renfroe, Pederson, Urshela and Diaz range 228 to 600 PA and very different batting output.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hunter Renfroe | 30.0 | 522 | 0 | 0.0 | 0.98830 | 480.29 | 474.67 | 548 | 1.30176 |
| Joc Pederson | 30.0 | 433 | 0 | 0.0 | 0.99187 | 378.92 | 375.84 | 425 | 1.65582 |
| Gio Urshela | 30.0 | 551 | 0 | 0.0 | 0.99130 | 449.19 | 445.29 | 228 | 0.52329 |
| Yandy Díaz | 30.0 | 558 | 0 | 0.0 | 0.99307 | 497.77 | 494.32 | 600 | 6.11208 |

## José Bautista — 2016 to 2017

Player 430832; row 22833; fold 2; age 35.0; Current MLB; snapshot MLB. Selection: binary_count value largest gain.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | MLB | 673 | 155 | 35 | 96 | 93 |
| 2015 | MLB | 666 | 153 | 40 | 106 | 108 |
| 2016 | AAA | 11 | 3 | 0 | 2 | 0 |
| 2016 | Aplus | 3 | 1 | 1 | 1 | 0 |
| 2016 | MLB | 517 | 116 | 22 | 103 | 86 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 427.039114 | 2.275708 | 2.938430 |
| scout | Not estimated | Not estimated | 387.971318 | 2.275708 | 2.669607 |
| fallback | Not estimated | Not estimated | 427.039114 | 2.275708 | 2.938430 |
| binary_count | 0.549691 | 487.557302 | 268.006047 | 2.275708 | 1.844133 |
| binary_scout | 0.531394 | 489.322348 | 260.022911 | 2.275708 | 1.789202 |
| Actual | 1 | 686 | 686 | -1.2228919314568512 | 0.712084 |

### binary_count: probability and workload accounting

Effective probability 0.54969138 × bounded conditional PA 487.557302 = expected PA 268.006047. Contribution = that PA × (2.275708/600 + 0.00308809). Raw probability 0.54969138 is preserved separately from any availability override.

participation: reference -3.950487 plus all saved terms = raw 0.199424 log odds; logistic link gives probability 0.54969138. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 116.0 | 2.056992 log odds |
| games_pool_MLB | 331.4 | 1.620778 log odds |
| on_40man | 0.0 | -1.009266 log odds |
| quality_0 | 0.5920253691863163 | 0.832989 log odds |
| age_centered | 1.6 | -0.695060 log odds |
| pooled_MLB_pa | 1453.6000000000001 | 0.693109 log odds |
| MLB_0_pa | 517.0 | 0.436747 log odds |
| quality_2 | 1.5407057942666498 | -0.358598 log odds |

conditional_pa: reference 281.380977 plus all saved terms = raw 487.557302 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 517.0 | 102.784404 PA |
| age_centered | 1.6 | -41.550153 PA |
| quality_0 | 0.5920253691863163 | 38.979368 PA |
| role_mlb_0 | 4.420634920634921 | 34.487228 PA |
| role_pool_MLB | 4.374926772114822 | 19.093753 PA |
| role_pool_AAA | 3.923076923076923 | -16.822689 PA |
| games_mlb_2 | 155.0 | 16.504997 PA |
| career_mlb_observed_pa | 4949.0 | 12.202618 PA |

### binary_scout: probability and workload accounting

Effective probability 0.53139390 × bounded conditional PA 489.322348 = expected PA 260.022911. Contribution = that PA × (2.275708/600 + 0.00308809). Raw probability 0.53139390 is preserved separately from any availability override.

participation: reference -3.961088 plus all saved terms = raw 0.125741 log odds; logistic link gives probability 0.53139390. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 116.0 | 2.038682 log odds |
| games_pool_MLB | 331.4 | 1.592612 log odds |
| on_40man | 0.0 | -1.008813 log odds |
| quality_0 | 0.5920253691863163 | 0.824551 log odds |
| pooled_MLB_pa | 1453.6000000000001 | 0.722682 log odds |
| age_centered | 1.6 | -0.652944 log odds |
| MLB_0_pa | 517.0 | 0.428091 log odds |
| quality_2 | 1.5407057942666498 | -0.367648 log odds |
| scout_rank_score_0 | 0.0 | -0.001335 log odds |
| scout_listed_0 | 0.0 | -0.000894 log odds |

conditional_pa: reference 281.416583 plus all saved terms = raw 489.322348 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 517.0 | 100.121278 PA |
| quality_0 | 0.5920253691863163 | 40.131452 PA |
| role_mlb_0 | 4.420634920634921 | 39.232941 PA |
| age_centered | 1.6 | -35.291777 PA |
| role_pool_MLB | 4.374926772114822 | 19.413961 PA |
| role_pool_AAA | 3.923076923076923 | -18.419219 PA |
| games_mlb_2 | 155.0 | 15.220289 PA |
| regular_window_scaled | 1.0 | 12.847743 PA |
| scout_list_capacity_2 | 100.0 | 3.839287 PA |
| scout_rank_score_0 | 0.0 | -0.559582 PA |

Full-population rank profile: [{'row_id': 22833, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 7.0, 'rank_band': 'not_listed', 'rank_profile_players': 102}]. Active-label conditional profile: [{'row_id': 22833, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 7.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 54}].

Actual original-fold general support: [{'row_id': 22833, 'horizon': 1, 'player_id': 430832, 'origin_year': 2016, 'elapsed': 12, 'current_state': 3, 'regular_window': 3, 'age': 35.0, 'quality_0': 0.5920253691863163, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 75, 'current_players': 319, 'regular_players': 186, 'joint_players': 172, 'quality_joint_players': 251, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 22833, 'horizon': 1, 'player_id': 430832, 'origin_year': 2016, 'elapsed': 12, 'current_state': 3, 'regular_window': 3, 'age': 35.0, 'quality_0': 0.5920253691863163, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 36, 'current_players': 313, 'regular_players': 182, 'joint_players': 168, 'quality_joint_players': 246, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 22833, 'horizon': 1, 'player_id': 430832, 'origin_year': 2016, 'elapsed': 12, 'current_state': 3, 'regular_window': 3, 'age': 35.0, 'quality_0': 0.5920253691863163, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 75, 'current_players': 319, 'regular_players': 186, 'joint_players': 172, 'quality_joint_players': 251, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 22833, 'horizon': 1, 'player_id': 430832, 'origin_year': 2016, 'elapsed': 12, 'current_state': 3, 'regular_window': 3, 'age': 35.0, 'quality_0': 0.5920253691863163, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 36, 'current_players': 313, 'regular_players': 182, 'joint_players': 168, 'quality_joint_players': 246, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Bautista had 517 MLB PA, 22 HR and 86 BB at age35 after 673/666-PA seasons with 35/40 HR. A zero roster flag and age suppress participation to 55.0% in count binary, while conditional PA remains 488; expected PA drops 427 to 268 (scouting 260) versus actual 686. This is the count arm's largest value improvement only because fixed batting rate 2.276 is far above observed -1.223. Less playing time hides a talent miss and worsens workload. Roster absence alone does not prove loss of a job. His active age/rank profile has 54 people, and peers Davis/Phillips/Pagan/Zobrist include actual 366/604/0/496 PA. The broader origin-only diagnostic shows established 400-PA unlisted hitters' participation is understated, but their total PA is almost correct through offsetting conditional use; this case does not justify indiscriminately removing the roster feature.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rajai Davis | 35.0 | 495 | 0 | 0.0 | 0.50013 | 259.37 | 129.72 | 366 | -0.10215 |
| Brandon Phillips | 35.0 | 584 | 0 | 0.0 | 0.94050 | 485.53 | 456.64 | 604 | 1.67677 |
| Ángel Pagán | 34.0 | 543 | 11 | 0.0 | 0.61877 | 365.59 | 226.21 | 0 | 0.00000 |
| Ben Zobrist | 35.0 | 631 | 0 | 0.0 | 0.98869 | 500.32 | 494.66 | 496 | 0.75896 |

## Joey Votto — 2016 to 2017

Player 458015; row 23027; fold 0; age 32.0; Current MLB; snapshot MLB. Selection: binary_count value largest harm, binary_scout value largest harm.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2014 | AAA | 6 | 2 | 0 | 2 | 0 |
| 2014 | MLB | 272 | 62 | 6 | 49 | 45 |
| 2015 | MLB | 695 | 158 | 29 | 135 | 128 |
| 2016 | MLB | 677 | 158 | 29 | 120 | 93 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 609.199971 | 2.941897 | 4.868271 |
| scout | Not estimated | Not estimated | 619.827687 | 2.941897 | 4.953200 |
| fallback | Not estimated | Not estimated | 609.199971 | 2.941897 | 4.868271 |
| binary_count | 0.994186 | 533.261557 | 530.161290 | 2.941897 | 4.236653 |
| binary_scout | 0.993924 | 550.892890 | 547.545794 | 2.941897 | 4.375577 |
| Actual | 1 | 707 | 707 | 4.964083787515388 | 8.024202 |

### binary_count: probability and workload accounting

Effective probability 0.99418622 × bounded conditional PA 533.261557 = expected PA 530.161290. Contribution = that PA × (2.941897/600 + 0.00308809). Raw probability 0.99418622 is preserved separately from any availability override.

participation: reference -4.071018 plus all saved terms = raw 5.141693 log odds; logistic link gives probability 0.99418622. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.342696 log odds |
| games_mlb_0 | 158.0 | 2.031703 log odds |
| quality_0 | 1.616572540824181 | 0.776990 log odds |
| MLB_0_pa | 677.0 | 0.771031 log odds |
| pooled_MLB_pa | 1396.2 | 0.434219 log odds |
| games_mlb_1 | 158.0 | 0.366264 log odds |
| pooled_MLB_BB | 0.15399010827429488 | 0.305639 log odds |
| games_pool_MLB | 321.59999999999997 | 0.277300 log odds |

conditional_pa: reference 281.257322 plus all saved terms = raw 533.261557 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 677.5576606260296 | 109.367029 PA |
| role_mlb_0 | 4.267857142857143 | 46.589028 PA |
| age_centered | 1.0 | -39.619684 PA |
| role_pool_MLB | 4.33112183353438 | 32.755465 PA |
| MLB_0_pa | 677.0 | 32.531959 PA |
| quality_0 | 1.616572540824181 | 20.603884 PA |
| pooled_MLB_HR | 0.03929955888250234 | 16.469478 PA |
| regular_window_scaled | 0.6666666666666666 | 13.087230 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99392423 × bounded conditional PA 550.892890 = expected PA 547.545794. Contribution = that PA × (2.941897/600 + 0.00308809). Raw probability 0.99392423 is preserved separately from any availability override.

participation: reference -4.061750 plus all saved terms = raw 5.097353 log odds; logistic link gives probability 0.99392423. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.342652 log odds |
| games_mlb_0 | 158.0 | 1.991698 log odds |
| quality_0 | 1.616572540824181 | 0.778969 log odds |
| MLB_0_pa | 677.0 | 0.741453 log odds |
| pooled_MLB_pa | 1396.2 | 0.429416 log odds |
| games_mlb_1 | 158.0 | 0.356815 log odds |
| games_pool_MLB | 321.59999999999997 | 0.329380 log odds |
| pooled_MLB_BB | 0.15399010827429488 | 0.253408 log odds |
| scout_rank_score_0 | 0.0 | -0.002993 log odds |

conditional_pa: reference 281.301982 plus all saved terms = raw 550.892890 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 677.5576606260296 | 106.652553 PA |
| role_mlb_0 | 4.267857142857143 | 46.820166 PA |
| age_centered | 1.0 | -33.331664 PA |
| role_pool_MLB | 4.33112183353438 | 32.033953 PA |
| MLB_0_pa | 677.0 | 29.150477 PA |
| quality_0 | 1.616572540824181 | 24.123227 PA |
| pooled_MLB_HR | 0.03929955888250234 | 16.626270 PA |
| regular_window_scaled | 0.6666666666666666 | 15.110932 PA |
| scout_rank_score_0 | 0.0 | -0.391953 PA |

Full-population rank profile: [{'row_id': 23027, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'rank_profile_players': 285}]. Active-label conditional profile: [{'row_id': 23027, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 224}].

Actual original-fold general support: [{'row_id': 23027, 'horizon': 1, 'player_id': 458015, 'origin_year': 2016, 'elapsed': 9, 'current_state': 3, 'regular_window': 2, 'age': 32.0, 'quality_0': 1.616572540824181, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 160, 'current_players': 307, 'regular_players': 220, 'joint_players': 161, 'quality_joint_players': 46, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 23027, 'horizon': 1, 'player_id': 458015, 'origin_year': 2016, 'elapsed': 9, 'current_state': 3, 'regular_window': 2, 'age': 32.0, 'quality_0': 1.616572540824181, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 94, 'current_players': 301, 'regular_players': 190, 'joint_players': 155, 'quality_joint_players': 46, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 23027, 'horizon': 1, 'player_id': 458015, 'origin_year': 2016, 'elapsed': 9, 'current_state': 3, 'regular_window': 2, 'age': 32.0, 'quality_0': 1.616572540824181, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 160, 'current_players': 307, 'regular_players': 220, 'joint_players': 161, 'quality_joint_players': 46, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 23027, 'horizon': 1, 'player_id': 458015, 'origin_year': 2016, 'elapsed': 9, 'current_state': 3, 'regular_window': 2, 'age': 32.0, 'quality_0': 1.616572540824181, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 2, 'elapsed_players': 94, 'current_players': 301, 'regular_players': 190, 'joint_players': 155, 'quality_joint_players': 46, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Votto had back-to-back 695/677-PA MLB seasons, 29 HR each and 128/93 BB, following a low-use 2014. Both heads give about 99.4% participation, so arrival is not the issue. Conditional PA is only 533–551; expected 530/548 falls below direct 609 and actual 707, producing both arms' largest value deterioration. Age subtracts from conditional opportunity while extensive work/role increases it. Fixed rate 2.942 also understates actual 4.964. This is a regular-player workload/talent compression case, not missing scouting or lack of training (224 active-profile people). Pedroia/Ramirez/Cabrera/Encarnacion have varying subsequent use, but a generic age penalty should not be assumed sufficient for an exceptional established hitter.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dustin Pedroia | 32.0 | 698 | 0 | 0.0 | 0.98655 | 551.13 | 543.72 | 463 | 1.78839 |
| Hanley Ramirez | 32.0 | 620 | 0 | 0.0 | 0.99123 | 536.54 | 531.84 | 553 | 1.50561 |
| Miguel Cabrera | 33.0 | 679 | 0 | 0.0 | 0.97570 | 534.00 | 521.02 | 529 | 1.24760 |
| Edwin Encarnación | 33.0 | 702 | 0 | 0.0 | 0.86172 | 500.39 | 431.19 | 669 | 4.98649 |

## Fernando Tatis Jr. — 2021 to 2022

Player 665487; row 43296; fold 0; age 22.0; Current MLB; snapshot MLB. Selection: binary_count value false high.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | AA | 8 | 2 | 0 | 1 | 3 |
| 2019 | MLB | 372 | 84 | 22 | 110 | 29 |
| 2020 | MLB | 257 | 59 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 130 | 42 | 153 | 56 |

Historical rank rows: [{'season': 2019, 'player_id': 665487, 'rank': 2, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Fernando Tatis Jr.'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 524.986636 | 2.746999 | 4.049398 |
| scout | Not estimated | Not estimated | 517.722709 | 2.746999 | 3.993369 |
| fallback | Not estimated | Not estimated | 524.986636 | 2.746999 | 4.049398 |
| binary_count | 0.989240 | 548.158746 | 542.260520 | 2.746999 | 4.182637 |
| binary_scout | 0.990750 | 546.431647 | 541.377302 | 2.746999 | 4.175825 |
| Actual | 0 | Unobserved | 0 | Unobserved | 0.000000 |

### binary_count: probability and workload accounting

Effective probability 0.98923993 × bounded conditional PA 548.158746 = expected PA 542.260520. Contribution = that PA × (2.746999/600 + 0.00313500). Raw probability 0.98923993 is preserved separately from any availability override.

participation: reference -4.104175 plus all saved terms = raw 4.521095 log odds; logistic link gives probability 0.98923993. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.925011 log odds |
| games_mlb_0 | 130.0 | 1.573433 log odds |
| work_0 | 546.2247838616715 | 0.992089 log odds |
| games_pool_MLB | 307.84 | 0.798476 log odds |
| quality_0 | 1.347878741765764 | 0.635794 log odds |
| pooled_mlb_quality | 1.8507237898777469 | 0.320558 log odds |
| position_6 | 1.0 | 0.237364 log odds |
| pooled_MLB_pa | 974.8 | 0.153956 log odds |

conditional_pa: reference 279.729726 plus all saved terms = raw 548.158746 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 546.2247838616715 | 119.335254 PA |
| role_mlb_0 | 4.185714285714286 | 43.327316 PA |
| role_pool_MLB | 4.271043771043771 | 32.516914 PA |
| age_centered | -1.0 | 24.773323 PA |
| pooled_MLB_K | 0.27056196501674734 | -23.358504 PA |
| pooled_mlb_quality | 1.8507237898777469 | 15.300559 PA |
| quality_0 | 1.347878741765764 | 15.046920 PA |
| pooled_MLB_pa | 974.8 | 14.779719 PA |

### binary_scout: probability and workload accounting

Effective probability 0.99075027 × bounded conditional PA 546.431647 = expected PA 541.377302. Contribution = that PA × (2.746999/600 + 0.00313500). Raw probability 0.99075027 is preserved separately from any availability override.

participation: reference -4.091881 plus all saved terms = raw 4.673868 log odds; logistic link gives probability 0.99075027. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.949607 log odds |
| games_mlb_0 | 130.0 | 1.563050 log odds |
| work_0 | 546.2247838616715 | 1.007460 log odds |
| games_pool_MLB | 307.84 | 0.788975 log odds |
| quality_0 | 1.347878741765764 | 0.657388 log odds |
| pooled_mlb_quality | 1.8507237898777469 | 0.344611 log odds |
| position_6 | 1.0 | 0.224308 log odds |
| MLB_0_pa | 546.0 | 0.132553 log odds |
| scout_listed_0 | -1.0 | 0.073796 log odds |
| scout_rank_score_0 | -1.0 | -0.002839 log odds |

conditional_pa: reference 279.724289 plus all saved terms = raw 546.431647 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 546.2247838616715 | 119.209490 PA |
| role_mlb_0 | 4.185714285714286 | 37.807977 PA |
| role_pool_MLB | 4.271043771043771 | 30.942937 PA |
| pooled_MLB_K | 0.27056196501674734 | -24.689691 PA |
| pooled_mlb_quality | 1.8507237898777469 | 21.128056 PA |
| age_centered | -1.0 | 20.819402 PA |
| quality_0 | 1.347878741765764 | 18.199078 PA |
| role_mlb_2 | 4.382978723404255 | 15.553716 PA |
| scout_rank_score_0 | -1.0 | -0.610543 PA |
| scout_listed_0 | -1.0 | -0.133710 PA |

Full-population rank profile: [{'row_id': 43296, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'unknown', 'rank_profile_players': 64}]. Active-label conditional profile: [{'row_id': 43296, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'unknown', 'conditional_rank_profile_players': 58}].

Actual original-fold general support: [{'row_id': 43296, 'horizon': 1, 'player_id': 665487, 'origin_year': 2021, 'elapsed': 2, 'current_state': 3, 'regular_window': 2, 'age': 22.0, 'quality_0': 1.347878741765764, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 2, 'elapsed_players': 708, 'current_players': 397, 'regular_players': 361, 'joint_players': 24, 'quality_joint_players': 10, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 43296, 'horizon': 1, 'player_id': 665487, 'origin_year': 2021, 'elapsed': 2, 'current_state': 3, 'regular_window': 2, 'age': 22.0, 'quality_0': 1.347878741765764, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 2, 'elapsed_players': 443, 'current_players': 390, 'regular_players': 321, 'joint_players': 24, 'quality_joint_players': 10, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 43296, 'horizon': 1, 'player_id': 665487, 'origin_year': 2021, 'elapsed': 2, 'current_state': 3, 'regular_window': 2, 'age': 22.0, 'quality_0': 1.347878741765764, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 2, 'elapsed_players': 708, 'current_players': 397, 'regular_players': 361, 'joint_players': 24, 'quality_joint_players': 10, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 43296, 'horizon': 1, 'player_id': 665487, 'origin_year': 2021, 'elapsed': 2, 'current_state': 3, 'regular_window': 2, 'age': 22.0, 'quality_0': 1.347878741765764, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 2, 'elapsed_players': 443, 'current_players': 390, 'regular_players': 321, 'joint_players': 24, 'quality_joint_players': 10, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Tatis had 546 MLB PA and 42 HR in 2021, with previous MLB success and a positive roster flag. The models estimate about 99% participation and 546–548 conditional PA, 541/542 expected versus actual zero; the count arm's largest value false high. Those predictions are understandable from the supplied production record. The following year's absence is not known from this table and cannot be inserted into an earlier forecast; no future suspension/injury detail is treated as origin evidence. Soto/Guerrero/Bichette subsequently play regularly while Baddoo gets much less use. This contrasts with the 2022-origin case: prospective sudden absence and a known missed-year return are different mechanisms, not a single universal health discount.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Juan Soto | 22.0 | 654 | 0 | -1.0 | 0.99433 | 615.61 | 612.11 | 664 | 5.61671 |
| Akil Baddoo | 22.0 | 461 | 18 | -1.0 | 0.97046 | 409.04 | 396.96 | 225 | -0.22757 |
| Vladimir Guerrero Jr. | 22.0 | 698 | 0 | -1.0 | 0.99347 | 632.81 | 628.68 | 706 | 4.51175 |
| Bo Bichette | 23.0 | 690 | 0 | -1.0 | 0.99600 | 624.98 | 622.48 | 697 | 4.41343 |

## Jorge Mateo — 2021 to 2022

Player 622761; row 42636; fold 2; age 26.0; Current MLB; snapshot MLB. Selection: binary_count value ordinary.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2019 | AAA | 566 | 119 | 19 | 145 | 28 |
| 2020 | MLB | 28 | 22 | 0 | 11 | 1 |
| 2021 | MLB | 209 | 89 | 4 | 55 | 9 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 177.960273 | -0.727931 | 0.342001 |
| scout | Not estimated | Not estimated | 185.977854 | -0.727931 | 0.357409 |
| fallback | Not estimated | Not estimated | 177.960273 | -0.727931 | 0.342001 |
| binary_count | 0.906295 | 195.084491 | 176.804049 | -0.727931 | 0.339779 |
| binary_scout | 0.907994 | 192.331720 | 174.636068 | -0.727931 | 0.335613 |
| Actual | 1 | 533 | 533 | -1.4969946821878757 | 0.338979 |

### binary_count: probability and workload accounting

Effective probability 0.90629474 × bounded conditional PA 195.084491 = expected PA 176.804049. Contribution = that PA × (-0.727931/600 + 0.00313500). Raw probability 0.90629474 is preserved separately from any availability override.

participation: reference -4.056612 plus all saved terms = raw 2.269210 log odds; logistic link gives probability 0.90629474. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.653712 log odds |
| games_mlb_0 | 89.0 | 1.718592 log odds |
| games_pool_MLB | 136.52 | 0.971167 log odds |
| role_pool_AAA | 4.663390663390664 | 0.280495 log odds |
| work_0 | 209.08604363935777 | 0.257881 log odds |
| pooled_AAA_3B | 0.020245677888989993 | 0.181202 log odds |
| quality_0 | -0.1657588047476541 | -0.148012 log odds |
| career_mlb_observed_pa | 237.0 | -0.122423 log odds |

conditional_pa: reference 281.962613 plus all saved terms = raw 195.084491 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 209.08604363935777 | -27.213158 PA |
| role_mlb_0 | 2.515151515151515 | -22.016509 PA |
| role_pool_AAA | 4.663390663390664 | 18.279359 PA |
| role_pool_MLB | 2.327615780445969 | -17.068210 PA |
| on_40man | 1.0 | 15.144150 PA |
| quality_0 | -0.1657588047476541 | -13.024654 PA |
| pooled_MLB_K | 0.2619191309595655 | -10.676685 PA |
| pooled_AAA_K | 0.2502274795268426 | -7.594739 PA |

### binary_scout: probability and workload accounting

Effective probability 0.90799411 × bounded conditional PA 192.331720 = expected PA 174.636068. Contribution = that PA × (-0.727931/600 + 0.00313500). Raw probability 0.90799411 is preserved separately from any availability override.

participation: reference -4.074246 plus all saved terms = raw 2.289385 log odds; logistic link gives probability 0.90799411. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.652961 log odds |
| games_mlb_0 | 89.0 | 1.722683 log odds |
| games_pool_MLB | 136.52 | 0.936139 log odds |
| role_pool_AAA | 4.663390663390664 | 0.246161 log odds |
| work_0 | 209.08604363935777 | 0.232316 log odds |
| pooled_AAA_3B | 0.020245677888989993 | 0.180181 log odds |
| quality_0 | -0.1657588047476541 | -0.158808 log odds |
| age_squared | 0.04000000000000001 | 0.130598 log odds |
| scout_list_capacity_2 | 100.0 | 0.060340 log odds |
| scout_list_capacity_0 | 99.0 | 0.028487 log odds |
| scout_listed_0 | -1.0 | 0.007183 log odds |
| scout_rank_score_0 | -1.0 | -0.006010 log odds |

conditional_pa: reference 281.956020 plus all saved terms = raw 192.331720 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| work_0 | 209.08604363935777 | -28.847227 PA |
| role_mlb_0 | 2.515151515151515 | -23.427975 PA |
| role_pool_AAA | 4.663390663390664 | 21.211735 PA |
| role_pool_MLB | 2.327615780445969 | -15.074642 PA |
| on_40man | 1.0 | 14.547420 PA |
| quality_0 | -0.1657588047476541 | -13.741665 PA |
| pooled_MLB_K | 0.2619191309595655 | -11.824300 PA |
| pooled_AAA_K | 0.2502274795268426 | -9.030086 PA |
| scout_rank_score_0 | -1.0 | -2.292123 PA |
| scout_rank_score_1 | -1.0 | -0.148304 PA |

Full-population rank profile: [{'row_id': 42636, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'unknown', 'rank_profile_players': 229}]. Active-label conditional profile: [{'row_id': 42636, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'unknown', 'conditional_rank_profile_players': 202}].

Actual original-fold general support: [{'row_id': 42636, 'horizon': 1, 'player_id': 622761, 'origin_year': 2021, 'elapsed': 1, 'current_state': 2, 'regular_window': 0, 'age': 26.0, 'quality_0': -0.1657588047476541, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 716, 'current_players': 583, 'regular_players': 9765, 'joint_players': 85, 'quality_joint_players': 198, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 42636, 'horizon': 1, 'player_id': 622761, 'origin_year': 2021, 'elapsed': 1, 'current_state': 2, 'regular_window': 0, 'age': 26.0, 'quality_0': -0.1657588047476541, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 511, 'current_players': 510, 'regular_players': 1062, 'joint_players': 78, 'quality_joint_players': 182, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 42636, 'horizon': 1, 'player_id': 622761, 'origin_year': 2021, 'elapsed': 1, 'current_state': 2, 'regular_window': 0, 'age': 26.0, 'quality_0': -0.1657588047476541, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 716, 'current_players': 583, 'regular_players': 9765, 'joint_players': 85, 'quality_joint_players': 198, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 42636, 'horizon': 1, 'player_id': 622761, 'origin_year': 2021, 'elapsed': 1, 'current_state': 2, 'regular_window': 0, 'age': 26.0, 'quality_0': -0.1657588047476541, 'elapsed_band': 1, 'age_band': 2, 'quality_band': 1, 'elapsed_players': 511, 'current_players': 510, 'regular_players': 1062, 'joint_players': 78, 'quality_joint_players': 182, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Mateo had 209 MLB PA over 89 games in 2021 after 28 PA in the shortened 2020 season and 566 AAA PA in 2019. Both binary heads assign about 91% participation but only 192–195 conditional PA, 175/177 expected versus 533 actual; part-time use suppresses conditional role. Predicted .340 contribution almost equals .339 actual in the ordinary value-selected case only because the fixed batting rate -.728 is far too optimistic versus -1.497 actual. Severe workload and talent errors offset, so this cannot certify the architecture. Two hundred two active-profile people are available, and McGuire/Frazier/Collins/Jansen span 45 to 274 actual PA; the peer set does not guarantee Mateo's eventual expanded job.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Reese McGuire | 26.0 | 217 | 0 | -1.0 | 0.96594 | 209.92 | 202.77 | 274 | 0.44112 |
| Clint Frazier | 26.0 | 218 | 11 | -1.0 | 0.93822 | 288.03 | 270.24 | 45 | 0.13992 |
| Zack Collins | 26.0 | 231 | 38 | -1.0 | 0.95862 | 202.39 | 194.01 | 108 | -0.23401 |
| Danny Jansen | 26.0 | 205 | 26 | -1.0 | 0.97656 | 239.15 | 233.55 | 248 | 1.85057 |

## Eloy Jiménez — 2018 to 2019

Player 650391; row 33651; fold 4; age 21.0; Upper minors; snapshot AAA. Selection: binary_scout pa largest gain.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | A | 464 | 112 | 14 | 94 | 22 |
| 2017 | AA | 73 | 18 | 3 | 16 | 4 |
| 2017 | Aplus | 296 | 71 | 16 | 56 | 25 |
| 2018 | AA | 228 | 53 | 10 | 39 | 18 |
| 2018 | AAA | 228 | 55 | 12 | 30 | 12 |

Historical rank rows: [{'season': 2017, 'player_id': 650391, 'rank': 14, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Eloy Jiménez'}, {'season': 2018, 'player_id': 650391, 'rank': 4, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Eloy Jiménez'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 81.674214 | 0.151706 | 0.272107 |
| scout | Not estimated | Not estimated | 309.865582 | 0.151706 | 1.032352 |
| fallback | Not estimated | Not estimated | 309.865582 | 0.151706 | 1.032352 |
| binary_count | 0.738405 | 156.032079 | 115.214798 | 0.151706 | 0.383851 |
| binary_scout | 0.889190 | 347.989576 | 309.428752 | 0.151706 | 1.030897 |
| Actual | 1 | 504 | 504 | 1.3650099206111617 | 2.686209 |

### binary_count: probability and workload accounting

Effective probability 0.73840455 × bounded conditional PA 156.032079 = expected PA 115.214798. Contribution = that PA × (0.151706/600 + 0.00307877). Raw probability 0.73840455 is preserved separately from any availability override.

participation: reference -4.163750 plus all saved terms = raw 1.037693 log odds; logistic link gives probability 0.73840455. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.921463 log odds |
| games_minor_0 | 108.0 | 0.381534 log odds |
| pooled_AA_pa | 286.4 | 0.345688 log odds |
| games_mlb_0 | 0.0 | -0.338704 log odds |
| games_pool_MLB | 0.0 | -0.255298 log odds |
| role_pool_AA | 4.217054263565891 | 0.250276 log odds |
| pooled_AA_K | 0.19358178053830227 | 0.232723 log odds |
| career_mlb_observed_pa | 0.0 | -0.228635 log odds |

conditional_pa: reference 283.113737 plus all saved terms = raw 156.032079 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 0.0 | -74.160420 PA |
| work_0 | 0.0 | -41.511719 PA |
| age_centered | -1.2 | 16.740638 PA |
| on_40man | 1.0 | 10.904167 PA |
| pooled_A_BB | 0.056025369978858354 | -10.681680 PA |
| quality_0 | 0.0 | -8.886494 PA |
| pooled_A_HBP | 0.008985200845665963 | 8.704394 PA |
| pooled_Aplus_3B | 0.008610451306413303 | 8.218520 PA |

### binary_scout: probability and workload accounting

Effective probability 0.88918972 × bounded conditional PA 347.989576 = expected PA 309.428752. Contribution = that PA × (0.151706/600 + 0.00307877). Raw probability 0.88918972 is preserved separately from any availability override.

participation: reference -4.172722 plus all saved terms = raw 2.082491 log odds; logistic link gives probability 0.88918972. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 3.903013 log odds |
| scout_rank_score_0 | 0.97 | 0.541939 log odds |
| scout_listed_0 | 1.0 | 0.383200 log odds |
| games_minor_0 | 108.0 | 0.373035 log odds |
| pooled_AA_pa | 286.4 | 0.348923 log odds |
| games_mlb_0 | 0.0 | -0.345617 log odds |
| role_pool_AA | 4.217054263565891 | 0.281471 log odds |
| pooled_AA_K | 0.19358178053830227 | 0.256283 log odds |

conditional_pa: reference 283.076477 plus all saved terms = raw 347.989576 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.97 | 193.455995 PA |
| MLB_0_pa | 0.0 | -71.014086 PA |
| work_0 | 0.0 | -40.418228 PA |
| pooled_A_HBP | 0.008985200845665963 | 12.688495 PA |
| games_pool_Aplus | 56.800000000000004 | -10.073311 PA |
| regular_window_scaled | 0.0 | -9.767511 PA |
| on_40man | 1.0 | 9.406914 PA |
| quality_0 | 0.0 | -8.676000 PA |
| scout_rank_score_1 | 0.87 | -3.038369 PA |
| scout_list_capacity_2 | 100.0 | 1.013666 PA |

Full-population rank profile: [{'row_id': 33651, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 7}]. Active-label conditional profile: [{'row_id': 33651, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 4}].

Actual original-fold general support: [{'row_id': 33651, 'horizon': 1, 'player_id': 650391, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 7449, 'current_players': 7884, 'regular_players': 8017, 'joint_players': 6012, 'quality_joint_players': 7524, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 33651, 'horizon': 1, 'player_id': 650391, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 540, 'current_players': 633, 'regular_players': 842, 'joint_players': 225, 'quality_joint_players': 564, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 33651, 'horizon': 1, 'player_id': 650391, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 7449, 'current_players': 7884, 'regular_players': 8017, 'joint_players': 6012, 'quality_joint_players': 7524, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 33651, 'horizon': 1, 'player_id': 650391, 'origin_year': 2018, 'elapsed': -1, 'current_state': 0, 'regular_window': 0, 'age': 21.0, 'quality_0': 0.0, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 540, 'current_players': 633, 'regular_players': 842, 'joint_players': 225, 'quality_joint_players': 564, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Jimenez had 456 AA/AAA PA, 22 HR, 69 K and 30 BB, rank four after fourteen, and roster listing. Count binary gives 73.8% × 156 = 115 PA; scouting gives 88.9% × 348 = 309 versus direct count 82 and actual 504, its largest PA gain. Roster and rank increase probability; rank also strongly raises conditional use, a plausible readiness mechanism on meaningful upper-level production. Only four earlier active-label people match the top20 profile, so this is not deeply supported conditional certainty. Rodgers/Hiura/Bichette/Sanchez later span 0 to 348 PA. Value rises .272 to 1.031 versus 2.686 but fixed batting rate still understates actual; this is a genuine opportunity gain, not an exact elite talent projection.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Brendan Rodgers | 21.0 | 0 | 474 | 0.86 | 0.54634 | 271.94 | 148.57 | 81 | -0.33082 |
| Keston Hiura | 21.0 | 0 | 535 | 0.45 | 0.33497 | 239.47 | 80.22 | 348 | 3.13002 |
| Bo Bichette | 20.0 | 0 | 595 | 0.87 | 0.57487 | 261.02 | 150.05 | 212 | 1.86286 |
| Jesús Sánchez | 20.0 | 0 | 488 | 0.44 | 0.39790 | 99.30 | 39.51 | 0 | 0.00000 |

## Lucas Duda — 2017 to 2018

Player 446263; row 27521; fold 2; age 31.0; Current MLB; snapshot MLB. Selection: binary_scout pa ordinary.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2015 | AA | 7 | 2 | 0 | 1 | 1 |
| 2015 | MLB | 554 | 135 | 27 | 138 | 59 |
| 2016 | MLB | 172 | 47 | 7 | 36 | 13 |
| 2017 | Aplus | 19 | 5 | 2 | 6 | 2 |
| 2017 | MLB | 491 | 127 | 30 | 135 | 54 |

Historical rank rows: []. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 1/2007/243; roster flag 0; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 358.619309 | 0.839407 | 1.604888 |
| scout | Not estimated | Not estimated | 356.913124 | 0.839407 | 1.597253 |
| fallback | Not estimated | Not estimated | 358.619309 | 0.839407 | 1.604888 |
| binary_count | 0.861475 | 438.099632 | 377.411744 | 0.839407 | 1.688988 |
| binary_scout | 0.865971 | 423.779118 | 366.980332 | 0.839407 | 1.642306 |
| Actual | 1 | 367 | 367 | 0.09430949351048923 | 1.188059 |

### binary_count: probability and workload accounting

Effective probability 0.86147469 × bounded conditional PA 438.099632 = expected PA 377.411744. Contribution = that PA × (0.839407/600 + 0.00307618). Raw probability 0.86147469 is preserved separately from any availability override.

participation: reference -3.977373 plus all saved terms = raw 1.827593 log odds; logistic link gives probability 0.86147469. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 127.0 | 2.099029 log odds |
| games_pool_MLB | 245.6 | 1.551037 log odds |
| on_40man | 0.0 | -0.929239 log odds |
| quality_0 | 0.2868619197148927 | 0.887653 log odds |
| MLB_0_pa | 491.0 | 0.558763 log odds |
| work_0 | 491.0 | 0.543731 log odds |
| pooled_MLB_pa | 961.0 | 0.360009 log odds |
| games_mlb_1 | 47.0 | 0.305166 log odds |

conditional_pa: reference 282.341172 plus all saved terms = raw 438.099632 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 491.0 | 75.482795 PA |
| work_0 | 491.0 | 45.062884 PA |
| quality_0 | 0.2868619197148927 | 38.152330 PA |
| role_mlb_2 | 4.096551724137931 | 14.430935 PA |
| age_centered | 0.8 | -11.993540 PA |
| pooled_Aplus_K | 0.24369747899159663 | 11.222296 PA |
| role_mlb_0 | 3.875912408759124 | -10.762454 PA |
| pooled_MLB_K | 0.25409990574929314 | -10.700708 PA |

### binary_scout: probability and workload accounting

Effective probability 0.86597078 × bounded conditional PA 423.779118 = expected PA 366.980332. Contribution = that PA × (0.839407/600 + 0.00307618). Raw probability 0.86597078 is preserved separately from any availability override.

participation: reference -3.974506 plus all saved terms = raw 1.865793 log odds; logistic link gives probability 0.86597078. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| games_mlb_0 | 127.0 | 2.092424 log odds |
| games_pool_MLB | 245.6 | 1.549162 log odds |
| on_40man | 0.0 | -0.926467 log odds |
| quality_0 | 0.2868619197148927 | 0.898974 log odds |
| work_0 | 491.0 | 0.563465 log odds |
| MLB_0_pa | 491.0 | 0.500935 log odds |
| games_mlb_1 | 47.0 | 0.354344 log odds |
| pooled_MLB_pa | 961.0 | 0.343775 log odds |
| scout_rank_score_0 | 0.0 | -0.002737 log odds |

conditional_pa: reference 282.334255 plus all saved terms = raw 423.779118 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 491.0 | 77.598878 PA |
| work_0 | 491.0 | 43.170315 PA |
| quality_0 | 0.2868619197148927 | 36.292665 PA |
| role_mlb_2 | 4.096551724137931 | 15.181011 PA |
| on_40man | 0.0 | -14.789706 PA |
| regular_window_scaled | 0.6666666666666666 | 12.796454 PA |
| pooled_MLB_K | 0.25409990574929314 | -11.663593 PA |
| age_centered | 0.8 | -11.585480 PA |
| scout_rank_score_0 | 0.0 | -0.698187 PA |

Full-population rank profile: [{'row_id': 27521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'rank_profile_players': 336}]. Active-label conditional profile: [{'row_id': 27521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'conditional_rank_profile_players': 264}].

Actual original-fold general support: [{'row_id': 27521, 'horizon': 1, 'player_id': 446263, 'origin_year': 2017, 'elapsed': 7, 'current_state': 3, 'regular_window': 2, 'age': 31.0, 'quality_0': 0.2868619197148927, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 260, 'current_players': 340, 'regular_players': 266, 'joint_players': 193, 'quality_joint_players': 273, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 27521, 'horizon': 1, 'player_id': 446263, 'origin_year': 2017, 'elapsed': 7, 'current_state': 3, 'regular_window': 2, 'age': 31.0, 'quality_0': 0.2868619197148927, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 155, 'current_players': 334, 'regular_players': 230, 'joint_players': 189, 'quality_joint_players': 268, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 27521, 'horizon': 1, 'player_id': 446263, 'origin_year': 2017, 'elapsed': 7, 'current_state': 3, 'regular_window': 2, 'age': 31.0, 'quality_0': 0.2868619197148927, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 260, 'current_players': 340, 'regular_players': 266, 'joint_players': 193, 'quality_joint_players': 273, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 27521, 'horizon': 1, 'player_id': 446263, 'origin_year': 2017, 'elapsed': 7, 'current_state': 3, 'regular_window': 2, 'age': 31.0, 'quality_0': 0.2868619197148927, 'elapsed_band': 2, 'age_band': 3, 'quality_band': 1, 'elapsed_players': 155, 'current_players': 334, 'regular_players': 230, 'joint_players': 189, 'quality_joint_players': 268, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': False, 'extrapolation': False, 'profile_check_pass': True, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Duda had 491 MLB PA, 30 HR and 54 BB in 2017 after 172 PA in 2016 and 554 in 2015; the roster flag is zero. Scouting binary gives 86.6% × 424 = 366.98 PA versus 367 actual, the ordinary scouting-arm workload case. Count binary gives 377 and direct 359. Known use supports return despite absent listing, unlike a blanket roster-zero policy. Fixed batting rate .839 misses actual .094, so value 1.642 overstates 1.188. Two hundred sixty-four active-profile people and Fowler/Walker/Lucroy/Gonzalez outcomes provide a populated but variable comparable set. Near-exact PA does not imply accurate batting or known health.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dexter Fowler | 31.0 | 491 | 0 | 0.0 | 0.98903 | 487.16 | 481.82 | 334 | -0.38484 |
| Neil Walker | 31.0 | 448 | 20 | 0.0 | 0.93255 | 481.45 | 448.97 | 398 | 0.49169 |
| Jonathan Lucroy | 31.0 | 481 | 0 | 0.0 | 0.90853 | 368.50 | 334.80 | 454 | -0.16628 |
| Carlos González | 31.0 | 534 | 0 | 0.0 | 0.90697 | 421.81 | 382.56 | 504 | 2.53708 |

## Francisco Mejía — 2018 to 2019

Player 642336; row 33489; fold 3; age 22.0; Current MLB; snapshot MLB. Selection: binary_scout value ordinary.

| Source year | Level | PA | Games | HR | K | UBB |
|---|---|---:|---:|---:|---:|---:|
| 2016 | A | 259 | 60 | 7 | 39 | 12 |
| 2016 | Aplus | 184 | 42 | 4 | 24 | 13 |
| 2017 | AA | 383 | 92 | 14 | 53 | 23 |
| 2017 | MLB | 14 | 11 | 0 | 3 | 0 |
| 2018 | AAA | 468 | 110 | 14 | 83 | 23 |
| 2018 | MLB | 62 | 21 | 3 | 19 | 5 |

Historical rank rows: [{'season': 2017, 'player_id': 642336, 'rank': 40, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Francisco Mejía'}, {'season': 2018, 'player_id': 642336, 'rank': 11, 'list_capacity': 100, 'list_complete': True, 'player_name': 'Francisco Mejía'}]. Source editions remain qualified; a complete-table absence is not a zero scouting grade. Partial/missing-table absence is unknown.

Draft known/year/pick: 0/None/None; roster flag 1; retirement False; hard unavailable False. Full 251 actual encoded inputs are persisted in cases.json.

| Forecast | MLB probability | PA if active | Expected PA | Fixed batting wins / 600 | Contribution |
|---|---:|---:|---:|---:|---:|---:|
| retired_games | Not estimated | Not estimated | 174.008111 | -0.507244 | 0.388623 |
| scout | Not estimated | Not estimated | 346.337299 | -0.507244 | 0.773496 |
| fallback | Not estimated | Not estimated | 346.337299 | -0.507244 | 0.773496 |
| binary_count | 0.930338 | 224.436174 | 208.801481 | -0.507244 | 0.466329 |
| binary_scout | 0.951093 | 336.615954 | 320.153219 | -0.507244 | 0.715018 |
| Actual | 1 | 244 | 244 | -0.0738220506916443 | 0.715341 |

### binary_count: probability and workload accounting

Effective probability 0.93033791 × bounded conditional PA 224.436174 = expected PA 208.801481. Contribution = that PA × (-0.507244/600 + 0.00307877). Raw probability 0.93033791 is preserved separately from any availability override.

participation: reference -4.126580 plus all saved terms = raw 2.591892 log odds; logistic link gives probability 0.93033791. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.977642 log odds |
| games_mlb_0 | 21.0 | 1.428075 log odds |
| games_pool_MLB | 29.8 | 0.650427 log odds |
| position_2 | 1.0 | 0.437977 log odds |
| pooled_MLB_pa | 73.2 | -0.287079 log odds |
| AAA_0_pa | 468.0 | 0.251227 log odds |
| pooled_AA_K | 0.1609251968503937 | 0.247052 log odds |
| pooled_A_BABIP | 0.3474264705882353 | 0.227838 log odds |

conditional_pa: reference 279.243356 plus all saved terms = raw 224.436174 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| MLB_0_pa | 62.0 | -52.849271 PA |
| work_0 | 61.97449609214315 | -35.277231 PA |
| role_pool_AAA | 4.233333333333333 | 25.818072 PA |
| pooled_A_3B | 0.009005481597494126 | 24.222326 PA |
| quality_0 | -0.08739626755793571 | -13.166773 PA |
| pooled_MLB_K | 0.25635103926096997 | -11.859488 PA |
| on_40man | 1.0 | 11.300950 PA |
| age_centered | -1.0 | 9.719564 PA |

### binary_scout: probability and workload accounting

Effective probability 0.95109342 × bounded conditional PA 336.615954 = expected PA 320.153219. Contribution = that PA × (-0.507244/600 + 0.00307877). Raw probability 0.95109342 is preserved separately from any availability override.

participation: reference -4.122137 plus all saved terms = raw 2.967700 log odds; logistic link gives probability 0.95109342. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| on_40man | 1.0 | 2.977081 log odds |
| games_mlb_0 | 21.0 | 1.516717 log odds |
| scout_rank_score_0 | 0.9 | 0.641737 log odds |
| games_pool_MLB | 29.8 | 0.603789 log odds |
| position_2 | 1.0 | 0.447406 log odds |
| pooled_MLB_pa | 73.2 | -0.289077 log odds |
| games_minor_1 | 92.0 | 0.263771 log odds |
| AAA_0_pa | 468.0 | 0.211299 log odds |
| scout_listed_0 | 1.0 | 0.074413 log odds |
| scout_rank_score_1 | 0.61 | -0.017737 log odds |

conditional_pa: reference 279.277067 plus all saved terms = raw 336.615954 PA; then bound hypothetical PA to [1,800]. Largest eight terms and any remaining ranking terms follow; the complete terms and tree splits remain in cases.json.

| Actual input | Encoded value | Path accounting |
|---|---:|---:|
| scout_rank_score_0 | 0.9 | 138.102711 PA |
| MLB_0_pa | 62.0 | -49.452453 PA |
| work_0 | 61.97449609214315 | -32.563652 PA |
| role_pool_AAA | 4.233333333333333 | 16.731832 PA |
| age_centered | -1.0 | 15.404081 PA |
| quality_0 | -0.08739626755793571 | -12.938392 PA |
| pooled_A_3B | 0.009005481597494126 | 11.018157 PA |
| on_40man | 1.0 | 10.806874 PA |
| scout_list_capacity_2 | 100.0 | -6.949886 PA |
| scout_rank_score_1 | 0.61 | 0.031902 PA |

Full-population rank profile: [{'row_id': 33489, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'top20', 'rank_profile_players': 34}]. Active-label conditional profile: [{'row_id': 33489, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'top20', 'conditional_rank_profile_players': 33}].

Actual original-fold general support: [{'row_id': 33489, 'horizon': 1, 'player_id': 642336, 'origin_year': 2018, 'elapsed': 1, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.08739626755793571, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 576, 'current_players': 836, 'regular_players': 7980, 'joint_players': 14, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'participation'}, {'row_id': 33489, 'horizon': 1, 'player_id': 642336, 'origin_year': 2018, 'elapsed': 1, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.08739626755793571, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 404, 'current_players': 585, 'regular_players': 851, 'joint_players': 12, 'quality_joint_players': 228, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_count', 'head': 'conditional_pa'}, {'row_id': 33489, 'horizon': 1, 'player_id': 642336, 'origin_year': 2018, 'elapsed': 1, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.08739626755793571, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 576, 'current_players': 836, 'regular_players': 7980, 'joint_players': 14, 'quality_joint_players': 326, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'participation'}, {'row_id': 33489, 'horizon': 1, 'player_id': 642336, 'origin_year': 2018, 'elapsed': 1, 'current_state': 1, 'regular_window': 0, 'age': 22.0, 'quality_0': -0.08739626755793571, 'elapsed_band': 1, 'age_band': 0, 'quality_band': 1, 'elapsed_players': 404, 'current_players': 585, 'regular_players': 851, 'joint_players': 12, 'quality_joint_players': 228, 'elapsed_outside': False, 'age_outside': False, 'quality_outside': False, 'unseen_profile': False, 'sparse_profile': True, 'extrapolation': False, 'profile_check_pass': False, 'arm': 'binary_scout', 'head': 'conditional_pa'}].

Mejia had 468 AAA PA with 14 HR and 83 K, a 62-PA MLB sample and verified rank eleven. Scouting gives 95.1% × 337 = 320 expected PA versus count binary 209, direct count 174 and actual 244. Probability of appearance is plausible, but rank raises conditional use enough to worsen PA. Predicted .71502 contribution nearly matches .71534 only because too much workload offsets a fixed -.507 batting rate that is worse than actual -.074. This ordinary product-selected case is not two correct forecasts or catcher defense value. The active top20/debut profile has 33 people. Verdugo/Tucker/Urias/Barreto have 377/72/249/58 next-year PA, demonstrating large opportunity variation even among promising young upper-level hitters.

| Origin-selected peer | Age | MLB PA | Minor PA | Rank score | Scouting probability | Conditional PA | Expected PA | Actual PA | Actual contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Alex Verdugo | 22.0 | 86 | 379 | 0.68 | 0.86654 | 275.84 | 239.03 | 377 | 1.89168 |
| Kyle Tucker | 21.0 | 72 | 465 | 0.84 | 0.92765 | 366.50 | 339.98 | 72 | 0.39212 |
| Luis Urías | 21.0 | 53 | 533 | 0.65 | 0.90549 | 204.25 | 184.95 | 249 | 0.25107 |
| Franklin Barreto | 22.0 | 75 | 333 | 0.35 | 0.90125 | 261.56 | 235.73 | 58 | -0.56564 |

## Decision after the actual reviews

Retain both binary constructions as qualified research. The scouting binary has the best broad/public PA point scores in this reviewed batch, and the ranked-lower-minor expected PA excess falls from 3,769 to 1,044 versus 836 actual. Salas falls from the fallback’s 232 to 7, rather than equating a high ranking with immediate readiness. But ranked lower-minor arrival count is still low (5.55 expected versus nine observed), showing that a reasonable PA sum can conceal opposing probability/workload errors.

Upper never-debut PA is 73,989 versus 92,891 actual, and 593.7 expected participants versus 730 observed. Langford (47 versus 557 PA), Kurtz (2 versus 489) and Bellinger (14 versus 548) remain serious fast-entry misses. Preseason nonlisting is stale for new top draftees and rapidly advancing prospects. Brinson and Mayer remain false highs. Conditional profile support is particularly thin for ranked young players.

On the 1,789 identical public matches, PA RMSE is 142.11 versus Steamer 135.02, but MAE is 110.09 versus 92.40 (19.1% higher), missing the predeclared 15% practical MAE target. The public contribution comparison has an environment qualification and is not proof of superior talent. The fixed rate badly misses Judge/Votto/Bellinger and is not improved by this architecture test.

The origin-only roster/absence diagnostic is separately preserved. Current 400-PA players without a roster listing have almost exact total PA (60,954 versus 60,860) despite too-low participation, offset by conditional use. Therefore do not blanket-remove the roster signal. Prior regulars absent now remain underpredicted (2,052 versus 3,892), with Tatis a consequential miss. No future cause is inserted into a forecast.

No whole-model adoption, protected forecast change or goal completion. Complete the talent/population milestone in the controlling practical plan rather than another marginal workload gate/library sweep. Preserve these readiness models as explicit alternatives and the concrete prospect/absence failures; do not attach a six-year valuation claim to a one-year offense test.
