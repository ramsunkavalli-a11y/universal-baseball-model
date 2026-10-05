# Corrected preseason context player walkthrough

This tests playing time only. Hitting stays fixed. Actual outcomes below are diagnostics, not forecast inputs. Node-path terms explain arithmetic, not causal effects. Own-source changes and global refitting effects are distinguished with a same-fit old-input probe.

## Hyeseong Kim before 2025

Selection: fixed before fitting.

Actual source changes: {"age": {"old": 27.0, "new": 25.927979356181165}, "age_unknown": {"old": 1, "new": 0}, "age_centered": {"old": 0.0, "new": -0.21440412876376697}, "age_squared": {"old": 0.0, "new": 0.04596913043094997}, "on_40man": {"old": 0, "new": 1}, "source_position": {"old": "UNKNOWN", "new": "4"}, "position_4": {"old": 0, "new": 1}, "position_UNKNOWN": {"old": 1, "new": 0}}.

Dated domestic component counts: [].

Original forecast 0.36 PA (p=0.0047, conditional=76.42); corrected context 19.82 PA (p=0.1978, conditional=100.23); actual 170 PA. Fixed hitting estimate -1.0334 custom batting wins/600; actual conditional hitting -0.3418.

Same fitted candidate with old own inputs gives 0.34 PA. Own input mechanics account for +19.48 PA; changing the fitted model accounts for -0.02. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.0005, new +0.0278, actual +0.4340. Actual-minus-predicted decomposes into opportunity +0.2103 and hitting +0.1960; the two can offset.

Actual held-player training profile support: [{"row_id": 58060, "prior_debut": 0, "stage": "Inactive / unknown", "ctx_age_band": 5, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": true, "profile_people": 2, "head": "participation", "ctx_origin": 2024, "ctx_fold": 4}, {"row_id": 58060, "prior_debut": 0, "stage": "Inactive / unknown", "ctx_age_band": 5, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": true, "profile_people": 1, "head": "conditional_pa", "ctx_origin": 2024, "ctx_fold": 4}].

Outcome-blind peers: [{"player_name": "Ricardo Cespedes", "player_id": 650701, "corrected_age": 26.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0005763303484532, "current_pa": 0.3614786534494445, "ctx_pa": 0.34120724487176846, "next_pa": 0}, {"player_name": "Brady McConnell", "player_id": 669381, "corrected_age": 26.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0005763303484532, "current_pa": 0.5774512818752591, "ctx_pa": 0.5202111904162764, "next_pa": 0}, {"player_name": "Chris Cornelius", "player_id": 674679, "corrected_age": 26.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0005763303484532, "current_pa": 0.4316392119262098, "ctx_pa": 0.44140243723005285, "next_pa": 0}, {"player_name": "Sam McWilliams", "player_id": 681955, "corrected_age": 26.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0005763303484532, "current_pa": 0.38784514561193323, "ctx_pa": 0.35845629275203145, "next_pa": 0}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Jung Hoo Lee before 2025

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2024, "player_id": 808982, "bucket": "MLB", "plate_appearances": 158, "strike_outs": 13, "unintentional_walks": 10, "hit_by_pitch": 1, "home_runs": 2, "babip_hits": 36, "doubles": 4, "triples": 0, "babip_opportunities": 132}].

Original forecast 153.65 PA (p=0.7928, conditional=193.79); corrected context 166.96 PA (p=0.8112, conditional=205.82); actual 617 PA. Fixed hitting estimate -0.6457 custom batting wins/600; actual conditional hitting 0.4631.

Same fitted candidate with old own inputs gives 166.96 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +13.31. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.3145, new +0.3417, actual +2.4030. Actual-minus-predicted decomposes into opportunity +0.9211 and hitting +1.1402; the two can offset.

Actual held-player training profile support: [{"row_id": 58061, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 5, "ctx_mlb_exposure": 1, "ctx_foreign_history_known": true, "profile_people": 12, "head": "participation", "ctx_origin": 2024, "ctx_fold": 1}, {"row_id": 58061, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 5, "ctx_mlb_exposure": 1, "ctx_foreign_history_known": true, "profile_people": 2, "head": "conditional_pa", "ctx_origin": 2024, "ctx_fold": 1}].

