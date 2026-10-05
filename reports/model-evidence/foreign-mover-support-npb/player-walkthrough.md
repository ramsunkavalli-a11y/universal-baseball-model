# Foreign hitter translation training support

Source and support audit only. No new forecast, adjustment or MLB accuracy claim. Both directions and same-season versus consecutive moves remain separate; 2020 bridge pairs are not in primary training support. Player roles come from the dated domestic side, not a present-day foreign profile. All identity gaps remain in the original source.

## Shohei Ohtani before 2018

Fixed case MLBAM 660271, origin 2017; NPB age at origin end 23.491242119961395. Three recent years: 732 PA, 35 HR, 204 K and 83 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 10 distinct direct hitter movers, 0 in the same age band and 0 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2015, "player_id": 660271, "league": "NPB", "source_name": "大谷　翔平", "birth_date": "1994-07-05", "role": "unknown", "pa": 119, "ab": 109, "hits": 22, "doubles": 4, "triples": 0, "hr": 5, "bb": 8, "ibb": 1, "hbp": 0, "so": 43, "sf": 2}, {"season": 2016, "player_id": 660271, "league": "NPB", "source_name": "大谷　翔平", "birth_date": "1994-07-05", "role": "unknown", "pa": 382, "ab": 323, "hits": 104, "doubles": 18, "triples": 1, "hr": 22, "bb": 54, "ibb": 2, "hbp": 1, "so": 98, "sf": 4}, {"season": 2017, "player_id": 660271, "league": "NPB", "source_name": "大谷　翔平", "birth_date": "1994-07-05", "role": "unknown", "pa": 231, "ab": 202, "hits": 67, "doubles": 16, "triples": 1, "hr": 8, "bb": 24, "ibb": 0, "hbp": 2, "so": 63, "sf": 3}]

Dated MLB context: [{"candidate_key": "2017:660271", "origin_year": 2017, "target_year": 2018, "information_date": "2018-01-27", "player_id": 660271, "player_name": "Shohei Ohtani", "current_model_origin": false, "current_row_id": null, "returned_40man": false, "roster_team_ids": [], "roster_position_codes": [], "roster_cross_team_conflict": false, "roster_raw_rows": 0, "roster_duplicate_rows": 0, "roster_status_conflict": false, "eligible_mlb_team_event_records": 1, "positive_context_records": 1, "late_event_records": 0, "latest_event_date": "2017-12-09", "latest_event_kinds": ["minor_agreement"], "scope_exit_records": 0, "minor_agreement_records": 1, "origin_has_positive_context": true, "latest_domestic_stat_season": null, "last_domestic_source_position": "UNKNOWN", "role_status": "unknown", "recent_domestic_pa": 0, "recent_mlb_pa": 0, "domestic_batting_history_missing": true, "hitter_eligibility_approved": false, "complete_historical_rights_verified": false}]

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 685542, "source_name": "横尾　俊建", "age": 24.597356550784752, "pa": 166, "k_rate": 0.2891566265060241, "hr_rate": 0.04216867469879518, "distance": 1.4574216703725411}, {"player_id": 451713, "source_name": "ペゲーロ", "age": 30.85621196876048, "pa": 717, "k_rate": 0.28730822873082285, "hr_rate": 0.0502092050209205, "distance": 1.6640242568546488}, {"player_id": 683819, "source_name": "上林　誠知", "age": 22.4179825732219, "pa": 517, "k_rate": 0.22437137330754353, "hr_rate": 0.029013539651837523, "distance": 1.7428456887886263}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

## Seiya Suzuki before 2022

Fixed case MLBAM 673548, origin 2021; NPB age at origin end 27.37085634886411. Three recent years: 1659 PA, 91 HR, 242 K and 230 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 10 distinct direct hitter movers, 3 in the same age band and 0 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2019, "player_id": 673548, "league": "NPB", "source_name": "鈴木　誠也", "birth_date": "1994-08-18", "role": "unknown", "pa": 612, "ab": 499, "hits": 167, "doubles": 31, "triples": 0, "hr": 28, "bb": 103, "ibb": 12, "hbp": 7, "so": 81, "sf": 3}, {"season": 2020, "player_id": 673548, "league": "NPB", "source_name": "鈴木　誠也", "birth_date": "1994-08-18", "role": "unknown", "pa": 514, "ab": 430, "hits": 129, "doubles": 26, "triples": 2, "hr": 25, "bb": 72, "ibb": 9, "hbp": 9, "so": 73, "sf": 3}, {"season": 2021, "player_id": 673548, "league": "NPB", "source_name": "鈴木　誠也", "birth_date": "1994-08-18", "role": "unknown", "pa": 533, "ab": 435, "hits": 138, "doubles": 26, "triples": 0, "hr": 38, "bb": 87, "ibb": 11, "hbp": 6, "so": 88, "sf": 5}]

