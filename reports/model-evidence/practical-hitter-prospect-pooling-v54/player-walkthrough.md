# Shared prospect models and actual player review

Seven complete source-to-fit reviews. The full shared candidate is not adopted: modest workload improvement is offset by worse hitting and overconfident rare-profile extrapolation. Its PA-only construction remains qualified research, not a proven delivered-value win. All established-player forecasts remain bit-exact.

Inputs use repaired three-year counts separately by fourteen leagues, draft context, rankings, age and role. Current highest observed level comes from current-year positive PA, even a cameo; it is not asserted to be the season-ending job. Log exposure and simple age/draft × upper-level interactions supplement that indicator. StandardScaler learns each head mean/scale from its actual chronological, held-player-excluded training subset. Logistic and Ridge penalties/settings are unchanged after results. No future public projection, player identity or protected season enters training.

| Scope | Rows | Baseline PA RMSE | Shared PA RMSE | Baseline rate RMSE | Shared rate RMSE | Baseline offense RMSE | Shared offense RMSE | PA only offense RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 30506 | 60.686 | 60.613 | 1.8782 | 1.9065 | 0.45383 | 0.45545 | 0.45379 |
| never_debut | 24199 | 27.745 | 27.547 | 2.6467 | 2.8690 | 0.15407 | 0.16007 | 0.15398 |
| upper_never_debut | 5454 | 56.242 | 55.792 | 2.6320 | 2.8647 | 0.31707 | 0.32781 | 0.31617 |
| lower_never_debut | 17852 | 7.828 | 7.923 | 3.1284 | 3.1859 | 0.04282 | 0.04364 | 0.04301 |
| public_broad_unchanged | 2627 | 138.488 | 138.488 | 1.7435 | 1.7435 | 1.06136 | 1.06136 | 1.06136 |

Rate scoring uses actual PA among future participants and equal target years. All non-arrivals remain in workload/contribution scoring. Rate is the custom fixed-event origin-centered wins/600, not official wOBA, park-neutral latent skill or current MLB-equivalent DSL ability. Offense includes replacement only. Four origin-selected peers use age/stage/exposure/draft rank without future outcomes; they do not establish identical health or talent. Sparse profile counts remain qualifications despite shared slopes.

## Nick Kurtz from 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0, highest current observed AA. Selection: fixed diagnostic, false low.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Draft 2024, pick 4, class 4YR JR. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.017252 | 115.972916 | 2.000789 | -0.063223 | 0.006040 |
| Shared prospect | 0.125809 | 223.707331 | 28.144307 | 0.745337 | 0.122889 |
| Actual | 1 | Not a forecast | 489 | 5.289192 | 5.838406 |

PA-only offense 0.084962, rate-only offense 0.008736. Shared expected PA is 0.125808605 × 223.707331314; offense adds origin replacement 0.003124161/PA to the rate/600.

participation: intercept -5.853996576, exact linear sum -1.938537598, linked output 0.125808605. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0510712 | 0.0935731 | 1.2339007 |
| draft_rank | 0.8176145 | 0.1120240 | 0.1591967 | 0.9765853 |
| age_upper_interaction | -1.2000000 | -0.1011796 | 0.2830291 | 0.6682068 |
| pooled_A_HR | 0.0518519 | 0.0272753 | 0.0063331 | 0.5775338 |
| draft_upper_interaction | 0.8176145 | 0.0354635 | 0.1079865 | 0.4464205 |

conditional_pa: intercept 114.230021555, exact linear sum 223.707331314, linked output 223.707331314. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0791099 | 0.1097164 | 45.7152309 |
| pooled_A_BB | 0.1333333 | 0.0835232 | 0.0169135 | 21.1984697 |
| draft_rank | 0.8176145 | 0.2752046 | 0.2350621 | 15.2211893 |
| age_upper_interaction | -1.2000000 | -0.5871166 | 0.4596140 | 14.9238290 |
| reorganized | 1.0000000 | 0.2995910 | 0.4580789 | -14.2885574 |

