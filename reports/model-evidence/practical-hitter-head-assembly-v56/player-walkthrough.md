# Separate prospect head assembly: eight actual player reviews

No new fits or weight search. Assembly uses standardized V54 opportunity and fixed-unit V55 hitting, with corrected V53 forecasts exact for established players. This post-result selection is development evidence, not confirmation.

| Scope | Rows | Baseline offense RMSE | Baseline-rate/new-PA RMSE | Combined RMSE |
|---|---:|---:|---:|---:|
| all | 30506 | 0.453826 | 0.453792 | 0.453791 |
| never_debut | 24199 | 0.154072 | 0.153978 | 0.153978 |
| upper_never_debut | 5454 | 0.317069 | 0.316168 | 0.315974 |
| lower_never_debut | 17852 | 0.042824 | 0.043012 | 0.043310 |
| public_broad_unchanged | 2627 | 1.061363 | 1.061363 | 1.061363 |

Rate is custom fixed-event origin-centered batting wins/600, not official wOBA or park-neutral latent talent. Future-participant rate errors use actual PA within each year and equal years. All non-arrivals stay in contribution scoring. Offense includes replacement, not full WAR. Highest observed level can be a cameo; it is not a season-ending role. No new environmental adjustment.

## Nick Kurtz: 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0, highest current observed AA; draft 2024, pick 4, class 4YR JR. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.017252 | 115.972916 | 2.000789 | -0.063223 | 0.006040 |
| standardized | 0.125809 | 223.707331 | 28.144307 | 0.745337 | 0.122889 |
| fixed | 0.028607 | 200.678842 | 5.740764 | 0.298603 | 0.020792 |
| assembled | 0.125809 | 223.707331 | 28.144307 | 0.298603 | 0.101934 |
| Actual | 1 | Not a forecast | 489 | 5.289192 | 5.838406 |

Expected PA = 0.125808605 × 223.707331314. Offense = PA × (rate/600 + origin replacement 0.003124161/PA).

participation: standardized; intercept -5.853996576, exact raw sum -1.938537598, linked output 0.125808605. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0510712 | 0.0935731 | 1.2339007 |
| draft_rank | 0.8176145 | 0.1120240 | 0.1591967 | 0.9765853 |
| age_upper_interaction | -1.2000000 | -0.1011796 | 0.2830291 | 0.6682068 |
| pooled_A_HR | 0.0518519 | 0.0272753 | 0.0063331 | 0.5775338 |
| draft_upper_interaction | 0.8176145 | 0.0354635 | 0.1079865 | 0.4464205 |

conditional_pa: standardized; intercept 114.230021555, exact raw sum 223.707331314, linked output 223.707331314. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0791099 | 0.1097164 | 45.7152309 |
| pooled_A_BB | 0.1333333 | 0.0835232 | 0.0169135 | 21.1984697 |
| draft_rank | 0.8176145 | 0.2752046 | 0.2350621 | 15.2211893 |
| age_upper_interaction | -1.2000000 | -0.5871166 | 0.4596140 | 14.9238290 |
| reorganized | 1.0000000 | 0.2995910 | 0.4580789 | -14.2885574 |

rate: fixed baseball units; intercept -0.253963650, exact raw sum 0.298602550, linked output 0.298602550. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 0.5575893 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.3307997 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 0.2773931 |
| position_3 | 1.0000000 | 0.0000000 | 1.0000000 | 0.1573337 |
| scout_list_available_2 | 1.0000000 | 0.0000000 | 1.0000000 | -0.1252315 |

Broad actual training support: participation 4 people, conditional_pa 0 people, rate 0 people.

Kurtz's 35 A and 15 AA PA, fourth overall college pick and recent draft date drive arrival upward: recent-pick context adds +1.23 logit units and +46 conditional PA. The combined forecast is 12.6% appearance × 224 conditional PA = 28 expected PA, versus 489 actual. Fixed-unit hitting is +0.30 versus +5.29 actual, producing only +0.10 offense wins versus +5.84. This is directionally less implausible than the two-PA baseline, not adequate readiness or upside. Four broad classifier-profile people and no conditional-profile participants limit confidence. Moore and Smith also outperform their workload forecasts; Montgomery and Williams do not arrive, so the whole peer class cannot simply be assigned regular MLB jobs.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Benny Montgomery | 4.88 | 0 | -0.5396 | unobserved |
| Christian Moore | 69.54 | 184 | 0.4566 | -1.0849 |
| Cam Smith | 30.98 | 493 | 0.2011 | -0.4969 |
| Jett Williams | 30.75 | 0 | 0.0945 | unobserved |

