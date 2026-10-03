# Joint hitter forecast player review

The new forest uses the same 199 inputs and held-player chronological folds as the control. Targets are following-calendar-year MLB PA and batting-plus-replacement wins, not full WAR or a current prospect talent grade. Sixteen actual manual reviews follow. Outcome-selected examples diagnose mechanisms, not independent confirmation.

The three-year official count inputs retain each level separately, with recency weights 1/.8/.6 and stabilized event counts. No additional park/opponent, injury diagnosis, foreign statistics or depth chart is silently inserted. Age 27 with age_unknown=1 is a placeholder, not a known age. Captured roster flags have the separately documented dating limitation.

Neighbor selection comes from the fitted trees and origin inputs only; the subsequent outcomes are paired records already mature by the forecast cutoff. Full weights are saved per case, alongside actual inputs and all control coefficient/tree accounting. Listed outcomes include zero returns. The twelve largest weights are only an excerpt, not the entire distribution. Effective rows do not mean independent people.

## Nick Kurtz 2024 to 2025

Selection: Fixed diagnostic.

Player 701762, row 57052, fold 2; stage Upper minors; age 21.0 (unknown flag 0); listed position 3; draft year/pick 2024/4; captured 40-man 0.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 42.495 | 0.12316 |
| Joint forest | 30.142 | 0.07612 |
| Actual | 489 | 5.72099 |

Control future-active batting forecast: -0.13556 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00312416). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 14.72%, at least 400 PA 2.34%, negative contribution 3.39%, at least two contribution wins 1.92%. PA deciles/median: 0/0/103. Contribution deciles/median: 0.0000/0.0000/0.0761. The median is not expected PA.

Control pa accounting: reference 39.299703; raw prediction 42.494583. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| draft_rank | 0.817615 | 34.484966 |
| work_0 | 0.000000 | -23.699251 |
| age_centered | -1.200000 | 8.736002 |
| on_40man | 0.000000 | -6.575131 |
| pooled_AA_BB | 0.086957 | 2.004532 |
| AAA_0_pa | 0.000000 | -1.882722 |
| regular_window_scaled | 0.000000 | -1.843877 |
| pooled_MLB_BB | 0.080000 | -1.692418 |

Control rate accounting: reference -0.972293; raw prediction -0.135562. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.642920 |
| reorganized | 1.000000 | -0.276479 |
| draft_rank | 0.817615 | 0.160851 |
| position_3 | 1.000000 | 0.133637 |
| draft_known | 1.000000 | -0.089751 |
| age_squared | 1.440000 | 0.088090 |
| draft_college | 1.000000 | 0.073031 |
| pooled_A_BB | 0.533333 | 0.063729 |

The actual source is just 35 A PA and 15 AA PA, with four HR and twelve unintentional walks altogether, plus age 21 and pick 4. The control's largest positive PA accounting term is draft rank, not an established professional track record. The joint forest gives 14.7% participation, 30 expected PA and a zero median; its high-weight outcomes include Crews' 132 PA but also Davis, Bohm, Cowser, India and several high-school draftees with no next-year MLB PA. The distribution includes plausible unsuccessful comparisons, but mixes age/level histories too broadly to establish a precise advanced-college readiness estimate. Two unnamed rows have placeholder age 27, and Kjerstad's inactive 2021 row is a prominent neighbor; that is missing history, not evidence Kurtz belongs to an age-27 inactive population. The actual 489 PA and 5.72 batting-plus-replacement wins exceed the 90th percentiles of 103 PA and 0.076 wins. This is a substantial miss in both arrival timing and contribution, not fixed by supplying an upside probability. Earlier early-draft cohorts are small and mostly do not arrive immediately, so the miss does not justify assigning all top selections Kurtz's outcome or calling his longer-run value zero.

Distinct-player profile support: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1744}]. Weighted distribution: 1360 people, effective rows 182.51, latest contributing target year 2024. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Unnamed source player 677008 | 2021 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01605 |
| Termarr Johnson | 2022 | 18.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01584 |
| Dylan Crews | 2023 | 21.0 | 0 / 0.0 / 85.0 | 132 | 0.13193 | 0.01521 |
| Henry Davis | 2021 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01366 |
| Alec Bohm | 2018 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01339 |
| Marcelo Mayer | 2021 | 18.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01315 |
| Unnamed source player 702258 | 2022 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01275 |
| Colton Cowser | 2021 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01271 |
| Jonathan India | 2018 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01264 |
| Jacob Berry | 2022 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01255 |
| Brendan McKay | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01206 |
| Nick Madrigal | 2018 | 21.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.01183 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): 677008 (2021, weight 0.01605); Termarr Johnson (2022, weight 0.01584); Henry Davis (2021, weight 0.01366); Alec Bohm (2018, weight 0.01339); Marcelo Mayer (2021, weight 0.01315).

## Heston Kjerstad 2023 to 2024

Selection: Fixed diagnostic.

Player 677008, row 51807, fold 1; stage Current MLB; age 24.0 (unknown flag 0); listed position 9; draft year/pick 2020/2; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 98 | 2 | 17 | 12 |
| 2022 | Aplus | 186 | 3 | 47 | 16 |
| 2023 | AA | 206 | 11 | 31 | 15 |
| 2023 | AAA | 337 | 10 | 69 | 26 |
| 2023 | MLB | 33 | 2 | 10 | 2 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 261.967 | 0.90814 |
| Joint forest | 191.270 | 0.60062 |
| Actual | 114 | 0.47709 |

Control future-active batting forecast: 0.22232 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00309608). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 86.72%, at least 400 PA 17.31%, negative contribution 31.08%, at least two contribution wins 12.57%. PA deciles/median: 0/137/486. Contribution deciles/median: -0.3079/0.0805/2.2531. The median is not expected PA.

Control pa accounting: reference 40.158995; raw prediction 261.967012. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 93.638287 |
| draft_rank | 0.908807 | 78.498701 |
| pooled_AA_HR | 0.045752 | 34.556219 |
| pooled_AA_pa | 206.000000 | 15.697279 |
| age_centered | -0.600000 | 12.007027 |
| AA_0_pa | 206.000000 | 10.352667 |
| MLB_0_pa | 33.000000 | -7.742313 |
| pooled_mlb_quality | -0.011299 | -7.431207 |

Control rate accounting: reference -0.785423; raw prediction 0.222318. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.342300 |
| reorganized | 1.000000 | -0.195725 |
| draft_rank | 0.908807 | 0.170059 |
| pooled_A_BABIP | 0.877005 | 0.154735 |
| position_9 | 1.000000 | 0.154160 |
| draft_college | 1.000000 | 0.141676 |
| pooled_AAA_BABIP | 0.385580 | 0.118372 |
| prior_debut | 1.000000 | 0.096121 |

His source has 206 AA and 337 AAA PA with 21 HR in 2023, followed by only 33 MLB PA. The control allocates strong PA credit to the captured 40-man flag and draft rank. The empirical neighborhood instead includes both Turner/Souza-type opportunity and Walker's 12 PA, plus non-returning Heathcott and Clark; there is no known Orioles depth-chart input. Mean PA falls from 262 to 191, median is 137 and actual is 114. Contribution falls from 0.908 to 0.601 against 0.477 actual. Both quantities improve here without pretending the brief MLB sample erases the upper-minor evidence. Catchers among the neighbors show that this is learned statistical similarity, not a hand-curated position-matched scouting list. The broad profile has 290 distinct players, but that does not establish fine-grained team-job or disease-history support. The probability/range is more informative than a single number; this good case does not cancel upper-minor underallocation elsewhere.

Distinct-player profile support: [{'row_id': 51807, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 290}]. Weighted distribution: 718 people, effective rows 426.64, latest contributing target year 2023. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Trea Turner | 2015 | 22.0 | 44 / 205.0 / 295.0 | 324 | 3.16757 | 0.00852 |
| Reese McGuire | 2018 | 23.0 | 33 / 369.0 / 0.0 | 105 | 0.70817 | 0.00794 |
| Royce Lewis | 2022 | 23.0 | 41 / 153.0 / 0.0 | 239 | 2.25307 | 0.00762 |
| Steven Souza Jr. | 2014 | 25.0 | 26 / 407.0 / 0.0 | 426 | 1.53522 | 0.00731 |
| Scott Schebler | 2015 | 24.0 | 40 / 485.0 / 0.0 | 282 | 1.12255 | 0.00691 |
| Ryan Lavarnway | 2011 | 23.0 | 43 / 264.0 / 239.0 | 166 | -0.92590 | 0.00648 |
| Devin Mesoraco | 2011 | 23.0 | 53 / 499.0 / 0.0 | 184 | -0.06788 | 0.00629 |
| Christian Walker | 2014 | 23.0 | 19 / 188.0 / 411.0 | 12 | -0.02310 | 0.00615 |
| Francisco Alvarez | 2022 | 20.0 | 14 / 199.0 / 296.0 | 423 | 1.06142 | 0.00610 |
| Matt Wallner | 2022 | 24.0 | 65 / 229.0 / 342.0 | 254 | 2.02992 | 0.00585 |
| Nick Castellanos | 2013 | 21.0 | 18 / 595.0 / 0.0 | 579 | 1.74834 | 0.00556 |
| Tyler Stephenson | 2020 | 23.0 | 20 / 0.0 / 0.0 | 402 | 2.39083 | 0.00547 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Slade Heathcott (2015, weight 0.00478); Matt Clark (2014, weight 0.00460); Brandon Guyer (2012, weight 0.00370); Chris McGuiness (2013, weight 0.00308); Travis Swaggerty (2022, weight 0.00289).

