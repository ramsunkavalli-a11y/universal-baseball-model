# Preseason ranking comparison: source to saved model to reality

Same 30,506 historical players/seasons, whole-player chronological folds and fixed hitting forecasts. The only new information is the coming-season preseason ranking vintage. Other sources remain through December; this is not a complete Opening Day roster forecast. Repeated development evidence, qualified retrospective lists, no protected 2026 outcomes or automatic promotion.

| Group | Rows | Old PA RMSE | New PA RMSE | Old PA MAE | New PA MAE | Old offense RMSE | New offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 30506 | 60.686 | 60.499 | 20.745 | 20.612 | 0.453810 | 0.453384 |
| public_broad | 2627 | 138.488 | 138.330 | 106.871 | 106.411 | 1.061315 | 1.060504 |
| never_debut | 24199 | 27.745 | 27.252 | 4.875 | 4.764 | 0.154066 | 0.152257 |
| upper_never_debut | 5454 | 56.242 | 55.127 | 19.097 | 18.732 | 0.317058 | 0.312832 |
| lower_never_debut | 17852 | 7.828 | 7.966 | 0.656 | 0.622 | 0.042821 | 0.043039 |
| current_MLB | 4541 | 140.980 | 140.951 | 107.900 | 107.697 | 1.113723 | 1.113963 |
| newly_listed | 242 | 135.016 | 123.085 | 56.860 | 60.491 | 0.965417 | 0.939224 |
| first_year_top_picks | 68 | 113.741 | 104.125 | 35.748 | 37.421 | 0.685287 | 0.666060 |

Losses weight target years equally. Offense is custom-event batting plus replacement, not full WAR or trade value. Exact counts, origin totals, probability scores and nominal intervals accompany this review. Profile counts are support warnings, not individual prediction intervals.

## Nick Kurtz / 2024 to 2025

Player 701762; row 57052; fold 2; age 21.0; Upper minors; new rank availability 2025-01-24. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.63, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.017252 | 115.973 | 2.001 | -0.06322 | 0.00604 |
| preseason | 0.060561 | 168.160 | 10.184 | -0.06322 | 0.03073 |
| Actual | 1 | not a forecast | 489 | 5.289191738139299 | 5.83778 |

Product: 0.060561166 × 168.160355078; offense yield: -0.063222554/600 + 0.003122875.

Actual MLB counts: 2025: 489 PA, 36 HR, 151 K, 60 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 842; rank band 0.
- baseline participation refined: 14; rank band 0.
- baseline conditional_pa broad: 158; rank band 0.
- baseline conditional_pa refined: 0; rank band 0.
- preseason participation broad: 54; rank band 2.
- preseason participation refined: 1; rank band 2.
- preseason conditional_pa broad: 31; rank band 2.
- preseason conditional_pa refined: 0; rank band 2.

Saved baseline participation: reference -4.013758, raw additive prediction -4.042413. Log odds; probability 0.017252.
Largest path terms (accounting, not causal effects):
- draft_rank: input 0.817615, contribution +0.833055.
- on_40man: input 0.000000, contribution -0.325946.
- games_mlb_0: input 0.000000, contribution -0.198218.
- games_pool_MLB: input 0.000000, contribution -0.188692.
- role_pool_A: input 4.411765, contribution +0.186531.

Saved preseason participation: reference -4.096228, raw additive prediction -2.741629. Log odds; probability 0.060561.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.630000, contribution +1.243941.
- draft_rank: input 0.817615, contribution +0.450012.
- scout_listed_0: input 1.000000, contribution +0.396579.
- on_40man: input 0.000000, contribution -0.334185.
- games_mlb_0: input 0.000000, contribution -0.202625.

Same fitted candidate with all old ranking inputs restored: 0.007716. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 278.575191, raw additive prediction 115.972916. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- work_0: input 0.000000, contribution -99.490116.
- on_40man: input 0.000000, contribution -23.436218.
- quality_0: input 0.000000, contribution -13.148363.
- draft_rank: input 0.817615, contribution +10.742506.
- regular_window_scaled: input 0.000000, contribution -10.311596.

Saved preseason conditional_pa: reference 278.554971, raw additive prediction 168.160355. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- work_0: input 0.000000, contribution -99.719816.
- scout_rank_score_0: input 0.630000, contribution +71.234719.
- on_40man: input 0.000000, contribution -22.649740.
- quality_0: input 0.000000, contribution -12.276285.
- regular_window_scaled: input 0.000000, contribution -11.785065.

Same fitted candidate with all old ranking inputs restored: 91.772051. Mechanics probe only, not causality or a separately validated replacement forecast.

Kurtz has 50 pro PA, four HR, pick four and rank 38 in the coming preseason. The saved candidate rewards current rank by 1.24 log-odds units and about 71 conditional PA; reverting all rankings in that fixed model gives only .77% arrival and 92 conditional PA. Thus newer reputation genuinely enters the mechanism. Arrival rises 1.73% to 6.06%, conditional PA 116 to 168 and expected PA two to ten, still nowhere near 489 actual with 36 HR. There are zero refined earlier active examples and only one matching participation example. Moore and Smith also remain far too low, while Williams becomes a larger false high at 101 versus zero. The new source helps, but cannot cure unsupported fast-entry workload or the nearly average fixed hitting estimate. No player-specific override is justified.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benny Montgomery | 6.54 | 5.41 | 0 | 0.018 | 0.015 | 0.000 |
| Christian Moore | 8.23 | 22.35 | 184 | 0.025 | 0.069 | 0.242 |
| Cam Smith | 2.33 | 9.98 | 493 | 0.006 | 0.027 | 1.131 |
| Jett Williams | 74.66 | 100.55 | 0 | 0.219 | 0.295 | 0.000 |

## Wyatt Langford / 2023 to 2024

