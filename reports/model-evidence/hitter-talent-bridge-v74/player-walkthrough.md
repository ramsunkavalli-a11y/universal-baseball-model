# Player review of prospect hitting alternatives

All 16 selected cases are retained. Rate forecasts are batting wins per 600 PA above the expected future MLB average; observed rates here use the realized target MLB average. Delivered values use the separate common-origin event reference and are not full WAR. Non-arrivals have no observed hitting rate. Playing time is fixed throughout.

Cases include nine fixed players and every arm’s largest gains, harms, false highs/lows and ordinary active cases. Peers are selected from same-origin stage, prior debut, age, minor PA and ranking without future outcomes. Outcomes are shown only afterward. Input probes explain saved-model mechanics, not causal effects or validated alternative forecasts.

## Nick Kurtz before 2025

Selection: fixed before fit, scout_ridge largest false low, translated_ridge largest false low. Age 21.0; Upper minors; fold 2. Information cutoff 2025-01-24.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2024 A: 35 / 7 / 10 / 4.
- 2024 AA: 15 / 3 / 2 / 0.

Translated supported exposure 50.0 of 50.0 recency-weighted PA; buckets A,AA. The graph has 12301 pairs and 5620 distinct people, cutoff 2024, held fold 2. Broad/refined active-profile support: broad 31 people, refined 0 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.063 | +0.031 |
| Rankings | +0.099 | +0.033 |
| Rankings and translation | +1.024 | +0.049 |
| Same inputs with trees | +0.042 | +0.033 |
| Actual | +5.150 | +5.838 |

Expected MLB PA 10.2; actual 489. Appearance chance 0.061; conditional PA 168.2. These quantities do not change in this test.

Kurtz is the thin-sample beneficiary but not a solved forecast. The source has 35 A PA with four HR and ten walks, then 15 AA PA with no HR and two walks. Translation raises the linear hitting estimate from -0.063 to +1.024, with +0.693 contributed by the complete translation block. The model still expects only ten MLB PA before 489 actually occurred. Broad active-profile support is 31 people, but the new-draftee/thin-sample intersection has zero; that extrapolation prevents treating his improved point estimate as reliable. Quero and Jett Williams, selected from the same origin profile, did not appear; Cam Smith and Christian Moore did. Pedigree and good tiny-sample production do not justify assuming every such player will arrive immediately.

Saved linear-head replay: rankings contribute +0.044, and the entire translation block +0.693, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: translated_other +0.807; age_centered +0.607; translated_K -0.334; reorganized -0.230.

The same tree fit with only the centered translated event deviations set to zero gives -0.131; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Jeferson Quero: age 21.0, 1 current minor PA, rank score 0.54; later 0 MLB PA. Existing/new translated values +0.192/+0.191. This peer was not selected for that outcome.
- Christian Moore: age 21.0, 110 current minor PA, rank score 0.33; later 184 MLB PA. Existing/new translated values +0.069/+0.085. This peer was not selected for that outcome.
- Cam Smith: age 21.0, 134 current minor PA, rank score 0.42; later 493 MLB PA. Existing/new translated values +0.027/+0.032. This peer was not selected for that outcome.
- Jett Williams: age 20.0, 148 current minor PA, rank score 0.43; later 0 MLB PA. Existing/new translated values +0.295/+0.321. This peer was not selected for that outcome.

## Wyatt Langford before 2024

Selection: fixed before fit. Age 21.0; Upper minors; fold 4. Information cutoff 2024-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2023 AA: 54 / 7 / 11 / 4.
- 2023 AAA: 26 / 6 / 6 / 0.
- 2023 Aplus: 106 / 18 / 18 / 5.
- 2023 RK121: 14 / 3 / 1 / 1.

Translated supported exposure 200.0 of 200.0 recency-weighted PA; buckets AA,AAA,Aplus,RK121. The graph has 11776 pairs and 5400 distinct people, cutoff 2023, held fold 4. Broad/refined active-profile support: broad 33 people, refined 0 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.688 | +0.912 |
| Rankings | +0.962 | +1.010 |
| Rankings and translation | +1.439 | +1.181 |
| Same inputs with trees | +0.668 | +0.905 |
| Actual | +0.549 | +1.796 |

Expected MLB PA 214.9; actual 557. Appearance chance 0.599; conditional PA 358.7. These quantities do not change in this test.

Langford supplies 200 professional PA across four buckets, with ten HR and 36 unintentional walks. The translated linear forecast becomes +1.439 versus the old +0.688 and therefore overshoots his modestly above-average first MLB season more. Translation and ranking terms both raise the fitted sum, but the exact difference also includes refitted original coefficients. The 215 expected PA is unchanged and remains far below his 557. There are no exact new-draftee/thin-sample active training peers. Crews received 132 MLB PA, while DeLauter, Montgomery and Teel did not appear. This is a real tradeoff: better recognizing a talented prospect does not ensure an immediate highly productive MLB batting season.

Saved linear-head replay: rankings contribute +0.178, and the entire translation block +0.474, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.657; translated_other +0.372; scout_listed_0 +0.183; position_7 +0.181.

