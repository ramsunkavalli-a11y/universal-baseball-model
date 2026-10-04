# Fresher rankings and the smooth prospect model

Retain the fresher-ranking tree candidate. The exact smooth opportunity model benefits from fresher rankings relative to its own old-source version, but does not clearly beat the current candidate on delivered offense. Keep the matched smooth results as development evidence, not a new deployed model or a general rejection of smooth models.

The same 30,506 forecasts and 171 prospect inputs are retained. Only eight ranking-vintage inputs change in the matched smooth contrast. Established-player forecasts and the 199-input hitting model remain fixed. Target: next-calendar-year MLB use and custom batting plus replacement, not full WAR, career quality or six years of control.

| Group | Rows | Fresh tree PA RMSE | Old smooth PA RMSE | Fresh smooth PA RMSE | Fresh tree MAE | Fresh smooth MAE | Fresh tree offense RMSE | Fresh smooth offense RMSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 30506 | 60.499 | 60.604 | 60.442 | 20.612 | 20.532 | 0.453384 | 0.453389 |
| never_debut | 24199 | 27.252 | 27.547 | 27.098 | 4.764 | 4.663 | 0.152257 | 0.152316 |
| upper_never_debut | 5454 | 55.127 | 55.792 | 54.773 | 18.732 | 18.397 | 0.312832 | 0.312277 |
| lower_never_debut | 17852 | 7.966 | 7.923 | 7.990 | 0.622 | 0.598 | 0.043039 | 0.043132 |
| public_broad | 2627 | 138.330 | 138.330 | 138.330 | 106.411 | 106.411 | 1.060504 | 1.060504 |
| new_draftees | 2205 | 23.192 | 22.345 | 22.270 | 2.129 | 2.244 | 0.163825 | 0.162233 |
| thin_pro | 5317 | 11.372 | 10.975 | 11.000 | 0.612 | 0.605 | 0.088416 | 0.087603 |

Losses weight target years equally. Raw totals are not rescaled; intervals are paired whole-player development evidence. Release dates are documented, but first-publication ranking table vintages and equal public-forecast information dates remain unverified.

The original review ID for the named Maitan case selected Burger. Both are retained, with the correction recorded separately. The largest raw conditional-PA case is added by an ordered boundary rule; no forecast or original selection is removed.

## Nick Kurtz 2024 to 2025

ID 701762; row 57052; fold 2; age input 21.0; Upper minors. Information date 2025-01-24. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.63 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.017252 | 115.973 | 2.001 | -0.06322 | 0.00604 |
| preseason | 0.060561 | 168.160 | 10.184 | -0.06322 | 0.03073 |
| old_smooth | 0.125809 | 223.707 | 28.144 | -0.06322 | 0.08493 |
| smooth_preseason | 0.135364 | 208.348 | 28.203 | -0.06322 | 0.08510 |
| Actual | 1 | not a forecast | 489 | 5.289191738139299 | 5.83778 |

Candidate product 0.135363828 × 208.347727195; offense yield -0.063222554/600 + 0.003122875.

Actual MLB counts: [{'season': 2025, 'player_id': 701762, 'bucket': 'MLB', 'plate_appearances': 489, 'strike_outs': 151, 'unintentional_walks': 60, 'hit_by_pitch': 2, 'home_runs': 36, 'babip_hits': 86, 'doubles': 26, 'triples': 2, 'babip_opportunities': 236}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 842 |
| old_smooth | participation | refined | 14 |
| old_smooth | conditional_pa | broad | 158 |
| old_smooth | conditional_pa | refined | 0 |
| smooth_preseason | participation | broad | 54 |
| smooth_preseason | participation | refined | 1 |
| smooth_preseason | conditional_pa | broad | 31 |
| smooth_preseason | conditional_pa | refined | 0 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.853916; additive output -1.854343; linked output 0.135364.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.093573, standardized input 8.192, contribution +0.982588.
- draft_rank: input 0.817615, training scale 0.159197, standardized input 4.432, contribution +0.933673.
- scout_listed_0: input 1.000000, training scale 0.320040, standardized input 3.378, contribution +0.658217.
- age_upper_interaction: input -1.200000, training scale 0.283029, standardized input -3.882, contribution +0.617515.
- pooled_A_HR: input 0.051852, training scale 0.006333, standardized input 3.881, contribution +0.550559.
- draft_upper_interaction: input 0.817615, training scale 0.107986, standardized input 7.243, contribution +0.462908.
- position_3: input 1.000000, training scale 0.312386, standardized input 2.850, contribution -0.390016.
- highest_AA: input 1.000000, training scale 0.308303, standardized input 2.899, contribution +0.222383.

Largest ranking contributions on this same fit: scout_listed_0 +0.658217, scout_rank_score_0 +0.129738, scout_rank_score_1 -0.041936, scout_listed_2 +0.026652. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.853997; additive output -1.938538; linked output 0.125809.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.093573, standardized input 8.192, contribution +1.233901.
- draft_rank: input 0.817615, training scale 0.159197, standardized input 4.432, contribution +0.976585.
- age_upper_interaction: input -1.200000, training scale 0.283029, standardized input -3.882, contribution +0.668207.
- pooled_A_HR: input 0.051852, training scale 0.006333, standardized input 3.881, contribution +0.577534.
- draft_upper_interaction: input 0.817615, training scale 0.107986, standardized input 7.243, contribution +0.446420.
- position_3: input 1.000000, training scale 0.312386, standardized input 2.850, contribution -0.405918.
- highest_AA: input 1.000000, training scale 0.308303, standardized input 2.899, contribution +0.249121.
- draft_rank_low_exposure: input 0.545076, training scale 0.052057, standardized input 9.977, contribution +0.223454.

Largest ranking contributions on this same fit: scout_listed_0 +0.032366, scout_rank_score_2 +0.020777, scout_listed_1 +0.020161, scout_listed_2 +0.012423. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.070634. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 114.294911; additive output 208.347727; linked output 208.347727.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.630000, training scale 0.389621, standardized input 1.553, contribution +35.788026.
- recent_draft_rank: input 0.817615, training scale 0.109716, standardized input 6.731, contribution +28.453091.
- draft_rank_low_exposure: input 0.545076, training scale 0.047117, standardized input 10.938, contribution -23.070130.
- reorganized: input 1.000000, training scale 0.458079, standardized input 1.529, contribution -20.311018.
- pooled_A_BB: input 0.133333, training scale 0.016913, standardized input 2.945, contribution +18.463660.
- draft_rank: input 0.817615, training scale 0.235062, standardized input 2.308, contribution +15.564715.
- age_upper_interaction: input -1.200000, training scale 0.459614, standardized input -1.333, contribution +14.978840.
- draft_elapsed: input 0.000000, training scale 0.214649, standardized input -1.188, contribution +14.529707.

Largest ranking contributions on this same fit: scout_rank_score_0 +35.788026, scout_listed_0 +8.047457, scout_rank_score_2 +2.244649, scout_rank_score_1 +1.736249. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 114.230022; additive output 223.707331; linked output 223.707331.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.109716, standardized input 6.731, contribution +45.715231.
- pooled_A_BB: input 0.133333, training scale 0.016913, standardized input 2.945, contribution +21.198470.
- draft_rank: input 0.817615, training scale 0.235062, standardized input 2.308, contribution +15.221189.
- age_upper_interaction: input -1.200000, training scale 0.459614, standardized input -1.333, contribution +14.923829.
- reorganized: input 1.000000, training scale 0.458079, standardized input 1.529, contribution -14.288557.
- draft_elapsed: input 0.000000, training scale 0.214649, standardized input -1.188, contribution +14.086708.
- log_minor_pa_1: input 0.000000, training scale 0.649516, standardized input -2.095, contribution +13.449194.
- age_squared: input 1.440000, training scale 0.616125, standardized input 1.143, contribution +13.124887.

Largest ranking contributions on this same fit: scout_rank_score_0 +3.773390, scout_rank_score_2 +2.816264, scout_listed_2 +2.437196, scout_listed_1 -1.774031. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 162.178297. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.984778; prediction -0.063223. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.200000, contribution +0.619142.
- reorganized: scaled input 1.000000, contribution -0.263145.
- draft_rank: scaled input 0.817615, contribution +0.165486.
- position_3: scaled input 1.000000, contribution +0.134554.
- age_squared: scaled input 1.440000, contribution +0.077598.
- absence_window_scaled: scaled input 1.000000, contribution -0.060767.
- pooled_A_BB: scaled input 0.533333, contribution +0.059321.
- draft_college: scaled input 1.000000, contribution +0.057207.

Kurtz has only 35 A and 15 AA PA, with four HR and twelve unintentional walks in total; his ranking becomes 38. The new smooth model assigns 13.54% appearance and 208.35 conditional PA, producing 28.20 versus 10.18 for the fresher trees and 489 actual. The old smooth estimate was already 28.14: the new source does not materially improve this case because refitted conditional PA falls while appearance probability rises. On the new fit, old ranking inputs give 7.06% and 162.18 PA, showing a favorable within-fit ranking effect, not a causal gain. Exact active-head elite/thin/draft-year support is zero. Moore and Cam Smith play, Williams and Montgomery do not. The fixed hitting head is -0.0632 wins/600, with age and position much stronger than his tiny minor sample, versus a 5.2892 realized breakout. This is a large unresolved readiness/talent miss, not proof that the model should predict that specific breakout or give every top pick 489 PA.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Christian Moore | 22.35 | 72.09 | 184 | 0.221 | 0.242 |
| Cam Smith | 9.98 | 32.35 | 493 | 0.087 | 1.131 |
| Jett Williams | 100.55 | 28.45 | 0 | 0.083 | 0.000 |
| Benny Montgomery | 5.41 | 3.31 | 0 | 0.009 | 0.000 |

## Wyatt Langford 2023 to 2024

ID 694671; row 53164; fold 4; age input 21.0; Upper minors. Information date 2024-01-26. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.95 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | -1 | 0 |
| scout_rank_score_2 | -1 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.201829 | 213.556 | 43.102 | 0.68803 | 0.18287 |
| preseason | 0.599098 | 358.735 | 214.918 | 0.68803 | 0.91185 |
| old_smooth | 0.729966 | 293.808 | 214.470 | 0.68803 | 0.90995 |
| smooth_preseason | 0.799532 | 305.215 | 244.029 | 0.68803 | 1.03537 |
| Actual | 1 | not a forecast | 557 | 0.07695317803827988 | 1.79595 |

Candidate product 0.799531831 × 305.215241095; offense yield 0.688029041/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 694671, 'bucket': 'MLB', 'plate_appearances': 557, 'strike_outs': 115, 'unintentional_walks': 48, 'hit_by_pitch': 4, 'home_runs': 16, 'babip_hits': 110, 'doubles': 25, 'triples': 4, 'babip_opportunities': 371}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 750 |
| old_smooth | participation | refined | 18 |
| old_smooth | conditional_pa | broad | 161 |
| old_smooth | conditional_pa | refined | 2 |
| smooth_preseason | participation | broad | 35 |
| smooth_preseason | participation | refined | 0 |
| smooth_preseason | conditional_pa | broad | 33 |
| smooth_preseason | conditional_pa | refined | 0 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.846780; additive output 1.383371; linked output 0.799532.

Largest standardized terms are exact accounting, not causal effects:

- draft_rank: input 0.817615, training scale 0.156505, standardized input 4.515, contribution +1.041433.
- recent_draft_rank: input 0.817615, training scale 0.091302, standardized input 8.404, contribution +0.945204.
- scout_listed_0: input 1.000000, training scale 0.326483, standardized input 3.335, contribution +0.759272.
- age_upper_interaction: input -1.200000, training scale 0.278295, standardized input -3.960, contribution +0.674244.
- draft_upper_interaction: input 0.817615, training scale 0.105186, standardized input 7.447, contribution +0.521260.
- pooled_AA_HR: input 0.045455, training scale 0.005043, standardized input 3.319, contribution +0.511086.
- reorganized: input 1.000000, training scale 0.372129, standardized input 2.241, contribution +0.426008.
- role_minor_0: input 4.444444, training scale 0.396527, standardized input 1.514, contribution +0.411607.

Largest ranking contributions on this same fit: scout_listed_0 +0.759272, scout_rank_score_0 +0.269271, scout_rank_score_1 -0.054519, scout_listed_2 +0.046441. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.844690; additive output 0.994449; linked output 0.729966.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.091302, standardized input 8.404, contribution +1.236697.
- draft_rank: input 0.817615, training scale 0.156505, standardized input 4.515, contribution +1.082502.
- age_upper_interaction: input -1.200000, training scale 0.278295, standardized input -3.960, contribution +0.713686.
- pooled_AA_HR: input 0.045455, training scale 0.005043, standardized input 3.319, contribution +0.542820.
- reorganized: input 1.000000, training scale 0.372129, standardized input 2.241, contribution +0.493932.
- draft_upper_interaction: input 0.817615, training scale 0.105186, standardized input 7.447, contribution +0.491399.
- position_7: input 1.000000, training scale 0.321123, standardized input 2.751, contribution -0.429801.
- role_minor_0: input 4.444444, training scale 0.396527, standardized input 1.514, contribution +0.409858.

