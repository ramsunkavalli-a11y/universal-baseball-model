# Reconstructed 2020 training cohort: player review

The same 199 features, model settings and 30,506 evaluation rows are retained. Only the training population changes. All case input vectors are unchanged; later fitted partitions, linear coefficients and equal-origin training weights can change. Targets are next-year MLB PA and batting-plus-replacement wins, not full WAR.

Fixed diagnostic cases plus affected largest gain/harm, false high/low and ordinary example. Lux 2023 is explicitly an additional after-scoring missed-season contrast. Peers use only origin information; their later results are displayed, not used for selection.

## Aaron Judge: 2021 to 2022

Selection: Predeclared diagnostic; Largest false low.

Age 29; observed MLB PA current/prior/older 633/114/447; pooled MLB quality 1.56168; soft captured listing 1; known draft 1, pick 32. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AAA | 19 | 1 | 7 | 3 |
| 2019 | MLB | 447 | 27 | 141 | 60 |
| 2020 | MLB | 114 | 9 | 32 | 10 |
| 2021 | MLB | 633 | 39 | 158 | 73 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 462.283 | 1.99020 | 2.98265 |
| cohort | 482.210 | 2.04558 | 3.15572 |
| Actual | 696 | 6.56063 | 9.78949 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031350). This product is not a joint uncertainty distribution.

Fold 3; 4096 distinct origin-2020 training people. Rate fit maximum target year 2021; saved fit hash c895409f75e209c6c3df33c9f2254313203fbd0bd59de2ce00b56e1d4967d08b.

Profile support: all=512 distinct training people; active=426 distinct training people.

Saved linear intercept: -0.9104387785456696. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.56168 | 1.56168 | 0.7079480 | 1.10559 |
| work_0 | 633.26060 | 633.26060 | 0.0012748 | 0.80725 |
| quality_0 | 1.27862 | 1.27862 | 0.4354345 | 0.55675 |
| work_2 | 447.18403 | 447.18403 | 0.0006328 | 0.28300 |
| work_1 | 308.48552 | 308.48552 | 0.0007714 | 0.23797 |
| age_centered | 0.40000 | 0.40000 | -0.5574227 | -0.22297 |
| prior_debut | 1.00000 | 1.00000 | 0.1717276 | 0.17173 |
| pooled_MLB_pa | 992.40000 | 1.65400 | -0.1005598 | -0.16633 |
| quality_2 | 0.84332 | 0.84332 | 0.1552068 | 0.13089 |
| position_9 | 1.00000 | 1.00000 | 0.1288436 | 0.12884 |
| MLB_0_pa | 633.00000 | 1.05500 | -0.1007634 | -0.10631 |
| draft_rank | 0.54404 | 0.54404 | 0.1712167 | 0.09315 |

The unchanged record contains 633 current MLB PA and 39 HR, plus his actual 114-PA shortened 2020 season. Adding other players' 2020 origins raises expected PA 462→482 and conditional batting rate 1.99→2.05 wins/600; actual was 696 PA and 9.79 batting-plus-replacement wins. Directionally sensible but still a major elite-performance miss, not proof that a missing cohort caused it. Turner, Castellanos and Betts supply origin-selected successful comparisons, not guaranteed MVP outcomes.

Origin-selected peers: Trea Turner, age 28, origin MLB 646 PA, draft pick 13: next 708 PA/4.542 wins; Nick Castellanos, age 29, origin MLB 585 PA, draft pick 44: next 558 PA/1.570 wins; Mookie Betts, age 28, origin MLB 550 PA, draft pick 172: next 639 PA/5.359 wins.

## Aaron Judge: 2024 to 2025

Selection: Predeclared diagnostic.

Age 32; observed MLB PA current/prior/older 704/458/696; pooled MLB quality 3.64857; soft captured listing 1; known draft 1, pick 32. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 534.275 | 4.50176 | 5.67779 |
| cohort | 548.496 | 4.55334 | 5.87607 |
| Actual | 679 | 6.28743 | 9.23105 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031242). This product is not a joint uncertainty distribution.

Fold 3; 4096 distinct origin-2020 training people. Rate fit maximum target year 2024; saved fit hash f9e2505c6fdf750def55fa7907721ebfa03f25e0fb05e8369ec151d8469049d2.

Profile support: all=224 distinct training people; active=170 distinct training people.

Saved linear intercept: -0.912483854882465. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 3.64857 | 3.64857 | 0.7361583 | 2.68592 |
| quality_0 | 2.79442 | 2.79442 | 0.4642449 | 1.29730 |
| work_0 | 704.28983 | 704.28983 | 0.0011950 | 0.84161 |
| age_centered | 1.00000 | 1.00000 | -0.5585141 | -0.55851 |
| quality_2 | 2.40833 | 2.40833 | 0.1981901 | 0.47731 |
| work_2 | 696.00000 | 696.00000 | 0.0005950 | 0.41410 |
| quality_1 | 1.31713 | 1.31713 | 0.2167031 | 0.28543 |
| reorganized | 1.00000 | 1.00000 | -0.2769170 | -0.27692 |
| work_1 | 458.00000 | 458.00000 | 0.0005052 | 0.23139 |
| pooled_MLB_BB | 0.15076 | 0.70756 | 0.2733287 | 0.19340 |
| pooled_MLB_pa | 1488.00000 | 2.48000 | -0.0779682 | -0.19336 |
| prior_debut | 1.00000 | 1.00000 | 0.1569581 | 0.15696 |

