# Employment evidence and hitter opportunity

Same 30,506 historical forecasts, chronological whole-player folds and fixed hitting. Three added inputs distinguish capture-era coverage, a current unambiguous employment event and recorded free agency. Unknown employment is not a deal; attachment is not a guaranteed MLB job. No protected 2026 use or deployment.

| Group | Rows | Original PA RMSE | Fresh-list PA RMSE | Employment PA RMSE | Original MAE | Fresh-list MAE | Employment MAE | Employment offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 30506 | 60.686 | 60.499 | 60.470 | 20.745 | 20.612 | 20.667 | 0.453326 |
| public_broad | 2627 | 138.488 | 138.330 | 138.271 | 106.871 | 106.411 | 106.559 | 1.060577 |
| unsigned_current | 458 | 142.522 | 142.587 | 142.670 | 110.098 | 109.982 | 110.357 | 0.970229 |
| other_unlisted_current | 953 | 81.527 | 81.596 | 81.597 | 53.025 | 52.626 | 52.922 | 0.405172 |
| listed_current | 3130 | 154.292 | 154.234 | 154.225 | 124.135 | 123.984 | 123.992 | 1.268812 |
| upper_never_debut | 5454 | 56.242 | 55.127 | 54.955 | 19.097 | 18.732 | 18.866 | 0.312547 |
| lower_never_debut | 17852 | 7.828 | 7.966 | 7.955 | 0.656 | 0.622 | 0.628 | 0.043014 |
| current_MLB | 4541 | 140.980 | 140.951 | 140.955 | 107.900 | 107.697 | 107.811 | 1.113890 |

Losses weight target years equally; raw totals are not rescaled. Offense is custom batting plus replacement, not full WAR. Development intervals are whole-player paired, not a fresh protected test. Exact transaction publication vintages and equal public-forecast information dates remain unverified.

## Harrison Bader / 2023 to 2024

ID 664056; row 51242; fold 1; age 29.0; Current MLB; ranking information date 2024-01-26. Selected: fixed before fit.

Employment evidence: {'row_id': 51242, 'player_id': 664056, 'origin_year': 2023, 'latest_employment_date': '2023-11-02', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 255909, 'player_id': 664056, 'available_date': '2016-03-03', 'recorded_date': '2016-03-03', 'effective_date': '2016-03-03', 'resolution_date': '2016-03-03', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'OF Harrison Bader assigned to St. Louis Cardinals.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 298052, 'player_id': 664056, 'available_date': '2017-02-16', 'recorded_date': '2017-02-16', 'effective_date': '2017-02-16', 'resolution_date': '2017-02-16', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'St. Louis Cardinals invited non-roster OF Harrison Bader to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 481081, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'St. Louis Cardinals activated CF Harrison Bader from the 10-day injured list.', 'recorded_date': '2021-04-30', 'effective_date': '2021-04-30', 'resolution_date': '2021-04-30', 'available_date': '2021-04-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 496162, 'player_id': 664056, 'available_date': '2021-06-25', 'recorded_date': '2021-06-25', 'effective_date': '2021-06-25', 'resolution_date': '2021-06-25', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'St. Louis Cardinals sent CF Harrison Bader on a rehab assignment to Palm Beach Cardinals.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 497733, 'player_id': 664056, 'available_date': '2021-06-29', 'recorded_date': '2021-06-29', 'effective_date': '2021-06-29', 'resolution_date': '2021-06-29', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'St. Louis Cardinals sent CF Harrison Bader on a rehab assignment to Memphis Redbirds.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 500412, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'St. Louis Cardinals activated CF Harrison Bader.', 'recorded_date': '2021-07-01', 'effective_date': '2021-07-01', 'resolution_date': '2021-07-01', 'available_date': '2021-07-01', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 639439, 'player_id': 664056, 'available_date': '2022-07-22', 'recorded_date': '2022-07-22', 'effective_date': '2022-07-22', 'resolution_date': '2022-07-22', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'St. Louis Cardinals sent CF Harrison Bader on a rehab assignment to Memphis Redbirds.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 641664, 'player_id': 664056, 'available_date': '2022-07-22', 'recorded_date': '2022-07-22', 'effective_date': '2022-07-22', 'resolution_date': '2022-07-22', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'St. Louis Cardinals sent CF Harrison Bader on a rehab assignment to Memphis Redbirds.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 642505, 'player_id': 664056, 'available_date': '2022-08-02', 'recorded_date': '2022-08-02', 'effective_date': '2022-08-02', 'resolution_date': None, 'status': 'attached', 'type_code': 'TR', 'type_description': 'Trade', 'description': 'New York Yankees traded LHP Jordan Montgomery to St. Louis Cardinals for CF Harrison Bader.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 651693, 'player_id': 664056, 'available_date': '2022-09-11', 'recorded_date': '2022-09-11', 'effective_date': '2022-09-11', 'resolution_date': '2022-09-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Somerset Patriots.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 652087, 'player_id': 664056, 'available_date': '2022-09-11', 'recorded_date': '2022-09-11', 'effective_date': '2022-09-11', 'resolution_date': '2022-09-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Somerset Patriots.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 653157, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated CF Harrison Bader from the 60-day injured list.', 'recorded_date': '2022-09-20', 'effective_date': '2022-09-20', 'resolution_date': '2022-09-20', 'available_date': '2022-09-20', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 686544, 'player_id': 664056, 'available_date': '2023-04-21', 'recorded_date': '2023-04-21', 'effective_date': '2023-04-21', 'resolution_date': '2023-04-21', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Somerset Patriots.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 688309, 'player_id': 664056, 'available_date': '2023-04-25', 'recorded_date': '2023-04-25', 'effective_date': '2023-04-25', 'resolution_date': '2023-04-25', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Scranton/Wilkes-Barre RailRiders.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 687145, 'player_id': 664056, 'available_date': '2023-04-25', 'recorded_date': '2023-04-25', 'effective_date': '2023-04-25', 'resolution_date': '2023-04-25', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Scranton/Wilkes-Barre RailRiders.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 688310, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated CF Harrison Bader from the 10-day injured list.', 'recorded_date': '2023-05-02', 'effective_date': '2023-05-02', 'resolution_date': '2023-05-02', 'available_date': '2023-05-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 703887, 'player_id': 664056, 'available_date': '2023-06-14', 'recorded_date': '2023-06-14', 'effective_date': '2023-06-14', 'resolution_date': '2023-06-14', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent CF Harrison Bader on a rehab assignment to Somerset Patriots.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 705351, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated CF Harrison Bader from the 10-day injured list.', 'recorded_date': '2023-06-20', 'effective_date': '2023-06-20', 'resolution_date': '2023-06-20', 'available_date': '2023-06-20', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 722763, 'player_id': 664056, 'available_date': '2023-08-31', 'recorded_date': '2023-08-31', 'effective_date': '2023-08-31', 'resolution_date': None, 'status': 'attached', 'type_code': 'CLW', 'type_description': 'Claimed Off Waivers', 'description': 'Cincinnati Reds claimed CF Harrison Bader off waivers from New York Yankees.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 722925, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Cincinnati Reds activated CF Harrison Bader.', 'recorded_date': '2023-09-01', 'effective_date': '2023-09-01', 'resolution_date': '2023-09-01', 'available_date': '2023-09-01', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 727566, 'player_id': 664056, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Cincinnati Reds activated CF Harrison Bader from the 10-day injured list.', 'recorded_date': '2023-10-02', 'effective_date': '2023-10-02', 'resolution_date': '2023-10-02', 'available_date': '2023-10-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 730389, 'player_id': 664056, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'CF Harrison Bader elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

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
| employment | 0.667524 | 205.983 | 137.498 | -1.24059 | 0.14141 |
| Actual | 1 | not a forecast | 437 | -1.6573096273164938 | 0.14591 |

PA product 0.667524261 × 205.982605712; offense yield -1.240591022/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 664056, 'bucket': 'MLB', 'plate_appearances': 437, 'strike_outs': 95, 'unintentional_walks': 20, 'hit_by_pitch': 8, 'home_runs': 12, 'babip_hits': 83, 'doubles': 19, 'triples': 0, 'babip_opportunities': 301}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 257, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 42, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 188, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 24, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 257, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 42, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 188, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51242, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 24, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.033199; raw additive 0.648606; linked probability 0.656696.

Largest path terms (accounting, not causality):

- games_mlb_0: input 98.000000, contribution +2.133544.
- games_pool_MLB: input 228.600000, contribution +1.080716.
- on_40man: input 0.000000, contribution -1.054582.
- work_0: input 344.000000, contribution +0.705119.
- pooled_MLB_pa: input 835.000000, contribution +0.428118.
- draft_rank: input 0.394128, contribution +0.372404.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -1.0545824766187355}]

Saved employment participation: reference -4.061106; raw additive 0.697009; linked probability 0.667524.

Largest path terms (accounting, not causality):

- games_mlb_0: input 98.000000, contribution +1.990713.
- games_pool_MLB: input 228.600000, contribution +1.068967.
- on_40man: input 0.000000, contribution -1.011159.
- work_0: input 344.000000, contribution +0.699023.
- draft_rank: input 0.394128, contribution +0.439794.
- pooled_MLB_pa: input 835.000000, contribution +0.413452.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -1.0111590867636437}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.15184825838001037}, {'feature': 'employment_year_fa', 'input': 1.0, 'path_effect': 0.13880137566162995}]

Same fitted candidate with the three new inputs zero: 0.637036. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 283.910666; raw additive 213.685535; raw PA before bounds.

Largest path terms (accounting, not causality):

- on_40man: input 0.000000, contribution -45.430389.
- work_0: input 344.000000, contribution +38.241481.
- quality_0: input -0.519569, contribution -34.674806.
- role_mlb_0: input 3.555556, contribution -30.268869.
- regular_window_scaled: input 0.333333, contribution +15.219887.
- role_pool_MLB: input 3.667225, contribution -10.165473.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -45.430389413060574}]

Saved employment conditional_pa: reference 283.915500; raw additive 205.982606; raw PA before bounds.

Largest path terms (accounting, not causality):

- on_40man: input 0.000000, contribution -45.430174.
- work_0: input 344.000000, contribution +38.241481.
- quality_0: input -0.519569, contribution -34.131532.
- role_mlb_0: input 3.555556, contribution -30.397544.
- regular_window_scaled: input 0.333333, contribution +15.219887.
- role_pool_MLB: input 3.667225, contribution -10.164856.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -45.43017400058688}, {'feature': 'employment_year_fa', 'input': 1.0, 'path_effect': -3.2567336373680313}]

Same fitted candidate with the three new inputs zero: 212.994357. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Bader had 401/313/344 MLB PA and 16/5/7 HR in the three source years, plus small rehab samples. His November 2 free agency is correctly known; roster zero is not secretly flipped. The new model's .667524 appearance chance times 205.983 conditional PA gives 137.498 expected PA, down from 140.326, versus 437 actual. Its roster path still subtracts 1.01116 log-odds and 45.43017 conditional PA. Known/free-agent paths add .15185/.13880 log-odds but the conditional FA path subtracts 3.25673 PA. Zero-new-input mechanics gives .637036 and 212.994, not a causal estimate. There are 42 refined participation people and 24 active people, so this is not an empty generic subgroup. Gallo 194/260, Anderson 158/5, Vogelbach 206/79 and Newman 118/311 retain failures as well as returns. Offense .1414 versus .1459 is cancellation: fixed hitting -1.2406/600 is less negative than observed -1.6573. The useful source distinction does not fix his workload.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Joey Gallo | 192.67 | 192.17 | 193.73 | 260 | 0.621 | -0.104 |
| Brian Anderson | 163.45 | 161.25 | 158.25 | 5 | 0.257 | -0.116 |
| Daniel Vogelbach | 179.71 | 192.62 | 206.42 | 79 | 0.750 | -0.118 |
| Kevin Newman | 119.86 | 118.69 | 117.63 | 311 | 0.136 | 0.302 |

## Bryce Harper / 2018 to 2019

ID 547180; row 32553; fold 2; age 25.0; Current MLB; ranking information date 2019-01-27. Selected: fixed before fit.