The same tree fit with only the centered translated event deviations set to zero gives +0.001; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Dylan Crews: age 21.0, 159 current minor PA, rank score 0.94; later 132 MLB PA. Existing/new translated values +0.159/+0.179. This peer was not selected for that outcome.
- Chase DeLauter: age 21.0, 242 current minor PA, rank score 0.70; later 0 MLB PA. Existing/new translated values +0.176/+0.196. This peer was not selected for that outcome.
- Colson Montgomery: age 21.0, 294 current minor PA, rank score 0.92; later 0 MLB PA. Existing/new translated values +0.414/+0.460. This peer was not selected for that outcome.
- Kyle Teel: age 21.0, 114 current minor PA, rank score 0.61; later 0 MLB PA. Existing/new translated values +0.124/+0.167. This peer was not selected for that outcome.

## Cody Bellinger before 2017

Selection: fixed before fit. Age 20.0; Upper minors; fold 3. Information cutoff 2017-01-28.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2016 AA: 465 / 94 / 57 / 23.
- 2016 AAA: 12 / 0 / 1 / 3.

Translated supported exposure 1052.0 of 1052.0 recency-weighted PA; buckets AA,AAA,Aplus,RK128. The graph has 6623 pairs and 3318 distinct people, cutoff 2016, held fold 3. Broad/refined active-profile support: broad 13 people, refined 13 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.085 | +0.331 |
| Rankings | +0.150 | +0.342 |
| Rankings and translation | +0.235 | +0.357 |
| Same inputs with trees | -0.010 | +0.315 |
| Actual | +2.700 | +4.365 |

Expected MLB PA 102.6; actual 548. Appearance chance 0.399; conditional PA 257.0. These quantities do not change in this test.

Bellinger's 2016 AA season has 465 PA, 23 HR and 57 walks, followed by three HR in just 12 AAA PA. The coherent translated profile prevents treating those tiny AAA rates as a large independent sample. The linear forecast rises only +0.150, from +0.085 to +0.235, and remains far below his realized breakout. There are only 13 active training people in the profile. Fixed expected PA of 103 is another large miss before 548 actual. Rosario, Frazier and Barreto received limited opportunities, while Adames did not debut that year. His breakout illustrates conservative readiness and development, not proof that the model should extrapolate three AAA homers at face value.

Saved linear-head replay: rankings contribute +0.120, and the entire translation block +0.068, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.604; draft_class_unknown -0.206; translated_other +0.152; scout_listed_0 +0.144.

The same tree fit with only the centered translated event deviations set to zero gives +0.098; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Amed Rosario: age 20.0, 527 current minor PA, rank score 0.96; later 170 MLB PA. Existing/new translated values +0.380/+0.377. This peer was not selected for that outcome.
- Willy Adames: age 20.0, 568 current minor PA, rank score 0.80; later 0 MLB PA. Existing/new translated values +0.422/+0.496. This peer was not selected for that outcome.
- Clint Frazier: age 21.0, 520 current minor PA, rank score 0.77; later 142 MLB PA. Existing/new translated values +0.648/+0.713. This peer was not selected for that outcome.
- Franklin Barreto: age 20.0, 525 current minor PA, rank score 0.49; later 76 MLB PA. Existing/new translated values +0.718/+0.800. This peer was not selected for that outcome.

## Pete Alonso before 2019

Selection: fixed before fit, translated_ridge largest gain, translated_hist largest false low. Age 23.0; Upper minors; fold 1. Information cutoff 2019-01-27.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2018 AA: 273 / 50 / 40 / 15.
- 2018 AAA: 301 / 78 / 33 / 21.

Translated supported exposure 962.2 of 962.2 recency-weighted PA; buckets AA,AAA,Aminus,Aplus. The graph has 8293 pairs and 4064 distinct people, cutoff 2018, held fold 1. Broad/refined active-profile support: broad 5 people, refined 5 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.286 | +0.765 |
| Rankings | +0.415 | +0.811 |
| Rankings and translation | +0.592 | +0.875 |
| Same inputs with trees | +0.084 | +0.692 |
| Actual | +3.283 | +6.598 |

Expected MLB PA 215.0; actual 693. Appearance chance 0.804; conditional PA 267.6. These quantities do not change in this test.

Alonso's source contains 36 HR in 574 current-year AA/AAA PA, with earlier professional history preserved. Translation plus rankings raises hitting from +0.286 to +0.592 and is the linear arm's largest delivered-value gain, but the newly translated block itself contributes only +0.004 to its fitted sum. Much of this improvement comes from reestimated original terms and rankings, not an independently demonstrated power-translation effect. The rate and 215 expected PA both remain low before his 693-PA breakout. The active profile has only five people. Rooker did not appear, while the origin-selected Edman, Lopez and Thaiss comparisons did; these are not interchangeable first-year outcomes.

Saved linear-head replay: rankings contribute +0.195, and the entire translation block +0.004, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.396; scout_listed_0 +0.194; translated_other +0.156; position_3 +0.154.