## Wyatt Langford: 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0, highest current observed AAA; draft 2023, pick 4, class 4YR JR. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.201829 | 213.555553 | 43.101733 | 0.688029 | 0.182872 |
| standardized | 0.729966 | 293.808130 | 214.469904 | 1.014924 | 1.026800 |
| fixed | 0.128688 | 247.482041 | 31.847917 | 0.850008 | 0.143722 |
| assembled | 0.729966 | 293.808130 | 214.469904 | 0.850008 | 0.967850 |
| Actual | 1 | Not a forecast | 557 | 0.076953 | 1.795953 |

Expected PA = 0.729965862 × 293.808129541. Offense = PA × (rate/600 + origin replacement 0.003096076/PA).

participation: standardized; intercept -5.844689722, exact raw sum 0.994449379, linked output 0.729965862. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0503537 | 0.0913017 | 1.2366967 |
| draft_rank | 0.8176145 | 0.1110490 | 0.1565050 | 1.0825023 |
| age_upper_interaction | -1.2000000 | -0.0978331 | 0.2782947 | 0.7136863 |
| pooled_AA_HR | 0.0454545 | 0.0287150 | 0.0050428 | 0.5428198 |
| reorganized | 1.0000000 | 0.1660536 | 0.3721287 | 0.4939324 |

conditional_pa: standardized; intercept 116.613726199, exact raw sum 293.808129541, linked output 293.808129541. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0778613 | 0.1019973 | 60.1817794 |
| pooled_RK121_2B | 0.0701754 | 0.0500632 | 0.0023949 | -42.1321463 |
| draft_rank | 0.8176145 | 0.2749697 | 0.2323657 | 24.8317184 |
| pooled_AA_HR | 0.0454545 | 0.0271245 | 0.0110940 | 24.7333119 |
| draft_elapsed | 0.0000000 | 0.2507479 | 0.2104621 | 16.8311025 |

rate: fixed baseball units; intercept 0.038245237, exact raw sum 0.850007924, linked output 0.850007924. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.4400000 | 0.0000000 | 1.0000000 | 0.6679617 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.4070875 |
| age_centered | -1.2000000 | 0.0000000 | 1.0000000 | 0.2988227 |
| position_7 | 1.0000000 | 0.0000000 | 1.0000000 | 0.2683413 |
| scout_listed_2 | -1.0000000 | 0.0000000 | 1.0000000 | -0.2676070 |

Broad actual training support: participation 31 people, conditional_pa 2 people, rate 2 people.

Langford's 54 AA, 26 AAA, 106 High-A and 14 rookie PA, college class and fourth pick are present. Recent-draft context adds +1.24 to arrival log odds and +60 conditional PA. However the three doubles in 14 rookie PA still contribute a nonsensical -42 conditional PA after rare-column standardization. Expected PA increases from 43 to 214 versus 557 actual; fixed-unit hitting +0.85 is too high versus +0.08. Delivered offense rises from +0.18 to +0.97 versus +1.80, primarily by repairing opportunity. Crews improves to 96 versus 132 PA, while Shaw, Veen and Wilken do not arrive. Useful readiness signal and an ill-founded rookie-rate term coexist; the combined result does not certify this conditional head.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Zac Veen | 35.46 | 0 | 0.0406 | unobserved |
| Dylan Crews | 95.81 | 132 | 0.1606 | -1.7462 |
| Matt Shaw | 123.30 | 0 | -0.1032 | unobserved |
| Brock Wilken | 28.85 | 0 | 0.1647 | unobserved |

