# Hitting comparisons using the same event units

Eleven actual source-to-forecast reviews complete. Fixed index weights use total PA, not official wOBA or park-neutral true talent. Predictions are unchanged; actual and forecast comparisons now share one unit. No future environment is inserted into a forecast. All original public results remain preserved.

Raw actual index = weighted mature MLB event counts/actual PA. UBM implied index = origin index + relative forecast/UNIT, where UNIT=600/(10×1.193). Public index = the same fixed-weight numerator/projected total PA. Common readable rate = UNIT×(index-origin index); all systems subtract the same origin. Contribution uses origin replacement. This is a same-unit event diagnostic, not full WAR or trade/control value.

The larger public sample contains 2,627 current-MLB forecasts, 2,088 with actual MLB PA; 1,789 legacy matches are retained exactly. Common membership still excludes missing public forecasts and non-current players, so it does not certify all prospects. A zero actual index stored on inactive rows is never scored as an observed talent value.

Peer selection uses origin year, age, elapsed and workload, without future results. It does not establish equal power/park/health profiles. Public source dates remain unknown. The one-PA availability grouping below is a diagnostic only: no row is removed from the primary population and no model uses future/public labels as an input.

## Aaron Judge from 2024 to 2025

Player 592450, row 54849, fold 3; age 32.0, elapsed 8. Selection: fixed source diagnostic.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Origin league index 0.305333851; realized target index 0.308101260. Only the origin enters forecast conversion. Old actual centered rate 6.287431; common-origin actual rate 6.426613.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.394843889 | 4.501762 | 534.274998 | 5.677793 |
| binary | 0.395869421 | 4.553340 | 530.583380 | 5.684172 |
| fixed | 0.426861042 | 6.112013 | 530.583380 | 7.062515 |
| learned | 0.409293989 | 5.228507 | 530.583380 | 6.281226 |
| steamer | 0.396426293 | 4.581347 | 624.684570 | 6.721443 |
| zips | 0.405944252 | 5.060037 | Conditional exposure only | Not a workload forecast |
| Actual | 0.433116348 | 6.426613 | 679 | 9.394089 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 624.684570 | 72.585403 | 22.710600 | 0.703100 | 44.233002 | 104.322304 | 14.367700 | 6.246800 | 247.641389 |
| zips | 635.000000 | 73.000000 | 26.000000 | 0.000000 | 46.000000 | 109.000000 | 13.000000 | 5.000000 | 257.774600 |

UBM implied index = 0.305333851 + 4.553340/50.293378039 = 0.395869421. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003124161). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Judge's known three-year MLB HR record is 62/37/58. UBM and Steamer imply almost the same event index (.39587/.39643); ZiPS is .40594, actual .43312. UBM's larger delivered miss is therefore substantially opportunity: 531 PA versus Steamer 625 and actual 679. Changing the evaluation center does not fix these forecasts or mean the hitter record disappeared. Nimmo/Hernandez/Schwarber/Diaz have similar age/exposure but are not equal-power peers; Schwarber and Diaz also outperform forecasts. This established case extends beyond the old elapsed-0–5 public slice.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Brandon Nimmo | 1.056658 | 1.363640 | 0.964655 | 652 |
| Teoscar Hernández | 0.802968 | 1.197656 | 0.264779 | 546 |
| Kyle Schwarber | 2.193751 | 2.163149 | 3.931920 | 724 |
| Yandy Díaz | 1.442283 | 2.378340 | 2.679506 | 651 |

## Masyn Winn from 2023 to 2024

Player 691026, row 52733, fold 4; age 21.0, elapsed 0. Selection: fixed source diagnostic.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Origin league index 0.314721261; realized target index 0.305333851. Only the origin enters forecast conversion. Old actual centered rate 0.254541; common-origin actual rate -0.217583.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.298824312 | -0.799511 | 302.679213 | 0.533792 |
| binary | 0.298879982 | -0.796711 | 338.133720 | 0.597896 |
| fixed | 0.253511244 | -3.078459 | 338.133720 | -0.687997 |
| learned | 0.286993140 | -1.394541 | 338.133720 | 0.260986 |
| steamer | 0.296919652 | -0.895303 | 427.368866 | 0.685459 |
| zips | 0.292324281 | -1.126420 | Conditional exposure only | Not a workload forecast |
| Actual | 0.310394976 | -0.217583 | 637 | 1.741199 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 427.368866 | 65.266403 | 17.549801 | 2.780600 | 9.522400 | 32.052700 | 0.000000 | 3.419000 | 126.894215 |
| zips | 626.000000 | 95.000000 | 24.000000 | 6.000000 | 13.000000 | 45.000000 | 0.000000 | 5.000000 | 182.995000 |

