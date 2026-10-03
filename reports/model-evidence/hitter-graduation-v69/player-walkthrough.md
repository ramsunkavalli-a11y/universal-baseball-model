# Graduation context in hitter opportunity

Same 30,506 historical forecasts, chronological whole-player folds and unchanged hitting. Three new origin-known inputs distinguish sufficient AB graduation and recent ranking history from current absence. Retrospective-list and source-coverage qualifications remain. No protected 2026 use or deployment.

| Group | Rows | Original PA RMSE | Fresh-list PA RMSE | Graduate PA RMSE | Original MAE | Fresh-list MAE | Graduate MAE | Graduate offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 30506 | 60.686 | 60.499 | 60.476 | 20.745 | 20.612 | 20.608 | 0.453243 |
| public_broad | 2627 | 138.488 | 138.330 | 138.196 | 106.871 | 106.411 | 106.321 | 1.060208 |
| previously_ranked_graduates | 274 | 177.598 | 178.907 | 177.953 | 144.396 | 145.510 | 144.858 | 1.409134 |
| never_debut | 24199 | 27.745 | 27.252 | 27.234 | 4.875 | 4.764 | 4.767 | 0.152203 |
| upper_never_debut | 5454 | 56.242 | 55.127 | 55.084 | 19.097 | 18.732 | 18.742 | 0.312690 |
| lower_never_debut | 17852 | 7.828 | 7.966 | 7.973 | 0.656 | 0.622 | 0.623 | 0.043050 |
| current_MLB | 4541 | 140.980 | 140.951 | 140.916 | 107.900 | 107.697 | 107.665 | 1.113636 |
| first_year_top_picks | 68 | 113.741 | 104.125 | 104.062 | 35.748 | 37.421 | 37.417 | 0.666051 |

Losses weight target years equally; raw totals are not rescaled. Offense includes custom batting and replacement, not full WAR or control/trade value. Profile counts are support warnings, not forecast intervals.

## Austin Meadows / 2018 to 2019

ID 640457; row 33319; fold 4; age 23.0; Current MLB; list available 2019-01-27. Selected: fixed before fit.

Observed MLB AB lower bound 178; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.56}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2018, 'at_bats': 178, 'plate_appearances': 191}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.56, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.91, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.56}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | AA | 190 | 6 | 32 | 15 |
| 2016 | AAA | 145 | 6 | 34 | 15 |
| 2016 | Aminus | 17 | 0 | 1 | 2 |
| 2017 | AAA | 312 | 4 | 50 | 22 |
| 2017 | Aminus | 24 | 0 | 3 | 3 |
| 2017 | RK124 | 14 | 1 | 2 | 1 |
| 2018 | AAA | 285 | 12 | 37 | 17 |
| 2018 | MLB | 191 | 6 | 40 | 8 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.964692 | 339.187 | 327.211 | -0.13793 | 0.93260 |
| preseason | 0.952220 | 260.504 | 248.057 | -0.13793 | 0.70700 |
| graduation | 0.947961 | 260.504 | 246.948 | -0.13793 | 0.70384 |
| Actual | 1 | not a forecast | 591 | 3.591219010796714 | 5.35765 |

PA product 0.947961431 × 260.503817302; offense yield -0.137929448/600 + 0.003080035.

Actual MLB counts: [{'season': 2019, 'player_id': 640457, 'bucket': 'MLB', 'plate_appearances': 591, 'strike_outs': 131, 'unintentional_walks': 48, 'hit_by_pitch': 7, 'home_runs': 33, 'babip_hits': 121, 'doubles': 29, 'triples': 7, 'babip_opportunities': 366}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 471, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 73, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 407, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 70, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 471, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 73, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 407, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33319, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 70, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}].

Saved preseason participation: reference -4.219757; raw additive 2.992196; linked probability 0.952220.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.640197.
- games_mlb_0: input 59.000000, contribution +1.583599.
- quality_0: input 0.112340, contribution +0.378423.
- games_pool_MLB: input 59.000000, contribution +0.344296.
- draft_rank: input 0.710926, contribution +0.317087.
- games_minor_1: input 81.000000, contribution +0.173558.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.006783116098547637}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': 0.0028092138290352793}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0010012869571796017}]

Saved graduation participation: reference -4.212746; raw additive 2.902329; linked probability 0.947961.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.638832.
- games_mlb_0: input 59.000000, contribution +1.559000.
- quality_0: input 0.112340, contribution +0.394031.
- games_pool_MLB: input 59.000000, contribution +0.354073.
- draft_rank: input 0.710926, contribution +0.270101.
- games_minor_1: input 81.000000, contribution +0.203663.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.007296948093924344}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': 0.002774457396931886}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0008689902762681842}]

Same fitted candidate with the three graduation inputs zero: 0.947961. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 283.086863; raw additive 260.503817; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 191.000000, contribution -41.525064.
- quality_0: input 0.112340, contribution +39.522401.
- scout_listed_1: input 1.000000, contribution +19.378453.
- role_pool_MLB: input 3.347826, contribution -17.909420.
- role_mlb_0: input 3.347826, contribution -13.353301.
- regular_window_scaled: input 0.000000, contribution -11.493831.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': 19.378453127904542}, {'feature': 'scout_rank_score_2', 'input': 0.91, 'path_effect': -1.936149382254327}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -1.1256191296386096}, {'feature': 'scout_rank_score_1', 'input': 0.56, 'path_effect': 0.9725415861977098}]

Saved graduation conditional_pa: reference 283.086863; raw additive 260.503817; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 191.000000, contribution -41.525064.
- quality_0: input 0.112340, contribution +39.522401.
- scout_listed_1: input 1.000000, contribution +19.378453.
- role_pool_MLB: input 3.347826, contribution -17.909420.
- role_mlb_0: input 3.347826, contribution -13.353301.
- regular_window_scaled: input 0.000000, contribution -11.493831.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': 19.378453127904542}, {'feature': 'scout_rank_score_2', 'input': 0.91, 'path_effect': -1.936149382254327}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -1.1256191296386096}, {'feature': 'scout_rank_score_1', 'input': 0.56, 'path_effect': 0.9725415861977098}]

Same fitted candidate with the three graduation inputs zero: 260.503817. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Meadows is the intended beneficiary, not a success. The source has 178 MLB AB and 191 PA with six HR, plus 285 AAA PA with 12 HR; the latest-list absence is correctly recognized as AB graduation and his preceding score .56 is preserved. Nevertheless active workload is exactly unchanged at 260.504 PA; appearance falls .9522 to .9480, giving 246.95 rather than 248.06 PA versus 591 actual. Neither saved head uses a graduation feature on his path, and zeroing the added inputs gives the identical forecast. Seventy earlier active graduates support the broad profile: this is not simply an absent training population. Prior rank history still contributes, but the shallow trees did not learn the desired context distinction. The original 327 PA is less wrong. His fixed hitting -.138/600 also misses actual +3.591, so a playing-time-only fix cannot repair his value. Frazier 177.5 versus 246, Smith 177.5 versus 197, McMahon 214.3 versus 539 and Arroyo 143.4 versus 57 show both successful and unsuccessful graduate outcomes. The tested representation fails this specific repair; do not insert a Meadows override or call a pooled gain resolution.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clint Frazier | 196.99 | 182.76 | 177.53 | 246 | 0.492 | 1.314 |
| Dominic Smith | 170.50 | 177.46 | 177.46 | 197 | 0.469 | 1.658 |
| Ryan McMahon | 229.02 | 215.34 | 214.34 | 539 | 0.694 | 2.700 |
| Christian Arroyo | 165.68 | 143.43 | 143.43 | 57 | 0.266 | 0.102 |

## Dustin Fowler / 2018 to 2019

ID 641583; row 33377; fold 0; age 23.0; Current MLB; list available 2019-01-27. Selected: fixed before fit.

Observed MLB AB lower bound 192; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2017, 'at_bats': 0, 'plate_appearances': 0}, {'season': 2018, 'at_bats': 192, 'plate_appearances': 203}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | AA | 574 | 12 | 86 | 22 |
| 2017 | AAA | 313 | 13 | 63 | 14 |
| 2017 | MLB | 0 | 0 | 0 | 0 |
| 2018 | AAA | 239 | 4 | 41 | 9 |
| 2018 | MLB | 203 | 6 | 47 | 8 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.906098 | 241.461 | 218.787 | -0.73826 | 0.40467 |
| preseason | 0.904973 | 237.099 | 214.568 | -0.73826 | 0.39687 |
| graduation | 0.905327 | 234.989 | 212.742 | -0.73826 | 0.39349 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