## Jake Burger 2021 to 2022

Selection: Fixed diagnostic.

Player 669394, row 43601, fold 4; stage Current MLB; age 25.0 (unknown flag 0); listed position 5; draft year/pick 2017/11; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 340 | 18 | 91 | 23 |
| 2021 | MLB | 42 | 1 | 15 | 4 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 144.420 | 0.41523 |
| Joint forest | 157.960 | 0.35041 |
| Actual | 183 | 0.77702 |

Control future-active batting forecast: -0.15591 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00313500). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 87.59%, at least 400 PA 10.50%, negative contribution 36.12%, at least two contribution wins 5.27%. PA deciles/median: 0/104/406. Contribution deciles/median: -0.3049/0.0184/1.3800. The median is not expected PA.

Control pa accounting: reference 38.249895; raw prediction 144.419682. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 94.629053 |
| pooled_MLB_K | 0.267606 | -12.921480 |
| MLB_0_pa | 42.000000 | 10.502316 |
| quality_0 | 0.054996 | 6.795318 |
| draft_rank | 0.684525 | 6.766831 |
| pooled_MLB_2B | 0.056338 | 6.533636 |
| work_0 | 42.017291 | -4.362681 |
| pooled_AAA_HR | 0.047727 | 4.025144 |

Control rate accounting: reference -0.852237; raw prediction -0.155912. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -0.400000 | 0.228697 |
| pooled_AAA_HR | 0.177273 | 0.111167 |
| position_5 | 1.000000 | 0.107074 |
| prior_debut | 1.000000 | 0.096991 |
| draft_class_unknown | 1.000000 | -0.094576 |
| work_0 | 42.017291 | 0.059833 |
| AAA_0_pa | 0.566667 | 0.054573 |
| pooled_AAA_BABIP | 0.201320 | 0.050317 |

The known professional history within the three-year window is 340 AAA PA, 18 HR and 91 K plus 42 MLB PA with 15 K. Earlier absence is not encoded as a diagnosed injury, and the canceled 2020 MiLB season is not a poor-performance sample. Control PA is driven mainly by 40-man listing, with a negative stabilized MLB strikeout contribution. Weighted neighbors span Goodwin's 278, Cooper's 38, Cozens' one and Brentz's zero next-year PA. Mean PA rises from 144 to 158 toward actual 183, but mean contribution falls from 0.415 to 0.350 away from actual 0.777. The joint mean's implied yield is therefore weaker even as opportunity improves. This is a genuine opportunity gain and performance tradeoff, not an overall player-value improvement or a validated reconstruction of Burger's medical recovery.

Distinct-player profile support: [{'row_id': 43601, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 422}]. Weighted distribution: 656 people, effective rows 368.14, latest contributing target year 2021. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Brian Goodwin | 2016 | 25.0 | 44 / 492.0 / 0.0 | 278 | 1.25449 | 0.01113 |
| Garrett Cooper | 2017 | 26.0 | 45 / 327.0 / 23.0 | 38 | -0.03187 | 0.01013 |
| Clint Frazier | 2018 | 23.0 | 41 / 216.0 / 0.0 | 246 | 1.06931 | 0.00958 |
| Christian Colón | 2014 | 25.0 | 49 / 388.0 / 9.0 | 119 | 0.38321 | 0.00946 |
| Dylan Cozens | 2018 | 24.0 | 44 / 348.0 / 0.0 | 1 | -0.02388 | 0.00852 |
| Andrew Lambo | 2013 | 24.0 | 33 / 254.0 / 247.0 | 39 | 0.00126 | 0.00795 |
| Tom Murphy | 2015 | 24.0 | 39 / 136.0 / 294.0 | 49 | 0.56454 | 0.00710 |
| Garrett Hampson | 2018 | 23.0 | 48 / 332.0 / 172.0 | 327 | 0.21381 | 0.00707 |
| Bryce Brentz | 2014 | 25.0 | 26 / 267.0 / 0.0 | 0 | 0.00000 | 0.00649 |
| Blake Tekotte | 2011 | 24.0 | 40 / 0.0 / 498.0 | 15 | -0.19228 | 0.00647 |
| Mitch Garver | 2017 | 26.0 | 52 / 372.0 / 0.0 | 335 | 1.31699 | 0.00643 |
| Alex Liddi | 2011 | 22.0 | 44 / 637.0 / 0.0 | 126 | 0.04043 | 0.00637 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Bryce Brentz (2014, weight 0.00649); Andy Wilkins (2014, weight 0.00542); Mike Olt (2012, weight 0.00449); Matt Davidson (2013, weight 0.00376); Jeremy Hazelbaker (2017, weight 0.00295).

## Anthony Volpe 2022 to 2023

Selection: Fixed diagnostic.

Player 683011, row 48516, fold 4; stage Upper minors; age 21.0 (unknown flag 0); listed position 6; draft year/pick 2019/30; captured 40-man 0.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 257 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 15 | 58 | 26 |
| 2022 | AA | 497 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 3 | 30 | 8 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 82.525 | 0.23807 |
| Joint forest | 66.109 | 0.24178 |
| Actual | 601 | 0.51373 |

Control future-active batting forecast: -0.14770 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00313097). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 35.46%, at least 400 PA 5.52%, negative contribution 10.91%, at least two contribution wins 4.70%. PA deciles/median: 0/0/273. Contribution deciles/median: -0.0251/0.0000/1.0452. The median is not expected PA.

Control pa accounting: reference 38.768214; raw prediction 82.524648. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -22.818125 |
| pooled_A_3B | 0.014725 | 21.690618 |
| age_centered | -1.200000 | 12.033576 |
| pooled_AAA_BABIP | 0.307692 | 11.688254 |
| draft_rank | 0.552527 | 9.261965 |
| on_40man | 0.000000 | -5.981171 |
| pooled_AA_K | 0.185930 | 5.933202 |
| pooled_A_2B | 0.063482 | -5.203496 |

Control rate accounting: reference -0.851468; raw prediction -0.147697. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -1.200000 | 0.679419 |
| position_6 | 1.000000 | -0.248138 |
| pooled_A_BB | 0.796859 | 0.235365 |
| reorganized | 1.000000 | -0.138872 |
| draft_class_unknown | 1.000000 | -0.124039 |
| age_squared | 1.440000 | 0.120673 |
| pooled_AA_BABIP | -0.216981 | -0.081557 |
| AA_0_pa | 0.828333 | 0.072831 |

He had 513 A/Aplus PA in 2021 and 497 AA plus 99 AAA PA in 2022, including 21 HR and 65 unintentional walks that last year. The control retains minor production and age but receives no MLB workload or captured 40-man membership. The joint neighborhood includes young upper-minor players with delayed starts or brief first opportunities: Casas 95 PA, Rodgers 81, Frazier 142, but also Guerrero 514 and Thomas 411. Winker, Cowart and Turang contribute actual zeros. These are origin-feature-selected outcomes, not comparisons cherry-picked for success. Joint mean PA falls 83 to 66, with 35.5% participation and only 5.5% chance of 400 PA; actual is 601. Contribution happens to be slightly closer (0.242 versus control 0.238, actual 0.514), but that masks severely wrong opportunity. A future MLB batting grade and a next-year chance of receiving the Yankees' shortstop job are different targets; the former alone does not repair this miss.

Distinct-player profile support: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1502}]. Weighted distribution: 1146 people, effective rows 467.75, latest contributing target year 2022. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Triston Casas | 2021 | 21.0 | 0 / 42.0 / 329.0 | 95 | 0.57970 | 0.00902 |
| Brendan Rodgers | 2018 | 21.0 | 0 / 72.0 / 402.0 | 81 | -0.33082 | 0.00770 |
| Matt Davidson | 2012 | 21.0 | 0 / 0.0 / 576.0 | 87 | 0.42073 | 0.00719 |
| Clint Frazier | 2016 | 21.0 | 0 / 129.0 / 391.0 | 142 | 0.20776 | 0.00670 |
| Jesse Winker | 2015 | 21.0 | 0 / 0.0 / 526.0 | 0 | 0.00000 | 0.00602 |
| Alek Thomas | 2021 | 21.0 | 0 / 166.0 / 329.0 | 411 | 0.06125 | 0.00591 |
| Kaleb Cowart | 2013 | 21.0 | 0 / 0.0 / 546.0 | 0 | 0.00000 | 0.00585 |
| Vladimir Guerrero Jr. | 2018 | 19.0 | 0 / 128.0 / 266.0 | 514 | 2.07804 | 0.00579 |
| Jaff Decker | 2011 | 21.0 | 0 / 0.0 / 613.0 | 0 | 0.00000 | 0.00579 |
| Brice Turang | 2021 | 21.0 | 0 / 176.0 / 320.0 | 0 | 0.00000 | 0.00566 |
| Kolten Wong | 2012 | 21.0 | 0 / 0.0 / 579.0 | 62 | -0.52043 | 0.00561 |
| Oscar Taveras | 2012 | 20.0 | 0 / 0.0 / 531.0 | 0 | 0.00000 | 0.00536 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Jesse Winker (2015, weight 0.00602); Kaleb Cowart (2013, weight 0.00585); Jaff Decker (2011, weight 0.00579); Brice Turang (2021, weight 0.00566); Oscar Taveras (2012, weight 0.00536).

## Aaron Judge 2016 to 2017

