# Shared hitting evidence: completed player review

Fixed original rates versus one shared event-opportunity denominator. Identical players, targets and model settings. Separate rate-only, PA-only and combined products. Next-year MLB batting-plus-replacement contribution, not full WAR. Every saved head replays; this does not establish predictive success.

Nine fixed cases plus each product largest gain/harm, false high/low and ordinary example. Peers use origin year/stage/debut, age, MLB/upper-minor PA, observed quality and draft rank without future outcomes. Missing school/health matching limits certain peer interpretations.

## Jeff McNeil: 2018 to 2019

Selection: Predeclared diagnostic.

Age 26; MLB PA 248/0/0; draft pick 356, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 14 | 1 | 1 | 2 |
| 2017 | AAA | 78 | 1 | 10 | 3 |
| 2017 | Aplus | 116 | 3 | 19 | 6 |
| 2018 | AA | 241 | 14 | 23 | 21 |
| 2018 | AAA | 143 | 5 | 19 | 13 |
| 2018 | MLB | 248 | 3 | 24 | 13 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 24.00 | 248.00 | 795.60 | 0.2300 | 0.135057 | 0.193109 |
| AAA/K | 27.00 | 205.40 | 795.60 | 0.2300 | 0.163720 | 0.207398 |
| AA/K | 23.60 | 249.40 | 795.60 | 0.2300 | 0.133371 | 0.192302 |
| Aplus/K | 15.20 | 92.80 | 795.60 | 0.2300 | 0.198133 | 0.223140 |
| MLB/BB | 13.00 | 248.00 | 795.60 | 0.0800 | 0.060345 | 0.072363 |
| AAA/BB | 15.40 | 205.40 | 795.60 | 0.0800 | 0.076621 | 0.078848 |
| AA/BB | 22.20 | 249.40 | 795.60 | 0.0800 | 0.086434 | 0.082510 |
| Aplus/BB | 4.80 | 92.80 | 795.60 | 0.0800 | 0.066390 | 0.077070 |
| MLB/HBP | 5.00 | 248.00 | 795.60 | 0.0100 | 0.017241 | 0.012814 |
| AAA/HBP | 2.60 | 205.40 | 795.60 | 0.0100 | 0.011788 | 0.010610 |
| AA/HBP | 5.00 | 249.40 | 795.60 | 0.0100 | 0.017172 | 0.012798 |
| Aplus/HBP | 3.20 | 92.80 | 795.60 | 0.0100 | 0.021784 | 0.012537 |
| MLB/HR | 3.00 | 248.00 | 795.60 | 0.0300 | 0.017241 | 0.025042 |
| AAA/HR | 5.80 | 205.40 | 795.60 | 0.0300 | 0.028815 | 0.029596 |
| AA/HR | 14.60 | 249.40 | 795.60 | 0.0300 | 0.050372 | 0.037948 |
| Aplus/HR | 2.40 | 92.80 | 795.60 | 0.0300 | 0.028008 | 0.029571 |
| MLB/BABIP | 71.00 | 198.00 | 601.00 | 0.3000 | 0.338926 | 0.316548 |
| AAA/BABIP | 54.60 | 153.60 | 601.00 | 0.3000 | 0.333596 | 0.312154 |
| AA/BABIP | 57.20 | 183.00 | 601.00 | 0.3000 | 0.308127 | 0.303281 |
| Aplus/BABIP | 24.80 | 66.40 | 601.00 | 0.3000 | 0.329327 | 0.306961 |
| MLB/2B | 11.00 | 248.00 | 795.60 | 0.0500 | 0.045977 | 0.048437 |
| AAA/2B | 14.00 | 205.40 | 795.60 | 0.0500 | 0.062213 | 0.054165 |
| AA/2B | 16.60 | 249.40 | 795.60 | 0.0500 | 0.061820 | 0.054611 |
| Aplus/2B | 5.60 | 92.80 | 795.60 | 0.0500 | 0.054979 | 0.051072 |
| MLB/3B | 6.00 | 248.00 | 795.60 | 0.0050 | 0.018678 | 0.010315 |
| AAA/3B | 2.00 | 205.40 | 795.60 | 0.0050 | 0.008186 | 0.006086 |
| AA/3B | 3.00 | 249.40 | 795.60 | 0.0050 | 0.010017 | 0.006957 |
| Aplus/3B | 0.00 | 92.80 | 795.60 | 0.0050 | 0.002593 | 0.004482 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 399.170 | -0.22474 | 1.07943 |
| rate_only | 399.170 | -0.21562 | 1.08550 |
| pa_only | 373.566 | -0.22474 | 1.01020 |
| shared | 373.566 | -0.21562 | 1.01588 |
| Actual | 567 | 3.35684 | 4.90426 |

Product uses PA × (rate/600 + origin replacement 0.0030788), not a joint predictive distribution.

Saved rate intercept -0.837613; fixed-old-model/new-encoding probe -0.208477. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.41986 | 0.41986 | 0.7263458 | 0.30496 |
| work_0 | 247.89798 | 247.89798 | 0.0008007 | 0.19849 |
| quality_0 | 0.41986 | 0.41986 | 0.4333183 | 0.18193 |
| position_4 | 1.00000 | 1.00000 | -0.1572398 | -0.15724 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1489985 | -0.14900 |
| prior_debut | 1.00000 | 1.00000 | 0.1223216 | 0.12232 |
| on_40man | 1.00000 | 1.00000 | 0.1090051 | 0.10901 |
| age_centered | -0.20000 | -0.20000 | -0.5425516 | 0.10851 |
| pooled_AA_K | 0.19230 | -0.37698 | 0.2091594 | -0.07885 |
| draft_known | 1.00000 | 1.00000 | 0.0699029 | 0.06990 |
| pooled_AA_pa | 249.40000 | 0.41567 | -0.1660513 | -0.06902 |
| pooled_AAA_K | 0.20740 | -0.22602 | 0.1533792 | -0.03467 |

The strong contact record is real: 24 K in 248 MLB PA and 23/19 K in 241 AA/143 AAA PA. Shared K deviations sum correctly, but the unchanged legacy MLB quality and workload features still dominate the linear estimate. Conditional rate barely rises −0.225→−0.216 while PA falls 399→374, worsening value. Mullins and O'Brien fail while Lowe succeeds, so this is not evidence every good-contact brief debut deserves McNeil's outcome. The proposed representation does not fix this miss.

Origin-selected peers: Cedric Mullins (age 23, MLB/AAA/AA PA 191/269.0/218.0; actual next 74 PA/-0.798 wins); Brandon Lowe (age 23, MLB/AAA/AA PA 148/205.0/240.0; actual next 327 PA/2.038 wins); Peter O'Brien (age 27, MLB/AAA/AA PA 74/135.0/286.0; actual next 47 PA/-0.191 wins).

Training profile: all=354 distinct people; active=279 distinct people.

## Spencer Steer: 2022 to 2023

Selection: Predeclared diagnostic.

Age 24; MLB PA 108/0/0; draft pick 90, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 26.00 | 108.00 | 990.40 | 0.2300 | 0.235577 | 0.231064 |
| AAA/K | 66.00 | 336.00 | 990.40 | 0.2300 | 0.204128 | 0.219655 |
| AA/K | 81.40 | 380.00 | 990.40 | 0.2300 | 0.217500 | 0.224497 |
| Aplus/K | 25.60 | 166.40 | 990.40 | 0.2300 | 0.182432 | 0.218379 |
| MLB/BB | 11.00 | 108.00 | 990.40 | 0.0800 | 0.091346 | 0.082164 |
| AAA/BB | 36.00 | 336.00 | 990.40 | 0.0800 | 0.100917 | 0.088364 |
| AA/BB | 29.20 | 380.00 | 990.40 | 0.0800 | 0.077500 | 0.078899 |
| Aplus/BB | 28.00 | 166.40 | 990.40 | 0.0800 | 0.135135 | 0.093470 |
| MLB/HBP | 2.00 | 108.00 | 990.40 | 0.0100 | 0.014423 | 0.010844 |
| AAA/HBP | 7.00 | 336.00 | 990.40 | 0.0100 | 0.018349 | 0.013338 |
| AA/HBP | 8.00 | 380.00 | 990.40 | 0.0100 | 0.018750 | 0.013852 |
| Aplus/HBP | 3.20 | 166.40 | 990.40 | 0.0100 | 0.015766 | 0.011409 |
| MLB/HR | 2.00 | 108.00 | 990.40 | 0.0300 | 0.024038 | 0.028863 |
| AAA/HR | 15.00 | 336.00 | 990.40 | 0.0300 | 0.041284 | 0.034512 |
| AA/HR | 19.20 | 380.00 | 990.40 | 0.0300 | 0.046250 | 0.037153 |
| Aplus/HR | 8.00 | 166.40 | 990.40 | 0.0300 | 0.041291 | 0.032759 |
| MLB/BABIP | 18.00 | 67.00 | 621.00 | 0.3000 | 0.287425 | 0.297087 |
| AAA/BABIP | 60.00 | 211.00 | 621.00 | 0.3000 | 0.289389 | 0.295423 |
| AA/BABIP | 70.80 | 241.40 | 621.00 | 0.3000 | 0.295255 | 0.297753 |
| Aplus/BABIP | 28.80 | 101.60 | 621.00 | 0.3000 | 0.291667 | 0.297670 |
| MLB/2B | 5.00 | 108.00 | 990.40 | 0.0500 | 0.048077 | 0.049633 |
| AAA/2B | 17.00 | 336.00 | 990.40 | 0.0500 | 0.050459 | 0.050183 |
| AA/2B | 21.80 | 380.00 | 990.40 | 0.0500 | 0.055833 | 0.052568 |
| Aplus/2B | 5.60 | 166.40 | 990.40 | 0.0500 | 0.039790 | 0.047506 |
| MLB/3B | 0.00 | 108.00 | 990.40 | 0.0050 | 0.002404 | 0.004505 |
| AAA/3B | 1.00 | 336.00 | 990.40 | 0.0050 | 0.003440 | 0.004376 |
| AA/3B | 2.60 | 380.00 | 990.40 | 0.0050 | 0.006458 | 0.005642 |
| Aplus/3B | 0.80 | 166.40 | 990.40 | 0.0050 | 0.004880 | 0.004971 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 180.375 | -0.23663 | 0.49361 |
| rate_only | 180.375 | -0.36647 | 0.45458 |
| pa_only | 181.449 | -0.23663 | 0.49655 |
| shared | 181.449 | -0.36647 | 0.45728 |
| Actual | 665 | 1.90921 | 4.17493 |

Product uses PA × (rate/600 + origin replacement 0.0031310), not a joint predictive distribution.

Saved rate intercept -0.818235; fixed-old-model/new-encoding probe -0.448672. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.5986411 | 0.35918 |
| work_0 | 108.00000 | 108.00000 | 0.0014877 | 0.16067 |
| reorganized | 1.00000 | 1.00000 | -0.1305155 | -0.13052 |
| position_5 | 1.00000 | 1.00000 | 0.1299457 | 0.12995 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1126830 | -0.11268 |
| prior_debut | 1.00000 | 1.00000 | 0.0892117 | 0.08921 |
| pooled_mlb_quality | -0.08442 | -0.08442 | 0.7977087 | -0.06735 |
| pooled_AA_pa | 380.00000 | 0.63333 | -0.0960086 | -0.06081 |
| AA_1_pa | 280.00000 | 0.46667 | -0.1082870 | -0.05053 |
| draft_rank | 0.40799 | 0.40799 | 0.1175422 | 0.04796 |
| AAA_0_pa | 336.00000 | 0.56000 | 0.0800223 | 0.04481 |
| quality_0 | -0.08442 | -0.08442 | 0.4565336 | -0.03854 |