PA product 0.905327130 × 234.989353707; offense yield -0.738259936/600 + 0.003080035.

Actual MLB counts: []. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 479, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 272, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 410, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 256, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 479, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 272, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 410, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 33377, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 256, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}].

Saved preseason participation: reference -4.174565; raw additive 2.253748; linked probability 0.904973.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.356331.
- games_mlb_0: input 69.000000, contribution +1.655908.
- games_pool_MLB: input 69.800000, contribution +0.363074.
- MLB_0_pa: input 203.000000, contribution +0.291536.
- pooled_AAA_3B: input 0.021887, contribution +0.224632.
- role_minor_0: input 4.292308, contribution +0.205488.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.005653720487919737}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.004170146212228084}]

Saved graduation participation: reference -4.169110; raw additive 2.257869; linked probability 0.905327.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.356331.
- games_mlb_0: input 69.000000, contribution +1.647336.
- games_pool_MLB: input 69.800000, contribution +0.361837.
- MLB_0_pa: input 203.000000, contribution +0.291536.
- pooled_AAA_3B: input 0.021887, contribution +0.227895.
- pooled_MLB_pa: input 203.000000, contribution +0.199836.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.00595861571055743}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.004170146212228084}]

Same fitted candidate with the three graduation inputs zero: 0.905327. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 282.062988; raw additive 237.098925; raw PA before bounds.
Largest path terms (accounting, not causality):
- role_pool_AAA: input 4.375207, contribution +22.655913.
- quality_0: input -0.350446, contribution -21.010487.
- role_mlb_0: input 3.075949, contribution -19.581415.
- work_0: input 202.916495, contribution -18.672264.
- role_pool_MLB: input 3.045113, contribution -12.786221.
- regular_window_scaled: input 0.000000, contribution -12.596011.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.2330046784497877}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.3975066078100784}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.17683839433585044}]

Saved graduation conditional_pa: reference 282.049613; raw additive 234.989354; raw PA before bounds.
Largest path terms (accounting, not causality):
- role_pool_AAA: input 4.375207, contribution +23.439634.
- quality_0: input -0.350446, contribution -21.652119.
- role_mlb_0: input 3.075949, contribution -19.382198.
- work_0: input 202.916495, contribution -18.672264.
- regular_window_scaled: input 0.000000, contribution -12.596011.
- on_40man: input 1.000000, contribution +12.129349.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.183832024909635}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.45499697511879844}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.16935049974412214}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -0.13413287504629218}]

Same fitted candidate with the three graduation inputs zero: 234.989354. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Fowler has 192 MLB AB, 203 current MLB PA/six HR/47 K and 239 AAA PA/four HR. He is an AB graduate, but neither preceding preseason list ranks him; graduation does not manufacture reputation. Expected PA falls only 214.57 to 212.74 versus zero next-year MLB PA, through a small conditional-workload refit, not a useful graduate boost or a forecast of his eventual failure. Zeroing graduation inputs leaves his own outputs unchanged; the .905 appearance chance is driven by his roster and MLB games. There are 256 earlier active people in the broad matching profile. This is a supported but unsuccessful opportunity expectation, not evidence all graduates should get regular workloads. His origin-selected peers Laureano 308 versus 481, Santander 167 versus 405, Bauers 334 versus 423 and Fletcher 323 versus 653 explain why predicting some opportunity was plausible; they are not evidence that his exact non-arrival was foreseeable. Keep the failure in scoring.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ramón Laureano | 318.32 | 301.28 | 307.55 | 481 | 1.252 | 3.527 |
| Anthony Santander | 170.18 | 158.71 | 166.68 | 405 | 0.388 | 1.759 |
| Jake Bauers | 343.90 | 334.43 | 334.43 | 423 | 1.211 | 0.948 |
| David Fletcher | 314.27 | 335.80 | 322.93 | 653 | 0.475 | 2.547 |

## Aaron Judge / 2016 to 2017

ID 592450; row 23934; fold 3; age 24.0; Current MLB; list available 2017-01-28. Selected: fixed before fit, major false low.

Observed MLB AB lower bound 84; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2016, 'at_bats': 84, 'plate_appearances': 95}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.56, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.7, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.33, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.925862 | 304.039 | 281.499 | -0.03966 | 0.84997 |
| preseason | 0.924997 | 335.052 | 309.922 | -0.03966 | 0.93580 |
| graduation | 0.923059 | 335.052 | 309.273 | -0.03966 | 0.93384 |
| Actual | 1 | not a forecast | 678 | 5.557415626157027 | 8.37188 |

PA product 0.923059401 × 335.052386027; offense yield -0.039659855/600 + 0.003085550.

Actual MLB counts: [{'season': 2017, 'player_id': 592450, 'bucket': 'MLB', 'plate_appearances': 678, 'strike_outs': 208, 'unintentional_walks': 116, 'hit_by_pitch': 5, 'home_runs': 52, 'babip_hits': 102, 'doubles': 24, 'triples': 3, 'babip_opportunities': 286}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 2, 'profile_people': 5, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 14, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 2, 'profile_people': 4, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 11, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 2, 'profile_people': 5, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 14, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 2, 'profile_people': 4, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 11, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}].

Saved preseason participation: reference -4.078610; raw additive 2.512262; linked probability 0.924997.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.132957.
- games_mlb_0: input 27.000000, contribution +1.060688.
- scout_rank_score_0: input 0.560000, contribution +0.657869.
- games_pool_MLB: input 27.000000, contribution +0.564445.
- MLB_0_pa: input 95.000000, contribution +0.347969.
- pooled_MLB_pa: input 95.000000, contribution -0.277269.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.56, 'path_effect': 0.6578686851930002}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.17389293598599082}]

Saved graduation participation: reference -4.075246; raw additive 2.484660; linked probability 0.923059.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.132957.
- games_mlb_0: input 27.000000, contribution +1.061754.
- scout_rank_score_0: input 0.560000, contribution +0.657867.
- games_pool_MLB: input 27.000000, contribution +0.564445.
- MLB_0_pa: input 95.000000, contribution +0.336560.
- pooled_MLB_pa: input 95.000000, contribution -0.277269.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.56, 'path_effect': 0.6578674980343128}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.17389293598599082}]

Same fitted candidate with the three graduation inputs zero: 0.923059. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 276.994851; raw additive 335.052386; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.560000, contribution +97.387567.
- scout_rank_score_1: input 0.700000, contribution +60.368168.
- MLB_0_pa: input 95.000000, contribution -53.874968.
- pooled_MLB_K: input 0.333333, contribution -28.556320.
- work_0: input 95.078254, contribution -20.955822.
- role_pool_AAA: input 4.334651, contribution +14.167469.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.56, 'path_effect': 97.38756740192885}, {'feature': 'scout_rank_score_1', 'input': 0.7, 'path_effect': 60.368167761937244}]

Saved graduation conditional_pa: reference 276.994851; raw additive 335.052386; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.560000, contribution +97.387567.
- scout_rank_score_1: input 0.700000, contribution +60.368168.
- MLB_0_pa: input 95.000000, contribution -53.874968.
- pooled_MLB_K: input 0.333333, contribution -28.556320.
- work_0: input 95.078254, contribution -20.955822.
- role_pool_AAA: input 4.334651, contribution +14.167469.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.56, 'path_effect': 97.38756740192885}, {'feature': 'scout_rank_score_1', 'input': 0.7, 'path_effect': 60.368167761937244}]

Same fitted candidate with the three graduation inputs zero: 335.052386. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Judge has only 84 MLB AB, below the sufficient graduation threshold, and remains ranked. His 95-PA debut has four HR but 42 strikeouts; AAA provides 410 PA/19 HR/98 K. Added graduation inputs are all zero and zeroing them leaves the candidate unchanged. Expected PA is 309.27 versus the fresher-list 309.92 and actual 678; active PA remains exactly 335.052. Current and prior rankings add about 97 and 60 PA on the saved active path, yet the fixed hitting rate -.040/600 misses actual +5.557. This is predominantly an extreme-talent/readiness miss, not a graduation fix. The age/stage/past-listed non-graduate profile has only 14 participation and 11 active earlier people; do not call the broad all-player population sufficient. Jones 84 versus 154, Pinder 148 versus 309, Marrero 72 versus 188 and Renda 43 versus zero retain weaker and failed comparisons. Ordinary college/prospect heuristics cannot guarantee Judge's later exceptional season.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| JaCoby Jones | 69.81 | 82.82 | 83.58 | 154 | 0.198 | -0.616 |
| Chad Pinder | 162.21 | 147.78 | 148.00 | 309 | 0.236 | 1.012 |
| Deven Marrero | 68.60 | 66.36 | 71.91 | 188 | 0.069 | -0.374 |
| Tony Renda | 39.98 | 44.10 | 43.39 | 0 | 0.069 | 0.000 |