rate: intercept -1.114477673, exact linear sum 0.745336714, linked output 0.745336714. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| draft_rank_low_exposure | 0.5450763 | 0.0297221 | 0.0471174 | 1.2270425 |
| reorganized | 1.0000000 | 0.2995910 | 0.4580789 | -0.4688763 |
| pooled_A_BB | 0.1333333 | 0.0835232 | 0.0169135 | 0.4068614 |
| draft_upper_interaction | 0.8176145 | 0.2293573 | 0.2341147 | -0.3861585 |
| recent_draft_rank | 0.8176145 | 0.0791099 | 0.1097164 | -0.2690050 |

Broad actual training-profile support: participation 4 distinct people, conditional_pa 0 distinct people, rate 0 distinct people.

The known 50 PA, four HR, twelve walks, pick four and college-junior class now produce 12.6% arrival probability and 224 conditional PA, versus 1.7% and 116 in the repaired control. Smooth recent-draft rank and age-at-upper-level terms explain much of the increase; no later scouting report or future performance is inserted. The 28 expected PA versus 489 actual is less absurdly low but still a substantial miss. Exact thin draft-year profile support remains four people and zero conditional participants; shared slopes are a modeled extrapolation, not new training evidence. The rate rises from -.063 to +.745, largely from the thin-exposure pedigree term, which is nearly eleven standard deviations from conditional training mean. This fragile amplification must not be mistaken for validated pedigree reliability. Peers Moore and Smith gain opportunity with actual MLB PA, while Montgomery and Williams do not arrive. PA-only is directionally helpful here; the full candidate cannot be justified from Kurtz's famous outcome.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Benny Montgomery | 6.54 | 4.88 | 0 | -0.4322 | unobserved |
| Christian Moore | 8.23 | 69.54 | 184 | 0.8575 | -1.0849 |
| Cam Smith | 2.33 | 30.98 | 493 | -0.2989 | -0.4969 |
| Jett Williams | 74.66 | 30.75 | 0 | -0.4317 | unobserved |

## Wyatt Langford from 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0, highest current observed AAA. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

Draft 2023, pick 4, class 4YR JR. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.201829 | 213.555553 | 43.101733 | 0.688029 | 0.182872 |
| Shared prospect | 0.729966 | 293.808130 | 214.469904 | 1.014924 | 1.026800 |
| Actual | 1 | Not a forecast | 557 | 0.076953 | 1.795953 |

PA-only offense 0.909951, rate-only offense 0.206355. Shared expected PA is 0.729965862 × 293.808129541; offense adds origin replacement 0.003096076/PA to the rate/600.

participation: intercept -5.844689722, exact linear sum 0.994449379, linked output 0.729965862. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0503537 | 0.0913017 | 1.2366967 |
| draft_rank | 0.8176145 | 0.1110490 | 0.1565050 | 1.0825023 |
| age_upper_interaction | -1.2000000 | -0.0978331 | 0.2782947 | 0.7136863 |
| pooled_AA_HR | 0.0454545 | 0.0287150 | 0.0050428 | 0.5428198 |
| reorganized | 1.0000000 | 0.1660536 | 0.3721287 | 0.4939324 |

conditional_pa: intercept 116.613726199, exact linear sum 293.808129541, linked output 293.808129541. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.8176145 | 0.0778613 | 0.1019973 | 60.1817794 |
| pooled_RK121_2B | 0.0701754 | 0.0500632 | 0.0023949 | -42.1321463 |
| draft_rank | 0.8176145 | 0.2749697 | 0.2323657 | 24.8317184 |
| pooled_AA_HR | 0.0454545 | 0.0271245 | 0.0110940 | 24.7333119 |
| draft_elapsed | 0.0000000 | 0.2507479 | 0.2104621 | 16.8311025 |

