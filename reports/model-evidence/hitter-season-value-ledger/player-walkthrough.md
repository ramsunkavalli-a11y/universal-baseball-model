# Player walks for the season value audit

All forecasts are unchanged. Values are fixed-event custom batting-plus-replacement wins, not full WAR. Actual minus predicted is split into opportunity, hitting and (for the old label) league environment. Exact saved inputs and full source histories accompany these calculations.

## Aaron Judge predicting 2019

Selection: fixed before scoring.

The 2017 breakout (678 MLB PA/52 HR) and 2018 (498/27) reach the MLB branch through pooled quality and separate histories, with 646 recent measured contacts. Quality and workload terms are positive; forecast hitting 3.415 exceeds observed 3.107 and forecast PA 516 exceeds 447. The higher-scoring 2019 league adds .433 to the old common-reference outcome, concealing part of that overforecast. The signed season-relative miss is -.836, not just -.402. Bryant reaches 634 PA while Polanco and Nimmo receive 167/254: differing health/use remains possible without a bad origin forecast.

The selected MLB Statcast Ridge head has intercept -0.822031 plus input terms 4.236731 = 3.414700 batting wins per 600. Appearance 0.984662 × active PA 524.216655 = 516.176410 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4.284813 | 4.527487 | 3.691676 | 4.125119 | -0.606760 | -0.229051 | 0.433443 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 140, 141, 60, 3, 57, 18, 1, 27. Origin/target indexes 0.309735712/0.321303894; replacement reference 0.003080035 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2016 AAA: 410 PA, 19 HR, 98 K, 47 UBB.
- 2016 MLB: 95 PA, 4 HR, 42 K, 9 UBB.
- 2017 MLB: 678 PA, 52 HR, 208 K, 116 UBB.
- 2018 MLB: 498 PA, 27 HR, 152 K, 73 UBB.

Origin-selected peers (expected/actual PA): Kris Bryant 560.8/634; Gregory Polanco 501.2/167; Joc Pederson 379.2/514; Brandon Nimmo 432.3/254.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Aaron Judge predicting 2025

Selection: fixed before scoring.

The origin records 696/458/704 MLB PA and 62/37/58 HR across three seasons. Pooled MLB quality contributes +2.408, recent quality +1.211 and age -.518 to the exact linear sum, with 1025 measured contacts. The main 4.935 hitting estimate improves on 4.534 but remains below actual 6.287. 531 expected versus 679 PA contributes +1.682 to the shortfall; hitting contributes another +1.530. League conditions add only .158 to the older label. This superstar miss is substantive, not explained by recentering. Ozuna, Harper, Schwarber and Profar have 592/580/724/371 actual PA, retaining ordinary downside alongside extreme upside.

The selected MLB Statcast Ridge head has intercept -0.898155 plus input terms 5.833645 = 4.935489 batting wins per 600. Appearance 0.990701 × active PA 535.735066 = 530.753484 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5.668306 | 6.023357 | 9.235708 | 9.393216 | 1.682404 | 1.529947 | 0.157508 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 245, 160, 88, 7, 94, 30, 2, 53. Origin/target indexes 0.305333851/0.308101260; replacement reference 0.003122875 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2022 MLB: 696 PA, 62 HR, 175 K, 92 UBB.
- 2023 MLB: 458 PA, 37 HR, 130 K, 79 UBB.
- 2024 MLB: 704 PA, 58 HR, 171 K, 113 UBB.

Origin-selected peers (expected/actual PA): Marcell Ozuna 513.4/592; Bryce Harper 538.0/580; Kyle Schwarber 581.7/724; Jurickson Profar 548.8/371.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Nick Kurtz predicting 2025

Selection: fixed before scoring.

Only 35 A PA/four HR and fifteen AA PA are present. Fourth-overall draft pedigree and dated rank are known, but the translated branch has no matching active hitting people and the workload profile has zero. Translated other-outcomes +.807 and age +.607 are partly offset by translated strikeouts -.334 and era -.230. Arrival .06056 times 168.16 active PA yields only 10.18 PA against 489. Main hitting 1.024 exceeds old -.063 but is far below 5.150. The value miss has +2.313 opportunity and +3.362 hitting terms; .113 league reference cannot explain it. Origin-selected peers mostly remain minors; this coarse nearest-profile rule does not make them equivalent fourth-overall college prospects. No post-result boost is adopted.

