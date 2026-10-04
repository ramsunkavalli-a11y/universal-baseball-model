# Player walkthrough for minor tracking precision adjustments

Historical next-calendar-year MLB batting only. All rates are custom batting wins per 600 PA; contribution includes batting and replacement, not full WAR. Playing time is fixed.

Cases retain the prior sixteen origins and add the largest gain and ordinary active case. Outcome-selected cases diagnose mechanics; they are not independent confirmation.

Source information shares are before league support routing. Unsupported source groups receive no applied adjustment. Peer distances use origin-known age, actual weighted level PA, draft/rank evidence and MLB PA; not later success.

## Bryce Eldridge at the end of 2024

Selection: retained reviewed origin before fit. Minimum refined profile people: 0. Exact fallback: False.

Eldridge's 519 PA/23 HR include only 35 AAA PA and twenty measured contacts. His mean-EV share is .275 and best-half share .463; the latter's smaller learned noise prior explains the difference, not a hand-selected prospect bonus. Exposure contributes -.081, strong mean/best-half EV recover about +.051, and angle offsets some of that. Rate +.468 to +.422 is a modest reduction, unlike old +.031. The -3.373 actual over 37 PA remains too small to establish talent. Miller/Jenkins/Emerson/Clark all fail to arrive next year, and this profile lacks refined support. No claim about six-year or trade value.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +0.4685 | +0.2659 |
| old_joint | +0.0313 | +0.2163 |
| precision_coverage | +0.4001 | +0.2582 |
| precision_measurements | +0.4222 | +0.2607 |
| Actual | -3.3728 | -0.0839 |

Expected PA 68.1; actual PA 37. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | SINGLE_A | 69 | 1 | 18 | 11 |
| 2023 | ROOKIE_COMPLEX | 61 | 5 | 16 | 8 |
| 2024 | AAA | 35 | 0 | 11 | 4 |
| 2024 | AA | 40 | 1 | 8 | 2 |
| 2024 | HIGH_A | 215 | 12 | 52 | 33 |
| 2024 | SINGLE_A | 229 | 10 | 61 | 17 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Aidan Miller | 20.0 | 0.0 | 39.1 | 0 | -0.442 | -0.558 |
| Walker Jenkins | 19.0 | 0.0 | 116.9 | 0 | +0.159 | +0.006 |
| Colt Emerson | 18.0 | 0.0 | 13.8 | 0 | +0.168 | +0.168 |
| Max Clark | 19.0 | 0.0 | 74.5 | 0 | -0.100 | -0.181 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.27490 | -0.29475 | -0.08103 |
| msp_112_0_best_half_ev | +0.14049 | +0.22852 | +0.03210 |
| msp_112_0_mean_ev | +0.11093 | +0.16941 | +0.01879 |
| msp_112_0_mean_la | -0.08293 | +0.20902 | -0.01733 |
| msp_112_0_hard_air_fraction | +0.04973 | +0.02434 | +0.00121 |
| msp_117_0_exposure | +0.00000 | -0.20081 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Geraldo Perdomo at the end of 2024

Selection: retained reviewed origin before fit, false low. Minimum refined profile people: 6. Exact fallback: False.

Perdomo's fourteen measured AAA contacts get only about 1.4% information share beside his MLB contact history. The new -.9345 rate is virtually unchanged from -.9331; the old apparent improvement to -.6805 no longer comes from an implausibly strong tiny-sample term. His real +2.728 in 720 PA still badly beats the projection and fixed 473 PA. Exposure peers Kirk/Tatis/Ruiz/Moreno have varied workloads and are not identical position/talent matches. This is a remaining base talent/workload miss, not proof the small-sample repair should have forecast the breakout.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.9331 | +0.7409 |
| old_joint | -0.6805 | +0.9399 |
| precision_coverage | -0.9367 | +0.7381 |
| precision_measurements | -0.9345 | +0.7398 |
| Actual | +2.7279 | +5.6890 |

Expected PA 472.6; actual PA 720. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 500 | 5 | 103 | 50 |
| 2023 | MLB | 495 | 6 | 86 | 63 |
| 2024 | MLB | 388 | 3 | 58 | 36 |
| 2024 | AAA | 16 | 0 | 0 | 2 |
| 2024 | ROOKIE_COMPLEX | 11 | 0 | 3 | 2 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alejandro Kirk | 25.0 | 0.0 | 390.1 | 506 | +0.139 | +0.139 |
| Fernando Tatis Jr. | 25.0 | 31.2 | 582.6 | 691 | +1.610 | +1.598 |
| Keibert Ruiz | 25.0 | 0.0 | 359.7 | 267 | -1.147 | -1.147 |
| Gabriel Moreno | 24.0 | 166.6 | 388.2 | 309 | +0.033 | +0.031 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.01435 | -0.29475 | -0.00423 |
| msp_112_0_mean_ev | +0.00705 | +0.16941 | +0.00119 |
| msp_112_0_best_half_ev | +0.00381 | +0.22852 | +0.00087 |
| msp_112_0_mean_la | +0.00404 | +0.20902 | +0.00084 |
| msp_112_0_hard_air_fraction | -0.00198 | +0.02434 | -0.00005 |
| msp_117_0_exposure | +0.00000 | -0.20081 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Narciso Crook at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 5. Exact fallback: False.

