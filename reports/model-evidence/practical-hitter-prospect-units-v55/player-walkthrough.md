# Fixed baseball-unit prospect model: actual player review

Nine complete source-to-fit reviews. The full candidate is not adopted. Fixed references remove extreme rare-column standardization but the fitted workload model materially deteriorates. All established forecasts are bit-exact.

The same features, sources, temporal/player folds, targets, numeric C=.01 and alpha=100 are retained. Important qualification: changing predictor units changes effective regularization even with numeric penalties held constant. This is a representation-and-shrinkage comparison, not isolated causal proof about StandardScaler or a rejection of smooth prospect models.

| Scope | Rows | Baseline PA RMSE | Standardized PA RMSE | Fixed PA RMSE | Baseline offense RMSE | Standardized offense RMSE | Fixed offense RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 30506 | 60.686 | 60.613 | 61.387 | 0.453826 | 0.455445 | 0.454702 |
| never_debut | 24199 | 27.745 | 27.547 | 29.623 | 0.154072 | 0.160075 | 0.157282 |
| upper_never_debut | 5454 | 56.242 | 55.792 | 60.141 | 0.317069 | 0.327814 | 0.323697 |
| lower_never_debut | 17852 | 7.828 | 7.923 | 7.880 | 0.042824 | 0.043641 | 0.042911 |

Future-participant rate scoring uses actual PA within each target year and equal years. Contribution retains non-arrivals. The rate is custom fixed-event, origin-centered batting wins/600, not official wOBA or latent park-neutral skill. Offense includes replacement, not fielding/full WAR. No new park/opponent correction is introduced. Four peers per case are selected using origin information, not future outcomes.

## Nick Kurtz: 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0, highest observed current level AA. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Draft 2024, pick 4, class 4YR JR. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.017252 | 115.972916 | 2.000789 | -0.063223 | 0.006040 |
| Standardized prospect | 0.125809 | 223.707331 | 28.144307 | 0.745337 | 0.122889 |
| Fixed-unit prospect | 0.028607 | 200.678842 | 5.740764 | 0.298603 | 0.020792 |
| Actual | 1 | Not a forecast | 489 | 5.289192 | 5.838406 |

Fixed expected PA = 0.028606723 × 200.678842186. Offense = expected PA × (rate/600 + origin replacement 0.003124161/PA). PA-only offense 0.017330; rate-only 0.007247.

participation: intercept -5.704140745, exact linear sum -3.525089633, linked output 0.028606723. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.2000000 | 0.0000000 | 1.0000000 | 0.7392927 |
| draft_rank | 0.8176145 | 0.0000000 | 1.0000000 | 0.3087593 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | 0.2830722 |
| draft_upper_interaction | 0.8176145 | 0.0000000 | 1.0000000 | 0.2367633 |
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | -0.1600390 |

conditional_pa: intercept 114.338680792, exact linear sum 200.678842186, linked output 200.678842186. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 30.8302647 |
| age_upper_interaction | -1.2000000 | 0.0000000 | 1.0000000 | 26.8337910 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 14.7525472 |
| highest_AA | 1.0000000 | 0.0000000 | 1.0000000 | -14.5174388 |
| draft_rank | 0.8176145 | 0.0000000 | 1.0000000 | 10.2431965 |

rate: intercept -0.253963650, exact linear sum 0.298602550, linked output 0.298602550. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 0.5575893 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.3307997 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 0.2773931 |
| position_3 | 1.0000000 | 0.0000000 | 1.0000000 | 0.1573337 |
| scout_list_available_2 | 1.0000000 | 0.0000000 | 1.0000000 | -0.1252315 |

Broad actual training-profile support: participation 4 distinct people, conditional_pa 0 distinct people, rate 0 distinct people.

Kurtz's 2024 AA record is real, but very short; the history, first-round pick and recent draft date are not a full-season readiness record. Fixed units remove the amplified recent-pedigree term seen in the standardized rate fit. Arrival rises only from 1.7% to 2.9%, and expected PA from 2 to 6, versus 489 actual. The rate moves from -0.06 to +0.30 versus +5.29 actual. Age and its square now dominate the rate adjustment, not recent AA power. Four broad readiness-profile players and zero conditional participants do not support confidence in this prediction. Moore and Smith also receive too little PA, while Montgomery and Williams did not play in MLB. A higher forecast for every recent first-rounder is not automatically correct; this fit nevertheless misses the fast-entry cases badly.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Benny Montgomery | 6.54 | 11.09 | 0 | -0.5396 | unobserved |
| Christian Moore | 8.23 | 11.31 | 184 | 0.4566 | -1.0849 |
| Cam Smith | 2.33 | 7.73 | 493 | 0.2011 | -0.4969 |
| Jett Williams | 74.66 | 46.18 | 0 | 0.0945 | unobserved |