## Wyatt Langford / 2023 to 2024

ID 694671; row 53164; fold 4; age 21.0; Upper minors; list available 2024-01-26. Selected: fixed before fit.

Observed MLB AB lower bound 0; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: []

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.95, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.201829 | 213.556 | 43.102 | 0.68803 | 0.18287 |
| preseason | 0.599098 | 358.735 | 214.918 | 0.68803 | 0.91185 |
| graduation | 0.599098 | 363.411 | 217.719 | 0.68803 | 0.92374 |
| Actual | 1 | not a forecast | 557 | 0.07695317803827988 | 1.79595 |

PA product 0.599098272 × 363.410826170; offense yield 0.688029041/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 694671, 'bucket': 'MLB', 'plate_appearances': 557, 'strike_outs': 115, 'unintentional_walks': 48, 'hit_by_pitch': 4, 'home_runs': 16, 'babip_hits': 110, 'doubles': 25, 'triples': 4, 'babip_opportunities': 371}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 1, 'profile_people': 35, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 865, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 1, 'profile_people': 33, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 186, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 1, 'profile_people': 35, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 865, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 1, 'profile_people': 33, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 186, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}].

Saved preseason participation: reference -4.136149; raw additive 0.401709; linked probability 0.599098.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.950000, contribution +1.300233.
- scout_listed_0: input 1.000000, contribution +1.173110.
- role_pool_AA: input 4.272727, contribution +0.920409.
- draft_rank: input 0.817615, contribution +0.443997.
- on_40man: input 0.000000, contribution -0.406939.
- pooled_AA_pa: input 54.000000, contribution +0.397450.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.95, 'path_effect': 1.300232583630407}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 1.1731100622601913}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.04601635338912652}, {'feature': 'scout_list_capacity_2', 'input': 100.0, 'path_effect': 0.005640793222627442}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0014002335249221163}]

Saved graduation participation: reference -4.136149; raw additive 0.401709; linked probability 0.599098.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.950000, contribution +1.300233.
- scout_listed_0: input 1.000000, contribution +1.173110.
- role_pool_AA: input 4.272727, contribution +0.920409.
- draft_rank: input 0.817615, contribution +0.443997.
- on_40man: input 0.000000, contribution -0.406939.
- pooled_AA_pa: input 54.000000, contribution +0.397450.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.95, 'path_effect': 1.300232583630407}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 1.1731100622601913}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.04601635338912652}, {'feature': 'scout_list_capacity_2', 'input': 100.0, 'path_effect': 0.005640793222627442}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0014002335249221163}]

Same fitted candidate with the three graduation inputs zero: 0.599098. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 279.203529; raw additive 358.735377; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.950000, contribution +147.249762.
- work_0: input 0.000000, contribution -94.004712.
- role_pool_AAA: input 4.400000, contribution +34.806643.
- on_40man: input 0.000000, contribution -19.537854.
- role_pool_AA: input 4.272727, contribution +15.145308.
- regular_window_scaled: input 0.000000, contribution -10.037675.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.95, 'path_effect': 147.24976164209835}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.9484166182728666}]

Saved graduation conditional_pa: reference 279.210702; raw additive 363.410826; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.950000, contribution +149.689140.
- work_0: input 0.000000, contribution -94.519707.
- role_pool_AAA: input 4.400000, contribution +35.278883.
- on_40man: input 0.000000, contribution -20.375878.
- role_pool_AA: input 4.272727, contribution +13.651396.
- regular_window_scaled: input 0.000000, contribution -10.037675.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.95, 'path_effect': 149.68913969903332}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.896499648335497}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -0.22327279533326214}]

Same fitted candidate with the three graduation inputs zero: 363.410826. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Langford's 200 professional PA span four levels and include ten HR; he has no MLB AB and all three added graduation inputs are zero. His appearance forecast remains exactly .59910 and conditional PA moves 358.74 to 363.41 through the changed shared training mapping, so expected PA rises only 214.92 to 217.72 versus 557. Zeroing the added inputs changes nothing for him. The much larger gain from the original 43 PA still belongs to fresher ranking information, not graduation. His fixed +.688/600 rate is optimistic versus actual +.077, partly cushioning the workload miss. Broad graduation-profile support 865/186 does not resolve V68's zero precisely matched recent-draft/top-rank profile; no finer new-entry support is claimed. Peers Veen and Shaw receive low opportunity and do not arrive, Crews plays 132 PA, Wilken stays in the minors. Preserve these distinctions and the remaining elite-entry weakness rather than presenting a small refit movement as solving readiness.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Zac Veen | 85.17 | 15.77 | 15.50 | 0 | 0.044 | 0.000 |
| Dylan Crews | 12.55 | 49.67 | 50.67 | 132 | 0.162 | 0.025 |
| Matt Shaw | 34.13 | 101.43 | 98.44 | 0 | 0.268 | 0.000 |
| Brock Wilken | 6.42 | 3.92 | 4.22 | 0 | 0.015 | 0.000 |

## Nick Kurtz / 2024 to 2025

ID 701762; row 57052; fold 2; age 21.0; Upper minors; list available 2025-01-24. Selected: fixed before fit.

Observed MLB AB lower bound 0; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: []

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.63, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.017252 | 115.973 | 2.001 | -0.06322 | 0.00604 |
| preseason | 0.060561 | 168.160 | 10.184 | -0.06322 | 0.03073 |
| graduation | 0.056100 | 170.252 | 9.551 | -0.06322 | 0.02882 |
| Actual | 1 | not a forecast | 489 | 5.289191738139299 | 5.83778 |

PA product 0.056099799 × 170.251878382; offense yield -0.063222554/600 + 0.003122875.

Actual MLB counts: [{'season': 2025, 'player_id': 701762, 'bucket': 'MLB', 'plate_appearances': 489, 'strike_outs': 151, 'unintentional_walks': 60, 'hit_by_pitch': 2, 'home_runs': 36, 'babip_hits': 86, 'doubles': 26, 'triples': 2, 'babip_opportunities': 236}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 2, 'profile_people': 54, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 944, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 2, 'profile_people': 31, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 176, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 2, 'profile_people': 54, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 944, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': 2, 'profile_people': 31, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'rank_band': None, 'profile_people': 176, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}].

Saved preseason participation: reference -4.096228; raw additive -2.741629; linked probability 0.060561.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.630000, contribution +1.243941.
- draft_rank: input 0.817615, contribution +0.450012.
- scout_listed_0: input 1.000000, contribution +0.396579.
- on_40man: input 0.000000, contribution -0.334185.
- games_mlb_0: input 0.000000, contribution -0.202625.
- games_pool_MLB: input 0.000000, contribution -0.198036.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.63, 'path_effect': 1.2439405368819731}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.3965785432052498}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.032307341632344076}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': -0.01579900902225148}]

Saved graduation participation: reference -4.082398; raw additive -2.822888; linked probability 0.056100.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.630000, contribution +1.202697.
- draft_rank: input 0.817615, contribution +0.419940.
- scout_listed_0: input 1.000000, contribution +0.414355.
- on_40man: input 0.000000, contribution -0.334185.
- games_mlb_0: input 0.000000, contribution -0.201755.
- games_pool_MLB: input 0.000000, contribution -0.195047.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.63, 'path_effect': 1.2026967929481924}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.4143548504325281}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.03947497557591787}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': -0.018461798421269368}]

Same fitted candidate with the three graduation inputs zero: 0.056100. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 278.554971; raw additive 168.160355; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 0.000000, contribution -99.719816.
- scout_rank_score_0: input 0.630000, contribution +71.234719.
- on_40man: input 0.000000, contribution -22.649740.
- quality_0: input 0.000000, contribution -12.276285.
- regular_window_scaled: input 0.000000, contribution -11.785065.
- role_pool_AAA: input 4.000000, contribution -9.248723.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.63, 'path_effect': 71.23471863609}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.953893359363807}, {'feature': 'scout_list_capacity_2', 'input': 100.0, 'path_effect': 1.3550542765479698}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': -0.288105795627787}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.058577565231899144}]