The selected Translated prospect Ridge head has intercept -0.551594 plus input terms 1.575848 = 1.024254 batting wins per 600. Appearance 0.060561 × active PA 168.160355 = 10.183987 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.030730 | 0.049188 | 5.724344 | 5.837777 | 2.312665 | 3.362491 | 0.113434 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 154, 151, 60, 2, 58, 26, 2, 36. Origin/target indexes 0.305333851/0.308101260; replacement reference 0.003122875 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2024 AA: 15 PA, 0 HR, 3 K, 2 UBB.
- 2024 SINGLE_A: 35 PA, 4 HR, 7 K, 10 UBB.

Origin-selected peers (expected/actual PA): Benny Montgomery 5.4/0; Ben Hartl 0.4/0; Wally Soto 0.1/0; Jeferson Quero 130.9/0.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Bo Bichette predicting 2025

Selection: fixed before scoring.

The input history has MLB 697 PA/24 HR, 601/20, then 336/four, with six and fourteen AAA PA in the last two seasons. MLB Statcast, not the minor overlay, is the selected main branch. It receives 1192 MLB measurements; past workload +.573, current workload +.324 and pooled quality +.237 partly offset era -.300. Main hitting -.019 is barely above old -.090; actual 2.424 shows a real rebound miss. Opportunity contributes +.503 and hitting +2.556 to the 3.059 season-relative shortfall. The prior precision repair keeps eighteen minor contacts from dominating, but does not repair this MLB estimate. The broad peer rule selects Rortvedt/Benson/Brujan/Brennan with much less established MLB success; those are exposure/profile diagnostics, not convincing healthy-Bichette talent analogues.

The selected MLB Statcast Ridge head has intercept -0.903745 plus input terms 0.884912 = -0.018833 batting wins per 600. Appearance 0.965625 × active PA 481.975676 = 465.407646 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.383635 | 1.438802 | 4.497847 | 4.643524 | 0.502652 | 2.556393 | 0.145677 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 315, 91, 38, 3, 118, 44, 1, 18. Origin/target indexes 0.305333851/0.308101260; replacement reference 0.003122875 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2022 MLB: 697 PA, 24 HR, 155 K, 41 UBB.
- 2023 AAA: 6 PA, 1 HR, 0 K, 0 UBB.
- 2023 MLB: 601 PA, 20 HR, 115 K, 27 UBB.
- 2024 AAA: 14 PA, 0 HR, 2 K, 0 UBB.
- 2024 MLB: 336 PA, 4 HR, 64 K, 19 UBB.

Origin-selected peers (expected/actual PA): Ben Rortvedt 201.5/128; Will Benson 271.7/253; Vidal Bruján 206.4/95; Will Brennan 322.3/13.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Junior Caminero predicting 2025

Selection: fixed before scoring.

The origin has 236 AAA PA/13 HR and 177 MLB PA/six HR after 2023 AA 351/20 and High-A 159/eleven. The main head uses 152 MLB measurements, age +.748 and current workload +.193, partly offset by era -.269. Its .588 hitting improves on .280 but misses observed 2.175. Arrival .8989 times 466.60 gives 419 PA against 653. The season-relative shortfall is +.958 opportunity and +1.728 hitting, versus just .151 for league reference. Holliday, Dominguez, Wood and Angel Martinez receive 649/429/689/484 PA, consistent with the risk of underallocating advancing players. The negative unadopted minor adjustment remains a separate contrary finding; this audit does not validate it.

The selected MLB Statcast Ridge head has intercept -0.820565 plus input terms 1.408261 = 0.587696 batting wins per 600. Appearance 0.898905 × active PA 466.600752 = 419.429560 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.505376 | 1.720654 | 4.406771 | 4.558248 | 0.958192 | 1.727925 | 0.151477 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 326, 125, 40, 3, 86, 28, 0, 45. Origin/target indexes 0.305333851/0.308101260; replacement reference 0.003122875 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2022 ROOKIE_COMPLEX: 154 PA, 5 HR, 21 K, 15 UBB.
- 2022 SINGLE_A: 117 PA, 6 HR, 22 K, 8 UBB.
- 2023 AA: 351 PA, 20 HR, 60 K, 31 UBB.
- 2023 HIGH_A: 159 PA, 11 HR, 40 K, 10 UBB.
- 2023 MLB: 36 PA, 1 HR, 8 K, 2 UBB.
- 2024 AAA: 236 PA, 13 HR, 50 K, 16 UBB.
- 2024 MLB: 177 PA, 6 HR, 38 K, 9 UBB.
- 2024 ROOKIE_COMPLEX: 22 PA, 3 HR, 2 K, 5 UBB.

Origin-selected peers (expected/actual PA): Jackson Holliday 328.4/649; Jasson Domínguez 285.2/429; James Wood 504.4/689; Angel Martínez 268.8/484.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Steven Kwan predicting 2022