Crook has 325 AAA PA/10 HR/117 K and 157 EV readings at mean 87.36. With little MLB history his latest minor share is .773, much larger than a veteran's brief-stint share. The exposure coefficient supplies -.160 of the -.170 adjustment; measured values add little and their conditional EV signs are negative. No next-year MLB PA supplies no observed rate. Lopez/Young/Oliva do not arrive, Johnson does. Lower expected contribution is not evidence his true talent was measured more accurately, and the exposure effect is a residual calibration association rather than causal harm from playing AAA.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.3218 | +0.0210 |
| old_joint | -0.6169 | +0.0170 |
| precision_coverage | -0.4820 | +0.0188 |
| precision_measurements | -0.4920 | +0.0187 |
| Actual | Unobserved | +0.0000 |

Expected PA 8.2; actual PA 0. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AAA | 286 | 11 | 77 | 36 |
| 2021 | AA | 61 | 3 | 19 | 5 |
| 2022 | MLB | 9 | 0 | 3 | 0 |
| 2022 | AAA | 409 | 19 | 124 | 36 |
| 2023 | AAA | 325 | 10 | 117 | 40 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Alejo Lopez | 27.0 | 877.6 | 85.4 | 0 | -2.010 | -2.227 |
| Jared Young | 27.0 | 824.6 | 115.9 | 0 | -0.376 | -0.772 |
| Bryce Johnson | 27.0 | 823.8 | 25.8 | 73 | -0.870 | -0.972 |
| Jared Oliva | 27.0 | 753.6 | 4.3 | 0 | -1.302 | -1.508 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.77317 | -0.20663 | -0.15976 |
| msp_117_0_best_half_ev | +0.17884 | -0.05545 | -0.00992 |
| msp_117_0_mean_la | -0.21910 | +0.01744 | -0.00382 |
| msp_117_0_mean_ev | -0.04668 | -0.07780 | +0.00363 |
| msp_117_0_hard_air_fraction | +0.02586 | -0.01309 | -0.00034 |
| msp_112_0_exposure | +0.00000 | -0.09933 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Bo Bichette at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 4. Exact fallback: False.

Bichette's six AAA contacts alongside 1,453 measured MLB EVs receive .004 information share. The combined +1.449 becomes +1.4475, not the old +.122. This preserves a reasonable forecast before his genuinely poor -2.243 future season, so it gives up the old lucky apparent gain. Latest EV terms together contribute less than -.0005. Pena/Varsho/Vaughn/Grisham all appear with differing workloads. A repair should not reproduce an unreasonable large change merely because it happened to match a later bad season.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +1.4488 | +3.4972 |
| old_joint | +0.1217 | +2.0935 |
| precision_coverage | +1.4480 | +3.4963 |
| precision_measurements | +1.4475 | +3.4959 |
| Actual | -2.2434 | -0.4804 |

Expected PA 634.6; actual PA 336. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | MLB | 690 | 29 | 137 | 40 |
| 2022 | MLB | 697 | 24 | 155 | 41 |
| 2023 | MLB | 601 | 20 | 115 | 27 |
| 2023 | AAA | 6 | 1 | 0 | 0 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Jeremy Peña | 25.0 | 79.8 | 552.3 | 650 | +0.008 | +0.008 |
| Daulton Varsho | 26.0 | 52.2 | 460.9 | 513 | +0.293 | +0.293 |
| Andrew Vaughn | 25.0 | 7.2 | 517.8 | 619 | +0.961 | +0.961 |
| Trent Grisham | 26.0 | 4.2 | 369.5 | 209 | -0.269 | -0.269 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.00400 | -0.20663 | -0.00083 |
| msp_117_0_mean_ev | +0.00417 | -0.07780 | -0.00032 |
| msp_117_0_best_half_ev | +0.00168 | -0.05545 | -0.00009 |
| msp_117_0_mean_la | -0.00083 | +0.01744 | -0.00001 |
| msp_117_0_hard_air_fraction | +0.00045 | -0.01309 | -0.00001 |
| msp_112_0_exposure | +0.00000 | -0.09933 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Nick Kurtz at the end of 2024

Selection: retained reviewed origin before fit. Minimum refined profile people: None. Exact fallback: True.

Kurtz has fifty A/AA PA, 4 HR/10 K/12 UBB and no tracked contact. All adjustment inputs are zero and exact fallback preserves +1.024, versus +5.150 observed in 489 PA and only ten expected PA. Cam Smith and Christian Moore arrive while Wetherholt/Condon do not. Measurement precision cannot supply an unavailable measurement or fix the large opportunity miss. His case stays in overall scoring and is not retrospectively removed for lacking coverage.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +1.0243 | +0.0492 |
| old_joint | +1.0243 | +0.0492 |
| precision_coverage | +1.0243 | +0.0492 |
| precision_measurements | +1.0243 | +0.0492 |
| Actual | +5.1500 | +5.8378 |