Selection: Fixed diagnostic; value false low.

Player 592450, row 23934, fold 3; stage Current MLB; age 24.0 (unknown flag 0); listed position 9; draft year/pick 2013/32; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 143.966 | 0.43085 |
| Joint forest | 189.635 | 0.56625 |
| Actual | 678 | 8.10841 |

Control future-active batting forecast: -0.05720 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00308809). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 87.60%, at least 400 PA 16.48%, negative contribution 34.09%, at least two contribution wins 13.24%. PA deciles/median: 0/129/499. Contribution deciles/median: -0.3629/0.0683/2.3255. The median is not expected PA.

Control pa accounting: reference 38.360689; raw prediction 143.965611. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| on_40man | 1.000000 | 72.971051 |
| MLB_0_pa | 95.000000 | 27.203824 |
| age_centered | -0.600000 | 13.668747 |
| pooled_MLB_K | 0.333333 | -9.543102 |
| pooled_A_3B | 0.006372 | 7.595328 |
| quality_0 | -0.175091 | -6.734861 |
| pooled_AA_BABIP | 0.326014 | -6.403581 |
| pooled_Aplus_BB | 0.138007 | 6.237603 |

Control rate accounting: reference -0.746346; raw prediction -0.057204. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -0.600000 | 0.286822 |
| draft_class_unknown | 1.000000 | -0.204214 |
| position_9 | 1.000000 | 0.165561 |
| pooled_mlb_quality | -0.175091 | -0.119076 |
| pooled_Aplus_BB | 0.580074 | 0.113202 |
| pooled_Aplus_BABIP | 0.367983 | 0.090674 |
| work_0 | 95.078254 | 0.083463 |
| AA_1_pa | 0.466667 | -0.078361 |

The source carries multiple productive minor years, including 410 AAA PA and 19 HR in 2016, alongside a very rough 95-PA MLB debut with 42 K. The stabilized debut K remains high, while draft class is missing for his vintage. Control PA accounting credits 40-man membership and the debut but penalizes the high MLB K rate; its rate is near league average rather than predicting a superstar. The joint forest assigns weight to both Rizzo/Pillar outcomes and Johnson/Pompey/Gallo limited follow-up, plus zero outcomes such as Sands and Vitters. It moves PA 144 to 190 and contribution 0.431 to 0.566, improving a large miss but remaining nowhere near actual 678 and 8.108. Both actuals are above the saved 90th-percentile bounds (499 PA, 2.326 wins). The model does not isolate Judge's later adjustment or infer physical traits not in its inputs. A 13.2% chance of two batting-contribution wins recognizes some upside but does not demonstrate that the breakout tail is appropriately estimated.

Distinct-player profile support: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': 'brief', 'draft_known': 1, 'profile_players': 141}]. Weighted distribution: 429 people, effective rows 214.15, latest contributing target year 2016. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Micah Johnson | 2015 | 24.0 | 114 / 353.0 / 0.0 | 6 | -0.06563 | 0.01538 |
| Ryan Rua | 2015 | 25.0 | 86 / 165.0 / 0.0 | 269 | 0.82884 | 0.01360 |
| Jimmy Paredes | 2012 | 23.0 | 82 / 536.0 / 0.0 | 135 | -0.63185 | 0.01300 |
| Joey Gallo | 2015 | 21.0 | 123 / 228.0 / 146.0 | 30 | -0.23895 | 0.01213 |
| Kevin Pillar | 2014 | 25.0 | 122 / 434.0 / 0.0 | 628 | 1.84859 | 0.01173 |
| Matt Adams | 2012 | 23.0 | 91 / 276.0 / 0.0 | 319 | 2.38344 | 0.01158 |
| Dalton Pompey | 2015 | 22.0 | 103 / 295.0 / 148.0 | 2 | -0.04640 | 0.01125 |
| Anthony Rizzo | 2011 | 21.0 | 153 / 413.0 / 0.0 | 368 | 2.27323 | 0.01105 |
| Kolten Wong | 2013 | 22.0 | 62 / 463.0 / 0.0 | 433 | 0.86732 | 0.01098 |
| Jordan Pacheco | 2011 | 25.0 | 88 / 411.0 / 0.0 | 505 | 2.32552 | 0.01077 |
| Dave Sappelt | 2011 | 24.0 | 118 / 336.0 / 0.0 | 78 | 0.40780 | 0.01045 |
| James Darnell | 2011 | 24.0 | 52 / 155.0 / 346.0 | 19 | 0.10358 | 0.01026 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Matt Angle (2011, weight 0.00552); Mike Olt (2015, weight 0.00551); Jerry Sands (2012, weight 0.00486); Josh Vitters (2012, weight 0.00482); Joey Terdoslavich (2015, weight 0.00481).

## Aaron Judge 2024 to 2025

Selection: Fixed diagnostic.

Player 592450, row 54849, fold 3; stage Current MLB; age 32.0 (unknown flag 0); listed position 8; draft year/pick 2013/32; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 548.496 | 5.87607 |
| Joint forest | 603.543 | 5.21625 |
| Actual | 679 | 9.23105 |

Control future-active batting forecast: 4.55334 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00312416). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.22%, at least 400 PA 90.82%, negative contribution 0.10%, at least two contribution wins 90.16%. PA deciles/median: 426/657/707. Contribution deciles/median: 2.2585/5.4489/7.6335. The median is not expected PA.

Control pa accounting: reference 39.316467; raw prediction 548.495726. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 704.289831 | 349.200542 |
| pooled_mlb_quality | 3.648566 | 59.624652 |
| quality_0 | 2.794425 | 38.851972 |
| regular_window_scaled | 1.000000 | 28.647865 |
| work_2 | 696.000000 | 23.835761 |
| age_centered | 1.000000 | -23.717465 |
| MLB_0_pa | 704.000000 | 16.915036 |
| pooled_MLB_pa | 1488.000000 | 12.057541 |

Control rate accounting: reference -0.912484; raw prediction 4.553340. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 3.648566 | 2.685922 |
| quality_0 | 2.794425 | 1.297297 |
| work_0 | 704.289831 | 0.841611 |
| age_centered | 1.000000 | -0.558514 |
| quality_2 | 2.408333 | 0.477308 |
| work_2 | 696.000000 | 0.414097 |
| quality_1 | 1.317130 | 0.285426 |
| reorganized | 1.000000 | -0.276917 |

The source has 696/458/704 MLB PA and 62/37/58 HR across 2022-24. The control's saved linear terms preserve strong pooled and recent MLB hitting and yield 4.553 batting wins per 600 PA. Its expected contribution is 5.876 at 548 PA. Joint mean PA improves to 604 toward 679 actual, but contribution drops to 5.216 against 9.231 actual. The most weighted outcomes include Goldschmidt, Martinez, Freeman, Soto and several Trout years, with smaller retirement/injury zeros. A forest average of past comparable outcomes limits extrapolation; the model substitutes a mixed observed trajectory distribution for the separate talent head. The actual contribution is above its 7.633-win 90th percentile despite the actual PA falling inside the 426-707 range. This is an elite batting compression problem, not a playing-time success that validates the combined forecast. Repeated Trout seasons are not independent people; effective weighted rows and distinct people are reported separately.

Distinct-player profile support: [{'row_id': 54849, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 87}]. Weighted distribution: 123 people, effective rows 96.11, latest contributing target year 2024. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Paul Goldschmidt | 2015 | 27.0 | 695 / 0.0 / 0.0 | 705 | 5.63285 | 0.02440 |
| Mike Trout | 2018 | 26.0 | 608 / 0.0 / 0.0 | 600 | 7.40881 | 0.02364 |
| J.D. Martinez | 2018 | 30.0 | 649 / 0.0 / 0.0 | 657 | 5.54230 | 0.02136 |
| Freddie Freeman | 2023 | 33.0 | 730 / 0.0 / 0.0 | 638 | 4.74237 | 0.02076 |
| Mike Trout | 2016 | 24.0 | 681 / 0.0 / 0.0 | 507 | 6.09429 | 0.02004 |
| Juan Soto | 2021 | 22.0 | 654 / 0.0 / 0.0 | 664 | 5.61671 | 0.01972 |
| Mike Trout | 2014 | 22.0 | 705 / 0.0 / 0.0 | 682 | 7.51491 | 0.01940 |
| Mike Trout | 2015 | 23.0 | 682 / 0.0 / 0.0 | 681 | 7.57758 | 0.01936 |
| Mookie Betts | 2023 | 30.0 | 693 / 0.0 / 0.0 | 516 | 4.22820 | 0.01916 |
| Charlie Blackmon | 2017 | 30.0 | 725 / 0.0 / 0.0 | 696 | 5.28506 | 0.01659 |
| Mike Trout | 2013 | 21.0 | 716 / 0.0 / 0.0 | 705 | 7.39491 | 0.01622 |
| Joey Votto | 2015 | 31.0 | 695 / 0.0 / 0.0 | 677 | 7.14610 | 0.01611 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): David Ortiz (2016, weight 0.00398); Fernando Tatis Jr. (2021, weight 0.00300); Corey Hart (2012, weight 0.00049); Rhys Hoskins (2022, weight 0.00033).

## Hyeseong Kim 2024 to 2025

Selection: Source-risk case discovered during fixed fits; no outcome-based eligibility change.

