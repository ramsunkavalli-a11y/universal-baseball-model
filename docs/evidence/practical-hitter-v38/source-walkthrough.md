# V38 game-source review, before fitting

All 122,799 existing stints reconcile PA exactly; gamesPlayed is available for every stint. No positive PA with zero games, no negative games, no conflicting keyed captures or more than 12 PA/appearance. All old features remain bit-exact. These are team appearances, not dated starts, healthy days or diagnosed absences. No 2026 outcomes.

Fixed cases and three origin-only peers per case. Distance uses age, current MLB/AAA/AA PA and draft evidence, within the same origin/stage/debut group. Outcomes are not used in source selection.

## Aaron Judge: origin 2016

95 MLB PA in 27 games produce stabilized 3.649 PA/appearance, versus AAA 410 PA/93 games (4.369). The complete current participation is 120 team appearances across the two levels, not 27 days of availability or an injury diagnosis. Cowart, Decker and Marrero are origin-selected brief-MLB/long-AAA contrasts; Decker's fewer PA/game illustrates a different MLB role. These features may distinguish use, but do not establish next year's job or Judge's later breakout.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 543094 | 2014 | AAA | 409 | 104 | 3.933 |
| 543094 | 2014 | MLB | 5 | 5 | 1.000 |
| 571918 | 2014 | AA | 307 | 68 | 4.515 |
| 571918 | 2014 | AAA | 202 | 50 | 4.040 |
| 592230 | 2014 | AA | 487 | 126 | 3.865 |
| 592450 | 2014 | A | 278 | 65 | 4.277 |
| 592450 | 2014 | Aplus | 285 | 66 | 4.318 |
| 543094 | 2015 | AAA | 265 | 69 | 3.841 |
| 543094 | 2015 | MLB | 36 | 23 | 1.565 |
| 571918 | 2015 | AAA | 419 | 102 | 4.108 |
| 571918 | 2015 | MLB | 56 | 25 | 2.240 |
| 592230 | 2015 | AAA | 253 | 62 | 4.081 |
| 592230 | 2015 | Aplus | 221 | 51 | 4.333 |
| 592230 | 2015 | MLB | 52 | 34 | 1.529 |
| 592450 | 2015 | AA | 280 | 63 | 4.444 |
| 592450 | 2015 | AAA | 260 | 61 | 4.262 |
| 543094 | 2016 | AAA | 417 | 99 | 4.212 |
| 543094 | 2016 | MLB | 57 | 19 | 3.000 |
| 571918 | 2016 | AAA | 388 | 96 | 4.042 |
| 571918 | 2016 | MLB | 14 | 13 | 1.077 |
| 592230 | 2016 | AAA | 458 | 107 | 4.280 |
| 592230 | 2016 | MLB | 87 | 31 | 2.806 |
| 592450 | 2016 | AAA | 410 | 93 | 4.409 |
| 592450 | 2016 | MLB | 95 | 27 | 3.519 |

Actual new inputs: games_mlb_0=27, role_mlb_0=3.6486, games_minor_0=93, role_minor_0=4.3689, games_mlb_1=0, role_mlb_1=4, games_minor_1=124, role_minor_1=4.3284, games_mlb_2=0, role_mlb_2=4, games_minor_2=131, role_minor_2=4.2766, games_pool_MLB=27, role_pool_MLB=3.6486, games_pool_AAA=141.8, role_pool_AAA=4.3347, games_pool_AA=50.4, role_pool_AA=4.3709, games_pool_Aplus=39.6, role_pool_Aplus=4.254, games_pool_A=39, role_pool_A=4.2204, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Aaron Judge: origin 2024

704 PA/158 MLB games gives stabilized 4.429 PA/appearance. The previous 458/106 and 696/157 seasons remain separate, preserving both regular role and varying participation. Castellanos, Chapman and Olson are similar age/workload contrasts. All regular use does not imply a guaranteed future 600-plus PA or no injury risk; a trade can also make summed team games exceed the usual schedule.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 592206 | 2022 | MLB | 558 | 136 | 4.103 |
| 592450 | 2022 | MLB | 696 | 157 | 4.433 |
| 621566 | 2022 | MLB | 699 | 162 | 4.315 |
| 656305 | 2022 | MLB | 621 | 155 | 4.006 |
| 592206 | 2023 | MLB | 671 | 157 | 4.274 |
| 592450 | 2023 | MLB | 458 | 106 | 4.321 |
| 621566 | 2023 | MLB | 720 | 162 | 4.444 |
| 656305 | 2023 | MLB | 581 | 140 | 4.150 |
| 592206 | 2024 | MLB | 659 | 162 | 4.068 |
| 592450 | 2024 | MLB | 704 | 158 | 4.456 |
| 621566 | 2024 | MLB | 685 | 162 | 4.228 |
| 656305 | 2024 | MLB | 647 | 154 | 4.201 |

Actual new inputs: games_mlb_0=158, role_mlb_0=4.4286, games_minor_0=0, role_minor_0=4, games_mlb_1=106, role_mlb_1=4.2931, games_minor_1=0, role_minor_1=4, games_mlb_2=157, role_mlb_2=4.4072, games_minor_2=0, role_minor_2=4, games_pool_MLB=337, role_pool_MLB=4.4035, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Masyn Winn: origin 2023