His unchanged 704-PA, 58-HR season and two preceding strong seasons remain visible. PA rises 534→548 and value 5.68→5.88 versus 679 PA and 9.23 actual. Both heads move modestly; no new Judge statistics were added. This supports retaining the source correction, not claiming elite-player calibration is solved.

Origin-selected peers: Shohei Ohtani, age 29, origin MLB 731 PA, draft pick None: next 727 PA/7.877 wins; Freddie Freeman, age 34, origin MLB 638 PA, draft pick 78: next 627 PA/4.784 wins; Mookie Betts, age 31, origin MLB 516 PA, draft pick 172: next 663 PA/2.398 wins.

## Fernando Tatis Jr.: 2022 to 2023

Selection: Predeclared diagnostic.

Age 23; observed MLB PA current/prior/older 0/546/257; pooled MLB quality 1.36737; soft captured listing 0; known draft 0, pick None. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |
| 2022 | AA | 14 | 0 | 2 | 4 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 150.149 | 1.20289 | 0.77113 |
| cohort | 147.175 | 1.27950 | 0.77465 |
| Actual | 635 | 0.72681 | 2.73521 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031310). This product is not a joint uncertainty distribution.

Fold 0; 4136 distinct origin-2020 training people. Rate fit maximum target year 2022; saved fit hash 828a0836b2af9c26f2c903a42dfddd814f44e7732dbfb17c0c2b7d7f04650f11.

Profile support: all=25 distinct training people; active=14 distinct training people.

Saved linear intercept: -0.7765989772615872. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 1.36737 | 1.36737 | 0.7367316 | 1.00738 |
| age_centered | -0.80000 | -0.80000 | -0.5193455 | 0.41548 |
| work_2 | 695.44543 | 695.44543 | 0.0005866 | 0.40793 |
| quality_1 | 1.34788 | 1.34788 | 0.2465593 | 0.33233 |
| position_6 | 1.00000 | 1.00000 | -0.2891702 | -0.28917 |
| quality_2 | 0.64772 | 0.64772 | 0.2909632 | 0.18846 |
| work_1 | 546.22478 | 546.22478 | 0.0002686 | 0.14669 |
| regular_window_scaled | 0.66667 | 0.66667 | -0.1992174 | -0.13281 |
| reorganized | 1.00000 | 1.00000 | -0.1324516 | -0.13245 |
| pooled_MLB_HR | 0.06773 | 0.37728 | 0.2741175 | 0.10342 |
| quality_present_2 | 1.00000 | 1.00000 | -0.0883816 | -0.08838 |
| pooled_MLB_pa | 591.00000 | 0.98500 | -0.0566763 | -0.05583 |

Current MLB PA is zero but 546 PA/42 HR and 257 PA/17 HR survive in previous seasons. A finite suspension is not an ordinary departure. The source extension leaves PA near 147 versus 635 actual and value near 0.77 versus 2.74. It does not repair status meaning. The nearest generic inactive peers all had zero subsequent PA, illustrating why they are poor substantive suspension analogues; no blanket comeback boost follows.

Origin-selected peers: Rafael Marchán, age 23, origin MLB 0 PA, draft pick None: next 0 PA/0.000 wins; Jorge Ona, age 25, origin MLB 0 PA, draft pick None: next 0 PA/0.000 wins; Ali Sánchez, age 25, origin MLB 0 PA, draft pick None: next 0 PA/0.000 wins.

## Gavin Lux: 2022 to 2023

Selection: Predeclared diagnostic.

Age 24; observed MLB PA current/prior/older 471/381/69; pooled MLB quality 0.10360; soft captured listing 1; known draft 1, pick 20. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 69 | 3 | 19 | 6 |
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 441.236 | 0.09076 | 1.44824 |
| cohort | 436.303 | 0.11053 | 1.44642 |
| Actual | 0 | 0.00000 | 0.00000 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031310). This product is not a joint uncertainty distribution.

Fold 3; 4096 distinct origin-2020 training people. Rate fit maximum target year 2022; saved fit hash e4d0166d6a346df974c4ba5323a07ac7fe779e7d160c6e23e4b10cdaf7b8467d.

Profile support: all=348 distinct training people; active=308 distinct training people.

Saved linear intercept: -0.8545304916388329. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 471.00000 | 471.00000 | 0.0012058 | 0.56794 |
| age_centered | -0.60000 | -0.60000 | -0.5753673 | 0.34522 |
| work_1 | 381.15685 | 381.15685 | 0.0004997 | 0.19048 |
| prior_debut | 1.00000 | 1.00000 | 0.1527144 | 0.15271 |
| position_4 | 1.00000 | 1.00000 | -0.1421688 | -0.14217 |
| reorganized | 1.00000 | 1.00000 | -0.1391116 | -0.13911 |
| quality_0 | 0.29476 | 0.29476 | 0.4051385 | 0.11942 |
| work_2 | 186.71492 | 186.71492 | 0.0006186 | 0.11549 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1132406 | -0.11324 |
| draft_rank | 0.60587 | 0.60587 | 0.1813237 | 0.10986 |
| MLB_0_pa | 471.00000 | 0.78500 | -0.1110595 | -0.08718 |
| pooled_MLB_pa | 817.20000 | 1.36200 | -0.0619767 | -0.08441 |

