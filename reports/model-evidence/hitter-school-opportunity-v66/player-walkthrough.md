# School background comparison and actual player review

Same 30,506 historical forecasts and thirty-five chronological whole-player folds. Only three broad school indicators change. The precise-class unknown flag, hitting forecasts, labels, membership and settings remain fixed. No protected 2026 outcomes or production changes. Repeated historical development evidence, not independent confirmation.

| Scope | Rows | Baseline PA RMSE | Candidate PA RMSE | Baseline PA MAE | Candidate PA MAE | Baseline offense RMSE | Candidate offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 30506 | 60.686 | 60.662 | 20.745 | 20.748 | 0.453810 | 0.453698 |
| public_broad | 2627 | 138.488 | 138.387 | 106.871 | 106.890 | 1.061315 | 1.060800 |
| never_debut | 24199 | 27.745 | 27.728 | 4.875 | 4.877 | 0.154066 | 0.153995 |
| upper_never_debut | 5454 | 56.242 | 56.212 | 19.097 | 19.105 | 0.317058 | 0.316919 |
| lower_never_debut | 17852 | 7.828 | 7.830 | 0.656 | 0.657 | 0.042821 | 0.042841 |
| current_MLB | 4541 | 140.980 | 140.939 | 107.900 | 107.912 | 1.113723 | 1.113489 |
| recovered_school | 8179 | 79.616 | 79.630 | 37.540 | 37.571 | 0.612586 | 0.612492 |
| first_year_top_picks | 68 | 113.741 | 113.626 | 35.748 | 35.747 | 0.685287 | 0.685083 |

Losses weight each target year equally. Offense is fixed-event batting plus replacement, not full WAR or trade value. Public forecast archive dating remains qualified. All cohort counts and probability scores are saved separately. No continuous prediction intervals are certified.

Eight cases were locked before fitting. Additional largest gains, harms, false highs/lows and ordinary cases follow fixed score ordering; they are diagnostics, not new independent validation. Four peers use only origin-known age, exposure, draft rank, stage and debut status; their outcomes are then shown without dropping non-arrivals.

## Nick Kurtz from 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0; stage Upper minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Selected pick: 2024/4; class 4YR JR, name Wake Forest. Broad background college; own dated school class or explicit HS/JC name; evidence year 2024. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 0.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.017252 | 115.973 | 2.001 | -0.06322 | 0.00604 |
| Candidate | 0.017423 | 106.638 | 1.858 | -0.06322 | 0.00561 |
| Observed | 1 | not a forecast | 489 | 5.28919 | 5.83778 |

Candidate product: 0.017422872 × 106.637852051; contribution uses (-0.063222554/600 + 0.003122875). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2025: 489 PA, 36 HR, 151 K, 60 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 624 people; background college.
- baseline participation refined: 1 people; background college.
- baseline conditional_pa broad: 6 people; background college.
- baseline conditional_pa refined: 0 people; background college.
- school participation broad: 1677 people; background college.
- school participation refined: 1 people; background college.
- school conditional_pa broad: 10 people; background college.
- school conditional_pa refined: 0 people; background college.

Saved school participation: reference -4.011631, raw additive output -4.032395. This is log odds, not PA; the logistic link gives 0.017423.
Largest exact path contributions:
- draft_rank: input 0.817615, path contribution +0.840577.
- on_40man: input 0.000000, path contribution -0.325946.
- role_pool_A: input 4.411765, path contribution +0.226958.
- games_mlb_0: input 0.000000, path contribution -0.198264.
- games_pool_MLB: input 0.000000, path contribution -0.187234.

Saved baseline participation: reference -4.013758, raw additive output -4.042413. This is log odds, not PA; the logistic link gives 0.017252.
Largest exact path contributions:
- draft_rank: input 0.817615, path contribution +0.833055.
- on_40man: input 0.000000, path contribution -0.325946.
- games_mlb_0: input 0.000000, path contribution -0.198218.
- games_pool_MLB: input 0.000000, path contribution -0.188692.
- role_pool_A: input 4.411765, path contribution +0.186531.

Same candidate fit with this player's old school flags gives 0.017423. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 278.546385, raw additive output 106.637852. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 0.000000, path contribution -99.768459.
- on_40man: input 0.000000, path contribution -23.447390.
- quality_0: input 0.000000, path contribution -13.149481.
- draft_rank: input 0.817615, path contribution +10.951978.
- age_centered: input -1.200000, path contribution +10.558880.

Saved baseline conditional_pa: reference 278.575191, raw additive output 115.972916. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 0.000000, path contribution -99.490116.
- on_40man: input 0.000000, path contribution -23.436218.
- quality_0: input 0.000000, path contribution -13.148363.
- draft_rank: input 0.817615, path contribution +10.742506.
- regular_window_scaled: input 0.000000, path contribution -10.311596.

Same candidate fit with this player's old school flags gives 106.637852. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Kurtz already had pick 4, Wake Forest, and an explicit college junior class. His own three flags do not change; the fixed-fit old-flag probe exactly equals the candidate forecast. Only the training repair can explain the difference. His 50 pro PA include four HR at A and 15 PA at AA. Draft rank raises arrival log odds, but the model still predicts 1.74% arrival and 107 PA if active, versus 489 actual PA and 36 MLB HR. The negative workload path remains large. Zero earlier active people match his refined entry profile in either arm; adding broad college examples does not fix that support gap. Moore and Cam Smith are also substantially underforecast, whereas Montgomery and Jett Williams do not arrive. Thus a universal high-pick boost would create false positives; this test does not resolve fast college entry.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Benny Montgomery | 6.54 | 6.90 | 0 | 0.018 | 0.019 | 0.000 |
| Christian Moore | 8.23 | 8.05 | 184 | 0.025 | 0.025 | 0.242 |
| Cam Smith | 2.33 | 2.00 | 493 | 0.006 | 0.005 | 1.131 |
| Jett Williams | 74.66 | 75.55 | 0 | 0.219 | 0.221 | 0.000 |

## Wyatt Langford from 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0; stage Upper minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

Selected pick: 2023/4; class 4YR JR, name Florida. Broad background college; own dated school class or explicit HS/JC name; evidence year 2023. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 0.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.201829 | 213.556 | 43.102 | 0.68803 | 0.18287 |
| Candidate | 0.210728 | 213.556 | 45.002 | 0.68803 | 0.19093 |
| Observed | 1 | not a forecast | 557 | 0.07695 | 1.79595 |

Candidate product: 0.210727681 × 213.555553050; contribution uses (0.688029041/600 + 0.003096076). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2024: 557 PA, 16 HR, 115 K, 48 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 499 people; background college.
- baseline participation refined: 1 people; background college.
- baseline conditional_pa broad: 3 people; background college.
- baseline conditional_pa refined: 1 people; background college.
- school participation broad: 1552 people; background college.
- school participation refined: 2 people; background college.
- school conditional_pa broad: 7 people; background college.
- school conditional_pa refined: 2 people; background college.