108 MLB PA coexist with 492 current upper-minor PA and 23 HR. Sharing denominators attenuates both poor-debut and positive minor-rate signals; the fixed-old-fit probe lowers rate to −0.449, with refitting recovering only to −0.367 versus old −0.237. PA stays near 181 versus 665 actual. The representation lost useful strength rather than translating it successfully. Brennan, Freeman and Henderson show materially different opportunities despite similar source profiles.

Origin-selected peers: Will Brennan (age 24, MLB/AAA/AA PA 45/433.0/157.0; actual next 455 PA/0.166 wins); Tyler Freeman (age 23, MLB/AAA/AA PA 86/343.0/0.0; actual next 168 PA/0.094 wins); Gunnar Henderson (age 21, MLB/AAA/AA PA 132/295.0/208.0; actual next 622 PA/3.402 wins).

Training profile: all=336 distinct people; active=298 distinct people.

## Masyn Winn: 2023 to 2024

Selection: Predeclared diagnostic.

Age 21; MLB PA 137/0/0; draft pick 54, class HS SR; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 26.00 | 137.00 | 1337.80 | 0.2300 | 0.206751 | 0.226168 |
| AAA/K | 83.00 | 498.00 | 1337.80 | 0.2300 | 0.177258 | 0.208064 |
| AA/K | 68.80 | 322.40 | 1337.80 | 0.2300 | 0.217330 | 0.226278 |
| Aplus/K | 47.20 | 210.00 | 1337.80 | 0.2300 | 0.226452 | 0.229235 |
| A/K | 36.00 | 170.40 | 1337.80 | 0.2300 | 0.218195 | 0.227780 |
| MLB/BB | 10.00 | 137.00 | 1337.80 | 0.0800 | 0.075949 | 0.079332 |
| AAA/BB | 44.00 | 498.00 | 1337.80 | 0.0800 | 0.086957 | 0.082893 |
| AA/BB | 40.00 | 322.40 | 1337.80 | 0.0800 | 0.113636 | 0.089882 |
| Aplus/BB | 14.00 | 210.00 | 1337.80 | 0.0800 | 0.070968 | 0.078053 |
| A/BB | 24.00 | 170.40 | 1337.80 | 0.0800 | 0.118343 | 0.087211 |
| MLB/HBP | 0.00 | 137.00 | 1337.80 | 0.0100 | 0.004219 | 0.009047 |
| AAA/HBP | 7.00 | 498.00 | 1337.80 | 0.0100 | 0.013378 | 0.011405 |
| AA/HBP | 0.80 | 322.40 | 1337.80 | 0.0100 | 0.004261 | 0.008314 |
| Aplus/HBP | 0.80 | 210.00 | 1337.80 | 0.0100 | 0.005806 | 0.009096 |
| A/HBP | 1.80 | 170.40 | 1337.80 | 0.0100 | 0.010355 | 0.010067 |
| MLB/HR | 2.00 | 137.00 | 1337.80 | 0.0300 | 0.021097 | 0.028532 |
| AAA/HR | 18.00 | 498.00 | 1337.80 | 0.0300 | 0.035117 | 0.032128 |
| AA/HR | 8.80 | 322.40 | 1337.80 | 0.0300 | 0.027936 | 0.029394 |
| Aplus/HR | 2.00 | 210.00 | 1337.80 | 0.0300 | 0.016129 | 0.027009 |
| A/HR | 1.80 | 170.40 | 1337.80 | 0.0300 | 0.017751 | 0.027696 |
| MLB/BABIP | 19.00 | 97.00 | 897.40 | 0.3000 | 0.248731 | 0.289874 |
| AAA/BABIP | 110.00 | 346.00 | 897.40 | 0.3000 | 0.313901 | 0.306216 |
| AA/BABIP | 62.40 | 202.40 | 897.40 | 0.3000 | 0.305556 | 0.301684 |
| Aplus/BABIP | 52.60 | 145.20 | 897.40 | 0.3000 | 0.336868 | 0.309064 |
| A/BABIP | 35.40 | 106.80 | 897.40 | 0.3000 | 0.316248 | 0.303369 |
| MLB/2B | 2.00 | 137.00 | 1337.80 | 0.0500 | 0.029536 | 0.046627 |
| AAA/2B | 15.00 | 498.00 | 1337.80 | 0.0500 | 0.033445 | 0.043114 |
| AA/2B | 20.00 | 322.40 | 1337.80 | 0.0500 | 0.059186 | 0.052699 |
| Aplus/2B | 11.20 | 210.00 | 1337.80 | 0.0500 | 0.052258 | 0.050487 |
| A/2B | 9.00 | 170.40 | 1337.80 | 0.0500 | 0.051775 | 0.050334 |
| MLB/3B | 0.00 | 137.00 | 1337.80 | 0.0050 | 0.002110 | 0.004524 |
| AAA/3B | 7.00 | 498.00 | 1337.80 | 0.0050 | 0.012542 | 0.008137 |
| AA/3B | 0.80 | 322.40 | 1337.80 | 0.0050 | 0.003078 | 0.004435 |
| Aplus/3B | 6.80 | 210.00 | 1337.80 | 0.0050 | 0.023548 | 0.008999 |
| A/3B | 1.80 | 170.40 | 1337.80 | 0.0050 | 0.008506 | 0.005659 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 305.512 | -0.79671 | 0.54021 |
| rate_only | 305.512 | -0.99353 | 0.44000 |
| pa_only | 288.292 | -0.79671 | 0.50977 |
| shared | 288.292 | -0.99353 | 0.41519 |
| Actual | 637 | 0.25454 | 2.25951 |

Product uses PA × (rate/600 + origin replacement 0.0030961), not a joint predictive distribution.

Saved rate intercept -0.864301; fixed-old-model/new-encoding probe -1.063243. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.6092363 | 0.73108 |
| pooled_mlb_quality | -0.55760 | -0.55760 | 0.7990614 | -0.44556 |
| position_6 | 1.00000 | 1.00000 | -0.3037072 | -0.30371 |
| quality_0 | -0.55760 | -0.55760 | 0.4628239 | -0.25807 |
| work_0 | 137.00000 | 137.00000 | 0.0015186 | 0.20805 |
| reorganized | 1.00000 | 1.00000 | -0.1831881 | -0.18319 |
| age_squared | 1.44000 | 1.44000 | 0.0926498 | 0.13342 |
| prior_debut | 1.00000 | 1.00000 | 0.1147973 | 0.11480 |
| AA_1_pa | 403.00000 | 0.67167 | -0.1512681 | -0.10160 |
| draft_rank | 0.47520 | 0.47520 | 0.1206480 | 0.05733 |
| pooled_AA_pa | 322.40000 | 0.53733 | -0.0954093 | -0.05127 |
| on_40man | 1.00000 | 1.00000 | 0.0478884 | 0.04789 |

The 498-PA AAA season has 18 HR and only 83 K, but the larger shared denominator pulls that favorable rate toward the common prior. The unchanged poor-MLB quality features remain strongly negative. The fixed-old-fit probe becomes −1.063, refit −0.993 versus old −0.797; PA falls 306→288 versus 637 actual. This is an identifiable representation tradeoff, not absent AAA data or proof minor history is unhelpful. Meadows, Edwards and Soderstrom provide varied outcomes.

Origin-selected peers: Parker Meadows (age 23, MLB/AAA/AA PA 145/517.0/0.0; actual next 298 PA/1.211 wins); Xavier Edwards (age 23, MLB/AAA/AA PA 84/433.0/0.0; actual next 303 PA/2.187 wins); Tyler Soderstrom (age 21, MLB/AAA/AA PA 138/335.0/0.0; actual next 213 PA/0.873 wins).

Training profile: all=384 distinct people; active=342 distinct people.

## Nick Kurtz: 2024 to 2025

Selection: Predeclared diagnostic.

Age 21; MLB PA 0/0/0; draft pick 4, class 4YR JR; soft roster listing 0. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| AA/K | 3.00 | 15.00 | 50.00 | 0.2300 | 0.226087 | 0.227000 |
| A/K | 7.00 | 35.00 | 50.00 | 0.2300 | 0.222222 | 0.223000 |
| AA/BB | 2.00 | 15.00 | 50.00 | 0.0800 | 0.086957 | 0.085333 |
| A/BB | 10.00 | 35.00 | 50.00 | 0.0800 | 0.133333 | 0.128000 |
| AA/HBP | 0.00 | 15.00 | 50.00 | 0.0100 | 0.008696 | 0.009000 |
| A/HBP | 0.00 | 35.00 | 50.00 | 0.0100 | 0.007407 | 0.007667 |
| AA/HR | 0.00 | 15.00 | 50.00 | 0.0300 | 0.026087 | 0.027000 |
| A/HR | 4.00 | 35.00 | 50.00 | 0.0300 | 0.051852 | 0.049667 |
| AA/BABIP | 4.00 | 10.00 | 24.00 | 0.3000 | 0.309091 | 0.308065 |
| A/BABIP | 6.00 | 14.00 | 24.00 | 0.3000 | 0.315789 | 0.314516 |
| AA/2B | 1.00 | 15.00 | 50.00 | 0.0500 | 0.052174 | 0.051667 |
| A/2B | 2.00 | 35.00 | 50.00 | 0.0500 | 0.051852 | 0.051667 |
| AA/3B | 0.00 | 15.00 | 50.00 | 0.0050 | 0.004348 | 0.004500 |
| A/3B | 0.00 | 35.00 | 50.00 | 0.0050 | 0.003704 | 0.003833 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| rate_only | 42.495 | 0.02765 | 0.13472 |
| pa_only | 64.216 | -0.13556 | 0.18611 |
| shared | 64.216 | 0.02765 | 0.20358 |
| Actual | 489 | 5.15001 | 5.72099 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.943150; fixed-old-model/new-encoding probe -0.150393. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.5720071 | 0.68641 |
| reorganized | 1.00000 | 1.00000 | -0.2340410 | -0.23404 |
| draft_rank | 0.81761 | 0.81761 | 0.2182086 | 0.17841 |
| position_3 | 1.00000 | 1.00000 | 0.1663446 | 0.16634 |
| age_squared | 1.44000 | 1.44000 | 0.0796801 | 0.11474 |
| draft_college | 1.00000 | 1.00000 | 0.0757800 | 0.07578 |
| draft_known | 1.00000 | 1.00000 | -0.0579094 | -0.05791 |
| absence_window_scaled | 1.00000 | 1.00000 | -0.0455333 | -0.04553 |
| pooled_A_BB | 0.12800 | 0.48000 | 0.0609661 | 0.02926 |
| pooled_AA_BABIP | 0.30806 | 0.08065 | 0.2437272 | 0.01966 |
| draft_rank_low_exposure | 0.54508 | 0.54508 | 0.0341428 | 0.01861 |
| pooled_A_BABIP | 0.31452 | 0.14516 | 0.0925902 | 0.01344 |

