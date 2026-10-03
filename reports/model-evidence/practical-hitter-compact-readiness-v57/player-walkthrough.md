# Compact readiness: eight actual player reviews

The compact model removes 92 sparse production-rate inputs and fits two readiness heads, not a new hitting head. All 70 saved heads replay. All original columns, established forecasts and hitting rates are exact. Do not adopt this forecast: better totals and clearer terms do not offset slightly worse individual errors.

| Scope | Rows | Baseline PA RMSE | Prior detailed PA RMSE | Compact PA RMSE | Baseline offense RMSE | Compact offense RMSE |
|---|---:|---:|---:|---:|---:|---:|
| all | 30506 | 60.6856 | 60.6128 | 60.7842 | 0.453826 | 0.453938 |
| never_debut | 24199 | 27.7450 | 27.5465 | 28.0219 | 0.154072 | 0.154510 |
| upper_never_debut | 5454 | 56.2422 | 55.7920 | 56.7141 | 0.317069 | 0.317419 |
| lower_never_debut | 17852 | 7.8283 | 7.9229 | 7.9399 | 0.042824 | 0.042997 |

Conditional PA is clipped on 2,322 of 24,199 never-debut forecasts (9.6%). This active-only linear model extrapolates negative conditional workload to some non-ready profiles. Those rows remain in all scores. A [1,800] bound ensures physical output, not calibrated conditional use; it is another reason not to certify this architecture.

Source pooling retains three-year 1/.8/.6 recency and the inherited neutral 100-opportunity prior. Only AA/AAA K, UBB and HR production rates enter readiness; all levels retain exposure. No new park/opponent correction or hitting fit is introduced. Offense uses custom common-origin event weights plus replacement, not official wOBA, full WAR or career value. Future-participant rate is unobserved when next PA is zero.

## Nick Kurtz: 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0, highest observed current AA; draft 2024, pick 4, class 4YR JR. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.017252 | 115.972916 | 2.000789 | -0.063223 | 0.006040 |
| shared | 0.107175 | 215.583223 | 23.105123 | -0.063223 | 0.069750 |
| Actual | 1 | Not a forecast | 489 | 5.289192 | 5.838406 |

Expected PA = 0.107174960 × 215.583222779; offense = PA × (unchanged rate/600 + origin replacement 0.003124161/PA).

participation: intercept -5.643157513, exact linear sum -2.119927999, linked output 0.107174960. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0510712 | 0.0935731 | 1.8739754 |
| age_upper_interaction | -1.2000000 | -0.1011796 | 0.2830291 | 0.7919050 |
| draft_rank | 0.8176145 | 0.1120240 | 0.1591967 | 0.7809330 |
| draft_upper_interaction | 0.8176145 | 0.0354635 | 0.1079865 | 0.4367465 |
| position_3 | 1.0000000 | 0.1095966 | 0.3123863 | -0.3631528 |

conditional_pa: intercept 114.213074949, exact linear sum 215.583222779, linked output 215.583222779. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0791099 | 0.1097164 | 63.4160559 |
| age_upper_interaction | -1.2000000 | -0.5871166 | 0.4596140 | 17.4588043 |
| reorganized | 1.0000000 | 0.2995910 | 0.4580789 | -15.8591904 |
| draft_rank | 0.8176145 | 0.2752046 | 0.2350621 | 15.3457819 |
| draft_elapsed | 0.0000000 | 0.2550102 | 0.2146487 | 14.8013015 |

Broad actual profile support: participation 4 people, conditional_pa 0 people.

Kurtz has only 35 A and 15 AA PA, but the recent fourth overall college pick is known. In the compact fit that recent-draft term adds +1.87 logit units and +63 conditional PA; arrival is 10.7%, conditional PA 216, expected PA 23 versus 489. This is higher than the corrected two-PA baseline but not a usable estimate of his actual fast entry. Hitting is deliberately unchanged at -0.06 versus +5.29 actual, so delivered offense remains just +0.07 versus +5.84. The four broad classifier-profile people and zero conditional participants do not support precision. Moore and Smith also exceed their low forecasts; Montgomery and Williams do not arrive. A draft signal is useful but cannot make this sparse training cohort decisive.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Benny Montgomery | 5.51 | 0 | -0.2032 | unobserved |
| Christian Moore | 51.18 | 184 | -0.0304 | -1.0849 |
| Cam Smith | 21.07 | 493 | -0.2546 | -0.4969 |
| Jett Williams | 31.98 | 0 | -0.1153 | unobserved |