## Wyatt Langford: 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0, highest observed current level AAA. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

Draft 2023, pick 4, class 4YR JR. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.201829 | 213.555553 | 43.101733 | 0.688029 | 0.182872 |
| Standardized prospect | 0.729966 | 293.808130 | 214.469904 | 1.014924 | 1.026800 |
| Fixed-unit prospect | 0.128688 | 247.482041 | 31.847917 | 0.850008 | 0.143722 |
| Actual | 1 | Not a forecast | 557 | 0.076953 | 1.795953 |

Fixed expected PA = 0.128687790 × 247.482040780. Offense = expected PA × (rate/600 + origin replacement 0.003096076/PA). PA-only offense 0.135124; rate-only 0.194508.

participation: intercept -5.766914130, exact linear sum -1.912611126, linked output 0.128687790. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.2000000 | 0.0000000 | 1.0000000 | 0.7382092 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | 0.3821031 |
| highest_AAA | 1.0000000 | 0.0000000 | 1.0000000 | 0.3163390 |
| draft_rank | 0.8176145 | 0.0000000 | 1.0000000 | 0.3099847 |
| role_minor_0 | 4.4444444 | 4.0000000 | 1.0000000 | 0.3023691 |

conditional_pa: intercept 108.041474703, exact linear sum 247.482040780, linked output 247.482040780. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 25.7093310 |
| age_upper_interaction | -1.2000000 | 0.0000000 | 1.0000000 | 19.7810760 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 16.3268196 |
| draft_rank | 0.8176145 | 0.0000000 | 1.0000000 | 13.1831002 |
| highest_AAA | 1.0000000 | 0.0000000 | 1.0000000 | 11.0957756 |

rate: intercept 0.038245237, exact linear sum 0.850007924, linked output 0.850007924. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 0.6679617 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.4070875 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 0.2988227 |
| position_7 | 1.0000000 | 0.0000000 | 1.0000000 | 0.2683413 |
| scout_listed_2 | -1.0000000 | 0.0000000 | 1.0000000 | -0.2676070 |

Broad actual training-profile support: participation 31 distinct people, conditional_pa 2 distinct people, rate 2 distinct people.

Langford's three-level 2023 history, college draft context and recent pick are present. The fixed scale stops the tiny rookie-league double sample from making a -42 PA term. But holding C=.01 and alpha=100 in different units changes effective shrinkage: the useful standardized readiness effects are also diminished. Arrival falls from the corrected baseline's 20% to 13%, expected PA from 43 to 32, versus 557. Conditional PA is 247, so both probability and conditional workload limit opportunity. Rate +0.85 remains well above +0.08 actual. Crews receives only 14 PA versus 132; Shaw, Wilken and Veen did not arrive. Removing an implausible term is a sound representation repair, not evidence that the resulting total forecast is better.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Zac Veen | 85.17 | 53.71 | 0 | 0.0406 | unobserved |
| Dylan Crews | 12.55 | 14.27 | 132 | 0.1606 | -1.7462 |
| Matt Shaw | 34.13 | 17.49 | 0 | -0.1032 | unobserved |
| Brock Wilken | 6.42 | 7.31 | 0 | 0.1647 | unobserved |

## Cody Bellinger: 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0, highest observed current level AAA. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Draft 2013, pick 124, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.110193 | 139.597326 | 15.382612 | 0.084596 | 0.049672 |
| Standardized prospect | 0.282332 | 120.934913 | 34.143757 | -0.011420 | 0.104789 |
| Fixed-unit prospect | 0.184025 | 138.129309 | 25.419277 | 0.036832 | 0.080057 |
| Actual | 1 | Not a forecast | 548 | 2.928011 | 4.366524 |

Fixed expected PA = 0.184025223 × 138.129308540. Offense = expected PA × (rate/600 + origin replacement 0.003088092/PA). PA-only offense 0.082081; rate-only 0.048447.

participation: intercept -5.986890043, exact linear sum -1.489310612, linked output 0.184025223. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 1.7316555 | 0.0000000 | 1.0000000 | 1.0549209 |
| log_minor_pa_0 | 1.7526721 | 0.0000000 | 1.0000000 | 0.7092377 |
| age_upper_interaction | -1.4000000 | 0.0000000 | 1.0000000 | 0.7061521 |
| log_minor_pa_1 | 1.8625285 | 0.0000000 | 1.0000000 | 0.5393958 |
| log_pool_Aplus | 1.6774703 | 0.0000000 | 1.0000000 | 0.3364898 |