471 current PA, 6 HR, 95 K and 47 unintentional walks support a plausible continuing-player forecast. PA changes 441→436, while the next season was zero after a later injury not known at this origin. The small reduction is not evidence the model foresaw that injury. Carlson, Naylor and Hoerner show contrasting subsequent workloads; retain the unavoidable future-event limitation.

Origin-selected peers: Dylan Carlson, age 23, origin MLB 488 PA, draft pick 33: next 255 PA/0.289 wins; Josh Naylor, age 25, origin MLB 498 PA, draft pick 12: next 495 PA/2.787 wins; Nico Hoerner, age 25, origin MLB 517 PA, draft pick 24: next 688 PA/2.421 wins.

## Gavin Lux: 2023 to 2024

Selection: Additional missed-season return contrast after scoring.

Age 25; observed MLB PA current/prior/older 0/471/381; pooled MLB quality 0.15072; soft captured listing 1; known draft 1, pick 20. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 199.701 | -0.31786 | 0.51249 |
| cohort | 215.427 | -0.23943 | 0.58101 |
| Actual | 487 | 0.08394 | 1.58897 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0030961). This product is not a joint uncertainty distribution.

Fold 3; 4096 distinct origin-2020 training people. Rate fit maximum target year 2023; saved fit hash 761dd3560a2b0318ab8180a69601092ef67689c5dcaee7d7cd5bcc3e6ccb0d59.

Profile support: all=111 distinct training people; active=9 distinct training people.

Saved linear intercept: -0.9064452719329148. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_2 | 381.15685 | 381.15685 | 0.0006462 | 0.24630 |
| age_centered | -0.40000 | -0.40000 | -0.5713051 | 0.22852 |
| work_1 | 471.00000 | 471.00000 | 0.0004772 | 0.22478 |
| reorganized | 1.00000 | 1.00000 | -0.2065161 | -0.20652 |
| prior_debut | 1.00000 | 1.00000 | 0.1753503 | 0.17535 |
| position_4 | 1.00000 | 1.00000 | -0.1215162 | -0.12152 |
| pooled_mlb_quality | 0.15072 | 0.15072 | 0.7396154 | 0.11147 |
| draft_rank | 0.60587 | 0.60587 | 0.1784066 | 0.10809 |
| quality_present_1 | 1.00000 | 1.00000 | 0.0839272 | 0.08393 |
| pooled_MLB_pa | 605.40000 | 1.00900 | -0.0758599 | -0.07654 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.0689014 | -0.06890 |
| quality_present_2 | 1.00000 | 1.00000 | -0.0686761 | -0.06868 |

Additional missed-season return contrast, selected after scoring and labeled accordingly. The missed 2023 season is zero observed MLB play, not zero prior talent: 471 and 381 PA persist with 6 and 7 HR in the two previous seasons, and an observed roster listing remains. PA rises 200→215 and value 0.51→0.58 versus 487 PA/1.59 actual. The generic nearest peers Plummer, McKay and Stokes all had zero PA; that peer rule inadequately distinguishes a returning established player from marginal exits. A modest improvement still leaves a large return-opportunity miss.

Origin-selected peers: Nick Plummer, age 26, origin MLB 0 PA, draft pick 23: next 0 PA/0.000 wins; Brendan McKay, age 27, origin MLB 0 PA, draft pick 4: next 0 PA/0.000 wins; Troy Stokes Jr., age 27, origin MLB 0 PA, draft pick 116: next 0 PA/0.000 wins.

## Matt McLain: 2024 to 2025

Selection: Predeclared diagnostic.

Age 24; observed MLB PA current/prior/older 0/403/0; pooled MLB quality 0.56675; soft captured listing 0; known draft 1, pick 17. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 155.443 | 0.19783 | 0.53688 |
| cohort | 173.516 | 0.21812 | 0.60517 |
| Actual | 577 | -1.27881 | 0.56815 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031242). This product is not a joint uncertainty distribution.

Fold 2; 4056 distinct origin-2020 training people. Rate fit maximum target year 2024; saved fit hash df87942f39baf2450d2d6203440e3146a35aac13a9679f29f35c802442f78e2f.

Profile support: all=5 distinct training people; active=4 distinct training people.

Saved linear intercept: -0.9722926751733945. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.56675 | 0.56675 | 0.7686747 | 0.43564 |
| age_centered | -0.60000 | -0.60000 | -0.5357663 | 0.32146 |
| reorganized | 1.00000 | 1.00000 | -0.2764789 | -0.27648 |
| position_6 | 1.00000 | 1.00000 | -0.2471043 | -0.24710 |
| prior_debut | 1.00000 | 1.00000 | 0.2261881 | 0.22619 |
| pooled_MLB_BABIP | 0.35515 | 0.55153 | -0.3429205 | -0.18913 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1866282 | 0.18663 |
| pooled_AA_BB | 0.13308 | 0.53082 | 0.3220329 | 0.17094 |
| quality_1 | 0.67281 | 0.67281 | 0.2321475 | 0.15619 |
| AA_2_pa | 452.00000 | 0.75333 | -0.2054518 | -0.15477 |
| pooled_AAA_HR | 0.05164 | 0.21639 | 0.6492275 | 0.14049 |
| pooled_AAA_BABIP | 0.33710 | 0.37104 | 0.3388643 | 0.12573 |