Saved school participation: reference -4.075074, raw additive output -1.320545. This is log odds, not PA; the logistic link gives 0.210728.
Largest exact path contributions:
- role_pool_AA: input 4.272727, path contribution +0.965841.
- draft_rank: input 0.817615, path contribution +0.745834.
- pooled_AA_pa: input 54.000000, path contribution +0.452237.
- on_40man: input 0.000000, path contribution -0.405848.
- role_minor_0: input 4.444444, path contribution +0.400404.

Saved baseline participation: reference -4.088718, raw additive output -1.374901. This is log odds, not PA; the logistic link gives 0.201829.
Largest exact path contributions:
- role_pool_AA: input 4.272727, path contribution +0.965841.
- draft_rank: input 0.817615, path contribution +0.716386.
- pooled_AA_pa: input 54.000000, path contribution +0.452237.
- role_minor_0: input 4.444444, path contribution +0.405194.
- on_40man: input 0.000000, path contribution -0.404258.

Same candidate fit with this player's old school flags gives 0.210728. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 279.215202, raw additive output 213.555553. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 0.000000, path contribution -99.865086.
- role_pool_AAA: input 4.400000, path contribution +37.070129.
- on_40man: input 0.000000, path contribution -18.288035.
- age_centered: input -1.200000, path contribution +14.860035.
- role_pool_AA: input 4.272727, path contribution +13.293606.

Saved baseline conditional_pa: reference 279.215202, raw additive output 213.555553. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 0.000000, path contribution -99.865086.
- role_pool_AAA: input 4.400000, path contribution +37.070129.
- on_40man: input 0.000000, path contribution -18.288035.
- age_centered: input -1.200000, path contribution +14.860035.
- role_pool_AA: input 4.272727, path contribution +13.293606.

Same candidate fit with this player's old school flags gives 213.555553. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Langford's own Florida college junior indicators were already correct, so the fixed-fit flag reversion changes nothing. His 200 PA span rookie, A-plus, AA and AAA, with ten HR and 34 strikeouts. Training repair raises arrival from 20.18% to 21.07%, holding conditional PA at 214, producing 45 expected PA versus 557 observed. The saved paths reward AA exposure and draft rank but retain a roughly minus-100 workload contribution in the conditional head. Refined earlier active support rises only from one person to two. Crews arrives for 132 PA while Shaw and Wilken do not arrive that year; Veen is a false high. These peers forbid interpreting Langford's success as proof all top college picks should receive full-season PA. The source substitution is far too weak to be a readiness solution.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Zac Veen | 85.17 | 84.16 | 0 | 0.241 | 0.238 | 0.000 |
| Dylan Crews | 12.55 | 12.07 | 132 | 0.040 | 0.039 | 0.025 |
| Matt Shaw | 34.13 | 38.32 | 0 | 0.093 | 0.104 | 0.000 |
| Brock Wilken | 6.42 | 6.32 | 0 | 0.022 | 0.022 | 0.000 |

## Cody Bellinger from 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0; stage Upper minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Selected pick: 2013/124; class unknown, name Hamilton (AZ) HS. Broad background hs; own dated school class or explicit HS/JC name; evidence year 2013. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 1, 'draft_jc': 0, 'draft_college': 0}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.110193 | 139.597 | 15.383 | 0.08460 | 0.04963 |
| Candidate | 0.109681 | 141.238 | 15.491 | 0.08460 | 0.04998 |
| Observed | 1 | not a forecast | 548 | 2.92801 | 4.36513 |

Candidate product: 0.109681170 × 141.238268779; contribution uses (0.084595978/600 + 0.003085550). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2017: 548 PA, 39 HR, 146 K, 51 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 1184 people; background unknown.
- baseline participation refined: 113 people; background unknown.
- baseline conditional_pa broad: 50 people; background unknown.
- baseline conditional_pa refined: 27 people; background unknown.
- school participation broad: 461 people; background hs.
- school participation refined: 55 people; background hs.
- school conditional_pa broad: 31 people; background hs.
- school conditional_pa refined: 21 people; background hs.

Saved school participation: reference -4.014067, raw additive output -2.094002. This is log odds, not PA; the logistic link gives 0.109681.
Largest exact path contributions:
- role_pool_AA: input 4.072581, path contribution +0.699191.
- pooled_AA_pa: input 465.000000, path contribution +0.520678.
- games_minor_0: input 117.000000, path contribution +0.484535.
- on_40man: input 0.000000, path contribution -0.425047.
- draft_rank: input 0.365828, path contribution +0.363886.

Saved baseline participation: reference -4.021534, raw additive output -2.088774. This is log odds, not PA; the logistic link gives 0.110193.
Largest exact path contributions:
- role_pool_AA: input 4.072581, path contribution +0.699191.
- pooled_AA_pa: input 465.000000, path contribution +0.534613.
- games_minor_0: input 117.000000, path contribution +0.457330.
- on_40man: input 0.000000, path contribution -0.424700.
- draft_rank: input 0.365828, path contribution +0.377775.

Same candidate fit with this player's old school flags gives 0.109681. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 276.994013, raw additive output 141.238269. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -83.956460.
- work_0: input 0.000000, path contribution -27.449139.
- on_40man: input 0.000000, path contribution -16.912854.
- pooled_AAA_pa: input 12.000000, path contribution +15.849642.
- role_minor_2: input 4.475410, path contribution +15.312682.

Saved baseline conditional_pa: reference 276.981156, raw additive output 139.597326. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -83.956460.
- work_0: input 0.000000, path contribution -27.449139.
- pooled_AAA_pa: input 12.000000, path contribution +18.259827.
- on_40man: input 0.000000, path contribution -16.912854.
- role_minor_2: input 4.475410, path contribution +15.641117.

Same candidate fit with this player's old school flags gives 141.238269. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Bellinger's Hamilton HS background is recovered while precise school class remains unknown. He had 30 A-plus HR in 2015 and 23 AA plus three AAA HR in 2016, not just a tiny pro sample. Yet arrival remains about 11%, conditional PA only 141, and expected PA 15.5 versus 548 actual with 39 MLB HR. The saved classifier rewards AA exposure; the conditional head is still reduced by zero prior MLB PA and the retained on-40-man input. His own flag reversion equals the candidate, so recovery is not directly used along these fitted paths. Twenty-one refined active HS people exist; sparse school coverage alone cannot explain this miss. Verdugo's 25 PA is close to his forecast, while Ward, Westbrook and Kiner-Falefa do not arrive. Inspect the actual roster-field dating next rather than treating all successful AA hitters as guaranteed full-season players.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alex Verdugo | 32.00 | 32.59 | 25 | 0.100 | 0.102 | -0.076 |
| Isiah Kiner-Falefa | 18.75 | 18.03 | 0 | 0.054 | 0.052 | 0.000 |
| Drew Ward | 1.95 | 1.86 | 0 | 0.006 | 0.006 | 0.000 |
| Jamie Westbrook | 4.21 | 4.45 | 0 | 0.010 | 0.011 | 0.000 |