rate: intercept -0.923153968, exact linear sum 1.014924374, linked output 1.014924374. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_RK121_2B | 0.0701754 | 0.0500632 | 0.0023949 | -0.7714739 |
| reorganized | 1.0000000 | 0.2297009 | 0.4206404 | -0.5450077 |
| pooled_RK121_HR | 0.0350877 | 0.0300038 | 0.0024810 | 0.4318663 |
| position_7 | 1.0000000 | 0.0758547 | 0.2647655 | 0.4065603 |
| scout_listed_2 | -1.0000000 | -0.2051282 | 0.4743590 | -0.3771477 |

Broad actual training-profile support: participation 31 distinct people, conditional_pa 2 distinct people, rate 2 distinct people.

The source already contained ten HR, 36 walks and 34 K across 200 professional PA up through AAA, plus fourth pick and college-junior pedigree. The smooth head raises appearance probability 20% to 73%, conditional PA 214 to 294, and expected PA 43 to 214 versus 557 actual. Recent-draft rank, upper-level age and AA power now share additive effects instead of depending on a sufficiently populated shallow-tree interaction leaf. This is a useful readiness correction but not a full-season expectation. Hitting rises .688 to 1.015 against .077 actual on shared-origin units, worsening conditional hitting even while delivered offense improves. One tiny complex doubles line subtracts 42 conditional PA and .77 batting wins/600 after rare-feature standardization; the sign/scale is a warning about representation, not an established baseball doubles penalty. Broad conditional support is two people. Crews gets 132 actual PA; Veen, Shaw and Wilken none, and Shaw's increased expectation illustrates a false-positive cost.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Zac Veen | 85.17 | 35.46 | 0 | -0.2920 | unobserved |
| Dylan Crews | 12.55 | 95.81 | 132 | -0.1693 | -1.7462 |
| Matt Shaw | 34.13 | 123.30 | 0 | -0.0539 | unobserved |
| Brock Wilken | 6.42 | 28.85 | 0 | -0.6797 | unobserved |

## Cody Bellinger from 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0, highest current observed AAA. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Draft 2013, pick 124, class unknown. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.110193 | 139.597326 | 15.382612 | 0.084596 | 0.049672 |
| Shared prospect | 0.282332 | 120.934913 | 34.143757 | -0.011420 | 0.104789 |
| Actual | 1 | Not a forecast | 548 | 2.928011 | 4.366524 |

PA-only offense 0.110253, rate-only offense 0.047210. Shared expected PA is 0.282331681 × 120.934912942; offense adds origin replacement 0.003088092/PA to the rate/600.

participation: intercept -5.680738549, exact linear sum -0.932924957, linked output 0.282331681. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_upper_interaction | -1.4000000 | -0.0988243 | 0.2819260 | 0.8314827 |
| log_pool_AA | 1.7316555 | 0.2566104 | 0.5969893 | 0.5949108 |
| draft_upper_interaction | 0.3658277 | 0.0345365 | 0.1055474 | 0.4564108 |
| pooled_Aplus_HR | 0.0504484 | 0.0277861 | 0.0062778 | 0.3615128 |
| pooled_AA_HR | 0.0460177 | 0.0284778 | 0.0051979 | 0.3245854 |

conditional_pa: intercept 110.140685521, exact linear sum 120.934912942, linked output 120.934912942. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_RK128_HR | 0.0200167 | 0.0298360 | 0.0023349 | -36.2154496 |
| age_squared | 1.9600000 | 0.7985302 | 0.6203461 | 25.2207761 |
| pooled_AAA_HR | 0.0535714 | 0.0276489 | 0.0076014 | 20.3616516 |
| role_minor_2 | 4.4754098 | 4.1399720 | 0.2447861 | 17.0460541 |
| log_pool_Aplus | 1.6774703 | 1.0904456 | 0.6562966 | -11.4342373 |