Largest ranking contributions on this same fit: scout_listed_2 -0.083587, scout_rank_score_2 -0.053203, scout_listed_0 +0.040873, scout_listed_1 +0.034941. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.524152. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 116.672808; additive output 305.215241; linked output 305.215241.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.101997, standardized input 7.253, contribution +45.556194.
- scout_rank_score_0: input 0.950000, training scale 0.392592, standardized input 2.384, contribution +41.759189.
- pooled_RK121_2B: input 0.070175, training scale 0.002395, standardized input 8.398, contribution -39.674601.
- draft_rank: input 0.817615, training scale 0.232366, standardized input 2.335, contribution +24.271027.
- pooled_AA_HR: input 0.045455, training scale 0.011094, standardized input 1.652, contribution +22.426223.
- draft_elapsed: input 0.000000, training scale 0.210462, standardized input -1.191, contribution +16.868933.
- draft_college: input 1.000000, training scale 0.281158, standardized input 3.249, contribution +16.734704.
- scout_listed_0: input 1.000000, training scale 0.498354, standardized input 1.827, contribution +11.104686.

Largest ranking contributions on this same fit: scout_rank_score_0 +41.759189, scout_listed_0 +11.104686, scout_rank_score_2 +2.464019, scout_rank_score_1 +1.915943. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 116.613726; additive output 293.808130; linked output 293.808130.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.817615, training scale 0.101997, standardized input 7.253, contribution +60.181779.
- pooled_RK121_2B: input 0.070175, training scale 0.002395, standardized input 8.398, contribution -42.132146.
- draft_rank: input 0.817615, training scale 0.232366, standardized input 2.335, contribution +24.831718.
- pooled_AA_HR: input 0.045455, training scale 0.011094, standardized input 1.652, contribution +24.733312.
- draft_elapsed: input 0.000000, training scale 0.210462, standardized input -1.191, contribution +16.831102.
- draft_college: input 1.000000, training scale 0.281158, standardized input 3.249, contribution +15.173853.
- log_minor_pa_1: input 0.000000, training scale 0.672767, standardized input -2.007, contribution +11.575256.
- pooled_AAA_HR: input 0.023810, training scale 0.007941, standardized input -0.636, contribution -11.232530.

Largest ranking contributions on this same fit: scout_rank_score_2 +4.300173, scout_rank_score_0 +3.672884, scout_rank_score_1 +1.825267, scout_list_available_1 +1.194228. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 244.059635. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.902989; prediction 0.688029. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.200000, contribution +0.674184.
- reorganized: scaled input 1.000000, contribution -0.191040.
- position_7: scaled input 1.000000, contribution +0.187333.
- draft_college: scaled input 1.000000, contribution +0.160559.
- pooled_AAA_BB: scaled input 0.311111, contribution +0.102261.
- age_squared: scaled input 1.440000, contribution +0.098968.
- pooled_AA_BB: scaled input 0.433766, contribution +0.089932.
- pooled_AA_BABIP: scaled input 0.257576, contribution +0.088533.

Langford supplies 200 PA across four levels, including ten HR, 34 K and 36 walks, and becomes rank six. His new smooth appearance estimate is 79.95% and conditional PA 305.22, giving 244.03 versus the fresher trees' 214.92 and 557 actual. Draft and upper-level age terms support arrival; the newer rank contributes about 41.76 conditional PA. But an old 14-PA rookie stint produces a -39.67 conditional term from stabilized doubles, which is not a persuasive baseball mechanism by itself. Refined current-rank draft-year support is zero in both heads. Crews gets 132 PA and the other three selected peers none, so a blanket full-season assignment would also create false positives. Fixed hitting .6880 is above the realized .0770; multiplying that rate by too little PA can mask part of the workload error. A partial improvement, not a solved elite college-arrival forecast.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dylan Crews | 49.67 | 125.48 | 132 | 0.402 | 0.025 |
| Chase DeLauter | 57.35 | 42.38 | 0 | 0.130 | 0.000 |
| Matt Shaw | 101.43 | 143.25 | 0 | 0.390 | 0.000 |
| Kyle Teel | 43.47 | 117.82 | 0 | 0.337 | 0.000 |

## Cody Bellinger 2016 to 2017

ID 641355; row 24967; fold 3; age input 20.0; Upper minors. Information date 2017-01-28. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.88 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.110193 | 139.597 | 15.383 | 0.08460 | 0.04963 |
| preseason | 0.399032 | 257.040 | 102.567 | 0.08460 | 0.33094 |
| old_smooth | 0.282332 | 120.935 | 34.144 | 0.08460 | 0.11017 |
| smooth_preseason | 0.714031 | 173.332 | 123.764 | 0.08460 | 0.39933 |
| Actual | 1 | not a forecast | 548 | 2.928010671333948 | 4.36513 |

Candidate product 0.714031325 × 173.331616659; offense yield 0.084595978/600 + 0.003085550.