Selection: fixed before scoring.

The cancelled 2020 minor season provides no sample. Actual source history is 2019 High-A 542 PA/three HR/51 K and 2021 AA 221/seven/23 plus AAA 120/five/eight. Translated strikeouts contribute +.331 and age +.428, but translated other-outcomes -.534 and older unavailable rank score -.160 offset that advantage. The translated .253 below-average point is worse than the prior +.106 against actual +1.618. .6957 arrival times 166.69 active PA gives 116 versus 638. The miss remains +1.416 opportunity and +1.990 hitting after removing the -.367 league shift. Carpio, Rodriguez and McKenna never arrive and Jung gets 102 PA, but their broad age/stage/exposure similarity is not equivalent low-strikeout AAA evidence. This is not a solved profile.

The selected Translated prospect Ridge head has intercept -0.416198 plus input terms 0.163077 = -0.253121 batting wins per 600. Appearance 0.695719 × active PA 166.688450 = 115.968394 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.383867 | 0.314488 | 3.719694 | 3.352745 | 1.415668 | 1.989537 | -0.366949 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 343, 60, 60, 7, 130, 25, 7, 6. Origin/target indexes 0.310763804/0.303902205; replacement reference 0.003133713 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2019 HIGH_A: 542 PA, 3 HR, 51 K, 52 UBB.
- 2021 AA: 221 PA, 7 HR, 23 K, 22 UBB.
- 2021 AAA: 120 PA, 5 HR, 8 K, 14 UBB.

Origin-selected peers (expected/actual PA): Luis Carpio 0.7/0; Josh Jung 181.8/102; Brett Rodriguez 0.4/0; Alex McKenna 4.4/0.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Brandon Belt predicting 2024

Selection: fixed before scoring.

The prior MLB samples are 381 PA/29 HR, 298/eight and 404/nineteen. The exact main rate sum uses positive pooled quality +.653 and current workload +.428 against age -.854. .6463 arrival times 377.77 active PA produces 244 PA and .979 contribution; actual MLB PA is zero. Both actual value definitions equal zero, with no observed hitting rate and no league term. The whole signed miss is opportunity -.979. Solano/Martinez/Pham/Blackmon receive 309/495/478/499 PA. This unexpected employment failure is not evidence to tune an ordinary older productive hitter to zero.

The selected MLB Statcast Ridge head has intercept -0.918354 plus input terms 1.465760 = 0.547406 batting wins per 600. Appearance 0.646312 × active PA 377.768520 = 244.156445 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.035277 | 0.978681 | 0.000000 | 0.000000 | -0.978681 | -0.000000 | -0.000000 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 0, 0, 0, 0, 0, 0, 0, 0. Origin/target indexes 0.314721261/0.305333851; replacement reference 0.003096076 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2021 AAA: 15 PA, 0 HR, 3 K, 2 UBB.
- 2021 MLB: 381 PA, 29 HR, 103 K, 45 UBB.
- 2022 MLB: 298 PA, 8 HR, 81 K, 35 UBB.
- 2023 MLB: 404 PA, 19 HR, 141 K, 60 UBB.

Origin-selected peers (expected/actual PA): Donovan Solano 233.7/309; J.D. Martinez 311.7/495; Tommy Pham 238.4/478; Charlie Blackmon 418.6/499.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Eric Thames predicting 2017

Selection: fixed before scoring.

There is no own recent source history in the panel. The main branch is exact current fallback, with age/draft/position terms but no recent Korean production or MLB launch sample. .2067 arrival times 100.49 active PA produces 20.78 PA and .039 contribution; actual is 551 PA and 2.423 hitting per 600. The season-relative shortfall is +1.007 opportunity and +2.878 hitting, versus .209 for league reference. Blanks/Danks/Exposito/Tosoni all have zero actual PA, but absent foreign production means they are not appropriate evidence against this known return. Source incompleteness remains, not an inherently unforecastable breakout.

The selected Current rate fallback head has intercept -0.536320 plus input terms -0.175137 = -0.711457 batting wins per 600. Appearance 0.206741 × active PA 100.491785 = 20.775746 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.039470 | 0.039470 | 3.924819 | 4.133776 | 1.007314 | 2.878035 | 0.208958 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 195, 163, 70, 7, 55, 26, 4, 31. Origin/target indexes 0.313566424/0.318090678; replacement reference 0.003085550 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

No own recent source production; unknown is not zero talent.