rate: intercept -0.879071116, exact linear sum -0.011420354, linked output -0.011420354. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_RK128_3B | 0.0170976 | 0.0052506 | 0.0016670 | 0.6483012 |
| pooled_AAA_HR | 0.0535714 | 0.0276489 | 0.0076014 | 0.4940511 |
| pooled_RK128_HR | 0.0200167 | 0.0298360 | 0.0023349 | -0.4525643 |
| pooled_RK128_BABIP | 0.3336585 | 0.3015921 | 0.0086016 | 0.4269747 |
| age_centered | -1.4000000 | -0.7926509 | 0.4125951 | 0.3034796 |

Broad actual training-profile support: participation 561 distinct people, conditional_pa 122 distinct people, rate 122 distinct people.

Bellinger has 23 AA HR in 465 PA, after 30 High-A HR, and a twelve-PA AAA cameo. Smooth arrival probability increases 11% to 28%, but conditional PA falls 140 to 121, so expected PA is only 34 versus 548 actual. Draft/upper-level and age/upper-level interactions reasonably recognize advanced youth. Old complex HR, however, subtracts 36 conditional PA while age squared and tiny AAA HR add 25 and 20; the rate is nearly zero because large opposing rare-level terms cancel. Standardizing rarely observed rookie-bucket rates gives them disproportionate influence. This is not a settled projection of current MLB-equivalent ability. Broad conditional support is 122 people; peers include three zero-PA players and Verdugo's 25 PA. Opportunity improves here, but conditional workload and power integration remain unresolved.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Alex Verdugo | 32.00 | 12.48 | 25 | -0.9320 | -3.6858 |
| Isiah Kiner-Falefa | 18.75 | 1.50 | 0 | 0.3848 | unobserved |
| Drew Ward | 1.95 | 1.96 | 0 | -0.8234 | unobserved |
| Jamie Westbrook | 4.21 | 15.83 | 0 | -0.6953 | unobserved |

## Pete Alonso from 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0, highest current observed AAA. Selection: fixed diagnostic, largest delivered gain.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Draft 2016, pick 64, class unknown. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.692850 | 183.403275 | 127.070997 | 0.286158 | 0.451826 |
| Shared prospect | 0.670824 | 206.524898 | 138.541939 | 2.517438 | 1.007823 |
| Actual | 1 | Not a forecast | 693 | 3.864560 | 6.597153 |

PA-only offense 0.492613, rate-only offense 0.924378. Shared expected PA is 0.670824393 × 206.524897913; offense adds origin replacement 0.003078768/PA to the rate/600.

participation: intercept -5.729388461, exact linear sum 0.711916026, linked output 0.670824393. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AAA | 1.3887912 | 0.0837693 | 0.3371582 | 1.1772063 |
| pooled_AAA_HR | 0.0598504 | 0.0294356 | 0.0030967 | 0.6353824 |
| log_pool_AA | 1.4124493 | 0.2539867 | 0.5907142 | 0.5443341 |
| pooled_AA_HR | 0.0477350 | 0.0284331 | 0.0051714 | 0.5245083 |
| age_upper_interaction | -0.8000000 | -0.1010469 | 0.2801271 | 0.4404004 |

conditional_pa: intercept 109.810506207, exact linear sum 206.524897913, linked output 206.524897913. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_AAA_HR | 0.0598504 | 0.0277197 | 0.0077869 | 51.5607193 |
| pooled_AA_HR | 0.0477350 | 0.0245100 | 0.0109472 | 25.3092424 |
| pooled_Aminus_HR | 0.0345224 | 0.0290362 | 0.0046372 | 10.6859377 |
| pooled_Aplus_3B | 0.0013270 | 0.0072151 | 0.0046836 | -9.9553063 |
| pooled_AAA_K | 0.2518703 | 0.2183310 | 0.0314046 | -9.8916717 |

rate: intercept -0.866834473, exact linear sum 2.517437546, linked output 2.517437546. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_AAA_HR | 0.0598504 | 0.0277197 | 0.0077869 | 0.9190869 |
| pooled_Aminus_2B | 0.0701956 | 0.0498542 | 0.0046008 | 0.4326943 |
| position_3 | 1.0000000 | 0.0852995 | 0.2793268 | 0.4293755 |
| pooled_Aplus_HR | 0.0419321 | 0.0250114 | 0.0099980 | 0.3807657 |
| pooled_Aminus_BABIP | 0.3191489 | 0.3022688 | 0.0105508 | -0.2005406 |