Zero current PA follows 403 MLB PA/16 HR and 180 AAA PA/12 HR. PA rises 155→174 toward the actual 577, but value rises 0.54→0.61 away from actual 0.57. Apparent good delivered-value accuracy hides simultaneous low workload and high rate errors. Generic inactive peers Feliciano, Lee and Swaggerty all failed to return; they do not validate treating every inactive record as medically equivalent.

Origin-selected peers: Mario Feliciano, age 25, origin MLB 0 PA, draft pick 75: next 0 PA/0.000 wins; Khalil Lee, age 26, origin MLB 0 PA, draft pick 103: next 0 PA/0.000 wins; Travis Swaggerty, age 26, origin MLB 0 PA, draft pick 10: next 0 PA/0.000 wins.

## Nick Kurtz: 2024 to 2025

Selection: Predeclared diagnostic.

Age 21; observed MLB PA current/prior/older 0/0/0; pooled MLB quality 0.00000; soft captured listing 0; known draft 1, pick 4. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 50.494 | -0.11288 | 0.14825 |
| cohort | 42.495 | -0.13556 | 0.12316 |
| Actual | 489 | 5.15001 | 5.72099 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031242). This product is not a joint uncertainty distribution.

Fold 2; 4056 distinct origin-2020 training people. Rate fit maximum target year 2024; saved fit hash df87942f39baf2450d2d6203440e3146a35aac13a9679f29f35c802442f78e2f.

Profile support: all=11 distinct training people; active=0 distinct training people.

Saved linear intercept: -0.9722926751733945. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.5357663 | 0.64292 |
| reorganized | 1.00000 | 1.00000 | -0.2764789 | -0.27648 |
| draft_rank | 0.81761 | 0.81761 | 0.1967326 | 0.16085 |
| position_3 | 1.00000 | 1.00000 | 0.1336366 | 0.13364 |
| draft_known | 1.00000 | 1.00000 | -0.0897514 | -0.08975 |
| age_squared | 1.44000 | 1.44000 | 0.0611737 | 0.08809 |
| draft_college | 1.00000 | 1.00000 | 0.0730308 | 0.07303 |
| pooled_A_BB | 0.13333 | 0.53333 | 0.1194926 | 0.06373 |
| absence_window_scaled | 1.00000 | 1.00000 | -0.0553940 | -0.05539 |
| pooled_A_BABIP | 0.31579 | 0.15789 | 0.1987326 | 0.03138 |
| pooled_AA_BABIP | 0.30909 | 0.09091 | 0.3242805 | 0.02948 |
| pooled_AA_BB | 0.08696 | 0.06957 | 0.3220329 | 0.02240 |

Only 50 pro PA are available, alongside a known fourth overall college draft pick. The model lowers PA 50→42 and conditional batting rate −0.11→−0.14; actual was 489 PA and 5.72 wins. The source addition does not repair exceptional fast-entry support or pedigree-to-performance translation. Origin-selected Mayer, Montgomery and Moore had mixed/non-arrival outcomes, so Kurtz's later success does not warrant a universal draft boost.

Origin-selected peers: Marcelo Mayer, age 21, origin MLB 0 PA, draft pick 4: next 136 PA/0.179 wins; Benny Montgomery, age 21, origin MLB 0 PA, draft pick 8: next 0 PA/0.000 wins; Christian Moore, age 21, origin MLB 0 PA, draft pick 8: next 184 PA/0.198 wins.

## Spencer Steer: 2022 to 2023

Selection: Predeclared diagnostic.

Age 24; observed MLB PA current/prior/older 108/0/0; pooled MLB quality -0.08442; soft captured listing 1; known draft 1, pick 90. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 183.018 | -0.23850 | 0.50027 |
| cohort | 180.375 | -0.23663 | 0.49361 |
| Actual | 665 | 1.90921 | 4.17493 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031310). This product is not a joint uncertainty distribution.

Fold 4; 4119 distinct origin-2020 training people. Rate fit maximum target year 2022; saved fit hash 227f01d205d8aaf6a396f902a0f0bb4026a0d1440f25dce02ecf70390261cfe4.

Profile support: all=336 distinct training people; active=298 distinct training people.

Saved linear intercept: -0.8514684858468237. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -0.60000 | -0.60000 | -0.5661824 | 0.33971 |
| work_0 | 108.00000 | 108.00000 | 0.0014575 | 0.15740 |
| reorganized | 1.00000 | 1.00000 | -0.1388722 | -0.13887 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1240387 | -0.12404 |
| position_5 | 1.00000 | 1.00000 | 0.1165084 | 0.11651 |
| prior_debut | 1.00000 | 1.00000 | 0.0861777 | 0.08618 |
| pooled_AA_HR | 0.04625 | 0.16250 | 0.4823267 | 0.07838 |
| pooled_AAA_HR | 0.04128 | 0.11284 | 0.6664119 | 0.07520 |
| pooled_AAA_BB | 0.10092 | 0.20917 | 0.3351410 | 0.07010 |
| pooled_Aplus_BB | 0.13514 | 0.55135 | 0.1243300 | 0.06855 |
| pooled_mlb_quality | -0.08442 | -0.08442 | 0.7492928 | -0.06326 |
| pooled_AA_pa | 380.00000 | 0.63333 | -0.0837474 | -0.05304 |