Player 694671; row 53164; fold 4; age 21.0; Upper minors; new rank availability 2024-01-26. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.95, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.201829 | 213.556 | 43.102 | 0.68803 | 0.18287 |
| preseason | 0.599098 | 358.735 | 214.918 | 0.68803 | 0.91185 |
| Actual | 1 | not a forecast | 557 | 0.07695317803827988 | 1.79595 |

Product: 0.599098272 × 358.735377142; offense yield: 0.688029041/600 + 0.003096076.

Actual MLB counts: 2024: 557 PA, 16 HR, 115 K, 48 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 750; rank band 0.
- baseline participation refined: 18; rank band 0.
- baseline conditional_pa broad: 161; rank band 0.
- baseline conditional_pa refined: 2; rank band 0.
- preseason participation broad: 35; rank band 1.
- preseason participation refined: 0; rank band 1.
- preseason conditional_pa broad: 33; rank band 1.
- preseason conditional_pa refined: 0; rank band 1.

Saved baseline participation: reference -4.088718, raw additive prediction -1.374901. Log odds; probability 0.201829.
Largest path terms (accounting, not causal effects):
- role_pool_AA: input 4.272727, contribution +0.965841.
- draft_rank: input 0.817615, contribution +0.716386.
- pooled_AA_pa: input 54.000000, contribution +0.452237.
- role_minor_0: input 4.444444, contribution +0.405194.
- on_40man: input 0.000000, contribution -0.404258.

Saved preseason participation: reference -4.136149, raw additive prediction 0.401709. Log odds; probability 0.599098.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.950000, contribution +1.300233.
- scout_listed_0: input 1.000000, contribution +1.173110.
- role_pool_AA: input 4.272727, contribution +0.920409.
- draft_rank: input 0.817615, contribution +0.443997.
- on_40man: input 0.000000, contribution -0.406939.

Same fitted candidate with all old ranking inputs restored: 0.119927. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 279.215202, raw additive prediction 213.555553. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- work_0: input 0.000000, contribution -99.865086.
- role_pool_AAA: input 4.400000, contribution +37.070129.
- on_40man: input 0.000000, contribution -18.288035.
- age_centered: input -1.200000, contribution +14.860035.
- role_pool_AA: input 4.272727, contribution +13.293606.

Saved preseason conditional_pa: reference 279.203529, raw additive prediction 358.735377. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.950000, contribution +147.249762.
- work_0: input 0.000000, contribution -94.004712.
- role_pool_AAA: input 4.400000, contribution +34.806643.
- on_40man: input 0.000000, contribution -19.537854.
- role_pool_AA: input 4.272727, contribution +15.145308.

Same fitted candidate with all old ranking inputs restored: 193.862399. Mechanics probe only, not causality or a separately validated replacement forecast.

Langford retains 200 pro PA spanning four levels and ten HR. His new sixth-place rank contributes 1.30 plus 1.17 log-odds units through score/listing paths and roughly 147 conditional PA. The old-vintage reversion probe reduces the candidate to 12% arrival and 194 conditional PA, compared with 60% and 359 for current rankings. Expected PA rises 43 to 215 versus 557 actual. Both heads improve his point forecast through a baseball-relevant source, not offsetting hitting changes, but refined training support is zero: the model borrows from other ranked profiles. Veen's false high declines 85 to 16, Crews rises 13 to 50 versus 132, and Shaw worsens 34 to 101 versus zero. New pedigree is not a job guarantee. Keep this evidence as a qualified readiness gain, not solved fast college entry.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Zac Veen | 85.17 | 15.77 | 0 | 0.241 | 0.045 | 0.000 |
| Dylan Crews | 12.55 | 49.67 | 132 | 0.040 | 0.159 | 0.025 |
| Matt Shaw | 34.13 | 101.43 | 0 | 0.093 | 0.276 | 0.000 |
| Brock Wilken | 6.42 | 3.92 | 0 | 0.022 | 0.014 | 0.000 |

## Cody Bellinger / 2016 to 2017

Player 641355; row 24967; fold 3; age 20.0; Upper minors; new rank availability 2017-01-28. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.88, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.110193 | 139.597 | 15.383 | 0.08460 | 0.04963 |
| preseason | 0.399032 | 257.040 | 102.567 | 0.08460 | 0.33094 |
| Actual | 1 | not a forecast | 548 | 2.928010671333948 | 4.36513 |

Product: 0.399032254 × 257.039623894; offense yield: 0.084595978/600 + 0.003085550.

Actual MLB counts: 2017: 548 PA, 39 HR, 146 K, 51 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 380; rank band 0.
- baseline participation refined: 353; rank band 0.
- baseline conditional_pa broad: 91; rank band 0.
- baseline conditional_pa refined: 90; rank band 0.
- preseason participation broad: 17; rank band 1.
- preseason participation refined: 17; rank band 1.
- preseason conditional_pa broad: 13; rank band 1.
- preseason conditional_pa refined: 13; rank band 1.

Saved baseline participation: reference -4.021534, raw additive prediction -2.088774. Log odds; probability 0.110193.
Largest path terms (accounting, not causal effects):
- role_pool_AA: input 4.072581, contribution +0.699191.
- pooled_AA_pa: input 465.000000, contribution +0.534613.
- games_minor_0: input 117.000000, contribution +0.457330.
- on_40man: input 0.000000, contribution -0.424700.
- draft_rank: input 0.365828, contribution +0.377775.

Saved preseason participation: reference -4.078610, raw additive prediction -0.409499. Log odds; probability 0.399032.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.880000, contribution +1.338380.
- role_pool_AA: input 4.072581, contribution +0.676734.
- pooled_AA_pa: input 465.000000, contribution +0.588616.
- draft_rank: input 0.365828, contribution +0.431578.
- on_40man: input 0.000000, contribution -0.427488.

Same fitted candidate with all old ranking inputs restored: 0.089808. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 276.981156, raw additive prediction 139.597326. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 0.000000, contribution -83.956460.
- work_0: input 0.000000, contribution -27.449139.
- pooled_AAA_pa: input 12.000000, contribution +18.259827.
- on_40man: input 0.000000, contribution -16.912854.
- role_minor_2: input 4.475410, contribution +15.641117.