## Pete Alonso from 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0; stage Upper minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Selected pick: 2016/64; class unknown, name Florida. Broad background college; exact institution name in a cutoff-known classified pick; evidence year 2009. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.692850 | 183.403 | 127.071 | 0.28616 | 0.45199 |
| Candidate | 0.676089 | 183.403 | 123.997 | 0.28616 | 0.44105 |
| Observed | 1 | not a forecast | 693 | 3.86456 | 6.59803 |

Candidate product: 0.676089463 × 183.403275318; contribution uses (0.286158486/600 + 0.003080035). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2019: 693 PA, 53 HR, 183 K, 66 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 1450 people; background unknown.
- baseline participation refined: 643 people; background unknown.
- baseline conditional_pa broad: 109 people; background unknown.
- baseline conditional_pa refined: 99 people; background unknown.
- school participation broad: 1158 people; background college.
- school participation refined: 556 people; background college.
- school conditional_pa broad: 107 people; background college.
- school conditional_pa refined: 94 people; background college.

Saved school participation: reference -4.014368, raw additive output 0.735858. This is log odds, not PA; the logistic link gives 0.676089.
Largest exact path contributions:
- games_minor_0: input 132.000000, path contribution +0.989401.
- role_pool_AA: input 4.183771, path contribution +0.915294.
- pooled_AA_pa: input 310.600000, path contribution +0.705914.
- draft_rank: input 0.452844, path contribution +0.540965.
- on_40man: input 0.000000, path contribution -0.466915.

Saved baseline participation: reference -4.017674, raw additive output 0.813478. This is log odds, not PA; the logistic link gives 0.692850.
Largest exact path contributions:
- games_minor_0: input 132.000000, path contribution +0.962217.
- role_pool_AA: input 4.183771, path contribution +0.915294.
- pooled_AA_pa: input 310.600000, path contribution +0.705914.
- draft_rank: input 0.452844, path contribution +0.543319.
- on_40man: input 0.000000, path contribution -0.466915.

Same candidate fit with this player's old school flags gives 0.676089. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 287.128813, raw additive output 183.403275. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -66.383899.
- work_0: input 0.000000, path contribution -42.506976.
- role_pool_AAA: input 4.428571, path contribution +34.618073.
- pooled_AAA_HR: input 0.059850, path contribution +29.557808.
- on_40man: input 0.000000, path contribution -21.980379.

Saved baseline conditional_pa: reference 287.128813, raw additive output 183.403275. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -66.383899.
- work_0: input 0.000000, path contribution -42.506976.
- role_pool_AAA: input 4.428571, path contribution +34.618073.
- pooled_AAA_HR: input 0.059850, path contribution +29.557808.
- on_40man: input 0.000000, path contribution -21.980379.

Same candidate fit with this player's old school flags gives 183.403275. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Alonso's college background is recovered through a cutoff-known exact Florida institution match, without inventing a class year. He had 574 AA/AAA PA and 36 HR in 2018. Arrival decreases from 69.29% to 67.61%; the conditional estimate stays 183, leaving 124 expected PA versus 693 actual and 53 HR. Candidate input reversion gives the same outputs, and neither saved path attributes an effect to his college flag. Refitting affects unrelated splits, not a convincing pedigree mechanism. Ninety-four refined earlier active college people are available. Solak and Mercado are also underforecast, but Brigman does not arrive and Neuse has only 61 PA. This is a broader readiness/workload problem, not evidence that school background or upper-minor power is uninformative.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nick Solak | 33.17 | 35.43 | 135 | 0.071 | 0.075 | 1.169 |
| Óscar Mercado | 87.73 | 83.39 | 482 | 0.158 | 0.150 | 1.897 |
| Bryson Brigman | 4.46 | 4.51 | 0 | 0.010 | 0.010 | 0.000 |
| Sheldon Neuse | 29.60 | 29.24 | 61 | 0.112 | 0.110 | -0.044 |

## Ethan Salas from 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0; stage Lower minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Selected pick: None/None; class unknown, name unknown. Broad background unknown; no usable drafted pick; evidence year None. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.025632 | 281.842 | 7.224 | -0.51171 | 0.01640 |
| Candidate | 0.025632 | 278.043 | 7.127 | -0.51171 | 0.01618 |
| Observed | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product: 0.025631912 × 278.043415085; contribution uses (-0.511710571/600 + 0.003122875). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- No MLB PA; no observed zero talent rate.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 3866 people; background unknown.
- baseline participation refined: 2543 people; background unknown.
- baseline conditional_pa broad: 3 people; background unknown.
- baseline conditional_pa refined: 3 people; background unknown.
- school participation broad: 3866 people; background unknown.
- school participation refined: 2543 people; background unknown.
- school conditional_pa broad: 3 people; background unknown.
- school conditional_pa refined: 3 people; background unknown.

Saved school participation: reference -4.049566, raw additive output -3.637951. This is log odds, not PA; the logistic link gives 0.025632.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +0.510934.
- games_minor_0: input 111.000000, path contribution +0.451357.
- on_40man: input 0.000000, path contribution -0.380078.
- scout_listed_0: input 1.000000, path contribution +0.332128.
- games_mlb_0: input 0.000000, path contribution -0.297719.

Saved baseline participation: reference -4.049566, raw additive output -3.637951. This is log odds, not PA; the logistic link gives 0.025632.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +0.510934.
- games_minor_0: input 111.000000, path contribution +0.451357.
- on_40man: input 0.000000, path contribution -0.380078.
- scout_listed_0: input 1.000000, path contribution +0.332128.
- games_mlb_0: input 0.000000, path contribution -0.297719.

Same candidate fit with this player's old school flags gives 0.025632. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 277.932257, raw additive output 278.043415. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +186.729878.
- work_0: input 0.000000, path contribution -95.676289.
- on_40man: input 0.000000, path contribution -22.080266.
- role_pool_AAA: input 4.000000, path contribution -13.363609.
- games_pool_Aplus: input 118.200000, path contribution -13.120510.

Saved baseline conditional_pa: reference 277.949401, raw additive output 281.841619. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +187.949120.
- work_0: input 0.000000, path contribution -95.676289.
- on_40man: input 0.000000, path contribution -22.080266.
- pooled_MLB_HBP: input 0.010000, path contribution +12.846755.
- role_pool_AAA: input 4.000000, path contribution -12.657879.

Same candidate fit with this player's old school flags gives 278.043415. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Salas has no usable Rule 4 draft record. Unknown stays unknown; this test must not assign him a low signing bonus or a college class. His 469 A-plus PA with four HR at age 18 contrast with 2023 A/AA exposure. Arrival remains 2.56%, with conditional PA near 278 and expected PA 7.1; he has no MLB PA in the target year, so no observed zero hitting talent exists. His prominent prospect rank contributes about 187 conditional PA even though only three earlier active people match the broad or refined age/entry profile. That branch is poorly supported, but the low arrival probability prevents a large unconditional forecast. All four age/exposure peers fail to arrive. A next-year non-arrival is sensible here and does not settle his long-term prospect value.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Yophery Rodriguez | 0.38 | 0.34 | 0 | 0.001 | 0.001 | 0.000 |
| Juan Flores | 0.69 | 0.68 | 0 | 0.001 | 0.001 | 0.000 |
| Filippo Di Turi | 0.35 | 0.33 | 0 | 0.001 | 0.001 | 0.000 |
| Samuel Zavala | 0.46 | 0.48 | 0 | 0.001 | 0.001 | 0.000 |