Only 35 A PA and 15 AA PA exist, alongside a fourth overall college pick. PA rises 42→64 and conditional rate −0.136→0.028, but actual 489/5.72 remains far away. Because the unchanged inputs have almost the same transformed values, much of the improvement comes from changed fitted mapping, not substantial new evidence. The peer rule returns high-school Johnson/Montgomery/Jenkins, all zero next-year PA, rather than truly analogous fast college entries; this limits the peer interpretation and does not justify a universal draft boost.

Origin-selected peers: Termarr Johnson (age 20, MLB/AAA/AA PA 0/0.0/57.0; actual next 0 PA/0.000 wins); Benny Montgomery (age 21, MLB/AAA/AA PA 0/0.0/48.0; actual next 0 PA/0.000 wins); Walker Jenkins (age 19, MLB/AAA/AA PA 0/0.0/28.0; actual next 0 PA/0.000 wins).

Training profile: all=11 distinct people; active=0 distinct people.

## Matt Olson: 2022 to 2023

Selection: Predeclared diagnostic.

Age 28; MLB PA 699/673/245; draft pick 47, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 306.60 | 1384.40 | 1384.40 | 0.2300 | 0.222043 | 0.222043 |
| MLB/BB | 149.00 | 1384.40 | 1384.40 | 0.0800 | 0.105767 | 0.105767 |
| MLB/HBP | 11.80 | 1384.40 | 1384.40 | 0.0100 | 0.008623 | 0.008623 |
| MLB/HR | 73.60 | 1384.40 | 1384.40 | 0.0300 | 0.051603 | 0.051603 |
| MLB/BABIP | 221.40 | 826.60 | 826.60 | 0.3000 | 0.271314 | 0.271314 |
| MLB/2B | 74.40 | 1384.40 | 1384.40 | 0.0500 | 0.053490 | 0.053490 |
| MLB/3B | 0.60 | 1384.40 | 1384.40 | 0.0050 | 0.000741 | 0.000741 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 572.650 | 1.85799 | 3.56624 |
| rate_only | 572.650 | 1.90389 | 3.61006 |
| pa_only | 588.848 | 1.85799 | 3.66712 |
| shared | 588.848 | 1.90389 | 3.71217 |
| Actual | 720 | 4.57082 | 7.71416 |

Product uses PA × (rate/600 + origin replacement 0.0031310), not a joint predictive distribution.

Saved rate intercept -0.683195; fixed-old-model/new-encoding probe 1.857985. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 699.00000 | 699.00000 | 0.0012965 | 0.90624 |
| pooled_mlb_quality | 1.03318 | 1.03318 | 0.8217162 | 0.84898 |
| work_2 | 662.97327 | 662.97327 | 0.0005998 | 0.39766 |
| quality_0 | 0.57358 | 0.57358 | 0.4081107 | 0.23408 |
| quality_1 | 1.07747 | 1.07747 | 0.1972635 | 0.21255 |
| position_3 | 1.00000 | 1.00000 | 0.1892415 | 0.18924 |
| regular_window_scaled | 1.00000 | 1.00000 | -0.1529108 | -0.15291 |
| reorganized | 1.00000 | 1.00000 | -0.1420125 | -0.14201 |
| pooled_MLB_pa | 1384.40000 | 2.30733 | -0.0606861 | -0.14002 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1201750 | 0.12018 |
| age_centered | 0.20000 | 0.20000 | -0.5898131 | -0.11796 |
| draft_rank | 0.49346 | 0.49346 | 0.2337902 | 0.11537 |

Almost exclusively MLB evidence means his encoded event inputs are essentially unchanged. Nonetheless different fitted coefficients and tree partitions raise PA 573→589 and rate 1.858→1.904, improving value toward his later exceptional 720-PA/7.71 season. This is a training-mapping effect, not successful adjustment of Olson's minor-league history. Alonso, Reynolds and Bell all play regularly without Olson's exact breakout.

Origin-selected peers: Pete Alonso (age 27, MLB/AAA/AA PA 685/0.0/0.0; actual next 658 PA/3.452 wins); Bryan Reynolds (age 27, MLB/AAA/AA PA 614/0.0/0.0; actual next 640 PA/3.040 wins); Josh Bell (age 29, MLB/AAA/AA PA 647/0.0/0.0; actual next 617 PA/2.116 wins).

Training profile: all=569 distinct people; active=455 distinct people.

## Aaron Judge: 2024 to 2025

Selection: Predeclared diagnostic.

Age 32; MLB PA 704/458/696; draft pick 32, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 380.00 | 1488.00 | 1488.00 | 0.2300 | 0.253778 | 0.253778 |
| MLB/BB | 231.40 | 1488.00 | 1488.00 | 0.0800 | 0.150756 | 0.150756 |
| MLB/HBP | 12.60 | 1488.00 | 1488.00 | 0.0100 | 0.008564 | 0.008564 |
| MLB/HR | 124.80 | 1488.00 | 1488.00 | 0.0300 | 0.080479 | 0.080479 |
| MLB/BABIP | 239.80 | 697.20 | 697.20 | 0.3000 | 0.338435 | 0.338435 |
| MLB/2B | 65.60 | 1488.00 | 1488.00 | 0.0500 | 0.044458 | 0.044458 |
| MLB/3B | 1.00 | 1488.00 | 1488.00 | 0.0050 | 0.000945 | 0.000945 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| rate_only | 548.496 | 4.60044 | 5.91912 |
| pa_only | 563.052 | 4.55334 | 6.03201 |
| shared | 563.052 | 4.60044 | 6.07621 |
| Actual | 679 | 6.28743 | 9.23105 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.879499; fixed-old-model/new-encoding probe 4.553340. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 3.64857 | 3.64857 | 0.7757845 | 2.83050 |
| quality_0 | 2.79442 | 2.79442 | 0.4563485 | 1.27523 |
| work_0 | 704.28983 | 704.28983 | 0.0012297 | 0.86603 |
| age_centered | 1.00000 | 1.00000 | -0.5947260 | -0.59473 |
| quality_2 | 2.40833 | 2.40833 | 0.1730254 | 0.41670 |
| work_2 | 696.00000 | 696.00000 | 0.0005115 | 0.35600 |
| quality_1 | 1.31713 | 1.31713 | 0.1971030 | 0.25961 |
| reorganized | 1.00000 | 1.00000 | -0.2506211 | -0.25062 |
| work_1 | 458.00000 | 458.00000 | 0.0004921 | 0.22537 |
| pooled_MLB_BB | 0.15076 | 0.70756 | 0.2809984 | 0.19882 |
| pooled_MLB_pa | 1488.00000 | 2.48000 | -0.0704226 | -0.17465 |
| prior_debut | 1.00000 | 1.00000 | 0.1645925 | 0.16459 |

All current-window evidence is MLB, so every rate input is exactly unchanged. Refit mapping raises PA 548→563 and rate 4.553→4.600, bringing value 5.88→6.08 versus 679/9.23 actual. Do not attribute this to reweighting Judge's own minor data, which is absent in the window. Freeman, Betts and Olson validate a broad productive profile, not certainty of another elite season.

Origin-selected peers: Freddie Freeman (age 34, MLB/AAA/AA PA 638/0.0/0.0; actual next 627 PA/4.784 wins); Mookie Betts (age 31, MLB/AAA/AA PA 516/0.0/0.0; actual next 663 PA/2.398 wins); Matt Olson (age 30, MLB/AAA/AA PA 685/0.0/0.0; actual next 724 PA/5.517 wins).

Training profile: all=224 distinct people; active=170 distinct people.

## Gavin Lux: 2023 to 2024

Selection: Predeclared diagnostic.

Age 25; MLB PA 0/471/381; draft pick 20, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 125.80 | 605.40 | 649.80 | 0.2300 | 0.210944 | 0.212073 |
| AAA/K | 9.00 | 44.40 | 649.80 | 0.2300 | 0.221607 | 0.228384 |
| MLB/BB | 60.40 | 605.40 | 649.80 | 0.0800 | 0.096966 | 0.095962 |
| AAA/BB | 3.60 | 44.40 | 649.80 | 0.0800 | 0.080332 | 0.080064 |
| MLB/HBP | 1.80 | 605.40 | 649.80 | 0.0100 | 0.003969 | 0.004326 |
| AAA/HBP | 0.00 | 44.40 | 649.80 | 0.0100 | 0.006925 | 0.009408 |
| MLB/HR | 9.00 | 605.40 | 649.80 | 0.0300 | 0.017012 | 0.017781 |
| AAA/HR | 0.60 | 44.40 | 649.80 | 0.0300 | 0.024931 | 0.029024 |
| MLB/BABIP | 132.40 | 406.60 | 437.80 | 0.3000 | 0.320568 | 0.319375 |
| AAA/BABIP | 10.80 | 31.20 | 437.80 | 0.3000 | 0.310976 | 0.302678 |
| MLB/2B | 23.20 | 605.40 | 649.80 | 0.0500 | 0.039977 | 0.040571 |
| AAA/2B | 2.40 | 44.40 | 649.80 | 0.0500 | 0.051247 | 0.050240 |
| MLB/3B | 8.00 | 605.40 | 649.80 | 0.0050 | 0.012050 | 0.011632 |
| AAA/3B | 0.00 | 44.40 | 649.80 | 0.0050 | 0.003463 | 0.004704 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 215.427 | -0.23943 | 0.58101 |
| rate_only | 215.427 | -0.18067 | 0.60211 |
| pa_only | 227.410 | -0.23943 | 0.61333 |
| shared | 227.410 | -0.18067 | 0.63560 |
| Actual | 487 | 0.08394 | 1.58897 |

Product uses PA × (rate/600 + origin replacement 0.0030961), not a joint predictive distribution.

Saved rate intercept -0.879327; fixed-old-model/new-encoding probe -0.232235. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.40000 | -0.40000 | -0.6071293 | 0.24285 |
| work_1 | 471.00000 | 471.00000 | 0.0004654 | 0.21922 |
| work_2 | 381.15685 | 381.15685 | 0.0005659 | 0.21569 |
| reorganized | 1.00000 | 1.00000 | -0.2011154 | -0.20112 |
| prior_debut | 1.00000 | 1.00000 | 0.1821210 | 0.18212 |
| position_4 | 1.00000 | 1.00000 | -0.1330992 | -0.13310 |
| pooled_mlb_quality | 0.15072 | 0.15072 | 0.7889322 | 0.11891 |
| draft_rank | 0.60587 | 0.60587 | 0.1935243 | 0.11725 |
| quality_present_2 | 1.00000 | 1.00000 | -0.0915661 | -0.09157 |
| quality_present_1 | 1.00000 | 1.00000 | 0.0856740 | 0.08567 |
| pooled_MLB_pa | 605.40000 | 1.00900 | -0.0692047 | -0.06983 |
| on_40man | 1.00000 | 1.00000 | 0.0652412 | 0.06524 |

The current missed season remains absent observation; 471/381 prior MLB PA and 74 old AAA PA persist. PA rises 215→227 and value 0.58→0.64 versus 487/1.59 actual. A small plausible improvement still leaves a major return-workload deficit. Plummer, Ciuffo and Craig all have zero later PA; generic inactive similarity is a weak medical-return comparison and must not motivate a blanket absence penalty.