## Cody Bellinger: 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0, highest current observed AAA; draft 2013, pick 124, class unknown. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.110193 | 139.597326 | 15.382612 | 0.084596 | 0.049672 |
| standardized | 0.282332 | 120.934913 | 34.143757 | -0.011420 | 0.104789 |
| fixed | 0.184025 | 138.129309 | 25.419277 | 0.036832 | 0.080057 |
| assembled | 0.282332 | 120.934913 | 34.143757 | 0.036832 | 0.107535 |
| Actual | 1 | Not a forecast | 548 | 2.928011 | 4.366524 |

Expected PA = 0.282331681 × 120.934912942. Offense = PA × (rate/600 + origin replacement 0.003088092/PA).

participation: standardized; intercept -5.680738549, exact raw sum -0.932924957, linked output 0.282331681. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.4000000 | -0.0988243 | 0.2819260 | 0.8314827 |
| log_pool_AA | 1.7316555 | 0.2566104 | 0.5969893 | 0.5949108 |
| draft_upper_interaction | 0.3658277 | 0.0345365 | 0.1055474 | 0.4564108 |
| pooled_Aplus_HR | 0.0504484 | 0.0277861 | 0.0062778 | 0.3615128 |
| pooled_AA_HR | 0.0460177 | 0.0284778 | 0.0051979 | 0.3245854 |

conditional_pa: standardized; intercept 110.140685521, exact raw sum 120.934912942, linked output 120.934912942. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| pooled_RK128_HR | 0.0200167 | 0.0298360 | 0.0023349 | -36.2154496 |
| age_squared | 1.9600000 | 0.7985302 | 0.6203461 | 25.2207761 |
| pooled_AAA_HR | 0.0535714 | 0.0276489 | 0.0076014 | 20.3616516 |
| role_minor_2 | 4.4754098 | 4.1399720 | 0.2447861 | 17.0460541 |
| log_pool_Aplus | 1.6774703 | 1.0904456 | 0.6562966 | -11.4342373 |

rate: fixed baseball units; intercept 0.389702579, exact raw sum 0.036832321, linked output 0.036832321. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 1.9600000 | 0.0000000 | 1.0000000 | 0.4522979 |
| log_minor_pa_1 | 1.8625285 | 0.0000000 | 1.0000000 | -0.4175959 |
| age_centered | -1.4000000 | 0.0000000 | 1.0000000 | 0.2777448 |
| log_pool_AA | 1.7316555 | 0.0000000 | 1.0000000 | -0.2152721 |
| log_minor_pa_2 | 1.2029723 | 0.0000000 | 1.0000000 | -0.1981107 |

Broad actual training support: participation 561 people, conditional_pa 122 people, rate 122 people.

Bellinger's 30 High-A HR in 2015, 23 AA HR in 2016 and three AAA HR in only 12 PA are known. Age at upper levels and substantial AA exposure raise arrival, but older complex HR still subtracts 36 conditional PA and the brief AAA HR sample adds 20. The resulting 28% × 121 = 34 expected PA is far below 548. Fixed hitting +0.04 remains far below +2.93. Offense only increases +0.05 to +0.11 versus +4.37 actual. Verdugo has 25 actual PA and other peers none. The combined system preserves a major false-low rather than solving it through a harmless numerical substitution.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Alex Verdugo | 12.48 | 25 | -0.5260 | -3.6858 |
| Isiah Kiner-Falefa | 1.50 | 0 | -0.4683 | unobserved |
| Drew Ward | 1.96 | 0 | -0.3315 | unobserved |
| Jamie Westbrook | 15.83 | 0 | -0.7855 | unobserved |

## Pete Alonso: 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0, highest current observed AAA; draft 2016, pick 64, class unknown. Selection: fixed diagnostic, false low.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.692850 | 183.403275 | 127.070997 | 0.286158 | 0.451826 |
| standardized | 0.670824 | 206.524898 | 138.541939 | 2.517438 | 1.007823 |
| fixed | 0.258407 | 145.421836 | 37.577972 | 0.733238 | 0.161616 |
| assembled | 0.670824 | 206.524898 | 138.541939 | 0.733238 | 0.595845 |
| Actual | 1 | Not a forecast | 693 | 3.864560 | 6.597153 |