Outcome-blind peers: [{"player_name": "Pedro Pagés", "player_id": 686780, "corrected_age": 25.0, "dated_listing": 1, "pa_0": 218, "minor_pa_0": 24, "distance": 0.066816, "current_pa": 162.10631100185975, "ctx_pa": 157.65070123617238, "next_pa": 389}, {"player_name": "Kyle McCann", "player_id": 668832, "corrected_age": 26.0, "dated_listing": 1, "pa_0": 157, "minor_pa_0": 0, "distance": 0.11112711111111111, "current_pa": 101.71845138479563, "ctx_pa": 113.5525353225063, "next_pa": 0}, {"player_name": "Garrett Mitchell", "player_id": 669003, "corrected_age": 25.0, "dated_listing": 1, "pa_0": 224, "minor_pa_0": 61, "distance": 0.129232, "current_pa": 287.9260380713035, "ctx_pa": 294.32489674632563, "next_pa": 78}, {"player_name": "Christian Encarnacion-Strand", "player_id": 687952, "corrected_age": 24.0, "dated_listing": 1, "pa_0": 123, "minor_pa_0": 0, "distance": 0.1307111111111111, "current_pa": 218.9781315551508, "ctx_pa": 228.83966595560148, "next_pa": 137}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Ha-Seong Kim before 2023

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2021, "player_id": 673490, "bucket": "MLB", "plate_appearances": 298, "strike_outs": 71, "unintentional_walks": 21, "hit_by_pitch": 4, "home_runs": 8, "babip_hits": 46, "doubles": 12, "triples": 2, "babip_opportunities": 191}, {"season": 2022, "player_id": 673490, "bucket": "MLB", "plate_appearances": 582, "strike_outs": 100, "unintentional_walks": 51, "hit_by_pitch": 7, "home_runs": 11, "babip_hits": 119, "doubles": 29, "triples": 3, "babip_opportunities": 410}].

Original forecast 445.74 PA (p=0.9885, conditional=450.91); corrected context 445.50 PA (p=0.9872, conditional=451.28); actual 626 PA. Fixed hitting estimate -0.6352 custom batting wins/600; actual conditional hitting 0.5131.

Same fitted candidate with old own inputs gives 445.50 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for -0.24. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.9237, new +0.9232, actual +2.4953. Actual-minus-predicted decomposes into opportunity +0.3740 and hitting +1.1980; the two can offset.

Actual held-player training profile support: [{"row_id": 47763, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 5, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": true, "profile_people": 5, "head": "participation", "ctx_origin": 2022, "ctx_fold": 2}, {"row_id": 47763, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 5, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": true, "profile_people": 3, "head": "conditional_pa", "ctx_origin": 2022, "ctx_fold": 2}].

Outcome-blind peers: [{"player_name": "Austin Hays", "player_id": 669720, "corrected_age": 26.0, "dated_listing": 1, "pa_0": 582, "minor_pa_0": 0, "distance": 0.0, "current_pa": 501.00668825568613, "ctx_pa": 498.2780752744516, "next_pa": 566}, {"player_name": "Cody Bellinger", "player_id": 641355, "corrected_age": 26.0, "dated_listing": 1, "pa_0": 550, "minor_pa_0": 0, "distance": 0.016384, "current_pa": 395.22121581550203, "ctx_pa": 395.67953582340874, "next_pa": 556}, {"player_name": "Lane Thomas", "player_id": 657041, "corrected_age": 26.0, "dated_listing": 1, "pa_0": 548, "minor_pa_0": 0, "distance": 0.018496000000000002, "current_pa": 377.0811908464311, "ctx_pa": 376.00287860224506, "next_pa": 682}, {"player_name": "Willy Adames", "player_id": 642715, "corrected_age": 26.0, "dated_listing": 1, "pa_0": 617, "minor_pa_0": 11, "distance": 0.021536000000000003, "current_pa": 546.3227754223096, "ctx_pa": 549.8527885794354, "next_pa": 638}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Eric Thames before 2017

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [].

Original forecast 20.78 PA (p=0.2067, conditional=100.49); corrected context 25.16 PA (p=0.2485, conditional=101.24); actual 551 PA. Fixed hitting estimate -0.7115 custom batting wins/600; actual conditional hitting 2.4225.

Same fitted candidate with old own inputs gives 25.16 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +4.38. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.0395, new +0.0478, actual +3.9248. Actual-minus-predicted decomposes into opportunity +0.9990 and hitting +2.8780; the two can offset.

Actual held-player training profile support: [{"row_id": 23458, "prior_debut": 1, "stage": "Inactive / unknown", "ctx_age_band": 5, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": true, "profile_people": 12, "head": "participation", "ctx_origin": 2016, "ctx_fold": 4}, {"row_id": 23458, "prior_debut": 1, "stage": "Inactive / unknown", "ctx_age_band": 5, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": true, "profile_people": 0, "head": "conditional_pa", "ctx_origin": 2016, "ctx_fold": 4}].

Outcome-blind peers: [{"player_name": "Kyle Blanks", "player_id": 452035, "corrected_age": 29.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 8.156193874444575, "ctx_pa": 6.5589744624837225, "next_pa": 0}, {"player_name": "Jordan Danks", "player_id": 458668, "corrected_age": 29.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 3.6827687563525826, "ctx_pa": 3.6052819140132355, "next_pa": 0}, {"player_name": "Luis Exposito", "player_id": 458701, "corrected_age": 29.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 0.548048357303533, "ctx_pa": 0.48080094639935156, "next_pa": 0}, {"player_name": "Rene Tosoni", "player_id": 459434, "corrected_age": 29.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 0.3766051839796978, "ctx_pa": 0.32753938588377585, "next_pa": 0}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Aaron Judge before 2025

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2022, "player_id": 592450, "bucket": "MLB", "plate_appearances": 696, "strike_outs": 175, "unintentional_walks": 92, "hit_by_pitch": 6, "home_runs": 62, "babip_hits": 115, "doubles": 28, "triples": 0, "babip_opportunities": 338}, {"season": 2023, "player_id": 592450, "bucket": "MLB", "plate_appearances": 458, "strike_outs": 130, "unintentional_walks": 79, "hit_by_pitch": 0, "home_runs": 37, "babip_hits": 61, "doubles": 16, "triples": 0, "babip_opportunities": 203}, {"season": 2024, "player_id": 592450, "bucket": "MLB", "plate_appearances": 704, "strike_outs": 171, "unintentional_walks": 113, "hit_by_pitch": 9, "home_runs": 58, "babip_hits": 122, "doubles": 36, "triples": 1, "babip_opportunities": 332}].