Player 808975, row 58060, fold 4; stage Inactive / unknown; age 27.0 (unknown flag 1); listed position UNKNOWN; draft year/pick None/None; captured 40-man 0.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| No observed own batting history by cutoff | Unknown | — | — | — | — |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 0.000 | 0.00000 |
| Joint forest | 0.000 | 0.00000 |
| Actual | 170 | 0.43287 |

Control future-active batting forecast: -1.20498 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00312416). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 0.00%, at least 400 PA 0.00%, negative contribution 0.00%, at least two contribution wins 0.00%. PA deciles/median: 0/0/0. Contribution deciles/median: 0.0000/0.0000/0.0000. The median is not expected PA.

Control pa accounting: reference 39.700981; raw prediction -1.070649. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 0.000000 | -21.555119 |
| on_40man | 0.000000 | -6.523590 |
| regular_window_scaled | 0.000000 | -2.147387 |
| MLB_0_pa | 0.000000 | -1.986919 |
| pooled_mlb_quality | 0.000000 | -1.239851 |
| quality_0 | 0.000000 | -0.689297 |
| work_1 | 0.000000 | -0.685827 |
| draft_rank | 0.000000 | -0.638577 |

Control rate accounting: reference -0.902660; raw prediction -1.204978. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| reorganized | 1.000000 | -0.212707 |
| draft_class_unknown | 1.000000 | -0.083230 |
| position_UNKNOWN | 1.000000 | 0.033997 |
| absence_window_scaled | 1.000000 | -0.027648 |
| elapsed_scaled | -0.100000 | -0.010351 |
| last_stat_gap | 1.000000 | -0.002378 |
| on_40man | 0.000000 | 0.000000 |
| age_unknown | 1.000000 | 0.000000 |

The actual model row has no dated affiliated batting history, no draft selection, unknown name/position/organization, age_unknown=1 and placeholder age 27. The raw retrospective full-roster request lists him with the Dodgers under an October 2024 requested date, but the dated January 2025 signing announcement contradicts treating that response as an October Dodgers membership snapshot. The model's 40-man flag is zero; do not attribute this defect to the separate 40-man source. Control raw PA is negative and clipped to zero; the forest's very large inactive empirical neighborhood also has exclusively zero future MLB PA and contribution for this input path. It therefore assigns exactly zero participation and zero range against actual 170 PA and 0.433 contribution wins. This is not confidence that a known KBO player cannot hit: KBO evidence, posting eligibility and correctly dated membership are absent. Keep him in primary scoring, qualify this eligibility/source row, and do not drop all unverified international signings merely because the pipeline cannot establish their histories.

Distinct-player profile support: [{'row_id': 58060, 'stage': 'Inactive / unknown', 'prior_debut': 0, 'age_band': 5.0, 'current_work_band': 'absent', 'draft_known': 0, 'profile_players': 260}]. Weighted distribution: 11381 people, effective rows 23685.90, latest contributing target year 2024. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Logan Wade | 2023 | 31.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Christopher Rodriguez | 2023 | 23.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Oscar Olivares | 2023 | 24.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Jose Aguilar | 2023 | 22.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 691944 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 700265 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 805136 | 2023 | 22.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 805324 | 2023 | 18.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 806754 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 806958 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 808112 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |
| Unnamed source player 808309 | 2023 | 27.0 | 0 / 0.0 / 0.0 | 0 | 0.00000 | 0.00006 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Logan Wade (2023, weight 0.00006); Christopher Rodriguez (2023, weight 0.00006); Oscar Olivares (2023, weight 0.00006); Jose Aguilar (2023, weight 0.00006); 691944 (2023, weight 0.00006).

## Matt McLain 2023 to 2024

Selection: pa largest gain.

Player 680574, row 51984, fold 2; stage Current MLB; age 23.0 (unknown flag 0); listed position 6; draft year/pick 2021/17; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2021 | Aplus | 119 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 0 | 0 | 0 |
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 561.901 | 2.56818 |
| Joint forest | 456.747 | 2.09910 |
| Actual | 0 | 0.00000 |

Control future-active batting forecast: 0.88467 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00309608). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 98.53%, at least 400 PA 67.82%, negative contribution 8.93%, at least two contribution wins 48.76%. PA deciles/median: 197/490/665. Contribution deciles/median: 0.0000/1.9365/4.1737. The median is not expected PA.

Control pa accounting: reference 39.120812; raw prediction 561.901395. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 403.000000 | 266.373658 |
| age_centered | -0.800000 | 65.589750 |
| quality_0 | 0.672812 | 42.318393 |
| pooled_mlb_quality | 0.672812 | 32.869643 |
| pooled_AAA_HR | 0.053571 | 30.573945 |
| regular_window_scaled | 0.333333 | 30.526850 |
| on_40man | 1.000000 | 22.716499 |
| pooled_MLB_K | 0.274354 | -19.008612 |

Control rate accounting: reference -0.951149; raw prediction 0.884667. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 0.672812 | 0.519938 |
| work_0 | 403.000000 | 0.513726 |
| age_centered | -0.800000 | 0.430328 |
| quality_0 | 0.672812 | 0.321554 |
| position_6 | 1.000000 | -0.294284 |
| prior_debut | 1.000000 | 0.207816 |
| pooled_AA_BB | 0.569151 | 0.199951 |
| reorganized | 1.000000 | -0.197988 |

The known sequence is 452 AA PA in 2022, then 180 AAA PA with 12 HR and 403 MLB PA with 16 HR in 2023 at age 23. Control expected PA is high (562), with positive saved workload, young-age and production terms. The forest averages rookie/young regular trajectories including Story, Rutschman, Harris and DeJong, but also Santana's poorer follow-up and a small number of zero outcomes. It lowers expected PA to 457 and contribution to 2.099 from 2.568, reducing error against actual zero. Yet it gives 98.5% participation and a 197-665 PA central range, which completely misses the absence. No pre-origin diagnosed shoulder event is present in this tested feature branch. This largest PA improvement is largely an outcome-selected gain from general regression, not evidence that the model foresaw his future absence. Do not add later medical information to a 2023-origin forecast.

Distinct-player profile support: [{'row_id': 51984, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 82}]. Weighted distribution: 471 people, effective rows 258.00, latest contributing target year 2023. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Trevor Story | 2016 | 23.0 | 415 / 0.0 / 0.0 | 555 | 1.83625 | 0.01890 |
| Adley Rutschman | 2022 | 24.0 | 470 / 53.0 / 14.0 | 687 | 3.95739 | 0.01555 |
| Michael Harris II | 2022 | 21.0 | 441 / 0.0 / 196.0 | 539 | 2.86981 | 0.01427 |
| Danny Santana | 2014 | 23.0 | 430 / 105.0 / 0.0 | 277 | -1.07566 | 0.01285 |
| Aledmys Díaz | 2016 | 25.0 | 460 / 0.0 / 0.0 | 301 | 0.20232 | 0.01189 |
| Paul DeJong | 2017 | 23.0 | 443 / 190.0 / 0.0 | 490 | 1.78822 | 0.01148 |
| George Springer | 2015 | 25.0 | 451 / 0.0 / 20.0 | 744 | 4.61335 | 0.01046 |
| Randal Grichuk | 2015 | 23.0 | 350 / 0.0 / 0.0 | 478 | 1.86556 | 0.00970 |
| Vinnie Pasquantino | 2022 | 24.0 | 298 / 313.0 / 0.0 | 260 | 0.94343 | 0.00915 |
| Miguel Sanó | 2015 | 22.0 | 335 / 0.0 / 286.0 | 495 | 2.27665 | 0.00873 |
| Shohei Ohtani | 2018 | 23.0 | 367 / 0.0 / 0.0 | 425 | 2.48391 | 0.00811 |
| Francisco Lindor | 2015 | 21.0 | 438 / 262.0 / 0.0 | 684 | 3.42594 | 0.00808 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Jung Ho Kang (2016, weight 0.00510); Scott Sizemore (2011, weight 0.00122); Greg Bird (2015, weight 0.00117); David Dahl (2016, weight 0.00113); Buster Posey (2021, weight 0.00084).

## David Ortiz 2016 to 2017

Selection: pa largest harm.

Player 120074, row 22760, fold 4; stage Current MLB; age 40.0 (unknown flag 0); listed position 10; draft year/pick None/None; captured 40-man 0.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2014 | MLB | 602 | 35 | 95 | 53 |
| 2015 | MLB | 614 | 37 | 95 | 61 |
| 2016 | MLB | 626 | 38 | 86 | 65 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 336.588 | 2.36600 |
| Joint forest | 525.169 | 3.77666 |
| Actual | 0 | 0.00000 |

Control future-active batting forecast: 2.36476 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00308809). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 94.92%, at least 400 PA 75.93%, negative contribution 2.95%, at least two contribution wins 71.23%. PA deciles/median: 203/619/695. Contribution deciles/median: 0.3821/3.7384/7.0661. The median is not expected PA.

Control pa accounting: reference 38.719675; raw prediction 336.588439. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 626.000000 | 211.886478 |
| age_centered | 2.600000 | -98.018778 |
| work_0 | 626.515651 | 92.616782 |
| on_40man | 0.000000 | -51.558750 |
| quality_0 | 1.612991 | 50.000439 |
| regular_window_scaled | 1.000000 | 48.554777 |
| pooled_mlb_quality | 1.930947 | 25.388997 |
| quality_1 | 0.968419 | 18.033475 |