Expected PA = 0.670824393 × 206.524897913. Offense = PA × (rate/600 + origin replacement 0.003078768/PA).

participation: standardized; intercept -5.729388461, exact raw sum 0.711916026, linked output 0.670824393. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| log_pool_AAA | 1.3887912 | 0.0837693 | 0.3371582 | 1.1772063 |
| pooled_AAA_HR | 0.0598504 | 0.0294356 | 0.0030967 | 0.6353824 |
| log_pool_AA | 1.4124493 | 0.2539867 | 0.5907142 | 0.5443341 |
| pooled_AA_HR | 0.0477350 | 0.0284331 | 0.0051714 | 0.5245083 |
| age_upper_interaction | -0.8000000 | -0.1010469 | 0.2801271 | 0.4404004 |

conditional_pa: standardized; intercept 109.810506207, exact raw sum 206.524897913, linked output 206.524897913. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| pooled_AAA_HR | 0.0598504 | 0.0277197 | 0.0077869 | 51.5607193 |
| pooled_AA_HR | 0.0477350 | 0.0245100 | 0.0109472 | 25.3092424 |
| pooled_Aminus_HR | 0.0345224 | 0.0290362 | 0.0046372 | 10.6859377 |
| pooled_Aplus_3B | 0.0013270 | 0.0072151 | 0.0046836 | -9.9553063 |
| pooled_AAA_K | 0.2518703 | 0.2183310 | 0.0314046 | -9.8916717 |

rate: fixed baseball units; intercept -0.187041274, exact raw sum 0.733237757, linked output 0.733237757. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_1 | 1.5953390 | 0.0000000 | 1.0000000 | -0.3399502 |
| log_minor_pa_2 | 0.8020016 | 0.0000000 | 1.0000000 | -0.3191623 |
| position_3 | 1.0000000 | 0.0000000 | 1.0000000 | 0.2737553 |
| log_minor_pa_0 | 1.9080599 | 0.0000000 | 1.0000000 | 0.2562041 |
| age_centered | -0.8000000 | 0.0000000 | 1.0000000 | 0.2181954 |

Broad actual training support: participation 805 people, conditional_pa 165 people, rate 165 people.

Alonso's 36 HR in 574 AA/AAA PA are real substantial evidence. AAA log exposure and power increase both participation and conditional PA, but those estimates still produce only 139 expected PA versus 693. Fixed-unit rate +0.73 versus +3.86 improves on the baseline +0.29 without capturing the breakout. Delivered offense +0.60 versus +6.60 is the largest false-low here. Solak and Mercado also exceed their workload forecasts, while Neuse gets limited time and Brigman none. Neither missing data nor a universal low-level penalty explains these misses; the model needs a better readiness/role-to-workload translation.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Nick Solak | 44.73 | 135 | -0.6278 | 3.3497 |
| Óscar Mercado | 86.30 | 482 | -1.0116 | 0.5131 |
| Bryson Brigman | 15.67 | 0 | -0.8712 | unobserved |
| Sheldon Neuse | 17.85 | 61 | 0.4064 | -2.2791 |

## Ethan Salas: 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0, highest current observed Aplus; draft None, pick None, class unknown. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.025632 | 281.841619 | 7.224140 | -0.511711 | 0.016408 |
| standardized | 0.011711 | 173.073507 | 2.026800 | 0.790657 | 0.009003 |
| fixed | 0.022907 | 181.868698 | 4.166103 | 1.364994 | 0.022493 |
| assembled | 0.011711 | 173.073507 | 2.026800 | 1.364994 | 0.010943 |
| Actual | 0 | Not a forecast | 0 | unobserved | 0.000000 |

Expected PA = 0.011710631 × 173.073506543. Offense = PA × (rate/600 + origin replacement 0.003124161/PA).

participation: standardized; intercept -5.918148651, exact raw sum -4.435478463, linked output 0.011710631. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| position_2 | 1.0000000 | 0.1744089 | 0.3794607 | 0.5640450 |
| highest_Aplus | 1.0000000 | 0.1155430 | 0.3196761 | 0.3631592 |
| role_minor_0 | 4.2066116 | 3.8481549 | 0.3958647 | 0.2955324 |
| reorganized | 1.0000000 | 0.2305676 | 0.4211962 | 0.2729890 |
| pooled_Aplus_HR | 0.0116940 | 0.0280833 | 0.0061139 | -0.2349237 |