108 MLB PA/2 HR coexist with 23 upper-minor HR in 2022 and 24 in 2021. Both histories were already present. PA falls 183→180 versus 665 actual, and value stays near 0.49 versus 4.17. Brief-debut opportunity and batting ability remain underrepresented. Jones succeeded while Stowers and Huff received little playing time; a tiny debut does not guarantee a regular job.

Origin-selected peers: Nolan Jones, age 24, origin MLB 94 PA, draft pick 55: next 424 PA/3.981 wins; Kyle Stowers, age 24, origin MLB 98 PA, draft pick 71: next 33 PA/-0.447 wins; Sam Huff, age 24, origin MLB 132 PA, draft pick 219: next 45 PA/0.217 wins.

## Masyn Winn: 2023 to 2024

Selection: Predeclared diagnostic.

Age 21; observed MLB PA current/prior/older 137/0/0; pooled MLB quality -0.55760; soft captured listing 1; known draft 1, pick 54. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 302.679 | -0.79951 | 0.53379 |
| cohort | 305.512 | -0.79671 | 0.54021 |
| Actual | 637 | 0.25454 | 2.25951 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0030961). This product is not a joint uncertainty distribution.

Fold 4; 4119 distinct origin-2020 training people. Rate fit maximum target year 2023; saved fit hash 00d093b765dbcb39d0ed4d3c7c33ef596e02e5d4beafc1b7470a520a619b1d1e.

Profile support: all=384 distinct training people; active=342 distinct training people.

Saved linear intercept: -0.9004847352235831. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| age_centered | -1.20000 | -1.20000 | -0.5753489 | 0.69042 |
| pooled_mlb_quality | -0.55760 | -0.55760 | 0.7521332 | -0.41939 |
| position_6 | 1.00000 | 1.00000 | -0.2732354 | -0.27324 |
| quality_0 | -0.55760 | -0.55760 | 0.4593798 | -0.25615 |
| work_0 | 137.00000 | 137.00000 | 0.0014989 | 0.20535 |
| reorganized | 1.00000 | 1.00000 | -0.1963060 | -0.19631 |
| pooled_MLB_BABIP | 0.24873 | -0.51269 | -0.2399803 | 0.12304 |
| prior_debut | 1.00000 | 1.00000 | 0.1106667 | 0.11067 |
| pooled_A_BB | 0.11834 | 0.38343 | 0.2830017 | 0.10851 |
| age_squared | 1.44000 | 1.44000 | 0.0736397 | 0.10604 |
| AA_1_pa | 403.00000 | 0.67167 | -0.1516872 | -0.10188 |
| pooled_Aplus_BABIP | 0.33687 | 0.36868 | 0.2395102 | 0.08830 |

137 weak MLB PA coexist with 498 AAA PA/18 HR/83 K and 44 walks. PA changes only 303→306 versus 637 actual; value 0.53→0.54 versus 2.26. The model has his longer minor-league record but still makes a conservative opportunity forecast. Soderstrom, Butler and Paris provide mixed future workloads. Representation/reliability is a hypothesis to test, not a missing-statistics claim.

Origin-selected peers: Tyler Soderstrom, age 21, origin MLB 138 PA, draft pick 26: next 213 PA/0.873 wins; Lawrence Butler, age 22, origin MLB 129 PA, draft pick 173: next 451 PA/2.725 wins; Kyren Paris, age 21, origin MLB 46 PA, draft pick 55: next 59 PA/-0.325 wins.

## Matt Olson: 2022 to 2023

Selection: Predeclared diagnostic.

Age 28; observed MLB PA current/prior/older 699/673/245; pooled MLB quality 1.03318; soft captured listing 1; known draft 1, pick 47. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 572.216 | 1.74298 | 3.45386 |
| cohort | 572.650 | 1.85799 | 3.56624 |
| Actual | 720 | 4.57082 | 7.71416 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031310). This product is not a joint uncertainty distribution.

Fold 1; 4125 distinct origin-2020 training people. Rate fit maximum target year 2022; saved fit hash 660f5ca291a253e5a7a0db5fa935dcd6570179795a520880c4f4b696579cf1f0.

Profile support: all=569 distinct training people; active=455 distinct training people.

Saved linear intercept: -0.7217772224812756. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 699.00000 | 699.00000 | 0.0012336 | 0.86231 |
| pooled_mlb_quality | 1.03318 | 1.03318 | 0.7726677 | 0.79831 |
| work_2 | 662.97327 | 662.97327 | 0.0006775 | 0.44919 |
| quality_0 | 0.57358 | 0.57358 | 0.4107189 | 0.23558 |
| quality_1 | 1.07747 | 1.07747 | 0.2155225 | 0.23222 |
| position_3 | 1.00000 | 1.00000 | 0.1591124 | 0.15911 |
| reorganized | 1.00000 | 1.00000 | -0.1437713 | -0.14377 |
| pooled_MLB_pa | 1384.40000 | 2.30733 | -0.0607268 | -0.14012 |
| regular_window_scaled | 1.00000 | 1.00000 | -0.1393649 | -0.13936 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1164190 | 0.11642 |
| age_centered | 0.20000 | 0.20000 | -0.5582823 | -0.11166 |
| MLB_0_pa | 699.00000 | 1.16500 | -0.0897638 | -0.10457 |