Control rate accounting: reference -0.537526; raw prediction 2.364757. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 1.930947 | 1.387395 |
| age_centered | 2.600000 | -1.133839 |
| quality_0 | 1.612991 | 0.752917 |
| work_2 | 602.000000 | 0.583216 |
| work_0 | 626.515651 | 0.455178 |
| age_squared | 6.760000 | 0.314124 |
| quality_1 | 0.968419 | 0.231436 |
| draft_class_unknown | 1.000000 | -0.219583 |

Actual known counts are 602/614/626 MLB PA and 35/37/38 HR over three years at age 40. The control gives negative accounting terms to age and absent captured 40-man membership but still predicts 337 PA and 2.366 contribution wins. The joint neighborhood is dominated by much younger strong hitters such as Bautista, Braun, Beltre, Cruz and Fielder; the exact age/workload/draft profile contains just two distinct training people. It raises the forecast to 525 PA and 3.777 wins with 94.9% participation, although actual is zero. Several known retirements enter as small zero neighbors, but no dated announced-retirement state is in either forecast. This is a source/context omission that ordinary batting regression should not be asked to solve, plus sparse age extrapolation; it is not evidence the good 2016 hitting counts are wrong. Investigate a consistent dated retirement ledger for all eligible players, not an Ortiz-only after-the-fact exception. An announcement can be reversed, so any rule must handle dated returns rather than equate retirement with permanent ineligibility.

Distinct-player profile support: [{'row_id': 22760, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 8.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 2}]. Weighted distribution: 188 people, effective rows 118.95, latest contributing target year 2016. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| José Bautista | 2014 | 33.0 | 673 / 0.0 / 0.0 | 666 | 6.31276 | 0.01793 |
| José Bautista | 2011 | 30.0 | 655 / 0.0 / 0.0 | 399 | 3.34299 | 0.01762 |
| Ryan Braun | 2011 | 27.0 | 629 / 0.0 / 0.0 | 677 | 7.25388 | 0.01710 |
| Adrian Beltré | 2012 | 33.0 | 654 / 0.0 / 0.0 | 690 | 5.59090 | 0.01659 |
| José Bautista | 2015 | 34.0 | 666 / 0.0 / 0.0 | 517 | 3.28941 | 0.01647 |
| Prince Fielder | 2011 | 27.0 | 692 / 0.0 / 0.0 | 690 | 6.53532 | 0.01617 |
| Ryan Braun | 2012 | 28.0 | 677 / 0.0 / 0.0 | 253 | 1.80345 | 0.01593 |
| Nelson Cruz | 2015 | 34.0 | 655 / 0.0 / 0.0 | 667 | 5.68494 | 0.01578 |
| Joey Votto | 2013 | 29.0 | 726 / 0.0 / 0.0 | 272 | 1.99420 | 0.01534 |
| Andrew McCutchen | 2014 | 27.0 | 648 / 0.0 / 0.0 | 685 | 5.78990 | 0.01484 |
| Josh Hamilton | 2012 | 31.0 | 636 / 0.0 / 0.0 | 636 | 2.30773 | 0.01482 |
| Matt Holliday | 2013 | 33.0 | 602 / 0.0 / 0.0 | 667 | 4.93088 | 0.01451 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Derrek Lee (2011, weight 0.00522); Adam Dunn (2014, weight 0.00456); Victor Martinez (2011, weight 0.00419); Vladimir Guerrero (2011, weight 0.00387); Torii Hunter (2015, weight 0.00384).

## Rhys Hoskins 2022 to 2023

Selection: pa false high.

Player 656555, row 46991, fold 4; stage Current MLB; age 29.0 (unknown flag 0); listed position 3; draft year/pick 2014/142; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 185 | 10 | 43 | 29 |
| 2021 | MLB | 443 | 27 | 108 | 47 |
| 2022 | MLB | 672 | 30 | 169 | 72 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 532.755 | 3.06482 |
| Joint forest | 564.789 | 3.42058 |
| Actual | 0 | 0.00000 |

Control future-active batting forecast: 1.57308 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00313097). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.73%, at least 400 PA 86.19%, negative contribution 2.70%, at least two contribution wins 74.37%. PA deciles/median: 334/615/696. Contribution deciles/median: 0.7901/3.4880/5.8677. The median is not expected PA.

Control pa accounting: reference 38.768214; raw prediction 532.754921. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 672.000000 | 337.859070 |
| pooled_mlb_quality | 1.061868 | 48.181257 |
| regular_window_scaled | 1.000000 | 32.306381 |
| quality_0 | 0.637590 | 26.260705 |
| MLB_0_pa | 672.000000 | 23.161175 |
| pooled_MLB_pa | 1137.400000 | 14.970487 |
| on_40man | 1.000000 | 11.995836 |
| pooled_MLB_K | 0.245838 | -7.580564 |

Control rate accounting: reference -0.851468; raw prediction 1.573082. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 672.000000 | 0.979407 |
| pooled_mlb_quality | 1.061868 | 0.795650 |
| work_2 | 500.612472 | 0.468646 |
| quality_0 | 0.637590 | 0.287403 |
| age_centered | 0.400000 | -0.226473 |
| position_3 | 1.000000 | 0.200748 |
| pooled_MLB_pa | 1.895667 | -0.198343 |
| reorganized | 1.000000 | -0.138872 |

His source has 185 actual PA in the shortened 2020 season, 443 in 2021 and 672 in 2022, with 30 HR most recently. Opportunity inputs schedule-adjust the 2020 workload; raw counts are not falsely shown as a full season. Both models view him as an established productive regular. Joint neighbors include Davis/Olson/Castellanos ongoing workloads and Haniger's partial year, with very little zero mass. Mean PA rises 533 to 565, probability of participating is 99.7%, and the PA lower decile is 334; actual 2023 PA is zero. Contribution rises 3.065 to 3.421, worsening the same miss. The tested origin features do not contain a then-known season-ending future injury; correctly dated late news would belong to a different preseason cutoff. This case exposes overconfidence about full-season absence, but cannot be cured by importing the actual future injury or claiming every high-workload regular should have zero PA.

Distinct-player profile support: [{'row_id': 46991, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 171}]. Weighted distribution: 263 people, effective rows 246.56, latest contributing target year 2022. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Khris Davis | 2017 | 29.0 | 652 / 0.0 / 0.0 | 654 | 4.70994 | 0.01296 |
| Christian Yelich | 2017 | 25.0 | 695 / 0.0 / 0.0 | 651 | 7.88660 | 0.01167 |
| Matt Olson | 2021 | 27.0 | 673 / 0.0 / 0.0 | 699 | 4.00392 | 0.01116 |
| Nick Castellanos | 2018 | 26.0 | 678 / 0.0 / 0.0 | 664 | 4.28900 | 0.01112 |
| Mitch Haniger | 2018 | 27.0 | 683 / 0.0 / 0.0 | 283 | 1.04532 | 0.01081 |
| Evan Longoria | 2013 | 27.0 | 693 / 0.0 / 0.0 | 700 | 2.39111 | 0.00994 |
| Chris Davis | 2016 | 30.0 | 665 / 0.0 / 0.0 | 524 | 1.26909 | 0.00969 |
| Khris Davis | 2018 | 30.0 | 654 / 0.0 / 0.0 | 533 | 0.27927 | 0.00853 |
| José Abreu | 2021 | 34.0 | 659 / 0.0 / 0.0 | 679 | 5.09731 | 0.00827 |
| Salvador Perez | 2021 | 31.0 | 665 / 0.0 / 0.0 | 473 | 1.98612 | 0.00814 |
| Todd Frazier | 2015 | 29.0 | 678 / 0.0 / 0.0 | 666 | 2.58924 | 0.00785 |
| Nolan Arenado | 2015 | 24.0 | 665 / 0.0 / 0.0 | 696 | 5.94110 | 0.00767 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Corey Hart (2012, weight 0.00138); Victor Martinez (2011, weight 0.00070); Derrek Lee (2011, weight 0.00035); Jung Ho Kang (2016, weight 0.00015); Michael Conforto (2021, weight 0.00015).

## Pete Alonso 2018 to 2019

Selection: pa false low.

Player 624413, row 33263, fold 1; stage Upper minors; age 23.0 (unknown flag 0); listed position 3; draft year/pick 2016/64; captured 40-man 0.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 157.890 | 0.55449 |
| Joint forest | 71.109 | 0.32086 |
| Actual | 693 | 5.90854 |

Control future-active batting forecast: 0.25988 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00307877). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 36.12%, at least 400 PA 5.29%, negative contribution 12.24%, at least two contribution wins 7.32%. PA deciles/median: 0/0/323. Contribution deciles/median: -0.0620/0.0000/1.3993. The median is not expected PA.

Control pa accounting: reference 39.746745; raw prediction 157.889779. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_AAA_HR | 0.059850 | 41.383354 |
| age_centered | -0.800000 | 21.264807 |
| draft_rank | 0.452844 | 21.093520 |
| pooled_AA_BB | 0.120799 | 20.529445 |
| MLB_0_pa | 0.000000 | -19.080274 |
| draft_known | 1.000000 | 18.933563 |
| pooled_AA_HR | 0.047735 | 16.680101 |
| pooled_Aplus_2B | 0.062102 | 8.884257 |

Control rate accounting: reference -0.675994; raw prediction 0.259881. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | -0.800000 | 0.422659 |
| position_3 | 1.000000 | 0.172191 |
| draft_class_unknown | 1.000000 | -0.132672 |
| pooled_AAA_HR | 0.298504 | 0.123817 |
| pooled_AA_BB | 0.407988 | 0.094429 |
| pooled_AA_BABIP | 0.275017 | 0.072305 |
| draft_known | 1.000000 | 0.069493 |
| pooled_AA_pa | 0.517667 | -0.063193 |