Saved preseason conditional_pa: reference 276.994851, raw additive prediction 257.039624. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.880000, contribution +109.994225.
- MLB_0_pa: input 0.000000, contribution -91.806672.
- work_0: input 0.000000, contribution -25.816599.
- on_40man: input 0.000000, contribution -21.422299.
- pooled_AAA_pa: input 12.000000, contribution +16.292125.

Same fitted candidate with all old ranking inputs restored: 138.774709. Mechanics probe only, not causality or a separately validated replacement forecast.

Bellinger's 26 AA/AAA HR after 30 A-plus HR now coexist with a preseason number-13 ranking, while his correct December roster absence stays zero. Rank paths add about 1.34 log-odds units and 110 conditional PA. Holding the candidate fit fixed but reverting rankings lowers arrival to 9% and conditional PA to 139. With the new inputs he reaches 40% arrival, 257 conditional PA and 103 expected PA versus 548 actual and 39 MLB HR. Refined support is seventeen participation and thirteen active people, not zero, though still modest. Verdugo also rises 32 to 98 but only gets 25 PA; Ward, Westbrook and Kiner-Falefa do not arrive. The improvement is real on this case, but less discrimination among ranked AA hitters can create false positives, and the fixed nearly-average batting rate remains inadequate for the breakout.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alex Verdugo | 32.00 | 97.94 | 25 | 0.100 | 0.306 | -0.076 |
| Isiah Kiner-Falefa | 18.75 | 15.02 | 0 | 0.054 | 0.043 | 0.000 |
| Drew Ward | 1.95 | 1.66 | 0 | 0.006 | 0.005 | 0.000 |
| Jamie Westbrook | 4.21 | 2.93 | 0 | 0.010 | 0.007 | 0.000 |

## Pete Alonso / 2018 to 2019

Player 624413; row 33263; fold 1; age 23.0; Upper minors; new rank availability 2019-01-27. Selected: fixed before fit, largest offense gain.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.5, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.692850 | 183.403 | 127.071 | 0.28616 | 0.45199 |
| preseason | 0.803630 | 267.577 | 215.033 | 0.28616 | 0.76486 |
| Actual | 1 | not a forecast | 693 | 3.864559970969914 | 6.59803 |

Product: 0.803629859 × 267.577142821; offense yield: 0.286158486/600 + 0.003080035.

Actual MLB counts: 2019: 693 PA, 53 HR, 183 K, 66 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 1374; rank band 0.
- baseline participation refined: 1353; rank band 0.
- baseline conditional_pa broad: 230; rank band 0.
- baseline conditional_pa refined: 230; rank band 0.
- preseason participation broad: 7; rank band 3.
- preseason participation refined: 7; rank band 3.
- preseason conditional_pa broad: 5; rank band 3.
- preseason conditional_pa refined: 5; rank band 3.

Saved baseline participation: reference -4.017674, raw additive prediction 0.813478. Log odds; probability 0.692850.
Largest path terms (accounting, not causal effects):
- games_minor_0: input 132.000000, contribution +0.962217.
- role_pool_AA: input 4.183771, contribution +0.915294.
- pooled_AA_pa: input 310.600000, contribution +0.705914.
- draft_rank: input 0.452844, contribution +0.543319.
- on_40man: input 0.000000, contribution -0.466915.

Saved preseason participation: reference -4.051331, raw additive prediction 1.409137. Log odds; probability 0.803630.
Largest path terms (accounting, not causal effects):
- games_minor_0: input 132.000000, contribution +0.953653.
- role_pool_AA: input 4.183771, contribution +0.914331.
- pooled_AA_pa: input 310.600000, contribution +0.747221.
- scout_listed_0: input 1.000000, contribution +0.600307.
- scout_rank_score_0: input 0.500000, contribution +0.576048.

Same fitted candidate with all old ranking inputs restored: 0.586215. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 287.128813, raw additive prediction 183.403275. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 0.000000, contribution -66.383899.
- work_0: input 0.000000, contribution -42.506976.
- role_pool_AAA: input 4.428571, contribution +34.618073.
- pooled_AAA_HR: input 0.059850, contribution +29.557808.
- on_40man: input 0.000000, contribution -21.980379.

Saved preseason conditional_pa: reference 287.111690, raw additive prediction 267.577143. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.500000, contribution +101.563320.
- MLB_0_pa: input 0.000000, contribution -69.064387.
- work_0: input 0.000000, contribution -38.369776.
- role_pool_AAA: input 4.428571, contribution +32.773239.
- pooled_AAA_HR: input 0.059850, contribution +26.230681.

Same fitted candidate with all old ranking inputs restored: 162.790209. Mechanics probe only, not causality or a separately validated replacement forecast.

Alonso is the largest offense gain, selected by the locked ordering. He had 574 AA/AAA PA and 36 HR and is newly ranked 51. Current rank/listing paths raise arrival and add about 102 conditional PA; the fixed-fit old-rank probe gives 59% and 163 versus the new 80% and 268. Expected PA improves 127 to 215 versus 693, offense .452 to .765 versus 6.598. The fixed batting rate is unchanged, so no hitting improvement is claimed. Five refined active people support this exact profile. Mercado remains strongly underforecast and Solak moderately so, while Brigman does not arrive and Neuse gets 61 PA. This supports fresher readiness evidence but also reveals compressed workload and underestimated MLB power that rankings alone have not solved.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nick Solak | 33.17 | 31.37 | 135 | 0.071 | 0.067 | 1.169 |
| Óscar Mercado | 87.73 | 81.36 | 482 | 0.158 | 0.147 | 1.897 |
| Bryson Brigman | 4.46 | 3.76 | 0 | 0.010 | 0.009 | 0.000 |
| Sheldon Neuse | 29.60 | 31.85 | 61 | 0.112 | 0.120 | -0.044 |

## Mickey Moniak / 2016 to 2017