Expected PA 10.2; actual PA 489. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | AA | 15 | 0 | 3 | 2 |
| 2024 | SINGLE_A | 35 | 4 | 7 | 10 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cam Smith | 21.0 | 0.0 | 10.0 | 493 | +0.057 | +0.057 |
| JJ Wetherholt | 21.0 | 0.0 | 7.9 | 0 | -0.231 | -0.328 |
| Charlie Condon | 21.0 | 0.0 | 10.0 | 0 | -0.319 | -0.319 |
| Christian Moore | 21.0 | 0.0 | 22.3 | 184 | +0.407 | +0.407 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.00000 | -0.26512 | -0.00000 |
| msp_117_0_exposure | +0.00000 | -0.44158 | -0.00000 |
| msp_123_0_exposure | +0.00000 | -0.13261 | -0.00000 |
| msp_112_1_exposure | +0.00000 | -0.49306 | -0.00000 |
| msp_117_1_exposure | +0.00000 | +0.03572 | +0.00000 |
| msp_123_1_exposure | +0.00000 | -0.20702 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Bo Bichette at the end of 2024

Selection: retained reviewed origin before fit. Minimum refined profile people: 24. Exact fallback: False.

Bichette's eighteen minor contacts over two years sit beside 1,192 MLB EVs. Latest minor share is about .0095, prior-year share .0048. The new -.0212 is nearly the -.0188 base rather than old -1.105; the six-ball angle-SD bypass is absent. That avoids the severe additional false low before his +2.424 rebound in 628 PA, while leaving the base miss and 465-PA forecast visible. Nootbaar/Fortes/Hayes/Carlson show varied career paths. Twenty-four refined people still do not certify every related injury/role mechanism.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.0188 | +1.4388 |
| old_joint | -1.1052 | +0.5961 |
| precision_coverage | -0.0227 | +1.4358 |
| precision_measurements | -0.0212 | +1.4370 |
| Actual | +2.4236 | +4.6435 |

Expected PA 465.4; actual PA 628. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 697 | 24 | 155 | 41 |
| 2023 | MLB | 601 | 20 | 115 | 27 |
| 2023 | AAA | 6 | 1 | 0 | 0 |
| 2024 | MLB | 336 | 4 | 64 | 19 |
| 2024 | AAA | 14 | 0 | 2 | 0 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lars Nootbaar | 26.0 | 79.0 | 425.5 | 583 | +1.228 | +1.218 |
| Nick Fortes | 27.0 | 72.0 | 230.3 | 242 | -1.897 | -1.897 |
| Ke'Bryan Hayes | 27.0 | 9.6 | 393.1 | 570 | -0.752 | -0.752 |
| Dylan Carlson | 25.0 | 31.2 | 88.1 | 241 | -0.586 | -0.595 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.00954 | -0.44158 | -0.00421 |
| msp_117_0_best_half_ev | +0.00533 | +0.13009 | +0.00069 |
| msp_117_0_mean_la | -0.00174 | -0.33421 | +0.00058 |
| msp_117_0_mean_ev | +0.00786 | +0.03833 | +0.00030 |
| msp_117_1_exposure | +0.00480 | +0.03572 | +0.00017 |
| msp_117_1_mean_ev | +0.00500 | +0.02150 | +0.00011 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Yordan Alvarez at the end of 2024

Selection: retained reviewed origin before fit, false high. Minimum refined profile people: 9. Exact fallback: False.

Alvarez's eight old AAA contacts receive .0066 share and change rate +4.030 to +4.0265, not a meaningful talent downgrade. His 635-PA/35-HR prior MLB season explains the high base. Actual 199 PA and +.920 rate versus 547 expected PA still generate the largest false high; later injury knowledge is not a legal predictor. Castro/De La Cruz/Torres/Devers are exposure peers, not uniformly elite-hitting peers. The repair prevents small samples from distracting from the real workload/base uncertainty.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +4.0301 | +5.3779 |
| old_joint | +4.0779 | +5.4214 |
| precision_coverage | +4.0270 | +5.3750 |
| precision_measurements | +4.0265 | +5.3745 |
| Actual | +0.9196 | +0.9726 |