UBM implied index = 0.314721261 + -0.796711/50.293378039 = 0.298879982. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003096076). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Winn's good 498-PA AAA season (18 HR, 83 K) and poor 137-PA MLB debut are both present. UBM's implied .29888 is slightly less pessimistic than Steamer .29692 and ZiPS .29232; actual is .31039. The old actual relative label was +.255, but actual relative to the origin environment is -.218 because the MLB environment fell. The apparent sign change is a unit change, not altered performance. All three miss some improvement, and UBM's 338 PA versus 427 Steamer and 637 actual is the bigger opportunity gap. Soderstrom/Butler improve, Schanuel is near average and Marte fails among origin-selected peers.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Tyler Soderstrom | -0.784320 | -1.824872 | 0.114133 | 213 |
| Nolan Schanuel | 0.757587 | 1.087111 | -0.174710 | 607 |
| Noelvi Marte | -0.151042 | 0.548529 | -3.735373 | 242 |
| Lawrence Butler | -0.393785 | -1.084589 | 1.279628 | 451 |

## Spencer Steer from 2022 to 2023

Player 668715, row 47421, fold 4; age 24.0, elapsed 0. Selection: fixed source diagnostic.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Origin league index 0.303902205; realized target index 0.314721261. Only the origin enters forecast conversion. Old actual centered rate 1.909209; common-origin actual rate 2.453336.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.299160016 | -0.238501 | 183.018033 | 0.500275 |
| binary | 0.299197206 | -0.236630 | 243.552996 | 0.666505 |
| fixed | 0.290770527 | -0.660436 | 243.552996 | 0.494473 |
| learned | 0.288637798 | -0.767699 | 243.552996 | 0.450933 |
| steamer | 0.304565007 | 0.033335 | 480.240845 | 1.530302 |
| zips | 0.324380741 | 1.029935 | Conditional exposure only | Not a workload forecast |
| Actual | 0.352682707 | 2.453336 | 665 | 4.801212 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 480.240845 | 58.833801 | 21.891399 | 1.207900 | 16.632401 | 41.060600 | 0.960500 | 6.723400 | 146.264556 |
| zips | 540.000000 | 71.000000 | 25.000000 | 2.000000 | 20.000000 | 47.000000 | 1.000000 | 10.000000 | 175.165600 |

UBM implied index = 0.303902205 + -0.236630/50.293378039 = 0.299197206. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003130974). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Steer's 2022 AA/AAA record has 23 HR in 492 PA, then only two in 108 MLB PA. UBM index .29920 is below Steamer .30457 and ZiPS .32438, all below actual .35268. UBM also predicts 244 PA versus Steamer 480 and actual 665. Unlike a pure environment-label dispute, both ability translation and readiness remain weak. Actual origin-centered rate 2.45 differs from old 1.91 because league offense rose, but raw event superiority is unambiguous. Carpenter, Jung and Jones also improve; Stowers struggles in 33 PA, preserving unsuccessful comparisons.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Kerry Carpenter | -0.138911 | 0.242525 | 1.954746 | 459 |
| Josh Jung | -0.188421 | -0.450320 | 1.417625 | 515 |
| Kyle Stowers | -0.142760 | 0.061399 | -9.442616 | 33 |
| Nolan Jones | -0.229629 | 0.828628 | 4.319307 | 424 |

## Yordan Alvarez from 2024 to 2025

Player 670541, row 55521, fold 2; age 27.0, elapsed 5. Selection: fixed source diagnostic.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