Employment evidence: {'row_id': 32553, 'player_id': 547180, 'origin_year': 2018, 'latest_employment_date': '2018-10-29', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 265585, 'player_id': 547180, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Washington Nationals activated RF Bryce Harper.', 'recorded_date': '2016-05-15', 'effective_date': '2016-05-15', 'resolution_date': '2016-05-15', 'available_date': '2016-05-15', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 314297, 'player_id': 547180, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Washington Nationals activated RF Bryce Harper.', 'recorded_date': '2017-06-04', 'effective_date': '2017-06-04', 'resolution_date': '2017-06-04', 'available_date': '2017-06-04', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 333065, 'player_id': 547180, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Washington Nationals activated RF Bryce Harper from the 10-day disabled list.', 'recorded_date': '2017-09-26', 'effective_date': '2017-09-26', 'resolution_date': '2017-09-26', 'available_date': '2017-09-26', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 381699, 'player_id': 547180, 'available_date': '2018-10-29', 'recorded_date': '2018-10-29', 'effective_date': '2018-10-29', 'resolution_date': '2018-10-29', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'RF Bryce Harper elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | MLB | 627 | 24 | 117 | 88 |
| 2017 | MLB | 492 | 29 | 99 | 57 |
| 2018 | MLB | 695 | 34 | 169 | 114 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.954089 | 590.268 | 563.169 | 2.77451 | 4.33878 |
| preseason | 0.931897 | 578.867 | 539.445 | 2.77451 | 4.15600 |
| employment | 0.933525 | 583.869 | 545.057 | 2.77451 | 4.19924 |
| Actual | 1 | not a forecast | 682 | 2.747467093500647 | 5.22354 |

PA product 0.933524955 × 583.869464785; offense yield 2.774511805/600 + 0.003080035.

Actual MLB counts: [{'season': 2019, 'player_id': 547180, 'bucket': 'MLB', 'plate_appearances': 682, 'strike_outs': 178, 'unintentional_walks': 88, 'hit_by_pitch': 6, 'home_runs': 35, 'babip_hits': 114, 'doubles': 36, 'triples': 1, 'babip_opportunities': 364}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 3, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 0, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 4, 'quality_band': 2}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 2, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 0, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 4, 'quality_band': 2}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 3, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 0, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 4, 'quality_band': 2}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 2, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 32553, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 0, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 4, 'quality_band': 2}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.075952; raw additive 2.616206; linked probability 0.931897.

Largest path terms (accounting, not causality):

- games_mlb_0: input 159.000000, contribution +2.739951.
- MLB_0_pa: input 695.000000, contribution +0.971607.
- on_40man: input 0.000000, contribution -0.903873.
- games_pool_MLB: input 336.000000, contribution +0.810781.
- quality_0: input 1.013842, contribution +0.623833.
- pooled_MLB_pa: input 1464.800000, contribution +0.487680.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.903873475649195}]

Saved employment participation: reference -4.075862; raw additive 2.642141; linked probability 0.933525.

Largest path terms (accounting, not causality):

- games_mlb_0: input 159.000000, contribution +2.723405.
- MLB_0_pa: input 695.000000, contribution +0.990574.
- on_40man: input 0.000000, contribution -0.903873.
- games_pool_MLB: input 336.000000, contribution +0.809317.
- quality_0: input 1.013842, contribution +0.614792.
- pooled_MLB_pa: input 1464.800000, contribution +0.487680.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.90387277365567}]

Same fitted candidate with the three new inputs zero: 0.933525. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 282.952438; raw additive 578.867455; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 694.714109, contribution +82.210283.
- MLB_0_pa: input 695.000000, contribution +65.143013.
- role_mlb_0: input 4.349112, contribution +36.711555.
- quality_0: input 1.013842, contribution +34.694794.
- age_centered: input -0.400000, contribution +20.851308.
- regular_window_scaled: input 1.000000, contribution +20.393387.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -16.94817618842978}]

Saved employment conditional_pa: reference 282.905166; raw additive 583.869465; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 694.714109, contribution +82.210283.
- MLB_0_pa: input 695.000000, contribution +65.143013.
- role_mlb_0: input 4.349112, contribution +36.434503.
- quality_0: input 1.013842, contribution +34.012735.
- pooled_mlb_quality: input 1.508592, contribution +21.321870.
- age_centered: input -0.400000, contribution +20.488199.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -16.94817618842978}]

Same fitted candidate with the three new inputs zero: 583.869465. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Harper's raw 627/492/695 MLB PA, 24/29/34 HR and 88/57/114 unintentional walks establish a young productive regular. October 29 free agency and roster zero are correct. New .933525 times 583.869 gives 545.057 PA, only six above 539.445, versus 682. No employment term is used on either own path and the zero-new-input outputs are identical; this is shared refitting, not a learned free-agent-star correction. The roster path remains -.90387 log-odds and -16.94818 PA. Only three distinct broad FA participation people/two active people and zero refined analogues precede this test, unlike broad all-unsigned support. Fixed hitting 2.7745 closely matches 2.7475 actual, so workload drives offense 4.199 versus 5.224. Machado 590/661 and Moustakas 502/584 return, while Davidson 325/0 and Russell 294/241 show why general unlisted optimism is unsafe.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Manny Machado | 592.41 | 587.85 | 590.41 | 661 | 3.480 | 3.596 |
| Addison Russell | 306.13 | 290.08 | 294.25 | 241 | 0.798 | 0.479 |
| Mike Moustakas | 520.80 | 499.84 | 501.53 | 584 | 2.001 | 3.787 |
| Matt Davidson | 323.08 | 327.16 | 325.20 | 0 | 1.115 | 0.000 |

## Matt Wieters / 2016 to 2017

ID 446308; row 22904; fold 3; age 30.0; Current MLB; ranking information date 2017-01-28. Selected: fixed before fit.

Employment evidence: {'row_id': 22904, 'player_id': 446308, 'origin_year': 2016, 'latest_employment_date': '2016-11-03', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 226807, 'player_id': 446308, 'available_date': '2015-05-26', 'recorded_date': '2015-05-26', 'effective_date': '2015-05-26', 'resolution_date': '2015-05-26', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Baltimore Orioles sent C Matt Wieters on a rehab assignment to Bowie Baysox.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 228496, 'player_id': 446308, 'available_date': '2015-06-02', 'recorded_date': '2015-06-02', 'effective_date': '2015-06-02', 'resolution_date': '2015-06-02', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Baltimore Orioles sent C Matt Wieters on a rehab assignment to Norfolk Tides.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 228913, 'player_id': 446308, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Baltimore Orioles activated C Matt Wieters from the 60-day disabled list.', 'recorded_date': '2015-06-05', 'effective_date': '2015-06-05', 'resolution_date': '2015-06-05', 'available_date': '2015-06-05', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 248553, 'player_id': 446308, 'available_date': '2015-11-02', 'recorded_date': '2015-11-02', 'effective_date': '2015-11-02', 'resolution_date': '2015-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'C Matt Wieters elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 250110, 'player_id': 446308, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Baltimore Orioles activated C Matt Wieters.', 'recorded_date': '2015-11-13', 'effective_date': '2015-11-13', 'resolution_date': '2015-11-13', 'available_date': '2015-11-13', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 284881, 'player_id': 446308, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Baltimore Orioles activated C Matt Wieters from the paternity list.', 'recorded_date': '2016-08-22', 'effective_date': '2016-08-22', 'resolution_date': '2016-08-22', 'available_date': '2016-08-22', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 292088, 'player_id': 446308, 'available_date': '2016-11-03', 'recorded_date': '2016-11-03', 'effective_date': '2016-11-03', 'resolution_date': '2016-11-03', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'C Matt Wieters elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | MLB | 112 | 5 | 19 | 6 |
| 2015 | AA | 13 | 0 | 0 | 1 |
| 2015 | AAA | 6 | 1 | 0 | 1 |
| 2015 | MLB | 282 | 8 | 67 | 21 |
| 2016 | MLB | 464 | 17 | 85 | 31 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.838938 | 334.034 | 280.233 | -0.61266 | 0.57853 |
| preseason | 0.819058 | 326.397 | 267.338 | -0.61266 | 0.55190 |
| employment | 0.819058 | 326.397 | 267.338 | -0.61266 | 0.55190 |
| Actual | 1 | not a forecast | 465 | -2.1523172599645304 | -0.23327 |

PA product 0.819058146 × 326.397023553; offense yield -0.612662944/600 + 0.003085550.

Actual MLB counts: [{'season': 2017, 'player_id': 446308, 'bucket': 'MLB', 'plate_appearances': 465, 'strike_outs': 94, 'unintentional_walks': 34, 'hit_by_pitch': 1, 'home_runs': 10, 'babip_hits': 85, 'doubles': 20, 'triples': 0, 'babip_opportunities': 322}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 41, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 8, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 1}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 24, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 6, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 1}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 41, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 8, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 1}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 24, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 22904, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 6, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.078610; raw additive 1.509979; linked probability 0.819058.

Largest path terms (accounting, not causality):

- games_mlb_0: input 124.000000, contribution +1.999160.
- games_pool_MLB: input 199.600000, contribution +1.350464.
- on_40man: input 0.000000, contribution -0.910270.
- MLB_0_pa: input 464.000000, contribution +0.841811.
- pooled_MLB_pa: input 756.800000, contribution +0.616043.
- draft_rank: input 0.788257, contribution +0.543814.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9102697831828568}]

Saved employment participation: reference -4.078610; raw additive 1.509979; linked probability 0.819058.

Largest path terms (accounting, not causality):

- games_mlb_0: input 124.000000, contribution +1.999160.
- games_pool_MLB: input 199.600000, contribution +1.350464.
- on_40man: input 0.000000, contribution -0.910270.
- MLB_0_pa: input 464.000000, contribution +0.841811.
- pooled_MLB_pa: input 756.800000, contribution +0.616043.
- draft_rank: input 0.788257, contribution +0.543814.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9102697831828568}]

Same fitted candidate with the three new inputs zero: 0.819058. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 276.994851; raw additive 326.397024; raw PA before bounds.

Largest path terms (accounting, not causality):

- MLB_0_pa: input 464.000000, contribution +87.813806.
- work_0: input 464.382208, contribution +56.092583.
- role_mlb_0: input 3.761194, contribution -30.826768.
- on_40man: input 0.000000, contribution -17.674140.
- quality_0: input -0.132015, contribution -15.980059.
- draft_elapsed: input 0.900000, contribution -11.054635.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -17.674140338111155}]

Saved employment conditional_pa: reference 276.994851; raw additive 326.397024; raw PA before bounds.

Largest path terms (accounting, not causality):

- MLB_0_pa: input 464.000000, contribution +87.813806.
- work_0: input 464.382208, contribution +56.092583.
- role_mlb_0: input 3.761194, contribution -30.826768.
- on_40man: input 0.000000, contribution -17.674140.
- quality_0: input -0.132015, contribution -15.980059.
- draft_elapsed: input 0.900000, contribution -11.054635.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -17.674140338111155}]

Same fitted candidate with the three new inputs zero: 326.397024. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Wieters returned from 112 and 282 MLB PA to 464 with 17 HR and 85 K; November 3 free agency is known, unlike an exit inferred merely from roster absence. Earliest training captures span only 2015. Both saved candidate heads exactly replay the fresher-list anchor: .819058 times 326.397 equals 267.338 expected PA versus 465 actual, and the zero-new-input probe is also identical. Neither new input appears on his paths; roster still subtracts .91027 log-odds and 17.67414 PA. Refined source-status support is eight participation people and six active people, not the complete unsigned population. Alvarez 285/34, Beckham 142/18, Coghlan 162/88 and Wallace 52/0 are failed-return controls. His fixed rate -.6127 is too optimistic versus -2.1523, so simply increasing PA would worsen offense .552 versus -.233. The employment addition proves neither workload nor delivered-value improvement.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pedro Álvarez | 295.35 | 285.16 | 285.16 | 34 | 1.165 | 0.186 |
| Gordon Beckham | 155.79 | 141.13 | 142.01 | 18 | 0.273 | -0.139 |
| Chris Coghlan | 150.33 | 154.46 | 162.32 | 88 | 0.551 | -0.141 |
| Brett Wallace | 59.89 | 50.30 | 52.04 | 0 | 0.103 | 0.000 |

## Jackie Bradley Jr. / 2022 to 2023

ID 598265; row 46588; fold 2; age 32.0; Current MLB; ranking information date 2023-01-26. Selected: fixed before fit.