Broad actual training-profile support: participation 805 distinct people, conditional_pa 165 distinct people, rate 165 distinct people.

Alonso's 36 AA/AAA HR and 73 walks in 574 PA provide substantial upper-level power evidence. Shared prospect hitting rises .286 to 2.517 wins/600, closer to 3.865 actual; the largest term is AAA HR (+.919), with additional High-A power and older short-season doubles. PA increases only 127 to 139 versus 693 actual, since appearance probability slightly decreases while conditional workload increases to 207. This is the largest delivered gain, .452 to 1.008 offense wins versus 6.597 actual, yet PA remains the dominant residual gap. The rate improvement makes baseball sense for this individual but cannot rescue a candidate whose other prospect rates deteriorate. Broad conditional support is 165 people. Solak, Mercado, Brigman and Neuse give mixed arrival and hitting outcomes. Power-based translation needs a representation whose scarce rookie rates do not overwhelm reliable upper-level performance.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Nick Solak | 33.17 | 44.73 | 135 | -1.0602 | 3.3497 |
| Óscar Mercado | 87.73 | 86.30 | 482 | -1.7954 | 0.5131 |
| Bryson Brigman | 4.46 | 15.67 | 0 | -1.5681 | unobserved |
| Sheldon Neuse | 29.60 | 17.85 | 61 | -0.4634 | -2.2791 |

## Ethan Salas from 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0, highest current observed Aplus. Selection: fixed diagnostic.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Draft None, pick None, class unknown. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.025632 | 281.841619 | 7.224140 | -0.511711 | 0.016408 |
| Shared prospect | 0.011711 | 173.073507 | 2.026800 | 0.790657 | 0.009003 |
| Actual | 0 | Not a forecast | 0 | unobserved | 0.000000 |

PA-only offense 0.004603, rate-only offense 0.032089. Shared expected PA is 0.011710631 × 173.073506543; offense adds origin replacement 0.003124161/PA to the rate/600.

participation: intercept -5.918148651, exact linear sum -4.435478463, linked output 0.011710631. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| position_2 | 1.0000000 | 0.1744089 | 0.3794607 | 0.5640450 |
| highest_Aplus | 1.0000000 | 0.1155430 | 0.3196761 | 0.3631592 |
| role_minor_0 | 4.2066116 | 3.8481549 | 0.3958647 | 0.2955324 |
| reorganized | 1.0000000 | 0.2305676 | 0.4211962 | 0.2729890 |
| pooled_Aplus_HR | 0.0116940 | 0.0280833 | 0.0061139 | -0.2349237 |

conditional_pa: intercept 115.862740422, exact linear sum 173.073506543, linked output 173.073506543. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | 0.9300000 | -0.1126022 | 0.4564796 | 53.9666652 |
| age_squared | 3.2400000 | 0.7430110 | 0.6148382 | 49.8732920 |
| age_centered | -1.8000000 | -0.7519442 | 0.4214154 | 20.3951548 |
| draft_elapsed | 0.0000000 | 0.2572283 | 0.2146552 | 13.5272067 |
| log_pool_Aplus | 1.7894234 | 0.9569076 | 0.6537686 | -12.3125157 |

rate: intercept -0.993932114, exact linear sum 0.790656603, linked output 0.790656603. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| age_squared | 3.2400000 | 0.7430110 | 0.6148382 | 0.9058808 |
| age_centered | -1.8000000 | -0.7519442 | 0.4214154 | 0.7016875 |
| scout_rank_score_0 | 0.9300000 | -0.1126022 | 0.4564796 | 0.4341693 |
| reorganized | 1.0000000 | 0.2961117 | 0.4565408 | -0.3285840 |
| pooled_Aplus_HR | 0.0116940 | 0.0270531 | 0.0102580 | -0.3206213 |