Saved graduation conditional_pa: reference 278.569273; raw additive 170.251878; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 0.000000, contribution -99.439241.
- scout_rank_score_0: input 0.630000, contribution +71.433340.
- on_40man: input 0.000000, contribution -23.533753.
- quality_0: input 0.000000, contribution -12.451748.
- regular_window_scaled: input 0.000000, contribution -11.033506.
- pooled_A_HBP: input 0.007407, contribution +9.796326.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.63, 'path_effect': 71.43334044276621}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.6287520008358687}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -1.0801866926497596}, {'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.05985613158693854}]

Same fitted candidate with the three graduation inputs zero: 170.251878. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Kurtz has only 50 professional PA, four HR and ten strikeouts, no MLB AB and zero graduation inputs. The fresher rank 38 is present, as are pick four and college background. Appearance falls .06056 to .05610, conditional PA rises 168.16 to 170.25, and the product falls 10.18 to 9.55 versus 489 actual. Zeroing the new features gives the same outputs: this is a shared refit effect, not a personal graduation penalty. The fixed hitting -.063/600 also misses actual +5.289. Broad support 944 participation/176 active is not evidence of a matched elite recent-draftee sample; V68 had no matching active refined profile. Montgomery and Williams do not arrive, but Moore gets 184 PA and Cam Smith 493 versus forecasts 22 and nine. The paired successful and failed new-draftee examples retain the unresolved rapid-entry issue. Do not manufacture a Kurtz star forecast or infer that all tiny pro samples deserve an MLB season.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benny Montgomery | 6.54 | 5.41 | 5.80 | 0 | 0.016 | 0.000 |
| Christian Moore | 8.23 | 22.35 | 21.84 | 184 | 0.067 | 0.242 |
| Cam Smith | 2.33 | 9.98 | 9.28 | 493 | 0.025 | 1.131 |
| Jett Williams | 74.66 | 100.55 | 101.55 | 0 | 0.298 | 0.000 |

## Mickey Moniak / 2016 to 2017

ID 666160; row 26836; fold 3; age 18.0; Lower minors; list available 2017-01-28. Selected: fixed before fit.

Observed MLB AB lower bound 0; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: []

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.82, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | RK124 | 194 | 1 | 35 | 11 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.006797 | 71.368 | 0.485 | 0.37128 | 0.00180 |
| preseason | 0.040447 | 157.123 | 6.355 | 0.37128 | 0.02354 |
| graduation | 0.041070 | 157.123 | 6.453 | 0.37128 | 0.02390 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

PA product 0.041069601 × 157.123101478; offense yield 0.371275556/600 + 0.003085550.

Actual MLB counts: []. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 1, 'profile_people': 5, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 1713, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 1, 'profile_people': 1, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 1, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 1, 'profile_people': 5, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 1713, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 1, 'profile_people': 1, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 26836, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 1, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': False}].

Saved preseason participation: reference -4.078610; raw additive -3.166475; linked probability 0.040447.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.820000, contribution +1.604370.
- draft_rank: input 1.000000, contribution +0.668943.
- on_40man: input 0.000000, contribution -0.423726.
- games_mlb_0: input 0.000000, contribution -0.244916.
- pooled_RK124_BABIP: input 0.326446, contribution +0.157242.
- games_pool_MLB: input 0.000000, contribution -0.153998.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.82, 'path_effect': 1.6043701719312478}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.13802804654747408}]

Saved graduation participation: reference -4.075246; raw additive -3.150550; linked probability 0.041070.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.820000, contribution +1.604768.
- draft_rank: input 1.000000, contribution +0.668805.
- on_40man: input 0.000000, contribution -0.423726.
- games_mlb_0: input 0.000000, contribution -0.243850.
- pooled_RK124_BABIP: input 0.326446, contribution +0.154876.
- games_pool_MLB: input 0.000000, contribution -0.153998.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.82, 'path_effect': 1.6047677601694574}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.13802804654747408}]

Same fitted candidate with the three graduation inputs zero: 0.041070. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 276.994851; raw additive 157.123101; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.820000, contribution +109.994225.
- MLB_0_pa: input 0.000000, contribution -92.600904.
- work_0: input 0.000000, contribution -25.816599.
- on_40man: input 0.000000, contribution -21.422299.
- role_pool_AAA: input 4.000000, contribution -10.092162.
- quality_0: input 0.000000, contribution -10.023872.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.82, 'path_effect': 109.99422524342644}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.692055691265587}]

Saved graduation conditional_pa: reference 276.994851; raw additive 157.123101; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.820000, contribution +109.994225.
- MLB_0_pa: input 0.000000, contribution -92.600904.
- work_0: input 0.000000, contribution -25.816599.
- on_40man: input 0.000000, contribution -21.422299.
- role_pool_AAA: input 4.000000, contribution -10.092162.
- quality_0: input 0.000000, contribution -10.023872.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.82, 'path_effect': 109.99422524342644}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.692055691265587}]

Same fitted candidate with the three graduation inputs zero: 157.123101. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Moniak's 194 rookie-league PA contain one HR and 35 strikeouts at age 18. He has no MLB AB, remains ranked and receives no graduation history. Appearance changes .04045 to .04107, active workload stays exactly 157.123, and expected PA is only 6.45 versus zero. The saved path rewards current ranking and draft standing, but the added inputs have no own effect in the fixed-model probe. There is only one earlier active person in the broad age/stage graduation profile, despite 1,713 participation people: this conditional forecast borrows older/higher-level paths. Lowe, Benson, Stephenson and Kirilloff all remain non-arrivals with very small forecasts. This is a small immediate-opportunity false positive, not a claim about Moniak's career or proof pedigree is unhelpful. The test does not turn prestigious high-school teenagers into immediate regulars, but conditional workload remains weakly supported.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Josh Lowe | 0.56 | 0.19 | 0.19 | 0 | 0.001 | 0.000 |
| Will Benson | 0.30 | 0.15 | 0.15 | 0 | 0.001 | 0.000 |
| Tyler Stephenson | 0.56 | 0.33 | 0.32 | 0 | 0.001 | 0.000 |
| Alex Kirilloff | 1.03 | 0.37 | 0.37 | 0 | 0.002 | 0.000 |

## Ethan Salas / 2024 to 2025

ID 806956; row 57694; fold 3; age 18.0; Lower minors; list available 2025-01-24. Selected: fixed before fit.

Observed MLB AB lower bound 0; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: []

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.68, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.93, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.025632 | 281.842 | 7.224 | -0.51171 | 0.01640 |
| preseason | 0.022453 | 262.436 | 5.892 | -0.51171 | 0.01338 |
| graduation | 0.022975 | 264.012 | 6.066 | -0.51171 | 0.01377 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

PA product 0.022974988 × 264.011595017; offense yield -0.511710571/600 + 0.003122875.

Actual MLB counts: []. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 2, 'profile_people': 21, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 12, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 2, 'profile_people': 1, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 0, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 2, 'profile_people': 21, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 12, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': 2, 'profile_people': 1, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 0, 'rank_band': None, 'profile_people': 0, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}].

Saved preseason participation: reference -4.111470; raw additive -3.773620; linked probability 0.022453.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.680000, contribution +1.238428.
- games_minor_0: input 111.000000, contribution +0.391314.
- on_40man: input 0.000000, contribution -0.386286.
- age_centered: input -1.800000, contribution -0.280447.
- position_2: input 1.000000, contribution +0.273544.
- games_mlb_0: input 0.000000, contribution -0.270559.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.68, 'path_effect': 1.2384278849550512}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.2543320325855999}, {'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': -0.024843840753048053}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': -0.0028607604089753757}, {'feature': 'scout_list_capacity_0', 'input': 100.0, 'path_effect': -0.0013022880988920152}]

Saved graduation participation: reference -4.119753; raw additive -3.750106; linked probability 0.022975.
Largest path terms (accounting, not causality):
- scout_rank_score_0: input 0.680000, contribution +1.257473.
- on_40man: input 0.000000, contribution -0.386286.
- games_minor_0: input 111.000000, contribution +0.370669.
- position_2: input 1.000000, contribution +0.272671.
- age_centered: input -1.800000, contribution -0.271441.
- games_mlb_0: input 0.000000, contribution -0.270652.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.68, 'path_effect': 1.2574731559215058}, {'feature': 'scout_listed_0', 'input': 1.0, 'path_effect': 0.2543320325855999}, {'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': -0.022491444615242363}, {'feature': 'scout_list_capacity_1', 'input': 100.0, 'path_effect': -0.0028607604089753757}, {'feature': 'scout_list_capacity_0', 'input': 100.0, 'path_effect': -0.0013022880988920152}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -0.0004954660403804828}]