## Wyatt Langford: 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0, highest observed current AAA; draft 2023, pick 4, class 4YR JR. Selection: fixed diagnostic, largest delivered gain.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.201829 | 213.555553 | 43.101733 | 0.688029 | 0.182872 |
| shared | 0.591715 | 357.767393 | 211.696442 | 0.688029 | 0.898184 |
| Actual | 1 | Not a forecast | 557 | 0.076953 | 1.795953 |

Expected PA = 0.591715305 × 357.767392552; offense = PA × (unchanged rate/600 + origin replacement 0.003096076/PA).

participation: intercept -5.627110301, exact linear sum 0.371060904, linked output 0.591715305. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0503537 | 0.0913017 | 1.8425923 |
| draft_rank | 0.8176145 | 0.1110490 | 0.1565050 | 0.9682008 |
| age_upper_interaction | -1.2000000 | -0.0978331 | 0.2782947 | 0.8126423 |
| role_minor_0 | 4.4444444 | 3.8439700 | 0.3965272 | 0.6004913 |
| pooled_AA_HR | 0.0454545 | 0.0287150 | 0.0050428 | 0.5324406 |

conditional_pa: intercept 116.547378890, exact linear sum 357.767392552, linked output 357.767392552. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0778613 | 0.1019973 | 79.4713743 |
| draft_rank | 0.8176145 | 0.2749697 | 0.2323657 | 22.5444036 |
| pooled_AA_HR | 0.0454545 | 0.0271245 | 0.0110940 | 21.9713086 |
| draft_elapsed | 0.0000000 | 0.2507479 | 0.2104621 | 16.0928784 |
| log_pool_AA | 0.4317824 | 1.3143776 | 0.6660530 | -12.0421948 |

Broad actual profile support: participation 31 people, conditional_pa 2 people.

Langford's college class, fourth pick and progression through 14 rookie, 106 High-A, 54 AA and 26 AAA PA are recorded. Removing rookie rate terms removes the old -42 conditional PA attributed to three rookie doubles. Recent draft now adds +79 conditional PA, AA power +22. Arrival 59% × conditional PA 358 produces 212 expected PA versus 557, an improvement over 43 and the largest delivered gain. Baseline hitting +0.69 versus +0.08 remains optimistic; offense +0.90 versus +1.80 improves mainly through opportunity. Crews gets 104 versus 132 PA while Shaw, Veen and Wilken do not arrive. Conditional broad support is only two people. The mechanism is clearer, but the forecast still misses a full-season starting job.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Zac Veen | 66.16 | 0 | -0.1593 | unobserved |
| Dylan Crews | 103.87 | 132 | 0.0662 | -1.7462 |
| Matt Shaw | 104.61 | 0 | -0.2230 | unobserved |
| Brock Wilken | 29.49 | 0 | 0.2414 | unobserved |

## Cody Bellinger: 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0, highest observed current AAA; draft 2013, pick 124, class unknown. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.110193 | 139.597326 | 15.382612 | 0.084596 | 0.049672 |
| shared | 0.243059 | 145.163870 | 35.283333 | 0.084596 | 0.113933 |
| Actual | 1 | Not a forecast | 548 | 2.928011 | 4.366524 |

Expected PA = 0.243058641 × 145.163869900; offense = PA × (unchanged rate/600 + origin replacement 0.003088092/PA).

participation: intercept -5.572731461, exact linear sum -1.135983048, linked output 0.243058641. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.4000000 | -0.0988243 | 0.2819260 | 0.8902561 |
| log_pool_AA | 1.7316555 | 0.2566104 | 0.5969893 | 0.6587729 |
| draft_upper_interaction | 0.3658277 | 0.0345365 | 0.1055474 | 0.4726860 |
| pooled_AA_HR | 0.0460177 | 0.0284778 | 0.0051979 | 0.4383046 |
| log_games_minor_0 | 0.7747272 | 0.4339032 | 0.2289401 | 0.2782472 |