Broad actual training-profile support: participation 3838 distinct people, conditional_pa 7 distinct people, rate 7 distinct people.

Salas's 18-year-old High-A season has four HR in 469 PA, not evidence of imminent MLB readiness. The shared head lowers arrival probability 2.6% to 1.2% and conditional workload 282 to 173, giving two expected PA against zero actual. This is plausible immediate opportunity, with all four origin-selected peers also not arriving. His rate rises from -.512 to +.791 mainly through age squared, age and ranking terms; only seven broad conditional-profile people exist. No MLB rate is observed for Salas, so neither his zero result nor peer zero labels validate that talent estimate. Yophery Rodriguez's +5.96 forecast among these peers is particularly unsupported and signals excessive rare-feature/conditional extrapolation, not evidence he is already an elite MLB hitter. Lower-stage improved totals must not conceal these rate and individual-risk problems.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Yophery Rodriguez | 0.38 | 1.54 | 0 | 5.9622 | unobserved |
| Juan Flores | 0.69 | 0.16 | 0 | -2.3672 | unobserved |
| Filippo Di Turi | 0.35 | 0.24 | 0 | 1.5737 | unobserved |
| Samuel Zavala | 0.46 | 1.21 | 0 | 0.4137 | unobserved |

## Jackson Holliday from 2023 to 2024

Player 702616, row 53595, fold 3; age 19.0, highest current observed AAA. Selection: largest delivered harm, false high.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | A | 57 | 0 | 10 | 14 |
| 2022 | RK124 | 33 | 1 | 2 | 10 |
| 2023 | A | 67 | 2 | 13 | 14 |
| 2023 | AA | 164 | 3 | 34 | 19 |
| 2023 | AAA | 91 | 2 | 17 | 16 |
| 2023 | Aplus | 259 | 5 | 54 | 50 |

Draft 2022, pick 1, class HS SR. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.825719 | 439.765700 | 363.123004 | 0.620777 | 1.499954 |
| Shared prospect | 0.936875 | 485.439565 | 454.796354 | 4.377755 | 4.726396 |
| Actual | 1 | Not a forecast | 208 | -3.309793 | -0.503411 |

PA-only offense 1.878629, rate-only offense 3.773696. Shared expected PA is 0.936875333 × 485.439564782; offense adds origin replacement 0.003096076/PA to the rate/600.

participation: intercept -5.898864977, exact linear sum 2.697438617, linked output 0.936875333. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| draft_rank | 1.0000000 | 0.1129834 | 0.1582807 | 1.3939233 |
| age_upper_interaction | -1.6000000 | -0.0995387 | 0.2802331 | 1.1349548 |
| draft_upper_interaction | 1.0000000 | 0.0350593 | 0.1066739 | 0.7844646 |
| role_minor_0 | 4.6000000 | 3.8472018 | 0.3976847 | 0.6149073 |
| pooled_AA_BABIP | 0.3640777 | 0.3004726 | 0.0102553 | 0.5334971 |

conditional_pa: intercept 116.212370367, exact linear sum 485.439564782, linked output 485.439564782. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| recent_draft_rank | 0.5000000 | 0.0760889 | 0.0944272 | 48.9741471 |
| scout_rank_score_0 | 0.8900000 | -0.1283551 | 0.4707811 | 43.7582055 |
| pooled_RK124_K | 0.1946203 | 0.2282978 | 0.0085009 | 42.6905219 |
| age_squared | 2.5600000 | 0.7506754 | 0.6141797 | 35.1252951 |
| pooled_AA_BABIP | 0.3640777 | 0.3105969 | 0.0228006 | 30.2511727 |