Expected PA 546.5; actual PA 199. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Willi Castro | 27.0 | 32.0 | 491.4 | 454 | -0.570 | -0.570 |
| Bryan De La Cruz | 27.0 | 32.4 | 465.9 | 50 | -0.329 | -0.329 |
| Gleyber Torres | 27.0 | 0.0 | 587.5 | 628 | +0.556 | +0.556 |
| Rafael Devers | 27.0 | 0.0 | 560.3 | 729 | +2.051 | +2.051 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_1_exposure | +0.00656 | -0.49306 | -0.00324 |
| msp_112_1_best_half_ev | -0.00161 | +0.13606 | -0.00022 |
| msp_112_1_mean_ev | -0.00108 | +0.13278 | -0.00014 |
| msp_112_1_mean_la | +0.00166 | -0.03055 | -0.00005 |
| msp_112_1_hard_air_fraction | -0.00137 | +0.00816 | -0.00001 |
| msp_112_0_exposure | +0.00000 | -0.26512 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Colby Thomas at the end of 2024

Selection: ordinary active. Minimum refined profile people: 6. Exact fallback: False.

Thomas has 575 AA/AAA PA in 2024 with 31 HR/142 K/40 UBB, including 314 AAA PA/17 HR. His 186 measured contacts average 87.90 EV and best-half 100.157, with no MLB sample and shares .782/.889. Exposure supplies -.207, best-half recovers +.058 and angle +.027. Rate -.058 to -.172 is nearer the observed -1.123, yet not a precise rate forecast. Delivered .1981 nearly equals .1958 because expected seventy PA versus 132 actual and rate errors offset. Six refined people and peers Durbin/Hickey/Rhylan Thomas/Seymour with very different arrivals show why a near-perfect value is not broad validation.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.0576 | +0.2115 |
| old_joint | +0.0528 | +0.2243 |
| precision_coverage | -0.2206 | +0.1925 |
| precision_measurements | -0.1724 | +0.1981 |
| Actual | -1.1230 | +0.1958 |

Expected PA 69.9; actual PA 132. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | HIGH_A | 237 | 10 | 70 | 11 |
| 2023 | SINGLE_A | 327 | 8 | 76 | 26 |
| 2024 | AAA | 314 | 17 | 95 | 23 |
| 2024 | AA | 261 | 14 | 47 | 17 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Caleb Durbin | 24.0 | 375.0 | 119.5 | 506 | -0.848 | -0.957 |
| Nathan Hickey | 24.0 | 365.0 | 62.5 | 0 | -0.394 | -0.660 |
| Rhylan Thomas | 24.0 | 392.0 | 19.1 | 10 | -0.663 | -0.966 |
| Bob Seymour | 25.0 | 218.0 | 17.5 | 83 | -0.116 | -0.469 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.78190 | -0.26512 | -0.20730 |
| msp_112_0_best_half_ev | +0.17510 | +0.32968 | +0.05773 |
| msp_112_0_mean_la | +0.21684 | +0.12570 | +0.02726 |
| msp_112_0_mean_ev | +0.03897 | +0.18124 | +0.00706 |
| msp_112_0_hard_air_fraction | +0.03109 | +0.01456 | +0.00045 |
| msp_117_0_exposure | +0.00000 | -0.44158 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Elly De La Cruz at the end of 2022

Selection: retained reviewed origin before fit. Minimum refined profile people: 0. Exact fallback: True.

Elly 2022 has a known 76-EV 2021 FSL sample, but no supported mature minor forecast context. Raw source shares are not applied: both heads retain the +.032 base exactly and no new head is fitted for that early cell. Expected 119 versus 427 actual PA remains a miss; future -.748 is a first-year MLB rate. Mead/Luciano/Soderstrom arrive and Cartaya does not. Source reliability alone does not supply historical outcome support.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +0.0324 | +0.3789 |
| old_joint | +0.0324 | +0.3789 |
| precision_coverage | +0.0324 | +0.3789 |
| precision_measurements | +0.0324 | +0.3789 |
| Actual | -0.7476 | +1.1921 |

Expected PA 119.0; actual PA 427. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | SINGLE_A | 210 | 5 | 65 | 10 |
| 2021 | ROOKIE_COMPLEX | 55 | 3 | 15 | 4 |
| 2022 | AA | 207 | 8 | 64 | 15 |
| 2022 | HIGH_A | 306 | 20 | 94 | 23 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Curtis Mead | 21.0 | 96.2 | 175.2 | 92 | +0.414 | +0.414 |
| Marco Luciano | 20.0 | 0.0 | 99.4 | 45 | -0.136 | -0.136 |
| Diego Cartaya | 20.0 | 0.0 | 117.4 | 0 | -0.428 | -0.428 |
| Tyler Soderstrom | 20.0 | 38.0 | 101.0 | 138 | +0.144 | +0.144 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Elly De La Cruz at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 1. Exact fallback: False.

Elly 2023 has 186 AAA PA/12 HR/50 K followed by 427 MLB PA/13 HR/144 K. His 109 IL contacts average 93.37 EV with best-half 105.41. Minor share .229 gives exposure -.087, while conditional EV and best-half coefficients remain negative and add about -.020. New +.082 is less wrong than old -.425, but worse than combined +.189 before +1.886 future rate. Two IL/one FSL refined people remain thin support. Alvarez/Matos/Garcia arrive with varied workloads, Diaz does not. This unresolved negative IL association must not be explained as physically beneficial weak contact.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +0.1887 | +1.3888 |
| old_joint | -0.4247 | +0.9725 |
| precision_coverage | +0.1011 | +1.3294 |
| precision_measurements | +0.0816 | +1.3161 |
| Actual | +1.8857 | +3.7946 |