conditional_pa: intercept 110.109677977, exact linear sum 145.163869900, linked output 145.163869900. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| log_pool_RK128 | 0.8746351 | 0.0467720 | 0.2113774 | -20.7666279 |
| role_minor_2 | 4.4754098 | 4.1399720 | 0.2447861 | 17.8810671 |
| age_squared | 1.9600000 | 0.7985302 | 0.6203461 | 15.7905710 |
| pooled_AAA_HR | 0.0535714 | 0.0276489 | 0.0076014 | 15.1145107 |
| pooled_AA_HR | 0.0460177 | 0.0243828 | 0.0108945 | 12.1494642 |

Broad actual profile support: participation 561 people, conditional_pa 122 people.

Bellinger's strong 544-PA/30-HR High-A and 465-PA/23-HR AA seasons, plus 12 AAA PA with three HR, are known. The removed old complex HR term no longer subtracts 36 conditional PA; older complex exposure still subtracts 21, which is an association with route/time rather than a causal penalty for having played there. Young age at upper levels raises arrival, but 24% × 145 gives only 35 expected PA versus 548. Unchanged batting +0.08 versus +2.93 and offense +0.11 versus +4.37 remain severe false lows. Verdugo receives 32 versus 25 PA; Kiner-Falefa, Ward and Westbrook do not arrive. Broad 561/122 support does not ensure the elite breakout's role is properly represented.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Alex Verdugo | 31.82 | 25 | 0.0249 | -3.6858 |
| Isiah Kiner-Falefa | 8.80 | 0 | -0.1348 | unobserved |
| Drew Ward | 4.27 | 0 | -0.0188 | unobserved |
| Jamie Westbrook | 14.95 | 0 | -0.4163 | unobserved |

## Pete Alonso: 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0, highest observed current AAA; draft 2016, pick 64, class unknown. Selection: fixed diagnostic, false low.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.692850 | 183.403275 | 127.070997 | 0.286158 | 0.451826 |
| shared | 0.665062 | 214.308206 | 142.528274 | 0.286158 | 0.506788 |
| Actual | 1 | Not a forecast | 693 | 3.864560 | 6.597153 |

Expected PA = 0.665062139 × 214.308205706; offense = PA × (unchanged rate/600 + origin replacement 0.003078768/PA).

participation: intercept -5.590916884, exact linear sum 0.685935452, linked output 0.665062139. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| log_pool_AAA | 1.3887912 | 0.0837693 | 0.3371582 | 1.3172516 |
| pooled_AAA_HR | 0.0598504 | 0.0294356 | 0.0030967 | 0.5942894 |
| log_pool_AA | 1.4124493 | 0.2539867 | 0.5907142 | 0.5899111 |
| pooled_AA_HR | 0.0477350 | 0.0284331 | 0.0051714 | 0.5724119 |
| age_upper_interaction | -0.8000000 | -0.1010469 | 0.2801271 | 0.4860308 |

conditional_pa: intercept 109.863830324, exact linear sum 214.308205706, linked output 214.308205706. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| pooled_AAA_HR | 0.0598504 | 0.0277197 | 0.0077869 | 51.7098662 |
| pooled_AA_HR | 0.0477350 | 0.0245100 | 0.0109472 | 27.6354478 |
| highest_AAA | 1.0000000 | 0.4337568 | 0.4955924 | 9.1278085 |
| pooled_AAA_K | 0.2518703 | 0.2183310 | 0.0314046 | -8.7722443 |
| highest_AA | 0.0000000 | 0.4519056 | 0.4976816 | 6.4807904 |

Broad actual profile support: participation 805 people, conditional_pa 165 people.