conditional_pa: intercept 80.006221792, exact linear sum 138.129308540, linked output 138.129308540. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.9600000 | 0.0000000 | 1.0000000 | 34.3225895 |
| age_upper_interaction | -1.4000000 | 0.0000000 | 1.0000000 | 19.3316953 |
| log_minor_pa_1 | 1.8625285 | 0.0000000 | 1.0000000 | -18.6528336 |
| age_centered | -1.4000000 | 0.0000000 | 1.0000000 | 13.9421013 |
| log_pool_AA | 1.7316555 | 0.0000000 | 1.0000000 | 12.7284747 |

rate: intercept 0.389702579, exact linear sum 0.036832321, linked output 0.036832321. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.9600000 | 0.0000000 | 1.0000000 | 0.4522979 |
| log_minor_pa_1 | 1.8625285 | 0.0000000 | 1.0000000 | -0.4175959 |
| age_centered | -1.4000000 | 0.0000000 | 1.0000000 | 0.2777448 |
| log_pool_AA | 1.7316555 | 0.0000000 | 1.0000000 | -0.2152721 |
| log_minor_pa_2 | 1.2029723 | 0.0000000 | 1.0000000 | -0.1981107 |

Broad actual training-profile support: participation 561 distinct people, conditional_pa 122 distinct people, rate 122 distinct people.

Bellinger's substantial AA season and earlier High-A history are present, along with only a brief AAA appearance. AA log exposure adds 1.05 to the arrival logit and roughly 13 conditional PA; old complex-league HR no longer supplies the large negative terms seen in the standardized fit. Expected PA rises from 15 to 25 but remains far below 548, and rate +0.04 remains far below +2.93 actual. Conditional workload is only 138 even if he arrives. Verdugo's 30 forecast PA versus 25 actual is reasonable, but the other selected peers did not arrive; those peers do not excuse the missed breakout. Better numerical behavior does not resolve the prospect opportunity or upside problem.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Alex Verdugo | 32.00 | 30.21 | 25 | -0.5260 | -3.6858 |
| Isiah Kiner-Falefa | 18.75 | 20.68 | 0 | -0.4683 | unobserved |
| Drew Ward | 1.95 | 11.65 | 0 | -0.3315 | unobserved |
| Jamie Westbrook | 4.21 | 24.85 | 0 | -0.7855 | unobserved |

## Pete Alonso: 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0, highest observed current level AAA. Selection: fixed diagnostic, false low.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Draft 2016, pick 64, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.692850 | 183.403275 | 127.070997 | 0.286158 | 0.451826 |
| Standardized prospect | 0.670824 | 206.524898 | 138.541939 | 2.517438 | 1.007823 |
| Fixed-unit prospect | 0.258407 | 145.421836 | 37.577972 | 0.733238 | 0.161616 |
| Actual | 1 | Not a forecast | 693 | 3.864560 | 6.597153 |

Fixed expected PA = 0.258406666 × 145.421835535. Offense = expected PA × (rate/600 + origin replacement 0.003078768/PA). PA-only offense 0.133616; rate-only 0.546511.

participation: intercept -6.071381229, exact linear sum -1.054266458, linked output 0.258406666. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_0 | 1.9080599 | 0.0000000 | 1.0000000 | 0.9014587 |
| log_pool_AA | 1.4124493 | 0.0000000 | 1.0000000 | 0.8865737 |
| log_pool_AAA | 1.3887912 | 0.0000000 | 1.0000000 | 0.8748352 |
| age_upper_interaction | -0.8000000 | 0.0000000 | 1.0000000 | 0.4423710 |
| log_minor_pa_1 | 1.5953390 | 0.0000000 | 1.0000000 | 0.3411399 |

conditional_pa: intercept 70.720813225, exact linear sum 145.421835535, linked output 145.421835535. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_1 | 1.5953390 | 0.0000000 | 1.0000000 | -17.3512385 |
| log_pool_AA | 1.4124493 | 0.0000000 | 1.0000000 | 16.2586316 |
| age_squared | 0.6400000 | 0.0000000 | 1.0000000 | 15.2246405 |
| age_upper_interaction | -0.8000000 | 0.0000000 | 1.0000000 | 12.7033014 |
| log_pool_AAA | 1.3887912 | 0.0000000 | 1.0000000 | 11.6781538 |