Origin league index 0.305333851; realized target index 0.308101260. Only the origin enters forecast conversion. Old actual centered rate 0.919648; common-origin actual rate 1.058831.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.380115613 | 3.761027 | 601.307464 | 5.647804 |
| binary | 0.379095125 | 3.709704 | 554.241843 | 5.158329 |
| fixed | 0.390512561 | 4.283925 | 554.241843 | 5.688758 |
| learned | 0.379576663 | 3.733922 | 554.241843 | 5.180700 |
| steamer | 0.395607809 | 4.540182 | 597.687622 | 6.389957 |
| zips | 0.389204255 | 4.218126 | Conditional exposure only | Not a workload forecast |
| Actual | 0.326386935 | 1.058831 | 199 | 0.972887 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 597.687622 | 87.090302 | 30.698500 | 2.215400 | 34.994202 | 72.200699 | 11.356100 | 9.563000 | 236.449891 |
| zips | 611.000000 | 86.000000 | 32.000000 | 2.000000 | 36.000000 | 70.000000 | 11.000000 | 10.000000 | 237.803800 |

UBM implied index = 0.305333851 + 3.709704/50.293378039 = 0.379095125. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003124161). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Alvarez has 37/31/35 HR in the known three MLB years. UBM .37910 is less aggressive than Steamer .39561 and ZiPS .38920, but actual .32639 and only 199 PA disappoint every forecast. UBM's 554 PA is lower than Steamer 598 without forecasting the actual short season. Lower error here is not injury foresight or proof of superior health modeling. Naylor and Hoerner improve among ordinary age/exposure peers, while Arraez is near average and Castro loses production. These peers do not certify elite power reliability.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Willi Castro | -0.383134 | -0.055460 | -0.383400 | 454 |
| Josh Naylor | 1.008427 | 1.337306 | 1.884799 | 604 |
| Nico Hoerner | 0.322637 | 0.496684 | 0.797714 | 649 |
| Luis Arraez | 1.224069 | 1.122616 | 0.005637 | 675 |

## Joey Votto from 2021 to 2022

Player 458015, row 42103, fold 0; age 37.0, elapsed 14. Selection: fixed source diagnostic.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | MLB | 608 | 15 | 123 | 74 |
| 2020 | MLB | 223 | 11 | 43 | 36 |
| 2021 | AAA | 22 | 0 | 5 | 1 |
| 2021 | MLB | 533 | 36 | 127 | 71 |

Origin league index 0.310763804; realized target index 0.303902205. Only the origin enters forecast conversion. Old actual centered rate 0.092638; common-origin actual rate -0.252455.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.325663516 | 0.749357 | 403.835262 | 1.770386 |
| binary | 0.328676752 | 0.900903 | 436.165939 | 2.022287 |
| fixed | 0.349472492 | 1.946791 | 436.165939 | 2.782588 |
| learned | 0.334462694 | 1.191897 | 436.165939 | 2.233823 |
| steamer | 0.347968435 | 1.871147 | 659.077271 | 4.121593 |
| zips | 0.350202053 | 1.983483 | Conditional exposure only | Not a workload forecast |
| Actual | 0.305744149 | -0.252455 | 376 | 1.020556 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 659.077271 | 80.446098 | 25.282000 | 1.645500 | 31.161699 | 90.689003 | 5.272600 | 5.272600 | 229.338087 |
| zips | 487.000000 | 58.000000 | 21.000000 | 1.000000 | 24.000000 | 65.000000 | 4.000000 | 3.000000 | 170.548400 |

UBM implied index = 0.310763804 + 0.900903/50.293378039 = 0.328676752. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003135003). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Votto supplied 36 HR in 533 PA after a short 2020 season, but at the 2021 origin he is an older established player. UBM .32868 is more regressed than Steamer .34797 and ZiPS .35020; actual .30574. UBM's 436 PA is also closer to actual 376 than Steamer 659. This is a genuine measured improvement over the public counts in this case, not a universal aging penalty. Lowrie/Molina decline, Gardner never appears, Turner remains productive. The shorter prior season remains real exposure, not a normal-length failure.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Jed Lowrie | -1.398574 | 0.054826 | -4.193303 | 184 |
| Brett Gardner | -0.497827 | -0.370245 | Unobserved | 0 |
| Justin Turner | 1.052239 | 2.000860 | 1.356981 | 532 |
| Yadier Molina | -1.521560 | -0.879041 | -3.992815 | 270 |

## Vladimir Guerrero Jr. from 2021 to 2022