## Mickey Moniak from 2016 to 2017

Player 666160, row 26836, fold 3; age 18.0; stage Lower minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | RK124 | 194 | 1 | 35 | 11 |

Selected pick: 2016/1; class unknown, name La Costa Canyon (CA) HS. Broad background hs; own dated school class or explicit HS/JC name; evidence year 2016. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 1, 'draft_jc': 0, 'draft_college': 0}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.006797 | 71.368 | 0.485 | 0.37128 | 0.00180 |
| Candidate | 0.007314 | 73.324 | 0.536 | 0.37128 | 0.00199 |
| Observed | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product: 0.007313553 × 73.323951199; contribution uses (0.371275556/600 + 0.003085550). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- No MLB PA; no observed zero talent rate.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 340 people; background unknown.
- baseline participation refined: 16 people; background unknown.
- baseline conditional_pa broad: 0 people; background unknown.
- baseline conditional_pa refined: 0 people; background unknown.
- school participation broad: 273 people; background hs.
- school participation refined: 15 people; background hs.
- school conditional_pa broad: 0 people; background hs.
- school conditional_pa refined: 0 people; background hs.

Saved school participation: reference -4.014067, raw additive output -4.910686. This is log odds, not PA; the logistic link gives 0.007314.
Largest exact path contributions:
- draft_rank: input 1.000000, path contribution +1.002997.
- on_40man: input 0.000000, path contribution -0.423230.
- games_mlb_0: input 0.000000, path contribution -0.241681.
- age_centered: input -1.800000, path contribution -0.203229.
- age_squared: input 3.240000, path contribution -0.162281.

Saved baseline participation: reference -4.021534, raw additive output -4.984456. This is log odds, not PA; the logistic link gives 0.006797.
Largest exact path contributions:
- draft_rank: input 1.000000, path contribution +0.963136.
- on_40man: input 0.000000, path contribution -0.421208.
- games_mlb_0: input 0.000000, path contribution -0.241469.
- age_centered: input -1.800000, path contribution -0.215584.
- age_squared: input 3.240000, path contribution -0.164575.

Same candidate fit with this player's old school flags gives 0.007314. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 276.994013, raw additive output 73.323951. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -84.775761.
- work_0: input 0.000000, path contribution -27.449139.
- on_40man: input 0.000000, path contribution -16.912854.
- quality_0: input 0.000000, path contribution -8.529338.
- role_pool_AAA: input 4.000000, path contribution -8.415376.

Saved baseline conditional_pa: reference 276.981156, raw additive output 71.368097. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -84.775761.
- work_0: input 0.000000, path contribution -27.449139.
- on_40man: input 0.000000, path contribution -16.912854.
- quality_0: input 0.000000, path contribution -8.656251.
- role_pool_AAA: input 4.000000, path contribution -8.415376.

Same candidate fit with this player's old school flags gives 73.323951. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Moniak's explicit La Costa Canyon HS name recovers HS background while exact class stays unknown. His 194 rookie PA with one HR at age 18 and no MLB debut reasonably produce less than one expected MLB PA next year. The candidate moves 0.49 to 0.54 PA, and he does not arrive. Draft rank raises log odds but there are no earlier active people in his age/background entry profile; the conditional estimate is an extrapolation, not a certified interval. The fixed-fit old-flag probe is unchanged, indicating training refit rather than use of his new HS flag. Lowe, Benson, Stephenson and Kirilloff likewise do not arrive in that target season. This is a valuable failed high-pick comparison against fast college arrivals, not a reason to discard Moniak's later career value.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Josh Lowe | 0.56 | 0.57 | 0 | 0.002 | 0.002 | 0.000 |
| Will Benson | 0.30 | 0.32 | 0 | 0.001 | 0.001 | 0.000 |
| Tyler Stephenson | 0.56 | 0.56 | 0 | 0.002 | 0.002 | 0.000 |
| Alex Kirilloff | 1.03 | 0.73 | 0 | 0.004 | 0.003 | 0.000 |

## Dansby Swanson from 2016 to 2017

Player 621020, row 24571, fold 3; age 22.0; stage Current MLB. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | Aminus | 99 | 1 | 14 | 12 |
| 2016 | AA | 377 | 8 | 71 | 33 |
| 2016 | Aplus | 93 | 1 | 13 | 13 |
| 2016 | MLB | 145 | 3 | 34 | 8 |

Selected pick: 2015/1; class unknown, name Vanderbilt. Broad background college; exact institution name in a cutoff-known classified pick; evidence year 2009. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.978522 | 358.742 | 351.037 | -0.32147 | 0.89506 |
| Candidate | 0.981641 | 356.052 | 349.515 | -0.32147 | 0.89118 |
| Observed | 1 | not a forecast | 551 | -2.13738 | -0.26269 |

Candidate product: 0.981641006 × 356.052009724; contribution uses (-0.321467306/600 + 0.003085550). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2017: 551 PA, 6 HR, 120 K, 49 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 21 people; background unknown.
- baseline participation refined: 10 people; background unknown.
- baseline conditional_pa broad: 21 people; background unknown.
- baseline conditional_pa refined: 10 people; background unknown.
- school participation broad: 8 people; background college.
- school participation refined: 4 people; background college.
- school conditional_pa broad: 8 people; background college.
- school conditional_pa refined: 4 people; background college.

Saved school participation: reference -4.014067, raw additive output 3.979106. This is log odds, not PA; the logistic link gives 0.981641.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.077238.
- games_mlb_0: input 38.000000, path contribution +1.209017.
- games_pool_MLB: input 38.000000, path contribution +0.579814.
- MLB_0_pa: input 145.000000, path contribution +0.578978.
- quality_0: input 0.030553, path contribution +0.415260.

Saved baseline participation: reference -4.021534, raw additive output 3.819027. This is log odds, not PA; the logistic link gives 0.978522.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.077238.
- games_mlb_0: input 38.000000, path contribution +1.195120.
- MLB_0_pa: input 145.000000, path contribution +0.578978.
- games_pool_MLB: input 38.000000, path contribution +0.568563.
- quality_0: input 0.030553, path contribution +0.412901.

Same candidate fit with this player's old school flags gives 0.981641. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 276.994013, raw additive output 356.052010. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +155.390785.
- MLB_0_pa: input 145.000000, path contribution -56.187695.
- work_0: input 145.119440, path contribution -22.663525.
- role_pool_AAA: input 4.000000, path contribution -12.299124.
- role_pool_AA: input 4.436170, path contribution +11.218412.