Same fitted candidate with the three graduation inputs zero: 0.022975. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 277.919440; raw additive 262.436300; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_1: input 0.930000, contribution +109.015667.
- work_0: input 0.000000, contribution -91.839471.
- scout_rank_score_0: input 0.680000, contribution +86.766936.
- on_40man: input 0.000000, contribution -24.396727.
- regular_window_scaled: input 0.000000, contribution -13.069478.
- quality_0: input 0.000000, contribution -9.572406.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.93, 'path_effect': 109.01566697357107}, {'feature': 'scout_rank_score_0', 'input': 0.68, 'path_effect': 86.76693590894232}]

Saved graduation conditional_pa: reference 277.947502; raw additive 264.011595; raw PA before bounds.
Largest path terms (accounting, not causality):
- scout_rank_score_1: input 0.930000, contribution +107.493524.
- work_0: input 0.000000, contribution -91.839471.
- scout_rank_score_0: input 0.680000, contribution +87.754331.
- on_40man: input 0.000000, contribution -24.396727.
- regular_window_scaled: input 0.000000, contribution -13.069478.
- quality_0: input 0.000000, contribution -9.497617.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.93, 'path_effect': 107.49352406038551}, {'feature': 'scout_rank_score_0', 'input': 0.68, 'path_effect': 87.7543314846095}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -0.07187438930098143}]

Same fitted candidate with the three graduation inputs zero: 264.011595. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Salas is 18 with 469 A-plus PA, four HR, 98 strikeouts and 47 unintentional walks. He has no MLB AB; the fresh rank 33 and preceding rank eight remain inputs. Expected PA moves 5.89 to 6.07 versus zero, as appearance .02245 to .02297 and active PA 262.44 to 264.01 change slightly. All own graduation features are zero, and the zero-feature probe is identical; the movement is a shared refit, not graduation evidence. Earlier active support for this graduation profile is zero, participation support 12. The large 264 conditional PA is borrowed, not a calibrated credible rookie season; the low appearance chance keeps expected PA small. Rodriguez, Flores, Di Turi and Zavala all remain in the minors. The lack of next-year MLB PA says nothing conclusive about long-run catching talent or trade value. Keep that horizon distinction and the conditional support warning.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Yophery Rodriguez | 0.38 | 0.22 | 0.19 | 0 | 0.001 | 0.000 |
| Juan Flores | 0.69 | 0.54 | 0.53 | 0 | 0.001 | 0.000 |
| Filippo Di Turi | 0.35 | 0.17 | 0.16 | 0 | 0.000 | 0.000 |
| Samuel Zavala | 0.46 | 0.35 | 0.33 | 0 | 0.001 | 0.000 |

## Ben Rortvedt / 2023 to 2024

ID 666163; row 51344; fold 1; age 25.0; Current MLB; list available 2024-01-26. Selected: fixed before fit.

Observed MLB AB lower bound 157; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2021, 'at_bats': 89, 'plate_appearances': 98}, {'season': 2023, 'at_bats': 68, 'plate_appearances': 79}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 136 | 5 | 35 | 10 |
| 2021 | MLB | 98 | 3 | 29 | 6 |
| 2022 | A | 5 | 1 | 1 | 1 |
| 2022 | AAA | 177 | 6 | 57 | 18 |
| 2022 | Aplus | 15 | 0 | 6 | 3 |
| 2023 | A | 11 | 0 | 1 | 1 |
| 2023 | AA | 4 | 0 | 0 | 0 |
| 2023 | AAA | 124 | 6 | 31 | 16 |
| 2023 | MLB | 79 | 2 | 19 | 11 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.870947 | 98.883 | 86.122 | -1.10170 | 0.10851 |
| preseason | 0.873256 | 94.221 | 82.279 | -1.10170 | 0.10366 |
| graduation | 0.866551 | 95.571 | 82.817 | -1.10170 | 0.10434 |
| Actual | 1 | not a forecast | 328 | -1.6693067607876315 | 0.10296 |

PA product 0.866550668 × 95.571036736; offense yield -1.101698619/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 666163, 'bucket': 'MLB', 'plate_appearances': 328, 'strike_outs': 88, 'unintentional_walks': 34, 'hit_by_pitch': 4, 'home_runs': 3, 'babip_hits': 63, 'doubles': 13, 'triples': 0, 'babip_opportunities': 199}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 740, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 442, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 638, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 414, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 740, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 442, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': 0, 'profile_people': 638, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'rank_band': None, 'profile_people': 414, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}].

Saved preseason participation: reference -4.033199; raw additive 1.930057; linked probability 0.873256.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +2.702640.
- games_mlb_0: input 32.000000, contribution +1.231958.
- games_pool_MLB: input 55.400000, contribution +0.606268.
- pooled_MLB_pa: input 137.800000, contribution +0.341837.
- position_2: input 1.000000, contribution +0.328208.
- draft_rank: input 0.470411, contribution +0.216131.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.05946729752929474}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.004861902639319466}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.004052634853726131}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0012135512535880963}]

Saved graduation participation: reference -4.022695; raw additive 1.870799; linked probability 0.866551.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +2.702640.
- games_mlb_0: input 32.000000, contribution +1.232035.
- games_pool_MLB: input 55.400000, contribution +0.606268.
- pooled_MLB_pa: input 137.800000, contribution +0.341837.
- position_2: input 1.000000, contribution +0.330354.
- draft_rank: input 0.470411, contribution +0.206201.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.05766743662786962}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.0048615117132406035}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.004052634853726131}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0012135512535880963}]

Same fitted candidate with the three graduation inputs zero: 0.866551. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 283.910666; raw additive 94.220873; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 79.000000, contribution -94.475876.
- quality_0: input -0.300548, contribution -19.983296.
- role_pool_AAA: input 4.163441, contribution +14.896681.
- pooled_MLB_2B: input 0.027754, contribution -12.267785.
- on_40man: input 1.000000, contribution +12.075051.
- pooled_MLB_K: input 0.249790, contribution -10.620559.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -5.693441978923961}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.3306301324386736}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.011611541282393698}]

Saved graduation conditional_pa: reference 283.918644; raw additive 95.571037; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 79.000000, contribution -94.475876.
- quality_0: input -0.300548, contribution -19.509746.
- role_pool_AAA: input 4.163441, contribution +13.937598.
- pooled_MLB_2B: input 0.027754, contribution -13.457880.
- on_40man: input 1.000000, contribution +12.256143.
- pooled_MLB_K: input 0.249790, contribution -10.932013.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -5.768701727337382}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -2.2418122298072953}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': 0.5655300569041659}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.06848923125524924}]

Same fitted candidate with the three graduation inputs zero: 95.571037. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Rortvedt has 157 observed career MLB AB but only 79 current MLB PA/two HR after a minor-only 2022. The AB-graduate/unlisted flags are one, while prior ranking score is zero. Appearance falls .8733 to .8666 and conditional PA increases 94.22 to 95.57, producing 82.82 versus 328 actual. Zeroing the added inputs leaves his forecast identical; most movement is a changed shared mapping. There are 414 matching broad active graduates, so this is not explained by an empty general training profile. Fixed hitting -1.102/600 is less poor than actual -1.669; predicted offense .104 versus actual .103 is another cancellation between too little workload and optimistic hitting, not sound accuracy. Miranda 234 versus 429 and McCarthy 274 versus 495 remain underpredicted; Kieboom 158 versus zero and Jones 484 versus 297 are false highs. Graduation alone does not explain these separate roster/workload opportunities.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jose F Miranda | 224.29 | 232.89 | 233.84 | 429 | 0.556 | 1.653 |
| Nolan Jones | 487.77 | 481.86 | 483.77 | 297 | 2.529 | 0.112 |
| Carter Kieboom | 167.56 | 162.46 | 157.89 | 0 | 0.333 | 0.000 |
| Jake McCarthy | 265.87 | 267.27 | 274.38 | 495 | 0.967 | 1.866 |

## Juan Soto / 2018 to 2019