Dated MLB context: [{"candidate_key": "2021:673548", "origin_year": 2021, "target_year": 2022, "information_date": "2022-03-18", "player_id": 673548, "player_name": "Seiya Suzuki", "current_model_origin": false, "current_row_id": null, "returned_40man": true, "roster_team_ids": [112], "roster_position_codes": ["O"], "roster_cross_team_conflict": false, "roster_raw_rows": 1, "roster_duplicate_rows": 0, "roster_status_conflict": false, "eligible_mlb_team_event_records": 3, "positive_context_records": 3, "late_event_records": 0, "latest_event_date": "2022-03-18", "latest_event_kinds": ["activation", "agreement_unspecified"], "scope_exit_records": 0, "minor_agreement_records": 0, "origin_has_positive_context": true, "latest_domestic_stat_season": null, "last_domestic_source_position": "UNKNOWN", "role_status": "unknown", "recent_domestic_pa": 0, "recent_mlb_pa": 0, "domestic_batting_history_missing": true, "hitter_eligibility_approved": false, "complete_historical_rights_verified": false}]

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 672960, "source_name": "岡本　和真", "age": 25.50360377009795, "pa": 1720, "k_rate": 0.18895348837209303, "hr_rate": 0.05872093023255814, "distance": 1.0348956517509142}, {"player_id": 831662, "source_name": "大山　悠輔", "age": 27.034093787004522, "pa": 1570, "k_rate": 0.18025477707006368, "hr_rate": 0.040127388535031845, "distance": 1.0503546214366728}, {"player_id": 660280, "source_name": "山田　哲人", "age": 29.459879395196342, "pa": 1606, "k_rate": 0.18929016189290163, "hr_rate": 0.050435865504358655, "distance": 1.087544667582021}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

## Masataka Yoshida before 2023

Fixed case MLBAM 807799, origin 2022; NPB age at origin end 29.46261730220333. Three recent years: 1455 PA, 56 HR, 96 K and 169 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 10 distinct direct hitter movers, 4 in the same age band and 2 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2020, "player_id": 807799, "league": "NPB", "source_name": "吉田　正尚", "birth_date": "1993-07-15", "role": "unknown", "pa": 492, "ab": 408, "hits": 143, "doubles": 22, "triples": 1, "hr": 14, "bb": 72, "ibb": 17, "hbp": 8, "so": 29, "sf": 4}, {"season": 2021, "player_id": 807799, "league": "NPB", "source_name": "吉田　正尚", "birth_date": "1993-07-15", "role": "unknown", "pa": 455, "ab": 389, "hits": 132, "doubles": 22, "triples": 1, "hr": 21, "bb": 58, "ibb": 6, "hbp": 5, "so": 26, "sf": 3}, {"season": 2022, "player_id": 807799, "league": "NPB", "source_name": "吉田　正尚", "birth_date": "1993-07-15", "role": "unknown", "pa": 508, "ab": 412, "hits": 138, "doubles": 28, "triples": 1, "hr": 21, "bb": 80, "ibb": 18, "hbp": 9, "so": 41, "sf": 7}]

Dated MLB context: [{"candidate_key": "2022:807799", "origin_year": 2022, "target_year": 2023, "information_date": "2023-01-26", "player_id": 807799, "player_name": "Masataka Yoshida", "current_model_origin": false, "current_row_id": null, "returned_40man": true, "roster_team_ids": [111], "roster_position_codes": ["7"], "roster_cross_team_conflict": false, "roster_raw_rows": 1, "roster_duplicate_rows": 0, "roster_status_conflict": false, "eligible_mlb_team_event_records": 1, "positive_context_records": 1, "late_event_records": 0, "latest_event_date": "2022-12-15", "latest_event_kinds": ["agreement_unspecified"], "scope_exit_records": 0, "minor_agreement_records": 0, "origin_has_positive_context": true, "latest_domestic_stat_season": null, "last_domestic_source_position": "UNKNOWN", "role_status": "hitter_history_or_listing_hint", "recent_domestic_pa": 0, "recent_mlb_pa": 0, "domestic_batting_history_missing": true, "hitter_eligibility_approved": false, "complete_historical_rights_verified": false}]

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 685547, "source_name": "近藤　健介", "age": 29.394169627028617, "pa": 1408, "k_rate": 0.14275568181818182, "hr_rate": 0.017045454545454544, "distance": 1.5745364708883218}, {"player_id": 493364, "source_name": "ビシエド", "age": 33.81041362930108, "pa": 1520, "k_rate": 0.10723684210526316, "hr_rate": 0.031578947368421054, "distance": 1.6207680433781926}, {"player_id": 831662, "source_name": "大山　悠輔", "age": 28.03342984455533, "pa": 1493, "k_rate": 0.19290020093770932, "hr_rate": 0.04822505023442733, "distance": 1.9429482773349127}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