conditional_pa: standardized; intercept 115.862740422, exact raw sum 173.073506543, linked output 173.073506543. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.9300000 | -0.1126022 | 0.4564796 | 53.9666652 |
| age_squared | 3.2400000 | 0.7430110 | 0.6148382 | 49.8732920 |
| age_centered | -1.8000000 | -0.7519442 | 0.4214154 | 20.3951548 |
| draft_elapsed | 0.0000000 | 0.2572283 | 0.2146552 | 13.5272067 |
| log_pool_Aplus | 1.7894234 | 0.9569076 | 0.6537686 | -12.3125157 |

rate: fixed baseball units; intercept -0.192516484, exact raw sum 1.364993986, linked output 1.364993986. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 3.2400000 | 0.0000000 | 1.0000000 | 1.3779442 |
| age_centered | -1.8000000 | 0.0000000 | 1.0000000 | 0.5436815 |
| position_2 | 1.0000000 | 0.0000000 | 1.0000000 | -0.3295097 |
| log_minor_pa_1 | 1.3609766 | 0.0000000 | 1.0000000 | -0.2897673 |
| reorganized | 1.0000000 | 0.0000000 | 1.0000000 | -0.2586527 |

Broad actual training support: participation 3838 people, conditional_pa 7 people, rate 7 people.

Salas has 469 High-A PA and four HR in 2024 after earlier A/High-A/AA exposure. His ranking supplies +54 conditional PA and youth-related terms more, but his 1.17% appearance probability yields only two expected PA versus none actual. The +1.36 hitting rate is unobserved, not validated by that non-arrival; the fixed model's age-square term dominates it. All four peers also lack next-year MLB PA. Seven broad conditional-profile training people are not sufficient to treat this rate as a present MLB grade. The combined candidate reduces contribution, which is sensible for next-year readiness but says little about longer-term prospect value.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Yophery Rodriguez | 1.54 | 0 | 0.7236 | unobserved |
| Juan Flores | 0.16 | 0 | 0.4502 | unobserved |
| Filippo Di Turi | 0.24 | 0 | 1.2240 | unobserved |
| Samuel Zavala | 1.21 | 0 | 0.7921 | unobserved |

## Ronald Acuña Jr.: 2017 to 2018

Player 660670, row 30192, fold 3; age 19.0, highest current observed AAA; draft None, pick None, class unknown. Selection: largest delivered gain.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2015 | RK120 | 237 | 4 | 42 | 28 |
| 2016 | A | 171 | 4 | 28 | 18 |
| 2016 | RK124 | 8 | 0 | 1 | 1 |
| 2017 | AA | 243 | 9 | 56 | 18 |
| 2017 | AAA | 243 | 9 | 48 | 17 |
| 2017 | Aplus | 126 | 3 | 40 | 8 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.199282 | 139.356631 | 27.771258 | 0.163747 | 0.093008 |
| standardized | 0.530952 | 277.593970 | 147.389121 | -0.699436 | 0.281579 |
| fixed | 0.263741 | 201.306196 | 53.092633 | 0.273203 | 0.187497 |
| assembled | 0.530952 | 277.593970 | 147.389121 | 0.273203 | 0.520507 |
| Actual | 1 | Not a forecast | 487 | 3.260543 | 4.144572 |

Expected PA = 0.530952172 × 277.593969749. Offense = PA × (rate/600 + origin replacement 0.003076176/PA).

participation: standardized; intercept -5.765983406, exact raw sum 0.123967205, linked output 0.530952172. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.6000000 | -0.1004791 | 0.2825397 | 0.9682731 |
| log_pool_AAA | 1.2325603 | 0.0864275 | 0.3407374 | 0.9371258 |
| pooled_AAA_BABIP | 0.3646617 | 0.3001475 | 0.0065625 | 0.5193307 |
| pooled_AA_BABIP | 0.3590734 | 0.3003638 | 0.0101567 | 0.4324192 |
| log_pool_AA | 1.2325603 | 0.2566116 | 0.5960214 | 0.4108702 |