rate: intercept -0.187041274, exact linear sum 0.733237757, linked output 0.733237757. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_1 | 1.5953390 | 0.0000000 | 1.0000000 | -0.3399502 |
| log_minor_pa_2 | 0.8020016 | 0.0000000 | 1.0000000 | -0.3191623 |
| position_3 | 1.0000000 | 0.0000000 | 1.0000000 | 0.2737553 |
| log_minor_pa_0 | 1.9080599 | 0.0000000 | 1.0000000 | 0.2562041 |
| age_centered | -0.8000000 | 0.0000000 | 1.0000000 | 0.2181954 |

Broad actual training-profile support: participation 805 distinct people, conditional_pa 165 distinct people, rate 165 distinct people.

Alonso had 36 HR and 574 PA across AA and AAA in 2018. His source is neither missing nor a rookie-sample artifact. The fixed model retains positive AA/AAA exposure terms but suppresses power's influence under the unchanged numeric Ridge penalty. Arrival falls from 69% to 26%, conditional PA from 183 to 145, and expected PA from 127 to 38, versus 693. Rate +0.73 is less low than the baseline's +0.29 but far below +3.86 actual. This is the largest underpredicted delivered-offense error selected here. Mercado and Solak also outperform their modest workload forecasts; Neuse has limited playing time and Brigman none. The evidence argues against this fitted joint construction, not against using minor-league power.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Nick Solak | 33.17 | 24.54 | 135 | -0.6278 | 3.3497 |
| Óscar Mercado | 87.73 | 82.22 | 482 | -1.0116 | 0.5131 |
| Bryson Brigman | 4.46 | 11.82 | 0 | -0.8712 | unobserved |
| Sheldon Neuse | 29.60 | 21.34 | 61 | 0.4064 | -2.2791 |

## Ethan Salas: 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0, highest observed current level Aplus. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Draft None, pick None, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.025632 | 281.841619 | 7.224140 | -0.511711 | 0.016408 |
| Standardized prospect | 0.011711 | 173.073507 | 2.026800 | 0.790657 | 0.009003 |
| Fixed-unit prospect | 0.022907 | 181.868698 | 4.166103 | 1.364994 | 0.022493 |
| Actual | 0 | Not a forecast | 0 | unobserved | 0.000000 |

Fixed expected PA = 0.022907204 × 181.868697688. Offense = expected PA × (rate/600 + origin replacement 0.003124161/PA). PA-only offense 0.009463; rate-only 0.039004.

participation: intercept -5.957437469, exact linear sum -3.753130175, linked output 0.022907204. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_0 | 1.7387102 | 0.0000000 | 1.0000000 | 0.5531051 |
| log_pool_Aplus | 1.7894234 | 0.0000000 | 1.0000000 | 0.4090020 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | 0.3058759 |
| position_2 | 1.0000000 | 0.0000000 | 1.0000000 | 0.2756625 |
| age_squared | 3.2400000 | 0.0000000 | 1.0000000 | -0.2402288 |

conditional_pa: intercept 95.977093781, exact linear sum 181.868697688, linked output 181.868697688. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 3.2400000 | 0.0000000 | 1.0000000 | 72.2743693 |
| age_centered | -1.8000000 | 0.0000000 | 1.0000000 | 28.6950642 |
| log_minor_pa_1 | 1.3609766 | 0.0000000 | 1.0000000 | -21.9837067 |
| scout_rank_score_0 | 0.9300000 | 0.0000000 | 1.0000000 | 20.8841118 |
| scout_listed_0 | 1.0000000 | 0.0000000 | 1.0000000 | 17.4750124 |

rate: intercept -0.192516484, exact linear sum 1.364993986, linked output 1.364993986. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 3.2400000 | 0.0000000 | 1.0000000 | 1.3779442 |
| age_centered | -1.8000000 | 0.0000000 | 1.0000000 | 0.5436815 |
| position_2 | 1.0000000 | 0.0000000 | 1.0000000 | -0.3295097 |
| log_minor_pa_1 | 1.3609766 | 0.0000000 | 1.0000000 | -0.2897673 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.2586527 |

Broad actual training-profile support: participation 3838 distinct people, conditional_pa 7 distinct people, rate 7 distinct people.

Salas's young age, catcher position, rankings, existing A/High-A history and missing 2020 minor season are not conflated. Arrival is 2.3% and expected PA 4 versus zero actual; there is no observed future MLB rate to validate his +1.36 conditional estimate. The age-square term alone contributes +1.38 batting wins/600, with only seven broad conditional-profile training players. The fixed scale removes the prior +5.96 forecast for peer Yophery Rodriguez, but all four peers have zero next-year MLB PA, so their rates are also unobserved. This is reduced numerical extrapolation, not established young-prospect batting accuracy or a statement about Salas's longer-term value.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Yophery Rodriguez | 0.38 | 1.44 | 0 | 0.7236 | unobserved |
| Juan Flores | 0.69 | 1.90 | 0 | 0.4502 | unobserved |
| Filippo Di Turi | 0.35 | 1.04 | 0 | 1.2240 | unobserved |
| Samuel Zavala | 0.46 | 3.08 | 0 | 0.7921 | unobserved |

