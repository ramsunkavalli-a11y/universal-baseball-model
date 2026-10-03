# Numeric history correction and actual player reviews

Ten source-to-forecast reviews complete. Same 30,506 historical forecasts, original chronological player folds and 105 saved/replayed heads. Numeric source repair is retained; it is not a material forecasting breakthrough or deployment approval. Protected 2026 remains untouched.

Reconstruction uses only origin and two earlier seasons with weights 1/.8/.6. Seven count rates per league keep the original 100-PA/opportunity neutral prior. No park/opponent adjustment is added. Time since draft is (origin minus dated draft year)/10 with an explicit float type; unknown is separately flagged. All other inputs and training labels are unchanged. New actual scoring uses the common origin environment, not the older target-centered units.

| Scope | Rows | Old PA RMSE | Corrected PA RMSE | Old hitting RMSE | Corrected hitting RMSE | Old offense RMSE | Corrected offense RMSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | 30506 | 60.650 | 60.686 | 1.8796 | 1.8782 | 0.45387 | 0.45383 |
| never_debut | 24199 | 27.712 | 27.745 | 2.6449 | 2.6467 | 0.15399 | 0.15407 |
| upper_never_debut | 5454 | 56.169 | 56.242 | 2.6306 | 2.6320 | 0.31690 | 0.31707 |
| lower_never_debut | 17852 | 7.850 | 7.828 | 3.1102 | 3.1284 | 0.04285 | 0.04282 |
| current_regular | 1445 | 152.440 | 152.453 | 1.5479 | 1.5467 | 1.51058 | 1.51030 |
| public_broad | 2627 | 138.278 | 138.488 | 1.7452 | 1.7435 | 1.06131 | 1.06136 |
| public_legacy | 1789 | 142.110 | 142.334 | 1.7609 | 1.7585 | 1.04186 | 1.04075 |

Rates are actual-PA weighted among future MLB participants, with equal target-year weight; workload/offense retain non-arrivals. Rate units are fixed-event batting wins/600, not official wOBA or neutralized latent talent. Offense includes replacement but no fielding, position or running. Public snapshots have unknown exact dates. No superiority claim.

Fixed cases precede fits. Outcome-selected gain, harm, false high/low and ordinary cases are diagnostics, not independent confirmation. Four peers per case use origin year, stage, prior debut, age, minor exposure and draft rank without future outcomes; they are not equally talented or equally healthy. Profile counts are distinct training people in broad intersections, not proof of sufficiency.

## Nick Kurtz from 2024 to 2025

Player 701762, row 57052, fold 2; age 21.0, stage Upper minors. Selection: fixed source diagnostic.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Dated draft year 2024, pick 4, source class 4YR JR. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.0 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.017676 | 105.343956 | 1.862081 | -0.135562 | 0.005397 |
| Corrected | 0.017252 | 115.972916 | 2.000789 | -0.063223 | 0.006040 |
| Actual | 1 | Not a forecast | 489 | 5.289192 | 5.838406 |

Corrected product = 0.017252206 × 115.972915825 PA × (-0.063222554/600 + 0.003124161). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.013758037, reconstructed raw output -4.042412503. Largest fitted terms:

- draft_rank: input 0.817614505, additive fitted contribution 0.833055209.
- on_40man: input 0.000000000, additive fitted contribution -0.325945851.
- games_mlb_0: input 0.000000000, additive fitted contribution -0.198217829.
- games_pool_MLB: input 0.000000000, additive fitted contribution -0.188691820.
- role_pool_A: input 4.411764706, additive fitted contribution 0.186530623.

Same corrected fit with old numeric inputs: 0.017252206. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 278.575191046, reconstructed raw output 115.972915825. Largest fitted terms:

- work_0: input 0.000000000, additive fitted contribution -99.490116377.
- on_40man: input 0.000000000, additive fitted contribution -23.436218384.
- quality_0: input 0.000000000, additive fitted contribution -13.148362713.
- draft_rank: input 0.817614505, additive fitted contribution 10.742505919.
- regular_window_scaled: input 0.000000000, additive fitted contribution -10.311596034.

Same corrected fit with old numeric inputs: 115.972915825. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.984777637, reconstructed raw output -0.063222554. Largest fitted terms:

- age_centered: input -1.200000000, additive fitted contribution 0.619141828.
- reorganized: input 1.000000000, additive fitted contribution -0.263144768.
- draft_rank: input 0.817614505, additive fitted contribution 0.165485849.
- position_3: input 1.000000000, additive fitted contribution 0.134553805.
- age_squared: input 1.440000000, additive fitted contribution 0.077597553.

Same corrected fit with old numeric inputs: -0.063222554. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 4 distinct people, conditional_pa 0 distinct people, rate 0 distinct people.