Alonso has 36 HR in 574 AA/AAA PA. AAA exposure raises arrival and AAA power adds +52 conditional PA; AA power adds +28, not an arbitrary unseen rookie statistic. Yet arrival 67% × conditional PA 214 yields only 143 expected PA versus 693. His unchanged +0.29 hitting rate versus +3.86 is also too low. Offense +0.51 versus +6.60 is the largest false-low of this compact experiment. Solak and Mercado get materially more actual time than projected, Neuse only 61 and Brigman zero. This cleaner fit still does not adequately convert an established high-level power prospect into a starting-role expectation.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Nick Solak | 42.52 | 135 | -0.5706 | 3.3497 |
| Óscar Mercado | 88.33 | 482 | -0.7653 | 0.5131 |
| Bryson Brigman | 16.64 | 0 | -0.4679 | unobserved |
| Sheldon Neuse | 6.87 | 61 | 0.4166 | -2.2791 |

## Ethan Salas: 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0, highest observed current Aplus; draft None, pick None, class unknown. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.025632 | 281.841619 | 7.224140 | -0.511711 | 0.016408 |
| shared | 0.016207 | 163.426694 | 2.648668 | -0.511711 | 0.006016 |
| Actual | 0 | Not a forecast | 0 | unobserved | 0.000000 |

Expected PA = 0.016207072 × 163.426693895; offense = PA × (unchanged rate/600 + origin replacement 0.003124161/PA).

participation: intercept -5.720113480, exact linear sum -4.105967726, linked output 0.016207072. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| position_2 | 1.0000000 | 0.1744089 | 0.3794607 | 0.4728731 |
| role_minor_0 | 4.2066116 | 3.8481549 | 0.3958647 | 0.4072090 |
| highest_Aplus | 1.0000000 | 0.1155430 | 0.3196761 | 0.3811281 |
| scout_listed_0 | 1.0000000 | -0.1623996 | 0.3909537 | 0.2286334 |
| log_pool_Aplus | 1.7894234 | 0.3249237 | 0.5953610 | 0.2152320 |

conditional_pa: intercept 115.763397040, exact linear sum 163.426693895, linked output 163.426693895. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.9300000 | -0.1126022 | 0.4564796 | 61.5440658 |
| age_squared | 3.2400000 | 0.7430110 | 0.6148382 | 49.2963346 |
| log_pool_AA | 0.2342813 | 1.3421314 | 0.6611285 | -18.8666642 |
| age_centered | -1.8000000 | -0.7519442 | 0.4214154 | 16.1329340 |
| position_2 | 1.0000000 | 0.1475573 | 0.3546606 | -15.3924117 |

Broad actual profile support: participation 3838 people, conditional_pa 7 people.

Salas's 469 High-A PA with four HR, prior lower/upper stints, age eighteen, catcher position and strong rank are known. Ranking and youth increase conditional PA but limited high-level exposure reduces it. Arrival 1.6% × 163 conditional PA gives three expected PA versus none, reducing offense from +0.016 to +0.006. That is a reasonable next-year non-readiness direction. It does not validate the unchanged -0.51 conditional hitting estimate or his career potential: there is no actual next-year MLB rate and just seven broad conditional-profile people. All four origin-selected peers also do not arrive.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Yophery Rodriguez | 0.27 | 0 | -0.2985 | unobserved |
| Juan Flores | 0.89 | 0 | -0.5833 | unobserved |
| Filippo Di Turi | 0.25 | 0 | -0.2552 | unobserved |
| Samuel Zavala | 1.61 | 0 | -0.3246 | unobserved |

## Julio Rodríguez: 2021 to 2022

Player 677594, row 44122, fold 1; age 20.0, highest observed current AA; draft None, pick None, class unknown. Selection: largest delivered harm.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | A | 295 | 10 | 66 | 19 |
| 2019 | Aplus | 72 | 2 | 10 | 5 |
| 2021 | AA | 206 | 7 | 37 | 28 |
| 2021 | Aplus | 134 | 6 | 29 | 14 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.802416 | 279.240940 | 224.067370 | 0.754077 | 0.984059 |
| shared | 0.543634 | 262.890025 | 142.915857 | 0.754077 | 0.627658 |
| Actual | 1 | Not a forecast | 560 | 2.338056 | 3.937787 |