Player 665489, row 43297, fold 2; age 22.0, elapsed 2. Selection: largest PA-weighted rate gain.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 34 | 3 | 2 | 4 |
| 2019 | Aplus | 17 | 0 | 2 | 1 |
| 2019 | MLB | 514 | 15 | 91 | 46 |
| 2020 | MLB | 243 | 9 | 38 | 19 |
| 2021 | MLB | 698 | 48 | 110 | 79 |

Origin league index 0.310763804; realized target index 0.303902205. Only the origin enters forecast conversion. Old actual centered rate 1.955760; common-origin actual rate 1.610667.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.378727591 | 3.418128 | 596.882393 | 5.271596 |
| binary | 0.380516614 | 3.508104 | 628.681772 | 5.646721 |
| fixed | 0.372406263 | 3.100207 | 628.681772 | 5.219326 |
| learned | 0.367330367 | 2.844924 | 628.681772 | 4.951839 |
| steamer | 0.411537183 | 5.068234 | 656.229553 | 7.600490 |
| zips | 0.403093553 | 4.643575 | Conditional exposure only | Not a workload forecast |
| Actual | 0.342789235 | 1.610667 | 706 | 4.108530 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 656.229553 | 94.465797 | 30.939899 | 1.764000 | 46.153099 | 77.632004 | 5.249800 | 5.906100 | 270.062862 |
| zips | 667.000000 | 100.000000 | 31.000000 | 2.000000 | 43.000000 | 79.000000 | 6.000000 | 5.000000 | 268.863400 |

UBM implied index = 0.310763804 + 3.508104/50.293378039 = 0.380516614. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003135003). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Guerrero's 48 HR in 698 PA follows 15/514 and nine/243. UBM regresses that spike more (.38052) than Steamer (.41154) or ZiPS (.40309); actual is .34279. This is the largest meaningful PA-weighted rate gain over Steamer, though UBM still overestimates ability and undershoots actual 706 PA with 629 expected. Do not infer that all breakouts should be suppressed: Riley improves, Bichette stays productive, Soto declines from forecast and Carlson struggles among origin-selected comparisons.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Bo Bichette | 1.625615 | 2.173516 | 1.575549 | 697 |
| Juan Soto | 4.062867 | 5.359925 | 2.851667 | 664 |
| Dylan Carlson | 1.005466 | 0.667132 | -0.440081 | 488 |
| Austin Riley | 1.947666 | 2.327967 | 2.952235 | 693 |

## Aaron Judge from 2021 to 2022

Player 592450, row 42360, fold 3; age 29.0, elapsed 5. Selection: largest PA-weighted rate harm.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 19 | 1 | 7 | 3 |
| 2019 | MLB | 447 | 27 | 141 | 60 |
| 2020 | MLB | 114 | 9 | 32 | 10 |
| 2021 | MLB | 633 | 39 | 158 | 73 |

Origin league index 0.310763804; realized target index 0.303902205. Only the origin enters forecast conversion. Old actual centered rate 6.560631; common-origin actual rate 6.215538.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.350335629 | 1.990201 | 462.282902 | 2.982651 |
| binary | 0.351436693 | 2.045577 | 526.577288 | 3.446079 |
| fixed | 0.371234918 | 3.041297 | 526.577288 | 4.319951 |
| learned | 0.358291763 | 2.390342 | 526.577288 | 3.748654 |
| steamer | 0.379801361 | 3.472132 | 665.021362 | 5.933247 |
| zips | 0.380499130 | 3.507225 | Conditional exposure only | Not a workload forecast |
| Actual | 0.434349425 | 6.215538 | 696 | 9.391987 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 665.021362 | 87.244797 | 25.778799 | 0.813700 | 41.268600 | 84.258202 | 1.995100 | 5.320200 | 252.576019 |
| zips | 575.000000 | 79.000000 | 22.000000 | 0.000000 | 36.000000 | 71.000000 | 2.000000 | 4.000000 | 218.787000 |