Kurtz's fourth overall pick and college-junior class were present. His 35 A-ball PA included four HR and ten unintentional walks; another 15 AA PA included two walks but no HR. His own repaired inputs are unchanged, so every forecast change comes through refitted training relationships. The probability remains only 1.7%, with 116 PA conditional on participation, yielding two expected PA versus 489 actual. This is not a sensible resolved fast-entry estimate. The exact thin, draft-year, upper-minor profile has four training people and no conditional participants; a general shallow tree extrapolates from other profiles. Nearby origin-selected players include Cam Smith (493 actual PA) and Christian Moore (184), but also Montgomery and Williams (zero). They show both the missing opportunity signal and the danger of boosting every high pick. Peers are not matched on draft vintage, offensive profile or health; their outcomes cannot establish the correct probability for Kurtz. His future elite batting outcome is not recoverable merely by fixing draft time.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Benny Montgomery | 7.17 | 6.54 | 0 | -0.2032 | unobserved |
| Christian Moore | 8.02 | 8.23 | 184 | -0.0304 | -1.0849 |
| Cam Smith | 2.20 | 2.33 | 493 | -0.2546 | -0.4969 |
| Jett Williams | 69.94 | 74.66 | 0 | -0.1153 | unobserved |

## Wyatt Langford from 2023 to 2024

Player 694671, row 53164, fold 4; age 21.0, stage Upper minors. Selection: fixed source diagnostic.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | Aplus | 106 | 5 | 18 | 18 |
| 2023 | RK121 | 14 | 1 | 3 | 1 |

Dated draft year 2023, pick 4, source class 4YR JR. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.0 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.216727 | 216.599272 | 46.942857 | 0.642693 | 0.195622 |
| Corrected | 0.201829 | 213.555553 | 43.101733 | 0.688029 | 0.182872 |
| Actual | 1 | Not a forecast | 557 | 0.076953 | 1.795953 |

Corrected product = 0.201829138 × 213.555553050 PA × (0.688029041/600 + 0.003096076). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.088718362, reconstructed raw output -1.374901199. Largest fitted terms:

- role_pool_AA: input 4.272727273, additive fitted contribution 0.965840927.
- draft_rank: input 0.817614505, additive fitted contribution 0.716385838.
- pooled_AA_pa: input 54.000000000, additive fitted contribution 0.452236942.
- role_minor_0: input 4.444444444, additive fitted contribution 0.405193758.
- on_40man: input 0.000000000, additive fitted contribution -0.404257507.

Same corrected fit with old numeric inputs: 0.201829138. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 279.215202358, reconstructed raw output 213.555553050. Largest fitted terms:

- work_0: input 0.000000000, additive fitted contribution -99.865086037.
- role_pool_AAA: input 4.400000000, additive fitted contribution 37.070128919.
- on_40man: input 0.000000000, additive fitted contribution -18.288035348.
- age_centered: input -1.200000000, additive fitted contribution 14.860034641.
- role_pool_AA: input 4.272727273, additive fitted contribution 13.293606122.

Same corrected fit with old numeric inputs: 213.555553050. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.902988807, reconstructed raw output 0.688029041. Largest fitted terms:

- age_centered: input -1.200000000, additive fitted contribution 0.674183676.
- reorganized: input 1.000000000, additive fitted contribution -0.191039507.
- position_7: input 1.000000000, additive fitted contribution 0.187332934.
- draft_college: input 1.000000000, additive fitted contribution 0.160559285.
- pooled_AAA_BB: input 0.311111111, additive fitted contribution 0.102261196.

Same corrected fit with old numeric inputs: 0.688029041. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 31 distinct people, conditional_pa 2 distinct people, rate 2 distinct people.

Langford's 200 professional PA crossed complex, High-A, AA and AAA, with ten HR, 36 unintentional walks and 34 strikeouts. The model already knew pick four and college junior. His own numeric inputs are unchanged; refitting slightly lowers probability and conditional workload, from 47 to 43 expected PA versus 557 actual. The rate rises from .643 to .688 wins/600 versus .077 actual on the common-origin metric, so this player's main error is opportunity rather than next-year hitting talent. There are 31 training people in the broad same draft-year upper-minor profile but only two participants for conditional heads. Fixed-path terms reward AA role, exposure and draft rank; the conditional head still applies large no-MLB-workload reductions. Origin peers Crews appeared for 132 PA, while Veen, Shaw and Wilken had none. Rapid movement and production deserve a coherent readiness representation, not an automatic college-prospect regular role.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Zac Veen | 82.69 | 85.17 | 0 | -0.1593 | unobserved |
| Dylan Crews | 12.73 | 12.55 | 132 | 0.0662 | -1.7462 |
| Matt Shaw | 34.44 | 34.13 | 0 | -0.2230 | unobserved |
| Brock Wilken | 5.16 | 6.42 | 0 | 0.2414 | unobserved |

## Cody Bellinger from 2016 to 2017

Player 641355, row 24967, fold 3; age 20.0, stage Upper minors. Selection: fixed source diagnostic.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Dated draft year 2013, pick 124, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 139.79999999999998 | 139.79999999999998 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.3 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.101018 | 140.758217 | 14.219100 | 0.084712 | 0.045917 |
| Corrected | 0.110193 | 139.597326 | 15.382612 | 0.084596 | 0.049672 |
| Actual | 1 | Not a forecast | 548 | 2.928011 | 4.366524 |

