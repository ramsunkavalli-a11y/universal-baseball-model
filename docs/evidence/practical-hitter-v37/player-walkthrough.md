# Empirical MLB anchor and learned event adjustment review

Same V36 144 features/likelihood/settings and fixed V34 workload. The only model repair is a direct own-MLB-count offset, with mature-target league transport during training. All earlier predictions remain byte-exact. No protected 2026 outcomes or frozen changes.

Eleven fixed diagnostics plus largest value gain/harm, false high/low and ordinary example. Peers use only origin-known stage/debut/age/exposure/quality/draft/college inputs, not future outcomes.

## Jeff McNeil: 2018 to 2019

Selection: Predeclared diagnostic.

Age 26; draft 356/unknown; actual weighted MLB exposure 248.000, anchor reliability 0.71264. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 14 | 1 | 1 | 2 |
| 2017 | AAA | 78 | 1 | 10 | 3 |
| 2017 | Aplus | 116 | 3 | 19 | 6 |
| 2018 | AA | 241 | 14 | 23 | 21 |
| 2018 | AAA | 143 | 5 | 19 | 13 |
| 2018 | MLB | 248 | 3 | 24 | 13 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465785 | 0.513157 | 0.542647 | 0.00000 | 0.540164 | 276 | 0.00000 |
| K | 0.222573 | 0.132923 | 0.139781 | -0.13673 | 0.122039 | 75 | -0.00000 |
| UBB | 0.079708 | 0.060261 | 0.059184 | -0.10050 | 0.057367 | 33 | -0.77819 |
| HBP | 0.010381 | 0.017351 | 0.010960 | 0.01613 | 0.018561 | 21 | 0.29710 |
| 1B | 0.142174 | 0.196027 | 0.179187 | -0.10691 | 0.185421 | 100 | 1.90881 |
| 2B | 0.044637 | 0.044436 | 0.046109 | -0.09018 | 0.042741 | 38 | -0.11777 |
| 3B | 0.004575 | 0.018556 | 0.006906 | -0.03127 | 0.018931 | 1 | 1.12434 |
| HR | 0.030167 | 0.017289 | 0.015228 | -0.20840 | 0.014776 | 23 | -1.53961 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 399.170 | -0.22474 | 1.07943 |
| event | 399.170 | -0.28066 | 1.04223 |
| anchor_only | 399.170 | 1.74699 | 2.39120 |
| anchored | 399.170 | 0.89470 | 1.82418 |
| Actual | 567 | 3.35684 | 4.90426 |

Product = fixed PA × (rate/600 + origin replacement 0.0030788). Actual trained distinct active people 1019; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 160, 'objective': 1.4541001916526621, 'maximum_gradient': 9.535185373393867e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.28761, 0.04693, -0.00955, -0.01071, -0.04197, 0.09443, 0.07776 |
| pooled_AA_K | -0.96629 | -0.14968, -0.06282, -0.02807, -0.01343, -0.03728, -0.00913, -0.13159 |
| prior_debut | 1.00000 | -0.10007, 0.00353, 0.03231, -0.02372, 0.02057, -0.05193, 0.02136 |
| pooled_AAA_K | -0.66280 | -0.09904, -0.01565, 0.00996, -0.00986, -0.02677, -0.02917, -0.05400 |
| pooled_MLB_K | -0.94943 | 0.08024, -0.02191, -0.00403, -0.01898, 0.01418, 0.00401, 0.00555 |
| pooled_MLB_BABIP | 0.38926 | -0.02728, -0.01375, 0.00040, -0.07462, -0.04922, -0.01990, -0.01223 |
| draft_class_unknown | 1.00000 | -0.03695, -0.02591, 0.00959, 0.00537, -0.01836, -0.01146, -0.06171 |
| on_40man | 1.00000 | -0.05997, -0.03661, 0.00854, -0.00155, -0.01138, -0.03345, -0.03446 |
| position_4 | 1.00000 | -0.02101, 0.00186, -0.01832, 0.01878, -0.00886, -0.00031, -0.04339 |
| pooled_MLB_BB | -0.19655 | -0.00290, 0.03724, -0.00320, 0.00232, 0.00243, 0.00001, 0.00292 |
| draft_known | 1.00000 | 0.01053, 0.03264, 0.03194, -0.01021, 0.01171, 0.03712, -0.00210 |
| pooled_MLB_pa | 0.41333 | -0.02709, 0.00819, -0.00884, 0.00207, 0.00562, -0.03092, 0.00362 |

The 248-PA low-K debut creates an anchor rate +1.747, and learned odds shrink it to +0.895 versus old −0.225. Low K/singles now retain meaningful talent, though a high triples estimate contributes substantially and forecast HR remains only 1.48% despite upper-minor power. Fixed 399 PA versus actual 567 still misses workload; value improves 1.08→1.82 but remains below 4.90. Mullins/O'Brien fail while Lowe succeeds, preventing a guaranteed-breakout interpretation.

Origin-selected peers: Cedric Mullins (age 23, MLB/AAA/AA PA 191/269.0/218.0; actual next 74 PA/-0.798 wins); Brandon Lowe (age 23, MLB/AAA/AA PA 148/205.0/240.0; actual next 327 PA/2.038 wins); Peter O'Brien (age 27, MLB/AAA/AA PA 74/135.0/286.0; actual next 47 PA/-0.191 wins).

Profile support: all=354 distinct people; active=279 distinct people.

## Spencer Steer: 2022 to 2023

Selection: Predeclared diagnostic.

Age 24; draft 90/unknown; actual weighted MLB exposure 108.000, anchor reliability 0.51923. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.460423 | 0.448227 | 0.00000 | 0.455421 | 289 | -0.00000 |
| K | 0.224178 | 0.232778 | 0.247988 | 0.03433 | 0.238290 | 139 | 0.00000 |
| UBB | 0.078977 | 0.090855 | 0.091838 | 0.04130 | 0.093656 | 68 | 0.51131 |
| HBP | 0.011239 | 0.015019 | 0.012507 | 0.08456 | 0.016166 | 11 | 0.17898 |
| 1B | 0.142135 | 0.130834 | 0.121201 | -0.03284 | 0.125232 | 95 | -0.74606 |
| 2B | 0.043614 | 0.045007 | 0.043796 | 0.00745 | 0.044851 | 37 | 0.07684 |
| 3B | 0.003532 | 0.001698 | 0.003645 | -0.00206 | 0.001676 | 3 | -0.14534 |
| HR | 0.028646 | 0.023387 | 0.030799 | 0.06585 | 0.024708 | 23 | -0.39391 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 180.375 | -0.23663 | 0.49361 |
| event | 180.375 | -0.19438 | 0.50631 |
| anchor_only | 180.375 | -0.53089 | 0.40515 |
| anchored | 180.375 | -0.51817 | 0.40897 |
| Actual | 665 | 1.90921 | 4.17493 |

Product = fixed PA × (rate/600 + origin replacement 0.0031310). Actual trained distinct active people 1387; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 151, 'objective': 1.4616409352485717, 'maximum_gradient': 8.031819144678291e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.25316, 0.00371, 0.01967, 0.01306, -0.01033, 0.07736, 0.02072 |
| prior_debut | 1.00000 | -0.07898, -0.00134, 0.01013, -0.00597, -0.01520, -0.05371, 0.02649 |
| pooled_Aplus_BB | 0.55135 | 0.00088, 0.06065, -0.00794, -0.00481, 0.00634, 0.00237, 0.00168 |
| age_centered | -0.60000 | -0.00822, 0.01238, -0.00770, 0.00880, 0.02664, 0.02246, 0.05670 |
| pooled_Aplus_K | -0.47568 | -0.05299, -0.01716, -0.00721, 0.00670, -0.00754, 0.00648, -0.03640 |
| on_40man | 1.00000 | -0.04494, -0.02497, -0.00179, -0.00114, -0.00866, -0.04118, -0.04503 |
| pooled_AAA_K | -0.25872 | -0.04452, -0.00907, -0.00197, -0.00203, -0.01228, -0.00613, -0.02215 |
| position_5 | 1.00000 | 0.01000, 0.01155, 0.02587, -0.00760, -0.00158, -0.02508, 0.04335 |
| draft_known | 1.00000 | 0.00300, 0.02847, 0.04146, -0.01028, -0.00573, 0.02057, 0.00019 |
| draft_class_unknown | 1.00000 | -0.03013, -0.01731, 0.00639, -0.00093, -0.01251, -0.00942, -0.03799 |
| pooled_AA_pa | 0.63333 | 0.03224, -0.02115, 0.00141, -0.01652, 0.00538, 0.01092, -0.00859 |
| pooled_AAA_BB | 0.20917 | 0.00401, 0.03119, -0.00229, -0.00465, 0.00241, -0.00314, 0.01057 |