Employment evidence: {'row_id': 46588, 'player_id': 598265, 'origin_year': 2022, 'latest_employment_date': '2022-11-07', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 268759, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr. from the paternity list.', 'recorded_date': '2016-06-03', 'effective_date': '2016-06-03', 'resolution_date': '2016-06-03', 'available_date': '2016-06-03', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 306336, 'player_id': 598265, 'available_date': '2017-04-18', 'recorded_date': '2017-04-18', 'effective_date': '2017-04-18', 'resolution_date': '2017-04-18', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Boston Red Sox sent CF Jackie Bradley Jr. on a rehab assignment to Pawtucket Red Sox.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 306967, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr. from the 10-day disabled list.', 'recorded_date': '2017-04-21', 'effective_date': '2017-04-21', 'resolution_date': '2017-04-21', 'available_date': '2017-04-21', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 331609, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr. from the 10-day injured list.', 'recorded_date': '2017-09-02', 'effective_date': '2017-09-02', 'resolution_date': '2017-09-02', 'available_date': '2017-09-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 454209, 'player_id': 598265, 'available_date': '2020-10-28', 'recorded_date': '2020-10-28', 'effective_date': '2020-10-28', 'resolution_date': '2020-10-28', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'CF Jackie Bradley Jr. elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 473212, 'player_id': 598265, 'available_date': '2021-03-08', 'recorded_date': '2021-03-08', 'effective_date': '2021-03-08', 'resolution_date': '2021-03-08', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Milwaukee Brewers signed free agent CF Jackie Bradley Jr..', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 478537, 'player_id': 598265, 'available_date': '2021-03-08', 'recorded_date': '2021-03-08', 'effective_date': '2021-03-08', 'resolution_date': '2021-03-08', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Milwaukee Brewers signed free agent CF Jackie Bradley Jr..', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 477801, 'player_id': 598265, 'available_date': '2021-03-08', 'recorded_date': '2021-03-08', 'effective_date': '2021-03-08', 'resolution_date': '2021-03-08', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Milwaukee Brewers signed free agent CF Jackie Bradley Jr..', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 615029, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr..', 'recorded_date': '2021-12-01', 'effective_date': '2021-12-01', 'resolution_date': '2021-12-01', 'available_date': '2021-12-01', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 615564, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr..', 'recorded_date': '2021-12-01', 'effective_date': '2021-12-01', 'resolution_date': '2021-12-01', 'available_date': '2021-12-01', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 601101, 'player_id': 598265, 'available_date': '2021-12-01', 'recorded_date': '2021-12-01', 'effective_date': None, 'resolution_date': None, 'status': 'attached', 'type_code': 'TR', 'type_description': 'Trade', 'description': 'Milwaukee Brewers traded CF Jackie Bradley Jr., SS David Hamilton and 3B Alex Binelas to Boston Red Sox for RF Hunter Renfroe.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 629080, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Boston Red Sox activated CF Jackie Bradley Jr. from the paternity list.', 'recorded_date': '2022-06-06', 'effective_date': '2022-06-06', 'resolution_date': '2022-06-06', 'available_date': '2022-06-06', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 645010, 'player_id': 598265, 'available_date': '2022-08-09', 'recorded_date': '2022-08-09', 'effective_date': '2022-08-09', 'resolution_date': '2022-08-09', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Toronto Blue Jays signed free agent CF Jackie Bradley Jr..', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 645080, 'player_id': 598265, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Toronto Blue Jays activated CF Jackie Bradley Jr..', 'recorded_date': '2022-08-09', 'effective_date': '2022-08-09', 'resolution_date': '2022-08-09', 'available_date': '2022-08-09', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 658443, 'player_id': 598265, 'available_date': '2022-11-07', 'recorded_date': '2022-11-07', 'effective_date': '2022-11-07', 'resolution_date': '2022-11-07', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'CF Jackie Bradley Jr. elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 217 | 7 | 48 | 22 |
| 2021 | MLB | 428 | 6 | 132 | 28 |
| 2022 | MLB | 370 | 4 | 77 | 24 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.659798 | 193.594 | 127.733 | -1.95192 | -0.01561 |
| preseason | 0.670462 | 193.547 | 129.766 | -1.95192 | -0.01586 |
| employment | 0.664741 | 198.238 | 131.777 | -1.95192 | -0.01611 |
| Actual | 1 | not a forecast | 113 | -6.341304727292759 | -0.84048 |

PA product 0.664741140 × 198.237911110; offense yield -1.951917201/600 + 0.003130974.

Actual MLB counts: [{'season': 2023, 'player_id': 598265, 'bucket': 'MLB', 'plate_appearances': 113, 'strike_outs': 29, 'unintentional_walks': 5, 'hit_by_pitch': 2, 'home_runs': 1, 'babip_hits': 13, 'doubles': 5, 'triples': 0, 'babip_opportunities': 75}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 230, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 38, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 161, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 230, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 38, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 161, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46588, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 0}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.106626; raw additive 0.710275; linked probability 0.670462.

Largest path terms (accounting, not causality):

- games_mlb_0: input 132.000000, contribution +2.382579.
- on_40man: input 0.000000, contribution -0.955947.
- games_pool_MLB: input 328.300000, contribution +0.944318.
- work_0: input 370.000000, contribution +0.652941.
- absence_window_scaled: input 0.000000, contribution +0.528647.
- draft_rank: input 0.514679, contribution +0.384305.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9559474750244967}]

Saved employment participation: reference -4.108696; raw additive 0.684495; linked probability 0.664741.

Largest path terms (accounting, not causality):

- games_mlb_0: input 132.000000, contribution +2.329357.
- on_40man: input 0.000000, contribution -0.956618.
- games_pool_MLB: input 328.300000, contribution +0.896861.
- work_0: input 370.000000, contribution +0.644880.
- absence_window_scaled: input 0.000000, contribution +0.528647.
- games_mlb_1: input 134.000000, contribution +0.336709.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.956618223385867}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.13644035598810955}]

Same fitted candidate with the three new inputs zero: 0.630619. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 279.630460; raw additive 193.546957; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 370.000000, contribution +102.994672.
- role_mlb_0: input 2.887324, contribution -64.424231.
- on_40man: input 0.000000, contribution -47.930906.
- quality_0: input -0.673977, contribution -31.811198.
- age_centered: input 1.000000, contribution -20.863546.
- regular_window_scaled: input 0.666667, contribution +13.817001.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -47.930906293001954}]

Saved employment conditional_pa: reference 279.642323; raw additive 198.237911; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 370.000000, contribution +103.044037.
- role_mlb_0: input 2.887324, contribution -64.409845.
- on_40man: input 0.000000, contribution -47.930906.
- quality_0: input -0.673977, contribution -31.759136.
- age_centered: input 1.000000, contribution -20.371312.
- pooled_mlb_quality: input -1.150958, contribution -15.932139.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -47.930906293001954}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 3.1570346429794194}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 0.7131143708182587}]

Same fitted candidate with the three new inputs zero: 188.154736. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Bradley had 217 PA in shortened 2020, then 428 and 370 with 6/4 HR. The short season remains explicit. Toronto's August signing/activation is followed by November 7 free agency; the current unsigned flag is correct. Expected PA moves 129.766 to 131.777 (.664741 times 198.238), versus 113: workload was already reasonable, not an automatic underprediction to repair. Known-current evidence adds .13644 log-odds and 3.15703 conditional PA; the zero-new-input probe is .630619/188.155, while the roster penalty remains nearly unchanged. Refined support is 38 participation/23 active people. Naquin 196/8 and Pinder 139/0 fail, Grossman 244/420 and Dickerson 97/152 return. Offense -.016 versus -.840 is a hitting miss: -1.9519 fixed rate versus -6.3413 observed. This case argues against a blanket free-agent PA increase.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Tyler Naquin | 199.43 | 197.01 | 195.54 | 8 | 0.547 | -0.179 |
| Robbie Grossman | 242.50 | 242.30 | 244.43 | 420 | 0.607 | 1.903 |
| Corey Dickerson | 97.61 | 96.33 | 97.18 | 152 | 0.189 | 0.112 |
| Chad Pinder | 149.83 | 134.60 | 138.65 | 0 | 0.241 | 0.000 |

## Brandon Belt / 2022 to 2023

ID 474832; row 46338; fold 3; age 34.0; Current MLB; ranking information date 2023-01-26. Selected: fixed before fit.

Employment evidence: {'row_id': 46338, 'player_id': 474832, 'origin_year': 2022, 'latest_employment_date': '2022-11-06', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 277732, 'player_id': 474832, 'available_date': '2016-07-11', 'recorded_date': '2016-07-11', 'effective_date': '2016-07-11', 'resolution_date': '2016-07-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': '1B Brandon Belt assigned to National League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 336139, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 60-day disabled list.', 'recorded_date': '2017-11-03', 'effective_date': '2017-11-03', 'resolution_date': '2017-11-03', 'available_date': '2017-11-03', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 361013, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day disabled list.', 'recorded_date': '2018-06-16', 'effective_date': '2018-06-16', 'resolution_date': '2018-06-16', 'available_date': '2018-06-16', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 370189, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the paternity list.', 'recorded_date': '2018-07-21', 'effective_date': '2018-07-21', 'resolution_date': '2018-07-21', 'available_date': '2018-07-21', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 374283, 'player_id': 474832, 'available_date': '2018-08-11', 'recorded_date': '2018-08-11', 'effective_date': '2018-08-11', 'resolution_date': '2018-08-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'San Francisco Giants sent 1B Brandon Belt on a rehab assignment to Sacramento River Cats.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 374764, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2018-08-14', 'effective_date': '2018-08-14', 'resolution_date': '2018-08-14', 'available_date': '2018-08-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 477758, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10 day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 478413, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 448529, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 493518, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2021-06-08', 'effective_date': '2021-06-08', 'resolution_date': '2021-06-08', 'available_date': '2021-06-08', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 507998, 'player_id': 474832, 'available_date': '2021-07-29', 'recorded_date': '2021-07-29', 'effective_date': '2021-07-29', 'resolution_date': '2021-07-29', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'San Francisco Giants sent 1B Brandon Belt on a rehab assignment to Sacramento River Cats.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 509806, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt.', 'recorded_date': '2021-08-05', 'effective_date': '2021-08-05', 'resolution_date': '2021-08-05', 'available_date': '2021-08-05', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 514831, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the bereavement list.', 'recorded_date': '2021-08-29', 'effective_date': '2021-08-29', 'resolution_date': '2021-08-29', 'available_date': '2021-08-29', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 521187, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2021-10-07', 'effective_date': '2021-10-07', 'resolution_date': '2021-10-07', 'available_date': '2021-10-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 521828, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt.', 'recorded_date': '2021-10-15', 'effective_date': '2021-10-15', 'resolution_date': '2021-10-15', 'available_date': '2021-10-15', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 523189, 'player_id': 474832, 'available_date': '2021-11-03', 'recorded_date': '2021-11-03', 'effective_date': '2021-11-03', 'resolution_date': '2021-11-03', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 600125, 'player_id': 474832, 'available_date': '2021-11-17', 'recorded_date': '2021-11-17', 'effective_date': '2021-11-17', 'resolution_date': '2021-11-17', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'San Francisco Giants signed free agent 1B Brandon Belt.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 619854, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2022-05-07', 'effective_date': '2022-05-07', 'resolution_date': '2022-05-07', 'available_date': '2022-05-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 631072, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2022-06-14', 'effective_date': '2022-06-14', 'resolution_date': '2022-06-14', 'available_date': '2022-06-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 658242, 'player_id': 474832, 'available_date': '2022-11-06', 'recorded_date': '2022-11-06', 'effective_date': '2022-11-06', 'resolution_date': '2022-11-06', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | MLB | 179 | 9 | 36 | 29 |
| 2021 | AAA | 15 | 0 | 3 | 2 |
| 2021 | MLB | 381 | 29 | 103 | 45 |
| 2022 | MLB | 298 | 8 | 81 | 35 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.425443 | 281.661 | 119.831 | 0.87359 | 0.54966 |
| preseason | 0.411813 | 273.409 | 112.593 | 0.87359 | 0.51646 |
| employment | 0.421589 | 276.221 | 116.452 | 0.87359 | 0.53416 |
| Actual | 1 | not a forecast | 404 | 3.1170577421166574 | 3.36373 |

PA product 0.421588890 × 276.221109349; offense yield 0.873587489/600 + 0.003130974.

Actual MLB counts: [{'season': 2023, 'player_id': 474832, 'bucket': 'MLB', 'plate_appearances': 404, 'strike_outs': 141, 'unintentional_walks': 60, 'hit_by_pitch': 2, 'home_runs': 19, 'babip_hits': 67, 'doubles': 23, 'triples': 0, 'babip_opportunities': 181}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 234, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 64, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 1}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 167, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 45, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 1}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 234, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 64, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 1}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 167, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 46338, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 45, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 2, 'quality_band': 1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.132366; raw additive -0.356477; linked probability 0.411813.