Saved baseline conditional_pa: reference 276.981156, raw additive output 358.742069. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.930000, path contribution +155.390785.
- MLB_0_pa: input 145.000000, path contribution -56.187695.
- work_0: input 145.119440, path contribution -22.663525.
- role_pool_AAA: input 4.000000, path contribution -12.299124.
- role_pool_AA: input 4.436170, path contribution +11.116366.

Same candidate fit with this player's old school flags gives 356.052010. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Swanson's Vanderbilt background is recovered, but he already had 145 MLB PA after 470 AA/A-plus PA in 2016. The retained roster and MLB-games inputs make appearance nearly certain in both arms. Conditional PA declines 359 to 356 and expected PA 351 to 350 versus 551 observed. Offense moves slightly toward the observed negative result, but only because reducing an underpredicted workload masks the retained optimistic batting rate. This is not better playing-time forecasting. College-profile support is only four refined active people after the repair, not an increase for every individual. Bregman and Benintendi get substantial, still underpredicted MLB time; Moran and Cecchini are false highs. The school input reversion leaves Swanson's forecast unchanged, so the tiny value gain is a refitting/cancellation result.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alex Bregman | 504.76 | 504.76 | 626 | 1.523 | 1.523 | 3.825 |
| Colin Moran | 129.84 | 131.37 | 12 | 0.356 | 0.360 | 0.224 |
| Andrew Benintendi | 417.34 | 414.87 | 658 | 1.608 | 1.599 | 2.858 |
| Gavin Cecchini | 213.10 | 215.54 | 82 | 0.456 | 0.462 | -0.337 |

## Jake Burger from 2017 to 2018

Player 669394, row 31137, fold 4; age 21.0; stage Lower minors. Selected for fixed prefit diagnostic.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2017 | A | 200 | 4 | 28 | 13 |
| 2017 | RK121 | 17 | 1 | 2 | 1 |

Selected pick: 2017/11; class unknown, name Missouri State. Broad background college; exact institution name in a cutoff-known classified pick; evidence year 2009. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.013129 | 85.844 | 1.127 | -0.01534 | 0.00344 |
| Candidate | 0.014627 | 85.844 | 1.256 | -0.01534 | 0.00383 |
| Observed | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product: 0.014627218 × 85.844031960; contribution uses (-0.015341796/600 + 0.003076176). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- No MLB PA; no observed zero talent rate.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 1480 people; background unknown.
- baseline participation refined: 13 people; background unknown.
- baseline conditional_pa broad: 7 people; background unknown.
- baseline conditional_pa refined: 4 people; background unknown.
- school participation broad: 885 people; background college.
- school participation refined: 10 people; background college.
- school conditional_pa broad: 4 people; background college.
- school conditional_pa refined: 2 people; background college.

Saved school participation: reference -4.122392, raw additive output -4.210136. This is log odds, not PA; the logistic link gives 0.014627.
Largest exact path contributions:
- draft_rank: input 0.684525, path contribution +0.663249.
- on_40man: input 0.000000, path contribution -0.469865.
- pooled_A_K: input 0.170000, path contribution +0.291850.
- games_mlb_0: input 0.000000, path contribution -0.184434.
- role_minor_0: input 4.213115, path contribution +0.150588.

Saved baseline participation: reference -4.114114, raw additive output -4.319697. This is log odds, not PA; the logistic link gives 0.013129.
Largest exact path contributions:
- draft_rank: input 0.684525, path contribution +0.633041.
- on_40man: input 0.000000, path contribution -0.472378.
- pooled_A_K: input 0.170000, path contribution +0.294560.
- games_mlb_0: input 0.000000, path contribution -0.179989.
- role_minor_0: input 4.213115, path contribution +0.139488.

Same candidate fit with this player's old school flags gives 0.014627. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 283.065211, raw additive output 85.844032. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -79.549486.
- work_0: input 0.000000, path contribution -28.919931.
- on_40man: input 0.000000, path contribution -23.909848.
- draft_rank_low_exposure: input 0.215938, path contribution +17.680582.
- regular_window_scaled: input 0.000000, path contribution -9.427474.

Saved baseline conditional_pa: reference 283.065211, raw additive output 85.844032. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 0.000000, path contribution -79.549486.
- work_0: input 0.000000, path contribution -28.919931.
- on_40man: input 0.000000, path contribution -23.909848.
- draft_rank_low_exposure: input 0.215938, path contribution +17.680582.
- regular_window_scaled: input 0.000000, path contribution -9.427474.

Same candidate fit with this player's old school flags gives 85.844032. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Burger's Missouri State name recovers college background from earlier exact-name evidence without adding class metadata. He had 217 A/rookie PA with five HR in his draft year. Arrival rises 1.31% to 1.46%; conditional PA remains 86, leaving 1.26 expected PA, with no actual MLB PA the following season. We cannot credit the model with foreseeing an injury not present at the origin. The saved classifier has a small path through the HS indicator when it equals zero; the old-flag probe nevertheless gives the same output. Only two refined earlier active college people support the conditional branch. Lewis, Smith, Haseley and Warmoth also do not arrive. Top-pick pedigree is useful background but does not guarantee immediate MLB participation.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyle Lewis | 6.46 | 6.97 | 0 | 0.020 | 0.021 | 0.000 |
| Pavin Smith | 2.38 | 2.18 | 0 | 0.008 | 0.007 | 0.000 |
| Adam Haseley | 1.65 | 1.65 | 0 | 0.004 | 0.004 | 0.000 |
| Logan Warmoth | 1.92 | 1.92 | 0 | 0.004 | 0.004 | 0.000 |

## Matt McLain from 2023 to 2024

Player 680574, row 51984, fold 2; age 23.0; stage Current MLB. Selected for largest delivered gain.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | Aplus | 119 | 3 | 24 | 17 |
| 2021 | RK121 | 7 | 0 | 0 | 0 |
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

Selected pick: 2021/17; class 4YR JR, name UCLA. Broad background college; own dated school class or explicit HS/JC name; evidence year 2021. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 0.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.989318 | 619.741 | 613.121 | 0.91512 | 2.83340 |
| Candidate | 0.988766 | 598.297 | 591.576 | 0.91512 | 2.73383 |
| Observed | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product: 0.988766193 × 598.296985618; contribution uses (0.915119035/600 + 0.003096076). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- No MLB PA; no observed zero talent rate.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 29 people; background college.
- baseline participation refined: 25 people; background college.
- baseline conditional_pa broad: 27 people; background college.
- baseline conditional_pa refined: 23 people; background college.
- school participation broad: 149 people; background college.
- school participation refined: 116 people; background college.
- school conditional_pa broad: 139 people; background college.
- school conditional_pa refined: 107 people; background college.

Saved school participation: reference -4.057192, raw additive output 4.477530. This is log odds, not PA; the logistic link gives 0.988766.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +2.573491.
- games_mlb_0: input 89.000000, path contribution +1.240866.
- work_0: input 403.000000, path contribution +1.056062.
- absence_window_scaled: input 0.666667, path contribution +0.721353.
- pooled_mlb_quality: input 0.672812, path contribution +0.475873.