699 current PA/34 HR and 673 prior PA/39 HR support an established productive profile. PA barely moves 572→573; conditional rate rises 1.74→1.86, raising value 3.45→3.57 against 720 PA/7.71 actual. This is a changed fitted linear mapping, not changed Olson input data. Seager and Alonso succeeded; Hoskins had zero PA, preventing a guarantee for all productive established players.

Origin-selected peers: Corey Seager, age 28, origin MLB 663 PA, draft pick 18: next 536 PA/5.893 wins; Pete Alonso, age 27, origin MLB 685 PA, draft pick 64: next 658 PA/3.452 wins; Rhys Hoskins, age 29, origin MLB 672 PA, draft pick 142: next 0 PA/0.000 wins.

## Jeff McNeil: 2018 to 2019

Selection: Predeclared diagnostic.

Age 26; observed MLB PA current/prior/older 248/0/0; pooled MLB quality 0.41986; soft captured listing 1; known draft 1, pick 356. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 14 | 1 | 1 | 2 |
| 2017 | AAA | 78 | 1 | 10 | 3 |
| 2017 | Aplus | 116 | 3 | 19 | 6 |
| 2018 | AA | 241 | 14 | 23 | 21 |
| 2018 | AAA | 143 | 5 | 19 | 13 |
| 2018 | MLB | 248 | 3 | 24 | 13 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 399.170 | -0.22474 | 1.07943 |
| cohort | 399.170 | -0.22474 | 1.07943 |
| Actual | 567 | 3.35684 | 4.90426 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0030788). This product is not a joint uncertainty distribution.

Fold 3; 0 distinct origin-2020 training people. Rate fit maximum target year 2018; saved fit hash 06fc7355390c9e393fc6aec19c0d9643663fcfaff1b7d1b3d4f416cf052a14b0.

Profile support: all=354 distinct training people; active=279 distinct training people.

Saved linear intercept: -0.8524019168849333. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 0.41986 | 0.41986 | 0.6877134 | 0.28874 |
| work_0 | 247.89798 | 247.89798 | 0.0007928 | 0.19652 |
| quality_0 | 0.41986 | 0.41986 | 0.4231185 | 0.17765 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.1562874 | -0.15629 |
| pooled_AA_K | 0.13337 | -0.96629 | 0.1490174 | -0.14399 |
| position_4 | 1.00000 | 1.00000 | -0.1398493 | -0.13985 |
| prior_debut | 1.00000 | 1.00000 | 0.1195631 | 0.11956 |
| age_centered | -0.20000 | -0.20000 | -0.5231994 | 0.10464 |
| on_40man | 1.00000 | 1.00000 | 0.1041550 | 0.10415 |
| pooled_AAA_BABIP | 0.33360 | 0.33596 | 0.1984174 | 0.06666 |
| pooled_AA_pa | 249.40000 | 0.41567 | -0.1522839 | -0.06330 |
| pooled_Aplus_BABIP | 0.32933 | 0.29327 | 0.2086771 | 0.06120 |

The earlier fit and forecast are exactly unchanged because 2020-origin outcomes were not yet available. His 248 MLB PA with 24 K coexist with 241 AA PA/14 HR/23 K and 143 AAA PA/5 HR/19 K. Forecast remains 399 PA/1.08 value versus 567/4.90. This is a valuable unresolved brief-debut/contact-representation case; the source repair cannot explain or fix an earlier forecast. Lamb, White and Austin did not reproduce McNeil's outcome.

Origin-selected peers: Jake Lamb, age 27, origin MLB 238 PA, draft pick 213: next 226 PA/0.267 wins; Tyler White, age 27, origin MLB 237 PA, draft pick 977: next 279 PA/-0.195 wins; Tyler Austin, age 26, origin MLB 268 PA, draft pick 415: next 179 PA/0.240 wins.

## Paul Goldschmidt: 2021 to 2022

Selection: Largest gain.

Age 33; observed MLB PA current/prior/older 679/231/682; pooled MLB quality 1.30639; soft captured listing 1; known draft 1, pick 246. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | MLB | 682 | 34 | 166 | 76 |
| 2020 | MLB | 231 | 6 | 43 | 37 |
| 2021 | MLB | 679 | 31 | 136 | 65 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 502.103 | 1.75652 | 3.04402 |
| cohort | 529.442 | 1.97844 | 3.40559 |
| Actual | 651 | 5.37443 | 7.86952 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031350). This product is not a joint uncertainty distribution.

Fold 0; 4136 distinct origin-2020 training people. Rate fit maximum target year 2021; saved fit hash bf3b64960fc592c18c31624fc0a96d02027366e0a8591629044ad38b8524f7a7.

Profile support: all=124 distinct training people; active=103 distinct training people.