Player 666160; row 26836; fold 3; age 18.0; Lower minors; new rank availability 2017-01-28. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | RK124 | 194 | 1 | 35 | 11 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.82, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.006797 | 71.368 | 0.485 | 0.37128 | 0.00180 |
| preseason | 0.040447 | 157.123 | 6.355 | 0.37128 | 0.02354 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Product: 0.040447016 × 157.123101478; offense yield: 0.371275556/600 + 0.003085550.

Actual MLB counts: No MLB PA, not observed zero talent.

Distinct earlier training people in actual profiles:
- baseline participation broad: 1713; rank band 0.
- baseline participation refined: 150; rank band 0.
- baseline conditional_pa broad: 1; rank band 0.
- baseline conditional_pa refined: 0; rank band 0.
- preseason participation broad: 5; rank band 1.
- preseason participation refined: 2; rank band 1.
- preseason conditional_pa broad: 1; rank band 1.
- preseason conditional_pa refined: 0; rank band 1.

Saved baseline participation: reference -4.021534, raw additive prediction -4.984456. Log odds; probability 0.006797.
Largest path terms (accounting, not causal effects):
- draft_rank: input 1.000000, contribution +0.963136.
- on_40man: input 0.000000, contribution -0.421208.
- games_mlb_0: input 0.000000, contribution -0.241469.
- age_centered: input -1.800000, contribution -0.215584.
- age_squared: input 3.240000, contribution -0.164575.

Saved preseason participation: reference -4.078610, raw additive prediction -3.166475. Log odds; probability 0.040447.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.820000, contribution +1.604370.
- draft_rank: input 1.000000, contribution +0.668943.
- on_40man: input 0.000000, contribution -0.423726.
- games_mlb_0: input 0.000000, contribution -0.244916.
- pooled_RK124_BABIP: input 0.326446, contribution +0.157242.

Same fitted candidate with all old ranking inputs restored: 0.003591. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 276.981156, raw additive prediction 71.368097. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 0.000000, contribution -84.775761.
- work_0: input 0.000000, contribution -27.449139.
- on_40man: input 0.000000, contribution -16.912854.
- quality_0: input 0.000000, contribution -8.656251.
- role_pool_AAA: input 4.000000, contribution -8.415376.

Saved preseason conditional_pa: reference 276.994851, raw additive prediction 157.123101. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.820000, contribution +109.994225.
- MLB_0_pa: input 0.000000, contribution -92.600904.
- work_0: input 0.000000, contribution -25.816599.
- on_40man: input 0.000000, contribution -21.422299.
- role_pool_AAA: input 4.000000, contribution -10.092162.

Same fitted candidate with all old ranking inputs restored: 52.380337. Mechanics probe only, not causality or a separately validated replacement forecast.

Moniak's first overall selection, age 18 and 194 rookie PA with one HR acquire a number-19 preseason rank. Rank adds 1.60 log-odds units and about 110 conditional PA. The product remains modest because appearance is only 4.04%: 6.36 expected PA versus zero actual, rather than a full-season assignment. This is nevertheless a deterioration from .49 PA, and there are no refined active training examples; the 157 PA-if-active estimate is unsupported by a close historical profile. Reverting rankings in the fixed fit produces .36% and 52 PA. Lowe, Benson, Stephenson and Kirilloff all fail to arrive. High draft standing raises eventual potential, but low-level exposure reasonably limits immediate MLB use. Do not call this next-year non-arrival zero lifetime value or hide the small false positive.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Josh Lowe | 0.56 | 0.19 | 0 | 0.002 | 0.001 | 0.000 |
| Will Benson | 0.30 | 0.15 | 0 | 0.001 | 0.001 | 0.000 |
| Tyler Stephenson | 0.56 | 0.33 | 0 | 0.002 | 0.001 | 0.000 |
| Alex Kirilloff | 1.03 | 0.37 | 0 | 0.004 | 0.002 | 0.000 |

## Jake Burger / 2017 to 2018

Player 669394; row 31137; fold 4; age 21.0; Lower minors; new rank availability 2018-01-27. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2017 | A | 200 | 4 | 28 | 13 |
| 2017 | RK121 | 17 | 1 | 2 | 1 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.013129 | 85.844 | 1.127 | -0.01534 | 0.00344 |
| preseason | 0.005400 | 71.567 | 0.386 | -0.01534 | 0.00118 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Product: 0.005400116 × 71.567198383; offense yield: -0.015341796/600 + 0.003076176.

Actual MLB counts: No MLB PA, not observed zero talent.

Distinct earlier training people in actual profiles:
- baseline participation broad: 4352; rank band 0.
- baseline participation refined: 897; rank band 0.
- baseline conditional_pa broad: 39; rank band 0.
- baseline conditional_pa refined: 5; rank band 0.
- preseason participation broad: 4320; rank band 0.
- preseason participation refined: 887; rank band 0.
- preseason conditional_pa broad: 27; rank band 0.
- preseason conditional_pa refined: 1; rank band 0.

Saved baseline participation: reference -4.114114, raw additive prediction -4.319697. Log odds; probability 0.013129.
Largest path terms (accounting, not causal effects):
- draft_rank: input 0.684525, contribution +0.633041.
- on_40man: input 0.000000, contribution -0.472378.
- pooled_A_K: input 0.170000, contribution +0.294560.
- games_mlb_0: input 0.000000, contribution -0.179989.
- role_minor_0: input 4.213115, contribution +0.139488.

Saved preseason participation: reference -4.161856, raw additive prediction -5.215920. Log odds; probability 0.005400.
Largest path terms (accounting, not causal effects):
- on_40man: input 0.000000, contribution -0.482265.
- draft_rank: input 0.684525, contribution +0.480010.
- games_mlb_0: input 0.000000, contribution -0.183721.
- games_minor_0: input 51.000000, contribution -0.176133.
- pooled_A_K: input 0.170000, contribution +0.145623.