Expected PA 407.2; actual PA 696. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | SINGLE_A | 210 | 5 | 65 | 10 |
| 2021 | ROOKIE_COMPLEX | 55 | 3 | 15 | 4 |
| 2022 | AA | 207 | 8 | 64 | 15 |
| 2022 | HIGH_A | 306 | 20 | 94 | 23 |
| 2023 | MLB | 427 | 13 | 144 | 32 |
| 2023 | AAA | 186 | 12 | 50 | 26 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Francisco Alvarez | 21.0 | 178.2 | 384.0 | 342 | +0.469 | +0.456 |
| Luis Matos | 21.0 | 152.0 | 263.2 | 156 | -0.267 | -0.338 |
| Jordan Diaz | 22.0 | 265.0 | 218.2 | 0 | -0.004 | +0.005 |
| Maikel Garcia | 23.0 | 260.8 | 484.5 | 626 | +0.084 | +0.049 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.22925 | -0.38111 | -0.08737 |
| msp_117_0_mean_ev | +0.12391 | -0.09036 | -0.01120 |
| msp_117_0_best_half_ev | +0.16158 | -0.05118 | -0.00827 |
| msp_117_0_hard_air_fraction | +0.02926 | -0.01325 | -0.00039 |
| msp_117_0_mean_la | -0.05433 | -0.00137 | +0.00007 |
| msp_112_0_exposure | +0.00000 | -0.12567 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Jimmy Herron at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 7. Exact fallback: False.

Herron has 539 AAA PA/19 HR/103 K and 467 contacts across two years. Mean/best-half power declines from the previous season. Latest share .680/.718 means the measurements can matter; exposure contributes -.086 and lower EV summaries about -.042, giving -.442 versus -.324 base. Actual zero MLB PA makes rate unobserved. Dorrian/Dungan/Mangum/Mendoza also do not arrive. The direction is more intelligible for PCL EV, but reduced contribution among non-arrivals cannot validate measured future talent.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.3236 | +0.0976 |
| old_joint | -0.5597 | +0.0826 |
| precision_coverage | -0.3885 | +0.0935 |
| precision_measurements | -0.4415 | +0.0901 |
| Actual | Unobserved | +0.0000 |

Expected PA 38.2; actual PA 0. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AA | 15 | 0 | 5 | 3 |
| 2022 | AAA | 163 | 4 | 32 | 17 |
| 2022 | AA | 221 | 9 | 37 | 28 |
| 2023 | AAA | 539 | 19 | 103 | 68 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Patrick Dorrian | 27.0 | 699.0 | 13.6 | 0 | -1.134 | -1.575 |
| Clay Dungan | 27.0 | 741.0 | 10.5 | 0 | -1.472 | -1.803 |
| Jake Mangum | 27.0 | 633.4 | 37.7 | 0 | -1.516 | -1.837 |
| Evan Mendoza | 27.0 | 675.8 | 0.8 | 0 | -1.412 | -1.605 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.68005 | -0.12567 | -0.08546 |
| msp_112_0_best_half_ev | -0.15562 | +0.19635 | -0.03056 |
| msp_112_0_mean_ev | -0.11376 | +0.09920 | -0.01129 |
| msp_112_0_mean_la | +0.05722 | +0.16406 | +0.00939 |
| msp_112_0_hard_air_fraction | -0.02080 | +0.00014 | -0.00000 |
| msp_117_0_exposure | +0.00000 | -0.38111 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Junior Caminero at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: None. Exact fallback: True.

Caminero 2023 has 510 AA/A+ PA/31 HR/100 K plus 36 MLB PA, with no tracked minor contact. All additive inputs are zero and +.308 remains exact. Later 177 PA/-.154 rate is retained, not used to manufacture a tracking signal. Luciano/Carter/Crow-Armstrong appear and Lawlar does not. Missing AA measurements remain unknown rather than average or weak talent.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +0.3076 | +0.8432 |
| old_joint | +0.3076 | +0.8432 |
| precision_coverage | +0.3076 | +0.8432 |
| precision_measurements | +0.3076 | +0.8432 |
| Actual | -0.1536 | +0.3634 |