conditional_pa: standardized; intercept 108.257836122, exact raw sum 277.593969749, linked output 277.593969749. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| pooled_RK120_3B | 0.0119736 | 0.0051139 | 0.0011225 | -60.5948843 |
| pooled_RK120_HBP | 0.0239472 | 0.0102358 | 0.0020338 | 58.1657853 |
| pooled_RK120_BB | 0.1023947 | 0.0802121 | 0.0037136 | -51.7606635 |
| age_squared | 2.5600000 | 0.7874946 | 0.6161297 | 34.9211945 |
| pooled_Aplus_3B | 0.0243363 | 0.0072311 | 0.0045335 | 26.1375554 |

rate: fixed baseball units; intercept 0.099272845, exact raw sum 0.273202898, linked output 0.273202898. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 2.5600000 | 0.0000000 | 1.0000000 | 0.5464310 |
| age_centered | -1.6000000 | 0.0000000 | 1.0000000 | 0.3463368 |
| log_minor_pa_2 | 1.2149127 | 0.0000000 | 1.0000000 | -0.3324822 |
| pooled_AA_BABIP | 0.3590734 | 0.3000000 | 0.1000000 | 0.1376629 |
| log_minor_pa_1 | 1.0260416 | 0.0000000 | 1.0000000 | -0.1351447 |

Broad actual training support: participation 15 people, conditional_pa 3 people, rate 3 people.

Acuna's 2017 AA and AAA seasons each contain 243 PA and nine HR; he also has 126 High-A PA and earlier rookie/A history. Young age at upper levels and AAA exposure lift arrival to 53%, conditional PA to 278, and expected PA from 28 to 147 versus 487. Fixed hitting +0.27 versus +3.26 remains very low, so offense +0.52 versus +4.14 only partially improves the missed star. The conditional head still assigns -61 PA to old rookie triples, +58 to rookie HBP and -52 to rookie walks: offsetting rare standardized terms, not a coherent baseball explanation. Adames's 293 versus 323 PA is comparatively reasonable; Urias has limited time and Tatis/Diaz none. Three broad conditional-profile training players qualify this gain. Identifying a star better while relying on these terms is not grounds for unconditional adoption.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Fernando Tatis Jr. | 3.34 | 0 | 0.6759 | unobserved |
| Luis Urías | 46.48 | 53 | -0.7431 | -2.5644 |
| Yusniel Díaz | 13.06 | 0 | 0.5514 | unobserved |
| Willy Adames | 292.95 | 323 | 0.4242 | 0.1864 |

## Jackson Holliday: 2023 to 2024

Player 702616, row 53595, fold 3; age 19.0, highest current observed AAA; draft 2022, pick 1, class HS SR. Selection: largest delivered harm, false high.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 57 | 0 | 10 | 14 |
| 2022 | RK124 | 33 | 1 | 2 | 10 |
| 2023 | A | 67 | 2 | 13 | 14 |
| 2023 | AA | 164 | 3 | 34 | 19 |
| 2023 | AAA | 91 | 2 | 17 | 16 |
| 2023 | Aplus | 259 | 5 | 54 | 50 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.825719 | 439.765700 | 363.123004 | 0.620777 | 1.499954 |
| standardized | 0.936875 | 485.439565 | 454.796354 | 4.377755 | 4.726396 |
| fixed | 0.531701 | 300.686257 | 159.875298 | 0.871145 | 0.727110 |
| assembled | 0.936875 | 485.439565 | 454.796354 | 0.871145 | 2.068407 |
| Actual | 1 | Not a forecast | 208 | -3.309793 | -0.503411 |

Expected PA = 0.936875333 × 485.439564782. Offense = PA × (rate/600 + origin replacement 0.003096076/PA).

