# V41 source walkthrough completed before fitting

Raw contact measurements, distinct league buckets, source/missingness and official-count corroboration. No forecast or protected outcomes in this source checkpoint.

Unreconciled player/league/seasons: 953; raw contacts excluded from this predictor: 78,688. Player eligibility and their official batting predictors stay unchanged. Four ambiguous 2023 PA keys are also quarantined. The old artifacts are retained; this does not certify or repair their every source join.

## Aaron Judge, origin 2016

His 2016 AAA contact is now observed, not missing as in the modern-only table. Its 257 weighted contacts support descriptive shape, but no contact training exists before this cutoff: both challengers must retain the baseline. MLB shape is unobserved here, not zero talent.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 59 | 38 | 9 |
| 2014 | Aplus | 285 | 72 | 49 | 8 |
| 2015 | AA | 280 | 70 | 23 | 12 |
| 2015 | AAA | 260 | 74 | 29 | 8 |
| 2016 | AAA | 410 | 98 | 47 | 19 |
| 2016 | MLB | 95 | 42 | 9 | 4 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| AAA | 257.000 | 0.41586 | 0.07283 | 0.32213 |

Origin-selected peers (no future outcomes used): Kaleb Cowart age 24.0, MLB/AAA/AA PA 87/458.0/0.0; Jaff Decker age 26.0, MLB/AAA/AA PA 57/417.0/0.0; Deven Marrero age 25.0, MLB/AAA/AA PA 14/388.0/0.0.

## Aaron Judge, origin 2024

Three years of MLB contact are available, unlike the minor-only gradient table. The approximately 807 weighted contacts give substantial shape evidence. These are ground/fly/direction labels, not a direct measurement of exit velocity or a replacement for his established home-run production.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 175 | 92 | 62 |
| 2023 | MLB | 458 | 130 | 79 | 37 |
| 2024 | MLB | 704 | 171 | 113 | 58 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| MLB | 807.400 | 0.54261 | 0.08574 | 0.32973 |

Origin-selected peers (no future outcomes used): Nick Castellanos age 32.0, MLB/AAA/AA PA 659/0.0/0.0; Matt Chapman age 31.0, MLB/AAA/AA PA 647/0.0/0.0; Matt Olson age 30.0, MLB/AAA/AA PA 685/0.0/0.0.

## Masyn Winn, origin 2023

Current brief MLB contact and larger AAA/AA histories remain in distinct buckets. The 100-contact prior strongly moderates his short MLB debut. A contact forecast must not discard stronger minor production merely because a few major-league balls were recorded.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 60 | 40 | 3 |
| 2021 | Aplus | 154 | 40 | 6 | 2 |
| 2022 | AA | 403 | 86 | 50 | 11 |
| 2022 | Aplus | 147 | 29 | 13 | 1 |
| 2023 | AAA | 498 | 83 | 44 | 18 |
| 2023 | MLB | 137 | 26 | 10 | 2 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| MLB | 95.000 | 0.69343 | 0.07179 | 0.38974 |
| AAA | 362.000 | 0.72691 | 0.06277 | 0.37662 |
| AA | 209.600 | 0.65012 | 0.08140 | 0.38372 |
| Aplus | 145.400 | 0.69238 | 0.07172 | 0.39772 |
| A | 107.400 | 0.63028 | 0.06268 | 0.35583 |

Origin-selected peers (no future outcomes used): Parker Meadows age 23.0, MLB/AAA/AA PA 145/517.0/0.0; Xavier Edwards age 23.0, MLB/AAA/AA PA 84/433.0/0.0; Jonathan Ornelas age 23.0, MLB/AAA/AA PA 8/517.0/0.0.

## Spencer Steer, origin 2022

The source retains both minor contact histories and the brief major debut. His AA fraction slightly exceeded BABIP opportunities in the first diagnostic; PA is the correct finite upper bound for this measurement fraction. This is not a retrospective promotion signal.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 73 | 19 | 14 |
| 2021 | Aplus | 208 | 32 | 35 | 10 |
| 2022 | AA | 156 | 23 | 14 | 8 |
| 2022 | AAA | 336 | 66 | 36 | 15 |
| 2022 | MLB | 108 | 26 | 11 | 2 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| MLB | 65.000 | 0.60185 | 0.07879 | 0.36364 |
| AAA | 225.000 | 0.66964 | 0.09231 | 0.40000 |
| AA | 261.400 | 0.68789 | 0.12120 | 0.30825 |
| Aplus | 108.800 | 0.65385 | 0.12452 | 0.27778 |

Origin-selected peers (no future outcomes used): Will Brennan age 24.0, MLB/AAA/AA PA 45/433.0/157.0; Gunnar Henderson age 21.0, MLB/AAA/AA PA 132/295.0/208.0; Tyler Freeman age 23.0, MLB/AAA/AA PA 86/343.0/0.0.