Expected PA 233.7; actual PA 177. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | ROOKIE_COMPLEX | 171 | 9 | 28 | 18 |
| 2022 | SINGLE_A | 117 | 6 | 22 | 8 |
| 2022 | ROOKIE_COMPLEX | 154 | 5 | 21 | 15 |
| 2023 | MLB | 36 | 1 | 8 | 2 |
| 2023 | AA | 351 | 20 | 60 | 31 |
| 2023 | HIGH_A | 159 | 11 | 40 | 10 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Marco Luciano | 21.0 | 78.0 | 226.4 | 81 | -0.279 | -0.274 |
| Evan Carter | 20.0 | 39.0 | 426.3 | 162 | +1.007 | +0.994 |
| Jordan Lawlar | 20.0 | 80.0 | 323.7 | 0 | -1.013 | -1.133 |
| Pete Crow-Armstrong | 21.0 | 158.0 | 272.7 | 410 | +0.039 | -0.088 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.00000 | -0.32769 | -0.00000 |
| msp_117_0_exposure | +0.00000 | -0.51588 | -0.00000 |
| msp_123_0_exposure | +0.00000 | -0.09122 | -0.00000 |
| msp_112_1_exposure | +0.00000 | +0.00000 | +0.00000 |
| msp_117_1_exposure | +0.00000 | +0.00000 | +0.00000 |
| msp_123_1_exposure | +0.00000 | -0.03330 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Wyatt Langford at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 0. Exact fallback: False.

Langford has 200 professional PA/10 HR/34 K/36 UBB, but only thirteen measured AAA contacts. Mean-EV share is .206 and best-half .337; strong best-half contributes +.029. The coverage head's +1.378 becomes +1.407 with values, closer than the +1.439 base but farther from +.549 reality than coverage alone. Fixed 215 versus 557 PA dominates the value miss. No refined active profile exists; Crews arrives among DeLauter/Teel/Shaw/Crews draft peers, who have no AAA history then. This is not a certified successful small-sample talent adjustment.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +1.4386 | +1.1807 |
| old_joint | +1.3548 | +1.1507 |
| precision_coverage | +1.3783 | +1.1591 |
| precision_measurements | +1.4067 | +1.1693 |
| Actual | +0.5491 | +1.7960 |

Expected PA 214.9; actual PA 557. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023 | AAA | 26 | 0 | 6 | 6 |
| 2023 | AA | 54 | 4 | 7 | 11 |
| 2023 | HIGH_A | 106 | 5 | 18 | 18 |
| 2023 | ROOKIE_COMPLEX | 14 | 1 | 3 | 1 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Chase DeLauter | 21.0 | 0.0 | 57.4 | 0 | +0.193 | +0.193 |
| Kyle Teel | 21.0 | 0.0 | 43.5 | 0 | +0.444 | +0.444 |
| Dylan Crews | 21.0 | 0.0 | 49.7 | 132 | +0.310 | +0.310 |
| Matt Shaw | 21.0 | 0.0 | 101.4 | 0 | +0.078 | +0.078 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.20615 | -0.32769 | -0.06755 |
| msp_112_0_best_half_ev | +0.11075 | +0.26060 | +0.02886 |
| msp_112_0_mean_ev | +0.02133 | +0.20256 | +0.00432 |
| msp_112_0_mean_la | +0.02272 | +0.10397 | +0.00236 |
| msp_112_0_hard_air_fraction | +0.00267 | +0.03505 | +0.00009 |
| msp_117_0_exposure | +0.00000 | -0.51588 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Brewer Hicklen at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 1. Exact fallback: False.

Hicklen's 286 AAA PA/10 HR/70 K follow a 559-PA/28-HR/202-K season. His 172 EVs have .798 share because MLB contact history is tiny. Latest IL exposure contributes -.412, measured EV terms roughly -.036, giving -.987 versus -.536 base. Actual -15.356 arises from five PA and is not precise talent truth. Hensley arrives among mostly unsuccessful Sands/Proctor/Deichmann peers; only one refined profile person exists. The large coverage reduction still needs interpretation and cannot be called proof better contact predicts worse batting.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.5360 | +0.0186 |
| old_joint | -1.4190 | +0.0062 |
| precision_coverage | -0.9483 | +0.0128 |
| precision_measurements | -0.9867 | +0.0123 |
| Actual | -15.3563 | -0.1164 |

Expected PA 8.5; actual PA 5. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | AA | 424 | 16 | 132 | 52 |
| 2022 | MLB | 4 | 0 | 4 | 0 |
| 2022 | AAA | 559 | 28 | 202 | 57 |
| 2023 | AAA | 286 | 10 | 70 | 35 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Donny Sands | 27.0 | 663.6 | 30.3 | 0 | -0.957 | -1.357 |
| David Hensley | 27.0 | 664.2 | 135.6 | 58 | -0.451 | -0.442 |
| Ford Proctor | 26.0 | 651.2 | 6.2 | 0 | -0.158 | -0.303 |
| Greg Deichmann | 28.0 | 661.8 | 15.5 | 0 | -1.048 | -1.212 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.79774 | -0.51588 | -0.41154 |
| msp_117_0_mean_ev | +0.25185 | -0.09962 | -0.02509 |
| msp_117_0_best_half_ev | +0.22361 | -0.04999 | -0.01118 |
| msp_117_0_mean_la | +0.11203 | -0.01744 | -0.00195 |
| msp_117_0_hard_air_fraction | +0.05689 | -0.01682 | -0.00096 |
| msp_112_0_exposure | +0.00000 | -0.32769 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Michael Massey at the end of 2023