The same tree fit with only the centered translated event deviations set to zero gives +0.508; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Tommy Edman: age 23.0, 574 current minor PA, rank score 0.00; later 349 MLB PA. Existing/new translated values +0.089/+0.062. This peer was not selected for that outcome.
- Matt Thaiss: age 23.0, 576 current minor PA, rank score 0.00; later 164 MLB PA. Existing/new translated values +0.196/+0.178. This peer was not selected for that outcome.
- Brent Rooker: age 23.0, 568 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.055/+0.053. This peer was not selected for that outcome.
- Nicky Lopez: age 23.0, 581 current minor PA, rank score 0.00; later 402 MLB PA. Existing/new translated values +0.057/+0.036. This peer was not selected for that outcome.

## Julio Rodríguez before 2022

Selection: fixed before fit. Age 20.0; Upper minors; fold 1. Information cutoff 2022-03-18.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2021 AA: 206 / 37 / 28 / 7.
- 2021 Aplus: 134 / 29 / 14 / 6.

Translated supported exposure 560.2 of 560.2 recency-weighted PA; buckets A,AA,Aplus. The graph has 10055 pairs and 4817 distinct people, cutoff 2021, held fold 1. Broad/refined active-profile support: broad 25 people, refined 25 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.754 | +1.116 |
| Rankings | +1.026 | +1.231 |
| Rankings and translation | +1.216 | +1.311 |
| Same inputs with trees | +0.984 | +1.213 |
| Actual | +2.683 | +3.937 |

Expected MLB PA 254.1; actual 560. Appearance chance 0.805; conditional PA 315.6. These quantities do not change in this test.

Julio's 2021 source shows 340 current A+/AA PA with 13 HR and 42 walks; 2020 is canceled minor evidence, not a failed performance season. The linear forecast rises from +0.754 to +1.216, moving toward his actual MLB production. Rankings contribute +0.249, whereas the total translated block is -0.033, so the gain cannot be credited simply to adding a stronger translated contact profile. His 254 expected PA still misses 560. The active-profile support is 25 people. Casas and Baty had small MLB samples; Valera and Davis did not appear. The model must distinguish recognition of talent from likelihood of immediate full-season opportunity.

Saved linear-head replay: rankings contribute +0.249, and the entire translation block -0.033, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.748; translated_other +0.294; pooled_AA_BABIP +0.225; translated_K -0.175.

The same tree fit with only the centered translated event deviations set to zero gives +1.209; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Triston Casas: age 21.0, 371 current minor PA, rank score 0.85; later 95 MLB PA. Existing/new translated values +0.509/+0.555. This peer was not selected for that outcome.
- Brett Baty: age 21.0, 385 current minor PA, rank score 0.74; later 42 MLB PA. Existing/new translated values +0.376/+0.408. This peer was not selected for that outcome.
- George Valera: age 20.0, 363 current minor PA, rank score 0.54; later 0 MLB PA. Existing/new translated values +0.191/+0.181. This peer was not selected for that outcome.
- Brennen Davis: age 21.0, 416 current minor PA, rank score 0.86; later 0 MLB PA. Existing/new translated values +0.553/+0.658. This peer was not selected for that outcome.

## Jackson Holliday before 2024

Selection: fixed before fit, scout_ridge largest false high, translated_ridge largest harm, translated_ridge largest false high, translated_hist largest false high. Age 19.0; Upper minors; fold 3. Information cutoff 2024-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2023 A: 67 / 13 / 14 / 2.
- 2023 AA: 164 / 34 / 19 / 3.
- 2023 AAA: 91 / 17 / 16 / 2.
- 2023 Aplus: 259 / 54 / 50 / 5.

Translated supported exposure 653.0 of 653.0 recency-weighted PA; buckets A,AA,AAA,Aplus,RK124. The graph has 11718 pairs and 5377 distinct people, cutoff 2023, held fold 3. Broad/refined active-profile support: broad 35 people, refined 35 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.621 | +1.451 |
| Rankings | +0.685 | +1.489 |
| Rankings and translation | +0.826 | +1.571 |
| Same inputs with trees | +0.038 | +1.109 |
| Actual | -2.838 | -0.503 |

Expected MLB PA 351.2; actual 208. Appearance chance 0.887; conditional PA 396.0. These quantities do not change in this test.

Holliday is the largest linear harm and a false high in every arm, not a case to remove. His 2023 history has 581 current professional PA, 12 HR and 99 walks across A through AAA. A +0.826 forecast at his age is not physically absurd, but it misses his difficult first MLB season and increases the old model's overestimate. The translated block and net ranking block are negative in the new fitted sum; his higher final estimate instead reflects changes elsewhere in the refitted head. Trees lower his rate to +0.038 and still overforecast delivered value because the fixed 351 PA also exceed 208. Chourio, Merrill and Wood played substantial MLB time, while Anthony did not. His failure does not justify a blanket penalty for highly ranked young players.

Saved linear-head replay: rankings contribute -0.033, and the entire translation block -0.038, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.873; translated_other +0.352; position_6 -0.236; translated_K -0.214.