The 108-PA debut anchor is −0.531 and adjustments barely alter it to −0.518, despite 492 current upper-minor PA/23 HR. This is worse than old −0.237; fixed 180 PA still misses actual 665. Learned upper-minor information does not materially overcome the poor brief MLB record. Brennan/Freeman/Henderson have varied later roles; this supports a reliability/translation gap rather than a promise for every advancing player.

Origin-selected peers: Will Brennan (age 24, MLB/AAA/AA PA 45/433.0/157.0; actual next 455 PA/0.166 wins); Tyler Freeman (age 23, MLB/AAA/AA PA 86/343.0/0.0; actual next 168 PA/0.094 wins); Gunnar Henderson (age 21, MLB/AAA/AA PA 132/295.0/208.0; actual next 622 PA/3.402 wins).

Profile support: all=336 distinct people; active=298 distinct people.

## Masyn Winn: 2023 to 2024

Selection: Predeclared diagnostic.

Age 21; draft 54/HS SR; actual weighted MLB exposure 137.000, anchor reliability 0.57806. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.456074 | 0.529989 | 0.472905 | 0.00000 | 0.506987 | 330 | 0.00000 |
| K | 0.227279 | 0.205603 | 0.226362 | 0.09668 | 0.216644 | 109 | -0.00000 |
| UBB | 0.083350 | 0.077363 | 0.081854 | 0.07145 | 0.079487 | 40 | -0.13456 |
| HBP | 0.011472 | 0.004840 | 0.009089 | -0.00542 | 0.004605 | 1 | -0.24940 |
| 1B | 0.141393 | 0.131389 | 0.132626 | 0.08877 | 0.137355 | 105 | -0.17822 |
| 2B | 0.044692 | 0.027296 | 0.042720 | 0.14776 | 0.030269 | 32 | -0.89597 |
| 3B | 0.003867 | 0.001632 | 0.005505 | 0.13073 | 0.001779 | 5 | -0.16356 |
| HR | 0.031873 | 0.021887 | 0.028938 | 0.08846 | 0.022874 | 15 | -0.90024 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 305.512 | -0.79671 | 0.54021 |
| event | 305.512 | -0.81343 | 0.53170 |
| anchor_only | 305.512 | -3.14561 | -0.65581 |
| anchored | 305.512 | -2.52195 | -0.33826 |
| Actual | 637 | 0.25454 | 2.25951 |

Product = fixed PA × (rate/600 + origin replacement 0.0030961). Actual trained distinct active people 1470; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 151, 'objective': 1.4641255406347977, 'maximum_gradient': 8.904760494273476e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24608, -0.00311, 0.03872, 0.01610, -0.00860, 0.05268, -0.01253 |
| age_centered | -1.20000 | -0.02081, 0.02044, -0.00346, 0.01900, 0.05113, 0.05048, 0.11169 |
| pooled_MLB_BABIP | -0.51269 | 0.03466, 0.02180, -0.00600, 0.10841, 0.06278, 0.01351, 0.02030 |
| pooled_AAA_K | -0.52742 | -0.08889, -0.01675, -0.00436, -0.00245, -0.02179, -0.01344, -0.04682 |
| prior_debut | 1.00000 | -0.08489, -0.00553, 0.00531, -0.01165, -0.01470, -0.05018, 0.04170 |
| pooled_MLB_2B | -0.20464 | -0.00384, -0.00806, -0.00314, -0.02773, 0.05868, 0.00064, -0.00921 |
| pooled_AA_BB | 0.33636 | -0.00634, 0.05656, 0.00120, -0.01339, 0.00025, -0.00185, 0.00575 |
| position_6 | 1.00000 | -0.01881, -0.04265, -0.02740, 0.00317, 0.00150, 0.01970, -0.04636 |
| on_40man | 1.00000 | -0.04061, -0.02050, -0.00806, 0.00337, -0.00999, -0.03501, -0.03662 |
| pooled_AA_pa | 0.53733 | 0.03212, -0.01549, 0.00164, -0.01075, 0.00106, 0.00858, -0.00412 |
| pooled_AAA_pa | 0.83000 | 0.01516, 0.00737, 0.00453, -0.00496, 0.02130, 0.00210, 0.03061 |
| draft_known | 1.00000 | 0.00202, 0.02967, 0.03042, -0.01150, -0.00476, 0.02059, -0.00450 |

A 137-PA debut receives anchor reliability about 58%, yielding −3.146 batting wins/600. Adjustments recover only to −2.522 versus old −0.797 and actual +0.254, while the much longer strong AAA season is present. Singles, doubles and power all remain suppressed. This is a substantive brief-debut reliability failure of the fixed 100-prior anchor, not a missing AAA source. Meadows/Edwards/Soderstrom differ in subsequent playing time and success.

Origin-selected peers: Parker Meadows (age 23, MLB/AAA/AA PA 145/517.0/0.0; actual next 298 PA/1.211 wins); Xavier Edwards (age 23, MLB/AAA/AA PA 84/433.0/0.0; actual next 303 PA/2.187 wins); Tyler Soderstrom (age 21, MLB/AAA/AA PA 138/335.0/0.0; actual next 213 PA/0.873 wins).

Profile support: all=384 distinct people; active=342 distinct people.

## Nick Kurtz: 2024 to 2025

Selection: Predeclared diagnostic.

Age 21; draft 4/4YR JR; actual weighted MLB exposure 0.000, anchor reliability 0.00000. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.465823 | 0.432224 | 0.00000 | 0.440583 | 154 | -0.00000 |
| K | 0.225800 | 0.225800 | 0.261919 | 0.17517 | 0.254451 | 151 | 0.00000 |
| UBB | 0.079036 | 0.079036 | 0.082601 | 0.07593 | 0.080650 | 60 | 0.05623 |
| HBP | 0.011072 | 0.011072 | 0.010142 | 0.00806 | 0.010556 | 2 | -0.01871 |
| 1B | 0.141968 | 0.141968 | 0.131564 | 0.00670 | 0.135178 | 58 | -0.29970 |
| 2B | 0.042593 | 0.042593 | 0.042540 | 0.02602 | 0.041347 | 26 | -0.07740 |
| 3B | 0.003820 | 0.003820 | 0.004186 | 0.17106 | 0.004287 | 2 | 0.03658 |
| HR | 0.029888 | 0.029888 | 0.034824 | 0.15316 | 0.032947 | 36 | 0.30603 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 42.495 | -0.13556 | 0.12316 |
| event | 42.495 | 0.15034 | 0.14341 |
| anchor_only | 42.495 | 0.00000 | 0.13276 |
| anchored | 42.495 | 0.00303 | 0.13297 |
| Actual | 489 | 5.15001 | 5.72099 |

Product = fixed PA × (rate/600 + origin replacement 0.0031242). Actual trained distinct active people 1545; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 148, 'objective': 1.464766294457457, 'maximum_gradient': 9.981703906322063e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24613, 0.01124, 0.03792, 0.01881, -0.03335, 0.07406, -0.02793 |
| age_centered | -1.20000 | -0.02201, 0.00360, -0.00375, 0.01571, 0.05227, 0.05761, 0.11237 |
| draft_college | 1.00000 | -0.03107, -0.00430, 0.00016, -0.00088, 0.00735, 0.00613, 0.00904 |
| draft_known | 1.00000 | 0.02159, 0.02926, 0.02241, -0.01891, -0.01235, 0.02133, 0.00105 |
| draft_rank | 0.81761 | -0.02753, -0.00207, -0.00718, 0.00435, 0.00914, -0.00117, 0.02224 |
| age_squared | 1.44000 | -0.02321, -0.01143, -0.02748, -0.01986, 0.00228, 0.01901, 0.01521 |
| pooled_A_BB | 0.53333 | -0.00643, 0.02689, 0.00026, -0.00248, -0.00342, 0.00211, 0.00647 |
| position_3 | 1.00000 | 0.01604, 0.01045, -0.01070, 0.00289, 0.00496, -0.01747, 0.02111 |
| pooled_AA_BB | 0.06957 | -0.00086, 0.01156, -0.00113, -0.00200, 0.00094, -0.00015, 0.00123 |
| pooled_A_HR | 0.21852 | 0.00761, 0.00295, 0.00024, -0.00593, -0.00049, -0.00133, 0.00467 |
| pooled_A_BABIP | 0.15789 | 0.00204, -0.00061, -0.00253, 0.00723, -0.00151, 0.00455, 0.00168 |
| pooled_AA_K | -0.03913 | -0.00611, -0.00247, -0.00062, -0.00054, -0.00126, -0.00095, -0.00402 |