Corrected product = 0.110192742 × 139.597325747 PA × (0.084595978/600 + 0.003088092). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.021533881, reconstructed raw output -2.088773847. Largest fitted terms:

- role_pool_AA: input 4.072580645, additive fitted contribution 0.699190658.
- pooled_AA_pa: input 465.000000000, additive fitted contribution 0.534613360.
- games_minor_0: input 117.000000000, additive fitted contribution 0.457330456.
- on_40man: input 0.000000000, additive fitted contribution -0.424700090.
- draft_rank: input 0.365827730, additive fitted contribution 0.377774928.

Same corrected fit with old numeric inputs: 0.110192742. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 276.981155813, reconstructed raw output 139.597325747. Largest fitted terms:

- MLB_0_pa: input 0.000000000, additive fitted contribution -83.956460241.
- work_0: input 0.000000000, additive fitted contribution -27.449139249.
- pooled_AAA_pa: input 12.000000000, additive fitted contribution 18.259827045.
- on_40man: input 0.000000000, additive fitted contribution -16.912854199.
- role_minor_2: input 4.475409836, additive fitted contribution 15.641116733.

Same corrected fit with old numeric inputs: 139.597325747. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.744379446, reconstructed raw output 0.084595978. Largest fitted terms:

- age_centered: input -1.400000000, additive fitted contribution 0.661387977.
- draft_class_unknown: input 1.000000000, additive fitted contribution -0.205747052.
- position_3: input 1.000000000, additive fitted contribution 0.148309967.
- age_squared: input 1.960000000, additive fitted contribution 0.141688347.
- draft_known: input 1.000000000, additive fitted contribution 0.128847110.

Same corrected fit with old numeric inputs: 0.138345229. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 561 distinct people, conditional_pa 122 distinct people, rate 122 distinct people.

Bellinger had 30 High-A HR in 2015 and 23 in 465 AA PA in 2016, plus three HR in twelve AAA PA. The tiny AAA line must not be treated as settled power. Draft time correctly becomes .3 rather than zero. Holding the repaired fitted parameters fixed and restoring the old input raises the rate .05375; the time term itself is negative, while refitted coefficients offset most of it. Participation and conditional forecasts do not change in that fixed-fit probe because his path remains on the same tree branches. Overall PA moves 14 to 15 versus 548 actual, and rate stays .085 versus 2.928. With 122 broad conditional-profile people, this is not only the recent-draft sparse-support issue: upper-minor power/readiness integration is compressed. Four peers have zero or 25 actual PA, preventing the claim that any similar-age upper-minor hitter deserves a full season. Blank source school class stays unknown, not invented high-school pedigree.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Alex Verdugo | 31.06 | 32.00 | 25 | 0.0249 | -3.6858 |
| Isiah Kiner-Falefa | 18.42 | 18.75 | 0 | -0.1348 | unobserved |
| Drew Ward | 2.13 | 1.95 | 0 | -0.0188 | unobserved |
| Jamie Westbrook | 4.86 | 4.21 | 0 | -0.4163 | unobserved |

## Pete Alonso from 2018 to 2019

Player 624413, row 33263, fold 1; age 23.0, stage Upper minors. Selection: fixed source diagnostic.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Dated draft year 2016, pick 64, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.2 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.729998 | 180.189571 | 131.538003 | 0.259881 | 0.461949 |
| Corrected | 0.692850 | 183.403275 | 127.070997 | 0.286158 | 0.451826 |
| Actual | 1 | Not a forecast | 693 | 3.864560 | 6.597153 |

Corrected product = 0.692850205 × 183.403275318 PA × (0.286158486/600 + 0.003078768). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.017674411, reconstructed raw output 0.813478261. Largest fitted terms:

- games_minor_0: input 132.000000000, additive fitted contribution 0.962216848.
- role_pool_AA: input 4.183770883, additive fitted contribution 0.915294174.
- pooled_AA_pa: input 310.600000000, additive fitted contribution 0.705913574.
- draft_rank: input 0.452843514, additive fitted contribution 0.543319136.
- on_40man: input 0.000000000, additive fitted contribution -0.466914996.

Same corrected fit with old numeric inputs: 0.692850205. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 287.128812587, reconstructed raw output 183.403275318. Largest fitted terms:

- MLB_0_pa: input 0.000000000, additive fitted contribution -66.383899044.
- work_0: input 0.000000000, additive fitted contribution -42.506976312.
- role_pool_AAA: input 4.428571429, additive fitted contribution 34.618073310.
- pooled_AAA_HR: input 0.059850374, additive fitted contribution 29.557808370.
- on_40man: input 0.000000000, additive fitted contribution -21.980378739.

Same corrected fit with old numeric inputs: 183.403275318. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.667725825, reconstructed raw output 0.286158486. Largest fitted terms:

- age_centered: input -0.800000000, additive fitted contribution 0.414810667.
- position_3: input 1.000000000, additive fitted contribution 0.174020665.
- draft_known: input 1.000000000, additive fitted contribution 0.155399275.
- draft_class_unknown: input 1.000000000, additive fitted contribution -0.139269648.
- pooled_AAA_HR: input 0.298503741, additive fitted contribution 0.122771737.

Same corrected fit with old numeric inputs: 0.326007188. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 805 distinct people, conditional_pa 165 distinct people, rate 165 distinct people.

Alonso's source has 36 HR and 73 unintentional walks in 574 AA/AAA PA in 2018, after 18 HR in 2017. Draft time correctly changes to .2. Its direct repaired Ridge effect is -.03985 wins/600; the fixed-fit old-input rate is .326 rather than .286. Refitting the whole model leaves the forecast somewhat above the old .260 but nowhere near 3.865 actual. Appearance probability is fairly high at 69%, yet conditional workload is only 183 PA; 127 expected versus 693 actual makes workload and power translation jointly deficient. There are 165 broad conditional-profile training people. Solak and Mercado reached MLB, Brigman did not, and Neuse appeared with poor hitting. Those peers were selected without looking at future outcomes but are not power-matched. This correction does not settle the already known missing-upper-minor-power hypothesis.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Nick Solak | 34.76 | 33.17 | 135 | -0.5706 | 3.3497 |
| Óscar Mercado | 91.39 | 87.73 | 482 | -0.7653 | 0.5131 |
| Bryson Brigman | 4.17 | 4.46 | 0 | -0.4679 | unobserved |
| Sheldon Neuse | 26.16 | 29.60 | 61 | 0.4166 | -2.2791 |

## Ethan Salas from 2024 to 2025

Player 806956, row 57694, fold 3; age 18.0, stage Lower minors. Selection: fixed source diagnostic.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Dated draft year None, pick None, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.0 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.025652 | 278.309347 | 7.139187 | -0.447557 | 0.016979 |
| Corrected | 0.025632 | 281.841619 | 7.224140 | -0.511711 | 0.016408 |
| Actual | 0 | Not a forecast | 0 | unobserved | 0.000000 |

Corrected product = 0.025631912 × 281.841619265 PA × (-0.511710571/600 + 0.003124161). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.049565585, reconstructed raw output -3.637950991. Largest fitted terms:

- scout_rank_score_0: input 0.930000000, additive fitted contribution 0.510933733.
- games_minor_0: input 111.000000000, additive fitted contribution 0.451357150.
- on_40man: input 0.000000000, additive fitted contribution -0.380077526.
- scout_listed_0: input 1.000000000, additive fitted contribution 0.332128474.
- games_mlb_0: input 0.000000000, additive fitted contribution -0.297719387.

Same corrected fit with old numeric inputs: 0.025631912. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 277.949400830, reconstructed raw output 281.841619265. Largest fitted terms:

- scout_rank_score_0: input 0.930000000, additive fitted contribution 187.949120302.
- work_0: input 0.000000000, additive fitted contribution -95.676289123.
- on_40man: input 0.000000000, additive fitted contribution -22.080265897.
- pooled_MLB_HBP: input 0.010000000, additive fitted contribution 12.846755108.
- role_pool_AAA: input 4.000000000, additive fitted contribution -12.657878922.

Same corrected fit with old numeric inputs: 281.841619265. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.921844180, reconstructed raw output -0.511710571. Largest fitted terms:

- age_centered: input -1.800000000, additive fitted contribution 0.973195294.
- reorganized: input 1.000000000, additive fitted contribution -0.265569819.
- position_2: input 1.000000000, additive fitted contribution -0.179442263.
- age_squared: input 3.240000000, additive fitted contribution 0.175883341.
- pooled_Aplus_pa: input 0.831000000, additive fitted contribution -0.118656414.

Same corrected fit with old numeric inputs: -0.511710571. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 3838 distinct people, conditional_pa 7 distinct people, rate 7 distinct people.

Salas was 18, playing High-A, with four HR, 98 K and 47 unintentional walks in 469 PA. His draft history is genuinely unknown in this source, not an old drafted player whose time was zeroed. Numeric inputs are unchanged; refitted parameters leave MLB probability at 2.6%, expected PA about seven and actual PA zero. This is a plausible next-year readiness result, not evidence of low career value. His high ranking adds about 188 PA to the conditional tree path, but only seven broad age/stage conditional-profile people exist, so the 282-PA conditional mean remains weakly supported. All four origin-selected peers also did not arrive. No participant rate is observed for Salas or those zero-PA peers; their stored zero target is never used as a hitting-talent score.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Yophery Rodriguez | 0.34 | 0.38 | 0 | -0.2985 | unobserved |
| Juan Flores | 0.70 | 0.69 | 0 | -0.5833 | unobserved |
| Filippo Di Turi | 0.32 | 0.35 | 0 | -0.2552 | unobserved |
| Samuel Zavala | 0.43 | 0.46 | 0 | -0.3246 | unobserved |

## Shohei Ohtani from 2023 to 2024