## Jackson Holliday: 2023 to 2024

Player 702616, row 53595, fold 3; age 19.0, highest observed current level AAA. Selection: largest delivered gain.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 57 | 0 | 10 | 14 |
| 2022 | RK124 | 33 | 1 | 2 | 10 |
| 2023 | A | 67 | 2 | 13 | 14 |
| 2023 | AA | 164 | 3 | 34 | 19 |
| 2023 | AAA | 91 | 2 | 17 | 16 |
| 2023 | Aplus | 259 | 5 | 54 | 50 |

Draft 2022, pick 1, class HS SR. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.825719 | 439.765700 | 363.123004 | 0.620777 | 1.499954 |
| Standardized prospect | 0.936875 | 485.439565 | 454.796354 | 4.377755 | 4.726396 |
| Fixed-unit prospect | 0.531701 | 300.686257 | 159.875298 | 0.871145 | 0.727110 |
| Actual | 1 | Not a forecast | 208 | -3.309793 | -0.503411 |

Fixed expected PA = 0.531701381 × 300.686256941. Offense = expected PA × (rate/600 + origin replacement 0.003096076/PA). PA-only offense 0.660398; rate-only 1.651478.

participation: intercept -5.969067502, exact linear sum 0.126975850, linked output 0.531701381. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.6000000 | 0.0000000 | 1.0000000 | 1.0115535 |
| log_pool_AA | 0.9707789 | 0.0000000 | 1.0000000 | 0.6627903 |
| log_minor_pa_0 | 1.9183921 | 0.0000000 | 1.0000000 | 0.5814132 |
| log_pool_AAA | 0.6471032 | 0.0000000 | 1.0000000 | 0.4814648 |
| role_minor_0 | 4.6000000 | 4.0000000 | 1.0000000 | 0.4275455 |

conditional_pa: intercept 89.082517915, exact linear sum 300.686256941, linked output 300.686256941. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 2.5600000 | 0.0000000 | 1.0000000 | 50.1631755 |
| age_upper_interaction | -1.6000000 | 0.0000000 | 1.0000000 | 28.0250116 |
| age_centered | -1.6000000 | 0.0000000 | 1.0000000 | 24.9439814 |
| scout_rank_score_0 | 0.8900000 | 0.0000000 | 1.0000000 | 17.3586405 |
| scout_listed_0 | 1.0000000 | 0.0000000 | 1.0000000 | 16.6267916 |

rate: intercept -0.067811830, exact linear sum 0.871145155, linked output 0.871145155. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 2.5600000 | 0.0000000 | 1.0000000 | 0.9804075 |
| position_6 | 1.0000000 | 0.0000000 | 1.0000000 | -0.4711666 |
| age_centered | -1.6000000 | 0.0000000 | 1.0000000 | 0.4602532 |
| scout_listed_2 | -1.0000000 | 0.0000000 | 1.0000000 | -0.2342692 |
| pooled_A_BB | 0.1561618 | 0.0800000 | 0.1000000 | 0.2221087 |

Broad actual training-profile support: participation 9 distinct people, conditional_pa 3 distinct people, rate 3 distinct people.

Holliday's four-level 2023 season totals 581 PA and 12 HR; his earlier rookie K sample was only 2 strikeouts in 33 PA. That tiny sample no longer produces the standardized fit's +1.10 batting-rate term. Expected PA drops from the baseline's 363 to 160, closer to 208 actual, and rate falls from the standardized +4.38 to +0.87. Actual rate was -3.31; a high-ranked young prospect can still struggle in his first season. This is the largest delivered-value gain, but offense remains +0.73 versus -0.50 actual. Merrill's forecast falls to 55 PA versus 593 actual, so indiscriminately shrinking this age/profile would harm another genuine star. Only nine readiness-profile and three conditional-profile people support the fitted comparison. The gain is removal of overconfidence, not a discovered universal rule that young elite prospects should receive little opportunity.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Jett Williams | 9.91 | 22.35 | 0 | 0.2027 | unobserved |
| Robert Hassell III | 67.30 | 106.45 | 0 | -0.0957 | unobserved |
| Max Muncy | 26.65 | 39.25 | 0 | -0.0797 | unobserved |
| Jackson Merrill | 144.31 | 55.14 | 593 | -0.5731 | 1.4836 |

## Julio Rodríguez: 2021 to 2022