No MLB observations means exactly the league anchor, not invented MLB skill. Draft pick 4/college plus 50 minor PA let learned odds produce rate +0.003, but fixed 42 PA leaves value around 0.13 versus 489/5.72. The exceptional arrival remains missed. College peers Moore/Smith/Davis show two advances and one non-arrival; a league fallback is a mathematical starting point, not proof all prospects have identical ability.

Origin-selected peers: Christian Moore (age 21, MLB/AAA/AA PA 0/0.0/98.0; actual next 184 PA/0.198 wins); Cam Smith (age 21, MLB/AAA/AA PA 0/0.0/20.0; actual next 493 PA/1.014 wins); Chase Davis (age 22, MLB/AAA/AA PA 0/0.0/31.0; actual next 0 PA/0.000 wins).

Profile support: all=11 distinct people; active=0 distinct people.

## Aaron Judge: 2016 to 2017

Selection: Predeclared diagnostic; false low.

Age 24; draft 32/unknown; actual weighted MLB exposure 95.000, anchor reliability 0.48718. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.474130 | 0.386734 | 0.327511 | 0.00000 | 0.351517 | 195 | -0.00000 |
| K | 0.211193 | 0.323689 | 0.380755 | 0.18149 | 0.352763 | 208 | 0.00000 |
| UBB | 0.076693 | 0.085484 | 0.094409 | 0.22407 | 0.097215 | 116 | 0.71483 |
| HBP | 0.008945 | 0.009715 | 0.008693 | 0.06353 | 0.009410 | 5 | 0.01689 |
| 1B | 0.149198 | 0.122666 | 0.106240 | 0.06090 | 0.118497 | 75 | -1.35509 |
| 2B | 0.044718 | 0.033189 | 0.037943 | 0.08368 | 0.032799 | 24 | -0.74039 |
| 3B | 0.004730 | 0.002425 | 0.004206 | 0.15176 | 0.002566 | 3 | -0.16946 |
| HR | 0.030393 | 0.036099 | 0.040242 | 0.07120 | 0.035233 | 52 | 0.48414 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 143.966 | -0.05720 | 0.43085 |
| event | 143.966 | -0.76474 | 0.26109 |
| anchor_only | 143.966 | -1.16279 | 0.16558 |
| anchored | 143.966 | -1.04907 | 0.19286 |
| Actual | 678 | 5.32988 | 8.10841 |

Product = fixed PA × (rate/600 + origin replacement 0.0030881). Actual trained distinct active people 856; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 160, 'objective': 1.4442498619377562, 'maximum_gradient': 8.093029688896563e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.28218, 0.06645, 0.00062, -0.02713, -0.02948, 0.07871, 0.06814 |
| prior_debut | 1.00000 | -0.10033, 0.00512, 0.03120, -0.02296, 0.00594, -0.04716, 0.01562 |
| pooled_Aplus_BB | 0.58007 | 0.01430, 0.09296, -0.01256, -0.00058, 0.01440, 0.00444, 0.00628 |
| pooled_MLB_K | 1.03333 | -0.06808, 0.02570, 0.01293, 0.01208, -0.00888, -0.00412, 0.00611 |
| age_centered | -0.60000 | -0.00108, 0.00249, -0.00448, 0.01991, 0.02874, 0.00845, 0.06293 |
| draft_known | 1.00000 | 0.00926, 0.01707, 0.01535, -0.00731, 0.00740, 0.06200, -0.00460 |
| draft_class_unknown | 1.00000 | -0.03212, -0.03240, 0.00049, 0.00317, -0.02557, -0.01197, -0.05752 |
| on_40man | 1.00000 | -0.05208, -0.03234, 0.02393, -0.00834, -0.01685, -0.02868, -0.05584 |
| pooled_AAA_pa | 1.03000 | 0.02602, -0.00985, 0.02128, 0.00745, 0.01833, -0.04450, 0.01185 |
| pooled_AAA_BB | 0.28914 | 0.00496, 0.04260, -0.00484, 0.00074, -0.00591, -0.00124, 0.00715 |
| pooled_MLB_2B | -0.14103 | -0.00023, -0.00397, -0.00118, -0.01780, 0.03861, 0.00092, -0.00602 |
| position_9 | 1.00000 | -0.00326, 0.00153, 0.00031, 0.02624, 0.01053, 0.03727, -0.00319 |

The 95-PA debut gets almost 49% anchor reliability and retains very high K/low singles despite a strong 410-PA AAA year. Rate −1.163 adjusts only to −1.049, worse than old −0.057 and naked −0.765, versus later +5.330. With fixed 144 PA the false low worsens. The empirical anchor fixes established production but is too influential for this brief-debut profile. Marrero/Decker/Cowart have weak later outcomes; a future MVP is not guaranteed, but the representation is still demonstrably unhelpful here.

Origin-selected peers: Deven Marrero (age 25, MLB/AAA/AA PA 14/388.0/0.0; actual next 188 PA/-0.447 wins); Jaff Decker (age 26, MLB/AAA/AA PA 57/417.0/0.0; actual next 62 PA/-0.115 wins); Kaleb Cowart (age 24, MLB/AAA/AA PA 87/458.0/0.0; actual next 117 PA/0.123 wins).

Profile support: all=186 distinct people; active=159 distinct people.

## Aaron Judge: 2024 to 2025

Selection: Predeclared diagnostic.

Age 32; draft 32/unknown; actual weighted MLB exposure 1488.000, anchor reliability 0.93703. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.343818 | 0.395760 | 0.00000 | 0.361670 | 245 | -0.00000 |
| K | 0.225800 | 0.253514 | 0.257366 | -0.02762 | 0.259413 | 160 | 0.00000 |
| UBB | 0.079036 | 0.150695 | 0.135478 | -0.10201 | 0.143147 | 88 | 2.23320 |
| HBP | 0.011072 | 0.008632 | 0.011031 | -0.02282 | 0.008875 | 7 | -0.07978 |
| 1B | 0.141968 | 0.118008 | 0.117461 | -0.07499 | 0.115167 | 94 | -1.18294 |
| 2B | 0.042593 | 0.043992 | 0.040317 | -0.09585 | 0.042046 | 30 | -0.03394 |
| 3B | 0.003820 | 0.000870 | 0.003303 | -0.15534 | 0.000784 | 2 | -0.23781 |
| HR | 0.029888 | 0.080472 | 0.039284 | -0.20590 | 0.068898 | 53 | 3.90233 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 548.496 | 4.55334 | 5.87607 |
| event | 548.496 | 1.64096 | 3.21369 |
| anchor_only | 548.496 | 6.26591 | 7.44163 |
| anchored | 548.496 | 4.60106 | 5.91969 |
| Actual | 679 | 6.28743 | 9.23105 |

Product = fixed PA × (rate/600 + origin replacement 0.0031242). Actual trained distinct active people 1554; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 149, 'objective': 1.4643731564795273, 'maximum_gradient': 6.234861274548637e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.22761, -0.01057, 0.02269, 0.01395, -0.03133, 0.05987, -0.03269 |
| pooled_MLB_pa | 2.48000 | -0.14802, 0.08663, -0.04756, -0.00919, 0.04870, -0.16130, 0.04891 |
| pooled_MLB_BB | 0.70756 | 0.01425, -0.13301, 0.01291, -0.00152, -0.00809, -0.00319, -0.00514 |
| pooled_MLB_HR | 0.50479 | 0.02402, 0.03511, 0.00074, -0.00180, -0.00682, -0.00748, -0.09934 |
| age_centered | 1.00000 | 0.01140, -0.01273, 0.01409, -0.01521, -0.04838, -0.03285, -0.09883 |
| prior_debut | 1.00000 | -0.08696, -0.00589, 0.00746, -0.01597, 0.00101, -0.04795, 0.03739 |
| pooled_MLB_BABIP | 0.38435 | -0.02787, -0.02171, -0.00298, -0.07728, -0.04857, -0.01567, -0.01806 |
| position_8 | 1.00000 | 0.01126, -0.00530, 0.00576, 0.02296, -0.00414, 0.05160, -0.01431 |
| on_40man | 1.00000 | -0.04837, -0.02197, -0.01354, -0.00038, -0.02010, -0.02329, -0.02518 |
| draft_known | 1.00000 | 0.02274, 0.03505, 0.01965, -0.01799, -0.00612, 0.02948, 0.00030 |
| age_squared | 1.00000 | -0.00684, 0.00639, -0.02179, -0.00997, -0.00230, 0.03363, 0.01571 |
| draft_elapsed | 1.00000 | -0.00271, -0.03324, -0.02545, 0.01921, 0.00120, 0.00743, -0.03094 |