Largest path terms (accounting, not causality):

- games_mlb_0: input 78.000000, contribution +2.591331.
- games_pool_MLB: input 238.220000, contribution +1.036271.
- on_40man: input 0.000000, contribution -0.969836.
- games_mlb_1: input 97.000000, contribution +0.319943.
- pooled_MLB_pa: input 710.200000, contribution +0.318013.
- draft_rank: input 0.343442, contribution +0.298000.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9698362717007196}]

Saved employment participation: reference -4.143127; raw additive -0.316254; linked probability 0.421589.

Largest path terms (accounting, not causality):

- games_mlb_0: input 78.000000, contribution +2.582511.
- games_pool_MLB: input 238.220000, contribution +1.034943.
- on_40man: input 0.000000, contribution -0.984987.
- pooled_MLB_pa: input 710.200000, contribution +0.332764.
- games_mlb_1: input 97.000000, contribution +0.302504.
- pooled_AAA_pa: input 12.000000, contribution +0.257504.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9849870443574347}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.23019907319728436}, {'feature': 'employment_year_fa', 'input': 1.0, 'path_effect': 0.053159194233040497}]

Same fitted candidate with the three new inputs zero: 0.384925. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 277.296431; raw additive 273.409336; raw PA before bounds.

Largest path terms (accounting, not causality):

- pooled_mlb_quality: input 0.980568, contribution +47.298893.
- role_mlb_0: input 3.840909, contribution +34.690393.
- age_centered: input 1.400000, contribution -30.448295.
- on_40man: input 0.000000, contribution -26.034607.
- quality_0: input -0.060737, contribution -15.367508.
- role_pool_AAA: input 3.714286, contribution -14.200920.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -26.034606689226464}]

Saved employment conditional_pa: reference 277.321686; raw additive 276.221109; raw PA before bounds.

Largest path terms (accounting, not causality):

- pooled_mlb_quality: input 0.980568, contribution +46.865829.
- role_mlb_0: input 3.840909, contribution +35.008835.
- age_centered: input 1.400000, contribution -29.644325.
- on_40man: input 0.000000, contribution -26.034607.
- quality_0: input -0.060737, contribution -15.635156.
- role_pool_AAA: input 3.714286, contribution -14.365969.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -26.034606689226464}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 1.0570082954497007}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 0.6571352435398419}]

Same fitted candidate with the three new inputs zero: 264.972198. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Belt had 179 short-season MLB PA, 381 with 29 HR, then 298 with eight, plus a small 2021 AAA rehab sample. His last employment event is November 6 free agency, not a future Toronto contract. Known and FA terms add .23020/.05316 log-odds, and known/capture terms add only 1.05701/.65714 conditional PA. New .421589 times 276.221 gives 116.452 expected PA, slightly above 112.593 but far below 404 actual. Zero-new-input mechanics .384925/264.972 shows a modest within-fit effect, not the cross-fit change. Refined support 64/45 includes failures and returns; Dickerson 97/152, Duvall 118/353, Harrison 151/114 and Calhoun 139/174 do not warrant a uniform near-certain full season. Fixed hitting .8736 also understates actual 3.1171, so offense .534 versus 3.364 is not solved by documenting free agency.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Corey Dickerson | 97.61 | 96.33 | 97.18 | 152 | 0.189 | 0.112 |
| Adam Duvall | 94.31 | 111.90 | 118.43 | 353 | 0.252 | 2.296 |
| Josh Harrison | 161.80 | 152.78 | 151.43 | 114 | 0.227 | -0.189 |
| Kole Calhoun | 119.74 | 132.00 | 138.90 | 174 | 0.229 | 0.258 |

## Brandon Belt / 2023 to 2024

ID 474832; row 50571; fold 3; age 35.0; Current MLB; ranking information date 2024-01-26. Selected: fixed before fit.

Employment evidence: {'row_id': 50571, 'player_id': 474832, 'origin_year': 2023, 'latest_employment_date': '2023-11-02', 'recorded_open_fa': 1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 1}

Dated records at cutoff: [{'transaction_id': 277732, 'player_id': 474832, 'available_date': '2016-07-11', 'recorded_date': '2016-07-11', 'effective_date': '2016-07-11', 'resolution_date': '2016-07-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': '1B Brandon Belt assigned to National League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 336139, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 60-day disabled list.', 'recorded_date': '2017-11-03', 'effective_date': '2017-11-03', 'resolution_date': '2017-11-03', 'available_date': '2017-11-03', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 361013, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day disabled list.', 'recorded_date': '2018-06-16', 'effective_date': '2018-06-16', 'resolution_date': '2018-06-16', 'available_date': '2018-06-16', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 370189, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the paternity list.', 'recorded_date': '2018-07-21', 'effective_date': '2018-07-21', 'resolution_date': '2018-07-21', 'available_date': '2018-07-21', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 374283, 'player_id': 474832, 'available_date': '2018-08-11', 'recorded_date': '2018-08-11', 'effective_date': '2018-08-11', 'resolution_date': '2018-08-11', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'San Francisco Giants sent 1B Brandon Belt on a rehab assignment to Sacramento River Cats.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 374764, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2018-08-14', 'effective_date': '2018-08-14', 'resolution_date': '2018-08-14', 'available_date': '2018-08-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 477758, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10 day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 478413, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 448529, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2020-07-30', 'effective_date': '2020-07-30', 'resolution_date': '2020-07-30', 'available_date': '2020-07-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 493518, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2021-06-08', 'effective_date': '2021-06-08', 'resolution_date': '2021-06-08', 'available_date': '2021-06-08', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 507998, 'player_id': 474832, 'available_date': '2021-07-29', 'recorded_date': '2021-07-29', 'effective_date': '2021-07-29', 'resolution_date': '2021-07-29', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'San Francisco Giants sent 1B Brandon Belt on a rehab assignment to Sacramento River Cats.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 509806, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt.', 'recorded_date': '2021-08-05', 'effective_date': '2021-08-05', 'resolution_date': '2021-08-05', 'available_date': '2021-08-05', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 514831, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the bereavement list.', 'recorded_date': '2021-08-29', 'effective_date': '2021-08-29', 'resolution_date': '2021-08-29', 'available_date': '2021-08-29', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 521187, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2021-10-07', 'effective_date': '2021-10-07', 'resolution_date': '2021-10-07', 'available_date': '2021-10-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 521828, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt.', 'recorded_date': '2021-10-15', 'effective_date': '2021-10-15', 'resolution_date': '2021-10-15', 'available_date': '2021-10-15', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 523189, 'player_id': 474832, 'available_date': '2021-11-03', 'recorded_date': '2021-11-03', 'effective_date': '2021-11-03', 'resolution_date': '2021-11-03', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 600125, 'player_id': 474832, 'available_date': '2021-11-17', 'recorded_date': '2021-11-17', 'effective_date': '2021-11-17', 'resolution_date': '2021-11-17', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'San Francisco Giants signed free agent 1B Brandon Belt.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 619854, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2022-05-07', 'effective_date': '2022-05-07', 'resolution_date': '2022-05-07', 'available_date': '2022-05-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 631072, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'San Francisco Giants activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2022-06-14', 'effective_date': '2022-06-14', 'resolution_date': '2022-06-14', 'available_date': '2022-06-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 658242, 'player_id': 474832, 'available_date': '2022-11-06', 'recorded_date': '2022-11-06', 'effective_date': '2022-11-06', 'resolution_date': '2022-11-06', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 684950, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Toronto Blue Jays activated 1B Brandon Belt.', 'recorded_date': '2023-01-10', 'effective_date': '2023-01-10', 'resolution_date': '2023-01-10', 'available_date': '2023-01-10', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 684675, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Toronto Blue Jays activated 1B Brandon Belt.', 'recorded_date': '2023-01-10', 'effective_date': '2023-01-10', 'resolution_date': '2023-01-10', 'available_date': '2023-01-10', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 664972, 'player_id': 474832, 'available_date': '2023-01-10', 'recorded_date': '2023-01-10', 'effective_date': '2023-01-10', 'resolution_date': '2023-01-10', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Toronto Blue Jays signed free agent 1B Brandon Belt.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 705797, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Toronto Blue Jays activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2023-06-21', 'effective_date': '2023-06-21', 'resolution_date': '2023-06-21', 'available_date': '2023-06-21', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 726751, 'player_id': 474832, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Toronto Blue Jays activated 1B Brandon Belt from the 10-day injured list.', 'recorded_date': '2023-09-26', 'effective_date': '2023-09-26', 'resolution_date': '2023-09-26', 'available_date': '2023-09-26', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 732859, 'player_id': 474832, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Brandon Belt elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 15 | 0 | 3 | 2 |
| 2021 | MLB | 381 | 29 | 103 | 45 |
| 2022 | MLB | 298 | 8 | 81 | 35 |
| 2023 | MLB | 404 | 19 | 141 | 60 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.646989 | 367.443 | 237.732 | 0.68649 | 1.00803 |
| preseason | 0.646312 | 377.769 | 244.156 | 0.68649 | 1.03528 |
| employment | 0.636491 | 374.847 | 238.587 | 0.68649 | 1.01166 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

PA product 0.636490680 × 374.847184258; offense yield 0.686486034/600 + 0.003096076.

Actual MLB counts: []. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 258, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 2}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 184, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 2}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 258, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 2}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 184, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 50571, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 1, 'profile_people': 23, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 3, 'quality_band': 2}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.123068; raw additive 0.602869; linked probability 0.646312.

Largest path terms (accounting, not causality):

- games_mlb_0: input 103.000000, contribution +2.580560.
- on_40man: input 0.000000, contribution -0.978755.
- games_pool_MLB: input 223.600000, contribution +0.875240.
- quality_0: input 0.648045, contribution +0.709231.
- pooled_MLB_pa: input 871.000000, contribution +0.466982.
- age_squared: input 2.560000, contribution -0.275326.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.9787546792654374}]

Saved employment participation: reference -4.119791; raw additive 0.560165; linked probability 0.636491.

Largest path terms (accounting, not causality):

- games_mlb_0: input 103.000000, contribution +2.549417.
- on_40man: input 0.000000, contribution -0.976785.
- games_pool_MLB: input 223.600000, contribution +0.769158.
- quality_0: input 0.648045, contribution +0.678585.
- pooled_MLB_pa: input 871.000000, contribution +0.423220.
- age_squared: input 2.560000, contribution -0.358092.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.976784621644687}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.21525043914680042}, {'feature': 'employment_year_fa', 'input': 1.0, 'path_effect': 0.06219288521482985}]

Same fitted candidate with the three new inputs zero: 0.628566. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 277.623139; raw additive 377.768520; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 404.000000, contribution +87.671906.
- quality_0: input 0.648045, contribution +44.240605.
- pooled_mlb_quality: input 0.969809, contribution +32.012103.
- age_centered: input 1.600000, contribution -31.061479.
- on_40man: input 0.000000, contribution -23.505989.
- pooled_MLB_K: input 0.299279, contribution -21.585037.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -23.50598879802772}]

Saved employment conditional_pa: reference 277.629089; raw additive 374.847184; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 404.000000, contribution +87.599315.
- quality_0: input 0.648045, contribution +43.974305.
- pooled_mlb_quality: input 0.969809, contribution +31.011668.
- age_centered: input 1.600000, contribution -28.623414.
- on_40man: input 0.000000, contribution -25.045117.
- pooled_MLB_K: input 0.299279, contribution -19.559370.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -25.04511669986465}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 1.2341098769349599}]

Same fitted candidate with the three new inputs zero: 370.561463. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