Saved linear intercept: -0.7695852627013908. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 679.27954 | 679.27954 | 0.0015138 | 1.02829 |
| pooled_mlb_quality | 1.30639 | 1.30639 | 0.7125664 | 0.93089 |
| age_centered | 1.20000 | 1.20000 | -0.5122021 | -0.61464 |
| work_2 | 682.28077 | 682.28077 | 0.0005957 | 0.40645 |
| quality_0 | 1.09528 | 1.09528 | 0.3557257 | 0.38962 |
| work_1 | 625.08909 | 625.08909 | 0.0004481 | 0.28011 |
| position_3 | 1.00000 | 1.00000 | 0.1929542 | 0.19295 |
| pooled_MLB_pa | 1273.00000 | 2.12167 | -0.0850874 | -0.18053 |
| regular_window_scaled | 1.00000 | 1.00000 | -0.1786472 | -0.17865 |
| draft_college | 1.00000 | 1.00000 | 0.1786423 | 0.17864 |
| quality_1 | 0.53965 | 0.53965 | 0.2723269 | 0.14696 |
| quality_2 | 0.49139 | 0.49139 | 0.2532588 | 0.12445 |

Largest delivered-value gain among affected forecasts. 679 current PA/31 HR and prior productive seasons are unchanged. PA rises 502→529 and rate 1.76→1.98, bringing value 3.04→3.41 toward 651 PA/7.87 actual. A sensible continuity improvement still substantially misses a later exceptional season. Martinez, LeMahieu and Canha offer origin-selected productive but less exceptional outcomes.

Origin-selected peers: J.D. Martinez, age 33, origin MLB 634 PA, draft pick 611: next 596 PA/3.524 wins; DJ LeMahieu, age 32, origin MLB 679 PA, draft pick 79: next 541 PA/2.676 wins; Mark Canha, age 32, origin MLB 625 PA, draft pick 227: next 542 PA/3.292 wins.

## Austin Riley: 2021 to 2022

Selection: Largest harm.

Age 24; observed MLB PA current/prior/older 662/206/297; pooled MLB quality 0.90002; soft captured listing 1; known draft 1, pick 41. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | A | 10 | 0 | 2 | 0 |
| 2019 | AAA | 194 | 15 | 39 | 20 |
| 2019 | MLB | 297 | 18 | 108 | 13 |
| 2020 | MLB | 206 | 8 | 49 | 15 |
| 2021 | MLB | 662 | 33 | 168 | 50 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 579.255 | 1.92227 | 3.67177 |
| cohort | 529.713 | 1.94767 | 3.38016 |
| Actual | 693 | 3.29733 | 5.97818 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031350). This product is not a joint uncertainty distribution.

Fold 1; 4125 distinct origin-2020 training people. Rate fit maximum target year 2021; saved fit hash de836d0f8b14706763e88f60dc8cc08f6b7998138213c1a2c883f80ef9b0ff6c.

Profile support: all=305 distinct training people; active=271 distinct training people.

Saved linear intercept: -0.7514413480567035. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 662.27254 | 662.27254 | 0.0012118 | 0.80256 |
| pooled_mlb_quality | 0.90002 | 0.90002 | 0.7408892 | 0.66681 |
| quality_0 | 1.18354 | 1.18354 | 0.4391138 | 0.51971 |
| age_centered | -0.60000 | -0.60000 | -0.5590538 | 0.33543 |
| work_1 | 557.43875 | 557.43875 | 0.0004142 | 0.23089 |
| work_2 | 297.12227 | 297.12227 | 0.0007049 | 0.20945 |
| pooled_MLB_pa | 1005.00000 | 1.67500 | -0.0964344 | -0.16153 |
| pooled_AAA_HR | 0.05545 | 0.25453 | 0.5138275 | 0.13078 |
| MLB_0_pa | 662.00000 | 1.10333 | -0.0967436 | -0.10674 |
| draft_rank | 0.51143 | 0.51143 | 0.2040391 | 0.10435 |
| regular_window_scaled | 0.66667 | 0.66667 | -0.1443437 | -0.09623 |
| prior_debut | 1.00000 | 1.00000 | 0.0897327 | 0.08973 |

Largest delivered-value deterioration. A strong 662-PA/33-HR current season is visible; adding the reconstructed cohort reduces PA 579→530 despite a slightly better conditional rate. Value falls 3.67→3.38 versus 693 PA/5.98 actual. This is a learned partition/weighting tradeoff, not missing Riley history. It directly contradicts any claim that the repaired year uniformly fixes established-player opportunity.

Origin-selected peers: Bo Bichette, age 23, origin MLB 690 PA, draft pick 66: next 697 PA/4.413 wins; Jonathan India, age 24, origin MLB 631 PA, draft pick 5: next 431 PA/1.547 wins; Alex Verdugo, age 25, origin MLB 604 PA, draft pick 62: next 644 PA/2.577 wins.

## Yordan Alvarez: 2024 to 2025

Selection: Largest false high.

Age 27; observed MLB PA current/prior/older 635/496/561; pooled MLB quality 2.45709; soft captured listing 1; known draft 0, pick None. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 601.307 | 3.76103 | 5.64780 |
| cohort | 584.774 | 3.70970 | 5.44249 |
| Actual | 199 | 0.91965 | 0.92510 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031242). This product is not a joint uncertainty distribution.

Fold 2; 4056 distinct origin-2020 training people. Rate fit maximum target year 2024; saved fit hash df87942f39baf2450d2d6203440e3146a35aac13a9679f29f35c802442f78e2f.

Profile support: all=439 distinct training people; active=346 distinct training people.