Origin-selected peers (expected/actual PA): Kyle Blanks 8.2/0; Jordan Danks 3.7/0; Luis Exposito 0.5/0; Rene Tosoni 0.4/0.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Juneiker Caceres predicting 2025

Selection: fixed before scoring.

The raw source has 167 PA, zero HR, eighteen K and seventeen unintentional walks at league 130; its broad stored label is ROOKIE_COMPLEX. Age contributes +1.179 but translated other-outcomes -.468 and era -.151 offset it. There is no draft/ranking or tracking evidence, no matching hitting/workload people, and no observed next-year MLB rate. .001074 arrival times 62.09 gives .0667 expected PA and .000193 value. All four origin-selected young peers have zero MLB PA. This explains immediate non-arrival expectations, not eventual DSL talent or career value; missing pedigree is not proof of poor ability.

The selected Translated prospect Ridge head has intercept -0.679720 plus input terms 0.538217 = -0.141502 batting wins per 600. Appearance 0.001074 × active PA 62.092822 = 0.066683 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000264 | 0.000193 | 0.000000 | 0.000000 | -0.000193 | 0.000000 | 0.000000 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 0, 0, 0, 0, 0, 0, 0, 0. Origin/target indexes 0.305333851/0.308101260; replacement reference 0.003122875 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2024 ROOKIE_COMPLEX: 167 PA, 0 HR, 18 K, 17 UBB.

Origin-selected peers (expected/actual PA): Stiven Martinez 0.1/0; Javier Sanchez 0.1/0; Johan Rodriguez 0.1/0; Estivel Morillo 0.1/0.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Aaron Judge predicting 2024

Selection: largest main gain on season-relative label.

The largest gain still has a major false low. Source MLB samples are 633 PA/39 HR, 696/62 and 458/37. Pooled quality +1.879, older quality +.558 and recent quality +.543 enter the exact MLB head, with 1031 measured contacts. Main hitting 3.899 improves on 3.360 but actual is 7.558; .9851 arrival times 544.11 gives 536 PA against 704. Value 5.142 versus 11.047 has +1.612 opportunity and +4.293 hitting residual. The old league reference subtracts .554 and understates the miss. Flores has 242 PA and negative value while Harper reaches 631; comparison outcomes retain both successes and failures. The gain supports useful measurements, not a solved superstar forecast.

The selected MLB Statcast Ridge head has intercept -0.918354 plus input terms 4.817161 = 3.898807 batting wins per 600. Appearance 0.985094 × active PA 544.111808 = 536.001072 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4.661469 | 5.142441 | 11.047280 | 10.493320 | 1.611796 | 4.293042 | -0.553959 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 231, 171, 113, 9, 85, 36, 1, 58. Origin/target indexes 0.314721261/0.305333851; replacement reference 0.003096076 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2021 MLB: 633 PA, 39 HR, 158 K, 73 UBB.
- 2022 MLB: 696 PA, 62 HR, 175 K, 92 UBB.
- 2023 MLB: 458 PA, 37 HR, 130 K, 79 UBB.

Origin-selected peers (expected/actual PA): Wilmer Flores 385.8/242; Willson Contreras 449.1/358; Yandy Díaz 498.3/621; Bryce Harper 518.7/631.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Ronald Acuña Jr. predicting 2024

Selection: largest main harm on season-relative label, largest false high.

The largest harm and false high has known 2021/22/23 MLB PA 360/533/735, HR 24/15/41 and K 85/126/84, plus a brief AAA rehab. Pooled quality +1.463, latest quality +.854 and work +.778 enter; recent EV95 adds +.274. .9921 arrival times 592.95 gives 588 PA. Main hitting rises 3.414 to 3.826, reasonable after the demonstrated season, but actual is only 222 PA/.723 rate. The shortfall reverses: opportunity -3.470 and hitting -1.148, with -.175 league term. Soto/Steer reach 713/656 PA, Riley/Tucker 469/339. Later absence is part of actual risk, not justification to use that future absence as an origin input or discard useful contact quality.

The selected MLB Statcast Ridge head has intercept -0.918354 plus input terms 4.744852 = 3.826498 batting wins per 600. Appearance 0.992120 × active PA 592.950106 = 588.277640 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5.168204 | 5.573091 | 0.955014 | 0.780328 | -3.469958 | -1.148119 | -0.174686 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 91, 53, 27, 3, 35, 8, 1, 4. Origin/target indexes 0.314721261/0.305333851; replacement reference 0.003096076 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2021 MLB: 360 PA, 24 HR, 85 K, 47 UBB.
- 2022 AAA: 25 PA, 0 HR, 6 K, 5 UBB.
- 2022 MLB: 533 PA, 15 HR, 126 K, 49 UBB.
- 2023 MLB: 735 PA, 41 HR, 84 K, 77 UBB.