ID 665742; row 34521; fold 0; age 19.0; Current MLB; list available 2019-01-27. Selected: largest offense gain.

Observed MLB AB lower bound 414; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.72}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2018, 'at_bats': 414, 'plate_appearances': 494}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.72, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.72}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 24 | 0 | 4 | 3 |
| 2016 | RK124 | 183 | 5 | 25 | 14 |
| 2017 | A | 96 | 3 | 8 | 8 |
| 2017 | RK124 | 27 | 0 | 1 | 2 |
| 2018 | A | 74 | 5 | 13 | 13 |
| 2018 | AA | 35 | 2 | 7 | 4 |
| 2018 | Aplus | 73 | 7 | 8 | 11 |
| 2018 | MLB | 494 | 22 | 99 | 69 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.990053 | 620.150 | 613.981 | 2.37266 | 4.31903 |
| preseason | 0.985935 | 604.019 | 595.524 | 2.37266 | 4.18919 |
| graduation | 0.985854 | 623.978 | 615.151 | 2.37266 | 4.32726 |
| Actual | 1 | not a forecast | 659 | 4.401652461941062 | 6.86422 |

PA product 0.985854319 × 623.977929716; offense yield 2.372659895/600 + 0.003080035.

Actual MLB counts: [{'season': 2019, 'player_id': 665742, 'bucket': 'MLB', 'plate_appearances': 659, 'strike_outs': 132, 'unintentional_walks': 105, 'hit_by_pitch': 3, 'home_runs': 34, 'babip_hits': 119, 'doubles': 32, 'triples': 5, 'babip_opportunities': 382}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 0, 'profile_people': 104, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 48, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 0, 'profile_people': 92, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 45, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 0, 'profile_people': 104, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 48, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 0, 'profile_people': 92, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 34521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 45, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': True}].

Saved preseason participation: reference -4.174565; raw additive 4.249888; linked probability 0.985935.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.482259.
- games_mlb_0: input 116.000000, contribution +1.643371.
- quality_0: input 1.040306, contribution +0.847460.
- work_0: input 493.796791, contribution +0.614758.
- pooled_MLB_HBP: input 0.001684, contribution -0.420485.
- games_pool_MLB: input 116.000000, contribution +0.371854.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.005653720487919737}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0005557895081015952}]

Saved graduation participation: reference -4.169110; raw additive 4.244099; linked probability 0.985854.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.580420.
- games_mlb_0: input 116.000000, contribution +1.634799.
- quality_0: input 1.040306, contribution +0.809783.
- work_0: input 493.796791, contribution +0.611696.
- pooled_MLB_HBP: input 0.001684, contribution -0.394810.
- games_pool_MLB: input 116.000000, contribution +0.372057.

Scouting/graduation path terms: [{'feature': 'scout_ab_graduated', 'input': 1.0, 'path_effect': 0.014007802300328876}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.00603021319026533}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0005557895081015952}]

Same fitted candidate with the three graduation inputs zero: 0.985621. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 282.062988; raw additive 604.019218; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 494.000000, contribution +81.243585.
- scout_rank_score_1: input 0.720000, contribution +46.806840.
- role_mlb_0: input 4.238095, contribution +46.667599.
- quality_0: input 1.040306, contribution +29.198393.
- role_pool_MLB: input 4.238095, contribution +28.755475.
- work_0: input 493.796791, contribution +26.062232.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.72, 'path_effect': 46.80684045514528}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 1.7938190734381645}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.35644263167055734}]

Saved graduation conditional_pa: reference 282.049613; raw additive 623.977930; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 494.000000, contribution +81.243585.
- role_mlb_0: input 4.238095, contribution +46.866817.
- scout_rank_score_1: input 0.720000, contribution +46.765660.
- quality_0: input 1.040306, contribution +33.856743.
- role_pool_MLB: input 4.238095, contribution +28.706578.
- work_0: input 493.796791, contribution +26.062232.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_1', 'input': 0.72, 'path_effect': 46.76566049266977}, {'feature': 'scout_graduated_prior_score', 'input': 0.72, 'path_effect': 4.882816324433573}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 4.629893450030561}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.38830013080657166}]

Same fitted candidate with the three graduation inputs zero: 615.809777. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Soto is the largest offense improvement over V68, but already near the original forecast. By cutoff he has 414 MLB AB and an outstanding 494-PA debut with 22 HR, 99 K and 69 unintentional walks. Latest absence is confirmed AB graduation and preceding rank score .72 is retained. Appearance barely changes .98593 to .98585; conditional PA increases 604.02 to 623.98, giving 615.15 versus 659 actual and original 613.98. The saved interacted prior-score term adds 4.883 PA; the fixed-fit zero-feature probe reduces conditional PA to 615.81, showing about eight PA of own-input mechanism, not the full twenty-PA refit difference or causality. Forty-five earlier active matching graduates support this profile. Fixed hitting +2.373/600 remains below actual +4.402, so offense 4.327 versus 6.864 still misses talent. Acuna, Torres, Devers and Albies all deliver substantial workloads, and some exceed their forecasts markedly. This demonstrates useful recovery for an already successful graduate, not identifying Soto before debut or fixing all former prospects.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ronald Acuña Jr. | 591.78 | 603.95 | 603.95 | 715 | 3.739 | 5.830 |
| Gleyber Torres | 560.84 | 534.07 | 533.71 | 604 | 2.388 | 4.474 |
| Rafael Devers | 439.90 | 437.09 | 437.09 | 702 | 1.839 | 6.172 |
| Ozzie Albies | 637.68 | 646.65 | 646.68 | 702 | 2.808 | 4.849 |

## Corbin Carroll / 2022 to 2023

ID 682998; row 48512; fold 3; age 21.0; Current MLB; list available 2023-01-26. Selected: largest offense harm.

Observed MLB AB lower bound 104; added inputs {'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2022, 'at_bats': 104, 'plate_appearances': 115}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.99, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.82, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.54, 'scout_ab_graduated': 0, 'scout_graduated_absent': 0, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | Aplus | 29 | 2 | 7 | 5 |
| 2022 | AA | 277 | 16 | 68 | 39 |
| 2022 | AAA | 157 | 7 | 36 | 24 |
| 2022 | MLB | 115 | 4 | 31 | 8 |
| 2022 | RK121 | 8 | 1 | 3 | 2 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.976495 | 460.906 | 450.072 | 0.86906 | 2.06106 |
| preseason | 0.967963 | 477.585 | 462.284 | 0.86906 | 2.11699 |
| graduation | 0.965975 | 458.601 | 442.997 | 0.86906 | 2.02866 |
| Actual | 1 | not a forecast | 645 | 3.0222716124968527 | 5.26842 |

PA product 0.965974739 × 458.601321597; offense yield 0.869059953/600 + 0.003130974.

Actual MLB counts: [{'season': 2023, 'player_id': 682998, 'bucket': 'MLB', 'plate_appearances': 645, 'strike_outs': 125, 'unintentional_walks': 56, 'hit_by_pitch': 13, 'home_runs': 25, 'babip_hits': 136, 'doubles': 30, 'triples': 10, 'babip_opportunities': 419}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 1, 'profile_people': 13, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 45, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 1, 'profile_people': 13, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 42, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 1, 'profile_people': 13, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 45, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': 1, 'profile_people': 13, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 48512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 1, 'rank_band': None, 'profile_people': 42, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 0, 'previously_listed': True}].

Saved preseason participation: reference -4.132366; raw additive 3.408316; linked probability 0.967963.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +2.983892.
- games_mlb_0: input 32.000000, contribution +1.301959.
- scout_rank_score_0: input 0.990000, contribution +0.934530.
- games_pool_MLB: input 32.000000, contribution +0.642525.
- quality_0: input 0.209475, contribution +0.573243.
- role_pool_AAA: input 4.581395, contribution +0.286926.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.99, 'path_effect': 0.9345302874357359}, {'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': -0.04548589975095569}]

Saved graduation participation: reference -4.145964; raw additive 3.346034; linked probability 0.965975.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +2.983892.
- games_mlb_0: input 32.000000, contribution +1.301979.
- scout_rank_score_0: input 0.990000, contribution +0.937005.
- games_pool_MLB: input 32.000000, contribution +0.642525.
- quality_0: input 0.209475, contribution +0.572650.
- role_minor_0: input 4.679612, contribution +0.284755.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.99, 'path_effect': 0.9370047037024097}, {'feature': 'scout_listed_1', 'input': 1.0, 'path_effect': -0.046342310147629434}, {'feature': 'scout_ab_graduated', 'input': 0.0, 'path_effect': -0.0014384604483198477}]