Origin-selected peers: Nick Plummer (age 26, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Nick Ciuffo (age 28, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Will Craig (age 28, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins).

Training profile: all=111 distinct people; active=9 distinct people.

## Matt McLain: 2024 to 2025

Selection: Predeclared diagnostic.

Age 24; MLB PA 0/403/0; draft pick 17, class 4YR JR; soft roster listing 0. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 92.00 | 322.40 | 737.60 | 0.2300 | 0.272254 | 0.251309 |
| AAA/K | 29.60 | 144.00 | 737.60 | 0.2300 | 0.215574 | 0.225798 |
| AA/K | 76.20 | 271.20 | 737.60 | 0.2300 | 0.267241 | 0.246504 |
| MLB/BB | 24.80 | 322.40 | 737.60 | 0.0800 | 0.077652 | 0.078816 |
| AAA/BB | 23.20 | 144.00 | 737.60 | 0.0800 | 0.127869 | 0.093945 |
| AA/BB | 41.40 | 271.20 | 737.60 | 0.0800 | 0.133082 | 0.103524 |
| MLB/HBP | 5.60 | 322.40 | 737.60 | 0.0100 | 0.015625 | 0.012837 |
| AAA/HBP | 4.00 | 144.00 | 737.60 | 0.0100 | 0.020492 | 0.013056 |
| AA/HBP | 4.80 | 271.20 | 737.60 | 0.0100 | 0.015625 | 0.012493 |
| MLB/HR | 12.80 | 322.40 | 737.60 | 0.0300 | 0.037405 | 0.033734 |
| AAA/HR | 9.60 | 144.00 | 737.60 | 0.0300 | 0.051639 | 0.036304 |
| AA/HR | 10.20 | 271.20 | 737.60 | 0.0300 | 0.035560 | 0.032464 |
| MLB/BABIP | 72.00 | 187.20 | 402.00 | 0.3000 | 0.355153 | 0.331554 |
| AAA/BABIP | 29.60 | 76.80 | 402.00 | 0.3000 | 0.337104 | 0.313068 |
| AA/BABIP | 41.40 | 138.00 | 402.00 | 0.3000 | 0.300000 | 0.300000 |
| MLB/2B | 18.40 | 322.40 | 737.60 | 0.0500 | 0.055398 | 0.052722 |
| AAA/2B | 9.60 | 144.00 | 737.60 | 0.0500 | 0.059836 | 0.052865 |
| AA/2B | 12.60 | 271.20 | 737.60 | 0.0500 | 0.047414 | 0.048854 |
| MLB/3B | 3.20 | 322.40 | 737.60 | 0.0050 | 0.008759 | 0.006896 |
| AAA/3B | 0.80 | 144.00 | 737.60 | 0.0050 | 0.005328 | 0.005096 |
| AA/3B | 3.00 | 271.20 | 737.60 | 0.0050 | 0.009429 | 0.006963 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 173.516 | 0.21812 | 0.60517 |
| rate_only | 173.516 | -0.01819 | 0.53683 |
| pa_only | 125.814 | 0.21812 | 0.43880 |
| shared | 125.814 | -0.01819 | 0.38925 |
| Actual | 577 | -1.27881 | 0.56815 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.943150; fixed-old-model/new-encoding probe -0.103843. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.56675 | 0.56675 | 0.8042362 | 0.45580 |
| age_centered | -0.60000 | -0.60000 | -0.5720071 | 0.34320 |
| position_6 | 1.00000 | 1.00000 | -0.2828698 | -0.28287 |
| reorganized | 1.00000 | 1.00000 | -0.2340410 | -0.23404 |
| prior_debut | 1.00000 | 1.00000 | 0.2292208 | 0.22922 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1852958 | 0.18530 |
| AA_2_pa | 452.00000 | 0.75333 | -0.2284613 | -0.17211 |
| quality_1 | 0.67281 | 0.67281 | 0.2123579 | 0.14288 |
| draft_rank | 0.62725 | 0.62725 | 0.2182086 | 0.13687 |
| work_1 | 403.00000 | 403.00000 | 0.0002870 | 0.11566 |
| pooled_MLB_BABIP | 0.33155 | 0.31554 | -0.3188211 | -0.10060 |
| draft_college | 1.00000 | 1.00000 | 0.0757800 | 0.07578 |

A known 403-PA MLB/180-PA AAA productive season follows a 452-PA AA season, then zero current play. Sharing evidence reduces rate 0.218→−0.018 and PA 174→126 versus actual 577. The rate-only value happens to move nearer the actual 0.57; combined workload gets worse. This is exactly why lucky delivered-value agreement cannot certify opportunity or talent. Swaggerty, Plummer and Rutherford are marginal inactive peers, not equivalent established injury returns.

Origin-selected peers: Travis Swaggerty (age 26, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Nick Plummer (age 27, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Blake Rutherford (age 27, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins).

Training profile: all=5 distinct people; active=4 distinct people.

## Fernando Tatis Jr.: 2022 to 2023

Selection: Predeclared diagnostic.

Age 23; MLB PA 0/546/257; draft pick None, class unknown; soft roster listing 0. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |
| 2022 | AA | 14 | 0 | 2 | 4 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 159.00 | 591.00 | 605.00 | 0.2300 | 0.263386 | 0.262723 |
| AA/K | 2.00 | 14.00 | 605.00 | 0.2300 | 0.219298 | 0.228270 |
| MLB/BB | 60.40 | 591.00 | 605.00 | 0.0800 | 0.098987 | 0.098610 |
| AA/BB | 4.00 | 14.00 | 605.00 | 0.0800 | 0.105263 | 0.084085 |
| MLB/HBP | 4.60 | 591.00 | 605.00 | 0.0100 | 0.008104 | 0.008142 |
| AA/HBP | 1.00 | 14.00 | 605.00 | 0.0100 | 0.017544 | 0.011220 |
| MLB/HR | 43.80 | 591.00 | 605.00 | 0.0300 | 0.067728 | 0.066979 |
| AA/HR | 0.00 | 14.00 | 605.00 | 0.0300 | 0.026316 | 0.029404 |
| MLB/BABIP | 101.40 | 317.80 | 324.80 | 0.3000 | 0.314505 | 0.314266 |
| AA/BABIP | 2.00 | 7.00 | 324.80 | 0.3000 | 0.299065 | 0.299765 |
| MLB/2B | 31.40 | 591.00 | 605.00 | 0.0500 | 0.052677 | 0.052624 |
| AA/2B | 1.00 | 14.00 | 605.00 | 0.0500 | 0.052632 | 0.050426 |
| MLB/3B | 1.20 | 591.00 | 605.00 | 0.0050 | 0.002460 | 0.002511 |
| AA/3B | 1.00 | 14.00 | 605.00 | 0.0050 | 0.013158 | 0.006319 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 147.175 | 1.27950 | 0.77465 |
| rate_only | 147.175 | 1.21633 | 0.75916 |
| pa_only | 145.574 | 1.27950 | 0.76622 |
| shared | 145.574 | 1.21633 | 0.75090 |
| Actual | 635 | 0.72681 | 2.73521 |

Product uses PA × (rate/600 + origin replacement 0.0031310), not a joint predictive distribution.

Saved rate intercept -0.750761; fixed-old-model/new-encoding probe 1.244510. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.36737 | 1.36737 | 0.7759918 | 1.06107 |
| age_centered | -0.80000 | -0.80000 | -0.5475684 | 0.43805 |
| work_2 | 695.44543 | 695.44543 | 0.0005094 | 0.35425 |
| position_6 | 1.00000 | 1.00000 | -0.3182163 | -0.31822 |
| quality_1 | 1.34788 | 1.34788 | 0.2342442 | 0.31573 |
| quality_2 | 0.64772 | 0.64772 | 0.2692248 | 0.17438 |
| work_1 | 546.22478 | 546.22478 | 0.0002990 | 0.16333 |
| regular_window_scaled | 0.66667 | 0.66667 | -0.2196187 | -0.14641 |
| reorganized | 1.00000 | 1.00000 | -0.1270138 | -0.12701 |
| quality_present_2 | 1.00000 | 1.00000 | -0.1171108 | -0.11711 |
| pooled_MLB_HR | 0.06698 | 0.36979 | 0.1965400 | 0.07268 |
| quality_present_1 | 1.00000 | 1.00000 | 0.0584578 | 0.05846 |

The only minor sample is a 14-PA AA stint; 546 and 257 prior MLB PA/42 and 17 HR remain. Changes in event weighting are small, and PA remains near 146 versus 635 actual. Rate and value slightly decline. The missing finite-suspension meaning is not repaired by a count denominator. Basabe, Apostel and Grullón all fail to arrive/return and are poor suspension analogues; do not infer ordinary inactive-player risk applies to a suspended star.

Origin-selected peers: Luis Alexander Basabe (age 25, MLB/AAA/AA PA 0/26.0/0.0; actual next 0 PA/0.000 wins); Sherten Apostel (age 23, MLB/AAA/AA PA 0/77.0/0.0; actual next 0 PA/0.000 wins); Deivy Grullón (age 26, MLB/AAA/AA PA 0/63.0/0.0; actual next 0 PA/0.000 wins).

Training profile: all=25 distinct people; active=14 distinct people.

## Colton Cowser: 2024 to 2025

Selection: shared largest gain; rate_only largest gain.

Age 24; MLB PA 561/77/0; draft pick 5, class 4YR JR; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 224 | 10 | 57 | 36 |
| 2022 | AAA | 124 | 5 | 38 | 13 |
| 2022 | Aplus | 278 | 4 | 79 | 45 |
| 2023 | AAA | 399 | 17 | 107 | 62 |
| 2023 | MLB | 77 | 0 | 22 | 13 |
| 2024 | MLB | 561 | 24 | 172 | 50 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 189.60 | 622.60 | 1317.40 | 0.2300 | 0.294215 | 0.262737 |
| AAA/K | 108.40 | 393.60 | 1317.40 | 0.2300 | 0.266207 | 0.242609 |
| AA/K | 34.20 | 134.40 | 1317.40 | 0.2300 | 0.244027 | 0.232320 |
| Aplus/K | 47.40 | 166.80 | 1317.40 | 0.2300 | 0.263868 | 0.236375 |
| MLB/BB | 60.40 | 622.60 | 1317.40 | 0.0800 | 0.094658 | 0.087473 |
| AAA/BB | 57.40 | 393.60 | 1317.40 | 0.0800 | 0.132496 | 0.098281 |
| AA/BB | 21.60 | 134.40 | 1317.40 | 0.0800 | 0.126280 | 0.087653 |
| Aplus/BB | 27.00 | 166.80 | 1317.40 | 0.0800 | 0.131184 | 0.089635 |
| MLB/HBP | 8.60 | 622.60 | 1317.40 | 0.0100 | 0.013285 | 0.011675 |
| AAA/HBP | 7.60 | 393.60 | 1317.40 | 0.0100 | 0.017423 | 0.012585 |
| AA/HBP | 5.40 | 134.40 | 1317.40 | 0.0100 | 0.027304 | 0.012862 |
| Aplus/HBP | 1.80 | 166.80 | 1317.40 | 0.0100 | 0.010495 | 0.010093 |
| MLB/HR | 24.00 | 622.60 | 1317.40 | 0.0300 | 0.037365 | 0.033755 |
| AAA/HR | 16.60 | 393.60 | 1317.40 | 0.0300 | 0.039708 | 0.033381 |
| AA/HR | 6.00 | 134.40 | 1317.40 | 0.0300 | 0.038396 | 0.031388 |
| Aplus/HR | 2.40 | 166.80 | 1317.40 | 0.0300 | 0.020240 | 0.028163 |
| MLB/BABIP | 102.60 | 338.00 | 694.60 | 0.3000 | 0.302740 | 0.301510 |
| AAA/BABIP | 74.80 | 201.20 | 694.60 | 0.3000 | 0.347942 | 0.318173 |
| AA/BABIP | 30.00 | 67.20 | 694.60 | 0.3000 | 0.358852 | 0.312384 |
| Aplus/BABIP | 33.00 | 88.20 | 694.60 | 0.3000 | 0.334750 | 0.308231 |
| MLB/2B | 25.60 | 622.60 | 1317.40 | 0.0500 | 0.042347 | 0.046098 |
| AAA/2B | 18.60 | 393.60 | 1317.40 | 0.0500 | 0.047812 | 0.049238 |
| AA/2B | 6.00 | 134.40 | 1317.40 | 0.0500 | 0.046928 | 0.049492 |
| Aplus/2B | 11.40 | 166.80 | 1317.40 | 0.0500 | 0.061469 | 0.052159 |
| MLB/3B | 3.00 | 622.60 | 1317.40 | 0.0050 | 0.004844 | 0.004920 |
| AAA/3B | 0.80 | 393.60 | 1317.40 | 0.0050 | 0.002634 | 0.004176 |
| AA/3B | 0.00 | 134.40 | 1317.40 | 0.0050 | 0.002133 | 0.004526 |
| Aplus/3B | 1.20 | 166.80 | 1317.40 | 0.0050 | 0.006372 | 0.005258 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 518.302 | 1.37155 | 2.80405 |
| rate_only | 518.302 | 0.94215 | 2.43312 |
| pa_only | 463.080 | 1.37155 | 2.50530 |
| shared | 463.080 | 0.94215 | 2.17389 |
| Actual | 360 | -1.34401 | 0.31536 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.827716; fixed-old-model/new-encoding probe 0.721537. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 561.23096 | 561.23096 | 0.0012525 | 0.70296 |
| age_centered | -0.60000 | -0.60000 | -0.5903121 | 0.35419 |
| reorganized | 1.00000 | 1.00000 | -0.2586756 | -0.25868 |
| position_7 | 1.00000 | 1.00000 | 0.1974187 | 0.19742 |
| draft_rank | 0.78826 | 0.78826 | 0.2383202 | 0.18786 |
| quality_0 | 0.33922 | 0.33922 | 0.4317777 | 0.14647 |
| pooled_mlb_quality | 0.17484 | 0.17484 | 0.7994893 | 0.13978 |
| prior_debut | 1.00000 | 1.00000 | 0.1258251 | 0.12583 |
| draft_college | 1.00000 | 1.00000 | 0.1232704 | 0.12327 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1211329 | 0.12113 |
| on_40man | 1.00000 | 1.00000 | 0.0877136 | 0.08771 |
| MLB_0_pa | 561.00000 | 0.93500 | -0.0782621 | -0.07318 |

Largest combined and rate-only value gain. The known 561-PA season has 24 HR but 172 K, alongside earlier minor samples. Refit lowers both rate 1.37→0.94 and PA 518→463, reducing a false-high value 2.80→2.17 versus 0.32 actual. It remains a false high, and the lower forecast does not identify a later injury/event. Langford, Abrams and Vaughn had substantially stronger delivered seasons; the case does not license downgrading every similar young regular.

Origin-selected peers: Wyatt Langford (age 22, MLB/AAA/AA PA 557/11.0/0.0; actual next 573 PA/2.948 wins); CJ Abrams (age 23, MLB/AAA/AA PA 602/0.0/0.0; actual next 635 PA/2.582 wins); Andrew Vaughn (age 26, MLB/AAA/AA PA 619/0.0/0.0; actual next 447 PA/1.371 wins).

Training profile: all=407 distinct people; active=365 distinct people.

## Cody Bellinger: 2018 to 2019

Selection: shared largest harm; pa_only largest harm.

Age 22; MLB PA 632/548/0; draft pick 124, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |
| 2017 | AAA | 77 | 5 | 22 | 8 |
| 2017 | MLB | 548 | 39 | 146 | 51 |
| 2017 | RK121 | 4 | 1 | 1 | 0 |
| 2018 | MLB | 632 | 25 | 151 | 60 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 267.80 | 1070.40 | 1421.40 | 0.2300 | 0.248462 | 0.244203 |
| AAA/K | 17.60 | 68.80 | 1421.40 | 0.2300 | 0.240521 | 0.231167 |
| AA/K | 56.40 | 279.00 | 1421.40 | 0.2300 | 0.209499 | 0.224893 |
| RK121/K | 0.80 | 3.20 | 1421.40 | 0.2300 | 0.230620 | 0.230042 |
| MLB/BB | 100.80 | 1070.40 | 1421.40 | 0.0800 | 0.092960 | 0.089970 |
| AAA/BB | 7.00 | 68.80 | 1421.40 | 0.0800 | 0.088863 | 0.080983 |
| AA/BB | 34.20 | 279.00 | 1421.40 | 0.0800 | 0.111346 | 0.087809 |
| RK121/BB | 0.00 | 3.20 | 1421.40 | 0.0800 | 0.077519 | 0.079832 |
| MLB/HBP | 3.80 | 1070.40 | 1421.40 | 0.0100 | 0.004101 | 0.005462 |
| AAA/HBP | 0.80 | 68.80 | 1421.40 | 0.0100 | 0.010664 | 0.010074 |
| AA/HBP | 1.80 | 279.00 | 1421.40 | 0.0100 | 0.007388 | 0.009349 |
| RK121/HBP | 0.00 | 3.20 | 1421.40 | 0.0100 | 0.009690 | 0.009979 |
| MLB/HR | 56.20 | 1070.40 | 1421.40 | 0.0300 | 0.050581 | 0.045833 |
| AAA/HR | 5.80 | 68.80 | 1421.40 | 0.0300 | 0.052133 | 0.032456 |
| AA/HR | 13.80 | 279.00 | 1421.40 | 0.0300 | 0.044327 | 0.033569 |
| RK121/HR | 0.80 | 3.20 | 1421.40 | 0.0300 | 0.036822 | 0.030463 |
| MLB/BABIP | 191.20 | 622.40 | 832.40 | 0.3000 | 0.306202 | 0.304805 |
| AAA/BABIP | 16.20 | 36.80 | 832.40 | 0.3000 | 0.337719 | 0.305534 |
| AA/BABIP | 49.20 | 171.60 | 832.40 | 0.3000 | 0.291605 | 0.297555 |
| RK121/BABIP | 0.00 | 1.60 | 832.40 | 0.3000 | 0.295276 | 0.299485 |
| MLB/2B | 48.80 | 1070.40 | 1421.40 | 0.0500 | 0.045967 | 0.046898 |
| AAA/2B | 3.20 | 68.80 | 1421.40 | 0.0500 | 0.048578 | 0.049842 |
| AA/2B | 10.20 | 279.00 | 1421.40 | 0.0500 | 0.040106 | 0.047535 |
| RK121/2B | 0.00 | 3.20 | 1421.40 | 0.0500 | 0.048450 | 0.049895 |
| MLB/3B | 10.20 | 1070.40 | 1421.40 | 0.0050 | 0.009142 | 0.008187 |
| AAA/3B | 0.00 | 68.80 | 1421.40 | 0.0050 | 0.002962 | 0.004774 |
| AA/3B | 0.60 | 279.00 | 1421.40 | 0.0050 | 0.002902 | 0.004477 |
| RK121/3B | 0.00 | 3.20 | 1421.40 | 0.0050 | 0.004845 | 0.004989 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 607.779 | 2.15788 | 4.05707 |
| rate_only | 607.779 | 2.05314 | 3.95097 |
| pa_only | 528.412 | 2.15788 | 3.52728 |
| shared | 528.412 | 2.05314 | 3.43504 |
| Actual | 661 | 4.31124 | 6.76875 |

Product uses PA × (rate/600 + origin replacement 0.0030788), not a joint predictive distribution.

Saved rate intercept -0.837613; fixed-old-model/new-encoding probe 1.944260. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.91523 | 0.91523 | 0.7263458 | 0.66477 |
| age_centered | -1.00000 | -1.00000 | -0.5425516 | 0.54255 |
| work_0 | 631.74002 | 631.74002 | 0.0008007 | 0.50582 |
| work_1 | 548.00000 | 548.00000 | 0.0007447 | 0.40811 |
| position_3 | 1.00000 | 1.00000 | 0.2589014 | 0.25890 |
| quality_1 | 0.84660 | 0.84660 | 0.2622468 | 0.22202 |
| quality_0 | 0.48802 | 0.48802 | 0.4333183 | 0.21147 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1489985 | -0.14900 |
| prior_debut | 1.00000 | 1.00000 | 0.1223216 | 0.12232 |
| AA_2_pa | 465.00000 | 0.77500 | -0.1459776 | -0.11313 |
| on_40man | 1.00000 | 1.00000 | 0.1090051 | 0.10901 |
| pooled_AA_pa | 279.00000 | 0.46500 | -0.1660513 | -0.07721 |

Largest combined/PA-only deterioration. Two substantial MLB seasons, 548 PA/39 HR and 632 PA/25 HR, already establish success. The representation retains but attenuates older minor signals; the refit cuts PA 608→528 and rate 2.158→2.053, worsening value against 661/6.77 actual. The workload loss is a learned partition change, not a justified retirement/injury flag. Olson, Hoskins and Gallo offer varied but productive subsequent workloads.

Origin-selected peers: Matt Olson (age 24, MLB/AAA/AA PA 660/0.0/0.0; actual next 547 PA/3.842 wins); Rhys Hoskins (age 25, MLB/AAA/AA PA 660/0.0/0.0; actual next 705 PA/3.683 wins); Joey Gallo (age 24, MLB/AAA/AA PA 577/0.0/0.0; actual next 297 PA/2.859 wins).

Training profile: all=253 distinct people; active=221 distinct people.

## Yordan Alvarez: 2024 to 2025

Selection: shared false high; rate_only false high; pa_only largest gain; pa_only false high.

Age 27; MLB PA 635/496/561; draft pick None, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 232.20 | 1368.40 | 1377.20 | 0.2300 | 0.173795 | 0.174129 |
| AAA/K | 0.80 | 8.80 | 1377.20 | 0.2300 | 0.218750 | 0.229171 |
| MLB/BB | 145.60 | 1368.40 | 1377.20 | 0.0800 | 0.104604 | 0.104457 |
| AAA/BB | 1.60 | 8.80 | 1377.20 | 0.0800 | 0.088235 | 0.080607 |
| MLB/HBP | 24.00 | 1368.40 | 1377.20 | 0.0100 | 0.017025 | 0.016983 |
| AAA/HBP | 0.00 | 8.80 | 1377.20 | 0.0100 | 0.009191 | 0.009940 |
| MLB/HR | 82.00 | 1368.40 | 1377.20 | 0.0300 | 0.057886 | 0.057720 |
| AAA/HR | 0.00 | 8.80 | 1377.20 | 0.0300 | 0.027574 | 0.029821 |
| MLB/BABIP | 270.40 | 859.20 | 865.60 | 0.3000 | 0.313178 | 0.313090 |
| AAA/BABIP | 2.40 | 6.40 | 865.60 | 0.3000 | 0.304511 | 0.300497 |
| MLB/2B | 70.60 | 1368.40 | 1377.20 | 0.0500 | 0.051485 | 0.051476 |
| AAA/2B | 0.80 | 8.80 | 1377.20 | 0.0500 | 0.053309 | 0.050244 |
| MLB/3B | 4.00 | 1368.40 | 1377.20 | 0.0050 | 0.003065 | 0.003076 |
| AAA/3B | 0.00 | 8.80 | 1377.20 | 0.0050 | 0.004596 | 0.004970 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| rate_only | 584.774 | 3.72660 | 5.45897 |
| pa_only | 556.300 | 3.70970 | 5.17749 |
| shared | 556.300 | 3.72660 | 5.19316 |
| Actual | 199 | 0.91965 | 0.92510 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.943150; fixed-old-model/new-encoding probe 3.691562. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 2.45709 | 2.45709 | 0.8042362 | 1.97608 |
| work_0 | 635.26142 | 635.26142 | 0.0012582 | 0.79927 |
| quality_0 | 1.41565 | 1.41565 | 0.4780208 | 0.67671 |
| work_2 | 561.00000 | 561.00000 | 0.0007257 | 0.40712 |
| position_10 | 1.00000 | 1.00000 | 0.3023981 | 0.30240 |
| quality_1 | 1.38309 | 1.38309 | 0.2123579 | 0.29371 |
| quality_2 | 1.73811 | 1.73811 | 0.1662152 | 0.28890 |
| reorganized | 1.00000 | 1.00000 | -0.2340410 | -0.23404 |
| pooled_MLB_pa | 1368.40000 | 2.28067 | -0.1026062 | -0.23401 |
| prior_debut | 1.00000 | 1.00000 | 0.2292208 | 0.22922 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1852958 | 0.18530 |
| work_1 | 496.00000 | 496.00000 | 0.0002870 | 0.14235 |

Largest false high and PA-only gain. Strong 635/496/561 MLB PA and 35/31/37 HR support an elite batting estimate. New rate is nearly unchanged, while PA falls 585→556 and value 5.44→5.19 against an unforeseen 199/0.93 season. The smaller loss is not health prediction. Soto, Ohtani and Guerrero remain successful and oppose a general elite-player penalty.

Origin-selected peers: Juan Soto (age 25, MLB/AAA/AA PA 713/0.0/0.0; actual next 715 PA/6.406 wins); Shohei Ohtani (age 29, MLB/AAA/AA PA 731/0.0/0.0; actual next 727 PA/7.877 wins); Vladimir Guerrero Jr. (age 25, MLB/AAA/AA PA 697/0.0/0.0; actual next 680 PA/4.973 wins).

Training profile: all=439 distinct people; active=346 distinct people.

## Aaron Judge: 2016 to 2017

Selection: shared false low; rate_only false low; pa_only false low.

Age 24; MLB PA 95/0/0; draft pick 32, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 42.00 | 95.00 | 1274.80 | 0.2300 | 0.333333 | 0.244657 |
| AAA/K | 157.20 | 618.00 | 1274.80 | 0.2300 | 0.250975 | 0.240954 |
| AA/K | 56.00 | 224.00 | 1274.80 | 0.2300 | 0.243827 | 0.233259 |
| Aplus/K | 43.20 | 171.00 | 1274.80 | 0.2300 | 0.244280 | 0.232815 |
| A/K | 35.40 | 166.80 | 1274.80 | 0.2300 | 0.218891 | 0.227844 |
| MLB/BB | 9.00 | 95.00 | 1274.80 | 0.0800 | 0.087179 | 0.081018 |
| AAA/BB | 70.20 | 618.00 | 1274.80 | 0.0800 | 0.108914 | 0.095100 |
| AA/BB | 18.40 | 224.00 | 1274.80 | 0.0800 | 0.081481 | 0.080349 |
| Aplus/BB | 29.40 | 171.00 | 1274.80 | 0.0800 | 0.138007 | 0.091434 |
| A/BB | 22.80 | 166.80 | 1274.80 | 0.0800 | 0.115442 | 0.086878 |
| MLB/HBP | 1.00 | 95.00 | 1274.80 | 0.0100 | 0.010256 | 0.010036 |
| AAA/HBP | 8.00 | 618.00 | 1274.80 | 0.0100 | 0.012535 | 0.011324 |
| AA/HBP | 2.40 | 224.00 | 1274.80 | 0.0100 | 0.010494 | 0.010116 |
| Aplus/HBP | 0.60 | 171.00 | 1274.80 | 0.0100 | 0.005904 | 0.009193 |
| A/HBP | 1.20 | 166.80 | 1274.80 | 0.0100 | 0.008246 | 0.009660 |
| MLB/HR | 4.00 | 95.00 | 1274.80 | 0.0300 | 0.035897 | 0.030836 |
| AAA/HR | 25.40 | 618.00 | 1274.80 | 0.0300 | 0.039554 | 0.034990 |
| AA/HR | 9.60 | 224.00 | 1274.80 | 0.0300 | 0.038889 | 0.032095 |
| Aplus/HR | 4.80 | 171.00 | 1274.80 | 0.0300 | 0.028782 | 0.029760 |
| A/HR | 5.40 | 166.80 | 1274.80 | 0.0300 | 0.031484 | 0.030288 |
| MLB/BABIP | 11.00 | 39.00 | 726.80 | 0.3000 | 0.294964 | 0.299153 |
| AAA/BABIP | 110.40 | 357.20 | 726.80 | 0.3000 | 0.307087 | 0.303919 |
| AA/BABIP | 47.20 | 136.80 | 726.80 | 0.3000 | 0.326014 | 0.307450 |
| Aplus/BABIP | 34.80 | 92.40 | 726.80 | 0.3000 | 0.336798 | 0.308563 |
| A/BABIP | 41.40 | 101.40 | 726.80 | 0.3000 | 0.354518 | 0.313280 |
| MLB/2B | 2.00 | 95.00 | 1274.80 | 0.0500 | 0.035897 | 0.048000 |
| AAA/2B | 26.00 | 618.00 | 1274.80 | 0.0500 | 0.043175 | 0.046436 |
| AA/2B | 12.80 | 224.00 | 1274.80 | 0.0500 | 0.054938 | 0.051164 |
| Aplus/2B | 5.40 | 171.00 | 1274.80 | 0.0500 | 0.038376 | 0.047709 |
| A/2B | 9.00 | 166.80 | 1274.80 | 0.0500 | 0.052474 | 0.050480 |
| MLB/3B | 0.00 | 95.00 | 1274.80 | 0.0050 | 0.002564 | 0.004654 |
| AAA/3B | 1.00 | 618.00 | 1274.80 | 0.0050 | 0.002089 | 0.003480 |
| AA/3B | 2.40 | 224.00 | 1274.80 | 0.0050 | 0.008951 | 0.005931 |
| Aplus/3B | 1.20 | 171.00 | 1274.80 | 0.0050 | 0.006273 | 0.005251 |
| A/3B | 1.20 | 166.80 | 1274.80 | 0.0050 | 0.006372 | 0.005266 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| rate_only | 143.966 | -0.37689 | 0.35415 |
| pa_only | 163.092 | -0.05720 | 0.48809 |
| shared | 163.092 | -0.37689 | 0.40120 |
| Actual | 678 | 5.32988 | 8.10841 |

Product uses PA × (rate/600 + origin replacement 0.0030881), not a joint predictive distribution.

Saved rate intercept -0.718275; fixed-old-model/new-encoding probe -0.446589. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.4964800 | 0.29789 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.2023996 | -0.20240 |
| position_9 | 1.00000 | 1.00000 | 0.1630220 | 0.16302 |
| pooled_mlb_quality | -0.17509 | -0.17509 | 0.6948538 | -0.12166 |
| draft_known | 1.00000 | 1.00000 | 0.0931947 | 0.09319 |
| work_0 | 95.07825 | 95.07825 | 0.0009042 | 0.08597 |
| AA_1_pa | 280.00000 | 0.46667 | -0.1666595 | -0.07777 |
| quality_0 | -0.17509 | -0.17509 | 0.4348441 | -0.07614 |
| prior_debut | 1.00000 | 1.00000 | 0.0679554 | 0.06796 |
| pooled_AA_pa | 224.00000 | 0.37333 | -0.1537799 | -0.05741 |
| pooled_AAA_pa | 618.00000 | 1.03000 | -0.0324314 | -0.03340 |
| quality_present_0 | 1.00000 | 1.00000 | 0.0323208 | 0.03232 |

Largest false low across products. A 95-PA debut contains 42 K, but a 410-PA AAA season with 19 HR and 98 K is also present. Sharing denominators reduces the large bad-debut K deviation, but simultaneously reduces useful minor power evidence while legacy MLB quality remains negative. The fixed-old-fit rate probe drops −0.057→−0.447; refitting recovers to −0.377. PA rises 144→163 but combined value still falls, versus 678 PA/8.11 actual. Marrero, Decker and Cowart had weak outcomes; an extraordinary breakout is not guaranteed, yet this encoding does not deliver the hoped-for sensible improvement.

Origin-selected peers: Deven Marrero (age 25, MLB/AAA/AA PA 14/388.0/0.0; actual next 188 PA/-0.447 wins); Jaff Decker (age 26, MLB/AAA/AA PA 57/417.0/0.0; actual next 62 PA/-0.115 wins); Kaleb Cowart (age 24, MLB/AAA/AA PA 87/458.0/0.0; actual next 117 PA/0.123 wins).

Training profile: all=186 distinct people; active=159 distinct people.

## Austin Nola: 2021 to 2022

Selection: shared ordinary.

Age 31; MLB PA 194/184/267; draft pick 167, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 229 | 7 | 40 | 29 |
| 2019 | MLB | 267 | 10 | 63 | 22 |
| 2020 | MLB | 184 | 7 | 34 | 17 |
| 2021 | AAA | 39 | 1 | 7 | 5 |
| 2021 | MLB | 194 | 2 | 19 | 14 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 84.00 | 501.40 | 677.80 | 0.2300 | 0.177918 | 0.189730 |
| AAA/K | 31.00 | 176.40 | 677.80 | 0.2300 | 0.195369 | 0.217693 |
| MLB/BB | 40.80 | 501.40 | 677.80 | 0.0800 | 0.081144 | 0.080885 |
| AAA/BB | 22.40 | 176.40 | 677.80 | 0.0800 | 0.109986 | 0.090656 |
| MLB/HBP | 9.80 | 501.40 | 677.80 | 0.0100 | 0.017958 | 0.016153 |
| AAA/HBP | 2.20 | 176.40 | 677.80 | 0.0100 | 0.011577 | 0.010561 |
| MLB/HR | 13.60 | 501.40 | 677.80 | 0.0300 | 0.027602 | 0.028146 |
| AAA/HR | 5.20 | 176.40 | 677.80 | 0.0300 | 0.029667 | 0.029882 |
| MLB/BABIP | 107.00 | 351.20 | 466.80 | 0.3000 | 0.303635 | 0.302893 |
| AAA/BABIP | 43.20 | 115.60 | 466.80 | 0.3000 | 0.339518 | 0.315032 |
| MLB/2B | 26.40 | 501.40 | 677.80 | 0.0500 | 0.052212 | 0.051710 |
| AAA/2B | 10.00 | 176.40 | 677.80 | 0.0500 | 0.054269 | 0.051517 |
| MLB/3B | 1.40 | 501.40 | 677.80 | 0.0050 | 0.003159 | 0.003577 |
| AAA/3B | 0.60 | 176.40 | 677.80 | 0.0050 | 0.003980 | 0.004637 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 263.210 | -0.28747 | 0.69905 |
| rate_only | 263.210 | -0.40627 | 0.64694 |
| pa_only | 256.655 | -0.28747 | 0.68164 |
| shared | 256.655 | -0.40627 | 0.63083 |
| Actual | 397 | -0.92471 | 0.63115 |

Product uses PA × (rate/600 + origin replacement 0.0031350), not a joint predictive distribution.

Saved rate intercept -0.878055; fixed-old-model/new-encoding probe -0.394701. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | 0.80000 | 0.80000 | -0.5247711 | -0.41982 |
| position_2 | 1.00000 | 1.00000 | -0.2685257 | -0.26853 |
| work_0 | 194.07987 | 194.07987 | 0.0012467 | 0.24195 |
| work_1 | 497.90646 | 497.90646 | 0.0004235 | 0.21088 |
| prior_debut | 1.00000 | 1.00000 | 0.1998819 | 0.19988 |
| pooled_mlb_quality | 0.24439 | 0.24439 | 0.7871816 | 0.19238 |
| work_2 | 267.10992 | 267.10992 | 0.0007180 | 0.19179 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1480284 | 0.14803 |
| pooled_MLB_pa | 501.40000 | 0.83567 | -0.1077920 | -0.09008 |
| draft_rank | 0.32666 | 0.32666 | 0.1588653 | 0.05189 |
| age_squared | 0.64000 | 0.64000 | 0.0788604 | 0.05047 |
| quality_1 | 0.21503 | 0.21503 | 0.2055468 | 0.04420 |

Ordinary combined example. Current 194 MLB PA/2 HR follows 184 and 267 PA, plus minor stints, at age 31. PA falls 263→257 and rate −0.288→−0.406; value 0.631 nearly matches actual 0.631 despite actual 397 PA. That close total partly offsets a low workload with a different rate, not exact player understanding. La Stella, Calhoun and Refsnyder provide contrasting opportunity/performance outcomes.

Origin-selected peers: Tommy La Stella (age 32, MLB/AAA/AA PA 242/38.0/0.0; actual next 195 PA/0.111 wins); Kole Calhoun (age 33, MLB/AAA/AA PA 182/5.0/0.0; actual next 424 PA/-0.357 wins); Rob Refsnyder (age 30, MLB/AAA/AA PA 157/80.0/0.0; actual next 177 PA/1.625 wins).

Training profile: all=127 distinct people; active=102 distinct people.

## Yoán Moncada: 2018 to 2019

Selection: rate_only largest harm.

Age 23; MLB PA 650/231/20; draft pick None, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 207 | 11 | 64 | 26 |
| 2016 | Aplus | 284 | 4 | 60 | 42 |
| 2016 | MLB | 20 | 0 | 12 | 1 |
| 2017 | AAA | 361 | 12 | 102 | 46 |
| 2017 | MLB | 231 | 8 | 74 | 29 |
| 2018 | MLB | 650 | 17 | 217 | 66 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 283.40 | 846.80 | 1430.20 | 0.2300 | 0.323616 | 0.287924 |
| AAA/K | 81.60 | 288.80 | 1430.20 | 0.2300 | 0.269033 | 0.239918 |
| AA/K | 38.40 | 124.20 | 1430.20 | 0.2300 | 0.273863 | 0.236427 |
| Aplus/K | 36.00 | 170.40 | 1430.20 | 0.2300 | 0.218195 | 0.227914 |
| MLB/BB | 89.80 | 846.80 | 1430.20 | 0.0800 | 0.103295 | 0.094414 |
| AAA/BB | 36.80 | 288.80 | 1430.20 | 0.0800 | 0.115226 | 0.088950 |
| AA/BB | 15.60 | 124.20 | 1430.20 | 0.0800 | 0.105263 | 0.083701 |
| Aplus/BB | 25.20 | 170.40 | 1430.20 | 0.0800 | 0.122781 | 0.087560 |
| MLB/HBP | 3.40 | 846.80 | 1430.20 | 0.0100 | 0.004647 | 0.006688 |
| AAA/HBP | 0.00 | 288.80 | 1430.20 | 0.0100 | 0.002572 | 0.008113 |
| AA/HBP | 1.20 | 124.20 | 1430.20 | 0.0100 | 0.009813 | 0.009973 |
| Aplus/HBP | 3.00 | 170.40 | 1430.20 | 0.0100 | 0.014793 | 0.010847 |
| MLB/HR | 23.40 | 846.80 | 1430.20 | 0.0300 | 0.027883 | 0.028690 |
| AAA/HR | 9.60 | 288.80 | 1430.20 | 0.0300 | 0.032407 | 0.030612 |
| AA/HR | 6.60 | 124.20 | 1430.20 | 0.0300 | 0.042819 | 0.031878 |
| Aplus/HR | 2.40 | 170.40 | 1430.20 | 0.0300 | 0.019970 | 0.028228 |
| MLB/BABIP | 151.80 | 443.80 | 763.60 | 0.3000 | 0.334314 | 0.321607 |
| AAA/BABIP | 60.00 | 158.40 | 763.60 | 0.3000 | 0.348297 | 0.314451 |
| AA/BABIP | 22.80 | 61.20 | 763.60 | 0.3000 | 0.327543 | 0.305141 |
| Aplus/BABIP | 39.60 | 100.20 | 763.60 | 0.3000 | 0.347652 | 0.311047 |
| MLB/2B | 39.00 | 846.80 | 1430.20 | 0.0500 | 0.046472 | 0.047817 |
| AAA/2B | 7.20 | 288.80 | 1430.20 | 0.0500 | 0.031379 | 0.045269 |
| AA/2B | 3.60 | 124.20 | 1430.20 | 0.0500 | 0.038359 | 0.048294 |
| Aplus/2B | 15.00 | 170.40 | 1430.20 | 0.0500 | 0.073964 | 0.054235 |
| MLB/3B | 7.60 | 846.80 | 1430.20 | 0.0050 | 0.008555 | 0.007200 |
| AAA/3B | 2.40 | 288.80 | 1430.20 | 0.0050 | 0.007459 | 0.005625 |
| AA/3B | 1.80 | 124.20 | 1430.20 | 0.0050 | 0.010259 | 0.005770 |
| Aplus/3B | 1.80 | 170.40 | 1430.20 | 0.0050 | 0.008506 | 0.005620 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 467.035 | 0.82333 | 2.07877 |
| rate_only | 467.035 | 0.34352 | 1.70529 |
| pa_only | 472.537 | 0.82333 | 2.10326 |
| shared | 472.537 | 0.34352 | 1.72538 |
| Actual | 559 | 3.08002 | 4.57716 |

Product uses PA × (rate/600 + origin replacement 0.0030788), not a joint predictive distribution.

Saved rate intercept -0.605393; fixed-old-model/new-encoding probe 0.337696. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 649.73262 | 649.73262 | 0.0012587 | 0.81783 |
| age_centered | -0.80000 | -0.80000 | -0.5204987 | 0.41640 |
| position_4 | 1.00000 | 1.00000 | -0.1317302 | -0.13173 |
| work_1 | 231.00000 | 231.00000 | 0.0004143 | 0.09571 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.0920847 | -0.09208 |
| quality_present_1 | 1.00000 | 1.00000 | -0.0687471 | -0.06875 |
| regular_window_scaled | 0.33333 | 0.33333 | -0.1864250 | -0.06214 |
| AAA_1_pa | 361.00000 | 0.60167 | -0.0907132 | -0.05458 |
| AA_2_pa | 207.00000 | 0.34500 | -0.1388354 | -0.04790 |
| pooled_AAA_BABIP | 0.31445 | 0.14451 | 0.3009118 | 0.04349 |
| pooled_AA_pa | 124.20000 | 0.20700 | -0.2078448 | -0.04302 |
| pooled_MLB_K | 0.28792 | 0.57924 | -0.0692183 | -0.04009 |

Largest rate-only harm. The known current season has 650 PA/17 HR and 217 K, with 231 prior MLB PA and 361 prior AAA PA. Shared encoding and refit reduce rate 0.823→0.344 while workload barely improves 467→473, worsening value against 559/4.58 actual. The future breakout is not inevitable given strikeouts, but this is a real harmful predictive tradeoff. Candelario and Peraza struggle while Marte breaks out; do not infer uniformly predictable development.

Origin-selected peers: Jeimer Candelario (age 24, MLB/AAA/AA PA 619/9.0/0.0; actual next 386 PA/0.016 wins); José Peraza (age 24, MLB/AAA/AA PA 683/0.0/0.0; actual next 403 PA/-0.318 wins); Ketel Marte (age 24, MLB/AAA/AA PA 580/0.0/0.0; actual next 628 PA/6.537 wins).

Training profile: all=141 distinct people; active=120 distinct people.

## Sean Murphy: 2024 to 2025

Selection: rate_only ordinary.

Age 29; MLB PA 264/438/612; draft pick 83, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 612 | 18 | 124 | 54 |
| 2023 | MLB | 438 | 21 | 98 | 49 |
| 2024 | AAA | 19 | 2 | 4 | 1 |
| 2024 | MLB | 264 | 10 | 67 | 26 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 219.80 | 981.60 | 1000.60 | 0.2300 | 0.224482 | 0.224578 |
| AAA/K | 4.00 | 19.00 | 1000.60 | 0.2300 | 0.226891 | 0.229664 |
| MLB/BB | 97.60 | 981.60 | 1000.60 | 0.0800 | 0.097633 | 0.097329 |
| AAA/BB | 1.00 | 19.00 | 1000.60 | 0.0800 | 0.075630 | 0.079528 |
| MLB/HBP | 25.20 | 981.60 | 1000.60 | 0.0100 | 0.024223 | 0.023978 |
| AAA/HBP | 0.00 | 19.00 | 1000.60 | 0.0100 | 0.008403 | 0.009827 |
| MLB/HR | 37.60 | 981.60 | 1000.60 | 0.0300 | 0.037537 | 0.037407 |
| AAA/HR | 2.00 | 19.00 | 1000.60 | 0.0300 | 0.042017 | 0.031299 |
| MLB/BABIP | 162.20 | 598.60 | 610.60 | 0.3000 | 0.275122 | 0.275542 |
| AAA/BABIP | 3.00 | 12.00 | 610.60 | 0.3000 | 0.294643 | 0.299156 |
| MLB/2B | 44.00 | 981.60 | 1000.60 | 0.0500 | 0.045303 | 0.045384 |
| AAA/2B | 1.00 | 19.00 | 1000.60 | 0.0500 | 0.050420 | 0.050045 |
| MLB/3B | 2.20 | 981.60 | 1000.60 | 0.0050 | 0.002496 | 0.002540 |
| AAA/3B | 0.00 | 19.00 | 1000.60 | 0.0050 | 0.004202 | 0.004914 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 329.203 | -0.11876 | 0.96333 |
| rate_only | 329.203 | -0.13920 | 0.95211 |
| pa_only | 333.457 | -0.11876 | 0.97577 |
| shared | 333.457 | -0.13920 | 0.96441 |
| Actual | 337 | -0.17493 | 0.95185 |

Product uses PA × (rate/600 + origin replacement 0.0031242), not a joint predictive distribution.

Saved rate intercept -0.827716; fixed-old-model/new-encoding probe -0.151981. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_2 | 612.00000 | 612.00000 | 0.0006165 | 0.37732 |
| work_0 | 264.10869 | 264.10869 | 0.0012525 | 0.33080 |
| pooled_mlb_quality | 0.40760 | 0.40760 | 0.7994893 | 0.32587 |
| position_2 | 1.00000 | 1.00000 | -0.2612213 | -0.26122 |
| reorganized | 1.00000 | 1.00000 | -0.2586756 | -0.25868 |
| age_centered | 0.40000 | 0.40000 | -0.5903121 | -0.23612 |
| quality_1 | 0.66182 | 0.66182 | 0.1957083 | 0.12952 |
| prior_debut | 1.00000 | 1.00000 | 0.1258251 | 0.12583 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1211329 | 0.12113 |
| quality_0 | -0.25285 | -0.25285 | 0.4317777 | -0.10918 |
| pooled_MLB_pa | 981.60000 | 1.63600 | -0.0619245 | -0.10131 |
| draft_rank | 0.41864 | 0.41864 | 0.2383202 | 0.09977 |

Ordinary rate-only example. Current 264 MLB PA/10 HR follows 438/21 and 612/18, with a 19-PA AAA stint. Tiny minor rates are appropriately neutralized; rate changes little −0.119→−0.139 and PA 329→333 versus 337 actual. Both products are close to actual 0.952 value. This is a reasonable ordinary forecast but one selected near-zero error cannot outweigh group losses. Hays, Caratini and Fraley have varied later workloads.

Origin-selected peers: Austin Hays (age 28, MLB/AAA/AA PA 255/17.0/17.0; actual next 416 PA/1.772 wins); Victor Caratini (age 30, MLB/AAA/AA PA 274/0.0/6.0; actual next 386 PA/1.441 wins); Jake Fraley (age 29, MLB/AAA/AA PA 382/0.0/0.0; actual next 217 PA/0.738 wins).

Training profile: all=700 distinct people; active=559 distinct people.

## Tyler Flowers: 2018 to 2019

Selection: pa_only ordinary.

Age 32; MLB PA 296/370/325; draft pick None, class unknown; soft roster listing 1. Unchanged legacy quality/workload features remain in this specific test.

| Year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | A | 4 | 0 | 1 | 0 |
| 2016 | AAA | 8 | 0 | 1 | 1 |
| 2016 | MLB | 325 | 8 | 91 | 28 |
| 2016 | RK124 | 2 | 0 | 0 | 0 |
| 2017 | MLB | 370 | 12 | 82 | 30 |
| 2018 | AA | 4 | 0 | 1 | 0 |
| 2018 | AAA | 7 | 0 | 2 | 0 |
| 2018 | MLB | 296 | 8 | 76 | 35 |

Actual transformation: old = prior + centered events/(bucket opportunities + 100); new = prior + centered events/(all-bucket opportunities + 100).

| League/event | Weighted events | Bucket opportunities | All opportunities | Prior | Old | New |
|---|---:|---:|---:|---:|---:|---:|
| MLB/K | 196.20 | 787.00 | 806.40 | 0.2300 | 0.247125 | 0.246759 |
| AAA/K | 2.60 | 11.80 | 806.40 | 0.2300 | 0.228980 | 0.229874 |
| AA/K | 1.00 | 4.00 | 806.40 | 0.2300 | 0.230769 | 0.230088 |
| A/K | 0.60 | 2.40 | 806.40 | 0.2300 | 0.230469 | 0.230053 |
| RK124/K | 0.00 | 1.20 | 806.40 | 0.2300 | 0.227273 | 0.229695 |
| MLB/BB | 75.80 | 787.00 | 806.40 | 0.0800 | 0.094476 | 0.094166 |
| AAA/BB | 0.60 | 11.80 | 806.40 | 0.0800 | 0.076923 | 0.079620 |
| AA/BB | 0.00 | 4.00 | 806.40 | 0.0800 | 0.076923 | 0.079647 |
| A/BB | 0.00 | 2.40 | 806.40 | 0.0800 | 0.078125 | 0.079788 |
| RK124/BB | 0.00 | 1.20 | 806.40 | 0.0800 | 0.079051 | 0.079894 |
| MLB/HBP | 31.60 | 787.00 | 806.40 | 0.0100 | 0.036753 | 0.036180 |
| AAA/HBP | 0.00 | 11.80 | 806.40 | 0.0100 | 0.008945 | 0.009870 |
| AA/HBP | 0.00 | 4.00 | 806.40 | 0.0100 | 0.009615 | 0.009956 |
| A/HBP | 0.00 | 2.40 | 806.40 | 0.0100 | 0.009766 | 0.009974 |
| RK124/HBP | 0.00 | 1.20 | 806.40 | 0.0100 | 0.009881 | 0.009987 |
| MLB/HR | 22.40 | 787.00 | 806.40 | 0.0300 | 0.028636 | 0.028665 |
| AAA/HR | 0.00 | 11.80 | 806.40 | 0.0300 | 0.026834 | 0.029609 |
| AA/HR | 0.00 | 4.00 | 806.40 | 0.0300 | 0.028846 | 0.029868 |
| A/HR | 0.00 | 2.40 | 806.40 | 0.0300 | 0.029297 | 0.029921 |
| RK124/HR | 0.00 | 1.20 | 806.40 | 0.0300 | 0.029644 | 0.029960 |
| MLB/BABIP | 151.40 | 459.60 | 474.20 | 0.3000 | 0.324160 | 0.323546 |
| AAA/BABIP | 1.80 | 8.60 | 474.20 | 0.3000 | 0.292818 | 0.298642 |
| AA/BABIP | 1.00 | 3.00 | 474.20 | 0.3000 | 0.300971 | 0.300174 |
| A/BABIP | 0.00 | 1.80 | 474.20 | 0.3000 | 0.294695 | 0.299060 |
| RK124/BABIP | 0.00 | 1.20 | 474.20 | 0.3000 | 0.296443 | 0.299373 |
| MLB/2B | 32.60 | 787.00 | 806.40 | 0.0500 | 0.042390 | 0.042553 |
| AAA/2B | 0.00 | 11.80 | 806.40 | 0.0500 | 0.044723 | 0.049349 |
| AA/2B | 0.00 | 4.00 | 806.40 | 0.0500 | 0.048077 | 0.049779 |
| A/2B | 0.00 | 2.40 | 806.40 | 0.0500 | 0.048828 | 0.049868 |
| RK124/2B | 0.00 | 1.20 | 806.40 | 0.0500 | 0.049407 | 0.049934 |
| MLB/3B | 0.00 | 787.00 | 806.40 | 0.0050 | 0.000564 | 0.000659 |
| AAA/3B | 0.00 | 11.80 | 806.40 | 0.0050 | 0.004472 | 0.004935 |
| AA/3B | 0.00 | 4.00 | 806.40 | 0.0050 | 0.004808 | 0.004978 |
| A/3B | 0.00 | 2.40 | 806.40 | 0.0050 | 0.004883 | 0.004987 |
| RK124/3B | 0.00 | 1.20 | 806.40 | 0.0050 | 0.004941 | 0.004993 |

| Model | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 286.591 | -0.47652 | 0.65473 |
| rate_only | 286.591 | -0.43002 | 0.67695 |
| pa_only | 294.956 | -0.47652 | 0.67384 |
| shared | 294.956 | -0.43002 | 0.69671 |
| Actual | 310 | -0.53039 | 0.67294 |

Product uses PA × (rate/600 + origin replacement 0.0030788), not a joint predictive distribution.

Saved rate intercept -0.732562; fixed-old-model/new-encoding probe -0.404186. Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.

| Actual new feature | Raw | Fixed scaled | Fitted coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | 1.00000 | 1.00000 | -0.5232834 | -0.52328 |
| pooled_mlb_quality | 0.44088 | 0.44088 | 0.7573181 | 0.33389 |
| position_2 | 1.00000 | 1.00000 | -0.2350187 | -0.23502 |
| work_0 | 295.87824 | 295.87824 | 0.0007892 | 0.23349 |
| work_2 | 325.26771 | 325.26771 | 0.0006845 | 0.22264 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1594261 | -0.15943 |
| prior_debut | 1.00000 | 1.00000 | 0.1210650 | 0.12107 |
| quality_1 | 0.47068 | 0.47068 | 0.2504660 | 0.11789 |
| work_1 | 370.00000 | 370.00000 | 0.0003046 | 0.11271 |
| quality_present_1 | 1.00000 | 1.00000 | 0.0995947 | 0.09959 |
| career_mlb_observed_pa | 2386.00000 | 0.39767 | -0.1802251 | -0.07167 |
| age_squared | 1.00000 | 1.00000 | 0.0563513 | 0.05635 |

Ordinary PA-only example. Three actual MLB seasons of 296/370/325 PA and scattered tiny rehab samples support a part-time age-32 catcher profile. Tiny minor deviations approach zero. PA rises 287→295 toward 310 actual, and PA-only value nearly matches actual 0.673. Combined rate movement makes value less accurate. Fowler, Joyce and Trumbo are origin-selected age/workload peers but not all catcher-role analogues; they provide limited role-specific interpretation.

Origin-selected peers: Dexter Fowler (age 32, MLB/AAA/AA PA 334/0.0/0.0; actual next 574 PA/2.096 wins); Matt Joyce (age 33, MLB/AAA/AA PA 246/35.0/0.0; actual next 238 PA/1.815 wins); Mark Trumbo (age 32, MLB/AAA/AA PA 358/14.0/12.0; actual next 31 PA/-0.166 wins).

Training profile: all=306 distinct people; active=244 distinct people.

## Decision

Do not adopt shared-denominator batting or combined assembly. Both conditional rate and delivered contribution worsen; the rate-only whole-cohort and brief-debut value intervals favor the old encoding. PA-only changes are small/uncertain and do not justify a new working forecast. Useful examples do not outweigh repeated harmful cases. This rejects this particular encoding within this legacy-feature assembly, not minor-league evidence, component forecasts or learned MLB equivalencies.

Next: a coherent MLB event-outcome target, rather than another alteration to the same value-regression inputs. Keep repaired-source V34 and working V33b anchors, fixed cohorts, component and delivered checks. No automatic deployment or 2026 outcomes.