## Kosuke Fukudome before 2008

Fixed case MLBAM 493120, origin 2007; NPB age at origin end 30.680985920313216. Three recent years: 1538 PA, 72 HR, 288 K and 228 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 0 distinct direct hitter movers, 0 in the same age band and 0 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2005, "player_id": 493120, "league": "NPB", "source_name": "福留　孝介", "birth_date": "1977-04-26", "role": "unknown", "pa": 612, "ab": 515, "hits": 169, "doubles": 39, "triples": 6, "hr": 28, "bb": 93, "ibb": 3, "hbp": 1, "so": 128, "sf": 3}, {"season": 2006, "player_id": 493120, "league": "NPB", "source_name": "福留　孝介", "birth_date": "1977-04-26", "role": "unknown", "pa": 578, "ab": 496, "hits": 174, "doubles": 47, "triples": 5, "hr": 31, "bb": 76, "ibb": 4, "hbp": 3, "so": 94, "sf": 3}, {"season": 2007, "player_id": 493120, "league": "NPB", "source_name": "福留　孝介", "birth_date": "1977-04-26", "role": "unknown", "pa": 348, "ab": 269, "hits": 79, "doubles": 22, "triples": 0, "hr": 13, "bb": 69, "ibb": 3, "hbp": 6, "so": 66, "sf": 4}]

Dated MLB context: []

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 150403, "source_name": "フェルナンデス", "age": 33.1615296686448, "pa": 1527, "k_rate": 0.17026850032743943, "hr_rate": 0.04977079240340537, "distance": 0.782877121260529}, {"player_id": 493115, "source_name": "新井　貴浩", "age": 30.916445922914228, "pa": 1817, "k_rate": 0.2085855806274078, "hr_rate": 0.05283434232250963, "distance": 0.926062641905243}, {"player_id": 493153, "source_name": "多村　仁", "age": 30.760385223515883, "pa": 1197, "k_rate": 0.2121971595655806, "hr_rate": 0.04344193817878028, "distance": 0.9460265555819036}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

## Yoshi Tsutsugo before 2020

Fixed case MLBAM 660294, origin 2019; NPB age at origin end 28.096401705716065. Three recent years: 1738 PA, 95 HR, 363 K and 246 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 11 distinct direct hitter movers, 4 in the same age band and 0 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2017, "player_id": 660294, "league": "NPB", "source_name": "筒香　嘉智", "birth_date": "1991-11-26", "role": "unknown", "pa": 601, "ab": 503, "hits": 143, "doubles": 31, "triples": 0, "hr": 28, "bb": 93, "ibb": 3, "hbp": 2, "so": 115, "sf": 3}, {"season": 2018, "player_id": 660294, "league": "NPB", "source_name": "筒香　嘉智", "birth_date": "1991-11-26", "role": "unknown", "pa": 580, "ab": 495, "hits": 146, "doubles": 33, "triples": 1, "hr": 38, "bb": 80, "ibb": 7, "hbp": 2, "so": 107, "sf": 3}, {"season": 2019, "player_id": 660294, "league": "NPB", "source_name": "筒香　嘉智", "birth_date": "1991-11-26", "role": "unknown", "pa": 557, "ab": 464, "hits": 126, "doubles": 24, "triples": 0, "hr": 29, "bb": 88, "ibb": 5, "hbp": 2, "so": 141, "sf": 3}]