UBM implied index = 0.310763804 + 2.045577/50.293378039 = 0.351436693. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003135003). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Judge's known record is 27/447, nine/114 and 39/633 HR/PA. UBM's .35144 regresses elite power much more than Steamer .37980 and ZiPS .38050, against actual .43435. Expected PA 527 versus Steamer 665 and actual 696 further magnifies the miss. This is the largest meaningful PA-weighted rate harm versus Steamer, and supports the concrete elite-power compression concern rather than cherry-picking a tiny outcome. Frazier/Mancini/Story fall below forecasts while Renfroe improves: exposure peers are not equal power profiles.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Adam Frazier | 0.412989 | -0.290070 | -2.102932 | 602 |
| Trey Mancini | 0.998193 | 0.814142 | -0.183503 | 587 |
| Hunter Renfroe | 0.631672 | 1.171561 | 1.379069 | 522 |
| Trevor Story | 1.421861 | 1.087793 | -0.159703 | 396 |

## Ronald Acuña Jr. from 2023 to 2024

Player 660670, row 51153, fold 3; age 25.0, elapsed 5. Selection: false high contribution.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 360 | 24 | 85 | 47 |
| 2022 | AAA | 25 | 0 | 6 | 5 |
| 2022 | MLB | 533 | 15 | 126 | 49 |
| 2023 | MLB | 735 | 41 | 84 | 77 |

Origin league index 0.314721261; realized target index 0.305333851. Only the origin enters forecast conversion. Old actual centered rate 0.723474; common-origin actual rate 0.251349.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.383210524 | 3.444556 | 611.908421 | 5.407437 |
| binary | 0.382263554 | 3.396930 | 582.562624 | 5.101866 |
| fixed | 0.389864391 | 3.779202 | 582.562624 | 5.473028 |
| learned | 0.380627265 | 3.314636 | 582.562624 | 5.021963 |
| steamer | 0.406075761 | 4.594526 | 695.049011 | 7.474293 |
| zips | 0.412272093 | 4.906161 | Conditional exposure only | Not a workload forecast |
| Actual | 0.319718919 | 0.251349 | 222 | 0.780328 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 695.049011 | 113.865303 | 34.283401 | 2.758100 | 38.093399 | 79.096603 | 3.475200 | 10.425700 | 282.242556 |
| zips | 688.000000 | 99.000000 | 34.000000 | 2.000000 | 43.000000 | 88.000000 | 4.000000 | 11.000000 | 283.643200 |

UBM implied index = 0.314721261 + 3.396930/50.293378039 = 0.382263554. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003096076). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Acuna's source includes a huge 2023 season: 41 HR, 84 K and 77 walks in 735 PA. All systems forecast continued strength, UBM .38226 versus Steamer .40608 and ZiPS .41227. Actual falls to .31972 in 222 PA. UBM is less wrong but still a large false high. Nothing in this no-fit repair anticipates the future reduction in workload. Soto succeeds, Tucker produces strongly with limited PA, Torres declines and Riley declines; uncertainty is real even for highly productive established hitters.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Juan Soto | 3.925638 | 4.476249 | 5.043850 | 713 |
| Kyle Tucker | 2.396499 | 2.795091 | 4.622613 | 339 |
| Gleyber Torres | 0.803387 | 1.236096 | -0.273614 | 665 |
| Austin Riley | 2.564108 | 2.342223 | 0.972059 | 469 |

## Ronald Acuña Jr. from 2022 to 2023

Player 660670, row 47087, fold 3; age 24.0, elapsed 4. Selection: false low contribution.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 202 | 14 | 60 | 36 |
| 2021 | MLB | 360 | 24 | 85 | 47 |
| 2022 | AAA | 25 | 0 | 6 | 5 |
| 2022 | MLB | 533 | 15 | 126 | 49 |

Origin league index 0.303902205; realized target index 0.314721261. Only the origin enters forecast conversion. Old actual centered rate 5.457062; common-origin actual rate 6.001189.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.344638943 | 2.048788 | 489.768225 | 3.205837 |
| binary | 0.345129899 | 2.073480 | 524.118372 | 3.452249 |
| fixed | 0.351224924 | 2.380019 | 524.118372 | 3.720021 |
| learned | 0.339790375 | 1.804937 | 524.118372 | 3.217669 |
| steamer | 0.359162361 | 2.779220 | 682.077087 | 5.294969 |
| zips | 0.368721317 | 3.259972 | Conditional exposure only | Not a workload forecast |
| Actual | 0.423225850 | 6.001189 | 735 | 9.652722 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 682.077087 | 95.494301 | 31.828300 | 1.025000 | 30.102600 | 79.871201 | 4.774500 | 11.595300 | 244.976417 |
| zips | 577.000000 | 81.000000 | 25.000000 | 1.000000 | 29.000000 | 68.000000 | 4.000000 | 10.000000 | 212.752200 |