Player 660271, row 51141, fold 1; age 28.0, stage Current MLB. Selection: largest delivered gain.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 639 | 46 | 189 | 76 |
| 2022 | MLB | 666 | 34 | 161 | 58 |
| 2023 | MLB | 599 | 44 | 143 | 70 |

Dated draft year None, pick None, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.0 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.992434 | 559.066705 | 554.837050 | 3.016594 | 4.507348 |
| Corrected | 0.992309 | 569.109892 | 564.732833 | 3.044074 | 4.613604 |
| Actual | 1 | Not a forecast | 731 | 5.139100 | 8.524368 |

Corrected product = 0.992308939 × 569.109891982 PA × (3.044074159/600 + 0.003096076). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.003237254, reconstructed raw output 4.859975807. Largest fitted terms:

- on_40man: input 1.000000000, additive fitted contribution 2.582623221.
- games_mlb_0: input 135.000000000, additive fitted contribution 1.967923006.
- work_0: input 599.000000000, additive fitted contribution 1.056187207.
- quality_0: input 1.629409412, additive fitted contribution 0.747658918.
- games_pool_MLB: input 355.400000000, additive fitted contribution 0.580133544.

Same corrected fit with old numeric inputs: 0.992308939. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 283.925540114, reconstructed raw output 569.109891982. Largest fitted terms:

- work_0: input 599.000000000, additive fitted contribution 135.191651358.
- quality_0: input 1.629409412, additive fitted contribution 34.725203292.
- role_pool_MLB: input 4.256157635, additive fitted contribution 32.244701349.
- role_mlb_0: input 4.406896552, additive fitted contribution 26.320657561.
- games_mlb_2: input 158.000000000, additive fitted contribution 16.637152347.

Same corrected fit with old numeric inputs: 569.109891982. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.789913341, reconstructed raw output 3.044074159. Largest fitted terms:

- pooled_mlb_quality: input 2.077295581, additive fitted contribution 1.587600734.
- work_0: input 599.000000000, additive fitted contribution 0.779915224.
- quality_0: input 1.629409412, additive fitted contribution 0.700897788.
- work_2: input 639.263071223, additive fitted contribution 0.492439922.
- quality_2: input 1.201022521, additive fitted contribution 0.272083876.

Same corrected fit with old numeric inputs: 3.044074159. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 457 distinct people, conditional_pa 351 distinct people, rate 351 distinct people.

Ohtani has three large MLB samples: 46, 34 and 44 HR with 639, 666 and 599 PA. He has no joined draft record, so his own repaired inputs are identical. His largest delivered-value gain comes from shared refitted coefficients: workload rises 555 to 565 and rate 3.017 to 3.044. Current workload, MLB quality and lineup opportunity lead the saved paths. Actual is 731 PA and 5.139 batting wins/600, so a .106 offense-win improvement still leaves a large miss. It is not proof the draft repair directly revealed Ohtani talent. The broad conditional profile has 351 people. Arcia and Ramirez peers declined, Santander improved, and Mateo had reduced workload. None was selected to match Ohtani's exceptional power or two-way context, which this branch omits.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Orlando Arcia | 417.37 | 416.85 | 602 | -0.5018 | -2.2996 |
| Jorge Mateo | 273.45 | 275.04 | 208 | -1.8741 | -1.7595 |
| Harold Ramírez | 409.99 | 409.16 | 246 | 0.4394 | -2.5959 |
| Anthony Santander | 549.66 | 547.72 | 665 | 0.9303 | 1.2043 |

## Matt Olson from 2022 to 2023

Player 621566, row 46729, fold 1; age 28.0, stage Current MLB. Selection: largest delivered harm.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

Dated draft year 2012, pick 47, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 1 | 1.0 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.992588 | 612.699131 | 608.157705 | 1.857985 | 3.787372 |
| Corrected | 0.993755 | 610.111677 | 606.301627 | 1.773564 | 3.690506 |
| Actual | 1 | Not a forecast | 720 | 5.114949 | 8.392240 |

Corrected product = 0.993755158 × 610.111677486 PA × (1.773564463/600 + 0.003130974). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -3.990266037, reconstructed raw output 5.069735040. Largest fitted terms:

- on_40man: input 1.000000000, additive fitted contribution 2.996809539.
- games_mlb_0: input 162.000000000, additive fitted contribution 1.988530131.
- quality_0: input 0.573576479, additive fitted contribution 0.961640156.
- work_0: input 699.000000000, additive fitted contribution 0.846151018.
- pooled_MLB_pa: input 1384.400000000, additive fitted contribution 0.532314774.

Same corrected fit with old numeric inputs: 0.993755158. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 283.464045859, reconstructed raw output 610.111677486. Largest fitted terms:

- work_0: input 699.000000000, additive fitted contribution 127.838409667.
- role_pool_MLB: input 4.280048077, additive fitted contribution 33.543145160.
- role_mlb_0: input 4.296511628, additive fitted contribution 32.826973450.
- quality_0: input 0.573576479, additive fitted contribution 27.929565011.
- MLB_0_pa: input 699.000000000, additive fitted contribution 19.973099559.