Dated MLB context: [{"candidate_key": "2019:660294", "origin_year": 2019, "target_year": 2020, "information_date": "2020-01-25", "player_id": 660294, "player_name": "Yoshi Tsutsugo", "current_model_origin": false, "current_row_id": null, "returned_40man": true, "roster_team_ids": [139], "roster_position_codes": ["3"], "roster_cross_team_conflict": false, "roster_raw_rows": 1, "roster_duplicate_rows": 0, "roster_status_conflict": false, "eligible_mlb_team_event_records": 4, "positive_context_records": 4, "late_event_records": 0, "latest_event_date": "2019-12-16", "latest_event_kinds": ["agreement_unspecified"], "scope_exit_records": 0, "minor_agreement_records": 0, "origin_has_positive_context": true, "latest_domestic_stat_season": null, "last_domestic_source_position": "UNKNOWN", "role_status": "hitter_history_or_listing_hint", "recent_domestic_pa": 0, "recent_mlb_pa": 0, "domestic_batting_history_missing": true, "hitter_eligibility_approved": false, "complete_historical_rights_verified": false}]

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 660280, "source_name": "山田　哲人", "age": 27.45846937308774, "pa": 1902, "k_rate": 0.19558359621451105, "hr_rate": 0.04889589905362776, "distance": 0.7258457756654596}, {"player_id": 660281, "source_name": "丸　佳浩", "age": 30.722054525418045, "pa": 1848, "k_rate": 0.19913419913419914, "hr_rate": 0.04816017316017316, "distance": 1.0224080403317966}, {"player_id": 608386, "source_name": "山川　穂高", "age": 28.10461542673703, "pa": 1566, "k_rate": 0.2247765006385696, "hr_rate": 0.07215836526181353, "distance": 1.030728019577843}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

## Kensuke Tanaka before 2013

Fixed case MLBAM 547887, origin 2012; NPB age at origin end 31.617350116703285. Three recent years: 1387 PA, 9 HR, 123 K and 118 unintentional BB. Counts are raw, not park neutral or MLB equivalents.

In the actual chronological held-player fold: 4 distinct direct hitter movers, 2 in the same age band and 0 matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.

Recent actual source lines: [{"season": 2010, "player_id": 547887, "league": "NPB", "source_name": "田中　賢介", "birth_date": "1981-05-20", "role": "unknown", "pa": 662, "ab": 576, "hits": 193, "doubles": 24, "triples": 4, "hr": 5, "bb": 72, "ibb": 4, "hbp": 2, "so": 66, "sf": 5}, {"season": 2011, "player_id": 547887, "league": "NPB", "source_name": "田中　賢介", "birth_date": "1981-05-20", "role": "unknown", "pa": 220, "ab": 200, "hits": 58, "doubles": 6, "triples": 1, "hr": 1, "bb": 17, "ibb": 0, "hbp": 0, "so": 21, "sf": 1}, {"season": 2012, "player_id": 547887, "league": "NPB", "source_name": "田中　賢介", "birth_date": "1981-05-20", "role": "unknown", "pa": 505, "ab": 457, "hits": 137, "doubles": 14, "triples": 3, "hr": 3, "bb": 35, "ibb": 2, "hbp": 2, "so": 36, "sf": 3}]

Dated MLB context: [{"candidate_key": "2012:547887", "origin_year": 2012, "target_year": 2013, "information_date": "2013-01-29", "player_id": 547887, "player_name": "Kensuke Tanaka", "current_model_origin": false, "current_row_id": null, "returned_40man": false, "roster_team_ids": [], "roster_position_codes": [], "roster_cross_team_conflict": false, "roster_raw_rows": 0, "roster_duplicate_rows": 0, "roster_status_conflict": false, "eligible_mlb_team_event_records": 1, "positive_context_records": 1, "late_event_records": 0, "latest_event_date": "2013-01-11", "latest_event_kinds": ["minor_agreement"], "scope_exit_records": 0, "minor_agreement_records": 1, "origin_has_positive_context": true, "latest_domestic_stat_season": null, "last_domestic_source_position": "UNKNOWN", "role_status": "unknown", "recent_domestic_pa": 0, "recent_mlb_pa": 0, "domestic_batting_history_missing": true, "hitter_eligibility_approved": false, "complete_historical_rights_verified": false}]

Unchanged saved intermediates: []. No forecast row is fabricated when absent.

Origin-only exposure/age/K/HR peers: [{"player_id": 493114, "source_name": "青木　宣親", "age": 30.98763150509593, "pa": 1310, "k_rate": 0.08854961832061069, "hr_rate": 0.013740458015267175, "distance": 0.49730803580307315}, {"player_id": 506455, "source_name": "梵　英心", "age": 32.22242756524775, "pa": 1466, "k_rate": 0.12551159618008187, "hr_rate": 0.017053206002728513, "distance": 0.9731381019731686}, {"player_id": 506093, "source_name": "坂口　智隆", "age": 28.48518450070843, "pa": 1438, "k_rate": 0.11613351877607789, "hr_rate": 0.005563282336578581, "distance": 1.016813670228327}]. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.

Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.