UBM implied index = 0.303902205 + 2.073480/50.293378039 = 0.345129899. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003130974). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Acuna's known 2022 season is 15 HR/533 PA after 24/360 and 14/202; UBM's .34513 is below Steamer .35916 and ZiPS .36872. Actual .42323 with 735 PA beats all, and UBM's 524 expected PA is well below Steamer 682. This false low is a mix of talent resurgence and opportunity, not a league-environment calculation bug. Torres improves, Urias/Grisham struggle, Lux never appears. Lux's public one-PA forecast while UBM expects 442 illustrates potentially different availability information at the archive date; its exact timestamp is unknown, so do not claim a precisely equal-information comparison.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Gleyber Torres | 0.351837 | 1.244737 | 1.987361 | 672 |
| Luis Urías | 0.577834 | 0.715642 | -0.560186 | 177 |
| Gavin Lux | 0.110527 | 0.778560 | Unobserved | 0 |
| Trent Grisham | 0.112734 | 0.119224 | -0.478424 | 555 |

## Eloy Jiménez from 2022 to 2023

Player 650391, row 46936, fold 4; age 25.0, elapsed 3. Selection: ordinary contribution.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 226 | 14 | 56 | 12 |
| 2021 | AAA | 41 | 1 | 14 | 2 |
| 2021 | Aplus | 8 | 1 | 0 | 1 |
| 2021 | MLB | 231 | 10 | 57 | 16 |
| 2022 | AAA | 63 | 2 | 12 | 6 |
| 2022 | MLB | 327 | 16 | 72 | 28 |

Origin league index 0.303902205; realized target index 0.314721261. Only the origin enters forecast conversion. Old actual centered rate 0.336184; common-origin actual rate 0.880311.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.328028603 | 1.213398 | 441.439249 | 2.274871 |
| binary | 0.329283425 | 1.276507 | 427.714118 | 2.249129 |
| fixed | 0.339756141 | 1.803216 | 427.714118 | 2.624596 |
| learned | 0.326735389 | 1.148358 | 427.714118 | 2.157776 |
| steamer | 0.346817524 | 2.158356 | 605.967346 | 4.077090 |
| zips | 0.341864270 | 1.909240 | Conditional exposure only | Not a workload forecast |
| Actual | 0.321405726 | 0.880311 | 489 | 2.248500 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 605.967346 | 91.882698 | 25.944901 | 0.766600 | 30.969700 | 45.023399 | 0.000000 | 4.847700 | 210.160095 |
| zips | 445.000000 | 68.000000 | 18.000000 | 1.000000 | 23.000000 | 31.000000 | 0.000000 | 2.000000 | 152.129600 |

UBM implied index = 0.303902205 + 1.276507/50.293378039 = 0.329283425. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003130974). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Jimenez supplies 16 HR in 327 MLB PA following 10/231 and 14/226, plus small minor stints. UBM predicts index .32928 versus actual .32141, too optimistic, and 428 PA versus actual 489, too low. Their product gives almost exact contribution (2.249 versus 2.248), so this ordinary value case is a warning about offsetting mistakes, not a perfect projection. Steamer is optimistic in both rate (.34682) and 606 PA. Hiura never appears, Bart struggles, Castro improves, Toro's high rate comes from 21 PA and is not stable talent evidence.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Abraham Toro | -0.788262 | 0.079262 | 11.900500 | 21 |
| Keston Hiura | 0.202736 | -0.458790 | Unobserved | 0 |
| Willi Castro | -0.351599 | -0.719064 | 0.959484 | 409 |
| Joey Bart | -0.380398 | -1.287216 | -3.345468 | 95 |

## Jorge Alfaro from 2023 to 2024

Player 595751, row 50730, fold 3; age 30.0, elapsed 7. Selection: ordinary established elapsed 6plus.