The same tree fit with only the centered translated event deviations set to zero gives +0.543; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Jackson Chourio: age 19.0, 583 current minor PA, rank score 0.99; later 573 MLB PA. Existing/new translated values +0.820/+0.821. This peer was not selected for that outcome.
- James Wood: age 20.0, 549 current minor PA, rank score 0.87; later 336 MLB PA. Existing/new translated values +0.752/+0.774. This peer was not selected for that outcome.
- Roman Anthony: age 19.0, 491 current minor PA, rank score 0.77; later 0 MLB PA. Existing/new translated values +0.300/+0.326. This peer was not selected for that outcome.
- Jackson Merrill: age 20.0, 511 current minor PA, rank score 0.89; later 593 MLB PA. Existing/new translated values +0.367/+0.360. This peer was not selected for that outcome.

## Kevin Maitan before 2018

Selection: fixed before fit. Age 17.0; Lower minors; fold 4. Information cutoff 2018-01-27.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2017 RK120: 176 / 49 / 10 / 2.

Translated supported exposure 176.0 of 176.0 recency-weighted PA; buckets RK120. The graph has 7380 pairs and 3649 distinct people, cutoff 2017, held fold 4. Broad/refined active-profile support: broad 0 people, refined 0 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.206 | +0.005 |
| Rankings | -0.099 | +0.006 |
| Rankings and translation | -0.380 | +0.005 |
| Same inputs with trees | -1.377 | +0.002 |
| Actual | Unobserved | +0.000 |

Expected MLB PA 2.0; actual 0. Appearance chance 0.015; conditional PA 130.4. These quantities do not change in this test.

Maitan's 176 rookie PA contain 49 strikeouts, ten walks and two HR. Translation lowers the linear forecast from -0.206 to -0.380 despite positive ranking terms; the tree rate is -1.377. These directions recognize production risk rather than ranking alone. However, his active training profile has zero people, and his observed MLB rate is absent because he did not debut. Two expected PA makes delivered value nearly zero in every arm. All four origin-selected comparisons also had no next-year MLB PA. A no-arrival outcome tests contribution, not whether a negative hypothetical MLB rate was correctly estimated.

Saved linear-head replay: rankings contribute +0.319, and the entire translation block -0.361, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.821; translated_K -0.391; position_6 -0.241; scout_listed_0 +0.214.

The same tree fit with only the centered translated event deviations set to zero gives -0.005; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Diego Infante: age 17.0, 176 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.000/+0.000. This peer was not selected for that outcome.
- Jean Cruz: age 17.0, 175 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.000/+0.000. This peer was not selected for that outcome.
- Andrew Caraballo: age 17.0, 175 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.000/+0.000. This peer was not selected for that outcome.
- Dewins Verbel: age 17.0, 174 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.000/+0.000. This peer was not selected for that outcome.

## Masyn Winn before 2024

Selection: fixed before fit. Age 21.0; Current MLB; fold 4. Information cutoff 2024-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2023 AAA: 498 / 83 / 44 / 18.
- 2023 MLB: 137 / 26 / 10 / 2.

Translated supported exposure 1337.8 of 1337.8 recency-weighted PA; buckets A,AA,AAA,Aplus,MLB. The graph has 11776 pairs and 5400 distinct people, cutoff 2023, held fold 4. Broad/refined active-profile support: broad 15 people, refined 15 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.769 | +0.594 |
| Rankings | -0.769 | +0.594 |
| Rankings and translation | -0.769 | +0.594 |
| Same inputs with trees | -0.769 | +0.594 |
| Actual | +0.255 | +1.741 |

Expected MLB PA 327.1; actual 637. Appearance chance 0.954; conditional PA 342.9. These quantities do not change in this test.

Winn tests the brief-debut boundary. He had 498 AAA PA with 18 HR and 83 strikeouts, plus 137 difficult MLB PA. The primary prospect-only assembly preserves his old -0.769 rate and 327 expected PA exactly because he had debuted. The separately declared all-player translated linear sensitivity gives -0.670, a modest move toward his observed MLB rate, not validation of automatic promotion. Exact active-profile support is 15 people. Crow-Armstrong received 410 MLB PA; Dominguez and Marte smaller samples; Lawlar none. This case keeps the question of using substantial minor evidence after a brief debut visible without changing the established-player branch opportunistically.

Saved linear-head replay: rankings contribute +0.042, and the entire translation block -0.306, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.657; pooled_mlb_quality -0.343; position_6 -0.256; quality_0 -0.232.

The same tree fit with only the centered translated event deviations set to zero gives +0.097; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Pete Crow-Armstrong: age 21.0, 500 current minor PA, rank score 0.85; later 410 MLB PA. Existing/new translated values +0.982/+0.982. This peer was not selected for that outcome.
- Jasson Domínguez: age 20.0, 544 current minor PA, rank score 0.60; later 67 MLB PA. Existing/new translated values +0.989/+0.989. This peer was not selected for that outcome.
- Noelvi Marte: age 21.0, 399 current minor PA, rank score 0.80; later 242 MLB PA. Existing/new translated values +1.114/+1.114. This peer was not selected for that outcome.
- Jordan Lawlar: age 20.0, 490 current minor PA, rank score 0.90; later 0 MLB PA. Existing/new translated values +0.995/+0.995. This peer was not selected for that outcome.