Selection: retained reviewed origin before fit. Minimum refined profile people: 17. Exact fallback: False.

Massey's eight AAA EVs receive about .016 share, so his very high mean angle no longer contributes the old +.281 term. New rate -.336 is close to combined -.329 and actual +.231. The previous nearly perfect delivered value resulted from rate/workload/environment cancellation, not proven angle precision. Doyle/Duran/Sabol/Outman produce different future workloads. A barely moved forecast can be sensible even if it does not improve this player's individual error.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.3288 | +0.9596 |
| old_joint | -0.3265 | +0.9611 |
| precision_coverage | -0.3370 | +0.9545 |
| precision_measurements | -0.3364 | +0.9549 |
| Actual | +0.2311 | +0.9592 |

Expected PA 376.6; actual PA 356. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | HIGH_A | 439 | 21 | 68 | 33 |
| 2022 | MLB | 194 | 4 | 46 | 9 |
| 2022 | AAA | 143 | 7 | 35 | 13 |
| 2022 | AA | 248 | 9 | 54 | 19 |
| 2023 | MLB | 461 | 15 | 99 | 24 |
| 2023 | AAA | 12 | 0 | 3 | 1 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Brenton Doyle | 25.0 | 89.8 | 354.4 | 603 | -1.452 | -1.469 |
| Ezequiel Duran | 24.0 | 124.0 | 414.3 | 285 | -0.015 | -0.015 |
| Blake Sabol | 25.0 | 80.8 | 218.7 | 38 | -0.556 | -0.556 |
| James Outman | 26.0 | 201.6 | 412.4 | 156 | +0.986 | +0.986 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.01585 | -0.51588 | -0.00818 |
| msp_117_0_mean_ev | -0.00595 | -0.09962 | +0.00059 |
| msp_117_0_mean_la | +0.02130 | -0.01744 | -0.00037 |
| msp_117_0_best_half_ev | -0.00708 | -0.04999 | +0.00035 |
| msp_117_0_hard_air_fraction | -0.00340 | -0.01682 | +0.00006 |
| msp_112_0_exposure | +0.00000 | -0.32769 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Christian Encarnacion-Strand at the end of 2023

Selection: largest gain. Minimum refined profile people: 0. Exact fallback: False.

Encarnacion-Strand has 316 AAA PA/20 HR/69 K/32 UBB and 241 MLB PA/13 HR/69 K/14 UBB at the 2023 origin. There are 210 current IL EVs, mean 90.92/best-half 102.12, plus forty older FSL EVs. Current share .470 gives exposure -.243; measurements supply only about -.025 beyond the coverage forecast. Rate +1.115 to +.848 improves contribution from 2.206 to 2.008 before -.587 actual, but still misses badly; forecast 445 PA versus 123 actual is unchanged. There are zero refined IL profile people. Frelick/Schmitt/Schneider/Velazquez all arrive at varied workloads. This largest gain is mostly coverage calibration, not successful measurement of a future collapse.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +1.1154 | +2.2063 |
| old_joint | +0.2476 | +1.5623 |
| precision_coverage | +0.8723 | +2.0259 |
| precision_measurements | +0.8477 | +2.0076 |
| Actual | -4.2475 | -0.5867 |

Expected PA 445.3; actual PA 123. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2021 | SINGLE_A | 92 | 4 | 26 | 5 |
| 2022 | AA | 208 | 12 | 52 | 9 |
| 2022 | HIGH_A | 330 | 20 | 85 | 29 |
| 2023 | MLB | 241 | 13 | 69 | 14 |
| 2023 | AAA | 316 | 20 | 69 | 32 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sal Frelick | 23.0 | 356.6 | 350.1 | 524 | -0.168 | -0.324 |
| Casey Schmitt | 24.0 | 229.8 | 269.0 | 113 | -0.918 | -1.020 |
| Davis Schneider | 24.0 | 452.0 | 396.0 | 454 | +0.967 | +0.609 |
| Nelson Velázquez | 24.0 | 463.4 | 345.7 | 230 | +0.635 | +0.407 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.47021 | -0.51588 | -0.24257 |
| msp_117_0_mean_ev | +0.13828 | -0.09962 | -0.01378 |
| msp_117_0_best_half_ev | +0.17037 | -0.04999 | -0.00852 |
| msp_117_0_mean_la | +0.12288 | -0.01744 | -0.00214 |
| msp_117_0_hard_air_fraction | +0.04054 | -0.01682 | -0.00068 |
| msp_112_0_exposure | +0.00000 | -0.32769 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Junior Caminero at the end of 2024

Selection: retained reviewed origin before fit, largest harm. Minimum refined profile people: 17. Exact fallback: False.