Original forecast 530.75 PA (p=0.9907, conditional=535.74); corrected context 531.16 PA (p=0.9911, conditional=535.95); actual 679 PA. Fixed hitting estimate 4.9355 custom batting wins/600; actual conditional hitting 6.2874.

Same fitted candidate with old own inputs gives 531.16 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +0.40. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +6.0234, new +6.0279, actual +9.2357. Actual-minus-predicted decomposes into opportunity +1.6778 and hitting +1.5299; the two can offset.

Actual held-player training profile support: [{"row_id": 54849, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 377, "head": "participation", "ctx_origin": 2024, "ctx_fold": 3}, {"row_id": 54849, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 348, "head": "conditional_pa", "ctx_origin": 2024, "ctx_fold": 3}].

Outcome-blind peers: [{"player_name": "Nick Castellanos", "player_id": 592206, "corrected_age": 32.0, "dated_listing": 1, "pa_0": 659, "minor_pa_0": 0, "distance": 0.0324, "current_pa": 501.81449620541986, "ctx_pa": 505.9041826458168, "next_pa": 589}, {"player_name": "Eugenio Suárez", "player_id": 553993, "corrected_age": 32.0, "dated_listing": 1, "pa_0": 640, "minor_pa_0": 0, "distance": 0.065536, "current_pa": 531.3194369035749, "ctx_pa": 537.8693531306897, "next_pa": 657}, {"player_name": "Yandy Díaz", "player_id": 650490, "corrected_age": 32.0, "dated_listing": 1, "pa_0": 621, "minor_pa_0": 0, "distance": 0.11022400000000002, "current_pa": 507.3539877906267, "ctx_pa": 504.0394335279203, "next_pa": 651}, {"player_name": "Kyle Schwarber", "player_id": 656941, "corrected_age": 31.0, "dated_listing": 1, "pa_0": 692, "minor_pa_0": 0, "distance": 0.1134151111111111, "current_pa": 581.6657540085623, "ctx_pa": 578.7333124307182, "next_pa": 724}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Nick Kurtz before 2025

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2024, "player_id": 701762, "bucket": "A", "plate_appearances": 35, "strike_outs": 7, "unintentional_walks": 10, "hit_by_pitch": 0, "home_runs": 4, "babip_hits": 6, "doubles": 2, "triples": 0, "babip_opportunities": 14}, {"season": 2024, "player_id": 701762, "bucket": "AA", "plate_appearances": 15, "strike_outs": 3, "unintentional_walks": 2, "hit_by_pitch": 0, "home_runs": 0, "babip_hits": 4, "doubles": 1, "triples": 0, "babip_opportunities": 10}].

Original forecast 10.18 PA (p=0.0606, conditional=168.16); corrected context 9.13 PA (p=0.0549, conditional=166.23); actual 489 PA. Fixed hitting estimate 1.0243 custom batting wins/600; actual conditional hitting 5.1500.

Same fitted candidate with old own inputs gives 9.13 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for -1.05. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.0492, new +0.0441, actual +5.7243. Actual-minus-predicted decomposes into opportunity +2.3178 and hitting +3.3625; the two can offset.

Actual held-player training profile support: [{"row_id": 57052, "prior_debut": 0, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 2579, "head": "participation", "ctx_origin": 2024, "ctx_fold": 2}, {"row_id": 57052, "prior_debut": 0, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 601, "head": "conditional_pa", "ctx_origin": 2024, "ctx_fold": 2}].