Supplemental review comparisons for an already debuted hitter use current MLB PA and origin-known batting quality instead of minor PA/rank. This addresses the weak original peer match; original peers remain. The rule was added for diagnosis after review, without changing any forecast or score.

- Tyler Soderstrom: age 21.0, origin MLB PA 138, origin quality -0.520; later 213 MLB PA.
- Nolan Schanuel: age 21.0, origin MLB PA 132, origin quality +0.087; later 607 MLB PA.
- Kyren Paris: age 21.0, origin MLB PA 46, origin quality -0.302; later 59 MLB PA.
- Lawrence Butler: age 22.0, origin MLB PA 129, origin quality -0.318; later 451 MLB PA.

## Aaron Judge before 2025

Selection: fixed before fit. Age 32.0; Current MLB; fold 3. Information cutoff 2025-01-24.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2024 MLB: 704 / 171 / 113 / 58.

Translated supported exposure 1488.0 of 1488.0 recency-weighted PA; buckets MLB. The graph has 12522 pairs and 5685 distinct people, cutoff 2024, held fold 3. Broad/refined active-profile support: broad 933 people, refined 931 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +4.534 | +5.668 |
| Rankings | +4.534 | +5.668 |
| Rankings and translation | +4.534 | +5.668 |
| Same inputs with trees | +4.534 | +5.668 |
| Actual | +6.287 | +9.393 |

Expected MLB PA 530.8; actual 679. Appearance chance 0.991; conditional PA 535.7. These quantities do not change in this test.

Judge's three MLB seasons supply 696, 458 and 704 PA with 62, 37 and 58 HR. The primary assembly preserves his +4.534 rate and 531 expected PA, rather than borrowing a prospect model into an established star. The all-player translated linear head stays close at +4.587, but the tree head falls to +3.109. Its same-fit neutral translated-profile probe is even lower at +2.632; extra event inputs help that tree relative to its own probe but do not rescue its overall star compression. This is a reason to retain the established anchor, not to call all trees or all event profiles useless. Age/exposure-selected peers are plainly imperfect talent matches and their limitations are kept visible.

Saved linear-head replay: rankings contribute -0.178, and the entire translation block +0.873, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: pooled_mlb_quality +2.144; quality_0 +1.172; work_0 +0.888; translated_other +0.651.

The same tree fit with only the centered translated event deviations set to zero gives +2.632; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Wilmer Flores: age 32.0, 0 current minor PA, rank score 0.00; later 463 MLB PA. Existing/new translated values +0.616/+0.616. This peer was not selected for that outcome.
- Ildemaro Vargas: age 32.0, 0 current minor PA, rank score 0.00; later 121 MLB PA. Existing/new translated values +0.065/+0.065. This peer was not selected for that outcome.
- Eugenio Suárez: age 32.0, 0 current minor PA, rank score 0.00; later 657 MLB PA. Existing/new translated values +2.091/+2.091. This peer was not selected for that outcome.
- Enrique Hernández: age 32.0, 0 current minor PA, rank score 0.00; later 256 MLB PA. Existing/new translated values +0.064/+0.064. This peer was not selected for that outcome.

Supplemental review comparisons for an already debuted hitter use current MLB PA and origin-known batting quality instead of minor PA/rank. This addresses the weak original peer match; original peers remain. The rule was added for diagnosis after review, without changing any forecast or score.

- Marcell Ozuna: age 33.0, origin MLB PA 688, origin quality +1.518; later 592 MLB PA.
- Bryce Harper: age 31.0, origin MLB PA 631, origin quality +1.097; later 580 MLB PA.
- Kyle Schwarber: age 31.0, origin MLB PA 692, origin quality +1.002; later 724 MLB PA.
- Jurickson Profar: age 31.0, origin MLB PA 668, origin quality +0.932; later 371 MLB PA.

## Eloy Jiménez before 2019

Selection: scout_ridge largest gain. Age 21.0; Upper minors; fold 4. Information cutoff 2019-01-27.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2018 AA: 228 / 39 / 18 / 10.
- 2018 AAA: 228 / 30 / 12 / 12.

Translated supported exposure 1029.6 of 1029.6 recency-weighted PA; buckets A,AA,AAA,Aplus. The graph has 8235 pairs and 3996 distinct people, cutoff 2018, held fold 4. Broad/refined active-profile support: broad 16 people, refined 16 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | +0.126 | +1.151 |
| Rankings | +0.577 | +1.413 |
| Rankings and translation | +0.625 | +1.441 |
| Same inputs with trees | +0.944 | +1.627 |
| Actual | +1.365 | +3.188 |

Expected MLB PA 349.6; actual 504. Appearance chance 0.941; conditional PA 371.5. These quantities do not change in this test.

Jimenez has 456 current AA/AAA PA with 22 HR and only 69 strikeouts. Rankings raise the first alternative from +0.126 to +0.577; translation adds little more, to +0.625, while trees give +0.944. The ranking block contributes approximately +0.546 to the translated head and the translation block -0.090. The new linear model therefore improves a plausible high-talent prospect mainly through pedigree and refitted existing production inputs. Fixed 350 PA remains below 504 actual. Only 16 exact active-profile people support this case. Hayes did not appear, while Rodgers, Riley and Hiura did; high-quality prospects still have different readiness outcomes.