Expected PA = 0.543633624 × 262.890025436; offense = PA × (unchanged rate/600 + origin replacement 0.003135003/PA).

participation: intercept -5.564809561, exact linear sum 0.174979592, linked output 0.543633624. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| on_40man | 1.0000000 | 0.0194866 | 0.1382275 | 2.2695762 |
| age_upper_interaction | -1.4000000 | -0.0907038 | 0.2672417 | 0.9872290 |
| role_minor_0 | 4.5238095 | 3.8575490 | 0.3933409 | 0.6197818 |
| log_pool_AA | 1.1184149 | 0.2436833 | 0.5754433 | 0.6035681 |
| highest_AA | 1.0000000 | 0.1009352 | 0.3012429 | 0.3530309 |

conditional_pa: intercept 111.878734337, exact linear sum 262.890025436, linked output 262.890025436. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.9600000 | -0.0372702 | 0.3784712 | 42.7028399 |
| age_squared | 1.9600000 | 0.7392758 | 0.6146064 | 29.3958607 |
| log_minor_pa_1 | 0.0000000 | 1.5861886 | 0.4264703 | 21.4326782 |
| draft_elapsed | 0.0000000 | 0.2459610 | 0.2067903 | 16.3839549 |
| age_upper_interaction | -1.4000000 | -0.5774373 | 0.4622738 | 16.3726153 |

Broad actual profile support: participation 534 people, conditional_pa 122 people.

Julio Rodriguez's 2019 A/High-A counts and 2021 High-A/AA counts are recorded, and canceled 2020 is explicit rather than treated as poor production. Forty-man status adds +2.27 to the arrival logit, young upper-level age +0.99, and AA exposure +0.60. Nevertheless the compact arrival probability falls from the baseline's 80% to 54%, conditional PA from 279 to 263, and expected PA from 224 to 143 versus 560. Unchanged hitting +0.75 versus +2.34 leaves offense falling +0.98 to +0.63 versus +3.94, the largest harm. Valera, Nunez, Guzman and Castillo do not arrive; they are broad peers, not identical talent. Available production, ranking and roster signals are present but the compact additive classifier fails to use them as effectively as the tree control.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| George Valera | 4.47 | 0 | 0.0834 | unobserved |
| Malcom Nuñez | 2.21 | 0 | -0.1193 | unobserved |
| Jose Guzman | 0.77 | 0 | -0.1215 | unobserved |
| Moisés Castillo | 0.66 | 0 | -0.8162 | unobserved |

## Jackson Holliday: 2023 to 2024

Player 702616, row 53595, fold 3; age 19.0, highest observed current AAA; draft 2022, pick 1, class HS SR. Selection: false high.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 57 | 0 | 10 | 14 |
| 2022 | RK124 | 33 | 1 | 2 | 10 |
| 2023 | A | 67 | 2 | 13 | 14 |
| 2023 | AA | 164 | 3 | 34 | 19 |
| 2023 | AAA | 91 | 2 | 17 | 16 |
| 2023 | Aplus | 259 | 5 | 54 | 50 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.825719 | 439.765700 | 363.123004 | 0.620777 | 1.499954 |
| shared | 0.836548 | 359.004295 | 300.324158 | 0.620777 | 1.240550 |
| Actual | 1 | Not a forecast | 208 | -3.309793 | -0.503411 |

Expected PA = 0.836547533 × 359.004295342; offense = PA × (unchanged rate/600 + origin replacement 0.003096076/PA).

participation: intercept -5.695124812, exact linear sum 1.632761119, linked output 0.836547533. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.6000000 | -0.0995387 | 0.2802331 | 1.2513961 |
| draft_rank | 1.0000000 | 0.1129834 | 0.1582807 | 1.2069461 |
| role_minor_0 | 4.6000000 | 3.8472018 | 0.3976847 | 0.8349379 |
| recent_draft_rank | 0.5000000 | 0.0514570 | 0.0927465 | 0.8278359 |
| draft_upper_interaction | 1.0000000 | 0.0350593 | 0.1066739 | 0.7692201 |