Same fitted candidate with all old ranking inputs restored: 0.005400. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 283.065211, raw additive prediction 85.844032. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 0.000000, contribution -79.549486.
- work_0: input 0.000000, contribution -28.919931.
- on_40man: input 0.000000, contribution -23.909848.
- draft_rank_low_exposure: input 0.215938, contribution +17.680582.
- regular_window_scaled: input 0.000000, contribution -9.427474.

Saved preseason conditional_pa: reference 283.078808, raw additive prediction 71.567198. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 0.000000, contribution -80.549002.
- on_40man: input 0.000000, contribution -26.603861.
- work_0: input 0.000000, contribution -25.566589.
- regular_window_scaled: input 0.000000, contribution -9.344182.
- role_pool_AAA: input 4.000000, contribution -8.530924.

Same fitted candidate with all old ranking inputs restored: 71.567198. Mechanics probe only, not causality or a separately validated replacement forecast.

Burger has 217 A/rookie PA and five HR, remains unlisted in both adjacent complete tables, and retains zero roster listing. Own scouting values do not change; the old-ranking probe exactly matches the candidate. Expected PA falls 1.13 to .39 solely through the refit, with arrival .54% and conditional PA 72. He has no target-year MLB PA, but the model is not credited with predicting a subsequently known injury. Only one refined active person matches the candidate profile. His peers Lewis, Smith and Haseley gain new preseason listings yet remain low immediate-use forecasts; Warmoth stays unlisted and none arrives. This is a sensible limited immediate expectation, not proof of broad talent rejection or a need to penalize college draftees.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyle Lewis | 6.46 | 4.36 | 0 | 0.020 | 0.013 | 0.000 |
| Pavin Smith | 2.38 | 1.51 | 0 | 0.008 | 0.005 | 0.000 |
| Adam Haseley | 1.65 | 2.37 | 0 | 0.004 | 0.006 | 0.000 |
| Logan Warmoth | 1.92 | 1.35 | 0 | 0.004 | 0.003 | 0.000 |

## Ethan Salas / 2024 to 2025

Player 806956; row 57694; fold 3; age 18.0; Lower minors; new rank availability 2025-01-24. Selected: fixed before fit.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.93, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.68, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.93, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.025632 | 281.842 | 7.224 | -0.51171 | 0.01640 |
| preseason | 0.022453 | 262.436 | 5.892 | -0.51171 | 0.01338 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Product: 0.022453043 × 262.436300245; offense yield: -0.511710571/600 + 0.003122875.

Actual MLB counts: No MLB PA, not observed zero talent.

Distinct earlier training people in actual profiles:
- baseline participation broad: 0; rank band 1.
- baseline participation refined: 0; rank band 1.
- baseline conditional_pa broad: 0; rank band 1.
- baseline conditional_pa refined: 0; rank band 1.
- preseason participation broad: 21; rank band 2.
- preseason participation refined: 8; rank band 2.
- preseason conditional_pa broad: 1; rank band 2.
- preseason conditional_pa refined: 1; rank band 2.

Saved baseline participation: reference -4.049566, raw additive prediction -3.637951. Log odds; probability 0.025632.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.930000, contribution +0.510934.
- games_minor_0: input 111.000000, contribution +0.451357.
- on_40man: input 0.000000, contribution -0.380078.
- scout_listed_0: input 1.000000, contribution +0.332128.
- games_mlb_0: input 0.000000, contribution -0.297719.

Saved preseason participation: reference -4.111470, raw additive prediction -3.773620. Log odds; probability 0.022453.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.680000, contribution +1.238428.
- games_minor_0: input 111.000000, contribution +0.391314.
- on_40man: input 0.000000, contribution -0.386286.
- age_centered: input -1.800000, contribution -0.280447.
- position_2: input 1.000000, contribution +0.273544.

Same fitted candidate with all old ranking inputs restored: 0.034441. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 277.949401, raw additive prediction 281.841619. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.930000, contribution +187.949120.
- work_0: input 0.000000, contribution -95.676289.
- on_40man: input 0.000000, contribution -22.080266.
- pooled_MLB_HBP: input 0.010000, contribution +12.846755.
- role_pool_AAA: input 4.000000, contribution -12.657879.

Saved preseason conditional_pa: reference 277.919440, raw additive prediction 262.436300. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_1: input 0.930000, contribution +109.015667.
- work_0: input 0.000000, contribution -91.839471.
- scout_rank_score_0: input 0.680000, contribution +86.766936.
- on_40man: input 0.000000, contribution -24.396727.
- regular_window_scaled: input 0.000000, contribution -13.069478.

Same fitted candidate with all old ranking inputs restored: 129.872363. Mechanics probe only, not causality or a separately validated replacement forecast.

Salas keeps age 18, 469 A-plus PA and four HR. His latest rank falls from eight to 33 while the old eighth-place rank moves into the previous-list input. Arrival falls 2.56% to 2.25%, conditional PA 282 to 262 and expected PA 7.22 to 5.89 versus zero observed. Earlier-rank history now contributes 109 conditional PA and current rank about 87, showing why the change is not just a universal rank reduction. Old-ranking reversion gives 3.44% appearance but only 130 conditional PA. The two intermediate shifts must be distinguished from a causal rank effect. Refined active support is one person, and all four peers do not arrive. The immediate mean is plausible; its high active branch is thinly supported and does not certify his later catcher or career value.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Yophery Rodriguez | 0.38 | 0.22 | 0 | 0.001 | 0.001 | 0.000 |
| Juan Flores | 0.69 | 0.54 | 0 | 0.001 | 0.001 | 0.000 |
| Filippo Di Turi | 0.35 | 0.17 | 0 | 0.001 | 0.000 | 0.000 |
| Samuel Zavala | 0.46 | 0.35 | 0 | 0.001 | 0.001 | 0.000 |

## Aaron Judge / 2016 to 2017