Saved linear-head replay: rankings contribute +0.546, and the entire translation block -0.090, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.567; scout_listed_0 +0.205; draft_class_unknown -0.203; position_7 +0.150.

The same tree fit with only the centered translated event deviations set to zero gives +1.208; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Brendan Rodgers: age 21.0, 474 current minor PA, rank score 0.91; later 81 MLB PA. Existing/new translated values +0.407/+0.550. This peer was not selected for that outcome.
- Austin Riley: age 21.0, 455 current minor PA, rank score 0.63; later 297 MLB PA. Existing/new translated values +0.536/+0.583. This peer was not selected for that outcome.
- Keston Hiura: age 21.0, 535 current minor PA, rank score 0.81; later 348 MLB PA. Existing/new translated values +0.293/+0.328. This peer was not selected for that outcome.
- Ke'Bryan Hayes: age 21.0, 508 current minor PA, rank score 0.55; later 0 MLB PA. Existing/new translated values +0.319/+0.326. This peer was not selected for that outcome.

## J.P. Crawford before 2017

Selection: scout_ridge largest harm. Age 21.0; Upper minors; fold 4. Information cutoff 2017-01-28.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2016 AA: 166 / 21 / 30 / 3.
- 2016 AAA: 385 / 59 / 42 / 4.

Translated supported exposure 1273.8 of 1273.8 recency-weighted PA; buckets A,AA,AAA,Aplus. The graph has 6563 pairs and 3323 distinct people, cutoff 2016, held fold 4. Broad/refined active-profile support: broad 11 people, refined 11 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.488 | +0.870 |
| Rankings | -0.085 | +1.128 |
| Rankings and translation | -0.165 | +1.076 |
| Same inputs with trees | -0.170 | +1.073 |
| Actual | -0.762 | +0.191 |

Expected MLB PA 383.0; actual 87. Appearance chance 0.853; conditional PA 448.9. These quantities do not change in this test.

Crawford is the ranking-only arm's largest harm. His current AA/AAA source shows 551 PA, seven HR and 72 walks. Scouting moves his projected hitting from -0.488 to -0.085, and the translated version backs off to -0.165. His actual rate was near the old forecast, and just 87 MLB PA made the fixed 383-PA allocation much too high. Net ranking terms are positive but the translation block is negative. Rank concerns overall prospect value, not batting alone, so this is a plausible source of imperfect hitting information rather than evidence that ranking is worthless. There are 11 active-profile people; the selected Frazier, Happ and Rosario peers appeared, O'Neill did not.

Saved linear-head replay: rankings contribute +0.445, and the entire translation block -0.250, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.486; draft_class_unknown -0.219; position_6 -0.219; translated_other -0.199.

The same tree fit with only the centered translated event deviations set to zero gives +0.676; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Clint Frazier: age 21.0, 520 current minor PA, rank score 0.77; later 142 MLB PA. Existing/new translated values +0.648/+0.713. This peer was not selected for that outcome.
- Ian Happ: age 21.0, 567 current minor PA, rank score 0.73; later 413 MLB PA. Existing/new translated values +0.308/+0.342. This peer was not selected for that outcome.
- Tyler O'Neill: age 21.0, 575 current minor PA, rank score 0.65; later 0 MLB PA. Existing/new translated values +0.292/+0.331. This peer was not selected for that outcome.
- Amed Rosario: age 20.0, 527 current minor PA, rank score 0.96; later 170 MLB PA. Existing/new translated values +0.380/+0.377. This peer was not selected for that outcome.

## José Azócar before 2022

Selection: scout_ridge ordinary active. Age 25.0; Upper minors; fold 4. Information cutoff 2022-03-18.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2021 AA: 343 / 71 / 35 / 9.
- 2021 AAA: 201 / 45 / 6 / 0.

Translated supported exposure 866.8 of 866.8 recency-weighted PA; buckets AA,AAA. The graph has 9992 pairs and 4724 distinct people, cutoff 2021, held fold 4. Broad/refined active-profile support: broad 272 people, refined 272 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -1.048 | +0.016 |
| Rankings | -1.249 | +0.012 |
| Rankings and translation | -1.328 | +0.011 |
| Same inputs with trees | -1.648 | +0.005 |
| Actual | -1.499 | +0.013 |

Expected MLB PA 11.7; actual 216. Appearance chance 0.123; conditional PA 95.3. These quantities do not change in this test.

Azocar is an ordinary delivered-value case, not an ordinary playing-time forecast. His current AA/AAA year contains 544 PA, nine HR and 41 walks. The linear rate falls from -1.048 to -1.328, moving toward his below-average MLB production. However, expected PA is only 12 before 216 actual. The small delivered-value error partly reflects that low batting rate and cannot be used to call the workload forecast good. The active profile has 272 people; Stefanic later appeared, while Casey, Dungan and Dorrian did not. This distinguishes rate information from the uncertainty in who gets a job.

Saved linear-head replay: rankings contribute -0.277, and the entire translation block -0.334, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.219; translated_K -0.198; scout_rank_score_2 -0.136; scout_listed_2 -0.130.