The same Belt had now produced 404 MLB PA, 19 HR, 141 K and 60 UBB; his November 2 free agency is known but no next-year signing is assumed. The new forecast falls from 244.156 to 238.587 expected PA (.636491 times 374.847), versus zero actual. Known/FA inputs add .21525/.06219 log-odds within the fit, yet the complete refit lowers the forecast; attribution must distinguish these. Zero-new-input mechanics yields .628566/370.561. Refined support is 23 participation and 23 active people, with Pham 245/478, Duvall 219/330, Crawford 71/80 and Martinez 303/495 as actual peers. Those successful returns make certain retirement an inappropriate hindsight rule. The 1.012 offense false high remains; no PA means no observed zero talent. The paired Belt seasons expose both workload underprediction and uncertain employment exit, not a universal roster correction.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Tommy Pham | 252.88 | 238.36 | 245.11 | 478 | 0.538 | 0.650 |
| Adam Duvall | 209.48 | 225.16 | 218.97 | 330 | 0.457 | -0.792 |
| Brandon Crawford | 77.16 | 65.69 | 70.52 | 80 | 0.028 | -0.212 |
| J.D. Martinez | 304.46 | 311.72 | 303.46 | 495 | 1.393 | 1.452 |

## Wyatt Langford / 2023 to 2024

ID 694671; row 53164; fold 4; age 21.0; Upper minors; ranking information date 2024-01-26. Selected: fixed before fit.

Employment evidence: {'row_id': 53164, 'player_id': 694671, 'origin_year': 2023, 'latest_employment_date': None, 'recorded_open_fa': -1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 0, 'employment_year_fa': 0}

Dated records at cutoff: []

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.95, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

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
| employment | 0.554102 | 352.193 | 195.150 | 0.68803 | 0.82798 |
| Actual | 1 | not a forecast | 557 | 0.07695317803827988 | 1.79595 |

PA product 0.554101614 × 352.192505232; offense yield 0.688029041/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 694671, 'bucket': 'MLB', 'plate_appearances': 557, 'strike_outs': 115, 'unintentional_walks': 48, 'hit_by_pitch': 4, 'home_runs': 16, 'babip_hits': 110, 'doubles': 25, 'triples': 4, 'babip_opportunities': 371}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 560, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 466, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 123, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 48, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 560, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 466, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 123, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 53164, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 48, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.136149; raw additive 0.401709; linked probability 0.599098.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.950000, contribution +1.300233.
- scout_listed_0: input 1.000000, contribution +1.173110.
- role_pool_AA: input 4.272727, contribution +0.920409.
- draft_rank: input 0.817615, contribution +0.443997.
- on_40man: input 0.000000, contribution -0.406939.
- pooled_AA_pa: input 54.000000, contribution +0.397450.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.40693884780043577}]

Saved employment participation: reference -4.141603; raw additive 0.217257; linked probability 0.554102.

Largest path terms (accounting, not causality):

- scout_listed_0: input 1.000000, contribution +1.198887.
- scout_rank_score_0: input 0.950000, contribution +1.172380.
- role_pool_AA: input 4.272727, contribution +0.861157.
- on_40man: input 0.000000, contribution -0.415335.
- pooled_AA_pa: input 54.000000, contribution +0.389916.
- draft_rank: input 0.817615, contribution +0.385292.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.4153353033729299}, {'feature': 'employment_year_known', 'input': 0.0, 'path_effect': -0.07037183131829068}]

Same fitted candidate with the three new inputs zero: 0.554102. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 279.203529; raw additive 358.735377; raw PA before bounds.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.950000, contribution +147.249762.
- work_0: input 0.000000, contribution -94.004712.
- role_pool_AAA: input 4.400000, contribution +34.806643.
- on_40man: input 0.000000, contribution -19.537854.
- role_pool_AA: input 4.272727, contribution +15.145308.
- regular_window_scaled: input 0.000000, contribution -10.037675.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -19.53785366020845}]

Saved employment conditional_pa: reference 279.204489; raw additive 352.192505; raw PA before bounds.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.950000, contribution +147.565264.
- work_0: input 0.000000, contribution -94.004712.
- role_pool_AAA: input 4.400000, contribution +34.955885.
- on_40man: input 0.000000, contribution -19.537854.
- role_pool_AA: input 4.272727, contribution +15.130375.
- regular_window_scaled: input 0.000000, contribution -10.037675.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -19.53785366020845}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': -2.078199801064473}]

Same fitted candidate with the three new inputs zero: 358.711563. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Langford had 200 professional PA across rookie/A-plus/AA/AAA, ten HR, 34 K and 36 UBB, age 21, fourth pick and preseason rank six. His three new employment inputs are 1/0/0: covered capture era but no current classified employment event, not a missing contract interpreted as zero talent. Candidate participation falls .599098 to .554102, conditional PA 358.735 to 352.193, and expected PA 214.918 to 195.150 versus 557 actual. A known-current-zero path subtracts .07037 log-odds and capture scope subtracts 2.07820 conditional PA; zero-new-input mechanics leaves chance identical and raises conditional PA to 358.712. Broad/refined new status counts 560/466 participation and 123/48 active people do not establish elite new-draftee support. Veen 16/0, Crews 35/132, Shaw 88/0 and Wilken 3/0 remain peers. Fresh ranking still improves substantially over original 43 PA, but this employment refit harms this clear readiness miss. Fixed hitting .6880 versus .0770 partly offsets workload; offense .828 versus 1.796 does not certify his talent forecast.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Zac Veen | 85.17 | 15.77 | 16.03 | 0 | 0.045 | 0.000 |
| Dylan Crews | 12.55 | 49.67 | 34.81 | 132 | 0.112 | 0.025 |
| Matt Shaw | 34.13 | 101.43 | 87.56 | 0 | 0.239 | 0.000 |
| Brock Wilken | 6.42 | 3.92 | 2.75 | 0 | 0.010 | 0.000 |

## Nick Kurtz / 2024 to 2025

ID 701762; row 57052; fold 2; age 21.0; Upper minors; ranking information date 2025-01-24. Selected: fixed before fit.

Employment evidence: {'row_id': 57052, 'player_id': 701762, 'origin_year': 2024, 'latest_employment_date': None, 'recorded_open_fa': -1, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 0, 'employment_year_fa': 0}

Dated records at cutoff: []

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.63, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.017252 | 115.973 | 2.001 | -0.06322 | 0.00604 |
| preseason | 0.060561 | 168.160 | 10.184 | -0.06322 | 0.03073 |
| employment | 0.058430 | 169.927 | 9.929 | -0.06322 | 0.02996 |
| Actual | 1 | not a forecast | 489 | 5.289191738139299 | 5.83778 |

PA product 0.058430337 × 169.926961410; offense yield -0.063222554/600 + 0.003122875.

Actual MLB counts: [{'season': 2025, 'player_id': 701762, 'bucket': 'MLB', 'plate_appearances': 489, 'strike_outs': 151, 'unintentional_walks': 60, 'hit_by_pitch': 2, 'home_runs': 36, 'babip_hits': 86, 'doubles': 26, 'triples': 2, 'babip_opportunities': 236}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 610, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 503, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 131, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 47, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 610, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 503, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 131, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 1, 'employment_year_known': 0, 'employment_year_fa': 0, 'profile_people': 47, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 0, 'work_band': 0, 'quality_band': -1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.096228; raw additive -2.741629; linked probability 0.060561.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.630000, contribution +1.243941.
- draft_rank: input 0.817615, contribution +0.450012.
- scout_listed_0: input 1.000000, contribution +0.396579.
- on_40man: input 0.000000, contribution -0.334185.
- games_mlb_0: input 0.000000, contribution -0.202625.
- games_pool_MLB: input 0.000000, contribution -0.198036.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.33418498329981394}]

Saved employment participation: reference -4.091086; raw additive -2.779713; linked probability 0.058430.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.630000, contribution +1.267942.
- scout_listed_0: input 1.000000, contribution +0.490775.
- draft_rank: input 0.817615, contribution +0.419090.
- on_40man: input 0.000000, contribution -0.339330.
- games_mlb_0: input 0.000000, contribution -0.201414.
- games_pool_MLB: input 0.000000, contribution -0.190798.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -0.3393302381631716}, {'feature': 'employment_year_known', 'input': 0.0, 'path_effect': -0.031029508836065426}]

Same fitted candidate with the three new inputs zero: 0.058430. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 278.554971; raw additive 168.160355; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 0.000000, contribution -99.719816.
- scout_rank_score_0: input 0.630000, contribution +71.234719.
- on_40man: input 0.000000, contribution -22.649740.
- quality_0: input 0.000000, contribution -12.276285.
- regular_window_scaled: input 0.000000, contribution -11.785065.
- role_pool_AAA: input 4.000000, contribution -9.248723.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -22.649740266203256}]

Saved employment conditional_pa: reference 278.544522; raw additive 169.926961; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 0.000000, contribution -99.859400.
- scout_rank_score_0: input 0.630000, contribution +71.154936.
- on_40man: input 0.000000, contribution -22.649740.
- quality_0: input 0.000000, contribution -12.264887.
- regular_window_scaled: input 0.000000, contribution -11.785065.
- role_pool_AAA: input 4.000000, contribution -9.186217.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 0.0, 'path_effect': -22.649740266203256}, {'feature': 'employment_year_known', 'input': 0.0, 'path_effect': -0.22356928535449586}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 0.13625595812217517}]

Same fitted candidate with the three new inputs zero: 169.506464. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Kurtz has exactly 50 pro PA, four HR, ten K and twelve UBB at A/AA, age 21 and fourth overall pick, with preseason rank 38. No classified employment event means covered-but-unknown 1/0/0, not unsigned or no investment. New .058430 times 169.927 gives 9.929 PA versus 489, nearly the same as fresher-list 10.184 and original two. Current rank/draft paths add 1.26794/.41909 log-odds but known-current-zero subtracts .03103; work_0 remains -99.85940 conditional PA. Zero-new-input mechanics leaves chance unchanged and conditional PA 169.506. Refined status support 503 participation/47 active people is a broad source-status/workload group, not comparable elite college stars. Montgomery 5/0 and Williams 109/0 fail while Moore 17/184 and Cam Smith 11/493 show other rapid arrivals being missed. The near-average fixed hitting -.0632 versus actual 5.2892 is an independent talent miss. Employment data does not remedy the readiness or talent extrapolation.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benny Montgomery | 6.54 | 5.41 | 5.27 | 0 | 0.015 | 0.000 |
| Christian Moore | 8.23 | 22.35 | 17.21 | 184 | 0.053 | 0.242 |
| Cam Smith | 2.33 | 9.98 | 10.93 | 493 | 0.030 | 1.131 |
| Jett Williams | 74.66 | 100.55 | 109.12 | 0 | 0.320 | 0.000 |

## Shohei Ohtani / 2023 to 2024

ID 660271; row 51141; fold 1; age 28.0; Current MLB; ranking information date 2024-01-26. Selected: largest offense gain.

Employment evidence: {'row_id': 51141, 'player_id': 660271, 'origin_year': 2023, 'latest_employment_date': '2023-12-11', 'recorded_open_fa': 0, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 0}