| Source year | Level | PA | HR | K | UBB |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 16 | 2 | 1 | 0 |
| 2021 | MLB | 311 | 4 | 99 | 11 |
| 2022 | AAA | 16 | 2 | 5 | 1 |
| 2022 | MLB | 274 | 7 | 98 | 11 |
| 2023 | AAA | 278 | 7 | 65 | 14 |
| 2023 | MLB | 52 | 1 | 15 | 2 |

Origin league index 0.314721261; realized target index 0.305333851. Only the origin enters forecast conversion. Old actual centered rate 0.000000; common-origin actual rate unobserved.

| Forecast | Event index | Origin centered wins per 600 | PA | Contribution |
|---|---:|---:|---:|---:|
| working | 0.277817724 | -1.856004 | 32.210067 | 0.000088 |
| binary | 0.277732255 | -1.860302 | 79.821450 | -0.000353 |
| fixed | 0.282377831 | -1.626660 | 79.821450 | 0.030729 |
| learned | 0.271041191 | -2.196818 | 79.821450 | -0.045122 |
| steamer | 0.275645679 | -1.965243 | 1.000000 | -0.000179 |
| zips | 0.276158360 | -1.939459 | Conditional exposure only | Not a workload forecast |
| Actual | Unobserved | Unobserved | 0 | 0.000000 |

| Public system | Projected PA | 1B | 2B | 3B | HR | BB | IBB | HBP | Weighted numerator |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| steamer | 1.000000 | 0.147800 | 0.043300 | 0.002700 | 0.023600 | 0.044000 | 0.000000 | 0.015000 | 0.275646 |
| zips | 317.000000 | 48.000000 | 14.000000 | 1.000000 | 7.000000 | 12.000000 | 0.000000 | 6.000000 | 87.542200 |

UBM implied index = 0.314721261 + -1.860302/50.293378039 = 0.277732255. Actual event numerator/counts and source environments remain in cases.json. Contribution = expected PA × (rate/600 + 0.003096076). Prior model fitting/support remains governed by the reviewed V34/V49 artifacts; this no-fit audit does not certify them anew.

Alfaro's MLB work declines from 311 to 274 to 52 PA with low walks and high K, while his 2023 AAA record is 278 PA with seven HR. UBM, Steamer and ZiPS have very similar weak conditional event indexes (.27773/.27565/.27616). Actual next-year MLB PA is zero, so there is no observed .000 hitting talent. UBM's nearly zero contribution arises because its negative batting rate almost cancels replacement despite predicting 80 PA; Steamer predicts one PA. Querecuto/Locastro/Allen also disappear and Gamel returns for 99 PA. Product accuracy cannot certify readiness or justify deleting non-arrivals.

| Origin selected peer | UBM rate | Steamer rate | Actual rate | Actual PA |
|---|---:|---:|---:|---:|
| Juniel Querecuto | -1.562894 | -2.159299 | Unobserved | 0 |
| Tim Locastro | -1.402290 | -2.243799 | Unobserved | 0 |
| Greg Allen | -1.213469 | -1.423971 | Unobserved | 0 |
| Ben Gamel | -0.639596 | -0.500022 | 0.360992 | 99 |

## Decision after review

The existing UBM hitting estimate is plausibly competitive on this fixed-event metric, not certified superior. Broader conditional rate RMSE is 1.74524 versus Steamer 1.77459 and ZiPS 1.75336; legacy-only 1.76092 versus 1.78377 and 1.75262. Target 2023 loses to both public systems. Timing, selection, parks, fixed weights and repeated development exposure prevent a blanket superiority claim.

Playing time remains the clearer issue: broader binary PA RMSE 138.28 versus Steamer 135.38; MAE 106.79 versus 92.08. Public one-PA rows explain a substantial part of the MAE gap (52.58 versus 11.12 within that group), but excluding them would change the question. On the remaining diagnostic group MAE is 115.50 versus 106.23. Potentially different availability information is concrete, not proof that UBM already solves it.

Retain existing talent plus qualified binary readiness as the coherent development candidate. Do not replace talent with V50. Prospect fast entry, elite-power compression, availability and translated/contextual talent remain visible gaps. Finish a concise practical candidate handoff and benchmark dashboard; do not launch another undirected algorithm tournament. No frozen forecast change or protected outcomes.