conditional_pa: intercept 116.144552129, exact linear sum 359.004295342, linked output 359.004295342. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.5000000 | 0.0760889 | 0.0944272 | 58.4219834 |
| scout_rank_score_0 | 0.8900000 | -0.1283551 | 0.4707811 | 49.3079332 |
| age_squared | 2.5600000 | 0.7506754 | 0.6141797 | 31.4656279 |
| pooled_AAA_BB | 0.1256545 | 0.0821719 | 0.0156376 | 17.4212405 |
| age_upper_interaction | -1.6000000 | -0.5960784 | 0.4637466 | 17.3265099 |

Broad actual profile support: participation 9 people, conditional_pa 3 people.

Holliday's first pick, rankings and 581-PA/12-HR four-level season are recorded. Removing his old 2 K in 33 rookie PA from this workload fit removes the prior +43 conditional PA term. Conditional PA falls from 440 to 359, while appearance remains 84%; expected PA 300 is closer to 208 than the baseline's 363. But unchanged hitting +0.62 versus -3.31 is still optimistic, and offense +1.24 versus -0.50 remains the largest false-high. Merrill still receives 106 versus 593 PA, whereas the Williams/Hassell/Muncy peers do not arrive. Cleaner youth/pedigree terms do not establish that this forecast or that pedigree-driven high certainty is well calibrated.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Jett Williams | 31.83 | 0 | 0.1713 | unobserved |
| Robert Hassell III | 98.93 | 0 | -0.1264 | unobserved |
| Max Muncy | 42.99 | 0 | -0.2835 | unobserved |
| Jackson Merrill | 106.21 | 593 | -0.3061 | 1.4836 |

## Derek Fisher: 2016 to 2017

Player 605233, row 24255, fold 2; age 22.0, highest observed current AAA; draft 2014, pick 37, class unknown. Selection: ordinary active prospect.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | Aminus | 172 | 2 | 35 | 15 |
| 2014 | RK124 | 4 | 0 | 0 | 1 |
| 2015 | A | 171 | 6 | 37 | 18 |
| 2015 | Aplus | 398 | 16 | 95 | 47 |
| 2016 | AA | 448 | 16 | 128 | 67 |
| 2016 | AAA | 118 | 5 | 26 | 9 |

| Forecast | Appearance | Conditional PA | Expected PA | Batting wins/600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| repaired | 0.426771 | 135.102774 | 57.657926 | 0.102486 | 0.187902 |
| shared | 0.378529 | 150.582286 | 56.999799 | 0.102486 | 0.185757 |
| Actual | 1 | Not a forecast | 166 | -1.191052 | 0.183099 |

Expected PA = 0.378529245 × 150.582286007; offense = PA × (unchanged rate/600 + origin replacement 0.003088092/PA).

participation: intercept -5.522686900, exact linear sum -0.495795519, linked output 0.378529245. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 1.7011051 | 0.2505367 | 0.5883062 | 0.7390241 |
| log_pool_AAA | 0.7793249 | 0.0890504 | 0.3478874 | 0.5419913 |
| age_upper_interaction | -1.0000000 | -0.0948702 | 0.2799721 | 0.5298177 |
| draft_upper_interaction | 0.5249356 | 0.0328561 | 0.1025940 | 0.5283126 |
| pooled_AA_K | 0.2755474 | 0.2253757 | 0.0205387 | -0.3902135 |

conditional_pa: intercept 112.129297056, exact linear sum 150.582286007, linked output 150.582286007. Contributions are coefficient × (input minus actual training mean)/training scale; they describe the fitted model, not causal effects.

| Feature | Origin input | Training mean | Training scale | Contribution |
|---|---:|---:|---:|---:|
| highest_AAA | 1.0000000 | 0.4086022 | 0.4915755 | 13.2144757 |
| pooled_AA_K | 0.2755474 | 0.1975577 | 0.0401689 | -12.6767664 |
| pooled_AA_BB | 0.1368613 | 0.0840083 | 0.0238550 | 10.9485014 |
| pooled_AA_HR | 0.0346715 | 0.0249584 | 0.0111230 | 10.0393471 |
| age_upper_interaction | -1.0000000 | -0.6338710 | 0.4626165 | 9.0035592 |