Dated records at cutoff: [{'transaction_id': 338507, 'player_id': 660271, 'available_date': '2017-12-09', 'recorded_date': '2017-12-09', 'effective_date': '2017-12-09', 'resolution_date': '2017-12-09', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Los Angeles Angels signed free agent RHP Shohei Ohtani to a minor league contract.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 341188, 'player_id': 660271, 'available_date': '2018-02-06', 'recorded_date': '2018-02-06', 'effective_date': '2018-02-06', 'resolution_date': '2018-02-06', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Los Angeles Angels invited non-roster RHP Shohei Ohtani to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 365990, 'player_id': 660271, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Los Angeles Angels activated RHP Shohei Ohtani from the 10-day injured list.', 'recorded_date': '2018-07-03', 'effective_date': '2018-07-03', 'resolution_date': '2018-07-03', 'available_date': '2018-07-03', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 400224, 'player_id': 660271, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Los Angeles Angels activated RHP Shohei Ohtani from the 10-day injured list.', 'recorded_date': '2019-05-07', 'effective_date': '2019-05-07', 'resolution_date': '2019-05-07', 'available_date': '2019-05-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 636120, 'player_id': 660271, 'available_date': '2022-07-18', 'recorded_date': '2022-07-18', 'effective_date': '2022-07-18', 'resolution_date': '2022-07-18', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'RHP Shohei Ohtani assigned to American League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 707216, 'player_id': 660271, 'available_date': '2023-07-10', 'recorded_date': '2023-07-10', 'effective_date': '2023-07-10', 'resolution_date': '2023-07-10', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'RHP Shohei Ohtani assigned to American League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 727386, 'player_id': 660271, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Los Angeles Angels activated RHP Shohei Ohtani from the 15-day injured list.', 'recorded_date': '2023-10-02', 'effective_date': '2023-10-02', 'resolution_date': '2023-10-02', 'available_date': '2023-10-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 730303, 'player_id': 660271, 'available_date': '2023-11-02', 'recorded_date': '2023-11-02', 'effective_date': '2023-11-02', 'resolution_date': '2023-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': 'RHP Shohei Ohtani elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 734907, 'player_id': 660271, 'available_date': '2023-12-11', 'recorded_date': '2023-12-11', 'effective_date': '2023-12-11', 'resolution_date': '2023-12-11', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Los Angeles Dodgers signed free agent RHP Shohei Ohtani.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 639 | 46 | 189 | 76 |
| 2022 | MLB | 666 | 34 | 161 | 58 |
| 2023 | MLB | 599 | 44 | 143 | 70 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.992309 | 569.110 | 564.733 | 3.04407 | 4.61360 |
| preseason | 0.993124 | 573.830 | 569.884 | 3.04407 | 4.65569 |
| employment | 0.992881 | 584.782 | 580.619 | 3.04407 | 4.74338 |
| Actual | 1 | not a forecast | 731 | 5.139099719765811 | 8.52437 |

PA product 0.992881275 × 584.781622234; offense yield 3.044074159/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 660271, 'bucket': 'MLB', 'plate_appearances': 731, 'strike_outs': 162, 'unintentional_walks': 71, 'hit_by_pitch': 6, 'home_runs': 54, 'babip_hits': 143, 'doubles': 38, 'triples': 7, 'babip_opportunities': 425}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 780, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 108, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 2}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 587, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 108, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 2}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 780, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 108, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 2}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 587, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51141, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 108, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 2}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.033199; raw additive 4.972795; linked probability 0.993124.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.656175.
- games_mlb_0: input 135.000000, contribution +2.043219.
- work_0: input 599.000000, contribution +1.073586.
- quality_0: input 1.629409, contribution +0.693065.
- games_pool_MLB: input 355.400000, contribution +0.661340.
- pooled_MLB_pa: input 1515.200000, contribution +0.384355.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.6561752518986426}]

Saved employment participation: reference -4.061106; raw additive 4.937882; linked probability 0.992881.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.645562.
- games_mlb_0: input 135.000000, contribution +1.918100.
- work_0: input 599.000000, contribution +1.061713.
- games_pool_MLB: input 355.400000, contribution +0.681913.
- quality_0: input 1.629409, contribution +0.678150.
- pooled_MLB_pa: input 1515.200000, contribution +0.413452.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.645562099613123}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.09989972902823757}]

Same fitted candidate with the three new inputs zero: 0.992860. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 283.910666; raw additive 573.830216; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 599.000000, contribution +133.035293.
- quality_0: input 1.629409, contribution +35.472642.
- role_pool_MLB: input 4.256158, contribution +29.152611.
- role_mlb_0: input 4.406897, contribution +24.889539.
- games_mlb_2: input 158.000000, contribution +16.844027.
- pooled_MLB_K: input 0.252724, contribution -14.797183.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.5052419206709544}]

Saved employment conditional_pa: reference 283.915500; raw additive 584.781622; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 599.000000, contribution +134.350528.
- quality_0: input 1.629409, contribution +35.574105.
- role_pool_MLB: input 4.256158, contribution +29.153228.
- role_mlb_0: input 4.406897, contribution +24.694929.
- games_mlb_2: input 158.000000, contribution +15.842645.
- pooled_MLB_K: input 0.252724, contribution -14.717255.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.5051665542940222}, {'feature': 'employment_year_fa', 'input': 0.0, 'path_effect': 0.15901085674374013}]

Same fitted candidate with the three new inputs zero: 584.781622. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Ohtani is the ordered largest offense gain, not a validation set chosen to flatter the model. He had 639/666/599 MLB PA and 46/34/44 HR; his November free agency is superseded by the December 11 Dodgers signing, correctly current attached 1/1/0 and roster one. New .992881 times 584.782 gives 580.619 PA versus 731, up eleven from 569.884. The known-current path adds .09990 log-odds, but zero-new-input mechanics leaves conditional PA exactly 584.782 and changes probability by only .000021. Most of the gain therefore comes from shared refitting, not a direct contract term. Refined support is 108 participation/108 active people. Suzuki 530/585, Arozarena 562/648, Santander 547/665 and Arcia 424/602 show mixed offense outcomes. Fixed hitting 3.0441 versus actual 5.1391 leaves offense 4.743 versus 8.524 even after the gain. This single largest gain cannot justify general promotion.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seiya Suzuki | 528.91 | 530.65 | 530.15 | 585 | 2.265 | 3.999 |
| Randy Arozarena | 553.86 | 557.19 | 561.89 | 648 | 2.945 | 2.161 |
| Anthony Santander | 547.72 | 545.63 | 546.77 | 665 | 2.541 | 3.394 |
| Orlando Arcia | 416.85 | 421.25 | 423.74 | 602 | 0.958 | -0.443 |

## Yordan Alvarez / 2024 to 2025

ID 670541; row 55521; fold 2; age 27.0; Current MLB; ranking information date 2025-01-24. Selected: largest offense harm.

Employment evidence: {'row_id': 55521, 'player_id': 670541, 'origin_year': 2024, 'latest_employment_date': '2024-07-03', 'recorded_open_fa': 0, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 0}

Dated records at cutoff: [{'transaction_id': 281262, 'player_id': 670541, 'available_date': '2016-07-15', 'recorded_date': '2016-07-15', 'effective_date': '2016-07-15', 'resolution_date': '2016-07-15', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Los Angeles Dodgers signed free agent Yordan Alvarez.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 281618, 'player_id': 670541, 'available_date': '2016-08-01', 'recorded_date': '2016-08-01', 'effective_date': '2016-08-01', 'resolution_date': None, 'status': 'attached', 'type_code': 'TR', 'type_description': 'Trade', 'description': 'Houston Astros traded RHP Josh Fields to Los Angeles Dodgers for 1B Yordan Alvarez.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 342813, 'player_id': 670541, 'available_date': '2018-02-25', 'recorded_date': '2018-02-25', 'effective_date': '2018-02-25', 'resolution_date': '2018-02-25', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'OF Yordan Alvarez assigned to Houston Astros.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 386503, 'player_id': 670541, 'available_date': '2019-01-22', 'recorded_date': '2019-01-22', 'effective_date': '2019-01-22', 'resolution_date': '2019-01-22', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Houston Astros invited non-roster LF Yordan Alvarez to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 449353, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated OF Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2020-08-14', 'effective_date': '2020-08-14', 'resolution_date': '2020-08-14', 'available_date': '2020-08-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 455147, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated OF Yordan Alvarez from the 60-day injured list.', 'recorded_date': '2020-11-02', 'effective_date': '2020-11-02', 'resolution_date': '2020-11-02', 'available_date': '2020-11-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 478982, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2021-04-20', 'effective_date': '2021-04-20', 'resolution_date': '2021-04-20', 'available_date': '2021-04-20', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 481543, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2021-04-30', 'effective_date': '2021-04-30', 'resolution_date': '2021-04-30', 'available_date': '2021-04-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 488618, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2021-04-30', 'effective_date': '2021-04-30', 'resolution_date': '2021-04-30', 'available_date': '2021-04-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 489457, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2021-04-30', 'effective_date': '2021-04-30', 'resolution_date': '2021-04-30', 'available_date': '2021-04-30', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 501181, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the paternity list.', 'recorded_date': '2021-07-05', 'effective_date': '2021-07-05', 'resolution_date': '2021-07-05', 'available_date': '2021-07-05', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 615738, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2022-04-18', 'effective_date': '2022-04-18', 'resolution_date': '2022-04-18', 'available_date': '2022-04-18', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 636457, 'player_id': 670541, 'available_date': '2022-07-18', 'recorded_date': '2022-07-18', 'effective_date': '2022-07-18', 'resolution_date': '2022-07-18', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': '1B Yordan Alvarez assigned to American League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 638729, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the reserve list.', 'recorded_date': '2022-07-21', 'effective_date': '2022-07-21', 'resolution_date': '2022-07-21', 'available_date': '2022-07-21', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 708526, 'player_id': 670541, 'available_date': '2023-07-10', 'recorded_date': '2023-07-10', 'effective_date': '2023-07-10', 'resolution_date': '2023-07-10', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': '1B Yordan Alvarez assigned to American League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 710748, 'player_id': 670541, 'available_date': '2023-07-14', 'recorded_date': '2023-07-14', 'effective_date': '2023-07-14', 'resolution_date': '2023-07-14', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Houston Astros sent 1B Yordan Alvarez on a rehab assignment to Sugar Land Space Cowboys.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 714728, 'player_id': 670541, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Houston Astros activated 1B Yordan Alvarez from the 10-day injured list.', 'recorded_date': '2023-07-26', 'effective_date': '2023-07-26', 'resolution_date': '2023-07-26', 'available_date': '2023-07-26', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 784867, 'player_id': 670541, 'available_date': '2024-07-03', 'recorded_date': '2024-07-03', 'effective_date': '2024-07-03', 'resolution_date': '2024-07-03', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': '1B Yordan Alvarez assigned to American League All-Stars.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.988559 | 560.015 | 553.608 | 3.74634 | 5.18552 |
| preseason | 0.988567 | 552.864 | 546.544 | 3.74634 | 5.11935 |
| employment | 0.988658 | 562.010 | 555.636 | 3.74634 | 5.20451 |
| Actual | 1 | not a forecast | 199 | 1.0588306908518377 | 0.97263 |

PA product 0.988657654 × 562.010116181; offense yield 3.746337990/600 + 0.003122875.

Actual MLB counts: [{'season': 2025, 'player_id': 670541, 'bucket': 'MLB', 'plate_appearances': 199, 'strike_outs': 33, 'unintentional_walks': 23, 'hit_by_pitch': 0, 'home_runs': 6, 'babip_hits': 39, 'doubles': 8, 'triples': 0, 'babip_opportunities': 132}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 839, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 64, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 4, 'quality_band': 2}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 622, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 64, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 4, 'quality_band': 2}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 839, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 64, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 4, 'quality_band': 2}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 622, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 64, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 4, 'quality_band': 2}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.096228; raw additive 4.459745; linked probability 0.988567.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.686501.
- games_mlb_0: input 147.000000, contribution +1.862568.
- work_0: input 635.261424, contribution +1.037008.
- games_pool_MLB: input 319.200000, contribution +0.941999.
- pooled_mlb_quality: input 2.457089, contribution +0.523077.
- quality_0: input 1.415653, contribution +0.407799.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.686501251687748}]

Saved employment participation: reference -4.091086; raw additive 4.467805; linked probability 0.988658.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.729470.
- games_mlb_0: input 147.000000, contribution +1.858688.
- work_0: input 635.261424, contribution +1.070198.
- games_pool_MLB: input 319.200000, contribution +0.891654.
- pooled_mlb_quality: input 2.457089, contribution +0.539545.
- quality_0: input 1.415653, contribution +0.435935.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.7294702962960278}]

Same fitted candidate with the three new inputs zero: 0.988658. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 278.554971; raw additive 552.864456; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 635.261424, contribution +148.508722.
- role_mlb_0: input 4.299363, contribution +28.108364.
- quality_0: input 1.415653, contribution +27.993901.
- role_pool_MLB: input 4.278250, contribution +25.774149.
- MLB_0_pa: input 635.000000, contribution +17.556846.
- regular_window_scaled: input 1.000000, contribution +15.741798.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 1.9953678975235971}]

Saved employment conditional_pa: reference 278.544522; raw additive 562.010116; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 635.261424, contribution +148.752543.
- role_mlb_0: input 4.299363, contribution +28.098353.
- quality_0: input 1.415653, contribution +28.005299.
- role_pool_MLB: input 4.278250, contribution +25.710003.
- MLB_0_pa: input 635.000000, contribution +16.979200.
- regular_window_scaled: input 1.000000, contribution +15.741798.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 1.9953678975235971}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.23782882975068237}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 0.13625595812217517}]