Player 677594, row 44122, fold 1; age 20.0, highest observed current level AA. Selection: largest delivered harm.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | A | 295 | 10 | 66 | 19 |
| 2019 | Aplus | 72 | 2 | 10 | 5 |
| 2021 | AA | 206 | 7 | 37 | 28 |
| 2021 | Aplus | 134 | 6 | 29 | 14 |

Draft None, pick None, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.802416 | 279.240940 | 224.067370 | 0.754077 | 0.984059 |
| Standardized prospect | 0.747709 | 284.436851 | 212.676056 | 1.899678 | 1.340100 |
| Fixed-unit prospect | 0.277010 | 224.739771 | 62.255104 | 1.310120 | 0.331106 |
| Actual | 1 | Not a forecast | 560 | 2.338056 | 3.937787 |

Fixed expected PA = 0.277009732 × 224.739771175. Offense = expected PA × (rate/600 + origin replacement 0.003135003/PA). PA-only offense 0.273412; rate-only 1.191710.

participation: intercept -5.818005723, exact linear sum -0.959343121, linked output 0.277009732. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| on_40man | 1.0000000 | 0.0000000 | 1.0000000 | 1.0973264 |
| log_pool_AA | 1.1184149 | 0.0000000 | 1.0000000 | 0.7595653 |
| age_upper_interaction | -1.4000000 | 0.0000000 | 1.0000000 | 0.7330974 |
| log_minor_pa_0 | 1.4816045 | 0.0000000 | 1.0000000 | 0.2984196 |
| role_minor_0 | 4.5238095 | 4.0000000 | 1.0000000 | 0.2894219 |

conditional_pa: intercept 93.515891019, exact linear sum 224.739771175, linked output 224.739771175. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.9600000 | 0.0000000 | 1.0000000 | 48.5013010 |
| age_upper_interaction | -1.4000000 | 0.0000000 | 1.0000000 | 24.1977876 |
| log_minor_pa_2 | 1.5411591 | 0.0000000 | 1.0000000 | -20.3715477 |
| age_centered | -1.4000000 | 0.0000000 | 1.0000000 | 19.3154570 |
| scout_listed_0 | 1.0000000 | 0.0000000 | 1.0000000 | 15.0457444 |

rate: intercept -0.156286508, exact linear sum 1.310119550, linked output 1.310119550. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.9600000 | 0.0000000 | 1.0000000 | 0.7657859 |
| log_minor_pa_2 | 1.5411591 | 0.0000000 | 1.0000000 | -0.6382844 |
| age_centered | -1.4000000 | 0.0000000 | 1.0000000 | 0.4261515 |
| log_minor_pa_0 | 1.4816045 | 0.0000000 | 1.0000000 | 0.2738079 |
| pooled_AA_BABIP | 0.3739130 | 0.3000000 | 0.1000000 | 0.2678537 |

Broad actual training-profile support: participation 534 distinct people, conditional_pa 122 distinct people, rate 122 distinct people.

Julio Rodriguez's A/High-A history in 2019 and strong High-A/AA history in 2021 are recorded; 2020 is explicitly a canceled minor season, not a poor season. His 40-man status adds +1.10 to the arrival logit, AA exposure +0.76, and age-by-upper-level +0.73. Nevertheless the heavily shrunken logistic model gives only 28% arrival versus the baseline's 80%, conditional PA 225, and expected PA 62 versus 560 actual. Rate improves from +0.75 to +1.31 versus +2.34, but that cannot rescue the workload collapse: offense falls from +0.98 to +0.33 versus +3.94 actual. The model did not simply lack his performance or roster evidence. Valera, Nunez, Guzman and Castillo did not arrive; broad matched support of 534/122 is not a guarantee of matched elite talent. This largest delivered-value harm exposes the price of over-shrinking readily available readiness evidence.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| George Valera | 24.53 | 4.43 | 0 | 0.0852 | unobserved |
| Malcom Nuñez | 2.51 | 3.40 | 0 | -0.0585 | unobserved |
| Jose Guzman | 0.31 | 1.40 | 0 | 0.3299 | unobserved |
| Moisés Castillo | 0.33 | 1.27 | 0 | 0.0760 | unobserved |

## Adam Engel: 2016 to 2017

Player 641553, row 25002, fold 1; age 24.0, highest observed current level AAA. Selection: false high.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 341 | 6 | 86 | 28 |
| 2014 | Aplus | 100 | 0 | 21 | 6 |
| 2014 | RK121 | 38 | 1 | 6 | 3 |
| 2015 | Aplus | 608 | 7 | 132 | 62 |
| 2016 | AA | 357 | 4 | 70 | 39 |
| 2016 | AAA | 161 | 3 | 50 | 10 |
| 2016 | Aplus | 64 | 0 | 11 | 7 |