Outcome-blind peers: [{"player_name": "Benny Montgomery", "player_id": 695603, "corrected_age": 21.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 48, "distance": 6.4e-05, "current_pa": 5.411682359784917, "ctx_pa": 5.048652992255163, "next_pa": 0}, {"player_name": "Ben Hartl", "player_id": 803015, "corrected_age": 21.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 57, "distance": 0.0007840000000000001, "current_pa": 0.3543775985679851, "ctx_pa": 0.2547483491672137, "next_pa": 0}, {"player_name": "Wally Soto", "player_id": 695222, "corrected_age": 21.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 85, "distance": 0.019600000000000003, "current_pa": 0.1210043385027775, "ctx_pa": 0.10704315833612878, "next_pa": 0}, {"player_name": "Sergio Tapia", "player_id": 685337, "corrected_age": 21.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 103, "distance": 0.044944, "current_pa": 0.1760903455325331, "ctx_pa": 0.14525869793274343, "next_pa": 0}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Steven Kwan before 2022

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2019, "player_id": 680757, "bucket": "Aplus", "plate_appearances": 542, "strike_outs": 51, "unintentional_walks": 52, "hit_by_pitch": 4, "home_runs": 3, "babip_hits": 131, "doubles": 26, "triples": 7, "babip_opportunities": 430}, {"season": 2021, "player_id": 680757, "bucket": "AA", "plate_appearances": 221, "strike_outs": 23, "unintentional_walks": 22, "hit_by_pitch": 3, "home_runs": 7, "babip_hits": 58, "doubles": 12, "triples": 3, "babip_opportunities": 164}, {"season": 2021, "player_id": 680757, "bucket": "AAA", "plate_appearances": 120, "strike_outs": 8, "unintentional_walks": 14, "hit_by_pitch": 1, "home_runs": 5, "babip_hits": 27, "doubles": 3, "triples": 1, "babip_opportunities": 90}].

Original forecast 115.97 PA (p=0.6957, conditional=166.69); corrected context 110.37 PA (p=0.6765, conditional=163.14); actual 638 PA. Fixed hitting estimate -0.2531 custom batting wins/600; actual conditional hitting 1.6179.

Same fitted candidate with old own inputs gives 110.37 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for -5.60. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.3145, new +0.2993, actual +3.7197. Actual-minus-predicted decomposes into opportunity +1.4308 and hitting +1.9895; the two can offset.

Actual held-player training profile support: [{"row_id": 44435, "prior_debut": 0, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 1834, "head": "participation", "ctx_origin": 2021, "ctx_fold": 1}, {"row_id": 44435, "prior_debut": 0, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 446, "head": "conditional_pa", "ctx_origin": 2021, "ctx_fold": 1}].

Outcome-blind peers: [{"player_name": "Ronaldo Hernández", "player_id": 660613, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 0, "minor_pa_0": 387, "distance": 0.033856, "current_pa": 73.93345523480006, "ctx_pa": 83.67526225659921, "next_pa": 0}, {"player_name": "Nolan Jones", "player_id": 666134, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 0, "minor_pa_0": 407, "distance": 0.06969600000000001, "current_pa": 117.38151599277352, "ctx_pa": 116.65870415073597, "next_pa": 94}, {"player_name": "Jonathan Aranda", "player_id": 666018, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 0, "minor_pa_0": 411, "distance": 0.07840000000000001, "current_pa": 42.997460209485645, "ctx_pa": 48.67868653901794, "next_pa": 87}, {"player_name": "Lucius Fox", "player_id": 665650, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 0, "minor_pa_0": 270, "distance": 0.08065600000000002, "current_pa": 41.67513250534476, "ctx_pa": 49.20809988968929, "next_pa": 28}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Junior Caminero before 2025

Selection: fixed before fitting.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2022, "player_id": 691406, "bucket": "A", "plate_appearances": 117, "strike_outs": 22, "unintentional_walks": 8, "hit_by_pitch": 2, "home_runs": 6, "babip_hits": 26, "doubles": 2, "triples": 1, "babip_opportunities": 79}, {"season": 2022, "player_id": 691406, "bucket": "RK124", "plate_appearances": 154, "strike_outs": 21, "unintentional_walks": 15, "hit_by_pitch": 4, "home_runs": 5, "babip_hits": 38, "doubles": 5, "triples": 1, "babip_opportunities": 109}, {"season": 2023, "player_id": 691406, "bucket": "AA", "plate_appearances": 351, "strike_outs": 60, "unintentional_walks": 31, "hit_by_pitch": 2, "home_runs": 20, "babip_hits": 77, "doubles": 9, "triples": 3, "babip_opportunities": 237}, {"season": 2023, "player_id": 691406, "bucket": "Aplus", "plate_appearances": 159, "strike_outs": 40, "unintentional_walks": 10, "hit_by_pitch": 3, "home_runs": 11, "babip_hits": 41, "doubles": 9, "triples": 3, "babip_opportunities": 95}, {"season": 2023, "player_id": 691406, "bucket": "MLB", "plate_appearances": 36, "strike_outs": 8, "unintentional_walks": 2, "hit_by_pitch": 0, "home_runs": 1, "babip_hits": 7, "doubles": 1, "triples": 0, "babip_opportunities": 25}, {"season": 2024, "player_id": 691406, "bucket": "AAA", "plate_appearances": 236, "strike_outs": 50, "unintentional_walks": 16, "hit_by_pitch": 2, "home_runs": 13, "babip_hits": 47, "doubles": 9, "triples": 0, "babip_opportunities": 155}, {"season": 2024, "player_id": 691406, "bucket": "MLB", "plate_appearances": 177, "strike_outs": 38, "unintentional_walks": 9, "hit_by_pitch": 1, "home_runs": 6, "babip_hits": 35, "doubles": 9, "triples": 1, "babip_opportunities": 121}, {"season": 2024, "player_id": 691406, "bucket": "RK124", "plate_appearances": 22, "strike_outs": 2, "unintentional_walks": 5, "hit_by_pitch": 0, "home_runs": 3, "babip_hits": 1, "doubles": 1, "triples": 0, "babip_opportunities": 12}].