Same fitted candidate with the three new inputs zero: 561.128221. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Alvarez is the ordered largest offense harm: 561/496/635 prior MLB PA with 37/31/35 HR support a high talent forecast, but next year he supplies 199 PA and .973 offense. Latest current assignment is to the American League All-Stars, not a new club contract. The broad adapter records it as attachment; that source semantics weakness must be stated rather than treating known-current as guaranteed employment. Candidate .988658 times 562.010 yields 555.636 PA versus fresh-list 546.544; fixed hitting remains 3.7463 versus observed 1.0588, so offense rises 5.119 to 5.205 and worsens the miss. Employment known/capture terms add only .23783/.13626 PA; zero-new-input conditional is 561.128, showing most of the nine-PA change is shared refit. Refined support 64/64 does not predict a specific future absence. Castro 488/454 and Torres 588/628 return, De La Cruz 465/50 disappoints, Devers 556/729 exceeds. Do not invent a post-cutoff health signal; do not promote this source interpretation as contracts.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Willi Castro | 496.45 | 491.39 | 488.28 | 454 | 1.231 | 1.128 |
| Bryan De La Cruz | 469.91 | 465.90 | 464.63 | 50 | 1.124 | -0.257 |
| Gleyber Torres | 583.55 | 587.46 | 588.33 | 628 | 2.446 | 3.220 |
| Rafael Devers | 553.89 | 560.32 | 555.99 | 729 | 3.408 | 5.408 |

## Chris Davis / 2017 to 2018

ID 448801; row 27537; fold 3; age 31.0; Current MLB; ranking information date 2018-01-27. Selected: major false high.

Employment evidence: {'row_id': 27537, 'player_id': 448801, 'origin_year': 2017, 'latest_employment_date': '2017-07-14', 'recorded_open_fa': 0, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 0}

Dated records at cutoff: [{'transaction_id': 221023, 'player_id': 448801, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Baltimore Orioles activated 1B Chris Davis from the restricted list.', 'recorded_date': '2015-04-07', 'effective_date': '2015-04-07', 'resolution_date': '2015-04-07', 'available_date': '2015-04-07', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 248549, 'player_id': 448801, 'available_date': '2015-11-02', 'recorded_date': '2015-11-02', 'effective_date': '2015-11-02', 'resolution_date': '2015-11-02', 'status': 'free_agent', 'type_code': 'DFA', 'type_description': 'Declared Free Agency', 'description': '1B Chris Davis elected free agency.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 253661, 'player_id': 448801, 'available_date': '2016-01-21', 'recorded_date': '2016-01-21', 'effective_date': '2016-01-21', 'resolution_date': '2016-01-21', 'status': 'attached', 'type_code': 'SFA', 'type_description': 'Signed as Free Agent', 'description': 'Baltimore Orioles signed free agent 1B Chris Davis.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 323778, 'player_id': 448801, 'available_date': '2017-07-10', 'recorded_date': '2017-07-10', 'effective_date': '2017-07-10', 'resolution_date': '2017-07-10', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Baltimore Orioles sent 1B Chris Davis on a rehab assignment to Frederick Keys.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 323306, 'player_id': 448801, 'available_date': '2017-07-10', 'recorded_date': '2017-07-10', 'effective_date': '2017-07-10', 'resolution_date': '2017-07-10', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Baltimore Orioles sent 1B Chris Davis on a rehab assignment to Frederick Keys.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 323779, 'player_id': 448801, 'available_date': '2017-07-12', 'recorded_date': '2017-07-12', 'effective_date': '2017-07-12', 'resolution_date': '2017-07-12', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Baltimore Orioles sent 1B Chris Davis on a rehab assignment to Delmarva Shorebirds.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 324155, 'player_id': 448801, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'Baltimore Orioles activated 1B Chris Davis from the 10-day injured list.', 'recorded_date': '2017-07-14', 'effective_date': '2017-07-14', 'resolution_date': '2017-07-14', 'available_date': '2017-07-14', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

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
| employment | 0.976234 | 511.111 | 498.964 | 1.08164 | 2.43440 |
| Actual | 1 | not a forecast | 522 | -4.101755833580411 | -1.96276 |

PA product 0.976234337 × 511.111010190; offense yield 1.081635642/600 + 0.003076176.

Actual MLB counts: [{'season': 2018, 'player_id': 448801, 'bucket': 'MLB', 'plate_appearances': 522, 'strike_outs': 192, 'unintentional_walks': 39, 'hit_by_pitch': 7, 'home_runs': 16, 'babip_hits': 63, 'doubles': 12, 'triples': 0, 'babip_opportunities': 266}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 321, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 29, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 1}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 242, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 29, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 1}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 321, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 29, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 1}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 242, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 27537, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 3, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 29, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 3, 'quality_band': 1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.135062; raw additive 3.666721; linked probability 0.975077.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +3.289472.
- games_mlb_0: input 128.000000, contribution +1.553995.
- MLB_0_pa: input 524.000000, contribution +0.771305.
- games_pool_MLB: input 349.600000, contribution +0.641813.
- pooled_MLB_pa: input 1458.000000, contribution +0.399849.
- work_0: input 524.000000, contribution +0.367452.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 3.289471786114171}]

Saved employment participation: reference -4.133739; raw additive 3.715461; linked probability 0.976234.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +3.301892.
- games_mlb_0: input 128.000000, contribution +1.573087.
- MLB_0_pa: input 524.000000, contribution +0.759401.
- games_pool_MLB: input 349.600000, contribution +0.620788.
- pooled_MLB_pa: input 1458.000000, contribution +0.427326.
- work_0: input 524.000000, contribution +0.367452.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 3.301892044261316}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.05259567979193432}]

Same fitted candidate with the three new inputs zero: 0.974851. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 278.199728; raw additive 515.522980; raw PA before bounds.

Largest path terms (accounting, not causality):

- MLB_0_pa: input 524.000000, contribution +81.982997.
- role_pool_MLB: input 4.165740, contribution +33.611574.
- role_mlb_0: input 4.086957, contribution +30.084716.
- work_0: input 524.000000, contribution +27.346201.
- pooled_MLB_pa: input 1458.000000, contribution +21.943456.
- quality_0: input -0.119313, contribution -21.090887.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 4.3933587514706005}]

Saved employment conditional_pa: reference 278.208242; raw additive 511.111010; raw PA before bounds.

Largest path terms (accounting, not causality):

- MLB_0_pa: input 524.000000, contribution +80.333878.
- role_pool_MLB: input 4.165740, contribution +33.630620.
- role_mlb_0: input 4.086957, contribution +30.085241.
- work_0: input 524.000000, contribution +27.081650.
- pooled_MLB_pa: input 1458.000000, contribution +21.558382.
- quality_0: input -0.119313, contribution -21.343286.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 4.3933587514706005}, {'feature': 'employment_capture_scope', 'input': 1.0, 'path_effect': 1.0374792226803797}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.9559621434395739}]

Same fitted candidate with the three new inputs zero: 508.475001. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Davis is the major false high. He had 670/665/524 MLB PA, 47/38/26 HR and 208/219/195 K, with small current rehab counts and a July 14 activation. Current known attachment and roster one are observed, not new future-contract information. Candidate .976234 times 511.111 gives 498.964 PA versus 522, a plausible workload even though slightly lower than 502.675. Known-current adds .05260 log-odds; known/capture add .95596/1.03748 PA, while zero-new-input mechanics is .974851/508.475. Refined support 29/29 exists. Cozart 491/253 and Donaldson 592/219 demonstrate workload risk; Turner 464/426 and Thames 443/278 retain ordinary comparisons. The real failure is fixed hitting +1.0816 versus -4.1018 observed, yielding +2.434 offense versus -1.963. Calling this an employment error would misdiagnose the reversal.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Zack Cozart | 484.38 | 487.95 | 490.56 | 253 | 1.858 | 0.133 |
| Josh Donaldson | 598.64 | 592.35 | 592.10 | 219 | 4.726 | 1.067 |
| Justin Turner | 477.27 | 468.59 | 463.76 | 426 | 2.743 | 3.909 |
| Eric Thames | 447.17 | 444.35 | 443.49 | 278 | 1.712 | 0.949 |

## Aaron Judge / 2016 to 2017

ID 592450; row 23934; fold 3; age 24.0; Current MLB; ranking information date 2017-01-28. Selected: major false low.

Employment evidence: {'row_id': 23934, 'player_id': 592450, 'origin_year': 2016, 'latest_employment_date': '2016-10-03', 'recorded_open_fa': 0, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 0}

Dated records at cutoff: [{'transaction_id': 215143, 'player_id': 592450, 'available_date': '2015-02-05', 'recorded_date': '2015-02-05', 'effective_date': '2015-02-05', 'resolution_date': '2015-02-05', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees invited non-roster RF Aaron Judge to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 254592, 'player_id': 592450, 'available_date': '2016-02-05', 'recorded_date': '2016-02-05', 'effective_date': '2016-02-05', 'resolution_date': '2016-02-05', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees invited non-roster RF Aaron Judge to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 288483, 'player_id': 592450, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated RF Aaron Judge from the 15-day disabled list.', 'recorded_date': '2016-10-03', 'effective_date': '2016-10-03', 'resolution_date': '2016-10-03', 'available_date': '2016-10-03', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.56, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.7, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.33}

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
| employment | 0.924997 | 335.052 | 309.922 | -0.03966 | 0.93580 |
| Actual | 1 | not a forecast | 678 | 5.557415626157027 | 8.37188 |

PA product 0.924996978 × 335.052386027; offense yield -0.039659855/600 + 0.003085550.

Actual MLB counts: [{'season': 2017, 'player_id': 592450, 'bucket': 'MLB', 'plate_appearances': 678, 'strike_outs': 208, 'unintentional_walks': 116, 'hit_by_pitch': 5, 'home_runs': 52, 'babip_hits': 102, 'doubles': 24, 'triples': 3, 'babip_opportunities': 286}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 68, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 32, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 1}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 57, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 24, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 1}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 68, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 32, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 1}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 57, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 24, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 1}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.078610; raw additive 2.512262; linked probability 0.924997.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +3.132957.
- games_mlb_0: input 27.000000, contribution +1.060688.
- scout_rank_score_0: input 0.560000, contribution +0.657869.
- games_pool_MLB: input 27.000000, contribution +0.564445.
- MLB_0_pa: input 95.000000, contribution +0.347969.
- pooled_MLB_pa: input 95.000000, contribution -0.277269.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 3.1329570412726437}]

Saved employment participation: reference -4.078610; raw additive 2.512262; linked probability 0.924997.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +3.132957.
- games_mlb_0: input 27.000000, contribution +1.060688.
- scout_rank_score_0: input 0.560000, contribution +0.657869.
- games_pool_MLB: input 27.000000, contribution +0.564445.
- MLB_0_pa: input 95.000000, contribution +0.347969.
- pooled_MLB_pa: input 95.000000, contribution -0.277269.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 3.1329570412726437}]

Same fitted candidate with the three new inputs zero: 0.924997. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 276.994851; raw additive 335.052386; raw PA before bounds.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.560000, contribution +97.387567.
- scout_rank_score_1: input 0.700000, contribution +60.368168.
- MLB_0_pa: input 95.000000, contribution -53.874968.
- pooled_MLB_K: input 0.333333, contribution -28.556320.
- work_0: input 95.078254, contribution -20.955822.
- role_pool_AAA: input 4.334651, contribution +14.167469.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 8.400217132560064}]

Saved employment conditional_pa: reference 276.994851; raw additive 335.052386; raw PA before bounds.

Largest path terms (accounting, not causality):

- scout_rank_score_0: input 0.560000, contribution +97.387567.
- scout_rank_score_1: input 0.700000, contribution +60.368168.
- MLB_0_pa: input 95.000000, contribution -53.874968.
- pooled_MLB_K: input 0.333333, contribution -28.556320.
- work_0: input 95.078254, contribution -20.955822.
- role_pool_AAA: input 4.334651, contribution +14.167469.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 8.400217132560064}]