The source carries 273 AA plus 301 AAA PA in 2018 with 36 HR, following productive lower-minor seasons. The control explicitly rewards AAA HR, young age and AA walks and predicts 158 PA. The joint top neighbors include Springer, Bryant, Gyorko, Bellinger and Myers successful entries but also Shaw's 62, Washington's six, Jackson's 142 and actual non-arrivals. Those visible top names represent only part of the saved distribution; the full neighbor weights produce 71 expected PA, 36.1% participation and 5.3% chance of 400 PA. Actual is 693 PA and 5.909 contribution wins, above both 90th-percentile bounds. This candidate worsens an existing fast-entry miss despite recognizable successful comparisons. A named-comparable list can look sensible while its complete weighting and probability of receiving a major-league job are not. The model lacks a dated future starter/depth-chart plan, and its upper-minor cohort underallocation confirms this is not solely one famous exception.

Distinct-player profile support: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'current_work_band': 'absent', 'draft_known': 1, 'profile_players': 1035}]. Weighted distribution: 856 people, effective rows 287.44, latest contributing target year 2018. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| George Springer | 2013 | 23.0 | 0 / 267.0 / 323.0 | 345 | 2.18201 | 0.01610 |
| Kris Bryant | 2014 | 22.0 | 0 / 297.0 / 297.0 | 650 | 5.31006 | 0.01579 |
| Chris Shaw | 2017 | 23.0 | 0 / 360.0 / 154.0 | 62 | -0.12361 | 0.01454 |
| Jedd Gyorko | 2012 | 23.0 | 0 / 408.0 / 149.0 | 525 | 2.18135 | 0.01447 |
| Preston Tucker | 2014 | 23.0 | 0 / 309.0 / 290.0 | 323 | 1.20359 | 0.01437 |
| Matt Chapman | 2016 | 23.0 | 0 / 85.0 / 504.0 | 326 | 1.39935 | 0.01251 |
| Austin Slater | 2016 | 23.0 | 0 / 278.0 / 172.0 | 127 | 0.44391 | 0.01010 |
| Cody Bellinger | 2016 | 20.0 | 0 / 12.0 / 465.0 | 548 | 4.15217 | 0.00972 |
| David Washington | 2016 | 25.0 | 0 / 401.0 / 92.0 | 6 | -0.14152 | 0.00832 |
| Wil Myers | 2012 | 21.0 | 0 / 439.0 / 152.0 | 373 | 2.39549 | 0.00783 |
| Deven Marrero | 2014 | 23.0 | 0 / 202.0 / 307.0 | 56 | -0.11379 | 0.00777 |
| Brett Jackson | 2011 | 22.0 | 0 / 215.0 / 297.0 | 142 | 0.21841 | 0.00744 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Matt Fields (2014, weight 0.00737); Jake Peter (2016, weight 0.00589); Casey Stevenson (2013, weight 0.00504); Matt Reynolds (2014, weight 0.00488); Nellie Rodriguez (2017, weight 0.00470).

## Miguel Rojas 2023 to 2024

Selection: pa ordinary.

Player 500743, row 50575, fold 4; stage Current MLB; age 34.0 (unknown flag 0); listed position 6; draft year/pick None/None; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 8 | 0 | 1 | 0 |
| 2021 | MLB | 539 | 9 | 74 | 37 |
| 2022 | MLB | 507 | 6 | 61 | 25 |
| 2023 | A | 7 | 1 | 0 | 0 |
| 2023 | MLB | 423 | 5 | 48 | 26 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 312.910 | -0.07476 |
| Joint forest | 336.985 | 0.37734 |
| Actual | 337 | 1.53255 |

Control future-active batting forecast: -2.00100 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00309608). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 96.60%, at least 400 PA 34.69%, negative contribution 41.14%, at least two contribution wins 6.93%. PA deciles/median: 116/337/568. Contribution deciles/median: -0.7310/0.1122/1.7155. The median is not expected PA.

Control pa accounting: reference 39.261905; raw prediction 312.910486. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 423.000000 | 268.780432 |
| quality_0 | -0.610111 | -54.026981 |
| age_centered | 1.400000 | -39.569397 |
| regular_window_scaled | 1.000000 | 33.610048 |
| on_40man | 1.000000 | 29.652649 |
| pooled_MLB_K | 0.131150 | 16.301983 |
| pooled_MLB_pa | 1152.000000 | 13.509113 |
| pooled_mlb_quality | -0.773262 | -12.079993 |

Control rate accounting: reference -0.900485; raw prediction -2.001004. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| age_centered | 1.400000 | -0.805488 |
| work_0 | 423.000000 | 0.634026 |
| pooled_mlb_quality | -0.773262 | -0.581596 |
| work_2 | 539.221902 | 0.549829 |
| quality_0 | -0.610111 | -0.280273 |
| position_6 | 1.000000 | -0.273235 |
| pooled_MLB_pa | 1.920000 | -0.235502 |
| reorganized | 1.000000 | -0.196306 |

Known MLB PA decline 539 to 507 to 423 over three years, with only five HR in 2023; the few A/AAA rehab PA are retained as exposure rather than diagnosed injury. The control forecasts 313 PA and a strongly negative batting rate, with negative age and recent-quality PA accounting terms. The forest mixes comparable modest-bat workloads such as Infante, Pennington, Suzuki, Ryan and Iglesias, including non-returning Sogard and Keppinger. It predicts 336.985 PA against 337 actual, almost exact, but contribution is 0.377 against 1.533 actual (control -0.075). This is an ordinary PA case, not an all-component success. Position affects the forecast through a listed-position input; neither prediction includes general defensive value. The better batting result remains a general empirical mean rather than proof that it foresaw Rojas' future offensive improvement.

Distinct-player profile support: [{'row_id': 50575, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 155}]. Weighted distribution: 373 people, effective rows 208.47, latest contributing target year 2023. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Omar Infante | 2015 | 33.0 | 455 / 0.0 / 0.0 | 149 | -0.25331 | 0.01410 |
| Martín Maldonado | 2021 | 34.0 | 426 / 0.0 / 0.0 | 379 | -0.30186 | 0.01385 |
| Cliff Pennington | 2012 | 28.0 | 462 / 14.0 / 0.0 | 299 | -0.08609 | 0.01356 |
| Kurt Suzuki | 2012 | 28.0 | 442 / 0.0 / 0.0 | 316 | -0.18930 | 0.01258 |
| Ichiro Suzuki | 2015 | 41.0 | 438 / 0.0 / 0.0 | 365 | 1.21388 | 0.01199 |
| Brendan Ryan | 2012 | 30.0 | 470 / 0.0 / 0.0 | 349 | -1.04034 | 0.01196 |
| Clint Barmes | 2012 | 33.0 | 493 / 0.0 / 0.0 | 330 | -0.99736 | 0.01169 |
| Jackie Bradley Jr. | 2021 | 31.0 | 428 / 0.0 / 0.0 | 370 | -0.60511 | 0.01165 |
| Jose Iglesias | 2017 | 27.0 | 489 / 0.0 / 0.0 | 464 | 1.06892 | 0.01066 |
| Victor Robles | 2022 | 25.0 | 407 / 0.0 / 0.0 | 126 | 0.50774 | 0.01062 |
| Adam Kennedy | 2011 | 35.0 | 409 / 0.0 / 0.0 | 201 | 0.50951 | 0.01033 |
| Alberto Callaspo | 2014 | 31.0 | 451 / 0.0 / 0.0 | 261 | -0.04766 | 0.01021 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Eric Sogard (2015, weight 0.00813); Jeff Keppinger (2013, weight 0.00667); Vernon Wells (2013, weight 0.00572); Brandon Moss (2017, weight 0.00243); Shogo Akiyama (2021, weight 0.00134).

## Aaron Judge 2021 to 2022

Selection: value largest gain.

Player 592450, row 42360, fold 3; stage Current MLB; age 29.0 (unknown flag 0); listed position 9; draft year/pick 2013/32; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 19 | 1 | 7 | 3 |
| 2019 | MLB | 447 | 27 | 141 | 60 |
| 2020 | MLB | 114 | 9 | 32 | 10 |
| 2021 | MLB | 633 | 39 | 158 | 73 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 482.210 | 3.15572 |
| Joint forest | 556.565 | 3.91484 |
| Actual | 696 | 9.78949 |

Control future-active batting forecast: 2.04558 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00313500). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.65%, at least 400 PA 84.70%, negative contribution 1.23%, at least two contribution wins 80.01%. PA deciles/median: 318/613/705. Contribution deciles/median: 1.0071/3.9245/6.7628. The median is not expected PA.

Control pa accounting: reference 38.182159; raw prediction 482.209795. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 633.260601 | 352.456881 |
| quality_0 | 1.278618 | 58.992739 |
| pooled_mlb_quality | 1.561682 | 42.490126 |
| pooled_MLB_K | 0.266569 | -35.165976 |
| regular_window_scaled | 0.666667 | 23.545726 |
| on_40man | 1.000000 | 11.789199 |
| pooled_MLB_HR | 0.059868 | 8.227279 |
| pooled_MLB_pa | 992.400000 | -7.473104 |