Saved baseline participation: reference -4.057210, raw additive output 4.528433. This is log odds, not PA; the logistic link gives 0.989318.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +2.573491.
- games_mlb_0: input 89.000000, path contribution +1.245223.
- work_0: input 403.000000, path contribution +1.057377.
- absence_window_scaled: input 0.666667, path contribution +0.719221.
- pooled_mlb_quality: input 0.672812, path contribution +0.460966.

Same candidate fit with this player's old school flags gives 0.988766. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 279.252603, raw additive output 598.296986. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 403.000000, path contribution +98.168335.
- pooled_AAA_HR: input 0.053571, path contribution +37.760889.
- quality_0: input 0.672812, path contribution +35.766560.
- role_mlb_0: input 4.474747, path contribution +31.215041.
- role_pool_MLB: input 4.474747, path contribution +23.317684.

Saved baseline conditional_pa: reference 279.280978, raw additive output 619.741390. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- work_0: input 403.000000, path contribution +98.168335.
- pooled_AAA_HR: input 0.053571, path contribution +38.939389.
- quality_0: input 0.672812, path contribution +37.285894.
- role_mlb_0: input 4.474747, path contribution +31.200431.
- role_pool_MLB: input 4.474747, path contribution +22.966416.

Same candidate fit with this player's old school flags gives 598.296986. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

McLain is the largest offense gain from this substitution, but his own UCLA college indicators were already known. With 403 MLB PA and 16 HR plus 180 AAA PA and 12 HR, a high arrival probability at this origin is not itself unreasonable. The candidate remains 98.88% likely to play and reduces conditional PA 620 to 598, yielding 592 expected PA versus zero actual. The school contribution within the regressor shrinks from about six to 1.5 PA, alongside other refitted splits. This is not a model that correctly anticipates his full missed season: the largest gain simply trims an enormous residual by 22 PA. Bo Naylor's 389 PA is well matched, Frelick is underforecast, Baty and Pratto overforecast. Do not use a subsequently known injury or this gain to justify a new injury rule.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sal Frelick | 366.55 | 367.71 | 524 | 1.200 | 1.203 | 0.427 |
| Brett Baty | 394.69 | 394.89 | 171 | 1.108 | 1.108 | -0.013 |
| Bo Naylor | 386.20 | 385.79 | 389 | 1.381 | 1.380 | -0.463 |
| Nick Pratto | 257.71 | 255.85 | 0 | 0.765 | 0.759 | 0.000 |

## Marcell Ozuna from 2016 to 2017

Player 542303, row 23518, fold 2; age 25.0; stage Current MLB. Selected for largest delivered harm.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | MLB | 612 | 23 | 164 | 40 |
| 2015 | AAA | 132 | 5 | 23 | 10 |
| 2015 | MLB | 494 | 10 | 110 | 29 |
| 2016 | MLB | 608 | 23 | 115 | 41 |

Selected pick: None/None; class unknown, name unknown. Broad background unknown; no usable drafted pick; evidence year None. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.992745 | 573.031 | 568.874 | 0.84865 | 2.55991 |
| Candidate | 0.992745 | 559.504 | 555.445 | 0.84865 | 2.49948 |
| Observed | 1 | not a forecast | 679 | 3.66460 | 6.24220 |

Candidate product: 0.992745188 × 559.503596575; contribution uses (0.848647673/600 + 0.003085550). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2017: 679 PA, 37 HR, 144 K, 60 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 137 people; background unknown.
- baseline participation refined: 129 people; background unknown.
- baseline conditional_pa broad: 115 people; background unknown.
- baseline conditional_pa refined: 112 people; background unknown.
- school participation broad: 137 people; background unknown.
- school participation refined: 129 people; background unknown.
- school conditional_pa broad: 115 people; background unknown.
- school conditional_pa refined: 112 people; background unknown.

Saved school participation: reference -3.960754, raw additive output 4.918809. This is log odds, not PA; the logistic link gives 0.992745.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +2.741954.
- games_mlb_0: input 148.000000, path contribution +1.839330.
- games_pool_MLB: input 338.200000, path contribution +1.201989.
- quality_0: input 0.233286, path contribution +0.842525.
- MLB_0_pa: input 608.000000, path contribution +0.469597.

Saved baseline participation: reference -3.960754, raw additive output 4.918809. This is log odds, not PA; the logistic link gives 0.992745.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +2.741954.
- games_mlb_0: input 148.000000, path contribution +1.839330.
- games_pool_MLB: input 338.200000, path contribution +1.201989.
- quality_0: input 0.233286, path contribution +0.842525.
- MLB_0_pa: input 608.000000, path contribution +0.469597.

Same candidate fit with this player's old school flags gives 0.992745. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 281.424868, raw additive output 559.503597. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 608.000000, path contribution +125.433004.
- quality_0: input 0.233286, path contribution +35.388727.
- role_mlb_0: input 4.101266, path contribution +32.254491.
- games_mlb_2: input 153.000000, path contribution +24.991031.
- work_0: input 608.500824, path contribution +24.842296.

Saved baseline conditional_pa: reference 281.415167, raw additive output 573.031448. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 608.000000, path contribution +125.694636.
- quality_0: input 0.233286, path contribution +35.512413.
- role_mlb_0: input 4.101266, path contribution +31.219332.
- age_centered: input -0.400000, path contribution +26.773454.
- games_mlb_2: input 153.000000, path contribution +25.914006.

Same candidate fit with this player's old school flags gives 559.503597. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Ozuna has no drafted school input and all three indicators stay zero. His 2016 MLB sample is 608 PA with 23 HR and 115 strikeouts, following substantial MLB seasons in 2014 and 2015. Arrival stays 99.27%, but training refit lowers conditional PA 573 to 560 and expected PA 569 to 555 versus 679 actual. That worsens the largest delivered-offense loss because the fixed batting forecast also misses his 2017 production. The changed school representation influences shared tree splits even for non-drafted players; it is not evidence about Ozuna's background. The old-flag probe exactly matches the candidate. Nearby peers include overpredicted Tomas and Diaz, and underpredicted Inciarte, so indiscriminately raising all established players would not fix the ranking.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jonathan Villar | 550.31 | 550.31 | 436 | 2.323 | 2.323 | 0.326 |
| Yasmany Tomás | 473.59 | 473.40 | 180 | 1.640 | 1.639 | 0.653 |
| Ender Inciarte | 479.73 | 476.46 | 718 | 1.770 | 1.758 | 2.919 |
| Aledmys Díaz | 544.48 | 548.42 | 301 | 1.661 | 1.673 | 0.319 |

## Chris Davis from 2017 to 2018

Player 448801, row 27537, fold 3; age 31.0; stage Current MLB. Selected for major false high.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