Player 592450; row 23934; fold 3; age 24.0; Current MLB; new rank availability 2017-01-28. Selected: fixed before fit, major false low.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.7, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.33, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.56, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.7, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.33}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.925862 | 304.039 | 281.499 | -0.03966 | 0.84997 |
| preseason | 0.924997 | 335.052 | 309.922 | -0.03966 | 0.93580 |
| Actual | 1 | not a forecast | 678 | 5.557415626157027 | 8.37188 |

Product: 0.924996978 × 335.052386027; offense yield: -0.039659855/600 + 0.003085550.

Actual MLB counts: 2017: 678 PA, 52 HR, 208 K, 116 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 13; rank band 2.
- baseline participation refined: 13; rank band 2.
- baseline conditional_pa broad: 12; rank band 2.
- baseline conditional_pa refined: 12; rank band 2.
- preseason participation broad: 5; rank band 2.
- preseason participation refined: 5; rank band 2.
- preseason conditional_pa broad: 4; rank band 2.
- preseason conditional_pa refined: 4; rank band 2.

Saved baseline participation: reference -4.021534, raw additive prediction 2.524795. Log odds; probability 0.925862.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.130486.
- games_mlb_0: input 27.000000, contribution +1.179131.
- games_pool_MLB: input 27.000000, contribution +0.568563.
- scout_rank_score_0: input 0.700000, contribution +0.299440.
- MLB_0_pa: input 95.000000, contribution +0.280294.

Saved preseason participation: reference -4.078610, raw additive prediction 2.512262. Log odds; probability 0.924997.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.132957.
- games_mlb_0: input 27.000000, contribution +1.060688.
- scout_rank_score_0: input 0.560000, contribution +0.657869.
- games_pool_MLB: input 27.000000, contribution +0.564445.
- MLB_0_pa: input 95.000000, contribution +0.347969.

Same fitted candidate with all old ranking inputs restored: 0.924997. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 276.981156, raw additive prediction 304.039468. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.700000, contribution +125.260278.
- MLB_0_pa: input 95.000000, contribution -63.349978.
- pooled_MLB_K: input 0.333333, contribution -23.006823.
- work_0: input 95.078254, contribution -22.663525.
- role_pool_AAA: input 4.334651, contribution +15.520093.

Saved preseason conditional_pa: reference 276.994851, raw additive prediction 335.052386. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- scout_rank_score_0: input 0.560000, contribution +97.387567.
- scout_rank_score_1: input 0.700000, contribution +60.368168.
- MLB_0_pa: input 95.000000, contribution -53.874968.
- pooled_MLB_K: input 0.333333, contribution -28.556320.
- work_0: input 95.078254, contribution -20.955822.

Same fitted candidate with all old ranking inputs restored: 297.450392. Mechanics probe only, not causality or a separately validated replacement forecast.

Judge remains the major false low on offense. He had 410 AAA PA with 19 HR and 95 MLB PA with four HR and 42 strikeouts. His latest rank falls 31 to 45, but three-year ranking history changes consistently; current and previous score paths supply about 97 and 60 conditional PA. Appearance stays 92.5%, conditional PA rises 304 to 335 and expected PA 281 to 310 versus 678 with 52 HR. The fixed-fit old-vintage probe gives 297 conditional PA, confirming history rather than a manually favorable latest rank drives part of the increase. Only four refined active profiles support this slice. Cowart is close on PA, Jones remains too low with poor actual offense, Pinder worsens slightly and Healy improves. Neither workload nor the near-average fixed batting forecast anticipates Judge's full breakout; call it partial repair, not success.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kaleb Cowart | 135.24 | 136.35 | 117 | 0.212 | 0.214 | 0.168 |
| JaCoby Jones | 69.81 | 82.82 | 154 | 0.165 | 0.196 | -0.616 |
| Chad Pinder | 162.21 | 147.78 | 309 | 0.259 | 0.236 | 1.012 |
| Ryon Healy | 429.59 | 441.74 | 605 | 1.521 | 1.564 | 2.216 |

## Austin Meadows / 2018 to 2019

Player 640457; row 33319; fold 4; age 23.0; Current MLB; new rank availability 2019-01-27. Selected: largest offense harm.

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

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 1.0, 'scout_rank_score_0': 0.56, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.91, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.81}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 1.0, 'scout_rank_score_1': 0.56, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 1.0, 'scout_rank_score_2': 0.91}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.964692 | 339.187 | 327.211 | -0.13793 | 0.93260 |
| preseason | 0.952220 | 260.504 | 248.057 | -0.13793 | 0.70700 |
| Actual | 1 | not a forecast | 591 | 3.591219010796714 | 5.35765 |

Product: 0.952220301 × 260.503817302; offense yield: -0.137929448/600 + 0.003080035.

Actual MLB counts: 2019: 591 PA, 33 HR, 131 K, 48 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 17; rank band 2.
- baseline participation refined: 17; rank band 2.
- baseline conditional_pa broad: 15; rank band 2.
- baseline conditional_pa refined: 15; rank band 2.
- preseason participation broad: 471; rank band 0.
- preseason participation refined: 470; rank band 0.
- preseason conditional_pa broad: 407; rank band 0.
- preseason conditional_pa refined: 406; rank band 0.

Saved baseline participation: reference -4.184543, raw additive prediction 3.307708. Log odds; probability 0.964692.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.611005.
- games_mlb_0: input 59.000000, contribution +1.430096.
- scout_rank_score_0: input 0.560000, contribution +0.489347.
- quality_0: input 0.112340, contribution +0.462578.
- games_pool_MLB: input 59.000000, contribution +0.460350.

Saved preseason participation: reference -4.219757, raw additive prediction 2.992196. Log odds; probability 0.952220.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.640197.
- games_mlb_0: input 59.000000, contribution +1.583599.
- quality_0: input 0.112340, contribution +0.378423.
- games_pool_MLB: input 59.000000, contribution +0.344296.
- draft_rank: input 0.710926, contribution +0.317087.