Saved linear intercept: -0.9722926751733945. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| pooled_mlb_quality | 2.45709 | 2.45709 | 0.7686747 | 1.88870 |
| work_0 | 635.26142 | 635.26142 | 0.0012040 | 0.76488 |
| quality_0 | 1.41565 | 1.41565 | 0.4827143 | 0.68336 |
| work_2 | 561.00000 | 561.00000 | 0.0008145 | 0.45694 |
| quality_2 | 1.73811 | 1.73811 | 0.1943126 | 0.33774 |
| quality_1 | 1.38309 | 1.38309 | 0.2321475 | 0.32108 |
| position_10 | 1.00000 | 1.00000 | 0.2954536 | 0.29545 |
| reorganized | 1.00000 | 1.00000 | -0.2764789 | -0.27648 |
| pooled_MLB_pa | 1368.40000 | 2.28067 | -0.1080279 | -0.24638 |
| prior_debut | 1.00000 | 1.00000 | 0.2261881 | 0.22619 |
| quality_present_1 | 1.00000 | 1.00000 | 0.1866282 | 0.18663 |
| work_1 | 496.00000 | 496.00000 | 0.0002950 | 0.14631 |

Largest affected false high. 635 PA/35 HR and two preceding strong seasons support an elite forecast. PA falls 601→585 and value 5.65→5.44 versus 199 PA/0.93 actual. A smaller loss is not evidence that the model identified a future absence. Soto, Ohtani and Guerrero remained productive; lowering every elite forecast would be an unjustified response to this case.

Origin-selected peers: Juan Soto, age 25, origin MLB 713 PA, draft pick None: next 715 PA/6.406 wins; Shohei Ohtani, age 29, origin MLB 731 PA, draft pick None: next 727 PA/7.877 wins; Vladimir Guerrero Jr., age 25, origin MLB 697 PA, draft pick None: next 680 PA/4.973 wins.

## Rhys Hoskins: 2024 to 2025

Selection: Ordinary affected.

Age 31; observed MLB PA current/prior/older 517/0/672; pooled MLB quality 0.37016; soft captured listing 1; known draft 1, pick 142. No new focal-player input is introduced.

| Source year | League | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 672 | 30 | 169 | 72 |
| 2024 | MLB | 517 | 26 | 149 | 52 |

| Forecast | PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| safe_ridge | 391.564 | 0.16920 | 1.33373 |
| cohort | 378.424 | 0.24123 | 1.33440 |
| Actual | 328 | 0.56988 | 1.33359 |

Value arithmetic: new PA × (new conditional batting rate/600 + origin replacement 0.0031242). This product is not a joint uncertainty distribution.

Fold 4; 4119 distinct origin-2020 training people. Rate fit maximum target year 2024; saved fit hash 6a9e70e9372d207ad5cfbcfe340437fb76d060af8f5ee5a2d0be4f9691f77049.

Profile support: all=222 distinct training people; active=173 distinct training people.

Saved linear intercept: -0.9026603250060004. Largest actual scaled terms:

| Feature | Raw | Fixed scaled | Coefficient | Contribution |
|---|---:|---:|---:|---:|
| work_0 | 517.21284 | 517.21284 | 0.0013921 | 0.72004 |
| work_2 | 672.00000 | 672.00000 | 0.0009242 | 0.62106 |
| age_centered | 0.80000 | 0.80000 | -0.5701635 | -0.45613 |
| pooled_mlb_quality | 0.37016 | 0.37016 | 0.7628004 | 0.28236 |
| reorganized | 1.00000 | 1.00000 | -0.2127066 | -0.21271 |
| pooled_MLB_pa | 920.20000 | 1.53367 | -0.1100287 | -0.16875 |
| position_3 | 1.00000 | 1.00000 | 0.1407578 | 0.14076 |
| quality_2 | 0.63759 | 0.63759 | 0.1937144 | 0.12351 |
| prior_debut | 1.00000 | 1.00000 | 0.1201801 | 0.12018 |
| MLB_0_pa | 517.00000 | 0.86167 | -0.1068716 | -0.09209 |
| draft_class_unknown | 1.00000 | 1.00000 | -0.0832305 | -0.08323 |
| regular_window_scaled | 0.66667 | 0.66667 | -0.1102581 | -0.07351 |

Ordinary affected example. A completed 517-PA/26-HR return season follows a missed season and an older 672-PA/30-HR year. PA falls 392→378 toward actual 328, but the rate rises and expected value remains almost exactly 1.33, matching actual 1.33. The agreement partly reflects offsetting head changes, not unique proof of the rate/workload decomposition. O'Hearn and McNeil played regularly; Winker barely played.

Origin-selected peers: Ryan O'Hearn, age 30, origin MLB 494 PA, draft pick 243: next 544 PA/3.319 wins; Jeff McNeil, age 32, origin MLB 472 PA, draft pick 356: next 462 PA/1.773 wins; Jesse Winker, age 30, origin MLB 508 PA, draft pick 49: next 81 PA/0.159 wins.

## Disposition

Keep the reconstructed source population and cancellation/missingness handling. Do not claim an established predictive gain or replace the working forecast: overall and public workload error slightly worsen, contribution differences are uncertain, and cohort/entry/absence problems remain. Use this repaired-source assembly as the fixed control for subsequent research while keeping V33b visible. No frozen forecast, protected 2026 outcomes or deployed explorer changes.

Next: one exposure/reliability representation test, rather than another algorithm tournament. In particular, a long upper-minor record and tiny MLB debut must coexist without assuming either source is infallible.