Caminero 2024 has 236 AAA PA/13 HR/50 K and 177 MLB PA/6 HR/38 K. His 167 readings have mean 93.27/best-half 104.72 and about .454/.488 information share. IL exposure contributes -.150, mean EV -.044 and best-half -.022, partially offset by angle +.025. Rate +.588 to +.397 harms the miss before +2.175 in 653 PA, but far less than old +.094. This remains the largest contribution deterioration. Seventeen refined people and Martinez/Ramos/Hernaiz/Wood peers' varied outcomes do not resolve the negative conditional IL relationship. Small-sample reliability is repaired; representation/calibration is not declared solved.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | +0.5877 | +1.7207 |
| old_joint | +0.0945 | +1.3759 |
| precision_coverage | +0.4341 | +1.6133 |
| precision_measurements | +0.3966 | +1.5871 |
| Actual | +2.1754 | +4.5582 |

Expected PA 419.4; actual PA 653. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2022 | SINGLE_A | 117 | 6 | 22 | 8 |
| 2022 | ROOKIE_COMPLEX | 154 | 5 | 21 | 15 |
| 2023 | MLB | 36 | 1 | 8 | 2 |
| 2023 | AA | 351 | 20 | 60 | 31 |
| 2023 | HIGH_A | 159 | 11 | 40 | 10 |
| 2024 | MLB | 177 | 6 | 38 | 9 |
| 2024 | AAA | 236 | 13 | 50 | 16 |
| 2024 | ROOKIE_COMPLEX | 22 | 3 | 2 | 5 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Angel Martínez | 22.0 | 372.2 | 268.8 | 484 | -0.975 | -1.038 |
| Bryan Ramos | 22.0 | 279.0 | 203.9 | 12 | -0.579 | -0.705 |
| Darell Hernaiz | 22.0 | 359.4 | 188.2 | 197 | -0.979 | -1.222 |
| James Wood | 21.0 | 231.0 | 504.4 | 689 | +1.422 | +1.363 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_117_0_exposure | +0.45397 | -0.32941 | -0.14954 |
| msp_117_0_mean_ev | +0.24896 | -0.17805 | -0.04433 |
| msp_117_0_mean_la | -0.16170 | -0.15509 | +0.02508 |
| msp_117_0_best_half_ev | +0.30618 | -0.07236 | -0.02216 |
| msp_117_0_hard_air_fraction | +0.00836 | -0.02018 | -0.00017 |
| msp_112_0_exposure | +0.00000 | -0.36650 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.

## Juneiker Caceres at the end of 2024

Selection: retained reviewed origin before fit. Minimum refined profile people: None. Exact fallback: True.

Caceres is sixteen with 167 DSL PA, zero HR/18 K/17 UBB and no measurements. Exact fallback keeps -.142. His and Martinez/Sanchez/Rodriguez/Morillo peers' zero next-year MLB PA do not observe batting skill or establish low long-term value. No measurement feature or contact-noise prior substitutes for missing DSL tracking. Retain the long-path player rather than deleting an easy zero to improve the cohort score.

| Forecast | Batting rate | Expected contribution |
| --- | ---: | ---: |
| combined | -0.1415 | +0.0002 |
| old_joint | -0.1415 | +0.0002 |
| precision_coverage | -0.1415 | +0.0002 |
| precision_measurements | -0.1415 | +0.0002 |
| Actual | Unobserved | +0.0000 |

Expected PA 0.1; actual PA 0. No zero-PA rate is fitted or scored.

| Known season | Level | PA | HR | K | Unintentional BB |
| --- | --- | ---: | ---: | ---: | ---: |
| 2024 | ROOKIE_COMPLEX | 167 | 0 | 18 | 17 |

| Origin selected peer | Age | Weighted recent AAA PA | Expected PA | Actual PA | Base rate | Adjusted rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stiven Martinez | 16.0 | 0.0 | 0.1 | 0 | -0.648 | -0.648 |
| Javier Sanchez | 16.0 | 0.0 | 0.1 | 0 | -0.476 | -0.476 |
| Johan Rodriguez | 16.0 | 0.0 | 0.1 | 0 | -0.959 | -0.959 |
| Estivel Morillo | 16.0 | 0.0 | 0.1 | 0 | -0.417 | -0.417 |

| Largest fitted adjustment terms | Actual input | Coefficient | Signed term |
| --- | ---: | ---: | ---: |
| msp_112_0_exposure | +0.00000 | -0.36650 | -0.00000 |
| msp_117_0_exposure | +0.00000 | -0.32941 | -0.00000 |
| msp_123_0_exposure | +0.00000 | -0.10800 | -0.00000 |
| msp_112_1_exposure | +0.00000 | -0.29285 | -0.00000 |
| msp_117_1_exposure | +0.00000 | +0.03780 | +0.00000 |
| msp_123_1_exposure | +0.00000 | -0.06877 | -0.00000 |

All inputs, source/noise references, sample shares, fitted terms, actual next-year history and peer dated production are preserved in reviewed-cases.json. Signed terms are conditional model mechanics, not causal attribution.