Same fitted candidate with the three graduation inputs zero: 0.965975. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 277.296431; raw additive 477.584637; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 115.000000, contribution -69.453969.
- scout_rank_score_0: input 0.990000, contribution +62.903284.
- quality_0: input 0.209475, contribution +52.875724.
- pooled_mlb_quality: input 0.209475, contribution +38.574455.
- scout_rank_score_1: input 0.820000, contribution +37.346669.
- role_pool_AAA: input 4.581395, contribution +27.569238.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.99, 'path_effect': 62.903283642440954}, {'feature': 'scout_rank_score_1', 'input': 0.82, 'path_effect': 37.346668592108}, {'feature': 'scout_rank_score_2', 'input': 0.54, 'path_effect': 2.4589131916474063}]

Saved graduation conditional_pa: reference 277.305136; raw additive 458.601322; raw PA before bounds.
Largest path terms (accounting, not causality):
- work_0: input 115.000000, contribution -69.453969.
- scout_rank_score_0: input 0.990000, contribution +63.231220.
- quality_0: input 0.209475, contribution +52.827905.
- pooled_mlb_quality: input 0.209475, contribution +38.694907.
- scout_rank_score_1: input 0.820000, contribution +37.311682.
- role_pool_AAA: input 4.581395, contribution +26.681016.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.99, 'path_effect': 63.231219525232156}, {'feature': 'scout_rank_score_1', 'input': 0.82, 'path_effect': 37.31168153475591}, {'feature': 'scout_graduated_absent', 'input': 0.0, 'path_effect': -0.13821362072029508}]

Same fitted candidate with the three graduation inputs zero: 458.601322. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Carroll is the largest offense deterioration relative to V68. He has only 104 MLB AB, remains rank two, and has 434 AA/AAA PA with 23 HR plus 115 MLB PA/four HR. His graduation inputs are all zero. Appearance falls .96796 to .96597, active PA falls 477.58 to 458.60 and expected PA declines 462.28 to 443.00 versus 645. The zero-feature probe is identical, so it would be wrong to claim he was personally penalized for failing graduation; the added training representation changed other tree paths. The active workload path retains positive performance and current-rank effects but strong negative current-PA exposure. Forty-two active prior-listed non-graduates support the broad profile. Fixed hitting +.869/600 misses actual +3.022, magnifying the workload harm. Henderson 378 versus 622 is also too low, while Baty 351 versus 389 has optimistic offense, Groshans predicts 185 versus zero and Ramos 113 versus 60. More confidence is not universally correct; keep the actual harm and failed peers.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jordan Groshans | 233.08 | 189.42 | 184.59 | 0 | 0.516 | 0.000 |
| Gunnar Henderson | 355.28 | 381.72 | 378.17 | 622 | 1.507 | 3.987 |
| Brett Baty | 335.47 | 340.25 | 350.91 | 389 | 1.289 | -0.171 |
| Heliot Ramos | 121.23 | 116.82 | 113.35 | 60 | 0.245 | -0.160 |

## Chris Davis / 2017 to 2018

ID 448801; row 27537; fold 3; age 31.0; Current MLB; list available 2018-01-27. Selected: major false high.

Observed MLB AB lower bound 4149; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2008, 'at_bats': 295, 'plate_appearances': 317}, {'season': 2009, 'at_bats': 391, 'plate_appearances': 419}, {'season': 2010, 'at_bats': 120, 'plate_appearances': 136}, {'season': 2011, 'at_bats': 199, 'plate_appearances': 210}, {'season': 2012, 'at_bats': 515, 'plate_appearances': 562}, {'season': 2013, 'at_bats': 584, 'plate_appearances': 673}, {'season': 2014, 'at_bats': 450, 'plate_appearances': 525}, {'season': 2015, 'at_bats': 573, 'plate_appearances': 670}, {'season': 2016, 'at_bats': 566, 'plate_appearances': 665}, {'season': 2017, 'at_bats': 456, 'plate_appearances': 524}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.977731 | 518.137 | 506.599 | 1.08164 | 2.47165 |
| preseason | 0.975077 | 515.523 | 502.675 | 1.08164 | 2.45250 |
| graduation | 0.975077 | 515.523 | 502.675 | 1.08164 | 2.45250 |
| Actual | 1 | not a forecast | 522 | -4.101755833580411 | -1.96276 |

PA product 0.975076889 × 515.522980010; offense yield 1.081635642/600 + 0.003076176.

Actual MLB counts: [{'season': 2018, 'player_id': 448801, 'bucket': 'MLB', 'plate_appearances': 522, 'strike_outs': 192, 'unintentional_walks': 39, 'hit_by_pitch': 7, 'home_runs': 16, 'babip_hits': 63, 'doubles': 12, 'triples': 0, 'babip_opportunities': 266}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 723, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 588, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 542, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 487, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 723, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 588, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 542, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 487, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}].

Saved preseason participation: reference -4.135062; raw additive 3.666721; linked probability 0.975077.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.289472.
- games_mlb_0: input 128.000000, contribution +1.553995.
- MLB_0_pa: input 524.000000, contribution +0.771305.
- games_pool_MLB: input 349.600000, contribution +0.641813.
- pooled_MLB_pa: input 1458.000000, contribution +0.399849.
- work_0: input 524.000000, contribution +0.367452.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.005820685547618742}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0014483555316486957}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0003171241753077542}]

Saved graduation participation: reference -4.135062; raw additive 3.666721; linked probability 0.975077.
Largest path terms (accounting, not causality):
- on_40man: input 1.000000, contribution +3.289472.
- games_mlb_0: input 128.000000, contribution +1.553995.
- MLB_0_pa: input 524.000000, contribution +0.771305.
- games_pool_MLB: input 349.600000, contribution +0.641813.
- pooled_MLB_pa: input 1458.000000, contribution +0.399849.
- work_0: input 524.000000, contribution +0.367452.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.005820685547618742}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.0014483555316486957}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0003171241753077542}]

Same fitted candidate with the three graduation inputs zero: 0.975077. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 278.199728; raw additive 515.522980; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 524.000000, contribution +81.982997.
- role_pool_MLB: input 4.165740, contribution +33.611574.
- role_mlb_0: input 4.086957, contribution +30.084716.
- work_0: input 524.000000, contribution +27.346201.
- pooled_MLB_pa: input 1458.000000, contribution +21.943456.
- quality_0: input -0.119313, contribution -21.090887.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.5708548621932074}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.4841882716977104}]

Saved graduation conditional_pa: reference 278.199728; raw additive 515.522980; raw PA before bounds.
Largest path terms (accounting, not causality):
- MLB_0_pa: input 524.000000, contribution +81.982997.
- role_pool_MLB: input 4.165740, contribution +33.611574.
- role_mlb_0: input 4.086957, contribution +30.084716.
- work_0: input 524.000000, contribution +27.346201.
- pooled_MLB_pa: input 1458.000000, contribution +21.943456.
- quality_0: input -0.119313, contribution -21.090887.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.5708548621932074}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.4841882716977104}]

Same fitted candidate with the three graduation inputs zero: 515.522980. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Davis is the major false high in offense, not a major workload miss. Three MLB seasons show HR declining 47 to 38 to 26, with 208/219/195 strikeouts and latest 524 PA. Observed AB is 4,149, graduate absence is known and recent ranking history is zero. Both candidate heads exactly equal V68, as does the zero-feature probe: 502.67 expected PA versus 522 is reasonable workload, but fixed hitting +1.082/600 versus actual -4.102 leads to offense +2.452 versus -1.963. Graduation cannot repair the extreme hitting decline. There are 487 earlier active people in the broad veteran profile; a general support excuse is inappropriate. Guyer 171 versus 221 is usable, Barney 150 versus zero is an exit miss, and Romine/Joseph receive modest PA but deliver worse offense. This case remains a talent-tail miss to assess in the broad integration work, not a reason to haircut every veteran or pretend the full decline was predictable.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Brandon Guyer | 164.16 | 171.58 | 171.02 | 221 | 0.550 | 0.248 |
| Darwin Barney | 149.58 | 150.13 | 150.47 | 0 | 0.072 | 0.000 |
| Andrew Romine | 190.75 | 181.32 | 181.27 | 131 | 0.140 | -0.667 |
| Caleb Joseph | 187.11 | 186.69 | 193.82 | 280 | 0.118 | -0.762 |