Control rate accounting: reference -0.910439; raw prediction 2.045577. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 1.561682 | 1.105589 |
| work_0 | 633.260601 | 0.807249 |
| quality_0 | 1.278618 | 0.556754 |
| work_2 | 447.184026 | 0.282999 |
| work_1 | 308.485523 | 0.237970 |
| age_centered | 0.400000 | -0.222969 |
| prior_debut | 1.000000 | 0.171728 |
| pooled_MLB_pa | 1.654000 | -0.166326 |

His actual counts are 447 MLB PA in 2019, 114 in shortened 2020 and 633 in 2021, with 39 HR most recently. The workload features explicitly schedule-adjust the shortened season, whereas the table retains actual PA. Control assigns substantial credit to workload and MLB quality but penalizes stabilized K and forecasts 482 PA, 3.156 contribution wins. The forest mixes Stanton, Harper, Trout and other productive outcomes, with small zero weights from Ortiz and Hart; expected PA rises to 557 and value to 3.915, both closer to actual 696 and 9.789. Yet the contribution upper decile is only 6.763, missing the historic power season badly. This is the largest outcome-selected value gain, not an independent validation of superstar detection. The raw rate/PA covariance construction is not automatically superior to the PA-weighted control rate, and a great subsequent season should not be treated as certain from these histories.

Distinct-player profile support: [{'row_id': 42360, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 134}]. Weighted distribution: 259 people, effective rows 187.79, latest contributing target year 2021. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Giancarlo Stanton | 2017 | 27.0 | 692 / 0.0 / 0.0 | 705 | 4.80600 | 0.02041 |
| Buster Posey | 2012 | 25.0 | 610 / 0.0 / 0.0 | 595 | 3.92453 | 0.02031 |
| Giancarlo Stanton | 2014 | 24.0 | 638 / 0.0 / 0.0 | 318 | 2.94528 | 0.01531 |
| Bryce Harper | 2015 | 22.0 | 654 / 0.0 / 0.0 | 627 | 2.86249 | 0.01528 |
| Mike Trout | 2012 | 20.0 | 639 / 93.0 / 0.0 | 716 | 8.51089 | 0.01337 |
| Paul Goldschmidt | 2013 | 25.0 | 710 / 0.0 / 0.0 | 479 | 4.73458 | 0.01265 |
| Alex Bregman | 2018 | 24.0 | 705 / 0.0 / 0.0 | 690 | 7.96852 | 0.01234 |
| Matt Carpenter | 2013 | 27.0 | 717 / 0.0 / 0.0 | 709 | 4.11883 | 0.01059 |
| Giancarlo Stanton | 2012 | 22.0 | 501 / 0.0 / 0.0 | 504 | 3.78879 | 0.01011 |
| Christian Yelich | 2018 | 26.0 | 651 / 0.0 / 0.0 | 580 | 7.33355 | 0.00992 |
| Freddie Freeman | 2016 | 26.0 | 693 / 0.0 / 0.0 | 514 | 4.96337 | 0.00935 |
| Jonathan Lucroy | 2014 | 28.0 | 655 / 0.0 / 0.0 | 415 | 1.41602 | 0.00935 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): David Ortiz (2016, weight 0.00220); Corey Hart (2012, weight 0.00115); Edwin Encarnación (2020, weight 0.00019).

## Mookie Betts 2017 to 2018

Selection: value largest harm.

Player 605141, row 28634, fold 0; stage Current MLB; age 24.0 (unknown flag 0); listed position 9; draft year/pick 2011/172; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2015 | AA | 4 | 1 | 0 | 0 |
| 2015 | MLB | 654 | 18 | 82 | 45 |
| 2016 | MLB | 730 | 31 | 80 | 48 |
| 2017 | MLB | 712 | 24 | 79 | 68 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 681.846 | 5.01213 |
| Joint forest | 583.818 | 3.63516 |
| Actual | 614 | 8.58835 |

Control future-active batting forecast: 2.56479 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00307618). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.76%, at least 400 PA 88.91%, negative contribution 1.17%, at least two contribution wins 80.53%. PA deciles/median: 373/641/697. Contribution deciles/median: 1.1745/3.6441/6.1584. The median is not expected PA.

Control pa accounting: reference 37.974580; raw prediction 681.846331. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 712.000000 | 267.291591 |
| work_0 | 712.000000 | 84.570670 |
| regular_window_scaled | 1.000000 | 47.082785 |
| MLB_2_pa | 654.000000 | 30.700479 |
| pooled_MLB_K | 0.120331 | 30.069305 |
| pooled_mlb_quality | 1.126245 | 28.131948 |
| MLB_1_pa | 730.000000 | 28.003013 |
| quality_0 | 0.321558 | 26.252385 |

Control rate accounting: reference -0.630598; raw prediction 2.564790. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 712.000000 | 0.911096 |
| pooled_mlb_quality | 1.126245 | 0.719506 |
| quality_1 | 1.210760 | 0.388768 |
| work_2 | 654.269247 | 0.296132 |
| age_centered | -0.600000 | 0.287648 |
| work_1 | 730.601318 | 0.240277 |
| quality_2 | 0.691132 | 0.183038 |
| position_9 | 1.000000 | 0.148644 |

The source has 654/730/712 MLB PA with 18/31/24 HR over three seasons at age 24 and low strikeouts. Control receives strong repeated-regular workload and MLB-quality evidence, predicting 682 PA, 2.565 batting wins/600 and 5.012 contribution wins. The forest includes Machado, Donaldson, Springer, Seager and Dozier trajectories but also Eaton's 107-PA follow-up and sparse zero outcomes. Expected PA drops to 584 and is closer to actual 614, while value drops much more to 3.635 against 8.588 actual. Actual PA is in the central range but actual contribution exceeds its 6.158-win upper decile. Thus better workload error can hide worse talent/contribution shrinkage. The cohort contains real comparable young regulars, but averaging paired outcomes still compresses elite upside; this largest value deterioration directly opposes the Judge-2021 favorable example.

Distinct-player profile support: [{'row_id': 28634, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 50}]. Weighted distribution: 198 people, effective rows 197.02, latest contributing target year 2017. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Kyle Seager | 2015 | 27.0 | 686 / 0.0 / 0.0 | 676 | 4.48366 | 0.01461 |
| Manny Machado | 2016 | 23.0 | 696 / 0.0 / 0.0 | 690 | 2.62526 | 0.01261 |
| Josh Donaldson | 2014 | 28.0 | 695 / 0.0 / 0.0 | 711 | 7.25264 | 0.01160 |
| Adam Eaton | 2016 | 27.0 | 706 / 0.0 / 0.0 | 107 | 0.78881 | 0.01137 |
| George Springer | 2016 | 26.0 | 744 / 0.0 / 0.0 | 629 | 4.92611 | 0.01061 |
| Kyle Seager | 2016 | 28.0 | 676 / 0.0 / 0.0 | 650 | 2.32612 | 0.01049 |
| Buster Posey | 2016 | 29.0 | 614 / 0.0 / 0.0 | 568 | 3.63351 | 0.01020 |
| Brian Dozier | 2015 | 28.0 | 704 / 0.0 / 0.0 | 691 | 5.03178 | 0.01009 |
| Christian Yelich | 2016 | 24.0 | 659 / 0.0 / 0.0 | 695 | 3.75804 | 0.01001 |
| Alex Gordon | 2013 | 29.0 | 700 / 0.0 / 0.0 | 643 | 3.94531 | 0.00995 |
| José Abreu | 2016 | 29.0 | 695 / 0.0 / 0.0 | 675 | 5.27878 | 0.00994 |
| Chris Davis | 2016 | 30.0 | 665 / 0.0 / 0.0 | 524 | 1.26909 | 0.00991 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Corey Hart (2012, weight 0.00096); Derrek Lee (2011, weight 0.00085); Victor Martinez (2011, weight 0.00035); Derek Jeter (2014, weight 0.00012); Michael Young (2013, weight 0.00010).

## Scooter Gennett 2018 to 2019

Selection: value false high.

Player 571697, row 32610, fold 1; stage Current MLB; age 28.0 (unknown flag 0); listed position 4; draft year/pick 2009/496; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2016 | Aplus | 7 | 0 | 2 | 1 |
| 2016 | MLB | 542 | 14 | 114 | 37 |
| 2017 | MLB | 497 | 27 | 114 | 29 |
| 2018 | MLB | 638 | 23 | 125 | 39 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 551.305 | 2.94542 |
| Joint forest | 569.725 | 3.34260 |
| Actual | 139 | -0.47879 |

Control future-active batting forecast: 1.35832 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00307877). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.87%, at least 400 PA 88.53%, negative contribution 1.54%, at least two contribution wins 73.70%. PA deciles/median: 362/620/697. Contribution deciles/median: 0.7888/3.2528/5.9411. The median is not expected PA.

Control pa accounting: reference 39.746745; raw prediction 551.305162. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| MLB_0_pa | 638.000000 | 302.968762 |
| work_0 | 637.737557 | 61.923939 |
| quality_0 | 0.806210 | 49.812818 |
| regular_window_scaled | 1.000000 | 39.713275 |
| pooled_mlb_quality | 0.946911 | 16.039883 |
| pooled_MLB_pa | 1360.800000 | 14.192394 |
| age_centered | 0.200000 | 12.047364 |
| on_40man | 1.000000 | 8.999702 |

Control rate accounting: reference -0.675994; raw prediction 1.358319. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| pooled_mlb_quality | 0.946911 | 0.658346 |
| work_0 | 637.737557 | 0.495223 |
| work_2 | 542.446458 | 0.348580 |
| quality_0 | 0.806210 | 0.345616 |
| quality_1 | 0.715741 | 0.189564 |
| work_1 | 497.000000 | 0.179907 |
| regular_window_scaled | 1.000000 | -0.131633 |
| position_4 | 1.000000 | -0.122789 |