Draft 2013, pick 573, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.664253 | 132.974669 | 88.328879 | -0.307779 | 0.227458 |
| Standardized prospect | 0.543509 | 51.384669 | 27.928015 | -0.632679 | 0.056795 |
| Fixed-unit prospect | 0.478216 | 90.718679 | 43.383099 | -0.021571 | 0.132411 |
| Actual | 1 | Not a forecast | 336 | -4.475590 | -1.468731 |

Fixed expected PA = 0.478215721 × 90.718679488. Offense = expected PA × (rate/600 + origin replacement 0.003088092/PA). PA-only offense 0.111717; rate-only 0.269592.

participation: intercept -5.790080966, exact linear sum -0.087192314, linked output 0.478215721. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 1.5195132 | 0.0000000 | 1.0000000 | 0.9057648 |
| log_minor_pa_0 | 1.9198595 | 0.0000000 | 1.0000000 | 0.8524065 |
| on_40man | 1.0000000 | 0.0000000 | 1.0000000 | 0.8013954 |
| log_pool_AAA | 0.9593502 | 0.0000000 | 1.0000000 | 0.5029902 |
| log_pool_Aplus | 1.9606580 | 0.0000000 | 1.0000000 | 0.4535939 |

conditional_pa: intercept 74.676397551, exact linear sum 90.718679488, linked output 90.718679488. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_1 | 1.9572739 | 0.0000000 | 1.0000000 | -21.1164317 |
| log_minor_pa_2 | 1.7561323 | 0.0000000 | 1.0000000 | -17.4206458 |
| log_pool_AA | 1.5195132 | 0.0000000 | 1.0000000 | 13.6908679 |
| log_minor_pa_0 | 1.9198595 | 0.0000000 | 1.0000000 | 12.2549432 |
| log_pool_Aplus | 1.9606580 | 0.0000000 | 1.0000000 | -7.7864771 |

rate: intercept -0.112069051, exact linear sum -0.021571013, linked output -0.021571013. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_2 | 1.7561323 | 0.0000000 | 1.0000000 | -0.5488465 |
| log_minor_pa_1 | 1.9572739 | 0.0000000 | 1.0000000 | -0.4697106 |
| log_minor_pa_0 | 1.9198595 | 0.0000000 | 1.0000000 | 0.3810852 |
| log_pool_Aplus | 1.9606580 | 0.0000000 | 1.0000000 | 0.2558568 |
| log_pool_AA | 1.5195132 | 0.0000000 | 1.0000000 | -0.1594010 |

Broad actual training-profile support: participation 564 distinct people, conditional_pa 120 distinct people, rate 120 distinct people.

Engel's extensive A/High-A/AA/AAA history and 40-man status are known. In 2016 he hit only seven HR in 582 minor PA; the prior year's seven HR in 608 PA also indicate limited power. The fixed model expects 43 PA versus 336 actual and an almost average -0.02 batting wins/600 versus -4.48 actual. It reduces the positive delivered-offense forecast from +0.23 to +0.13, but it remains false-high because low opportunity disguises a severely optimistic rate. A center fielder's ability to earn a roster place is not equivalent to his hitting ability; this test does not include his defense in offense. Brugman's 71 versus 162 PA and less extreme rate are a useful contrasting peer. McBroom, Jones and Garlick did not arrive. The missing mechanism is not a fabricated source gap: the available low-power/contact profile was insufficiently translated to MLB hitting.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Jaycob Brugman | 114.45 | 70.66 | 162 | -0.6954 | -0.5046 |
| Ryan McBroom | 3.30 | 4.93 | 0 | -0.6967 | unobserved |
| Hunter Jones | 2.86 | 8.58 | 0 | -0.6350 | unobserved |
| Kyle Garlick | 6.95 | 7.67 | 0 | 0.2408 | unobserved |

## José Azócar: 2021 to 2022

Player 640492, row 42694, fold 4; age 25.0, highest observed current level AAA. Selection: ordinary active prospect.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 538 | 10 | 132 | 20 |
| 2021 | AA | 343 | 9 | 71 | 35 |
| 2021 | AAA | 201 | 0 | 45 | 6 |

Draft None, pick None, class unknown. Source pooling retains the inherited neutral 100-opportunity prior.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.126439 | 100.739873 | 12.737471 | -1.047503 | 0.017694 |
| Standardized prospect | 0.047303 | 97.886825 | 4.630350 | -0.470069 | 0.010889 |
| Fixed-unit prospect | 0.070195 | 82.279681 | 5.775606 | -0.632821 | 0.012015 |
| Actual | 1 | Not a forecast | 216 | -1.844412 | 0.013172 |