Current 498 AAA PA/105 games plus 137 MLB PA/37 games show sustained participation and mostly regular appearances in both leagues. Stabilized AAA ratio is 4.678, MLB 3.766. Meadows also has 37 MLB games but 145 PA; Edwards has 84/30, Ornelas 8/8. Games add role information beyond the PA totals, but they cannot certify dates or future starting assignments. This source supplies no actual innings/starts or injury cause.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 669364 | 2021 | AA | 337 | 79 | 4.266 |
| 678009 | 2021 | A | 12 | 3 | 4.000 |
| 678009 | 2021 | Aplus | 408 | 94 | 4.340 |
| 680716 | 2021 | Aplus | 405 | 94 | 4.309 |
| 691026 | 2021 | A | 284 | 61 | 4.656 |
| 691026 | 2021 | Aplus | 154 | 37 | 4.162 |
| 669364 | 2022 | AAA | 400 | 93 | 4.301 |
| 678009 | 2022 | AA | 489 | 113 | 4.327 |
| 678009 | 2022 | Aplus | 67 | 14 | 4.786 |
| 680716 | 2022 | AA | 580 | 123 | 4.715 |
| 691026 | 2022 | AA | 403 | 86 | 4.686 |
| 691026 | 2022 | Aplus | 147 | 33 | 4.455 |
| 669364 | 2023 | AAA | 433 | 93 | 4.656 |
| 669364 | 2023 | MLB | 84 | 30 | 2.800 |
| 678009 | 2023 | AAA | 517 | 113 | 4.575 |
| 678009 | 2023 | MLB | 145 | 37 | 3.919 |
| 680716 | 2023 | AAA | 517 | 114 | 4.535 |
| 680716 | 2023 | MLB | 8 | 8 | 1.000 |
| 691026 | 2023 | AAA | 498 | 105 | 4.743 |
| 691026 | 2023 | MLB | 137 | 37 | 3.703 |

Actual new inputs: games_mlb_0=37, role_mlb_0=3.766, games_minor_0=105, role_minor_0=4.6783, games_mlb_1=0, role_mlb_1=4, games_minor_1=119, role_minor_1=4.5736, games_mlb_2=0, role_mlb_2=4, games_minor_2=98, role_minor_2=4.4259, games_pool_MLB=37, role_pool_MLB=3.766, games_pool_AAA=105, role_pool_AAA=4.6783, games_pool_AA=68.8, role_pool_AA=4.599, games_pool_Aplus=48.6, role_pool_Aplus=4.2662, games_pool_A=36.6, role_pool_A=4.515, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Spencer Steer: origin 2022

156 AA PA/35 games, 336 AAA PA/71 games and 108 MLB PA/28 games preserve an advancing season. Aggregate minor ratio is 4.586 and MLB 3.895. Brennan, Henderson and Freeman have similar advancing exposure, selected without subsequent outcomes. A late promotion followed by continued play differs from a full-season low-volume role, but summed season counts alone do not locate the promotion date or identify next-year roster competition.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 668715 | 2021 | AA | 280 | 65 | 4.308 |
| 668715 | 2021 | Aplus | 208 | 45 | 4.622 |
| 671289 | 2021 | AA | 180 | 41 | 4.390 |
| 683002 | 2021 | A | 157 | 35 | 4.486 |
| 683002 | 2021 | AA | 17 | 5 | 3.400 |
| 683002 | 2021 | Aplus | 289 | 65 | 4.446 |
| 686823 | 2021 | AA | 177 | 40 | 4.425 |
| 686823 | 2021 | Aplus | 269 | 62 | 4.339 |
| 668715 | 2022 | AA | 156 | 35 | 4.457 |
| 668715 | 2022 | AAA | 336 | 71 | 4.732 |
| 668715 | 2022 | MLB | 108 | 28 | 3.857 |
| 671289 | 2022 | AAA | 343 | 72 | 4.764 |
| 671289 | 2022 | MLB | 86 | 24 | 3.583 |
| 683002 | 2022 | AA | 208 | 47 | 4.426 |
| 683002 | 2022 | AAA | 295 | 65 | 4.538 |
| 683002 | 2022 | MLB | 132 | 34 | 3.882 |
| 686823 | 2022 | AA | 157 | 36 | 4.361 |
| 686823 | 2022 | AAA | 433 | 93 | 4.656 |
| 686823 | 2022 | MLB | 45 | 11 | 4.091 |

Actual new inputs: games_mlb_0=28, role_mlb_0=3.8947, games_minor_0=106, role_minor_0=4.5862, games_mlb_1=0, role_mlb_1=4, games_minor_1=110, role_minor_1=4.4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=28, role_pool_MLB=3.8947, games_pool_AAA=71, role_pool_AAA=4.642, games_pool_AA=87, role_pool_AA=4.3299, games_pool_Aplus=36, role_pool_Aplus=4.487, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Nick Kurtz: origin 2024