Source MLB PA are 542/497/638 with 14/27/23 HR across three years. Both forecasts expect a productive age-28 regular. The joint neighborhood includes Davis, LeMahieu, Belt and Dozier ongoing years, with small zero mass from Martinez/Ortiz/Cuddyer. Mean PA rises 551 to 570 and value rises 2.945 to 3.343; actual is just 139 PA and -0.479 contribution wins. Its 362-697 PA range misses the reduced season, and its contribution lower decile remains positive at 0.789. The model did not predict the collapse and cannot explain it using later injuries or transactions absent at origin. This large false high is a risk-tail failure and an expected-value deterioration, not proof that his observed earlier production lacked predictive information.

Distinct-player profile support: [{'row_id': 32610, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 1, 'profile_players': 118}]. Weighted distribution: 237 people, effective rows 235.87, latest contributing target year 2018. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Khris Davis | 2017 | 29.0 | 652 / 0.0 / 0.0 | 654 | 4.70994 | 0.01309 |
| DJ LeMahieu | 2016 | 27.0 | 635 / 0.0 / 0.0 | 682 | 3.35989 | 0.01273 |
| Brandon Belt | 2016 | 28.0 | 655 / 0.0 / 0.0 | 451 | 2.62376 | 0.01116 |
| Kyle Seager | 2016 | 28.0 | 676 / 0.0 / 0.0 | 650 | 2.32612 | 0.01088 |
| Brian Dozier | 2017 | 30.0 | 705 / 0.0 / 0.0 | 632 | 1.50955 | 0.01072 |
| Brian Dozier | 2016 | 29.0 | 691 / 0.0 / 0.0 | 705 | 4.61498 | 0.01061 |
| J.D. Martinez | 2015 | 27.0 | 657 / 0.0 / 0.0 | 517 | 4.50156 | 0.01047 |
| Nolan Arenado | 2015 | 24.0 | 665 / 0.0 / 0.0 | 696 | 5.94110 | 0.01018 |
| Khris Davis | 2016 | 28.0 | 610 / 0.0 / 0.0 | 652 | 4.36542 | 0.00994 |
| DJ LeMahieu | 2017 | 28.0 | 682 / 0.0 / 0.0 | 581 | 2.25847 | 0.00897 |
| Buster Posey | 2015 | 28.0 | 623 / 0.0 / 0.0 | 614 | 3.05652 | 0.00874 |
| Carlos González | 2016 | 30.0 | 632 / 0.0 / 0.0 | 534 | 1.97416 | 0.00812 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Victor Martinez (2011, weight 0.00103); David Ortiz (2016, weight 0.00016); Michael Cuddyer (2015, weight 0.00014).

## Lourdes Gurriel Jr. 2021 to 2022

Selection: value ordinary.

Player 666971, row 43438, fold 0; stage Current MLB; age 27.0 (unknown flag 0); listed position 7; draft year/pick None/None; captured 40-man 1.

| Season | Level bucket | PA | HR | K | Unintentional BB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 130 | 4 | 23 | 3 |
| 2019 | MLB | 343 | 20 | 86 | 20 |
| 2020 | MLB | 224 | 11 | 48 | 14 |
| 2021 | MLB | 541 | 21 | 102 | 31 |

| Forecast | Expected MLB PA | Batting plus replacement wins |
|---|---:|---:|
| Control | 481.480 | 2.48593 |
| Joint forest | 487.894 | 2.28157 |
| Actual | 493 | 2.28208 |

Control future-active batting forecast: 1.21685 wins/600. Contribution arithmetic: expected PA × (rate/600 + origin replacement 0.00313500). The future-PA-weighted rate is not necessarily an independent unweighted mean. The joint forecast instead averages the same weighted actual PA/value pairs; its implied yield is not a separately validated talent grade.

Joint probabilities: participation 99.35%, at least 400 PA 74.77%, negative contribution 5.76%, at least two contribution wins 52.67%. PA deciles/median: 257/515/656. Contribution deciles/median: 0.2977/2.1957/4.4402. The median is not expected PA.

Control pa accounting: reference 37.627167; raw prediction 481.479845. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 541.222725 | 296.497507 |
| regular_window_scaled | 0.666667 | 35.818824 |
| pooled_mlb_quality | 0.678614 | 31.398622 |
| quality_0 | 0.306555 | 28.383048 |
| pooled_MLB_pa | 926.000000 | 21.556627 |
| age_centered | 0.000000 | 11.899109 |
| on_40man | 1.000000 | 11.232349 |
| work_1 | 606.146993 | 8.099469 |

Control rate accounting: reference -0.769585; raw prediction 1.216855. PA clipping or permanent-status override, when applicable, follows the raw prediction.

| Actual input | Input or scaled input | Accounting effect |
|---|---:|---:|
| work_0 | 541.222725 | 0.819298 |
| pooled_mlb_quality | 0.678614 | 0.483558 |
| work_1 | 606.146993 | 0.271621 |
| position_7 | 1.000000 | 0.225538 |
| work_2 | 343.141210 | 0.204417 |
| pooled_MLB_pa | 1.543333 | -0.131318 |
| regular_window_scaled | 0.666667 | -0.119098 |
| quality_1 | 0.427408 | 0.116395 |

Actual histories are 343 MLB PA plus 130 AAA in 2019, 224 MLB PA in shortened 2020 and 541 MLB PA in 2021, with 21 HR that last season. The opportunity representation schedule-adjusts 2020 rather than interpreting it as reduced health. Control predicts 481 PA and 2.486 contribution wins; the forest's weighted ordinary productive-player outcomes include Walker, Dickerson, Carter, Joyce and Rosario, plus small zero weights from Kang/Cespedes/Perez. Joint mean is 488 PA and 2.28157 wins versus actual 493 and 2.28208. This is a genuinely well-predicted ordinary case with compatible PA and contribution, not a lucky cancellation of a gross workload miss. The exactness of one outcome-selected case is not expected to repeat; the proper cohort comparisons still show the joint point model loses overall. Neither forecast incorporates missing Cuban amateur/foreign statistics as fabricated zeros of talent.

Distinct-player profile support: [{'row_id': 43438, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'current_work_band': '400plus', 'draft_known': 0, 'profile_players': 138}]. Weighted distribution: 381 people, effective rows 383.20, latest contributing target year 2021. Sparse profile support remains qualified, not repaired by the overall leaf count.

| Weighted origin neighbor | Origin | Age | Origin MLB / AAA / AA PA | Next MLB PA | Next contribution | Weight |
|---|---:|---:|---|---:|---:|---:|
| Miguel Montero | 2011 | 27.0 | 553 / 0.0 / 0.0 | 573 | 4.13660 | 0.01079 |
| Neil Walker | 2012 | 26.0 | 530 / 0.0 / 0.0 | 551 | 2.52077 | 0.00950 |
| Corey Dickerson | 2016 | 27.0 | 548 / 0.0 / 0.0 | 629 | 2.97277 | 0.00874 |
| Chris Carter | 2014 | 27.0 | 572 / 0.0 / 0.0 | 460 | 1.71586 | 0.00856 |
| Matt Joyce | 2012 | 27.0 | 462 / 3.0 / 0.0 | 481 | 2.26064 | 0.00811 |
| Matt Joyce | 2011 | 26.0 | 522 / 0.0 / 0.0 | 462 | 2.22640 | 0.00694 |
| Khris Davis | 2014 | 26.0 | 549 / 0.0 / 0.0 | 440 | 2.87096 | 0.00693 |
| Starling Marte | 2014 | 25.0 | 545 / 12.0 / 0.0 | 633 | 3.25192 | 0.00692 |
| Yasiel Puig | 2018 | 27.0 | 444 / 11.0 / 0.0 | 611 | 2.52768 | 0.00670 |
| Yoenis Cespedes | 2013 | 27.0 | 574 / 11.0 / 0.0 | 645 | 2.85730 | 0.00650 |
| Eddie Rosario | 2018 | 26.0 | 592 / 0.0 / 0.0 | 590 | 2.35285 | 0.00637 |
| Ike Davis | 2012 | 25.0 | 584 / 0.0 / 0.0 | 377 | 0.68744 | 0.00619 |

Highest-weight zero follow-ups (also selected by fitted origin-feature weights): Jung Ho Kang (2016, weight 0.00186); Yoenis Cespedes (2018, weight 0.00106); Salvador Perez (2018, weight 0.00084); Tommy Joseph (2017, weight 0.00068); Yasmany Tomás (2017, weight 0.00045).

## Decision after reviewing the players

Do not replace the working means. The joint candidate worsens PA and contribution error overall; all seven origin contribution errors worsen, and upper-minor opportunity totals fall farther below actual. Better league-wide PA totals are not a sufficient win. Its risk probabilities outperform a simple stage/debut reference, but upper-minor participation is underpredicted and lower-minor rare-event log loss worsens. Retain the empirical distribution implementation and case evidence as research, not validated uncertainty grafted onto a different point model.

The review identifies dated availability/context as a useful source repair, especially announced retirement and foreign-player eligibility. It also shows elite-value compression and broad readiness neighborhoods. These are different issues: first repair or explicitly qualify origin-known population/status evidence; do not launch another library sweep or tune to famous breakouts. Frozen 2026 and the deployed forecast stay unchanged.