Original forecast 419.43 PA (p=0.8989, conditional=466.60); corrected context 421.14 PA (p=0.9181, conditional=458.69); actual 653 PA. Fixed hitting estimate 0.5877 custom batting wins/600; actual conditional hitting 2.1754.

Same fitted candidate with old own inputs gives 421.14 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +1.71. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +1.7207, new +1.7277, actual +4.4068. Actual-minus-predicted decomposes into opportunity +0.9512 and hitting +1.7279; the two can offset.

Actual held-player training profile support: [{"row_id": 56439, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 4, "ctx_mlb_exposure": 1, "ctx_foreign_history_known": false, "profile_people": 505, "head": "participation", "ctx_origin": 2024, "ctx_fold": 4}, {"row_id": 56439, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 4, "ctx_mlb_exposure": 1, "ctx_foreign_history_known": false, "profile_people": 435, "head": "conditional_pa", "ctx_origin": 2024, "ctx_fold": 4}].

Outcome-blind peers: [{"player_name": "Jackson Holliday", "player_id": 702616, "corrected_age": 20.0, "dated_listing": 1, "pa_0": 208, "minor_pa_0": 346, "distance": 0.13928, "current_pa": 328.4366772748338, "ctx_pa": 308.20352149986473, "next_pa": 649}, {"player_name": "Jasson Domínguez", "player_id": 691176, "corrected_age": 21.0, "dated_listing": 1, "pa_0": 67, "minor_pa_0": 250, "distance": 0.3057351111111111, "current_pa": 285.15214769229425, "ctx_pa": 273.5659405128781, "next_pa": 429}, {"player_name": "Angel Martínez", "player_id": 682657, "corrected_age": 22.0, "dated_listing": 1, "pa_0": 169, "minor_pa_0": 258, "distance": 0.44546844444444444, "current_pa": 268.8366458101944, "ctx_pa": 279.8869619059016, "next_pa": 484}, {"player_name": "Jhonkensy Noel", "player_id": 678877, "corrected_age": 22.0, "dated_listing": 1, "pa_0": 198, "minor_pa_0": 284, "distance": 0.4623164444444444, "current_pa": 304.68423842904946, "ctx_pa": 297.8592354487974, "next_pa": 153}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Rhys Hoskins before 2024

Selection: largest PA squared-error gain.

Actual source changes: {"on_40man": {"old": 0, "new": 1}}.

Dated domestic component counts: [{"season": 2021, "player_id": 656555, "bucket": "MLB", "plate_appearances": 443, "strike_outs": 108, "unintentional_walks": 47, "hit_by_pitch": 5, "home_runs": 27, "babip_hits": 69, "doubles": 29, "triples": 0, "babip_opportunities": 256}, {"season": 2022, "player_id": 656555, "bucket": "MLB", "plate_appearances": 672, "strike_outs": 169, "unintentional_walks": 72, "hit_by_pitch": 6, "home_runs": 30, "babip_hits": 115, "doubles": 33, "triples": 2, "babip_opportunities": 394}].

Original forecast 26.26 PA (p=0.1007, conditional=260.91); corrected context 193.13 PA (p=0.6703, conditional=288.11); actual 517 PA. Fixed hitting estimate 0.0373 custom batting wins/600; actual conditional hitting 0.1328.

Same fitted candidate with old own inputs gives 24.87 PA. Own input mechanics account for +168.27 PA; changing the fitted model accounts for -1.39. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.0829, new +0.6100, actual +1.7151. Actual-minus-predicted decomposes into opportunity +1.0228 and hitting +0.0823; the two can offset.

Actual held-player training profile support: [{"row_id": 51083, "prior_debut": 1, "stage": "Inactive / unknown", "ctx_age_band": 6, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 166, "head": "participation", "ctx_origin": 2023, "ctx_fold": 4}, {"row_id": 51083, "prior_debut": 1, "stage": "Inactive / unknown", "ctx_age_band": 6, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 8, "head": "conditional_pa", "ctx_origin": 2023, "ctx_fold": 4}].

Outcome-blind peers: [{"player_name": "Max Stassi", "player_id": 545358, "corrected_age": 32.0, "dated_listing": 1, "pa_0": 0, "minor_pa_0": 0, "distance": 0.4444444444444444, "current_pa": 94.9029390568878, "ctx_pa": 104.2643751147277, "next_pa": 0}, {"player_name": "Christian Lopes", "player_id": 547173, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 1.8060677390307585, "ctx_pa": 1.4967049343729155, "next_pa": 0}, {"player_name": "Alfredo González", "player_id": 554054, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 0.4598171262805604, "ctx_pa": 0.4396124311210717, "next_pa": 0}, {"player_name": "José Marmolejos", "player_id": 592530, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 0, "distance": 1.0, "current_pa": 6.389341982218823, "ctx_pa": 7.048647200766347, "next_pa": 0}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Luke Voit before 2022

Selection: largest PA squared-error harm.

Actual source changes: {"on_40man": {"old": 1, "new": 0}}.

Dated domestic component counts: [{"season": 2019, "player_id": 572228, "bucket": "AAA", "plate_appearances": 19, "strike_outs": 2, "unintentional_walks": 2, "hit_by_pitch": 0, "home_runs": 2, "babip_hits": 6, "doubles": 2, "triples": 0, "babip_opportunities": 13}, {"season": 2019, "player_id": 572228, "bucket": "MLB", "plate_appearances": 510, "strike_outs": 142, "unintentional_walks": 69, "hit_by_pitch": 9, "home_runs": 21, "babip_hits": 92, "doubles": 21, "triples": 1, "babip_opportunities": 267}, {"season": 2020, "player_id": 572228, "bucket": "MLB", "plate_appearances": 234, "strike_outs": 54, "unintentional_walks": 17, "hit_by_pitch": 3, "home_runs": 22, "babip_hits": 37, "doubles": 5, "triples": 0, "babip_opportunities": 138}, {"season": 2021, "player_id": 572228, "bucket": "AA", "plate_appearances": 17, "strike_outs": 5, "unintentional_walks": 1, "hit_by_pitch": 0, "home_runs": 2, "babip_hits": 5, "doubles": 1, "triples": 0, "babip_opportunities": 9}, {"season": 2021, "player_id": 572228, "bucket": "AAA", "plate_appearances": 36, "strike_outs": 8, "unintentional_walks": 3, "hit_by_pitch": 1, "home_runs": 4, "babip_hits": 7, "doubles": 3, "triples": 0, "babip_opportunities": 20}, {"season": 2021, "player_id": 572228, "bucket": "MLB", "plate_appearances": 241, "strike_outs": 74, "unintentional_walks": 21, "hit_by_pitch": 7, "home_runs": 11, "babip_hits": 40, "doubles": 7, "triples": 1, "babip_opportunities": 128}].

Original forecast 345.43 PA (p=0.9436, conditional=366.08); corrected context 179.81 PA (p=0.5707, conditional=315.06); actual 568 PA. Fixed hitting estimate 1.3246 custom batting wins/600; actual conditional hitting 0.1174.

Same fitted candidate with old own inputs gives 340.84 PA. Own input mechanics account for -161.03 PA; changing the fitted model accounts for -4.59. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +1.8451, new +0.9604, actual +1.8911. Actual-minus-predicted decomposes into opportunity +2.0735 and hitting -1.1428; the two can offset.

Actual held-player training profile support: [{"row_id": 42318, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 266, "head": "participation", "ctx_origin": 2021, "ctx_fold": 3}, {"row_id": 42318, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 244, "head": "conditional_pa", "ctx_origin": 2021, "ctx_fold": 3}].

Outcome-blind peers: [{"player_name": "Brian Goodwin", "player_id": 571718, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 271, "minor_pa_0": 95, "distance": 0.042624, "current_pa": 92.98969274807482, "ctx_pa": 90.06835364772053, "next_pa": 0}, {"player_name": "Joe Panik", "player_id": 605412, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 257, "minor_pa_0": 0, "distance": 0.04904, "current_pa": 55.38576004155876, "ctx_pa": 48.497470467346766, "next_pa": 0}, {"player_name": "Jake Marisnick", "player_id": 545350, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 198, "minor_pa_0": 6, "distance": 0.06492800000000001, "current_pa": 55.567082685136555, "ctx_pa": 54.97100571480621, "next_pa": 82}, {"player_name": "Jake Lamb", "player_id": 571875, "corrected_age": 30.0, "dated_listing": 0, "pa_0": 170, "minor_pa_0": 69, "distance": 0.08475200000000002, "current_pa": 58.923737502179975, "ctx_pa": 62.586357262973486, "next_pa": 111}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Matt McLain before 2024

Selection: major false high.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2021, "player_id": 680574, "bucket": "Aplus", "plate_appearances": 119, "strike_outs": 24, "unintentional_walks": 17, "hit_by_pitch": 2, "home_runs": 3, "babip_hits": 24, "doubles": 6, "triples": 0, "babip_opportunities": 73}, {"season": 2021, "player_id": 680574, "bucket": "RK121", "plate_appearances": 7, "strike_outs": 0, "unintentional_walks": 0, "hit_by_pitch": 0, "home_runs": 0, "babip_hits": 3, "doubles": 2, "triples": 1, "babip_opportunities": 7}, {"season": 2022, "player_id": 680574, "bucket": "AA", "plate_appearances": 452, "strike_outs": 127, "unintentional_walks": 69, "hit_by_pitch": 8, "home_runs": 17, "babip_hits": 69, "doubles": 21, "triples": 5, "babip_opportunities": 230}, {"season": 2023, "player_id": 680574, "bucket": "AAA", "plate_appearances": 180, "strike_outs": 37, "unintentional_walks": 29, "hit_by_pitch": 5, "home_runs": 12, "babip_hits": 37, "doubles": 12, "triples": 1, "babip_opportunities": 96}, {"season": 2023, "player_id": 680574, "bucket": "MLB", "plate_appearances": 403, "strike_outs": 115, "unintentional_walks": 31, "hit_by_pitch": 7, "home_runs": 16, "babip_hits": 90, "doubles": 23, "triples": 4, "babip_opportunities": 234}].

Original forecast 599.38 PA (p=0.9853, conditional=608.34); corrected context 604.71 PA (p=0.9845, conditional=614.24); actual 0 PA. Fixed hitting estimate 0.8747 custom batting wins/600; actual conditional hitting 0.0000.

Same fitted candidate with old own inputs gives 604.71 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +5.34. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +2.7295, new +2.7538, actual +0.0000. Actual-minus-predicted decomposes into opportunity -2.7538 and hitting -0.0000; the two can offset.

Actual held-player training profile support: [{"row_id": 51984, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 4, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 246, "head": "participation", "ctx_origin": 2023, "ctx_fold": 2}, {"row_id": 51984, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 4, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 238, "head": "conditional_pa", "ctx_origin": 2023, "ctx_fold": 2}].

Outcome-blind peers: [{"player_name": "Alek Thomas", "player_id": 677950, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 402, "minor_pa_0": 128, "distance": 0.04328000000000001, "current_pa": 353.67856546183333, "ctx_pa": 369.9647763221934, "next_pa": 103}, {"player_name": "Brett Baty", "player_id": 683146, "corrected_age": 23.0, "dated_listing": 1, "pa_0": 389, "minor_pa_0": 121, "distance": 0.05883200000000001, "current_pa": 385.83262356492867, "ctx_pa": 378.4233249005167, "next_pa": 171}, {"player_name": "Edouard Julien", "player_id": 666397, "corrected_age": 24.0, "dated_listing": 1, "pa_0": 408, "minor_pa_0": 170, "distance": 0.1131111111111111, "current_pa": 367.9790481517715, "ctx_pa": 370.4507242754037, "next_pa": 301}, {"player_name": "Christopher Morel", "player_id": 666624, "corrected_age": 24.0, "dated_listing": 1, "pa_0": 429, "minor_pa_0": 134, "distance": 0.1557831111111111, "current_pa": 449.0079965923585, "ctx_pa": 442.5263320274598, "next_pa": 611}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Fernando Tatis Jr. before 2023

Selection: major false low.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2020, "player_id": 665487, "bucket": "MLB", "plate_appearances": 257, "strike_outs": 61, "unintentional_walks": 26, "hit_by_pitch": 5, "home_runs": 17, "babip_hits": 45, "doubles": 11, "triples": 2, "babip_opportunities": 147}, {"season": 2021, "player_id": 665487, "bucket": "MLB", "plate_appearances": 546, "strike_outs": 153, "unintentional_walks": 56, "hit_by_pitch": 2, "home_runs": 42, "babip_hits": 93, "doubles": 31, "triples": 0, "babip_opportunities": 287}, {"season": 2022, "player_id": 665487, "bucket": "AA", "plate_appearances": 14, "strike_outs": 2, "unintentional_walks": 4, "hit_by_pitch": 1, "home_runs": 0, "babip_hits": 2, "doubles": 1, "triples": 1, "babip_opportunities": 7}].