Origin-selected peers (expected/actual PA): Juan Soto 633.9/713; Austin Riley 613.0/469; Kyle Tucker 579.1/339; Spencer Steer 570.6/656.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Aaron Judge predicting 2017

Selection: largest false low.

The largest false low has 410 AAA PA/nineteen HR/98 K and just 95 MLB PA/four HR/42 K after earlier AA/AAA exposure. There are only 43 measured MLB contacts. Age/draft/position add value but negative pooled MLB quality subtracts .117; main hitting .264 beats old -.040 yet falls far below actual 5.330. .9250 arrival times 335.05 gives 310 PA against 678. Season-relative value 8.115 versus 1.093 has +1.298 opportunity and +5.724 hitting residual; league reference adds just .257. Moya has zero PA, Austin 46, Cowart 117 and Difo 365. These outcomes show breakout risk but do not make the model capable of identifying extreme upper tails.

The selected MLB Statcast Ridge head has intercept -0.747861 plus input terms 1.012012 = 0.264151 batting wins per 600. Appearance 0.924997 × active PA 335.052386 = 309.922445 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.935795 | 1.092725 | 8.114763 | 8.371883 | 1.297769 | 5.724268 | 0.257120 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 195, 208, 116, 5, 75, 24, 3, 52. Origin/target indexes 0.313566424/0.318090678; replacement reference 0.003085550 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2014 HIGH_A: 285 PA, 8 HR, 72 K, 49 UBB.
- 2014 SINGLE_A: 278 PA, 9 HR, 59 K, 38 UBB.
- 2015 AA: 280 PA, 12 HR, 70 K, 23 UBB.
- 2015 AAA: 260 PA, 8 HR, 74 K, 29 UBB.
- 2016 AAA: 410 PA, 19 HR, 98 K, 47 UBB.
- 2016 MLB: 95 PA, 4 HR, 42 K, 9 UBB.

Origin-selected peers (expected/actual PA): Steven Moya 212.2/0; Tyler Austin 95.1/46; Kaleb Cowart 136.4/117; Wilmer Difo 180.1/365.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

## Brian Anderson predicting 2023

Selection: ordinary active diagnostic.

The ordinary near-exact value example has MLB 229 PA/eleven HR in short 2020, 264/seven in 2021 and 383/eight in 2022; rehab stays separate. Actual skill counts are not annualized, but historical workload 2020 is separately schedule normalized. Current/older workload contribute +.407/+.390, launch-angle variability -.242 and age -.208. Main hitting -.260 versus actual -.874 is too high. .6861 arrival times 327.27 gives 225 PA versus 361. Contribution .6058 nearly equals .6045 actual only because +.368 opportunity and -.369 hitting cancel. The old league reference adds .327. Trevino/Story have 168 PA, Tim Anderson 524 and Franco zero. This near-perfect total is not proof of correct talent or workload.

The selected MLB Statcast Ridge head has intercept -0.709533 plus input terms 0.449628 = -0.259905 batting wins per 600. Appearance 0.686088 × active PA 327.270620 = 224.536574 expected PA.

| Previous value | Main value | Actual season relative | Actual origin relative | Opportunity miss | Hitting miss | League term |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.611457 | 0.605755 | 0.604533 | 0.931916 | 0.368151 | -0.369372 | 0.327383 |

Observed eight-event vector (other, K, UBB, HBP, 1B, 2B, 3B, HR): 141, 108, 36, 4, 48, 12, 3, 9. Origin/target indexes 0.303902205/0.314721261; replacement reference 0.003130974 per PA. No future reference enters the forecast.

Origin source production (season, level, PA, HR, K, unintentional walks):

- 2020 MLB: 229 PA, 11 HR, 66 K, 21 UBB.
- 2021 AAA: 15 PA, 0 HR, 6 K, 0 UBB.
- 2021 MLB: 264 PA, 7 HR, 65 K, 24 UBB.
- 2022 AAA: 28 PA, 2 HR, 10 K, 2 UBB.
- 2022 MLB: 383 PA, 8 HR, 101 K, 35 UBB.
- 2022 SINGLE_A: 4 PA, 0 HR, 1 K, 2 UBB.

Origin-selected peers (expected/actual PA): Jose Trevino 266.0/168; Trevor Story 479.1/168; Tim Anderson 492.5/524; Maikel Franco 205.5/0.

These broad peers and support counts are diagnostics, not evidence that the comparison players have equivalent talent, pedigree or health.