Selected pick: 2006/148; class unknown, name Navarro College. Broad background unknown; no exact dated institution match; evidence year None. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.977731 | 518.137 | 506.599 | 1.08164 | 2.47165 |
| Candidate | 0.977731 | 518.137 | 506.599 | 1.08164 | 2.47165 |
| Observed | 1 | not a forecast | 522 | -4.10176 | -1.96276 |

Candidate product: 0.977731064 × 518.137250825; contribution uses (1.081635642/600 + 0.003076176). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2018: 522 PA, 16 HR, 192 K, 39 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 251 people; background unknown.
- baseline participation refined: 196 people; background unknown.
- baseline conditional_pa broad: 186 people; background unknown.
- baseline conditional_pa refined: 151 people; background unknown.
- school participation broad: 40 people; background unknown.
- school participation refined: 36 people; background unknown.
- school conditional_pa broad: 32 people; background unknown.
- school conditional_pa refined: 29 people; background unknown.

Saved school participation: reference -4.072655, raw additive output 3.782042. This is log odds, not PA; the logistic link gives 0.977731.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.316210.
- games_mlb_0: input 128.000000, path contribution +1.646415.
- MLB_0_pa: input 524.000000, path contribution +0.697600.
- games_pool_MLB: input 349.600000, path contribution +0.563022.
- pooled_MLB_pa: input 1458.000000, path contribution +0.415482.

Saved baseline participation: reference -4.072655, raw additive output 3.782042. This is log odds, not PA; the logistic link gives 0.977731.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.316210.
- games_mlb_0: input 128.000000, path contribution +1.646415.
- MLB_0_pa: input 524.000000, path contribution +0.697600.
- games_pool_MLB: input 349.600000, path contribution +0.563022.
- pooled_MLB_pa: input 1458.000000, path contribution +0.415482.

Same candidate fit with this player's old school flags gives 0.977731. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 278.205818, raw additive output 518.137251. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 524.000000, path contribution +85.808587.
- role_pool_MLB: input 4.165740, path contribution +35.261442.
- role_mlb_0: input 4.086957, path contribution +29.409516.
- pooled_Aplus_K: input 0.238095, path contribution +28.731419.
- work_0: input 524.000000, path contribution +27.012267.

Saved baseline conditional_pa: reference 278.205818, raw additive output 518.137251. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- MLB_0_pa: input 524.000000, path contribution +85.808587.
- role_pool_MLB: input 4.165740, path contribution +35.261442.
- role_mlb_0: input 4.086957, path contribution +29.409516.
- pooled_Aplus_K: input 0.238095, path contribution +28.731419.
- work_0: input 524.000000, path contribution +27.012267.

Same candidate fit with this player's old school flags gives 518.137251. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Chris Davis remains the major false high in offense, not a playing-time miss. His MLB HR decline from 47 to 38 to 26 and latest strikeout rate is high, but the fixed hitting forecast still projects positive batting value per 600. Both arms give exactly 507 expected PA versus 522 observed; actual offense is negative after 16 HR and 192 strikeouts. No school repair touches the forecast. Navarro College remains unknown because no exact dated institution match was found; it must not be manually classified from his future outcome. The saved workload paths use prior MLB volume and roles. This case belongs to hitting decline/uncertainty review, not arrival calibration. Peers include Barney's non-arrival and weak production from Romine/Joseph, showing retirement and performance risks differ.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Brandon Guyer | 164.16 | 159.46 | 221 | 0.528 | 0.513 | 0.248 |
| Darwin Barney | 149.58 | 150.85 | 0 | 0.072 | 0.073 | 0.000 |
| Andrew Romine | 190.75 | 191.73 | 131 | 0.147 | 0.148 | -0.667 |
| Caleb Joseph | 187.11 | 186.75 | 280 | 0.114 | 0.114 | -0.762 |

## Aaron Judge from 2016 to 2017

Player 592450, row 23934, fold 3; age 24.0; stage Current MLB. Selected for major false low.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Selected pick: 2013/32; class unknown, name Fresno State. Broad background college; exact institution name in a cutoff-known classified pick; evidence year 2009. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 0} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 1.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.925862 | 304.039 | 281.499 | -0.03966 | 0.84997 |
| Candidate | 0.925584 | 306.974 | 284.130 | -0.03966 | 0.85792 |
| Observed | 1 | not a forecast | 678 | 5.55742 | 8.37188 |

Candidate product: 0.925583760 × 306.973686853; contribution uses (-0.039659855/600 + 0.003085550). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2017: 678 PA, 52 HR, 208 K, 116 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 79 people; background unknown.
- baseline participation refined: 68 people; background unknown.
- baseline conditional_pa broad: 75 people; background unknown.
- baseline conditional_pa refined: 63 people; background unknown.
- school participation broad: 81 people; background college.
- school participation refined: 70 people; background college.
- school conditional_pa broad: 77 people; background college.
- school conditional_pa refined: 65 people; background college.

Saved school participation: reference -4.014067, raw additive output 2.520750. This is log odds, not PA; the logistic link gives 0.925584.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.132772.
- games_mlb_0: input 27.000000, path contribution +1.192549.
- games_pool_MLB: input 27.000000, path contribution +0.568511.
- MLB_0_pa: input 95.000000, path contribution +0.291929.
- scout_rank_score_0: input 0.700000, path contribution +0.286652.

Saved baseline participation: reference -4.021534, raw additive output 2.524795. This is log odds, not PA; the logistic link gives 0.925862.
Largest exact path contributions:
- on_40man: input 1.000000, path contribution +3.130486.
- games_mlb_0: input 27.000000, path contribution +1.179131.
- games_pool_MLB: input 27.000000, path contribution +0.568563.
- scout_rank_score_0: input 0.700000, path contribution +0.299440.
- MLB_0_pa: input 95.000000, path contribution +0.280294.

Same candidate fit with this player's old school flags gives 0.925584. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 276.994013, raw additive output 306.973687. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.700000, path contribution +125.260278.
- MLB_0_pa: input 95.000000, path contribution -63.349978.
- work_0: input 95.078254, path contribution -22.663525.
- pooled_MLB_K: input 0.333333, path contribution -22.527384.
- role_pool_AAA: input 4.334651, path contribution +15.520093.

Saved baseline conditional_pa: reference 276.981156, raw additive output 304.039468. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.700000, path contribution +125.260278.
- MLB_0_pa: input 95.000000, path contribution -63.349978.
- pooled_MLB_K: input 0.333333, path contribution -23.006823.
- work_0: input 95.078254, path contribution -22.663525.
- role_pool_AAA: input 4.334651, path contribution +15.520093.