Same fitted candidate with all old ranking inputs restored: 0.973587. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 283.064959, raw additive prediction 339.187144. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- quality_0: input 0.112340, contribution +48.782644.
- MLB_0_pa: input 191.000000, contribution -43.139274.
- scout_rank_score_0: input 0.560000, contribution +26.482048.
- scout_listed_0: input 1.000000, contribution +16.991992.
- games_pool_Aplus: input 0.000000, contribution +12.917985.

Saved preseason conditional_pa: reference 283.086863, raw additive prediction 260.503817. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 191.000000, contribution -41.525064.
- quality_0: input 0.112340, contribution +39.522401.
- scout_listed_1: input 1.000000, contribution +19.378453.
- role_pool_MLB: input 3.347826, contribution -17.909420.
- role_mlb_0: input 3.347826, contribution -13.353301.

Same fitted candidate with all old ranking inputs restored: 410.242096. Mechanics probe only, not causality or a separately validated replacement forecast.

Meadows is the largest offense harm. He had 285 AAA PA with twelve HR and 191 MLB PA with six HR in 2018; the dated raw source has 178 MLB at-bats. He therefore already exceeded the 130-AB rookie limit before the 2019 list, so his new absence is a graduation, not proof of lost prospect standing. Rank 45 (.56) shifts to lag one, but zero current rank reduces conditional PA 339 to 261 and expected PA 327 to 248 versus 591 actual. Restoring old ranking inputs in the fixed candidate gives 97.4% arrival and 410 conditional PA, a substantial mechanism change. Arrival itself remains high, so graduation status needs to distinguish the reason for absent current rank in the workload head. Ciuffo is a false high; McGuire is close, Frazier and McKinney underpredicted. This does not justify boosting every graduate, but exposes a concrete representation flaw before adoption.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clint Frazier | 196.99 | 182.76 | 246 | 0.546 | 0.507 | 1.314 |
| Nick Ciuffo | 90.74 | 80.19 | 6 | 0.165 | 0.146 | -0.064 |
| Billy McKinney | 184.39 | 177.97 | 276 | 0.558 | 0.539 | 0.475 |
| Reese McGuire | 117.33 | 111.27 | 105 | 0.223 | 0.212 | 0.813 |

## Chris Davis / 2017 to 2018

Player 448801; row 27537; fold 3; age 31.0; Current MLB; new rank availability 2018-01-27. Selected: major false high.

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.977731 | 518.137 | 506.599 | 1.08164 | 2.47165 |
| preseason | 0.975077 | 515.523 | 502.675 | 1.08164 | 2.45250 |
| Actual | 1 | not a forecast | 522 | -4.101755833580411 | -1.96276 |

Product: 0.975076889 × 515.522980010; offense yield: 1.081635642/600 + 0.003076176.

Actual MLB counts: 2018: 522 PA, 16 HR, 192 K, 39 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 723; rank band 0.
- baseline participation refined: 720; rank band 0.
- baseline conditional_pa broad: 542; rank band 0.
- baseline conditional_pa refined: 541; rank band 0.
- preseason participation broad: 723; rank band 0.
- preseason participation refined: 720; rank band 0.
- preseason conditional_pa broad: 542; rank band 0.
- preseason conditional_pa refined: 541; rank band 0.

Saved baseline participation: reference -4.072655, raw additive prediction 3.782042. Log odds; probability 0.977731.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.316210.
- games_mlb_0: input 128.000000, contribution +1.646415.
- MLB_0_pa: input 524.000000, contribution +0.697600.
- games_pool_MLB: input 349.600000, contribution +0.563022.
- pooled_MLB_pa: input 1458.000000, contribution +0.415482.

Saved preseason participation: reference -4.135062, raw additive prediction 3.666721. Log odds; probability 0.975077.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +3.289472.
- games_mlb_0: input 128.000000, contribution +1.553995.
- MLB_0_pa: input 524.000000, contribution +0.771305.
- games_pool_MLB: input 349.600000, contribution +0.641813.
- pooled_MLB_pa: input 1458.000000, contribution +0.399849.

Same fitted candidate with all old ranking inputs restored: 0.975077. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 278.205818, raw additive prediction 518.137251. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 524.000000, contribution +85.808587.
- role_pool_MLB: input 4.165740, contribution +35.261442.
- role_mlb_0: input 4.086957, contribution +29.409516.
- pooled_Aplus_K: input 0.238095, contribution +28.731419.
- work_0: input 524.000000, contribution +27.012267.

Saved preseason conditional_pa: reference 278.199728, raw additive prediction 515.522980. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- MLB_0_pa: input 524.000000, contribution +81.982997.
- role_pool_MLB: input 4.165740, contribution +33.611574.
- role_mlb_0: input 4.086957, contribution +30.084716.
- work_0: input 524.000000, contribution +27.346201.
- pooled_MLB_pa: input 1458.000000, contribution +21.943456.

Same fitted candidate with all old ranking inputs restored: 515.522980. Mechanics probe only, not causality or a separately validated replacement forecast.

Chris Davis is again the major false high on offense, not a material playing-time error. His HR decline 47 to 38 to 26 in three MLB seasons is present, but hitting is deliberately held fixed at positive 1.08 custom batting wins per 600. New rankings remain all zero and the reversion probe equals the candidate. Refit lowers expected PA 507 to 503 versus 522 observed; offense remains +2.45 versus -1.96. This is no validated improvement in recognizing decline and cannot be fixed by prospect-list dating. His refined profile has 541 earlier active people; poor support is not the explanation here. Guyer/Joseph get more PA than expected, Barney does not arrive and Romine plays weakly. Keep talent decline and playing-time uncertainty separate.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Brandon Guyer | 164.16 | 171.58 | 221 | 0.528 | 0.552 | 0.248 |
| Darwin Barney | 149.58 | 150.13 | 0 | 0.072 | 0.072 | 0.000 |
| Andrew Romine | 190.75 | 181.32 | 131 | 0.147 | 0.140 | -0.667 |
| Caleb Joseph | 187.11 | 186.69 | 280 | 0.114 | 0.114 | -0.762 |

## Ben Rortvedt / 2023 to 2024