35 A PA/7 games and 15 AA PA/5 games give 50 total PA/12 minor games, stabilized 4.091 PA/appearance. With no MLB games, the role ratio is exactly its prior 4 while exposure stays zero: this is not observed MLB regular use. Johnson, Montgomery and Jenkins share age/draft/AA exposure to varying degrees; peer matching is not a precise draft-age/college-timing comparison. The short first professional season must not be labeled poor durability; existing draft year and class stay available.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 695603 | 2022 | A | 264 | 56 | 4.714 |
| 695603 | 2022 | RK121 | 22 | 6 | 3.667 |
| 702261 | 2022 | A | 53 | 14 | 3.786 |
| 702261 | 2022 | RK124 | 29 | 9 | 3.222 |
| 695603 | 2023 | Aplus | 497 | 109 | 4.560 |
| 702261 | 2023 | A | 330 | 75 | 4.400 |
| 702261 | 2023 | Aplus | 132 | 30 | 4.400 |
| 805805 | 2023 | A | 56 | 12 | 4.667 |
| 805805 | 2023 | RK124 | 59 | 14 | 4.214 |
| 695603 | 2024 | AA | 48 | 11 | 4.364 |
| 701762 | 2024 | A | 35 | 7 | 5.000 |
| 701762 | 2024 | AA | 15 | 5 | 3.000 |
| 702261 | 2024 | AA | 57 | 14 | 4.071 |
| 702261 | 2024 | Aplus | 487 | 110 | 4.427 |
| 805805 | 2024 | A | 151 | 33 | 4.576 |
| 805805 | 2024 | AA | 28 | 6 | 4.667 |
| 805805 | 2024 | Aplus | 152 | 34 | 4.471 |
| 805805 | 2024 | RK124 | 37 | 9 | 4.111 |

Actual new inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=12, role_minor_0=4.0909, games_mlb_1=0, role_mlb_1=4, games_minor_1=0, role_minor_1=4, games_mlb_2=0, role_mlb_2=4, games_minor_2=0, role_minor_2=4, games_pool_MLB=0, role_pool_MLB=4, games_pool_AAA=0, role_pool_AAA=4, games_pool_AA=5, role_pool_AA=3.6667, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=7, role_pool_A=4.4118, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Gavin Lux: origin 2023

Current MLB and minor games/PA are zero; role ratios fall back to 4 with zero games exposure. Prior MLB records 381/102 and 471/129 survive in lagged features. The counts alone do not distinguish known medical absence from retirement, suspension or foreign play. Plummer, Ciuffo and Craig are origin-selected inactive contrasts, not medical-return analogues. No injury interpretation or missing-history zeroing has been added.

| Player ID | Year | League | PA | Games | Raw PA/game |
|---:|---:|---|---:|---:|---:|
| 624419 | 2021 | AAA | 58 | 17 | 3.412 |
| 624419 | 2021 | MLB | 6 | 2 | 3.000 |
| 643269 | 2021 | AAA | 139 | 33 | 4.212 |
| 643269 | 2021 | MLB | 65 | 18 | 3.611 |
| 663911 | 2021 | AA | 376 | 90 | 4.178 |
| 663911 | 2021 | AAA | 102 | 27 | 3.778 |
| 666158 | 2021 | AAA | 74 | 17 | 4.353 |
| 666158 | 2021 | MLB | 381 | 102 | 3.735 |
| 624419 | 2022 | AAA | 151 | 42 | 3.595 |
| 663911 | 2022 | AAA | 270 | 65 | 4.154 |
| 663911 | 2022 | MLB | 31 | 14 | 2.214 |
| 666158 | 2022 | MLB | 471 | 129 | 3.651 |

Actual new inputs: games_mlb_0=0, role_mlb_0=4, games_minor_0=0, role_minor_0=4, games_mlb_1=129, role_mlb_1=3.6763, games_minor_1=0, role_minor_1=4, games_mlb_2=102, role_mlb_2=3.7589, games_minor_2=17, role_minor_2=4.2222, games_pool_MLB=164.4, role_pool_MLB=3.7007, games_pool_AAA=10.2, role_pool_AAA=4.1782, games_pool_AA=0, role_pool_AA=4, games_pool_Aplus=0, role_pool_Aplus=4, games_pool_A=0, role_pool_A=4, games_pool_Aminus=0, role_pool_Aminus=4, games_pool_DSL=0, role_pool_DSL=4, games_pool_RK120=0, role_pool_RK120=4, games_pool_RK121=0, role_pool_RK121=4, games_pool_RK124=0, role_pool_RK124=4, games_pool_RK128=0, role_pool_RK128=4, games_pool_RK134=0, role_pool_RK134=4, games_pool_RKother=0, role_pool_RKother=4, games_pool_MEX=0, role_pool_MEX=4.

## Scope and disposition

Source extraction is usable for the fixed model comparison. This is not a predictive win. Aggregate games cannot measure healthy-days fractions, date of promotion, actual starts or guarantee a future job. Existing foreign/inactive and historical roster qualifications remain. MLB 2020 exposure alone is schedule-scaled 162/60; no canceled minor games are invented. Proceed to the one predeclared workload fit, retaining existing batting rates and every test row.