Same corrected fit with old numeric inputs: 610.111677486. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.721053407, reconstructed raw output 1.773564463. Largest fitted terms:

- work_0: input 699.000000000, additive fitted contribution 0.873189113.
- pooled_mlb_quality: input 1.033181034, additive fitted contribution 0.799016095.
- work_2: input 662.973273942, additive fitted contribution 0.457995175.
- quality_0: input 0.573576479, additive fitted contribution 0.235634384.
- quality_1: input 1.077474794, additive fitted contribution 0.233075572.

Same corrected fit with old numeric inputs: 1.773564463. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 568 distinct people, conditional_pa 454 distinct people, rate 454 distinct people.

Olson had 39 and 34 HR in 673 and 699 full-season PA after the shortened 2020 season. The source already has elapsed draft time 1.0, so his own numeric repair is exactly zero. The biggest delivered harm is parameter refitting: PA falls 608 to 606 and rate 1.858 to 1.774, against a 720-PA, 5.115-win/600 actual breakout. Saved rate terms rely on MLB quality and workload, and his broad conditional profile has 454 players. The repair does not explain his breakout or justify a name-specific boost. Winker collapses among the origin-selected peers while Gallo, Caratini and Ward give mixed results, demonstrating why a known power hitter is not guaranteed to repeat or improve. This is a small forecast movement within an already large hitting-rate miss.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Jesse Winker | 497.74 | 490.73 | 197 | 1.3584 | -1.8157 |
| Joey Gallo | 320.14 | 317.16 | 332 | 0.1259 | 0.6390 |
| Victor Caratini | 216.39 | 220.57 | 226 | -1.1630 | 0.3315 |
| Taylor Ward | 484.20 | 483.25 | 409 | 1.3644 | 1.1649 |

## Chris Davis from 2017 to 2018

Player 448801, row 27537, fold 3; age 31.0, stage Current MLB. Selection: false high.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

Dated draft year 2006, pick 148, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 1 | 1.1 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.975763 | 515.122880 | 502.637696 | 1.173578 | 2.529343 |
| Corrected | 0.977731 | 518.137251 | 506.598886 | 1.081636 | 2.471646 |
| Actual | 1 | Not a forecast | 522 | -4.101756 | -1.962764 |

Corrected product = 0.977731064 × 518.137250825 PA × (1.081635642/600 + 0.003076176). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.072655002, reconstructed raw output 3.782041960. Largest fitted terms:

- on_40man: input 1.000000000, additive fitted contribution 3.316210340.
- games_mlb_0: input 128.000000000, additive fitted contribution 1.646414985.
- MLB_0_pa: input 524.000000000, additive fitted contribution 0.697599882.
- games_pool_MLB: input 349.600000000, additive fitted contribution 0.563021580.
- pooled_MLB_pa: input 1458.000000000, additive fitted contribution 0.415481663.

Same corrected fit with old numeric inputs: 0.977731064. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 278.205818472, reconstructed raw output 518.137250825. Largest fitted terms:

- MLB_0_pa: input 524.000000000, additive fitted contribution 85.808587076.
- role_pool_MLB: input 4.165739711, additive fitted contribution 35.261441703.
- role_mlb_0: input 4.086956522, additive fitted contribution 29.409516355.
- pooled_Aplus_K: input 0.238095238, additive fitted contribution 28.731418798.
- work_0: input 524.000000000, additive fitted contribution 27.012266923.

Same corrected fit with old numeric inputs: 518.137250825. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.845705077, reconstructed raw output 1.081635642. Largest fitted terms:

- pooled_mlb_quality: input 0.720993005, additive fitted contribution 0.478257379.
- work_0: input 524.000000000, additive fitted contribution 0.463188613.
- work_1: input 665.547775947, additive fitted contribution 0.409308258.
- age_centered: input 0.800000000, additive fitted contribution -0.376047883.
- work_2: input 670.275833676, additive fitted contribution 0.309067241.

Same corrected fit with old numeric inputs: 1.096436043. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 39 distinct people, conditional_pa 28 distinct people, rate 28 distinct people.

Davis is the largest positive offense error: 506.6 PA is near the actual 522, but projected +1.082 batting wins/600 contrasts with -4.102 actual. The known history shows 47, 38 and 26 HR and K rates rising from 208/670 to 195/524, so declining production was observable. Draft time goes 1.0 to 1.1; its direct fixed-fit rate reduction is only .0148. Shared refitting supplies most of the .092 total rate drop. A catastrophic collapse is not certain from that history, but this case motivates preserving trend information in an interpretable talent comparison rather than calling close workload success. The broad conditional profile is only 28 people. Guyer, Romine and Joseph also hit poorly in the next year and Barney did not appear; these role-unmatched peers show exit/decline risk, not a precise Davis collapse probability.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Brandon Guyer | 162.98 | 164.16 | 221 | 0.0842 | -1.1714 |
| Darwin Barney | 150.71 | 149.58 | 0 | -1.5570 | unobserved |
| Andrew Romine | 185.07 | 190.75 | 131 | -1.3829 | -4.9006 |
| Caleb Joseph | 187.60 | 187.11 | 280 | -1.4805 | -3.4796 |