Actual MLB counts: [{'season': 2017, 'player_id': 641355, 'bucket': 'MLB', 'plate_appearances': 548, 'strike_outs': 146, 'unintentional_walks': 51, 'hit_by_pitch': 1, 'home_runs': 39, 'babip_hits': 89, 'doubles': 26, 'triples': 4, 'babip_opportunities': 298}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 380 |
| old_smooth | participation | refined | 353 |
| old_smooth | conditional_pa | broad | 91 |
| old_smooth | conditional_pa | refined | 90 |
| smooth_preseason | participation | broad | 17 |
| smooth_preseason | participation | refined | 17 |
| smooth_preseason | conditional_pa | broad | 13 |
| smooth_preseason | conditional_pa | refined | 13 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.729733; additive output 0.915045; linked output 0.714031.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.880000, training scale 0.064469, standardized input 13.552, contribution +1.515320.
- scout_listed_0: input 1.000000, training scale 0.110857, standardized input 8.908, contribution +0.712815.
- age_upper_interaction: input -1.400000, training scale 0.281926, standardized input -4.615, contribution +0.695847.
- log_pool_AA: input 1.731656, training scale 0.596989, standardized input 2.471, contribution +0.632104.
- draft_upper_interaction: input 0.365828, training scale 0.105547, standardized input 3.139, contribution +0.462486.
- pooled_Aplus_HR: input 0.050448, training scale 0.006278, standardized input 3.610, contribution +0.306543.
- log_games_minor_1: input 0.824175, training scale 0.278044, standardized input 1.746, contribution +0.272129.
- log_games_minor_0: input 0.774727, training scale 0.228940, standardized input 1.489, contribution +0.256560.

Largest ranking contributions on this same fit: scout_rank_score_0 +1.515320, scout_listed_0 +0.712815, scout_rank_score_2 +0.011460, scout_listed_2 +0.009356. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.680739; additive output -0.932925; linked output 0.282332.

Largest standardized terms are exact accounting, not causal effects:

- age_upper_interaction: input -1.400000, training scale 0.281926, standardized input -4.615, contribution +0.831483.
- log_pool_AA: input 1.731656, training scale 0.596989, standardized input 2.471, contribution +0.594911.
- draft_upper_interaction: input 0.365828, training scale 0.105547, standardized input 3.139, contribution +0.456411.
- pooled_Aplus_HR: input 0.050448, training scale 0.006278, standardized input 3.610, contribution +0.361513.
- pooled_AA_HR: input 0.046018, training scale 0.005198, standardized input 3.374, contribution +0.324585.
- pooled_RK128_3B: input 0.017098, training scale 0.001756, standardized input 6.754, contribution +0.304752.
- position_3: input 1.000000, training scale 0.303407, standardized input 2.958, contribution -0.268318.
- log_games_minor_0: input 0.774727, training scale 0.228940, standardized input 1.489, contribution +0.260687.

Largest ranking contributions on this same fit: scout_listed_2 +0.027077, scout_rank_score_1 +0.009141, scout_rank_score_2 +0.006990, scout_list_available_2 -0.004806. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.208662. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 110.067315; additive output 173.331617; linked output 173.331617.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.880000, training scale 0.249130, standardized input 3.145, contribution +41.758960.
- pooled_RK128_HR: input 0.020017, training scale 0.002335, standardized input -4.205, contribution -36.897733.
- scout_listed_0: input 1.000000, training scale 0.369119, standardized input 2.268, contribution +29.146527.
- pooled_RK128_3B: input 0.017098, training scale 0.001667, standardized input 7.107, contribution -21.615914.
- age_squared: input 1.960000, training scale 0.620346, standardized input 1.872, contribution +17.750103.
- role_minor_2: input 4.475410, training scale 0.244786, standardized input 1.370, contribution +17.428233.
- pooled_AAA_HR: input 0.053571, training scale 0.007601, standardized input 3.410, contribution +15.034094.
- pooled_RK128_2B: input 0.055880, training scale 0.002261, standardized input 2.561, contribution +12.559155.

Largest ranking contributions on this same fit: scout_rank_score_0 +41.758960, scout_listed_0 +29.146527, scout_rank_score_1 -4.584648, scout_list_available_2 +1.219509. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 110.140686; additive output 120.934913; linked output 120.934913.

Largest standardized terms are exact accounting, not causal effects:

- pooled_RK128_HR: input 0.020017, training scale 0.002335, standardized input -4.205, contribution -36.215450.
- age_squared: input 1.960000, training scale 0.620346, standardized input 1.872, contribution +25.220776.
- pooled_AAA_HR: input 0.053571, training scale 0.007601, standardized input 3.410, contribution +20.361652.
- role_minor_2: input 4.475410, training scale 0.244786, standardized input 1.370, contribution +17.046054.
- log_pool_Aplus: input 1.677470, training scale 0.656297, standardized input 0.894, contribution -11.434237.
- log_pool_RK128: input 0.874635, training scale 0.211377, standardized input 3.917, contribution -11.308558.
- pooled_RK128_2B: input 0.055880, training scale 0.002261, standardized input 2.561, contribution +10.658376.
- pooled_RK128_3B: input 0.017098, training scale 0.001667, standardized input 7.107, contribution -10.488812.

Largest ranking contributions on this same fit: scout_rank_score_0 -6.446957, scout_list_available_2 +2.504047, scout_rank_score_2 +2.143596, scout_listed_0 -1.423362. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 91.617483. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.744379; prediction 0.084596. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.400000, contribution +0.661388.
- draft_class_unknown: scaled input 1.000000, contribution -0.205747.
- position_3: scaled input 1.000000, contribution +0.148310.
- age_squared: scaled input 1.960000, contribution +0.141688.
- draft_known: scaled input 1.000000, contribution +0.128847.
- pooled_AA_pa: scaled input 0.775000, contribution -0.107306.
- pooled_AAA_HR: scaled input 0.235714, contribution +0.059209.
- pooled_AA_BB: scaled input 0.350442, contribution +0.055924.

Bellinger has 465 AA PA with 23 HR in 2016, plus twelve AAA PA with three HR, after thirty HR in High A. The updated rank is thirteen. Smooth appearance increases to 71.40%, but conditional PA is only 173.33, yielding 123.76 versus fresher-tree 102.57 and 548 actual. The same new fit with old rankings gives 20.87% and 91.62 PA; current ranking is genuinely an important mechanical input. Current AA exposure and young upper-level age help, while two-year-old rookie HR and triples contribute -36.90 and -21.62 conditional PA. There are seventeen matching earlier people for participation and thirteen active, not hundreds of matched elite stars. Verdugo gets 25 PA, Crawford 87, O'Neill and Bauers none. Fixed hitting .0846 against 2.9280 actual leaves a separate talent miss. Higher arrival probability alone cannot close this delivered-value gap; neither these peers nor the case justifies forcing a full-season forecast.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alex Verdugo | 97.94 | 33.02 | 25 | 0.103 | -0.076 |
| Tyler O'Neill | 95.86 | 64.54 | 0 | 0.196 | 0.000 |
| J.P. Crawford | 383.05 | 309.86 | 87 | 0.704 | 0.191 |
| Jake Bauers | 67.53 | 89.17 | 0 | 0.279 | 0.000 |

## Pete Alonso 2018 to 2019

ID 624413; row 33263; fold 1; age input 23.0; Upper minors. Information date 2019-01-27. Selected: fixed before fit, false low.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.5 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.692850 | 183.403 | 127.071 | 0.28616 | 0.45199 |
| preseason | 0.803630 | 267.577 | 215.033 | 0.28616 | 0.76486 |
| old_smooth | 0.670824 | 206.525 | 138.542 | 0.28616 | 0.49279 |
| smooth_preseason | 0.844194 | 244.816 | 206.672 | 0.28616 | 0.73513 |
| Actual | 1 | not a forecast | 693 | 3.864559970969914 | 6.59803 |

Candidate product 0.844194141 × 244.815675957; offense yield 0.286158486/600 + 0.003080035.

Actual MLB counts: [{'season': 2019, 'player_id': 624413, 'bucket': 'MLB', 'plate_appearances': 693, 'strike_outs': 183, 'unintentional_walks': 66, 'hit_by_pitch': 21, 'home_runs': 53, 'babip_hits': 102, 'doubles': 30, 'triples': 2, 'babip_opportunities': 364}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 1374 |
| old_smooth | participation | refined | 1353 |
| old_smooth | conditional_pa | broad | 230 |
| old_smooth | conditional_pa | refined | 230 |
| smooth_preseason | participation | broad | 7 |
| smooth_preseason | participation | refined | 7 |
| smooth_preseason | conditional_pa | broad | 5 |
| smooth_preseason | conditional_pa | refined | 5 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.751555; additive output 1.689772; linked output 0.844194.

Largest standardized terms are exact accounting, not causal effects:

- log_pool_AAA: input 1.388791, training scale 0.337158, standardized input 3.871, contribution +1.168605.
- scout_listed_0: input 1.000000, training scale 0.110055, standardized input 8.975, contribution +0.658406.
- scout_rank_score_0: input 0.500000, training scale 0.066265, standardized input 7.449, contribution +0.606729.
- pooled_AAA_HR: input 0.059850, training scale 0.003097, standardized input 9.822, contribution +0.559073.
- log_pool_AA: input 1.412449, training scale 0.590714, standardized input 1.961, contribution +0.547793.
- pooled_AA_HR: input 0.047735, training scale 0.005171, standardized input 3.732, contribution +0.457182.
- draft_upper_interaction: input 0.452844, training scale 0.105786, standardized input 3.949, contribution +0.442532.
- age_upper_interaction: input -0.800000, training scale 0.280127, standardized input -2.495, contribution +0.372592.

Largest ranking contributions on this same fit: scout_listed_0 +0.658406, scout_rank_score_0 +0.606729, scout_list_available_2 +0.022317, scout_rank_score_2 +0.010956. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.729388; additive output 0.711916; linked output 0.670824.

Largest standardized terms are exact accounting, not causal effects:

- log_pool_AAA: input 1.388791, training scale 0.337158, standardized input 3.871, contribution +1.177206.
- pooled_AAA_HR: input 0.059850, training scale 0.003097, standardized input 9.822, contribution +0.635382.
- log_pool_AA: input 1.412449, training scale 0.590714, standardized input 1.961, contribution +0.544334.
- pooled_AA_HR: input 0.047735, training scale 0.005171, standardized input 3.732, contribution +0.524508.
- age_upper_interaction: input -0.800000, training scale 0.280127, standardized input -2.495, contribution +0.440400.
- position_3: input 1.000000, training scale 0.309567, standardized input 2.884, contribution -0.414147.
- draft_upper_interaction: input 0.452844, training scale 0.105786, standardized input 3.949, contribution +0.412791.
- log_games_minor_0: input 0.841567, training scale 0.228629, standardized input 1.801, contribution +0.357385.

Largest ranking contributions on this same fit: scout_list_available_1 +0.021096, scout_list_available_2 +0.020452, scout_rank_score_1 +0.009126, scout_listed_2 -0.007813. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.600746. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 109.776026; additive output 244.815676; linked output 244.815676.

Largest standardized terms are exact accounting, not causal effects:

- pooled_AAA_HR: input 0.059850, training scale 0.007787, standardized input 4.126, contribution +45.731029.
- scout_listed_0: input 1.000000, training scale 0.372948, standardized input 2.234, contribution +22.958331.
- scout_rank_score_0: input 0.500000, training scale 0.252073, standardized input 1.596, contribution +22.507664.
- pooled_AA_HR: input 0.047735, training scale 0.010947, standardized input 2.122, contribution +20.458555.
- pooled_Aminus_HR: input 0.034522, training scale 0.004637, standardized input 1.183, contribution +9.943271.
- log_pool_A: input 0.000000, training scale 0.666920, standardized input -0.973, contribution +9.585392.
- pooled_AAA_K: input 0.251870, training scale 0.031405, standardized input 1.068, contribution -9.346513.
- pooled_Aplus_3B: input 0.001327, training scale 0.004684, standardized input -1.257, contribution -8.591375.

Largest ranking contributions on this same fit: scout_listed_0 +22.958331, scout_rank_score_0 +22.507664, scout_rank_score_1 -3.327440, scout_list_available_2 +1.942622. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 109.810506; additive output 206.524898; linked output 206.524898.

Largest standardized terms are exact accounting, not causal effects:

- pooled_AAA_HR: input 0.059850, training scale 0.007787, standardized input 4.126, contribution +51.560719.
- pooled_AA_HR: input 0.047735, training scale 0.010947, standardized input 2.122, contribution +25.309242.
- pooled_Aminus_HR: input 0.034522, training scale 0.004637, standardized input 1.183, contribution +10.685938.
- pooled_Aplus_3B: input 0.001327, training scale 0.004684, standardized input -1.257, contribution -9.955306.
- pooled_AAA_K: input 0.251870, training scale 0.031405, standardized input 1.068, contribution -9.891672.
- log_pool_A: input 0.000000, training scale 0.666920, standardized input -0.973, contribution +9.020329.
- position_3: input 1.000000, training scale 0.279327, standardized input 3.275, contribution -7.408414.
- highest_AAA: input 1.000000, training scale 0.495592, standardized input 1.143, contribution +7.206429.

Largest ranking contributions on this same fit: scout_rank_score_0 -5.317813, scout_list_available_1 +1.811896, scout_list_available_2 +1.365892, scout_listed_1 -1.014956. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 189.275973. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.667726; prediction 0.286158. Largest terms on its deterministic input scale:

- age_centered: scaled input -0.800000, contribution +0.414811.
- position_3: scaled input 1.000000, contribution +0.174021.
- draft_known: scaled input 1.000000, contribution +0.155399.
- draft_class_unknown: scaled input 1.000000, contribution -0.139270.
- pooled_AAA_HR: scaled input 0.298504, contribution +0.122772.
- pooled_AA_BB: scaled input 0.407988, contribution +0.092229.
- pooled_AA_BABIP: scaled input 0.275017, contribution +0.071216.
- pooled_AA_pa: scaled input 0.517667, contribution -0.063956.

Alonso's 574 AA/AAA PA include 36 HR and 73 walks; current rank becomes 51. Smooth appearance is already 84.42%, versus trees 80.36%, so the remaining problem is not chiefly whether he arrives. Conditional PA is 244.82 versus trees 267.58, leaving 206.67 expected PA, slightly worse than trees 215.03 and far below 693 actual. AAA HR is a +45.73 conditional term, and current listed/rank terms add about 45.47. Earlier exact profile support is only seven participation people and five active. Solak and Mercado get meaningful MLB use, Brigman none and Neuse 61 PA. The fixed hitting projection .2862 is far short of 3.8646 actual; this historic 53-HR debut remains a joint workload and talent miss. A high debut chance is not a forecast of a regular job, and no reasonable audit should require the exact record rookie HR total to call the forecast sound.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nick Solak | 31.37 | 35.86 | 135 | 0.076 | 1.169 |
| Óscar Mercado | 81.36 | 86.53 | 482 | 0.156 | 1.897 |
| Bryson Brigman | 3.76 | 13.71 | 0 | 0.032 | 0.000 |
| Sheldon Neuse | 31.85 | 13.10 | 61 | 0.049 | -0.044 |

## Mickey Moniak 2016 to 2017

ID 666160; row 26836; fold 3; age input 18.0; Lower minors. Information date 2017-01-28. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.82 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2016 | RK124 | 194 | 1 | 35 | 11 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.006797 | 71.368 | 0.485 | 0.37128 | 0.00180 |
| preseason | 0.040447 | 157.123 | 6.355 | 0.37128 | 0.02354 |
| old_smooth | 0.015463 | 254.699 | 3.938 | 0.37128 | 0.01459 |
| smooth_preseason | 0.047912 | 263.278 | 12.614 | 0.37128 | 0.04673 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product 0.047911613 × 263.278027286; offense yield 0.371275556/600 + 0.003085550.

Actual MLB counts: []. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 1713 |
| old_smooth | participation | refined | 150 |
| old_smooth | conditional_pa | broad | 1 |
| old_smooth | conditional_pa | refined | 0 |
| smooth_preseason | participation | broad | 5 |
| smooth_preseason | participation | refined | 2 |
| smooth_preseason | conditional_pa | broad | 1 |
| smooth_preseason | conditional_pa | refined | 0 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.729733; additive output -2.989300; linked output 0.047912.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.820000, training scale 0.064469, standardized input 12.621, contribution +1.411257.
- recent_draft_rank: input 1.000000, training scale 0.093217, standardized input 10.145, contribution +0.958579.
- scout_listed_0: input 1.000000, training scale 0.110857, standardized input 8.908, contribution +0.712815.
- draft_rank: input 1.000000, training scale 0.155489, standardized input 5.701, contribution +0.472452.
- log_pool_RK124: input 1.078410, training scale 0.293209, standardized input 3.283, contribution -0.254250.
- position_8: input 1.000000, training scale 0.297369, standardized input 3.033, contribution +0.222199.
- pooled_RK124_3B: input 0.015306, training scale 0.002129, standardized input 4.697, contribution -0.212407.
- highest_complex: input 1.000000, training scale 0.403866, standardized input 1.968, contribution -0.207764.

Largest ranking contributions on this same fit: scout_rank_score_0 +1.411257, scout_listed_0 +0.712815, scout_rank_score_2 +0.011460, scout_listed_2 +0.009356. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.680739; additive output -4.153708; linked output 0.015463.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 1.000000, training scale 0.093217, standardized input 10.145, contribution +1.382286.
- draft_rank: input 1.000000, training scale 0.155489, standardized input 5.701, contribution +0.563279.
- draft_rank_low_exposure: input 0.340136, training scale 0.043373, standardized input 7.303, contribution +0.306386.
- position_8: input 1.000000, training scale 0.297369, standardized input 3.033, contribution +0.249401.
- log_pool_RK124: input 1.078410, training scale 0.293209, standardized input 3.283, contribution -0.241553.
- highest_complex: input 1.000000, training scale 0.403866, standardized input 1.968, contribution -0.222362.
- role_minor_0: input 4.178571, training scale 0.440374, standardized input 0.785, contribution +0.195956.
- pooled_RK124_BABIP: input 0.326446, training scale 0.009024, standardized input 2.891, contribution +0.195629.

Largest ranking contributions on this same fit: scout_listed_2 +0.027077, scout_rank_score_1 +0.009141, scout_rank_score_2 +0.006990, scout_list_available_2 -0.004806. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.005863. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 110.067315; additive output 263.278027; linked output 263.278027.

Largest standardized terms are exact accounting, not causal effects:

- draft_rank_low_exposure: input 0.340136, training scale 0.034518, standardized input 9.163, contribution +66.406840.
- pooled_RK124_HR: input 0.013605, training scale 0.002082, standardized input -7.769, contribution -40.229576.
- scout_rank_score_0: input 0.820000, training scale 0.249130, standardized input 2.904, contribution +38.561045.
- age_squared: input 3.240000, training scale 0.620346, standardized input 3.936, contribution +37.311636.
- pooled_RK124_K: input 0.197279, training scale 0.008404, standardized input -3.691, contribution +32.589542.
- log_pool_RK124: input 1.078410, training scale 0.104472, standardized input 10.078, contribution -31.441952.
- scout_listed_0: input 1.000000, training scale 0.369119, standardized input 2.268, contribution +29.146527.
- recent_draft_rank: input 1.000000, training scale 0.110499, standardized input 8.338, contribution +18.079111.

Largest ranking contributions on this same fit: scout_rank_score_0 +38.561045, scout_listed_0 +29.146527, scout_rank_score_1 -4.584648, scout_list_available_2 +1.219509. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 110.140686; additive output 254.699060; linked output 254.699060.

Largest standardized terms are exact accounting, not causal effects:

- draft_rank_low_exposure: input 0.340136, training scale 0.034518, standardized input 9.163, contribution +80.094282.
- age_squared: input 3.240000, training scale 0.620346, standardized input 3.936, contribution +53.015380.
- pooled_RK124_HR: input 0.013605, training scale 0.002082, standardized input -7.769, contribution -45.503459.
- recent_draft_rank: input 1.000000, training scale 0.110499, standardized input 8.338, contribution +37.094088.
- pooled_RK124_K: input 0.197279, training scale 0.008404, standardized input -3.691, contribution +29.029632.
- log_pool_RK124: input 1.078410, training scale 0.104472, standardized input 10.078, contribution -28.250228.
- log_pool_Aplus: input 0.000000, training scale 0.656297, standardized input -1.662, contribution +21.240013.
- log_minor_pa_1: input 0.000000, training scale 0.407304, standardized input -3.967, contribution +18.516284.

Largest ranking contributions on this same fit: scout_rank_score_0 -6.446957, scout_list_available_2 +2.504047, scout_rank_score_2 +2.143596, scout_listed_0 -1.423362. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 184.761809. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.744379; prediction 0.371276. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.800000, contribution +0.850356.
- age_squared: scaled input 3.240000, contribution +0.234220.
- draft_class_unknown: scaled input 1.000000, contribution -0.205747.
- draft_known: scaled input 1.000000, contribution +0.128847.
- position_8: scaled input 1.000000, contribution +0.073821.
- draft_rank: scaled input 1.000000, contribution +0.052008.
- absence_window_scaled: scaled input 1.000000, contribution -0.015355.
- pooled_RK124_K: scaled input -0.327211, contribution -0.010928.

Moniak is eighteen with 194 complex PA, one HR, 35 K and eleven walks, despite first-pick pedigree and a new rank of nineteen. Smooth appearance is 4.79% and conditional PA 263.28, yielding 12.61 expected PA versus trees 6.36 and zero actual. The current rank and draft terms raise arrival even though this is next-year MLB use, not eventual prospect value. Young ranked complex active-head support is zero after refinement. Conditional terms include a +66.41 low-exposure draft interaction and -40.23 rookie HR, showing extensive extrapolation and cancellation; this is not an empirically supported 263-PA MLB role. Rutherford, Lewis, Lowe and Kirilloff all have zero next-year PA. Low next-year participation is baseball-reasonable; failure to debut then does not mean Moniak or those peers lacked eventual talent. The extra expected PA is a modest false positive, not a reason to erase pedigree or all young-prospect upside.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Blake Rutherford | 6.94 | 1.68 | 0 | 0.006 | 0.000 |
| Kyle Lewis | 10.36 | 7.06 | 0 | 0.022 | 0.000 |
| Josh Lowe | 0.19 | 0.00 | 0 | 0.000 | 0.000 |
| Alex Kirilloff | 0.37 | 1.37 | 0 | 0.006 | 0.000 |

## Jake Burger 2017 to 2018

ID 669394; row 31137; fold 4; age input 21.0; Lower minors. Information date 2018-01-27. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 0 |
| scout_rank_score_0 | 0 | 0 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2017 | A | 200 | 4 | 28 | 13 |
| 2017 | RK121 | 17 | 1 | 2 | 1 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.013129 | 85.844 | 1.127 | -0.01534 | 0.00344 |
| preseason | 0.005400 | 71.567 | 0.386 | -0.01534 | 0.00118 |
| old_smooth | 0.016044 | 70.471 | 1.131 | -0.01534 | 0.00345 |
| smooth_preseason | 0.007105 | 47.125 | 0.335 | -0.01534 | 0.00102 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product 0.007104979 × 47.125457305; offense yield -0.015341796/600 + 0.003076176.

Actual MLB counts: []. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 4352 |
| old_smooth | participation | refined | 897 |
| old_smooth | conditional_pa | broad | 39 |
| old_smooth | conditional_pa | refined | 5 |
| smooth_preseason | participation | broad | 4320 |
| smooth_preseason | participation | refined | 887 |
| smooth_preseason | conditional_pa | broad | 27 |
| smooth_preseason | conditional_pa | refined | 1 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.794088; additive output -4.939829; linked output 0.007105.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.684525, training scale 0.091444, standardized input 6.906, contribution +0.655262.
- pooled_RK121_HBP: input 0.034188, training scale 0.002871, standardized input 8.282, contribution -0.276301.
- pooled_A_K: input 0.170000, training scale 0.024992, standardized input -2.173, contribution +0.246331.
- draft_rank_low_exposure: input 0.215938, training scale 0.040585, standardized input 4.758, contribution +0.199964.
- role_minor_0: input 4.213115, training scale 0.432167, standardized input 0.886, contribution +0.197919.
- draft_rank: input 0.684525, training scale 0.153347, standardized input 3.735, contribution +0.173385.
- position_5: input 1.000000, training scale 0.308304, standardized input 2.899, contribution -0.170093.
- position_2: input 0.000000, training scale 0.382583, standardized input -0.465, contribution -0.130433.

Largest ranking contributions on this same fit: scout_list_available_2 +0.030081, scout_rank_score_2 +0.020355, scout_listed_0 -0.010984, scout_rank_score_0 -0.009719. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.745728; additive output -4.116228; linked output 0.016044.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.684525, training scale 0.091444, standardized input 6.906, contribution +1.096644.
- draft_rank_low_exposure: input 0.215938, training scale 0.040585, standardized input 4.758, contribution +0.392992.
- pooled_A_K: input 0.170000, training scale 0.024992, standardized input -2.173, contribution +0.261718.
- pooled_RK121_HBP: input 0.034188, training scale 0.002871, standardized input 8.282, contribution -0.246374.
- draft_rank: input 0.684525, training scale 0.153347, standardized input 3.735, contribution +0.239274.
- role_minor_0: input 4.213115, training scale 0.432167, standardized input 0.886, contribution +0.207904.
- position_5: input 1.000000, training scale 0.308304, standardized input 2.899, contribution -0.149972.
- pooled_RK121_HR: input 0.034188, training scale 0.004197, standardized input 1.303, contribution +0.140589.

Largest ranking contributions on this same fit: scout_list_available_1 +0.025259, scout_rank_score_1 +0.017626, scout_listed_2 +0.016908, scout_rank_score_2 +0.007931. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.007105. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 111.640131; additive output 47.125457; linked output 47.125457.

Largest standardized terms are exact accounting, not causal effects:

- highest_A: input 1.000000, training scale 0.158392, standardized input 6.151, contribution -70.118567.
- recent_draft_rank: input 0.684525, training scale 0.115123, standardized input 5.262, contribution +25.074152.
- log_minor_pa_1: input 0.000000, training scale 0.431256, standardized input -3.692, contribution +23.474845.
- log_games_minor_1: input 0.000000, training scale 0.204629, standardized input -3.339, contribution +16.380407.
- pooled_RK121_BABIP: input 0.281818, training scale 0.005740, standardized input -3.328, contribution -16.062338.
- draft_elapsed: input 0.000000, training scale 0.198423, standardized input -1.156, contribution +15.962578.
- log_pool_Aplus: input 0.000000, training scale 0.660480, standardized input -1.683, contribution +15.029020.
- age_upper_interaction: input -0.000000, training scale 0.458291, standardized input 1.388, contribution -11.139803.

Largest ranking contributions on this same fit: scout_rank_score_0 -4.916818, scout_rank_score_1 -4.813585, scout_listed_0 -2.595718, scout_list_available_2 +1.357566. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 111.646142; additive output 70.471277; linked output 70.471277.

Largest standardized terms are exact accounting, not causal effects:

- highest_A: input 1.000000, training scale 0.158392, standardized input 6.151, contribution -68.648116.
- recent_draft_rank: input 0.684525, training scale 0.115123, standardized input 5.262, contribution +35.272469.
- log_minor_pa_1: input 0.000000, training scale 0.431256, standardized input -3.692, contribution +23.986554.
- pooled_RK121_BABIP: input 0.281818, training scale 0.005740, standardized input -3.328, contribution -16.944765.
- log_pool_Aplus: input 0.000000, training scale 0.660480, standardized input -1.683, contribution +16.735356.
- draft_rank_low_exposure: input 0.215938, training scale 0.038323, standardized input 5.016, contribution +15.782031.
- draft_elapsed: input 0.000000, training scale 0.198423, standardized input -1.156, contribution +15.615625.
- log_games_minor_1: input 0.000000, training scale 0.204629, standardized input -3.339, contribution +15.498740.

Largest ranking contributions on this same fit: scout_rank_score_0 -6.147046, scout_listed_2 +1.807993, scout_list_available_2 -1.745457, scout_list_available_1 +1.594277. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 47.125457. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.728554; prediction -0.015342. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.200000, contribution +0.552735.
- draft_class_unknown: scaled input 1.000000, contribution -0.204122.
- position_5: scaled input 1.000000, contribution +0.144641.
- draft_known: scaled input 1.000000, contribution +0.110476.
- pooled_A_K: scaled input -0.600000, contribution +0.065825.
- draft_rank: scaled input 0.684525, contribution +0.052682.
- age_squared: scaled input 1.440000, contribution +0.034913.
- absence_window_scaled: scaled input 1.000000, contribution -0.033994.

This is Jake Burger, not Maitan. The original numeric review list used Burger's ID under the intended Maitan name; the amendment retains Burger and appends the correct Maitan case without changing any forecast. Burger's current 217 PA are mostly A, with five HR and thirty K, at age 21. None of his rank inputs change, and the same new fit with old ranks gives identical outputs. His PA falls from old smooth 1.13 to new smooth .335, close to fresher trees .386, with zero actual. The shift is shared refitting, not evidence that a personal ranking disappeared. Highest-A contributes -70.12 conditional PA; only one current refined active analogue exists. Haseley, Pavin Smith, Warmoth and Kendall also do not debut next year. This reasonable low immediate-use forecast is not a diagnosis of Burger's later injury history or eventual MLB value, neither of which the experiment predicts.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Adam Haseley | 2.37 | 4.03 | 0 | 0.011 | 0.000 |
| Pavin Smith | 1.51 | 2.17 | 0 | 0.007 | 0.000 |
| Logan Warmoth | 1.35 | 1.29 | 0 | 0.003 | 0.000 |
| Jeren Kendall | 0.60 | 0.96 | 0 | 0.003 | 0.000 |

## Ethan Salas 2024 to 2025

ID 806956; row 57694; fold 3; age input 18.0; Lower minors. Information date 2025-01-24. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 1 | 1 |
| scout_rank_score_0 | 0.93 | 0.68 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 1 |
| scout_rank_score_1 | 0 | 0.93 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.025632 | 281.842 | 7.224 | -0.51171 | 0.01640 |
| preseason | 0.022453 | 262.436 | 5.892 | -0.51171 | 0.01338 |
| old_smooth | 0.011711 | 173.074 | 2.027 | -0.51171 | 0.00460 |
| smooth_preseason | 0.014591 | 161.805 | 2.361 | -0.51171 | 0.00536 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product 0.014591424 × 161.804593073; offense yield -0.511710571/600 + 0.003122875.

Actual MLB counts: []. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 0 |
| old_smooth | participation | refined | 0 |
| old_smooth | conditional_pa | broad | 0 |
| old_smooth | conditional_pa | refined | 0 |
| smooth_preseason | participation | broad | 21 |
| smooth_preseason | participation | refined | 8 |
| smooth_preseason | conditional_pa | broad | 1 |
| smooth_preseason | conditional_pa | refined | 1 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.918595; additive output -4.212622; linked output 0.014591.

Largest standardized terms are exact accounting, not causal effects:

- scout_listed_0: input 1.000000, training scale 0.317426, standardized input 3.404, contribution +0.589972.
- position_2: input 1.000000, training scale 0.379461, standardized input 2.176, contribution +0.560226.
- scout_rank_score_1: input 0.930000, training scale 0.381596, standardized input 2.874, contribution -0.377592.
- highest_Aplus: input 1.000000, training scale 0.319676, standardized input 2.767, contribution +0.330268.
- role_minor_0: input 4.206612, training scale 0.395865, standardized input 0.906, contribution +0.295533.
- reorganized: input 1.000000, training scale 0.421196, standardized input 1.827, contribution +0.228688.
- pooled_Aplus_HR: input 0.011694, training scale 0.006114, standardized input -2.681, contribution -0.209344.
- log_games_minor_0: input 0.746688, training scale 0.248074, standardized input 1.490, contribution +0.200293.

Largest ranking contributions on this same fit: scout_listed_0 +0.589972, scout_rank_score_1 -0.377592, scout_rank_score_0 +0.162507, scout_listed_1 -0.145726. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.918149; additive output -4.435478; linked output 0.011711.

Largest standardized terms are exact accounting, not causal effects:

- position_2: input 1.000000, training scale 0.379461, standardized input 2.176, contribution +0.564045.
- highest_Aplus: input 1.000000, training scale 0.319676, standardized input 2.767, contribution +0.363159.
- role_minor_0: input 4.206612, training scale 0.395865, standardized input 0.906, contribution +0.295532.
- reorganized: input 1.000000, training scale 0.421196, standardized input 1.827, contribution +0.272989.
- pooled_Aplus_HR: input 0.011694, training scale 0.006114, standardized input -2.681, contribution -0.234924.
- log_games_minor_0: input 0.746688, training scale 0.248074, standardized input 1.490, contribution +0.205552.
- pooled_A_HR: input 0.036957, training scale 0.006347, standardized input 1.533, contribution +0.201852.
- scout_rank_score_0: input 0.930000, training scale 0.381596, standardized input 2.874, contribution -0.176365.

Largest ranking contributions on this same fit: scout_rank_score_0 -0.176365, scout_listed_0 +0.084630, scout_listed_2 +0.018106, scout_rank_score_2 +0.016669. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.023797. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 115.849519; additive output 161.804593; linked output 161.804593.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.680000, training scale 0.376135, standardized input 1.753, contribution +45.408015.
- scout_rank_score_1: input 0.930000, training scale 0.456480, standardized input 2.284, contribution +30.911518.
- age_squared: input 3.240000, training scale 0.614838, standardized input 4.061, contribution +28.467998.
- age_centered: input -1.800000, training scale 0.421415, standardized input -2.487, contribution +18.511128.
- draft_elapsed: input 0.000000, training scale 0.214655, standardized input -1.198, contribution +13.681696.
- reorganized: input 1.000000, training scale 0.456541, standardized input 1.542, contribution -12.137944.
- log_pool_AA: input 0.234281, training scale 0.661129, standardized input -1.676, contribution -11.208103.
- log_pool_Aplus: input 1.789423, training scale 0.653769, standardized input 1.273, contribution -10.807014.

Largest ranking contributions on this same fit: scout_rank_score_0 +45.408015, scout_rank_score_1 +30.911518, scout_listed_0 +7.689635, scout_listed_1 -7.311764. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 115.862740; additive output 173.073507; linked output 173.073507.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.930000, training scale 0.456480, standardized input 2.284, contribution +53.966665.
- age_squared: input 3.240000, training scale 0.614838, standardized input 4.061, contribution +49.873292.
- age_centered: input -1.800000, training scale 0.421415, standardized input -2.487, contribution +20.395155.
- draft_elapsed: input 0.000000, training scale 0.214655, standardized input -1.198, contribution +13.527207.
- log_pool_Aplus: input 1.789423, training scale 0.653769, standardized input 1.273, contribution -12.312516.
- log_pool_AA: input 0.234281, training scale 0.661129, standardized input -1.676, contribution -11.733021.
- pooled_AA_BABIP: input 0.293103, training scale 0.022878, standardized input -0.770, contribution -10.371626.
- recent_draft_rank: input 0.000000, training scale 0.098248, standardized input -0.788, contribution -10.178188.

Largest ranking contributions on this same fit: scout_rank_score_0 +53.966665, scout_listed_0 +7.499843, scout_listed_1 -3.087796, scout_rank_score_2 +2.766944. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 158.390070. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.921844; prediction -0.511711. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.800000, contribution +0.973195.
- reorganized: scaled input 1.000000, contribution -0.265570.
- position_2: scaled input 1.000000, contribution -0.179442.
- age_squared: scaled input 3.240000, contribution +0.175883.
- pooled_Aplus_pa: scaled input 0.831000, contribution -0.118656.
- pooled_Aplus_BABIP: scaled input -0.331808, contribution -0.083042.
- draft_class_unknown: scaled input 1.000000, contribution -0.072176.
- Aplus_0_pa: scaled input 0.781667, contribution -0.042597.

Salas has 469 High A PA with four HR, 98 K and 47 walks at age eighteen, after a brief earlier AA stint. His rank score falls .93 to .68 while the older rank moves to lag one. Smooth appearance 1.46% times 161.80 conditional PA gives 2.36 expected PA versus trees 5.89 and zero actual. On the same fit with old ranks, chance is 2.38%, illustrating the fresher source's immediate-readiness effect; shared refitting means this is not the full arm comparison. The new active profile has only one distinct earlier person. The fixed rate -.5117 includes weak recent production and catcher position, while age adds favorable potential. De Paula, Montes, Jaison Chourio and De Vries all have zero next-year MLB PA too. Low immediate opportunity is sensible. This one-year score cannot reject their upside, certify career grades or answer trade value; it must not be used to call all these young prospects failures.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Josue De Paula | 3.33 | 3.00 | 0 | 0.010 | 0.000 |
| Lazaro Montes | 5.27 | 0.02 | 0 | 0.000 | 0.000 |
| Jaison Chourio | 0.86 | 0.91 | 0 | 0.003 | 0.000 |
| Leo De Vries | 5.03 | 1.42 | 0 | 0.004 | 0.000 |

## Julio Rodríguez 2021 to 2022

ID 677594; row 44122; fold 1; age input 20.0; Upper minors. Information date 2022-03-18. Selected: fixed before fit.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 1 | 1 |
| scout_rank_score_0 | 0.96 | 0.98 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 1 | 1 |
| scout_rank_score_1 | 0.83 | 0.96 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 1 |
| scout_rank_score_2 | 0 | 0.83 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2019 | A | 295 | 10 | 66 | 19 |
| 2019 | Aplus | 72 | 2 | 10 | 5 |
| 2021 | AA | 206 | 7 | 37 | 28 |
| 2021 | Aplus | 134 | 6 | 29 | 14 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.802416 | 279.241 | 224.067 | 0.75408 | 0.98377 |
| preseason | 0.805070 | 315.633 | 254.107 | 0.75408 | 1.11566 |
| old_smooth | 0.747709 | 284.437 | 212.676 | 0.75408 | 0.93376 |
| smooth_preseason | 0.759085 | 286.565 | 217.527 | 0.75408 | 0.95506 |
| Actual | 1 | not a forecast | 560 | 2.338055577200592 | 3.93706 |

Candidate product 0.759085264 × 286.565233745; offense yield 0.754077358/600 + 0.003133713.

Actual MLB counts: [{'season': 2022, 'player_id': 677594, 'bucket': 'MLB', 'plate_appearances': 560, 'strike_outs': 145, 'unintentional_walks': 36, 'hit_by_pitch': 8, 'home_runs': 28, 'babip_hits': 117, 'doubles': 25, 'triples': 3, 'babip_opportunities': 339}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 17 |
| old_smooth | participation | refined | 17 |
| old_smooth | conditional_pa | broad | 15 |
| old_smooth | conditional_pa | refined | 15 |
| smooth_preseason | participation | broad | 29 |
| smooth_preseason | participation | refined | 29 |
| smooth_preseason | conditional_pa | broad | 25 |
| smooth_preseason | conditional_pa | refined | 25 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.750894; additive output 1.147671; linked output 0.759085.

Largest standardized terms are exact accounting, not causal effects:

- on_40man: input 1.000000, training scale 0.138227, standardized input 7.093, contribution +2.235740.
- age_upper_interaction: input -1.400000, training scale 0.267242, standardized input -4.899, contribution +0.824683.
- pooled_AA_BABIP: input 0.373913, training scale 0.010158, standardized input 7.239, contribution +0.599974.
- scout_listed_0: input 1.000000, training scale 0.349681, standardized input 3.176, contribution +0.520273.
- log_pool_AA: input 1.118415, training scale 0.575443, standardized input 1.520, contribution +0.515515.
- pooled_Aplus_BABIP: input 0.368569, training scale 0.013034, standardized input 5.101, contribution +0.437213.
- role_minor_0: input 4.523810, training scale 0.393341, standardized input 1.694, contribution +0.423899.
- scout_rank_score_1: input 0.960000, training scale 0.332963, standardized input 3.241, contribution -0.351474.

Largest ranking contributions on this same fit: scout_listed_0 +0.520273, scout_rank_score_1 -0.351474, scout_listed_2 +0.132204, scout_rank_score_2 +0.129109. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.754682; additive output 1.086432; linked output 0.747709.

Largest standardized terms are exact accounting, not causal effects:

- on_40man: input 1.000000, training scale 0.138227, standardized input 7.093, contribution +2.219109.
- age_upper_interaction: input -1.400000, training scale 0.267242, standardized input -4.899, contribution +0.869247.
- pooled_AA_BABIP: input 0.373913, training scale 0.010158, standardized input 7.239, contribution +0.623564.
- log_pool_AA: input 1.118415, training scale 0.575443, standardized input 1.520, contribution +0.514279.
- pooled_Aplus_BABIP: input 0.368569, training scale 0.013034, standardized input 5.101, contribution +0.467232.
- role_minor_0: input 4.523810, training scale 0.393341, standardized input 1.694, contribution +0.424786.
- pooled_AA_K: input 0.196078, training scale 0.020087, standardized input -1.517, contribution +0.281736.
- highest_AA: input 1.000000, training scale 0.301243, standardized input 2.985, contribution +0.272583.

Largest ranking contributions on this same fit: scout_listed_0 +0.188622, scout_rank_score_0 -0.147944, scout_listed_1 +0.105464, scout_rank_score_1 +0.102073. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.721924. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 111.836042; additive output 286.565234; linked output 286.565234.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.980000, training scale 0.411475, standardized input 2.404, contribution +31.725783.
- pooled_AA_BABIP: input 0.373913, training scale 0.022929, standardized input 2.752, contribution +29.187117.
- age_squared: input 1.960000, training scale 0.614606, standardized input 1.986, contribution +28.118945.
- log_minor_pa_1: input 0.000000, training scale 0.426470, standardized input -3.719, contribution +18.690465.
- scout_rank_score_1: input 0.960000, training scale 0.378471, standardized input 2.635, contribution +18.135362.
- scout_listed_0: input 1.000000, training scale 0.499433, standardized input 1.899, contribution +17.927508.
- scout_rank_score_2: input 0.830000, training scale 0.332625, standardized input 2.696, contribution +16.100976.
- pooled_Aplus_3B: input 0.015512, training scale 0.004500, standardized input 1.882, contribution +14.986454.

Largest ranking contributions on this same fit: scout_rank_score_0 +31.725783, scout_rank_score_1 +18.135362, scout_listed_0 +17.927508, scout_rank_score_2 +16.100976. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 111.858417; additive output 284.436851; linked output 284.436851.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.960000, training scale 0.378471, standardized input 2.635, contribution +36.330066.
- age_squared: input 1.960000, training scale 0.614606, standardized input 1.986, contribution +34.279495.
- pooled_AA_BABIP: input 0.373913, training scale 0.022929, standardized input 2.752, contribution +31.942467.
- log_minor_pa_1: input 0.000000, training scale 0.426470, standardized input -3.719, contribution +19.938238.
- pooled_Aplus_3B: input 0.015512, training scale 0.004500, standardized input 1.882, contribution +15.899979.
- scout_rank_score_1: input 0.830000, training scale 0.332625, standardized input 2.696, contribution +14.886446.
- age_upper_interaction: input -1.400000, training scale 0.462274, standardized input -1.779, contribution +14.831709.
- draft_elapsed: input 0.000000, training scale 0.206790, standardized input -1.189, contribution +14.207156.

Largest ranking contributions on this same fit: scout_rank_score_0 +36.330066, scout_rank_score_1 +14.886446, scout_listed_1 -6.194269, scout_list_available_2 +2.316143. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 273.865018. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.743643; prediction 0.754077. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.400000, contribution +0.760705.
- pooled_AA_BABIP: scaled input 0.739130, contribution +0.271786.
- age_squared: scaled input 1.960000, contribution +0.161285.
- pooled_Aplus_BABIP: scaled input 0.685688, contribution +0.161192.
- position_9: scaled input 1.000000, contribution +0.138607.
- pooled_AA_BB: scaled input 0.376471, contribution +0.088127.
- draft_class_unknown: scaled input 1.000000, contribution -0.080634.
- A_2_pa: scaled input 0.491667, contribution -0.052160.

Julio has 340 High A/AA PA, thirteen HR and 42 walks at age twenty; the fresh list is rank three, released March 18, 2022, not at a December cutoff. Roster and young upper-level terms already support arrival. New smooth chance 75.91% and conditional PA 286.57 give 217.53 versus fresher trees 254.11 and 560 actual. Old smooth was 212.68, so the fresher source helps that model only a little while the model choice harms this case. Broad refined counts of 29 participation and 25 active people do not include a new-draftee support gap; this is a materially better-supported profile than Kurtz. Valera and Mauricio do not play; Moreno gets 73 and Peraza 57 PA. Fixed hitting .7541 is below actual 2.3381, but assigning every ranked peer Julio's workload would be wrong. The cohort's 62 expected debuts versus 158 actual shows a repeated post-COVID allocation shortfall that this model does not fix, despite better pooled RMSE.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| George Valera | 58.47 | 24.75 | 0 | 0.081 | 0.000 |
| Gabriel Moreno | 151.42 | 159.03 | 73 | 0.382 | 0.301 |
| Ronny Mauricio | 59.62 | 41.14 | 0 | 0.080 | 0.000 |
| Oswald Peraza | 178.79 | 164.68 | 57 | 0.474 | 0.450 |

## Ronald Acuña Jr. 2017 to 2018

ID 660670; row 30192; fold 3; age input 19.0; Upper minors. Information date 2018-01-27. Selected: largest offense gain.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 1 |
| scout_rank_score_0 | 0 | 0.99 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2015 | RK120 | 237 | 4 | 42 | 28 |
| 2016 | A | 171 | 4 | 28 | 18 |
| 2016 | RK124 | 8 | 0 | 1 | 1 |
| 2017 | AA | 243 | 9 | 56 | 18 |
| 2017 | AAA | 243 | 9 | 48 | 17 |
| 2017 | Aplus | 126 | 3 | 40 | 8 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.199282 | 139.357 | 27.771 | 0.16375 | 0.09301 |
| preseason | 0.482238 | 210.548 | 101.534 | 0.16375 | 0.34005 |
| old_smooth | 0.530952 | 277.594 | 147.389 | 0.16375 | 0.49362 |
| smooth_preseason | 0.834219 | 329.054 | 274.503 | 0.16375 | 0.91933 |
| Actual | 1 | not a forecast | 487 | 3.2605434261248205 | 4.14457 |

Candidate product 0.834218749 × 329.053921624; offense yield 0.163746918/600 + 0.003076176.

Actual MLB counts: [{'season': 2018, 'player_id': 660670, 'bucket': 'MLB', 'plate_appearances': 487, 'strike_outs': 123, 'unintentional_walks': 43, 'hit_by_pitch': 6, 'home_runs': 26, 'babip_hits': 101, 'doubles': 26, 'triples': 4, 'babip_opportunities': 287}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 466 |
| old_smooth | participation | refined | 437 |
| old_smooth | conditional_pa | broad | 105 |
| old_smooth | conditional_pa | refined | 104 |
| smooth_preseason | participation | broad | 19 |
| smooth_preseason | participation | refined | 19 |
| smooth_preseason | conditional_pa | broad | 17 |
| smooth_preseason | conditional_pa | refined | 17 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.802727; additive output 1.615827; linked output 0.834219.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.990000, training scale 0.064723, standardized input 15.199, contribution +1.110237.
- log_pool_AAA: input 1.232560, training scale 0.340737, standardized input 3.364, contribution +0.920408.
- scout_listed_0: input 1.000000, training scale 0.110059, standardized input 8.975, contribution +0.903056.
- age_upper_interaction: input -1.600000, training scale 0.282540, standardized input -5.307, contribution +0.829211.
- pooled_AAA_BABIP: input 0.364662, training scale 0.006563, standardized input 9.831, contribution +0.469320.
- log_pool_AA: input 1.232560, training scale 0.596021, standardized input 1.637, contribution +0.429016.
- pooled_AA_BABIP: input 0.359073, training scale 0.010157, standardized input 5.780, contribution +0.391409.
- log_games_minor_0: input 0.871293, training scale 0.228645, standardized input 1.918, contribution +0.321521.

Largest ranking contributions on this same fit: scout_rank_score_0 +1.110237, scout_listed_0 +0.903056, scout_list_available_2 +0.018473, scout_rank_score_2 +0.011176. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.765983; additive output 0.123967; linked output 0.530952.

Largest standardized terms are exact accounting, not causal effects:

- age_upper_interaction: input -1.600000, training scale 0.282540, standardized input -5.307, contribution +0.968273.
- log_pool_AAA: input 1.232560, training scale 0.340737, standardized input 3.364, contribution +0.937126.
- pooled_AAA_BABIP: input 0.364662, training scale 0.006563, standardized input 9.831, contribution +0.519331.
- pooled_AA_BABIP: input 0.359073, training scale 0.010157, standardized input 5.780, contribution +0.432419.
- log_pool_AA: input 1.232560, training scale 0.596021, standardized input 1.637, contribution +0.410870.
- position_8: input 1.000000, training scale 0.298611, standardized input 3.017, contribution +0.329354.
- log_games_minor_0: input 0.871293, training scale 0.228645, standardized input 1.918, contribution +0.325112.
- role_minor_0: input 4.375839, training scale 0.434139, standardized input 1.249, contribution +0.324721.

Largest ranking contributions on this same fit: scout_listed_2 +0.018473, scout_list_available_1 +0.012992, scout_listed_1 -0.010777, scout_rank_score_2 +0.010323. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.397530. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 108.176045; additive output 329.053922; linked output 329.053922.

Largest standardized terms are exact accounting, not causal effects:

- pooled_RK120_3B: input 0.011974, training scale 0.001123, standardized input 6.111, contribution -64.999547.
- pooled_RK120_HBP: input 0.023947, training scale 0.002034, standardized input 6.742, contribution +60.986916.
- scout_rank_score_0: input 0.990000, training scale 0.247732, standardized input 3.610, contribution +49.937872.
- pooled_RK120_BB: input 0.102395, training scale 0.003714, standardized input 5.973, contribution -45.668044.
- pooled_Aplus_3B: input 0.024336, training scale 0.004534, standardized input 3.773, contribution +24.668001.
- age_squared: input 2.560000, training scale 0.616130, standardized input 2.877, contribution +22.759666.
- scout_listed_0: input 1.000000, training scale 0.371074, standardized input 2.251, contribution +22.567387.
- pooled_RK120_2B: input 0.055326, training scale 0.002405, standardized input 2.169, contribution +19.272904.

Largest ranking contributions on this same fit: scout_rank_score_0 +49.937872, scout_listed_0 +22.567387, scout_rank_score_1 -3.157077, scout_list_available_2 +1.087294. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 108.257836; additive output 277.593970; linked output 277.593970.

Largest standardized terms are exact accounting, not causal effects:

- pooled_RK120_3B: input 0.011974, training scale 0.001123, standardized input 6.111, contribution -60.594884.
- pooled_RK120_HBP: input 0.023947, training scale 0.002034, standardized input 6.742, contribution +58.165785.
- pooled_RK120_BB: input 0.102395, training scale 0.003714, standardized input 5.973, contribution -51.760664.
- age_squared: input 2.560000, training scale 0.616130, standardized input 2.877, contribution +34.921195.
- pooled_Aplus_3B: input 0.024336, training scale 0.004534, standardized input 3.773, contribution +26.137555.
- pooled_RK120_2B: input 0.055326, training scale 0.002405, standardized input 2.169, contribution +18.967254.
- pooled_AA_BABIP: input 0.359073, training scale 0.022913, standardized input 2.119, contribution +18.699488.
- pooled_RK120_BABIP: input 0.310881, training scale 0.007960, standardized input 1.206, contribution +13.371288.

Largest ranking contributions on this same fit: scout_rank_score_0 -5.072953, scout_listed_2 +1.768350, scout_listed_0 -1.701037, scout_rank_score_2 +1.202543. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 246.750721. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.845705; prediction 0.163747. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.600000, contribution +0.752096.
- draft_class_unknown: scaled input 1.000000, contribution -0.173582.
- pooled_AA_BABIP: scaled input 0.590734, contribution +0.148095.
- pooled_AAA_BABIP: scaled input 0.646617, contribution +0.141909.
- pooled_Aplus_BABIP: scaled input 0.468208, contribution +0.128875.
- age_squared: scaled input 2.560000, contribution +0.096289.
- pooled_Aplus_K: scaled input 0.487611, contribution -0.078805.
- pooled_AA_pa: scaled input 0.405000, contribution -0.039746.

Acuña is the largest offense gain selected by the locked error rule. His 612 PA span High A, AA and AAA, with 21 HR, 144 K and 43 walks; the new list identifies rank two. New smooth .8342 appearance times 329.05 conditional PA gives 274.50 versus fresher trees 101.53, old smooth 147.39 and actual 487. With old ranks on the new fit, chance is .3975 and conditional PA 246.75. Current ranking clearly changes the fitted forecast, but two-year-old rookie triples and HBP also contribute about -65 and +61 conditional PA: opposing rare-level terms remain. Support is nineteen participation and seventeen active people. Tatis and Jiménez do not appear, Urías gets 53 and Adames 323 PA. Fixed hitting .1637 versus 3.2605 realized still misses most of the breakout quality. This is a useful gain, not independent proof of the model or permission to tune around future stars.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fernando Tatis Jr. | 16.06 | 14.15 | 0 | 0.039 | 0.000 |
| Luis Urías | 116.10 | 91.45 | 53 | 0.194 | -0.063 |
| Willy Adames | 373.10 | 307.21 | 323 | 0.780 | 1.094 |
| Eloy Jiménez | 264.45 | 215.92 | 0 | 0.769 | 0.000 |

## Jackson Holliday 2023 to 2024

ID 702616; row 53595; fold 3; age input 19.0; Upper minors. Information date 2024-01-26. Selected: largest offense harm, false high.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 1 | 1 |
| scout_rank_score_0 | 0.89 | 1 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 1 |
| scout_rank_score_1 | 0 | 0.89 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | -1 | 0 |
| scout_rank_score_2 | -1 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | A | 57 | 0 | 10 | 14 |
| 2022 | RK124 | 33 | 1 | 2 | 10 |
| 2023 | A | 67 | 2 | 13 | 14 |
| 2023 | AA | 164 | 3 | 34 | 19 |
| 2023 | AAA | 91 | 2 | 17 | 16 |
| 2023 | Aplus | 259 | 5 | 54 | 50 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.825719 | 439.766 | 363.123 | 0.62078 | 1.49995 |
| preseason | 0.886812 | 396.012 | 351.188 | 0.62078 | 1.45065 |
| old_smooth | 0.936875 | 485.440 | 454.796 | 0.62078 | 1.87863 |
| smooth_preseason | 0.931594 | 452.129 | 421.200 | 0.62078 | 1.73985 |
| Actual | 1 | not a forecast | 208 | -3.309793244638865 | -0.50341 |

Candidate product 0.931594299 × 452.128610971; offense yield 0.620777003/600 + 0.003096076.

Actual MLB counts: [{'season': 2024, 'player_id': 702616, 'bucket': 'MLB', 'plate_appearances': 208, 'strike_outs': 69, 'unintentional_walks': 15, 'hit_by_pitch': 2, 'home_runs': 5, 'babip_hits': 31, 'doubles': 4, 'triples': 2, 'babip_opportunities': 117}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 22 |
| old_smooth | participation | refined | 22 |
| old_smooth | conditional_pa | broad | 19 |
| old_smooth | conditional_pa | refined | 19 |
| smooth_preseason | participation | broad | 40 |
| smooth_preseason | participation | refined | 40 |
| smooth_preseason | conditional_pa | broad | 35 |
| smooth_preseason | conditional_pa | refined | 35 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.897619; additive output 2.611441; linked output 0.931594.

Largest standardized terms are exact accounting, not causal effects:

- draft_rank: input 1.000000, training scale 0.158281, standardized input 5.604, contribution +1.343558.
- age_upper_interaction: input -1.600000, training scale 0.280233, standardized input -5.354, contribution +1.084958.
- draft_upper_interaction: input 1.000000, training scale 0.106674, standardized input 9.046, contribution +0.825507.
- role_minor_0: input 4.600000, training scale 0.397685, standardized input 1.893, contribution +0.614739.
- scout_listed_0: input 1.000000, training scale 0.327221, standardized input 3.325, contribution +0.523126.
- pooled_AA_BABIP: input 0.364078, training scale 0.010255, standardized input 6.202, contribution +0.512452.
- log_pool_AAA: input 0.647103, training scale 0.334125, standardized input 1.681, contribution +0.498628.
- reorganized: input 1.000000, training scale 0.373272, standardized input 2.231, contribution +0.413114.

Largest ranking contributions on this same fit: scout_listed_0 +0.523126, scout_rank_score_1 -0.337654, scout_rank_score_0 +0.228222, scout_listed_1 -0.181271. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.898865; additive output 2.697439; linked output 0.936875.

Largest standardized terms are exact accounting, not causal effects:

- draft_rank: input 1.000000, training scale 0.158281, standardized input 5.604, contribution +1.393923.
- age_upper_interaction: input -1.600000, training scale 0.280233, standardized input -5.354, contribution +1.134955.
- draft_upper_interaction: input 1.000000, training scale 0.106674, standardized input 9.046, contribution +0.784465.
- role_minor_0: input 4.600000, training scale 0.397685, standardized input 1.893, contribution +0.614907.
- pooled_AA_BABIP: input 0.364078, training scale 0.010255, standardized input 6.202, contribution +0.533497.
- recent_draft_rank: input 0.500000, training scale 0.092746, standardized input 4.836, contribution +0.522638.
- log_pool_AAA: input 0.647103, training scale 0.334125, standardized input 1.681, contribution +0.498924.
- reorganized: input 1.000000, training scale 0.373272, standardized input 2.231, contribution +0.451447.

Largest ranking contributions on this same fit: scout_rank_score_0 -0.163256, scout_listed_2 -0.046689, scout_listed_0 +0.029295, scout_rank_score_2 -0.028077. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.948075. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 116.221101; additive output 452.128611; linked output 452.128611.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 1.000000, training scale 0.384669, standardized input 2.566, contribution +54.337045.
- pooled_RK124_K: input 0.194620, training scale 0.008501, standardized input -3.962, contribution +46.332628.
- recent_draft_rank: input 0.500000, training scale 0.094427, standardized input 4.489, contribution +39.258261.
- pooled_A_BB: input 0.156162, training scale 0.016190, standardized input 4.542, contribution +27.991139.
- pooled_AA_BABIP: input 0.364078, training scale 0.022801, standardized input 2.346, contribution +27.766373.
- scout_rank_score_1: input 0.890000, training scale 0.470781, standardized input 2.163, contribution +25.351417.
- pooled_RK124_BB: input 0.126582, training scale 0.003268, standardized input 14.184, contribution +21.438298.
- age_squared: input 2.560000, training scale 0.614180, standardized input 2.946, contribution +20.459918.

Largest ranking contributions on this same fit: scout_rank_score_0 +54.337045, scout_rank_score_1 +25.351417, scout_listed_0 +13.891040, scout_listed_1 -7.103163. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 116.212370; additive output 485.439565; linked output 485.439565.

Largest standardized terms are exact accounting, not causal effects:

- recent_draft_rank: input 0.500000, training scale 0.094427, standardized input 4.489, contribution +48.974147.
- scout_rank_score_0: input 0.890000, training scale 0.470781, standardized input 2.163, contribution +43.758206.
- pooled_RK124_K: input 0.194620, training scale 0.008501, standardized input -3.962, contribution +42.690522.
- age_squared: input 2.560000, training scale 0.614180, standardized input 2.946, contribution +35.125295.
- pooled_AA_BABIP: input 0.364078, training scale 0.022801, standardized input 2.346, contribution +30.251173.
- pooled_A_BB: input 0.156162, training scale 0.016190, standardized input 4.542, contribution +30.057277.
- pooled_RK124_BB: input 0.126582, training scale 0.003268, standardized input 14.184, contribution +28.187259.
- draft_rank: input 1.000000, training scale 0.232670, standardized input 3.109, contribution +18.423924.

Largest ranking contributions on this same fit: scout_rank_score_0 +43.758206, scout_listed_0 +7.387996, scout_listed_1 -2.804238, scout_listed_2 +2.779490. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 431.876337. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.909693; prediction 0.620777. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.600000, contribution +0.889861.
- position_6: scaled input 1.000000, contribution -0.258690.
- reorganized: scaled input 1.000000, contribution -0.199968.
- pooled_AA_BABIP: scaled input 0.640777, contribution +0.195950.
- draft_rank: scaled input 1.000000, contribution +0.189812.
- pooled_Aplus_BB: scaled input 0.815599, contribution +0.162038.
- pooled_A_BB: scaled input 0.761618, contribution +0.161785.
- age_squared: scaled input 2.560000, contribution +0.160749.

Holliday is both the largest offense harm and false high. At nineteen he has 581 current PA across four levels, twelve HR, 118 K and 99 walks; the current list moves him to rank one. New smooth chance .9316 times 452.13 conditional PA produces 421.20 versus trees 351.19 and 208 actual. Old smooth was even higher at 454.80, so fresher rankings improve the same smooth model while replacing the trees still worsens error. A stabilized rookie K term contributes +46.33 conditional PA, and rank/draft terms add substantial role expectation. Support is forty current-profile people and 35 active, not zero. Fixed hitting +.6208 versus -3.3098 actual is the larger delivered-offense failure. Among matched peers Merrill gets 593 PA and succeeds while Jett/Carson Williams and Mayer have none. A reasonable high arrival chance can coexist with uncertain role and hitting; this mixed group cannot justify either universal low forecasts or guaranteed full-season jobs.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Jett Williams | 40.87 | 48.72 | 0 | 0.165 | 0.000 |
| Jackson Merrill | 141.89 | 103.23 | 593 | 0.267 | 3.302 |
| Carson Williams | 56.54 | 51.35 | 0 | 0.107 | 0.000 |
| Marcelo Mayer | 144.89 | 82.73 | 0 | 0.236 | 0.000 |

## Ronny Mauricio 2022 to 2023

ID 677595; row 47956; fold 0; age input 21.0; Upper minors. Information date 2023-01-26. Selected: ordinary active.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 1 | 0 |
| scout_rank_score_0 | 0.23 | 0 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 1 | 1 |
| scout_rank_score_1 | 0.35 | 0.23 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 1 | 1 |
| scout_rank_score_2 | 0.39 | 0.35 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AA | 33 | 1 | 11 | 2 |
| 2021 | Aplus | 420 | 19 | 101 | 24 |
| 2022 | AA | 541 | 26 | 125 | 24 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.656879 | 146.385 | 96.157 | -0.92585 | 0.15269 |
| preseason | 0.538663 | 129.299 | 69.648 | -0.92585 | 0.11059 |
| old_smooth | 0.749226 | 178.517 | 133.749 | -0.92585 | 0.21238 |
| smooth_preseason | 0.674570 | 131.374 | 88.621 | -0.92585 | 0.14072 |
| Actual | 1 | not a forecast | 108 | -1.108334788754199 | 0.13864 |

Candidate product 0.674570159 × 131.373801469; offense yield -0.925851745/600 + 0.003130974.

Actual MLB counts: [{'season': 2023, 'player_id': 677595, 'bucket': 'MLB', 'plate_appearances': 108, 'strike_outs': 31, 'unintentional_walks': 7, 'hit_by_pitch': 0, 'home_runs': 2, 'babip_hits': 23, 'doubles': 4, 'triples': 0, 'babip_opportunities': 68}]. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 59 |
| old_smooth | participation | refined | 59 |
| old_smooth | conditional_pa | broad | 34 |
| old_smooth | conditional_pa | refined | 34 |
| smooth_preseason | participation | broad | 711 |
| smooth_preseason | participation | refined | 667 |
| smooth_preseason | conditional_pa | broad | 150 |
| smooth_preseason | conditional_pa | refined | 150 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.791516; additive output 0.728929; linked output 0.674570.

Largest standardized terms are exact accounting, not causal effects:

- on_40man: input 1.000000, training scale 0.140101, standardized input 6.995, contribution +2.167588.
- log_pool_AA: input 1.898219, training scale 0.573305, standardized input 2.881, contribution +1.057416.
- age_upper_interaction: input -1.200000, training scale 0.273129, standardized input -4.045, contribution +0.630591.
- pooled_AA_HR: input 0.044651, training scale 0.005016, standardized input 3.208, contribution +0.629568.
- reorganized: input 1.000000, training scale 0.285749, standardized input 3.186, contribution +0.581747.
- role_minor_0: input 4.368421, training scale 0.399050, standardized input 1.304, contribution +0.381237.
- position_6: input 1.000000, training scale 0.298499, standardized input 3.019, contribution +0.278158.
- log_pool_Aplus: input 1.472472, training scale 0.603648, standardized input 1.896, contribution +0.239854.

Largest ranking contributions on this same fit: scout_listed_2 +0.183603, scout_listed_1 -0.101683, scout_rank_score_1 -0.095371, scout_rank_score_2 +0.059121. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.791772; additive output 1.094489; linked output 0.749226.

Largest standardized terms are exact accounting, not causal effects:

- on_40man: input 1.000000, training scale 0.140101, standardized input 6.995, contribution +2.145971.
- log_pool_AA: input 1.898219, training scale 0.573305, standardized input 2.881, contribution +1.053712.
- reorganized: input 1.000000, training scale 0.285749, standardized input 3.186, contribution +0.671618.
- age_upper_interaction: input -1.200000, training scale 0.273129, standardized input -4.045, contribution +0.661333.
- pooled_AA_HR: input 0.044651, training scale 0.005016, standardized input 3.208, contribution +0.648443.
- role_minor_0: input 4.368421, training scale 0.399050, standardized input 1.304, contribution +0.379343.
- position_6: input 1.000000, training scale 0.298499, standardized input 3.019, contribution +0.300564.
- highest_AA: input 1.000000, training scale 0.302977, standardized input 2.963, contribution +0.240597.

Largest ranking contributions on this same fit: scout_listed_1 +0.163143, scout_listed_0 +0.098131, scout_rank_score_1 +0.036286, scout_listed_2 +0.035582. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.771923. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 115.331275; additive output 131.373801; linked output 131.373801.

Largest standardized terms are exact accounting, not causal effects:

- pooled_AA_HR: input 0.044651, training scale 0.010951, standardized input 1.673, contribution +31.511923.
- draft_elapsed: input 0.000000, training scale 0.207624, standardized input -1.235, contribution +15.516339.
- age_squared: input 1.440000, training scale 0.600635, standardized input 1.206, contribution +14.551118.
- scout_listed_1: input 1.000000, training scale 0.572354, standardized input 1.925, contribution -14.511348.
- position_6: input 1.000000, training scale 0.358653, standardized input 2.365, contribution +12.596767.
- highest_AA: input 1.000000, training scale 0.477906, standardized input 1.354, contribution -10.633658.
- pooled_AA_K: input 0.234942, training scale 0.041828, standardized input 0.728, contribution -10.337694.
- scout_rank_score_2: input 0.350000, training scale 0.457279, standardized input 1.152, contribution +9.856045.

Largest ranking contributions on this same fit: scout_listed_1 -14.511348, scout_rank_score_2 +9.856045, scout_rank_score_1 +5.256619, scout_listed_2 -4.704481. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 115.263461; additive output 178.516503; linked output 178.516503.

Largest standardized terms are exact accounting, not causal effects:

- pooled_AA_HR: input 0.044651, training scale 0.010951, standardized input 1.673, contribution +34.826714.
- age_squared: input 1.440000, training scale 0.600635, standardized input 1.206, contribution +20.952837.
- draft_elapsed: input 0.000000, training scale 0.207624, standardized input -1.235, contribution +15.611811.
- position_6: input 1.000000, training scale 0.358653, standardized input 2.365, contribution +14.505754.
- scout_listed_2: input 1.000000, training scale 0.431859, standardized input 2.667, contribution +13.903477.
- scout_rank_score_0: input 0.230000, training scale 0.494044, standardized input 0.776, contribution +12.497762.
- recent_draft_rank: input 0.000000, training scale 0.091078, standardized input -0.820, contribution -11.593987.
- pooled_AA_K: input 0.234942, training scale 0.041828, standardized input 0.728, contribution -11.044876.

Largest ranking contributions on this same fit: scout_listed_2 +13.903477, scout_rank_score_0 +12.497762, scout_listed_1 -8.351948, scout_rank_score_1 +6.999586. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 166.685651. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.775135; prediction -0.925852. Largest terms on its deterministic input scale:

- age_centered: scaled input -1.200000, contribution +0.607262.
- position_6: scaled input 1.000000, contribution -0.290864.
- pooled_AA_pa: scaled input 0.945667, contribution -0.182437.
- reorganized: scaled input 1.000000, contribution -0.126895.
- pooled_Aplus_pa: scaled input 0.560000, contribution -0.075822.
- Aplus_1_pa: scaled input 0.700000, contribution -0.071811.
- pooled_AA_HR: scaled input 0.146509, contribution +0.063401.
- AA_0_pa: scaled input 0.901667, contribution +0.059126.

Mauricio is the ordered ordinary-active offense case. His 541 AA PA include 26 HR, 125 K and 24 walks at age 21. He falls off the current list, but remains listed in older lags. Smooth chance .6746 times 131.37 conditional PA gives 88.62 versus trees 69.65, old smooth 133.75 and 108 actual. The same new fit with old rank inputs gives .7719 and 166.69 conditional PA, showing the personal ranking update reduces immediate expectation. AA HR adds +31.51 conditional PA, with an older-listed term subtracting 14.51. The fixed rate -.9259 is near the realized -1.1083; candidate offense .1407 is close to .1385 actual, without the extreme rate/workload cancellation seen in Holliday. Rojas gets 164 PA while Dale, Barrosa and Hernandez do not appear. This is a sensible ordinary gain and a useful control, not a reason to ignore star readiness misses elsewhere.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Jarryd Dale | 1.98 | 1.99 | 0 | 0.004 | 0.000 |
| Jorge Barrosa | 74.10 | 68.78 | 0 | 0.171 | 0.000 |
| Johan Rojas | 80.50 | 54.86 | 164 | 0.111 | 0.749 |
| Diego Hernandez | 41.65 | 30.04 | 0 | 0.077 | 0.000 |

## Kevin Maitan 2017 to 2018

ID 670867; row 31364; fold 4; age input 17.0; Lower minors. Information date 2018-01-27. Selected: intended fixed Maitan case; ID correction documented separately.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 1 | 1 |
| scout_rank_score_0 | 0.69 | 0.14 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 1 |
| scout_rank_score_1 | 0 | 0.69 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2017 | RK120 | 176 | 2 | 49 | 10 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.007357 | 177.625 | 1.307 | -0.20648 | 0.00357 |
| preseason | 0.015228 | 130.367 | 1.985 | -0.20648 | 0.00542 |
| old_smooth | 0.014149 | 320.464 | 4.534 | -0.20648 | 0.01239 |
| smooth_preseason | 0.009090 | 284.504 | 2.586 | -0.20648 | 0.00707 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product 0.009090113 × 284.504269399; offense yield -0.206475487/600 + 0.003076176.

Actual MLB counts: []. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 4 |
| old_smooth | participation | refined | 4 |
| old_smooth | conditional_pa | broad | 1 |
| old_smooth | conditional_pa | refined | 1 |
| smooth_preseason | participation | broad | 11 |
| smooth_preseason | participation | refined | 5 |
| smooth_preseason | conditional_pa | broad | 0 |
| smooth_preseason | conditional_pa | refined | 0 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.794088; additive output -4.691436; linked output 0.009090.

Largest standardized terms are exact accounting, not causal effects:

- scout_listed_0: input 1.000000, training scale 0.106412, standardized input 9.290, contribution +0.947889.
- position_6: input 1.000000, training scale 0.294954, standardized input 3.064, contribution +0.374835.
- scout_listed_1: input 1.000000, training scale 0.079246, standardized input 12.539, contribution +0.247106.
- highest_complex: input 1.000000, training scale 0.399049, standardized input 2.008, contribution -0.245235.
- scout_rank_score_0: input 0.140000, training scale 0.061568, standardized input 2.180, contribution +0.226405.
- role_minor_0: input 4.153846, training scale 0.432167, standardized input 0.749, contribution +0.167292.
- age_squared: input 4.000000, training scale 1.218451, standardized input 1.993, contribution -0.140167.
- position_2: input 0.000000, training scale 0.382583, standardized input -0.465, contribution -0.130433.

Largest ranking contributions on this same fit: scout_listed_0 +0.947889, scout_listed_1 +0.247106, scout_rank_score_0 +0.226405, scout_rank_score_1 +0.100884. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.745728; additive output -4.243880; linked output 0.014149.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.690000, training scale 0.042948, standardized input 15.996, contribution +0.981952.
- scout_listed_0: input 1.000000, training scale 0.079246, standardized input 12.539, contribution +0.756623.
- position_6: input 1.000000, training scale 0.294954, standardized input 3.064, contribution +0.414129.
- highest_complex: input 1.000000, training scale 0.399049, standardized input 2.008, contribution -0.267496.
- role_minor_0: input 4.153846, training scale 0.432167, standardized input 0.749, contribution +0.175732.
- pooled_RK120_K: input 0.260870, training scale 0.013471, standardized input 2.377, contribution -0.133258.
- position_2: input 0.000000, training scale 0.382583, standardized input -0.465, contribution -0.130563.
- log_pool_AA: input 0.000000, training scale 0.594216, standardized input -0.430, contribution -0.111072.

Largest ranking contributions on this same fit: scout_rank_score_0 +0.981952, scout_listed_0 +0.756623, scout_list_available_1 +0.025259, scout_rank_score_1 +0.017626. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.016083. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 111.640131; additive output 284.504269; linked output 284.504269.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_1: input 0.690000, training scale 0.192068, standardized input 3.264, contribution +47.903037.
- pooled_RK120_BB: input 0.065217, training scale 0.004036, standardized input -3.682, contribution +30.665735.
- log_pool_RK120: input 1.015231, training scale 0.186620, standardized input 5.227, contribution +28.695965.
- pooled_RK120_K: input 0.260870, training scale 0.010351, standardized input 3.141, contribution +24.445144.
- log_minor_pa_1: input 0.000000, training scale 0.431256, standardized input -3.692, contribution +23.474845.
- log_games_minor_1: input 0.000000, training scale 0.204629, standardized input -3.339, contribution +16.380407.
- draft_elapsed: input 0.000000, training scale 0.198423, standardized input -1.156, contribution +15.962578.
- log_pool_Aplus: input 0.000000, training scale 0.660480, standardized input -1.683, contribution +15.029020.

Largest ranking contributions on this same fit: scout_rank_score_1 +47.903037, scout_listed_0 +11.804338, scout_rank_score_0 +1.924155, scout_list_available_2 +1.357566. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 111.646142; additive output 320.464385; linked output 320.464385.

Largest standardized terms are exact accounting, not causal effects:

- scout_rank_score_0: input 0.690000, training scale 0.192068, standardized input 3.264, contribution +61.173159.
- pooled_RK120_BB: input 0.065217, training scale 0.004036, standardized input -3.682, contribution +33.628230.
- age_squared: input 4.000000, training scale 0.646502, standardized input 4.945, contribution +28.774687.
- log_pool_RK120: input 1.015231, training scale 0.186620, standardized input 5.227, contribution +25.347838.
- log_minor_pa_1: input 0.000000, training scale 0.431256, standardized input -3.692, contribution +23.986554.
- pooled_RK120_K: input 0.260870, training scale 0.010351, standardized input 3.141, contribution +22.820915.
- log_pool_Aplus: input 0.000000, training scale 0.660480, standardized input -1.683, contribution +16.735356.
- draft_elapsed: input 0.000000, training scale 0.198423, standardized input -1.156, contribution +15.615625.

Largest ranking contributions on this same fit: scout_rank_score_0 +61.173159, scout_listed_0 +8.986113, scout_listed_2 +1.807993, scout_list_available_2 -1.745457. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 260.140812. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.728554; prediction -0.206475. Largest terms on its deterministic input scale:

- age_centered: scaled input -2.000000, contribution +0.921225.
- position_6: scaled input 1.000000, contribution -0.262275.
- draft_class_unknown: scaled input 1.000000, contribution -0.204122.
- age_squared: scaled input 4.000000, contribution +0.096981.
- absence_window_scaled: scaled input 1.000000, contribution -0.033994.
- pooled_RK120_pa: scaled input 0.293333, contribution +0.001508.
- pooled_RK120_BB: scaled input -0.147826, contribution +0.001085.
- pooled_RK120_BABIP: scaled input 0.145540, contribution +0.000792.

The intended Kevin Maitan case uses verified ID 670867. At seventeen he has 176 rookie PA with two HR, 49 K and ten walks; his rank score falls .69 to .14, corresponding to rank 87 in the newer list. New smooth chance .00909 and conditional PA 284.50 yield 2.59 expected PA versus trees 1.99, old smooth 4.53 and zero actual. On the same fit, old ranks give chance .01608 and conditional PA 260.14: the newer list lowers immediate probability but moves strong old ranking evidence into the conditional lag term, which adds +47.90 PA. Current refined active-head support is zero. Infante, Jean Cruz, Caraballo and Verbel also do not appear next year. Fixed hitting -.2065 is largely age and position rather than his tiny observed sample. His low immediate expectation makes baseball sense; zero next-year PA is not observed zero batting talent or a settled eventual-career forecast.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Diego Infante | 0.08 | 0.19 | 0 | 0.001 | 0.000 |
| Jean Cruz | 0.05 | 0.05 | 0 | 0.000 | 0.000 |
| Andrew Caraballo | 0.06 | 0.00 | 0 | 0.000 | 0.000 |
| Dewins Verbel | 0.06 | 0.00 | 0 | 0.000 | 0.000 |

## Emil Morales 2024 to 2025

ID 815896; row 58297; fold 4; age input 17.0; Lower minors. Information date 2025-01-24. Selected: ordered largest raw conditional PA; boundary and rare-column review.

| Ranking input | Old source | Fresh source |
| --- | ---: | ---: |
| scout_list_available_0 | 1 | 1 |
| scout_listed_0 | 0 | 0 |
| scout_rank_score_0 | 0 | 0 |
| scout_list_available_1 | 1 | 1 |
| scout_listed_1 | 0 | 0 |
| scout_rank_score_1 | 0 | 0 |
| scout_list_available_2 | 1 | 1 |
| scout_listed_2 | 0 | 0 |
| scout_rank_score_2 | 0 | 0 |

| Known season | Level | PA | HR | K | UBB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | DSL | 201 | 14 | 45 | 40 |

| Arm | Appearance chance | PA if active | Expected PA | Fixed hitting per 600 PA | Offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | 0.001745 | 89.869 | 0.157 | -0.13155 | 0.00046 |
| preseason | 0.001540 | 66.489 | 0.102 | -0.13155 | 0.00030 |
| old_smooth | 0.002964 | 800.000 | 2.371 | -0.13155 | 0.00689 |
| smooth_preseason | 0.002020 | 800.000 | 1.616 | -0.13155 | 0.00469 |
| Actual | 0 | not a forecast | 0 | unobserved | 0.00000 |

Candidate product 0.002019557 × 800.000000000; offense yield -0.131548786/600 + 0.003122875.

Actual MLB counts: []. No PA is not observed zero batting talent.

| Earlier profile | Head | Profile detail | Distinct people |
| --- | --- | --- | ---: |
| old_smooth | participation | broad | 3841 |
| old_smooth | participation | refined | 2366 |
| old_smooth | conditional_pa | broad | 2 |
| old_smooth | conditional_pa | refined | 2 |
| smooth_preseason | participation | broad | 4184 |
| smooth_preseason | participation | refined | 2463 |
| smooth_preseason | conditional_pa | broad | 0 |
| smooth_preseason | conditional_pa | refined | 0 |

Broad counts do not create matched elite-star analogues. Full profile definitions and all actual inputs are in the machine-readable case summary.

Saved smooth_preseason participation: reference -5.861783; additive output -6.202856; linked output 0.002020.

Largest standardized terms are exact accounting, not causal effects:

- pooled_DSL_HR: input 0.056478, training scale 0.006901, standardized input 4.384, contribution +0.565540.
- pooled_DSL_BB: input 0.159468, training scale 0.015402, standardized input 4.843, contribution -0.415351.
- position_6: input 1.000000, training scale 0.298784, standardized input 3.015, contribution +0.391221.
- role_minor_0: input 4.303571, training scale 0.395246, standardized input 1.159, contribution +0.299330.
- log_pool_DSL: input 1.101940, training scale 0.477098, standardized input 1.730, contribution -0.256390.
- highest_DSL: input 1.000000, training scale 0.375443, standardized input 2.211, contribution -0.240718.
- age_squared: input 4.000000, training scale 1.242641, standardized input 1.918, contribution -0.194108.
- draft_rank: input 0.000000, training scale 0.157222, standardized input -0.703, contribution -0.163638.

Largest ranking contributions on this same fit: scout_listed_0 +0.057636, scout_rank_score_1 -0.057397, scout_listed_2 +0.035870, scout_rank_score_0 +0.023583. All ranking terms remain in the machine-readable summary.

Saved old_smooth participation: reference -5.861624; additive output -5.818138; linked output 0.002964.

Largest standardized terms are exact accounting, not causal effects:

- pooled_DSL_HR: input 0.056478, training scale 0.006901, standardized input 4.384, contribution +0.588808.
- position_6: input 1.000000, training scale 0.298784, standardized input 3.015, contribution +0.419037.
- pooled_DSL_BB: input 0.159468, training scale 0.015402, standardized input 4.843, contribution -0.397246.
- role_minor_0: input 4.303571, training scale 0.395246, standardized input 1.159, contribution +0.300974.
- log_pool_DSL: input 1.101940, training scale 0.477098, standardized input 1.730, contribution -0.254110.
- highest_DSL: input 1.000000, training scale 0.375443, standardized input 2.211, contribution -0.244420.
- reorganized: input 1.000000, training scale 0.419844, standardized input 1.838, contribution +0.226253.
- draft_rank: input 0.000000, training scale 0.157222, standardized input -0.703, contribution -0.168108.

Largest ranking contributions on this same fit: scout_listed_2 +0.049579, scout_listed_0 +0.046886, scout_rank_score_2 +0.044104, scout_listed_1 +0.022663. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 0.002020. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Saved smooth_preseason conditional_pa: reference 116.435205; additive output 1150.934287; linked output 1150.934287.

Largest standardized terms are exact accounting, not causal effects:

- pooled_DSL_BB: input 0.159468, training scale 0.001377, standardized input 57.673, contribution +539.740285.
- pooled_DSL_HR: input 0.056478, training scale 0.000541, standardized input 48.974, contribution +353.745571.
- log_pool_DSL: input 1.101940, training scale 0.056746, standardized input 19.352, contribution +99.652803.
- pooled_DSL_3B: input 0.001661, training scale 0.000365, standardized input -9.206, contribution +76.581335.
- pooled_DSL_BABIP: input 0.343434, training scale 0.001611, standardized input 26.903, contribution -73.437866.
- age_squared: input 4.000000, training scale 0.625640, standardized input 5.190, contribution +26.363372.
- reorganized: input 1.000000, training scale 0.454885, standardized input 1.555, contribution -18.814311.
- draft_elapsed: input 0.000000, training scale 0.210813, standardized input -1.191, contribution +15.520705.

Largest ranking contributions on this same fit: scout_rank_score_1 +2.233432, scout_rank_score_0 -1.184967, scout_list_available_2 +1.183046, scout_rank_score_2 +1.013463. All ranking terms remain in the machine-readable summary.

Saved old_smooth conditional_pa: reference 116.409297; additive output 1238.635490; linked output 1238.635490.

Largest standardized terms are exact accounting, not causal effects:

- pooled_DSL_BB: input 0.159468, training scale 0.001377, standardized input 57.673, contribution +575.994941.
- pooled_DSL_HR: input 0.056478, training scale 0.000541, standardized input 48.974, contribution +361.612697.
- log_pool_DSL: input 1.101940, training scale 0.056746, standardized input 19.352, contribution +103.304058.
- pooled_DSL_BABIP: input 0.343434, training scale 0.001611, standardized input 26.903, contribution -75.029517.
- pooled_DSL_3B: input 0.001661, training scale 0.000365, standardized input -9.206, contribution +74.069088.
- age_squared: input 4.000000, training scale 0.625640, standardized input 5.190, contribution +48.844910.
- pooled_DSL_HBP: input 0.016611, training scale 0.000944, standardized input 6.958, contribution +17.132553.
- log_pool_AA: input 0.000000, training scale 0.659362, standardized input -2.000, contribution -16.338590.

Largest ranking contributions on this same fit: scout_rank_score_0 +4.111726, scout_listed_2 +1.626677, scout_list_available_1 +1.366677, scout_listed_1 -1.219222. All ranking terms remain in the machine-readable summary.

Same new fit with old ranking inputs: 1150.934287. Same fitted candidate with old ranking inputs; mechanics only, not causality or a validated alternative.

Unchanged saved hitting head: reference -0.910294; prediction -0.131549. Largest terms on its deterministic input scale:

- age_centered: scaled input -2.000000, contribution +1.105863.
- position_6: scaled input 1.000000, contribution -0.249036.
- age_squared: scaled input 4.000000, contribution +0.223032.
- reorganized: scaled input 1.000000, contribution -0.201481.
- draft_class_unknown: scaled input 1.000000, contribution -0.085530.
- absence_window_scaled: scaled input 1.000000, contribution -0.032667.
- pooled_DSL_BB: scaled input 0.794684, contribution +0.022727.
- elapsed_scaled: scaled input -0.100000, contribution -0.011738.

Morales is the ordered largest raw conditional-PA case. At seventeen his only source is 201 DSL PA with fourteen HR, 45 K and forty walks; he is not on the current top-100 list. The appearance head gives .202% probability, but the conditional head extrapolates to 1,150.93 PA before the declared 800 bound. DSL walks and HR are about 57.7 and 49.0 training standard deviations from the active-head means, contributing +539.74 and +353.75 PA. Refined active support is zero even though participation has 2,463 people. Clipping produces only 1.62 expected PA versus trees .10 and actual zero, so the unreasonable conditional output is hidden by a sensible low participation chance. Naibel Mariano, José Anderson, Soto and Arguelles also have no next-year MLB use. This confirms rare-column extrapolation in the conditional head, not a bad two-PA point forecast, and certainly not evidence that Morales lacks eventual upside. Keep it visible; do not claim physical bounds repaired the learned model.

| Origin-selected peer | Fresh tree PA | Fresh smooth PA | Actual PA | Fresh smooth offense | Actual offense |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naibel Mariano | 0.11 | 0.00 | 0 | 0.000 | 0.000 |
| José Anderson | 0.07 | 0.67 | 0 | 0.002 | 0.000 |
| Juarlin Soto | 0.10 | 0.32 | 0 | 0.001 | 0.000 |
| Cristian Arguelles | 0.08 | 0.35 | 0 | 0.001 | 0.000 |

## Decision after actual review

Retain the fresher-ranking tree candidate. The exact smooth opportunity model benefits from fresher rankings relative to its own old-source version, but does not clearly beat the current candidate on delivered offense. Keep the matched smooth results as development evidence, not a new deployed model or a general rejection of smooth models.

Close ranking-vintage and opportunity-penalty experiments. The next coherent model milestone is the prospect batting-talent bridge, with the established-player rate benchmark protected. Audit which prior component/MLE results have comparable future-MLB targets and legitimate chronological adjustments before a bounded matched comparison; do not presume that short-sample superstars should have been forecast exactly. Preserve failed peers and joint value checks. No new college collection, name-specific overrides, protected 2026 use or deployment.