Player 666163; row 51344; fold 1; age 25.0; Current MLB; new rank availability 2024-01-26. Selected: ordinary active.

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

Old scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 99.0, 'scout_listed_2': -1.0, 'scout_rank_score_2': -1.0}

New scouting: {'scout_list_available_0': 1.0, 'scout_list_capacity_0': 100.0, 'scout_listed_0': 0.0, 'scout_rank_score_0': 0.0, 'scout_list_available_1': 1.0, 'scout_list_capacity_1': 100.0, 'scout_listed_1': 0.0, 'scout_rank_score_1': 0.0, 'scout_list_available_2': 1.0, 'scout_list_capacity_2': 100.0, 'scout_listed_2': 0.0, 'scout_rank_score_2': 0.0}

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting/600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.870947 | 98.883 | 86.122 | -1.10170 | 0.10851 |
| preseason | 0.873256 | 94.221 | 82.279 | -1.10170 | 0.10366 |
| Actual | 1 | not a forecast | 328 | -1.6693067607876315 | 0.10296 |

Product: 0.873255704 × 94.220872750; offense yield: -1.101698619/600 + 0.003096076.

Actual MLB counts: 2024: 328 PA, 3 HR, 88 K, 34 UBB

Distinct earlier training people in actual profiles:
- baseline participation broad: 657; rank band 0.
- baseline participation refined: 654; rank band 0.
- baseline conditional_pa broad: 565; rank band 0.
- baseline conditional_pa refined: 562; rank band 0.
- preseason participation broad: 740; rank band 0.
- preseason participation refined: 736; rank band 0.
- preseason conditional_pa broad: 638; rank band 0.
- preseason conditional_pa refined: 635; rank band 0.

Saved baseline participation: reference -4.003237, raw additive prediction 1.909361. Log odds; probability 0.870947.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +2.710685.
- games_mlb_0: input 32.000000, contribution +1.220189.
- games_pool_MLB: input 55.400000, contribution +0.559544.
- pooled_MLB_pa: input 137.800000, contribution +0.395043.
- position_2: input 1.000000, contribution +0.393486.

Saved preseason participation: reference -4.033199, raw additive prediction 1.930057. Log odds; probability 0.873256.
Largest path terms (accounting, not causal effects):
- on_40man: input 1.000000, contribution +2.702640.
- games_mlb_0: input 32.000000, contribution +1.231958.
- games_pool_MLB: input 55.400000, contribution +0.606268.
- pooled_MLB_pa: input 137.800000, contribution +0.341837.
- position_2: input 1.000000, contribution +0.328208.

Same fitted candidate with all old ranking inputs restored: 0.873256. Mechanics probe only, not causality or a separately validated replacement forecast.

Saved baseline conditional_pa: reference 283.925540, raw additive prediction 98.882919. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- work_0: input 79.000000, contribution -96.773520.
- quality_0: input -0.300548, contribution -19.565636.
- pooled_MLB_2B: input 0.027754, contribution -15.771879.
- role_pool_AAA: input 4.163441, contribution +14.898700.
- on_40man: input 1.000000, contribution +12.131530.

Saved preseason conditional_pa: reference 283.910666, raw additive prediction 94.220873. Raw PA before the [1,800] bound.
Largest path terms (accounting, not causal effects):
- work_0: input 79.000000, contribution -94.475876.
- quality_0: input -0.300548, contribution -19.983296.
- role_pool_AAA: input 4.163441, contribution +14.896681.
- pooled_MLB_2B: input 0.027754, contribution -12.267785.
- on_40man: input 1.000000, contribution +12.075051.

Same fitted candidate with all old ranking inputs restored: 94.220873. Mechanics probe only, not causality or a separately validated replacement forecast.

Rortvedt is the ordinary-active case selected by a small offense residual, not a successful PA forecast. Recent history includes 79 MLB PA and 124 AAA PA with six HR in 2023, after 98 MLB PA in 2021 and a minor-only 2022. All own ranking inputs remain zero, so the probe is unchanged and the difference comes from shared refitting. Appearance stays about 87%, but conditional PA falls 99 to 94 and expected PA 86 to 82 versus 328 actual. Forecast offense .104 almost matches .103 only because too little playing time offsets a hitting rate -1.10 versus observed -1.67 per 600. That cancellation cannot count as getting the player right. Miranda and McCarthy are underpredicted, Nolan Jones a workload false high and Kieboom does not arrive. His 635 refined earlier active examples show no simple sparse-profile excuse. Future team job circumstances are not retroactively inserted.

| Origin-selected peer | Old PA | New PA | Actual PA | Old offense | New offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jose F Miranda | 224.29 | 232.89 | 429 | 0.533 | 0.553 | 1.653 |
| Nolan Jones | 487.77 | 481.86 | 297 | 2.550 | 2.519 | 0.112 |
| Carter Kieboom | 167.56 | 162.46 | 0 | 0.353 | 0.342 | 0.000 |
| Jake McCarthy | 265.87 | 267.27 | 495 | 0.937 | 0.942 | 1.866 |

## Decision after actual review

Retain the newer preseason ranking source and its qualified prospect-readiness improvement, but do not replace the coherent research candidate or deploy this refit. Never-debut and upper-minor squared errors improve with nominal development intervals below zero; overall intervals span zero, public PA MAE still misses the practical target, and graduation-related workload harm is confirmed. Eleven actual player reviews and all 140 saved-head replays are complete. This is evidence for a source/design extension, not a satisfactory full hitter model.

Run one graduation-aware representation check, not another algorithm sweep: distinguish prospect-list absence caused by known prior MLB at-bats exceeding eligibility from genuine current unlisting, and preserve previous reputation as history rather than a newly observed zero assessment. Verify source coverage and failed/successful graduates before fitting, leave unknown service-day-only graduations unknown, keep the fresher-source and original baselines, and retain all forecast identities. After that resolve the remaining broad workload/talent limitation rather than repeating rank-vintage variants. Protected 2026 and deployed forecasts remain unchanged.