The same tree fit with only the centered translated event deviations set to zero gives -0.865; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Michael Stefanic: age 25.0, 554 current minor PA, rank score 0.00; later 69 MLB PA. Existing/new translated values +0.036/+0.031. This peer was not selected for that outcome.
- Donovan Casey: age 25.0, 532 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.067/+0.054. This peer was not selected for that outcome.
- Clay Dungan: age 25.0, 499 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.012/+0.007. This peer was not selected for that outcome.
- Patrick Dorrian: age 25.0, 489 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.015/+0.012. This peer was not selected for that outcome.

## Terrin Vavra before 2022

Selection: translated_ridge ordinary active. Age 24.0; Upper minors; fold 3. Information cutoff 2022-03-18.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2021 AA: 184 / 42 / 29 / 5.
- 2021 Aplus: 24 / 6 / 3 / 0.
- 2021 RK124: 10 / 0 / 2 / 0.

Translated supported exposure 489.8 of 489.8 recency-weighted PA; buckets A,AA,Aplus,RK124. The graph has 9986 pairs and 4697 distinct people, cutoff 2021, held fold 3. Broad/refined active-profile support: broad 272 people, refined 272 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.025 | +0.265 |
| Rankings | -0.280 | +0.228 |
| Rankings and translation | -0.216 | +0.237 |
| Same inputs with trees | +0.200 | +0.297 |
| Actual | -0.146 | +0.238 |

Expected MLB PA 85.6; actual 103. Appearance chance 0.496; conditional PA 172.6. These quantities do not change in this test.

Vavra's current source has 184 AA PA with five HR and 29 walks plus 34 lower-level PA. The linear forecast moves from near average (-0.025) to -0.216; fixed 86 expected PA is reasonably close to 103, and this is the translated arm's ordinary active case. Net ranking and translation terms are negative while original inputs partly offset them. Its profile is supported by 272 active people, unlike the very thin newly drafted cases. None of his four nearest origin-selected peers appears next year. His actual return is evidence of uncertain selection even within an apparently well-supported broad population.

Saved linear-head replay: rankings contribute -0.311, and the entire translation block -0.206, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.320; draft_college +0.167; scout_rank_score_2 -0.161; scout_list_available_2 -0.147.

The same tree fit with only the centered translated event deviations set to zero gives +0.809; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Marcos Rivera: age 24.0, 218 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.000/+0.000. This peer was not selected for that outcome.
- Kennie Taylor: age 24.0, 220 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.001/+0.001. This peer was not selected for that outcome.
- Matt Kroon: age 24.0, 215 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.005/+0.003. This peer was not selected for that outcome.
- Reggie Pruitt: age 24.0, 227 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.002/+0.001. This peer was not selected for that outcome.

## Jackson Merrill before 2024

Selection: translated_hist largest gain. Age 20.0; Upper minors; fold 1. Information cutoff 2024-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2023 AA: 211 / 25 / 18 / 5.
- 2023 Aplus: 300 / 37 / 17 / 10.

Translated supported exposure 783.0 of 783.0 recency-weighted PA; buckets A,AA,Aplus,RK121. The graph has 11787 pairs and 5475 distinct people, cutoff 2023, held fold 1. Broad/refined active-profile support: broad 32 people, refined 32 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.306 | +0.367 |
| Rankings | -0.098 | +0.416 |
| Rankings and translation | -0.336 | +0.360 |
| Same inputs with trees | +1.180 | +0.718 |
| Actual | +1.956 | +3.302 |

Expected MLB PA 141.9; actual 593. Appearance chance 0.698; conditional PA 203.4. These quantities do not change in this test.

Merrill is the tree arm's largest gain: 511 current A+/AA PA, 15 HR and 62 strikeouts make a sensible low-strikeout young-hitter profile. The tree forecast rises to +1.180 from the old -0.306, while the translated linear rate remains -0.336. But replacing only the translated deviations with the MLB reference increases the same tree fit to +1.440. Thus its improvement cannot be attributed simply to a beneficial translation adjustment; learned responses to the other inputs and refitting matter. The 142 expected PA still severely misses 593. Wood appeared, but Williams, Caissie and Anthony did not. This useful individual tree result does not overcome the tree arm's broader uncertainty or its Chourio harm.

Saved linear-head replay: rankings contribute +0.044, and the entire translation block -0.615, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.763; translated_other -0.396; position_6 -0.284; scout_list_available_2 -0.168.

The same tree fit with only the centered translated event deviations set to zero gives +1.440; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Carson Williams: age 20.0, 503 current minor PA, rank score 0.81; later 0 MLB PA. Existing/new translated values +0.117/+0.113. This peer was not selected for that outcome.
- James Wood: age 20.0, 549 current minor PA, rank score 0.87; later 336 MLB PA. Existing/new translated values +0.752/+0.774. This peer was not selected for that outcome.
- Owen Caissie: age 20.0, 528 current minor PA, rank score 0.54; later 0 MLB PA. Existing/new translated values +0.311/+0.340. This peer was not selected for that outcome.
- Roman Anthony: age 19.0, 491 current minor PA, rank score 0.77; later 0 MLB PA. Existing/new translated values +0.300/+0.326. This peer was not selected for that outcome.