rate: intercept -0.942759494, exact linear sum 4.377755278, linked output 4.377755278. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_RK124_K | 0.1946203 | 0.2282978 | 0.0085009 | 1.1013656 |
| pooled_A_BB | 0.1561618 | 0.0826288 | 0.0161904 | 0.8230257 |
| pooled_AAA_BB | 0.1256545 | 0.0821719 | 0.0156376 | 0.7400216 |
| age_squared | 2.5600000 | 0.7506754 | 0.6141797 | 0.6087771 |
| age_centered | -1.6000000 | -0.7572985 | 0.4209209 | 0.5597214 |

Broad actual training-profile support: participation 9 distinct people, conditional_pa 3 distinct people, rate 3 distinct people.

Holliday's 2023 source shows twelve HR across 581 A/High-A/AA/AAA PA, strong walk rates and age 19; he was first overall, high-school senior class. Appearance probability increases 83% to 94% and conditional PA 440 to 485, yielding 455 expected versus 208 actual. That opportunity overestimate is worsened by batting rate .621 to 4.378 against -3.310 actual. He is both the largest delivered harm and false high: 4.726 offense wins versus -.503 actual. The new rate receives +1.10 from a small 2022 complex K sample, +.82 from A-ball walks, +.74 from AAA walks and large age terms. Broad conditional support is only three people. The underlying source history is real; the failure is overconfident standardized extrapolation and transfer of correlated low-level signals, not a discovered future-data leak. Merrill succeeds among peers while Williams, Hassell and Muncy do not arrive. The full candidate is not credible even though promising prospects should receive meaningful upside.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Jett Williams | 9.91 | 37.59 | 0 | -0.0513 | unobserved |
| Robert Hassell III | 67.30 | 107.33 | 0 | -0.2760 | unobserved |
| Max Muncy | 26.65 | 39.96 | 0 | 0.2416 | unobserved |
| Jackson Merrill | 144.31 | 102.94 | 593 | 0.2630 | 1.4836 |

## José Azócar from 2021 to 2022

Player 640492, row 42694, fold 4; age 25.0, highest current observed AAA. Selection: ordinary active prospect.

| Year | League | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 538 | 10 | 132 | 20 |
| 2021 | AA | 343 | 9 | 71 | 35 |
| 2021 | AAA | 201 | 0 | 45 | 6 |

Draft None, pick None, class unknown. Existing neutral 100-opportunity pooling is inherited; no park/opponent adjustment is newly introduced.

| Forecast | Appearance probability | Conditional PA | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Corrected baseline | 0.126439 | 100.739873 | 12.737471 | -1.047503 | 0.017694 |
| Shared prospect | 0.047303 | 97.886825 | 4.630350 | -0.470069 | 0.010889 |
| Actual | 1 | Not a forecast | 216 | -1.844412 | 0.013172 |

PA-only offense 0.006432, rate-only offense 0.029953. Shared expected PA is 0.047303101 × 97.886825160; offense adds origin replacement 0.003135003/PA to the rate/600.

participation: intercept -5.799524192, exact linear sum -3.002720949, linked output 0.047303101. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| log_pool_AA | 2.0357509 | 0.2440063 | 0.5762266 | 1.0561180 |
| log_pool_AAA | 1.1019401 | 0.0826137 | 0.3323664 | 0.9650389 |
| pooled_AAA_HR | 0.0099668 | 0.0294770 | 0.0031002 | -0.6341567 |
| pooled_AAA_BABIP | 0.3413655 | 0.3002258 | 0.0063145 | 0.3985534 |
| pooled_AA_BABIP | 0.3393449 | 0.3004517 | 0.0101580 | 0.2573767 |

conditional_pa: intercept 114.976159310, exact linear sum 97.886825160, linked output 97.886825160. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| scout_rank_score_0 | -1.0000000 | -0.0491678 | 0.3813337 | -34.5953341 |
| pooled_AAA_HR | 0.0099668 | 0.0281970 | 0.0077667 | -32.4299067 |
| log_minor_pa_1 | 0.0000000 | 1.5991448 | 0.4044666 | 24.2889627 |
| scout_rank_score_1 | -1.0000000 | -0.0614563 | 0.3120928 | -20.0278381 |
| pooled_AA_BABIP | 0.3393449 | 0.3104792 | 0.0225241 | 17.4011730 |