participation: standardized; intercept -5.898864977, exact raw sum 2.697438617, linked output 0.936875333. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| draft_rank | 1.0000000 | 0.1129834 | 0.1582807 | 1.3939233 |
| age_upper_interaction | -1.6000000 | -0.0995387 | 0.2802331 | 1.1349548 |
| draft_upper_interaction | 1.0000000 | 0.0350593 | 0.1066739 | 0.7844646 |
| role_minor_0 | 4.6000000 | 3.8472018 | 0.3976847 | 0.6149073 |
| pooled_AA_BABIP | 0.3640777 | 0.3004726 | 0.0102553 | 0.5334971 |

conditional_pa: standardized; intercept 116.212370367, exact raw sum 485.439564782, linked output 485.439564782. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.5000000 | 0.0760889 | 0.0944272 | 48.9741471 |
| scout_rank_score_0 | 0.8900000 | -0.1283551 | 0.4707811 | 43.7582055 |
| pooled_RK124_K | 0.1946203 | 0.2282978 | 0.0085009 | 42.6905219 |
| age_squared | 2.5600000 | 0.7506754 | 0.6141797 | 35.1252951 |
| pooled_AA_BABIP | 0.3640777 | 0.3105969 | 0.0228006 | 30.2511727 |

rate: fixed baseball units; intercept -0.067811830, exact raw sum 0.871145155, linked output 0.871145155. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| age_squared | 2.5600000 | 0.0000000 | 1.0000000 | 0.9804075 |
| position_6 | 1.0000000 | 0.0000000 | 1.0000000 | -0.4711666 |
| age_centered | -1.6000000 | 0.0000000 | 1.0000000 | 0.4602532 |
| scout_listed_2 | -1.0000000 | 0.0000000 | 1.0000000 | -0.2342692 |
| pooled_A_BB | 0.1561618 | 0.0800000 | 0.1000000 | 0.2221087 |

Broad actual training support: participation 9 people, conditional_pa 3 people, rate 3 people.

Holliday's 581 PA and 12 HR across four levels in 2023, prior first overall high-school pick and ranking legitimately indicate a high-quality young prospect. The standardized conditional head still adds +43 PA from his old 2 K in 33 rookie PA; the rate head no longer turns that into an extreme batting-rate gain. The assembly predicts 94% appearance × 485 conditional PA = 455 expected PA versus 208, and +0.87 hitting versus -3.31 actual. Offense +2.07 versus -0.50 is the largest harm/false-high relative to the corrected baseline +1.50. Only nine broad readiness and three conditional-profile people support the fit. Merrill's 103 versus 593 PA remains too low, whereas Hassell, Williams and Muncy do not arrive. High pedigree raises probability and upside, but should not imply near-certainty of a successful first full season.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Jett Williams | 37.59 | 0 | 0.2027 | unobserved |
| Robert Hassell III | 107.33 | 0 | -0.0957 | unobserved |
| Max Muncy | 39.96 | 0 | -0.0797 | unobserved |
| Jackson Merrill | 102.94 | 593 | -0.5731 | 1.4836 |

## Bradley Zimmer: 2016 to 2017

Player 605548, row 24303, fold 0; age 23.0, highest current observed AAA; draft 2014, pick 21, class unknown. Selection: ordinary active prospect.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 13 | 2 | 3 | 2 |
| 2014 | Aminus | 197 | 4 | 30 | 19 |
| 2015 | AA | 214 | 6 | 54 | 18 |
| 2015 | Aplus | 335 | 10 | 77 | 36 |
| 2016 | AA | 407 | 14 | 115 | 55 |
| 2016 | AAA | 150 | 1 | 56 | 21 |

| Construction | Arrival | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.584205 | 255.772465 | 149.423680 | 0.131010 | 0.494061 |
| standardized | 0.613924 | 252.387914 | 154.947064 | 1.096836 | 0.761743 |
| fixed | 0.307785 | 174.191693 | 53.613579 | 0.450308 | 0.205801 |
| assembled | 0.613924 | 252.387914 | 154.947064 | 0.450308 | 0.594781 |
| Actual | 1 | Not a forecast | 332 | -0.772375 | 0.597866 |

Expected PA = 0.613924263 × 252.387914227. Offense = PA × (rate/600 + origin replacement 0.003088092/PA).