The established 1,488 weighted MLB PA correctly retain an 8.05% HR anchor. Learned odds lower it to 6.89%, rather than V36's implausible 3.93%; final rate +4.601 is close to old +4.553 and much better than naked +1.641. This repairs the intended power representation but does not beat the working assembly materially. Fixed 548 PA remains low against actual 679, while value 5.92 remains below 9.23. Freeman/Betts/Olson are productive contrasts, not guaranteed repeat MVPs.

Origin-selected peers: Freddie Freeman (age 34, MLB/AAA/AA PA 638/0.0/0.0; actual next 627 PA/4.784 wins); Mookie Betts (age 31, MLB/AAA/AA PA 516/0.0/0.0; actual next 663 PA/2.398 wins); Matt Olson (age 30, MLB/AAA/AA PA 685/0.0/0.0; actual next 724 PA/5.517 wins).

Profile support: all=224 distinct people; active=170 distinct people.

## Matt Olson: 2022 to 2023

Selection: Predeclared diagnostic.

Age 28; draft 47/unknown; actual weighted MLB exposure 1384.400, anchor reliability 0.93263. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 245 | 14 | 77 | 32 |
| 2021 | MLB | 673 | 39 | 113 | 76 |
| 2022 | MLB | 699 | 34 | 170 | 69 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.450531 | 0.438465 | 0.00000 | 0.442551 | 281 | -0.00000 |
| K | 0.224178 | 0.221650 | 0.230950 | 0.02777 | 0.223855 | 167 | -0.00000 |
| UBB | 0.078977 | 0.105698 | 0.106395 | 0.03991 | 0.108053 | 96 | 1.01281 |
| HBP | 0.011239 | 0.008706 | 0.010468 | -0.00673 | 0.008495 | 4 | -0.09965 |
| 1B | 0.142135 | 0.108201 | 0.120651 | 0.07952 | 0.115081 | 88 | -1.19408 |
| 2B | 0.043614 | 0.053059 | 0.045417 | -0.00760 | 0.051725 | 27 | 0.50388 |
| 3B | 0.003532 | 0.000642 | 0.002636 | -0.20624 | 0.000513 | 3 | -0.23642 |
| HR | 0.028646 | 0.051512 | 0.045017 | -0.01742 | 0.049726 | 54 | 2.10876 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 572.650 | 1.85799 | 3.56624 |
| event | 572.650 | 1.65831 | 3.37567 |
| anchor_only | 572.650 | 1.98888 | 3.69117 |
| anchored | 572.650 | 2.09529 | 3.79273 |
| Actual | 720 | 4.57082 | 7.71416 |

Product = fixed PA × (rate/600 + origin replacement 0.0031310). Actual trained distinct active people 1390; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 151, 'objective': 1.4621479296895852, 'maximum_gradient': 9.91037504060978e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.20334, 0.00775, 0.01108, 0.03551, -0.01992, 0.10299, 0.02169 |
| pooled_MLB_pa | 2.30733 | -0.13607, 0.05692, -0.04531, -0.00616, 0.02939, -0.17100, 0.01446 |
| prior_debut | 1.00000 | -0.06024, -0.00845, 0.01591, -0.02740, 0.00468, -0.05729, 0.03385 |
| pooled_MLB_BABIP | -0.28686 | 0.02713, 0.01627, 0.00093, 0.05323, 0.03453, 0.01442, 0.01332 |
| pooled_MLB_BB | 0.25767 | 0.00429, -0.05021, 0.00268, -0.00171, -0.00741, -0.00135, -0.00640 |
| on_40man | 1.00000 | -0.04048, -0.02162, -0.00880, -0.00784, -0.01153, -0.04429, -0.02120 |
| pooled_MLB_HR | 0.21603 | 0.00757, 0.01522, 0.00077, -0.00170, -0.00049, -0.00403, -0.04260 |
| draft_known | 1.00000 | 0.02115, 0.03061, 0.03706, -0.01214, -0.01007, 0.01724, -0.00561 |
| draft_elapsed | 1.00000 | -0.01283, -0.02596, -0.00888, 0.03552, 0.00156, 0.00119, -0.02608 |
| draft_class_unknown | 1.00000 | -0.02666, -0.01199, 0.00149, -0.00058, -0.01084, -0.01624, -0.03329 |
| position_3 | 1.00000 | 0.01753, 0.02423, -0.01978, 0.00014, -0.00559, -0.02365, 0.02256 |
| age_centered | 0.20000 | 0.00067, -0.00307, 0.00307, -0.00327, -0.00865, -0.00686, -0.02035 |

1,384 weighted MLB PA give 5.15% HR anchor and +1.989 rate. Adjustments yield 4.97% HR/+2.095 rate, improving old +1.858 and naked +1.658. Value rises 3.57→3.79 toward actual 7.71, with fixed PA 573 versus 720 actual. Both workload conservatism and later breakout remain. Alonso/Reynolds/Bell play regularly but do not reproduce the exact breakout.

Origin-selected peers: Pete Alonso (age 27, MLB/AAA/AA PA 685/0.0/0.0; actual next 658 PA/3.452 wins); Bryan Reynolds (age 27, MLB/AAA/AA PA 614/0.0/0.0; actual next 640 PA/3.040 wins); Josh Bell (age 29, MLB/AAA/AA PA 647/0.0/0.0; actual next 617 PA/2.116 wins).

Profile support: all=569 distinct people; active=455 distinct people.

## Gavin Lux: 2023 to 2024

Selection: Predeclared diagnostic.

Age 25; draft 20/unknown; actual weighted MLB exposure 605.400, anchor reliability 0.85824. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 74 | 1 | 15 | 6 |
| 2021 | MLB | 381 | 7 | 83 | 38 |
| 2022 | MLB | 471 | 6 | 95 | 47 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.456074 | 0.455922 | 0.451506 | 0.00000 | 0.461452 | 221 | 0.00000 |
| K | 0.227279 | 0.210558 | 0.220958 | -0.00037 | 0.213033 | 110 | -0.00000 |
| UBB | 0.083350 | 0.097441 | 0.093598 | -0.02737 | 0.095961 | 44 | 0.43928 |
| HBP | 0.011472 | 0.004178 | 0.011680 | 0.01628 | 0.004298 | 2 | -0.26056 |
| 1B | 0.141393 | 0.163509 | 0.147139 | -0.05144 | 0.157194 | 74 | 0.69744 |
| 2B | 0.044692 | 0.039225 | 0.044224 | -0.01570 | 0.039082 | 24 | -0.34851 |
| 3B | 0.003867 | 0.011889 | 0.004600 | -0.06192 | 0.011311 | 2 | 0.58296 |
| HR | 0.031873 | 0.017277 | 0.026296 | 0.01037 | 0.017669 | 10 | -1.42091 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 215.427 | -0.23943 | 0.58101 |
| event | 215.427 | 0.08852 | 0.69876 |
| anchor_only | 215.427 | 0.03059 | 0.67796 |
| anchored | 215.427 | -0.31030 | 0.55557 |
| Actual | 487 | 0.08394 | 1.58897 |

Product = fixed PA × (rate/600 + origin replacement 0.0030961). Actual trained distinct active people 1468; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 152, 'objective': 1.464466346404626, 'maximum_gradient': 7.637406715136084e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24313, 0.01168, 0.03876, 0.01126, -0.03225, 0.05875, -0.00296 |
| prior_debut | 1.00000 | -0.08101, -0.00479, 0.01048, -0.01994, 0.00169, -0.05312, 0.03751 |
| pooled_MLB_pa | 1.00900 | -0.06681, 0.03039, -0.02237, -0.00483, 0.02168, -0.06314, 0.01333 |
| on_40man | 1.00000 | -0.04986, -0.02541, -0.01067, -0.00150, -0.02180, -0.03152, -0.03202 |
| position_4 | 1.00000 | -0.01959, 0.00365, -0.02162, 0.00999, -0.01095, 0.01379, -0.04294 |
| age_centered | -0.40000 | -0.00266, 0.00590, -0.00350, 0.00696, 0.01926, 0.01235, 0.04083 |
| pooled_MLB_BABIP | 0.20568 | -0.01519, -0.01317, -0.00088, -0.03932, -0.02408, -0.00801, -0.00846 |
| draft_known | 1.00000 | 0.01919, 0.03331, 0.02280, -0.01534, -0.00411, 0.02198, 0.00014 |
| pooled_MLB_BB | 0.16966 | 0.00278, -0.03121, 0.00294, -0.00061, -0.00313, -0.00119, -0.00168 |
| draft_class_unknown | 1.00000 | -0.02728, -0.02139, 0.00470, 0.00140, -0.01037, -0.00161, -0.02989 |
| pooled_MLB_2B | -0.10023 | -0.00253, -0.00466, -0.00124, -0.01258, 0.02797, 0.00024, -0.00461 |
| pooled_MLB_HR | -0.12988 | -0.00552, -0.00935, -0.00016, 0.00123, 0.00205, 0.00199, 0.02565 |