## Nick Kurtz, origin 2024

There are only 18 A and 10 AA contacts. The displayed probabilities are heavily prior-driven, not estimates of mature MLB talent. The larger upper-minor samples of other players cannot be assigned to him by confidence; pedigree remains in the unchanged count backbone.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 7 | 10 | 4 |
| 2024 | AA | 15 | 3 | 2 | 0 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| AA | 10.000 | 0.66667 | 0.09091 | 0.33636 |
| A | 18.000 | 0.51429 | 0.10169 | 0.31356 |

Origin-selected peers (no future outcomes used): Termarr Johnson age 20.0, MLB/AAA/AA PA 0/0.0/57.0; Benny Montgomery age 21.0, MLB/AAA/AA PA 0/0.0/48.0; Walker Jenkins age 19.0, MLB/AAA/AA PA 0/0.0/28.0.

## Gavin Lux, origin 2023

A missed current year does not erase prior MLB contact. Recency-weighted 2021/22 evidence remains usable. The source cannot explain why he missed the year or assert his future health; workload is deliberately fixed.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 15 | 6 | 1 |
| 2021 | MLB | 381 | 83 | 38 | 7 |
| 2022 | MLB | 471 | 95 | 47 | 6 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| MLB | 408.000 | 0.67393 | 0.05551 | 0.45630 |
| AAA | 31.800 | 0.71622 | 0.08498 | 0.35053 |

Origin-selected peers (no future outcomes used): Nick Plummer age 26.0, MLB/AAA/AA PA 0/0.0/0.0; Nick Ciuffo age 28.0, MLB/AAA/AA PA 0/0.0/0.0; Will Craig age 28.0, MLB/AAA/AA PA 0/0.0/0.0.

## Chase Meidroth, origin 2024

The larger AAA and preceding AA histories have ample measured contact. A high ground-ball share and few pulled flies are not automatically bad hitting: his walk/strikeout/extra-base production remains supplied separately and the future-MLB test decides whether shape adds signal.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2022 | A | 85 | 9 | 12 | 4 |
| 2022 | RK124 | 11 | 2 | 2 | 0 |
| 2023 | AA | 396 | 78 | 59 | 7 |
| 2023 | Aplus | 97 | 20 | 21 | 2 |
| 2024 | AAA | 558 | 71 | 105 | 7 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| AAA | 371.000 | 0.66487 | 0.04883 | 0.45648 |
| AA | 198.400 | 0.62626 | 0.06836 | 0.44370 |
| Aplus | 43.200 | 0.55670 | 0.07542 | 0.38827 |
| A | 36.000 | 0.70588 | 0.07794 | 0.31765 |
| RK124 | 3.000 | 0.45455 | 0.09709 | 0.30874 |

Origin-selected peers (no future outcomes used): Owen Caissie age 21.0, MLB/AAA/AA PA 0/549.0/0.0; Tristan Peters age 24.0, MLB/AAA/AA PA 0/478.0/0.0; Grant Lavigne age 24.0, MLB/AAA/AA PA 0/530.0/0.0.

## Cody Bellinger, origin 2016

AA and short AAA contact are observed, unlike the modern-only source. They cannot train a relationship before contact history begins, so the 2016 forecast stays exact baseline. This source repair alone cannot fix his low projected first-year MLB opportunity.

| Year | League | PA | K | UBB | HR |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 40 | 15 | 3 |
| 2015 | Aplus | 544 | 150 | 51 | 30 |
| 2016 | AA | 465 | 94 | 57 | 23 |
| 2016 | AAA | 12 | 0 | 1 | 3 |

| Bucket | Weighted contacts | Measured/PA | Pull fly share | GB share |
|---|---:|---:|---:|---:|
| AAA | 11.000 | 0.91667 | 0.11712 | 0.28829 |
| AA | 300.000 | 0.64516 | 0.12250 | 0.28750 |

Origin-selected peers (no future outcomes used): Isiah Kiner-Falefa age 21.0, MLB/AAA/AA PA 0/0.0/457.0; Jamie Westbrook age 21.0, MLB/AAA/AA PA 0/0.0/473.0; Kean Wong age 21.0, MLB/AAA/AA PA 0/0.0/492.0.

## Interpretation

The raw ten-bin shape records use coordinate-based direction and scorer/trajectory labels. Cross-level measurement equivalence is not assumed; distinct buckets, measured PA fractions and exposure are supplied. The new forecast test—not this audit—will decide transfer utility. Pre-2016 minor and pre-2021 MLB shape remain unobserved. Rows/buckets with no relevant active-player training support get exact baseline fallbacks.