Same fitted candidate with the three new inputs zero: 335.052386. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Judge is the major false low. Raw three-year progression includes 2016 AAA 410 PA/19 HR/98 K/47 UBB and his 95-PA MLB debut with four HR and 42 K; the earlier A/AA/AAA production is retained. His October activation establishes known attachment and roster one. Earliest employment fit has no new own paths: both saved heads and zero-new-input probe are identical to the fresher-list .924997/335.052, giving 309.922 PA versus 678. Participation is already high; workload and near-average fixed talent -.0397 versus +5.5574 are the major gaps. Ranking paths add 97.38757/60.36817 conditional PA but debut PA and pooled K paths subtract 53.87497/28.55632. Refined employment support is 32 participation/24 active people, not none. Cowart 128/117, Pinder 143/309, Jones 81/154 and Gose 176/0 preserve failure risk rather than granting every debut star a full season. Offense .936 versus 8.372 remains extreme; these new source flags cannot solve it.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kaleb Cowart | 135.24 | 136.35 | 128.05 | 117 | 0.201 | 0.168 |
| Chad Pinder | 162.21 | 147.78 | 143.26 | 309 | 0.229 | 1.012 |
| JaCoby Jones | 69.81 | 82.82 | 81.37 | 154 | 0.192 | -0.616 |
| Anthony Gose | 182.42 | 176.42 | 176.30 | 0 | 0.437 | 0.000 |

## Ben Rortvedt / 2023 to 2024

ID 666163; row 51344; fold 1; age 25.0; Current MLB; ranking information date 2024-01-26. Selected: ordinary active.

Employment evidence: {'row_id': 51344, 'player_id': 666163, 'origin_year': 2023, 'latest_employment_date': '2023-05-11', 'recorded_open_fa': 0, 'fa_roster_conflict': 0, 'employment_capture_scope': 1, 'employment_year_known': 1, 'employment_year_fa': 0}

Dated records at cutoff: [{'transaction_id': 343894, 'player_id': 666163, 'available_date': '2018-03-12', 'recorded_date': '2018-03-12', 'effective_date': '2018-03-12', 'resolution_date': '2018-03-12', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'C Ben Rortvedt assigned to Minnesota Twins.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 387754, 'player_id': 666163, 'available_date': '2019-02-09', 'recorded_date': '2019-02-09', 'effective_date': '2019-02-09', 'resolution_date': '2019-02-09', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Minnesota Twins invited non-roster C Ben Rortvedt to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 437774, 'player_id': 666163, 'available_date': '2020-02-03', 'recorded_date': '2020-02-03', 'effective_date': '2020-02-03', 'resolution_date': '2020-02-03', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'Minnesota Twins invited non-roster C Ben Rortvedt to spring training.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 605978, 'player_id': 666163, 'available_date': '2022-03-13', 'recorded_date': '2022-03-13', 'effective_date': None, 'resolution_date': None, 'status': 'attached', 'type_code': 'TR', 'type_description': 'Trade', 'description': 'New York Yankees traded C Gary Sanchez and 3B Gio Urshela to Minnesota Twins for 3B Josh Donaldson, 3B Isiah Kiner-Falefa and C Ben Rortvedt.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 619800, 'player_id': 666163, 'available_date': '2022-05-07', 'recorded_date': '2022-05-07', 'effective_date': '2022-05-07', 'resolution_date': '2022-05-07', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Tampa Tarpons.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 636762, 'player_id': 666163, 'available_date': '2022-07-12', 'recorded_date': '2022-07-12', 'effective_date': '2022-07-12', 'resolution_date': '2022-07-12', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Hudson Valley Renegades.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 636766, 'player_id': 666163, 'available_date': '2022-07-12', 'recorded_date': '2022-07-12', 'effective_date': '2022-07-12', 'resolution_date': '2022-07-12', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Hudson Valley Renegades.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 639056, 'player_id': 666163, 'available_date': '2022-07-12', 'recorded_date': '2022-07-12', 'effective_date': '2022-07-12', 'resolution_date': '2022-07-12', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Hudson Valley Renegades.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 639183, 'player_id': 666163, 'available_date': '2022-07-22', 'recorded_date': '2022-07-22', 'effective_date': '2022-07-22', 'resolution_date': '2022-07-22', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Scranton/Wilkes-Barre RailRiders.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 639057, 'player_id': 666163, 'available_date': '2022-07-22', 'recorded_date': '2022-07-22', 'effective_date': '2022-07-22', 'resolution_date': '2022-07-22', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Scranton/Wilkes-Barre RailRiders.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 642541, 'player_id': 666163, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated C Ben Rortvedt from the 60-day injured list.', 'recorded_date': '2022-08-02', 'effective_date': '2022-08-02', 'resolution_date': '2022-08-02', 'available_date': '2022-08-02', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 657361, 'player_id': 666163, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated C Ben Rortvedt.', 'recorded_date': '2022-10-24', 'effective_date': '2022-10-24', 'resolution_date': '2022-10-24', 'available_date': '2022-10-24', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 686330, 'player_id': 666163, 'available_date': '2023-04-21', 'recorded_date': '2023-04-21', 'effective_date': '2023-04-21', 'resolution_date': '2023-04-21', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Benjamin Rortvedt on a rehab assignment to Tampa Tarpons.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 688430, 'player_id': 666163, 'available_date': '2023-05-02', 'recorded_date': '2023-05-02', 'effective_date': '2023-05-02', 'resolution_date': '2023-05-02', 'status': 'attached', 'type_code': 'ASG', 'type_description': 'Assigned', 'description': 'New York Yankees sent C Ben Rortvedt on a rehab assignment to Scranton/Wilkes-Barre RailRiders.', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}, {'transaction_id': 691216, 'player_id': 666163, 'status': 'attached', 'type_code': 'SC', 'type_description': 'Status Change', 'description': 'New York Yankees activated C Ben Rortvedt from the 10-day injured list.', 'recorded_date': '2023-05-11', 'effective_date': '2023-05-11', 'resolution_date': '2023-05-11', 'available_date': '2023-05-11', 'date_qualification': 'Recorded announcement date, not independently verified first-publication vintage.'}]

Actual ranking inputs: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

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
| employment | 0.873159 | 95.858 | 83.699 | -1.10170 | 0.10545 |
| Actual | 1 | not a forecast | 328 | -1.6693067607876315 | 0.10296 |

PA product 0.873159388 × 95.857655573; offense yield -1.101698619/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 666163, 'bucket': 'MLB', 'plate_appearances': 328, 'strike_outs': 88, 'unintentional_walks': 34, 'hit_by_pitch': 4, 'home_runs': 3, 'babip_hits': 63, 'doubles': 13, 'triples': 0, 'babip_opportunities': 199}]. No PA is not observed zero hitting talent.

Earlier distinct-player profile support: [{'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 417, 'arm': 'preseason', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 33, 'arm': 'preseason', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 0}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 353, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 28, 'arm': 'preseason', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 0}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 417, 'arm': 'employment', 'head': 'participation', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 33, 'arm': 'employment', 'head': 'participation', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 0}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 353, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'broad', 'on_40man': None, 'work_band': None, 'quality_band': None}, {'row_id': 51344, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 2, 'employment_year_known': 1, 'employment_year_fa': 0, 'profile_people': 28, 'arm': 'employment', 'head': 'conditional_pa', 'kind': 'refined', 'on_40man': 1, 'work_band': 1, 'quality_band': 0}]. Broad support does not establish a matched elite-star analogue.

Saved preseason participation: reference -4.033199; raw additive 1.930057; linked probability 0.873256.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.702640.
- games_mlb_0: input 32.000000, contribution +1.231958.
- games_pool_MLB: input 55.400000, contribution +0.606268.
- pooled_MLB_pa: input 137.800000, contribution +0.341837.
- position_2: input 1.000000, contribution +0.328208.
- draft_rank: input 0.470411, contribution +0.216131.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.702639922252493}]

Saved employment participation: reference -4.061106; raw additive 1.929187; linked probability 0.873159.

Largest path terms (accounting, not causality):

- on_40man: input 1.000000, contribution +2.730953.
- games_mlb_0: input 32.000000, contribution +1.159666.
- games_pool_MLB: input 55.400000, contribution +0.603832.
- pooled_MLB_pa: input 137.800000, contribution +0.373299.
- position_2: input 1.000000, contribution +0.329505.
- draft_rank: input 0.470411, contribution +0.226464.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 2.730952967318384}, {'feature': 'employment_year_known', 'input': 1.0, 'path_effect': 0.11173481564373067}]

Same fitted candidate with the three new inputs zero: 0.870517. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Saved preseason conditional_pa: reference 283.910666; raw additive 94.220873; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 79.000000, contribution -94.475876.
- quality_0: input -0.300548, contribution -19.983296.
- role_pool_AAA: input 4.163441, contribution +14.896681.
- pooled_MLB_2B: input 0.027754, contribution -12.267785.
- on_40man: input 1.000000, contribution +12.075051.
- pooled_MLB_K: input 0.249790, contribution -10.620559.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 12.075051138526161}]

Saved employment conditional_pa: reference 283.915500; raw additive 95.857656; raw PA before bounds.

Largest path terms (accounting, not causality):

- work_0: input 79.000000, contribution -94.475876.
- quality_0: input -0.300548, contribution -20.856577.
- role_pool_AAA: input 4.163441, contribution +14.692884.
- on_40man: input 1.000000, contribution +12.074976.
- pooled_MLB_2B: input 0.027754, contribution -12.045417.
- pooled_MLB_pa: input 137.800000, contribution -10.849206.

Employment and roster path terms: [{'feature': 'on_40man', 'input': 1.0, 'path_effect': 12.07497577214923}, {'feature': 'employment_year_fa', 'input': 0.0, 'path_effect': 0.15901085674374013}]

Same fitted candidate with the three new inputs zero: 95.857656. Artificial no-observed-employment fixed-fit probe; roster/performance remain. Not causality or a validated forecast.

Rortvedt is the ordinary case selected by close delivered offense, not by close workload. His 79 MLB PA with two HR plus 124 AAA PA/six HR and preceding minor-only year remain visible; May 11 activation is current attachment, roster one. Candidate .873159 times 95.858 gives 83.699 expected PA versus 328, only 1.42 above fresh-list. Known-current adds .11173 log-odds; the conditional new FA-zero term adds .15901 PA. Zero-new-input probe gives .870517/95.858, with conditional unchanged. Refined support is 33 participation/28 active people. Kieboom 166/0, Miranda 242/429, Kessinger 110/25 and Freeman 195/383 show why short prior samples can lead to diverse jobs. Offense .10545 versus .10296 is cancellation: hitting -1.1017/600 is too favorable relative to -1.6693. The near-perfect offense total must not be used as evidence that workload or talent is right. Employment does not repair that diagnosis.

| Origin-selected peer | Original PA | Fresh-list PA | Employment PA | Actual PA | Employment offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Carter Kieboom | 167.56 | 162.46 | 166.30 | 0 | 0.350 | 0.000 |
| Jose F Miranda | 224.29 | 232.89 | 242.41 | 429 | 0.576 | 1.653 |
| Grae Kessinger | 108.68 | 103.10 | 109.60 | 25 | 0.109 | -0.347 |
| Tyler Freeman | 189.03 | 188.66 | 195.25 | 383 | 0.375 | 0.004 |

## Decision after actual review

Do not adopt the employment addition. Overall and public expected-PA/offense gains are tiny, intervals span zero, MAE worsens against the fresher-ranking anchor, unsigned PA does not improve, and the intended Bader/Wieters/Belt workload errors remain. The upper-minor PA gain is real development evidence worth retaining, not grounds to call the entire model repaired. Latest generic assignment also includes All-Star records: current captured affiliation must not be sold as contract or job evidence. Close this representation batch without another flag/filter sweep. Select V68 fresher-preseason rankings with unchanged V53/V63 hitting as the next coherent research handoff candidate, retain the original as a visible benchmark, and preserve graduation/employment challengers as rejected comparisons. This is a research choice supported by the larger upper-minor source/readiness improvement, not production adoption or completion of the overall goal.

Finish a comparative team-filtered historical handoff for the coherent fresher-ranking candidate and the original model. Expose fixed hitting, appearance chance, conditional/expected PA, expected offense, actual source histories and player reviews separately. State public MAE and immediate-readiness gaps explicitly; support is not calibrated uncertainty. Do not fit more tiny status features. Do not access protected 2026 outcomes or change its frozen forecast.