605 weighted prior MLB PA survive the missed current season. The direct anchor +0.031 is close to actual +0.084, but learned adjustments make it −0.310, worse than old −0.239 and naked +0.089. Positive prior triples are balanced by low HR and HBP. Value slightly deteriorates with unchanged 215 PA versus actual 487. Plummer/Ciuffo/Craig are marginal inactive peers, not equivalent medical returns; the method has not repaired health or job context.

Origin-selected peers: Nick Plummer (age 26, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Nick Ciuffo (age 28, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Will Craig (age 28, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins).

Profile support: all=111 distinct people; active=9 distinct people.

## Matt McLain: 2024 to 2025

Selection: Predeclared diagnostic.

Age 24; draft 17/4YR JR; actual weighted MLB exposure 322.400, anchor reliability 0.76326. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AA | 452 | 17 | 127 | 69 |
| 2023 | AAA | 180 | 12 | 37 | 29 |
| 2023 | MLB | 403 | 16 | 115 | 31 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.383007 | 0.404406 | 0.00000 | 0.381675 | 238 | -0.00000 |
| K | 0.225800 | 0.271259 | 0.287974 | 0.02239 | 0.276438 | 167 | 0.00000 |
| UBB | 0.079036 | 0.077423 | 0.091529 | 0.16627 | 0.091111 | 55 | 0.42060 |
| HBP | 0.011072 | 0.015879 | 0.009734 | 0.00939 | 0.015973 | 5 | 0.17802 |
| 1B | 0.141968 | 0.152928 | 0.130060 | -0.12891 | 0.133964 | 79 | -0.35329 |
| 2B | 0.042593 | 0.053644 | 0.043230 | -0.04031 | 0.051345 | 18 | 0.54373 |
| 3B | 0.003820 | 0.008480 | 0.004548 | 0.03102 | 0.008717 | 0 | 0.38349 |
| HR | 0.029888 | 0.037379 | 0.028519 | 0.09052 | 0.040778 | 15 | 1.08937 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 173.516 | 0.21812 | 0.60517 |
| event | 173.516 | -0.17939 | 0.49021 |
| anchor_only | 173.516 | 2.40300 | 1.23702 |
| anchored | 173.516 | 2.26193 | 1.19623 |
| Actual | 577 | -1.27881 | 0.56815 |

Product = fixed PA × (rate/600 + origin replacement 0.0031242). Actual trained distinct active people 1545; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 148, 'objective': 1.464766294457457, 'maximum_gradient': 9.981703906322063e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24613, 0.01124, 0.03792, 0.01881, -0.03335, 0.07406, -0.02793 |
| prior_debut | 1.00000 | -0.10998, -0.01703, -0.00351, -0.01585, 0.00673, -0.04800, 0.04553 |
| pooled_MLB_BABIP | 0.55153 | -0.04618, -0.02950, -0.00121, -0.10959, -0.06994, -0.02746, -0.03892 |
| pooled_AA_BB | 0.53082 | -0.00657, 0.08824, -0.00859, -0.01524, 0.00716, -0.00111, 0.00939 |
| pooled_AAA_BB | 0.47869 | -0.00205, 0.06958, -0.00369, -0.01073, -0.00337, -0.00008, 0.00647 |
| pooled_AA_K | 0.37241 | 0.05814, 0.02354, 0.00587, 0.00511, 0.01200, 0.00901, 0.03829 |
| age_centered | -0.60000 | -0.01101, 0.00180, -0.00187, 0.00785, 0.02613, 0.02881, 0.05618 |
| position_6 | 1.00000 | -0.02403, -0.04542, -0.01740, 0.00056, -0.00082, -0.00028, -0.03904 |
| pooled_MLB_pa | 0.53733 | -0.02864, 0.01866, -0.00829, -0.00328, 0.01212, -0.03946, 0.00793 |
| draft_college | 1.00000 | -0.03107, -0.00430, 0.00016, -0.00088, 0.00735, 0.00613, 0.00904 |
| pooled_MLB_K | 0.42254 | -0.03080, 0.00981, -0.00821, 0.00286, -0.00665, 0.00030, -0.00187 |
| draft_known | 1.00000 | 0.02159, 0.02926, 0.02241, -0.01891, -0.01235, 0.02133, 0.00105 |

322 weighted MLB PA from the previous strong debut generate +2.403 anchor; residual adjustment retains +2.262 versus old +0.218 and actual −1.279. His later poor performance is uncertain, but the fixed 100-prior anchor is strongly optimistic here. Value rises 0.61→1.20 versus 0.57 with only 174 predicted PA versus actual 577. Product and component errors remain separate; the old close total was partly cancellation. Swaggerty/Walker/Proctor have zero later PA and are not equivalent return-role cases.

Origin-selected peers: Travis Swaggerty (age 26, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Steele Walker (age 27, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins); Ford Proctor (age 27, MLB/AAA/AA PA 0/0.0/0.0; actual next 0 PA/0.000 wins).

Profile support: all=5 distinct people; active=4 distinct people.

## Fernando Tatis Jr.: 2022 to 2023

Selection: Predeclared diagnostic.

Age 23; draft None/unknown; actual weighted MLB exposure 591.000, anchor reliability 0.85528. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |
| 2022 | AA | 14 | 0 | 2 | 4 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.388666 | 0.419758 | 0.00000 | 0.389967 | 290 | -0.00000 |
| K | 0.224178 | 0.262544 | 0.282658 | 0.01827 | 0.268281 | 141 | 0.00000 |
| UBB | 0.078977 | 0.098839 | 0.088456 | -0.02458 | 0.096762 | 53 | 0.61950 |
| HBP | 0.011239 | 0.008283 | 0.009312 | -0.03393 | 0.008034 | 3 | -0.11640 |
| 1B | 0.142135 | 0.120135 | 0.119061 | -0.02486 | 0.117578 | 89 | -1.08389 |
| 2B | 0.043614 | 0.051753 | 0.042237 | -0.03729 | 0.050026 | 33 | 0.39831 |
| 3B | 0.003532 | 0.002248 | 0.003628 | -0.03974 | 0.002167 | 1 | -0.10687 |
| HR | 0.028646 | 0.067532 | 0.034891 | -0.00850 | 0.067185 | 25 | 3.85519 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 147.175 | 1.27950 | 0.77465 |
| event | 147.175 | -0.21153 | 0.40891 |
| anchor_only | 147.175 | 3.90847 | 1.41952 |
| anchored | 147.175 | 3.56585 | 1.33547 |
| Actual | 635 | 0.72681 | 2.73521 |

Product = fixed PA × (rate/600 + origin replacement 0.0031310). Actual trained distinct active people 1394; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 153, 'objective': 1.458662632011743, 'maximum_gradient': 8.708936931078496e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.22914, -0.00555, 0.02136, 0.00710, -0.03789, 0.09596, 0.03046 |
| age_centered | -0.80000 | 0.00239, 0.00457, -0.00779, 0.01080, 0.03627, 0.02752, 0.08152 |
| pooled_MLB_HR | 0.37728 | 0.01273, 0.01326, -0.00010, -0.00008, 0.00047, -0.00570, -0.07413 |
| prior_debut | 1.00000 | -0.07186, 0.00263, 0.01213, -0.01053, -0.00620, -0.06153, 0.01837 |
| pooled_MLB_pa | 0.98500 | -0.06384, 0.01891, -0.01645, -0.00228, 0.01877, -0.07022, 0.01223 |
| position_6 | 1.00000 | -0.02283, -0.04812, -0.03238, -0.00107, -0.00617, -0.00301, -0.04436 |
| pooled_AA_BB | 0.25263 | -0.00028, 0.04642, -0.00364, -0.00830, -0.00147, -0.00098, 0.00438 |
| pooled_MLB_BB | 0.18987 | 0.00634, -0.04197, 0.00262, -0.00182, -0.00153, 0.00012, -0.00313 |
| pooled_MLB_BABIP | 0.14505 | -0.01389, -0.00854, 0.00034, -0.02743, -0.01758, -0.00534, -0.00642 |
| pooled_MLB_K | 0.33386 | -0.02664, 0.00840, -0.00666, 0.00545, -0.00700, 0.00143, -0.00783 |
| draft_class_unknown | 1.00000 | -0.02611, -0.01363, 0.00998, 0.00808, -0.00633, -0.02014, -0.02370 |
| pooled_AA_K | -0.10702 | -0.01878, -0.00460, -0.00209, -0.00060, -0.00199, -0.00136, -0.01136 |

591 weighted MLB PA/strong prior power generate +3.909 anchor and +3.566 after adjustments. The rate is optimistic versus realized +0.727, but fixed 147 PA is far below actual 635; value moves closer 0.77→1.34 versus 2.74 partly by compensating workload with high rate. Retaining talent is more sensible than naked near-zero power, yet this is not jointly accurate or a finite-suspension opportunity repair. Generic inactive peers all fail to return and are poor suspension analogues.

Origin-selected peers: Luis Alexander Basabe (age 25, MLB/AAA/AA PA 0/26.0/0.0; actual next 0 PA/0.000 wins); Sherten Apostel (age 23, MLB/AAA/AA PA 0/77.0/0.0; actual next 0 PA/0.000 wins); Deivy Grullón (age 26, MLB/AAA/AA PA 0/63.0/0.0; actual next 0 PA/0.000 wins).

Profile support: all=25 distinct people; active=14 distinct people.

## Chris Davis: 2017 to 2018

Selection: Predeclared diagnostic.

Age 31; draft 148/unknown; actual weighted MLB exposure 1458.000, anchor reliability 0.93582. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2015 | MLB | 670 | 47 | 208 | 78 |
| 2016 | MLB | 665 | 38 | 219 | 85 |
| 2017 | A | 4 | 0 | 1 | 0 |
| 2017 | Aplus | 5 | 0 | 2 | 1 |
| 2017 | MLB | 524 | 26 | 195 | 57 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.466035 | 0.343776 | 0.350684 | 0.00000 | 0.360797 | 205 | -0.00000 |
| K | 0.216433 | 0.331607 | 0.304593 | -0.16884 | 0.293956 | 192 | 0.00000 |
| UBB | 0.080191 | 0.115417 | 0.123584 | 0.03143 | 0.124998 | 39 | 1.56077 |
| HBP | 0.009515 | 0.009725 | 0.010324 | 0.04943 | 0.010724 | 7 | 0.04391 |
| 1B | 0.145271 | 0.106885 | 0.106943 | 0.05073 | 0.118014 | 51 | -1.20305 |
| 2B | 0.045317 | 0.035258 | 0.041469 | -0.01143 | 0.036583 | 12 | -0.54258 |
| 3B | 0.004290 | 0.000917 | 0.002308 | -0.16741 | 0.000814 | 0 | -0.27225 |
| HR | 0.032947 | 0.056415 | 0.060094 | -0.08998 | 0.054114 | 16 | 2.11732 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 493.395 | 1.17358 | 2.48283 |
| event | 493.395 | 2.17052 | 3.30265 |
| anchor_only | 493.395 | 0.99888 | 2.33918 |
| anchored | 493.395 | 1.70414 | 2.91913 |
| Actual | 522 | -3.68156 | -1.59518 |

Product = fixed PA × (rate/600 + origin replacement 0.0030762). Actual trained distinct active people 946; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 169, 'objective': 1.4502471992657386, 'maximum_gradient': 8.465641251016921e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.29091, 0.05363, 0.01921, -0.02525, -0.01318, 0.11767, 0.06457 |
| pooled_MLB_pa | 2.43000 | -0.15398, 0.03609, -0.04584, 0.02538, 0.03026, -0.17842, 0.01309 |
| prior_debut | 1.00000 | -0.08978, -0.00127, 0.02886, -0.01808, 0.01130, -0.05772, 0.03876 |
| age_centered | 0.80000 | -0.00121, -0.00354, 0.01378, -0.02015, -0.03338, -0.01302, -0.08163 |
| pooled_MLB_K | 1.02478 | -0.07763, 0.03253, 0.01225, 0.02222, -0.01370, -0.01168, 0.00658 |
| pooled_MLB_BB | 0.35404 | -0.00127, -0.06904, 0.00385, -0.00543, -0.00547, -0.00063, -0.00585 |
| on_40man | 1.00000 | -0.06451, -0.03578, 0.00888, -0.00474, -0.01241, -0.04091, -0.05224 |
| draft_class_unknown | 1.00000 | -0.03454, -0.02212, 0.00604, 0.00625, -0.02453, -0.01580, -0.05988 |
| draft_elapsed | 1.00000 | -0.05129, 0.00718, 0.01105, 0.04990, -0.00301, -0.00233, -0.02542 |
| draft_known | 1.00000 | 0.01368, 0.03770, 0.02446, -0.01971, 0.00498, 0.04664, 0.00795 |
| pooled_MLB_HR | 0.26226 | 0.01849, 0.00805, -0.00012, 0.00093, -0.00097, -0.00419, -0.04647 |
| pooled_MLB_2B | -0.14442 | -0.00335, -0.00471, -0.00119, -0.01661, 0.03958, 0.00111, -0.00597 |

1,458 weighted MLB PA retain strong older power, and the direct anchor +0.999 is less extreme than naked +2.170. Learned adjustments lower K sharply from 33.2% to 29.4% and increase singles, raising rate to +1.704, worse than old +1.174 against actual −3.682. The fixed recency pattern plus common regression misses a severe decline; this harmful correction cannot be excused as preserving production. Thames/Cozart/Duda do not show the same extreme collapse.

Origin-selected peers: Eric Thames (age 30, MLB/AAA/AA PA 551/0.0/0.0; actual next 278 PA/1.145 wins); Zack Cozart (age 31, MLB/AAA/AA PA 507/0.0/0.0; actual next 253 PA/0.311 wins); Lucas Duda (age 31, MLB/AAA/AA PA 491/0.0/0.0; actual next 367 PA/1.188 wins).

Profile support: all=39 distinct people; active=28 distinct people.

## Ronald Acuña Jr.: 2022 to 2023

Selection: largest gain.

Age 24; draft None/unknown; actual weighted MLB exposure 942.200, anchor reliability 0.90405. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2020 | MLB | 202 | 14 | 60 | 36 |
| 2021 | MLB | 360 | 24 | 85 | 47 |
| 2022 | AAA | 25 | 0 | 6 | 5 |
| 2022 | MLB | 533 | 15 | 126 | 49 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.467680 | 0.399125 | 0.413321 | 0.00000 | 0.399064 | 348 | -0.00000 |
| K | 0.224178 | 0.242197 | 0.255245 | 0.00597 | 0.243610 | 84 | 0.00000 |
| UBB | 0.078977 | 0.111397 | 0.108164 | 0.00267 | 0.111677 | 77 | 1.13903 |
| HBP | 0.011239 | 0.019885 | 0.010468 | -0.03420 | 0.019213 | 9 | 0.28965 |
| 1B | 0.142135 | 0.134536 | 0.127504 | -0.01899 | 0.131985 | 137 | -0.44799 |
| 2B | 0.043614 | 0.048130 | 0.043596 | -0.01632 | 0.047344 | 35 | 0.23172 |
| 3B | 0.003532 | 0.001107 | 0.003367 | -0.11699 | 0.000984 | 4 | -0.19953 |
| HR | 0.028646 | 0.043624 | 0.038335 | 0.05586 | 0.046123 | 41 | 1.74828 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 478.488 | 2.07348 | 3.15169 |
| event | 478.488 | 1.29812 | 2.53336 |
| anchor_only | 478.488 | 2.69682 | 3.64879 |
| anchored | 478.488 | 2.76115 | 3.70010 |
| Actual | 735 | 5.45706 | 8.96052 |

Product = fixed PA × (rate/600 + origin replacement 0.0031310). Actual trained distinct active people 1378; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 149, 'objective': 1.462459809255393, 'maximum_gradient': 9.682209383749345e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.25381, 0.01972, 0.00708, 0.01043, -0.02546, 0.09123, 0.02513 |
| pooled_MLB_pa | 1.57033 | -0.11138, 0.03998, -0.03159, -0.00341, 0.03278, -0.11567, 0.01736 |
| prior_debut | 1.00000 | -0.07369, 0.00577, 0.02188, -0.01869, 0.00211, -0.05744, 0.02695 |
| age_centered | -0.60000 | -0.00114, 0.01060, -0.01153, 0.01093, 0.02892, 0.01733, 0.06424 |
| pooled_MLB_BB | 0.31495 | 0.00513, -0.05932, 0.00569, -0.00346, -0.00667, -0.00130, -0.00482 |
| on_40man | 1.00000 | -0.05446, -0.03157, -0.00159, -0.00612, -0.02447, -0.03578, -0.04101 |
| draft_class_unknown | 1.00000 | -0.03196, -0.02412, 0.00843, -0.00008, -0.01333, -0.00618, -0.03810 |
| pooled_AAA_BB | 0.24000 | 0.00473, 0.03794, -0.00355, -0.00573, -0.00096, -0.00200, 0.00719 |
| pooled_MLB_BABIP | 0.19055 | -0.01453, -0.01103, -0.00145, -0.03625, -0.02165, -0.00894, -0.00707 |
| pooled_MLB_HR | 0.13754 | 0.00624, 0.00879, 0.00002, -0.00132, -0.00096, -0.00200, -0.02683 |
| career_mlb_observed_pa | 0.38283 | 0.01955, -0.00066, 0.00185, 0.00657, 0.00109, -0.00474, 0.00818 |
| pooled_AAA_BABIP | 0.27434 | 0.00151, 0.00165, -0.00138, 0.01489, 0.00430, 0.00046, 0.00095 |

Largest gain against V34. A 533-PA/15-HR current year follows 360/24 and actual shortened 202/14; the 942 weighted MLB PA retain past power. Anchor +2.697 and adjusted +2.761 improve old +2.074, raising value 3.15→3.70 versus actual 735 PA/8.96. It helps a rebound profile but still misses the exceptional next season and workload. Devers/Kirk/Arraez provide successful but different outcomes; no uniform superstar rebound follows.

Origin-selected peers: Rafael Devers (age 25, MLB/AAA/AA PA 614/0.0/0.0; actual next 656 PA/4.053 wins); Alejandro Kirk (age 23, MLB/AAA/AA PA 541/0.0/0.0; actual next 422 PA/0.984 wins); Luis Arraez (age 25, MLB/AAA/AA PA 603/0.0/0.0; actual next 617 PA/4.262 wins).

Profile support: all=209 distinct people; active=185 distinct people.

## Fernando Tatis Jr.: 2021 to 2022

Selection: largest harm.

Age 22; draft None/unknown; actual weighted MLB exposure 974.800, anchor reliability 0.90696. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 8 | 0 | 1 | 3 |
| 2019 | MLB | 372 | 22 | 110 | 29 |
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.456423 | 0.373318 | 0.403021 | 0.00000 | 0.388464 | 0 | -0.00000 |
| K | 0.231798 | 0.270729 | 0.282717 | -0.08798 | 0.257986 | 0 | 0.00000 |
| UBB | 0.083001 | 0.095367 | 0.092434 | -0.03716 | 0.095616 | 0 | 0.43942 |
| HBP | 0.011616 | 0.009454 | 0.009441 | -0.08399 | 0.009045 | 0 | -0.09337 |
| 1B | 0.137533 | 0.130586 | 0.119983 | -0.06414 | 0.127442 | 0 | -0.44541 |
| 2B | 0.043247 | 0.048311 | 0.044140 | -0.02826 | 0.048870 | 0 | 0.34934 |
| 3B | 0.003691 | 0.005181 | 0.003771 | -0.11962 | 0.004784 | 0 | 0.08563 |
| HR | 0.032692 | 0.067054 | 0.044493 | -0.02879 | 0.067794 | 0 | 3.51137 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 507.519 | 2.74700 | 3.91467 |
| event | 507.519 | 0.71728 | 2.19780 |
| anchor_only | 507.519 | 3.91428 | 4.90203 |
| anchored | 507.519 | 3.84698 | 4.84510 |
| Actual | 0 | 0.00000 | 0.00000 |

Product = fixed PA × (rate/600 + origin replacement 0.0031350). Actual trained distinct active people 1262; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 171, 'objective': 1.458441132147953, 'maximum_gradient': 9.110092328100282e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.26067, -0.00137, 0.03397, 0.00095, -0.03214, 0.10231, 0.05641 |
| pooled_MLB_pa | 1.62467 | -0.10770, 0.02927, -0.03226, -0.00367, 0.02336, -0.11492, 0.00956 |
| age_centered | -1.00000 | 0.00651, 0.00660, -0.01116, 0.01260, 0.04878, 0.03048, 0.09885 |
| prior_debut | 1.00000 | -0.08568, 0.00046, 0.01210, -0.00917, 0.00022, -0.06292, 0.01958 |
| pooled_MLB_HR | 0.36803 | 0.01480, 0.01199, -0.00033, 0.00008, -0.00170, -0.00650, -0.07569 |
| pooled_MLB_BABIP | 0.33652 | -0.03356, -0.01802, 0.00276, -0.06388, -0.04260, -0.01222, -0.01565 |
| on_40man | 1.00000 | -0.04575, -0.02176, -0.02642, -0.00320, -0.00483, -0.04318, -0.04234 |
| position_6 | 1.00000 | -0.02416, -0.04214, -0.03596, -0.00226, -0.00161, -0.00426, -0.04516 |
| draft_class_unknown | 1.00000 | -0.03778, -0.01002, 0.00915, 0.00909, -0.01050, -0.02101, -0.03084 |
| pooled_MLB_K | 0.40562 | -0.03392, 0.01236, -0.00749, 0.00698, -0.00808, -0.00077, -0.01085 |
| pooled_MLB_BB | 0.15087 | 0.00528, -0.03291, 0.00151, -0.00229, -0.00127, 0.00028, -0.00172 |
| pooled_AA_BB | 0.13511 | -0.00050, 0.02340, -0.00182, -0.00306, 0.00016, -0.00037, 0.00223 |

Largest deterioration is a subsequent zero-PA season from later injury/regulatory events. A known 546-PA/42-HR season plus two strong prior years justify retaining high batting talent: anchor +3.914, adjusted +3.847. With fixed 508 PA, value 4.85 is farther from zero than old 3.91. This error is mostly future opportunity, not proof that a high origin talent forecast was irrational. Alvarez/Soto/Guerrero subsequently play/productively; do not solve this by depressing every young star.

Origin-selected peers: Yordan Alvarez (age 24, MLB/AAA/AA PA 598/0.0/0.0; actual next 561 PA/6.858 wins); Juan Soto (age 22, MLB/AAA/AA PA 654/0.0/0.0; actual next 664 PA/5.617 wins); Vladimir Guerrero Jr. (age 22, MLB/AAA/AA PA 698/0.0/0.0; actual next 706 PA/4.512 wins).

Profile support: all=185 distinct people; active=157 distinct people.

## Yordan Alvarez: 2024 to 2025

Selection: false high.

Age 27; draft None/unknown; actual weighted MLB exposure 1368.400, anchor reliability 0.93190. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.450002 | 0.469768 | 0.00000 | 0.453059 | 98 | -0.00000 |
| K | 0.225800 | 0.173509 | 0.183070 | -0.01751 | 0.171655 | 33 | -0.00000 |
| UBB | 0.079036 | 0.104538 | 0.102202 | 0.01917 | 0.107286 | 23 | 0.98404 |
| HBP | 0.011072 | 0.017098 | 0.011150 | 0.01965 | 0.017556 | 0 | 0.23553 |
| 1B | 0.141968 | 0.143011 | 0.144294 | -0.00879 | 0.142723 | 31 | 0.03329 |
| 2B | 0.042593 | 0.050980 | 0.046173 | -0.02914 | 0.049853 | 8 | 0.45101 |
| 3B | 0.003820 | 0.002984 | 0.003352 | -0.20938 | 0.002437 | 0 | -0.10834 |
| HR | 0.029888 | 0.057878 | 0.039992 | -0.04996 | 0.055432 | 6 | 2.55527 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 584.774 | 3.70970 | 5.44249 |
| event | 584.774 | 2.10895 | 3.88236 |
| anchor_only | 584.774 | 4.40881 | 6.12386 |
| anchored | 584.774 | 4.15079 | 5.87239 |
| Actual | 199 | 0.91965 | 0.92510 |

Product = fixed PA × (rate/600 + origin replacement 0.0031242). Actual trained distinct active people 1545; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 148, 'objective': 1.464766294457457, 'maximum_gradient': 9.981703906322063e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24613, 0.01124, 0.03792, 0.01881, -0.03335, 0.07406, -0.02793 |
| pooled_MLB_pa | 2.28067 | -0.12155, 0.07920, -0.03518, -0.01393, 0.05145, -0.16750, 0.03366 |
| prior_debut | 1.00000 | -0.10998, -0.01703, -0.00351, -0.01585, 0.00673, -0.04800, 0.04553 |
| pooled_MLB_HR | 0.27886 | 0.01335, 0.01880, -0.00013, 0.00395, -0.00114, -0.00258, -0.05389 |
| pooled_MLB_BB | 0.24604 | 0.00573, -0.04513, 0.00471, 0.00020, -0.00496, -0.00101, -0.00074 |
| pooled_MLB_K | -0.56205 | 0.04097, -0.01304, 0.01092, -0.00381, 0.00885, -0.00040, 0.00249 |
| on_40man | 1.00000 | -0.03837, -0.03543, -0.00656, -0.00357, -0.02135, -0.02618, -0.03168 |
| draft_class_unknown | 1.00000 | -0.02609, -0.01005, 0.00861, 0.00596, -0.00867, -0.00926, -0.02790 |
| pooled_MLB_BABIP | 0.13178 | -0.01103, -0.00705, -0.00029, -0.02618, -0.01671, -0.00656, -0.00930 |
| position_10 | 1.00000 | -0.01777, 0.02587, 0.01326, 0.01140, 0.00088, 0.00175, 0.01185 |
| pooled_AAA_K | -0.11250 | -0.01863, -0.00308, -0.00049, -0.00198, -0.00360, -0.00264, -0.01146 |
| elapsed_scaled | 0.50000 | 0.00991, 0.00103, -0.00474, 0.00349, -0.00206, -0.01560, 0.01572 |

Largest false high. The strong 1,368 weighted MLB PA give +4.409 anchor and +4.151 after adjustments, above old +3.710. Fixed 585 PA versus later 199 makes value 5.87 versus 0.93 actual. Production is represented plausibly, but the later absence is not predicted. Soto/Ohtani/Guerrero stay productive; this is a workload uncertainty loss, not authorization for a universal elite-player haircut.

Origin-selected peers: Juan Soto (age 25, MLB/AAA/AA PA 713/0.0/0.0; actual next 715 PA/6.406 wins); Shohei Ohtani (age 29, MLB/AAA/AA PA 731/0.0/0.0; actual next 727 PA/7.877 wins); Vladimir Guerrero Jr. (age 25, MLB/AAA/AA PA 697/0.0/0.0; actual next 680 PA/4.973 wins).

Profile support: all=439 distinct people; active=346 distinct people.

## Alek Thomas: 2024 to 2025

Selection: ordinary.

Age 24; draft 63/HS SR; actual weighted MLB exposure 671.200, anchor reliability 0.87033. Counts use 1/.8/.6 and one fixed 100-opportunity league prior; no schedule-inflated batting evidence.

| Source year | League | Actual PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | AAA | 131 | 4 | 18 | 14 |
| 2022 | MLB | 411 | 8 | 74 | 22 |
| 2023 | AAA | 128 | 3 | 20 | 11 |
| 2023 | MLB | 402 | 9 | 86 | 18 |
| 2024 | AAA | 69 | 2 | 11 | 5 |
| 2024 | MLB | 103 | 3 | 17 | 7 |
| 2024 | RK121 | 16 | 1 | 1 | 2 |

Prediction logits = log(empirical origin anchor) + learned effect, then joint softmax. Rate conversion subtracts completed-origin league environment, not the anchor or future environment.

| Event | League reference | Own anchor | Naked model | Learned odds effect | New probability | Actual count | Wins/600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|
| other | 0.465823 | 0.529541 | 0.489417 | 0.00000 | 0.513555 | 213 | 0.00000 |
| K | 0.225800 | 0.198107 | 0.211446 | 0.03598 | 0.199165 | 122 | -0.00000 |
| UBB | 0.079036 | 0.055114 | 0.068178 | 0.09677 | 0.058881 | 21 | -0.70206 |
| HBP | 0.011072 | 0.007919 | 0.010853 | 0.01740 | 0.007815 | 5 | -0.11829 |
| 1B | 0.141968 | 0.135369 | 0.141569 | 0.08826 | 0.143396 | 77 | 0.06300 |
| 2B | 0.042593 | 0.042867 | 0.043474 | 0.07173 | 0.044665 | 19 | 0.12872 |
| 3B | 0.003820 | 0.007757 | 0.005740 | 0.02573 | 0.007719 | 3 | 0.30531 |
| HR | 0.029888 | 0.023326 | 0.029321 | 0.09215 | 0.024805 | 9 | -0.50844 |

Event-value contributions sum to conditional batting wins/600 under the existing fixed neutral weights/scale and ten runs/win. Other/K have zero direct weight but affect the probability allocation.

| Model | Fixed PA | Conditional batting wins/600 | Batting + replacement wins |
|---|---:|---:|---:|
| cohort | 226.588 | -0.80116 | 0.40534 |
| event | 226.588 | -0.25531 | 0.61148 |
| anchor_only | 226.588 | -1.57014 | 0.11494 |
| anchored | 226.588 | -0.83177 | 0.39378 |
| Actual | 469 | -1.36482 | 0.39458 |

Product = fixed PA × (rate/600 + origin replacement 0.0031242). Actual trained distinct active people 1545; optimizer {'success': True, 'message': 'CONVERGENCE: NORM OF PROJECTED GRADIENT <= PGTOL', 'iterations': 148, 'objective': 1.464766294457457, 'maximum_gradient': 9.981703906322063e-07}.

Largest actual odds terms (K, UBB, HBP, 1B, 2B, 3B, HR):

| Feature | Fixed scaled | Effects in event order |
|---|---:|---|
| intercept | 1.00000 | 0.24613, 0.01124, 0.03792, 0.01881, -0.03335, 0.07406, -0.02793 |
| prior_debut | 1.00000 | -0.10998, -0.01703, -0.00351, -0.01585, 0.00673, -0.04800, 0.04553 |
| pooled_AAA_K | -0.56286 | -0.09323, -0.01539, -0.00246, -0.00990, -0.01804, -0.01319, -0.05736 |
| pooled_MLB_pa | 1.11867 | -0.05962, 0.03885, -0.01725, -0.00683, 0.02524, -0.08216, 0.01651 |
| pooled_MLB_BABIP | -0.34820 | 0.02916, 0.01862, 0.00077, 0.06919, 0.04416, 0.01733, 0.02457 |
| age_centered | -0.60000 | -0.01101, 0.00180, -0.00187, 0.00785, 0.02613, 0.02881, 0.05618 |
| position_8 | 1.00000 | 0.01134, -0.00346, 0.00638, 0.02353, -0.00441, 0.05188, -0.00958 |
| pooled_MLB_BB | -0.24761 | -0.00577, 0.04541, -0.00474, -0.00021, 0.00499, 0.00102, 0.00075 |
| on_40man | 1.00000 | -0.03837, -0.03543, -0.00656, -0.00357, -0.02135, -0.02618, -0.03168 |
| draft_known | 1.00000 | 0.02159, 0.02926, 0.02241, -0.01891, -0.01235, 0.02133, 0.00105 |
| draft_hs | 1.00000 | 0.02916, 0.01895, -0.01222, 0.00282, 0.00680, 0.00269, 0.02030 |
| pooled_AAA_BABIP | 0.37616 | 0.00052, 0.01178, -0.00046, 0.02305, 0.00933, 0.00487, 0.00341 |

Ordinary example. Three partial MLB seasons and AAA stints give 671 weighted MLB PA, anchor −1.570 and adjusted −0.832 versus old −0.801 and actual −1.365. Predicted 227 PA versus actual 469 means value 0.394 nearly matches realized 0.395 through offsetting rate/workload errors. This must not be counted as both components being correct. Nuñez plays a little while Shewmake does not and Hernaiz struggles, providing relevant less-successful comparisons.

Origin-selected peers: Nasim Nuñez (age 23, MLB/AAA/AA PA 78/0.0/0.0; actual next 92 PA/0.205 wins); Braden Shewmake (age 26, MLB/AAA/AA PA 67/33.0/0.0; actual next 0 PA/0.000 wins); Darell Hernaiz (age 22, MLB/AAA/AA PA 135/157.0/0.0; actual next 197 PA/-0.151 wins).

Profile support: all=405 distinct people; active=362 distinct people.

## Decision

Do not adopt this fixed 100-prior empirical anchor plus residual model. It repairs established power representation and improves the naked model overall, but loses to the actual working control on conditional rates/value, especially brief debuts. Keep the mathematical source/likelihood infrastructure and negative evidence; reject this specification, not all empirical component anchors.

Current V33b remains working hitter forecast. The broad practical goal is incomplete. Pause further event reweighting in this batch; next inspect available games/role evidence for workload, the outstanding public MAE and cohort allocation gap. A failed component experiment must not erase the stronger existing batting forecast.