participation: standardized; intercept -5.612322740, exact raw sum 0.463838009, linked output 0.613924263. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.7500000 | 0.0034439 | 0.0468966 | 1.0374831 |
| draft_upper_interaction | 0.5994525 | 0.0346431 | 0.1052138 | 0.7004492 |
| log_pool_AA | 1.9142720 | 0.2574723 | 0.5984913 | 0.6070926 |
| log_pool_AAA | 0.9162907 | 0.0889548 | 0.3456909 | 0.5804283 |
| pooled_AA_K | 0.2671778 | 0.2253868 | 0.0208732 | -0.4306238 |

conditional_pa: standardized; intercept 111.193563213, exact raw sum 252.387914227, linked output 252.387914227. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.7500000 | 0.0625000 | 0.1984299 | 87.9916013 |
| pooled_Aminus_HBP | 0.0293309 | 0.0104417 | 0.0025174 | 40.2319599 |
| pooled_AA_K | 0.2671778 | 0.1953148 | 0.0393987 | -16.5759545 |
| pooled_Aplus_BABIP | 0.3542945 | 0.3156215 | 0.0228451 | 15.4391250 |
| pooled_AAA_K | 0.3160000 | 0.2165101 | 0.0324586 | -13.5728766 |

rate: fixed baseball units; intercept 0.640992536, exact raw sum 0.450308339, linked output 0.450308339. Contributions are coefficient × transformed origin input, not causal effects.

| Feature | Origin input | Reference | Scale | Contribution |
|---|---:|---:|---:|---:|
| log_minor_pa_1 | 1.8702625 | 0.0000000 | 1.0000000 | -0.4534701 |
| log_minor_pa_2 | 1.1314021 | 0.0000000 | 1.0000000 | -0.3431255 |
| log_pool_Aplus | 1.3029128 | 0.0000000 | 1.0000000 | -0.2345595 |
| scout_list_available_1 | 1.0000000 | 0.0000000 | 1.0000000 | 0.1469063 |
| age_centered | -0.8000000 | 0.0000000 | 1.0000000 | 0.1461966 |

Broad actual training support: participation 557 people, conditional_pa 122 people, rate 122 people.

Zimmer has 407 AA PA with 14 HR, 115 K and 55 walks, followed by 150 AAA PA with one HR, 56 K and 21 walks. Rankings and AA/AAA exposure lift readiness; AAA strikeouts reduce conditional PA, but old short-season HBP supplies an implausibly large +40 PA. The assembly predicts 155 PA versus 332, and +0.45 batting wins/600 versus -0.77. Offense +0.595 matches +0.598 actual almost exactly because two major errors offset. This ordinary case is not a success of either component. Chapman receives only 31 versus 326 PA, Gillaspie none, Ervin 53 versus 64 and Smith 20 versus 29. A close product and a few plausible peers cannot rescue a badly supported hitting/workload mechanism.

| Origin-selected peer | Expected PA | Actual PA | Rate | Actual rate |
|---|---:|---:|---:|---:|
| Casey Gillaspie | 36.96 | 0 | -0.2651 | unobserved |
| Matt Chapman | 30.77 | 326 | -0.2010 | 0.9573 |
| Phillip Ervin | 53.44 | 64 | -0.9046 | 0.5012 |
| Dwight Smith Jr. | 20.11 | 29 | -0.5762 | 3.1435 |

## Decision

Do not replace baseline hitting with the fixed-unit prospect head. Never-debut offense MSE changes -.0000291 against corrected baseline, nominal interval [-.0007089,+.0006280]; against new-PA/baseline-rate it changes +.000000061 [-.0003551,+.0003669]. This is effectively no gain. Upper-minor contribution improves modestly, lower-minor contribution worsens; sparse profiles remain.

The simpler PA-only construction remains a research alternative, not an automatic promotion. Exact player checks reveal rare rookie statistics still dominating conditional playing time, including Acuna's offsetting rookie triples/HBP/walk terms. Stop combining and scaling the same over-detailed readiness representation. A materially different compact readiness head must focus on role/exposure, pedigree, age and supported production, retaining talent as its own target. Established-player availability remains a separate practical shortfall.