Broad actual profile support: participation 528 people, conditional_pa 112 people.

Fisher has 448 AA PA with 16 HR, 128 K and 67 walks, followed by 118 AAA PA with five HR, 26 K and nine walks. AA/AAA exposure and draft context raise appearance; AA K lowers conditional PA, while walks and power raise it. The mechanics are more intelligible than old rookie HBP/tri​ples. Expected PA remains 57 versus 166 and unchanged hitting +0.10 versus -1.19 is too high. Offense +0.186 versus +0.183 is close only because errors offset. Shaw, Stewart and Kingery do not arrive; Stevenson gets 66 PA with very poor measured hitting. The ordinary-case product is not a successful joint forecast or proof every prospect peer deserved regular time.

| Origin-selected peer | Expected PA | Actual PA | Forecast rate | Actual rate |
|---|---:|---:|---:|---:|
| Chris Shaw | 15.75 | 0 | -0.0736 | unobserved |
| Christin Stewart | 26.21 | 0 | 0.1556 | unobserved |
| Scott Kingery | 16.20 | 0 | -0.3352 | unobserved |
| Andrew Stevenson | 25.67 | 66 | -0.1946 | -5.5121 |

## Origin and probability checks

| Information year → MLB target | Actual prospect PA | Baseline PA | Compact PA | Actual arrivals | Baseline expected arrivals | Compact expected arrivals |
|---|---:|---:|---:|---:|---:|---:|
| 2016 → 2017 | 10735 | 10897 | 11167 | 108 | 97.3 | 97.0 |
| 2017 → 2018 | 11854 | 9440 | 10326 | 95 | 90.2 | 93.7 |
| 2018 → 2019 | 15836 | 9752 | 11385 | 108 | 90.0 | 94.7 |
| 2021 → 2022 | 18944 | 10463 | 6326 | 158 | 79.9 | 45.2 |
| 2022 → 2023 | 14072 | 14520 | 16660 | 106 | 110.8 | 109.4 |
| 2023 → 2024 | 11697 | 14758 | 22091 | 107 | 115.5 | 143.3 |
| 2024 → 2025 | 15190 | 11985 | 13587 | 105 | 99.6 | 113.2 |

The 2021-origin return-to-normal cohort worsens from 10,463 to 6,326 prospect PA versus 18,944 actual, with expected arrivals 80 to 45 versus 158. The 2023-origin cohort rises from 14,758 to 22,091 versus only 11,697 actual. These are major opposite calibration errors, not a harmless one-player miss. Canceled-year flags are present, but their presence does not prove the model handles career interruption/reorganization correctly. The exact source of the vintage/role associations remains unestablished; do not call this a uniquely identified COVID effect. Probability losses also worsen overall: Brier .020003 to .020559 and log loss .071834 to .074951. A closer seven-year PA total masks these errors.

## Batch decision

Never-debut offense MSE worsens +.0001351, nominal interval [-.0003200,+.0005834]; no meaningful individual gain. Upper-never PA total improves from 73,593 to 83,447 versus 92,891 actual. Lower-never remains 7,652 versus 5,194. Never-debut total offense 217.53 is close to 214.80 actual but the model misallocates individual forecasts. All public current-MLB forecasts remain unchanged (PA MAE 106.87 versus Steamer 92.08).

Removing fragile rookie rates makes several model explanations more baseball-reasonable, but loses useful classifier signal for Julio Rodriguez and does not resolve stars' starting-role expectations. This negative does not prove lower-league production is useless; it tests this reduced next-year readiness construction with fixed penalties.

Close V54–57 without an automatic forecast promotion. Keep numeric source repair and corrected baseline talent/readiness as the defensible research anchor. Preserve the detailed PA-only variant as an uncertain alternative, not a new winning model. Next material work is timely MLB availability and role-to-workload uncertainty, with matched public cutoff qualifications. Do not spend another batch sweeping feature scales or penalties on these same rare prospect cases.