## Jackson Chourio before 2024

Selection: translated_hist largest harm. Age 19.0; Upper minors; fold 0. Information cutoff 2024-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2023 AA: 559 / 103 / 41 / 22.
- 2023 AAA: 24 / 1 / 2 / 0.

Translated supported exposure 1047.6 of 1047.6 recency-weighted PA; buckets A,AA,AAA,Aplus,DSL. The graph has 11828 pairs and 5453 distinct people, cutoff 2023, held fold 0. Broad/refined active-profile support: broad 33 people, refined 33 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.251 | +0.820 |
| Rankings | -0.125 | +0.884 |
| Rankings and translation | -0.249 | +0.821 |
| Same inputs with trees | -0.822 | +0.529 |
| Actual | +1.328 | +2.592 |

Expected MLB PA 306.3; actual 573. Appearance chance 0.916; conditional PA 334.3. These quantities do not change in this test.

Chourio is the tree arm's largest harm. His current AA season has 559 PA, 22 HR and 103 strikeouts, plus 24 AAA PA with only one strikeout. Despite that promising current-year production, the tree predicts -0.822, below the old -0.251, before positive actual MLB batting. Its same-fit neutral translated-profile probe gives -0.079, identifying a harmful model response to the pooled translated profile. That profile includes earlier low-level history and pooled bucket offsets, not just the latest improved AA season; the experiment does not identify which context or development adjustment is correct. The linear arm stays near its old forecast. Holliday, Wood and Merrill appeared and Anthony did not. This is a concrete limitation of this fitted tree, not permission to ban tree systems generally.

Saved linear-head replay: rankings contribute -0.086, and the entire translation block -0.498, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.827; translated_K -0.286; scout_list_available_2 -0.192; scout_listed_0 +0.173.

The same tree fit with only the centered translated event deviations set to zero gives -0.079; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Jackson Holliday: age 19.0, 581 current minor PA, rank score 1.00; later 208 MLB PA. Existing/new translated values +1.451/+1.571. This peer was not selected for that outcome.
- James Wood: age 20.0, 549 current minor PA, rank score 0.87; later 336 MLB PA. Existing/new translated values +0.752/+0.774. This peer was not selected for that outcome.
- Roman Anthony: age 19.0, 491 current minor PA, rank score 0.77; later 0 MLB PA. Existing/new translated values +0.300/+0.326. This peer was not selected for that outcome.
- Jackson Merrill: age 20.0, 511 current minor PA, rank score 0.89; later 593 MLB PA. Existing/new translated values +0.367/+0.360. This peer was not selected for that outcome.

## Ronny Mauricio before 2023

Selection: translated_hist ordinary active. Age 21.0; Upper minors; fold 0. Information cutoff 2023-01-26.

Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.

- 2022 AA: 541 / 125 / 24 / 26.

Translated supported exposure 903.4 of 903.4 recency-weighted PA; buckets AA,Aplus. The graph has 10959 pairs and 5156 distinct people, cutoff 2022, held fold 0. Broad/refined active-profile support: broad 150 people, refined 150 people. Sparse support remains a limitation.

| Estimate | Hitting rate | Delivered batting value |
| --- | ---: | ---: |
| Existing | -0.926 | +0.111 |
| Rankings | -0.909 | +0.113 |
| Rankings and translation | -0.951 | +0.108 |
| Same inputs with trees | -0.676 | +0.140 |
| Actual | -1.652 | +0.139 |

Expected MLB PA 69.6; actual 108. Appearance chance 0.539; conditional PA 129.3. These quantities do not change in this test.

Mauricio's current AA line has 541 PA, 26 HR, 125 strikeouts and only 24 walks. The translated linear forecast remains around -0.951 versus the old -0.926, while trees give -0.676. Those are coherent caution about a power-heavy, low-walk profile; his actual hitting was below average over 108 PA. The tree arm's ordinary delivered-value case still has only 70 expected PA, and that modest miss must not be hidden by the small value error. The active profile has 150 people. Rojas appeared, while Nunez, Dale and Barrosa did not. No-arrival peers are retained rather than discarded because their batting rate cannot be observed.

Saved linear-head replay: rankings contribute -0.124, and the entire translation block -0.448, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: age_centered +0.608; translated_K -0.354; position_6 -0.273; scout_list_available_2 -0.173.

The same tree fit with only the centered translated event deviations set to zero gives -0.213; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.

Origin-selected comparisons:

- Nasim Nuñez: age 21.0, 549 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.042/+0.031. This peer was not selected for that outcome.
- Jarryd Dale: age 21.0, 552 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.004/+0.002. This peer was not selected for that outcome.
- Jorge Barrosa: age 21.0, 553 current minor PA, rank score 0.00; later 0 MLB PA. Existing/new translated values +0.185/+0.157. This peer was not selected for that outcome.
- Johan Rojas: age 21.0, 556 current minor PA, rank score 0.00; later 164 MLB PA. Existing/new translated values +0.163/+0.101. This peer was not selected for that outcome.