rate: intercept -0.850931177, exact linear sum -0.470069099, linked output -0.470069099. Each contribution is coefficient × (input minus training mean)/training scale.

| Feature | Origin input | Training mean | Training scale | Fitted contribution |
|---|---:|---:|---:|---:|
| pooled_AAA_HR | 0.0099668 | 0.0281970 | 0.0077667 | -0.6839540 |
| pooled_AAA_3B | 0.0282392 | 0.0053367 | 0.0027732 | -0.4227140 |
| log_games_minor_1 | 0.0000000 | 0.6861522 | 0.1935860 | 0.4210271 |
| log_minor_pa_1 | 0.0000000 | 1.5991448 | 0.4044666 | 0.4067155 |
| pooled_AAA_BB | 0.0465116 | 0.0804288 | 0.0142389 | -0.3519683 |

Broad actual training-profile support: participation 349 distinct people, conditional_pa 38 distinct people, rate 38 distinct people.

Azocar's 2019 and 2021 AA/AAA records are substantial, with nine AA HR and zero AAA HR in 201 PA in 2021. The canceled 2020 minor season remains zero exposure with an explicit cancellation indicator, not poor batting. Shared appearance probability falls 12.6% to 4.7% and expected PA 13 to five versus 216 actual. Conditional rate rises -1.048 to -.470 versus -1.844 actual. Delivered offense happens to be .011 versus .013 actual because opportunity and hitting errors offset near replacement; it is not successful readiness prediction. Missing 2020/2021 rank values (-1) and zero canceled-season exposure appear among large linear terms despite separate availability/cancellation flags, illustrating correlated encoding rather than proof absence predicts better talent. Broad conditional support is 38 people. Stefanic gets 69 actual PA, Casey and Beltre zero, Larsen one. Keep this ordinary-product case to prevent a close total from disguising poor components.

| Origin selected peer | Baseline PA | Shared PA | Actual PA | Shared rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Michael Stefanic | 15.87 | 15.50 | 69 | 1.1761 | -3.8550 |
| Donovan Casey | 43.60 | 6.31 | 0 | -1.9186 | unobserved |
| Michael Beltre | 1.17 | 1.28 | 0 | 1.3274 | unobserved |
| Jack Larsen | 11.74 | 4.93 | 1 | 1.4302 | -15.6294 |

## Decision and next step

Do not adopt the full candidate. Never-debut offense MSE worsens +.001886, nominal interval [-.000383,+.004730]; conditional rate MSE worsens +1.2260, [.5535,1.9774]. Prospect PA MSE improves -10.974, [-45.147,+20.705], a modest uncertain gain. PA-only offense MSE changes -.0000292, [-.000558,+.000459], not an established delivered-value gain.

Upper-never PA increases 73,593 to 78,029 versus 92,891 actual, while lower PA falls 7,652 to 6,762 versus 5,194. Total never-debut arrivals worsen 683 to 666 versus 787, despite better upper-group allocation. Expected total offense becomes close (219.39 versus 214.80 actual) but individual forecasts worsen. Holliday and Azocar explain why totals and products are insufficient.

The intended smooth pooling raises some fast-entry prospects, but StandardScaler amplifies rare rookie-sport count rates. Those rates have little variation among conditional training participants, so small known samples can become extreme standardized inputs. Holliday receives an implausibly firm +4.38 wins/600 while Bellinger is pulled down by older complex HR. This is a representation failure visible in exact fitted terms, not a reason to reject all prospect-specific prediction.

Next bounded repair: compare this same linear/hurdle construction using fixed baseball-unit scaling rather than dividing rare rate columns by tiny training standard deviations. Keep settings, source, population, folds and outputs unchanged and retain both controls. Do not tune to Holliday or Kurtz, introduce a new library, or claim profile support has increased. Separately dated scouting and MLB availability still remain missing information.