Same candidate fit with this player's old school flags gives 306.973687. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Judge's Fresno State background is recovered, but both participation models were already above 92%. His origin includes 410 AAA PA, 19 HR and 98 strikeouts, followed by 95 MLB PA with four HR and 42 strikeouts. Expected PA improves 281 to 284 because conditional PA moves 304 to 307; actual is 678 with 52 HR. The saved paths reward rank and roster status but still penalize low MLB exposure and MLB strikeouts. College flags have no direct path contribution for Judge, and the reversion probe matches the candidate. His fixed hitting rate is approximately average, so the largest low offense error combines workload and a real breakout miss; school recovery fixes neither. Cowart's 117 PA is close, Jones gets 154 with poor offense, Pinder and Healy are underforecast. No player-specific guarantee is warranted.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kaleb Cowart | 135.24 | 136.66 | 117 | 0.212 | 0.214 | 0.168 |
| JaCoby Jones | 69.81 | 64.43 | 154 | 0.165 | 0.152 | -0.616 |
| Chad Pinder | 162.21 | 162.21 | 309 | 0.259 | 0.259 | 1.012 |
| Ryon Healy | 429.59 | 433.16 | 605 | 1.521 | 1.534 | 2.216 |

## Henry Davis from 2022 to 2023

Player 680779, row 48210, fold 4; age 22.0; stage Upper minors. Selected for ordinary active.

| Source season | Level | PA | HR | K | Unintentional walks |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | Aplus | 24 | 2 | 8 | 4 |
| 2021 | RK124 | 7 | 1 | 2 | 0 |
| 2022 | A | 15 | 1 | 2 | 1 |
| 2022 | AA | 136 | 4 | 30 | 12 |
| 2022 | Aplus | 100 | 5 | 18 | 8 |
| 2022 | RK124 | 4 | 0 | 1 | 0 |

Selected pick: 2021/1; class 4YR JR, name Louisville. Broad background college; own dated school class or explicit HS/JC name; evidence year 2021. Exact old/new indicators: {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1} → {'draft_hs': 0, 'draft_jc': 0, 'draft_college': 1}. Precise class-unknown input remains 0.

| Forecast | Any MLB PA probability | PA if active | Expected PA | Fixed hitting per 600 | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.514661 | 273.810 | 140.919 | -0.19777 | 0.39477 |
| Candidate | 0.479293 | 271.119 | 129.946 | -0.19777 | 0.36402 |
| Observed | 1 | not a forecast | 255 | -1.02477 | 0.36287 |

Candidate product: 0.479292728 × 271.119433738; contribution uses (-0.197768982/600 + 0.003130974). Hitting is held fixed, not newly neutralized or learned. Actual MLB counts:
- 2023: 255 PA, 7 HR, 69 K, 23 walks.

Distinct training people in the actual background/entry profiles:
- baseline participation broad: 63 people; background college.
- baseline participation refined: 1 people; background college.
- baseline conditional_pa broad: 6 people; background college.
- baseline conditional_pa refined: 1 people; background college.
- school participation broad: 879 people; background college.
- school participation refined: 14 people; background college.
- school conditional_pa broad: 31 people; background college.
- school conditional_pa refined: 6 people; background college.

Saved school participation: reference -4.081834, raw additive output -0.082876. This is log odds, not PA; the logistic link gives 0.479293.
Largest exact path contributions:
- role_pool_AA: input 4.292683, path contribution +1.020697.
- scout_rank_score_0: input 0.770000, path contribution +0.905896.
- pooled_AA_pa: input 136.000000, path contribution +0.784478.
- draft_rank: input 1.000000, path contribution +0.737471.
- on_40man: input 0.000000, path contribution -0.435708.

Saved baseline participation: reference -4.073345, raw additive output 0.058663. This is log odds, not PA; the logistic link gives 0.514661.
Largest exact path contributions:
- role_pool_AA: input 4.292683, path contribution +1.044292.
- scout_rank_score_0: input 0.770000, path contribution +0.920335.
- draft_rank: input 1.000000, path contribution +0.805399.
- pooled_AA_pa: input 136.000000, path contribution +0.784478.
- on_40man: input 0.000000, path contribution -0.436197.

Same candidate fit with this player's old school flags gives 0.479293. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Saved school conditional_pa: reference 278.670923, raw additive output 271.119434. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.770000, path contribution +104.557681.
- work_0: input 0.000000, path contribution -101.835732.
- on_40man: input 0.000000, path contribution -14.292165.
- role_pool_AA: input 4.292683, path contribution +12.328532.
- pooled_mlb_quality: input 0.000000, path contribution -10.102161.

Saved baseline conditional_pa: reference 278.684289, raw additive output 273.809514. Conditional PA is bounded only after this calculation.
Largest exact path contributions:
- scout_rank_score_0: input 0.770000, path contribution +103.162316.
- work_0: input 0.000000, path contribution -101.829472.
- on_40man: input 0.000000, path contribution -14.292165.
- role_pool_AA: input 4.292683, path contribution +11.493019.
- pooled_mlb_quality: input 0.000000, path contribution -10.153950.

Same candidate fit with this player's old school flags gives 271.119434. This is an input-path probe, not a causal estimate or a validated replacement forecast. Changes with unchanged own flags reflect refitting on repaired training evidence.

Henry Davis is the ordinary-active case selected by small offense residual, not by baseball similarity or a successful PA forecast. His own Louisville college junior metadata was already complete. He had 255 pro PA in 2022 spanning AA and lower levels with ten HR; the candidate lowers arrival 51.47% to 47.93% and expected PA 141 to 130, whereas he actually gets 255 MLB PA. Candidate offense .364 happens to match .363 observed because the retained hitting forecast is too optimistic for his actual MLB production. Thus a smaller offense residual masks a worse workload estimate. Rank/AA exposure raise arrival, while workload lowers conditional PA; background recovery adds six refined active training people but does not cure the miss. Gonzales is closer on PA with poorer offense; Beck, Lee and Wilson do not arrive. This is why component checks accompany total-value scores.

| Origin selected peer | Baseline PA | Candidate PA | Actual PA | Baseline offense | Candidate offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Austin Beck | 1.09 | 1.09 | 0 | 0.002 | 0.002 | 0.000 |
| Nick Gonzales | 150.80 | 152.40 | 128 | 0.466 | 0.471 | -0.021 |
| Brooks Lee | 4.15 | 4.08 | 0 | 0.014 | 0.013 | 0.000 |
| Will Wilson | 32.90 | 30.00 | 0 | 0.055 | 0.051 | 0.000 |

## Decision after actual review

Do not promote the school-substitution forecast. Preserve the reviewed school facts for future inputs, but retain V53/V63 forecasts as the research candidate. The tiny pooled RMSE reduction has nominal development intervals spanning zero, slightly worse PA MAE and appearance scoring, no meaningful first-year top-pick improvement, continued upper-minor underprediction and lower-minor overprediction. All thirteen actual player reviews and saved-head replays are complete. This negative comparison does not reject pedigree or readiness information generally.

Before another fit, verify whether the retained roster and scouting fields actually represent the forecast origin. Bellinger's on-40-man zero and fast new-draftee readiness gaps warrant a bounded source-timing check against existing dated roster/transaction and ranking captures, including failed peers. Repair a demonstrated material source defect before choosing a new readiness architecture. Do not repeat a generic algorithm, penalty or school-flag sweep. The overall practical hitter goal remains active; protected 2026 and deployed forecasts are unchanged.