Fixed expected PA = 0.070194804 × 82.279681256. Offense = expected PA × (rate/600 + origin replacement 0.003135003/PA). PA-only offense 0.008023; rate-only 0.026498.

participation: intercept -5.929149860, exact linear sum -2.583700804, linked output 0.070194804. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 2.0357509 | 0.0000000 | 1.0000000 | 1.3895212 |
| log_pool_AAA | 1.1019401 | 0.0000000 | 1.0000000 | 0.7364263 |
| log_minor_pa_2 | 1.8531681 | 0.0000000 | 1.0000000 | 0.3319029 |
| log_minor_pa_0 | 1.8625285 | 0.0000000 | 1.0000000 | 0.2777477 |
| highest_AAA | 1.0000000 | 0.0000000 | 1.0000000 | 0.2156840 |

conditional_pa: intercept 114.014074059, exact linear sum 82.279681256, linked output 82.279681256. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 2.0357509 | 0.0000000 | 1.0000000 | 22.1325822 |
| log_minor_pa_2 | 1.8531681 | 0.0000000 | 1.0000000 | -21.7980360 |
| scout_listed_0 | -1.0000000 | 0.0000000 | 1.0000000 | -17.8334008 |
| scout_rank_score_0 | -1.0000000 | 0.0000000 | 1.0000000 | -17.4783075 |
| log_minor_pa_0 | 1.8625285 | 0.0000000 | 1.0000000 | -11.8862194 |

rate: intercept 0.214687122, exact linear sum -0.632820710, linked output -0.632820710. Contribution = coefficient × (input minus fixed reference)/fixed scale.

| Feature | Origin input | Fixed reference | Fixed scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_2 | 1.8531681 | 0.0000000 | 1.0000000 | -0.7757966 |
| position_8 | 1.0000000 | 0.0000000 | 1.0000000 | -0.2269639 |
| log_minor_pa_0 | 1.8625285 | 0.0000000 | 1.0000000 | 0.2154906 |
| scout_rank_score_0 | -1.0000000 | 0.0000000 | 1.0000000 | -0.1521579 |
| log_games_minor_2 | 0.8285518 | 0.0000000 | 1.0000000 | -0.1458071 |

Broad actual training-profile support: participation 349 distinct people, conditional_pa 38 distinct people, rate 38 distinct people.

Azocar's 2019 AA and 2021 AA/AAA PA, K, BB and HR counts are real. The model knows his exposure, and marks canceled 2020 separately. Unknown ranking fields and their availability flags remain separate but correlated raw terms; a negative unknown-rank coefficient is not evidence that an unranked player lacks talent. Expected PA is only 6 versus 216, while rate -0.63 is substantially too high versus -1.84 actual. Offense +0.012 happens to match +0.013 actual because the workload and rate errors offset. That is not a successful playing-time or talent forecast. Stefanic similarly receives only five PA versus 69; Casey and Beltre did not arrive. Larsen's one actual PA gives an extremely noisy rate and is not a meaningful major-league skill benchmark. This ordinary product case illustrates why total contribution alone is insufficient.

| Origin-selected peer | Baseline PA | Fixed PA | Actual PA | Fixed rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Michael Stefanic | 15.87 | 5.33 | 69 | -0.5621 | -3.8550 |
| Donovan Casey | 43.60 | 11.48 | 0 | -1.1633 | unobserved |
| Michael Beltre | 1.17 | 1.04 | 0 | -0.5056 | unobserved |
| Jack Larsen | 11.74 | 1.40 | 1 | -0.4265 | -15.6294 |

## Decision

Do not adopt the full fixed-unit model. Never-debut PA MSE worsens +107.718 (nominal interval +67.114 to +153.027), offense MSE +.000999 (+.000286 to +.001784). Conditional rate MSE changes +.021800 (-.167961 to +.216508), statistically uncertain and much less bad than the standardized +1.226. Public established-player forecasts do not change.

Upper-never PA falls from 73,593 to 64,274 versus 92,891 actual. Lower-never PA rises from 7,652 to 11,915 versus 5,194. Holliday improves, but Alonso and Julio Rodriguez lose useful opportunity signal. Neither closeness of a product for Azocar nor fixing one extreme validates the joint forecast.

The head-specific results justify one bounded, explicitly post-result assembly check: standardized prospect opportunity with fixed-unit prospect hitting, against both complete models and standardized-PA/baseline-rate. No new fits or weight search. Review that combined forecast before any selection; none of these development comparisons can certify long-term prospect value or resolve the established-player availability deficit.