## Harrison Bader / 2023 to 2024

ID 664056; row 51242; fold 1; age 29.0; Current MLB; list available 2024-01-26. Selected: ordinary active.

Observed MLB AB lower bound 1895; added inputs {'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}. Lower AB does not establish eligibility; no service-day reconstruction.

Raw MLB AB history: [{'season': 2017, 'at_bats': 85, 'plate_appearances': 92}, {'season': 2018, 'at_bats': 379, 'plate_appearances': 427}, {'season': 2019, 'at_bats': 347, 'plate_appearances': 406}, {'season': 2020, 'at_bats': 106, 'plate_appearances': 125}, {'season': 2021, 'at_bats': 367, 'plate_appearances': 401}, {'season': 2022, 'at_bats': 292, 'plate_appearances': 313}, {'season': 2023, 'at_bats': 319, 'plate_appearances': 344}]

Actual preseason ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0, 'scout_ab_graduated': 1, 'scout_graduated_absent': 1, 'scout_graduated_prior_score': 0.0}

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

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.666666 | 214.027 | 142.684 | -1.24059 | 0.14674 |
| preseason | 0.656696 | 213.686 | 140.326 | -1.24059 | 0.14432 |
| graduation | 0.658945 | 215.210 | 141.812 | -1.24059 | 0.14584 |
| Actual | 1 | not a forecast | 437 | -1.6573096273164938 | 0.14591 |

PA product 0.658944862 × 215.210038461; offense yield -1.240591022/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 664056, 'bucket': 'MLB', 'plate_appearances': 437, 'strike_outs': 95, 'unintentional_walks': 20, 'hit_by_pitch': 8, 'home_runs': 12, 'babip_hits': 83, 'doubles': 19, 'triples': 0, 'babip_opportunities': 301}]. No MLB PA is not observed zero hitting talent.

Actual earlier distinct-player profile support: [{'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 1179, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 951, 'arm': 'preseason', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 884, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 799, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 1179, 'arm': 'graduation', 'head': 'participation', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 951, 'arm': 'graduation', 'head': 'participation', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': 0, 'profile_people': 884, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'broad', 'scout_ab_graduated': None, 'previously_listed': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'rank_band': None, 'profile_people': 799, 'arm': 'graduation', 'head': 'conditional_pa', 'kind': 'graduation', 'scout_ab_graduated': 1, 'previously_listed': False}].

Saved preseason participation: reference -4.033199; raw additive 0.648606; linked probability 0.656696.
Largest path terms (accounting, not causality):
- games_mlb_0: input 98.000000, contribution +2.133544.
- games_pool_MLB: input 228.600000, contribution +1.080716.
- on_40man: input 0.000000, contribution -1.054582.
- work_0: input 344.000000, contribution +0.705119.
- pooled_MLB_pa: input 835.000000, contribution +0.428118.
- draft_rank: input 0.394128, contribution +0.372404.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.05548214786370521}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.013884193541377408}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.002335083926934947}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0016697089204641595}]

Saved graduation participation: reference -4.022695; raw additive 0.658596; linked probability 0.658945.
Largest path terms (accounting, not causality):
- games_mlb_0: input 98.000000, contribution +2.133621.
- games_pool_MLB: input 228.600000, contribution +1.080716.
- on_40man: input 0.000000, contribution -1.054582.
- work_0: input 344.000000, contribution +0.705119.
- pooled_MLB_pa: input 835.000000, contribution +0.428118.
- draft_rank: input 0.394128, contribution +0.362473.

Scouting/graduation path terms: [{'feature': 'scout_listed_1', 'input': 0.0, 'path_effect': -0.053682286962280085}, {'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.013883802615298545}, {'feature': 'scout_listed_0', 'input': 0.0, 'path_effect': -0.002335083926934947}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.0016697089204641595}]

Same fitted candidate with the three graduation inputs zero: 0.658945. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Saved preseason conditional_pa: reference 283.910666; raw additive 213.685535; raw PA before bounds.
Largest path terms (accounting, not causality):
- on_40man: input 0.000000, contribution -45.430389.
- work_0: input 344.000000, contribution +38.241481.
- quality_0: input -0.519569, contribution -34.674806.
- role_mlb_0: input 3.555556, contribution -30.268869.
- regular_window_scaled: input 0.333333, contribution +15.219887.
- role_pool_MLB: input 3.667225, contribution -10.165473.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.8916321051339628}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.2636789392767092}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.06706168295568601}]

Saved graduation conditional_pa: reference 283.918644; raw additive 215.210038; raw PA before bounds.
Largest path terms (accounting, not causality):
- on_40man: input 0.000000, contribution -45.959501.
- work_0: input 344.000000, contribution +38.241481.
- quality_0: input -0.519569, contribution -33.396502.
- role_mlb_0: input 3.555556, contribution -30.573043.
- regular_window_scaled: input 0.333333, contribution +15.219887.
- role_pool_MLB: input 3.667225, contribution -10.268842.

Scouting/graduation path terms: [{'feature': 'scout_rank_score_0', 'input': 0.0, 'path_effect': -0.9561285195423054}, {'feature': 'scout_rank_score_1', 'input': 0.0, 'path_effect': -0.26247153999466066}, {'feature': 'scout_graduated_prior_score', 'input': 0.0, 'path_effect': -0.1896929564957866}, {'feature': 'scout_rank_score_2', 'input': 0.0, 'path_effect': 0.06848923125524924}]

Same fitted candidate with the three graduation inputs zero: 215.210038. Artificial mechanics probe only; existing MLB history remains. Not a validated replacement forecast.

Bader is selected as an ordinary near-exact offense case, but the components are badly wrong. His known MLB workloads are 401, 313 and 344 PA with 16, five and seven HR. There are 1,895 observed AB, known graduate absence and no recent ranking history. Expected PA barely moves 140.33 to 141.81 versus 437; appearance .659 and active PA 215.21 are both low. The saved paths give the year-end on-40-man zero a -1.055 log-odds effect and -45.96 conditional-PA contribution. This is a roster-status mechanism to audit: being off a December roster need not mean a veteran has no future MLB employment. It is not proof his source zero was wrong or that correcting it would recover the actual season. Zeroing graduation inputs changes nothing. Fixed hitting -1.241/600 versus actual -1.657 cancels much of the workload error, yielding nearly exact offense .14584 versus .14591. His 799 active broad peers and Taylor/DeJong/Caratini/O'Hearn comparisons rule out a blanket empty-profile explanation. Check unsigned established hitters and role evidence before treating this lucky total as validated player value.

| Origin-selected peer | Original PA | Fresh-list PA | Graduate PA | Actual PA | Graduate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Tyrone Taylor | 261.19 | 258.73 | 257.23 | 345 | 0.667 | 0.608 |
| Paul DeJong | 374.94 | 384.45 | 383.82 | 482 | 0.120 | 0.832 |
| Victor Caratini | 246.38 | 249.73 | 255.68 | 274 | 0.246 | 0.976 |
| Ryan O'Hearn | 392.69 | 386.51 | 388.09 | 494 | 1.058 | 1.977 |

## Decision after actual review

Do not promote V69 as the full hitter candidate or claim graduation has been repaired. The 274 previously ranked AB graduates improve PA RMSE 178.907 to 177.953 versus V68, nominal paired MSE interval -667.61 to -25.39, but still trail original 177.598; graduate offense and overall/public intervals span zero. Meadows remains unfixed, Carroll worsens, and public PA MAE 106.321 is still 15.46% worse than Steamer 92.083. Preserve the source logic and qualified evidence. Retain the original V53/V63 research model and the V68/V69 extensions separately; no post-result subgroup blend. Execution, baseball review and source representation are complete, not overall statistical validation or deployment.

Close the ranking/graduation batch. Return to the practical goal with one broad opportunity-semantics audit: distinguish a December roster listing from known MLB employment/role evidence, starting with unsigned established hitters such as Bader and weak/failed comparables. Reconcile actual source transactions and feature definitions before any fixed matched comparison; do not fabricate a roster listing, collect new college data, erase exits or launch a library tournament. Keep talent/workload cancellation explicit and prioritize the largest systematic workload gap over another rare ranking feature. After that bounded correction, choose the strongest coherent research candidate and provide a side-by-side team-filtered handoff, without claiming full WAR, six-year control or protected-2026 validation. The overall goal stays active.