## Aaron Judge from 2016 to 2017

Player 592450, row 23934, fold 3; age 24.0, stage Current MLB. Selection: false low.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Dated draft year 2013, pick 32, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.3 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.931614 | 308.550582 | 287.450116 | -0.057204 | 0.860267 |
| Corrected | 0.925862 | 304.039468 | 281.498549 | -0.039660 | 0.850686 |
| Actual | 1 | Not a forecast | 678 | 5.557416 | 8.373606 |

Corrected product = 0.925861866 × 304.039467855 PA × (-0.039659855/600 + 0.003088092). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.021533881, reconstructed raw output 2.524795024. Largest fitted terms:

- on_40man: input 1.000000000, additive fitted contribution 3.130486109.
- games_mlb_0: input 27.000000000, additive fitted contribution 1.179130602.
- games_pool_MLB: input 27.000000000, additive fitted contribution 0.568563150.
- scout_rank_score_0: input 0.700000000, additive fitted contribution 0.299440395.
- MLB_0_pa: input 95.000000000, additive fitted contribution 0.280294083.

Same corrected fit with old numeric inputs: 0.925861866. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 276.981155813, reconstructed raw output 304.039467855. Largest fitted terms:

- scout_rank_score_0: input 0.700000000, additive fitted contribution 125.260278122.
- MLB_0_pa: input 95.000000000, additive fitted contribution -63.349977937.
- pooled_MLB_K: input 0.333333333, additive fitted contribution -23.006822574.
- work_0: input 95.078253707, additive fitted contribution -22.663524883.
- role_pool_AAA: input 4.334650856, additive fitted contribution 15.520093352.

Same corrected fit with old numeric inputs: 304.039467855. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.744379446, reconstructed raw output -0.039659855. Largest fitted terms:

- age_centered: input -0.600000000, additive fitted contribution 0.283451990.
- draft_class_unknown: input 1.000000000, additive fitted contribution -0.205747052.
- position_9: input 1.000000000, additive fitted contribution 0.167209664.
- draft_known: input 1.000000000, additive fitted contribution 0.128847110.
- pooled_mlb_quality: input -0.175091262, additive fitted contribution -0.119032750.

Same corrected fit with old numeric inputs: 0.014089396. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 104 distinct people, conditional_pa 100 distinct people, rate 100 distinct people.

Judge's 2016 source includes 19 HR, 98 K and 47 walks in 410 AAA PA, followed by 42 K in a 95-PA MLB debut. Time since draft correctly becomes .3, but the repaired projection stays almost average at -.040 batting wins/600 and 281 expected PA versus 678 and +5.557 actual. Appearance chance is already 93%; the unresolved problems are conditional playing time and translating longer upper-minor evidence alongside a short poor debut. Saved conditional paths reward his rank but penalize current MLB exposure and K rate. The direct draft-time rate effect is only -.05375, not the cause of this enormous miss. Cowart/Jones remain weak next-year hitters among peers, Pinder is near average and Healy plays regularly; not every short debut should be rescued. One 52-HR season does not prove a prospect's ex ante expectation should have been that high.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Kaleb Cowart | 136.82 | 135.24 | 117 | -0.9111 | -0.9890 |
| JaCoby Jones | 71.85 | 69.81 | 154 | -0.4322 | -4.2514 |
| Chad Pinder | 163.19 | 162.21 | 309 | -0.8933 | 0.1139 |
| Ryon Healy | 425.73 | 429.59 | 605 | 0.2733 | 0.3468 |

## Harrison Bader from 2023 to 2024

Player 664056, row 51242, fold 1; age 29.0, stage Current MLB. Selection: ordinary.

| Season | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 11 | 0 | 1 | 1 |
| 2021 | AAA | 3 | 0 | 1 | 1 |
| 2021 | MLB | 401 | 16 | 85 | 21 |
| 2022 | AA | 23 | 1 | 3 | 2 |
| 2022 | AAA | 4 | 0 | 0 | 1 |
| 2022 | MLB | 313 | 5 | 62 | 15 |
| 2023 | AA | 18 | 0 | 5 | 0 |
| 2023 | AAA | 21 | 0 | 3 | 2 |
| 2023 | MLB | 344 | 7 | 59 | 17 |

Dated draft year 2015, pick 100, source class unknown. No additional school/college evidence is collected.

| Reconstructed input | Old | Corrected |
|---|---:|---:|
| pooled_DSL_pa | 0 | 0.0 |
| pooled_RK120_pa | 0 | 0.0 |
| pooled_RK128_pa | 0.0 | 0.0 |
| pooled_RK134_pa | 0 | 0.0 |
| draft_elapsed | 0 | 0.8 |

| Forecast | MLB probability | PA if active | Expected PA | Batting wins per 600 | Offense wins |
|---|---:|---:|---:|---:|---:|
| Old | 0.659958 | 214.134383 | 141.319803 | -1.241758 | 0.145062 |
| Corrected | 0.666666 | 214.026691 | 142.684396 | -1.240591 | 0.146740 |
| Actual | 1 | Not a forecast | 437 | -1.657310 | 0.145911 |