Original forecast 39.68 PA (p=0.1340, conditional=296.16); corrected context 22.32 PA (p=0.0795, conditional=280.93); actual 635 PA. Fixed hitting estimate 1.3131 custom batting wins/600; actual conditional hitting 0.7268.

Same fitted candidate with old own inputs gives 22.32 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for -17.36. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.2111, new +0.1187, actual +2.7574. Actual-minus-predicted decomposes into opportunity +3.2591 and hitting -0.6205; the two can offset.

Actual held-player training profile support: [{"row_id": 47261, "prior_debut": 1, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 52, "head": "participation", "ctx_origin": 2022, "ctx_fold": 0}, {"row_id": 47261, "prior_debut": 1, "stage": "Upper minors", "ctx_age_band": 4, "ctx_mlb_exposure": 0, "ctx_foreign_history_known": false, "profile_people": 31, "head": "conditional_pa", "ctx_origin": 2022, "ctx_fold": 0}].

Outcome-blind peers: [{"player_name": "Sherten Apostel", "player_id": 665947, "corrected_age": 23.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 77, "distance": 0.063504, "current_pa": 3.685561571158761, "ctx_pa": 4.64170044890649, "next_pa": 0}, {"player_name": "Colton Welker", "player_id": 666213, "corrected_age": 24.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 45, "distance": 0.1264871111111111, "current_pa": 8.183293097937952, "ctx_pa": 6.829540359749968, "next_pa": 0}, {"player_name": "Jahmai Jones", "player_id": 663330, "corrected_age": 24.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 118, "distance": 0.28416711111111115, "current_pa": 9.568313358018756, "ctx_pa": 8.26077178059475, "next_pa": 11}, {"player_name": "Luis Alexander Basabe", "player_id": 642772, "corrected_age": 25.0, "dated_listing": 0, "pa_0": 0, "minor_pa_0": 26, "distance": 0.4467484444444444, "current_pa": 1.428240118648999, "ctx_pa": 1.7087732249464849, "next_pa": 0}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Martín Prado before 2019

Selection: ordinary active forecast.

Actual source changes: {}.

Dated domestic component counts: [{"season": 2016, "player_id": 445988, "bucket": "MLB", "plate_appearances": 658, "strike_outs": 69, "unintentional_walks": 45, "hit_by_pitch": 4, "home_runs": 8, "babip_hits": 175, "doubles": 37, "triples": 3, "babip_opportunities": 528}, {"season": 2017, "player_id": 445988, "bucket": "AA", "plate_appearances": 5, "strike_outs": 0, "unintentional_walks": 0, "hit_by_pitch": 0, "home_runs": 0, "babip_hits": 2, "doubles": 1, "triples": 0, "babip_opportunities": 5}, {"season": 2017, "player_id": 445988, "bucket": "Aplus", "plate_appearances": 25, "strike_outs": 5, "unintentional_walks": 3, "hit_by_pitch": 0, "home_runs": 0, "babip_hits": 6, "doubles": 1, "triples": 0, "babip_opportunities": 17}, {"season": 2017, "player_id": 445988, "bucket": "MLB", "plate_appearances": 147, "strike_outs": 22, "unintentional_walks": 6, "hit_by_pitch": 0, "home_runs": 2, "babip_hits": 33, "doubles": 9, "triples": 0, "babip_opportunities": 117}, {"season": 2018, "player_id": 445988, "bucket": "Aplus", "plate_appearances": 31, "strike_outs": 2, "unintentional_walks": 3, "hit_by_pitch": 0, "home_runs": 0, "babip_hits": 7, "doubles": 1, "triples": 0, "babip_opportunities": 26}, {"season": 2018, "player_id": 445988, "bucket": "MLB", "plate_appearances": 209, "strike_outs": 35, "unintentional_walks": 11, "hit_by_pitch": 1, "home_runs": 1, "babip_hits": 47, "doubles": 9, "triples": 0, "babip_opportunities": 161}].

Original forecast 228.76 PA (p=0.7952, conditional=287.68); corrected context 260.03 PA (p=0.8605, conditional=302.17); actual 260 PA. Fixed hitting estimate -1.1925 custom batting wins/600; actual conditional hitting -3.8230.

Same fitted candidate with old own inputs gives 260.03 PA. Own input mechanics account for +0.00 PA; changing the fitted model accounts for +31.27. This is a diagnostic decomposition, not causal attribution or a new forecast arm.

Delivered relative contribution: old +0.2499, new +0.2841, actual -0.8558. Actual-minus-predicted decomposes into opportunity -0.0000 and hitting -1.1399; the two can offset.

Actual held-player training profile support: [{"row_id": 32154, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 232, "head": "participation", "ctx_origin": 2018, "ctx_fold": 3}, {"row_id": 32154, "prior_debut": 1, "stage": "Current MLB", "ctx_age_band": 6, "ctx_mlb_exposure": 2, "ctx_foreign_history_known": false, "profile_people": 211, "head": "conditional_pa", "ctx_origin": 2018, "ctx_fold": 3}].

Outcome-blind peers: [{"player_name": "Brian McCann", "player_id": 435263, "corrected_age": 34.0, "dated_listing": 1, "pa_0": 216, "minor_pa_0": 25, "distance": 0.00136, "current_pa": 199.57870526727638, "ctx_pa": 204.52085641431208, "next_pa": 316}, {"player_name": "Howie Kendrick", "player_id": 435062, "corrected_age": 34.0, "dated_listing": 1, "pa_0": 160, "minor_pa_0": 0, "distance": 0.053792000000000006, "current_pa": 326.8868201250588, "ctx_pa": 317.80287631292185, "next_pa": 370}, {"player_name": "Jeff Mathis", "player_id": 425772, "corrected_age": 35.0, "dated_listing": 1, "pa_0": 218, "minor_pa_0": 0, "distance": 0.1277831111111111, "current_pa": 124.30876880559637, "ctx_pa": 129.84755631488935, "next_pa": 244}, {"player_name": "Jarrod Dyson", "player_id": 502481, "corrected_age": 33.0, "dated_listing": 1, "pa_0": 237, "minor_pa_0": 6, "distance": 0.1336551111111111, "current_pa": 165.15723929462672, "ctx_pa": 156.9301842976607, "next_pa": 452}].

Exact old/new inputs and all head terms are saved in reviewed-cases.json. Foreign counts, if present there, were not used in this fit. Missing listing is not retirement; any remaining foreign-history gap is not zero talent.

## Omitted international entrants remain unfinished

Ohtani before 2018, Suzuki before 2022, Yoshida before 2023 and Lee before 2024 are source additions with dated context and foreign counts but no old forecast. This matched original-row test cannot repair their missing forecasts. The separate additions/translation comparison is still required; none is counted as a correct zero here.