Corrected product = 0.666666363 × 214.026691453 PA × (-1.240591022/600 + 0.003096076). All input fields, exact tree paths and Ridge sums are saved in cases.json.

participation: reference -4.003237254, reconstructed raw output 0.693145812. Largest fitted terms:

- games_mlb_0: input 98.000000000, additive fitted contribution 2.076557277.
- on_40man: input 0.000000000, additive fitted contribution -1.017001440.
- games_pool_MLB: input 228.600000000, additive fitted contribution 0.995647728.
- work_0: input 344.000000000, additive fitted contribution 0.649629314.
- pooled_MLB_pa: input 835.000000000, additive fitted contribution 0.489276950.

Same corrected fit with old numeric inputs: 0.666666363. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

conditional_pa: reference 283.925540114, reconstructed raw output 214.026691453. Largest fitted terms:

- on_40man: input 0.000000000, additive fitted contribution -41.595132198.
- work_0: input 344.000000000, additive fitted contribution 34.988355703.
- quality_0: input -0.519569479, additive fitted contribution -33.005210702.
- role_mlb_0: input 3.555555556, additive fitted contribution -26.172823471.
- regular_window_scaled: input 0.333333333, additive fitted contribution 12.411775367.

Same corrected fit with old numeric inputs: 214.026691453. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

rate: reference -0.789913341, reconstructed raw output -1.240591022. Largest fitted terms:

- work_0: input 344.000000000, additive fitted contribution 0.447897891.
- pooled_mlb_quality: input -0.443048261, additive fitted contribution -0.338605517.
- work_2: input 401.165088514, additive fitted contribution 0.309027244.
- quality_0: input -0.519569479, additive fitted contribution -0.223495148.
- age_centered: input 0.400000000, additive fitted contribution -0.221366367.

Same corrected fit with old numeric inputs: -1.112663581. This isolates input-path sensitivity from parameter refitting; it is not causal attribution or a validated alternative.

Broad training-profile counts: participation 638 distinct people, conditional_pa 505 distinct people, rate 505 distinct people.

Bader is selected as an ordinary delivered-value error, but his component forecasts are not ordinary successes. Prior MLB PA is 401, 313 and 344; he is not on the cutoff 40-man source. Probability 66.7% times 214 conditional PA gives 143 expected, versus 437 actual. Forecast hitting rate -1.241 is less bad than -1.657 actual. The product happens to be .147 offense wins versus .146 actual because workload and rate errors offset around replacement. Draft time correctly changes from zero to .8, with a direct -.12793 rate effect, largely offset by other coefficient refitting. His 505-person conditional profile does not validate treating cutoff unsigned status as permanent loss of a job. Taylor, DeJong, Caratini and O'Hearn all get future PA. This reinforces the availability/opportunity gap and the need to score components separately, not celebrate a lucky product.

| Origin selected peer | Old PA | Corrected PA | Actual PA | Corrected rate | Actual rate |
|---|---:|---:|---:|---:|---:|
| Tyrone Taylor | 260.10 | 261.19 | 345 | -0.3021 | -0.7996 |
| Paul DeJong | 369.08 | 374.94 | 482 | -1.6708 | -0.8218 |
| Victor Caratini | 246.29 | 246.38 | 274 | -1.2798 | 0.2796 |
| Ryan O'Hearn | 394.06 | 392.69 | 494 | -0.2216 | 0.5442 |

## Decision after review

Keep the explicit floating-point source repair for subsequent candidate construction, preserving the old candidate. A tiny score improvement cannot establish practical success. Full PA RMSE is 60.686 versus 60.650; common-origin offense RMSE .45383 versus .45387. Public broad hitting RMSE is 1.74350 versus old 1.74524, Steamer 1.77459 and ZiPS 1.75336; PA MAE 106.87 versus Steamer 92.08 still fails the practical 15% tolerance.

Nominal full-population offense MSE change is -.0000400, interval [-.0004472,+.0003667]; PA MSE change +4.290, interval [-3.085,+10.794]. Conditional rate MSE improves -.005068, interval [-.009666,-.000973], but prospect-only rates worsen slightly and do not establish an overall value win. All are development intervals after repeated historical testing.

Upper never-debut expected PA falls 73,989 to 73,593 against 92,891 actual, and expected arrivals remain about 593 against 730 actual. Lower never-debut still allocates 7,652 PA against 5,194. Public exact archive timing, 218 roster-only qualifications, park/opponent treatment and joint value uncertainty remain open. The source defect is real, but it does not explain away the missed fast entrants.

Next: one prospect-readiness alternative that shares strength across closely related level/exposure/pedigree profiles, using the corrected source and both entrants and non-arrivals. Do not fit a separate tiny Kurtz-like leaf on zero conditional examples, hand-boost named stars, or switch to another general algorithm tournament. Also preserve the known establishment/availability gap rather than pretending a prospect-only change can solve public MLB workload.
